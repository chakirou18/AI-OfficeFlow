"""Explicit metadata-only OTel. Never inspect bodies, URL strings or exceptions."""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import os
import time
from urllib.parse import urlsplit

from opentelemetry import trace
from opentelemetry._logs import LogRecord, SeverityNumber
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
import requests

CURRENT = ContextVar("officeflow_telemetry", default=None)
PROPAGATOR = TraceContextTextMapPropagator()
BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 20, 30)


def trace_headers():
    carrier = {}
    if trace.get_current_span().get_span_context().is_valid:
        PROPAGATOR.inject(carrier)
    return carrier


class Telemetry:
    def __init__(self, traces, metrics, logs):
        self.traces, self.metrics, self.logs = traces, metrics, logs
        self.tracer = traces.get_tracer("officeflow")
        meter = metrics.get_meter("officeflow")
        self.http_requests = meter.create_counter("officeflow.http.requests")
        self.http_errors = meter.create_counter("officeflow.http.errors")
        self.http_duration = meter.create_histogram("officeflow.http.duration", unit="s")
        self.analysis_outcomes = meter.create_counter("officeflow.analysis.outcomes")
        self.analysis_duration = meter.create_histogram("officeflow.analysis.duration", unit="s")
        self.decision_outcomes = meter.create_counter("officeflow.decision.outcomes")
        self.logger = logs.get_logger("officeflow")

    def event(self, event, attributes, *, severity=SeverityNumber.INFO):
        context = trace.get_current_span().get_span_context()
        # All callers supply fixed keys and bounded enums/numbers, never input text.
        body = {"timestamp": datetime.now(timezone.utc).isoformat(), "severity": severity.name,
                "event": event, "trace_id": format(context.trace_id, "032x"),
                "span_id": format(context.span_id, "016x"), **attributes}
        self.logger.emit(LogRecord(timestamp=time.time_ns(), trace_id=context.trace_id,
                         span_id=context.span_id, trace_flags=context.trace_flags,
                         severity_number=severity, severity_text=severity.name,
                         body=json.dumps(body), attributes=attributes))

    def analysis(self, state, error, mode, seconds):
        attrs = {"outcome": state if state in {"pending", "failed"} else "unknown",
                 "error_code": error if error in {"timeout", "interrupted", "invalid_output", "provider_error"} else "none",
                 "provider_mode": "ollama" if mode == "ollama" else "simulated"}
        self.analysis_outcomes.add(1, attrs)
        self.analysis_duration.record(seconds, attrs)
        self.event("analysis.completed", attrs, severity=SeverityNumber.ERROR if state == "failed" else SeverityNumber.INFO)

    def decision(self, outcome):
        attrs = {"outcome": outcome if outcome in {"approved", "rejected", "conflict", "failed"} else "unknown"}
        self.decision_outcomes.add(1, attrs)
        self.event("decision.completed", attrs)

    def flush(self):
        return all(provider.force_flush(timeout_millis=5000) for provider in (self.traces, self.metrics, self.logs))

    def shutdown(self):
        for provider in (self.metrics, self.logs, self.traces):
            provider.shutdown()


def configured_telemetry():
    if os.getenv("TELEMETRY_ENABLED", "false").lower() != "true":
        return None
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318").rstrip("/")
    parsed = urlsplit(endpoint)
    if (parsed.scheme != "http" or parsed.hostname not in {"otel-collector", "127.0.0.1", "localhost"}
            or parsed.port != 4318 or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
        raise ValueError("Telemetry endpoint must be a private local Collector")
    # Explicit resource avoids environment detectors/OTEL_RESOURCE_ATTRIBUTES leaks.
    environment = os.getenv("TELEMETRY_ENVIRONMENT", "local")
    if environment not in {"local", "development", "production"}:
        raise ValueError("Unknown telemetry environment")
    resource = Resource({"service.name": "officeflow-api", "deployment.environment": environment})
    session = requests.Session()
    session.trust_env = False
    traces = TracerProvider(resource=resource)
    traces.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(
        endpoint=endpoint + "/v1/traces", timeout=2, session=session), schedule_delay_millis=1000))
    metrics = MeterProvider(resource=resource, views=[View(instrument_type=None, instrument_name="*.duration",
        aggregation=ExplicitBucketHistogramAggregation(BUCKETS))], metric_readers=[PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint + "/v1/metrics", timeout=2, session=session), export_interval_millis=5000)])
    logs = LoggerProvider(resource=resource)
    logs.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(
        endpoint=endpoint + "/v1/logs", timeout=2, session=session), schedule_delay_millis=1000))
    return Telemetry(traces, metrics, logs)


@contextmanager
def operation_span(name, *, kind=SpanKind.INTERNAL):
    observer = CURRENT.get()
    if observer is None:
        yield
        return
    with observer.tracer.start_as_current_span(name, kind=kind, record_exception=False, set_status_on_exception=False) as span:
        try:
            yield
        except BaseException:
            span.set_status(Status(StatusCode.ERROR))
            raise


class TelemetryMiddleware:
    def __init__(self, app, *, observer):
        self.app, self.observer = app, observer

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        method = scope["method"] if scope["method"] in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} else "OTHER"
        # Only W3C traceparent is accepted. Never forward baggage/tracestate/headers.
        parent = {"traceparent": value.decode("ascii", errors="ignore") for key, value in scope.get("headers", []) if key == b"traceparent"}
        started, status = time.monotonic(), 500
        token = CURRENT.set(self.observer)
        try:
            with self.observer.tracer.start_as_current_span("HTTP " + method,
                    context=PROPAGATOR.extract(parent), kind=SpanKind.SERVER,
                    record_exception=False, set_status_on_exception=False) as span:
                async def respond(message):
                    nonlocal status
                    if message["type"] == "http.response.start":
                        status = message["status"]
                        message["headers"] = list(message.get("headers", [])) + [(b"traceparent", trace_headers()["traceparent"].encode())]
                    await send(message)
                try:
                    await self.app(scope, receive, respond)
                finally:
                    # FastAPI resolves included routers lazily; use only its matched
                    # template after dispatch, never the raw path or query string.
                    route = getattr(scope.get("route"), "path", "/unmatched")
                    span.update_name(method + " " + route)
                    attrs = {"http_method": method, "http_route": route, "http_status": status}
                    span.set_attributes(attrs)
                    if status >= 500:
                        span.set_status(Status(StatusCode.ERROR))
                    self.observer.http_requests.add(1, attrs)
                    self.observer.http_duration.record(time.monotonic() - started, attrs)
                    if status >= 400:
                        self.observer.http_errors.add(1, attrs)
                    self.observer.event("http.completed", attrs,
                        severity=SeverityNumber.ERROR if status >= 500 else SeverityNumber.WARN if status >= 400 else SeverityNumber.INFO)
        finally:
            CURRENT.reset(token)

FROM python:3.12-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock ./requirements.lock
RUN pip install --no-cache-dir --require-hashes -r requirements.lock \
    && useradd --uid 10001 --create-home app
COPY app ./app
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations
RUN mkdir -p /data && chown app:app /data

FROM base AS test
COPY requirements-test.lock ./requirements-test.lock
RUN pip install --no-cache-dir --require-hashes -r requirements-test.lock
COPY tests ./tests
COPY pyproject.toml run_tests.py ./
RUN chown -R app:app /app
USER app
CMD ["python", "run_tests.py"]

FROM base AS runtime
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

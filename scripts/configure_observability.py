"""Generate separate private local monitoring/ops credentials, preserving valid values."""
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]


def main():
    config = ROOT / ".env"
    if not config.exists():
        raise SystemExit("Run python scripts/configure_local.py first")
    directory = ROOT / "artifacts"
    directory.mkdir(exist_ok=True)
    password = directory / "grafana-admin-password"
    if not password.exists():
        password.write_text(secrets.token_urlsafe(32), encoding="utf-8")
        password.chmod(0o600)
    lines = config.read_text(encoding="utf-8").splitlines()
    configured = next((line.partition("=")[2] for line in lines if line.startswith("OPS_TOKEN=")), "")
    if not configured:
        lines = [line for line in lines if not line.startswith("OPS_TOKEN=")]
        lines.append("OPS_TOKEN=" + secrets.token_urlsafe(32))
        config.write_text("\n".join(lines) + "\n", encoding="utf-8")
        config.chmod(0o600)
    print("Private Grafana password and read-only ops credential configured; values not displayed.")


if __name__ == "__main__":
    main()

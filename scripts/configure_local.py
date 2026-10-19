"""Create local-only configuration without printing or overwriting credentials."""

from pathlib import Path
import secrets


def main() -> None:
    destination = Path(__file__).resolve().parents[1] / ".env"
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as config:
            config.write(
                "# Generated for loopback-only T04 development. Do not commit.\n"
                "POSTGRES_USER=officeflow\n"
                "POSTGRES_DB=officeflow\n"
                f"POSTGRES_PASSWORD={secrets.token_urlsafe(32)}\n"
                "FRONTEND_PORT=8080\n"
                "API_PORT=8000\n"
            )
        destination.chmod(0o600)
        print("Created ignored .env with a generated local password (not displayed).")
    except FileExistsError:
        print("Existing .env preserved; no configuration changed.")


if __name__ == "__main__":
    main()

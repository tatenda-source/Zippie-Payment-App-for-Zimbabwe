"""Print a cryptographically strong hex token suitable for SECRET_KEY.

Usage:
    python backend/scripts/generate_secret_key.py

Copy the output into backend/.env as SECRET_KEY, or store it in your
secrets provider (AWS Secrets Manager) under zippie/{env}/SECRET_KEY.
"""

import secrets


def main() -> None:
    print(secrets.token_hex(32))


if __name__ == "__main__":
    main()

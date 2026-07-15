"""Connect one Google test account: run OAuth in the browser, save its token.

Run once per test account (use a different Google login each time):

    python backend/scripts/connect_account.py

Tokens land in backend/.tokens/<email>.json (gitignored). After connecting
all test accounts, run check_freebusy.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # -> backend/

from app.auth.google import get_account_email, run_oauth_flow, save_credentials


def main() -> None:
    print("Opening browser for Google consent... log in with a TEST account.")
    creds = run_oauth_flow()
    email = get_account_email(creds)
    path = save_credentials(email, creds)
    print(f"Connected: {email}")
    print(f"Token saved to: {path}")


if __name__ == "__main__":
    main()

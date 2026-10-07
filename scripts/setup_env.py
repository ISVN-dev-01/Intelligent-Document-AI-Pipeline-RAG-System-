"""Create .env interactively without displaying or storing plaintext login passwords."""
import argparse
import getpass
from pathlib import Path

from _common import ROOT, cli_error

from security.auth import hash_password
from utils.errors import AppError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["demo", "google"], default="demo")
    args = parser.parse_args()
    destination = ROOT / ".env"
    if destination.exists():
        raise AppError(".env already exists. Edit it manually; setup will not overwrite secrets.")
    hashes = {}
    for role in ("admin", "user"):
        password = getpass.getpass(f"Choose {role} password (12+ characters): ")
        if password != getpass.getpass("Confirm password: "):
            raise AppError("Passwords did not match.")
        hashes[role] = hash_password(password)
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    replacements = {"ADMIN_PASSWORD_HASH": hashes["admin"], "USER_PASSWORD_HASH": hashes["user"],
                    "APP_MODE": args.mode}
    if args.mode == "demo":
        replacements.update(EMBEDDING_PROVIDER="hash", DB_BACKEND="sqlite", SIMILARITY_THRESHOLD="0.12",
                            DATA_DIR=(Path.home() / ".document_ai_demo").as_posix())
    lines = []
    for line in text.splitlines():
        key = line.split("=", 1)[0]
        if key in replacements:
            line = f"{key}={replacements[key]}"
        lines.append(line)
    with destination.open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    print(f"Created {destination}. Keep this file private.")
    print("Run streamlit run app.py." if args.mode == "demo" else "Set GOOGLE_API_KEY and MySQL credentials in .env, then initialize MySQL.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        cli_error(exc)

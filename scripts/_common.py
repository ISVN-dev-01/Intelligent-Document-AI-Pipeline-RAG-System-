"""Make `python scripts/tool.py` work from the repository root on Windows and POSIX."""
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def authenticated_app(role="admin"):
    from services.bootstrap import build_application
    app = build_application()
    principal = app.auth.login(role, getpass.getpass(f"{role.capitalize()} password: "))
    return app, principal


def cli_error(exc):
    from utils.errors import AppError
    print(str(exc) if isinstance(exc, AppError) else "Operation failed. Check configuration and local event logs.", file=sys.stderr)
    raise SystemExit(1)

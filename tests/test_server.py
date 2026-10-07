"""Real local HTTP startup, distinct from Streamlit's in-process AppTest."""
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def test_streamlit_http_health(settings):
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, APP_MODE="demo", EMBEDDING_PROVIDER="hash", DB_BACKEND="sqlite",
               DATA_DIR=str(settings.data_dir),
               ADMIN_PASSWORD_HASH=settings.admin_password_hash.get_secret_value(),
               USER_PASSWORD_HASH=settings.user_password_hash.get_secret_value())
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with (settings.data_dir / "server.log").open("w") as log:
        process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless=true", f"--server.port={port}", "--server.address=127.0.0.1"],
            cwd=root, env=env, stdout=log, stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                assert process.poll() is None, "Streamlit exited during startup"
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=1) as response:
                        assert response.status == 200 and response.read() == b"ok"
                    break
                except (urllib.error.URLError, TimeoutError):
                    time.sleep(0.2)
            else:
                raise AssertionError("Streamlit did not become healthy within 30 seconds")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

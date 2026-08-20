import os
import socket
import subprocess
import sys
import time
from urllib.request import urlopen


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_static_root_and_health_endpoints(tmp_path):
    (tmp_path / "index.html").write_text("web mvp", encoding="utf-8")
    port = _free_port()
    env = {**os.environ, "GITSHELVES_ROOT": str(tmp_path), "PORT": str(port)}
    process = subprocess.Popen(
        [sys.executable, "deploy/server.py"], env=env, stdout=subprocess.DEVNULL
    )
    try:
        for _ in range(50):
            try:
                with urlopen(f"http://127.0.0.1:{port}/healthz") as response:
                    assert response.status == 200
                    break
            except OSError:
                time.sleep(0.02)
        else:
            raise AssertionError("server did not start")
        for path, body in [("/", b"web mvp"), ("/livez", b"ok\n")]:
            with urlopen(f"http://127.0.0.1:{port}{path}") as response:
                assert response.status == 200
                assert body in response.read()
    finally:
        process.terminate()
        process.wait(timeout=5)

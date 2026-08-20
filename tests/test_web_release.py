import contextlib
import importlib.util
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
import pytest

ROOT = Path(__file__).parents[1]


def _server_module():
    spec = importlib.util.spec_from_file_location(
        "static_server", ROOT / "scripts/static_server.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_static_server_routes(tmp_path):
    (tmp_path / "index.html").write_text("web mvp", encoding="utf-8")
    module = _server_module()
    module.ROOT = tmp_path
    server = ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for path, body in [("/", "web mvp"), ("/healthz", "ok\n"), ("/livez", "ok\n")]:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{server.server_port}{path}"
            ) as response:
                assert response.status == 200
                assert response.read().decode() == body
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_generated_model_contract_is_ignored():
    assert "web/public/models/*.stl" in (ROOT / ".gitignore").read_text()
    script = (ROOT / "scripts/prepare_web_models.py").read_text()
    assert "baseplate_2x6.stl" in script and "contrib_cube.stl" in script


@pytest.mark.parametrize("tag", ["latest", "main", "staging", "production"])
def test_chart_rejects_known_mutable_tags(tag):
    helper = (ROOT / "charts/gitshelves/templates/_helpers.tpl").read_text()
    assert f'(eq $tag "{tag}")' in helper

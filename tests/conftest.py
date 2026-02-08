import logging
import socket
import subprocess
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

import pytest

logger = logging.getLogger(__name__)


REPO_ROOT = Path(__file__).parent / ".."


@pytest.fixture(scope="session", autouse=True)
def build_wasm():
    # Run ../build_wasm.sh
    script = REPO_ROOT / "build_wasm.sh"
    res = subprocess.run([script], check=True)
    logger.info("Built WASM: %s", res.stdout)


@pytest.fixture(scope="session")
def port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session", autouse=True)
def local_server(port: int):
    def handler(*args: Any, **kwargs: Any):
        return SimpleHTTPRequestHandler(*args, directory=REPO_ROOT / "build", **kwargs)

    server = HTTPServer(("127.0.0.1", port), handler)

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    yield
    server.shutdown()
    server_thread.join()

from __future__ import annotations
import base64, json, mimetypes, threading, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from .model import clean

ASSETS = Path(__file__).resolve().parent.parent / "web"


def make_server(engine, host="127.0.0.1", port=8888):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(
            self, value, status=200, content_type="application/json; charset=utf-8", filename=None
        ):
            if isinstance(value, (dict, list)):
                value = json.dumps(clean(value), ensure_ascii=False, allow_nan=False).encode()
            if isinstance(value, str):
                value = value.encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(value)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            if filename:
                self.send_header("Content-Disposition", 'attachment; filename="' + filename + '"')
            self.end_headers()
            self.wfile.write(value)

        def do_GET(self):
            try:
                path = urllib.parse.urlsplit(self.path)
                route = path.path
                q = urllib.parse.parse_qs(path.query)
                if route == "/api/state":
                    return self.send(
                        {
                            "calculations": engine.listing(),
                            "utilities": engine.utilities,
                            "root": str(engine.root),
                            "fields": {k: v.info() for k, v in engine.fields.items()},
                        }
                    )
                if route == "/api/help":
                    from .help import help_payload

                    return self.send(help_payload())
                if route.startswith("/api/calculation/"):
                    return self.send(engine.detail(route.rsplit("/", 1)[1]))
                if route.startswith("/api/task/"):
                    return self.send(engine.task(route.rsplit("/", 1)[1]))
                if route == "/api/project":
                    return self.send(engine.project(), filename="GaussLook.glproj")
                if route == "/api/browse":
                    p = (engine.root / q.get("path", [""])[0]).resolve()
                    if not p.is_relative_to(engine.root):
                        raise ValueError("--root 바깥 경로에 접근할 수 없습니다.")
                    entries = []
                    for v in sorted(p.iterdir(), key=lambda v: (not v.is_dir(), v.name.lower())):
                        if v.name.startswith("."):
                            continue
                        entries.append(
                            {
                                "name": v.name,
                                "directory": v.is_dir(),
                                "path": str(v.relative_to(engine.root)),
                                "size": v.stat().st_size if v.is_file() else None,
                            }
                        )
                    return self.send(
                        {"path": str(p.relative_to(engine.root)), "entries": entries[:1000]}
                    )
                if route == "/api/catalog":
                    return self.send(
                        json.loads((ASSETS.parent / "docs/feature_status.json").read_text())
                    )
                target = (ASSETS / ("index.html" if route == "/" else route.lstrip("/"))).resolve()
                if not target.is_relative_to(ASSETS) or not target.is_file():
                    return self.send({"error": "Not found"}, 404)
                return self.send(
                    target.read_bytes(),
                    content_type=mimetypes.guess_type(target)[0] or "application/octet-stream",
                )
            except Exception as exc:
                self.send({"error": str(exc)}, 400)

        def do_POST(self):
            try:
                origin = self.headers.get("Origin")
                host_value = self.headers.get("Host", "")
                if origin and urllib.parse.urlsplit(origin).netloc != host_value:
                    raise ValueError("교차 출처 요청을 허용하지 않습니다.")
                if self.headers.get("Sec-Fetch-Site") == "cross-site":
                    raise ValueError("교차 사이트 요청을 허용하지 않습니다.")
                length = int(self.headers.get("Content-Length", 0))
                if not 0 < length <= 360 * 1024 * 1024:
                    raise ValueError("요청 크기가 허용 범위를 벗어났습니다.")
                if not self.headers.get("Content-Type", "").startswith("application/json"):
                    raise ValueError("JSON 요청이 필요합니다.")
                data = json.loads(self.rfile.read(length))
                path = urllib.parse.urlsplit(self.path).path
                if path == "/api/upload":
                    return self.send(
                        engine.upload(data["name"], base64.b64decode(data["base64"], validate=True))
                    )
                if path == "/api/open":
                    return self.send(engine.load(engine.root / data["path"], restricted=True))
                if path == "/api/demo":
                    return self.send(engine.demo())
                if path == "/api/action":
                    return self.send(
                        engine.action(data.pop("action"), data.pop("id", None), **data)
                    )
                if path == "/api/cancel":
                    return self.send(engine.cancel(data["task"]))
                if path == "/api/project":
                    return self.send(engine.load_project(data))
                return self.send({"error": "Not found"}, 404)
            except Exception as exc:
                self.send({"error": str(exc)}, 400)

    return ThreadingHTTPServer((host, int(port)), Handler)

#!/usr/bin/env python3
"""python GaussLook.py [--web --port 8888] [result.log ...]"""

from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path


def main(argv=None):
    p = argparse.ArgumentParser(description="GaussLook · Gaussian 16 results / X11 and web")
    p.add_argument("files", nargs="*")
    p.add_argument("--web", action="store_true", help="현재 PC 브라우저에서 사용할 웹 서버 실행")
    p.add_argument("--port", type=int, default=8888)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--root", default=str(Path.cwd()), help="웹 파일 브라우저의 기준 폴더")
    p.add_argument("--gaussian-dir", help="formchk/cubegen/freqchk 실행 파일 폴더")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--check", action="store_true", help="GUI 없이 설치 환경 확인")
    p.add_argument("--json", action="store_true", help="파일 분석 결과를 JSON으로 출력")
    p.add_argument("--quit-after", type=int, help=argparse.SUPPRESS)
    p.add_argument("--version", action="version", version="GaussLook 1.4.0")
    args = p.parse_args(argv)
    try:
        from gausslook.engine import Engine
    except ImportError as exc:
        print(
            f"필수 모듈을 찾지 못했습니다: {exc}\n실행: python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 2
    e = Engine(args.root, args.gaussian_dir)
    if args.check:
        import importlib.util

        print(
            json.dumps(
                {
                    "version": "1.4.0",
                    "python": sys.version,
                    "DISPLAY": bool(os.environ.get("DISPLAY")),
                    "utilities": e.utilities,
                    "modules": {
                        n: bool(importlib.util.find_spec(n))
                        for n in ["numpy", "scipy", "skimage", "cclib", "tkinter", "rdkit"]
                    },
                    "web_assets": (Path(__file__).parent / "web/vendor/3Dmol-min.js").is_file(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        e.close()
        return 0
    for path in args.files:
        try:
            loaded = e.load(path)
            if loaded.get("task"):
                tid = loaded["task"]
                if not args.json:
                    print(f"{path}: formchk 변환 중…", flush=True)
                while e.task(tid)["status"] in ("queued", "running"):
                    time.sleep(0.1)
                task = e.task(tid)
                if task["status"] != "done":
                    raise ValueError(task.get("error", task["status"]))
        except Exception as exc:
            print(f"{path}: {exc}", file=sys.stderr)
    if args.demo:
        e.demo()
    if args.json:
        print(
            json.dumps(
                [e.detail(cid) for cid in e.calcs], ensure_ascii=False, indent=2, allow_nan=False
            )
        )
        e.close()
        return 0
    if args.web:
        from gausslook.webserver import make_server

        try:
            server = make_server(e, args.host, args.port)
        except OSError as exc:
            print(f"웹 서버 시작 실패: {exc}\n다른 --port 값을 지정하세요.", file=sys.stderr)
            e.close()
            return 2
        print(
            f"GaussLook 1.4.0\nURL: http://127.0.0.1:{server.server_port}\n서버 root: {e.root}\nMobaXterm: 같은 포트로 Local port forwarding 후 현재 PC 브라우저에서 URL을 여세요.\nCtrl+C로 종료합니다.",
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
            e.close()
    else:
        try:
            from gausslook.desktop import App

            App(e, args.quit_after).run()
        except Exception as exc:
            print(
                f"X11 GUI 시작 실패: {exc}\nLinux: python3-tk 설치, MobaXterm X server 및 SSH X11 forwarding과 DISPLAY를 확인하세요.\n웹 모드: python GaussLook.py --web --port 8888",
                file=sys.stderr,
            )
            e.close()
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

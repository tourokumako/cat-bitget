"""dashboard_server.py — ダッシュボード配信 + ラベル保存サーバ

GET  *                         dashboard/ 配下を静的配信
POST /api/save_daily_labels    body: {"labels": [{"date":"YYYY-MM-DD","label":"...","note":"..."}, ...]}
                               → data/regime_ground_truth_daily_human.csv に書き戻し（自動バックアップ付）

起動:
    python3 scripts/dashboard_server.py
    → http://localhost:8765/index.html

注意:
- 既存の `python3 -m http.server 8765` を kill してから起動
- バックアップ先: data/regime_label_backups/regime_ground_truth_daily_human_YYYYMMDD_HHMMSS.csv
"""
from __future__ import annotations

import csv
import http.server
import json
import shutil
import socketserver
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = REPO_ROOT / "dashboard"
DATA_DIR = REPO_ROOT / "data"
LABEL_CSV = DATA_DIR / "regime_ground_truth_daily_human.csv"
BACKUP_DIR = DATA_DIR / "regime_label_backups"
PORT = 8765
VALID_LABELS = {"", "downtrend", "range", "uptrend"}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/save_daily_labels":
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid json"})
            return
        labels = payload.get("labels")
        if not isinstance(labels, list) or not labels:
            self._send_json(400, {"error": "labels must be non-empty list"})
            return
        for r in labels:
            if not isinstance(r, dict) or "date" not in r:
                self._send_json(400, {"error": "each row must have date"})
                return
            if r.get("label", "") not in VALID_LABELS:
                self._send_json(400, {"error": f"invalid label: {r.get('label')!r}"})
                return
        BACKUP_DIR.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"regime_ground_truth_daily_human_{ts}.csv"
        if LABEL_CSV.exists():
            shutil.copy2(LABEL_CSV, backup_path)
        rows_sorted = sorted(labels, key=lambda r: r["date"])
        with LABEL_CSV.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "label", "note"])
            for r in rows_sorted:
                w.writerow([r["date"], r.get("label", ""), r.get("note", "")])
        self._send_json(200, {"ok": True, "rows": len(labels), "backup": backup_path.name})


def main() -> None:
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"serving at http://localhost:{PORT}/index.html")
        print(f"  static dir: {DASHBOARD_DIR}")
        print(f"  POST /api/save_daily_labels -> {LABEL_CSV}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nshutdown")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""enforce_worklog_on_experiment_selftest.py — enforce_worklog_on_experiment.py（判定の本体）を、一時フォルダで試す
（2026-10-17・187回目・まこさん「要で、CCの案の通りに修正する」）。本物の売買記録・worklog・状態のファイルは触らない。

見る物＝実験（新しい売買記録）の後の3つの決まり（A 記録・B report と analysis・C 型別）が今までどおり止まること、
  10月1日に登録を外した hook が立てていた印（fastmode_record_pending・tool_change_pending）が残っていても止めないこと。
使い方＝python3 .claude/hooks/enforce_worklog_on_experiment_selftest.py（全部 期待どおりなら exit 0）
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import time

PY = pathlib.Path(__file__).resolve().parent / "enforce_worklog_on_experiment.py"


def run(files: dict) -> int:
    """files＝{置き場の種類/名前: 何秒前に書いたか}。種類＝r（売買記録の置き場）・w（worklog の置き場）・s（状態の置き場）。"""
    with tempfile.TemporaryDirectory(prefix="ewoe_selftest_") as d:
        dirs = {k: os.path.join(d, k) for k in "rws"}
        for p in dirs.values():
            os.mkdir(p)
        now = time.time()
        for key, (age, text) in files.items():
            kind, name = key.split("/", 1)
            path = os.path.join(dirs[kind], name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            os.utime(path, (now - age, now - age))
        r = subprocess.run([sys.executable, str(PY), dirs["r"], dirs["w"], dirs["s"]], capture_output=True, text=True)
        return r.returncode


SC = "r/trades_e37_range_scalp_v59d_164_score.csv"
REP = "r/report_trades_e37_range_scalp_v59d_164_score.txt"
ANA = "r/analysis_trades_e37_range_scalp_v59d_164_score.txt"
WL_OLD = ("w/session_worklog_20261016.md", (100, "前の記録"))
WL_TYPED = ("w/session_worklog_20261017.md", (10, "v59d_164 の結果。型別＝down と flat_up に分けて見た"))
WL_NOTYPE = ("w/session_worklog_20261017.md", (10, "v59d_164 の結果。合計 net だけ見た"))

CASES = [
    ("S1 何もしていない → 通す", {WL_OLD[0]: WL_OLD[1]}, 0),
    ("S2 新しい売買記録の後に worklog を書いていない → 止める（A）", {WL_OLD[0]: WL_OLD[1], SC: (5, "x")}, 7),
    ("S3 worklog は書いたが report と analysis が無い → 止める（B）", {SC: (50, "x"), WL_TYPED[0]: WL_TYPED[1]}, 8),
    ("S4 report と analysis は在るが、worklog に型別が無い → 止める（C）",
     {SC: (50, "x"), REP: (40, "x"), ANA: (40, "x"), WL_NOTYPE[0]: WL_NOTYPE[1]}, 9),
    ("S5 手順を全部 済ませた → 通す", {SC: (50, "x"), REP: (40, "x"), ANA: (40, "x"), WL_TYPED[0]: WL_TYPED[1]}, 0),
    ("S6 10月1日に外した hook の分析の印（fastmode_record_pending）が残っている → 止めない",
     {WL_OLD[0]: WL_OLD[1], "s/fastmode_record_pending": (5, "")}, 0),
    ("S7 10月1日に外した hook の道具の直しの印（tool_change_pending）が残っている → 止めない",
     {WL_OLD[0]: WL_OLD[1], "s/tool_change_pending": (5, "")}, 0),
]


def main() -> int:
    bad = 0
    for name, files, want in CASES:
        got = run(files)
        ok = got == want
        bad += 0 if ok else 1
        print(f"{'✅' if ok else '❌'} {name}（終了コード {got}・期待 {want}）")
    print(f"[selftest] {len(CASES) - bad}/{len(CASES)}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

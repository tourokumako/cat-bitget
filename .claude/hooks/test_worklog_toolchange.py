#!/usr/bin/env python3
"""test_worklog_toolchange.py — 「わざと壊して止まるか試すテスト」

対象＝`enforce_worklog_on_experiment.py`（引き継ぎ記録ゲート・fast-mode）。
新設: 2026-08-22（50回目・まこさん決定 A・`next_step.md` §6 の20番）。

★何を確かめるか
  直す前の穴＝見張りが見ていたのは ①売買記録CSV の更新時刻 ②分析の印 の2つだけ。
  ＝**売買記録CSVを出さない作業（プログラムを直す）は、まるごと検知の外**だった。
  直したあと＝`tool_change_pending`（pdca_mark.py が Edit/Write で立てる印）も見る。

★誤って止めないことも確かめる
  道具を直しただけのターンで、過去の採点CSVの report/analysis を求めて止めると邪魔になる。
  だから B（report/analysis が無い）と C（型別の分析が無い）は、実験・分析のときだけ見る。

使い方
  python3 test_worklog_toolchange.py
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import time

HOOK = pathlib.Path(__file__).resolve().parent / "enforce_worklog_on_experiment.py"


def run_case(*, trade: float | None, pending: float | None, tool: float | None,
             worklog: float | None, with_report: bool = False,
             score_csv: bool = False, score_t: float | None = None) -> int:
    """それぞれの時刻（None＝作らない）で 見張りを走らせて、終了の番号を返す。"""
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        ratchet = root / "ratchet"; ratchet.mkdir()
        wldir = root / "wl"; wldir.mkdir()
        state = root / "state"; state.mkdir()

        def put(p: pathlib.Path, t: float) -> None:
            p.write_text("x", encoding="utf-8")
            os.utime(p, (t, t))

        if trade is not None:
            put(ratchet / "trades_demo_001.csv", trade)
        if score_csv:
            st = score_t if score_t is not None else (trade if trade is not None else time.time())
            put(ratchet / "trades_demo_001_score.csv", st)
            if with_report:
                put(ratchet / "report_trades_demo_001_score.txt", st)
                put(ratchet / "analysis_trades_demo_001_score.txt", st)
        if pending is not None:
            put(state / "fastmode_record_pending", pending)
        if tool is not None:
            put(state / "tool_change_pending", tool)
        if worklog is not None:
            put(wldir / "session_worklog_20260822.md", worklog)
        r = subprocess.run([sys.executable, str(HOOK), str(ratchet), str(wldir), str(state)],
                           capture_output=True, text=True)
        return r.returncode


def main() -> int:
    ng: list[str] = []

    def chk(name: str, cond: bool, got: object = "") -> None:
        print(("  ✅ " if cond else "  ❌ ") + name + (f"（実際＝{got}）" if not cond else ""))
        if not cond:
            ng.append(name)

    old, new = 1000.0, 2000.0
    print("[test_worklog_toolchange] わざと壊して止まるか試すテスト")

    rc = run_case(trade=None, pending=None, tool=None, worklog=None)
    chk("T1 何もしていなければ通す（0）", rc == 0, rc)

    rc = run_case(trade=new, pending=None, tool=None, worklog=old, score_csv=True, with_report=True)
    chk("T2 実験が記録より新しければ止まる（7）", rc == 7, rc)

    rc = run_case(trade=None, pending=new, tool=None, worklog=old)
    chk("T3 分析が記録より新しければ止まる（7）", rc == 7, rc)

    rc = run_case(trade=None, pending=None, tool=new, worklog=old)
    chk("T4 ★プログラムの直しが記録より新しければ止まる（7）＝直す前は通っていた穴", rc == 7, rc)

    rc = run_case(trade=None, pending=None, tool=old, worklog=new)
    chk("T5 記録の方が新しければ通す（0）", rc == 0, rc)

    # T6＝★新しく厳しくなっていないことの確認。
    #   過去の採点CSV が在るターンで、「道具の印が在る場合」と「無い場合」の結果を並べる。
    #   同じ結果なら、B（report/analysis）と C（型別の分析）は 今回の直しで変わっていない。
    rc_with = run_case(trade=None, pending=None, tool=new, worklog=new + 1,
                       score_csv=True, score_t=old, with_report=True)
    rc_without = run_case(trade=None, pending=None, tool=None, worklog=new + 1,
                          score_csv=True, score_t=old, with_report=True)
    chk(f"T6 ★道具の印が在っても無くても B・C の結果は同じ（{rc_with} と {rc_without}）",
        rc_with == rc_without, f"{rc_with} と {rc_without}")

    # T6b＝★直したことで新しく厳しくなっていないことの確認。
    #      売買記録CSV が1本も無ければ、B（report/analysis）は見ない＝道具の直しだけで止まらない。
    rc = run_case(trade=None, pending=None, tool=new, worklog=new + 1,
                  score_csv=False, with_report=False)
    chk("T6b ★売買記録CSVが1本も無ければ、道具の直しだけでは止めない（0）", rc == 0, rc)

    rc = run_case(trade=new, pending=None, tool=None, worklog=new + 1, score_csv=True, with_report=False)
    chk("T7 実験のあとに report/analysis が無ければ止まる（8）", rc == 8, rc)

    rc = run_case(trade=None, pending=None, tool=None, worklog=new)
    chk("T8 記録だけ在って作業が無ければ通す（0）", rc == 0, rc)

    print(f"[test_worklog_toolchange] {9 - len(ng)}/9 pass")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())

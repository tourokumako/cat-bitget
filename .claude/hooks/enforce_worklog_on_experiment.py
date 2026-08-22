#!/usr/bin/env python3
"""enforce_worklog_on_experiment.py — 判定本体（Stop hook・fast-mode・.sh から呼ばれる）。

pdca_mark の教訓（2026-07-03 無言死）に従い python は別ファイル。
判定（まこさん承認 2026-07-17「強制化はOK」で B/C を拡張）:
  A) 実験(新 trades_*.csv) or 分析(fastmode_record_pending) の後に worklog 未更新 → exit 7（従来）。
  B) 最新の採点 CSV（trades_*_score.csv・直下）に対応する report_<stem>.txt / analysis_<stem>.txt が無い → exit 8
     ＝「report/analyze を出さずに結論を言う」を物理で止める。
  C) worklog に その実験の <タグ_番号>（例 fix6m_095）の記載が無い、または記載以降に「型別」の分析が無い → exit 9
     ＝「型別（down/flat_up）に分けて見る」を物理で促す（中身の質までは機械で保証できない＝まこさんの目）。
"""
import glob
import os
import re
import sys

ratchet, wldir, state = sys.argv[1], sys.argv[2], sys.argv[3]

trades = glob.glob(os.path.join(ratchet, "trades_*.csv"))
newest_trade = max((os.path.getmtime(p) for p in trades), default=0)
marker = os.path.join(state, "fastmode_record_pending")
newest_pending = os.path.getmtime(marker) if os.path.exists(marker) else 0
# ★2026-08-22（50回目・まこさん決定 A・next_step §6 の20番）＝プログラムを直した作業も対象にする。
#   直す前の穴＝見ていたのは ①売買記録CSV ②分析の印 の2つだけ＝売買記録CSVを出さない作業
#   （プログラムを直す・文書を直す・検査を走らせる）が、まるごと検知の外だった。
#   実例＝50回目のセッション。CC が5本のファイルを書き換えても、この見張りは1度も止めなかった。
#   印を立てるのは pdca_mark.py（Edit/Write/MultiEdit で scripts/priority_rebuild/*.py を触ったとき）。
tool_marker = os.path.join(state, "tool_change_pending")
newest_tool = os.path.getmtime(tool_marker) if os.path.exists(tool_marker) else 0
newest_exp = max(newest_trade, newest_pending)             # B/C は実験・分析のときだけ見る
newest_action = max(newest_exp, newest_tool)               # A は道具の直しも見る
if newest_action == 0:
    sys.exit(0)                                            # 実験も分析も道具の直しもしていない → 通す

wls = glob.glob(os.path.join(wldir, "session_worklog_*.md"))
newest_wl = max((os.path.getmtime(p) for p in wls), default=0)
if newest_wl < newest_action:                              # A) 記録が実験/分析/道具の直しより古い
    sys.stderr.write("EXPERIMENT " if newest_trade > newest_wl else "")
    sys.stderr.write("ANALYSIS " if newest_pending > newest_wl else "")
    sys.stderr.write("TOOLCHANGE " if newest_tool > newest_wl else "")
    sys.exit(7)

# ★B と C は「実験・分析をした」ときだけ見る。
#   道具を直しただけのターンで、過去の採点CSVの report/analysis を求めると、誤って止めてしまう。
if newest_exp == 0:
    sys.exit(0)

scs = glob.glob(os.path.join(ratchet, "trades_*_score.csv"))
if not scs:
    sys.exit(0)
sc = max(scs, key=os.path.getmtime)
stem = os.path.basename(sc)[:-4]                           # trades_..._score
rep = os.path.join(ratchet, "report_" + stem + ".txt")
ana = os.path.join(ratchet, "analysis_" + stem + ".txt")
missing = [n for n, p in (("report", rep), ("analysis", ana)) if not os.path.exists(p)]
if missing:                                                # B) report/analyze 未実行
    sys.stderr.write("MISSING:" + ",".join(missing) + " (" + stem + ") ")
    sys.exit(8)

m = re.search(r"_([A-Za-z0-9]+_\d+)_score$", stem)
tok = m.group(1) if m else stem                            # 例: fix6m_095
found = False
for p in wls:
    try:
        txt = open(p, encoding="utf-8", errors="ignore").read()
    except OSError:
        continue
    i = txt.find(tok)
    if i >= 0 and "型別" in txt[i:]:
        found = True
        break
if not found:                                              # C) worklog に タグ_番号＋型別 の記録が無い
    sys.stderr.write("NO_TYPED_ANALYSIS (" + tok + ") ")
    sys.exit(9)

sys.exit(0)

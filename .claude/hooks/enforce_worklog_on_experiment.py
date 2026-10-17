#!/usr/bin/env python3
"""enforce_worklog_on_experiment.py — 判定本体（Stop hook・fast-mode・.sh から呼ばれる）。

pdca_mark の教訓（2026-07-03 無言死）に従い python は別ファイル。
判定（まこさん承認 2026-07-17「強制化はOK」で B/C を拡張）:
  A) 実験(新 trades_*.csv) の後に worklog 未更新 → exit 7（2026-10-17 から分析の印・道具の直しの印は読まない）。
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
# ★2026-10-17（187回目・まこさん「要で、CCの案の通りに修正する」）＝分析の印（fastmode_record_pending）と
#   道具の直しの印（tool_change_pending）は読まない。印を立てる hook（track_fastmode_data_read・pdca_mark）は
#   2026-10-01 に まこさんの指示で登録から外れた。直近30日の止め17回は全部この2つの印から来ていて、
#   売買の実験とは関係が無かった（試しの道具・hook の試しの後）。
if newest_trade == 0:
    sys.exit(0)                                            # 戦略の実験をしていない → 通す

wls = glob.glob(os.path.join(wldir, "session_worklog_*.md"))
newest_wl = max((os.path.getmtime(p) for p in wls), default=0)
if newest_wl < newest_trade:                               # A) 記録が実験より古い
    sys.stderr.write("EXPERIMENT ")
    sys.exit(7)

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

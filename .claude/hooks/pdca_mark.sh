#!/bin/bash
# PostToolUse: PDCA マーカー管理（analysis_playbook §4 物理強制・2026-06-05 まこさん矯正指示）
# score.py 採点 → 「report未済」「ledger未済」の旗を立てる。
# report.py 実行で report 旗 / ledger.md 編集で ledger 旗 を下ろす。
# 2026-06-12 拡張（まこさん合意）:
#  - precheck（審判の門）通過/FAIL でも report/analyze/ledger/5q を必須化（FAIL=閉じる時も分析を飛ばせない）
#  - report.py は --vs（前回ベースライン比較・KB §0）必須。無しで実行すると need_vs 旗。
#    真の初回のみ、まこさん GO を得て state/no_baseline_approved を作成（1回で消費）。
#  - ledger 記録は「5つの問い」(【問1 レバー】【問2 不足量】【問3 負け集中】【問4 過去接続】【問5 次仮説】)
#    が全部含まれる編集があるまで need_5q 旗が残る（最低ライン分析≠ゴールの物理化）。
# Stop hook(pdca_gate.sh) が旗の残存でターン終了をブロックする。
export PDCA_STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$PDCA_STATE"
cat | python3 -c '
import sys, json, os, re
state = os.environ["PDCA_STATE"]
need_report = os.path.join(state, "pdca_need_report")
need_ledger = os.path.join(state, "pdca_need_ledger")
need_analyze = os.path.join(state, "pdca_need_analyze")
need_score = os.path.join(state, "pdca_need_score")
need_vs = os.path.join(state, "pdca_need_vs")
need_5q = os.path.join(state, "pdca_need_5q")
need_next_step = os.path.join(state, "pdca_need_next_step")
no_baseline = os.path.join(state, "no_baseline_approved")
def touch(p): open(p, "w").close()
def rm(p):
    try: os.remove(p)
    except FileNotFoundError: pass
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
tn = d.get("tool_name", "")
ti = d.get("tool_input", {}) or {}
if tn == "Bash":
    cmd = ti.get("command", "") or ""
    # 実験スクリプト実行 → 審判(score.py/precheck.py)を通すまでターン終了不可（2026-06-12 E24 素通り事案）
    # ただし以下は need_score を立てない:
    #  - --smoke: 採点しない検証ステップ（自己検査・規模確認）（2026-06-12 まこさん・smoke で永久未閉じ事案）
    #  - --no-score: 設計上採点なしの工程（メタラベリング Phase1=OOF 診断のみ・採点は別工程 Phase2 の score.py）。
    #    （2026-06-12 まこさん承認・E28 Phase1 OOF で永久未閉じ事案＝Phase1 は連続モード変換前で score.py 適用外）
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*(strat_|train_|measure_)[A-Za-z0-9_]*\.py", cmd) and "--smoke" not in cmd and "--no-score" not in cmd:
        touch(need_score)
    # python(3) で実際に score.py/report.py を実行する形のみ検知（grep/echo/別行言及では誤爆しない）
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*score\.py", cmd):
        rm(need_score); touch(need_report); touch(need_ledger); touch(need_analyze); touch(need_5q)
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*precheck\.py", cmd):
        # precheck も審判系の門。FAIL=閉じる場合も 分析・記録・5つの問い を飛ばせない（2026-06-12 まこさん）
        rm(need_score); touch(need_report); touch(need_ledger); touch(need_analyze); touch(need_5q)
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*report\.py", cmd):
        rm(need_report)
        # --vs（前回比較・KB §0）必須。無しは need_vs 旗（初回のみ no_baseline_approved で免除・1回で消費）
        if "--vs" in cmd:
            rm(need_vs)
        elif os.path.exists(no_baseline):
            rm(no_baseline); rm(need_vs)
        else:
            touch(need_vs)
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*analyze\.py", cmd):
        rm(need_analyze)  # 深掘りバッテリー N1〜N9 実行で旗が下りる
elif tn in ("Edit", "Write", "MultiEdit"):
    fp = ti.get("file_path", "") or ""
    if fp.endswith("ledger.md"):
        rm(need_ledger)
        # ledger を更新した＝実験を記録した → 次セッションの起点 next_step.md を上書き更新するまで
        # ターン終了不可（2026-06-12 まこさん指示・引き継ぎ漏れの物理強制）。next_step.md 編集で下りる。
        touch(need_next_step)
        # 5つの問いが全部含まれる編集なら need_5q を下ろす（形だけ防止は まこさん30秒チェックが担保）
        payload = (ti.get("new_string", "") or "") + (ti.get("content", "") or "")
        for e in (ti.get("edits", []) or []):
            payload += e.get("new_string", "") or ""
        tokens = ["【問1 レバー】", "【問2 不足量】", "【問3 負け集中】", "【問4 過去接続】", "【問5 次仮説】"]
        if all(t in payload for t in tokens):
            rm(need_5q)
    if fp.endswith("next_step.md"):
        # 次セッションの起点を上書き更新 → 旗を下ろす。ただし記載必須項目（本筋/やってはいけない/出典）を
        # 含む編集の時だけ（薄い1文字編集で旗を消す＝引き継ぎ空洞化を防ぐ・中身の質はまこさん30秒チェック）。
        ns = (ti.get("new_string", "") or "") + (ti.get("content", "") or "")
        for e in (ti.get("edits", []) or []):
            ns += e.get("new_string", "") or ""
        if all(t in ns for t in ("本筋", "やってはいけない", "出典")):
            rm(need_next_step)
'
exit 0

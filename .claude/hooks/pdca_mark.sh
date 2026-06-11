#!/bin/bash
# PostToolUse: PDCA マーカー管理（analysis_playbook §4 物理強制・2026-06-05 まこさん矯正指示）
# score.py 採点 → 「report未済」「ledger未済」の旗を立てる。
# report.py 実行で report 旗 / ledger.md 編集で ledger 旗 を下ろす。
# Stop hook(pdca_gate.sh) が旗の残存でターン終了をブロックする。
export PDCA_STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$PDCA_STATE"
cat | python3 -c '
import sys, json, os, re
state = os.environ["PDCA_STATE"]
need_report = os.path.join(state, "pdca_need_report")
need_ledger = os.path.join(state, "pdca_need_ledger")
need_analyze = os.path.join(state, "pdca_need_analyze")
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
    # python(3) で実際に score.py/report.py を実行する形のみ検知（grep/echo/別行言及では誤爆しない）
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*score\.py", cmd):
        touch(need_report); touch(need_ledger); touch(need_analyze)
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*report\.py", cmd):
        rm(need_report)
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*analyze\.py", cmd):
        rm(need_analyze)  # 深掘りバッテリー N1〜N6 実行で旗が下りる（2026-06-12 まこさん「手抜き分析できない仕組み」）
elif tn in ("Edit", "Write", "MultiEdit"):
    fp = ti.get("file_path", "") or ""
    if fp.endswith("ledger.md"):
        rm(need_ledger)
'
exit 0

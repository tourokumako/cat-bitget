#!/bin/bash
# PostToolUse on WebSearch|WebFetch — L-236 物理強制経路 ＋ 検索ログ記録（2026-06-15 まこさん承認）。
# 役割:
#   - last_websearch.timestamp : 任意の web 活動の recency（旧来・後方互換で維持）
#   - last_webfetch.timestamp  : WebFetch（一次ソース精読）の recency
#   - search_log.txt           : 1件1行（epoch \t tool \t query \t domains \t url）
#       = (a) まこさんが事後に「裏取り（固有名詞狙い撃ち）になってないか」を見れる透明化
#         (b) check_websearch_before_design_write.sh が「検索回数・跨いだソース種別・精読回数」を数える土台
STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$STATE"
NOW=$(date +%s)
echo "$NOW" > "$STATE/last_websearch.timestamp"

INPUT=$(cat)
printf '%s' "$INPUT" | NOW="$NOW" STATE="$STATE" python3 -c '
import sys, json, os
from urllib.parse import urlparse
now = os.environ["NOW"]; state = os.environ["STATE"]
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
tn = d.get("tool_name", "") or ""
ti = d.get("tool_input", {}) or {}
log = os.path.join(state, "search_log.txt")
def esc(s): return str(s).replace("\t", " ").replace("\n", " ").strip()
if tn == "WebSearch":
    q = esc(ti.get("query", ""))
    doms = ",".join(ti.get("allowed_domains", []) or []) or "-"
    with open(log, "a") as f:
        f.write(f"{now}\tSearch\t{esc(q)}\t{esc(doms)}\t-\n")
elif tn == "WebFetch":
    url = ti.get("url", "") or ""
    host = (urlparse(url).netloc or "-")
    with open(log, "a") as f:
        f.write(f"{now}\tFetch\t-\t{esc(host)}\t{esc(url)}\n")
    with open(os.path.join(state, "last_webfetch.timestamp"), "w") as f:
        f.write(now)
' 2>/dev/null
exit 0

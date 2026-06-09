#!/usr/bin/env bash
# PreToolUse(Edit|Write): ledger.md / strat_v9ml_design.md に「経緯・失敗のログ」を書く違反(文書マップ §8.2)を物理ブロック。
# cat_requirements §8.2: ledger=結果/原因3分類/改善/採用or破棄 だけ ／ strat_v9ml_design=設計の決定事項 だけ。
#   経緯・学び・失敗の物語は session_log_YYYYMMDD.md へ・教訓は lessons_active.md へ。
# 2026-06-09 まこさん指示（CC が ledger に経緯を書き連ねた違反 L-257 を受けて）。
cat | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = d.get("tool_input", {}) or {}
fp = ti.get("file_path", "") or ""
if not (fp.endswith("ledger.md") or fp.endswith("strat_v9ml_design.md")):
    sys.exit(0)
text = ti.get("new_string", "") or ti.get("content", "") or ""
# 経緯・失敗のログに特有の語（結果/原因/改善/判定・設計の決定事項 には本来不要）
ng = ["やらかし","叱ら","激怒","すみません","再演","busy-loop","トークン浪費","失敗の物語",
      "勝手に解釈","勝手に変更","勝手にいじ","読んだフリ","court混入","悪魔的","の物語"]
hit = [w for w in ng if w in text]
if hit:
    is_ledger = fp.endswith("ledger.md")
    where = "ledger.md" if is_ledger else "strat_v9ml_design.md（設計書）"
    role = "結果/原因3分類/改善/採用or破棄 だけ" if is_ledger else "設計の決定事項 だけ"
    sys.stderr.write(
        "⛔ 文書マップ §8.2 違反ブロック: %s に「経緯・失敗のログ」を書こうとしています。\n"
        "   検出語: %s\n"
        "   %s は %s。経緯・学び・失敗の物語は session_log_YYYYMMDD.md へ、教訓は lessons_active.md へ書いてください。\n"
        "   （ledger/設計書を読む次セッションが経緯で混乱する＝引き継ぎ事故を防ぐための物理ゲート。L-257）\n"
        % (where, "/".join(hit), where, role)
    )
    sys.exit(2)
sys.exit(0)
'

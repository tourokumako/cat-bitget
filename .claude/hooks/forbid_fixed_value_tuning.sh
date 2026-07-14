#!/bin/bash
[ -f "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/pdca_fast_mode" ] && exit 0  # [fast-mode] process hook を一時無効化（touch/rm pdca_fast_mode で切替・safety hook には入れない・2026-07-16）
# 固定値調整の物理禁止（まこさん命令 2026-06-12・L-261/E20 再演防止）
#
# 対象: scripts/priority_rebuild/*.py への Write/Edit のうち、戦略パラメータの「手置き候補値スイープ」
#       （大文字定数 = 数値2個以上のタプル/リスト）を含み、かつ ML（lightgbm）を使わないもの → block。
# 趣旨: レバーは ML 場面別学習（学習で値・切れ目を出す）。固定値の比較で1つ選ぶ実験は禁止。
#       ML が選ぶ離散アクションメニュー（lightgbm を含むスクリプト）は対象外。
# 例外: まこさんがチャットで明示 GO した場合のみ `# fixed-value-approved: まこさんGO YYYY-MM-DD` を
#       ファイルに記載して通す（GO なしでマーカーを書くのは類型 G・虚偽）。
#       別ディレクトリ（/tmp 等）への退避実装での回避も禁止（cc_role §1.4.6.2 回避禁止）。
INPUT=$(cat)
RES=$(echo "$INPUT" | python3 -c "
import sys, json, re
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
path = ti.get('file_path', '')
text = (ti.get('content') or '') + (ti.get('new_string') or '')
if 'scripts/priority_rebuild' not in path or not path.endswith('.py'):
    print('OK'); sys.exit(0)
if 'fixed-value-approved' in text or 'lightgbm' in text:
    print('OK'); sys.exit(0)
pat = re.compile(r'^[A-Z][A-Z0-9_]*\s*=\s*[\(\[]\s*-?\d[\d_.]*\s*,\s*-?\d', re.M)
m = pat.search(text)
print('NG:' + m.group(0).strip() if m else 'OK')
" 2>/dev/null)
if [[ "$RES" == NG:* ]]; then
    echo "⛔ BLOCKED: 固定値調整（手置き候補値スイープ）の疑い → ${RES#NG:}" >&2
    echo "固定値の比較で1つ選ぶ実験は禁止（まこさん 2026-06-12）。レバーは ML 場面別学習で実装する。" >&2
    echo "ML スクリプト（lightgbm 使用）の離散アクションメニューは対象外。正当な非戦略定数なら小文字に。" >&2
    echo "例外はまこさん明示 GO 後に fixed-value-approved マーカー（GO なしで付けるのは類型G）。" >&2
    exit 2
fi
exit 0

#!/bin/bash
# require_counted_number.sh — count_items.py の記録に無い数を止める（本体は .py）。★2026-11-05 の時点で settings.json に登録していない
# まこさん 2026-11-05「今後あらゆる場面での数の数え間違いをふせぐように言ったんだけど」
set -u
ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
exec python3 "$ROOT/.claude/hooks/require_counted_number.py"

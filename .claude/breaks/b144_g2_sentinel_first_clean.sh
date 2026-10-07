#!/bin/bash
# EXPECT_RC: 1
# MEANS: G2 の番人が使う構造を、表に沿った1本目（clean[0]）に戻すと、番人が「差し替えられる材料が構造に無い」で落ちる
# EXPECT_MSG: 差し替えられる材料が構造に無い
# b144_g2_sentinel_first_clean — G2 の番人が使う構造を、表に沿った1本目（clean[0]）に戻すと、番人が「差し替えられる材料が構造に無い」で落ちる（工事 g2-sentinel-material-pick-20261007・2026-10-07）
#   守っているもの＝完成の条件の G2（gen_signal_families.py --verify）
#   壊し方＝scripts/priority_rebuild/gen_signal_families.py の中の、下の old を new に置き換える（直す前の形に戻す・承認の前の検査の仮当てで、落ちるのを確かめる）。
#   期待＝gen_signal_families.py --verify が「差し替えられる材料が構造に無い」で落ちる（終了コード 1・落ちたときは検査済みの印を書かない）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
#   ★いまの材料の一覧では、表に沿った1本目の構造に指標の材料が無いので落ちる。一覧が変わると落ちなくなることがある（設計書 7-4）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/gen_signal_families.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    def _first_col_cond(st):\n        conds: list = []\n        _walk_conds(st.get("entry", {}).get("connective", {}), conds)\n        for c in conds:\n            for m in (c.get("material") or []):\n                if "family" in m:\n                    return m\n        return None\n\n    # ★2026-10-07（工事 g2-sentinel-material-pick-20261007・まこさん「A」）＝表に沿っていて、指標の材料を持つ最初の構造を使う。\n    #   直す前は表に沿った1本目（clean[0]）をそのまま使い、材料の一覧が1本 増えただけで（同じ日の RCI5）、\n    #   1本目に指標の材料が無くなり「差し替えられる材料が構造に無い」で止まった（乱数の引き方に頼っていた）。\n    with_col = [st for st in clean if _first_col_cond(st) is not None]\n    if not with_col:\n        raise SystemExit("[番人エラー] 表に沿っていて指標の材料を持つ構造が1本も作れない＝既知答えが作れない")\n    base_st = copy.deepcopy(with_col[0])\n\n    ban_st = copy.deepcopy(base_st)\n'
new = '    base_st = copy.deepcopy(clean[0])\n\n    def _first_col_cond(st):\n        conds: list = []\n        _walk_conds(st.get("entry", {}).get("connective", {}), conds)\n        for c in conds:\n            for m in (c.get("material") or []):\n                if "family" in m:\n                    return m\n        return None\n\n    ban_st = copy.deepcopy(base_st)\n'
if s.count(old) != 1:
    raise SystemExit("[b144_g2_sentinel_first_clean] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/gen_signal_families.py" --verify
finish

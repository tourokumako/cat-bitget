#!/bin/bash
# EXPECT_RC: 1
# MEANS: gen_materials の鍵を拾う口が見る関数を build_catalog に戻す＝写す元の関数に鍵の読みを足しても場所1 が増えず、gen_materials の自己テスト T12 が落ちる
# EXPECT_MSG: T12: 場所1 に架空の数の並びを1つ 足しても件数が1 増えない
# b227_materials_keys_from_catalog — 場所1 の数え方が写す元の関数を見なくなると、gen_materials の自己テストが落ちる（工事 m2c15-catalog-redirect-20261101・やることの表 7-6 の F-6）
#   守っているもの＝7-6 の F-6（測るコマンドは、完成の条件と同じ＝gen_materials.py --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/gen_materials.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '               if isinstance(n, ast.FunctionDef) and n.name == "_catalog_from_config"), None)\n'
new = '               if isinstance(n, ast.FunctionDef) and n.name == "build_catalog"), None)\n'
if s.count(old) != 1:
    raise SystemExit("[b227_materials_keys_from_catalog] 壊す対象（鍵を拾う口が見る関数の名前の行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$F" --selftest
finish

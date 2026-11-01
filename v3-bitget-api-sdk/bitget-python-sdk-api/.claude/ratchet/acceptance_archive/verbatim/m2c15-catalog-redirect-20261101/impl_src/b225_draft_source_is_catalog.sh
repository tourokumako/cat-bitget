#!/bin/bash
# EXPECT_RC: 1
# MEANS: 写すプログラムの catalog_sets の呼び先を build_catalog に戻す＝写す元が indicators.json 自身になり、写すプログラムの自己テストが落ちる
# EXPECT_MSG: ❌ 写す: 写す元は _catalog_from_config で、build_catalog を呼ばない
# b225_draft_source_is_catalog — 写すプログラムの写す元が build_catalog に戻ると、自己テストが落ちる（工事 m2c15-catalog-redirect-20261101・やることの表 7-6 の F-3・F-4）
#   守っているもの＝7-6 の F-3・F-4（測るコマンドは、完成の条件と同じ＝写すプログラムの --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$ROOT/.claude/state/indicator_review/gen_indicators_draft.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    cat = od._catalog_from_config(cfg)                    # 写す元＝設定から列を作る関数（162番まで・161-2 のやることの表 F-4）\n'
new = '    cat = od.build_catalog(cfg)\n'
if s.count(old) != 1:
    raise SystemExit("[b225_draft_source_is_catalog] 壊す対象（catalog_sets の写す元の行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$F" --selftest
finish

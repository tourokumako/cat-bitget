#!/bin/bash
# EXPECT_RC: 1
# MEANS: build_catalog に、設定の古い鍵 rsi_periods を読む行を足す＝構文の木の照らしが当たり、カタログの自己テストが落ちる
# EXPECT_MSG: [材料カタログ] build_catalog が設定の鍵を読んでいる
# b223_catalog_reads_old_key — build_catalog が設定の鍵を読む形に戻ると、カタログの自己テストが落ちる（工事 m2c15-catalog-redirect-20261101・やることの表 7-6 の F-1 の2行目・集約の要件定義書 R6）
#   守っているもの＝7-6 の F-1 の2行目（測るコマンドは、完成の条件と同じ＝observe_diag.py --selftest-catalog）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    _bfl = _band_fee_floor(cfg)\n    C = []\n    for cs in _ind.load().column_sets():\n'
new = '    _bfl = _band_fee_floor(cfg)\n    _zzz_rsi = cfg["rsi_periods"]\n    C = []\n    for cs in _ind.load().column_sets():\n'
if s.count(old) != 1:
    raise SystemExit("[b223_catalog_reads_old_key] 壊す対象（build_catalog の床と列を作る組を回す行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

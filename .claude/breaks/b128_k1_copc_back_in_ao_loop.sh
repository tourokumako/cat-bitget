#!/bin/bash
# EXPECT_RC: 1
# MEANS: K-1 で戻した7種を、AO の for の中へ入れ直すと（修正13 を当てた直後と同じ）、自己テストの K-1 の番人が落ちる
# EXPECT_MSG: ❌ K-1:
# b128_k1_copc_back_in_ao_loop — K-1 で戻した7種を、AO の for の中へ入れ直すと（修正13 を当てた直後と同じ）、自己テストの K-1 の番人が落ちる（工事 m2c15-indicator-six-items-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ K-1:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    for (f_, s_, g_) in cfg["macd_params"]:\n        addf("AO%", f_, s_)\n        addf("APO%", f_, s_)\n        # ★K-1（2026-10-04・工事 m2c15-indicator-six-items-20261004）＝監査 CP60 の修正13 を当てたとき、下の7種が AO の for の中に入り、\n        #   AO の 5・34 と、上の for から漏れた g_ で作られていた（COPC(9,5,34) ほか）。修正13 の前（commit 4656de3）と同じ場所に戻す。\n        addf("COPC", g_, f_, s_)\n        addf("FISHER", f_, g_)\n        addf("FISHERシグナル", f_, g_)\n        addf("KSTシグナル", g_)\n        for n in cfg["stoch_periods"]:\n            addf("KDJ%K", n, g_)\n            addf("KDJ%D", n, g_)\n            addf("KDJ%J", n, g_)\n    # ★AO の教科書の期間（Bill Williams・TradingView の逐語 lengthAO1=5・lengthAO2=34・監査 CP60）。\n    #   macd_params の 12/26 だけだと AO% は PPO と相関 0.9974 の重複になる。\n    for (f_, s_) in cfg.get("ao_params", []):\n        addf("AO%", f_, s_)\n'
new = '    for (f_, s_, g_) in cfg["macd_params"]:\n        addf("AO%", f_, s_)\n        addf("APO%", f_, s_)\n    # ★AO の教科書の期間（Bill Williams・TradingView の逐語 lengthAO1=5・lengthAO2=34・監査 CP60）。\n    #   macd_params の 12/26 だけだと AO% は PPO と相関 0.9974 の重複になる。\n    for (f_, s_) in cfg.get("ao_params", []):\n        addf("AO%", f_, s_)\n        addf("COPC", g_, f_, s_)\n        addf("FISHER", f_, g_)\n        addf("FISHERシグナル", f_, g_)\n        addf("KSTシグナル", g_)\n        for n in cfg["stoch_periods"]:\n            addf("KDJ%K", n, g_)\n            addf("KDJ%D", n, g_)\n            addf("KDJ%J", n, g_)\n'
if s.count(old) != 1:
    raise SystemExit("[b128_k1_copc_back_in_ao_loop] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

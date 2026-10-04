<!-- ARC iter="m2c15-indicator-six-items-20261004" -->

# 設計書｜指標の修正の1回目＝作りの直し。M2-C-15

TARGET: scripts/priority_rebuild/indicator_reference_diag.py, scripts/priority_rebuild/observe_config.json, scripts/priority_rebuild/observe_diag.py, .claude/breaks/b128_k1_copc_back_in_ao_loop.sh, .claude/breaks/b129_htf_bar_close_two_bars.sh, .claude/breaks/b131_industry_map_prev_pivot_gone.sh
NEW_FILE: .claude/breaks/b128_k1_copc_back_in_ao_loop.sh, .claude/breaks/b129_htf_bar_close_two_bars.sh, .claude/breaks/b131_industry_map_prev_pivot_gone.sh
MODEL: .claude/breaks/b127_stage_q_rank_off.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2c15-indicator-six-items-20261004/ok_d1_20261004`・`m2c15-indicator-six-items-20261004/ok_hidden_param_next_work_b_20261004`・`m2c15-indicator-six-items-20261004/ok_k4move_20261004`・`m2c15-indicator-six-items-20261004/ok_k_20261004`・`m2c15-indicator-six-items-20261004/ok_r1_20261004`・`m2c15-indicator-six-items-20261004/ok_rep_nearest_b_20261004`・`m2c15-indicator-six-items-20261004/ok_split_20261004`・`m2c15-indicator-six-items-20261004/okd_d1_20261004`・`m2c15-indicator-six-items-20261004/okd_k4move_20261004`・`m2c15-indicator-six-items-20261004/okd_k8band_20261004`・`m2c15-indicator-six-items-20261004/okd_k_20261004`・`m2c15-indicator-six-items-20261004/okd_r1_20261004`・`m2c15-indicator-six-items-20261004/okd_split_20261004`・`m2c15-indicator-six-items-20261004/req_no_value_in_name_20261004`・`m2c15-indicator-six-items-20261004/req_staged_search_20261004`・`m2c15-indicator-six-items-20261004/req_v9_indicators_on_20261004`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2c15-indicator-six-items-20261004/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-indicator-six-items-20261004 --write`。検出＝`--work m2c15-indicator-six-items-20261004 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=bf3e39fe80c94c18 gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2c15-indicator-six-items-20261004/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2c15-indicator-six-items-20261004/ok_d1_20261004.txt`（まこさんの発言）・`verbatim/m2c15-indicator-six-items-20261004/ok_hidden_param_next_work_b_20261004.txt`（まこさんの発言）・`verbatim/m2c15-indicator-six-items-20261004/ok_k4move_20261004.txt`（まこさんの発言）・`verbatim/m2c15-indicator-six-items-20261004/ok_k_20261004.txt`（まこさんの発言）・`verbatim/m2c15-indicator-six-items-20261004/ok_r1_20261004.txt`（まこさんの発言）・`verbatim/m2c15-indicator-six-items-20261004/ok_rep_nearest_b_20261004.txt`（まこさんの発言）・`verbatim/m2c15-indicator-six-items-20261004/ok_split_20261004.txt`（まこさんの発言）・`verbatim/m2c15-indicator-six-items-20261004/okd_d1_20261004.txt`（まこさんが OK した CC の文）・`verbatim/m2c15-indicator-six-items-20261004/okd_k4move_20261004.txt`（まこさんが OK した CC の文）・`verbatim/m2c15-indicator-six-items-20261004/okd_k8band_20261004.txt`（まこさんが OK した CC の文）・`verbatim/m2c15-indicator-six-items-20261004/okd_k_20261004.txt`（まこさんが OK した CC の文）・`verbatim/m2c15-indicator-six-items-20261004/okd_r1_20261004.txt`（まこさんが OK した CC の文）・`verbatim/m2c15-indicator-six-items-20261004/okd_split_20261004.txt`（まこさんが OK した CC の文）・`verbatim/m2c15-indicator-six-items-20261004/req_no_value_in_name_20261004.txt`（まこさんの発言）・`verbatim/m2c15-indicator-six-items-20261004/req_staged_search_20261004.txt`（まこさんの発言）・`verbatim/m2c15-indicator-six-items-20261004/req_v9_indicators_on_20261004.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝611 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_d1_20261004` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_hidden_param_next_work_b_20261004` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_k4move_20261004` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_k_20261004` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_r1_20261004` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_rep_nearest_b_20261004` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_split_20261004` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_d1_20261004` | V01〜V45（45 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_k4move_20261004` | V01〜V11（11 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_k8band_20261004` | V01〜V13（13 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_k_20261004` | V01〜V22（22 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_r1_20261004` | V01〜V05（5 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_r1_20261004` | V06〜V19（14 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V20〜V25（6 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V26〜V30（5 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V31〜V45（15 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V46〜V52（7 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V53〜V59（7 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V60〜V66（7 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V67〜V68（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V69〜V70（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V71〜V74（4 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V75〜V76（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V77〜V78（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V79〜V84（6 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V85〜V93（9 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V94〜V99（6 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V100〜V101（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V102〜V103（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V104〜V107（4 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V108〜V113（6 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V114〜V258（145 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V259〜V267（9 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V268〜V273（6 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V274〜V282（9 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V283〜V289（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V290〜V291（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V292〜V293（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V294〜V298（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V299〜V309（11 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V310〜V330（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V331〜V336（6 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V337〜V406（70 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_r1_20261004` | V407〜V410（4 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `okd_split_20261004` | V01〜V20（20 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `req_no_value_in_name_20261004` | V01〜V16（16 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `req_staged_search_20261004` | V01〜V60（60 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `req_v9_indicators_on_20261004` | V01〜V07（7 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
指標の修正の1回目です。壊れている所を戻す直しだけを行います。中身は3つです。①前回当てた修正13 で AO の for の中に入った7種（COPC・FISHER ほか）を、修正13 の前のパラメータに戻す（K-1）。②上位足の値が5分足1本ぶん遅れて届く所を、今の形と直した形を切り替えられるようにする（K-8・修正68）。③前回足した前期間pivot の3種を、業界のライブラリとの対応表に足す（今は足し忘れで、観察の道具の自己テストが落ちる）。指標の名前に値を入れる直しと、値違いの材料を足す直しは、1件も入れません（まこさん 2026-10-04「指標名に閾値やパラメータの値を固定で入れて、指標数を増やすという解決策はやめてほしい」）。材料の一覧の本数は変わりません。最後に表を作り直し、自己テスト・G2・H2 を取り直します。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 修正13 で AO の for の中に入った7種（K-1） | `grep -n -A2 'in cfg.get("ao_params"' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、AO の for の下に COPC の行が続く。実装の後は、AO% の行だけ（COPC ほかは macd の for に戻る） | 1477:    for (f_, s_) in cfg.get("ao_params", []): ⏎ 1478-        addf("AO%", f_, s_) ⏎ 1479-        addf("COPC", g_, f_, s_)（終了コード 0） |
| 上位足のずらしの切り替え（K-8） | `grep -n htf_shift_mode v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json` | 実装の前は、無い。実装の後は、設定と注記が在り、値は now（今と同じ） | （終了コード 1） |
| 業界のライブラリとの対応表の前期間pivot（G-2） | `grep -n '"前期間pivot' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py` | 実装の前は、系統の一覧の行だけ（業界の対応表に無いので、観察の道具の自己テストが、業界のライブラリとの突き合わせの検査で落ちる）。実装の後は、業界の対応表の行が増える | 1291:_r(r"close vs 前期間pivotPP%", "前期間pivotPP", ⏎ 1295:_r(r"close vs 前期間pivotR1%", "前期間pivotR1", ⏎ 1298:_r(r"close vs 前期間pivotS1%", "前期間pivotS1", ⏎ 4599:    "前期間pivotPP": dict(k="構造・位置"), "前期間pivotR1": dict(k="構造・位置"), "前期間pivotS1": dict(k="構造・位置"),（終了コード 0） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

［自動］印のファイル・型の表・格子と範囲
<!-- ACC_MATERIALS_START hash=27bccc2869a2aa6f gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`indicator_switch.json`・`signal_families.json`・`search_limits.json`。

**探す指標＝印がオンの 141種**（印を切り替えると、この一覧も設計も変わります）。

```
ADX・DI差・MACD線%・MACDヒスト%・MACDシグナル線%・RSI・ROC・Stoch%K・Stoch%D・MFI・CMF・OBV傾き・転換線・基準線・EMA傾き・ATR%・BB%b・BB幅・realized_vol・Donchian幅・volume_ratio・swing高値距離・swing安値距離・高値からの経過バー・安値からの経過バー・形スコア・W字・fractal高値距離%・fractal安値距離%・高値切り上げ幅%・安値切り上げ幅%・構造破断距離%・close vs EMA・close vs SMA・close vs VWAP・Keltner上・Keltner下・n本高値・n本安値・pivotPP・pivotR1・pivotS1・fib位置・POC・VAH・VAL・MMI・S-Rタッチ1時間ATR・S-Rタッチ数・AO%・CCI・ER・KST・KSTシグナル・PPO・PPOシグナル・PPOヒスト・PVO・PVOシグナル・PVOヒスト・SMC_SWEEP・SQZ_ON・STC・STCstoch・StochRSI%K・StochRSI%D・TRIX・TRIXシグナル・TRIXヒスト・TSI・TSIシグナル・TSIヒスト・UO・close vs ALMA%・close vs DEMA%・close vs FWMA%・close vs HILO%・close vs HMA%・close vs HT_TRENDLINE%・close vs HWMA%・close vs JMA%・close vs KAMA%・KAMA傾き%・close vs LINREG%・close vs LRb%・close vs MAMA%・close vs FAMA%・close vs MCGD%・close vs MIDPOINT%・close vs MIDPRICE%・close vs MMAR%・close vs PWMA%・close vs RAINBOW%・close vs RMA%・close vs SINWMA%・close vs SSF%・close vs SWMA%・close vs T3%・close vs TEMA%・close vs TRIMA%・close vs TSF%・close vs VIDYA%・close vs VWMA%・close vs WMA%・WMA傾き%・close vs ZLMA%・AROONU・AROOND・AROONOSC・CHOP・close vs CKSPl%・close vs CKSPs%・DPO%・close vs PMAX%・close vs PSAR%・PSAR加速・PSAR反転・close vs SAREXT%・VHF・VTXP・VTXM・EFI比・EOM比・NVI傾き・PVT傾き・MAD比・stdev%・close vs MEDIAN%・close vs ABER_ZG%・ABER位置・close vs ACCBL%・close vs ACCBU%・close vs CE_L%・close vs CE_S%・HWC位置・HWC幅%・MASSI・THERMO%・TR%・UI・HT_DCPHASE
```

**別枠の材料**

| 別枠 | 印がオンのもの |
|---|---|
| レンジ幾何 | W%・帯内位置% |
| 需給 | CVD・L-S比・taker_ls |
| 時間帯 | 時刻・曜日 |

**役割ごとに使える系統と時間足（型の表）**

| 役割 | 系統 | 時間足 | レンジ幾何 |
|---|---|---|---|
| env | トレンド・ボラ・時間帯 | 全部 | — |
| location | 構造・位置 | 全部 | 使う |
| sufficiency | ボラ・出来高・需給・オシレーター | 全部 | — |
| trigger | オシレーター・ローソク | 5m・10m・15m | — |

**値の範囲と格子（承認済み・この工事で数字を1つも作らない）**

| 鍵 | 中身 |
|---|---|
| `quantile_grid` | ["q10", "q20", "q30", "q40", "q50", "q60", "q70", "q80", "q90"] |
| `quantile_range` | {"lo": 10, "hi": 90, "kind": "int"} |
| `int_grid` | [3, 6, 12, 24] |
| `int_range` | {"lo": 3, "hi": 24} |
| `state_hold_bars_range` | {"lo": 24, "hi": 288, "kind": "int"} |
| `nest_offset_range` | {"lo": 0, "hi": 1, "kind": "int"} |
| `ref_mult_range` | {"lo": 0.5, "hi": 1.5, "kind": "float", "dec": 2} |
| `hour_range` | {"lo": 6, "hi": 18, "kind": "int"} |
| `material_param_ranges` | （空＝材料カタログの最小〜最大を使う） |

<!-- ACC_MATERIALS_END -->

### 2-3 成績表に載っている本数

［自動］成績表
<!-- ACC_RANKING_START hash=c3db5c4b748433d9 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`material_ranking.json`。

**成績表に載っている列の本数**（札＝強さ・先読み12・執行足より上の時間足だけ）

| 役割 | 上位足の列の本数 | 分離力の高い順に3本 |
|---|---|---|
| env | 1918 | THERMO比__1h（0.725）／TR%__1h（0.717）／CVI7__30m（0.714） |
| location | 1414 | S-Rタッチ数(144,0.0015)__10m（0.359）／S-Rタッチ1時間ATR(144,0.5,21)__10m（0.368）／S-Rタッチ1時間ATR(144,0.5,14)__10m（0.37） |
| sufficiency | 1528 | volume_ratio20__1h（0.757）／volume_ratio50__30m（0.749）／PVO(12,26,9)__15m（0.737） |
| trigger | 250 | TD_SEQ_UP__10m（0.602）／TD_SEQ_DN__15m（0.594）／TD_SEQ_DN__10m（0.589） |

**★この本数は、印がオンの指標だけを数えたものではありません。**組む側は `ranked_materials` を通して引き、その関数が印オフの指標を落とします。

<!-- ACC_RANKING_END -->

### 2-4 いま乱数を使っている場所

［自動］実物のコード
<!-- ACC_RANDOM_START hash=83d74398b13a5184 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`engine_tuner_gen.py` を構文の木で読んだ結果（コメントの中の文字は数えません）。

**乱数を使っている関数＝21個 ／ 使っている回数の合計＝64**

| 関数 | 回数 |
|---|---|
| `_make_exits` | 17 |
| `sample_structure` | 7 |
| `synth_df` | 6 |
| `_exit_indicator_cond` | 4 |
| `_make_cond` | 4 |
| `_pair_materials` | 4 |
| `_pick_material` | 3 |
| `_loose_q` | 2 |
| `_pick_exit_material` | 2 |
| `_thr_band_drawn` | 2 |
| `draw_num` | 2 |
| `draw_param` | 2 |
| `_dc1_side` | 1 |
| `_iv` | 1 |
| `_iv_from` | 1 |
| `_mat_drawn` | 1 |
| `_nv` | 1 |
| `_thr_drawn` | 1 |
| `draw_int` | 1 |
| `draw_q` | 1 |
| `write_kakikudashi` | 1 |

**★乱数を外すのは、入口は M3、出口は M4 です（まこさんが決めた順番）。**この工事で外すかどうかは、設計の中身（4-0・4-20）に書きます。

<!-- ACC_RANDOM_END -->

## 3｜目標と、やらないこと

### 3-1 やらないこと（1件ずつ・理由と出どころ）

［手書き］やることの表の「3-1 やらないこと」
| # | やらないこと | 理由 | 出どころ |
|---|---|---|---|
| 1 | パラメータ（P-5・P-1・P-2・P-3・P-4） | 2回目の工事 | まこさん「分ける」（ok_split_20261004） |
| 2 | 新しい材料（K-3・B-1・S-1・K-7）と検査の直し（K-4） | 3回目の工事（K-4 はまこさん「よい」ok_k4move_20261004） | まこさん「分ける」（ok_split_20261004） |
| 3 | 帯の1時間足の区切りの切り替え（監査 CP60 の修正69） | 3回目の工事（B-1）で作る。測る道具が受け取る帯は E38 の接続が作るので、観察の道具だけを切り替えても一致率で比べられない | まこさんの答え「3回目へ移す」（2026-10-04・案＝okd_k8band_20261004） |
| 4 | 役割と閾値（R-1・T-1） | 4回目の工事 | まこさん「分ける」（ok_split_20261004） |
| 5 | 期間・本数・係数の値を変えること | 2回目で修正対応表から入れる。1回目は今の値のまま | まこさん「分ける」（ok_split_20261004）・全体の表の P-1・P-2 |
| 6 | 監査 CP60 の修正7〜12・30〜34（傾きの本数・HILO の本数・HWMA の係数を名前に出す直し）と RAINBOW傾き | 監査の「直した後の文字」が、指標の名前に値を入れる形で、HILO は値違いの材料を1つ足す形。パラメータを範囲から探せるようにする直しは、名前に値を入れない形を決めてから、別の工事にする | まこさん（2026-10-04・154回目）「指標名に閾値やパラメータの値を固定で入れて、指標数を増やすという解決策はやめてほしい」 |
| 7 | 説明の文だけの直し・%化・MACD の平滑の最初・Keltner の ATR の本数・KST の100倍・TSI の期間・SMC_SWEEP の向きの印 | そのまま（net にも一致率にも効かない） | 読むもの宣言の入れないもの・M2-C-14 の決定 |
| 8 | MMAR を重複として外すか（修正63）・AO%(12,26) を外すか | まこさんが決めるまで入れない | 読むもの宣言の入れないもの・worklog 20261003 §45-7 |
| 9 | 法則の判定の直し・測る道具の直し・段ごとの測定の閾値の1点 | 工事2 | 読むもの宣言の入れないもの・next_step「▶ 次にやること」 |
| 10 | 成績表（material_ranking.json）の作り直し | M2-D-8 で、まこさんの OK の後に走らせる | 読むもの宣言の入れないもの |
| 11 | オフの指標を教科書と照らして直すこと | 今は対応しない | まこさん「オフは現状は対応しなくてよい」（2026-10-04） |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 目的の照合（purpose_check.md）の条件の書き方。この工事は探索の経路のファイル（observe_diag.py・observe_config.json）を書き替えるので、目的ゲートは「変えない」を書かせない。この工事は、閾値・時間足・パラメータの探し方そのものは変えない | 事実だけを書く。閾値＝「COPC・FISHER ほか7種は、今は AO の組の値で作られている。戻した後は、修正13 の前の値の上で閾値を探せる（探し方は今のまま）」。時間足＝「上位足の値を使う時刻を、設定で切り替えられる（初めは今のまま・探す時間足の候補は今のまま）」。パラメータ＝「COPC・FISHER ほか7種のパラメータが、修正13 の前の組に戻る。範囲から探せるようにする直しは、この工事に入っていない」 | enforce_purpose_gate.py の「変えない」の決まり・worklog 20261004 §22 |
| 2 | パラメータを範囲から探せるようにする直しを、指標の名前に値を入れない形で、どう作るか。いまの仕組みは、パラメータを指標の名前の中の数字として持つ。資料のパラメータの数と、いま指標が受け取っている数が違う指標が、使う指標の中に在る（HILO・HWMA・傾き ほか）。151回目に本物へ入れた EMA の傾き（名前に本数を足した）と AO（値違いの組を足した）も、同じ形で残っている | ★決まった（まこさん 2026-10-04「案B」）＝この工事には入れず、次の工事にする。形＝登録の計算式が、パラメータを「名前に出さない引数」で受け取る。何も渡さなければ、今と同じ計算をする。指標の名前・種類の数・材料の列の数は変わらない。写しで確かめた結果＝登録 47種類（次の工事で直す所は 54か所）・名前の違い 0件・何も渡さない列が直す前と同じ 47／47・引数を変えると列が変わる 47／47（道具＝.claude/state/indicator_review/hidden_param_check.py・記録＝session_worklog_20261004.md の §30〜§35）。151回目に本物へ入れた EMA の傾きと AO を、名前に値を入れない形へ戻すことは、次の工事で扱う（まだ調べていない） | まこさん（2026-10-04・154回目）「指標名に閾値やパラメータの値を固定で入れて、指標数を増やすという解決策はやめてほしい」「範囲で探せるという上記要件は絶対」「案B」（ok_hidden_param_next_work_b_20261004） |
| 3 | next_step §6 の70番（移動平均そのものの向きの部品が無い・21件）を、どの回に入れるか | 3回目（新しい材料）に入れる。1回目には入れない | next_step §6 の70番・worklog 20261004 §20 |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、指標の修正の1回目で、壊れている所を戻す直しです。**指標の名前・パラメータの値・材料の本数は変えません。
**①いま何が起きているか。**
- 前回（151回目）に監査 CP60 の修正13（AO の教科書の期間）を当てたとき、後ろの7行が AO の for の中に入りました。そのため COPC・FISHER・FISHERシグナル が、AO の 5・34 の組で作られています（K-1）。
- 上位足の値は、5分足1本ぶん遅れて届いています（監査 CP60 の修正68）。まこさんの決定は「今の形と直した形を切り替えられるようにして比べる」です（K-8）。
- 151回目に足した前期間pivot の3種が、業界のライブラリとの対応表に入っていません。そのため、今の実物の観察の道具の自己テストは、検査10 で落ちています（G-2）。
**②この工事で何が変わるか。**
- K-1：7種を、修正13 の前と同じ macd の for に戻します。
- K-8：設定 htf_shift_mode を足します。初めは now（今と同じ値）です。
- G-2：業界のライブラリとの対応表に、前期間pivot の3種を足します。
- G-1（RCI）：V9 が使う指標のうち、RCI だけが「使わない」の印になっています（indicator_switch.json の off）。参照表の RCI の行の mako の欄に、まこさんの指示の逐語を書いて「使う」にします。指示の逐語は2つです（まこさん 2026-10-04）。1つ目は「V9で使ってる指標は入れるようにしてほしい」です。2つ目は「V９で使ってる指標もいれないと、V9のロジックもengine_tunerで最適化するときに、機能しなくなる」です。名前（RCI7 ほか）と本数（設定 rci_periods の 7・9・26・52）は変えません。印が「使う」に変わるのは、G-1 でオン・オフの表を作り直したときです。
- 自己テストに、K-1 と K-8 の番人を足します。
**③数字はどう変わるか。**材料の一覧の本数は 577 列 → 577 列 で、変わりません。名前が変わるのは 3 種だけです。修正13 で変わってしまった名前が、修正13 の前の名前に戻ります。戻る名前は、COPC(9,5,34) → COPC(9,12,26) と、FISHER(5,9) → FISHER(12,9) と、FISHERシグナル(5,9) → FISHERシグナル(12,9) です。新しい値を名前に入れる直しは在りません。
**④この工事に入れなかったもの。**監査 CP60 の修正7〜12・30〜34（傾きの本数・HILO の本数・HWMA の係数を、名前に出す直し）と RAINBOW傾き は、入れていません。監査の「直した後の文字」が、指標の名前に値を入れる形だからです。パラメータを範囲から探せるようにする直しは、名前に値を入れない形を決めてから、別の工事にします。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、当てる道具 apply_audit_fix.py・観察の道具の自己テスト（observe_diag.py --selftest）・表を作る道具（G-1）・G2・H2 を動かします。
**誰が結果を使うか。**
- 材料の一覧（observe_diag.py の build_catalog）は、engine_tuner が試す範囲（engine_tuner_gen.py の material_ranges）と、成績表を作る道具が読みます。
- 型の表（signal_families.json）・出口の型の表・組み立ての表・オン・オフの表は、engine_tuner が読みます。G-1 で作り直します。
- 成績表（material_ranking.json）は、この工事では作り直しません（Y-4）。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**今の実物（observe_diag.py・indicator_reference_diag.py・observe_config.json）・修正13 の前の版（git 4656de3）・設計書の 4-20。
**書くもの。**
- 当てる（--design）：上の3つのファイルと、新しい壊すプログラム 3本。
- G-1：型の表・出口の型の表・組み立ての表・材料の文書・オン・オフの表。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 指標の名前に値を入れない・指標の数を増やさない | まこさん 2026-10-04「指標名に閾値やパラメータの値を固定で入れて、指標数を増やすという解決策はやめてほしい」 | 名前に値を入れる直しと、値違いの材料を足す直しを、1件も入れません。材料の一覧の本数は変わりません |
| 未来のデータを使わない | 要件定義書 §4.6.H2 | 上位足の切り替えは、自己テストの番人が本物の関数を切り詰めて計算し直して確かめます。既定は now で、今と同じ値です |
| 乱数を使わない | 恒久67番 | 足すのは、設定の切り替え・対応表の行・番人だけです |
| オフの指標を直さない | まこさん「オフは現状は対応しなくてよい」 | オフの指標には触りません |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| observe_diag.py の build_catalog | 材料の一覧。K-1 の7種を macd の for に戻す | 直す |
| observe_diag.py の build_features | 設定 htf_shift_mode が bar_close のときだけ、上位足を5分足1本ぶん早める | 直す |
| observe_diag.py の _insp_close_leak・_insp_resample（検査2） | 上位足の漏れの検査を、2つの形で確かめる | 直す |
| observe_diag.py の selftest_catalog と口 --selftest-catalog | K-1 の番人（COPC・FISHER・FISHERシグナル が macd の組で在る）・K-8 の番人（上位足の切り替えで、切り詰めても値が変わらない・now と値が違う）・参照表の網羅・G-2 の検査10 を、数秒で走らせる軽い口 | 新設 |
| observe_diag.py の selftest | 全体の自己テストから、軽い口 selftest_catalog を呼ぶ | 直す |
| indicator_reference_diag.py | 業界のライブラリとの対応表に前期間pivot の3種を足す | 直す |
| observe_config.json | 上位足の切り替えの設定 | 直す |
| .claude/breaks の新しい壊すプログラム | 直しを1つずつ壊すと、自己テストが決めた番人で落ちるかを見る | 新設 |
- 触る関数は、全部の指示を当てる前と後の構文木を比べて、道具が数えました（下の囲み）。
```
observe_diag.py＝<モジュール直下>・_insp_close_leak・_insp_resample・build_catalog・build_features・selftest・selftest_catalog／indicator_reference_diag.py＝<モジュール直下>
```

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. まこさんの承認の後、当てる前の監査に出します（まこさんが貼った結論の V13）。
2. 全部を当てます（apply_audit_fix.py --design --dry → --design）。当てる道具は、全件を当てる前の実物で照らしてから、番号の順に当てます。1件でも合わなければ1件も当てません。当てた直後に、当てる道具が G2 と H2 を自分で走らせます（apply_audit_fix.py:947〜959）。この時点の G2 は、型の表を作り直す前なので、一致しない見込みです（走らせて確かめてはいません。型の表を作り直す前に G2 を走らせる場面は、写しでは作れないためです）。G2 と H2 は、G-1 の後に取り直します。
3. 照合（verify_design_contract.py --diff）をかけます。関数の中身が変わるので、設計書の SPEC と実物が食い違う見込みです。食い違ったら、gen_acceptance.py --write で設計書を作り直し、承認の打ち直しを1回 お願いします（教訓 L-655）。
4. 軽い口（--selftest-catalog）と壊すプログラムを走らせ、全体の自己テスト（--selftest）を1回 走らせて、出力をそのまま貼ります。
5. G-1：表を作り直します。型の表と出口の型の表は、中身が変わったときだけ、まこさんに再承認していただきます。
6. G-2：範囲の中の値が全部 計算できるかの検査（gen_materials.py の param_range_both_ways）→ G2 → H2（約5分）の順に取り直します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝COPC。いま COPC は、修正13 の後、AO の for の中で (9,5,34) で作られている（修正13 の前は (9,12,26)）。K-1 の後は (9,12,26) に戻り、自己テストの K-1 の番人が「COPC(9,12,26) が材料の一覧に在る」ことを確かめる。材料の一覧の本数は、前と後で同じ。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**探す値の範囲は、この工事では変えません。**engine_tuner が試す範囲は、今と同じです。パラメータを範囲から探せるようにする直しは、この工事に入れていません（4-0 の④）。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**observe_config.json に足すもの。**
- htf_shift_mode（"now"／"bar_close"・初めは "now"）と、その注記。
コマンドの旗を1つ増やします。--selftest-catalog（K-1・K-8・G-2 の番人だけを走らせる軽い口）です。完成の条件が、この旗で走ります。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**
1. 軽い口（K-1・K-8・G-2 の番人）が全部 通る。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog。全体の自己テストも通る。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest。
2. 新しい壊すプログラムが、全部 決めた番人で落ちる。コマンド＝python3 .claude/tools/run_breaks.py --design。
3. 材料の一覧に COPC(9,12,26)・FISHER(12,9)・FISHERシグナル(12,9) が在る（自己テストの K-1 の番人が見る）。
4. 表を作り直した後に G2 が一致する。コマンド＝python3 scripts/priority_rebuild/gen_signal_families.py --verify。続けて H2 を取り直す。コマンド＝python3 scripts/priority_rebuild/leak_causality_diag.py。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| --design の --dry で、当たらない件が出る | 1件も当てずに止まります。まこさんに報告します |
| 自己テストで K-1 の番人が落ちる | COPC・FISHER・FISHERシグナル が macd の組で作られていません。「K-1:」で落ちます |
| 自己テストで K-8 の番人が落ちる | 切り替えのどちらかで、切り詰めると値が変わる（未来参照の疑い）か、now と値が同じ（切り替えが効いていない）です。「K-8:」で落ちます |
| 業界のライブラリとの対応表に足し忘れが残る | 検査10 の番人で落ちます |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**変えません。**COPC・FISHER・FISHERシグナル の名前が、修正13 の前の名前に戻るだけです。カタログの1件の形（名前・計算・向き）は変えません。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**変えません。**

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**既定では変えません。**設定を bar_close にすると、上位足の値を5分足1本ぶん早く使います（足が閉じた5分足の行から使う）。今の形と比べるのは M2-F-10f です（判定には一致率、Entry・Exit には net）。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| 観察の道具の自己テスト（全体） | 124秒 | 写しで当てた後に走らせた実測（r1_draft_build.py の [6]） |
| 軽い口（--selftest-catalog） | 3秒 | 写しで当てた後に走らせた実測（r1_draft_build.py の [6b]） |
| 材料の一覧 | 577 列 → 577 列 | 写しで数えた（r1_draft_build.py の [3]） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**ありません。**全部を --design の1回で当てるので、途中の状態は残りません。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しの道具だけが書きます。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**
- 検査2 の行が「閉じる前のバーへの漏れ（人工データ・15m と 2h・ずらし2種）」になります。
- 自己テストの番人は、落ちたときだけ「K-1:」「K-8:」で始まる行を出します。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **observe_diag.py と observe_config.json は H2 の対象、indicator_reference_diag.py は G2 の対象です。**当てた後に G2 → H2 を取り直します。
2. **成績表（material_ranking.json）は、修正13 の前の名前（COPC(9,12,26) ほか）で持っています。**K-1 で名前が戻るので、成績表の名前と合います。151回目に名前が変わった EMA の傾き4種は、成績表では古い名前のままです（この工事では直しません）。
3. **前からの壊すプログラムが探す文字の数は、当てる前と後で同じです。**道具が数えた相手は、下の囲みです。
```
b104_atr1h_own_tf.sh・b105_atr1h_future_hour.sh・b106_atr1h_no_clip.sh・b107_atr1h_base_not_passed.sh・b108_atr1h_base_wrong_bars.sh・b122_obs_formula_copied.sh・b126_rank_resume_save_off.sh・b55_cyc_key_time_gone.sh・b56_one_min_csv_old.sh・b60_only5_with_others.sh・b61_insp5_bars_kind.sh・b63_tm_bitget_scope.sh・b64_tm_subdir.sh・b65_tm_badtail.sh
```
4. **151回目に本物へ入れた直しのうち、指標の名前に値を入れた物と、値違いの材料を足した物が残っています。**EMA の傾き（名前に本数の 5 を足した・修正1〜6）と、AO（値違いの組 5・34 を足した・修正13〜14）です。この2つを名前に値を入れない形へ直すのは、パラメータを範囲から探せるようにする工事と一緒に行います（3-2 に書きました）。
5. **観察の道具の検査9（距離は在るが向きが無い材料）は、今の実物で正しく照らせていません。**この工事の前からの不具合です（検査9 は報告だけで、落ちない）。next_step の「あとで直すこと」に書き、直す工程を決めます（恒久59番）。

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| observe_diag.py の _insp_lookahead（検査4） | 切り詰めて計算し直して値を比べる形（K-8 の番人） |
| observe_diag.py の selftest の検査4 の番人（わざと未来を見る列を入れる） | 小さなカタログと合成のバーで本物の build_features を呼ぶ形 |
| 壊すプログラム b127 | 壊すプログラムの形 |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=9106e5c40f5a86ad gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1472〜1486行（build_catalog・K-1＝修正13 で AO の for の中に入った7種を、修正13 の前の場所に戻す）
直す前の文字:
~~~
    for (f_, s_, g_) in cfg["macd_params"]:
        addf("AO%", f_, s_)
        addf("APO%", f_, s_)
    # ★AO の教科書の期間（Bill Williams・TradingView の逐語 lengthAO1=5・lengthAO2=34・監査 CP60）。
    #   macd_params の 12/26 だけだと AO% は PPO と相関 0.9974 の重複になる。
    for (f_, s_) in cfg.get("ao_params", []):
        addf("AO%", f_, s_)
        addf("COPC", g_, f_, s_)
        addf("FISHER", f_, g_)
        addf("FISHERシグナル", f_, g_)
        addf("KSTシグナル", g_)
        for n in cfg["stoch_periods"]:
            addf("KDJ%K", n, g_)
            addf("KDJ%D", n, g_)
            addf("KDJ%J", n, g_)

~~~
直した後の文字:
~~~
    for (f_, s_, g_) in cfg["macd_params"]:
        addf("AO%", f_, s_)
        addf("APO%", f_, s_)
        # ★K-1（2026-10-04・工事 m2c15-indicator-six-items-20261004）＝監査 CP60 の修正13 を当てたとき、下の7種が AO の for の中に入り、
        #   AO の 5・34 と、上の for から漏れた g_ で作られていた（COPC(9,5,34) ほか）。修正13 の前（commit 4656de3）と同じ場所に戻す。
        addf("COPC", g_, f_, s_)
        addf("FISHER", f_, g_)
        addf("FISHERシグナル", f_, g_)
        addf("KSTシグナル", g_)
        for n in cfg["stoch_periods"]:
            addf("KDJ%K", n, g_)
            addf("KDJ%D", n, g_)
            addf("KDJ%J", n, g_)
    # ★AO の教科書の期間（Bill Williams・TradingView の逐語 lengthAO1=5・lengthAO2=34・監査 CP60）。
    #   macd_params の 12/26 だけだと AO% は PPO と相関 0.9974 の重複になる。
    for (f_, s_) in cfg.get("ao_params", []):
        addf("AO%", f_, s_)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1472「for (f_, s_, g_) in cfg["macd_params"]:」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1861〜1864行（build_features・上位足のずらしを切り替えられるようにする（既定は今のまま））
直す前の文字:
~~~
                if tf != "5m":
                    s = s.copy()
                    s.index = src.index + pd.Timedelta(TF_RULE[tf])
                    s = s.reindex(bars.index, method="ffill")

~~~
直した後の文字:
~~~
                if tf != "5m":
                    s = s.copy()
                    s.index = src.index + pd.Timedelta(TF_RULE[tf])
                    # ★K-8（監査 CP60 の修正68・まこさん決定 2026-10-04）＝設定 htf_shift_mode が "bar_close" のときだけ、5分足1本ぶん早める
                    #   （今の作りは1本遅れて届く）。どちらも未来は使わない（5分足の行 R は R+5分に閉じるので、閉じた時刻 ≤ R+5分 の上位足だけが当たる）。
                    if cfg.get("htf_shift_mode", "now") == "bar_close":
                        s.index = s.index - (bars.index[1] - bars.index[0])
                    s = s.reindex(bars.index, method="ffill")

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1861「if tf != "5m":」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 3860〜3878行（_insp_close_leak・上位足の漏れの検査を、2つの形で確かめる）
直す前の文字:
~~~
def _insp_close_leak(shift: bool = True) -> list[str]:
    """検査2 の一部＝閉じる前の上位足バーへの漏れ（未来参照）を人工データで確かめる。
    shift=False は番人用＝『足が閉じた時刻へずらす』処理を外した壊れた状態を再現する。"""
    ng = []
    idx = pd.date_range("2026-03-01", periods=288, freq="5min")
    syn = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0,
                        "close": np.arange(288, dtype=float) + 1.0, "volume": 1.0}, index=idx)
    for tf in ("15m", "2h"):
        src = _resample(syn, TF_RULE[tf])
        s = src["close"].copy()
        if shift:
            s.index = src.index + pd.Timedelta(TF_RULE[tf])
        s = s.reindex(syn.index, method="ffill")
        t = idx[30]                                  # 02:30＝どの足でも形成中の時刻
        exp = float(syn["close"].loc[t.floor(TF_RULE[tf]) - pd.Timedelta("5min")])
        got = s.loc[t]
        if pd.isna(got) or float(got) != exp:
            ng.append(f"{tf}: 形成中の足の値が漏れている（t={t} の値 {got} ≠ 閉じた足の close {exp}）")
    return ng

~~~
直した後の文字:
~~~
def _insp_close_leak(shift: bool = True, mode: str = "now") -> list[str]:
    """検査2 の一部＝閉じる前の上位足バーへの漏れ（未来参照）を人工データで確かめる。
    shift=False は番人用＝『足が閉じた時刻へずらす』処理を外した壊れた状態を再現する。
    ★K-8（監査 CP60 の修正68・2026-10-04）＝mode="bar_close" は5分足1本ぶん早める形（build_features の htf_shift_mode と同じ式）。
      どちらの形でも、5分足の行 t で当たるのは「行 t が閉じた時刻までに閉じた上位足」だけであることを、2つの時刻（02:25・02:30）で確かめる。"""
    ng = []
    idx = pd.date_range("2026-03-01", periods=288, freq="5min")
    step = idx[1] - idx[0]
    syn = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0,
                        "close": np.arange(288, dtype=float) + 1.0, "volume": 1.0}, index=idx)
    for tf in ("15m", "2h"):
        src = _resample(syn, TF_RULE[tf])
        s = src["close"].copy()
        if shift:
            s.index = src.index + pd.Timedelta(TF_RULE[tf])
            if mode == "bar_close":
                s.index = s.index - step
        s = s.reindex(syn.index, method="ffill")
        for t in (idx[29], idx[30]):                 # 02:25＝早める形で差が出る時刻／02:30＝どの足でも形成中の時刻
            base = t + step if mode == "bar_close" else t
            exp = float(syn["close"].loc[base.floor(TF_RULE[tf]) - step])
            got = s.loc[t]
            if pd.isna(got) or float(got) != exp:
                ng.append(f"{tf}（{mode}）: 形成中の足の値が漏れている（t={t} の値 {got} ≠ 閉じた足の close {exp}）")
    return ng

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:3860「def _insp_close_leak(shift: bool = True) -> list[str]:」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 3904〜3905行（_insp_resample・検査2 で、ずらし2種とも確かめる）
直す前の文字:
~~~
    leak = _insp_close_leak(shift=True)
    print(f"  閉じる前のバーへの漏れ（人工データ・15m と 2h）: {'なし' if not leak else '検出'}")

~~~
直した後の文字:
~~~
    leak = _insp_close_leak(shift=True) + _insp_close_leak(shift=True, mode="bar_close")   # ★K-8＝ずらし2種
    print(f"  閉じる前のバーへの漏れ（人工データ・15m と 2h・ずらし2種）: {'なし' if not leak else '検出'}")

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:3904「leak = _insp_close_leak(shift=True)」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7324〜7325行（selftest・自己テストの番人で、ずらし2種とも誤検出しないことを見る）
直す前の文字:
~~~
    if _insp_close_leak(shift=True):
        ng.append("検査2 が正しい組み立てで誤検出")

~~~
直した後の文字:
~~~
    if _insp_close_leak(shift=True) or _insp_close_leak(shift=True, mode="bar_close"):   # ★K-8＝ずらし2種とも誤検出しない
        ng.append("検査2 が正しい組み立てで誤検出")

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7324「if _insp_close_leak(shift=True):」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/observe_config.json
直す箇所: 159行（設定・上位足のずらしの切り替えの設定（既定は今のまま））
直す前の文字:
~~~
 "ao_params": [

~~~
直した後の文字:
~~~
 "htf_shift_mode": "now",
 "_htf_shift_mode": "上位足の値をいつから使うか（監査 CP60 の修正68・まこさん決定 2026-10-04＝切り替えて比べる）。now＝今（足の始まり＋足の長さ＝5分足1本遅れて届く）／bar_close＝5分足1本ぶん早める。どちらも未来は使わない。初めは now＝今と同じ値",
 "ao_params": [

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_config.json:159「"ao_params": [」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4901行（<モジュール直下>・自己テストの検査10 が止まる直し忘れ（151回目に当てた修正18〜21 の残り））
直す前の文字:
~~~
    "pivotS1": (("cpr",), "⚠️ 部分的。cpr は S1 を返さない（同上）"),

~~~
直した後の文字:
~~~
    "pivotS1": (("cpr",), "⚠️ 部分的。cpr は S1 を返さない（同上）"),
    # ★G-2（2026-10-04・工事 m2c15-indicator-six-items-20261004）＝監査 CP60 の修正18〜21 で足した教科書の前期間 pivot。151回目に当てたとき、
    #   この対応表に足し忘れ、観察の道具の自己テスト（検査10）が止まっていた。ライブラリの cpr と同じ作りかは照らしていない（定義表の既知答え＝修正20 で確かめる）。
    "前期間pivotPP": ((), "前の UTC の日で固定する教科書の PP。ライブラリの cpr と同じ作りかは照らしていない（定義表の既知答えで確かめる）"),
    "前期間pivotR1": ((), "同上（教科書の R1＝2×PP − 前の期間の安値）"),
    "前期間pivotS1": ((), "同上（教科書の S1＝2×PP − 前の期間の高値）"),

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:4901「"pivotS1": (("cpr",), "⚠️ 部分的。cpr は S1 を返さない（同上）"),」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1063〜1064行（<モジュール直下>・V9 が使う RCI を、使う指標にする（参照表の mako の欄・名前と本数は変えない））
直す前の文字:
~~~
   "順張り値＝+100 で一貫した上昇", "trend", tb=_tb_rci,
   known=lambda p: [(_up(p[0] + 5), [(-1, 100.0, 1e-9)]), (_dn(p[0] + 5), [(-1, -100.0, 1e-9)])])

~~~
直した後の文字:
~~~
   "順張り値＝+100 で一貫した上昇", "trend", tb=_tb_rci,
   known=lambda p: [(_up(p[0] + 5), [(-1, 100.0, 1e-9)]), (_dn(p[0] + 5), [(-1, -100.0, 1e-9)])],
   mako="2026-10-04 まこさん指示「V9で使ってる指標は入れるようにしてほしい」（V9 の P22 が RCI7 と RCI9 のクロスを使う）")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1063「"順張り値＝+100 で一貫した上昇", "trend", tb=_tb_rci,」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7438〜7439行（selftest・全体の自己テストから、K-1・K-8・G-2 の番人（軽い口）を呼ぶ）
直す前の文字:
~~~
    if not any("未来を見る列" in x for x in _ng4):
        ng.append("検査4 がわざと入れた未来参照列（1本先の close）を見逃す")

~~~
直した後の文字:
~~~
    if not any("未来を見る列" in x for x in _ng4):
        ng.append("検査4 がわざと入れた未来参照列（1本先の close）を見逃す")
    ng += selftest_catalog(exit_=False)              # ★K-1・K-8・G-2 の番人（工事 m2c15-indicator-six-items-20261004）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7438「if not any("未来を見る列" in x for x in _ng4):」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 6918〜6919行（selftest・K-1・K-8・G-2 の番人だけを走らせる軽い口を足す（完成の条件・壊すプログラムが測る相手））
直す前の文字:
~~~
def selftest() -> None:
    """この道具が守ると言っていることを機械で確かめる。まこさんはこれを叩けばよい。"""

~~~
直した後の文字:
~~~
def selftest_catalog(exit_: bool = True) -> list:
    """K-1・K-8・G-2 の番人だけを走らせる軽い口（工事 m2c15-indicator-six-items-20261004・2026-10-04）。
    口＝`--selftest-catalog`（完成の条件と壊すプログラム b128・b129・b131 が使う）。全体の自己テスト（selftest）からも呼ぶ。
    手本＝selftest_atr1h（口の形・selftest からの呼び方）。★全体の自己テストは約2分かかり、承認の前の仮当て（A12）で
    完成の条件と壊すプログラムが毎回それを走らせると20分を超えるため、番人だけを切り出した。"""
    cfg = load_config()
    ng = []
    _t3 = np.arange(6000, dtype=float)
    _c3 = pd.Series(100 + np.sin(_t3 / 9.0) * 2 + _t3 * 0.001,
                    index=pd.date_range("2026-03-01", periods=6000, freq="5min"))
    _sb3 = pd.DataFrame({"open": _c3.shift().fillna(_c3.iloc[0]), "high": _c3 + 0.1,
                         "low": _c3 - 0.1, "close": _c3, "volume": 1.0}, index=_c3.index)
    #  ①K-1＝COPC・FISHER・FISHERシグナル は macd_params の組で作る（修正13 の前と同じ）。AO の for に入ると AO の組の名前になる
    _nm_k1 = {nm for nm, _f, _d in build_catalog(cfg)}
    for (_f1, _s1, _g1) in cfg["macd_params"]:
        for _want1 in (f"COPC({_g1},{_f1},{_s1})", f"FISHER({_f1},{_g1})", f"FISHERシグナル({_f1},{_g1})"):
            if _want1 not in _nm_k1:
                ng.append(f"K-1: {_want1} がカタログに無い（macd_params の組で作られていない）")
    #  ②K-8 修正68＝上位足のずらし bar_close でも、本物の build_features を切り詰めて計算し直して値が変わらない（検査4 と同じ機構）。
    #    ★漏れは、上位足の中の決まった位置の5分足でだけ起きる＝最後の「上位足1本ぶん」の5分足を全部 切り詰めて確かめる（15m＝3本・2h＝24本）。
    #    あわせて now と値が違う（切り替えが効いている）
    _cat68 = [("close そのまま", lambda d: d.close, True)]
    for _tf68, _n68 in (("15m", 3), ("2h", 24)):
        _c68 = {**cfg, "timeframes": [_tf68], "warmup_days": 3, "htf_shift_mode": "bar_close"}
        _full68, _m68 = build_features(_sb3, _c68, catalog=_cat68)
        _cols68 = [c for c in _full68.columns if "close そのまま" in str(c)]
        if not _cols68:
            ng.append(f"K-8: 上位足のずらしの番人が列を作れない（{_tf68}）＝測れない")
            continue
        for _t68 in _sb3.index[-_n68:]:
            _tr68, _m68 = build_features(_sb3.loc[:_t68], _c68, catalog=_cat68)
            _x68, _y68 = _full68[_cols68[0]].loc[_t68], _tr68[_cols68[0]].loc[_t68]
            if pd.isna(_x68) != pd.isna(_y68) or (not pd.isna(_x68) and abs(float(_x68) - float(_y68)) > 1e-9 * max(1.0, abs(float(_x68)))):
                ng.append(f"K-8: 上位足のずらし bar_close で、切り詰めると値が変わる（{_tf68}・時点 {_t68}・未来参照の疑い）")
                break
        _now68, _m68 = build_features(_sb3, {**_c68, "htf_shift_mode": "now"}, catalog=_cat68)
        if _now68[_cols68[0]].equals(_full68[_cols68[0]]):
            ng.append(f"K-8: 上位足のずらし bar_close と now の値が同じ（{_tf68}・切り替えが効いていない）")
    #  ④材料の一覧の全部の名前が、参照表で引ける（全体の自己テストの「参照表の網羅」と同じ iref.coverage を呼ぶ）
    _miss = iref.coverage([nm for nm, _f, _d in build_catalog(cfg)])
    if _miss:
        ng.append(f"参照表に無いカタログ列 {len(_miss)} 件: {_miss[:5]}")
    #  ⑤G-2＝業界のライブラリとの対応表に足し忘れが無い（全体の自己テストの検査10 の番人と同じ iref.industry_gap を呼ぶ）
    try:
        import pandas_ta_classic as _pt10
        _ng10 = iref.industry_gap({k: list(v) for k, v in _pt10.Category.items()},
                                  [e["family"] for e in iref.REFS])["ng"]
        if _ng10:
            ng.append(f"検査10 が現状の対応表で不一致を出す（表の直し忘れ）: {_ng10[:3]}")
    except ImportError:
        ng.append("検査10 が使う pandas-ta-classic が入っていない（requirements.txt の版で入れる）")
    if exit_:
        for x in ng:
            print(f"  ❌ {x}")
        print(f"  K-1・K-8・G-2 の番人（--selftest-catalog）: ❌ {len(ng)} 件")
        raise SystemExit(1 if ng else 0)
    return ng


def selftest() -> None:
    """この道具が守ると言っていることを機械で確かめる。まこさんはこれを叩けばよい。"""

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:6918「def selftest() -> None:」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7966行（<モジュール直下>・軽い口の旗 --selftest-catalog を受ける）
直す前の文字:
~~~
    if "--selftest-atr1h" in sys.argv:                # ★T-A1〜T-A5 だけを（設計書 m2e-bundle2-20260926・壊すプログラム b104〜b107 が使う）

~~~
直した後の文字:
~~~
    if "--selftest-catalog" in sys.argv:              # ★K-1・K-8・G-2 の番人だけを（工事 m2c15-indicator-six-items-20261004・壊すプログラム b128・b129・b131 が使う）
        selftest_catalog()                            # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）
    if "--selftest-atr1h" in sys.argv:                # ★T-A1〜T-A5 だけを（設計書 m2e-bundle2-20260926・壊すプログラム b104〜b107 が使う）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7966「if "--selftest-atr1h" in sys.argv:                # ★T-A1〜T-A5 だけを（設計書 m2e-bundle2-20260926・壊すプログラム b104〜b107 が使う）」
状態: 確定

#### 実装 12
対象のファイル: .claude/breaks/b128_k1_copc_back_in_ao_loop.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
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

~~~
根拠の抜き書き: .claude/breaks/b127_stage_q_rank_off.sh:1「#!/bin/bash」
状態: 確定

#### 実装 13
対象のファイル: .claude/breaks/b129_htf_bar_close_two_bars.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 上位足のずらし bar_close を5分足2本ぶん早める（形成中の上位足を使う）と、切り詰め再計算の番人が落ちる
# EXPECT_MSG: ❌ K-8: 上位足のずらし bar_close で
# b129_htf_bar_close_two_bars — 上位足のずらし bar_close を5分足2本ぶん早める（形成中の上位足を使う）と、切り詰め再計算の番人が落ちる（工事 m2c15-indicator-six-items-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ K-8: 上位足のずらし bar_close で」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '                        s.index = s.index - (bars.index[1] - bars.index[0])\n'
new = '                        s.index = s.index - 2 * (bars.index[1] - bars.index[0])\n'
if s.count(old) != 1:
    raise SystemExit("[b129_htf_bar_close_two_bars] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b127_stage_q_rank_off.sh:1「#!/bin/bash」
状態: 確定

#### 実装 14
対象のファイル: .claude/breaks/b131_industry_map_prev_pivot_gone.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 業界のライブラリとの対応表から前期間pivot の3行を外す（151回目の直し忘れと同じ）と、検査10 の番人が落ちる
# EXPECT_MSG: ❌ 検査10 が現状の対応表で不一致を出す
# b131_industry_map_prev_pivot_gone — 業界のライブラリとの対応表から前期間pivot の3行を外す（151回目の直し忘れと同じ）と、検査10 の番人が落ちる（工事 m2c15-indicator-six-items-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/indicator_reference_diag.py の中の、下の old を new に置き換える（r1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ 検査10 が現状の対応表で不一致を出す」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicator_reference_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    # ★G-2（2026-10-04・工事 m2c15-indicator-six-items-20261004）＝監査 CP60 の修正18〜21 で足した教科書の前期間 pivot。151回目に当てたとき、\n    #   この対応表に足し忘れ、観察の道具の自己テスト（検査10）が止まっていた。ライブラリの cpr と同じ作りかは照らしていない（定義表の既知答え＝修正20 で確かめる）。\n    "前期間pivotPP": ((), "前の UTC の日で固定する教科書の PP。ライブラリの cpr と同じ作りかは照らしていない（定義表の既知答えで確かめる）"),\n    "前期間pivotR1": ((), "同上（教科書の R1＝2×PP − 前の期間の安値）"),\n    "前期間pivotS1": ((), "同上（教科書の S1＝2×PP − 前の期間の高値）"),\n'
new = ''
if s.count(old) != 1:
    raise SystemExit("[b131_industry_map_prev_pivot_gone] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b127_stage_q_rank_off.sh:1「#!/bin/bash」
状態: 確定

<!-- ACC_IMPL_END -->

### 4-A この節に何を書いたか（一覧）

［自動］項目の正本と、OK された案・やることの表の有無
| 番号 | 段 | 項目 | 書いたか |
|---|---|---|---|
| 4-0 | 必ず | この仕組みは何か（全体・一続きの文章で書く） | 書いた |
| 4-1 | 必ず | システムの境界（誰が動かし、誰が結果を使うか） | 書いた |
| 4-2 | 必ず | 入力と出力（受け取るもの・出すもの・その形） | 書いた |
| 4-6 | 条件 | 制約（従う決まりの全件と、その出どころ） | 書いた |
| 4-3 | 必ず | 部品と責任の割り当て（どの部品が何をやるか） | 書いた |
| 4-4 | 必ず | 処理の流れ（うまくいったとき、何がどの順に起きるか） | 書いた |
| 4-19 | 必ず | 通しの例（最初から最後まで、1件を追いかけた例） | 書いた |
| 4-7 | 条件 | 探索の範囲（決める値と、その探し方＝範囲・並び・本数） | 書いた |
| 4-9 | 条件 | 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗） | 書いた |
| 4-12 | 必ず | 出る結果の姿（完成したとき、何がどう表示されるか） | 書いた |
| 4-5 | 必ず | 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか） | 書いた |
| 4-8 | 条件 | データ構造（表や JSON の列と中身を、新しく作るか・変えるか） | 書いた |
| 4-10 | 条件 | 保存先（出したものをどこに置くか・上書きか、書き足すか） | 書いた |
| 4-11 | 条件 | 時刻の扱い（時間帯・足の区切りをどこで切るか） | 書いた |
| 4-14 | 条件 | 性能（どれくらい時間が掛かり、どれくらい容量を使うか） | 書いた |
| 4-15 | 条件 | 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか） | 書いた |
| 4-16 | 条件 | セキュリティ（人に見せてはいけない値と、書き換えられては困る記録） | 書いた |
| 4-17 | 省ける | ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか） | 書いた |
| 4-13 | 必ず | 影響範囲（この直しで、ほかのどれが壊れるか） | 書いた |
| 4-18 | 省ける | 再利用（手本にした、既にあるものの形） | 書いた |
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 14 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 監査 CP60 の修正7〜12・30〜34 と RAINBOW傾き を、この工事に入れない | 監査の「直した後の文字」は、指標の名前に値を入れる形で、HILO は値違いの材料を1つ足す形。まこさんの指示（2026-10-04）に反する | 監査の文のまま当てる（取り下げた） |
| 2 | 全部を --design の1回で当てる | 承認の前の仮当て（A12）は設計書の 4-20 だけを当てる | 2段に分けて当てる |
| 3 | E38 の上位足のずらし（e38_logic_parts.py:66-69 の _al）は、この工事では変えない | 監査 CP60 の修正68 は「直すならそろえる」。まこさんの決定は「切り替えて比べる」で、比べた後に決める | 観察の道具と一緒に E38 も変える |
| 4 | K-1・K-8 の番人を自己テストに足す | 検査2 の _insp_close_leak は式の写しを試すだけで、本物の build_features を見ない。だから切り替えの形を、本物の関数を切り詰めて確かめる番人が要る | 番人を足さずに検査2 の直しだけにする |
| 5 | 番人を軽い口 selftest_catalog と旗 --selftest-catalog にまとめ、完成の条件と壊すプログラムはその口で測る | 全体の自己テストは 124秒かかる。完成の条件と壊すプログラムが毎回それを走らせると、承認の前の仮当て（A12）と承認が長くなる。手本は selftest_atr1h と --selftest-atr1h（口の形と、全体の自己テストからの呼び方） | 完成の条件を全体の自己テストで測る |
| 6 | K-8 の番人は、最後の「上位足1本ぶん」の5分足を全部 切り詰めて確かめる | 上位足の漏れは、上位足の中の決まった位置の5分足でだけ起きる。最初に書いた番人（検査4 の3つの時点）は、3つとも同じ位置に当たり、壊すプログラム b129 の壊し方を見逃した（写しで実測） | 検査4 の3つの時点で確かめる |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=097a684c62c58d3e gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b128_k1_copc_back_in_ao_loop.sh` | #1 | K-1 で戻した7種を、AO の for の中へ入れ直す（修正13 を当てた直後と同じ） |
| `b129_htf_bar_close_two_bars.sh` | #2 | bar_close のずらしを5分足2本ぶんにする（形成中の上位足を使う） |
| `b131_industry_map_prev_pivot_gone.sh` | #3 | 対応表から前期間pivot の3行を外す（151回目の直し忘れと同じ） |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | この工事の後も、パラメータを範囲から探せない指標が残る（6項目の3番を、この工事だけでは満たさない） | 名前に値を入れない形を決めてから、別の工事で直す（3-2 に書いた） |
| 2 | K-8 の番人は合成のバー（約20日）で確かめる。本物の5分足での確かめは H2 の範囲（既定の now だけ） | bar_close に切り替えて比べる前（M2-F-10f）に、H2 をその設定で走らせる |
| 3 | list_fix_sites.py の --instr は、指示の中身に在る文を、どこに在っても「書いたとおり」に数える | K-1 が直ったかは、自己テストの K-1 の番人と壊すプログラム b128 で確かめる（list_fix_sites.py の数では確かめない） |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（--design） | 1分未満 | 当てる道具は1秒未満で終わった（151回目） |
| 全体の自己テスト | 124秒 | 4-14 |
| 軽い口と壊すプログラム | 軽い口1回 3秒 | 写しで壊すプログラムを並べて走らせた実測は 3秒（r1_draft_build.py の [7]） |
| G-1 の表の作り直し | 未測定（走らせる前に小さく測る） | — |
| G2 → H2 | 約30秒 → 約5分 | 10/03 の取り直し |
| まこさんの承認 | 設計書2回（当てる前・SPEC を作り直した後）。型の表と出口の型の表は、中身が変わったときだけ再承認 | 4-4 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝①修正13 の「直した後の文字」が後ろの7行を含めておらず、当てる道具はそのまま当てた。当てた後に構造を見る検査が無かった。②修正68 は、まこさんの決定で切り替えにした。③151回目に前期間pivot を足したとき、業界のライブラリとの対応表に足し忘れた。自己テストを走らせなかったので気づかなかった。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。壊れていた7種の材料が、修正13 の前の値に戻ります。

**③ root か symptom か**＝root です。K-1 は修正13 の前の場所に戻し、K-8 は切り替えの設定と、本物の関数を切り詰めて確かめる番人を足し、G-2 は足し忘れの3行を足します。

**④ ベースアップ**＝監査 CP60（修正13・修正68 の文）・上位足の値は足が閉じた時刻から使う（要件定義書 §4.6.H2）。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。値は今の値のままです。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝指標の修正の1回目（壊れを戻す直し）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。条件をつなぐものではなく、壊れた材料を戻す直しです |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 私は探す値を1つも決めていません。値は今の値のままで、点の一覧を足す直しは在りません |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **K-8 の番人は本物の5分足で確かめるか** | 確かめません。合成のバーで、本物の関数を切り詰めて確かめます。本物の5分足での確かめは、切り替えて比べる前に H2 をその設定で走らせて行います |
| **list_fix_sites.py の数で K-1 が直ったと言えるか** | 言えません（6-2 の3）。自己テストの K-1 の番人と b128 で確かめます |
| **この工事で、パラメータは範囲から探せるようになるか** | なりません（6-2 の1）。別の工事で直します |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=8199925baea8363a gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝observe_diag.py・indicator_reference_diag.py・observe_config.json と、新しい壊すプログラムを【7-8】に書いた。主なファイルは observe_diag.py。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝observe_diag.py）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム（NEW_FILE）。手本は b127（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝151回目は、修正13 を当てた後に構造を見ずに進み、7種が AO の for に入った。この工事は、写しで構造の検査（修正13 の前と比べ、どの指示にも無いのに囲みが変わった文が0）を通し、自己テストに K-1 の番人を足した。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | H2 が走らせる案に、新しい切り替えの形（bar_close）は入らない（設定の既定は now）。だから H2 で測るとは書かず、自己テストの番人に、本物の関数の切り詰めの確かめを入れた。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | この工事は engine_tuner_exec.py・engine_tuner_gen.py を直さないので、その行番号を指す文書は無い。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、探す文字の数が当てる前と後で同じことを道具が数えた（4-13 の3）。走らせるコマンドの旗も変えない（旗を消す直しは無い）。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 新しい壊すプログラムが測るのは observe_diag.py --selftest-catalog で、軽い口は合成のバーだけを使い、ファイルに書かない。本物の結果の置き場には書かない。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 新しく足す関数は selftest_catalog の1つ。触る関数は全部 DESIGN_CONTRACT の impl_functions に書いた（道具が当てる前と後の構文木で数えた）。must_use の名前は、当てた後の関数の中に在ることを道具が ast で照らした。observe_diag.py の触る関数＝<モジュール直下>・_insp_close_leak・_insp_resample・build_catalog・build_features・selftest。observe_diag.py の触る関数＝selftest_catalog。indicator_reference_diag.py の触る関数＝<モジュール直下>。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足すコマンドの旗は --selftest-catalog の1つで、完成の条件がこの旗で走る。新しい設定の htf_shift_mode は、軽い口の番人が2つの値の両方で通す。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2c15-indicator-six-items-20261004）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝観察の道具の自己テスト（K-1・K-8 の番人・検査10・参照表の網羅・材料の往復）と、新しい壊すプログラム（わざと壊して落ちるか）。写しで走らせ、全部 通った。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | K-1＝COPC・FISHER・FISHERシグナル が macd の組で在る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | K-1 で戻した7種を、AO の for の中へ入れ直す（修正13 を当てた直後と同じ） | `b128_k1_copc_back_in_ao_loop.sh` | — | **未着手** |
| 2 | K-8 修正68＝上位足のずらし bar_close でも、切り詰めて値が変わらない | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | bar_close のずらしを5分足2本ぶんにする（形成中の上位足を使う） | `b129_htf_bar_close_two_bars.sh` | — | **未着手** |
| 3 | G-2＝業界のライブラリとの対応表に前期間pivot の3種が在る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | 対応表から前期間pivot の3行を外す（151回目の直し忘れと同じ） | `b131_industry_map_prev_pivot_gone.sh` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=6e8521d6ad13e16e gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/observe_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `selftest_catalog` | （この関数は実物に無い） |
| `_insp_close_leak` | 3860 |
| `build_features` | 1832 |
| `build_catalog` | 1317 |
| `selftest` | 6918 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 178件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=e10bc3d204ba4808 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/observe_diag.py",
  "_impl_file の意味": "照らす相手は実在するファイル。材料の一覧（build_catalog）・上位足のずらし（build_features）・帯（build_range_geometry）・自己テストが在る、観察の道具を照らす。",
  "impl_functions": {
    "scripts/priority_rebuild/observe_diag.py": [
      "<モジュール直下>",
      "_insp_close_leak",
      "_insp_resample",
      "build_catalog",
      "build_features",
      "selftest",
      "selftest_catalog"
    ],
    "scripts/priority_rebuild/indicator_reference_diag.py": [
      "<モジュール直下>"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数（実装の指示を全部 当てる前と後の構文木を関数ごとに比べて、r1_proposal_build.py が数えた）。",
  "self_check_calls": [
    "selftest_catalog",
    "_insp_close_leak",
    "build_features",
    "build_catalog",
    "selftest"
  ],
  "_self_check_calls の意味": "実装の後の observe_diag.py に在るはずの、この工事が触る関数の名前。",
  "must_use": {
    "selftest_catalog": [
      "load_config",
      "build_catalog",
      "build_features"
    ],
    "selftest": [
      "selftest_catalog",
      "_insp_close_leak"
    ],
    "_insp_resample": [
      "_insp_close_leak"
    ]
  },
  "_must_use の意味": "自己テストが K-1・K-8 の番人で呼ぶ関数と、検査2・検査8 が切り替えの2つの形を呼ぶ関数（r1_proposal_build.py が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は材料の作りと切り替えの設定を直すだけ。外から読む一覧の形（カタログの1件の形・参照表の欄）は変えない。",
  "generated_from": {
    "impl_functions": "当てる前と後の関数ごとの構文木の差（r1_proposal_build.py が数えた）",
    "must_use": "ast で照らした",
    "spec_lists": "空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/observe_diag.py",
 "public_functions": {
  "load_config": [],
  "find_material": [],
  "make_material": [],
  "build_catalog": [
   "make_material"
  ],
  "load_1m": [],
  "insp5_frame": [
   "load_1m"
  ],
  "build_features": [
   "build_catalog",
   "load_1m"
  ],
  "load_demand": [],
  "build_range_geometry": [],
  "rank_separation": [],
  "rank_separation_independent": [
   "rank_separation"
  ],
  "trajectory": [],
  "post_exit": [],
  "neighbors": [],
  "observe": [
   "build_catalog",
   "build_features",
   "grow_search",
   "load_config",
   "load_demand",
   "mech_thresholds",
   "next_actions",
   "verdict"
  ],
  "next_actions": [],
  "grow_search": [
   "round_trip_cost"
  ],
  "mech_thresholds": [],
  "round_trip_cost": [],
  "plan_scene": [
   "build_catalog",
   "load_config",
   "round_trip_cost"
  ],
  "observe_scene": [
   "build_features",
   "load_config",
   "load_demand",
   "rank_separation_independent",
   "round_trip_cost"
  ],
  "plan": [
   "build_catalog",
   "load_config"
  ],
  "verdict": [],
  "inspect_data": [
   "build_catalog",
   "load_config"
  ],
  "check_materials": [
   "build_catalog",
   "load_config"
  ],
  "check_materials_meta": [
   "build_catalog",
   "load_config"
  ],
  "rank_materials_for_regime": [
   "build_catalog",
   "build_features",
   "rank_separation"
  ],
  "rank_regime": [
   "add_demand_to_ranking",
   "build_catalog",
   "load_config"
  ],
  "rank_demand_for_regime": [
   "load_demand",
   "rank_separation"
  ],
  "merge_demand_into_ranking": [],
  "add_demand_to_ranking": [
   "load_config",
   "merge_demand_into_ranking",
   "rank_demand_for_regime"
  ],
  "selftest_rank_demand": [
   "load_demand",
   "merge_demand_into_ranking",
   "rank_demand_for_regime",
   "rank_separation"
  ],
  "selftest_rank_resume": [
   "build_catalog",
   "load_config",
   "rank_materials_for_regime"
  ],
  "selftest_insp5": [
   "build_catalog",
   "insp5_frame",
   "load_1m",
   "load_config"
  ],
  "selftest_atr1h": [
   "build_catalog",
   "build_features",
   "load_config"
  ],
  "selftest": [
   "build_catalog",
   "build_features",
   "build_range_geometry",
   "load_config",
   "load_demand",
   "make_material",
   "mech_thresholds",
   "next_actions",
   "rank_separation",
   "rank_separation_independent",
   "round_trip_cost",
   "selftest_atr1h",
   "selftest_insp5",
   "selftest_rank_demand",
   "selftest_rank_resume",
   "verdict"
  ],
  "build_parser": []
 },
 "constants": {
  "ONE_MIN_CSV": "data/BTCUSDT-1m-binance-taker-2023-06-01_2026-06-30.csv",
  "BARS_CSV": "data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv",
  "_INSP_STEP_NG_PCT": 5.0,
  "_INSP_STEP_WARN_PCT": 0.5,
  "_H6_RTOL": 1e-08,
  "_DUP_NEAR": 0.999,
  "_DUP_SAME": 0.99999,
  "_DUP_CALC_ROWS": 60000,
  "_DUP_ROWS": 20000,
  "_V9_MATCH_SAME": 0.99999,
  "_V9_MATCH_NEAR": 0.99,
  "_V9_RECORD_SINCE": "2026-07-28 00:00",
  "DEMAND_RANK_TF": "5m"
 },
 "cli_flags": [
  "--selftest",
  "--selftest-atr1h",
  "--selftest-insp5",
  "--selftest-rank-demand",
  "--selftest-rank-resume"
 ]
}
```

<!-- ACC_SPEC_END -->

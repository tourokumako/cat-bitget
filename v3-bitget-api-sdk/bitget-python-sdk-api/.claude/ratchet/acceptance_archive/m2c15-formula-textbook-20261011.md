<!-- ARC iter="m2c15-formula-textbook-20261011" -->

# 設計書｜K-3c 計算式の違い＝計算式が教科書と違う15種に、教科書の版を今の版を残して足す。M2-C-15

TARGET: .claude/memory/regime_detection_kb.md, scripts/priority_rebuild/indicator_reference_diag.py, scripts/priority_rebuild/observe_diag.py, .claude/breaks/b160_dpo_tb_lib_shift.sh, .claude/breaks/b161_thermo_orig_abs.sh, .claude/breaks/b162_stochrsi_raw_smoothed.sh, .claude/breaks/b163_trix_ema_signal_sma.sh, .claude/breaks/b164_rvol_rv_mean_subtracted.sh, .claude/breaks/b165_ssf_avg_single_input.sh, .claude/breaks/b166_sqz_carter_scalar_fixed.sh
NEW_FILE: .claude/breaks/b160_dpo_tb_lib_shift.sh, .claude/breaks/b161_thermo_orig_abs.sh, .claude/breaks/b162_stochrsi_raw_smoothed.sh, .claude/breaks/b163_trix_ema_signal_sma.sh, .claude/breaks/b164_rvol_rv_mean_subtracted.sh, .claude/breaks/b165_ssf_avg_single_input.sh, .claude/breaks/b166_sqz_carter_scalar_fixed.sh
MODEL: .claude/breaks/b142_rci_list_stale.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2c15-formula-textbook-20261011/ok_k3c_proposal_20261011`・`m2c15-formula-textbook-20261011/okd_k3c_proposal_20261011`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2c15-formula-textbook-20261011/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-formula-textbook-20261011 --write`。検出＝`--work m2c15-formula-textbook-20261011 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=f9dec5ce2c655439 gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2c15-formula-textbook-20261011/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2c15-formula-textbook-20261011/ok_k3c_proposal_20261011.txt`（まこさんの発言）・`verbatim/m2c15-formula-textbook-20261011/okd_k3c_proposal_20261011.txt`（まこさんが OK した CC の文）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝685 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_k3c_proposal_20261011` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_k3c_proposal_20261011` | V01〜V09（9 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_k3c_proposal_20261011` | V10〜V72（63 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V73〜V77（5 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V78〜V83（6 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V84〜V93（10 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V94〜V100（7 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V101〜V109（9 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V110〜V119（10 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V120〜V121（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V122〜V123（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V124〜V126（3 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V127〜V128（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V129〜V130（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V131〜V136（6 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V137〜V145（9 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V146〜V151（6 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V152〜V153（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V154〜V155（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V156〜V157（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V158〜V163（6 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V164〜V498（335 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V499〜V510（12 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V511〜V517（7 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V518〜V527（10 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V528〜V534（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V535〜V536（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V537〜V538（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V539〜V543（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V544〜V554（11 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V555〜V575（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V576〜V585（10 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V586〜V679（94 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_k3c_proposal_20261011` | V680〜V684（5 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
監査 CP60 は、今の材料のうち15種の計算式が教科書と違うと指摘しました。DPO は、教科書を時点 t で作れる形に書くと「k本前の終値 − いまの n本平均」ですが、今の材料は「いまの終値 − k本前の n本平均」です。THERMO は、教科書（Elder）では前の足から外へはみ出した幅だけで内はらみ足は 0 ですが、今の材料は絶対値を取ります。SQZ_ON は、Carter の作りではケルトナーの中心を代表値段の SMA・幅を ATR にしますが、今の材料は終値の SMA と真の値幅の SMA です。StochRSI は原式ではならしませんが、今の材料は SMA3 でならします。TRIX のシグナルは教科書では EMA ですが、今の材料は単純移動平均です。realized_vol は教科書の実現ボラは平均を引きませんが、今の材料は引きます。SSF は Ehlers の式では入力を2本の平均にしますが、今の材料はしません。TRIMA は TA-Lib では偶数の本数で窓が違い、VIDYA は CMO の本数を別に持ちます。HT_TRENDLINE・MAMA・FAMA は Ehlers の入力が (高値＋安値)/2 ですが、今の材料は終値です。Aberration は原作が80本・標準偏差2倍のボリンジャーバンドですが、今の材料はライブラリ独自の作りです。まこさんは、今の版を残し、教科書の版を別の材料として足して、後で比べる形を決めました（K-3 の「A」）。K-7 の決定で、THERMO% に EMA でならした版も足します。作りの5点（新しいパラメータは名前に出さない引数・EMA の本数の最初の値は既定の値・式は監査の本文と原典の逐語から・Aberration 原作は別の材料・対応表と既知答えは K-3b と同じ形）にも「進めて良い」をいただきました。この工事は、その15種を観察の道具と参照表に足します。前から在る列の値は1本も変えません。どちらの版が良いかを比べるのは、この工事ではなく M2-F-10f です。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 教科書の DPO の登録（F-1） | `grep -n -F '_reg("DPO教科書%"' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、今の DPO% の登録の後ろに在る | （終了コード 1） |
| Carter の作りのスクイーズ（F-1・F-2） | `grep -n -F 'def _sqz_carter' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、今の SQZ_ON の登録の後ろに在る | （終了コード 1） |
| 足す種類の参照表の登録（F-1・F-3） | `grep -n -F 'mako=MAKO_K3C' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py` | 実装の前は、無い。実装の後は、足した種類の登録の行に在る | （終了コード 1） |
| ta の DPOIndicator の対応（F-1） | `grep -n -F '"DPOIndicator": ("DPO教科書%", "DPO%")' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py` | 実装の前は、無い。実装の後は、TA_CLASS_MAP の中に在る | （終了コード 1） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

［自動］印のファイル・型の表・格子と範囲
<!-- ACC_MATERIALS_START hash=8dc7b5eb6f7cf59f gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`indicator_switch.json`・`signal_families.json`・`search_limits.json`。

**探す指標＝印がオンの 160種**（印を切り替えると、この一覧も設計も変わります）。

```
ADX・DI差・MACD線%・MACDヒスト%・MACDシグナル線%・RSI・ROC・Stoch%K・Stoch%D・MFI・CMF・OBV傾き・転換線・基準線・RCI・EMA傾き・ATR%・BB%b・BB幅・realized_vol・Donchian幅・volume_ratio・swing高値距離・swing安値距離・高値からの経過バー・安値からの経過バー・形スコア・W字・fractal高値距離%・fractal安値距離%・高値切り上げ幅%・安値切り上げ幅%・構造破断距離%・close vs EMA・close vs SMA・close vs VWAP・close vs VWAP典型・当日VWAP・Keltner上・Keltner下・n本高値・n本安値・pivotPP・pivotR1・pivotS1・前期間pivotPP・前期間pivotR1・前期間pivotS1・前週pivotPP・前週pivotR1・前週pivotS1・fib位置・POC・VAH・VAL・前日POC・前日VAH・前日VAL・当日POC・当日VAH・当日VAL・MMI・S-Rタッチ1時間ATR・S-Rタッチ数・W字確定谷・S-Rタッチ確定数・S-Rタッチ確定1時間ATR・SMC_SWEEP確定・AO%・CCI・ER・KST・KSTシグナル・PPO・PPOシグナル・PPOヒスト・PVO・PVOシグナル・PVOヒスト・SMC_SWEEP・SQZ_ON・STC・STCstoch・StochRSI%K・StochRSI%D・TRIX・TRIXシグナル・TRIXヒスト・TSI・TSIシグナル・TSIヒスト・UO・close vs ALMA%・close vs DEMA%・close vs FWMA%・close vs HILO%・close vs HMA%・close vs HT_TRENDLINE%・close vs HWMA%・close vs JMA%・close vs KAMA%・KAMA傾き%・close vs LINREG%・close vs LRb%・close vs MAMA%・close vs FAMA%・close vs MCGD%・close vs MIDPOINT%・close vs MIDPRICE%・close vs MMAR%・close vs PWMA%・close vs RAINBOW%・close vs RMA%・close vs SINWMA%・close vs SSF%・close vs SWMA%・close vs T3%・close vs TEMA%・close vs TRIMA%・close vs TSF%・close vs VIDYA%・close vs VWMA%・close vs WMA%・WMA傾き%・close vs ZLMA%・AROONU・AROOND・AROONOSC・CHOP・close vs CKSPl%・close vs CKSPs%・DPO%・close vs PMAX%・close vs PSAR%・PSAR加速・PSAR反転・close vs SAREXT%・VHF・VTXP・VTXM・EFI比・EOM比・NVI傾き・PVT傾き・MAD比・stdev%・close vs MEDIAN%・close vs ABER_ZG%・ABER位置・close vs ACCBL%・close vs ACCBU%・close vs CE_L%・close vs CE_S%・HWC位置・HWC幅%・MASSI・THERMO%・TR%・UI・HT_DCPHASE
```

**別枠の材料**

| 別枠 | 印がオンのもの |
|---|---|
| レンジ幾何 | W%・下半分位置・帯内位置% |
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
| `material_param_ranges` | {"ADX": [{"kind": "int", "lo": 7, "hi": 21}], "DI差": [{"kind": "int", "lo": 7, "hi": 21}], "MACD線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}], "MACDヒスト%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "MACDシグナル線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "転換線": [{"kind": "int", "lo": 5, "hi": 12}], "基準線": [{"kind": "int", "lo": 13, "hi": 26}], "EMA傾き": [{"kind": "int", "lo": 9, "hi": 200}], "KSTシグナル": [{"kind": "int", "lo": 9, "hi": 9}], "PPO": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOシグナル": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOヒスト": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "TRIX": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TSI": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIシグナル": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIヒスト": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "KAMA傾き%": [{"kind": "int", "lo": 7, "hi": 10}], "WMA傾き%": [{"kind": "int", "lo": 20, "hi": 200}], "AROONU": [{"kind": "int", "lo": 7, "hi": 288}], "AROOND": [{"kind": "int", "lo": 7, "hi": 25}], "AROONOSC": [{"kind": "int", "lo": 7, "hi": 25}], "VTXP": [{"kind": "int", "lo": 14, "hi": 30}], "VTXM": [{"kind": "int", "lo": 14, "hi": 30}], "RSI": [{"kind": "int", "lo": 2, "hi": 21}], "ROC": [{"kind": "int", "lo": 9, "hi": 24}], "Stoch%K": [{"kind": "int", "lo": 5, "hi": 21}], "Stoch%D": [{"kind": "int", "lo": 5, "hi": 21}], "MFI": [{"kind": "int", "lo": 10, "hi": 20}], "CMF": [{"kind": "int", "lo": 20, "hi": 36}], "OBV傾き": [{"kind": "int", "lo": 10, "hi": 20}], "BB%b": [{"kind": "int", "lo": 10, "hi": 50}, {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}], "volume_ratio": [{"kind": "int", "lo": 20, "hi": 50}], "CCI": [{"kind": "int", "lo": 7, "hi": 21}], "PVO": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOシグナル": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOヒスト": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "StochRSI%K": [{"kind": "int", "lo": 7, "hi": 21}], "StochRSI%D": [{"kind": "int", "lo": 7, "hi": 21}], "DPO%": [{"kind": "int", "lo": 14, "hi": 40}], "EFI比": [{"kind": "int", "lo": 10, "hi": 20}], "EOM比": [{"kind": "int", "lo": 10, "hi": 20}], "NVI傾き": [{"kind": "int", "lo": 10, "hi": 20}], "PVT傾き": [{"kind": "int", "lo": 10, "hi": 20}], "ATR%": [{"kind": "int", "lo": 5, "hi": 21}], "BB幅": [{"kind": "int", "lo": 10, "hi": 50}, {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}], "realized_vol": [{"kind": "int", "lo": 10, "hi": 50}], "Donchian幅": [{"kind": "int", "lo": 10, "hi": 20}], "MMI": [{"kind": "int", "lo": 200, "hi": 500}], "ER": [{"kind": "int", "lo": 7, "hi": 21}], "CHOP": [{"kind": "int", "lo": 7, "hi": 21}], "VHF": [{"kind": "int", "lo": 7, "hi": 28}], "MAD比": [{"kind": "int", "lo": 20, "hi": 50}], "stdev%": [{"kind": "int", "lo": 10, "hi": 50}], "UI": [{"kind": "int", "lo": 7, "hi": 21}], "高値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "安値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "形スコア": [{"kind": "int", "lo": 24, "hi": 96}], "W字": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.0, "hi": 0.06, "dec": 3}], "fractal高値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "fractal安値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "高値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "安値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "構造破断距離%": [{"kind": "int", "lo": 2, "hi": 3}], "close vs EMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs SMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs VWAP": [{"kind": "int", "lo": 288, "hi": 288}], "Keltner上": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "Keltner下": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "n本高値": [{"kind": "int", "lo": 10, "hi": 50}], "n本安値": [{"kind": "int", "lo": 10, "hi": 50}], "pivotPP": [{"kind": "int", "lo": 288, "hi": 288}], "pivotR1": [{"kind": "int", "lo": 288, "hi": 288}], "pivotS1": [{"kind": "int", "lo": 288, "hi": 288}], "fib位置": [{"kind": "int", "lo": 14, "hi": 96}], "S-Rタッチ1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}], "S-Rタッチ数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}], "close vs ALMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs DEMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs FWMA%": [{"kind": "int", "lo": 10, "hi": 20}], "close vs HMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs JMA%": [{"kind": "int", "lo": 3, "hi": 80}], "close vs KAMA%": [{"kind": "int", "lo": 7, "hi": 30}], "close vs LINREG%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs LRb%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs MCGD%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs MIDPOINT%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MIDPRICE%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MMAR%": [{"kind": "int", "lo": 10, "hi": 35}], "close vs PWMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs RAINBOW%": [{"kind": "int", "lo": 2, "hi": 2}, {"kind": "int", "lo": 1, "hi": 10}], "close vs RMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SINWMA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs SSF%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SWMA%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs T3%": [{"kind": "int", "lo": 8, "hi": 200}], "close vs TEMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TRIMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TSF%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs VIDYA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs VWMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs WMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs MEDIAN%": [{"kind": "int", "lo": 4, "hi": 200}], "RCI": [{"kind": "int", "lo": 5, "hi": 52}], "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}], "W字確定谷": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.0, "hi": 0.06, "dec": 3}], "S-Rタッチ確定数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}], "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}]} |

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
| 1 | 足した版と今の版を比べること | 比べるのは M2-F-10f。この工事は材料を足すだけ | 監査 CP60 の修正45〜53 の補足 |
| 2 | PMAX 原作の版 | 原典のコードの全文が資料に無く、新しく Web を調べない | まこさん「進めて良い」の3 |
| 3 | 名前に出さない引数を範囲で探すこと | 値を渡すのは工事2（M2-F-10b） | まこさん「進めて良い」の1 |
| 4 | TSIヒスト・STC の期間の比べ方（修正49 の残り） | K-3c の16種に入っていない | okd_k3_split_20261007 |
| 5 | BB%b の範囲を 80 まで広げること | 範囲は資料の規則で決める。原作の 80本は名前に出さない引数で持つ | まこさん「進めて良い」の4 |
| 6 | 成績表（material_ranking.json）の作り直し | M2-D-8。増える列は、作り直すまで段の候補の順位に出ない | K-3b と同じ |
| 7 | K-4 から先の工事 | この工事の後 | まこさん 2026-10-10 |
| 8 | 監査に出す前のチェックの自己テストの P7-1 の落ち | この工事の前から在る。next_step §6 に積んである | worklog 20261007 §11 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | SQZ_ON_Carter の ATR の作り | Wilder の ATR（最初の n 本の真の値幅の単純平均を種に (前×(n−1)＋今)/n）。監査の文は「幅を ATR」で、ライブラリの版が「真の値幅の SMA」だと指摘している＝ATR の標準の作り（参照表の _wilder と同じ）にする | 監査 CP60 の修正47・表 62「平滑のしかた（Keltner の中心を終値の SMA・幅を真の値幅の SMA）」 |
| 2 | THERMO_EMA% の元（何を EMA でならすか） | 原作の温度計（THERMO原作%）をならす。教科書の版を足す工事なので、EMA の元も教科書の形にする | K-7 の決定（ok_k7_pivot_thermo_20261007）・監査 CP60 の修正45 |
| 3 | ta の DPOIndicator の対応 | （DPO教科書%・DPO%）の2つにする。教科書の版に対応させ、今の DPO% は比べるために残す。DPO% を外すと「使う」から落ちる | 全体の表 G-1（まこさん「すべて案どおりでよい」）・監査 CP60 の修正37 の補足 |
| 4 | 監査の出し方 | この工事と2つ目の工事を、工事ごとに1通ずつ実装の監査に出す（依頼書の道具は1つの工事に1通・K-3a・K-3b と同じ） | 教訓 L-670・L-672・まこさん「2通に分ける」（K-3a） |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、計算式が教科書と違う15種に、教科書の版を今の版を残して別の材料として足す工事です。**監査 CP60 は、DPO・Aberration・THERMO・SQZ_ON・StochRSI・TRIX のシグナル・realized_vol・SSF・TRIMA・VIDYA・HT_TRENDLINE・MAMA・FAMA の今の作りが教科書と違うと指摘しました（修正37・45・47〜53）。まこさんは、今の版を残して教科書の版を足し、後で比べる形を決めました（K-3 の「A」）。K-7 の決定で、THERMO% に EMA でならした版も足します。どちらが良いかを比べるのは M2-F-10f で、この工事は材料を足すだけです。
**①足す15種（名前・作り・出どころ）。**
| 材料の名前 | 作り | 出どころ |
|---|---|---|
| DPO教科書%(n) | k本前の終値 − いまの n本平均（k=n/2+1）を終値で割って%化。今の DPO% は「いまの終値 − k本前の n本平均」 | 修正37・45 の補足の式・StockCharts「Price - X-period SMA from {X/2 + 1} periods in the future」 |
| ABER原作位置 | 終値の80本 SMA ± 2σ（ddof 0）の帯の中の位置（%b と同じ作り）。本数と倍率は名前に出さない引数（80・2.0） | 修正45・71・georgepruitt.com「a breakout system based on Bollinger bands with a period length of 80 days and two standard deviations」 |
| THERMO原作% | max(max(High − PrevHigh, 0), max(PrevLow − Low, 0)) を終値で割って%化（内はらみ足は 0）。今の THERMO% は絶対値 | 修正45 の直した後の文字・修正58 |
| THERMO_EMA% | THERMO原作% の温度計を EMA でならして%化。EMA の本数は名前に出さない引数（最初の値 20） | K-7 の決定（ok_k7_pivot_thermo_20261007）・資料の既定 20（motivewave）と 22（tradingview） |
| SQZ_ON_Carter | ボリンジャー（終値の SMA ± 2σ）がケルトナー（代表値段 (H+L+C)/3 の SMA ± 1.5×ATR（Wilder））の内側なら 1。4つの数は名前に出さない引数（20・2.0・20・1.5） | 修正47・StockCharts「Carter uses 20 periods for the moving average and ATR, and 1.5 for the ATR multiplier」 |
| StochRSI素%K(n) | 原式の値（ならさない）＝ライブラリの stochrsi の k を 1 にしたもの | 修正48・StockCharts「StochRSI = (RSI - Lowest Low RSI) / (Highest High RSI - Lowest Low RSI)」 |
| TRIX_EMAシグナル(n,g)・TRIX_EMAヒスト(n,g) | TRIX を g 本の EMA（種＝最初の g 本の単純平均）でならしたシグナルと、その差 | 修正49・StockCharts「The signal line is a 9-day EMA of the TRIX.」 |
| realized_vol_rv(n) | √(Σr²/n)×100（平均を引かない） | 修正50 の直した後の文字・Wikipedia「RV(n) = Σ r²」 |
| close vs SSF平均%(n) | Ehlers の2極のスーパースムーザーで、入力を (c + c[1])/2 にしたもの | 修正51・linnsoft「Filt = c1*(Close + Close[1]) / 2 + c2*Filt[1] + c3*Filt[2];」 |
| close vs TRIMA_TA%(n) | TA-Lib の TRIMA（偶数の n＝SMA(SMA(x, n/2), n/2+1)・奇数は今の版と同じ） | 修正52・ta-lib.org「even: SMA(SMA(x,period/2),period/2+1)」 |
| close vs VIDYA_CMO%(n) | CMO の本数 m を n と別に持つ VIDYA。m は名前に出さない引数（最初の値 9） | 修正52・ta-lib.org「n = optInTimePeriod, m = optInCMOPeriod」 |
| close vs HT_TRENDLINE_HL%・close vs MAMA_HL%・close vs FAMA_HL% | 入力を (高値＋安値)/2 にしたもの（ライブラリの関数に渡す入力だけを変える） | 修正53・MAMA.pdf「Inputs: Price((H+L)/2), FastLimit(.5), SlowLimit(.05);」 |
- 今の版は1文字も変えません（前から在る列の値の違い0本）。新しい名前は作りの違いだけを表し、名前に数字は増やしません（名前に出る軸は元の種類と同じ）。
- 名前に出さない引数の最初の値は、資料の既定（Carter の4つ・原作の 80・2.0・CMO の 9）か、ライブラリの既定（EMA の本数 20）です。範囲で探すのは工事2（M2-F-10b）です。
**②既知答え（手で計算できる合成の足）と独立の実装。**
| 材料 | 合成の足 | 答え |
|---|---|---|
| DPO教科書% | 平らな足／1本ごとに 1 ずつ上げ続ける足（_up） | 0／((n−1)/2 − k) ÷ 最後の終値 × 100（k=n/2+1） |
| realized_vol_rv | 平らな足／終値が毎本 0.1% ずつ増える足 | 0／100×ln(1.001)（今の版は 0＝平均を引くと消える） |
| THERMO原作% | 平らな足／最後の足だけ内はらみ（高値 100.5・安値 99.5） | 0／0（今の版は 0.5） |
| THERMO_EMA%・HT_TRENDLINE_HL%・MAMA_HL%・FAMA_HL% | 平らな足 | 0 |
| 上の全部と SQZ_ON_Carter・StochRSI素%K・TRIX_EMA 2種・SSF平均・TRIMA_TA・VIDYA_CMO・ABER原作位置 | 観察の道具の自己テストの値動き | 参照表の独立の実装（素直な繰り返し）と最大差 1e-6 以内 |
**③オン・オフの表（使う）の違い（G-1 の試し＝写しで作り直した・道具が数えた）。**
使う 160 種 → 175 種。増えた 15 種＝ABER原作位置・DPO教科書%・SQZ_ON_Carter・StochRSI素%K・THERMO_EMA%・THERMO原作%・TRIX_EMAシグナル・TRIX_EMAヒスト・close vs FAMA_HL%・close vs HT_TRENDLINE_HL%・close vs MAMA_HL%・close vs SSF平均%・close vs TRIMA_TA%・close vs VIDYA_CMO%・realized_vol_rv。減った 0 種。
**④この工事で増える材料の名前（道具が数えた）。**
ABER原作位置・DPO教科書%20・DPO教科書%48・SQZ_ON_Carter・StochRSI素%K14・StochRSI素%K21・StochRSI素%K7・StochRSI素%K9・THERMO_EMA%・THERMO原作%・TRIX_EMAシグナル(14,9)・TRIX_EMAシグナル(21,9)・TRIX_EMAシグナル(7,9)・TRIX_EMAシグナル(9,9)・TRIX_EMAヒスト(14,9)・TRIX_EMAヒスト(21,9)・TRIX_EMAヒスト(7,9)・TRIX_EMAヒスト(9,9)・close vs FAMA_HL%・close vs HT_TRENDLINE_HL%・close vs MAMA_HL%・close vs SSF平均%20・close vs SSF平均%200・close vs SSF平均%50・close vs TRIMA_TA%20・close vs TRIMA_TA%200・close vs TRIMA_TA%50・close vs VIDYA_CMO%20・close vs VIDYA_CMO%200・close vs VIDYA_CMO%50・realized_vol_rv20・realized_vol_rv50
**⑤この工事の設定（今の資料から写し直しても変わらない＝設定の指示は無い）。**
観察の道具の設定 observe_config.json と探す範囲 search_limits.json は、この工事では変えません。
**⑥ta の対応表（TA_CLASS_MAP）。**
全体の表 G-1 のとおり、ta の DPOIndicator（k本前の終値 − SMA）を DPO教科書% に対応させます。今の DPO% も比べるために残すので、対応は（DPO教科書%・DPO%）の2つにします。
**⑦2つ目の工事で写す設定（G-1 の試しの後に、資料から写し直すと変わる行・道具が数えた）。**
- observe_config.json（13 行）
```
-  "RCI": [[5], [7], [9], [26], [52]]
+  "RCI": [[5], [7], [9], [26], [52]],
+  "DPO教科書%": [[20]],
+  "TRIX_EMAシグナル": [[15, 9]],
+  "TRIX_EMAヒスト": [[15, 9]],
+  "close vs TRIMA_TA%": [[10]]
-  "HWC位置": {"スキャル": [[0.2, 0.1, 0.1, 0.1, 1.0]], "デイトレ": [[0.2, 0.1, 0.1, 0.1, 1.0]]}
+  "HWC位置": {"スキャル": [[0.2, 0.1, 0.1, 0.1, 1.0]], "デイトレ": [[0.2, 0.1, 0.1, 0.1, 1.0]]},
+  "SQZ_ON_Carter": {"スキャル": [[20, 2, 20, 1.5]], "デイトレ": [[20, 2, 20, 1.5]]},
+  "close vs MAMA_HL%": {"スキャル": [[0.5, 0.05]], "デイトレ": [[0.5, 0.05]]},
+  "close vs FAMA_HL%": {"スキャル": [[0.5, 0.05]], "デイトレ": [[0.5, 0.05]]}
- "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0", "close vs VWAP典型＝範囲が1点のまま（全部の軸）：288", "当日VWAP＝最初の値も範囲も決まらない", "前日POC＝最初の値も範囲も決まらない", "前日VAH＝最初の値も範囲も決まらない", "前日VAL＝最初の値も範囲も決まらない", "当日POC＝最初の値も範囲も決まらない", "当日VAH＝最初の値も範囲も決まらない", "当日VAL＝最初の値も範囲も決まらない"],
+ "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0", "close vs VWAP典型＝範囲が1点のまま（全部の軸）：288", "当日VWAP＝最初の値も範囲も決まらない", "前日POC＝最初の値も範囲も決まらない", "前日VAH＝最初の値も範囲も決まらない", "前日VAL＝最初の値も範囲も決まらない", "当日POC＝最初の値も範囲も決まらない", "当日VAH＝最初の値も範囲も決まらない", "当日VAL＝最初の値も範囲も決まらない", "StochRSI素%K＝範囲が1点のまま（全部の軸）：14・3・3", "close vs SSF平均%＝範囲が1点のまま（全部の軸）：10・2", "close vs MAMA_HL%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA_HL%＝範囲が1点のまま（全部の軸）：0.5・0.05"],
```
- search_limits.json（8 行）
```
-    "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}]
+    "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}],
+    "DPO教科書%": [{"kind": "int", "lo": 14, "hi": 40}],
+    "TRIX_EMAシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}],
+    "TRIX_EMAヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}],
+    "realized_vol_rv": [{"kind": "int", "lo": 10, "hi": 50}],
+    "close vs TRIMA_TA%": [{"kind": "int", "lo": 1, "hi": 200}],
+    "close vs VIDYA_CMO%": [{"kind": "int", "lo": 20, "hi": 200}]
```

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、当てる道具 apply_audit_fix.py・観察の道具の自己テスト・照らしの道具・表を作る道具（G-1）・資料の道具4本・監査に出す前のチェックを動かします。
**誰が結果を使うか。**
- 足した15種の列は、観察の道具の build_catalog が材料のカタログに入れ、engine_tuner と M2-F の段の道具が読みます。
- 参照表の登録（定義・独立の実装・既知答え・系統・「使う」の決定）は、観察の道具の自己テストと、オン・オフの表を作る道具（gen_indicator_switch.py）が読みます。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**今の実物（observe_diag.py・indicator_reference_diag.py）・資料（research/alias_map_k3c.json）・設計書の 4-20。
**書くもの。**
- 当てる（--design）：上の2つのコードと、知識の文書 regime_detection_kb.md の件数の囲みと、新しい壊すプログラム 7本。
- G-1：オン・オフの表・型の表・出口の型の表・材料の文書・観察の説明書・組み立ての表・資料の表3つ（資料の道具4本）・修正対応表。
- 2つ目の工事（G-1 の後）：observe_config.json と search_limits.json の、資料から写す塊（4-0 の⑦）。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 今の版を残して、教科書の版を別の材料として足す | まこさん「A」（K-3） | 今の15種は1文字も変えません。前から在る列の値は直す前と同じです（写しで 0本の違い） |
| 指標の名前に値を入れて、指標の数を増やさない | 探し方の決定（2026-10-10） | 新しいパラメータは名前に出さない引数にしました（まこさん「進めて良い」2026-10-11 の1） |
| 数字を CC が作らない | 思考の順の7（req_thinking_20261004） | 最初の値は資料の既定かライブラリの既定です。式は監査の本文と原典の逐語から写しました。既知答えの数字は合成の足から手で計算できる形で、式を 4-0 に書きました |
| 探す値を、点の一覧で先に限定しない | 要件の作ってはいけないもの2番 | 15種の名前に出る軸は今の版と同じ一覧から作り、探す範囲は2つ目の工事で資料から写します |
| 未来のデータを使わない | 要件定義書 §4.6.H2 | DPO教科書% は k本前の終値といまの平均だけを使います（未来の足を見ない形）。当てた後に H2 を取り直します |
| 値段の高さで値が変わらない | 要件定義書 §4.6.H6 | 値段の単位の物は終値で割って%にし、位置は比、スクイーズは 0/1 です |
| 乱数を使わない | 恒久67番 | 乱数は使いません |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| observe_diag.py の _atr_wilder・_sqz_carter | Wilder の ATR と Carter の作りのスクイーズ | 新設 |
| observe_diag.py の _trix_ema・_ssf_avg・_trima_ta・_vidya_cmo・_mama_hl・_thermo_orig | 教科書の版の計算 | 新設 |
| observe_diag.py の登録（_reg）・build_catalog | 15種をカタログに入れる | 直す |
| indicator_reference_diag.py の登録（_r）・系統・業界の対応表・TA_CLASS_MAP | 15種の定義・独立の実装・既知答え・「使う」の決定の逐語・ta の DPOIndicator の対応 | 直す |
| regime_detection_kb.md の件数の囲み（COUNTS_START〜COUNTS_END） | gen_materials.py が書き出す「指標の種類・材料の一覧の行・部品の件数」（写しで gen_materials.bans_count_block が数えた文に置き換える） | 直す |
| .claude/breaks の壊すプログラム | DPO の向き・内はらみ足・ならし・EMA のシグナル・平均を引かないこと・2本の平均の入力を壊すと、決めた文で落ちるかを見る | 新設 |
- 触る関数（当てる前と後の構文木を関数ごとに比べて道具が数えた）＝observe_diag.py：<モジュール直下>・_atr_wilder・_mama_hl・_sqz_carter・_ssf_avg・_thermo_orig・_trima_ta・_trix_ema・_vidya_cmo・build_catalog／indicator_reference_diag.py：<モジュール直下>・_geo_case・_ssf2_avg・_tb_aber_orig・_tb_dpo_tb・_tb_pos_ssf_avg・_tb_pos_trima_ta・_tb_pos_vidya_cmo・_tb_rvol_rv・_tb_sqz_carter・_tb_stochrsi_raw・_tb_thermo_ema・_tb_thermo_orig・_tb_trix_ema_h・_tb_trix_ema_s・_thermo_in_case・_thermo_orig_arr・_trima_ta・_vidya_cmo

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. まこさんの承認の後、全部を当てます（apply_audit_fix.py --design --dry → --design）。当てる道具は、全件を当てる前の実物で照らしてから、番号の順に当てます。1件でも合わなければ1件も当てません。
2. 当てた直後に、当てる道具が G2 と H2 を自分で走らせます（observe_diag.py は H2 の対象です）。
3. 照合（verify_design_contract.py --diff）をかけます。照らしの道具（①②）・壊すプログラムを走らせ、全体の自己テスト（--selftest）を1回 走らせて、出力をそのまま貼ります（当てた直後の写しで、全部 通ることを確かめた）。
4. G-1：オン・オフの表を作り直し（15種が「使う」に入る）、型の表・出口の型の表（変わればまこさんに再承認していただく）・材料の文書・観察の説明書・組み立ての表を作り直します。そのあと資料の道具4本（list_on_families.py --add・make_param_table.py・extract_threshold_role_add.py --alias・build_role_threshold_table.py）を走らせ、修正対応表を作り直します。ここで照らしの①は0件、②は 4-0 の⑦の設定を写すまで食い違います（G-1 の試しで実測）。
5. 2つ目の工事：4-0 の⑦の設定を、資料から道具が写す案を出し、承認をいただいて当てます（照らしの②が0件になる）。
6. G-2：G2 → H2 を取り直し、監査に出す前のチェック（pre_audit_check.py --run）を走らせます。そのあと、工事ごとに1通ずつ実装の監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝DPO。今の材料 DPO%20 は、いまの終値から「11本前の20本平均」を引いて、終値で割って%にします（TradingView の中心化しない版）。この工事で足す DPO教科書%20 は、「11本前の終値」から「いまの20本平均」を引いて、終値で割って%にします（StockCharts の「Price - X-period SMA from {X/2 + 1} periods in the future」を、未来の足を見ずに時点 t で作れる形に書いたもの＝ta の DPOIndicator と同じ）。2つは、ずらす側が逆です。既知答えは、平らな足で 0 になることと、1本ごとに 1 ずつ上げ続ける足で ((20−1)/2 − 11) ÷ 最後の終値 × 100 になることを見ます。今の版に戻すと、この値が違うので自己テストが落ちます（壊すプログラム b160）。今の DPO%20 の値は1本も変わりません。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**この工事で探す範囲は変わりません。**15種の探す範囲は、2つ目の工事で資料から写します（4-0 の⑦）。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**observe_config.json と search_limits.json は、この工事では変えません**（今の資料から写し直しても同じ。15種の分は2つ目の工事で写す）。
コマンドの旗は増やしません。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**
1. 観察の道具の全体の自己テストが通る（足した15種の既知答えと独立の実装、名前に出さない引数の番人を含む）。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest。
2. 照らしの道具が、①②とも食い違い0件。コマンド＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources。
3. 壊すプログラムが、全部 決めた文で落ちる。コマンド＝python3 .claude/tools/run_breaks.py --design。
4. G2 と H2 が取り直される。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| --design の --dry で、当たらない件が出る | 1件も当てずに止まります。まこさんに報告します |
| DPO教科書%・realized_vol_rv・THERMO原作% の作りが戻る | 観察の道具の自己テストが「手計算の既知答えと不一致」を出して落ちます |
| 15種の計算と独立の実装が合わない | 観察の道具の自己テストが「教科書の独立実装と不一致」を出して落ちます |
| 名前に出さない引数が計算に届いていない | 観察の道具の自己テスト（名前に出さない引数の番人）が落ちます |
| 15種が「使う」になったのに、資料に行が無い | 照らしの道具が「①」で始まる行を出して落ちます（資料の道具4本を G-1 の中で走らせる） |
| G-1 の後、2つ目の工事を当てる前に監査に出す前のチェックを走らせる | 照らしの道具が「②」で落ちます（2つ目の工事を当ててから走らせる＝4-4 の順） |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**変えません。**カタログの1件の形・参照表の欄・設定の欄の形は前の工事のままです。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**変えません。**

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**DPO教科書% は k本前の終値といまの n本平均を使います**（未来の足は見ません）。ほかの14種は、今の足までの値だけで計算します。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| 観察の道具の自己テスト（全体） | 139秒 | 写しで当てた後に走らせた実測（k3c_draft_build.py の [7]） |
| 軽い口（--selftest-catalog） | 9秒 | 写しで当てた後に走らせた実測（k3c_draft_build.py の [7]） |
| 材料の一覧 | 548 列 | 写しで数えた（k3c_draft_build.py の [3]） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**この工事の中ではありません。**全部を --design の1回で当てます。★この工事と2つ目の工事の間（G-1 の後）は、照らしの②が食い違う途中の状態です。その間に監査に出す前のチェックを走らせません（4-4 の順）。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しの道具だけが書きます。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**観察の道具の自己テストは、落ちたときだけ「手計算の既知答えと不一致」「教科書の独立実装と不一致」「名前に出さない引数」で始まる行を出します。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **observe_diag.py は H2 の対象です。**当てた後に G2 → H2 を取り直します。
2. **材料のカタログに 32 列が増えます。**型の表（signal_families）の部品も増え、まこさんの再承認が要ります（G-1）。
3. **成績表（material_ranking.json）には、増える列の行がありません。**作り直す（M2-D-8）まで、段の候補の順位に出ません。
4. **マイルストーンへの差し込み（作ってはいけないものとの照合）は変わりません**（写しで 0行の違い）。
5. **前からの壊すプログラムが探す文字の数は、当てる前と後で同じです。**道具が数えた相手は、下の囲みです。
```
b104_atr1h_own_tf.sh・b105_atr1h_future_hour.sh・b106_atr1h_no_clip.sh・b107_atr1h_base_not_passed.sh・b108_atr1h_base_wrong_bars.sh・b122_obs_formula_copied.sh・b126_rank_resume_save_off.sh・b128_k1_copc_back_in_ao_loop.sh・b129_htf_bar_close_two_bars.sh・b131_industry_map_prev_pivot_gone.sh・b132_hidden_param_not_passed.sh・b133_cksp_mixed_set.sh・b134_ao_name_with_value.sh・b135_rci_mako_gone.sh・b136_insp2_bar_close_dropped.sh・b137_material_params_ignored.sh・b138_keep_name_dropped.sh・b139_range_excludes_keep.sh・b140_group_range_ignored.sh・b141_catalog_out_of_range.sh・b143_rci_range_short.sh・b145_vwap_day_no_reset.sh・b146_pivot_week_as_day.sh・b147_vp_today_from_start.sh・b151_w_fractal_not_first.sh・b152_sr_fractal_counts_bars.sh・b153_smc_fractal_no_close_back.sh・b154_lower_half_upper_span.sh・b156_sr_fractal_unconfirmed.sh・b55_cyc_key_time_gone.sh・b56_one_min_csv_old.sh・b60_only5_with_others.sh・b61_insp5_bars_kind.sh・b63_tm_bitget_scope.sh・b64_tm_subdir.sh・b65_tm_badtail.sh
```

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| k3a_draft_build.py・k3b_draft_build.py（前の工事の道具） | 写しの作り・資料の写し・照らし・設定の写し・A12 の自己テストの一覧と許しの判定（import して使う） |
| indicator_reference_diag.py の _trix_parts・_stochrsi_parts・_ssf2・_trima・_vidya・_wilder・_ema_seed | 独立の実装の部品（教科書の版は、同じ部品で入力と作りだけを変える） |
| 壊すプログラム b142 | 壊すプログラムの形 |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=8e166457c7b77db0 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 941〜942行（<モジュール直下>・監査 CP60 の修正50＝平均を引かない実現ボラを、今の版を残して足す）
直す前の文字:
~~~
_reg("realized_vol", "realized_vol{}", False, lambda d, n:
     np.log(d.close / d.close.shift()).rolling(n).std() * 100)

~~~
直した後の文字:
~~~
_reg("realized_vol", "realized_vol{}", False, lambda d, n:
     np.log(d.close / d.close.shift()).rolling(n).std() * 100)
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正50 の直した後の文字）＝平均を引かない実現ボラ √(Σr²/n)。
#   今の版（平均を引いた標本の標準偏差）は残す。どちらが良いかは M2-F-10f で比べる。
_reg("realized_vol_rv", "realized_vol_rv{}", False, lambda d, n:
     np.sqrt((np.log(d.close / d.close.shift()) ** 2).rolling(n).sum() / n) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:941「_reg("realized_vol", "realized_vol{}", False, lambda d, n:」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1201行（<モジュール直下>・監査 CP60 の修正47＝Carter の作りのスクイーズを、今の版を残して足す（4つの数は名前に出さない引数））
直す前の文字:
~~~
_reg("SQZ_ON", "SQZ_ON", False, lambda d, bb_length=None, bb_std=None, kc_length=None, kc_scalar=None: _pta6.squeeze(high=d.high, low=d.low, close=d.close, bb_length=bb_length, bb_std=bb_std, kc_length=kc_length, kc_scalar=kc_scalar).iloc[:, 1])

~~~
直した後の文字:
~~~
_reg("SQZ_ON", "SQZ_ON", False, lambda d, bb_length=None, bb_std=None, kc_length=None, kc_scalar=None: _pta6.squeeze(high=d.high, low=d.low, close=d.close, bb_length=bb_length, bb_std=bb_std, kc_length=kc_length, kc_scalar=kc_scalar).iloc[:, 1])
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正47）＝Carter の作り（StockCharts の逐語「Carter uses 20 periods
#   for the moving average and ATR, and 1.5 for the ATR multiplier」）＝ボリンジャー（終値の SMA ± 倍率×σ・ddof 0）が、ケルトナー
#   （代表値段 (H+L+C)/3 の SMA ± 倍率×ATR（Wilder））の内側なら 1。ライブラリの版（中心を終値の SMA・幅を真の値幅の SMA）は残す。
#   ★4つの数は名前に出さない引数（最初の値＝資料の既定 20・2.0・20・1.5）。
def _atr_wilder(d, n):
    """Wilder の ATR（最初の n 本の真の値幅の単純平均を種に (前×(n−1)＋今)/n）。真の値幅の1本目は欠損。"""
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(axis=1).to_numpy(float)
    tr[0] = np.nan
    out = np.full(len(tr), np.nan)
    if len(tr) > n:
        out[n] = np.nanmean(tr[1:n + 1])
        for i in range(n + 1, len(tr)):
            out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return pd.Series(out, index=d.index)


def _sqz_carter(d, bb_length=20, bb_std=2.0, kc_length=20, kc_scalar=1.5):
    tp = (d.high + d.low + d.close) / 3.0
    mid, sd = d.close.rolling(bb_length).mean(), d.close.rolling(bb_length).std(ddof=0)
    km, atr = tp.rolling(kc_length).mean(), _atr_wilder(d, kc_length)
    on = ((mid - bb_std * sd) > (km - kc_scalar * atr)) & ((mid + bb_std * sd) < (km + kc_scalar * atr))
    return on.astype(float).where(atr.notna() & sd.notna())


_reg("SQZ_ON_Carter", "SQZ_ON_Carter", False,
     lambda d, bb_length=20, bb_std=2.0, kc_length=20, kc_scalar=1.5: _sqz_carter(d, bb_length, bb_std, kc_length, kc_scalar))

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1201「_reg("SQZ_ON", "SQZ_ON", False, lambda d, bb_length=None, bb_std=None, kc_length=None, kc_scalar=None: _pta6.squeeze(hig」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1240〜1243行（<モジュール直下>・監査 CP60 の修正48＝ならさない StochRSI を、今の版を残して足す）
直す前の文字:
~~~
_reg("StochRSI%K", "StochRSI%K{}", True, lambda d, n, k=None:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=k).iloc[:, 0])
_reg("StochRSI%D", "StochRSI%D{}", True, lambda d, n, k=None, d_=None:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=k, d=d_).iloc[:, 1])

~~~
直した後の文字:
~~~
_reg("StochRSI%K", "StochRSI%K{}", True, lambda d, n, k=None:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=k).iloc[:, 0])
_reg("StochRSI%D", "StochRSI%D{}", True, lambda d, n, k=None, d_=None:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=k, d=d_).iloc[:, 1])
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正48）＝原式のならさない値（StockCharts「StochRSI =
#   (RSI - Lowest Low RSI) / (Highest High RSI - Lowest Low RSI)」・0〜100）＝ならしの本数 k を 1 にしたもの。今の %K（SMA3）は残す。
_reg("StochRSI素%K", "StochRSI素%K{}", True, lambda d, n:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=1).iloc[:, 0])

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1240「_reg("StochRSI%K", "StochRSI%K{}", True, lambda d, n, k=None:」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1248〜1249行（<モジュール直下>・監査 CP60 の修正49＝シグナルを EMA にした TRIX のシグナルとヒストを、今の版を残して足す）
直す前の文字:
~~~
_reg("TRIXヒスト", "TRIXヒスト({},{})", False, lambda d, n, g_:
     _pta6.trixh(close=d.close, length=n, signal=g_).iloc[:, 2])

~~~
直した後の文字:
~~~
_reg("TRIXヒスト", "TRIXヒスト({},{})", False, lambda d, n, g_:
     _pta6.trixh(close=d.close, length=n, signal=g_).iloc[:, 2])
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正49）＝シグナルを EMA にした版（StockCharts「The signal line
#   is a 9-day EMA of the TRIX.」）。ライブラリの版（シグナルは単純移動平均）は残す。EMA はライブラリの ema（種＝最初の g 本の単純平均）。
def _trix_ema(d, n, g_):
    tx = _pta6.trix(close=d.close, length=n, signal=g_).iloc[:, 0]
    return tx, _pta6.ema(close=tx, length=g_)


_reg("TRIX_EMAシグナル", "TRIX_EMAシグナル({},{})", True, lambda d, n, g_: _trix_ema(d, n, g_)[1])
_reg("TRIX_EMAヒスト", "TRIX_EMAヒスト({},{})", False, lambda d, n, g_: (lambda t: t[0] - t[1])(_trix_ema(d, n, g_)))

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1248「_reg("TRIXヒスト", "TRIXヒスト({},{})", False, lambda d, n, g_:」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1309〜1311行（<モジュール直下>・監査 CP60 の修正51・52＝SSF（入力を2本の平均）・TRIMA（TA-Lib の偶数の形）・VIDYA（CMO の本数を別に持つ）を、今の版を残して足す）
直す前の文字:
~~~
    if _nm not in ("JMA",):        # JMA は独立実装を書いていない＝傾きも作らない
        _reg(f"{_nm}傾き", f"{_nm}{{}}傾き%", True,
             lambda d, n, f=_mafn, slope_n=5, **kw: f(d, n, **kw).pct_change(slope_n) * 100)

~~~
直した後の文字:
~~~
    if _nm not in ("JMA",):        # JMA は独立実装を書いていない＝傾きも作らない
        _reg(f"{_nm}傾き", f"{_nm}{{}}傾き%", True,
             lambda d, n, f=_mafn, slope_n=5, **kw: f(d, n, **kw).pct_change(slope_n) * 100)
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正51・52）＝教科書の式の版（今の版は残す・傾きの形は作らない）。
def _ssf_avg(c, n):
    """Ehlers のスーパースムーザー（2極）で、入力を2本の平均にしたもの（linnsoft の逐語「Filt = c1*(Close + Close[1]) / 2 + c2*Filt[1] + c3*Filt[2]」）。"""
    x = np.pi * np.sqrt(2.0) / n
    a0 = np.exp(-x)
    b0 = 2.0 * a0 * np.cos(x)
    c2, c3 = b0, -a0 * a0
    c1 = 1.0 - c2 - c3
    v = c.to_numpy(float)
    out = v.copy()
    for i in range(2, len(v)):
        out[i] = c1 * (v[i] + v[i - 1]) / 2.0 + c2 * out[i - 1] + c3 * out[i - 2]
    return pd.Series(out, index=c.index)


def _trima_ta(c, n):
    """TA-Lib の TRIMA（偶数の n＝SMA(SMA(x, n/2), n/2+1)・ta-lib.org の逐語「even: SMA(SMA(x,period/2),period/2+1)」）。奇数の n は今の版と同じ。"""
    if n % 2 == 0:
        return c.rolling(n // 2).mean().rolling(n // 2 + 1).mean()
    h = n // 2 + 1
    return c.rolling(h).mean().rolling(h).mean()


def _vidya_cmo(c, n, m=9):
    """VIDYA で CMO の本数 m を n と別に持つ版（ta-lib.org の逐語「n = optInTimePeriod, m = optInCMOPeriod」）。m は名前に出さない引数（最初の値 9＝資料の既定）。"""
    dif = c.diff()
    up, dn = dif.clip(lower=0).rolling(m).sum(), (-dif).clip(lower=0).rolling(m).sum()
    k = ((up - dn) / (up + dn)).abs().to_numpy(float)
    v = c.to_numpy(float)
    a = 2.0 / (n + 1)
    out = np.full(len(v), np.nan)
    if len(v) >= n:
        out[n - 1] = float(np.nanmean(v[:n]))
        for i in range(n, len(v)):
            kk = 0.0 if np.isnan(k[i]) else k[i]
            out[i] = a * kk * v[i] + (1 - a * kk) * out[i - 1]
    return pd.Series(out, index=c.index)


_reg("close vs SSF平均%", "close vs SSF平均%{}", True, lambda d, n: (d.close / _ssf_avg(d.close, n) - 1) * 100)
_reg("close vs TRIMA_TA%", "close vs TRIMA_TA%{}", True, lambda d, n: (d.close / _trima_ta(d.close, n) - 1) * 100)
_reg("close vs VIDYA_CMO%", "close vs VIDYA_CMO%{}", True, lambda d, n, m=9: (d.close / _vidya_cmo(d.close, n, m) - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1309「if _nm not in ("JMA",):        # JMA は独立実装を書いていない＝傾きも作らない」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1320〜1321行（<モジュール直下>・監査 CP60 の修正53＝入力を (高値＋安値)/2 にした HT_TRENDLINE を、今の版を残して足す）
直す前の文字:
~~~
_reg("close vs HT_TRENDLINE%", "close vs HT_TRENDLINE%", True,
     lambda d: (d.close / _pta6.ht_trendline(close=d.close) - 1) * 100)

~~~
直した後の文字:
~~~
_reg("close vs HT_TRENDLINE%", "close vs HT_TRENDLINE%", True,
     lambda d: (d.close / _pta6.ht_trendline(close=d.close) - 1) * 100)
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正53）＝Ehlers の入力 (高値＋安値)/2 の版（今の版は残す）。
_reg("close vs HT_TRENDLINE_HL%", "close vs HT_TRENDLINE_HL%", True,
     lambda d: (d.close / _pta6.ht_trendline(close=(d.high + d.low) / 2.0) - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1320「_reg("close vs HT_TRENDLINE%", "close vs HT_TRENDLINE%", True,」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1323〜1324行（<モジュール直下>・監査 CP60 の修正53＝入力を (高値＋安値)/2 にした MAMA・FAMA を、今の版を残して足す）
直す前の文字:
~~~
_reg("close vs MAMA%", "close vs MAMA%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama(d, fastlimit=fastlimit, slowlimit=slowlimit).iloc[:, 0] - 1) * 100)
_reg("close vs FAMA%", "close vs FAMA%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama(d, fastlimit=fastlimit, slowlimit=slowlimit).iloc[:, 1] - 1) * 100)

~~~
直した後の文字:
~~~
_reg("close vs MAMA%", "close vs MAMA%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama(d, fastlimit=fastlimit, slowlimit=slowlimit).iloc[:, 0] - 1) * 100)
_reg("close vs FAMA%", "close vs FAMA%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama(d, fastlimit=fastlimit, slowlimit=slowlimit).iloc[:, 1] - 1) * 100)
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正53）＝Ehlers の入力 (高値＋安値)/2 の版
#   （MAMA.pdf のコードの逐語「Inputs: Price((H+L)/2), FastLimit(.5), SlowLimit(.05);」）。今の版（入力が終値）は残す。
def _mama_hl(d, **kw):
    return _pta6.mama(close=(d.high + d.low) / 2.0, **kw)


_reg("close vs MAMA_HL%", "close vs MAMA_HL%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama_hl(d, fastlimit=fastlimit, slowlimit=slowlimit).iloc[:, 0] - 1) * 100)
_reg("close vs FAMA_HL%", "close vs FAMA_HL%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama_hl(d, fastlimit=fastlimit, slowlimit=slowlimit).iloc[:, 1] - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1323「_reg("close vs MAMA%", "close vs MAMA%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama(d, fastlimit=f」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1371〜1372行（<モジュール直下>・監査 CP60 の修正37・45＝教科書の DPO（k本前の終値 − いまの n本平均）を、今の版を残して足す）
直す前の文字:
~~~
_reg("DPO%", "DPO%{}", False, lambda d, n:
     _pta6.dpo(close=d.close, length=n, centered=False) / d.close * 100)

~~~
直した後の文字:
~~~
_reg("DPO%", "DPO%{}", False, lambda d, n:
     _pta6.dpo(close=d.close, length=n, centered=False) / d.close * 100)
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正37・45 の補足の式）＝教科書の DPO を時点 t で計算できる形
#   「k本前の終値 − いまの n本平均」（k=n/2+1・StockCharts「Price - X-period SMA from {X/2 + 1} periods in the future」）。今の版（いまの終値 −
#   k本前の n本平均＝TradingView の中心化しない版）は残す。未来は見ない。
_reg("DPO教科書%", "DPO教科書%{}", False, lambda d, n:
     (d.close.shift(int(0.5 * n) + 1) - _pta6.sma(close=d.close, length=n)) / d.close * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1371「_reg("DPO%", "DPO%{}", False, lambda d, n:」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1432〜1433行（<モジュール直下>・監査 CP60 の修正45・71＝Fitschen の原作の Aberration の帯の中の位置を、今の版を残して足す（本数と倍率は名前に出さない引数））
直す前の文字:
~~~
_reg("ABER位置", "ABER位置", True,
     lambda d, length=None, atr_length=None: (lambda a: (d.close - a.iloc[:, 2]) / (a.iloc[:, 1] - a.iloc[:, 2]))(_ab(d, length=length, atr_length=atr_length)))

~~~
直した後の文字:
~~~
_reg("ABER位置", "ABER位置", True,
     lambda d, length=None, atr_length=None: (lambda a: (d.close - a.iloc[:, 2]) / (a.iloc[:, 1] - a.iloc[:, 2]))(_ab(d, length=length, atr_length=atr_length)))
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正45・71）＝Fitschen の原作の Aberration＝80本・標準偏差2倍の
#   ボリンジャーバンドの中の位置（%b と同じ作り・ddof 0）。ライブラリの版（HLC3 の5本 SMA ± ATR15）は残す。
#   ★本数と倍率は名前に出さない引数（最初の値＝原作の既定 80・2.0＝監査の逐語「80本・標準偏差2倍」）。BB%b の範囲は触らない（案の4）。
_reg("ABER原作位置", "ABER原作位置", True, lambda d, length=80, std=2.0:
     (lambda m, s: (d.close - (m - std * s)) / (2.0 * std * s))(d.close.rolling(length).mean(), d.close.rolling(length).std(ddof=0)))

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1432「_reg("ABER位置", "ABER位置", True,」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1444〜1445行（<モジュール直下>・監査 CP60 の修正45・58＝Elder の原作の温度計と、K-7 の決定＝EMA でならした版を、今の版を残して足す）
直す前の文字:
~~~
_reg("THERMO%", "THERMO%", False, lambda d: _th(d).iloc[:, 0] / d.close * 100)
_reg("THERMO比", "THERMO比", False, lambda d: (lambda t: t.iloc[:, 0] / t.iloc[:, 1])(_th(d)))

~~~
直した後の文字:
~~~
_reg("THERMO%", "THERMO%", False, lambda d: _th(d).iloc[:, 0] / d.close * 100)
_reg("THERMO比", "THERMO比", False, lambda d: (lambda t: t.iloc[:, 0] / t.iloc[:, 1])(_th(d)))
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正45 の直した後の文字）＝Elder の原作＝外へはみ出した幅だけ
#   （max(max(High − PrevHigh, 0), max(PrevLow − Low, 0))・内はらみ足は 0）。ライブラリの版（絶対値）は残す。
def _thermo_orig(d):
    return np.maximum((d.high - d.high.shift(1)).clip(lower=0), (d.low.shift(1) - d.low).clip(lower=0))


_reg("THERMO原作%", "THERMO原作%", False, lambda d: _thermo_orig(d) / d.close * 100)
# ★K-7 の決定（ok_k7_pivot_thermo_20261007）＝EMA でならした版。EMA の本数は名前に出さない引数（最初の値＝ライブラリの既定 20・資料の既定は 20 と 22）。
_reg("THERMO_EMA%", "THERMO_EMA%", False, lambda d, ema_n=20: _pta6.ema(close=_thermo_orig(d), length=ema_n) / d.close * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1444「_reg("THERMO%", "THERMO%", False, lambda d: _th(d).iloc[:, 0] / d.close * 100)」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1558〜1559行（build_catalog・realized_vol_rv をカタログに入れる（今の realized_vol と同じ本数の一覧で作る））
直す前の文字:
~~~
    for n in cfg["realized_vol_periods"]:
        addf("realized_vol", n)

~~~
直した後の文字:
~~~
    for n in cfg["realized_vol_periods"]:
        addf("realized_vol", n)
        addf("realized_vol_rv", n)        # 監査 CP60 の修正50（K-3c・2026-10-11）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1558「for n in cfg["realized_vol_periods"]:」
状態: 確定

#### 実装 12
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1698〜1699行（build_catalog・StochRSI素%K をカタログに入れる（今の StochRSI と同じ本数の一覧で作る））
直す前の文字:
~~~
        addf("StochRSI%K", n)
        addf("StochRSI%D", n)

~~~
直した後の文字:
~~~
        addf("StochRSI%K", n)
        addf("StochRSI%D", n)
        addf("StochRSI素%K", n)           # 監査 CP60 の修正48（K-3c・2026-10-11）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1698「addf("StochRSI%K", n)」
状態: 確定

#### 実装 13
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1703行（build_catalog・TRIX_EMAシグナル・TRIX_EMAヒスト をカタログに入れる（今の TRIX と同じ一覧で作る））
直す前の文字:
~~~
            addf("TRIXヒスト", n, g_)

~~~
直した後の文字:
~~~
            addf("TRIXヒスト", n, g_)
            addf("TRIX_EMAシグナル", n, g_)   # 監査 CP60 の修正49（K-3c・2026-10-11）
            addf("TRIX_EMAヒスト", n, g_)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1703「addf("TRIXヒスト", n, g_)」
状態: 確定

#### 実装 14
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1731行（build_catalog・close vs HT_TRENDLINE_HL% をカタログに入れる）
直す前の文字:
~~~
    addf("close vs HT_TRENDLINE%")

~~~
直した後の文字:
~~~
    addf("close vs HT_TRENDLINE%")
    addf("close vs HT_TRENDLINE_HL%")      # 監査 CP60 の修正53（K-3c・2026-10-11）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1731「addf("close vs HT_TRENDLINE%")」
状態: 確定

#### 実装 15
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1740〜1741行（build_catalog・close vs MAMA_HL%・close vs FAMA_HL% をカタログに入れる）
直す前の文字:
~~~
    addf("close vs MAMA%")
    addf("close vs FAMA%")

~~~
直した後の文字:
~~~
    addf("close vs MAMA%")
    addf("close vs FAMA%")
    addf("close vs MAMA_HL%")               # 監査 CP60 の修正53（K-3c・2026-10-11）
    addf("close vs FAMA_HL%")

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1740「addf("close vs MAMA%")」
状態: 確定

#### 実装 16
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1758〜1762行（build_catalog・close vs SSF平均%・TRIMA_TA%・VIDYA_CMO% をカタログに入れる（今の移動平均と同じ本数の一覧で作る））
直す前の文字:
~~~
    for n in cfg["sma_periods"]:
        for _nm in ("SINWMA", "SSF", "SWMA", "T3", "TEMA", "TRIMA",
                    "TSF", "VIDYA", "VWMA", "WMA", "ZLMA"):
            addf(f"close vs {_nm}%", n)
            addf(f"{_nm}傾き", n)

~~~
直した後の文字:
~~~
    for n in cfg["sma_periods"]:
        for _nm in ("SINWMA", "SSF", "SWMA", "T3", "TEMA", "TRIMA",
                    "TSF", "VIDYA", "VWMA", "WMA", "ZLMA"):
            addf(f"close vs {_nm}%", n)
            addf(f"{_nm}傾き", n)
        addf("close vs SSF平均%", n)       # 監査 CP60 の修正51（K-3c・2026-10-11）
        addf("close vs TRIMA_TA%", n)      # 監査 CP60 の修正52（K-3c・2026-10-11）
        addf("close vs VIDYA_CMO%", n)     # 監査 CP60 の修正52（K-3c・2026-10-11）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1758「for n in cfg["sma_periods"]:」
状態: 確定

#### 実装 17
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1772〜1773行（build_catalog・DPO教科書% をカタログに入れる（今の DPO% と同じ本数の一覧で作る））
直す前の文字:
~~~
        addf("DPO%", n)
        addf("TTM_TREND", n)

~~~
直した後の文字:
~~~
        addf("DPO%", n)
        addf("DPO教科書%", n)              # 監査 CP60 の修正37・45（K-3c・2026-10-11）
        addf("TTM_TREND", n)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1772「addf("DPO%", n)」
状態: 確定

#### 実装 18
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1694行（build_catalog・SQZ_ON_Carter をカタログに入れる（名前に出る軸は無い））
直す前の文字:
~~~
    addf("SMC_SWEEP確定")                     # 監査 CP60 の修正46（K-3b・2026-10-09）

~~~
直した後の文字:
~~~
    addf("SMC_SWEEP確定")                     # 監査 CP60 の修正46（K-3b・2026-10-09）
    addf("SQZ_ON_Carter")                     # 監査 CP60 の修正47（K-3c・2026-10-11）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1694「addf("SMC_SWEEP確定")                     # 監査 CP60 の修正46（K-3b・2026-10-09）」
状態: 確定

#### 実装 19
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1821〜1823行（build_catalog・ABER原作位置 をカタログに入れる（名前に出る軸は無い））
直す前の文字:
~~~
    for _fam in ("close vs ABER_ZG%", "ABER位置", "close vs ACCBL%", "close vs ACCBU%",
                 "close vs CE_L%", "close vs CE_S%"):
        addf(_fam)

~~~
直した後の文字:
~~~
    for _fam in ("close vs ABER_ZG%", "ABER位置", "close vs ACCBL%", "close vs ACCBU%",
                 "close vs CE_L%", "close vs CE_S%"):
        addf(_fam)
    addf("ABER原作位置")                     # 監査 CP60 の修正45・71（K-3c・2026-10-11）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1821「for _fam in ("close vs ABER_ZG%", "ABER位置", "close vs ACCBL%", "close vs ACCBU%",」
状態: 確定

#### 実装 20
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1828〜1829行（build_catalog・THERMO原作%・THERMO_EMA% をカタログに入れる（名前に出る軸は無い））
直す前の文字:
~~~
    for _fam in ("HWC位置", "HWC幅%", "MASSI", "PDIST%", "TR%", "THERMO%", "THERMO比"):
        addf(_fam)

~~~
直した後の文字:
~~~
    for _fam in ("HWC位置", "HWC幅%", "MASSI", "PDIST%", "TR%", "THERMO%", "THERMO比"):
        addf(_fam)
    addf("THERMO原作%")                       # 監査 CP60 の修正45・58（K-3c・2026-10-11）
    addf("THERMO_EMA%")                      # K-7 の決定（ok_k7_pivot_thermo_20261007・K-3c・2026-10-11）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1828「for _fam in ("HWC位置", "HWC幅%", "MASSI", "PDIST%", "TR%", "THERMO%", "THERMO比"):」
状態: 確定

#### 実装 21
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 948行（<モジュール直下>・15種の「使う」の決定（まこさんの逐語のファイル）を、mako の欄から1か所で引けるようにする）
直す前の文字:
~~~
MAKO_K3B = '2026-10-09 まこさん「よい」（K-3b の作りの3点＝確定した山・谷の本数 k は名前に出さない引数・SMC_SWEEP の教科書の版はライブラリの 15・1.5 を使わない・下半分位置を使う）＝逐語のファイル ok_k3b_design_20261009（m2c15-k3b-decisions-20261009）。K-3 を3つの工事に分けた まこさん決定「A」＝ok_k3_split_20261007'

~~~
直した後の文字:
~~~
MAKO_K3B = '2026-10-09 まこさん「よい」（K-3b の作りの3点＝確定した山・谷の本数 k は名前に出さない引数・SMC_SWEEP の教科書の版はライブラリの 15・1.5 を使わない・下半分位置を使う）＝逐語のファイル ok_k3b_design_20261009（m2c15-k3b-decisions-20261009）。K-3 を3つの工事に分けた まこさん決定「A」＝ok_k3_split_20261007'
# ★2026-10-11（工事 m2c15-formula-textbook-20261011）＝K-3c の15種の「使う」の決定の逐語（mako の欄に書く）。
MAKO_K3C = '2026-10-11 まこさん「把握してるならよい／指標の修正のゴールに対し、このフェーズでの修正案は正しく、齟齬が無いのであれば進めて良い」（K-3c の作りの5点＝新しい名前は作りの違いだけ・新しいパラメータは名前に出さない引数・式は監査の本文と原典の逐語から・Aberration 原作は別の材料・対応表と既知答えは K-3b と同じ形）＝逐語のファイル ok_k3c_design_20261011（m2c15-formula-textbook-20261011）。K-3 を3つの工事に分けた まこさん決定「A」＝ok_k3_split_20261007。THERMO の EMA の版＝ok_k7_pivot_thermo_20261007'

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:948「MAKO_K3B = '2026-10-09 まこさん「よい」（K-3b の作りの3点＝確定した山・谷の本数 k は名前に出さない引数・SMC_SWEEP の教科書の版はライブラリの 15・1.5 を使わない・下半分位置を使う）＝逐語のファ」
状態: 確定

#### 実装 22
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1673〜1681行（<モジュール直下>・監査 CP60 の修正37・45・47〜53 と K-7 の決定＝15種を参照表に登録し、独立の実装と手計算の既知答えを付ける）
直す前の文字:
~~~
_r(r"SMC_SWEEP確定", "SMC_SWEEP確定",
   "流動性の刈り取りの教科書の版。1本前までに確定した直近の谷を安値で割り、終値でその上に戻した足を +1・"
   "山を高値で抜き、終値でその下に戻した足を −1",
   "監査 CP60 の修正46＝LuxAlgo の逐語「The classic anatomy is a wick through a prior swing high or low…followed by a close back inside the old range.」。"
   "山・谷は前後 k 本で確定（k は名前に出さない引数・最初の値 2）。ライブラリの版（直前15本の高安・陽線陰線・ヒゲが実体の1.5倍）の条件は使わない",
   "反転サイン", "none", tb=_tb_smc_fr,
   known=lambda p: [(_smc_fr_case("bull"), [(-1, 1.0, 1e-9)]), (_smc_fr_case("bear"), [(-1, -1.0, 1e-9)]),
                    (_smc_fr_case("stay"), [(-1, 0.0, 1e-9)])],
   mako=MAKO_K3B)

~~~
直した後の文字:
~~~
_r(r"SMC_SWEEP確定", "SMC_SWEEP確定",
   "流動性の刈り取りの教科書の版。1本前までに確定した直近の谷を安値で割り、終値でその上に戻した足を +1・"
   "山を高値で抜き、終値でその下に戻した足を −1",
   "監査 CP60 の修正46＝LuxAlgo の逐語「The classic anatomy is a wick through a prior swing high or low…followed by a close back inside the old range.」。"
   "山・谷は前後 k 本で確定（k は名前に出さない引数・最初の値 2）。ライブラリの版（直前15本の高安・陽線陰線・ヒゲが実体の1.5倍）の条件は使わない",
   "反転サイン", "none", tb=_tb_smc_fr,
   known=lambda p: [(_smc_fr_case("bull"), [(-1, 1.0, 1e-9)]), (_smc_fr_case("bear"), [(-1, -1.0, 1e-9)]),
                    (_smc_fr_case("stay"), [(-1, 0.0, 1e-9)])],
   mako=MAKO_K3B)


# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正37・45・47〜53 と K-7 の決定）＝計算式の教科書の版。
#   独立の実装は、素直な繰り返しと部品（_roll・_ema_seed・_wilder）で書く＝観察の道具（ライブラリ）とは別の書き方。
def _tb_rvol_rv(d, p):
    c = d.close.to_numpy(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.log(c / np.where(np.roll(c, 1) == 0, np.nan, np.roll(c, 1)))
    r[0] = np.nan
    n = int(p[0])
    return _S(np.sqrt(_roll(r * r, n, "sum") / n) * 100, d)


def _geo_case(n=60, r=0.001):
    """realized_vol_rv の既知答え用＝終値が毎本 同じ割合 r で増える足（対数リターンが一定）。平均を引く今の版は 0・引かない版は 100×ln(1+r)。"""
    c = 100.0 * (1.0 + r) ** np.arange(n)
    return _mk(c=c)


def _tb_sqz_carter(d, p, bb_length=20, bb_std=2.0, kc_length=20, kc_scalar=1.5):
    o, h, l, c, v = _arr(d)
    mid, sd = _roll(c, bb_length, "mean"), _roll(c, bb_length, "std", ddof=0)
    km = _roll((h + l + c) / 3.0, kc_length, "mean")
    atr = _wilder(_tr(h, l, c), kc_length)
    on = ((mid - bb_std * sd) > (km - kc_scalar * atr)) & ((mid + bb_std * sd) < (km + kc_scalar * atr))
    out = np.where(np.isnan(atr) | np.isnan(sd), np.nan, on.astype(float))
    return _S(out, d)


def _tb_stochrsi_raw(d, p):
    return _S(_stochrsi_parts(d, int(p[0]), int(p[0]), 1, 1)[0], d)


def _tb_trix_ema_s(d, p):
    tx = _trix_parts(d, int(p[0]), int(p[1]))[0]
    return _S(_ema_seed(tx, int(p[1])), d)


def _tb_trix_ema_h(d, p):
    tx = _trix_parts(d, int(p[0]), int(p[1]))[0]
    return _S(tx - _ema_seed(tx, int(p[1])), d)


def _ssf2_avg(c: np.ndarray, n: int) -> np.ndarray:
    """Ehlers のスーパースムーザー（2極）＝入力を (c + c[1])/2 にしたもの。"""
    x = np.pi * np.sqrt(2.0) / n
    a0 = np.exp(-x)
    b0 = 2.0 * a0 * np.cos(x)
    c2, c3 = b0, -a0 * a0
    c1 = 1.0 - c2 - c3
    out = c.astype(float).copy()
    for i in range(2, len(c)):
        out[i] = c1 * (c[i] + c[i - 1]) / 2.0 + c2 * out[i - 1] + c3 * out[i - 2]
    return out


def _tb_pos_ssf_avg(d, p):
    return _pos(_ssf2_avg(d.close.to_numpy(float), int(p[0])), d)


def _trima_ta(c, n):
    """TA-Lib の TRIMA。偶数の n＝SMA(SMA(x, n/2), n/2+1)。奇数の n は今の _trima と同じ。"""
    if n % 2 == 0:
        return _roll(_roll(c, n // 2, "mean"), n // 2 + 1, "mean")
    return _trima(c, n)


def _tb_pos_trima_ta(d, p):
    return _pos(_trima_ta(d.close.to_numpy(float), int(p[0])), d)


def _vidya_cmo(c: np.ndarray, n: int, m: int = 9) -> np.ndarray:
    a = 2.0 / (n + 1)
    up = _roll(np.r_[np.nan, np.diff(c)].clip(min=0), m, "sum")
    dn = _roll((-np.r_[np.nan, np.diff(c)]).clip(min=0), m, "sum")
    k = np.abs(_div(up - dn, up + dn))
    out = np.full(len(c), np.nan)
    if len(c) < n:
        return out
    out[n - 1] = float(np.nanmean(c[:n]))
    for i in range(n, len(c)):
        kk = 0.0 if np.isnan(k[i]) else k[i]
        out[i] = a * kk * c[i] + (1 - a * kk) * out[i - 1]
    return out


def _tb_pos_vidya_cmo(d, p, m=9):
    return _pos(_vidya_cmo(d.close.to_numpy(float), int(p[0]), int(m)), d)


def _tb_dpo_tb(d, p):
    """教科書の DPO を時点 t で作れる形＝k本前の終値 − いまの n本平均（k=n/2+1）。終値で割って%化（H6）。"""
    n = int(p[0])
    c = d.close.to_numpy(float)
    return (_S(c, d).shift(int(0.5 * n) + 1) - _S(_roll(c, n, "mean"), d)) / d.close * 100


def _tb_aber_orig(d, p, length=80, std=2.0):
    c = d.close.to_numpy(float)
    mid, sd = _roll(c, int(length), "mean"), _roll(c, int(length), "std", ddof=0)
    return _S(_div(c - (mid - std * sd), 2.0 * std * sd), d)


def _thermo_orig_arr(d):
    o, h, l, c, v = _arr(d)
    ph, pl = np.r_[np.nan, h[:-1]], np.r_[np.nan, l[:-1]]
    return c, np.maximum(np.maximum(h - ph, 0.0), np.maximum(pl - l, 0.0))


def _tb_thermo_orig(d, p):
    c, t = _thermo_orig_arr(d)
    return _S(_div(t, c) * 100.0, d)


def _tb_thermo_ema(d, p, ema_n=20):
    c, t = _thermo_orig_arr(d)
    return _S(_div(_ema_seed(t, int(ema_n)), c) * 100.0, d)


def _thermo_in_case(n=30):
    """THERMO原作% の既知答え用＝平らな足（高値 101・安値 99）の最後の足だけ内はらみ（高値 100.5・安値 99.5）。原作は 0・ライブラリの版は 0.5/100×100。"""
    c = np.full(n, 100.0)
    h = np.full(n, 101.0)
    l = np.full(n, 99.0)
    h[-1], l[-1] = 100.5, 99.5
    return _mk(c=c, o=c.copy(), h=h, l=l)


_r(r"realized_vol_rv(\d+)", "realized_vol_rv",
   "平均を引かない実現ボラ＝対数リターンの二乗の n 本平均の平方根×100",
   "監査 CP60 の修正50＝Wikipedia「RV(n) = Σ r²」「the square root of the realized variance」。今の realized_vol（平均を引いた標本の標準偏差）は残す",
   "ボラ量", "vol", tb=_tb_rvol_rv,
   known=lambda p: [(_flat(p[0] * 3), [(-1, 0.0, 1e-9)]), (_geo_case(p[0] * 3), [(-1, 100.0 * np.log(1.001), 1e-9)])],
   mako=MAKO_K3C)
_r(r"SQZ_ON_Carter", "SQZ_ON_Carter",
   "スクイーズ（Carter の作り）＝ボリンジャー（終値の SMA ± 2σ）がケルトナー（代表値段の SMA ± 1.5×ATR（Wilder））の内側なら 1",
   "監査 CP60 の修正47＝StockCharts「Carter uses 20 periods for the moving average and ATR, and 1.5 for the ATR multiplier」。"
   "4つの数は名前に出さない引数（最初の値 20・2.0・20・1.5）。今の SQZ_ON（中心を終値の SMA・幅を真の値幅の SMA）は残す",
   "状態量", "none", tb=_tb_sqz_carter, mako=MAKO_K3C)
_r(r"StochRSI素%K(\d+)", "StochRSI素%K",
   "RSI にストキャスを掛けた原式の値（ならさない・0〜100）",
   "監査 CP60 の修正48＝StockCharts「StochRSI = (RSI - Lowest Low RSI) / (Highest High RSI - Lowest Low RSI)」。今の %K（SMA3 でならす）は残す",
   "順張り値", "trend", tb=_tb_stochrsi_raw, mako=MAKO_K3C)
_r(r"TRIX_EMAシグナル\((\d+),(\d+)\)", "TRIX_EMAシグナル",
   "TRIX を g 本の EMA でならしたシグナル", "監査 CP60 の修正49＝StockCharts「The signal line is a 9-day EMA of the TRIX.」。今の TRIXシグナル（単純移動平均）は残す",
   "順張り値", "trend", tb=_tb_trix_ema_s, mako=MAKO_K3C)
_r(r"TRIX_EMAヒスト\((\d+),(\d+)\)", "TRIX_EMAヒスト",
   "TRIX と EMA のシグナルの差", "同上。今の TRIXヒスト（単純移動平均のシグナルとの差）は残す",
   "状態量＝加速（向きを持たない）", "none", tb=_tb_trix_ema_h, mako=MAKO_K3C)
_r(r"close vs SSF平均%(\d+)", "close vs SSF平均%",
   "終値が、入力を2本の平均にした Ehlers のスーパースムーザー（2極）から何%離れているか",
   "監査 CP60 の修正51＝linnsoft の逐語「Filt = c1*(Close + Close[1]) / 2 + c2*Filt[1] + c3*Filt[2];」。今の close vs SSF%（入力が終値）は残す",
   "反転サイン", "trend", tb=_tb_pos_ssf_avg, mako=MAKO_K3C)
_r(r"close vs TRIMA_TA%(\d+)", "close vs TRIMA_TA%",
   "終値が TA-Lib の TRIMA（偶数の n＝SMA(SMA(x, n/2), n/2+1)）から何%離れているか",
   "監査 CP60 の修正52＝ta-lib.org「even: SMA(SMA(x,period/2),period/2+1)」。奇数の n は今の版と同じ。今の close vs TRIMA%（偶数でも n/2+1 を2回）は残す",
   "反転サイン", "trend", tb=_tb_pos_trima_ta, mako=MAKO_K3C)
_r(r"close vs VIDYA_CMO%(\d+)", "close vs VIDYA_CMO%",
   "終値が、CMO の本数 m を n と別に持つ VIDYA から何%離れているか",
   "監査 CP60 の修正52＝ta-lib.org「n = optInTimePeriod, m = optInCMOPeriod」。m は名前に出さない引数（最初の値 9＝資料の既定）。今の版（m=n）は残す",
   "反転サイン", "trend", tb=_tb_pos_vidya_cmo, mako=MAKO_K3C)
_r(r"close vs HT_TRENDLINE_HL%", "close vs HT_TRENDLINE_HL%",
   "終値が、入力を (高値＋安値)/2 にしたヒルベルト変換のトレンド線から何%離れているか",
   "監査 CP60 の修正53＝Ehlers の入力は (H+L)/2（ta-lib.org の表 79）。★変換が多段で独立実装を書けない。既知答え＝値段が一定なら ぴったり 0。今の版（入力が終値）は残す",
   "反転サイン", "none", known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])], mako=MAKO_K3C)
_r(r"close vs MAMA_HL%", "close vs MAMA_HL%",
   "終値が、入力を (高値＋安値)/2 にした MAMA から何%離れているか",
   "監査 CP60 の修正53＝MAMA.pdf のコードの逐語「Inputs: Price((H+L)/2), FastLimit(.5), SlowLimit(.05);」。★独立実装を書けない＝既知答えで検証。今の版は残す",
   "反転サイン", "none", known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])], mako=MAKO_K3C)
_r(r"close vs FAMA_HL%", "close vs FAMA_HL%",
   "終値が、入力を (高値＋安値)/2 にした FAMA（MAMA の追従線）から何%離れているか",
   "同上", "反転サイン", "none", known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])], mako=MAKO_K3C)
_r(r"DPO教科書%(\d+)", "DPO教科書%",
   "教科書の DPO を時点 t で作れる形＝k本前の終値 − いまの n本平均（k=n/2+1）を、終値で割って%化",
   "監査 CP60 の修正37・45＝StockCharts「Price - X-period SMA from {X/2 + 1} periods in the future」を未来を見ずに書いた形（ta の DPOIndicator と同じ）。"
   "今の DPO%（いまの終値 − k本前の n本平均＝TradingView の中心化しない版）は残す",
   "反転サイン", "none", tb=_tb_dpo_tb,
   known=lambda p: [(_flat(p[0] * 3), [(-1, 0.0, 1e-9)]),
                    (_up(p[0] * 3), [(-1, (((p[0] - 1) / 2.0) - (int(0.5 * p[0]) + 1)) / (100.0 + p[0] * 3 - 1) * 100.0, 1e-9)])],
   mako=MAKO_K3C)
_r(r"ABER原作位置", "ABER原作位置",
   "終値が、Fitschen の原作の Aberration の帯（80本・標準偏差2倍のボリンジャーバンド）の中のどこにあるか。0 で下の帯・1 で上の帯",
   "監査 CP60 の修正45・71＝georgepruitt.com「a breakout system based on Bollinger bands with a period length of 80 days and two standard deviations」。"
   "本数と倍率は名前に出さない引数（最初の値 80・2.0）。今の ABER位置（ライブラリの HLC3 の5本 SMA ± ATR15）は残す",
   "順張り値＝大きいほど帯の上側", "trend", tb=_tb_aber_orig, mako=MAKO_K3C)
_r(r"THERMO原作%", "THERMO原作%",
   "Elder の原作の温度計＝前の足から外へはみ出した幅（高値の上げ幅か安値の下げ幅の大きい方・内はらみ足は 0）を、終値で割って%化",
   "監査 CP60 の修正45・58＝Elder（Come Into My Trading Room 2002 p.162）・TradingView の逐語「Inside bars: Both protrusions clamp to zero」。"
   "今の THERMO%（絶対値を取るライブラリの版）は残す",
   "ボラ量", "vol", tb=_tb_thermo_orig,
   known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)]), (_thermo_in_case(), [(-1, 0.0, 1e-9)])], mako=MAKO_K3C)
_r(r"THERMO_EMA%", "THERMO_EMA%",
   "Elder の原作の温度計を EMA でならしたもの（終値で割って%化）",
   "K-7 の決定（ok_k7_pivot_thermo_20261007）＝教科書の既定 20（motivewave）・22（tradingview）は EMA の本数。EMA の本数は名前に出さない引数"
   "（最初の値＝ライブラリの既定 20）。EMA の種＝最初の n 本の単純平均（ライブラリの既定）",
   "ボラ量", "vol", tb=_tb_thermo_ema, known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])], mako=MAKO_K3C)

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1673「_r(r"SMC_SWEEP確定", "SMC_SWEEP確定",」
状態: 確定

#### 実装 23
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4920行（<モジュール直下>・15種の系統（元の種類と同じ）を書く）
直す前の文字:
~~~
    "SMC_SWEEP確定": dict(k="構造・位置", note="SMC_SWEEP と同じ（確定した山・谷を抜いて戻した足＝水準に関わる判定）"),

~~~
直した後の文字:
~~~
    "SMC_SWEEP確定": dict(k="構造・位置", note="SMC_SWEEP と同じ（確定した山・谷を抜いて戻した足＝水準に関わる判定）"),
    # ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c）＝計算式の教科書の版（系統は元の種類と同じ）
    "realized_vol_rv": dict(k="ボラ"), "SQZ_ON_Carter": dict(k="ボラ"), "THERMO原作%": dict(k="ボラ"), "THERMO_EMA%": dict(k="ボラ"),
    "StochRSI素%K": dict(k="オシレーター"), "DPO教科書%": dict(k="オシレーター"),
    "TRIX_EMAシグナル": dict(k="トレンド"), "TRIX_EMAヒスト": dict(k="トレンド"),
    "close vs SSF平均%": dict(k="構造・位置"), "close vs TRIMA_TA%": dict(k="構造・位置"), "close vs VIDYA_CMO%": dict(k="構造・位置"),
    "close vs HT_TRENDLINE_HL%": dict(k="構造・位置"), "close vs MAMA_HL%": dict(k="構造・位置"), "close vs FAMA_HL%": dict(k="構造・位置"),
    "ABER原作位置": dict(k="構造・位置", note="ABER位置 と同じ（帯の中の位置）"),

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:4920「"SMC_SWEEP確定": dict(k="構造・位置", note="SMC_SWEEP と同じ（確定した山・谷を抜いて戻した足＝水準に関わる判定）"),」
状態: 確定

#### 実装 24
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 5247〜5248行（<モジュール直下>・15種の業界のライブラリとの対応を書く（観察の道具の検査10 が全部の種類に求める））
直す前の文字:
~~~
    "SMC_SWEEP確定": ((), "pandas-ta の smc_sweep は直前 n 本の高安とヒゲの倍率で作る別の版。確定した山・谷で作る教科書の版の関数は"
                          "ライブラリに無い（定義表の既知答えで確かめる）"),

~~~
直した後の文字:
~~~
    "SMC_SWEEP確定": ((), "pandas-ta の smc_sweep は直前 n 本の高安とヒゲの倍率で作る別の版。確定した山・谷で作る教科書の版の関数は"
                          "ライブラリに無い（定義表の既知答えで確かめる）"),
    # ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c）＝計算式の教科書の版（ライブラリの相当する関数と、作りの違い）
    "realized_vol_rv": (("hvol",), "hvol は平均を引いた標準偏差。平均を引かない版の関数はライブラリに無い"),
    "SQZ_ON_Carter": (("squeeze",), "squeeze はケルトナーの中心を終値の SMA・幅を真の値幅の SMA で作る。Carter の作りの関数はライブラリに無い"),
    "StochRSI素%K": (("stochrsi",), "stochrsi の k を 1 にしたもの（ならさない）"),
    "TRIX_EMAシグナル": (("trix", "ema"), "trix の本体を ema でならしたもの（trix のシグナルは単純移動平均）"),
    "TRIX_EMAヒスト": (("trix", "ema"), "同上（本体との差）"),
    "close vs SSF平均%": (("ssf",), "ssf は入力を2本の平均にしていない。Ehlers の式の関数はライブラリに無い"),
    "close vs TRIMA_TA%": (("trima",), "trima は偶数の n でも n/2+1 を2回。TA-Lib の偶数の形の関数はライブラリに無い"),
    "close vs VIDYA_CMO%": (("vidya",), "vidya は CMO の本数を n と同じにする。別に持つ形の関数はライブラリに無い"),
    "close vs HT_TRENDLINE_HL%": (("ht_trendline",), "入力を (高値＋安値)/2 にして呼ぶ"),
    "close vs MAMA_HL%": (("mama",), "入力を (高値＋安値)/2 にして呼ぶ"), "close vs FAMA_HL%": (("mama",), "同上"),
    "DPO教科書%": (("dpo", "sma"), "dpo の centered=False（いまの終値 − k本前の SMA）と値が違う。k本前の終値 − いまの SMA を sma で作る"),
    "ABER原作位置": ((), "aberration は HLC3 の SMA ± ATR の別の作り。原作（80本・2σ のボリンジャー）の関数は aberration の名ではライブラリに無い"),
    "THERMO原作%": (("thermo",), "thermo は絶対値を取る（内はらみ足も 0 にならない）。原作の関数はライブラリに無い"),
    "THERMO_EMA%": (("thermo", "ema"), "原作の温度計を ema でならす"),

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:5247「"SMC_SWEEP確定": ((), "pandas-ta の smc_sweep は直前 n 本の高安とヒゲの倍率で作る別の版。確定した山・谷で作る教科書の版の関数は"」
状態: 確定

#### 実装 25
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4699行（<モジュール直下>・全体の表 G-1＝ta の DPOIndicator を教科書の版の DPO に対応させる（今の DPO% は比べるために残す））
直す前の文字:
~~~
    "DPOIndicator": ("DPO%",),

~~~
直した後の文字:
~~~
    # ★2026-10-11（工事 m2c15-formula-textbook-20261011・全体の表 G-1・監査 CP60 の修正37 の補足）＝ta の DPOIndicator（k本前の終値 − SMA）を
    #   教科書の版に対応させる。今の DPO% は比べるために残す（M2-F-10f）。
    "DPOIndicator": ("DPO教科書%", "DPO%"),

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:4699「"DPOIndicator": ("DPO%",),」
状態: 確定

#### 実装 26
対象のファイル: .claude/memory/regime_detection_kb.md
直す箇所: 1290〜1295行（文書・足す15種で、材料の種類・一覧の行・部品の数が変わる＝KB の件数の囲み（gen_materials.py --write が書き出す所）を、写しで数えた文に置き換える（材料の文書の自己テストの B3・B4 と承認の前の検査 A12 が見る））
直す前の文字:
~~~
<!-- COUNTS_START gen_materials.py --write が実物から書き出す＝手で書き換えない -->
| 5 | 指標の種類 | **276種類**（engine_tuner が選べる **158**／選べない **118**） | materials.md の「engine_tuner が選べる指標の種類」の行 |
| 6 | 材料の一覧の行 | **282件**（在る。ほかに「入れない」45件） | materials.md の一覧 |
| 7 | パラメータまで展開した部品 | **516件**（＋別枠 8件＝**524**） | signal_families.json の parts と extra_parts |
| 8 | ★524 に膨らむ理由 | ADX7・ADX14・ADX21 のように、同じ指標のパラメータ違いを別々に数えているため | 部品の名前の実測 |
<!-- COUNTS_END -->
~~~
直した後の文字:
~~~
<!-- COUNTS_START gen_materials.py --write が実物から書き出す＝手で書き換えない -->
| 5 | 指標の種類 | **291種類**（engine_tuner が選べる **158**／選べない **133**） | materials.md の「engine_tuner が選べる指標の種類」の行 |
| 6 | 材料の一覧の行 | **297件**（在る。ほかに「入れない」45件） | materials.md の一覧 |
| 7 | パラメータまで展開した部品 | **516件**（＋別枠 8件＝**524**） | signal_families.json の parts と extra_parts |
| 8 | ★524 に膨らむ理由 | ADX7・ADX14・ADX21 のように、同じ指標のパラメータ違いを別々に数えているため | 部品の名前の実測 |
<!-- COUNTS_END -->
~~~
根拠の抜き書き: .claude/memory/regime_detection_kb.md:1290「<!-- COUNTS_START gen_materials.py --write が実物から書き出す＝手で書き換えない -->」
状態: 確定

#### 実装 27
対象のファイル: .claude/breaks/b160_dpo_tb_lib_shift.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: DPO教科書% を今の版（いまの終値 − k本前の SMA）に戻すと、観察の道具の自己テスト（上げ続ける足の既知答え）が落ちる
# EXPECT_MSG: DPO教科書%20: 手計算の既知答えと不一致
# b160_dpo_tb_lib_shift — DPO教科書% を今の版（いまの終値 − k本前の SMA）に戻すと、観察の道具の自己テスト（上げ続ける足の既知答え）が落ちる（工事 m2c15-formula-textbook-20261011・2026-10-11）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「DPO教科書%20: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '     (d.close.shift(int(0.5 * n) + 1) - _pta6.sma(close=d.close, length=n)) / d.close * 100)\n'
new = '     _pta6.dpo(close=d.close, length=n, centered=False) / d.close * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b160_dpo_tb_lib_shift] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 28
対象のファイル: .claude/breaks/b161_thermo_orig_abs.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: THERMO原作% を絶対値（ライブラリの版）に戻すと、観察の道具の自己テスト（内はらみ足の既知答え）が落ちる
# EXPECT_MSG: THERMO原作%: 手計算の既知答えと不一致
# b161_thermo_orig_abs — THERMO原作% を絶対値（ライブラリの版）に戻すと、観察の道具の自己テスト（内はらみ足の既知答え）が落ちる（工事 m2c15-formula-textbook-20261011・2026-10-11）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「THERMO原作%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    return np.maximum((d.high - d.high.shift(1)).clip(lower=0), (d.low.shift(1) - d.low).clip(lower=0))\n'
new = '    return np.maximum((d.high - d.high.shift(1)).abs(), (d.low.shift(1) - d.low).abs())\n'
if s.count(old) != 1:
    raise SystemExit("[b161_thermo_orig_abs] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 29
対象のファイル: .claude/breaks/b162_stochrsi_raw_smoothed.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: StochRSI素%K をならす形（k=3）に戻すと、観察の道具の自己テスト（教科書の独立実装）が落ちる
# EXPECT_MSG: StochRSI素%K7: 教科書の独立実装と不一致
# b162_stochrsi_raw_smoothed — StochRSI素%K をならす形（k=3）に戻すと、観察の道具の自己テスト（教科書の独立実装）が落ちる（工事 m2c15-formula-textbook-20261011・2026-10-11）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「StochRSI素%K7: 教科書の独立実装と不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=1).iloc[:, 0])\n'
new = '     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=3).iloc[:, 0])\n'
if s.count(old) != 1:
    raise SystemExit("[b162_stochrsi_raw_smoothed] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 30
対象のファイル: .claude/breaks/b163_trix_ema_signal_sma.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: TRIX_EMAシグナル のシグナルを単純移動平均（今の版）に戻すと、観察の道具の自己テスト（教科書の独立実装）が落ちる
# EXPECT_MSG: TRIX_EMAシグナル(7,9): 教科書の独立実装と不一致
# b163_trix_ema_signal_sma — TRIX_EMAシグナル のシグナルを単純移動平均（今の版）に戻すと、観察の道具の自己テスト（教科書の独立実装）が落ちる（工事 m2c15-formula-textbook-20261011・2026-10-11）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「TRIX_EMAシグナル(7,9): 教科書の独立実装と不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    return tx, _pta6.ema(close=tx, length=g_)\n'
new = '    return tx, _pta6.sma(close=tx, length=g_)\n'
if s.count(old) != 1:
    raise SystemExit("[b163_trix_ema_signal_sma] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 31
対象のファイル: .claude/breaks/b164_rvol_rv_mean_subtracted.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: realized_vol_rv を平均を引く形に戻すと、観察の道具の自己テスト（一定の割合で増える足の既知答え）が落ちる
# EXPECT_MSG: realized_vol_rv20: 手計算の既知答えと不一致
# b164_rvol_rv_mean_subtracted — realized_vol_rv を平均を引く形に戻すと、観察の道具の自己テスト（一定の割合で増える足の既知答え）が落ちる（工事 m2c15-formula-textbook-20261011・2026-10-11）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「realized_vol_rv20: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '     np.sqrt((np.log(d.close / d.close.shift()) ** 2).rolling(n).sum() / n) * 100)\n'
new = '     np.log(d.close / d.close.shift()).rolling(n).std(ddof=0) * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b164_rvol_rv_mean_subtracted] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 32
対象のファイル: .claude/breaks/b165_ssf_avg_single_input.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: close vs SSF平均% の入力を1本（今の版）に戻すと、観察の道具の自己テスト（教科書の独立実装）が落ちる
# EXPECT_MSG: close vs SSF平均%20: 教科書の独立実装と不一致
# b165_ssf_avg_single_input — close vs SSF平均% の入力を1本（今の版）に戻すと、観察の道具の自己テスト（教科書の独立実装）が落ちる（工事 m2c15-formula-textbook-20261011・2026-10-11）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「close vs SSF平均%20: 教科書の独立実装と不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        out[i] = c1 * (v[i] + v[i - 1]) / 2.0 + c2 * out[i - 1] + c3 * out[i - 2]\n'
new = '        out[i] = c1 * v[i] + c2 * out[i - 1] + c3 * out[i - 2]\n'
if s.count(old) != 1:
    raise SystemExit("[b165_ssf_avg_single_input] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 33
対象のファイル: .claude/breaks/b166_sqz_carter_scalar_fixed.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: SQZ_ON_Carter の kc_scalar を使わず 1.5 を固定で書くと、観察の道具の自己テストの軽い口（名前に出さない引数の番人⑥＝selftest_catalog）が落ちる
# EXPECT_MSG: 名前に出さない引数: SQZ_ON_Carter の kc_scalar を変えても列が変わらない
# b166_sqz_carter_scalar_fixed — SQZ_ON_Carter の kc_scalar を使わず 1.5 を固定で書くと、観察の道具の自己テストの軽い口（名前に出さない引数の番人⑥＝selftest_catalog）が落ちる（工事 m2c15-formula-textbook-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_catalog の番人⑥）（observe_diag.py --selftest-catalog）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「名前に出さない引数: SQZ_ON_Carter の kc_scalar を変えても列が変わらない」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    on = ((mid - bb_std * sd) > (km - kc_scalar * atr)) & ((mid + bb_std * sd) < (km + kc_scalar * atr))\n'
new = '    on = ((mid - bb_std * sd) > (km - 1.5 * atr)) & ((mid + bb_std * sd) < (km + 1.5 * atr))\n'
if s.count(old) != 1:
    raise SystemExit("[b166_sqz_carter_scalar_fixed] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 33 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 新しいパラメータ（EMA の本数・CMO の本数・原作の本数と倍率・Carter の4つ）を名前に出さない引数にする | 名前に入れると資料の行と軸の数が合わず、探し方の決定「名前に値を入れて指標を増やさない」に反する（まこさん「進めて良い」の1） | 名前に出す |
| 2 | THERMO の EMA の本数の最初の値をライブラリの既定 20 にする | 資料の2つ（20・22）はどちらも「ブログ等」で最初の値にならない＝選び方の規則の「無ければ既定の値」（まこさん「進めて良い」の2） | 22 を選ぶ（CC が選ぶことになる） |
| 3 | PMAX 原作を入れない | 原典のコードの全文が資料に無い。新しく Web を調べない決まり（まこさん「進めて良い」の3） | 1行の逐語から作りを推測する |
| 4 | Aberration 原作を別の材料にし、BB%b の範囲は触らない | 原作の 80本は BB%b の範囲（10〜50）の外。範囲を広げるのは資料の規則の外（まこさん「進めて良い」の4） | BB%b の範囲を 80 まで広げる |
| 5 | SQZ_ON_Carter の ATR を Wilder にする | 監査の文「幅を ATR」（ライブラリは真の値幅の SMA）。ATR の標準は Wilder（参照表の _wilder と同じ） | 真の値幅の SMA（ライブラリの版と同じになる） |
| 6 | THERMO_EMA% の元を原作の温度計にする | 教科書の版を足す工事なので、EMA の元も教科書（原作）の形にする | ライブラリの版（絶対値）を EMA でならす |
| 7 | ta の DPOIndicator を（DPO教科書%・DPO%）の2つに対応させる | 全体の表 G-1＝教科書の版に対応させ、今の DPO% は比べるために残す（まこさん「すべて案どおりでよい」） | DPO% を対応から外す（「使う」から落ちる） |
| 8 | K-3a・K-3b の対応表は封のまま触らず、K-3c の15種は alias_map_k3c.json に書く | 封をし直さずに済む。読む道具3本は alias_maps.py で全部のファイルを合わせて読む | 前の対応表に書き足す |
| 9 | この工事（コード）と、G-1 の後の2つ目の工事（15種の設定を写す）に分ける | 15種は G-1 まで「使う」でなく資料の行も無い。K-3a・K-3b と同じ | 道具が作るはずの表まで指示に入れて1回で当てる |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=65c511ea5465340b gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b160_dpo_tb_lib_shift.sh` | #1 | 今の版（いまの終値 − k本前の SMA）に戻す |
| `b161_thermo_orig_abs.sh` | #2 | 絶対値（ライブラリの版）に戻す |
| `b162_stochrsi_raw_smoothed.sh` | #3 | ならす形（k=3）に戻す |
| `b163_trix_ema_signal_sma.sh` | #4 | シグナルを単純移動平均に戻す |
| `b164_rvol_rv_mean_subtracted.sh` | #5 | 平均を引く形に戻す |
| `b165_ssf_avg_single_input.sh` | #6 | 入力を1本に戻す |
| `b166_sqz_carter_scalar_fixed.sh` | #7 | kc_scalar を使わず 1.5 を固定で書く |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 型の表が変わる | G-1 で作り直し、まこさんに再承認していただく（4-4 の4） |
| 2 | 名前に出さない引数の最初の値（Carter の4つ・原作の 80・2.0・CMO の 9・EMA の 20）が、この市場に合っているか | 範囲で探すのは工事2（M2-F-10b）。この工事は材料を足すだけ |
| 3 | VIDYA_CMO・SSF平均 の計算は Python の繰り返しで、全体の自己テストが重くなる | 写しの実測 139秒（4-14） |
| 4 | 2つ目の工事で写す設定に、最初の値も範囲も出ない種類が在る（資料の規則で「無い」） | P-6・P-7・H-1 の工事で扱う（next_step の 5） |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（--design） | 1分未満 | 前の工事で、当てる道具は1秒未満で終わった |
| 全体の自己テスト | 139秒 | 4-14 |
| 壊すプログラム | 1本あたり約 139秒（全体の自己テスト）×7本 | 写しで壊し方を並べて走らせた（k3c_draft_build.py の [8]） |
| G-1 の表の作り直しと資料の道具4本 | 約2分 | 写しの実測（オン・オフの表 約3秒・資料の道具4本 約6秒）と前の工事の実測 |
| 監査に出す前のチェック | 約10分 | 前の工事の実測（pre_audit_check.py --run） |
| まこさんの承認 | この工事の設計書1回・型の表の再承認1回（変われば）・2つ目の工事の設計書1回 | 4-4 |
| 2つ目の工事 | K-3b の2つ目の工事（m2c15-shape-settings-20261009）と同じ流れ（案 → OK → 設計書 → 承認 → 当てる） | worklog 20261010 §3 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝今の15種はライブラリの作り（平均を引く・絶対値・入力が終値・ならす・SMA のシグナル・CMO の本数を n と同じにする ほか）で、教科書の式と値が違う（監査 CP60 の表 19・62・65〜69・79・86・87・96・100・102・113・129・130・138）。教科書の版が無いので、engine_tuner はその情報を材料から取り出せず、どちらが良いかも比べられなかった。この工事で教科書の版を足し、M2-F-10f で比べられるようにする。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。M2-F で使える材料が15種 増えます。

**③ root か symptom か**＝root です。比べる相手（教科書の版）が無いことが原因で、それを足します。

**④ ベースアップ**＝15種の作りは、監査 CP60 の修正37・45・47〜53 の本文と、監査が引いた原典の逐語（StockCharts・linnsoft・ta-lib.org・MAMA.pdf・georgepruitt.com・TradingView・Wikipedia）から取った。ライブラリの作りは監査 CP60 の4節の表（ファイルと行）で確かめた。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。名前に出さない引数の最初の値は資料の既定かライブラリの既定です。既知答えは合成の足から手で計算できる値です。壊し方の値も、当てた後の中身の行から道具が取りました。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝計算式が教科書と違う15種に、教科書の版を今の版を残して足す（K-3c の1つ目の工事。15種の設定を写すのは G-1 の後の2つ目の工事）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。条件をつなぐものではなく、教科書の作りの材料を足すだけです |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 15種の名前に出る軸は今の版と同じ一覧から作り、探す範囲は資料から道具が写します |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **既知答えが、本物の値動きでの正しさまで見るか** | 見ません。合成の足で、式の向き・内はらみ足・平均を引かないことを見るだけです |
| **名前に出さない引数の最初の値が、この市場に合っているか** | 見ません。範囲で探すのは工事2 です |
| **資料の値そのものが正しいかを、照らしの道具が見るか** | 見ません。照らしの道具は、資料と設定ファイルが同じかだけを見ます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=2356ea77129168b4 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝observe_diag.py・indicator_reference_diag.py・regime_detection_kb.md（件数の囲み）と、新しい壊すプログラムを【7-8】に書いた。主なファイルは observe_diag.py（材料の計算）。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝observe_diag.py・触る関数は道具が構文木の差から数えた）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム（NEW_FILE）。手本は b142（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝経緯・目的を工事の内側だけで答え、上位（機能要件・探し方）に結び付けなかった（166回目）。この工事は、材料に要る4つ（教科書の作り・役割に沿う値・範囲から探せる形・代表の値）の①に当たるものとして組んだ。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 新しい部品は、未来を見ない形にした（DPO教科書% は k本前の終値といまの平均）。当てた後に H2 を取り直す。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 行番号を指す文書は、当てた後に動く（observe_diag.py・indicator_reference_diag.py に行が増える）。設計書の行番号は当てる前の実物のもの。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、探す文字の数が当てる前と後で同じことを道具が数えた（4-13 の5）。走らせるコマンドの旗は変えない。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムが測るのは、観察の道具の全体の自己テストで、本物の結果の置き場には書かない。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 触る関数（DESIGN_CONTRACT の impl_functions・道具が書いた）＝observe_diag.py：<モジュール直下>・_atr_wilder・_mama_hl・_sqz_carter・_ssf_avg・_thermo_orig・_trima_ta・_trix_ema・_vidya_cmo・build_catalog／indicator_reference_diag.py：<モジュール直下>・_geo_case・_ssf2_avg・_tb_aber_orig・_tb_dpo_tb・_tb_pos_ssf_avg・_tb_pos_trima_ta・_tb_pos_vidya_cmo・_tb_rvol_rv・_tb_sqz_carter・_tb_stochrsi_raw・_tb_thermo_ema・_tb_thermo_orig・_tb_trix_ema_h・_tb_trix_ema_s・_thermo_in_case・_thermo_orig_arr・_trima_ta・_vidya_cmo。self_check_calls と must_use の名前は、当てた後の構文木に在ることを道具が ast で照らした。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足すコマンドの旗は無い。資料の対応表（alias_map_k3c.json）は .claude/state の道具の側で、設計書の前に済ませた。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2c15-formula-textbook-20261011）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝観察の道具の既知答え・独立の実装・名前に出さない引数の番人・照らしの道具の①②と、壊すプログラム（わざと壊して落ちるか）。写しで走らせ、全部 通った。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | F-1・F-3＝DPO教科書% が、k本前の終値 − いまの n本平均 になる（既知答えが通る） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | 今の版（いまの終値 − k本前の SMA）に戻す | `b160_dpo_tb_lib_shift.sh` | — | **未着手** |
| 2 | F-1・F-3＝THERMO原作% が、内はらみ足で 0 になる（既知答えが通る） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | 絶対値（ライブラリの版）に戻す | `b161_thermo_orig_abs.sh` | — | **未着手** |
| 3 | F-1・F-3＝StochRSI素%K が、ならさない値になる（独立の実装と合う） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | ならす形（k=3）に戻す | `b162_stochrsi_raw_smoothed.sh` | — | **未着手** |
| 4 | F-1・F-3＝TRIX_EMAシグナル が EMA になる（独立の実装と合う） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | シグナルを単純移動平均に戻す | `b163_trix_ema_signal_sma.sh` | — | **未着手** |
| 5 | F-1・F-3＝realized_vol_rv が平均を引かない（既知答えが通る） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | 平均を引く形に戻す | `b164_rvol_rv_mean_subtracted.sh` | — | **未着手** |
| 6 | F-1・F-3＝close vs SSF平均% の入力が2本の平均になる（独立の実装と合う） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | 入力を1本に戻す | `b165_ssf_avg_single_input.sh` | — | **未着手** |
| 7 | F-2＝SQZ_ON_Carter の名前に出さない引数（kc_scalar）が計算に届く（自己テストの⑥の番人が通る） | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | kc_scalar を使わず 1.5 を固定で書く | `b166_sqz_carter_scalar_fixed.sh` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=acf95a18d7d59915 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/observe_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `_atr_wilder` | （この関数は実物に無い） |
| `_sqz_carter` | （この関数は実物に無い） |
| `_trix_ema` | （この関数は実物に無い） |
| `_ssf_avg` | （この関数は実物に無い） |
| `_trima_ta` | （この関数は実物に無い） |
| `_vidya_cmo` | （この関数は実物に無い） |
| `_mama_hl` | （この関数は実物に無い） |
| `_thermo_orig` | （この関数は実物に無い） |
| `build_catalog` | 1487 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 188件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=8e308e00259103fb gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/observe_diag.py",
  "_impl_file の意味": "照らす相手は実在するファイル。足す15種の計算（_atr_wilder・_sqz_carter・_trix_ema・_ssf_avg・_trima_ta・_vidya_cmo・_mama_hl・_thermo_orig）とカタログ（build_catalog）が在る、観察の道具を照らす。",
  "impl_functions": {
    "scripts/priority_rebuild/observe_diag.py": [
      "<モジュール直下>",
      "_atr_wilder",
      "_mama_hl",
      "_sqz_carter",
      "_ssf_avg",
      "_thermo_orig",
      "_trima_ta",
      "_trix_ema",
      "_vidya_cmo",
      "build_catalog"
    ],
    "scripts/priority_rebuild/indicator_reference_diag.py": [
      "<モジュール直下>",
      "_geo_case",
      "_ssf2_avg",
      "_tb_aber_orig",
      "_tb_dpo_tb",
      "_tb_pos_ssf_avg",
      "_tb_pos_trima_ta",
      "_tb_pos_vidya_cmo",
      "_tb_rvol_rv",
      "_tb_sqz_carter",
      "_tb_stochrsi_raw",
      "_tb_thermo_ema",
      "_tb_thermo_orig",
      "_tb_trix_ema_h",
      "_tb_trix_ema_s",
      "_thermo_in_case",
      "_thermo_orig_arr",
      "_trima_ta",
      "_vidya_cmo"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数（実装の指示を全部 当てる前と後の構文木を関数ごとに比べて、k3c_proposal_build.py が数えた）。",
  "self_check_calls": [
    "_atr_wilder",
    "_sqz_carter",
    "_trix_ema",
    "_ssf_avg",
    "_trima_ta",
    "_vidya_cmo",
    "_mama_hl",
    "_thermo_orig",
    "build_catalog"
  ],
  "_self_check_calls の意味": "実装の後の observe_diag.py に在るはずの、この工事が足す・直す関数の名前。",
  "must_use": {
    "_sqz_carter": [
      "_atr_wilder"
    ]
  },
  "_must_use の意味": "Carter の作りのスクイーズが、Wilder の ATR（_atr_wilder）を使う（k3c_proposal_build.py が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は、材料を足すだけ。外から読む一覧の形（カタログの1件の形・参照表の欄・設定の欄）は変えない。",
  "generated_from": {
    "impl_functions": "当てる前と後の関数ごとの構文木の差（k3c_proposal_build.py が数えた）",
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
   "find_material",
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
  "selftest_catalog": [
   "build_catalog",
   "build_features",
   "find_material",
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
   "selftest_catalog",
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
  "--selftest-catalog",
  "--selftest-insp5",
  "--selftest-rank-demand",
  "--selftest-rank-resume"
 ]
}
```

<!-- ACC_SPEC_END -->

<!-- ARC iter="m2c15-shape-structure-20261009" -->

# 設計書｜K-3b 形と構造＝確定した山・谷で作る教科書の版を4種と、レンジ幾何の下半分位置を、今の版を残して足す。M2-C-15

TARGET: .claude/memory/regime_detection_kb.md, scripts/priority_rebuild/engine_tuner_exec.py, scripts/priority_rebuild/engine_tuner_fire_diag.py, scripts/priority_rebuild/engine_tuner_gen.py, scripts/priority_rebuild/gen_indicator_switch.py, scripts/priority_rebuild/indicator_reference_diag.py, scripts/priority_rebuild/observe_diag.py, .claude/breaks/b151_w_fractal_not_first.sh, .claude/breaks/b152_sr_fractal_counts_bars.sh, .claude/breaks/b156_sr_fractal_unconfirmed.sh, .claude/breaks/b153_smc_fractal_no_close_back.sh, .claude/breaks/b154_lower_half_upper_span.sh, .claude/breaks/b155_geo_mako_not_read.sh
NEW_FILE: .claude/breaks/b151_w_fractal_not_first.sh, .claude/breaks/b152_sr_fractal_counts_bars.sh, .claude/breaks/b156_sr_fractal_unconfirmed.sh, .claude/breaks/b153_smc_fractal_no_close_back.sh, .claude/breaks/b154_lower_half_upper_span.sh, .claude/breaks/b155_geo_mako_not_read.sh
MODEL: .claude/breaks/b142_rci_list_stale.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2c15-shape-structure-20261009/ok_k3b_20261009`・`m2c15-shape-structure-20261009/ok_k3b_design_20261009`・`m2c15-shape-structure-20261009/okd_k3b_20261009`・`m2c15-shape-structure-20261009/okd_k3b_design_20261009`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2c15-shape-structure-20261009/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-shape-structure-20261009 --write`。検出＝`--work m2c15-shape-structure-20261009 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=c21876ce353e771e gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2c15-shape-structure-20261009/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2c15-shape-structure-20261009/ok_k3b_20261009.txt`（まこさんの発言）・`verbatim/m2c15-shape-structure-20261009/ok_k3b_design_20261009.txt`（まこさんの発言）・`verbatim/m2c15-shape-structure-20261009/okd_k3b_20261009.txt`（まこさんが OK した CC の文）・`verbatim/m2c15-shape-structure-20261009/okd_k3b_design_20261009.txt`（まこさんが OK した CC の文）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝699 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_k3b_20261009` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_k3b_design_20261009` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_k3b_20261009` | V01〜V09（9 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_k3b_20261009` | V10〜V45（36 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V46〜V51（6 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V52〜V57（6 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V58〜V70（13 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V71〜V77（7 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V78〜V87（10 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V88〜V97（10 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V98〜V99（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V100〜V101（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V102〜V104（3 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V105〜V106（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V107〜V108（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V109〜V115（7 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V116〜V124（9 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V125〜V130（6 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V131〜V132（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V133〜V134（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V135〜V136（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V137〜V143（7 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V144〜V478（335 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V479〜V488（10 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V489〜V495（7 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V496〜V505（10 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V506〜V512（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V513〜V514（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V515〜V516（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V517〜V521（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V522〜V532（11 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V533〜V553（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V554〜V562（9 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V563〜V674（112 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_k3b_20261009` | V675〜V679（5 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `okd_k3b_design_20261009` | V01〜V18（18 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
監査 CP60 は、今の材料のいくつかが教科書と違う作りだと指摘しました。W字は、教科書では確定した2つの谷とその間の最高値（ネック）で作り、ネックを上抜けた足で完成しますが、今の材料は窓の前半と後半の最安値と中央の区間の最高値で近似し、条件が続く間ずっと1を出します。S-Rタッチは、教科書では値段が跳ね返された山と谷の数ですが、今の材料は帯に掛かった足の本数（滞在時間）です。SMC_SWEEP は、教科書では確定した山か谷をヒゲで抜けて終値で戻した足ですが、今の材料はライブラリの作り（直前15本の高安・ヒゲが実体の1.5倍）です。帯内位置% は、下半分も上半分の幅で割っています。まこさんは、今の版を残し、教科書の版を別の材料として足して、後で比べる形を決めました（K-3 の「A」）。作りの3点（確定の本数は名前に出さない引数・SMC_SWEEP の教科書の版はライブラリの数字を使わない・下半分位置を使う）にも「よい」をいただきました。この工事は、その4種と下半分位置を観察の道具と参照表と印を作る道具に足します。前から在る列の値は1本も変えません。どちらの版が良いかを比べるのは、この工事ではなく M2-F-10f です。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 確定の決まりの切り出し（F-1） | `grep -n -F 'def _fractal_marks' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、_fractal_levels の後ろに在る | （終了コード 1） |
| 足す4種の登録（F-1） | `grep -n -F '_reg("S-Rタッチ確定数"' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、登録の行に在る | （終了コード 1） |
| 下半分位置の定義（F-3） | `grep -n -F '"下半分位置": dict(' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py` | 実装の前は、無い。実装の後は、レンジ幾何の定義表の中に在る | （終了コード 1） |
| geo_on の源4（F-4） | `grep -n -F 'def source_mako_geo' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_indicator_switch.py` | 実装の前は、無い。実装の後は、build の前に在る | （終了コード 1） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

［自動］印のファイル・型の表・格子と範囲
<!-- ACC_MATERIALS_START hash=20c8982b5d895b52 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`indicator_switch.json`・`signal_families.json`・`search_limits.json`。

**探す指標＝印がオンの 156種**（印を切り替えると、この一覧も設計も変わります）。

```
ADX・DI差・MACD線%・MACDヒスト%・MACDシグナル線%・RSI・ROC・Stoch%K・Stoch%D・MFI・CMF・OBV傾き・転換線・基準線・RCI・EMA傾き・ATR%・BB%b・BB幅・realized_vol・Donchian幅・volume_ratio・swing高値距離・swing安値距離・高値からの経過バー・安値からの経過バー・形スコア・W字・fractal高値距離%・fractal安値距離%・高値切り上げ幅%・安値切り上げ幅%・構造破断距離%・close vs EMA・close vs SMA・close vs VWAP・close vs VWAP典型・当日VWAP・Keltner上・Keltner下・n本高値・n本安値・pivotPP・pivotR1・pivotS1・前期間pivotPP・前期間pivotR1・前期間pivotS1・前週pivotPP・前週pivotR1・前週pivotS1・fib位置・POC・VAH・VAL・前日POC・前日VAH・前日VAL・当日POC・当日VAH・当日VAL・MMI・S-Rタッチ1時間ATR・S-Rタッチ数・AO%・CCI・ER・KST・KSTシグナル・PPO・PPOシグナル・PPOヒスト・PVO・PVOシグナル・PVOヒスト・SMC_SWEEP・SQZ_ON・STC・STCstoch・StochRSI%K・StochRSI%D・TRIX・TRIXシグナル・TRIXヒスト・TSI・TSIシグナル・TSIヒスト・UO・close vs ALMA%・close vs DEMA%・close vs FWMA%・close vs HILO%・close vs HMA%・close vs HT_TRENDLINE%・close vs HWMA%・close vs JMA%・close vs KAMA%・KAMA傾き%・close vs LINREG%・close vs LRb%・close vs MAMA%・close vs FAMA%・close vs MCGD%・close vs MIDPOINT%・close vs MIDPRICE%・close vs MMAR%・close vs PWMA%・close vs RAINBOW%・close vs RMA%・close vs SINWMA%・close vs SSF%・close vs SWMA%・close vs T3%・close vs TEMA%・close vs TRIMA%・close vs TSF%・close vs VIDYA%・close vs VWMA%・close vs WMA%・WMA傾き%・close vs ZLMA%・AROONU・AROOND・AROONOSC・CHOP・close vs CKSPl%・close vs CKSPs%・DPO%・close vs PMAX%・close vs PSAR%・PSAR加速・PSAR反転・close vs SAREXT%・VHF・VTXP・VTXM・EFI比・EOM比・NVI傾き・PVT傾き・MAD比・stdev%・close vs MEDIAN%・close vs ABER_ZG%・ABER位置・close vs ACCBL%・close vs ACCBU%・close vs CE_L%・close vs CE_S%・HWC位置・HWC幅%・MASSI・THERMO%・TR%・UI・HT_DCPHASE
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
| `material_param_ranges` | {"ADX": [{"kind": "int", "lo": 7, "hi": 21}], "DI差": [{"kind": "int", "lo": 7, "hi": 21}], "MACD線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}], "MACDヒスト%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "MACDシグナル線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "転換線": [{"kind": "int", "lo": 5, "hi": 12}], "基準線": [{"kind": "int", "lo": 13, "hi": 26}], "EMA傾き": [{"kind": "int", "lo": 9, "hi": 200}], "KSTシグナル": [{"kind": "int", "lo": 9, "hi": 9}], "PPO": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOシグナル": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOヒスト": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "TRIX": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TSI": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIシグナル": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIヒスト": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "KAMA傾き%": [{"kind": "int", "lo": 7, "hi": 10}], "WMA傾き%": [{"kind": "int", "lo": 20, "hi": 200}], "AROONU": [{"kind": "int", "lo": 7, "hi": 288}], "AROOND": [{"kind": "int", "lo": 7, "hi": 25}], "AROONOSC": [{"kind": "int", "lo": 7, "hi": 25}], "VTXP": [{"kind": "int", "lo": 14, "hi": 30}], "VTXM": [{"kind": "int", "lo": 14, "hi": 30}], "RSI": [{"kind": "int", "lo": 2, "hi": 21}], "ROC": [{"kind": "int", "lo": 9, "hi": 24}], "Stoch%K": [{"kind": "int", "lo": 5, "hi": 21}], "Stoch%D": [{"kind": "int", "lo": 5, "hi": 21}], "MFI": [{"kind": "int", "lo": 10, "hi": 20}], "CMF": [{"kind": "int", "lo": 20, "hi": 36}], "OBV傾き": [{"kind": "int", "lo": 10, "hi": 20}], "BB%b": [{"kind": "int", "lo": 10, "hi": 50}, {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}], "volume_ratio": [{"kind": "int", "lo": 20, "hi": 50}], "CCI": [{"kind": "int", "lo": 7, "hi": 21}], "PVO": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOシグナル": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOヒスト": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "StochRSI%K": [{"kind": "int", "lo": 7, "hi": 21}], "StochRSI%D": [{"kind": "int", "lo": 7, "hi": 21}], "DPO%": [{"kind": "int", "lo": 14, "hi": 40}], "EFI比": [{"kind": "int", "lo": 10, "hi": 20}], "EOM比": [{"kind": "int", "lo": 10, "hi": 20}], "NVI傾き": [{"kind": "int", "lo": 10, "hi": 20}], "PVT傾き": [{"kind": "int", "lo": 10, "hi": 20}], "ATR%": [{"kind": "int", "lo": 5, "hi": 21}], "BB幅": [{"kind": "int", "lo": 10, "hi": 50}, {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}], "realized_vol": [{"kind": "int", "lo": 10, "hi": 50}], "Donchian幅": [{"kind": "int", "lo": 10, "hi": 20}], "MMI": [{"kind": "int", "lo": 200, "hi": 500}], "ER": [{"kind": "int", "lo": 7, "hi": 21}], "CHOP": [{"kind": "int", "lo": 7, "hi": 21}], "VHF": [{"kind": "int", "lo": 7, "hi": 28}], "MAD比": [{"kind": "int", "lo": 20, "hi": 50}], "stdev%": [{"kind": "int", "lo": 10, "hi": 50}], "UI": [{"kind": "int", "lo": 7, "hi": 21}], "高値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "安値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "形スコア": [{"kind": "int", "lo": 24, "hi": 96}], "W字": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.0, "hi": 0.06, "dec": 3}], "fractal高値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "fractal安値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "高値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "安値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "構造破断距離%": [{"kind": "int", "lo": 2, "hi": 3}], "close vs EMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs SMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs VWAP": [{"kind": "int", "lo": 288, "hi": 288}], "Keltner上": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "Keltner下": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "n本高値": [{"kind": "int", "lo": 10, "hi": 50}], "n本安値": [{"kind": "int", "lo": 10, "hi": 50}], "pivotPP": [{"kind": "int", "lo": 288, "hi": 288}], "pivotR1": [{"kind": "int", "lo": 288, "hi": 288}], "pivotS1": [{"kind": "int", "lo": 288, "hi": 288}], "fib位置": [{"kind": "int", "lo": 14, "hi": 96}], "S-Rタッチ1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}], "S-Rタッチ数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}], "close vs ALMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs DEMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs FWMA%": [{"kind": "int", "lo": 10, "hi": 20}], "close vs HMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs JMA%": [{"kind": "int", "lo": 3, "hi": 80}], "close vs KAMA%": [{"kind": "int", "lo": 7, "hi": 30}], "close vs LINREG%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs LRb%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs MCGD%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs MIDPOINT%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MIDPRICE%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MMAR%": [{"kind": "int", "lo": 10, "hi": 35}], "close vs PWMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs RAINBOW%": [{"kind": "int", "lo": 2, "hi": 2}, {"kind": "int", "lo": 1, "hi": 10}], "close vs RMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SINWMA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs SSF%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SWMA%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs T3%": [{"kind": "int", "lo": 8, "hi": 200}], "close vs TEMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TRIMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TSF%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs VIDYA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs VWMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs WMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs MEDIAN%": [{"kind": "int", "lo": 4, "hi": 200}], "RCI": [{"kind": "int", "lo": 5, "hi": 52}], "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}]} |

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
| 1 | 足した版と今の版を比べること | 比べるのは M2-F-10f。この工事は材料を足すだけ | 監査 CP60 の修正43・44・46・65 の補足 |
| 2 | 確定の本数 k を範囲で探すこと | 名前に出さない引数へ値を渡すのは工事2（M2-F-10b） | まこさん「よい」の1 |
| 3 | SMC_SWEEP の向きの印を True にすること | 全体の表の Y-5（そのまま）。SMC_SWEEP確定 も False | indicator_review/m2c15_全体の表.md の Y-5 |
| 4 | 法則どおりの帯の部品・段1 の候補の直し | B-1（4つの工事の最後）と工事2 | まこさん「A」・worklog 20261003 §35 |
| 5 | 成績表（material_ranking.json）の作り直し | M2-D-8。増える列は、作り直すまで段の候補の順位に出ない | K-3a と同じ |
| 6 | K-3c の種類 | 次の工事 | まこさん「A」 |
| 7 | 監査に出す前のチェックの自己テストの P7-1 の落ち | この工事の前から在る。next_step §6 に積んである | worklog 20261007 §11 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | W字確定谷 の許容幅（2つの谷の差）の探す範囲に、K-7 の範囲の直し（0〜0.06）を掛けるか | 掛ける。K-7 の直しは、W字 の資料の行の教科書の文（谷の差 0〜4%・0〜6%）から決めた範囲で、W字確定谷は同じ資料の行を使い、同じ「2つの谷の差」の許容を持つ。掛けないと、写しの G-1 の試しで 0.003 の1点になる（点で限定する形＝作ってはいけないもの2番）。★直しは種類の名前「W字」にだけ掛かる作り（k7_range_fix.json）なので、2つ目の工事で、対応表の元の種類の直しを引く形にする | 写しの G-1 の試しの出力（k3b_check.json の「工事2で写す設定」）・K-7 の「OK」（ok_k7_range_20261007） |
| 2 | W字確定谷 の2つの谷をどこから取るか | 窓 n 本（今の足まで）の中で確定した直近の2つ（谷の足がどちらも窓の中・2つの谷の間に1本以上）。ネックは2つの谷の間の足の最高値 | 監査 CP60 の修正43「2つの底＝窓の中の確定した谷・ネック＝2つの谷の間の最高値」 |
| 3 | S-Rタッチ確定 の窓に、今の足で確定した山・谷を入れるか | 入れない（確定した足が [i−n, i)）。今の S-Rタッチ数 も今の足を窓に入れていないので、同じ決まりにする | observe_diag.py の _sr_touch（窓 [i−n, i)） |
| 4 | SMC_SWEEP確定 は、いつまでに確定した山・谷を使うか | 1本前までに確定した直近の山・谷。今の足で確定する山・谷は、今の足の値段で決まるので使わない | 監査 CP60 の修正46・ライブラリの版も1本前までの高安（shift(1)） |
| 5 | 監査の出し方 | この工事と2つ目の工事を、工事ごとに1通ずつ実装の監査に出す（依頼書の道具は1つの工事に1通・K-3a と同じ） | 教訓 L-670・L-672・まこさん「2通に分ける」（K-3a） |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、確定した山・谷で作る教科書の版を、今の版を残して別の材料として足す工事です。**監査 CP60 は、W字・S-Rタッチ・SMC_SWEEP の今の作りが教科書と違い（確定した山・谷を使っていない）、帯内位置% の下半分の尺度が違うと指摘しました（修正43・44・46・65）。まこさんは、今の版を残して教科書の版を足し、後で比べる形を決めました（K-3 の「A」）。どちらが良いかを比べるのは M2-F-10f で、この工事は材料を足すだけです。
**①足す4種とレンジ幾何の1列（名前・作り）。**
| 材料の名前 | 作り | 出どころ |
|---|---|---|
| W字確定谷(n,tol) | 窓 n 本（今の足まで）の中で確定した直近の2つの谷（前後 k 本）の値段の差が tol×終値 以内で、2つ目の谷の後に終値がネック（2つの谷の間の最高値）を最初に上抜けた足だけ 1・それ以外 0 | 監査 CP60 の修正43・StockCharts「Breaking resistance from the highest point between the troughs completes the Double Bottom Reversal.」 |
| S-Rタッチ確定数(n,tol) | 今の足の前の n 本の中で確定した山（高値）と谷（安値）のうち、今の終値 ± tol×終値 に入るものの数 | 修正44「教科書の数え方＝窓の中の確定した山・谷のうち、今の値段の帯に入る数」 |
| S-Rタッチ確定1時間ATR(n,倍率,ATR の期間) | 上と同じ数え方で、許容幅＝倍率 × 1時間足の ATR% を 0.15%〜0.6% に収めたもの | 修正44・今の S-Rタッチ1時間ATR と同じ許容幅 |
| SMC_SWEEP確定 | 1本前までに確定した直近の谷を安値で割り、終値でその上に戻した足＝+1・山を高値で抜き、終値でその下に戻した足＝−1 | 修正46・LuxAlgo「a wick through a prior swing high or low…followed by a close back inside the old range」 |
| 下半分位置（レンジ幾何の列） | (終値 − mid) ÷ (mid − sup_lo)。下半分は下半分の幅で割る（帯内位置% は下半分も上半分の幅で割る） | 修正65 の直した後の文字 |
- 確定の本数 k は、4種とも名前に出さない引数で、最初の値は 2 です（資料の fractal の既定。資料の調べ verify_out_g4.json で、LuxAlgo・MetaTrader 5・TradingView・FXOpen の4件の出どころが 2 と一致した）。範囲で探すのは工事2（M2-F-10b）です。
- 確定した山・谷は、今の _fractal_levels の確定の決まりを _fractal_marks に切り出して使います（計算は1文字も変えない・前から在る列の値の違い0本）。
**②既知答え（手で計算できる合成の足）。**
| 材料 | 合成の足 | 答え |
|---|---|---|
| W字確定谷 | 今の W字 の既知答えと同じ足（_w_case）＝谷1 100・ネック 108・谷2 100.2 か 92・最後の終値 109 | 谷2 が 100.2 なら 1、92 なら 0（今の W字 と同じ答え）。最後の2本の終値を 109 にすると、1本前が 1・最後は 0（「最初に上抜けた足だけ」。今の W字 なら最後も 1） |
| S-Rタッチ確定数・確定1時間ATR | n＋12 本の平らな足（全部 100）に、山 100.1・101・100.1 と谷 99.9 を置き、最後の足の2本前にも山 100.1 を置く | 3（100.1 の山2つ・99.9 の谷1つ。101 は帯の外。2本前の山は確定が最後の足＝窓の外）。今の S-Rタッチ数 なら n |
| SMC_SWEEP確定 | 40本の平らな足に、20本目の谷 99.0（または山 101.0）。最後の足で安値 98.5・終値 99.6／高値 101.5・終値 100.5／安値 98.5・終値 98.8 | +1／−1／0 |
| 下半分位置 | 今のレンジ幾何の既知答えと同じ足（帯の4隅が電卓で決まる） | (100 − mid) ÷ (mid − sup_lo) |
**③オン・オフの表（使う）の違い（G-1 の試し＝写しで作り直した・道具が数えた）。**
使う 156 種 → 160 種。増えた 4 種＝S-Rタッチ確定1時間ATR・S-Rタッチ確定数・SMC_SWEEP確定・W字確定谷。減った 0 種。レンジ幾何の geo_on に増えた列＝下半分位置。
**④この工事で増える材料の名前（道具が数えた）。**
S-Rタッチ確定1時間ATR(144,0.5,14)・S-Rタッチ確定1時間ATR(144,0.5,21)・S-Rタッチ確定1時間ATR(144,0.5,7)・S-Rタッチ確定1時間ATR(144,1.0,14)・S-Rタッチ確定1時間ATR(144,1.0,21)・S-Rタッチ確定1時間ATR(144,1.0,7)・S-Rタッチ確定1時間ATR(144,1.5,14)・S-Rタッチ確定1時間ATR(144,1.5,21)・S-Rタッチ確定1時間ATR(144,1.5,7)・S-Rタッチ確定1時間ATR(288,0.5,14)・S-Rタッチ確定1時間ATR(288,0.5,21)・S-Rタッチ確定1時間ATR(288,0.5,7)・S-Rタッチ確定1時間ATR(288,1.0,14)・S-Rタッチ確定1時間ATR(288,1.0,21)・S-Rタッチ確定1時間ATR(288,1.0,7)・S-Rタッチ確定1時間ATR(288,1.5,14)・S-Rタッチ確定1時間ATR(288,1.5,21)・S-Rタッチ確定1時間ATR(288,1.5,7)・S-Rタッチ確定数(144,0.0015)・S-Rタッチ確定数(144,0.003)・S-Rタッチ確定数(144,0.006)・S-Rタッチ確定数(288,0.0015)・S-Rタッチ確定数(288,0.003)・S-Rタッチ確定数(288,0.006)・SMC_SWEEP確定・W字確定谷(24,0.003)・W字確定谷(48,0.003)・W字確定谷(96,0.003)
**⑤この工事の設定（今の資料から写し直しても変わらない＝設定の指示は無い）。**
観察の道具の設定 observe_config.json と探す範囲 search_limits.json は、この工事では変えません。
**⑥名前に出さない引数の番人で見つかったこと。**
- 番人（_insp_hidden_params）は、決まった式の値動きで k を変えて列が変わるかを見ます。W字確定谷 は、その値動きでは W の形が1回も出ず、列が変わりませんでした（写しで実測）。そこで、番人の中で W字確定谷だけ、形が出る既知答えの足（_w_case）で確かめる形にしました（k を 8 にすると2つ目の谷が確定せず、最後の足が 1 → 0 に変わる）。
**⑦2つ目の工事で写す設定（G-1 の試しの後に、資料から写し直すと変わる行・道具が数えた）。**
- search_limits.json（5 行）
```
-    "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}]
+    "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}],
+    "W字確定谷": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.003, "hi": 0.003, "dec": 3}],
+    "S-Rタッチ確定数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}],
+    "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}]
```

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、当てる道具 apply_audit_fix.py・観察の道具の自己テスト・印を作る道具の自己テスト・照らしの道具・表を作る道具（G-1）・資料の道具4本・監査に出す前のチェックを動かします。
**誰が結果を使うか。**
- 足した4種の列は、観察の道具の build_catalog が材料のカタログに入れ、engine_tuner と M2-F の段の道具が読みます。
- 下半分位置の列は、レンジ幾何を作る4か所（観察の道具・値を探すプログラム・売買を回すプログラム・関門を数える道具）が作り、条件の材料（geo）として読まれます。
- 参照表の登録（定義・独立の実装・既知答え・系統・「使う」の決定）は、観察の道具の自己テストと、オン・オフの表を作る道具（gen_indicator_switch.py）が読みます。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**今の実物（observe_diag.py・indicator_reference_diag.py・gen_indicator_switch.py・engine_tuner_gen.py・engine_tuner_exec.py・engine_tuner_fire_diag.py）・資料（research/alias_map_k3b.json）・設計書の 4-20。
**書くもの。**
- 当てる（--design）：上の6つのコードと、知識の文書 regime_detection_kb.md の件数の囲みと、新しい壊すプログラム 6本。
- G-1：オン・オフの表・型の表・出口の型の表・材料の文書・観察の説明書・組み立ての表・資料の表3つ（資料の道具4本）・修正対応表。
- 2つ目の工事（G-1 の後）：search_limits.json の、資料から写す塊（4-0 の⑦）。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 今の版を残して、教科書の版を別の材料として足す | まこさん「A」（K-3） | 今の W字・S-Rタッチ数・S-Rタッチ1時間ATR・SMC_SWEEP・帯内位置% は1文字も変えません。前から在る列の値は直す前と同じです（写しで 0本の違い） |
| 指標の名前に値を入れて、指標の数を増やさない | まこさん 2026-10-04 | 確定の本数 k は名前に出さない引数にしました（まこさん「よい」2026-10-09 の1） |
| 数字を CC が作らない | 思考の順の7（req_thinking_20261004） | k の最初の値 2 は資料の fractal の既定です。既知答えの数字は合成の足から手で計算できる形で、式を 4-0 に書きました |
| 探す値を、点の一覧で先に限定しない | 要件の作ってはいけないもの2番 | 4種の窓と許容幅は、今の版と同じ一覧から作り、探す範囲は2つ目の工事で資料から写します |
| 未来のデータを使わない | 要件定義書 §4.6.H2 | 山・谷は前後 k 本で確定してから使います。SMC_SWEEP確定は1本前までに確定した山・谷を使います。当てた後に H2 を取り直します |
| 値段の高さで値が変わらない | 要件定義書 §4.6.H6 | W字確定谷は 0 か 1、S-Rタッチは数、SMC_SWEEP確定は −1・0・+1、下半分位置は比です |
| 乱数を使わない | 恒久67番 | 乱数は使いません |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| observe_diag.py の _fractal_marks | 確定した山・谷の値段を、確定した足に置く（今の _fractal_levels の中から切り出す・計算は変えない） | 新設 |
| observe_diag.py の _w_fractal・_sr_touch_fractal・_sr_touch_fractal_atr・_smc_sweep_fractal | 確定した山・谷で作る教科書の版の計算 | 新設 |
| observe_diag.py の登録（_reg）・build_catalog・build_range_geometry | 4種をカタログに入れる・レンジ幾何の列に下半分位置 | 直す |
| observe_diag.py の _insp_hidden_params | 名前に出さない引数の番人＝W字確定谷だけ形の出る足で確かめる | 直す |
| indicator_reference_diag.py の登録（_r）・系統・業界の対応表・RANGE_GEO_REF・その既知答え | 4種の定義・独立の実装・既知答え・「使う」の決定の逐語・下半分位置の定義と既知答え | 直す |
| gen_indicator_switch.py の source_mako_geo・build・自己テスト T12 | レンジ幾何の定義表の mako の欄の列を geo_on に入れる | 新設と直す |
| engine_tuner_gen.py の _geo_of・engine_tuner_exec.py・engine_tuner_fire_diag.py の build_geo | レンジ幾何の列に下半分位置（観察の道具と同じ式） | 直す |
| regime_detection_kb.md の件数の囲み（COUNTS_START〜COUNTS_END） | gen_materials.py が書き出す「指標の種類・材料の一覧の行・部品の件数」（写しで gen_materials.bans_count_block が数えた文に置き換える） | 直す |
| .claude/breaks の壊すプログラム | 最初の上抜け・確定した山の数え方・まだ確定していない山を使わないこと・終値で戻す条件・下半分の幅・geo_on の源を壊すと、決めた文で落ちるかを見る | 新設 |
- 触る関数（当てる前と後の構文木を関数ごとに比べて道具が数えた）＝observe_diag.py：<モジュール直下>・_fractal_levels・_fractal_marks・_insp_hidden_params・_smc_sweep_fractal・_sr_touch_fractal・_sr_touch_fractal_atr・_w_fractal・build_catalog・build_range_geometry／indicator_reference_diag.py：<モジュール直下>・_smc_fr_case・_sr_fr_case・_tb_fractal_marks・_tb_smc_fr・_tb_sr_fr・_tb_sr_fr_atr1h・_tb_w_fr・_w_case2・range_geo_known_check／gen_indicator_switch.py：build・cmd_selftest・source_mako_geo／engine_tuner_gen.py：_geo_of／engine_tuner_exec.py：run_recipe／engine_tuner_fire_diag.py：build_geo

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. まこさんの承認の後、全部を当てます（apply_audit_fix.py --design --dry → --design）。当てる道具は、全件を当てる前の実物で照らしてから、番号の順に当てます。1件でも合わなければ1件も当てません。
2. 当てた直後に、当てる道具が G2 と H2 を自分で走らせます（observe_diag.py・engine_tuner_gen.py・engine_tuner_exec.py は H2 の対象です）。
3. 照合（verify_design_contract.py --diff）をかけます。照らしの道具（①②）・壊すプログラムを走らせ、全体の自己テスト（--selftest）を1回 走らせて、出力をそのまま貼ります（当てた直後の写しで、全部 通ることを確かめた）。
4. G-1：オン・オフの表を作り直し（4種が「使う」に・下半分位置が geo_on に入る）、型の表・出口の型の表（変わればまこさんに再承認していただく）・材料の文書・観察の説明書・組み立ての表を作り直します。そのあと資料の道具4本（list_on_families.py --add・make_param_table.py・extract_threshold_role_add.py --alias・build_role_threshold_table.py）を走らせ、修正対応表を作り直します。ここで照らしの①は0件、②は 4-0 の⑦の設定を写すまで食い違います（G-1 の試しで実測）。
5. 2つ目の工事：4-0 の⑦の設定を、資料から道具が写す案を出し、承認をいただいて当てます（照らしの②が0件になる）。
6. G-2：G2 → H2 を取り直し、監査に出す前のチェック（pre_audit_check.py --run）を走らせます。そのあと、工事ごとに1通ずつ実装の監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝S-Rタッチ。今の材料 S-Rタッチ数(144,0.003) は、今の終値 ± 0.3% の帯に、直前144本の足が何本 掛かったかを数えます。値段が帯の中で横ばいに動いていると、144本 全部が数えられます（滞在時間）。この工事で足す S-Rタッチ確定数(144,0.003) は、直前144本の中で確定した山（前後2本より高い高値）と谷（前後2本より低い安値）のうち、帯に入るものだけを数えます。横ばいの間は山も谷もできないので 0 で、値段が帯で跳ね返されるたびに1つずつ増えます。山・谷は、その2本 後の足で確定してから数えます。既知答えは、平らな足に 100.1 の山を2つ・101 の山を1つ・99.9 の谷を1つ置き、最後の足の帯（100 ± 0.15〜0.6）で 3 になるかを見ます。最後の足の2本前に置いた 100.1 の山は、確定が最後の足なので数えません。今の S-Rタッチ数(144,0.003) の値は1本も変わりません。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**この工事で探す範囲は変わりません。**4種の探す範囲は、2つ目の工事で資料から写します（4-0 の⑦）。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**observe_config.json と search_limits.json は、この工事では変えません**（今の資料から写し直しても同じ。4種の範囲は2つ目の工事で写す）。
コマンドの旗は増やしません。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**
1. 観察の道具の全体の自己テストが通る（足した4種の既知答えと独立の実装、下半分位置の既知答えを含む）。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest。
2. 印を作る道具の自己テストが通る（T12 を含む）。コマンド＝python3 scripts/priority_rebuild/gen_indicator_switch.py --selftest。
3. 照らしの道具が、①②とも食い違い0件。コマンド＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources。
4. 壊すプログラムが、全部 決めた文で落ちる。コマンド＝python3 .claude/tools/run_breaks.py --design。
5. G2 と H2 が取り直される。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| --design の --dry で、当たらない件が出る | 1件も当てずに止まります。まこさんに報告します |
| 4種のどれかが、確定していない山・谷を使う・最初の上抜けを取り違える | 観察の道具の自己テストが「手計算の既知答えと不一致」を出して落ちます |
| 4種の計算と独立の実装が合わない | 観察の道具の自己テストが「教科書の独立実装と不一致」を出して落ちます |
| 下半分位置を上半分の幅で割る | 観察の道具の自己テストが「レンジ幾何 既知答え不一致: 下半分位置」を出して落ちます |
| geo_on が mako の欄の列を読まない | 印を作る道具の自己テスト T12 が落ちます |
| 4種が「使う」になったのに、資料に行が無い | 照らしの道具が「①」で始まる行を出して落ちます（資料の道具4本を G-1 の中で走らせる） |
| G-1 の後、2つ目の工事を当てる前に監査に出す前のチェックを走らせる | 照らしの道具が「②」で落ちます（2つ目の工事を当ててから走らせる＝4-4 の順） |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**変えません。**カタログの1件の形・参照表の欄・設定の欄の形は前の工事のままです。レンジ幾何の定義表の1件に mako の欄が増えます（材料の定義表 REFS の mako の欄と同じ意味）。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**変えません。**

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**山・谷は、中央の足の k 本 後の足で確定します。**確定した足より前には使いません（今の _fractal_levels と同じ）。SMC_SWEEP確定は、1本前までに確定した山・谷を使います。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| 観察の道具の自己テスト（全体） | 136秒 | 写しで当てた後に走らせた実測（k3b_draft_build.py の [7]） |
| 軽い口（--selftest-catalog） | 9秒 | 写しで当てた後に走らせた実測（k3b_draft_build.py の [7]） |
| 材料の一覧 | 516 列 | 写しで数えた（k3b_draft_build.py の [3]） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**この工事の中ではありません。**全部を --design の1回で当てます。★この工事と2つ目の工事の間（G-1 の後）は、照らしの②が食い違う途中の状態です。その間に監査に出す前のチェックを走らせません（4-4 の順）。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しの道具だけが書きます。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**観察の道具の自己テストは、落ちたときだけ「手計算の既知答えと不一致」「教科書の独立実装と不一致」「レンジ幾何 既知答え不一致」で始まる行を出します。印を作る道具の自己テストは、T12 の行に pass か ng を出します。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **observe_diag.py・engine_tuner_gen.py・engine_tuner_exec.py は H2 の対象です。**当てた後に G2 → H2 を取り直します。
2. **材料のカタログに 28 列が増えます。**型の表（signal_families）の部品も増え（レンジ幾何の別枠にも下半分位置が入る）、まこさんの再承認が要ります（G-1）。
3. **成績表（material_ranking.json）には、増える列の行がありません。**作り直す（M2-D-8）まで、段の候補の順位に出ません。
4. **マイルストーンへの差し込み（作ってはいけないものとの照合）は変わりません**（写しで 0行の違い）。
5. **前からの壊すプログラムが探す文字の数は、当てる前と後で同じです。**道具が数えた相手は、下の囲みです。
```
b100_streak_tree_eval.sh・b103_geo_switch_unchecked.sh・b104_atr1h_own_tf.sh・b105_atr1h_future_hour.sh・b106_atr1h_no_clip.sh・b107_atr1h_base_not_passed.sh・b108_atr1h_base_wrong_bars.sh・b109_moving_line_not_built.sh・b110_ts_pos_in_random_draw.sh・b111_ts_pos_excludes_current.sh・b112_stage_warm_not_extended.sh・b122_obs_formula_copied.sh・b126_rank_resume_save_off.sh・b127_stage_q_rank_off.sh・b128_k1_copc_back_in_ao_loop.sh・b129_htf_bar_close_two_bars.sh・b131_industry_map_prev_pivot_gone.sh・b132_hidden_param_not_passed.sh・b133_cksp_mixed_set.sh・b134_ao_name_with_value.sh・b135_rci_mako_gone.sh・b136_insp2_bar_close_dropped.sh・b137_material_params_ignored.sh・b138_keep_name_dropped.sh・b139_range_excludes_keep.sh・b140_group_range_ignored.sh・b141_catalog_out_of_range.sh・b143_rci_range_short.sh・b145_vwap_day_no_reset.sh・b146_pivot_week_as_day.sh・b147_vp_today_from_start.sh・b55_cyc_key_time_gone.sh・b56_one_min_csv_old.sh・b60_only5_with_others.sh・b61_insp5_bars_kind.sh・b63_tm_bitget_scope.sh・b64_tm_subdir.sh・b65_tm_badtail.sh・b77_no_streak.sh・b78_law_literal.sh・b79_param_drawn.sh・b80_quantile_one_by_one.sh・b82_abs_missing.sh・b83_bool_col_extra_key.sh・b84_qtable_per_bundle.sh・b85_band_ignores_laws.sh・b87_stages_record.sh・b91_keep_range_ignored.sh・b92_stage2_no_drop_tfs.sh・b94_stage_limits_ignored.sh・b96_tf_hardcoded.sh・b98_qkey_abs_missing.sh・b99_streak_inner_band_only.sh
```

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| k3a_draft_build.py（前の工事の道具） | 写しの作り・資料の写し・照らし・設定の写し・A12 の自己テストの一覧と許しの判定（import して使う） |
| observe_diag.py の _fractal_levels・_sr_touch・_sr_touch_atr | 確定の決まり・帯の数え方の窓 [i−n, i)・1時間足の許容幅 |
| indicator_reference_diag.py の _tb_fractal・_w_case・_known_sr_touch_atr1h | 独立の実装の書き方・既知答えの合成の足 |
| 壊すプログラム b142 | 壊すプログラムの形 |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=d55edc0df754c3d9 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 600〜614行（_fractal_levels・監査 CP60 の修正43・44・46＝確定の決まりを _fractal_marks に切り出し（計算は変えない）、確定した山・谷で作る3つの計算を足す）
直す前の文字:
~~~
    k = int(k)
    if k < 1:
        raise SystemExit(f"[材料カタログ] 山と谷の確定の本数は 1 以上（渡された＝{k}）")
    if is_high:
        left = s.rolling(k).max().shift(1)         # 中央のバー j の直前 k本（j の時点で分かる）
        right = s.rolling(k).max()                 # j+1 〜 j+k（バー j+k の時点で分かる）
        hit = (s.shift(k) > left.shift(k)) & (s.shift(k) > right)
    else:
        left = s.rolling(k).min().shift(1)
        right = s.rolling(k).min()
        hit = (s.shift(k) < left.shift(k)) & (s.shift(k) < right)
    lvl = s.shift(k).where(hit)                    # 確定したバーにだけ、その山（谷）の値段が入る
    last = lvl.ffill()                             # 直近で確定した水準
    prev = last.shift(1).where(hit).ffill()        # その1つ前に確定した水準
    return last, prev

~~~
直した後の文字:
~~~
    lvl, hit = _fractal_marks(s, k, is_high)       # 確定したバーにだけ、その山（谷）の値段が入る
    last = lvl.ffill()                             # 直近で確定した水準
    prev = last.shift(1).where(hit).ffill()        # その1つ前に確定した水準
    return last, prev


def _fractal_marks(s, k: int, is_high: bool):
    """確定した山（谷）の値段を、確定したバー（中央のバー j の k本 後）にだけ置いた列と、その印（真偽）を返す。
    ★2026-10-09（工事 m2c15-shape-structure-20261009・K-3b）に _fractal_levels の中から切り出した（計算は1文字も変えていない）。
      窓の中で確定した山・谷を全部 使う教科書の版（W字確定谷・S-Rタッチ確定数・SMC_SWEEP確定）と、今の _fractal_levels が
      同じ確定の決まりを使うため。"""
    k = int(k)
    if k < 1:
        raise SystemExit(f"[材料カタログ] 山と谷の確定の本数は 1 以上（渡された＝{k}）")
    if is_high:
        left = s.rolling(k).max().shift(1)         # 中央のバー j の直前 k本（j の時点で分かる）
        right = s.rolling(k).max()                 # j+1 〜 j+k（バー j+k の時点で分かる）
        hit = (s.shift(k) > left.shift(k)) & (s.shift(k) > right)
    else:
        left = s.rolling(k).min().shift(1)
        right = s.rolling(k).min()
        hit = (s.shift(k) < left.shift(k)) & (s.shift(k) < right)
    return s.shift(k).where(hit), hit


def _w_fractal(c, h, l, n, tol, k=2):
    """W字確定谷＝ダブルボトムの教科書の版（監査 CP60 の修正43・2026-10-09・工事 m2c15-shape-structure-20261009）。
    ①2つの底＝窓 n 本（今の足まで）の中で確定した谷（_fractal_marks・前後 k 本）のうち、直近の2つ
    ②2つの底の値段の差が tol×終値 以内（今の W字 と同じ許容幅の決まり）
    ③ネック＝2つの谷の間の足の最高値
    ④完成＝2つ目の谷の後で、終値がネックを最初に上抜けた足だけ 1。それ以外は 0（今の W字 は条件が続く間ずっと1）。
    出どころ＝StockCharts の逐語「Breaking resistance from the highest point between the troughs completes the Double Bottom Reversal.」
    （監査 CP60 の表 27）。★未来を見ない＝谷はその k 本 後の足で確定してから使う。
    ★k は名前に出さない引数（最初の値 2＝資料の fractal の既定・まこさん「よい」2026-10-09 の1）。"""
    lv, hit = _fractal_marks(l, k, False)
    ca, ha = c.to_numpy(float), h.to_numpy(float)
    tv = np.flatnonzero(hit.to_numpy(bool))        # 谷が確定した足の番号
    pv = lv.to_numpy(float)[tv]                    # その谷の値段
    jv = tv - int(k)                               # 谷そのものの足の番号
    n = int(n)
    out = np.full(len(ca), np.nan)
    m = 0
    for i in range(n - 1, len(ca)):
        while m < len(tv) and tv[m] <= i:
            m += 1
        out[i] = 0.0
        if m < 2:
            continue
        j1, j2 = jv[m - 2], jv[m - 1]
        if j1 < i - n + 1 or j2 - j1 < 2 or abs(pv[m - 2] - pv[m - 1]) > tol * ca[i]:
            continue
        neck = ha[j1 + 1:j2].max()
        if ca[i] > neck and not (ca[j2 + 1:i] > neck).any():
            out[i] = 1.0
    return pd.Series(out, index=c.index)


def _sr_touch_fractal(d, n, tol, k=2):
    """S-Rタッチ確定数＝S-Rタッチの教科書の数え方（監査 CP60 の修正44・2026-10-09・工事 m2c15-shape-structure-20261009）。
    今の足の前の n 本（確定した足が [i−n, i)）の中で確定した山（高値）と谷（安値）のうち、今の終値 ± 許容幅（tol×終値）に入るものの数。
    今の S-Rタッチ数（_sr_touch）は、帯に掛かった足の本数（滞在時間）を数える＝監査 CP60 の表 48・49。
    ★今の足は窓に入れない（_sr_touch と同じ）。山・谷は前後 k 本で確定してから使う（未来を見ない）。
    ★tol は数でも並び（足ごとの割合）でもよい（_sr_touch と同じ）。k は名前に出さない引数（最初の値 2）。"""
    hv = _fractal_marks(d.high, k, True)[0].to_numpy(float)
    lv = _fractal_marks(d.low, k, False)[0].to_numpy(float)
    ca = d.close.to_numpy(float)
    ta = np.asarray(tol, dtype=float) if np.ndim(tol) else None   # 並びなら配列・数なら None
    n = int(n)
    out = np.full(len(ca), np.nan)
    for i in range(n, len(ca)):
        t = tol if ta is None else ta[i]
        if t != t:                                   # NaN（ATR がまだ出ていない区間）は空のまま
            continue
        band = ca[i] * t
        out[i] = float(np.sum(np.abs(hv[i - n:i] - ca[i]) <= band) + np.sum(np.abs(lv[i - n:i] - ca[i]) <= band))
    return pd.Series(out, index=d.index)


def _sr_touch_fractal_atr(d, n, m, a, k=2):
    """S-Rタッチ確定1時間ATR＝S-Rタッチ確定数 の許容幅を「1時間足の ATR% × 倍率」で決め、0.15%〜0.6% に収めた版（K-3b）。
    許容幅の作りは _sr_touch_atr と同じ（_atr_pct_1h_on・_SR_ATR_TOL_LO〜_SR_ATR_TOL_HI）。"""
    atr_pct = pd.Series(_atr_pct_1h_on(d, a), index=d.index)
    tol = (m * atr_pct).clip(lower=_SR_ATR_TOL_LO, upper=_SR_ATR_TOL_HI)
    return _sr_touch_fractal(d, n, tol.to_numpy(float), k)


def _smc_sweep_fractal(d, k=2):
    """SMC_SWEEP確定＝流動性の刈り取りの教科書の版（監査 CP60 の修正46・2026-10-09・工事 m2c15-shape-structure-20261009）。
    1本前までに確定した直近の谷（前後 k 本）を安値で割り、終値でその上に戻した足＝+1。
    1本前までに確定した直近の山を高値で抜き、終値でその下に戻した足＝−1。どちらでもない足＝0。
    出どころ＝LuxAlgo の逐語「The classic anatomy is a wick through a prior swing high or low…followed by a close back inside
    the old range.」（監査 CP60 の表 61）。ライブラリの版（直前15本の高安・陽線陰線・ヒゲが実体の1.5倍）の条件は使わない
    （まこさん「よい」2026-10-09 の2）。★値の向き（+1＝下側の刈り取り）はライブラリの版と同じ。山・谷が1つも確定していない足は欠損。"""
    hi = _fractal_levels(d.high, k, True)[0].shift(1)
    lo = _fractal_levels(d.low, k, False)[0].shift(1)
    bull = ((d.low < lo) & (d.close > lo)).astype(float)
    bear = ((d.high > hi) & (d.close < hi)).astype(float)
    return (bull - bear).where(hi.notna() | lo.notna())

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:600「k = int(k)」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1028〜1029行（<モジュール直下>・4種を、今の版を残して別の材料として登録する（k は名前に出さない引数・まこさん「よい」2026-10-09））
直す前の文字:
~~~
_reg("S-Rタッチ1時間ATR", "S-Rタッチ1時間ATR({},{},{})", False,
     lambda d, n, k, a: _sr_touch_atr(d, n, k, a))

~~~
直した後の文字:
~~~
_reg("S-Rタッチ1時間ATR", "S-Rタッチ1時間ATR({},{},{})", False,
     lambda d, n, k, a: _sr_touch_atr(d, n, k, a))
# ── 2026-10-09（工事 m2c15-shape-structure-20261009・K-3b・監査 CP60 の修正43・44・46）＝確定した山・谷で作る教科書の版を、
#   今の版を残して別の材料として足す。どちらが良いかは M2-F-10f で比べる（この工事は材料を足すだけ）。
#   ★確定の本数 k は名前に出さない引数（最初の値 2＝資料の fractal の既定・まこさん「よい」2026-10-09 の1）。向きの印は今の版と同じ。
_reg("W字確定谷", "W字確定谷({},{})", True, lambda d, n, t, k=2: _w_fractal(d.close, d.high, d.low, n, t, k))
_reg("S-Rタッチ確定数", "S-Rタッチ確定数({},{})", False, lambda d, n, t, k=2: _sr_touch_fractal(d, n, t, k))
_reg("S-Rタッチ確定1時間ATR", "S-Rタッチ確定1時間ATR({},{},{})", False,
     lambda d, n, m, a, k=2: _sr_touch_fractal_atr(d, n, m, a, k))
_reg("SMC_SWEEP確定", "SMC_SWEEP確定", False, lambda d, k=2: _smc_sweep_fractal(d, k))

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1028「_reg("S-Rタッチ1時間ATR", "S-Rタッチ1時間ATR({},{},{})", False,」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1492〜1493行（build_catalog・W字確定谷をカタログに入れる（今の W字 と同じ窓と許容幅の一覧で作る））
直す前の文字:
~~~
        for t in cfg["w_tol"]:
            addf("W字", n, t)

~~~
直した後の文字:
~~~
        for t in cfg["w_tol"]:
            addf("W字", n, t)
            addf("W字確定谷", n, t)           # 監査 CP60 の修正43（K-3b・2026-10-09）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1492「for t in cfg["w_tol"]:」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1545行（build_catalog・S-Rタッチ確定数をカタログに入れる（今の S-Rタッチ数 と同じ窓と許容幅の一覧で作る））
直す前の文字:
~~~
            addf("S-Rタッチ数", n, t)

~~~
直した後の文字:
~~~
            addf("S-Rタッチ数", n, t)
            addf("S-Rタッチ確定数", n, t)     # 監査 CP60 の修正44（K-3b・2026-10-09）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1545「addf("S-Rタッチ数", n, t)」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1557行（build_catalog・S-Rタッチ確定1時間ATR をカタログに入れる（今の S-Rタッチ1時間ATR と同じ一覧で作る））
直す前の文字:
~~~
                addf("S-Rタッチ1時間ATR", n, k, a)

~~~
直した後の文字:
~~~
                addf("S-Rタッチ1時間ATR", n, k, a)
                addf("S-Rタッチ確定1時間ATR", n, k, a)   # 監査 CP60 の修正44（K-3b・2026-10-09）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1557「addf("S-Rタッチ1時間ATR", n, k, a)」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1598〜1599行（build_catalog・SMC_SWEEP確定をカタログに入れる（名前に出る軸は無い））
直す前の文字:
~~~
                 "SQZPRO_ON_WIDE", "SQZPRO_ON_NARROW", "STC", "STCstoch"):
        addf(_fam)

~~~
直した後の文字:
~~~
                 "SQZPRO_ON_WIDE", "SQZPRO_ON_NARROW", "STC", "STCstoch"):
        addf(_fam)
    addf("SMC_SWEEP確定")                     # 監査 CP60 の修正46（K-3b・2026-10-09）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1598「"SQZPRO_ON_WIDE", "SQZPRO_ON_NARROW", "STC", "STCstoch"):」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 2031〜2033行（build_range_geometry・監査 CP60 の修正65＝レンジ幾何の列に下半分位置を足す（帯内位置% は残す））
直す前の文字:
~~~
        wpct = np.where(np.isfinite(res_hi) & np.isfinite(sup_lo), (res_hi - sup_lo) / c * 100.0, np.nan)
    return pd.DataFrame({"res_hi": res_hi, "res_lo": res_lo, "sup_hi": sup_hi, "sup_lo": sup_lo,
                         "mid": mid, "W%": wpct, "帯内位置%": pos}, index=bars.index)

~~~
直した後の文字:
~~~
        wpct = np.where(np.isfinite(res_hi) & np.isfinite(sup_lo), (res_hi - sup_lo) / c * 100.0, np.nan)
        # ★2026-10-09（工事 m2c15-shape-structure-20261009・監査 CP60 の修正65）＝下半分の位置（下半分の幅＝mid − sup_lo で割る）。
        #   帯内位置% は下半分も上半分の幅で割る（今の版は残す）。定義表＝indicator_reference_diag.RANGE_GEO_REF の 下半分位置
        dn = mid - sup_lo
        low = np.where(np.isfinite(dn) & (dn > 0), (c - mid) / dn, np.nan)
    return pd.DataFrame({"res_hi": res_hi, "res_lo": res_lo, "sup_hi": sup_hi, "sup_lo": sup_lo,
                         "mid": mid, "W%": wpct, "帯内位置%": pos, "下半分位置": low}, index=bars.index)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:2031「wpct = np.where(np.isfinite(res_hi) & np.isfinite(sup_lo), (res_hi - sup_lo) / c * 100.0, np.nan)」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7061〜7062行（_insp_hidden_params・名前に出さない引数の番人＝W字確定谷だけ、形が出る既知答えの合成の足で確かめる（決まった式の値動きでは形が出ない））
直す前の文字:
~~~
    ng, seen = [], 0
    for fam, (tpl, _dr, fn) in MATERIAL_FAMILIES.items():

~~~
直した後の文字:
~~~
    # ★2026-10-09（工事 m2c15-shape-structure-20261009）＝形の材料（W字確定谷）は、上の決まった式の値動きでは形が1回も出ず、
    #   確定の本数 k を変えても列が変わらない（写しで実測）。その種類だけ、形が出る既知答えの合成の足（参照表の _w_case）で確かめる。
    _cases = {"W字確定谷": lambda: iref._w_case(24, 100.2)}
    ng, seen = [], 0
    for fam, (tpl, _dr, fn) in MATERIAL_FAMILIES.items():

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7061「ng, seen = [], 0」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7076〜7077行（_insp_hidden_params・同上＝その種類の足で基準の列を作る）
直す前の文字:
~~~
        seen += 1
        base = _h(fn(d, *P))

~~~
直した後の文字:
~~~
        seen += 1
        dd = _cases[fam]() if fam in _cases else d
        base = _h(fn(dd, *P))

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7076「seen += 1」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7087行（_insp_hidden_params・同上＝その種類の足で、別の値の列を作る）
直す前の文字:
~~~
                    if _h(fn(d, *P, **{k: alt})) != base:

~~~
直した後の文字:
~~~
                    if _h(fn(dd, *P, **{k: alt})) != base:

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7087「if _h(fn(d, *P, **{k: alt})) != base:」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 946行（<モジュール直下>・4種と下半分位置の「使う」の決定（まこさんの逐語のファイル）を、mako の欄から1か所で引けるようにする）
直す前の文字:
~~~
MAKO_K7 = '2026-10-07 まこさん決定「OK」（K-7 の1番＝前期間pivot の3種に前の週の版を別の材料として足す）＝逐語のファイル ok_k7_pivot_thermo_20261007（m2c15-memo-sort-20261007）'

~~~
直した後の文字:
~~~
MAKO_K7 = '2026-10-07 まこさん決定「OK」（K-7 の1番＝前期間pivot の3種に前の週の版を別の材料として足す）＝逐語のファイル ok_k7_pivot_thermo_20261007（m2c15-memo-sort-20261007）'
# ★2026-10-09（工事 m2c15-shape-structure-20261009）＝K-3b の4種と下半分位置の「使う」の決定の逐語（mako の欄に書く）。
MAKO_K3B = '2026-10-09 まこさん「よい」（K-3b の作りの3点＝確定した山・谷の本数 k は名前に出さない引数・SMC_SWEEP の教科書の版はライブラリの 15・1.5 を使わない・下半分位置を使う）＝逐語のファイル ok_k3b_design_20261009（m2c15-k3b-decisions-20261009）。K-3 を3つの工事に分けた まこさん決定「A」＝ok_k3_split_20261007'

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:946「MAKO_K7 = '2026-10-07 まこさん決定「OK」（K-7 の1番＝前期間pivot の3種に前の週の版を別の材料として足す）＝逐語のファイル ok_k7_pivot_thermo_20261007（m2c15-memo-so」
状態: 確定

#### 実装 12
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1481〜1491行（<モジュール直下>・監査 CP60 の修正43・44・46＝4種を参照表に登録し、独立の実装と手計算の既知答えを付ける）
直す前の文字:
~~~
_r(r"S-Rタッチ数\((\d+),([\d.]+)\)", "S-Rタッチ数",
   "いまの価格の許容幅つき帯に、過去 n 本の高安が何回触れたか", "サポート・レジスタンスの強度の近似",
   "状態量＝多いほど節が固い", "none", tb=_tb_sr_touch,
   known=lambda p: [(_mk(np.full(int(p[0]) + 12, 100.0), o=np.full(int(p[0]) + 12, 100.0),
                         h=np.full(int(p[0]) + 12, 100.0), l=np.full(int(p[0]) + 12, 100.0)),
                     [(-1, float(int(p[0])), 1e-9)]),
                    (_mk(np.r_[np.full(int(p[0]) + 5, 90.0), 100.0, 100.0, 100.0, 90.0, 90.0, 100.0],
                         o=np.r_[np.full(int(p[0]) + 5, 90.0), 100.0, 100.0, 100.0, 90.0, 90.0, 100.0],
                         h=np.r_[np.full(int(p[0]) + 5, 90.0), 100.0, 100.0, 100.0, 90.0, 90.0, 100.0],
                         l=np.r_[np.full(int(p[0]) + 5, 90.0), 100.0, 100.0, 100.0, 90.0, 90.0, 100.0]),
                     [(-1, 3.0, 1e-9)])])

~~~
直した後の文字:
~~~
_r(r"S-Rタッチ数\((\d+),([\d.]+)\)", "S-Rタッチ数",
   "いまの価格の許容幅つき帯に、過去 n 本の高安が何回触れたか", "サポート・レジスタンスの強度の近似",
   "状態量＝多いほど節が固い", "none", tb=_tb_sr_touch,
   known=lambda p: [(_mk(np.full(int(p[0]) + 12, 100.0), o=np.full(int(p[0]) + 12, 100.0),
                         h=np.full(int(p[0]) + 12, 100.0), l=np.full(int(p[0]) + 12, 100.0)),
                     [(-1, float(int(p[0])), 1e-9)]),
                    (_mk(np.r_[np.full(int(p[0]) + 5, 90.0), 100.0, 100.0, 100.0, 90.0, 90.0, 100.0],
                         o=np.r_[np.full(int(p[0]) + 5, 90.0), 100.0, 100.0, 100.0, 90.0, 90.0, 100.0],
                         h=np.r_[np.full(int(p[0]) + 5, 90.0), 100.0, 100.0, 100.0, 90.0, 90.0, 100.0],
                         l=np.r_[np.full(int(p[0]) + 5, 90.0), 100.0, 100.0, 100.0, 90.0, 90.0, 100.0]),
                     [(-1, 3.0, 1e-9)])])


# ★2026-10-09（工事 m2c15-shape-structure-20261009・K-3b・監査 CP60 の修正43・44・46）＝確定した山・谷で作る教科書の版。
#   独立の実装は、確定した山・谷を素直な繰り返し（_tb_fractal と同じ決まり）で作る＝観察の道具のまとめ計算とは別の書き方。
def _tb_fractal_marks(d, k, is_high):
    """確定した山（谷）の値段を、確定した足（中央の足 j の k 本 後）にだけ置いた並び。"""
    k = int(k)
    s = (d.high if is_high else d.low).to_numpy(float)
    out = np.full(len(s), np.nan)
    for t in range(len(s)):
        j = t - k
        if j - k >= 0:
            mid, lft, rgt = s[j], s[j - k:j], s[j + 1:j + k + 1]
            if (mid > lft.max() and mid > rgt.max()) if is_high else (mid < lft.min() and mid < rgt.min()):
                out[t] = mid
    return out


def _tb_w_fr(d, p, k=2):
    n, tol = int(p[0]), float(p[1])
    o, h, l, c, v = _arr(d)
    lv = _tb_fractal_marks(d, k, False)
    out = np.full(len(c), np.nan)
    tl = []
    for i in range(len(c)):
        if lv[i] == lv[i]:
            tl.append(i)
        if i < n - 1:
            continue
        out[i] = 0.0
        if len(tl) < 2:
            continue
        t1, t2 = tl[-2], tl[-1]
        j1, j2 = t1 - k, t2 - k
        if j1 < i - n + 1 or j2 - j1 < 2 or abs(lv[t1] - lv[t2]) > tol * c[i]:
            continue
        neck = max(h[j1 + 1:j2])
        if c[i] > neck and all(c[x] <= neck for x in range(j2 + 1, i)):
            out[i] = 1.0
    return _S(out, d)


def _w_case2(n):
    """W字確定谷 の「最初に上抜けた足だけ 1」の既知答え用。_w_case(n, 100.2) と同じ並びで、最後の2本の終値を 109 にする
    ＝1本前が最初の上抜け（1）・最後の足は2回目（0）。今の W字 なら最後の足も 1（条件が続く間ずっと1）。"""
    half, q = n // 2, (n // 2) // 2
    m = n + 6
    c = np.full(m, 106.0)
    h = np.full(m, 106.0)
    l = np.full(m, 105.0)
    base = m - n
    l[base + 2] = 100.0
    h[base + half] = 108.0
    l[base + half + q + 1] = 100.2
    c[-2:] = 109.0
    return _mk(c=c, o=c.copy(), h=np.maximum(h, c), l=np.minimum(l, c))


def _tb_sr_fr(d, p, k=2):
    n, tol = int(p[0]), float(p[1])
    o, h, l, c, v = _arr(d)
    hv, lv = _tb_fractal_marks(d, k, True), _tb_fractal_marks(d, k, False)
    out = np.full(len(c), np.nan)
    for i in range(n, len(c)):
        band = c[i] * tol
        out[i] = float(np.sum(np.abs(hv[i - n:i] - c[i]) <= band) + np.sum(np.abs(lv[i - n:i] - c[i]) <= band))
    return _S(out, d)


def _tb_sr_fr_atr1h(d, p, k=2):
    """S-Rタッチ確定1時間ATR の独立の実装。許容幅（1時間足の ATR%・0.15%〜0.6%）は _tb_sr_touch_atr1h の①〜⑤と同じ書き方、
    数え方は _tb_sr_fr（確定した山・谷）。"""
    n, km, an = int(p[0]), float(p[1]), int(p[2])
    o, h, l, c, v = _arr(d)
    starts, groups = [], []
    for i, t in enumerate(d.index.floor("h")):
        if not starts or starts[-1] != t:
            starts.append(t)
            groups.append([i])
        else:
            groups[-1].append(i)
    hh = np.array([h[g].max() for g in groups])
    hl = np.array([l[g].min() for g in groups])
    hc = np.array([c[g[-1]] for g in groups])
    atr = np.full(len(groups), np.nan)
    for j in range(len(groups)):
        if j == 0:
            atr[j] = hh[j] - hl[j]
        else:
            tr = max(hh[j] - hl[j], abs(hh[j] - hc[j - 1]), abs(hl[j] - hc[j - 1]))
            atr[j] = (atr[j - 1] * (an - 1) + tr) / an
    pct = atr / hc
    closes = (pd.DatetimeIndex(starts) + pd.Timedelta("1h")).values
    pos = np.searchsorted(closes, (d.index + pd.Timedelta("5min")).values, side="right") - 1
    hv, lv = _tb_fractal_marks(d, k, True), _tb_fractal_marks(d, k, False)
    out = np.full(len(c), np.nan)
    for i in range(n, len(c)):
        if pos[i] < 0:
            continue
        band = c[i] * min(max(km * pct[pos[i]], 0.0015), 0.006)
        out[i] = float(np.sum(np.abs(hv[i - n:i] - c[i]) <= band) + np.sum(np.abs(lv[i - n:i] - c[i]) <= band))
    return _S(out, d)


def _sr_fr_case(n):
    """S-Rタッチ確定数・S-Rタッチ確定1時間ATR の既知答え用（2026-10-09・K-3b）。n＋12 本の平らな足（始値＝高値＝安値＝終値＝100）に、
    確定する山を3つ（100.1・101・100.1）と谷を1つ（99.9）置く。最後の足の終値 100 の帯（許容幅 0.15%〜0.6%＝±0.15〜±0.6）に入るのは
    100.1 の山2つと 99.9 の谷1つ＝3。101 の山は帯の外。最後の足の2本前にも 100.1 の山を置くが、確定は最後の足（窓 [i−n, i) の外）なので数えない。
    今の S-Rタッチ数 なら、窓の n 本が全部 100 に触れる＝n（数え方の違いを見分ける）。"""
    m = n + 12
    c = np.full(m, 100.0)
    h = c.copy()
    l = c.copy()
    i = m - 1
    h[i - 20] = 100.1
    h[i - 15] = 101.0
    h[i - 10] = 100.1
    l[i - 5] = 99.9
    h[i - 2] = 100.1
    return _mk(c=c, o=c.copy(), h=h, l=l)


def _tb_smc_fr(d, p, k=2):
    o, h, l, c, v = _arr(d)
    hl_, _p1 = _tb_fractal(d, k, True)
    ll_, _p2 = _tb_fractal(d, k, False)
    out = np.full(len(c), np.nan)
    for i in range(1, len(c)):
        hi, lo = hl_[i - 1], ll_[i - 1]
        if hi != hi and lo != lo:
            continue
        bull = lo == lo and l[i] < lo and c[i] > lo
        bear = hi == hi and h[i] > hi and c[i] < hi
        out[i] = float(bull) - float(bear)
    return _S(out, d)


def _smc_fr_case(kind):
    """SMC_SWEEP確定 の既知答え用（2026-10-09・K-3b）。40本の平らな足（始値＝終値＝100・高値 100.2・安値 99.8）の20本目に、
    谷（安値 99.0）か山（高値 101.0）を置く（前後2本より低い（高い）＝22本目で確定）。最後の足で、
    kind="bull"＝安値 98.5・終値 99.6（谷を割って戻した＝+1）／kind="bear"＝高値 101.5・終値 100.5（山を抜いて戻した＝−1）／
    kind="stay"＝安値 98.5・終値 98.8（割ったが戻していない＝0）。陽線・陰線とヒゲの長さは条件に入れない（ライブラリの版との違い）。"""
    m = 40
    c = np.full(m, 100.0)
    o = c.copy()
    h = np.full(m, 100.2)
    l = np.full(m, 99.8)
    if kind == "bear":
        h[20] = 101.0
        h[-1] = 101.5
        c[-1] = 100.5
    else:
        l[20] = 99.0
        l[-1] = 98.5
        c[-1] = 99.6 if kind == "bull" else 98.8
    return _mk(c=c, o=o, h=h, l=l)


_r(r"W字確定谷\((\d+),([\d.]+)\)", "W字確定谷",
   "ダブルボトムの教科書の版。窓 n 本の中で確定した直近の2つの谷（前後 k 本）の値段の差が tol×終値 以内で、"
   "2つ目の谷の後に終値がネック（2つの谷の間の最高値）を最初に上抜けた足だけ 1・それ以外 0",
   "監査 CP60 の修正43＝StockCharts の逐語「Breaking resistance from the highest point between the troughs completes the Double Bottom Reversal.」。"
   "確定の本数 k は名前に出さない引数（最初の値 2＝資料の fractal の既定）。今の W字（中央区間の最高値の近似・条件が続く間ずっと1）は残す",
   "反転サイン＝1 は買い転換（ダブルボトム完成）の示唆", "reversal", tb=_tb_w_fr,
   known=lambda p: [(_w_case(int(p[0]), 100.2), [(-1, 1.0, 1e-9)]), (_w_case(int(p[0]), 92.0), [(-1, 0.0, 1e-9)]),
                    (_w_case2(int(p[0])), [(-2, 1.0, 1e-9), (-1, 0.0, 1e-9)])],
   mako=MAKO_K3B)
_r(r"S-Rタッチ確定数\((\d+),([\d.]+)\)", "S-Rタッチ確定数",
   "今の足の前の n 本の中で確定した山（高値）と谷（安値）のうち、今の終値 ± 許容幅（tol×終値）に入るものの数",
   "監査 CP60 の修正44＝教科書の数え方（chartinglens「You need to see price react at approximately the same price point at least twice」）。"
   "山・谷は前後 k 本で確定してから数える（k は名前に出さない引数・最初の値 2）。今の S-Rタッチ数（帯に掛かった足の本数＝滞在時間）は残す",
   "状態量＝多いほど節が固い", "none", tb=_tb_sr_fr,
   known=lambda p: [(_sr_fr_case(int(p[0])), [(-1, 3.0, 1e-9)])], mako=MAKO_K3B)
_r(r"S-Rタッチ確定1時間ATR\((\d+),([\d.]+),(\d+)\)", "S-Rタッチ確定1時間ATR",
   "S-Rタッチ確定数 の許容幅を「倍率 × 1時間足の ATR%（ATR ÷ その1時間足の終値）」で決め、0.15%〜0.6% に収めたもの",
   "監査 CP60 の修正44 の数え方（確定した山・谷）＋ S-Rタッチ1時間ATR と同じ許容幅（出どころの逐語『tol=clamp(K×ATR%_1h,0.15%,0.6%)』）。"
   "1時間足の値は、その1時間足が閉じた時刻から使う",
   "状態量＝多いほど節が固い", "none", tb=_tb_sr_fr_atr1h,
   known=lambda p: [(_sr_fr_case(int(p[0])), [(-1, 3.0, 1e-9)])], mako=MAKO_K3B)
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
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1481「_r(r"S-Rタッチ数\((\d+),([\d.]+)\)", "S-Rタッチ数",」
状態: 確定

#### 実装 13
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4721行（<モジュール直下>・4種の系統（構造・位置）を書く）
直す前の文字:
~~~
    "S-Rタッチ1時間ATR": dict(k="構造・位置", note="S-Rタッチ数と同じ数え方で、許容幅を1時間足の ATR% に連動させたもの"),

~~~
直した後の文字:
~~~
    "S-Rタッチ1時間ATR": dict(k="構造・位置", note="S-Rタッチ数と同じ数え方で、許容幅を1時間足の ATR% に連動させたもの"),
    # ★2026-10-09（工事 m2c15-shape-structure-20261009）＝確定した山・谷で作る教科書の版（監査 CP60 の修正43・44・46）
    "W字確定谷": dict(k="構造・位置", note="W字と同じ（ダブルボトム＝構造パターン）"),
    "S-Rタッチ確定数": dict(k="構造・位置"), "S-Rタッチ確定1時間ATR": dict(k="構造・位置"),
    "SMC_SWEEP確定": dict(k="構造・位置", note="SMC_SWEEP と同じ（確定した山・谷を抜いて戻した足＝水準に関わる判定）"),

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:4721「"S-Rタッチ1時間ATR": dict(k="構造・位置", note="S-Rタッチ数と同じ数え方で、許容幅を1時間足の ATR% に連動させたもの"),」
状態: 確定

#### 実装 14
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 5043行（<モジュール直下>・4種の業界のライブラリとの対応を書く（観察の道具の検査10 が全部の種類に求める））
直す前の文字:
~~~
    "S-Rタッチ1時間ATR": ((), "S-Rタッチ数の許容幅を1時間足の ATR% に連動させたもの。ライブラリに相当する関数が無い"),

~~~
直した後の文字:
~~~
    "S-Rタッチ1時間ATR": ((), "S-Rタッチ数の許容幅を1時間足の ATR% に連動させたもの。ライブラリに相当する関数が無い"),
    # ★2026-10-09（工事 m2c15-shape-structure-20261009）＝確定した山・谷で作る教科書の版
    "W字確定谷": ((), "ダブルボトムの教科書の版（確定した谷・ネック・最初の上抜け）。ライブラリに相当する関数が無い"),
    "S-Rタッチ確定数": ((), "確定した山・谷のうち今の値段の帯に入る数。ライブラリに相当する関数が無い"),
    "S-Rタッチ確定1時間ATR": ((), "S-Rタッチ確定数の許容幅を1時間足の ATR% に連動させたもの。ライブラリに相当する関数が無い"),
    "SMC_SWEEP確定": ((), "pandas-ta の smc_sweep は直前 n 本の高安とヒゲの倍率で作る別の版。確定した山・谷で作る教科書の版の関数は"
                          "ライブラリに無い（定義表の既知答えで確かめる）"),

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:5043「"S-Rタッチ1時間ATR": ((), "S-Rタッチ数の許容幅を1時間足の ATR% に連動させたもの。ライブラリに相当する関数が無い"),」
状態: 確定

#### 実装 15
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4431〜4432行（<モジュール直下>・監査 CP60 の修正65＝レンジ幾何の定義表に下半分位置を足し、まこさんの決定を mako の欄に書く）
直す前の文字:
~~~
                  houkou="順張り値＝1 に近いほど上端（戻り売りの場所）"),
}

~~~
直した後の文字:
~~~
                  houkou="順張り値＝1 に近いほど上端（戻り売りの場所）"),
    # ★2026-10-09（工事 m2c15-shape-structure-20261009・監査 CP60 の修正65 の直した後の文字＋まこさんの決定の欄）
    "下半分位置": dict(kind="ratio", teigi="下半分の帯内位置＝(close − mid) / (mid − sup_lo)。mid=0・sup_lo=−1",
                   ryugi="帯内位置% の下半分の対（%b と同じく、その半分の幅で割る・監査 CP60）。分母≤0 は欠損",
                   houkou="順張り値＝−1 に近いほど下端（押し目買いの場所）", mako=MAKO_K3B),
}

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:4431「houkou="順張り値＝1 に近いほど上端（戻り売りの場所）"),」
状態: 確定

#### 実装 16
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4467行（range_geo_known_check・レンジ幾何の既知答えに下半分位置の電卓式を足す）
直す前の文字:
~~~
    exp["帯内位置%"] = (100.0 - exp["mid"]) / (exp["res_hi"] - exp["mid"])

~~~
直した後の文字:
~~~
    exp["帯内位置%"] = (100.0 - exp["mid"]) / (exp["res_hi"] - exp["mid"])
    exp["下半分位置"] = (100.0 - exp["mid"]) / (exp["mid"] - exp["sup_lo"])     # 2026-10-09（K-3b・監査 CP60 の修正65）

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:4467「exp["帯内位置%"] = (100.0 - exp["mid"]) / (exp["res_hi"] - exp["mid"])」
状態: 確定

#### 実装 17
対象のファイル: scripts/priority_rebuild/gen_indicator_switch.py
直す箇所: 288〜289行（build・まこさん「よい」の3＝レンジ幾何の定義表の mako の欄の列を、源4 として読む関数を足す）
直す前の文字:
~~~
def build() -> dict:
    """3つの源から印を組み立てる。CC の手書きの一覧はゼロ。"""

~~~
直した後の文字:
~~~
def source_mako_geo() -> set[str]:
    """源4 のレンジ幾何＝`indicator_reference_diag.RANGE_GEO_REF` のうち、mako の欄（まこさんの決定の逐語）が書かれた列。

    ★2026-10-09（工事 m2c15-shape-structure-20261009・まこさん「よい」の3＝ok_k3b_design_20261009）に足した。
      直す前の geo_on は法則（law_geo）と恒等レシピ（source_identity）の2つだけから作り、まこさんが個別に決めた列を入れる道が無かった
      （mako の欄は材料の定義表 REFS にしか効かない＝source_mako）。下半分位置（監査 CP60 の修正65）を「使う」にするため。
    ★手書きの一覧は作らない＝定義表の欄を機械で読む。"""
    return {g for g, r in iref.RANGE_GEO_REF.items() if r.get("mako")}


def build() -> dict:
    """3つの源から印を組み立てる。CC の手書きの一覧はゼロ。"""

~~~
根拠の抜き書き: scripts/priority_rebuild/gen_indicator_switch.py:288「def build() -> dict:」
状態: 確定

#### 実装 18
対象のファイル: scripts/priority_rebuild/gen_indicator_switch.py
直す箇所: 293行（build・印を組み立てるときに、源4 のレンジ幾何を読む）
直す前の文字:
~~~
    mako_f, mako_demand = source_mako()          # 源4（2026-09-05・案A）

~~~
直した後の文字:
~~~
    mako_f, mako_demand = source_mako()          # 源4（2026-09-05・案A）
    mako_g = source_mako_geo()                   # 源4 のレンジ幾何（2026-10-09・K-3b）

~~~
根拠の抜き書き: scripts/priority_rebuild/gen_indicator_switch.py:293「mako_f, mako_demand = source_mako()          # 源4（2026-09-05・案A）」
状態: 確定

#### 実装 19
対象のファイル: scripts/priority_rebuild/gen_indicator_switch.py
直す箇所: 309行（build・印の源の説明に③（レンジ幾何の mako の欄）を書く）
直す前の文字:
~~~
                "②材料の定義表 REFS の mako の欄が書かれているもの（いまは MMI）。"

~~~
直した後の文字:
~~~
                "②材料の定義表 REFS の mako の欄が書かれているもの（いまは MMI）。"
                "③レンジ幾何の定義表 RANGE_GEO_REF の mako の欄が書かれている列（2026-10-09・K-3b）。"

~~~
根拠の抜き書き: scripts/priority_rebuild/gen_indicator_switch.py:309「"②材料の定義表 REFS の mako の欄が書かれているもの（いまは MMI）。"」
状態: 確定

#### 実装 20
対象のファイル: scripts/priority_rebuild/gen_indicator_switch.py
直す箇所: 329行（build・geo_on に源4 のレンジ幾何を入れる）
直す前の文字:
~~~
        "geo_on": sorted(law_g | id_g),

~~~
直した後の文字:
~~~
        # ★2026-10-09（工事 m2c15-shape-structure-20261009・まこさん「よい」の3）＝まこさんが個別に決めたレンジ幾何の列（RANGE_GEO_REF の mako の欄）も使う
        "geo_on": sorted(law_g | id_g | mako_g),

~~~
根拠の抜き書き: scripts/priority_rebuild/gen_indicator_switch.py:329「"geo_on": sorted(law_g | id_g),」
状態: 確定

#### 実装 21
対象のファイル: scripts/priority_rebuild/gen_indicator_switch.py
直す箇所: 335行（build・印の sources の mako に源4 のレンジ幾何を入れる）
直す前の文字:
~~~
                    "mako": sorted(mako_f | mako_demand)},

~~~
直した後の文字:
~~~
                    "mako": sorted(mako_f | mako_demand | mako_g)},

~~~
根拠の抜き書き: scripts/priority_rebuild/gen_indicator_switch.py:335「"mako": sorted(mako_f | mako_demand)},」
状態: 確定

#### 実装 22
対象のファイル: scripts/priority_rebuild/gen_indicator_switch.py
直す箇所: 479行（cmd_selftest・自己テスト T12＝mako の欄が在る列は必ず geo_on に入る）
直す前の文字:
~~~
    names = {"T1": "恒等レシピの材料は必ず使う", "T2": "法則の名指しは必ず使う",

~~~
直した後の文字:
~~~
    # T12 まこさんが個別に決めたレンジ幾何の列（RANGE_GEO_REF の mako の欄）は、必ず geo_on に入る
    #   （2026-10-09・工事 m2c15-shape-structure-20261009・まこさん「よい」の3）
    bad12 = sorted(g for g in source_mako_geo() if g not in d["geo_on"])
    if bad12:
        ng.append("T12")
        print(f"      T12 の中身＝mako の欄が在るのに geo_on に無い列: {bad12}")

    names = {"T1": "恒等レシピの材料は必ず使う", "T2": "法則の名指しは必ず使う",

~~~
根拠の抜き書き: scripts/priority_rebuild/gen_indicator_switch.py:479「names = {"T1": "恒等レシピの材料は必ず使う", "T2": "法則の名指しは必ず使う",」
状態: 確定

#### 実装 23
対象のファイル: scripts/priority_rebuild/gen_indicator_switch.py
直す箇所: 485行（cmd_selftest・自己テストの名前の一覧に T12 を足す）
直す前の文字:
~~~
                    "（legacy_col・state）が、実装の分岐6つと一致する"}

~~~
直した後の文字:
~~~
                    "（legacy_col・state）が、実装の分岐6つと一致する",
             "T12": "まこさんが個別に決めたレンジ幾何の列は必ず使う"}

~~~
根拠の抜き書き: scripts/priority_rebuild/gen_indicator_switch.py:485「"（legacy_col・state）が、実装の分岐6つと一致する"}」
状態: 確定

#### 実装 24
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 3849〜3851行（_geo_of・値を探すプログラムのレンジ幾何の列（_geo_of）に下半分位置を足す（観察の道具と同じ式））
直す前の文字:
~~~
        geo["W%"] = np.where(np.isfinite(geo["res_hi"]) & np.isfinite(geo["sup_lo"]),
                             (geo["res_hi"] - geo["sup_lo"]) / c * 100.0, np.nan)
    return geo

~~~
直した後の文字:
~~~
        geo["W%"] = np.where(np.isfinite(geo["res_hi"]) & np.isfinite(geo["sup_lo"]),
                             (geo["res_hi"] - geo["sup_lo"]) / c * 100.0, np.nan)
        # ★2026-10-09（工事 m2c15-shape-structure-20261009・監査 CP60 の修正65）＝下半分の位置（観察の道具 build_range_geometry と同じ式）
        dn = geo["mid"] - geo["sup_lo"]
        geo["下半分位置"] = np.where(np.isfinite(dn) & (dn > 0), (c - geo["mid"]) / dn, np.nan)
    return geo

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:3849「geo["W%"] = np.where(np.isfinite(geo["res_hi"]) & np.isfinite(geo["sup_lo"]),」
状態: 確定

#### 実装 25
対象のファイル: scripts/priority_rebuild/engine_tuner_exec.py
直す箇所: 2687〜2689行（run_recipe・売買を回すプログラムのレンジ幾何の列に下半分位置を足す（観察の道具と同じ式））
直す前の文字:
~~~
        wpct_arr = np.where(np.isfinite(res_hi) & np.isfinite(sup_lo), (res_hi - sup_lo) / c * 100.0, np.nan)
    geo = {"res_hi": res_hi, "res_lo": res_lo, "sup_hi": sup_hi, "sup_lo": sup_lo,
           "mid": mid, "W%": wpct_arr, "帯内位置%": pos_arr}

~~~
直した後の文字:
~~~
        wpct_arr = np.where(np.isfinite(res_hi) & np.isfinite(sup_lo), (res_hi - sup_lo) / c * 100.0, np.nan)
        # ★2026-10-09（工事 m2c15-shape-structure-20261009・監査 CP60 の修正65）＝下半分の位置（観察の道具 build_range_geometry と同じ式）
        dn_arr = mid - sup_lo
        low_arr = np.where(np.isfinite(dn_arr) & (dn_arr > 0), (c - mid) / dn_arr, np.nan)
    geo = {"res_hi": res_hi, "res_lo": res_lo, "sup_hi": sup_hi, "sup_lo": sup_lo,
           "mid": mid, "W%": wpct_arr, "帯内位置%": pos_arr, "下半分位置": low_arr}

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_exec.py:2687「wpct_arr = np.where(np.isfinite(res_hi) & np.isfinite(sup_lo), (res_hi - sup_lo) / c * 100.0, np.nan)」
状態: 確定

#### 実装 26
対象のファイル: scripts/priority_rebuild/engine_tuner_fire_diag.py
直す箇所: 164〜166行（build_geo・関門を数える道具（build_geo＝run_generation と同じ作り方）に下半分位置を足す）
直す前の文字:
~~~
        geo["W%"] = np.where(np.isfinite(geo["res_hi"]) & np.isfinite(geo["sup_lo"]),
                             (geo["res_hi"] - geo["sup_lo"]) / c * 100.0, np.nan)
    return geo

~~~
直した後の文字:
~~~
        geo["W%"] = np.where(np.isfinite(geo["res_hi"]) & np.isfinite(geo["sup_lo"]),
                             (geo["res_hi"] - geo["sup_lo"]) / c * 100.0, np.nan)
        # ★2026-10-09（工事 m2c15-shape-structure-20261009・監査 CP60 の修正65）＝下半分の位置（観察の道具 build_range_geometry と同じ式）
        dn = geo["mid"] - geo["sup_lo"]
        geo["下半分位置"] = np.where(np.isfinite(dn) & (dn > 0), (c - geo["mid"]) / dn, np.nan)
    return geo

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_fire_diag.py:164「geo["W%"] = np.where(np.isfinite(geo["res_hi"]) & np.isfinite(geo["sup_lo"]),」
状態: 確定

#### 実装 27
対象のファイル: .claude/memory/regime_detection_kb.md
直す箇所: 1290〜1295行（文書・足す4種とレンジ幾何の下半分位置で、材料の種類・一覧の行・部品の数が変わる＝KB の件数の囲み（gen_materials.py --write が書き出す所）を、写しで数えた文に置き換える（材料の文書の自己テストの B3・B4 と承認の前の検査 A12 が見る））
直す前の文字:
~~~
<!-- COUNTS_START gen_materials.py --write が実物から書き出す＝手で書き換えない -->
| 5 | 指標の種類 | **272種類**（engine_tuner が選べる **154**／選べない **118**） | materials.md の「engine_tuner が選べる指標の種類」の行 |
| 6 | 材料の一覧の行 | **277件**（在る。ほかに「入れない」45件） | materials.md の一覧 |
| 7 | パラメータまで展開した部品 | **488件**（＋別枠 7件＝**495**） | signal_families.json の parts と extra_parts |
| 8 | ★495 に膨らむ理由 | ADX7・ADX14・ADX21 のように、同じ指標のパラメータ違いを別々に数えているため | 部品の名前の実測 |
<!-- COUNTS_END -->
~~~
直した後の文字:
~~~
<!-- COUNTS_START gen_materials.py --write が実物から書き出す＝手で書き換えない -->
| 5 | 指標の種類 | **276種類**（engine_tuner が選べる **154**／選べない **122**） | materials.md の「engine_tuner が選べる指標の種類」の行 |
| 6 | 材料の一覧の行 | **282件**（在る。ほかに「入れない」45件） | materials.md の一覧 |
| 7 | パラメータまで展開した部品 | **488件**（＋別枠 7件＝**495**） | signal_families.json の parts と extra_parts |
| 8 | ★495 に膨らむ理由 | ADX7・ADX14・ADX21 のように、同じ指標のパラメータ違いを別々に数えているため | 部品の名前の実測 |
<!-- COUNTS_END -->
~~~
根拠の抜き書き: .claude/memory/regime_detection_kb.md:1290「<!-- COUNTS_START gen_materials.py --write が実物から書き出す＝手で書き換えない -->」
状態: 確定

#### 実装 28
対象のファイル: .claude/breaks/b151_w_fractal_not_first.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: W字確定谷の「ネックを最初に上抜けた足だけ 1」を外す（条件が続く間ずっと1）と、観察の道具の自己テスト（手計算の既知答え）が落ちる
# EXPECT_MSG: W字確定谷(24,0.003): 手計算の既知答えと不一致
# b151_w_fractal_not_first — W字確定谷の「ネックを最初に上抜けた足だけ 1」を外す（条件が続く間ずっと1）と、観察の道具の自己テスト（手計算の既知答え）が落ちる（工事 m2c15-shape-structure-20261009・2026-10-09）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「W字確定谷(24,0.003): 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        if ca[i] > neck and not (ca[j2 + 1:i] > neck).any():\n'
new = '        if ca[i] > neck:\n'
if s.count(old) != 1:
    raise SystemExit("[b151_w_fractal_not_first] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 29
対象のファイル: .claude/breaks/b152_sr_fractal_counts_bars.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: S-Rタッチ確定数で、確定した山の代わりに全部の足の高値を数えると、観察の道具の自己テスト（手計算の既知答え）が落ちる
# EXPECT_MSG: S-Rタッチ確定数(144,0.0015): 手計算の既知答えと不一致
# b152_sr_fractal_counts_bars — S-Rタッチ確定数で、確定した山の代わりに全部の足の高値を数えると、観察の道具の自己テスト（手計算の既知答え）が落ちる（工事 m2c15-shape-structure-20261009・2026-10-09）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「S-Rタッチ確定数(144,0.0015): 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    hv = _fractal_marks(d.high, k, True)[0].to_numpy(float)\n'
new = '    hv = d.high.to_numpy(float)\n'
if s.count(old) != 1:
    raise SystemExit("[b152_sr_fractal_counts_bars] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 30
対象のファイル: .claude/breaks/b156_sr_fractal_unconfirmed.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: S-Rタッチ確定数で、山を確定した足でなく山そのものの足に置く（まだ確定していない山を使う＝未来を見る）と、観察の道具の自己テスト（手計算の既知答え）が落ちる
# EXPECT_MSG: S-Rタッチ確定数(144,0.0015): 手計算の既知答えと不一致
# b156_sr_fractal_unconfirmed — S-Rタッチ確定数で、山を確定した足でなく山そのものの足に置く（まだ確定していない山を使う＝未来を見る）と、観察の道具の自己テスト（手計算の既知答え）が落ちる（工事 m2c15-shape-structure-20261009・2026-10-09）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「S-Rタッチ確定数(144,0.0015): 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    hv = _fractal_marks(d.high, k, True)[0].to_numpy(float)\n'
new = '    hv = _fractal_marks(d.high, k, True)[0].shift(-int(k)).to_numpy(float)\n'
if s.count(old) != 1:
    raise SystemExit("[b156_sr_fractal_unconfirmed] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 31
対象のファイル: .claude/breaks/b153_smc_fractal_no_close_back.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: SMC_SWEEP確定で、終値で谷の上に戻した条件を外すと、観察の道具の自己テスト（手計算の既知答え）が落ちる
# EXPECT_MSG: SMC_SWEEP確定: 手計算の既知答えと不一致
# b153_smc_fractal_no_close_back — SMC_SWEEP確定で、終値で谷の上に戻した条件を外すと、観察の道具の自己テスト（手計算の既知答え）が落ちる（工事 m2c15-shape-structure-20261009・2026-10-09）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「SMC_SWEEP確定: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    bull = ((d.low < lo) & (d.close > lo)).astype(float)\n'
new = '    bull = (d.low < lo).astype(float)\n'
if s.count(old) != 1:
    raise SystemExit("[b153_smc_fractal_no_close_back] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 32
対象のファイル: .claude/breaks/b154_lower_half_upper_span.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 下半分位置を上半分の幅で割る形（帯内位置% と同じ）に戻すと、観察の道具の自己テスト（レンジ幾何の既知答え）が落ちる
# EXPECT_MSG: レンジ幾何 既知答え不一致: 下半分位置
# b154_lower_half_upper_span — 下半分位置を上半分の幅で割る形（帯内位置% と同じ）に戻すと、観察の道具の自己テスト（レンジ幾何の既知答え）が落ちる（工事 m2c15-shape-structure-20261009・2026-10-09）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「レンジ幾何 既知答え不一致: 下半分位置」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        low = np.where(np.isfinite(dn) & (dn > 0), (c - mid) / dn, np.nan)\n'
new = '        low = np.where(np.isfinite(span) & (span > 0), (c - mid) / span, np.nan)\n'
if s.count(old) != 1:
    raise SystemExit("[b154_lower_half_upper_span] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 33
対象のファイル: .claude/breaks/b155_geo_mako_not_read.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: geo_on が源4 のレンジ幾何（mako の欄）を読まない形に戻すと、印を作る道具の自己テスト T12 が落ちる
# EXPECT_MSG: T12 まこさんが個別に決めたレンジ幾何の列は必ず使う → ng
# b155_geo_mako_not_read — geo_on が源4 のレンジ幾何（mako の欄）を読まない形に戻すと、印を作る道具の自己テスト T12 が落ちる（工事 m2c15-shape-structure-20261009・2026-10-09）
#   守っているもの＝完成の条件の印を作る道具の自己テスト（gen_indicator_switch.py --selftest）
#   壊し方＝scripts/priority_rebuild/gen_indicator_switch.py の中の、下の old を new に置き換える（k3b_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝gen_indicator_switch.py --selftest が「T12 まこさんが個別に決めたレンジ幾何の列は必ず使う → ng」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/gen_indicator_switch.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        "geo_on": sorted(law_g | id_g | mako_g),\n'
new = '        "geo_on": sorted(law_g | id_g),\n'
if s.count(old) != 1:
    raise SystemExit("[b155_geo_mako_not_read] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/gen_indicator_switch.py" --selftest
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
| 1 | 確定の本数 k を名前に出さない引数にする | 名前に入れると資料の行と軸の数が合わず、まこさんの「名前に値を入れて指標を増やさない」にも反する（まこさん「よい」2026-10-09 の1） | k を名前に出す |
| 2 | 確定の決まりを _fractal_marks に切り出し、今の _fractal_levels と4種が同じものを使う | 同じ決まりを2か所に書かない。今の列の値が変わらないことは写しで確かめた（0本の違い） | 4種に確定の決まりをもう1つ書く |
| 3 | SMC_SWEEP確定はライブラリの 15・1.5 を使わず、資料の行のパラメータを写さない | 教科書の形にヒゲの倍率の条件は無い。写すと使わない数字が資料と設定に入る（まこさん「よい」2026-10-09 の2・対応表の「パラメータ」＝「写さない」） | ライブラリの数字のまま確定した山・谷に替える |
| 4 | 下半分位置の「使う」は、レンジ幾何の定義表の mako の欄を印を作る道具が読む形にする | 今の geo_on は法則と恒等レシピの2つからしか作れず、まこさんが個別に決めた列を入れる道が無い（まこさん「よい」2026-10-09 の3） | 法則の名指しに足す（法則は相場の法則の原文から作るので、CC が足せない） |
| 5 | K-3a の対応表 alias_map.json は封のまま触らず、K-3b の4種は alias_map_k3b.json に書く | 封をし直さずに済む。読む道具3本は alias_maps.py で全部のファイルを合わせて読む（同じ種類が2つに在れば止まる） | alias_map.json の封を外して書き足す |
| 6 | 名前に出さない引数の番人で、W字確定谷だけ形の出る既知答えの足を使う | 決まった式の値動きでは W の形が出ず、k が計算に届いているかを見られない（写しで実測） | 番人から W字確定谷を外す |
| 7 | この工事（コード）と、G-1 の後の2つ目の工事（4種の探す範囲を写す）に分ける | 4種は G-1 まで「使う」でなく資料の行も無い。K-3a と同じ（承認の前の検査 A12 は指示だけを当てて測る） | 道具が作るはずの表まで指示に入れて1回で当てる |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=47d984796afaf896 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b151_w_fractal_not_first.sh` | #1 | 「最初に上抜けた足だけ」を外す |
| `b152_sr_fractal_counts_bars.sh` | #2 | 確定した山の代わりに全部の足の高値を数える |
| `b156_sr_fractal_unconfirmed.sh` | #3 | 山を確定した足でなく山そのものの足に置く |
| `b153_smc_fractal_no_close_back.sh` | #4 | 終値で戻した条件を外す |
| `b154_lower_half_upper_span.sh` | #5 | 上半分の幅で割る形に戻す |
| `b155_geo_mako_not_read.sh` | #6 | geo_on が mako の欄の列を読まない形に戻す |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 型の表が変わる | G-1 で作り直し、まこさんに再承認していただく（4-4 の4） |
| 2 | 確定の本数 k の最初の値 2 で、山・谷が多すぎる・少なすぎる | 範囲で探すのは工事2（M2-F-10b）。この工事は材料を足すだけ |
| 3 | S-Rタッチ確定の数え方は Python の繰り返しで、全体の自己テストが重くなる | 写しの実測 136秒（4-14） |
| 4 | W字確定谷の範囲が1点（許容幅 0.003）のまま写る | 3-2 で決めていただく（K-7 の範囲の直しを掛けるか） |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（--design） | 1分未満 | 前の工事で、当てる道具は1秒未満で終わった |
| 全体の自己テスト | 136秒 | 4-14 |
| 壊すプログラム | 1本あたり約 136秒（全体の自己テスト）×5本と、印を作る道具の自己テストの1本 | 写しで壊し方を並べて走らせた（k3b_draft_build.py の [8]） |
| G-1 の表の作り直しと資料の道具4本 | 約2分 | 写しの実測（オン・オフの表 約3秒・資料の道具4本 約7秒）と前の工事の実測 |
| 監査に出す前のチェック | 約10分 | 前の工事の実測（pre_audit_check.py --run） |
| まこさんの承認 | この工事の設計書1回・型の表の再承認1回（変われば）・2つ目の工事の設計書1回 | 4-4 |
| 2つ目の工事 | 前の工事の2つ目の工事（m2c15-period-settings-20261008）と同じ流れ（案 → OK → 設計書 → 承認 → 当てる） | worklog 20261008 §5 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝今の W字・S-Rタッチ・SMC_SWEEP は、確定した山・谷を使わず、移動窓の最高値・最安値や帯に掛かった足の本数で近似していた（監査 CP60 の表 27・48・49・61）。帯内位置% は下半分も上半分の幅で割っていた（表 143）。教科書の版が無いので、どちらが良いかを比べられなかった。この工事で教科書の版を足し、M2-F-10f で比べられるようにする。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。M2-F で使える材料が4種とレンジ幾何の1列 増えます。

**③ root か symptom か**＝root です。比べる相手（教科書の版）が無いことが原因で、それを足します。

**④ ベースアップ**＝4種の作りは、監査 CP60 の修正43・44・46・65 の本文と、資料の逐語（StockCharts・LuxAlgo・chartinglens）から取った。SMC_SWEEP のライブラリの作りは pandas_ta_classic/momentum/smc_sweep.py を開いて確かめた。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。k の最初の値 2 は資料の fractal の既定です。既知答えは合成の足から手で計算できる値です。壊し方の値も、当てた後の中身の行から道具が取りました。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝確定した山・谷で作る教科書の版を4種と、レンジ幾何の下半分位置を、今の版を残して足す（K-3b の1つ目の工事。4種の探す範囲を写すのは G-1 の後の2つ目の工事）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。条件をつなぐものではなく、教科書の作りの材料を足すだけです |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 4種の窓と許容幅は今の版と同じ一覧から作り、探す範囲は資料から道具が写します |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **既知答えが、本物の値動きでの正しさまで見るか** | 見ません。合成の足で、確定の決まり・最初の上抜け・帯の数え方を見るだけです |
| **k の最初の値 2 が、この市場に合っているか** | 見ません。範囲で探すのは工事2 です |
| **資料の値そのものが正しいかを、照らしの道具が見るか** | 見ません。照らしの道具は、資料と設定ファイルが同じかだけを見ます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=336f5532eecb6661 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝observe_diag.py・indicator_reference_diag.py・gen_indicator_switch.py・engine_tuner_gen.py・engine_tuner_exec.py・engine_tuner_fire_diag.py・regime_detection_kb.md（件数の囲み）と、新しい壊すプログラムを【7-8】に書いた。主なファイルは observe_diag.py（材料の計算）。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝observe_diag.py・触る関数は道具が構文木の差から数えた）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム（NEW_FILE）。手本は b142（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝写しの道具を作ってから承認の前の検査 A12 の作りを知った（159回目）。この工事は、A12 の本体から自己テストの一覧と許しの判定を import する前の工事の道具（k3a_draft_build.py）を使い回した。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 新しい部品は、未来を見ない形にした（山・谷は確定してから使う・SMC_SWEEP確定は1本前までに確定した山・谷）。当てた後に H2 を取り直す。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 行番号を指す文書は、当てた後に動く（observe_diag.py・indicator_reference_diag.py・gen_indicator_switch.py に行が増える）。設計書の行番号は当てる前の実物のもの。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、探す文字の数が当てる前と後で同じことを道具が数えた（4-13 の5）。走らせるコマンドの旗は変えない。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムが測るのは、観察の道具の全体の自己テストと印を作る道具の自己テストで、どちらも本物の結果の置き場には書かない。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 触る関数（DESIGN_CONTRACT の impl_functions・道具が書いた）＝observe_diag.py：<モジュール直下>・_fractal_levels・_fractal_marks・_insp_hidden_params・_smc_sweep_fractal・_sr_touch_fractal・_sr_touch_fractal_atr・_w_fractal・build_catalog・build_range_geometry／indicator_reference_diag.py：<モジュール直下>・_smc_fr_case・_sr_fr_case・_tb_fractal_marks・_tb_smc_fr・_tb_sr_fr・_tb_sr_fr_atr1h・_tb_w_fr・_w_case2・range_geo_known_check／gen_indicator_switch.py：build・cmd_selftest・source_mako_geo／engine_tuner_gen.py：_geo_of／engine_tuner_exec.py：run_recipe／engine_tuner_fire_diag.py：build_geo。self_check_calls と must_use の名前は、当てた後の構文木に在ることを道具が ast で照らした。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足すコマンドの旗は無い。資料の道具の直し（alias_maps.py・対応表の「写さない」）は .claude/state の道具の側で、設計書の前に済ませた。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2c15-shape-structure-20261009）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝観察の道具の既知答え・独立の実装・印を作る道具の T12・照らしの道具の①②と、壊すプログラム（わざと壊して落ちるか）。写しで走らせ、全部 通った。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | F-1・F-2＝W字確定谷が、2つ目の谷の後に最初に上抜けた足だけ 1 になる（既知答えが通る） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | 「最初に上抜けた足だけ」を外す | `b151_w_fractal_not_first.sh` | — | **未着手** |
| 2 | F-1・F-2＝S-Rタッチ確定数が、確定した山・谷だけを数える（既知答えが通る） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | 確定した山の代わりに全部の足の高値を数える | `b152_sr_fractal_counts_bars.sh` | — | **未着手** |
| 3 | F-1・F-2＝S-Rタッチ確定数が、確定した足に来てから山を数える（まだ確定していない山を使わない・既知答えが通る） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | 山を確定した足でなく山そのものの足に置く | `b156_sr_fractal_unconfirmed.sh` | — | **未着手** |
| 4 | F-1・F-2＝SMC_SWEEP確定が、終値で戻した足だけを数える（既知答えが通る） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | 終値で戻した条件を外す | `b153_smc_fractal_no_close_back.sh` | — | **未着手** |
| 5 | F-3＝下半分位置が、下半分の幅で割る（レンジ幾何の既知答えが通る） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | 上半分の幅で割る形に戻す | `b154_lower_half_upper_span.sh` | — | **未着手** |
| 6 | F-4＝下半分位置が geo_on に入る（印を作る道具の自己テスト T12 が通る） | `python3 scripts/priority_rebuild/gen_indicator_switch.py --selftest` | 実経路 | geo_on が mako の欄の列を読まない形に戻す | `b155_geo_mako_not_read.sh` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=90532b21013084c2 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/observe_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `_fractal_marks` | （この関数は実物に無い） |
| `_fractal_levels` | 581 |
| `_w_fractal` | （この関数は実物に無い） |
| `_sr_touch_fractal` | （この関数は実物に無い） |
| `_sr_touch_fractal_atr` | （この関数は実物に無い） |
| `_smc_sweep_fractal` | （この関数は実物に無い） |
| `build_range_geometry` | 2016 |
| `build_catalog` | 1396 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 183件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=1611fabd499336d1 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/observe_diag.py",
  "_impl_file の意味": "照らす相手は実在するファイル。足す4種の計算（_fractal_marks・_w_fractal・_sr_touch_fractal・_sr_touch_fractal_atr・_smc_sweep_fractal）とカタログ（build_catalog）とレンジ幾何（build_range_geometry）が在る、観察の道具を照らす。",
  "impl_functions": {
    "scripts/priority_rebuild/observe_diag.py": [
      "<モジュール直下>",
      "_fractal_levels",
      "_fractal_marks",
      "_insp_hidden_params",
      "_smc_sweep_fractal",
      "_sr_touch_fractal",
      "_sr_touch_fractal_atr",
      "_w_fractal",
      "build_catalog",
      "build_range_geometry"
    ],
    "scripts/priority_rebuild/indicator_reference_diag.py": [
      "<モジュール直下>",
      "_smc_fr_case",
      "_sr_fr_case",
      "_tb_fractal_marks",
      "_tb_smc_fr",
      "_tb_sr_fr",
      "_tb_sr_fr_atr1h",
      "_tb_w_fr",
      "_w_case2",
      "range_geo_known_check"
    ],
    "scripts/priority_rebuild/gen_indicator_switch.py": [
      "build",
      "cmd_selftest",
      "source_mako_geo"
    ],
    "scripts/priority_rebuild/engine_tuner_gen.py": [
      "_geo_of"
    ],
    "scripts/priority_rebuild/engine_tuner_exec.py": [
      "run_recipe"
    ],
    "scripts/priority_rebuild/engine_tuner_fire_diag.py": [
      "build_geo"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数（実装の指示を全部 当てる前と後の構文木を関数ごとに比べて、k3b_proposal_build.py が数えた）。",
  "self_check_calls": [
    "_fractal_marks",
    "_fractal_levels",
    "_w_fractal",
    "_sr_touch_fractal",
    "_sr_touch_fractal_atr",
    "_smc_sweep_fractal",
    "build_range_geometry",
    "build_catalog"
  ],
  "_self_check_calls の意味": "実装の後の observe_diag.py に在るはずの、この工事が足す・直す関数の名前。",
  "must_use": {
    "_fractal_levels": [
      "_fractal_marks"
    ],
    "_w_fractal": [
      "_fractal_marks"
    ],
    "_sr_touch_fractal": [
      "_fractal_marks"
    ],
    "_sr_touch_fractal_atr": [
      "_sr_touch_fractal"
    ],
    "_smc_sweep_fractal": [
      "_fractal_levels"
    ]
  },
  "_must_use の意味": "今の _fractal_levels と、確定した山・谷で作る3つの版が、同じ1つの確定の決まり（_fractal_marks）を使う（k3b_proposal_build.py が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は、材料とレンジ幾何の列を足すだけ。外から読む一覧の形（カタログの1件の形・参照表の欄・設定の欄）は変えない。",
  "generated_from": {
    "impl_functions": "当てる前と後の関数ごとの構文木の差（k3b_proposal_build.py が数えた）",
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

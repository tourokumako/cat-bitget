<!-- ARC iter="m2c15-period-textbook-20261007" -->

# 設計書｜K-3a 期間の区切り＝教科書の期間の版を別の材料として11種 足す・範囲の直しを設定に写す。M2-C-15

TARGET: .claude/memory/regime_detection_kb.md, scripts/priority_rebuild/indicator_reference_diag.py, scripts/priority_rebuild/observe_diag.py, scripts/priority_rebuild/recipes/search_limits.json, .claude/breaks/b145_vwap_day_no_reset.sh, .claude/breaks/b146_pivot_week_as_day.sh, .claude/breaks/b147_vp_today_from_start.sh, .claude/breaks/b148_bb_range_not_widened.sh
NEW_FILE: .claude/breaks/b145_vwap_day_no_reset.sh, .claude/breaks/b146_pivot_week_as_day.sh, .claude/breaks/b147_vp_today_from_start.sh, .claude/breaks/b148_bb_range_not_widened.sh
MODEL: .claude/breaks/b142_rci_list_stale.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2c15-period-textbook-20261007/ok_k3_split_20261007`・`m2c15-period-textbook-20261007/ok_k3a_20261008`・`m2c15-period-textbook-20261007/ok_k3a_rows_20261007`・`m2c15-period-textbook-20261007/okd_k3_split_20261007`・`m2c15-period-textbook-20261007/okd_k3a_20261008`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2c15-period-textbook-20261007/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-period-textbook-20261007 --write`。検出＝`--work m2c15-period-textbook-20261007 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=7dfefb380b247312 gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2c15-period-textbook-20261007/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2c15-period-textbook-20261007/ok_k3_split_20261007.txt`（まこさんの発言）・`verbatim/m2c15-period-textbook-20261007/ok_k3a_20261008.txt`（まこさんの発言）・`verbatim/m2c15-period-textbook-20261007/ok_k3a_rows_20261007.txt`（まこさんの発言）・`verbatim/m2c15-period-textbook-20261007/okd_k3_split_20261007.txt`（まこさんが OK した CC の文）・`verbatim/m2c15-period-textbook-20261007/okd_k3a_20261008.txt`（まこさんが OK した CC の文）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝604 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_k3_split_20261007` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_k3a_20261008` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_k3a_rows_20261007` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_k3_split_20261007` | V01〜V40（40 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_k3a_20261008` | V01〜V08（8 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_k3a_20261008` | V09〜V58（50 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V59〜V64（6 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V65〜V70（6 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V71〜V83（13 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V84〜V90（7 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V91〜V100（10 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V101〜V110（10 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V111〜V112（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V113〜V114（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V115〜V118（4 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V119〜V120（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V121〜V122（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V123〜V128（6 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V129〜V137（9 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V138〜V143（6 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V144〜V145（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V146〜V147（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V148〜V149（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V150〜V156（7 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V157〜V401（245 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V402〜V412（11 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V413〜V419（7 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V420〜V429（10 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V430〜V436（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V437〜V438（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V439〜V440（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V441〜V445（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V446〜V456（11 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V457〜V477（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V478〜V484（7 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V485〜V556（72 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_k3a_20261008` | V557〜V561（5 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
監査 CP60 は、今の材料のいくつかが教科書と違う作りだと指摘しました。VWAP は教科書ではセッションの始まりから積み上げる典型価格ですが、今の材料は終値の288本の移動窓です。出来高プロファイル（POC・VAH・VAL）は教科書では前のセッションの値を後のセッションで使いますが、今の材料は直前288本の移動窓です。まこさんは、今の版を残し、教科書の版を別の材料として足して、後で比べる形を決めました（K-3 の「A」）。K-7 では、前期間pivot に前の週の版を足すこと、BB と W字 の範囲を教科書の値に届くように広げることも決まりました。この工事は、その11種を観察の道具と参照表に足し、範囲の直しを設定ファイルに写します。11種の資料の行は、新しく調べずに同じ指標の今の行の調べた結果を使います（まこさん「B」）。前から在る列の値は1本も変えません。どちらの版が良いかを比べるのは、この工事ではなく M2-F-10f です。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 足す11種の登録（F-1） | `grep -n -F 'close vs 当日VWAP%' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、登録とカタログの行に在る | （終了コード 1） |
| 前の週で区切る作り（F-1） | `grep -n -F 'to_period("W-SUN")' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、_pivot_prev_period の中に在る | （終了コード 1） |
| 日で区切る出来高プロファイル（F-1） | `grep -n -F 'def _vp_by_day' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、在る | （終了コード 1） |
| BB%b の探す範囲（F-3） | `grep -n -F '"BB%b": [{"kind": "int", "lo": 10, "hi": 50}' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json` | 実装の前は、無い（直す前の本数と倍率の範囲の行が在る）。実装の後は、material_param_ranges の中に在る | （終了コード 1） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

［自動］印のファイル・型の表・格子と範囲
<!-- ACC_MATERIALS_START hash=b61112e623987231 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`indicator_switch.json`・`signal_families.json`・`search_limits.json`。

**探す指標＝印がオンの 145種**（印を切り替えると、この一覧も設計も変わります）。

```
ADX・DI差・MACD線%・MACDヒスト%・MACDシグナル線%・RSI・ROC・Stoch%K・Stoch%D・MFI・CMF・OBV傾き・転換線・基準線・RCI・EMA傾き・ATR%・BB%b・BB幅・realized_vol・Donchian幅・volume_ratio・swing高値距離・swing安値距離・高値からの経過バー・安値からの経過バー・形スコア・W字・fractal高値距離%・fractal安値距離%・高値切り上げ幅%・安値切り上げ幅%・構造破断距離%・close vs EMA・close vs SMA・close vs VWAP・Keltner上・Keltner下・n本高値・n本安値・pivotPP・pivotR1・pivotS1・前期間pivotPP・前期間pivotR1・前期間pivotS1・fib位置・POC・VAH・VAL・MMI・S-Rタッチ1時間ATR・S-Rタッチ数・AO%・CCI・ER・KST・KSTシグナル・PPO・PPOシグナル・PPOヒスト・PVO・PVOシグナル・PVOヒスト・SMC_SWEEP・SQZ_ON・STC・STCstoch・StochRSI%K・StochRSI%D・TRIX・TRIXシグナル・TRIXヒスト・TSI・TSIシグナル・TSIヒスト・UO・close vs ALMA%・close vs DEMA%・close vs FWMA%・close vs HILO%・close vs HMA%・close vs HT_TRENDLINE%・close vs HWMA%・close vs JMA%・close vs KAMA%・KAMA傾き%・close vs LINREG%・close vs LRb%・close vs MAMA%・close vs FAMA%・close vs MCGD%・close vs MIDPOINT%・close vs MIDPRICE%・close vs MMAR%・close vs PWMA%・close vs RAINBOW%・close vs RMA%・close vs SINWMA%・close vs SSF%・close vs SWMA%・close vs T3%・close vs TEMA%・close vs TRIMA%・close vs TSF%・close vs VIDYA%・close vs VWMA%・close vs WMA%・WMA傾き%・close vs ZLMA%・AROONU・AROOND・AROONOSC・CHOP・close vs CKSPl%・close vs CKSPs%・DPO%・close vs PMAX%・close vs PSAR%・PSAR加速・PSAR反転・close vs SAREXT%・VHF・VTXP・VTXM・EFI比・EOM比・NVI傾き・PVT傾き・MAD比・stdev%・close vs MEDIAN%・close vs ABER_ZG%・ABER位置・close vs ACCBL%・close vs ACCBU%・close vs CE_L%・close vs CE_S%・HWC位置・HWC幅%・MASSI・THERMO%・TR%・UI・HT_DCPHASE
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
| `material_param_ranges` | {"ADX": [{"kind": "int", "lo": 7, "hi": 21}], "DI差": [{"kind": "int", "lo": 7, "hi": 21}], "MACD線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}], "MACDヒスト%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "MACDシグナル線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "転換線": [{"kind": "int", "lo": 5, "hi": 12}], "基準線": [{"kind": "int", "lo": 13, "hi": 26}], "EMA傾き": [{"kind": "int", "lo": 9, "hi": 200}], "KSTシグナル": [{"kind": "int", "lo": 9, "hi": 9}], "PPO": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOシグナル": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOヒスト": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "TRIX": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TSI": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIシグナル": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIヒスト": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "KAMA傾き%": [{"kind": "int", "lo": 7, "hi": 10}], "WMA傾き%": [{"kind": "int", "lo": 20, "hi": 200}], "AROONU": [{"kind": "int", "lo": 7, "hi": 288}], "AROOND": [{"kind": "int", "lo": 7, "hi": 25}], "AROONOSC": [{"kind": "int", "lo": 7, "hi": 25}], "VTXP": [{"kind": "int", "lo": 14, "hi": 30}], "VTXM": [{"kind": "int", "lo": 14, "hi": 30}], "RSI": [{"kind": "int", "lo": 2, "hi": 21}], "ROC": [{"kind": "int", "lo": 9, "hi": 24}], "Stoch%K": [{"kind": "int", "lo": 5, "hi": 21}], "Stoch%D": [{"kind": "int", "lo": 5, "hi": 21}], "MFI": [{"kind": "int", "lo": 10, "hi": 20}], "CMF": [{"kind": "int", "lo": 20, "hi": 36}], "OBV傾き": [{"kind": "int", "lo": 10, "hi": 20}], "BB%b": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}], "volume_ratio": [{"kind": "int", "lo": 20, "hi": 50}], "CCI": [{"kind": "int", "lo": 7, "hi": 21}], "PVO": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOシグナル": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOヒスト": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "StochRSI%K": [{"kind": "int", "lo": 7, "hi": 21}], "StochRSI%D": [{"kind": "int", "lo": 7, "hi": 21}], "DPO%": [{"kind": "int", "lo": 14, "hi": 40}], "EFI比": [{"kind": "int", "lo": 10, "hi": 20}], "EOM比": [{"kind": "int", "lo": 10, "hi": 20}], "NVI傾き": [{"kind": "int", "lo": 10, "hi": 20}], "PVT傾き": [{"kind": "int", "lo": 10, "hi": 20}], "ATR%": [{"kind": "int", "lo": 5, "hi": 21}], "BB幅": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}], "realized_vol": [{"kind": "int", "lo": 10, "hi": 50}], "Donchian幅": [{"kind": "int", "lo": 10, "hi": 20}], "MMI": [{"kind": "int", "lo": 200, "hi": 500}], "ER": [{"kind": "int", "lo": 7, "hi": 21}], "CHOP": [{"kind": "int", "lo": 7, "hi": 21}], "VHF": [{"kind": "int", "lo": 7, "hi": 28}], "MAD比": [{"kind": "int", "lo": 20, "hi": 50}], "stdev%": [{"kind": "int", "lo": 10, "hi": 50}], "UI": [{"kind": "int", "lo": 7, "hi": 21}], "高値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "安値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "形スコア": [{"kind": "int", "lo": 24, "hi": 96}], "W字": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.003, "hi": 0.003, "dec": 3}], "fractal高値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "fractal安値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "高値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "安値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "構造破断距離%": [{"kind": "int", "lo": 2, "hi": 3}], "close vs EMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs SMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs VWAP": [{"kind": "int", "lo": 288, "hi": 288}], "Keltner上": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "Keltner下": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "n本高値": [{"kind": "int", "lo": 10, "hi": 50}], "n本安値": [{"kind": "int", "lo": 10, "hi": 50}], "pivotPP": [{"kind": "int", "lo": 288, "hi": 288}], "pivotR1": [{"kind": "int", "lo": 288, "hi": 288}], "pivotS1": [{"kind": "int", "lo": 288, "hi": 288}], "fib位置": [{"kind": "int", "lo": 14, "hi": 96}], "S-Rタッチ1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}], "S-Rタッチ数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}], "close vs ALMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs DEMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs FWMA%": [{"kind": "int", "lo": 10, "hi": 20}], "close vs HMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs JMA%": [{"kind": "int", "lo": 3, "hi": 80}], "close vs KAMA%": [{"kind": "int", "lo": 7, "hi": 30}], "close vs LINREG%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs LRb%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs MCGD%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs MIDPOINT%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MIDPRICE%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MMAR%": [{"kind": "int", "lo": 10, "hi": 35}], "close vs PWMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs RAINBOW%": [{"kind": "int", "lo": 2, "hi": 2}, {"kind": "int", "lo": 1, "hi": 10}], "close vs RMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SINWMA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs SSF%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SWMA%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs T3%": [{"kind": "int", "lo": 8, "hi": 200}], "close vs TEMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TRIMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TSF%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs VIDYA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs VWMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs WMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs MEDIAN%": [{"kind": "int", "lo": 4, "hi": 200}], "RCI": [{"kind": "int", "lo": 5, "hi": 52}]} |

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
| 1 | 監査 CP60 の修正41 の説明の直し | 修正41 の状態は「未決」で、監査の修正を当てる道具は未決の件を当てない（apply_audit_fix.py:37・883）。まこさんが状態を決めた後に、その道具で当てる | 監査 CP60 の修正41 |
| 2 | 足した版と今の版を比べること | 比べるのは M2-F-10f。この工事は材料を足すだけ | 監査 CP60 の修正41・42 の補足 |
| 3 | 法則の帯で教科書の pivot・VAH/VAL を使うこと | 4つの工事の最後（B-1＋S-1） | まこさん「A」（4つの工事に分ける） |
| 4 | 成績表（material_ranking.json）の作り直し | M2-D-8。増える11列は、作り直すまで段の候補の順位に出ない | 前の工事と同じ |
| 5 | 出来高プロファイルの区画24・70% を探す範囲にすること | 今の POC・VAH・VAL と同じく、名前に出さない引数のまま（値を埋めない種類の並びに載る）。値を渡すのは工事2（M2-F-10b） | 前の工事の material_first_hidden の説明 |
| 6 | ta のクラスの対応（TA_CLASS_MAP）を変えること | 「使う」の印の源1 を変えると、ほかの種類の印も作り直しになる。11種の「使う」は参照表の mako の欄で付ける | gen_indicator_switch.py の源の作り |
| 7 | K-3b・K-3c の種類 | 次の工事 | まこさん「A」 |
| 8 | 監査に出す前のチェックの自己テストの P7-1 の落ち | この工事の前から在る。next_step §6 に積んである | worklog 20261007 §11 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 前の週の区切り（週の始まり） | 月曜0時 UTC に始まる7日（ISO 8601 の週）。★出どころの逐語は在りません。資料の逐語（StockCharts・TradingView）は「前の週」とだけ書き、週の始まりを書いていない | 資料 indicator_params_review.json の前期間pivotPP の行・ISO 8601 |
| 2 | その日の0時から育つ出来高プロファイルに、今の足を入れるか | 入れない（その日の0時から1本前まで）。今の POC・VAH・VAL（_vp_levels）も今の足を窓に入れていないので、同じ決まりにする。その日の最初の足は値が無い（NaN） | observe_diag.py の _vp_levels（窓 [i−n, i)） |
| 3 | UTC 0時から積み上げる VWAP に、今の足を入れるか | 入れる。教科書の積み上げは今の足までを含む（StockCharts「Cumulative(Volume x Typical Price)/Cumulative(Volume)」）。pandas-ta の vwap も同じで、値で照らす | 監査 CP60 の結果の §5 外部検索の3（StockCharts の逐語）・pandas-ta overlap/vwap.py:46 |
| 4 | 工事の分け方 | この工事（コード・範囲の直し）と、G-1 の後の2つ目の工事（11種の設定を写す）に分ける。承認の前の検査 A12 は指示だけを当てて測るので、11種の設定を同じ工事に入れると、当てた直後に照らしの①②と壊し方が狙いまで届かない（写しで実測） | require_design_check_before_approval.py:560〜715 |
| 5 | 監査の出し方 | この工事と2つ目の工事をまとめて、実装の監査 CP67 の1回に出す | 恒久65番の1（監査は1つの工事につき1回） |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、教科書の期間の区切りで作る版を、今の版を残して別の材料として足す工事です。**監査 CP60 は、VWAP・出来高プロファイル（POC・VAH・VAL）・前期間pivot の今の作りが、教科書と違うと指摘しました。まこさんは、今の版を残して教科書の版を足し、後で比べる形を決めました（K-3 の「A」・K-7 の「OK」）。どちらが良いかを比べるのは M2-F-10f で、この工事は材料を足すだけです。
**①足す11種（名前・作り）。**
| 材料の名前 | 作り | 出どころ |
|---|---|---|
| close vs VWAP典型%288 | 典型価格（(高値＋安値＋終値)÷3）の288本の移動窓の VWAP からの乖離%。窓の一覧は今の close vs VWAP% と同じ（vwap_windows） | 監査 CP60 の修正41 の (b)＝ta の VolumeWeightedAveragePrice の作り |
| close vs 当日VWAP% | UTC の日の0時から積み上げる典型価格の VWAP からの乖離%（今の足までを含む） | 修正41 の (c)＝StockCharts「VWAP calculations start fresh at the open」・pandas-ta の vwap |
| close vs 前日POC%・前日VAH%・前日VAL% | 前の UTC の日の足ぜんぶで作り、その日のあいだ線が動かない | 修正42「前の UTC の日で固定（教科書の『前のセッションの値を後のセッションの参照にする』）」 |
| close vs 当日POC%・当日VAH%・当日VAL% | その日の0時から1本前までの足で作り、足が進むごとに育つ（今の足は窓に入れない＝今の版と同じ） | 修正42「その日の0時から育つ版」 |
| close vs 前週pivotPP%・前週pivotR1%・前週pivotS1% | 前の週（月曜0時 UTC に始まる7日）の高値・安値・終値で作り、その週のあいだ線が動かない | K-7 の決定・StockCharts「Pivot Points for 30-, 60-, and 120-minute charts use the prior week's high, low, and close.」 |
**②既知答え（手で計算できる合成の足・データの始まり 2026-03-01 は日曜）。**
| 材料 | 合成の足 | 答え |
|---|---|---|
| VWAP典型 | 全部の足が 高値112・安値100・終値103・出来高1 | 典型価格105 → (103÷105−1)×100。終値で作ると 0 になる＝値段の取り違えが分かる |
| 当日VWAP | 1日目288本＝終値150。2日目＝典型価格105 の足2本（出来高1）と、99 の足1本（出来高2） | 2本目＝(103÷105−1)×100。3本目＝VWAP (105＋105＋99×2)÷4＝102 → (99÷102−1)×100。日で区切らないと1日目の150 が混ざる |
| 前日POC・VAH・VAL | 1日目＝終値100 の足144本と200 の足144本（出来高の比 10:1 と 6:4）。2日目＝終値100 | 今の POC・VAH・VAL の手計算と同じ答え（POC と VAL は下の区画・VAH は 10:1 で下・6:4 で上）。同じ日の足で作ると乖離0 になる |
| 当日POC・VAH・VAL | 1日目288本＝終値150。2日目＝終値100 と200 の足20本、最後に終値100 | 同上。日で区切らないと1日目の150 が線になる |
| 前週pivot | 1日目（日曜）＝終値105・高値110 が1本・安値100 が1本。2日目（月曜）＝全部104。3日目＝終値105 | 3日目の線は日曜の週から＝PP 105・R1 110・S1 100 → 乖離 0・(105÷110−1)×100・5。前の日の版なら 104 で作るので答えが変わる |
**③オン・オフの表（使う）の違い（G-1 の試し＝写しで作り直した・道具が数えた）。**
使う 145 種 → 156 種。増えた 11 種＝close vs VWAP典型・前日POC・前日VAH・前日VAL・前週pivotPP・前週pivotR1・前週pivotS1・当日POC・当日VAH・当日VAL・当日VWAP。減った 0 種。
**④範囲の違い（今の設定 → 当てた後・道具が数えた）。**
| 種類 | 今の範囲 | 当てた後の範囲 |
|---|---|---|
| BB%b | 20〜50・2.0〜2.0 | 10〜50・1.9〜2.1 |
| BB幅 | 20〜50・2.0〜2.0 | 10〜50・1.9〜2.1 |
| W字 | 24〜96・0.003〜0.003 | 24〜96・0.0〜0.06 |
**⑤値を埋めずに並べる種類（P-4）の違い（この工事・道具が数えた）。**
なし
**⑥範囲で見つかったこと。**
- 範囲を広げた軸＝ROC の軸1: 範囲 9〜14 の外に、一覧の値 [9.0, 12.0, 24.0] が在る → 9〜24 に広げる
- 範囲を広げた軸＝close vs T3% の軸1: 範囲 8〜34 の外に、カタログの値 [20.0, 50.0, 200.0] が在る → 8〜200 に広げる
- 軸の順が入れ替わる組（前の工事から在る・工事2）＝MACD線%: 軸1 3〜12 と 軸2 10〜26 が重なる
- 軸の順が入れ替わる組（前の工事から在る・工事2）＝MACDヒスト%: 軸1 3〜12 と 軸2 10〜26 が重なる
- 軸の順が入れ替わる組（前の工事から在る・工事2）＝MACDシグナル線%: 軸1 3〜12 と 軸2 10〜26 が重なる
- 軸の順が入れ替わる組（前の工事から在る・工事2）＝TSI: 軸1 4〜13 と 軸2 7〜26 が重なる
- 軸の順が入れ替わる組（前の工事から在る・工事2）＝TSIシグナル: 軸1 4〜13 と 軸2 7〜26 が重なる
- 軸の順が入れ替わる組（前の工事から在る・工事2）＝TSIヒスト: 軸1 4〜13 と 軸2 7〜26 が重なる
- P-3＝この直しで増えた、端の値が効いていない軸 0件（範囲の端とまん中の値で列を作り、2種類の値動きで比べた）。
**⑦2つ目の工事で写す設定（G-1 の試しの後に、資料から写し直すと変わる行・道具が数えた）。**
- observe_config.json（2 行）
```
- "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0"],
+ "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0", "close vs VWAP典型＝範囲が1点のまま（全部の軸）：288", "当日VWAP＝最初の値も範囲も決まらない", "前日POC＝最初の値も範囲も決まらない", "前日VAH＝最初の値も範囲も決まらない", "前日VAL＝最初の値も範囲も決まらない", "当日POC＝最初の値も範囲も決まらない", "当日VAH＝最初の値も範囲も決まらない", "当日VAL＝最初の値も範囲も決まらない"],
```
- search_limits.json（3 行）
```
-    "RCI": [{"kind": "int", "lo": 5, "hi": 52}]
+    "RCI": [{"kind": "int", "lo": 5, "hi": 52}],
+    "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}]
```

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、当てる道具 apply_audit_fix.py・観察の道具の自己テスト・照らしの道具・表を作る道具（G-1）・資料の道具4本・監査に出す前のチェックを動かします。
**誰が結果を使うか。**
- 足した11種の列は、観察の道具の build_catalog が材料のカタログに入れ、engine_tuner と M2-F の段の道具が読みます。
- 参照表の登録（定義・既知答え・照合・系統・「使う」の決定）は、観察の道具の自己テストと、オン・オフの表を作る道具（gen_indicator_switch.py）が読みます。
- 探す範囲の設定は、engine_tuner_gen.py の material_ranges が読みます。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**今の実物（observe_diag.py・indicator_reference_diag.py・search_limits.json）・資料（indicator_params_by_strategy.json ほか2つ・research/alias_map.json）・設計書の 4-20。
**書くもの。**
- 当てる（--design）：observe_diag.py・indicator_reference_diag.py・search_limits.json・知識の文書 regime_detection_kb.md の件数の囲みと、新しい壊すプログラム 4本。
- G-1：オン・オフの表・型の表・出口の型の表・材料の文書・観察の説明書・組み立ての表・資料の表3つ（資料の道具4本）・修正対応表。
- 2つ目の工事（G-1 の後）：observe_config.json・search_limits.json の、資料から写す塊（4-0 の⑦）。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 今の版を残して、教科書の版を別の材料として足す | まこさん「A」（K-3）・K-7 の「OK」 | 今の close vs VWAP%・POC%・VAH%・VAL%・前期間pivot は1文字も変えません。前から在る列の値は直す前と同じです（写しで 0本の違い） |
| 指標の名前に値を入れて、指標の数を増やさない | まこさん 2026-10-04「指標名に閾値やパラメータの値を固定で入れて、指標数を増やすという解決策はやめてほしい」 | 新しい名前は、作りの違い（典型価格・当日・前日・前週）を表すだけで、値は入れません。VWAP典型 の窓は今の VWAP と同じ一覧から作ります |
| 数字を CC が作らない | 思考の順の7（req_thinking_20261004） | 範囲は資料から道具が写しました。既知答えの数字は合成の足から手で計算できる形で、式を 4-0 に書きました |
| 探す値を、点の一覧で先に限定しない | 要件の作ってはいけないもの2番 | BB と W字 の範囲を、教科書の値に届くように広げます |
| 未来のデータを使わない | 要件定義書 §4.6.H2 | 前日・前週は閉じた期間だけ、当日の出来高プロファイルは1本前まで、当日VWAP は今の足までを使います。当てた後に H2 を取り直します |
| 値段の高さで値が変わらない | 要件定義書 §4.6.H6 | 11種とも終値との乖離%（比）で作ります |
| 乱数を使わない | 恒久67番 | 乱数は使いません |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| observe_diag.py の _vp_one | 出来高プロファイルの1つの窓の計算（今の _vp_levels の中から切り出す・計算は変えない） | 新設 |
| observe_diag.py の _vp_by_day | 日で区切る出来高プロファイル（前日・当日） | 新設 |
| observe_diag.py の _vwap_day | UTC の日の0時から積み上げる典型価格の VWAP | 新設 |
| observe_diag.py の _pivot_prev_period | 前の期間の pivot に「前の週」を選べる引数を足す（渡さなければ今までと同じ） | 直す |
| observe_diag.py の build_catalog と登録（_reg） | 11種をカタログに入れる | 直す |
| indicator_reference_diag.py の登録（_r）・系統・業界の対応表・2つ目の照合 | 11種の定義・既知答え・照合・「使う」の決定の逐語 | 直す |
| search_limits.json の資料から写す塊 | 範囲の直し（道具が資料から写し直す） | 直す |
| regime_detection_kb.md の件数の囲み（COUNTS_START〜COUNTS_END） | gen_materials.py が書き出す「指標の種類・材料の一覧の行・部品の件数」（写しで gen_materials.bans_count_block が数えた文に置き換える） | 直す |
| .claude/breaks の壊すプログラム | 日の区切り・週の区切り・当日の区切り・範囲の写しを壊すと、決めた文で落ちるかを見る | 新設 |
- 触る関数（当てる前と後の構文木を関数ごとに比べて道具が数えた）＝observe_diag.py：<モジュール直下>・_pivot_prev_period・_vp_by_day・_vp_levels・_vp_one・_vwap_day・build_catalog／indicator_reference_diag.py：<モジュール直下>・_pivot_week_case・_tb_vs_vwap_tp・_tp_case・_vp_day_case・_vwap_day_case

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. まこさんの承認の後、全部を当てます（apply_audit_fix.py --design --dry → --design）。当てる道具は、全件を当てる前の実物で照らしてから、番号の順に当てます。1件でも合わなければ1件も当てません。
2. 当てた直後に、当てる道具が G2 と H2 を自分で走らせます（observe_diag.py・search_limits.json は H2 の対象です）。
3. 照合（verify_design_contract.py --diff）をかけます。照らしの道具（①②）・壊すプログラムを走らせ、全体の自己テスト（--selftest）を1回 走らせて、出力をそのまま貼ります（当てた直後の写しで、全部 通ることを確かめた）。
4. G-1：オン・オフの表を作り直し（11種が「使う」に入る）、型の表・出口の型の表（変わればまこさんに再承認していただく）・材料の文書・観察の説明書・組み立ての表を作り直します。そのあと資料の道具4本（list_on_families.py --add・make_param_table.py・extract_threshold_role_add.py --alias・build_role_threshold_table.py）を走らせ、修正対応表を作り直します。ここで照らしの①は0件、②は 4-0 の⑦の設定を写すまで食い違います（G-1 の試しで実測）。
5. 2つ目の工事：4-0 の⑦の設定を、資料から道具が写す案を出し、承認をいただいて当てます（照らしの②が0件になる）。
6. G-2：G2 → H2 を取り直し、監査に出す前のチェック（pre_audit_check.py --run）を走らせます。そのあと、2つの工事をまとめて実装の監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝出来高プロファイルの POC。今の材料 close vs POC%288 は、どの足でも直前288本（24時間）の終値と出来高で POC を作ります。夜中の0時をまたいでも、窓はずれていくだけです。この工事の後は、2つの版が増えます。close vs 前日POC% は、前の UTC の日の足ぜんぶで POC を作り、その日のあいだ線を動かしません（教科書の「前のセッションの値を後のセッションの参照にする」）。close vs 当日POC% は、その日の0時から1本前までの足で POC を作り、足が進むごとに育ちます。0時の最初の足は値がありません。どちらも区画24・同量なら価格の高い側という今の POC の決まり（_vp_one に切り出した）をそのまま使います。既知答えは、1日目に終値100 と200 の足を置き、2日目の足で POC が100 の区画に来るかを見ます。日の区切りを取り違えると、1日目の終値150 の足が混ざって答えが変わります。今の close vs POC%288 の値は1本も変わりません。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**この工事で探す範囲が変わるのは 3種類です（4-0 の④）。**足す11種は、名前に出る軸が無いか（10種）、今の VWAP と同じ1点の範囲（VWAP典型）で、その設定は2つ目の工事で写します（4-0 の⑦）。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**observe_config.json は、この工事では変えません**（今の資料から写し直しても同じ。足した種類の値を埋めない並びは、2つ目の工事で写す）。
**search_limits.json で変えるもの。**material_param_ranges を資料から写し直す（BB%b・BB幅・W字 の範囲）。
コマンドの旗は増やしません。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**
1. 観察の道具の全体の自己テストが通る（足した11種の既知答えと照合を含む）。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest。
2. 照らしの道具が、①②とも食い違い0件。コマンド＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources。
3. 壊すプログラムが、全部 決めた文で落ちる。コマンド＝python3 .claude/tools/run_breaks.py --design。
4. G2 と H2 が取り直される。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| --design の --dry で、当たらない件が出る | 1件も当てずに止まります。まこさんに報告します |
| 11種のどれかの作りが日・週の区切りを取り違える | 観察の道具の自己テストが「手計算の既知答えと不一致」を出して落ちます |
| 当日VWAP・VWAP典型 がライブラリの値と合わない | 観察の道具の自己テストが「2つ目の照合」「外部ライブラリ ta と不一致」を出して落ちます |
| 設定ファイルが、資料から写したものと違う | 照らしの道具が「②」で始まる行を出して落ちます |
| 11種が「使う」になったのに、資料に行が無い | 照らしの道具が「①」で始まる行を出して落ちます（資料の道具4本を G-1 の中で走らせる） |
| G-1 の後、2つ目の工事を当てる前に監査に出す前のチェックを走らせる | 照らしの道具が「②」で落ちます（2つ目の工事を当ててから走らせる＝4-4 の順） |
| 資料の行を作る前に、元にする種類の行が無い | 資料の道具が止まります（make_param_table.py・extract_threshold_role_add.py が「元にする種類の行が無い」で止まる） |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**変えません。**カタログの1件の形・参照表の欄・設定の欄の形は前の工事のままです。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**変えません。**

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**日と週の区切りは、データの時刻（UTC）で決めます。**日＝UTC の0時。週＝月曜0時 UTC に始まる7日（pandas の週の区切り W-SUN の始まり）。前日・前週は「データに在る1つ前の期間」です（今の前期間pivot と同じ）。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| 観察の道具の自己テスト（全体） | 130秒 | 写しで当てた後に走らせた実測（k3a_draft_build.py の [7]） |
| 軽い口（--selftest-catalog） | 9秒 | 写しで当てた後に走らせた実測（k3a_draft_build.py の [7]） |
| 材料の一覧 | 488 列 | 写しで数えた（k3a_draft_build.py の [3]） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**この工事の中ではありません。**全部を --design の1回で当てます。★この工事と2つ目の工事の間（G-1 の後）は、照らしの②が食い違う途中の状態です。その間に監査に出す前のチェックを走らせません（4-4 の順）。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しの道具だけが書きます。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**観察の道具の自己テストは、落ちたときだけ「手計算の既知答えと不一致」「2つ目の照合」で始まる行を出します。照らしの道具は、食い違いがあるときだけ「①」「②」で始まる行を出します。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **observe_diag.py・search_limits.json は H2 の対象です。**当てた後に G2 → H2 を取り直します。
2. **材料のカタログに 11 列が増えます（close vs VWAP典型%288・close vs 前日POC%・close vs 前日VAH%・close vs 前日VAL%・close vs 前週pivotPP%・close vs 前週pivotR1%・close vs 前週pivotS1%・close vs 当日POC%・close vs 当日VAH%・close vs 当日VAL%・close vs 当日VWAP%）。**型の表（signal_families）の部品も増える見込みで、まこさんの再承認が要ります（G-1）。
3. **成績表（material_ranking.json）には、増える列の行がありません。**作り直す（M2-D-8）まで、段の候補の順位に出ません。
4. **マイルストーンへの差し込み（作ってはいけないものとの照合）は変わりません**（写しで 0行の違い）。
5. **前からの壊すプログラムが探す文字の数は、当てる前と後で同じです。**道具が数えた相手は、下の囲みです。★2つ目の工事では、探す範囲の RCI の行の後ろに close vs VWAP典型 の行が来て、b143 が探す行の末尾に「,」が付きます（その工事で b143 も直す・k3a_oldbreak_check.py で写しの測り方を確かめた）。
```
b104_atr1h_own_tf.sh・b105_atr1h_future_hour.sh・b106_atr1h_no_clip.sh・b107_atr1h_base_not_passed.sh・b108_atr1h_base_wrong_bars.sh・b122_obs_formula_copied.sh・b126_rank_resume_save_off.sh・b128_k1_copc_back_in_ao_loop.sh・b129_htf_bar_close_two_bars.sh・b131_industry_map_prev_pivot_gone.sh・b132_hidden_param_not_passed.sh・b133_cksp_mixed_set.sh・b134_ao_name_with_value.sh・b135_rci_mako_gone.sh・b136_insp2_bar_close_dropped.sh・b137_material_params_ignored.sh・b138_keep_name_dropped.sh・b139_range_excludes_keep.sh・b140_group_range_ignored.sh・b141_catalog_out_of_range.sh・b143_rci_range_short.sh・b55_cyc_key_time_gone.sh・b56_one_min_csv_old.sh・b60_only5_with_others.sh・b61_insp5_bars_kind.sh・b63_tm_bitget_scope.sh・b64_tm_subdir.sh・b65_tm_badtail.sh
```

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| r5_draft_build.py・r3_draft_build.py（同じ日と前の日の工事の道具） | 指示を作る形・写しで確かめる形・壊し方を並べて走らせる形・資料から設定を作る写し方 |
| observe_diag.py の _vp_levels と _pivot_prev_period | 出来高プロファイルの決まり（区画24・70%・同量なら高い側）と、前の期間の区切り方（shift(1)） |
| indicator_reference_diag.py の _vp_case と _pivot_day_case | 既知答えの合成の足の形 |
| 壊すプログラム b142・b143 | 壊すプログラムの形 |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=0fdf27742f133dca gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 367〜391行（_vp_levels・監査 CP60 の修正42＝出来高プロファイルの1つの窓の計算を _vp_one に切り出し（計算は変えない）、日で区切る版 _vp_by_day を足す）
直す前の文字:
~~~
    poc, vah, val = [], [], []
    ca, va = c.to_numpy(), v.to_numpy()
    for i in range(len(ca)):
        if i < win:
            poc.append(np.nan); vah.append(np.nan); val.append(np.nan); continue
        cw, vw = ca[i - win:i], va[i - win:i]
        bins = np.linspace(cw.min(), cw.max(), rows + 1)
        idx = np.clip(np.digitize(cw, bins) - 1, 0, len(bins) - 2)
        agg = np.bincount(idx, weights=vw, minlength=len(bins) - 1)
        centers = (bins[:-1] + bins[1:]) / 2
        p = int(np.argsort(agg)[::-1][0])
        last = len(agg) - 1
        tot = max(agg.sum(), 1e-9)
        lo, hi, acc = p, p, agg[p]
        while acc / tot < va_pct and (lo > 0 or hi < last):
            up = agg[hi + 1] if hi < last else -1.0
            dn = agg[lo - 1] if lo > 0 else -1.0
            if up > dn or (up == dn and (hi + 1 - p) <= (p - lo + 1)):
                hi += 1
                acc += agg[hi]
            else:
                lo -= 1
                acc += agg[lo]
        poc.append(centers[p]); vah.append(centers[hi]); val.append(centers[lo])
    return (pd.Series(poc, index=c.index), pd.Series(vah, index=c.index), pd.Series(val, index=c.index))

~~~
直した後の文字:
~~~
    poc, vah, val = [], [], []
    ca, va = c.to_numpy(), v.to_numpy()
    for i in range(len(ca)):
        if i < win:
            poc.append(np.nan); vah.append(np.nan); val.append(np.nan); continue
        p_, h_, l_ = _vp_one(ca[i - win:i], va[i - win:i], va_pct, rows)
        poc.append(p_); vah.append(h_); val.append(l_)
    return (pd.Series(poc, index=c.index), pd.Series(vah, index=c.index), pd.Series(val, index=c.index))


def _vp_one(cw, vw, va_pct=0.7, rows=24):
    """1つの窓の出来高プロファイル＝(POC・VAH・VAL の価格)。決まりは _vp_levels の説明のとおり。
    ★2026-10-07（工事 m2c15-period-textbook-20261007）に _vp_levels の中から切り出した（計算は1文字も変えていない）。
      n 本の移動窓（_vp_levels）と、日で区切る版（_vp_by_day・監査 CP60 の修正42）が同じ決まりを使うため。"""
    bins = np.linspace(cw.min(), cw.max(), rows + 1)
    idx = np.clip(np.digitize(cw, bins) - 1, 0, len(bins) - 2)
    agg = np.bincount(idx, weights=vw, minlength=len(bins) - 1)
    centers = (bins[:-1] + bins[1:]) / 2
    p = int(np.argsort(agg)[::-1][0])
    last = len(agg) - 1
    tot = max(agg.sum(), 1e-9)
    lo, hi, acc = p, p, agg[p]
    while acc / tot < va_pct and (lo > 0 or hi < last):
        up = agg[hi + 1] if hi < last else -1.0
        dn = agg[lo - 1] if lo > 0 else -1.0
        if up > dn or (up == dn and (hi + 1 - p) <= (p - lo + 1)):
            hi += 1
            acc += agg[hi]
        else:
            lo -= 1
            acc += agg[lo]
    return centers[p], centers[hi], centers[lo]


def _vp_by_day(c, v, mode, va_pct=0.7, rows=24):
    """日で区切る出来高プロファイル（監査 CP60 の修正42 の比べる版・2026-10-07・工事 m2c15-period-textbook-20261007）。
    区切り＝UTC の日（データの時刻は UTC）。戻り＝(POC・VAH・VAL の価格の列)。決まり（区画・70%）は _vp_one。
    mode="前日"＝1つ前の日の足ぜんぶで作り、その日のあいだ動かない（監査 CP60 の修正42「前の UTC の日で固定（教科書の
      『前のセッションの値を後のセッションの参照にする』）」）。1つ前の日＝データに在る1つ前の日（_pivot_prev_period の
      shift(1) と同じ）。データの最初の日は NaN。
    mode="当日"＝その日の0時から、今の足の1本前までの足で作る（同「その日の0時から育つ版」）。今の足は窓に入れない
      （_vp_levels と同じ＝未来を見ない）。その日の最初の足は NaN。"""
    if mode not in ("前日", "当日"):
        raise ValueError(f"_vp_by_day の mode は 前日 か 当日（{mode}）")
    ca, va = c.to_numpy(float), v.to_numpy(float)
    dv = c.index.floor("D").to_numpy()
    out = np.full((3, len(ca)), np.nan)
    bounds, s = [], 0
    for i in range(1, len(ca) + 1):
        if i == len(ca) or dv[i] != dv[s]:
            bounds.append((s, i))
            s = i
    for k, (s, e) in enumerate(bounds):
        if mode == "前日":
            if k == 0:
                continue
            ps, pe = bounds[k - 1]
            out[:, s:e] = np.array(_vp_one(ca[ps:pe], va[ps:pe], va_pct, rows))[:, None]
        else:
            for i in range(s + 1, e):
                out[:, i] = _vp_one(ca[s:i], va[s:i], va_pct, rows)
    return tuple(pd.Series(out[j], index=c.index) for j in range(3))

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:367「poc, vah, val = [], [], []」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 891〜892行（<モジュール直下>・監査 CP60 の修正41 の (b)(c)＝典型価格の移動窓の VWAP と、UTC 0時から積み上げる VWAP を、今の版を残して足す）
直す前の文字:
~~~
_reg("close vs VWAP%", "close vs VWAP%{}", True, lambda d, n: (d.close / ((d.close * d.volume).rolling(n).sum()
     / d.volume.rolling(n).sum().replace(0, np.nan)) - 1) * 100)

~~~
直した後の文字:
~~~
_reg("close vs VWAP%", "close vs VWAP%{}", True, lambda d, n: (d.close / ((d.close * d.volume).rolling(n).sum()
     / d.volume.rolling(n).sum().replace(0, np.nan)) - 1) * 100)
# ★2026-10-07（工事 m2c15-period-textbook-20261007・監査 CP60 の修正41 の (b)(c)）＝教科書の VWAP（値段は典型価格）の2つの版を、
#   今の版（終値・n 本の移動窓）を残して別の材料として足す。どちらが良いかは M2-F-10f で比べる（この工事は材料を足すだけ）。
#   (b) 典型価格＝(高値＋安値＋終値)÷3 の n 本の移動窓＝ta の VolumeWeightedAveragePrice の作り
#   (c) UTC の日の0時から積み上げる典型価格＝StockCharts の逐語「VWAP calculations start fresh at the open」「(H+L+C)/3」
#       ＝pandas-ta の vwap（anchor の既定 D）の作り。今の足までを含む（今の版の移動窓も今の足を含む）。
def _vwap_day(d):
    """UTC の日の0時から積み上げる VWAP（値段は典型価格・今の足までを含む）。"""
    key = d.index.floor("D")
    tp = (d.high + d.low + d.close) / 3
    return (tp * d.volume).groupby(key).cumsum() / d.volume.groupby(key).cumsum().replace(0, np.nan)


_reg("close vs VWAP典型%", "close vs VWAP典型%{}", True, lambda d, n: (d.close / ((((d.high + d.low + d.close) / 3) * d.volume)
     .rolling(n).sum() / d.volume.rolling(n).sum().replace(0, np.nan)) - 1) * 100)
_reg("close vs 当日VWAP%", "close vs 当日VWAP%", True, lambda d: (d.close / _vwap_day(d) - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:891「_reg("close vs VWAP%", "close vs VWAP%{}", True, lambda d, n: (d.close / ((d.close * d.volume).rolling(n).sum()」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 913行（_pivot_prev_period・K-7 の決定＝前期間pivot の作りに「前の週」を選べる引数を足す（渡さなければ今までと同じ））
直す前の文字:
~~~
def _pivot_prev_period(d):

~~~
直した後の文字:
~~~
def _pivot_prev_period(d, unit=None):

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:913「def _pivot_prev_period(d):」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 918〜920行（_pivot_prev_period・K-7 の決定＝unit="W" のときは前の週（月曜0時 UTC 始まり）で区切る）
直す前の文字:
~~~
    step = pd.Series(d.index).diff().median()
    if pd.isna(step) or step < pd.Timedelta("1D"):
        key = d.index.floor("D")

~~~
直した後の文字:
~~~
    step = pd.Series(d.index).diff().median()
    # ★unit="W"（2026-10-07・工事 m2c15-period-textbook-20261007・K-7 の決定「前期間pivot の3種に前の週の版を別の材料として足す」）＝
    #   足の長さによらず、前の週（月曜0時 UTC に始まる7日）の高値・安値・終値で作る。StockCharts の逐語「Pivot Points for 30-, 60-,
    #   and 120-minute charts use the prior week's high, low, and close.」。週の始まりを月曜にしたのは ISO 8601 の週の決まり
    #   （出どころの逐語は無い＝設計書の「決めたこと」に書いた）。unit を渡さなければ今までと同じ（日中の足は前の日）。
    if unit == "W":
        key = d.index.to_period("W-SUN").to_timestamp()
    elif pd.isna(step) or step < pd.Timedelta("1D"):
        key = d.index.floor("D")

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:918「step = pd.Series(d.index).diff().median()」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 934行（<モジュール直下>・K-7 の決定＝前の週で固定する pivot の3種を、今の前の日の版を残して足す）
直す前の文字:
~~~
_reg("close vs 前期間pivotS1%", "close vs 前期間pivotS1%", True, lambda d: (d.close / _pivot_prev_period(d)[2] - 1) * 100)

~~~
直した後の文字:
~~~
_reg("close vs 前期間pivotS1%", "close vs 前期間pivotS1%", True, lambda d: (d.close / _pivot_prev_period(d)[2] - 1) * 100)
# ★2026-10-07（工事 m2c15-period-textbook-20261007・K-7 の決定）＝前の週で固定する版（今の前の日の版は残す）
_reg("close vs 前週pivotPP%", "close vs 前週pivotPP%", True, lambda d: (d.close / _pivot_prev_period(d, "W")[0] - 1) * 100)
_reg("close vs 前週pivotR1%", "close vs 前週pivotR1%", True, lambda d: (d.close / _pivot_prev_period(d, "W")[1] - 1) * 100)
_reg("close vs 前週pivotS1%", "close vs 前週pivotS1%", True, lambda d: (d.close / _pivot_prev_period(d, "W")[2] - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:934「_reg("close vs 前期間pivotS1%", "close vs 前期間pivotS1%", True, lambda d: (d.close / _pivot_prev_period(d)[2] - 1) * 100)」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 941〜942行（<モジュール直下>・監査 CP60 の修正42＝前の日で固定・その日の0時から育つ POC・VAH・VAL の6種を、今の版を残して足す）
直す前の文字:
~~~
_reg("close vs VAL%", "close vs VAL%{}", True, lambda d, n, va_pct=0.7, rows=24:
     (d.close / _vp_levels(d.close, d.volume, n, va_pct=va_pct, rows=rows)[2] - 1) * 100)

~~~
直した後の文字:
~~~
_reg("close vs VAL%", "close vs VAL%{}", True, lambda d, n, va_pct=0.7, rows=24:
     (d.close / _vp_levels(d.close, d.volume, n, va_pct=va_pct, rows=rows)[2] - 1) * 100)
# ★2026-10-07（工事 m2c15-period-textbook-20261007・監査 CP60 の修正42）＝出来高プロファイルを日で区切る2つの版を、
#   今の版（n 本の移動窓）を残して別の材料として足す。前日＝前の UTC の日で固定／当日＝その日の0時から育つ（_vp_by_day）。
#   区画の数・70% は今の版と同じ既定（名前に出さない引数）。POC は 70% を使わないので、今の POC と同じく区画の数だけを持つ。
_reg("close vs 前日POC%", "close vs 前日POC%", True, lambda d, rows=24:
     (d.close / _vp_by_day(d.close, d.volume, "前日", rows=rows)[0] - 1) * 100)
_reg("close vs 前日VAH%", "close vs 前日VAH%", True, lambda d, va_pct=0.7, rows=24:
     (d.close / _vp_by_day(d.close, d.volume, "前日", va_pct, rows)[1] - 1) * 100)
_reg("close vs 前日VAL%", "close vs 前日VAL%", True, lambda d, va_pct=0.7, rows=24:
     (d.close / _vp_by_day(d.close, d.volume, "前日", va_pct, rows)[2] - 1) * 100)
_reg("close vs 当日POC%", "close vs 当日POC%", True, lambda d, rows=24:
     (d.close / _vp_by_day(d.close, d.volume, "当日", rows=rows)[0] - 1) * 100)
_reg("close vs 当日VAH%", "close vs 当日VAH%", True, lambda d, va_pct=0.7, rows=24:
     (d.close / _vp_by_day(d.close, d.volume, "当日", va_pct, rows)[1] - 1) * 100)
_reg("close vs 当日VAL%", "close vs 当日VAL%", True, lambda d, va_pct=0.7, rows=24:
     (d.close / _vp_by_day(d.close, d.volume, "当日", va_pct, rows)[2] - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:941「_reg("close vs VAL%", "close vs VAL%{}", True, lambda d, n, va_pct=0.7, rows=24:」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1429〜1430行（build_catalog・足した VWAP の2種をカタログに入れる（典型価格の移動窓は今の VWAP と同じ窓の一覧で作る））
直す前の文字:
~~~
    for n in cfg["vwap_windows"]:
        addf("close vs VWAP%", n)

~~~
直した後の文字:
~~~
    for n in cfg["vwap_windows"]:
        addf("close vs VWAP%", n)
        addf("close vs VWAP典型%", n)         # 監査 CP60 の修正41 の (b)（2026-10-07）
    addf("close vs 当日VWAP%")                # 同 (c)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1429「for n in cfg["vwap_windows"]:」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1447行（build_catalog・足した前週pivot の3種をカタログに入れる）
直す前の文字:
~~~
    addf("close vs 前期間pivotS1%")

~~~
直した後の文字:
~~~
    addf("close vs 前期間pivotS1%")
    addf("close vs 前週pivotPP%")             # K-7 の決定＝前の週の版（2026-10-07）
    addf("close vs 前週pivotR1%")
    addf("close vs 前週pivotS1%")

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1447「addf("close vs 前期間pivotS1%")」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1450〜1453行（build_catalog・足した日で区切る出来高プロファイルの6種をカタログに入れる）
直す前の文字:
~~~
    for n in cfg["vp_windows"]:
        addf("close vs POC%", n)
        addf("close vs VAH%", n)
        addf("close vs VAL%", n)

~~~
直した後の文字:
~~~
    for n in cfg["vp_windows"]:
        addf("close vs POC%", n)
        addf("close vs VAH%", n)
        addf("close vs VAL%", n)
    # 監査 CP60 の修正42＝日で区切る2つの版（2026-10-07）
    addf("close vs 前日POC%")
    addf("close vs 前日VAH%")
    addf("close vs 前日VAL%")
    addf("close vs 当日POC%")
    addf("close vs 当日VAH%")
    addf("close vs 当日VAL%")

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1450「for n in cfg["vp_windows"]:」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 942行（_r・足す11種の「使う」の決定（まこさんの逐語のファイル）を、登録の mako の欄から1か所で引けるようにする）
直す前の文字:
~~~
def _r(pat, family, teigi, ryugi, houkou, prop, tb=None, ext=None, known=None, tol=1e-6, mako=None):

~~~
直した後の文字:
~~~
# ★まこさんの決定の逐語（2026-10-07・工事 m2c15-period-textbook-20261007）＝下の登録の mako の欄に書く（同じ文を11か所に書かないため）。
MAKO_K3 = '2026-10-07 まこさん決定「A」（K-3 を3つの工事に分け、K-3a で監査 CP60 の修正41 の (b)(c) と修正42 の比べる版を、今の版を残して別の材料として足す）＝逐語のファイル ok_k3_split_20261007（工事 m2c15-period-textbook-20261007）'
MAKO_K7 = '2026-10-07 まこさん決定「OK」（K-7 の1番＝前期間pivot の3種に前の週の版を別の材料として足す）＝逐語のファイル ok_k7_pivot_thermo_20261007（m2c15-memo-sort-20261007）'


def _r(pat, family, teigi, ryugi, houkou, prop, tb=None, ext=None, known=None, tol=1e-6, mako=None):

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:942「def _r(pat, family, teigi, ryugi, houkou, prop, tb=None, ext=None, known=None, tol=1e-6, mako=None):」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1226〜1227行（<モジュール直下>・監査 CP60 の修正41 の (b)(c)＝参照表に登録し、手計算の既知答え・教科書の独立実装・ta との照合を付ける）
直す前の文字:
~~~
   "順張り値", "trend", tb=_tb_vs_vwap,
   known=lambda p: [(_flat(p[0] + 10), [(-1, 0.0, 1e-9)])])

~~~
直した後の文字:
~~~
   "順張り値", "trend", tb=_tb_vs_vwap,
   known=lambda p: [(_flat(p[0] + 10), [(-1, 0.0, 1e-9)])])
# ★2026-10-07（工事 m2c15-period-textbook-20261007・監査 CP60 の修正41 の (b)(c)）＝教科書の VWAP（典型価格）の2つの版。
def _tb_vs_vwap_tp(d, p):
    n = p[0]
    o, h, l, c, v = _arr(d)
    tp = (h + l + c) / 3
    return _S((c / _div(_roll(tp * v, n, "sum"), _roll(v, n, "sum")) - 1) * 100, d)


def _tp_case(n):
    """VWAP典型 の手計算用。全部の足が 高値112・安値100・終値103・出来高1＝典型価格105 → VWAP 105 → 乖離%＝(103÷105−1)×100。
    終値で作る今の版なら VWAP 103 → 0（＝値段の違いを見分ける）。"""
    c = np.full(n, 103.0)
    return _mk(c, o=c, h=np.full(n, 112.0), l=np.full(n, 100.0))


def _vwap_day_case():
    """当日VWAP の手計算用。1日目（3/1・288本）＝終値150・出来高1（積み上げが日で区切れていなければ、ここが混ざる）。
    2日目＝1本目と2本目は 高値112・安値100・終値103（典型価格105）・出来高1、3本目は 高値＝安値＝終値＝99・出来高2。
    2本目の VWAP＝105 → (103÷105−1)×100。3本目の VWAP＝(105＋105＋99×2)÷4＝102 → (99÷102−1)×100。"""
    c = np.r_[np.full(288, 150.0), [103.0, 103.0, 99.0]]
    h = np.r_[np.full(288, 150.0), [112.0, 112.0, 99.0]]
    l = np.r_[np.full(288, 150.0), [100.0, 100.0, 99.0]]
    v = np.r_[np.full(288, 1.0), [1.0, 1.0, 2.0]]
    return _mk(c, o=c, h=h, l=l, v=v)


_r(r"close vs VWAP典型%(\d+)", "close vs VWAP典型",
   "典型価格（(高値＋安値＋終値)÷3）で作る n 本の移動 VWAP からの乖離%",
   "監査 CP60 の修正41 の (b)＝ta の VolumeWeightedAveragePrice の作り（n 本の移動窓＋典型価格）。今の close vs VWAP（終値）とは値段だけが違う",
   "順張り値", "trend", tb=_tb_vs_vwap_tp,
   ext=lambda d, p: (d.close / _ta.volume.VolumeWeightedAveragePrice(d.high, d.low, d.close, d.volume, window=int(p[0]))
                     .volume_weighted_average_price() - 1) * 100,
   known=lambda p: [(_flat(p[0] + 10), [(-1, 0.0, 1e-9)]), (_tp_case(p[0] + 10), [(-1, (103.0 / 105.0 - 1) * 100, 1e-9)])],
   mako=MAKO_K3)
_r(r"close vs 当日VWAP%", "当日VWAP",
   "UTC の日の0時から積み上げる VWAP（典型価格・今の足までを含む）からの乖離%",
   "監査 CP60 の修正41 の (c)＝StockCharts の逐語「VWAP calculations start fresh at the open」「(H+L+C)/3」。pandas-ta の vwap（anchor の既定 D）と同じ作り",
   "順張り値", "trend",
   known=lambda p: [(_vwap_day_case(), [(-2, (103.0 / 105.0 - 1) * 100, 1e-9), (-1, (99.0 / 102.0 - 1) * 100, 1e-9)])],
   mako=MAKO_K3)

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1226「"順張り値", "trend", tb=_tb_vs_vwap,」
状態: 確定

#### 実装 12
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1299〜1301行（<モジュール直下>・K-7 の決定＝前週pivot の3種を参照表に登録し、週と日を見分ける手計算の既知答えを付ける）
直す前の文字:
~~~
_r(r"close vs 前期間pivotS1%", "前期間pivotS1",
   "教科書の S1＝2×PP − 前の期間の高値 からの乖離%", "StockCharts の逐語「Support 1 (S1) = (P x 2) - High」",
   "順張り値", "trend", known=lambda p: [(_pivot_day_case(), [(-1, 5.0, 1e-9)])])

~~~
直した後の文字:
~~~
_r(r"close vs 前期間pivotS1%", "前期間pivotS1",
   "教科書の S1＝2×PP − 前の期間の高値 からの乖離%", "StockCharts の逐語「Support 1 (S1) = (P x 2) - High」",
   "順張り値", "trend", known=lambda p: [(_pivot_day_case(), [(-1, 5.0, 1e-9)])])


def _pivot_week_case():
    """前週ピボットの手計算用（2026-10-07）。データの始まり 2026-03-01 は日曜＝月曜0時 UTC に始まる週の最後の日。
    1日目（3/1・288本）＝終値105・高値110 が1本・安値100 が1本（_pivot_day_case と同じ）、2日目（3/2 月曜・288本）＝高値＝安値＝終値＝104、
    3日目（3/3）＝終値105 が3本。3日目の前週ピボット＝3/1 の週＝PP 105・R1 110・S1 100 → 乖離% 0・(105÷110−1)×100・5。
    前の日の版なら 3/2 の 104 で作る＝PP=R1=S1=104（＝週と日の取り違えを見分ける）。"""
    c = np.r_[np.full(288, 105.0), np.full(288, 104.0), np.full(3, 105.0)]
    h = c.copy()
    l = c.copy()
    h[100] = 110.0
    l[200] = 100.0
    return _mk(c, o=c, h=h, l=l)


_r(r"close vs 前週pivotPP%", "前週pivotPP",
   "教科書のピボット PP を前の週（月曜0時 UTC に始まる7日）の（高値＋安値＋終値）÷3 で作り、その週のあいだ動かない線からの乖離%",
   "StockCharts の逐語「Pivot Points for 30-, 60-, and 120-minute charts use the prior week's high, low, and close.」。週の始まりは ISO 8601 の月曜",
   "順張り値", "trend", known=lambda p: [(_pivot_week_case(), [(-1, 0.0, 1e-9)])], mako=MAKO_K7)
_r(r"close vs 前週pivotR1%", "前週pivotR1",
   "前の週の R1＝2×PP − 前の週の安値 からの乖離%", "StockCharts の逐語「Resistance 1 (R1) = (P x 2) - Low」",
   "順張り値", "trend", known=lambda p: [(_pivot_week_case(), [(-1, (105.0 / 110.0 - 1) * 100, 1e-9)])], mako=MAKO_K7)
_r(r"close vs 前週pivotS1%", "前週pivotS1",
   "前の週の S1＝2×PP − 前の週の高値 からの乖離%", "StockCharts の逐語「Support 1 (S1) = (P x 2) - High」",
   "順張り値", "trend", known=lambda p: [(_pivot_week_case(), [(-1, 5.0, 1e-9)])], mako=MAKO_K7)

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1299「_r(r"close vs 前期間pivotS1%", "前期間pivotS1",」
状態: 確定

#### 実装 13
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1320〜1325行（<モジュール直下>・監査 CP60 の修正42＝日で区切る POC・VAH・VAL の6種を参照表に登録し、日の区切りを見分ける手計算の既知答えを付ける）
直す前の文字:
~~~
_r(r"close vs VAL%(\d+)", "VAL",
   "バリューエリア下端からの乖離%", "Market Profile。25分割の近似",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 2),
   # 下端は どちらの場合も下の区画。
   known=lambda p: [(_vp_case(int(p[0]), 10, 1), [(-1, _VP_D_LO, 1e-9)]),
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_LO, 1e-9)])])

~~~
直した後の文字:
~~~
_r(r"close vs VAL%(\d+)", "VAL",
   "バリューエリア下端からの乖離%", "Market Profile。25分割の近似",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 2),
   # 下端は どちらの場合も下の区画。
   known=lambda p: [(_vp_case(int(p[0]), 10, 1), [(-1, _VP_D_LO, 1e-9)]),
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_LO, 1e-9)])])


# ★2026-10-07（工事 m2c15-period-textbook-20261007・監査 CP60 の修正42）＝日で区切る出来高プロファイルの2つの版。
def _vp_day_case(prev: bool, va, vb, n=20):
    """日で区切る出来高プロファイルの手計算用。_vp_case（終値 100 と 200 の2つだけ）を日の区切りに置く＝答えは _vp_case と同じ。
    prev=True（前日の版）＝1日目（3/1・288本）の前半144本＝終値100・出来高 va／後半144本＝終値200・出来高 vb、2日目＝終値100 が3本。
      2日目の線は1日目の足ぜんぶで作る（同じ日の足だけで作ると終値100 だけ＝乖離0 になり見分けられる）。
    prev=False（当日の版）＝1日目（288本）＝終値150・出来高1（日で区切れていなければ、出来高の多いこの値段が線になる）、
      2日目＝_vp_case(n, va, vb) と同じ n＋1本。2日目の最後の足の線は、2日目の0時から1本前までの n 本で作る。"""
    if prev:
        c = np.r_[np.full(144, 100.0), np.full(144, 200.0), np.full(3, 100.0)]
        v = np.r_[np.full(144, float(va)), np.full(144, float(vb)), np.full(3, 1.0)]
        return _mk(c, o=c, h=c, l=c, v=v)
    m = n // 2
    c = np.r_[np.full(288, 150.0), np.full(m, 100.0), np.full(n - m, 200.0), [100.0]]
    v = np.r_[np.full(288, 1.0), np.full(m, float(va)), np.full(n - m, float(vb)), [1.0]]
    return _mk(c, o=c, h=c, l=c, v=v)


for _vpk, _vpw in (("前日", True), ("当日", False)):
    _r(rf"close vs {_vpk}POC%", f"{_vpk}POC",
       f"出来高プロファイルの最厚価格帯 POC（{'前の UTC の日の足ぜんぶ・その日のあいだ固定' if _vpw else 'その日の0時から1本前までの足'}）からの乖離%",
       "監査 CP60 の修正42 の比べる版。区画24・同量なら価格の高い側（今の POC と同じ決まり＝_vp_one）",
       "順張り値", "trend",
       known=lambda p, w=_vpw: [(_vp_day_case(w, 10, 1), [(-1, _VP_D_LO, 1e-9)]), (_vp_day_case(w, 6, 4), [(-1, _VP_D_LO, 1e-9)])],
       mako=MAKO_K3)
    _r(rf"close vs {_vpk}VAH%", f"{_vpk}VAH",
       f"バリューエリア上端（出来高上位70%帯の上端・{'前の UTC の日' if _vpw else 'その日の0時から1本前まで'}）からの乖離%",
       "監査 CP60 の修正42 の比べる版。今の VAH と同じ決まり（_vp_one）",
       "順張り値", "trend",
       known=lambda p, w=_vpw: [(_vp_day_case(w, 10, 1), [(-1, _VP_D_LO, 1e-9)]), (_vp_day_case(w, 6, 4), [(-1, _VP_D_HI, 1e-9)])],
       mako=MAKO_K3)
    _r(rf"close vs {_vpk}VAL%", f"{_vpk}VAL",
       f"バリューエリア下端（{'前の UTC の日' if _vpw else 'その日の0時から1本前まで'}）からの乖離%",
       "監査 CP60 の修正42 の比べる版。今の VAL と同じ決まり（_vp_one）",
       "順張り値", "trend",
       known=lambda p, w=_vpw: [(_vp_day_case(w, 10, 1), [(-1, _VP_D_LO, 1e-9)]), (_vp_day_case(w, 6, 4), [(-1, _VP_D_LO, 1e-9)])],
       mako=MAKO_K3)

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1320「_r(r"close vs VAL%(\d+)", "VAL",」
状態: 確定

#### 実装 14
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4604行（<モジュール直下>・足す11種の系統（構造・位置）を書く）
直す前の文字:
~~~
    "VAL": dict(k="構造・位置"), "S-Rタッチ数": dict(k="構造・位置"),

~~~
直した後の文字:
~~~
    "VAL": dict(k="構造・位置"), "S-Rタッチ数": dict(k="構造・位置"),
    # ★2026-10-07（工事 m2c15-period-textbook-20261007）＝教科書の期間の区切りの版（監査 CP60 の修正41・42・K-7 の決定）
    "close vs VWAP典型": dict(k="構造・位置"), "当日VWAP": dict(k="構造・位置"),
    "前週pivotPP": dict(k="構造・位置"), "前週pivotR1": dict(k="構造・位置"), "前週pivotS1": dict(k="構造・位置"),
    "前日POC": dict(k="構造・位置"), "前日VAH": dict(k="構造・位置"), "前日VAL": dict(k="構造・位置"),
    "当日POC": dict(k="構造・位置"), "当日VAH": dict(k="構造・位置"), "当日VAL": dict(k="構造・位置"),

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:4604「"VAL": dict(k="構造・位置"), "S-Rタッチ数": dict(k="構造・位置"),」
状態: 確定

#### 実装 15
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4914行（<モジュール直下>・足す11種の業界のライブラリとの対応を書く（観察の道具の検査10 が全部の種類に求める））
直す前の文字:
~~~
    "VAL": (("vp",), "同上"),

~~~
直した後の文字:
~~~
    "VAL": (("vp",), "同上"),
    # ★2026-10-07（工事 m2c15-period-textbook-20261007）＝教科書の期間の区切りの版
    "close vs VWAP典型": ((), "ta の VolumeWeightedAveragePrice（n 本の移動窓＋典型価格）と同じ作り（定義表の外部照合で確かめる）。pandas-ta の vwap は日の始まりから積み上げる版＝当日VWAP"),
    "当日VWAP": (("vwap",), "pandas-ta の vwap（anchor の既定 D＝日の始まりから積み上げる典型価格・overlap/vwap.py）。定義表の2つ目の照合で値を確かめる"),
    "前週pivotPP": ((), "前の週で固定する教科書の PP。ライブラリの cpr と同じ作りかは照らしていない（定義表の既知答えで確かめる）"),
    "前週pivotR1": ((), "同上（教科書の R1＝2×PP − 前の週の安値）"),
    "前週pivotS1": ((), "同上（教科書の S1＝2×PP − 前の週の高値）"),
    "前日POC": (("vp",), "vp の作りを前の UTC の日で区切ったもの。日で区切る形はライブラリと照らしていない（定義表の既知答えで確かめる）"),
    "前日VAH": (("vp",), "同上"),
    "前日VAL": (("vp",), "同上"),
    "当日POC": (("vp",), "vp の作りを、その日の0時から1本前までで区切ったもの。日で区切る形はライブラリと照らしていない（定義表の既知答えで確かめる）"),
    "当日VAH": (("vp",), "同上"),
    "当日VAL": (("vp",), "同上"),

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:4914「"VAL": (("vp",), "同上"),」
状態: 確定

#### 実装 16
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 929〜930行（<モジュール直下>・当日VWAP を pandas-ta の vwap と値で照らす（2つ目の照合））
直す前の文字:
~~~
    "RCI": (_x2_rci, "scipy"),
}

~~~
直した後の文字:
~~~
    "RCI": (_x2_rci, "scipy"),
    # ★2026-10-07（工事 m2c15-period-textbook-20261007）＝当日VWAP は pandas-ta の vwap（anchor="D"）と同じ作り
    "当日VWAP": (lambda d, p: (d.close / _pta.vwap(d.high, d.low, d.close, d.volume, anchor="D") - 1) * 100, "pandas-ta"),
}

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:929「"RCI": (_x2_rci, "scipy"),」
状態: 確定

#### 実装 17
対象のファイル: .claude/memory/regime_detection_kb.md
直す箇所: 1290〜1295行（文書・足す11種で材料の種類と一覧の行の数が変わる＝KB の件数の囲み（gen_materials.py --write が書き出す所）を、写しで数えた文に置き換える（材料の文書の自己テストの B3・B4 と承認の前の検査 A12 が見る））
直す前の文字:
~~~
<!-- COUNTS_START gen_materials.py --write が実物から書き出す＝手で書き換えない -->
| 5 | 指標の種類 | **261種類**（engine_tuner が選べる **143**／選べない **118**） | materials.md の「engine_tuner が選べる指標の種類」の行 |
| 6 | 材料の一覧の行 | **266件**（在る。ほかに「入れない」45件） | materials.md の一覧 |
| 7 | パラメータまで展開した部品 | **477件**（＋別枠 7件＝**484**） | signal_families.json の parts と extra_parts |
| 8 | ★484 に膨らむ理由 | ADX7・ADX14・ADX21 のように、同じ指標のパラメータ違いを別々に数えているため | 部品の名前の実測 |
<!-- COUNTS_END -->
~~~
直した後の文字:
~~~
<!-- COUNTS_START gen_materials.py --write が実物から書き出す＝手で書き換えない -->
| 5 | 指標の種類 | **272種類**（engine_tuner が選べる **143**／選べない **129**） | materials.md の「engine_tuner が選べる指標の種類」の行 |
| 6 | 材料の一覧の行 | **277件**（在る。ほかに「入れない」45件） | materials.md の一覧 |
| 7 | パラメータまで展開した部品 | **477件**（＋別枠 7件＝**484**） | signal_families.json の parts と extra_parts |
| 8 | ★484 に膨らむ理由 | ADX7・ADX14・ADX21 のように、同じ指標のパラメータ違いを別々に数えているため | 部品の名前の実測 |
<!-- COUNTS_END -->
~~~
根拠の抜き書き: .claude/memory/regime_detection_kb.md:1290「<!-- COUNTS_START gen_materials.py --write が実物から書き出す＝手で書き換えない -->」
状態: 確定

#### 実装 18
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 77行（設定・資料の範囲の直し（BB%b・BB幅・W字＝まこさん「OK」）を、探す範囲に道具が写し直す（照らしの道具の②が見る中身））
直す前の文字:
~~~
    "BB%b": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}],

~~~
直した後の文字:
~~~
    "BB%b": [{"kind": "int", "lo": 10, "hi": 50}, {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}],

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:77「"BB%b": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}],」
状態: 確定

#### 実装 19
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 91行（設定・資料の範囲の直し（BB%b・BB幅・W字＝まこさん「OK」）を、探す範囲に道具が写し直す（照らしの道具の②が見る中身））
直す前の文字:
~~~
    "BB幅": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}],

~~~
直した後の文字:
~~~
    "BB幅": [{"kind": "int", "lo": 10, "hi": 50}, {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}],

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:91「"BB幅": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}],」
状態: 確定

#### 実装 20
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 104行（設定・資料の範囲の直し（BB%b・BB幅・W字＝まこさん「OK」）を、探す範囲に道具が写し直す（照らしの道具の②が見る中身））
直す前の文字:
~~~
    "W字": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.003, "hi": 0.003, "dec": 3}],

~~~
直した後の文字:
~~~
    "W字": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.0, "hi": 0.06, "dec": 3}],

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:104「"W字": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.003, "hi": 0.003, "dec": 3}],」
状態: 確定

#### 実装 21
対象のファイル: .claude/breaks/b145_vwap_day_no_reset.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 当日VWAP の積み上げを日で区切らない形に戻すと、観察の道具の自己テスト（参照表の手計算の既知答え）が落ちる
# EXPECT_MSG: close vs 当日VWAP%: 手計算の既知答えと不一致
# b145_vwap_day_no_reset — 当日VWAP の積み上げを日で区切らない形に戻すと、観察の道具の自己テスト（参照表の手計算の既知答え）が落ちる（工事 m2c15-period-textbook-20261007・2026-10-07）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3a_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「close vs 当日VWAP%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    return (tp * d.volume).groupby(key).cumsum() / d.volume.groupby(key).cumsum().replace(0, np.nan)\n'
new = '    return (tp * d.volume).cumsum() / d.volume.cumsum().replace(0, np.nan)\n'
if s.count(old) != 1:
    raise SystemExit("[b145_vwap_day_no_reset] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 22
対象のファイル: .claude/breaks/b146_pivot_week_as_day.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 前週pivot を前の日で作る形に戻すと、観察の道具の自己テスト（参照表の手計算の既知答え）が落ちる
# EXPECT_MSG: close vs 前週pivotR1%: 手計算の既知答えと不一致
# b146_pivot_week_as_day — 前週pivot を前の日で作る形に戻すと、観察の道具の自己テスト（参照表の手計算の既知答え）が落ちる（工事 m2c15-period-textbook-20261007・2026-10-07）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3a_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「close vs 前週pivotR1%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    if unit == "W":\n'
new = '    if unit == "W" and False:\n'
if s.count(old) != 1:
    raise SystemExit("[b146_pivot_week_as_day] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 23
対象のファイル: .claude/breaks/b147_vp_today_from_start.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 当日の出来高プロファイルを、その日の0時でなくデータの始まりから作る形に戻すと、観察の道具の自己テスト（手計算の既知答え）が落ちる
# EXPECT_MSG: close vs 当日POC%: 手計算の既知答えと不一致
# b147_vp_today_from_start — 当日の出来高プロファイルを、その日の0時でなくデータの始まりから作る形に戻すと、観察の道具の自己テスト（手計算の既知答え）が落ちる（工事 m2c15-period-textbook-20261007・2026-10-07）
#   守っているもの＝完成の条件の全体の自己テスト（observe_diag.py --selftest）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k3a_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest が「close vs 当日POC%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '                out[:, i] = _vp_one(ca[s:i], va[s:i], va_pct, rows)\n'
new = '                out[:, i] = _vp_one(ca[:i], va[:i], va_pct, rows)\n'
if s.count(old) != 1:
    raise SystemExit("[b147_vp_today_from_start] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 24
対象のファイル: .claude/breaks/b148_bb_range_not_widened.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: BB%b の範囲を直す前（本数 20〜50・倍率 2.0〜2.0）に戻すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②search_limits.json
# b148_bb_range_not_widened — BB%b の範囲を直す前（本数 20〜50・倍率 2.0〜2.0）に戻すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-period-textbook-20261007・2026-10-07）
#   守っているもの＝完成の条件の照らしの道具（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources）
#   壊し方＝scripts/priority_rebuild/recipes/search_limits.json の中の、下の old を new に置き換える（k3a_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources が「❌ ②search_limits.json」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/recipes/search_limits.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "BB%b": [{"kind": "int", "lo": 10, "hi": 50}, {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}],\n'
new = '    "BB%b": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}],\n'
if s.count(old) != 1:
    raise SystemExit("[b148_bb_range_not_widened] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 24 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 出来高プロファイルの1つの窓の計算を _vp_one に切り出し、今の版と日で区切る版の両方が使う | 同じ決まりを2か所に書かない。今の列の値が変わらないことは写しで確かめた（0本の違い） | 日で区切る版に同じ計算をもう1つ書く |
| 2 | 11種の資料の行は、対応表（research/alias_map.json・封つき）から道具が作る | まこさん「B」。新しく調べない。同じ指標の調べた結果と照らした印を、そのまま使う | 調べる係を走らせる（まこさん「A」の案） |
| 3 | 資料の行を作るのは、11種が「使う」に入った後（G-1 の中） | 「使う」に入る前に行を作ると、照らしの道具の①が「行が在るのに使うでない」で止め、設計書も作れない | 設計書の前に資料の行を足す |
| 4 | 範囲の直しは、資料の道具（apply_param_rule.py）が k7_range_fix.json を教科書の範囲として読む | 設定ファイルに直接 書くと照らしの②が落ちる。軸の番号の取り違えは、直す前の範囲（「今」の欄）と照らして止める | 設定ファイルに手で書く |
| 5 | 11種の「使う」は、参照表の mako の欄（まこさんの決定の逐語）で付ける | オン・オフの表の道具が機械で読む4つ目の源。ta のクラスの対応を変えると、ほかの種類の印も作り直しになる | ta のクラスの対応（TA_CLASS_MAP）を変える |
| 6 | 知識の文書の件数の囲みを、この工事の指示に入れる | 材料の種類が増えると、材料の文書の自己テストの B3・B4 が「素の状態で verify が鳴っている」で落ちる（写しで実測）。承認の前の検査 A12 が許すのは T6 だけ。囲みは gen_materials.py --write が書き出す所で、数えた文をそのまま写すので CC は数字を書かない。G-1 で gen_materials.py --write がもう一度 書き出す | A12 の許しに B3・B4 を足す（承認の前の検査＝守りの hook の直しになる） |
| 7 | 壊すプログラムの3本は、観察の道具の全体の自己テストで測る | 既知答えの照らしは全体の自己テストの中に在る（軽い口には無い） | 軽い口で測る |
| 8 | この工事（コードと範囲の直し）と、G-1 の後の2つ目の工事（11種の設定を写す）に分ける | 承認の前の検査 A12 は、指示だけを当てた状態で完成の条件と壊すプログラムを測る。11種はオン・オフの表を作り直す（G-1）まで「使う」でなく資料の行も無いので、11種の設定を同じ工事に入れると、当てた直後に照らしの①②と壊し方が狙いまで届かない（写しで実測）。分ければ、どちらの工事も当てた直後に全部 通る | 道具が作るはずのオン・オフの表と資料の表（json と md）まで指示に入れて1回で当てる（写しで数えた違い 約2,200行。G-1 で道具が作り直す中身を、手順の外で先に書くことになる） |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=40654d8d4f46bb1e gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b145_vwap_day_no_reset.sh` | #1 | 積み上げを日で区切らない形に戻す |
| `b146_pivot_week_as_day.sh` | #2 | 前の週の区切りを外し、前の日で作る形に戻す |
| `b147_vp_today_from_start.sh` | #3 | 窓の始まりを、その日の0時でなくデータの始まりにする |
| `b148_bb_range_not_widened.sh` | #4 | BB%b の範囲を直す前（本数 20〜50・倍率 2.0〜2.0）に戻す |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 型の表が変わる | G-1 で作り直し、まこさんに再承認していただく（4-4 の4） |
| 2 | 週の始まり（月曜）に出どころの逐語が無い | 3-2 で決めていただく。日曜始まりにするなら、_pivot_prev_period の W-SUN を W-SAT に変える1か所と、既知答えの合成の足を直す |
| 3 | 当日の出来高プロファイルは、その日の最初の足に値が無い | 今の版の最初の288本と同じ扱い（NaN）。engine_tuner は値の無い足を条件の外にする |
| 4 | 全体の自己テストが重くなる | 写しの実測 130秒（4-14） |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（--design） | 1分未満 | 同じ日の前の工事で、当てる道具は1秒未満で終わった |
| 全体の自己テスト | 130秒 | 4-14 |
| 壊すプログラム | 1本あたり約 130秒（全体の自己テスト）×3本と、照らしの道具の1本 | 写しで壊し方を並べて走らせた（k3a_draft_build.py の [8]） |
| G-1 の表の作り直しと資料の道具4本 | 約2分 | 写しの実測（オン・オフの表 約20秒・資料の道具4本 約10秒）と前の工事の実測 |
| 監査に出す前のチェック | 約10分 | 前の工事の実測（pre_audit_check.py --run） |
| まこさんの承認 | この工事の設計書1回・型の表の再承認1回（変われば）・2つ目の工事の設計書1回 | 4-4 |
| 2つ目の工事 | 時間は測っていない。流れは158回目の同じ形の工事（資料に足した4種を設定に写す・r5_draft_build.py）と同じ（案 → OK → 設計書 → 承認 → 当てる） | worklog 20261007 §11〜§13 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝今の VWAP・出来高プロファイル・前期間pivot は、24時間市場向けに移動窓や前の日で作った（参照表の流儀の欄に「本プロジェクトの流儀」と書いてある）。教科書の版が無いので、どちらが良いかを比べられなかった。この工事で教科書の版を足し、M2-F-10f で比べられるようにする。範囲は、資料の選び方が教科書の範囲の文（BB の (10,1.9)〜(50,2.1)・W字 の 0%〜6%）を読めず、1点のままだった。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。M2-F で使える材料が11種 増え、BB と W字 の探す範囲が教科書の値に届きます。

**③ root か symptom か**＝root です。比べる相手（教科書の版）が無いことが原因で、それを足します。範囲は、資料の道具が教科書の範囲として読む形にしたので、資料を作り直しても戻りません。

**④ ベースアップ**＝11種の作りは、資料の逐語（StockCharts・TradingView）と監査 CP60 の修正41・42 の本文から取った。当日VWAP は pandas-ta の vwap のソース（overlap/vwap.py:32・38・46）を開いて、同じ作りであることを確かめ、値で照らす。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。範囲は資料から道具が写しました。既知答えは合成の足から手で計算できる値です。壊し方の値も、今の設定の行から道具が取りました。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝教科書の期間の区切りの版を別の材料として足し、範囲の直しを写す（K-3a の1つ目の工事。11種の設定を写すのは G-1 の後の2つ目の工事）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。条件をつなぐものではなく、教科書の作りの材料を足すだけです |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | BB と W字 の範囲を広げ、点の一覧で限定する所を減らします。範囲の数字は資料から道具が写しました |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **既知答えが、本物の値動きでの正しさまで見るか** | 見ません。合成の足で、日・週の区切りと決まりを見るだけです。当日VWAP と VWAP典型 は、ライブラリと実際の値動きで照らします |
| **週の始まりが正しいか** | 見ません。出どころの逐語が無いので、3-2 でまこさんに決めていただきます |
| **資料の値そのものが正しいかを、照らしの道具が見るか** | 見ません。照らしの道具は、資料と設定ファイルが同じかだけを見ます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=ad865df76affa88a gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝observe_diag.py・indicator_reference_diag.py・search_limits.json・regime_detection_kb.md（件数の囲み）と、新しい壊すプログラムを【7-8】に書いた。主なファイルは observe_diag.py（材料の計算）。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝observe_diag.py・触る関数は道具が構文木の差から数えた）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム（NEW_FILE）。手本は b142（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝資料を作った後に指標を「使う」にして、資料に行が無いまま気づかなかった（158回目）。この工事は、資料の行を「使う」に入った後に道具で作る順を 4-4 に書き、照らしの道具の①で見る。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 新しい部品は、未来を見ない形にした（前日・前週は閉じた期間・当日の出来高プロファイルは1本前まで・当日VWAP は今の足まで）。当てた後に H2 を取り直す。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 行番号を指す文書は、当てた後に動く（observe_diag.py・indicator_reference_diag.py に行が増える）。設計書の行番号は当てる前の実物のもの。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、探す文字の数が当てる前と後で同じことを道具が数えた（4-13 の5）。走らせるコマンドの旗は変えない。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムが測るのは、観察の道具の全体の自己テストと照らしの道具の口で、どちらも本物の結果の置き場には書かない。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 触る関数（DESIGN_CONTRACT の impl_functions・道具が書いた）＝observe_diag.py：<モジュール直下>・_pivot_prev_period・_vp_by_day・_vp_levels・_vp_one・_vwap_day・build_catalog／indicator_reference_diag.py：<モジュール直下>・_pivot_week_case・_tb_vs_vwap_tp・_tp_case・_vp_day_case・_vwap_day_case。self_check_calls と must_use の名前は、当てた後の構文木に在ることを道具が ast で照らした。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足すコマンドの旗は無い。資料の道具の旗（--alias）は .claude/state の道具の側で、設計書の前に足した。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2c15-period-textbook-20261007）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝観察の道具の既知答え・ライブラリとの照合・照らしの道具の①②と、壊すプログラム（わざと壊して落ちるか）。写しで走らせ、全部 通った。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | F-1・F-2＝当日VWAP が UTC の日で区切って積み上がる（既知答えが通る） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | 積み上げを日で区切らない形に戻す | `b145_vwap_day_no_reset.sh` | — | **未着手** |
| 2 | F-1・F-2＝前週pivot が前の週で作られる（既知答えが通る） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | 前の週の区切りを外し、前の日で作る形に戻す | `b146_pivot_week_as_day.sh` | — | **未着手** |
| 3 | F-1・F-2＝当日の出来高プロファイルが、その日の0時から作られる（既知答えが通る） | `python3 scripts/priority_rebuild/observe_diag.py --selftest` | 実経路 | 窓の始まりを、その日の0時でなくデータの始まりにする | `b147_vp_today_from_start.sh` | — | **未着手** |
| 4 | F-3＝範囲の直しが設定に写り、設定ファイルが資料から写したものと同じ（照らしの①②が食い違い0件） | `python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources` | 実経路 | BB%b の範囲を直す前（本数 20〜50・倍率 2.0〜2.0）に戻す | `b148_bb_range_not_widened.sh` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=4f9f7bd33c3f056b gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/observe_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `_vp_one` | （この関数は実物に無い） |
| `_vp_by_day` | （この関数は実物に無い） |
| `_vwap_day` | （この関数は実物に無い） |
| `_pivot_prev_period` | 913 |
| `build_catalog` | 1319 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 180件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=181dce2f927c77ee gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/observe_diag.py",
  "_impl_file の意味": "照らす相手は実在するファイル。足す11種の計算（_vp_one・_vp_by_day・_vwap_day・_pivot_prev_period）とカタログ（build_catalog）が在る、観察の道具を照らす。",
  "impl_functions": {
    "scripts/priority_rebuild/observe_diag.py": [
      "<モジュール直下>",
      "_pivot_prev_period",
      "_vp_by_day",
      "_vp_levels",
      "_vp_one",
      "_vwap_day",
      "build_catalog"
    ],
    "scripts/priority_rebuild/indicator_reference_diag.py": [
      "<モジュール直下>",
      "_pivot_week_case",
      "_tb_vs_vwap_tp",
      "_tp_case",
      "_vp_day_case",
      "_vwap_day_case"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数（実装の指示を全部 当てる前と後の構文木を関数ごとに比べて、k3a_proposal_build.py が数えた）。",
  "self_check_calls": [
    "_vp_one",
    "_vp_by_day",
    "_vwap_day",
    "_pivot_prev_period",
    "build_catalog"
  ],
  "_self_check_calls の意味": "実装の後の observe_diag.py に在るはずの、この工事が足す・直す関数の名前。",
  "must_use": {
    "_vp_levels": [
      "_vp_one"
    ],
    "_vp_by_day": [
      "_vp_one"
    ]
  },
  "_must_use の意味": "出来高プロファイルの今の版（_vp_levels）と日で区切る版（_vp_by_day）が、同じ1つの窓の計算（_vp_one）を呼ぶ（k3a_proposal_build.py が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は、材料を足し、設定の値を資料から写し直すだけ。外から読む一覧の形（カタログの1件の形・参照表の欄・設定の欄）は変えない。",
  "generated_from": {
    "impl_functions": "当てる前と後の関数ごとの構文木の差（k3a_proposal_build.py が数えた）",
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

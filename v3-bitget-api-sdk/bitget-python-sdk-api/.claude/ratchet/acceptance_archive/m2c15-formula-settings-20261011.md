<!-- ARC iter="m2c15-formula-settings-20261011" -->

# 設計書｜K-3c の2つ目の工事＝1つ目の工事で「使う」に入った15種の設定を、資料から observe_config.json と search_limits.json に写す。M2-C-15

TARGET: scripts/priority_rebuild/observe_config.json, scripts/priority_rebuild/recipes/search_limits.json, .claude/breaks/b142_rci_list_stale.sh, .claude/breaks/b149_pending_not_copied.sh, .claude/breaks/b158_shape_ranges_missing.sh, .claude/breaks/b167_formula_params_missing.sh, .claude/breaks/b168_formula_hidden_missing.sh, .claude/breaks/b169_formula_ranges_missing.sh, .claude/breaks/b170_alias_axis_list_dropped.sh, .claude/breaks/b171_alias_axis_range_dropped.sh
NEW_FILE: .claude/breaks/b167_formula_params_missing.sh, .claude/breaks/b168_formula_hidden_missing.sh, .claude/breaks/b169_formula_ranges_missing.sh, .claude/breaks/b170_alias_axis_list_dropped.sh, .claude/breaks/b171_alias_axis_range_dropped.sh
MODEL: .claude/breaks/b149_pending_not_copied.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2c15-formula-settings-20261011/ok_k3cs_axis_20261011`・`m2c15-formula-settings-20261011/ok_k3cs_proposal_20261011`・`m2c15-formula-settings-20261011/ok_k3csplit_20261011`・`m2c15-formula-settings-20261011/okd_k3cs_proposal_20261011`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2c15-formula-settings-20261011/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-formula-settings-20261011 --write`。検出＝`--work m2c15-formula-settings-20261011 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=ab2e7355e4f29284 gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2c15-formula-settings-20261011/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2c15-formula-settings-20261011/ok_k3cs_axis_20261011.txt`（まこさんの発言）・`verbatim/m2c15-formula-settings-20261011/ok_k3cs_proposal_20261011.txt`（まこさんの発言）・`verbatim/m2c15-formula-settings-20261011/ok_k3csplit_20261011.txt`（まこさんの発言）・`verbatim/m2c15-formula-settings-20261011/okd_k3cs_proposal_20261011.txt`（まこさんが OK した CC の文）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝433 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_k3cs_axis_20261011` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_k3cs_proposal_20261011` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_k3csplit_20261011` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_k3cs_proposal_20261011` | V01〜V07（7 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_k3cs_proposal_20261011` | V08〜V74（67 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V75〜V81（7 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V82〜V86（5 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V87〜V95（9 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V96〜V101（6 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V102〜V109（8 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V110〜V119（10 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V120〜V121（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V122〜V123（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V124〜V127（4 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V128〜V129（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V130〜V131（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V132〜V137（6 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V138〜V147（10 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V148〜V153（6 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V154〜V155（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V156〜V157（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V158〜V159（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V160〜V165（6 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V166〜V290（125 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V291〜V299（9 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V300〜V306（7 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V307〜V316（10 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V317〜V323（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V324〜V325（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V326〜V327（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V328〜V332（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V333〜V342（10 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V343〜V363（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V364〜V374（11 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V375〜V426（52 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_k3cs_proposal_20261011` | V427〜V430（4 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
K-3c の1つ目の工事（m2c15-formula-textbook-20261011）で、計算式が教科書と違う種類に教科書の版を足し、G-1 で「使う」の表と資料の表3つを作り直しました。資料が変わったので、照らしのプログラムの②が、設定ファイル2本（observe_config.json・search_limits.json）と資料の食い違いを出しています。これは1つ目の工事の設計書に書いた見込みどおりで、まこさんが OK した分け方（コードの工事と、G-1 の後に設定を写す工事）の後半が、この工事です。StochRSI素%K と close vs SSF平均% は、まこさんの決定「Bで進めてよい」のとおり、元の種類と同じ扱いで写します。そのために、写し方のプログラムの対応表が、対応表の元の種類の軸の対応を引く形に、案の前に直しました。指標ごとの一覧に行が入った種類は、ほかの指標の期間を借りて作っていた列が消え、資料の最初の値（最初の段階で使う代表の値）の列になります。だから、この工事では材料の列が変わります。探す範囲には、最後の段階で探す、指標ごとに1つの範囲が入ります。設定の行が変わると、前からの壊すプログラム b142・b149・b158 が探す行も変わるので、3本を同じ形に直します。コードは1行も変えません。この工事の後、1つ目の工事とこの工事を、工事ごとに1通ずつ実装の監査に出します。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 指標ごとの一覧の StochRSI素%K（F-1・F-3） | `grep -n -F '"StochRSI素%K": [[14]]' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json` | 実装の前は、無い。実装の後は、指標ごとの一覧の中に在る（元の種類と同じ値） | （終了コード 1） |
| 探す範囲の close vs SSF平均%（F-2・F-3） | `grep -n -F '"close vs SSF平均%": [{"kind": "int", "lo": 10, "hi": 200}]' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json` | 実装の前は、無い。実装の後は、探す範囲の中に在る（元の種類と同じ範囲） | （終了コード 1） |
| 前からの壊すプログラムの探す行（F-4） | `grep -n -F '[52]],\n' .claude/breaks/b142_rci_list_stale.sh` | 実装の前は、無い（末尾に「,」の無い行が在る）。実装の後は、old の行に在る | （終了コード 1） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

［自動］印のファイル・型の表・格子と範囲
<!-- ACC_MATERIALS_START hash=7da7b45888427421 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`indicator_switch.json`・`signal_families.json`・`search_limits.json`。

**探す指標＝印がオンの 175種**（印を切り替えると、この一覧も設計も変わります）。

```
ADX・DI差・MACD線%・MACDヒスト%・MACDシグナル線%・RSI・ROC・Stoch%K・Stoch%D・MFI・CMF・OBV傾き・転換線・基準線・RCI・EMA傾き・ATR%・BB%b・BB幅・realized_vol・Donchian幅・volume_ratio・swing高値距離・swing安値距離・高値からの経過バー・安値からの経過バー・形スコア・W字・fractal高値距離%・fractal安値距離%・高値切り上げ幅%・安値切り上げ幅%・構造破断距離%・close vs EMA・close vs SMA・close vs VWAP・close vs VWAP典型・当日VWAP・Keltner上・Keltner下・n本高値・n本安値・pivotPP・pivotR1・pivotS1・前期間pivotPP・前期間pivotR1・前期間pivotS1・前週pivotPP・前週pivotR1・前週pivotS1・fib位置・POC・VAH・VAL・前日POC・前日VAH・前日VAL・当日POC・当日VAH・当日VAL・MMI・S-Rタッチ1時間ATR・S-Rタッチ数・W字確定谷・S-Rタッチ確定数・S-Rタッチ確定1時間ATR・SMC_SWEEP確定・realized_vol_rv・SQZ_ON_Carter・StochRSI素%K・TRIX_EMAシグナル・TRIX_EMAヒスト・close vs SSF平均%・close vs TRIMA_TA%・close vs VIDYA_CMO%・close vs HT_TRENDLINE_HL%・close vs MAMA_HL%・close vs FAMA_HL%・DPO教科書%・ABER原作位置・THERMO原作%・THERMO_EMA%・AO%・CCI・ER・KST・KSTシグナル・PPO・PPOシグナル・PPOヒスト・PVO・PVOシグナル・PVOヒスト・SMC_SWEEP・SQZ_ON・STC・STCstoch・StochRSI%K・StochRSI%D・TRIX・TRIXシグナル・TRIXヒスト・TSI・TSIシグナル・TSIヒスト・UO・close vs ALMA%・close vs DEMA%・close vs FWMA%・close vs HILO%・close vs HMA%・close vs HT_TRENDLINE%・close vs HWMA%・close vs JMA%・close vs KAMA%・KAMA傾き%・close vs LINREG%・close vs LRb%・close vs MAMA%・close vs FAMA%・close vs MCGD%・close vs MIDPOINT%・close vs MIDPRICE%・close vs MMAR%・close vs PWMA%・close vs RAINBOW%・close vs RMA%・close vs SINWMA%・close vs SSF%・close vs SWMA%・close vs T3%・close vs TEMA%・close vs TRIMA%・close vs TSF%・close vs VIDYA%・close vs VWMA%・close vs WMA%・WMA傾き%・close vs ZLMA%・AROONU・AROOND・AROONOSC・CHOP・close vs CKSPl%・close vs CKSPs%・DPO%・close vs PMAX%・close vs PSAR%・PSAR加速・PSAR反転・close vs SAREXT%・VHF・VTXP・VTXM・EFI比・EOM比・NVI傾き・PVT傾き・MAD比・stdev%・close vs MEDIAN%・close vs ABER_ZG%・ABER位置・close vs ACCBL%・close vs ACCBU%・close vs CE_L%・close vs CE_S%・HWC位置・HWC幅%・MASSI・THERMO%・TR%・UI・HT_DCPHASE
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
| 1 | 1つ目の工事で当てたコード・参照表を変えること | もう当てた。この工事は設定の写しだけ | 読むもの宣言の入れないもの |
| 2 | 資料の決まりで最初の値も範囲も出ない種類と、名前に軸が無い種類の値を埋めること | この工事の後の T-2・T-3・P-6・P-7・H-1 で扱う。CC は数字を作らない | 読むもの宣言の入れないもの・next_step の順 |
| 3 | close vs VIDYA_CMO%・THERMO_EMA%・ABER原作位置 に、元の種類のパラメータを写すこと。名前に出さない引数に範囲を渡すこと | 対応表の決定「パラメータは写さない」のまま。名前に出さない引数を範囲から渡すのは工事2（M2-F-10b） | 対応表 alias_map_k3c.json・まこさん「進めて良い」（ok_k3c_design_20261011） |
| 4 | 教科書の版と今の版を比べること | M2-F-10f | 読むもの宣言の入れないもの |
| 5 | 探す側の直し（最初の段階に代表の値を渡す・最後の段階でパラメータを動かす） | M2-E-8 | 読むもの宣言の入れないもの |
| 6 | 成績表（material_ranking.json）の作り直し | M2-D-8。増える列は、作り直すまで成績表に行が無く、段の候補の順位に出ない | 読むもの宣言の入れないもの |
| 7 | K-4・B-1＋S-1・R-1・T-1 | この工事の後 | 読むもの宣言の入れないもの |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | StochRSI素%K と close vs SSF平均% の扱い | 決定済み＝元の種類と同じ扱いで写す（写し方のプログラムの対応表が、対応表の元の種類の軸の対応を引く形にして、資料を作り直した） | まこさん「Bで進めてよい」（ok_k3cs_axis_20261011） |
| 2 | 監査の出し方 | 決定済み＝1つ目の工事とこの工事を、工事ごとに1通ずつ実装の監査に出す | まこさん「OK」（ok_k3csplit_20261011・K-3c の1つ目の工事の 3-2 の4番） |
| 3 | 設定の値 | 決定済み＝まこさんが OK した選び方で、プログラムが資料から決めた（値は 4-0 の表） | okd_param_rule_20261004 |
| 4 | 目的の照合（purpose_check.md）の条件の書き方 | 事実だけを書く。パラメータ＝「足した種類の代表の値が指標ごとの一覧に入り、範囲が探す範囲に入る」。閾値＝「今のまま」。時間足＝「今のまま」 | 前の工事の 3-2 |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、1つ目の工事（m2c15-formula-textbook-20261011）で「使う」に入った15種の設定を、資料から設定ファイル2本に写す工事です。**1つ目の工事は、15種の計算と参照表を足し、G-1 で「使う」の表と資料の表3つを作り直しました。資料は、観察のプログラムと engine_tuner が直接 読むものではありません。読むのは設定ファイル（observe_config.json と search_limits.json）です。だから、資料から設定ファイルに写します。
**①いま何が起きているか。**
- 照らしのプログラムの②が、設定ファイル2本と資料の食い違いを出しています（observe_config.json 17行・search_limits.json 10行）。1つ目の工事の設計書の 4-0 の⑦に書いた見込みどおりです。
- ⑦に書いた行（13行と8行）より増えています。増えたのは、StochRSI素%K と close vs SSF平均% の分です（下の②）。
**②まこさんの決定「Bで進めてよい」の中身（元の種類と同じ扱いで写る2種・プログラムが元の種類の値と照らした）。**
| 新しい種類 | 元の種類 | 指標ごとの一覧 | 探す範囲 | 名前に出ない軸の最初の値 |
|---|---|---|---|---|
| StochRSI素%K | StochRSI%K | [[14]] | 7〜21 | {"スキャル": [], "デイトレ": [[14, 3, 3]]} |
| close vs SSF平均% | close vs SSF% | [[10]] | 10〜200 | {"スキャル": [[10, 2]], "デイトレ": [[10, 2]]} |
- 直す前は、名前の軸と資料の軸の対応表（r3_draft_build.py の AXIS_MAP）が種類の名前だけで引く作りで、新しい2種の行がありませんでした。そのため、資料の範囲が1点になり、指標ごとの一覧にも探す範囲にも写りませんでした。
- 案の前に、新しい種類は対応表 research/alias_map_k3c.json の元の種類の対応を引く形に直しました。対応表で「パラメータは写さない」と決めた種類（close vs VIDYA_CMO% ほか）には引きません。私は対応の数字を書いていません。
**③設定の違い（今の設定 → 当てた後・プログラムが数えた）。**
指標ごとの一覧（observe_config.json の material_params）が変わる種類は 6種類です。ここに入るのは、最初の段階で使う代表の値（資料の最初の値）です。
| 種類 | 今の一覧 | 当てた後の一覧 |
|---|---|---|
| DPO教科書% | 無い（ほかの指標の期間の一覧から列を作っている） | [[20]] |
| StochRSI素%K | 無い（ほかの指標の期間の一覧から列を作っている） | [[14]] |
| TRIX_EMAシグナル | 無い（ほかの指標の期間の一覧から列を作っている） | [[15, 9]] |
| TRIX_EMAヒスト | 無い（ほかの指標の期間の一覧から列を作っている） | [[15, 9]] |
| close vs SSF平均% | 無い（ほかの指標の期間の一覧から列を作っている） | [[10]] |
| close vs TRIMA_TA% | 無い（ほかの指標の期間の一覧から列を作っている） | [[10]] |
名前に出ない軸の最初の値（observe_config.json の material_first_hidden）が変わる種類は 5種類です。この欄は列の計算には使いません。
| 種類 | 今 | 当てた後（スキャル／デイトレ） |
|---|---|---|
| SQZ_ON_Carter | 無い | [[20, 2, 20, 1.5]]／[[20, 2, 20, 1.5]] |
| StochRSI素%K | 無い | []／[[14, 3, 3]] |
| close vs SSF平均% | 無い | [[10, 2]]／[[10, 2]] |
| close vs MAMA_HL% | 無い | [[0.5, 0.05]]／[[0.5, 0.05]] |
| close vs FAMA_HL% | 無い | [[0.5, 0.05]]／[[0.5, 0.05]] |
値を埋めない種類の並び（observe_config.json の _material_params_pending）に足される種類は 2種類です＝close vs MAMA_HL%（範囲が1点のまま（全部の軸）：0.5・0.05）・close vs FAMA_HL%（範囲が1点のまま（全部の軸）：0.5・0.05）。
探す範囲（search_limits.json の material_param_ranges）が変わる種類は 8種類です。ここに入るのは、最後の段階で探す、指標ごとに1つの範囲です。
| 種類 | 今の範囲 | 当てた後の範囲 |
|---|---|---|
| DPO教科書% | 無い（カタログの数字の最小〜最大を使う） | 14〜40 |
| StochRSI素%K | 無い（カタログの数字の最小〜最大を使う） | 7〜21 |
| TRIX_EMAシグナル | 無い（カタログの数字の最小〜最大を使う） | 7〜21・9〜9 |
| TRIX_EMAヒスト | 無い（カタログの数字の最小〜最大を使う） | 7〜21・9〜9 |
| realized_vol_rv | 無い（カタログの数字の最小〜最大を使う） | 10〜50 |
| close vs SSF平均% | 無い（カタログの数字の最小〜最大を使う） | 10〜200 |
| close vs TRIMA_TA% | 無い（カタログの数字の最小〜最大を使う） | 1〜200 |
| close vs VIDYA_CMO% | 無い（カタログの数字の最小〜最大を使う） | 20〜200 |
**④材料の列の違い（プログラムが写しで数えた）。**
- 材料の列は 548 列 → 534 列 になります。
- 消える列（18列）＝DPO教科書%48・StochRSI素%K21・StochRSI素%K7・StochRSI素%K9・TRIX_EMAシグナル(14,9)・TRIX_EMAシグナル(21,9)・TRIX_EMAシグナル(7,9)・TRIX_EMAシグナル(9,9)・TRIX_EMAヒスト(14,9)・TRIX_EMAヒスト(21,9)・TRIX_EMAヒスト(7,9)・TRIX_EMAヒスト(9,9)・close vs SSF平均%20・close vs SSF平均%200・close vs SSF平均%50・close vs TRIMA_TA%20・close vs TRIMA_TA%200・close vs TRIMA_TA%50
- 増える列（4列）＝TRIX_EMAシグナル(15,9)・TRIX_EMAヒスト(15,9)・close vs SSF平均%10・close vs TRIMA_TA%10
- 理由＝指標ごとの一覧に行が入った種類は、観察のプログラムの build_catalog が、その一覧の組だけで列を作ります。消える列は、ほかの指標の期間の一覧を借りて作っていた列です。残る列と増える列は、資料の最初の値の列です。
- 当てた後も残る列の値は、1本も変わりません。指標の名前に値を固定で入れて種類を増やす直しは、入っていません（種類の数は変わりません）。
- ★1つ目の工事の設計書の 4-0 の⑦は、設定の行だけを書いていて、列が変わることを書いていませんでした。
**⑤前からの壊すプログラムの直し（プログラムが見つけた・許す直し方は2つだけ）。**
| 壊すプログラム | 対象の設定 | 直し方 | 落ちる文（測るもの） |
|---|---|---|---|
| b142_rci_list_stale.sh | observe_config.json | 探す行と壊した行の末尾に「,」を付ける | ❌ ②observe_config.json（pre_audit_check.py --check-indicator-sources） |
| b149_pending_not_copied.sh | observe_config.json | 探す行を、当てた後の「値を埋めない種類の並び」の行に置き換える（壊した行は変えない） | ❌ ②observe_config.json（pre_audit_check.py --check-indicator-sources） |
| b158_shape_ranges_missing.sh | search_limits.json | 探す行と壊した行の末尾に「,」を付ける | ❌ ②search_limits.json（pre_audit_check.py --check-indicator-sources） |
- 直し方の1つ目＝探す行と壊した行の末尾に「,」を付ける（設定の行が後ろに増えるため）。
- 直し方の2つ目＝探す行が「値を埋めない種類の並び」の行そのものなので、当てた後の行に置き換える。壊した行と落ちる文は変えません。
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

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、当てるプログラム apply_audit_fix.py・照らしのプログラム・観察のプログラムの自己テスト・表を作るプログラム（G-1）・監査に出す前のチェックを動かします。
**誰が結果を使うか。**
- 指標ごとの一覧は、観察のプログラムの build_catalog が読み、材料の列を作ります。
- 探す範囲の設定は、engine_tuner_gen.py の material_ranges が読み、売買を回すプログラムの検証と段の候補の絞りが使います。
- 名前に出ない軸の最初の値と、値を埋めない種類の並びは、照らしのプログラムの②が読みます（列の計算には使いません）。
- 壊すプログラムは、承認のプログラムと監査に出す前のチェックが走らせます。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**今の実物（observe_config.json・search_limits.json・b142・b149・b158）・資料（indicator_params_by_strategy.json）・設計書の 4-20。
**書くもの。**
- 当てる（--design）：observe_config.json・search_limits.json・b142・b149・b158・新しい壊すプログラム 5本。
- G-1：材料の列が変わるので、型の表・出口の型の表・材料の文書・観察の説明書・組み立ての表を作り直します（型の表の中身が変われば、まこさんに再承認していただく）。材料の文書を作るプログラムは、知識の文書 regime_detection_kb.md の件数の囲みも書き直します。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 最初の段階は代表の固定値・最後の段階で指標ごとに1つの範囲から探す | 探し方の決定（まこさん 2026-10-10・2026-10-11） | 指標ごとの一覧に資料の最初の値を写し、探す範囲に資料の範囲を写します。範囲は指標ごとに1つです |
| 指標の名前に値を入れて、指標の数を増やさない | まこさん 2026-10-04「指標名に閾値やパラメータの値を固定で入れて、指標数を増やすという解決策はやめてほしい」 | 名前は変えません。種類の数も変わりません。ほかの指標の期間を借りて作っていた列が消え、代表の値の列になります |
| 数字を CC が作らない | 思考の順の7（req_thinking_20261004） | 設定の行はプログラムが資料から写しました。2種の軸の対応は、元の種類の行を引きました。壊し方の値も、今の設定の行と当てた後の行からプログラムが作りました |
| 探す値を、点の一覧で先に限定しない | 要件の作ってはいけないもの2番 | 範囲は資料の範囲を写します。StochRSI素%K と close vs SSF平均% の範囲は、1点でなく元の種類と同じ範囲になります |
| 未来のデータを使わない | 要件定義書 §4.6.H2 | 計算式は変えません。当てた後に H2 を取り直します |
| 値段の高さで値が変わらない | 要件定義書 §4.6.H6 | 計算式は変えません |
| 乱数を使わない | 恒久67番 | 足すのは設定と壊すプログラムだけです |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| observe_config.json の material_params・material_first_hidden・_material_params_pending | 資料から写した、指標ごとの一覧・名前に出ない軸の最初の値・値を埋めない種類の並び（プログラムが写し直す） | 直す |
| search_limits.json の material_param_ranges | 資料から写した探す範囲（プログラムが写し直す） | 直す |
| .claude/breaks の b142・b149・b158 | 探す行が変わるので、同じ形に直す（壊し方と落ちる文は同じ） | 直す |
| .claude/breaks の新しい壊すプログラム | 照らしの②が、写し直しを壊すと決めた文で落ちるかを見る | 新設 |
| 写し方のプログラム r3_draft_build.py の対応表（.claude/state の下） | 新しい種類が、対応表の元の種類の軸の対応を引く（案の前に直した・この設計書の指示には入らない） | 直した |
- コードは1行も変えません。触る関数はありません。

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. まこさんの承認の後、全部を当てます（apply_audit_fix.py --design --dry → --design）。当てるプログラムは、全件を当てる前の実物で照らしてから、番号の順に当てます。1件でも合わなければ1件も当てません。
2. 当てた直後に、当てるプログラムが G2 と H2 を自分で走らせます（observe_config.json と search_limits.json は H2 の対象です）。型の表の作り直しが要るので、G2 は G-1 の後に取り直します。
3. 照合（verify_design_contract.py --diff）をかけます。照らしのプログラム（①②）・壊すプログラムを走らせ、全体の自己テスト（--selftest）を1回 走らせて、出力をそのまま貼ります。
4. G-1：型の表・出口の型の表・材料の文書・観察の説明書・組み立ての表を作り直します。型の表の中身が変われば、まこさんに再承認していただきます。資料の表3つは作り直しません（種類は増えません）。
5. G-2：G2 → H2 を取り直し、1つ目の工事の壊すプログラム7本（b160〜b166）を、当てた後の実物で測り直します（python3 .claude/tools/run_breaks.py --design v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-formula-textbook-20261011.md --measure-only・約15分・走らせる前に まこさんの OK をいただく）。続けて、監査に出す前のチェック（pre_audit_check.py --run・照らしの①②と組み立ての表の照らしを含む）を走らせます。そのあと、1つ目の工事（m2c15-formula-textbook-20261011）とこの工事を、工事ごとに1通ずつ実装の監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝StochRSI素%K。1つ目の工事で、この材料の計算と参照表を足し、G-1 で「使う」に入り、資料の表に行が足されました。資料の行は StochRSI%K の行の調べた結果を使います（対応表）。ところが、指標ごとの一覧（observe_config.json）には、まだ行がありません。そのため観察のプログラムは、ほかの指標の期間の一覧を借りて、StochRSI素%K7・StochRSI素%K9・StochRSI素%K14・StochRSI素%K21 の4列を作っています。探す範囲の設定（search_limits.json）にも行が無いので、engine_tuner は、カタログの数字の最小〜最大を範囲として使っています。案の前は、名前の軸と資料の軸の対応表に StochRSI素%K の行が無く、資料の範囲が 14〜14 の1点になり、指標ごとの一覧にも探す範囲にも写らない形でした。まこさんの決定のとおり、対応表の元の種類（StochRSI%K）の対応を引く形に直したので、資料の範囲は元の種類と同じ 7〜21 になりました。この工事の後は、指標ごとの一覧に StochRSI素%K の [[14]]（元の種類と同じ代表の値）が入り、列は StochRSI素%K14 の1列になります。探す範囲には 7〜21 の行が入り、engine_tuner は最後の段階で、この範囲から探せます。指標ごとの一覧の最後の行が RCI から close vs TRIMA_TA% に替わるので、RCI の行の末尾に「,」が付き、b142 は「,」の付いた行を探す形に直します。照らしのプログラムの②は、食い違い0件になります。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**探す範囲が変わるのは 8種類です（4-0 の③）。**最初の値も範囲も資料の決まりで出ない種類と、名前に軸が無い種類は、この工事では埋めません（P-6・P-7・H-1 の相手）。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**observe_config.json で変えるもの。**material_params・material_first_hidden・_material_params_pending を資料から写し直す。
**search_limits.json で変えるもの。**material_param_ranges を資料から写し直す。
コマンドの旗は増やしません。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**
1. 照らしのプログラムが、①②とも食い違い0件。コマンド＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources。
2. 壊すプログラムが、全部 決めた文で落ちる（直した b142・b149・b158 も）。コマンド＝python3 .claude/tools/run_breaks.py --design。
3. 全体の自己テストが通る。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest。
4. G2 と H2 が取り直される。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| --design の --dry で、当たらない件が出る | 1件も当てずに止まります。まこさんに報告します |
| 設定ファイルが、資料から写したものと違う | 照らしのプログラムが「②」で始まる行を出して落ちます |
| 対応表の元の種類の軸の対応を引けていない種類が在る | 写し方のプログラムの数え（--plan）が「軸の対応が要るのに AXIS_MAP に無い種類」を出して止まり、写しで確かめるプログラムも案のプログラムも止まります |
| 「使う」の指標が資料に無い | 照らしのプログラムが「①」で始まる行を出して落ちます |
| 型の表の中身が、当てた後の材料の一覧と合わない | 型の表の照らし（gen_signal_families.py --verify）が止まります（1つ目の工事を当てた直後と同じ）。G-1 で作り直し、まこさんの再承認の後に取り直します |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**変えません。**カタログの1件の形・設定の欄の形は前の工事のままです。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**変えません。**

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**変えません。**

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| 観察のプログラムの自己テスト（全体） | 142秒 | 写しで当てた後に走らせた実測（k3cs_draft_build.py の [7]） |
| 軽い口（--selftest-catalog） | 10秒 | 写しで当てた後に走らせた実測（k3cs_draft_build.py の [7]） |
| 材料の一覧 | 534 列 | 写しで数えた（k3cs_draft_build.py の [3]） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**ありません。**全部を --design の1回で当てるので、途中の状態は残りません。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しのプログラムだけが書きます。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**照らしのプログラムは、食い違いがあるときだけ「①」「②」で始まる行を出します。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **observe_config.json と search_limits.json は H2 の対象です。**当てた後に G2 → H2 を取り直します。
2. **材料の列が変わります**（写しで数えた・548 列 → 534 列）。型の表（signal_families）の部品も変わるので、作り直して、まこさんの再承認が要ります（G-1）。材料の文書（materials.md）と、知識の文書 regime_detection_kb.md の件数の囲み（部品の数）も、G-1 で gen_materials.py --write が書き直します（実装の指示には入りません）。
3. **成績表（material_ranking.json）には、増える列の行がありません。**作り直す（M2-D-8）まで、増える列は段の候補の順位に出ません。消える列は、1つ目の工事で足した列です（1つ目の工事の設計書の 4-13 の3番のとおり、成績表に行が無い列）。
4. **マイルストーンへの差し込み（作ってはいけないものとの照合）の違いは、写しで 0行でした。**
5. **前からの壊すプログラムが探す文字の数は、直す3本のほかは当てる前と後で同じです。**直す3本は、同じ指示の中で直します（4-0 の⑤）。プログラムが数えた相手は、下の囲みです。
```
b138_keep_name_dropped.sh・b139_range_excludes_keep.sh・b141_catalog_out_of_range.sh・b143_rci_range_short.sh・b148_bb_range_not_widened.sh・b150_vwaptp_range_missing.sh・b157_wfractal_tol_point.sh
```
6. **1つ目の工事の壊すプログラム7本（b160〜b166）は、列が変わる前の実物で測った物です。**壊す相手は観察のプログラムのコードで、この工事では変わりません。ただし、測る口（自己テスト）が見る列が変わるので、G-2 で、当てた後の実物で測り直します。

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| k3bs_draft_build.py・k3bs_proposal_build.py（同じ形の前の2つ目の工事のプログラム） | 今の実物と直しを全部 当てた後の中身を比べて指示を作る形・写しで確かめる形・壊し方を並べて走らせる形・前からの壊すプログラムの末尾に「,」を付ける直し方 |
| r3_draft_build.py の compute・cfg_block・lim_ranges | 資料から設定ファイルの中身を作る写し方（照らしのプログラムの②と同じ） |
| 壊すプログラム b149 | 照らしのプログラムで測る壊すプログラムの形 |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=0d87933ae1772264 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/observe_config.json
直す箇所: 248行（設定・1つ目の工事で「使う」に入った種類の、指標ごとの一覧・名前に出ない軸の最初の値・値を埋めない種類の並びを、資料からプログラムが写し直す（照らしのプログラムの②が見る中身））
直す前の文字:
~~~
  "RCI": [[5], [7], [9], [26], [52]]

~~~
直した後の文字:
~~~
  "RCI": [[5], [7], [9], [26], [52]],
  "DPO教科書%": [[20]],
  "StochRSI素%K": [[14]],
  "TRIX_EMAシグナル": [[15, 9]],
  "TRIX_EMAヒスト": [[15, 9]],
  "close vs SSF平均%": [[10]],
  "close vs TRIMA_TA%": [[10]]

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_config.json:248「"RCI": [[5], [7], [9], [26], [52]]」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/observe_config.json
直す箇所: 291行（設定・1つ目の工事で「使う」に入った種類の、指標ごとの一覧・名前に出ない軸の最初の値・値を埋めない種類の並びを、資料からプログラムが写し直す（照らしのプログラムの②が見る中身））
直す前の文字:
~~~
  "HWC位置": {"スキャル": [[0.2, 0.1, 0.1, 0.1, 1.0]], "デイトレ": [[0.2, 0.1, 0.1, 0.1, 1.0]]}

~~~
直した後の文字:
~~~
  "HWC位置": {"スキャル": [[0.2, 0.1, 0.1, 0.1, 1.0]], "デイトレ": [[0.2, 0.1, 0.1, 0.1, 1.0]]},
  "SQZ_ON_Carter": {"スキャル": [[20, 2, 20, 1.5]], "デイトレ": [[20, 2, 20, 1.5]]},
  "StochRSI素%K": {"スキャル": [], "デイトレ": [[14, 3, 3]]},
  "close vs SSF平均%": {"スキャル": [[10, 2]], "デイトレ": [[10, 2]]},
  "close vs MAMA_HL%": {"スキャル": [[0.5, 0.05]], "デイトレ": [[0.5, 0.05]]},
  "close vs FAMA_HL%": {"スキャル": [[0.5, 0.05]], "デイトレ": [[0.5, 0.05]]}

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_config.json:291「"HWC位置": {"スキャル": [[0.2, 0.1, 0.1, 0.1, 1.0]], "デイトレ": [[0.2, 0.1, 0.1, 0.1, 1.0]]}」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/observe_config.json
直す箇所: 294行（設定・1つ目の工事で「使う」に入った種類の、指標ごとの一覧・名前に出ない軸の最初の値・値を埋めない種類の並びを、資料からプログラムが写し直す（照らしのプログラムの②が見る中身））
直す前の文字:
~~~
 "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0", "close vs VWAP典型＝範囲が1点のまま（全部の軸）：288", "当日VWAP＝最初の値も範囲も決まらない", "前日POC＝最初の値も範囲も決まらない", "前日VAH＝最初の値も範囲も決まらない", "前日VAL＝最初の値も範囲も決まらない", "当日POC＝最初の値も範囲も決まらない", "当日VAH＝最初の値も範囲も決まらない", "当日VAL＝最初の値も範囲も決まらない"],

~~~
直した後の文字:
~~~
 "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0", "close vs VWAP典型＝範囲が1点のまま（全部の軸）：288", "当日VWAP＝最初の値も範囲も決まらない", "前日POC＝最初の値も範囲も決まらない", "前日VAH＝最初の値も範囲も決まらない", "前日VAL＝最初の値も範囲も決まらない", "当日POC＝最初の値も範囲も決まらない", "当日VAH＝最初の値も範囲も決まらない", "当日VAL＝最初の値も範囲も決まらない", "close vs MAMA_HL%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA_HL%＝範囲が1点のまま（全部の軸）：0.5・0.05"],

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_config.json:294「"_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・1」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 153行（設定・1つ目の工事で「使う」に入った種類の探す範囲を、資料からプログラムが写し直す（照らしのプログラムの②が見る中身））
直す前の文字:
~~~
    "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}]

~~~
直した後の文字:
~~~
    "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}],
    "DPO教科書%": [{"kind": "int", "lo": 14, "hi": 40}],
    "StochRSI素%K": [{"kind": "int", "lo": 7, "hi": 21}],
    "TRIX_EMAシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}],
    "TRIX_EMAヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}],
    "realized_vol_rv": [{"kind": "int", "lo": 10, "hi": 50}],
    "close vs SSF平均%": [{"kind": "int", "lo": 10, "hi": 200}],
    "close vs TRIMA_TA%": [{"kind": "int", "lo": 1, "hi": 200}],
    "close vs VIDYA_CMO%": [{"kind": "int", "lo": 20, "hi": 200}]

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:153「"S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "i」
状態: 確定

#### 実装 5
対象のファイル: .claude/breaks/b142_rci_list_stale.sh
直す箇所: 19〜20行（壊すプログラム・探す行と壊した行の末尾に「,」を付ける＝observe_config.json の当てた後の行に合わせる）
直す前の文字:
~~~
old = '  "RCI": [[5], [7], [9], [26], [52]]\n'
new = '  "RCI": [[7], [9], [26], [52]]\n'

~~~
直した後の文字:
~~~
old = '  "RCI": [[5], [7], [9], [26], [52]],\n'
new = '  "RCI": [[7], [9], [26], [52]],\n'

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:19「old = '  "RCI": [[5], [7], [9], [26], [52]]\n'」
状態: 確定

#### 実装 6
対象のファイル: .claude/breaks/b149_pending_not_copied.sh
直す箇所: 19〜20行（壊すプログラム・探す行を、当てた後の「値を埋めない種類の並び」の行に置き換える（壊した行は変えない）＝observe_config.json の当てた後の行に合わせる）
直す前の文字:
~~~
old = ' "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0", "close vs VWAP典型＝範囲が1点のまま（全部の軸）：288", "当日VWAP＝最初の値も範囲も決まらない", "前日POC＝最初の値も範囲も決まらない", "前日VAH＝最初の値も範囲も決まらない", "前日VAL＝最初の値も範囲も決まらない", "当日POC＝最初の値も範囲も決まらない", "当日VAH＝最初の値も範囲も決まらない", "当日VAL＝最初の値も範囲も決まらない"],\n'
new = ' "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0"],\n'

~~~
直した後の文字:
~~~
old = ' "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0", "close vs VWAP典型＝範囲が1点のまま（全部の軸）：288", "当日VWAP＝最初の値も範囲も決まらない", "前日POC＝最初の値も範囲も決まらない", "前日VAH＝最初の値も範囲も決まらない", "前日VAL＝最初の値も範囲も決まらない", "当日POC＝最初の値も範囲も決まらない", "当日VAH＝最初の値も範囲も決まらない", "当日VAL＝最初の値も範囲も決まらない", "close vs MAMA_HL%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA_HL%＝範囲が1点のまま（全部の軸）：0.5・0.05"],\n'
new = ' "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0"],\n'

~~~
根拠の抜き書き: .claude/breaks/b149_pending_not_copied.sh:19「old = ' "_material_params_pending": ["KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30」
状態: 確定

#### 実装 7
対象のファイル: .claude/breaks/b158_shape_ranges_missing.sh
直す箇所: 19〜20行（壊すプログラム・探す行と壊した行の末尾に「,」を付ける＝search_limits.json の当てた後の行に合わせる）
直す前の文字:
~~~
old = '    "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}],\n    "W字確定谷": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.0, "hi": 0.06, "dec": 3}],\n    "S-Rタッチ確定数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}],\n    "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}]\n'
new = '    "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}]\n'

~~~
直した後の文字:
~~~
old = '    "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}],\n    "W字確定谷": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.0, "hi": 0.06, "dec": 3}],\n    "S-Rタッチ確定数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}],\n    "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}],\n'
new = '    "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}],\n'

~~~
根拠の抜き書き: .claude/breaks/b158_shape_ranges_missing.sh:19「old = '    "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}],\n    "W字確定谷": [{"kind": "int", "lo": 24, "hi": 96」
状態: 確定

#### 実装 8
対象のファイル: .claude/breaks/b167_formula_params_missing.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 指標ごとの一覧から、1つ目の工事で「使う」に入った種類の行を外すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②observe_config.json
# b167_formula_params_missing — 指標ごとの一覧から、1つ目の工事で「使う」に入った種類の行を外すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-formula-settings-20261011・2026-10-11）
#   守っているもの＝完成の条件の照らしのプログラム（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources）
#   壊し方＝scripts/priority_rebuild/observe_config.json の中の、下の old を new に置き換える（k3cs_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources が「❌ ②observe_config.json」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_config.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '  "RCI": [[5], [7], [9], [26], [52]],\n  "DPO教科書%": [[20]],\n  "StochRSI素%K": [[14]],\n  "TRIX_EMAシグナル": [[15, 9]],\n  "TRIX_EMAヒスト": [[15, 9]],\n  "close vs SSF平均%": [[10]],\n  "close vs TRIMA_TA%": [[10]]\n'
new = '  "RCI": [[5], [7], [9], [26], [52]]\n'
if s.count(old) != 1:
    raise SystemExit("[b167_formula_params_missing] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
finish

~~~
根拠の抜き書き: .claude/breaks/b149_pending_not_copied.sh:1「#!/bin/bash」
状態: 確定

#### 実装 9
対象のファイル: .claude/breaks/b168_formula_hidden_missing.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 名前に出ない軸の最初の値から、1つ目の工事で「使う」に入った種類の行を外すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②observe_config.json
# b168_formula_hidden_missing — 名前に出ない軸の最初の値から、1つ目の工事で「使う」に入った種類の行を外すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-formula-settings-20261011・2026-10-11）
#   守っているもの＝完成の条件の照らしのプログラム（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources）
#   壊し方＝scripts/priority_rebuild/observe_config.json の中の、下の old を new に置き換える（k3cs_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources が「❌ ②observe_config.json」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_config.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '  "HWC位置": {"スキャル": [[0.2, 0.1, 0.1, 0.1, 1.0]], "デイトレ": [[0.2, 0.1, 0.1, 0.1, 1.0]]},\n  "SQZ_ON_Carter": {"スキャル": [[20, 2, 20, 1.5]], "デイトレ": [[20, 2, 20, 1.5]]},\n  "StochRSI素%K": {"スキャル": [], "デイトレ": [[14, 3, 3]]},\n  "close vs SSF平均%": {"スキャル": [[10, 2]], "デイトレ": [[10, 2]]},\n  "close vs MAMA_HL%": {"スキャル": [[0.5, 0.05]], "デイトレ": [[0.5, 0.05]]},\n  "close vs FAMA_HL%": {"スキャル": [[0.5, 0.05]], "デイトレ": [[0.5, 0.05]]}\n'
new = '  "HWC位置": {"スキャル": [[0.2, 0.1, 0.1, 0.1, 1.0]], "デイトレ": [[0.2, 0.1, 0.1, 0.1, 1.0]]}\n'
if s.count(old) != 1:
    raise SystemExit("[b168_formula_hidden_missing] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
finish

~~~
根拠の抜き書き: .claude/breaks/b149_pending_not_copied.sh:1「#!/bin/bash」
状態: 確定

#### 実装 10
対象のファイル: .claude/breaks/b169_formula_ranges_missing.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 探す範囲から、1つ目の工事で「使う」に入った種類の行を外すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②search_limits.json
# b169_formula_ranges_missing — 探す範囲から、1つ目の工事で「使う」に入った種類の行を外すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-formula-settings-20261011・2026-10-11）
#   守っているもの＝完成の条件の照らしのプログラム（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources）
#   壊し方＝scripts/priority_rebuild/recipes/search_limits.json の中の、下の old を new に置き換える（k3cs_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources が「❌ ②search_limits.json」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/recipes/search_limits.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}],\n    "DPO教科書%": [{"kind": "int", "lo": 14, "hi": 40}],\n    "StochRSI素%K": [{"kind": "int", "lo": 7, "hi": 21}],\n    "TRIX_EMAシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}],\n    "TRIX_EMAヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}],\n    "realized_vol_rv": [{"kind": "int", "lo": 10, "hi": 50}],\n    "close vs SSF平均%": [{"kind": "int", "lo": 10, "hi": 200}],\n    "close vs TRIMA_TA%": [{"kind": "int", "lo": 1, "hi": 200}],\n    "close vs VIDYA_CMO%": [{"kind": "int", "lo": 20, "hi": 200}]\n'
new = '    "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}]\n'
if s.count(old) != 1:
    raise SystemExit("[b169_formula_ranges_missing] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
finish

~~~
根拠の抜き書き: .claude/breaks/b149_pending_not_copied.sh:1「#!/bin/bash」
状態: 確定

#### 実装 11
対象のファイル: .claude/breaks/b170_alias_axis_list_dropped.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 指標ごとの一覧から、元の種類の軸の対応を引いて写した StochRSI素%K の行を外すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②observe_config.json
# b170_alias_axis_list_dropped — 指標ごとの一覧から、元の種類の軸の対応を引いて写した StochRSI素%K の行を外すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-formula-settings-20261011・2026-10-11）
#   守っているもの＝完成の条件の照らしのプログラム（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources）
#   壊し方＝scripts/priority_rebuild/observe_config.json の中の、下の old を new に置き換える（k3cs_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources が「❌ ②observe_config.json」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_config.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '  "StochRSI素%K": [[14]],\n'
new = ''
if s.count(old) != 1:
    raise SystemExit("[b170_alias_axis_list_dropped] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
finish

~~~
根拠の抜き書き: .claude/breaks/b149_pending_not_copied.sh:1「#!/bin/bash」
状態: 確定

#### 実装 12
対象のファイル: .claude/breaks/b171_alias_axis_range_dropped.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 探す範囲から、元の種類の軸の対応を引いて写した close vs SSF平均% の行を外すと、資料と設定ファイルの照らし（②）が落ちる
# EXPECT_MSG: ❌ ②search_limits.json
# b171_alias_axis_range_dropped — 探す範囲から、元の種類の軸の対応を引いて写した close vs SSF平均% の行を外すと、資料と設定ファイルの照らし（②）が落ちる（工事 m2c15-formula-settings-20261011・2026-10-11）
#   守っているもの＝完成の条件の照らしのプログラム（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources）
#   壊し方＝scripts/priority_rebuild/recipes/search_limits.json の中の、下の old を new に置き換える（k3cs_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources が「❌ ②search_limits.json」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/recipes/search_limits.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "close vs SSF平均%": [{"kind": "int", "lo": 10, "hi": 200}],\n'
new = ''
if s.count(old) != 1:
    raise SystemExit("[b171_alias_axis_range_dropped] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py" --check-indicator-sources
finish

~~~
根拠の抜き書き: .claude/breaks/b149_pending_not_copied.sh:1「#!/bin/bash」
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 12 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 1つ目の工事と分けて、G-1 の後に写す | 15種は G-1 で「使う」の表を作り直すまで「使う」でなく、資料の行も無い。1つ目の工事に入れると、承認の前の検査 A12（指示だけを当てて測る）で照らしの②と壊し方が狙いまで届かない（1つ目の工事の 4-4・まこさんの OK） | 1つ目の工事に入れる |
| 2 | StochRSI素%K と close vs SSF平均% は、対応表の元の種類の軸の対応を引いて、元の種類と同じ扱いで写す | まこさんの決定「Bで進めてよい」。新しい種類の名前に出る軸は、元の種類と同じ。対応を引かないと、2種は代表の値も範囲も持たず、探し方の決定（最初の段階は代表の固定値）に合わない | 1つ目の工事の 4-0 の⑦のまま写す（2種は値を埋めない種類の並びに「範囲が1点のまま」と載るだけ） |
| 3 | 軸の対応は、対応表の行を手で足さず、元の種類の行を引く形にし、案の前に資料を作り直す | 同じ対応を2か所に書かない。資料を作るプログラムの直しを設計書の指示に入れると、A12 の仮当てでは資料が作り直されず、照らしの②が狙いまで届かない。直しは .claude/state の下のプログラムで、BOT の中身ではない | 対応表に2種の行を手で足す（同じ事実を2か所に書く）・設定に2種の行だけ手で書く（資料と設定が食い違う） |
| 4 | 写し方は、照らしのプログラムの②と同じ r3_draft_build.py の写し方を使う | 同じ写し方を2か所に書かない。当てた後に②が食い違い0件になることを、写しで確かめられる | 足す行だけを手で書く |
| 5 | b142・b149・b158 を同じ指示の中で直す | 設定の行が増えると、3本が探す行が変わり、壊すプログラムが「壊す対象の文字が1か所でない」で止まる。壊し方と落ちる文は変えない | 3本を消す・別の工事で直す |
| 6 | 新しい壊すプログラム5本は、照らしのプログラムの口で測る | この工事が守るのは「設定ファイルが資料から写したものと同じ（2種は元の種類と同じ扱い）」で、それを見るのは②だけ | 軽い口で測る |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=20b303e85bd35285 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b167_formula_params_missing.sh` | #1 | 指標ごとの一覧から、1つ目の工事で「使う」に入った種類の行を外す |
| `b168_formula_hidden_missing.sh` | #2 | 名前に出ない軸の最初の値から、1つ目の工事で「使う」に入った種類の行を外す |
| `b169_formula_ranges_missing.sh` | #3 | 探す範囲から、1つ目の工事で「使う」に入った種類の行を外す |
| `b170_alias_axis_list_dropped.sh` | #4 | 指標ごとの一覧から StochRSI素%K の行を外す |
| `b171_alias_axis_range_dropped.sh` | #5 | 探す範囲から close vs SSF平均% の行を外す |
| `b142_rci_list_stale.sh` | #6 | 指標ごとの一覧の RCI を、前の組に戻す |
| `b149_pending_not_copied.sh` | #7 | 値を埋めない種類の並びを、前の形に戻す |
| `b158_shape_ranges_missing.sh` | #8 | 探す範囲から、前の工事で足した3種の行を外す |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 型の表が変わる | G-1 で作り直し、まこさんに再承認していただく（4-4 の4） |
| 2 | 成績表に、増える列の行が無い | M2-D-8 で成績表を作り直すまで、増える列は段の候補の順位に出ない |
| 3 | 照らしのプログラムは、写し方のプログラム（r3_draft_build.py）と資料を読む。写し方のプログラムや資料を作るプログラムが変われば、照らしの基準も変わる | どちらも .claude/state の下に在る。直したときは、照らしのプログラムと監査に出す前のチェックで見る（資料の表のハッシュ値は、監査に出す前のチェックの対象）。直す前の版は .claude/state/indicator_review/_w2_before_20261011 に控えた |
| 4 | 値を埋めない種類が残る | P-6・P-7・H-1 で扱う。この工事では埋めない |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（--design） | 1分未満 | 前の2つ目の工事で、当てるプログラムは1秒未満で終わった |
| 全体の自己テスト | 142秒 | 4-14 |
| 壊すプログラム | 照らしのプログラムの口が8本 | 写しで壊し方を並べて走らせた（k3cs_draft_build.py の [8]） |
| G-1 の表の作り直し | 約2分 | 1つ目の工事の実測（表を作るプログラムの合計） |
| 1つ目の工事の壊すプログラム7本の測り直し | 約15分（走らせる前に まこさんの OK をいただく） | 1つ目の工事の実測（全体の自己テストで測る6本と、軽い口で測る1本） |
| 監査に出す前のチェック | 約10分 | 前の工事の実測（pre_audit_check.py --run） |
| まこさんの承認 | 設計書は1回の見込み。型の表の再承認が1回 | 4-4 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝1つ目の工事で15種を「使う」にし、資料に行を足した。資料が変われば、設定ファイルを写し直すまで照らしの②が食い違う。さらに、名前の軸と資料の軸の対応表が種類の名前だけで引く作りで、元の行の調べた結果を使う新しい種類（StochRSI素%K・close vs SSF平均%）に対応が掛からず、2種が代表の値も範囲も持たない形で写るところだった。この工事は、対応表を直した後の資料を、承認の前の検査で測れる順（G-1 の後）で写す。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。足した種類のうち、資料に最初の値が在る種類は代表の値の列になり、資料に範囲が在る種類は探す範囲を持つようになります。

**③ root か symptom か**＝root です。資料から設定ファイルへの写し方を1つ（r3_draft_build.py）にし、照らしのプログラムが毎回 同じ写し方で比べます。軸の対応は対応表の元の種類から引くので、同じ対応を2か所に書きません。

**④ ベースアップ**＝15種の資料の行は、同じ指標の今の行の調べた結果を使った（research/alias_map_k3c.json・まこさん「進めて良い」2026-10-11）。新しく調べていない。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。設定の行は、資料からプログラムが写しました。壊し方の値も、今の設定の行と当てた後の行からプログラムが作りました。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝1つ目の工事で「使う」に入った15種の設定を、資料から設定ファイル2本に写す（b142・b149・b158 の直しは、その写しで探す行が変わることへの追随）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。条件をつなぐものではなく、資料から設定ファイルへの写しです |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 探す範囲は資料の範囲を写します。指標ごとの一覧は、最初の段階で使う代表の値で、探す値を限定するものではありません（探す範囲は別の欄に持ちます） |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **資料の値そのものが正しいかを、照らしのプログラムが見るか** | 見ません。照らしのプログラムは、資料と設定ファイルが同じかだけを見ます |
| **照らしのプログラムが、写し方のプログラムや資料を作るプログラムの誤りを見つけるか** | 見ません。プログラムが誤っていれば、資料と設定ファイルを同じ誤り方で比べます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作るプログラムを書き換えられたら** | そのプログラム自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=5b010e82f1f1f91d gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝observe_config.json・search_limits.json・b142・b149・b158 と、新しい壊すプログラムを【7-8】に書いた。主なファイルは observe_config.json（指標ごとの一覧）。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝observe_diag.py・軽い口の関数が在る）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム（NEW_FILE）。手本は b149（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝写しで確かめるプログラムを A12 と違う状態で作り、長い確かめを走らせ直した（159回目・教訓 L-671）。この工事のプログラムは、A12 と同じ状態（指示だけを当てる）で測り、自己テストの一覧と許しを A12 の本体から読んだ。写し方のプログラムの直しは指示に入れず、案の前に済ませた。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | この工事は、新しい部品も前処理も足さない。計算式は変えず、当てた後も残る列の値は直す前と同じ。当てた後に H2 を取り直す。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | コードは1行も変えない。行番号を指す文書は動かない（設定ファイルの行だけが増える）。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、探す文字の数が当てる前と後で同じことをプログラムが数えた。変わる3本は同じ指示の中で直す（4-13 の5）。走らせるコマンドの旗は変えない。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムが測るのは照らしのプログラムの口で、ファイルに書かない。本物の結果の置き場には書かない。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 新しく足す関数も、触る関数も無い。DESIGN_CONTRACT の impl_functions は空で、理由を no_impl_functions_reason に書いた。must_use の名前は、軽い口の関数の中に在ることをプログラムが ast で照らした。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足すコマンドの旗は無い。照らしのプログラムは、監査に出す前のチェックの口から呼ぶ。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2c15-formula-settings-20261011）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝照らしのプログラムの①②と、壊すプログラム（わざと壊して落ちるか）。写しで走らせ、全部 通った。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | F-1＝指標ごとの一覧が、いまの資料から写したものと同じ（照らしの②が食い違い0件・足した種類の行が入る） | `python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources` | 実経路 | 指標ごとの一覧から、1つ目の工事で「使う」に入った種類の行を外す | `b167_formula_params_missing.sh` | — | **未着手** |
| 2 | F-1＝名前に出ない軸の最初の値が、いまの資料から写したものと同じ（照らしの②が食い違い0件） | `python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources` | 実経路 | 名前に出ない軸の最初の値から、1つ目の工事で「使う」に入った種類の行を外す | `b168_formula_hidden_missing.sh` | — | **未着手** |
| 3 | F-2＝探す範囲が、いまの資料から写したものと同じ（照らしの②が食い違い0件・足した種類の行が入る） | `python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources` | 実経路 | 探す範囲から、1つ目の工事で「使う」に入った種類の行を外す | `b169_formula_ranges_missing.sh` | — | **未着手** |
| 4 | F-3＝StochRSI素%K が、元の種類の軸の対応を引いて、指標ごとの一覧に写る（照らしの②が食い違い0件） | `python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources` | 実経路 | 指標ごとの一覧から StochRSI素%K の行を外す | `b170_alias_axis_list_dropped.sh` | — | **未着手** |
| 5 | F-3＝close vs SSF平均% が、元の種類の軸の対応を引いて、探す範囲に写る（照らしの②が食い違い0件） | `python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources` | 実経路 | 探す範囲から close vs SSF平均% の行を外す | `b171_alias_axis_range_dropped.sh` | — | **未着手** |
| 6 | F-4＝直した b142 が、照らしの②まで届く（RCI の一覧を前の組に戻すと②が落ちる） | `python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources` | 実経路 | 指標ごとの一覧の RCI を、前の組に戻す | `b142_rci_list_stale.sh` | — | **未着手** |
| 7 | F-1・F-4＝直した b149 が、照らしの②まで届く（値を埋めない種類の並びを前の形に戻すと②が落ちる） | `python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources` | 実経路 | 値を埋めない種類の並びを、前の形に戻す | `b149_pending_not_copied.sh` | — | **未着手** |
| 8 | F-2・F-4＝直した b158 が、照らしの②まで届く（探す範囲から前の工事の3種の行を外すと②が落ちる） | `python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources` | 実経路 | 探す範囲から、前の工事で足した3種の行を外す | `b158_shape_ranges_missing.sh` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=adc47c79643ed92b gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/observe_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `selftest_catalog` | 7333 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 196件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=cb1574056bab3f98 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/observe_diag.py",
  "_impl_file の意味": "照らす相手は実在するファイル。材料の一覧の軽い口が在る、観察のプログラムを照らす。この工事はコードを変えない。",
  "impl_functions": {},
  "no_impl_functions_reason": "この工事は設定ファイル observe_config.json と search_limits.json の、資料から写す塊と、壊すプログラム（前からの3本の直しと新しい5本）だけを直す。コードの関数は1つも触らない。触った関数が0件であることは、実装の後に確定させる（当てた後に照合 verify_design_contract.py --diff をかけて確かめる）。",
  "self_check_calls": [
    "selftest_catalog"
  ],
  "_self_check_calls の意味": "observe_diag.py に在るはずの、材料の一覧の軽い口の関数の名前。",
  "must_use": {
    "selftest_catalog": [
      "build_catalog",
      "load_config",
      "find_material"
    ]
  },
  "_must_use の意味": "軽い口が呼ぶ関数（k3cs_proposal_build.py が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は、設定ファイルの値を資料から写し直すだけ。外から読む一覧の形（カタログの1件の形・設定の欄の形）は変えない。",
  "generated_from": {
    "impl_functions": "空（理由＝no_impl_functions_reason）",
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

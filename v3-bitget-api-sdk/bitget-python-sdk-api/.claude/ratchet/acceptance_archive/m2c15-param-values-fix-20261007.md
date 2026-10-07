<!-- ARC iter="m2c15-param-values-fix-20261007" -->

# 設計書｜監査 CP63 の修正1・4・6 を案 A で直す。M2-C-15

TARGET: scripts/priority_rebuild/engine_tuner_gen.py, scripts/priority_rebuild/observe_config.json, scripts/priority_rebuild/observe_diag.py, scripts/priority_rebuild/recipes/search_limits.json, .claude/breaks/b140_group_range_ignored.sh, .claude/breaks/b141_catalog_out_of_range.sh
NEW_FILE: .claude/breaks/b140_group_range_ignored.sh, .claude/breaks/b141_catalog_out_of_range.sh
MODEL: .claude/breaks/b139_range_excludes_keep.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2c15-param-values-fix-20261007/ok_all_20261007`・`m2c15-param-values-fix-20261007/ok_r4_20261007`・`m2c15-param-values-fix-20261007/ok_source_20261007`・`m2c15-param-values-fix-20261007/okd_r4_20261007`・`m2c15-param-values-fix-20261007/req_fix_20261007`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2c15-param-values-fix-20261007/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-param-values-fix-20261007 --write`。検出＝`--work m2c15-param-values-fix-20261007 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=8c5b3ff852ac2304 gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2c15-param-values-fix-20261007/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2c15-param-values-fix-20261007/ok_all_20261007.txt`（まこさんの発言）・`verbatim/m2c15-param-values-fix-20261007/ok_r4_20261007.txt`（まこさんの発言）・`verbatim/m2c15-param-values-fix-20261007/ok_source_20261007.txt`（まこさんの発言）・`verbatim/m2c15-param-values-fix-20261007/okd_r4_20261007.txt`（まこさんが OK した CC の文）・`verbatim/m2c15-param-values-fix-20261007/req_fix_20261007.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝506 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_all_20261007` | V01〜V09（9 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_r4_20261007` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_source_20261007` | V01〜V04（4 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_r4_20261007` | V01〜V05（5 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_r4_20261007` | V06〜V99（94 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V100〜V105（6 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V106〜V110（5 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V111〜V123（13 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V124〜V130（7 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V131〜V137（7 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V138〜V147（10 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V148〜V149（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V150〜V151（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V152〜V155（4 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V156〜V157（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V158〜V159（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V160〜V165（6 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V166〜V174（9 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V175〜V180（6 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V181〜V182（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V183〜V184（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V185〜V186（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V187〜V192（6 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V193〜V357（165 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V358〜V365（8 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V366〜V372（7 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V373〜V381（9 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V382〜V388（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V389〜V390（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V391〜V392（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V393〜V397（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V398〜V408（11 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V409〜V429（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V430〜V434（5 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V435〜V487（53 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_r4_20261007` | V488〜V491（4 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `req_fix_20261007` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
工事 m2c15-param-values-20261006（指標の修正の全体の表の2回目）の実装の監査 CP63 は NO-GO でした。この工事は、その修正1・4・6 を、まこさんが選んだ案 A で直します（まこさん「全部直す」）。前の工事に指示を足すと、前の17件の直した後の文字の塊の中を書き替え、設計書を作る道具の照らしが止まるので、新しい工事名にしました（まこさん「全部OK」）。中身は4つです。①修正1（Critical）＝段の候補を作る所（engine_tuner_gen.py の _group_usable_col）が、成績表の列の数字が範囲の外なら使わない形にします。前の工事の設計書 4-13 の3 に書いたのに、実物は禁止3（標本不足）しか見ていませんでした。②修正4（Major）＝TSI の3種の範囲を、名前の軸に正しく当てます（短い方 7〜25・長い方 4〜26 → 短い方 4〜13・長い方 7〜26）。③修正6（Major）＝VIDYA と T3 の範囲が、カタログの列（20・50・200）を含む形にします（VIDYA 14〜14 → 14〜200・T3 8〜34 → 8〜200）。④修正4・6 の元＝範囲を作る道具が、今の値と資料の値の軸の順をそろえずに混ぜ、軸の数が違う今の値を捨てていたので、元から直して修正対応表を作り直しました。同じ原因で、StochRSI%K・%D（14〜14 → 7〜21）・ALMA（9〜18 → 9〜200）・MCGD（10〜10 → 10〜200）・SSF（10〜10 → 10〜200）の範囲も変わります（まこさん「全部OK」）。材料の名前は1本も変わらず、カタログは 476 列のままです。前の工事の監査の修正2・5・7（前の工事の設計書の作り直し）は、この工事の設計書で受けます。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 段の候補の範囲の照らし（F-1） | `grep -n -F 'param_in_range(family, m["param"], ranges)' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 実装の前は、無い。実装の後は、_group_usable_col の中に在る | （終了コード 1） |
| TSI の範囲（F-4） | `grep -n -F '"TSI": [{"kind": "int", "lo": 7, "hi": 25}' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json` | 実装の前は、在る（名前の短い方の軸に、資料の長い方の値が混ざっている）。実装の後は、無い | 60:    "TSI": [{"kind": "int", "lo": 7, "hi": 25}, {"kind": "int", "lo": 4, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}],（終了コード 0） |
| T3 の範囲（F-6） | `grep -n -F '"close vs T3%": [{"kind": "int", "lo": 8, "hi": 34}]' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json` | 実装の前は、在る（カタログの列の数字が範囲の外）。実装の後は、無い | 141:    "close vs T3%": [{"kind": "int", "lo": 8, "hi": 34}],（終了コード 0） |
| 軽い口の⑬をカタログの全部に広げた所（F-6） | `grep -n -F 'set(_nm_k1)' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、selftest_catalog の中に在る | （終了コード 1） |
| 軽い口の⑭（F-1） | `grep -n -F '修正1: 範囲の外の数字の列' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、selftest_catalog の中に在る | （終了コード 1） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

［自動］印のファイル・型の表・格子と範囲
<!-- ACC_MATERIALS_START hash=9c91a091e89762dc gen_acceptance.py が自動生成＝手で書き換えない -->
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
| `material_param_ranges` | {"ADX": [{"kind": "int", "lo": 7, "hi": 21}], "DI差": [{"kind": "int", "lo": 7, "hi": 21}], "MACD線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}], "MACDヒスト%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "MACDシグナル線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "転換線": [{"kind": "int", "lo": 5, "hi": 12}], "基準線": [{"kind": "int", "lo": 13, "hi": 26}], "EMA傾き": [{"kind": "int", "lo": 9, "hi": 200}], "KSTシグナル": [{"kind": "int", "lo": 9, "hi": 9}], "PPO": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOシグナル": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOヒスト": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "TRIX": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TSI": [{"kind": "int", "lo": 7, "hi": 25}, {"kind": "int", "lo": 4, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIシグナル": [{"kind": "int", "lo": 7, "hi": 25}, {"kind": "int", "lo": 4, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIヒスト": [{"kind": "int", "lo": 7, "hi": 25}, {"kind": "int", "lo": 4, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "KAMA傾き%": [{"kind": "int", "lo": 7, "hi": 10}], "WMA傾き%": [{"kind": "int", "lo": 20, "hi": 200}], "AROONU": [{"kind": "int", "lo": 7, "hi": 288}], "AROOND": [{"kind": "int", "lo": 7, "hi": 25}], "AROONOSC": [{"kind": "int", "lo": 7, "hi": 25}], "VTXP": [{"kind": "int", "lo": 14, "hi": 30}], "VTXM": [{"kind": "int", "lo": 14, "hi": 30}], "RSI": [{"kind": "int", "lo": 2, "hi": 21}], "ROC": [{"kind": "int", "lo": 9, "hi": 24}], "Stoch%K": [{"kind": "int", "lo": 5, "hi": 21}], "Stoch%D": [{"kind": "int", "lo": 5, "hi": 21}], "MFI": [{"kind": "int", "lo": 10, "hi": 20}], "CMF": [{"kind": "int", "lo": 20, "hi": 36}], "OBV傾き": [{"kind": "int", "lo": 10, "hi": 20}], "BB%b": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}], "volume_ratio": [{"kind": "int", "lo": 20, "hi": 50}], "CCI": [{"kind": "int", "lo": 7, "hi": 21}], "PVO": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOシグナル": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOヒスト": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "StochRSI%K": [{"kind": "int", "lo": 14, "hi": 14}], "StochRSI%D": [{"kind": "int", "lo": 14, "hi": 14}], "DPO%": [{"kind": "int", "lo": 14, "hi": 40}], "EFI比": [{"kind": "int", "lo": 10, "hi": 20}], "EOM比": [{"kind": "int", "lo": 10, "hi": 20}], "NVI傾き": [{"kind": "int", "lo": 10, "hi": 20}], "PVT傾き": [{"kind": "int", "lo": 10, "hi": 20}], "ATR%": [{"kind": "int", "lo": 5, "hi": 21}], "BB幅": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}], "realized_vol": [{"kind": "int", "lo": 10, "hi": 50}], "Donchian幅": [{"kind": "int", "lo": 10, "hi": 20}], "MMI": [{"kind": "int", "lo": 200, "hi": 500}], "ER": [{"kind": "int", "lo": 7, "hi": 21}], "CHOP": [{"kind": "int", "lo": 7, "hi": 21}], "VHF": [{"kind": "int", "lo": 7, "hi": 28}], "MAD比": [{"kind": "int", "lo": 20, "hi": 50}], "stdev%": [{"kind": "int", "lo": 10, "hi": 50}], "UI": [{"kind": "int", "lo": 7, "hi": 21}], "高値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "安値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "形スコア": [{"kind": "int", "lo": 24, "hi": 96}], "W字": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.003, "hi": 0.003, "dec": 3}], "fractal高値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "fractal安値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "高値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "安値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "構造破断距離%": [{"kind": "int", "lo": 2, "hi": 3}], "close vs EMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs SMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs VWAP": [{"kind": "int", "lo": 288, "hi": 288}], "Keltner上": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "Keltner下": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "n本高値": [{"kind": "int", "lo": 10, "hi": 50}], "n本安値": [{"kind": "int", "lo": 10, "hi": 50}], "pivotPP": [{"kind": "int", "lo": 288, "hi": 288}], "pivotR1": [{"kind": "int", "lo": 288, "hi": 288}], "pivotS1": [{"kind": "int", "lo": 288, "hi": 288}], "fib位置": [{"kind": "int", "lo": 14, "hi": 96}], "S-Rタッチ1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}], "S-Rタッチ数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}], "close vs ALMA%": [{"kind": "int", "lo": 9, "hi": 18}], "close vs DEMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs FWMA%": [{"kind": "int", "lo": 10, "hi": 20}], "close vs HMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs JMA%": [{"kind": "int", "lo": 3, "hi": 80}], "close vs KAMA%": [{"kind": "int", "lo": 7, "hi": 30}], "close vs LINREG%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs LRb%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs MCGD%": [{"kind": "int", "lo": 10, "hi": 10}], "close vs MIDPOINT%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MIDPRICE%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MMAR%": [{"kind": "int", "lo": 10, "hi": 35}], "close vs PWMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs RAINBOW%": [{"kind": "int", "lo": 2, "hi": 2}, {"kind": "int", "lo": 1, "hi": 10}], "close vs RMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SINWMA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs SSF%": [{"kind": "int", "lo": 10, "hi": 10}], "close vs SWMA%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs T3%": [{"kind": "int", "lo": 8, "hi": 34}], "close vs TEMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TRIMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TSF%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs VIDYA%": [{"kind": "int", "lo": 14, "hi": 14}], "close vs VWMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs WMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs MEDIAN%": [{"kind": "int", "lo": 4, "hi": 200}]} |

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
| 1 | 範囲の「短い方 < 長い方」の決まり（MACD の3種＝短い方 3〜12・長い方 10〜26／TSI の3種＝短い方 4〜13・長い方 7〜26） | 範囲を作る関数は軸どうしの関係を持たない（engine_tuner_gen.py の material_ranges の説明）。探す側をつなぐ工事2 に入れる。TSI は、資料のスキャルの値 [7,4,2] の長い方 7 が、デイトレの短い方 13 より小さいので、軸を正しく当てても 7〜13 で重なる | 前の工事の やることの表 3-2 の3行目・r4_names.json の軸の順が入れ替わる組 |
| 2 | 材料の名前の一覧（material_params）を変えること | この工事は範囲と段の候補の直し。カタログは 476 列のまま（写しで同じと確かめた） | 読むもの宣言の入れないもの・r4_check.json |
| 3 | 成績表（material_ranking.json）の作り直し | M2-D-8 で、まこさんの OK の後に走らせる。この工事の後は、範囲の外の列（ROC3・ROC6 ほか）は段の候補に出ない | 読むもの宣言の入れないもの |
| 4 | 指標の修正の3回目・4回目（K-3・B-1・S-1・K-7・K-4・R-1・T-1） | まこさん「分ける」 | ok_split_20261004 |
| 5 | 前の工事の設計書を作り直すこと（監査 CP63 の修正2・5・7） | 前の工事の設計書を作り直しても、この工事の設計書で上書きされ、承認もしないので記録に残らない。修正1・4・6 の決定は、この工事の 3-2 に書く | まこさん「全部OK」（ok_all_20261007） |
| 6 | 監査 CP63 の Minor-5（出口の型の表の元データ exit_families_rules.json の説明の文の古い数）と Minor-6（依頼書の自己申告の書き方） | 監査が修正の指示を書いていない（表示だけ・書き方だけ） | 監査 CP63 の Q11・§6 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 監査 CP63 の修正1・4・6 の案（A か B か） | 決定済み＝3つとも案 A（まこさん「全部直す」2026-10-07） | req_fix_20261007・worklog 20261007 §1 |
| 2 | 修正4・6 を、範囲を作る道具（apply_param_rule.py）の元から直すこと。この直しで TSI・VIDYA のほかに StochRSI%K・%D・ALMA・MCGD・SSF の範囲も変わる | 決定済み＝元から直す・5行も変える（まこさん「OK」「全部OK」） | ok_source_20261007・ok_all_20261007 |
| 3 | 修正1 の番人（範囲の外の列を段の候補に使わない）の置き場 | 観察の道具の軽い口（observe_diag.py --selftest-catalog）に⑭として置き、engine_tuner_gen.py の _group_usable_col を呼んで確かめる。engine_tuner_gen.py の自己テストの口に置くと、承認の前に私が完成の条件のコマンドを走らせられない（設計↔実装ゲートは、承認されていない設計書では engine_tuner を走らせない） | require_design_contract_before_run.sh の engine_tuner の止め |
| 4 | TSI の3種の範囲は、軸を正しく当てても 7〜13 で重なる | MACD と同じく、「短い方 < 長い方」の決まりは工事2 に入れる（3-1 の1行目） | r4_names.json |
| 5 | 目的の照合（purpose_check.md）の条件の書き方 | 事実だけを書く。パラメータ＝「TSI・VIDYA・T3 ほかの探す範囲が変わる（4-0 の③の表）。段の候補は範囲の外の列を使わない」。閾値＝「今のまま」。時間足＝「今のまま」 | 前の工事の 3-2 |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、前の工事（m2c15-param-values-20261006）の実装の監査 CP63 の修正1・4・6 を、案 A で直す工事です。**前の工事の目的（まこさんの6項目の3番＝パラメータが、範囲から探されている）を、監査が見つけた3つの穴を塞いで、実物でも成り立たせます。
**①いま何が起きているか。**
- 修正1（Critical）＝段の候補を作る所（engine_tuner_gen.py の _group_usable_col）は、禁止3（標本不足）しか見ていません。前の工事の設計書 4-13 の3 には「その列の数字が範囲の中かで絞ります」と書きましたが、実物にその仕組みはありませんでした。成績表は前のカタログの数字で作られているので、範囲の外の列（例＝ROC3・ROC6）が段の候補に残り、案を作った後の出どころの検査で止まります（監査 CP63 の Q11＝ROC の組84のうち36組）。
- 修正4（Major）＝TSI の3種の範囲が、名前の軸に正しく当たっていません。名前の軸は tsi(fast, slow, signal)＝1つ目が短い方です。資料の軸は「first（長い方・先にならす）・second（短い方）・signal」です。範囲を作る道具（apply_param_rule.py）が、資料の値と今の値 [12,26,9] を、軸の順をそろえずに混ぜていました。
- 修正6（Major）＝close vs VIDYA% と close vs T3% は、カタログの列の数字（20・50・200）が範囲の外です。VIDYA の範囲の出どころは「見つかった値と今の値の最小〜最大」なのに、範囲を作る道具が、軸の数が違う今の値（名前の1軸だけの [20]・[50]・[200]）を捨てていました。T3 の範囲は「教科書の範囲」8〜34 です。
**②この工事で何が変わるか。**
- F-0：範囲を作る道具を元から直し、修正対応表を作り直しました（名前の軸と資料の軸の対応で、今の値を資料の軸へ入れてから混ぜる）。
- F-4・F-6：探す範囲の設定（search_limits.json の material_param_ranges）を、作り直した修正対応表から道具が写し直します。一覧に入らない種類も、カタログの数字が範囲の外なら範囲を広げて含めます（いま当たるのは T3）。設定の範囲が変わるのは 10種類です（下の③の表）。範囲の注記に、この決まりを足します。値を埋めずに並べる種類（P-4）は 28種になります。
- F-1：段の候補を作る所が、列の数字が範囲の外なら使わない形にします。説明の文（_mat_from_col の「範囲を狭めていない」）を事実に合わせます。
- 番人：軽い口（--selftest-catalog）の⑬（範囲が数字を含むか）を、カタログの名前の全部に広げます。⑭（段の候補は範囲の外の列を使わない・範囲の中の列は使う）を足します。
**③範囲の違い（今の設定 → 当てた後・道具が数えた）。**
| 種類 | 今の範囲 | 当てた後の範囲 |
|---|---|---|
| TSI | 7〜25・4〜26・7〜12 | 4〜13・7〜26・7〜12 |
| TSIシグナル | 7〜25・4〜26・7〜12 | 4〜13・7〜26・7〜12 |
| TSIヒスト | 7〜25・4〜26・7〜12 | 4〜13・7〜26・7〜12 |
| StochRSI%K | 14〜14 | 7〜21 |
| StochRSI%D | 14〜14 | 7〜21 |
| close vs ALMA% | 9〜18 | 9〜200 |
| close vs MCGD% | 10〜10 | 10〜200 |
| close vs SSF% | 10〜10 | 10〜200 |
| close vs T3% | 8〜34 | 8〜200 |
| close vs VIDYA% | 14〜14 | 14〜200 |
**④名前の軸と資料の軸の対応（21種）。**前の工事の18種に、TSI の3種を足しました。TSI の根拠＝ライブラリは slow を先に、fast を後に掛けます（pandas_ta_classic/momentum/tsi.py の slow_ema → fast_slow_ema）。
| 種類 | 名前の軸の引数（計算式） | 資料のパラメータの名前 | 名前の軸に当てた資料の軸 |
|---|---|---|---|
| 転換線 | t_ | 転換線の期間・基準線の期間・先行スパンBの期間 | t_ ↔ 転換線の期間 |
| 基準線 | k_ | 転換線の期間・基準線の期間・先行スパンBの期間 | k_ ↔ 基準線の期間 |
| KSTシグナル | g_ | roc1・roc2・roc3・roc4・sma1・sma2・sma3・sma4・signal | g_ ↔ signal |
| KAMA傾き% | n | er_period・fast_sc・slow_sc | n ↔ er_period |
| StochRSI%K | n | n（RSI の本数とストキャスの本数）・%K の平滑・%D（%K の移動平均の本数） | n ↔ n（RSI の本数とストキャスの本数） |
| StochRSI%D | n | n（RSI の本数とストキャスの本数）・%K の平滑・%D（%K の移動平均の本数） | n ↔ n（RSI の本数とストキャスの本数） |
| Keltner上 | n・k | EMA の期間・ATR の倍率・ATR の期間 | n ↔ EMA の期間・k ↔ ATR の倍率 |
| Keltner下 | n・k | EMA の期間・ATR の倍率・ATR の期間 | n ↔ EMA の期間・k ↔ ATR の倍率 |
| close vs ALMA% | n | window（本数）・offset・sigma | n ↔ window（本数） |
| close vs JMA% | n | length（本数）・phase | n ↔ length（本数） |
| close vs KAMA% | n | length（効率比の本数）・fast・slow | n ↔ length（効率比の本数） |
| close vs MCGD% | n | N（本数）・c（分母の係数） | n ↔ N（本数） |
| close vs SSF% | n | length（臨界周期の本数）・poles | n ↔ length（臨界周期の本数） |
| EMA傾き | n | ema_period・slope_lookback_k | n ↔ ema_period |
| Stoch%K | n | n（%K の高安を見る本数）・%K の平滑（slow）・%D（%K の移動平均の本数） | n ↔ n（%K の高安を見る本数） |
| Stoch%D | n | n（%K の高安を見る本数）・%K の平滑（slow）・%D（%K の移動平均の本数） | n ↔ n（%K の高安を見る本数） |
| close vs T3% | n | length・vfactor（a） | n ↔ length |
| close vs VIDYA% | n | length（EMA の長さ）・CMO の期間 | n ↔ length（EMA の長さ） |
| TSI | f_・s_・g_ | first（長い方・先にならす）・second（短い方・後にならす）・signal | f_ ↔ second（短い方・後にならす）・s_ ↔ first（長い方・先にならす）・g_ ↔ signal |
| TSIシグナル | f_・s_・g_ | first・second・signal | f_ ↔ second・s_ ↔ first・g_ ↔ signal |
| TSIヒスト | f_・s_・g_ | first・second・signal | f_ ↔ second・s_ ↔ first・g_ ↔ signal |
**⑤値を埋めずに並べる種類（P-4・28種）。**
| 種類 | わけ |
|---|---|
| RCI | 資料（修正対応表）に行が無い＝最初の値も範囲も無い |
| 前期間pivotPP | 資料（修正対応表）に行が無い＝最初の値も範囲も無い |
| 前期間pivotR1 | 資料（修正対応表）に行が無い＝最初の値も範囲も無い |
| 前期間pivotS1 | 資料（修正対応表）に行が無い＝最初の値も範囲も無い |
| KST | 範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9 |
| KSTシグナル | 範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9 |
| PPO | 範囲が1点のまま（全部の軸）：12・26・9 |
| PPOシグナル | 範囲が1点のまま（全部の軸）：12・26・9 |
| PPOヒスト | 範囲が1点のまま（全部の軸）：12・26・9 |
| STCstoch | 範囲が1点のまま（全部の軸）：23・50・10 |
| HWC幅% | 範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1 |
| MASSI | 範囲が1点のまま（全部の軸）：9・25 |
| close vs VWAP | 範囲が1点のまま（全部の軸）：288 |
| pivotPP | 範囲が1点のまま（全部の軸）：288 |
| pivotR1 | 範囲が1点のまま（全部の軸）：288 |
| pivotS1 | 範囲が1点のまま（全部の軸）：288 |
| POC | 最初の値も範囲も決まらない |
| VAH | 最初の値も範囲も決まらない |
| VAL | 最初の値も範囲も決まらない |
| SMC_SWEEP | 範囲が1点のまま（全部の軸）：15・1.5 |
| close vs MAMA% | 範囲が1点のまま（全部の軸）：0.5・0.05 |
| close vs FAMA% | 範囲が1点のまま（全部の軸）：0.5・0.05 |
| close vs ZLMA% | 最初の値も範囲も決まらない |
| close vs PMAX% | 最初の値も範囲も決まらない |
| close vs SAREXT% | 最初の値も範囲も決まらない |
| close vs ABER_ZG% | 範囲が1点のまま（全部の軸）：5・15 |
| ABER位置 | 範囲が1点のまま（全部の軸）：5・15 |
| HWC位置 | 範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0 |
**⑥範囲で見つかったこと。**
- 範囲を広げた軸＝ROC の軸1: 範囲 9〜14 の外に、一覧の値 [9.0, 12.0, 24.0] が在る → 9〜24 に広げる
- 範囲を広げた軸＝close vs T3% の軸1: 範囲 8〜34 の外に、カタログの値 [20.0, 50.0, 200.0] が在る → 8〜200 に広げる
- 軸の順が入れ替わる組＝MACD線%: 軸1 3〜12 と 軸2 10〜26 が重なる
- 軸の順が入れ替わる組＝MACDヒスト%: 軸1 3〜12 と 軸2 10〜26 が重なる
- 軸の順が入れ替わる組＝MACDシグナル線%: 軸1 3〜12 と 軸2 10〜26 が重なる
- 軸の順が入れ替わる組＝TSI: 軸1 4〜13 と 軸2 7〜26 が重なる
- 軸の順が入れ替わる組＝TSIシグナル: 軸1 4〜13 と 軸2 7〜26 が重なる
- 軸の順が入れ替わる組＝TSIヒスト: 軸1 4〜13 と 軸2 7〜26 が重なる
- P-3 の照らしで見つけた、列の計算に使われない軸（前から在る作り・前の工事の 3-1）＝S-Rタッチ1時間ATR の軸2（[0.5, 1.0, 1.5] のどれでも、2種類の値動きとも列が同じ）
- P-3 の照らしで見つけた、列の計算に使われない軸（前から在る作り・前の工事の 3-1）＝S-Rタッチ1時間ATR の軸3（[7, 14, 21] のどれでも、2種類の値動きとも列が同じ）
- P-3 の照らしで見つけた、列の計算に使われない軸（前から在る作り・前の工事の 3-1）＝PVO の軸3（[5, 7, 9] のどれでも、2種類の値動きとも列が同じ）
- P-3 の照らしで見つけた、列の計算に使われない軸（前から在る作り・前の工事の 3-1）＝TSI の軸3（[7, 10, 12] のどれでも、2種類の値動きとも列が同じ）
- P-3＝この直しで増えた、端の値が効いていない軸 0件（範囲の端とまん中の値で列を作り、2種類の値動きで比べた）。
- マイルストーンへの差し込み（作ってはいけないものとの照合）の違い＝0行。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、当てる道具 apply_audit_fix.py・観察の道具の自己テスト・表を作る道具（G-1）・監査に出す前のチェックを動かします。
**誰が結果を使うか。**
- 探す範囲の設定は、engine_tuner_gen.py の material_ranges が読み、売買を回すプログラムの検証器（G6）と段の候補の絞り（_group_usable_col）が使います。
- 段の候補を作る関数（_ranked_material_at（2347行）・build_stage_candidates（2899行）・_material_for_lineage（3100行）・_material_for_law（3140行）・build_width_candidates（3053行）・selftest（6710行））は、_group_usable_col を通して成績表の列を選びます。
- 成績表（material_ranking.json）は、この工事では作り直しません（3-1）。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**今の実物（observe_diag.py・observe_config.json・search_limits.json・engine_tuner_gen.py）・設計書の 4-20。
**書くもの。**
- 当てる（--design）：上の4つのファイルと、新しい壊すプログラム 2本。
- G-1：修正対応表 indicator_fix_plan.json・材料の文書・型の表ほか（変われば）。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 指標の名前に値を入れて、指標の数を増やさない | まこさん 2026-10-04「指標名に閾値やパラメータの値を固定で入れて、指標数を増やすという解決策はやめてほしい」 | 名前は1本も変えません。材料は 476 列 のままです |
| 最初は教科書の固定値で組み、最後に範囲でチューニングする | まこさん（req_scope_20261004） | 範囲だけを直します。一覧（最初の値）は変えません |
| 数字を CC が作らない | 思考の順の7（req_thinking_20261004） | 範囲は道具が修正対応表から写しました。広げるのは、一覧の値とカタログの数字を含めるためだけです |
| 探す値を、点の一覧で先に限定しない | 要件の作ってはいけないもの2番 | 値を埋めずに並べる種類（P-4）から 5種類（StochRSI%D・StochRSI%K・close vs MCGD%・close vs SSF%・close vs VIDYA%）が外れ、範囲になります |
| 未来のデータを使わない | 要件定義書 §4.6.H2 | 計算式は変えません。列の値は直す前と同じです（写しで 0本の違い）。当てた後に H2 を取り直します |
| 値段の高さで値が変わらない | 要件定義書 §4.6.H6 | 計算式は変えません |
| 乱数を使わない | 恒久67番 | 足すのは、範囲の照らし・番人・壊すプログラム・設定だけです |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| search_limits.json の material_param_ranges と注記 | 修正対応表の範囲（名前の軸）を持つ。一覧に入らない種類も、カタログの数字を含むように広げる | 直す |
| observe_config.json の _material_params_pending・material_keep | 値を埋めない種類と残す名前（道具が写し直す） | 直す |
| engine_tuner_gen.py の _group_usable_col | 列の数字が範囲の外なら、段の候補に使わない | 直す |
| engine_tuner_gen.py の _mat_from_col の説明 | 範囲を照らすのは _group_usable_col だと書く（動きは変えない） | 直す |
| observe_diag.py の selftest_catalog（軽い口） | ⑬をカタログの名前の全部に広げる・⑭を足す | 直す |
| .claude/breaks の壊すプログラム | 番人ごとに、直しを壊すと決めた文で落ちるかを見る | 新設 |
- 触る関数は、全部の指示を当てる前と後の構文木を比べて、道具が数えました（下の囲み）。
```
observe_diag.py＝selftest_catalog／engine_tuner_gen.py＝_group_usable_col・_mat_from_col
```

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. まこさんの承認の後、全部を当てます（apply_audit_fix.py --design --dry → --design）。当てる道具は、全件を当てる前の実物で照らしてから、番号の順に当てます。1件でも合わなければ1件も当てません。
2. 当てた直後に、当てる道具が G2 と H2 を自分で走らせます。
3. 照合（verify_design_contract.py --diff）をかけます。設計書の関数の一覧は、当てた後の中身から作るので、食い違わない見込みです（承認の前の検査の仮当てで確かめます）。
4. 軽い口と壊すプログラムを走らせ、全体の自己テスト（--selftest）を1回 走らせて、出力をそのまま貼ります。
5. G-1：修正対応表 indicator_fix_plan.json（make_fix_plan.py）と材料の文書（gen_materials.py --write）を作り直します。型の表と出口の型の表は、範囲だけが変わり名前は変わらないので、変わらない見込みです（変われば、まこさんに再承認していただきます）。
6. G-2：監査に出す前のチェック（pre_audit_check.py --run・G2 と H2 を含む）。そのあと、実装の監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝ROC と TSI。いま、段の候補を作る所（engine_tuner_gen.py の _group_usable_col）は、成績表の列の数字が範囲の中かを見ません。成績表の sufficiency・trigger の ROC の組84のうち36組は、代表の列が ROC3 か ROC6 です（監査 CP63 の Q11）。ROC の範囲は 9〜24 なので、この列は案を作った後の出どころの検査で止まります。この工事の後は、ROC3・ROC6 の列は段の候補に出ず、ROC9・ROC12・ROC24 の列が残ります。TSI は、いま範囲の1つ目（名前の短い方）が 7〜25、2つ目（長い方）が 4〜26 です。資料の「長い方が先」の値と、今の値の「短い方が先」の値を、同じ軸の順のまま混ぜたためです。この工事の後は、1つ目が 4〜13、2つ目が 7〜26 になります。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**探す範囲を、作り直した修正対応表の範囲にします（104種）。**範囲が変わるのは 10種類です（4-0 の③）。名前に出さない引数の範囲は、この工事でも書けません（工事2）。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**search_limits.json で変えるもの。**material_param_ranges の 10行と、その注記（一覧に入らない種類もカタログの数字を含めて広げる、の1文を足す）。
**observe_config.json で変えるもの。**_material_params_pending（値を埋めずに並べる種類）と material_keep（残す名前＝監査の修正9 で正規表現を直したので、確認のレシピの MACDヒスト%(12,26,9) が入る。カタログの列は変わらない）。
コマンドの旗は増やしません。この工事の番人は、前の工事で作った軽い口（--selftest-catalog）に足します。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**
1. 軽い口が全部 通る。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog。全体の自己テストも通る。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest。
2. 壊すプログラムが、全部 決めた文で落ちる。コマンド＝python3 .claude/tools/run_breaks.py --design。
3. 段の候補が、範囲の外の数字の列（ROC3・ROC6 ほか）を使わない（軽い口の⑭が見る）。
4. G2 と H2 が取り直される（監査に出す前のチェックの中）。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| --design の --dry で、当たらない件が出る | 1件も当てずに止まります。まこさんに報告します |
| 段の候補が、範囲の外の数字の列を使えると判定する | 軽い口が「修正1:」で落ちます |
| 設定の範囲が、カタログの列の数字を含まない | 軽い口が「P-2:」で落ちます |
| 範囲の設定に、カタログに無い種類か、軸の数が名前と違う種類が在る | 範囲を作る関数（material_ranges）が「[範囲エラー]」で止まります（前から在る止め） |

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
| 観察の道具の自己テスト（全体） | 123秒 | 写しで当てた後に走らせた実測（r4_draft_build.py の [7]） |
| 軽い口（--selftest-catalog） | 8秒 | 写しで当てた後に走らせた実測（r4_draft_build.py の [7]）。⑭で engine_tuner_gen を読み込むので、前の工事の 7秒より少し延びる |
| 材料の一覧 | 476 列 | 写しで数えた（r4_draft_build.py の [3]） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**ありません。**全部を --design の1回で当てるので、途中の状態は残りません。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しの道具だけが書きます。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**軽い口の番人は、落ちたときだけ「修正1:」「P-2:」で始まる行を出します。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **observe_diag.py・observe_config.json・search_limits.json・engine_tuner_gen.py は H2 の対象です。**当てた後に G2 → H2 を取り直します。
2. **_group_usable_col を呼ぶ所は 6か所です（engine_tuner_gen.py の _ranked_material_at（2347行）・build_stage_candidates（2899行）・_material_for_lineage（3100行）・_material_for_law（3140行）・build_width_candidates（3053行）・selftest（6710行）・道具が構文木で数えた）。**どこでも、範囲の外の数字の列は使われなくなります。直す前は、その列を選ぶと、案を作った後の出どころの検査（assert_provenance の param_in_range）で止まっていました＝止まる所が前に来るだけで、通る案は変わらない見込みです（走らせて確かめてはいません。段の本走は M2-F で走らせます）。
3. **範囲が広がる種類（4-0 の③の表）は、チューニングで試せる数字が増えます。**engine_tuner が範囲から数字を選ぶのは、探す側をつなぐ工事2 からです（今の段の候補は成績表の列の数字を使う）。
4. **マイルストーンへの差し込み（作ってはいけないものとの照合）は変わりません**（写しで 0行の違い）。
5. **前からの壊すプログラムが探す文字の数は、当てる前と後で同じです。**道具が数えた相手は、下の囲みです。
```
b104_atr1h_own_tf.sh・b105_atr1h_future_hour.sh・b106_atr1h_no_clip.sh・b107_atr1h_base_not_passed.sh・b108_atr1h_base_wrong_bars.sh・b109_moving_line_not_built.sh・b110_ts_pos_in_random_draw.sh・b111_ts_pos_excludes_current.sh・b112_stage_warm_not_extended.sh・b122_obs_formula_copied.sh・b126_rank_resume_save_off.sh・b127_stage_q_rank_off.sh・b128_k1_copc_back_in_ao_loop.sh・b129_htf_bar_close_two_bars.sh・b131_industry_map_prev_pivot_gone.sh・b132_hidden_param_not_passed.sh・b133_cksp_mixed_set.sh・b134_ao_name_with_value.sh・b135_rci_mako_gone.sh・b136_insp2_bar_close_dropped.sh・b137_material_params_ignored.sh・b138_keep_name_dropped.sh・b139_range_excludes_keep.sh・b55_cyc_key_time_gone.sh・b56_one_min_csv_old.sh・b60_only5_with_others.sh・b61_insp5_bars_kind.sh・b63_tm_bitget_scope.sh・b64_tm_subdir.sh・b65_tm_badtail.sh・b77_no_streak.sh・b78_law_literal.sh・b79_param_drawn.sh・b80_quantile_one_by_one.sh・b82_abs_missing.sh・b83_bool_col_extra_key.sh・b84_qtable_per_bundle.sh・b85_band_ignores_laws.sh・b87_stages_record.sh・b91_keep_range_ignored.sh・b92_stage2_no_drop_tfs.sh・b94_stage_limits_ignored.sh・b96_tf_hardcoded.sh・b98_qkey_abs_missing.sh・b99_streak_inner_band_only.sh
```

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| r3_draft_build.py（前の工事の道具） | 今の実物と直しを全部 当てた後の中身を比べて指示を作る形・写しで確かめる形・壊し方を並べて走らせる形 |
| observe_diag.py の selftest_catalog（前の工事の軽い口） | 番人を足す場所と、落ちたときの行の形 |
| 壊すプログラム b139 | 壊すプログラムの形 |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=6149ed7bde4e913a gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7115行（selftest_catalog・修正6＝軽い口の⑬（範囲がカタログの数字を含む）を、カタログの名前の全部に広げる）
直す前の文字:
~~~
    _chk13 |= {_x13 for _l13 in (cfg.get("material_keep") or {}).values() for _x13 in _l13}

~~~
直した後の文字:
~~~
    _chk13 |= {_x13 for _l13 in (cfg.get("material_keep") or {}).values() for _x13 in _l13}
    # ★2026-10-07（監査 CP63 の修正6）＝一覧に入らない種類のカタログの名前も見る（VIDYA・T3 の列が範囲の外だった）
    _chk13 |= set(_nm_k1)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7115「_chk13 |= {_x13 for _l13 in (cfg.get("material_keep") or {}).values() for _x13 in _l13}」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7125行（selftest_catalog・修正1＝軽い口に⑭（段の候補は範囲の外の列を使わない・範囲の中の列は使う）を足す）
直す前の文字:
~~~
                ng.append(f"P-2: {_x13} の {_i13 + 1} 番目の数字 {_v13} が、設定の範囲 {_a13['lo']}〜{_a13['hi']} の外")

~~~
直した後の文字:
~~~
                ng.append(f"P-2: {_x13} の {_i13 + 1} 番目の数字 {_v13} が、設定の範囲 {_a13['lo']}〜{_a13['hi']} の外")
    # ── 工事 m2c15-param-values-fix-20261007 の番人（2026-10-07・監査 CP63 の修正1）──
    #  ⑭段の候補（engine_tuner_gen._group_usable_col）は、列の数字が範囲の外なら使わない・範囲の中なら使う
    #    範囲は渡さない（None＝関数の中で本物と同じ範囲を読む）。ROC の範囲は設定の 9〜24（ROC3 は外・ROC12 は中）。
    import engine_tuner_gen as _g14
    _tb14 = _g14.load_signal_table()
    if _g14._group_usable_col("ROC3__5m", "ROC", "5m", None, _tb14):
        ng.append("修正1: 範囲の外の数字の列（ROC3）を、段の候補に使えると判定した")
    if not _g14._group_usable_col("ROC12__5m", "ROC", "5m", None, _tb14):
        ng.append("修正1: 範囲の中の数字の列（ROC12）を、段の候補に使えないと判定した")

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7125「ng.append(f"P-2: {_x13} の {_i13 + 1} 番目の数字 {_v13} が、設定の範囲 {_a13['lo']}〜{_a13['hi']} の外")」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/observe_config.json
直す箇所: 250行（設定・残す名前を写し直す（監査 CP63 の修正9 で正規表現を直したので、確認のレシピの MACDヒスト%(12,26,9) が入る・カタログの列は変わらない））
直す前の文字:
~~~
 "material_keep": {"V9": ["ADX14", "ATR%14", "BB%b(20,2.0)", "BB幅(20,2.0)", "EMA20傾き%", "MACDシグナル線%(12,26,9)", "MACDヒスト%(12,26,9)", "MACD線%(12,26)", "RCI52", "RCI7", "RCI9", "RSI14", "RSI21", "RSI7", "RSI9", "Stoch%D14", "Stoch%K14", "close vs EMA20%", "fib位置20"], "採用中の戦略と確認のレシピ": ["ADX14", "DI差7", "Donchian幅%20", "ROC24", "S-Rタッチ数(144,0.006)", "Stoch%D14", "stdev%50", "volume_ratio20", "volume_ratio50"]},

~~~
直した後の文字:
~~~
 "material_keep": {"V9": ["ADX14", "ATR%14", "BB%b(20,2.0)", "BB幅(20,2.0)", "EMA20傾き%", "MACDシグナル線%(12,26,9)", "MACDヒスト%(12,26,9)", "MACD線%(12,26)", "RCI52", "RCI7", "RCI9", "RSI14", "RSI21", "RSI7", "RSI9", "Stoch%D14", "Stoch%K14", "close vs EMA20%", "fib位置20"], "採用中の戦略と確認のレシピ": ["ADX14", "DI差7", "Donchian幅%20", "MACDヒスト%(12,26,9)", "ROC24", "S-Rタッチ数(144,0.006)", "Stoch%D14", "stdev%50", "volume_ratio20", "volume_ratio50"]},

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_config.json:250「"material_keep": {"V9": ["ADX14", "ATR%14", "BB%b(20,2.0)", "BB幅(20,2.0)", "EMA20傾き%", "MACDシグナル線%(12,26,9)", "MACDヒスト%(」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/observe_config.json
直す箇所: 293行（設定・P-4＝値を埋めずに並べる種類を、作り直した修正対応表から道具が写し直す（範囲が1点でなくなった種類が外れる））
直す前の文字:
~~~
 "_material_params_pending": ["RCI＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "前期間pivotPP＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "前期間pivotR1＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "前期間pivotS1＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "StochRSI%K＝範囲が1点のまま（全部の軸）：14・3・3", "StochRSI%D＝範囲が1点のまま（全部の軸）：14・3・3", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs MCGD%＝範囲が1点のまま（全部の軸）：10・1", "close vs SSF%＝範囲が1点のまま（全部の軸）：10・2", "close vs VIDYA%＝範囲が1点のまま（全部の軸）：14・9", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0"],

~~~
直した後の文字:
~~~
 "_material_params_pending": ["RCI＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "前期間pivotPP＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "前期間pivotR1＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "前期間pivotS1＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0"],

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_config.json:293「"_material_params_pending": ["RCI＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "前期間pivotPP＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "前期間pivotR1＝資料（修正対」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 60〜62行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す）
直す前の文字:
~~~
    "TSI": [{"kind": "int", "lo": 7, "hi": 25}, {"kind": "int", "lo": 4, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}],
    "TSIシグナル": [{"kind": "int", "lo": 7, "hi": 25}, {"kind": "int", "lo": 4, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}],
    "TSIヒスト": [{"kind": "int", "lo": 7, "hi": 25}, {"kind": "int", "lo": 4, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}],

~~~
直した後の文字:
~~~
    "TSI": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}],
    "TSIシグナル": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}],
    "TSIヒスト": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}],

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:60「"TSI": [{"kind": "int", "lo": 7, "hi": 25}, {"kind": "int", "lo": 4, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}],」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 83〜84行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す）
直す前の文字:
~~~
    "StochRSI%K": [{"kind": "int", "lo": 14, "hi": 14}],
    "StochRSI%D": [{"kind": "int", "lo": 14, "hi": 14}],

~~~
直した後の文字:
~~~
    "StochRSI%K": [{"kind": "int", "lo": 7, "hi": 21}],
    "StochRSI%D": [{"kind": "int", "lo": 7, "hi": 21}],

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:83「"StochRSI%K": [{"kind": "int", "lo": 14, "hi": 14}],」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 123行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す）
直す前の文字:
~~~
    "close vs ALMA%": [{"kind": "int", "lo": 9, "hi": 18}],

~~~
直した後の文字:
~~~
    "close vs ALMA%": [{"kind": "int", "lo": 9, "hi": 200}],

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:123「"close vs ALMA%": [{"kind": "int", "lo": 9, "hi": 18}],」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 131行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す）
直す前の文字:
~~~
    "close vs MCGD%": [{"kind": "int", "lo": 10, "hi": 10}],

~~~
直した後の文字:
~~~
    "close vs MCGD%": [{"kind": "int", "lo": 10, "hi": 200}],

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:131「"close vs MCGD%": [{"kind": "int", "lo": 10, "hi": 10}],」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 139行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す）
直す前の文字:
~~~
    "close vs SSF%": [{"kind": "int", "lo": 10, "hi": 10}],

~~~
直した後の文字:
~~~
    "close vs SSF%": [{"kind": "int", "lo": 10, "hi": 200}],

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:139「"close vs SSF%": [{"kind": "int", "lo": 10, "hi": 10}],」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 141行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す）
直す前の文字:
~~~
    "close vs T3%": [{"kind": "int", "lo": 8, "hi": 34}],

~~~
直した後の文字:
~~~
    "close vs T3%": [{"kind": "int", "lo": 8, "hi": 200}],

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:141「"close vs T3%": [{"kind": "int", "lo": 8, "hi": 34}],」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 145行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す）
直す前の文字:
~~~
    "close vs VIDYA%": [{"kind": "int", "lo": 14, "hi": 14}],

~~~
直した後の文字:
~~~
    "close vs VIDYA%": [{"kind": "int", "lo": 14, "hi": 200}],

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:145「"close vs VIDYA%": [{"kind": "int", "lo": 14, "hi": 14}],」
状態: 確定

#### 実装 12
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 150行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す）
直す前の文字:
~~~
  "_material_param_ranges_note": "指標のパラメータの範囲（段A の A-4・2026-08-13 新設）。★2026-10-06（工事 m2c15-param-values-20261006・全体の表の P-2）から、修正対応表（.claude/state/indicator_fix_plan.json・その元の indicator_params_by_strategy.json）の範囲を、プログラムが写して書く（CC は数字を書いていない）。範囲の選び方＝まこさんが OK した選び方（okd_param_rule_20261004 の2＝教科書に範囲が書いてあればそれ、無ければ見つかった値と今の値の最小〜最大）。名前の軸に当たる軸だけを書く（名前に出さない引数の範囲は工事2）。★指標ごとの一覧（observe_config.json の material_params・残す名前を含む）の値が範囲の外なら、範囲を広げて含める（まこさん決定 2026-10-04 の①＝教科書の範囲と最初の値がぶつかる軸は範囲を広げて含める、と同じ型）。★ここに書いていない種類は、材料カタログの数字の 最小〜最大 を範囲として使う（engine_tuner_gen.material_ranges）。★直す前のこの注記に在った「ここに書くのは まこさんが決めた範囲だけ」は、CC が 2026-08-13 に書いた文で、まこさんの発言ではない（worklog 20261004 §10）。形＝{\"RSI\": [{\"kind\": \"int\", \"lo\": 2, \"hi\": 21}]}（軸＝名前の {} の数だけ並べる・kind は int か float・float は dec で小数の桁数）。使い方の出どころ＝まこさんの逐語 2026-08-07（engine_tuner_defects.md の D14 ⑥）「閾値は指標によって様々な値になるので、範囲で検索すると膨大な量になるはずなので、最初は疑似シミュである程度値を絞って、その後、engine_tunerで最適化する際は、疑似シミュで出た値の前後あたりで範囲を事前に指定して（例えば３０〜５０の間とか）探す、という使い方を想定している」。★ここに書いた範囲は 材料カタログの数字を含まなくてよい（狭めるのが目的）。範囲の外の数字は検証器（G6）が止める。",

~~~
直した後の文字:
~~~
  "_material_param_ranges_note": "指標のパラメータの範囲（段A の A-4・2026-08-13 新設）。★2026-10-06（工事 m2c15-param-values-20261006・全体の表の P-2）から、修正対応表（.claude/state/indicator_fix_plan.json・その元の indicator_params_by_strategy.json）の範囲を、プログラムが写して書く（CC は数字を書いていない）。範囲の選び方＝まこさんが OK した選び方（okd_param_rule_20261004 の2＝教科書に範囲が書いてあればそれ、無ければ見つかった値と今の値の最小〜最大）。名前の軸に当たる軸だけを書く（名前に出さない引数の範囲は工事2）。★指標ごとの一覧（observe_config.json の material_params・残す名前を含む）の値が範囲の外なら、範囲を広げて含める（まこさん決定 2026-10-04 の①＝教科書の範囲と最初の値がぶつかる軸は範囲を広げて含める、と同じ型）。★2026-10-07（監査 CP63 の修正6・まこさん「全部直す」）＝一覧に入らない種類も、材料カタログの数字が範囲の外なら、範囲を広げて含める（engine_tuner が段の候補でその列を使えるように・いま当たるのは close vs T3%）。★ここに書いていない種類は、材料カタログの数字の 最小〜最大 を範囲として使う（engine_tuner_gen.material_ranges）。★直す前のこの注記に在った「ここに書くのは まこさんが決めた範囲だけ」は、CC が 2026-08-13 に書いた文で、まこさんの発言ではない（worklog 20261004 §10）。形＝{\"RSI\": [{\"kind\": \"int\", \"lo\": 2, \"hi\": 21}]}（軸＝名前の {} の数だけ並べる・kind は int か float・float は dec で小数の桁数）。使い方の出どころ＝まこさんの逐語 2026-08-07（engine_tuner_defects.md の D14 ⑥）「閾値は指標によって様々な値になるので、範囲で検索すると膨大な量になるはずなので、最初は疑似シミュである程度値を絞って、その後、engine_tunerで最適化する際は、疑似シミュで出た値の前後あたりで範囲を事前に指定して（例えば３０〜５０の間とか）探す、という使い方を想定している」。★ここに書いた範囲は 材料カタログの数字を含まなくてよい（狭めるのが目的）。範囲の外の数字は検証器（G6）が止める。",

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:150「"_material_param_ranges_note": "指標のパラメータの範囲（段A の A-4・2026-08-13 新設）。★2026-10-06（工事 m2c15-param-values-20261006・全体の表の P-2」
状態: 確定

#### 実装 13
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 430行（_mat_from_col・修正1＝_mat_from_col の説明の文を事実に合わせる（範囲を照らすのは _group_usable_col））
直す前の文字:
~~~
    ★範囲を狭めていない＝成績表は材料カタログの数字で作られており、範囲の中に在る。

~~~
直した後の文字:
~~~
    ★成績表は前のカタログの数字で作られているので、列の数字が範囲の外のことがある（ROC3・ROC6 ほか）。
      この関数は範囲を照らさない。段の候補では _group_usable_col が範囲の外の列を外す（監査 CP63 の修正1・2026-10-07）。

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:430「★範囲を狭めていない＝成績表は材料カタログの数字で作られており、範囲の中に在る。」
状態: 確定

#### 実装 14
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 462〜463行（_group_usable_col・修正1＝_group_usable_col が、列の数字が範囲の外なら段の候補に使わない）
直す前の文字:
~~~
        m = _mat_from_col(col, family, tf, ranges, table=table)
    except SampleError:

~~~
直した後の文字:
~~~
        m = _mat_from_col(col, family, tf, ranges, table=table)
    except SampleError:
        return False
    # ★2026-10-07（監査 CP63 の修正1・まこさん「全部直す」＝案 A）＝その列の数字が範囲の外なら、段の候補に使わない。
    #   直す前は禁止3（標本不足）だけを見ていた。成績表（material_ranking.json）は前のカタログの数字で作られているので、
    #   範囲の外の列（ROC3・ROC6 ほか）が順位に残り、案を作った後の出どころの検査（assert_provenance の param_in_range）で止まった。
    if not param_in_range(family, m["param"], ranges)[0]:

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:462「m = _mat_from_col(col, family, tf, ranges, table=table)」
状態: 確定

#### 実装 15
対象のファイル: .claude/breaks/b140_group_range_ignored.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 段の候補が列の数字の範囲を見ない形に戻すと、軽い口の⑭が落ちる
# EXPECT_MSG: ❌ 修正1:
# b140_group_range_ignored — 段の候補が列の数字の範囲を見ない形に戻すと、軽い口の⑭が落ちる（工事 m2c15-param-values-fix-20261007・2026-10-07）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）
#   壊し方＝scripts/priority_rebuild/engine_tuner_gen.py の中の、下の old を new に置き換える（r4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ 修正1:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/engine_tuner_gen.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    if not param_in_range(family, m["param"], ranges)[0]:\n        return False\n'
new = '    if False and not param_in_range(family, m["param"], ranges)[0]:\n        return False\n'
if s.count(old) != 1:
    raise SystemExit("[b140_group_range_ignored] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b139_range_excludes_keep.sh:1「#!/bin/bash」
状態: 確定

#### 実装 16
対象のファイル: .claude/breaks/b141_catalog_out_of_range.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: T3 の範囲の上限を、カタログの数字 50・200 を含まない 34 に戻すと、範囲の番人（⑬）が落ちる
# EXPECT_MSG: ❌ P-2: close vs T3%
# b141_catalog_out_of_range — T3 の範囲の上限を、カタログの数字 50・200 を含まない 34 に戻すと、範囲の番人（⑬）が落ちる（工事 m2c15-param-values-fix-20261007・2026-10-07）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）
#   壊し方＝scripts/priority_rebuild/recipes/search_limits.json の中の、下の old を new に置き換える（r4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ P-2: close vs T3%」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/recipes/search_limits.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "close vs T3%": [{"kind": "int", "lo": 8, "hi": 200}],\n'
new = '    "close vs T3%": [{"kind": "int", "lo": 8, "hi": 34}],\n'
if s.count(old) != 1:
    raise SystemExit("[b141_catalog_out_of_range] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b139_range_excludes_keep.sh:1「#!/bin/bash」
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 16 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 新しい工事名にする | 前の工事に指示を足すと、前の17件の直した後の文字の塊の中を書き替え、設計書を作る道具の照らし（gen_acceptance.py の impl_before_problems）が止まる（まこさん「全部OK」） | 前の工事の 4-20 に足す |
| 2 | 修正4・6 は、範囲を作る道具（apply_param_rule.py）の元から直す | 監査の案 A（軸の対応で入れ替える）だけでは、混ぜた後の最小〜最大を入れ替えるだけで、重なりが残る（まこさん「OK」） | 案を作る道具の対応だけを直す |
| 3 | 一覧に入らない種類も、カタログの数字が範囲の外なら範囲を広げて含める | まこさん決定 2026-10-04 の①（範囲を広げて含める）と同じ型。広げないと、engine_tuner はその列を使えない（いま当たるのは T3） | 範囲の外のままにする（監査の案 C） |
| 4 | 修正1 の番人は、軽い口に⑭として置く | 承認の前に完成の条件のコマンドを私が走らせられる（engine_tuner_gen.py の口は、承認の前は設計↔実装ゲートが止める） | engine_tuner_gen.py の selftest_stages に置く |
| 5 | ⑭は範囲を渡さず（None）に呼ぶ | 自己テストの中で範囲の表を読む呼び出しを足すと、マイルストーンの差し込み（法則の表を読む所の数）が変わる（写しで 64 → 65件になった） | material_ranges() を呼んで渡す |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=f32370711deec5ee gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b140_group_range_ignored.sh` | #1 | _group_usable_col の範囲の照らしを外す |
| `b141_catalog_out_of_range.sh` | #2 | T3 の範囲の上限を、カタログの数字 50・200 を含まない 34 に戻す |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | MACD と TSI の3種は、範囲の中に短い方が長い方以上になる組が在る | 工事2 で「短い方 < 長い方」の決まりを探す側に入れる（3-1 の1行目） |
| 2 | 名前の軸の対応（21種）は私が決めた | 根拠の表を設計書に載せ、監査で確かめていただく（4-0 の④） |
| 3 | 範囲の上限が 200 に広がる種類（4-0 の③の表）の 200 は、調べた時のカタログの数字（20・50・200）から来ている | まこさんが OK した選び方（見つかった値と今の値の最小〜最大）の文どおり。狭めるのは まこさんが決める（この設定の行を書き換える） |
| 4 | 段の候補で、範囲の外の列が外れる | 監査 CP63 の修正1 の案 A。M2-F の段の本走で確かめる（4-13 の2） |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（--design） | 1分未満 | 前の工事で、当てる道具は1秒未満で終わった |
| 全体の自己テスト | 123秒 | 4-14 |
| 軽い口と壊すプログラム | 軽い口1回 8秒 | 写しで壊し方を並べて走らせた（r4_draft_build.py の [8]） |
| G-1 の表の作り直し | 約1分 | 前の工事の実測（表を作る道具の合計） |
| 監査に出す前のチェック | 約9分 | 前の工事の実測（pre_audit_check.py --run） |
| まこさんの承認 | 設計書は1回の見込み。型の表が変われば再承認が1回 | 4-4 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝①前の工事の設計書で、段の候補を範囲で絞ると書いたが、_group_usable_col を開いて確かめずに書いた（監査 CP63 の Process-1）。②範囲を作る道具が、今の値を資料の軸の順にそろえずに混ぜ、軸の数が違う今の値を捨てていた。③範囲を広げる決まりと軽い口の⑬が、一覧に在る種類だけを見ていた。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。段の候補が、出どころの検査で止まる列を先に外すようになります。

**③ root か symptom か**＝root です。範囲を作る道具の元を直し、段の候補の絞りに範囲の照らしを入れ、番人で確かめます。

**④ ベースアップ**＝監査 CP63 の結果・前の工事の設計書と やることの表・ライブラリの実物（pandas_ta_classic の tsi.py）・修正対応表。新しい Web の調べはしていません。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。範囲は、修正対応表（調べた資料から道具が写した表）から道具が写しました。⑭が使う ROC3・ROC12 は、監査 CP63 が挙げた列の名前で、自己テストの入力です。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝監査 CP63 の修正1・4・6 で、探す範囲と段の候補の範囲の照らしを、実物で成り立たせる。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。条件をつなぐものではなく、範囲と段の候補の絞りの直しです |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 範囲が1点だった 5種類が範囲になり、点の一覧で限定する所は減ります。範囲の数字は修正対応表から道具が写しました |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **TSI の軸の順が正しいかを、番人が見るか** | 見ません。⑬は範囲がカタログの数字を含むかだけを見ます（直す前の TSI の範囲でも、カタログの TSI(12,26,9) は中に在った）。軸の順は、道具の対応（4-0 の④）と監査で確かめます |
| **番人は、範囲の数字が修正対応表と同じかを見るか** | 見ません。範囲がカタログの数字を含むかだけを見ます（写しの道具が、当てる前に修正対応表から写しました） |
| **⑭は、段の候補の全部の列を照らすか** | 照らしません。範囲の外の列（ROC3）と中の列（ROC12）の2つで、_group_usable_col の働きを見ます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=03f0172a5c3efa63 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝observe_diag.py・observe_config.json・search_limits.json・engine_tuner_gen.py と、新しい壊すプログラムを【7-8】に書いた。主なファイルは observe_diag.py（番人）と engine_tuner_gen.py（段の候補）。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝observe_diag.py）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム（NEW_FILE）。手本は b139（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝前の工事は、関数を開かずに「範囲で絞る」と設計書に書いた（監査 CP63 の Process-1）。この工事は、_group_usable_col を開いて直し、写しで⑭が働くことを確かめた。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | この工事は、新しい部品も前処理も足さない。計算式は変えず、列の値は直す前と同じ。当てた後に H2 を取り直す。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | engine_tuner_gen.py は、_group_usable_col に5行（説明の3行と照らしの2行）を足し、_mat_from_col の説明の1行を2行にする。その行より後ろの行番号を指す文書は動く（設計書の CODEREF は道具が作り直す）。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、探す文字の数が当てる前と後で同じことを道具が数えた（4-13 の5）。走らせるコマンドの旗は変えない。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムが測るのは observe_diag.py --selftest-catalog で、軽い口は決まった式で作った値動きと設定だけを使い、ファイルに書かない。本物の結果の置き場には書かない。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 新しく足す関数は無い。触る関数は全部 DESIGN_CONTRACT の impl_functions に書いた（道具が当てる前と後の構文木で数えた）。must_use の名前は、当てた後の関数の中に在ることを道具が ast で照らした。observe_diag.py の触る関数＝selftest_catalog。engine_tuner_gen.py の触る関数＝_group_usable_col・_mat_from_col。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足すコマンドの旗は無い。番人は、完成の条件が走らせる軽い口（--selftest-catalog）の中で全部 通る。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2c15-param-values-fix-20261007）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝軽い口の番人（⑬・⑭と、前の工事までの番人）と、壊すプログラム（わざと壊して落ちるか）。写しで走らせ、全部 通った。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | F-1＝段の候補は、列の数字が範囲の外なら使わない・範囲の中なら使う | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | _group_usable_col の範囲の照らしを外す | `b140_group_range_ignored.sh` | — | **未着手** |
| 2 | F-6＝設定の範囲が、カタログの列の数字を全部 含む | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | T3 の範囲の上限を、カタログの数字 50・200 を含まない 34 に戻す | `b141_catalog_out_of_range.sh` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=692c1c216dda90af gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/observe_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `selftest_catalog` | 7011 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 180件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=2eacd0c0c5c4c574 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/observe_diag.py",
  "_impl_file の意味": "照らす相手は実在するファイル。この工事の番人（軽い口の⑬・⑭）が在る、観察の道具を照らす。段の候補の直し（engine_tuner_gen.py）は impl_functions で照らす。",
  "impl_functions": {
    "scripts/priority_rebuild/observe_diag.py": [
      "selftest_catalog"
    ],
    "scripts/priority_rebuild/engine_tuner_gen.py": [
      "_group_usable_col",
      "_mat_from_col"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数（実装の指示を全部 当てる前と後の構文木を関数ごとに比べて、r4_proposal_build.py が数えた）。",
  "self_check_calls": [
    "selftest_catalog"
  ],
  "_self_check_calls の意味": "実装の後の observe_diag.py に在るはずの、この工事が触る関数の名前。",
  "must_use": {
    "selftest_catalog": [
      "build_catalog",
      "load_config",
      "find_material"
    ]
  },
  "_must_use の意味": "軽い口が呼ぶ関数（r4_proposal_build.py が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は、範囲の設定と段の候補の絞りを直すだけ。外から読む一覧の形（カタログの1件の形・参照表の欄）は変えない。",
  "generated_from": {
    "impl_functions": "当てる前と後の関数ごとの構文木の差（r4_proposal_build.py が数えた）",
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

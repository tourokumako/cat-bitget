<!-- ARC iter="g2-table-range-source-20261010" -->

# 設計書｜値を探すプログラムの自己テストが、本走が止まった理由を出して、後ろの検査へ進む形に直す。監査 CP69 の修正1 の一部

TARGET: scripts/priority_rebuild/engine_tuner_gen.py, .claude/hooks/require_design_contract_before_run.sh, .claude/breaks/b159_selftest_run_passthrough.sh
NEW_FILE: .claude/breaks/b159_selftest_run_passthrough.sh
MODEL: .claude/breaks/b127_stage_q_rank_off.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `g2-table-range-source-20261010/ok_g2r_20261010`・`g2-table-range-source-20261010/okd_g2r_20261010`・`g2-table-range-source-20261010/req_stopnote_20261010`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/g2-table-range-source-20261010/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work g2-table-range-source-20261010 --write`。検出＝`--work g2-table-range-source-20261010 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=7c58bdaa39d6a6eb gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/g2-table-range-source-20261010/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/g2-table-range-source-20261010/ok_g2r_20261010.txt`（まこさんの発言）・`verbatim/g2-table-range-source-20261010/okd_g2r_20261010.txt`（まこさんが OK した CC の文）・`verbatim/g2-table-range-source-20261010/req_stopnote_20261010.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝421 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_g2r_20261010` | V01〜V11（11 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_g2r_20261010` | V01〜V14（14 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_g2r_20261010` | V15〜V27（13 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V28〜V32（5 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V33〜V37（5 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V38〜V51（14 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V52〜V59（8 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V60〜V67（8 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V68〜V77（10 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V78〜V79（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V80〜V81（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V82〜V83（2 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V84〜V85（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V86〜V87（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V88〜V100（13 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V101〜V116（16 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V117〜V121（5 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V122〜V123（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V124〜V125（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V126〜V127（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V128〜V133（6 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V134〜V268（135 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V269〜V277（9 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V278〜V283（6 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V284〜V292（9 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V293〜V299（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V300〜V301（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V302〜V303（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V304〜V308（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V309〜V319（11 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V320〜V340（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V341〜V344（4 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V345〜V403（59 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_g2r_20261010` | V404〜V407（4 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `req_stopnote_20261010` | V01〜V03（3 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
値を探すプログラム（engine_tuner_gen.py）の全体の自己テストは、いま、文を1行も出さずに終了コード 1 で終わります（監査 CP69 の所見 MJ-1）。自己テストの中の検査 T6 が小さい本走を呼び、その本走が型の表との照らしでプログラムごと終わるためです。本走の出す文は受け皿に入れてあるので、理由の行は画面に出ずに捨てられます。T6 より後ろの検査も走りません。この工事は、自己テストの中で本走を呼ぶ所を1つの口にまとめ、本走が止まったら、理由の行を失敗の一覧に入れて、後ろの検査へ進む形に直します（まこさん「→これはやる」）。後ろの検査の中で、見本の数字が探す範囲の外になっていた1か所（T22）も直します。本走が止まる原因そのものは、この工事では直しません（やることリストの M2-E-8）。自己テストは、失敗の検査を失敗のまま出します。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 自己テストの中で本走を呼ぶ口（F-1） | `grep -n -F 'def _selftest_run(fn, *bufs):' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 実装の前は、無い。実装の後は、在る | （終了コード 1） |
| T6 がミニ本走を直に呼ぶ行（F-2） | `grep -n -F 'out1 = run_generation(df, **kw)' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 実装の前は、在る。実装の後は、無い | 5640:                out1 = run_generation(df, **kw)（終了コード 0） |
| T22 の見本の材料が ROC 6 の行（F-3） | `grep -n -F '_lv22("ROC", 6, "5m", "q50")' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 実装の前は、在る。実装の後は、無い | 6457:                _lv22("ROC", 6, "5m", "q50"),（終了コード 0） |
| 短い口の旗（F-4） | `grep -n -F '"--selftest-stop-note"' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 実装の前は、無い。実装の後は、在る | （終了コード 1） |

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
| 1 | T6・T29・T10 を通す直し（最初の段階を代表の値で組む・最後の段階でパラメータを動かす） | やることリストの M2-E-8。指標の修正の最後に固まる表と範囲を読むので、指標の修正が全部 済んだ後 | next_step の「毎回 必ず読むこと」の4・6 |
| 2 | 型の表との照らしを緩める直し | 探し方の決定と逆の向き | next_step の「毎回 必ず読むこと」の6 |
| 3 | まとめの文のうち、T29 の行と、T5〜T8・T12 の行を直すこと | 検査の説明を毎回 同じ文で出す作り（前から）。失敗は末尾の一覧に出る | 写しの4回目の走行 |
| 4 | 監査に出す前のチェックの自己テストの P7-1 の失敗 | この工事の前から在る | session_worklog_20261007.md |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | hook（設計↔実装ゲート）の通す旗の一覧に、短い口 --selftest-stop-note を足すこと | 足す。旗は完全一致で見るので、足さないと CC がこの口を打って確かめられない | require_design_contract_before_run.sh の旗の一覧の説明 |
| 2 | 完成の条件を、全体の自己テストでなく、短い口で見ること | 短い口で見る。全体の自己テストは、承認の前の検査の打ち切りを超え、T6 が失敗のままなので終了コードも 0 にならない | require_design_check_before_approval.py の A12・写しの実測 |
| 3 | T22 の見本の数字 | 資料の表の ROC の行の、最初の値（既定）に在る数字にする | .claude/state/indicator_params_by_strategy.md の ROC の行 |
| 4 | 目的の照合（purpose_check.md）の条件の書き方 | 事実だけを書く。指標・閾値・時間足・パラメータは、どれも「今のまま」（自己テストの中の本走の呼び方と、見本の数字を直す。探す所は直さない） | 工事 g2-sentinel-material-pick-20261007 の 3-2 |
| 5 | 監査の出し方 | この工事の実装の監査の依頼書を1通 作る。出す時は まこさんが決める | 恒久64番・next_step の「毎回 必ず読むこと」の9 |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、値を探すプログラム（engine_tuner_gen.py）の自己テストの中で、本走を呼ぶ所の作りを直す工事です。**自己テスト（--selftest）は、作り物のデータで、案を作る所から判定表までを通しで試す検査です。その中の3つの検査（T6・T29・T10）は、小さい本走（run_generation）を実際に呼びます。
**①いま何が起きているか。**
- 本走の中には、作った案を型の表と照らす所が在ります。沿わない案が1本でも在ると、プログラムごと終わります（SystemExit）。
- 自己テストは、本走が画面に出す文を受け皿に入れています。本走がプログラムごと終わると、受け皿の文は捨てられます。
- そのため、T6 で自己テストの全部が終わり、止まった理由が1行も出ません。T6 より後ろの検査は1本も走りません（監査 CP69 の所見 MJ-1）。
- 後ろの検査の中に、別の原因で止まる所が1つ在りました。T22 の見本の材料 ROC 6 が、いまの探す範囲の外です（写しの3回目の走行で見つけた）。
**②この工事で何が変わるか。**
- F-1：自己テストの中で本走を呼ぶ口（_selftest_run）を1つ作ります。本走が途中で止まったら、止まる前に出た文から理由の行を取り出して知らせます。
- F-2：T6・T29・T10 は、その口を通して本走を呼びます。止まったら、理由を失敗の一覧に入れて、後ろの検査へ進みます。T6 の結果を使う T12 の検査は「走らせていない」と失敗の一覧に入れます。
- F-3：T22 の見本の材料を、いまの範囲の中の数字にします。
- F-4：口の既知答え（T50）を足します。全体の自己テストと、短い口（--selftest-stop-note）が、同じ本体を呼びます。
- **T6・T29・T10 は失敗のままです。**終了コードも 1 のままです。本走が止まる原因（最初の段階が範囲から選んだ数字を、型の表との照らしが止める）は、この工事では直しません（やることリストの M2-E-8）。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、apply_audit_fix.py と、engine_tuner_gen.py の --selftest・--selftest-stop-note を動かします。承認の前の検査と壊すプログラムは、短い口を動かします。
**誰が結果を使うか。**
- 自己テストの画面の出力を、私（CC）と監査が読みます。失敗の一覧に、本走が止まった理由の行が出ます。
- 売買を回すプログラムも、本走も、この直しの結果を読みません。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**今の実物（engine_tuner_gen.py・hook の require_design_contract_before_run.sh）・設計書の 4-20。
**書くもの。**
- 当てる（--design）：engine_tuner_gen.py の 11か所・hook の1か所・新しい壊すプログラム 1本。
- 自己テストと短い口は、画面に文を出すだけです。案も成績表も売買記録も書きません。累積の試行数にも足しません。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 照らす側を緩めない・最初の段階の作りを直さない | next_step の「毎回 必ず読むこと」の6・まこさん 2026-10-10「→これはやる」の範囲 | 型の表との照らし（gen_signal_families.py の check_structures）と、案を作る所には触りません。触るのは、自己テストの中で本走を呼ぶ所だけです |
| 乱数を新しく足さない | 恒久67番 | 乱数は足しません |
| 作ってはいけないもの1番・2番 | 要件 | 案を作る所・探す値には触りません |
| 未来のデータを使わない | 要件定義書 §4.6.H2 | 材料の計算は変えません。当てた後に H2 を取り直します |
| 値段の高さで値が変わらない | 要件定義書 §4.6.H6 | 材料の計算は変えません |
| 数字を CC が作らない | 思考の順の7（req_thinking_20261004） | 新しい数字は、T22 の見本の 12 の1つです。資料の表の ROC の行の最初の値（既定）に在る数字で、いまの探す範囲の中です。探す値ではなく、検査の見本です |
| 失敗を成功に見せない | 恒久64番 | T6・T29・T10 は失敗のまま出します。終了コードも 1 のままです |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| engine_tuner_gen.py の _selftest_run | 自己テストの中で本走を呼ぶ。本走が途中で止まったら、理由の行を持たせて知らせる。ほかの例外は握りつぶさない | 新設 |
| engine_tuner_gen.py の _stop_note | 止まる前に画面へ出た文から、理由の行（[G2] の行・❌ の行の数・1件目）を取り出す | 新設 |
| engine_tuner_gen.py の selftest_stop_note | 口の既知答え（T50・4件） | 新設 |
| engine_tuner_gen.py の selftest | T6・T29・T10 が口を通して本走を呼ぶ。T12 とまとめの文は、止まったときに結果を使わない。T22 の見本の数字。最後に T50 を呼ぶ | 直す |
| engine_tuner_gen.py の main | 短い口 --selftest-stop-note | 直す |
| hook の require_design_contract_before_run.sh | 通す旗の一覧に、短い口を1つ足す | 直す |
| .claude/breaks の壊すプログラム | 口を、本走が止まるとプログラムごと終わる形に戻すと、短い口が決めた文で失敗するかを見る | 新設 |
- 触る関数は、指示を当てる前と後の構文木を比べて、プログラムが数えました（下の囲み）。
```
engine_tuner_gen.py＝_selftest_run・_stop_note・main・selftest・selftest_stop_note
```

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. まこさんの承認の後、全部を当てます（apply_audit_fix.py --design --dry → --design）。1件でも合わなければ1件も当てません。
2. 同じ時に、監査 CP69 の修正8・9（gen_signal_families.py の説明の文2か所）を、監査の結果から当てます（apply_audit_fix.py --report）。これは、この設計書の指示ではありません。型の表の再承認を1回にするために、同じ時に当てます。
3. 型の表を作り直します（gen_signal_families.py --write）。まこさんに再承認（--approve）をお願いします。
4. 材料の文書とオン・オフの表を作り直します（監査に出す前のチェックの順番のとおり）。engine_tuner_gen.py の行が下がるので、行番号を持つ材料の文書を作り直す必要が在ります。
5. G2 → H2 を取り直します。
6. 照合（verify_design_contract.py --diff）をかけ、壊すプログラムを測ります（run_breaks.py --design --measure-only）。
7. 監査に出す前のチェック（pre_audit_check.py --run）を走らせます。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝いまの自己テスト。T6 が小さい本走を呼びます。本走は案を10本 作り、型の表と照らします。沿わない案が在るので、本走はプログラムごと終わります。自己テストは、その場で終了コード 1 で終わり、画面には何も出ません。直した後は、T6 が口を通して本走を呼びます。本走が終わろうとすると、口が受け、止まる前に出た文から「[G2] 表に沿っていた構造 …」の行と、❌ の行の数と、1件目の ❌ の行を取り出します。T6 は、それを「T6: ミニ本走が途中で止まった＝…」として失敗の一覧に入れ、次の検査へ進みます。T29 と T10 も同じです。T12 は「T6 のミニ本走が途中で止まったので…走らせていない」を失敗の一覧に入れます。T22 は、見本の材料が範囲の中になったので、止まらずに通ります。最後に T50（口の既知答え）が走り、末尾に失敗の一覧が出ます。終了コードは 1 のままです。この流れは、完成の条件のコマンド（短い口）では通りません。そこで、4-4 の手順を全部 終えた後に、全体の自己テスト（engine_tuner_gen.py --selftest）を本物で1回 走らせ、最後の検査（T50）まで届くことと、失敗の一覧の行を、作業の記録に書きます。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**変えません。**探す範囲の設定（search_limits.json）にも、案を作る関数にも触りません。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**設定ファイルは変えません。**コマンドの旗を1つ足します（--selftest-stop-note）。hook の通す旗の一覧にも同じ1つを足します。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**
1. 短い口が通る。コマンド＝python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest-stop-note。画面に「✅ T50 本走を呼ぶ口（途中で止まった理由を知らせる）／ダメだった件 0」が出る。
2. 壊すプログラムが、決めた文（❌ T50: ①）を出して失敗する。コマンド＝python3 .claude/tools/run_breaks.py --design。
3. 全体の自己テストが、最後の検査（T50）と、末尾の失敗の一覧まで届く。失敗の一覧に、T6・T29・T10 の「本走が途中で止まった＝（理由の行）」が出る。写しで測ったときの失敗の一覧は、下の囲みの 6行でした。
```
❌ T6: ミニ本走が途中で止まった＝[G2] 表に沿っていた構造 2/10（20%） ／ 照合できた材料 合計 74 個 ／ ❌ の行 8 件 ／ 1件目＝❌ 構造#1: 部品 CCI11 のパラメータが表の範囲の外（CCI の 1 番目の数字 11 が範囲の外（20.0〜20.0・出どころ＝approved_tab
❌ T29: 本走が途中で止まった＝[G2] 表に沿っていた構造 2/10（20%） ／ 照合できた材料 合計 74 個 ／ ❌ の行 8 件 ／ 1件目＝❌ 構造#1: 部品 CCI11 のパラメータが表の範囲の外（CCI の 1 番目の数字 11 が範囲の外（20.0〜20.0・出どころ＝approved_tabl
❌ T10: 本走が途中で止まった＝[G2] 表に沿っていた構造 2/10（20%） ／ 照合できた材料 合計 74 個 ／ ❌ の行 8 件 ／ 1件目＝❌ 構造#1: 部品 CCI11 のパラメータが表の範囲の外（CCI の 1 番目の数字 11 が範囲の外（20.0〜20.0・出どころ＝approved_tabl
❌ T12: T6 のミニ本走が途中で止まったので、実走の第1段で 0玉の案が通過していないかの検査は走らせていない
❌ T13: 対応表・向きの決まりの違反 51 本（例＝#0: 部品 realized_vol15 のパラメータが表の範囲の外（realized_vol の 1 番目の数字 15 が範囲の外（20.0〜50.0・出どころ＝approved_table）））
❌ T13: G2 適合率が100%でない（7/60）
```

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| --design の --dry で、当たらない件が出る | 1件も当てずに止まります。まこさんに報告します |
| 自己テストの中の本走が、途中でプログラムごと終わろうとする | 口が受け、理由の行を失敗の一覧に入れて、後ろの検査へ進みます。その検査は失敗のままです |
| 止まる前の文に、理由の行が無い | 口が「止まる前の文に [G2] の行が無い」と言います。空の理由にしません |
| 本走が、SystemExit でない例外を出す | 口は握りつぶしません。そのまま上へ投げます（T6 は前と同じく自己テストごと止まり、T29 は前から在る受けが「検査が走らない」と記録します） |
| 本物の走行（自己テストでない本走）が、型の表との照らしで止まる | 前と同じく、試行を1本も走らせずに止まります（変えていない） |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**変えません。**検査済みの記録の形も前のままです。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**変えません。**短い口は、ファイルを1つも書きません。

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**変えません。**

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| 短い口（--selftest-stop-note） | 3.5秒 | 写しの実測（g2r_quick.json） |
| 全体の自己テスト（--selftest） | 565秒 | 写しの実測（g2r_full.json）。直す前は T6 で終わっていたので、最後まで走るぶん長くなる |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**ありません。**全部を --design の1回で当てるので、途中の状態は残りません。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しのプログラムだけが書きます。hook は、通す旗の一覧に1つ足すだけで、止める判定は変えません。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**自己テストの画面の出力が変わります。**失敗の一覧に、本走が止まった理由の行が出ます。まとめの文に T50 の1行が増えます。T10 のまとめの文は、本走が止まったときは「本走が途中で止まったので…出ていない」になります。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **engine_tuner_gen.py は G2 と H2 の対象です。**当てた後に G2 → H2 を取り直します。
2. **型の表の中身は、この設計書の指示では変わりません。**同じ時に当てる監査 CP69 の修正8・9 で、説明の文が1行 変わります（4-4 の2・3）。
3. **engine_tuner_gen.py の行が、自己テストの関数より後ろで下がります。**行番号を持つ材料の文書は、作り直します（4-4 の4）。直すファイルの行番号を指している文書を git grep で探しました。足す行より後ろを指す所は、設計書の控え・監査の結果・作業の記録（どれも過去の記録）だけで、法則ファイルとマイルストーンには在りませんでした。
4. **前からの壊すプログラムが探す文字の数は、当てる前と後で同じです。**プログラムが数えた相手は、下の囲みです。
```
33 本（探す文字の数が変わるものは 0 本）
```
5. **承認の前の検査 A12 が走らせる自己テストを、写しで走らせました。**結果は下の囲みです。
```
engine_tuner_exec.py --selftest＝終了コード 0・9.4秒
observe_diag.py --selftest＝終了コード 0・140.1秒
gen_materials.py --selftest＝終了コード 0・79.5秒
gen_audit_request.py --selftest＝終了コード 0・2.5秒
engine_tuner_gen.py --selftest-extra-gate＝終了コード 0・3.0秒
```

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| engine_tuner_gen.py の selftest_stage_q と、口 --selftest-stage-q | 全体の自己テストと短い口が、同じ本体を呼ぶ形 |
| 壊すプログラム b127 | 短い口を測る壊すプログラムの形 |
| r6b_build.py（工事 g2-sentinel-material-pick-20261007 のプログラム） | 指示と壊すプログラムを作り、前からの壊すプログラムの探す文字を数え、一時の置き場で設計書を組む形 |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=8ad7af546567243f gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 5186行（selftest・自己テストの関数の直前（本走を呼ぶ口 _selftest_run・理由の行を取り出す関数・既知答えを足す））
直す前の文字:
~~~
def selftest() -> int:

~~~
直した後の文字:
~~~
class _RunStopped(Exception):
    """自己テストの中の本走が、途中で止まった（文＝止まる前に画面へ出た理由の行）。自己テストだけが使う。"""


def _stop_note(text: str) -> str:
    """本走が途中で止まったとき、止まる前に画面へ出た文から、理由の行を短く取り出す（自己テストだけが使う）。"""
    _ls = [x.strip() for x in text.splitlines()]
    _bad = [x for x in _ls if x.startswith("❌")]
    _g2 = [x for x in _ls if x.startswith("[G2] 表に沿っていた構造")]
    _head = _g2[-1] if _g2 else "止まる前の文に [G2] の行が無い"
    return f"{_head} ／ ❌ の行 {len(_bad)} 件" + (f" ／ 1件目＝{_bad[0][:200]}" if _bad else "")


def _selftest_run(fn, *bufs):
    """自己テストの中で本走を呼ぶ口（★2026-10-10・工事 g2-table-range-source-20261010・監査 CP69 の修正1）。

    fn が返した物を、そのまま返す。fn が途中でプログラムごと終わろうとしたら（SystemExit）、止まる前に受け皿（bufs）へ
    出た文から理由の行を取り出し、_RunStopped にして投げる。呼ぶ側は、理由を失敗の一覧に入れて、後ろの検査へ進む。
    直す前＝本走の中の型の表との照らしが SystemExit で終わると、受け皿の文が捨てられ、止まった理由が1行も出ないまま、
    自己テストの全部が終了コード 1 で終わっていた（T6 より後ろの検査が1本も走らない）。
    ★受けるのは SystemExit だけ。ほかの例外は握りつぶさず、そのまま上へ投げる。
    """
    try:
        return fn()
    except SystemExit:
        raise _RunStopped(_stop_note("".join(b.getvalue() for b in bufs))) from None


def selftest_stop_note() -> list:
    """本走を呼ぶ口（_selftest_run）の既知答え。戻り＝ダメだった件の一覧（空なら全部 通った）。

    全体の --selftest（T50）と、短い口 --selftest-stop-note が、この同じ本体を呼ぶ（判定を2か所に書き写さない）。
    ★全体の --selftest は、承認の前の仮当ての打ち切り300秒を超える。だから、この枝だけを走らせる口を持つ。
    """
    import io as _io
    out = []
    # ① 途中で止まる本走＝理由の行（[G2] の行・❌ の行の数・1件目）を持った _RunStopped が投げられる
    _b1 = _io.StringIO()

    def _stops():
        _b1.write("[G2] 表に沿っていた構造 見本の行\n❌ 構造#1: 見本の理由\n❌ 構造#2: 見本の理由\n")
        raise SystemExit(1)
    try:
        _selftest_run(_stops, _b1)
        out.append("① 本走が途中で止まったのに、止まったことを知らせない")
    except _RunStopped as _e1:
        _s1 = str(_e1)
        if ("[G2] 表に沿っていた構造 見本の行" not in _s1 or "❌ の行 2 件" not in _s1
                or "1件目＝❌ 構造#1: 見本の理由" not in _s1):
            out.append(f"① 止まった理由の行が欠けている: {_s1}")
    except SystemExit:
        out.append("① 本走が途中で止まると、プログラムごと終わってしまう（理由を知らせていない）")

    # ② 止まらない本走＝fn が返した物が、そのまま返る
    if _selftest_run(lambda: "見本の結果", _io.StringIO()) != "見本の結果":
        out.append("② 止まらない本走の結果が、そのまま返らない")

    # ③ 止まる前の文に [G2] の行も ❌ の行も無い＝そう言う（空の理由にしない）
    def _stops_plain():
        raise SystemExit(1)
    try:
        _selftest_run(_stops_plain, _io.StringIO())
        out.append("③ 本走が途中で止まったのに、止まったことを知らせない")
    except _RunStopped as _e3:
        if "止まる前の文に [G2] の行が無い" not in str(_e3) or "❌ の行 0 件" not in str(_e3):
            out.append(f"③ 止まる前の文に理由の行が無いことを言わない: {_e3}")
    except SystemExit:
        out.append("③ 本走が途中で止まると、プログラムごと終わってしまう（理由を知らせていない）")

    # ④ メタ確認＝SystemExit でない例外は握りつぶさない（そのまま上へ投げる）
    def _raises():
        raise ValueError("見本の例外")
    try:
        _selftest_run(_raises, _io.StringIO())
        out.append("④ SystemExit でない例外（ValueError）が握りつぶされた")
    except _RunStopped:
        out.append("④ SystemExit でない例外（ValueError）が、本走が止まったことにされた")
    except ValueError:
        pass
    return out


def selftest() -> int:

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:5186「def selftest() -> int:」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 5638〜5659行（selftest・自己テスト T6（ミニ本走が止まったら、理由を失敗の一覧に入れて進む））
直す前の文字:
~~~
        try:
            with contextlib.redirect_stdout(buf):
                out1 = run_generation(df, **kw)
            with contextlib.redirect_stdout(buf):
                out2 = run_generation(df, **kw)
            # T6b（2026-08-05 新設）＝確認の走行では累積が1本も増えない
            if _ts.CUMULATIVE.exists():
                ng.append("T6b: 確認の走行なのに累積ファイルが作られた（数えない約束が守られていない）")
        finally:
            _ts.CUMULATIVE, _ts.CHECK_RUNS = _real_cum, _real_chk
        if out2["reused"] != 10:
            ng.append(f"T6: 再開で第1段 10 本が再利用されない（{out2['reused']} 本）")
        a = [(r["idx"], r["total"], r["ok"]) for r in out1["results1"]]
        b = [(r["idx"], r["total"], r["ok"]) for r in out2["results1"]]
        if a != b:
            ng.append("T6: 再開の結果が初走と一致しない（R12 が壊れている）")
        # meta が違う journal は拒否（fail-closed）
        try:
            Journal(run_dir / "journal.jsonl", {"seed": 999})
            ng.append("T6: meta 食い違いの journal が拒否されない")
        except SystemExit:
            pass

~~~
直した後の文字:
~~~
        _stop6 = None                                # ★ミニ本走が途中で止まったときの理由（止まらなければ None）
        try:
            try:
                with contextlib.redirect_stdout(buf):
                    out1 = _selftest_run(lambda: run_generation(df, **kw), buf)
                with contextlib.redirect_stdout(buf):
                    out2 = _selftest_run(lambda: run_generation(df, **kw), buf)
            except _RunStopped as _e6:
                # ★2026-10-10（監査 CP69 の修正1）＝ミニ本走が途中で止まったら、理由を失敗の一覧に入れて、後ろの検査へ進む。
                #   ★T6 は失敗のまま＝終了コードは 1。本走が止まる原因の直しは、ここには入れていない（やることリストの M2-E-8）。
                _stop6 = str(_e6)
            # T6b（2026-08-05 新設）＝確認の走行では累積が1本も増えない
            if _ts.CUMULATIVE.exists():
                ng.append("T6b: 確認の走行なのに累積ファイルが作られた（数えない約束が守られていない）")
        finally:
            _ts.CUMULATIVE, _ts.CHECK_RUNS = _real_cum, _real_chk
        if _stop6 is not None:
            ng.append(f"T6: ミニ本走が途中で止まった＝{_stop6}（再開と journal の検査は走らせていない）")
        else:
            if out2["reused"] != 10:
                ng.append(f"T6: 再開で第1段 10 本が再利用されない（{out2['reused']} 本）")
            a = [(r["idx"], r["total"], r["ok"]) for r in out1["results1"]]
            b = [(r["idx"], r["total"], r["ok"]) for r in out2["results1"]]
            if a != b:
                ng.append("T6: 再開の結果が初走と一致しない（R12 が壊れている）")
            # meta が違う journal は拒否（fail-closed）
            try:
                Journal(run_dir / "journal.jsonl", {"seed": 999})
                ng.append("T6: meta 食い違いの journal が拒否されない")
            except SystemExit:
                pass

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:5638「try:」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 5683〜5686行（selftest・自己テスト T29（本走を、口を通して呼ぶ））
直す前の文字:
~~~
                with _c29.redirect_stdout(_b29):
                    _o29 = run_generation(df, run_dir=_rd29, minimize="TIME_EXIT", **_kw29)
                with _c29.redirect_stdout(_b29b):
                    _o29b = run_generation(df, run_dir=_rd29b, **_kw29)

~~~
直した後の文字:
~~~
                with _c29.redirect_stdout(_b29):
                    _o29 = _selftest_run(lambda: run_generation(df, run_dir=_rd29, minimize="TIME_EXIT", **_kw29), _b29)
                with _c29.redirect_stdout(_b29b):
                    _o29b = _selftest_run(lambda: run_generation(df, run_dir=_rd29b, **_kw29), _b29b)

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:5683「with _c29.redirect_stdout(_b29):」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 5719〜5720行（selftest・自己テスト T29（本走が止まったら、理由を失敗の一覧に入れて進む））
直す前の文字:
~~~
    except Exception as _e29:
        t29.append(f"検査が走らない: {type(_e29).__name__} {_e29}")

~~~
直した後の文字:
~~~
    except _RunStopped as _e29s:
        # ★2026-10-10（監査 CP69 の修正1）＝本走が途中で止まったら、理由を失敗の一覧に入れて、後ろの検査へ進む。
        t29.append(f"本走が途中で止まった＝{_e29s}")
    except Exception as _e29:
        t29.append(f"検査が走らない: {type(_e29).__name__} {_e29}")

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:5719「except Exception as _e29:」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 5780〜5798行（selftest・自己テスト T10（本走が止まったら、理由を失敗の一覧に入れて進む））
直す前の文字:
~~~
        try:
            with _ctx10.redirect_stdout(_io10.StringIO()):
                # ★T6 と同じ種と本数を使う（この合成データで材料が組み立てられることが確認済みの経路）
                out10 = run_generation(df, limits=lm, judge=judge, start=s4, end=e4,
                                       trials1=10, trials2=0, top_k=2, seed=11, run_dir=rd10,
                                       pool=pool, tfs=tfs_small, catalog_total=cat_total,
                                       purpose=_ts10.PURPOSE_CHECK, tag="t10",
                                       df_confirm=df, confirm_start=s4, confirm_end=e4,
                                       base=None)
        finally:
            globals()["build_qtable"] = _real_qt
            _ts10.CUMULATIVE, _ts10.CHECK_RUNS = _rc, _rk
            _tj10.JUDGE_DIR = _jd
        if _calls["n"] != 1:
            t10.append(f"① 分位の解決表を {_calls['n']} 回 作った（確認窓では作り直さない＝1回のはず）")
        if out10.get("kept") and out10.get("verdict") is None:
            t10.append("② 通った構造が在るのに判定表を出していない")
        if out10.get("verdict") == _tj10.PASS:
            t10.append("② 土台が無いのに『これ以上出ない』と出た（偽装の✅）")

~~~
直した後の文字:
~~~
        _b10 = _io10.StringIO()
        _stop10 = None                               # ★本走が途中で止まったときの理由（止まらなければ None）
        try:
            try:
                with _ctx10.redirect_stdout(_b10):
                    # ★T6 と同じ種と本数を使う（この合成データで材料が組み立てられることが確認済みの経路）
                    out10 = _selftest_run(lambda: run_generation(
                        df, limits=lm, judge=judge, start=s4, end=e4,
                        trials1=10, trials2=0, top_k=2, seed=11, run_dir=rd10,
                        pool=pool, tfs=tfs_small, catalog_total=cat_total,
                        purpose=_ts10.PURPOSE_CHECK, tag="t10",
                        df_confirm=df, confirm_start=s4, confirm_end=e4,
                        base=None), _b10)
            except _RunStopped as _e10:
                # ★2026-10-10（監査 CP69 の修正1）＝本走が途中で止まったら、理由を失敗の一覧に入れて、後ろの検査へ進む。
                _stop10 = str(_e10)
        finally:
            globals()["build_qtable"] = _real_qt
            _ts10.CUMULATIVE, _ts10.CHECK_RUNS = _rc, _rk
            _tj10.JUDGE_DIR = _jd
        if _stop10 is not None:
            t10.append(f"本走が途中で止まった＝{_stop10}（①②の検査は走らせていない）")
        else:
            if _calls["n"] != 1:
                t10.append(f"① 分位の解決表を {_calls['n']} 回 作った（確認窓では作り直さない＝1回のはず）")
            if out10.get("kept") and out10.get("verdict") is None:
                t10.append("② 通った構造が在るのに判定表を出していない")
            if out10.get("verdict") == _tj10.PASS:
                t10.append("② 土台が無いのに『これ以上出ない』と出た（偽装の✅）")

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:5780「try:」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 5888〜5890行（selftest・自己テスト T12（T6 が止まったときは、T6 の結果を使う検査を走らせていないと記録する））
直す前の文字:
~~~
    z_bad = [r for r in out1["results1"] if r["n"] == 0 and r["ok"]]
    if z_bad:
        t12.append(f"実走（T6 のミニ本走）の第1段で 0玉の案が {len(z_bad)} 本 通過している")

~~~
直した後の文字:
~~~
    if _stop6 is not None:
        # ★2026-10-10（監査 CP69 の修正1）＝T6 のミニ本走が止まったときは、その結果を使う検査を「走らせていない」と失敗の一覧に入れる。
        t12.append("T6 のミニ本走が途中で止まったので、実走の第1段で 0玉の案が通過していないかの検査は走らせていない")
    else:
        z_bad = [r for r in out1["results1"] if r["n"] == 0 and r["ok"]]
        if z_bad:
            t12.append(f"実走（T6 のミニ本走）の第1段で 0玉の案が {len(z_bad)} 本 通過している")

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:5888「z_bad = [r for r in out1["results1"] if r["n"] == 0 and r["ok"]]」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 6398〜6399行（selftest・自己テストのまとめの T10 の文（T10 が止まったときは、結果を使う文を出さない））
直す前の文字:
~~~
    print(f"  T10 判定表の接続: 分位の解決表は {_calls['n']} 回だけ作った（確認窓では作り直さない）／"
          f"土台なしの結論 {out10.get('verdict')}（『これ以上出ない』ではない）")

~~~
直した後の文字:
~~~
    if _stop10 is not None:
        # ★2026-10-10（監査 CP69 の修正1）＝T10 の本走が止まったときは、その結果を使うまとめの文を出さない。
        print("  T10 判定表の接続: 本走が途中で止まったので、分位の解決表の回数と結論は出ていない（下の ❌ の行を見る）")
    else:
        print(f"  T10 判定表の接続: 分位の解決表は {_calls['n']} 回だけ作った（確認窓では作り直さない）／"
              f"土台なしの結論 {out10.get('verdict')}（『これ以上出ない』ではない）")

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:6398「print(f"  T10 判定表の接続: 分位の解決表は {_calls['n']} 回だけ作った（確認窓では作り直さない）／"」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 6457行（selftest・自己テスト T22 の見本の材料（ROC 6 → ROC 12＝いまの範囲の中））
直す前の文字:
~~~
                _lv22("ROC", 6, "5m", "q50"),

~~~
直した後の文字:
~~~
                _lv22("ROC", 12, "5m", "q50"),

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:6457「_lv22("ROC", 6, "5m", "q50"),」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 6461行（selftest・自己テスト T22 の待つ鍵（ROC6__5m → ROC12__5m））
直す前の文字:
~~~
    _want22 = {"入口のふつうの条件": "ROC6__5m", "状態を保つ形の中": "ADX14__15m",

~~~
直した後の文字:
~~~
    _want22 = {"入口のふつうの条件": "ROC12__5m", "状態を保つ形の中": "ADX14__15m",

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:6461「_want22 = {"入口のふつうの条件": "ROC6__5m", "状態を保つ形の中": "ADX14__15m",」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 7888〜7890行（selftest・自己テストの最後（口の既知答え T50 を呼ぶ））
直す前の文字:
~~~
    print("  T44・T49 段2a: ①分位を書いた設定で順位が通し番号（材料の順 → 分位の順） ②系統を絞った設定で組むと C に abs ／ abs の鍵が作れる")

    if ng:

~~~
直した後の文字:
~~~
    print("  T44・T49 段2a: ①分位を書いた設定で順位が通し番号（材料の順 → 分位の順） ②系統を絞った設定で組むと C に abs ／ abs の鍵が作れる")
    # ══ T50（2026-10-10・工事 g2-table-range-source-20261010）＝本体は selftest_stop_note（口 --selftest-stop-note と同じ1本）══
    t50 = selftest_stop_note()
    ng += [f"T50: {_x}" for _x in t50]
    print("  T50 本走を呼ぶ口: ①途中で止まると理由の行つきで知らせる ②止まらなければ結果をそのまま返す ③理由の行が無ければそう言う ④ほかの例外は握りつぶさない")

    if ng:

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:7888「print("  T44・T49 段2a: ①分位を書いた設定で順位が通し番号（材料の順 → 分位の順） ②系統を絞った設定で組むと C に abs ／ abs の鍵が作れる")」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 8084〜8085行（main・コマンドの入口（短い口 --selftest-stop-note を足す））
直す前の文字:
~~~
    a = ap.parse_args()
    if a.selftest_stage_q:

~~~
直した後の文字:
~~~
    ap.add_argument("--selftest-stop-note", action="store_true",
                    help="自己テストの中で本走を呼ぶ口（_selftest_run）だけを試す＝T50 と同じ本体（selftest_stop_note）を呼ぶ"
                         "（全体の --selftest は、承認の前の仮当ての打ち切り300秒を超えるため・壊すプログラム b159 が使う）")
    a = ap.parse_args()
    if a.selftest_stop_note:
        # ★2026-10-10（工事 g2-table-range-source-20261010）＝T50 だけを短く走らせる口（--selftest-stage-q と同じ作り）
        _ng50 = selftest_stop_note()
        for _x in _ng50:
            print(f"  ❌ T50: {_x}")
        print(f"  {'❌' if _ng50 else '✅'} T50 本走を呼ぶ口（途中で止まった理由を知らせる）／ダメだった件 {len(_ng50)}")
        return 1 if _ng50 else 0
    if a.selftest_stage_q:

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:8084「a = ap.parse_args()」
状態: 確定

#### 実装 12
対象のファイル: .claude/hooks/require_design_contract_before_run.sh
直す箇所: 108行（設計↔実装ゲートが通す旗の一覧の最後）
直す前の文字:
~~~
             '--selftest-stage-q'])

~~~
直した後の文字:
~~~
             '--selftest-stage-q',
             # ★2026-10-10（設計書 iter="g2-table-range-source-20261010"）＝自己テストの中で本走を呼ぶ口の既知答え
             #   （engine_tuner_gen.py の selftest_stop_note＝T50）だけを試す口。作り物の文と関数だけを使い、案も成績表も
             #   売買記録も書かない・累積の試行数に足さない。足した理由は上と同じ＝旗は「独立した語として完全一致」で
             #   見るので、'--selftest' に一致しない。壊すプログラム b159 が使う。
             '--selftest-stop-note'])

~~~
根拠の抜き書き: .claude/hooks/require_design_contract_before_run.sh:108「'--selftest-stage-q'])」
状態: 確定

#### 実装 13
対象のファイル: .claude/breaks/b159_selftest_run_passthrough.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 本走を呼ぶ口（_selftest_run）を、本走が止まるとプログラムごと終わる形に戻すと、短い口の T50① が落ちる
# EXPECT_MSG: ❌ T50: ①
# b159_selftest_run_passthrough — 本走を呼ぶ口（_selftest_run）を、本走が止まるとプログラムごと終わる形に戻すと、短い口の T50① が落ちる（工事 g2-table-range-source-20261010・2026-10-10）
#   守っているもの＝完成の条件 #1（短い口 --selftest-stop-note の T50①＝本走が途中で止まったら、理由の行つきで知らせる）
#   壊し方＝engine_tuner_gen.py の _selftest_run の中の、下の old を new に置き換える（SystemExit をそのまま通す＝直す前と同じ動き）。
#   期待＝engine_tuner_gen.py --selftest-stop-note が「❌ T50: ①」を出して落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

G="$PR/engine_tuner_gen.py"
guard "$G"

python3 - "$G" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    except SystemExit:\n        raise _RunStopped(_stop_note("".join(b.getvalue() for b in bufs))) from None\n'
new = '    except SystemExit:\n        raise\n'
if s.count(old) != 1:
    raise SystemExit("[b159_selftest_run_passthrough] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$G" --selftest-stop-note
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 13 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 本走が止まったら、理由を失敗の一覧に入れて、後ろの検査へ進む | T6 で自己テストの全部が終わると、後ろの検査が1本も走らない。2026-10-06 から、後ろの検査は1回も走っていなかった | 理由を画面に出してから、同じ所で終わる（後ろの検査が走らないまま） |
| 2 | 本走を呼ぶ所を、1つの口（_selftest_run）にまとめる | 受ける所が1か所になり、既知答えと壊すプログラムで守れる | T6・T29・T10 のそれぞれに、同じ受けを書く（3か所に同じ判定が在る形になる） |
| 3 | 短い口（--selftest-stop-note）を足す | 承認の前の検査は、完成の条件のコマンドを 300秒で打ち切る。全体の自己テストは写しで 565秒かかり、T6 が失敗のままなので終了コードも 1。完成の条件のコマンドに使えない | 完成の条件を grep だけで見る（形しか見ない） |
| 4 | hook の通す旗の一覧に、短い口を1つ足す | 旗は「独立した語として完全一致」で見るので、足さないと CC がこの口を打てない（前から在る短い口と同じ） | 足さない（承認の前の検査と壊すプログラムからは走るが、CC が手で確かめられない） |
| 5 | T22 の見本の材料を ROC 12 にする | 6 は、2026-10-06 に資料から写した探す範囲の外になった。12 は資料の表の ROC の行の最初の値（既定）に在り、範囲の中 | 見本の指標を ROC でない物に替える（検査が見る4か所の組み合わせが変わる） |
| 6 | T6・T29・T10 を通す直しは入れない | 最初の段階を代表の値で組む直しと、最後の段階でパラメータを動かす直しが一緒に要る（M2-E-8）。指標の修正の最後に固まる表と範囲を読む | この工事で、照らす側を緩めて通す（決定と逆の向き） |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=520e888f8295521f gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b159_selftest_run_passthrough.sh` | #1 | 口を、本走が止まるとプログラムごと終わる形に戻す |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 全体の自己テストは、M2-E-8 が済むまで終了コード 1 のまま。失敗の一覧に T6・T29・T10・T12・T13 が出続ける | 理由の行が出るので、同じ原因かどうかを毎回 読める。M2-E-8 の完成の条件に、全体の自己テストが通ることを入れる |
| 2 | T6・T29・T10 が口を通さない形に戻されても、短い口は通る | 設計書の照合（must_use＝selftest が _selftest_run を呼ぶ）が、呼んでいるかを見る。3か所とも通しているかまでは見ない（7-4） |
| 3 | 後ろの検査のうち、今回 初めて最後まで走った検査が、次の工事（K-3c）で失敗する | 全体の自己テストを、K-3c の写しの確かめで走らせる |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（--design） | 1分未満 | 工事 g2-sentinel-material-pick-20261007 の設計書の 6-3（当てるプログラムは1秒未満で終わった） |
| 承認の前の検査 | 約234秒に、当てる・完成の条件・壊すプログラム・元に戻す時間を足した長さ | 写しで A12 の自己テストを走らせた合計（g2r_quick.json） |
| G2 | 約30秒 | next_step の「印の状態」の節 |
| H2 | 約5分 | 同じ節 |
| 監査に出す前のチェック | 約9分 | pre_audit_check.py の説明（H2 を含む） |
| まこさんの手数 | 設計書の承認 1回・型の表の再承認 1回 | 4-4 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝自己テストが、本走の出す文を受け皿に入れたまま、本走がプログラムごと終わる（SystemExit）のを受けていなかった。受け皿の文は捨てられ、自己テストの全部が T6 で終わった。後ろの検査が走らないので、T22 の見本の数字が範囲の外になったことにも、誰も気づかなかった。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。自己テストが最後まで走り、止まった理由が読める状態になります。

**③ root か symptom か**＝「理由が出ない・後ろの検査が走らない」の root です。本走が型の表との照らしで止まる原因（M2-E-8）は残ります。

**④ ベースアップ**＝自己テストのコード（T6・T29・T10・T12・T22・まとめの文）と、A12 の本体（完成の条件のコマンドの打ち切り）を読んだ。写しで、全体の自己テストを5回・短い口と壊し方を1回 走らせた。新しい Web の調べはしていません。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。新しい数字は、T22 の見本の 12 の1つで、資料の表の ROC の行に在る数字です。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝自己テストの中で本走を呼ぶ所の作り（止まった理由を知らせて、後ろの検査へ進む）。T22 の見本の数字は、その結果 初めて見えた、同じ自己テストの中の1行です。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 案を作る所は変えません。乱数も足しません |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 探す値にも、探す範囲にも触りません。12 は検査の見本の数字です |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **全体の自己テストが最後まで届くことを、完成の条件のコマンドで見るか** | 見ません。承認の前の検査の打ち切り（300秒）を超え、T6 が失敗のままなので終了コードも 1 です。写しで走らせて確かめました（4-12 の3） |
| **T6・T29・T10 が、3か所とも口を通しているか** | 短い口と壊すプログラムは見ません。設計書の照合は、selftest が _selftest_run を呼んでいるかだけを見ます |
| **本走が型の表との照らしで止まること** | この工事では塞ぎません（M2-E-8） |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作るプログラムを書き換えられたら** | そのプログラム自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=f969f810d904e4c8 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝engine_tuner_gen.py・hook の require_design_contract_before_run.sh・新しい壊すプログラムを【7-8】に書いた。主なファイルは engine_tuner_gen.py（自己テスト）。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝engine_tuner_gen.py）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム（NEW_FILE）。手本は b127（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝照らす側を緩めて合わせる直しは入れていない（163回目に、要件と逆の向きの案を出して止められた）。失敗を成功に見せる直しも入れていない（T6 は失敗のまま）。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | この工事は、新しい部品も前処理も足さない。材料の計算は変えない。当てた後に H2 を取り直す。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 直すファイルの行番号を指す文書を git grep で出した。足す行より後ろを指す所は、設計書の控え・監査の結果・作業の記録だけで、法則ファイルとマイルストーンには無い（4-13 の3）。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、探す文字の数が当てる前と後で同じことをプログラムが数えた（4-13 の4）。前からの壊すプログラムが走らせるコマンドの旗は変えない。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムが測るのは短い口で、ファイルを1つも書かない。本物の結果の置き場には書かない。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 新しく足す関数は、DESIGN_CONTRACT の impl_functions に全部 書いた（当てる前と後の構文木でプログラムが数えた）。must_use の名前は、当てた後の関数の中に在ることを ast で照らした。engine_tuner_gen.py の触る関数＝_selftest_run・_stop_note・main・selftest・selftest_stop_note。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足すコマンドの旗 --selftest-stop-note は、完成の条件のコマンドと壊すプログラムで通る。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=g2-table-range-source-20261010）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝口の既知答え T50（4件・うち1件はメタ確認）と、壊すプログラム（口を戻すと失敗するか）。承認の前の検査の仮当てで走らせる。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | F-1＝自己テストの中で本走を呼ぶ口が、途中で止まった本走の理由を知らせる（既知答え T50 が全部 通る） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest-stop-note` | 実経路 | 口を、本走が止まるとプログラムごと終わる形に戻す | `b159_selftest_run_passthrough.sh` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=c4ffe37f909cbb7d gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/engine_tuner_gen.py`

| 触る関数 | 定義の行 |
|---|---|
| `selftest_stop_note` | （この関数は実物に無い） |
| `_selftest_run` | （この関数は実物に無い） |
| `_stop_note` | （この関数は実物に無い） |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 162件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=b4e1b9ef15eb590d gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
  "_impl_file の意味": "自己テストと、本走を呼ぶ口が在る、値を探すプログラムを照らす。",
  "impl_functions": {
    "scripts/priority_rebuild/engine_tuner_gen.py": [
      "_selftest_run",
      "_stop_note",
      "main",
      "selftest",
      "selftest_stop_note"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数と、新しく足す関数（当てる前と後の構文木を関数ごとに比べて、g2r_proposal_build.py が数えた）。",
  "self_check_calls": [
    "selftest_stop_note",
    "_selftest_run",
    "_stop_note"
  ],
  "_self_check_calls の意味": "実装の後の engine_tuner_gen.py に在るはずの、この工事が足す関数の名前。",
  "must_use": {
    "selftest": [
      "_selftest_run",
      "selftest_stop_note"
    ],
    "selftest_stop_note": [
      "_selftest_run"
    ],
    "_selftest_run": [
      "_stop_note"
    ],
    "main": [
      "selftest_stop_note"
    ]
  },
  "_must_use の意味": "自己テストが本走を呼ぶ口を通すこと・全体の自己テストと短い口が同じ既知答えを呼ぶこと（g2r_proposal_build.py が当てた後の構文木で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は自己テストの中の本走の呼び方と、見本の数字1つを直す。外から読む一覧の形（型の表・設定・検査済みの記録）は変えない。",
  "generated_from": {
    "impl_functions": "当てる前と後の関数ごとの構文木の差（g2r_proposal_build.py が数えた）",
    "must_use": "ast で照らした",
    "spec_lists": "空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
 "public_functions": {
  "load_limits": [],
  "HoldRangeError": [],
  "resolve_hold_range": [
   "HoldRangeError"
  ],
  "hold_bars": [
   "HoldRangeError"
  ],
  "material_pool": [],
  "material_ranges": [
   "load_limits"
  ],
  "param_in_range": [
   "material_ranges"
  ],
  "draw_param": [
   "material_ranges"
  ],
  "assert_provenance": [
   "SampleError",
   "material_ranges",
   "param_in_range",
   "q_range_of"
  ],
  "assert_roles": [
   "SampleError"
  ],
  "assert_exit_roles": [
   "SampleError"
  ],
  "validate_drawn": [
   "strip_marks"
  ],
  "strip_marks": [],
  "int_range_of": [],
  "draw_int": [
   "int_range_of"
  ],
  "num_range_of": [],
  "draw_num": [
   "num_range_of"
  ],
  "ladder_min_frac": [],
  "max_ladder_steps": [
   "ladder_min_frac",
   "num_range_of"
  ],
  "q_range_of": [],
  "quantile_list": [
   "q_range_of"
  ],
  "draw_q": [
   "q_range_of"
  ],
  "q_in_range": [
   "q_range_of"
  ],
  "num_in_range": [
   "num_range_of"
  ],
  "SampleError": [],
  "load_signal_table": [],
  "load_material_ranking": [],
  "ranked_materials": [
   "load_material_ranking"
  ],
  "same_fn_family_pairs": [],
  "pair_allowed": [
   "same_fn_family_pairs"
  ],
  "load_exit_table": [],
  "ranked_groups": [
   "ranked_materials"
  ],
  "regime_draw_order": [
   "SampleError"
  ],
  "laws_for_scene": [
   "SampleError"
  ],
  "stage_candidates": [
   "SampleError"
  ],
  "pre_win_bars": [
   "SampleError"
  ],
  "stage_warm": [
   "pre_win_bars",
   "stage_candidates"
  ],
  "drop_tfs_of": [
   "SampleError"
  ],
  "stage_limits_of": [
   "SampleError",
   "material_ranges",
   "q_range_of"
  ],
  "stage_tfs_of": [
   "SampleError",
   "drop_tfs_of",
   "stage_limits_of"
  ],
  "stage_lineages_of": [
   "SampleError"
  ],
  "build_stage_candidates": [
   "SampleError",
   "int_range_of",
   "material_ranges",
   "pre_win_bars",
   "ranked_groups",
   "stage_candidates",
   "stage_limits_of",
   "stage_lineages_of",
   "stage_tfs_of"
  ],
  "build_width_candidates": [
   "SampleError",
   "material_ranges",
   "ranked_groups",
   "stage_candidates",
   "stage_tfs_of"
  ],
  "stage_keep_of": [
   "SampleError"
  ],
  "stage_counts": [
   "build_stage_candidates",
   "stage_keep_of"
  ],
  "sample_regime_build": [
   "SampleError",
   "build_stage_candidates",
   "build_width_candidates",
   "laws_for_scene",
   "regime_draw_order",
   "stage_candidates",
   "stage_counts",
   "stage_keep_of"
  ],
  "default_regime": [],
  "sample_structure": [
   "SampleError",
   "default_regime",
   "load_signal_table",
   "sample_regime_build"
  ],
  "recipe_hash": [
   "strip_marks"
  ],
  "write_kakikudashi": [],
  "structure_breakdown": [],
  "needed_qkeys": [],
  "build_qtable": [
   "needed_qkeys"
  ],
  "attach_materials": [],
  "pvalue_daily": [],
  "bh_select": [],
  "strat_gate": [],
  "Journal": [],
  "assert_known_exit_reason": [],
  "run_trial": [
   "strip_marks"
  ],
  "run_trial_guarded": [
   "run_trial"
  ],
  "reject_code": [],
  "zero_trade_gate": [],
  "per_day_gate": [
   "zero_trade_gate"
  ],
  "suggest_slot": [],
  "value_slots": [
   "hold_bars",
   "int_range_of",
   "num_range_of",
   "q_range_of"
  ],
  "apply_slots": [],
  "read_slots": [],
  "run_generation": [
   "Journal",
   "apply_slots",
   "bh_select",
   "build_qtable",
   "load_signal_table",
   "per_day_gate",
   "pvalue_daily",
   "quantile_list",
   "read_slots",
   "recipe_hash",
   "reject_code",
   "run_trial",
   "run_trial_guarded",
   "sample_structure",
   "strat_gate",
   "strip_marks",
   "structure_breakdown",
   "suggest_slot",
   "value_slots",
   "write_kakikudashi"
  ],
  "synth_df": [],
  "selftest_rank_demand": [
   "load_signal_table",
   "ranked_groups",
   "ranked_materials"
  ],
  "selftest_stages": [
   "build_stage_candidates",
   "laws_for_scene",
   "load_limits",
   "load_signal_table",
   "material_pool",
   "sample_regime_build",
   "stage_keep_of"
  ],
  "selftest_stage_q": [
   "build_stage_candidates",
   "laws_for_scene",
   "load_limits",
   "load_signal_table",
   "material_pool",
   "needed_qkeys",
   "resolve_hold_range",
   "sample_regime_build",
   "stage_candidates"
  ],
  "selftest_stop_note": [],
  "selftest": [
   "Journal",
   "apply_slots",
   "assert_known_exit_reason",
   "assert_provenance",
   "bh_select",
   "build_qtable",
   "build_stage_candidates",
   "build_width_candidates",
   "drop_tfs_of",
   "gate_matrix",
   "ladder_min_frac",
   "laws_for_scene",
   "lint_provenance",
   "load_exit_table",
   "load_limits",
   "load_material_ranking",
   "load_signal_table",
   "material_pool",
   "material_ranges",
   "max_ladder_steps",
   "needed_qkeys",
   "num_in_range",
   "pair_allowed",
   "param_in_range",
   "per_day_gate",
   "pre_run_gate",
   "pre_win_bars",
   "pvalue_daily",
   "q_in_range",
   "q_range_of",
   "quantile_list",
   "ranked_groups",
   "ranked_materials",
   "read_slots",
   "regime_draw_order",
   "reject_code",
   "resolve_hold_range",
   "run_generation",
   "run_trial_guarded",
   "sample_regime_build",
   "sample_structure",
   "selftest_rank_demand",
   "selftest_stage_q",
   "selftest_stages",
   "selftest_stop_note",
   "stage_candidates",
   "stage_counts",
   "stage_keep_of",
   "stage_lineages_of",
   "stage_tfs_of",
   "stage_warm",
   "strat_gate",
   "strip_marks",
   "structure_breakdown",
   "synth_df",
   "validate_drawn",
   "value_slots",
   "verify_provenance",
   "zero_trade_gate"
  ],
  "pre_run_gate": [],
  "run_main": [
   "assert_known_exit_reason",
   "hold_bars",
   "load_limits",
   "material_pool",
   "pre_run_gate",
   "resolve_hold_range",
   "run_generation",
   "stage_warm"
  ],
  "main": [
   "gate_matrix",
   "lint_provenance",
   "load_limits",
   "load_signal_table",
   "material_pool",
   "run_main",
   "sample_structure",
   "selftest",
   "selftest_rank_demand",
   "selftest_stage_q",
   "selftest_stages",
   "selftest_stop_note",
   "strip_marks",
   "structure_breakdown",
   "verify_provenance"
  ],
  "lint_provenance": [],
  "gate_matrix": [
   "apply_slots",
   "load_limits",
   "load_signal_table",
   "material_pool",
   "material_ranges",
   "resolve_hold_range",
   "run_trial_guarded",
   "sample_structure",
   "value_slots"
  ],
  "verify_provenance": [
   "load_limits",
   "load_signal_table",
   "resolve_hold_range"
  ]
 },
 "constants": {
  "PARAM_SRC": "_param_src",
  "Q_SRC": "_q_src",
  "NUM_SRC": "_num_src",
  "LIN_SRC": "_lineage_src",
  "_EXEC_BAR_MIN": 5,
  "ATTACH_CALLS": 0
 },
 "cli_flags": []
}
```

<!-- ACC_SPEC_END -->

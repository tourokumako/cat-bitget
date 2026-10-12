<!-- ARC iter="k4-reference-known-20261011" -->

# 設計書｜K-4 検査の直し＝監査 CP60 の修正59・60。参照表の独立実装に「教科書から書いたか・写しか」の印を付け、写しの物と4種の既知答えに定義から導いた答えを足す。M2-C-15

TARGET: scripts/priority_rebuild/indicator_reference_diag.py, scripts/priority_rebuild/observe_diag.py, .claude/breaks/b172_alma_weights_reversed.sh, .claude/breaks/b173_stc_zero_range_divides.sh, .claude/breaks/b174_hilo_short_column.sh, .claude/breaks/b175_dpo_centered_future.sh, .claude/breaks/b176_sarext_sign_not_abs.sh, .claude/breaks/b177_psar_af_column.sh, .claude/breaks/b178_cksp_long_short_swapped.sh, .claude/breaks/b179_pmax_ma_of_high.sh, .claude/breaks/b180_vwap_volume_weight_dropped.sh, .claude/breaks/b181_thermo_ma_column.sh, .claude/breaks/b182_copy_mark_without_known.sh, .claude/breaks/b183_copy_verified_by_tb_alone.sh
NEW_FILE: .claude/breaks/b172_alma_weights_reversed.sh, .claude/breaks/b173_stc_zero_range_divides.sh, .claude/breaks/b174_hilo_short_column.sh, .claude/breaks/b175_dpo_centered_future.sh, .claude/breaks/b176_sarext_sign_not_abs.sh, .claude/breaks/b177_psar_af_column.sh, .claude/breaks/b178_cksp_long_short_swapped.sh, .claude/breaks/b179_pmax_ma_of_high.sh, .claude/breaks/b180_vwap_volume_weight_dropped.sh, .claude/breaks/b181_thermo_ma_column.sh, .claude/breaks/b182_copy_mark_without_known.sh, .claude/breaks/b183_copy_verified_by_tb_alone.sh
MODEL: .claude/breaks/b142_rci_list_stale.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `k4-reference-known-20261011/k4_proposal_20261011`・`k4-reference-known-20261011/ok_k4_proposal_20261011`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/k4-reference-known-20261011/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work k4-reference-known-20261011 --write`。検出＝`--work k4-reference-known-20261011 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=8d558741d6838bb6 gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/k4-reference-known-20261011/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/k4-reference-known-20261011/k4_proposal_20261011.txt`（まこさんが OK した CC の文）・`verbatim/k4-reference-known-20261011/ok_k4_proposal_20261011.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝770 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `k4_proposal_20261011` | V01〜V07（7 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `k4_proposal_20261011` | V08〜V35（28 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V36〜V40（5 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V41〜V45（5 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V46〜V58（13 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V59〜V64（6 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V65〜V73（9 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V74〜V82（9 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V83〜V84（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V85〜V86（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V87〜V88（2 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V89〜V90（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V91〜V92（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V93〜V98（6 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V99〜V107（9 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V108〜V114（7 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V115〜V116（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V117〜V118（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V119〜V120（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V121〜V126（6 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V127〜V591（465 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V592〜V601（10 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V602〜V609（8 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V610〜V618（9 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V619〜V625（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V626〜V627（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V628〜V629（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V630〜V634（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V635〜V646（12 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V647〜V667（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V668〜V682（15 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V683〜V764（82 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `k4_proposal_20261011` | V765〜V769（5 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `ok_k4_proposal_20261011` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
監査 CP60 は、参照表の「教科書の独立実装」の多くが、教科書でなくカタログやライブラリの変形を別の書き方で写した物で、検査3 の照合が「自分と同じか」しか確かめていないと指摘しました（修正59・一般の観点④）。ALMA の重みの向き・STC の式・SAREXT の符号の誤りが、その照合を通った理由です。修正60 は、SAREXT・CKSP・PMAX・PSAR の既知答えが「値段が一定なら 0」だけで、売り側を一度も通らないと指摘しました。この工事は、参照表の登録に「教科書から書いたか・写しか」の欄を足し、名指しされた10件の独立実装を使う16の登録に写しの印を付け、写しの物に定義から導いた既知答えを足し、4種の既知答えに下げ続ける合成のバーを足します。観察の道具の検査3 は、写しの独立実装が合っただけでは一致検証済みに数えない形にし、自己テストに写しの印の番人を2つ足します。あわせて、監査 CP73 の Q8 で「観察の道具と同じ式の写しどうしの照らし」と指摘された3種（close vs SSF平均%・close vs VIDYA_CMO%・SQZ_ON_Carter）の独立の実装を、別の書き方にします。材料の値・設定の値は1つも変えません（写しで前から在る列の値の違い 0 本）。既知答えの数字は、定義から導いた式で書き、ライブラリの値を写していません。導いた答えは、写しで走らせて全部 ライブラリの実物の値と合いました。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 登録の欄 tb_kind（F-1） | `grep -n -F 'tb_kind=tb_kind' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py` | 実装の前は、無い。実装の後は、登録の関数 _r の中に在る | （終了コード 1） |
| 写しの印（F-1） | `grep -c -F 'tb_kind="写し"' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py` | 実装の前は、ゼロ。実装の後は、名指しの十件の独立実装を使う登録の数（十六） | 0（終了コード 1） |
| 下げ続ける足の既知答え（F-3） | `grep -c -F '_dn(600, 1000.0, 1.0)' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py` | 実装の前は、ゼロ。実装の後は、四種の登録（七つの列）の既知答えの行に在る | 0（終了コード 1） |
| 検査3 の写しの扱い（F-5） | `grep -n -F '独立(写し)✓' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、検査三の照合本体の独立実装の枝に在る | （終了コード 1） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

［自動］印のファイル・型の表・格子と範囲
<!-- ACC_MATERIALS_START hash=602714fc3524185b gen_acceptance.py が自動生成＝手で書き換えない -->
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
| `material_param_ranges` | {"ADX": [{"kind": "int", "lo": 7, "hi": 21}], "DI差": [{"kind": "int", "lo": 7, "hi": 21}], "MACD線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}], "MACDヒスト%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "MACDシグナル線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "転換線": [{"kind": "int", "lo": 5, "hi": 12}], "基準線": [{"kind": "int", "lo": 13, "hi": 26}], "EMA傾き": [{"kind": "int", "lo": 9, "hi": 200}], "KSTシグナル": [{"kind": "int", "lo": 9, "hi": 9}], "PPO": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOシグナル": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOヒスト": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "TRIX": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TSI": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIシグナル": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIヒスト": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "KAMA傾き%": [{"kind": "int", "lo": 7, "hi": 10}], "WMA傾き%": [{"kind": "int", "lo": 20, "hi": 200}], "AROONU": [{"kind": "int", "lo": 7, "hi": 288}], "AROOND": [{"kind": "int", "lo": 7, "hi": 25}], "AROONOSC": [{"kind": "int", "lo": 7, "hi": 25}], "VTXP": [{"kind": "int", "lo": 14, "hi": 30}], "VTXM": [{"kind": "int", "lo": 14, "hi": 30}], "RSI": [{"kind": "int", "lo": 2, "hi": 21}], "ROC": [{"kind": "int", "lo": 9, "hi": 24}], "Stoch%K": [{"kind": "int", "lo": 5, "hi": 21}], "Stoch%D": [{"kind": "int", "lo": 5, "hi": 21}], "MFI": [{"kind": "int", "lo": 10, "hi": 20}], "CMF": [{"kind": "int", "lo": 20, "hi": 36}], "OBV傾き": [{"kind": "int", "lo": 10, "hi": 20}], "BB%b": [{"kind": "int", "lo": 10, "hi": 50}, {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}], "volume_ratio": [{"kind": "int", "lo": 20, "hi": 50}], "CCI": [{"kind": "int", "lo": 7, "hi": 21}], "PVO": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOシグナル": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOヒスト": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "StochRSI%K": [{"kind": "int", "lo": 7, "hi": 21}], "StochRSI%D": [{"kind": "int", "lo": 7, "hi": 21}], "DPO%": [{"kind": "int", "lo": 14, "hi": 40}], "EFI比": [{"kind": "int", "lo": 10, "hi": 20}], "EOM比": [{"kind": "int", "lo": 10, "hi": 20}], "NVI傾き": [{"kind": "int", "lo": 10, "hi": 20}], "PVT傾き": [{"kind": "int", "lo": 10, "hi": 20}], "ATR%": [{"kind": "int", "lo": 5, "hi": 21}], "BB幅": [{"kind": "int", "lo": 10, "hi": 50}, {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}], "realized_vol": [{"kind": "int", "lo": 10, "hi": 50}], "Donchian幅": [{"kind": "int", "lo": 10, "hi": 20}], "MMI": [{"kind": "int", "lo": 200, "hi": 500}], "ER": [{"kind": "int", "lo": 7, "hi": 21}], "CHOP": [{"kind": "int", "lo": 7, "hi": 21}], "VHF": [{"kind": "int", "lo": 7, "hi": 28}], "MAD比": [{"kind": "int", "lo": 20, "hi": 50}], "stdev%": [{"kind": "int", "lo": 10, "hi": 50}], "UI": [{"kind": "int", "lo": 7, "hi": 21}], "高値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "安値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "形スコア": [{"kind": "int", "lo": 24, "hi": 96}], "W字": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.0, "hi": 0.06, "dec": 3}], "fractal高値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "fractal安値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "高値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "安値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "構造破断距離%": [{"kind": "int", "lo": 2, "hi": 3}], "close vs EMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs SMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs VWAP": [{"kind": "int", "lo": 288, "hi": 288}], "Keltner上": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "Keltner下": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "n本高値": [{"kind": "int", "lo": 10, "hi": 50}], "n本安値": [{"kind": "int", "lo": 10, "hi": 50}], "pivotPP": [{"kind": "int", "lo": 288, "hi": 288}], "pivotR1": [{"kind": "int", "lo": 288, "hi": 288}], "pivotS1": [{"kind": "int", "lo": 288, "hi": 288}], "fib位置": [{"kind": "int", "lo": 14, "hi": 96}], "S-Rタッチ1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}], "S-Rタッチ数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}], "close vs ALMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs DEMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs FWMA%": [{"kind": "int", "lo": 10, "hi": 20}], "close vs HMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs JMA%": [{"kind": "int", "lo": 3, "hi": 80}], "close vs KAMA%": [{"kind": "int", "lo": 7, "hi": 30}], "close vs LINREG%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs LRb%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs MCGD%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs MIDPOINT%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MIDPRICE%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MMAR%": [{"kind": "int", "lo": 10, "hi": 35}], "close vs PWMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs RAINBOW%": [{"kind": "int", "lo": 2, "hi": 2}, {"kind": "int", "lo": 1, "hi": 10}], "close vs RMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SINWMA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs SSF%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SWMA%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs T3%": [{"kind": "int", "lo": 8, "hi": 200}], "close vs TEMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TRIMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TSF%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs VIDYA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs VWMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs WMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs MEDIAN%": [{"kind": "int", "lo": 4, "hi": 200}], "RCI": [{"kind": "int", "lo": 5, "hi": 52}], "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}], "W字確定谷": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.0, "hi": 0.06, "dec": 3}], "S-Rタッチ確定数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}], "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}], "DPO教科書%": [{"kind": "int", "lo": 14, "hi": 40}], "StochRSI素%K": [{"kind": "int", "lo": 7, "hi": 21}], "TRIX_EMAシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIX_EMAヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "realized_vol_rv": [{"kind": "int", "lo": 10, "hi": 50}], "close vs SSF平均%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs TRIMA_TA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs VIDYA_CMO%": [{"kind": "int", "lo": 20, "hi": 200}]} |

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
| 1 | 写しの独立実装10件を教科書の作りに書き直すこと | 修正59 の直し方は印と既知答えまで。書き直すと材料の値が変わり、別の工事になる | 監査 CP60 の修正59 の補足 |
| 2 | 名指しの10件の外の登録に印を付けること | 1件ずつの判定が要る。この工事は名指しの10件と書き替える3種だけ | 読むもの宣言 |
| 3 | 修正61（説明の文だけ） | 説明の文だけの直しは直さない | 全体の表の Y-5 |
| 4 | 材料の値・設定の値・探す範囲を変えること | T-2・T-3・P-6・P-7・H-1（この工事の後） | next_step の順 |
| 5 | 教科書の版と今の版を比べること | M2-F-10f | 読むもの宣言 |
| 6 | 仕組みの直し①②④ | 作業が実際に止まったときにやる（恒久65番の3） | まこさん「CCの案でOK」 |
| 7 | 監査に出す前のチェックの自己テストの P7-1 の落ち | この工事の前から在る。next_step §6 に積んである | worklog 20261007 §11 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 写しの既知答えの「教科書」の出どころ | 修正59 の補足の例（ALMA の重み）のように原典に数字が在る物は無く、定義（登録の定義・流儀の欄の文と、監査 CP60 が引いた原典の逐語）から合成の足で導ける値にした。どの定義から導いたかを登録の説明に書いた | 監査 CP60 の修正59 の補足・読むもの宣言「原典に数字が無い物は、定義から導ける既知答えにし、どの定義から導いたかを登録の文に書く」 |
| 2 | 下げ続ける足の答えの導き方 | PSAR は Wilder の漸化式（SAR_t＝SAR_{t−1}＋AF×(EP_{t−1}−SAR_{t−1})・毎本 新しい安値で AF は 0.2 に頭打ち）から、SAR と前の終値の差が 4 に収束＝終値＋5。CKSP・PMAX も定義から導いた。写しで走らせて合った（1e-6 以内） | 監査 CP60 の修正60 の補足「答えの値は手で出してから足す＝監査では走らせていない」 |
| 3 | 設計書の監査の出し方 | この工事は新しいコードと既知答えの値が入る（判断が入る）ので、設計書の監査を出す。依頼書は1通 | まこさん「CCの案でOK」の③ |
| 4 | 壊すプログラムの測る口 | 観察の道具に軽い口 --selftest-match（正しいカタログの検査3 と写しの印の番人2つ）を足し、壊すプログラム12本はそれで測る。コマンドから呼ぶ軽い口は、検査3 を「既知答えを持つ登録の列と写しの印の列」に絞る。全体の自己テストは軽い口を全列で呼ぶので守りは減らない。理由＝承認の前の仮当ての壊すプログラムの打ち切りが 900秒で、全体の自己テスト（1本 約2分）では12本が入らず、試しの設計書の全部の検査が打ち切りで落ちた。全列の軽い口でも写しで 92秒（12本で 900秒を超える） | 試しの設計書の全部の検査の記録（.claude/state/indicator_review/k4_trial_full_prev.log）・next_step §6 の仕組みの直し②・手本＝selftest_catalog（工事 m2c15-indicator-six-items-20261004 で同じ理由で切り出した口） |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、参照表（indicator_reference_diag.py）の検査の守りを直す工事です。**監査 CP60 は、参照表の「教科書の独立実装」のうち10件（_tb_vs_pivot・_vp_ref・_tb_vs_vwap・_tb_wpat・_tb_sr_touch・_alma・_stc_parts・_tb_pos_hilo・_tb_thermo_pct・_tb_dpo）が、教科書でなくカタログかライブラリと同じ変形を別の書き方で写した物で、検査3 の照合が「自分と同じか」しか確かめていないと指摘しました（修正59）。ALMA の重みの向き・STC の式・SAREXT の符号の誤りが、その照合を通った理由です。修正60 は、SAREXT・CKSP・PMAX・PSAR の既知答えが「値段が一定なら 0」だけで、売り側を一度も通らないと指摘しました。
**①登録の欄 tb_kind（F-1）。**登録の関数 _r に、独立実装が「教科書」か「写し」かの欄を足します。既定は None（未判定）で、既存の登録は1行も変わりません。名指しの10件を使う16の登録（W字・close vs VWAP・pivotPP・pivotR1・pivotS1・POC・VAH・VAL・S-Rタッチ数・STC・STCstoch・close vs ALMA%・ALMA傾き%・close vs HILO%・DPO%・THERMO%）に tb_kind="写し" を付けます。
**②写しの既知答え（F-2）。**既知答えが無い6登録と、平らな足で 0 だけの3登録に、定義から導いた既知答えを足します。
| 登録 | 合成の足 | 答え（式） | 導いた定義 |
|---|---|---|---|
| close vs ALMA%(n) | 1本ごとに 1 上げる足（n＋40本） | (終値 ÷ (終値 − 遅れ) − 1)×100・遅れ＝Σ重み_i×(n−1−i)÷Σ重み_i（重み＝正規分布・ずらし 0.85・幅 n/6・i は古い側から） | Legoux／TradingView（監査 CP60 の §5「by setting it to 1, you can make it align fully to the current price」＝山は新しい側） |
| ALMA傾き%(n) | 同じ足 | 5 ÷ (終値 − 5 − 遅れ)×100 | 同上・傾きは5本前からの変化率（流儀） |
| STC・STCstoch | 値段が一定の足（400本） | 0 | TA-Lib「When a range is zero, the fraction keeps its previous value (0 before any).」 |
| close vs HILO% | 1本ごとに 1 上げる足（80本） | (179 ÷ 168 − 1)×100＝線は終値 − 11 | Krausz（LuxAlgo）＝前の高値の平均を終値が上抜けたら安値の平均の線（13本・21本＝流儀） |
| DPO%(n) | 1本ごとに 1 上げる足（2n＋40本） | ((n/2+1) ＋ (n−1)/2) ÷ 終値 ×100 | 流儀の欄＝終値 − n本平均を (n/2+1) 本ずらしたもの（centered=False） |
| close vs VWAP%(n) | 出来高 1 で上げる足／最後の1本だけ出来高 9 | (終値 ÷ (終値 − (n−1)/2) − 1)×100／VWAP＝(n×終値 − n(n−1)/2 ＋ 8×終値) ÷ (n＋8) | StockCharts「Cumulative(Volume x Typical Price)/Cumulative(Volume)」の移動窓・終値の流儀 |
| THERMO% | 内はらみ足（高値 101→100.5・安値 99→99.5） | 0.5 | 流儀の欄＝絶対値の大きい方（教科書の版 THERMO原作% は 0） |
| S-Rタッチ数(n,tol) | 前の n 本が 50・最後の1本が 100 | 0 | 定義＝帯（終値±許容幅）に触れた本数＝帯の外なら 0 |
**③下げ続ける合成のバー（F-3）。**終値 1000 から1本ごとに 1 下げる600本の足（始値＝前の終値・高値＝始値・安値＝終値。最後の終値 c＝401）で、
| 登録 | 答え（式） | 導いた定義 |
|---|---|---|
| close vs PSAR% | (c ÷ (c＋5) − 1)×100 | Wilder＝SAR_t＝SAR_{t−1}＋AF×(EP_{t−1}−SAR_{t−1})。毎本 新しい安値で AF は 0.2 に頭打ち。SAR と EP の差は g←0.8×(g＋1) で 4 に収束＝SAR＝前の終値＋4＝c＋5 |
| PSAR加速・PSAR反転 | 0.2・0 | 同上（頭打ち・反転なし） |
| close vs SAREXT% | (c ÷ (c＋5) − 1)×100 | TA-Lib＝買いと売りの加速が同じなら PSAR と同じ線。売り側は負で返るので絶対値（監査 CP60 の修正24） |
| close vs CKSPl% | (c ÷ (c＋17) − 1)×100 | Chande & Kroll（TradingView の形 p=10・x=1・q=9・ATR は Wilder）＝真の値幅は毎本 1 → ATR 1。買い側＝直近 q 本の max(10本高値 − ATR)＝c＋17 |
| close vs CKSPs% | (c ÷ (c＋1) − 1)×100 | 同上。売り側＝直近 q 本の min(10本安値 ＋ ATR)＝c＋1 |
| close vs PMAX% | (c ÷ (c＋7.5) − 1)×100 | PMax＝EMA10 ± 3×ATR10・下げでは上の帯。EMA10 の遅れは (10−1)/2＝4.5・ATR 1 |
写しで走らせて、7つとも 1e-6 以内で合いました。値段が一定の足（0）だけでは売り側を一度も通りません。
**④3種の独立の実装を別の書き方に（F-4）。**監査 CP73 の Q8 の (c) の3種は、観察の道具と同じ文字の繰り返しでした。SSF平均は scipy.signal.lfilter（分子 [c1/2, c1/2]・分母 [1, −c2, −c3]・最初の2本を初期状態に）、VIDYA_CMO は np.convolve で CMO の上げ・下げの合計を出し itertools.accumulate で適応の漸化式を畳む形、SQZ_ON_Carter の ATR は pandas の指数平滑（alpha＝1/n・adjust=False・最初の n 本の単純平均を種）にしました。式の出どころは変えません。3種の登録に tb_kind="教科書" を付けます。
**⑤検査3 の直し（F-5）。**観察の道具の検査3（_insp_indicator_match）で、写しの印の独立実装が合っただけでは「一致検証済み」に数えません（印は「独立(写し)✓」）。検証済みにするのは手計算の既知答えです。自己テストに番人を2つ足します＝写しの印の登録は既知答えを必ず持つ／既知答えを外した写しの列は検証済みに入らない。正しいカタログの検査3 と、この番人2つは、軽い口 selftest_match（旗 --selftest-match）に切り出します。全体の自己テストはこの軽い口を全列で呼び、壊すプログラム12本は、検査3 を「既知答えを持つ列と写しの印の列」に絞った軽い口で測ります（理由は 4-9）。
**⑥仕組みの直し③（F-6）。**写しで確かめるプログラムに、増える・消える列の名前を決めた文（EXPECT_MSG）に持つ壊すプログラムを .claude/breaks の全部から探す関数を入れました。この工事は列を変えないので 0本です。
**⑦変えないもの。**材料の列は 534 列 → 534 列（増減 0）。前から在る列の値の違い 0 本。設定ファイル・型の表・オン・オフの表は変わりません（印を作る道具の入力＝参照表の mako の欄は触らない）。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、当てる道具 apply_audit_fix.py・観察の道具の自己テスト・壊すプログラム・監査に出す前のチェックを動かします。
**誰が結果を使うか。**
- 参照表の登録（欄 tb_kind・既知答え・独立の実装）は、観察の道具の検査3 と自己テストが読みます。
- 検査3 の「一致検証済み」の数は、観察の道具の検査3 の表示と、監査に出す前のチェックが読みます。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**今の実物（indicator_reference_diag.py・observe_diag.py）・監査 CP60 の修正59・60 と §5 の原典の逐語・監査 CP73 の Q8・設計書の 4-20。
**書くもの。**
- 当てる（--design）：上の2つのコードと、新しい壊すプログラム 12本。
- G-2：G2・H2 の記録、監査に出す前のチェックの記録。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 写しの物は印と既知答えまで（教科書の作りに書き直さない） | 監査 CP60 の修正59 の補足 | 10件の独立実装の中身は変えません。材料の値も変わりません（写しで 0 本の違い） |
| 数字を CC が作らない | 思考の順の7（req_thinking_20261004） | 既知答えの数字は、定義から合成の足で導いた式で書きました。ライブラリの値は写していません |
| 名指しの10件の外の登録は触らない | 読むもの宣言・恒久65番の3 | tb_kind の既定は None＝既存の登録は1行も変わりません |
| 未来のデータを使わない | 要件定義書 §4.6.H2 | 合成の足と既知答えは検査の中だけで使います。材料の計算は変えません。当てた後に H2（observe_diag.py が対象）を取り直します |
| 値段の高さで値が変わらない | 要件定義書 §4.6.H6 | 既知答えは全部 終値で割った%か 0/1 です |
| 乱数を使わない | 恒久67番 | 乱数は使いません |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| indicator_reference_diag.py の _r | 登録の欄 tb_kind（教科書か写しか） | 直す |
| indicator_reference_diag.py の _alma_lag | ALMA の定義から、1本ごとに 1 上げる足の遅れを導く（既知答え用） | 新設 |
| indicator_reference_diag.py の16の登録（写し）と7の登録（4種） | 写しの印・定義から導いた既知答え・下げ続ける足の既知答え | 直す |
| indicator_reference_diag.py の _tb_sqz_carter・_ssf2_avg・_vidya_cmo | 3種の独立の実装（別の書き方） | 直す |
| observe_diag.py の _insp_indicator_match | 写しの独立実装が合っただけでは一致検証済みに数えない | 直す |
| observe_diag.py の selftest_match | 軽い口（旗 --selftest-match）＝正しいカタログの検査3 と、写しの印の番人2つ。コマンドから呼ぶときは検査3 を既知答えを持つ列と写しの印の列に絞る | 新設 |
| observe_diag.py の selftest | 全体の自己テスト＝軽い口 selftest_match を全列で呼ぶ（検査3 の番人の場所を軽い口に移す） | 直す |
| observe_diag.py のコマンドの分岐 | 旗 --selftest-match で selftest_match を呼ぶ | 直す |
| .claude/breaks の壊すプログラム | 既知答え・印・検査3 の直しを壊すと、軽い口が決めた文で落ちるかを見る | 新設 |
- 触る関数（当てる前と後の構文木を関数ごとに比べて道具が数えた）＝indicator_reference_diag.py：<モジュール直下>・_alma_lag・_r・_ssf2_avg・_tb_sqz_carter・_vidya_cmo／observe_diag.py：<モジュール直下>・_insp_indicator_match・selftest・selftest_match

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. 設計書の監査（別セッション）の結果を まこさんが確かめ、修正が在れば当てます。
2. まこさんの承認の後、全部を当てます（apply_audit_fix.py --design --dry → --design）。当てる道具は、全件を当てる前の実物で照らしてから、番号の順に当てます。1件でも合わなければ1件も当てません。
3. 当てた直後に、当てる道具が G2 と H2 を自分で走らせます（observe_diag.py は H2 と G2 の対象・indicator_reference_diag.py は G2 の対象です＝h2_pass.json と g2_pass.json の files の一覧で確かめた）。
4. 照合（verify_design_contract.py --diff）をかけます。壊すプログラム（測るのは軽い口 --selftest-match）を走らせ、全体の自己テスト（--selftest）を1回 走らせて、出力をそのまま貼ります（当てた直後の写しで、全部 通ることを確かめた）。
5. G-2：G2 → H2 を取り直し、監査に出す前のチェック（pre_audit_check.py --run）を走らせます。そのあと実装の監査に出します（1通）。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝SAREXT。今の既知答えは「値段が一定の足（600本・全部 100）で close vs SAREXT% は 0」だけでした。値段が一定なら逆指値はその値に張り付くので、符号を間違えても 0 のままで通ります（監査 CP60 は、下げの列で −191.89% になることを見つけました）。この工事で足す既知答えは、終値 1000 から1本ごとに 1 下げる600本の足です。売り側の SAR は、Wilder の漸化式で「前の終値＋4」に収束するので、最後の足（終値 401）では 406 です。絶対値に直してから割ると (401 ÷ 406 − 1) × 100 ＝ −1.2315…% になります。絶対値を外す（監査 CP60 が見つけた符号の誤りに戻す）と、SAR が −406 で返り、値が −198.77% になって、この既知答えで検査3 が落ちます（壊すプログラム b176）。同じ足で PSAR% も −1.2315…%、PSAR加速は 0.2、PSAR反転は 0、CKSPl% は (401 ÷ 418 − 1) × 100、CKSPs% は (401 ÷ 402 − 1) × 100、PMAX% は (401 ÷ 408.5 − 1) × 100 です。写しで走らせて、7つとも 1e-6 以内で合いました。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**変わりません。**材料も探す範囲も触りません。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**設定ファイルは変えません。**コマンドの旗を1つ足します＝observe_diag.py の --selftest-match（検査3＝参照表との照合と、写しの印の番人2つだけを走らせる軽い口。selftest_catalog の --selftest-catalog と同じ形）。コマンドから呼ぶときは、検査3 を「手計算の既知答えを持つ登録の列と、写しの印の列」（254本）だけに絞ります。壊すプログラム12本が落とす相手は全部この中に在ります。全体の自己テスト（--selftest）はこの軽い口を全列（full=True）で呼ぶので、全体の自己テストの中身は減りません。**なぜ足すか**＝全体の自己テストは1本 約142秒で、承認の前の仮当て（A12）の壊すプログラムの打ち切り 900秒に12本が入りません（試しの設計書の全部の検査を走らせたとき、打ち切りで落ちました）。全列の検査3 でも写しで92秒＝12本で900秒を超えました。壊すプログラム12本は、絞った軽い口で測ります（1本 約63秒）。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**
1. 観察の道具の全体の自己テストが通る（足した既知答え・写しの印の番人2つを含む）。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest。軽い口（検査3 を既知答えを持つ列と写しの印の列に絞った物と、写しの印の番人2つ）も通る。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest-match。
2. 検査3 の表示で、写しの印の列に「独立(写し)✓」と「既知n/n」が並ぶ（独立実装だけでは検証済みにならない）。
3. 壊すプログラムが、全部 決めた文で落ちる。コマンド＝python3 .claude/tools/run_breaks.py --design。
4. G2 と H2 が取り直される。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| --design の --dry で、当たらない件が出る | 1件も当てずに止まります。まこさんに報告します |
| 写しの登録の既知答えが実物の値と合わない | 観察の道具の自己テストが「手計算の既知答えと不一致」を出して落ちます |
| 写しの印の登録から既知答えを外す | 自己テストの番人①が「写しの印の登録に手計算の既知答えが無い」を出して落ちます |
| 検査3 の直しを戻す（写しが独立実装だけで検証済みになる） | 自己テストの番人②が「写しの独立実装だけで一致検証済みになっている」を出して落ちます |
| 3種の別の書き方が、観察の道具の値と合わない | 観察の道具の自己テストが「教科書の独立実装と不一致」を出して落ちます |
| 軽い口が、既知答えを持つ列と写しの印の列を1本も見つけない（参照表の既知答えと印が全部 消えた） | 軽い口が「既知答えを持つ列・写しの印の列がカタログに1本も無い（軽い口が回せない）」を出して落ちます |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**参照表の登録の欄に tb_kind（文字・None／"教科書"／"写し"）が増えます。**カタログの1件の形・設定の欄の形は変えません。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**変えません。**

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**変えません。**合成の足は検査の中だけで使います。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| 観察の道具の自己テスト（全体） | 142秒 | 写しで当てた後に走らせた実測（k4_draft_build.py の [7]） |
| 軽い口（--selftest-catalog） | 9秒 | 写しで当てた後に走らせた実測（k4_draft_build.py の [7]） |
| 軽い口（--selftest-match＝この工事で足す・254本に絞った検査3 と番人2つ） | 63秒 | 写しで当てた後に走らせた実測（k4_draft_build.py の [7]） |
| 材料の一覧 | 534 列 | 写しで数えた（k4_draft_build.py の [3]） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**ありません。**全部を --design の1回で当てます。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しの道具だけが書きます。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**検査3 の表示に「独立(写し)✓」が増えます。自己テストは、落ちたときだけ「手計算の既知答えと不一致」「写しの印の登録に手計算の既知答えが無い」「写しの独立実装だけで一致検証済みになっている」で始まる行を出します。軽い口（--selftest-match）は、終わりに「検査3（既知答えを持つ列と写しの印の列 N 本）と写しの印の番人（--selftest-match）: ❌ n 件」の1行を出します（selftest_catalog と同じ形）。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **observe_diag.py は H2（未来参照の検査）と G2（型の表の照らし）の対象、indicator_reference_diag.py は G2 の対象です**（h2_pass.json の24件と g2_pass.json の39件の一覧で確かめた）。当てた後に G2 → H2 を取り直します。
2. **材料の列は増減しません**（写しで 534 列 → 534 列）。型の表・オン・オフの表の作り直し（G-1）は無く、再承認も要りません。
3. **検査3 の「一致検証済み」の数は変わりません**（写しの16登録は全部 既知答えを持つ）。
4. **前からの壊すプログラムが探す文字の数は、当てる前と後で同じです。**道具が数えた相手は、下の囲みです。
```
b104_atr1h_own_tf.sh・b105_atr1h_future_hour.sh・b106_atr1h_no_clip.sh・b107_atr1h_base_not_passed.sh・b108_atr1h_base_wrong_bars.sh・b122_obs_formula_copied.sh・b126_rank_resume_save_off.sh・b128_k1_copc_back_in_ao_loop.sh・b129_htf_bar_close_two_bars.sh・b131_industry_map_prev_pivot_gone.sh・b132_hidden_param_not_passed.sh・b133_cksp_mixed_set.sh・b134_ao_name_with_value.sh・b135_rci_mako_gone.sh・b136_insp2_bar_close_dropped.sh・b137_material_params_ignored.sh・b138_keep_name_dropped.sh・b139_range_excludes_keep.sh・b140_group_range_ignored.sh・b141_catalog_out_of_range.sh・b143_rci_range_short.sh・b145_vwap_day_no_reset.sh・b146_pivot_week_as_day.sh・b147_vp_today_from_start.sh・b151_w_fractal_not_first.sh・b152_sr_fractal_counts_bars.sh・b153_smc_fractal_no_close_back.sh・b154_lower_half_upper_span.sh・b156_sr_fractal_unconfirmed.sh・b160_dpo_tb_lib_shift.sh・b161_thermo_orig_abs.sh・b162_stochrsi_raw_smoothed.sh・b163_trix_ema_signal_sma.sh・b164_rvol_rv_mean_subtracted.sh・b165_ssf_avg_single_input.sh・b166_sqz_carter_scalar_fixed.sh・b55_cyc_key_time_gone.sh・b56_one_min_csv_old.sh・b60_only5_with_others.sh・b61_insp5_bars_kind.sh・b63_tm_bitget_scope.sh・b64_tm_subdir.sh・b65_tm_badtail.sh
```
5. **増える・消える列の名前を決めた文に持つ壊すプログラム＝0本**（教訓 L-678 の照らし・列が変わらないため）。

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| k3a_draft_build.py・k3c_draft_build.py（前の工事の道具） | 写しの作り・A12 の自己テストの一覧と許しの判定（import して使う）・壊し方の確かめ |
| indicator_reference_diag.py の _flat・_up・_dn・_mk・_thermo_in_case | 既知答えの合成の足（前から在る部品をそのまま使う） |
| 壊すプログラム b142 | 壊すプログラムの形 |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=d875acb904ec9406 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 953〜961行（_r・監査 CP60 の修正59＝登録 _r に「教科書から書いたか・写しか」の欄 tb_kind を足す）
直す前の文字:
~~~
def _r(pat, family, teigi, ryugi, houkou, prop, tb=None, ext=None, known=None, tol=1e-6, mako=None):
    """材料の種類を1つ、定義表に登録する。

    ★mako（2026-09-05・M2-C-4・まこさん決定「案A にします」）＝**まこさんが個別に「使う」と
      決めた材料**に、その決定の逐語と日付を書く欄。既定は None＝既存の登録は1行も変わらない。
      この欄は印（indicator_switch.json）の源の4つ目が機械で読む＝CC が手書きの一覧を作らない。
    """
    REFS.append(dict(pat=re.compile("^" + pat + "$"), family=family, teigi=teigi, ryugi=ryugi,
                     houkou=houkou, prop=prop, tb=tb, ext=ext, known=known, tol=tol, mako=mako))

~~~
直した後の文字:
~~~
def _r(pat, family, teigi, ryugi, houkou, prop, tb=None, ext=None, known=None, tol=1e-6, mako=None, tb_kind=None):
    """材料の種類を1つ、定義表に登録する。

    ★mako（2026-09-05・M2-C-4・まこさん決定「案A にします」）＝**まこさんが個別に「使う」と
      決めた材料**に、その決定の逐語と日付を書く欄。既定は None＝既存の登録は1行も変わらない。
      この欄は印（indicator_switch.json）の源の4つ目が機械で読む＝CC が手書きの一覧を作らない。
    ★tb_kind（2026-10-11・K-4・監査 CP60 の修正59）＝独立実装 tb が「教科書から書いた物」か「カタログかライブラリと同じ変形を
      別の書き方で写した物（写し）」かの印。"写し" の登録は、検査3 で独立実装が合っただけでは「一致検証済み」に数えない
      （照合が「自分と同じか」しか確かめていないため）＝手計算の既知答えが要る（観察の道具の自己テストの番人が見る）。
      "教科書"＝教科書の式から書いた物。None＝まだ判定していない（既存の登録は1行も変わらない）。
    """
    REFS.append(dict(pat=re.compile("^" + pat + "$"), family=family, teigi=teigi, ryugi=ryugi,
                     houkou=houkou, prop=prop, tb=tb, ext=ext, known=known, tol=tol, mako=mako, tb_kind=tb_kind))

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:953「def _r(pat, family, teigi, ryugi, houkou, prop, tb=None, ext=None, known=None, tol=1e-6, mako=None):」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1185〜1193行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（W字＝_tb_wpat））
直す前の文字:
~~~
_r(r"W字\((\d+),([\d.]+)\)", "W字",
   "ダブルボトム（W字）の完成フラグ。窓 n の前半の最安値と後半の最安値が同水準（許容幅=tol×終値）で、"
   "終値がネックラインを上抜けたら 1・それ以外 0",
   "教科書のダブルボトム＝2つの底が同水準＋間の山（ネックライン）の上抜けで完成。ネックラインは"
   "中央 n/2 区間の最高値で近似（ベクトル計算のための本プロジェクトの流儀）。定義は 2026-07-30 に"
   "まこさん判断不能のため feedback_design_judgment_owner に基づき CC が案A（教科書定義）で確定",
   "反転サイン＝1 は買い転換（ダブルボトム完成）の示唆", "reversal", tb=_tb_wpat,
   known=lambda p: [(_w_case(int(p[0]), 100.2), [(-1, 1.0, 1e-9)]),
                    (_w_case(int(p[0]), 92.0), [(-1, 0.0, 1e-9)])])

~~~
直した後の文字:
~~~
_r(r"W字\((\d+),([\d.]+)\)", "W字",
   "ダブルボトム（W字）の完成フラグ。窓 n の前半の最安値と後半の最安値が同水準（許容幅=tol×終値）で、"
   "終値がネックラインを上抜けたら 1・それ以外 0",
   "教科書のダブルボトム＝2つの底が同水準＋間の山（ネックライン）の上抜けで完成。ネックラインは"
   "中央 n/2 区間の最高値で近似（ベクトル計算のための本プロジェクトの流儀）。定義は 2026-07-30 に"
   "まこさん判断不能のため feedback_design_judgment_owner に基づき CC が案A（教科書定義）で確定",
   "反転サイン＝1 は買い転換（ダブルボトム完成）の示唆", "reversal", tb=_tb_wpat,
   known=lambda p: [(_w_case(int(p[0]), 100.2), [(-1, 1.0, 1e-9)]),
                    (_w_case(int(p[0]), 92.0), [(-1, 0.0, 1e-9)])], tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1185「_r(r"W字\((\d+),([\d.]+)\)", "W字",」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1237〜1238行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（close vs VWAP＝_tb_vs_vwap））
直す前の文字:
~~~
   "順張り値", "trend", tb=_tb_vs_vwap,
   known=lambda p: [(_flat(p[0] + 10), [(-1, 0.0, 1e-9)])])

~~~
直した後の文字:
~~~
   "順張り値", "trend", tb=_tb_vs_vwap,
   # ★K-4（監査 CP60 の修正59）＝定義（出来高×終値の合計 ÷ 出来高の合計・n 本の移動窓＝流儀の欄）から導いた既知答えを足す。
   #   ①出来高が全部 1 で1本ごとに 1 上げる足＝VWAP は終値の単純平均＝終値 − (n−1)/2
   #   ②同じ足で最後の1本だけ出来高 9＝VWAP＝(n×終値 − n(n−1)/2 ＋ 8×終値) ÷ (n＋8)。出来高の重みを外すと①は通り②だけ落ちる。
   known=lambda p: [(_flat(p[0] + 10), [(-1, 0.0, 1e-9)]),
                    (_up(p[0] + 40), [(-1, ((100.0 + p[0] + 39) / ((100.0 + p[0] + 39) - (p[0] - 1) / 2.0) - 1.0) * 100.0, 1e-9)]),
                    (_mk(100.0 + np.arange(p[0] + 40, dtype=float), v=np.r_[np.ones(p[0] + 39), 9.0]),
                     [(-1, ((100.0 + p[0] + 39) / ((p[0] * (100.0 + p[0] + 39) - p[0] * (p[0] - 1) / 2.0 + 8.0 * (100.0 + p[0] + 39)) / (p[0] + 8.0)) - 1.0) * 100.0, 1e-9)])],
   tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1237「"順張り値", "trend", tb=_tb_vs_vwap,」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1316〜1317行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（pivotPP＝_tb_vs_pivot））
直す前の文字:
~~~
   "順張り値", "trend", tb=_tb_vs_pivot,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, 0.0, 1e-6)])])

~~~
直した後の文字:
~~~
   "順張り値", "trend", tb=_tb_vs_pivot,
   known=lambda p: [(_range_case(n=max(300, p[0] + 60)), [(-1, 0.0, 1e-6)])], tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1316「"順張り値", "trend", tb=_tb_vs_pivot,」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1318〜1323行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（pivotR1＝_tb_vs_pivot_rs））
直す前の文字:
~~~
_r(r"close vs pivotR1%(\d+)", "pivotR1",
   "ピボットの抵抗1 R1（2×PP − n 本安値）からの乖離%",
   "★流儀に注意＝教科書の R1 は前の期間の高安・終値から。本カタログは PP と同じ移動窓の変形（2026-07-30 検査7 を受けて追加）。外部照合は定義が違うため対象外",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_pivot_rs(d, p, +1),
   known=lambda p: [(_flat(p[0] + 20), [(-1, 0.0, 1e-9)]),
                    (_range_case(n=max(300, p[0] + 60)), [(-1, (105.0 / 110.0 - 1) * 100, 1e-6)])])

~~~
直した後の文字:
~~~
_r(r"close vs pivotR1%(\d+)", "pivotR1",
   "ピボットの抵抗1 R1（2×PP − n 本安値）からの乖離%",
   "★流儀に注意＝教科書の R1 は前の期間の高安・終値から。本カタログは PP と同じ移動窓の変形（2026-07-30 検査7 を受けて追加）。外部照合は定義が違うため対象外",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_pivot_rs(d, p, +1),
   known=lambda p: [(_flat(p[0] + 20), [(-1, 0.0, 1e-9)]),
                    (_range_case(n=max(300, p[0] + 60)), [(-1, (105.0 / 110.0 - 1) * 100, 1e-6)])], tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1318「_r(r"close vs pivotR1%(\d+)", "pivotR1",」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1327〜1329行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（pivotS1＝_tb_vs_pivot_rs））
直す前の文字:
~~~
   "順張り値", "trend", tb=lambda d, p: _tb_vs_pivot_rs(d, p, -1),
   known=lambda p: [(_flat(p[0] + 20), [(-1, 0.0, 1e-9)]),
                    (_range_case(n=max(300, p[0] + 60)), [(-1, 5.0, 1e-6)])])

~~~
直した後の文字:
~~~
   "順張り値", "trend", tb=lambda d, p: _tb_vs_pivot_rs(d, p, -1),
   known=lambda p: [(_flat(p[0] + 20), [(-1, 0.0, 1e-9)]),
                    (_range_case(n=max(300, p[0] + 60)), [(-1, 5.0, 1e-6)])], tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1327「"順張り値", "trend", tb=lambda d, p: _tb_vs_pivot_rs(d, p, -1),」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1381〜1388行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（POC＝_vp_ref））
直す前の文字:
~~~
_r(r"close vs POC%(\d+)", "POC",
   "出来高プロファイルの最厚価格帯 POC からの乖離%",
   "Market Profile。窓 n 本・25分割の近似。同量の帯が並んだら価格の高い側を採る（実装の決め）",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 0),
   # 手計算の既知答え（2026-08-09 新設・フロー 段3 の 3-4）。POC＝出来高が一番 厚い区画の中央。
   # 場合1（出来高が下に偏る 10:1）も 場合2（6:4）も、一番 厚いのは下の区画＝答えは同じ。
   known=lambda p: [(_vp_case(int(p[0]), 10, 1), [(-1, _VP_D_LO, 1e-9)]),
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_LO, 1e-9)])])

~~~
直した後の文字:
~~~
_r(r"close vs POC%(\d+)", "POC",
   "出来高プロファイルの最厚価格帯 POC からの乖離%",
   "Market Profile。窓 n 本・25分割の近似。同量の帯が並んだら価格の高い側を採る（実装の決め）",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 0),
   # 手計算の既知答え（2026-08-09 新設・フロー 段3 の 3-4）。POC＝出来高が一番 厚い区画の中央。
   # 場合1（出来高が下に偏る 10:1）も 場合2（6:4）も、一番 厚いのは下の区画＝答えは同じ。
   known=lambda p: [(_vp_case(int(p[0]), 10, 1), [(-1, _VP_D_LO, 1e-9)]),
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_LO, 1e-9)])], tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1381「_r(r"close vs POC%(\d+)", "POC",」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1389〜1395行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（VAH＝_vp_ref））
直す前の文字:
~~~
_r(r"close vs VAH%(\d+)", "VAH",
   "バリューエリア上端（出来高上位70%帯の上端）からの乖離%", "Market Profile。25分割の近似",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 1),
   # 場合1＝下の区画だけで出来高の91%を占める→上位70%帯は1区画で足りる→上端も下の区画。
   # 場合2＝下の区画は60%しか無い→上位70%帯に上の区画も要る→上端は上の区画。
   known=lambda p: [(_vp_case(int(p[0]), 10, 1), [(-1, _VP_D_LO, 1e-9)]),
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_HI, 1e-9)])])

~~~
直した後の文字:
~~~
_r(r"close vs VAH%(\d+)", "VAH",
   "バリューエリア上端（出来高上位70%帯の上端）からの乖離%", "Market Profile。25分割の近似",
   "順張り値", "trend", tb=lambda d, p: _tb_vs_vp(d, p, 1),
   # 場合1＝下の区画だけで出来高の91%を占める→上位70%帯は1区画で足りる→上端も下の区画。
   # 場合2＝下の区画は60%しか無い→上位70%帯に上の区画も要る→上端は上の区画。
   known=lambda p: [(_vp_case(int(p[0]), 10, 1), [(-1, _VP_D_LO, 1e-9)]),
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_HI, 1e-9)])], tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1389「_r(r"close vs VAH%(\d+)", "VAH",」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1396〜1401行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（VAL＝_vp_ref））
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
                    (_vp_case(int(p[0]), 6, 4), [(-1, _VP_D_LO, 1e-9)])], tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1396「_r(r"close vs VAL%(\d+)", "VAL",」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1485〜1495行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（S-Rタッチ数＝_tb_sr_touch））
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
                     [(-1, 3.0, 1e-9)]),
                    # ★K-4（監査 CP60 の修正59）＝帯の外の既知答え＝前の n 本が全部 50 で最後の1本だけ 100（帯は 100±許容幅）＝触れる足は 0
                    (_mk(np.r_[np.full(int(p[0]) + 12, 50.0), 100.0], o=np.r_[np.full(int(p[0]) + 12, 50.0), 100.0],
                         h=np.r_[np.full(int(p[0]) + 12, 50.0), 100.0], l=np.r_[np.full(int(p[0]) + 12, 50.0), 100.0]),
                     [(-1, 0.0, 1e-9)])], tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1485「_r(r"S-Rタッチ数\((\d+),([\d.]+)\)", "S-Rタッチ数",」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1688〜1690行（<モジュール直下>・監査 CP73 の Q8（修正2）＝3種の独立の実装を別の書き方にした旨の説明）
直す前の文字:
~~~
#   ★観察の道具も手の繰り返しで書いた3種は、同じ式の写しどうしの照らし（監査 CP73 の Q8）＝close vs SSF平均%（_ssf2_avg と
#   observe_diag.py の _ssf_avg の繰り返しが同じ文字）・close vs VIDYA_CMO%（繰り返しが同じ文字）・SQZ_ON_Carter（Wilder の繰り返しと
#   内側の判定の式が同じ文字）。この3種の式そのものは、出どころの逐語と読んで照らす。

~~~
直した後の文字:
~~~
#   ★観察の道具も手の繰り返しで書いた3種（close vs SSF平均%・close vs VIDYA_CMO%・SQZ_ON_Carter）は、同じ式の写しどうしの照らしだった
#   （監査 CP73 の Q8）。K-4（2026-10-11・まこさん「CCの案でOK」）で、この3種の独立の実装を別の書き方にした＝SSF は線形フィルタ
#   （scipy.signal.lfilter）・VIDYA は畳み込みで CMO を出し accumulate で畳む・Carter の ATR は pandas の指数平滑。式の出どころは変えない。

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1688「#   ★観察の道具も手の繰り返しで書いた3種は、同じ式の写しどうしの照らし（監査 CP73 の Q8）＝close vs SSF平均%（_ssf2_avg と」
状態: 確定

#### 実装 12
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1706〜1713行（_tb_sqz_carter・監査 CP73 の Q8＝SQZ_ON_Carter の独立の実装を別の書き方に（ATR は pandas の指数平滑））
直す前の文字:
~~~
def _tb_sqz_carter(d, p, bb_length=20, bb_std=2.0, kc_length=20, kc_scalar=1.5):
    o, h, l, c, v = _arr(d)
    mid, sd = _roll(c, bb_length, "mean"), _roll(c, bb_length, "std", ddof=0)
    km = _roll((h + l + c) / 3.0, kc_length, "mean")
    atr = _wilder(_tr(h, l, c), kc_length)
    on = ((mid - bb_std * sd) > (km - kc_scalar * atr)) & ((mid + bb_std * sd) < (km + kc_scalar * atr))
    out = np.where(np.isnan(atr) | np.isnan(sd), np.nan, on.astype(float))
    return _S(out, d)

~~~
直した後の文字:
~~~
def _tb_sqz_carter(d, p, bb_length=20, bb_std=2.0, kc_length=20, kc_scalar=1.5):
    """Carter のスクイーズの独立実装（K-4 で別の書き方にした）＝観察の道具は手の繰り返しで Wilder の ATR を出す。こちらは pandas の
    指数平滑（alpha＝1/n・adjust=False＝(前×(n−1)＋今)/n と同じ式）に、最初の n 本の真の値幅の単純平均を種として渡す。"""
    o, h, l, c, v = _arr(d)
    tr = pd.Series(_tr(h, l, c), index=d.index)
    seed = tr.iloc[1:kc_length + 1].mean()
    x = tr.copy()
    x.iloc[:kc_length] = np.nan
    x.iloc[kc_length] = seed
    atr = x.ewm(alpha=1.0 / kc_length, adjust=False).mean()
    atr[x.isna().cummin()] = np.nan                       # 種より前は欠損
    mid, sd = d.close.rolling(bb_length).mean(), d.close.rolling(bb_length).std(ddof=0)
    km = ((d.high + d.low + d.close) / 3.0).rolling(kc_length).mean()
    inside = ((mid - bb_std * sd) > (km - kc_scalar * atr)) & ((mid + bb_std * sd) < (km + kc_scalar * atr))
    return inside.astype(float).where(atr.notna() & sd.notna())

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1706「def _tb_sqz_carter(d, p, bb_length=20, bb_std=2.0, kc_length=20, kc_scalar=1.5):」
状態: 確定

#### 実装 13
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1730〜1740行（_ssf2_avg・監査 CP73 の Q8＝close vs SSF平均% の独立の実装を別の書き方に（scipy の線形フィルタ））
直す前の文字:
~~~
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

~~~
直した後の文字:
~~~
def _ssf2_avg(c: np.ndarray, n: int) -> np.ndarray:
    """Ehlers のスーパースムーザー（2極）＝入力を (c + c[1])/2 にしたもの（linnsoft の逐語「Filt = c1*(Close + Close[1]) / 2 + c2*Filt[1] + c3*Filt[2]」）。
    K-4 で別の書き方にした＝線形フィルタ（scipy.signal.lfilter）で書く。分子＝[c1/2, c1/2]・分母＝[1, −c2, −c3]。
    最初の2本は入力のまま（観察の道具と同じ始め方）＝その2本を初期状態（lfiltic）にして3本目から回す。"""
    from scipy.signal import lfilter, lfiltic
    x = np.pi * np.sqrt(2.0) / n
    a0 = np.exp(-x)
    b0 = 2.0 * a0 * np.cos(x)
    c2, c3 = b0, -a0 * a0
    c1 = 1.0 - c2 - c3
    y = np.asarray(c, float).copy()
    if len(y) > 2:
        b, a = [c1 / 2.0, c1 / 2.0], [1.0, -c2, -c3]
        zi = lfiltic(b, a, y=y[1::-1], x=y[1::-1])
        y[2:] = lfilter(b, a, y[2:], zi=zi)[0]
    return y

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1730「def _ssf2_avg(c: np.ndarray, n: int) -> np.ndarray:」
状態: 確定

#### 実装 14
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1758〜1770行（_vidya_cmo・監査 CP73 の Q8＝close vs VIDYA_CMO% の独立の実装を別の書き方に（畳み込みと accumulate））
直す前の文字:
~~~
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

~~~
直した後の文字:
~~~
def _vidya_cmo(c: np.ndarray, n: int, m: int = 9) -> np.ndarray:
    """VIDYA で CMO の本数 m を n と別に持つ版（ta-lib.org の逐語「n = optInTimePeriod, m = optInCMOPeriod」）。
    K-4 で別の書き方にした＝CMO の上げ・下げの合計は畳み込み（np.convolve）で出し、適応の漸化式 out←a×k×c＋(1−a×k)×out は
    itertools.accumulate で畳む（種＝最初の n 本の単純平均）。"""
    from itertools import accumulate
    c = np.asarray(c, float)
    a = 2.0 / (n + 1)
    dif = np.diff(c)
    k = np.full(len(c), np.nan)
    if len(c) > m:
        up = np.convolve(np.clip(dif, 0.0, None), np.ones(m), "valid")
        dn = np.convolve(np.clip(-dif, 0.0, None), np.ones(m), "valid")
        k[m:] = np.abs(_div(up - dn, up + dn))
    out = np.full(len(c), np.nan)
    if len(c) < n:
        return out
    kk = np.nan_to_num(k[n:], nan=0.0)
    seed = float(np.nanmean(c[:n]))
    out[n - 1:] = list(accumulate(zip(c[n:], kk), lambda prev, t: a * t[1] * t[0] + (1.0 - a * t[1]) * prev, initial=seed))
    return out

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1758「def _vidya_cmo(c: np.ndarray, n: int, m: int = 9) -> np.ndarray:」
状態: 確定

#### 実装 15
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1825行（<モジュール直下>・3種の登録に印 tb_kind="教科書"（SQZ_ON_Carter））
直す前の文字:
~~~
   "状態量", "none", tb=_tb_sqz_carter, mako=MAKO_K3C)

~~~
直した後の文字:
~~~
   "状態量", "none", tb=_tb_sqz_carter, mako=MAKO_K3C, tb_kind="教科書")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1825「"状態量", "none", tb=_tb_sqz_carter, mako=MAKO_K3C)」
状態: 確定

#### 実装 16
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1839行（<モジュール直下>・3種の登録に印 tb_kind="教科書"（close vs SSF平均%））
直す前の文字:
~~~
   "反転サイン", "trend", tb=_tb_pos_ssf_avg, mako=MAKO_K3C)

~~~
直した後の文字:
~~~
   "反転サイン", "trend", tb=_tb_pos_ssf_avg, mako=MAKO_K3C, tb_kind="教科書")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1839「"反転サイン", "trend", tb=_tb_pos_ssf_avg, mako=MAKO_K3C)」
状態: 確定

#### 実装 17
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1847行（<モジュール直下>・3種の登録に印 tb_kind="教科書"（close vs VIDYA_CMO%））
直す前の文字:
~~~
   "反転サイン", "trend", tb=_tb_pos_vidya_cmo, mako=MAKO_K3C)

~~~
直した後の文字:
~~~
   "反転サイン", "trend", tb=_tb_pos_vidya_cmo, mako=MAKO_K3C, tb_kind="教科書")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1847「"反転サイン", "trend", tb=_tb_pos_vidya_cmo, mako=MAKO_K3C)」
状態: 確定

#### 実装 18
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3279行（<モジュール直下>・監査 CP60 の修正59＝ALMA の定義から遅れを導く部品 _alma_lag（既知答え用））
直す前の文字:
~~~
_r(r"close vs ALMA%(\d+)", "close vs ALMA%",

~~~
直した後の文字:
~~~
def _alma_lag(n: int, sigma: float = 6.0, off: float = 0.85) -> float:
    """ALMA の定義（Legoux／TradingView＝重みは正規分布・ずらし 0.85 で山が新しい側・幅 n/σ）から導く、
    1本ごとに 1 上げる足での遅れ＝Σ 重み_i × (n−1−i) ÷ Σ 重み_i（i は窓の古い側から数える）。
    ★K-4（監査 CP60 の修正59）の既知答え用。重みを逆向きに当てる（ライブラリの写し）と遅れは Σ 重み_i × i ÷ Σ 重み_i になり、
    値が変わる＝監査 CP60 が見つけた向きの誤りを、この既知答えが捕まえる。"""
    i = np.arange(n, dtype=float)
    w = np.exp(-((i - off * (n - 1)) ** 2) / (2.0 * (n / sigma) ** 2))
    return float(np.sum(w * (n - 1 - i)) / np.sum(w))


_r(r"close vs ALMA%(\d+)", "close vs ALMA%",

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:3279「_r(r"close vs ALMA%(\d+)", "close vs ALMA%",」
状態: 確定

#### 実装 19
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3281行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（close vs ALMA%＝_alma））
直す前の文字:
~~~
   "Arnaud Legoux。重みは正規分布（ずらし 0.85・幅 n/6）＝ライブラリの既定", "反転サイン", "trend", tb=_tb_pos_alma)

~~~
直した後の文字:
~~~
   "Arnaud Legoux。重みは正規分布（ずらし 0.85・幅 n/6）＝ライブラリの既定", "反転サイン", "trend", tb=_tb_pos_alma,
   # ★K-4（監査 CP60 の修正59）＝定義から導いた既知答え＝1本ごとに 1 上げる足で、ALMA は終値 − 遅れ（_alma_lag）。
   known=lambda p: [(_up(int(p[0]) + 40), [(-1, ((100.0 + int(p[0]) + 39) / ((100.0 + int(p[0]) + 39) - _alma_lag(int(p[0]))) - 1.0) * 100.0, 1e-9)])],
   tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:3281「"Arnaud Legoux。重みは正規分布（ずらし 0.85・幅 n/6）＝ライブラリの既定", "反転サイン", "trend", tb=_tb_pos_alma)」
状態: 確定

#### 実装 20
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3283行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（ALMA傾き%＝_alma））
直す前の文字:
~~~
   "ALMA の5本前からの変化率%", "同上。傾きの5本は本プロジェクトの流儀", "順張り値", "trend", tb=_tb_slp_alma)

~~~
直した後の文字:
~~~
   "ALMA の5本前からの変化率%", "同上。傾きの5本は本プロジェクトの流儀", "順張り値", "trend", tb=_tb_slp_alma,
   # ★K-4＝1本ごとに 1 上げる足で、5本前からの変化＝5 ÷ (5本前の ALMA＝終値 − 5 − 遅れ) × 100。
   known=lambda p: [(_up(int(p[0]) + 40), [(-1, 5.0 / ((100.0 + int(p[0]) + 39) - 5.0 - _alma_lag(int(p[0]))) * 100.0, 1e-9)])],
   tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:3283「"ALMA の5本前からの変化率%", "同上。傾きの5本は本プロジェクトの流儀", "順張り値", "trend", tb=_tb_slp_alma)」
状態: 確定

#### 実装 21
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3222行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（STC＝_stc_parts））
直す前の文字:
~~~
   "順張り値", "trend", tb=_tb_stc)

~~~
直した後の文字:
~~~
   "順張り値", "trend", tb=_tb_stc,
   # ★K-4（監査 CP60 の修正59）＝TA-Lib の逐語「When a range is zero, the fraction keeps its previous value (0 before any).」から導いた
   #   既知答え＝値段が一定なら MACD は 0 で範囲も 0＝2段とも 0 のまま。
   known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])], tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:3222「"順張り値", "trend", tb=_tb_stc)」
状態: 確定

#### 実装 22
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3225行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（STCstoch＝_stc_parts））
直す前の文字:
~~~
   "同上（Schaff Trend Cycle の1段目）", "順張り値", "trend", tb=_tb_stcstoch)

~~~
直した後の文字:
~~~
   "同上（Schaff Trend Cycle の1段目）", "順張り値", "trend", tb=_tb_stcstoch,
   known=lambda p: [(_flat(400), [(-1, 0.0, 1e-9)])], tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:3225「"同上（Schaff Trend Cycle の1段目）", "順張り値", "trend", tb=_tb_stcstoch)」
状態: 確定

#### 実装 23
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3297行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（close vs HILO%＝_tb_pos_hilo））
直す前の文字:
~~~
   "反転サイン", "none", tb=_tb_pos_hilo)

~~~
直した後の文字:
~~~
   "反転サイン", "none", tb=_tb_pos_hilo,
   # ★K-4（監査 CP60 の修正59）＝定義（Krausz＝前の13本の高値の平均を終値が上抜けたら、21本の安値の平均の線）から導いた既知答え
   #   ＝1本ごとに 1 上げる足（高値＝終値・安値＝前の終値）では、終値は常に高値の平均の上＝線は安値の平均＝終値 − 11。
   known=lambda p: [(_up(80), [(-1, (179.0 / 168.0 - 1.0) * 100.0, 1e-9)])], tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:3297「"反転サイン", "none", tb=_tb_pos_hilo)」
状態: 確定

#### 実装 24
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3475行（<モジュール直下>・監査 CP60 の修正60＝下げ続ける合成のバーの既知答えの導き方（4種の登録の前の説明））
直す前の文字:
~~~
_r(r"close vs CKSPl%", "close vs CKSPl%",
~~~
直した後の文字:
~~~
# ★K-4（監査 CP60 の修正60）＝下の CKSP・PMAX・PSAR・SAREXT の既知答えに「下げ続ける合成のバー」を足した。
#   足＝_dn(600, 1000.0, 1.0)（終値 1000 から1本ごとに 1 下げる・始値＝前の終値・高値＝始値・安値＝終値）。最後の終値 c＝401。
#   答えは定義から導いた（ライブラリは見ていない）＝
#   ・PSAR（Wilder）＝売り側。SAR_t＝SAR_{t−1}＋AF×(EP_{t−1}−SAR_{t−1})。毎本 新しい安値なので AF は 0.02 ずつ増えて 0.2 で頭打ち。
#     EP_{t−1}＝前の終値＝c＋1。SAR と EP の差 g は g←0.8×(g＋1) で 4 に収束＝SAR＝c＋5 → close vs PSAR%＝(c/(c+5)−1)×100・加速 0.2・反転 0。
#   ・SAREXT（TA-Lib）＝買いと売りの加速が同じ値なら PSAR と同じ線（絶対値に直してから割る）＝(c/(c+5)−1)×100。
#   ・CKSP（TradingView の形 p=10・x=1・q=9・ATR は Wilder）＝真の値幅は毎本 1 → ATR＝1。買い側の逆指値＝直近 q 本の max(10本高値 − ATR)
#     ＝(c＋2＋8＋10)−1＝c＋17（10本高値は 9本前の高値＝終値＋10、q 本の中で最大は 8本前）→ (c/(c+17)−1)×100。
#     売り側＝直近 q 本の min(10本安値 ＋ ATR)＝今の安値 c ＋ 1 → (c/(c+1)−1)×100。
#   ・PMAX（EMA10 ± 3×ATR10・下げでは上の帯）＝1本ごとに 1 下げる足で EMA10 の遅れは (10−1)/2＝4.5・ATR＝1 → 線＝c＋4.5＋3 → (c/(c+7.5)−1)×100。
#   値段が一定の足（0）だけでは売り側を一度も通らない（監査 CP60 の修正60 の文）。
_r(r"close vs CKSPl%", "close vs CKSPl%",
~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:3475「_r(r"close vs CKSPl%", "close vs CKSPl%",」
状態: 確定

#### 実装 25
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3475〜3482行（<モジュール直下>・監査 CP60 の修正60＝CKSPl・CKSPs の既知答えに下げ続ける足を足す）
直す前の文字:
~~~
_r(r"close vs CKSPl%", "close vs CKSPl%",
   "終値が Chande Kroll の買い側の逆指値から何%離れているか",
   "Chande & Kroll。★独立実装は書いていないが、定義から導ける既知答えで検証する＝"
   "値段が一定なら逆指値も その値に張り付くので、この列は ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
_r(r"close vs CKSPs%", "close vs CKSPs%",
   "終値が Chande Kroll の売り側の逆指値から何%離れているか", "同上",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])

~~~
直した後の文字:
~~~
_r(r"close vs CKSPl%", "close vs CKSPl%",
   "終値が Chande Kroll の買い側の逆指値から何%離れているか",
   "Chande & Kroll。★独立実装は書いていないが、定義から導ける既知答えで検証する＝"
   "値段が一定なら逆指値も その値に張り付くので、この列は ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]),
                                          (_dn(600, 1000.0, 1.0), [(-1, (401.0 / (401.0 + 17.0) - 1.0) * 100.0, 1e-6)])])
_r(r"close vs CKSPs%", "close vs CKSPs%",
   "終値が Chande Kroll の売り側の逆指値から何%離れているか", "同上",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]),
                                          (_dn(600, 1000.0, 1.0), [(-1, (401.0 / (401.0 + 1.0) - 1.0) * 100.0, 1e-6)])])

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:3475「_r(r"close vs CKSPl%", "close vs CKSPl%",」
状態: 確定

#### 実装 26
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3488行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（DPO%＝_tb_dpo））
直す前の文字:
~~~
   "反転サイン", "none", tb=_tb_dpo)

~~~
直した後の文字:
~~~
   "反転サイン", "none", tb=_tb_dpo,
   # ★K-4（監査 CP60 の修正59）＝流儀の欄の定義（終値 − n本平均を (n/2+1) 本ずらしたもの）から導いた既知答え
   #   ＝1本ごとに 1 上げる足では (n/2+1) ＋ (n−1)/2 を終値で割って%化。教科書の版（DPO教科書%）とは別の値になる。
   known=lambda p: [(_up(int(p[0]) * 2 + 40), [(-1, ((int(0.5 * int(p[0])) + 1) + (int(p[0]) - 1) / 2.0) / (100.0 + int(p[0]) * 2 + 39) * 100.0, 1e-9)])],
   tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:3488「"反転サイン", "none", tb=_tb_dpo)」
状態: 確定

#### 実装 27
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3491〜3492行（<モジュール直下>・監査 CP60 の修正60＝PMAX の既知答えに下げ続ける足を足す）
直す前の文字:
~~~
   "ライブラリの計算式。★定義から導ける既知答えで検証する＝値段が一定なら ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])

~~~
直した後の文字:
~~~
   "ライブラリの計算式。★定義から導ける既知答えで検証する＝値段が一定なら ぴったり 0・下げ続ける足なら EMA10＋3×ATR10 の上の帯（K-4）",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]),
                                          (_dn(600, 1000.0, 1.0), [(-1, (401.0 / (401.0 + 7.5) - 1.0) * 100.0, 1e-6)])])

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:3491「"ライブラリの計算式。★定義から導ける既知答えで検証する＝値段が一定なら ぴったり 0",」
状態: 確定

#### 実装 28
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3496〜3505行（<モジュール直下>・監査 CP60 の修正60＝PSAR%・PSAR加速・PSAR反転 の既知答えに下げ続ける足を足す）
直す前の文字:
~~~
   "★定義から導ける既知答えで検証する＝値段が一定なら ぴったり 0",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])
_r(r"PSAR加速", "PSAR加速",
   "パラボリック SAR の加速係数（0.02 ずつ増えて 0.2 で頭打ち）",
   "Wilder。★定義から導ける既知答えで検証する＝値段が一定なら加速しないので初期値 0.02 のまま",
   "状態量", "none", known=lambda p: [(_flat(600), [(-1, 0.02, 1e-9)])])
_r(r"PSAR反転", "PSAR反転",
   "パラボリック SAR が反転した足か。1 か 0",
   "同上。★既知答えで検証する＝値段が一定なら反転しないので 0", "状態量", "none",
   known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])

~~~
直した後の文字:
~~~
   "★定義から導ける既知答えで検証する＝値段が一定なら ぴったり 0・下げ続ける足なら売り側の SAR＝終値＋5（K-4）",
   "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]),
                                          (_dn(600, 1000.0, 1.0), [(-1, (401.0 / (401.0 + 5.0) - 1.0) * 100.0, 1e-6)])])
_r(r"PSAR加速", "PSAR加速",
   "パラボリック SAR の加速係数（0.02 ずつ増えて 0.2 で頭打ち）",
   "Wilder。★定義から導ける既知答えで検証する＝値段が一定なら加速しないので初期値 0.02 のまま・下げ続ける足なら頭打ちの 0.2（K-4）",
   "状態量", "none", known=lambda p: [(_flat(600), [(-1, 0.02, 1e-9)]), (_dn(600, 1000.0, 1.0), [(-1, 0.2, 1e-9)])])
_r(r"PSAR反転", "PSAR反転",
   "パラボリック SAR が反転した足か。1 か 0",
   "同上。★既知答えで検証する＝値段が一定なら反転しないので 0・下げ続ける足でも反転しないので 0（K-4）", "状態量", "none",
   known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]), (_dn(600, 1000.0, 1.0), [(-1, 0.0, 1e-9)])])

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:3496「"★定義から導ける既知答えで検証する＝値段が一定なら ぴったり 0",」
状態: 確定

#### 実装 29
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 3513行（<モジュール直下>・監査 CP60 の修正60＝SAREXT の既知答えに下げ続ける足を足す（符号の誤りを捕まえる））
直す前の文字:
~~~
   "この列は ぴったり 0", "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])

~~~
直した後の文字:
~~~
   "この列は ぴったり 0。下げ続ける足なら PSAR と同じ線（終値＋5・絶対値に直してから割る＝K-4）", "反転サイン", "none",
   known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)]), (_dn(600, 1000.0, 1.0), [(-1, (401.0 / (401.0 + 5.0) - 1.0) * 100.0, 1e-6)])])

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:3513「"この列は ぴったり 0", "反転サイン", "none", known=lambda p: [(_flat(600), [(-1, 0.0, 1e-9)])])」
状態: 確定

#### 実装 30
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 4246行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（THERMO%＝_tb_thermo_pct））
直す前の文字:
~~~
   tb=_tb_thermo_pct, known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])])

~~~
直した後の文字:
~~~
   tb=_tb_thermo_pct,
   # ★K-4（監査 CP60 の修正59）＝流儀の欄の定義（安値の下げ幅と高値の上げ幅の絶対値の大きい方）から導いた既知答え
   #   ＝内はらみ足（高値 101→100.5・安値 99→99.5）では 0.5 を終値 100 で割って%化＝0.5。教科書の版（THERMO原作%）は 0＝別の値になる。
   known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)]), (_thermo_in_case(80), [(-1, 0.5, 1e-9)])], tb_kind="写し")

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:4246「tb=_tb_thermo_pct, known=lambda p: [(_flat(80), [(-1, 0.0, 1e-9)])])」
状態: 確定

#### 実装 31
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 4375〜4377行（_insp_indicator_match・監査 CP60 の修正59＝検査3 で写しの独立実装が合っただけでは一致検証済みに数えない）
直す前の文字:
~~~
            elif dmax <= ref["tol"]:
                marks.append(f"独立✓({dmax:.0e})")
                verified.add(name)

~~~
直した後の文字:
~~~
            elif dmax <= ref["tol"]:
                if ref.get("tb_kind") == "写し":
                    # ★K-4（2026-10-11・監査 CP60 の修正59）＝写しの独立実装（カタログかライブラリと同じ変形を別の書き方で写した物）は
                    #   「自分と同じか」しか確かめていない＝一致しても検証済みに数えない。検証済みにするのは手計算の既知答え（③）。
                    marks.append(f"独立(写し)✓({dmax:.0e})")
                else:
                    marks.append(f"独立✓({dmax:.0e})")
                    verified.add(name)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:4375「elif dmax <= ref["tol"]:」
状態: 確定

#### 実装 32
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7333行（selftest_catalog・監査 CP60 の修正59＝検査3 と写しの印の番人2つを走らせる軽い口 selftest_match（壊すプログラム12本が承認の前の仮当ての打ち切り 900秒に入るため））
直す前の文字:
~~~
def selftest_catalog(exit_: bool = True) -> list:

~~~
直した後の文字:
~~~
def selftest_match(exit_: bool = True, with_verified: bool = False, full: bool = False):
    """検査3（参照表との照合）と、写しの印の番人2つだけを走らせる軽い口
    （工事 k4-reference-known-20261011・2026-10-11・監査 CP60 の修正59）。
    口＝`--selftest-match`（完成の条件と壊すプログラム b172〜b183 が使う）。全体の自己テスト（selftest）からも full=True で呼ぶ。
    手本＝selftest_catalog（口の形・selftest からの呼び方）。★全体の自己テストは1本 約2分かかり、承認の前の仮当て（A12）の
    打ち切り 900秒に壊すプログラム12本が入らないため、検査3 と番人だけを切り出した。
    full=False（コマンドの口）＝検査3 を「手計算の既知答えを持つ登録の列と、写しの印の列」だけに絞る（壊すプログラムが落とす相手は
    全部この中に在る。全列では写しで92秒＝12本で900秒を超えた）。full=True（selftest から）＝正しいカタログの全列。
    with_verified=True のときは (ng, 一致検証済みの列の集合) を返す（selftest が「検証済みにならない列」を数えるのに使う）。"""
    cfg = load_config()
    ng = []
    import contextlib as _cl2
    import io as _io2
    _q = _io2.StringIO()
    _t3 = np.arange(6000, dtype=float)
    _c3 = pd.Series(100 + np.sin(_t3 / 9.0) * 2 + _t3 * 0.001,
                    index=pd.date_range("2026-03-01", periods=6000, freq="5min"))
    _sb3 = pd.DataFrame({"open": _c3.shift().fillna(_c3.iloc[0]), "high": _c3 + 0.1,
                         "low": _c3 - 0.1, "close": _c3, "volume": 1.0}, index=_c3.index)
    #  ①正しいカタログで検査3 が不一致を出さない（既知答え＝定義から導いた数字と、独立実装・ライブラリの照合）
    _catm = build_catalog(cfg)
    if not full:
        _catm = [x for x in _catm if (iref.find(x[0])[0] or {}).get("known") is not None
                 or (iref.find(x[0])[0] or {}).get("tb_kind") == "写し"]
        if not _catm:
            ng.append("既知答えを持つ列・写しの印の列がカタログに1本も無い（軽い口が回せない）")
    with _cl2.redirect_stdout(_q):
        _ng3m, _v3m, _r3m = _insp_indicator_match(_sb3, cfg, catalog=_catm)
    if _ng3m:
        ng.append(f"検査3 が正しいカタログで不一致を出す（許容差の線を疑う）: {_ng3m[:3]}")
    #  ②写しの印（tb_kind="写し"）の登録は、手計算の既知答えを必ず持つ（独立実装だけでは検証済みにならないため）
    for _e in iref.REFS:
        if _e.get("tb_kind") == "写し" and _e["known"] is None:
            ng.append(f"写しの印の登録に手計算の既知答えが無い: {_e['family']}")
    #  ③写しの印の列は、既知答えを外すと「一致検証済み」に入らない（独立実装が合っても検証済みに数えない）
    _cat_cp = [x for x in build_catalog(cfg)
               if (iref.find(x[0])[0] or {}).get("tb_kind") == "写し" and (iref.find(x[0])[0] or {}).get("tb") is not None]
    if not _cat_cp:
        ng.append("写しの印の列がカタログに1本も無い（この番人が回せない）")
    else:
        _ecp = iref.find(_cat_cp[0][0])[0]
        _kn_save = _ecp["known"]
        _ecp["known"] = None
        try:
            with _cl2.redirect_stdout(_q):
                _ngcp, _vcp, _rcp = _insp_indicator_match(_sb3, cfg, catalog=[_cat_cp[0]])
        finally:
            _ecp["known"] = _kn_save
        if _cat_cp[0][0] in _vcp:
            ng.append(f"写しの独立実装だけで一致検証済みになっている: {_cat_cp[0][0]}")
    if exit_:
        for x in ng:
            print(f"  ❌ {x}")
        print(f"  検査3（{'全列' if full else '既知答えを持つ列と写しの印の列 ' + str(len(_catm)) + ' 本'}）と写しの印の番人（--selftest-match）: ❌ {len(ng)} 件")
        raise SystemExit(1 if ng else 0)
    return (ng, _v3m) if with_verified else ng


def selftest_catalog(exit_: bool = True) -> list:

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7333「def selftest_catalog(exit_: bool = True) -> list:」
状態: 確定

#### 実装 33
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7886〜7889行（selftest・監査 CP60 の修正59＝全体の自己テストから軽い口 selftest_match を呼ぶ（正しいカタログの検査3 と写しの印の番人2つ））
直す前の文字:
~~~
    with _cl2.redirect_stdout(_q):
        _ng3b, _v3b, _r3b = _insp_indicator_match(_sb3, cfg)
    if _ng3b:
        ng.append(f"検査3 が正しいカタログで不一致を出す（許容差の線を疑う）: {_ng3b[:3]}")

~~~
直した後の文字:
~~~
    # ★K-4（2026-10-11・監査 CP60 の修正59・工事 k4-reference-known-20261011）＝正しいカタログの検査3 と、写しの印の番人2つは
    #   軽い口 selftest_match に切り出した（壊すプログラムが測る口）。ここからも呼ぶ＝全体の自己テストの中身は減らさない。
    _ngm, _v3b = selftest_match(exit_=False, with_verified=True, full=True)
    ng += _ngm

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7886「with _cl2.redirect_stdout(_q):」
状態: 確定

#### 実装 34
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 8516〜8517行（<モジュール直下>・監査 CP60 の修正59＝コマンドの旗 --selftest-match を足す（selftest_catalog と同じ形））
直す前の文字:
~~~
    if "--selftest-catalog" in sys.argv:              # ★K-1・K-8・G-2 の番人だけを（工事 m2c15-indicator-six-items-20261004・壊すプログラム b128・b129・b131 が使う）
        selftest_catalog()                            # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）

~~~
直した後の文字:
~~~
    if "--selftest-catalog" in sys.argv:              # ★K-1・K-8・G-2 の番人だけを（工事 m2c15-indicator-six-items-20261004・壊すプログラム b128・b129・b131 が使う）
        selftest_catalog()                            # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）
    if "--selftest-match" in sys.argv:                # ★検査3 と写しの印の番人だけを（工事 k4-reference-known-20261011・壊すプログラム b172〜b183 が使う）
        selftest_match()                              # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:8516「if "--selftest-catalog" in sys.argv:              # ★K-1・K-8・G-2 の番人だけを（工事 m2c15-indicator-six-items-20261004・壊すプログラム b1」
状態: 確定

#### 実装 35
対象のファイル: .claude/breaks/b172_alma_weights_reversed.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: ALMA の重みを逆向き（ライブラリの元の 0.85）に戻すと、定義から導いた既知答え（1本ごとに 1 上げる足の遅れ）で検査3 が落ちる＝監査 CP60 が見つけた向きの誤りを捕まえる
# EXPECT_MSG: close vs ALMA%9: 手計算の既知答えと不一致
# b172_alma_weights_reversed — ALMA の重みを逆向き（ライブラリの元の 0.85）に戻すと、定義から導いた既知答え（1本ごとに 1 上げる足の遅れ）で検査3 が落ちる＝監査 CP60 が見つけた向きの誤りを捕まえる（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「close vs ALMA%9: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    ("ALMA", lambda d, n, distribution_offset=0.15, sigma=None: _pta6.alma(close=d.close, length=n, distribution_offset=distribution_offset, sigma=sigma)),\n'
new = '    ("ALMA", lambda d, n, distribution_offset=0.85, sigma=None: _pta6.alma(close=d.close, length=n, distribution_offset=distribution_offset, sigma=sigma)),\n'
if s.count(old) != 1:
    raise SystemExit("[b172_alma_weights_reversed] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 36
対象のファイル: .claude/breaks/b173_stc_zero_range_divides.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: STC の「範囲が 0 なら前の値を持ち越す」を外して 0 で割ると、値段が一定の足の既知答え（0）で検査3 が落ちる
# EXPECT_MSG: STC: 手計算の既知答えと不一致
# b173_stc_zero_range_divides — STC の「範囲が 0 なら前の値を持ち越す」を外して 0 で割ると、値段が一定の足の既知答え（0）で検査3 が落ちる（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「STC: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            st[i] = 100.0 * (x[i] - lo[i]) / rng[i] if rng[i] > 0 else st[i - 1]\n'
new = '            st[i] = 100.0 * (x[i] - lo[i]) / rng[i] if rng[i] >= 0 else st[i - 1]\n'
if s.count(old) != 1:
    raise SystemExit("[b173_stc_zero_range_divides] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 37
対象のファイル: .claude/breaks/b174_hilo_short_column.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: HILO の線を売り側の列に差し替えると、1本ごとに 1 上げる足の既知答え（終値 − 11 の線）で検査3 が落ちる
# EXPECT_MSG: close vs HILO%: 手計算の既知答えと不一致
# b174_hilo_short_column — HILO の線を売り側の列に差し替えると、1本ごとに 1 上げる足の既知答え（終値 − 11 の線）で検査3 が落ちる（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「close vs HILO%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '                                                                              close=d.close, high_length=high_length, low_length=low_length).iloc[:, 0] - 1) * 100)\n'
new = '                                                                              close=d.close, high_length=high_length, low_length=low_length).iloc[:, 2] - 1) * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b174_hilo_short_column] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 38
対象のファイル: .claude/breaks/b175_dpo_centered_future.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: DPO% を未来を見る版（centered=True）に戻すと、1本ごとに 1 上げる足の既知答えで検査3 が落ちる
# EXPECT_MSG: DPO%20: 手計算の既知答えと不一致
# b175_dpo_centered_future — DPO% を未来を見る版（centered=True）に戻すと、1本ごとに 1 上げる足の既知答えで検査3 が落ちる（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「DPO%20: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '     _pta6.dpo(close=d.close, length=n, centered=False) / d.close * 100)\n'
new = '     _pta6.dpo(close=d.close, length=n, centered=True) / d.close * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b175_dpo_centered_future] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 39
対象のファイル: .claude/breaks/b176_sarext_sign_not_abs.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: SAREXT の絶対値を外す（売り側が負の数のまま）と、下げ続ける足の既知答えで検査3 が落ちる＝監査 CP60 の符号の誤りを捕まえる（直す前は値段が一定の足だけで通った）
# EXPECT_MSG: close vs SAREXT%: 手計算の既知答えと不一致
# b176_sarext_sign_not_abs — SAREXT の絶対値を外す（売り側が負の数のまま）と、下げ続ける足の既知答えで検査3 が落ちる＝監査 CP60 の符号の誤りを捕まえる（直す前は値段が一定の足だけで通った）（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「close vs SAREXT%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'accelerationmaxshort=accelerationmaxshort).abs() - 1) * 100)\n'
new = 'accelerationmaxshort=accelerationmaxshort) - 1) * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b176_sarext_sign_not_abs] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 40
対象のファイル: .claude/breaks/b177_psar_af_column.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: PSAR加速 を反転の列に差し替えると、下げ続ける足の既知答え（頭打ちの 0.2）で検査3 が落ちる（値段が一定の足では 0.02 の既知答えも落ちる）
# EXPECT_MSG: PSAR加速: 手計算の既知答えと不一致
# b177_psar_af_column — PSAR加速 を反転の列に差し替えると、下げ続ける足の既知答え（頭打ちの 0.2）で検査3 が落ちる（値段が一定の足では 0.02 の既知答えも落ちる）（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「PSAR加速: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '_reg("PSAR加速", "PSAR加速", False, lambda d, af0=None, af=None, max_af=None: _ps(d, af0=af0, af=af, max_af=max_af).iloc[:, 2])\n'
new = '_reg("PSAR加速", "PSAR加速", False, lambda d, af0=None, af=None, max_af=None: _ps(d, af0=af0, af=af, max_af=max_af).iloc[:, 3])\n'
if s.count(old) != 1:
    raise SystemExit("[b177_psar_af_column] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 41
対象のファイル: .claude/breaks/b178_cksp_long_short_swapped.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: CKSP の買い側を売り側の列に差し替えると、下げ続ける足の既知答え（終値＋17 の線）で検査3 が落ちる（値段が一定の足では見分けられない）
# EXPECT_MSG: close vs CKSPl%: 手計算の既知答えと不一致
# b178_cksp_long_short_swapped — CKSP の買い側を売り側の列に差し替えると、下げ続ける足の既知答え（終値＋17 の線）で検査3 が落ちる（値段が一定の足では見分けられない）（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「close vs CKSPl%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '_reg("close vs CKSPl%", "close vs CKSPl%", True, lambda d, p=None, x=None, q=None: (d.close / _ck(d, p=p, x=x, q=q).iloc[:, 0] - 1) * 100)\n'
new = '_reg("close vs CKSPl%", "close vs CKSPl%", True, lambda d, p=None, x=None, q=None: (d.close / _ck(d, p=p, x=x, q=q).iloc[:, 1] - 1) * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b178_cksp_long_short_swapped] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 42
対象のファイル: .claude/breaks/b179_pmax_ma_of_high.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: PMAX の移動平均の入力を高値にすると、下げ続ける足の既知答え（EMA10＋3×ATR10 の線）で検査3 が落ちる（値段が一定の足では見分けられない）
# EXPECT_MSG: close vs PMAX%: 手計算の既知答えと不一致
# b179_pmax_ma_of_high — PMAX の移動平均の入力を高値にすると、下げ続ける足の既知答え（EMA10＋3×ATR10 の線）で検査3 が落ちる（値段が一定の足では見分けられない）（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「close vs PMAX%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '     lambda d, length=None, multiplier=None: (d.close / _pta6.pmax(high=d.high, low=d.low, close=d.close, length=length, multiplier=multiplier) - 1) * 100)\n'
new = '     lambda d, length=None, multiplier=None: (d.close / _pta6.pmax(high=d.high, low=d.low, close=d.high, length=length, multiplier=multiplier) - 1) * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b179_pmax_ma_of_high] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 43
対象のファイル: .claude/breaks/b180_vwap_volume_weight_dropped.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: VWAP の分子の出来高の重みを外すと、最後の1本だけ出来高 9 の既知答えで検査3 が落ちる（出来高が全部 1 の足では見分けられない）
# EXPECT_MSG: close vs VWAP%288: 手計算の既知答えと不一致
# b180_vwap_volume_weight_dropped — VWAP の分子の出来高の重みを外すと、最後の1本だけ出来高 9 の既知答えで検査3 が落ちる（出来高が全部 1 の足では見分けられない）（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「close vs VWAP%288: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '_reg("close vs VWAP%", "close vs VWAP%{}", True, lambda d, n: (d.close / ((d.close * d.volume).rolling(n).sum()\n     / d.volume.rolling(n).sum().replace(0, np.nan)) - 1) * 100)\n'
new = '_reg("close vs VWAP%", "close vs VWAP%{}", True, lambda d, n: (d.close / ((d.close * (d.volume * 0 + 1.0)).rolling(n).sum()\n     / d.volume.rolling(n).sum().replace(0, np.nan)) - 1) * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b180_vwap_volume_weight_dropped] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 44
対象のファイル: .claude/breaks/b181_thermo_ma_column.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: THERMO% を EMA の列に差し替えると、内はらみ足の既知答え（0.5）で検査3 が落ちる（値段が一定の足では見分けられない）
# EXPECT_MSG: THERMO%: 手計算の既知答えと不一致
# b181_thermo_ma_column — THERMO% を EMA の列に差し替えると、内はらみ足の既知答え（0.5）で検査3 が落ちる（値段が一定の足では見分けられない）（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「THERMO%: 手計算の既知答えと不一致」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '_reg("THERMO%", "THERMO%", False, lambda d: _th(d).iloc[:, 0] / d.close * 100)\n'
new = '_reg("THERMO%", "THERMO%", False, lambda d: _th(d).iloc[:, 1] / d.close * 100)\n'
if s.count(old) != 1:
    raise SystemExit("[b181_thermo_ma_column] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 45
対象のファイル: .claude/breaks/b182_copy_mark_without_known.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 写しの印の登録から既知答えを外すと、自己テストの番人①（写しの印の登録は既知答えを必ず持つ）が落ちる
# EXPECT_MSG: 写しの印の登録に手計算の既知答えが無い: close vs HILO%
# b182_copy_mark_without_known — 写しの印の登録から既知答えを外すと、自己テストの番人①（写しの印の登録は既知答えを必ず持つ）が落ちる（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/indicator_reference_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「写しの印の登録に手計算の既知答えが無い: close vs HILO%」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicator_reference_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '   "反転サイン", "none", tb=_tb_pos_hilo,\n   # ★K-4（監査 CP60 の修正59）＝定義（Krausz＝前の13本の高値の平均を終値が上抜けたら、21本の安値の平均の線）から導いた既知答え\n   #   ＝1本ごとに 1 上げる足（高値＝終値・安値＝前の終値）では、終値は常に高値の平均の上＝線は安値の平均＝終値 − 11。\n   known=lambda p: [(_up(80), [(-1, (179.0 / 168.0 - 1.0) * 100.0, 1e-9)])], tb_kind="写し")\n'
new = '   "反転サイン", "none", tb=_tb_pos_hilo,\n   # ★K-4（監査 CP60 の修正59）＝定義（Krausz＝前の13本の高値の平均を終値が上抜けたら、21本の安値の平均の線）から導いた既知答え\n   #   ＝1本ごとに 1 上げる足（高値＝終値・安値＝前の終値）では、終値は常に高値の平均の上＝線は安値の平均＝終値 − 11。\n   tb_kind="写し")\n'
if s.count(old) != 1:
    raise SystemExit("[b182_copy_mark_without_known] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
finish

~~~
根拠の抜き書き: .claude/breaks/b142_rci_list_stale.sh:1「#!/bin/bash」
状態: 確定

#### 実装 46
対象のファイル: .claude/breaks/b183_copy_verified_by_tb_alone.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 検査3 の「写しの独立実装が合っただけでは検証済みに数えない」を外すと、自己テストの番人②が落ちる
# EXPECT_MSG: 写しの独立実装だけで一致検証済みになっている
# b183_copy_verified_by_tb_alone — 検査3 の「写しの独立実装が合っただけでは検証済みに数えない」を外すと、自己テストの番人②が落ちる（工事 k4-reference-known-20261011・2026-10-11）
#   守っているもの＝完成の条件の軽い口（selftest_match＝検査3 と写しの印の番人）（observe_diag.py --selftest-match）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（k4_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-match が「写しの独立実装だけで一致検証済みになっている」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            elif dmax <= ref["tol"]:\n                if ref.get("tb_kind") == "写し":\n                    # ★K-4（2026-10-11・監査 CP60 の修正59）＝写しの独立実装（カタログかライブラリと同じ変形を別の書き方で写した物）は\n                    #   「自分と同じか」しか確かめていない＝一致しても検証済みに数えない。検証済みにするのは手計算の既知答え（③）。\n                    marks.append(f"独立(写し)✓({dmax:.0e})")\n                else:\n                    marks.append(f"独立✓({dmax:.0e})")\n                    verified.add(name)\n'
new = '            elif dmax <= ref["tol"]:\n                marks.append(f"独立✓({dmax:.0e})")\n                verified.add(name)\n'
if s.count(old) != 1:
    raise SystemExit("[b183_copy_verified_by_tb_alone] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-match
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 46 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 写しの既知答えは、原典の数字でなく定義から導いた式にする | 修正59 の補足の例（ALMA の重み）のように原典に数字が在る物は無い。定義から合成の足で1つに決まる値なら、写しが写した誤り（向き・列・未来・重み）で値が変わる（読むもの宣言のとおり） | 既知答えを足さず印だけ付ける（検証済みが減る） |
| 2 | 下げ続ける足は終値 1000 から1本ごとに 1 下げる600本 | 前から在る部品 _dn で作れる。600本で漸化式が収束し、終値が負にならない | 200 から下げる（既存の _dn の既定＝600本で負になる） |
| 3 | 写しの独立実装が合っただけでは検証済みに数えない | 修正59 の文「照合は自分と同じかしか確かめていない」。検証済みにするのは既知答え | 写しの独立実装を照合から外す（独立✗ の検出まで失う） |
| 4 | 3種の独立の実装は別の書き方にし、式の出どころは変えない | 監査 CP73 の Q8 の (c)＝同じ文字の写しどうしでは、両方に同じ誤りが入ると見つからない | 説明の文だけ（CP73 の修正2 で済）のまま |
| 5 | 名指しの10件の外の登録は未判定（None）のまま | 1件ずつの判定が要る（272件）。この工事の範囲の外 | 全部に印を付ける |
| 6 | 設計書の監査を出す | 新しいコードと既知答えの値が入る（判断が入る） | 飛ばす（判断が入らない工事の決まりは当たらない） |
| 7 | 壊すプログラム12本は、検査3 を既知答えを持つ列と写しの印の列に絞った軽い口（--selftest-match）で測る | 承認の前の仮当て（A12）の壊すプログラムの打ち切りは 900秒。全体の自己テスト（1本 約142秒）では12本が入らず、試しの設計書の全部の検査が打ち切りで落ちた。全列の軽い口でも写しで92秒（12本で 900秒を超える）。壊すプログラムが落とす相手（既知答えの不一致・番人①②）は絞った列の中に全部 在る。全体の自己テストは全列で呼ぶので、守りは減らない | 全体の自己テストで測る（打ち切りで落ちた）／全列の軽い口で測る（12本で 900秒を超える）／壊すプログラムを減らす（守りが減る） |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=acc7e8dcb0ec47f7 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b172_alma_weights_reversed.sh` | #1 | ALMA の重みを逆向き（ライブラリの元の 0.85）に戻す |
| `b173_stc_zero_range_divides.sh` | #2 | 範囲 0 で割る形にする |
| `b174_hilo_short_column.sh` | #3 | 線を売り側の列に差し替える |
| `b175_dpo_centered_future.sh` | #4 | 未来を見る版（centered=True）に戻す |
| `b176_sarext_sign_not_abs.sh` | #5 | 絶対値を外す（監査 CP60 の符号の誤りに戻す） |
| `b177_psar_af_column.sh` | #6 | 加速の列を反転の列に差し替える |
| `b178_cksp_long_short_swapped.sh` | #7 | 買い側を売り側の列に差し替える |
| `b179_pmax_ma_of_high.sh` | #8 | 移動平均の入力を高値にする |
| `b180_vwap_volume_weight_dropped.sh` | #9 | 分子の出来高の重みを外す |
| `b181_thermo_ma_column.sh` | #10 | EMA の列に差し替える |
| `b182_copy_mark_without_known.sh` | #11 | close vs HILO% の既知答えを外す |
| `b183_copy_verified_by_tb_alone.sh` | #12 | 検査3 の直しを戻す |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 定義から導いた答えが、ライブラリの初期値の作りで 1e-6 を超えてずれる | 写しで7つとも 1e-6 以内で合った（4-0 の③）。ずれたら、答えを合わせずに 3-2 で出す |
| 2 | 写しの印の登録が増えると、検証済みの数が減る | 写しの16登録は全部 既知答えを持つ（番人①）。検証済みの数は変わらない |
| 3 | 3種の別の書き方が scipy を要る | 参照表は2つ目の照合で scipy を既に使う（ext2_ready）。写しで全体の自己テストが通った |
| 4 | 絞った軽い口が通っても、絞った列の外で検査3 が落ちる | 全体の自己テスト（--selftest）が軽い口を全列で呼ぶ（4-12 の1）。完成の条件の壊すプログラムは軽い口、G2・H2 の取り直しと監査に出す前のチェックは全体の自己テストを走らせる |
| 5 | 軽い口が 12本×約63秒で、まだ打ち切り 900秒に近い | 写しで12本を並べて走らせ、900秒の中に入った（k4_draft_build.py の [8]・k4_check_run.log）。超えたら、そこで止めて まこさんに報告する（6-3 の下の文） |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（--design） | 1分未満 | 前の工事で、当てる道具は1秒未満で終わった |
| 全体の自己テスト | 142秒 | 4-14 |
| 壊すプログラム | 1本あたり約 63秒（軽い口 --selftest-match）×12本 | 写しで壊し方を並べて走らせた（k4_draft_build.py の [8]）。承認の前の仮当ての打ち切り 900秒に入る |
| 監査に出す前のチェック | 約10分 | 前の工事の実測（pre_audit_check.py --run） |
| まこさんの承認 | この工事の設計書1回 | 4-4 |
| 設計書の監査・実装の監査 | 各1通 | まこさん「CCの案でOK」の③ |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝参照表の「教科書の独立実装」の10件が、カタログかライブラリの変形を別の書き方で写した物で、検査3 の照合が「自分と同じか」しか確かめていなかった（監査 CP60 の修正59・一般の観点④）。4種の既知答えが「値段が一定なら 0」だけで売り側を通らなかった（修正60・観点⑥）。だから ALMA の向き・STC の式・SAREXT の符号の誤りが「一致検証済み」で通った。この工事で、写しの印を付け、写しの独立実装だけでは検証済みにせず、定義から導いた既知答えで検証する。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。材料の値も変わりません。変わるのは、材料の検査が誤りを捕まえる力です。

**③ root か symptom か**＝root です。検査が「自分と同じか」しか見ていなかったことが原因で、それを直します。

**④ ベースアップ**＝既知答えの定義は、参照表の定義・流儀の欄の文と、監査 CP60 の §5 の原典の逐語（TradingView の ALMA・TA-Lib の STC と SAREXT・LuxAlgo の HILO・StockCharts の VWAP）から取った。Wilder の PSAR・Chande & Kroll・PMax の作りは、監査 CP60 の4節の表と、ライブラリの実物（pandas_ta_classic の trend/psar.py・sarext.py・cksp.py・pmax.py）で確かめた。答えの数字はライブラリから写していない。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。既知答えは合成の足から定義で導いた式です。壊し方の値も、当てた後の中身の行から道具が取りました。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝参照表の検査の守りを直す（写しの印・定義から導いた既知答え・下げ続ける足の既知答え・3種の別の書き方・検査3 の数え方と番人）。材料の値と設定は変えない。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

［自動］左の2列は要件の正本・右の2列は まこさんが OK した案の【7-3b】
**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。条件をつなぐものではなく、検査の守りを直すだけです |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 探す値には触りません |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **既知答えが、本物の値動きでの正しさまで見るか** | 見ません。合成の足で、向き・列・未来・重み・符号を見るだけです |
| **名指しの10件の外の独立実装が写しかどうか** | 見ません。未判定（None）のままです |
| **定義から導いた答えが、定義の読み違いでないか** | 写しでライブラリの実物と合ったことまで。定義の読みは設計書の監査とまこさんの目です |
| **軽い口（コマンドから呼ぶ --selftest-match）が、絞った列の外の検査3 まで見るか** | 見ません。既知答えを持つ列と写しの印の列だけです。全列は全体の自己テスト（--selftest）が見ます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=738f33a100f59dae gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝indicator_reference_diag.py・observe_diag.py と、新しい壊すプログラムを【7-8】に書いた。主なファイルは observe_diag.py（検査3 の照合本体）。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝observe_diag.py・触る関数は道具が構文木の差から数えた）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム（NEW_FILE）。手本は b142（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝「独立実装と一致した」を「教科書どおり」と読み替えた（監査 CP60 の修正59 の欠陥）。この工事は、写しの印を付けて読み替えを機械で止める。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 新しい計算は材料に足さない（既知答えは検査の中だけ）。当てた後に H2 を取り直す。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 行番号を指す文書は、当てた後に動く（indicator_reference_diag.py・observe_diag.py に行が増える）。設計書の行番号は当てる前の実物のもの。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、探す文字の数が当てる前と後で同じことを道具が数えた（4-13 の4）。前からの壊すプログラムが走らせるコマンドの旗は変えない。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムが測るのは、観察の道具の軽い口（--selftest-match＝既知答えを持つ列と写しの印の列の検査3 と、写しの印の番人2つ）で、本物の結果の置き場には書かない。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 触る関数（DESIGN_CONTRACT の impl_functions・道具が書いた）＝indicator_reference_diag.py：<モジュール直下>・_alma_lag・_r・_ssf2_avg・_tb_sqz_carter・_vidya_cmo／observe_diag.py：<モジュール直下>・_insp_indicator_match・selftest・selftest_match。self_check_calls と must_use の名前は、当てた後の構文木に在ることを道具が ast で照らした。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足すコマンドの旗は1つ（observe_diag.py の --selftest-match・4-9）。資料の表・設定ファイルは触らない。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=k4-reference-known-20261011）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝観察の道具の既知答え・写しの印の番人2つ・壊すプログラム（わざと壊して落ちるか）。写しで走らせ、全部 通った。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | F-2＝close vs ALMA% の既知答え（定義から導いた遅れ）が通る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-match` | 実経路 | ALMA の重みを逆向き（ライブラリの元の 0.85）に戻す | `b172_alma_weights_reversed.sh` | — | **未着手** |
| 2 | F-2＝STC の既知答え（範囲が 0 なら前の値）が通る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-match` | 実経路 | 範囲 0 で割る形にする | `b173_stc_zero_range_divides.sh` | — | **未着手** |
| 3 | F-2＝close vs HILO% の既知答え（終値 − 11 の線）が通る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-match` | 実経路 | 線を売り側の列に差し替える | `b174_hilo_short_column.sh` | — | **未着手** |
| 4 | F-2＝DPO% の既知答え（(n/2+1)＋(n−1)/2）が通る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-match` | 実経路 | 未来を見る版（centered=True）に戻す | `b175_dpo_centered_future.sh` | — | **未着手** |
| 5 | F-3＝close vs SAREXT% の下げ続ける足の既知答え（終値＋5・絶対値）が通る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-match` | 実経路 | 絶対値を外す（監査 CP60 の符号の誤りに戻す） | `b176_sarext_sign_not_abs.sh` | — | **未着手** |
| 6 | F-3＝PSAR加速 の下げ続ける足の既知答え（頭打ち 0.2）が通る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-match` | 実経路 | 加速の列を反転の列に差し替える | `b177_psar_af_column.sh` | — | **未着手** |
| 7 | F-3＝close vs CKSPl% の下げ続ける足の既知答え（終値＋17）が通る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-match` | 実経路 | 買い側を売り側の列に差し替える | `b178_cksp_long_short_swapped.sh` | — | **未着手** |
| 8 | F-3＝close vs PMAX% の下げ続ける足の既知答え（EMA10＋3×ATR10）が通る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-match` | 実経路 | 移動平均の入力を高値にする | `b179_pmax_ma_of_high.sh` | — | **未着手** |
| 9 | F-2＝close vs VWAP% の既知答え（出来高 9 の足）が通る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-match` | 実経路 | 分子の出来高の重みを外す | `b180_vwap_volume_weight_dropped.sh` | — | **未着手** |
| 10 | F-2＝THERMO% の既知答え（内はらみ足 0.5）が通る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-match` | 実経路 | EMA の列に差し替える | `b181_thermo_ma_column.sh` | — | **未着手** |
| 11 | F-1・F-5＝写しの印の登録は既知答えを必ず持つ（番人①） | `python3 scripts/priority_rebuild/observe_diag.py --selftest-match` | 実経路 | close vs HILO% の既知答えを外す | `b182_copy_mark_without_known.sh` | — | **未着手** |
| 12 | F-5＝写しの独立実装だけでは一致検証済みにならない（番人②） | `python3 scripts/priority_rebuild/observe_diag.py --selftest-match` | 実経路 | 検査3 の直しを戻す | `b183_copy_verified_by_tb_alone.sh` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=6de766d196828c63 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/observe_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `_insp_indicator_match` | 4286 |
| `selftest` | 7467 |
| `selftest_match` | （この関数は実物に無い） |
| `build_catalog` | 1602 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 196件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=133f1835c5512b2f gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/observe_diag.py",
  "_impl_file の意味": "照らす相手は実在するファイル。検査3 の照合本体（_insp_indicator_match）と自己テスト（selftest）が在る、観察の道具を照らす。参照表（indicator_reference_diag.py）の直しは TARGET と impl_functions で照らす。",
  "impl_functions": {
    "scripts/priority_rebuild/indicator_reference_diag.py": [
      "<モジュール直下>",
      "_alma_lag",
      "_r",
      "_ssf2_avg",
      "_tb_sqz_carter",
      "_vidya_cmo"
    ],
    "scripts/priority_rebuild/observe_diag.py": [
      "<モジュール直下>",
      "_insp_indicator_match",
      "selftest",
      "selftest_match"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数（実装の指示を全部 当てる前と後の構文木を関数ごとに比べて、k4_proposal_build.py が数えた）。",
  "self_check_calls": [
    "_insp_indicator_match",
    "selftest",
    "selftest_match",
    "build_catalog"
  ],
  "_self_check_calls の意味": "実装の後の observe_diag.py に在るはずの、この工事が直す関数の名前。",
  "must_use": {
    "_insp_indicator_match": [
      "build_catalog"
    ],
    "selftest": [
      "selftest_match"
    ]
  },
  "_must_use の意味": "検査3 の照合本体が、材料のカタログ（build_catalog）を読む（k4_proposal_build.py が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は、参照表の検査の守りを直すだけ。外から読む一覧の形（カタログの1件の形・設定の欄）は変えない。参照表の登録の欄 tb_kind は増えるが、既定 None で既存の登録は変わらない。",
  "generated_from": {
    "impl_functions": "当てる前と後の関数ごとの構文木の差（k4_proposal_build.py が数えた）",
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
  "selftest_match": [
   "build_catalog",
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
   "selftest_match",
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
  "--selftest-match",
  "--selftest-rank-demand",
  "--selftest-rank-resume"
 ]
}
```

<!-- ACC_SPEC_END -->

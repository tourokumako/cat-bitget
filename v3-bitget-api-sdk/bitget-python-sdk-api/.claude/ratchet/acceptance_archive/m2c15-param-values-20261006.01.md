<!-- ARC iter="m2c15-param-values-20261006" -->

# 設計書｜指標の修正の全体の表の2回目＝パラメータ。M2-C-15

TARGET: scripts/priority_rebuild/engine_tuner_exec.py, scripts/priority_rebuild/engine_tuner_gen.py, scripts/priority_rebuild/gen_materials.py, scripts/priority_rebuild/observe_config.json, scripts/priority_rebuild/observe_diag.py, scripts/priority_rebuild/recipes/search_limits.json, .claude/breaks/b137_material_params_ignored.sh, .claude/breaks/b138_keep_name_dropped.sh, .claude/breaks/b139_range_excludes_keep.sh
NEW_FILE: .claude/breaks/b137_material_params_ignored.sh, .claude/breaks/b138_keep_name_dropped.sh, .claude/breaks/b139_range_excludes_keep.sh
MODEL: .claude/breaks/b131_industry_map_prev_pivot_gone.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2c15-param-values-20261006/ok_p1a_20261006`・`m2c15-param-values-20261006/ok_r3_20261006`・`m2c15-param-values-20261006/okd_p1a_20261006`・`m2c15-param-values-20261006/okd_r3_20261006`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2c15-param-values-20261006/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-param-values-20261006 --write`。検出＝`--work m2c15-param-values-20261006 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=ee9c8bd999b17aca gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2c15-param-values-20261006/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2c15-param-values-20261006/ok_p1a_20261006.txt`（まこさんの発言）・`verbatim/m2c15-param-values-20261006/ok_r3_20261006.txt`（まこさんの発言）・`verbatim/m2c15-param-values-20261006/okd_p1a_20261006.txt`（まこさんが OK した CC の文）・`verbatim/m2c15-param-values-20261006/okd_r3_20261006.txt`（まこさんが OK した CC の文）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝579 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_p1a_20261006` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_r3_20261006` | V01〜V02（2 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_p1a_20261006` | V01〜V06（6 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_r3_20261006` | V01〜V41（41 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_r3_20261006` | V42〜V148（107 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V149〜V154（6 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V155〜V159（5 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V160〜V172（13 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V173〜V180（8 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V181〜V189（9 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V190〜V201（12 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V202〜V203（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V204〜V205（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V206〜V209（4 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V210〜V211（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V212〜V213（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V214〜V219（6 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V220〜V228（9 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V229〜V234（6 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V235〜V236（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V237〜V238（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V239〜V240（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V241〜V246（6 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V247〜V421（175 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V422〜V431（10 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V432〜V439（8 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V440〜V448（9 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V449〜V455（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V456〜V457（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V458〜V459（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V460〜V464（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V465〜V475（11 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V476〜V496（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V497〜V502（6 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V503〜V566（64 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_r3_20261006` | V567〜V570（4 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
指標の修正の全体の表の2回目（パラメータ）です。まこさん決定「A」のとおり、材料の名前の一覧を、教科書の最初の値（スキャル∪デイトレ）に入れ替え、最後のチューニングで探す範囲を設定に書きます。中身は5つです。①P-1＝観察の道具の設定（observe_config.json）に、指標ごとの一覧（80種）を道具が書く。一覧＝最初の値（名前の軸に当たる軸）＋残す名前（V9 19本・採用中の戦略と確認のレシピ 9本）。材料の一覧を作る関数（build_catalog）は、一覧に在る種類を、ほかの指標の期間の一覧を使わずに作る。材料は 576列 → 476列 になる（消える 153本・増える 53本・両方に在る 423本の値は変わらない）。名前に出ない軸がある 38種の最初の値は、列の計算を変えずに別の欄へ書く。②P-2＝探す範囲（search_limits.json の material_param_ranges）に、修正対応表の範囲（名前の軸・104種）を道具が書く。同じ事実を書く説明5か所をそろえる。③P-3＝範囲の端の値で作った列が、ライブラリが黙って既定に戻したものでないかを写しで測った（当たり 0件）。④P-4＝範囲が決まらない・範囲が1点のまま・資料に行が無い 33種を、値を埋めずに設定の注記に並べる。⑤P-5＝29種のうち26種は前の工事の名前に出さない引数で受け取れている。残り3種は直さない（3-1）。★数の訂正＝決めていただいたときの案（okd_p1a_20261006）の「45本 増えて130本 減ります」は、名前に出ない軸がある種類の名前の軸を数えていなかった。その扱い（記録の返信 c717283a の「A のときの扱い」）を入れて道具が数え直すと、増える 53本・消える 153本になる。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 指標ごとの一覧の設定（P-1） | `grep -n -F '"material_params"' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json` | 実装の前は、無い。実装の後は、在る | （終了コード 1） |
| 材料の一覧を作る関数が、指標ごとの一覧を読む所（P-1） | `grep -n -F '_per_done' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、build_catalog の中に在る | （終了コード 1） |
| 探す範囲の設定（P-2） | `grep -n -F '"material_param_ranges": {}' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json` | 実装の前は、空の形が在る。実装の後は、無い（範囲が書いてある） | 44:  "material_param_ranges": {},（終了コード 0） |
| 範囲の置き場所の説明（P-2 の同じ事実） | `grep -n -F 'いまは空です' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 実装の前は、在る。実装の後は、無い | 248:      **いまは空です。**空のあいだは、上のカタログ由来の範囲を使います。（終了コード 0） |
| この工事の番人（P-1・P-2） | `grep -n -F '工事 m2c15-param-values-20261006 の番人' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、軽い口 selftest_catalog の中に在る | （終了コード 1） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

［自動］印のファイル・型の表・格子と範囲
<!-- ACC_MATERIALS_START hash=8faab679aa44dc33 gen_acceptance.py が自動生成＝手で書き換えない -->
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
| 1 | 名前に出さない引数の範囲を書き、探す側が範囲から渡す仕組み（KST の本数・HWMA の係数・PSAR と CKSP の値・傾きの比べる本数 k ほか） | 範囲の設定は名前の軸しか持てない（範囲を作る関数が、軸の数が名前と違えば止める）。探す側をつなぐのは工事2 | 読むもの宣言の入れないもの・next_step |
| 2 | 名前に出ない軸の最初の値を、列の計算に渡すこと | 列の計算を変えずに別の欄へ書く。渡すのは工事2 | まこさん決定「A」（記録の返信 c717283a） |
| 3 | P-5 の残り3種を直すこと（THERMO%・swing高値距離・swing安値距離） | THERMO% は、ライブラリの本数が平らにする線（THERMO比 の分母）にだけ効き、THERMO% の列には効かない＝パラメータが無い（observe_diag.py の _th・pandas_ta_classic の thermo.py:14〜24）。swing の2種は、列が全部 close vs n本高値% と同じとして省いてあり（重複を外す一覧）、教科書のパラメータ（前後 N 本）は、すでに在る fractal高値距離%(k) の k と同じ定義（indicator_params_review の元の指標の欄） | worklog 20261006 §18・まこさん決定「A」（記録の返信 c717283a） |
| 4 | 列の計算に使われない軸を直すこと（S-Rタッチ1時間ATR の倍率と ATR の本数・PVO と TSI の線のシグナルの本数） | 前から在る作り。この工事の直しが原因ではない（写しで、2種類の値動きのどちらでも列が変わらないと測った）。直し方（名前から外すか・計算に届かせるか）は、作りの違いの仕分け（K-7）か帯の部品（B-1）で決める | r3_draft_build.py の [6]（r3_check.json の P-3） |
| 5 | P-5 の一文の「参照の計算（indicator_reference_diag.py の _stc_parts・_slope など）も同じパラメータを受ける形にする」 | 名前に出さない引数を受け取る形は前の工事で入れたが、参照の計算は、何も渡さないときの列だけを照らす（前の工事の やらないこと Y-2「別の値を渡した列を、参照表で照らすこと」）。探す側が別の値を渡し始める工事2 で一緒に直す | 前の工事のやることの表 Y-2・worklog 20261004 §35 |
| 6 | P-2 の一文のうち、名前に出ない軸の範囲（監査 CP60 の修正64 の PSAR・CKSP・ALMA の σ と offset、HWMA の係数3つ＝0〜1、傾きの比べる本数 k） | 名前の形を変えない（まこさん「指標名に…値を固定で入れて…やめてほしい」）ので、どれも名前に出ない軸になった。範囲の設定は名前の軸しか持てない＝工事2。ALMA の本数（名前の軸）は、この工事で範囲を書く | req_no_value_in_name_20261004・engine_tuner_gen.py の material_ranges |
| 7 | P-3 の一文のきっかけの HWMA（hwma.py:36＝0 以下を黙って既定に戻す）の照らし | HWMA の係数は名前に出ない軸なので、この工事の範囲に入らない。範囲を書く工事2 で、同じ照らし（端の値とまん中の値の列を比べる）をかける | 監査 CP60 の修正33 の根拠・r3_draft_build.py の [6] |
| 8 | G-1 の一文のうち、新しく足す材料（K-3 の教科書の版・B-1 の帯の部品・S-1 の部品）を「使う」にすることと、DPO の対応（TA_CLASS_MAP） | その材料を足すのは3回目。この工事の G-1 は、表の作り直しと再承認、段の候補と出口の元データの名前の照らし | まこさん「分ける」（ok_split_20261004） |
| 9 | 教科書の版を足す直し（K-3）・帯の部品（B-1）・S1 の部品（S-1）・作りの違いの仕分け（K-7）・検査の直し（K-4）・役割と閾値（R-1・T-1） | 3回目・4回目 | まこさん「分ける」（ok_split_20261004） |
| 10 | オフの指標（使わない116種）を直すこと | 今は対応しない | まこさん「オフは現状は対応しなくてよい」（2026-10-04） |
| 11 | 成績表（material_ranking.json）の作り直し | M2-D-8 で、まこさんの OK の後に走らせる | 読むもの宣言の入れないもの |
| 12 | RSI7・RSI9・RSI14・RSI21 と、V9 が使う指標の名前を変えること | そのままでよい。この工事では、残す名前に入れて番人で守る | まこさん（req_v9_indicators_on_20261004） |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 名前の軸と資料の軸の対応（18種）。決めていただいたときの文は「プログラムがパラメータの名前で照らします。照らせない軸は『決まらない』と書いて並べます」。実物は、資料とコードでパラメータの名前の書き方が違い（例＝KAMA の n と er_period）、プログラムで名前が一致した種類は0種だった。私が、計算式の引数の名前と資料のパラメータの名前を並べて、18種の対応を決めた（4-0 の⑤の表）。対応を使わないと、この18種は一覧も範囲も書けない | 私の対応を使う（根拠の表を設計書に載せ、監査で確かめていただく） | 記録の返信 c717283a・p1p5_survey.py --axes・r3_draft_build.py の AXIS_MAP |
| 2 | ROC の範囲を広げること。修正対応表の範囲は 9〜14 で、採用中の戦略（E38 の実行時の別名）と確認のレシピが使う ROC24 が外に出る | 9〜24 に広げる（まこさん決定 2026-10-04 の①＝教科書の範囲と最初の値がぶつかる軸は範囲を広げて含める、と同じ型）。広げないと、engine_tuner は E38 の ROC24 に届かない | r3_names.json の広げた範囲・worklog 20261004 §10 |
| 3 | MACD の3種（MACD線%・MACDシグナル線%・MACDヒスト%）の範囲は、短い方 3〜12 と長い方 10〜26 が重なる（10〜12）。範囲の中に、短い方が長い方以上になる組が在る | この工事では範囲を修正対応表のとおり書き、「短い方 < 長い方」の決まりは、探す側をつなぐ工事2 に入れる（範囲を作る関数の説明の「軸どうしの関係は、この表に持っていません」と同じ扱い）。それまでの間、engine_tuner がその組を引くと、線の向きが逆の MACD になる | r3_names.json の軸の順が入れ替わる組・engine_tuner_gen.py の material_ranges の説明 |
| 4 | 目的の照合（purpose_check.md）の条件の書き方。この工事は探索の経路のファイルを書き替えるので、目的ゲートは「変えない」を書かせない | 事実だけを書く。パラメータ＝「材料の一覧が教科書の最初の値になり、探す範囲が修正対応表の範囲になる」。閾値＝「探し方は今のまま。消える列の閾値は探さなくなる」。時間足＝「今のまま」 | enforce_purpose_gate.py の「変えない」の決まり・前の工事の 3-2 |
| 5 | 成績表（material_ranking.json）と名前の食い違い。消える 153本は、成績表の行が引けなくなる。増える 53本は、成績表に行が無い。どちらも、成績表を作り直す（M2-D-8）まで、段の候補の順位に出ない | このまま進める（成績表の作り直しは M2-D-8） | r3_names.json |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、材料の名前の一覧を教科書の最初の値にし、最後のチューニングで探す範囲を設定に書く直しです。**まこさんの6項目の3番（パラメータが、範囲から探されている）と、まこさんの逐語「パラメータや指標は最初は戦略に沿って教科書通りの固定値でロジックを組んで、最後に範囲指定をしてチューニングする」のための直しです。
**①いま何が起きているか。**
- 材料の一覧（observe_diag.py の build_catalog）は、指標の期間を、ほかの指標の期間の一覧から借りて作っています。例＝CCI・AR・CMO ほか14種類は RSI の一覧（7・9・14・21）を、ADX・AROON・CHOP ほか14種類は ATR の一覧（7・14・21）を使っています。そのため、教科書の値（CCI の 20・AROON の 25 ほか）が一覧に在りません。
- 探す範囲（search_limits.json の material_param_ranges）は空で、範囲は一覧の数字の最小〜最大になっています。一覧に教科書の値が無いので、範囲も教科書の値に届かない指標が在ります。
- 範囲の置き場所の説明（5か所）に「ここに書くのは まこさんが決めた範囲だけ」「いまは空」と書いてあります。前の文は、私が 2026-08-13 に書いた文で、まこさんの発言ではありません（worklog 20261004 §10）。
**②この工事で何が変わるか。**
- P-1：観察の道具の設定に、指標ごとの一覧（80種）を道具が書きます。一覧＝修正対応表の最初の値（スキャル∪デイトレ・名前の軸に当たる軸）＋残す名前（V9 19本・採用中の戦略と確認のレシピ 9本）。材料の一覧を作る関数は、一覧に在る種類を、ほかの指標の期間の一覧を使わずに作ります。重複を外す一覧の「残す側」が一覧で外れた名前のときは、省く側も同じ値なので、一緒に外れたままにします。名前に出ない軸がある 38種の最初の値は、列の計算を変えずに別の欄（material_first_hidden）へ書きます。
- P-2：探す範囲の設定に、修正対応表の範囲（名前の軸・104種）を道具が書きます。一覧の値が範囲の外に出る軸は、範囲を広げて含めます（3-2 の2行目・1軸）。範囲の置き場所の説明5か所を、事実にそろえます。
- P-3：範囲の端の値で作った列が、まん中の値の列と同じにならないかを、写しで2種類の値動きの上で測りました。ライブラリが黙って既定に戻す端は0件でした。
- P-4：範囲が決まらない・範囲が1点のまま・資料に行が無い 33種を、値を埋めずに設定の注記（_material_params_pending）に並べます。
- P-5：29種のうち26種は、前の工事の名前に出さない引数で受け取れています。残り3種は直しません（3-1）。
- 番人：軽い口（--selftest-catalog）に3つ足します。⑪一覧の種類は、カタログの名前が一覧の組とちょうど同じ。⑫残す名前がカタログに在る。⑬設定の範囲が、一覧の組と残す名前の数字を全部 含む。
**③数字はどう変わるか。**材料の一覧は 576 列 → 476 列 です。両方に在る 423本の列は、決まった式で作った値動きの上で、値が直す前と同じでした。
```
消える名前（153本）＝ADX21・AROOND21・AROOND7・AROONOSC14・AROONOSC21・AROONOSC7・AROONU21・AROONU7・ATR%21・ATR%7・BB%b(50,2.0)・BB幅(50,2.0)・CCI14・CCI21・CCI7・CCI9・CHOP21・CHOP7・DI差21・DPO%48・Donchian幅%48・EFI比10・EFI比20・EOM比10・EOM比20・KAMA200傾き%・KAMA20傾き%・KAMA50傾き%・ROC3・ROC6・StochRSI%D21・StochRSI%D7・StochRSI%D9・StochRSI%K21・StochRSI%K7・StochRSI%K9・TRIX(14,9)・TRIX(21,9)・TRIX(7,9)・TRIX(9,9)・TRIXシグナル(14,9)・TRIXシグナル(21,9)・TRIXシグナル(7,9)・TRIXシグナル(9,9)・TRIXヒスト(14,9)・TRIXヒスト(21,9)・TRIXヒスト(7,9)・TRIXヒスト(9,9)・UI21・UI7・VTXM21・VTXM7・VTXP21・VTXP7・WMA200傾き%・WMA20傾き%・WMA50傾き%・close vs 24本安値%・close vs 24本高値%・close vs 48本安値%・close vs 48本高値%・close vs 96本安値%・close vs 96本高値%・close vs ALMA%20・close vs ALMA%200・close vs ALMA%50・close vs DEMA%200・close vs DEMA%50・close vs EMA200%・close vs EMA50%・close vs FWMA%20・close vs HMA%200・close vs HMA%50・close vs JMA%20・close vs JMA%200・close vs JMA%50・close vs KAMA%20・close vs KAMA%200・close vs KAMA%50・close vs LINREG%20・close vs LINREG%200・close vs LINREG%50・close vs LRb%20・close vs LRb%200・close vs LRb%50・close vs MCGD%20・close vs MCGD%200・close vs MCGD%50・close vs MEDIAN%20・close vs MEDIAN%200・close vs MEDIAN%50・close vs MIDPOINT%20・close vs MIDPOINT%200・close vs MIDPOINT%50・close vs MIDPRICE%20・close vs MIDPRICE%200・close vs MIDPRICE%50・close vs MMAR%15・close vs MMAR%25・close vs MMAR%30・close vs MMAR%35・close vs PWMA%20・close vs PWMA%200・close vs PWMA%50・close vs RAINBOW%(2,1)・close vs RAINBOW%(2,2)・close vs RAINBOW%(2,3)・close vs RAINBOW%(2,4)・close vs RAINBOW%(2,5)・close vs RAINBOW%(2,6)・close vs RAINBOW%(2,7)・close vs RAINBOW%(2,8)・close vs RAINBOW%(2,9)・close vs RMA%20・close vs RMA%200・close vs RMA%50・close vs SINWMA%20・close vs SINWMA%200・close vs SINWMA%50・close vs SMA20%・close vs SMA200%・close vs SMA50%・close vs SSF%20・close vs SSF%200・close vs SSF%50・close vs SWMA%20・close vs SWMA%200・close vs SWMA%50・close vs TEMA%200・close vs TEMA%50・close vs TRIMA%20・close vs TRIMA%50・close vs TSF%20・close vs TSF%200・close vs TSF%50・close vs VWMA%20・close vs VWMA%200・close vs VWMA%50・close vs WMA%20・close vs WMA%200・close vs WMA%50・fib位置96・fractal安値距離%(5)・fractal高値距離%(5)・安値からの経過バー24・安値からの経過バー48・安値からの経過バー96・安値切り上げ幅%(5)・構造破断距離%(5)・高値からの経過バー24・高値からの経過バー48・高値からの経過バー96・高値切り上げ幅%(5)
増える名前（53本）＝ADX10・AROOND25・AROONOSC25・AROONU25・CCI20・EFI比13・EOM比14・KAMA10傾き%・ROC9・RSI5・TRIX(15,9)・TRIXシグナル(15,9)・TRIXヒスト(15,9)・WMA30傾き%・close vs 20本安値%・close vs 20本高値%・close vs ALMA%10・close vs ALMA%9・close vs DEMA%10・close vs DEMA%30・close vs EMA5%・close vs FWMA%10・close vs HMA%10・close vs JMA%7・close vs KAMA%10・close vs KAMA%30・close vs LINREG%14・close vs LINREG%25・close vs LRb%14・close vs MCGD%10・close vs MEDIAN%30・close vs MIDPOINT%14・close vs MIDPOINT%2・close vs MIDPRICE%14・close vs MIDPRICE%2・close vs PWMA%10・close vs RMA%10・close vs RMA%14・close vs RMA%30・close vs SINWMA%14・close vs SMA9%・close vs SSF%10・close vs SWMA%10・close vs TEMA%10・close vs TRIMA%10・close vs TSF%14・close vs VWMA%10・close vs WMA%10・close vs WMA%9・fib位置14・stdev%10・安値からの経過バー25・高値からの経過バー25
```
**④残す名前（道具が実物から読んだ）。**
- V9 RCI（7・9・52）→ RCI7・RCI9・RCI52
- V9 ボリンジャーバンド（20本）→ BB%b(20,2.0)・BB幅(20,2.0)
- V9 ADX（14）→ ADX14
- V9 ATR（14の単純平均）→ ATR%14
- V9 EMA（20）→ EMA20傾き%・close vs EMA20%
- V9 RSI（21、傾きは3本差分）→ RSI21
- V9 MACD（12・26・9）→ MACD線%(12,26)・MACDシグナル線%(12,26,9)・MACDヒスト%(12,26,9)
- V9 ストキャスティクス（14、平滑3）→ Stoch%K14・Stoch%D14
- V9 location_prev（直近20本）→ fib位置20
- V9 entry_risk_score（20本の標準偏差 ÷ close）→ BB幅(20,2.0)
- まこさんの逐語の RSI → RSI7・RSI9・RSI14・RSI21
- 採用中の戦略・確認のレシピ ADX14 ← engine_tuner_exec.RUNTIME_ALIAS
- 採用中の戦略・確認のレシピ DI差7 ← engine_tuner_exec.RUNTIME_ALIAS
- 採用中の戦略・確認のレシピ Donchian幅%20 ← engine_tuner_exec.RUNTIME_ALIAS
- 採用中の戦略・確認のレシピ ROC24 ← engine_tuner_exec.RUNTIME_ALIAS・recipes/identity_s2_legacy.json
- 採用中の戦略・確認のレシピ S-Rタッチ数(144,0.006) ← recipes/r9_demand_fixture.json
- 採用中の戦略・確認のレシピ Stoch%D14 ← engine_tuner_exec.RUNTIME_ALIAS
- 採用中の戦略・確認のレシピ stdev%50 ← recipes/r9_demand_fixture.json
- 採用中の戦略・確認のレシピ volume_ratio20 ← engine_tuner_exec.RUNTIME_ALIAS・recipes/identity_s2_legacy.json
- 採用中の戦略・確認のレシピ volume_ratio50 ← engine_tuner_exec.RUNTIME_ALIAS
**⑤名前の軸と資料の軸の対応（18種・3-2 の1行目）。**計算式の引数の名前と、資料のパラメータの名前を並べて、私が決めました。
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
**⑥値を埋めずに並べる種類（P-4・33種）。**
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
| StochRSI%K | 範囲が1点のまま（全部の軸）：14・3・3 |
| StochRSI%D | 範囲が1点のまま（全部の軸）：14・3・3 |
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
| close vs MCGD% | 範囲が1点のまま（全部の軸）：10・1 |
| close vs SSF% | 範囲が1点のまま（全部の軸）：10・2 |
| close vs VIDYA% | 範囲が1点のまま（全部の軸）：14・9 |
| close vs ZLMA% | 最初の値も範囲も決まらない |
| close vs PMAX% | 最初の値も範囲も決まらない |
| close vs SAREXT% | 最初の値も範囲も決まらない |
| close vs ABER_ZG% | 範囲が1点のまま（全部の軸）：5・15 |
| ABER位置 | 範囲が1点のまま（全部の軸）：5・15 |
| HWC位置 | 範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0 |
**⑦範囲で見つかったこと。**
- 範囲を広げた軸＝ROC の軸1: 範囲 9〜14 の外に、一覧の値 [9.0, 12.0, 24.0] が在る → 9〜24 に広げる
- 軸の順が入れ替わる組＝MACD線%: 軸1 3〜12 と 軸2 10〜26 が重なる
- 軸の順が入れ替わる組＝MACDヒスト%: 軸1 3〜12 と 軸2 10〜26 が重なる
- 軸の順が入れ替わる組＝MACDシグナル線%: 軸1 3〜12 と 軸2 10〜26 が重なる
- P-3＝ライブラリが黙って既定に戻す端は 0件（範囲の端とまん中の値で列を作り、2種類の値動きで比べた）。
- P-3 の照らしで見つけた、列の計算に使われない軸（前から在る作り・3-1）＝S-Rタッチ1時間ATR の軸2（[0.5, 1.0, 1.5] のどれでも、2種類の値動きとも列が同じ）
- P-3 の照らしで見つけた、列の計算に使われない軸（前から在る作り・3-1）＝S-Rタッチ1時間ATR の軸3（[7, 14, 21] のどれでも、2種類の値動きとも列が同じ）
- P-3 の照らしで見つけた、列の計算に使われない軸（前から在る作り・3-1）＝PVO の軸3（[5, 7, 9] のどれでも、2種類の値動きとも列が同じ）
- P-3 の照らしで見つけた、列の計算に使われない軸（前から在る作り・3-1）＝TSI の軸3（[7, 10, 12] のどれでも、2種類の値動きとも列が同じ）
- 資料の「範囲が1点のまま24種」は、数え直すと23種（値の表 indicator_params_by_strategy.md の見出しの数と同じ）。資料に行が無い種類は、前期間pivot の3種に、1回目の工事で「使う」にした RCI を足した4種。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、当てる道具 apply_audit_fix.py・観察の道具の自己テスト・表を作る道具（G-1）・G2・H2 を動かします。
**誰が結果を使うか。**
- 材料の一覧は、engine_tuner が試す範囲（engine_tuner_gen.py の material_ranges）・表を作る道具・H2 が読みます。
- 探す範囲の設定は、engine_tuner_gen.py の material_ranges が読み、売買を回すプログラムの検証器（G6）と段の候補の絞りが使います。
- 成績表（material_ranking.json）は、この工事では作り直しません（3-1）。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**今の実物（observe_diag.py・observe_config.json・search_limits.json・engine_tuner_gen.py・engine_tuner_exec.py・gen_materials.py）・設計書の 4-20。
**書くもの。**
- 当てる（--design）：上の6つのファイルと、新しい壊すプログラム 3本。
- G-1：型の表・出口の型の表・組み立ての表・材料の文書・オン・オフの表。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 指標の名前に値を入れて、指標の数を増やさない | まこさん 2026-10-04「指標名に閾値やパラメータの値を固定で入れて、指標数を増やすという解決策はやめてほしい」 | 名前の形は変えません。一覧を教科書の最初の値にするので、材料は 576 列 → 476 列 に減ります |
| 最初は教科書の固定値で組み、最後に範囲でチューニングする | まこさん（req_scope_20261004） | 一覧＝教科書の最初の値。範囲＝修正対応表の範囲 |
| 数字を CC が作らない | 思考の順の7（req_thinking_20261004） | 一覧と範囲は道具が修正対応表から写しました。範囲を広げるのは、一覧の値を含めるためだけです |
| 探す値を、点の一覧で先に限定しない | 要件の作ってはいけないもの2番 | 一覧は最初に組む値で、探す値は範囲です |
| V9 の名前と RSI7・9・14・21 を変えない | まこさん（req_v9_indicators_on_20261004） | 残す名前に入れ、番人⑫で守ります |
| 未来のデータを使わない | 要件定義書 §4.6.H2 | 計算式は変えません。両方に在る列は値が同じです。当てた後に H2 を取り直します |
| 値段の高さで値が変わらない | 要件定義書 §4.6.H6 | 計算式は変えません |
| 乱数を使わない | 恒久67番 | 足すのは、一覧の読み方・番人・壊すプログラム・設定だけです |
| オフの指標を直さない | まこさん「オフは現状は対応しなくてよい」 | 一覧を書くのは、使う指標（修正対応表の行）だけです |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| observe_config.json の material_params・material_keep・material_first_hidden・_material_params_pending | 指標ごとの一覧・残す名前・名前に出ない軸の最初の値・値を埋めない種類を持つ（道具が写した） | 新設 |
| observe_diag.py の build_catalog | 一覧に在る種類を、その一覧の組だけで作る。一覧の種類が1度も出てこなければ止める。重複を外す一覧の残す側が一覧で外れた名前なら止めない | 直す |
| observe_diag.py の selftest_catalog（軽い口） | この工事の番人3つを足す | 直す |
| search_limits.json の material_param_ranges と注記 | 修正対応表の範囲（名前の軸）を持つ。注記を事実どおりにする | 直す |
| engine_tuner_gen.py の material_ranges の説明・engine_tuner_exec.py の説明・gen_materials.py の文 | 範囲の置き場所の説明を事実にそろえる（動きは変えない） | 直す |
| .claude/breaks の壊すプログラム | 番人ごとに、直しを壊すと決めた文で落ちるかを見る | 新設 |
- 触る関数は、全部の指示を当てる前と後の構文木を比べて、道具が数えました（下の囲み）。
```
observe_diag.py＝build_catalog・selftest_catalog／engine_tuner_gen.py＝material_ranges／engine_tuner_exec.py＝_check_param_range／gen_materials.py＝render_md
```

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. 承認の前の検査（A12）の穴2つは、まこさん「なおしてよい」で、この案の前に直しました（worklog 20261006 §20）。①仮当ての gen_materials.py の自己テストで、落ちたのが T6（表を作り直すまで鳴る）だけのときは止めない。②設計書の関数の一覧（SPEC）を、4-20 の指示を当てた後の中身から作る。
2. まこさんの承認の後、全部を当てます（apply_audit_fix.py --design --dry → --design）。当てる道具は、全件を当てる前の実物で照らしてから、番号の順に当てます。1件でも合わなければ1件も当てません。
3. 当てた直後に、当てる道具が G2 と H2 を自分で走らせます。この時点の G2 は、型の表を作り直す前なので、一致しない見込みです（材料の名前が変わるため。走らせて確かめてはいません。型の表を作り直す前に G2 を走らせる場面は、写しでは作れないためです）。G2 と H2 は、G-1 の後に取り直します。
4. 照合（verify_design_contract.py --diff）をかけます。設計書の関数の一覧は、当てた後の中身から作ったので、食い違わない見込みです（承認の前の検査の仮当てで、食い違い0件を確かめました）。食い違ったら、gen_acceptance.py --write で設計書を作り直し、私が全部 読んで見直してから、承認の打ち直しを1回 お願いします。
5. 軽い口と壊すプログラムを走らせ、全体の自己テスト（--selftest）を1回 走らせて、出力をそのまま貼ります。
6. G-1：表を作り直します。型の表と出口の型の表は、材料の名前が変わるので、まこさんに再承認していただきます。段の候補と出口の型の表の元データが名前で指す材料が、直した後のカタログに在るかを照らします。
7. G-2：範囲の中の値が全部 計算できるかの検査（gen_materials.py --selftest の param_range_both_ways）→ G2 → H2（約5分）の順に取り直します。そのあと、実装の監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝RSI。いま材料の一覧は、RSI の本数を設定 rsi_periods（7・9・14・21）から作り、同じ一覧を CCI・AR・CMO ほか14種類も使い回している（CCI は 7・9・14・21 で、教科書の 20 が無い）。この工事の後は、指標ごとの一覧が RSI＝5・7・9・14・21（スキャルの教科書 5・7、デイトレの教科書 14、V9 とまこさんの 7・9・14・21）、CCI＝20（教科書）になる。探す範囲は、RSI＝2〜21、CCI＝7〜21（修正対応表の範囲）。engine_tuner は、最初は一覧の値で組み、チューニングでは範囲の中のどの整数でも試せる。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**探す範囲を、修正対応表の範囲にします（104種）。**範囲を作る関数は、設定の範囲が在る種類はそれを使い、無い種類は今までどおり一覧の数字の最小〜最大を使います。名前に出さない引数の範囲は、この工事では書けません（工事2）。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**observe_config.json に足すもの。**material_params・_material_params・material_keep・_material_keep・material_first_hidden・_material_first_hidden・_material_params_pending。
**search_limits.json で変えるもの。**material_param_ranges（空 → 範囲）と、その注記。
コマンドの旗は増やしません。この工事の番人は、前の工事で作った軽い口（--selftest-catalog）に足します。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**
1. 軽い口が全部 通る。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog。全体の自己テストも通る。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest。
2. 壊すプログラムが、全部 決めた文で落ちる。コマンド＝python3 .claude/tools/run_breaks.py --design。
3. 材料の一覧が 576 列 → 476 列 になり、一覧の種類の名前が一覧の組とちょうど同じ（軽い口の番人が見る）。
4. 表を作り直した後に G2 が一致する。コマンド＝python3 scripts/priority_rebuild/gen_signal_families.py --verify。続けて H2 を取り直す。コマンド＝python3 scripts/priority_rebuild/leak_causality_diag.py。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| --design の --dry で、当たらない件が出る | 1件も当てずに止まります。まこさんに報告します |
| 材料の一覧を作る関数が、指標ごとの一覧を読まない | 材料の一覧を作る所が「[材料カタログ] 指標ごとの一覧 material_params の種類が、カタログを作る所で1度も出てこない」で止まります |
| 一覧の種類で、一覧に無い名前が作られる | 軽い口が「P-1:」で落ちます |
| 残す名前（V9・採用中の戦略・確認のレシピ）がカタログから消える | 軽い口が「P-1: 残す名前」で落ちます |
| 設定の範囲が、一覧の組か残す名前の数字を含まない | 軽い口が「P-2:」で落ちます |
| 範囲の設定に、カタログに無い種類か、軸の数が名前と違う種類が在る | 範囲を作る関数（material_ranges）が「[範囲エラー]」で止まります（前から在る止め） |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**カタログの1件の形（名前・計算・向き）は変えません。**設定に、指標ごとの一覧の欄（種類の名前 → 名前の軸の組の並び）を足します。

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
| 観察の道具の自己テスト（全体） | 121秒 | 写しで当てた後に走らせた実測（r3_draft_build.py の [7]） |
| 軽い口（--selftest-catalog） | 7秒 | 写しで当てた後に走らせた実測（r3_draft_build.py の [7]） |
| 材料の一覧 | 576 列 → 476 列 | 写しで数えた（r3_draft_build.py の [3]）。列が減るので、材料を作る時間と H2 の時間は短くなる見込み（測っていない） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**ありません。**全部を --design の1回で当てるので、途中の状態は残りません。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しの道具だけが書きます。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**軽い口の番人は、落ちたときだけ「P-1:」「P-1: 残す名前」「P-2:」で始まる行を出します。材料の一覧を作る所は、一覧の種類が1度も出てこないときに「[材料カタログ]」で止まります。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **observe_diag.py・observe_config.json・search_limits.json・engine_tuner_gen.py・engine_tuner_exec.py は H2 の対象です。**当てた後に G2 → H2 を取り直します。
2. **消える名前を文字のまま書いているファイルを、道具が数えました（r3_draft_build.py --refs）。**道具が作り直す表を除くと 18本で、中身は、重複を外す一覧の残す側（省く側も一緒に外れる）・自己テストの文（写しで自己テストが通った）・説明の文と記録（regime_kb_findings.json・m2_todo.json・gen_materials.py の例の文）でした。採用中の戦略と確認のレシピが使う名前は、残す名前に入れました。
3. **段の候補は、成績表の順位から作り、その列の数字が範囲の中かで絞ります（engine_tuner_gen.py の _group_usable_col）。**一覧から消えても範囲の中の数字の列（例＝2026-10-03 の段2a の1位 CHOP7・15分足。CHOP の範囲は 7〜21）は、候補に残る見込みです。範囲の外に出る数字の列（例＝ROC3・ROC6・96本高値・安値）は、候補から外れます（まこさん「今の値が新しい範囲の外に出る14行は、OK の文どおり外す」と同じ向き）。走らせて確かめてはいません。G-2 の後の段の本走で確かめます。
4. **成績表（material_ranking.json）は、この工事では作り直しません。**消える名前の行は引けなくなり、増える名前は行が無いので、成績表を作り直す（M2-D-8）まで、段の候補の順位に出ません（3-2 の5行目）。
5. **前からの壊すプログラムが探す文字の数は、当てる前と後で同じです。**道具が数えた相手は、下の囲みです。
```
b100_streak_tree_eval.sh・b103_geo_switch_unchecked.sh・b104_atr1h_own_tf.sh・b105_atr1h_future_hour.sh・b106_atr1h_no_clip.sh・b107_atr1h_base_not_passed.sh・b108_atr1h_base_wrong_bars.sh・b109_moving_line_not_built.sh・b110_ts_pos_in_random_draw.sh・b111_ts_pos_excludes_current.sh・b112_stage_warm_not_extended.sh・b122_obs_formula_copied.sh・b126_rank_resume_save_off.sh・b127_stage_q_rank_off.sh・b128_k1_copc_back_in_ao_loop.sh・b129_htf_bar_close_two_bars.sh・b131_industry_map_prev_pivot_gone.sh・b132_hidden_param_not_passed.sh・b133_cksp_mixed_set.sh・b134_ao_name_with_value.sh・b135_rci_mako_gone.sh・b136_insp2_bar_close_dropped.sh・b55_cyc_key_time_gone.sh・b56_one_min_csv_old.sh・b60_only5_with_others.sh・b61_insp5_bars_kind.sh・b63_tm_bitget_scope.sh・b64_tm_subdir.sh・b65_tm_badtail.sh・b77_no_streak.sh・b78_law_literal.sh・b79_param_drawn.sh・b80_quantile_one_by_one.sh・b82_abs_missing.sh・b83_bool_col_extra_key.sh・b84_qtable_per_bundle.sh・b85_band_ignores_laws.sh・b87_stages_record.sh・b91_keep_range_ignored.sh・b92_stage2_no_drop_tfs.sh・b94_stage_limits_ignored.sh・b96_tf_hardcoded.sh・b98_qkey_abs_missing.sh・b99_streak_inner_band_only.sh
```

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| r2_draft_build.py（前の工事の道具） | 今の実物と直しを全部 当てた後の中身を比べて指示を作る形・写しで確かめる形・壊し方を並べて走らせる形 |
| observe_diag.py の selftest_catalog（前の工事の軽い口） | 番人を足す場所と、落ちたときの行の形 |
| 壊すプログラム b131 | 壊すプログラムの形 |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=8f7df738daed987c gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1328行（add・P-1＝build_catalog が、指標ごとの一覧に在る種類を、その一覧の組だけで作る）
直す前の文字:
~~~
        C.append((name, fn, directional))


~~~
直した後の文字:
~~~
        C.append((name, fn, directional))

    # ★P-1（2026-10-06・工事 m2c15-param-values-20261006・まこさん決定「A」）＝指標ごとの一覧 material_params に在る種類は、
    #   ほかの指標の期間の一覧（rsi_periods・atr_periods・sma_periods など）を使わず、その一覧の組だけを、最初に出てきた場所で作る。
    #   一覧＝修正対応表の最初の値（スキャル∪デイトレ）＋残す名前（V9・採用中の戦略・確認のレシピ）。プログラムが書いた（CC は値を書いていない）。
    _per = cfg.get("material_params") or {}
    _per_done = set()


~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1328「C.append((name, fn, directional))」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1331行（addf・P-1＝build_catalog が、指標ごとの一覧に在る種類を、その一覧の組だけで作る）
直す前の文字:
~~~
        """材料の表から1組 作って足す（パラメータは引数で渡す）。"""

~~~
直した後の文字:
~~~
        """材料の表から1組 作って足す（パラメータは引数で渡す）。指標ごとの一覧に在る種類は、その一覧の組を作る。"""
        if family in _per:
            if family not in _per_done:
                _per_done.add(family)
                for _p in _per[family]:
                    C.append(make_material(family, *_p))
            return

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1331「"""材料の表から1組 作って足す（パラメータは引数で渡す）。"""」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1669行（build_catalog・P-1＝指標ごとの一覧の種類が、カタログを作る所で1度も出てこなければ止める）
直す前の文字:
~~~
    addf("HA下ヒゲ比")

~~~
直した後の文字:
~~~
    addf("HA下ヒゲ比")
    _unused = sorted(set(_per) - _per_done)
    if _unused:
        raise SystemExit(f"[材料カタログ] 指標ごとの一覧 material_params の種類が、カタログを作る所で1度も出てこない: {_unused}")

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1669「addf("HA下ヒゲ比")」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1676行（build_catalog・P-1＝重複を外す一覧の残す側が、指標ごとの一覧で外れた名前のときは止めない）
直す前の文字:
~~~
        bad = [f"{d}→{k}" for d, k in drop.items() if k not in have]

~~~
直した後の文字:
~~~
        # ★P-1（2026-10-06）＝残す側が、指標ごとの一覧で外した名前のときは止めない（省く側も同じ値の列なので、一緒に外れたままにする）。
        _gone = {k for k in drop.values() if k not in have and find_material(k)[0] in _per}
        bad = [f"{d}→{k}" for d, k in drop.items() if k not in have and k not in _gone]

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1676「bad = [f"{d}→{k}" for d, k in drop.items() if k not in have]」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7074行（selftest_catalog・軽い口 selftest_catalog に、この工事の番人（⑪ 一覧どおり・⑫ 残す名前・⑬ 範囲が含む）を足す）
直す前の文字:
~~~
            ng.append(f"検査2: {_fn10.__name__} が、上位足のずらし bar_close の形を確かめていない")

~~~
直した後の文字:
~~~
            ng.append(f"検査2: {_fn10.__name__} が、上位足のずらし bar_close の形を確かめていない")
    # ── 工事 m2c15-param-values-20261006 の番人（2026-10-06）──
    #  ⑪P-1＝指標ごとの一覧の種類は、カタログの名前がその一覧の組とちょうど同じ（ほかの指標の期間の一覧を使っていない）
    _per11 = cfg.get("material_params") or {}
    if not _per11:
        ng.append("P-1: 指標ごとの一覧 material_params が空")
    for _f11, _l11 in _per11.items():
        _want11 = {MATERIAL_FAMILIES[_f11][0].format(*_p11) for _p11 in _l11}
        _have11 = {_x11 for _x11 in sorted(_nm_k1) if find_material(_x11)[0] == _f11}
        if _want11 != _have11:
            ng.append(f"P-1: {_f11} のカタログの名前が、指標ごとの一覧と違う（多い {sorted(_have11 - _want11)[:4]}・無い {sorted(_want11 - _have11)[:4]}）")
    #  ⑫P-1＝残す名前（V9・採用中の戦略・確認のレシピ）がカタログに在る（まこさん決定「A」）
    if not cfg.get("material_keep"):
        ng.append("P-1: 残す名前 material_keep が空")
    for _g12, _l12 in (cfg.get("material_keep") or {}).items():
        _miss12 = [_x12 for _x12 in _l12 if _x12 not in _nm_k1]
        if _miss12:
            ng.append(f"P-1: 残す名前（{_g12}）がカタログに無い: {_miss12}")
    #  ⑬P-2＝設定の範囲は、指標ごとの一覧の組と残す名前の数字を、全部 含む（engine_tuner が V9 と採用中の戦略の値に届く）
    import json as _js13
    _rg13 = _js13.loads((pathlib.Path(__file__).resolve().parent / "recipes" / "search_limits.json").read_text(encoding="utf-8")).get("material_param_ranges") or {}
    if not _rg13:
        ng.append("P-2: 設定の範囲 material_param_ranges が空")
    _chk13 = {MATERIAL_FAMILIES[_f13][0].format(*_p13) for _f13, _l13 in _per11.items() for _p13 in _l13}
    _chk13 |= {_x13 for _l13 in (cfg.get("material_keep") or {}).values() for _x13 in _l13}
    for _x13 in sorted(_chk13):
        _e13, _p13 = iref.find(_x13)
        _ax13 = _rg13.get(_e13["family"]) if _e13 else None
        if not _ax13:
            continue
        for _i13, (_v13, _a13) in enumerate(zip(_p13, _ax13)):
            if not float(_a13["lo"]) <= float(_v13) <= float(_a13["hi"]):
                ng.append(f"P-2: {_x13} の {_i13 + 1} 番目の数字 {_v13} が、設定の範囲 {_a13['lo']}〜{_a13['hi']} の外")

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7074「ng.append(f"検査2: {_fn10.__name__} が、上位足のずらし bar_close の形を確かめていない")」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/observe_config.json
直す箇所: 164〜166行（設定・P-1・P-4＝指標ごとの一覧・残す名前・名前に出ない軸の最初の値・値を埋めない種類を、プログラムが修正対応表から写して書く）
直す前の文字:
~~~
  10,
  20
 ],

~~~
直した後の文字:
~~~
  10,
  20
 ],
 "material_params": {
  "ADX": [[7], [10], [14]],
  "DI差": [[7], [14]],
  "MACD線%": [[12, 26]],
  "MACDヒスト%": [[12, 26, 9]],
  "MACDシグナル線%": [[12, 26, 9]],
  "close vs 転換線%": [[9]],
  "close vs 基準線%": [[26]],
  "KSTシグナル": [[9]],
  "PPO": [[12, 26, 9]],
  "PPOシグナル": [[12, 26, 9]],
  "PPOヒスト": [[12, 26, 9]],
  "TRIX": [[15, 9]],
  "TRIXシグナル": [[15, 9]],
  "TRIXヒスト": [[15, 9]],
  "KAMA傾き": [[10]],
  "WMA傾き": [[30]],
  "AROONU": [[14], [25]],
  "AROOND": [[14], [25]],
  "AROONOSC": [[25]],
  "VTXP": [[14]],
  "VTXM": [[14]],
  "RSI": [[5], [7], [9], [14], [21]],
  "ROC": [[9], [12], [24]],
  "MFI": [[14]],
  "CMF": [[20]],
  "BB%b": [[20, 2.0]],
  "volume_ratio": [[20], [50]],
  "CCI": [[20]],
  "PVO": [[12, 26, 9]],
  "PVOシグナル": [[12, 26, 9]],
  "PVOヒスト": [[12, 26, 9]],
  "StochRSI%K": [[14]],
  "StochRSI%D": [[14]],
  "DPO%": [[20]],
  "EFI比": [[13]],
  "EOM比": [[14]],
  "ATR%": [[14]],
  "BB幅": [[20, 2.0]],
  "Donchian幅%": [[20]],
  "CHOP": [[14]],
  "stdev%": [[10], [50]],
  "UI": [[14]],
  "高値からの経過バー": [[25]],
  "安値からの経過バー": [[25]],
  "fractal高値距離%": [[2]],
  "fractal安値距離%": [[2]],
  "高値切り上げ幅%": [[2]],
  "安値切り上げ幅%": [[2]],
  "構造破断距離%": [[2]],
  "close vs EMA": [[5], [9], [20]],
  "close vs SMA": [[9]],
  "close vs Keltner上%": [[20, 2.0]],
  "close vs Keltner下%": [[20, 2.0]],
  "close vs 本高値%": [[20]],
  "close vs 本安値%": [[20]],
  "fib位置": [[14], [20]],
  "close vs ALMA%": [[9], [10]],
  "close vs DEMA%": [[10], [20], [30]],
  "close vs FWMA%": [[10]],
  "close vs HMA%": [[10], [20]],
  "close vs JMA%": [[7]],
  "close vs KAMA%": [[10], [30]],
  "close vs LINREG%": [[14], [25]],
  "close vs LRb%": [[14]],
  "close vs MCGD%": [[10]],
  "close vs MIDPOINT%": [[2], [14]],
  "close vs MIDPRICE%": [[2], [14]],
  "close vs MMAR%": [[10]],
  "close vs PWMA%": [[10]],
  "close vs RAINBOW%": [[2, 10]],
  "close vs RMA%": [[10], [14], [30]],
  "close vs SINWMA%": [[14]],
  "close vs SSF%": [[10]],
  "close vs SWMA%": [[10]],
  "close vs TEMA%": [[10], [20]],
  "close vs TRIMA%": [[10]],
  "close vs TSF%": [[14]],
  "close vs VWMA%": [[10]],
  "close vs WMA%": [[9], [10]],
  "close vs MEDIAN%": [[30]]
 },
 "_material_params": "★P-1（2026-10-06・工事 m2c15-param-values-20261006・まこさん決定「A」）＝指標ごとの一覧（名前に出る軸の組）。build_catalog は、ここに在る種類を、ほかの指標の期間の一覧（rsi_periods など）を使わずに、この組だけで作る。中身＝修正対応表の最初の値（スキャル∪デイトレ・名前の軸に当たる軸）＋残す名前（下の material_keep）。値はプログラム（.claude/state/indicator_review/r3_draft_build.py）が修正対応表から写した（CC は値を書いていない）。まこさんの逐語（req_scope_20261004）「パラメータや指標は最初は戦略に沿って教科書通りの固定値でロジックを組んで、最後に範囲指定をしてチューニングする」。範囲は recipes/search_limits.json の material_param_ranges。",
 "material_keep": {"V9": ["ADX14", "ATR%14", "BB%b(20,2.0)", "BB幅(20,2.0)", "EMA20傾き%", "MACDシグナル線%(12,26,9)", "MACDヒスト%(12,26,9)", "MACD線%(12,26)", "RCI52", "RCI7", "RCI9", "RSI14", "RSI21", "RSI7", "RSI9", "Stoch%D14", "Stoch%K14", "close vs EMA20%", "fib位置20"], "採用中の戦略と確認のレシピ": ["ADX14", "DI差7", "Donchian幅%20", "ROC24", "S-Rタッチ数(144,0.006)", "Stoch%D14", "stdev%50", "volume_ratio20", "volume_ratio50"]},
 "_material_keep": "残す名前（まこさん決定「A」2026-10-06）。V9＝v9_logic.md の §1.2 の表の設定の数字 × gen_signal_families.V9_FAMILY_MAP と、まこさんの逐語「RSI7・RSI9・RSI14・RSI21 は、初期の戦略で一つの指標として使用してるのでそのままで良い」。採用中の戦略と確認のレシピ＝engine_tuner_exec.RUNTIME_ALIAS と recipes/*.json の family・param。観察の道具の番人（selftest_catalog の⑫）がカタログに在ることを見る。",
 "material_first_hidden": {
  "転換線": {"スキャル": [[9, 26, 52]], "デイトレ": [[9, 26, 52]]},
  "基準線": {"スキャル": [[9, 26, 52]], "デイトレ": [[9, 26, 52]]},
  "AO%": {"スキャル": [[5, 34]], "デイトレ": [[5, 34]]},
  "KST": {"スキャル": [[10, 15, 20, 30, 10, 10, 10, 15, 9]], "デイトレ": [[10, 15, 20, 30, 10, 10, 10, 15, 9]]},
  "KSTシグナル": {"スキャル": [[10, 15, 20, 30, 10, 10, 10, 15, 9]], "デイトレ": [[10, 15, 20, 30, 10, 10, 10, 15, 9]]},
  "STC": {"スキャル": [[23, 50, 10]], "デイトレ": [[23, 50, 10]]},
  "STCstoch": {"スキャル": [[23, 50, 10]], "デイトレ": [[23, 50, 10]]},
  "KAMA傾き%": {"スキャル": [[10, 2, 30]], "デイトレ": [[10, 2, 30]]},
  "PSAR加速": {"スキャル": [[0.02, 0.2]], "デイトレ": [[0.02, 0.2]]},
  "StochRSI%K": {"スキャル": [], "デイトレ": [[14, 3, 3]]},
  "StochRSI%D": {"スキャル": [], "デイトレ": [[14, 3, 3]]},
  "UO": {"スキャル": [[7, 14, 28]], "デイトレ": [[7, 14, 28]]},
  "SQZ_ON": {"スキャル": [[20, 2, 20, 1.5]], "デイトレ": [[20, 2, 20, 1.5]]},
  "HWC幅%": {"スキャル": [[0.2, 0.1, 0.1, 0.1, 1]], "デイトレ": [[0.2, 0.1, 0.1, 0.1, 1]]},
  "MASSI": {"スキャル": [[9, 25]], "デイトレ": [[9, 25]]},
  "Keltner上": {"スキャル": [[20, 2.0, 10]], "デイトレ": [[20, 2.0, 10]]},
  "Keltner下": {"スキャル": [[20, 2.0, 10]], "デイトレ": [[20, 2.0, 10]]},
  "SMC_SWEEP": {"スキャル": [[15, 1.5]], "デイトレ": [[15, 1.5]]},
  "close vs ALMA%": {"スキャル": [[9, 0.85, 6], [10, 0.85, 6.0]], "デイトレ": [[9, 0.85, 6], [10, 0.85, 6.0]]},
  "close vs HILO%": {"スキャル": [[13, 21]], "デイトレ": [[13, 21]]},
  "close vs HWMA%": {"スキャル": [[0.2, 0.1, 0.1]], "デイトレ": [[0.2, 0.1, 0.1]]},
  "close vs JMA%": {"スキャル": [[7, 0]], "デイトレ": [[7, 0]]},
  "close vs KAMA%": {"スキャル": [[10, 2, 30], [30, 2, 30]], "デイトレ": [[10, 2, 30], [30, 2, 30]]},
  "close vs MAMA%": {"スキャル": [[0.5, 0.05]], "デイトレ": [[0.5, 0.05]]},
  "close vs FAMA%": {"スキャル": [[0.5, 0.05]], "デイトレ": [[0.5, 0.05]]},
  "close vs MCGD%": {"スキャル": [[10, 1]], "デイトレ": [[10, 1]]},
  "close vs SSF%": {"スキャル": [[10, 2]], "デイトレ": [[10, 2]]},
  "close vs CKSPl%": {"スキャル": [[10, 1, 9], [10, 3, 20]], "デイトレ": [[10, 1, 9], [10, 3, 20]]},
  "close vs CKSPs%": {"スキャル": [[10, 1, 9], [10, 3, 20]], "デイトレ": [[10, 1, 9], [10, 3, 20]]},
  "close vs PSAR%": {"スキャル": [[0.02, 0.02, 0.2]], "デイトレ": [[0.02, 0.02, 0.2]]},
  "PSAR反転": {"スキャル": [[0.02, 0.02, 0.2]], "デイトレ": [[0.02, 0.02, 0.2]]},
  "close vs ABER_ZG%": {"スキャル": [[5, 15]], "デイトレ": [[5, 15]]},
  "ABER位置": {"スキャル": [[5, 15]], "デイトレ": [[5, 15]]},
  "close vs ACCBL%": {"スキャル": [[20, 4]], "デイトレ": [[20, 4]]},
  "close vs ACCBU%": {"スキャル": [[20, 4]], "デイトレ": [[20, 4]]},
  "close vs CE_L%": {"スキャル": [[22, 3.0]], "デイトレ": [[22, 3.0]]},
  "close vs CE_S%": {"スキャル": [[22, 3.0]], "デイトレ": [[22, 3.0]]},
  "HWC位置": {"スキャル": [[0.2, 0.1, 0.1, 0.1, 1.0]], "デイトレ": [[0.2, 0.1, 0.1, 0.1, 1.0]]}
 },
 "_material_first_hidden": "名前に出ない軸がある種類の、修正対応表の最初の値（軸は資料の並びのまま）。列の計算には使わない（まこさん決定「A」＝列の計算を変えずに別の欄へ書く）。名前に出さない引数へ値を渡すのは工事2（M2-F-10b）。",
 "_material_params_pending": ["RCI＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "前期間pivotPP＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "前期間pivotR1＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "前期間pivotS1＝資料（修正対応表）に行が無い＝最初の値も範囲も無い", "KST＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "KSTシグナル＝範囲が1点のまま（全部の軸）：10・15・20・30・10・10・10・15・9", "PPO＝範囲が1点のまま（全部の軸）：12・26・9", "PPOシグナル＝範囲が1点のまま（全部の軸）：12・26・9", "PPOヒスト＝範囲が1点のまま（全部の軸）：12・26・9", "STCstoch＝範囲が1点のまま（全部の軸）：23・50・10", "StochRSI%K＝範囲が1点のまま（全部の軸）：14・3・3", "StochRSI%D＝範囲が1点のまま（全部の軸）：14・3・3", "HWC幅%＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1", "MASSI＝範囲が1点のまま（全部の軸）：9・25", "close vs VWAP＝範囲が1点のまま（全部の軸）：288", "pivotPP＝範囲が1点のまま（全部の軸）：288", "pivotR1＝範囲が1点のまま（全部の軸）：288", "pivotS1＝範囲が1点のまま（全部の軸）：288", "POC＝最初の値も範囲も決まらない", "VAH＝最初の値も範囲も決まらない", "VAL＝最初の値も範囲も決まらない", "SMC_SWEEP＝範囲が1点のまま（全部の軸）：15・1.5", "close vs MAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs FAMA%＝範囲が1点のまま（全部の軸）：0.5・0.05", "close vs MCGD%＝範囲が1点のまま（全部の軸）：10・1", "close vs SSF%＝範囲が1点のまま（全部の軸）：10・2", "close vs VIDYA%＝範囲が1点のまま（全部の軸）：14・9", "close vs ZLMA%＝最初の値も範囲も決まらない", "close vs PMAX%＝最初の値も範囲も決まらない", "close vs SAREXT%＝最初の値も範囲も決まらない", "close vs ABER_ZG%＝範囲が1点のまま（全部の軸）：5・15", "ABER位置＝範囲が1点のまま（全部の軸）：5・15", "HWC位置＝範囲が1点のまま（全部の軸）：0.2・0.1・0.1・0.1・1.0"],

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_config.json:164「10,」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: 44〜45行（設定・P-2＝修正対応表の範囲（名前の軸）を、プログラムが写して書く。注記を事実どおりに直す）
直す前の文字:
~~~
  "material_param_ranges": {},
  "_material_param_ranges_note": "指標のパラメータの範囲（段A の A-4・2026-08-13 新設）。★いまは空＝空のあいだは、材料カタログに在る数字の 最小〜最大 を範囲として使う（engine_tuner_gen.material_ranges が機械で作る＝CC は数字を作らない。例＝RSI は 7〜21 の整数）。★ここに書くのは まこさんが決めた範囲だけ。形＝{\"RSI\": [{\"kind\": \"int\", \"lo\": 30, \"hi\": 50}]}（軸＝名前の {} の数だけ並べる・kind は int か float・float は dec で小数の桁数）。出どころ＝まこさんの逐語 2026-08-07（engine_tuner_defects.md の D14 ⑥）「閾値は指標によって様々な値になるので、範囲で検索すると膨大な量になるはずなので、最初は疑似シミュである程度値を絞って、その後、engine_tunerで最適化する際は、疑似シミュで出た値の前後あたりで範囲を事前に指定して（例えば３０〜５０の間とか）探す、という使い方を想定している」。★ここに書いた範囲は 材料カタログの数字を含まなくてよい（狭めるのが目的）。範囲の外の数字は検証器（G6）が止める。",

~~~
直した後の文字:
~~~
  "material_param_ranges": {
    "ADX": [{"kind": "int", "lo": 7, "hi": 21}],
    "DI差": [{"kind": "int", "lo": 7, "hi": 21}],
    "MACD線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}],
    "MACDヒスト%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}],
    "MACDシグナル線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}],
    "転換線": [{"kind": "int", "lo": 5, "hi": 12}],
    "基準線": [{"kind": "int", "lo": 13, "hi": 26}],
    "EMA傾き": [{"kind": "int", "lo": 9, "hi": 200}],
    "KSTシグナル": [{"kind": "int", "lo": 9, "hi": 9}],
    "PPO": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}],
    "PPOシグナル": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}],
    "PPOヒスト": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}],
    "TRIX": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}],
    "TRIXシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}],
    "TRIXヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}],
    "TSI": [{"kind": "int", "lo": 7, "hi": 25}, {"kind": "int", "lo": 4, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}],
    "TSIシグナル": [{"kind": "int", "lo": 7, "hi": 25}, {"kind": "int", "lo": 4, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}],
    "TSIヒスト": [{"kind": "int", "lo": 7, "hi": 25}, {"kind": "int", "lo": 4, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}],
    "KAMA傾き%": [{"kind": "int", "lo": 7, "hi": 10}],
    "WMA傾き%": [{"kind": "int", "lo": 20, "hi": 200}],
    "AROONU": [{"kind": "int", "lo": 7, "hi": 288}],
    "AROOND": [{"kind": "int", "lo": 7, "hi": 25}],
    "AROONOSC": [{"kind": "int", "lo": 7, "hi": 25}],
    "VTXP": [{"kind": "int", "lo": 14, "hi": 30}],
    "VTXM": [{"kind": "int", "lo": 14, "hi": 30}],
    "RSI": [{"kind": "int", "lo": 2, "hi": 21}],
    "ROC": [{"kind": "int", "lo": 9, "hi": 24}],
    "Stoch%K": [{"kind": "int", "lo": 5, "hi": 21}],
    "Stoch%D": [{"kind": "int", "lo": 5, "hi": 21}],
    "MFI": [{"kind": "int", "lo": 10, "hi": 20}],
    "CMF": [{"kind": "int", "lo": 20, "hi": 36}],
    "OBV傾き": [{"kind": "int", "lo": 10, "hi": 20}],
    "BB%b": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}],
    "volume_ratio": [{"kind": "int", "lo": 20, "hi": 50}],
    "CCI": [{"kind": "int", "lo": 7, "hi": 21}],
    "PVO": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}],
    "PVOシグナル": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}],
    "PVOヒスト": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}],
    "StochRSI%K": [{"kind": "int", "lo": 14, "hi": 14}],
    "StochRSI%D": [{"kind": "int", "lo": 14, "hi": 14}],
    "DPO%": [{"kind": "int", "lo": 14, "hi": 40}],
    "EFI比": [{"kind": "int", "lo": 10, "hi": 20}],
    "EOM比": [{"kind": "int", "lo": 10, "hi": 20}],
    "NVI傾き": [{"kind": "int", "lo": 10, "hi": 20}],
    "PVT傾き": [{"kind": "int", "lo": 10, "hi": 20}],
    "ATR%": [{"kind": "int", "lo": 5, "hi": 21}],
    "BB幅": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}],
    "realized_vol": [{"kind": "int", "lo": 10, "hi": 50}],
    "Donchian幅": [{"kind": "int", "lo": 10, "hi": 20}],
    "MMI": [{"kind": "int", "lo": 200, "hi": 500}],
    "ER": [{"kind": "int", "lo": 7, "hi": 21}],
    "CHOP": [{"kind": "int", "lo": 7, "hi": 21}],
    "VHF": [{"kind": "int", "lo": 7, "hi": 28}],
    "MAD比": [{"kind": "int", "lo": 20, "hi": 50}],
    "stdev%": [{"kind": "int", "lo": 10, "hi": 50}],
    "UI": [{"kind": "int", "lo": 7, "hi": 21}],
    "高値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}],
    "安値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}],
    "形スコア": [{"kind": "int", "lo": 24, "hi": 96}],
    "W字": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.003, "hi": 0.003, "dec": 3}],
    "fractal高値距離%": [{"kind": "int", "lo": 2, "hi": 3}],
    "fractal安値距離%": [{"kind": "int", "lo": 2, "hi": 3}],
    "高値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}],
    "安値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}],
    "構造破断距離%": [{"kind": "int", "lo": 2, "hi": 3}],
    "close vs EMA": [{"kind": "int", "lo": 5, "hi": 60}],
    "close vs SMA": [{"kind": "int", "lo": 5, "hi": 60}],
    "close vs VWAP": [{"kind": "int", "lo": 288, "hi": 288}],
    "Keltner上": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}],
    "Keltner下": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}],
    "n本高値": [{"kind": "int", "lo": 10, "hi": 50}],
    "n本安値": [{"kind": "int", "lo": 10, "hi": 50}],
    "pivotPP": [{"kind": "int", "lo": 288, "hi": 288}],
    "pivotR1": [{"kind": "int", "lo": 288, "hi": 288}],
    "pivotS1": [{"kind": "int", "lo": 288, "hi": 288}],
    "fib位置": [{"kind": "int", "lo": 14, "hi": 96}],
    "S-Rタッチ1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}],
    "S-Rタッチ数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}],
    "close vs ALMA%": [{"kind": "int", "lo": 9, "hi": 18}],
    "close vs DEMA%": [{"kind": "int", "lo": 9, "hi": 200}],
    "close vs FWMA%": [{"kind": "int", "lo": 10, "hi": 20}],
    "close vs HMA%": [{"kind": "int", "lo": 1, "hi": 200}],
    "close vs JMA%": [{"kind": "int", "lo": 3, "hi": 80}],
    "close vs KAMA%": [{"kind": "int", "lo": 7, "hi": 30}],
    "close vs LINREG%": [{"kind": "int", "lo": 14, "hi": 200}],
    "close vs LRb%": [{"kind": "int", "lo": 14, "hi": 200}],
    "close vs MCGD%": [{"kind": "int", "lo": 10, "hi": 10}],
    "close vs MIDPOINT%": [{"kind": "int", "lo": 2, "hi": 200}],
    "close vs MIDPRICE%": [{"kind": "int", "lo": 2, "hi": 200}],
    "close vs MMAR%": [{"kind": "int", "lo": 10, "hi": 35}],
    "close vs PWMA%": [{"kind": "int", "lo": 10, "hi": 200}],
    "close vs RAINBOW%": [{"kind": "int", "lo": 2, "hi": 2}, {"kind": "int", "lo": 1, "hi": 10}],
    "close vs RMA%": [{"kind": "int", "lo": 10, "hi": 200}],
    "close vs SINWMA%": [{"kind": "int", "lo": 14, "hi": 200}],
    "close vs SSF%": [{"kind": "int", "lo": 10, "hi": 10}],
    "close vs SWMA%": [{"kind": "int", "lo": 4, "hi": 200}],
    "close vs T3%": [{"kind": "int", "lo": 8, "hi": 34}],
    "close vs TEMA%": [{"kind": "int", "lo": 1, "hi": 200}],
    "close vs TRIMA%": [{"kind": "int", "lo": 1, "hi": 200}],
    "close vs TSF%": [{"kind": "int", "lo": 4, "hi": 200}],
    "close vs VIDYA%": [{"kind": "int", "lo": 14, "hi": 14}],
    "close vs VWMA%": [{"kind": "int", "lo": 1, "hi": 200}],
    "close vs WMA%": [{"kind": "int", "lo": 1, "hi": 200}],
    "close vs MEDIAN%": [{"kind": "int", "lo": 4, "hi": 200}]
  },
  "_material_param_ranges_note": "指標のパラメータの範囲（段A の A-4・2026-08-13 新設）。★2026-10-06（工事 m2c15-param-values-20261006・全体の表の P-2）から、修正対応表（.claude/state/indicator_fix_plan.json・その元の indicator_params_by_strategy.json）の範囲を、プログラムが写して書く（CC は数字を書いていない）。範囲の選び方＝まこさんが OK した選び方（okd_param_rule_20261004 の2＝教科書に範囲が書いてあればそれ、無ければ見つかった値と今の値の最小〜最大）。名前の軸に当たる軸だけを書く（名前に出さない引数の範囲は工事2）。★指標ごとの一覧（observe_config.json の material_params・残す名前を含む）の値が範囲の外なら、範囲を広げて含める（まこさん決定 2026-10-04 の①＝教科書の範囲と最初の値がぶつかる軸は範囲を広げて含める、と同じ型）。★ここに書いていない種類は、材料カタログの数字の 最小〜最大 を範囲として使う（engine_tuner_gen.material_ranges）。★直す前のこの注記に在った「ここに書くのは まこさんが決めた範囲だけ」は、CC が 2026-08-13 に書いた文で、まこさんの発言ではない（worklog 20261004 §10）。形＝{\"RSI\": [{\"kind\": \"int\", \"lo\": 2, \"hi\": 21}]}（軸＝名前の {} の数だけ並べる・kind は int か float・float は dec で小数の桁数）。使い方の出どころ＝まこさんの逐語 2026-08-07（engine_tuner_defects.md の D14 ⑥）「閾値は指標によって様々な値になるので、範囲で検索すると膨大な量になるはずなので、最初は疑似シミュである程度値を絞って、その後、engine_tunerで最適化する際は、疑似シミュで出た値の前後あたりで範囲を事前に指定して（例えば３０〜５０の間とか）探す、という使い方を想定している」。★ここに書いた範囲は 材料カタログの数字を含まなくてよい（狭めるのが目的）。範囲の外の数字は検証器（G6）が止める。",

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:44「"material_param_ranges": {},」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 242行（material_ranges・P-2＝範囲の置き場所の説明を、事実（修正対応表の範囲をプログラムが写した）にそろえる）
直す前の文字:
~~~
      決まったら、下の「まこさんが決めた範囲」に書けば、そちらが優先されます（CC は書きません）。

~~~
直した後の文字:
~~~
      ★2026-10-06（工事 m2c15-param-values-20261006）から、下の設定の範囲に、修正対応表の範囲（まこさんが OK した選び方で
      出たもの）をプログラムが写して書いています。設定の範囲が在る種類は、そちらが優先されます（CC は数字を書いていない）。

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:242「決まったら、下の「まこさんが決めた範囲」に書けば、そちらが優先されます（CC は書きません）。」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 244行（material_ranges・P-2＝範囲の置き場所の説明を、事実（修正対応表の範囲をプログラムが写した）にそろえる）
直す前の文字:
~~~
    ★まこさんが決めた範囲の置き場所＝recipes/search_limits.json の material_param_ranges。

~~~
直した後の文字:
~~~
    ★設定の範囲の置き場所＝recipes/search_limits.json の material_param_ranges。

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:244「★まこさんが決めた範囲の置き場所＝recipes/search_limits.json の material_param_ranges。」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 248行（material_ranges・P-2＝範囲の置き場所の説明を、事実（修正対応表の範囲をプログラムが写した）にそろえる）
直す前の文字:
~~~
      **いまは空です。**空のあいだは、上のカタログ由来の範囲を使います。

~~~
直した後の文字:
~~~
      設定に無い種類は、上のカタログ由来の範囲を使います。名前に出さない引数の範囲は、ここには書けません（工事2）。

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:248「**いまは空です。**空のあいだは、上のカタログ由来の範囲を使います。」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 254〜255行（material_ranges・P-2＝範囲の置き場所の説明を、事実（修正対応表の範囲をプログラムが写した）にそろえる）
直す前の文字:
~~~
      いまはカタログ由来＝どの軸も1点なので問題は出ません。まこさんが範囲を広げるときに、
      その決まりが要るかを1件ずつ決めます。

~~~
直した後の文字:
~~~
      ★2026-10-06 から設定の範囲を書いたので、軸どうしの範囲が重なる種類が在る（工事 m2c15-param-values-20261006 の
      設計書に一覧）。その決まりが要るかを1件ずつ決めます。

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:254「いまはカタログ由来＝どの軸も1点なので問題は出ません。まこさんが範囲を広げるときに、」
状態: 確定

#### 実装 12
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 293行（material_ranges・P-2＝範囲の置き場所の説明を、事実（修正対応表の範囲をプログラムが写した）にそろえる）
直す前の文字:
~~~
    # ── まこさんが決めた範囲が在れば、そちらを使う（CC は数字を書かない）──

~~~
直した後の文字:
~~~
    # ── 設定の範囲（material_param_ranges）が在れば、そちらを使う（CC は数字を書かない）──

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:293「# ── まこさんが決めた範囲が在れば、そちらを使う（CC は数字を書かない）──」
状態: 確定

#### 実装 13
対象のファイル: scripts/priority_rebuild/engine_tuner_exec.py
直す箇所: 736行（_check_param_range・P-2＝範囲の正本の説明を、事実にそろえる）
直す前の文字:
~~~
    範囲の正本＝`engine_tuner_gen.material_ranges`（材料カタログ由来の範囲＋まこさんが決めた範囲）。

~~~
直した後の文字:
~~~
    範囲の正本＝`engine_tuner_gen.material_ranges`（材料カタログ由来の範囲＋設定 material_param_ranges の範囲）。

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_exec.py:736「範囲の正本＝`engine_tuner_gen.material_ranges`（材料カタログ由来の範囲＋まこさんが決めた範囲）。」
状態: 確定

#### 実装 14
対象のファイル: scripts/priority_rebuild/gen_materials.py
直す箇所: 1583行（render_md・P-2＝材料の文書（materials.md）に書く範囲の置き場所の文を、事実にそろえる）
直す前の文字:
~~~
              "**まこさんが範囲を決めたときの置き場所＝`recipes/search_limits.json` の `material_param_ranges`（いまは空）。**",

~~~
直した後の文字:
~~~
              "**設定の範囲の置き場所＝`recipes/search_limits.json` の `material_param_ranges`（2026-10-06 から、修正対応表の範囲をプログラムが写したもの）。**",

~~~
根拠の抜き書き: scripts/priority_rebuild/gen_materials.py:1583「"**まこさんが範囲を決めたときの置き場所＝`recipes/search_limits.json` の `material_param_ranges`（いまは空）。**",」
状態: 確定

#### 実装 15
対象のファイル: .claude/breaks/b137_material_params_ignored.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: build_catalog が指標ごとの一覧を読まず、ほかの指標の期間の一覧で作ると、カタログを作る所が止まる（軽い口が落ちる）
# EXPECT_MSG: [材料カタログ] 指標ごとの一覧 material_params の種類が、カタログを作る所で1度も出てこない
# b137_material_params_ignored — build_catalog が指標ごとの一覧を読まず、ほかの指標の期間の一覧で作ると、カタログを作る所が止まる（軽い口が落ちる）（工事 m2c15-param-values-20261006・2026-10-06）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r3_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「[材料カタログ] 指標ごとの一覧 material_params の種類が、カタログを作る所で1度も出てこない」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        if family in _per:\n'
new = '        if False and family in _per:\n'
if s.count(old) != 1:
    raise SystemExit("[b137_material_params_ignored] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b131_industry_map_prev_pivot_gone.sh:1「#!/bin/bash」
状態: 確定

#### 実装 16
対象のファイル: .claude/breaks/b138_keep_name_dropped.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 指標ごとの一覧から、採用中の戦略が使う ROC24 を外すと、残す名前の番人（⑫）が落ちる
# EXPECT_MSG: ❌ P-1: 残す名前
# b138_keep_name_dropped — 指標ごとの一覧から、採用中の戦略が使う ROC24 を外すと、残す名前の番人（⑫）が落ちる（工事 m2c15-param-values-20261006・2026-10-06）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）
#   壊し方＝scripts/priority_rebuild/observe_config.json の中の、下の old を new に置き換える（r3_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ P-1: 残す名前」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_config.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '  "ROC": [[9], [12], [24]],\n'
new = '  "ROC": [[9], [12]],\n'
if s.count(old) != 1:
    raise SystemExit("[b138_keep_name_dropped] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b131_industry_map_prev_pivot_gone.sh:1「#!/bin/bash」
状態: 確定

#### 実装 17
対象のファイル: .claude/breaks/b139_range_excludes_keep.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 設定の範囲を、残す名前 ROC24 を含まない形（上限 14）に戻すと、範囲の番人（⑬）が落ちる
# EXPECT_MSG: ❌ P-2:
# b139_range_excludes_keep — 設定の範囲を、残す名前 ROC24 を含まない形（上限 14）に戻すと、範囲の番人（⑬）が落ちる（工事 m2c15-param-values-20261006・2026-10-06）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）
#   壊し方＝scripts/priority_rebuild/recipes/search_limits.json の中の、下の old を new に置き換える（r3_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ P-2:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/recipes/search_limits.json"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    "ROC": [{"kind": "int", "lo": 9, "hi": 24}],\n'
new = '    "ROC": [{"kind": "int", "lo": 9, "hi": 14}],\n'
if s.count(old) != 1:
    raise SystemExit("[b139_range_excludes_keep] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b131_industry_map_prev_pivot_gone.sh:1「#!/bin/bash」
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 17 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 名前の一覧を、教科書の最初の値（スキャル∪デイトレ）＋残す名前にする | まこさん決定「A」 | 今の名前を全部 残して足す（B）・名前は変えず別の欄に書くだけ（C） |
| 2 | 一覧に在る種類だけ、ほかの指標の期間の一覧を使わない形にする（build_catalog の addf の入口で切り替える） | 一覧を読む所が1か所で済み、今の作りの並び（カタログの順）を変えない | 指標ごとに for を書き直す（行が多く、直し漏れが出る） |
| 3 | 残す名前は、V9 の §1.2 の表・まこさんの RSI の逐語・実行時の別名・確認のレシピから、道具が読む | 手で名前を並べると漏れる（例＝V9 の location_prev は fib位置20 に当たる＝道具が型の表の道具の対応表から読んで見つけた） | 私が名前を手で並べる |
| 4 | 重複を外す一覧の残す側が一覧で外れた名前のときは、止めずに省く側も外れたままにする | 省く側は残す側と同じ値の列。残す側を消したのに省く側を残すと、同じ列が別の名前で戻る | 止めたまま／省く側を残す |
| 5 | 範囲は、名前の軸だけを書く | 範囲を作る関数は、軸の数が名前と違えば止める（前から在る止め） | 名前に出ない軸も書く（関数が止まる） |
| 6 | 一覧の値が範囲の外に出る軸は、範囲を広げて含める | まこさん決定 2026-10-04 の①と同じ型。広げないと、engine_tuner が残す名前の値に届かない | 範囲の外のままにする |
| 7 | 番人は、前の工事の軽い口に足す | 新しい旗を増やさずに済む。完成の条件と壊すプログラムが、数秒で測れる | 新しい旗を作る |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=1a806d06bb08e2b0 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b137_material_params_ignored.sh` | #1 | 一覧の種類を、ほかの指標の期間の一覧で作る形に戻す |
| `b138_keep_name_dropped.sh` | #2 | 指標ごとの一覧から、採用中の戦略が使う ROC24 を外す |
| `b139_range_excludes_keep.sh` | #3 | ROC の範囲の上限を、残す名前 ROC24 を含まない 14 に戻す |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 名前に出ない軸（KST の本数・HWMA の係数・PSAR と CKSP の値・傾きの比べる本数 k ほか）は、この工事の後も範囲から探されない | 工事2 で、探す側が範囲から渡す仕組みを作る（3-1） |
| 2 | MACD の3種は、範囲の中に短い方が長い方以上になる組が在る | 工事2 で「短い方 < 長い方」の決まりを探す側に入れる（3-2 の3行目） |
| 3 | 名前の軸の対応（18種）は私が決めた | 根拠の表を設計書に載せ、監査で確かめていただく（3-2 の1行目） |
| 4 | 成績表は古い名前のまま | 成績表の作り直し（M2-D-8）で直る（3-2 の5行目） |
| 5 | 段の候補で、範囲の外に出る数字の列が外れる | まこさんの決定（範囲の外の行は外す）と同じ向き。G-2 の後の段の本走で確かめる（4-13 の3） |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（--design） | 1分未満 | 前の工事で、当てる道具は1秒未満で終わった |
| 全体の自己テスト | 121秒 | 4-14 |
| 軽い口と壊すプログラム | 軽い口1回 7秒 | 写しで壊し方を並べて走らせた（r3_draft_build.py の [8]） |
| G-1 の表の作り直し | 約1分 | 前の工事の実測（表を作る道具の合計） |
| G2 → H2 | 約30秒 → 約5分 | 前の工事の実測 |
| まこさんの承認 | 設計書は1回の見込み（関数の一覧を当てた後の中身から作るので、当てた後に作り直さない）。型の表と出口の型の表は再承認が1回 | 4-4 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝①材料の一覧の作りが、指標ごとの期間の一覧を持たず、ほかの指標の一覧を借りる形だった（段A の A-6 で直書きを設定へ出したときも、借りる形のまま残った）。②範囲の置き場所が空で、その説明に「まこさんが決めた範囲だけ」という、まこさんの発言でない文が在った。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。材料の一覧と探す範囲が、教科書の値に届く形になります。

**③ root か symptom か**＝root です。一覧の読み方そのものを指標ごとにし、範囲を設定に書き、番人で一覧どおりかを確かめます。

**④ ベースアップ**＝154回目に調べた資料（indicator_params_by_strategy・indicator_params_review・修正対応表）・ライブラリの実物（thermo.py・kst.py）・監査 CP60 の修正64。新しい Web の調べはしていません。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。一覧と範囲は、修正対応表（調べた資料から道具が写した表）から道具が写しました。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝材料の名前の一覧を教科書の最初の値にし、探す範囲を設定に書く。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。条件をつなぐものではなく、材料の一覧と範囲の直しです |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 一覧は最初に組む値で、探す値は範囲です。範囲の数字は修正対応表から道具が写しました |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **この工事で、全部のパラメータが範囲から探せるようになるか** | なりません。名前に出ない軸は工事2 です（6-2 の1行目） |
| **番人は、範囲の数字が修正対応表と同じかを見るか** | 見ません。範囲が一覧と残す名前を含むかだけを見ます（写しの道具が、当てる前に修正対応表と照らしました） |
| **範囲の中の値が教科書どおりの列かを確かめるか** | 確かめません。参照表は、名前の数字で計算した列だけを照らします |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=b07fb684be548e4e gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝observe_diag.py・observe_config.json・search_limits.json・engine_tuner_gen.py・engine_tuner_exec.py・gen_materials.py と、新しい壊すプログラムを【7-8】に書いた。主なファイルは observe_diag.py。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝observe_diag.py）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム（NEW_FILE）。手本は b131（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝151回目は名前に値を足す直しで指標を増やした。153回目は資料に無い所を私が埋めて改ざんした。この工事は、名前の形を変えず、一覧と範囲を修正対応表から道具が写し、私が決めた所（名前の軸の対応・範囲を広げる軸）を 3-2 に全部 出した。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | この工事は、新しい部品も前処理も足さない。計算式は変えず、両方に在る列は値が同じ。当てた後に H2 を取り直す。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | engine_tuner_gen.py と engine_tuner_exec.py は説明の文だけを直すので、その行番号を指す文書は動かない（関数の中の行は増えない）。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、探す文字の数が当てる前と後で同じことを道具が数えた（4-13 の5）。走らせるコマンドの旗は変えない。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムが測るのは observe_diag.py --selftest-catalog で、軽い口は決まった式で作った値動きと設定だけを使い、ファイルに書かない。本物の結果の置き場には書かない。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 新しく足す関数は無い。触る関数は全部 DESIGN_CONTRACT の impl_functions に書いた（道具が当てる前と後の構文木で数えた）。must_use の名前は、当てた後の関数の中に在ることを道具が ast で照らした。observe_diag.py の触る関数＝build_catalog・selftest_catalog。engine_tuner_gen.py の触る関数＝material_ranges。engine_tuner_exec.py の触る関数＝_check_param_range。gen_materials.py の触る関数＝render_md。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足すコマンドの旗は無い。番人は、完成の条件が走らせる軽い口（--selftest-catalog）の中で全部 通る。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2c15-param-values-20261006）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝軽い口の番人（⑪〜⑬と、前の工事の番人）と、壊すプログラム（わざと壊して落ちるか）。写しで走らせ、全部 通った。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | P-1＝材料の一覧を作る関数が、指標ごとの一覧を読む | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | 一覧の種類を、ほかの指標の期間の一覧で作る形に戻す | `b137_material_params_ignored.sh` | — | **未着手** |
| 2 | P-1＝残す名前（V9・採用中の戦略・確認のレシピ）がカタログに在る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | 指標ごとの一覧から、採用中の戦略が使う ROC24 を外す | `b138_keep_name_dropped.sh` | — | **未着手** |
| 3 | P-2＝設定の範囲が、一覧の組と残す名前の数字を全部 含む | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | ROC の範囲の上限を、残す名前 ROC24 を含まない 14 に戻す | `b139_range_excludes_keep.sh` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=0ff82e5f99a9cb95 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/observe_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `build_catalog` | 1319 |
| `selftest_catalog` | 6994 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 180件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=cdb082738037dad4 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/observe_diag.py",
  "_impl_file の意味": "照らす相手は実在するファイル。材料の一覧（build_catalog）と軽い口の番人（selftest_catalog）が在る、観察の道具を照らす。",
  "impl_functions": {
    "scripts/priority_rebuild/observe_diag.py": [
      "build_catalog",
      "selftest_catalog"
    ],
    "scripts/priority_rebuild/engine_tuner_gen.py": [
      "material_ranges"
    ],
    "scripts/priority_rebuild/engine_tuner_exec.py": [
      "_check_param_range"
    ],
    "scripts/priority_rebuild/gen_materials.py": [
      "render_md"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数（実装の指示を全部 当てる前と後の構文木を関数ごとに比べて、r3_proposal_build.py が数えた）。",
  "self_check_calls": [
    "build_catalog",
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
  "_must_use の意味": "軽い口が、この工事の番人で呼ぶ関数（r3_proposal_build.py が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は、材料の一覧の読み方と設定を直すだけ。外から読む一覧の形（カタログの1件の形・参照表の欄）は変えない。",
  "generated_from": {
    "impl_functions": "当てる前と後の関数ごとの構文木の差（r3_proposal_build.py が数えた）",
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

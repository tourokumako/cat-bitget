<!-- ARC iter="m2f-label-structure-20261001" -->

# 設計書｜答え合わせに使う札を作る部品 regime_label.py と設定 recipes/regime_label.json を新しく作り、H2 の印の対象に足す＝14a の工事 A

TARGET: scripts/priority_rebuild/leak_causality_diag.py, scripts/priority_rebuild/regime_label.py, scripts/priority_rebuild/recipes/regime_label.json
NEW_FILE: scripts/priority_rebuild/regime_label.py, scripts/priority_rebuild/recipes/regime_label.json, .claude/breaks/b118_band_continue_off.sh
MODEL: scripts/priority_rebuild/observe_diag.py, .claude/breaks/b113_catch_share_broken.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2f-label-structure-20261001/ok_labelA_20261002`・`m2f-label-structure-20261001/ok_split_20261002`・`m2f-label-structure-20261001/ok_t6_20261002`・`m2f-label-structure-20261001/ok_todo_20261001`・`m2f-label-structure-20261001/okd_labelA_20261002`・`m2f-label-structure-20261001/req_6d_20260928`・`m2f-label-structure-20261001/req_split_20261001`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2f-label-structure-20261001/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2f-label-structure-20261001 --write`。検出＝`--work m2f-label-structure-20261001 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=73ba1ada3f0e2afd gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2f-label-structure-20261001/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2f-label-structure-20261001/ok_labelA_20261002.txt`（まこさんの発言）・`verbatim/m2f-label-structure-20261001/ok_split_20261002.txt`（まこさんの発言）・`verbatim/m2f-label-structure-20261001/ok_t6_20261002.txt`（まこさんの発言）・`verbatim/m2f-label-structure-20261001/ok_todo_20261001.txt`（まこさんの発言）・`verbatim/m2f-label-structure-20261001/okd_labelA_20261002.txt`（まこさんが OK した CC の文）・`verbatim/m2f-label-structure-20261001/req_6d_20260928.txt`（まこさんの発言）・`verbatim/m2f-label-structure-20261001/req_split_20261001.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝358 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_labelA_20261002` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_split_20261002` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_t6_20261002` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_todo_20261001` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_labelA_20261002` | V01〜V02（2 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_labelA_20261002` | V03〜V07（5 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V08〜V10（3 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V11〜V14（4 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V15〜V23（9 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V24〜V29（6 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V30〜V37（8 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V38〜V49（12 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V50〜V59（10 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V60〜V62（3 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V63〜V66（4 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V67〜V68（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V69〜V71（3 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V72〜V73（2 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V74〜V78（5 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V79〜V84（6 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V85〜V86（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V87〜V88（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V89〜V90（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V91〜V97（7 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V98〜V142（45 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V143〜V153（11 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V154〜V160（7 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V161〜V166（6 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V167〜V173（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V174〜V175（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V176〜V177（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V178〜V182（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V183〜V194（12 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V195〜V215（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V216〜V221（6 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V222〜V301（80 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_labelA_20261002` | V302〜V306（5 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `req_6d_20260928` | V01〜V46（46 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `req_split_20261001` | V01〜V02（2 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
M2 は、4つの場面（レンジ・上げ・下げ・スパイク）の判定を、全部の戦略のために組む段です。組んだ判定の良し悪しは、答え合わせに使う札（そのバーが後から見て実際にレンジだったかの答え）と照らして測ります。いまの札の式は観察の道具（observe_diag.py の _regime_labels）の中に在り、先を見る本数は組む側の設定と共用で、札を直すには H2 の印の対象を開いて式を書き替えるしかありません。14a（M2-F-6d）は、札を作る場所を1つにし、数字を設定に、式を版にして、あとで直しやすくする工事です。大きいので3つに分けました（まこさん「よい」）。この工事 A は、札を作る部品 regime_label.py と設定 recipes/regime_label.json を新しく作り、H2 の印の対象に足します。観察の道具と測る道具を部品に切り替えるのは工事 B、⑪タブは工事 C です。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 札を作る部品が無い | `find v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild -maxdepth 1 -name regime_label.py` | 実装の前は何も出ない（ファイルが無い）。実装の後はファイルの道が出る | （終了コード 0） |
| 札の設定が無い | `find v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes -maxdepth 1 -name regime_label.json` | 実装の前は何も出ない。実装の後はファイルの道が出る | （終了コード 0） |
| H2 の見張りの一覧に札の部品が無い | `grep -c -F 'regime_label' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py` | 実装の前は当たる行が無い。実装の後は、札の部品と設定を足す行に当たる | 0（終了コード 1） |

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
<!-- ACC_RANKING_START hash=c4af94c1b5c022bf gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`material_ranking.json`。

**成績表に載っている列の本数**（札＝強さ・先読み24・執行足より上の時間足だけ）

| 役割 | 上位足の列の本数 | 分離力の高い順に3本 |
|---|---|---|
| env | 1918 | MMI500__1d（0.639）／PWMA20傾き%__1d（0.595）／kurtosis50__1d（0.405） |
| location | 1414 | close vs TSF%20__1d（0.429）／close vs TEMA%20__1d（0.434）／close vs LINREG%20__1d（0.435） |
| sufficiency | 1528 | MMI500__1d（0.639）／kurtosis50__1d（0.405）／MAD比50__1d（0.592） |
| trigger | 250 | TD_SEQ_DN__10m（0.473）／TD_SEQ_DN__15m（0.484）／HT_LEADSINE__10m（0.514） |

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
| 1 | 観察の道具と測る道具を部品に切り替えること・自己検査 T6・壊すプログラム b119〜b121 | 工事 B でやる。T6 は呼ぶ側を切り替えた後でないと必ず落ちる | ok_t6_20261002 |
| 2 | ⑪タブの道具を直すこと | 工事 C でやる | ok_split_20261002 |
| 3 | 版2 の使う値を選ぶこと・採点に使う版を band_hold に切り替えること | 使う値は まこさんが⑪タブの目と検査15 で選ぶ。選ぶまでは版1 のまま | label_structure_definition_verbatim_20260929.txt の11行目 |
| 4 | 上げ・下げ・スパイクの札を作ること | 範囲は M2-M-1 で まこさんが決める。版2 の向きと大きさは版1 と同じ式のまま | label_structure_definition_verbatim_20260929.txt の36〜37行目 |
| 5 | 成績表 material_ranking.json を作り直すこと | 札の版を書く口は工事 B。作り直しは約2時間14分かかる | m2_todo.json の M2-F-6d の注意 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| — | 無し（やることの表の「決めてほしいこと」が「無し」か空） | — | — |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、答え合わせに使う正解ラベル（札）を作る部品 regime_label.py と、その設定 recipes/regime_label.json を新しく作るものです。**14a（札を作る場所を1つにまとめる工事）を3つに分けた最初の工事です（まこさん「よい」2026-10-02）。
**①いま何が起きているか。**札の式は観察の道具（observe_diag.py）の _regime_labels に書いてあり、先を見る本数（24・288）は組む側の設定（search_limits.json の state_hold_bars_range）と共用です。札を直すには H2 の印の対象を開いて式を書き替えるしかありません。
**②この工事で何が変わるか。**札の部品と設定が出来ます。版1（er_median）は _regime_labels の式を1文字も変えずに写した物、版2（band_hold）は定義の文（役割ごとに、前の山と谷から帯を作り、終値が帯の中・帯の幅が手数料の床以上・次の保有の上限の本数のあいだ帯の中に居続けた）です。採点に使う版は設定の1行で選び、既定は版1 です。札の部品と設定を H2 の印の対象に足します。
**③まだ誰も部品を呼びません。**観察の道具と測る道具を部品に切り替えるのは工事 B、⑪タブは工事 C です。だから この工事の後も、札・順位表・成績表・⑪タブの数字は1つも変わりません。工事 B までのあいだ、版1 の式は observe_diag.py と regime_label.py の2か所に在りますが、呼ばれるのは observe_diag.py の方だけです。工事 B で observe_diag.py の式を消して部品を呼ぶ形にし、自己検査 T6 がそれを見ます。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、札の部品の自己検査（regime_label.py --selftest）を走らせます。引数なしで走らせると、採点に使う版と版の名前を出します。
**誰が結果を使うか。**工事 B から、観察の道具（_regime_labels・_regime_horizons）と測る道具（_labels_for）が、工事 C から⑪タブの道具が、この部品を呼びます。この工事の時点では、呼ぶ所は自己検査だけです。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**札の部品が受け取るもの。**値決め窓の5分足（高値・安値・終値）と、先を見る本数か役割の名前。
**札の部品が出すもの。**3つの見方（強さ・向き・大きさ）ごとに、バーごとの真偽と「その行が使えるか」の真偽。形はいまの _regime_labels と同じです（工事 B で呼ぶ側を変えずに済むため）。版2 の強さは「レンジだった の否定」で、向きと大きさは版1 と同じ式です（上げ・下げ・スパイクの札は M2-M-1 で決める）。
**札の版の名前。**版1＝label-er24-288。版2＝label-band-<役割>-x<倍率>-m<m>-c<c>-mw<まとめる幅>-wl<幅の線>-h<続く本数>。★⑪タブのファイル名になるので英字だけにし、日本語の名前と値は⑪タブの仕様に出します（工事 C）。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 数字は全部 設定ファイルに置く・コードには書かない | まこさん決定 2026-09-28（構造の文） | 帯・幅・続くの数字、先を見る本数、役割の保有の範囲は regime_label.json に置く。コードは読むだけ |
| 手数料の床は既存の定数を読む | まこさん決定 2026-09-28（構造の文） | fee_floor() が e38_logic_parts.SCALP_FLOOR を import して読む。まとめる幅と幅の線は「手数料の床の何倍か」で設定に書く |
| 札の式を版で持つ | まこさん決定 2026-09-28（構造の文の1つ目） | 版1（er_median）と版2（band_hold）を設定の「版」に置き、「採点に使う版」の1行で選ぶ |
| いまの ER の札を版の1つとして残す | まこさん OK 2026-09-28（§51 の3） | 版1 の式は _regime_labels の式を1文字も変えずに写す。T5 がニセのデータで前の式と同じ答えを確かめる |
| 札を作る場所を1つにする | まこさん決定 2026-09-28（構造の文の2つ目） | この工事で部品を作り、工事 B で呼ぶ側を切り替えて完成する。T6 は工事 B で足す |
| 札は評価にだけ使う（判定の条件・入口に入れない） | worklog 20260928 §44・word_replacements の「正解ラベル」の行 | 未来を見る行には # H2OK を付ける。呼ぶのは工事 B・C の道具だけ |
| 乱数を使わない | 恒久67番 | ⑪タブに出す値の組は、範囲の両端と真ん中の決まった並び。T9 が2回呼んで同じかを見る |
| 値を選ぶのは、⑪タブの まこさんの目と検査15。CC は選ばない | 定義の文（label_structure_definition_verbatim_20260929.txt の11行目） | 使う値は空のまま。空のまま band_hold を採点に使う版にすると止まる |
| 帯は、近い山を1つにまとめ、c 個以上なら上の線、谷で下の線を作る | 定義の文（同 9行目） | _line が近い山を群にまとめ、c 個以上の群を線にする（どの群を線にするかは CC が決めた＝決めたことと理由）。T11 が見る |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| regime_label.py | 設定を読む・札の2つの版を作る・札の版の名前を作る・⑪タブに出す値の組を作る・自己検査 T1〜T5・T7〜T11 | **新設** |
| recipes/regime_label.json | 札の数字と、採点に使う版 | **新設** |
| .claude/breaks/b118_band_continue_off.sh | 帯の版の「続く」の判定を外すと T10 が落ちるかを試す | **新設** |
| leak_causality_diag.WATCHED | H2 の印の対象に regime_label.py と regime_label.json を足す | 直す |
- 触る所（regime_label.py）＝<モジュール直下>・load_config・fee_floor・horizons・roles・role_bars・er_median・band_range・band_hold・keys・key_bars・key_label・groups・labels_for_key・labels_at_bars・bars_keys・version_tag・spec・variants・_synth・selftest・_line
- 触る所（leak_causality_diag.py）＝<モジュール直下>

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. 当てる道具（apply_audit_fix.py --design）で実装の指示を当てます（22番の見張りの一覧と、新しいファイル3本）。
2. regime_label.py --selftest（T1〜T5・T7〜T11）を走らせます。★走らせる前に時間の見込みをフロー宣言に書きます（恒久60〜62番）。
3. 壊すプログラム b118 を測ります（run_breaks.py --measure-only）。
4. leak_causality_diag.py は H2 の印の対象（見張りの一覧の中に自分が在る）なので、印の照合（enforce_g2_pass.py・enforce_h2_pass.py の --check-fingerprint）で外れた方を、G2 → H2 の順に取り直します。
5. 実装を監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝終値が100と101のあいだを8本ごとに往復し、960本目から1本ごとに0.1ずつ上がる合成データで、scalp（保有の上限12本・倍率5＝前の60本の山と谷）の札を作る。959本目は、前の60本の山が101・谷が100で、終値100.25は帯の中、幅は1%で手数料の床0.08%以上。しかし次の12本のうちに終値が101を超えるので「続く」が成り立たず、「レンジだった」にならない（自己検査 T10）。壊すプログラム b118 が「続く」の判定を外すと、この959本目が「レンジだった」になり、T10 が落ちる。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**探す値＝版2 の6つ（役割ごと）。**範囲は設定ファイルの「範囲」の欄に在ります。この工事では値を選びません。
| 値 | scalp の範囲 | daytrade の範囲 | 出どころ |
|---|---|---|---|
| 保有の下限・上限（本） | 1〜12 | 12〜120 | search_limits.json の hold_range_by_role（自己検査 T8 が食い違いを見る） |
| 倍率（帯を作る前の本数＝保有の上限の何倍か） | 4〜6 | 4〜6 | 法則 C4（上位足の比） |
| m（山と谷を決める前後の本数） | 1〜12 | 12〜120 | 定義の文（その役割の保有の下限〜上限） |
| c（上の線・下の線に要る山と谷の数） | 2〜3 | 2〜3 | 法則 R1 の目安3・StockCharts の片側2 |
| まとめる幅・幅の線（手数料の床の何倍か） | 1.0 | 1.0 | 定義の文（手数料の床そのもの） |
| 続く本数（保有の上限の何倍か） | 1.0 | 1.0 | 定義の文（保有の上限そのもの） |

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**設定ファイル recipes/regime_label.json（新設）。**採点に使う版（er_median か band_hold）・版1 の先を見る本数（24・288）・版2 の役割ごとの保有の範囲と6つの値の範囲と使う値（空）。使う値が空のまま band_hold を採点に使う版にすると、読む時点で止まります（fail-closed）。
**コマンドの旗。**札の部品は --selftest だけを持ちます。引数なしで、採点に使う版と版の名前を出します。
**search_limits.json は変えません。**先を見る本数（24・288）は同じ値を regime_label.json に書きます。組む側の保つ上限（state_hold_bars_range）は今までどおり search_limits.json を読みます。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに画面に出るもの。**①regime_label.py --selftest の T1〜T5・T7〜T11 の行と「全部 pass」。②引数なしの regime_label.py が {"採点に使う版": "er_median", "版の名前": "label-er24-288"} を出す。③H2 の印の対象（h2_pass.json の files）に regime_label.py と regime_label.json が入る。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| 設定ファイルが無い | 札の部品が読む時点で止まる（LabelError＝終了） |
| 採点に使う版が、設定の「版」に無い名前 | 止まる |
| 採点に使う版が band_hold なのに、役割の使う値が空 | 止まる（自己検査 T7 が確かめる） |
| 版2 の札を作るバーに高値・安値の列が無い | 列が無いと言って止まる（KeyError） |
| 役割の保有の範囲が search_limits.json と食い違った | 自己検査 T8 が落ちる |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**新しく作るもの。**regime_label.json（4-9）。
**形が変わるもの。**この工事では無し。順位表・落ちた候補・成績表に札の版を書くのは工事 B、⑪タブの版の仕様は工事 C です。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**札の部品は何も書きません（読むだけ）。**自己検査 T7 だけが、一時の置き場（tempfile）に設定の写しを書きます。

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**窓。**札を作るのは値決め窓（periods.SEARCH_START〜SEARCH_END）だけです。窓の切り方は呼ぶ側が持ちます（_assert_search_window_only・工事 B から）。
**足。**5分足だけです。版2 の保有の範囲・倍率・m・続く本数は、全部 5分足の本数で数えます。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| regime_label.py --selftest | 測っていない | ★走らせる前に、worklog から過去の実測を探し、無ければ小さく測ってから走らせる（恒久61・62番） |
| G2 の取り直し | 約30秒 | 前の実測 29.2秒（worklog 20261001 §35） |
| H2 の取り直し | 約5分 | 前の実測 4分57秒（worklog 20261001 §35） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**奪い合いに気をつけるもの。**設定ファイルは読むだけです。自己検査は一時の置き場にだけ書くので、並走しても奪い合いません。H2 と G2 の印は、取り直しを2つ同時に走らせません。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**書き換えられては困る記録。**設定ファイル regime_label.json を書き替えると札が変わります。だから H2 の印の対象に足し、書き替えたら H2 を取り直すまで engine_tuner が走らない形にします。人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**自己検査の各行（T1〜T5・T7〜T11）と、参考の数（T1 と T3 の割合）と、「全部 pass」か ❌ の行。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **leak_causality_diag.py は H2 の印の対象です。**直した後は、H2 を取り直すまで engine_tuner が走りません（4-4 の手順4）。見張りの一覧に2本を足すので、H2 の印の対象は22件から24件になります。
2. **札の部品は、まだ誰も呼びません。**札・順位表・成績表・⑪タブの数字は変わりません。
3. **H2 の見張りの一覧（WATCHED・h2_scan.py の行）を触る既存の壊すプログラムは0本でした**（.claude/breaks/*.sh を grep した）。
4. **leak_causality_diag.py の251行より後の行番号を引いている文書は0件でした**（監査・承認の控え・worklog を除いて git grep した）。

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| observe_diag._regime_labels | 版1 の式（1文字も変えずに写す） |
| observe_diag._synth_regime_bars | T5 の答えの分かるニセのデータ（呼ぶだけ） |
| search_limits.json の書き方（lo・hi の範囲） | 設定の範囲の書き方 |
| b113_catch_share_broken.sh | 壊すプログラムの形（壊す対象が1か所でなければ止まる） |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=40a9fbf6a6f896c5 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/leak_causality_diag.py
直す箇所: 251行（WATCHED）
直す前の文字:
~~~
    f"{_PR}/h2_scan.py",
~~~
足す文字:
~~~

    # ★2026-10-02（M2-F-6d の工事 A・L-8）＝札の部品と設定を印の対象に足す。観察の道具が読み込むのは工事 B（先に足しておけば、読み込んだ時から印が見張る）。
    f"{_PR}/regime_label.py", f"{_PR}/recipes/regime_label.json",
~~~
根拠の抜き書き: scripts/priority_rebuild/leak_causality_diag.py:251「    f"{_PR}/h2_scan.py",」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/usr/bin/env python3
"""regime_label.py — 答え合わせに使う正解ラベル（札）を作る、ただ1つの場所（M2-F-6d・2026-09-29）。

なぜ在るか（まこさん 2026-09-28・逐語は m2_todo.json の M2-F-6d の注意）
  札が正しいかは、最後は M2-L の net で分かる。外れていたら札を直して段1から並べ直す。
  そのときに直しやすく・どの札で選んだかをたどれるように、札を作る場所を1つにし、数字は設定ファイルに置き、
  札の式そのものを版として持つ。

何をするか
  ・設定ファイル recipes/regime_label.json を読む（数字はコードに1つも書かない）。
  ・版1「er_median」＝いままでの札（observe_diag._regime_labels の式をそのまま移した）。
      そのバーから先 n本の値動きを3つの見方で真偽にする（強さ・向き・大きさ・中央値で切る）。n＝設定の「先を見る本数」。
  ・版2「band_hold」＝1411行目の定義（役割ごと・帯・幅・続く）。
      帯＝そのバーの前（保有の上限 × 倍率 本）の山と谷。山＝前後 m 本で最も高いバー（谷は最も低い）。
      上の線＝近い山（「まとめる幅」以内）を1つにまとめ、c 個以上の群のうち終値に いちばん近い上の群（_line）。下の線は谷で同じ。
      幅＝(上の線 − 下の線) ÷ 終値 が「幅の線」以上。続く＝次のバーから「続く本数」本の終値が全部 帯の中。
      そのバーの終値が帯の中 ∧ 幅 ∧ 続く ＝「レンジだった」。「強さ」の真偽＝レンジだった の否定（使える行だけ）。
      「向き」「大きさ」は版1 と同じ式（先の本数＝続く本数）＝上げ・下げ・スパイクの札は M2-M-1 で決める。
      まとめる幅と幅の線は「手数料の床（e38_logic_parts.SCALP_FLOOR）の何倍か」で書く（構造の文＝手数料の床は既存の定数を読む）。
  ・採点に使う版は設定ファイルの「採点に使う版」の1行（既定＝er_median＝いままでと同じ）。

呼ぶ側
  observe_diag._regime_labels・_regime_horizons（中身はここを呼ぶだけ）／regime_r9_diag._labels_for／
  scripts/dashboard/build_regime_label_dashboard.py（⑪タブの版）。
  ★呼ぶ側を切り替えるのは工事 B（観察の道具・測る道具）と工事 C（⑪タブ）。呼ぶ側の確かめ（自己検査 T6）は工事 B で足す。

★札は先を見るのが仕事（評価にだけ使う・判定の条件や入口には入れない）＝未来参照の行には H2OK を付ける。
★乱数は使わない（恒久67番）。
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
CONFIG = HERE / "recipes" / "regime_label.json"
LABEL_NAMES = ("強さ", "向き", "大きさ")
BAND_KEYS = ("倍率", "m", "c", "まとめる幅", "幅の線", "続く本数")
# 版の名前に入れる略（版の名前は⑪タブのファイル名になるので英字だけにする・日本語の名前と値は⑪タブの仕様に出す）
TAG_KEYS = {"倍率": "x", "m": "m", "c": "c", "まとめる幅": "mw", "幅の線": "wl", "続く本数": "h"}


class LabelError(SystemExit):
    """札の設定が読めない・足りない（fail-closed）。"""


# ══ 設定 ═══════════════════════════════════════════════════════════════════════════
def load_config(path=None) -> dict:
    """設定ファイルを読む。無い・採点に使う版が無い・版2 の使う値が無い → 止まる。"""
    p = pathlib.Path(path) if path else CONFIG
    if not p.exists():
        raise LabelError(f"[札] 設定ファイルが無い: {p}（fail-closed）")
    d = json.loads(p.read_text(encoding="utf-8"))
    vers = d.get("版") or {}
    use = d.get("採点に使う版")
    if use not in vers:
        raise LabelError(f"[札] 採点に使う版 {use} が設定の「版」に無い（在る版＝{sorted(vers)}・fail-closed）")
    if use == "band_hold":
        for role, rc in (vers["band_hold"].get("役割") or {}).items():
            if not rc.get("使う値"):
                raise LabelError(f"[札] 採点に使う版が band_hold なのに、役割 {role} の「使う値」が空（⑪タブで まこさんが選ぶ・fail-closed）")
    return d


def fee_floor() -> float:
    """手数料の床＝既存の定数を読む（構造の文・e38_logic_parts.py:23）。"""
    import e38_logic_parts as lp
    return float(lp.SCALP_FLOOR)


def horizons(cfg=None) -> tuple:
    """版1 の先を見る本数。"""
    cfg = cfg or load_config()
    return tuple(int(x) for x in cfg["版"]["er_median"]["先を見る本数"])


def roles(cfg=None) -> list:
    cfg = cfg or load_config()
    return list((cfg["版"].get("band_hold") or {}).get("役割") or {})


def role_bars(cfg, role: str, values: dict | None = None) -> int:
    """その役割の札が先を見る本数＝保有の上限 × 続く本数（成績表の鍵に使う）。"""
    rc = cfg["版"]["band_hold"]["役割"][role]
    v = values or rc["使う値"]
    return int(round(int(rc["保有の上限"]) * float(v["続く本数"])))


# ══ 版1＝いままでの札（observe_diag._regime_labels の式をそのまま移した）══════════════════════
def er_median(win: pd.DataFrame, n: int) -> dict:
    """そのバーから先 n本の値動きの性質を、3つの見方で真偽に直す（＝正解の印）。

    ①強さ   … 先 n本の ER（まっすぐ進んだ距離 ÷ 実際に歩いた距離）が、この窓の中央値以上か
    ②向き   … 先 n本の終値が、いまの終値より上か
    ③大きさ … 先 n本で動いた幅 ÷ 直前 n本で動いた幅 が、この窓の中央値以上か
    戻り＝{名前: (真偽の並び, その行が使えるか)}。先が足りない末尾は「使えない」になる。
    ★どれも比か上下だけ＝ドルの絶対値を1つも使わない（H6）。
    """
    c = win["close"].astype(float)
    fwd = c.shift(-n) - c  # H2OK: 正解の印（ラベル）を作る側＝本番の判断には入らない。build_labels_pct の Triple Barrier と同じ作り。値決め窓に閉じ、窓の外へはみ出す分は欠損になって落ちる
    walk = c.diff().abs().rolling(n).sum().shift(-n)  # H2OK: 同上（ラベル側の未来参照）。材料の列は build_features が当該バーまでの確定値だけで作る＝判断に未来は入らない
    er = (fwd.abs() / walk).where(walk > 0)
    past = (c - c.shift(n)).abs()                             # 直前 n本で動いた幅（未来を見ない）
    size = (fwd.abs() / past).where(past > 0)
    return {"強さ": (er >= er.median(), er.notna()),
            "向き": (fwd > 0, fwd.notna()),
            "大きさ": (size >= size.median(), size.notna())}


# ══ 版2＝帯・幅・続く（1411行目の定義）════════════════════════════════════════════════════
def _line(vals, merge_w: float, c_min: int, x: float, above: bool):
    """近い山（谷）を1つにまとめ、c 個以上の群を線にする。終値 x に いちばん近い上（下）の線を返す。無ければ None。

    定義の文（.claude/state/label_structure_definition_verbatim_20260929.txt）＝「帯は、近い山を1つにまとめ、
    c 個以上なら上の線、谷で下の線を作ります」。
    ★文に無いので CC が決めたこと（2026-09-29・依頼書の自己申告）＝①まとめ方＝高い山から順に並べ、
      群の先頭の山から「まとめる幅」以内の山を同じ群に入れる（谷は低い方から）②線の値＝群の先頭の山（谷）
      ③線が2本以上あるとき＝終値に いちばん近い上の線と下の線を使う。
    """
    v = np.sort(np.asarray(vals, float))
    if above:
        v = v[::-1]
    best = None
    i = 0
    while i < len(v):
        j = i + 1
        while j < len(v) and abs(v[j] - v[i]) <= v[i] * merge_w:
            j += 1
        if j - i >= c_min:
            line = float(v[i])
            if (above and line >= x) or ((not above) and line <= x):
                best = line                                   # 先頭から遠い順に見るので、最後に残るのが いちばん近い線
        i = j
    return best


def band_range(win: pd.DataFrame, hi_bars: int, values: dict, floor: float) -> tuple:
    """「レンジだった」の真偽と、使えるか。戻り＝(pd.Series[bool], pd.Series[bool])。"""
    a = float(values["倍率"])
    m = int(values["m"])
    c_min = int(values["c"])
    merge_w = floor * float(values["まとめる幅"])
    width_line = floor * float(values["幅の線"])
    hold_n = int(round(hi_bars * float(values["続く本数"])))
    look = int(round(hi_bars * a))
    h = win["high"].astype(float)
    lo = win["low"].astype(float)
    cl = win["close"].astype(float).to_numpy()
    n_all = len(cl)
    is_pk = (h == h.rolling(2 * m + 1, center=True).max()).to_numpy()   # H2OK: 札を作る側＝山は前後 m 本で決める（評価にだけ使う・判断に入らない）
    is_tr = (lo == lo.rolling(2 * m + 1, center=True).min()).to_numpy()  # H2OK: 同上（谷）
    pk_idx = np.flatnonzero(is_pk)
    tr_idx = np.flatnonzero(is_tr)
    hv = h.to_numpy()
    lv = lo.to_numpy()
    cs = pd.Series(cl)
    fmax = cs.rolling(hold_n).max().shift(-hold_n).to_numpy()  # H2OK: 札を作る側＝続くを見る（次のバーから hold_n 本の終値の最大）
    fmin = cs.rolling(hold_n).min().shift(-hold_n).to_numpy()  # H2OK: 同上（最小）
    rng = np.zeros(n_all, bool)
    ok = np.zeros(n_all, bool)
    for t in range(look, n_all - hold_n):
        ok[t] = True
        p0, p1 = np.searchsorted(pk_idx, t - look), np.searchsorted(pk_idx, t)   # 山は t より前（t を含まない）
        q0, q1 = np.searchsorted(tr_idx, t - look), np.searchsorted(tr_idx, t)
        if p1 - p0 < c_min or q1 - q0 < c_min:
            continue
        x = cl[t]
        top = _line(hv[pk_idx[p0:p1]], merge_w, c_min, x, True)    # 上の線＝近い山を1つにまとめ、c 個以上の群
        bot = _line(lv[tr_idx[q0:q1]], merge_w, c_min, x, False)   # 下の線＝谷で同じ
        if top is None or bot is None:
            continue
        if not (bot <= x <= top) or (top - bot) / x < width_line:
            continue
        if fmax[t] <= top and fmin[t] >= bot:
            rng[t] = True
    return pd.Series(rng, index=win.index), pd.Series(ok, index=win.index)


def band_hold(win: pd.DataFrame, cfg: dict, role: str, values: dict | None = None) -> dict:
    """版2 の札（3つの見方の形で返す＝呼ぶ側を変えない）。"""
    rc = cfg["版"]["band_hold"]["役割"][role]
    v = values or rc["使う値"]
    rng, ok = band_range(win, int(rc["保有の上限"]), v, fee_floor())
    er = er_median(win, role_bars(cfg, role, v))
    return {"強さ": (ok & ~rng, ok), "向き": er["向き"], "大きさ": er["大きさ"]}


# ══ 呼ぶ側の口 ═══════════════════════════════════════════════════════════════════════
def keys(cfg=None) -> list:
    """採点に使う版の札の鍵＝版1 は先を見る本数（24・288）／版2 は役割（scalp・daytrade）。"""
    cfg = cfg or load_config()
    return list(horizons(cfg)) if cfg["採点に使う版"] == "er_median" else roles(cfg)


def key_bars(key, cfg=None) -> int:
    """鍵を、先を見る本数に直す（成績表の鍵・間引きの間隔に使う）。"""
    cfg = cfg or load_config()
    return int(key) if cfg["採点に使う版"] == "er_median" else role_bars(cfg, str(key))


def key_label(key, cfg=None) -> str:
    """鍵を、行の名前に入れる文字にする（版1＝「先24本」＝いままでと同じ／版2＝役割の名前）。"""
    cfg = cfg or load_config()
    return f"先{int(key)}本" if cfg["採点に使う版"] == "er_median" else str(key)


def groups(cfg=None):
    """役割ごとに並べるときの組（版1＝None＝いままでどおり／版2＝役割の名前の並び）。"""
    cfg = cfg or load_config()
    return None if cfg["採点に使う版"] == "er_median" else [key_label(k, cfg) for k in keys(cfg)]


def labels_for_key(win: pd.DataFrame, key, cfg=None) -> dict:
    cfg = cfg or load_config()
    if cfg["採点に使う版"] == "er_median":
        return er_median(win, int(key))
    return band_hold(win, cfg, str(key))


def labels_at_bars(win: pd.DataFrame, n: int, cfg=None) -> dict:
    """先を見る本数 n の札（observe_diag._regime_labels が呼ぶ）。n が版2 の役割の本数に当たればその役割の札、
    当たらなければ版1 の式（自己検査が小さな n で呼ぶ所を壊さない）。"""
    cfg = cfg or load_config()
    if cfg["採点に使う版"] == "band_hold":
        for role in roles(cfg):
            if role_bars(cfg, role) == int(n):
                return band_hold(win, cfg, role)
    return er_median(win, int(n))


def bars_keys(cfg=None) -> tuple:
    """採点に使う版の、先を見る本数の並び（observe_diag._regime_horizons が返す物）。"""
    cfg = cfg or load_config()
    return tuple(sorted(key_bars(k, cfg) for k in keys(cfg)))


def version_tag(cfg=None, version=None, role=None, values=None) -> str:
    """札の版の名前＝版＋役割＋値（⑪タブの版の名前・順位表・成績表に書く）。"""
    cfg = cfg or load_config()
    ver = version or cfg["採点に使う版"]
    if ver == "er_median":
        return "label-er" + "-".join(str(x) for x in horizons(cfg)) if role is None else f"label-er{int(role)}"
    rs = [role] if role else roles(cfg)
    parts = []
    for r in rs:
        v = values or cfg["版"]["band_hold"]["役割"][r].get("使う値") or {}
        parts.append(f"{r}-" + "-".join(f"{TAG_KEYS[k]}{v.get(k)}" for k in BAND_KEYS))
    return "label-band-" + "_".join(parts)


def spec(cfg=None) -> dict:
    """設定ファイルの中身そのまま（⑪タブの仕様に出す＝手で書き写さない）。"""
    return json.loads(json.dumps(cfg or load_config()))


def variants(cfg, role: str) -> list:
    """⑪タブに出す値の組＝範囲の両端と真ん中を1つずつ動かす（ほかの値は真ん中）。乱数なし。"""
    rng = cfg["版"]["band_hold"]["役割"][role]["範囲"]

    def mid(k):
        lo, hi = rng[k]["lo"], rng[k]["hi"]
        return (lo + hi) // 2 if isinstance(lo, int) and isinstance(hi, int) else (lo + hi) / 2.0

    base = {k: mid(k) for k in BAND_KEYS}
    out = [dict(base)]
    for k in BAND_KEYS:
        for end in (rng[k]["lo"], rng[k]["hi"]):
            v = dict(base)
            v[k] = end
            if v not in out:
                out.append(v)
    return out


# ══ 自己検査（答えの分かるデータ・乱数なし）═══════════════════════════════════════════════
def _synth(kind: str, n: int = 1200) -> pd.DataFrame:
    """答えの分かる値動き。range＝100〜101 を8本ごとに往復／trend＝1本ごとに +0.1 で上がる／
    range80＝前の8割が range・後ろ2割が trend。"""
    if kind == "range":
        cyc = np.array([100.0, 100.25, 100.5, 100.75, 101.0, 100.75, 100.5, 100.25])
        c = np.tile(cyc, n // len(cyc) + 1)[:n]
    elif kind == "trend":
        c = 100.0 + 0.1 * np.arange(n)
    else:
        k = int(n * 0.8)
        a = _synth("range", k)["close"].to_numpy()
        c = np.concatenate([a, a[-1] + 0.1 * np.arange(1, n - k + 1)])
    idx = pd.date_range("2024-06-01", periods=n, freq="5min")
    return pd.DataFrame({"high": c, "low": c, "close": c}, index=idx)


def selftest() -> int:
    ng = []
    cfg = load_config()
    fl = fee_floor()
    vals = {"倍率": 5, "m": 3, "c": 2, "まとめる幅": 1.0, "幅の線": 1.0, "続く本数": 1.0}
    # T1 全部レンジ＝使える行はほぼ全部「レンジだった」
    r, ok = band_range(_synth("range"), 12, vals, fl)
    share = float(r[ok].mean()) if ok.any() else float("nan")
    if not share >= 0.95:
        ng.append(f"T1: 全部レンジのデータで、レンジだった の割合が {share:.3f}（0.95 以上のはず）")
    # T2 全部トレンド＝1本も「レンジだった」にならない
    r2, ok2 = band_range(_synth("trend"), 12, vals, fl)
    if bool(r2[ok2].any()):
        ng.append(f"T2: 全部トレンドのデータで、レンジだった が {int(r2[ok2].sum())} 本 出た（0本のはず）")
    # T3 レンジが8割＝版2 は8割近く、版1 は中央値で切るので約半分（版1 の弱点を見える形で残す）
    d3 = _synth("range80")
    r3, ok3 = band_range(d3, 12, vals, fl)
    s3 = float(r3[ok3].mean())
    e3m, e3u = er_median(d3, 12)["強さ"]
    e3 = float((~e3m[e3u]).mean())
    if not (s3 >= 0.7 and e3 <= 0.6):
        ng.append(f"T3: レンジが8割のデータで、版2 {s3:.3f}（0.7 以上のはず）・版1 {e3:.3f}（中央値で切るので 0.6 以下のはず）")
    # T4 幅の線を帯の幅（1%）より高くすると、1本も「レンジだった」にならない
    v4 = dict(vals)
    v4["幅の線"] = 0.02 / fl
    r4, ok4 = band_range(_synth("range"), 12, v4, fl)
    if bool(r4[ok4].any()):
        ng.append("T4: 幅の線を帯より広くしても、レンジだった が出た")
    # T5 版1 は前の式と同じ（observe_diag のニセのデータの N1 と同じ見本で、強さが区間の答えと一致）
    import observe_diag as od
    sdf, strend = od._synth_regime_bars()
    em, eu = er_median(sdf, 24)["強さ"]
    same = (strend.shift(-24) == strend) & (strend.shift(-1) == strend)  # H2OK: ニセのデータの中だけで完結する検査
    use = eu & same.fillna(False)
    if int(use.sum()) < 10 or float((em[use] == strend[use]).mean()) < 1.0:
        ng.append("T5: 版1 の強さが、答えの分かるニセのデータの区間と一致しない")
    # T7 採点に使う版が band_hold なのに使う値が空なら止まる
    import tempfile
    bad = json.loads(json.dumps(cfg))
    bad["採点に使う版"] = "band_hold"
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "x.json"
        p.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
        try:
            load_config(p)
            ng.append("T7: 使う値が空の band_hold を採点に使う版にしても止まらない")
        except SystemExit:
            pass
    # T8 版の名前に値が入る・役割の保有の範囲が組む側の設定と同じ（2か所に書いた値の食い違いを見る）
    tag = version_tag(cfg, "band_hold", "scalp", vals)
    if not all(f"{TAG_KEYS[k]}{vals[k]}" in tag for k in BAND_KEYS) or "scalp" not in tag or not tag.isascii():
        ng.append(f"T8: 版の名前に役割と値が入っていない（か英字でない）: {tag}")
    sl = json.loads((HERE / "recipes" / "search_limits.json").read_text(encoding="utf-8"))["hold_range_by_role"]
    for role in roles(cfg):
        rc = cfg["版"]["band_hold"]["役割"][role]
        if role not in sl or (int(rc["保有の下限"]), int(rc["保有の上限"])) != (int(sl[role]["lo_bars"]), int(sl[role]["hi_bars"])):
            ng.append(f"T8: 役割 {role} の保有の範囲が search_limits.json の hold_range_by_role と違う")
    # T9 ⑪タブの値の組＝真ん中1つ＋両端（重なりは除く）・乱数なし（2回 呼んで同じ）
    for role in roles(cfg):
        v1, v2 = variants(cfg, role), variants(cfg, role)
        if v1 != v2 or not v1:
            ng.append(f"T9: {role} の値の組が決まった並びでない")
    # T10 続くの確かめ＝レンジが終わる直前のバー（次の保有の上限の本数のうちに帯を抜ける）は「レンジだった」にならない
    k3 = int(len(d3) * 0.8)
    if not bool(ok3.iloc[k3 - 1]):
        ng.append("T10: レンジが終わる直前のバーが、使える行に入っていない（検査が空振りする）")
    elif bool(r3.iloc[k3 - 1]):
        ng.append("T10: レンジが終わる直前のバー（次の12本で帯を抜ける）が レンジだった になった")
    # T11 近い山を1つにまとめ、c 個以上の群を線にする＝いちばん高い山が1つだけでも、下の群（3個）が上の線になる
    if _line(np.array([103.0, 101.0, 101.01, 101.02]), 0.0008, 2, 100.5, True) != 101.02:
        ng.append("T11: いちばん高い山の群が c 個に足りないとき、下の群（c 個以上）が上の線にならない")
    if _line(np.array([97.0, 99.0, 98.99, 98.98]), 0.0008, 2, 99.5, False) != 98.98:
        ng.append("T11: いちばん低い谷の群が c 個に足りないとき、上の群（c 個以上）が下の線にならない")
    if _line(np.array([101.0, 101.01]), 0.0008, 3, 100.5, True) is not None:
        ng.append("T11: c 個に足りない群だけなのに、線ができた")
    print("[regime_label selftest] T1 全部レンジ ／ T2 全部トレンド ／ T3 レンジ8割（版1 の弱点）／ T4 幅の線 ／ "
          "T5 版1 は前の式と同じ ／ T7 使う値が空なら止まる ／ T8 版の名前・保有の範囲 ／ T9 値の組 ／ T10 続くの確かめ ／ T11 近い山のまとめ方")
    print(f"  参考＝T1 {share:.3f} ／ T3 版2 {s3:.3f}・版1 {e3:.3f}")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print(json.dumps({"採点に使う版": load_config()["採点に使う版"], "版の名前": version_tag()}, ensure_ascii=False))

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:5831「def _regime_labels(win: pd.DataFrame, n: int) -> dict:」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/recipes/regime_label.json
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
{
 "_これは何か": "答え合わせに使う正解ラベル（札）の設定。読むのは scripts/priority_rebuild/regime_label.py だけ（札を作る場所は1つ）。まこさん決定 2026-09-28（構造の文＝m2_todo.json の M2-F-6d の注意・worklog 20260928 §41-4）。",
 "_直し方": "値を書き替えて走らせ直すと、札と⑪タブの版が作り直される（scripts/dashboard/build_regime_label_dashboard.py）。採点に使う版を変えたら、成績表（observe_diag.py --rank-regime・前の実測 2時間14分）を作り直す。★コードは直さない。",
 "_search_limits に置かない理由": "search_limits.json は H2 と G2 の印の対象（h2_pass.json・g2_pass.json）＝札の値を変えるたびに H2（約13分）を取り直すことになる。版1 の先を見る本数は、組む側の state_hold_bars_range（保つ上限）と共用だったのを切り離した（値は同じ 24・288）。",
 "採点に使う版": "er_median",
 "_採点に使う版の意味": "R9 の3つの割合・順位表・成績表・⑪タブの既定に使う版。er_median＝いままでと同じ。band_hold にするのは、まこさんが⑪タブの目と検査15 で役割ごとの「使う値」を選んでから（空のまま band_hold にすると止まる）。選んだら band_hold にする＝測る道具と成績表が役割ごとの札で両方 測り、段ごとに役割ごとに10本ずつ残す（.claude/state/label_structure_definition_verbatim_20260929.txt の「1. どの役割の札で測るか」）。版1 には役割の札が無いので、版1 のあいだは役割で分けられない。",
 "版": {
  "er_median": {
   "説明": "いままでの札。そのバーから先 n本の値動きの ER（まっすぐ進んだ距離 ÷ 歩いた距離）が窓の中央値以上なら「トレンドだった」、未満なら「レンジだった」（強さ）。向き＝先 n本の終値が上か。大きさ＝先 n本の幅 ÷ 直前 n本の幅 が窓の中央値以上か。",
   "先を見る本数": [24, 288],
   "_先を見る本数の出どころ": "search_limits.json の state_hold_bars_range の両端（2026-08-21 まこさん承認 24a453d6…）。値は変えずに、ここへ移した。"
  },
  "band_hold": {
   "説明": "1411行目の定義（まこさん「これらをすべて満たすように、設計しなおせ」の一続き・worklog 20260928 §46）。役割ごとに1つ。そのバーの前（保有の上限 × 倍率 本）の山と谷から帯を作り、そのバーの終値が帯の中・帯の幅が幅の線以上・次のバーから続く本数の終値が全部 帯の中 なら「レンジだった」。",
   "_まとめる幅と幅の線の単位": "手数料の床（e38_logic_parts.SCALP_FLOOR＝0.08%）の何倍か。1411行目では両方とも手数料の床そのもの（＝1倍）。",
   "_続く本数の単位": "保有の上限の何倍か。1411行目では保有の上限そのもの（＝1倍）。",
   "役割": {
    "scalp": {
     "保有の下限": 1,
     "保有の上限": 12,
     "範囲": {
      "倍率": {"lo": 4, "hi": 6},
      "m": {"lo": 1, "hi": 12},
      "c": {"lo": 2, "hi": 3},
      "まとめる幅": {"lo": 1.0, "hi": 1.0},
      "幅の線": {"lo": 1.0, "hi": 1.0},
      "続く本数": {"lo": 1.0, "hi": 1.0}
     },
     "使う値": null
    },
    "daytrade": {
     "保有の下限": 12,
     "保有の上限": 120,
     "範囲": {
      "倍率": {"lo": 4, "hi": 6},
      "m": {"lo": 12, "hi": 120},
      "c": {"lo": 2, "hi": 3},
      "まとめる幅": {"lo": 1.0, "hi": 1.0},
      "幅の線": {"lo": 1.0, "hi": 1.0},
      "続く本数": {"lo": 1.0, "hi": 1.0}
     },
     "使う値": null
    }
   },
   "_範囲の出どころ": "保有の下限と上限＝search_limits.json の hold_range_by_role（regime_label.py の自己検査 T8 が食い違いを見る）。倍率 4〜6＝法則 C4（上位足の比）。m＝その役割の保有の下限〜上限（1411行目）。c 2〜3＝法則 R1 の目安3 と StockCharts の片側2。まとめる幅・幅の線・続く本数＝1411行目の値（1倍）だけ。★この3つの幅を広げる出どころは無い＝広げるのは まこさんが決める（この行を書き替える）。",
   "_使う値": "⑪タブで まこさんが選んだ値を書く（例＝{\"倍率\": 5, \"m\": 6, \"c\": 2, \"まとめる幅\": 1.0, \"幅の線\": 1.0, \"続く本数\": 1.0}）。空のあいだは band_hold を採点に使えない。"
  }
 }
}

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:20「  "hold_range_by_role": {」
状態: 確定

#### 実装 4
対象のファイル: .claude/breaks/b118_band_continue_off.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 帯の版の「続く」（次のバーから続く本数の終値が全部 帯の中）を見なくすると、自己検査 T10 が「レンジが終わる直前のバーが レンジだった になった」で落ちた
# EXPECT_MSG: ❌ T10
# b118 — regime_label.band_range の「続く」の判定を外すと、T10 が落ちるか（M2-F-6d・2026-09-29）
#   守っているもの＝完成の条件 #1（札の部品の自己検査が、帯・幅・続く の3つを全部 見ている）
#   壊し方＝`        if fmax[t] <= top and fmin[t] >= bot:` を `        if True:` にする（続くを見ない）。
#   期待＝regime_label.py --selftest の T10 が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

RL="$PR/regime_label.py"
guard "$RL"

python3 - "$RL" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        if fmax[t] <= top and fmin[t] >= bot:\n'
if s.count(old) != 1:
    raise SystemExit("[b118] 壊す対象の行が1か所でない: " + old.strip())
new = '        if True:  # b118 が壊した（続くを見ない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$RL" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b113_catch_share_broken.sh:1「#!/bin/bash」
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 4 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 14a を3つの工事に分け、工事 A は札の部品・設定・H2 の対象への追加・b118 だけにする | 1つの工事の案は約10万文字で、1回の返信に収まらない。部品を先に作り、使う側を後で切り替える順にした（まこさん「よい」2026-10-02） | 1つの工事のまま出す。捨てた理由＝返信に収まらない |
| 2 | 自己検査 T6 を工事 B へ移す | T6 は、観察の道具と測る道具が部品を呼んでいるかを見る。切り替えは工事 B なので、工事 A では必ず落ちる（まこさん「よい」2026-10-02） | T6 を残して工事 A で落ちたままにする。捨てた理由＝完成の条件を満たせない |
| 3 | H2 の見張りの一覧への追加（22番）は工事 A に入れる | OK された表の L-8 が、自己検査と H2 の対象への追加を1つにしている。部品と設定を先に印の対象に入れておけば、工事 B で読み込んだ時から印が見張る | 工事 B に入れる。捨てた理由＝L-8 を2つに割る |
| 4 | 22番の説明の行を、工事 A の事実に書き替える | 9/29 の控えの説明は「observe_diag.py が札を作る部品を読み込むようになった」で、工事 A の時点では事実でない | 控えの説明のまま当てる。捨てた理由＝コードの説明が実物と食い違う |
| 5 | 札の数字を search_limits.json に置かず、新しい regime_label.json に置く | search_limits.json は組む側の設定で、H2 と G2 の印の対象。札の値を変えるたびに組む側の設定を書き替えることになり、組む側の値と札の値が混ざる | search_limits.json に札の欄を足す。捨てた理由＝同じファイルに2つの役割を持たせると、片方だけ直したつもりでもう片方が変わる |
| 6 | 札の版の名前を英字だけにする（値の名前は x・m・c・mw・wl・h の略） | ⑪タブの版の名前はファイル名になる。日本語の名前と値は⑪タブの仕様にそのまま出す | 日本語の値の名前を版の名前に入れる。捨てた理由＝ファイル名と URL に日本語が入り、読み手ごとに扱いが分かれる |
| 7 | 帯の線の作り方＝近い山を1つにまとめ（高い山から順に並べ、群の先頭から まとめる幅 以内の山を同じ群）、c 個以上の群のうち終値に いちばん近い上の群の先頭を上の線にする（谷で下の線）。関数 _line・自己検査 T11 | 定義の文は「帯は、近い山を1つにまとめ、c 個以上なら上の線、谷で下の線を作ります」。どの群を線にするか・線の値・まとめ方は文に無いので、CC が決めた（worklog 20260929 §12・§14・§15） | いちばん高い山の群だけを見る。捨てた理由＝定義の文と食い違う |
| 8 | 壊すプログラムは b118 の1本にする | 札は選抜の答えそのもので、「続く」の判定が壊れても画面に出ない（恒久71番の線引きの内）。b119〜b121 が試す T6・⑫・⑬は工事 B の物 | 4本とも工事 A に入れる。捨てた理由＝試す相手が工事 A に無い |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=aff791fd23b9740b gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b118_band_continue_off.sh` | #1 | 帯の版の「続く」の判定を外すと、T10 が『❌』で落ちる |
| `—` | #2 | 壊すプログラムは付けない（設定の1行を読んで出すだけで、自己検査 T7・T8 が設定の読み方を見る） |
| `—` | #3 | 壊すプログラムは付けない（H2 の取り直しで、印の対象の一覧に2本が出ることを見る） |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 札の部品の自己検査の合成データの目安（T1 の0.95・T3 の0.7／0.6）が、実装して走らせると外れる | 走らせた数字をそのまま貼り、目安の方を実物に合わせるときは理由を書いて監査に出す（隠さない） |
| 2 | 工事 B までのあいだ、版1 の式が observe_diag.py と regime_label.py の2か所に在る | 呼ばれるのは observe_diag.py だけなので、結果は1つ。工事 B で observe_diag.py の式を消し、T6 が式の残りを見る |
| 3 | H2 の検査が、新しく対象に入る regime_label.py の未来参照の行（# H2OK を付けた行）で止まる | H2 の検査の結果をそのまま貼る。止まったら、札の行が判定に入っていないことを示して直し方を まこさんに出す |
| 4 | 版2 の札の時間が分からない（バーごとに山と谷を探す） | この工事では版2 を実データで走らせない。⑪タブの版を作る工事 C の前に1版を測る（恒久61番） |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる・新しいファイルを書く | 測っていない | 当てる道具は1件ずつ文字を置き換えるだけ |
| 自己検査と b118 | 測っていない | 4-14 |
| G2 と H2 の取り直し | 約5分30秒 | G2 29.2秒・H2 4分57秒（worklog 20261001 §35） |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝札の式と数字が、観察の道具の関数の中と組む側の設定の中に散らばっていて、札だけを直す口も、どの札で作った結果かを残す口も無いことです。この工事 A は、札を直す口（部品と設定）を作ります。結果の側に札の版を残す口は工事 B です。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。札もまだ誰も呼ばないので、判定の成績も動きません。

**③ root か symptom か**＝root です。札を直すたびに式を書き替える形は、写し間違いと古い結果の取り違えを生む symptom の運用です。この工事は、札を1か所の部品・数字を設定・式を版に置く所までを作ります。

**④ ベースアップ**＝版2 の定義は まこさんが OK した定義の文で、出どころの法則（R1・R4・R7・C4・C7・C9）は regime_laws.json の実物を読んで確かめました（読むもの宣言の10番）。c の目安は法則 R1 と StockCharts の片側2 から取りました。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。版1 の数字（24・288）は まこさんの決定（2026-08-21 承認の state_hold_bars_range の両端）、版2 の範囲の両端は search_limits.json・法則・定義の文、手数料の床は既存の定数です。使う値は まこさんが⑪タブの目と検査15 で選びます。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝札を作る部品と設定を作り、H2 の印の対象に足す（14a の工事 A＝L-2・L-3・L-4・L-8）。観察の道具と測る道具の切り替えは工事 B、⑪タブは工事 C（まこさん「よい」2026-10-02）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。⑪タブに出す値の組は範囲の両端と真ん中の決まった並びで、自己検査 T9 が2回呼んで同じかを見ます。札は条件をつなぐものではなく、答え合わせの答えです |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 値は点の一覧ではなく範囲で設定に書きます（lo・hi）。範囲の両端は、保有の範囲＝search_limits.json・倍率＝法則 C4・c＝法則 R1 と StockCharts・3つの幅＝定義の文から取り、私が作った数字はありません |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **版2 の札が、実際の相場で正しいか** | この工事では分かりません。まこさんが⑪タブの目と検査15 で確かめ、最後は M2-L の net で分かります |
| **工事 B までのあいだに、observe_diag.py の式だけが書き替えられたら** | 版1 の写しと食い違っても、この工事の自己検査では気づけません。工事 B で observe_diag.py の式を消すまでの間です |
| **設定ファイルを手で書き替えられたら** | 札が変わります。H2 の印の対象に入れるので、書き替えたら engine_tuner は H2 を取り直すまで走りません |
| **札の部品と壊すプログラムそのものを書き換えられたら** | 書き換えれば無効にできます。承認で凍結され、差分は git に出ます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=8f6e2ca91f81707c gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝3本（直す leak_causality_diag.py と、新しく作る regime_label.py・recipes/regime_label.json）を【7-8】に書いた。新しく作る2本は NEW_FILE にも書いた。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝leak_causality_diag.py＝この工事で直す既存のファイル。新しい regime_label.py は impl_functions に書いた）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイル3本（札の部品・札の設定・壊すプログラム b118）を NEW_FILE に、手本を MODEL に書いた（【7-8】）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝9/29 の設計書が まこさんの定義の文と食い違った3つ（検査15・帯の線の作り方・役割）は、控え 0174e179… で直っていることを確かめた。直す前の文字が実物にちょうど1か所ずつ在ることを道具で数えた。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 新しい部品＝札の部品 regime_label.py。H2 が走らせる案（tuner_recipes）には入らない（札の部品は engine_tuner の経路に無く、この工事ではまだ誰も呼ばない）。H2 の見張りの一覧に足すのは、部品と設定を書き替えたら印が外れて engine_tuner が止まるようにするため（実装の指示の1番）。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 直すファイルの行番号を指す文書は0件（4-13 の4）。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前で壊すプログラムを grep した。見張りの一覧を触る物は0本（4-13 の3）。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 新しい壊すプログラム b118 が測るコマンドは regime_label.py --selftest で、本物の結果の置き場（results/ ほか）や帳簿には書かない（T7 だけが一時の置き場に書く）。壊す相手は lib.sh の guard で控えに写して戻す（手本 b113）。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 新しく足す関数（札の部品の関数）は、全部 DESIGN_CONTRACT の impl_functions に書いた（【7-8】・下書きの道具が ast で照らした）＝regime_label.py: <モジュール直下>・load_config・fee_floor・horizons・roles・role_bars・er_median・band_range・band_hold・keys・key_bars・key_label・groups・labels_for_key・labels_at_bars・bars_keys・version_tag・spec・variants・_synth・selftest・_line ／ leak_causality_diag.py: <モジュール直下>。must_use に、band_hold と selftest が呼ぶ名前を書いた（下書きの道具が ast で照らした）。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足す旗（札の部品の --selftest）は、完成の条件の1行目が走らせる。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2f-label-structure-20261001）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝札の部品の --selftest・壊すプログラム b118・承認の前の検査。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 札の部品の自己検査が全部 通る（T1〜T5・T7〜T11＝全部レンジ・全部トレンド・レンジ8割・幅の線・版1 は前の式と同じ・使う値が空なら止まる・版の名前と保有の範囲・値の組・続くの確かめ・近い山のまとめ方） | `python3 scripts/priority_rebuild/regime_label.py --selftest` | 実経路 | 帯の版の「続く」の判定を外すと、T10 が『❌』で落ちる | `b118_band_continue_off.sh` | — | **未着手** |
| 2 | 引数なしで、採点に使う版 er_median と版の名前 label-er24-288 が出る | `python3 scripts/priority_rebuild/regime_label.py` | 実経路 | 壊すプログラムは付けない（設定の1行を読んで出すだけで、自己検査 T7・T8 が設定の読み方を見る） | `—` | — | **未着手** |
| 3 | H2 の見張りの一覧に、札の部品と設定の2本が在る | `grep -c -F 'regime_label' scripts/priority_rebuild/leak_causality_diag.py` | 実経路 | 壊すプログラムは付けない（H2 の取り直しで、印の対象の一覧に2本が出ることを見る） | `—` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=55d210b62f76b827 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/leak_causality_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `regime_label` | （この関数は実物に無い） |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 24件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=329663e608e28207 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/leak_causality_diag.py",
  "_impl_file の意味": "照らす相手は実在するファイルでなければならない（gen_acceptance.py:680〜683）。この工事で直す既存のファイルは leak_causality_diag.py だけ。regime_label.py は新しいファイルなので impl_functions にだけ書いた。",
  "impl_functions": {
    "scripts/priority_rebuild/regime_label.py": [
      "<モジュール直下>",
      "load_config",
      "fee_floor",
      "horizons",
      "roles",
      "role_bars",
      "er_median",
      "band_range",
      "band_hold",
      "keys",
      "key_bars",
      "key_label",
      "groups",
      "labels_for_key",
      "labels_at_bars",
      "bars_keys",
      "version_tag",
      "spec",
      "variants",
      "_synth",
      "selftest",
      "_line"
    ],
    "scripts/priority_rebuild/leak_causality_diag.py": [
      "<モジュール直下>"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数と、新しく作る関数。regime_label.py は全部 新しく作る。leak_causality_diag.py は見張りの一覧（モジュール直下）だけ。",
  "self_check_calls": [
    "regime_label"
  ],
  "_self_check_calls の意味": "実装の後の leak_causality_diag.py の見張りの一覧に在るはずの文字（実装の指示の1番が足す2本の道の中の名前）。★ファイル名を書かない＝7-7 の表が「読んだ」の行の下に並べ、まだ無いファイルを必読ゲートが数えるため。",
  "must_use": {
    "band_hold": [
      "band_range",
      "er_median",
      "fee_floor"
    ],
    "selftest": [
      "band_range",
      "er_median",
      "_line",
      "version_tag",
      "variants",
      "load_config"
    ]
  },
  "_must_use の意味": "regime_label.py の band_hold と selftest が呼ぶはずの名前（下書きの道具が ast で照らした）。照らす道具は impl_functions に書いた全部の .py を見る（verify_design_contract.py:1186〜1196）。",
  "spec_lists": {},
  "no_spec_lists_reason": "札の部品は外から一覧（候補・法則・成績表・範囲の鍵・印）を読まない。設定は regime_label.json だけで、自己検査 T7・T8 が読み方を見る。",
  "generated_from": {
    "impl_functions": "9/29 の控えの実装の指示28 の関数を ast で数えた（_labelA_draft_build.py が照らす）",
    "must_use": "band_hold と selftest が呼ぶ名前（ast で照らした）",
    "spec_lists": "空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/leak_causality_diag.py",
 "public_functions": {
  "scan_line": [],
  "scan_text": [],
  "scan_existing_code": [
   "scan_text"
  ],
  "load_features": [],
  "run_e38_trades": [
   "load_features"
  ],
  "h2_fingerprint": [],
  "load_tuner_df": [],
  "tuner_recipes": [],
  "tuner_check": [
   "compare_features",
   "compare_trades",
   "load_tuner_df",
   "tuner_recipes"
  ],
  "compare_features": [],
  "compare_trades": [],
  "selftest": [
   "compare_features",
   "compare_trades",
   "load_features",
   "scan_line",
   "scan_text"
  ],
  "main": [
   "compare_features",
   "compare_trades",
   "load_features",
   "run_e38_trades",
   "scan_existing_code",
   "selftest",
   "tuner_check"
  ]
 },
 "constants": {
  "TUNER_QUICK_DAYS": 90,
  "TUNER_CUT_DAYS": 45,
  "TUNER_GEN_N": 3,
  "TUNER_SEED": 20260816,
  "_PR": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild",
  "FORCED_EOD": "FORCE_CLOSE_EOD"
 },
 "cli_flags": []
}
```

<!-- ACC_SPEC_END -->

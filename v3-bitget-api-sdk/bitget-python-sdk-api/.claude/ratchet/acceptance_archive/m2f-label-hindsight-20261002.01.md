<!-- ARC iter="m2f-label-hindsight-20261002" -->

# 設計書｜役割ごとの札2本を、札の部品 regime_label.py の新しい版に入れる＝14a の工事 D

TARGET: scripts/priority_rebuild/regime_label.py, scripts/priority_rebuild/recipes/regime_label.json, scripts/dashboard/build_regime_label_dashboard.py, scripts/priority_rebuild/regime_r9_diag.py, .claude/breaks/b125_hindsight_osc_off.sh
NEW_FILE: .claude/breaks/b125_hindsight_osc_off.sh
MODEL: .claude/breaks/b118_band_continue_off.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2f-label-hindsight-20261002/ok_labelD_20261002`・`m2f-label-hindsight-20261002/okd_labelD_20261002`・`m2f-label-hindsight-20261002/req_6c_20261002`・`m2f-label-hindsight-20261002/req_6d_20260928`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2f-label-hindsight-20261002/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2f-label-hindsight-20261002 --write`。検出＝`--work m2f-label-hindsight-20261002 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=080ae219d193cb81 gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2f-label-hindsight-20261002/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2f-label-hindsight-20261002/ok_labelD_20261002.txt`（まこさんの発言）・`verbatim/m2f-label-hindsight-20261002/okd_labelD_20261002.txt`（まこさんが OK した CC の文）・`verbatim/m2f-label-hindsight-20261002/req_6c_20261002.txt`（まこさんの発言）・`verbatim/m2f-label-hindsight-20261002/req_6d_20260928.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝572 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_labelD_20261002` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_labelD_20261002` | V01〜V15（15 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_labelD_20261002` | V16〜V20（5 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V21〜V23（3 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V24〜V26（3 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V27〜V35（9 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V36〜V42（7 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V43〜V49（7 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V50〜V59（10 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V60〜V61（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V62〜V63（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V64〜V66（3 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V67〜V68（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V69〜V70（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V71〜V72（2 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V73〜V78（6 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V79〜V87（9 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V88〜V89（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V90〜V91（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V92〜V93（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V94〜V99（6 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V100〜V344（245 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V345〜V352（8 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V353〜V358（6 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V359〜V365（7 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V366〜V372（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V373〜V374（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V375〜V376（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V377〜V381（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V382〜V391（10 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V392〜V412（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V413〜V417（5 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V418〜V520（103 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_labelD_20261002` | V521〜V524（4 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `req_6c_20261002` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `req_6d_20260928` | V01〜V46（46 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
M2 は、4つの場面（レンジ・上げ・下げ・スパイク）の判定を、全部の戦略のために組む段です。組んだ判定の良し悪しは、答え合わせに使う札（そのバーが後から見て実際にレンジだったかの答え）と照らして測ります。札を作る場所は工事 A〜C で札の部品 regime_label.py の1か所になりましたが、採点に使う札は、いまも先の値動きを中央値で切る古い札（版1）です。2026-10-02 に まこさんが⑪タブで見て、役割ごとの札2本（スキャル用 label-c24b-scalp・デイトレ用 label-c24b-daytrade）に決めました。この2本は、いまは CC の手元の調べの道具でしか作れません。この工事 D は、2本の作り方を札の部品の新しい版（版3）として入れ、数字を設定ファイルに置き、採点に使う版を版3 にします。⑪タブの道具と測る道具も、版3 で動くようにします。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 設定ファイルに版3 が在るか | `grep -c -F 'hindsight_box' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/regime_label.json` | 実装の前は当たる行が無い。実装の後は当たる行が在る | 0（終了コード 1） |
| 採点に使う版が版3 か | `grep -c -F '"採点に使う版": "hindsight_box"' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/regime_label.json` | 実装の前は当たる行が無い。実装の後は当たる行が在る | 0（終了コード 1） |
| 札の部品に版3 の式が在るか | `grep -c -F 'def hindsight_range' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_label.py` | 実装の前は当たる行が無い。実装の後は当たる行が在る | 0（終了コード 1） |
| 測る道具が札に時刻を渡すか | `grep -c -F 'w.index = pd.DatetimeIndex' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py` | 実装の前は当たる行が無い。実装の後は当たる行が在る | 0（終了コード 1） |

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
| 1 | 札の値を変えること | まこさんが⑪タブで見て決めた2本の値のまま入れる。値を変えるなら、もう一度⑪タブで見ていただく | 2026-10-02 のまこさん「OK」・req_6c_20261002 |
| 2 | 上げ・下げ・スパイクの札を作ること | 範囲は M2-M-1 で まこさんが決める | worklog 20260928 §51 の4 |
| 3 | 版1 er_median と版2 band_hold の式を消すこと | 版1 はいままでの数字と比べるために残す。版2 は使えないと分かったが、消すかは まこさんが決める | worklog 20260928 §51 の3・worklog 20261002 §12 |
| 4 | 観察の道具 observe_diag.py を直すこと | 札の部品の口（labels_at_bars・bars_keys）を呼ぶだけで、版3 がそのまま通る（案を作る道具が、当てた後の札の部品で _regime_labels と _regime_horizons を走らせて確かめた） | scripts/priority_rebuild/observe_diag.py の5807行と5831行 |
| 5 | 画面（index.html・app.js）を直すこと | 仕様の欄は中身のまま並べる作りで、版の名前は版の一覧から読む | dashboard/assets/app.js の2924〜2938行 |
| 6 | 成績表の作り直しを、この工事の承認の中で走らせること | 前の実測で2時間14分かかる。実装と G2・H2 の後に、フロー宣言に時間の見込みを書いてから走らせる | observe_diag.py の6005行の注記・恒久の決まり60〜62番 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 工事 C と工事 D の実装の監査を出すか | 出さない。札が⑪タブの2本と1本ずつ同じことは案を作る道具が値決め窓の全部で数え、承認のプログラムが壊すプログラム b125 を走らせる。⑪タブの道具は読むための道具（恒久の決まり71番）で、決まりの上でも監査の側に入っていない | まこさん「この作業は監査必要？」（2026-10-02） |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、⑪タブで まこさんが決めた役割ごとの札2本を、札の部品 regime_label.py の新しい版（版3）にして、採点に使う札にするものです。**14a の4つ目の工事です。
**①いま何が起きているか。**採点に使う札は、いまも古い札（版1＝先の値動きを窓の中央値で切る札）です。まこさんが⑪タブで決めた2本は、CC の手元の調べの道具でしか作れません。だから M2 の段1 から先は、古い札で点数が付きます。
**②この工事で何が変わるか。**札の部品に版3 を足し、2本の作り方を移します。数字は全部 設定ファイルに置きます。採点に使う版を版3 にします。測る道具と成績表は、役割ごとの札（スキャル・デイトレ）で両方 測ります。⑪タブの道具は版3 を出せるようになります。
**③数字はどう変わるか。**版3 の札は、⑪タブで見た2本と1本ずつ同じです（スキャル 97,594本・デイトレ 77,535本がレンジ）。測る道具の列の名前の括弧の中は、先を見る本数から役割の名前に変わります。成績表は作り直すまで古い札のままで、測る道具は作り直すまで止まります（regime_r9_diag.py の510行の照らし）。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**札の部品は、測る道具（regime_r9_diag.py）・観察の道具の成績表（observe_diag.py --rank-regime）・⑪タブの道具が呼びます。私（CC）は、実装の後に自己テストと⑪タブの道具を1回ずつ走らせます。
**誰が結果を使うか。**M2 の段1〜段4 の点数付け（M2-F-8 から）と、まこさんの⑪タブの目です。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**5分足（値決め窓）と、設定ファイル recipes/regime_label.json の版3。手数料の床は e38_logic_parts.SCALP_FLOOR を読みます。
**書くもの。**札の部品は何も書きません（札を返すだけ）。⑪タブの道具は版のファイルと版の一覧を書きます（build_regime_from_tuner.py の write_version_files と update_index・直さずに呼ぶ）。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 数字は全部 設定ファイルに置く。コードには1つも書かない | まこさん決定 2026-09-28（構造の文） | 版3 の関数に 0・1・2 のほかの数字が無いことを、案を作る道具が ast で照らした |
| 手数料の床は既存の定数を読む | まこさん決定 2026-09-28（構造の文） | 行き来の幅の下限は fee_floor()（e38_logic_parts.SCALP_FLOOR） |
| 札の定義を版として持つ | まこさん決定 2026-09-28（構造の文） | 版3 を足す。版1・版2 は消さない |
| 札を作る場所は1つ | まこさん決定 2026-09-28（構造の文） | 呼ぶ側は札の部品の口を呼ぶだけ（自己テスト T6 が見る） |
| 役割ごとに札を持つ | まこさん決定 2026-09-28（構造の文） | 版3 は役割ごと（scalp・daytrade） |
| 札は先を見てよいが、評価にだけ使う | 要件定義書 §4.6.H2 | 先を見る行に全部 H2OK の注記（案を作る道具の h2_scan で、注記の無い先読み0件） |
| 乱数を使わない | 恒久67番 | 乱数は1つも無い |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| regime_label.py | 版3 の札の式（箱・脚・移る所・行き来）と、版を選ぶ口・自己テスト T12〜T17 | 直す |
| recipes/regime_label.json | 版3 の数字・採点に使う版 | 直す |
| build_regime_label_dashboard.py | 版3 を⑪タブに出す | 直す |
| regime_r9_diag.py | 札に時刻を渡す（_labels_for） | 直す |
| .claude/breaks/b125_hindsight_osc_off.sh | 版3 の「行き来している箱を戻す」を外すと、自己テストが落ちるかを見る | 新設 |
- 触る所＝regime_label.py＝<モジュール直下>・_range_on・_spread・box_stats・hindsight・hindsight_bars・hindsight_range・hindsight_roles・key_bars・keys・labels_at_bars・labels_for_key・legs_of・load_config・local_scale・oscillates・selftest・step_mask・trend_mask・version_tag・zigzag_adaptive／build_regime_label_dashboard.py＝<モジュール直下>・label_frame・main・spec_of／regime_r9_diag.py＝_labels_for。

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. 当てる道具（apply_audit_fix.py --design）で実装の指示を当てます。
2. 当てた直後に、照合（verify_design_contract.py --diff）をかけます。★設計書の SPEC（7-8）は、設計書を作った時点の実物（実装の前のコード）から作られます。この工事は札の部品に関数を足すので、SPEC と実物が食い違う見込みです。食い違ったら、gen_acceptance.py --write で設計書を作り直し、承認の打ち直しを1回 お願いします（教訓 L-655＝工事 B・C と同じ型）。
3. 札の部品の自己テストと、⑪タブの道具（--version hindsight_box）を1回ずつ走らせます。
4. G2 → H2 の順で印を取り直します（札の部品は G2 と H2 の対象・設定ファイルと測る道具は H2 の対象）。
5. ⑪タブの試しの版（label-trial-c24・label-rule-scalp・label-rule-daytrade・label-c24b-scalp・label-c24b-daytrade）を版の一覧から外します（git の対象外の出力）。
6. 成績表を作り直します（前の実測 2時間14分・走らせる前にフロー宣言に時間の見込みを書く）。そのあと M2-F-5 の走行（--stage stage1 --limit 2）で数字が出ることを確かめます。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝実装の後に python3 scripts/priority_rebuild/regime_label.py を引数なしで走らせると、採点に使う版が hindsight_box で、版の名前が label-hind-scalp-5min-b24_daytrade-15min-b40-…（使った値が全部 入る）と出る。測る道具 regime_r9_diag.py の _labels_for は、鍵 scalp と daytrade の2つの札を返し、R9 の3つの割合の列の名前は「③実はトレンド(scalp)」「③実はトレンド(daytrade)」になる。観察の道具の先を見る本数は、役割の保有の上限（スキャル 12本・デイトレ 120本）になる。⑪タブの道具を --version hindsight_box で走らせると、2本の版が出て、レンジだった の本数はスキャル 97,594本・デイトレ 77,535本（⑪タブで まこさんが見た2本と同じ）。そのあと成績表を作り直すと、測る道具の段1（M2-F-8）が役割ごとに10本ずつ上位を残す。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**探す値はありません。**版3 の値は、まこさんが⑪タブで決めた2本の値のままです。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**設定ファイルに版3 の欄を足します。**値動きの大きさ・箱・脚・移る所・行き来・役割（保有の下限と上限・数える足・箱の本数）。採点に使う版を hindsight_box にします。古くなっていた注記2つ（採点に使う版の意味・search_limits に置かない理由）を、いまの事実に直します。
**コマンドの旗を1つ増やします。**⑪タブの道具の --version に hindsight_box を足します。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**①札の部品の自己テストが全部 通る（T12〜T17 を含む）②⑪タブの道具が版3 の2本を出し、レンジだった の本数が⑪タブで見た2本と同じ ③壊すプログラム b125 で T15 が落ちる。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| 設定ファイルに版3 の欄（値動きの大きさ・箱・脚・移る所・行き来・役割）が足りない | 札の部品が読む時点で止まる（LabelError） |
| 測る道具が時刻の無い表で札を呼ぶ | 時刻の列 ts が在れば時刻を付けて渡す。無ければ今までどおり（5分足だけの版の数は変わらない） |
| 成績表の札の版が、いまの設定の札の版と違う | 測る道具が止まる（regime_r9_diag.py の510行・直さない）＝成績表の作り直しが要る |
| 窓の外のバーが混ざる | ⑪タブの道具の load_window が止める（直さない） |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**形が変わるもの。**①札の鍵が、先を見る本数（24・288）から役割の名前（scalp・daytrade）になります。測る道具の列の名前の括弧の中と、成績表の「先を見るバー数」が変わります（成績表は 12・120）。②段ごとに残す上位10本は、役割ごとに10本ずつになります（groups＝worklog 20260928 §51）。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**変えません。**札の部品は何も書きません。⑪タブの版は dashboard/regime_prototype/（git の対象外）です。

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**窓は変えません。**デイトレの札は15分足にまとめて数え、5分足の各バーへ写します。15分足のまとめ方は「左の端の時刻で、左の端を含む」です（案を作る道具が、⑪タブで見た2本と同じになることを確かめた）。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| 札の部品の自己テスト | 2.9秒 | 案を作る道具が、当てた後の札の部品を本物に書かずに走らせた実測 |
| 版3 の札（スキャル・値決め窓の全部） | 0.5秒 | 同上 |
| 版3 の札（デイトレ・値決め窓の全部） | 0.2秒 | 同上 |
| ⑪タブの道具の1版（scalp・札を付け・検査15 を数え・仕様を作る） | 0.6秒 | 同上（版のファイルを書く時間は入らない） |
| ⑪タブの道具の1版（daytrade・札を付け・検査15 を数え・仕様を作る） | 0.3秒 | 同上（版のファイルを書く時間は入らない） |
| 版のファイルを書く | 1版 約2.5秒以下 | 2026-09-28 の走行（worklog 20260928 §34） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**奪い合いに気をつけるもの。**版の一覧 index.json は、⑪タブのほかの版を作る道具も書きます。2つを同時に走らせません。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しの道具だけが書きます。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**札の部品の自己テストは、T12〜T17 の名前を足した1行を出します。⑪タブの道具は今までどおり、版ごとに数えた結果を出します。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **札の部品・設定ファイル・測る道具は H2 の対象、札の部品は G2 の対象です。**実装の後に G2 → H2 を取り直します。
2. **成績表（material_ranking.json）は、作り直すまで古い札のままです。**測る道具は、成績表の札の版が違うと止まります（regime_r9_diag.py の510行）。作り直しは実装の後の走行です。
3. **観察の道具 observe_diag.py は直しません。**札の部品の口を呼ぶだけで、版3 が通ります（案を作る道具が確かめた）。
4. **画面（index.html・app.js）は直しません。**
5. **直すファイルの行の文字を探している壊すプログラムが在ります**（札の部品＝b118・b122、測る道具＝b84・b97・b113〜b117・b123・b124）。この工事は、どれが探す文字も変えません（案を作る道具が、それぞれが探す文字の数を当てる前と後で数えた）。

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| CC の調べの道具（_labelC5・C14・C20・C24・C25_probe.py） | 前の版 label-trial-c24 の式（式を変えずに移した） |
| CC の調べの道具（_labelD_rule_probe.py の qualify・_labelD_c24b_probe.py） | 行き来の数え方と、役割ごとの組み立て |
| 版2 band_hold の口 | 役割ごとの鍵・groups・labels_at_bars の作り |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=88733126c2cfe104 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 20行（<モジュール直下>）
直す前の文字:
~~~
  ・採点に使う版は設定ファイルの「採点に使う版」の1行（既定＝er_median＝いままでと同じ）。

~~~
直した後の文字:
~~~
  ・版3「hindsight_box」＝後から全部 見て作る札（M2-F-6c・まこさん「OK」2026-10-02＝⑪タブの label-c24b-scalp・label-c24b-daytrade）。
      役割ごと（スキャル＝5分足・箱24本／デイトレ＝15分足・箱40本）。①水平な箱に入ったバーをレンジ ②大きくて速い脚を外す
      ③段と段の間の移る所を外す ④箱の中で上下に2回ずつ行き来している所は、②の脚の中でもレンジに戻す。
      式は CC の調べの道具（.claude/state/_labelC5・C14・C20・C24・C25・_labelD_rule・_labelD_c24b_probe.py）から、式を変えずに移した。
      「強さ」の真偽＝レンジだった の否定（全部の行が使える）。「向き」「大きさ」は版1 と同じ式（先の本数＝その役割の保有の上限）。
  ・採点に使う版は設定ファイルの「採点に使う版」の1行（2026-10-02 から hindsight_box＝版3）。

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:20「・採点に使う版は設定ファイルの「採点に使う版」の1行（既定＝er_median＝いままでと同じ）。」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 45行（<モジュール直下>）
直す前の文字:
~~~
TAG_KEYS = {"倍率": "x", "m": "m", "c": "c", "まとめる幅": "mw", "幅の線": "wl", "続く本数": "h"}

~~~
足す文字:
~~~
HINDSIGHT = "hindsight_box"                       # 版3＝後から全部 見て作る札（役割ごと）
FORMULA_VERSIONS = ("er_median", "band_hold", HINDSIGHT)   # 式が在る版
BASE_TF = "5min"                                  # 読む足（5分足）＝版3 の数える足がこれと違えば、まとめて数える

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:45「TAG_KEYS = {"倍率": "x", "m": "m", "c": "c", "まとめる幅": "mw", "幅の線": "wl", "続く本数": "h"}」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 63〜64行（load_config）
直す前の文字:
~~~
    if use not in ("er_median", "band_hold"):
        raise LabelError(f"[札] 採点に使う版 {use} の式が regime_label.py に無い（式が在る版＝er_median・band_hold・fail-closed）")

~~~
直した後の文字:
~~~
    if use not in FORMULA_VERSIONS:
        raise LabelError(f"[札] 採点に使う版 {use} の式が regime_label.py に無い（式が在る版＝{'・'.join(FORMULA_VERSIONS)}・fail-closed）")
    if use == HINDSIGHT:
        for k in ("値動きの大きさ", "箱", "脚", "移る所", "行き来", "役割"):
            if not (vers[HINDSIGHT] or {}).get(k):
                raise LabelError(f"[札] 版 {HINDSIGHT} に「{k}」が無い（fail-closed）")

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:63「if use not in ("er_median", "band_hold"):」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 196行（band_hold）
直す前の文字:
~~~
    return {"強さ": (ok & ~rng, ok), "向き": er["向き"], "大きさ": er["大きさ"]}

~~~
足す文字:
~~~


# ══ 版3＝後から全部 見て作る札（M2-F-6c で まこさんが決めた label-c24b-scalp・label-c24b-daytrade）══════════════
#   まこさん決定（2026-10-02）＝⑪タブの2本を見て「OK」。前の版 label-trial-c24（「確認したけど、視覚的にはほぼOKに見えるので、
#   これでいいよ」）を土台に、9/28 の構造の文「役割ごとに、保有時間の下限と上限、倍率、m、c を持たせます」に合わせて役割ごとにした。
#   式は CC の調べの道具から、式を変えずに移した（工事 D の案を作る道具が、⑪タブの2本と1本ずつ同じかを数えた）。
#   数字は全部 設定ファイルの版 hindsight_box に置く（構造の文＝「数字は全部、設定ファイルに置きます。コードには1つも書きません。」）。
#   ★先を見るのが仕事（答え合わせにだけ使う・判定の条件や入口には入れない）＝先を見る行には H2OK を付ける。乱数は使わない。
def local_scale(win: pd.DataFrame, sc: dict) -> np.ndarray:
    """その時期の値動きの大きさ s＝（n本の最高値 − 最安値）÷ 終値 の、前後 m本の中央値（窓の端は近い値で埋める）。"""
    n = int(sc["幅を測る本数"])
    w = (win["high"].rolling(n).max() - win["low"].rolling(n).min()) / win["close"]
    s = w.rolling(int(sc["中央値を取る本数"]), center=True, min_periods=int(sc["最小の本数"])).median()  # H2OK: 札を作る側＝前後を見て s を決める（評価にだけ使う・判断に入らない）
    return s.bfill().ffill().to_numpy(float)  # H2OK: 同上（窓の頭の欠けを後ろの値で埋める）


def zigzag_adaptive(h: np.ndarray, lo: np.ndarray, theta: np.ndarray) -> list:
    """戻りがその時の theta[i]（割合）以上で向きが変わるジグザグ。戻り＝[(位置, 値, +1 山 / -1 谷)]。"""
    piv = []
    trend = 0
    hi_i, hi_v, lo_i, lo_v = 0, h[0], 0, lo[0]
    for i in range(1, len(h)):
        if h[i] > hi_v:
            hi_i, hi_v = i, h[i]
        if lo[i] < lo_v:
            lo_i, lo_v = i, lo[i]
        th = theta[i]
        if trend >= 0 and lo[i] <= hi_v * (1 - th) and (trend == 1 or hi_i < i):
            if trend == 0 and lo_i < hi_i:
                piv.append((lo_i, lo_v, -1))
            piv.append((hi_i, hi_v, 1))
            trend = -1
            lo_i, lo_v = i, lo[i]
        elif trend <= 0 and h[i] >= lo_v * (1 + th) and (trend == -1 or lo_i < i):
            if trend == 0 and hi_i < lo_i:
                piv.append((hi_i, hi_v, 1))
            piv.append((lo_i, lo_v, -1))
            trend = 1
            hi_i, hi_v = i, h[i]
    piv.append((hi_i, hi_v, 1) if trend == 1 else (lo_i, lo_v, -1))
    return piv


def legs_of(win: pd.DataFrame, s: np.ndarray, a: float, per: int) -> list:
    """ジグザグ（戻り a×s）の脚。戻り＝[(始まり, 終わり, 始値, 終値, 大きさ÷s, 速さ＝大きさ÷（本数÷per）)]。"""
    h = win["high"].to_numpy(float)
    lo = win["low"].to_numpy(float)
    piv = zigzag_adaptive(h, lo, a * s)
    out = []
    for (i0, v0, _), (i1, v1, _) in zip(piv[:-1], piv[1:]):
        if i1 <= i0:
            continue
        amp = abs(v1 - v0) / v0 / s[i0]
        out.append((i0, i1, v0, v1, amp, amp / ((i1 - i0) / float(per))))
    return out


def trend_mask(c: np.ndarray, legs: list, a0: float, v0_: float, f: float) -> np.ndarray:
    """大きさ ≥ a0 かつ 速さ ≥ v0_ の脚を、終値が脚の f〜(1−f) 進んだ所だけ真にする（脚の両端の止まった所は除く）。"""
    m = np.zeros(len(c), bool)
    for i0, i1, v0, v1, amp, spd in legs:
        if amp < a0 or spd < v0_:
            continue
        d = 1.0 if v1 > v0 else -1.0
        p = (c[i0: i1 + 1] - v0) * d / abs(v1 - v0)
        st = np.flatnonzero(p >= f)
        en = np.flatnonzero(p >= 1 - f)
        if len(st) == 0 or len(en) == 0:
            continue
        a_, b_ = i0 + st[0], i0 + en[0]
        if b_ >= a_:
            m[a_: b_ + 1] = True
    return m


def box_stats(win: pd.DataFrame, s: np.ndarray, n_box: int):
    """バー i から n_box 本の箱の高さ（÷終値÷s）と、前半と後半の終値の平均の差（÷箱の幅）。"""
    c = win["close"]
    hh = win["high"][::-1].rolling(n_box).max()[::-1]  # H2OK: 札を作る側＝バーから先 n_box 本の最高値（後ろから数える）
    ll = win["low"][::-1].rolling(n_box).min()[::-1]   # H2OK: 同上（最安値）
    width = (hh - ll)
    h = (width / c).to_numpy() / s
    a = n_box // 2
    m1 = c[::-1].rolling(a).mean()[::-1]               # H2OK: 同上（前半の終値の平均）
    m2 = c[::-1].rolling(n_box - a).mean()[::-1].shift(-a)  # H2OK: 同上（後半の終値の平均）
    d = ((m1 - m2).abs() / width).where(width > 0).to_numpy()
    return np.nan_to_num(h, nan=np.inf), np.nan_to_num(d, nan=np.inf)


def step_mask(win: pd.DataFrame, s: np.ndarray, k: int, x: float) -> np.ndarray:
    """前の k本と後の k本の終値の平均の差 ≥ x×s のバーと、その前後 k÷2 本（段と段の間の移る所）。"""
    c = win["close"]
    before = c.rolling(k).mean()
    after = c[::-1].rolling(k).mean()[::-1]            # H2OK: 札を作る側＝後の k本の平均（後ろから数える）
    mv = ((after - before).abs() / c).to_numpy() / s
    hit = np.nan_to_num(mv, nan=0) >= x
    half = max(k // 2, 1)
    return pd.Series(hit.astype(float)).rolling(2 * half + 1, center=True, min_periods=1).max().to_numpy() > 0  # H2OK: 同上（前後へ広げる）


def oscillates(c: np.ndarray, n_box: int, v: dict) -> np.ndarray:
    """長さ n_box の区間（始まり a）ごとに、終値の帯（区間の最高と最安）の上と下の近く（端の近く×高さ）へ、行ったり来たりの順で
    それぞれ回数の下限以上 入り、前半と後半の終値の平均の差 ≤ 高さ×前後の差の上限、高さ÷平均 ≥ 手数料の床 か。"""
    from numpy.lib.stride_tricks import sliding_window_view
    near, need, shift, floor = float(v["端の近く"]), int(v["回数の下限"]), float(v["前後の差の上限"]), fee_floor()
    w = sliding_window_view(c, n_box)                  # 札を作る側＝区間の中（先を見る＝答え合わせにだけ使う）
    mx, mn = w.max(1), w.min(1)
    hgt = mx - mn
    rows = len(mx)
    prev = np.zeros(rows, np.int8)
    n_top = np.zeros(rows, np.int16)
    n_bot = np.zeros(rows, np.int16)
    hi_th, lo_th = mx - near * hgt, mn + near * hgt
    for j in range(n_box):
        cj = c[j:j + rows]
        code = np.where(cj >= hi_th, 1, np.where(cj <= lo_th, -1, 0)).astype(np.int8)
        new = (code != 0) & (code != prev)
        n_top += new & (code == 1)
        n_bot += new & (code == -1)
        prev = np.where(code != 0, code, prev)
    cs = np.concatenate([[0.0], np.cumsum(c)])
    a = np.arange(rows)
    half = n_box // 2
    m1 = (cs[a + half] - cs[a]) / half
    m2 = (cs[a + n_box] - cs[a + half]) / (n_box - half)
    mean = (cs[a + n_box] - cs[a]) / n_box
    return (n_top >= need) & (n_bot >= need) & (np.abs(m1 - m2) <= shift * hgt) & (hgt / mean >= floor) & (hgt > 0)


def _spread(flag, n_box: int) -> np.ndarray:
    """始まりの印を、その区間の n_box 本 全部へ広げる（バー i は、始まりが i−n_box+1〜i のどれかなら真）。"""
    return pd.Series(np.asarray(flag, float)).rolling(n_box, min_periods=1).max().to_numpy() > 0


def _range_on(win: pd.DataFrame, v: dict, n_box: int) -> np.ndarray:
    """1つの足の上で「レンジだった」を作る。①箱 ②脚を外す ③移る所を外す ④行き来している箱は、脚の中でもレンジに戻す。"""
    c = win["close"].to_numpy(float)
    s = local_scale(win, v["値動きの大きさ"])
    lg, bx, st = v["脚"], v["箱"], v["移る所"]
    tm = trend_mask(c, legs_of(win, s, float(lg["戻り"]), int(lg["速さを測る本数"])),
                    float(lg["大きさの下限"]), float(lg["速さの下限"]), float(lg["端を除く割合"]))
    h, d = box_stats(win, s, n_box)
    ok = (h <= float(bx["高さの上限"])) & (d <= float(bx["前後の差の上限"]))
    stp = step_mask(win, s, int(st["前後の本数"]), float(st["差の下限"]))
    lab = _spread(ok, n_box) & ~tm & ~stp
    q = np.zeros(len(c), bool)
    qq = oscillates(c, n_box, v["行き来"])
    q[:len(qq)] = qq
    return lab | (_spread(ok & q, n_box) & ~stp)


def hindsight_range(win: pd.DataFrame, cfg: dict, role: str) -> pd.Series:
    """版3 の「レンジだった」の真偽（役割ごと）。数える足が5分足でなければ、その足にまとめて数え、5分足の各バーへ写す。"""
    v = cfg["版"][HINDSIGHT]
    rc = v["役割"][role]
    tf, n_box = str(rc["数える足"]), int(rc["箱の本数"])
    if pd.to_timedelta(tf) == pd.to_timedelta(BASE_TF):
        return pd.Series(_range_on(win, v, n_box), index=win.index)
    w2 = pd.DataFrame({"high": win["high"].resample(tf, label="left", closed="left").max(),
                       "low": win["low"].resample(tf, label="left", closed="left").min(),
                       "close": win["close"].resample(tf, label="left", closed="left").last()}).dropna()
    m2 = pd.Series(_range_on(w2, v, n_box), index=w2.index)
    return pd.Series(m2.reindex(win.index.floor(tf)).fillna(False).to_numpy(bool), index=win.index)


def hindsight_roles(cfg=None) -> list:
    cfg = cfg or load_config()
    return list(cfg["版"][HINDSIGHT]["役割"])


def hindsight_bars(cfg, role: str) -> int:
    """版3 の役割の先を見る本数＝保有の上限（向き・大きさの札と、成績表の鍵に使う）。"""
    return int(cfg["版"][HINDSIGHT]["役割"][role]["保有の上限"])


def hindsight(win: pd.DataFrame, cfg: dict, role: str) -> dict:
    """版3 の札（3つの見方の形で返す＝呼ぶ側を変えない）。強さ＝レンジだった の否定（全部の行が使える）。"""
    rng = hindsight_range(win, cfg, role)
    er = er_median(win, hindsight_bars(cfg, role))
    return {"強さ": (~rng, pd.Series(True, index=win.index)), "向き": er["向き"], "大きさ": er["大きさ"]}

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:196「return {"強さ": (ok & ~rng, ok), "向き": er["向き"], "大きさ": er["大きさ"]}」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 201〜203行（keys）
直す前の文字:
~~~
    """採点に使う版の札の鍵＝版1 は先を見る本数（24・288）／版2 は役割（scalp・daytrade）。"""
    cfg = cfg or load_config()
    return list(horizons(cfg)) if cfg["採点に使う版"] == "er_median" else roles(cfg)

~~~
直した後の文字:
~~~
    """採点に使う版の札の鍵＝版1 は先を見る本数（24・288）／版2・版3 は役割（scalp・daytrade）。"""
    cfg = cfg or load_config()
    if cfg["採点に使う版"] == "er_median":
        return list(horizons(cfg))
    return hindsight_roles(cfg) if cfg["採点に使う版"] == HINDSIGHT else roles(cfg)

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:201「"""採点に使う版の札の鍵＝版1 は先を見る本数（24・288）／版2 は役割（scalp・daytrade）。"""」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 209行（key_bars）
直す前の文字:
~~~
    return int(key) if cfg["採点に使う版"] == "er_median" else role_bars(cfg, str(key))

~~~
直した後の文字:
~~~
    if cfg["採点に使う版"] == "er_median":
        return int(key)
    return hindsight_bars(cfg, str(key)) if cfg["採点に使う版"] == HINDSIGHT else role_bars(cfg, str(key))

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:209「return int(key) if cfg["採点に使う版"] == "er_median" else role_bars(cfg, str(key))」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 227〜228行（labels_for_key）
直す前の文字:
~~~
        return er_median(win, int(key))
    return band_hold(win, cfg, str(key))

~~~
直した後の文字:
~~~
        return er_median(win, int(key))
    if cfg["採点に使う版"] == HINDSIGHT:
        return hindsight(win, cfg, str(key))
    return band_hold(win, cfg, str(key))

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:227「return er_median(win, int(key))」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 234〜235行（labels_at_bars）
直す前の文字:
~~~
    cfg = cfg or load_config()
    if cfg["採点に使う版"] == "band_hold":

~~~
直した後の文字:
~~~
    cfg = cfg or load_config()
    if cfg["採点に使う版"] == HINDSIGHT:
        for role in hindsight_roles(cfg):
            if hindsight_bars(cfg, role) == int(n):
                return hindsight(win, cfg, role)
    if cfg["採点に使う版"] == "band_hold":

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:234「cfg = cfg or load_config()」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 253行（version_tag）
直す前の文字:
~~~
        return "label-er" + "-".join(str(x) for x in horizons(cfg)) if role is None else f"label-er{int(role)}"

~~~
足す文字:
~~~
    if ver == HINDSIGHT:
        v = cfg["版"][HINDSIGHT]
        rs = [role] if role else hindsight_roles(cfg)
        common = (f"w{v['値動きの大きさ']['幅を測る本数']}-m{v['値動きの大きさ']['中央値を取る本数']}-h{v['箱']['高さの上限']}"
                  f"-g{v['箱']['前後の差の上限']}-r{v['脚']['戻り']}-a{v['脚']['大きさの下限']}-v{v['脚']['速さの下限']}"
                  f"-k{v['移る所']['前後の本数']}-x{v['移る所']['差の下限']}-q{v['行き来']['端の近く']}")
        return "label-hind-" + "_".join(f"{r}-{v['役割'][r]['数える足']}-b{v['役割'][r]['箱の本数']}" for r in rs) + "-" + common

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:253「return "label-er" + "-".join(str(x) for x in horizons(cfg)) if role is None else f"label-er{int(role)}"」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 392〜393行（selftest）
直す前の文字:
~~~
    print("[regime_label selftest] T1 全部レンジ ／ T2 全部トレンド ／ T3 レンジ8割（版1 の弱点）／ T4 幅の線 ／ "
          "T5 版1 は前の式と同じ ／ T6 呼ぶ側がここを呼ぶ ／ T7 使う値が空なら止まる ／ T8 版の名前・保有の範囲 ／ T9 値の組 ／ T10 続くの確かめ ／ T11 近い山のまとめ方")

~~~
直した後の文字:
~~~
    # ══ 版3（hindsight_box・M2-F-6d の工事 D）＝答えの分かる作り物のチャート ══
    if HINDSIGHT not in (cfg.get("版") or {}):
        ng.append(f"T12: 設定ファイルに版 {HINDSIGHT} が無い")
    else:
        hr = hindsight_roles(cfg)
        # T12 全部レンジ＝役割ごとに、ほぼ全部「レンジだった」
        for role in hr:
            s12 = float(hindsight_range(_synth("range"), cfg, role).mean())
            if not s12 >= 0.95:
                ng.append(f"T12: 全部レンジのデータで、{role} の レンジだった の割合が {s12:.3f}（0.95 以上のはず）")
        # T13 全部トレンド＝1本も「レンジだった」にならない
        for role in hr:
            n13 = int(hindsight_range(_synth("trend"), cfg, role).sum())
            if n13:
                ng.append(f"T13: 全部トレンドのデータで、{role} の レンジだった が {n13} 本 出た（0本のはず）")
        # T14 レンジ8割＝前8割はほぼレンジ・後ろ2割（上げ）はほぼレンジでない
        for role in hr:
            r14 = hindsight_range(d3, cfg, role).to_numpy()
            a14, b14 = float(r14[:k3].mean()), float(r14[k3:].mean())
            if not (a14 >= 0.9 and b14 <= 0.05):
                ng.append(f"T14: レンジ8割のデータで、{role} の前8割 {a14:.3f}（0.9 以上のはず）・後ろ2割 {b14:.3f}（0.05 以下のはず）")
        # T15 階段（observe_diag の答えの分かるニセのデータ＝上げの区間と横ばいの区間を交互）
        #   箱の長さが区間より短い役割＝横ばいはレンジ・上げはレンジでない。長い役割＝その長さの帯が無いので全部 レンジでない。
        #   ★前の版 label-trial-c24 は、スキャルの尺で横ばいのうち 0.208 しかレンジと言えなかった（脚が階段の全体を1本と見た）
        sdf15, st15 = od._synth_regime_bars()
        up = st15.to_numpy()
        inner = ((st15.shift(-12) == st15) & (st15.shift(12) == st15)).fillna(False).to_numpy()  # H2OK: ニセのデータの中だけで完結する検査
        blk_min = int(np.argmax(up != up[0])) * 5            # 区間1つの長さ（分）＝本数 × 5分
        for role in hr:
            rc = cfg["版"][HINDSIGHT]["役割"][role]
            box_min = int(rc["箱の本数"]) * pd.to_timedelta(str(rc["数える足"])).total_seconds() / 60
            r15 = hindsight_range(sdf15, cfg, role).to_numpy()
            f15, u15 = float(r15[inner & ~up].mean()), float(r15[inner & up].mean())
            want = (f15 >= 0.9) if box_min <= blk_min else (f15 <= 0.05)
            if not (want and u15 <= 0.05):
                ng.append(f"T15: 階段のデータで、{role}（箱 {box_min:.0f}分・区間 {blk_min}分）の横ばいのうちレンジ {f15:.3f}・上げのうちレンジ {u15:.3f}"
                          f"（{'横ばい 0.9 以上' if box_min <= blk_min else '横ばい 0.05 以下'}・上げ 0.05 以下のはず）")
        # T16 数字は設定ファイルから読む＝箱の高さの上限を 0 にすると、1本も「レンジだった」にならない
        bad16 = json.loads(json.dumps(cfg))
        bad16["版"][HINDSIGHT]["箱"]["高さの上限"] = 0
        for role in hr:
            if bool(hindsight_range(_synth("range"), bad16, role).any()):
                ng.append(f"T16: 箱の高さの上限を 0 にしても、{role} で レンジだった が出た（設定の数字を読んでいない）")
        # T17 役割の保有の範囲が、組む側の設定（search_limits.json の hold_range_by_role）と同じ
        for role in hr:
            rc = cfg["版"][HINDSIGHT]["役割"][role]
            if role not in sl or (int(rc["保有の下限"]), int(rc["保有の上限"])) != (int(sl[role]["lo_bars"]), int(sl[role]["hi_bars"])):
                ng.append(f"T17: 版3 の役割 {role} の保有の範囲が search_limits.json の hold_range_by_role と違う")
    print("[regime_label selftest] T1 全部レンジ ／ T2 全部トレンド ／ T3 レンジ8割（版1 の弱点）／ T4 幅の線 ／ "
          "T5 版1 は前の式と同じ ／ T6 呼ぶ側がここを呼ぶ ／ T7 使う値が空なら止まる ／ T8 版の名前・保有の範囲 ／ T9 値の組 ／ T10 続くの確かめ ／ T11 近い山のまとめ方"
          " ／ T12〜T16 版3 の作り物のチャート（全部レンジ・全部トレンド・レンジ8割・階段・設定の数字）／ T17 版3 の保有の範囲")

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:392「print("[regime_label selftest] T1 全部レンジ ／ T2 全部トレンド ／ T3 レンジ8割（版1 の弱点）／ T4 幅の線 ／ "」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/recipes/regime_label.json
直す箇所: 4行
直す前の文字:
~~~
 "_search_limits に置かない理由": "search_limits.json は H2 と G2 の印の対象（h2_pass.json・g2_pass.json）＝札の値を変えるたびに H2（約13分）を取り直すことになる。版1 の先を見る本数は、組む側の state_hold_bars_range（保つ上限）と共用だったのを切り離した（値は同じ 24・288）。",

~~~
直した後の文字:
~~~
 "_search_limits に置かない理由": "search_limits.json は H2 と G2 の印の対象（h2_pass.json・g2_pass.json）。★2026-10-02 に確かめた＝この設定ファイル自身も H2 の印の対象（h2_pass.json）に入っている（G2 には入っていない）＝値を変えたら H2 を取り直す。版1 の先を見る本数は、組む側の state_hold_bars_range（保つ上限）と共用だったのを切り離した（値は同じ 24・288）。",

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/regime_label.json:4「"_search_limits に置かない理由": "search_limits.json は H2 と G2 の印の対象（h2_pass.json・g2_pass.json）＝札の値を変えるたびに H2（約13分）を取り直すことになる。版1 の先を見る本数は、組む側の state_hold_bars_range（保つ上限）と共用だったのを切り離した（値は同じ 24・288）。",」
状態: 確定

#### 実装 12
対象のファイル: scripts/priority_rebuild/recipes/regime_label.json
直す箇所: 5行
直す前の文字:
~~~
 "採点に使う版": "er_median",

~~~
直した後の文字:
~~~
 "採点に使う版": "hindsight_box",

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/regime_label.json:5「"採点に使う版": "er_median",」
状態: 確定

#### 実装 13
対象のファイル: scripts/priority_rebuild/recipes/regime_label.json
直す箇所: 6行
直す前の文字:
~~~
 "_採点に使う版の意味": "R9 の3つの割合・順位表・成績表・⑪タブの既定に使う版。er_median＝いままでと同じ。band_hold にするのは、まこさんが⑪タブの目と検査15 で役割ごとの「使う値」を選んでから（空のまま band_hold にすると止まる）。選んだら band_hold にする＝測る道具と成績表が役割ごとの札で両方 測り、段ごとに役割ごとに10本ずつ残す（.claude/state/label_structure_definition_verbatim_20260929.txt の「1. どの役割の札で測るか」）。版1 には役割の札が無いので、版1 のあいだは役割で分けられない。",

~~~
直した後の文字:
~~~
 "_採点に使う版の意味": "R9 の3つの割合・順位表・成績表・⑪タブの既定に使う版。★2026-10-02 から hindsight_box（版3＝M2-F-6c で まこさんが⑪タブで見て「OK」と決めた役割ごとの札 label-c24b-scalp・label-c24b-daytrade）。役割ごとの札で両方 測り、段ごとに役割ごとに10本ずつ残す（worklog 20260928 §51）。er_median に戻すと、いままでの札（先 n本の ER）で測る。band_hold は「使う値」が空のあいだ採点に使えない（2026-10-02 に全体の 0〜9.2% しかレンジと言わず、使えないと分かった）。",

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/regime_label.json:6「"_採点に使う版の意味": "R9 の3つの割合・順位表・成績表・⑪タブの既定に使う版。er_median＝いままでと同じ。band_hold にするのは、まこさんが⑪タブの目と検査15 で役割ごとの「使う値」を選んでから（空のまま band_hold にすると止まる）。選んだら band_hold にする＝測る道具と成績表が役割ごとの札で両方 測り、段ごとに役割ごとに10本ずつ残す（.claude/state/label_structure_definition_verbatim_20260929.txt の「1. どの役割の札で測るか」）。版1 には役割の札が無いので、版1 のあいだは役割で分けられない。",」
状態: 確定

#### 実装 14
対象のファイル: scripts/priority_rebuild/recipes/regime_label.json
直す箇所: 47〜49行
直す前の文字:
~~~
  }
 }
}

~~~
直した後の文字:
~~~
  },
  "hindsight_box": {
   "説明": "後から全部 見て作る札（M2-F-6c・まこさん「OK」2026-10-02＝⑪タブの label-c24b-scalp・label-c24b-daytrade）。役割ごとに1つ。①水平な箱（箱の本数のあいだの高さ ≤ 高さの上限×s・前半と後半の終値の平均の差 ≤ 高さ×前後の差の上限）に入ったバーをレンジ ②ジグザグ（戻り×s）の脚のうち、大きさ ≥ 大きさの下限×s かつ 速さ ≥ 速さの下限 の所を外す ③前と後の終値の平均の差 ≥ 差の下限×s のバーとその前後を外す ④箱の中で、帯の上と下の近く（端の近く×高さ）へ行ったり来たりの順でそれぞれ回数の下限以上 入る所は、②の脚の中でもレンジに戻す。s＝その時期の値動きの大きさ（幅を測る本数の幅 ÷ 終値の、前後の中央値）。先も前も見る（答え合わせにだけ使う）。",
   "_出どころ": "前の版 label-trial-c24（まこさん「確認したけど、視覚的にはほぼOKに見えるので、これでいいよ」）の値をそのまま使い、④を足した（階段の横ばいを②が消していたため）。役割ごとにしたのは 9/28 の構造の文。デイトレの数える足（15分足）と箱の本数（40本＝10時間）と④の値は CC が決めた（worklog 20261002 §20〜§23）。④の幅の下限は手数料の床（e38_logic_parts.SCALP_FLOOR）を読む。",
   "_本数の単位": "どれも、その役割の数える足の本数（スキャル＝5分足・デイトレ＝15分足）。デイトレでは同じ数が3倍の時間になる（例＝速さを測る本数 12＝スキャル1時間・デイトレ3時間）。",
   "値動きの大きさ": {"幅を測る本数": 12, "中央値を取る本数": 288, "最小の本数": 48},
   "箱": {"高さの上限": 1.5, "前後の差の上限": 0.25},
   "脚": {"戻り": 1.0, "大きさの下限": 3.0, "速さの下限": 0.5, "端を除く割合": 0.1, "速さを測る本数": 12},
   "移る所": {"前後の本数": 18, "差の下限": 1.0},
   "行き来": {"端の近く": 0.25, "回数の下限": 2, "前後の差の上限": 0.5},
   "役割": {
    "scalp": {"保有の下限": 1, "保有の上限": 12, "数える足": "5min", "箱の本数": 24},
    "daytrade": {"保有の下限": 12, "保有の上限": 120, "数える足": "15min", "箱の本数": 40}
   }
  }
 }
}

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/regime_label.json:47「}」
状態: 確定

#### 実装 15
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 14行（<モジュール直下>）
直す前の文字:
~~~
       版2 band_hold＝役割ごと × 設定の範囲の両端と真ん中の値の組（regime_label.variants）＝まこさんが目で見て「使う値」を選ぶ

~~~
足す文字:
~~~
       版3 hindsight_box＝役割ごと（後から全部 見て作る札・M2-F-6c で まこさんが⑪タブで見て決めた2本）

~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:14「版2 band_hold＝役割ごと × 設定の範囲の両端と真ん中の値の組（regime_label.variants）＝まこさんが目で見て「使う値」を選ぶ」
状態: 確定

#### 実装 16
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 34行（<モジュール直下>）
直す前の文字:
~~~
  python3 scripts/dashboard/build_regime_label_dashboard.py --version band_hold   （版2 だけ＝役割ごとに、設定の範囲の両端と真ん中の値の組を全部）

~~~
足す文字:
~~~
  python3 scripts/dashboard/build_regime_label_dashboard.py --version hindsight_box   （版3 だけ＝役割ごと）

~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:34「python3 scripts/dashboard/build_regime_label_dashboard.py --version band_hold   （版2 だけ＝役割ごとに、設定の範囲の両端と真ん中の値の組を全部）」
状態: 確定

#### 実装 17
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 93行（label_frame）
直す前の文字:
~~~
    version＝"er_median"（key＝先を見る本数）か "band_hold"（key＝役割・values＝⑪タブに出す値の組）。

~~~
直した後の文字:
~~~
    version＝"er_median"（key＝先を見る本数）か "band_hold"（key＝役割・values＝⑪タブに出す値の組）か "hindsight_box"（key＝役割）。

~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:93「version＝"er_median"（key＝先を見る本数）か "band_hold"（key＝役割・values＝⑪タブに出す値の組）。」
状態: 確定

#### 実装 18
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 98〜99行（label_frame）
直す前の文字:
~~~
    else:
        mask, usable = rl.band_hold(win, cfg, str(key), values)["強さ"]

~~~
直した後の文字:
~~~
    elif version == rl.HINDSIGHT:
        mask, usable = rl.hindsight(win, cfg, str(key))["強さ"]
    else:
        mask, usable = rl.band_hold(win, cfg, str(key), values)["強さ"]

~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:98「else:」
状態: 確定

#### 実装 19
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 107行（label_frame）
直す前の文字:
~~~
    n15 = int(key) if version == "er_median" else rl.role_bars(cfg, str(key), values)

~~~
直した後の文字:
~~~
    if version == "er_median":
        n15 = int(key)
    elif version == rl.HINDSIGHT:
        n15 = rl.hindsight_bars(cfg, str(key))
    else:
        n15 = rl.role_bars(cfg, str(key), values)

~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:107「n15 = int(key) if version == "er_median" else rl.role_bars(cfg, str(key), values)」
状態: 確定

#### 実装 20
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 138〜140行（spec_of）
直す前の文字:
~~~
    else:
        out["役割"] = str(key)
        out["使った値"] = values

~~~
直した後の文字:
~~~
    elif version == rl.HINDSIGHT:
        out["役割"] = str(key)
        out["手数料の床（e38_logic_parts.SCALP_FLOOR）"] = rl.fee_floor()
        out["設定ファイルの中身（この版・そのまま）"] = ver
    else:
        out["役割"] = str(key)
        out["使った値"] = values

~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:138「else:」
状態: 確定

#### 実装 21
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 149行（main）
直す前の文字:
~~~
    ap.add_argument("--version", choices=("all", "er_median", "band_hold"), default="all",

~~~
直した後の文字:
~~~
    ap.add_argument("--version", choices=("all", "er_median", "band_hold", "hindsight_box"), default="all",

~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:149「ap.add_argument("--version", choices=("all", "er_median", "band_hold"), default="all",」
状態: 確定

#### 実装 22
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 165行（main）
直す前の文字:
~~~
        jobs += [("band_hold", role, v) for role in rl.roles(cfg) for v in rl.variants(cfg, role)]

~~~
足す文字:
~~~
    if a.version in ("all", rl.HINDSIGHT):
        jobs += [(rl.HINDSIGHT, role, None) for role in rl.hindsight_roles(cfg)]

~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:165「jobs += [("band_hold", role, v) for role in rl.roles(cfg) for v in rl.variants(cfg, role)]」
状態: 確定

#### 実装 23
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 208行（_labels_for）
直す前の文字:
~~~
    w = df_win[[c for c in ("high", "low", "close") if c in df_win.columns]].astype(float)

~~~
足す文字:
~~~
    if "ts" in df_win.columns:   # ★版3 は役割ごとに足をまとめて数える＝時刻が要る（M2-F-6d の工事 D・5分足だけの版の数は変わらない）
        w.index = pd.DatetimeIndex(pd.to_datetime(df_win["ts"]).to_numpy())

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:208「w = df_win[[c for c in ("high", "low", "close") if c in df_win.columns]].astype(float)」
状態: 確定

#### 実装 24
対象のファイル: .claude/breaks/b125_hindsight_osc_off.sh
直す箇所: 新しいファイル
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 版3（hindsight_box）の「箱の中で上下に2回ずつ行き来している所は、脚の中でもレンジに戻す」を外すと、自己検査 T15 が「階段の横ばい」で落ちた
# EXPECT_MSG: ❌ T15
# b125 — regime_label._range_on の、行き来している箱を戻す所を外すと、T15 が落ちるか（M2-F-6d の工事 D・2026-10-02）
#   守っているもの＝完成の条件 #1（札の部品の自己検査が、版3 が階段の横ばいをレンジと言えるかを見ている）
#   壊し方＝`    return lab | (_spread(ok & q, n_box) & ~stp)` を `    return lab` にする（戻さない＝前の版 label-trial-c24 と同じ）。
#   期待＝regime_label.py --selftest の T15 が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

RL="$PR/regime_label.py"
guard "$RL"

python3 - "$RL" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    return lab | (_spread(ok & q, n_box) & ~stp)\n'
if s.count(old) != 1:
    raise SystemExit("[b125] 壊す対象の行が1か所でない: " + old.strip())
new = '    return lab  # b125 が壊した（行き来している箱を戻さない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$RL" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b125_hindsight_osc_off.sh＝まだ無い（新しく作る）
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
| 1 | 版3 を足し、版1・版2 は消さない | 札の定義を版として持つ（構造の文）。版1 は前の数字と比べるために要る | 版2 を版3 に置き換える。捨てた理由＝版2 を消すかは まこさんが決める |
| 2 | 札の鍵を役割の名前にする | 役割ごとの札で両方 測り、段ごとに役割ごとに10本ずつ残す（worklog 20260928 §51）。版2 と同じ口の作り | 先を見る本数（24・288）のままにする。捨てた理由＝役割が鍵に出ず、役割ごとに残せない |
| 3 | 先を見る本数（向き・大きさの札と成績表の鍵）を、役割の保有の上限（12・120）にする | 版2 と同じ考え（その役割が持つ時間の先を見る） | 版1 の 24・288 を使う。捨てた理由＝役割と結び付かない |
| 4 | 測る道具に、札へ時刻を渡す2行を足す | デイトレの札は15分足にまとめて数えるので、時刻が要る | 札の部品の中で時刻を作る。捨てた理由＝測る道具の表に時刻が無いと作れない |
| 5 | 式は調べの道具から変えずに移す | ⑪タブで まこさんが見た2本と1本ずつ同じにするため | 書き直す。捨てた理由＝見た札と違う札になるおそれ |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=2de1295262235d4a gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b125_hindsight_osc_off.sh` | #1 | 版3 の「行き来している箱を戻す」所を外す（前の版と同じにする）と、T15（階段の横ばい）が落ちる |
| `—` | #2 | 壊すプログラムは付けない（読むための道具＝恒久71番。数は案を作る道具が出した 97,594本・77,535本と照らす） |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 成績表を作り直すまで、測る道具が止まる | 実装・G2・H2 の後すぐに作り直す（時間の見込みをフロー宣言に書く） |
| 2 | 段1 の候補の本数が、役割の数だけ増える | 段ごとに役割ごとに10本ずつ残す作りは工事 B で入っている。時間は M2-F-8 のフロー宣言で見積もる |
| 3 | 版3 の弱い所（2時間で1回 上下する作り物の行き来で、スキャル用が 61% しかレンジと言えない） | 前の版から持ち込んだ性質。まこさんが⑪タブで見て決めた札なので、この工事では変えない |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる | 30秒未満 | 当てる道具は1秒未満で終わった（2026-10-02 の工事 C） |
| 自己テストと⑪タブの道具 | それぞれ1分未満 | 4-14 |
| G2 → H2 | 約30秒 → 約5分 | 2026-10-02 の取り直し（next_step の 0-b-2） |
| まこさんの承認 | 2回（当てる前に1回・当てた後に SPEC を実物から作り直した設計書に1回） | 4-4 の2（教訓 L-655） |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝採点に使う札が、いまも古い札（版1）だからです。まこさんが⑪タブで決めた2本は、手元の調べの道具でしか作れません。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は動きません。動くのは、判定の束に付く点数（3つの割合）と、段ごとに残る10本です。

**③ root か symptom か**＝root です。点数を付ける答えそのものを、まこさんが決めた札にします。

**④ ベースアップ**＝札の式は、まこさんが⑪タブで見た2本の作り方をそのまま移しました。口の作りは、版2（役割ごと）と同じにしました。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。数字は全部 設定ファイルの版3 に置き、値は まこさんが⑪タブで決めた2本の値です。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝役割ごとの札2本を、札の部品の新しい版（版3）にして、採点に使う札にする（14a の工事 D）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。札は答え合わせの答えで、条件をつなぐものではありません |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 値を選びません。値は まこさんが⑪タブで決めた2本の値です |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **版3 の札が正しいか** | この工事では分かりません。まこさんの⑪タブの目で決め、最後は M2-L の net で分かります |
| **札の部品そのものを書き換えられたら** | 書き換えれば無効にできます。承認で凍結され、差分は git に出ます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=b00d5c37190b8ddf gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝5本（札の部品・設定ファイル・⑪タブの道具・測る道具・壊すプログラム b125）を【7-8】に書いた。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝regime_label.py）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム b125 の1本（NEW_FILE）。手本は同じ札の部品の壊すプログラム b118（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝前の版 label-trial-c24 は1種類だけで、9/28 に決めた役割ごとの構造に合っていなかった。この工事は役割ごとの2本を入れる。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 新しい部品は版3 の関数（local_scale ほか）。式は調べの道具から変えずに移した。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 直すファイルの行番号を指す文書は、この工事の実装の指示だけで、いまの実物から道具が作った。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、それぞれが探す行の文字の数が、この工事の前と後で同じことを案を作る道具が数えた（4-13 の5・照らした組は案の冒頭）。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムは b125 を1本 作る（版3 の行き来で戻す所を外すと T15 が落ちる＝案を作る道具が同じ壊し方で確かめた）。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 触る関数は、全部 DESIGN_CONTRACT の impl_functions に書いた（【7-8】・案を作る道具が当てる前と後の差の行から数えた）。regime_label.py＝<モジュール直下>・_range_on・_spread・box_stats・hindsight・hindsight_bars・hindsight_range・hindsight_roles・key_bars・keys・labels_at_bars・labels_for_key・legs_of・load_config・local_scale・oscillates・selftest・step_mask・trend_mask・version_tag・zigzag_adaptive／build_regime_label_dashboard.py＝<モジュール直下>・label_frame・main・spec_of／regime_r9_diag.py＝_labels_for。must_use に、版3 の組み立ての関数が呼ぶ名前を書いた。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足す旗は⑪タブの道具の --version hindsight_box（4-9）。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2f-label-hindsight-20261002）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己テスト＝札の部品に T12〜T17 を足した。案を作る道具が当てた後の札の部品を本物に書かずに走らせ、全部 通った。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 札の部品の自己テストが全部 通る（版3 の T12〜T17 を含む） | `python3 scripts/priority_rebuild/regime_label.py --selftest` | 実経路 | 版3 の「行き来している箱を戻す」所を外す（前の版と同じにする）と、T15（階段の横ばい）が落ちる | `b125_hindsight_osc_off.sh` | — | **未着手** |
| 2 | ⑪タブの道具が版3 の2本を出し、レンジだった の本数が⑪タブで見た2本と同じ | `python3 scripts/dashboard/build_regime_label_dashboard.py --version hindsight_box` | 実経路 | 壊すプログラムは付けない（読むための道具＝恒久71番。数は案を作る道具が出した 97,594本・77,535本と照らす） | `—` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=1faa19ed43d8ad8c gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/regime_label.py`

| 触る関数 | 定義の行 |
|---|---|
| `hindsight_range` | （この関数は実物に無い） |
| `hindsight` | （この関数は実物に無い） |
| `oscillates` | （この関数は実物に無い） |
| `local_scale` | （この関数は実物に無い） |
| `box_stats` | （この関数は実物に無い） |
| `step_mask` | （この関数は実物に無い） |
| `trend_mask` | （この関数は実物に無い） |
| `legs_of` | （この関数は実物に無い） |
| `zigzag_adaptive` | （この関数は実物に無い） |
| `hindsight_roles` | （この関数は実物に無い） |
| `hindsight_bars` | （この関数は実物に無い） |
| `_range_on` | （この関数は実物に無い） |
| `_spread` | （この関数は実物に無い） |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 22件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=43c42a4843abdbd0 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/regime_label.py",
  "_impl_file の意味": "照らす相手は実在するファイル（gen_acceptance.py:680〜683）。札の式が在る札の部品を主に照らす。",
  "impl_functions": {
    "scripts/priority_rebuild/regime_label.py": [
      "<モジュール直下>",
      "_range_on",
      "_spread",
      "box_stats",
      "hindsight",
      "hindsight_bars",
      "hindsight_range",
      "hindsight_roles",
      "key_bars",
      "keys",
      "labels_at_bars",
      "labels_for_key",
      "legs_of",
      "load_config",
      "local_scale",
      "oscillates",
      "selftest",
      "step_mask",
      "trend_mask",
      "version_tag",
      "zigzag_adaptive"
    ],
    "scripts/dashboard/build_regime_label_dashboard.py": [
      "<モジュール直下>",
      "label_frame",
      "main",
      "spec_of"
    ],
    "scripts/priority_rebuild/regime_r9_diag.py": [
      "_labels_for"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数。当てる前と後の差の行を、当てた後のコードの関数に当てはめて、案を作る道具（_labelD_draft_build.py）が数えた。",
  "self_check_calls": [
    "hindsight_range",
    "hindsight",
    "oscillates",
    "local_scale",
    "box_stats",
    "step_mask",
    "trend_mask",
    "legs_of",
    "zigzag_adaptive",
    "hindsight_roles",
    "hindsight_bars",
    "_range_on",
    "_spread"
  ],
  "_self_check_calls の意味": "実装の後の札の部品に在るはずの、版3 の関数の名前。★ファイル名を書かない＝7-7 の表が「読んだ」の行の下に並べ、必読ゲートが数えるため。",
  "must_use": {
    "_range_on": [
      "local_scale",
      "trend_mask",
      "legs_of",
      "box_stats",
      "step_mask",
      "oscillates",
      "_spread"
    ],
    "hindsight_range": [
      "_range_on"
    ],
    "hindsight": [
      "hindsight_range",
      "er_median",
      "hindsight_bars"
    ],
    "oscillates": [
      "fee_floor"
    ]
  },
  "_must_use の意味": "版3 の組み立ての関数が呼ぶはずの名前（案を作る道具が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は札の式と版を選ぶ口を足すだけ。外から読む一覧（候補・法則・成績表の順位・範囲の鍵）は読まない。",
  "generated_from": {
    "impl_functions": "当てる前と後の差の行（_labelD_draft_build.py が数えた）",
    "must_use": "版3 の組み立ての関数が呼ぶ名前（ast で照らした）",
    "spec_lists": "空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/regime_label.py",
 "public_functions": {
  "LabelError": [],
  "load_config": [
   "LabelError"
  ],
  "fee_floor": [],
  "horizons": [
   "load_config"
  ],
  "roles": [
   "load_config"
  ],
  "role_bars": [],
  "er_median": [],
  "band_range": [],
  "band_hold": [
   "LabelError",
   "band_range",
   "er_median",
   "fee_floor",
   "role_bars"
  ],
  "keys": [
   "horizons",
   "load_config",
   "roles"
  ],
  "key_bars": [
   "load_config",
   "role_bars"
  ],
  "key_label": [
   "load_config"
  ],
  "groups": [
   "key_label",
   "keys",
   "load_config"
  ],
  "labels_for_key": [
   "band_hold",
   "er_median",
   "load_config"
  ],
  "labels_at_bars": [
   "band_hold",
   "er_median",
   "load_config",
   "role_bars",
   "roles"
  ],
  "bars_keys": [
   "key_bars",
   "keys",
   "load_config"
  ],
  "version_tag": [
   "LabelError",
   "horizons",
   "load_config",
   "roles"
  ],
  "spec": [
   "load_config"
  ],
  "variants": [],
  "selftest": [
   "band_range",
   "er_median",
   "fee_floor",
   "load_config",
   "roles",
   "variants",
   "version_tag"
  ]
 },
 "constants": {},
 "cli_flags": [
  "--selftest"
 ]
}
```

<!-- ACC_SPEC_END -->

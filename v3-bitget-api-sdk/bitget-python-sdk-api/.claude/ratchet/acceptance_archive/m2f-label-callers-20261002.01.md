<!-- ARC iter="m2f-label-callers-20261002" -->

# 設計書｜観察の道具と測る道具を、札の部品 regime_label.py を呼ぶ形に切り替え、札の版の名前を順位表・落ちた候補・成績表に書く＝14a の工事 B

TARGET: scripts/priority_rebuild/regime_r9_diag.py, scripts/priority_rebuild/observe_diag.py, scripts/priority_rebuild/regime_label.py
NEW_FILE: .claude/breaks/b122_obs_formula_copied.sh, .claude/breaks/b123_label_tag_dropped.sh, .claude/breaks/b124_role_keep_off.sh
MODEL: .claude/breaks/b118_band_continue_off.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2f-label-callers-20261002/ok_labelB_20261002`・`m2f-label-callers-20261002/ok_split_20261002`・`m2f-label-callers-20261002/ok_t6_20261002`・`m2f-label-callers-20261002/ok_todo_20261001`・`m2f-label-callers-20261002/okd_labelB_20261002`・`m2f-label-callers-20261002/req_6d_20260928`・`m2f-label-callers-20261002/req_split_20261001`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2f-label-callers-20261002/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2f-label-callers-20261002 --write`。検出＝`--work m2f-label-callers-20261002 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=3974a648fefb7100 gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2f-label-callers-20261002/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2f-label-callers-20261002/ok_labelB_20261002.txt`（まこさんの発言）・`verbatim/m2f-label-callers-20261002/ok_split_20261002.txt`（まこさんの発言）・`verbatim/m2f-label-callers-20261002/ok_t6_20261002.txt`（まこさんの発言）・`verbatim/m2f-label-callers-20261002/ok_todo_20261001.txt`（まこさんの発言）・`verbatim/m2f-label-callers-20261002/okd_labelB_20261002.txt`（まこさんが OK した CC の文）・`verbatim/m2f-label-callers-20261002/req_6d_20260928.txt`（まこさんの発言）・`verbatim/m2f-label-callers-20261002/req_split_20261001.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝607 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_labelB_20261002` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_split_20261002` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_t6_20261002` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_todo_20261001` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_labelB_20261002` | V01〜V09（9 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_labelB_20261002` | V10〜V15（6 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V16〜V18（3 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V19〜V22（4 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V23〜V34（12 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V35〜V41（7 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V42〜V49（8 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V50〜V59（10 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V60〜V61（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V62〜V63（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V64〜V66（3 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V67〜V68（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V69〜V70（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V71〜V72（2 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V73〜V78（6 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V79〜V86（8 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V87〜V88（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V89〜V90（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V91〜V92（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V93〜V98（6 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V99〜V403（305 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V404〜V412（9 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V413〜V418（6 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V419〜V424（6 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V425〜V431（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V432〜V433（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V434〜V435（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V436〜V440（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V441〜V451（11 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V452〜V472（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V473〜V479（7 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V480〜V551（72 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_labelB_20261002` | V552〜V555（4 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `req_6d_20260928` | V01〜V46（46 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `req_split_20261001` | V01〜V02（2 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
M2 は、4つの場面（レンジ・上げ・下げ・スパイク）の判定を、全部の戦略のために組む段です。組んだ判定の良し悪しは、答え合わせに使う札（そのバーが後から見て実際にレンジだったかの答え）と照らして測ります。工事 A で、札を作る部品 regime_label.py と設定 recipes/regime_label.json を作りました。しかし、観察の道具（observe_diag.py の _regime_labels）と測る道具（regime_r9_diag.py の _labels_for）は、まだ自分の式と search_limits.json の本数で札を作っています。札を直しても、片方だけが変わる形のままです。この工事 B は、2つの道具を部品を呼ぶ形に切り替え、どの版の札で作ったかを順位表・落ちた候補・成績表に書き、役割ごとの札のときは役割ごとに上位を残すようにします。採点に使う版は er_median のままなので、札・順位表・成績表の数字は変わりません。⑪タブは工事 C です。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 観察の道具の中に、札の式がまだ在る | `grep -c -F 'er.median()' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は当たる行が在る。実装の後は当たる行が無い（式は部品の中だけ） | 1（終了コード 0） |
| 測る道具が、札を部品から受け取っていない | `grep -c -F 'import regime_label as rl' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py` | 実装の前は当たる行が無い。実装の後は当たる行が在る | 0（終了コード 1） |
| 順位表に札の版を書く所が無い | `grep -c -F '札の版=tag_l' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py` | 実装の前は当たる行が無い。実装の後は、順位表と落ちた候補に書く行に当たる | 0（終了コード 1） |

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
| 1 | ⑪タブの道具 build_regime_label_dashboard.py を部品に切り替えること（9/29 の控えの実装の指示 23〜27） | 工事 C でやる | ok_split_20261002 |
| 2 | 役割ごとの札（band_hold）のときの差し戻し（--sweep）を作ること | 差し戻しは「良くなったか」を1つの並べる鍵で比べる。役割ごとの札のとき、どの役割の鍵で比べるかは、まだどの文書にも決まっていない（§51 の1 は段ごとに残す本数だけ）。役割の列を黙って混ぜて比べないよう、band_hold のときは止まる形にし、採点に使う版を切り替えるときに作る | worklog 20260928 §51 の1 |
| 3 | 版2 の使う値を選ぶこと・採点に使う版を band_hold に切り替えること | 使う値は まこさんが⑪タブの目と検査15 で選ぶ。選ぶまでは版1 のまま | req_6d_20260928（「この3つの中でどれを使うかは、⑪タブで まこさんが見ることと、検査15 の片道の度合いで決めます。私は選びません。」） |
| 4 | 上げ・下げ・スパイクの札を作ること | 範囲は M2-M-1 で まこさんが決める | worklog 20260928 §51 の4 |
| 5 | 観察の道具の中で _regime_labels と _regime_horizons を呼んでいる8か所を直すこと | 呼ぶ名前と戻りの形を変えないので、8か所は直さずに部品を通る | observe_diag.py の中の呼び出し（git grep で数えた8か所） |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 成績表 material_ranking.json を、この工事で作り直すか | 作り直さない。採点に使う版は er_median のままで、成績表の数字は変わらない。いまの成績表には札の版の欄が無いが、需給を足す口は「欄が無い成績表は版1（er_median）で作った物」と読む。作り直しは前の実測で約2時間14分かかるので、採点に使う版を切り替えるときに作り直す | m2_todo.json の M2-F-6d の注意（作り直しは前の実測で 2時間14分）・worklog 20260928 §51 の2 |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、答え合わせに使う正解ラベル（札）を作る場所を、工事 A で作った部品 regime_label.py の1か所にするものです。**14a を3つに分けた2つ目の工事です（まこさん「よい」2026-10-02）。
**①いま何が起きているか。**観察の道具（observe_diag.py の _regime_labels）は、札の式をまだ自分の中に持ち、先を見る本数（24・288）を search_limits.json から読みます。測る道具（regime_r9_diag.py の _labels_for）は、観察の道具の式を呼びます。工事 A で作った部品は、まだ誰も呼びません。だから札を直しても、片方だけが変わる形のままです。順位表・落ちた候補・成績表には、どの版の札で作ったかが書かれません。
**②この工事で何が変わるか。**観察の道具の _regime_labels と _regime_horizons は、部品を呼ぶだけの形になり、式と search_limits.json の本数を消します。測る道具の _labels_for も部品を呼びます。順位表と落ちた候補の各行と、成績表の書き出しに、札の版の名前を書きます。
**役割ごとの札のとき。**採点に使う版が役割を持つとき（band_hold）は、列の名前の括弧の中を役割の名前にし、段ごとに役割ごとに上位 keep 本ずつ残します。札の部品の自己検査に T6（呼ぶ側が部品を呼び、式を書き写していないか）を足します。
**③数字は変わりません。**採点に使う版は er_median のままなので、札・順位表・成績表の数字は、直す前と同じです。M2-F-5 の走行で、144回目と同じ3つの割合が出ることを確かめます。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、札の部品・測る道具・観察の道具の自己検査と、M2-F-5 の走行を走らせます。段の走行（M2-F-8〜15）と成績表の作り直しは、この工事の後に、時間の見込みをフロー宣言に書いてから走らせます。
**誰が結果を使うか。**順位表と落ちた候補は、次の段の走行（--top・--sweep）と、まこさんの見比べが使います。成績表は、組む側 engine_tuner_gen.py が材料を並べるのに使います（札の版の欄は読みません）。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**呼ぶ側が部品に渡すもの。**値決め窓の5分足（高値・安値・終値のうち在る列）と、鍵（版1＝先を見る本数・版2＝役割の名前）。
**呼ぶ側が部品から受け取るもの。**3つの見方（強さ・向き・大きさ）ごとに、バーごとの真偽と「その行が使えるか」。形は直す前の _regime_labels と同じです。
**書き出しに足すもの。**順位表と落ちた候補の各行の「札の版」（例＝label-er24-288）。成績表の「札の版」。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 札を作る場所を1つにする | まこさん決定 2026-09-28（構造の文の2つ目） | 観察の道具と測る道具は部品を呼ぶだけにする。T6 が、呼んでいるか・式（median）を持っていないかを見る |
| どの版の札で作った成績表かを、成績表の側に残す | まこさん決定 2026-09-28（構造の文の3つ目） | 順位表・落ちた候補の各行と、成績表に札の版の名前を書く。⑬が見る |
| 測る道具と成績表は、役割ごとの札の両方で測り、段ごとに役割ごとに上位を残す | まこさん OK 2026-09-28（worklog 20260928 §51 の1） | 列の名前の括弧の中を役割にし、rank_rows が役割ごとに keep 本ずつ残す。⑫が見る |
| 数字は全部 設定ファイルに置く | まこさん決定 2026-09-28（構造の文） | 先を見る本数は部品（regime_label.json）から読む。観察の道具の search_limits.json を読む行を消す |
| 札は評価にだけ使う（判定の条件・入口に入れない） | word_replacements の「正解ラベル」の行 | 札を呼ぶのは、成績表を作る所と測る道具の答え合わせだけ（呼ぶ所は変えない） |
| 乱数を使わない | 恒久67番 | 乱数を足さない。測る道具の自己検査⑦が見る |
| 値を選ぶのは、⑪タブの まこさんの目と検査15。CC は選ばない | req_6d_20260928 | 採点に使う版は er_median のまま。使う値は空のまま |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| regime_r9_diag.py | 札を部品から受け取る（_labels_for）・列の名前を札の鍵にする（measure）・役割ごとに並べて残す（rank_key・rank_rows）・札の版を書く（write_outputs）・band_hold の差し戻しは止める（run_sweep）・自己検査⑤⑫⑬ | 直す |
| observe_diag.py | 先を見る本数と札を部品から読む（_regime_horizons・_regime_labels）・成績表に札の版を書く（_insp_regime_rank・add_demand_to_ranking） | 直す |
| regime_label.py | 自己検査 T6（呼ぶ側が部品を呼び、式を書き写していないか）・説明の文 | 直す |
| .claude/breaks/b122_obs_formula_copied.sh | 観察の道具の _regime_labels に札の式を書き写すと T6 が落ちるかを試す | **新設** |
| .claude/breaks/b123_label_tag_dropped.sh | 順位表に札の版を書かないと⑬が落ちるかを試す | **新設** |
| .claude/breaks/b124_role_keep_off.sh | 役割ごとに残す判定を外すと⑫が落ちるかを試す | **新設** |
- 触る所（regime_r9_diag.py）＝<モジュール直下>・_labels_for・main・measure・rank_key・rank_rows・run_stage・run_sweep・selftest・write_outputs。
- 触る所（observe_diag.py）＝<モジュール直下>・_insp_regime_rank・_regime_horizons・_regime_labels・add_demand_to_ranking。
- 触る所（regime_label.py）＝<モジュール直下>・selftest。

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. 当てる道具（apply_audit_fix.py --design）で実装の指示を当てます（測る道具・観察の道具・札の部品と、新しい壊すプログラム3本）。
2. 札の部品の自己検査（regime_label.py --selftest）と、測る道具の自己検査（regime_r9_diag.py --selftest）を走らせます。★走らせる前に時間の見込みをフロー宣言に書きます（恒久60〜62番）。
3. 壊すプログラム b122〜b124 を測ります（run_breaks.py --measure-only）。
4. 観察の道具と札の部品は H2 の印の対象なので、commit の後に照合（verify_design_contract.py --diff）をかけ、G2 → H2 の順に取り直します。
5. M2-F-5 の走行（regime_r9_diag.py --stage stage1 --limit 2 --purpose check）で、144回目と同じ3つの割合が出ることと、順位表と落ちた候補の各行に札の版が在ることを見ます。
6. 実装を監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝採点に使う版が er_median のとき、測る道具の --stage stage1 --limit 2 --purpose check は、札を部品から受け取る（鍵＝24 と 288・列の名前＝「先24本」「先288本」でいままでと同じ）。そして144回目と同じ3つの割合（1位 stage1_0 の①18.53%・③(先24本)=49.6%）を出し、順位表と落ちた候補の各行に「札の版」＝label-er24-288 を書く。採点に使う版が band_hold のときは、鍵が役割の名前（scalp・daytrade）になり、列は「③実はトレンド(scalp)」の形になり、段ごとに役割ごとに上位 keep 本ずつ残す（片方の役割で1位の束は、もう片方で最下位でも残る＝自己検査⑫）。観察の道具の _regime_labels に札の式を書き写すと、札の部品の自己検査 T6 が落ちる（壊すプログラム b122）。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**探す値はありません。**この工事は札の呼び方と書き出しだけを変え、値を選びません。版2 の6つの値の範囲は、工事 A の設定 regime_label.json の「範囲」の欄のままです。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**新しい設定はありません。**札の版と鍵は、工事 A の設定 recipes/regime_label.json の「採点に使う版」の1行で決まります。
**コマンドの旗は変えません。**

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに画面に出るもの。**①regime_label.py --selftest の T1〜T11 の行（T6 を含む）と「全部 pass」。②regime_r9_diag.py --selftest の印字に ⑫役割ごとに keep 本ずつ残す・⑬札の版をファイルに書く が出て「全部 pass」。③M2-F-5 の走行の印字が、144回目と同じ3つの割合を出し、順位表と落ちた候補の各行に「札の版」: "label-er24-288" が在る。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| 札の設定ファイルが無い・採点に使う版が式の無い名前 | 札の部品が読む時点で止まる（LabelError） |
| 採点に使う版が band_hold で、差し戻し（--sweep）を走らせた | 止まる（役割の列を混ぜて比べない・fail-closed） |
| 成績表に札の版が在り、いまの設定の札の版と違うまま需給を足そうとした | 止まる（違う札の順位を1つの表に混ぜない・fail-closed） |
| 札の版の欄が無い成績表に需給を足す | 版1（er_median）で作った物として読む（版を持つ前に作った成績表） |
| 観察の道具の中に札の式が書き写された | 札の部品の自己検査 T6 が落ちる |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**形が変わるもの。**①順位表と落ちた候補の各行に「札の版」の欄が足されます。②成績表 material_ranking.json に「札の版」の欄が足されます（次に作り直したとき）。③採点に使う版が band_hold のときだけ、列の名前の括弧の中が役割の名前になり（例＝「③実はトレンド(scalp)」）、行に「順位(役割)」が足されます。er_median のときの列の名前は直す前と同じです（「③実はトレンド(先24本)」）。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**変えません。**順位表と落ちた候補は results/priority_rebuild/regime_r9/、成績表は .claude/ratchet/material_ranking.json です。

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**窓は変えません。**札を作るのは値決め窓だけです（測る道具は窓の中だけを渡し、成績表は _assert_search_window_only が止めます）。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| regime_label.py --selftest | 約5秒 | 2026-10-02 の実測 4.468秒（T6 は observe_diag.py と regime_r9_diag.py を構文の木として読むだけ） |
| regime_r9_diag.py --selftest | 測っていない | ★走らせる前に、worklog から過去の実測を探し、無ければ小さく測ってから走らせる（恒久61・62番） |
| M2-F-5 の走行 | 測っていない | 144回目は 6.2秒（前に作った物を再利用した）。コードが変わると作り直しになるかを、走らせる前に確かめる（恒久61・62番） |
| G2 の取り直し | 約30秒 | 2026-10-02 の実測 29.0秒 |
| H2 の取り直し | 約5分 | 2026-10-02 の実測 5分0秒 |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**奪い合いに気をつけるもの。**順位表と落ちた候補は時刻の付いた名前で書き、同じ名前が在れば上書きせずに止まります。H2 と G2 の印は、取り直しを2つ同時に走らせません。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**書き換えられては困る記録。**観察の道具と札の部品は H2 の印の対象です。書き替えたら H2 を取り直すまで engine_tuner が走りません。人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**自己検査の各行と「全部 pass」か ❌ の行。成績表を作るときの「先を見るバー数」の行に、出どころ（regime_label.json の採点に使う版）と札の版の名前を出します。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **観察の道具と札の部品は、H2 の印の対象です。**直した後は、H2 を取り直すまで engine_tuner が走りません（4-4 の手順4）。
2. **観察の道具の中で、_regime_labels と _regime_horizons を呼ぶ所が8か所在ります。**呼ぶ名前と戻りの形を変えないので、8か所は直さずに部品を通ります（er_median のとき、答えは直す前と同じ）。
3. **⑪タブの道具（build_regime_label_dashboard.py）は、まだ観察の道具の _regime_labels を呼びます。**部品を通るので答えは同じです。⑪タブの版の名前と仕様は工事 C で直します。
4. **工事 B で直す行の文字を探している既存の壊すプログラムは0本でした**（.claude/breaks/*.sh を、直す行の文字で grep した・相手のファイルの名前で探して、その壊す行も見た）。
5. **壊すプログラムの番号 b119〜b121 は、9/30 の道具の工事が使っていました。**工事 B の3本は b122〜b124 にしました。next_step と工事 A のやることの表に書いた「b119〜b121」は、承認の後に b122〜b124 に揃えます。

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| 9/29 の控えの実装の指示 1〜21・31〜33 | 実装の指示の中身（道具で取り出した） |
| 9/29 の控えの実装の指示 28 の T6 の塊 | 札の部品の自己検査 T6（道具で取り出した） |
| b118_band_continue_off.sh | 壊すプログラムの形（壊す対象が1か所でなければ止まる） |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=cd67351d00cf2e7f gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 11〜14行（<モジュール直下>）
直す前の文字:
~~~
  ③ 実はトレンドだった割合       ＝ 判定が真のバーのうち、observe_diag._regime_labels の「強さ」（先 n本の ER が窓の
                                   中央値以上）が真の割合。先読み n は成績表と同じ2つ（_regime_horizons）
  ＋当たった割合（1−③）・捉えた割合（正解がレンジのうち判定が真・正解0本なら nan）・正解レンジの割合（≈50%）を出し、
    第一キー＝③の2つの先読みの平均の低さ・第二キー＝捉えた割合の平均の高さで並べる（まこさん決定 2026-09-27「１は平均でOK」）。
~~~
直した後の文字:
~~~
  ③ 実はトレンドだった割合       ＝ 判定が真のバーのうち、答え合わせに使う正解ラベル（札）の「強さ」が真の割合。
                                   札を作る場所は regime_label.py の1か所（M2-F-6d）。版と鍵は recipes/regime_label.json の
                                   「採点に使う版」（版1 er_median＝先 n本の ER が窓の中央値以上・n は 24 と 288／版2 band_hold＝役割ごと）
  ＋当たった割合（1−③）・捉えた割合（正解がレンジのうち判定が真・正解0本なら nan）・正解レンジの割合を出し、
    第一キー＝③の平均の低さ・第二キー＝捉えた割合の平均の高さで並べる（まこさん決定 2026-09-27「１は平均でOK」）。
    版2 のときは役割ごとに並べ、役割ごとに上位を残す（M2-F-6d・worklog 20260928 §51 の1）。
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:11「  ③ 実はトレンドだった割合       ＝ 判定が真のバーのうち、observe_diag._regime_labels の「強さ」（先 n本の ER が窓の」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 49行（<モジュール直下>）
直す前の文字:
~~~
import score                            # noqa: E402  審判（改造しない・import して呼ぶだけ）
~~~
足す文字:
~~~

import regime_label as rl               # noqa: E402  答え合わせに使う正解ラベル（札）を作る、ただ1つの場所（M2-F-6d）
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:49「import score                            # noqa: E402  審判（改造しない・import して呼ぶだけ）」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 94〜104行（rank_key）
直す前の文字:
~~~
def rank_key(r: dict) -> tuple:
    """並べる鍵＝第一キー：③（実はトレンド）の2つの先読みの平均の低さ／第二キー：捉えた割合の平均の高さ。

    ★まこさん決定 2026-09-27（逐語「１は平均でOK」）＝先24本と先288本の平均で順位をつける。
    ★nan は最後（測れない束を上位に出さない）。
    """
    _t3s = [v for k, v in r.items() if k.startswith("③")]
    # ★先読みの片方でも nan なら平均を取らない（1つだけの数字で並べない＝測れない束と同じく最後・監査 CP48）
    t3 = _nanmean(_t3s) if _t3s and all(v == v for v in _t3s) else float("nan")
    ct = _nanmean([v for k, v in r.items() if k.startswith("捉えた")])
    return (t3 if t3 == t3 else float("inf"), -(ct if ct == ct else float("-inf")))
~~~
直した後の文字:
~~~
def rank_key(r: dict, group: str | None = None) -> tuple:
    """並べる鍵＝第一キー：③（実はトレンド）の平均の低さ／第二キー：捉えた割合の平均の高さ。

    ★まこさん決定 2026-09-27（逐語「１は平均でOK」）＝先24本と先288本の平均で順位をつける（札の版が er_median のとき）。
    ★group（札の役割の名前・M2-F-6d）を渡したら、その役割の札の列だけで鍵を作る（列の名前の末尾が「(役割)」）。
    ★nan は最後（測れない束を上位に出さない）。
    """
    _t3s = [v for k, v in r.items() if k.startswith("③") and (group is None or k.endswith(f"({group})"))]
    # ★先読みの片方でも nan なら平均を取らない（1つだけの数字で並べない＝測れない束と同じく最後・監査 CP48）
    t3 = _nanmean(_t3s) if _t3s and all(v == v for v in _t3s) else float("nan")
    ct = _nanmean([v for k, v in r.items() if k.startswith("捉えた") and (group is None or k.endswith(f"({group})"))])
    return (t3 if t3 == t3 else float("inf"), -(ct if ct == ct else float("-inf")))
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:94「def rank_key(r: dict) -> tuple:」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 107〜127行（rank_rows）
直す前の文字:
~~~
def rank_rows(rows: list[dict], keep: int | None = None) -> tuple[list[dict], list[dict]]:
    """行を並べて順位を書き込む。keep より下は場面「成績下位」を付ける（行は消さない＝§2.2）。

    戻り＝(並べた行, 成績下位の落ちた候補)。測れない行（①が無い行）は最後に置く。
    """
    ok = [r for r in rows if "①時間の割合" in r]
    ng = [r for r in rows if "①時間の割合" not in r]
    ok.sort(key=rank_key)
    dropped = []
    k = 0
    for i, r in enumerate(ok, start=1):
        r["順位"] = i
        # ★比べる相手（RG-v5）は順位だけ付け、上位の枠（keep）を使わない・落ちた候補に数えない（束ではないため・監査 CP48）
        if str(r.get("判定", "")).startswith("RG-v5"):
            r["比べる相手"] = True
            continue
        k += 1
        if keep is not None and k > keep:
            r["dropped_by"] = "成績下位"
            dropped.append({"場面": "成績下位", "判定": r.get("判定"), "順位": i})
    return ok + ng, dropped
~~~
直した後の文字:
~~~
def rank_rows(rows: list[dict], keep: int | None = None,
              groups: list | None = None) -> tuple[list[dict], list[dict]]:
    """行を並べて順位を書き込む。keep より下は場面「成績下位」を付ける（行は消さない＝§2.2）。

    groups（札の役割の名前の並び＝regime_label.groups()・M2-F-6d）を渡したら、役割ごとに並べて「順位(役割)」を書き、
    役割ごとに keep 本ずつ残す（まこさん OK 2026-09-28「上記でOKなので、再度todo作成して、修正を進めて」＝
    worklog 20260928 §51 の1）。どれかの役割で keep の内に入った行は残る。全体の「順位」＝役割ごとの順位のうち最も良いもの。
    groups が None なら、いままでと同じ（1つの並び）。
    戻り＝(並べた行, 成績下位の落ちた候補)。測れない行（①が無い行）は最後に置く。
    """
    ok = [r for r in rows if "①時間の割合" in r]
    ng = [r for r in rows if "①時間の割合" not in r]
    gs = list(groups) if groups else [None]
    inside = set()
    for g in gs:
        k = 0
        for i, r in enumerate(sorted(ok, key=lambda x: rank_key(x, g)), start=1):
            if g is not None:
                r[f"順位({g})"] = i
            # ★比べる相手（RG-v5）は順位だけ付け、上位の枠（keep）を使わない・落ちた候補に数えない（束ではないため・監査 CP48）
            if str(r.get("判定", "")).startswith("RG-v5"):
                continue
            k += 1
            if keep is None or k <= keep:
                inside.add(id(r))
    if groups:
        ok.sort(key=lambda x: (min(x[f"順位({g})"] for g in gs), rank_key(x, gs[0])))
    else:
        ok.sort(key=rank_key)
    dropped = []
    for i, r in enumerate(ok, start=1):
        r["順位"] = i
        if str(r.get("判定", "")).startswith("RG-v5"):
            r["比べる相手"] = True
            continue
        if id(r) not in inside:
            r["dropped_by"] = "成績下位"
            dropped.append({"場面": "成績下位", "判定": r.get("判定"), "順位": i})
    return ok + ng, dropped
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:107「def rank_rows(rows: list[dict], keep: int | None = None) -> tuple[list[dict], list[dict]]:」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 139行（write_outputs）
直す前の文字:
~~~
    stamp = time.strftime("%Y%m%d-%H%M%S")
~~~
足す文字:
~~~

    # ★札の版（M2-F-6d・まこさん決定 2026-09-28 の構造の文の3つ目）＝どの版の札で作った順位表かを、順位表と落ちた候補の各行に書く
    tag_l = rl.version_tag()
    rows = [dict(r, 札の版=tag_l) for r in rows]
    dropped = [dict(d, 札の版=tag_l) for d in dropped]
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:139「    stamp = time.strftime("%Y%m%d-%H%M%S")」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 176〜184行（_labels_for）
直す前の文字:
~~~
def _labels_for(df_win: pd.DataFrame) -> dict:
    """観察の道具の正解の印（強さ）を、値決め窓の close から作る。戻り＝{n: (強さ, 使える)}。"""
    import observe_diag as od
    out = {}
    for n in od._regime_horizons():
        lab = od._regime_labels(df_win[["close"]].astype(float), int(n))
        s, u = lab["強さ"]
        out[int(n)] = (s.to_numpy(bool), u.to_numpy(bool))
    return out
~~~
直した後の文字:
~~~
def _labels_for(df_win: pd.DataFrame) -> dict:
    """答え合わせに使う正解ラベル（札）の強さを、値決め窓のバーから作る。戻り＝{行の名前に入れる文字: (強さ, 使える)}。

    ★札を作る場所は regime_label.py の1か所（M2-F-6d・まこさん決定 2026-09-28「札を作る場所を1つにすること」）。
      採点に使う版が er_median なら鍵は「先24本」「先288本」（いままでと同じ）、band_hold なら役割の名前。
    """
    w = df_win[[c for c in ("high", "low", "close") if c in df_win.columns]].astype(float)
    out = {}
    for key in rl.keys():
        s, u = rl.labels_for_key(w, key)["強さ"]
        out[rl.key_label(key)] = (s.to_numpy(bool), u.to_numpy(bool))
    return out
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:176「def _labels_for(df_win: pd.DataFrame) -> dict:」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 203〜208行（measure）
直す前の文字:
~~~
        for n, (s, u) in labels.items():
            r[f"③実はトレンド(先{n}本)"] = r9_trend_share(col, s, u)
            # ★M2-F-2 の (a)(b)(f)＝当たった（1−③・nan は nan のまま）・捉えた・正解レンジの割合を足す
            r[f"当たった(先{n}本)"] = 1.0 - r[f"③実はトレンド(先{n}本)"]
            r[f"捉えた(先{n}本)"] = r9_catch_share(col, s, u)
            r[f"正解レンジ(先{n}本)"] = r9_range_share(s, u)
~~~
直した後の文字:
~~~
        for nm, (s, u) in labels.items():
            r[f"③実はトレンド({nm})"] = r9_trend_share(col, s, u)
            # ★M2-F-2 の (a)(b)(f)＝当たった（1−③・nan は nan のまま）・捉えた・正解レンジの割合を足す
            # ★M2-F-6d＝列の名前の括弧の中は札の鍵（版1＝「先24本」「先288本」＝いままでと同じ／版2＝役割の名前）
            r[f"当たった({nm})"] = 1.0 - r[f"③実はトレンド({nm})"]
            r[f"捉えた({nm})"] = r9_catch_share(col, s, u)
            r[f"正解レンジ({nm})"] = r9_range_share(s, u)
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:203「        for n, (s, u) in labels.items():」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 534行（run_stage）
直す前の文字:
~~~
    rows, drop_rank = rank_rows(rows, keep=keep)
~~~
直した後の文字:
~~~
    rows, drop_rank = rank_rows(rows, keep=keep, groups=rl.groups())
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:534「    rows, drop_rank = rank_rows(rows, keep=keep)」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 588行（run_sweep）
直す前の文字:
~~~
        rows, _ = rank_rows(rows)
~~~
直した後の文字:
~~~
        rows, _ = rank_rows(rows, groups=rl.groups())
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:588「        rows, _ = rank_rows(rows)」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 639行（run_sweep）
直す前の文字:
~~~
    finals, _ = rank_rows(finals)
~~~
直した後の文字:
~~~
    finals, _ = rank_rows(finals, groups=rl.groups())
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:639「    finals, _ = rank_rows(finals)」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 969行（main）
直す前の文字:
~~~
    rows, _dr = rank_rows(rows)
~~~
直した後の文字:
~~~
    rows, _dr = rank_rows(rows, groups=rl.groups())
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:969「    rows, _dr = rank_rows(rows)            # keep=None＝この口では成績下位を作らない（並べて順位を付けるだけ）」
状態: 確定

#### 実装 12
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 780行（selftest）
直す前の文字:
~~~
            ng.append("⑨: 順位表のファイルが書かれない")
~~~
足す文字:
~~~

        # ⑬ 札の版（M2-F-6d・まこさん決定 2026-09-28 の構造の文の3つ目）＝順位表と落ちた候補の各行に、いまの設定の札の版の名前が書かれる
        try:
            _rows13 = json.loads(rp9.read_text(encoding="utf-8"))
        except Exception:
            _rows13 = []
        if not _rows13 or not _back or any(x.get("札の版") != rl.version_tag() for x in _rows13 + _back):
            ng.append("⑬: 順位表か落ちた候補に、札の版（regime_label.version_tag）が書かれていない")
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:780「            ng.append("⑨: 順位表のファイルが書かれない")」
状態: 確定

#### 実装 13
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 805行（selftest）
直す前の文字:
~~~
        ng.append("⑩: keep の内の行に成績下位が付いた・比べる相手が keep を使った・落ちた候補の並びが違う")
~~~
足す文字:
~~~

    # ⑫ 役割ごとに keep 本ずつ残す（M2-F-6d・まこさん OK 2026-09-28＝worklog 20260928 §51 の1）＝片方の役割で1位の行は、もう片方で最下位でも残る
    _rS = {"判定": "S", "①時間の割合": 0.5, "③実はトレンド(scalp)": 0.40, "③実はトレンド(daytrade)": 0.60,
           "捉えた(scalp)": 0.6, "捉えた(daytrade)": 0.6}
    _rT = {"判定": "T", "①時間の割合": 0.5, "③実はトレンド(scalp)": 0.60, "③実はトレンド(daytrade)": 0.40,
           "捉えた(scalp)": 0.6, "捉えた(daytrade)": 0.6}
    _rU = {"判定": "U", "①時間の割合": 0.5, "③実はトレンド(scalp)": 0.50, "③実はトレンド(daytrade)": 0.50,
           "捉えた(scalp)": 0.6, "捉えた(daytrade)": 0.6}
    _rk12, _drop12 = rank_rows([_rU, _rS, _rT], keep=1, groups=["scalp", "daytrade"])
    if ([d["判定"] for d in _drop12] != ["U"] or _rS.get("順位(scalp)") != 1 or _rT.get("順位(daytrade)") != 1
            or _rS.get("dropped_by") or _rT.get("dropped_by")):
        ng.append(f"⑫: 役割ごとに keep 本ずつ残っていない（落ちた候補＝{[d['判定'] for d in _drop12]}）")
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:805「        ng.append("⑩: keep の内の行に成績下位が付いた・比べる相手が keep を使った・落ちた候補の並びが違う")」
状態: 確定

#### 実装 14
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 861行（selftest）
直す前の文字:
~~~
／ ⑯差し戻しの段2c の「なし」と足す側")
~~~
直した後の文字:
~~~
／ ⑯差し戻しの段2c の「なし」と足す側 ／ ⑫役割ごとに keep 本ずつ残す ／ ⑬札の版をファイルに書く")
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:861「          f" ／ ⑥捉えた割合（既知答え・反転・正解0本は nan）／ ⑦乱数 0件 ／ ⑧record_run ／ ⑨落ちた候補の5つの場面 ／ ⑩並べる鍵は平均 ／ ⑪段の口の束（合成データ・関所で拒否の行）／ ⑭段2a の出る線は緩い側 ／ ⑮段1 は上側と下側 ／ ⑯差し戻しの段2c の「なし」と足す側")」
状態: 確定

#### 実装 15
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 556行（run_sweep）
直す前の文字:
~~~
    # ★M2-F-15＝上位（stage_keep_of の本数）の束ごとに差し戻し、最終の束を最大 keep 本 出す（監査 CP48・直す前は1位の1本だけ）
~~~
直した後の文字:
~~~
    # ★M2-F-6d（工事 B）＝札の版が役割を持つとき（band_hold）、下の「良くなったか」の比べ（rank_key）が役割の列を混ぜた平均になる。
    #   役割ごとの差し戻しの比べ方は、まだどの文書にも決まっていない（worklog 20260928 §51 の1 は段ごとに残す本数だけ）
    #   ＝黙って混ぜずに止まる（fail-closed）。採点に使う版を切り替えるときに作る。
    if rl.groups() is not None:
        raise SystemExit("[R9] 札の版が役割ごと（band_hold）のときの差し戻しは、まだ作っていない"
                         "（役割の列を混ぜて比べない・fail-closed）")
    # ★M2-F-15＝上位（stage_keep_of の本数）の束ごとに差し戻し、最終の束を最大 keep 本 出す（監査 CP48・直す前は1位の1本だけ）
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:556「    # ★M2-F-15＝上位（stage_keep_of の本数）の束ごとに差し戻し、最終の束を最大 keep 本 出す（監査 CP48・直す前は1位の1本だけ）」
状態: 確定

#### 実装 16
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 856〜859行（selftest）
直す前の文字:
~~~
    # ⑤ 印の作り方が観察の道具の実物と同じ関数であること（写しを作っていない）
    import observe_diag as od
    if not hasattr(od, "_regime_labels") or not hasattr(od, "_regime_horizons"):
        ng.append("⑤: observe_diag の印の関数が見つからない")
~~~
直した後の文字:
~~~
    # ⑤ 札は、札を作る場所（regime_label）の口で作る（写しを作っていない・M2-F-6d）。
    #   観察の道具と測る道具が部品を呼び、式を書き写していないかは regime_label.py の自己検査 T6 が見る
    if not all(hasattr(rl, f) for f in ("keys", "labels_for_key", "key_label", "groups", "version_tag")):
        ng.append("⑤: regime_label の札の口が見つからない")
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:856「    # ⑤ 印の作り方が観察の道具の実物と同じ関数であること（写しを作っていない）」
状態: 確定

#### 実装 17
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 860行（selftest）
直す前の文字:
~~~
⑤印は observe_diag の関数
~~~
直した後の文字:
~~~
⑤札は regime_label の口
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:860「    print(f"[selftest] ①100%/0% ／ ②反転で 1−x（x={x:.2f}）・真0本は nan ／ ③束なしは止まる ／ ④未来参照 0件 ／ ⑤印は observe_diag の関数"」
状態: 確定

#### 実装 18
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 115行（<モジュール直下>）
直す前の文字:
~~~
import indicator_reference_diag as iref   # noqa: E402
~~~
足す文字:
~~~

import regime_label as rl   # noqa: E402  答え合わせに使う正解ラベル（札）を作る、ただ1つの場所（M2-F-6d）
~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:115「import indicator_reference_diag as iref   # noqa: E402」
状態: 確定

#### 実装 19
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 5791〜5792行（<モジュール直下>）
直す前の文字:
~~~
#   N（先を見る本数）＝実物（recipes/search_limits.json の state_hold_bars_range）の両端をその場で読む
#     ＝コードに写さない（2か所に持つと片方だけ直って黙って腐る・教訓 L-519）。
~~~
直した後の文字:
~~~
#   N（先を見る本数）＝札を作る場所（regime_label.py・設定＝recipes/regime_label.json）の、採点に使う版の本数をその場で読む
#     ＝コードに写さない（2か所に持つと片方だけ直って黙って腐る・教訓 L-519）。M2-F-6d で search_limits.json から移した。
~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:5791「#   N（先を見る本数）＝実物（recipes/search_limits.json の state_hold_bars_range）の両端をその場で読む」
状態: 確定

#### 実装 20
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 5806〜5814行（_regime_horizons）
直す前の文字:
~~~
def _regime_horizons() -> tuple[int, ...]:
    """先を見るバー数（N）。実物の範囲の両端をその場で読む＝コードに数字を写さない。

    出どころ＝recipes/search_limits.json の state_hold_bars_range（M2-2-5・まこさん承認 24a453d6…）。
    """
    import json
    p = pathlib.Path(__file__).resolve().parent / "recipes" / "search_limits.json"
    d = json.loads(p.read_text(encoding="utf-8"))["state_hold_bars_range"]
    return (int(d["lo"]), int(d["hi"]))
~~~
直した後の文字:
~~~
def _regime_horizons() -> tuple[int, ...]:
    """先を見るバー数（N）。札を作る場所（regime_label.py）の、採点に使う版の本数を返す＝コードに数字を写さない。

    出どころ＝recipes/regime_label.json（M2-F-6d・まこさん決定 2026-09-28）。
      版1 er_median＝「先を見る本数」（24・288＝もとは search_limits.json の state_hold_bars_range の両端・まこさん承認 24a453d6…）
      版2 band_hold＝役割ごとに 保有の上限 × 続く本数
    """
    return rl.bars_keys()
~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:5806「def _regime_horizons() -> tuple[int, ...]:」
状態: 確定

#### 実装 21
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 5831〜5848行（_regime_labels）
直す前の文字:
~~~
def _regime_labels(win: pd.DataFrame, n: int) -> dict:
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
~~~
直した後の文字:
~~~
def _regime_labels(win: pd.DataFrame, n: int) -> dict:
    """そのバーから先 n本の値動きの性質を、3つの見方で真偽に直す（＝答え合わせに使う正解ラベル・札）。

    ★札を作る場所は regime_label.py の1か所（M2-F-6d・まこさん決定 2026-09-28「札を作る場所を1つにすること」）。
      ここは呼ぶだけ＝式を写さない（regime_label.py の自己検査 T6 が見る）。
    ①強さ・②向き・③大きさ の作り方＝regime_label.py の er_median（版1＝いままでの式）と band_hold（版2）の説明。
    戻り＝{名前: (真偽の並び, その行が使えるか)}。先が足りない末尾は「使えない」になる。
    """
    return rl.labels_at_bars(win, n)
~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:5831「def _regime_labels(win: pd.DataFrame, n: int) -> dict:」
状態: 確定

#### 実装 22
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 6090行（_insp_regime_rank）
直す前の文字:
~~~
          "（出どころ＝search_limits.json の state_hold_bars_range の両端）")
~~~
直した後の文字:
~~~
          f"（出どころ＝recipes/regime_label.json の採点に使う版・札の版 {rl.version_tag()}）")
~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:6090「          "（出どころ＝search_limits.json の state_hold_bars_range の両端）")」
状態: 確定

#### 実装 23
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 6119行（_insp_regime_rank）
直す前の文字:
~~~
    body = dict(r)
~~~
足す文字:
~~~

    body["札の版"] = rl.version_tag()   # ★M2-F-6d＝どの版の札で作った成績表か（まこさん決定 2026-09-28 の構造の文の3つ目・§51 の2）
~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:6119「    body = dict(r)」
状態: 確定

#### 実装 24
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 6307行（add_demand_to_ranking）
直す前の文字:
~~~
    body = dict(rank2)
~~~
足す文字:
~~~

    # ★M2-F-6d＝足す前の成績表と、いまの設定の札の版が同じでなければ書かない（違う札の順位を1つの表に混ぜない・fail-closed）。
    #   札の版が無い成績表＝版を持つ前に版1（er_median）の式で作った物（先を見るバー数の食い違いは merge_demand_into_ranking が先に止める）。
    _tag0 = rank.get("札の版") or rl.version_tag(version="er_median")
    if _tag0 != rl.version_tag():
        raise SystemExit(f"[需給の順位づけ] 成績表の札の版 {_tag0} と、いまの設定の札の版 {rl.version_tag()} が違う"
                         "（先に --rank-regime で作り直す・fail-closed）")
    body["札の版"] = rl.version_tag()
~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:6307「    body = dict(rank2)」
状態: 確定

#### 実装 25
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 25行（<モジュール直下>）
直す前の文字:
~~~
  ★呼ぶ側を切り替えるのは工事 B（観察の道具・測る道具）と工事 C（⑪タブ）。呼ぶ側の確かめ（自己検査 T6）は工事 B で足す。
~~~
直した後の文字:
~~~
  ★呼ぶ側の切り替え＝観察の道具と測る道具は、工事 B（2026-10-02）で部品を呼ぶ形にした
    （自己検査 T6 が、呼ぶ側が部品を呼び、札の式を書き写していないかを見る）。⑪タブの道具は工事 C。
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:25「  ★呼ぶ側を切り替えるのは工事 B（観察の道具・測る道具）と工事 C（⑪タブ）。呼ぶ側の確かめ（自己検査 T6）は工事 B で足す。」
状態: 確定

#### 実装 26
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 340行（selftest）
直す前の文字:
~~~
    # T7 採点に使う版が band_hold なのに使う値が空なら止まる
~~~
直した後の文字:
~~~
    # T6 呼ぶ側が、ここを呼んでいる（作る場所が1つ＝式を書き写していない）
    import ast
    for fn, path in (("_regime_labels", HERE / "observe_diag.py"), ("_regime_horizons", HERE / "observe_diag.py"),
                     ("_labels_for", HERE / "regime_r9_diag.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        f = [x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef) and x.name == fn]
        calls = [x for x in ast.walk(f[0]) if isinstance(x, ast.Attribute)
                 and isinstance(x.value, ast.Name) and x.value.id == "rl"] if f else []
        if not calls:
            ng.append(f"T6: {path.name} の {fn} が、札を作る場所（regime_label）を呼んでいない")
        if f and any(isinstance(x, ast.Attribute) and x.attr == "median" for x in ast.walk(f[0])):
            ng.append(f"T6: {path.name} の {fn} に、札の式（median）が書き写されている")
    # T7 採点に使う版が band_hold なのに使う値が空なら止まる
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:340「    # T7 採点に使う版が band_hold なのに使う値が空なら止まる」
状態: 確定

#### 実装 27
対象のファイル: scripts/priority_rebuild/regime_label.py
直す箇所: 380行（selftest）
直す前の文字:
~~~
T5 版1 は前の式と同じ ／ T7 使う値が空なら止まる
~~~
直した後の文字:
~~~
T5 版1 は前の式と同じ ／ T6 呼ぶ側がここを呼ぶ ／ T7 使う値が空なら止まる
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_label.py:380「          "T5 版1 は前の式と同じ ／ T7 使う値が空なら止まる ／ T8 版の名前・保有の範囲 ／ T9 値の組 ／ T10 続くの確かめ ／ T11 近い山のまとめ方")」
状態: 確定

#### 実装 28
対象のファイル: .claude/breaks/b122_obs_formula_copied.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 観察の道具の _regime_labels に札の式を書き写すと、自己検査 T6 が「札を作る場所を呼んでいない・式が書き写されている」で落ちた
# EXPECT_MSG: ❌ T6
# b122 — observe_diag._regime_labels が regime_label を呼ばずに式（中央値で切る）を持つと、T6 が落ちるか（M2-F-6d・2026-09-29）
#   守っているもの＝完成の条件 #1（札を作る場所が1つ＝まこさん決定 2026-09-28「札を作る場所を1つにすること」）
#   壊し方＝`    return rl.labels_at_bars(win, n)` を、中央値で切る式の写しに置き替える。
#   期待＝regime_label.py --selftest の T6 が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    return rl.labels_at_bars(win, n)\n'
if s.count(old) != 1:
    raise SystemExit("[b122] 壊す対象の行が1か所でない: " + old.strip())
new = ('    c = win["close"].astype(float).diff().abs()  # b122 が壊した（札の式を写した）\n'
       '    return {"強さ": (c >= c.median(), c.notna()), "向き": (c > 0, c.notna()), "大きさ": (c >= c.median(), c.notna())}\n')
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/regime_label.py" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b113_catch_share_broken.sh:1「#!/bin/bash」
状態: 確定

#### 実装 29
対象のファイル: .claude/breaks/b123_label_tag_dropped.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 順位表の各行に札の版を書かなくすると、自己検査⑬が「順位表か落ちた候補に、札の版が書かれていない」で落ちた
# EXPECT_MSG: ❌ ⑬
# b123 — regime_r9_diag.write_outputs が順位表の行に札の版を書かないと、⑬が落ちるか（M2-F-6d・2026-09-29）
#   守っているもの＝完成の条件 #3（どの版の札で作った順位表かを、順位表の側に残す＝まこさん決定 2026-09-28 の構造の文の3つ目）
#   壊し方＝`    rows = [dict(r, 札の版=tag_l) for r in rows]` を `    pass` にする。
#   期待＝regime_r9_diag.py --selftest の⑬が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    rows = [dict(r, 札の版=tag_l) for r in rows]\n'
if s.count(old) != 1:
    raise SystemExit("[b123] 壊す対象の行が1か所でない: " + old.strip())
new = '    pass  # b123 が壊した（順位表に札の版を書かない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b113_catch_share_broken.sh:1「#!/bin/bash」
状態: 確定

#### 実装 30
対象のファイル: .claude/breaks/b124_role_keep_off.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 役割ごとに上位を残す判定を外すと、自己検査⑫が「役割ごとに keep 本ずつ残っていない」で落ちた
# EXPECT_MSG: ❌ ⑫
# b124 — regime_r9_diag.rank_rows が役割ごとに keep 本を残さないと、⑫が落ちるか（M2-F-6d・2026-09-29）
#   守っているもの＝完成の条件 #2（役割ごとに10本ずつ残す＝worklog 20260928 §51 の1・まこさん OK）
#   壊し方＝`            if keep is None or k <= keep:` を `            if False:` にする（どの行も残す側に入らない）。
#   期待＝regime_r9_diag.py --selftest の⑫が落ちる（終了コード 1）。⑩も一緒に落ちる。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            if keep is None or k <= keep:\n'
if s.count(old) != 1:
    raise SystemExit("[b124] 壊す対象の行が1か所でない: " + old.strip())
new = '            if False:  # b124 が壊した（役割ごとに残さない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 30 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 9/29 の控えの 1〜21・31〜33 を土台にし、直すのは実物が変わった所と足す所だけにする | 9/29 の控えは まこさんの構造の文と定義の文を満たす形で書いた（worklog 20260929 §15）。手で書き直すと写し間違いが入る | 実装の指示を一から書き直す。捨てた理由＝写し間違いが入る |
| 2 | 自己検査の印字の行（9/29 の14番）を、⑯の後ろに⑫⑬を足す形に直す | 14b（142回目）で印字の行に⑭⑮⑯が足され、9/29 の直す前の文字が実物に無くなった | 9/29 のまま当てる。捨てた理由＝当たらない |
| 3 | 壊すプログラムの番号を b122〜b124 にする | b119〜b121 は 9/30 の道具の工事が使っていた | 9/29 の番号のまま作る。捨てた理由＝同じ番号が2本になり、どちらの話か分からなくなる |
| 4 | 役割ごとの札（band_hold）のときの差し戻しは止める | 差し戻しの「良くなったか」は1つの並べる鍵で比べる。役割ごとの比べ方は、まだどの文書にも決まっていない | 役割の列を混ぜた平均で比べる。捨てた理由＝黙って違う物差しで比べることになる |
| 5 | 測る道具の自己検査⑤を、札の部品の口があるかを見る形にする | 測る道具は観察の道具を呼ばなくなるので、「印は observe_diag の関数」が事実でなくなる（恒久72番の2＝同じ事実を揃える） | ⑤をそのまま残す。捨てた理由＝説明と印字が実物と食い違う |
| 6 | 札の部品の説明の文を、工事 B の後の事実に直す | 説明の文は「呼ぶ側を切り替えるのは工事 B」「T6 は工事 B で足す」で、工事 B の後は事実でなくなる | そのまま残す。捨てた理由＝説明が実物と食い違う |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=fcde7b193cd69f47 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b122_obs_formula_copied.sh` | #1 | 観察の道具の _regime_labels に札の式を書き写すと、T6 が『❌』で落ちる |
| `b124_role_keep_off.sh` | #2 | 役割ごとに残す判定を外すと、⑫が『❌』で落ちる |
| `b123_label_tag_dropped.sh` | #3 | 順位表の行に札の版を書かないと、⑬が『❌』で落ちる |
| `—` | #4 | 壊すプログラムは付けない（直す前と後で結果が同じかを、144回目の印字と照らす） |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | M2-F-5 の走行の数字が、144回目と違う | 違ったら、どの列が違うかをそのまま貼り、直す前のコード（git の版）で同じ走行をして、違いが札の呼び方から来るのかを確かめてから まこさんに出す |
| 2 | 観察の道具の自己検査（約2分）や H2 の検査が、札の行の変更で止まる | 結果をそのまま貼る。札の行が判定に入っていないことを示して、直し方を まこさんに出す |
| 3 | 工事 A の壊すプログラム b118 と、9/30 の b118_audit_fix_tools_target.sh が同じ番号 | この工事では直さない（工事 A の設計書と承認の記録が b118 の名前を持っている）。next_step の「あとで直すこと」に積む |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる・新しいファイルを書く | 30秒未満 | 2026-10-02 の監査 cp58 の直しで、当てる道具は1秒未満で終わった（worklog 20261002 §7） |
| 自己検査と b122〜b124 | 測っていない | 4-14 |
| G2 と H2 の取り直し | 約5分30秒 | G2 29.0秒・H2 5分0秒（2026-10-02 の実測） |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝札の式と先を見る本数が、観察の道具の中と組む側の設定の中に在り、測る道具はそれを呼んでいることです。工事 A で部品を作りましたが、呼ぶ側を切り替えないと、札を作る場所は1つになりません。結果の側にも、どの札で作ったかが残りません。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。採点に使う版は er_median のままなので、判定の成績（3つの割合）も動きません。

**③ root か symptom か**＝root です。札を直すたびに2つの道具を別々に直す形は、片方だけ直る symptom の運用です。この工事で、札を作る場所を部品の1か所にし、どの札で作ったかを結果に残します。

**④ ベースアップ**＝役割ごとに測って残す形は、まこさんの OK（worklog 20260928 §51 の1）に従いました。札の版を成績表に書く理由は、段2a の並び順が成績表を使うことです（§51 の2）。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。新しい数字も作りません。先を見る本数は工事 A の設定 regime_label.json から読み、keep は search_limits.json の stage_keep_range から読みます。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝観察の道具と測る道具を、札の部品を呼ぶ形に切り替え、札の版を結果に書く（14a の工事 B＝L-1 のうち⑪タブを除く分・L-5・L-6）。⑪タブは工事 C（まこさん「よい」2026-10-02）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。札は条件をつなぐものではなく、答え合わせの答えです。役割ごとに残す並べ方は、並べる鍵の決まった順です |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 値を選びません。先を見る本数と keep は、承認済みの設定から読みます |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **版2 の札で測った順位が、実際の相場で正しいか** | この工事では分かりません。まこさんが⑪タブの目と検査15 で値を選び、最後は M2-L の net で分かります |
| **役割ごとの札のときの差し戻し** | この工事では作りません（止まる形）。採点に使う版を切り替えるときに作ります |
| **観察の道具と測る道具と札の部品そのものを書き換えられたら** | 書き換えれば無効にできます。承認で凍結され、差分は git に出ます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=ea963af9f7175174 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝3本（測る道具 regime_r9_diag.py・観察の道具 observe_diag.py・札の部品 regime_label.py）を【7-8】に書いた。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝regime_r9_diag.py＝この工事でいちばん多く直すファイル。ほかの2本は impl_functions に書いた）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイル3本（壊すプログラム b122〜b124）を NEW_FILE に、手本を MODEL に書いた（【7-8】）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝9/29 の控えの直す前の文字が、14b の後の実物とずれた所（自己検査の印字の行）を道具で見つけて直した。壊すプログラムの番号の重なりも道具で確かめて付け替えた。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 新しい部品は無い。札の部品は工事 A で作った物で、H2 の見張りの一覧に既に在る。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 直すファイルの行番号を指す文書は、9/29 の控え（承認していない古い控え）だけで、この工事の実装の指示の行は いまの実物から作り直した。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前で壊すプログラムを grep し、直す行の文字を探している物は0本だった（4-13 の4）。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 新しい壊すプログラム b122〜b124 が測るコマンドは、札の部品と測る道具の --selftest で、本物の結果の置き場（results/ ほか）や帳簿には書かない（測る道具の⑨⑬は一時の置き場に書く）。壊す相手は lib.sh の guard で控えに写して戻す（手本 b118）。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 触る関数は、全部 DESIGN_CONTRACT の impl_functions に書いた（【7-8】・下書きの道具が当てる前と後の差の行から数えた）。regime_r9_diag.py: <モジュール直下>・_labels_for・main・measure・rank_key・rank_rows・run_stage・run_sweep・selftest・write_outputs。observe_diag.py: <モジュール直下>・_insp_regime_rank・_regime_horizons・_regime_labels・add_demand_to_ranking。regime_label.py: <モジュール直下>・selftest。must_use に、rank_rows と run_stage が呼ぶ名前を書いた（下書きの道具が ast で照らした）。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足す旗は無い。足す自己検査（T6・⑫・⑬）は、完成の条件の1〜3行目が走らせる。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2f-label-callers-20261002）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝札の部品と測る道具の --selftest・壊すプログラム b122〜b124・承認の前の検査。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 札の部品の自己検査が全部 通る（T1〜T11・T6＝観察の道具と測る道具が部品を呼び、札の式を書き写していない） | `python3 scripts/priority_rebuild/regime_label.py --selftest` | 実経路 | 観察の道具の _regime_labels に札の式を書き写すと、T6 が『❌』で落ちる | `b122_obs_formula_copied.sh` | — | **未着手** |
| 2 | 測る道具の自己検査が全部 通る（⑫役割ごとに keep 本ずつ残す） | `python3 scripts/priority_rebuild/regime_r9_diag.py --selftest` | 実経路 | 役割ごとに残す判定を外すと、⑫が『❌』で落ちる | `b124_role_keep_off.sh` | — | **未着手** |
| 3 | 測る道具の自己検査が全部 通る（⑬順位表と落ちた候補に札の版を書く） | `python3 scripts/priority_rebuild/regime_r9_diag.py --selftest` | 実経路 | 順位表の行に札の版を書かないと、⑬が『❌』で落ちる | `b123_label_tag_dropped.sh` | — | **未着手** |
| 4 | M2-F-5 の走行で、144回目と同じ3つの割合が出て、順位表と落ちた候補の各行に札の版が在る | `python3 scripts/priority_rebuild/regime_r9_diag.py --stage stage1 --limit 2 --purpose check` | 実経路 | 壊すプログラムは付けない（直す前と後で結果が同じかを、144回目の印字と照らす） | `—` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=7e842caf4ca4bb4c gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/regime_r9_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `version_tag` | （この関数は実物に無い） |
| `labels_for_key` | （この関数は実物に無い） |
| `groups` | （この関数は実物に無い） |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 28件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=5af380427fb90648 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/regime_r9_diag.py",
  "_impl_file の意味": "照らす相手は実在するファイル（gen_acceptance.py:680〜683）。この工事でいちばん多く直す測る道具 regime_r9_diag.py にした。ほかの2本は impl_functions に書いた。",
  "impl_functions": {
    "scripts/priority_rebuild/regime_r9_diag.py": [
      "<モジュール直下>",
      "_labels_for",
      "main",
      "measure",
      "rank_key",
      "rank_rows",
      "run_stage",
      "run_sweep",
      "selftest",
      "write_outputs"
    ],
    "scripts/priority_rebuild/observe_diag.py": [
      "<モジュール直下>",
      "_insp_regime_rank",
      "_regime_horizons",
      "_regime_labels",
      "add_demand_to_ranking"
    ],
    "scripts/priority_rebuild/regime_label.py": [
      "<モジュール直下>",
      "selftest"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数。当てる前と後の差の行を、当てた後のコードの関数に当てはめて、下書きの道具（_labelB_draft_build.py）が数えた。",
  "self_check_calls": [
    "version_tag",
    "labels_for_key",
    "groups"
  ],
  "_self_check_calls の意味": "実装の後の regime_r9_diag.py に在るはずの、札の部品の口の名前（版の名前・鍵ごとの札・役割の組）。★ファイル名を書かない＝7-7 の表が「読んだ」の行の下に並べ、必読ゲートが数えるため。",
  "must_use": {
    "rank_rows": [
      "rank_key"
    ],
    "run_stage": [
      "rank_rows",
      "measure",
      "write_outputs"
    ]
  },
  "_must_use の意味": "rank_rows が並べる鍵を、run_stage が測る・並べる・書くを呼ぶはず（下書きの道具が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は、札の呼び方と、順位表・落ちた候補・成績表への札の版の書き方だけを変える。外から読む一覧（候補・法則・成績表の順位・範囲の鍵）の読み方は変えない。",
  "generated_from": {
    "impl_functions": "当てる前と後の差の行（_labelB_draft_build.py が数えた）",
    "must_use": "rank_rows と run_stage が呼ぶ名前（ast で照らした）",
    "spec_lists": "空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/regime_r9_diag.py",
 "public_functions": {
  "r9_share": [],
  "r9_trend_share": [],
  "r9_catch_share": [],
  "r9_range_share": [],
  "rank_key": [],
  "rank_rows": [],
  "write_outputs": [],
  "r9_trades": [],
  "measure": [
   "r9_catch_share",
   "r9_range_share",
   "r9_share",
   "r9_trades",
   "r9_trend_share"
  ],
  "print_stage_candidates": [],
  "run_stage": [
   "measure",
   "rank_rows",
   "write_outputs"
  ],
  "run_sweep": [
   "measure",
   "rank_key",
   "rank_rows",
   "write_outputs"
  ],
  "run_nan_check": [],
  "selftest": [
   "measure",
   "r9_catch_share",
   "r9_share",
   "r9_trend_share",
   "rank_rows",
   "write_outputs"
  ],
  "main": [
   "measure",
   "print_stage_candidates",
   "rank_rows",
   "run_nan_check",
   "run_stage",
   "run_sweep",
   "selftest",
   "write_outputs"
  ]
 },
 "constants": {},
 "cli_flags": []
}
```

<!-- ACC_SPEC_END -->

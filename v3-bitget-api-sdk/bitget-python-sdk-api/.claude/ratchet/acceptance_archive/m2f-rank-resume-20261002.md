<!-- ARC iter="m2f-rank-resume-20261002" -->

# 設計書｜成績表の全走を、途中で落ちても続きから計算できる形にする＝14a の工事 E

TARGET: scripts/priority_rebuild/observe_diag.py, .claude/breaks/b126_rank_resume_save_off.sh
NEW_FILE: .claude/breaks/b126_rank_resume_save_off.sh
MODEL: .claude/breaks/b125_hindsight_osc_off.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2f-rank-resume-20261002/ok_labelE_20261003`・`m2f-rank-resume-20261002/okd_labelE_20261003`・`m2f-rank-resume-20261002/req_resume_20261003`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2f-rank-resume-20261002/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2f-rank-resume-20261002 --write`。検出＝`--work m2f-rank-resume-20261002 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=358d4a7869e1d9ab gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2f-rank-resume-20261002/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2f-rank-resume-20261002/ok_labelE_20261003.txt`（まこさんの発言）・`verbatim/m2f-rank-resume-20261002/okd_labelE_20261003.txt`（まこさんが OK した CC の文）・`verbatim/m2f-rank-resume-20261002/req_resume_20261003.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝328 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_labelE_20261003` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_labelE_20261003` | V01〜V21（21 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_labelE_20261003` | V22〜V26（5 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V27〜V29（3 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V30〜V32（3 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V33〜V42（10 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V43〜V48（6 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V49〜V55（7 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V56〜V62（7 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V63〜V64（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V65〜V66（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V67〜V68（2 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V69〜V70（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V71〜V72（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V73〜V74（2 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V75〜V79（5 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V80〜V85（6 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V86〜V87（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V88〜V89（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V90〜V91（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V92〜V97（6 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V98〜V182（85 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V183〜V189（7 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V190〜V194（5 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V195〜V201（7 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V202〜V208（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V209〜V210（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V211〜V212（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V213〜V217（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V218〜V227（10 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V228〜V248（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V249〜V253（5 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V254〜V309（56 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_labelE_20261003` | V310〜V318（9 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `req_resume_20261003` | V01〜V09（9 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
成績表 material_ranking.json は、M2 の段の候補の並びと engine_tuner の組む側が読む、材料の成績表です。作り直す全走（observe_diag.py --rank-regime）は約2時間15分かかり、札を変えるたびに走らせます。いまの道具は、時間足11本の結果をメモリにだけ持ち、最後にまとめて成績表を書くので、途中で落ちると計算が全部 消えます。2026-10-02 には2回 途中で止まり、約3時間半を失いました。この工事 E は、時間足を1本 計算し終えるごとに結果をファイルに書き、走らせ直したら続きから計算する形にします。続きから計算するのは、設定・材料・期間・札・元データ・コードが前と全く同じときだけです。成績表の中身は変えません。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 続きの部品が在るか | `grep -c -F 'def _rank_resume_save' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は当たる行が無い。実装の後は当たる行が在る | 1（終了コード 0） |
| 成績表の本体が結果を書く行が在るか | `grep -c -F '_rank_resume_save(_ck, tf, auc, nsample)' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は当たる行が無い。実装の後は当たる行が在る | 1（終了コード 0） |
| 自己テスト T-r の口が在るか | `grep -c -F -e '--selftest-rank-resume' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は当たる行が無い。実装の後は当たる行が在る | 2（終了コード 0） |

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
| 1 | 成績表の中身（分離力の数え方・札・材料・時間足）を変えること | この工事は、途中で落ちても計算が残る形にするだけ。中身が同じことは、当てる前と後で道具が確かめた | req_resume_20261003（V01〜V02） |
| 2 | 成績表の全走を、この工事の承認の中で走らせること | 10/03 に作り直し済みで、中身は変わらない。次の全走は、札や材料を変えたときに まこさんの OK をもらってから走らせる | worklog 20261003 §2 |
| 3 | 時間足よりも細かい区切り（材料1種ごと）で書くこと | 書く回数が6,000回を超えて遅くなる。いちばん長い1分足で失うのは最大 約75分 | worklog 20261003 §1 |
| 4 | 走らせ方（裏で走らせる仕組みの2時間の上限）を、この工事で守ること | 別に作った hook（block_long_background.py）が守っている（commit 1bb2deb） | worklog 20261002 §33 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 工事 E の実装の監査を出すか | 出さない。直しの文字は6つの試しで証明し、案を作る道具が当てる前と後の成績表の中身が同じことと、自己テスト T-r・壊すプログラム b126 の働きを確かめた。工事 C・D の監査を出すかと一緒に決めていただく | まこさん「監査は出す必要があるのか？」（2026-10-03） |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、成績表の道具の全走を、途中で落ちても続きから計算できる形にするものです。**14a の5つ目の工事です。
**①いま何が起きているか。**成績表の全走は約2時間15分かかります。道具は時間足11本の結果をメモリにだけ持ち、11本が全部 終わってから成績表を書きます。だから途中で落ちると、それまでの計算が全部 消えます。10/02 には2回 途中で止まり、約3時間半を失いました。
**②この工事で何が変わるか。**時間足を1本 計算し終えるごとに、その時間足の結果をファイルに書きます。走らせ直すと、書き終わった時間足は読んで飛ばし、続きから計算します。続きから計算するのは、設定・材料・先を見る本数・期間・札・元データ・コードが前と全く同じときだけです。1つでも違えば、前の結果は使いません。
**③数字はどう変わるか。**成績表の中身は変わりません。直す前と直した後で、同じ材料の成績表の中身が1文字も違わないことを確かめました。変わるのは、途中で落ちたときに失う時間だけです（失うのは計算中の時間足1本ぶん。いちばん長い1分足で約75分）。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**成績表の全走は、私（CC）が まこさんの OK をもらってから走らせます（observe_diag.py --rank-regime）。札を変えたときや、材料の印を切り替えたときに走らせます。
**誰が結果を使うか。**成績表 material_ranking.json は、engine_tuner の組む側（ranked_materials・ranked_groups）と、測る道具（regime_r9_diag.py の段の候補づくり）が読みます。この工事は、成績表の中身を変えないので、読む側は直しません。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**今までどおり（5分足・1分足・設定・材料の一覧・札）。走らせ直したときは、続きの置き場の時間足ごとのファイルも読みます。
**書くもの。**今までどおりの成績表に加えて、時間足ごとの結果のファイルを書きます。置き場＝results/priority_rebuild/ratchet/observe/rank_resume/<指紋16桁>/<時間足>.json（results の下＝git の対象外）。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 成績表の中身を変えない | この工事の目的（途中で落ちても残る） | 当てる前と後で、同じ材料の成績表の中身が1文字も違わないことを道具で確かめた |
| 違う札の結果を混ぜない | 恒久の決まり（札の版を成績表に残す・M2-F-6d の構造の文の3つ目） | 札の中身そのものを指紋に入れる。札の版の名前だけでは決めない |
| 乱数を使わない | 恒久67番 | 自己テスト T-r の作り物の4本値は決まった式（正弦と一次式）で作る |
| 未来の値を使わない | 要件定義書 §4.6.H2 | 足す所は書き方と読み方だけ。未来参照の検査で、注記の無い先読みは当てる前も後も0件 |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| observe_diag.py の _rank_resume_dir | 中身の指紋を作り、続きの置き場を決める | 新設（関数） |
| observe_diag.py の _rank_resume_save | 時間足1本の結果を、一時の名前で書いてから名前を替えて書く | 新設（関数） |
| observe_diag.py の _rank_resume_load | 書き終わった時間足の結果を読んで足す | 新設（関数） |
| observe_diag.py の rank_materials_for_regime | 上の3つを呼ぶ（3か所に足す） | 直す |
| observe_diag.py の selftest_rank_resume と口 --selftest-rank-resume | 途中で落ちても続きから計算できるかを、作り物の4本値で毎回 確かめる（T-r） | 新設 |
| .claude/breaks/b126_rank_resume_save_off.sh | 結果を書く行を外すと、T-r が落ちるかを見る | 新設 |
- 触る所＝observe_diag.py＝<モジュール直下>・_rank_resume_dir・_rank_resume_load・_rank_resume_save・rank_materials_for_regime・selftest・selftest_rank_resume（<モジュール直下>＝口 --selftest-rank-resume の2行・selftest＝T-r を呼ぶ1行）。

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. 当てる道具（apply_audit_fix.py --design）で実装の指示を当てます。
2. 当てた直後に、照合（verify_design_contract.py --diff）をかけます。★この工事は関数を足すので、設計書の SPEC（実装の前のコードから作る）と実物が食い違う見込みです。食い違ったら、gen_acceptance.py --write で設計書を作り直し、承認の打ち直しを1回 お願いします（教訓 L-655）。
3. 自己テスト T-r（--selftest-rank-resume）と T-f（--selftest-rank-demand）を走らせ、壊すプログラム b126 を走らせます。
4. G2 → H2 の順で印を取り直します（observe_diag.py は G2 と H2 の両方の対象）。
5. 成績表の全走は、この工事では走らせません（10/03 に作り直し済み・中身は変わらない）。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝実装の後に、成績表の全走（python3 scripts/priority_rebuild/observe_diag.py --rank-regime data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv）を走らせ、5分足まで3本が終わった所で PC が止まったとする。results/priority_rebuild/ratchet/observe/rank_resume/<指紋16桁>/ には、1分足・3分足・5分足の3本の結果のファイルが残っている。同じコマンドで走らせ直すと、「時間足 1m は前に書き終わった結果を読んだ（1/11 本・続きから）」の行が3本ぶん出て、10分足から計算を始め、約20分で成績表を書く（10/02 の2回目なら、約2時間の計算を捨てずに済んだ）。札を変えてから走らせた場合は、指紋が変わるので前の3本は読まず、1分足から計算する。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**探す値はありません。**

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**コマンドの旗を1つ増やします。**--selftest-rank-resume（自己テスト T-r だけを数秒で走らせる口）。設定ファイルは変えません。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**①自己テスト T-r が通る（①結果が同じ ②落ちた後に1本目だけ残る ③走らせ直すと1本目を読んで飛ばす ④材料が違えば読まない）②壊すプログラム b126 で T-r が T-r② で落ちる ③全走の途中で落ちても、同じコマンドで走らせ直すと「時間足 … は前に書き終わった結果を読んだ（続きから）」と出る。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| 時間足の計算の途中で落ちる（例外・強制終了・PC の再起動） | 書き終わった時間足のファイルは残る。同じコマンドで走らせ直すと、続きから計算する |
| 時間足の結果を書いている途中で落ちる | 一時の名前（<時間足>.json.tmp）のまま残り、本物の名前のファイルは作られない＝読まれない。走らせ直すと、その時間足は計算し直す |
| 設定・材料・先を見る本数・期間・札・元データ・コードのどれかが変わった | 指紋が変わり、別の置き場になる＝前の結果は使わない |
| 書き終わった時間足のファイルが壊れていて読めない | 読む所で止まる（黙って計算し直さない）。置き場を消してから走らせ直す |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**新しく作るもの。**時間足ごとの結果のファイル＝{"時間足": …, "分離力": {列名: {札: {先を見る本数: 分離力}}}, "独立な標本の数": [[札, 先を見る本数, 時間足, 数], …]}。成績表 material_ranking.json の形は変えません。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**足すもの。**results/priority_rebuild/ratchet/observe/rank_resume/<指紋16桁>/（git の対象外）。成績表の置き場は変えません。

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**変えません。**

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| 時間足ごとの結果を書く | 1本 1秒未満 | 10/03 の全走で書いた 1m.json は 81,766 バイト |
| 自己テスト T-r | 約4秒 | 案を作る道具が、当てた後の道具を本物に書かずに走らせた実測 |
| 全走の時間 | 変わらない（約2時間15分） | 10/03 の全走（外から同じ直しを掛けた）は 132.1分＝前の3回と同じ |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**同時に2つ走らせると、同じ置き場の同じ時間足を書き合うおそれがあります。**全走を同時に2つ走らせません（今までどおり、成績表も1つの置き場です）。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しの道具だけが書きます。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**走らせ直して書き終わった時間足を読んだときに、「時間足 … は前に書き終わった結果を読んだ（i/11 本・続きから）」と1行 出します。今までの時間足ごとの終わりの行は変えません。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **observe_diag.py は G2 と H2 の対象です。**実装の後に G2 → H2 を取り直します。
2. **成績表の中身は変わりません。**読む側（engine_tuner の組む側・測る道具）は直しません。
3. **直すファイルの行の文字を探している壊すプログラムが12本 在ります。**この工事は、どれが探す文字も変えません（案を作る道具が、当てる前と後で数えた）。
4. **結果の置き場に、時間足ごとのファイルが増えます**（1回の全走で11本・合わせて約1MB）。

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| 試作 .claude/state/_labelE_resume_probe.py の HELPERS・PATCHES | 直しの文字（6つの証明に使った物と同じ） |
| 試作 .claude/state/_labelE_selftest_probe.py の SELFTEST_FN | 自己テスト T-r の文字（直しが在れば通り、直しを壊すと落ちると確かめた物と同じ） |
| observe_diag.py の selftest_rank_demand（T-f） | 自己テストの形・口の形 |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=7248df4fea323b06 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 5969〜5970行（_rank_record_unmeasured）
直す前の文字:
~~~
                      "または 良い/悪いの片側の標本が10未満）＝黙って消さず記録（M2-3-4）")
    return dropped

~~~
足す文字:
~~~


# ══ 成績表の全走を、途中で落ちても続きから計算する（2026-10-03・工事 E・まこさん「データが途中落ちても残るようにできてるのか証明しろ」）══
#   なぜ＝2026-10-02 に全走（約2時間15分）が2回 途中で止まり、時間足11本の結果をメモリにだけ持つ作りだったので何も残らなかった。
#   直した後＝時間足を1本 計算し終えるごとに、その結果を OBSERVE_DIR/rank_resume/<指紋>/<時間足>.json に書く。
#     走らせ直すと、同じ指紋の置き場に在る時間足は読んで飛ばす。
#   ★指紋＝設定・材料の名前・先を見る本数・値決め窓・札の中身・5分足と1分足の元データ・この道具と札の部品と参照表のコードで決める
#     ＝どれか1つでも違えば別の置き場になり、前の結果を混ぜない。
#   ★書くときは一時の名前で書いてから名前を替える＝書きかけのファイルは読まない。
def _rank_resume_dir(win, cfg, cat_use, horizons, labels) -> pathlib.Path:
    """続きの結果の置き場（中身の指紋で決める）。"""
    import json as _json
    h = hashlib.sha256()

    def _add(x):
        h.update(_json.dumps(x, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8"))
    _add({"設定": {k: v for k, v in cfg.items() if k != "_source"}})
    _add({"材料": [c[0] for c in cat_use]})
    _add({"先を見る本数": [int(n) for n in horizons]})
    _add({"値決め窓": [str(win.index.min()), str(win.index.max()), int(len(win))]})
    h.update(pd.util.hash_pandas_object(win, index=True).to_numpy().tobytes())
    for n in horizons:
        for lab in REGIME_LABELS:
            _m, _u = labels[n][lab]
            h.update(_m.to_numpy(dtype=bool).tobytes())
            h.update(_u.to_numpy(dtype=bool).tobytes())
    _root = pathlib.Path(__file__).resolve().parent.parent.parent
    _one = _root / ONE_MIN_CSV
    _add({"1分足": [_one.stat().st_size, _one.stat().st_mtime_ns] if _one.exists() else None})
    for _p in (pathlib.Path(__file__), pathlib.Path(rl.__file__), pathlib.Path(iref.__file__)):
        h.update(_p.read_bytes())
    d = OBSERVE_DIR / "rank_resume" / h.hexdigest()[:16]
    d.mkdir(parents=True, exist_ok=True)
    return d


def _rank_resume_save(path: pathlib.Path, tf: str, auc: dict, nsample: dict) -> None:
    """その時間足の結果（分離力と独立な標本の数）を書く。一時の名前で書いてから名前を替える。"""
    import json as _json
    body = {"時間足": tf,
            "分離力": {c: {lab: {str(n): v for n, v in bn.items()} for lab, bn in by.items()}
                    for c, by in auc.items() if c.endswith(f"__{tf}")},
            "独立な標本の数": [[lab, int(n), t, int(v)] for (lab, n, t), v in nsample.items() if t == tf]}
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(_json.dumps(body, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _rank_resume_load(path: pathlib.Path, auc: dict, nsample: dict) -> None:
    """書き終わった時間足の結果を読んで、分離力と独立な標本の数に足す。"""
    import json as _json
    d = _json.loads(path.read_text(encoding="utf-8"))
    for c, by in d["分離力"].items():
        auc[c] = {lab: {int(n): float(v) for n, v in bn.items()} for lab, bn in by.items()}
    for lab, n, t, v in d["独立な標本の数"]:
        nsample[(lab, int(n), t)] = int(v)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:5969「"または 良い/悪いの片側の標本が10未満）＝黙って消さず記録（M2-3-4）")」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 6002〜6003行（rank_materials_for_regime）
直す前の文字:
~~~
    labels = {n: _regime_labels(win, n) for n in horizons}
    auc: dict = {}                                            # 列名 → {ラベル: {N: 分離力}}

~~~
直した後の文字:
~~~
    labels = {n: _regime_labels(win, n) for n in horizons}
    _ck_dir = _rank_resume_dir(win, cfg, cat_use, horizons, labels)   # ★工事 E＝続きの結果の置き場
    auc: dict = {}                                            # 列名 → {ラベル: {N: 分離力}}

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:6002「labels = {n: _regime_labels(win, n) for n in horizons}」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 6009〜6010行（rank_materials_for_regime）
直す前の文字:
~~~
    for _i_tf, tf in enumerate(use_tfs, 1):
        cfg_tf = dict(cfg)

~~~
直した後の文字:
~~~
    for _i_tf, tf in enumerate(use_tfs, 1):
        _ck = _ck_dir / f"{tf}.json"
        if _ck.exists():                                      # ★工事 E＝書き終わった時間足は読んで飛ばす
            _rank_resume_load(_ck, auc, nsample)
            print(f"  … 時間足 {tf} は前に書き終わった結果を読んだ（{_i_tf}/{len(use_tfs)} 本・続きから）", flush=True)
            continue
        cfg_tf = dict(cfg)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:6009「for _i_tf, tf in enumerate(use_tfs, 1):」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 6028〜6029行（rank_materials_for_regime）
直す前の文字:
~~~
            del grid
        del df

~~~
直した後の文字:
~~~
            del grid
        del df
        _rank_resume_save(_ck, tf, auc, nsample)              # ★工事 E＝この時間足の結果を書く

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:6028「del grid」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 6399〜6402行（selftest_rank_demand）
直す前の文字:
~~~
    return ng


def selftest_insp5(
~~~
直した後の文字:
~~~
    return ng


def selftest_rank_resume(exit_: bool = True) -> list:
    """T-r＝成績表の全走が、途中で落ちても続きから計算できるか（工事 E・口 --selftest-rank-resume・壊すプログラム b126 が使う）。

    ①止めずに走らせた結果と、2本目の時間足で落としてから走らせ直した結果が、並びまで同じ
    ②落ちた後に、書き終わった1本目の時間足のファイルだけが残る
    ③走らせ直すと、1本目を読んで飛ばす（読んだのは1本）
    ④材料が違えば、同じ置き場でも前の結果を読まない
    ★乱数を使わない（決まった式の4本値）。★本物の成績表と続きの置き場は触らない（一時のフォルダ）。
    """
    global OBSERVE_DIR
    import json as _json
    import tempfile as _tf
    ng: list = []
    n_bars = 6000
    idx = pd.date_range(SEARCH_START, periods=n_bars, freq="5min")
    _i = np.arange(n_bars, dtype=float)
    _c = 100.0 + 3.0 * np.sin(_i / 40.0) + 0.002 * _i
    bars = pd.DataFrame({"open": _c, "high": _c + 0.05, "low": _c - 0.05, "close": _c,
                         "volume": 1.0 + (_i % 7)}, index=idx)
    cfg = load_config(None)
    cat = build_catalog(cfg)[:6]
    tfs = ["5m", "1h"]
    g = globals()
    keep_dir, keep_bf, keep_load = OBSERVE_DIR, g["build_features"], g["_rank_resume_load"]
    loads: list = []

    def _bf_fail(win, cfg_tf, catalog=None):
        if cfg_tf["timeframes"] == [tfs[1]]:
            raise RuntimeError(f"T-r: 試しに {tfs[1]} で落とす")
        return keep_bf(win, cfg_tf, catalog)

    def _load_count(path, auc, nsample):
        loads.append(path.name)
        return keep_load(path, auc, nsample)
    full = again = None
    with _tf.TemporaryDirectory() as d:
        try:
            OBSERVE_DIR = pathlib.Path(d) / "full"
            full = rank_materials_for_regime(bars, cfg, cat, tfs=tfs)
            OBSERVE_DIR = pathlib.Path(d) / "resume"
            g["build_features"] = _bf_fail
            try:
                rank_materials_for_regime(bars, cfg, cat, tfs=tfs)
                ng.append("T-r: 2本目で落とせなかった（試しの仕掛けが効いていない）")
            except RuntimeError:
                pass
            g["build_features"] = keep_bf
            left = sorted(p.name for p in (OBSERVE_DIR / "rank_resume").glob("*/*.json"))
            if left != [f"{tfs[0]}.json"]:
                ng.append(f"T-r②: 落ちた後に残ったファイルが {left}（期待 ['{tfs[0]}.json']）")
            g["_rank_resume_load"] = _load_count
            again = rank_materials_for_regime(bars, cfg, cat, tfs=tfs)
            if loads != [f"{tfs[0]}.json"]:
                ng.append(f"T-r③: 走らせ直したときに読んだのが {loads}（期待 ['{tfs[0]}.json']）")
            if _json.dumps(full, ensure_ascii=False, default=str) != _json.dumps(again, ensure_ascii=False, default=str):
                ng.append("T-r①: 止めずに走らせた結果と、落としてから走らせ直した結果が違う")
            if not full.get("測れた列"):
                ng.append("T-r①: 作り物の4本値で、分離力を測れた列が0本（試しになっていない）")
            loads.clear()
            rank_materials_for_regime(bars, cfg, cat[:5], tfs=tfs)
            if loads:
                ng.append(f"T-r④: 材料が違うのに、前の結果を読んだ: {loads}")
        finally:
            OBSERVE_DIR, g["build_features"], g["_rank_resume_load"] = keep_dir, keep_bf, keep_load
    print(f"  T-r 途中で落ちても続きから計算する（工事 E）: ①結果が同じ ②1本目だけ残る ③1本目を読んで飛ばす ④材料が違えば読まない"
          f" ／ 測れた列 {(full or {}).get('測れた列')} 本 ／ ❌ {len(ng)} 件")
    if exit_:
        for x in ng:
            print(f"  ❌ {x}")
        raise SystemExit(1 if ng else 0)
    return ng


def selftest_insp5(
~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:6399「return ng」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7685行（selftest）
直す前の文字:
~~~
    ng += selftest_rank_demand(exit_=False)          # T-f（需給を成績表に足す差分の口・設計書 demand-in-ranking-20260907）

~~~
足す文字:
~~~
    ng += selftest_rank_resume(exit_=False)          # T-r（途中で落ちても続きから計算する・工事 E）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7685「ng += selftest_rank_demand(exit_=False)          # T-f（需給を成績表に足す差分の口・設計書 demand-in-ranking-20260907）」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 7737行（<モジュール直下>）
直す前の文字:
~~~
        selftest_rank_demand()                        # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）

~~~
足す文字:
~~~
    if "--selftest-rank-resume" in sys.argv:          # T-r だけを数秒で（工事 E・壊すプログラム b126 が使う）
        selftest_rank_resume()                        # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:7737「selftest_rank_demand()                        # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）」
状態: 確定

#### 実装 8
対象のファイル: .claude/breaks/b126_rank_resume_save_off.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 成績表の全走で、時間足を1本 計算し終えたら結果を書く所（_rank_resume_save）を外すと、自己テスト T-r が「落ちた後に書き終わった時間足のファイルが残らない」で落ちた
# EXPECT_MSG: ❌ T-r②
# b126 — observe_diag.rank_materials_for_regime の、時間足の結果を書く行を外すと、T-r が落ちるか（工事 E・2026-10-03）
#   守っているもの＝完成の条件 #1（観察の道具の自己テスト T-r が、途中で落ちても続きから計算できるかを見ている）
#   壊し方＝時間足の結果を書く行（_rank_resume_save の呼び出し）を消す（直す前と同じ＝最後にまとめて書くだけになる）。
#   期待＝observe_diag.py --selftest-rank-resume の T-r② が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

OD="$PR/observe_diag.py"
guard "$OD"

python3 - "$OD" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        _rank_resume_save(_ck, tf, auc, nsample)              # ★工事 E＝この時間足の結果を書く\n'
if s.count(old) != 1:
    raise SystemExit("[b126] 壊す対象の行が1か所でない: " + old.strip())
new = '        pass  # b126 が壊した（時間足の結果を書かない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$OD" --selftest-rank-resume
finish

~~~
根拠の抜き書き: .claude/breaks/b125_hindsight_osc_off.sh:1「#!/bin/bash」
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 8 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 時間足1本ごとに結果を書く | 全走は時間足ごとのループで、1本の結果がまとまる所が自然な区切り | 材料1種ごとに書く。捨てた理由＝書く回数が6,000回を超え、遅くなる |
| 2 | 続きの置き場を中身の指紋で決める | 違う札・違う材料の結果を混ぜないため。名前や版の名前だけでは、中身の違いを見落とす | 札の版の名前で決める。捨てた理由＝式や元データが変わっても名前が同じだと混ざる |
| 3 | 一時の名前で書いてから名前を替える | 書いている途中で落ちても、書きかけのファイルを読まないため | そのまま書く。捨てた理由＝書きかけを次に読むおそれ |
| 4 | 書き終わった後も置き場を消さない | 走らせ直したときにすぐ終わる・中身を後で見られる | 終わったら消す。捨てた理由＝成績表を書く所で落ちたときに、また全部 計算することになる |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=723abeeaa657149b gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b126_rank_resume_save_off.sh` | #1 | 時間足の結果を書く行（_rank_resume_save の呼び出し）を外すと、T-r が T-r②（落ちた後に1本目のファイルが残らない）で落ちる |
| `—` | #2 | 壊すプログラムは付けない（この工事は T-f の関数を変えない・前からの壊すプログラム b39・b40 が見ている） |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 指紋に入れ忘れた入力が変わると、古い結果を混ぜる | 指紋には、設定・材料の名前・先を見る本数・期間・5分足の中身・札の中身・1分足の元データ（大きさと時刻）・3つのコード（観察の道具・札の部品・参照表）を入れた。ほかに結果を変える入力を見つけたら、指紋に足す |
| 2 | 置き場のファイルが増え続ける | 1回の全走で11本・約1MB。増えすぎたら、まこさんに確かめてから消す |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる | 30秒未満 | 当てる道具は1秒未満で終わった（工事 C・D） |
| 自己テストと壊すプログラム | それぞれ1分未満 | 4-14 |
| G2 → H2 | 約30秒 → 約5分 | 10/02 の取り直し |
| まこさんの承認 | 2回（当てる前に1回・当てた後に SPEC を実物から作り直した設計書に1回） | 4-4 の2（教訓 L-655） |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝成績表の道具が、2時間を超える計算の結果をメモリにだけ持ち、最後にまとめて書く作りだからです（私が 8/22 に設計し、2時間14分かかると分かった後も直さなかった）。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は動きません。動くのは、全走が途中で落ちたときに失う時間だけです。

**③ root か symptom か**＝root です。落ちる理由（走らせ方・PC・私の誤り）を1つずつ塞ぐのではなく、どの理由で落ちても計算が残る形にします。

**④ ベースアップ**＝長い計算を区切りごとに書いて続きから再開する形（チェックポイント）は、長い学習や計算で一般的なやり方です。区切りは、この道具の時間足のループにしました。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。数字を足しません（自己テストの作り物の4本値の式の数字だけで、成績表には入りません）。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝成績表の全走を、途中で落ちても続きから計算できる形にする（14a の工事 E）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。条件をつなぐものではなく、成績表の書き方と読み方の直しです |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 値を選びません。成績表の中身は変わりません |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **指紋に入れていない入力が変わったら** | 古い結果を混ぜます。入れていない入力（例＝指標を計算する外の部品の版）が変わったときは、置き場を消してから走らせ直します |
| **置き場のファイルを手で書き換えられたら** | 読んでしまいます。置き場は results の下（git の対象外）で、書くのはこの道具だけです |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=f115d814c078186d gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝2本（観察の道具・壊すプログラム b126）を【7-8】に書いた。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝observe_diag.py）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム b126 の1本（NEW_FILE）。手本は工事 D の壊すプログラム b125（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝10/02 に全走が2回 途中で止まり、何も残らなかった。この工事は、どの理由で落ちても計算が残る形にする。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 新しい部品は続きの部品3つ（_rank_resume_dir・_rank_resume_save・_rank_resume_load）。H2 が走らせる案には入らない（成績表の書き方と読み方だけで、案の判定には使わない）。未来参照の検査で注記の無い先読みは0件。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 直すファイルの行番号を指す文書は、この工事の実装の指示だけで、いまの実物から道具が作った。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、それぞれが探す行の文字の数が、この工事の前と後で同じことを案を作る道具が数えた（4-13 の3・照らした組は案の冒頭）。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムは b126 を1本 作る（結果を書く行を外すと T-r が T-r② で落ちる＝案を作る道具が同じ壊し方で確かめた）。結果の置き場は、壊すプログラムが走らせる自己テストの中で一時のフォルダにしてある。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 触る関数は、全部 DESIGN_CONTRACT の impl_functions に書いた（【7-8】・案を作る道具が照合の道具と同じ数え方で数えた）。<モジュール直下>・_rank_resume_dir・_rank_resume_load・_rank_resume_save・rank_materials_for_regime・selftest・selftest_rank_resume。must_use に、本体が呼ぶ続きの部品3つと、T-r が呼ぶ本体を書いた。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足す旗は --selftest-rank-resume（4-9）。完成の条件 #1 のコマンドで通る。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2f-rank-resume-20261002）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己テスト＝観察の道具に T-r を足し、全部の自己テスト（selftest）からも呼ぶ。案を作る道具が当てた後の道具を本物に書かずに走らせ、通った。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 自己テスト T-r が通る（途中で落ちても続きから計算でき、結果が同じ） | `python3 scripts/priority_rebuild/observe_diag.py --selftest-rank-resume` | 実経路 | 時間足の結果を書く行（_rank_resume_save の呼び出し）を外すと、T-r が T-r②（落ちた後に1本目のファイルが残らない）で落ちる | `b126_rank_resume_save_off.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝成績表の全走で、時間足を1本 計算し終えたら結果を書く所（_rank_resume_save）を外すと、自己テスト T-r が「落ちた後に書き終わった時間足のファイルが残らない」で落ちた |
| 2 | 需給の自己テスト T-f が今までどおり通る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-rank-demand` | 実経路 | 壊すプログラムは付けない（この工事は T-f の関数を変えない・前からの壊すプログラム b39・b40 が見ている） | `—` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=0c720203bfa6b962 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/observe_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `_rank_resume_dir` | 5980 |
| `_rank_resume_save` | 6007 |
| `_rank_resume_load` | 6019 |
| `selftest_rank_resume` | 6465 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 176件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=61ee443e3a44d448 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/observe_diag.py",
  "_impl_file の意味": "照らす相手は実在するファイル。成績表を作る本体が在る観察の道具を照らす。",
  "impl_functions": {
    "scripts/priority_rebuild/observe_diag.py": [
      "<モジュール直下>",
      "_rank_resume_dir",
      "_rank_resume_load",
      "_rank_resume_save",
      "rank_materials_for_regime",
      "selftest",
      "selftest_rank_resume"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数。当てる前と後の差の行を、当てた後のコードの関数に当てはめて、案を作る道具（_labelE_draft_build.py）が数えた。",
  "self_check_calls": [
    "_rank_resume_dir",
    "_rank_resume_save",
    "_rank_resume_load",
    "selftest_rank_resume"
  ],
  "_self_check_calls の意味": "実装の後の観察の道具に在るはずの、工事 E の関数の名前。",
  "must_use": {
    "rank_materials_for_regime": [
      "_rank_resume_dir",
      "_rank_resume_save",
      "_rank_resume_load"
    ],
    "selftest_rank_resume": [
      "rank_materials_for_regime"
    ]
  },
  "_must_use の意味": "成績表の本体が続きの部品3つを呼び、自己テスト T-r が本体を呼ぶ（案を作る道具が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は成績表の書き方と読み方を足すだけ。外から読む一覧（候補・法則・成績表の順位・範囲の鍵）は読まない。",
  "generated_from": {
    "impl_functions": "当てる前と後の差の行（_labelE_draft_build.py が数えた）",
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
  "--selftest-insp5",
  "--selftest-rank-demand",
  "--selftest-rank-resume"
 ]
}
```

<!-- ACC_SPEC_END -->

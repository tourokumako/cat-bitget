<!-- ARC iter="m2f2-catch-rank-stages-20260927" -->

# 設計書｜M2-F-2＝測る道具（regime_r9_diag.py）に「捉えた割合」を足し、順位表と落ちた候補をファイルに出し、段ごとに測る口と段4 の差し戻しの口を作り、乱数を消し、試行を累積に数える（1変更）

TARGET: scripts/priority_rebuild/regime_r9_diag.py, .claude/breaks/b97_demand_not_attached.sh
NEW_FILE: .claude/breaks/b113_catch_share_broken.sh, .claude/breaks/b114_default_rng_back.sh, .claude/breaks/b115_record_run_renamed.sh, .claude/breaks/b116_dropped_file_not_written.sh, .claude/breaks/b117_stage_recipe_no_entry.sh
MODEL: .claude/breaks/b104_atr1h_own_tf.sh

REQUIREMENTS: まこさんの決定（下の §0）と、`engine_tuner_milestones2.md` の §2.2（レンジ判定の検索方法）。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書はプログラムが作ります。**手で書いたのは、元データ `.claude/ratchet/acceptance_src.json` の5つ（何を作るか・なぜ作るか・組み方・やらないこと・決めてほしいこと）だけです。残りは正本から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --write`。手で書き換えられていないかの検出＝`--verify`。

## 0｜まこさんの決定（逐語）

> ★この工事への決定（逐語）
> 修正は全部やる（2026-09-28＝監査 CP48 の修正79件を全部〔Critical・Major・Minor・Process〕当てる）
> 決めることは、CCのおすすめの通りでOK（2026-09-28＝決めてほしいことの1〔段2c で C3 を掛けない・M2-F-13 の文を揃える〕・2〔段3 は続く本数だけを探し、保つ上限と緩め幅は段5 で開く・M2-F-14 の文を揃える〕と、監査が工事の外とした生成器の段2a の出る線の向きを next_step §6 に積み M2-F-14 の前に直す、を私の案のとおりにする）
> １は平均でOK（2026-09-27＝順位をつける「③実はトレンドだった割合の低さ」は、先24本と先288本の2つの点数の平均で取る。第二キーの捉えた割合も同じ扱い）
> 了解。進めて良い（2026-09-27＝骨組み2〜5＝書き先 results/priority_rebuild/regime_r9/・口3つ〔--stage・--top・--sweep〕・乱数の撤去・--nan-check を私の案のとおり進める）
> OK（2026-09-27＝この設計書の読むもの宣言17件への OK）
> ★束3 と余白とリスク8 の決定（逐語）
> 上記でOK。（2026-09-24＝この設計書に M2-F-15〔段4 の差し戻しの口〕を含める。M2-F-7〔渡す本数10本〕の書き込みは M2-F-4 の実装と同じ回に行う）
> とりあえず１０本にする／結果を見て変更すると思う（2026-09-18＝上位を次の段へ渡す本数）
> 余白の直し方→C（2026-09-27＝動く線を使う走行だけ余白を長くする。段を測る道具は M2-F-2 で stage_warm(et.WARM) を使う形にする＝m2_todo の M2-F-2 の注意）
> 案1（2026-09-27＝M2-E-4e のリスク8＝BB幅 の動く線の材料の値なしの本数を、M2-F-2 の設計書で数える口を作る）
> ★前から引き継ぐ決定（逐語）
> 一旦この検索方法がベストということで記録しておいて（2026-09-01＝§2.2 レンジ判定の検索方法。成績＝R9 の3つ・第一キー＝実はトレンドだった割合の低さ・第二キー＝捉えた割合・net は M2-L まで使わない・試行は累積・落とした候補は全部 出す）
> じゃあ、まず１点でつくる（2026-09-11＝閾値の分位は1点）
> 乱数は禁止用語にするレベル。絶対に使うな（2026-09-09・恒久67番）
> １と２は今のままでOK（2026-08-29＝正解の印〔強さ・ER〕と先読みの本数〔24・288〕は変えない）
> ヌケモレがおおいから、手で書かざるを得ない部分以外は自動生成にしろよ。（2026-09-09・恒久69番）
> 2-Eと２−Fの進行が遅すぎるので、修正は極力まとめて効率的に進めること（2026-09-21）
> とにかく、不具合はすべて直すように（2026-08-21・恒久59番）
> コードを直したら、その行を探している壊すプログラムが在るかを、必ず grep（2026-09-16・L-605）

## 1｜概要

M2-F（段ごとの選抜＝レンジ判定の候補を測って並べ、上位10本を次の段へ渡す）の採点係になるように、測る道具 regime_r9_diag.py を1本だけ直します。直すことは6つです。1つ目、捉えた割合（正解がレンジ〔強さが偽 ∧ 使える〕のバーのうち、判定が真の割合）と、当たった割合（1−③）と、正解レンジの割合を、いまの①③に足して出します。式は M2-A で決まった印（強さ・先24本／288本・変えない）に合わせます。2つ目、順位をつけます。第一キー＝③実はトレンドだった割合の低さ（先24本と先288本の平均＝まこさん決定 2026-09-27「１は平均でOK」）、第二キー＝捉えた割合（同じく平均）の高さです。3つ目、順位表と落ちた候補（組めない・測れない・束が無い・関所で拒否・成績下位の5つの場面）を、画面だけでなくファイル（results/priority_rebuild/regime_r9/ に段の名前と日時つき）に書きます。4つ目、段ごとに測る口を作ります。--stage <段> はその段の候補を全部 束にして測り、--top <前の段の順位表> は上位10本（本数は設定の stage_keep_of）と候補を掛け合わせ、--sweep <順位表の行> は段4 の差し戻し（確定した束の1枠を、その段の全候補で入れ直して1周し、良くならなくなるまで繰り返す＝M2-F-15）を行います。5つ目、乱数を消します。--build N は sample_regime_build（判定の束だけを、成績表の順位 × 案の番号の決まった並びで組む関数）だけで束を組み、sample_structure と default_rng をこの道具から消します。あわせて net を既定で測らない形（--trades を付けたときだけ測る）にし、--seed を消し、走行の目的（--purpose search か check）を必ず書かせて tuner_stats.record_run で試行を数えます（恒久の決まり24番・§2.2「試行は累積」）。6つ目、--nan-check の口を作ります。stage_warm の余白で読んだ値決め窓・確認窓について、BB幅 の動く線の材料の値なしの本数を数え、窓の始まりの後に値なしが在れば止まって まこさんに出します（まこさん決定「案1」）。データを読む余白は stage_warm(et.WARM) にします（まこさん決定「余白の直し方→C」の続き・m2_todo の M2-F-2 の注意）。売買は1件も回さないので、net は動きません。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

| 何を測ったか | コマンド | 結果 |
|---|---|---|
| 捉えた割合が道具に無い | `grep -c '捉えた' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py` | 15（終了コード 0）／読み方＝零件。検索方法の第二キー（捉えた割合）が測れない |
| 順位をつける処理が無い | `grep -c 'rank_key' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py` | 4（終了コード 0）／読み方＝零件。並べて上位を渡す段の選抜ができない |
| 結果をファイルに書く処理が無い | `grep -c 'write_text' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py` | 2（終了コード 0）／読み方＝零件。画面に印字するだけで、次の段が前の段の上位を機械で読めない |
| 乱数が残っている | `grep -n 'default_rng' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py` | 696:        if _nm7 in ("default_rng", "sample_structure", "random", "RandomState"):（終了コード 0）／読み方＝在る。乱数は使わない、の決まり（禁止用語のレベル）に反したまま |
| 試行を累積に数える口を呼んでいない | `grep -c 'record_run' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py` | 7（終了コード 0）／読み方＝零件。試行は累積して数える、の共通の決まりを満たさない |
| 束1本の時間の実測（M2-F-1） | `grep -n '実測＝8.704秒' /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/session_worklog_20260927.md` | 441:- **実測＝8.704秒（rc=0）**。内訳の注意＝出力の1行目が「[キャッシュ] 前に作ったものを再利用した（指紋 bc0dfb5bc869a22b）」＝データの読み込みはキャッシュを再利用した。キャッシュが無い初回は読み込みが足される（土台の実測＝読み込み 99〜103秒・milestones2:2010 の前置き8）。（終了コード 0）／読み方＝固定のレシピ一本を、玉を測らない口で走らせた実測が記録に在る。段の走行の時間の見込みの材料 |
| 直すファイルに commit されていない差の塊の数 | `git diff HEAD -- v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py ／ grep -c '^@@'` | 11（終了コード 0）／読み方＝承認の前は差が無い。照合が数える触った関数は、この工事で直すものだけになる |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

<!-- ACC_MATERIALS_START hash=ba987a5abd7ee17e gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`indicator_switch.json`・`signal_families.json`・`search_limits.json`。

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

<!-- ACC_RANKING_START hash=31b989fc34f0fa0c gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`material_ranking.json`。

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

<!-- ACC_RANDOM_START hash=b77eb360eebdb373 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`engine_tuner_gen.py` を構文の木で読んだ結果（コメントの中の文字は数えません）。

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

**★この工事で0にするのは、場面の判定の束を組む所だけです。**入口は M3、出口は M4 で外します（まこさんが決めた順番）。

<!-- ACC_RANDOM_END -->

## 3｜目標と、やらないこと

### 3-1 やらないこと（1件ずつ・理由と出どころ）

| # | やらないこと | 理由 | 出どころ |
|---|---|---|---|
| 1 | 実行器・生成器・法則・成績表・審判・正解の印・設定の置き場を直すこと | 1変更＝regime_r9_diag.py だけ。候補・束・余白・窓の本数は生成器の関数を呼ぶ（書き写さない） | next_step §0-2 の10番・恒久69番 |
| 2 | M2-F-7（渡す本数10本）をこの設計書で書くこと | 設定ファイルの1行で承認の相手ではなく、M2-F-4 の実装と同じ回に書くと H2 の印の取り直しが1回で済む | まこさん OK 2026-09-24（束3） |
| 3 | 途中の束を審査（G7）に掛けること | 1つの枠だけでは法則を満たせない。G7 は完成した束（段3）で掛ける＝M2-F-14 | 中身13 の (j)・milestones2 の M2-F-14 |
| 4 | 順位の鍵を、先24本か先288本のどちらか1つにすること | まこさんの決定は平均 | まこさん決定 2026-09-27「１は平均でOK」 |
| 5 | net で並べること・net を既定で測ること | net は M2-L まで使わない。判定の成績は3つの割合で測る | まこさん決定 2026-09-01（§2.2） |
| 6 | 段5（詰め＝勝った値の前後を細かく）の口を作ること | 段5 は M2-K の担当（§5-1 の置き先の規則） | m2_todo の M2-F のまとまりの分け方 |
| 7 | 候補の母集団を変えること（MMI・需給・曜日を足す など） | 候補は build_stage_candidates が作る。母集団は M2-C・M2-D の担当 | milestones2 §2.2 の表 |
| 8 | 段3 の包み（hysteresis の off）を生成器の関数で作ること | sample_regime_build は案の番号から束を丸ごと組む形で、上位10本 × 候補の掛け合わせには使えない。だから同じ形（水準を1段 緩めた any・_loose_q_fixed を呼ぶ）をこの道具に書く＝2か所目になる（正直に塞げないものに書いた） | engine_tuner_gen.py:3242 の sample_regime_build の作り |
| 9 | --nan-check を完成の条件に載せること | 実データの値なしの本数は実装の前に分からない。値なしが在れば rc=1 で止まって まこさんに出す口なので、承認の門で走らせる条件にすると、データ次第で承認が止まる。走らせるのは M2-F-5（実走）と M2-F-13 の前 | まこさん決定「案1」・恒久64番 |
| 10 | 順位表の JSON を git に入れること | 実験の出力は results/ 配下（commit 対象外）の決まり | CLAUDE.md のコミット禁止（results/ 配下すべて） |

### 3-2 決めてほしいこと

| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 段2c で C3（実データで動きがほぼ同じ指標は片方を外す）を掛けるか。M2-F-13 の中身は「C2（段2a と同じ系統は不可）と C3（動きが重なる組は落とす）で落とします」と書き、法則ファイルの C3 は「使う段: M2-G」で機械が読む判定を持たない（G7 でも落ちない）。この設計書の段の口は C2・C3 を掛けない | ★まこさん決定 2026-09-28（逐語「決めることは、CCのおすすめの通りでOK」）＝この案で決まった。C3 は M2-G に任せ、段2c では掛けない（C2 は、段2c の候補が法則 R6 の名指しした family だけで段2a の系統と重ならないので、候補の作りで満たす）。M2-F-13 の中身の文も、この形に揃える（m2_todo.json → gen_regime_kb.py --write todo）。★M2-G は保留なので、再開するまで C3 はどの段でも掛からない | engine_tuner_milestones2.md の M2-F-13・regime_laws.json の C3（監査 CP48） |
| 2 | 段3 で何を探すか。§2.2 の段3 は「成立の連続本数と解除の緩め幅・n＝state_hold_bars_range の範囲／緩め幅＝_loose_q の分位差」と書き、M2-F-14 は「streak（続く本数 n＝3〜24 の22通り）と hysteresis（解除の緩め幅・保つ上限 24〜288）を掛けて・測った本数＝10本 × 22通り」と書く。この設計書の段の口は streak の本数だけを候補にし、保つ上限は候補の番号で決まる1つの値、緩め幅は隣の段の1つに固定する＝保つ上限の範囲の大半と、ほかの緩め幅は段3 で1度も試されない | ★まこさん決定 2026-09-28（逐語「決めることは、CCのおすすめの通りでOK」）＝この案で決まった。M2-F-14 の本数（10本 × 22通り）のまま進め、保つ上限と緩め幅は段5（詰め）で範囲から開く。M2-F-14 の中身の文を、この形に揃える（m2_todo.json → gen_regime_kb.py --write todo） | engine_tuner_milestones2.md の §2.2 の段3・M2-F-14（監査 CP48） |

## 4｜設計の中身

**★この節の項目は、正本 `design_section_sources.json` の3つの出どころ（うちの正本・外の標準・まこさんが過去に指摘したこと）118件を、1件も余さず引き受ける形に決めたものです。**割り当て＝`design_section_map.json`。検算＝`gen_design_sections.py --check`。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

**この項目に書くこと**＝何を作るのか／どういう流れで動くのか／何ができるようになるのか／完成したとき何が出るのか。★項目に分けない。ここだけ読めば全体が分かる状態にする。★★必ず「なぜこの形にするのか」を、ほかの形と比べた実測の数字で書く（この形を取らなかったら何通り・何時間 掛かるか）。★なぜ必須か＝まこさん指摘 2026-09-10「2-2の設計思想は、総当りで組合わせロジックを出すと数百年かかるので、段ごとに絞り込んでいくという方法ということを、このセッション内で何度も言ってるのに、毎回抜けるから、いい加減にしてほしい」。私は「段＝枠を埋める順番」と読み、「段＝候補を絞る段階」という思想を毎回 落とした。

**この仕組みは、M2-F の段ごとの選抜の採点係を作るものです。**レンジ判定の候補（束）を測って3つの割合で並べ、上位10本を次の段へ渡し、落ちた候補を全部 残します（§2.2・まこさん決定 2026-09-01）。

**①いま何が起きているか。**測る道具（regime_r9_diag.py・354行）は、①レンジと言った割合と③実はトレンドだった割合を出すだけです。捉えた割合（第二キー）が無く、順位という考えが無く、結果は画面に印字するだけでファイルに残らず、--build には乱数（default_rng・324行）が残り、試行は累積に数えられていません（record_run 0件）。落ちた候補のうち2つの場面（組めない・関所で拒否）は記録がどこにも残りません。

**②どう変えるか。**中身13（milestones2 の M2-F-2）のとおり6つを直します。(a)捉えた割合・(b)当たった割合（1−③）・(f)正解レンジの割合を足す。(g)第一キー＝③の低さ（先24本と288本の平均・まこさん決定「１は平均でOK」）・第二キー＝捉えた割合の平均で並べる。(h)(i)順位表と(l)落ちた候補の5つの場面をファイルに書く。(j)(k)段ごとに測る口（--stage・--top）と、M2-F-15 の差し戻しの口（--sweep）を作る。(c)(d)net を既定で測らず、束は sample_regime_build だけで組み、乱数を消す。(e)--purpose を必ず書かせて record_run で試行を数える。あわせて --nan-check（リスク8・まこさん決定「案1」）と、余白の stage_warm 化（まこさん決定「余白の直し方→C」の続き）を入れます。

**③なぜこの形か。**選抜は「測って・並べて・上位を渡して・落ちた候補を残す」の繰り返しで、その全部が1つの道具に無いと、段のたびに手作業と写し間違いが入ります。候補を作る関数（build_stage_candidates・build_width_candidates）と束を組む関数（sample_regime_build）は生成器に完成済みなので、この道具はそれらを呼ぶだけにし、絞りや候補の作り方を書き写しません（恒久69番）。

**完成したときに出るもの。**regime_r9_diag.py --selftest の⑥〜⑩の行（捉えた割合の既知答え・乱数0件・record_run・落ちた候補の5つの場面・並べる鍵）。固定のレシピの走行で、順位表と落ちた候補のファイルが results/priority_rebuild/regime_r9/ に書かれます。売買は0件・net はゼロのままです。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

**この項目に書くこと**＝このプログラムを呼ぶ相手（人か、別のプログラムか）と、出た結果を次に使う相手。やること／やらないことの線。

**誰が動かすか。**私（CC）が M2-F-5（実走）と M2-F-8〜15（段の走行）でコマンドから動かします。走らせる前にフロー宣言（時間の見込み・過去の実測の引用）を書きます（恒久60〜62番）。

**誰が結果を使うか。**次の段の走行（--top が順位表のファイルを読む）と、M2-F-9（段1 の結果を数える）と、M2-F-10（まこさんが3つを決める材料）と、M2-G・M2-H（重ねる・組み上がる）です。試行の記録は tuner_stats（DSR・PBO の N）が読みます。

**線。**直すのは regime_r9_diag.py の1本だけです。生成器（候補と束を組む関数）・実行器（列を作る関数）・法則・成績表・審判・正解の印・設定の置き場は読むだけで、1文字も変えません。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

**この項目に書くこと**＝関数やコマンドの取り決め（引数・戻り値・その意味・呼んでよい相手）。

**捉えた割合（r9_catch_share）。**受け取る＝判定の列・強さの印・使える印。出す＝正解がレンジ（強さが偽 ∧ 使える）のバーのうち判定が真の割合（0〜1）。正解が0本なら nan（嘘の0を出さない）。

**正解レンジの割合（r9_range_share）。**受け取る＝強さの印・使える印。出す＝使えるバーのうち強さが偽の割合（約50%・一緒に出す＝前置き9）。

**並べる鍵（rank_key）と順位（rank_rows）。**受け取る＝束の行の一覧。出す＝第一キー＝③の2つの先読みの平均の低さ・第二キー＝捉えた割合の平均の高さで並べ、順位を書き込む。keep より下の行は消さずに「成績下位」の場面を付ける。測れない行（①が無い行）は最後に置く。

**ファイルに書く（write_outputs）。**受け取る＝札（段の名前）・行の一覧・落ちた候補の一覧。出す＝rank_<札>_<日時>.json と dropped_<札>_<日時>.json（results/priority_rebuild/regime_r9/）。画面に場面の内訳を出す。

**段の口（run_stage）。**受け取る＝--stage の段の名前と（段1 以外は）--top の順位表。出す＝前の束 × 候補の全部の束の順位表・落ちた候補・record_run の記録。束の行には 内側（条件の一覧）・枠（各条件の段の名前）・包み（段3 の持続と保つ上限）を残す＝次の段と差し戻しが機械で読める形。

**差し戻しの口（run_sweep）。**受け取る＝順位表の行（内側・枠・包み）。出す＝周ごとの順位表と、良くならなくなった時点の最終の束。

**値なしの口（run_nan_check）。**受け取る＝なし（段2c の動く線の候補を自分で作る）。出す＝BB幅 の動く線の材料の、値決め窓・確認窓の値なしの本数。窓の始まりの後に値なしが在れば終了コード1。

### 4-6 制約（従う決まりの全件と、その出どころ）

**この項目に書くこと**＝決まりを1件も落とさずに並べ、どれをどの工程で使うかを書く。動かせないもの（承認済みの設定・取引所の仕様）も。

| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 成績＝R9 の3つ・第一キー＝③の低さ・第二キー＝捉えた割合・net は M2-L まで使わない | まこさん決定 2026-09-01（§2.2） | 捉えた割合を足し、net を既定で測らない（--trades を付けたときだけ） |
| 順位の数字は2つの先読みの平均 | まこさん決定 2026-09-27「１は平均でOK」 | rank_key＝③と捉えた割合の nan を除いた平均。番人⑩と壊すプログラム b113 |
| 乱数は使わない | 恒久67番 | sample_structure と default_rng をこの道具から消す。番人⑦（構文木で見る）と b114 |
| 走行の目的を必ず書く（道具の確認は check） | 恒久24番・違反の記録 #20 | --purpose search／check を必須にし、record_run に渡す。番人⑧と b115 |
| 試行は累積して DSR・PBO に数える | §2.2 の共通の決まり | 測る走行の全部で record_run を呼ぶ（search＝累積・check＝確認の帳簿） |
| 落とした候補は全部 出す | §2.2 の共通の決まり | 5つの場面を dropped_*.json に書く。番人⑨と b116 |
| 正解の印と先読みの本数は変えない | まこさん決定 2026-08-29「１と２は今のままでOK」 | observe_diag._regime_labels の「強さ」と _regime_horizons をそのまま使う（既存の⑤の番人が守る） |
| 未来のデータを使わない | cat_requirements §4.6 の H2 | 式は列の平均だけ（未来参照を足さない）。既存の④の番人（shift(-)・center=True を構文木で見る）がこのファイルを見張る |
| 値段に依存しない | cat_requirements §4.6 の H6 | 3つの割合は全部 0〜1 の比 |
| 同じ判定を2か所に書かない | 恒久69番 | 候補＝build_stage_candidates／束＝sample_regime_build／余白＝stage_warm／窓の本数＝pre_win_bars を呼ぶ（書き写さない）。★例外＝段3 の包み（下のやらないことの8） |
| 審判に触れない | cat_requirements §4.6 の H13 | score.py は import して呼ぶだけ（r9_trades は1文字も変えない） |
| 1変更 | cat_requirements §4.6 の H16 | 「M2-F の採点係を作る」の1つ。束3 で H16 を満たさないことは まこさん OK 2026-09-24 で決定済み（捨てるものに明記） |
| コードを直したら、その行を探す壊すプログラムを grep | L-605 | なぜ作るかの表の後に grep（当たった壊すプログラムが探す行は消さない＝4-13 の7） |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

**この項目に書くこと**＝主要な部品を挙げ、それぞれが何に責任を持つかを書く。部品どうしの協調も。

| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| r9_catch_share・r9_range_share | 捉えた割合（正解0本なら nan）と正解レンジの割合 | **新設**（実装の指示 4） |
| rank_key・rank_rows | 並べる鍵（2つの先読みの平均・まこさん決定）と順位・成績下位 | **新設**（実装の指示 4） |
| write_outputs・OUT_DIR・DROP_KINDS | 順位表と落ちた候補のファイル（5つの場面） | **新設**（実装の指示 4） |
| _q50_width_cond・_loosened_off・_wrap_bundle・_load_top・_stage_recipe・_record | 段1 の帯・段3 の包み（hysteresis）・前の段の上位の読み込み・束だけのレシピ・試行の記録 | **新設**（実装の指示 7） |
| run_stage・run_sweep・run_nan_check | 段の口・差し戻しの口・値なしの口 | **新設**（実装の指示 7） |
| _nanmean | 並べる鍵の平均（nan を除く） | **新設**（実装の指示 4） |
| _row（measure の中） | 当たった・捉えた・正解レンジの列を足す | 直す（実装の指示 5） |
| measure | 関所（G5 ほか）の拒否を行として残す | 直す（実装の指示 6） |
| _print_rows | 順位と新しい列を画面に出す | 直す（実装の指示 8） |
| main | --trades・--purpose・--stage・--top・--sweep・--nan-check・stage_warm・sample_regime_build・record_run・ファイル書き | 直す（実装の指示 11〜16） |
| selftest の⑥〜⑪ | 捉えた割合の既知答え・乱数0件・record_run・落ちた候補の5つの場面・並べる鍵・段の口の束 | 直す（実装の指示 9・10） |
| b113〜b117 | 番人⑥⑦⑧⑨⑪を壊して測る | **新設**（実装の指示 18〜21・24） |
| b97 | 固定のレシピの需給の列の番人（AUDIT-5）を新しい旗で測る | 直す（実装の指示 22・23） |

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

**この項目に書くこと**＝工程の順番と、工程の間で何を渡すか。組み方の根拠（何の法則で決めるか）も。

1. 当てる道具（apply_audit_fix.py --design）で実装の指示を当て、壊すプログラムの新しいファイル（実装の指示 18〜21・24）を Write ツールで書き、b97 を実装の指示 22・23 のとおり Edit ツールで直します（壊すプログラムは当てる道具の NEVER_WRITE のため）。
2. 構文を確かめ、regime_r9_diag.py --selftest を走らせ、⑥〜⑪の行を見ます。
3. 壊すプログラム b113〜b117 を1本ずつ測ります（run_breaks.py --measure-only）。b97 は m2e2-cp36-major-20260914 の控えの設計書で --measure-only --only b97_demand_not_attached.sh を測ります。
4. M2-F-7＝search_limits.json の stage_keep_range の hi に 10 を書き、G2 → H2 の順で印を取り直します（設定は H2 の対象のため・約6分半）。
5. ★固定のレシピ（完成の条件 #6）は、ここではまだ走らせません（監査 CP48）。7-8 の SPEC と 7-7 の定義の行は直す前の実物から作られているので、実装の後は設計↔実装ゲート（require_design_contract_before_run.sh の --diff）が --selftest 以外の走行を止めます。gen_acceptance.py --write で設計書を作り直し（SPEC と定義の行を実物から取り直す）、verify_design_contract.py --diff が齟齬0件なのを確かめて、2回目の承認をお願いします。
6. 2回目の承認の後に、固定のレシピを --purpose check で走らせ（python3 regime_r9_diag.py --recipe recipes/r9_demand_fixture.json --purpose check）、順位表と落ちた候補のファイルが書かれることを見て、①③を M2-F-1 の実測（①5.30%・③50.3%／51.4%）と並べて貼ります。
7. 実装の監査（6段の⑤）に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

**この項目に書くこと**＝実際の1件が、入口から出口までどう通るか。★読み手が設計を確かめられる唯一の欄。

**通しの例1（捉えた割合の既知答え・合成データ）。**バーが8本。正解の印＝強さが真（トレンドだった）は 1・3・5・7本目、使える印は全部 真とします。正解がレンジのバー＝2・4・6・8本目の4本です。判定が 2・4本目だけ真なら、捉えた割合＝2 ÷ 4＝0.5。判定を反転（2・4本目以外を真）すると 0.5＝1 − 0.5。正解の印が全部 真（レンジが0本）なら nan です。

**通しの例2（並べる鍵）。**束Xの③が 先24本 48%・先288本 52%（平均 50.0%）、束Yが 50%・49%（平均 49.5%）。第一キー＝平均の低さなので Y が上です（まこさん決定「１は平均でOK」の実例そのまま）。keep＝1 なら X の行に「成績下位」が付き、行は消えません。

**通しの例3（段の口）。**--stage stage1 は、帯（W% が q50 より上）∩ 段1 の候補（いま336本）の束を336本 作って測り、rank_stage1_<日時>.json に順位つきで書きます。次に --stage stage2a --top rank_stage1_<日時>.json は、上位10本（stage_keep_of＝M2-F-7 で 10）× 段2a の候補（いま89本）＝890本を測ります。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

**この項目に書くこと**＝工程ごとに、使う材料（指標）・時間足・閾値の格子・パラメータの範囲・候補の本数。

**値の出どころ。**

| 値 | 中身 | 出どころ |
|---|---|---|
| 並べる鍵 | ③と捉えた割合の、先24本と先288本の平均 | まこさん決定 2026-09-27「１は平均でOK」 |
| 先読みの本数 | 24・288 | search_limits.json の state_hold_bars_range の両端（observe_diag._regime_horizons が読む・変えない） |
| 上位を渡す本数 | stage_keep_of（設定の stage_keep_range・M2-F-7 で hi＝10） | まこさん決定 2026-09-18「とりあえず１０本にする」 |
| 段3 の保つ上限 | state_hold_bars_range を候補の番号で端から歩く（_nv_fixed） | 承認済みの範囲・決まった並び（恒久67番） |
| 書き先 | results/priority_rebuild/regime_r9/ | まこさん決定 2026-09-27「了解。進めて良い」（骨組み2） |

**下の囲みは、§2.2 の段の表をプログラムがそのまま写したものです。**

<!-- ACC_STAGES_START hash=959fb92a2f79c965 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この表はプログラムが作ります（手で書き換えない）。**出どころ＝`engine_tuner_milestones2.md` の §2.2（レンジ判定の検索方法）を、`gen_s22_map.py` の抽出関数で読んだもの。**私は1文字も足していません。**

| 段 | 何を選ぶ枠か | 使う法則 | 材料（指標の系統）と時間足 | 値の範囲 |
|---|---|---|---|---|
| **段0** | 0 準備 | — | ①候補×材料の突き合わせ表 ②1列・1組の時間の実測（3分超の段だけ「帯の形→付帯」に分割・差し戻しで拾い直す）③範囲の案を設計書へ | — |
| **段1** | 帯 | R1・R3・R7 | 帯タイプ7系統（レンジ幾何 W%・帯内位置%／S-Rタッチ数／pivot 3種／n本高安／close vs EMA%・SMA%・Keltner／POC・VAH・VAL／転換線・基準線）×時間足8本（10m〜1d） | S-R 窓144〜288・許容幅0.0015〜0.006／高安20〜96本／タッチ2〜4／幅の床0.08%×2〜6倍／余白0〜20%刻み5 |
| **段2a** | 強さの否定 | R5・C1 | ADX・CHOP・ER・VHF・MACDヒスト%・EMA傾き・DI差の絶対値。時間足は上位足（15m〜4h） | ADX 12〜28刻み2（期間は既定14・段5で開く）／CHOP 55〜70刻み3×期間7〜21／分位型は下位20〜50% |
| **段2b** | 向きの否定 | R8 | `rg5_uptrend` の not（承認済みの借用）。自前の向きは M2-M | — |
| **段2c** | 3枠目 | R2・R6・R10 | ばらつき（BB幅・ATR%・realized_vol・Donchian幅・stdev%）／出来高（volume_ratio・CMF ほか）／位置・形（BB%b と0.5の差・経過バー）／時刻。「なし」を必ず併走。段2a の系統は不可（C2）・動きが重なる組は落とす（C3） | 分位＝下位15〜40%刻み5／volume_ratio 0.5〜1.8／CMF 0.05〜0.15／差0.2〜0.35／経過10〜40本 |
| **段3** | 持続 | R4・C6・C7 | 成立の連続本数と解除の緩め幅。5分足で数える | n＝`state_hold_bars_range` の範囲／緩め幅＝`_loose_q` の分位差 |
| **段4** | 4 差し戻し | — | 確定した束に全候補を1枠ずつ入れ直して1周（列はキャッシュ再利用） | — |
| **段5** | 5 詰め | — | 勝った値の前後を細かく。勝った指標だけ期間を範囲から開く（カタログ外の期間も列を作る）。判定は最良値でなく形（前後で崩れる束は落とす） | 閾値は刻み1・分位は刻み半分／線＝`neighbor_drop_max`（まこさんの判断待ち） |

**段の件数＝8件**（§2.2 に在るものを1つも落としていません）。

<!-- ACC_STAGES_END -->

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

**この項目に書くこと**＝指定できる項目・その置き場・既定値・指定しなかったときの動き。

**設定ファイルはこの設計書では変えません。**M2-F-7（stage_keep_range の hi＝10）は M2-F-4 の実装と同じ回に書きます（まこさん OK 2026-09-24・承認の相手ではない）。

**コマンドの旗。**足す＝--trades・--purpose（search／check・測る走行で必須）・--stage・--top・--sweep・--nan-check。消す＝--seed（乱数が消えるため）・--no-trades（既定が「測らない」になるため）。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

**この項目に書くこと**＝できあがったときに出てくるものの形。★4-17（走っている途中の表示）とは別。数字は機械の出力から出す（私が書かない）。

**完成したときに画面に出るもの。**①--selftest の⑥〜⑩の行。②測る走行で「[書いた] 順位表 …／落ちた候補 …（場面の内訳: …）」と「[試行] cumulative か check へ N 本」。③順位表の行が「N位 <束の名前>: ①… ③… 当たった… 捉えた… 正解レンジ…」の形。★数は走らせた出力から書きます。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

**この項目に書くこと**＝入力の検証／起こりうる誤りの状態／中途半端な出力が残ったとき／やり直せるか。★正常の道だけを書かない。

| 起きたこと | どうなるか |
|---|---|
| --purpose が無いのに測る走行を打った | argparse が止める（恒久24番） |
| --trades を --recipe 以外に付けた | argparse が止める（--build・--stage の束は入口を持たない） |
| --stage stage2a 以降で --top が無い | 止まる（前の段の順位表が要る・fail-closed） |
| --top の順位表に、束（内側）を持つ行が1本も無い | 止まる（fail-closed） |
| 候補から束を組めない | 「組めない」の場面で dropped に残す（引き直さない＝乱数が無いので引き直しても同じ） |
| 解決表が作れない | 「測れない」の行と場面（いまの153行の形を保つ） |
| 関所（G5 ほか）が束を拒否した | 「関所で拒否」の行と場面（いまは走行ごと落ちる＝直す） |
| 束の無いレシピ | いまのとおり止まる（100行の fail-closed）＝ファイルには出ない（塞げないもの） |
| 正解レンジが0本 | 捉えた割合＝nan（嘘の0を出さない） |
| hysteresis の出る線を1つも作れない | 止まる（fail-closed） |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

**この項目に書くこと**＝途中で作る表の列の意味・鍵の意味・既にあるデータの形をどう変えるか。

**ほかのファイルは直しません。作り直しも要りません。**regime_r9_diag.py は H2・G2 の印の対象に入っていない（milestones2:2008 の前置き7）ので、この実装では印は失効しません。★M2-F-7（設定の1行）を書く回だけ、設定が H2 の対象なので G2 → H2 の順で印を取り直します（4-4 の5）。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

**この項目に書くこと**＝置き場・上書きか追記か・作り直せるか・古いものをどうするか。

**新しく書く先＝results/priority_rebuild/regime_r9/**（無ければ作る）。rank_<札>_<日時>.json（順位表）と dropped_<札>_<日時>.json（落ちた候補）。日時つき＝上書きしない。ratchet 直下には書きません（保管運用ルール §3.1＝あそこは現役の売買記録の置き場）。

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

**この項目に書くこと**＝タイムゾーン／境目の時刻を含むか含まないか／足の締まる時刻の定義。★静かに結果を変えるので、非該当にしない。

**余白。**この道具はデータを stage_warm(et.WARM)（＝いまの余白60日＋いちばん長い窓182.625日）で読みます。理由＝段2c の動く線（6か月の窓）を、値決め窓の最初のバーから固定の線と同じ条件で測るためです（まこさん決定「余白の直し方→C」の続き・m2_todo の M2-F-2 の注意）。

**窓。**測るのは値決め窓（SEARCH_START〜SEARCH_END）だけです（H8・採点窓は1バーも使わない）。--nan-check だけ確認窓も読みます（数えるだけ・測らない・試行に数えない）。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

**この項目に書くこと**＝時間と容量。★設計の形を決める材料でもあるので、§6-3 の見積もりとは別に書く。

| 何 | 見込み | 根拠 |
|---|---|---|
| regime_r9_diag.py --selftest | 測っていない | ★走らせる前に worklog から過去の実測を探し、無ければ小さく測ってから全体を走らせる（恒久61・62番） |
| 固定のレシピ1本（--recipe・玉なし） | 約9秒（キャッシュ再利用時） | M2-F-1 の実測 8.704秒（worklog 20260927 §13）。キャッシュが無い初回は読み込み99〜103秒が足される。★stage_warm で読む範囲が延びるので、初回の読み込みは延びる |
| 段1 の走行（--stage stage1・336本） | かけ算の目安＝約49分（8.704秒 × 336。1プロセスでラベル・解決表・読み込みが1回なので短くなる見込み） | 実測ではない。M2-F-5 で束数本を測ってから、M2-F-8 のフロー宣言に実測根拠を書く（恒久61番） |
| 壊すプログラム1本 | selftest 1回ぶん＋数秒 | b109〜b112 と同じ形（自己テストを測る） |
| 段4 の差し戻し（--sweep・上位 keep 本） | かけ算の目安＝束1本の時間 × 周の数 × keep 本 ×（帯の幅＋段1＋段2a＋段2b＋段2c＋段3 の候補の本数）。★実測ではない・周の数は走らせるまで分からない | M2-F-5 の --limit で測った束1本の時間を掛けて M2-F-15 のフロー宣言に書く。見込みが要件 R7 の30分を超えるなら、走らせる前に まこさんに出す（監査 CP48） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

**この項目に書くこと**＝同じファイル・同じ記録を2つの走行が触らないか。

**奪い合いに気をつけるもの。**順位表と落ちた候補は日時つきの新しいファイルに書くので、並走しても上書きしません。tuner_stats の記録（cumulative）は record_run の中の既存の書き方に従います（この設計では触りません）。★監査 CP48＝tuner_stats.add_cumulative は読んでから書き直す形で鍵を持たない（tuner_stats.py の175〜192行）＝段の走行を2つ同時に終えると、片方の本数が消える。だから段の走行（--stage・--sweep）は並べて走らせない。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

**この項目に書くこと**＝取引所の鍵／本番で実際に発注するかの切り替え／検査済みの記録。

**書き換えられては困る記録。**順位表のファイルは git の外に在り、手で書き替えて --top に渡せば上位でない束を進められます（塞げないもの）。法則・成績表・設定・印は読むだけです。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

**この項目に書くこと**＝途中経過が見えるか（恒久60番が求める）。後から何が起きたかを追えるか。

**画面に出すもの。**selftest の⑥〜⑩の行（最後が「＝通った」か ❌）。測る走行の「[書いた]」「[試行]」の行。順位つきの表。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

**この項目に書くこと**＝いま在るもののうち、何がこの部分に依存しているか。★hook 64本と承認・ハッシュ値が絡むので、この repo では特に重い。

1. **regime_r9_diag.py の出力の形。**行に 順位・当たった・捉えた・正解レンジ・内側・枠・包み の鍵が増えます。機械が読む形（JSON）を読む側は、いまはありません（この工事で作る --top が最初の読み手）。
2. **--no-trades と --seed を消す。**next_step の順9 の欄と m2_todo の M2-F-1 の文に --no-trades が残りますが、終わった段の記録なので直しません。これから書くフロー宣言・記録は新しい旗で書きます。
3. **固定のレシピの走行の数字。**stage_warm で読む範囲が延びるので、長い記憶の指標の値が窓の始まりで変わりえます＝M2-F-1 の実測（①5.30%・③50.3%／51.4%）と少し違う数字が出えます。実装の後の走行で両方を並べて貼ります。
4. **試行の累積。**測る走行が record_run で数えられるようになります（search＝累積が増える・check＝確認の帳簿）。走らせる前にフロー宣言の「数え方:」と --purpose を一致させます（違反の記録 #20 の再発防止）。
5. **生成器・実行器・法則・成績表・審判・設定・型の表・印。**触りません。
6. **G2・H2 の印。**この実装では失効しません（前置き7）。M2-F-7 の設定の1行を書く回だけ取り直します。
7. **壊すプログラム。**なぜ作るかの後に grep で確かめ、当たった壊すプログラムが探す行は消しません（L-605）。★監査 CP48＝この道具のファイル名で .claude/breaks を grep すると2本 当たる。b84＝探す行 qt = qt_all は残り、測るのは組む側の自己テスト T38＝この工事の後も通る。b97＝測るコマンドが --no-trades を使い --purpose が無い＝この工事の後は argparse が rc=2 で止め、完成の条件 AUDIT-5 の番人が壊れる。b97 は実装の指示 22・23 で直し（--purpose check・確認の帳簿を控えに写して戻す）、実装の後に run_breaks.py --design v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2e2-cp36-major-20260914.md --measure-only --only b97_demand_not_attached.sh で測る。
8. **RG-v5 の行。**比べる相手として順位表に載り、順位も付きますが、束（内側）を持たないので --top には拾われません。★監査 CP48 の直しの後は、上位の枠（keep）を使わず、落ちた候補にも数えず、行に 比べる相手＝真 が付きます（M2-F-9 の数えでは外す）。
9. **ほかの道具の文（この工事では直さない・1変更）。**.claude/tools/gen_stage0_timing.py の59行目は、読み方を regime_r9_diag.py:230 と同じ（WARM）と書くが、この工事の後の道具は stage_warm で読む＝段0 の時間の実測と余白が違う。.claude/tools/gen_s22_fidelity.py の15行目は、regime_r9_diag の --build と同じやり方と書くが、この工事の後の --build は sample_regime_build だけで組み、あちらは sample_structure と乱数のまま。2つとも next_step §6 に積む。

### 4-18 再利用（手本にした、既にあるものの形）

**この項目に書くこと**＝同じ形が既にどこかに在るか。手本にしたファイル（`MODEL:` の行と同じ相手）。

| 手本 | 何を写すか |
|---|---|
| r9_trend_share と番人②（反転で 1−x・真0本は nan） | 捉えた割合の式と既知答えの形 |
| sample_regime_build の E・F（hysteresis と streak の組み方） | 段3 の包みの形（内側＝成立の全体・off＝1段 緩めた any） |
| engine_tuner_gen._nv_fixed | 範囲を決まった並びで歩く形（段3 の保つ上限） |
| tuner_stats.record_run（213行） | 試行の数え方の口（purpose で行き先が変わる） |
| .claude/breaks/b104_atr1h_own_tf.sh | 壊すプログラムの書き方（EXPECT_RC・MEANS・EXPECT_MSG・guard・measure・finish） |
| いまの153行（測れない束の行を残す形） | 落ちた候補を行として残す形（m） |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

**この項目に書くこと**＝この工事で実物に当てる直しを、監査結果の修正の指示と同じ6つの欄（対象のファイル・直す箇所・直す前の文字・4つ目・根拠の抜き書き・状態）で1件ずつ書く。★元データの「実装の指示」が空なら非該当（理由を書く）。

<!-- ACC_IMPL_START hash=ad71c102320c1e96 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 20〜23行（説明文の使い方）
直す前の文字:
~~~
使い方:
  python3 regime_r9_diag.py --build 3 --seed 53        # 1位から順に束を3本 組んで測る
  python3 regime_r9_diag.py --recipe path.json         # 束を持つレシピ1本を測る
  python3 regime_r9_diag.py --selftest                 # 合成データの番人（わざと壊して止まる3件＋未来参照の grep）
~~~
直した後の文字:
~~~
使い方（★測る走行は --purpose search か check が必須＝恒久の決まり24番・道具の確認は check）:
  python3 regime_r9_diag.py --build 3 --purpose check                   # 1位から順に束を3本 組んで測る（乱数なし・案の番号の決まった並び）
  python3 regime_r9_diag.py --recipe path.json --purpose check          # 束を持つレシピ1本を測る（玉も測るときだけ --trades）
  python3 regime_r9_diag.py --stage stage1 --purpose search             # 段の候補を全部 束にして測り、順位表と落ちた候補をファイルに書く（M2-F-8）
  python3 regime_r9_diag.py --stage stage2a --top <rank_stage1_*.json> --purpose search   # 前の段の上位 × 候補（M2-F-11〜14）
  python3 regime_r9_diag.py --sweep <rank_stage3_*.json> --purpose search  # 段4 差し戻し＝1枠ずつ入れ直して1周・良くならなくなるまで（M2-F-15）
  python3 regime_r9_diag.py --nan-check                                 # BB幅 の動く線の材料の値なしを数える（リスク8・測らない＝試行に数えない）
  python3 regime_r9_diag.py --selftest                                  # 合成データの番人（実データの試行ゼロ）
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:21「  python3 regime_r9_diag.py --build 3 --seed 53        # 1位から順に束を3本 組んで測る」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 16行（説明文の決まり）
直す前の文字:
~~~
決まり＝売買記録CSVを書かない・_output_and_report を呼ばない・採用を書き出さない・審判（score.py）は改造しない。
~~~
直した後の文字:
~~~
決まり＝売買記録CSVを書かない・_output_and_report を呼ばない・採用を書き出さない・審判（score.py）は改造しない。
        順位表と落ちた候補は results/priority_rebuild/regime_r9/ に書く（売買記録ではない・M2-F-2 の (i)(l)）。
        測る走行は tuner_stats.record_run で数える（--purpose search＝累積／check＝確認・§2.2「試行は累積」）。
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:16「決まり＝売買記録CSVを書かない・_output_and_report を呼ばない・採用を書き出さない・審判（score.py）は改造しない。」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 30行（import sys）
直す前の文字:
~~~
import sys

import numpy as np
~~~
直した後の文字:
~~~
import sys
import time

import numpy as np
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:30「import sys」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 55行（r9_trend_share の最後の行の直後）
直す前の文字:
~~~
    return float(np.asarray(strong, bool)[m].mean())
~~~
足す文字:
~~~



def r9_catch_share(col: np.ndarray, strong: np.ndarray, usable: np.ndarray) -> float:
    """捉えた割合（0〜1）＝正解がレンジ（強さが偽 ∧ 使える）のバーのうち、判定が真の割合（M2-F-2 の (a)）。

    ★正解が0本なら nan（嘘の0を出さない）。式の出どころ＝recall＝tp/(tp+fn)（milestones2 の M2-F 前置き3・外の一次資料で確認済み）。
    """
    col = np.asarray(col, bool)
    m = (~np.asarray(strong, bool)) & np.asarray(usable, bool)
    if not m.any():
        return float("nan")
    return float(col[m].mean())


def r9_range_share(strong: np.ndarray, usable: np.ndarray) -> float:
    """正解レンジの割合（≈50%・一緒に出す＝前置き9）＝使えるバーのうち、強さが偽（レンジだった）の割合。"""
    u = np.asarray(usable, bool)
    if not u.any():
        return float("nan")
    return float((~np.asarray(strong, bool))[u].mean())


def _nanmean(vals: list) -> float:
    """nan を除いた平均。全部 nan なら nan（並べる鍵で使う）。"""
    xs = [v for v in vals if v == v]
    return float(np.mean(xs)) if xs else float("nan")


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


# ★書き先（まこさん決定 2026-09-27「了解。進めて良い」＝骨組み2）。ratchet 直下には書かない（保管運用ルール §3.1）。
OUT_DIR = HERE.parents[1] / "results" / "priority_rebuild" / "regime_r9"
# ★落ちた候補の5つの場面（M2-F-2 の (l)）。名前を散らさない（ファイルの読み手が数えるため）。
DROP_KINDS = ("組めない", "測れない", "束が無い", "関所で拒否", "成績下位")


def write_outputs(tag: str, rows: list[dict], dropped: list[dict]):
    """順位表と落ちた候補をファイルに書く（画面だけに出さない＝M2-F-2 の (i)(l)）。戻り＝2つのパス。"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    rp = OUT_DIR / f"rank_{tag}_{stamp}.json"
    dp = OUT_DIR / f"dropped_{tag}_{stamp}.json"
    if rp.exists() or dp.exists():
        raise SystemExit(f"[R9] 同じ名前のファイルが既に在る＝上書きしない（fail-closed）: {rp.name}")
    rp.write_text(json.dumps(rows, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8")
    dp.write_text(json.dumps(dropped, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8")
    _n = {k: sum(1 for d in dropped if d.get("場面") == k) for k in DROP_KINDS}
    print(f"[書いた] 順位表 {rp} ／ 落ちた候補 {dp}（場面の内訳: {json.dumps(_n, ensure_ascii=False)}）")
    return rp, dp
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:55「    return float(np.asarray(strong, bool)[m].mean())」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 110〜111行（_row の③の繰り返し）
直す前の文字:
~~~
        for n, (s, u) in labels.items():
            r[f"③実はトレンド(先{n}本)"] = r9_trend_share(col, s, u)
~~~
直した後の文字:
~~~
        for n, (s, u) in labels.items():
            r[f"③実はトレンド(先{n}本)"] = r9_trend_share(col, s, u)
            # ★M2-F-2 の (a)(b)(f)＝当たった（1−③・nan は nan のまま）・捉えた・正解レンジの割合を足す
            r[f"当たった(先{n}本)"] = 1.0 - r[f"③実はトレンド(先{n}本)"]
            r[f"捉えた(先{n}本)"] = r9_catch_share(col, s, u)
            r[f"正解レンジ(先{n}本)"] = r9_range_share(s, u)
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:111「            r[f"③実はトレンド(先{n}本)"] = r9_trend_share(col, s, u)」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 155〜158行（measure の列を作る所）
直す前の文字:
~~~
        qt = qt_all                        # ★作り直さない（上で1回 作った表を使い回す）
        d2 = df.copy()
        d2.attrs = {}
        ex.build_regime_columns(d2, rec, geo, qt)
~~~
直した後の文字:
~~~
        qt = qt_all                        # ★作り直さない（上で1回 作った表を使い回す）
        d2 = df.copy()
        d2.attrs = {}
        try:
            ex.build_regime_columns(d2, rec, geo, qt)
        except ex.RecipeError as e:
            # ★M2-F-2 の (l)＝関所（G5 ほか）の拒否を行として残す（直す前は走行ごと落ちて記録が残らなかった）
            rows.append({"判定": rec["meta"].get("logic_id"), "注": f"関所で拒否: {str(e)[:120]}"})
            continue
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:158「        ex.build_regime_columns(d2, rec, geo, qt)」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 216行（番人の見出しの直前）
直す前の文字:
~~~
# ══ 番人（合成データ・実データの試行ゼロ）════════════════════════════════════════════════
~~~
直した後の文字:
~~~
# ══ 段ごとに測る口（M2-F-2 の (k)・M2-F-15・§2.2 の段の表）═══════════════════════════════
def _q50_width_cond(limits) -> dict:
    """段1 の帯＝レンジ幾何 W% が q50 より上（build_width_candidates の先頭＝geo が先頭・M2-F-8 の中身）。"""
    import engine_tuner_gen as g
    cw = g.build_width_candidates(g.laws_for_scene("range"), g.load_signal_table(),
                                  g.material_pool()[1], limits)
    if not (cw and "geo" in ((cw[0]["cond"].get("material") or [{}])[0])):
        raise SystemExit("[R9] 帯の幅の候補の先頭がレンジ幾何でない（法則 R7 の geo が空・fail-closed）")
    return json.loads(json.dumps(cw[0]["cond"]))


def _loosened_off(conds: list[dict], limits, frames: list | None = None) -> dict:
    """hysteresis の出る線＝sample_regime_build の E と同じ形の any（監査 CP48 で直した）。

    ★生成器の E（engine_tuner_gen.py の sample_regime_build）＝off は、A（帯の幅）と B（段1）を1段 緩めて側を返したもの（_flip_loose）と、
      C（段2a の not の中身）を1段 緩めて側は返さないもの（off_c）の any。段2b・段2c の条件は off に入れない。
      緩め方の判定は書き写さない＝生成器の _loose_q_fixed を呼ぶ。frames＝各条件の段の名前（無ければ水準の条件を全部 使う）。
    """
    import engine_tuner_gen as g
    outs = []
    for i, c in enumerate(conds):
        if frames is not None and (i >= len(frames) or frames[i] not in ("width", "stage1", "stage2a")):
            continue
        is_not = isinstance(c, dict) and "not" in c
        base = c.get("not") if is_not else c
        if not isinstance(base, dict) or base.get("form") != "level":
            continue
        q = (base.get("value") or {}).get("threshold_q")
        if not q:
            continue
        cc = json.loads(json.dumps(base))
        side = cc.get("side", "above")
        try:
            cc["value"]["threshold_q"] = g._loose_q_fixed(limits, q, side)
        except g.SampleError:
            continue
        if not is_not:
            # ★not の中身（段2a の強さ）は側を返さない＝生成器の off_c と同じ向き（強さが戻ったら出る）
            cc["side"] = "below" if side == "above" else "above"
        outs.append(cc)
    if not outs:
        raise SystemExit("[R9] hysteresis の出る線を1つも作れない（fail-closed）")
    return {"any": outs}


def _wrap_bundle(inner: list[dict], wrap: dict | None, limits, out_col: str, frames: list | None = None) -> dict:
    """内側の条件の一覧（＋段3 の包み）から判定の束（meta.regime.build の中身）を作る。

    wrap＝None（段1〜2c＝all で束ねるだけ）か {"持続n", "保つ上限", "role"}（段3＝
    hysteresis（on＝streak〔内側＝成立の全体・M2-E-4d と同じ〕／off＝1段 緩めた any／value＝保つ上限））。
    """
    conds = json.loads(json.dumps(inner))
    if not wrap:
        return {"entry": {"out_col": out_col, "tree": {"all": conds}}, "block": None}
    streak = {"role": wrap.get("role") or "location", "form": "streak",
              "value": {"n": int(wrap["持続n"])}, "inner": {"all": json.loads(json.dumps(conds))}}
    tree = {"all": [{"form": "hysteresis", "on": {"all": [streak]},
                     "off": _loosened_off(conds, limits, frames), "value": {"n": int(wrap["保つ上限"])}}]}
    return {"entry": {"out_col": out_col, "tree": tree}, "block": None}


def _load_top(path: str, keep: int) -> list[dict]:
    """前の段の順位表（rank_*.json）から、内側を持つ上位 keep 本を読む（fail-closed）。"""
    rows = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    tops = [r for r in rows if r.get("順位") and not r.get("dropped_by") and r.get("内側")]
    tops = sorted(tops, key=lambda r: r["順位"])[:keep]
    if not tops:
        raise SystemExit(f"[R9] 順位表 {path} に、束（内側）を持つ行が1本も無い（fail-closed）")
    return tops


def _stage_recipe(strategy: str, name: str, bd: dict) -> dict:
    """判定の束だけを持つ最小のレシピ（入口を持たない＝玉は測らない）。"""
    return {"meta": {"strategy": strategy, "logic_id": name, "side": "SHORT",
                     "regime": {"name": "range", "entry_col": bd["entry"]["out_col"], "build": bd}},
            # ★入口の木は空の all（束だけを測る・玉は測らない）。無いと build_qtable の needed_qkeys が r["entry"] で KeyError になる（監査 CP48）
            "entry": {"connective": {"all": []}}}


def _record(a, tag: str, n: int) -> None:
    """試行を数える（§2.2＝累積して DSR・PBO に数える・恒久の決まり24番＝目的は呼ぶ側が必ず宣言する）。"""
    import tuner_stats as ts
    dest, tot = ts.record_run(key=f"{a.strategy}/r9/{tag}", n_trials=int(n),
                              stamp=time.strftime("%Y-%m-%d %H:%M:%S"), purpose=a.purpose,
                              note=f"R9 の診断（{tag}・束 {n} 本・判定の成績だけ）")
    print(f"[試行] {dest} へ {n} 本（この鍵の合計 {tot}）")


def run_stage(df, a) -> int:
    """--stage＝その段の候補を全部 束にして測り、並べて、順位表と落ちた候補をファイルに書く（M2-F-8〜14）。"""
    import engine_tuner_gen as g
    from periods import SEARCH_END, SEARCH_START
    lm, _w = g.load_limits()
    lm = g.resolve_hold_range(lm, a.strategy)
    laws = g.laws_for_scene("range")
    table = g.load_signal_table()
    _pool, tfs, _ = g.material_pool()
    cands = (g.build_width_candidates(laws, table, tfs, lm) if a.stage == "width"
             else g.build_stage_candidates(a.stage, laws, table, tfs, lm))
    dropped: list[dict] = []
    if a.stage == "width":
        base = [{"判定": "（単独）", "内側": [], "枠": []}]   # 帯の候補1本だけの束（重ねる相手なし）
    elif a.stage == "stage1":
        base = [{"判定": "帯（W% above q50）", "内側": [_q50_width_cond(lm)], "枠": ["width"]}]
    else:
        if not a.top:
            raise SystemExit(f"[R9] {a.stage} には --top <前の段の順位表.json> が要る（width・stage1 だけ無しで走れる）")
        if (lm.get("stage_keep_range") or {}).get("hi") is None:
            raise SystemExit("[R9] stage_keep_range の hi が未設定＝前の段の上位を絞れない（M2-F-7 の後に走らせる・fail-closed）")
        base = _load_top(a.top, None)
    # ★渡す本数（keep）は、この段で測る束の本数に対して stage_keep_of で決める（監査 CP48）。
    #   直す前＝候補の本数で決めた＝候補1本の段2b で keep＝1（上位1本しか渡らない）・hi＝10 では stage_keep_of が止まった。
    _n_meas = len(base) * (len(cands) + (1 if a.stage == "stage2c" else 0))
    _hi = (lm.get("stage_keep_range") or {}).get("hi")
    keep = g.stage_keep_of(lm, max(_n_meas, int(_hi)) if _hi is not None else _n_meas)
    base = base[:keep]
    recipes = []
    marks = {}
    for t in base:
        # ★段2c は「なし」（3枠目を足さない束）を必ず併走する（§2.2 の段2c・M2-F-13）
        for j, c in enumerate(([None] if a.stage == "stage2c" else []) + list(cands)):
            name = f"{a.stage}_{len(recipes) + len(dropped)}"
            try:
                if a.stage == "stage3":
                    # ★保つ上限は候補の番号 j で決める＝前の束が違っても同じ候補なら同じ値（sample_regime_build の order_n と同じ組）
                    wrap = {"持続n": int(c["cond"]["value"]["n"]),
                            "保つ上限": int(g._nv_fixed(lm, "state_hold_bars_range", "n", j)["n"]),
                            "role": c["cond"].get("role")}
                    inner = list(t["内側"])
                elif c is None:
                    wrap = None
                    inner = list(t["内側"])
                else:
                    wrap = None
                    inner = list(t["内側"]) + [json.loads(json.dumps(c["cond"]))]
                # ★枠は内側と同じ並び（段3 の包みと「なし」は条件を足さない＝枠も足さない・差し戻しが読む）
                frames_in = list(t.get("枠") or []) + ([] if (a.stage == "stage3" or c is None) else [a.stage])
                bd = _wrap_bundle(inner, wrap, lm, f"regime_{name}", frames=frames_in)
            except (SystemExit, KeyError, TypeError) as e:
                dropped.append({"場面": "組めない", "判定": name, "理由": str(e)[:120]})
                continue
            if a.stage == "stage3":
                # ★完成した束だけを G7（法則の審査）に掛ける（M2-F-14）。途中の段では掛けない（中身13 の (j)）
                try:
                    ex._check_scene_rules({"name": "range", "build": g.strip_marks(bd)}, "")
                except ex.RecipeError as e:
                    dropped.append({"場面": "関所で拒否", "判定": name, "理由": f"G7: {str(e)[:120]}"})
                    continue
            recipes.append(_stage_recipe(a.strategy, name, bd))
            marks[name] = {"内側": inner, "枠": frames_in, "包み": wrap,
                           "前の束": t.get("判定"),
                           "候補": ("なし" if c is None else {k: c.get(k) for k in ("rank", "family", "tf", "col")})}
    if a.limit:
        recipes = recipes[:int(a.limit)]
    print(f"[R9] {a.stage}＝前の束 {len(base)} 本 × 候補 {len(cands)} 本 → 測る束 {len(recipes)} 本（keep={keep}）")
    rows = measure(df, recipes, SEARCH_START, SEARCH_END, with_trades=False)
    for r in rows:
        if r.get("判定") in marks:
            r.update(marks[r["判定"]])
    rows, drop_rank = rank_rows(rows, keep=keep)
    dropped += drop_rank
    dropped += [{"場面": ("関所で拒否" if str(r.get("注", "")).startswith("関所で拒否") else "測れない"),
                 "判定": r.get("判定"), "理由": r.get("注")} for r in rows if "①時間の割合" not in r]
    _print_rows(rows)
    write_outputs(a.stage, rows, dropped)
    _record(a, a.stage, len(recipes))
    return 0


def run_sweep(df, a) -> int:
    """--sweep＝段4 差し戻し（M2-F-15）＝束の1枠を、その段の全候補で入れ直して1周し、良くならなくなるまで繰り返す。"""
    import engine_tuner_gen as g
    from periods import SEARCH_END, SEARCH_START
    got = json.loads(pathlib.Path(a.sweep).read_text(encoding="utf-8"))
    rows_in = got if isinstance(got, list) else [got]
    tops = sorted([r for r in rows_in if r.get("内側") and not r.get("dropped_by")],
                  key=lambda r: (r.get("順位") is None, r.get("順位") or 0))
    if not tops:
        raise SystemExit("[R9] --sweep の順位表に、束（内側）を持つ行が1本も無い（fail-closed）")
    lm, _w = g.load_limits()
    lm = g.resolve_hold_range(lm, a.strategy)
    # ★M2-F-15＝上位（stage_keep_of の本数）の束ごとに差し戻し、最終の束を最大 keep 本 出す（監査 CP48・直す前は1位の1本だけ）
    _hi = (lm.get("stage_keep_range") or {}).get("hi")
    keep = g.stage_keep_of(lm, max(len(tops), int(_hi)) if _hi is not None else len(tops))
    laws = g.laws_for_scene("range")
    table = g.load_signal_table()
    _pool, tfs, _ = g.material_pool()
    cands_of = {}
    dropped: list[dict] = []
    finals = []
    n_all = 0

    def _measure_one(tag, variants):
        recipes, marks = [], {}
        for j, (nm, iv, wv, fv) in enumerate(variants):
            try:
                bd = _wrap_bundle(iv, wv, lm, f"regime_{tag}_{j}", frames=fv)
            except (SystemExit, KeyError, TypeError) as e:
                dropped.append({"場面": "組めない", "判定": nm, "理由": str(e)[:120]})
                continue
            if wv:
                # ★段3 の包みを持つ束（完成した束）は G7 に掛ける（M2-F-14 と同じ・入れ替えで法則を破った束を残さない）
                try:
                    ex._check_scene_rules({"name": "range", "build": g.strip_marks(bd)}, "")
                except ex.RecipeError as e:
                    dropped.append({"場面": "関所で拒否", "判定": nm, "理由": f"G7: {str(e)[:120]}"})
                    continue
            recipes.append(_stage_recipe(a.strategy, nm, bd))
            marks[nm] = (iv, wv)
        rows = measure(df, recipes, SEARCH_START, SEARCH_END, with_trades=False)
        rows, _ = rank_rows(rows)
        dropped.extend({"場面": ("関所で拒否" if str(r.get("注", "")).startswith("関所で拒否") else "測れない"),
                        "判定": r.get("判定"), "理由": r.get("注")} for r in rows if "①時間の割合" not in r)
        return rows, marks, len(recipes)

    for b_i, row in enumerate(tops[:keep]):
        inner = row.get("内側")
        frames = row.get("枠") or []
        wrap = row.get("包み")
        cf = list(frames[:len(inner or [])])
        if not inner or len(cf) != len(inner):
            raise SystemExit("[R9] --sweep の行に 内側 と 枠 が揃っていない（段の口が書いた順位表の行を渡す・fail-closed）")
        # ★入れ直す枠＝条件の枠（内側と同じ並び）＋段3 の包みが在れば持続（streak の本数）の枠
        slots = list(cf) + (["stage3"] if wrap else [])
        for st in slots:
            if st not in cands_of:
                cands_of[st] = (g.build_width_candidates(laws, table, tfs, lm) if st == "width"
                                else g.build_stage_candidates(st, laws, table, tfs, lm))
        base_nm = f"sweep_b{b_i}_r0_base"
        rows0, _m0, n0 = _measure_one(f"sweep_b{b_i}_r0", [(base_nm, inner, wrap, cf)])
        best = next((r for r in rows0 if r.get("判定") == base_nm), {"判定": base_nm})
        n_all += n0
        rnd = 0
        improved = True
        while improved:
            improved = False
            rnd += 1
            for k, st in enumerate(slots):
                variants = []
                for j, c in enumerate(cands_of[st]):
                    nm = f"sweep_b{b_i}_r{rnd}_f{k}_c{j}"
                    if k < len(cf):
                        iv = json.loads(json.dumps(inner))
                        iv[k] = json.loads(json.dumps(c["cond"]))
                        variants.append((nm, iv, wrap, cf))
                    else:
                        wv = dict(wrap)
                        wv["持続n"] = int(c["cond"]["value"]["n"])
                        variants.append((nm, inner, wv, cf))
                rows, marks, n = _measure_one(f"sweep_b{b_i}_r{rnd}_f{k}", variants)
                n_all += n
                cand_best = next((r for r in rows if r.get("判定") in marks and "①時間の割合" in r), None)
                if cand_best is not None and rank_key(cand_best) < rank_key(best):
                    best = cand_best
                    inner, wrap = marks[cand_best["判定"]]
                    improved = True
                write_outputs(f"sweep_b{b_i}_r{rnd}_f{k}", rows, [])
                print(f"[差し戻し] 束 {b_i}・周 {rnd}・枠 {k}（{st}）＝いまの最良 {best.get('判定')}")
        best_row = dict(best)
        best_row["内側"] = inner
        best_row["枠"] = frames
        best_row["包み"] = wrap
        best_row["差し戻しの元"] = row.get("判定")
        finals.append(best_row)
    finals, _ = rank_rows(finals)
    write_outputs("sweep_final", finals, dropped)
    _record(a, "sweep", n_all)
    return 0


def run_nan_check(ad, warm, a) -> int:
    """--nan-check＝BB幅 の動く線の材料の値なしの本数を、値決め窓・確認窓で数える（リスク8・まこさん決定「案1」）。

    ★測らない＝試行に数えない。窓の始まりの後に値なしが在れば終了コード1で止まって まこさんに出す。
    """
    import engine_tuner as et
    import engine_tuner_gen as g
    from periods import CONFIRM_END, CONFIRM_START, SEARCH_END, SEARCH_START
    lm, _w = g.load_limits()
    lm = g.resolve_hold_range(lm, a.strategy)
    cands = g.build_stage_candidates("stage2c", g.laws_for_scene("range"), g.load_signal_table(),
                                     g.material_pool()[1], lm)
    moving = [c for c in cands if c.get("pre_win")]
    if not moving:
        raise SystemExit("[R9] 段2c に動く線の候補が1本も無い（M2-E-4e の後のはず・fail-closed）")
    df, df_c = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END), (CONFIRM_START, CONFIRM_END)], warm)
    ng = 0
    for wname, dfx, w0, w1 in (("値決め窓", df, SEARCH_START, SEARCH_END), ("確認窓", df_c, CONFIRM_START, CONFIRM_END)):
        ts_col = pd.to_datetime(dfx["ts"])
        m = ((ts_col >= pd.Timestamp(w0)) & (ts_col < pd.Timestamp(w1))).to_numpy()
        seen = set()
        for c in moving:
            col = c["col"]
            if col in seen:
                continue
            seen.add(col)
            base = c["cond"].get("not") if "not" in c["cond"] else c["cond"]
            pre = dict(base["material"][0]["pre"])
            # ★材料は実行データの列に無い（実行器がその場で作る）＝_col_array で、前処理（動く線）まで実行器と同じ式で作る（監査 CP48）
            try:
                arr = ex._col_array(dfx, base["material"][0], g._geo_of(dfx), "")
            except ex.RecipeError as e:
                print(f"  ❌ {col}: 材料を作れない（{str(e)[:80]}）")
                ng += 1
                continue
            n_nan = int(np.isnan(arr[m]).sum())
            print(f"  {col}（窓 {pre.get('n')}本）: {wname} の値なし {n_nan} 本 ／ 窓 {int(m.sum())} 本")
            if n_nan:
                ng += 1
    if ng:
        print(f"❌ 窓の始まりの後に値なしが在る（{ng} 件）＝止まって まこさんに出す（リスク8）", file=sys.stderr)
        return 1
    print("[値なし] 値決め窓・確認窓の動く線の材料に、値なし 0 本（通った）")
    return 0


# ══ 番人（合成データ・実データの試行ゼロ）════════════════════════════════════════════════
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:216「# ══ 番人（合成データ・実データの試行ゼロ）════════════════════════════════════════════════」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 201〜213行（_print_rows の全体）
直す前の文字:
~~~
def _print_rows(rows: list[dict]) -> None:
    print("\n[R9 の測るもの3つ]（値決め窓だけ・数字は審判と印の出力・この診断は案を選ばない）")
    for r in rows:
        if "注" in r and "①時間の割合" not in r:
            print(f"  {r['判定']}: {r['注']}")
            continue
        t = r.get("②玉")
        tt = (f"②玉 {t['n']}件 net ${t['net']:+,.0f} {t['per_day']:.2f}件/日" if t and t["n"]
              else ("②玉 0件" if t is not None else "②玉 （測っていない）"))
        tr = " ".join(f"{k.replace('③実はトレンド', '③')}={v:.1%}" if v == v else f"{k}=nan"
                      for k, v in r.items() if k.startswith("③"))
        print(f"  {r['判定']}: ①{r['①時間の割合']:.2%} ／ {tt} ／ {tr}"
              + (f" ／ {r['注']}" if r.get("注") else ""))
~~~
直した後の文字:
~~~
def _print_rows(rows: list[dict]) -> None:
    print("\n[R9 の測るもの]（値決め窓だけ・数字は審判と印の出力・この診断は案を選ばない）")
    for r in rows:
        if "注" in r and "①時間の割合" not in r:
            print(f"  {r['判定']}: {r['注']}")
            continue
        t = r.get("②玉")
        tt = (f"②玉 {t['n']}件 net ${t['net']:+,.0f} {t['per_day']:.2f}件/日" if t and t["n"]
              else ("②玉 0件" if t is not None else "②玉 （測っていない）"))
        # ★M2-F-2＝当たった・捉えた・正解レンジも出す（順位は先頭・並べる鍵は rank_key）
        tr = " ".join(f"{k.replace('③実はトレンド', '③')}={v:.1%}" if v == v else f"{k}=nan"
                      for k, v in r.items() if k.startswith(("③", "当たった", "捉えた", "正解レンジ")))
        _rk = f"{r['順位']}位 " if r.get("順位") else ""
        print(f"  {_rk}{r['判定']}: ①{r['①時間の割合']:.2%} ／ {tt} ／ {tr}"
              + (f" ／ 成績下位" if r.get("dropped_by") == "成績下位" else "")
              + (f" ／ {r['注']}" if r.get("注") else ""))
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:201「def _print_rows(rows: list[dict]) -> None:」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 252〜253行（番人④の判定の直後）
直す前の文字:
~~~
    if bad4:
        ng.append(f"④: 診断のコードに未来参照の式が在る: {bad4}")
~~~
直した後の文字:
~~~
    if bad4:
        ng.append(f"④: 診断のコードに未来参照の式が在る: {bad4}")
    # ⑥ 捉えた割合（M2-F-2 の (a)）＝全部 真→1.0／全部 偽→0.0／正解レンジ0本→nan／判定の反転で 1−x
    if r9_catch_share(col_all, strong, usable) != 1.0 or r9_catch_share(col_none, strong, usable) != 0.0:
        ng.append("⑥: 捉えた割合が 全部真→1.0・全部偽→0.0 にならない")
    if r9_catch_share(col_all, np.ones(n, bool), usable) == r9_catch_share(col_all, np.ones(n, bool), usable):
        ng.append("⑥: 正解レンジが0本なのに nan でない")
    # ⑥ の既知答え（設計書 4-19 の通しの例1）＝8本・強さが真は1・3・5・7本目・判定は2・4本目だけ真 → 0.5（監査 CP48）
    _s8 = (np.arange(8) % 2 == 0)
    _c8 = np.isin(np.arange(8), [1, 3])
    if r9_catch_share(_c8, _s8, np.ones(8, bool)) != 0.5:
        ng.append("⑥: 既知答え（8本・判定2本／正解レンジ4本＝0.5）にならない")
    # ⑥ 使えない印のバーは分母に入れない（8本目を使えないにすると 2÷3）
    if abs(r9_catch_share(_c8, _s8, np.arange(8) != 7) - 2.0 / 3.0) > 1e-12:
        ng.append("⑥: 使えない印のバーを分母から外していない")
    colX = (np.arange(n) % 3 == 0)
    cx1 = r9_catch_share(colX, strong, usable)
    cx2 = r9_catch_share(~colX, strong, usable)
    if abs((cx1 + cx2) - 1.0) > 1e-12:
        ng.append(f"⑥: 判定を反転しても 1−x にならない（x={cx1}, y={cx2}）")
    # ⑦ 乱数がこの道具に残っていない（恒久67番・構文木で見る＝説明の文には反応しない）
    for node in ast.walk(tree):
        _nm7 = node.attr if isinstance(node, ast.Attribute) else (node.id if isinstance(node, ast.Name) else None)
        if _nm7 in ("default_rng", "sample_structure", "random", "RandomState"):
            ng.append(f"⑦: 乱数の道が残っている: {_nm7} 行 {node.lineno}")
        if isinstance(node, ast.Import) and any(al.name.split(".")[-1] == "random" for al in node.names):
            ng.append(f"⑦: 乱数の import が残っている: 行 {node.lineno}")
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[-1] == "random":
            ng.append(f"⑦: 乱数の import が残っている: 行 {node.lineno}")
    # ⑧ 試行を累積に数える口（record_run）が呼ばれている（§2.2・恒久24番）
    if not any(isinstance(nd, ast.Attribute) and nd.attr == "record_run" for nd in ast.walk(tree)):
        ng.append("⑧: 試行を数える口（record_run）が1回も呼ばれていない")
    # ⑧ 測る口（main・run_stage・run_sweep）が、それぞれ試行を数える _record を呼ぶ（監査 CP48）
    for _fn8 in ("main", "run_stage", "run_sweep"):
        _d8 = [f for f in tree.body if isinstance(f, ast.FunctionDef) and f.name == _fn8]
        if not _d8 or not any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "_record" for x in ast.walk(_d8[0])):
            ng.append(f"⑧: 測る口 {_fn8} が試行を数える _record を呼んでいない")
    # ⑨ 落ちた候補の5つの場面が全部 ファイルに出る（M2-F-2 の (l)・合成＝実データゼロ）
    import tempfile
    global OUT_DIR
    _old_out = OUT_DIR
    try:
        OUT_DIR = pathlib.Path(tempfile.mkdtemp()) / "regime_r9"
        _drops = [{"場面": k, "判定": f"x{i}"} for i, k in enumerate(DROP_KINDS)]
        rp9, dp9 = write_outputs("selftest", [{"判定": "t", "①時間の割合": 0.5, "順位": 1}], _drops)
        try:
            _back = json.loads(dp9.read_text(encoding="utf-8"))
        except Exception:
            _back = []
        if sorted({d.get("場面") for d in _back}) != sorted(DROP_KINDS):
            ng.append("⑨: 落ちた候補の5つの場面が全部 ファイルに出ない")
        if not rp9.exists():
            ng.append("⑨: 順位表のファイルが書かれない")
    finally:
        OUT_DIR = _old_out
    # ⑩ 並べる鍵＝2つの先読みの平均（まこさん決定 2026-09-27「１は平均でOK」）・keep の下は成績下位
    _rA = {"判定": "A", "①時間の割合": 0.5, "③実はトレンド(先24本)": 0.48, "③実はトレンド(先288本)": 0.52,
           "捉えた(先24本)": 0.6, "捉えた(先288本)": 0.6}
    _rB = {"判定": "B", "①時間の割合": 0.5, "③実はトレンド(先24本)": 0.50, "③実はトレンド(先288本)": 0.49,
           "捉えた(先24本)": 0.6, "捉えた(先288本)": 0.6}
    _rk, _dropA = rank_rows([_rA, _rB], keep=1)
    if [_rk[0]["判定"], _rk[1]["判定"]] != ["B", "A"] or _rk[1].get("dropped_by") != "成績下位" or not _dropA:
        ng.append("⑩: 並べる鍵（2つの先読みの平均）か 成績下位 が違う")
    # ⑪ 段の口が組む束（判定の束だけ・入口の木は空）を、合成データで最後まで測れる（束を組む→解決表→列→3つの割合・関所で拒否の行・監査 CP48）
    _n11 = 2000
    _c11 = 100.0 + (np.arange(_n11) % 7)
    _df11 = pd.DataFrame({"ts": pd.date_range("2024-03-01", periods=_n11, freq="5min"), "close": _c11,
                          "v11_res_hi": _c11 * (1.0 + (np.arange(_n11) % 5) / 1000.0), "v11_res_lo": _c11,
                          "v11_sup_hi": _c11, "v11_sup_lo": _c11 * 0.99, "v11_mid": _c11})
    _w11 = {"role": "location", "form": "level", "material": [{"geo": "W%"}], "side": "above",
            "value": {"threshold_q": "q50"}}
    _rec11 = [_stage_recipe("e38", "t11_ok", _wrap_bundle([_w11], None, None, "regime_t11_ok")),
              _stage_recipe("e38", "t11_ng", _wrap_bundle([{"not": {"bool_col": "t11_no_such_col", "want": True}}],
                                                          None, None, "regime_t11_ng"))]
    try:
        _rows11 = measure(_df11, _rec11, _df11["ts"].iloc[0], _df11["ts"].iloc[-1], with_trades=False)
        _ok11 = [r for r in _rows11 if r.get("判定") == "t11_ok" and "①時間の割合" in r and "捉えた(先24本)" in r]
        _ng11 = [r for r in _rows11 if r.get("判定") == "t11_ng" and str(r.get("注", "")).startswith("関所で拒否")]
        if not _ok11 or not _ng11:
            ng.append(f"⑪: 段の口の束を測れない（測れた {len(_ok11)}・関所で拒否 {len(_ng11)}）")
    except BaseException as _e11:
        ng.append(f"⑪: 段の口の束を測る所で止まった: {type(_e11).__name__} {str(_e11)[:80]}")
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:253「        ng.append(f"④: 診断のコードに未来参照の式が在る: {bad4}")」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 258行（selftest の印字）
直す前の文字:
~~~
    print(f"[selftest] ①100%/0% ／ ②反転で 1−x（x={x:.2f}）・真0本は nan ／ ③束なしは止まる ／ ④未来参照 0件 ／ ⑤印は observe_diag の関数")
~~~
直した後の文字:
~~~
    print(f"[selftest] ①100%/0% ／ ②反転で 1−x（x={x:.2f}）・真0本は nan ／ ③束なしは止まる ／ ④未来参照 0件 ／ ⑤印は observe_diag の関数"
          f" ／ ⑥捉えた割合（既知答え・反転・正解0本は nan）／ ⑦乱数 0件 ／ ⑧record_run ／ ⑨落ちた候補の5つの場面 ／ ⑩並べる鍵は平均")
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:258「    print(f"[selftest] ①100%/0% ／ ②反転で 1−x（x={x:.2f}）・真0本は nan ／ ③束なしは止まる ／ ④未来参照 0件 ／ ⑤印は observe_diag の関数")」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 273〜279行（--seed と --no-trades の argparse）
直す前の文字:
~~~
    # ★2026-09-16（監査 cp36 の M-7 の #11・別枠 S-7）＝説明を実物に合わせた。
    #   直す前の文「閾値の分位・続く長さ（範囲で探す値）の種」は、乱数で引いていた頃のもの。
    #   いまは閾値の分位も続く長さも乱数で引かない（`_thr_fixed`・`_nv_fixed`）。
    #   この種が効くのは `--build` で入口の束を組むとき（`sample_structure` の乱数）だけ。
    ap.add_argument("--seed", type=int, default=53,
                    help="--build で入口の束を組むときの種（判定の束の閾値・本数には効かない）")
    ap.add_argument("--no-trades", action="store_true", help="②（玉の成績）を測らない＝①③だけ（速い）")
~~~
直した後の文字:
~~~
    # ★2026-09-27（M2-F-2）＝--seed は消した（乱数がこの道具から消えた＝束は sample_regime_build の決まった並び）。
    #   --no-trades も消した＝net を既定で測らない（§2.2・まこさん決定 2026-09-01）。測るときだけ --trades。
    ap.add_argument("--trades", action="store_true",
                    help="②（玉の成績）も測る（run_recipe＋score.score・--recipe のときだけ・既定は測らない）")
    # ★恒久の決まり24番＝走行の目的を必ず書く（道具の確認は check）。record_run は既定を持たない。
    ap.add_argument("--purpose", choices=["search", "check"], default=None,
                    help="走行の目的（search＝累積に数える／check＝確認の帳簿・測る走行で必須）")
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:279「    ap.add_argument("--no-trades", action="store_true", help="②（玉の成績）を測らない＝①③だけ（速い）")」
状態: 確定

#### 実装 12
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 287〜288行（--dump-build の argparse の直後）
直す前の文字:
~~~
    ap.add_argument("--dump-build", type=int, default=None, metavar="N",
                    help="案 N の判定の束を JSON で画面に出す（固定のレシピを作るため・読むだけ）")
~~~
足す文字:
~~~

    # ★2026-09-27（M2-F-2 の (k)・M2-F-15・リスク8）＝段ごとに測る口・差し戻しの口・値なしの口。
    ap.add_argument("--stage", default=None, choices=["width", "stage1", "stage2a", "stage2b", "stage2c", "stage3"],
                    help="段の候補を全部 束にして測り、順位表と落ちた候補をファイルに書く（M2-F-8〜14）")
    ap.add_argument("--top", default=None,
                    help="前の段の順位表（rank_*.json）＝上位（stage_keep_of の本数）と候補を掛け合わせる")
    ap.add_argument("--sweep", default=None,
                    help="段4 差し戻し＝順位表（か行）の束の1枠ずつを入れ直して1周・良くならなくなるまで（M2-F-15）")
    ap.add_argument("--nan-check", action="store_true",
                    help="BB幅 の動く線の材料の値なしを数える（リスク8・まこさん決定「案1」・測らない）")
    ap.add_argument("--limit", type=int, default=None,
                    help="--stage で測る束を先頭から N本 だけにする（束1本の時間の実測のため・M2-F-5・道具の確認なので --purpose check）")
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:288「                    help="案 N の判定の束を JSON で画面に出す（固定のレシピを作るため・読むだけ）")」
状態: 確定

#### 実装 13
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 303〜304行（入口の指定が無いときの止まり）
直す前の文字:
~~~
    if not a.recipe and not a.build:
        ap.error("--recipe か --build N か --candidates <段> を指定")
~~~
直した後の文字:
~~~
    if a.trades and not a.recipe:
        ap.error("--trades は --recipe のときだけ（--build・--stage の束は入口を持たない＝玉を測れない）")
    if not (a.recipe or a.build or a.stage or a.sweep or a.nan_check):
        ap.error("--recipe か --build N か --candidates <段> か --stage <段> か --sweep <順位表> か --nan-check を指定")
    if (a.recipe or a.build or a.stage or a.sweep) and not a.purpose:
        ap.error("--purpose search か check を書く（恒久の決まり24番＝道具の確認は check）")
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:304「        ap.error("--recipe か --build N か --candidates <段> を指定")」
状態: 確定

#### 実装 14
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 308〜309行（データを読む所）
直す前の文字:
~~~
    ad = et.load_adapter(a.strategy)
    df, = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END)], et.WARM)
~~~
直した後の文字:
~~~
    ad = et.load_adapter(a.strategy)
    # ★M2-F-2＝段2c の動く線（6か月の窓）も測る道具なので、余白を stage_warm で延ばして読む
    #   （まこさん決定 2026-09-27「余白の直し方→C」の続き・m2_todo の M2-F-2 の注意）。
    _warm = g.stage_warm(et.WARM)
    if a.nan_check:
        return run_nan_check(ad, _warm, a)
    df, = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END)], _warm)
    if a.stage:
        return run_stage(df, a)
    if a.sweep:
        return run_sweep(df, a)
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:309「    df, = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END)], et.WARM)」
状態: 確定

#### 実装 15
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 310〜334行（--build の乱数の塊）
直す前の文字:
~~~
    recipes = []
    if a.recipe:
        recipes.append(json.loads(pathlib.Path(a.recipe).read_text(encoding="utf-8")))
    else:
        pool, tfs, _ = g.material_pool()
        lm, _w = g.load_limits()
        lm = g.resolve_hold_range(lm, a.strategy)
        lim = {"n_min": None, "p_max": lm.get("p_max"), "count_range": lm.get("count_range"),
               "role_max": lm.get("role_max"), "depth_max": lm.get("depth_max"), "k_max": lm.get("k_max"),
               "r_min": lm.get("r_min")}
        regime = ad.regime("S2")
        i = 0
        tries = 0
        while len(recipes) < a.build and tries < a.build * 20:
            rng = np.random.default_rng([a.seed, 1, tries])
            tries += 1
            try:
                r = g.sample_structure(rng, lm, pool, tfs, side="SHORT", regime=regime, logic_id=f"R9_{i}",
                                       build_regime=True, regime_order_n=i)
                g.validate_drawn(r, limits=lim)          # ★69回目＝印を外してから検査に通す（原因A の直し・番人 T31）
            except (g.SampleError, ex.RecipeError) as e:
                print(f"  [組めない] 案 {i}: {str(e)[:80]}（同じ番号で引き直す）")
                continue
            recipes.append(r)
            i += 1
~~~
直した後の文字:
~~~
    recipes = []
    dropped: list[dict] = []
    if a.recipe:
        recipes.append(json.loads(pathlib.Path(a.recipe).read_text(encoding="utf-8")))
    else:
        # ★2026-09-27（M2-F-2 の (d)）＝束は sample_regime_build（判定の束だけ・乱数0件・成績表の順位 × 案の番号の
        #   決まった並び）で組む。直す前は sample_structure（入口まで含むレシピ・細部に乱数）を rng で呼んでいた。
        #   組めない案は引き直さない（乱数が無いので引き直しても同じ）＝落ちた候補として残す（(l)）。
        pool, tfs, _ = g.material_pool()
        lm, _w = g.load_limits()
        lm = g.resolve_hold_range(lm, a.strategy)
        table = g.load_signal_table()
        for i in range(a.build):
            try:
                bd, drw = g.sample_regime_build(lm, pool, tfs, table, order_n=i)
                # ★直す前の validate_drawn と同じく、法則（G7）に反する束は測らない（監査 CP48）
                ex._check_scene_rules({"name": "range", "build": g.strip_marks(bd)}, "")
                rec = _stage_recipe(a.strategy, f"R9_{i}", bd)
                rec["meta"]["regime_draw"] = drw
                recipes.append(rec)
            except (g.SampleError, ex.RecipeError) as e:
                print(f"  [組めない] 案 {i}: {str(e)[:80]}")
                dropped.append({"場面": "組めない", "判定": f"R9_{i}", "理由": str(e)[:120]})
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:324「            rng = np.random.default_rng([a.seed, 1, tries])」
状態: 確定

#### 実装 16
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 335〜339行（main の測って出す所）
直す前の文字:
~~~
    print(f"[R9] 値決め窓 {SEARCH_START}〜{SEARCH_END} ／ 束 {len(recipes)} 本 ／ 玉の成績を{'測らない' if a.no_trades else '測る（run_recipe＋score.score）'}")
    rows = measure(df, recipes, SEARCH_START, SEARCH_END, with_trades=not a.no_trades)
    _print_rows(rows)
    print("\n[機械が読む形]")
    print(json.dumps(rows, ensure_ascii=False, default=float))
~~~
直した後の文字:
~~~
    print(f"[R9] 値決め窓 {SEARCH_START}〜{SEARCH_END} ／ 束 {len(recipes)} 本 ／ 玉の成績を{'測る（run_recipe＋score.score）' if a.trades else '測らない（既定）'}")
    rows = measure(df, recipes, SEARCH_START, SEARCH_END, with_trades=a.trades)
    rows, _dr = rank_rows(rows)            # keep=None＝この口では成績下位を作らない（並べて順位を付けるだけ）
    dropped += [{"場面": ("関所で拒否" if str(r.get("注", "")).startswith("関所で拒否") else "測れない"),
                 "判定": r.get("判定"), "理由": r.get("注")} for r in rows if "①時間の割合" not in r]
    _print_rows(rows)
    write_outputs("recipe" if a.recipe else "build", rows, dropped)
    _record(a, "recipe" if a.recipe else "build", len(recipes))
    print("\n[機械が読む形]")
    print(json.dumps(rows, ensure_ascii=False, default=float))
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:336「    rows = measure(df, recipes, SEARCH_START, SEARCH_END, with_trades=not a.no_trades)」
状態: 確定

#### 実装 17
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 7〜11行（説明文の測るもの3つ）
直す前の文字:
~~~
  ① レンジと判定した時間の割合   ＝ 値決め窓で判定が真のバー ÷ 全バー
  ② その中の玉の成績             ＝ 判定の列を entry_col に向けて run_recipe → 値決め窓の玉だけを score.score に通す
                                   → 件数・net 合計・件数/日（★net は審判の数字をそのまま出す＝この診断は計算しない。勝率は審判が返さないので出さない）
  ③ 実はトレンドだった割合       ＝ 判定が真のバーのうち、observe_diag._regime_labels の「強さ」（先 n本の ER が窓の
                                   中央値以上）が真の割合。先読み n は成績表と同じ2つ（_regime_horizons）
~~~
直した後の文字:
~~~
  ① レンジと判定した時間の割合   ＝ 値決め窓で判定が真のバー ÷ 全バー（＝言った割合）
  ② その中の玉の成績             ＝ 判定の列を entry_col に向けて run_recipe → 値決め窓の玉だけを score.score に通す
                                   → 件数・net 合計・件数/日（★net は審判の数字をそのまま出す＝この診断は計算しない。勝率は審判が返さないので出さない）
                                   ★既定では測らない（--trades を付けたときだけ＝§2.2「net は M2-L まで使わない」・M2-F-2 の (c)）
  ③ 実はトレンドだった割合       ＝ 判定が真のバーのうち、observe_diag._regime_labels の「強さ」（先 n本の ER が窓の
                                   中央値以上）が真の割合。先読み n は成績表と同じ2つ（_regime_horizons）
  ＋当たった割合（1−③）・捉えた割合（正解がレンジのうち判定が真・正解0本なら nan）・正解レンジの割合（≈50%）を出し、
    第一キー＝③の2つの先読みの平均の低さ・第二キー＝捉えた割合の平均の高さで並べる（まこさん決定 2026-09-27「１は平均でOK」）。
~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:7「  ① レンジと判定した時間の割合   ＝ 値決め窓で判定が真のバー ÷ 全バー」
状態: 確定

#### 実装 18
対象のファイル: .claude/breaks/b113_catch_share_broken.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
足す文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 捉えた割合の正解の向きを逆にすると、番人⑥が「正解レンジが0本なのに nan でない」で落ちた
# EXPECT_MSG: ❌ ⑥
# b113 — r9_catch_share の分母（正解がレンジ＝強さが偽 ∧ 使える）から否定を外すと、⑥が落ちるか（M2-F-2・2026-09-27）
#   守っているもの＝完成の条件 #1（捉えた割合の式＝正解がレンジのバーのうち判定が真・正解0本なら nan）
#   壊し方＝`    m = (~np.asarray(strong, bool)) & np.asarray(usable, bool)` の否定（~）を外す。
#   期待＝regime_r9_diag.py --selftest の⑥が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    m = (~np.asarray(strong, bool)) & np.asarray(usable, bool)\n'
if s.count(old) != 1:
    raise SystemExit("[b113] 壊す対象の行が1か所でない: " + old.strip())
new = '    m = np.asarray(strong, bool) & np.asarray(usable, bool)  # b113 が壊した（正解の向きを逆にする）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b104_atr1h_own_tf.sh:1「#!/bin/bash」
状態: 確定

#### 実装 19
対象のファイル: .claude/breaks/b114_default_rng_back.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
足す文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 乱数を使う行を道具に戻すと、番人⑦が「乱数の道が残っている: default_rng」で落ちた
# EXPECT_MSG: ❌ ⑦
# b114 — main に default_rng を使う行を戻すと、⑦（構文木の見張り）が落ちるか（M2-F-2・恒久67番・2026-09-27）
#   守っているもの＝完成の条件 #2（乱数がこの道具に残っていない）
#   壊し方＝`    ad = et.load_adapter(a.strategy)` の直後に `_rng = np.random.default_rng(0)` を足す。
#   期待＝regime_r9_diag.py --selftest の⑦が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    ad = et.load_adapter(a.strategy)\n'
if s.count(old) != 1:
    raise SystemExit("[b114] 壊す対象の行が1か所でない: " + old.strip())
new = '    ad = et.load_adapter(a.strategy)\n    _rng = np.random.default_rng(0)  # b114 が壊した（乱数の道を戻す）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b104_atr1h_own_tf.sh:1「#!/bin/bash」
状態: 確定

#### 実装 20
対象のファイル: .claude/breaks/b115_record_run_renamed.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
足す文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 試行を数える口の呼び出しを別の名前に替えると、番人⑧が「record_run が1回も呼ばれていない」で落ちた
# EXPECT_MSG: ❌ ⑧
# b115 — ts.record_run( の呼び出しを ts.record_run_off( に替えると、⑧が落ちるか（M2-F-2・§2.2・恒久24番・2026-09-27）
#   守っているもの＝完成の条件 #3（測る走行が試行を累積に数える）
#   壊し方＝`ts.record_run(` を全部（1か所の見込み） `ts.record_run_off(` に替える。
#   期待＝regime_r9_diag.py --selftest の⑧（構文木の見張り）が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'ts.record_run('
if s.count(old) != 1:
    raise SystemExit("[b115] 壊す対象が1か所でない: " + old)
new = 'ts.record_run_off('
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b104_atr1h_own_tf.sh:1「#!/bin/bash」
状態: 確定

#### 実装 21
対象のファイル: .claude/breaks/b116_dropped_file_not_written.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
足す文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 落ちた候補のファイルを書かない形にすると、番人⑨が「5つの場面が全部 ファイルに出ない」で落ちた
# EXPECT_MSG: ❌ ⑨
# b116 — write_outputs が落ちた候補（dropped_*.json）を書かない形にすると、⑨が落ちるか（M2-F-2 の (l)・2026-09-27）
#   守っているもの＝完成の条件 #4（落ちた候補の5つの場面が全部 ファイルに出る）
#   壊し方＝dropped を書く write_text の行を、書かない行に替える。
#   期待＝regime_r9_diag.py --selftest の⑨が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    dp.write_text(json.dumps(dropped, ensure_ascii=False, indent=1, default=float) + "\\n", encoding="utf-8")\n'
if s.count(old) != 1:
    raise SystemExit("[b116] 壊す対象の行が1か所でない: " + old.strip())
new = '    pass  # b116 が壊した（落ちた候補を書かない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b104_atr1h_own_tf.sh:1「#!/bin/bash」
状態: 確定

#### 実装 22
対象のファイル: .claude/breaks/b97_demand_not_attached.sh
直す箇所: 31行（測るコマンド）
直す前の文字:
~~~
measure python3 "$PR/regime_r9_diag.py" --recipe "$PR/recipes/r9_demand_fixture.json" --no-trades
~~~
直した後の文字:
~~~
measure python3 "$PR/regime_r9_diag.py" --recipe "$PR/recipes/r9_demand_fixture.json" --purpose check
~~~
根拠の抜き書き: .claude/breaks/b97_demand_not_attached.sh:31「measure python3 "$PR/regime_r9_diag.py" --recipe "$PR/recipes/r9_demand_fixture.json" --no-trades」
状態: 確定

#### 実装 23
対象のファイル: .claude/breaks/b97_demand_not_attached.sh
直す箇所: 18行（控えに写すファイル）
直す前の文字:
~~~
guard "$DIAG"
~~~
直した後の文字:
~~~
guard "$DIAG" "$SDK/.claude/ratchet/engine_tuner_check_runs.json"
~~~
根拠の抜き書き: .claude/breaks/b97_demand_not_attached.sh:18「guard "$DIAG"」
状態: 確定

#### 実装 24
対象のファイル: .claude/breaks/b117_stage_recipe_no_entry.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
足す文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 段の口の束から入口の木を外すと、番人⑪が「段の口の束を測る所で止まった」で落ちた
# EXPECT_MSG: ❌ ⑪
# b117 — _stage_recipe から入口の木（entry）を外すと、⑪が落ちるか（M2-F-2・監査 CP48）
#   守っているもの＝完成の条件 #7（段の口が組む束を、合成データで最後まで測れる）
#   壊し方＝_stage_recipe の入口の木の行を、閉じ括弧だけの行に替える（入口の木の無い束に戻す）。
#   期待＝regime_r9_diag.py --selftest の⑪が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

DIAG="$PR/regime_r9_diag.py"
guard "$DIAG"

python3 - "$DIAG" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            "entry": {"connective": {"all": []}}}\n'
if s.count(old) != 1:
    raise SystemExit("[b117] 壊す対象の行が1か所でない: " + old.strip())
new = '            }  # b117 が壊した（入口の木を外す）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$DIAG" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b104_atr1h_own_tf.sh:1「#!/bin/bash」
状態: 確定

<!-- ACC_IMPL_END -->

### 4-A この節に何を書いたか（一覧）

**★この表は管理のためのものです。**設計の中身は上の 4-0 から順に読んでください。

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

| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 並べる鍵の nan は最後に置く（両方の先読みが nan の束を上位に出さない） | 測れない束が上位10本に混ざると、次の段が空の束を掛け合わせる | nan を0として扱う。捨てた理由＝嘘の数字になる（③=0 は最好成績の意味になってしまう） |
| 2 | --purpose（search／check）を測る走行の必須の旗にする | 恒久24番（道具の確認は必ず check）と違反の記録 #20（確認の走行を search で走らせて累積を増やした）の再発防止。record_run は既定を持たない（呼ぶ側が必ず宣言する） | 全部 search で数える。捨てた理由＝道具の確認の走行まで累積に入り、DSR の N が実態より増える |
| 3 | 順位表の行に 内側・枠・包み を残す | 次の段（--top）と差し戻し（--sweep）が、束を機械で読んで組み直せる形にする（手で写さない・恒久69番） | レシピ全体を行に入れる。捨てた理由＝この束は判定だけで入口を持たない＝要らない欄が誤解を生む |
| 4 | --seed と --no-trades の旗を消す | 乱数が消えるので種は意味を失い、net を測らないのが既定になるので旗の意味が逆になる。残すと読み手が混乱する | 旗を残して無視する。捨てた理由＝効かない旗は嘘の口になる |
| 5 | RG-v5 の比べる行は今までどおり出す | 選抜の毎回で、いまの E38 の判定との差が1つの表で見える | 段の走行では消す。捨てた理由＝比べる相手が無い順位表は、良し悪しの当たりが付かない |
| 6 | 壊すプログラムを4本 作る（b113〜b116） | この道具は選抜の採点係＝どの束が次の段へ進むかを決める＝BOT の中身に触る（恒久71番の線引きの内） | 付けない。捨てた理由＝並べる鍵・乱数・試行の数え・落ちた候補は、壊れると選抜が黙って狂う |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

<!-- ACC_SELFTEST_START hash=fbec820fa49bcc5a gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝元データの「完成の条件」。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b113_catch_share_broken.sh` | #1 | 捉えた割合の式の正解の向きを逆にすると、⑥が『❌』で落ちる |
| `b114_default_rng_back.sh` | #2 | default_rng を使う行を戻すと、⑦が『❌』で落ちる |
| `b115_record_run_renamed.sh` | #3 | record_run の呼び出しを別の名前に替えると、⑧が『❌』で落ちる |
| `b116_dropped_file_not_written.sh` | #4 | 落ちた候補のファイルを書かない形にすると、⑨が『❌』で落ちる |
| `b117_stage_recipe_no_entry.sh` | #7 | 段の口の束から入口の木を外すと、⑪が『❌』で落ちる |
| `—` | #5・#6 | 壊すプログラムは付けない（壊し方は上の4本） |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

| # | リスク | どうするか |
|---|---|---|
| 1 | regime_r9_diag.py --selftest の時間が分からない（⑥〜⑩と段2c の候補作りが増える） | 走らせる前に worklog から過去の実測を探す。無ければ まこさんに報告してから走らせる（恒久61・62番） |
| 2 | stage_warm で読む範囲が延び、固定のレシピの①③が M2-F-1 の実測と少し変わる（長い記憶の指標が窓の始まりで変わる） | 実装の後の走行で、M2-F-1 の数字（①5.30%・③50.3%／51.4%）と並べて貼り、差を隠さない |
| 3 | 段の走行の解決表が、束の本数ぶんの鍵を1回で作る＝メモリと時間が増える | M2-F-5 で束数本の実測を先に取り、M2-F-8 のフロー宣言に実測根拠を書く（恒久61番）。同じ材料の鍵は1つにまとまる（M2-E-3 の手順3の実測＝34.3%減・python3 .claude/tools/gen_s22_fidelity.py --keys 50） |
| 4 | 段3 の包み（off の作り方）が sample_regime_build と食い違う | _loose_q_fixed（生成器の同じ関数）を呼び、緩め方の判定は書き写さない。束ね方の形は監査 CP48 と G7（M2-F-14）が見る |
| 5 | record_run の n_trials は「束の本数」で、似た動きをまとめた数ではない | record_run の説明（まとめた後の数を渡す）と食い違う向きに倒れる＝数は多めに入り、DSR の罰は重い側＝甘くならない。note にその旨を書いて残す |
| 6 | 順位表の JSON は git の外＝手で書き替えられる | 塞げないものに書く。走行の画面とファイルの日時を worklog に残し、まこさんの目で照らせる形にする |

### 6-3 見積もり

| 何 | 見込み | 根拠 |
|---|---|---|
| コードの直し（当てる道具で当てる17件・壊すプログラム4本を Write） | 30分 | ★測っていない。当てる処理は道具が数秒で終わる |
| 走らせて確かめる（selftest・固定のレシピ・壊すプログラム4本） | selftest の実測が出るまで確定しない | 4-14（selftest 未実測・固定のレシピ 約9秒） |
| M2-F-7 と印の取り直し（実装と同じ回） | 約6分半 | G2 約30秒・H2 約5〜6分（2026-09-26 の実測 H2 303.9秒） |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

**① 真因（root cause）**＝①M2-F の選抜（測って・並べて・上位を渡して・落ちた候補を残す）に要る機能が、測る道具に無いことです（捉えた割合0件・順位0件・ファイル書き0件・record_run 0件）。②--build が入口まで含むレシピを sample_structure で組む古い形のままで、乱数（default_rng・324行）が残っていることです（判定の束だけを乱数ゼロで組む sample_regime_build は完成済みなのに、この道具が呼んでいない）。③落ちた候補のうち組めない・関所で拒否の2つの場面が、どこにも記録されないことです。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。動くのは、レンジ判定の候補の選抜の道具です。判定の成績は M2-F-8〜15 で、net は M2-L で測ります。

**③ root か symptom か**＝root です。段の選抜を手作業（画面の数字を手で写して次の段へ渡す）で回す形は、写し間違いと隠れた落ちを生む symptom の運用です。この設計は、並べる鍵・ファイルの受け渡し・落ちた候補の記録・試行の累積を道具の中に作り、手写しを消します。乱数も、指摘された場所だけでなく道具から丸ごと消します（違反の記録 #24＝直したフリ、の再発防止）。

**④ ベースアップ**＝3つの割合の式の外の一次資料は 2026-09-06 に確かめて正本に記録済みです（milestones2:2000＝scikit-learn の評価指標の頁・Wikipedia「Precision and recall」・arXiv 2605.30363・arXiv 2607.17555〔precision・recall・陽性の比率を一緒に出す〕）。この設計はその式を実装するだけで、新しい式を作らないので、新しい検索はしていません。読むもの宣言（design_read_plan.md・まこさんの OK「OK」2026-09-27）の17件を Read tool で開きました（worklog 20260927 §15）。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

この工事に、疑似シミュから取った値は1つもありません。並べる鍵の平均は まこさんの決定、先読みの本数（24・288）と保つ上限の範囲は承認済みの設定、上位を渡す本数10本は まこさんの決定、書き先は まこさんの決定（骨組み2）です。閾値は既存の分位の1点のままです。

### 7-3 変更の単位（H16）

「M2-F の段ごとの選抜の採点係を作る」の1つです。捉えた割合・順位・ファイル書き・段の口・差し戻しの口・乱数の撤去・試行の数え・--nan-check は、その1つを作るための部品です（束3＝まこさん OK 2026-09-24。H16 を満たさないことは捨てるものとして決定済み）。H1〜H15 と審判整合（群2）は非該当です（売買のロジックにも審判にも触れないため。H2 と H6 は 4-6 で照らしました）。過去に取りやめた失敗の再演か＝当たりません（乱数のくじ引き〔#14・#24〕を消す側です）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | この工事は乱数を消す側です。束は sample_regime_build（成績表の順位 × 案の番号の決まった並び）で組み、候補は build_stage_candidates（乱数0件）が作り、番人⑦が default_rng と sample_structure の残りを構文木で見張ります。 |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 候補・閾値・範囲は承認済みの置き場（成績表・quantile_range・state_hold_bars_range）のままで、私が点の一覧を作りません。上位を渡す本数10本は まこさん決定（2026-09-18）で、設定の欄（stage_keep_range）から読みます。 |

### 7-4 塞げないもの

| 問い | 塞げないこと |
|---|---|
| **束が無いレシピの場面は、実走のファイルに出るか** | 出ません。束の無いレシピは fail-closed で止まる（いまの100行の形を保つ）ので、ファイルには書けません。5つの場面が全部そろうのは番人⑨（合成）だけです |
| **順位表のファイルを手で書き替えて --top に渡したら** | 上位でない束を次の段へ進められます。ファイルは git の外です。走行の画面と日時を worklog に残し、まこさんの目で照らします |
| **段3 の包み（off の作り方）が生成器と同じか** | 形は生成器と同じに書きます（監査 CP48 の修正7・9）が、同じ関数ではありません（1変更の制約で生成器に関数を足せない）。★生成器そのものの段2a の出る線（off_c）は、入る側の内側で真になる向きです（監査 CP48 が工事の外として見つけた＝緩めるなら1つ上の段）。この道具も同じ向きになります。直すのは M2-F-14（段3 を測る）の前の1変更で、そのとき この道具の出る線も一緒に直します（まこさん決定 2026-09-28「決めることは、CCのおすすめの通りでOK」・next_step §6） |
| **並べる鍵の平均は、両方の先読みが揃わない束をどう扱うか** | 片方の先読みでも nan なら平均を取らず、測れない束と同じく最後に置きます（監査 CP48 で、nan を除いた平均＝残りの1つで並べる形から直した）。捉えた割合（第二キー）は nan を除いた平均のままです。この扱いは正本に書かれていません |
| **record_run の n_trials（束の本数）は、似た動きをまとめた数か** | まとめていません。数は多めに入り、DSR の罰は重い側に倒れます（甘くならない向き） |
| **--nan-check の結果（値なしが在るか）** | 実装の前には分かりません。在れば rc=1 で止まって まこさんに出します（完成の条件に載せない理由＝やらないこと9） |
| **段の走行の実測の時間** | この設計では分かりません（かけ算の目安だけ）。M2-F-5 で束数本を実測してから、M2-F-8 のフロー宣言に書きます |
| **この道具と壊すプログラムそのものを書き換えられたら** | 書き換えれば無効にできます。承認で凍結され、差分は git に出ます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認済みで凍結されているため） |

### 7-5 §4.6 ハード制約の照合

<!-- ACC_CHECKLIST_START hash=c768565bd4893beb gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

- 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記）
- 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine`
- 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ
- 【群1】① 真因（root cause・損/不足の構造的原因）
- 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか）
- 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由）
- 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止）
- 【群1】変更は 1レバーか（複数混ぜない）
- 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行）
- 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（
- 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R
- 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、
- 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前）
- 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che
- 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設
- 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc
- 【群1】H16 1変更・過去失敗の不再演
- 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③）
- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。**★触る関数の一覧は、実装の後に確定させます**＝`verify_design_contract.py --write` の出力で置き替えます。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 捉えた割合と並べる鍵の番人が通る（⑥＝全部真→1.0／全部偽→0.0／正解0本→nan／判定の反転で 1−x、⑩＝2つの先読みの平均で並ぶ・成績下位が付く） | `python3 scripts/priority_rebuild/regime_r9_diag.py --selftest` | 実経路 | 捉えた割合の式の正解の向きを逆にすると、⑥が『❌』で落ちる | `b113_catch_share_broken.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝捉えた割合の正解の向きを逆にすると、番人⑥が「正解レンジが0本なのに nan でない」で落ちた |
| 2 | 乱数がこの道具に残っていない（⑦＝default_rng・sample_structure を構文木で見る・恒久67番） | `python3 scripts/priority_rebuild/regime_r9_diag.py --selftest` | 実経路 | default_rng を使う行を戻すと、⑦が『❌』で落ちる | `b114_default_rng_back.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝乱数を使う行を道具に戻すと、番人⑦が「乱数の道が残っている: default_rng」で落ちた |
| 3 | 試行を累積に数える口が呼ばれている（⑧＝record_run の呼び出しを構文木で見る・§2.2・恒久24番） | `python3 scripts/priority_rebuild/regime_r9_diag.py --selftest` | 実経路 | record_run の呼び出しを別の名前に替えると、⑧が『❌』で落ちる | `b115_record_run_renamed.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝試行を数える口の呼び出しを別の名前に替えると、番人⑧が「record_run が1回も呼ばれていない」で落ちた |
| 4 | 落ちた候補の5つの場面（組めない・測れない・束が無い・関所で拒否・成績下位）が全部 ファイルに出る（⑨） | `python3 scripts/priority_rebuild/regime_r9_diag.py --selftest` | 実経路 | 落ちた候補のファイルを書かない形にすると、⑨が『❌』で落ちる | `b116_dropped_file_not_written.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝落ちた候補のファイルを書かない形にすると、番人⑨が「5つの場面が全部 ファイルに出ない」で落ちた |
| 5 | 自己テストが全部 通る（①〜⑪・実データの試行ゼロ・⑪＝段の口の束を合成データで最後まで測れる） | `python3 scripts/priority_rebuild/regime_r9_diag.py --selftest` | 実経路 | 壊すプログラムは付けない（壊し方は上の4本） | `—` | — | **未着手** |
| 6 | 固定のレシピが rc=0 で走り、順位表と落ちた候補のファイルが results/priority_rebuild/regime_r9/ に書かれる（確認の走行＝check で数える） | `cd v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild && python3 regime_r9_diag.py --recipe recipes/r9_demand_fixture.json --purpose check` | 実経路 | 壊すプログラムは付けない（書けなければ rc≠0 か ⑨が落ちる） | `—` | — | **未着手** |
| 7 | 段の口が組む束（判定の束だけ・入口の木は空）を、合成データで最後まで測れる（⑪＝束を組む→解決表→列→3つの割合・関所で拒否の行） | `python3 scripts/priority_rebuild/regime_r9_diag.py --selftest` | 実経路 | 段の口の束から入口の木を外すと、⑪が『❌』で落ちる | `b117_stage_recipe_no_entry.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝段の口の束から入口の木を外すと、番人⑪が「段の口の束を測る所で止まった」で落ちた |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

<!-- ACC_CODEREF_START hash=3f8867f9cdc786eb gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/regime_r9_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `r9_catch_share` | 68 |
| `rank_rows` | 107 |
| `write_outputs` | 136 |
| `record_run` | （この関数は実物に無い） |
| `stage_warm` | （この関数は実物に無い） |
| `sample_regime_build` | （この関数は実物に無い） |
| `DROP_KINDS` | （この関数は実物に無い） |
| `--purpose` | （この関数は実物に無い） |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 25件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

<!-- ACC_SPEC_START hash=11ac95dccc729786 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/regime_r9_diag.py",
  "impl_functions": {
    "scripts/priority_rebuild/regime_r9_diag.py": [
      "<モジュール直下>",
      "r9_catch_share",
      "r9_range_share",
      "rank_key",
      "rank_rows",
      "write_outputs",
      "_q50_width_cond",
      "_loosened_off",
      "_wrap_bundle",
      "_load_top",
      "_stage_recipe",
      "_record",
      "_nanmean",
      "run_stage",
      "run_sweep",
      "run_nan_check",
      "measure",
      "_print_rows",
      "selftest",
      "main"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数。r9_catch_share・r9_range_share・rank_key・rank_rows・write_outputs・_q50_width_cond・_loosened_off・_wrap_bundle・_load_top・run_stage・run_sweep・run_nan_check は新設。定数 OUT_DIR・DROP_KINDS はモジュール直下で数える。照合A は commit 済みの版（HEAD）との差で数える＝直すファイルの差は0（なぜ作るかの7行目）。",
  "self_check_calls": [
    "r9_catch_share",
    "rank_rows",
    "write_outputs",
    "record_run",
    "stage_warm",
    "sample_regime_build",
    "DROP_KINDS",
    "--purpose"
  ],
  "_self_check_calls の意味": "7-7 の表に出す regime_r9_diag.py の名前。全部この工事で新しく書くので、実装の後に在る。",
  "must_use": {
    "main": [
      "stage_warm",
      "sample_regime_build",
      "rank_rows",
      "write_outputs",
      "_record"
    ],
    "run_stage": [
      "build_stage_candidates",
      "rank_rows",
      "write_outputs",
      "_record",
      "_wrap_bundle",
      "_check_scene_rules"
    ],
    "run_sweep": [
      "rank_rows",
      "write_outputs",
      "_record",
      "_wrap_bundle",
      "_check_scene_rules"
    ],
    "run_nan_check": [
      "build_stage_candidates",
      "_col_array"
    ],
    "_record": [
      "record_run"
    ],
    "selftest": [
      "r9_catch_share",
      "rank_rows",
      "write_outputs"
    ]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "この道具が外から読む一覧（候補・法則・成績表・範囲の鍵・印）の形は、この工事で変えない。候補は build_stage_candidates・束は sample_regime_build・余白は stage_warm を呼ぶだけで、番人⑥〜⑩が振る舞いで測る。",
  "generated_from": {
    "impl_functions": "設計の段で、中身を直す関数と新しく作る関数を書いた（HEAD との差が0なのを git で確かめた）",
    "must_use": "直した後に呼ぶ名前（4-3・4-18）",
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

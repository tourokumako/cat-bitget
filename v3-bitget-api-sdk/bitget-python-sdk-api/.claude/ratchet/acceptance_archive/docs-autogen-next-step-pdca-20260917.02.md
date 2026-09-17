<!-- ARC iter="docs-autogen-next-step-pdca-20260917" -->

# 設計書｜next_step.md（§0 の各節・§0-4・§5・§6）と pdca_flow.md の hook の一覧を、手で書かずに元データからプログラムで作り、手の書き替えと出どころの無い参照を止める

TARGET: .claude/tools/tidy_next_step.py, .claude/state/next_step.md, .claude/rules/pdca_flow.md, .claude/hooks/enforce_next_step_tidy.sh, .claude/settings.json
NEW_FILE: .claude/tools/gen_hook_list.py, .claude/state/next_step_src.json, .claude/state/hook_roles.json, .claude/hooks/forbid_edit_generated_docs.sh, .claude/hooks/forbid_edit_generated_docs.py
MODEL: .claude/tools/gen_session_todo.py, .claude/tools/gen_regime_kb.py, .claude/hooks/enforce_checked_edit.sh

REQUIREMENTS: まこさんの決定（下の §0）と、`engine_tuner_milestones2.md` の §2.2（レンジ判定の検索方法）。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書はプログラムが作ります。**手で書いたのは、元データ `.claude/ratchet/acceptance_src.json` の5つ（何を作るか・なぜ作るか・組み方・やらないこと・決めてほしいこと）だけです。残りは正本から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --write`。手で書き換えられていないかの検出＝`--verify`。

## 0｜まこさんの決定（逐語）

> ★この工事への決定（逐語）
> CCは確認せずミスを繰り返すので、手書きせざるをえないもの以外は自動生成にしてほしい。（2026-09-17）
> OK（2026-09-17・読むもの宣言 docs-autogen-next-step-pdca-20260917 への答え）
> OK（2026-09-17・宣言に gen_acceptance.py を足すことへの答え）
> 決めた欲しいことは、４つともCCのおすすめのやり方でOK（2026-09-17・3-2 の決めてほしいこと3つと、監査に出すか＝①next_step.md は全部の節 ②pdca_flow.md は §1 の表だけ ③生成部分の Write・Edit を止める hook を足す ④この設計書は監査に出さない）
> ★前から引き継ぐ決定（逐語）
> 監査、設計書以外の以下は、その文書を使う際に自動生成できるようにテンプレ化するので わすれないように書いておけ（2026-09-14・next_step §6 の188番）
> ヌケモレがおおいから、手で書かざるを得ない部分以外は自動生成にしろよ。（2026-09-09・恒久69番）
> hookの修正ごときで承認いれるな（2026-09-06）
> 毎回、next_stepが汚くなり、私が指示しないと整理されない状況なんだけど、改善できないのか？（2026-08-28）

## 1｜概要

私（CC）が next_step.md と pdca_flow.md の hook の一覧を手で書く道を塞ぎます。next_step.md は、機械が書いている (0-b-2) の1節を除いて、全部 手で書かれています（2-1 の表）。pdca_flow.md の hook の一覧も手で書かれていて、見出しの本数（69本）が settings.json の登録（72本）と合わず、今日足した hook 2本は一覧に1行もありません（2-1 の表）。作るものは3つです。①tidy_next_step.py を広げ、next_step.md を元データ next_step_src.json と json の印の値から全部 作ります。元データは、いまの next_step.md をプログラムが1文字も変えずに読み込んで作ります（最初の1回だけ）。作るときに、worklog の節の参照・★いまここ の件数・0-1 の日付・終わった行の移し先を、プログラムが照らします。②gen_hook_list.py（新設）が、pdca_flow.md の hook の一覧を、settings.json の登録と hook_roles.json（役割の文）から作ります。登録に在るのに役割の無い hook が在れば止まります。③hook forbid_edit_generated_docs（新設）が、この2つの文書の生成された部分を Write・Edit で直そうとした瞬間に止めます。Stop hook enforce_next_step_tidy.sh は、2つの道具の --verify を呼び、手の書き替えが残っていればターンを終われなくします。★私が手で書くのは、元データの中の文（何が問題か・次に何をするか・hook の役割の説明）だけです。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

| 何を測ったか | コマンド | 結果 |
|---|---|---|
| next_step.md のうち、機械が書いている節 | `grep -c 'json から書く' .claude/state/next_step.md ／ grep -c 'hash=' .claude/state/next_step.md` | 1（(0-b-2) の見出し）／0（2026-09-17）。ほかの節は全部 手で書いている |
| §6（あとで直すこと）の表の行 | `awk 'NR>144 && NR<315 && /^\／ /' .claude/state/next_step.md に grep -c '^／ \*\*[0-9]' と grep -c '^／ — ' と wc -l` | 番号つき 93行・「—」の行 3行・表の行 全部で 107行（2026-09-17）。全部 手で書いている |
| 表の中の縦棒のエスケープ（読み込みで壊しやすい所） | `grep -c '\\／' .claude/state/next_step.md` | 4行（2026-09-17） |
| settings.json に登録された hook の本数 | `grep -o 'hooks/[a-z0-9_]*\.sh' .claude/settings.json ／ sort -u ／ wc -l` | 72（2026-09-17） |
| pdca_flow.md の hook の一覧の見出しの本数 | `grep -n '実測 69本' .claude/rules/pdca_flow.md` | 「hook 一覧（実測 69本・登録は settings.json）」＝登録の72本と合わない |
| 今日足した hook 2本が一覧に在るか | `grep -c 'show_breaks_on_code_edit\／require_selftest_after_source_edit' .claude/rules/pdca_flow.md` | 0（2026-09-17） |
| next_step の検査の道具が見ているもの | `Read tool で開いた（tidy_next_step.py の verify）` | (a) 消す印の節 (b) 0-1 の日付 (c) 印の値 (d) §0 の行数 (e) ★いまここ の件数 (f) 0-2 の終わった行、の6つ。手の書き替えと、worklog の節の参照が在るかは見ていない |
| 今日 ToDo ゲートで見つけた不具合（§6 に積む相手） | `grep -n 'files\[-1\]' .claude/hooks/enforce_todo_declaration.py` | worklog_sections が `p = files[-1]`＝いちばん新しい worklog だけの見出しを集める＝日付が変わると前日の節を指す ✅済 で止まる。もう1件＝1回目に貼った行を読み取れず、2回目で通る（今日 4回 起きた・worklog 20260917 §10） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

<!-- ACC_MATERIALS_START hash=c55cc4bff2fb96cb gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`indicator_switch.json`・`signal_families.json`・`search_limits.json`。

**探す指標＝印がオンの 140種**（印を切り替えると、この一覧も設計も変わります）。

```
ADX・DI差・MACD線%・MACDヒスト%・MACDシグナル線%・RSI・ROC・Stoch%K・Stoch%D・MFI・CMF・OBV傾き・転換線・基準線・EMA傾き・ATR%・BB%b・BB幅・realized_vol・Donchian幅・volume_ratio・swing高値距離・swing安値距離・高値からの経過バー・安値からの経過バー・形スコア・W字・fractal高値距離%・fractal安値距離%・高値切り上げ幅%・安値切り上げ幅%・構造破断距離%・close vs EMA・close vs SMA・close vs VWAP・Keltner上・Keltner下・n本高値・n本安値・pivotPP・pivotR1・pivotS1・fib位置・POC・VAH・VAL・MMI・S-Rタッチ数・AO%・CCI・ER・KST・KSTシグナル・PPO・PPOシグナル・PPOヒスト・PVO・PVOシグナル・PVOヒスト・SMC_SWEEP・SQZ_ON・STC・STCstoch・StochRSI%K・StochRSI%D・TRIX・TRIXシグナル・TRIXヒスト・TSI・TSIシグナル・TSIヒスト・UO・close vs ALMA%・close vs DEMA%・close vs FWMA%・close vs HILO%・close vs HMA%・close vs HT_TRENDLINE%・close vs HWMA%・close vs JMA%・close vs KAMA%・KAMA傾き%・close vs LINREG%・close vs LRb%・close vs MAMA%・close vs FAMA%・close vs MCGD%・close vs MIDPOINT%・close vs MIDPRICE%・close vs MMAR%・close vs PWMA%・close vs RAINBOW%・close vs RMA%・close vs SINWMA%・close vs SSF%・close vs SWMA%・close vs T3%・close vs TEMA%・close vs TRIMA%・close vs TSF%・close vs VIDYA%・close vs VWMA%・close vs WMA%・WMA傾き%・close vs ZLMA%・AROONU・AROOND・AROONOSC・CHOP・close vs CKSPl%・close vs CKSPs%・DPO%・close vs PMAX%・close vs PSAR%・PSAR加速・PSAR反転・close vs SAREXT%・VHF・VTXP・VTXM・EFI比・EOM比・NVI傾き・PVT傾き・MAD比・stdev%・close vs MEDIAN%・close vs ABER_ZG%・ABER位置・close vs ACCBL%・close vs ACCBU%・close vs CE_L%・close vs CE_S%・HWC位置・HWC幅%・MASSI・THERMO%・TR%・UI・HT_DCPHASE
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

<!-- ACC_RANKING_START hash=aa91c5a6fb1e7086 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`material_ranking.json`。

**成績表に載っている列の本数**（札＝強さ・先読み24・執行足より上の時間足だけ）

| 役割 | 上位足の列の本数 | 分離力の高い順に3本 |
|---|---|---|
| env | 1918 | MMI500__1d（0.639）／PWMA20傾き%__1d（0.595）／kurtosis50__1d（0.405） |
| location | 1270 | close vs TSF%20__1d（0.429）／close vs TEMA%20__1d（0.434）／close vs LINREG%20__1d（0.435） |
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
| 1 | pdca_flow.md の §1 の表のほかの節（§0 の読み方・§1.5・§2 の段階別フロー・§3〜§6・改訂ルール）を元データにすること | 決まりと経緯を説明する文で、実物から作れる値を持たない。今回の不整合（本数・載っていない hook）は §1 の表に在る。★含めるかは まこさんが決める（決めてほしいこと2） | 2-1 の表・まこさん 2026-09-17「手書きせざるをえないもの以外は自動生成」 |
| 2 | worklog・lessons・memory を元データから作ること | 起きたことを書き足す記録そのもので、書き足す文が中身。★表や件数の部分をプログラムで作るかは、使うときに188番のとおり決める | next_step §6 の188番 |
| 3 | 壊すプログラムと新しい自己テストを付けること | 文書を作る道具と、生成された部分を止める hook で、BOT の中身に触らない。走らせて1回 確かめた出力を貼る | 恒久71番 |
| 4 | 元データの文の中身（何が問題か・次に何をするか）が正しいかを、プログラムで判定すること | 文の中身は照らす実物が無い。照らせるのは、worklog の節の参照・日付・件数・状態の形だけ | 恒久64番 |
| 5 | 今日見つけた ToDo ゲートの不具合2件を、この工事で直すこと | この工事は文書を作る仕組みの工事。不具合は §6 に行として積み、直す工事は別にする（1変更・H16） | cat_requirements §4.6 の H16 |

### 3-2 決めてほしいこと

| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | next_step.md の全部の節（0-1・0-2 だけでなく、先頭の注記・0-3・(0-d)・§0-4・§5・§6・§7）を元データにするか | 全部にする。まこさんの指示「手書きせざるをえないもの以外は自動生成」のとおりで、手で書く節を残すと、その節で同じ失敗が起きるため | まこさん 2026-09-17 |
| 2 | pdca_flow.md は §1 の hook の一覧だけにするか、ほかの節も元データにするか | §1 の表だけ。ほかの節は決まりの説明の文で、実物から作れる値を持たないため（3-1 のやらないこと1） | 2-1 の表 |
| 3 | 生成された部分の Write・Edit を止める hook を新しく足すか、Stop hook の --verify だけにするか | 足す。Stop hook だけだと、手で直した文がまこさんの画面に出た後に止まるため。書く瞬間に止める方が、直す手間が少ない | chat_writing_rules.md の Stop hook の限界と同じ理由 |

## 4｜設計の中身

**★この節の項目は、正本 `design_section_sources.json` の3つの出どころ（うちの正本・外の標準・まこさんが過去に指摘したこと）118件を、1件も余さず引き受ける形に決めたものです。**割り当て＝`design_section_map.json`。検算＝`gen_design_sections.py --check`。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

**この項目に書くこと**＝何を作るのか／どういう流れで動くのか／何ができるようになるのか／完成したとき何が出るのか。★項目に分けない。ここだけ読めば全体が分かる状態にする。★★必ず「なぜこの形にするのか」を、ほかの形と比べた実測の数字で書く（この形を取らなかったら何通り・何時間 掛かるか）。★なぜ必須か＝まこさん指摘 2026-09-10「2-2の設計思想は、総当りで組合わせロジックを出すと数百年かかるので、段ごとに絞り込んでいくという方法ということを、このセッション内で何度も言ってるのに、毎回抜けるから、いい加減にしてほしい」。私は「段＝枠を埋める順番」と読み、「段＝候補を絞る段階」という思想を毎回 落とした。

**この仕組みは、next_step.md と pdca_flow.md の hook の一覧を、私が手で書かずにプログラムに作らせるものです。**

**いま何が起きているか。**next_step.md は、(0-b-2) の1節を除いて全部 手で書いています。§6 の表は93行あり、今日も「不具合2件を手で1行ずつ足す」案を私が出しました。手で書くと、worklog の節の番号を実在しないものにしたり、同じ事実を2か所に書いて片方だけ直したりします（恒久72番の実例）。pdca_flow.md の hook の一覧も手で書いていて、見出しの本数が登録と合わず、今日足した2本が載っていません。

**どう変えるか。**next_step.md は、元データ next_step_src.json から tidy_next_step.py が作ります。元データは、いまの next_step.md を1文字も変えずに読み込んだものから始めます（読み込んで作り直した文書が、いまのファイルと1文字も違わないことを確かめてから元データを書きます）。そのあと私が直すのは元データだけです。作るときにプログラムが照らすもの＝①文の中の `session_worklog_YYYYMMDD.md` の §番号が、そのファイルに見出しとして在るか ②0-2 の ★いまここ がちょうど1件か ③0-1 の「書いた日」が、いちばん新しい worklog の日付と同じか ④0-2 と §6 で状態が「済」の印の行を、archive へ1文字も変えずに移す ⑤(0-b-2) は json の印の値から書く。pdca_flow.md の hook の一覧は、gen_hook_list.py が settings.json の登録（名前・タイミング・matcher）と hook_roles.json（役割の文）から作ります。

**手の書き替えをどう止めるか。**2つの文書の生成された部分は、目印とハッシュ値で囲みます。hook forbid_edit_generated_docs が、囲みの中を Write・Edit で直そうとした瞬間に止め、元データと作り直しのコマンドを出します。Bash で書き替えた場合は、Stop hook enforce_next_step_tidy.sh が2つの道具の --verify を呼び、ハッシュ値が合わなければターンを終われなくします。

**完成したときに出るもの。**私が next_step.md や hook の一覧を手で直そうとすると、その瞬間か、ターンの終わりに止まります。元データに実在しない worklog の節を書くと、作るときに止まります。settings.json に hook を足して役割を書かないと、一覧を作るときに止まります。売買のロジックにも審判にも触りません。net はゼロのままです。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

**この項目に書くこと**＝このプログラムを呼ぶ相手（人か、別のプログラムか）と、出た結果を次に使う相手。やること／やらないことの線。

**誰が動かすか。**①私が元データ（next_step_src.json・hook_roles.json）を直し、`tidy_next_step.py --write` と `gen_hook_list.py --write` を走らせます。②hook forbid_edit_generated_docs は、私の Write・Edit のたびに Claude Code が走らせます。③Stop hook enforce_next_step_tidy.sh は、ターンの終わりごとに Claude Code が走らせます。

**誰が結果を使うか。**まこさんが next_step.md と pdca_flow.md を読みます。次のセッションの私が、SessionStart で next_step.md を読みます。

**やること／やらないことの線。**next_step.md の全部の節と、pdca_flow.md の §1 の hook の一覧を作ります。pdca_flow.md のほかの節（§0・§1.5・§2〜§6・改訂ルール）と、worklog・lessons・memory は作りません（3-1 のやらないこと）。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

**この項目に書くこと**＝関数やコマンドの取り決め（引数・戻り値・その意味・呼んでよい相手）。

**受け取るもの。**

| 何 | 置き場 | 形 |
|---|---|---|
| next_step の元データ | `.claude/state/next_step_src.json`（新設） | 節の並び。1節＝見出しの行と、本文の行の一覧。表の節は、表の前の行・行の一覧（1行＝欄の一覧と状態）・表の後の行に分ける |
| 印の値 | `.claude/state/h2_pass.json`・`g2_pass.json` | いまと同じ（(0-b-2) に書く） |
| worklog | `.claude/state/session_worklog_*.md` | 見出しの §番号を読むだけ |
| hook の登録 | `.claude/settings.json` | タイミングごとの matcher と command |
| hook の役割の文 | `.claude/state/hook_roles.json`（新設） | 1件＝一覧の1行（名前の欄の文字と、役割の欄の文字） |

**出すもの。**

| 何 | 置き場 | 形 |
|---|---|---|
| next_step.md | いまの置き場 | 目印 `<!-- NEXT_STEP_GENERATED hash=… tidy_next_step.py が作った＝手で書き換えない -->` を1行目に持つ、全文の生成 |
| hook の一覧 | `pdca_flow.md` の §1 | 目印の囲み `<!-- HOOK_LIST_START hash=… -->`〜`<!-- HOOK_LIST_END -->` の中だけ |
| 移した行と節 | `.claude/state/next_step_archive_202608.md` | いまと同じ（書き足す） |

**旗。**`tidy_next_step.py` に `--import`（いまの next_step.md から元データを作る・作り直した文書が1文字も違わないときだけ書く）を足します。`--write`・`--verify` は、元データからの生成と全文のハッシュ値の照合を含む形に広げます。`gen_hook_list.py` は `--import`・`--write`・`--verify` を持ちます。

### 4-6 制約（従う決まりの全件と、その出どころ）

**この項目に書くこと**＝決まりを1件も落とさずに並べ、どれをどの工程で使うかを書く。動かせないもの（承認済みの設定・取引所の仕様）も。

| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 手で書かざるを得ない部分以外は自動生成 | 恒久69番・まこさん 2026-09-17 | 文書の全体を元データから作る。私が書けるのは元データの文だけ |
| 実物を開いて確かめていない直しは書かない／同じ事実を揃える | 恒久72番 | worklog の節の参照を作るときに照らす。印の値は json から書く |
| 消してはいけない印（🔴・★消さない・毎回消さない）の数を移す前後で照らす | tidy_next_step.py の決まり | いまの照らし方（check_marks）をそのまま使う |
| 終わった行は ✅済 の4文字だけ／表に残さない | 恒久55番・tidy の (f) | 状態の欄を見て archive へ移す（残りは `grep -c '済' .claude/state/next_step.md` で数える） |
| worklog は日付ごとに1本 | 恒久66番 | 0-1 の書いた日を worklog の日付と照らす |
| 文書を作る道具に過剰なテストを付けない | 恒久71番 | 壊すプログラムと新しい自己テストを付けない。走らせて1回 確かめる（完成の条件の壊すプログラムの欄は「—」） |
| hook の直しに承認を入れない | まこさん 2026-09-06 | 新しい hook と Stop hook の直しは承認の外。道具（.claude/tools）の直しは承認の相手 |
| 合言葉で hook を外せないようにする | 恒久57番 | 新しい hook に合言葉を作らない |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

**この項目に書くこと**＝主要な部品を挙げ、それぞれが何に責任を持つかを書く。部品どうしの協調も。

| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| `tidy_next_step.py` | next_step.md の読み込み（最初の1回）・元データからの生成・照らす5つ・全文のハッシュ値の照合・いまの6つの検査 | 直す |
| `next_step_src.json` | next_step.md の文の置き場 | 新設（プログラムが作る） |
| `gen_hook_list.py` | hook の一覧の読み込み（最初の1回）・settings.json との照合・一覧の生成・囲みのハッシュ値の照合 | 新設 |
| `hook_roles.json` | hook の一覧の役割の文の置き場 | 新設（プログラムが作る） |
| hook `forbid_edit_generated_docs`（.sh と .py） | 生成された部分への Write・Edit を止める | 新設 |
| `enforce_next_step_tidy.sh` | ターンの終わりに2つの道具の --verify を呼ぶ | 直す（1行足す） |
| `settings.json` | 新しい hook を PreToolUse に登録する | 直す |

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

**この項目に書くこと**＝工程の順番と、工程の間で何を渡すか。組み方の根拠（何の法則で決めるか）も。

**最初の1回（読み込み）。**

1. 私が `tidy_next_step.py --import` を走らせます。プログラムが next_step.md を節と表の行に分けて元データの形にし、その元データから文書を作り直して、いまのファイルと1文字ずつ比べます。1文字でも違えば、元データを書かずに止まり、違う最初の行を出します。
2. 同じなら、`next_step_src.json` を書きます。
3. 私が `gen_hook_list.py --import` を走らせます。同じ手順で、pdca_flow.md の §1 の表から `hook_roles.json` を作ります。
4. 私が2つの `--write` を走らせ、目印とハッシュ値の入った文書にします（中身の文字は変わらず、目印の行が増えるだけ）。

**そのあとの直し（うまくいったとき）。**

1. 私が元データを直します（例＝§6 に今日の不具合2件の行を足す）。
2. 私が `tidy_next_step.py --write` を走らせます。プログラムが照らす5つ（4-0）を確かめ、「済」の印の行を archive へ移し、(0-b-2) を印の値から書き、全文を作って目印のハッシュ値を付けます。
3. Stop hook が `--verify` を呼び、ハッシュ値と6つの検査が通ればターンを終われます。

**hook を足したとき。**settings.json に登録し、hook_roles.json に役割の文を足して、`gen_hook_list.py --write` を走らせます。見出しの本数は、プログラムが settings.json から数えて書きます。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

**この項目に書くこと**＝実際の1件が、入口から出口までどう通るか。★読み手が設計を確かめられる唯一の欄。

**通しの例（今日の不具合2件を §6 に積む）。**

1. **直す前。**私は §6 の表に手で2行 足す案を出した（まこさんの指示で取り下げた）。
2. **この工事の後。**私は next_step_src.json の §6 の節の「行」に2件を足す。1件目の欄＝番号・いつ直すか・何が問題か（ToDo ゲートが日付をまたぐと前日の節を指す「済」の行で止まる）・いま何が起きているか・見つけた日（2026-09-17）・出典（`session_worklog_20260917.md` の §10）。
3. **`tidy_next_step.py --write` を走らせる。**プログラムが出典の §10 が worklog 20260917 に見出しとして在るかを照らす。在るので、§6 の表を作り、全文を書き、目印のハッシュ値を付ける。
4. **私が出典を §99 と打ち間違えた場合。**プログラムが「§99 が session_worklog_20260917.md の見出しに無い」で止まり、文書を書かない。
5. **私が next_step.md の §6 を Edit で直そうとした場合。**hook forbid_edit_generated_docs が止め、「元データ next_step_src.json を直して `tidy_next_step.py --write`」と出す。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

**この項目に書くこと**＝工程ごとに、使う材料（指標）・時間足・閾値の格子・パラメータの範囲・候補の本数。

**非該当。**この工事は値を探しません（文書を作る道具と hook の工事）。出どころ＝恒久70番の §4 の項目の説明

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

**この項目に書くこと**＝指定できる項目・その置き場・既定値・指定しなかったときの動き。

| 道具 | 旗 | 既定の動き |
|---|---|---|
| `tidy_next_step.py` | `--import`（足す）・`--write`・`--verify`・`--selftest`・`--file`・`--archive`・`--limit`（いまの旗） | `--import` は next_step_src.json が既に在れば止まる（上書きしない） |
| `gen_hook_list.py` | `--import`・`--write`・`--verify` | `--import` は hook_roles.json が既に在れば止まる |

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

**この項目に書くこと**＝できあがったときに出てくるものの形。★4-17（走っている途中の表示）とは別。数字は機械の出力から出す（私が書かない）。

**完成したときに画面に出るもの。**`tidy_next_step.py --verify` が「✅ [tidy --verify] 7つとも通った」（いまの6つ＋全文のハッシュ値）を出し（`python3 .claude/tools/tidy_next_step.py --verify`）、`python3 .claude/tools/gen_hook_list.py --verify` が登録の本数と一覧の行数を出して ✅ を出します。next_step.md の1行目に生成の目印が在り、pdca_flow.md の §1 の見出しの本数が settings.json の登録の本数と同じになり、今日足した hook 2本（と、この工事で足す1本）の行が在ります。§6 に今日の不具合2件の行が在ります。★数は走らせた出力から書きます。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

**この項目に書くこと**＝入力の検証／起こりうる誤りの状態／中途半端な出力が残ったとき／やり直せるか。★正常の道だけを書かない。

| 起きたこと | どうなるか |
|---|---|
| 読み込みで作り直した文書が、いまのファイルと1文字でも違う | 元データを書かずに止まる。違う最初の行の番号と、両方の文字を出す |
| 元データの文に、実在しない worklog の §番号が在る | 書かずに止まる。節の見出しと参照を出す |
| 0-2 の ★いまここ が1件でない／0-1 の書いた日が worklog の日付と違う | 書かずに止まる |
| 印の json が無い・読めない | いまと同じく止まる |
| settings.json に登録が在るのに、hook_roles.json に役割が無い | 一覧を書かずに止まる。その hook の名前を出す |
| hook_roles.json に在るのに、登録が無い | 止めずに、その行の名前の欄に「（登録なし）」を足して出す（廃止した hook の行を消さないため） |
| 生成された部分を Write・Edit しようとした | hook が止め、元データの置き場と `--write` のコマンドを出す |
| Bash で生成された部分を書き替えた | Stop hook の `--verify` がハッシュ値の食い違いで止める |
| hook 自身が例外で落ちた | 止めない（いまの hook と同じく、本体が無い・読めないときは通す）。★ハッシュ値の照合は Stop hook に残るので、手の書き替えはそこで止まる |
| 書いている途中で落ちた | 一時のファイルに書いてから置き替える（`os.replace`）ので、半分だけ書かれた文書は残らない |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

**この項目に書くこと**＝途中で作る表の列の意味・鍵の意味・既にあるデータの形をどう変えるか。

**next_step_src.json の形。**`{"節": [ {"見出し": "### 0-1 …", "本文": ["行", …]} , {"見出し": …, "表": {"前": [行…], "見出しの行": "| … |", "区切り": "|---|…|", "行": [{"欄": [文字…], "状態の欄": n}], "後": [行…]}} ]}`。見出しの無い先頭の行（1行目から §0 の前まで）は、見出しを空にした節で持ちます。

**書いた日の欄。**0-1 の節に `"書いた日": "YYYY-MM-DD"` を持たせます。見出しの日付はこの欄から作り、いちばん新しい worklog の日付と照らします。

**hook_roles.json の形。**`{"行": [{"名前の欄": "…", "タイミングの欄": "…", "matcher の欄": "…", "役割の欄": "…"}]}`。名前の欄の中の hook の名前（`/` で区切られた複数も）を、settings.json の登録の名前と照らします。

**既に在るデータの形は変えません。**`h2_pass.json`・`g2_pass.json`・archive の文書はいまのままです。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

**この項目に書くこと**＝置き場・上書きか追記か・作り直せるか・古いものをどうするか。

**上書きか書き足すか。**next_step.md と hook の一覧の囲みは、作るたびに上書きします（元データから作り直せるため）。archive は書き足すだけです。元データは私が直します。

**古いものをどうするか。**読み込みの前の next_step.md は git に在ります（いまの commit）。作り直しで中身の文字は変わらないことを、読み込みのときに1文字ずつ確かめます。

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

**この項目に書くこと**＝タイムゾーン／境目の時刻を含むか含まないか／足の締まる時刻の定義。★静かに結果を変えるので、非該当にしない。

**日付だけを扱います。**0-1 の書いた日と、worklog のファイル名の日付（YYYYMMDD）を、文字として比べます。時刻とタイムゾーンは使いません。archive に移すときの見出しの日付は、いまと同じく `date.today()` です。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

**この項目に書くこと**＝時間と容量。★設計の形を決める材料でもあるので、§6-3 の見積もりとは別に書く。

**測っていません。**以下は見込みで、実装のあと測って worklog に残します。

| 何 | 見込み | 根拠 |
|---|---|---|
| `tidy_next_step.py --write`・`--verify` | 1秒以内 | いまの next_step.md は319行・archive は2,321行（wc -l）。文字の読み書きだけ |
| `gen_hook_list.py --verify` | 1秒以内 | settings.json と pdca_flow.md（200行）を読むだけ |
| hook forbid_edit_generated_docs の1回 | 1秒以内 | Edit の対象のファイル名と囲みの位置を比べるだけ |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

**この項目に書くこと**＝同じファイル・同じ記録を2つの走行が触らないか。

**同時に2つのセッションが next_step.md を作ったとき。**どちらも同じ元データから作るので、後に走った方が残ります。元データを2つのセッションが同時に直すと、後に保存した方の直しだけが残ります（いまの手書きと同じ）。★書くときは一時のファイルから置き替えるので、壊れた文書は残りません。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

**この項目に書くこと**＝取引所の鍵／本番で実際に発注するかの切り替え／検査済みの記録。

**書き換えられては困る記録。**`h2_pass.json`・`g2_pass.json` は読むだけです。この工事の文書に、取引所の鍵や本番の切り替え（ALLOW_LIVE_ORDERS）は出てきません。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

**この項目に書くこと**＝途中経過が見えるか（恒久60番が求める）。後から何が起きたかを追えるか。

**画面に出すもの。**`--import` は、読み込んだ節の数と表の行の数と、作り直しの比べの結果（1文字も違わない／違う最初の行）を出します。`--write` は、移した行の数・照らした参照の数・書いたファイルを出します。hook は止めたときだけ、止めた理由と直す道を出します。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

**この項目に書くこと**＝いま在るもののうち、何がこの部分に依存しているか。★hook 64本と承認・ハッシュ値が絡むので、この repo では特に重い。

1. **next_step.md を手で直していた作業の全部。**以後は元データを直して `--write` を走らせます。SessionStart の表示（show_latest_state.sh）は文書を読むだけなので変わりません。
2. **tidy_next_step.py のいまの `--write`（消す印の節と終わった行を移す）。**元データの側で移す形に置き替わります。いまの `--selftest`（19件）は、読み込みの前の形の見本で走るので、見本を元データの形に合わせる直しが要るかを実装で確かめます。
3. **Stop hook enforce_next_step_tidy.sh。**呼ぶ道具が1本 増え、ターンの終わりが少し遅くなります（4-14）。
4. **pdca_flow.md。**§1 の表だけが囲みの中になります。ほかの節は手で書いたままです。★この文書は毎セッション自動で読み込まれるので、目印の行が読み込まれる文字に増えます。
5. **仕組み2の hook（require_selftest_after_source_edit）。**新しい元データ2本（.json）を書き替えると、それを読む道具で自己テストを持つもの（tidy_next_step.py）の自己テストを求めます＝直すたびに `--selftest` を走らせることになります。
6. **enforce_checked_edit。**元データの文に「ファイル名:行番号」を書くと、いまと同じく開いたかを照らします。
7. **売買のロジック・審判・材料・法則。**触りません。
8. **tidy_next_step.py の行を文字で探している壊すプログラム3本。**`b54_table_tidy_gone.sh`（move_done_rows の移す行の見分け方）・`b59_tidy_head_dup_live.sh`（控えの見出しの取り方）・`b67_marks_time_check.sh`（印の時刻を照らす2行）。承認のプログラムが設計書を試したとき、仕組み1の hook（show_breaks_on_code_edit）が名指しした。**この工事では、この3本が探す行を変えません**（生成は、いまの関数の上に足す）。実装で変えることになったら、同じ直しで3本の探す文字を合わせ、TARGET に足して承認を取り直す（L-605）。

### 4-18 再利用（手本にした、既にあるものの形）

**この項目に書くこと**＝同じ形が既にどこかに在るか。手本にしたファイル（`MODEL:` の行と同じ相手）。

| 手本 | 何を写すか |
|---|---|
| `gen_session_todo.py` | 元データから文書を作り、作ったままかを `--verify` で見る形。書く先を道具の側で限る形（out_path） |
| `gen_regime_kb.py` | 囲みの目印とハッシュ値の形 |
| `enforce_checked_edit.sh` | hook の .sh から本体の .py を呼ぶ形 |
| `tidy_next_step.py` のいまの `move_to_archive`・`move_done_rows`・`check_marks` | archive へ1文字も変えずに移す形と、印の数の照らし方 |

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
| 4-7 | 条件 | 探索の範囲（決める値と、その探し方＝範囲・並び・本数） | 非該当（この工事は値を探しません（文書を作る道具と hook の工事）。出どころ＝恒久70番の §4 の項目の説明） |
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


## 5｜決めたことと理由・捨てた案

| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 元データは、いまの next_step.md をプログラムが読み込んで作る。私は元データを手で作らない | 93行の §6 を私が json に書き写すと、写し間違いが入る。読み込んで作り直し、1文字も違わないことを確かめれば、写し間違いが入らない | 私が元データを書き、作った文書を目で比べる。捨てた理由＝恒久72番 |
| 2 | 新しい道具を作らず、next_step は tidy_next_step.py を広げる | next_step の検査と archive への移し方と Stop hook が、既にこの道具に在る。道具を分けると、同じ文書を2本の道具が書く | gen_next_step.py を新設する。捨てた理由＝同じ文書を書く道具が2本になる |
| 3 | hook の一覧の名前・タイミング・matcher は settings.json から照らす | 本数が登録と合わず、今日の2本が載っていない（2-1）。登録が正本（pdca_flow.md の冒頭の逐語「実体が正・差異が出たら実体に合わせて更新」） | 一覧を全部 hook_roles.json に手で持つ。捨てた理由＝登録とずれる |
| 4 | 壊すプログラムを付けず、完成の条件の壊すプログラムの欄は「—」にする | 恒久71番。承認のプログラムは「—」の行を済にしない＝完成は まこさんが出力を見て決める | 壊すプログラムを付ける。捨てた理由＝恒久71番 |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

<!-- ACC_SELFTEST_START hash=72b3b9e0e85dba0d gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝元データの「完成の条件」。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `—` | #1・#2・#3・#4・#5 | 壊すプログラムは付けない（恒久71番） |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

| # | リスク | どうするか |
|---|---|---|
| 1 | 読み込みで作り直した文書が、いまのファイルと1文字 違う（表の中の縦棒のエスケープ4行・末尾の空行・全角の空白） | 違えば元データを書かずに止まるので、壊れた元データは残らない。違う行を見て、読み込みの処理を直す |
| 2 | tidy_next_step.py のいまの自己テスト19件が、元データの形に変わると落ちる | 実装で走らせて確かめる。落ちたら見本の形を元データに合わせる（判定は緩めない） |
| 3 | 元データの文に書いた worklog の節の参照で、過去の worklog の古い番号が多く見つからず止まる | 照らすのは読み込みの後に足した文だけにするか、全部にするかを、読み込みの結果（見つからない参照の件数）を見て まこさんに出す |
| 4 | pdca_flow.md の §1 の表は1行が長く、名前の欄に複数の hook と取り消し線が入っている | 名前の欄から hook の名前を取り出す規則（`/` で区切る・取り消し線の中は廃止として数える）を実装で確かめ、取り出せない行は名前を出して止まる |

### 6-3 見積もり

| 何 | 見込み | 根拠 |
|---|---|---|
| tidy_next_step.py の読み込み・生成・照らす5つ・全文のハッシュ値 | 3時間 | いまの道具（538行）の上に足す。★実測ではない |
| gen_hook_list.py と hook_roles.json の読み込み | 2時間 | 同上 |
| hook forbid_edit_generated_docs と settings.json・Stop hook の直し | 1時間 | enforce_checked_edit の形を写す。★実測ではない |
| §6 に今日の不具合2件を足し、hook の一覧に今日の hook 3本の役割を足して作り直す | 30分 | 元データに行を足して --write を走らせるだけ |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

**① 真因（root cause）**＝next_step.md と hook の一覧に、元データも生成の道具も無く、私が文書そのものを手で直す道しかないことです。手で直すと、worklog の節の参照を確かめず、同じ事実の片方だけを直し、登録と一覧がずれても誰も止めません（2-1 の表の本数のずれ・載っていない2本）。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。動くのは、私が next_step.md と hook の一覧を手で書き替える道（開いている → 書く瞬間とターンの終わりに止まる）と、実在しない worklog の節を参照する道（開いている → 作るときに止まる）です。

**③ root か symptom か**＝root です。symptom の直し方は、①§6 に今日の2行を手で足す ②pdca_flow.md の見出しの本数を手で直す、で、どちらも手で書く道を残します。この設計は、文書を直す場所を元データに移し、文書そのものを手で書けなくします。

**④ ベースアップ**＝この工事で私は外の検索をしていません。実物は、読むものの宣言（design_read_plan.md・まこさんの OK 2026-09-17「OK」2回）の12件を Read tool で開きました。数は 2-1 の表のコマンドで数えました。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

この工事に、疑似シミュから取った値は1つもありません。数は全部、2-1 の表のコマンドで数えた実物の数です。見積もりの時間は実測ではないと書きました。

### 7-3 変更の単位（H16）

変更の単位は「next_step.md と pdca_flow.md の hook の一覧を、手で書かずに元データから作る」の1つです（まこさんの指示「手書きせざるをえないもの以外は自動生成にしてほしい」）。部品は4つ（4-3 の表）です。H1〜H16 と審判整合（群2）は非該当です（売買のロジックにも審判にも触れないため）。過去に取りやめた失敗の再演か＝近い型があります。2026-09-14 に、同じ目的を含むもっと大きな工事（指示の台帳・9つの検査・実例79件の起こし直し）の設計書を書き、取り下げました（worklog 20260914 §67）。今回は、まこさんの今日の指示の相手（今日 手で書こうとした §6 と hook の一覧）に絞り、指示の台帳や検査の仕組みは入れません。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | この工事は乱数を1つも使いません。文書は元データの並びのとおりに作ります。 |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | この工事は探す値を持ちません（文書を作る道具と hook の工事）。 |

### 7-4 塞げないもの

| 問い | 塞げないこと |
|---|---|
| **元データの文の中身は正しいか** | 判定しません。照らすのは、worklog の節の参照・日付・★いまここ の件数・状態の形だけです |
| **元データを手で直した誤り** | 文書は元データのとおりに作られるので、元データの誤りはそのまま文書に出ます |
| **hook と道具そのものを書き換えられたら** | 書き換えれば無効にできます。道具は承認ゲートの相手で、差分は git に出ます |
| **worklog 以外の参照（ファイル名と行番号・設計書の節）** | この工事では照らしません（enforce_checked_edit が Write・Edit の瞬間に行番号だけ照らします） |
| **pdca_flow.md の §1 以外の節の手書き** | 止めません（まこさん決定 2026-09-17＝§1 の表だけ） |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認済みで凍結されているため） |

### 7-5 §4.6 ハード制約の照合

<!-- ACC_CHECKLIST_START hash=cb5f35c3aee2bdd1 gen_acceptance.py が自動生成＝手で書き換えない -->
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
| 1 | 読み込み。`tidy_next_step.py --import` が next_step_src.json を書き、それから作り直した文書が、読み込む前の next_step.md と1文字も違わない（違えば書かずに rc=1） | `python3 ../../.claude/tools/tidy_next_step.py --import` | 実経路 | 壊すプログラムは付けない（恒久71番） | `—` | — | **未着手** |
| 2 | 照らす。`tidy_next_step.py --verify` が、いまの6つの検査と全文のハッシュ値で「通った」を出す | `python3 ../../.claude/tools/tidy_next_step.py --verify` | 実経路 | 壊すプログラムは付けない（恒久71番） | `—` | — | **未着手** |
| 3 | hook の一覧。`gen_hook_list.py --verify` が、settings.json の登録の本数と一覧の見出しの本数が同じで、登録の全部に行が在ることを出す | `python3 ../../.claude/tools/gen_hook_list.py --verify` | 実経路 | 壊すプログラムは付けない（恒久71番） | `—` | — | **未着手** |
| 4 | 書く瞬間に止まる。hook forbid_edit_generated_docs が、next_step.md の生成された部分への Edit の入力で rc=2 を返し、生成されていない文書への Edit で rc=0 を返す（`--try` で1回ずつ） | `python3 ../../.claude/hooks/forbid_edit_generated_docs.py --try <入力の json>` | 実経路 | 壊すプログラムは付けない（恒久71番） | `—` | — | **未着手** |
| 5 | いまの自己テストが通る。`tidy_next_step.py --selftest` が全部 pass | `python3 ../../.claude/tools/tidy_next_step.py --selftest` | 実経路 | 壊すプログラムは付けない（恒久71番） | `—` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

<!-- ACC_CODEREF_START hash=062b68da7dbf10ee gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`../../.claude/tools/tidy_next_step.py`

| 触る関数 | 定義の行 |
|---|---|
| `verify` | 277 |
| `do_verify` | 610 |
| `do_write` | 626 |
| `move_to_archive` | 120 |
| `move_done_rows` | 151 |
| `check_marks` | 215 |
| `refresh_marks` | 242 |
| `import_src` | 523 |
| `render` | 399 |
| `check_refs` | 451 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 32件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

<!-- ACC_SPEC_START hash=1e097d0a4eb5c409 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "../../.claude/tools/tidy_next_step.py",
  "impl_functions": {
    ".claude/tools/tidy_next_step.py": [
      "_split_cells",
      "_state_col",
      "parse_doc",
      "render",
      "strip_gen_head",
      "_hash16",
      "gen_head",
      "_worklog_secs",
      "check_refs",
      "move_done_rows_s6",
      "_atomic_write",
      "_first_diff",
      "import_src",
      "check_generated",
      "do_write_src",
      "do_verify",
      "do_write",
      "main"
    ],
    ".claude/tools/gen_hook_list.py": [
      "registered",
      "_cells",
      "find_region",
      "parse_region",
      "names_in",
      "render_region",
      "_hash16",
      "_atomic_write",
      "missing_roles",
      "do_import",
      "do_write",
      "do_verify",
      "main"
    ],
    ".claude/hooks/forbid_edit_generated_docs.py": [
      "_region",
      "_block",
      "check",
      "main"
    ]
  },
  "_impl_functions の意味": "この工事で触った関数だけ（実装の後に確定させた・2026-09-17）。tidy_next_step.py は足した15個と、呼び出しを足した do_verify・do_write・main。gen_hook_list.py と forbid_edit_generated_docs.py は新しいファイルなので全部の関数。★いま在る move_to_archive・move_done_rows・check_marks・refresh_marks・verify は触っていない（壊すプログラム b54・b59・b67 が探す行を変えないため）。",
  "self_check_calls": [
    "verify",
    "do_verify",
    "do_write",
    "move_to_archive",
    "move_done_rows",
    "check_marks",
    "refresh_marks",
    "import_src",
    "render",
    "check_refs"
  ],
  "_self_check_calls の意味": "7-7 の表に出す tidy_next_step.py の関数の名前。verify・do_verify・do_write・move_to_archive・move_done_rows・check_marks・refresh_marks は前から在る。import_src・render・check_refs はこの工事で足した。",
  "must_use": {
    "do_verify": [
      "check_generated"
    ],
    "do_write": [
      "do_write_src"
    ],
    "main": [
      "import_src"
    ],
    "import_src": [
      "parse_doc",
      "render",
      "check_refs",
      "strip_gen_head"
    ],
    "check_generated": [
      "strip_gen_head",
      "render"
    ],
    "do_write_src": [
      "render",
      "move_to_archive",
      "move_done_rows",
      "move_done_rows_s6",
      "refresh_marks",
      "check_refs",
      "verify",
      "parse_doc",
      "gen_head"
    ]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "組む側が外から読む一覧（法則・成績表・範囲の鍵）には触らない工事のため。",
  "generated_from": {
    "impl_functions": "実装の後に、足した関数・呼び出しを足した関数を書いた（新しいファイルは全部の関数）",
    "must_use": "実装の後に、足した関数が中で呼ぶ名前を書いた",
    "spec_lists": "空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "../../.claude/tools/tidy_next_step.py",
 "public_functions": {
  "count_marks": [],
  "find_disposable_sections": [],
  "move_to_archive": [
   "check_marks",
   "count_marks",
   "find_disposable_sections"
  ],
  "move_done_rows": [
   "check_marks",
   "count_marks"
  ],
  "check_marks": [],
  "marks_block": [],
  "refresh_marks": [
   "count_marks",
   "marks_block"
  ],
  "latest_worklog_date": [],
  "sec0_lines": [],
  "verify": [
   "find_disposable_sections",
   "sec0_lines"
  ],
  "parse_doc": [],
  "render": [],
  "strip_gen_head": [],
  "gen_head": [],
  "check_refs": [],
  "move_done_rows_s6": [
   "check_marks",
   "count_marks"
  ],
  "import_src": [
   "check_refs",
   "parse_doc",
   "render",
   "strip_gen_head"
  ],
  "check_generated": [
   "render",
   "strip_gen_head"
  ],
  "do_write_src": [
   "check_refs",
   "do_verify",
   "gen_head",
   "latest_worklog_date",
   "move_done_rows",
   "move_done_rows_s6",
   "move_to_archive",
   "parse_doc",
   "refresh_marks",
   "render",
   "verify"
  ],
  "do_verify": [
   "check_generated",
   "latest_worklog_date",
   "sec0_lines",
   "verify"
  ],
  "do_write": [
   "count_marks",
   "do_verify",
   "do_write_src",
   "move_done_rows",
   "move_to_archive",
   "refresh_marks"
  ],
  "selftest": [
   "check_marks",
   "count_marks",
   "latest_worklog_date",
   "move_done_rows",
   "move_to_archive",
   "refresh_marks",
   "sec0_lines",
   "verify"
  ],
  "main": [
   "do_verify",
   "do_write",
   "import_src",
   "selftest"
  ]
 },
 "constants": {
  "LIMIT": 100,
  "DISPOSE": "次の書き替えで消す",
  "SEC0_START": "# §0 ",
  "SEC0_END": "## §0-4",
  "H01": "### 0-1 ",
  "H02": "### 0-2 ",
  "HB2": "### （0-b-2）",
  "HD": "### （0-d）",
  "HERE_MARK": "★いまここ",
  "DONE_MARK": "✅済",
  "SRC_NAME": "next_step_src.json",
  "GEN_HEAD": "<!-- NEXT_STEP_GENERATED hash=",
  "SEC6_HEAD": "# §6 ",
  "S6_FLAG": "§6の済の行を移す",
  "BASELINE_KEY": "読み込んだときに見つからなかった参照",
  "SAMPLE": "# 次のセッションの起点\n\n# §0 次にやること\n\n### 0-1 いまの状態（{d}・◯回目の末）\n\n> 🔴 次のセッションはここから。\n\n#### （0-1' 前回の記録・次の書き替えで消す）\n\n- 🔴 古い記録1\n\n#### （0-1'' 前々回の記録・次の書き替えで消す）\n\n- ★消さない 古い記録2\n- 毎回消さない 古い記録3\n\n### 0-2 🔴 次にやること\n\n| 番号 | やること | 状態 |\n|---|---|---|\n| 1 | あれ | まだ |\n| 2 | これ | ★いまここ |\n\n### （0-b-2）🔴 印の状態（2026-01-01 時点）\n\n- H2 の印＝`0000000000000000…`／G2 の印＝`1111111111111111…`\n\n### （0-d）まだ埋まっていないこと\n\n| # | 何 |\n|---|---|\n\n## §0-4 🔴 まこさんの判断待ち\n\n- 何か\n"
 },
 "cli_flags": []
}
```

<!-- ACC_SPEC_END -->

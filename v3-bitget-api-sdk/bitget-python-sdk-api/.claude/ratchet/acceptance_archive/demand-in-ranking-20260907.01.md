<!-- ARC iter="demand-in-ranking-20260907" -->

# 設計書｜需給3列を、場面を分ける材料の成績表（順位）に足す（2026-09-07・M2-D-4／M2-D-5 の「基準を変える場合の道」）

TARGET: scripts/priority_rebuild/observe_diag.py, scripts/priority_rebuild/engine_tuner_gen.py, .claude/audits/m2d1_ranking_scan.py, .claude/breaks/b38_rank_demand_reader_gone.sh, .claude/breaks/b39_rank_demand_merge_gone.sh, .claude/breaks/b40_rank_demand_touch_indicator.sh

NEW_FILE: .claude/breaks/b38_rank_demand_reader_gone.sh, .claude/breaks/b39_rank_demand_merge_gone.sh, .claude/breaks/b40_rank_demand_touch_indicator.sh

MODEL: .claude/breaks/b36_demand_attach_gone.sh, .claude/breaks/lib.sh

REQUIREMENTS: M2-D（場面を分ける材料の順位を engine_tuner に渡す・正本＝engine_tuner_milestones2.md §3）。まこさんの決定 2026-09-06（逐語「需給に関しては、2-Cでの判断がどうであれ、順位に入れるべきなので、２−D側で修正すればいいのでは？」「その進め方で良い」）と 2026-09-07（差分の口を作る案に「OK」）。

**★足すだけ**＝`observe_diag.py` と `engine_tuner_gen.py` の既存の行は1行も消さず、書き換えもしません（書き換えは「消して足す」なので、機械の照らしで消した行に数えられます）。足すのは、新しい関数と、既存の関数の中に**前置きで挿し込む新しい枝**だけです。具体的には ①既存の関数の引数は増やさない（新しい入口は新しい関数にする）②既存の `if … continue` の行は触らず、その手前に需給用の枝を入れて `continue` で抜ける ③CLI の分岐は、既存の分岐の手前に新しい `if` を置く、の3つの形で書きます。

## 0. 承認の往復について

**往復：2回／内訳＝1回目で書く権利をもらい、2回目で機械が測ります。**

**なぜ1回で終わらないか**＝壊すプログラム3本（b38・b39・b40）は、これから作るファイルです。承認のプログラムは、承認を打ったその場で壊すプログラムを走らせて終了コードを記録します。まだ実在しないファイルは走らせられないので、1回目は「未着手」のまま残ります。b36・b37 と同じ形です。

**★まこさんの決まり（2026-09-05「net に直結しない工事は承認1回で閉じなければ打ち切り」）との関係**＝この2回目は、私の不備で往復が増えるものではなく、壊すプログラムが承認の後にしか作れない仕組みから来るものです（`.claude/breaks/*.sh` は承認ゲートの相手）。1回で終える形は、壊すプログラムを先に置くことですが、それは承認なしに `.claude/breaks/` を書くことになり、できません。**だから「仕組み上の2回目」を例外として認めていただくお願いです。**認められない場合は、完成の条件の表から壊すプログラムの欄を外す形にはできない（hook が「壊すプログラムが無い行は済にできない」と止める）ので、この工事は進められません。

**net に直結するか**＝直接はしません。売買のロジックには1行も触れません。直すのは、材料の順位を作る道具と、それを読む側です。ただし、順位は「どの材料から先に試すか」を決めるものなので、需給が順位に無いと、engine_tuner は需給を場面の判定で試す順番を決められません。この工事はその入口を開けるものです。

## 1. 何を作るか

需給3列（taker_ls・L-S比・CVD）を、場面を分ける材料の成績表 `material_ranking.json` に足します。指標と同じ物差し（分離力＝正解ラベル3本×先読み2本）で採点し、役割は承認済みの型の表で系統「需給」を持つ役割（いまは sufficiency）に入れます。

成績表は全部 作り直しません。需給3列だけを採点して、いまの成績表に足す口（`--rank-regime --add-demand`）を作ります。指標の列は1本も触りません。

生成器が順位を読む側は、いま需給の列を2か所で落とします（印の判定と、列名から種類を引く所）。3か所目の `ranked_groups` は、2か所目が止まった列を飛ばします。落とさずに読めるように直します。順位から需給を引いて束に入れる道は、この工事では作りません（理由は §7）。

**型の表の承認の出どころ**＝`signal_families.json` の中の `approval.fingerprint` は null のままです（note＝「まこさんの承認の指紋が入るまで、この表は無効」）。承認の印は別ファイル `.claude/ratchet/signal_families_approved.txt` に在ります（中身＝`ac94ccafdb6852eed3859d39ef492e7c  approved 2026-09-06`）。生成器の `load_signal_table` は、`gen_signal_families._table_status()` でこの別ファイルの印と表を照らしてから読みます（未承認・指紋不一致なら止まる＝fail-closed）。`engine_tuner_gen.py` の別の関数の説明文（743行）にも「型の表（signal_families_approved.txt）の『役割 → 使える系統』に、条件の材料の系統が合っているかを」とあり、承認の印がこの別ファイルであることは一致しています。この設計書で「承認済みの型の表」と書くのは、この別ファイルの印のことです。**印の照らし方**＝ファイル全体の md5 ではなく「中身だけの指紋」です（`gen_signal_families.py` の `core_of`・`core_hash`＝`approval` の欄と `inventory.limits_copy`（設定ファイルの写し）を除いてから md5 を取る。2026-08-16 まこさん決定「C」）。生成器は `_table_status()` でこの指紋を照らします。**実測（2026-09-07）**＝`python3 scripts/priority_rebuild/gen_signal_families.py --core-hash` → `ac94ccafdb6852eed3859d39ef492e7c`＝承認の印と一致（rc=0）。ファイル全体の `md5` は `6021672605cc7e9ed2ca1dadab1590e9` で印と違いますが、それは上の作りのとおりで、工程表 5 で `load_signal_table` が止まることはありません。

**型の表（`signal_families.json`）は触りません。**型の表の rule「時間足には展開しない」は、入口の条件の材料（別枠 `{"demand": 名前}`）についての決まりで、そのまま守ります。この工事が付ける `__5m` は成績表の列名の中だけの印で、需給を時間足11本に広げるものではありません。つまり「型の表を直す」のではなく「順位の側で、5分足1本の列として採点する」形です。

**決定の時刻順（Web Claude の指摘 赤1 への答え）**＝記録に在る まこさんの逐語は3つです。①「需給に関しては、2-Cでの判断がどうであれ、順位に入れるべきなので、２−D側で修正すればいいのでは？」（2026-09-06 夜・worklog 20260904 §49-13）②「その進め方で良い。M2-Cが完了するまで待機だね」（同）③差分の口を作る案に「OK」（2026-09-07 昼・同 §49-15）。`m2_todo.json` の M2-D の前提3にあった「需給が入るのは入口の条件だけで、場面の判定の束には入らない（まこさん決定 2026-09-07）」は、別セッションが監査 cp25 の §5-6 の直しで書いたもので、その決定の逐語は worklog・decisions・next_step に見つかりませんでした。だから最新の決定は①〜③です。この設計は束に需給を入れないので、「束には入らない」とは矛盾しません。食い違うのは「成績表に0本は設計」の1点で、前提3の文言を①〜③に合わせて直しました。

## 2. なぜ作るか（実測）

**いまの成績表に需給は 0本です。**実測＝2026-09-06 に `python3 .claude/audits/m2d1_ranking_scan.py` を走らせた結果「需給 taker_ls／L-S比／CVD（足した・別枠）: 成績表 0 本」（worklog 20260904 §49-2）。別セッションが同日 20:07 に成績表を全部 作り直した後も 0本のままでした（同 §49-10）。

**0本の原因は、成績表を作る本体が需給を読まないことです。**`observe_diag.py` の `rank_materials_for_regime`（5696〜5791行）は `build_catalog(cfg)` が作る指標の列だけを `build_features` で作って採点します。需給の列を読む `load_demand` の呼び出しは、この関数にも `_insp_regime_rank` にも 0件です（worklog 20260904 §47-2 と §49-14 の1）。

**読む側も需給を落とします。**`engine_tuner_gen.py` の `ranked_materials`（1259行）は列名の種類を `ex.indicator_enabled` で見ますが、需給の名前は参照表 REFS に無いので `iref.find` が None を返し、`indicator_enabled` は False になります（§49-14 の7・8）。`_family_tf_from_col`（2105行）は列名に `__` が無いと止まり、`iref.find` が None なら「順位の列がカタログに無い」で止まります（`ranked_groups` はその列を飛ばします）。

**まこさんの決定**＝需給は順位に入れる。M2-C の判断がどうであれ、M2-D 側で直す（2026-09-06・worklog 20260904 §49-13）。差分の口で足す（2026-09-07「OK」）。

## 3. 深掘り4点

**① 真因**＝成績表を作る本体が「材料＝指標のカタログ」と決め打ちしていることです。需給はカタログの外（別枠）に置かれたため、採点の対象に入りませんでした。読む側も「列名の種類は参照表で引ける」を前提に書かれ、別枠の名前を扱う枝がありません。

**② 期待値分解**＝この工事は売買のロジックに1行も触れません。勝率・平均利益・敗率・平均損失は動きません。動くのは、順位に載る材料の本数（5,981本 → 5,984本の見込み。需給3列とも分離力を測れた場合）と、生成器が順位から読める需給の本数（0本 → 3本）です。

**③ root か symptom か**＝root です。「今回だけ需給を手で足す」のではなく、需給を採点して成績表に足す口と、読む側の枝を作ります。以後、別枠の材料を成績表に足すときは同じ口を使えます。

**④ ベースアップ**＝外の検索は使いません。手本は同じファイルの実物です。採点＝`rank_separation`（1713行）と `_regime_labels`（5545行）と `_independent_step`（5666行）。役割の振り方＝`_role_lineage_table`（5659行）。需給の列の作り方＝`load_demand`（1609行）。壊すプログラムの形＝`b36_demand_attach_gone.sh` と `lib.sh`。

## 4. やること（9つ）

| # | 触るファイル | 何をするか |
|---|---|---|
| **A** | `observe_diag.py` | **`rank_demand_for_regime(bars, cfg)` を新しく作る**＝値決め窓（`_insp_windows()[0]`・`_assert_search_window_only`）で `load_demand(win.index)` の3列を作り、列名を `名前__5m` にする。正解ラベルは `_regime_labels`、先読みは `_regime_horizons()`、間引きは `_independent_step("5m", n)`、採点は `rank_separation`。**全走の本体と同じ関数だけを呼ぶ**（式を書き写さない）。戻り＝`{列名: {ラベル: {N: 分離力}}}` と、測れなかった列と、**`load_demand` が返す被覆率（cov＝元データの範囲と、値決め窓の中で値が在る割合）の3行**。★重複のふるい（`_dup_pairs`）は掛けない（理由＝§7 の補3） |
| **B** | `observe_diag.py` | **`merge_demand_into_ranking(rank, auc_demand, unmeasured)` を新しく作る**＝いまの成績表（辞書）に、A の結果を足す。①窓・先読み・時間足の欄が成績表と一致しなければ止める（fail-closed） ②役割は `_role_lineage_table()` で系統「需給」を持つ役割だけ ③足した後に |分離力−0.5| の降順に並べ直す ④`測れた列`・`順位に載った列` を数え直す ⑤測れなかった列は `省いた列` に理由つきで記録する ⑥**指標の列は1本も書き換えない** |
| **C** | `observe_diag.py` | **新しい入口 `add_demand_to_ranking(bars_csv, config_path)` を作り、CLI に `--add-demand` を足す**＝`--rank-regime --add-demand <5分足CSV>` で、成績表を読み → A → B → 同じファイルに書き戻す。前後の本数（測れた列・載った列）と、足した列の分離力と、**需給3列の被覆率（A の cov の3行＝この分離力が何%の標本で出たか）**と、「重複のふるいは未適用」の1行と、段ごとの経過時間を印字する。被覆率は成績表の json にも `需給の被覆` の欄として書き残す（生成器はこの欄を読まない＝順位の中身は変わらない）。`--cols`・`--rank-tf` と同時に指定されたら止める。**★既存の `rank_regime` の引数は増やさない**＝`main` の既存の分岐の手前に `if args.add_demand:` の枝を置いて新しい入口へ回す（足すだけ） |
| **D** | `observe_diag.py` | **自己検査に T-f を足し、その枝だけを数秒で走らせる口 `--selftest-rank-demand` を作る**＝合成の5分足と、偽の需給ファイル（検査6 と同じ作り＝`load_demand` の `files=` に一時ファイルを渡す）で ①A の分離力が、同じ入力で `rank_separation` を直に呼んだ値と一致する ②B が sufficiency に3列を足し、ほかの役割には足さない ③B の前後で指標の列の分離力が1つも変わらない ④窓が違う成績表には止まる、を確かめる。**T-f は既存の `selftest` の中に足すのではなく、新しい関数 `selftest_rank_demand()` にし、`selftest()` の末尾から呼ぶ行を1行 足す**（足すだけ） |
| **E** | `engine_tuner_gen.py` | **`ranked_materials` の印の判定に需給の枝を足す**＝既存の `if not ex.indicator_enabled(nm): continue` の**手前**に、「列名の種類が `iref.DEMAND_REF` に在れば `ex.demand_enabled` で見て、通れば rows に足して `continue`、通らなければ `continue`」の枝を置く（既存の行は触らない）。**`_family_tf_from_col` に需給の枝を足す**＝`name, tf = col.rsplit("__", 1)` の直後に「名前が `DEMAND_REF` に在れば `(名前, 時間足)` を返す」の2行を置く（参照表を通さない・既存の行は触らない）。**`ranked_groups` のコードは触らないが、挙動は変わる**＝いまは `_family_tf_from_col` が需給で止まるので需給の列を飛ばしている。直した後は需給の組（種類＝需給の名前・時間足＝5m）を拾う。拾うのは B が需給を足した役割（sufficiency）だけで、location と env の群には混ざらない（成績表の側で需給がその役割に無いため）。`_ranked_material_at` は需給を引かない（`fam not in ranges` で今までどおり飛ぶ＝説明を1行 足すだけ） |
| **F** | `engine_tuner_gen.py` | **自己検査に T23-demand を足し、その枝だけを数秒で走らせる口 `--selftest-rank-demand` を作る**＝需給3列を持つ小さな成績表を一時的に差し込み ①`ranked_materials("sufficiency")` に需給3列が出る ②`demand_on` から1件 外すと、その列だけ消える ③戻すと出る ④`_family_tf_from_col("CVD__5m")` が `("CVD", "5m")` を返す ⑤`ranked_groups("sufficiency")` に需給の組が出て、`ranked_groups("location")` と `ranked_groups("env")` には需給の組が1つも出ない。**T23-demand は新しい関数 `selftest_rank_demand()` にし、`selftest()` の末尾から呼ぶ行を1行 足す**（足すだけ）。**★既存の T23②（location の1位＝S-Rタッチ数(144,0.006)__15m）は書き換えない**＝需給は sufficiency にしか載らないので location の順位は変わらない。変わっていないことは工程表 6 の `--selftest` で実測する |
| **G** | `.claude/hooks/require_design_contract_before_run.sh` | 「確認のための走行」の旗の一覧に `--selftest-rank-demand` と `--add-demand` を足す（`--selftest-marks` と同じ理由＝独立した語として完全一致で見るため。hook の直しは承認不要＝まこさん指示 2026-09-06）。**★なぜ最初にやるか**＝この旗が無いと、設計↔実装ゲートの照合A(双方向) が「未コミットの .py が `impl_functions` に無い」で走行を止める（`impl_functions` は2回目の承認まで空・next_step §6 の138番の落ち方）。「確認のための走行」の旗が在れば、そのゲートを通る。`--rank-regime --add-demand` は `--add-demand` の語で通る |
| **H** | `.claude/breaks/b38_rank_demand_reader_gone.sh`・`b39_rank_demand_merge_gone.sh`・`b40_rank_demand_touch_indicator.sh` | **壊すプログラム3本を新しく作る**（手本＝b36・lib.sh）。b38＝`ranked_materials` の需給の枝を消し `engine_tuner_gen.py --selftest-rank-demand` を測る（条件3）。b39＝B の「足す」処理を消し `observe_diag.py --selftest-rank-demand` を測る（条件1・T-f の②が落ちる）。b40＝B の中に「足した後に指標の列の分離力を1つ書き換える」行を注入し `observe_diag.py --selftest-rank-demand` を測る（条件2・T-f の③が落ちる）。3本とも数秒（承認のときの打ち切り 120秒 の中） |
| **I** | `.claude/audits/m2d1_ranking_scan.py` | **`--assert-demand` の口を足す**＝実物の成績表を読み、需給3列（`iref.DEMAND_REF` の鍵）が順位に載っていなければ rc=1。承認のプログラムは完成の条件の「その数字を出したコマンド」を実際に走らせて rc=0 を求める（`approve_impl.sh` の386行・432行）ので、条件1のコマンド欄をこの1本にする。★この口は 2026-09-07 に足した（設計書を書く前に足したので、承認の相手として TARGET に入れる）。**あわせて⑥（生成器が実際に使う順位）に sufficiency（ラベル全部）の上位15組と、需給3列がその中で何位かを出す行を足す**＝工程表 4 で まこさんが目で見る材料。★この道具は読むだけ（成績表を書き換えない） |

**工程表（★M2-D-2 (c) の決定＝成績表を作り直したあと、上位の材料を まこさんが目で見て OK を出してから M2-D-5 へ進む、の順番に合わせた。Web Claude の指摘 黄2 で直した）**

| 順 | 何を | どちらの段か |
|---|---|---|
| 1 | **G（hook の旗）を最初に**、次に A〜D（成績表を作る側）と I（目視の材料の行）を書く。`observe_diag.py --selftest-rank-demand` を走らせる | M2-D-4 |
| 2 | 差分の走行 `--rank-regime --add-demand`（フロー宣言に時間の見込みと過去の実測の逐語を書く）。走らせる前に成績表の控えを取る。**時間の見込み＝15分未満。根拠**＝A が行う計算は、値決め窓 158,112本に対する正解ラベル3本×先読み2本の rolling の演算と、需給3列の読み込み（1分足 CSV 1本＝1,226,881行と OI の CSV 1本）だけで、全走が2時間17分かかった主因（材料 6,101列の生成＝`build_features` を時間足11本ぶん）を含まない。C が段ごとの経過時間を印字するので、走らせた実測を記録に残す | M2-D-4 |
| 3 | `python3 .claude/audits/m2d1_ranking_scan.py` で前後を数え、需給3列の順位（sufficiency の中の位置と分離力）を出す | M2-D-4 |
| 4 | **まこさんが順位を目で見て OK を出す**（これが無いと 5 へ進まない） | M2-D-2 (c) |
| 5 | E・F（生成器の読む側）と H（壊すプログラム b38・b39・b40）を書く。`engine_tuner_gen.py --selftest-rank-demand` を走らせる | M2-D-5 |
| 6 | `engine_tuner_gen.py --selftest`（約6分半・❌ は既知3件のまま・T23② の location の1位が変わっていないことを実測する）と `engine_tuner_exec.py --identity`（S2） | M2-D-5 |
| 7 | `gen_signal_families.py --verify`（G2）→ `leak_causality_diag.py`（H2）→ **設計書の `NEW_FILE:` の行を外す**（b38・b39・b40 は 5 で実在するようになる。新規と書いたまま実在すると承認が止まる＝worklog §43-7 の実例）→ 触る関数だけを手で列挙して `impl_functions` を埋める（§9 の予定の一覧を、実物の `git diff` で確かめてから確定させる。`verify_design_contract.py --write` は使わない＝それは SPEC を `.actual.md` に書き出す道具で、`impl_functions` の出どころではない）→ 2回目の承認（機械が壊すプログラムと条件のコマンドを走らせて測る）→ 記録 → 監査 | M2-D-7 |

★A〜I は1つの設計書で承認を受けますが、書く順番は上の表のとおりで、4 の OK の前に E・F・H は書きません。

## 5. ★疑似シミュ由来の固定値ゼロ宣言

疑似シミュ（probe）から出た数字を、1つも固定値にしていません。

- **(a)** この工事で新しく決める数字は 0個です。閾値・期間・パラメータを1つも決めていません。需給の列名の `__5m` は数字の決定ではなく、元データが5分足1本であるという事実の印です。
- **(b)** probe の数値を設計の固定値に焼いていません。probe を1本も走らせていません。
- **(c)** 採否は probe でなく、自己検査の終了コードと、壊すプログラムの終了コードと、差分の走行の前後の数え上げで決めます。

## 6. 変更の単位（H16）

1レバーです。「**需給3列を、指標と同じ物差しで採点して成績表に足し、読む側が落とさないようにする**」の1つです。A〜I は、その1つを成り立たせる部品です。

**過去に破棄した失敗の再演ではありません。**乱数は1つも増えません。順位から引いて束に入れる所（`_ranked_material_at`・`sample_regime_build`）は触りません。

**入っていないもの（正直に）**＝①需給を場面の判定の束に引く道（需給を場面の判定でどの役割として使うかは M2-E で相場の法則から決める）②需給が本当に場面を分けるか（分離力が 0.5 から離れるか）は走らせるまで分からない ③全走（2時間17分）はしない。

## 7. 塞げないもの

| # | 問い | 塞げないこと |
|---|---|---|
| **監査 Q5 の1** | 差分で足した需給の分離力は、全走に需給を含めた場合と同じか | **全走を1回 走らせないと直接は比べられません。**代わりに、同じ関数（`rank_separation`・`_regime_labels`・`_independent_step`）と同じ窓を使い、T-f の①で「同じ入力に対して直接 呼んだ値と一致する」ことを確かめます。全走の本体の中で需給を読む形にしなかった理由は、まこさんの決定（2時間17分の全走をしない）です |
| **監査 Q5 の2** | 成績表の中身が正しいか | **json をそのまま読んで足します。**成績表の指標の列が偽造されていれば、この工事では見抜けません（G2・H2 と同じ限界）。足す前後で指標の列が変わらないことだけを確かめます |
| **監査 Q5 の3** | `--add-demand` を打ち忘れたら | **成績表に需給は載らないままです。**完成の条件1（`m2d1_ranking_scan.py --assert-demand`）が rc=1 のまま残るので、済にできません |
| **監査 Q5 の4** | この道具自身を書き換えられたら | **無効にできます**（承認ゲートの対象なので承認は要ります。H2 の印の対象でもあるので、触れば印が失効します） |
| **監査 Q5 の5** | 需給を順位に入れても、場面の判定の束に使われるか | **使われません。**需給の役割は型の表で sufficiency で、場面の判定の束が順位から引くのは location と env だけです。需給を束に引く道は M2-E で作ります。この工事は「順位に載って、読める」までです |
| **補1**（Web Claude の指摘） | 型の表の rule「時間足には展開しない」を「入口の条件の材料についての決まり」と読むのは、CC の解釈ではないか | **解釈です。**rule の文は「需給の列（taker_ls・L-S比・CVD）は入口の条件の材料に使える。★時間足には展開しない（元データが5分足の1本だけ）」で、成績表の列名については何も書いていません。監査が別の読み方（成績表にも `__5m` を付けてはいけない）を採る余地はあります。その場合は、列名から `__5m` を外し、読む側で「時間足の無い列＝5m」と扱う形に直します（採点の中身は変わりません） |
| **補2**（Web Claude の指摘） | 生成器の自己テスト T23 の突き合わせが、需給の列で落ちないか | **落ちません（実物で確かめた）。**T23 の突き合わせは「型の表の parts × tfs（555×11＝6,105本）のうち、順位に載っている本数」を数えて印字するだけで、順位にだけ在る列（需給の `__5m`）は `ng` に足しません（`engine_tuner_gen.py` の T23 の突き合わせの行）。T23① は location の並び、T23② は location の1位、T33-d は env の順位を見るので、sufficiency にだけ載る需給には当たりません。**限界**＝これはコードを読んだ結果で、工程表 6 の `--selftest`（約6分半）で実測して記録します |
| **補3**（Web Claude の指摘） | 需給の列に、全走の本体が掛けている重複のふるいが掛かるか | **掛かりません。**全走の本体は採点の前に `_dup_pairs`（法則 C2・C3＝「実質 同じもの」の省く側を落とす）をカタログの列に掛けています（`rank_materials_for_regime` の冒頭）。A はこのふるいを需給に掛けません。理由＝`_dup_pairs` はカタログの列どうしを比べる作りで、別枠の需給を渡す形が無いためです。需給が指標のどれか（例＝CVD と OBV傾き・PVT傾き、taker_ls と出来高系）と「実質 同じもの」でも、この工事では落ちません。束に引くのは M2-E なので、そこで確かめます。この工事では、需給を順位に載せるときに「重複のふるいは未適用」と印字して記録に残します |

## 8. §4.6 ハード制約の照合

**H1〜H16 の16件を1件ずつ照らします（該当4件・非該当12件）。**触るのは、材料の順位を作る道具と、それを読む生成器の関数と、壊すプログラムです。売買のロジック・審判（score.py・eval_engine）・発注には触りません。`acceptance_checklist.md` の【群2】（同ファイル19行の逐語「売買のロジックか審判を触るときだけ、1件ずつ照合する。触らないときは「まとめて非該当（理由）」の1行でよい」・18件）は、同じ理由でまとめて非該当です。

| H | 何の決まりか | この工事 | 理由 |
|---|---|---|---|
| H1 | ポジション合計 0.12 BTC | 非該当 | 売買を1件も回さない。建玉のサイズに触れる処理を書かない |
| **H2** | leak なし | **該当** | 需給の列は `load_demand` が作り、元データの終端より後を ffill で埋めない。正解ラベルは未来を見るが、成績を測るときにだけ使い、判定の条件には入れない（全走と同じ）。値決め窓だけで測る（`_assert_search_window_only`）。`observe_diag.py` と `engine_tuner_gen.py` は H2 の印の対象なので、直したら G2 → H2 の順で印を取り直す |
| H3 | net 判定（gross 禁止） | 非該当 | net を計算しない。金額を1つも出さない |
| H4 | コスト確定値 | 非該当 | 手数料・funding・slippage の定数に触れない |
| H5 | 約定モデル | 非該当 | 約定を模さない |
| **H6** | 価格非依存 | **該当** | 需給の3列は 比（taker_ls・L-S比）と数量の累積（CVD）で、ドルの金額の列は作らない。分離力は順位（rank）で出すので単位に依らない |
| H7 | 足の標準＝5m | 非該当 | 需給は元データが5分足1本なので5分足で採点する。ほかの足を採用する話ではない |
| **H8** | 期間分割 | **該当** | 差分の走行は値決め窓だけで測る（成績表の `窓` と一致しなければ止める＝B の①）。採点窓は1バーも使わない |
| H9 | 最小注文 | 非該当 | 注文を出さない |
| H10 | サイズ固定値扱い禁止 | 非該当 | サイズに触れない |
| H11 | 合格ライン／地面 | 非該当 | 合否を判定しない |
| H12 | 異常値 STOP | 非該当 | 勝率・月 net を出さない |
| H13 | judge 固定 | 非該当 | score.py・eval_engine に触れない |
| H14 | 発注フラグ | 非該当 | 発注のコードに触れない |
| H15 | Entry のボラ逃げ禁止 | 非該当 | Entry の方向スコアもラベルも作らない。成績表の正解ラベル（強さ・向き・大きさ）は既存のもので、この工事では変えない |
| **H16** | 1変更・過去失敗の不再演 | **該当** | 上の §6 に書いた |

## 9. 完成の条件

**★状態は「未着手」です。**「済」にするのは機械です（恒久の決まり64番）。

**★触る関数の一覧（`impl_functions`）は、実装の後に確定させる。**中身は「触る関数だけ」を手で列挙します。いまは空です。書き方の決まり（2026-09-05・worklog 20260904 §22 の逐語「前の設計書までは『実物の全関数の写し』を貼っていたが、この回は『触る関数4件』を手で列挙した。理由＝照合B（impl_functions ⊆ 触った関数）の定義＝全関数を貼ると、差分が commit されるまで触っていない関数が全部 落ちる」・next_step §6 の132番）に従います。`verify_design_contract.py --write` は公開する関数の一覧（SPEC）を `.actual.md` に書き出す道具で、`impl_functions` の出どころではありません。

**列挙する予定（実装のときに実物で確定させる）**＝2ファイルです。①`scripts/priority_rebuild/observe_diag.py`＝A〜D で新しく作る4関数（`rank_demand_for_regime`・`merge_demand_into_ranking`・`add_demand_to_ranking`・`selftest_rank_demand`）と、行を足す既存の関数（`main` の引数と分岐・`selftest` の末尾の呼び出し）。②`scripts/priority_rebuild/engine_tuner_gen.py`＝E で行を足す `ranked_materials`・`_family_tf_from_col`、F で新しく作る `selftest_rank_demand` と、行を足す `selftest`・`main`。**★照合A(双方向) が見るディレクトリは `scripts/priority_rebuild`・`.claude/hooks`・`.claude/tools` の3つ**（`verify_design_contract.py` の1048行で実物を確かめた）＝`.claude/audits/m2d1_ranking_scan.py` は対象の外なので `impl_functions` に入れません。`.claude/hooks/require_design_contract_before_run.sh` は .sh なので照合A の対象（.py）の外です。

**★コマンドに数秒で走る口を選んだ理由**＝`engine_tuner_gen.py --selftest` は約6分半かかり、承認のときの打ち切り（120秒）を超えます。しかも既知の ❌3件（T24②・T26・T30・M2-E で直す）で終了コードが既に 0 ではないので、「壊すと落ちる」の測りに使えません。だから、この工事の枝だけを走らせる口を2本（`observe_diag.py` と `engine_tuner_gen.py` に1つずつ）作り、そこを測ります（`--selftest-extra-gate`・`--selftest-marks` と同じ形）。

**★1回目の承認では3行とも「未着手」のまま**＝条件1のコマンドは、差分の走行の前なので rc=1（実測済み）。条件2と3のコマンドは、口がまだ無いので走りません。壊すプログラムもまだ在りません。2回目の承認で、機械が3本の壊すプログラムと3行のコマンドを走らせて測ります。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 成績表に需給3列（taker_ls__5m・L-S比__5m・CVD__5m）が順位に載っている（いま 0本＝いまは rc=1） | `python3 .claude/audits/m2d1_ranking_scan.py --assert-demand` | 実経路 | B の「足す」処理を消して差分の走行をやり直すと、成績表に需給が載らず rc=1 に戻る（承認のときの測りは b39＝T-f の②） | `b39_rank_demand_merge_gone.sh` | 終了コードが0でない | **未着手** |
| 2 | AUDIT-1＝差分で足した需給の分離力が、同じ入力で `rank_separation` を直に呼んだ値と一致し、足す前後で指標の列の分離力が1つも変わらない | `python3 scripts/priority_rebuild/observe_diag.py --selftest-rank-demand`（T-f の①③） | 実経路 | B の中に「足した後に指標の列の分離力を1つ書き換える」行を注入すると、T-f の③が落ちる | `b40_rank_demand_touch_indicator.sh` | 対象 | **未着手** |
| 3 | 生成器の順位読みで需給3列が sufficiency に出て、`demand_on` から1件 外すとその列だけ消え、戻すと出る | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest-rank-demand` | 実経路 | `ranked_materials` の需給の枝を消すと、需給の列が1本も出ずに落ちる | `b38_rank_demand_reader_gone.sh` | 終了コードが0でない | **未着手** |

<!-- ACCEPT_TABLE_END -->

**自己検査（完成の条件の外で、実装の後に必ず走らせて記録するもの）**＝①`engine_tuner_gen.py --selftest`（約6分半・❌ が既知の3件のまま増えない・T23② の location の1位が変わっていないことを実測する）②`engine_tuner_exec.py --identity`（S2・直す前と後で結果が同じか確かめる走行・md5 不変）③`gen_signal_families.py --verify`（G2）と `leak_causality_diag.py`（H2）④成績表の前後の突き合わせ（載った列 5,981本 → 5,984本・指標の列の分離力は不変）。

## 10. DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/observe_diag.py",
  "impl_functions": {},
  "no_impl_functions_reason": "実装の後に、触る関数だけを手で列挙する（照合B＝impl_functions ⊆ 触った関数・worklog 20260904 §22 の決まり）。対象は observe_diag.py と engine_tuner_gen.py の2ファイル（§9 に予定の一覧）。2回目の承認の版で埋める",
  "self_check_calls": ["rank_demand_for_regime", "merge_demand_into_ranking", "add_demand_to_ranking", "selftest_rank_demand", "load_demand", "rank_separation", "_regime_labels", "_independent_step", "_role_lineage_table"],
  "must_use": {},
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は値の一覧を持たない（需給3列の名前は observe_diag._DEMAND_FILES と型の表 extra_parts.demand.parts が正本で、コードに写さない）",
  "generated_from": {
    "impl_functions": "実装の後に、触る関数だけを CC が手で列挙する（実物の diff で確かめてから書く・全関数の写しにしない・worklog 20260904 §22）",
    "self_check_calls": "この設計書 §4 の A〜D が observe_diag.py に新しく作る関数名4つと、A・B が呼ぶ observe_diag.py の既存の関数名5つ（行番号は書かない＝別セッションの編集で動くため、関数名で指す）"
  }
}
```

# 設計書｜4つの要素（指標・閾値・パラメータ・時間足）の使い方を強制する｜v2（59回目・2026-08-25）

TARGET: scripts/priority_rebuild/engine_tuner_gen.py
TARGET: scripts/priority_rebuild/leak_causality_diag.py

> **★2つ目の TARGET（まこさん承認 2026-08-25・逐語「leak_causality_diag.py の1行を直してよい」）**＝H2 の道具が `gen.sample_structure` の案（印つき）を実行器へ直に渡して落ちる（`tuner_recipes` の331行・Read で確認）。渡す前に `gen.strip_marks` を通す**1行だけ**を直す。ほかは触らない。

**★この1本が設計書です。**ほかの場所に設計書を作りません（`permanent_rules.md` §0-2）。
**★前の版（v58・未承認）の控え**＝`.claude/ratchet/acceptance_archive/unapproved-four-elements-gate-v58-20260825.md`（ハッシュ値の先頭 f05c9dfe58c7ef52）。

<!-- ARC order=2 iter="four-elements-gate-v2-drawn-only-20260825" 前提="監査 cp6＝NO-GO（印が自己申告で本物でない／完成の条件が自分と矛盾／実測3件が実物と違う）と、まこさん決定 C-4＝(a')（順位を種類×時間足でまとめて読む＝組の成績は中央値・数字だけ範囲から引く）" 採否="未定" 狙い="値を『範囲から引く』以外の作り方をコードから無くし、検査のあとに値を書き換える道を塞ぎ、出どころを記録に残す" 内容="_mat/_thr を『引く関数』に置き換え・_cat 削除・第2段と走らせる入口の再検査・出口の系統の既定を止める・場面の判定は種類と時間足＝順位（種類×時間足の中央値）・数字＝範囲" 方法="18マスを機械が壊して測る（壊し方を CC が書かない）＋静的検査で『引く関数の外で材料を作る所』を数える" -->

---

## 0. まこさんの1行（これが守るべきもの・逐語 2026-08-24）

> 指標、閾値、パラメータ、時間足の役割に基づき、法則に則って４つを組み合わせ、Entry/Exit やレジーム判定などの条件を作る

> 出口も含め、engine_tuneを設計実装する際に、守るべき６つをまもらせるようにしてほしい（逐語 2026-08-25）

**守るべき6つ（まこさん確認済み・言い換えない）**＝①指標がカタログに在る ②閾値が範囲から ③パラメータが範囲から ④時間足が使えるものから ⑤役割に沿う ⑥つなぎ方が型の表と場面の決まりに沿う。
**当てる範囲**＝入口・場面の判定・出口の3か所＝18マス。

## 1. この版の前提（監査の結果と、まこさんの決定）

**監査 cp6（2026-08-25・`.claude/audits/2026-08-25_four_elements_gate_design_impl_cp6_audit_report.md`）＝NO-GO。**根拠のうち、この版が直すもの＝

| 監査の指摘 | 中身 |
|---|---|
| 印が自己申告 | `_mat` は渡された値が何でも「範囲から」の印を付ける。出口の材料は決まった一覧（pool）の数字なのに印が付いている |
| 検査の後に値が変わる | 第2段の `apply_slots` が値を書き込んだ後、検査が走らない＝売買に使う値が検査を受けていない |
| 点の一覧を作る関数が残る | `_cat` は未使用のまま残り、1行で戻せる |
| 印を消す | `strip_marks` が案を返す前に印を消す＝保存された案から出どころを後で確かめられない |
| 場面の判定を止める設計 | v58 の条件4は「場面の判定の案が拒否される」を合格にしていた＝2026-08-23 承認の「1位から順に組む」が動かなくなる |
| 表に基準が無い枝を黙って通す | 出口の枝で系統の欄が無いとき、コードに直書きの6系統（全部）を既定にしている |
| 完成の条件の矛盾・測れない条件 | 条件5と条件20が真逆／条件8・9・11・18 が測れない・曖昧 |
| 実測の誤り | 出口の表「19件とも空」（実物は BREAKOUT の1件に系統の欄が在る）／行番号の食い違い |

**まこさん決定（2026-08-25）＝C-4 は (a)**＝場面の判定で、指標の**種類と時間足**は成績表の順位から取り（2026-08-23 の決定のまま）、**数字（パラメータ）だけ**をその指標の範囲から引く。**★同日の追加の決定＝(a')**（逐語「(a')これにする」）＝順位は「種類×時間足」ごとにまとめて読む（詳細＝§4 やること2）。

**承認の状態**＝v58 は未承認。v58 の実装の一部（`_mat`・`_thr`・`assert_marks`・`assert_roles`・`strip_marks`・`_cc`・`_vr`）は承認前に `engine_tuner_gen.py` に入っている。この版は、それを「引く関数」に置き換える。

## 2. いま実物に在るもの（2026-08-25 に grep で実測した行・この版が置き換える相手）

| 名前 | 行（`grep -n` の出力） | いま何をするか | 何が足りないか（監査） |
|---|---|---|---|
| `draw_param` | 317 | 指標の範囲から数字を引く | 引いた事実が値に残らない |
| `PARAM_SRC`／`Q_SRC` | 351／352 | 印の鍵の名前 | 印は「在るか無いか」しか見られない |
| `_mat` | 355 | 材料の辞書を作り、無条件に印を付ける | 決まった数字にも印が付く（出口 1333・1373 行で実際に起きている） |
| `_thr` | 371 | 閾値の辞書を作り、無条件に印を付ける | 同上 |
| `assert_marks` | 389 | 印の有無を見る | 値が範囲の中かを見ない |
| `assert_roles` | 406 | 入口と場面の判定の役割×系統を見る | 出口を見ない。出口の条件は役割が一律 `env` の直書き（1359 行ほか） |
| `_cc`／`_vr`／`strip_marks` | 457／467／473 | 自己テストと本走で印を外す | 保存する案からも印が消える |
| `_material_from_col` | 1613 | 成績表の列名から材料を作る（数字も列名の値） | 78番の実体＝数字が範囲から引かれていない |
| `_pick_exit_material` | 1322 | 出口の材料を pool から引く | 数字が pool の決まった値のまま印が付く |
| `_exit_indicator_cond` の既定 | 1345〜1346 | 系統の欄が無い枝に6系統を既定で当てる | 黙って通す |
| `sample_structure` の検査と返却 | 1873〜1879 | 印と役割を検査し、印を外して返す | 出口に役割の検査が無い・印が消える |
| `_cat` | 2404 | 点の一覧から選ぶ値を作る | 未使用のまま残る（1行で戻せる） |
| `apply_slots` | 2541（呼び出し 2798・2866） | 第2段の値を案に書き込む | 書き込んだ後に検査が無い |

**実行器（`engine_tuner_exec.py`）に既に在る検査（この版は触らない・そのまま使う）**＝G6 `_check_param_range`（580 行・材料のパラメータが範囲の中か）／G5 `_check_num_range`（586 行・当てているのは2件だけと自認）／材料を作る瞬間のカタログ（1548 行）と時間足（1561〜1562 行）の検査。

## 3. 深掘り4点

### ① 真因（root cause）

**印は「作った側が自分で押す」ものなので、値の出どころを保証しない。**外部知見（監査の検索4・5）＝自己申告はでっち上げられる。強制になるのは「作った側の署名」ではなく「引く以外に作れない形」。

### ② 期待値分解

**該当なし**（売買の戦略ではなく、案を作るプログラムの直し）。net は動かない。**代わりに動く数字**＝「引く関数の外で材料・閾値・数値を作っている所」の件数（静的検査）と、18マスのうち「機械が壊して止まった」マスの数。

### ③ root を直すか symptom か

**root を直す（Y）。**symptom の直し方＝出口の 1333・1373 行だけ `draw_param` に書き換える。採らない。理由＝印が無条件に付く限り、次に同じ形が別の場所で起きても検査は通る（監査 B1）。

### ④ ベースアップ（参照したもの）

| 何を見たか | 取った事実 |
|---|---|
| 監査 cp6 の報告 §3 Q2・§6 C-1〜C-7・§4 外部検索 5・6・7・8 | 自己申告の弱さ／「引く以外に作れない形」／検査と使用の間で値が変わる穴（TOCTOU） |
| `engine_tuner_gen.py`（Read＝355〜480・918〜982・1322〜1411・1613〜1642・1860〜1884） | 上の §2 の実物 |
| `engine_tuner_exec.py`（Read＝570〜609・1538〜1565） | G5・G6・カタログ・時間足の検査の実物 |
| `exit_families.json`（プログラムで数えた） | 枝19件・系統の欄が在るのは BREAKOUT の1件 |
| `verify_design_contract.py`（Read＝700〜772） | `--write` は実物から `.actual.md` を書き出す・`--diff` で齟齬を数える |

## 4. やること（8件）＝監査の C-1〜C-7 と決定 (a')（8番は2回目の監査の指摘＝B6）

| # | やること | 直す場所 | 何が変わるか |
|---|---|---|---|
| **1** | **C-1＝材料・閾値・数値を「引く関数」でしか作れなくする。**`_mat(family, param, tf)` を廃止し、`_mat_drawn(rng, family, tf, ranges)` にする（数字は関数の中で `draw_param` が引く。外から数字を渡す口を無くす）。同じく `_thr(q)` → `_thr_drawn(rng, limits)`（`draw_q` が引く）。出口の枝の数値（倍数・割合・戻し）も `_num_drawn`／`_int_drawn` で引く。2本の線の交差（Stoch%K×%D など）は `_mat_pair_drawn`（1回 引いた数字を2本で共有）。**印の中身**＝`{"kind": "range", "lo": …, "hi": …}`（引いた瞬間の範囲を写す・「range」の1語ではない） | `_mat`・`_thr`・`_pick_exit_material`・`_exit_indicator_cond`・`_make_exits`・入口の材料を作る所（941 行）・自己テストの見本 | 決まった数字を材料にする書き方がコードに無くなる。監査 B1・B3 が閉じる |
| **2** | **決定 (a')（まこさん 2026-08-25・逐語「(a')これにする」）＝場面の判定は、順位を「種類×時間足」ごとにまとめて読み、数字は範囲から引く。**①`ranked_materials` の出力（列ごとの順位＝例 ER21__1h・ER35__1h が別の行）を、`_ranked_material_at` が使う前に「種類×時間足」ごとにまとめる＝同じ種類・同じ時間足の列の成績の**中央値**をその組の成績にする（例＝ER×1h の成績＝ER14・ER21・ER35 … の成績の真ん中の値）。**★「いちばん良い列」ではなく中央値にする理由（3回目の監査の指摘・2026-08-25 に実測）**＝1組が持つ列の本数は 1〜10本 でばらつく（実測＝env 6,534組・中央3本・最大10本）。「いちばん良い列」で読むと、列を多く持つ種類ほど まぐれの良い数字が出やすく、上に来やすい（類型C＝多重検定と同じ型）。実測＝「最良」と「中央値」で読んだときの上位10の重なりは、役割ごとの平均で 5.7〜6.8／10（＝3〜4組が入れ替わる）。中央値なら列の本数による有利不利が消える。**順位の表そのもの（M2-3 で承認）は変えない＝読み方だけ** ②まとめた順位を1位から順に走査し、種類と時間足を取る ③数字は `_mat_drawn(rng, family, tf, ranges)` が範囲から引く。`_material_from_col` は `(family, tf)` だけを返す関数 `_family_tf_from_col` に変える | `_material_from_col`・`_ranked_material_at`・`sample_regime_build` | 78番が直る。場面の判定は止まらずに組める（v58 の穴A が閉じる）。順位の根拠が「その種類がその時間足で効いた」になり、数字を引き直すことと矛盾しない。同じ種類は順位に1回だけ出る。**★(a) のままだと残った副作用2つ**（順位の根拠の数字と使う数字が食い違う／同じ種類の行が順位に何本も並ぶ）は、(a') で消える |
| **3** | **C-2＝検査の後に値を書き換える道を塞ぐ。**①`_cat` を削除する ②`apply_slots` が値を書き込むとき、その値スロットの範囲（`value_slots` が持つ kind/lo/hi）を印として一緒に書く ③第2段の `run_trial_guarded` の直前と、前後比較（2866 行）の直前で、書き込んだ案に `assert_provenance`（下の4）と実行器の `validate_recipe` を掛け直す | `_cat`・`apply_slots`・`run_generation` | 売買に使う値が検査を受ける。監査 B4 が閉じる |
| **4** | **印の検査を「在るか」から「値が範囲の中か・範囲が正本と同じか」に変える。**`assert_marks` を `assert_provenance` に置き換える＝案の中の材料・閾値・数値ごとに、印の範囲を読み、①値がその範囲の中か ②その範囲が いまの正本（`material_ranges`／`q_range_of`／`num_range_of`）と一致するか、を見る。どちらか外れれば `SampleError`。かたちの列（geo）・時刻・玉の状態の材料は「数字を持たない材料」として印の対象から外す代わりに、**候補の表（`table["geo_ok"]` など）に在るか**を見る（監査の穴E） | `assert_marks` → `assert_provenance` | 手で足した印（監査 B2）は範囲が正本と違えば落ちる。範囲の中の決まった値を手で入れる形は、ここでは止まらない（→ 静的検査 K1 で止める） |
| **5** | **C-6＝出口の枝に系統の基準が無ければ止める。**1345〜1346 行の直書きの既定（6系統）を消し、`lineage_any`／`lineage` の無い枝は `SampleError`。**★前提（2026-08-25・60回目に片づいた）**＝出口の枝の系統の案を、私が出典つきで作り、まこさんが決めて表を再承認する。**★実測で分かったこと**＝系統の欄を実際に使う枝は **2件だけ**（`REVERSE_IND`＝指標の反転で利確／`BREAKOUT`＝前提崩れで成行）。ほかの17件は指標の条件を1本も作らない（案300本の実測＝0回）。**決めたもの（2026-08-25）**＝`REVERSE_IND`＝オシレーター・トレンド・ボラ・構造位置 の4系統／`BREAKOUT`＝もとの3系統に トレンド を足して4系統。**案の出どころ**＝`v9_exits.md`（機械生成・V9 の反転の枝が使う指標）と 軸カタログ X-g 系（`exit_families.json` の `axis_options`）。**表は承認済み**（`exit_families_approved.txt`＝`f5d53842ff40ab09b8fd69161f6eddff  approved 2026-08-25`）。**＝この5番は実装した**（60回目・§11） | `_exit_indicator_cond`・`exit_families.json`（まこさん承認） | 黙って通す道が消える。表が正本になる |
| **8** | **検査を呼ぶ場所を1か所に頼らない（監査 B6）。**`assert_provenance`・`assert_roles` を、案が売買に使われる入口 `run_trial_guarded` の中でも必ず掛ける（案を作る関数を通さずに渡された案も、ここで止まる）。**例外は恒等レシピ（`identity_*.json`）だけ**＝ファイルのハッシュ値が一致するものだけを例外にする（レーンの名前 `legacy` で例外にしない＝名前を付けるだけで通る道を作らない） | `run_trial_guarded`・恒等レシピの読み込み | 検査を呼ぶ場所が「案を返す直前」と「走らせる入口」の2か所になる。片方を通さない道が消える |
| **6** | **5番（役割）を出口にも当てる。**出口の指標の条件の役割を、一律 `env` ではなく出口専用の名前 `exit` にし、`assert_roles` は出口の条件について「材料の系統がその枝の系統の欄に在るか」を見る。**実行器が役割 `exit` を受けるかを実測してから**（受けなければ、役割の名前は変えず、枝の系統で見る形にする） | `_exit_indicator_cond`・`assert_roles` | 出口の役割が実物の基準（枝の表）で判定される |
| **7** | **C-7＝出どころを記録に残す。**`strip_marks` は実行器に渡す直前（`_cc`・`_vr`・`run_trial` の入口）だけで使い、`sample_structure` は印つきの案を返す。案のハッシュ値は印を外した形で計算する（＝いまのハッシュ値と変わらない）。`Journal` に書く案は印つき。新しい旗 `--verify-provenance <journal>` で、保存された案の全部の値が印の範囲の中か・範囲が正本と同じかを後から数え直せる | `strip_marks` の使い所・`recipe_hash`・`Journal`・`--verify-provenance` | 走行の後でも出どころを機械で再判定できる |

**★変更の単位（H16）**＝中身は1つ＝「材料・閾値・数値は『範囲から引く関数』でしか作れず、その出どころを検査と記録で確かめる」。1〜4・6・7・8 がこの1つの中身。**5番だけは表の再承認が先なので、承認が出るまで入れない**（入れる順番＝1・2・4・7 → 3・8 → 6 → 表の承認 → 5）。

**★触るのは `engine_tuner_gen.py` だけです。**`engine_tuner_exec.py` は触らない（G5・G6・カタログ・時間足の検査は、そのまま実行時の受け皿）。`exit_families.json` は まこさんの承認で変わる（私は案を出す）。

## 5. 18マス＝どの瞬間に・どの関数が止めるか（この版の目標）

**止まる瞬間の名前（監査 Q4 の S1〜S6 をそのまま使う）**＝S1 作る瞬間の絞り込み／S2 案を返す直前の検査（gen）／S3 案1本ずつの検査（exec `validate_recipe`）／S4 型の表との照合（`gen_signal_families.check_structures`）／S5 走らせる瞬間（exec の材料を作る所）／S6 第2段で値を詰めた後。
**合格の基準**＝**S2 で止まる**（＝案を作らせない・まこさん確認済みの理解）。S3〜S5 は受け皿。

| # | 守るべきこと | 入口 | 場面の判定 | 出口 |
|---|---|---|---|---|
| 1 | 指標がカタログに在る | S1（pool は表から）＋S3・S5（いまのまま） | S1（順位の列はカタログ照合・1619 行）＋S5 | S1＋S3・S5 |
| 2 | 閾値が範囲から | **S2 `assert_provenance`**（`_thr_drawn` の印） | **S2**（同） | **S2**（`_num_drawn` の印）。★実行器側の受け皿（G5 が出口の枝の数字を見ない）は、この版の外＝§7 |
| 3 | パラメータが範囲から | **S2 `assert_provenance`**（`_mat_drawn` の印）＋S3 G6 | **S2**（決定 (a')）＋S3 G6 | **S2**＋S3 G6 |
| 4 | 時間足が使えるものから | **S2**（`_mat_drawn` が `table["tfs"]` と `observe_config` の時間足の両方に在るかを見る）＋S4・S5（いまのまま） | **S2**（同・順位の列の時間足も通す）＋S5（★S4 は場面の判定の中身を歩かない＝監査 注2） | **S2**（同）＋S4・S5（いまのまま） |
| 5 | 役割に沿う | S2 `assert_roles`（いまのまま） | S2（いまのまま） | **S2**（やること6＝枝の系統の欄で見る）。**★2026-08-25 に実測＝S2 で止まる**（理由の逐語＝「枝 REVERSE_IND に 系統 出来高 の指標 CMF。枝が使える系統は ['オシレーター', 'トレンド', 'ボラ', '構造・位置']」）。表の承認が出たので「未実装」の印字は外した |
| 6 | つなぎ方が型の表・場面の決まりに沿う | S3・S4（いまのまま） | S3 G7（`--build-regime` のとき） | S3（いまのまま） |

**★場面の判定の列について**＝`--build-regime` は既定 OFF（4477 行）。旗なしのときは場面の判定の中身が案に入らない＝この列の検査は「旗つきの走行」で測る。**旗を既定 ON にするかは、この設計の外**（M2 の再開のときに まこさんが決める・`next_step.md`（0-C））。

## 6. ★疑似シミュ由来の固定値ゼロ宣言

**疑似シミュは1回も使っていない。**この設計の数字は、実物の行番号（2026-08-25 の `grep -n`／Read の出力）と、プログラムで数えた件数（出口の枝 19件・系統の欄 1件）だけ。**設計の中に閾値・段数・パラメータの類は1つも作っていない。**範囲の正本は `recipes/search_limits.json`・`material_ranges` のまま。

## 7. 入っていないもの（正直に）

| 何 | なぜ入れないか | どこで扱うか |
|---|---|---|
| 出口の枝の数字の**実行器側**の範囲検査（G5 が2件しか見ていない） | `engine_tuner_exec.py` を触る変更なので、この設計（TARGET＝gen）の外 | TARGET を exec にした次の設計書 |
| 出口の枝の系統の表の中身 | トレードの判断＝まこさんが決める | 私が出典つきの案を出す → まこさんの承認 → やること5 |
| つなぎ方を乱数で決める件（D14①） | 守るべき6つの外（M3 の欠陥） | `engine_tuner_defects.md`・M3 |
| `--build-regime` を既定 ON にするか | M2 の再開の判断 | `next_step.md`（0-C） |
| **順位で測った数字と、範囲から引ける数字の幅が違うこと（前提・誤りではない）** | 順位の表は、指標ごとに 3〜4通りの数字（例＝EMA傾き＝9・20・50・200）で成績を測っている。範囲から引ける数字は 181〜192通り（例＝9〜200）。**＝組の成績（中央値）は、実際に引いた数字（例＝EMA137）の成績を保証しない。**これは (a') が持ち込んだものではなく、「数字は範囲から引く」と決めた時点で必ず付いてくる（4回目の監査の指摘・2026-08-25）。**順位の表に範囲の外の数字を持つ列は0列**（同監査が 2,594列 を全部 調べた） | 直す対象ではない。引いた数字の成績は、engine_tuner が走らせて net で決める（要件の目的そのもの） |
| **設計書の行番号を機械で出すこと（監査 P-2）** | この設計書の行番号は、私が 2026-08-25 に `grep -n` と Read で確かめて手で写したもの（12件・2回目の監査で12件とも当たりを確認）。**実装すると行番号は全部ずれる。**`--write` は関数の名前だけを書き出し、定義の行は出さない | `next_step.md` §6 の93番（`--write` に「公開する関数の定義の行」を足す）。それまでは、実装後に §2 の行を grep で写し直す |
| **CC 自身に対する完全な強制** | Python では、作者が新しい書き方を足す道は塞げない（監査の外部知見4）。この設計が作るのは①引く以外の書き方をコードから無くす ②静的検査で「引く関数の外で作る所」を数える（K1）③実行時の範囲検査（S2・S3）④記録からの再判定（K9）の4重。**CC が1行 足したら K1 で数に出る**、が限界 | — |

## 8. 変更の単位（H16）・審判整合（D）・§4.6 の照合

- **変更は1つ**（上の §4 の★）。**既定 OFF にしない**（検査を切れる形にすると私が切る道が残る・恒久57番）。
- **審判整合＝該当なし。**新しい決済の理由は出さない。`score.py`・`eval_engine.py` は触らない。
- **§4.6**＝H1・H2・H3〜H5・H8 は非該当（建玉・時系列・net・日付を扱わない）／H13 守る／H16 守る。
- **★コードを触るので、H2 の印（`leak_causality_diag.py`・約13分）と G2 の印（`gen_signal_families.py --verify`・約25秒）を実装後に取り直す**（`permanent_rules.md` §0-5・§0-5b）。

## 9. 完成の条件（全部 走らせた出力で確かめる・壊し方は CC が書かない）

**★書き方の決まり**＝①1件ごとに「走らせるコマンド」と「合格の線」を書く ②「わざと壊す」は、壊し方の一覧をプログラムの中の表に持たせ、機械が全部 走らせる（監査 P-3）③互いに矛盾する条件を置かない。

| # | 確かめること | コマンド | 合格の線 |
|---|---|---|---|
| K1 | **静的検査＝「引く関数の外で材料を作る所」が無い**＝AST で「`family` と `tf` の両方の鍵を持つ辞書リテラル」を数える | `python3 scripts/priority_rebuild/engine_tuner_gen.py --lint-provenance` | 引く関数（`_mat_drawn`・`_mat_pair_drawn`）の中の1件ずつ以外＝**0件**。自己テストの見本も0件（見本は種を固定した `_mat_drawn` で作る） |
| K2 | `_cat` が消えている | `grep -c "_cat(" scripts/priority_rebuild/engine_tuner_gen.py` | **0** |
| K3 | 印を書く行が「引く関数」の中だけ＝AST で `PARAM_SRC`／`Q_SRC`／`NUM_SRC` を鍵にする辞書リテラルを数える | `--lint-provenance` の2つ目の数 | 引く関数の中の件数と一致（それ以外 **0件**） |
| K4 | **18マスを機械が壊す**＝6つ×3か所の壊し方の表（プログラムの中）を全部 当て、どの瞬間（S1〜S6）のどの関数で止まったかを表で印字する | `--gate-matrix` | **18マス全部が印字され、§5 の表と一致する。**中身＝18マスとも「止まった瞬間（S1〜S6）と関数の名前」。**★2026-08-25（60回目）に表が承認されたので、出口5番の例外（未実装＝合格の線の外）は外した**＝18マスとも同じに測る |
| K5 | 正しい案は通る（止めすぎていない） | `--gate-matrix` の末尾（壊していない案 20本） | **20本とも通る** |
| K6 | **決定 (a') の実測**＝場面の判定を100本 組む | `--selftest`（T24②） | **T24② が ✅**（100本中0本 ではなく、検査を通る束が出る）。`--selftest` 全体で **❌ 0件**（v58 の条件5・20 の矛盾は、この1行に一本化）。★加えて、まとめた順位の中で**同じ種類×時間足が2回 出ない**ことを機械で数えて印字する（0件） |
| K7 | **第2段の再検査**＝`apply_slots` の後に範囲の外の値を入れる壊し方（K4 の表の1行） | `--gate-matrix` | `run_trial_guarded` に届く前に **止まる** |
| K8 | 出口の系統の既定が消えている（やること5） | `--gate-matrix` の5番の出口 | 系統の欄に無い指標を入れると **S2 で止まる**。**★2026-08-25 に実測して合格**（§11） |
| K14 | **走らせる入口の検査（やること8）**＝案を作る関数を通さずに、範囲の外の値を持つ案を `run_trial_guarded` に直に渡す壊し方（K4 の表の1行） | `--gate-matrix` | **止まる**。恒等レシピ（ハッシュ値が一致）だけは通る |
| K9 | **記録からの再判定**＝保存した案の全部の値が印の範囲の中か・範囲が正本と同じか | `--verify-provenance <journal.jsonl>` | **違反 0件**。わざと journal の1つの値を範囲の外に書き換えた控えでは **違反 1件** |
| K10 | 設計書と実物の齟齬 | `python3 scripts/priority_rebuild/verify_design_contract.py --diff .claude/state/acceptance.md` | **齟齬 0件**（実装後に SPEC を `--write` で作り直してから） |
| K11 | 構文 | `python3 -m py_compile scripts/priority_rebuild/engine_tuner_gen.py` | 通る |
| K12 | 機械生成の文書 | `gen_materials.py --verify`／`gen_signal_families.py --verify`（G2 の印） | ✅／印が書き直される |
| K13 | 未来参照の検査（コードを触ったため） | `leak_causality_diag.py`（全検査） | 全部 pass・H2 の印が書き直される |

**★K4 の壊し方の表は、プログラムの中に置く**（CC がその場で選ばない）。18行＝（守るべきこと1〜6）×（入口・場面の判定・出口）。各行＝「どの案の・どの値を・どう壊すか（範囲の外の数字を入れる／カタログに無い名前を入れる／使えない時間足 `9m` を入れる／役割に合わない系統の材料を入れる／型の表に無い形を入れる）」と「止まるはずの瞬間」。**表の中身は設計書のこの節に写さず、実装のプログラムの中の表が正本**＝チャットには `--gate-matrix` の出力をそのまま貼る。

**★時間の見込み**＝`--selftest`・`--gate-matrix`・`--lint-provenance` の実行時間の実測は記録に無い。**実装のときのフロー宣言で、先に小さく測ってから走らせる**（恒久61番・62番）。`leak_causality_diag.py` は記録に「約13分」（`permanent_rules.md` §0-5）。

**★K10 の SPEC**＝下の SPEC は、実装が終わった実物（2026-08-25）から `--write` で作り直したもの（設計書は承認の対象＝C-6・56回目＝**この版は再承認の対象**）。

## 10. 実装の記録（2026-08-25・59回目・全部 走らせた出力）

**設計と実物が違う所（正直に書く・4件）**

| # | 設計の文 | 実物 | なぜ |
|---|---|---|---|
| 1 | やること6＝出口の役割の名前を `exit` にする | **役割の名前は `env` のまま。**枝の系統の欄（印 `LIN_SRC`＝枝・使える系統・表に欄が在ったか）で見る | 実行器は役割を `ROLES = ("env","trigger","sufficiency","location")` に限る（`engine_tuner_exec.py` 133行・実測）＝設計に書いた「受けなければ名前を変えない」の側 |
| 2 | やること7＝`--verify-provenance <journal>` | **`--verify-provenance` は `structures_marked.json`・走行の置き場・`journal.jsonl` のどれでも受ける**（journal を渡すと隣の `structures_marked.json` を読む） | journal は結果の記録で案そのものを持たない＝印つきの案は `structures_marked.json` に残す（`structures.json` は従来どおり印なし＝型の表との照合が読む） |
| 3 | 印の中身＝`{"kind": "range", "lo", "hi"}` | 印の種類は **param（材料・軸ごとの lo/hi）／q（分位・lo/hi）／num・int（数字そのもの）／linear（値＝引いた数×scale）／derived（丸め・割り算で作った値＝式は検査しない）** | 出口の枝の数字は「引いた数を式に通した値」が案に入る（例＝手数料床の倍数×100・割合÷100）。式まで検査できる形（linear）と、できない形（derived）を分けて印に書いた |
| 4 | K1〜K3・K4〜K9 は新しい旗で走らせる | **`--lint-provenance`・`--gate-matrix`・`--verify-provenance` を `--selftest` の中（T25・T26・T27）にも組み込んだ** | 新しい旗は H2・G2 の印の対象＝コードを直すたびに印を取り直さないと走らせられない。`--selftest` は印の対象外＝直すたびに走らせられる |

**走らせた結果（2026-08-25・`--selftest` 307秒・❌ 0件）**

| 条件 | 結果 |
|---|---|
| K1〜K3（T25） | 材料の辞書 0件／印の書き込み 0件／draw_* 0件／_cat 0件／見本の関数 0件＝**合格** |
| K4（T26・18マス） | **18マス全部が期待どおり**＝1〜5番は S2（4要素ゲート）、6番は S3（実行器 G6・G7）。★出口5番＝土台の案の出口が BREAKOUT（表に系統の欄が在る唯一の枝）だったので **S2 で止まった**（「未実装」の印字は、表に欄の無い枝が土台になったときに出る） |
| K5（正しい案） | 20／20 本 通る |
| K6（(a') の実測） | T24②＝100本 組んで検査を通った **31本**（53回目の 92本 から減った。理由＝引いた数字が10回とも禁止3（標本不足）なら その案は作らない、という新しい決まり＝順位→組の対応を乱数に依らせないため）。同じ種類×時間足の重複 0件（T23⑤） |
| K7（第2段の再検査） | S2 で止まる |
| K8 | 表の承認待ち＝測らない（K4 の印字が代わり） |
| K9（T27） | 正しい案3本＝違反0／1本の数字を範囲の外に書き換えた控え＝違反1 |
| K10 | 齟齬 0件（SPEC を実装後に作り直した） |
| K11 | py_compile 通る |
| K12 | `gen_materials --write` → `--verify` ✅（行番号がずれたので作り直した）／G2＝§11 に追記 |
| K13 | **H2＝通った（印を書いた）。**最初の走行（291秒）で 1-c の「生成1〜3（種20260816）」が落ちた＝この道具が `engine_tuner_gen.sample_structure` の案（印つき）を実行器へ直に渡すため、実行器が `_num_src` を未知のフィールドとして拒否した。**★この道具は TARGET の外なので、受け入れ条件ゲートに止められた（正しい止まり）**＝TARGET に足して まこさんの承認（逐語「leak_causality_diag.py の1行を直してよい」「承認した」）をもらってから1行を直した（案を渡す前に `gen.strip_marks` を通す）。**直したあとの走行＝全部 pass・印 624e51062c0d6cec…**（worklog 20260825 の §17）。★**60回目に走らせ直した結果は §11** |
| K14 | 走らせる入口に直に渡した案＝止まる |

**★新しく見つけたこと（`next_step.md` §6 に足す）**＝第2段の値スロットは分位を「正本の範囲の全部」から動かす（`value_slots` の `qg`）＝DC2 の帯（引き金のオシレーターは高分位／低分位）を第2段が外れうる。今回の印は apply_slots がスロットの範囲で書き直すので検査は通る。**帯を第2段でも守るかは別の直し。**

---

## 11. 60回目（2026-08-25）＝やること5 の実装と、そこで見つかった不具合

### 11-1 やった3つ

1. **出口の表に系統の欄を入れた**（`exit_families_rules.json` → `gen_exit_families.py --write`）。`REVERSE_IND`＝オシレーター・トレンド・ボラ・構造位置／`BREAKOUT`＝＋トレンド。**まこさん承認 済**（`exit_families_approved.txt`＝`f5d53842ff40ab09b8fd69161f6eddff  approved 2026-08-25`）。
2. **やること5 を実装した**（`engine_tuner_gen.py` の5か所）＝①直書きの既定6系統を消し、欄が無い枝は `SampleError` ②`assert_exit_roles` は印 `from_table=False` を止める ③ローソクの形の条件に印が付いていなかった穴を塞いだ ④18マスの表から出口5番の例外を外した ⑤未判定の印字を見張りに変えた。
3. **自己テストで見つかった不具合を1件 直した**（下の 11-3 の②）。

### 11-2 走らせた結果（2026-08-25・60回目）

| 条件 | 結果 |
|---|---|
| K4（18マス） | **18マス全部 期待どおり**。出口5番＝**S2 で止まった**（逐語「枝 REVERSE_IND に 系統 出来高 の指標 CMF。枝が使える系統は ['オシレーター', 'トレンド', 'ボラ', '構造・位置']」） |
| K5・K7・K14 | 正しい案 20/20 通る ／ 第2段の書き換え＝S2 ／ 走らせる入口に直に渡す＝止まる |
| K1〜K3（`--lint-provenance`） | 0件（合格） |
| K9（`--verify-provenance`） | 違反0（壊した控えは違反1） |
| K11 | `py_compile` 通る |
| K12 | `gen_signal_families --verify` ✅（G2 の印 e53d71d5…・29.6秒）／`gen_materials`・`gen_composition_rules` は表が変わったので `--write` で作り直して ✅／`gen_exit_families`・`gen_engine_tuner_requirements`・`gen_cat_requirements` は ✅ |
| K13 | **H2 ✅ 全部 pass・印 029ed6f23b98a2b2…**（4分49秒）。★1-c の「生成1」だけ ⚠️ 突き合わせ対象外（下の①が理由・両方 走れないので比較にならない） |
| **`--selftest` 全体** | **❌ 1件（T6）**＝下の①が理由。**それ以外は全部 ✅**（304.8秒） |

### 11-3 見つかった不具合3件（隠さない）

| # | 中身 | 扱い |
|---|---|---|
| **①** | **実行器が、出口の発火条件で「形」を見ていない**＝材料の値と数字を比べるだけ。傾きは「値そのものを本数と比べる」に化け（拒否されずに走る）、交差は値を解けず案ごと拒否、差は2本目が無視される | **`next_step.md` §6 の97番。**まこさん決定（逐語「(う) にして、次のセッションで (あ) をやる」）＝**いま何も足さず、97番を直すまで探索の本走をしない**。★**自己テストの ❌1件（T6）はこれが原因**（拒否された案は journal に書かれず、再開の再利用が1本 減る） |
| **②** | **第2段（値を詰める段）の試行が、4要素ゲートで全部 落ちていた**＝`apply_slots` が印の名前をパスから当てており、ずらす本数（offset）の印に `__int__` を書いていた（正本は `nest_offset_range`）。**59回目の実装の不具合** | **直した**（`_int_range` に出どころの名前を持たせ、`apply_slots` がそれを使う）。実測＝拒否 6/6本 → 0本 |
| **③** | **第2段が窓の本数（corr の n）を動かすと、分位の解決表に鍵が無くて落ちる**（実測 2/6本） | **`next_step.md` §6 の98番**（次に第2段を触るとき） |

### 11-4 ★②を、59回目の自己テストが見逃した理由

**自己テスト（T6）は「第2段で落ちた案の数」を見ていない。**再利用の本数と結果の一致だけを見る。**＝第2段が全滅しても ✅ が出る作りだった。**60回目に、拒否の理由を画面に出して初めて分かった。

---

DESIGN_CONTRACT

```json
{"impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
 "self_check_calls": ["draw_param", "draw_q", "assert_roles", "sample_regime_build", "apply_slots",
                      "assert_provenance", "assert_exit_roles", "_mat_drawn", "_thr_drawn", "_nv",
                      "ranked_groups", "lint_provenance", "gate_matrix", "verify_provenance"]}
```

---

## 作る関数の一覧（★手書きしていません）

**下は `verify_design_contract.py --write` が、実物のコード（設計書 v2 の実装が入った 2026-08-25 の状態）を読んで書き出したものです**（`permanent_rules.md` §0-2 の決まり3）。**実装後に作り直した版＝再承認の対象。**

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
  "load_scene_rules": [],
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
  "sample_regime_build": [
   "SampleError",
   "load_scene_rules",
   "regime_draw_order"
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
  "selftest": [
   "Journal",
   "apply_slots",
   "bh_select",
   "build_qtable",
   "gate_matrix",
   "ladder_min_frac",
   "lint_provenance",
   "load_exit_table",
   "load_limits",
   "load_material_ranking",
   "load_signal_table",
   "material_pool",
   "max_ladder_steps",
   "needed_qkeys",
   "num_in_range",
   "pair_allowed",
   "param_in_range",
   "per_day_gate",
   "pre_run_gate",
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
   "sample_structure",
   "strat_gate",
   "strip_marks",
   "structure_breakdown",
   "synth_df",
   "value_slots",
   "verify_provenance",
   "zero_trade_gate"
  ],
  "pre_run_gate": [],
  "run_main": [
   "hold_bars",
   "load_limits",
   "material_pool",
   "pre_run_gate",
   "resolve_hold_range",
   "run_generation"
  ],
  "main": [
   "gate_matrix",
   "lint_provenance",
   "load_limits",
   "material_pool",
   "run_main",
   "sample_structure",
   "selftest",
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
  "ATTACH_CALLS": 0
 },
 "cli_flags": []
}
```


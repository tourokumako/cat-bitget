<!-- gen_audit_docs request-design kind=impl design_sha256=1249fa04e4ea67ae812f007e62740ea71064e03ee7b2e5b455365afc50393307 src_sha256=c2fd497da236da9f5b7b98e13e8c478b1e9ece8adeab77f19388d4b555612784 body_sha256=92fdeed0e3393df6a787f4f909481fb7c936ef98ffda9074cf659bf7832f6f53 -->
<!-- 項目: メタ -->
日付: 2026-10-06
task: m2c15_param_values_20261006_impl
cp: cp63
題: CP63 — 指標の修正の全体の表の2回目＝パラメータ。M2-C-15（実装の監査）
依頼者: CC（起案者）
監査区分: 実装の監査
監査対象タスク: M2-C-15／設計書 m2c15-param-values-20261006
監査の相手: .claude/state/acceptance.md
売買に触るか: はい

<!-- 項目: 作業場の指示 -->
**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp63_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました。**判断が要る4つ（この工事は何のためか・必読・工事ごとの問い・要望のまとめ）は、CC が工事のフォルダの 監査依頼の手書き（実装の監査）.md に書き、まこさんが OK した文を写しました。ほかは道具が実物から作りました。問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・まこさんの要望が在る工事だけ）と、この工事で確かめてほしいことを問う工事ごとの問い（Q8〜Q12）です。

<!-- 項目: 結論を決める問い -->
- **問い1**＝設計書の実装の指示（17 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。あわせて、この工事で確かめてほしいこと（Q8〜Q12 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けている・工事ごとの問いで設計書と違う所が見つかれば NO。

<!-- 項目: 結論の決め方 -->
- **GO**＝問い1 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の番号と実物の行で示してください。

<!-- 項目: この監査の前提 -->
1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-param-values-20261006/やることの表.md`）に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。
5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。

<!-- 項目: 経緯 -->
1. **この工事は何のためか**＝指標・閾値・パラメータ・時間足の4つを、役割に基づき法則に則って組み合わせて、Entry・Exit やレジーム判定の条件を作れる状態にする（6項目）。この工事は6項目の3番（パラメータが、範囲から探されている）のために、材料の名前の一覧を教科書の最初の値（スキャル∪デイトレ）＋残す名前（V9・採用中の戦略・確認のレシピ）にし、最後のチューニングで探す範囲（修正対応表の範囲・名前の軸）を設定に書く。名前の形は変えず、指標の数を増やさない（材料は 576列 → 476列）
   一覧と範囲の値は、CC が書かず、道具（r3_draft_build.py）が修正対応表から写す。CC が決めた所（名前の軸と資料の軸の対応 18種・ROC の範囲を 9〜24 に広げる・MACD の軸の重なりを工事2 に回す）は、設計書の 3-2 に全部 出し、まこさんが OK した
2. **この工事は何か**＝指標の修正の全体の表の2回目（パラメータ）です。まこさん決定「A」のとおり、材料の名前の一覧を、教科書の最初の値（スキャル∪デイトレ）に入れ替え、最後のチューニングで探す範囲を設定に書きます。中身は5つです。①P-1＝観察の道具の設定（observe_config.json）に、指標ごとの一覧（80種）を道具が書く。一覧＝最初の値（名前の軸に当たる軸）＋残す名前（V9 19本・採用中の戦略と確認のレシピ 9本）。材料の一覧を作る関数（build_catalog）は、一覧に在る種類を、ほかの指標の期間の一覧を使わずに作る。材料は 576列 → 476列 になる（消える 153本・増える 53本・両方に在る 423本の値は変わらない）。名前に出ない軸がある 38種の最初の値は、列の計算を変えずに別の欄へ書く。②P-2＝探す範囲（search_limits.json の material_param_ranges）に、修正対応表の範囲（名前の軸・104種）を道具が書く。同じ事実を書く説明5か所をそろえる。③P-3＝範囲の端の値で作った列が、ライブラリが黙って既定に戻したものでないかを写しで測った（当たり 0件）。④P-4＝範囲が決まらない・範囲が1点のまま・資料に行が無い 33種を、値を埋めずに設定の注記に並べる。⑤P-5＝29種のうち26種は前の工事の名前に出さない引数で受け取れている。残り3種は直さない（3-1）。★数の訂正＝決めていただいたときの案（逐語のファイル）の「45本 増えて130本 減ります」は、名前に出ない軸がある種類の名前の軸を数えていなかった。その扱い（記録の返信 c717283a の「A のときの扱い」）を入れて道具が数え直すと、増える 53本・消える 153本になる。（やることの番号 M2-C-15）
   **この工事の位置**＝全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝材料を直す（監査 CP60 の修正・法則どおりの帯の部品・S1 の部品） → この工事

<!-- 項目: 着手前必読 -->
**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `.claude/state/acceptance.md` — 監査の相手（設計書・プログラムが作った）
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-20261006.01.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-20261006.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
4. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:m2c15-param-values-20261006 の行）
5. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-param-values-20261006/やることの表.md` — 設計書の元（やることの表）＝修正の指示を書く先
6. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — 目標（全月 net ≥ $1,900）と全体戦略、ハード制約（§4.6＝H2 未来参照なし・H6 値段の高さで値が変わらない ほか）。計算式は変えていないが、材料の列の入れ替わりが制約に触れないかを照らす
7. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-103） — engine_tuner の目的と、作ってはいけないもの（乱数・探す値を CC が点の一覧で限定するもの）。一覧は最初に組む値で、探す値は範囲、という線引きを照らす
8. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:95-146） — M2 が M1〜M6 のどこに当たり、何ができたら終わりか
9. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:3-46・:995-1040・:1173-1183） — M2 で作っている物と、この工事（M2-C-15＝材料を直す）の行と中身。この工事は M2-C-15 のうち、全体の表の2回目（パラメータ）＝監査 CP60 の修正64 ほかの範囲の直し。帯の部品・S1 の部品は3回目
10. `.claude/state/acceptance.md`（全文） — 承認済みの設計書（実装の指示17件・完成の条件3行は ✅済・承認のプログラムが測った）
11. `.claude/state/indicator_params_by_strategy.json`（全文）・`.claude/state/indicator_fix_plan.json`（RSI・ADX・CCI・ROC・MACD の行） — 一覧と範囲の出どころ（修正対応表）。写した値が資料と同じか（Q8・Q9）
12. `SDK/scripts/priority_rebuild/observe_diag.py`（:1319-1345・:1675-1700・:7011-7125） — build_catalog の指標ごとの一覧の読み方（_per・addf・_unused・_gone）と、軽い口 selftest_catalog に足した番人⑪〜⑬
13. `SDK/scripts/priority_rebuild/observe_config.json`（:160-300） — 足した欄（material_params・material_keep・material_first_hidden・_material_params_pending）と、重複を外す一覧 drop_columns
14. `SDK/scripts/priority_rebuild/recipes/search_limits.json`（:44-150） — 書いた範囲 material_param_ranges（104種）と注記
15. `SDK/scripts/priority_rebuild/engine_tuner_gen.py`（:231-300・:450-500） — 範囲を作る関数 material_ranges（設定の範囲が優先）と、段の候補を範囲で絞る _group_usable_col（Q11）
16. `SDK/scripts/priority_rebuild/engine_tuner_exec.py`（:733-745） — 範囲の外のパラメータを止める _check_param_range。直したのは説明の文（736行）だけで、動きは変えていない
17. `SDK/scripts/priority_rebuild/gen_materials.py`（:1575-1590） — 材料の文書に書く、範囲の置き場所の文（1583行）を直した。★CC の自己申告＝すぐ上の 1581行の例の文「RSI は 7〜21 の整数 全部。設定ファイルに並んでいるのは 7・9・14・21 の4つだけ」は、この工事の後は事実と違う（RSI の範囲は 2〜21・一覧は 5・7・9・14・21）。設計書の直しに入れていなかった＝同じ事実を書く場所を揃え漏れた。この工事では直していない
18. `SDK/.claude/ratchet/signal_families.md`（全文） — 作り直して再承認された型の表（部品 476種・禁止1 128種・禁止3 366組）。前の版（576種・141種・514組）との差
19. `SDK/.claude/ratchet/m2_stage_candidates.json`（全文） — 段の候補が種類の名前で指す材料（19種）。直した後のカタログで名前が何本 残るか（Q11）
20. `.claude/breaks/b137_material_params_ignored.sh` — 壊すプログラム。build_catalog が指標ごとの一覧を読まないと、カタログを作る所が止まるか（Q10）
21. `.claude/breaks/b138_keep_name_dropped.sh` — 壊すプログラム。一覧から ROC24 を外すと、残す名前の番人⑫が落ちるか（Q10）
22. `.claude/breaks/b139_range_excludes_keep.sh` — 壊すプログラム。ROC の範囲の上限を 14 に戻すと、範囲の番人⑬が落ちるか（Q10）
23. `.claude/state/reviews/acceptance.review.md`（全文） — CC の見直し表（止める理由0件）
24. `.claude/state/indicator_review/r3_draft_build.py`（全文） — 一覧・範囲・指示を作った道具（AXIS_MAP・v9_keep・adopted_keep・compute・PROBE）。写した値の作り方そのもの（Q8・Q9）
25. `.claude/state/session_worklog_20261006.md`（:168-223） — この工事の照らし・案・当て方・止まった所・走らせた結果（§18〜§23）。仮当てが打ち切られて本物が書き替わったまま残った件（§21・Q12 の元）
26. `.claude/hooks/require_design_check_before_approval.py`（:600-645）・`.claude/tools/gen_acceptance.py`（:676-707） — このセッションで直した承認の前の検査（T6 だけの落ちを止めない）と、設計書の関数の一覧を当てた後の中身から作る直し（Q12）

<!-- 項目: 大目的の注記 -->
⚠️ 本監査スコープ = 設計書 `m2c15-param-values-20261006` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `m2c15-param-values-20261006` の中身です。

<!-- 項目: 事実データ 名前=設計書の実装の指示の一覧（4-20・当てる道具が当てる相手） -->
| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1328行（add・P-1＝build_catalog が、指標ごとの一覧に在る種類を、その一覧の組だけで作る） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1331行（addf・P-1＝build_catalog が、指標ごとの一覧に在る種類を、その一覧の組だけで作る） | 直した後の文字 |
| 3 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1669行（build_catalog・P-1＝指標ごとの一覧の種類が、カタログを作る所で1度も出てこなければ止める） | 直した後の文字 |
| 4 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1676行（build_catalog・P-1＝重複を外す一覧の残す側が、指標ごとの一覧で外れた名前のときは止めない） | 直した後の文字 |
| 5 | `SDK/scripts/priority_rebuild/observe_diag.py` | 7074行（selftest_catalog・軽い口 selftest_catalog に、この工事の番人（⑪ 一覧どおり・⑫ 残す名前・⑬ 範囲が含む）を足す） | 直した後の文字 |
| 6 | `SDK/scripts/priority_rebuild/observe_config.json` | 164〜166行（設定・P-1・P-4＝指標ごとの一覧・残す名前・名前に出ない軸の最初の値・値を埋めない種類を、プログラムが修正対応表から写して書く） | 直した後の文字 |
| 7 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 44〜45行（設定・P-2＝修正対応表の範囲（名前の軸）を、プログラムが写して書く。注記を事実どおりに直す） | 直した後の文字 |
| 8 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 242行（material_ranges・P-2＝範囲の置き場所の説明を、事実（修正対応表の範囲をプログラムが写した）にそろえる） | 直した後の文字 |
| 9 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 244行（material_ranges・P-2＝範囲の置き場所の説明を、事実（修正対応表の範囲をプログラムが写した）にそろえる） | 直した後の文字 |
| 10 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 248行（material_ranges・P-2＝範囲の置き場所の説明を、事実（修正対応表の範囲をプログラムが写した）にそろえる） | 直した後の文字 |
| 11 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 254〜255行（material_ranges・P-2＝範囲の置き場所の説明を、事実（修正対応表の範囲をプログラムが写した）にそろえる） | 直した後の文字 |
| 12 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 293行（material_ranges・P-2＝範囲の置き場所の説明を、事実（修正対応表の範囲をプログラムが写した）にそろえる） | 直した後の文字 |
| 13 | `SDK/scripts/priority_rebuild/engine_tuner_exec.py` | 736行（_check_param_range・P-2＝範囲の正本の説明を、事実にそろえる） | 直した後の文字 |
| 14 | `SDK/scripts/priority_rebuild/gen_materials.py` | 1583行（render_md・P-2＝材料の文書（materials.md）に書く範囲の置き場所の文を、事実にそろえる） | 直した後の文字 |
| 15 | `.claude/breaks/b137_material_params_ignored.sh` | なし（新しいファイル） | 直した後の文字 |
| 16 | `.claude/breaks/b138_keep_name_dropped.sh` | なし（新しいファイル） | 直した後の文字 |
| 17 | `.claude/breaks/b139_range_excludes_keep.sh` | なし（新しいファイル） | 直した後の文字 |

<!-- 項目: 事実データ 名前=当てた記録（applied_fixes.json の名前 design:m2c15-param-values-20261006） -->
| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T21:49:17 |
| 2 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T21:49:17 |
| 3 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T21:49:17 |
| 4 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T21:49:17 |
| 5 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T21:49:17 |
| 6 | `SDK/scripts/priority_rebuild/observe_config.json` | 当てた | 2026-10-06T21:49:17 |
| 7 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-06T21:49:17 |
| 8 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-06T21:49:17 |
| 9 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-06T21:49:17 |
| 10 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-06T21:49:17 |
| 11 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-06T21:49:17 |
| 12 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-06T21:49:17 |
| 13 | `SDK/scripts/priority_rebuild/engine_tuner_exec.py` | 当てた | 2026-10-06T21:49:17 |
| 14 | `SDK/scripts/priority_rebuild/gen_materials.py` | 当てた | 2026-10-06T21:49:17 |
| 15 | `.claude/breaks/b137_material_params_ignored.sh` | 当てた | 2026-10-06T21:49:17 |
| 16 | `.claude/breaks/b138_keep_name_dropped.sh` | 当てた | 2026-10-06T21:49:17 |
| 17 | `.claude/breaks/b139_range_excludes_keep.sh` | 当てた | 2026-10-06T21:49:17 |

<!-- 項目: 事実データ 名前=必読に要るファイル（道具が設計書と実装から拾った） -->
| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15） | 入れる |
| `SDK/scripts/priority_rebuild/engine_tuner_exec.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/gen_materials.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_config.json` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b137_material_params_ignored.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b138_keep_name_dropped.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b139_range_excludes_keep.sh` | 直す相手（TARGET） | 入れる |

<!-- 項目: 監査対象 -->
- Q1：実装の指示を当てた結果が、実装の後と1文字も同じか
- Q2：実装の指示のどれにも当たらない行（設計書に無い変更）が無いか
- Q3：当てた記録が、実装の指示の全部と1件ずつ合うか
- Q4：承認した版の設計書どうしで、実装の指示が同じか
- Q5：実装の指示が、やることの表の要件を全部 満たすか
- Q6：完成の条件が、実装の後に本当に成り立つか
- Q8：指標ごとの一覧（P-1）は、修正対応表の最初の値と残す名前を、漏れなく・余計なく写しているか
- Q9：範囲（P-2）は、修正対応表の範囲を名前の軸に正しく当てているか。CC が決めた対応 18種は正しいか
- Q10：完成の条件3行は、設計書の直し（P-1・P-2）を全部 覆っているか。壊すプログラム3本は、直しを外したときだけ落ちるか
- Q11：名前が入れ替わったことで、ほかの仕組みが黙って変わった所は無いか
- Q12：このセッションで直した承認の仕組み2つと、仮当てが打ち切られた件の影響

<!-- 項目: 監査対象外 -->
- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- 名前に出さない引数の範囲を書き、探す側が範囲から渡す仕組み（KST の本数・HWMA の係数・PSAR と CKSP の値・傾きの比べる本数 k ほか）（範囲の設定は名前の軸しか持てない（範囲を作る関数が、軸の数が名前と違えば止める）。探す側をつなぐのは工事2）
- 名前に出ない軸の最初の値を、列の計算に渡すこと（列の計算を変えずに別の欄へ書く。渡すのは工事2）
- P-5 の残り3種を直すこと（THERMO%・swing高値距離・swing安値距離）（THERMO% は、ライブラリの本数が平らにする線（THERMO比 の分母）にだけ効き、THERMO% の列には効かない＝パラメータが無い（observe_diag.py の _th・pandas_ta_classic の thermo.py:14〜24）。swing の2種は、列が全部 close vs n本高値% と同じとして省いてあり（重複を外す一覧）、教科書のパラメータ（前後 N 本）は、すでに在る fractal高値距離%(k) の k と同じ定義（indicator_params_review の元の指標の欄））
- 列の計算に使われない軸を直すこと（S-Rタッチ1時間ATR の倍率と ATR の本数・PVO と TSI の線のシグナルの本数）（前から在る作り。この工事の直しが原因ではない（写しで、2種類の値動きのどちらでも列が変わらないと測った）。直し方（名前から外すか・計算に届かせるか）は、作りの違いの仕分け（K-7）か帯の部品（B-1）で決める）
- P-5 の一文の「参照の計算（indicator_reference_diag.py の _stc_parts・_slope など）も同じパラメータを受ける形にする」（名前に出さない引数を受け取る形は前の工事で入れたが、参照の計算は、何も渡さないときの列だけを照らす（前の工事の やらないこと Y-2「別の値を渡した列を、参照表で照らすこと」）。探す側が別の値を渡し始める工事2 で一緒に直す）
- P-2 の一文のうち、名前に出ない軸の範囲（監査 CP60 の修正64 の PSAR・CKSP・ALMA の σ と offset、HWMA の係数3つ＝0〜1、傾きの比べる本数 k）（名前の形を変えない（まこさん「指標名に…値を固定で入れて…やめてほしい」）ので、どれも名前に出ない軸になった。範囲の設定は名前の軸しか持てない＝工事2。ALMA の本数（名前の軸）は、この工事で範囲を書く）
- P-3 の一文のきっかけの HWMA（hwma.py:36＝0 以下を黙って既定に戻す）の照らし（HWMA の係数は名前に出ない軸なので、この工事の範囲に入らない。範囲を書く工事2 で、同じ照らし（端の値とまん中の値の列を比べる）をかける）
- G-1 の一文のうち、新しく足す材料（K-3 の教科書の版・B-1 の帯の部品・S-1 の部品）を「使う」にすることと、DPO の対応（TA_CLASS_MAP）（その材料を足すのは3回目。この工事の G-1 は、表の作り直しと再承認、段の候補と出口の元データの名前の照らし）
- 教科書の版を足す直し（K-3）・帯の部品（B-1）・S1 の部品（S-1）・作りの違いの仕分け（K-7）・検査の直し（K-4）・役割と閾値（R-1・T-1）（3回目・4回目）
- オフの指標（使わない116種）を直すこと（今は対応しない）
- 成績表（material_ranking.json）の作り直し（M2-D-8 で、まこさんの OK の後に走らせる）
- RSI7・RSI9・RSI14・RSI21 と、V9 が使う指標の名前を変えること（そのままでよい。この工事では、残す名前に入れて番人で守る）

<!-- 項目: 問い 番号=Q1 優先度=A 理由=違えば、実装は設計書のとおりに作られていない 名前=実装の指示を当てた結果が、実装の後と1文字も同じか -->
実装の前（HEAD の commit 0cb31ab（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる））の対象のファイル（`.claude/breaks/b137_material_params_ignored.sh`・`.claude/breaks/b138_keep_name_dropped.sh`・`.claude/breaks/b139_range_excludes_keep.sh`・`SDK/scripts/priority_rebuild/engine_tuner_exec.py`・`SDK/scripts/priority_rebuild/engine_tuner_gen.py`・`SDK/scripts/priority_rebuild/gen_materials.py`・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/observe_diag.py`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）に、設計書 4-20 の実装の指示（17 件）を番号の順に当てた結果が、実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる））と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

<!-- 項目: 問い 番号=Q2 優先度=A 理由=在れば、設計書に無い変更が実装に混ざっている 名前=実装の指示のどれにも当たらない行（設計書に無い変更）が無いか -->
実装の前（HEAD の commit 0cb31ab（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる））と実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる））の差分（`.claude/breaks/b137_material_params_ignored.sh`・`.claude/breaks/b138_keep_name_dropped.sh`・`.claude/breaks/b139_range_excludes_keep.sh`・`SDK/scripts/priority_rebuild/engine_tuner_exec.py`・`SDK/scripts/priority_rebuild/engine_tuner_gen.py`・`SDK/scripts/priority_rebuild/gen_materials.py`・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/observe_diag.py`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

<!-- 項目: 問い 番号=Q3 優先度=A 理由=合わなければ、どの件を道具が当てたかを後から確かめられない 名前=当てた記録が、実装の指示の全部と1件ずつ合うか -->
当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2c15-param-values-20261006`）が、実装の指示の 17 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

<!-- 項目: 問い 番号=Q4 優先度=B 理由=当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない 名前=承認した版の設計書どうしで、実装の指示が同じか -->
承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-20261006.01.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-20261006.md`）と、いまの設計書の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

<!-- 項目: 問い 番号=Q5 優先度=B 理由=要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない 名前=実装の指示が、やることの表の要件を全部 満たすか -->
実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-param-values-20261006/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

<!-- 項目: 問い 番号=Q6 優先度=B 理由=成り立たなければ、承認のときの「済」が根拠にならない 名前=完成の条件が、実装の後に本当に成り立つか -->
設計書の完成の条件（3 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog`

<!-- 項目: 問い 番号=Q8 優先度=A 理由=一覧に教科書の値が抜けると、その値の列が材料に無くなり、engine_tuner が戦略に合う値から組み始められない。余計な名前が入ると、指標の数を増やさないという決まりに反する 名前=指標ごとの一覧（P-1）は、修正対応表の最初の値と残す名前を、漏れなく・余計なく写しているか -->
observe_config.json の material_params（80種）を、indicator_params_by_strategy.json の「最初の値（スキャル）」「最初の値（デイトレ）」と1種ずつ照らしてください。名前に出ない軸がある種類は、r3_draft_build.py の AXIS_MAP（18種）で名前の軸だけを取り出しています（Q9）。残す名前 material_keep（V9 19本・採用中の戦略と確認のレシピ 9本）は、v9_logic.md の §1.2 の表の設定の数字（1つ目の数字だけで照らしている＝r3_draft_build.py の v9_keep）と、engine_tuner_exec.RUNTIME_ALIAS・recipes の family と param から道具が読みました。この読み方で、V9 や採用中の戦略が使う名前を取りこぼしていないかを見てください（例＝2つ目の数字で区別する名前）。両方に在る 423本の列が当てる前と同じか（設計書の 4-0 の③）を、写しの作業場で当てる前の版（git の 0cb31ab）と比べてください。

<!-- 項目: 問い 番号=Q9 優先度=A 理由=名前の軸と資料の軸の当て方を誤ると、別のパラメータの範囲で探すことになる（例＝基準線の期間の範囲で転換線を探す） 名前=範囲（P-2）は、修正対応表の範囲を名前の軸に正しく当てているか。CC が決めた対応 18種は正しいか -->
search_limits.json の material_param_ranges（104種）を、修正対応表の範囲と1種ずつ照らしてください。設計書の 4-0 の⑤の表（18種＝転換線・基準線・KSTシグナル・KAMA傾き%・StochRSI%K/D・Keltner上/下・ALMA・JMA・KAMA%・MCGD・SSF・EMA傾き・Stoch%K/D・T3・VIDYA）の「名前の軸に当てた資料の軸」が、observe_diag.py の計算式の引数と、資料の元の指標の定義で合っているかを見てください（3-2 の1行目＝まこさんが「監査で確かめる」として OK した所）。ROC の範囲を 9〜24 に広げたこと（3-2 の2行目）と、MACD の3種の軸の重なり（3〜12 と 10〜26・3-2 の3行目＝工事2 に回した）が、設計書のとおりかも見てください。

<!-- 項目: 問い 番号=Q10 優先度=A 理由=覆っていない直し・落ちない壊し方が在ると、一覧を読まない形・残す名前が消える形・範囲が残す名前を含まない形が黙って戻る 名前=完成の条件3行は、設計書の直し（P-1・P-2）を全部 覆っているか。壊すプログラム3本は、直しを外したときだけ落ちるか -->
壊すプログラム3本を写しの作業場で走らせ、宣言した文（EXPECT_MSG）で落ちるか、壊す対象の行がちょうど1か所かを見てください。番人⑬は、設定の範囲が無い種類を飛ばします（observe_diag.py の selftest_catalog の `if not _ax13: continue`）。この飛ばしで、範囲を書くべきなのに書いていない種類を見逃さないかを見てください。番人⑪は、一覧の種類の名前がカタログとちょうど同じかを見ますが、一覧に無い種類（RCI・前期間pivot ほか）が今までどおり作られているかは見ません。重複を外す一覧の「残す側」が一覧で外れたとき止めない直し（実装4・_gone）で、書き間違いによる取りこぼしを止められなくなっていないかも見てください。

<!-- 項目: 問い 番号=Q11 優先度=B 理由=材料の名前を頼りにしている仕組みは、名前が消えると、止まらずに静かに候補から外す 名前=名前が入れ替わったことで、ほかの仕組みが黙って変わった所は無いか -->
段の候補（m2_stage_candidates.json）は種類の名前で19種を指し、直した後のカタログには、種類ごとに1本以上の名前が在ります（CC が r3_name_refs.py で数えた＝CHOP は CHOP14 の1本・BB%b は1本・close vs SMA は1本）。段の候補は成績表の順位から作り、列の数字が範囲の中かで絞ります（engine_tuner_gen.py の _group_usable_col）。成績表は作り直していないので、消えた名前（例＝2026-10-03 の段2a の1位 CHOP7）が候補にどう扱われるか、範囲の外の列（ROC3・ROC6 ほか）が設計書の 4-13 の3のとおり外れるかを、実物で確かめてください。型の表の禁止3（標本不足・gen_signal_families.py の _window_days:93）は名前の数字から窓を計算するので、514組から 366組に減りました。この減り方が、名前の入れ替わりだけで説明できるかを見てください。★出口の型の表の元データ（exit_families_rules.json）の説明の文に、型の表の古い数（641・649・657・666・679・688・693・698 行）が残っています。この工事の前から古いものですが、出口の表を組む道具がこの文を数として読んでいないかを見てください。

<!-- 項目: 問い 番号=Q12 優先度=B 理由=承認の仕組みは、この工事の後も全部の工事で使う。直しが別の落ちを見逃せば、以後の承認で穴が通る 名前=このセッションで直した承認の仕組み2つと、仮当てが打ち切られた件の影響 -->
①require_design_check_before_approval.py の A12（624〜627行）は、gen_materials.py の自己テストで落ちた番人が T6（素の状態で --verify が鳴っている）だけのときは止めません。この判定で、T6 以外の落ちを見逃す形が無いかを見てください。②gen_acceptance.py の build_spec（676〜707行）は、設計書の関数の一覧を、4-20 の指示を当てた後の中身から作ります。「直した後の文字がもう1か所在る指示は当て終わり」とみなす判定が、別の場所に同じ文字が在るときに誤って当て終わりとみる形が無いかを見てください。★CC の自己申告＝設計書を作る道具を走らせた直後に、hook（show_design_check_after_write.sh・時間の上限 120秒）が承認の前の検査を走らせ、その中の仮当て（約4分半）が本物のファイル6本を書き替えた後に打ち切られ、承認の前なのに本物が工事の中身のまま残りました（21:16〜21:2x・worklog §21）。CC は控えのハッシュ値がコミットの中身と同じことを確かめてから、hook 自身の戻す処理で戻しました。この hook の直し方は、まこさんがまだ決めていません。当てる前の本物が、この件の後に本当にコミットの中身へ戻っていたか（当てる道具の --dry が17件とも「当たる」と出したのは、その証拠になるか）を見てください。★CC の自己申告（2つ目）＝当てた後に `gen_acceptance.py --work m2c15-param-values-20261006 --verify` を走らせると、囲み MATERIALS（設計書の 2-2・承認の前の時点の「material_param_ranges は空」）と CODEREF（7-7・定義の行）が「正本と食い違う」と出ます。どちらも当てた後に実物が変わったためで、囲みの外の文は作り直しても同じでした。設計書は作り直していません（作り直すと承認の打ち直しが要り、上の hook の穴も起きるため）。この2つの食い違いが、当てた後に起きて当然のものだけか（ほかの食い違いを隠していないか）を見てください。


<!-- 項目: 自己申告 -->
**承認の後に設計書を作り直した**＝前の版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-20261006.01.md` と いまの版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-20261006.md` の違い＝囲みの外で 6 行（実装の指示の囲み ACC_IMPL は同じ）

<!-- 項目: 自己申告 -->
**この工事の外の作業中の変更**＝`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_design_check_before_approval.py`・`.claude/hooks/require_request_understood.sh`・`.claude/tools/gen_acceptance.py`・`.claude/tools/gen_audit_docs.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）

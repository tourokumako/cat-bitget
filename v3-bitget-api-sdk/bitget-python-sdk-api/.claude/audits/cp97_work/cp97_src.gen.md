<!-- gen_audit_docs request-design kind=impl work=m2c15-catalog-redirect-20261101 design_sha256=b3bc8c29388fae099081f3753c01cb6f46d083611eaaa8a7a25f19e82f27479f src_sha256=c99b859edbbf98c79a95e167f359f47c168b7e7f31a2ad6ab74cbfbe5ef7fe9d body_sha256=aceef0de3717352f901121810f89a4cf62397deb1ade7ed3a33c7ae2ab3f00b6 -->
<!-- 項目: メタ -->
日付: 2026-11-01
task: m2c15_catalog_redirect_20261101_impl
cp: cp97
題: CP97 — 161-2＝列を作る所 build_catalog を、読む口の列を作る組から列を作る形にし、列の名前・並び・値が直す前と同じかを比べる。ToDo の161番・M2-C-15（実装の監査）
依頼者: CC（起案者）
監査の種類: 実装の監査
監査対象タスク: M2-C-15／設計書 m2c15-catalog-redirect-20261101
監査の相手: .claude/state/acceptance.md
売買に触るか: はい
直す相手: `.claude/breaks/b222_catalog_drops_last_set.sh`・`.claude/breaks/b223_catalog_reads_old_key.sh`・`.claude/breaks/b224_reader_sets_no_reg.sh`・`.claude/breaks/b225_draft_source_is_catalog.sh`・`.claude/breaks/b226_h2_watch_no_indicators.sh`・`.claude/breaks/b227_materials_keys_from_catalog.sh`・`.claude/state/indicator_review/gen_indicators_draft.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py`

<!-- 項目: 作業場の指示 -->
写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp97_work/` に作る。必要なファイルは自分で開き、写しで走らせて確かめる。

<!-- 項目: 修正をどこに書くか -->
実装が設計書と違う所の修正は、その実装のファイルに書いてください。修正を当てるプログラムが、その修正を当てます。
ただし、修正を当てるプログラムは、.claude/hooks と .claude/tools と .claude/breaks のファイルには当てません。そのファイルの修正は、CC が書きます。
設計書の誤りの修正は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-catalog-redirect-20261101/やることの表.md`）に書いてください。設計書はプログラムが作るので、設計書に直接書けません。

<!-- 項目: 目的と経緯 -->
1. **この工事は何のためか**：この工事は、列を作る所（observe_diag.py の build_catalog）を、読む口 indicators.py が返す「列を作る組」から列を作る形にしました。
   - 直す前の build_catalog は、設定ファイル observe_config.json の古い鍵（約40個）と material_params から列を作っていました。そのため、indicators.json の列を作る組を直しても、列に届きませんでした。
   - 目的は、集約の要件定義書の R6 のうち、「記録から作る・古い鍵を読まない」を満たすことです。満たす要件は、指標を指標一覧（material）からだけ呼び出すこと（要件定義の6番）と、誤りを1か所で直せば全部のロジックに届くこと（7番）です。
   - 列の名前・並び・値は、直す前と変えません。代表の値と範囲から列を作る形にするのは、後の工事（171番と M2-E-8）です。
   - 設計書の監査 CP96 の修正17件と、同じ事実をそろえる5か所を、全部入れました。
2. **この工事は何か**：この工事の中身は、設計書の「§1 概要」に書いてあります。実装の指示の一覧は、事実データの表に載せました。やることの番号は、M2-C-15です。
   **この工事の位置**：目標からこの工事までのつながりは、次のとおりです。全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝指標の構造の工事（ゴール1〜3）。指標の情報を1つのデータに集め、形を要件に合わせ（worklog 20261030 §17-1 の A〜C）、法則を1つのデータにまとめる（同 D）。全体のマイルストーンでは①の中で行う → この工事
3. **この工事が結ぶ要件**：M2-C-15＝この工事が満たす要件は、要件定義の次の3つです。3番：指標・閾値・パラメータ・時間足が、それぞれの役割に沿って使われ、閾値とパラメータが範囲から探されていること。4番と5番：最初の段階では、閾値とパラメータを、戦略ごとの代表の固定値にして探すこと。6番：指標は1か所から呼び出すこと。教科書と法則の誤りは、1か所を直せば全部に届くこと。（出どころ＝やることリスト m2_todo.json の「結ぶ要件」）
4. **経緯**：この監査に至るまでの経緯は、次のとおりです。
   - 前の監査（設計書の監査 CP96・2026-11-01）の結論は、GO でした。件数の行は Critical 0・Major 2・Minor 13・Process 1 です。修正の指示は17件です。Minor の見出しの下の修正は14件で、件数の行と1件違います。
   - Major の2件は、同じ事実を指します。G2 の検査済みの記録（g2_pass.json）に、indicators.json が入らないことです。そのため、indicators.json の見張りは H2 だけです。G2 の対象に足すのは171番です。
   - まこさんは、修正17件を全部直し、同じ事実を書く5か所もそろえると決めました（2026-11-01）。
   - この決定で、実装は2か所変わりました。1つ目に、build_catalog に止める条件が2つ増えました（修正13・14）。2つ目に、4-4 の2 に確かめが2つ増えました（修正16）。
   - その前の工事（161-1）の実装の監査 CP95 では、Critical が3件ありました。そのうち2件は、CC が --verify の後にファイルを消し、走らせ直さずに commit したことが原因でした。同じ誤りが無いかを、Q8 で見てください。
   - 実装の後に、CC は設計書と違う手順を取りました（Q8 の自己申告1・3・4）。そのうち、一覧を作り直す段と、一覧を作る道具の直しは、--rewrite が読む行に関わります。
   - 承認の記録には、壊すプログラム6本の終了コードがありません。CC は、依頼書を作る前に1回だけ走らせました（Q9）。

<!-- 項目: 着手前必読 -->
**パスは、リポジトリの根（`cat-bitget/`）からの相対です。**`SDK` は、`v3-bitget-api-sdk/bitget-python-sdk-api` の略です。

1. `.claude/state/acceptance.md` — 監査の相手の設計書です。プログラムが作りました。
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-catalog-redirect-20261101.md`（全文） — まこさんが承認した版の設計書の控えです。どの版の 4-20 で当てたかは、Q4 で照らします。このファイルは、承認された設計書の控えです。やらないことは 3-1（:297-314）、処理の流れは 4-4（:384-395）、出る結果の姿は 4-12（:480-488）、止まる条件は 4-5（:490-504）、影響範囲は 4-13（:559-576）、実装の指示22件は 4-20（:588-1277）、決めたことは §5（:1278-1290）、完成の条件6行は 7-6（:1447-1466）に在ります。
3. `SDK/.claude/audits/applied_fixes.json` — 当てる道具が書いた、当てた記録です。この工事の行の名前は design:m2c15-catalog-redirect-20261101 です。
4. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-catalog-redirect-20261101/やることの表.md` — 設計書の元（やることの表）です。監査人は、修正の指示をこのファイルに書きます。
5. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — このファイルには、目標と全体戦略とハード制約が書いてあります。目標は、全月 net ≥ $1,900 です。
6. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-232） — このファイルには、engine_tuner の目的と、探し方の要件と、作ってはいけない物が書いてあります。
7. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:130-152） — このファイルには、M2 が M1〜M6 のどこに当たるかが書いてあります。
8. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:81-109） — このファイルには、M2 で作っている物が書いてあります。この工事は、M2-C-15（指標の工事）の1つです。
9. `SDK/.claude/ratchet/acceptance_archive/verbatim/m2c15-catalog-redirect-20261101/impl_4-20_20261101.json`（全文） — このファイルには、実装の指示22件の中身が在ります。設計書の 4-20 と同じ物です（Q8・Q9）。
10. `SDK/scripts/priority_rebuild/observe_diag.py`（:1792-1835・:7847-7855・:7971-7995） — build_catalog と写す元の関数 _catalog_from_config の頭、カタログの自己テストの照らし⑮⑯です（Q8）。
11. `SDK/scripts/priority_rebuild/indicators/indicators.py`（:21-30・:335-375） — 読む口の column_sets です。組ごとに計算の登録の名前を返します（Q8）。
12. `.claude/state/indicator_review/gen_indicators_draft.py`（:16・:128・:547-610・:812-850・:979-1000・:1720-1730） — 写すプログラムの、写す元と要素の定義表を合わせる所と、構文の木の照らしです（Q8）。
13. `SDK/scripts/priority_rebuild/leak_causality_diag.py`（:244-266） — H2 の検査済みの記録の対象の一覧です（Q8）。
14. `SDK/scripts/priority_rebuild/gen_materials.py`（:454-481・:2478-2485） — materials.md の場所1 を数える口と、その自己テストです（Q8）。
15. `SDK/scripts/priority_rebuild/gen_signal_families.py`（:526・:567・:909-916・:964-972） — G2 の検査です。修正1 の「indicators.json は対象に入らない」の根拠です（Q10）。
16. `SDK/scripts/priority_rebuild/indicators/indicators.json`（:3・:283-303・:795-815・:3371-3400・:38413-38440・:99115-99215） — 4-4 の3 で写すプログラムが書き替えた相手です。要素の定義表の ②-12・④-9、記録の ALMA傾き%・RSI、部品の記録の帯VA の行です（Q8）。
17. `.claude/state/indicator_review/col_snapshot.py`（全文） — 列の比べのプログラムです（Q8 の自己申告3）。
18. `.claude/state/indicator_review/col_snapshot/before_20261024.log`（全文） — 直す前の列の控えを作ったときの記録です（Q8）。
19. `.claude/state/indicator_review/gen_fix_inventory.py`（:111-149・:296・:339-340） — 一覧を作る道具の、行番号を読み替える所です（Q8 の自己申告1）。
20. `.claude/state/indicator_review/fix_inventory_20261024.md`（:1-5・:230・:430） — 作り直した直す相手の一覧です（Q8 の自己申告1）。
21. `.claude/tools/pre_audit_check.py`（:108-126・:212-222） — 監査の前の検査の指紋です。やらないことの Y-6 で2本を足しました（Q8 の自己申告4）。
22. `.claude/breaks/b222_catalog_drops_last_set.sh`（全文） — 新しい壊すプログラムです。完成の条件1 を守ります（Q9）。
23. `.claude/breaks/b223_catalog_reads_old_key.sh`（全文） — 新しい壊すプログラムです。完成の条件2 を守ります（Q9）。
24. `.claude/breaks/b224_reader_sets_no_reg.sh`（全文） — 新しい壊すプログラムです。完成の条件3 を守ります（Q9）。
25. `.claude/breaks/b225_draft_source_is_catalog.sh`（全文） — 新しい壊すプログラムです。完成の条件4 を守ります（Q9）。
26. `.claude/breaks/b226_h2_watch_no_indicators.sh`（全文） — 新しい壊すプログラムです。完成の条件5 を守ります（Q9）。
27. `.claude/breaks/b227_materials_keys_from_catalog.sh`（全文） — 新しい壊すプログラムです。完成の条件6 を守ります（Q9）。
28. `.claude/breaks/lib.sh`（:21-23・:29-101） — 壊すプログラムが使う guard・measure・finish です。壊したファイルを必ず戻す所です（Q9）。
29. `.claude/state/session_worklog_20261101.md`（:319-325・:415-456・:479-545） — この工事の実装の記録です。§9-6 に仮当ての結果が在ります（Q9）。§14 に CP96 の直す範囲の決定と直し方が在ります。§17〜§22 に実装・手順の違い・走行の結果が在ります（Q8・Q10）。
30. `SDK/.claude/audits/2026-11-01_m2c15_catalog_redirect_20261101_design_cp96_audit_report.md`（:214-222・:225-476） — 設計書の監査 CP96 の結果です。総合判定と、修正の指示17件が在ります（Q10）。
31. `SDK/.claude/ratchet/acceptance_archive/verbatim/m2c15-single-source-fix-20261023/m2c15_指標の構造_要件定義書.md`（全文） — 指標の構造の要件定義書です。3つのゴール・構造に要ることの30件・直す物の一覧・ToDo の順番が書いてあります（Q11）。
32. `SDK/.claude/ratchet/acceptance_archive/verbatim/m2c15-single-source-fix-20261023/m2c15_指標の情報を1つのデータに集約する修正_要件定義書.md`（:83-86・:135-152） — 集約の要件定義書の、修正の5つの「3.」と、要件 R1〜R14 です（Q11）。
33. `.claude/rules/core_requirements_full.md`（全文） — 要件定義の全文です。3番は機能要件、4番は探し方、5番は代表の固定値と範囲の定義、6番と7番は指標の呼び方と直し方、8番は作ってはいけない物です（R0・Q11）。

<!-- 項目: 範囲の中 -->
- 監査の相手は、`.claude/state/acceptance.md` です（設計書 `m2c15-catalog-redirect-20261101`・実装の監査）。当てる道具が、設計書の実装の指示のとおりに実装を作れているかを確かめます。
- 直す相手は、`.claude/breaks/b222_catalog_drops_last_set.sh`・`.claude/breaks/b223_catalog_reads_old_key.sh`・`.claude/breaks/b224_reader_sets_no_reg.sh`・`.claude/breaks/b225_draft_source_is_catalog.sh`・`.claude/breaks/b226_h2_watch_no_indicators.sh`・`.claude/breaks/b227_materials_keys_from_catalog.sh`・`.claude/state/indicator_review/gen_indicators_draft.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` です。
- この工事は、売買のロジックに触る工事です。engine_tuner の目的は、まこさんの言葉で「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的」です（まこさん確定 2026-08-06）。

<!-- 項目: 事実データ 名前=設計書の実装の指示の一覧（4-20・当てる道具が当てる相手） -->
| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | build_catalog の頭（F-1・F-3）＝読む口の列を作る組から列を作る新しい build_catalog を置き、直す前の中身を _catalog_from_config として残す（直す前の本体の文字は1文字も変えない） | 直した後の文字 |
| 2 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | カタログの自己テスト selftest_catalog（F-1）＝build_catalog と写す元の関数の名前の並びの照らし（⑮）と、build_catalog が設定の鍵を読まないことの照らし（⑯）を足す | 直した後の文字 |
| 3 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 読む口の column_sets（F-2）＝組ごとに計算の登録の名前を返す。組を持つのに登録の名前が無い・計算の関数の要素がオフなら止まる | 直した後の文字 |
| 4 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 読む口の使い方の説明（F-2） | 直した後の文字 |
| 5 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 読む口の自己テスト（F-2）＝登録の名前を返す行と、無ければ止まる行を足す | 直した後の文字 |
| 6 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 読む口の自己テスト（F-2）＝計算の口の「登録の名前が無ければ止まる」の試しを、組を持たない部品（帯既定）で行う（組を持つ記録は、3件目の直しで読み込みのときに止まるため） | 直した後の文字 |
| 7 | `.claude/state/indicator_review/gen_indicators_draft.py` | 写すプログラムの build_old の cols（F-4）＝写す元を _catalog_from_config にする | 直した後の文字 |
| 8 | `.claude/state/indicator_review/gen_indicators_draft.py` | 写すプログラムの catalog_sets（F-4）＝写す元を _catalog_from_config にする | 直した後の文字 |
| 9 | `.claude/state/indicator_review/gen_indicators_draft.py` | 写すプログラムの自己テスト（F-4）＝写す元が build_catalog でないことを、構文の木で照らす行を足す | 直した後の文字 |
| 10 | `.claude/state/indicator_review/gen_indicators_draft.py` | 写すプログラムの table_update（F-4）＝要素の定義表の ②-12・④-9 の「写す元」を _catalog_from_config に、「読むプログラム」に build_catalog を書く（当てた後の --rewrite で indicators.json に入る） | 直した後の文字 |
| 11 | `.claude/state/indicator_review/gen_indicators_draft.py` | 写すプログラムの PART_SRC（F-4）＝部品の記録の出どころの文を、帯の for の在りか（_catalog_from_config）に合わせる（当てた後の --rewrite で indicators.json の部品の記録8件に入る） | 直した後の文字 |
| 12 | `.claude/state/indicator_review/gen_indicators_draft.py` | 写すプログラムの頭の説明（F-4）＝列の並びの写す元を _catalog_from_config と書く | 直した後の文字 |
| 13 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py` | H2 の印の対象 WATCHED（F-5）＝読む口と1つのデータを足す | 直した後の文字 |
| 14 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py` | gen_materials の鍵を拾う口 _catalog_keys の説明（F-6） | 直した後の文字 |
| 15 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py` | gen_materials の鍵を拾う口 _catalog_keys（F-6）＝見る関数を _catalog_from_config にする | 直した後の文字 |
| 16 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py` | gen_materials の自己テスト T12（F-6）＝鍵の読みを足す相手の関数を _catalog_from_config にする | 直した後の文字 |
| 17 | `.claude/breaks/b222_catalog_drops_last_set.sh` | 壊すプログラム b222（7-6 の F-1 の1行目）＝build_catalog が列を作る組の最後の1組を作らないと、カタログの自己テストが落ちる（新しいファイル） | 直した後の文字 |
| 18 | `.claude/breaks/b223_catalog_reads_old_key.sh` | 壊すプログラム b223（7-6 の F-1 の2行目）＝build_catalog が設定の鍵を読むと、カタログの自己テストが落ちる（新しいファイル） | 直した後の文字 |
| 19 | `.claude/breaks/b224_reader_sets_no_reg.sh` | 壊すプログラム b224（7-6 の F-2）＝column_sets が登録の名前を返さないと、読む口の自己テストが落ちる（新しいファイル） | 直した後の文字 |
| 20 | `.claude/breaks/b225_draft_source_is_catalog.sh` | 壊すプログラム b225（7-6 の F-3・F-4）＝写すプログラムの写す元が build_catalog に戻ると、自己テストが落ちる（新しいファイル） | 直した後の文字 |
| 21 | `.claude/breaks/b226_h2_watch_no_indicators.sh` | 壊すプログラム b226（7-6 の F-5）＝H2 の印の対象から読む口と1つのデータを消すと、完成の条件が落ちる（新しいファイル） | 直した後の文字 |
| 22 | `.claude/breaks/b227_materials_keys_from_catalog.sh` | 壊すプログラム b227（7-6 の F-6）＝鍵を拾う口が見る関数を build_catalog に戻すと、gen_materials の自己テスト T12 が落ちる（新しいファイル） | 直した後の文字 |

<!-- 項目: 事実データ 名前=当てた記録（applied_fixes.json の名前 design:m2c15-catalog-redirect-20261101） -->
| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-11-01T18:30:35 |
| 2 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-11-01T18:30:35 |
| 3 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 当てた | 2026-11-01T18:30:35 |
| 4 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 当てた | 2026-11-01T18:30:35 |
| 5 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 当てた | 2026-11-01T18:30:35 |
| 6 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 当てた | 2026-11-01T18:30:35 |
| 7 | `.claude/state/indicator_review/gen_indicators_draft.py` | 当てた | 2026-11-01T18:30:35 |
| 8 | `.claude/state/indicator_review/gen_indicators_draft.py` | 当てた | 2026-11-01T18:30:35 |
| 9 | `.claude/state/indicator_review/gen_indicators_draft.py` | 当てた | 2026-11-01T18:30:35 |
| 10 | `.claude/state/indicator_review/gen_indicators_draft.py` | 当てた | 2026-11-01T18:30:35 |
| 11 | `.claude/state/indicator_review/gen_indicators_draft.py` | 当てた | 2026-11-01T18:30:35 |
| 12 | `.claude/state/indicator_review/gen_indicators_draft.py` | 当てた | 2026-11-01T18:30:35 |
| 13 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py` | 当てた | 2026-11-01T18:30:35 |
| 14 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py` | 当てた | 2026-11-01T18:30:35 |
| 15 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py` | 当てた | 2026-11-01T18:30:35 |
| 16 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py` | 当てた | 2026-11-01T18:30:35 |
| 17 | `.claude/breaks/b222_catalog_drops_last_set.sh` | 当てた | 2026-11-01T18:30:35 |
| 18 | `.claude/breaks/b223_catalog_reads_old_key.sh` | 当てた | 2026-11-01T18:30:35 |
| 19 | `.claude/breaks/b224_reader_sets_no_reg.sh` | 当てた | 2026-11-01T18:30:35 |
| 20 | `.claude/breaks/b225_draft_source_is_catalog.sh` | 当てた | 2026-11-01T18:30:35 |
| 21 | `.claude/breaks/b226_h2_watch_no_indicators.sh` | 当てた | 2026-11-01T18:30:35 |
| 22 | `.claude/breaks/b227_materials_keys_from_catalog.sh` | 当てた | 2026-11-01T18:30:35 |

<!-- 項目: 事実データ 名前=実装の前と後の版（git） -->
- **実装の前**：commit a3e50dfb
- **実装の後**：commit eed56c58。★この工事の中で、設計書の 4-4 の手順（G-1 の表の作り直しほか）の道具が、TARGET のファイルを書き出し直すことがある（例＝gen_materials.py --write が regime_detection_kb.md の件数の囲みを書き出す）。その行は実装の指示ではなく、設計書の 4-4・5 で照らす

<!-- 項目: 事実データ 名前=必読に要るファイル（道具が設計書と実装から拾った） -->
| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15） | 入れる |
| `.claude/breaks/b222_catalog_drops_last_set.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b223_catalog_reads_old_key.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b224_reader_sets_no_reg.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b225_draft_source_is_catalog.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b226_h2_watch_no_indicators.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b227_materials_keys_from_catalog.sh` | 直す相手（TARGET） | 入れる |
| `.claude/state/indicator_review/gen_indicators_draft.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/gen_materials.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/indicators/indicators.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/leak_causality_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/indicators/indicators.json` | `.claude/state/indicator_review/gen_indicators_draft.py` が名前を出す（実装の前後の差分） | 入れる |
| `SDK/scripts/priority_rebuild/observe_config.json` | `SDK/scripts/priority_rebuild/observe_diag.py` が名前を出す（実装の前後の差分） | 入れない（写す元の関数 _catalog_from_config が読む設定です。build_catalog が読むのは band_fee_mult だけです。この工事は変えていません） |

<!-- 項目: 範囲の外 -->
- 守りの穴探し（すり抜けの道を新しく探すこと）は、範囲の外です。穴探しは、探すたびに新しい穴が出て、終わらないためです（恒久の決まり65番）。CC は、作業が実際に止まったときに、その穴を直します。
- engine_tuner の経路の7本（observe_diag.py のほかの関数・engine_tuner_exec.py・engine_tuner_gen.py・indicator_reference_diag.py・e38.py・e38_logic_parts.py・enforce_g2_pass.py）を、読む口へ向け直さないは、範囲の外です。171番で行う。列の名前と並びは変わらないので、7本はいまのまま build_catalog の名前を読める（engine_tuner_gen.py:211・:268）。
- 残りの道具・採点・診断の24本を、読む口へ向け直さない（F-4・F-6 を除く）は、範囲の外です。170番で行う。
- 元の置き場を消さない（observe_config.json の古い鍵・material_params・drop_columns・F-3 の写す元の関数・INDICATOR_TABLE・_reg の名前と型・search_limits.json の範囲・indicator_switch.json）は、範囲の外です。162番で行う。161-2 の後も、写すプログラム（gen_indicators_draft.py:549〜550）・engine_tuner_exec・gen_materials・check_indicator_sources がこれらを読む。
- 列の名前・並び・値を変えない。パラメータの軸（②-4）の代表の値と範囲から列を作る形にしないは、範囲の外です。列を作る組（②-12・④-9）は、171番まで列を変えないための写し（161-1 の目標④・Y-4）。集約の要件定義書 R6 の「記録のパラメータだけから列を作る」のうち、161-2 で満たすのは「古い鍵を読まない・記録から作る」まで。代表の値から作るのは171番と M2-E-8。
- build_catalog から、読む口の計算の口（calc）を呼ばない。計算の本体は、いまと同じく make_material と _band_material が計算の登録（MATERIAL_FAMILIES）から取るは、範囲の外です。calc はオフの指標の計算を返さない（indicators.py:311〜312）。列を作る組は、オフの121記録（組を持つのは111記録）の250組も持つ（jq 2026-11-01・indicators.py:337〜338）。calc が返す関数と make_material が使う関数は、同じ計算の登録の同じ行（indicators.py:301〜306・observe_diag.py:1060）。calc は観察の道具を import し直す（indicators.py:73〜87）ので、観察の道具を __main__ で走らせたとき（python3 observe_diag.py --selftest-catalog）と gen_signal_families.py:55〜57 が spec_from_file_location で読み込んだときに、build_catalog から calc を呼ぶと観察の道具が2重に読み込まれる（MATERIAL_FAMILIES が別の辞書になる）。また、calc が返す帯の計算式は床を設定ファイルから読む（observe_diag.py:731〜740）ので、CP83 の修正14 案B「渡した設定の床を部品へ結び付ける」は _band_material（:793〜797）でしか守れない。★161-1 の 4-13 の :232「計算の口（calc）を、読む口から読む」とは違う。この違いが正しいかは、設計書の監査で問う（まこさん「よい」2026-11-01＝技術のやり方は CC が決め、監査で確かめる・恒久49番）。
- 監査の前の検査の指紋（.claude/tools/pre_audit_check.py:108〜122 の FINGERPRINT_FILES と :213〜215 の materials_fingerprint）に indicators/ の2本を足す直しを、この設計書に入れないは、範囲の外です。インフラの直し（2026-10-20 の決定の2＝.claude/tools は設計書と監査が要らない）。実装の後、監査に出す前のチェック（4-4 の6）の前に、規模を宣言して直す（同じ決定の3）。足すだけで、検査を外す・緩める直しではない。
- 閉じた工事の壊すプログラム b137（observe_diag.py:1811 を壊す）と b128（:1823 を壊す）を直さない・消さないは、範囲の外です。2つの工事（m2c15-param-values-20261006・m2c15-indicator-six-items-20261004）は閉じている。F-3 で壊す相手の行が写す元の関数へ移る。照らし⑮が写す元の関数を呼ぶので、b137 は写す元の関数の SystemExit「指標ごとの一覧 material_params の種類が…」で落ち（期待の文と同じ）、b128 は⑮の「名前の並びが、写す元の関数と違う」で落ちる（期待の文「❌ K-1:」とは違う＝古い壊すプログラム）。承認で走るのは設計書の表の壊すプログラムだけ（run_breaks.py --design）なので止まらない（前提が変わる＝4-13）。消すのは守りを外す直し。161-2 の守りは、7-6 の新しい壊すプログラムで作る。
- 161-1 で決まった、隠れた数字の軸の代表の値の分け方を変えない。分け方は、CP95 の修正10 の案B の文＝「合わない軸は「まだ決めていない」にし、合わない値の一覧を画面に出す（対応を決めるのは70番の T-3）。隠れた数字の軸は、資料の表に合わない値が在る記録では「まだ決めていない」にし、資料の表に当てる値が無い記録では、いまの値（要件5 の②＝既定の値・F-3）を代表の値にする」は、範囲の外です。161-2 は列を作る所だけを直し、パラメータの軸の値は写し直さない。この文は、161-1 の やることの表 F-2（:20）の文が実装と違う所を、正しく書いた物（修正10 は当てなかった＝まこさん「１は当てない」2026-11-01）。対応を決めて写すのは70番の T-3。
- RVGI({},4) の「4」のような名前の型に在る固定の数字と、登録の外の定数（band_fee_mult・_SR_ATR_TOL_LO・_SR_ATR_TOL_HI）を、パラメータの軸にしないは、範囲の外です。軸にするのは171番と70番の T-3（161-1 の 4-13 の :232・CP91 の修正13）。161-2 は列を変えない。
- 閾値の値・範囲・代表の値を、新しく調べて埋めないは、範囲の外です。70番（T-2・T-3）で行う。
- 置き場どうしで値が違う物を、CC がどちらかに決めないは、範囲の外です。R11。列を作る組は、いまのカタログの列をそのまま写した物で、どちらの値かを選んでいない。
- 成績表（material_ranking.json）と型の表を作り直さないは、範囲の外です。列の名前が変わらないので、成績表はいまのまま引ける。型の表を作る道具は build_catalog の名前を読む（gen_signal_families.py:53〜62）が、名前が同じなので型の表は変わらない見込み（G2 で確かめる）。作り直すのは M2-D-8 と197番。
- materials.md に入る説明の文（gen_materials.py:1588「材料カタログを作る関数（`observe_diag.build_catalog`）が実際に読む鍵」）を直さないは、範囲の外です。直すと、作る文書 materials.md の作り直しが要る（gen_materials.py が作る＝docmap.json）。161-2 の後、この文の「build_catalog」は、正しくは写す元の関数（F-3）を指す。162番で写す元の関数を消すときに、場所1 の数え方ごと直す。

<!-- 項目: 問い 番号=R0 優先度=A 理由=要件定義に反する直しや、要件のどれにも結び付かない直しが、そのまま進む 名前=この工事は、要件定義の何番を満たすための物か。要件定義に反する所は無いか -->
この工事が結ぶ要件は、この依頼書の「この監査は何のためか」の 3 に書いてあります。3 に「欄が無い」と書いてあるときは、3 に書いた読み方で、結ぶ要件を読み取ってください。
要件定義の要約は、この依頼書の上の方に載っています。要件定義の全文は、`.claude/rules/core_requirements_full.md` に在ります。

次の2つを確かめてください。

- **R0-1**：結ぶ要件が、工事の目的と中身に合っているかを確かめてください。もっと合う要件や、抜けている要件があれば、挙げてください。
- **R0-2**：設計と実装と直しに、要件定義に反する所が無いかを確かめてください。反する所があれば、ファイルの名前と行で挙げてください。

<!-- 項目: 問い 番号=Q1 優先度=A 理由=違えば、実装は設計書のとおりに作られていない 名前=実装の指示を当てた結果が、実装の後と1文字も同じか -->
設計書の 4-20 には、実装の指示が 22 件あります。
実装の前の対象のファイルに、この 22 件を番号の順に当ててください。実装の前の版は、事実データ「実装の前と後の版」の実装の前です。対象のファイルは、`.claude/breaks/b222_catalog_drops_last_set.sh`・`.claude/breaks/b223_catalog_reads_old_key.sh`・`.claude/breaks/b224_reader_sets_no_reg.sh`・`.claude/breaks/b225_draft_source_is_catalog.sh`・`.claude/breaks/b226_h2_watch_no_indicators.sh`・`.claude/breaks/b227_materials_keys_from_catalog.sh`・`.claude/state/indicator_review/gen_indicators_draft.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py`です。
当てた結果が、実装の後の版と1文字も同じかを確かめてください。実装の後の版は、事実データ「実装の前と後の版」の実装の後です。
確かめ方の例は、次のとおりです。まず、作業場に、git show で実装の前のファイルを出します。次に、直す前の文字を、直した後の文字に置き替えます。足す文字の指示なら、直す前の文字の後ろに、足す文字を足します。最後に、置き替えた結果と実装の後の版の差を、diff で取ります。

<!-- 項目: 問い 番号=Q2 優先度=A 理由=在れば、設計書に無い変更が実装に混ざっている 名前=実装の指示のどれにも当たらない行（設計書に無い変更）が無いか -->
実装の前の版と実装の後の版の差分を取ってください。実装の前の版は、事実データ「実装の前と後の版」の実装の前です。実装の後の版は、事実データ「実装の前と後の版」の実装の後です。差分を取るファイルは、`.claude/breaks/b222_catalog_drops_last_set.sh`・`.claude/breaks/b223_catalog_reads_old_key.sh`・`.claude/breaks/b224_reader_sets_no_reg.sh`・`.claude/breaks/b225_draft_source_is_catalog.sh`・`.claude/breaks/b226_h2_watch_no_indicators.sh`・`.claude/breaks/b227_materials_keys_from_catalog.sh`・`.claude/state/indicator_review/gen_indicators_draft.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py`です。
差分のうち、実装の指示のどれにも当たらない行が在るかを確かめてください。在れば、全部を挙げてください。

<!-- 項目: 問い 番号=Q3 優先度=A 理由=合わなければ、どの件を道具が当てたかを後から確かめられない 名前=当てた記録が、実装の指示の全部と1件ずつ合うか -->
当てる道具は、実装の指示を当てるたびに、`SDK/.claude/audits/applied_fixes.json` に記録を書きます。この工事の記録の名前は、`design:m2c15-catalog-redirect-20261101` です。
この記録が、実装の指示の 22 件と、番号と対象のファイルで1件ずつ合うかを確かめてください。
記録に「当てた」とも「もう当て終わっていた」とも書かれていない件が在るかを確かめてください。
「もう当て終わっていた」の件について、その件がどの実行で当たったかを確かめてください。確かめる材料は、当てる道具の出力と、git の差分です。

<!-- 項目: 問い 番号=Q4 優先度=B 理由=当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない 名前=承認した版の設計書どうしで、実装の指示が同じか -->
まこさんが承認した版の設計書の控えは、`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-catalog-redirect-20261101.md`です。
この控えの 4-20 の実装の指示と、いまの設計書の 4-20 の実装の指示が同じかを確かめてください。★2つが同じファイルを指すときは、控えのハッシュ値と、承認の印（`.claude/state/acceptance.approved`）の値と、控えのコミットの版が同じかを確かめてください。違うなら、その違いが実装に影響するかを答えてください。

<!-- 項目: 問い 番号=Q5 優先度=B 理由=要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない 名前=実装の指示が、やることの表の要件を全部 満たすか -->
やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-catalog-redirect-20261101/やることの表.md`）の一覧には、この工事でやることが書いてあります。
実装の指示が、この一覧のやることを全部満たすかを確かめてください。
一覧に在るのに実装の指示に無い物と、実装の指示に在るのに一覧に無い物を、全部挙げてください。

<!-- 項目: 問い 番号=Q6 優先度=B 理由=成り立たなければ、承認のときの「済」が根拠にならない 名前=完成の条件が、実装の後に本当に成り立つか -->
設計書の完成の条件の表には、6 行の条件が書いてあります。
この条件が、実装の後に本当に成り立つかを確かめてください。
各行のコマンドを、作業場で走らせるか、読むだけの形で走らせてください。コマンドの中のパスは、`SDK` のフォルダからの相対です。そのため、どのコマンドも `SDK` のフォルダで走らせます。
走らせるコマンドは、次のとおりです。`python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog`・`python3 scripts/priority_rebuild/indicators/indicators.py --selftest`・`python3 ../../.claude/state/indicator_review/gen_indicators_draft.py --selftest`・`grep -H -c -F 'indicators/indicators.json' scripts/priority_rebuild/leak_causality_diag.py`・`python3 scripts/priority_rebuild/gen_materials.py --selftest`

<!-- 項目: 問い 番号=Q8 優先度=A 理由=実装が設計書と違うと、171番が読む build_catalog と読む口が、まこさんが承認した物と違ってしまう 名前=当てた実装16件と、書き替えた indicators.json が、承認された設計書のとおりか -->
実装の指示は22件です。
- 実装1・2 は、observe_diag.py の build_catalog と、カタログの自己テストを直します。
- 実装3〜6 は、読む口 indicators.py を直します。
- 実装7〜12 は、写すプログラムを直します。
- 実装13 は、H2 の検査の対象を足します。
- 実装14〜16 は、gen_materials.py を直します。
- 実装17〜22 は、壊すプログラム6本を新しく作ります（Q9）。

CC がしたことは、次のとおりです。
- 当てる道具（apply_audit_fix.py --design）が22件を当てました。
- CC は、設計書の 4-4 の2〜7 を走らせました。
- 写すプログラムの --verify は「違い 0 件」でした。
- 列の比べ（155-1）は、控えに在って今に無い列 0・今にだけ在る列 0・値が違う列 0・名前の並び同じでした。

次の4つに答えてください。
- 1つ目に、実装1〜16 の実物が、設計書の「直した後の文字」と1文字も違わないかを答えてください。
- 2つ目に、F-3 の「本体の文字は1文字も変えない」が守られているかを答えてください。確かめるコマンドは、4-4 の2 の git diff -U0 です。commit の後なので、eed56c58 とその親の差で見てください。
- 3つ目に、書き替えた indicators.json が、4-4 の3 と 4-12 のとおりかを答えてください。列を作る組の組と並びは変わっていないはずです。確かめるコマンドは、写すプログラムの --verify（約97秒）と読む口の --count です。
- 4つ目に、完成の条件6行（設計書の 7-6）を SDK の直下で走らせ、結果を答えてください。

**CC の自己申告1（--rewrite の前に一覧を作り直し、一覧を作る道具を直した）**
- 設計書の 4-4 に、この段はありません。まこさんの OK をいただいて足しました。
- 写すプログラムは、直す相手の一覧の行番号で置き場を探します。実装で build_catalog の前に35行が足されたので、--rewrite が「置き場が見つからない」で止まりました（worklog :489-492）。
- 一覧を作り直すと、行番号が読む係の報告の版のままなので、写す行が 732 から 731 に減り、行と中身が合わない行が出ました（worklog :495-498）。この一覧では --rewrite を走らせていません。
- CC は、一覧を作る道具 gen_fix_inventory.py に、報告の行番号をいまの行番号へ読み替える関数を足しました。インフラの直しなので、設計書と監査は付けていません。このファイルは git の対象外です。
- 直した後の一覧は、写す行 732・2,761行です。拾えなかった行は 202 から 195 に減りました。CC は、減った7行が正しい方向の変化だと考えています（worklog :509）。ただし、CC 自身の確かめです。
- 見てほしいことは、この一覧で --rewrite の写し漏れの照らしが弱まっていないかです。

**CC の自己申告2（--rewrite の「違う所」が、見込みの10件でなく34件だった）**
- 設計書の 4-4 の3 と 4-10 と 4-12 は、「違う所」を10か所と書いています。実物は34件でした。
- 記録は置き場を行番号で持ちます。そのため、「置き場」の行番号も「違う所」に数えられました（worklog :514-515）。設計書は、この行番号の更新を数えていませんでした。
- CC は git diff を見て、列を作る組・並び・代表の値・範囲の変更は0件と読みました。これも CC 自身の確かめです。

**CC の自己申告3（列の比べの打ち方を、設計書のコマンドから変えた）**
- 設計書の 4-4 の5 のコマンドは --compare だけです。CC は、途中で落ちてもやり直さないように、--out を一緒に付けました。
- CC は先に、--out と --budget 60 で先頭の100種を計算し、jq で控えと照らしました。本番は、その続きから計算しました。結果は rc 0・59分03秒です（worklog :523-529）。
- 帯VA の3本は、別に --cols で照らしました。
- --compare に --cols を付けると、控えの全部の列と比べるので、控えに在って今に無い列が多く出ます（col_snapshot.py の main）。小さく確かめるときは、--out と --cols で作業場に書き、jq で控えと照らしてください。
- 全部を走らせ直すと、約59分かかります。走らせ直すかは、監査人が決めてください。

**CC の自己申告4（インフラの直しを先に commit した）**
- 4-4 の6 のインフラの直し（Y-6）は、設計書のやらないことに書いた物です。
- 4-4 の7 の走らせ直しで、設計↔実装ゲートが、Y-6 の直し（pre_audit_check.py）を「設計書の impl_functions に書いていないファイルを触った」と止めました（worklog :540）。設計書の Y-6 とゲートが食い違っていました。
- まこさんの OK をいただき、インフラの4本を先に commit しました（a3e50dfb）。この commit には、別の直しの宣言の hook（202番）も入っています。
- そのあと、4-4 の7 を走らせ直し、実装を commit しました（eed56c58）。

**CC の自己申告5（監査に出す前のチェックが、見込みの12分でなく約44分かかった）**
- 設計書の 4-14 と 6-3 は、約12分と書いています。実物は約44分でした。指紋が変わったので、材料の検査（34分40秒）が省略されずに走ったためです（worklog :535-536）。
- 設計書の 6-3 は、見込みの2倍を超えたら止めて報告すると書いています。CC は止めませんでした。まこさんに聞かれて初めて気づきました。
- 記録（pre_audit_check.json）の時刻は 21:24:11 です。直したファイルの時刻は、全部それより前です。

**CC の自己申告6（当てる道具が、4-4 の3 の前に G2 と H2 を走らせた）**
- 当てる道具は、当てた後に G2 と H2 まで走らせました（worklog :483）。4-4 の4 より前です。
- CC は、--rewrite の後に G2 → H2 を走らせ直しました。いまの検査済みの記録は、走らせ直した物です。

<!-- 項目: 問い 番号=Q9 優先度=B 理由=落ちない壊し方が在ると、build_catalog や読む口が壊れても、誰も気づかない 名前=壊すプログラム6本は、設計書の 7-6 の壊し方のとおりで、直しを外したときだけ落ちるか -->
写しの作業場で、次の6本を走らせてください。
- b222：build_catalog が、列を作る組の最後の1組を作らない（条件1 を守る）
- b223：build_catalog に cfg["rsi_periods"] を読む行を足す（条件2 を守る）
- b224：column_sets の返り値から登録の名前を外す（条件3 を守る）
- b225：catalog_sets の呼び先を build_catalog に戻す（条件4 を守る）
- b226：WATCHED から indicators.json の行を消す（条件5 を守る）
- b227：_catalog_keys が見る関数の名前を build_catalog に戻す（条件6 を守る）

見てほしいことは、次の3つです。
- 宣言した文（EXPECT_MSG）で落ちるか。
- 壊す対象を、正しく1か所だけ見つけるか。
- 壊した後に、必ず元に戻るか。

CC が確かめたことは、次のとおりです。
- 承認の前の検査（仮当てを含む）は、通りました。その中に、壊すプログラム6本の確かめが入ります（worklog :320-324）。仮当ての時点の indicators.json は、--rewrite の前の形でした。
- 承認の記録（m2c15-catalog-redirect-20261101.breaks.json）の終了コードは、6本とも空です。
- CC は、commit の後に、run_breaks.py --design <設計書> --measure-only で6本を走らせました。この走らせ方は、記録を書きません。6本とも終わりのコード 1 で、宣言した文が出力に在りました（1分41秒）。
- 161-1 の壊すプログラム b215〜b221 も、同じ走らせ方で、承認の控えの設計書を渡して走らせました。7本とも同じ結果でした（10秒）。設計書の 4-13 は「変わらない見込み」と書いています。
- 走らせた後に、読む口の自己テストは 36/36、写すプログラムの自己テストは 40/40 でした。indicators.json の sha256 は 4d3f3717… のままで、追跡しているファイルに変更は残っていません。
- どれも CC 自身の確かめです。b215〜b221 が、いまも決めた文で落ちるかも見てください。

<!-- 項目: 問い 番号=Q10 優先度=A 理由=指示と違う形で入った件が在ると、設計書の監査で直したはずの誤りが残ったまま、171番へ進む。161-1 では、案の文とコードが違う件が1つ在った 名前=設計書の監査 CP96 の修正17件と、同じ事実をそろえた5か所が、指示のとおりに実装と設計書に入っているか -->
監査 CP96 の修正の指示は、結果の8番の節と9番の節（:225-476）に在る17件です。

まこさんが決めた直し方は、次のとおりです。
- 修正1〜17 を、全部入れる。修正15 は、修正13・14 を当てた後の sha256 を、CC が書く。
- 同じ事実を書く5か所もそろえる。5か所は、①オフの121記録の文（やることの表:36 と案:26）②案の「56ある」（:159）③案の「効かなくなる」（:173）④やることの表の 4-5 の止まる条件 ⑤実装の指示の下書き（impl_src/e01_after.txt）です（worklog :427）。
- 決めた記録は、session_worklog_20261101.md の §14-3（:431）です。

CC の入れ方は、次のとおりです。
- 11件（修正1・3・4・6・7・10・12・13・14・16・17）は、当てる道具が当てました（applied_fixes.json の CP96 の行）。修正13・14 は実装の指示の json へ、ほかはやることの表へ入りました。
- 6件（修正2・5・8・9・11・15）は、CC が案の節に入れて直し、まこさんの OK をいただきました（okd_an2_20261101.txt）。そのため、当てた記録には残っていません。next_move.py が「いまここ」を段6 と出すのは、この6件のためです。
- 修正1 と修正16 の文に在ったパイプの記号は、設計書を作る道具が表の区切りと数えます。CC は、表の中だけ、パイプを使わない同じ確かめに書き替えました（worklog :442）。
- 監査の修正に無い直しを1つ入れました。2-1 の awk の終わりの目印です。まこさん「直して良い」です（worklog :444・:447）。

次の2つに答えてください。
- 1つ目に、修正1〜17 と5か所を1件ずつ、修正の指示の文と、設計書と、実装の3つで照らしてください。そのうえで、合っているか、違うかを答えてください。違う件は、どこがどう違うかを、実物の行で示してください。
- 2つ目に、設計書の文（§5・4-5・4-12・4-13 ほか）と、実装の実物が、食い違っている所が無いかを答えてください。自己申告2 と自己申告5 は、その例です。

<!-- 項目: 問い 番号=Q11 優先度=A 理由=要件どおりでない実装が在ると、171番・70番が、その上に積み上がる。設計書の監査（CP96 の Q12）でも照らしたが、その後に修正17件を入れて実装したので、実装で照らし直す 名前=指標の構造の要件定義書の要件のうち、この工事に当たる箇所が、要件どおりに実装されているか -->
指標の構造の要件定義書は、指標の工事で守る物を1本にまとめた文書です（367行）。

照らす項目は、次のとおりです。
- 第1章：ゴール1、ゴール2の①〜⑤、ゴール3の①〜④、順番。
- 第2章：機能要件の1〜6、探し方、言葉の定義、指標の使い方、教科書と法則の扱い、作ってはいけない物。
- 第2章の2：作る物（1つのデータ・読む口・どのプログラムからも呼べるライブラリ・記録に入れる物の一覧・読む口が指標一覧に当たること）。
- 第3章：拡張と直しやすさの条件。
- 第4章：構造の案 A〜F、決めたこと2つ、indicators.json の欄との対応。
- 第5章：構造に要ることの30件。
- 第6章：直す物の一覧（A 探し方と母数〜G 正本と ToDo）。
- 第7章：やってはいけないこと。
- 第8章：ToDo の行のうち、161番・155番の決まった中身。

項目ごとに、次の3つのどれか1つで答えてください。
- 実装で受けている：受けている所（関数と行・indicators.json の要素）を書き、要件どおりかを答えてください。
- 後の工事で受ける：その工事が、第8章の ToDo の行か、設計書のやらないこと（Y-1〜Y-13）に在るかを確かめてください。
- この工事に当たらない：その理由を書いてください。

特に、次の5か所を見てください。
- 集約の要件定義書の R6 は「記録のパラメータだけから列を作る」と書いています。実装は、パラメータの軸（②-4）でなく、列を作る組（②-12・④-9）から列を作ります（Y-4）。この形で「記録から作る」と言えるかを見てください。
- 第2章の2 は、読む口が「指標の値の計算も返す」と書いています。build_catalog は calc を使いません（Y-5）。計算の取り方と帯の床の結び付け方は、CP96 の Q9 が171番で決めると書いています。CC は、この申し送りを171番の ToDo の行に足しました（まこさんの決定 2026-11-01）。
- 要件の「オン/オフは全部のロジックに効く」について、build_catalog はオフの列も作ります（Y-4・Y-5）。engine_tuner の側で外す形で足りるかを見てください。
- 第6章の F は「G2・H2 の印」を、名前を変えると連鎖で壊れる物に挙げています。実装では、G2 の対象に indicators.json が入りません（4-13）。
- 第1章のゴール1 の「そこからしか取れない」は、162番で受けます。写す元の関数 _catalog_from_config は、162番まで設定の古い鍵を読みます（Y-3）。

受け先が無い項目や、第7章のやってはいけないことに当たる実装が在れば、挙げてください。

<!-- 項目: 外部検索 名前=列を作る所を、データの側の定義から作る作り -->
検索の言葉：feature catalog built from metadata registry function lookup by name single source of truth
調べる物：列の組（名前の型・パラメータの組・並び）をデータの側に持ち、列を作る関数がそれを読んで、計算の本体は名前で引く登録から取る作りが、外の一般の作り方と合うか。新しく Web は開いていない。実装の監査では、この出どころと、実装の該当の所が合うかを照らします

<!-- 項目: 外部検索 名前=作り直す前と後で出力が同じことを確かめる作り -->
検索の言葉：refactoring regression test snapshot hash compare feature columns before after
調べる物：直す前の列の名前と値のハッシュ値を控え、直した後に同じかを比べる作り（回帰の照合）が、外の一般の作り方と合うか。新しく Web は開いていない。実装の監査では、この出どころと、実装の該当の所が合うかを照らします


<!-- 項目: 自己申告 -->
**この工事の外の作業中の変更**：次のファイルには、作業中の変更があります。`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`。この変更は、この工事の実装の指示が当てた物ではありません。そのため、Q1 と Q2 の差分を、この工事の対象のファイルだけで取ってください。

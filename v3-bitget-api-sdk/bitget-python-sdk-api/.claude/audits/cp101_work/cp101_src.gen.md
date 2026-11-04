<!-- gen_audit_docs request-design kind=impl work=m2c15-laws-rows-20261103 design_sha256=4d785eea322aa0bfc4b301e8ff7821ddb4288a526a8611a976e5310a41e8eec2 src_sha256=d1c6906127b045fc5c6c84426c6676b32f4855a75ab2cc88504ca0d656cc6faa body_sha256=e9dd377a946b904c1d006dfa1fb94cc9a71ceb2e275c1958dc1a7fa16eb073b6 -->
<!-- 項目: メタ -->
日付: 2026-11-04
task: m2c15_laws_rows_20261103_impl
cp: cp101
題: CP101 — レベル3 の法則のデータに行を写し、読むプログラムを作る。ToDo の209番・M2-C-15（実装の監査）
依頼者: CC（起案者）
監査の種類: 実装の監査
監査対象タスク: M2-C-15／設計書 m2c15-laws-rows-20261103
監査の相手: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-laws-rows-20261103.md
売買に触るか: はい
直す相手: `.claude/breaks/b211_structure_need_missing.sh`・`.claude/breaks/b213_place_missing.sh`・`.claude/breaks/b228_laws_kubun_missing.sh`・`.claude/breaks/b230_records_changed_laws.sh`・`.claude/breaks/b234_laws_row_missing.sh`・`.claude/breaks/b235_laws_form_missing.sh`・`.claude/breaks/b236_laws_reader_ref.sh`・`.claude/breaks/b237_laws_doc_changed.sh`・`.claude/breaks/b238_laws_source_diff.sh`・`.claude/breaks/b239_records_changed_rows.sh`・`.claude/breaks/b240_t44_s1_diff.sh`・`.claude/state/req_trace_src.json`・`.claude/tools/check_one_path.py`・`.claude/tools/pre_audit_check.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json`

<!-- 項目: 作業場の指示 -->
写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp101_work/` に作る。必要なファイルは自分で開き、写しで走らせて確かめる。

<!-- 項目: 修正をどこに書くか -->
実装が設計書と違う所の修正は、その実装のファイルに書いてください。修正を当てるプログラムが、その修正を当てます。
ただし、修正を当てるプログラムは、.claude/hooks と .claude/tools と .claude/breaks のファイルには当てません。そのファイルの修正は、CC が書きます。
設計書の誤りの修正は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-laws-rows-20261103/やることの表.md`）に書いてください。設計書はプログラムが作るので、設計書に直接書けません。

<!-- 項目: 目的と経緯 -->
1. **この工事は何のためか**：この工事は、E38 の売り方と決済の枝を法則のデータ laws.json に行として写し、読むプログラム laws.py を作ります。法則の値を1か所に置き、足す・直す・止める・消すを行えるようにするためです。行が誤っていると、engine_tuner が後で組むロジックも誤ります。この監査では、設計書のとおりに実装できているかを確かめます。設計の中身は問いません
2. **この工事は何か**：この工事の中身は、設計書の「§1 概要」に書いてあります。実装の指示の一覧は、事実データの表に載せました。やることの番号は、M2-C-15です。
   **この工事の位置**：目標からこの工事までのつながりは、次のとおりです。全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝指標の構造の工事（ゴール1〜3）。指標の情報を1つのデータに集め、形を要件に合わせ（worklog 20261030 §17-1 の A〜C）、法則を1つのデータにまとめる（同 D）。全体のマイルストーンでは①の中で行う → この工事
3. **この工事が結ぶ要件**：M2-C-15＝この工事が満たす要件は、要件定義の次の3つです。3番：指標・閾値・パラメータ・時間足が、それぞれの役割に沿って使われ、閾値とパラメータが範囲から探されていること。4番と5番：最初の段階では、閾値とパラメータを、戦略ごとの代表の固定値にして探すこと。6番：指標は1か所から呼び出すこと。教科書と法則の誤りは、1か所を直せば全部に届くこと。（出どころ＝やることリスト m2_todo.json の「結ぶ要件」）
4. **経緯**：この監査に至るまでの経緯は、次のとおりです。
   - 設計書の監査 CP100 の結論は CONDITIONAL-GO で、Critical は7件でした。問題は5つです。1つ目は、オフの行も照らすので S1 を止められないことです。2つ目は、使い方の行を売買の方向で絞らないので、ロングの行を足すとショートの枝が解けないことです。3つ目は、枝の型 FINSTOP の負の値の欄を写し漏らし、逆の条件になることです。4つ目は、T44 の比べる欄が足りないことです。5つ目は、BB%b の 1 が +2σ の旗と同じ条件でないことです。
   - まこさんは、CP100 の修正を全部（Critical・Major・Minor・Process）直すと決めました。修正4 は案B（BB%b の閾値 1.0129892）です。修正26 は案B です。修正14 は、写しと書く相手を手数料の床だけにしました。
   - CP100 の修正32件は、次の2つに分かれます。10件（修正5・19・20・22・25・26・27・29・30・31）は、当てる道具で当てました。22件は、道具が案の写しに当てない作りなので、CC が次の案と実装の指示に書き、まこさんの OK を受けました。このため、当てた記録に無い修正が22件あります。next_move.py は、段6 を「飛ばした」と出します。
   - CC は、監査の指示と次の3か所を変えました。1つ目に、修正13 は監査が挙げた4行のほかに `"208"` の行が18行あったので、22行全部を「済＝208番」にしました。この22行は、設計書を作るプログラムが止まるので、承認の前に当てました。2つ目に、修正9 の後半（完成の条件の表に b213 を載せる）は行っていません。すでに在る壊すプログラムを表に載せると、承認の検査が承認の前の測定を求めるためです。3つ目に、修正20 の「37行」は、修正18 を入れた結果の「36行」に直しました。
   - CC は、修正を入れた後に、同じ事実を書いた別の節を揃えました。やることの表の一覧・3-2・4-5・4-8・4-13・4-19・7-6 と、ToDo の222番と224番の確認の文です。
   - 実装では、次の2つが設計書と違いました。1つ目に、当てる道具は34件を当てた後に、照合A(双方向) で止まり、後半の実行を行いませんでした。CC が確かめを1本ずつ走らせました。2つ目に、設計書 6-5 の `bash .claude/breaks/b213_place_missing.sh` は土台ゲートに止められました。CC は、前の工事の設計書を相手に run_breaks.py --measure-only --only で測りました。
   - CC は、次の所を確かめていません。実装の指示の中の法則の行の全文は、1行ずつ目で読んでいません。CC は、写す元の鍵のうち行へ写さない鍵98件の理由を書きましたが、その理由が正しいかは CC 以外が確かめていません。
   - 法則の中の数の出どころのうち、S1_下げ型の天井の窓 と S1_レンジの年齢の上限 は、実装の指示では identity_s1_legacy.json:5 を指していました。この行は値の行ではなく説明の文の行です。CC は実装の後に法則一覧.md を読んで気づきました。まこさんの OK を受け、laws.json のこの2行を :15 と :16 に直し、法則一覧.md を作り直しました。この2行の出どころと、法則一覧.md の同じ2行は、実装の指示と違います。
   - CC は、当てた後に次を走らせました。読む口の自己テスト 43/43、完成の条件14行、壊すプログラム8本、対応表、G2、H2、監査に出す前のチェックです。この結果を、そのまま信じないでください。

<!-- 項目: 着手前必読 -->
**パスは、リポジトリの根（`cat-bitget/`）からの相対です。**`SDK` は、`v3-bitget-api-sdk/bitget-python-sdk-api` の略です。

1. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-laws-rows-20261103.md`（全文） — 監査の相手の設計書です。プログラムが作りました。まこさんが承認した版の設計書の控えです。どの版の 4-20 で当てたかは、Q4 で照らします。このファイルは、承認された設計書です。実装の指示は34件、完成の条件は14行です。実物と照らす相手です。
2. `SDK/.claude/audits/applied_fixes.json`（全文） — 当てる道具が書いた、当てた記録です。この工事の行の名前は design:m2c15-laws-rows-20261103 です。このファイルは、当てた記録です。経緯に書いた22件が記録に無いことを照らします。
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-laws-rows-20261103/やることの表.md` — 設計書の元（やることの表）です。監査人は、修正の指示をこのファイルに書きます。
4. `SDK/.claude/rules/cat_requirements.md`（:269-290） — このファイルの §1.2.2 に情報の4段が在ります。実装の監査は設計の中身を問わないので、前提として読むだけです。
5. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-60） — このファイルに engine_tuner の目的が在ります。前提として読むだけです。
6. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:132-150） — このファイルに M2 以降の順番が在ります。前提として読むだけです。
7. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:81-109） — このファイルに M2 で作っている物が在ります。前提として読むだけです。
8. `SDK/.claude/audits/2026-11-03_m2c15_laws_rows_20261103_design_cp100_audit_report.md`（:476-998） — このファイルには、設計書の監査の修正32件が在ります。修正が設計書と実装に入ったかを照らします。
9. `SDK/scripts/priority_rebuild/laws/laws.json`（全文） — このファイルに行と表を入れました。実装1〜5 と同じかを照らします。
10. `SDK/scripts/priority_rebuild/laws/laws.py`（全文） — このファイルは読む口です。実装7 と同じかを照らします。
11. `SDK/.claude/rules/法則一覧.md`（全文） — この文書は読む口が作ります。実装8 と同じかを照らします。
12. `SDK/scripts/priority_rebuild/indicators/indicators.json`（:98945-99060） — このファイルに使い方の行を4行足しました。実装6 と照らします。
13. `SDK/scripts/priority_rebuild/indicators/indicators.py`（:220-331） — このファイルは指標データの読む口です。laws.py が usages・record・choices・names を呼びます。
14. `SDK/scripts/priority_rebuild/indicator_reference_diag.py`（:6010-6060） — このファイルの CONST_REGISTRY と STATE_COLS は写す元です。--check-sources の比べの相手です。
15. `SDK/scripts/priority_rebuild/recipes/search_limits.json`（:14-37） — このファイルは数の範囲の写す元です。--check-sources の比べの相手です。
16. `SDK/scripts/priority_rebuild/recipes/identity_s1_legacy.json`（全文） — このファイルは S1 の写す元です。T44 の比べの相手です。
17. `SDK/.claude/ratchet/exit_families_rules.json`（全文） — このファイルは枝の型の写す元です。--check-sources の比べの相手です。
18. `SDK/scripts/priority_rebuild/e38_logics.json`（:30-60・:140-290） — このファイルは売り方の写す元です。--check-sources の比べの相手です。
19. `.claude/tools/check_one_path.py`（:270-290・:431-539） — このファイルに T44 を足しました。実装9・10 と照らします。
20. `.claude/state/req_trace_src.json`（:21-31・:134・:162・:166・:191・:202・:213・:217） — このファイルの確認と試験と割り当てを直しました。実装11〜20 と照らします。
21. `.claude/tools/pre_audit_check.py`（:63-72・:125-130） — このファイルに検査4本と指紋を足しました。実装25・26 と照らします。
22. `SDK/.claude/rules/要件定義書_レベル4_指標の構造.md`（:160-166） — この文書の法則の文を直しました。実装27 と照らします。
23. `.claude/breaks/b211_structure_need_missing.sh`（全文） — 壊すプログラムです。実装21 と照らします。
24. `.claude/breaks/b213_place_missing.sh`（全文） — 壊すプログラムです。実装22 と照らします。
25. `.claude/breaks/b228_laws_kubun_missing.sh`（全文） — 壊すプログラムです。実装23 と照らします。
26. `.claude/breaks/b230_records_changed_laws.sh`（全文） — 壊すプログラムです。実装24 と照らします。
27. `.claude/breaks/b234_laws_row_missing.sh`（全文） — 壊すプログラムです。実装28 と照らします。
28. `.claude/breaks/b235_laws_form_missing.sh`（全文） — 壊すプログラムです。実装29 と照らします。
29. `.claude/breaks/b236_laws_reader_ref.sh`（全文） — 壊すプログラムです。実装30 と照らします。
30. `.claude/breaks/b237_laws_doc_changed.sh`（全文） — 壊すプログラムです。実装31 と照らします。
31. `.claude/breaks/b238_laws_source_diff.sh`（全文） — 壊すプログラムです。実装32 と照らします。
32. `.claude/breaks/b239_records_changed_rows.sh`（全文） — 壊すプログラムです。実装33 と照らします。
33. `.claude/breaks/b240_t44_s1_diff.sh`（全文） — 壊すプログラムです。実装34 と照らします。

<!-- 項目: 範囲の中 -->
- 監査の相手は、`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-laws-rows-20261103.md` です（設計書 `m2c15-laws-rows-20261103`・実装の監査）。当てる道具が、設計書の実装の指示のとおりに実装を作れているかを確かめます。
- 直す相手は、`.claude/breaks/b211_structure_need_missing.sh`・`.claude/breaks/b213_place_missing.sh`・`.claude/breaks/b228_laws_kubun_missing.sh`・`.claude/breaks/b230_records_changed_laws.sh`・`.claude/breaks/b234_laws_row_missing.sh`・`.claude/breaks/b235_laws_form_missing.sh`・`.claude/breaks/b236_laws_reader_ref.sh`・`.claude/breaks/b237_laws_doc_changed.sh`・`.claude/breaks/b238_laws_source_diff.sh`・`.claude/breaks/b239_records_changed_rows.sh`・`.claude/breaks/b240_t44_s1_diff.sh`・`.claude/state/req_trace_src.json`・`.claude/tools/check_one_path.py`・`.claude/tools/pre_audit_check.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` です。
- この工事は、売買のロジックに触る工事です。engine_tuner の目的は、まこさんの言葉で「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的」です（まこさん確定 2026-08-06）。

<!-- 項目: 事実データ 名前=設計書の実装の指示の一覧（4-20・当てる道具が当てる相手） -->
| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` | 「動く条件が指せる物」の末尾と選べる値の閉じ（:1099〜:1101） | 直した後の文字 |
| 2 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` | 「読む口が守る決まり」の末尾（:1112） | 直した後の文字 |
| 3 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` | 表の形の条件の1本の欄（:1115〜・枝型 FINSTOP の負の印） | 直した後の文字 |
| 4 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` | 表の形の法則の中の数の単位の形（:1179） | 直した後の文字 |
| 5 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` | 「法則の行」と3つの表（:1187〜:1190） | 直した後の文字 |
| 6 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` | 「使い方の記録」の末尾（:98945） | 直した後の文字 |
| 7 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.py` | 新しいファイル（F-3・F-5） | 直した後の文字 |
| 8 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/法則一覧.md` | 新しいファイル（F-4） | 直した後の文字 |
| 9 | `.claude/tools/check_one_path.py` | t44 を足す（F-7） | 直した後の文字 |
| 10 | `.claude/tools/check_one_path.py` | CHECKS に T44 を足す（F-7） | 直した後の文字 |
| 11 | `.claude/state/req_trace_src.json` | 確認の 209・216・225（:21・F-8）。同じ行なので1件にまとめた | 直した後の文字 |
| 12 | `.claude/state/req_trace_src.json` | 試験を作る番号の T17（F-8）と T46・T47 | 直した後の文字 |
| 13 | `.claude/state/req_trace_src.json` | 試験の一覧に T46・T47 を足す（修正13） | 直した後の文字 |
| 14 | `.claude/state/req_trace_src.json` | 割り当て :134（修正13） | 直した後の文字 |
| 15 | `.claude/state/req_trace_src.json` | 割り当て :162（修正13） | 直した後の文字 |
| 16 | `.claude/state/req_trace_src.json` | 割り当て :166（修正13） | 直した後の文字 |
| 17 | `.claude/state/req_trace_src.json` | 割り当て :191（修正13） | 直した後の文字 |
| 18 | `.claude/state/req_trace_src.json` | 割り当て :202（修正13） | 直した後の文字 |
| 19 | `.claude/state/req_trace_src.json` | 割り当て :213（修正13） | 直した後の文字 |
| 20 | `.claude/state/req_trace_src.json` | 割り当て :217（修正13） | 直した後の文字 |
| 21 | `.claude/breaks/b211_structure_need_missing.sh` | measure の行（F-9） | 直した後の文字 |
| 22 | `.claude/breaks/b213_place_missing.sh` | 全文（F-10） | 直した後の文字 |
| 23 | `.claude/breaks/b228_laws_kubun_missing.sh` | measure の行（F-11） | 直した後の文字 |
| 24 | `.claude/breaks/b230_records_changed_laws.sh` | measure の行（F-12） | 直した後の文字 |
| 25 | `.claude/tools/pre_audit_check.py` | CHECKS（F-13） | 直した後の文字 |
| 26 | `.claude/tools/pre_audit_check.py` | FINGERPRINT_FILES（F-13） | 直した後の文字 |
| 27 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md` | 第3章の2 の法則の文（:163・F-14） | 直した後の文字 |
| 28 | `.claude/breaks/b234_laws_row_missing.sh` | 壊すプログラム（7-6 の F-1・新しいファイル） | 直した後の文字 |
| 29 | `.claude/breaks/b235_laws_form_missing.sh` | 壊すプログラム（7-6 の F-2・新しいファイル） | 直した後の文字 |
| 30 | `.claude/breaks/b236_laws_reader_ref.sh` | 壊すプログラム（7-6 の F-3・新しいファイル） | 直した後の文字 |
| 31 | `.claude/breaks/b237_laws_doc_changed.sh` | 壊すプログラム（7-6 の F-4・新しいファイル） | 直した後の文字 |
| 32 | `.claude/breaks/b238_laws_source_diff.sh` | 壊すプログラム（7-6 の F-5・新しいファイル） | 直した後の文字 |
| 33 | `.claude/breaks/b239_records_changed_rows.sh` | 壊すプログラム（7-6 の F-6・新しいファイル） | 直した後の文字 |
| 34 | `.claude/breaks/b240_t44_s1_diff.sh` | 壊すプログラム（7-6 の F-7・新しいファイル） | 直した後の文字 |

<!-- 項目: 事実データ 名前=当てた記録（applied_fixes.json の名前 design:m2c15-laws-rows-20261103） -->
| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` | 当てた | 2026-11-04T09:11:45 |
| 2 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` | 当てた | 2026-11-04T09:11:45 |
| 3 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` | 当てた | 2026-11-04T09:11:45 |
| 4 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` | 当てた | 2026-11-04T09:11:45 |
| 5 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` | 当てた | 2026-11-04T09:11:45 |
| 6 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` | 当てた | 2026-11-04T09:11:45 |
| 7 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.py` | 当てた | 2026-11-04T09:11:45 |
| 8 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/法則一覧.md` | 当てた | 2026-11-04T09:11:45 |
| 9 | `.claude/tools/check_one_path.py` | 当てた | 2026-11-04T09:11:45 |
| 10 | `.claude/tools/check_one_path.py` | 当てた | 2026-11-04T09:11:45 |
| 11 | `.claude/state/req_trace_src.json` | 当てた | 2026-11-04T09:11:45 |
| 12 | `.claude/state/req_trace_src.json` | 当てた | 2026-11-04T09:11:45 |
| 13 | `.claude/state/req_trace_src.json` | 当てた | 2026-11-04T09:11:45 |
| 14 | `.claude/state/req_trace_src.json` | 当てた | 2026-11-04T09:11:45 |
| 15 | `.claude/state/req_trace_src.json` | 当てた | 2026-11-04T09:11:45 |
| 16 | `.claude/state/req_trace_src.json` | 当てた | 2026-11-04T09:11:45 |
| 17 | `.claude/state/req_trace_src.json` | 当てた | 2026-11-04T09:11:45 |
| 18 | `.claude/state/req_trace_src.json` | 当てた | 2026-11-04T09:11:45 |
| 19 | `.claude/state/req_trace_src.json` | 当てた | 2026-11-04T09:11:45 |
| 20 | `.claude/state/req_trace_src.json` | 当てた | 2026-11-04T09:11:45 |
| 21 | `.claude/breaks/b211_structure_need_missing.sh` | 当てた | 2026-11-04T09:11:45 |
| 22 | `.claude/breaks/b213_place_missing.sh` | 当てた | 2026-11-04T09:11:45 |
| 23 | `.claude/breaks/b228_laws_kubun_missing.sh` | 当てた | 2026-11-04T09:11:45 |
| 24 | `.claude/breaks/b230_records_changed_laws.sh` | 当てた | 2026-11-04T09:11:45 |
| 25 | `.claude/tools/pre_audit_check.py` | 当てた | 2026-11-04T09:11:45 |
| 26 | `.claude/tools/pre_audit_check.py` | 当てた | 2026-11-04T09:11:45 |
| 27 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md` | 当てた | 2026-11-04T09:11:45 |
| 28 | `.claude/breaks/b234_laws_row_missing.sh` | 当てた | 2026-11-04T09:11:45 |
| 29 | `.claude/breaks/b235_laws_form_missing.sh` | 当てた | 2026-11-04T09:11:45 |
| 30 | `.claude/breaks/b236_laws_reader_ref.sh` | 当てた | 2026-11-04T09:11:45 |
| 31 | `.claude/breaks/b237_laws_doc_changed.sh` | 当てた | 2026-11-04T09:11:45 |
| 32 | `.claude/breaks/b238_laws_source_diff.sh` | 当てた | 2026-11-04T09:11:45 |
| 33 | `.claude/breaks/b239_records_changed_rows.sh` | 当てた | 2026-11-04T09:11:45 |
| 34 | `.claude/breaks/b240_t44_s1_diff.sh` | 当てた | 2026-11-04T09:11:45 |

<!-- 項目: 事実データ 名前=実装の前と後の版（git） -->
- **実装の前**：commit bf699d9f
- **実装の後**：commit 8ed860d0。★この工事の中で、設計書の 4-4 の手順（G-1 の表の作り直しほか）の道具が、TARGET のファイルを書き出し直すことがある（例＝gen_materials.py --write が regime_detection_kb.md の件数の囲みを書き出す）。その行は実装の指示ではなく、設計書の 4-4・5 で照らす

<!-- 項目: 事実データ 名前=必読に要るファイル（道具が設計書と実装から拾った） -->
| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15） | 入れる |
| `.claude/breaks/b211_structure_need_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b213_place_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b228_laws_kubun_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b230_records_changed_laws.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b234_laws_row_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b235_laws_form_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b236_laws_reader_ref.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b237_laws_doc_changed.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b238_laws_source_diff.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b239_records_changed_rows.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b240_t44_s1_diff.sh` | 直す相手（TARGET） | 入れる |
| `.claude/state/req_trace_src.json` | 直す相手（TARGET） | 入れる |
| `.claude/tools/check_one_path.py` | 直す相手（TARGET） | 入れる |
| `.claude/tools/pre_audit_check.py` | 直す相手（TARGET） | 入れる |
| `SDK/.claude/rules/要件定義書_レベル4_指標の構造.md` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/indicators/indicators.json` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/laws/laws.json` | 直す相手（TARGET） | 入れる |
| `SDK/.claude/rules/法則一覧.md` | 新しく作るファイル（NEW_FILE） | 入れる |
| `SDK/scripts/priority_rebuild/laws/laws.py` | 新しく作るファイル（NEW_FILE） | 入れる |
| `SDK/scripts/priority_rebuild/recipes/identity_s1_legacy.json` | `.claude/tools/check_one_path.py` が名前を出す（実装の前後の差分） | 入れる |
| `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | `.claude/tools/check_one_path.py` が名前を出す（実装の前後の差分） | 入れる |
| `SDK/.claude/ratchet/exit_families_rules.json` | `.claude/tools/pre_audit_check.py` が名前を出す（実装の前後の差分） | 入れる |
| `SDK/scripts/priority_rebuild/e38_logics.json` | `.claude/tools/pre_audit_check.py` が名前を出す（実装の前後の差分） | 入れる |
| `SDK/scripts/priority_rebuild/indicators/indicators.py` | `.claude/tools/pre_audit_check.py` が名前を出す（実装の前後の差分） | 入れる |
| `SDK/scripts/priority_rebuild/engine_tuner_exec.py` | `SDK/scripts/priority_rebuild/laws/laws.py` が名前を出す（全文） | 入れない（この工事は変えません。--check-sources が FORM_SPEC を読むだけです（やらないことの Y-3）） |
| `SDK/scripts/priority_rebuild/observe_config.json` | `SDK/scripts/priority_rebuild/laws/laws.py` が名前を出す（全文） | 入れない（laws.py の選べる値の文に名前が出るだけで、この工事は変えません） |
| `SDK/scripts/priority_rebuild/recipes/search_limits.json` | `SDK/scripts/priority_rebuild/laws/laws.py` が名前を出す（全文） | 入れる |

<!-- 項目: 範囲の外 -->
- 守りの穴探し（すり抜けの道を新しく探すこと）は、範囲の外です。穴探しは、探すたびに新しい穴が出て、終わらないためです（恒久の決まり65番）。CC は、作業が実際に止まったときに、その穴を直します。
- 相場の法則51件と組み合わせの法則を入れないは、範囲の外です。195番の相手。
- 役割ごとの決まりの行を入れないは、範囲の外です。中身を決めるのは210番。
- engine_tuner のコードを直さない（engine_tuner_gen.py・engine_tuner_exec.py・observe_diag.py）は、範囲の外です。読む先を向けるのは196番・210番・211番。
- 写す元のファイルを直さない・消さない（search_limits.json・exit_families_rules.json・identity_s1_legacy.json・e38_logics.json）は、範囲の外です。読み手がまだ在る。消すのは162番。
- 指標の範囲（material_param_ranges）を写さないは、範囲の外です。211番の相手。
- ロングの売り方と枝を入れないは、範囲の外です。234番の横展開。
- 指標の役割の区分を変えない（RSI・基準線・BB%b は空のまま）は、範囲の外です。役割は教科書で確かめて222番で埋める。法則に合わせて変えない。
- 新しい法則の文と新しい数字を作らないは、範囲の外です。文と数は写す元から写す。例外は BB%b の閾値で、+2σ の旗（ddof=1）と BB%b（ddof=0）は同じ条件ではない。値は【新しく入る数字と式の一覧】の番号4 のとおり。列の比べは222番の試験 T47 で行う。
- 法則の中の数の範囲を埋めない（S1 の値の分）は、範囲の外です。S1_SL_倍率（sl_zone_k 0.5〜2.0）・S1_TP1_割合（tp1_frac 0.2〜0.8）ほかは e38_logics.json:474〜516 に出どころが在るが、この工事では入れない。M5（220番）がそこから写す。手数料の床ほか5行は探さない数。
- S2〜S5 の値と範囲を入れないは、範囲の外です。値は未確定（null）で、段⑤より前は S1 だけを通す。S2〜S5 は売り方の行（文・方向・計算の関数・指値の置き場）だけ。探す値の範囲を受ける欄は定義表に無いので、M3-1 で受ける。
- H2 と G2 の対象に laws.json を足さないは、範囲の外です。engine_tuner が読み始める196番で足す。

<!-- 項目: 問い 番号=Q0 優先度=A 理由=通らないのに進めると、抜けが後の工程まで残る 名前=作った後の確認を走らせて通るか -->
次のコマンドを走らせてください。`python3 .claude/tools/check_one_path.py --work m2c15-laws-rows-20261103`
「通らない」か「未作」の試験が在れば、その番号と理由を全部挙げてください。「見た範囲」と出た試験は、文字や数やハッシュ値を見ただけです。動きを確かめたとは読まないでください。

<!-- 項目: 問い 番号=Q1 優先度=A 理由=違えば、実装は設計書のとおりに作られていない 名前=実装の指示を当てた結果が、実装の後と1文字も同じか -->
設計書の 4-20 には、実装の指示が 34 件あります。
実装の前の対象のファイルに、この 34 件を番号の順に当ててください。実装の前の版は、事実データ「実装の前と後の版」の実装の前です。対象のファイルは、`.claude/breaks/b211_structure_need_missing.sh`・`.claude/breaks/b213_place_missing.sh`・`.claude/breaks/b228_laws_kubun_missing.sh`・`.claude/breaks/b230_records_changed_laws.sh`・`.claude/breaks/b234_laws_row_missing.sh`・`.claude/breaks/b235_laws_form_missing.sh`・`.claude/breaks/b236_laws_reader_ref.sh`・`.claude/breaks/b237_laws_doc_changed.sh`・`.claude/breaks/b238_laws_source_diff.sh`・`.claude/breaks/b239_records_changed_rows.sh`・`.claude/breaks/b240_t44_s1_diff.sh`・`.claude/state/req_trace_src.json`・`.claude/tools/check_one_path.py`・`.claude/tools/pre_audit_check.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/法則一覧.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.py`です。
当てた結果が、実装の後の版と1文字も同じかを確かめてください。実装の後の版は、事実データ「実装の前と後の版」の実装の後です。
確かめ方の例は、次のとおりです。まず、作業場に、git show で実装の前のファイルを出します。次に、直す前の文字を、直した後の文字に置き替えます。足す文字の指示なら、直す前の文字の後ろに、足す文字を足します。最後に、置き替えた結果と実装の後の版の差を、diff で取ります。

<!-- 項目: 問い 番号=Q2 優先度=A 理由=在れば、設計書に無い変更が実装に混ざっている 名前=実装の指示のどれにも当たらない行（設計書に無い変更）が無いか -->
実装の前の版と実装の後の版の差分を取ってください。実装の前の版は、事実データ「実装の前と後の版」の実装の前です。実装の後の版は、事実データ「実装の前と後の版」の実装の後です。差分を取るファイルは、`.claude/breaks/b211_structure_need_missing.sh`・`.claude/breaks/b213_place_missing.sh`・`.claude/breaks/b228_laws_kubun_missing.sh`・`.claude/breaks/b230_records_changed_laws.sh`・`.claude/breaks/b234_laws_row_missing.sh`・`.claude/breaks/b235_laws_form_missing.sh`・`.claude/breaks/b236_laws_reader_ref.sh`・`.claude/breaks/b237_laws_doc_changed.sh`・`.claude/breaks/b238_laws_source_diff.sh`・`.claude/breaks/b239_records_changed_rows.sh`・`.claude/breaks/b240_t44_s1_diff.sh`・`.claude/state/req_trace_src.json`・`.claude/tools/check_one_path.py`・`.claude/tools/pre_audit_check.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/法則一覧.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.py`です。
差分のうち、実装の指示のどれにも当たらない行が在るかを確かめてください。在れば、全部を挙げてください。

<!-- 項目: 問い 番号=Q3 優先度=A 理由=合わなければ、どの件を道具が当てたかを後から確かめられない 名前=当てた記録が、実装の指示の全部と1件ずつ合うか -->
当てる道具は、実装の指示を当てるたびに、`SDK/.claude/audits/applied_fixes.json` に記録を書きます。この工事の記録の名前は、`design:m2c15-laws-rows-20261103` です。
この記録が、実装の指示の 34 件と、番号と対象のファイルで1件ずつ合うかを確かめてください。
記録に「当てた」とも「もう当て終わっていた」とも書かれていない件が在るかを確かめてください。
「もう当て終わっていた」の件について、その件がどの実行で当たったかを確かめてください。確かめる材料は、当てる道具の出力と、git の差分です。

<!-- 項目: 問い 番号=Q4 優先度=B 理由=当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない 名前=承認した版の設計書どうしで、実装の指示が同じか -->
まこさんが承認した版の設計書の控えは、`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-laws-rows-20261103.md`です。
この控えの 4-20 の実装の指示と、監査の相手の設計書（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-laws-rows-20261103.md`。★比べる相手は、承認の控えです。`.claude/state/acceptance.md` は、後の工事の設計書で上書きされることがあるので、比べる相手にしません）の 4-20 の実装の指示が同じかを確かめてください。★2つが同じファイルを指すときは、控えのハッシュ値と、承認の印（`.claude/state/acceptance.approved`）の値と、控えのコミットの版が同じかを確かめてください。違うなら、その違いが実装に影響するかを答えてください。

<!-- 項目: 問い 番号=Q5 優先度=B 理由=要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない 名前=実装の指示が、やることの表の要件を全部 満たすか -->
やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-laws-rows-20261103/やることの表.md`）の一覧には、この工事でやることが書いてあります。
実装の指示が、この一覧のやることを全部満たすかを確かめてください。
一覧に在るのに実装の指示に無い物と、実装の指示に在るのに一覧に無い物を、全部挙げてください。

<!-- 項目: 問い 番号=Q6 優先度=A 理由=成り立たなければ、完成の根拠が無い。新しく作る壊すプログラムは承認のときに走らせられず、7-6 の状態は未着手のまま残る 名前=完成の条件が、実装の後に本当に成り立つか -->
設計書の完成の条件の表には、14 行の条件が書いてあります。
この条件が、実装の後に本当に成り立つかを確かめてください。
各行のコマンドを、作業場で走らせるか、読むだけの形で走らせてください。コマンドの中のパスは、`SDK` のフォルダからの相対です。そのため、どのコマンドも `SDK` のフォルダで走らせます。
走らせるコマンドは、次のとおりです。`jq -e '(reduce .["法則の行"][] as $r (0; .+1))==40 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="決済の枝" then .+1 else . end))==31 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="売り方" then .+1 else . end))==5 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="建てる前の確認" then .+1 else . end))==1 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="玉全体の決済" then .+1 else . end))==2 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="玉の持ち方" then .+1 else . end))==1' scripts/priority_rebuild/laws/laws.json`・`jq -e '(reduce .["条件の書き方"][] as $r (0; .+1))==13 and (reduce .["玉の状態"][] as $r (0; .+1))==9 and (reduce .["法則の中の数"][] as $r (0; .+1))==50' scripts/priority_rebuild/laws/laws.json`・`python3 scripts/priority_rebuild/laws/laws.py --selftest`・`python3 scripts/priority_rebuild/laws/laws.py --verify`・`python3 scripts/priority_rebuild/laws/laws.py --check-sources`・`T=$(mktemp) && git show cbde6ab2:v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json > "$T" && jq -e --slurpfile o "$T" '(reduce .["使い方の記録"][] as $r (0; .+1))==20 and $o[0]["使い方の記録"]==.["使い方の記録"][0:16] and $o[0]["指標の記録"]==.["指標の記録"] and $o[0]["部品の記録"]==.["部品の記録"]' scripts/priority_rebuild/indicators/indicators.json`・`T=$(mktemp) && python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/check_one_path.py --test T44 > "$T"; grep -q '通る 1 件' "$T"`・`python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/gen_req_trace.py --check`・`jq -e --slurpfile l scripts/priority_rebuild/laws/laws.json '((reduce range(1;31) as $i ([]; . + ["\($i)"])) - (reduce (.["要素の定義表"]["要素"][]["根拠"]["構造に要ること"][], $l[0]["要素の定義表"]["要素"][]["根拠"]["構造に要ること"][]?) as $n ([]; . + ["\($n)"])) - (reduce path(.["要素の定義表"]["この表で受けない要ること"][]) as $p ([]; . + [$p[2]]))) == []' scripts/priority_rebuild/indicators/indicators.json`・`jq -e --slurpfile l scripts/priority_rebuild/laws/laws.json '(["使い方の記録","指標の記録","部品の記録"] - [.["要素の定義表"]["要素"][]["置く記録"]]) == [] and (reduce $l[0]["要素の定義表"]["要素"][] as $r (0; if $r["置く記録"]=="法則の記録" then .+1 else . end))==10' scripts/priority_rebuild/indicators/indicators.json`・`jq -e '.["要素の定義表"]["選べる値"]["区分"]==["相場の法則","組み合わせの法則","売り方","建てる前の確認","決済の枝","玉全体の決済","玉の持ち方","役割ごとの決まり"]' scripts/priority_rebuild/laws/laws.json`・`T=$(mktemp) && git show 1f6f5ff9:v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json > "$T" && jq -e --slurpfile o "$T" '$o[0]["指標の記録"]==.["指標の記録"] and $o[0]["使い方の記録"]==.["使い方の記録"][0:16] and $o[0]["部品の記録"]==.["部品の記録"]' scripts/priority_rebuild/indicators/indicators.json`・`grep -c -e 'laws/laws.py' -e 'check_one_path.py --test T44' /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py`・`! grep -q '法則の行を入れるのは 209番と 195番' .claude/rules/要件定義書_レベル4_指標の構造.md`

<!-- 項目: 問い 番号=Q8 優先度=A 理由=この22件は道具の記録に残らないので、抜けていても機械では分かりません。抜けていると、監査の指摘が直らないまま次の工事へ進みます。 名前=当てた記録に無い修正22件は、設計書と実装に入っているか -->
次の3つを確かめてください。
1つ目に、修正1・2・3・4・6・7・8・9・10・11・12・13・14・15・16・17・18・21・23・24・28・32 の中身が、設計書の該当の節か実装の指示に入っているかを、修正ごとに1行で答えてください。修正4 は案B です。
2つ目に、経緯に書いた CC の変更（修正13 の22行・修正9 の後半・修正14 の相手・修正20 の36行）で、ほかの修正の中身が変わっていないかを答えてください。
3つ目に、修正1・2・3・7・8 が CP100 で測った壊し方で、いま止まるかを写しで答えてください。CP100 の4節の Q8 の表の壊し方と、Q9 の止める操作と足す操作です。

<!-- 項目: 問い 番号=Q9 優先度=A 理由=実物が実装の指示と違うと、承認された形と違う物の上に、195番以降の工事を積むことになります。 名前=実物は、実装の指示34件のとおりか -->
次の2つを確かめてください。
1つ目に、実装の指示の「直した後の文字」が、実物に1文字も違わず在るかを、実装ごとに1行で答えてください。
2つ目に、実装の指示に無い変更が、直すファイル（TARGET と NEW_FILE）に無いかを答えてください。基準は commit bf699d9f です。req_trace_src.json の割り当て22行の「済＝208番」と、法則の中の数の出どころ2行（と法則一覧.md の同じ2行）は、経緯に書いた変更です。

<!-- 項目: 問い 番号=Q10 優先度=A 理由=CC は自分で判定しません。CC の結果を監査が走らせ直さないと、確かめた人がいないことになります。 名前=完成の条件と試験は、設計書のとおりに動くか -->
次の4つを確かめてください。
1つ目に、完成の条件の14行のコマンドを走らせ、結果を行ごとに答えてください。
2つ目に、壊すプログラム7本を run_breaks.py --design <設計書> --measure-only で走らせ、結果を答えてください。
3つ目に、b213 を run_breaks.py --design <前の工事の設計書 m2c15-indicator-structure-20261031.md> --measure-only --only b213_place_missing.sh で走らせ、結果を答えてください。
4つ目に、indicators.py --count の結果が、指標の記録・部品の記録・列を作る組について、commit bf699d9f の時と同じで、使い方の記録だけが 16 から 20 になっているかを答えてください。

<!-- 項目: 問い 番号=Q11 優先度=B 理由=設計書と違う手順で確かめた結果を、そのまま完成の根拠にできないためです。 名前=実装で設計書と違った点の扱いは、正しいか -->
次の3つを確かめてください。
1つ目に、当てる道具が後半を走らせなかったことで、確かめに抜けが出ていないかを答えてください。g2_pass.json と h2_pass.json の対象のハッシュ値が、いまの実物と合うかを照らしてください。
2つ目に、法則の中の数の出どころの欄が、値の在る行を指しているかを、全部の行で答えてください。経緯に書いて直した2行のほかにも、説明の文の行を指す行が在れば挙げてください。
3つ目に、laws_rows_build.py --unused-keys の一覧のうち、理由の文が実物と合わない鍵が無いかを答えてください。売買の動きに効く鍵を「効かない」と書いた行が無いかを見てください。

<!-- 項目: 外部検索 名前=区分ごとに欄が違う記録を1つの表で持つ作り -->
検索の言葉：JSON schema discriminated union type specific fields metadata driven rule engine
調べる物：種類ごとの欄を定義表で持ち、読む口がそれを読む作りが、外の一般の作り方と合うか。新しく Web は開いていない。実装の監査では、この出どころと、実装の該当の所が合うかを照らします

<!-- 項目: 外部検索 名前=売買ルールをデータで持つ作り -->
検索の言葉：declarative trading strategy rule definition exit branch data driven backtest framework
調べる物：入口と決済の枝をデータの行で持つ作りが、外の一般の作り方と合うか。新しく Web は開いていない。実装の監査では、この出どころと、実装の該当の所が合うかを照らします


<!-- 項目: 自己申告 -->
**測っていない見積もり**：当てる・完成の条件。見込みは、数分の見込みです。根拠は、写しで当てた結果。時間は測っていないです。

<!-- 項目: 自己申告 -->
**この工事の外の作業中の変更**：次のファイルには、作業中の変更があります。`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`。この変更は、この工事の実装の指示が当てた物ではありません。そのため、Q1 と Q2 の差分を、この工事の対象のファイルだけで取ってください。

<!-- gen_audit_docs request-design kind=impl work=m2c15-indicator-redirect-20261031 design_sha256=52996fb4219e81271595f19ae8839f26af14e10fb3f8dd7c6b644f5a4a98ef86 src_sha256=d0415098b3fe8cbcbb8b7761415873b524ea8a3e317e6386e8de73c75c531149 body_sha256=ba25d410f9fa9942e0f6d5fc43106f2622b6a39e760a75452330a0bf93840963 -->
<!-- 項目: メタ -->
日付: 2026-11-01
task: m2c15_indicator_redirect_20261031_impl
cp: cp95
題: CP95 — 161-1＝読む口を作り、indicators.json を要素の定義表の形で写し直す。build_catalog の向け直しは161-2。ToDo の161番・172番の中身・M2-C-15（実装の監査）
依頼者: CC（起案者）
監査の種類: 実装の監査
監査対象タスク: M2-C-15／設計書 m2c15-indicator-redirect-20261031
監査の相手: .claude/state/acceptance.md
売買に触るか: はい
直す相手: `.claude/breaks/b215_reader_off_element.sh`・`.claude/breaks/b216_reader_choice_check.sh`・`.claude/breaks/b217_draft_range_not_copied.sh`・`.claude/breaks/b218_draft_hidden_rows_missing.sh`・`.claude/breaks/b219_probe_direct_read.sh`・`.claude/breaks/b220_reader_calc_from_registry.sh`・`.claude/breaks/b221_draft_rep_by_position.sh`・`.claude/state/indicator_review/gen_fix_inventory.py`・`.claude/state/indicator_review/gen_indicators_draft.py`・`.claude/state/indicator_review/ss_outside_probe.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json`

<!-- 項目: 作業場の指示 -->
写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp95_work/` に作る。必要なファイルは自分で開き、写しで走らせて確かめる。

<!-- 項目: 修正をどこに書くか -->
実装が設計書と違う所の修正は、その実装のファイルに書いてください。修正を当てるプログラムが、その修正を当てます。
ただし、修正を当てるプログラムは、.claude/hooks と .claude/tools と .claude/breaks のファイルには当てません。そのファイルの修正は、CC が書きます。
設計書の誤りの修正は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-indicator-redirect-20261031/やることの表.md`）に書いてください。設計書はプログラムが作るので、設計書に直接書けません。

<!-- 項目: 目的と経緯 -->
1. **この工事は何のためか**：この工事は、指標の情報を1つにまとめたデータ（indicators.json）を、読む口 indicators.py からだけ読める状態にします。
   - 作った物の1つ目は、要素の定義表を読み、決まり5つを守って要素を返す読む口です。
   - 作った物の2つ目は、23の欄の古い形の記録を、要素の定義表の形（②指標の記録・③使い方の記録・④部品の記録）へ写し直す写すプログラムです。
   - 作った物の3つ目は、写し直した indicators.json です。
   - 目的は、指標の工事のゴール1とゴール2のうち、読む口と写し直しの段を終えることです。ゴール1は、指標の情報を1つのデータに集約して、そこからしか取れない状態にすることです。ゴール2は、そのデータの形を、機能要件に合う形に直すことです。
   - 列を作る所（build_catalog）を読む口へ向けるのは、次の工事（161-2）です。
   - 設計書の監査 CP94 の修正31件を、全部入れました。修正1 は案B です。案B は、資料の表の名前が軸に合わない値を「まだ決めていない」にし、対応を70番の T-3 で決める形です。
2. **この工事は何か**：この工事の中身は、設計書の「§1 概要」に書いてあります。実装の指示の一覧は、事実データの表に載せました。やることの番号は、M2-C-15です。
   **この工事の位置**：目標からこの工事までのつながりは、次のとおりです。全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝指標の構造の工事（ゴール1〜3）。指標の情報を1つのデータに集め、形を要件に合わせ（worklog 20261030 §17-1 の A〜C）、法則を1つのデータにまとめる（同 D）。全体のマイルストーンでは①の中で行う → この工事
3. **この工事が結ぶ要件**：M2-C-15＝この工事が満たす要件は、要件定義の次の3つです。3番：指標・閾値・パラメータ・時間足が、それぞれの役割に沿って使われ、閾値とパラメータが範囲から探されていること。4番と5番：最初の段階では、閾値とパラメータを、戦略ごとの代表の固定値にして探すこと。6番：指標は1か所から呼び出すこと。教科書と法則の誤りは、1か所を直せば全部に届くこと。（出どころ＝やることリスト m2_todo.json の「結ぶ要件」）
4. **経緯**：この監査に至るまでの経緯は、次のとおりです。
   - 前の監査（設計書の監査 CP94・2026-10-31）の結論は、CONDITIONAL-GO でした。修正の指示は31件です（Critical 6・Major 13・Minor 9・Process 3）。
   - 大きな誤りは2つでした。C-1 は、代表の値を並びの番号で軸に割り当てていたため、KSTシグナル・KAMA傾き% ほか8種の値が、別の軸に入るか空になることです。C-2 は、いまの engine_tuner が範囲で探している名前に出る軸19本が「まだ決めていない」になり、171番の後に探せなくなることです。
   - まこさんは、31件を全部入れると決めました（2026-11-01）。修正1 は案B で、資料の表の名前が軸に合わない値は「まだ決めていない」にし、対応は70番の T-3 で決めます。ほかの案の選び方は、Q10 に書きました。
   - この決定で、設計は2か所変わりました。1つ目に、代表の値を、並びの番号でなく、資料の表の名前で軸に合わせる形になりました（C-1）。2つ目に、名前に出る軸の範囲を、いまの engine_tuner と同じ決まりで写し、写すプログラムの --verify で照らす形になりました（C-2）。
   - 実装の後に、CC は問題を2つ見つけました。1つは、写すプログラムの自己テストの1本が、indicators.json を書き替えた後にいつも落ちることです（Q8 の自己申告1）。もう1つは、合わない隠れた数字の軸47本に、案の文と違って、いまの値が入っていることです（Q8 の自己申告5）。
   - 2つ目の問題は、まこさんが OK した案の文と、コードの食い違いです。まこさんは、ほかにも同じ食い違いが在りうると考えています。そのため、修正31件を1件ずつ確かめる問い（Q10）と、指標の構造の要件定義書の要件どおりかを確かめる問い（Q11）を足しました。

<!-- 項目: 着手前必読 -->
**パスは、リポジトリの根（`cat-bitget/`）からの相対です。**`SDK` は、`v3-bitget-api-sdk/bitget-python-sdk-api` の略です。

1. `.claude/state/acceptance.md` — 監査の相手の設計書です。プログラムが作りました。
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-indicator-redirect-20261031.md`（全文） — まこさんが承認した版の設計書の控えです。どの版の 4-20 で当てたかは、Q4 で照らします。このファイルは、承認された設計書の控えです。処理の流れは 4-4（:395-404）、出る結果の姿は 4-12（:491-506）、実装の指示12件は 4-20（:621-4056）、完成の条件7行は 7-6（:4297-4317）に在ります。
3. `SDK/.claude/audits/applied_fixes.json` — 当てる道具が書いた、当てた記録です。この工事の行の名前は design:m2c15-indicator-redirect-20261031 です。
4. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-indicator-redirect-20261031/やることの表.md` — 設計書の元（やることの表）です。監査人は、修正の指示をこのファイルに書きます。
5. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — このファイルには、目標と全体戦略とハード制約が書いてあります。目標は、全月 net ≥ $1,900 です。
6. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-232） — このファイルには、engine_tuner の目的と、探し方の要件と、作ってはいけない物が書いてあります。
7. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:130-152） — このファイルには、M2 が M1〜M6 のどこに当たるかが書いてあります。
8. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:81-109） — このファイルには、M2 で作っている物が書いてあります。この工事は、M2-C-15（指標の工事）の1つです。
9. `SDK/.claude/ratchet/acceptance_archive/verbatim/m2c15-indicator-redirect-20261031/impl_4-20_20261031.json`（全文） — このファイルには、実装の指示12件の中身が在ります。設計書の 4-20 と同じ物です（Q8・Q9）。
10. `SDK/scripts/priority_rebuild/indicators/indicators.py`（全文） — このファイルは、実装1 で新しく作った読む口です（Q8）。
11. `.claude/state/indicator_review/gen_indicators_draft.py`（全文） — このファイルは、実装2 で全文を置き替えた写すプログラムです。落ちる自己テストの1本は :1693-1700 に在り、本物の要素の定義表を読む所は :1593 です（Q8）。
12. `.claude/state/indicator_review/gen_fix_inventory.py`（:30・:79-83） — このファイルは、実装3 と実装4 で直した一覧を作るプログラムです。ROOT（:30）と、名前を読む口から読む所（:79-83）です（Q8）。
13. `.claude/state/indicator_review/ss_outside_probe.py`（:28-33） — このファイルは、実装5 で直した数える道具です。名前を読む口から読む所です（Q8）。
14. `SDK/scripts/priority_rebuild/indicators/indicators.json`（:1-3・:1772・:20614-21697・:38431-39066・:98803-99168・:99169-99491・:101372-101941） — このファイルは、4-4 の2 で写すプログラムが書き替えた相手です。一番外の鍵（:2・:3・:1772・:98803・:99169）、KSTシグナル（:20614-）、RSI（:38431-）、使い方の記録（:98803-）、帯VA（:99170-）、帯スイング（:101372-）の行です（Q8）。
15. `.claude/breaks/b215_reader_off_element.sh`（全文） — 新しい壊すプログラムです。完成の条件1 を守ります（Q9）。
16. `.claude/breaks/b216_reader_choice_check.sh`（全文） — 新しい壊すプログラムです。完成の条件2 を守ります（Q9）。
17. `.claude/breaks/b220_reader_calc_from_registry.sh`（全文） — 新しい壊すプログラムです。完成の条件3 を守ります（Q9）。
18. `.claude/breaks/b217_draft_range_not_copied.sh`（全文） — 新しい壊すプログラムです。完成の条件4 を守ります（Q9）。
19. `.claude/breaks/b218_draft_hidden_rows_missing.sh`（全文） — 新しい壊すプログラムです。完成の条件5 を守ります（Q9）。
20. `.claude/breaks/b219_probe_direct_read.sh`（全文） — 新しい壊すプログラムです。完成の条件6 を守ります（Q9）。
21. `.claude/breaks/b221_draft_rep_by_position.sh`（全文） — 新しい壊すプログラムです。完成の条件7 を守ります（Q9）。
22. `.claude/breaks/lib.sh`（:21-23・:29-101） — 壊すプログラムが使う guard・measure・finish です。壊したファイルを必ず戻す所です（Q9）。
23. `.claude/state/indicator_review/fix_inventory_20261024.md`（:1-5・:1799） — このファイルは、4-4 の3 で作り直した直す相手の一覧です。:1799 は、設計書の 4-19 の F-4 の例（LINEAGE_KINDS の行）です（Q8）。
24. `.claude/state/session_worklog_20261101.md`（:24-78・:100-174） — この工事の230回目と231回目の経緯です。§2 には、監査 CP94 の修正の直す範囲と案の決定（§2-4・§2-7）と、直し方（§2-5〜§2-10）が書いてあります。§4 には、承認・実装・4-4 の1〜5 の結果・見つけた食い違いが書いてあります（Q10）。
25. `SDK/.claude/audits/2026-10-31_m2c15_indicator_redirect_20261031_design_cp94_audit_report.md`（:394-416・:417-908） — このファイルは、設計書の監査 CP94 の結果です。総合判定（:394〜）と、修正の指示31件（8番の節 :417〜・9番の節 :862〜）が在ります（Q10）。
26. `SDK/.claude/ratchet/acceptance_archive/verbatim/m2c15-single-source-fix-20261023/m2c15_指標の構造_要件定義書.md`（全文） — このファイルは、指標の構造の要件定義書です。3つのゴール・構造の案（A〜F）・構造に要ることの30件・直す物の一覧・ToDo の順番が書いてあります（Q11）。
27. `.claude/rules/core_requirements_full.md`（全文） — このファイルは、要件定義の全文です。3番は機能要件、4番は探し方、5番は代表の固定値と範囲の定義、6番と7番は指標の呼び方と直し方、8番は作ってはいけない物です（R0・Q11）。

<!-- 項目: 範囲の中 -->
- 監査の相手は、`.claude/state/acceptance.md` です（設計書 `m2c15-indicator-redirect-20261031`・実装の監査）。当てる道具が、設計書の実装の指示のとおりに実装を作れているかを確かめます。
- 直す相手は、`.claude/breaks/b215_reader_off_element.sh`・`.claude/breaks/b216_reader_choice_check.sh`・`.claude/breaks/b217_draft_range_not_copied.sh`・`.claude/breaks/b218_draft_hidden_rows_missing.sh`・`.claude/breaks/b219_probe_direct_read.sh`・`.claude/breaks/b220_reader_calc_from_registry.sh`・`.claude/breaks/b221_draft_rep_by_position.sh`・`.claude/state/indicator_review/gen_fix_inventory.py`・`.claude/state/indicator_review/gen_indicators_draft.py`・`.claude/state/indicator_review/ss_outside_probe.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` です。
- この工事は、売買のロジックに触る工事です。engine_tuner の目的は、まこさんの言葉で「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的」です（まこさん確定 2026-08-06）。

<!-- 項目: 事実データ 名前=設計書の実装の指示の一覧（4-20・当てる道具が当てる相手） -->
| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 読む口（F-1・新しいファイル）＝要素の定義表を読み、決まり5つを守って②③④の要素を返す。読む口が使う要素は要素の定義表の番号から名前を引く（監査 CP94 の修正11）。列を作る組を返す口（161-2 の build_catalog が使う・決まり⑤の外・監査 CP94 の修正12）を持つ。計算の関数の本体は持たず（R8）、記録の計算の関数の登録の名前で、観察の道具の計算の登録から取って返す口（calc・value）を持つ | 直した後の文字 |
| 2 | `.claude/state/indicator_review/gen_indicators_draft.py` | 写すプログラムの全文（F-2・F-3）＝要素の定義表の形で②③④へ写す。23の欄を全部読む。置き場は名前で探す。隠れた数字を②④の軸へ写す。代表の値は資料の表の名前で軸に合わせ、合わない軸は「まだ決めていない」にして合わない値の一覧を出す（監査 CP94 の修正1・まこさん「案B」）。写す元から作り直して書き替える口（--rewrite・162番までは新しい形にも使う＝修正14 案B）と自己テスト（--selftest）を持つ | 直した後の文字 |
| 3 | `.claude/state/indicator_review/gen_fix_inventory.py` | 一番上の ROOT（F-4）＝写しで確かめるときに IND_ROOT で写しの一番上を渡せる形にする（ss_outside_probe.py の SS_ROOT と同じ） | 直した後の文字 |
| 4 | `.claude/state/indicator_review/gen_fix_inventory.py` | 名前の読み元（F-4）＝indicators.json を直に開く2行を、読む口 indicators.py から読む形にする（R5） | 直した後の文字 |
| 5 | `.claude/state/indicator_review/ss_outside_probe.py` | 名前の読み元（F-5）＝indicators.json を直に開く行と INDICATOR_TABLE から読む行を、読む口 indicators.py から読む形にする（R5） | 直した後の文字 |
| 6 | `.claude/breaks/b215_reader_off_element.sh` | 壊すプログラム b215（7-6 の F-1 の1行目）＝読む口の決まり③の判定を外すと、読む口の自己テストが落ちる（新しいファイル） | 直した後の文字 |
| 7 | `.claude/breaks/b216_reader_choice_check.sh` | 壊すプログラム b216（7-6 の F-1 の2行目）＝読む口の決まり④の照らしを外すと、読む口の自己テストが落ちる（新しいファイル） | 直した後の文字 |
| 8 | `.claude/breaks/b217_draft_range_not_copied.sh` | 壊すプログラム b217（7-6 の F-2）＝範囲を②のパラメータの軸へ写す所を外すと、写すプログラムの自己テストが落ちる（新しいファイル） | 直した後の文字 |
| 9 | `.claude/breaks/b218_draft_hidden_rows_missing.sh` | 壊すプログラム b218（7-6 の F-3）＝隠れた数字のうち rows を写さない形にすると、写すプログラムの自己テストが落ちる（新しいファイル） | 直した後の文字 |
| 10 | `.claude/breaks/b219_probe_direct_read.sh` | 壊すプログラム b219（7-6 の F-4・F-5）＝ss_outside_probe.py に indicators.json を直に読む行を戻すと、grep が当たって落ちる（新しいファイル） | 直した後の文字 |
| 11 | `.claude/breaks/b220_reader_calc_from_registry.sh` | 壊すプログラム b220（7-6 の F-1 の3行目）＝読む口の計算の口が計算の登録から関数を取らない形にすると、読む口の自己テストが落ちる（新しいファイル） | 直した後の文字 |
| 12 | `.claude/breaks/b221_draft_rep_by_position.sh` | 壊すプログラム b221（7-6 の F-3 の2行目・監査 CP94 の修正1・修正2）＝代表の値を並びの番号で軸に割り当てる形に戻すと、写すプログラムの自己テストが落ちる（新しいファイル） | 直した後の文字 |

<!-- 項目: 事実データ 名前=当てた記録（applied_fixes.json の名前 design:m2c15-indicator-redirect-20261031） -->
| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 当てた | 2026-11-01T08:58:01 |
| 2 | `.claude/state/indicator_review/gen_indicators_draft.py` | 当てた | 2026-11-01T08:58:01 |
| 3 | `.claude/state/indicator_review/gen_fix_inventory.py` | 当てた | 2026-11-01T08:58:01 |
| 4 | `.claude/state/indicator_review/gen_fix_inventory.py` | 当てた | 2026-11-01T08:58:01 |
| 5 | `.claude/state/indicator_review/ss_outside_probe.py` | 当てた | 2026-11-01T08:58:01 |
| 6 | `.claude/breaks/b215_reader_off_element.sh` | 当てた | 2026-11-01T08:58:01 |
| 7 | `.claude/breaks/b216_reader_choice_check.sh` | 当てた | 2026-11-01T08:58:01 |
| 8 | `.claude/breaks/b217_draft_range_not_copied.sh` | 当てた | 2026-11-01T08:58:01 |
| 9 | `.claude/breaks/b218_draft_hidden_rows_missing.sh` | 当てた | 2026-11-01T08:58:01 |
| 10 | `.claude/breaks/b219_probe_direct_read.sh` | 当てた | 2026-11-01T08:58:01 |
| 11 | `.claude/breaks/b220_reader_calc_from_registry.sh` | 当てた | 2026-11-01T08:58:01 |
| 12 | `.claude/breaks/b221_draft_rep_by_position.sh` | 当てた | 2026-11-01T08:58:01 |

<!-- 項目: 事実データ 名前=実装の前と後の版（git） -->
- **実装の前**：commit f1fd2c28（依頼書を作った時点の HEAD。承認の控えをまだ commit していないので、実装の前はこの commit の版。`git show f1fd2c28:<パス>` で出せる。★この後に commit しても、この番号で出せる）
- **実装の後**：依頼書を作った時点の作業中の変更（まだ commit していない。`git diff f1fd2c28 -- <パス>` で見られる。★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、`git diff f1fd2c28 <その commit> -- <パス>` で見る）。★この工事の中で、設計書の 4-4 の手順（G-1 の表の作り直しほか）の道具が、TARGET のファイルを書き出し直すことがある（例＝gen_materials.py --write が regime_detection_kb.md の件数の囲みを書き出す）。その行は実装の指示ではなく、設計書の 4-4・5 で照らす

<!-- 項目: 事実データ 名前=必読に要るファイル（道具が設計書と実装から拾った） -->
| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15） | 入れる |
| `.claude/breaks/b215_reader_off_element.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b216_reader_choice_check.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b217_draft_range_not_copied.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b218_draft_hidden_rows_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b219_probe_direct_read.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b220_reader_calc_from_registry.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b221_draft_rep_by_position.sh` | 直す相手（TARGET） | 入れる |
| `.claude/state/indicator_review/gen_fix_inventory.py` | 直す相手（TARGET） | 入れる |
| `.claude/state/indicator_review/gen_indicators_draft.py` | 直す相手（TARGET） | 入れる |
| `.claude/state/indicator_review/ss_outside_probe.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/indicators/indicators.json` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/indicators/indicators.py` | 新しく作るファイル（NEW_FILE） | 入れる |
| `SDK/.claude/ratchet/indicator_switch.json` | `.claude/state/indicator_review/gen_indicators_draft.py` が名前を出す（実装の前後の差分） | 入れない（写す元（指標のオン/オフ）です。この工事は変えていません。写した値は、写すプログラムの --verify が写す元と照らします（違い0件）） |
| `SDK/scripts/priority_rebuild/engine_tuner_exec.py` | `.claude/state/indicator_review/gen_indicators_draft.py` が名前を出す（実装の前後の差分） | 入れない（写すプログラムは、時間帯の材料（時刻・曜日）の注記と出どころの文に、このファイルの名前を書くだけで、読み込みません（gen_indicators_draft.py:701・:756・:1196）。この工事は変えていません。読む所を読む口へ向け直すのは、後の工事（171番・やらないことの Y-1）です） |
| `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | `.claude/state/indicator_review/gen_indicators_draft.py` が名前を出す（実装の前後の差分） | 入れない（写すプログラムが、名前に出る軸の範囲の照らし（material_ranges・gen_indicators_draft.py:1385）と、出口の水準の定数（_EXIT_LEVEL_CONST・:563）を読む写す元です。この工事は変えていません。写した値は、写すプログラムの --verify が写す元と照らします（違い0件）。読む所を読む口へ向け直すのは、後の工事（171番・やらないことの Y-1）です） |
| `.claude/state/indicator_review/gen_params_in_name.py` | `.claude/state/indicator_review/gen_indicators_draft.py` が名前を出す（実装の前後の差分） | 入れない（写すプログラムが、隠れた数字の測り方（measure）を読む172番の道具です。この工事は変えていません。測った数（相手 64種・隠れた数字を持つ記録 66）は、--rewrite と --verify の画面に出ます） |
| `.claude/state/indicator_params_by_strategy.json` | `.claude/state/indicator_review/gen_indicators_draft.py` が名前を出す（実装の前後の差分） | 入れない（写す元（資料の表の代表の値と範囲）です。この工事は変えていません。写した値は、写すプログラムの --verify が写す元と照らします（違い0件）） |
| `SDK/scripts/priority_rebuild/observe_config.json` | `.claude/state/indicator_review/gen_indicators_draft.py` が名前を出す（実装の前後の差分） | 入れない（写す元（列を作る値の material_params と、名前に出ない軸の最初の値の material_first_hidden）です。この工事は変えていません。写した値は、写すプログラムの --verify が写す元と照らします（違い0件）） |
| `SDK/scripts/priority_rebuild/observe_diag.py` | `.claude/state/indicator_review/gen_indicators_draft.py` が名前を出す（実装の前後の差分） | 入れない（設計書の DESIGN_CONTRACT（承認の道具が照らす相手の設定）に名前が出るだけで、この工事は1文字も変えていません。監査に出す前のチェックの照合（verify_design_contract.py --diff）は rc 0 でした） |
| `SDK/scripts/priority_rebuild/recipes/search_limits.json` | `.claude/state/indicator_review/gen_indicators_draft.py` が名前を出す（実装の前後の差分） | 入れない（写す元（名前に出る軸の範囲）です。この工事は変えていません。写した値は、写すプログラムの --verify が写す元と照らします（違い0件）） |

<!-- 項目: 範囲の外 -->
- 守りの穴探し（すり抜けの道を新しく探すこと）は、範囲の外です。穴探しは、探すたびに新しい穴が出て、終わらないためです（恒久の決まり65番）。CC は、作業が実際に止まったときに、その穴を直します。
- engine_tuner の経路の7本（observe_diag.py のほかの関数・engine_tuner_exec.py・engine_tuner_gen.py・indicator_reference_diag.py・e38.py・e38_logic_parts.py・leak_causality_diag.py・enforce_g2_pass.py）を、読む口へ向け直さないは、範囲の外です。171番で行う。161番は元の置き場を消さないので、この7本は161番の後も、いまの置き場（設定ファイル・INDICATOR_TABLE ほか）を読める。
- 残りの道具・採点・診断の24本を、読む口へ向け直さない（F-4・F-5 の2本を除く）は、範囲の外です。170番で行う。
- 元の置き場を消さない（INDICATOR_TABLE・_r・_reg の名前と型・observe_config.json の指標の部分・search_limits.json の範囲・indicator_switch.json・資料の表3つ）は、範囲の外です。162番で行う。161番の写すプログラムは、これらを写す元として読む。
- 列の名前を変えない。隠れた数字は、列の名前に出さず、②のパラメータの軸に持つだけにするは、範囲の外です。192番の要素 ②-4 で、列の名前の型は、成績表と列の名前で照らすために171番まで保つと決めた。要件 :55（指標の名前に値を入れない）。engine_tuner が隠れた数字を範囲で探せるのは、171番で探す側が記録を読むようになり、M2-E-8 で最後の段階を作った後。
- 監査 CP91 の修正5・6（監査の前の検査の、分かっている一覧と出力の sha）・8・9（成績表を列の名前で引く）・10（Keltner の照合の ATR の本数）を、161番では当てないは、範囲の外です。どれも、隠れた数字を列の名前に出す直しに付いた修正で、列の名前か設定の塊が変わるときに起きる（CP91 の結果:441〜530 の根拠の行）。161番は、列の名前も設定の塊も変えないので当たらない。列の名前を変える171番で受ける。修正18（当てた後に監査の前の検査が通るか）は、161番の完成の条件には入れず、承認の後の 4-4 の5（まこさんの OK の後）で走らせる（scripts の下で直す .py は新しい読む口だけで、材料の検査と check_indicator_sources.py は indicators.json を読まない＝監査 CP94 の grep）。★10-30 の ToDo の案（161番＝CP91 の 1〜4・19・5・6・18・8・9・10・worklog 20261030:1308）から、割り当てを変える。
- 閾値の値・範囲・代表の値を、新しく調べて埋めない。③使い方の記録に、使い方を1種ずつ決めて閾値を写すこともしないは、範囲の外です。70番（T-2・T-3）で行う。161番は、いまのデータが使い方を決めている4種だけを写す（F-2）。
- 置き場どうしで値が違う物を、CC がどちらかに決めないは、範囲の外です。R11。食い違いの記録は、そのまま②の照らしと出どころへ写す。
- 法則の記録（⑤）を作らない。法則のデータを移さないは、範囲の外です。195番で行う。
- ローソクの形の4種をオンにしないは、範囲の外です。194番で行う。
- E の記録（型・出口の枝・指標でない数の値・上位足の並べ方）と、F（機械学習のモデル）の要素を作らないは、範囲の外です。2026-10-30 の決定（192番の Y-6・Y-7 と同じ）。
- 計算の関数の本体（各指標の式）を直さないは、範囲の外です。R8（記録は関数の名前で指すだけ）。式の正しさは70番の T-1 で見る。
- 型の表の、役割ごとの時間足を③へ移さないは、範囲の外です。型の表は承認の指紋つき（gen_signal_families.py:229〜298）で、移すと再承認が要る。197番で行う。
- 成績表（material_ranking.json）を作り直さないは、範囲の外です。M2-D-8 で行う。161番は列の名前を変えないので、成績表はいまのまま引ける。
- 閉じた工事の壊すプログラム（設計書1の ss1_f1〜f8・192番の b212 と b214）を直さない・消さないは、範囲の外です。2つの工事は、承認と実装の監査が済んでいる。161番で写すプログラムと記録を作り直すと、この10本は前提が変わる（ss1 の4本は今も効いていない＝worklog 20261031 §12。b212 は、記録の差でいつも止まる＝§12-4。★2026-10-31 に足した＝b214 が測る192番の完成の条件5は、要素が40行で、2つの表が一番外に在ることを見るので、F-7 の後はいつも止まる）。消すのは守りを外す直しなので、161番では消さず、4-13 に「前提が変わる」と書く。161番の守りは、161番の完成の条件に新しい壊すプログラムを作る。
- gen_read_plan_ss.py（読むもの宣言の元データを作る道具）の、indicators.json の「記録」を読む所を直さないは、範囲の外です。前の工事（設計書2・172番）の読むもの宣言を作る口で、161番の宣言は使っていない（worklog 20261031 §12-3）。--step 3・4 を走らせ直すと止まる。
- いまのデータに値が無い要素（②-3 出力・②-5 の値の単位・②-8 確定と期間・②-4 の軸の意味と軸どうしの決まり・③④の新しい要素）を埋めない（★2026-10-31 に足した）は、範囲の外です。写す元に値が無い。CC が名前から決めると、CC の決まりで値を作ることになる（作ってはいけない物2）。読む口は、これらを「まだ決めていない」で返す（192番の決まり②）。どの工事で埋めるかは 3-2 で伺う。
- build_catalog を、読む口が返す列の組から列を作る形にしない。列の比べ（列の名前と並びと値が直す前と同じか）も走らせない（★2026-10-31 に足した）は、範囲の外です。161-2 で行う。indicators.json は約3.4MB（3,382,713 バイト）で、実装の指示に新しい形の全文を入れられない。書き替えは当てた後に写すプログラムで行う。承認の前の検査は、当てた直後に観察の道具の自己テストを走らせる（require_design_check_before_approval.py:697〜704）ので、build_catalog を同じ設計書で直すと、古い形の indicators.json を読んで止まる。161-1 で書き替えた indicators.json を commit した後に、161-2 で build_catalog を直す。
- 155番の 155-1（同じパラメータの値で計算した値が、直す前と同じこと）を、この設計書では確かめない（★2026-10-31 に足した）は、範囲の外です。161-1 は、計算の作り（build_catalog と観察の道具の計算の登録）を変えない。読む口の calc は、計算の登録の関数をそのまま返す。値が変わりうるのは、build_catalog が読む口から列を作る161-2 なので、155-1 の確かめは161-2 の設計書に書く（228回目の締めで ToDo の155番の行に書いた・コミットに まこさん「コミットOK」）。
- 別枠の材料8種（レンジ幾何の W%・下半分位置・帯内位置%／需給の CVD・L-S比・taker_ls／時間帯の時刻・曜日）の計算を、読む口の calc から返さない（★2026-10-31 に足した）は、範囲の外です。この8種の計算は、1種ずつの関数として計算の登録に無い。まとめて作る関数（observe_diag.py の build_range_geometry・load_demand）か、engine_tuner_exec.py の _col_array の中に在り、記録の計算の関数は登録の名前が空（写しの読む口 --count＝登録の名前が無い 8件）。1種ずつの関数に切り出すのは、engine_tuner の経路を向け直す171番。読む口は、この8種の calc で「計算の関数の登録が無い」と止まる。
- 資料の表のパラメータの名前が、計算式の引数の名前と合わない軸（名前の語・計算式の渡し方・意味の対応表・並びの値・残った1組のどれでも合わない軸）の、代表の値の対応を決めない（★2026-11-01 に足した）は、範囲の外です。対応を決めると、私が約100組を1組ずつ決めることになり、監査を通らずに indicators.json に入る（C-1 と同じ取り違えの恐れ）。資料の表の値を軸と対応させて写すのは、教科書の値を写す70番の T-3 と同じ仕事（3-2＝値の無い要素は70番で埋める）。161-1 では、合わない軸を「まだ決めていない」にし、合わない値の一覧を写すプログラムが画面に出す。元の値は②-9 に残る。

<!-- 項目: 問い 番号=R0 優先度=A 理由=要件定義に反する直しや、要件のどれにも結び付かない直しが、そのまま進む 名前=この工事は、要件定義の何番を満たすための物か。要件定義に反する所は無いか -->
この工事が結ぶ要件は、この依頼書の「この監査は何のためか」の 3 に書いてあります。3 に「欄が無い」と書いてあるときは、3 に書いた読み方で、結ぶ要件を読み取ってください。
要件定義の要約は、この依頼書の上の方に載っています。要件定義の全文は、`.claude/rules/core_requirements_full.md` に在ります。

次の2つを確かめてください。

- **R0-1**：結ぶ要件が、工事の目的と中身に合っているかを確かめてください。もっと合う要件や、抜けている要件があれば、挙げてください。
- **R0-2**：設計と実装と直しに、要件定義に反する所が無いかを確かめてください。反する所があれば、ファイルの名前と行で挙げてください。

<!-- 項目: 問い 番号=Q1 優先度=A 理由=違えば、実装は設計書のとおりに作られていない 名前=実装の指示を当てた結果が、実装の後と1文字も同じか -->
設計書の 4-20 には、実装の指示が 12 件あります。
実装の前の対象のファイルに、この 12 件を番号の順に当ててください。実装の前の版は、事実データ「実装の前と後の版」の実装の前です。対象のファイルは、`.claude/breaks/b215_reader_off_element.sh`・`.claude/breaks/b216_reader_choice_check.sh`・`.claude/breaks/b217_draft_range_not_copied.sh`・`.claude/breaks/b218_draft_hidden_rows_missing.sh`・`.claude/breaks/b219_probe_direct_read.sh`・`.claude/breaks/b220_reader_calc_from_registry.sh`・`.claude/breaks/b221_draft_rep_by_position.sh`・`.claude/state/indicator_review/gen_fix_inventory.py`・`.claude/state/indicator_review/gen_indicators_draft.py`・`.claude/state/indicator_review/ss_outside_probe.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py`です。
当てた結果が、実装の後の版と1文字も同じかを確かめてください。実装の後の版は、事実データ「実装の前と後の版」の実装の後です。
確かめ方の例は、次のとおりです。まず、作業場に、git show で実装の前のファイルを出します。次に、直す前の文字を、直した後の文字に置き替えます。足す文字の指示なら、直す前の文字の後ろに、足す文字を足します。最後に、置き替えた結果と実装の後の版の差を、diff で取ります。

<!-- 項目: 問い 番号=Q2 優先度=A 理由=在れば、設計書に無い変更が実装に混ざっている 名前=実装の指示のどれにも当たらない行（設計書に無い変更）が無いか -->
実装の前の版と実装の後の版の差分を取ってください。実装の前の版は、事実データ「実装の前と後の版」の実装の前です。実装の後の版は、事実データ「実装の前と後の版」の実装の後です。差分を取るファイルは、`.claude/breaks/b215_reader_off_element.sh`・`.claude/breaks/b216_reader_choice_check.sh`・`.claude/breaks/b217_draft_range_not_copied.sh`・`.claude/breaks/b218_draft_hidden_rows_missing.sh`・`.claude/breaks/b219_probe_direct_read.sh`・`.claude/breaks/b220_reader_calc_from_registry.sh`・`.claude/breaks/b221_draft_rep_by_position.sh`・`.claude/state/indicator_review/gen_fix_inventory.py`・`.claude/state/indicator_review/gen_indicators_draft.py`・`.claude/state/indicator_review/ss_outside_probe.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py`です。
差分のうち、実装の指示のどれにも当たらない行が在るかを確かめてください。在れば、全部を挙げてください。

<!-- 項目: 問い 番号=Q3 優先度=A 理由=合わなければ、どの件を道具が当てたかを後から確かめられない 名前=当てた記録が、実装の指示の全部と1件ずつ合うか -->
当てる道具は、実装の指示を当てるたびに、`SDK/.claude/audits/applied_fixes.json` に記録を書きます。この工事の記録の名前は、`design:m2c15-indicator-redirect-20261031` です。
この記録が、実装の指示の 12 件と、番号と対象のファイルで1件ずつ合うかを確かめてください。
記録に「当てた」とも「もう当て終わっていた」とも書かれていない件が在るかを確かめてください。
「もう当て終わっていた」の件について、その件がどの実行で当たったかを確かめてください。確かめる材料は、当てる道具の出力と、git の差分です。

<!-- 項目: 問い 番号=Q4 優先度=B 理由=当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない 名前=承認した版の設計書どうしで、実装の指示が同じか -->
まこさんが承認した版の設計書の控えは、`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-indicator-redirect-20261031.md`です。
この控えの 4-20 の実装の指示と、いまの設計書の 4-20 の実装の指示が同じかを確かめてください。★2つが同じファイルを指すときは、控えのハッシュ値と、承認の印（`.claude/state/acceptance.approved`）の値と、控えのコミットの版が同じかを確かめてください。違うなら、その違いが実装に影響するかを答えてください。

<!-- 項目: 問い 番号=Q5 優先度=B 理由=要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない 名前=実装の指示が、やることの表の要件を全部 満たすか -->
やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-indicator-redirect-20261031/やることの表.md`）の一覧には、この工事でやることが書いてあります。
実装の指示が、この一覧のやることを全部満たすかを確かめてください。
一覧に在るのに実装の指示に無い物と、実装の指示に在るのに一覧に無い物を、全部挙げてください。

<!-- 項目: 問い 番号=Q6 優先度=B 理由=成り立たなければ、承認のときの「済」が根拠にならない 名前=完成の条件が、実装の後に本当に成り立つか -->
設計書の完成の条件の表には、7 行の条件が書いてあります。
この条件が、実装の後に本当に成り立つかを確かめてください。
各行のコマンドを、作業場で走らせるか、読むだけの形で走らせてください。コマンドの中のパスは、`SDK` のフォルダからの相対です。そのため、どのコマンドも `SDK` のフォルダで走らせます。
走らせるコマンドは、次のとおりです。`python3 scripts/priority_rebuild/indicators/indicators.py --selftest`・`python3 ../../.claude/state/indicator_review/gen_indicators_draft.py --selftest`・`bash -c "! grep -n -E '/ .indicators\.json.' ../../.claude/state/indicator_review/gen_fix_inventory.py ../../.claude/state/indicator_review/ss_outside_probe.py"`

<!-- 項目: 問い 番号=Q8 優先度=A 理由=実装が設計書と違うと、161-2 と171番が読む読む口と記録が、まこさんが承認した物と違ってしまう 名前=当てた実装12件と、書き替えた indicators.json が、承認された設計書のとおりか -->
実装の指示は12件です。
- 実装1 は、読む口 indicators.py を新しく作ります。
- 実装2 は、写すプログラムの全文を置き替えます。
- 実装3 と実装4 は、一覧を作るプログラムの2か所を直します。
- 実装5 は、数える道具の1か所を直します。
- 実装6〜12 は、壊すプログラム7本を新しく作ります。

CC がしたことは、次のとおりです。
- 当てる道具（apply_audit_fix.py --design）が12件を当てました。当てなかった件は0でした。
- CC は、設計書の 4-4 の2〜4 を走らせました。
- 写すプログラムの --rewrite は、indicators.json を新しい形に書き替えました。画面の数は、4-12 に書いた写しの結果と全部同じでした。
- 写すプログラムの --verify は「違い 0 件」でした。

次の3つに答えてください。
- 1つ目に、実装1〜5 の実物が、設計書の「直した後の文字」と1文字も違わないかを答えてください。一覧を作るプログラムと数える道具は、.gitignore の対象（:78）です。そのため、git の差には出ません。設計書の文字と、ファイルを直に比べてください。
- 2つ目に、書き替えた indicators.json が、設計書の 4-8 の形と 4-12 の数のとおりかを答えてください。確かめるコマンドは、4-12 に在る写すプログラムの --verify（約98秒）と、読む口の --count と、jq の7本です。
- 3つ目に、完成の条件7行（設計書の 7-6）を SDK の直下で走らせ、結果を答えてください。

**CC の自己申告1（写すプログラムの自己テストが、書き替えの後に 38/39 になる）**
- 完成の条件4・5・7 のコマンドは、写すプログラムの --selftest です。この自己テストは、indicators.json を書き替えた後に 38/39 になります。
- 落ちるのは「写す: 要素の定義表に ②-12 が無ければ止まる」の1本です（gen_indicators_draft.py:1693-1700）。
- この1本は、本物の indicators.json の要素の定義表（:1593 の read_table）を、「②-12 がまだ無い表」として to_new に渡します。
- 書き替えの前の表には ②-12 が無く、書き替えの後の表には在ります。そのため、書き替えの後は、いつも落ちます。当てた直後（書き替えの前）は 39/39 でした。
- 同じ自己テストの :1598 は、本物の表が新しい形のときにも合うように書いてあります。:1697 は合いません。
- CC は、写しの確かめで、自己テストを書き替えの前にだけ走らせていました。そのため、承認の前に見つけられませんでした。
- まこさんは、承認したコードのまま進め、直しはこの監査の修正として入れると決めました。修正の指示を書いてください。
- CC の直し方の案は、自己テストの中で、本物の表から ②-12 を除いた写しを作り、to_new に渡す形です。

**CC の自己申告2（完成の条件6 を、bash -c の形で打てなかった）**
- 完成の条件6 のコマンドは、bash -c "! grep …" の形です。
- hook（設計↔実装ゲート）が bash -c の形を止めるので、CC はこの形を打てませんでした。
- CC は、中の grep を直に打ちました。当たりは0件で、grep の終わりのコードは 1 でした。条件の形では、0 に当たります。

**CC の自己申告3（数える道具の合計が、写しの値と違った）**
- 数える道具（ss_outside_probe.py）の「表の外の合計」は 2796 でした。4-12 に書いた写しの値は 2780 です。
- 差 16 のうち 7 は、.json の本数の差です（写し 100・本物 107）。
- 写しの .claude/state には、json を3本しか入れていませんでした。そのため、ほかの7本が数えられませんでした。7本は、indicator_fix_plan.json・indicator_params_by_strategy.before_153.json・indicator_source_map.json・read_plan_src_m2c15-* の4本です。
- 残りの 9 は、D（表の外の指標の情報を読む行）の差です（写し 1497・本物 1506）。
- D は、.py の中で「数えた json の名前」を含む文字の行も数えます（ss_outside_probe.py:178）。CC は、7本の名前を含む行が ＋9 に当たると考えています。ただし、1行ずつの突き合わせはしていません。

**CC の自己申告4（一覧に 5484 の行が残っている）**
- 作り直した一覧（fix_inventory_20261024.md）の :1799 は「5487・LINEAGE_KINDS・①写す」で、実物の行と合いました（設計書の 4-19 の F-4）。
- 一覧の :218 と :424 は、5484 のままです。この2行は、エージェントの報告の文をそのまま残す節（「照らし」と「拾えなかった物」）の行です。

**CC の自己申告5（合わない隠れた数字の軸に、いまの値が入っている）**
- 写すプログラムは、資料の表の名前と合わない隠れた数字の軸に、コードの既定値を代表の値として入れます（gen_indicators_draft.py:1138）。
- 出どころには「いまの値（コードの既定値）・資料の表の名前と合わない（対応は70番の T-3）」と書きます（:1142）。
- 本物の indicators.json では、この軸が47本（28記録）あります（jq で数えた）。
- まこさんが OK した案と、設計書の §5 の5行目（承認の控えの :4101）は、「合わない軸は『まだ決めていない』にし」と書いています。
- CC は、コードを書くときに、やることの表の F-3 の「範囲が無い軸は…代表の値（いまの値）だけを持つ」に合わせました。CC は、案の文とコードの食い違いに、承認の前に気づきませんでした。
- 名前に出る軸で合わない軸（141本）は、案の文のとおり「まだ決めていない」です。
- どちらに合わせるかを含めて、修正の指示を書いてください。

<!-- 項目: 問い 番号=Q9 優先度=B 理由=落ちない壊し方が在ると、読む口や写すプログラムが壊れても、誰も気づかない 名前=壊すプログラム7本は、設計書の 7-6 の壊し方のとおりで、直しを外したときだけ落ちるか -->
写しの作業場で、次の7本を走らせてください。
- b215：決まり③の判定を外す（条件1 を守る）
- b216：決まり④の照らしを外す（条件2 を守る）
- b220：計算の登録から関数を取らない（条件3 を守る）
- b217：範囲を軸へ写す所を外す（条件4 を守る）
- b218：隠れた数字の rows を写さない（条件5 を守る）
- b219：数える道具に、indicators.json を直に読む行を戻す（条件6 を守る）
- b221：代表の値を、並びの番号で割り当てる（条件7 を守る）

見てほしいことは、次の3つです。
- 宣言した文（EXPECT_MSG）で落ちるか。
- 壊す対象を、正しく1か所だけ見つけるか。
- 壊した後に、必ず元に戻るか。

CC が確かめたことは、次のとおりです。
- CC は、run_breaks.py --design <設計書> --measure-only で、7本とも終わりのコード 1 を確かめました。この走らせ方は、記録を書きません。
- 走らせた後に、読む口の自己テストは 34/34、grep の当たりは0件でした。
- 写すプログラムは、承認した中身と同じでした。違いは、jq が最後に足す改行だけです。
- 写すプログラムの自己テストは 38/39 でした。これは Q8 の自己申告1 の1本で、壊すプログラムのせいではありません。

注意してほしいことが1つあります。
- b217・b218・b221 が測るのは、写すプログラムの自己テストです。この自己テストは、書き替えの後はいつも 38/39 で、終わりのコードが 1 になります。
- そのため、この3本は、壊さなくても落ちる状態です。壊したときに、宣言した文が出ることも見てください。

<!-- 項目: 問い 番号=Q10 優先度=A 理由=修正の指示と違う形や、まこさんが決めた案と違う形で入った件が在ると、設計書の監査で直したはずの誤りが残ったまま、161-2 と171番へ進む。CC は、案の文とコードが違う件を、すでに1つ見つけている（Q8 の自己申告5） 名前=設計書の監査 CP94 の修正31件が、修正の指示のとおりで、まこさんが決めた直し方のとおりに、実装に入っているか -->
監査 CP94 の修正の指示は、結果の8番の節（:417-861）と9番の節（:862-908）に在る31件です。

まこさんが決めた直し方は、次のとおりです。
- 修正1〜31 を、全部入れる。
- 案が複数の件は、修正4＝案A、修正8＝案B、修正10＝案B（案A の1時間ATR の単位の注記も足す）、修正14＝案B、修正16＝案B、修正17＝案A。
- 入れるかを選ぶ件は、修正12＝入れる、修正27＝入れる。
- 修正1＝案B。資料の表の名前が軸に合わない値は「まだ決めていない」にし、合わない値の一覧を画面に出す。対応は70番の T-3 で決める。
- 修正20 の注記（ADX の使い方の記録の出どころ）を、写すプログラムにも足す。
- 決めた直し方の記録は、session_worklog_20261101.md の §2-4 と §2-7 と §4、設計書の §5 の30行（承認の控えの :4092-4126）です。

CC の入れ方は、次のとおりです。
- 11件（修正2・3・4・8・15・16・22・25・26・27・31）は、当てる道具が、やることの表に当てました（applied_fixes.json の CP94 の行）。
- 17件（修正1・5・7・9・10・11・12・13・14・17・18・20・21・23・24・29・30）は、CC が案の節に入れて直し、まこさんの OK をいただきました。設計書の実装の指示（4-20）は、この案から作りました。
- 3件（修正6・19・28）は、設計書を作り直すコマンドの件です。CC は、設計書を作り直しました。

次の2つに答えてください。
- 1つ目に、修正1〜31 を1件ずつ、修正の指示の文と、まこさんが決めた直し方と、実装の3つを照らしてください。実装は、読む口・写すプログラム・一覧を作るプログラム・数える道具・壊すプログラム・書き替えた indicators.json です。そのうえで、合っているか、違うかを答えてください。違う件は、どこがどう違うかを、実物の行で示してください。
- 2つ目に、設計書の文（§5・4-7・4-12 ほか）と、設計書の実装の指示のコード（4-20）が、食い違っている所が無いかを答えてください。Q8 の自己申告5 は、その1つです。

<!-- 項目: 問い 番号=Q11 優先度=A 理由=要件どおりでない実装が在ると、161-2・171番・70番が、その上に積み上がる。設計書の監査（CP94 の Q15）でも照らしたが、その後に修正31件を入れて設計書と実装を作り直したので、実装で照らし直す 名前=指標の構造の要件定義書の要件のうち、この工事に当たる箇所が、要件どおりに実装されているか -->
指標の構造の要件定義書は、指標の工事で守る物を1本にまとめた文書です（367行）。

照らす項目は、次のとおりです。
- 第1章：ゴール1、ゴール2の①〜⑤、ゴール3の①〜④、順番。
- 第2章：機能要件の1〜6、探し方、言葉の定義（代表の固定値・範囲・戦略・教科書・法則・指標一覧）、指標の使い方、教科書と法則の扱い、作ってはいけない物。
- 第2章の2：作る物（1つのデータ・読む口・どのプログラムからも呼べるライブラリ・記録に入れる物の一覧・読む口が指標一覧に当たること）。
- 第3章：拡張と直しやすさの条件。
- 第4章：構造の案 A〜F、決めたこと2つ、indicators.json の欄との対応（そのまま使える欄・形を変える欄・足す欄）。
- 第5章：構造に要ることの30件。
- 第6章：直す物の一覧（A 探し方と母数〜G 正本と ToDo）。
- 第7章：やってはいけないこと。
- 第8章：ToDo の行のうち、161番・172番・155番の決まった中身。

項目ごとに、次の3つのどれか1つで答えてください。
- 実装で受けている：受けている所（読む口と写すプログラムの関数と行・indicators.json の要素）を書き、要件どおりかを答えてください。
- 後の工事で受ける：その工事が、第8章の ToDo の行か、設計書のやらないこと（Y-1〜Y-20）に在るかを確かめてください。
- この工事に当たらない：その理由を書いてください。

特に、次の5か所を見てください。
- 第2章の2 は、読む口が「指標の値の計算も返す」と書いています。実装は、読む口の calc と value で受けます。別枠の材料8種は、calc で止めます（Y-19）。
- 第4章の欄との対応は、「列の名前の型」と「列を作る値」を、パラメータの定義（②-4）に置き替えると書いています。実装は、171番まで ②-12「列を作る組」として残します（Y-4）。
- 第4章の欄との対応は、「方向・性質」を、使い方の記録の向き（③-4）へ移すと書いています。実装は、指標の記録の ②-6「値の読み方」に写し、使い方の記録の向きは出口の4種だけに書きます。
- 第8章の155番の行は、155-1 を161番の設計書に書くと書いています。実装は、この確かめを161-2 へ回しました（Y-18）。
- 第2章の要件5 は、代表の固定値を「教科書に在ればその値、無ければ既定の値」と書いています。合わない隠れた数字の軸47本は、いまの値（コードの既定値）を代表の値に持ちます（Q8 の自己申告5）。

受け先が無い項目や、第7章のやってはいけないことに当たる実装が在れば、挙げてください。

<!-- 項目: 外部検索 名前=定義表（スキーマ）を読む読む口の作り -->
検索の言葉：schema driven data access layer default values enum validation fail closed JSON
調べる物：記録の欄の種類・既定の扱い・選べる値を、データの側の定義表に持たせ、読む口がその表を読んで照らし、無い欄は定義表の既定で返す作りが、外の一般の作り方と合うか。新しく Web は開いていない。実装の監査では、この出どころと、実装の該当の所が合うかを照らします

<!-- 項目: 外部検索 名前=パラメータの軸を名前・範囲・代表の値で持つ作り -->
検索の言葉：indicator parameter space definition name range default separate from column naming feature store
調べる物：指標のパラメータを、名前に数字を入れずに、軸ごとの定義（名前・型・範囲・既定）として持つ作りが、外の一般の作り方（hyperparameter space の定義）と合うか。新しく Web は開いていない。実装の監査では、この出どころと、実装の該当の所が合うかを照らします

<!-- 項目: 外部検索 名前=計算の本体を1か所に置き、読む口が名前で引いて返す作り -->
検索の言葉：registry pattern function lookup by name single source of truth indicator library
調べる物：記録が関数の名前を持ち、読む口がその名前で計算の登録から関数を返す作り（登録の表＝registry パターン）が、外の一般の作り方と合うか。新しく Web は開いていない。実装の監査では、この出どころと、実装の該当の所が合うかを照らします


<!-- 項目: 自己申告 -->
**この工事の外の作業中の変更**：次のファイルには、作業中の変更があります。`.claude/tools/gen_audit_docs.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_audit_request.py`。この変更は、この工事の実装の指示が当てた物ではありません。そのため、Q1 と Q2 の差分を、この工事の対象のファイルだけで取ってください。

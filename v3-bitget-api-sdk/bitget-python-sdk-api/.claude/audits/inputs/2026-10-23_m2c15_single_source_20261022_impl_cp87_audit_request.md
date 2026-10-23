# 【監査依頼】CP87 — 指標の情報の置き場を1つにする・a＝役割・札・方向・性質・検査（実装の監査）

## ⚠️ 監査人への宣言（本依頼書を開いた CC への指示・最優先）

あなたは、このセッションで監査人として呼ばれた CC です。依頼を出した CC とは、別のセッションです。
この依頼書と、「着手前必読」のファイルと、問いが指す実物（コード・設定・記録）だけを読みます。
セッションの始めに読み込まれる CLAUDE.md などは、参考にするだけです。

依頼を出した CC の判断に、合わせないでください。同じ種類の AI は、同じ思い込みをしやすいためです。
あなたは、まこさんの味方でも、CC の味方でもありません。あなたは、要件定義と教科書と業界の標準の味方です。

### やること（読み終えたら、確認の質問なしで）

1. この依頼書の全文を、Read で読みます。
2. `Agent` の道具で、Plan agent（`subagent_type=Plan`）を、何も知らない状態から起動します。Plan agent に、依頼書のパスと、着手前必読のファイルの名前だけを渡します。
3. Plan agent は、依頼書を読んで監査し、所見をあなたに返します。Plan agent は、ファイルを作れず、コマンドも走らせられません。そのため、写しを作る作業と、自己テストや試しの道具を走らせる作業は、あなたがします。その結果を Plan agent に渡します。
4. 結果を、次の順で書きます。結果を手で1から書きません。コマンドを全部、リポジトリの根（`cat-bitget/`）で打ちます。
   - まず、結果の骨組みを作業場に作ります。コマンドは `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-23_m2c15_single_source_20261022_impl_cp87_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp87_work/cp87_result.md` です。
   - 次に、骨組みの「<監査が書く>」を全部埋めます。見出しと並びを変えません。
   - 次に、埋めた結果を照らします。コマンドは `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-23_m2c15_single_source_20261022_impl_cp87_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>` です。食い違いを0件にします。
   - 次に、結果を見直します。`python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` が作る表を全部埋めます。そのあと、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通します。
   - 最後に、結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-23_m2c15_single_source_20261022_impl_cp87_audit_report.md` に、Write で1回だけ書きます。hook 11 が、書く瞬間に同じ照らしを掛けます。書いた後に、結果ファイルを書き替えられません。
5. 最後に、3つを報告します。1つ目は、結果ファイルのパスです。2つ目は、結論（GO・CONDITIONAL-GO・NO-GO のどれか）です。3つ目は、重さごとの件数（Critical・Major・Minor・Process）です。

### 禁止

- 依頼を出した CC に、確認の質問をしません。この依頼書だけで、監査ができるように書いてあります。
- Plan agent を起動せずに、自分だけで監査しません。
- 本物のファイルを書き替えません。写しを作業場に作ります。最後に、`git status --short` の出力で、本物を書き替えていないことを示します。
- ChatGPT などの外の AI を使いません。まこさんの課金の外になるためです。
- 「可能性がある」「かもしれない」「検討の余地」という言い方で答えません。数字と実物の行で言い切ります。言い切れないときは、「データ不足」と書き、その理由を書きます。

### 作業場

写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp87_work/` に作る。必要なファイルは自分で開き、写しで走らせて確かめる。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-23
- 依頼者: CC（起案者）
- 監査の種類: 実装の監査
- 売買に触るか: はい
- 監査対象タスク: M2-C-15／設計書 m2c15-single-source-20261022
- 監査の相手と版: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-single-source-20261022.md` ／ ハッシュ値 76d086a739174c3895c22e22c8be2738c8e57beda660da600d38b45066ac8518
- 直す相手: `.claude/breaks/b182_copy_mark_without_known.sh`・`.claude/breaks/b199_adx_back_to_trend.sh`・`.claude/tools/pre_audit_check.py`・`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_diag.py`・`SDK/scripts/priority_rebuild/gen_indicator_table.py`・`.claude/hooks/check_indicator_table_on_save.py`・`.claude/hooks/check_indicator_table_on_save.sh`・`.claude/state/indicator_review/check_materials_known_ng.json`・`.claude/breaks/b204_table_role_handwritten.sh`・`.claude/breaks/b205_row_arg_back.sh`・`.claude/breaks/b206_lineage_handwritten.sh`・`.claude/breaks/b207_table_check_dropped.sh`・`.claude/breaks/b208_known_ng_new_ignored.sh`・`.claude/breaks/b209_table_prop_handwritten.sh`
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-23_m2c15_single_source_20261022_impl_cp87_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-23_m2c15_single_source_20261022_impl_cp87_audit_request.md`

---

## 要件定義と工事の流れ (固定・消さない・まこさん指示 2026-10-12)

**■ 要件定義と工事の流れ（固定・毎回 読む・消さない）**

★この文書は、まこさんが OK した要約（2026-10-18・逐語のファイル `okd_summary_20261018.txt`・OK の発言＝`ok_summary_20261018.txt`。10 だけは 2026-10-20 の `design-audit-scope-20261020/okd_summary10_20261020.txt`・OK の発言＝`ok_summary10_20261020.txt`）を、プログラムが写した物です。見出しの行と、この説明の4行だけが、プログラムの中の決まった文です。
★全文＝`.claude/rules/core_requirements_full.md`（同じプログラムが逐語のファイルから作る）。要約の中の まこさんの言葉（「」の行と、機能要件の6行）が全文に1文字も違わずに在ることを、`--verify` が照らします。
★作り直し＝`python3 .claude/tools/gen_core_requirements.py --write`。検出＝`--verify`。
★設計書・監査の依頼書・next_step の上部には、それぞれを作るプログラムが、この要約を写して載せます（いつも載せるのは 1・2・3・7・8・10。売買のロジックに触る工事では 4・5・6・9 も足します）。この文書が無い・逐語のファイルと違うときは、どのプログラムも文書を作らずに止まります。

**■ 1. CAT プロジェクトの目標**
- 本番で BOT を走らせて、全月 net ≥ $1,900 を達成する。単月で判定する。全部の採用戦略を合わせた net で見る。
- 「目標達成のため、ただ早く進めることが正解ではなく、正しく早く進めることが最善」

**■ 2. engine_tuner の目的**
- 「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的」
- 「上記目的に即していないものは作らないこと。」
- 現状の位置付け＝「現状、CCの思考を補助する機能とする」

**■ 3. engine_tuner の機能要件**
指標、閾値、パラメータ、時間足の役割に基づき、法則に則って４つを組み合わせ、Entry/Exitやレジーム判定などの条件を作る
| 1 | 指標が、承認済みのカタログに在るものから使われている
| 2 | 閾値が、範囲から探されている
| 3 | パラメータが、範囲から探されている
| 4 | 時間足が、使える時間足から指定されている
| 5 | 4つが、それぞれの役割に沿って使われている
| 6 | つなぎ方が、型の表と場面の決まりに沿っている

**■ 4. 探し方**
- 最初の段階は、パラメータと閾値を代表の固定値にして、指標・時間足・役割・つなぎ方の組を絞る。
- 最後の段階で、残った組のパラメータと閾値を、指標ごとの範囲から探す。「範囲で探せるという上記要件は絶対」
- ほかの探し方に替えない。

**■ 5. 言葉**
- 代表の固定値＝最初の段階で固定して使う値。戦略（スキャル／デイトレ）ごと・指標ごとに1つ。教科書に在ればその値、無ければ既定の値。「厳密でなくてもいい」
- 範囲＝最後の段階で探す幅。指標ごとに1つ。指標の名前に値を入れて指標を増やさない。
- 教科書＝指標のパラメータ・閾値・役割・計算の出どころの資料（資料の表3つ）。
- 法則＝相場から見つけた知識を文で書いた物（regime_detection_kb.md §11）。「法則があるからロジックって言われてるんだけど。」

**■ 6. 指標と、教科書と法則の扱い**
- 指標は、指標一覧（material）からだけ呼び出す。オン・オフは全部のロジックに効く。
- 教科書と法則は完璧ではない前提で作る。誤りは置き場の1か所を直せば済み、直した物が全部のロジックに届く作りにする。

**■ 7. 作ってはいけないもの**
1. ランダムに条件をつなぐだけのもの。
2. 探す値を、CC が先に決まった数字の一覧で限定するもの。

**■ 8. 設計書と監査で確かめること**
- その設計のとおりに作ると、net 利益を最大にするロジックを見つける力が上がるか。少なくとも、損なわないか。
- 文字や手順が合っているかは、その手前の確かめ。

**■ 9. 工事の流れ**
| 1 | 設計書の元を作る（読む・案・まこさんの OK） | 私 → まこさん |
| 2 | 設計書を作る | プログラム |
| 3 | 設計書の監査（設計の中身が正しいか） | 監査 |
| 4 | 設計書の監査結果の確認（直す範囲を決める） | まこさん |
| 5 | 設計書の修正（監査が書いた修正を入れる） | プログラム |
| 6 | 承認 | まこさん |
| 7 | 実装（承認した設計書から書き込む） | プログラム |
| 8 | 実装の監査（設計書のとおりか） | 監査 |
| 9 | 実装の監査結果の確認（直す範囲を決める） | まこさん |
| 10 | 実装の修正（監査が書いた修正を入れる） | プログラム |
- 設計の誤りは 3〜5 で全部 出して直す。8 で見るのは「設計書のとおりか」だけ。

**■ 10. 設計書の監査が要る物**
- 売買のロジック・材料（指標）・法則・設定（scripts/priority_rebuild の .py と設定ファイル）を直す工事＝要る。
- インフラ（.claude/hooks・.claude/tools・文書を作るプログラム）を直す工事＝要らない。直した後の監査も要らない。
- インフラの工事も、宣言に規模を書く。応相談にするかは、まこさんが決める。
- 検査・問い・止める条件を外す、または緩める直しは、直す前に、消す行を まこさんに見ていただく。

---

## この監査は何のためか（目的と経緯）

1. **この工事は何のためか**：この工事は、指標1つの役割の情報（札・方向・性質・教科書の役割）の置き場を、定義表の中の1つの表 INDICATOR_TABLE にします。直す前は、この4つが別々の場所に手で書かれていました。1か所を直しても、ほかの場所は直りませんでした。2026-10-22 に、材料の検査で、方向の欄と性質の欄の食い違いが119件 見つかりました。まこさんは、指標の情報の読み込み元と繋ぎ先の全体の設計をし直し、指標を1つのデータから読む形にするように求めました。
2. **この工事は何か**：指標1つの役割の情報が4か所に分かれていて、1か所を直してもほかが直らないので、役割の情報の置き場を定義表の1か所にします。 ⏎  ⏎ - 指標は、engine_tuner が Entry・Exit と4つの場面の判定の条件を組むときの材料です。指標1つの役割の情報は、札（系統）・方向の欄・性質の欄・教科書の役割の4つです。 ⏎ - いまは、この4つが、札の表（FAMILY_LINEAGE）・定義表の各行（方向の欄・性質の欄）・資料の表（教科書の役割）に、別々の言葉で在ります。4か所の間に対応の決まりが無く、CC が別々に手で書きました。R-1 で札だけを直した結果、方向の欄と性質の欄の食い違いが119件、材料の検査で見つかりました。材料の検査は、2026-08-06 から10-22 まで一度も走っていませんでした。 ⏎ - この工事でやることは、次の3つです。①定義表の中に、指標1種につき1行の表（INDICATOR_TABLE）をプログラムが書く（役割・札・方向・性質・値域）②定義表の各行から手書きの方向と性質の引数を消し、札の表を消して、全部この表から読む形にする ③材料の検査を、監査に出す前のチェックと、定義表を書き替える瞬間の hook に入れる。 ⏎ - パラメータの値と範囲を同じ行に置く直しは、次の工事 b です。1件ずつの値の判定（119件）は、その後の M-1 です。（やることの番号は、M2-C-15です）
   **この工事の位置**：目標からこの工事までのつながりは、次のとおりです。全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝材料を直す（監査 CP60 の修正・パラメータ・法則どおりの帯の部品・S1 の部品・役割・閾値） → この工事
3. **この工事が結ぶ要件**：M2-C-15＝要件定義の3番（機能要件の1〜5＝指標・閾値・パラメータ・時間足・役割）と4番・5番（代表の固定値＝新しい種類の代表の値）と6番（指標と、教科書と法則の扱い）。材料（指標）の誤りを教科書と照らして直し、指標・閾値・パラメータ・時間足が、正しい材料から、範囲で探せる形にする（まこさん OK 2026-10-20）（出どころ＝やることリスト m2_todo.json の「結ぶ要件」）
4. **経緯**：この監査に至るまでの経緯は、次のとおりです。
   - 2026-10-22 に、設計書の監査 CP86 を出しました。結果は CONDITIONAL-GO で、修正は24件でした。まこさんは、24件の全部を直すと決めました。案が2つある4件は、CC の勧め（修正6＝A・修正7＝A・修正8＝B・修正12＝A）に決めました。
   - 2026-10-23 に、CC は、修正を入れた案を作り直しました。写しで3回 確かめ、仮当ての試しも通しました。まこさんは、その案に「OK」をくださいました。実装の指示は314件です。
   - まこさんは、設計書を承認しました（1回目・承認のハッシュ値 738351c7…）。当てる道具は、実装の指示314件を全部 当てました。まこさんは、新しい hook（check_indicator_table_on_save.sh）を settings.json に登録しました。
   - まこさんは、同じ設計書で2回目の承認を打ちました。承認のプログラムは、完成の条件6行を全部「済」にしました。設計書は1回目と同じ版です（ハッシュ値が同じ）。
   - そのあと、CC は、表の作り直し（G-1）と、監査に出す前のチェック（G-2）を走らせました。G-1 の表は、作り直す前と1文字も同じでした。G-2 は全部 rc=0 でした。材料の検査は、分かっている ❌ の一覧と1行も違わず、rc=0 でした（2,050秒）。

---

## 監査の範囲

### 範囲の中

- 監査の相手は、`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-single-source-20261022.md` です（設計書 `m2c15-single-source-20261022`・実装の監査）。当てる道具が、設計書の実装の指示のとおりに実装を作れているかを確かめます。
- 直す相手は、`.claude/breaks/b182_copy_mark_without_known.sh`・`.claude/breaks/b199_adx_back_to_trend.sh`・`.claude/tools/pre_audit_check.py`・`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_diag.py`・`SDK/scripts/priority_rebuild/gen_indicator_table.py`・`.claude/hooks/check_indicator_table_on_save.py`・`.claude/hooks/check_indicator_table_on_save.sh`・`.claude/state/indicator_review/check_materials_known_ng.json`・`.claude/breaks/b204_table_role_handwritten.sh`・`.claude/breaks/b205_row_arg_back.sh`・`.claude/breaks/b206_lineage_handwritten.sh`・`.claude/breaks/b207_table_check_dropped.sh`・`.claude/breaks/b208_known_ng_new_ignored.sh`・`.claude/breaks/b209_table_prop_handwritten.sh` です。
- この工事は、売買のロジックに触る工事です。engine_tuner の目的は、まこさんの言葉で「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的」です（まこさん確定 2026-08-06）。

### 範囲の外（理由つき）

- 守りの穴探し（すり抜けの道を新しく探すこと）は、範囲の外です。穴探しは、探すたびに新しい穴が出て、終わらないためです（恒久の決まり65番）。CC は、作業が実際に止まったときに、その穴を直します。
- 材料の検査の ❌ 119件（検査1 の54種・検査2 の12種）を、1件ずつ判定して直すことは、範囲の外です。この工事は、置き場と作りを直す工事です。1件ずつの値の判定は、1つのデータになった後の M-1 で行います。方向・性質・札の値は、この工事では1つも変えません。
- パラメータの値と範囲を同じ行に置くこと・カタログを作る所が古い鍵（〜_periods）を読むのをやめること・計算の登録の鍵（56件）を定義表の名前にそろえること・material_params と search_limits の範囲を表から作る写しにすることは、範囲の外です。b（次の工事）です。まこさん「分けてもいいけど」（2026-10-22）。この工事の INDICATOR_TABLE には、軸の欄を持たせません（b で足します）。
- 使い方の照らし（U-1）・閾値（T-1〜T-3）・パラメータの値の直し（P-6・P-7・H-1）は、範囲の外です。全体の表の順のとおり、後の工事です。
- 法則の判定そのもの（regime_laws.json の機械が読む判定）を書き替えることは、範囲の外です。工事2（M2-F-10b）です。
- オフの指標（使わない116種）の役割と値を、教科書と照らして判定することは、範囲の外です。まこさん「オフは現状は対応しなくてよい」（2026-10-04）。ただし、置き場を1つにする作りは、オン・オフを問わず全部の行（301）に掛かります。オフの116種の役割の欄は空です。
- 成績表（material_ranking.json）の作り直しは、範囲の外です。まこさんの決定カ＝U-1 の前に作り直します。
- R-1 の実装の監査の依頼書は、範囲の外です。この工事（a）・b・M-1 の後です。

---

## 確かめてほしいこと（Q1〜QN）

★問いの番号（Q1・Q2 など）は、問いの見出しの頭に書いてあります。結果の所見で、この番号をそのまま見出しにします。問いの中の「特に見てほしい点」（Q8 など）にも、その番号で1点ずつ答えます。
★問いには、優先度 A・B・C・D のどれかが付いています。A の問いは、答えによって監査の結論（GO・CONDITIONAL-GO・NO-GO）が変わる問いです。B の問いは、直すべき所を探す問いです。C の問いは、書き漏れを探す問いです。D の問いは、結論には使わない問いです。
★所見は、優先度 A の問いから順に書きます。時間が足りずに答えなかった問いは、結果にその番号を書いてください。

### R0 — この工事は、要件定義の何番を満たすための物か。要件定義に反する所は無いか（優先度 A）

**この問いが要る理由**：要件定義に反する直しや、要件のどれにも結び付かない直しが、そのまま進む。

この工事が結ぶ要件は、この依頼書の「この監査は何のためか」の 3 に書いてあります。3 に「欄が無い」と書いてあるときは、3 に書いた読み方で、結ぶ要件を読み取ってください。
要件定義の要約は、この依頼書の上の方に載っています。要件定義の全文は、`.claude/rules/core_requirements_full.md` に在ります。

次の2つを確かめてください。

- **R0-1**：結ぶ要件が、工事の目的と中身に合っているかを確かめてください。もっと合う要件や、抜けている要件があれば、挙げてください。
- **R0-2**：設計と実装と直しに、要件定義に反する所が無いかを確かめてください。反する所があれば、ファイルの名前と行で挙げてください。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**この問いが要る理由**：違えば、実装は設計書のとおりに作られていない。

設計書の 4-20 には、実装の指示が 314 件あります。
実装の前の対象のファイルに、この 314 件を番号の順に当ててください。実装の前の版は、事実データ「実装の前と後の版」の実装の前です。対象のファイルは、`.claude/breaks/b182_copy_mark_without_known.sh`・`.claude/breaks/b199_adx_back_to_trend.sh`・`.claude/breaks/b204_table_role_handwritten.sh`・`.claude/breaks/b205_row_arg_back.sh`・`.claude/breaks/b206_lineage_handwritten.sh`・`.claude/breaks/b207_table_check_dropped.sh`・`.claude/breaks/b208_known_ng_new_ignored.sh`・`.claude/breaks/b209_table_prop_handwritten.sh`・`.claude/hooks/check_indicator_table_on_save.py`・`.claude/hooks/check_indicator_table_on_save.sh`・`.claude/state/indicator_review/check_materials_known_ng.json`・`.claude/tools/pre_audit_check.py`・`SDK/scripts/priority_rebuild/gen_indicator_table.py`・`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_diag.py`です。
当てた結果が、実装の後の版と1文字も同じかを確かめてください。実装の後の版は、事実データ「実装の前と後の版」の実装の後です。
確かめ方の例は、次のとおりです。まず、作業場に、git show で実装の前のファイルを出します。次に、直す前の文字を、直した後の文字に置き替えます。足す文字の指示なら、直す前の文字の後ろに、足す文字を足します。最後に、置き替えた結果と実装の後の版の差を、diff で取ります。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**この問いが要る理由**：在れば、設計書に無い変更が実装に混ざっている。

実装の前の版と実装の後の版の差分を取ってください。実装の前の版は、事実データ「実装の前と後の版」の実装の前です。実装の後の版は、事実データ「実装の前と後の版」の実装の後です。差分を取るファイルは、`.claude/breaks/b182_copy_mark_without_known.sh`・`.claude/breaks/b199_adx_back_to_trend.sh`・`.claude/breaks/b204_table_role_handwritten.sh`・`.claude/breaks/b205_row_arg_back.sh`・`.claude/breaks/b206_lineage_handwritten.sh`・`.claude/breaks/b207_table_check_dropped.sh`・`.claude/breaks/b208_known_ng_new_ignored.sh`・`.claude/breaks/b209_table_prop_handwritten.sh`・`.claude/hooks/check_indicator_table_on_save.py`・`.claude/hooks/check_indicator_table_on_save.sh`・`.claude/state/indicator_review/check_materials_known_ng.json`・`.claude/tools/pre_audit_check.py`・`SDK/scripts/priority_rebuild/gen_indicator_table.py`・`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_diag.py`です。
差分のうち、実装の指示のどれにも当たらない行が在るかを確かめてください。在れば、全部を挙げてください。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**この問いが要る理由**：合わなければ、どの件を道具が当てたかを後から確かめられない。

当てる道具は、実装の指示を当てるたびに、`SDK/.claude/audits/applied_fixes.json` に記録を書きます。この工事の記録の名前は、`design:m2c15-single-source-20261022` です。
この記録が、実装の指示の 314 件と、番号と対象のファイルで1件ずつ合うかを確かめてください。
記録に「当てた」とも「もう当て終わっていた」とも書かれていない件が在るかを確かめてください。
「もう当て終わっていた」の件について、その件がどの実行で当たったかを確かめてください。確かめる材料は、当てる道具の出力と、git の差分です。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**この問いが要る理由**：当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない。

まこさんが承認した版の設計書の控えは、`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-single-source-20261022.01.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-single-source-20261022.md`です。
この控えの 4-20 の実装の指示と、監査の相手の設計書（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-single-source-20261022.md`。★比べる相手は、承認の控えです。`.claude/state/acceptance.md` は、後の工事の設計書で上書きされることがあるので、比べる相手にしません）の 4-20 の実装の指示が同じかを確かめてください。★2つが同じファイルを指すときは、控えのハッシュ値と、承認の印（`.claude/state/acceptance.approved`）の値と、控えのコミットの版が同じかを確かめてください。違うなら、その違いが実装に影響するかを答えてください。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**この問いが要る理由**：要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない。

やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-single-source-20261022/やることの表.md`）の一覧には、この工事でやることが書いてあります。
実装の指示が、この一覧のやることを全部満たすかを確かめてください。
一覧に在るのに実装の指示に無い物と、実装の指示に在るのに一覧に無い物を、全部挙げてください。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**この問いが要る理由**：成り立たなければ、承認のときの「済」が根拠にならない。

設計書の完成の条件の表には、6 行の条件が書いてあります。
この条件が、実装の後に本当に成り立つかを確かめてください。
各行のコマンドを、作業場で走らせるか、読むだけの形で走らせてください。コマンドの中のパスは、`SDK` のフォルダからの相対です。そのため、どのコマンドも `SDK` のフォルダで走らせます。
走らせるコマンドは、次のとおりです。`python3 scripts/priority_rebuild/gen_indicator_table.py --verify`・`python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --selftest-p8`・`python3 scripts/priority_rebuild/observe_diag.py --selftest-known-ng`

### Q7 — まこさんの要望を、この工事の後の実装が満たしているか（優先度 A）

**この問いが要る理由**：満たしていない要望が在れば、まこさんの要望が届いていない。

下に並べた まこさんの要望を、この工事の後の実装が満たしているかを確かめてください。満たしていない要望があれば、その全部について、要望の番号と、足りない実装の行を示してください。1つでも満たしていない要望があれば、その指摘を Critical にします。

  1. 目的：指標の情報の読み込み元と繋ぎ先の全体を設計し直し、指標を1つのデータから読む形にする
  2. 役割の一覧から役割の情報を引いているのに、方向やトレンドの情報が食い違う仕組みを直す
  3. 後で大きなミスが見つからないように、指標に関するデータを全部 確かめ直してから設計する

### Q8 — 実装の後も、札・方向・性質・カタログの列・値域は、直す前と1つも違わないか（優先度 A）

**この問いが要る理由**：値が1つでも違えば、この工事は設計書の「値は1つも変えない」と違う。そうなると、engine_tuner の候補と材料の検査の結果が、まこさんの決定の外で変わる。

設計書は、この工事が値を1つも変えないと書いています（3-0・4-13 の2）。写しの道具は、当てる前と後の写しで、札の表・方向と性質・カタログの列の名前と並び・値域（有界と分位）・系統の区分が同じことを照らしました（ss_check.json）。
実装の後に、CC は、G-1 の表を作り直しました。型の表・出口の型の表・オン・オフの表・組み立ての表は、作り直す前の控えと1文字も同じでした（cmp）。本物の定義表を読み込んで、直す前と後の値を比べることは、CC はしていません。
次の2つに答えてください。
1つ目に、コミット 967b4ba5（直す前）と今の定義表・観察の道具を読み込み、札の表（FAMILY_LINEAGE）・各行の方向と性質（REFS の houkou と prop）・カタログの列の名前と並び・値域の一覧（_OSC_BOUNDS・_OSC_PCTL）が同じかを答えてください。
2つ目に、INDICATOR_TABLE の301行の方向・性質・値域・注記が、直す前の定義表の行・札の表・値域の一覧から写した値と同じかを答えてください。

### Q9 — 材料の検査の照らし・一覧の sha256 の照らし・省く判定は、設計書の 4-5 のとおりに動くか（優先度 A）

**この問いが要る理由**：照らしが動かなければ、新しい ❌ が監査に出す前のチェックを黙って通る。省く判定の指紋が漏れていれば、走らせるべきときに材料の検査を省く。

G-2 で、材料の検査は rc=0 でした（2,050秒）。❌ は、分かっている一覧の178行と1行も違いませんでした。一覧の sha256 は、pre_audit_check.py の KNOWN_MATERIALS の値（0c99daaa…）と同じです。材料の検査が通ったときの指紋は、pre_audit_materials_pass.json に書かれました。
次の3つに答えてください。
1つ目に、_known_ng_judge と selftest_known_ng と check_materials の分かれ方が、設計書の 4-5 の行（一覧に無い ❌ で rc 1・一覧に在る ❌ が出なくなったら rc 1・❌ が0件でも照らす）のとおりかを答えてください。
2つ目に、materials_fingerprint が指紋に入れるファイルが、材料の検査（observe_diag.py --check-materials）が読むファイルを全部 含むかを答えてください。CC は、scripts/priority_rebuild の直下の .py と .json・recipes の .json・5分足の CSV・一覧・印・V9 の3本と最後のコミットを入れました。
3つ目に、known_materials_problem が、一覧の中身を1文字でも変えたときに --run と --verify を止めるかを答えてください。
★CC の自己申告＝省く判定（設計書の 6-5 の7件目）は、本物で1回 動かしました。承認の控えを相手にした2回目の --run（--design に承認の控え）で、材料の検査は「省略」の行（rc 0）で終わりました。読むファイルの指紋が、1回目の --run で rc 0 で通ったとき（2026-10-23 11:06:17）と同じだったためです。2回目の記録は、pre_audit_check.json に在ります（1回目の記録は、この2回目で上書きされました）。また、KNOWN_MATERIALS の ok の欄と一覧の _OK の欄は、OK の逐語のファイルを `.claude/state/verbatim/m2c15-single-source-20261022/ok_proposal_20261023.txt` と書いています。承認の後、承認のプログラムは、このフォルダを acceptance_archive/verbatim/ に移しました。逐語のファイルの名前は、gen_verbatim.py で同じ名前のまま引けます。

### Q10 — 監査 CP86 の修正の入れ方と、当てた後の手順は、設計書のとおりか（優先度 A）

**この問いが要る理由**：修正の入れ方が設計書と違えば、承認した設計書と実装の間に、確かめていない違いが残る。

CC は、監査 CP86 の24件を、次のように入れました。
- やることの表への7件（修正9・10・11・12・19・20・21）は、当てる道具で当てました。修正10 の文の数字（別枠6種＝需給3…）は、2-1 の「読み方」の欄に数字を書けない決まり（gen_acceptance.py）に当たりました。そこで、数字を除いた同じ意味の文にしました。
- 案の写しへの15件は、案のひな型を直して案を組み直し、まこさんの OK を取り直しました。修正6 は、表の行を先に足し、定義表の行を後に足す順にしました（保存の瞬間の hook が --verify を掛けるため・設計書の 4-5）。
- 修正13・22（設計書の作り直し）は、当てる道具が実装の前の照合で止まって走らせなかったので、修正に書かれたコマンドを直接 走らせました。
- 修正24 の「確かめていないこと」の行の最後の欄は、CC がもう3つとも写しで走らせたので、「走らせた」と書きました。
当てた後は、設計書の 4-12 の順に、表の照らし・軽い口・全体の自己テスト・G-1・G-2 を走らせ、どれも rc=0 でした。新しい hook は、まこさんが settings.json の152行目に登録しました。試しの道具（try_hooks.py）で、表の RSI の行の性質を手で書き替える直しを試すと、この hook が⑥で止めました。
次の2つに答えてください。
1つ目に、実装の314件が、承認した設計書の 4-20（ss_impl.json の sha256 b2aab886…）と1件も違わずに当たっているかを、git diff 967b4ba5 で答えてください。
2つ目に、新しい hook の登録が、設計書の 4-23 の行（PreToolUse Write|Edit|MultiEdit の欄）のとおりかを答えてください。

---

## 問いの外から当てる視点

### 一般の観点（①〜⑦・どの監査でも当てる）

問いに無いことも、次の7つの観点で見てください。観点ごとに、見つけたことと、その根拠を、結果の所見に書きます。何も見つからなかった観点には、「見つからなかった」と書き、何を見たかを書きます。

- ①統計学的妥当性：数字の根拠が足りているかを見ます。
- ②リスク管理：損失が出たときや、プログラムが壊れたときの備えが在るかを見ます。
- ③認知バイアス：CC の思い込みで組まれた所が無いかを見ます。
- ④ソフトウェア工学：プログラムの作りが正しいかを見ます。重複・壊れやすさ・テストの抜けが、見る物です。
- ⑤再現性：同じ手順で、同じ結果が出るかを見ます。
- ⑥実行プロセス：CC が、決めた流れのとおりに進めたかを見ます。
- ⑦主エージェントバイアス：CC が、自分に都合よく判定した所が無いかを見ます。

### 外の基準で確かめること（外部検索・WebSearch／WebFetch）

依頼書の中の文書だけで判断しないでください。次の物を、外の出どころで確かめます。外の出どころは、教科書・公式の文書・業界の標準・論文です。結果に、ページの URL と、使った文の逐語を書きます。

件数: 1 件。結果の外部検索で、この件数の調べる物に1つずつ答えてください。

1. **置き場を1つにする作り（single source of truth）**:
   - 検索の言葉: single source of truth generated table verify hash
   - 何と照らすか: 新しく Web を開いていない。要件定義の7番の文（誤りは置き場の1か所を直せば済む）と、まこさんの指示「指標は１つデータから読み込むようにできないの？」を出どころにした。実装の監査では、この出どころと、実装の該当の所が合うかを照らします

---

## CC がまだ確かめていないこと

次の一覧は、依頼を出した CC が、まだ測っていないことと、まだ確かめていないことです。監査人は、この一覧を自分で測る必要はありません。番号ごとに、確かめないまま実装に進んでよいかを1件ずつ答えてください。進めてはいけない件には、その理由と、先に走らせるべきコマンドを書いてください。

1. **承認の後に設計書を作り直した**：CC は、承認の後に設計書を作り直しました。前の版は `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-single-source-20261022.01.md` で、いまの版は `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-single-source-20261022.md` です。違いは、次のとおりです。囲みの外で 12 行（実装の指示の囲み ACC_IMPL は同じ）
2. **この工事の外の作業中の変更**：次のファイルには、作業中の変更があります。`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_request_understood.sh`・`.claude/tools/gen_audit_docs.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`。この変更は、この工事の実装の指示が当てた物ではありません。そのため、Q1 と Q2 の差分を、この工事の対象のファイルだけで取ってください。

---

## 着手前必読（省略禁止・31 件）

**パスは、リポジトリの根（`cat-bitget/`）からの相対です。**`SDK` は、`v3-bitget-api-sdk/bitget-python-sdk-api` の略です。

1. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-single-source-20261022.md`（全文） — 監査の相手の設計書です。プログラムが作りました。まこさんが承認した版の設計書の控えです。どの版の 4-20 で当てたかは、Q4 で照らします。このファイルは、承認した設計書の控えです。実装の指示は314件で、完成の条件は6行です。4-5・4-12・4-13・4-23 は、Q8〜Q10 で照らします。
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-single-source-20261022.01.md` — まこさんが承認した版の設計書の控えです。どの版の 4-20 で当てたかは、Q4 で照らします。
3. `SDK/.claude/audits/applied_fixes.json` — 当てる道具が書いた、当てた記録です。この工事の行の名前は design:m2c15-single-source-20261022 です。
4. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-single-source-20261022/やることの表.md`（全文） — 設計書の元（やることの表）です。監査人は、修正の指示をこのファイルに書きます。このファイルは、設計書の元データです。一覧（F-1・F-2・F-4・G-1・G-2）と、やらないこと（1〜7）が書いてあります。
5. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — このファイルには、目標と全体戦略とハード制約が書いてあります。目標は、全月 net ≥ $1,900 です。
6. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-232） — このファイルには、engine_tuner の目的と、探し方の要件と、作ってはいけない物が書いてあります。
7. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:124-146） — このファイルには、M2 が M1〜M6 のどこに当たるかが書いてあります。
8. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:81-130） — このファイルには、M2 で作っている物が書いてあります。この工事は M2-C-15（指標の修正）の1つです。
9. `SDK/.claude/ratchet/acceptance_archive/m2c15-single-source-20261022.breaks.json`（全文） — このファイルは、承認のプログラムが壊すプログラム6本と条件のコマンドを走らせた記録です。Q6 は、この記録を見ます。
10. `.claude/state/indicator_review/ss_impl.json`（全文） — このファイルには、実装の指示314件の中身（直す前の文字と直した後の文字）が在ります。設計書の 4-20 は、このファイルから写しています。
11. `SDK/scripts/priority_rebuild/indicator_reference_diag.py`（:956-1260・:1263-1285・:5470-5481） — このファイルは、定義表です。読む範囲には、指標1種につき1行の表 INDICATOR_TABLE と、行を登録する関数 `_r` と、札の表を表から作る関数 `_lineage_from_table` が在ります。Q8 は、この範囲を見ます。
12. `SDK/scripts/priority_rebuild/gen_indicator_table.py`（全文） — このファイルは、表を書く・照らす新しい道具です。照らしの①〜⑥と、新しい種類を足す口 --add が在ります。
13. `.claude/state/indicator_roles_thresholds.json`（全文） — このファイルは、資料の表の1つです。新しい道具は、表の役割の欄をここから写します。Q8 は、このファイルを見ます。
14. `.claude/state/indicator_review/r1_role_map.json`（全文） — このファイルは、R-1 の90種の札の正本です（封つき）。新しい道具は、90種の役割の区分をここから写します。Q8 は、このファイルを見ます。
15. `SDK/scripts/priority_rebuild/observe_diag.py`（:6066-6100・:6175-6195・:6387-6485・:8970-8980・:9000-9025） — このファイルは、観察の道具です。読む範囲には、値域の一覧・印を読む関数 `_switch_on`・材料の検査1 の「役割の欄が空」の行・材料の検査の照らし `_known_ng_judge` と口 `selftest_known_ng`・入口の旗が在ります。Q9 は、この範囲を見ます。
16. `.claude/tools/pre_audit_check.py`（:58-120・:170-300・:350-365・:705-720） — このファイルは、監査に出す前のチェックです。読む範囲には、材料の検査の名前・CHECKS・指紋の対象・一覧の sha256 の照らし（KNOWN_MATERIALS）・省く判定（materials_row）・番人 P8 の口が在ります。Q9 は、この範囲を見ます。
17. `.claude/state/indicator_review/check_materials_known_ng.json`（全文） — このファイルは、分かっている ❌ の一覧です（178行）。Q9 は、この一覧を見ます。
18. `.claude/state/pre_audit_check.json`（全文） — このファイルは、G-2 の監査に出す前のチェックの記録です。Q9 は、この記録を見ます。
19. `.claude/state/pre_audit_materials_pass.json`（全文） — このファイルは、材料の検査が rc 0 で通ったときの指紋の記録です。Q9 は、この記録を見ます。
20. `.claude/hooks/check_indicator_table_on_save.py`（全文） — このファイルは、定義表を保存する瞬間に照らす新しい hook です。Q10 は、このファイルを見ます。
21. `.claude/hooks/check_indicator_table_on_save.sh`（全文） — このファイルは、新しい hook の入口です。
22. `.claude/settings.json`（:125-158） — この範囲には、新しい hook の登録が在ります。Q10 は、この範囲を見ます。
23. `.claude/breaks/b182_copy_mark_without_known.sh`（全文） — この壊すプログラムは、壊す文字を新しい行の形に直しました（実装301・302）。
24. `.claude/breaks/b199_adx_back_to_trend.sh`（全文） — この壊すプログラムは、壊す文字を新しい行の形に直しました（実装303・304）。
25. `.claude/breaks/b204_table_role_handwritten.sh` — 新しい壊すプログラムです。表の ADX の役割の区分を手で書き替えます（完成の条件の1行目・Q6）。
26. `.claude/breaks/b205_row_arg_back.sh` — 新しい壊すプログラムです。ADX の行に方向と性質の引数を戻します（完成の条件の2行目・Q6）。
27. `.claude/breaks/b206_lineage_handwritten.sh` — 新しい壊すプログラムです。札の表を手書きの辞書に戻します（完成の条件の3行目・Q6）。
28. `.claude/breaks/b207_table_check_dropped.sh` — 新しい壊すプログラムです。CHECKS から表の照らしの行を外します（完成の条件の4行目・Q6）。
29. `.claude/breaks/b208_known_ng_new_ignored.sh` — 新しい壊すプログラムです。--known-ng の照らしで、一覧に無い ❌ を数えない形にします（完成の条件の5行目・Q6）。
30. `.claude/breaks/b209_table_prop_handwritten.sh` — 新しい壊すプログラムです。表の RSI の行の性質の欄を手で書き替えます（完成の条件の6行目・Q6）。
31. `.claude/state/session_worklog_20261023.md`（全文） — このファイルは、監査 CP86 の結果の確認から G-2 までの記録です。

★この一覧には、直す相手のファイルが必ず入っています。結果の「修正の指示」の「直す前の文字」を、このファイルの実物から写します。

---

## 事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 956〜957行（_r・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 965〜966行（_r・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 3 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 968行（_r・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 4 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1008行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 5 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1011行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 6 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1014〜1015行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 7 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1027〜1028行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 8 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1031〜1032行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 9 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1035〜1036行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 10 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1039行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 11 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1042行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 12 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1046行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 13 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1049〜1050行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 14 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1053〜1054行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 15 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1062〜1063行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 16 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1066〜1067行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 17 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1070〜1071行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 18 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1080〜1081行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 19 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1086〜1087行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 20 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1091〜1092行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 21 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1096〜1097行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 22 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1100〜1101行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 23 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1104行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 24 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1107行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 25 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1111〜1112行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 26 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1116〜1118行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 27 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1123行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 28 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1128〜1129行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 29 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1136〜1137行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 30 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1144行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 31 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1148行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 32 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1151行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 33 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1155行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 34 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1159行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 35 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1164〜1165行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 36 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1168行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 37 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1171〜1173行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 38 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1178〜1180行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 39 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1186〜1187行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 40 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1197〜1198行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 41 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1206〜1207行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 42 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1211〜1212行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 43 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1217〜1218行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 44 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1222〜1223行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 45 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1231〜1232行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 46 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1236行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 47 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1239行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 48 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1243〜1244行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 49 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1281〜1282行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 50 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1289〜1290行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 51 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1294〜1295行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 52 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1298〜1299行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 53 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1303〜1304行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 54 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1319〜1320行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 55 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1324行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 56 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1329〜1330行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 57 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1334〜1335行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 58 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1340〜1341行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 59 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1359〜1360行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 60 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1362〜1363行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 61 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1365〜1366行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 62 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1384〜1385行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 63 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1387〜1388行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 64 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1390〜1391行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 65 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1393行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 66 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1397〜1398行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 67 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1404〜1405行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 68 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1411〜1412行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 69 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1438〜1439行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 70 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1444〜1445行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 71 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1450〜1451行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 72 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1470行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 73 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1494〜1495行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 74 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1500〜1501行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 75 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1676〜1677行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 76 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1684〜1685行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 77 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1690〜1691行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 78 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1921〜1922行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 79 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1926〜1927行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 80 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1933〜1934行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 81 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1937〜1938行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 82 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1942〜1943行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 83 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1946〜1947行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 84 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1951〜1952行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 85 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1955〜1956行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 86 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1962〜1963行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 87 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1968〜1969行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 88 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1975〜1976行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 89 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2132〜2133行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 90 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2139〜2140行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 91 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2143〜2144行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 92 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2146〜2147行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 93 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2149〜2150行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 94 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2153〜2154行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 95 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2157〜2158行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 96 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2161〜2162行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 97 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2165〜2166行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 98 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2173〜2174行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 99 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2181行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 100 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2189〜2190行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 101 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2197〜2198行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 102 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2202〜2203行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 103 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2208〜2209行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 104 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3366〜3367行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 105 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3370〜3371行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 106 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3374行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 107 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3377行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 108 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3380行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 109 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3383行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 110 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3386行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 111 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3389〜3390行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 112 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3393行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 113 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3396行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 114 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3399行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 115 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3402行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 116 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3406〜3407行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 117 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3410行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 118 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3413行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 119 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3416行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 120 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3419行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 121 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3423行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 122 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3426行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 123 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3431〜3432行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 124 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3435行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 125 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3437行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 126 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3439行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 127 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3442〜3443行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 128 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3446行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 129 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3450〜3451行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 130 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3460行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 131 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3463〜3464行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 132 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3467〜3468行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 133 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3471行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 134 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3475〜3476行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 135 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3479行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 136 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3481行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 137 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3485〜3486行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 138 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3489行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 139 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3491行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 140 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3493行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 141 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3496〜3497行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 142 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3499行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 143 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3501〜3502行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 144 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3506〜3507行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 145 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3510行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 146 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3515行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 147 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3521〜3522行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 148 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3525〜3526行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 149 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3529行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 150 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3532行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 151 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3536〜3537行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 152 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3545行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 153 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3554行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 154 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3556行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 155 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3559〜3560行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 156 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3562行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 157 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3565〜3566行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 158 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3568行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 159 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3570〜3571行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 160 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3574行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 161 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3576行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 162 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3579行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 163 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3582〜3583行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 164 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3586〜3587行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 165 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3589行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 166 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3591〜3592行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 167 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3612行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 168 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3617行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 169 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3623行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 170 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3625行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 171 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3628行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 172 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3630行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 173 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3633〜3634行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 174 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3640行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 175 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3642行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 176 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3645〜3647行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 177 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3650〜3651行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 178 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3655〜3656行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 179 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3659行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 180 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3661行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 181 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3664行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 182 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3666行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 183 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3675〜3676行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 184 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3684〜3685行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 185 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3688〜3689行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 186 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3692〜3694行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 187 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3697〜3698行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 188 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3701〜3702行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 189 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3705〜3706行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 190 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3709〜3710行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 191 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3713〜3714行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 192 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3717〜3718行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 193 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3723〜3724行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 194 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3728〜3729行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 195 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3736〜3737行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 196 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3740〜3741行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 197 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3744〜3745行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 198 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3748〜3749行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 199 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3752〜3753行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 200 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3756〜3757行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 201 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3761〜3763行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 202 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3766〜3767行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 203 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3770〜3771行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 204 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3774〜3775行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 205 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3778〜3779行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 206 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3787行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 207 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3790行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 208 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3792行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 209 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3795行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 210 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3801行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 211 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3805行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 212 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3807〜3808行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 213 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3810行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 214 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3813〜3814行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 215 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3832〜3833行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 216 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3836〜3837行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 217 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3843〜3844行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 218 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3851〜3852行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 219 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3857〜3858行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 220 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3862〜3863行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 221 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3866行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 222 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3870〜3871行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 223 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3875行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 224 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3879行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 225 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3882行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 226 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3885行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 227 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3887〜3888行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 228 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4102〜4103行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 229 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4108〜4109行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 230 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4113〜4114行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 231 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4120〜4121行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 232 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4126〜4127行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 233 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4132〜4133行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 234 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4137〜4138行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 235 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4143〜4144行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 236 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4148〜4149行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 237 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4153〜4154行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 238 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4161〜4162行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 239 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4166〜4167行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 240 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4223〜4224行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 241 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4232〜4233行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 242 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4316行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 243 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4320〜4321行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 244 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4326〜4327行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 245 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4331〜4332行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 246 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4336〜4337行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 247 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4340〜4341行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 248 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4345〜4346行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 249 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4542〜4543行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 250 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4548〜4549行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 251 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4553〜4554行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 252 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4557〜4560行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 253 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4564〜4565行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 254 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4568〜4569行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 255 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4574〜4575行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 256 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4581〜4582行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 257 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4585行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 258 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4590〜4591行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 259 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4597〜4598行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 260 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4603〜4604行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 261 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4608行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 262 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4618行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 263 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4626行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 264 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4631〜4632行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 265 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4850〜4851行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 266 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4858〜4859行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 267 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4867〜4868行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 268 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4871行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 269 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4876〜4877行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 270 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4881〜4882行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 271 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4885行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 272 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4891〜4892行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 273 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4900〜4901行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 274 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4906〜4907行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 275 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 5007〜5008行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 276 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 5013〜5014行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 277 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 5023〜5024行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 278 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 5028〜5029行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 279 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 5033〜5034行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 280 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 5042〜5043行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 281 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 5048〜5049行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 282 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 5055〜5056行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 283 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 5337〜5554行（<モジュール直下>・F-1・F-2＝INDICATOR_TABLE を置き、_r が表から方向・性質を読み、札の表を表から作る（値は変えない）） | 直した後の文字 |
| 284 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6071〜6075行（<モジュール直下>・F-4＝値域を表から読む・検査1 に役割の欄が空の ❌（印が「使う」の種類だけ・監査 CP86 の修正12）・--known-ng と、その照らしだけを試す口 --selftest-known-ng（修正1・2・18）） | 直した後の文字 |
| 285 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6078行（<モジュール直下>・F-4＝値域を表から読む・検査1 に役割の欄が空の ❌（印が「使う」の種類だけ・監査 CP86 の修正12）・--known-ng と、その照らしだけを試す口 --selftest-known-ng（修正1・2・18）） | 直した後の文字 |
| 286 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6167行（_insp_direction_known・F-4＝値域を表から読む・検査1 に役割の欄が空の ❌（印が「使う」の種類だけ・監査 CP86 の修正12）・--known-ng と、その照らしだけを試す口 --selftest-known-ng（修正1・2・18）） | 直した後の文字 |
| 287 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6363行（check_materials・F-4＝値域を表から読む・検査1 に役割の欄が空の ❌（印が「使う」の種類だけ・監査 CP86 の修正12）・--known-ng と、その照らしだけを試す口 --selftest-known-ng（修正1・2・18）） | 直した後の文字 |
| 288 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6365行（check_materials・F-4＝値域を表から読む・検査1 に役割の欄が空の ❌（印が「使う」の種類だけ・監査 CP86 の修正12）・--known-ng と、その照らしだけを試す口 --selftest-known-ng（修正1・2・18）） | 直した後の文字 |
| 289 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6389〜6392行（check_materials・F-4＝値域を表から読む・検査1 に役割の欄が空の ❌（印が「使う」の種類だけ・監査 CP86 の修正12）・--known-ng と、その照らしだけを試す口 --selftest-known-ng（修正1・2・18）） | 直した後の文字 |
| 290 | `SDK/scripts/priority_rebuild/observe_diag.py` | 8891行（build_parser・F-4＝値域を表から読む・検査1 に役割の欄が空の ❌（印が「使う」の種類だけ・監査 CP86 の修正12）・--known-ng と、その照らしだけを試す口 --selftest-known-ng（修正1・2・18）） | 直した後の文字 |
| 291 | `SDK/scripts/priority_rebuild/observe_diag.py` | 8919行（<モジュール直下>・F-4＝値域を表から読む・検査1 に役割の欄が空の ❌（印が「使う」の種類だけ・監査 CP86 の修正12）・--known-ng と、その照らしだけを試す口 --selftest-known-ng（修正1・2・18）） | 直した後の文字 |
| 292 | `SDK/scripts/priority_rebuild/observe_diag.py` | 8936行（<モジュール直下>・F-4＝値域を表から読む・検査1 に役割の欄が空の ❌（印が「使う」の種類だけ・監査 CP86 の修正12）・--known-ng と、その照らしだけを試す口 --selftest-known-ng（修正1・2・18）） | 直した後の文字 |
| 293 | `.claude/tools/pre_audit_check.py` | 58行（<モジュール直下>・F-4＝監査に出す前のチェックに表の照らしと材料の検査を足す・一覧の sha256 を照らす（監査 CP86 の修正7）・指紋が前回 rc 0 と同じなら材料の検査を省く（修正8）） | 直した後の文字 |
| 294 | `.claude/tools/pre_audit_check.py` | 86行（<モジュール直下>・F-4＝監査に出す前のチェックに表の照らしと材料の検査を足す・一覧の sha256 を照らす（監査 CP86 の修正7）・指紋が前回 rc 0 と同じなら材料の検査を省く（修正8）） | 直した後の文字 |
| 295 | `.claude/tools/pre_audit_check.py` | 92行（<モジュール直下>・F-4＝監査に出す前のチェックに表の照らしと材料の検査を足す・一覧の sha256 を照らす（監査 CP86 の修正7）・指紋が前回 rc 0 と同じなら材料の検査を省く（修正8）） | 直した後の文字 |
| 296 | `.claude/tools/pre_audit_check.py` | 105行（<モジュール直下>・F-4＝監査に出す前のチェックに表の照らしと材料の検査を足す・一覧の sha256 を照らす（監査 CP86 の修正7）・指紋が前回 rc 0 と同じなら材料の検査を省く（修正8）） | 直した後の文字 |
| 297 | `.claude/tools/pre_audit_check.py` | 154〜155行（<モジュール直下>・F-4＝監査に出す前のチェックに表の照らしと材料の検査を足す・一覧の sha256 を照らす（監査 CP86 の修正7）・指紋が前回 rc 0 と同じなら材料の検査を省く（修正8）） | 直した後の文字 |
| 298 | `.claude/tools/pre_audit_check.py` | 193〜194行（run・F-4＝監査に出す前のチェックに表の照らしと材料の検査を足す・一覧の sha256 を照らす（監査 CP86 の修正7）・指紋が前回 rc 0 と同じなら材料の検査を省く（修正8）） | 直した後の文字 |
| 299 | `.claude/tools/pre_audit_check.py` | 262〜263行（verify_problems・F-4＝監査に出す前のチェックに表の照らしと材料の検査を足す・一覧の sha256 を照らす（監査 CP86 の修正7）・指紋が前回 rc 0 と同じなら材料の検査を省く（修正8）） | 直した後の文字 |
| 300 | `.claude/tools/pre_audit_check.py` | 610行（main・F-4＝監査に出す前のチェックに表の照らしと材料の検査を足す・一覧の sha256 を照らす（監査 CP86 の修正7）・指紋が前回 rc 0 と同じなら材料の検査を省く（修正8）） | 直した後の文字 |
| 301 | `.claude/breaks/b182_copy_mark_without_known.sh` | 9行（設定・F-2＝前からの壊すプログラムの壊す文字から、消える引数（"反転サイン", "none"）を外す（壊し方と測る物は同じ）） | 直した後の文字 |
| 302 | `.claude/breaks/b182_copy_mark_without_known.sh` | 19〜20行（設定・F-2＝前からの壊すプログラムの壊す文字から、消える引数（"反転サイン", "none"）を外す（壊し方と測る物は同じ）） | 直した後の文字 |
| 303 | `.claude/breaks/b199_adx_back_to_trend.sh` | 9行（設定・F-2＝前からの壊すプログラムの壊す文字を、札の辞書の1件から INDICATOR_TABLE の ADX の行にする（壊し方と測る物は同じ）） | 直した後の文字 |
| 304 | `.claude/breaks/b199_adx_back_to_trend.sh` | 19〜20行（設定・F-2＝前からの壊すプログラムの壊す文字を、札の辞書の1件から INDICATOR_TABLE の ADX の行にする（壊し方と測る物は同じ）） | 直した後の文字 |
| 305 | `SDK/scripts/priority_rebuild/gen_indicator_table.py` | なし（新しいファイル） | 直した後の文字 |
| 306 | `.claude/hooks/check_indicator_table_on_save.py` | なし（新しいファイル） | 直した後の文字 |
| 307 | `.claude/hooks/check_indicator_table_on_save.sh` | なし（新しいファイル） | 直した後の文字 |
| 308 | `.claude/state/indicator_review/check_materials_known_ng.json` | なし（新しいファイル） | 直した後の文字 |
| 309 | `.claude/breaks/b204_table_role_handwritten.sh` | なし（新しいファイル） | 直した後の文字 |
| 310 | `.claude/breaks/b205_row_arg_back.sh` | なし（新しいファイル） | 直した後の文字 |
| 311 | `.claude/breaks/b206_lineage_handwritten.sh` | なし（新しいファイル） | 直した後の文字 |
| 312 | `.claude/breaks/b207_table_check_dropped.sh` | なし（新しいファイル） | 直した後の文字 |
| 313 | `.claude/breaks/b208_known_ng_new_ignored.sh` | なし（新しいファイル） | 直した後の文字 |
| 314 | `.claude/breaks/b209_table_prop_handwritten.sh` | なし（新しいファイル） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:m2c15-single-source-20261022）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 2 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 3 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 4 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 5 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 6 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 7 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 8 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 9 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 10 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 11 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 12 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 13 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 14 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 15 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 16 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 17 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 18 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 19 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 20 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 21 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 22 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 23 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 24 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 25 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 26 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 27 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 28 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 29 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 30 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 31 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 32 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 33 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 34 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 35 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 36 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 37 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 38 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 39 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 40 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 41 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 42 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 43 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 44 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 45 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 46 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 47 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 48 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 49 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 50 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 51 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 52 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 53 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 54 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 55 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 56 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 57 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 58 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 59 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 60 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 61 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 62 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 63 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 64 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 65 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 66 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 67 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 68 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 69 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 70 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 71 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 72 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 73 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 74 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 75 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 76 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 77 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 78 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 79 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 80 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 81 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 82 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 83 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 84 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 85 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 86 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 87 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 88 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 89 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 90 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 91 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 92 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 93 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 94 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 95 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 96 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 97 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 98 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 99 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 100 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 101 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 102 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 103 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 104 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 105 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 106 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 107 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 108 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 109 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 110 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 111 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 112 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 113 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 114 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 115 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 116 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 117 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 118 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 119 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 120 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 121 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 122 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 123 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 124 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 125 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 126 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 127 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 128 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 129 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 130 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 131 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 132 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 133 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 134 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 135 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 136 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 137 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 138 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 139 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 140 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 141 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 142 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 143 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 144 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 145 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 146 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 147 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 148 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 149 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 150 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 151 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 152 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 153 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 154 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 155 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 156 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 157 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 158 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 159 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 160 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 161 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 162 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 163 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 164 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 165 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 166 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 167 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 168 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 169 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 170 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 171 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 172 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 173 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 174 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 175 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 176 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 177 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 178 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 179 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 180 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 181 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 182 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 183 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 184 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 185 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 186 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 187 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 188 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 189 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 190 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 191 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 192 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 193 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 194 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 195 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 196 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 197 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 198 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 199 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 200 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 201 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 202 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 203 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 204 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 205 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 206 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 207 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 208 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 209 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 210 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 211 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 212 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 213 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 214 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 215 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 216 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 217 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 218 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 219 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 220 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 221 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 222 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 223 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 224 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 225 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 226 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 227 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 228 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 229 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 230 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 231 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 232 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 233 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 234 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 235 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 236 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 237 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 238 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 239 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 240 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 241 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 242 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 243 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 244 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 245 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 246 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 247 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 248 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 249 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 250 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 251 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 252 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 253 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 254 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 255 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 256 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 257 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 258 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 259 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 260 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 261 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 262 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 263 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 264 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 265 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 266 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 267 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 268 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 269 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 270 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 271 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 272 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 273 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 274 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 275 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 276 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 277 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 278 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 279 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 280 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 281 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 282 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 283 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 284 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 285 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 286 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 287 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 288 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 289 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 290 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 291 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 292 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-23T09:19:30 |
| 293 | `.claude/tools/pre_audit_check.py` | 当てた | 2026-10-23T09:19:30 |
| 294 | `.claude/tools/pre_audit_check.py` | 当てた | 2026-10-23T09:19:30 |
| 295 | `.claude/tools/pre_audit_check.py` | 当てた | 2026-10-23T09:19:30 |
| 296 | `.claude/tools/pre_audit_check.py` | 当てた | 2026-10-23T09:19:30 |
| 297 | `.claude/tools/pre_audit_check.py` | 当てた | 2026-10-23T09:19:30 |
| 298 | `.claude/tools/pre_audit_check.py` | 当てた | 2026-10-23T09:19:30 |
| 299 | `.claude/tools/pre_audit_check.py` | 当てた | 2026-10-23T09:19:30 |
| 300 | `.claude/tools/pre_audit_check.py` | 当てた | 2026-10-23T09:19:30 |
| 301 | `.claude/breaks/b182_copy_mark_without_known.sh` | 当てた | 2026-10-23T09:19:30 |
| 302 | `.claude/breaks/b182_copy_mark_without_known.sh` | 当てた | 2026-10-23T09:19:30 |
| 303 | `.claude/breaks/b199_adx_back_to_trend.sh` | 当てた | 2026-10-23T09:19:30 |
| 304 | `.claude/breaks/b199_adx_back_to_trend.sh` | 当てた | 2026-10-23T09:19:30 |
| 305 | `SDK/scripts/priority_rebuild/gen_indicator_table.py` | 当てた | 2026-10-23T09:19:30 |
| 306 | `.claude/hooks/check_indicator_table_on_save.py` | 当てた | 2026-10-23T09:19:30 |
| 307 | `.claude/hooks/check_indicator_table_on_save.sh` | 当てた | 2026-10-23T09:19:30 |
| 308 | `.claude/state/indicator_review/check_materials_known_ng.json` | 当てた | 2026-10-23T09:19:30 |
| 309 | `.claude/breaks/b204_table_role_handwritten.sh` | 当てた | 2026-10-23T09:19:30 |
| 310 | `.claude/breaks/b205_row_arg_back.sh` | 当てた | 2026-10-23T09:19:30 |
| 311 | `.claude/breaks/b206_lineage_handwritten.sh` | 当てた | 2026-10-23T09:19:30 |
| 312 | `.claude/breaks/b207_table_check_dropped.sh` | 当てた | 2026-10-23T09:19:30 |
| 313 | `.claude/breaks/b208_known_ng_new_ignored.sh` | 当てた | 2026-10-23T09:19:30 |
| 314 | `.claude/breaks/b209_table_prop_handwritten.sh` | 当てた | 2026-10-23T09:19:30 |

### 実装の前と後の版（git）

- **実装の前**：commit 967b4ba5（承認の控えを入れた commit 1a5656a5 の1つ前）
- **実装の後**：作業中の変更（まだ commit していない。承認の控えだけを commit 1a5656a5 に先に入れたので、その commit には実装が入っていない。`git diff 967b4ba5 -- <パス>` で見られる。git に無い新しいファイル（10本）は、本物のファイルをそのまま読む。★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、`git diff 967b4ba5 <その commit> -- <パス>` で見る）。★この工事の中で、設計書の 4-4 の手順（G-1 の表の作り直しほか）の道具が、TARGET のファイルを書き出し直すことがある（例＝gen_materials.py --write が regime_detection_kb.md の件数の囲みを書き出す）。その行は実装の指示ではなく、設計書の 4-4・5 で照らす

### 必読に要るファイル（道具が設計書と実装から拾った）

| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15） | 入れる |
| `.claude/breaks/b182_copy_mark_without_known.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b199_adx_back_to_trend.sh` | 直す相手（TARGET） | 入れる |
| `.claude/tools/pre_audit_check.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/gen_indicator_table.py` | 直す相手（TARGET） | 入れる |
| `.claude/hooks/check_indicator_table_on_save.py` | 直す相手（TARGET） | 入れる |
| `.claude/hooks/check_indicator_table_on_save.sh` | 直す相手（TARGET） | 入れる |
| `.claude/state/indicator_review/check_materials_known_ng.json` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b204_table_role_handwritten.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b205_row_arg_back.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b206_lineage_handwritten.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b207_table_check_dropped.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b208_known_ng_new_ignored.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b209_table_prop_handwritten.sh` | 直す相手（TARGET） | 入れる |
| `SDK/.claude/ratchet/indicator_switch.json` | `.claude/tools/pre_audit_check.py` が名前を出す（実装の前後の差分） | 入れない（pre_audit_check.py は、材料の検査を省く指紋の対象として、このファイルの名前を出すだけです。中身は G-1 で作り直す前と1文字も同じでした（cmp）。Q9 で見るのは、指紋の対象の並びです） |
| `.claude/state/pre_audit_materials_pass.json` | `.claude/tools/pre_audit_check.py` が名前を出す（実装の前後の差分） | 入れる |
| `SDK/data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv` | `.claude/tools/pre_audit_check.py` が名前を出す（実装の前後の差分） | 入れない（pre_audit_check.py は、材料の検査の入力と指紋の対象として、このファイルの名前を出すだけです。約37MB の5分足のデータで、この工事は直しません） |
| `SDK/scripts/priority_rebuild/gen_composition_rules.py` | `.claude/tools/pre_audit_check.py` が名前を出す（実装の前後の差分） | 入れない（pre_audit_check.py は、前からの CHECKS の行として、このファイルの名前を出すだけです。この工事は直しません） |
| `.claude/state/indicator_review/ss_impl.json` | `.claude/tools/pre_audit_check.py` が名前を出す（実装の前後の差分） | 入れる |
| `.claude/state/indicator_review/research/out_w1.json` | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` が名前を出す（実装の前後の差分） | 入れない（定義表は、表の行の役割の出どころの文の中で、このファイルの名前を出すだけです（R-1 の決定 D7オ）。表は、このファイルを読みません） |
| `.claude/state/indicator_review/r1_role_map.json` | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` が名前を出す（実装の前後の差分） | 入れる |
| `.claude/state/indicator_review/build_role_threshold_table.py` | `SDK/scripts/priority_rebuild/gen_indicator_table.py` が名前を出す（全文） | 入れない（新しい道具は、説明の文の中で、札の対応（LIN2CAT の逆）の出どころとして、このファイルの名前を出すだけです。新しい道具は、このファイルを読みません） |
| `.claude/state/indicator_roles_thresholds.json` | `SDK/scripts/priority_rebuild/gen_indicator_table.py` が名前を出す（全文） | 入れる |

---

## 答えの出し方（結果ファイルフォーマット）

### 結果の11節（名前と並びは変えない・どの種類の監査でも同じ）

結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-23_m2c15_single_source_20261022_impl_cp87_audit_report.md` に、次の 11 節を、この順で書きます。

| # | 結果の節 | 依頼書の対応する項目 |
|---|---|---|
| 1 | **監査の相手と版**（依頼書のパス・監査の相手・ハッシュ値を照らした結果・実施日） | 監査依頼メタ情報 |
| 2 | **監査対象の型宣言**（数値型・コード型・文書型のうち、当てはまる物の全部） | —（結果だけ） |
| 3 | **監査対象の事実データの確認**（あなたが、依頼書の事実データを自分で確かめた結果） | 事実データ |
| 4 | **所見**（問いの番号ごとの答えと、一般の観点ごとの答え） | 確かめてほしいこと・問いの外から当てる視点 |
| 5 | **外部検索**（依頼書の調べる物ごとに、URL と逐語） | 外の基準で確かめること |
| 6 | **依頼を出した CC の自己申告への答え**（依頼書の番号ごとに1件ずつ） | CC がまだ確かめていないこと |
| 7 | **総合判定**（結論と、その根拠と、重さごとの件数） | 答えの出し方 |
| 8 | **修正の指示**（重さが Critical・Major・Minor の修正） | 着手前必読（直す相手のファイル） |
| 9 | **CC プロセス欠陥対策**（重さが Process の修正） | —（結果だけ） |
| 10 | **開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由** | 着手前必読 |
| 11 | **本物のファイルを書き替えていないこと**（`git status --short` の出力） | 監査人への宣言の禁止 |

4 の所見について、次の4つを守ってください。
- 各所見の終わりに、その所見に対応する修正の番号を書きます。
- 所見に、直し方の文を書きません。直し方は、8 と 9 の修正の指示に書きます。
- 答えなかった問いの番号を書きます。
- 一般の観点①〜⑦ごとに、見つけたことと根拠を書きます。

### 重さと結論

- Critical は、監査の結論を変える重さです。Major は、直すべきですが、結論は変えない重さです。Minor は、結論に使わない重さです。Process は、CC の進め方の欠陥の重さで、9 に書きます。
- 結論が GO になるのは、Critical が0件のときです。結論が CONDITIONAL-GO になるのは、Critical が在り、それを直せば先に進めるときです。結論が NO-GO になるのは、直し方の向きそのものが違うときです。NO-GO のとき、何が違うかを、4 の所見に、指摘の文と実物の行で示します。
- どこまで直すかは、まこさんが結果を見て決めます。そのため、修正を、重さの見出し（「### Critical」「### Major」「### Minor」「### Process」）の下に並べます。

### 修正の指示の書き方（★この形以外では書けない）

この形を決めた目的は、監査が書いた修正のとおりに、プログラムが直しを当てるためです。CC が修正の文を書き替えたり、小さく直したりすることを、この形で止めます。
- どの種類の監査でも、同じ欄で修正を書きます。
- 直す相手が設計書でも、コードでも、設定でも、文書でも、走らせるコマンドでも、同じ欄で書きます。
- どの修正も、プログラムがそのまま当てられる形で書きます。CC は、修正の文も数も打ちません。
- 修正の番号を、4 の所見の終わりに書いた番号と同じにします。所見の無い修正を書きません。あなたが所見に書いた修正の番号は、必ず 8 か 9 に在るようにします。

1件を、次の形で書きます。

```text
### Critical

#### 修正 <番号>
対象のファイル: <リポジトリの中のパス>
直す箇所: <監査が読んだ時点の行番号の範囲>
直す前の文字:
~~~
<実物から1文字も変えずに写す>
~~~
直した後の文字:
~~~
<そのまま当てられる全文>
~~~
根拠の抜き書き: <ファイル名>:<行番号>「<その行の逐語>」
状態: <確定 / 未決 / 案が複数 のどれか>
```

**欄の決まり（6つ）**

1. **対象のファイル**：直すファイルを1つだけ書きます。プログラムが作る文書（設計書など）は、ここに書けません。その文書を直すときは、元データを直す件と、作り直すコマンドの件の2件に分けて書きます。作り直すコマンドの件は、元データを直す件のすぐ後ろに、同じ重さの見出しの中に書きます。
2. **直す箇所**：あなたが読んだ時点の行番号の範囲を書きます。走らせるコマンドの件では、「なし」と書きます。
3. **直す前の文字**：対象のファイルの中で1か所だけに当たる文字を、実物から写します。新しいファイルを作る件と、走らせるコマンドの件では、「なし」と書きます。
4. **直した後の文字**：見出しを、次の4つから1つ選びます。
   - **直した後の文字**：プログラムは、直す前の文字を、この全文に置き換えます。
   - **足す文字**：プログラムは、直す前の文字のすぐ後ろに、この文字を足します。新しいファイルを作るときは、ここに全文を書きます。
   - **消す文字**：プログラムは、直す前の文字の中から、この文字を消します。
   - **走らせるコマンド**：1行のコマンドをそのまま書きます。まこさんが打つ承認のコマンドも、ここに書きます。そのコマンドを走らせたときにかかった時間を、根拠の抜き書きに書きます（恒久61番）。
5. **根拠の抜き書き**：「ファイル名:行番号」と、その行の逐語を書きます。
6. **状態**：「確定」「未決」「案が複数」の3つのどれかを書きます。
   - **未決**：まこさんが決める件に書きます。
   - **案が複数**：4の欄を「案A」「案B」のように、案の数だけ並べます。

**プログラムが止めて、まこさんに報告するとき（2つだけ）**

1. 直す前の文字か、根拠の抜き書きが、実物と合わないとき、プログラムは止まります。
2. 状態が「未決」か「案が複数」のとき、プログラムは止まります。

止めた後にどうするかは、まこさんが決めます。

**書けないもの**

- 行番号と向きだけの指示（例：「78-114行を〜の形にする」）を書けません。
- 散文の「修正の方向性」「直し方（案）」「対策は〜にする」を書けません。
- 一度出した結果ファイルに、指示の取り下げを後から書き足せません。
- 1件に2つ以上のファイルを書けません。ファイルごとに件を分けます。
- 行ごとに「残す・直す・消す・足す」を並べた表を書けません。1行を1件にします。

**当てる順番**：プログラムは、修正を、番号の順に当てます。

### 修正をどこに書くか

実装が設計書と違う所の修正は、その実装のファイルに書いてください。修正を当てるプログラムが、その修正を当てます。
ただし、修正を当てるプログラムは、.claude/hooks と .claude/tools と .claude/breaks のファイルには当てません。そのファイルの修正は、CC が書きます。
設計書の誤りの修正は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-single-source-20261022/やることの表.md`）に書いてください。設計書はプログラムが作るので、設計書に直接書けません。

### 守ること

- CC は、自分で「合っている」「動く」と判定していません（恒久64番）。それを確かめるのが、この監査です。
- 乱数は、禁止です（恒久67番）。乱数を残す形や、乱数を足す形の設計か実装なら、その指摘を Critical にします。
- 監査は、1つの工事につき1回です（恒久65番）。どこまで直すかは、まこさんが結果を見て決めます。
- 目標（全月 net ≥ $1,900）を下げる方向の提案をしません。目標を達成できるかの判定がこの監査の対象外なら、そのことを結果に書きます。
- net を、M2-L の段まで判断の材料に使いません（まこさん決定 2026-09-01）。
- トレードについての外の知識を踏まえて判断します。外の知識は、暗号資産の先物の自動売買（Crypto futures algo trading）の業界の実情です。

---

## 起動の仕方（まこさん向け呼びかけ例文）

まこさんは、別の Claude Code セッションを開き、次の文を打ちます。

```
監査してほしい
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-23_m2c15_single_source_20261022_impl_cp87_audit_request.md
```

監査人の CC は、冒頭の宣言を読んで、Plan agent を起動します。監査人の CC は、結果ファイルを書くまで、自分で進めます。

依頼書終わり。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp87_work/cp87_src.gen.md src_sha256=40a4092e6663943ec00fc181bd5f9a2cd65b1034158e5ccb3265820791a4d3a8 body_sha256=22a6f046e8a2540d0ca949dbb39d3a86287d313d641ce4464639386f80f0e610 -->

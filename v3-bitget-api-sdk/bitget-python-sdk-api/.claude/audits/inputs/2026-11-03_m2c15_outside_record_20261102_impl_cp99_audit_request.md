# 【監査依頼】CP99 — レベル3 の法則のデータの形と、レベル4 の要素の定義表に足す分を決める。ToDo の208番・M2-C-15（実装の監査）

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
   - まず、結果の骨組みを作業場に作ります。コマンドは `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-11-03_m2c15_outside_record_20261102_impl_cp99_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp99_work/cp99_result.md` です。
   - 次に、骨組みの「<監査が書く>」を全部埋めます。見出しと並びを変えません。
   - 次に、埋めた結果を照らします。コマンドは `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-11-03_m2c15_outside_record_20261102_impl_cp99_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>` です。食い違いを0件にします。
   - 次に、結果を見直します。`python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` が作る表を全部埋めます。そのあと、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通します。
   - 最後に、結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-11-03_m2c15_outside_record_20261102_impl_cp99_audit_report.md` に、Write で1回だけ書きます。hook 11 が、書く瞬間に同じ照らしを掛けます。書いた後に、結果ファイルを書き替えられません。
5. 最後に、3つを報告します。1つ目は、結果ファイルのパスです。2つ目は、結論（GO・CONDITIONAL-GO・NO-GO のどれか）です。3つ目は、重さごとの件数（Critical・Major・Minor・Process）です。

### 禁止

- 依頼を出した CC に、確認の質問をしません。この依頼書だけで、監査ができるように書いてあります。
- Plan agent を起動せずに、自分だけで監査しません。
- 本物のファイルを書き替えません。写しを作業場に作ります。最後に、`git status --short` の出力で、本物を書き替えていないことを示します。
- ChatGPT などの外の AI を使いません。まこさんの課金の外になるためです。
- 「可能性がある」「かもしれない」「検討の余地」という言い方で答えません。数字と実物の行で言い切ります。言い切れないときは、「データ不足」と書き、その理由を書きます。

### 作業場

写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp99_work/` に作る。必要なファイルは自分で開き、写しで走らせて確かめる。

---

## 監査依頼メタ情報

- 依頼日: 2026-11-03
- 依頼者: CC（起案者）
- 監査の種類: 実装の監査
- 売買に触るか: はい
- 監査対象タスク: M2-C-15／設計書 m2c15-outside-record-20261102
- 監査の相手と版: `.claude/state/acceptance.md` ／ ハッシュ値 a234f8f54bd257ec7b7388e1951c387f7aa3135a508254c023f0e8340235f519
- 直す相手: `.claude/breaks/b228_laws_kubun_missing.sh`・`.claude/breaks/b229_laws_row_changed.sh`・`.claude/breaks/b230_records_changed_laws.sh`・`.claude/breaks/b231_style_missing.sh`・`.claude/breaks/b232_reader_style_check.sh`・`.claude/breaks/b233_t23_missing.sh`・`.claude/state/req_trace_src.json`・`.claude/tools/check_one_path.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py`
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-11-03_m2c15_outside_record_20261102_impl_cp99_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-11-03_m2c15_outside_record_20261102_impl_cp99_audit_request.md`

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

1. **この工事は何のためか**：この工事は、Entry と Exit の法則を1か所で持てるように、法則のデータ laws.json の形を決めます。あわせて、指標データの定義表に、足すと決まった要素を入れます。この形が誤っていると、その後の法則の行も、engine_tuner が組むロジックも、全部 誤ります。この監査では、設計書のとおりに実装できているかを確かめます。設計の中身は問いません
2. **この工事は何か**：この工事の中身は、設計書の「§1 概要」に書いてあります。実装の指示の一覧は、事実データの表に載せました。やることの番号は、M2-C-15です。
   **この工事の位置**：目標からこの工事までのつながりは、次のとおりです。全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝指標の構造の工事（ゴール1〜3）。指標の情報を1つのデータに集め、形を要件に合わせ（worklog 20261030 §17-1 の A〜C）、法則を1つのデータにまとめる（同 D）。全体のマイルストーンでは①の中で行う → この工事
3. **この工事が結ぶ要件**：M2-C-15＝この工事が満たす要件は、要件定義の次の3つです。3番：指標・閾値・パラメータ・時間足が、それぞれの役割に沿って使われ、閾値とパラメータが範囲から探されていること。4番と5番：最初の段階では、閾値とパラメータを、戦略ごとの代表の固定値にして探すこと。6番：指標は1か所から呼び出すこと。教科書と法則の誤りは、1か所を直せば全部に届くこと。（出どころ＝やることリスト m2_todo.json の「結ぶ要件」）
4. **経緯**：この監査に至るまでの経緯は、次のとおりです。
   - 設計書の監査 CP98 の結論は CONDITIONAL-GO で、Critical は9件でした。大きな誤りは3つです。1つ目は、3つの表の形が laws.json に無かったことです。2つ目は、S1 の枝6本の動く条件を、書いた形で持てなかったことです。3つ目は、場面と枝の名前の読み方が無かったことです。
   - まこさんは、CP98 の修正を全部（Critical・Major・Minor・Process）直すと決めました。修正20 は案B、修正22 は監査の案のとおりです。
   - CP98 の修正47件は、次の3つに分かれます。28件は、当てる道具で設計書の元データへ当てました。15件（修正15・17・18・20・23・30〜33・36・37・39・40・45・46）は、道具が案の写しに当てない作りなので、CC が次の案と実装の指示 impl_4-20_2_20261103.json に書き、まこさんの OK を受けました。4件（修正9・24・44・47）は設計書を作り直すコマンドで、CC が手で1回走らせました。
   - このため、当てた記録に無い修正が19件あります。next_move.py は、段6を「飛ばした」と出します。この19件が設計書に入っているかを、この監査で確かめてください。
   - CC は、監査の指示と次の2か所を変えました。修正22 の行は、欄が4つで表の3つに合わなかったので、頭の番号の欄を外しました。修正33 は、直す前の文字が離れた2か所に在るので、実装25 と実装26 の2件に分けました。
   - CC は、修正を入れた後に、同じ事実を書いた別の節を揃えました。4-3・4-5・4-8・4-12・4-13・6-2・7-3b と、新しく入る数字の 7 行目です。この文は、設計書の監査を受けていません。
   - 実装では、次の2つが設計書と違いました。1つ目に、4-12 に書いた run_breaks.py --design は土台ゲートに止められたので、--measure-only を付けて走らせました。2つ目に、当てる道具が自動で走らせる G2 と H2 は、走らせる前の照合に止められました。impl_functions が空なのに indicators.py と check_one_path.py を触ったためです。CC が G2 と H2 を手で走らせ、どちらも通りました。
   - 前の工事の壊すプログラム b211 と b213 は、この工事の後は落ちます。直すのは ToDo の209番です（設計書の 3-2 の2件目）。
   - 同じ回に、CC はインフラを直しました。require_trial_before_proposal.py と gen_acceptance.py の --drop です。この監査の相手ではありません。
   - CC は、当てた後に次を走らせました。読む口の自己テスト 39/39、--count、F-1〜F-7、壊すプログラム6本、対応表、G2、H2、監査に出す前のチェックです。この結果を、そのまま信じないでください。

---

## 監査の範囲

### 範囲の中

- 監査の相手は、`.claude/state/acceptance.md` です（設計書 `m2c15-outside-record-20261102`・実装の監査）。当てる道具が、設計書の実装の指示のとおりに実装を作れているかを確かめます。
- 直す相手は、`.claude/breaks/b228_laws_kubun_missing.sh`・`.claude/breaks/b229_laws_row_changed.sh`・`.claude/breaks/b230_records_changed_laws.sh`・`.claude/breaks/b231_style_missing.sh`・`.claude/breaks/b232_reader_style_check.sh`・`.claude/breaks/b233_t23_missing.sh`・`.claude/state/req_trace_src.json`・`.claude/tools/check_one_path.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` です。
- この工事は、売買のロジックに触る工事です。engine_tuner の目的は、まこさんの言葉で「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的」です（まこさん確定 2026-08-06）。

### 範囲の外（理由つき）

- 守りの穴探し（すり抜けの道を新しく探すこと）は、範囲の外です。穴探しは、探すたびに新しい穴が出て、終わらないためです（恒久の決まり65番）。CC は、作業が実際に止まったときに、その穴を直します。
- laws.json に法則の行を入れないは、範囲の外です。行を写すのは 209番と 195番。この工事は形だけを決める。
- 読むプログラム laws.py を作らないは、範囲の外です。209番で、行と一緒に作り、T44 で確かめる。
- regime_laws.json を動かさない。H2 の検査の対象も変えないは、範囲の外です。動かすのは 195番。法則を足した後の H2 の走らせ直しは必要なので残す。
- engine_tuner のコードを直さない（engine_tuner_gen.py・engine_tuner_exec.py・observe_diag.py）は、範囲の外です。法則を読む形に向けるのは 196番、型の表は 210番。
- search_limits.json の項目を動かさないは、範囲の外です。法則の中の数を写すのは 209番。指標の範囲は 211番。
- 時間足の一覧と上位足の写し方の値を observe_config.json から動かさないは、範囲の外です。この工事は要素の形だけを決める。値を動かすのは、読むプログラムを向ける 211番。
- 代表の値を埋めないは、範囲の外です。値を埋めるのは 222番。
- レベル1 とレベル2 のデータを作らないは、範囲の外です。取引所は 244番、運用ルールは 242番、台帳は 241番。
- 新しい法則の文を作らないは、範囲の外です。文は出どころから写す。無い物は法則にせず伺う。
- S1 のレシピ identity_s1_legacy.json を直さないは、範囲の外です。M6 まで、今の形で走らせる。入口の名前が2つ在る件は M6-1 で確かめる。
- 機械学習のモデルの要素を作らないは、範囲の外です。足せる形かだけを確かめる。
- 法則一覧.md を作らないは、範囲の外です。行が入る 209番で、プログラムで作る。
- S1 のレシピの record（売買記録の書き方）を法則の欄に入れないは、範囲の外です。net に関わらない診断列で、恒等の確かめ専用（engine_tuner_exec.py:1651〜1653）。

---

## 確かめてほしいこと（Q1〜QN）

★問いの番号（Q1・Q2 など）は、問いの見出しの頭に書いてあります。結果の所見で、この番号をそのまま見出しにします。問いの中の「特に見てほしい点」（Q8 など）にも、その番号で1点ずつ答えます。
★問いには、優先度 A・B・C・D のどれかが付いています。A の問いは、答えによって監査の結論（GO・CONDITIONAL-GO・NO-GO）が変わる問いです。B の問いは、直すべき所を探す問いです。C の問いは、書き漏れを探す問いです。D の問いは、結論には使わない問いです。
★所見は、優先度 A の問いから順に書きます。時間が足りずに答えなかった問いは、結果にその番号を書いてください。

### Q0 — 作った後の確認を走らせて通るか（優先度 A）

**この問いが要る理由**：通らないのに進めると、抜けが後の工程まで残る。

次のコマンドを走らせてください。`python3 .claude/tools/check_one_path.py --work m2c15-outside-record-20261102`
「通らない」か「未作」の試験が在れば、その番号と理由を全部挙げてください。「見た範囲」と出た試験は、文字や数やハッシュ値を見ただけです。動きを確かめたとは読まないでください。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**この問いが要る理由**：違えば、実装は設計書のとおりに作られていない。

設計書の 4-20 には、実装の指示が 26 件あります。
実装の前の対象のファイルに、この 26 件を番号の順に当ててください。実装の前の版は、事実データ「実装の前と後の版」の実装の前です。対象のファイルは、`.claude/breaks/b228_laws_kubun_missing.sh`・`.claude/breaks/b229_laws_row_changed.sh`・`.claude/breaks/b230_records_changed_laws.sh`・`.claude/breaks/b231_style_missing.sh`・`.claude/breaks/b232_reader_style_check.sh`・`.claude/breaks/b233_t23_missing.sh`・`.claude/state/req_trace_src.json`・`.claude/tools/check_one_path.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json`です。
当てた結果が、実装の後の版と1文字も同じかを確かめてください。実装の後の版は、事実データ「実装の前と後の版」の実装の後です。
確かめ方の例は、次のとおりです。まず、作業場に、git show で実装の前のファイルを出します。次に、直す前の文字を、直した後の文字に置き替えます。足す文字の指示なら、直す前の文字の後ろに、足す文字を足します。最後に、置き替えた結果と実装の後の版の差を、diff で取ります。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**この問いが要る理由**：在れば、設計書に無い変更が実装に混ざっている。

実装の前の版と実装の後の版の差分を取ってください。実装の前の版は、事実データ「実装の前と後の版」の実装の前です。実装の後の版は、事実データ「実装の前と後の版」の実装の後です。差分を取るファイルは、`.claude/breaks/b228_laws_kubun_missing.sh`・`.claude/breaks/b229_laws_row_changed.sh`・`.claude/breaks/b230_records_changed_laws.sh`・`.claude/breaks/b231_style_missing.sh`・`.claude/breaks/b232_reader_style_check.sh`・`.claude/breaks/b233_t23_missing.sh`・`.claude/state/req_trace_src.json`・`.claude/tools/check_one_path.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json`です。
差分のうち、実装の指示のどれにも当たらない行が在るかを確かめてください。在れば、全部を挙げてください。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**この問いが要る理由**：合わなければ、どの件を道具が当てたかを後から確かめられない。

当てる道具は、実装の指示を当てるたびに、`SDK/.claude/audits/applied_fixes.json` に記録を書きます。この工事の記録の名前は、`design:m2c15-outside-record-20261102` です。
この記録が、実装の指示の 26 件と、番号と対象のファイルで1件ずつ合うかを確かめてください。
記録に「当てた」とも「もう当て終わっていた」とも書かれていない件が在るかを確かめてください。
「もう当て終わっていた」の件について、その件がどの実行で当たったかを確かめてください。確かめる材料は、当てる道具の出力と、git の差分です。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**この問いが要る理由**：当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない。

まこさんが承認した版の設計書の控えは、`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-outside-record-20261102.md`です。
この控えの 4-20 の実装の指示と、いまの設計書の 4-20 の実装の指示が同じかを確かめてください。★2つが同じファイルを指すときは、控えのハッシュ値と、承認の印（`.claude/state/acceptance.approved`）の値と、控えのコミットの版が同じかを確かめてください。違うなら、その違いが実装に影響するかを答えてください。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**この問いが要る理由**：要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない。

やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-outside-record-20261102/やることの表.md`）の一覧には、この工事でやることが書いてあります。
実装の指示が、この一覧のやることを全部満たすかを確かめてください。
一覧に在るのに実装の指示に無い物と、実装の指示に在るのに一覧に無い物を、全部挙げてください。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 A）

**この問いが要る理由**：成り立たなければ、承認のときの「済」が根拠にならない。

設計書の完成の条件の表には、8 行の条件が書いてあります。
この条件が、実装の後に本当に成り立つかを確かめてください。
各行のコマンドを、作業場で走らせるか、読むだけの形で走らせてください。コマンドの中のパスは、`SDK` のフォルダからの相対です。そのため、どのコマンドも `SDK` のフォルダで走らせます。
走らせるコマンドは、次のとおりです。`jq -e '.["要素の定義表"]["選べる値"]["区分"]==["相場の法則","組み合わせの法則","売り方","建てる前の確認","決済の枝","玉全体の決済","玉の持ち方","役割ごとの決まり"] and .["法則の行"]==[] and .["条件の書き方"]==[] and .["玉の状態"]==[] and .["法則の中の数"]==[] and .["要素の定義表"]["表の形"]["条件の1本"]["欄"]!=null and .["要素の定義表"]["表の形"]["条件の書き方"]["欄"]!=null and .["要素の定義表"]["表の形"]["玉の状態"]["欄"]!=null and .["要素の定義表"]["表の形"]["法則の中の数"]["範囲の形"]!=null and (reduce .["要素の定義表"]["要素"][] as $r (0; .+1))==46 and (reduce .["要素の定義表"]["選べる値"]["値段の決め方の種類"][] as $r (0; .+1))==7 and (reduce .["要素の定義表"]["選べる値"]["売り方の決まりの種類"][] as $r (0; .+1))==8' scripts/priority_rebuild/laws/laws.json`・`T=$(mktemp) && git show 1f6f5ff9:v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json > "$T" && jq -e --slurpfile o "$T" --slurpfile n scripts/priority_rebuild/laws/laws.json '$o[0]["要素の定義表"]["要素"][37:47]==$n[0]["要素の定義表"]["要素"][0:10] and (reduce .["要素の定義表"]["要素"][] as $r (0; if $r["置く記録"]=="法則の記録" then .+1 else . end))==0 and .["要素の定義表"]["選べる値"]["法則の種類"]==null and .["要素の定義表"]["選べる値"]["判定の型"]==null and .["要素の定義表"]["選べる値"]["法則が指せる物"]==null and .["要素の定義表"]["法則の記録の置き場"]=="scripts/priority_rebuild/laws/laws.json" and $o[0]["要素の定義表"]["要素"][0:37]==.["要素の定義表"]["要素"][0:37] and $o[0]["要素の定義表"]["選べる値"]["法則の種類"]==$n[0]["要素の定義表"]["選べる値"]["法則の種類"] and $o[0]["要素の定義表"]["選べる値"]["判定の型"]==$n[0]["要素の定義表"]["選べる値"]["判定の型"] and $o[0]["要素の定義表"]["選べる値"]["法則が指せる物"]==$n[0]["要素の定義表"]["選べる値"]["法則が指せる物"]' scripts/priority_rebuild/indicators/indicators.json`・`T=$(mktemp) && git show 1f6f5ff9:v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json > "$T" && jq -e --slurpfile o "$T" '$o[0]["指標の記録"]==.["指標の記録"] and $o[0]["使い方の記録"]==.["使い方の記録"] and $o[0]["部品の記録"]==.["部品の記録"]' scripts/priority_rebuild/indicators/indicators.json`・`jq -e '.["要素の定義表"]["選べる値"]["売買スタイル"]==["スキャル","デイトレ"] and .["要素の定義表"]["選べる値"]["場面"]==["レンジ","上げ","下げ","スパイク"] and (reduce .["要素の定義表"]["要素"][] as $r (0; if $r["要素の名前"]=="確かめの強さ" or $r["要素の名前"]=="使える条件の形" or $r["要素の名前"]=="上位足の写し方" then .+1 else . end))==3' scripts/priority_rebuild/indicators/indicators.json`・`python3 scripts/priority_rebuild/indicators/indicators.py --selftest`・`! grep -q -e '【未決】208番' -e '【未決】195番' -e '形は 208番で決める' -e '置き場は 208番で決める' .claude/rules/要件定義書_レベル4_指標の構造.md`・`grep -c '"T23": t23, "T24": t24' /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/check_one_path.py`・`T=$(mktemp) && python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/check_one_path.py --todo 208 > "$T"; grep -q '通る 3 件' "$T"`

### Q8 — 当てた記録に無い修正19件は、設計書と実装に入っているか（優先度 A）

**この問いが要る理由**：この19件は道具の記録に残らないので、抜けていても機械では分かりません。抜けていると、監査の指摘が直らないまま次の工事へ進みます。

次の3つを確かめてください。
1つ目に、修正15・17・18・20・23・30〜33・36・37・39・40・45・46 の中身が、設計書の該当の節か実装の指示に入っているかを、修正ごとに1行で答えてください。修正20 は案B です。
2つ目に、修正9・24・44・47 のコマンドの結果が、いまの設計書と同じかを答えてください（gen_acceptance.py --work m2c15-outside-record-20261102 --dry-run と比べます）。
3つ目に、経緯に書いた CC の変更（修正22 の欄・修正33 の2件への分割）で、修正の中身が変わっていないかを答えてください。

### Q9 — 実物は、実装の指示26件のとおりか（優先度 A）

**この問いが要る理由**：実物が実装の指示と違うと、承認された形と違う物の上に、209番以降の工事を積むことになります。

次の3つを確かめてください。
1つ目に、実装の指示の「直した後の文字」が、実物に1文字も違わず在るかを、実装ごとに1行で答えてください。
2つ目に、実装の指示に無い変更が、直すファイル（TARGET と NEW_FILE）に無いかを答えてください。基準は commit c3c61eeb です。修正41〜43 と、ToDo の252番の行（req_trace_src.json）は、経緯に書いた変更です。
3つ目に、laws.json の法則の行と3つの表が空で、表の形と読み方の欄が在るかを答えてください。

### Q10 — 完成の条件と試験は、設計書のとおりに動くか（優先度 A）

**この問いが要る理由**：CC は自分で判定しません。CC の結果を監査が走らせ直さないと、確かめた人がいないことになります。

次の4つを確かめてください。
1つ目に、完成の条件の8行のコマンドを走らせ、結果を行ごとに答えてください。
2つ目に、壊すプログラム6本を run_breaks.py --design <設計書> --measure-only で走らせ、結果を答えてください。
3つ目に、T23 と T24 が、読む口の照らしを外すと「通らない」と出るかを、写しで答えてください。
4つ目に、indicators.py --count の結果が、指標の記録・部品の記録・使い方の記録・列を作る組について、commit c3c61eeb の時と同じかを答えてください。

### Q11 — 実装で設計書と違った点の扱いは、正しいか（優先度 B）

**この問いが要る理由**：設計書と違う手順で確かめた結果を、そのまま完成の根拠にできないためです。

次の3つを確かめてください。
1つ目に、当てる道具が G2 と H2 を走らせなかったことで、確かめに抜けが出ていないかを答えてください。g2_pass.json と h2_pass.json の対象のハッシュ値が、いまの実物と合うかを照らしてください。
2つ目に、設計書の 4-12 の run_breaks.py --design の文を、このまま残してよいかを答えてください。
3つ目に、設計書の 7-8 の「実装の後に照合をかける」の文と、照合の実際の結果（当てる道具の中の照合は止まり、監査に出す前のチェックの --diff は rc=0）の違いを、実物で説明してください。

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

件数: 2 件。結果の外部検索で、この件数の調べる物に1つずつ答えてください。

1. **区分ごとに欄が違う記録を1つの表で持つ作り**:
   - 検索の言葉: JSON schema discriminated union type specific fields metadata driven rule engine
   - 何と照らすか: 種類ごとの欄を定義表で持ち、読む口がそれを読む作りが、外の一般の作り方と合うか。新しく Web は開いていない。実装の監査では、この出どころと、実装の該当の所が合うかを照らします
2. **売買ルールをデータで持つ作り**:
   - 検索の言葉: declarative trading strategy rule definition exit branch data driven backtest framework
   - 何と照らすか: 入口と決済の枝をデータの行で持つ作りが、外の一般の作り方と合うか。新しく Web は開いていない。実装の監査では、この出どころと、実装の該当の所が合うかを照らします

---

## CC がまだ確かめていないこと

次の一覧は、依頼を出した CC が、まだ測っていないことと、まだ確かめていないことです。監査人は、この一覧を自分で測る必要はありません。番号ごとに、確かめないまま実装に進んでよいかを1件ずつ答えてください。進めてはいけない件には、その理由と、先に走らせるべきコマンドを書いてください。

1. **測っていない見積もり**：当てる・完成の条件。見込みは、数分の見込みです。根拠は、写しで当てた結果。時間は測っていないです。
2. **この工事の外の作業中の変更**：次のファイルには、作業中の変更があります。`.claude/hooks/require_trial_before_proposal.py`・`.claude/hooks/require_trial_before_proposal_selftest.py`・`.claude/tools/gen_acceptance.py`・`.claude/tools/gen_audit_docs.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`。この変更は、この工事の実装の指示が当てた物ではありません。そのため、Q1 と Q2 の差分を、この工事の対象のファイルだけで取ってください。

---

## 着手前必読（省略禁止・22 件）

**パスは、リポジトリの根（`cat-bitget/`）からの相対です。**`SDK` は、`v3-bitget-api-sdk/bitget-python-sdk-api` の略です。

1. `.claude/state/acceptance.md`（全文） — 監査の相手の設計書です。プログラムが作りました。このファイルは、承認された設計書です。実装の指示は26件、完成の条件は8行です。実物と照らす相手です。
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-outside-record-20261102.md` — まこさんが承認した版の設計書の控えです。どの版の 4-20 で当てたかは、Q4 で照らします。
3. `SDK/.claude/audits/applied_fixes.json`（全文） — 当てる道具が書いた、当てた記録です。この工事の行の名前は design:m2c15-outside-record-20261102 です。このファイルは、当てた記録です。経緯に書いた19件が記録に無いことを照らします。
4. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-outside-record-20261102/やることの表.md` — 設計書の元（やることの表）です。監査人は、修正の指示をこのファイルに書きます。
5. `SDK/.claude/rules/cat_requirements.md`（:269-290） — このファイルの §1.2.2 に情報の4段が在ります。実装の監査は設計の中身を問わないので、前提として読むだけです。
6. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-60） — このファイルに engine_tuner の目的が在ります。前提として読むだけです。
7. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:132-150） — このファイルに M2 以降の順番が在ります。前提として読むだけです。
8. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:81-109） — このファイルに M2 で作っている物が在ります。前提として読むだけです。
9. `SDK/.claude/audits/2026-11-03_m2c15_outside_record_20261102_design_cp98_audit_report.md`（:400-1172） — このファイルには、設計書の監査の修正47件が在ります。修正が設計書と実装に入ったかを照らします。
10. `SDK/scripts/priority_rebuild/laws/laws.json`（全文） — このファイルは、この工事で作りました。実装1 と同じかを照らします。
11. `SDK/scripts/priority_rebuild/indicators/indicators.json`（:1-12・:900-1120・:1730-1770） — このファイルの定義表を、この工事で直しました。実装2〜4・25・26 と照らします。
12. `SDK/scripts/priority_rebuild/indicators/indicators.py`（:40-65・:172-225・:440-470・:540-570） — このファイルは読む口です。実装5〜9 と照らします。
13. `.claude/tools/check_one_path.py`（:140-195・:255-260） — このファイルに T23 と T24 を足しました。実装10・11 と照らします。
14. `.claude/state/req_trace_src.json`（:20-28・:65-66・:200） — このファイルに T23 と T24 の見方を足しました。実装12・13 と、CP98 の修正41〜43 を照らします。
15. `SDK/.claude/rules/要件定義書_レベル4_指標の構造.md`（:160-166・:350-356・:373-374・:685-692・:720-726） — この文書の未決の行を直しました。実装14〜17・24 と照らします。
16. `.claude/breaks/b228_laws_kubun_missing.sh`（全文） — 壊すプログラムです。実装18 と照らします。
17. `.claude/breaks/b229_laws_row_changed.sh`（全文） — 壊すプログラムです。実装19 と照らします。
18. `.claude/breaks/b230_records_changed_laws.sh`（全文） — 壊すプログラムです。実装20 と照らします。
19. `.claude/breaks/b231_style_missing.sh`（全文） — 壊すプログラムです。実装21 と照らします。
20. `.claude/breaks/b232_reader_style_check.sh`（全文） — 壊すプログラムです。実装22 と照らします。
21. `.claude/breaks/b233_t23_missing.sh`（全文） — 壊すプログラムです。実装23 と照らします。
22. `SDK/.claude/ratchet/acceptance_archive/verbatim/m2c15-outside-record-20261102/laws_elements_src.json`（全文） — このファイルは、laws.json の区分ごとの要素の元データです。実装1 と同じかを照らします。

★この一覧には、直す相手のファイルが必ず入っています。結果の「修正の指示」の「直す前の文字」を、このファイルの実物から写します。

---

## 事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` | 新しいファイル（F-1）。要素の定義表の全文。法則の行は空 | 直した後の文字 |
| 2 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` | 要素の定義表の要素から ⑤-1〜⑤-10 を外し、足す要素3行と置き場の1行を入れる（F-2・F-3） | 直した後の文字 |
| 3 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` | 選べる値の場面を4つにする（F-3） | 直した後の文字 |
| 4 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` | 選べる値の時間足に欄を足し、売買スタイル・確かめの強さ・上位足の写し方を足し、法則用の3つを外す（F-2・F-3） | 直した後の文字 |
| 5 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | RECORD_KINDS の注記を直す（F-4） | 直した後の文字 |
| 6 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | _CHOICE_FIELD から判定の型を外す（F-4） | 直した後の文字 |
| 7 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | _check_all で売買スタイルを照らす関数を呼ぶ（F-4） | 直した後の文字 |
| 8 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 見本の選べる値に売買スタイルを足す（F-4） | 直した後の文字 |
| 9 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 自己テストを2件足す（F-4） | 直した後の文字 |
| 10 | `.claude/tools/check_one_path.py` | T23・T24 の測る処理を足す（F-6） | 直した後の文字 |
| 11 | `.claude/tools/check_one_path.py` | CHECKS に T23・T24 を足す（F-6） | 直した後の文字 |
| 12 | `.claude/state/req_trace_src.json` | T23 に見方を足す（F-7） | 直した後の文字 |
| 13 | `.claude/state/req_trace_src.json` | T24 に見方を足す（F-7） | 直した後の文字 |
| 14 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md` | 第3章の2 の要素の一覧と、法則と指標の外の行（F-5） | 直した後の文字 |
| 15 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md` | 表10 の法則の行と指標の外のデータの行（F-5） | 直した後の文字 |
| 16 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md` | 表13 の見出しに置き場を足す（F-5） | 直した後の文字 |
| 17 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md` | 表26 の5〜7（F-5） | 直した後の文字 |
| 18 | `.claude/breaks/b228_laws_kubun_missing.sh` | 壊すプログラム（7-6 の F-1・新しいファイル） | 直した後の文字 |
| 19 | `.claude/breaks/b229_laws_row_changed.sh` | 壊すプログラム（7-6 の F-2・新しいファイル） | 直した後の文字 |
| 20 | `.claude/breaks/b230_records_changed_laws.sh` | 壊すプログラム（7-6 の F-3 の1行目・新しいファイル） | 直した後の文字 |
| 21 | `.claude/breaks/b231_style_missing.sh` | 壊すプログラム（7-6 の F-3 の2行目・新しいファイル） | 直した後の文字 |
| 22 | `.claude/breaks/b232_reader_style_check.sh` | 壊すプログラム（7-6 の F-4・新しいファイル） | 直した後の文字 |
| 23 | `.claude/breaks/b233_t23_missing.sh` | 壊すプログラム（7-6 の F-6・新しいファイル） | 直した後の文字 |
| 24 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md` | ディレクトリマップの observe_config.json の行（F-5・監査 CP98 の修正31） | 直した後の文字 |
| 25 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` | 要素の定義表の説明の文から法則の記録を外す（F-2・監査 CP98 の修正33） | 直した後の文字 |
| 26 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` | この表で受けない要ることの 9・13・21・30 の受け先（F-3・監査 CP98 の修正33） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:m2c15-outside-record-20261102）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json` | 当てた | 2026-11-03T19:24:01 |
| 2 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` | 当てた | 2026-11-03T19:24:01 |
| 3 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` | 当てた | 2026-11-03T19:24:01 |
| 4 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` | 当てた | 2026-11-03T19:24:01 |
| 5 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 当てた | 2026-11-03T19:24:01 |
| 6 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 当てた | 2026-11-03T19:24:01 |
| 7 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 当てた | 2026-11-03T19:24:01 |
| 8 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 当てた | 2026-11-03T19:24:01 |
| 9 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py` | 当てた | 2026-11-03T19:24:01 |
| 10 | `.claude/tools/check_one_path.py` | 当てた | 2026-11-03T19:24:01 |
| 11 | `.claude/tools/check_one_path.py` | 当てた | 2026-11-03T19:24:01 |
| 12 | `.claude/state/req_trace_src.json` | 当てた | 2026-11-03T19:24:01 |
| 13 | `.claude/state/req_trace_src.json` | 当てた | 2026-11-03T19:24:01 |
| 14 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md` | 当てた | 2026-11-03T19:24:01 |
| 15 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md` | 当てた | 2026-11-03T19:24:01 |
| 16 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md` | 当てた | 2026-11-03T19:24:01 |
| 17 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md` | 当てた | 2026-11-03T19:24:01 |
| 18 | `.claude/breaks/b228_laws_kubun_missing.sh` | 当てた | 2026-11-03T19:24:01 |
| 19 | `.claude/breaks/b229_laws_row_changed.sh` | 当てた | 2026-11-03T19:24:01 |
| 20 | `.claude/breaks/b230_records_changed_laws.sh` | 当てた | 2026-11-03T19:24:01 |
| 21 | `.claude/breaks/b231_style_missing.sh` | 当てた | 2026-11-03T19:24:01 |
| 22 | `.claude/breaks/b232_reader_style_check.sh` | 当てた | 2026-11-03T19:24:01 |
| 23 | `.claude/breaks/b233_t23_missing.sh` | 当てた | 2026-11-03T19:24:01 |
| 24 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md` | 当てた | 2026-11-03T19:24:01 |
| 25 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` | 当てた | 2026-11-03T19:24:01 |
| 26 | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json` | 当てた | 2026-11-03T19:24:01 |

### 実装の前と後の版（git）

- **実装の前**：commit c3c61eeb（依頼書を作った時点の HEAD。承認の控えをまだ commit していないので、実装の前はこの commit の版。`git show c3c61eeb:<パス>` で出せる。★この後に commit しても、この番号で出せる）
- **実装の後**：依頼書を作った時点の作業中の変更（まだ commit していない。`git diff c3c61eeb -- <パス>` で見られる。★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、`git diff c3c61eeb <その commit> -- <パス>` で見る）。★この工事の中で、設計書の 4-4 の手順（G-1 の表の作り直しほか）の道具が、TARGET のファイルを書き出し直すことがある（例＝gen_materials.py --write が regime_detection_kb.md の件数の囲みを書き出す）。その行は実装の指示ではなく、設計書の 4-4・5 で照らす

### 必読に要るファイル（道具が設計書と実装から拾った）

| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15） | 入れる |
| `.claude/breaks/b228_laws_kubun_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b229_laws_row_changed.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b230_records_changed_laws.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b231_style_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b232_reader_style_check.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b233_t23_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/state/req_trace_src.json` | 直す相手（TARGET） | 入れる |
| `.claude/tools/check_one_path.py` | 直す相手（TARGET） | 入れる |
| `SDK/.claude/rules/要件定義書_レベル4_指標の構造.md` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/indicators/indicators.json` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/indicators/indicators.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/laws/laws.json` | 新しく作るファイル（NEW_FILE） | 入れる |

---

## 答えの出し方（結果ファイルフォーマット）

### 結果の11節（名前と並びは変えない・どの種類の監査でも同じ）

結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-11-03_m2c15_outside_record_20261102_impl_cp99_audit_report.md` に、次の 11 節を、この順で書きます。

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
- 結論は、要件を満たしたことを示しません。設計書の監査では、7 に「要件の状態」の表を書きます。行ごとに、状態（満たす・後の工事で受ける・当たらない・確かめられなかった）と、確かめ方（動かした・読んだだけ）を書きます。実装の監査は、設計書のとおりかを問うので、この表を書きません。

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
設計書の誤りの修正は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-outside-record-20261102/やることの表.md`）に書いてください。設計書はプログラムが作るので、設計書に直接書けません。

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
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-11-03_m2c15_outside_record_20261102_impl_cp99_audit_request.md
```

監査人の CC は、冒頭の宣言を読んで、Plan agent を起動します。監査人の CC は、結果ファイルを書くまで、自分で進めます。

依頼書終わり。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp99_work/cp99_src.gen.md src_sha256=32d6e0558c6aef0d7eadabc8f42fe655aef173badb0b7ee6ec91cf23dfb46b36 body_sha256=70f4c7e4dcac895c0f0909a57631397d1b0fd32678dfceab22e2d4893b6baa5d -->

# 【監査依頼】CP81 — 直し終えた hook の残り15本は、止めるべき物を止め、止めすぎず、すり抜けが無いか（残り30本の2回目・最後）

## ⚠️ 監査人への宣言（本依頼書を開いた CC への指示・最優先）

**あなたは、本セッションで監査人として呼ばれた CC です**（依頼を出した CC とは別のセッション）。SessionStart で読み込まれる CLAUDE.md などは参考のみ。読むのは、本依頼書と「着手前必読」と、問いが材料として指す実物（コード・設定・記録）だけ。

依頼を出した CC の判断に共感しないこと（同型バイアス）。あなたは、まこさんの味方でも CC の味方でもなく、基準（要件定義・教科書・業界の標準）の味方です。

### やること（読み終えたら、確認の質問なしで）

1. 本依頼書の全文を Read で読む。
2. `Agent`（`subagent_type=Plan`）を cold start で起動する。渡すのは、依頼書のパスと着手前必読の名前だけ。Plan agent が依頼書を読んで監査し、所見を返す。Plan agent はファイルを作れず、コマンドを走らせられない。写しを作る・自己テストや試しの道具を走らせるのは、監査人の CC（あなた）がやり、結果を Plan agent に渡す。
3. 結果を、次の順で書く（手で1から書かない。コマンドは全部、リポジトリの根 `cat-bitget/` で打つ）:
   - 骨組みを作業場に作る: `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-18_hook_fix_part3_nodesign_cp81_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp81_work/cp81_result.md`
   - 骨組みの「<監査が書く>」を全部 埋める（見出しと並びは変えない）。
   - 照らす: `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-18_hook_fix_part3_nodesign_cp81_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>` で、食い違い0件にする。
   - 見直す: `python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` の表を全部 埋め、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通す。
   - 結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-18_hook_fix_part3_nodesign_cp81_audit_report.md` に、Write で1回だけ書く（hook 11 が同じ照らしを掛ける。書いた後は書き替えられない）。
4. 戻り報告＝結果ファイルのパス／結論（GO・CONDITIONAL-GO・NO-GO）／重さごとの件数（Critical・Major・Minor・Process）。

### 禁止

- 依頼を出した CC への確認の質問（本依頼書だけで完結する）。
- Plan agent を起動せず、自分で監査すること。
- 本物のファイルを書き替えること。写しは作業場に作り、最後に `git status --short` で書き替えていないことを示す。
- ChatGPT など外の AI を使うこと（まこさんの課金外）。
- 「可能性がある」「かもしれない」「検討の余地」で答えること。数字と実物の行で言い切るか、「データ不足（理由）」と書く。

### 作業場

写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp81_work/` に作る。必要なファイルは自分で開き、写しで走らせて確かめる。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-18
- 依頼者: CC（起案者）
- 監査の種類: 手書きの依頼
- 売買に触るか: いいえ
- 監査対象タスク: hook の見直しの流れの4（直し終えた hook をまとめて監査に出す）。CP79（5本）・CP80（15本）の次の、最後の15本
- 監査の相手と版: `.claude/state/hook_inventory.md` ／ ハッシュ値 492041e25b289b5cecfa12ce9b2f1e0543b965d6262689e8439d602bcdb9bbae
- 直す相手: この回の15本の hook の本体（下の事実データの表の .sh と、判定の本体の .py）
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-18_hook_fix_part3_nodesign_cp81_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-18_hook_fix_part3_nodesign_cp81_audit_request.md`

---

## 要件定義と工事の流れ (固定・消さない・まこさん指示 2026-10-12)

**■ 要件定義と工事の流れ（固定・毎回 読む・消さない）**

★この文書は、まこさんが OK した要約（2026-10-18・逐語のファイル `okd_summary_20261018.txt`・OK の発言＝`ok_summary_20261018.txt`）を、プログラムが写した物です。見出しの行と、この説明の4行だけが、プログラムの中の決まった文です。
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

**■ 7. 作ってはいけないもの**
1. ランダムに条件をつなぐだけのもの。
2. 探す値を、CC が先に決まった数字の一覧で限定するもの。

**■ 8. 設計書と監査で確かめること**
- その設計のとおりに作ると、net 利益を最大にするロジックを見つける力が上がるか。少なくとも、損なわないか。
- 文字や手順が合っているかは、その手前の確かめ。

**■ 10. 設計書の監査が要る物**
- 売買のロジック・材料（指標）・法則・設定を直す工事＝要る。
- 「何を確かめるか」を決めるプログラムを直す工事＝要る。
- 読むため・整えるためのプログラム、数行の小さな直し＝要らない。

---

## この監査は何のためか（目的と経緯）

1. **この工事は何のためか**＝hook の不具合と、止めすぎと、要らない hook が、作業を遅らせていました。それを根本から直して、CC のミスを減らし、作業効率を上げるための工事です（hook_inventory.md の冒頭「hook を見直す目的」）。まこさんの要件（2026-10-15）＝「CATの目標達成のため、engine_tunerの機能要件を満たしつつ、効率的かつ正確にプロジェクト進行したいが、hookの不具合や、過剰なhook、不要なhookにより進行を妨げられている状態を完全に改善したい。」
2. **この工事は何か**＝2026-10-15〜10-18 に、hook を1本ずつ確かめました。まこさんが要・過剰・不要に振り分け、不要な物を止め、要る物の不具合を CC が直しました。直しが済で、いま動いている hook は35本です。5本は CP79 で、15本は CP80 で監査が済みました。この回の相手は、残りの15本（全部 止める hook）です。これで35本の全部が監査に出たことになります。
3. **この工事が結ぶ要件**＝要件定義の 1（CAT プロジェクトの目標）の「目標達成のため、ただ早く進めることが正解ではなく、正しく早く進めることが最善」と、10（「何を確かめるか」を決めるプログラムを直す工事）。hook は、承認や検査で何を通して何を止めるかを決めるプログラムです。2026-10-14 の まこさんの決定で、hook の直しには設計書を付けず、まとまりごとに監査に1回 出す形になりました。この回の15本のうち、enforce_h2_pass・enforce_g2_pass の相手の H2（未来のデータを使わない）は要件定義の 8（設計書と監査で確かめること）の「本番で再現する net」に、enforce_signal_table_gate は 3 の機能要件 6（つなぎ方が型の表に沿っている）に、require_period_source は検証の期間の正本に、それぞれ直接 結び付きます。
4. **経緯**＝2026-10-14 に、hook の直しには設計書を付けず、まとまりごとに直し終えたら監査に出す、と決まりました。2026-10-15〜10-17 に hook を1本ずつ直しました（直す前と後の行は `.claude/state/hook_fix_proposals/` に、まこさんの「よい」「OK」つきで残っています）。2026-10-18 に CP79 で5本を監査し（約55分・修正28件）、問いを13個から4個に絞って CP80 で15本を監査しました（開始から結果ファイルまで74分・修正42件＝Critical 4・Major 20・Minor 16・Process 2）。CP80 の修正は、まこさんの決定「修正は全部やる」で、42件を全部 当てました（当てるプログラムで40件・一覧の作り直し2件）。CP80 では、止める10本の全部に、一覧に書いていないすり抜けか止めすぎが在りました。まこさんの指示「次へ進める」（2026-10-18）で、残り15本を CP80 と同じ形（問い4つ・1回）で出します。
5. **なぜこの監査が要るか**＝直した物が本当に効いているかを、CC 以外が確かめるためです（恒久の決まり64番）。設計書の無い直しなので、依頼の中身は手書きです（まこさん決定 2026-10-18「b」）。

---

## 監査の範囲

### 範囲の中

- 監査の相手＝`.claude/state/hook_inventory.md`（直した hook の一覧。役割・いま動く場面・止める物・試した結果・不具合の直し・防げない物が書いてある。CP80 の修正29〜39・41 を当てて 2026-10-18 に作り直した版）のうち、この回の15本の行と「4. 1本ずつの詳しい中身」の15本の節、15本の本体（`.claude/hooks/`）とその部品、登録の実物（`.claude/settings.json`）。
- 直す相手＝この回の15本の hook の本体。一覧の文の誤りは、元データ `.claude/state/hook_inventory_src.json`。

### 範囲の外（理由つき）

- CP79 で監査した5本（verify_handoff_paths・require_work_declaration・block_repeat_kind・enforce_audit_request_gen・show_breaks_on_code_edit）と、CP80 で監査した15本（show_decisions・hook_health_check・reset_read_log・show_design_check_after_write・record_read・require_selftest_after_source_edit・block_repeat_failure・enforce_purpose_gate・enforce_audit_report_form・enforce_audit_fix_gen・require_source_read_before_acceptance・require_read_plan_before_design・forbid_edit_generated_docs・check_source_on_save・limit_repeat_verification）。ただし、この回の hook が同じ部品を使うときは、その部品の働きは見る。
- require_leak_annotation.sh（登録は在るが、2026-10-17 の確かめで不具合が見つからず、直していない＝「直し終えた hook」ではない）。
- 振り分け（要・過剰・不要）が正しいか（まこさんが1本ずつ決めた）。
- 止めた hook と、直しが済でない hook（動いていない物は、確かめる物が無い）。
- 決まりの文書（permanent_rules.md・pdca_flow.md・chat_writing_rules.md）の文が実物と合うか。恒久の決まり77番で、古い文書の文は監査の問いに使わないと決まった。
- scripts/priority_rebuild の .py（verify_design_contract.py・gen_signal_families.py・leak_causality_diag.py・periods.py ほか）の中身。この回の hook が呼ぶ相手だが、売買のフォルダの .py は設計書と承認が要る。誤りを見つけたら、修正ではなく一覧の元データ（防げない物）への追記に書く。
- 同じ状態に戻らない仕組み（hook の流れの5＝この監査の後の工事）。

---

## 確かめてほしいこと（Q1〜QN）

★優先度＝A（結論を変える）／B（直すべき）／C（書き漏れ）／D（結論に効かせない）。結果の所見は、この番号をそのまま見出しにし、優先度の順に書く。時間が足りずに省いた問いは、結果にその番号を書く。
★各 Q に、何を確かめるか・材料（どのファイルのどこ）・答えの形（表／件数／見つけた事の一覧）を書く。

### R0 — この工事は、要件定義の何番を満たすための物か。要件定義に反する所は無いか（優先度 A）

**優先度の理由**＝要件定義に反する直しや、要件のどれにも結び付かない直しが、そのまま進む

この工事が結ぶ要件は、「この監査は何のためか」の 3 に書いてあります。要件定義は、依頼書の上部に要約を載せています。全文は `.claude/rules/core_requirements_full.md` です。

- **R0-1**＝結ぶ要件が、工事の目的と中身に合っているか。もっと合う要件や、抜けている要件は無いか。
- **R0-2**＝hook の直しに、要件定義（上部の要約と、全文）に反する所は無いか。反する所は、ファイルと行で挙げてください。

### Q1 — 止めるべき物を止め、止めてはいけない物を止めないか（優先度 A）

**優先度の理由**＝止めないとミスが減らず、止めすぎると作業が遅れる

★**Q1〜Q3 に共通の答えの形**＝表を1つ作ってください。行は hook（15本）、列は確かめの番号（Q1-1・Q1-2・Q2-1・Q3-1 の4個）です。マスは、✅（確かめて問いのとおり）／❌（確かめて問いのとおりでない）／△（確かめきれなかった）のどれかだけ（この回は15本とも止める hook なので「—」は使いません）。❌ と △ のマスだけ、表の下に「hook の名前 ／ 確かめの番号」の見出しで、ファイル名と行・渡した入力と出た結果・理由を書き、❌ には対応する修正の番号（結果の 8 に書く）を添えてください。直し方の文は、ここには書きません。

★この回の問いは CP80 の4個と同じです。CP80 との対応＝Q1-1・Q1-2 は CP80 の Q2-1・Q2-2、Q2-1 は Q3-1、Q3-1 は Q4-1（CP80 の Q1〔表示だけの hook〕は、この回は相手が0本なので無い）。

相手は、15本の全部です。材料は、一覧の「4. 1本ずつの詳しい中身」の「止める物」の行と、判定の本体です。

- **Q1-1**＝止めるべき入力で止まるか。役割で防ぐ事を、実際に防いでいるか。
- **Q1-2**＝役割と関係の無い操作や、正しい操作で止まらないか。過去の止めすぎの例（「試した結果」の欄）も含む。

試し方は3つあります。①自己テスト（下の事実データの表「自己テストの口」の列。本体と別の名前のファイルが6本あります）②判定の本体の .py に PreToolUse の JSON を直接 渡す形（CP79・CP80 の監査人が使った `printf '<json>' | python3 .claude/hooks/<本体>.py`）③試しの道具（`python3 .claude/tools/try_hooks.py --session <やり取りの記録の名前> --bash "<コマンド>"`。Write なら `--write <パス>`・Edit なら `--edit <パス> --old <直す前の文字> --new <直した後の文字>`）。この回は、判定を .sh 自身が行う hook が6本あります（require_acceptance_before_impl・require_design_contract_before_run・require_period_source・enforce_observe_diag_only・enforce_flow_declaration・enforce_signal_table_gate）。CP80 で、`.claude/hooks` の .sh を `bash` で直接 走らせる形は土台ゲート（require_acceptance_before_impl）が止めました。この6本は、③の試しの道具（止める hook を全部 同じ入力で走らせ、止めた物を一度に出す）と、①の自己テストで試してください。ターンの終わり（Stop）の5本は、判定の本体の .py に、やり取りの記録のパスを含む JSON を渡す形で試せます（本体の先頭の説明に入力の形が書いてあります）。2本の hook が互いに通れない形でぶつかっていないかも見てください（例＝この回の土台ゲートと、CP80 の目的ゲートが、同じ engine_tuner の走行を別々の理由で止めないか）。

### Q2 — 判定をすり抜ける打ち方は無いか（優先度 A）

**優先度の理由**＝すり抜ける打ち方が残ると、その分だけミスが残る

相手は、15本の全部です。材料は、判定の本体と、一覧の「防げない物」（「4. 1本ずつの詳しい中身」の「まこさんの振り分け」の行の中に、「防げない物」「直さなかった物」「限界」として書いてある）です。

- **Q2-1**＝一覧に書いていない防げない物（判定をすり抜ける打ち方）は無いか。見つけた物は、渡した入力と、通った理由（本体の行）を書き、直せる物は修正に、直せない物は一覧の元データ（hook_inventory_src.json）への追記を修正に書いてください。一覧に「防げない物」として書いてある物でも、本体の数行で直せる物（例＝値を取る旗の後ろの .py・python3 -m の形）は、修正に書いてください。

★CP79・CP80 で見つかったすり抜けの型（この回の hook にも同じ型が在るかを見てください）＝①引用符の中を丸ごと消す作りで、引用符で囲んだパスが見えなくなる（enforce_audit_docs.py・enforce_purpose_gate.py の直す前）②旗の名前（--check・--selftest など）を、1語としてでなく文字の並びとして見る（--tag x--help・--log /tmp/x--verify.log・区切りの後ろのコメント # --selftest・& でつないだ別のコマンドの旗、で通った）③find -delete・sort -o・$( )・` `・sed -n -i・awk の system() を「読むだけ」と見る ④値を取る旗（-X utf8・-W ignore）の後ろの .py を見失う・python3 -m <モジュール> を見ない ⑤サブエージェントの操作を親の記録で判定する（入力の agent_type を見ない）⑥同じファイルを、sdk の .claude/state の近道のパスや、大文字と小文字だけ違うパス（macOS の APFS は区別しない）で書くと別の相手に見える ⑦PreToolUse の時点で、いま打つ操作の行が記録に入っているかの前提が hook ごとに逆で、どちらか片方で通る ⑧変数に入れたパス（D=…; cp a $D）を使う区切りに、相手の名前が無い ⑨名前（basename）が同じだけの別のファイルを「開いた」「走らせた」と数える ⑩ヒアドキュメントを、<< の在る行ごと消す。

### Q3 — 自己テストの結果が再現するか（優先度 A）

**優先度の理由**＝再現しない結果では、直ったと言えない

相手は、15本の全部です。材料は、一覧の「試した結果・見つかった不具合」の欄と、下の事実データの表「自己テストの口」の列です。

- **Q3-1**＝自己テストを走らせ、一覧に書いてある件数と同じ結果が出るか。自己テストが無い hook は、どれかを書いてください。自己テストが、Q1・Q2 の形（止めるべき入力と、正しい入力の両方）を入れているかも書いてください。

---

## 問いの外から当てる視点

### 一般の観点（①〜⑦・どの監査でも当てる）

問いに無くても、次の7つの視点で見る。観点ごとに「見つけた事と根拠」を、結果の所見に書く（見つからなければ「見つからなかった」と、見た相手を書く）。

- ①統計学的妥当性＝数字の根拠は足りているか。
- ②リスク管理＝損失や壊れたときの備えは在るか。
- ③認知バイアス＝CC の思い込みで組まれていないか。
- ④ソフトウェア工学＝作りとして正しいか（重複・壊れやすさ・テスト）。
- ⑤再現性＝同じ手順で同じ結果が出るか。
- ⑥実行プロセス＝決めた流れのとおりに進めたか。
- ⑦主エージェントバイアス＝CC が自分に都合よく判定していないか。

### 外の基準で確かめること（外部検索・WebSearch／WebFetch）

内部の文書だけで判断しない。次の物を、外の出どころ（教科書・公式の文書・業界の標準・論文）で確かめ、結果に URL と使った逐語を書く。

件数: 0 件（外で調べる物は無い。理由＝下の行。結果の5「外部検索」には「0件」と、この理由を写す）

この監査は、直した hook が役割どおりに働くかを、実物（本体・登録・試しの結果）で照らします。設計書の案から写す外の出どころがありません。hook の作りを外の標準（ソフトウェア工学）に照らす見方は、一般の観点④で当ててください。

---

## CC がまだ確かめていないこと

依頼を出した CC が、測っていない・確かめていない。結果は、この番号ごとに1件ずつ答える。

1. この回の15本の自己テストを、依頼書を作る前に CC は走らせ直していません。直したときの結果は「試した結果」の欄にあります。
2. この回の時間の見込み（約75分）は、CP80 の実測（開始から結果ファイルまで74分・15本・同じ問い4つ）からの見込みです。ただし、この回は判定を .sh 自身が行う hook が6本あり、require_acceptance_before_impl.sh は約1500行で、土台ゲートが bash での直接の走行を止めるため、CP80 より時間がかかる可能性があります。結果の 10 に、開始と終了の時刻を書いてください。
3. CP80 が見つけたすり抜けの型のうち、値を取る旗の後ろの .py・python3 -m の形・bash -c で包んだ形は、この回の enforce_flow_declaration・enforce_h2_pass・enforce_g2_pass・require_tag_for_experiment の「防げない物」に、CC が 2026-10-17 の直しのときに書いています。CP80 では、同じ型を enforce_purpose_gate で本体の直し（_run_target）で塞ぎました。この回の4本で、同じ直しを入れられるかは、CC は確かめていません（Q2-1 で見てください）。
4. この回の hook が使う部品（shell_cmd_scan.py・design_gate_fallback.py・lib_engine_entry_scan.py・transcript_rows.py・check_todo_file_paths.py・check_worklog_date.py・next_step_tidy_gate.py）は、CP80 の修正では変わっていません。CP80 の修正で変わった部品（require_check_after_failure.py・enforce_audit_docs.py・record_read.sh ほか）を、この回の15本は使っていません（2026-10-18 に CC が一覧の「本体の .py」の行で見ました。grep はしていません）。

---

## 着手前必読（省略禁止・40 件）

1. `.claude/state/hook_inventory.md` — 監査の相手（この回の15本の行と、「4. 1本ずつの詳しい中身」の15本の節＝359〜502行）
2. `.claude/settings.json` — hook の登録の実物
3. `.claude/hooks/require_acceptance_before_impl.sh` — 直す相手（本体。判定もこの .sh・約1500行・土台ゲートを含む6つの役目）
4. `.claude/state/hook_fix_proposals/dodai_gate_cases_20261016.tsv` — require_acceptance_before_impl の見本59件（1列目が期待＝1 止まる・0 通る）
5. `.claude/hooks/require_stage_conditions.sh` — 直す相手（本体）
6. `.claude/hooks/require_stage_conditions.py` — 直す相手（判定の本体・--selftest）
7. `.claude/hooks/require_design_contract_before_run.sh` — 直す相手（本体。判定もこの .sh）
8. `.claude/hooks/design_gate_fallback.py` — require_design_contract_before_run の部品
9. `.claude/hooks/require_design_contract_before_run_selftest.py` — 自己テスト
10. `.claude/hooks/require_period_source.sh` — 直す相手（本体。判定もこの .sh）
11. `.claude/hooks/require_period_source_selftest.py` — 自己テスト
12. `.claude/hooks/enforce_observe_diag_only.sh` — 直す相手（本体。判定もこの .sh）
13. `.claude/hooks/enforce_observe_diag_only_selftest.py` — 自己テスト
14. `.claude/hooks/enforce_flow_declaration.sh` — 直す相手（本体。判定もこの .sh）
15. `.claude/hooks/enforce_flow_declaration_selftest.py` — 自己テスト
16. `.claude/hooks/enforce_h2_pass.sh` — 直す相手（本体）
17. `.claude/hooks/enforce_h2_pass.py` — 直す相手（判定の本体・--selftest）
18. `.claude/hooks/enforce_g2_pass.sh` — 直す相手（本体）
19. `.claude/hooks/enforce_g2_pass.py` — 直す相手（判定の本体・--selftest）
20. `.claude/hooks/lib_engine_entry_scan.py` — enforce_h2_pass・enforce_g2_pass の部品（engine の入口の関数を使う .py の判定）
21. `.claude/hooks/require_tag_for_experiment.sh` — 直す相手（本体）
22. `.claude/hooks/shell_cmd_scan.py` — require_tag_for_experiment の判定の本体（--selftest）
23. `.claude/hooks/require_tag_for_experiment_selftest.py` — 自己テスト
24. `.claude/hooks/enforce_signal_table_gate.sh` — 直す相手（本体。判定もこの .sh）
25. `.claude/hooks/enforce_next_step_tidy.sh` — 直す相手（本体）
26. `.claude/hooks/next_step_tidy_gate.py` — enforce_next_step_tidy の判定の本体の1つ（--selftest）
27. `.claude/hooks/check_todo_file_paths.py` — 同（判定の本体の1つ）
28. `.claude/hooks/check_worklog_date.py` — 同（判定の本体の1つ・--selftest）
29. `.claude/hooks/require_run_after_edit.sh` — 直す相手（本体）
30. `.claude/hooks/require_run_after_edit.py` — 直す相手（判定の本体・--selftest）
31. `.claude/hooks/enforce_worklog_on_experiment.sh` — 直す相手（本体）
32. `.claude/hooks/enforce_worklog_on_experiment.py` — 直す相手（判定の本体）
33. `.claude/hooks/enforce_worklog_on_experiment_selftest.py` — 自己テスト
34. `.claude/hooks/require_design_check_before_approval.sh` — 直す相手（本体）
35. `.claude/hooks/require_design_check_before_approval.py` — 直す相手（判定の本体。CP80 の show_design_check_after_write と共有）
36. `.claude/hooks/require_design_check_before_approval_selftest.py` — 自己テスト
37. `.claude/hooks/require_trial_before_proposal.sh` — 直す相手（本体）
38. `.claude/hooks/require_trial_before_proposal.py` — 直す相手（判定の本体）
39. `.claude/hooks/require_trial_before_proposal_selftest.py` — 自己テスト
40. `.claude/hooks/transcript_rows.py` — やり取りの記録を読む共通の部品（Stop の hook が使う）

---

## 事実データ

### 項目が hook_inventory.md のどこに在るか

| 項目 | 在る所 |
|---|---|
| 役割 | 1節の表の「役割」の欄 |
| いま動く場面 | 1節の表の「いま動く場面」の欄 |
| 止める物 | 「4. 1本ずつの詳しい中身」の「止める物」の行 |
| 試した結果 | 1節の表の「試した結果・見つかった不具合」の欄 |
| 不具合の直し | 1節の表の「不具合の直し」の欄 |
| 防げない物 | 「4. 1本ずつの詳しい中身」の「まこさんの振り分け」の行の中（「防げない物」「直さなかった物」「限界」） |

### この回の15本と、登録の場面・判定の本体・自己テストの口

登録の場面は settings.json から（2026-10-18 に jq で読んだ）、判定の本体は hook_inventory.md の「本体の .py」の行から写しました。自己テストの口は、本体と自己テストのファイルを grep で見ました（2026-10-18）。15本とも止める hook です（Q1〜Q3 を全部に当てる）。

| hook | 登録の場面 | 判定の本体 | 自己テストの口 |
|---|---|---|---|
| require_acceptance_before_impl.sh | PreToolUse:Write\|Edit・PreToolUse:Bash・PreToolUse:MultiEdit（3行） | この .sh | .sh に --selftest の文字は在るが、一覧の試した結果は見本59件（dodai_gate_cases_20261016.tsv）を試しの道具で当てる形 |
| require_stage_conditions.sh | PreToolUse:Bash（引数 pre）と Stop（2行） | require_stage_conditions.py | require_stage_conditions.py --selftest |
| require_design_contract_before_run.sh | PreToolUse:Bash | この .sh（部品 design_gate_fallback.py） | require_design_contract_before_run_selftest.py |
| require_period_source.sh | PreToolUse:Bash | この .sh | require_period_source_selftest.py |
| enforce_observe_diag_only.sh | PreToolUse:Bash | この .sh | enforce_observe_diag_only_selftest.py |
| enforce_flow_declaration.sh | PreToolUse:Bash | この .sh | enforce_flow_declaration_selftest.py（古い番人 selftest_flow_declaration.sh は登録が無く、走らせない） |
| enforce_h2_pass.sh | PreToolUse:Bash | enforce_h2_pass.py（部品 lib_engine_entry_scan.py） | enforce_h2_pass.py --selftest |
| enforce_g2_pass.sh | PreToolUse:Bash | enforce_g2_pass.py（部品 lib_engine_entry_scan.py） | enforce_g2_pass.py --selftest |
| require_tag_for_experiment.sh | PreToolUse:Bash | shell_cmd_scan.py | require_tag_for_experiment_selftest.py と shell_cmd_scan.py --selftest |
| enforce_signal_table_gate.sh | PreToolUse:Write\|Edit | この .sh | 無し（一覧＝「まだ試していない」。当てる道具 apply_audit_fix.py の自己テスト T48 が同じ照らしを試す） |
| enforce_next_step_tidy.sh | Stop | check_todo_file_paths.py・check_worklog_date.py・next_step_tidy_gate.py | next_step_tidy_gate.py --selftest・check_worklog_date.py --selftest |
| require_run_after_edit.sh | Stop | require_run_after_edit.py | require_run_after_edit.py --selftest |
| enforce_worklog_on_experiment.sh | Stop | enforce_worklog_on_experiment.py | enforce_worklog_on_experiment_selftest.py |
| require_design_check_before_approval.sh | Stop | require_design_check_before_approval.py | require_design_check_before_approval_selftest.py |
| require_trial_before_proposal.sh | Stop | require_trial_before_proposal.py | require_trial_before_proposal_selftest.py |

### CP79・CP80 の結果で、この回に関わる物

- CP79（2026-10-18）の結論＝CONDITIONAL-GO。修正28件のうち18件を当てた。CP80（2026-10-18）の結論＝CONDITIONAL-GO。修正42件を全部 当てた（当てるプログラムで40件・一覧の作り直し2件）。
- CP80 の一般の観点で挙がった、この回にも当たる見方＝①引用符とヒアドキュメントを外す処理が hook ごとに別々に在り、1か所を直しても他に残る（この回では、require_acceptance_before_impl.sh・require_period_source.sh・enforce_observe_diag_only.sh・enforce_flow_declaration.sh・shell_cmd_scan.py がそれぞれ自前で外す）②自己テストに、見つかったすり抜けの型が入っていない ③PreToolUse の時点で、いま打つ操作の行が記録に入っているかの前提が hook ごとに逆（この回の Stop の hook は記録を読むので、記録の読み方〔transcript_rows.py を使うか自前か〕を見てください）。
- CP80 の修正で変わった部品で、この回の hook が使う物＝無し（自己申告に書いた）。

---

## 答えの出し方（結果ファイルフォーマット）

### 結果の11節（名前と並びは変えない・どの種類の監査でも同じ）

`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-18_hook_fix_part3_nodesign_cp81_audit_report.md` に、次の 11 節をこの順で出力する。

| # | 結果の節 | 依頼書の対応する項目 |
|---|---|---|
| 1 | **監査の相手と版**（依頼書のパス・監査の相手・ハッシュ値を照らした結果・実施日） | 監査依頼メタ情報 |
| 2 | **監査対象の型宣言**（数値型・コード型・文書型のうち該当するもの全部） | —（結果だけ） |
| 3 | **監査対象の事実データの確認**（依頼書の事実データを、自分で確かめた結果） | 事実データ |
| 4 | **所見**（依頼書の問いの番号をそのまま見出しにし、優先度の順に書く。一般の観点①〜⑦は、観点ごとに見つけた事と根拠。各所見の末尾に、対応する修正の番号を書く。直し方の文は書かない。省いた問いは番号を書く） | 確かめてほしいこと・問いの外から当てる視点 |
| 5 | **外部検索**（依頼書の件数の調べる物に1つずつ・URL と逐語） | 外の基準で確かめること |
| 6 | **依頼を出した CC の自己申告への答え**（依頼書の番号ごとに1件ずつ） | CC がまだ確かめていないこと |
| 7 | **総合判定**（結論＝GO／CONDITIONAL-GO／NO-GO と根拠・重さごとの件数） | 答えの出し方 |
| 8 | **修正の指示**（下の「修正の指示の書き方」の形だけで書く。重さは Critical・Major・Minor） | 着手前必読（直す相手のファイル） |
| 9 | **CC プロセス欠陥対策**（下の「修正の指示の書き方」の形だけで書く。重さは Process） | —（結果だけ） |
| 10 | **開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由** | 着手前必読 |
| 11 | **本物のファイルを書き替えていないこと**（`git status --short` の出力） | 監査人への宣言の禁止 |

### 重さと結論

- **Critical**＝結論を変える。**Major**＝直すべきだが、結論は変えない。**Minor**＝結論に効かせない。**Process**＝CC の進め方の欠陥（9 に書く）。
- **GO**＝Critical が0件。**CONDITIONAL-GO**＝Critical が在る（直せば先に進める）。**NO-GO**＝直し方の向きが違う（何が違うかを、4 の所見で、指摘の文と実物の行で示す）。
- どこまで直すかは、まこさんが結果を見て決める。だから修正は、重さの見出し（「### Critical」「### Major」「### Minor」「### Process」）の下に並べる。

### 修正の指示の書き方（★この形以外では書けない）

- **目的**：監査が書いた修正方法のとおりに、CC の改ざん・虚偽・矮小化・不正を通さずに直すため。
- **監査の種類**：設計書の内容確認、設計書どおりに実装できているかの確認など、どの種類の監査でも同じ欄で書く。
- **直す相手**：設計書・コード・実装データ（設定・json・法則ファイルなど）・文書・走らせるコマンドなど。どの相手の直しも同じ欄で書く。
- **直し方**：どの修正指示も、プログラムがそのまま実行できる形で書く。プログラムが欄のとおりに直しを当てる。CC は文も数も打たない。
- **直す範囲**：まこさんが結果ファイルを見て決める（Critical だけか、Major もか、Minor もか）。そのため修正は、重さの見出し（「### Critical」「### Major」「### Minor」「### Process」）の下に並べる。Process は 9 に書く。
- **所見との結び付き**：修正の番号は、4 の所見の末尾に書いた番号と同じにする。所見の無い修正は書かない。所見に書いた修正の番号は、必ず 8 か 9 に在るようにする。

1件は次の形で書く。

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

1. **対象のファイル**：直すファイルを1つだけ書く。プログラムが作る文書（設計書など）は書けない。その文書の元データの直し1件と、作り直すコマンド1件の2件に分けて書く。作り直すコマンドの件は、元データを直す件と同じ重さの見出しの中で、その件のすぐ後ろに書く。
2. **直す箇所**：監査が読んだ時点の行番号の範囲。走らせるコマンドのときは「なし」。
3. **直す前の文字**：対象のファイルの中で1か所だけに当たる文字を、実物から写す。新しいファイルを作るときと、走らせるコマンドのときは「なし」。
4. **直した後の文字**：見出しを次の4つから1つ選ぶ。
   - **直した後の文字**：直す前の文字を、この全文に置き換える。
   - **足す文字**：直す前の文字のすぐ後ろに足す。新しいファイルを作るときは、ここに全文を書く。
   - **消す文字**：直す前の文字の中から、この文字を消す。
   - **走らせるコマンド**：1行のコマンドをそのまま書く。承認のスクリプトなど、まこさんが打つコマンドもここに書く。監査が走らせたときにかかった時間を、根拠の抜き書きに書く（恒久61番）。
5. **根拠の抜き書き**：「ファイル名:行番号」と、その行の逐語。
6. **状態**：「確定」「未決」「案が複数」の3つだけ。
   - **未決**：まこさんが決めるもの。
   - **案が複数**：4の欄を「案A」「案B」のように、案の数だけ並べる。

**プログラムが止めて、まこさんに報告するとき（2つだけ）**

1. 直す前の文字か、根拠の抜き書きが、実物と合わないとき。
2. 状態が「未決」か「案が複数」のとき。

止めた後どうするかは、まこさんが決める。

**書けないもの**

- 行番号と向きだけの指示（例＝「78-114行を〜の形にする」）。
- 散文の「修正の方向性」「直し方（案）」「対策＝〜にする」。
- 取り下げ。一度出した結果ファイルに、あとから指示の取り下げを書き足さない。
- 1件に2つ以上のファイル。ファイルごとに件を分ける。
- 行ごとに残す・直す・消す・足すを並べた表。1行を1件にする。

**当てる順番**＝修正の番号の順。

### 修正をどこに書くか

- hook の働きの誤り＝その hook の本体（.sh と、呼ぶ .py・部品）。修正を当てるプログラムは、ふだんは .claude/hooks に当てない。CP79・CP80 では、まこさんの決定の逐語のファイルを渡したときだけ当てる道を、そのセッション限定で足して当て、終わった後に元に戻した。この回も同じ形で当てる見込み（まこさんが決める）。
- 一覧（hook_inventory.md）の文の誤り＝元データ `.claude/state/hook_inventory_src.json`（一覧はプログラムが作るので直接 直せない）。当てた後に `python3 .claude/state/_hook_inventory.py --write` を走らせる。
- settings.json の登録＝まこさんが直す物。直す行を書いてください。
- scripts/priority_rebuild の .py（売買のフォルダ）＝範囲の外。設計書と承認が要るので、修正でなく一覧の元データへの追記に書いてください。

### 守ること

- CC は自分で「合っている」「動く」と判定していない（恒久64番）。それを確かめるのが、この監査。
- 乱数は禁止（恒久67番）。乱数を残す・足す形なら Critical にする。
- 監査は1つの工事につき1回（恒久65番）。どこまで直すかは、まこさんが結果を見て決める。
- 目標（全月 net ≥ $1,900）を下げる方向の提案はしない。目標の達成可能性の判定が対象外なら、明示する。

---

## 起動の仕方（まこさん向け呼びかけ例文）

別の Claude Code セッションを開き、本依頼書のパスを示して依頼する:

```
監査してほしい
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-18_hook_fix_part3_nodesign_cp81_audit_request.md
```

→ 監査人の CC が、冒頭の宣言を読んで Plan agent を起動し、結果ファイルを書くまで自走する。

依頼書終わり。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp81_work/hook_fix_nodesign_src.md src_sha256=9cfdcd02b08bdf1d981e391550da9975468485def55fd7cee2b8c55b1e79227d body_sha256=8c10faadea0d8ed3649a269942568d962ec64af8249575b367795cf079c9f9ce -->

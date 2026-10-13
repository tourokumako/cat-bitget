# 【監査依頼】CP78 — 設計書を作るプログラムと項目の正本を直す。新しい形の設計書の元を読んで設計書に出す・法則の原文と指標の値を置き場から写す・項目の抜けを見張る検算を設計書を作るたびに走らせる（実装の監査）

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 32 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて、結果ファイルを次の順で書く（手で1から書かない）:
   - 結果の骨組みを道具で作業場に作る: `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-13_design_doc_gen_form_20261013_impl_cp78_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp78_work/cp78_result.md`
   - 骨組みの「<監査が書く>」などの印を全部 埋める（見出しと並びは変えない）
   - 食い違い0件を確かめる: `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-13_design_doc_gen_form_20261013_impl_cp78_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>`
   - 出す前に見直す: `python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` で見直し表を作り、全部の行（結果の見出しごと）に ①意味が通じるか ②実物と合うか（根拠＝ファイル名:行番号・実際に開いた行）③争点（この依頼書の結論を決める問い）に合うか と判定（OK／直した／該当なし（理由））を書き、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通す（結果を直したら表を作り直す・hook 11 が同じ照らしを掛ける）
   - 埋めた結果の全文を、結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-13_design_doc_gen_form_20261013_impl_cp78_audit_report.md` に Write で1回だけ書く（hook 11 が同じ照らしを掛ける。書いた後は書き替えられない）
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / CONDITIONAL-GO / NO-GO)
   - 重さごとの件数 (Critical / Major / Minor / Process)

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)
- 本物のファイルを書き替えること (写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp78_work/` に作る。最後に `git status --short` で書き替えていないことを示す)

### この監査の作業場

**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp78_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました。**判断が要る4つ（この工事は何のためか・必読・工事ごとの問い・要望のまとめ）は、CC が工事のフォルダの 監査依頼の手書き（実装の監査）.md に書き、まこさんが OK した文を写しました。ほかは道具が実物から作りました。問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・まこさんの要望が在る工事だけ）と、この工事で確かめてほしいことを問う工事ごとの問い（Q8〜Q14）です。

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-13
- 依頼者: CC（起案者）
- 監査区分: 実装の監査
- 監査対象タスク: （やることの番号なし）／設計書 design-doc-gen-form-20261013
- 監査の相手と版: `.claude/state/acceptance.md` ／ ハッシュ値 afd01bfe308913159295f7e86769b3e334ec6cd7f60d0d2996920ac741b95191
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-13_design_doc_gen_form_20261013_impl_cp78_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-13_design_doc_gen_form_20261013_impl_cp78_audit_request.md`
- 設計書のハッシュ値: afd01bfe308913159295f7e86769b3e334ec6cd7f60d0d2996920ac741b95191

---

## 要件定義と工事の流れ (固定・消さない・まこさん指示 2026-10-12)

**■ 要件定義と工事の流れ（固定・毎回 読む・消さない）**

★この文書は、まこさんが OK した文を、プログラムが逐語のファイルから写した物です。見出しの3行と、この説明の4行だけが、プログラムの中の決まった文です。
★出どころ＝`.claude/state/verbatim/requirements-core-20261012/` の okd_requirements_core_20261012.txt・okd_work_flow_20261012.txt・okd_design_audit_scope_20261012.txt（記録の発言との照らし＝`python3 .claude/tools/gen_verbatim.py --verify requirements-core-20261012/<名前>`）。
★作り直し＝`python3 .claude/tools/gen_core_requirements.py --write`。検出＝`--verify`。
★設計書・監査の依頼書・next_step の上部には、それぞれを作るプログラムが、この文書を写して載せます。この文書が無い・逐語のファイルと違うときは、どのプログラムも文書を作らずに止まります。

**■ 要件定義（CAT プロジェクトと engine_tuner の目的と要件）**

**■ 1. CAT プロジェクトの目標**

- 本番で BOT を走らせて、**全月 net ≥ $1,900** を達成する。
- 単月で判定する。通算でも平均でもない。全部の採用戦略を合わせた net で見る。
- 「目標達成のため、ただ早く進めることが正解ではなく、正しく早く進めることが最善」

**■ 2. engine_tuner の目的**

- 「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的」
- 「上記目的に即していないものは作らないこと。」
- 現状の位置付け＝「現状、CCの思考を補助する機能とする」

**■ 3. engine_tuner の機能要件**

```
指標、閾値、パラメータ、時間足の役割に基づき、法則に則って４つを組み合わせ、Entry/Exitやレジーム判定などの条件を作る
| 1 | **指標**が、承認済みのカタログに在るものから使われている 
| 2 | **閾値**が、範囲から探されている
| 3 | **パラメータ**が、範囲から探されている 
| 4 | **時間足**が、使える時間足から指定されている 
| 5 | **4つが、それぞれの役割に沿って使われている
| 6 | **つなぎ方が、型の表と場面の決まりに沿っている**
```

**■ 4. 探し方（段階を追って絞る）**

- 意図＝「膨大な組み合わせを一気に総当りで検索をしたいが、時間的に不可能なので、段階を追って以下組み合わせをふるいにかけて、最終的にnet利益最大化できるロジックを見つけ出すという構想。」
- 決定＝「ロジック検索の第一弾回では、パラメータや閾値は、スキャル、デイトレそれぞれの代表的な固定値で、最終的にパラメータと閾値は、それぞれに設定した範囲から検索をし、最適値を見つけられるようする」
- 最初の段階で絞るのは、指標・時間足・役割・つなぎ方の組。
- 最後の段階で、残った組のパラメータと閾値を、範囲から探す。
- ほかの探し方に替えない。

**■ 5. 言葉の定義**

**■ 代表の固定値**

**最初の段階で、探さずに固定して使う値です。パラメータと閾値のそれぞれに、戦略（スキャル／デイトレ）ごと・指標ごとに、1つ決めます。**

| 項目 | 中身 |
|---|---|
| 何のためか | 組み合わせの数を減らして、指標・時間足・役割・つなぎ方の組を絞るため |
| 例 | 「RSIをデイトレ戦略で検索する場合は、14」「スキャル戦略では９」 |
| 選び方 | ①教科書にその戦略向けの値が在れば、それを使う（1つのサイトだけの値でもよい）②無ければ、既定の値を使う ③2つ以上 在るときは、決まった規則で1つにする |
| 厳密さ | 「厳密でなくてもいい」「RSIのスキャル用パラメータは５でも９でも大差ないので、どちらでもいい」 |
| 値の持ち方 | 指標の名前に入れない。戦略ごとの設定として持つ |
| 最後の段階では | 固定を外し、範囲から探す |

**■ 範囲**

- 最後の段階で、パラメータと閾値を探す幅です。**指標ごとに1つ**です。
- 「範囲で探せるという上記要件は絶対」
- 「指標名に閾値やパラメータの値を固定で入れて、指標数を増やすという解決策はやめてほしい。」

**■ 戦略**

- スキャルか、デイトレか、です。どの戦略がどちらかは、採用の台帳（adopted_strategies.md）のとおりにします。

**■ 教科書**

- 指標のパラメータ・閾値・役割・計算の作りの、出どころにする資料です（開発者の原典・定番の教育サイトなど）。
- 置き場＝資料の表3つ（indicator_params_review.md・indicator_params_by_strategy.md・indicator_roles_thresholds.md）。

**■ 法則**

- 「法則に則って」の法則です。相場から見つけた知識を、文で書いた物です。
- 置き場＝知識の文書 regime_detection_kb.md の §11（共通・レンジ・上げ・下げ・スパイク・変わり始め）。
- 「法則があるからロジックって言われてるんだけど。」

**■ 指標一覧（material）**

- 指標を計算する、ただ1つの置き場です。Entry・Exit・場面の判定は、全部ここから指標を呼び出します。

**■ 6. 指標の使い方**

- **指標は、指標一覧（material）からだけ呼び出す。**売買のロジックの中に、指標の式を直書きしない。
- **指標のオン・オフが、全部のロジックに効く。**オフの指標は、どのロジックからも使えない。
- 指標は、Entry・Exit と、4つの場面（レンジ・上げ・下げ・スパイク）の判定の全部が使う材料です。材料が誤っていると、その上の絞り込みも net の比べも、全部 誤ります。
- 順番＝「指標を完璧に修正しきってから、M2へ戻す」

**■ 7. 教科書と法則の扱い（前提）**

- **教科書と法則は、完璧ではない、という前提で作る。**
- 「法則、教科書は現状で完璧だとは思っていないので、間違いが見つかったらスムーズに、修正できて、修正したものを適用できる状態にしてほしい。」
- つまり、次の2つができる作りにする。
  1. 誤りが見つかったら、置き場の1か所を直せば済む。
  2. 直した物が、それを使う全部のロジックに、そのまま届く。

**■ 8. 作ってはいけないもの**

1. ランダムに条件をつなぐだけのもの。
2. 探す値を、CC が先に決まった数字の一覧で限定するもの。

**■ 9. 設計書と監査で確かめること（★この節は私の言葉です）**

- **その設計のとおりに作ると、net 利益を最大にするロジックを見つける力が上がるか。少なくとも、損なわないか。**
- 文字や手順が合っているかは、その手前の確かめです。

**■ 10. いまの実物との違い（今後 直す物・今日 実物で確かめた分だけ）**

| 要件 | いまの実物 |
|---|---|
| 指標は指標一覧からだけ呼び出す（6） | E38 の11本と、売買を回すプログラムに、自前の計算が在る |
| 最初の段階は代表の固定値で探す（4） | engine_tuner は、代表の固定値を読むコードをまだ持っていない |
| 教科書の誤りを直せる（7） | 確かめたのは「値がページに書いてあるか」まで。中身の正しさは確かめていない。閾値を数字で調べたのは70種だけ |
| 法則の誤りを直せる（7） | 法則が正しいかを、私以外が確かめた記録を、今日は開いていない |
| 設計の中身を監査で確かめる（9） | 設計書の監査が、設計の中身を対象外にしている |

**■ 工事の流れ（やることリストの1件を進める順）**

**■ 流れ（まこさんが 2026-09-21 に決めた6段に、前後を足した形）**

| 順 | 段 | 何をするか | 誰が |
|---|---|---|---|
| 1 | 設計書の元を作る | 読むものを決めて読む。案を出す。まこさんの OK をもらう | 私 → まこさん |
| 2 | 設計書を作る | OK された案から、プログラムが設計書を作る | プログラム |
| 3 | 設計書の監査 | 設計の中身が正しいかを、私以外が確かめる | 監査 |
| 4 | 設計書の監査結果の確認 | 結果を読み、直す範囲を決める | まこさん |
| 5 | 設計書の修正 | 監査が書いた修正を、プログラムが設計書に入れる | プログラム |
| 6 | 承認 | 直した設計書を承認する | まこさん |
| 7 | 実装 | 承認した設計書から、プログラムが実装を書き込む | プログラム |
| 8 | 実装の監査 | 設計書のとおりに実装できているかを確かめる | 監査 |
| 9 | 実装の監査結果の確認 | 結果を読み、直す範囲を決める | まこさん |
| 10 | 実装の修正 | 監査が書いた修正を、プログラムが実装に入れる | プログラム |

出どころは、まこさんの 2026-09-21 の決定（6段）と、next_step の 125行の「工事の流れ」です。

**■ この流れの要点（私の理解）**

- **設計の誤りは、3〜5 で全部 出して直す。**だから、7 より後で設計をやり直すことが無い。
- **8 で見るのは「設計書のとおりか」だけ。**設計はもう正しいと確かめてあるから。
- 3 が設計の中身を見ないと、設計の誤りが 8 より後に出る。そうなると 1 まで戻る。終わらない。

**■ 設計書の監査が要る物・要らない物**

| 直す物 | 設計書の監査 |
|---|---|
| 売買のロジック・材料（指標）・法則・設定 | 要る（飛ばさない） |
| 「何を確かめるか」を決めるプログラム | 要る、と考えます（今日の件が根拠） |
| 読むため・整えるためのプログラム、数行の小さな直し | 要らない（まこさんの前の決定のとおり） |

まこさんの決定（逐語 2026-10-12）＝「では上記まとめの内容を決定とする」

---

## この監査で答えてほしいこと

### 結論を決める問い

- **問い1**＝設計書の実装の指示（64 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。あわせて、この工事で確かめてほしいこと（Q8〜Q14 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けている・工事ごとの問いで設計書と違う所が見つかれば NO。

- **問い2**＝この工事の後の実装が、下に並べた まこさんの要望（8 件）を満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。1つでも満たしていなければ NO（Q7 で照らす）。
  1. 目的：設計書を作るプログラムを直し、設計書の元の内容を、そのまま自動で設計書に書き写せるようにする
  2. 別セッションの監査の指摘 M-2・m-2・m-5・m-8 を、この工事に入れる
  3. 読むもの宣言のすり抜けを塞ぐ照らしを、この工事に入れる
  4. 外部検索の欄の直しは、次の工事（監査依頼書を作るプログラムの直し）でやる
  5. 古い形の設計書の元は残し、いままでどおりに読めるようにする
  6. 閾値を読む場所は、パラメータと同じ形に決めておく。置き場に欄が在れば写し、無ければ「未決」と出す
  7. 新しい項目の置き場所は、「新しく入る数字と式の一覧」を 4-9 のすぐ後、「検査やプログラムを直す工事で書く5つ」を 4-6 のすぐ後にする
  8. 4-19 の名前は、新しい形の設計書では、新しい名前に変える

(結論を決めるのは、これらの問いだけ。結果の「7. 総合判定」で、問いごとに YES / NO と根拠を書く)

### 結論の決め方

- **GO**＝問い1 と 問い2 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 と 問い2 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 と 問い2 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の番号と実物の行で示してください。

### この監査の前提

1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/design-doc-gen-form-20261013/やることの表.md`）に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。

---

## 監査依頼の経緯

1. **この工事は何のためか**＝設計の誤りを、実装の前に CC 以外（設計書の監査）が見つけられるようにする。前の工事で、設計書の元（工事を始めるときに CC が書いて、まこさんの OK をいただく物）に、目標・結ぶ要件・確かめていないことを書く場所を足した。ところが、設計書を作るプログラムが古い形しか読めないので、その中身が設計書に載らなかった。この実装で、設計書を作るプログラムと項目の正本を直し、設計書の元の内容を、そのままプログラムが設計書に書き写せるようにした。古い形の元は、いままでどおりに読めるまま残した。★この実装の監査では、いつもの「設計書のとおりに実装できているか」に加えて、設計書の監査 CP77 の指摘が、直した後の設計書と実装で解消しているかも確かめていただく（直した後の設計書は、設計書の監査を受け直していない）
2. **この工事は何か**＝設計書を作るプログラムが古い形のままなので、新しい ひな型で書いた設計書の元から、設計書を作れません。この工事は、それを作れるようにします。 ⏎ 前の工事で、設計書の元の形を改めました。設計書の元とは、工事を始めるときに CC が書いて、まこさんの OK をいただく物です。その工事が要件定義の何番のためのものか、何を目標にするか、CC が何を確かめていないかを、書く場所ができました。ところが、設計書を作るプログラムは、その新しい欄を知りません。知らない見出しに出会うと、そこで止まります。そのため、新しい ひな型は置いてあるだけで、まだ1回も使えていません。 ⏎ そこでこの工事では、設計書を作るプログラムと、設計書の項目の正本を、次の点で改めます。 ⏎ 1. 新しい形の やることの表と案を読んで、設計書に出せるようにする。 ⏎ 2. CC が自分で「要件に合っています」と判定を書く表をやめる。代わりに、どの要件をどの節に書いたかの索引を、プログラムが作る。 ⏎ 3. 法則の原文と、指標の役割・範囲・代表の値を、CC が手で写すのをやめる。プログラムが置き場から写す。 ⏎ 4. 項目の抜けを見張る検算を、設計書を作るたびに走らせる。この検算は、作った日の後、1回も走っていなかった。 ⏎ 5. 古い形の元で作った設計書は、いままでどおりに作り直せるままにする。 ⏎ 監査依頼書を作るプログラムは、今回は直しません。次の工事で直します。（やることの番号 無し）
   **この工事の位置**＝全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → この工事

---

## 着手前必読 (省略禁止・auditor 用・32 件)

**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `.claude/state/acceptance.md` — 監査の相手（設計書・プログラムが作った）
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/design-doc-gen-form-20261013.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
3. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:design-doc-gen-form-20261013 の行）
4. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/design-doc-gen-form-20261013/やることの表.md` — 設計書の元（やることの表）＝修正の指示を書く先
5. `.claude/rules/core_requirements.md`（全文） — 要件定義・工事の流れ。この工事が結ぶ要件は9番。カタログ・時間足・オンとオフの要件は3番と6番
6. `SDK/.claude/ratchet/acceptance_archive/design-doc-gen-form-20261013.md`（全文） — 承認済みの設計書の控え（実装の指示64件・完成の条件7行・4-0・4-5 異常系・4-12 出る結果の姿・4-13 影響範囲・5 決めたことと理由・6-2 リスク・7-4 塞げないもの）。設計書の監査 CP77 の修正を入れた版
7. `SDK/.claude/audits/2026-10-13_design_doc_gen_form_20261013_design_cp77_audit_report.md`（全文） — 設計書の監査 CP77 の結果（結論 NO-GO・Critical 2・Major 8・Minor 12・Process 4・修正の指示 14件）。Q10〜Q13 は、この結果の指摘を1件ずつ問う
8. `.claude/tools/gen_acceptance.py`（全文） — 実装 1〜41 を当てた後の、設計書を作るプログラム（新しい形の元を読む関数・設計書に出す関数・置き場から写す関数・自己テストの番人 T19〜T26）（Q8〜Q13）
9. `.claude/tools/gen_design_sections.py`（全文） — 実装 42・43 を当てた後の、項目の抜けを見張る検算（記録から指摘を拾う collect_c）（Q11）
10. `.claude/tools/gen_core_requirements.py`（全文） — 実装 44〜47 を当てた後の、要件定義の行の一覧を作る所（Q8）
11. `SDK/.claude/ratchet/design_section_map.json`（全文） — 実装 48〜62 を当てた後の、項目の正本（新しい項目2件・設計のもとの項目・割り当て）（Q8・Q11・Q12）
12. `.claude/breaks/b186_design_hand_unknown_heading_pass.sh` — 実装 63 で置いた壊すプログラム（知らない見出しの検査を、いつも通す形にする）（Q9）
13. `.claude/breaks/b187_design_sections_check_ignored.sh` — 実装 64 で置いた壊すプログラム（検算の結果を、見ない形にする）（Q9）
14. `.claude/breaks/b184_read_plan_requirement_link_off.sh` — 壊すプログラム2本の手本
15. `SDK/.claude/templates/design_origin_todo_template.md`（全文） — やることの表の共通の ひな型（プログラムが読む見出しと、表の列の名前の相手）（Q10・Q11）
16. `SDK/.claude/templates/design_origin_proposal_template.txt`（全文） — 案の共通の ひな型（4-6 の表の「法則・型の表・場面の決まり」の行と、4-7 の表の「指標・閾値・パラメータ・時間足」の行）（Q10・Q11）
17. `SDK/.claude/ratchet/m2_todo.json`（:812-830） — やることリストの元データの1件の形（読むもの宣言のすり抜けを塞ぐ照らしが、行の番号を読む相手）
18. `SDK/.claude/ratchet/indicator_switch.json`（:1-20） — 指標のオンとオフの一覧（鍵 on・off・counts。counts に「定義表の種類 291・使う 175・使わない 116」）（Q10）
19. `SDK/.claude/ratchet/signal_families.json`（:1-40） — 承認済みの型の表（鍵 families・parts・role_lineage・timeframes）。型の名前・部品・役割ごとの時間足を写す相手（Q10・Q11）
20. `SDK/.claude/ratchet/regime_laws.json`（:1-60） — 法則のファイル（法則の番号・一文・「機械が読む判定」）。法則の原文と、場面の決まりの原文を写す相手（Q11）
21. `SDK/scripts/priority_rebuild/observe_config.json`（:1-40） — 使える時間足の全部（鍵 timeframes の11個）を写す相手（Q11）
22. `SDK/scripts/priority_rebuild/engine_tuner_exec.py`（:684-700） — カタログに無い材料を止める検査 G6（指標の定義の表 indicator_reference_diag と照らす）。「カタログ」の読みの根拠（Q10）
23. `SDK/scripts/priority_rebuild/gen_signal_families.py`（:676-690） — 「1か所目は、カタログに在るか。2か所目は、表で承認された範囲か」と書いた行。「承認された範囲」の読みの根拠（Q10）
24. `SDK/scripts/priority_rebuild/gen_indicator_switch.py`（:1-30） — 「使える指標は、承認済みの型の表と、印がオンの重なりで決まる」と書いた行（Q10）
25. `SDK/scripts/priority_rebuild/engine_tuner_gen.py`（:378-390） — 使える時間足の全部を読む関数 _allowed_tfs（observe_config.json の timeframes）。「使える時間足」の読みの根拠（Q11）
26. `.claude/state/indicator_params_by_strategy.json`（:1-40） — パラメータの代表の値と範囲の置き場（指標の行に写す相手）（Q10）
27. `.claude/state/indicator_roles_thresholds.json`（:1-40） — 役割と閾値の置き場（指標の行に写す相手。「閾値の値」の欄は、まだ無い）（Q10）
28. `.claude/state/indicator_review/ddg_check.json` — 写しで確かめた結果（当てた後の自己テスト 26/26・検算 128件・壊し方2つ・いま在る工事のフォルダ45個の比べ・組めない31個が止まるときの文）（Q9・Q13）
29. `.claude/state/indicator_review/ddg_patches.py`（全文） — 実装の指示の元（直す前の文字・直した後の文字・なぜ）。監査 CP77 の修正の相手（Q10〜Q13）
30. `SDK/.claude/ratchet/acceptance_archive/design-origin-form-20261013.md`（:273-285） — 前の工事の承認済みの設計書の控え。設計書の 4-12 の5番の確かめの相手（2-1 の表の、走らせた時点の数の列）（Q9・Q14）
31. `.claude/hooks/require_acceptance_before_impl.sh`（:930-943） — 実装の前に承認を求める検査の相手（売買のロジックの .py と、壊すプログラムだけ）。設計書の 4-13 の6に書いた、項目の正本を直す道の根拠（Q12）
32. `.claude/state/session_worklog_20261013.md`（:383-479） — この工事の経緯（§23〜§28）＝監査 CP77 の結果・まこさんの決定・当てた修正・CC が書いた直し・案の出し直し・設計書の作り直し・承認・実装を当てた結果・CC の誤りで控えを書き替えた件

★直す相手になりうるファイルを必ず入れる (結果の「修正の指示」の「直す前の文字」を、監査が実物から写すため)。プログラムが作る文書 (設計書など) を監査するときは、その元データ (設計書なら、工事のフォルダ `.claude/state/verbatim/<工事名>/` の `やることの表.md`。承認の後は `SDK/.claude/ratchet/acceptance_archive/verbatim/<工事名>/`) も入れる。`acceptance_src.json` は 2026-09-30 から使っていない (ratchet に無い) ので、直す相手に書かない。

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = 設計書 `design-doc-gen-form-20261013` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。あわせて、まこさんの要望を、この工事の後の実装が満たしているか（問い2・Q7）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

この監査の相手は、売買のロジックに触らない道具の直しです（直す相手 TARGET に scripts/priority_rebuild も engine_tuner も無い）。

---

## 監査対象の事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/../../.claude/tools/gen_acceptance.py` | 233行（<モジュール直下>・新しい形の やることの表の、手書きの項目の名前を足す） | 直した後の文字 |
| 2 | `SDK/../../.claude/tools/gen_acceptance.py` | 204行（_tag・新しい形の設計書では、見出しの下の表示を「CC が書いて、まこさんが OK した案」にする） | 直した後の文字 |
| 3 | `SDK/../../.claude/tools/gen_acceptance.py` | 314〜317行（src_from_work・新しい形かどうかを見分け、手書きの項目の知らない見出しを止める） | 直した後の文字 |
| 4 | `SDK/../../.claude/tools/gen_acceptance.py` | 322行（src_from_work・新しい形の やることの表を読む） | 直した後の文字 |
| 5 | `SDK/../../.claude/tools/gen_acceptance.py` | 373〜374行（src_from_work・案の新しい見出し3つを読む） | 直した後の文字 |
| 6 | `SDK/../../.claude/tools/gen_acceptance.py` | 395〜396行（src_from_work・新しい形の案の【7-3b】は、根拠と確かめ直すコマンドの表を読む） | 直した後の文字 |
| 7 | `SDK/../../.claude/tools/gen_acceptance.py` | 413〜414行（src_from_work・新しい形の元を読んだ後の検査を呼ぶ） | 直した後の文字 |
| 8 | `SDK/../../.claude/tools/gen_acceptance.py` | 424行（src_from_work・新しい形の案には、【0-R】を求めない（索引はプログラムが作る）） | 直した後の文字 |
| 9 | `SDK/../../.claude/tools/gen_acceptance.py` | 433〜434行（src・新しい形の元を読む関数と、設計書に出す関数を足す） | 直した後の文字 |
| 10 | `SDK/../../.claude/tools/gen_acceptance.py` | 440〜441行（src・いま組んでいる設計書が新しい形かを、覚える） | 直した後の文字 |
| 11 | `SDK/../../.claude/tools/gen_acceptance.py` | 464行（build_materials・新しい形の設計書では、探す材料の一覧を、関わる指標の行だけにする） | 直した後の文字 |
| 12 | `SDK/../../.claude/tools/gen_acceptance.py` | 762行（build_checklist・新しい形の設計書では、7-5 の群2 を、直すファイルの全部で決める） | 直した後の文字 |
| 13 | `SDK/../../.claude/tools/gen_acceptance.py` | 953行（<モジュール直下>・対応の表に書いてよい節に、6-5 を足す） | 直した後の文字 |
| 14 | `SDK/../../.claude/tools/gen_acceptance.py` | 957行（<モジュール直下>・案の新しい見出しを、設計書の節の番号に読み替える） | 直した後の文字 |
| 15 | `SDK/../../.claude/tools/gen_acceptance.py` | 1269〜1270行（section4・新しい形だけの項目と、新しい形の名前を扱う） | 直した後の文字 |
| 16 | `SDK/../../.claude/tools/gen_acceptance.py` | 1292〜1293行（section4・種類①の工事では、4-6 と 4-7 を「必ず」にする） | 直した後の文字 |
| 17 | `SDK/../../.claude/tools/gen_acceptance.py` | 1299行（section4・非該当の項目の名前を、形に合わせる） | 直した後の文字 |
| 18 | `SDK/../../.claude/tools/gen_acceptance.py` | 1331行（section4・項目の見出しの名前を、形に合わせる） | 直した後の文字 |
| 19 | `SDK/../../.claude/tools/gen_acceptance.py` | 1357〜1360行（section4・新しい形の設計書では、項目の下に、プログラムが置き場から写す行を出す（概要の1文目だけは、4-0 の冒頭に出す）） | 直した後の文字 |
| 20 | `SDK/../../.claude/tools/gen_acceptance.py` | 1402〜1404行（page・新しい形の設計書の先頭に、工事の種類と、概要の1文目を出す） | 直した後の文字 |
| 21 | `SDK/../../.claude/tools/gen_acceptance.py` | 1425行（page・手書きの項目の数と名前を、形に合わせる） | 直した後の文字 |
| 22 | `SDK/../../.claude/tools/gen_acceptance.py` | 1435〜1436行（page・新しい形の設計書には、要件定義の文を必ず載せる） | 直した後の文字 |
| 23 | `SDK/../../.claude/tools/gen_acceptance.py` | 1441〜1442行（page・新しい形の設計書では、要件定義との照らしの表の代わりに、索引を出す） | 直した後の文字 |
| 24 | `SDK/../../.claude/tools/gen_acceptance.py` | 1483行（page・新しい形の設計書の2番の節に、やることリストのどの行の工事かと、やることの一覧を出す） | 直した後の文字 |
| 25 | `SDK/../../.claude/tools/gen_acceptance.py` | 1599〜1601行（page・新しい形の設計書の3番の節に、目標を出す。やらないことは、表の1か所から写す） | 直した後の文字 |
| 26 | `SDK/../../.claude/tools/gen_acceptance.py` | 1659〜1662行（page・新しい形の設計書では、受けた設計書の監査の結果ファイルを出す） | 直した後の文字 |
| 27 | `SDK/../../.claude/tools/gen_acceptance.py` | 1672行（page・新しい形の設計書の6番の節に、確かめていないことを出す） | 直した後の文字 |
| 28 | `SDK/../../.claude/tools/gen_acceptance.py` | 1677行（page・新しい形の設計書の 7-1 に、概要の1文目を写す） | 直した後の文字 |
| 29 | `SDK/../../.claude/tools/gen_acceptance.py` | 1698〜1701行（page・新しい形の設計書の 7-3b は、根拠と確かめ直すコマンドの表にする） | 直した後の文字 |
| 30 | `SDK/../../.claude/tools/gen_acceptance.py` | 1786行（write・設計書を作るたびに、項目の抜けを見張る検算を走らせる） | 直した後の文字 |
| 31 | `SDK/../../.claude/tools/gen_acceptance.py` | 1790〜1791行（write・手書きの印の数の検査を、形に合わせる） | 直した後の文字 |
| 32 | `SDK/../../.claude/tools/gen_acceptance.py` | 1805〜1806行（write・読むもの宣言の写しを、工事のフォルダに置く） | 直した後の文字 |
| 33 | `SDK/../../.claude/tools/gen_acceptance.py` | 1962行（_sample_work・自己テストの見本を、新しい形でも作れるようにする（引数）） | 直した後の文字 |
| 34 | `SDK/../../.claude/tools/gen_acceptance.py` | 1974〜1975行（_sample_work・新しい形の見本の、工事の名前） | 直した後の文字 |
| 35 | `SDK/../../.claude/tools/gen_acceptance.py` | 2012行（_sample_work・新しい形の案の見本） | 直した後の文字 |
| 36 | `SDK/../../.claude/tools/gen_acceptance.py` | 2034行（_sample_work・新しい形の やることの表と、読むもの宣言の写しの見本） | 直した後の文字 |
| 37 | `SDK/../../.claude/tools/gen_acceptance.py` | 2350行（selftest・自己テストに、新しい形の元の番人を7つ足す） | 直した後の文字 |
| 38 | `SDK/../../.claude/tools/gen_acceptance.py` | 92行（touches_trading・新しい形の設計書では、「売買に触るか」を、先頭に出す工事の種類と同じ決め方で決める（2-2〜2-4・7-1・7-5 の出し分けがそろう）） | 直した後の文字 |
| 39 | `SDK/../../.claude/tools/gen_acceptance.py` | 320行（src_from_work・「3-2 決めてほしいこと」に、ひな型の★の行を残して「無し」と書いても、止まらないようにする） | 直した後の文字 |
| 40 | `SDK/../../.claude/tools/gen_acceptance.py` | 1343行（section4・新しい形の設計書の 4-21 と 4-22 の、見出しの下の表示を、案の見出しの名前にする） | 直した後の文字 |
| 41 | `SDK/../../.claude/tools/gen_acceptance.py` | 1274行（section4・新しい形の設計書では、古い数「118件」を書かない（いままでの形の設計書は、作り直しても文字が変わらないように、そのまま）） | 直した後の文字 |
| 42 | `SDK/../../.claude/tools/gen_design_sections.py` | 170〜172行（collect_c・記録から指摘を拾うときに、まこさんの語のすぐ後ろに続く かぎ括弧の中の、設計と抜けの両方を言う文だけを拾う（割り当てを作った日より後）） | 直した後の文字 |
| 43 | `SDK/../../.claude/tools/gen_design_sections.py` | 66行（<モジュール直下>・拾い方を分ける日を足す） | 直した後の文字 |
| 44 | `SDK/../../.claude/tools/gen_core_requirements.py` | 149行（<モジュール直下>・要件定義の行の一覧に、5・9・10 を足す（新しい形の設計書の索引だけ）） | 直した後の文字 |
| 45 | `SDK/../../.claude/tools/gen_core_requirements.py` | 152行（requirement_items・行の一覧を、新しい形の索引のために全部 出す引数を足す） | 直した後の文字 |
| 46 | `SDK/../../.claude/tools/gen_core_requirements.py` | 171行（requirement_items・引数で、行の一覧を切り替える） | 直した後の文字 |
| 47 | `SDK/../../.claude/tools/gen_core_requirements.py` | 182行（requirement_items・件数の検査も、引数で切り替える） | 直した後の文字 |
| 48 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 8行（項目の正本・並び順に、新しい項目2件を足す（4-22 は 4-6 のすぐ後・4-21 は 4-9 のすぐ後。まこさん「１，OK」2026-10-13）） | 直した後の文字 |
| 49 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 26行（項目の正本・4-3 に、足す中身を書き足す） | 直した後の文字 |
| 50 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 30行（項目の正本・4-4 に、足す中身を書き足す） | 直した後の文字 |
| 51 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 37行（項目の正本・4-6 を、種類①の工事（指標・探索・売買のロジック・設定に触る工事）では必ず書く項目にする） | 直した後の文字 |
| 52 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 39行（項目の正本・4-6 に、足す中身を書き足す） | 直した後の文字 |
| 53 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 42行（項目の正本・4-7 を、種類①の工事では必ず書く項目にする） | 直した後の文字 |
| 54 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 44行（項目の正本・4-7 に、足す中身を書き足す） | 直した後の文字 |
| 55 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 49行（項目の正本・4-8 に、足す中身を書き足す） | 直した後の文字 |
| 56 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 54行（項目の正本・4-9 に、足す中身を書き足す） | 直した後の文字 |
| 57 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 59行（項目の正本・4-10 に、足す中身を書き足す） | 直した後の文字 |
| 58 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 72行（項目の正本・4-13 に、足す中身を書き足す） | 直した後の文字 |
| 59 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 98行（項目の正本・4-19 の、新しい形の設計書での名前を足す（まこさん「２，名前は変更する」2026-10-13）） | 直した後の文字 |
| 60 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 103〜105行（項目の正本・新しい項目2件（4-21・4-22）を足す） | 直した後の文字 |
| 61 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 125行（項目の正本・検算で入っていなかった、うちの正本の7件（受け入れのチェックリストの項目6件と、設計書を相手にする hook の数）を、付録の項目に入れる） | 直した後の文字 |
| 62 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 126行（項目の正本・検算で入っていなかった、過去の指摘の2件（まこさんの文をそのまま設計書に組み込む・元と設計書の食い違いをプログラムで照らす）を、設計のもとの項目（新しく足す）に入れる。★設計書の監査 CP77 の修正＝検査の出力の2件は、拾い方を直して拾わなくなったので、割り当てから外した（番号は C-39・C-40 の2件になる）） | 直した後の文字 |
| 63 | `.claude/breaks/b186_design_hand_unknown_heading_pass.sh` | なし（新しいファイル） | 直した後の文字 |
| 64 | `.claude/breaks/b187_design_sections_check_ignored.sh` | なし（新しいファイル） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:design-doc-gen-form-20261013）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 2 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 3 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 4 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 5 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 6 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 7 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 8 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 9 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 10 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 11 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 12 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 13 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 14 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 15 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 16 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 17 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 18 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 19 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 20 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 21 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 22 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 23 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 24 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 25 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 26 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 27 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 28 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 29 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 30 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 31 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 32 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 33 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 34 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 35 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 36 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 37 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 38 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 39 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 40 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 41 | `SDK/../../.claude/tools/gen_acceptance.py` | 当てた | 2026-10-13T21:31:32 |
| 42 | `SDK/../../.claude/tools/gen_design_sections.py` | 当てた | 2026-10-13T21:31:32 |
| 43 | `SDK/../../.claude/tools/gen_design_sections.py` | 当てた | 2026-10-13T21:31:32 |
| 44 | `SDK/../../.claude/tools/gen_core_requirements.py` | 当てた | 2026-10-13T21:31:32 |
| 45 | `SDK/../../.claude/tools/gen_core_requirements.py` | 当てた | 2026-10-13T21:31:32 |
| 46 | `SDK/../../.claude/tools/gen_core_requirements.py` | 当てた | 2026-10-13T21:31:32 |
| 47 | `SDK/../../.claude/tools/gen_core_requirements.py` | 当てた | 2026-10-13T21:31:32 |
| 48 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 49 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 50 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 51 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 52 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 53 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 54 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 55 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 56 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 57 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 58 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 59 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 60 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 61 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 62 | `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 当てた | 2026-10-13T21:31:32 |
| 63 | `.claude/breaks/b186_design_hand_unknown_heading_pass.sh` | 当てた | 2026-10-13T21:31:32 |
| 64 | `.claude/breaks/b187_design_sections_check_ignored.sh` | 当てた | 2026-10-13T21:31:32 |

### 必読に要るファイル（道具が設計書と実装から拾った）

| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/../../.claude/tools/gen_acceptance.py` | 直す相手（TARGET） | 入れる |
| `SDK/../../.claude/tools/gen_core_requirements.py` | 直す相手（TARGET） | 入れる |
| `SDK/../../.claude/tools/gen_design_sections.py` | 直す相手（TARGET） | 入れる |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b186_design_hand_unknown_heading_pass.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b187_design_sections_check_ignored.sh` | 直す相手（TARGET） | 入れる |
| `.claude/state/indicator_params_by_strategy.json` | `SDK/../../.claude/tools/gen_acceptance.py` が名前を出す（実装の前後の差分） | 入れる |
| `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | `SDK/../../.claude/tools/gen_acceptance.py` が名前を出す（実装の前後の差分） | 入れない（指標の定義の表。この工事では直していない。設計書を作るプログラムは、部品の名前から種類を引く関数 find を呼ぶだけ（名前を出すのは、関数 _table_kinds の中）） |
| `.claude/state/indicator_roles_thresholds.json` | `SDK/../../.claude/tools/gen_acceptance.py` が名前を出す（実装の前後の差分） | 入れる |
| `SDK/.claude/ratchet/materials.json` | `SDK/../../.claude/tools/gen_acceptance.py` が名前を出す（実装の前後の差分） | 入れない（この工事では、読んでも書いてもいない。工事の種類を決める語の一覧に、ファイルの名前を足しただけ（監査の修正 8）） |
| `SDK/scripts/priority_rebuild/observe_config.json` | `SDK/../../.claude/tools/gen_acceptance.py` が名前を出す（実装の前後の差分） | 入れる |
| `SDK/.claude/ratchet/signal_families.json` | `SDK/../../.claude/tools/gen_acceptance.py` が名前を出す（実装の前後の差分） | 入れる |

---

## 監査スコープ

### 監査対象 (本監査内)

- Q1：実装の指示を当てた結果が、実装の後と1文字も同じか
- Q2：実装の指示のどれにも当たらない行（設計書に無い変更）が無いか
- Q3：当てた記録が、実装の指示の全部と1件ずつ合うか
- Q4：承認した版の設計書どうしで、実装の指示が同じか
- Q5：実装の指示が、やることの表の要件を全部 満たすか
- Q6：完成の条件が、実装の後に本当に成り立つか
- Q7：まこさんの要望を、この工事の後の実装が満たしているか（問い2）
- Q8：実装の指示64件は、承認した設計書のとおりに、漏れなく・余計なく当たっているか
- Q9：当てた後の設計書を作るプログラムは、設計書の 4-5 と 4-12 のとおりに動くか。古い形の元から作る設計書は、当てた後も変わらないか
- Q10：設計書の監査 CP77 の Critical の2件は、直した後の設計書と実装で、解消しているか
- Q11：設計書の監査 CP77 の Major の8件は、直した後の設計書と実装で、解消しているか
- Q12：設計書の監査 CP77 の Minor の12件は、どう扱ったか。扱いは妥当か
- Q13：設計書の監査 CP77 の Process の4件は、どう扱ったか
- Q14：承認した設計書と実物の間に、CC が知っている食い違いと、決まった流れから外れた所が、合わせて7つ在る。ほかに無いか

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- 監査依頼書を作るプログラム（gen_audit_docs.py）の直し（次の工事で直す。確かめる問い・自己申告への写し・外部検索の欄は、そちらに入る）
- 新しい ひな型2本の中身の直し（監査を受けて置いた物。読む側を、ひな型に合わせる）
- 個別の工事（K-4 ほか）のファイルの直し（個別の工事を直す相手にしない）
- 売買の戦略の設計書（別の形の設計書）
- 閾値の代表の値を決めることと、置き場に書くこと（閾値の修正の工事でやる。この工事は、読む場所の形を決めるだけ）
- 指標の役割の置き場の中身の直し（役割の修正の工事でやる。プログラムは、置き場の文をそのまま写す）
- 案を自動で組み立てる共通のプログラムを作ること（修正内容の一覧に無い）
- 次の一手を出すプログラム（next_move.py）の直し（確かめずにミスをする問題の解決策の検討の後）

---

## 監査観点 (一般・auditor_template ①〜⑦)

該当なし（この監査は、実装が設計書のとおりかと、まこさんの要望を満たしているかだけを問う。①〜⑦の観点は、この争点に関係しない。結果の所見の「一般の観点」にも「該当なし」と書く）

---

## 監査観点 (本監査固有・Q1-QN)

★問いごとに優先度を付ける＝A（結論を変える）／B（実装の前に直す）／C（完成の測り方以外の書き漏れ）／D（結論に効かせない）。結果の所見は、この問いの番号をそのまま見出しにし、優先度の順に書く。時間が足りずに省いた問いは、結果にその番号を書く。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**優先度の理由**＝違えば、実装は設計書のとおりに作られていない

実装の前（commit 713e85a（依頼書を作った時点の HEAD。承認の控えをまだ commit していないので、実装の前はこの commit の版。`git show 713e85a:<パス>` で出せる。★この後に commit しても、この番号で出せる））の対象のファイル（`.claude/breaks/b186_design_hand_unknown_heading_pass.sh`・`.claude/breaks/b187_design_sections_check_ignored.sh`・`SDK/../../.claude/tools/gen_acceptance.py`・`SDK/../../.claude/tools/gen_core_requirements.py`・`SDK/../../.claude/tools/gen_design_sections.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json`）に、設計書 4-20 の実装の指示（64 件）を番号の順に当てた結果が、実装の後（依頼書を作った時点の作業中の変更（まだ commit していない。`git diff 713e85a -- <パス>` で見られる。★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、`git diff 713e85a <その commit> -- <パス>` で見る）。★この工事の中で、設計書の 4-4 の手順（G-1 の表の作り直しほか）の道具が、TARGET のファイルを書き出し直すことがある（例＝gen_materials.py --write が regime_detection_kb.md の件数の囲みを書き出す）。その行は実装の指示ではなく、設計書の 4-4・5 で照らす）と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**優先度の理由**＝在れば、設計書に無い変更が実装に混ざっている

実装の前（commit 713e85a（依頼書を作った時点の HEAD。承認の控えをまだ commit していないので、実装の前はこの commit の版。`git show 713e85a:<パス>` で出せる。★この後に commit しても、この番号で出せる））と実装の後（依頼書を作った時点の作業中の変更（まだ commit していない。`git diff 713e85a -- <パス>` で見られる。★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、`git diff 713e85a <その commit> -- <パス>` で見る）。★この工事の中で、設計書の 4-4 の手順（G-1 の表の作り直しほか）の道具が、TARGET のファイルを書き出し直すことがある（例＝gen_materials.py --write が regime_detection_kb.md の件数の囲みを書き出す）。その行は実装の指示ではなく、設計書の 4-4・5 で照らす）の差分（`.claude/breaks/b186_design_hand_unknown_heading_pass.sh`・`.claude/breaks/b187_design_sections_check_ignored.sh`・`SDK/../../.claude/tools/gen_acceptance.py`・`SDK/../../.claude/tools/gen_core_requirements.py`・`SDK/../../.claude/tools/gen_design_sections.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/design_section_map.json`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**優先度の理由**＝合わなければ、どの件を道具が当てたかを後から確かめられない

当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:design-doc-gen-form-20261013`）が、実装の指示の 64 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**優先度の理由**＝当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない

承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/design-doc-gen-form-20261013.md`）と、いまの設計書の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**優先度の理由**＝要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない

実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/design-doc-gen-form-20261013/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**優先度の理由**＝成り立たなければ、承認のときの「済」が根拠にならない

設計書の完成の条件（7 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 ../../.claude/tools/gen_acceptance.py --selftest`・`python3 ../../.claude/tools/gen_design_sections.py --check`・`grep -c -F '新しく入る数字と式の一覧' .claude/ratchet/design_section_map.json`・`grep -c -F 'ONE_ROW_OLD' ../../.claude/tools/gen_core_requirements.py`・`grep -c -F '_design_audit_reports' ../../.claude/tools/gen_acceptance.py`

### Q7 — まこさんの要望を、この工事の後の実装が満たしているか（問い2）（優先度 A）

**優先度の理由**＝満たしていない要望が在れば、まこさんの要望が届いていない（この答えが問い2 の答えになる）

下に並べた まこさんの要望を、この工事の後の実装が満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。この問いの答えが、結論を決める問い2 の答えになる。

  1. 目的：設計書を作るプログラムを直し、設計書の元の内容を、そのまま自動で設計書に書き写せるようにする
  2. 別セッションの監査の指摘 M-2・m-2・m-5・m-8 を、この工事に入れる
  3. 読むもの宣言のすり抜けを塞ぐ照らしを、この工事に入れる
  4. 外部検索の欄の直しは、次の工事（監査依頼書を作るプログラムの直し）でやる
  5. 古い形の設計書の元は残し、いままでどおりに読めるようにする
  6. 閾値を読む場所は、パラメータと同じ形に決めておく。置き場に欄が在れば写し、無ければ「未決」と出す
  7. 新しい項目の置き場所は、「新しく入る数字と式の一覧」を 4-9 のすぐ後、「検査やプログラムを直す工事で書く5つ」を 4-6 のすぐ後にする
  8. 4-19 の名前は、新しい形の設計書では、新しい名前に変える

### Q8 — 実装の指示64件は、承認した設計書のとおりに、漏れなく・余計なく当たっているか（優先度 A）

**優先度の理由**＝当て漏れや、設計書に無い直しが在ると、承認した設計書の中身と、実物が違う物になる

当てたのは、実装を書き込むプログラム（apply_audit_fix.py --design）で、CC は手で書いていません。結果は「当てた 64 件／当てなかった 0 件」でした。確かめ直すコマンドは3つです。1つ目は `python3 .claude/tools/apply_audit_fix.py --design --dry`（64件とも、もう当て終わっていると出るか）。2つ目は `python3 scripts/priority_rebuild/verify_design_contract.py --diff ../../.claude/state/acceptance.md`（SDK の下で走らせる。CC が走らせた結果は「齟齬: 0件」）。3つ目は、直すファイル4本（設計書を作るプログラム・検算・要件定義の行の一覧を作る所・項目の正本）の `git diff` です。実装の指示に無い直しが入っていないかを見てください。★CC の自己申告＝実装の後に、設計書の実装の指示に無い本物のファイルを、CC が直した物は在りません。ただし、確かめの途中で、CC の誤りで、前の工事の設計書の控えを1回 書き替えました（Q14 の2番）。

### Q9 — 当てた後の設計書を作るプログラムは、設計書の 4-5 と 4-12 のとおりに動くか。古い形の元から作る設計書は、当てた後も変わらないか（優先度 A）

**優先度の理由**＝このプログラムは、どの工事の設計書を作るときにも走る。誤って止めると、どの工事の設計書も作れなくなる。古い形の設計書の文字が変わると、承認済みの設計書が、作り直して比べる検査で落ちる

確かめ直すコマンドは4つです。1つ目は `python3 .claude/tools/gen_acceptance.py --selftest`（CC が当てた後の実物で走らせた結果は「selftest 26/26 pass」。足した番人は T19〜T25 の7つで、前からの最後の番人は T26）。2つ目は `python3 .claude/tools/gen_design_sections.py --check`（結果は「出どころ 128件 は、全部どれかの項目に入っています（項目 33件）」）。3つ目は `python3 .claude/tools/run_breaks.py --design .claude/state/acceptance.md --measure-only`（壊すプログラム2本とも期待どおり。b186 は終了コード 1・b187 は終了コード 1）。4つ目は、古い形の設計書の比べです。CC は、前の工事（design-origin-form-20261013）の設計書を、当てた後のプログラムで、別の置き場に作り直して（`--work design-origin-form-20261013 --out <作業場の .md>`）、承認済みの控えと diff で比べました。違う行は9行で、2-1 の表の「走らせた時点の数」の列の3行と、触る関数の行番号の囲みの6行でした。設計の文・実装の指示・完成の条件の行に、違いは在りませんでした。★CC の自己申告（1）＝新しい形の元で、本物の工事1件の設計書を作った実例は、まだ在りません。確かめたのは、自己テストの見本（検査やプログラムを直す工事の形）だけです。指標に触る工事の形は、番人 T25 が、関数を直に呼んで測っています。★CC の自己申告（2）＝写しで、いま在る工事のフォルダ45個を、当てる前と後に組んで比べました。45個とも同じでしたが、そのうち31個は、当てる前も後も、同じ文で止まって組めません（「実装の指示の直す前の文字が、実物と合いません」が23個・「直すファイルが在るのに、実装の指示が0件です」が7個・「工事のフォルダから設計書を組めません」が1個）。23個が合わない訳は、1個ずつは確かめていません。★CC の自己申告（3）＝設計書の 4-5 異常系の行を、本物の工事のフォルダで起こして確かめた物は在りません。自己テスト T20〜T24（知らない見出し・目標の④が空・完成の条件の行が無い・検算が落ちる・宣言のすり抜け）で見ています。残りの行は、コードを読んだだけです。

### Q10 — 設計書の監査 CP77 の Critical の2件は、直した後の設計書と実装で、解消しているか（優先度 A）

**優先度の理由**＝直した後の設計書は、設計書の監査を受け直していない。直しの一部は、監査が文字を書いておらず、CC が書いた。CC のほかに、直しの中身を確かめた人がいない

**1件目（4-7 に写す指標の行が、案の文と合わない。結果の 247〜252行）。**指摘は3つでした。（1）オフの指標と、資料の表に無い指標が、行に出ない。直し＝名前を探す相手に、オンとオフの一覧を足しました（監査の修正 1。関数 _hit_names と _indicator_rows）。（2）案に書いていない指標の行が出る（「前日POC」と書くと「POC」の行も出る）。直し＝長い名前から先に当て、当てた所を消してから、短い名前を探します（同じ修正 1）。2-2 の「この工事が関わる指標」の数も、同じ関数で数えます（実装 11）。（3）「カタログに在るか」の列が無い。直し＝列を2つ足しました。「カタログ（指標の定義の表）に在るか」は、オンとオフの一覧の291種に名前が在るかで出します。「承認済みの型の表に在るか」は、型の表の部品（parts）の名前から、指標の定義の表の関数 find で種類を引き、その種類に入っているかで出します（関数 _table_kinds）。確かめ直すには、当てた後の実物の自己テスト（番人 T25）と、写しの作業場で、関数 _auto_rows を、オフの指標の名前・「前日POC」・「ADX」を書いた文で呼んだ結果を見てください。★CC の自己申告（1）＝「カタログ」と「承認された範囲」が何を指すかは、要件定義の文書には書いてありません。CC が、プログラムの実物から読みました（engine_tuner_exec.py の 698行の検査 G6・gen_signal_families.py の 682行・gen_indicator_switch.py の 18〜19行・indicator_switch.json の counts）。この読みが正しいかを、CC のほかに確かめた人はいません。★CC の自己申告（2）＝行の「オンとオフの一覧に名前が無い」の文字は、直した後も、いまの実物では出る道が在りません（名前を探す相手が、資料の表と、オンとオフの一覧だけのため。資料の表の175種は、オンの175種と同じ集合です）。どの一覧にも無い名前を案に書いた場合は、行が出ないだけです。★CC の自己申告（3）＝オフの指標の行は、資料の表に行が無いので、役割と値の欄が「置き場に行が無い」「範囲の行が無い」などの文で出ます。
**2件目（完成の条件が、F-1・F-2・F-3・F-6 の実装の一部を測らない。結果の 303〜308行）。**監査が挙げた5つの実装と、いま測っている番人は、次のとおりです。（1）6-4 に監査の結果ファイルを出す実装＝完成の条件に1行 足しました（監査の修正 2。関数の名前が在るかを数える行）。加えて、番人 T25 が、結果ファイルを探す関数が、この工事の監査 CP77 の結果ファイルを見つけるかを測ります。（2）売買に触らない工事の期待値分解を、目標から写す実装＝番人 T19 が、見本の設計書に「目標の③（net までのつながり）＝見本のつながり」が出るかを測ります（監査の修正 3）。（3）完成の条件に、やることの番号ごとの行が在るかを照らす実装＝番人 T22 を足しました（やることの番号を、完成の条件に無い番号に替えると止まるか）。（4）探す材料の一覧を、関わる指標の行だけにする実装＝番人 T25 が、探す材料の一覧を作る関数を、指標に触る工事の形で呼び、「この工事が関わる指標＝2種」と出るかを測ります。（5）概要を写す実装＝番人 T19 が、題の下・4-0・7-1 の3つの文字が出るかと、4-0 では冒頭に出ているかを測ります。確かめ直すには、当てた後の実物で、それぞれの実装を1つずつ外して、自己テストが落ちるかを、写しの作業場で見てください。★CC の自己申告＝（1）の、6-4 の行そのものに結果ファイルの名前が出ることは、測っていません（見本の工事には、監査の結果ファイルが無いため）。測っているのは、探す関数の戻りだけです。5つの実装を外すと番人が落ちることを、CC は外して確かめては いません。

### Q11 — 設計書の監査 CP77 の Major の8件は、直した後の設計書と実装で、解消しているか（優先度 A）

**優先度の理由**＝Q10 と同じ（直した後の設計書は、設計書の監査を受け直していない）

（1）**型・場面の決まり・時間足を写さない（結果の 164〜168行）。**型は、番号に加えて、名前でも探します（監査の修正 6）。場面の決まりの原文は、法則のファイルの「機械が読む判定」の欄から写します。「場面の決まり」の語が在る行に書いた、法則の番号で探します。時間足は、使える時間足の全部（observe_config.json の timeframes）と、役割ごとに使える時間足（型の表の role_lineage）を、4-7 に出します（関数 _timeframe_rows）。★CC の自己申告＝場面の決まりと時間足の置き場は、監査が「まこさんが決める」とした所です。CC が、プログラムの実物から読みました（場面の決まり＝engine_tuner_exec.py の審査の関数 _check_scene_rules の説明。時間足＝engine_tuner_gen.py の _allowed_tfs と _role_tfs）。時間足の行は、案が時間足に触れていなくても、4-7 に必ず出ます。役割ごとの時間足は、型の表が持つ物（型 E-a1・E-a4・E-a5・E-a8 に掛かる物）だけです。ひな型の 4-7 の表の「閾値」と「パラメータ」の行の右の列は、別の行としては出ず、指標の行の中の列（パラメータの名前と範囲・代表の値・閾値の代表の値）として出ます。
（2）**概要を写す先が、やることの表の F-1 と合わない（結果の 170〜174行）。**監査の修正 11（やることの表から「設計書の題の下・」を消す）は、入れていません。やることの表は変えずに、実装の側を表に合わせました。題の下にも概要の1文目を出し（実装 20）、4-0 では冒頭に出します（実装 19）。
（3）**要件定義の9番の対応に、目標の⑥が無い（結果の 205行）。**対応に足しました（監査の修正 9）。
（4）**索引が、中身を見ずに「書いた」と出す（結果の 206行）。**索引が指す目標の欄（③・⑤・⑥）が空のときは、索引に「空」と出します（監査の修正 10）。★CC の自己申告＝空でも止めません（止めるのは、前からの④と⑥だけ）。目標の①は、プログラムが読むもの宣言から写すので、見ません。2-0 と 7-3b は、いまも、いつも「書いた」と出ます。
（5）**狭めた読み方が、まこさんの発言かどうかを見ない（結果の 224行）。**監査は、修正の指示を書いていません。CC が、読み方を次の形に決めました。割り当てを作った日より後の記録では、「まこさん」の語のすぐ後ろに続く かぎ括弧の並びの中の文だけを拾います（実装 42）。「まこさん」の語から かぎ括弧までの間は、40文字までで、句点・矢印・別の かぎ括弧が在れば、その並びは見ません。この読み方で、入っていない物は、84件から2件（C-39・C-40）になりました。項目の正本の割り当ても、2件に直しました（実装 62）。★CC の自己申告＝40文字と、句点・矢印の決まりは、CC が決めた数字と形です。出どころは在りません。問いの形の発言（「〜はいらないの？」など）は、抜けを指す語が無いので、いまも拾えません。記録に、「まこさん」の語と かぎ括弧を離して書いた文も、拾えません。
（6）**法則の番号が、自己テストの番人の番号と同じ文字（結果の 254行）。**法則の番号は、「法則」の語が在る行だけで探します（監査の修正 5）。★CC の自己申告＝「法則」の語を書かない行に在る法則の番号は、写されなくなりました。同じ行に「法則」の語と、自己テストの番号（T1〜T5）の両方が在ると、いまも取り違えます。
（7）**「売買に触るか」の決め方が2つ在る（結果の 256行）。**新しい形の設計書では、売買に触るかを決める関数（touches_trading）が、先頭に出す工事の種類と同じ決め方（work_kind）で答えます（実装 38）。期待値分解を目標から写す所も、工事の種類で決めます（監査の修正 7）。★CC の自己申告＝古い形の設計書は、前の決め方のままです（承認済みの設計書の文字を変えないため）。
（8）**いま在る置き場のうち、種類②と決まる物が在る（結果の 258行）。**種類①と決める語に、materials.json・exit_families・regime_detection_kb の3つを足しました（監査の修正 8）。★CC の自己申告＝置き場のファイルが今後 増えれば、語をまた足す必要が在ります。

### Q12 — 設計書の監査 CP77 の Minor の12件は、どう扱ったか。扱いは妥当か（優先度 B）

**優先度の理由**＝12件のうち、この工事で直した物と、直していない物が在る。直していない物の理由を、CC の申告だけに頼らないため

**この工事で直した物（7件）。**「3-2 決めてほしいこと」に、ひな型の★の行を残して「無し」と書くと止まる件（結果の 178行）＝★の行を、中身に数えません（実装 39）。4-21 と 4-22 の見出しの下の表示が、案の見出しの名前と違う件（181行）＝案の見出しの名前で出します（実装 40）。「新しく足した関数を1つも通りません」の文（194行）＝文を直しました（監査の修正 13）。プログラムの出力の2件の割り当て先（225行）＝拾い方を直して、2件を拾わなくなったので、割り当てから外しました（実装 62）。足す自己テストの番人の呼び名のずれ（309行）＝設計書の文を、出る番号（T19〜T25。最後は T26）に直しました。直しが新しい形だけに入る事が、設計書に無い件（179行）＝設計書の5番の節に書きました。検算が止まったときに、項目の正本を直す道が、設計書に無い件（282行）＝設計書の 4-13 の6に書きました。
**新しい形の設計書でだけ直した物（1件）。**どの設計書にも出る「118件」の固定の文（195行）＝新しい形の設計書では、数を書きません（実装 41）。古い形の設計書は、同じ文字のままです。
**直していない物（4件）。**対応の表の 7-3b の5行（56行）と、段落の間の空行（64行）＝古い形の設計書の文字は、変えていません。新しい形では、この工事の実装で直ります。代表の値が置き場の形のまま出る件（180行）＝置き場の中身の直しは、この工事の やらないこと です。指標の修正の工事で直します。見出しの下の表示を新しい形に替える変数を立てる所（283行）＝直す相手は、監査依頼書を作るプログラムで、次の工事で直します。★CC の自己申告＝直していない4件は、まだ、次の工事の表に行を足していません。締めのときに足します。

### Q13 — 設計書の監査 CP77 の Process の4件は、どう扱ったか（優先度 B）

**優先度の理由**＝Process の所見は、CC の確かめ方の弱さ。同じ弱さが、直した後の実装に残っていないかを見るため

（1）見直し表が、置き場から写す所を、指標1件で「合う」と判定した件＝番人 T25 を、見本1件でなく、11の場面を1つずつ測る形にしました（オフの指標・「前日POC」と「POC」・自己テストの番号と法則の番号・場面の決まり・型の名前・時間足・関わる指標の数・監査の結果ファイル ほか）。置き場の件数は、jq で数えました（資料の表 175種＝オン 175種・オフ 116種は資料の表に0件・名前が別の名前の一部になる組 39組）。（2）見直し表が、番人の呼び名を、出る番号と照らしていない件＝当てた後の実物の自己テストの出力で、T19〜T26 の番号を確かめました。（3）組めない32個の理由を調べずに案を出した件＝写しで確かめるプログラムに、止まるときの文を工事ごとに出す所を足しました。結果は、Q9 の自己申告（2）のとおりです（いまは31個）。（4）外部検索要請のクエリ案が、検索の言葉でない件＝直していません。直す相手は、依頼書を作るプログラムで、次の工事で直します。★CC の自己申告＝番人 T25 と、番人 T22 は、CC が書きました。直した人と、確かめる番人を書いた人が、同じです。番人が、監査の挙げた場面を本当に測れているかを、見てください。

### Q14 — 承認した設計書と実物の間に、CC が知っている食い違いと、決まった流れから外れた所が、合わせて7つ在る。ほかに無いか（優先度 B）

**優先度の理由**＝設計書と実物が違う所と、流れから外れた所を、CC の申告だけに頼らないため

★CC の自己申告（1）＝設計書の 4-12 の5番のコマンド（`gen_acceptance.py --work design-origin-form-20261013 --verify`）は、書いたとおりには確かめられません。このコマンドは、いまの設計書の置き場（この工事の設計書）を相手にするので、違う工事どうしを比べる形になります。CC は、書く先を別の置き場にして作り直し、承認済みの控えと diff で比べました（Q9 の4つ目）。★CC の自己申告（2）＝その確かめの途中で、CC の誤りで、前の工事の承認済みの設計書の控え（acceptance_archive の design-origin-form-20261013.md）を、1回 書き替えました。書く先を指す旗（--out）に、控えのファイルを渡したためです（この旗は、照らす旗と一緒に渡しても、必ず書きます。CC は、走らせる前に確かめていませんでした）。変わったのは9行（2-1 の表の、走らせた時点の数の3行と、触る関数の行番号の囲みの6行）でした。まこさんが、git で、最後のコミットの中身に戻しました。いまは、git で比べて、違う行は0行です。★CC の自己申告（3）＝設計書の監査 CP77 の修正のうち、修正を当てるプログラムで入れたのは、1・2・3・5・6・7・8・9・10・13 の10件です。修正 4・12（案を作り直すコマンド）と、修正 14（設計書を作り直すコマンド）は、CC が直に走らせました。修正 11 は、入れていません（Q11 の2番）。当てた記録に在るのは、10件だけです。次の一手を出すプログラムは、この工事の段を「6」のまま出します。★CC の自己申告（4）＝承認をお願いする前に、CC は、本物の設計書を、1行目から最後までは読み直していません。読んだのは、作り直しで変わった所（0-1 の節）と、監査の修正で変わった所です。★CC の自己申告（5）＝直した後の設計書は、設計書の監査を受け直していません。この実装の監査で、Q10〜Q13 として確かめていただく形にしました。★CC の自己申告（6）＝設計書の 6-4 の1行は「この設計書は監査の指摘を受けていない」と出ていますが、事実と違います（承認した設計書は、監査 CP77 の修正を入れた版です）。この設計書は古い形の元から作るので、直しは入りません（設計書の5番の節に書いてあります）。★CC の自己申告（7）＝設計書の 7-4 の1文「承認ゲートの対象なので承認は要ります」は、いまの実物と合いません。設計書を作るプログラム（.claude/tools の下の .py）は、いまは、実装の前に承認を求める検査の相手に入っていません。この文は、どの設計書にも書かせている文で、この工事では直していません。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

件数: 0 件 (結果の外部検索の節にも「該当なし」と書く)

該当なし（この監査は、実装が設計書のとおりかを実物で照らす。外部の知見は答えに要らない。設計の理由を調べる外部検索は、設計書の監査で行う）

---

## 依頼を出した CC の自己申告

1. **この工事の外の作業中の変更**＝`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_request_understood.sh`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）

(結果は、この番号ごとに1件ずつ答える)

---

## 結果ファイルフォーマット (auditor 用)

`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-13_design_doc_gen_form_20261013_impl_cp78_audit_report.md` に、次の 11 節をこの順で出力する。★節の名前と並びは変えない。どの種類の監査でも同じ。

| # | 結果の節 | 依頼書の対応する項目 |
|---|---|---|
| 1 | **監査の相手と版**（依頼書のパス・監査の相手・ハッシュ値を照らした結果・実施日） | 監査依頼メタ情報 |
| 2 | **監査対象の型宣言**（数値型・コード型・文書型のうち該当するもの全部） | —（結果だけ） |
| 3 | **監査対象の事実データの確認**（依頼書の事実データを、自分で確かめた結果） | 監査対象の事実データ |
| 4 | **所見**（依頼書の問いの番号をそのまま見出しにし、依頼書の優先度の順に書く。一般の観点 ①〜⑦ は PASS / FAIL。各所見の末尾に、対応する修正の番号を書く。直し方の文は書かない。省いた問いは番号を書く） | 監査観点（一般・本監査固有）と優先度 |
| 5 | **外部検索**（依頼書の件数の検索対象に1つずつ・URL と逐語） | 外部検索要請 |
| 6 | **依頼を出した CC の自己申告への答え**（依頼書の番号ごとに1件ずつ） | 依頼を出した CC の自己申告 |
| 7 | **総合判定**（結論を決める問いへの答え〔問いごとに YES / NO と根拠〕・下の「結論の決め方」の3つのどれか・重さごとの件数） | この監査で答えてほしいこと・auditor 宣言の戻り報告 |
| 8 | **修正の指示**（下の「修正の指示の書き方」の形だけで書く。重さは Critical・Major・Minor） | 着手前必読（直す相手のファイル） |
| 9 | **CC プロセス欠陥対策**（下の「修正の指示の書き方」の形だけで書く。重さは Process） | —（結果だけ） |
| 10 | **開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由** | 着手前必読 |
| 11 | **本物のファイルを書き替えていないこと**（`git status --short` の出力） | auditor 宣言の禁止（本物を書き替えない） |

依頼書だけの項目＝監査依頼の経緯・この監査の前提・この監査の作業場・大目的・監査スコープ・必ず守ること。

### 結論の決め方

依頼書の「この監査で答えてほしいこと」に結論の決め方が在れば、それを使う。無ければ次の3つ。

- **GO**＝Critical が0件。
- **CONDITIONAL-GO**＝Critical が在る。直せば先に進める。
- **NO-GO**＝直し方の向きが違う。何が違うかを、4 の所見で、指摘の文と実物の行で示す。

### 重さの決め方

- **Critical**＝結論を変える。
- **Major**＝直すべきだが、結論は変えない。
- **Minor**＝結論に効かせない（前の「別枠」もここに入れる）。
- **Process**＝CC の進め方の欠陥。9 に書く。

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

---

## 必ず守ること (auditor 守則)

- 目標 ($1,900/月) の達成可能性の判定＝該当なし（この監査は、実装が設計書のとおりかを照らす）
- 月次 NET ≥ $1,900 を下げる方向の提案禁止 (cc_role §1.0 / auditor_template L15)
- 「可能性がある」「かもしれない」「検討の余地」は禁止 (auditor_template L20)
- 数値根拠の断言 or 「データ不足 (理由: 〇〇)」で答える
- 同型バイアス警告: 同一訓練ベース AI として CC の論理に共感しすぎないこと (auditor_template L24-30)
- ChatGPT 等の外部 AI 使用不可
- 外部検索＝該当なし（この監査では外部検索を求めない）
- トレードの外部認知＝該当なし（この監査は、実装が設計書のとおりかを照らす）

---

依頼書終わり。

---

## まこさん向け呼びかけ例文 (新規セッション起動時)

別 Claude Code セッションを開き、本依頼書のフルパスを明示して以下のように依頼:

```
監査してほしい
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-13_design_doc_gen_form_20261013_impl_cp78_audit_request.md
```

または

```
本依頼書を読んで監査して
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-13_design_doc_gen_form_20261013_impl_cp78_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp78_work/cp78_src.gen.md src_sha256=2ff42ed01768837c7a79c96dd652418345c806fae1df1ee0345b673c0f17f30f body_sha256=cd435377e222d2e68b9fe9bb0612f6bd9f484a4c951f71c5886c7aeeadf06ce3 -->

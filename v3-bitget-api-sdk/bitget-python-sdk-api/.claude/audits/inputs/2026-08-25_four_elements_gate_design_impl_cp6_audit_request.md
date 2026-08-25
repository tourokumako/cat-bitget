# 【監査依頼】4要素ゲート（acceptance.md の設計と engine_tuner_gen.py の実装）の監査

---

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 5 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-Q4 + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて結果ファイル `.claude/audits/2026-08-25_four_elements_gate_design_impl_cp6_audit_report.md` を Write
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / NO-GO / PIVOT / OTHER)
   - 最優先指摘 (Critical) 件数

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)
- **★起案 CC の見直しの結果（`.claude/state/session_worklog_20260825.md` の §2 に在る）を、監査が終わるまで読まないこと**（独立性の確保。監査後にまこさんが突き合わせに使う）

---

## 監査依頼メタ情報

- 依頼日: 2026-08-25
- 依頼者: CC (起案)。発意＝まこさん（起案 CC の自己見直しだけでは足りないため）
- 監査区分: cp6（設計＋実装の監査）
- 監査対象タスク: 4要素ゲート＝「指標・閾値・パラメータ・時間足」の使い方を engine_tuner に守らせる強制（設計書と実装）
- 結果ファイル保存先: `.claude/audits/2026-08-25_four_elements_gate_design_impl_cp6_audit_report.md`
- 入力ファイル保存先 (本依頼書): `.claude/audits/inputs/2026-08-25_four_elements_gate_design_impl_cp6_audit_request.md`

---

## 監査依頼の経緯

1. 2026-08-24 まこさんの依頼（逐語）＝「指標、閾値、パラメータ、時間足の役割に基づき、法則に則って４つを組み合わせ、Entry/Exitやレジーム判定などの条件を作る」（出どころ＝リポジトリ直下 `.claude/state/session_worklog_20260824.md` §20-1）。これを守らせる強制を作ることになった。
2. 58回目（2026-08-24〜25）に起案 CC が設計書 `.claude/state/acceptance.md`（リポジトリ直下）を書き、実装の一部を先に行った。**★この設計書は未承認**（最後に承認された控え＝`.claude/ratchet/acceptance_archive/four-elements-gate-20260824.md`＝出口を含める前の版）。**★同じ58回目に、起案 CC が設計書へ「既に在る」と虚偽を書いていたことが、まこさんの指摘で発覚している**（同 worklog §20-2-0）。
3. 2026-08-25 まこさん指示（逐語）＝「この設計も怪しいので見直せ」。起案 CC が見直したが、起案 CC 自身の見直しには同型バイアスが残るため、本監査を依頼する。

---

## 着手前必読 (省略禁止・auditor 用・5 件)

> パスは、リポジトリの根（cat-bitget/）からのもの。

1. `.claude/state/acceptance.md`（445行）— 監査対象の設計書（未承認・4要素ゲートの設計と完成の条件）
2. `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py`（4,547行）— 監査対象の実装（売買ルールの案を作るプログラム。印 `_param_src`/`_q_src`・`assert_marks`・`assert_roles` を含む）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py`（4,004行）— 検証器（条件データを調べる部分。カタログ・時間足・場面の決まりの検査を含む）
4. `.claude/state/session_worklog_20260824.md` §20 — 依頼の逐語と58回目の経緯（起案 CC が外したことの記録）
5. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/signal_families_approved.txt`（1行）— 型の表の承認の印（型の表の実体は `engine_tuner_gen.load_signal_table` が読む）

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = **設計書 `.claude/state/acceptance.md` と実装が、まこさんの依頼（上の逐語1行）を強制できているか**。net の数字・各戦略の性能・engine_tuner のその他の欠陥（D14 ほか＝`engine_tuner_defects.md` で別管理）の判定は対象外。

---

## 監査対象の事実データ

### 対象ファイルの実測（2026-08-25・機械の出力）

| ファイル | 行数 | sha256（先頭16桁） |
|---|---|---|
| `.claude/state/acceptance.md` | 445 | f05c9dfe58c7ef52 |
| `scripts/priority_rebuild/engine_tuner_gen.py` | 4,547 | 9102998cd5ba6ccd |
| `scripts/priority_rebuild/engine_tuner_exec.py` | 4,004 | 8a606184d6ed4cf8 |
| `.claude/ratchet/signal_families_approved.txt` | 1 | 7d8ad7e78b098a1a |

### 守るべき6つ（まこさんが確認済みの一覧・`next_step.md`（0-A4）からの複写）

| # | 守るべきこと |
|---|---|
| 1 | 指標が、承認済みのカタログに在るものから使われている |
| 2 | 閾値が、範囲から探されている |
| 3 | パラメータが、範囲から探されている |
| 4 | 時間足が、使える時間足から指定されている |
| 5 | 4つが、それぞれの役割に沿って使われている |
| 6 | つなぎ方が、型の表と場面の決まりに沿っている |

### 承認の状態

- 現在の `.claude/state/acceptance.md`＝**未承認**（`session_worklog_20260824.md` §20-6）。
- 実装の一部（印・検査の関数）は、承認前に `engine_tuner_gen.py` へ入っている（同 §20-5）。

---

## 監査観点 (一般・auditor_template ①〜⑦)

- ①統計学的妥当性
- ②リスク管理
- ③認知バイアス
- ④ソフトウェア工学
- ⑤再現性
- ⑥実行プロセス
- ⑦主エージェントバイアス

---

## 監査観点 (本監査固有・Q1-Q4)

### Q1 — 完成の条件は目的を担保するか

`.claude/state/acceptance.md` §8（受け入れ判定）の各条件について、①その条件を全部 満たしても目的（守るべき6つを、入口・場面の判定・出口の3か所で守らせる）に届かない穴が無いか ②書いてあるとおりに測れない条件・曖昧な条件が無いか、を1件ずつ判定せよ。

### Q2 — 強制は本物か（バイパスの有無）

実装の強制（印 `_param_src`/`_q_src`・`assert_marks`・`assert_roles`）は、「値の出どころ（範囲から探したのか・決まった一覧から取ったのか）」を**本当に**保証するか。実物のコードで確かめよ。特に、**将来の小さな変更（1行の追加など）で、値の出どころを変えないまま検査だけ通せる道**が無いかを、攻撃者の目で探せ。

### Q3 — 設計書と実物は一致しているか

設計書の記述（「在る」「止まる」の主張・行番号・SPEC の関数一覧・18マスの実測表）を、実物のコードと1件ずつ突き合わせ、食い違いを全部 挙げよ。設計書の中で記述どうしが矛盾している箇所も挙げよ。

### Q4 — 18マスを独立に測り直せ

6つ × 3か所（入口・場面の判定・出口）の18マスについて、「どの瞬間に・どのプログラムの・どの行が止めるか」を実物から独立に特定せよ。**設計書の表を写さず、自分で測ること。**止まらないマスと、止まる瞬間が設計書の主張と違うマスを挙げよ。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

`.claude/memory/technical_analysis_knowledge_base.md` 等の内部知識に閉じない。auditor は以下の **外部検索を必ず実施** すること。ChatGPT 等の外部 AI 使用不可 (まこさん課金外)。

### 検索対象 (例・auditor 適宜拡張)

1. **戦略最適化のパラメータ探索空間の設計**:
   - クエリ案: trading strategy optimization parameter search space discrete grid vs continuous range overfitting
   - 期待発見: 離散リストと連続範囲の使い分け・データスヌーピングとの関係
2. **生成物の検証ゲートの設計（自己申告の印の弱さ）**:
   - クエリ案: validation gate design provenance tagging self-attestation weakness software
   - 期待発見: 「作った側が自分で付ける印」がなぜ強制にならないか・強制にする設計

---

## 結果ファイルフォーマット (auditor 用)

`.claude/audits/2026-08-25_four_elements_gate_design_impl_cp6_audit_report.md` に以下 7 セクションを出力:

1. **Step -1 監査対象の型宣言** (混合型: コード型 + 文書型)
2. **Step 0 指摘前提確認** (事実データ verify + spec 文言 verify)
3. **観点 ①〜⑦ + Q1-Q4 の所見** (各観点・各 Q に対し「数値根拠ある断言」or「データ不足 (理由)」)
   - 観点 = PASS / FAIL 明示
   - Q = 一致 / 食い違い N 件 明示（該当行の逐語引用つき）
4. **外部検索結果サマリー** (検索クエリ + 主要発見 5-10 件・URL or 論文出典)
5. **総合判定**:
   - Verdict: GO / NO-GO / PIVOT / OTHER
   - 根拠
6. **改善方向性** (具体提案 3-7 件・優先度明示 Critical/Major/Minor)
7. **CC プロセス欠陥対策** (cc_role §1.4.6 改訂提案・該当があれば)

---

## 必ず守ること (auditor 守則)

- **目標 ($1,900/月) 達成可能性判定は対象外**（本監査は強制の設計と実装の監査）
- 月次 NET ≥ $1,900 を下げる方向の提案禁止 (cc_role §1.0 / auditor_template L15)
- 「可能性がある」「かもしれない」「検討の余地」は禁止 (auditor_template L20)
- 数値根拠の断言 or 「データ不足 (理由: 〇〇)」で答える
- 同型バイアス警告: 同一訓練ベース AI として CC の論理に共感しすぎないこと (auditor_template L24-30)
- ChatGPT 等の外部 AI 使用不可
- **外部検索は WebSearch / WebFetch ツールで必ず実施**
- 指摘には必ず**実物の行番号と逐語引用**を付ける（まこさんが英語とコードを読めない前提で、日本語の説明も1行 添える）

---

依頼書終わり。

## まこさん向け呼びかけ例文 (新規セッション起動時)

別 Claude Code セッションを開き、本依頼書のフルパスを明示して以下のように依頼:

```
監査してほしい
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-25_four_elements_gate_design_impl_cp6_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

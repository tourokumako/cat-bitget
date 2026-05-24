# 【監査依頼テンプレート】<タスク名>

> 本ファイルはテンプレ。新規監査依頼を作る際は本ファイルを `2026-XX-XX_<task>_cpN_audit_request.md` にコピーし、`<...>` 部分を埋めて使用する。
> テンプレ自体は編集禁止 (構造を維持する)。

---

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 N 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて結果ファイル `.claude/audits/2026-XX-XX_<task>_cpN_audit_report.md` を Write
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / NO-GO / PIVOT / OTHER)
   - 最優先指摘 (Critical) 件数

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

## 監査依頼メタ情報

- 依頼日: 2026-XX-XX
- 依頼者: <CC (起案者) / まこさん>
- 監査区分: <CP3.5 / CP4 / CP5 / CP6 / 方法論監査 / その他>
- 監査対象タスク: <例: Step I-4.5 §4.1 判定再評価 / Phase 1 v6 6 案完走後判定>
- 結果ファイル保存先: `.claude/audits/2026-XX-XX_<task>_cpN_audit_report.md`
- 入力ファイル保存先 (本依頼書): `.claude/audits/inputs/2026-XX-XX_<task>_cpN_audit_request.md`

---

## 監査依頼の経緯

1. <経緯 1 行目>
2. <経緯 2 行目>
3. <経緯 3 行目>

---

## 着手前必読 (省略禁止・auditor 用・N 件)

1. <ファイル相対パス> §<section> (L<line>-<line>) — <1 行要約>
2. <ファイル相対パス> §<section> — <1 行要約>
3. ...

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = <スコープ明示>。<スコープ外項目があれば「○○判定は対象外 (理由)」>

---

## 監査対象の事実データ

### <データセット 1 名>

<表 / リスト / コードブロック>

### <データセット 2 名>

...

---

## 監査スコープ

### 監査対象 (本監査内)

- <観点 1>
- <観点 2>
- ...

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- <スコープ外 1> → <移行先>
- ...

---

## 監査観点 (一般・auditor_template ①〜⑦)

- ①統計学的妥当性
- ②リスク管理
- ③認知バイアス
- ④ソフトウェア工学
- ⑤再現性
- ⑥実行プロセス
- ⑦主エージェントバイアス

(各観点を本タスクに適用する際の具体的指示があればここに追記)

---

## 監査観点 (本監査固有・Q1-QN)

### Q1 — <観点名>

<質問内容 + 監査者が verify すべき事項>

### Q2 — <観点名>

<質問内容>

### ... (必要数まで追加)

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

`.claude/memory/technical_analysis_knowledge_base.md` 等の内部知識に閉じない。auditor は以下の **外部検索を必ず実施** すること。ChatGPT 等の外部 AI 使用不可 (まこさん課金外)。

### 検索対象 (例・auditor 適宜拡張)

1. **<検索トピック 1>**:
   - クエリ案: <検索クエリ>
   - 期待発見: <業界相場・論文・OSS 実装>
2. **<検索トピック 2>**:
   - クエリ案: ...
3. ... (必要数まで追加)

---

## 結果ファイルフォーマット (auditor 用)

`.claude/audits/2026-XX-XX_<task>_cpN_audit_report.md` に以下 7 セクションを出力:

1. **Step -1 監査対象の型宣言** (混合型: 数値型 + コード型 + 文書型 / 該当する型を明示)
2. **Step 0 指摘前提確認** (事実データ verify + spec 文言 verify)
3. **観点 ①〜⑦ + Q1-QN の所見** (各観点・各 Q に対し「数値根拠ある断言」or「データ不足 (理由)」)
   - 観点 = PASS / FAIL 明示
   - Q = 業界整合 / 改善余地 N 件 明示
4. **外部検索結果サマリー** (検索クエリ + 主要発見 5-10 件・URL or 論文出典)
5. **総合判定**:
   - Verdict: GO / NO-GO / PIVOT / OTHER
   - 業界基準・学術根拠を伴う根拠
6. **改善方向性** (具体提案 3-7 件・優先度明示 Critical/Major/Minor)
7. **CC プロセス欠陥対策** (cc_role §1.4.6 改訂提案・該当があれば)

---

## 必ず守ること (auditor 守則)

- **目標 ($1,900/月) 達成可能性判定は対象外**の場合は明示
- 月次 NET ≥ $1,900 を下げる方向の提案禁止 (cc_role §1.0 / auditor_template L15)
- 「可能性がある」「かもしれない」「検討の余地」は禁止 (auditor_template L20)
- 数値根拠の断言 or 「データ不足 (理由: 〇〇)」で答える
- 同型バイアス警告: 同一訓練ベース AI として CC の論理に共感しすぎないこと (auditor_template L24-30)
- ChatGPT 等の外部 AI 使用不可
- **外部検索は WebSearch / WebFetch ツールで必ず実施**
- 内部文書だけでなく、トレードについての外部認知 (Crypto futures algo trading の業界実情) を踏まえる

---

依頼書終わり。

## まこさん向け呼びかけ例文 (新規セッション起動時)

別 Claude Code セッションを開き、本依頼書のフルパスを明示して以下のように依頼:

```
監査してほしい
.claude/audits/inputs/2026-XX-XX_<task>_cpN_audit_request.md
```

または

```
本依頼書を読んで監査して
.claude/audits/inputs/2026-XX-XX_<task>_cpN_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

# 【タスク】最大級の禁止事項「本番運用再現性」を 5 箇所に埋め込み（Prime Directive 固定）

発行日: 2026-05-15
承認: まこさん（明示的 GO）
本ルート: WORKFLOW.md 改訂11 §🔴現在のフェーズ Step 1 の **前段** として実施（trailing/fixed_tp 修正の前に、再発防止構造を固定する）

## 構造化ルール準拠

- 保存先: `.claude/instructions/2026-05-15_prime_directive_embed.md`
- 完了報告: `.claude/instructions/2026-05-15_prime_directive_embed_completion.md`
- 着手前に `.claude/instructions/2026-05-15_governance_docs_integration.md` を参照しフォーマットを踏襲

## このタスクの位置づけ（最重要）

trailing leak は本プロジェクトで 7 回目の同種事故（フラクタル / MA70 / M_dom / 期間ソート / §8違反 / trailing / 読んだふり）。「気をつける」「コメントに防止と書く」「実装後に verify する」では止まらないことが過去 6 回の再発で実証されている。

本タスクは、**「本番運用で再現不可能な実装を、いかなる工程でも使用しない」** を最大級の禁止事項（Prime Directive）として固定し、5 つの異なる文書入口に同一基準を埋め込むことで、どの入口を通っても必ず引っかかる構造を作る。

文書を増やすだけでは止まらないことも実証済み（L-159/L-160 を入れて1日で再発）。本タスクの効力は「文書」ではなく「**実装前に発動する機械的ゲート**」と「**5 箇所に同じ基準が冗長配置されている構造**」にある。

---

## 着手前必読（省略禁止）

1. `WORKFLOW.md` §🔴現在のフェーズ（改訂11）
2. `CLAUDE.md` §⛔ 絶対禁止（NEVER）セクション全文 / §セッション開始時に必ず読むこと
3. `cc_ml_design_spec.md` §8 制約・禁止事項
4. `.claude/rules/false_positive_incident_policy.md` 全文（特に §2 類型A・F、§5 関所B）
5. `.claude/rules/web_claude_self_check.md` チェック A 全項目
6. `.claude/rules/feedback_pre_execution_premise_check.md` 全文
7. `.claude/memory/lessons_active.md` L-179（コメント信用禁止）/ L-181（旧記述放置禁止）/ L-182（期間全体ソート leak）

## Step 0-1: 必読ファイル引用（読んだふり防止・false_positive_incident_policy §2 類型G）

以下を完了報告に現物引用すること。期待値と一致しない/省略 → STOP：
a. CLAUDE.md §⛔ 絶対禁止（NEVER）セクションの先頭行・末尾行（埋め込み箇所の特定）
b. false_positive_incident_policy.md §1 「なぜこれが最重大なのか」冒頭2行（§0 を新設する位置の確認）
c. web_claude_self_check.md チェック A の最初の項目（埋め込み位置確認）
d. cc_ml_design_spec.md §8 制約・禁止事項の冒頭3項目（埋め込み位置確認）
e. feedback_pre_execution_premise_check.md の冒頭1ブロック（埋め込み位置確認）

---

## 共通の判定基準（5 箇所すべてに、この基準を埋め込む）

埋め込む内容の核は以下である。各文書の文脈に合わせて文言を調整するが、**判定基準は同一**：

### 判定基準（Prime Directive）

> **本番運用の推論時点 t において、その変数の値が因果的に確定済みで、かつ実際の取引システムから取得可能であるものだけを、計算式・判定式・採用ロジックに使用できる。**
>
> この基準は本プロジェクトの全ルールに優先する最大級の禁止事項（Prime Directive）である。
> エントリー判定・Exit判定・PnL計算・採用判定・パラメータ決定の全工程に適用する。
> 違反は `false_positive_incident_policy.md` §2 類型 A（look-ahead leak）として最重大インシデント扱い。

### 使えない例（推論時点 t で取得不能）

- 保有期間中の最大値・最小値（MFE/MAE）など、保有終了まで未確定の値
- K本後の価格など、t 時点で未到来の値
- 全期間を見渡して計算される値（期間全体ソート・期間全体の正規化等）
- test 期間の結果を見てから決めたパラメータ
- 学習データに含まれていない区間の集計値

### 使える例（推論時点 t で取得可能）

- 過去データの集計値で、当該時点を含まないウィンドウ（`shift(1)` 等で当該時点を除外したもの）
- 過去時点ですでに発表・確定済みの外部指標（ラグを正しく扱えば本番でも取得可能）
- train データだけで決定し、test 期間の結果に依存しない定数
- 過去に発生したイベントのフラグ（発生時刻 < t）

### 判定の根拠提示義務

「使える」と判定する変数については、**「t 時点で取得可能と判定した根拠」を1行で明示する義務**を負う。`exchange_spec.md` 等の確定タイミング記載と整合させる。根拠が示せない変数は計算式に入れない。

---

## 修正対象 5 箇所

（詳細は指示書本文参照）

### 修正1: `CLAUDE.md` §⛔ 絶対禁止（NEVER）への追加（先頭に最上位項目として）
### 修正2: `false_positive_incident_policy.md` §0 の新設（§1 より前に配置）
### 修正3: `web_claude_self_check.md` チェック A への追加（読了ゲート・第〇原則の直後）
### 修正4: `cc_ml_design_spec.md` §8 制約・禁止事項への追加（冒頭に最上位項目として）
### 修正5: `feedback_pre_execution_premise_check.md` への追加（最上位の項目として）

---

## 完了報告 必須証跡

1. Step 0-1 必読ファイル引用 a-e
2〜6. 修正1〜5 の before/after diff（各箇所）
7. 5 箇所すべての commit hash
8. 整合性 verify（5 箇所が同一判定基準を参照・文言矛盾なし）
9. 異常値スメルテスト: 該当なし（ドキュメント整合性修正のみ）

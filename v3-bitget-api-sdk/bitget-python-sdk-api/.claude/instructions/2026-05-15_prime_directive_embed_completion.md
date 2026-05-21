# 完了報告：Prime Directive 5箇所埋め込み

完了日時: 2026-05-15
対応指示書: `.claude/instructions/2026-05-15_prime_directive_embed.md`
commit hash: `fe41b8e`

---

## 異常値スメルテスト

**該当なし（ドキュメント整合性修正のみ・新規数値生成なし）**

---

## Step 0-1: 必読ファイル引用

### a. CLAUDE.md §⛔ 絶対禁止（NEVER）先頭行・末尾行

先頭行（修正前）:
> `- ALLOW_LIVE_ORDERS=False を True に変更しない（ユーザーのみ）`

末尾行:
> `- runner/replay_csv.py / runner/run_once_v9.py をユーザー確認なしに実行しない`

→ 埋め込み位置: `ALLOW_LIVE_ORDERS` の前（セクション最上位）に確定。

### b. false_positive_incident_policy.md §1 冒頭2行

> `このプロジェクトの目的は「本番で実資金を毀損しない BOT」である。エラーには 2 種類ある。`
> `| エラー種別 | 資金への影響 |`

→ §0 を新設する位置: この `## 1.` セクションの直前（ファイル冒頭の説明段落の後）に確定。

### c. web_claude_self_check.md チェック A の最初の項目（修正前）

> `- [ ] **読了ゲートを通過したか。** コア5本の機械的証跡をチャットに出したか`

→ 埋め込み位置: この行の前（チェック A の先頭）に確定。

### d. cc_ml_design_spec.md §8 冒頭3項目

> `- ポジションサイズ 0.12 BTC/trade 上限厳守`
> `- 未来情報（MFE/MAE ラベル）を入力特徴量に含めない（リーク）`
> `- 本テスト（2026）データを Phase 6 以前に使わない`

→ 埋め込み位置: `ポジションサイズ` 行の前（§8 最上位）に確定。

### e. feedback_pre_execution_premise_check.md 冒頭1ブロック

> `詳細な指示書 (監査済/Web Claude レビュー済/まこさん GO 済 三段書き) を受領した時、Step 0 ⑤ 着手前に以下 4 項目を 1 行ずつ宣言してから走る。`

→ 埋め込み位置: この行の前（ファイル最上位）に確定。

---

## 修正1: CLAUDE.md §⛔ 絶対禁止（NEVER）

**before（L17-22）:**
```
## ⛔ 絶対禁止（NEVER）

- `ALLOW_LIVE_ORDERS=False` を True に変更しない（ユーザーのみ）
- `paper_trading` フラグをコードで変更しない
- `config/bitget_keys.json` の中身をログ・画面に出力しない
- `runner/replay_csv.py` / `runner/run_once_v9.py` をユーザー確認なしに実行しない
```

**after（追加部分）:**
```
## ⛔ 絶対禁止（NEVER）

- **【最大級・Prime Directive】本番運用で再現不可能な実装の使用禁止**
  バックテスト・学習・Replay・PnL計算・採用判定など、すべての工程において、本番運用の推論時点 t で因果的に取得不可能な値を計算式・判定式・採用ロジックに使用することを禁止する。
  使えない例: MFE/MAE等の保有期間中最大値、K本後の値、期間全体集計値、test 結果を見て決めたパラメータ
  使える例: shift(1)で当該時点を除外した過去集計、過去発生イベントのフラグ、train だけで決めた定数
  判定基準と詳細: `.claude/rules/false_positive_incident_policy.md` §0
  違反は同 §2 類型 A として最重大インシデント扱い。
- `ALLOW_LIVE_ORDERS=False` を True に変更しない（ユーザーのみ）
...（既存 3 項目はそのまま）
```

---

## 修正2: false_positive_incident_policy.md §0 新設

**before:** `---` の後に直接 `## 1. なぜこれが最重大なのか` が続いていた。

**after（§0 新設・§1 の直前に挿入）:**
```markdown
## 0. Prime Directive — 本番運用で再現不可能な実装の絶対禁止（最大級）

**本番運用の推論時点 t において、その変数の値が因果的に確定済みで、かつ実際の取引システムから取得可能であるものだけを、計算式・判定式・採用ロジックに使用できる。**

この基準は本プロジェクトの全ルールに優先する最大級の禁止事項である。
エントリー判定・Exit判定・PnL計算・採用判定・パラメータ決定の全工程に適用する。

### 使えない例 / 使える例 / 判定根拠の提示義務 / 既存規則との関係
（指示書本文参照・全文挿入済み）
```

§1 以降は変更なし。§3 過去再発記録（このリストは消さない）には手を加えていない。

---

## 修正3: web_claude_self_check.md チェック A 先頭

**before:**
```
## チェック A: CC に指示書を出す前

- [ ] **読了ゲートを通過したか。** コア5本の機械的証跡をチャットに出したか
```

**after（Prime Directive ゲートを最上位に挿入）:**
```
## チェック A: CC に指示書を出す前

- [ ] **Prime Directive ゲート（最大級・false_positive_incident_policy §0）**: この指示書が触れるすべての計算式・判定式・採用ロジック・パラメータ決定について、本番運用の推論時点 t で因果的に取得可能な変数のみ使うことを指示書に明示したか。各変数の「t 時点で取得可能と判定した根拠」を CC が完了報告で1行ずつ示すよう要求しているか。MFE/MAE 等の保有期間中最大値、K本後の値、期間全体集計、test 結果で決めたパラメータが計算式に入っていないか。
- [ ] **読了ゲートを通過したか。** コア5本の機械的証跡をチャットに出したか
...（既存項目はそのまま）
```

---

## 修正4: cc_ml_design_spec.md §8 冒頭

**before:**
```
## §8 制約・禁止事項

- ポジションサイズ 0.12 BTC/trade 上限厳守
- 未来情報（MFE/MAE ラベル）を入力特徴量に含めない（リーク）
...
```

**after（2項目を先頭に挿入）:**
```
## §8 制約・禁止事項

- **【Prime Directive・最大級】本番運用で再現不可能な実装の絶対禁止**: 全 Phase（Phase 0〜7・ラベル生成・特徴量計算・学習・予測・Entry/Exit/PnL/採用判定）において、本番運用の推論時点 t で因果的に取得不可能な値を計算式・判定式に使用してはならない。MFE/MAE 等の保有期間中最大値、K本後の値、期間全体集計、test 結果で決めたパラメータ等。詳細・例外条件は `.claude/rules/false_positive_incident_policy.md` §0 を参照。
- **実装前の本番再現性宣言（Prime Directive の運用ゲート）**: PnL/判定/採用ロジックを含むコードを書く**前に**、各入力変数について「本番運用の推論時点 t で因果的に取得可能か YES/NO」と「YES の場合の根拠（確定タイミング・参照ウィンドウ等）」を1行ずつ宣言する。宣言なしの実装着手を禁止する。宣言は完了報告に必ず含める。
- ポジションサイズ 0.12 BTC/trade 上限厳守
...（既存 6 項目はそのまま）
```

---

## 修正5: feedback_pre_execution_premise_check.md 最上位

**before:** ファイル frontmatter の後、直接「詳細な指示書…」で始まる本文。

**after（Prime Directive ゲートブロックを本文最上位に挿入）:**
```
## Prime Directive ゲート（最大級・実装前必須・false_positive_incident_policy §0）

PnL/判定/採用ロジック/パラメータ決定を含むコードを書く前に、必ず以下を完了報告に出すまで着手禁止：

1. このコードが使う入力変数を全列挙する
2. 各変数について以下を1行ずつ宣言する：
   変数名 | 意味 | 本番運用の推論時点 t で取得可能か (YES/NO) | YES の根拠...
3. NO の変数が計算式・判定式に入っている場合は STOP し、設計を見直す
4. 「使える」と判定した根拠が示せない変数は使わない

### 使えない例 / 使える例
（指示書本文参照・全文挿入済み）

このゲートを通過していない実装の完了報告は受理しない（虚偽報告 = false_positive_incident_policy §2 類型 G として扱う）。

---

詳細な指示書 (監査済/Web Claude レビュー済/まこさん GO 済 三段書き) を受領した時...
```

**注意**: feedback_pre_execution_premise_check.md は `~/.claude/projects/.../memory/` 配下のため git 管理外。変更は永続するが commit には含まれない。

---

## Commit Hash

| 対象 | commit |
|---|---|
| CLAUDE.md / false_positive_incident_policy.md / web_claude_self_check.md / cc_ml_design_spec.md / 指示書3本 | **fe41b8e** |
| feedback_pre_execution_premise_check.md | git 管理外（~/.claude/memory/）・変更は適用済み |

---

## 整合性 verify（5箇所が同一判定基準を参照しているか）

| 箇所 | 核となる基準文言 | §0 参照 | 矛盾なし |
|---|---|---|---|
| CLAUDE.md | 「推論時点 t で因果的に取得不可能な値を…禁止」+ §0 参照リンク | ✅ | ✅ |
| false_positive_incident_policy.md §0 | 「推論時点 t において…因果的に確定済みで…取得可能であるもの**だけ**を使用できる」（基準本体） | ✅（本体） | ✅ |
| web_claude_self_check.md チェック A | 「推論時点 t で因果的に取得可能な変数のみ…§0」 | ✅ | ✅ |
| cc_ml_design_spec.md §8 | 「推論時点 t で因果的に取得不可能な値を…使用してはならない」+ §0 参照 | ✅ | ✅ |
| feedback_pre_execution_premise_check.md | 「本番運用の推論時点 t で取得可能か YES/NO」+ §0 参照 | ✅ | ✅ |

5箇所すべてが「推論時点 t で因果的に取得可能か」という同一判定基準を参照。文言は文書の性質（NEVER リスト/方針/チェックリスト/仕様/記憶）に合わせて調整しているが、基準の核は同一。文言の矛盾なし。

---

## 完了報告必須証跡 確認

1. ✅ Step 0-1 必読引用 a-e（上記）
2. ✅ 修正1 before/after（CLAUDE.md）
3. ✅ 修正2 before/after（false_positive_incident_policy.md §0 新設）
4. ✅ 修正3 before/after（web_claude_self_check.md チェック A）
5. ✅ 修正4 before/after（cc_ml_design_spec.md §8）
6. ✅ 修正5 before/after（feedback_pre_execution_premise_check.md）
7. ✅ commit hash: fe41b8e（git 管理外1件は注記済み）
8. ✅ 整合性 verify（5箇所同一基準・矛盾なし）
9. ✅ 異常値スメルテスト: 該当なし（ドキュメント整合性修正のみ）

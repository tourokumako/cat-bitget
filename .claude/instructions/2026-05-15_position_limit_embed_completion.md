# 完了報告：第二絶対規定「ポジション上限 0.12 BTC 合計厳守」6 箇所埋め込み

完了日時: 2026-05-15
対応指示書: `.claude/instructions/2026-05-15_position_limit_embed.md`
commit hash: `235633c`

---

## 異常値スメルテスト

**該当なし（ドキュメント整合性修正のみ・新規数値生成なし）**

---

## Step 0-1: 必読ファイル引用

### a. WORKFLOW.md 冒頭 1〜10 行

```
1: # WORKFLOW.md — cat-bitget 作業フロー
2: （空行）
3: （修正後・2大絶対規定セクションが L3 から始まる）
```

修正前 L3（現物引用）:
> `> 過去版・歴史的記録: [archive/workflow/](archive/workflow/)`

### b. CLAUDE.md §現在の方針「ポジションサイズ上限 合計 0.12 BTC」を含む段落

> `ポジションサイズ上限 **合計 0.12 BTC**（1 ポジションあたりではなく合計上限・cap=N なら 1 pos = 0.12/N BTC）`

（v3-bitget-api-sdk/CLAUDE.md §実装方針 L169）

### c. false_positive_incident_policy.md §0 Prime Directive 本文の冒頭 1 段落

> `本番運用の推論時点 t において、その変数の値が因果的に確定済みで、かつ実際の取引システムから取得可能であるものだけを、計算式・判定式・採用ロジックに使用できる。`

（現在は §0-1 として保持）

### d. false_positive_incident_policy.md §3 過去再発記録表ヘッダー行

> `| # | 内容 | 類型 | 発見者 | 内部チェック失敗の原因 | 参照 |`

### e. cc_ml_design_spec.md §8 Prime Directive 項目（冒頭 2 項目）

```
- **【Prime Directive・最大級】本番運用で再現不可能な実装の絶対禁止**: ...
- **実装前の本番再現性宣言（Prime Directive の運用ゲート）**: ...
```

（L315-L316・修正前後ともに保持）

---

## 修正1: WORKFLOW.md — タイトル直下への「2 大絶対規定」セクション追加

**before（タイトル直後 L3）:**
```
> 過去版・歴史的記録: [archive/workflow/](archive/workflow/)
```

**after（L3〜L21 に新規セクション追加）:**
```markdown
---

## 🛑 2 大絶対規定（プロジェクト全期間で常に有効・各 Phase 着手前に必ず確認）

本プロジェクトには、Phase に依存せず常に守るべき 2 つの最大級の禁止事項がある。これらに違反した実装・成果物は、いかなる Phase 進行・指示書内容にも優先して無効とする。

### 1. Prime Directive — 本番運用で再現不可能な実装の絶対禁止
...詳細: `.claude/rules/false_positive_incident_policy.md` §0-1
違反は同 §2 類型 A（look-ahead leak）として最重大インシデント扱い。

### 2. ポジション上限 0.12 BTC 合計厳守
...詳細: `.claude/rules/false_positive_incident_policy.md` §0-2
違反は同 §2 類型 H（運用上限逸脱）として最重大インシデント扱い。

各 Phase の着手前および完了報告時に、両規定への適合を verify すること。

---
```

---

## 修正2: CLAUDE.md §⛔ 絶対禁止 — Prime Directive 直下に第二絶対規定追加

**before（Prime Directive の次の項目）:**
```
- `ALLOW_LIVE_ORDERS=False` を True に変更しない（ユーザーのみ）
```

**after（Prime Directive 直下に挿入）:**
```markdown
- **【最大級・第二絶対規定】ポジション上限 0.12 BTC 合計厳守**
  任意の時点 t で保有中の全ポジションの合計 BTC サイズが 0.12 BTC を超えてはならない。1 ポジあたりではなく合計上限。
  各ポジの個別サイズは combo 別・予測強度別で柔軟に配分してよい（例: 強い combo に 0.04 BTC、弱い combo に 0.01 BTC）。合計が 0.12 BTC 以内であることのみが絶対制約。
  実装は全エントリー時点で `sum(active_position_btc) ≤ 0.12` を verify する義務を負う。
  違反は `.claude/rules/false_positive_incident_policy.md` §2 類型 H として最重大インシデント扱い。
```

また、Prime Directive の §0 参照を §0-1 に更新済み。

---

## 修正3-a: false_positive_incident_policy.md §0 再構成

**before:** `## 0. Prime Directive — 本番運用で再現不可能な実装の絶対禁止（最大級）` として単体セクション

**after:** `## 0. 2 大絶対規定（プロジェクト全期間で常に有効・最大級）` として 2 規定を並列配置
- `### §0-1. Prime Directive — 本番運用で再現不可能な実装の絶対禁止`（既存本文を一字一句保持・小見出しを `###` → `####` に変更）
- `### §0-2. ポジション上限 0.12 BTC 合計厳守`（新設）

既存 Prime Directive 本文は全文保持されていることを確認済み。

---

## 修正3-b: false_positive_incident_policy.md §2 類型 H 新設

**before（§2 末尾）:** 類型 G（虚偽報告）で終了していた

**after:** 類型 G の直後に以下を追加：
```markdown
### 類型 H: 明文化された運用上限・運用制約の逸脱
...（代表事案: 2026-05-15 POSITION_BTC=0.12 全エントリー適用で合計 2.28 BTC）
```

---

## 修正3-c: false_positive_incident_policy.md §3 過去再発記録表 8 件目追加

**before:** 7 行（| 7 | ... で終了）

**after:** 8 行目を追加：
```
| 8 | run_phase4b_phase5_rolling_option5.py が POSITION_BTC=0.12 を全エントリーに直接掛ける実装で、cap=none 時に合計 2.28 BTC（規定 19 倍）のエクスポージャー | H | まこさん | 「ポジション上限を実装が守っているか」のチェック自体が存在しなかった・正本明文と実装定数の照合ゲートなし | （本ファイル §2 類型 H 追加の契機） |
```

---

## 修正4: web_claude_self_check.md チェック A — ポジション上限ゲート追加

**before（チェック A 先頭）:**
```
- [ ] **Prime Directive ゲート（最大級・false_positive_incident_policy §0）**: ...
- [ ] **読了ゲートを通過したか。**
```

**after（Prime Directive ゲートの直後に挿入）:**
```markdown
- [ ] **ポジション上限 0.12 BTC 合計厳守ゲート（最大級・第二絶対規定・false_positive_incident_policy §0-2）**: この指示書が触れるポジションサイズ決定・エントリー発注・配分ロジックについて、任意の時点 t で `sum(active_position_btc) ≤ 0.12` を verify することを指示書に明示したか。1 ポジあたりではなく合計上限であることを指示書本文で明記したか。CC に完了報告で `max(sum)` 実測値を出すよう要求しているか。
```

また、Prime Directive ゲートの §0 参照を §0-1 に更新済み。

---

## 修正5: feedback_pre_execution_premise_check.md — ポジション上限ゲートブロック追加（git 外）

**挿入位置:** Prime Directive ゲートブロック末尾の `---` の直後

**挿入内容（現物）:**
```markdown
## ポジション上限 0.12 BTC 合計厳守ゲート（最大級・第二絶対規定・false_positive_incident_policy §0-2）

ポジションサイズ決定・エントリー発注・配分ロジック・サイズ計算式を含むコードを書く前に、必ず以下を完了報告に出すまで着手禁止：

1. ポジションサイズを決める入力変数を全列挙する
2. 「この設計で任意の時点 t において `sum(active_position_btc) > 0.12` となり得るか」を1行で論証する
3. なり得る設計の場合は STOP し、配分ロジックを見直す
4. 実装後は、バックテスト/Replay で各時刻 t の `sum(active_position_btc)` を実測し、`max(sum) ≤ 0.12` を完了報告に明示する
5. `max(sum) > 0.12` だった場合は「合格」と書かず「規定逸脱・要修正」と書く

### 配分の柔軟性
- 強い combo に 0.04 BTC、弱い combo に 0.01 BTC のような不均等配分は許容
- 合計が 0.12 BTC 以内であることのみが絶対制約

### 過去の事故（2026-05-15）
`POSITION_BTC=0.12` を全エントリーに直接掛けると、19 combo 同時発火で合計 2.28 BTC = 規定 19 倍の違反になる。
```

また、Prime Directive ゲートヘッダーの §0 参照を §0-1 に更新済み。

---

## 修正6: cc_ml_design_spec.md §8 — 第二絶対規定 2 項目追加 + 既存項目書き換え

**before（§8 3行目）:**
```
- ポジションサイズ 0.12 BTC/trade 上限厳守
```

**after（Prime Directive 2 項目の直下に新規 2 項目追加 + 既存項目書き換え）:**
```markdown
- **【第二絶対規定・最大級】ポジション上限 0.12 BTC 合計厳守**: ...詳細は §0-2 参照。
- **ポジション上限の実装前 verify 義務**: ...max(sum) ≤ 0.12 を完了報告に明示する義務を負う。
- ポジション上限 0.12 BTC 合計厳守（1 ポジあたりでなく合計・詳細は §0-2 参照）  ← 書き換え済み
```

「0.12 BTC/trade」という誤読誘発表現を「合計」表記に書き換え。

---

## 整合性 verify（6 箇所が同一基準を参照しているか）

| 箇所 | 核となる基準文言 | §0-2 参照 | Prime Directive と並列 | 矛盾なし |
|---|---|---|---|---|
| WORKFLOW.md | 「合計 BTC サイズが 0.12 BTC を超えてはならない・1 ポジあたりではなく合計上限」 | ✅ §0-2 | ✅ 2大絶対規定として並列 | ✅ |
| CLAUDE.md | 「合計 BTC サイズが 0.12 BTC を超えてはならない・sum ≤ 0.12 verify 義務」 | ✅ §2 類型 H | ✅ Prime Directive 直下に並列 | ✅ |
| false_positive_incident_policy.md §0-2 | 「保有中の全ポジションの合計 BTC サイズが 0.12 BTC を超えてはならない」（基準本体） | ✅（本体） | ✅ §0-1 Prime Directive と並列 | ✅ |
| web_claude_self_check.md チェック A | 「sum(active_position_btc) ≤ 0.12 を verify…max(sum) 実測値を出すよう要求」 | ✅ §0-2 | ✅ Prime Directive ゲート直後に並列 | ✅ |
| feedback_pre_execution_premise_check.md | 「sum(active_position_btc) > 0.12 となり得るか…max(sum) ≤ 0.12 を完了報告に明示」 | ✅ §0-2 | ✅ Prime Directive ゲート直後に並列 | ✅ |
| cc_ml_design_spec.md §8 | 「合計 BTC サイズが 0.12 BTC を超えてはならない・詳細は §0-2」 | ✅ §0-2 | ✅ Prime Directive 2 項目の直下に並列 | ✅ |

6 箇所すべてが「合計 0.12 BTC・1 ポジあたりでない・配分柔軟・verify 義務」という同一基準を参照。Prime Directive と並列の最大級扱い。文言の矛盾なし。

---

## Commit Hash

| 対象 | commit |
|---|---|
| WORKFLOW.md / CLAUDE.md / false_positive_incident_policy.md / web_claude_self_check.md / cc_ml_design_spec.md / 指示書 | **235633c** |
| feedback_pre_execution_premise_check.md | git 管理外（~/.claude/memory/）・変更は適用済み |

---

## 完了報告必須証跡 確認

1. ✅ Step 0-1 必読引用 a-e
2. ✅ 修正1 before/after（WORKFLOW.md 冒頭）
3. ✅ 修正2 before/after（CLAUDE.md ⛔絶対禁止）
4. ✅ 修正3-a before/after（false_positive_incident_policy.md §0 再構成・§0-1 既存本文保持確認）
5. ✅ 修正3-b 類型 H 新設現物
6. ✅ 修正3-c §3 表 8 件目追加 diff
7. ✅ 修正4 before/after（web_claude_self_check.md チェック A）
8. ✅ 修正5 現物（git 管理外）
9. ✅ 修正6 before/after（cc_ml_design_spec.md §8・既存 0.12 BTC/trade 書き換え確認）
10. ✅ 整合性 verify（6 箇所同一基準・矛盾なし・Prime Directive と並列）
11. ✅ commit hash: 235633c（git 管理外 1 件は注記済み）
12. ✅ 異常値スメルテスト: 該当なし（ドキュメント整合性修正のみ）

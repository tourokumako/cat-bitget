# 【完了報告】audit#19 監査結論 3 条件対応

完了日時: 2026-05-20
担当: CC (Claude Code)
対応指示書: `.claude/instructions/2026-05-20_audit19_audit_followup.md`

---

## §0 Step 0-1 必読引用 (読んだフリ防止)

### a. 監査結論セクション全文 (条件 1-3 表 + 重大懸念 1-2)

**出典**: `.claude/audits/2026-05-20_audit19_exchange_spec_full_verify.md` L232-251

```
### 判定: **条件付き PASS（3条件）**

| 条件 | 優先度 | 内容 |
| 1 | **必須・まこさん GO 前** | `.claude/auditor_template.md` L213: `最大 125x` → `最大 150x` に修正 |
| 2 | 推奨（低優先） | exchange_spec.md posLimit 行に「Support 記事による 10% 解釈は Cloudflare ブロックで独立 confirm 不可（2026-05-20）」を注記 |
| 3 | Phase 7-d 要件 | maxMarketOrderQty 単位を paper trading 実発注テストで confirm |

### 重大懸念
懸念1（必須対応）: `auditor_template.md` L213 の 125x 残存
- CC sweep が `.claude/rules/` 配下のみに限定され `.claude/auditor_template.md` を漏らした
- L-181 同型（設計転換時 旧記述全 grep sweep 義務）の再発

懸念2（監視継続）: F2 maxMarketOrderQty 単位の ⚠️ 維持
- 公式テキストによる明示的な BTC 単位確認が未完了
- Phase 7-d paper trading テストで確定するまで ⚠️ を外さない
```

### b. auditor_template.md L210-216 修正前現状 (実行ログ)

**sed -n '211,215p' auditor_template.md** 修正前:
```
**E. レバレッジ・証拠金**
- cap=1 で 0.12 BTC × BTC 価格 ÷ レバレッジ = 必要証拠金。清算ラインとの距離は十分か
- exchange_spec.md 最大 125x に対して実運用レバレッジを確認     ← 旧値 (修正対象)
```

**修正後**:
```
**E. レバレッジ・証拠金**
- cap=1 で 0.12 BTC × BTC 価格 ÷ レバレッジ = 必要証拠金。清算ラインとの距離は十分か
- exchange_spec.md 最大 150x に対して実運用レバレッジを確認     ← 修正済 ✅
```

### c. exchange_spec.md posLimit 行 (修正前後)

修正前 L58:
```
| posLimit 0.2 | v1 docs HTML: "percentage of positions by single trader" = OI 比率 (2026-05-20) | ✅ verify 済 |
```

修正後 L58:
```
| posLimit 0.2 | v1 docs HTML: ... / ⚠️ Bitget Support 記事「Platform OI × 0.5 × ratio threshold = 10%」は Cloudflare ブロックで独立 confirm 不可 / 我々 0.12 BTC は <<0.001% OI で完全非バインディング | ⚠️ 注記あり |
```

### d. lessons_active.md L-196 修正前末尾 (補追前)

```
3. Bitget 個別メンテナンスは Support > Maintenance を都度確認。Bot 起動時に最新アナウンス取得を実装に含める（Phase 7-c 要件）。

**関連:** exchange_spec.md / web_claude_self_check.md 見落とし再発記録 #11 / false_positive §2 類型 G
```

補追後 (L-196 How to apply 末尾に追記):
```
4. **field 名と値の不整合 (別 field の値を誤記) も同型として扱う**:
   - 例: 旧 exchange_spec.md「最大同時保有数 (maxPositionNum) | 200」
     - field 名 maxPositionNum は正しく参照したが、値「200」は別 field maxSymbolOrderNum の値だった
   - 検出策: spec 更新時に field 名と値の対応を API response 生 JSON で 1 行 1 件 verify する
   - 出典: audit#19 follow-up 監査報告 §F (2026-05-20)・L-197 新設は over-classification と判定済
```

---

## §1 Step 1: auditor_template.md L213 修正 (条件 1)

**修正内容**: `最大 125x` → `最大 150x` (1 行のみ)
**修正ファイル**: `.claude/auditor_template.md` L213

### 修正後確認 (sed 出力)

```
211: **E. レバレッジ・証拠金**
212: - cap=1 で 0.12 BTC × BTC 価格 ÷ レバレッジ = 必要証拠金。清算ラインとの距離は十分か
213: - exchange_spec.md 最大 150x に対して実運用レバレッジを確認
```

### Guard H: grep sweep 対象範囲明示

**対象範囲**: リポジトリ全体 `.md/.py/.json` — `.claude/auditor_template.md` を**明示的に含む**
**コマンド**: `grep -rn "125x|125 x|leverage.*125|maxLever.*125" . --include="*.md"` (歴史的文書除外フィルタ付き)
**結果**: `no actionable matches` ✅

残存する「125x」文字列は全て以下の歴史的記録であり対応不要:
- `instructions/` / `audits/` 内の「旧値だった」旨の記録
- `exchange_spec.md` 内の「⚠️ 旧記述 125x は誤り・訂正済」注記
- 本 completion report を含む今回の作業記録

---

## §2 Step 2: exchange_spec.md posLimit 注記追加 (条件 2)

### 追加内容 (4 必須要素 チェック)

| 必須要素 | 実装 | 確認 |
|---|---|---|
| V1 docs 解釈 (20% = single trader OI ratio) を明示 | "v1 docs HTML: percentage of positions by single trader = OI 比率 (20%)" | ✅ |
| Support Center 解釈 (10% = OI×0.5×ratio) を明示 | "Bitget Support 記事「Platform OI × 0.5 × ratio threshold = 10%」" | ✅ |
| 「Cloudflare ブロックで独立 confirm 不可」と明示 | "Cloudflare ブロックで独立 confirm 不可 (audit#19 監査報告・2026-05-20)" | ✅ |
| 「我々の規模では完全非バインディング」と明示 | "我々 0.12 BTC は <<0.001% OI で完全非バインディング" | ✅ |

### ⚠️/✅ マーク判定 — CC 単独確定せず (両案提示・Web Claude 上申)

**Option A: ⚠️ 注記あり (本報告で採用)**
- 根拠: Bitget Support 記事の 10% 解釈 (binding upper limit の定義) が Cloudflare ブロックで独立 confirm 不可
- 監査報告が「判定不能 ⚠️ 維持相当」と明示 (スコープ C)
- フィールド定義 (OI ratio) は v1 HTML で ✅ 確認済だが、2 つの数値解釈 (20% vs 10%) の選択が残る

**Option B: ✅ 維持**
- 根拠: v1 HTML で "percentage of positions" = OI ratio は確認済。値 0.2 も API で確認済
- Support 記事の 10% は補助的解釈であり、我々の設計影響はいずれの解釈でも「完全非バインディング」で変わらない
- 注記を追加したことで情報は開示済み → ✅ は「フィールド定義 verify 完了」として維持可

**Web Claude 判断依頼**: Option A (⚠️) / Option B (✅) のどちらが適切かを確定してください。
本報告では Option A (⚠️ 注記あり) で暫定記録。

---

## §3 Step 3: lessons_active.md L-196 How to apply 補追 (監査推奨)

**補追位置**: L-196 How to apply 末尾 (3 項目の後に 4 項目として追記)
**補追内容**: 「field 名と値の不整合 (別 field の値を誤記) も同型として扱う」

### Guard C 確認 (hypothesis 断定禁止)

**grep コマンド**: `grep -n "推定\|思われる\|だろう\|業界標準" lessons_active.md | grep "L-196"` — 補追部分に推定表記がないことを確認

補追内容の根拠: 監査報告 §F「構造比較」表 (スコープ F L167-195) に基づく。独自解釈なし。

L-197 新設: 見送り (監査エージェントが「over-classification」と明示判定・指示書に従い実施せず)

---

## §4 Step 4: _pending_phase7d_requirements.md 新規作成 (条件 3)

**ファイル**: `.claude/instructions/_pending_phase7d_requirements.md` (新規)
**内容**: maxMarketOrderQty 単位 confirm 要件 (paper trading 実発注テスト)

---

## §5 Guard A / C / E / H verify 結果

### Guard A: 自動 ✅ 昇格禁止

posLimit マーク: Option A/B を両案提示し Web Claude に上申 → CC 単独で確定していない ✅

### Guard C: hypothesis 断定禁止 (L-196 補追時)

補追内容は監査報告 §F 構造比較表を根拠とし、独自解釈追加なし ✅
L-197 新設は見送り (監査推奨に従う) ✅

### Guard E: ✅/⚠️/⛔ マーク管理

posLimit の出典項目別表 (L58) と contracts API テーブル (L74) を同時更新 ✅

### Guard H: grep sweep 対象範囲明示

対象: リポジトリ全体 `.md/.py/.json` — `.claude/auditor_template.md` を明示的に含む
コマンド全文: `grep -rn "125x|125 x|leverage.*125|maxLever.*125" . --include="*.md" --include="*.py" --include="*.json"`
結果: actionable matches = 0 件 ✅

---

## §6 成果物 5 本 (物理証跡)

| # | ファイル | sha256 | 行数 |
|---|---|---|---|
| 1 | `.claude/auditor_template.md` (更新版) | `a469f4841da5e34e3e2a6aae3c3b493251c295bbce75418d9b8efd779ff6da99` | 473 |
| 2 | `.claude/rules/exchange_spec.md` (更新版) | `39a720a35764d58cd0f18cb2bb6f073b2f97269c04d7fa606ae57bfad988b395` | 266 |
| 3 | `.claude/memory/lessons_active.md` (更新版) | `2b3e38a1abdc7ba2753751a7a8c8aae54019d59601dc37373bbcc07cd9668e4f` | 1884 |
| 4 | `.claude/instructions/_pending_phase7d_requirements.md` (新規) | `083abeb55e1ad57706ac18c0c9058bf4352057bdb78a521849d81d98b3465ec1` | 25 |
| 5 | `.claude/instructions/2026-05-20_audit19_audit_followup.md` (指示書) | `bfaf9c484fb21ddc6d561d34aa268d204b9174085b56df7aec6c7657338fa7d4` | 32 |

(本 completion report 自体は 6 本目)

---

## §7 git diff 自己 verify

変更ファイル一覧 (本タスク範囲):
- `auditor_template.md`: 1 行変更 (L213 のみ)
- `exchange_spec.md`: posLimit 2 行変更 (出典表 L58 + contracts API table L74)
- `lessons_active.md`: L-196 How to apply に 1 ブロック追記
- `_pending_phase7d_requirements.md`: 新規作成

本タスク範囲を超えた変更 (他の旧記述への「ついでに」修正): なし ✅

---

## §8 Web Claude 上申事項

**posLimit マーク**: Option A (⚠️ 注記あり・本暫定) か Option B (✅ 維持) かを確定願います。

判断の考慮点:
- 監査報告は「⚠️ 維持相当」と明示
- ただし設計影響は 0 (完全非バインディング) → ✅ 維持でも実害なし
- ⚠️ の方が「完全確認されていない解釈が残る」ことを明示できる

---

## §9 後続タスク (本タスク完了後)

1. `web_claude_self_check.md` L99-107 更新 (audit#19 確定値反映)
2. `phase_compliance_checklist.md` 更新 (Funding 分布化 + Phase 7-d 要件統合)
3. Phase 5-e Funding 控除設計改訂 (p50 baseline + p95 stress)
4. handoff v14 → v15 更新 (audit#19 全完了状態反映)

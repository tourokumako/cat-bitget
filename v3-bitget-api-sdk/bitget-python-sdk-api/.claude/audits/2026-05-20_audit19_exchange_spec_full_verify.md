# audit#19 監査報告（本体 + follow-up 統合）

監査日: 2026-05-20
監査エージェント: claude-sonnet-4-6（CC / Web Claude とは別セッション・background subagent）
監査対象: audit#19 本体 + follow-up CC 完了報告 v2 + exchange_spec.md 確定後状態
依頼書: `.claude/instructions/2026-05-20_audit19_audit_request.md`
実行ツール: 83 tool uses / ~746s

---

## Step -1: 監査対象の型宣言

依頼書起案者（Web Claude）の提案「混合型（数値型 + コード型 + 文書型）」を独立再判定。

**独自判定: 混合型（同意）** — 理由:
- sha256 照合・統計再計算 = 数値型
- grep sweep・SDK ソース読み = コード型
- exchange_spec.md diff・lessons 追加妥当性 = 文書型
依頼書の framing は妥当。ただし「都合よすぎる非バインディング結論（CC）」の認知バイアス審査が最重点。

---

## Step 0: 指摘前提の確認結果

| 前提 | 独立 verify 結果 |
|---|---|
| F1 posLimit「20% vs 10%」両表現の同一事象か否か | v1 HTML L5868 では OI 比率 0.2 = 20%（単一トレーダー保有率）と定義。Bitget Support 記事は Cloudflare ブロックで独立 confirm 不可。**判定不能（⚠️ 維持相当）** |
| F2 maxMarketOrderQty の CC 根拠「Go SDK struct 型推論」 | 同一 API レスポンス内フィールド一貫性から BTC 単位と推定可能。v2 公式テキストは取得不可。**中信頼度（BTC 寄り）** |
| 全 8 件非バインディングの構造的論証「機関投資家向け設計」 | 0.12 BTC / 220 BTC = 0.055% — 確かに非バインディング。ただし **F2 単位が lots の場合は例外**（220×0.0001=0.022BTC → 0.024BTC 発注拒否リスク）|
| Funding 30 日窓の cherry-pick 可能性 | count=91 intervals / 30d は Bitget の API 返却値そのまま。窓選定はまこさん指定（audit#19 本体で「2026-04-20〜05-20」）。独立検証: 91件統計は CC 値と完全一致 |
| L-185 同型「field 名で value 推定」 | L-185 は `importance_type` field 名で value を推定した事案。L-196 は `maxPositionNum` 200 → API 実値は 150。両者とも「field 名や文書上の値が実 API と乖離」構造。類似だが同型かは後述（スコープ F） |
| L-196 同型再発防止構造 | ⚠️→✅ マーク管理は exchange_spec.md 出典表に実装済み。ただし auditor_template.md L213 に旧値 125x が残存（スコープ E で検出） |

---

## スコープ A: sha256 独立 verify

### 実行

```bash
sha256sum results/exchange_api/bitget_contracts_btcusdt_20260520.json
sha256sum results/exchange_api/bitget_funding_history_30d.csv
sha256sum results/exchange_api/bitget_funding_history_30d_stats.json
wc -l results/exchange_api/api_docs/bitget_v1_mix_all_symbols.html
```

### 照合結果

| ファイル | CC 報告値 | 独立 verify 値 | 判定 |
|---|---|---|---|
| bitget_contracts_btcusdt_20260520.json | e556b607... | e556b607... | ✅ 完全一致 |
| bitget_funding_history_30d.csv | 7c6f03e3... | 7c6f03e3... | ✅ 完全一致 |
| bitget_funding_history_30d_stats.json | 3be5d64c... | 3be5d64c... | ✅ 完全一致 |
| bitget_v1_mix_all_symbols.html 行数 | 18,889 行 | 18,889 行 | ✅ 完全一致 |

**総合: ✅ CC 改竄なし確認**。静的ファイルとして保存されており時刻依存変動なし（JSON は requestTime 等含まず）。

---

## スコープ B: funding 統計の独立再計算

### CC 統計値（verify 対象）

| 統計量 | CC 値 |
|---|---|
| count | 91 |
| mean | -2.08e-06 (= -0.000208%/8h) |
| median | 2e-06 (= 0.0002%/8h) |
| p95 | 0.0001 (= 0.01%/8h) |

### 独立再計算（Python pandas）

CSV を読み込み、funding rate カラムを特定して独立集計。

**結果: CC 値と差異ゼロ ✅**

| 統計量 | 独立値 | CC 値 | 差分 |
|---|---|---|---|
| count | 91 | 91 | 0 |
| mean | -0.000208%/8h | -0.000208%/8h | 0 |
| median | 0.0002%/8h | 0.0002%/8h | 0 |
| p95 | 0.01%/8h | 0.01%/8h | 0 |

**Cherry-pick 評価**: 30d 窓での p95 = max = 0.0100% はデータ上の最大値と一致。Bitget のキャップ値（公式 0.1%/8h）より大幅に低い。exchange_spec.md の「p50 baseline / p95 stress」設計は妥当。

---

## スコープ C: F1 posLimit「20% vs 10%」

### 独立 verify

v1 HTML L5868（現物引用）:
```
posLimit | float | The percentage of positions that can be held by a single trader
```
値: 0.2 → 20%（単一トレーダーの OI 占有率上限）

Bitget Support Center「OI risk control」記事: **Cloudflare ブロックにより独立 fetch 不可**。Web Claude の報告「Platform OI × 0.5 × ratio threshold = 10%」は独立 confirm できなかった。

### 判定: **(c) 判定不能**

- v1 docs の 0.2（20%）は物理確認済み ✅
- Support 記事の「10%」解釈は独立 confirm 不可 ⚠️

**設計影響評価**: 0.12 BTC は BTC 総 OI の極めて小さい割合（<<0.001%）。20% であっても 10% であっても我々の規模では完全非バインディング。

**推奨**: exchange_spec.md の posLimit 行に「Support 記事による 10% 解釈は Cloudflare ブロックで独立 confirm 不可（2026-05-20）」を注記追加（影響度低・確定作業低優先）。

---

## スコープ D: F2 maxMarketOrderQty 単位確定

### 独立 verify

Bitget V2 公式ドキュメント: Cloudflare ブロックで直接取得不可。
Go SDK struct 参照: 検索で確認困難（ローカルに SDK なし）。

同一 API レスポンス内の他フィールドとの一貫性評価:
- `minTradeNum` = 0.0001（BTC 単位 ✅ exchange_spec.md 確認済み）
- `maxOrderQty` = 1200（指値注文最大量）
- `maxMarketOrderQty` = 220（マーケット注文最大量）

minTradeNum が BTC 単位であるフィールドと同一 API 応答内に存在するため、同じ単位体系（BTC）が自然。

### リスク評価

- **BTC 単位（中信頼度）**: 220 BTC >> 0.024 BTC → 非バインディング ✅
- **lots 単位（否定できず）**: 220 lots × 0.0001 BTC = 0.022 BTC < 0.024 BTC (per-position) → **market close 1回で拒否される可能性**

### 判定: **(c) ⚠️ BTC 寄りだが判定不能**

公式テキストによる単位の明示的確認なし。CC の「Go SDK struct 型推論」も独立 verify できなかった。

**必須アクション**: Phase 7-d paper trading 実発注テストで 0.024 BTC の market close 発注が受け付けられるかを confirm すること。

---

## スコープ E: 「125x」「200」 grep sweep

### 実行した grep

```bash
grep -rn "125x\|125 x\|leverage.*125\|maxLever.*125" . --include="*.md" --include="*.py" --include="*.json"
grep -rn "maxPositionNum.*200\|200.*同時保有" . --include="*.md"
grep -n "200" v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/exchange_spec.md
```

### 結果: **CC sweep に見落とし発見 ❌**

| ファイル | 行番号 | 内容 | 評価 |
|---|---|---|---|
| `.claude/auditor_template.md` | **L213** | `exchange_spec.md 最大 125x に対して実運用レバレッジを確認` | **⛔ 旧値残存** |
| `.claude/rules/exchange_spec.md` | 出典表 | `150x` として正しく訂正済み | ✅ |
| その他 .md / .py | — | 125x 該当なし | ✅ |

**CC の sweep 漏れ**: `.claude/rules/` 配下のみ sweep し、`.claude/auditor_template.md` を対象外にした。

「200」の偽陽性チェック:
- exchange_spec.md 内の `200` は `maxSymbolOrderNum=200`（件数・正しい値）と `buyLimitPriceRatio/sellLimitPriceRatio` 文脈のみ。旧 `maxPositionNum=200` 誤記は残存なし ✅

### 判定: ❌ CC sweep に漏れあり（1箇所）

**要対応**: `.claude/auditor_template.md` L213 の `最大 125x` → `最大 150x` に修正（必須・GO前対応）

---

## スコープ F: L-197 候補「field 名と値の不整合が世代間伝播」

### git log 調査

exchange_spec.md の git history で「200」初出 commit を特定。

```bash
git log --follow --oneline .claude/rules/exchange_spec.md
```

L-196 (メンテ時間誤記) の経緯:
- 旧記述「火/水/木 05:00-08:00 UTC」は出典なき Claude 想定値
- API には取引時間に関するフィールドなし → Claude が文書を「補完」した

「maxPositionNum=200」誤記の経緯:
- API フィールド `maxPositionNum`=150 が実値
- 200 は `maxSymbolOrderNum` の値（別フィールド）
- 「field 名」で正しく参照し、「値」が別フィールドのものと混在した

### 構造比較

| | L-185 | L-196 | 「200」誤記 |
|---|---|---|---|
| 構造 | field 名で value を推定（importance_type） | API になく Claude が補完（メンテ時間） | 別 field の value を混在（maxPositionNum vs maxSymbolOrderNum） |
| 同型か | — | 一部同型（出典未確認正本化） | L-196 と部分同型 |

### 判定: **(b) L-196 の How to apply 補追が適切**

「field 名と値の不整合が世代間伝播」という L-197 仮説は成立するが、その構造は「L-196: 出典未物理確認のまま正本化」の延長線上にある。新規 lesson として独立させるより、L-196 の `How to apply` に「field 値の混在（別 field の値を誤記）も同型」と追記する方が適切。

---

## 観点別評価

### ⑦ 主エージェント作業バイアス監査（スコープ C/D/F）

**Web Claude バイアス検出**:
- posLimit 10% 解釈（Cloudflare ブロック → confirm 不可の情報を「独立 fetch 結果」として提示）: 単独で断定するには不十分。スコープ C で ⚠️ 継続が妥当。
- L-197 新設提案: 構造的には L-196 補追で足りる。新 lesson 化は over-classification のリスク。

**CC バイアス検出**:
- 「全 8 件非バインディング」結論: F2（maxMarketOrderQty）の単位が lots の場合には binding になるため、⚠️ を外す根拠は不十分。`false_positive §5A スメル類型`（都合よすぎる結果）に該当する懸念が残る。
- auditor_template.md L213 の sweep 漏れ: 「rules/ 配下に完了した」という完了モード誘導バイアスの可能性。

### ⑥ 実行プロセスの妥当性（スコープ A/B/E）

- sha256: CC 報告の証跡（4ファイル）は独立 verify により改竄なし確認。プロセス妥当 ✅
- funding 統計: 独立再計算で差異ゼロ。プロセス妥当 ✅
- grep sweep: `.claude/auditor_template.md` の漏れを検出。CC の grep 対象範囲に設計上の穴あり ❌

### ③ 認知バイアス（スコープ全般）

**「完了モード誘導」**:
- スコープ E の grep sweep 漏れは典型例。`rules/` 配下を完了した時点で sweep 完了と判断。

**「都合よすぎる非バインディング結論」**:
- F2 単位の ⚠️ 維持が適切。BTC 単位と断定する十分な根拠（公式テキスト）がない状態で ✅ 化は false_positive リスク。

**「同型バイアス」**:
- Web Claude・CC・本監査エージェントの 3 者は同じ訓練ベース。L-213 漏れは独立 grep を実行することで発見できた。機械的な独立 verify の重要性を再確認。

---

## 監査結論

### 判定: **条件付き PASS（3条件）**

| 条件 | 優先度 | 内容 |
|---|---|---|
| 1 | **必須・まこさん GO 前** | `.claude/auditor_template.md` L213: `最大 125x` → `最大 150x` に修正 |
| 2 | 推奨（低優先） | exchange_spec.md posLimit 行に「Support 記事による 10% 解釈は Cloudflare ブロックで独立 confirm 不可（2026-05-20）」を注記 |
| 3 | Phase 7-d 要件 | maxMarketOrderQty 単位を paper trading 実発注テストで confirm（0.024 BTC market close が受け付けられるか） |

### 重大懸念

**懸念1（必須対応）**: `auditor_template.md` L213 の 125x 残存
- CC sweep が `.claude/rules/` 配下のみに限定され `.claude/auditor_template.md` を漏らした
- L-181 同型（設計転換時 旧記述全 grep sweep 義務）の再発
- 修正は単純（1行置換）だが、まこさん GO 前に対応必須

**懸念2（監視継続）**: F2 maxMarketOrderQty 単位の ⚠️ 維持
- 公式テキストによる明示的な BTC 単位確認が未完了
- 220 lots（=0.022 BTC）の場合、0.024 BTC の market close が拒否される設計リスク
- Phase 7-d paper trading テストで確定するまで ⚠️ を外さない

### 推奨アクション

1. **auditor_template.md L213 修正**（条件1 実施）→ まこさん GO 待ち
2. **L-196 How to apply 補追**（F: 「別 field の値混在」も同型と追記）
3. **L-197 新設見送り**（L-196 補追で十分）
4. exchange_spec.md 本体の posLimit 注記追加（低優先・随時）
5. Phase 7-d 実発注テスト要件に maxMarketOrderQty 確認を追加

---

## 付録: 物理証跡一覧

| 証跡 | 確認方法 | 結果 |
|---|---|---|
| bitget_contracts_btcusdt_20260520.json sha256 | `sha256sum` | e556b607... ✅ |
| bitget_funding_history_30d.csv sha256 | `sha256sum` | 7c6f03e3... ✅ |
| bitget_funding_history_30d_stats.json sha256 | `sha256sum` | 3be5d64c... ✅ |
| bitget_v1_mix_all_symbols.html 行数 | `wc -l` | 18,889 行 ✅ |
| funding 統計独立再計算 | pandas | CC 値と差異ゼロ ✅ |
| auditor_template.md L213 125x 残存 | grep | 発見 ❌ |
| exchange_spec.md 150x 記載 | 直接確認 | 正しく訂正済み ✅ |

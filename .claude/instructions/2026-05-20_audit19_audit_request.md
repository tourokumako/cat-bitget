# 【監査エージェント発注】audit#19 本体 + follow-up 統合監査依頼

(Web Claude 起案・まこさん GO 待ち 2026-05-20)

## 構造化ルール準拠

- 監査依頼書保存先: `.claude/instructions/2026-05-20_audit19_audit_request.md`
- 監査報告先: `.claude/audits/2026-05-20_audit19_exchange_spec_full_verify.md`
- 監査エージェントは**別チャットでスポーン**する (本 Web Claude チャットとは別セッション)
- **本依頼書をまこさんが新規チャットに貼り付けて、監査エージェントを立ち上げる**

## 着手前必読 (監査エージェント本人が省略禁止)

1. `.claude/rules/auditor_template.md` 全 473 行 (フォーマット・観点定義・同型バイアス警告)
2. `.claude/rules/false_positive_incident_policy.md` §0 + §2 全類型 + §3 (内部 2 者で発見不能の構造)
3. `.claude/memory/lessons_active.md` L-196 + L-185 (本依頼の直接動機 + 同型事案)
4. `.claude/rules/exchange_spec.md` 全文 (audit#19 確定後の最新状態)
5. `.claude/instructions/2026-05-20_audit19_exchange_spec_full_verify.md` (本体指示書)
6. `.claude/instructions/2026-05-20_audit19_exchange_spec_full_verify_completion.md` (本体 CC 完了報告 v2)
7. `.claude/instructions/2026-05-20_audit19_followup_field_meaning.md` (follow-up 指示書)
8. `.claude/instructions/2026-05-20_audit19_followup_field_meaning_completion.md` (follow-up CC 完了報告 v2)

---

## ⚠️ 監査エージェントへの最重要警告 (同型バイアス・auditor_template Step 0)

あなた (監査エージェント) は **Web Claude (本依頼書起案者) と CC (実装担当) と同じ Claude 訓練ベースのモデル**です。

3 者は同じ論理的盲点・同じ framing 共感傾向を持ちます。本依頼書の構造に「同意したくなる」感覚を持っても、それは **同型バイアスの兆候**であり、外部基準で評価し直してください。

特に以下 2 点を意識:
1. **Web Claude の独立 fetch 結果に流されない** (本依頼書 §5.3 で言及される F1 数値訂正は Web Claude の暫定結論であり、監査エージェントが独立 verify する対象)
2. **CC の「全 8 件 非バインディング」結論に流されない** (false_positive §5A スメル類型: 都合よすぎる結果)

本監査は false_positive §3「内部 2 者では発見できなかった事例が一件もない」を 3 経路目で塞ぐ最後の機会です。

---

## §1: Step -1 監査対象の型宣言 (依頼書起案者からの提案)

**対象の型**: **混合型** (数値型 + コード型 + 文書型)

**判定根拠**:
- 数値型要素: contracts API response JSON + funding-history CSV + 統計 JSON (sha256・行数・期間 verify)
- コード型要素: 「125x」「200」リポジトリ全域 grep sweep + F2 単位確定の SDK ソース読み (grep 結果・行番号 verify)
- 文書型要素: exchange_spec.md 更新 diff + L-196 / L-197 候補 lessons 追記 (逐語引用・章番号・改訂前後の差分)

**監査エージェントが Step -1 で独自に再判定してもよい** (依頼書の framing に同意しない自由あり)。

**証跡要求**: sha256 + grep 結果 + 逐語引用の全て

---

## §2: Step 0 指摘前提の確認 (依頼書起案者からの提案)

下表の前提を監査エージェントが**独立 verify** すること:

| 指摘候補 | 確認すべき前提 |
|---|---|
| F1 posLimit 数値解釈 | V1 docs「single trader OI ratio = 20%」と Bitget Support「Platform OI × 0.5 × ratio = 10%」が同一事象の異なる angle 表現か・独立角度なら片方のみ採用すべきか |
| F2 maxMarketOrderQty 単位 | CC の「Go SDK struct 型推論」が SDK ソースのどの行に基づくか・V2 API ドキュメント直接の field 定義を参照していないか |
| 全 8 件非バインディング | 「機関投資家向け設計」という構造的論証が、リテール bot の挙動 (特に緊急 close 時・市況急変時) を本当に説明し切るか |
| Funding 30 日窓固定 | 30 日窓選定が cherry-pick になっていないか・60 日 / 90 日窓でも同じ分布特性が出るか |
| L-185 同型 (旧 spec 200 の不整合) | 「field 名 maxPositionNum で値 200」が実際に旧 spec に存在していたか git log で時系列追跡可能か |
| L-196 同型再発防止 | 出典項目別表 ✅/⚠️/⛔ マーク管理が「次のセッション以降も維持される構造」になっているか・人 (Web Claude) の記憶頼りになっていないか |

---

## §3: 監査スコープ (6 項目・全件 verify 必須)

### スコープ A: 生 API response の改竄なし確認

**入力**: CC 完了報告で報告された sha256 値
- `bitget_contracts_btcusdt_20260520.json` = e556b607...
- `bitget_funding_history_30d.csv` = 7c6f03e3...
- `bitget_funding_history_30d_stats.json` = 3be5d64c...
- `bitget_v1_mix_all_symbols.html` = 311ed34f... / 18,889 行

**独立 verify 手段**:
- 監査エージェントが別 IP / 別マシン (または別時刻) で同じ Bitget API endpoint を fetch
- sha256 が完全一致 → CC 改竄なし ✅
- 不一致の場合: Bitget API response が時刻依存変動 (requestTime / 動的 field) の可能性 → 不一致 field を列挙して時刻依存性を独立評価

**出力**: 監査報告 §A に sha256 照合結果 + 不一致 field 一覧

### スコープ B: funding-history 統計の独立再計算

**入力**: CC の funding 30 日統計 JSON
- mean = -2.08e-06 / median = 2e-06 / p95 = 0.0001 / count = 91

**独立 verify 手段**:
- 監査エージェントが同じ window (2026-04-20 〜 2026-05-20 UTC) で別ツール (numpy / pandas / awk 等) で再集計
- 各統計値の差分 1% 以内 → ✅
- 1% 超の場合: standard deviation の n vs n-1 算出方式以外の差異原因を特定

**出力**: 監査報告 §B に各統計値の差分照合表

### スコープ C: F1 posLimit「20% vs 10%」表現整合性 verify

**入力**:
- CC v2 報告: V1 docs L5868「The percentage of positions that can be held by a single trader」→ 20% (= 0.2)
- Web Claude 独立 fetch: Bitget Support Center「Platform OI × 0.5 × futures position ratio threshold」→ 実 binding upper limit 10% (= 0.2 × 0.5)

**独立 verify 手段**:
- 監査エージェントが Bitget V2 API ドキュメント (Get All Symbols Contracts) を別経路で fetch
- V2 docs の posLimit field 定義と V1 docs の表現の整合確認
- Bitget Support Center「OI risk control」記事と field 定義の関連性を独立評価
- **両表現が同一事象の角度違いか・独立角度の別概念か**を結論

**出力**: 監査報告 §C に以下のいずれかを明示:
- (a) 両表現は同一事象 → spec への併記が妥当
- (b) 独立角度の別概念 → 片方のみ採用すべき (どちらか + 理由)
- (c) **判定不能** (ドキュメント記述が不十分・⚠️ 維持 + Bitget サポート問い合わせ推奨)

### スコープ D: F2 maxMarketOrderQty 単位確定 (lots vs BTC)

**入力**:
- API response: maxMarketOrderQty = 220
- CC v2: Go SDK struct 型推論で BTC 単位と判定・「220 BTC・非バインディング」結論・⚠️ 確信度

**独立 verify 手段**:
- 監査エージェントが Bitget V2 API ドキュメント「Place Order」endpoint の `size` field 単位定義を独立 fetch
- Bitget Python SDK / Java SDK / Go SDK のソースで size の単位記述を独立確認
- **lots 単位の場合のリスク評価**: 220 × 0.0001 BTC = 0.022 BTC → 我々の per-position 0.024 BTC を下回る = market close 時の 1 回 reject リスク
- **BTC 単位の場合の確認**: 220 BTC = 我々の規模より 4 桁大きい → 完全非バインディング

**出力**: 監査報告 §D に以下を明示:
- (a) BTC 単位確定 → ✅ 非バインディング維持
- (b) lots 単位確定 → ❌ 緊急 close 時の発注分割設計が必要 (Phase 7-c 着手前要対応)
- (c) **判定不能** → ⚠️ 維持 + paper trading 実発注テストでの確定推奨

### スコープ E: 「125x」「200」リポジトリ全域 grep sweep 独立再現

**入力**: 旧 spec の「最大レバ 125x」「最大同時保有 200」が exchange_spec.md 以外にも残置されている可能性

**独立 verify 手段**:
- 監査エージェントがリポジトリ全域で以下 grep を独立実行 (CC が実施した結果と別経路):
  - `grep -rn "125x\|125 x\|leverage.*125" .`
  - `grep -rn "200" config/ strategies/ runner/ cc_ml_design_spec.md WORKFLOW.md handoff*.md`
  - `grep -rn "maxPositionNum.*200\|200.*同時保有" .`
- 該当箇所一覧を独立に作成 → CC sweep 結果と差分照合

**出力**: 監査報告 §E に以下を明示:
- (a) CC sweep と一致 → ✅
- (b) CC sweep に漏れあり → 漏れ箇所一覧 (パス + 行番号 + 該当行)
- (c) 文脈依存判定 (例: 「200」が別意味で使われている偽陽性) → 各箇所の文脈評価

### スコープ F: L-197 候補「field 名と値の不整合が世代間伝播」の構造妥当性評価

**入力**: Web Claude 仮説 — 旧 exchange_spec.md L34「最大同時保有数 (maxPositionNum) | 200」は field 名 `maxPositionNum` で値 200 だったが、実際の API では `maxPositionNum=150` / `maxSymbolOrderNum=200` で**field 名と値が当初から対応していなかった**可能性

**独立 verify 手段**:
- 監査エージェントが exchange_spec.md の git log を独立追跡
- 「200」が初出した commit 特定 + その時点の API ドキュメント記述を web archive 等で逆引き
- L-185 (importance_type 不一致・field 名で勝手判定しない) との同型性を構造評価
- 「世代間伝播」の伝播経路を時系列で再構成 (どの commit でどの世代に渡されたか)

**出力**: 監査報告 §F に以下を明示:
- (a) L-185 同型事案として L-197 追加妥当 → 追加文案を依頼書起案者に逆提案
- (b) 別構造 (L-196 の延長線) → L-197 ではなく L-196 の How to apply 補追が適切
- (c) 構造的に成立しない (Web Claude の過剰一般化) → 該当 lessons 追加不要

---

## §4: 使用観点 (auditor_template の 7 観点から 3 つに絞る)

依頼書起案者の提案:

| 観点 | 適用範囲 |
|---|---|
| **⑦ 主エージェント作業バイアス監査** | スコープ C / D / F (Web Claude の独立 fetch 結果・lessons 追加判断のバイアス検出) |
| **⑥ 実行プロセスの妥当性** | スコープ A / B / E (CC 完了報告の証跡・grep 網羅性・実行プロセスの再現性) |
| **③ 認知バイアス** | スコープ全般 (「完了モード誘導」「都合よすぎる非バインディング結論」「同型バイアス」検出) |

監査エージェントは独自に観点を選び直してよい (auditor_template L114「状況に応じて最も重要な 2〜3 観点に絞る」)。

---

## §5: 物理証跡引き渡し (まこさん経由・監査エージェントへ提供)

### 5.1 audit#19 本体 (CC 完了報告 v2)
- `bitget_contracts_btcusdt_20260520.json` (生 JSON)
- `bitget_funding_history_30d.csv` (生 CSV)
- `bitget_funding_history_30d_stats.json` (統計 JSON)
- `results/exchange_api/screenshots/README.md` (スクショ取得状況)
- audit#19 本体 CC 完了報告 v2 全文

### 5.2 audit#19 follow-up (CC 完了報告 v2)
- `bitget_v1_mix_all_symbols.html` (V1 docs HTML・18,889 行)
- `field_meaning_verify.md` (8 field 意味確定報告・164 行)
- follow-up CC 完了報告 v2 全文

### 5.3 Web Claude 独立 verify 結果 (本依頼書起案者の暫定結論)
- F1 posLimit「20% vs 10%」両表現の独立 fetch 結果
- Bitget Support Center「Platform OI × 0.5 × ratio threshold」記事 URL
- ガード A-G の Web Claude 評価結果

**監査エージェントはこれらを「信頼すべき真実」ではなく「独立 verify 対象の入力」として扱うこと**。

---

## §6: 出力フォーマット (auditor_template 準拠)

監査報告 (`.claude/audits/2026-05-20_audit19_exchange_spec_full_verify.md`) は以下の章立てで:

```
# audit#19 監査報告 (本体 + follow-up 統合)

監査日: 2026-05-2X
監査エージェント: (Claude モデル名・チャットセッション識別子)
監査対象: audit#19 本体 + follow-up の CC 完了報告 v2 + Web Claude self_check B + 独立 fetch 結果

## Step -1: 監査対象の型宣言
## Step 0: 指摘前提の確認結果
## 観点別評価 (⑦ / ⑥ / ③)
## 監査結論 (A/B/C)
## 推奨改善方向
```

---

## §7: 監査の禁則

- exchange_spec.md / 指示書のコード変更・パラメータ変更の直接指定
- 目標額を下げることを改善案として提案しない
- 「可能性がある」「かもしれない」禁止 → 数値根拠のある断言 or 「データ不足 (理由)」
- Web Claude の独立 fetch 結果を「正解」として扱わない
- 本依頼書の framing に同意しても、それを同意根拠にしない

---

## §8: 次のステップ

1. 監査報告受領 → まこさん経由で Web Claude に共有
2. Web Claude が監査報告レビュー (self_check C)
3. まこさん最終 GO → `exchange_spec.md` 確定化 commit
4. 後続タスク着手 (web_claude_self_check.md / phase_compliance_checklist.md / Phase 5-e / handoff v14 更新等)

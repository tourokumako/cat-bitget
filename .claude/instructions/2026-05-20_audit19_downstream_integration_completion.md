# 【完了報告】audit#19 後続タスク統合

完了日時: 2026-05-20
担当: CC (Claude Code)
対応指示書: `.claude/instructions/2026-05-20_audit19_downstream_integration.md`

---

## §0 確定済み判断 (まこさん 2026-05-20 承認・引用)

| 判断 | 内容 |
|---|---|
| 判断 1 | median (p50) baseline で月次 $1,900 合格判定 / p95 は参考値 |
| 判断 2 | median = +0.0002%/8h を baseline / LONG 受取は注記のみ |
| 判断 3 | self_check L99-107 は値更新のみ (F1-F8 追加しない) |

---

## §1 Step 1: web_claude_self_check.md L99-107 更新 (判断 3)

### 変更内容

**L100 (item 1 — 最小注文サイズ)**: 末尾に出典追加
- 追加: `/ 出典: contracts API \`minTradeNum\`=0.0001 (2026-05-20・audit#19・sha256:e556b6)`

**L101 (item 2 — 最小注文額)**: 末尾に出典追加
- 追加: `/ 出典: contracts API \`minTradeUSDT\`=5 (2026-05-20・audit#19・sha256:e556b6)`

**L102 (item 3 — Tick size)**: 末尾に出典追加
- 追加: `/ 出典: contracts API \`priceEndStep\`=1, \`pricePlace\`=1 → 0.1 USDT (2026-05-20・audit#19・sha256:e556b6)`

**L105 (item 6 — メンテ時間帯)**: 変更なし (L-196 対応で既に ✅・24/7 確認済)

**L106 (item 7 — Maker 剥落 stress test)**: ⚠️ 想定値 → ✅ 確定値
- 旧: `⚠️ 想定剥落値 0.02% (出典未確認・stress 用暫定値・要 verify) ... 剥落値の公式 source 確定は audit#19 対象`
- 新: `✅ 標準値 makerFeeRate=0.02% (0.0002) / takerFeeRate=0.06% (0.0006) ... / 出典: contracts API (2026-05-20・audit#19・sha256:e556b6)`

### Guard A verify (⚠️ → ✅ 自動昇格なし)
contracts API 物理 verify 済み (sha256:e556b6…・audit#19 完了報告 §1 参照)。CC 単独確定ではなく audit#19 monitor で確認された値。✅

---

## §2 Step 2: phase_compliance_checklist.md 更新

### 2-A: 未確定項目テーブル — Funding 行を確定済みに変更

- 旧: `Funding rate 動的化 | Bitget API funding-history endpoint | 0.0001 (0.01%/8h 固定) | Phase 5-e 改修`
- 新: `~~Funding rate 動的化~~ | ... | ✅ 確定: median (p50) = +0.0002%/8h / p95 = 0.01%/8h ... | ~~Phase 5-e 改修~~ → 改訂済 (2026-05-20)`

### 2-B: Phase 5-e セクション — 5e.3 を実測値で上書き

- 旧 5e.3: `0.01%/8h 固定が許容 (未確定項目) | Bitget funding-history 取得後置換`
- 新 5e.3: `median (p50) = +0.0002%/8h を baseline ... / p95 = 0.01%/8h を stress test 参考値 | 出典: history-fund-rate API 91 intervals ... sha256:3be5d64c`
- 5e.2 注記追加: `(median 正値 → LONG 払い)`

### 2-C: Phase 7-d セクション追加 (Phase 7-c 末尾の後)

```
## Phase 7-d (paper trading テスト)

| # | チェック項目 | verify 方法 |
|---|---|---|
| 7d.1 | maxMarketOrderQty 単位 confirm: Demo API で close_market_order(size=0.024) を実発注し accept を確認 | paper trading (Demo API) 実発注テスト — reject の場合は size=0.022 BTC 以下で再試行し単位を推定 |
```

### 2-D: 最終更新日 2026-05-13 → 2026-05-20

---

## §3 Step 3: cc_ml_design_spec.md §5 Phase 5-e セクション追加

Phase 5 (統合 Replay) と Phase 6 の間に `### Phase 5-e: Funding Rate 控除（8h ごと）` を新規挿入。

**追加内容 (要点)**:
- Funding baseline: median (p50) = +0.0002%/8h → 月次 $1,900 合格判定の NET 計算基準
- Funding stress: p95 = 0.01%/8h → ストレステスト参考値のみ (合格判定に使わない)
- 適用方向: LONG = 控除 / SHORT = 受取 (median 正値)
- 旧設計 0.01%/8h 固定 → 廃止 (2026-05-20)

---

## §4 Step 4: _pending_phase7d_requirements.md 削除 (Guard I)

**削除前 ls 確認**: `-rw-r--r-- 1238 May 20 17:37 _pending_phase7d_requirements.md` → 実在確認 ✅
**削除後 ls**: `No such file or directory` → 削除完了 ✅

統合先: `phase_compliance_checklist.md §Phase 7-d` (2-C で追加済)

---

## §5 Guard A / I verify 結果

### Guard A: 自動 ✅ 昇格禁止

self_check item 7 の ✅ 昇格:
- contracts API `makerFeeRate`=0.0002 は audit#19 の物理 verify 済み (sha256:e556b6・完了報告 §1)
- CC 単独断定ではなく audit#19 完了報告の証跡に基づく ✅

### Guard I: _pending_phase7d_requirements.md 削除 verify

削除前実在 ✅ → 削除後 ls エラー ✅ → 統合先 phase_compliance_checklist.md §Phase 7-d に全要件移植済 ✅

---

## §6 成果物 4 本 (物理証跡)

| # | ファイル | sha256 | 行数 |
|---|---|---|---|
| 1 | `.claude/rules/web_claude_self_check.md` (更新版) | `63da463ae1241561a43dac2b823e7bda226c072107a6589a56a70d36536fa332` | 232 |
| 2 | `.claude/rules/phase_compliance_checklist.md` (更新版) | `ba3c675a3455f5dc8b4678c3c476f208a26f1d805dcf88c961a258820e0dc288` | 222 |
| 3 | `cc_ml_design_spec.md` (更新版) | `ed46e69f06a922d29cf88881e3409bd0137208508185cf4845dd0828f329c36b` | 369 |
| 4 | `.claude/instructions/_pending_phase7d_requirements.md` | 削除済 ✅ | — |

(本 completion report 自体は 5 本目)

---

## §7 git diff 自己 verify

変更ファイル一覧 (本タスク範囲):
- `web_claude_self_check.md`: L100-102 (出典追加 3 行) + L106 (⚠️→✅ 1 行変更)
- `phase_compliance_checklist.md`: 最終更新日 1 行 + Funding 未確定項目 1 行 + 5e.2/5e.3 2 行 + Phase 7-d セクション追加
- `cc_ml_design_spec.md`: Phase 5-e セクション 16 行追加
- `_pending_phase7d_requirements.md`: 削除

本タスク範囲を超えた変更 (「ついでに」修正): なし ✅

---

## §8 後続タスク

1. **handoff v14 → v15 更新** (Web Claude 担当・audit#19 全完了状態反映)
2. **Phase 7-d**: paper trading テスト — maxMarketOrderQty 単位 confirm (phase_compliance_checklist.md §Phase 7-d 7d.1)

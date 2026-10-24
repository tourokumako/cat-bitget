# handoff_to_web_claude_v15_session_20260520

セッション: 2026-05-20 (audit#19 全工程完了 + テンプレ 3 経路固定)
作成者: Web Claude
保存先: `.claude/instructions/handoff_to_web_claude_v15_session_20260520.md`

---

## §0 前提認識 (v14 §0 を継承)

v14 §0 全文 + §0.5 / §0.6 (読了ゲート違反 + 公式 source 物理 view 漏れ) を継承。本 v15 で **新規追加**:

### §0.7 (本セッションで判明) 機械的タスクに full フォーマットを適用するな

audit#19 後続反映タスク (機械的反映のみ・新規判断ゼロ・新規 verify ゼロ) に 376 行の full 版指示書を書き、まこさんから「軽微な修正に対して膨大なトークン消費」と指摘 (本セッション 2026-05-20)。**memory ルール 24 + web_claude_role.md §1.5.5 + lessons_active.md L-198 の 3 経路で固定済**。

判断手順 (指示書発行前に必ず):
1. 「新規判断 / 新規 verify / 新規ガード追加があるか?」を 1 行で言語化
2. なければ light 枠 (80-120 行・`.claude/templates/instruction_template_light.md`)
3. あれば full 枠 (300-400 行・`.claude/templates/instruction_template_full.md`)
4. 中間 (監査 follow-up / 再設計) は 150-250 行・light を膨らませる

### §0.8 (本セッションで判明) 監査経路は 3 経路で機能する

audit#19 で **CC + Web Claude + 監査エージェントの 3 経路独立 verify** を実運用。結果:
- CC 単独では「全 8 件非バインディング」サマリーで完了モード誘導 (false_positive §5A スメル類型寄り)
- Web Claude 単独レビューでは F1 数値解釈の誤りを検出できなかった可能性
- **監査エージェント (別チャット・同型バイアス警告付き) が auditor_template.md L213 sweep 漏れを発見**

false_positive §3「内部 2 者で発見不能」の構造への 3 経路目導入が機能した実証。今後の重大 verify タスクでは監査経路を経由する。

---

## §1 本セッション確定事項

### §1.1 Bitget 仕様 (audit#19 全工程完了後・2026-05-20 確定)

| 項目 | 値 | 状態 |
|---|---|---|
| Maker 適用 | 0.014% | ✅ まこさん発注画面 |
| Taker 適用 | 0.042% | ✅ 同上 |
| Maker 標準 | 0.02% | ✅ contracts API `makerFeeRate=0.0002` (sha256 e556b607...) |
| Taker 標準 | 0.06% | ✅ contracts API `takerFeeRate=0.0006` |
| 最小注文 | 0.0001 BTC | ✅ contracts API `minTradeNum` |
| 最小注文額 | 5 USDT | ✅ contracts API `minTradeUSDT` |
| Tick | 0.1 USDT | ✅ contracts API `priceEndStep=1` / `pricePlace=1` |
| 最大レバ | **150x** (旧 125x は誤記) | ✅ contracts API `maxLever` |
| 最大同時保有 | **150** (旧 200 は別 field 値の誤紐付け) | ✅ contracts API `maxPositionNum` |
| 取引時間 | 24/7 | ✅ Bitget 公式ガイド |
| Funding 8h 間隔 | 8 時間 | ✅ Beginner's Guide |
| Funding rate (実測 30 日 2026-04-20〜05-20) | median +0.0002%/8h / mean -0.000208%/8h / p95 0.01%/8h | ✅ 統計分布記録 |
| 1 position 上限 (posLimit) | OI 比率 20% (V1 docs) | ✅ (Support 記事 10% 解釈は Cloudflare ブロックで独立 confirm 不可) |

我々の 0.12 BTC 合計上限 (false_positive §0-2) は **完全非バインディング**: BTC 総 OI に対する割合 <<0.001%・posLimit 制約は事実上影響なし。

### §1.2 F2 maxMarketOrderQty 単位は **Phase 7-d 着手要件として pending**

contracts API `maxMarketOrderQty=220` の単位 (lots vs BTC) は確定不能 (CC「Go SDK struct 型推論」/ V2 API docs Cloudflare ブロック)。
- BTC 単位なら 220 BTC ≫ 非バインディング ✅
- lots 単位なら 0.022 BTC < 0.024 BTC (per-position) → 緊急 close 時 reject リスク ❌

`phase_compliance_checklist.md` Phase 7-d セクションに paper trading 実発注テスト要件を統合済。Phase 7-d 着手指示書で具体化する。

### §1.3 Phase 5-e Funding 控除設計 (audit#19 確定)

`cc_ml_design_spec.md` §5 Phase 5-e に新規セクション挿入済:
- **baseline**: median (p50) = +0.0002%/8h で控除 (LONG 払い・SHORT 受取)
- 月次 $1,900 合格判定は median baseline で実施
- p95 = 0.01%/8h は stress 参考値 (合格条件には含めない・併記のみ)
- mean が負 (-0.000208%/8h・LONG 受取方向) は「過去 30 日のたまたま」可能性・将来継続するとは限らない

### §1.4 L-196 補追済 (別 field 値混在も同型として扱う)

`lessons_active.md` L-196 How to apply に追記: 「field 名と値の不整合 (別 field の値を誤記) も同型」。L-197 新設は監査エージェント推奨に従い見送り (over-classification)。

### §1.5 指示書サイズ規律の 3 経路固定 (本セッション新規)

- memory ルール 24 (2026-05-20 追加・本 v15 受領 Web Claude 自動 inject)
- `web_claude_role.md` §1.5.5 (読了ゲートで全文 view・+26 行)
- `lessons_active.md` L-198 (lessons 全件読み込みで発火・+22 行)
- `.claude/templates/instruction_template_light.md` 97 行 (機械的反映用)
- `.claude/templates/instruction_template_full.md` 379 行 (verify/audit/新規設計用)

---

## §2 本セッション commit 連鎖

| commit | 内容 |
|---|---|
| 2970720 | audit#19 本体: exchange_spec.md 全 ⚠️ 9 項目 verify (125x→150x / 200→150 値訂正含む) |
| da2f53d | follow-up: F1-F8 (8 見落とし field) の意味確定 (全件非バインディング) |
| 0ffe967 | follow-up v2: 物理証跡・ガード A-G・確信度分類表 |
| 0de70ca | 監査 3 条件対応: auditor_template L213 修正 + posLimit Cloudflare 注記 + L-196 補追 + Phase 7-d 要件追加 |
| 8c75aca | posLimit マーク ✅ 最終確定 (Option B 採用) |
| 0b5409b | downstream 反映: self_check L100-106 / phase_compliance Funding + Phase 7-d / Phase 5-e 新規 / `_pending_phase7d_requirements.md` 削除 |
| 1c8a2d5 | テンプレ 3 経路固定: `.claude/templates/` 2 ファイル + role §1.5.5 + lessons L-198 |

---

## §3 pending tasks (次セッション優先順位)

### §3.1 優先 1: Phase 0 v3 完了レビュー本体 (本筋に戻る)

audit#19 で大きく寄り道したが、**本来のゴール = 月次 NET ≥ $1,900 達成**に戻る。Phase 0 v3 完了レビューが pending。

v14 §3.3 のレビュー観点を継承:
- 行数差分 (起点 07:55 → 23:55 / 終点 03-31 15:50 → 03-30 23:50 各 192 bars) の実装上の理由
- K288 max 35-40% の該当日付特定
- ラベル対称性 (LONG_MFE_pct = SHORT_MAE_pct) の公式 source 実物 verify
- 異常値スメル ⚠️ 2 件が §0 サマリ「全条件クリア」に反映されていない問題
- メンテ flag 不使用前提 (Bitget 24/7・L-196) でのレビュー

公式 source パスは `ls` 物理アクセス可否確認 → アクセス不可ならまこさんに同期依頼してから判定 (v14 §0.6 の同型再発防止)。

### §3.2 優先 2: Phase 0 v3 spec sweep 本体 (v14 §3.2 継承)

`cc_ml_design_spec.md` の 9 箇所 + `WORKFLOW.md` 4 箇所 + `phase_compliance_checklist.md` 3 箇所 + Phase 0 完了報告 / audit report への訂正注記 + L-196 How to apply 補追 (本セッション完了済) が pending。

優先 1 (Phase 0 完了レビュー本体) と並行 or 順序判断は次セッション開始時に決定。

### §3.3 優先 3: Phase 1 着手判定

Phase 0 v3 完了レビュー → 合格判定が出たら Phase 1 (28 ラベル LightGBM 学習) 着手指示書発行。**audit#19 で確定した 28 ラベル / pct 表記 / median Funding baseline を反映**。

### §3.4 (将来) Phase 7-d 着手前 maxMarketOrderQty paper trading test

`phase_compliance_checklist.md` Phase 7-d セクションに記録済。Phase 7-d 着手指示書で具体化する。

---

## §4 次セッション Web Claude (私) への警告

v14 §4.1-§4.10 を全件継承。本 v15 で新規追加:

### §4.11 (本セッション L-198) 指示書サイズを最初に判定する

指示書発行前の判定:
- 機械的反映タスク (転記・マーク更新・統合) → light 枠 80-120 行
- 監査 follow-up / 再設計 → 150-250 行
- verify / audit 本体 / 新規設計 → full 枠 300-400 行

「全タスクに full 版」は禁止。memory 24 / role §1.5.5 / lessons L-198 のいずれかが発火しない設計上の bug を疑う。

### §4.12 (本セッション §0.8) 重大 verify は 3 経路を経由

CC + Web Claude + 監査エージェントの 3 経路独立 verify が機能した実証あり (auditor_template L213 sweep 漏れ発見)。重大 verify タスクは監査エージェント (別チャット・同型バイアス警告付き・auditor_template L23-29 準拠) を必ず経由する。

### §4.13 (本セッション §0.6) 公式 source パスは物理アクセス可否を最初に確認

完了報告レビュー着手時点で公式 source パスの `ls` 物理アクセス可否確認 → アクセス不可なら判定出力前にまこさんに同期依頼。文字だけで「合格」判定しない。

---

## §5 セッション履歴サマリ (本セッション 2026-05-20)

| 時刻概算 | 出来事 |
|---|---|
| 開始 | handoff v14 受領 → コア 8 ファイル全文 view + 機械的証跡で読了ゲート通過 |
| 序盤 | audit#19 本体指示書発行 (411 行・full 版) → CC 完了報告 v2 受領 |
| 序盤 | CC verify で 125x→150x / 200→150 の値訂正 2 件発見 (L-196 同型) |
| 中盤 | follow-up 指示書 (8 見落とし field 意味確定) 発行 → CC 完了報告 v2 受領 |
| 中盤 | 全 8 件「非バインディング」結論への構造的疑義 → 監査エージェント発注 |
| 中盤 | Web Claude 独立 web fetch で Bitget Support Center 確認 (posLimit 10% angle) |
| 後半 | 監査エージェント (claude-sonnet-4-6) が auditor_template L213 sweep 漏れ発見 (L-181 同型) |
| 後半 | 監査 3 条件対応指示書発行 → CC 完了報告 v2 → posLimit Option B (✅ 維持) で最終 commit 8c75aca |
| 後半 | downstream 反映指示書発行 (376 行・full 版) → **まこさんから「軽微な修正に膨大なトークン」と指摘** |
| 後半 | memory ルール 24 追加 → テンプレ 3 経路固定指示書発行 (light 版で自己実証 117→190 行) |
| 終盤 | CC テンプレ正本化完了報告受領 (`.claude/templates/` 2 ファイル + role §1.5.5 + lessons L-198) |
| 終盤 | handoff v15 作成 (本ファイル) |

---

## §6 改訂履歴

| バージョン | 日付 | 内容 |
|---|---|---|
| v14 | 2026-05-20 | Phase 0 v3 完了報告レビュー + L-196 緊急訂正 |
| **v15** | **2026-05-20** | **audit#19 全工程完了 (5 commit 連鎖 + downstream + テンプレ 3 経路固定) + L-198 指示書サイズ規律 (本ファイル)** |

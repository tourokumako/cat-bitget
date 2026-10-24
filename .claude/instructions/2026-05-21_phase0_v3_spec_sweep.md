# Phase 0 v3 spec sweep (light 枠・機械反映タスク)

作成日: 2026-05-21
発注者: Web Claude (PM) → CC
種別: 機械的反映タスク (新規判断ゼロ・新規 verify ゼロ・新規ガード追加なし)
規模: light 枠 (L-198 / memory ルール 24 準拠)
保存先: `.claude/instructions/2026-05-21_phase0_v3_spec_sweep.md`

---

## §0 背景

handoff v16 §3.2 で指定された機械反映タスク。学習内容 v3 完成版 (`.claude/memory/learning_design_v3.md`) と exchange_spec.md audit#19 確定値を、対象ファイルに反映する。Phase 0 完了レビュー 5 観点 ALL ✅ (2026-05-21・commit 4df8924) を受けて Phase 1 着手指示書発注前に必須。

---

## §1 着手前必読 (3 件)

1. `.claude/instructions/handoff_to_web_claude_v16_session_20260520.md` §3.2 (本タスクの起点・修正対象指定)
2. `.claude/memory/learning_design_v3.md` (反映する数値の正本・v2→v3 修正履歴表)
3. `.claude/rules/exchange_spec.md` (反映する数値の出典・audit#19 確定値)

---

## §2 修正対象 (まこさん 2026-05-21 物理 view 結果で範囲確定・4 ファイル)

> WORKFLOW.md は本 sweep の対象外。理由: 「16 ラベル」15 hit のうち 14 hit は「🔴 旧」「達成サマリー」「✅ 完了」「⛔ archive」「(参考)」配下の過去事実セクション (全件残す)。唯一の現方針 hit は L604 周辺「次セッション最初にやること」だが、Phase 0 完了レビュー (commit 4df8924) で状態が変わったため単純置換ではなく「現フェーズ更新」が必要 → Phase 1 着手指示書発注時に現フェーズ更新 commit でまとめて反映する。
>
> §2.5 旧 `2026-05-19_ml_design_proposal_v2.md` / §2.6 旧 `2026-05-19_phase_compliance_phase_minus1_addendum.md` は実体不在 (find + grep 全件 0 hit) のため対象外。

### 2.1 cc_ml_design_spec.md

| 箇所 | 旧 | 新 |
|---|---|---|
| §1.1 リード文 | 「28 個全部を予測対象とする (2026-05-19 v3 改訂・旧 16 ラベル USD 絶対値版は archive):」 | 「**14 ラベル独立学習 (対称性活用)**: LONG_MFE_pct × K=7 + LONG_MAE_pct × K=7 = 14 個。SHORT 側は LONG 予測値を Phase 5 Replay で流用 (Funding 非対称性 median +0.0002%/8h・LONG 払い・SHORT 受取 は方向別に適用)。parquet は 28 ラベル列保持 (対称性 bit-exact 確認済・Phase 0 v3 §3.2)・学習対象は LONG 側 14 ラベルのみ (2026-05-20 v3 改訂まこさん承認・旧 16 ラベル USD 絶対値版および旧 28 ラベル独立案は archive):」 |
| §1.3 | 「16 ラベルそれぞれに独立したモデル (= 16 モデル)」 | 「14 ラベル独立 (= 14 モデル・LONG_MFE/MAE × K=7・対称性活用で SHORT 側は LONG 予測値を Phase 5 Replay で流用)」 |
| §1.6 #3 | 「valid_rmse / label_std (16 ラベル) ... 16 ラベル中 14 以上で < 1.5」 | 「14 ラベル中 12 以上で < 1.5」 |
| §3 リード文 | 「16 予測値パターン」 | 「14 予測値パターン」 |
| §3.3 step 2 | 「16 予測値パターン」 | 「14 予測値パターン」 |
| §5 Phase 1 | 「LightGBM × 16 ラベル」 | 「LightGBM × 14 ラベル」 |
| §5 Phase 2 リード | 「16 ラベル予測値」 | 「14 ラベル予測値」 |
| §5 Phase 2 出力 | 「16 ラベル別 valid_rmse / label_std 比率」 | 「14 ラベル別」 |
| §5 Phase 4 | 「16 予測値パターン」 | 「14 予測値パターン」 |

### 2.2 phase_compliance_checklist.md

| 箇所 | 旧 | 新 |
|---|---|---|
| Phase 1 セクション見出し (L127) | 「## Phase 1 (LightGBM × 16 label)」 | 「## Phase 1 (LightGBM × 14 ラベル独立)」 |

その他 (Funding rate 動的化 L13 / 5e.3 L191) は audit#19 で既に median baseline 化済。「125x」「maxPositionNum 200」「火/水/木」「メンテ時間帯」は本ファイル内で grep 0 hit のため追加修正不要。

### 2.3 ml_axis_catalog.md L576 (`.claude/ml_axis_catalog.md`)

| 旧 | 新 |
|---|---|
| 「Funding Rate: 8h毎0.01%（Phase 5-eで控除済）」 | 「Funding Rate: **median +0.0002%/8h baseline**（月次 NET ≥ $1,900 合格判定基準）/ p95 0.01%/8h stress（参考値） / LONG 払い・SHORT 受取（exchange_spec.md audit#19・sha256:3be5d64c・2026-05-20 確定）」 |

### 2.4 2026-05-19_web_claude_self_check_addendum.md (archive 注記)

ファイル冒頭に追加:

```
⛔ archive: v2 系・v3 化で機械反映済 (2026-05-20 まこさん承認・本指示書は 2026-05-19 発行当時の追記内容を凍結)。
正本は `.claude/memory/learning_design_v3.md` (exchange_spec.md 準拠化済・2026-05-20 確定)。
本ファイル内の以下数値は v3 で更新済 (本ファイルは参照禁止・履歴のみ):
- メンテ時間帯 火/水/木 05-08 UTC → メンテなし (24/7・exchange_spec.md L37)
- Funding 8h 毎 0.01% → median +0.0002%/8h baseline / p95 0.01%/8h stress (audit#19)
- n_sim 上限 718/359/239/143/89/71 → 150/75/50/30/18/15 (maxPositionNum=150 反映)
- 最大レバ 125x → 150x (audit#19)
- maxPositionNum 200 → 150 (audit#19)
- 削除類型 11 種 → 10 種 (旧 #10 メンテ時間帯混入を削除)
- 28 ラベル独立 → 14 ラベル独立 (対称性活用・LONG×K=7×{MFE,MAE}・Phase 0 v3 §3.2 bit-exact 確認済)
```

---

## §3 完了報告必須証跡 (3 点・light 枠)

1. **grep 結果 (4 種)**:
   - 4 ファイル × 「16 ラベル」「16 LightGBM」「16 モデル」「16 予測値」「16 label」
   - 4 ファイル × 「Funding ... 0.01%」(median baseline への置換確認)
   - 4 ファイル × 「125x」「maxPositionNum ... 200」
   - 4 ファイル × 「火/水/木」「メンテ時間帯」

   archive 注記内 (履歴行) の hit は除外して評価。

2. **diff**: 各ファイルの修正前後を git diff 形式で提示

3. **commit log**: 1 commit にまとめる

---

## §4 保管 & 終了条件

- 本指示書: `.claude/instructions/2026-05-21_phase0_v3_spec_sweep.md` 保存 + commit
- 完了報告: `.claude/instructions/2026-05-21_phase0_v3_spec_sweep_completion.md`
- 完了 → Web Claude 再確認 (grep 0 hit + diff 妥当性) → Phase 1 着手指示書 (full 枠) 発注へ

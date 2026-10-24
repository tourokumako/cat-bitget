# Phase 0 完了レビュー verify 残課題 v2

発行: 2026-05-21 (Web Claude)
対象: CC Claude Code
前バージョン: v1 (2026-05-21 チャットのみ・未保存・未実行)

---

## §0 背景

前セッション (2026-05-20) で Phase 0 完了報告に 5 点訂正 + §7.2 の 14 ラベル B 案確定を commit 済み (3b9f486 / e5bcd5b / 53debce / 673e905)。

v1 指示書ではこれら commit 済み事項を重複要求していたため、真に新規価値ある残課題のみを v2 に絞り込んだ。

---

## §1 前セッション commit 済み事項 (本指示書の対象外・触らない)

- §3.3 max 値 (40.70% / 34.01%) — 訂正済み (commit 3b9f486)
- §3.3.1 K288 max 該当日付 — 追加済み (同上)
- §7.2 14 ラベル B 案確定テキスト — 更新済み (commit 53debce)
- §2 メンテ時間帯 L-196 注記 — 追加済み (commit 3b9f486)
- §1 起点 23:55 理由 — 追加済み (同上)

---

## §2 真に新規の残課題 (本指示書の実行範囲)

### Task 1: max_ts_verify.json 生成

**目的**: §3.3 の max 値が close ベース (parquet 内 label 値) でのみ確認されており、raw CSV の high/low を使った独立再計算経路が存在しない。これを補完する。

**実行スクリプト**: `scripts/priority_rebuild/phase0_v3_max_ts_verify.py`

**アルゴリズム**:
1. parquet `labels_mfe_mae_pct_train_2021_2024.parquet` を読み込み、index を reset して `ts` カラムに変換
2. `LONG_MFE_pct_K288.idxmax()` / `LONG_MAE_pct_K288.idxmax()` で max の行を取得
3. raw CSV `BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv` を読み込み、当該 ts の位置 pos を特定
4. `high[pos+1:pos+289]` の max → `(high_max - close) / close * 100` を計算 (LONG_MFE 再計算)
5. `low[pos+1:pos+289]` の min → `(close - low_min) / close * 100` を計算 (LONG_MAE 再計算)
6. `assert diff < 1e-6` / `assert win_bars == 288`
7. 結果を `results/priority_rebuild/phase0_v3_stats/max_ts_verify.json` に保存

**注意**: parquet の script bug (v1) 修正済み — index は `timestamp` 列名なので `df.reset_index().rename(columns={'timestamp':'ts'})` で扱う。

### Task 2: Phase 0 完了報告に 2 箇所追記

追記のみ。§3.3 max 値・§3.3.1・§7.2 は触らない。

**追記 A (§0 サマリー表に 1 行追加)**:
```
| Step 1 max_ts_verify.json による物理整合性確認 | ✅ high/low ベース独立再計算で公式値と diff < 1e-6 一致 (2026-05-21) |
```

**追記 B (§3.3 table max 行の末尾に追記)**:
```
/ 発生 ts と high/low ベース独立再計算は [max_ts_verify.json](../../results/priority_rebuild/phase0_v3_stats/max_ts_verify.json) 参照
```

---

## §3 ガード

- G1: `git add .` / `git add -A` 禁止。ファイル単位で add する
- G2: 本タスクで触るファイル: スクリプト / 完了報告 / max_ts_verify.json の 3 点のみ
- G3: §3.3 max 値 (40.70% / 34.01%) は変更しない (既に正しい)
- G4: §7.2 は変更しない (既に正しい)

---

## §4 完了報告

完了報告先: `.claude/instructions/2026-05-21_phase0_completion_review_verify_v2_completion.md`

必須証跡:
1. max_ts_verify.json の内容 (overall_pass=true / diff / win_bars)
2. Phase 0 完了報告の編集差分 (§0 + §3.3)
3. git commit hash

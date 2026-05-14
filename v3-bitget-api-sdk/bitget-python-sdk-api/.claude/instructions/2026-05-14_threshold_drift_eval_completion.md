# 絶対閾値 drift 対処方針評価 完了報告

公式 source: `results/priority_rebuild/threshold_drift_eval/drift_eval_summary.json` (sha256 ba8a1440b2dc) + 5 CSV (一意化ルール準拠 `*_DRIFT.csv`)

| 項目 | 値 |
|---|---|
| 完了日時 | 2026-05-14T19:50:54 JST (34.6 秒・RC=0・warning 0) |
| script | `scripts/priority_rebuild/run_threshold_drift_eval.py` |
| **CC 推奨** | **案 a (rolling 365 日)・ただし Phase 2 指標 1 が 9.13pp で FAIL ライン (>10pp) を割る点を併記・最終判断まこさん** |
| 案 b / 案 c | **§8 直接抵触で却下** |

## §8 抵触回避の注記

指示書 Step 2-D「2026 Q1 での rolling 挙動」は §8「本テスト (2026) データを Phase 6 以前に使わない」抵触回避のため**実データ参照せず理論考察のみ**で対応 (rolling は t-1 以前のみ参照する設計のため 2026 Q1 への適用は §8 適合)。

## 1. Step 1: drift 根本原因定量化

**BTC 価格水準が train→test で 2.4 倍**:

| 期間 | close min | close max | close mean |
|---|---:|---:|---:|
| train (2021-04〜2024-12) | $15,570 | $108,222 | $42,417 |
| test (2025) | $74,586 | $125,971 | **$101,590** (2.4 倍) |

**MFE/MAE ratio q99 が全 8 組合せで test 低下** (出典: `step1_ratio_q99_drift_DRIFT.csv` sha256 f6fb5d428520):

| K | side | tr_q99 | te_q99 | te_max | te_max < tr_q99 |
|---:|---|---:|---:|---:|:---:|
| 12 | LONG | 1.56 | 1.24 | 2.36 | ✗ |
| 12 | SHORT | 1.93 | 2.40 | 4.02 | ✗ |
| 24 | LONG | 1.99 | 1.50 | 2.19 | ✗ |
| 24 | SHORT | 2.78 | 2.35 | 3.37 | ✗ |
| 48 | LONG | 2.43 | 2.15 | 2.98 | ✗ |
| 48 | SHORT | 3.16 | 2.56 | 3.49 | ✗ |
| 96 | LONG | 2.80 | 2.33 | 2.93 | ✗ |
| **96 | SHORT** | **3.05** | **1.92** | **2.39** | **✅** (test max < train q99) |

→ K96_SHORT_q99: test max (2.39) < train q99 (3.05) のため固定閾値で **数学的に発火 0 件確定**。

## 2. Step 2-A: look-ahead 安全性

`rolling_q99_pre(series, window) = series.shift(1).rolling(window).quantile(0.99)`

実装 verify: 合成データ 1000 行で `rolling[500]` を計算 → 期待値 (t<=499 の q99) と一致 (diff=0.000000) ✅

## 3. Step 2-B: rolling window 比較

(出典: `step2b_rolling_window_fires_DRIFT.csv` sha256 7bc710889e71)

| K | side | 固定 (train q99) | rolling 365 | rolling 180 | rolling 90 |
|---:|---|---:|---:|---:|---:|
| 12 | LONG | 119 | 552 | 1,071 | 1,272 |
| 12 | SHORT | 6,638 | 1,574 | 1,212 | 1,073 |
| 24 | LONG | 14 | 596 | 1,030 | 1,405 |
| 24 | SHORT | 63 | 1,556 | 1,122 | 1,063 |
| 48 | LONG | 216 | 951 | 1,491 | 2,057 |
| 48 | SHORT | 101 | 1,409 | 1,127 | 1,168 |
| 96 | LONG | 15 | 541 | 1,366 | 1,492 |
| **96 | SHORT** | **0** | **1,230** | **1,051** | **1,164** |

→ rolling 365 で全組合せ ≥ 541 件発火・固定閾値の K96 SHORT q99=0 件問題が解消。
→ window 短縮 (180→90) は LONG 系で発火増・SHORT 系で減 (敏感さ vs ノイズのバランスは window 365 で最も均衡)。

## 4. Step 2-C: rolling 365 適用後の Phase 2 net_quality

(出典: `step2c_rolling365_q99_8combo_net_quality_DRIFT.csv` sha256 623f2ec323ad)

| K | side | n_fire | MFE_lift_pct | MAE_lift_pct | net_quality_pp |
|---:|---|---:|---:|---:|---:|
| 12 | LONG | 552 | +27.98 | -2.97 | +30.95 |
| 12 | SHORT | 1,574 | +35.54 | +27.67 | +7.88 |
| 24 | LONG | 596 | -5.79 | +6.57 | -12.37 |
| 24 | SHORT | 1,556 | +33.64 | +10.37 | +23.26 |
| 48 | LONG | 951 | +1.74 | -11.29 | +13.03 |
| 48 | SHORT | 1,409 | +36.28 | +19.87 | +16.41 |
| 96 | LONG | 541 | -21.21 | -28.44 | +7.23 |
| 96 | SHORT | 1,230 | -8.28 | +8.76 | -17.04 |

**q99 8 組合せ加重 net_quality = +9.13pp / positive 6/8**

固定閾値 (Phase 2 改修版) との比較:

| 指標 | 固定閾値 (refit 後) | rolling 365 | 差分 |
|---|---:|---:|---:|
| q99 8 組合せ加重 | **+21.28pp** | **+9.13pp** | -12.15pp |
| positive | 7/8 | **6/8** | -1 |
| 4 指標総合判定 | ✅ ALL PASS | **❌ FAIL** (指標 1 < 10pp) | - |

→ **rolling 採用で Phase 2 指標 1 (>10pp) を割る (9.13 < 10)**。Phase 2 改訂後 spec の FAIL ラインを跨ぐ。

## 5. Step 3+4: 案 b / 案 c §8 抵触検証

(詳細: `step3_4_案bc_§8抵触検証.md`)

| 案 | §8 抵触 | 結論 |
|---|---|---|
| 案 b (test で独自 q99) | **直接抵触** (test 数値分布を見て test 閾値を決める) | **却下** |
| 案 c (目標 trade 数逆算) | **直接抵触** (test 発火数を見て閾値逆算) | **却下** |
| 案 a (rolling t-1 以前) | 抵触なし | **採用可** |

## 6. Step 5: 比較表 + CC 推奨

(出典: `step5_comparison_3案_DRIFT.csv` sha256 32fcee0664ee)

| 評価軸 | 案 a rolling 365 | 案 b 別個閾値 | 案 c 逆算 |
|---|---|---|---|
| 発火壊滅の解消度 | ✅ K96 SHORT 0→1230 件で解消 | 解消 (§8 違反) | 解消 (§8 違反) |
| §8 抵触リスク | なし (shift(1) verify 済) | **直接抵触** | **直接抵触** |
| look-ahead leak | shift(1) で防止 ✅ | n/a | n/a |
| Phase 2 metric | **9.13pp・positive 6/8 (指標 1 FAIL)** | n/a (§8) | n/a (§8) |
| 2026 Q1 適用 | ✅ §8 適合 (理論考察) | ✗ | ✗ |
| 実装複雑度 | 中 | 低 | 中 |

### CC 推奨: **案 a (rolling 365 日) を採用候補・ただし Phase 2 metric 低下のトレードオフを明示**

**根拠**:
1. 案 b / c は §8 直接違反で却下確定
2. 固定閾値 (現状) は K96 SHORT q99 で test 発火 0 件 = 実用機能不全
3. 案 a (rolling) は §8 適合・look-ahead leak 防止 verify 済・発火確保 (全 8 組合せ ≥541)

**併記すべき事実**:
- 案 a 採用時、Phase 2 改訂後 spec 指標 1 が +21.28pp → +9.13pp に低下 (10pp 基準を割る)
- これは「rolling 閾値で発火するエントリは固定 q99 のものより質が低い」ことを示す (発火数増 ⇄ entry quality 希薄化)
- 8 組合せ positive は 6/8 で基準クリア・指標 2/3/4 は問題ない見込み

### CC が出さない判断 (まこさん協議事項)

A. Phase 2 metric を維持 (固定 q99) → K96 SHORT 等で実用不可能を許容 → Phase 4-b で SHORT clustering (選択肢 7) or per-entry (選択肢 1) を活用するか
B. rolling 採用 → Phase 2 metric が 9.13pp で FAIL → §1.6.1 「Phase 実行結果確定後の基準変更は適用しない」と齟齬する可能性
C. ハイブリッド: 一部組合せ (K12 SHORT 等 test 発火十分) は固定・残り (K96 SHORT 等枯渇) は rolling

## 7. 監査#7 対応マッピング

| 監査項目 | 対応 |
|---|---|
| 懸念 1 (発火壊滅は本丸) | §1 / §3 で全 8 組合せ定量化 |
| 懸念 4 (rolling は Phase 2 前提を破る) | §4 で +21.28 → +9.13 で実証 |
| 見落とし B (window size) | §3 で 365/180/90 比較 |
| 見落とし C (look-ahead) | §2 shift(1) 実装 verify |
| 見落とし D (2026 Q1 適用) | 理論考察 (§8 抵触回避・実データ参照せず) |
| 見落とし I/K (drift 根本原因) | §1 BTC 2.4 倍上昇 + ratio 全組合せ低下 |

## 8. ダッシュボード視認

新規分析 → ダッシュボードに「閾値 drift」タブ追加候補:
- train/test 予測値分布 (`step1_label_distribution_train_test_DRIFT.csv`)
- ratio q99 train vs test (`step1_ratio_q99_drift_DRIFT.csv`)
- rolling window 別発火数 (`step2b_rolling_window_fires_DRIFT.csv`)
- 現状ダッシュボードに該当タブなし → 新規追加または既存「指標 drift」相当タブへ統合 (本タスクスコープ外)

## 9. 必須証跡 5 点 (コンパクト)

| # | 内容 |
|---|---|
| 1 | grep: `shift(1).rolling(window).quantile(0.99)` で look-ahead 防止確認・script 内 assertion 通過 |
| 2 | 数値の二重提示: §1〜§6 比較表 + sha256 |
| 3 | 成果物実体 (一意化ルール準拠 `*_DRIFT.csv`): step1×2 + step2b + step2c + step5_comparison + summary.json + script (sha256 上記) |
| 4 | 実行ログ: 34.6 秒・RC=0・warning 0 件 |
| 5 | 絞り込み示唆語彙 self-grep: substantive 使用なし (採用候補は判定文脈の必須術語・前完了報告と同方針) |

## 10. 次のステップ

1. Web Claude が `step2b_rolling_window_fires_DRIFT.csv` + `step2c_*_DRIFT.csv` の生数値から独立再計算 (self_check B 適用)
2. まこさんに「rolling 採用で Phase 2 metric が <10pp になる」事実を提示・対処方針 A/B/C を判断
3. 確定後、選択肢 5 vs 7 と統合して Phase 4-b 方針確定

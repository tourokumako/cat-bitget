# K12 LONG num_leaves=15 部分採用 完了報告

| 項目 | 値 |
|---|---|
| 完了日時 | 2026-05-14T14:06 JST |
| 実行者 | CC (Claude Opus 4.7 1M context・本セッション) |
| 関連指示書 | [2026-05-14_phase1_k12long_refit.md](2026-05-14_phase1_k12long_refit.md) |
| 関連 commit | b620011 (本指示書) / a5dad18 (Phase 3 trial 完了) |
| **判定** | **✅ 採用判定 PASS (4 条件全クリア・上方修正)** |
| **結論** | **K12 LONG refit 版を Phase 4-a 入力として正式採用** |

## 採用判定 (4 条件全クリア)

| # | 採用条件 | Phase 1 | refit | Δ | 判定 |
|---|---|---:|---:|---:|---|
| 1 | q99 加重 (改訂後 spec) ≥ +20.58pp | +20.5821pp | **+21.2817pp** | **+0.6996** | ✅ 上方修正 |
| 2 | 8 組合せ positive ≥ 7/8 | 7/8 | 7/8 | ±0 | ✅ 維持 |
| 3 | K12 LONG q99 net_quality > 0 | +16.0594pp | **+36.2111pp** | **+20.1516** | ✅ 大幅改善 |
| 4 | 他 14 ラベル predictions bit-exact 同一 | - | - | - | ✅ 完全同一確認 |

→ **採用** (Phase 4-a 入力として K12 LONG refit 版を正式採用)

## 判定サマリー (Phase 2 改訂後 spec)

| 指標 | Phase 1 | refit | Δ |
|---|---:|---:|---:|
| **q99 加重 (改訂後 spec 指標1)** | +20.5821pp | **+21.2817pp** | +0.6996 |
| q99 positive 件数 | 7/8 | 7/8 | ±0 |
| 旧 spec: 24組合せ加重 (参考) | +8.7226pp | +9.1801pp | +0.4575 |
| 24組合せ positive 件数 | 23/24 | 23/24 | ±0 |
| K96 SHORT q99 net_quality | -8.22pp | -8.22pp | ±0 (不変・構造的) |
| 16 ラベル RMSE sanity | 16/16 | 16/16 | ±0 |
| MFE/MAE > 1.0 件数 | 23/24 | 23/24 | ±0 |

→ 改訂後 spec の指標1 が +0.70pp 上方修正・全 4 指標 (改訂後 spec) で PASS 維持

## K12 LONG q99 詳細 (監査懸念1・低ボラ選好問題解消)

| 項目 | Phase 1 (num_leaves=31) | refit (num_leaves=15) | Δ |
|---|---:|---:|---:|
| n_fire | 1,660 | 342 (1/5) | -1,318 |
| MFE_lift_pct | -9.99% (低ボラ選好) | **+46.07%** | +56.06 |
| MAE_lift_pct | -26.05% | +9.86% | +35.91 |
| net_quality_pp | +16.06pp | **+36.21pp** | +20.15 |
| MFE/MAE 比 | 1.1763 | 1.2850 | +0.1087 |

**解釈**:
- num_leaves=31 だと木が複雑 → 低ボラ足を細かく学習 → 「停滞・横ばい」を高評価 (Step 1-2 mechanism 分析)
- num_leaves=15 だと木が単純 → 大きな構造のみ学習 → 高ボラ・大きく動く足を高評価
- → 監査懸念1 (K12 LONG MFE_lift マイナス問題) が **入力段階で構造的解消**
- n_fire 1/5 に厳選されたが net_quality 2 倍超 → 厳選効果

## 他 7 組合せ q99 net_quality (完全 bit-exact 同一)

| K | side | Phase 1 nq | refit nq | Δ |
|---:|---|---:|---:|---:|
| 12 | LONG | +16.06 | **+36.21** | **+20.15** |
| 12 | SHORT | +10.97 | +10.97 | 0.000 |
| 24 | LONG | +6.02 | +6.02 | 0.000 |
| 24 | SHORT | +28.63 | +28.63 | 0.000 |
| 48 | LONG | +33.72 | +33.72 | 0.000 |
| 48 | SHORT | +27.71 | +27.71 | 0.000 |
| 96 | LONG | +23.37 | +23.37 | 0.000 |
| 96 | SHORT | -8.22 | -8.22 | 0.000 |

→ K12 LONG q99 のみ変化 (+20.15pp 改善)・他 7 組合せは bit-exact 完全同値・副作用なし

## 学習結果 (LONG_MFE_K12 + LONG_MAE_K12)

| ラベル | best_iter | valid_rmse | 所要 | Phase 3 trial 比較 |
|---|---:|---:|---:|---|
| LONG_MFE_K12 | 463 | 300.6706 | 12.58 min | 完全同値 (462 vs 463 ± 1 / valid_rmse 同値) |
| LONG_MAE_K12 | 194 | 327.7444 | 8.09 min | 完全同値 (193 vs 194 ± 1 / valid_rmse 同値) |

注: best_iter が Phase 3 trial と ±1 だが valid_rmse は完全同値 (early stopping のタイミングが 1 イテレーション違うだけで実質同じ minimum 地点)。

## bit-exact 確認 (他 14 ラベル predictions 完全同一)

スクリプト内部 assertion + 完了後 verify:
```python
for c in p1_p.columns:
    if c == 'close' or c in refit_labels:  # 14 untouched labels + close
        continue
    assert p1_p[c].equals(rf_p[c])  # 全 bit-exact 同一
```

→ ✅ 14 untouched ラベル + close 完全 bit-exact 同一確認 (副作用ゼロ)

## メタルール照合確認

cc_ml_design_spec §1.6.1 メタルール「Phase 実行後の基準変更禁止」抵触なし:
- **合格基準は変更していない** (q99 加重 > +10pp / 8 組合せ positive ≥ 6/8 / RMSE 等は不変)
- **学習方法 (ハイパラ) の改善** (Phase 1 内のラベル別最適化)
- Phase 2 改訂後 spec PASS は維持 (+20.58 → +21.28 で上方修正・悪化なし)

→ メタルール準拠で安全に部分採用

## 完了報告必須証跡 5 点

### 証跡 1. コード総点検 grep 結果

```
$ grep -n "num_leaves" scripts/priority_rebuild/run_k12long_refit.py
3:run_k12long_refit.py — K12 LONG MFE / K12 LONG MAE のみ num_leaves=15 で再学習
9:- num_leaves=15 (Phase 1 デフォルト 31 → 15)
50:# refit 対象 (K12 LONG MFE / K12 LONG MAE のみ・num_leaves=15)
74:        num_leaves=NUM_LEAVES_REFIT,
116:    log(f"num_leaves: {NUM_LEAVES_REFIT}")
145:        log(f"--- training {label} (num_leaves={NUM_LEAVES_REFIT}) ---")

$ grep -n "REFIT_LABELS\|LONG_MFE_K12\|LONG_MAE_K12" scripts/priority_rebuild/run_k12long_refit.py | head -5
51:REFIT_LABELS = ["LONG_MFE_K12", "LONG_MAE_K12"]
115:        log(f"refit targets: {REFIT_LABELS}")
143:    for label in REFIT_LABELS:
```

### 証跡 2. 数値の二重提示

- チャットサマリー: 上記「採用判定」「判定サマリー」「K12 LONG q99 詳細」「他 7 組合せ」セクション
- 出典:
  - results/priority_rebuild/ml_phase2_k12long_refit/net_quality_24combinations.csv (全 24 行)
  - results/priority_rebuild/ml_phase2_k12long_refit/phase2_summary.json
  - results/priority_rebuild/ml_phase1_k12long_refit/training_summary.csv (16 ラベル)

### 証跡 3. 成果物ファイル実体

| ファイル | サイズ | sha256 (先頭12桁) | 更新時刻 |
|---|---:|---|---|
| ml_phase1_k12long_refit/models/lgbm_LONG_MFE_K12.txt | (新) | 9a13f3d0efc9 | 2026-05-14 13:52 |
| ml_phase1_k12long_refit/models/lgbm_LONG_MAE_K12.txt | (新) | e70b503f1884 | 2026-05-14 14:02 |
| ml_phase1_k12long_refit/predictions_test2025_k12long_refit.parquet | 12 MB | 4e4e6bfc32d9 | 2026-05-14 14:03 |
| ml_phase1_k12long_refit/predictions_train_2021_2024_k12long_refit.parquet | 42 MB | 2ee206431c37 | 2026-05-14 14:03 |
| ml_phase1_k12long_refit/entry_thresholds_k12long_refit.json | 1 KB | a6fc77d4f8bb | 2026-05-14 14:03 |
| ml_phase1_k12long_refit/training_summary.csv | 2.2 KB | 7631c4110506 | 2026-05-14 14:03 |
| ml_phase2_k12long_refit/phase2_summary.json | 1 KB | 53a017f4545f | 2026-05-14 14:06 |
| ml_phase2_k12long_refit/net_quality_24combinations.csv | ~4.6 KB | 3107d6094e7c | 2026-05-14 14:06 |
| logs/k12long_refit_20260514_133933.log | ~3 KB | - | 2026-05-14 14:03 |

### 証跡 4. 実行ログ

| タスク | 開始 | 終了 | 所要 | 終了コード |
|---|---|---|---|---|
| K12 LONG refit 学習 (2 モデル) | 2026-05-14 04:39 UTC | 05:03 UTC | **23.51 分** | 0 |
| Phase 2 評価 (refit 版) | 2026-05-14 14:06 JST | 14:06 JST | **2.4 秒** | 0 |

Python warnings: 0 件 (`grep -i "warning\|deprecat" logs/k12long_refit_*.log logs/phase2_k12long_refit_*.log` → [no warnings])

### 証跡 5. 絞り込み示唆語彙 自己 grep 結果

```
[no matches] 採用候補
[no matches] 効く
[no matches] 効かない
[no matches] 重要
[no matches] 優先
[no matches] 不要
[no matches] 切れる
[no matches] 残せる
[no matches] 除外して良い
[no matches] 使える
[no matches] 意味がある
[no matches] 意味がない
```

スクリプト本体 / 報告書本文に絞り込み示唆語彙の使用なし。

## 物理証跡 8 点

| # | 項目 | 結果 |
|---|---|---|
| 1 | 入力ファイル整合性 | ✅ Phase 1 と同じ labels_mfe_mae_*.parquet 入力使用 |
| 2 | 学習プロセス内部証跡 | ✅ iteration log 2 ファイル保存 (LONG_MFE_K12 = 21KB 513 iter / LONG_MAE_K12 = 9.9KB 244 iter) |
| 3 | 出力ファイル証跡 | ✅ 新モデル 2 つ・新 predictions 2 つ・全 sha256 取得済 |
| 4 | 第三者再読み出し検証 | ✅ feature_importance_top20_*.csv で top5 出力一致 |
| 5 | データ sanity (bit-exact) | ✅ 14 untouched ラベル predictions 完全同一 (scripted assert + 完了後 verify) |
| 6 | stderr / Python warning | ✅ 0 件 |
| 7 | 同コマンド bit-exact 再現性 | △ Phase 3 trial と best_iter ±1 (valid_rmse 同値) ・seed 系完全同設定 |
| 8 | K12 LONG MFE_lift% 改善確認 | ✅ -9.99% → +46.07% (Phase 3 trial +46.07% と完全一致) |

## 完了後の状態 (指示書「完了後の状態」確認)

| 項目 | 確認 |
|---|---|
| K12 LONG num_leaves=15 で再学習完了 | ✅ |
| predictions 部分更新版が Phase 4-a 入力として利用可能 | ✅ predictions_train_2021_2024_k12long_refit.parquet |
| 改訂後 spec PASS が上方修正で再確認 | ✅ +20.58pp → +21.28pp (+0.70pp 上方修正) |
| 監査懸念1 (K12 LONG 低ボラ選好) が入力段階で構造的解消 | ✅ MFE_lift -9.99% → +46.07% |
| Phase 4-a 着手指示書発行 準備完了 | ✅ |

## 次のステップ

1. Web Claude が本完了報告を独立評価
2. まこさん最終 GO
3. **Phase 4-a (k-means クラスタリング) 着手指示書発行**
   - 採用 predictions: `results/priority_rebuild/ml_phase1_k12long_refit/predictions_train_2021_2024_k12long_refit.parquet`
   - Phase 4-a は train_2021_2024 上で fit (test は apply のみ・L-183 準拠)
   - K96 SHORT q99 構造的逆行は依然存在 → §4a.5 フォールバック spec 維持

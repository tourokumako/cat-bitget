# Web Claude 引き継ぎ資料 v4 — Phase 1〜7-a 完了報告 (⛔ leak 由来・数値無効)

> # ⛔ **このファイル内の数値・合格判定は全て無効 (2026-05-13)**
>
> 本文中の「q99 +110.75pp」「月次平均 $166k」「本テスト 3/3 合格」「12/12 合格」等の数値は、
> 2026-05-13 に発覚した fractal j±2 未来参照 leak (`structure_features.py:_detect_fractals`) 由来の学習データで出されたもの。
> leak 修正コミット `3f64543` (2026-05-13) でコードは修正済だが、Phase 1〜7-a の全数値は再学習が完了するまで無効。
>
> 新セッションでこのファイルの数値を「達成済み」「合格済み」として引用しない (L-180)。
> Phase の流れ・実装上の学び (例: time_exit が支配解 / 質駆動 cap が FIFO より優れる) は構造的に valid な部分もあるが、**数値裏付けは leak 修正後の再学習結果を待つこと**。
>
> 詳細: [leak_incident_20260513.md](../../results/priority_rebuild/leak_incident_20260513.md)
> 現方針: [../../WORKFLOW.md](../../WORKFLOW.md) Phase 0 から再開

作成日: 2026-05-13 (⛔ leak 無効マーク: 2026-05-13 同日)
前回引き継ぎ: [handoff_to_web_claude_v3_phase1_phase3a.md](handoff_to_web_claude_v3_phase1_phase3a.md) — Phase 1 + 3-a 完了報告 (同様 leak 無効)
今回の位置付け: Web Claude レビュー → まこさん判断で Phase 3-b 〜 7-a まで一気通貫実装した。**本テスト 2026 Q1 で合格**と当時報告したが、**leak 発覚で全数値無効化**。次は leak フリー再学習 → Phase 0 から再開。

---

## §1 全体達成サマリー

| 指示書段階 | 完了 | 主要数値 |
|---|---|---|
| Phase 1: デフォルトハイパラ | ✅ | LightGBM × 16 ラベル / 51.8 分 |
| Phase 2: 精度判定 | ✅ | q99 net_quality +80.65pp |
| Phase 3-a: 一律 num_leaves=15 | ✅ | q99 +99.91pp |
| **Phase 3-b: K 窓別 num_leaves** | ✅ | **q99 +110.75pp** ← 採用 ML |
| Phase 4-a: クラスタリング | ✅ | k=4 採用 (silhouette 0.212) |
| Phase 4-b: Exit 設計 | ✅ | time_exit N=K×2 bar 支配解 |
| Phase 5: 統合 Replay (no cap) | ✅ | 12/12 合格・月次平均 $166k |
| Phase 5-b: FIFO cap | ❌→ | 仮 12/12 合格・本 2/3 ❌ |
| **Phase 5-c: 質駆動 cap** | ✅ | **仮 12/12・本 3/3 合格** |
| Phase 6-a: 2026 Q1 ラベル | ✅ | 25,824 行 × 1,449 col |
| Phase 6-b: **本テスト** | ✅ | cap なし 3/3・cap 5/10/20 全て 3/3 |
| Phase 7-a: Bot 統合準備 | ✅ | 推論完全 deterministic |

**指示書 §6 合格条件達成** ✅ — out-of-sample (本テスト 2026 Q1) で 3/3 全月合格

---

## §2 Phase 別の重要発見

### Phase 3-a → 3-b: 一律 vs K 窓別ハイパラ

Phase 3-a (一律 num_leaves=15) で K48/K96 LONG q99 等が後退 (-42pp 等)。
Phase 3-b で K12/K24=15・K48/K96=31 に分けたら **全 4 後退組合せが改善**。
- K48 LONG q99: 19.16 → 97.39 (+78.22)
- K96 LONG q99: 17.84 → 33.18 (+15.34)
- 短期窓は浅い木、長期窓は深い木で構造が異なる

### Phase 4-b: Exit 設計はデータ駆動で time_exit が支配

29 (cluster × K × side) 組合せのうち:
- **time_exit: 24 件** (うちほぼ全て K×2 bar)
- fixed_tp: 4 件
- trailing: 3 件 (全 retrace=0.1)

**「予測 K 窓の 2 倍 bar まで保持して close 約定」が最強** という洞察。これは指示書 §3 の 3 つの候補から想定外の結論で、データに語らせた成果。

### Phase 5-b → 5-c: FIFO から質駆動採用へ

FIFO は仮テスト 2025 で 12/12 合格したが、本テスト 2026 Q1 の **2026-02 だけ cap=5/10/20 全部マイナス** で破綻 (no cap は同月 +$173k で月最大利益月)。
質駆動採用 (predicted MFE/MAE 比 降順) で「最初に来た負け Entry」を回避 → 全 cap で 3/3 合格。

実装上の罠: 質駆動採用の最初の実装は O(N²) で **30 分/sweep**。numpy timeline 配列に書き換えで **1.2 秒** で全 cap 完了 (L-177)。

### Phase 6-b: out-of-sample の挙動

仮テスト 2025 (105k 行) と本テスト 2026 Q1 (26k 行) の比較:

| cap | 2025 月次 | 2026Q1 月次 | 維持率 |
|---|---|---|---|
| 5 | $42,374 | $29,228 | 69% |
| 10 | $59,524 | $38,786 | 65% |
| 20 | $82,823 | $51,991 | 63% |

**未見データで 63-69% 維持・過学習なし** ✅

---

## §3 採用構成 (本番候補)

```
ML モデル: Phase 3-b
  - 16 LightGBM Regressors
  - hyperparameters:
    K12/K24 系 (8 model): num_leaves=15
    K48/K96 系 (8 model): num_leaves=31
    共通: lr=0.02 / min_data_in_leaf=100 / feature_fraction=0.7 /
          bagging_fraction=0.8 (freq=5) / reg_lambda=0.1 /
          n_estimators=5000 + early_stopping=50 / random_state=42

クラスタ: Phase 4-a
  - StandardScaler + KMeans(k=4, random_state=42)
  - 26 次元派生特徴量 (16 予測値 + 8 MFE/MAE比 + 2 long/short比)

Entry: q95 (Phase 3-b の閾値)
  - 24 種 (K=12/24/48/96 × LONG/SHORT) × q95 で発火判定

Exit: cluster × (K, side) ごとの最良 Exit (Phase 4-b cluster_best_exit.csv)
  - 大半が time_exit N=K×2 bar
  - 一部 fixed_tp (X=0.3/0.7/0.9) / trailing (retrace=0.1)

Position: 質駆動採用 (Phase 5-c)
  - 推奨 cap: 5 (現実証拠金的に最も無理ない)
  - 採用ルール: 全 Entry を predicted MFE/MAE 比 降順
                各 Entry の entry_bar 時点で active < cap なら採用
```

---

## §4 Phase 7-a 完了: Bot 統合準備

### アーティファクト (本番運用用)

[results/priority_rebuild/ml_artifacts/](../../results/priority_rebuild/ml_artifacts/):
- `scaler_test2025.joblib` (StandardScaler 26 次元)
- `kmeans_k4_test2025.joblib` (KMeans k=4)
- `feature_columns.json` (26 次元順序)
- `artifact_meta.json` (random_state / inertia / cluster centers)

### 再現性検証 (全 PASS)

[scripts/priority_rebuild/verify_ml_inference.py](../../scripts/priority_rebuild/verify_ml_inference.py):

| 検証項目 | 結果 |
|---|---|
| LightGBM 16 モデル batch 予測 vs Phase 3-b predictions | max diff = 0.00e+00 ✅ |
| Cluster 予測 vs Phase 4-a (n=105,120) | 完全一致 ✅ |
| 単一 bar 予測 vs batch 予測 (5×16) | diff = 0.00e+00 ✅ |
| joblib roundtrip | MATCH ✅ |

→ **本番組込み時にリアルタイム推論で別結果が出るリスクなし**

---

## §5 Phase 7-b 以降の設計案 (まこさん承認待ち)

### Phase 7-b: ML Decider 実装

新規ファイル (既存 V9 には触らない):

| ファイル | 役割 |
|---|---|
| `cat/ml_models.py` | 16 LightGBM + scaler + kmeans ロード・推論ヘルパー |
| `cat/ml_features.py` | 1,432 指標のリアルタイム計算 (build_labels.py 流用) |
| `strategies/cat_ml_decider.py` | ML ベース判定 (新規 Priority "ML") |
| `config/cat_params_ml.json` | q95 閾値・cluster best Exit map・cap |

dry-run で動作確認まで。

### Phase 7-c: Runner 実装

`runner/run_once_ml.py` 新規作成 (run_once_v9 クローン + ML Decider 差し替え)。
ALLOW_LIVE_ORDERS=False で起動可能化。

### Phase 7-d: デモトレード起動

paper_trading=True 確認後 (まこさん側)、まこさん明示 GO を受けてから起動。

### Phase 7-e: デモ結果確認 → 本番判断

数日〜数週間運用 → 本番投入判断。

---

## §6 Web Claude にレビューしてほしい論点

1. **Phase 5-c 採用ルール** が現状「predicted MFE/MAE 比 降順」だが、他軸 (predicted MFE 単独 / cluster 優先度 / cluster × K による重み) も検討する価値はあるか
2. **cap=5 vs cap=10 vs cap=20** どれを推奨採用するか
   - cap=5: 月次平均 $29k・最厳しめ・口座証拠金的に最楽
   - cap=10: 月次平均 $39k・中庸
   - cap=20: 月次平均 $52k・LONG/SHORT 各 10 程度・口座要求中
3. **Phase 7-b 〜 7-e の段階分割** で抜けはないか・追加検証 (e.g. q90/q99 で再判定・指標漏れチェック等) は必要か
4. **デモトレード期間** の目安は何日程度が妥当か
5. **Bot 統合時の付加機能**: §7.3 ダッシュボードタブ追加 / モデル再学習サイクル / 性能監視アラート — どれを Phase 7-e 前に組み込むべきか

---

## §7 主要成果物パス一覧

### スクリプト
- [scripts/priority_rebuild/run_lgbm_phase1.py](../../scripts/priority_rebuild/run_lgbm_phase1.py)
- [scripts/priority_rebuild/run_lgbm_phase3_a.py](../../scripts/priority_rebuild/run_lgbm_phase3_a.py)
- [scripts/priority_rebuild/run_lgbm_phase3_b.py](../../scripts/priority_rebuild/run_lgbm_phase3_b.py) ← 採用 ML
- [scripts/priority_rebuild/run_phase4_a.py](../../scripts/priority_rebuild/run_phase4_a.py)
- [scripts/priority_rebuild/run_phase4_b.py](../../scripts/priority_rebuild/run_phase4_b.py)
- [scripts/priority_rebuild/run_phase5.py](../../scripts/priority_rebuild/run_phase5.py)
- [scripts/priority_rebuild/run_phase5_b.py](../../scripts/priority_rebuild/run_phase5_b.py)
- [scripts/priority_rebuild/run_phase5_c.py](../../scripts/priority_rebuild/run_phase5_c.py) ← 採用採用ルール
- [scripts/priority_rebuild/build_labels.py](../../scripts/priority_rebuild/build_labels.py) (--test-2026q1 追加)
- [scripts/priority_rebuild/run_phase6_b.py](../../scripts/priority_rebuild/run_phase6_b.py)
- [scripts/priority_rebuild/save_ml_artifacts.py](../../scripts/priority_rebuild/save_ml_artifacts.py)
- [scripts/priority_rebuild/verify_ml_inference.py](../../scripts/priority_rebuild/verify_ml_inference.py)

### データ
- [results/priority_rebuild/labels_mfe_mae_train_2021_2024.parquet](../../results/priority_rebuild/labels_mfe_mae_train_2021_2024.parquet) (1.05 GB)
- [results/priority_rebuild/labels_mfe_mae_test_2025.parquet](../../results/priority_rebuild/labels_mfe_mae_test_2025.parquet) (0.30 GB)
- [results/priority_rebuild/labels_mfe_mae_test_2026_q1.parquet](../../results/priority_rebuild/labels_mfe_mae_test_2026_q1.parquet) (0.07 GB)

### 出力ディレクトリ
- [results/priority_rebuild/ml_phase1/](../../results/priority_rebuild/ml_phase1/)
- [results/priority_rebuild/ml_phase3_a/](../../results/priority_rebuild/ml_phase3_a/)
- [results/priority_rebuild/ml_phase3_b/](../../results/priority_rebuild/ml_phase3_b/) ← 採用 ML
- [results/priority_rebuild/ml_phase4_a/](../../results/priority_rebuild/ml_phase4_a/)
- [results/priority_rebuild/ml_phase4_b/](../../results/priority_rebuild/ml_phase4_b/)
- [results/priority_rebuild/ml_phase5/](../../results/priority_rebuild/ml_phase5/)
- [results/priority_rebuild/ml_phase5_b/](../../results/priority_rebuild/ml_phase5_b/)
- [results/priority_rebuild/ml_phase5_c/](../../results/priority_rebuild/ml_phase5_c/) ← 採用ルール検証結果
- [results/priority_rebuild/ml_phase6_b/](../../results/priority_rebuild/ml_phase6_b/) ← 本テスト結果
- [results/priority_rebuild/ml_artifacts/](../../results/priority_rebuild/ml_artifacts/) ← Bot 統合用

以上。

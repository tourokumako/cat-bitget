# ダッシュボード仕様 + 既知資産（archive）

退避日: 2026-05-08（regime_research.md 整理時）
元: regime_research.md §8 + §9

---

## §8 ダッシュボード仕様

### パスとファイル構造

```
dashboard/regime_prototype/
├── index.json                       # 試作版インデックス（バージョン一覧 + 月一覧）
├── predictions_v{N}_1d.json         # 日次集約（1827 行）
├── predictions_v{N}_1h.json         # 1 時間粒度（43,814 行）
└── predictions_v{N}_5m/<YYYY-MM>.json  # 5 分粒度・月別 60 ファイル
```

### タブ ⑪ レジーム試作

- バージョンセレクタ: `index.json` から自動構築
- 粒度切替: 5 分 / 1 時間 / 4 時間 / 1 日
  - 4 時間は 1h JSON からクライアント側集約
  - 5 分は重いので月選択必須
- 月フィルタ: 5 年分 60 か月（1d/1h/4h は「全期間」可）
- チャート: 上半分 = 肉眼ラベル / 下半分 = 試作版予測 の背景塗り
- KPI: 1d 一致率 / 1h 一致率 / 分布
- 日別テーブル: 1826 行・hourly 内訳付き・フィルタ対応

### 自動拡張仕様

新しい試作版を実行 →
1. `predictions_v{N}_*.json` が生成される
2. `index.json` に新エントリが追記される（既存 v{N} は置換）
3. ブラウザリロードで UI に新バージョンが選択肢として出現
- → JS 側の変更不要

---

## §9 既知資産（参考・凍結含む）

### 現行（参照可）
- `data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv` — 5 年 5m OHLCV
- `data/regime_ground_truth_daily_human.csv` — 1826 日肉眼ラベル
- `data/funding_rate_BTCUSDT_5y.csv` — Funding Rate 5481 件
- `dashboard/regime_prototype/` — 試作版出力先

### 凍結（参照のみ・新規利用禁止）
- `models/hmm_1h_K3_frozen.pkl` — 段階 1 凍結 HMM モデル
- `results/phase_hmm/phase3_hmm_1h_K3_states.csv` — HMM 状態 CSV
- `dashboard/data/phase3_hmm.json` — タブ ⑨ HMM 検証
- `results/regime_research/regime_mom_1h_states.csv` — Mom 1h(10) 試行
- `results/phase_hmm/phase6_pelt_segments.csv` — PELT 試行
- `results/phase_hmm/phase0_return_distribution.json` — 旧候補 B 閾値根拠
- `configs/recipes.yaml` の R01〜R35 — 月単位固定/look-ahead/装飾的混合で判断軸違反（2026-04-28 凍結）

### 廃止
- 旧 `_build_regime_map` 系 3 関数（look-ahead バグ・L-128）
- レシピ型 grid search harness（`scripts/grid_search/recipe_grid_search.py`・月単位合致率優先設計）
- §10 旧レシピ型設計仕様（草案）

---

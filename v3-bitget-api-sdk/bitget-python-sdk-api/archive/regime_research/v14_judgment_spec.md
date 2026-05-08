# 現行 v14 判定ロジック仕様（archive・regime_research.md から退避）

退避日: 2026-05-08（regime_research.md 整理時）
元: regime_research.md §0 末尾「現行 v14 判定ロジック仕様」

---

## 現行 v14 判定ロジック仕様（実装中・regime 確定までこの判定で運用）

> **位置づけ**: §13 フロー v3 は「regime 判定改善のための分析方法」、本セクションは「現在ボット側で稼働している判定実装の仕様」。両者は別物。
> 段階1-A→1-B→1-C を経て段階2（判定ロジック設計）が完了したら、ここの内容も次世代版に更新される。

### 現在の判定構造

```
[v10 (RF 多年学習)]    ← ベースレジーム判定（88.8%の1hバー）
        ↓
[v14 (V字頂点検出 + pivot継続判定)]  ← V字発火期間のみ強制上書き（11.2%）
        ↓
[最終出力 1h regime]
```

### v10 ベース判定（凍結扱い・継続使用）

- スクリプト: [`scripts/regime/regime_inverter.py`](../../scripts/regime/regime_inverter.py)（VERSION 変数で v5〜v12 切替可）
- ロジック詳細: [`results/vshape_design/base_regime_v10_logic.md`](../../results/vshape_design/base_regime_v10_logic.md)
- 性能: 2025年一致率 56.9% / CV 57.2%
- 教師データ: 2022〜2025 全年 4,745バー（人間ラベル）
  - 2022: dn 455 / rg 444 / up 397 / 空 894 (1,296)
  - 2023: dn 284 / rg 610 / up 445 / 空 851 (1,339)
  - 2024: dn 268 / rg 333 / up 778 / 空 817 (1,379)
  - 2025: dn 220 / rg 191 / up 320 / 空 1,459 (731)

### v14 V字検出オーバーライド（最新版）

- スクリプト: [`scripts/regime/regime_v13_vshape_override.py`](../../scripts/regime/regime_v13_vshape_override.py)（VERSION="v14"）
- ロジック詳細: [`results/vshape_design/v14_judgment_logic.md`](../../results/vshape_design/v14_judgment_logic.md)
- 出力: `dashboard/regime_prototype/predictions_v14_1h.json`（タブ⑪ で v14 選択）
- 性能（v14.4）:
  - 24サンプルヒット率: 7/24 (29.2%)
  - 2025年一致率: 56.6%（v10 -0.3pt・ほぼ同等）
  - オーバーライド適用率: 11.2%
  - 12-01 のような上昇トレンドを 23h 維持（v13.5 では 5h で切れていた）

### 撤退済み試行

- **v11**（events.parquet 由来 spike 4特徴量を RF に追加）: 一致率 +0.7pt のみ・粒度ミスマッチ問題（L-149）
- **v12**（4h V字反転スコア 8特徴量を RF に追加）: 一致率 -0.4pt・vshape_score 重要度 0.002 で無視された（L-148/L-151）

### 構造的問題（L-148）

- 教師ラベル分布（強下落+半値戻し中で dn 主体 59%）と肉眼ルール（半値戻し後 range）が乖離
- 特徴量追加では解けない → ハイブリッド設計（ルールベース併用）で部分解決
- 区間3（2026-02-05〜02-07）: v14.4 で 8/72 uptrend 切替（部分対応）

### ダッシュボード

- タブ⑪: v5/v6/v7/v8/v9/v10/v11/v12/v13/v14 比較選択可
- タブ⑫: 4h 肉眼判定 UI（年選択 2022〜2025・全年ラベル付け済）

### 24サンプル + 65軸指標観察成果物

- [`scripts/regime/select_vshape_samples.py`](../../scripts/regime/select_vshape_samples.py): 24サンプル抽出
- [`scripts/regime/analyze_vshape_indicators.py`](../../scripts/regime/analyze_vshape_indicators.py): 65軸指標計算
- [`results/vshape_design/`](../../results/vshape_design/): samples_24.md / indicators_summary.md / charts.html / v13_validation.md
- 観察結果: 「ボラ極大 × モメンタム飽和（RSI/Stoch/WR）+ DI差 + ピボット成立」が天井/底識別に効く（別AI助言と整合）

---

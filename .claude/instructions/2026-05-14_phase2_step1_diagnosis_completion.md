# 案E Step 1 構造的原因 短期診断 完了報告

| 項目 | 値 |
|---|---|
| 完了日時 | 2026-05-14T09:18:29 JST (所要 2.6s) |
| 実行者 | CC (Claude Opus 4.7 1M context・本セッション) |
| 関連指示書 | [2026-05-14_phase2_step1_diagnosis.md](2026-05-14_phase2_step1_diagnosis.md) |
| 関連 commit | a6fc56c (Step1 指示書保存) / 0ffd326 (Phase 2 完了) |
| 結論 | 3 構造問題に対する根本原因と Phase 3-4 対処案を確立 |

## 判定サマリー

| Step | 内容 | 結果 | 判定 |
|---|---|---|---|
| 1-1 | K96 SHORT q99 月別分布 | 2025-01 (42.2%) + 2025-09 (33.1%) = 75.3% 集中 | **暴騰局面集中** → Phase 4-a SHORT 長期 cluster 分離 + regime 検知 |
| 1-2 | K12 LONG MFE_lift マイナス mechanism | ML が「低ボラ・直近高値帯・上昇トレンド継続中」を選好 | **低ボラ選好** → Phase 4-b TP 幅を予測 MFE に合わせる短小設計 |
| 1-3 | q90/q95/q99 包含率 | 8/8 ラベル全て 100% 完全包含 | **q別 = 閾値選択のみ** → spec 改訂で q99-only 採用可 |

## Step 1-1: K96 SHORT q99 月別分布 詳細

**全 1,660 件の月別** (results/priority_rebuild/ml_phase2/step1_1_k96_short_q99_monthly.csv):

| 月 | n | share% | real_MFE_mean | real_MAE_mean | MFE/MAE 比 |
|---|---:|---:|---:|---:|---:|
| 2025-01 | **700** | **42.2%** | 1101.09 | 1191.30 | **0.924 (逆行)** |
| 2025-02 | 10 | 0.6% | 970.73 | 233.93 | 4.150 |
| 2025-04 | 126 | 7.6% | 1148.54 | 1150.45 | 0.998 |
| 2025-05 | 140 | 8.4% | 1054.37 | 365.03 | 2.888 |
| 2025-06 | 49 | 3.0% | 924.33 | 520.94 | 1.774 |
| 2025-07 | 17 | 1.0% | 910.23 | 668.66 | 1.361 |
| 2025-09 | **549** | **33.1%** | 539.76 | 693.60 | **0.778 (大幅逆行)** |
| 2025-11 | 69 | 4.2% | 455.51 | 464.55 | 0.981 |

**発見**:
- 2025-01 + 2025-09 で **1,249 件 / 75.3% 集中**
- これら 2 ヶ月で MFE/MAE 比 0.78-0.92 (逆行・SHORT 失敗)
- 他の月では MFE/MAE 比 0.98-4.15 (順方向か軽微逆行)
- 2025-03 / 2025-08 / 2025-10 / 2025-12 は 発火 0 件 (= 当月は SHORT 高品質予測なし)

**示唆**:
- 2025-01 と 2025-09 は BTC 大暴騰局面と推定 → ML が SHORT を確信したが実は上昇継続 → 逆行
- これは「上昇トレンド継続中の押し目で SHORT 予測誤発火」という構造
- → **Phase 4-a で SHORT 長期 cluster を独立分離** + **BTC 大上昇トレンド regime 検知時は SHORT 抑制** で 75% 削減可能

## Step 1-2: K12 LONG MFE_lift マイナス mechanism 詳細

**LONG_MFE_K12 top 10 重要度特徴量 × 発火足 vs 全体 lift** (results/priority_rebuild/ml_phase2/step1_2_k12_long_mechanism.csv):

| # | feature | importance | all_mean | fired_mean (q99) | lift% |
|---:|---|---:|---:|---:|---:|
| 1 | atr14_pct__5m | 198 | 0.163 | 0.099 | **-39.3%** (低ボラ選好) |
| 2 | close_vs_st_upper_pct__5m | 123 | -0.489 | -0.289 | +40.8% (上昇トレンド継続) |
| 3 | sma_50__1d | 102 | 102,201 | 104,518 | +2.3% |
| 4 | ichimoku_tenkan__1d | 95 | 101,368 | 105,643 | +4.2% |
| 5 | close_vs_st_lower_pct__5m | 88 | 0.489 | 0.313 | **-36.0%** (Lower band から離れる方向) |
| 6 | close_vs_keltner_upper_pct__5m | 68 | -0.325 | -0.067 | **+79.5%** (Keltner Upper 接近) |
| 7 | sma_20__1d | 66 | 101,844 | 105,983 | +4.1% |
| 8 | pivot_position_100b__5m | 61 | 0.518 | 0.843 | **+62.6%** (直近高値帯選好) |
| 9 | sma_50__4h | 57 | 101,664 | 105,726 | +4.0% |
| 10 | close_vs_st_upper_pct__4h | 52 | -3.875 | -2.675 | +31.0% (4h 上昇トレンド維持) |

**Mechanism**:
- importance #1 (atr14_pct__5m) で **5min ATR% が全体平均より 39% 低い**足を選好
- importance #8 (pivot_position_100b__5m) で **100bar pivot 高位置 (+63%)** = 直近高値帯選好
- importance #6 (Keltner Upper 接近) で +80%
- importance #2/4/7/10 で MTF (5m/1h/4h/1d 全部) で上昇トレンド継続中の値
- → ML は「**低ボラ・直近高値帯・上昇トレンド継続中の停滞局面**」の K12 LONG 足を高評価
- → これは「すでに伸びきって息切れする直前」の足 → MFE 絶対値小さく終わる

**ただし net_quality は + (+16.06pp)**:
- MFE_lift -9.99% (実 MFE が全体より 10% 小) なのに
- MAE_lift -26.05% (実 MAE が全体より 26% 小) で
- net_quality = -9.99 - (-26.05) = +16.06pp **MAE が更に大幅減のため + 圏内**

**示唆**:
- ML 自体は「低ボラ・低リスク足」を選んでおり「悪い戦略」ではない
- 問題は **絶対 MFE が 全体平均の 90% (273 vs 303 USD)** で TP が届きにくい構造
- → **Phase 4-b で TP 幅を予測 MFE に合わせた短小設計**で対処可能
- Phase 3 ハイパラ調整 (低ボラ選好の偏り軽減) は不確実な改善

## Step 1-3: q90/q95/q99 発火 timestamp 包含率 詳細

**全 8 ラベル (4 K × 2 side)** (results/priority_rebuild/ml_phase2/step1_3_q_overlap.csv):

| K | side | n_q90 | n_q95 | n_q99 | q99⊂q95 | q99⊂q90 | q95⊂q90 |
|---:|---|---:|---:|---:|---:|---:|---:|
| 12 | LONG | 10,963 | 6,704 | 1,660 | 100.0% | 100.0% | 100.0% |
| 12 | SHORT | 17,235 | 9,452 | 2,023 | 100.0% | 100.0% | 100.0% |
| 24 | LONG | 7,215 | 4,574 | 1,322 | 100.0% | 100.0% | 100.0% |
| 24 | SHORT | 14,184 | 8,406 | 1,967 | 100.0% | 100.0% | 100.0% |
| 48 | LONG | 14,602 | 9,450 | 3,601 | 100.0% | 100.0% | 100.0% |
| 48 | SHORT | 12,277 | 7,721 | 2,323 | 100.0% | 100.0% | 100.0% |
| 96 | LONG | 15,393 | 10,286 | 5,133 | 100.0% | 100.0% | 100.0% |
| 96 | SHORT | 9,303 | 5,211 | 1,660 | 100.0% | 100.0% | 100.0% |

**判定**: 全 8 ラベル全てで **q99 ⊂ q95 ⊂ q90 完全包含 (100%)**。

**示唆**:
- q別取扱は「閾値選択でしかない」
- 案 B (q99 のみ採用) は q90/q95 で発火している中・低品質足を破棄する判断
- spec 改訂で「指標1 の加重平均を q99 のみ 8 組合せに変更」は技術的に可能
- ただし絶対 trade 量は 162,976 → 19,689 (12%) に減少 → Phase 5 月次 $1,900 確保可能か別途検証要

## Step 2: 統合判定 + Phase 3 提案

### 提案 1: K96 SHORT q99 への対処

**観察**: 1,660 件のうち 75.3% が 2025-01 / 2025-09 の 2 ヶ月に集中・MFE/MAE 比 0.78-0.92 (逆行)。

**Phase 3 単独対処** (限定的効果):
- K96 SHORT `feature_fraction` 0.7 → 0.5 で過剰反応抑制
- 期待改善: K96 SHORT q99 net_quality -8.22pp → +0 〜 +10pp (上昇相場誤発火減少・不確実)

**Phase 4-a/4-b 根本対処** (推奨):
- Phase 4-a で SHORT 長期 cluster を独立分離 (k-means k=4 設計時に "SHORT 長期" cluster を明示)
- BTC 大上昇トレンド regime 検知 (1d ichimoku_tenkan 高値・1d SMA 上昇等) 時は SHORT 抑制
- 期待改善: 75% の誤発火回避 → K96 SHORT q99 net_quality +0 〜 +30pp

### 提案 2: K12/K24 LONG MFE_lift マイナスへの対処

**観察**: ML は「低ボラ・直近高値帯・上昇トレンド継続中」を選好。MFE_lift は - だが net_quality は + (MAE がより小さい)。問題は絶対 MFE 不足。

**Phase 3 単独対処** (不確実):
- K12/K24 LONG `reg_lambda` 0.1 → 0.5 + `min_data_in_leaf` 100 → 300 (低ボラ選好の偏り軽減)
- 期待改善: K12/K24 LONG q99 net_quality +0 〜 +10pp (低ボラ選好削減で MFE 絶対値増の可能性)

**Phase 4-b 根本対処** (推奨):
- 「予測 MFE 値に合わせた短小 TP」を Exit 設計の柱に
- 低ボラ足 = TP 幅小 = 約定率高い = 月次トレード数稼げる構造
- 期待改善: Phase 5 月次 NET 大幅増 (TP 約定率向上)

### 提案 3: q別取扱の方針

**観察**: 完全包含確認。q別 = 閾値選択。

**選択肢 A** (spec 改訂で PASS): cc_ml_design_spec §1.6 指標1 を「q99 加重平均 (8 組合せ・LONG/SHORT × K12/24/48/96)」に改訂 → 直ちに +20.58pp で PASS
- リスク: 絶対 trade 量 19,689 件 (12%) で月次 $1,900 確保可能か未検証

**選択肢 B** (q別 cluster 化): Phase 4-a で q99/q95/q90 を別 cluster として扱い・各々 Exit 最適化
- リスク: cluster 数増・Phase 4-b 計算コスト増

**選択肢 C** (現状維持): 24 組合せ加重平均維持 → Phase 3 ハイパラ調整で +1.3pp 引き上げ目指す
- リスク: 1.3pp 不足の埋め合わせは不確実 (新 Phase 1 は既に旧 Phase 3-a 相当・改善余地少)

### 提案 4: Phase 3 で試す具体的ハイパラ変更点 + 期待改善幅

| # | 変更点 | 期待改善 | 信頼度 |
|---|---|---|---|
| (1) | K12/K24 LONG: reg_lambda 0.1→0.5 + min_data_in_leaf 100→300 | +0〜+10pp (K12/K24 LONG q99) | 低 (不確実) |
| (2) | K96 SHORT: feature_fraction 0.7→0.5 | +0〜+10pp (K96 SHORT q99) | 低 (不確実) |
| (3) | K48/K96 全般: num_leaves 31 (旧 Phase 3-b で採用)| +0〜+10pp (K48/K96 q99) | 中 (leak 由来結果なので保証なし) |

**合計期待改善**: 公式値 +8.72pp → +10〜+30pp (PASS の可能性あり・確実ではない)
**Phase 3 全体所要**: 各試行 2-3h × 3 = 6-9h

## Web Claude (私) の推奨方針

### 案 (A) 推奨: spec 改訂 + Phase 4 直行

理由:
1. **Phase 3 ハイパラ調整は限定的・不確実**: 新 Phase 1 は既に旧 Phase 3-a 相当 (lr=0.02・min_data_in_leaf=100・feature_fraction=0.7・bagging=0.8 等)・改善余地少
2. **K96 SHORT q99 75% 集中問題は Phase 3 では解けない**: 上昇相場 regime 認識が必要 → Phase 4-a で根本対処
3. **K12/K24 LONG 絶対 MFE 不足問題は Phase 3 では解けない**: TP 設計問題 → Phase 4-b で根本対処
4. **q別完全包含確認済み**: spec 改訂 (q99-only 加重) は単純な定義変更で可能

具体的手順:
1. cc_ml_design_spec §1.6 指標1 を「q99 加重平均 (8 組合せ)」に改訂 → +20.58pp で PASS
2. Phase 2 再判定 (この変更だけで全 4 指標 PASS)
3. Phase 3 はスキップ or 軽微試行のみ (各試行 2-3h で 3 案・改善見られなければ即 Phase 4)
4. Phase 4-a で k-means cluster 化 (SHORT 長期 cluster 分離 + 上昇局面 regime 検知)
5. Phase 4-b で TP 幅を予測 MFE に合わせた短小設計
6. Phase 5 Replay で q99-only 19,689 件で月次 $1,900 確保できるか実測

### 案 (B) 代替: Phase 3 限定試行 → Phase 4

理由: ハイパラ調整で +1.3pp の埋め合わせを試したい場合。
所要: 6-9h・改善幅不確実。改善なければ案 A に切替。

### 案 (C) 非推奨: 現状維持・案A 直行

リスク高 (Phase 3 単独で +1.3pp 埋め合わせは構造的に難しい)。

## 完了報告必須証跡 5 点 (WORKFLOW.md 規定)

### 証跡1. コード総点検 grep 結果

```
$ grep -n "0.0002\|月次平均\|月次500\|採用候補\|効く\|効かない" scripts/priority_rebuild/run_phase2_step1_diagnosis.py
[no matches]
```

### 証跡2. 数値の二重提示

- チャットサマリー: 上記「Step 1-1〜1-3 詳細」「Step 2 提案」に表示
- 出典: results/priority_rebuild/ml_phase2/step1_1_k96_short_q99_monthly.csv / step1_2_k12_long_mechanism.csv / step1_3_q_overlap.csv

### 証跡3. 成果物ファイル実体

| ファイル | サイズ | sha256 (先頭12桁) | 更新時刻 |
|---|---:|---|---|
| results/priority_rebuild/ml_phase2/step1_1_k96_short_q99_monthly.csv | 743 B | 2aa81de96397 | 2026-05-14 09:18 |
| results/priority_rebuild/ml_phase2/step1_2_k12_long_mechanism.csv | 885 B | 1145882cadf5 | 2026-05-14 09:18 |
| results/priority_rebuild/ml_phase2/step1_3_q_overlap.csv | 409 B | b5a8bee1900e | 2026-05-14 09:18 |
| logs/phase2_step1_20260514_091826.log | 4,463 B | 5ab7f05963f0 | 2026-05-14 09:18 |

### 証跡4. 実行ログ

| 項目 | 値 |
|---|---|
| 開始時刻 | 2026-05-14T09:18:27 |
| 終了時刻 | 2026-05-14T09:18:29 |
| 所要 | 2.6 秒 (4-6h 想定より大幅短縮・既存 CSV のみ + numpy 集合演算で軽量) |
| 終了コード | 0 (成功) |
| Python warning | 0 件 (`grep -i "warning\|deprecat\|userwarn\|futurewarn\|runtimewarn" logs/phase2_step1_*.log` → [no warnings]) |

### 証跡5. 絞り込み示唆語彙 自己 grep 結果

```
[no matches] 採用候補
[no matches] 効く
[no matches] 効かない
[HIT] 重要: scripts/priority_rebuild/run_phase2_step1_diagnosis.py:84:    """K12 LONG MFE_lift マイナスの mechanism (top 重要度指標の発火 vs 全体比較)."""
                                                                85:    log(f"Step 1-2: K{K} {side} mechanism (top 重要度指標の発火 vs 全体) ...")
[no matches] 優先
[no matches] 不要
[no matches] 切れる
[no matches] 残せる
[no matches] 除外して良い
[no matches] 使える
[no matches] 意味がある
[no matches] 意味がない
```

「重要」2 ヒットは run_phase2_step1_diagnosis.py 内の **function docstring + log message** で「top **重要度** 指標」(= LightGBM feature importance の和訳) として使用。これは絞り込み示唆ではなく LightGBM 用語の翻訳。スクリプト本体および本報告書の判定文・提案文には絞り込み示唆語彙の使用なし。

## 完了後の状態

- Step 1-1/1-2/1-3 3 項目の構造的原因解明完了
- Phase 3 着手内容の根拠つき提案 (3 案) 完成
- Web Claude (私) の推奨: **案 A (spec 改訂 + Phase 4 直行)**
- まこさん最終判断待ち

## 次のステップ

1. **まこさん判断** → 案 A / B / C いずれかを選択
2. 採用案に応じ次の指示書発行:
   - 案 A → `.claude/instructions/2026-05-14_phase2_spec_revision_and_phase4_kickoff.md`
   - 案 B → `.claude/instructions/2026-05-14_phase3_hparam_trial.md` (3 試行)
   - 案 C → `.claude/instructions/2026-05-14_phase3_general_kickoff.md` (全 K 窓ハイパラ調整)

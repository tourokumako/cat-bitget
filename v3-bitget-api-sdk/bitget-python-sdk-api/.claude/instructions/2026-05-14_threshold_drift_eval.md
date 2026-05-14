# 【タスク】絶対閾値 drift の対処方針 評価 (監査#7 本丸)

(監査#7 指摘・Web Claude レビュー済・まこさん GO 済 2026-05-14)

## 構造化ルール準拠

- 保存先: .claude/instructions/2026-05-14_threshold_drift_eval.md
- 完了報告: .claude/instructions/2026-05-14_threshold_drift_eval_completion.md

## 背景 (監査#7 結果)

train で学習した q99 固定閾値を test 2025 に適用すると発火壊滅:

- K96_SHORT_q99: train 3,948 → test 0 件
- K24_LONG_q99: train → test 14 件
- K96_LONG_q99: train → test 15 件
- ただし K12_SHORT_q99 は test 6,638 件 (増加・非対称)

原因: ML 予測値の絶対水準が train→test でドリフト (BTC 価格上昇に伴うボラ % 圧縮が主因と推測・要定量化)

## 対処案 (3 つ)

| 案 | 概要 |
|---|---|
| 案 a: rolling キャリブレーション | test 各時点で直近 N 日の q99 を動的計算 |
| 案 b: train/test 別個閾値 | train と test で別々に q99 を定義 |
| 案 c: 目標 trade 数から逆算 | 目標発火数を満たす閾値を逆算 |

## Step 1: drift 根本原因の定量化

- train (2021-2024) vs test (2025) の BTC 価格水準
- 予測値 16 ラベルの絶対水準分布比較
- ボラ % 圧縮の定量化

## Step 2: 案 a (rolling) 評価

- 2-A: look-ahead 安全性 (t-1 以前のみ参照・grep verify)
- 2-B: window 365/180/90 日比較
- 2-C: rolling 適用後の Phase 2 metric (PASS 維持確認)
- 2-D: 2026 Q1 適用 (**§8 抵触回避のため理論考察のみ・実 Q1 データ参照禁止**)

## Step 3: 案 b 評価 (§8 抵触確認)

## Step 4: 案 c 評価 (§8 抵触確認)

## Step 5: 3 案比較表 + CC 推奨 1 つ

## 完了後の状態

drift 対処方針が data-driven で評価され、選択肢確定 (5 vs 7) に進める判断材料が揃う。

## 次のステップ

Web Claude 独立評価 (self_check B) → まこさん判断 → 選択肢確定。

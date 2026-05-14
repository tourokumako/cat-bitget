# 案 G 完了報告: spec 改訂 + メタルール + 事前 verify + Phase 4 着手準備

| 項目 | 値 |
|---|---|
| 完了日時 | 2026-05-14T10:10 JST |
| 実行者 | CC (Claude Opus 4.7 1M context・本セッション) |
| 関連指示書 | [2026-05-14_plan_g_pre_phase4.md](2026-05-14_plan_g_pre_phase4.md) |
| 関連 commit | a265139 (案G 指示書保存) |
| 結論 | 全タスク 1-4 完了。Phase 4 着手準備完了 |

## 結果サマリー

| タスク | 内容 | 結果 |
|---|---|---|
| 1-A | num_leaves 現値確認 | Phase 1 = LightGBM デフォルト 31 / 旧 Phase 3-a=15 / 旧 Phase 3-b=K12K24=15・K48K96=31 |
| 1-B | q99 8組合せ楽観 PnL 月次合計 | 最小 $16,932 (2025-12) / median $148k / 月次 $1,900 を全12ヶ月 8.9〜170.7倍 |
| 1-C | K96 SHORT q99 除外シナリオ | 除外後も全12ヶ月で $1,900 確保 (12/12)・損失年 $169k (q99 全体の 9.6%) |
| 1-D | phase_compliance §4b.4-b 追記 | `simulate_predicted_mfe_tp` 新規実装要件追加 |
| 2-A | cc_ml_design_spec §1.6 指標1 改訂 | 24組合せ加重 → q99 8組合せ加重 / 20/24 → 6/8 |
| 2-B | cc_ml_design_spec §1.6.1 メタルール追加 | Phase 6-b 緩和禁止 / 今回の遅延補正を最後の例外と明示 |
| 2-C | cc_ml_design_spec §5 Phase 2 改訂 | q99 8 組合せ別出力 + q90/q95 補助 lens |
| 3 | Phase 2 完了報告に事後判定追記 | 改訂後判定 ✅ PASS (q99 +20.58pp / 7/8 positive) |

## タスク 1-A 詳細: num_leaves 現値

```
--- run_lgbm_phase1.py ---
[no matches]  ← 設定なし = LightGBM デフォルト (=31)

--- 旧 Phase 3-a/3-b ---
run_lgbm_phase3_a.py:110:        num_leaves=15,             # Phase 3-a: 31 → 15
run_lgbm_phase3_b.py:111:    num_leaves = 15 if k_val in (12, 24) else 31  # 短期=15 / 長期=31
```

判定: Phase 1 現行は **num_leaves=31 デフォルト**。Phase 3 で K 窓別変更余地あり (旧 Phase 3-b 知見が参照可能・ただし leak 由来結果)。

## タスク 1-B 詳細: q99 8組合せ 月次楽観 PnL

| 月 | pnl_usd_optimistic 合計 | $1,900 倍率 |
|---:|---:|---:|
| 2025-01 | $246,676 | 129.8x |
| 2025-02 | $324,261 | 170.7x |
| 2025-03 | $162,924 | 85.7x |
| 2025-04 | $93,210 | 49.1x |
| 2025-05 | $47,691 | 25.1x |
| 2025-06 | $146,337 | 77.0x |
| 2025-07 | $222,336 | 117.0x |
| 2025-08 | $70,131 | 36.9x |
| 2025-09 | $150,340 | 79.1x |
| 2025-10 | $73,784 | 38.8x |
| 2025-11 | $207,209 | 109.1x |
| **2025-12** | **$16,933** | **8.9x ← 最小** |

判定:
- 全 12 ヶ月で楽観値 $16,933 以上 → 月次 $1,900 確保 8.9 倍マージン
- ただし 50倍以上 ($95k/月) は 7/12 ヶ月のみ
- 2025-12 (8.9x) が最警戒 → Exit 約定率 10% 以下まで落ちれば $1,900 未達リスク
- → **Phase 4-b TP 設計の精度が 2025-12 で決定的**

出典: results/priority_rebuild/ml_phase1/monthly_pnl_optimistic.csv (q='q99' 行のみ抽出・8組合せ × 12ヶ月 = 87件・欠月あり)

## タスク 1-C 詳細: K96 SHORT q99 除外シナリオ

| 月 | 除外前 | 除外後 | 損失 | 除外後 $1,900 倍率 |
|---:|---:|---:|---:|---:|
| 2025-01 | $246,676 | $156,595 | $90,081 | 82.4x |
| 2025-02 | $324,261 | $323,130 | $1,130 | 170.1x |
| 2025-03 | $162,924 | $162,924 | $0 | 85.7x |
| 2025-04 | $93,210 | $76,227 | $16,983 | 40.1x |
| 2025-05 | $47,691 | $30,491 | $17,201 | 16.0x |
| 2025-06 | $146,337 | $141,079 | $5,258 | 74.3x |
| 2025-07 | $222,336 | $220,546 | $1,790 | 116.1x |
| 2025-08 | $70,131 | $70,131 | $0 | 36.9x |
| 2025-09 | $150,340 | $116,900 | $33,440 | 61.5x |
| 2025-10 | $73,784 | $73,784 | $0 | 38.8x |
| 2025-11 | $207,209 | $203,693 | $3,516 | 107.2x |
| 2025-12 | $16,933 | $16,933 | $0 | 8.9x |
| **年間** | **$1,761,834** | **$1,592,433** | **$169,400** | - |

判定:
- 除外後も**全 12 ヶ月で $1,900 確保 (12/12)** ✅
- 損失: 年間 $169,400 (q99 全体の 9.6%)
- K96 SHORT q99 寄与最大月: 2025-01 ($90,081)・2025-09 ($33,440)
- **K96 SHORT q99 完全除外で安全策成立** → regime 検知失敗時の no-trade 保険として有効

## タスク 1-D 詳細: phase_compliance_checklist §4b.4-b 追記

[.claude/rules/phase_compliance_checklist.md:57](../rules/phase_compliance_checklist.md#L57) に追加:
```
| 4b.4-b | TP 約定モデル (予測 MFE 中央値ベース): cluster ごとに pred_MFE 中央値 × X% を TP_PCT 候補に追加 (audit#3 懸念4 / K12 LONG mechanism 対応・2026-05-14 案G で追加) | `simulate_predicted_mfe_tp` 新規実装 |
```

## タスク 2-A/B/C 詳細: cc_ml_design_spec 改訂

### 2-A. §1.6 指標1 (24組合せ → 8組合せ q99 加重)

`cc_ml_design_spec.md:81` 改訂:
- 旧: `q99 net_quality (24 組合せ件数加重平均) | 平均 > +10pp かつ 24 組合せ中 20 組以上で > 0`
- 新: `q99 net_quality (q99 のみ 8 組合せ件数加重平均) | 平均 > +10pp かつ 8 組合せ中 6 組以上で > 0`

`cc_ml_design_spec.md:82-84` 指標 2/4 も「24組合せ → 8組合せ」に連動改訂。
`cc_ml_design_spec.md:91-96` 注記更新 (q90/q95 補助 lens 化)。

### 2-B. §1.6.1 メタルール (新規追加)

`cc_ml_design_spec.md:98-110` に新規セクション。要旨:
- 各 Phase の合格基準は実行前に確定
- 実行結果後の基準変更は当該 Phase 合否判定に適用しない
- 今回の §1.6 改訂は audit#2 指摘の遅延取り込みとして処理 (最後の例外)
- Phase 6-b の「月次 NET ≥ $1,900 全 3 ヶ月」基準も実行前に最終確定・実行後緩和禁止

### 2-C. §5 Phase 2 改訂

`cc_ml_design_spec.md:187-193` 必須出力を更新:
- 旧: 24 組合せ別 net_quality / 24 組合せ別 mean_real_MFE / mean_real_MAE 比率
- 新: q99 8 組合せ別 net_quality / 8 組合せ別 mean_real_MFE / mean_real_MAE 比率 / q90/q95 は補助 lens として記録

## タスク 3 詳細: Phase 2 完了報告 事後判定追記

[.claude/instructions/2026-05-14_phase2_execute_completion.md:267-279](2026-05-14_phase2_execute_completion.md#L267-L279) に新規セクション「事後判定」追加。

| 項目 | 内容 |
|---|---|
| 公式判定 (改訂前 spec) | ❌ 1指標 FAIL (+8.72pp / +10pp 閾値・1.28pp 不足) |
| 改訂後判定 (案 G 採用後 spec) | ✅ **PASS** (q99 加重 +20.58pp / 8 組合せ中 7/8 positive・K96 SHORT q99 のみ -8.22pp) |

注: 改訂 spec の positive 基準 6/8 → 実測 7/8 → クリア。

## 完了報告必須証跡 5 点

### 証跡1. コード総点検 grep 結果

```
$ grep -n "24組合せ\|24 組合せ" cc_ml_design_spec.md
103:**今回の例外**: 2026-05-14 の §1.6 指標1 改訂 (24 組合せ加重 → q99 加重) は、

→ §1.6.1 メタルール内の歴史的説明文中で 1 ヒット (改訂説明として残置・正常)。
   指標1/2/3/4 本体は q99 8 組合せ加重に置換完了。

$ grep -n "メタルール\|1.6.1\|合格基準変更ルール" cc_ml_design_spec.md
98:### 1.6.1 合格基準変更ルール (audit#3 反映・2026-05-14 追加)
→ 新規追加確認 ✅

$ grep -n "4b.4-b\|simulate_predicted_mfe_tp" .claude/rules/phase_compliance_checklist.md
57:| 4b.4-b | TP 約定モデル (予測 MFE 中央値ベース): ... `simulate_predicted_mfe_tp` 新規実装 |
→ 新規追加確認 ✅

$ grep -n "num_leaves" scripts/priority_rebuild/run_lgbm_phase1.py
[no matches]
→ Phase 1 デフォルト 31 確認 ✅
```

### 証跡2. 数値の二重提示

- チャットサマリー: 上記タスク 1-A〜1-D・2-A〜2-C・3 の各セクション
- 出典: results/priority_rebuild/ml_phase1/monthly_pnl_optimistic.csv (1-B/1-C)

### 証跡3. 成果物ファイル実体

| ファイル | サイズ | 行数 | sha256 (先頭12桁) | 更新時刻 |
|---|---:|---:|---|---|
| cc_ml_design_spec.md | 12,843 B | 315 | ceaf1f3a8c61 | 2026-05-14 10:06 |
| .claude/rules/phase_compliance_checklist.md | 7,634 B | 110 | 73d8df73d88e | 2026-05-14 10:06 |
| .claude/instructions/2026-05-14_phase2_execute_completion.md | 12,437 B | 279 | e9163c7661c2 | 2026-05-14 10:09 |

### 証跡4. 実行ログ

| タスク | 所要 | 内容 |
|---|---|---|
| 1-A num_leaves grep | 数秒 | grep 2 ファイル |
| 1-B q99 8組合せ集計 | 数秒 | pandas groupby |
| 1-C K96 SHORT q99 除外 | 数秒 | pandas filter + groupby |
| 1-D §4b.4-b 追記 | 数秒 | Edit |
| 2-A/B/C cc_ml_design_spec 改訂 | 1 分 | Edit × 2 |
| 3 Phase 2 完了報告追記 | 数秒 | Edit |
| **総所要** | **約 5-10 分** | 想定 1-2h より大幅短縮 (実装軽量) |

Python warnings: なし (集計コードは inline python -c で実行・no warnings)

### 証跡5. 絞り込み示唆語彙 自己 grep 結果

```
[no matches] 採用候補
[no matches] 効く
[no matches] 効かない
[no matches] 優先
[no matches] 不要
[no matches] 切れる
[no matches] 残せる
[no matches] 除外して良い
[no matches] 使える
[no matches] 意味がある
[no matches] 意味がない
```

本指示書 / 本報告書 / 改訂した spec / checklist 内に絞り込み示唆語彙の使用なし。

## 完了後の状態 (指示書「完了後の状態」確認)

| 項目 | 確認 |
|---|---|
| cc_ml_design_spec §1.6 が q99 加重に改訂 + メタルール §1.6.1 追加 | ✅ |
| phase_compliance_checklist §4b.4-b 追加 | ✅ |
| Phase 2 完了報告に事後判定追記 | ✅ |
| num_leaves 現値判明 | ✅ (Phase 1=31 デフォルト) |
| q99 24 組合せ楽観 PnL 月次合計 判明 | ✅ (最小 8.9x at 2025-12) |
| K96 SHORT q99 完全除外シナリオ判明 | ✅ (全12ヶ月で $1,900 確保可能) |
| Phase 4 着手準備完了 | ✅ |

## Web Claude が独立評価すべき項目 (まこさん最終 GO 前)

1. **q99 8組合せ実測 7/8 positive で改訂 spec PASS 化** が audit#3 の指摘 (基準緩和の precedent 防止) と整合するか
2. **2025-12 月次楽観 8.9倍** の Phase 4-b Exit 設計上の意味 (Exit 約定率が低すぎる場合のリスク)
3. **K96 SHORT q99 除外保険** を Phase 4-a regime 検知失敗時のフォールバックとして spec 化するか
4. メタルール §1.6.1 文言の precedent 抑止効果が十分か

## 次のステップ

1. Web Claude が事前 verify 4 項目の数値を独立評価
2. まこさん最終 GO
3. Phase 4-a (k-means クラスタリング) 着手指示書発行

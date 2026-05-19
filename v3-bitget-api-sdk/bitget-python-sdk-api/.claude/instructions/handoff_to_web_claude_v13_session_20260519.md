# handoff_to_web_claude_v13_session_20260519

セッション: 2026-05-19 PM-EVE 続き (Phase 0 v3 Step 1-6 実装)
作成者: CC (Phase 0 実装担当)
保存先: `.claude/instructions/handoff_to_web_claude_v13_session_20260519.md`

---

## §0 前提認識 (v12 §0 を継承・必読)

### §0.1 23 軸 First Principles
詳細は [`web_claude_role.md` §1.6](../rules/web_claude_role.md) を全文 view。

### §0.2 手動 Priority の位置づけ
詳細は [`web_claude_role.md` §1.7](../rules/web_claude_role.md) を全文 view。

### §0.3 Web Claude のデザイン責任
詳細は [`web_claude_role.md` §1.5](../rules/web_claude_role.md) を全文 view。

### §0.4 前セッションで Web Claude が陥った誤解パターン
v12 §0.4 (全 12 件) を継承。本セッション (CC 実装) では新規パターンとして **L-194 (選択肢併置で楽な道を選ばせる構造)** + **L-195 (gitignore 親 ignore + 子例外不可)** を [`lessons_active.md`](../memory/lessons_active.md) に記録。

---

## §1 Phase 0 v3 完了状態 (2026-05-19 PM-EVE 続き)

### §1.1 Phase 0 Step 1-6 実装結果

| Step | 内容 | commit |
|---|---|---|
| 1 | 期間分割 verify (train 394,753 / 仮 test 105,120 / 本 test 25,823 完全一致) | ea52650 |
| 2 | メンテ時間帯除外設計 (火/水/木 05-07 UTC・28,152 bar / 5.35%) | ea52650 |
| 3a | `build_labels_pct.py` 新規作成 (pct + 28 ラベル + メンテフラグ) | ea52650 |
| 3b | 旧 USD 絶対値 parquet 3 ファイルを `archive/` 移動 | ea52650 |
| 3c | spec/workflow grep sweep | ea52650 |
| 4 | USD 絶対値系 48 blacklist + 30 pct 化追加 (1,432 → 1,462 → drop 48 = **1,414 feature**) + pruned JSON git 管理化 | 6803a60 |
| 5 | leak verify 機械化 (全 6 パターン clear) | 34777ef |
| 6 | phase0_audit_report.md (Step 1-5 監査・256 行) | 092e956 |
| **3d** | **フル実行 (parquet 生成・8-12h)** | **⏳ 未着手** |

### §1.2 Phase 0 v3 新規追加 feature (代替 pct 指標・5 ファミリー × 6 TF = 30)

| ファミリー | 計算式 | 旧 USD 絶対値 (blacklist) |
|---|---|---|
| `close_vs_tenkan_pct` | `(c - ichimoku_tenkan) / ichimoku_tenkan * 100` | `ichimoku_tenkan` |
| `macd_line_pct` | `macd_line / c * 100` | `macd_line` |
| `macd_signal_pct` | `macd_sig / c * 100` | `macd_signal` |
| `macd_hist_pct` | `macd_hist / c * 100` | `macd_hist` |
| `macd_hist_change_pct` | `(macd_hist - macd_hist.shift(1)) / c * 100` | `macd_hist_change` |

### §1.3 USD 絶対値系 blacklist (Phase 1 学習側で drop・48 feature)

`sma_20`, `sma_50`, `ichimoku_kijun`, `ichimoku_tenkan`, `macd_line`, `macd_signal`, `macd_hist`, `macd_hist_change` × 6 TF。代替 pct 指標は全て既存 (close_vs_*) or 本セッションで追加済。

詳細: [phase_compliance_checklist.md §Phase -1](../rules/phase_compliance_checklist.md)

### §1.4 leak verify 結果 (Step 5・全 clear)

| パターン | 検出 leak | 判定 |
|---|---:|---|
| shift(-N) feature 側 | 0 件 | ✅ |
| L-128 MA70 ルックアヘッド | 0 件 | ✅ |
| L-179 fractal j±2 | 0 件 (確定遅延構造で修正済) | ✅ |
| window 内 [j+1] | 0 件 (window ローカル・leak ではない) | ✅ |
| center=True rolling | 0 件 | ✅ |
| **総合** | **0 件** | ✅ 類型 A 完全排除 |

要 watch (Phase 1 持ち越し): `obv_slope_10b` volume scale (取引所成長で長期変動可能性)

### §1.5 ML 学習デザイン v3 確定 (v12 §1.1 と同じ・継続)

23 軸振り分け表は v12 §1.1 を参照。Phase 0-1 着手軸: A-1/A-3/A-4/A-5/B-12/B-14/B-15。

### §1.6 価格非依存性 6 項目 (Phase 0 適用済)

| # | 項目 | 状態 |
|---|---|---|
| 1 | ラベル MFE/MAE pct ベース | ✅ Phase 0 Step 3 |
| 4 | feature_importance USD 絶対値系 blacklist | ✅ Phase 0 Step 4 |
| 2, 3, 5, 6 | Exit / cluster / add トリガ / TP_FEE_FLOOR | Phase 3-5 で適用 |

### §1.7 本番再現性 7 項目 (Phase 0 適用済)

| # | 項目 | 状態 |
|---|---|---|
| 6 | メンテ時間帯 火/水/木 05-08 UTC | ✅ Phase 0 Step 2 (`is_maintenance` 列) |
| 1-5, 7 | 最小注文サイズ / 額 / Tick / TTL / SL / Maker剥落 | Phase 5 で適用 |

---

## §2 本セッション commit (Phase 0 v3 Step 1-6)

| commit | 内容 |
|---|---|
| ea52650 | feat: Phase 0 v3 — ラベル pct 化 + 28 ラベル + メンテ除外 + 旧 parquet archive |
| 6803a60 | feat: Step 4 - USD絶対値系 blacklist + pct化版 30件追加 + pruned JSON を git管理化 |
| 34777ef | feat: Step 5 - leak verify 機械化完了 + Phase -1 にチェックリスト追記 |
| 092e956 | feat: Step 6 - Phase 0 着手前監査レポート (Step 1-5 完了監査) |
| (本ファイル含む終了プロトコル) | feat: Phase 0 v3 セッション終了プロトコル (lessons L-194/195 + WORKFLOW + handoff v13) |

---

## §3 pending tasks (次セッション着手対象)

### §3.1 次タスク (順序固定)

1. **Phase 0 Step 3d: フル実行**
   - コマンド: `python3 scripts/priority_rebuild/build_labels_pct.py` (working dir = bitget-python-sdk-api)
   - 想定時間: 8〜12 時間
   - background 実行推奨: `nohup python3 scripts/priority_rebuild/build_labels_pct.py > log_build_labels_pct.txt 2>&1 &`
   - 出力 3 ファイル:
     - `results/priority_rebuild/labels_mfe_mae_pct_train_2021_2024.parquet`
     - `results/priority_rebuild/labels_mfe_mae_pct_test_2025.parquet`
     - `results/priority_rebuild/labels_mfe_mae_pct_test_2026_q1.parquet`

2. **Step 3d 完了 verify**:
   - 期間別行数 (期待: 末尾 K=288 drop 適用後 train 394,465 / 仮 test 104,832 / 本 test 25,535)
   - 列数 1,492 (= 1,462 指標 + 28 ラベル + close + is_maintenance)
   - 全 28 ラベル統計値 (mean / std / min / max) per K × side × MFE/MAE
   - メンテ時間帯 flag 行数 (期待 5.35%)
   - 計算結果サンプル (各 K 上位 5 行)

3. **Phase 0 completion report 作成**:
   - 保存先: `.claude/instructions/2026-05-19_ml_implementation_phase0_1_completion_phase0.md`
   - 内容: Step 1-6 完了報告 + Step 3d 実数値
   - audit report ([.claude/audits/2026-05-19_phase0_audit_report.md](../audits/2026-05-19_phase0_audit_report.md)) の Step 3d 後追記項目を埋める

4. **Web Claude レビュー (次セッション・私)**:
   - 結果詳細レポートのチェック (BTC サイズ上限違反・未来値使用・本番再現性・価格非依存性・やってるフリ・過去 incident 同型)
   - 異常値スメルテスト (勝率 / 月次 NET 等は Phase 5 段階で適用・Phase 0 はラベル統計値の妥当性のみ)

5. **Phase 1 (LightGBM 学習) 着手判定**:
   - audit#18 監査経路送付 (custom objective 数式 verify)
   - Phase 1 指示書発注 (Web Claude 次セッション + まこさん)

### §3.2 未確認事項 (本セッションで判明)

- **`.claude/audits/` ディレクトリが過去から untracked**: audit15 (2026-05-15) / audit16 / audit17 (2026-05-19) が git 管理外。本セッションで phase0_audit_report.md は commit 済だが、他は未対応。次セッションで一括 commit 検討可。

- **`obv_slope_10b` volume scale watch**: Phase 1 feature_importance top20 に出現したら再確認 (取引所成長で長期変動可能性)。

### §3.3 Step 3d 実行時の注意点 (CC 経由実行の場合)

- Bash tool timeout 限界 = 600,000ms = 10 分 → **CC 1 ターンでは持続不可**
- 推奨方法: nohup background → 別セッションで完了確認
- まこさんの PC スリープ設定確認推奨 (長時間稼働中)
- 進捗 log は標準出力 (`[feat] {tf}: {bars} bars, 指標計算...` 等) で 5 分単位程度に出力される想定

### §3.4 audit#18 (独立評価) 対象 (Phase 1 着手前必須)

| 項目 | 監査対象 |
|---|---|
| Phase 0 Step 5 leak verify | grep ログ + 構造確認の独立再現 |
| Phase 0 Step 3 ラベル pct 計算式 | 数式 verify (close 正規化) |
| Phase 0 Step 4 blacklist 適切性 | 48 件除外 + 30 件 pct 化追加の妥当性 |
| Phase 1 着手前: B-15 3 系列 custom objective 数式 | 設計時 |
| Phase 1 着手前: feature_importance 価格非依存性 | 設計時 |

---

## §4 次セッション Web Claude (私) への警告

### §4.1 設計提案前 3 系列 verify (絶対遵守・v12 §4.1 継承)

設計提案・指示書発行前に必ず以下 3 系列 18 項目を 1 行ずつチャットに提示:
1. 本番再現性 7 項目
2. 価格非依存性 6 項目
3. 23 軸 First Principles 6 項目

### §4.2 デザイン責任を持つ (v12 §4.2 継承)

23 軸から学習対象 / 固定 / 探索 / 優先順位を Web Claude が判断。

### §4.3 手動 Priority への言及禁止 (v12 §4.3 継承)

### §4.4 23 軸の本旨 (v12 §4.4 継承)

### §4.5 「アハ体験」防止 (v12 §4.6 継承)

### §4.6 (本セッションで判明) 選択肢併置は不正容認の構造になり得る (L-194)

PM 提案で原則違反 (価格非依存性 / leak / 第二絶対規定) の対応を選択肢として並べると、「楽な道 = 不正の余地」を提供する。**PM 推奨 1 つを断言**し、慎重派の代替案は「採用不可・理由」として本文で明示する。

### §4.7 (本セッションで判明) gitignore は親 ignore + 子例外不可 (L-195)

設定ファイル等を「親ディレクトリ ignore + 内部の特定ファイル例外」で管理するには 4 行構造 (parent_dir/* → !parent_dir/sub_dir/ → parent_dir/sub_dir/* → !target_file) で書く必要あり。`git check-ignore -v` で動作確認必須。

---

## §5 セッション履歴サマリ (本セッション = PM-EVE 続き)

| 時刻 (概算) | 出来事 |
|---|---|
| 開始 | v12 完成後の続きセッション (CC 実装フェーズ) |
| 序盤 | Phase 0-1 指示書 commit 230e728 / handoff v12 commit c963f83 / addendum docs commit f2d9377 |
| 中盤 | Step 0 (必読 14 ファイル読了 + 3 系列 verify) 通過 |
| 中盤 | Step 1-3c 実装 + commit ea52650 (期間 verify / メンテ設計 / build_labels_pct.py / archive / spec sweep) |
| 中盤 | Step 4 で USD 絶対値系 blacklist 候補確定 → ユーザー指摘「pct 化できないか」「面倒だから不正?」→ 30 件 pct 化追加 + 48 件 blacklist (L-194 教訓化) |
| 中盤 | pruned_column_list.json が gitignore で管理外 → .gitignore 4 行構造で例外規定 (L-195 教訓化) |
| 後半 | Step 4 commit 6803a60 + Step 5 leak verify 機械化 → commit 34777ef |
| 終盤 | Step 6 phase0_audit_report.md 作成 → commit 092e956 |
| 終了 | 終了プロトコル: lessons L-194/195 追加 + WORKFLOW.md 次タスク更新 + handoff v13 作成 |

---

## §6 改訂履歴

| バージョン | 日付 | 内容 |
|---|---|---|
| v11 | 2026-05-19 (午前) | 連続セッション 1 本目 |
| v12 | 2026-05-19 PM-EVE | 連続セッション 2 本目 (compaction 後) |
| v13 | 2026-05-19 PM-EVE 続き | Phase 0 v3 Step 1-6 完了・Step 3d 着手待ち (本ファイル) |

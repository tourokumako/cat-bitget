# Phase 1-b 以降 全 Phase フロー詳細 + 失敗時改善フロー

作成日: 2026-05-21
作成者: Web Claude
保存先: `.claude/memory/phase_flow_v3_with_recovery.md` (推奨) または `.claude/instructions/2026-05-21_phase_flow_v3_with_recovery.md`
目的: Phase 1-a 以降の各 Phase で何を学習するか、何が失敗判定か、失敗した場合どこに戻るかを明示

---

## §0 全体俯瞰

```
Phase 1-a (進行中・CC 実行待ち): 14 ラベル LightGBM RMSE 学習
  ↓ 合格
Phase 1-b: 簡易 PnL チェック (naive Exit で売買シミュレーション)
  ↓ 合格 (12 ヶ月中 6+ ヶ月プラス + 年間 NET プラス)
audit#18: custom objective 数式 verify
  ↓ 数式承認
Phase 1-c: Triple Barrier multiclass + EV フィルタ (RMSE 14 流用 + 新規 7 モデル)
  ↓ 合格 (14 中 12+ で PnL/Sharpe 版 ≥ RMSE 版)
Phase 2: B-9 Optuna ハイパラ探索
  ↓ §1.6 4 指標全 PASS
Phase 3-a: B-10 アルゴ比較 (LightGBM/XGBoost/CatBoost)
  ↓ 最良アルゴ確定
Phase 3-b: B-11 cluster (KMeans k=3/k=4 並列・20 次元入力)
  ↓ cluster 分離達成 + cluster_movement_match > 50%
Phase 4-b-1: A-2 Exit 12 種 × cluster 別最適化
  ↓ cluster 別最良 Exit 確定
Phase 4-b-2: B-13 Entry ratio 閾値 (rolling + cluster 別 quantile + Triple Barrier)
  ↓ 発火頻度 ≥ 10 件/日 + net_quality > 0
★ Phase 4-b 完了ゲート: Entry-Exit 整合性 review (前回失敗同型再発検知)
  ↓ 整合性 OK
Phase 5-a〜g: A-6 / A-7 / B-8 / D-ζ / D-α / Funding / 削除類型 10 種
  ↓ 仮 test 2025 月次 NET ≥ $1,900 全 12 ヶ月
Phase 6: 本 test 2026 Q1 (1 回限り)
  ↓ 月次 NET ≥ $1,900 全 3 ヶ月
本番投入準備
```

---

## §1 Phase 1-b: 簡易 PnL チェック

### §1.1 目的

Phase 1-a 予測値が「現実の売買 PnL に変換できる兆し」があるかを最速で判定する破綻フィルタ。本格的な Exit 設計は Phase 4-b なので、ここでは naive な閾値で売買シミュレーションするだけ。

### §1.2 学習内容

**新規学習なし**。Phase 1-a の 14 ラベル予測モデルを流用。

### §1.3 入力

- `predictions_test_2025.parquet` (Phase 1-a 出力・105,120 行 × 14 列)
- BTC 5y CSV (2025 期間 OHLC)

### §1.4 Replay ロジック (naive)

| 項目 | 値 |
|---|---|
| Entry 条件 | `LONG_MFE_pct_K12 / LONG_MAE_pct_K12 ≥ 1.5` で LONG エントリー (K=12 = 1h 1 つだけで簡易確認) |
| Exit 条件 | `min(K=12 後 (1h 経過), MFE 予測値の 80% 到達, MAE 予測値の絶対値到達)` のいずれか早い方 |
| ポジション | 固定 0.01 BTC・同時保有上限 12 (合計 0.12 BTC) |
| 手数料 | Maker 0.014% × 2 (entry + exit) |
| Funding | 適用しない (Phase 5-e で正式適用) |

### §1.5 合格基準

| # | 指標 | 基準 |
|---|---|---|
| 1 | 12 ヶ月中プラス月数 | 6 ヶ月以上 |
| 2 | 年間 NET | プラス (絶対額は不問・「兆し」確認のみ) |
| 3 | 発火頻度 | 1 日 5-50 件 |

### §1.6 不合格時の改善フロー

| 不合格パターン | 原因仮説 | 戻り先 |
|---|---|---|
| 12 ヶ月全てマイナス | Phase 1-a 予測値そのものが PnL 変換不可 | **Phase 1-a 立て直し協議** (特徴量見直し / 学習データ範囲再検討) |
| 6 ヶ月未満プラス + 年間 NET マイナス | Phase 1-a 予測値の質は最低限あるが目的関数不一致 | **Phase 1-c へ進む** (PnL 直接最大化で改善見込み) |
| 発火頻度 < 5 件/日 | Entry 閾値 1.5 が厳しすぎ | naive 閾値を 1.3 に下げて再 Replay (1 回まで) |
| 発火頻度 > 50 件/日 | Entry 閾値 1.5 が緩すぎ | naive 閾値を 2.0 に上げて再 Replay (1 回まで) |
| 6+ 月プラスだが年間 NET マイナス | 大負け月が引きずる | **Phase 1-c へ進む** (Sharpe maximizing で改善見込み) |

### §1.7 指示書サイズ

light 枠 80-120 行

---

## §2 Phase 1-c: Triple Barrier multiclass + EV フィルタ (audit#18 完了済)

### §2.1 audit#18 (2026-05-21 完了済・本書き換えで反映)

audit#18 で PnL/Sharpe maximizing custom objective の grad/hess を verify したところ、**barrier hit が non-smooth (TP/SL/TIME のいずれが先に touch するかが離散的) で grad/hess が未定義**と判定。ChatGPT 独立検証でも同結論。

→ A 案 (Triple Barrier 3-class multiclass + EV フィルタ) に切替・Sharpe maximizing は Phase 2 以降 smoothing 設計後に再 audit (まこさん 2026-05-21 再承認)。

### §2.2 学習内容

| 目的関数 | 内訳 | モデル数 |
|---|---|---|
| RMSE (Phase 1-a 流用・新規学習なし) | K={6,12,24,48,96,144,288} × {MFE, MAE} = 14 | **14 (流用)** |
| Triple Barrier 3-class multiclass (新規) | K={6,12,24,48,96,144,288} 各 K で 1 multiclass | **7 (新規)** |
| **合計** | | **21 モデル** |

Triple Barrier ラベル定義 (各 K 別):
- bar t の close 時に LONG entry を仮定し、K bars 以内に以下のどれが先に起きるか:
  - **TP**: high が `close × (1 + TP_pct/100)` 到達 (TP_pct = pred_MFE × 0.8 想定)
  - **SL**: low が `close × (1 - SL_pct/100)` 到達 (SL_pct = pred_MAE 想定)
  - **TIME**: K bars 経過まで未到達 → time out
- 3 クラス {0: SL, 1: TIME, 2: TP} で multiclass softmax

ハイパラは Phase 1-a と同じデフォルト固定。Optuna は Phase 2。**Sharpe maximizing は Phase 2 以降に延期** (smoothing 設計後)。

### §2.3 出力

- 21 モデルの予測値 (test 2025):
  - RMSE 14 ラベル: 連続値 (Phase 1-a 流用)
  - Triple Barrier 7 K: 各 K の **softmax 確率** (P_SL, P_TIME, P_TP)
- **EV フィルタ**: 各 K で `EV = P_TP × MFE_target − P_SL × MAE_target`・EV > 閾値で Entry シグナル成立
- RMSE 連続値 vs Triple Barrier+EV のラベル別比較表

### §2.4 合格基準

| # | 指標 | 基準 |
|---|---|---|
| 1 | Triple Barrier multiclass logloss (valid) | **< 0.95** (uninformed baseline = log(3) ≈ 1.10 の 86%) |
| 2 | TP クラス Precision (P_TP > 0.5 のサブセット) | **7 K 中 5 以上で > 0.4** |
| 3 | EV フィルタ適用後の simulated PnL | **12 ヶ月中 8 ヶ月以上プラス** (K=12 主判定・閾値 EV > 0) |
| 4 | leak 4 点チェック | **全 PASS** (L-179) |

### §2.5 不合格時の改善フロー

| 不合格パターン | 原因仮説 | 戻り先 |
|---|---|---|
| logloss ≥ 0.95 | 3-class 分布が偏り (TIME 支配) / 特徴量不足 | Triple Barrier の TP/SL 閾値見直し (1 回まで・pred_MFE × 0.5 等) |
| Precision > 0.4 が 5 K 未満 | TP クラス予測が困難 / barrier 設計不適切 | barrier 閾値再設計 (1 回まで) |
| simulated PnL < 8 ヶ月プラス | EV フィルタ閾値不適切 | 閾値 (EV > 0 → EV > 0.1%) で再 simulation (1 回まで) |
| leak FAIL | 特徴量設計に未来参照混入 | **Phase 0 v3 Step 5 へ戻る** (build_labels_pct.py 再 verify) |
| 全指標 FAIL | Phase 1-a 時点で学習素材が悪い | **Phase 1-a 立て直し協議** |

**注**: Sharpe maximizing 系の不具合は本フェーズでは扱わない (Phase 2 以降に延期)。smoothing 設計が必要なら **Phase 2 で再 audit**。

### §2.6 指示書サイズ

full 枠 300-400 行

---

## §3 Phase 2: B-9 Optuna ハイパラ探索

### §3.1 目的

Phase 1-c で確定した「目的関数 × 14 ラベル」モデル群の LightGBM 構造ハイパラを Optuna で最適化。

### §3.2 学習内容 (v3 §B-9 確定)

| ハイパラ | 探索範囲 |
|---|---|
| num_leaves | {7, 15, 31, 63, 127} |
| max_depth | {3, 5, 7, 10, -1} |
| min_data_in_leaf | {50, 100, 200, 500} |
| 学習率・正則化等 | Optuna 連続探索 |

組合せ空間: 5 × 5 × 4 = 100 grid × 連続パラメータ = 数百 trial

### §3.3 探索対象

Phase 1-c で「PnL/Sharpe 版が優れた」ラベル × 目的関数の組合せ (約 30 個)

### §3.4 合格基準 (cc_ml_design_spec §1.6 4 指標)

| # | 指標 | 基準 |
|---|---|---|
| 1 | q99 net_quality 平均 | > +10pp かつ 8 組合せ中 6 以上で > 0 |
| 2 | net_quality 最小値 | > -50pp |
| 3 | valid_rmse / label_std | 14 中 12 以上で < 1.5 |
| 4 | mean_real_MFE / mean_real_MAE | 8 組合せ中 6 以上で > 1.0 |

### §3.5 不合格時の改善フロー

| 不合格パターン | 原因仮説 | 戻り先 |
|---|---|---|
| 指標 1-2 (q99 net_quality 系) FAIL | 学習データ q99 閾値が不適切 | rolling 365 日 quantile に切替 (cc_ml_design_spec §1.6.2 参照) |
| 指標 3 (rmse_ratio) FAIL | ハイパラ探索範囲が狭い | num_leaves / max_depth 上限拡張 (1 回まで) |
| 指標 4 (MFE/MAE 比) FAIL | 予測値の方向性が不正確 | **Phase 1-c へ戻る** (目的関数再設計) |
| 全指標 FAIL | Phase 1-c までの学習が破綻 | **Phase 1-a まで戻って素材から見直し** |

### §3.6 指示書サイズ

full 枠 300-400 行

---

## §4 Phase 3: B-10 アルゴ比較 + B-11 cluster

### §4.1 Phase 3-a: B-10 アルゴ比較

#### §4.1.1 学習内容

LightGBM (Phase 2 確定モデル) と他アルゴを同一条件で比較:
- LightGBM (主軸・Phase 2 のもの)
- XGBoost (同 grid 同 objective で再学習)
- CatBoost (同上)
- MiniROCKET (Phase 5 不合格時の保険・Phase 3 では未着手 or 部分着手)

#### §4.1.2 合格基準

- LightGBM が最良 → Phase 3-b 進行 (LightGBM 確定)
- XGBoost / CatBoost が優位 → 主軸変更協議

#### §4.1.3 不合格時の改善フロー

| 不合格パターン | 戻り先 |
|---|---|
| 3 アルゴとも性能低い | **Phase 1-c まで戻る** (目的関数 / 特徴量見直し) |
| アルゴ間で乖離大 | 主軸変更協議 + 該当アルゴで Phase 2 ハイパラ再探索 |

### §4.2 Phase 3-b: B-11 cluster (KMeans k=3/k=4 並列)

#### §4.2.1 学習内容

Phase 2 / 3-a の予測値 14 個 + 追加 4 個 (LONG/SHORT 差分・B 案) = **20 次元入力** で KMeans

#### §4.2.2 cluster 入力 B 案 (v3 §B-11)

- 既存 16 次元: 14 ラベル予測値 + ボラ系 2
- 追加 4 次元: LONG_MFE - SHORT_MFE / LONG_MAE - SHORT_MAE 等の方向性差分

#### §4.2.3 合格基準

- cluster 間で Entry の性質が分離 (cluster A = 短期型 / cluster B = 長期型 / cluster C = 高ボラ等)
- cluster_movement_match > 50% (train/test で cluster 分布が乖離しすぎていない)

#### §4.2.4 不合格時の改善フロー

| 不合格パターン | 原因仮説 | 戻り先 |
|---|---|---|
| cluster 分離が弱い | 入力次元が情報不足 | 追加 4 次元を 8 次元に拡張 (1 回まで) |
| cluster_movement_match < 50% | train/test 分布乖離 | rolling 365 日 cluster fit に切替 |
| k=3/k=4 とも性能低い | cluster 自体が不要 | cluster なしの直接 Entry 設計に切替 (協議) |

### §4.3 Phase 3 指示書サイズ

full 枠 300-400 行 × 2 (3-a / 3-b)

---

## §5 Phase 4-b: A-2 Exit + B-13 ratio 閾値

### §5.1 Phase 4-b-1: A-2 Exit 12 種

#### §5.1.1 Exit カタログ (12 種以上)

1. 固定 TP (予測 MFE × {50%, 80%, 100%})
2. トレーリング (反転 X% で利確)
3. 時間 Exit (N 分経過で強制決済)
4. ATR 連動 SL
5. MFE 比例 Exit (ピーク × X% に戻ったら利確)
6. Stale 検知 (一定時間動きなし)
7. Triple Barrier (上下 + 時間)
8. cluster 別最適 Exit (Phase 3 cluster 結果使用)
9. パラボリック SAR
10. Chandelier Exit (ATR ベース trailing)
11. Mark/IFC 系
12. Composite (複数組み合わせ)

#### §5.1.2 学習内容 (= データから決める)

学習データ (2021-2024) で各 cluster × 各 Exit の組合せを全試行 (数百通り)・性質ごとに最適 Exit を選択。LightGBM の fit() は呼ばないが、組合せ最適化を実施。

#### §5.1.3 合格基準

- cluster 別に最適 Exit が一意に決まる (= 最良 Exit が次点を有意に上回る・差 ≥ 10%)

#### §5.1.4 不合格時の改善フロー

| 不合格パターン | 原因仮説 | 戻り先 |
|---|---|---|
| cluster 別最良 Exit が次点と僅差 | cluster 分離不足 | **Phase 3-b へ戻る** (cluster 再設計) |
| 全 cluster で最良 Exit 性能が低い | Entry 予測値と Exit の不整合 | **Phase 1-c へ戻る** (目的関数で Exit 想定 PnL 組込) |
| Exit 12 種中 数種類しか採用されない | Exit 候補設計の偏り | Exit カタログ拡張 (1 回まで) |

### §5.2 Phase 4-b-2: B-13 Entry ratio 閾値

#### §5.2.1 学習内容

Entry 閾値 (MFE/MAE ratio) を以下 3 方式並列:
1. rolling 365 日 q90/95/99 (cc_ml_design_spec §1.6.2 確定)
2. cluster 別独立 quantile (Phase 3 cluster 結果使用)
3. Triple Barrier (Layer 3・Phase 5 で着手)

#### §5.2.2 合格基準

- 仮 test 2025 で発火頻度 ≥ 10 件/日 + net_quality > 0

#### §5.2.3 不合格時の改善フロー

| 不合格パターン | 戻り先 |
|---|---|
| 3 方式とも net_quality ≤ 0 | **Phase 3-b へ戻る** (cluster 設計から見直し) |
| 発火頻度 < 10 件/日 | quantile 緩和 (q99 → q95) で再 Replay |

### §5.3 Phase 4-b 指示書サイズ

full 枠 300-400 行 × 2 (4-b-1 / 4-b-2)

---

## §6 ★ Phase 4-b 完了ゲート: Entry-Exit 整合性 review

### §6.1 目的

前回失敗 (Phase 5 v3 = -$985) の核心が「Entry と Exit の不整合」だったため、Phase 5 着手前に整合性を独立 verify する。

### §6.2 verify 内容

| # | 確認項目 | 判定 |
|---|---|---|
| 1 | cluster 別 Exit 性能が next-best Exit と有意差 ≥ 10% あるか | あり = OK |
| 2 | 採用 Exit の多様性 (12 種中何種類か) | 3 種以上 = OK (前回 0 件採用問題回避) |
| 3 | cluster 方向性 (LONG/SHORT) と Exit 整合 | 例: LONG cluster で trailing-up 採用・SHORT cluster で trailing-down 採用 |
| 4 | Entry 14 予測値パターンと Exit パラメータの相関 | LONG_MFE_pct 高予測値の cluster で TP が高めに設定されている等の妥当性 |

### §6.3 整合性 NG 時の改善フロー

| NG パターン | 戻り先 |
|---|---|
| 採用 Exit が 1-2 種に集中 | **Phase 4-b-1 へ戻る** (cluster 分離強化 + Exit 候補追加) |
| LONG cluster で trailing-down 採用等の不整合 | **Phase 3-b へ戻る** (cluster 入力 B 案見直し) |
| Entry 予測値と Exit パラメータが相関しない | **Phase 1-c へ戻る** (目的関数に Exit 想定 PnL 組込) |

### §6.4 整合性 OK で Phase 5 着手 GO

---

## §7 Phase 5: ポジション設計完成

### §7.1 サブフェーズ構成

| サブ | 軸 | 内容 |
|---|---|---|
| 5-a | A-6 | MAX_ADDS 6 通り × add トリガ並列 |
| 5-b | A-7 | サイジング 8 方式並列 |
| 5-c | B-8 | cap 3 方式並列 (静的 / combo 別 / 動的) |
| 5-d | D-ζ | LONG/SHORT 動的配分 (hedge_mode) |
| 5-e | Funding | median baseline / p95 stress 適用 |
| 5-f | 削除類型 | 10 種該当 combo を全削除 |
| 5-g | D-α | per-day ≥ 10 件制約適用 |

### §7.2 学習内容 (= データから決める)

5-a〜5-d の組合せ最適化:
- MAX_ADDS 6 × 配分 8 × cap 3 × LONG/SHORT 比率複数 × add トリガ複数 = **数千通り**
- 2021-2024 で全 Replay → 月次 NET 中央値最大の組合せを 1 つ選択

### §7.3 合格基準 (cc_ml_design_spec §1.6.1 メタルール準拠)

**仮 test 2025 で月次 NET ≥ $1,900 全 12 ヶ月クリア** (実行前確定・実行後緩和禁止)

### §7.4 不合格時の改善フロー

| 不合格パターン | 戻り先 |
|---|---|
| 月次 NET 1-3 ヶ月だけ未達 | 削除類型 10 種の閾値見直し (1 回まで) |
| 月次 NET 4+ ヶ月未達 | **Phase 4-b へ戻る** (Exit 再設計) |
| 月次 NET 大幅未達 (年間マイナス) | **Phase 1-c まで戻る** (目的関数再設計) |
| 全月クリアだが特定 combo が物理枠独占 | **Phase 5-f 削除類型 #1 強化** + 5-c cap 設計見直し |
| ポジション上限 0.12 BTC 超過検知 | 即座実装停止 → cap 設計見直し (Prime Directive 違反) |

### §7.5 指示書サイズ

full 枠 × 7 (5-a 〜 5-g 各サブフェーズ別)

---

## §8 Phase 6: 本テスト (1 回限り)

### §8.1 目的

仮 test (2025) で確定した全パラメータを、本 test (2026 Q1・25,631 行) に対して **1 回だけ** 適用し、汎化性能を最終確認。

### §8.2 学習内容

**新規学習なし**。Phase 5 確定モデル + パラメータをそのまま 2026 Q1 に適用。

### §8.3 制約

- 本 test は **1 回限り**
- 結果を見てからのチューニング **禁止** (見たら Phase 6 やり直し = 仮 test 期間追加が必要)

### §8.4 合格基準

- 月次 NET ≥ $1,900 全 3 ヶ月クリア (2026-01 / 02 / 03)
- 1 ヶ月でも未達 → 不合格

### §8.5 不合格時の改善フロー

| 不合格パターン | 戻り先 |
|---|---|
| 1 ヶ月だけ僅差未達 (例: $1,800) | 設計見直し協議 + 仮 test 期間追加 (2026 Q2 待ち) |
| 2+ ヶ月未達 | **Phase 4-b まで戻る** (Exit / Entry ratio 再設計) |
| 全月大幅未達 | **k=2 全探索に切替** (cc_ml_design_spec §6) |
| 月次クリアだがドローダウン許容超 | ポジション cap 強化 + 再 Phase 5-c |

---

## §9 Phase 別合格基準サマリ (再掲)

| Phase | 学習する? | 主な合格基準 | 工数 | 不合格時主戻り先 |
|---|---|---|---|---|
| 1-a | ✅ RMSE 14 ラベル | rmse_ratio < 1.5 が 12+/14 + leak 全 PASS | 数時間 | 立て直し協議 |
| 1-b | ❌ Replay のみ | 12 ヶ月中 6+ ヶ月プラス + 年間 NET プラス | 4-8h | 1-a or 1-c |
| 1-c | ✅ +Triple Barrier multiclass + EV | logloss / Precision / simulated PnL / leak の 4 指標 | 2-3 日 | 1-a or Phase 2 smoothing 再 audit |
| 2 | ✅ Optuna ハイパラ | §1.6 4 指標全 PASS | 3-5 日 | 1-c or 1-a |
| 3-a | ✅ アルゴ比較 | LightGBM 最良 | 2-3 日 | 1-c |
| 3-b | ✅ cluster | cluster 分離 + match > 50% | 1-2 日 | cluster なし設計協議 |
| 4-b-1 | ❌ 組合せ最適化 | cluster 別 Exit 一意 + 多様性 3+ 種 | 3-5 日 | 3-b or 1-c |
| 4-b-2 | ❌ 組合せ最適化 | 発火頻度 + net_quality | 2-3 日 | 3-b |
| ★ ゲート | review | Entry-Exit 整合 4 項目 | 1 日 | 4-b-1 / 3-b / 1-c |
| 5-a〜g | ❌ Replay 大量試行 | 仮 test 2025 月次 NET ≥ $1,900 全 12 ヶ月 | 1-2 週間 | 4-b / 1-c / 1-a |
| 6 | ❌ 適用のみ | 本 test 2026 Q1 月次 NET ≥ $1,900 全 3 ヶ月 | 半日 | 4-b / k=2 切替 |

---

## §10 改善フロー総まとめ (どの Phase 不合格でどこに戻るか)

```
                    [Phase 1-a 立て直し]
                            ↑
                            │ (素材から見直し)
                            │
            ┌───────────────┼───────────────┐
            │               │               │
        [Phase 1-c]   [Phase 1-a]      [k=2 切替]
            ↑               ↑               ↑
   1-b/2/3-a/4-b/5/6  1-b 全敗/leak    6 大幅未達
            │
   (目的関数再設計)


[Phase 2 で smoothing 設計再 audit] ← Sharpe 着手時

[Phase 3-b 戻る] ← 4-b-1 cluster 不整合
[Phase 4-b 戻る] ← 5/6 不合格 (Exit 再設計)
```

---

## §11 改訂履歴

| Date | Ver | 内容 |
|---|---|---|
| 2026-05-21 | v1 | 初版 (Web Claude 起案・まこさん「現状方針 OK + 失敗時改善フロー追加」指示反映) |

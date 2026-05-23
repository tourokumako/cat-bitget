# 2026-05-23_step_i4_1_case_a_v2_v3_critical1_spec.md — Critical-1 修正設計仕様書

**起案**: CC (2026-05-23 22:45・改訂29 続編)
**宛先**: CC 自身 (Step I-4.1 実装担当・明日 fresh head)
**版**: v1 (CP5 監査前ドラフト)
**前身**: handoff v30 §1.4 CP4 監査 Critical-1 / 仕様書 v2.1 §6 time_exit method
**目的**: Step I-3.4 §4.1 v5.1 判定で全 8 組合せ time_exit method が **fold 内完全同一値 (= naive baseline)** を出した構造的欠陥を解消し、time_exit method を**予測装置**として復活させる
**位置づけ**: cc_role.md §1.5.5 で **full 寄り (250-350 行)**・新規設計判断 + 新規 verify 含む
**読了ゲート**: WORKFLOW Step 0 / handoff v30 / lessons L-212c 通過済 (2026-05-23 22:30 機械的証跡記録)

---

## §0 目的・背景・Critical-1 の核心

### §0.1 何が起きたか (事実)

Step I-3.4 merge_step_i_summaries.py 完走後の §4.1 v5.1 判定で:

| 指標 | 結果 |
|---|---|
| n_combinations | 8 / 8 ✅ |
| fixed_tp ALL PASS | **0 / 8** ❌ |
| time_exit ALL PASS | **0 / 8** ❌ |
| meets_6plus_any_method | **False** ❌ |

CP4 監査 (Plan サブエージェント独立評価) で **Critical-1**「time_exit method が予測装置になっていない (naive baseline)」が指摘された。

数値証跡 (`case_a_v2_summary_*_p1.json` 抜粋):

| 組合せ × method | fold 0 | fold 1 | fold 2 | fold 内分散 |
|---|---|---|---|---|
| K12_LONG / fixed_tp | $-279,331 | $-286,831 | $-287,411 | 非ゼロ |
| **K12_LONG / time_exit** | **$-27,991** | **$-27,991** | **$-27,991** | **完全ゼロ** ❌ |
| K12_SHORT / time_exit | $-33,021 × 3 fold | | | 完全ゼロ ❌ |
| K24_LONG / time_exit | $-24,671 × 3 fold | | | 完全ゼロ ❌ |
| (全 8 組合せ time_exit で同パターン) | | | | |

**24 fold (= 8 組合せ × 3 fold) すべてで time_exit returns が fold 内完全同一値** = 予測モデル出力が評価結果に影響しない構造。

### §0.2 根本原因 (実装で verify 済)

`merge_step_i_summaries.py` L162-176:
```python
elif method == "time_exit":
    N = fold_summary.get("best_N")
    median_pct = time_exit_medians.get((K, side, N))
    n_test = fold_summary.get("n_test", 0)
    ret_const = (median_pct / 100.0) - cost_per_trade
    return np.full(n_test, ret_const, dtype=float)  # ★ 全 trade に同じ定数
```

`run_phase1_v5_purged_kfold.py` L388-395 (compute_simulated_pnl_v2 内 time_exit method):
```python
elif method == "time_exit":
    returns_per_trade = pd.Series(
        (time_exit_return_median / 100.0) - cost_per_trade,  # ★ 同じく定数 broadcast
        index=tp_hit_prob.index,
    )
```

`run_lgbm_phase1_v5_case_a_v2.py` L264-283 (time_exit grid loop):
```python
train_probs_dummy = pd.Series(0.5, index=train_ts)  # ★ dummy 0.5 渡し
test_probs_dummy = pd.Series(0.5, index=test_ts)
... compute_simulated_pnl_v2(tp_hit_prob=train_probs_dummy, ...)
```

3 箇所すべてで tp_hit_prob (予測値) が消費されない構造。CC は仕様書 v2.1 §6.1 で「time_exit return = train 期間中央値定数」と設計し、これが「予測装置の評価式」として機能不能であることに気付かないまま本走させた (L-212c)。

### §0.3 原因切り分け寄与率 (CP4 監査独立評価)

| 寄与因子 | 推定寄与率 | 本仕様書スコープ |
|---|---|---|
| ① 学習不良 (overfit / regime 過依存) | 10-15% | 範囲外 (案 X / 案 Z 領域) |
| (2a) fixed_tp 評価式暫定 (TP_PCT grid 狭さ等) | 40-50% | 範囲外 (案 W で対応) |
| **(2b) time_exit naive baseline** | **25-30%** | **本仕様書で解消** |
| ③ データ regime 過依存 | 10-15% | 範囲外 (案 V K96 除外で軽減) |

本仕様書単独の改善期待値: **25-30%** (case_a_v2 のうち 8 fold = 半数の構造的 PASS 不可能を解消)。1 週間並列実施で 4 案合計 75-95% 寄与をカバーすることで 6+ 組合せ ALL PASS 到達を狙う。

### §0.4 本仕様書のスコープ

**スコープ**:
- compute_simulated_pnl_v2 (runner v5.1 内) の time_exit method 数式変更 → 予測装置化
- case_a_v2_v3 新規ファイル作成 (既存 case_a_v2 保護・Step I-3 結果保持)
- case_a_v2_v3 で time_exit grid を **N (2) × TP_PCT (6) = 12 grid** に拡張 (現状は N 2 grid のみ)
- merge_step_i_summaries.py L162-176 returns 再構成式の予測装置化

**非スコープ** (別タスクで対応):
- Critical-2 dsr.py ガード (Step I-4.2)
- 案 W SL_PCT grid 拡張 (Step I-4.3)
- 案 V K=96 除外 (Step I-4.4)
- Phase 4-b-1 本確定 (cluster 別最適化 / DSR walk-forward / 24 種 Exit 網羅)

---

## §1 設計原則

### §1.1 Prime Directive 適合 (false_positive §0-1)

本仕様書で参照する全変数の推論時点 t 取得可能性:

| 変数 | t 時点取得可能性 | 根拠 |
|---|---|---|
| `tp_hit_prob[i]` | ✅ 可 | I-2.1 Classifier 出力・t 時点 X[i] で推論可 |
| `tp_pct` (TP_PCT grid) | ✅ 可 | Bot 起動時設定の定数 |
| `time_exit_return_median` | ✅ 可 | train (2021-04〜2024-12) のみで算出した定数 |
| `cost_per_trade` (= 0.00033) | ✅ 可 | exchange_spec.md 確定値 |

未来参照変数なし。L-179 / L-212c 同型再演リスクなし。

### §1.2 leak 防止

- time_exit_return_median は train 期間定数 (test 2025 / 2026Q1 への apply のみ)
- TP_PCT grid は事前固定 (test 結果見て変更しない)
- tp_hit_prob predictions は **Step I-2.1 で生成済の test 期間予測値** を再利用 (再学習しない)
- L-181 設計転換時 grep sweep 不要 (新数式は既存変数のみ使用・固有名詞なし)

### §1.3 暫定性の明示

本仕様書の time_exit method 新数式は **Step I-4.5 (Step I-3 再走) までの暫定版**。Phase 4-b-1 本確定で:
- time_exit を「TP 不発火時の代替 exit」でなく独立 strategy として再設計
- cluster 別 time_exit median (k=3 cluster 想定・regime ロバスト化)
- N grid を {K/4, K/2, K, K×1.5} に拡張可

に置き換える。本仕様書の暫定モデルは Phase 4-b-1 着手時に **破棄前提**。

---

## §2 修正前後の数式比較

### §2.1 fixed_tp method (変更なし・参考)

```
r[i] = tp_hit_prob[i] × (TP_PCT/100) - (1 - tp_hit_prob[i]) × (SL_pct/100) - cost
```

意味: 「TP 到達なら +TP_PCT・到達せず SL 引っかかれば -SL_pct・コスト引く」。
tp_hit_prob[i] が trade ごとに変動 → fold 内 returns 分散非ゼロ → 予測装置として機能 ✅

### §2.2 time_exit method (★ 本仕様書で改修)

**現状 (naive baseline)**:
```
r = time_exit_return_median / 100 - cost   (全 trade で同じ定数)
```

**修正後 (予測装置化)**:
```
r[i] = tp_hit_prob[i] × (TP_PCT/100) + (1 - tp_hit_prob[i]) × (time_exit_return_median/100) - cost
```

意味: 「TP 到達なら +TP_PCT・到達せず時間切れになれば time_exit_median (train 期間中央値・プラスもマイナスも有り得る)・コスト引く」。

### §2.3 数式の数学的等価性 (fixed_tp の SL を time_exit_median に置き換えただけ)

fixed_tp と time_exit の違い = 「TP 不発火時の処理」のみ:

| method | TP 発火時 | TP 不発火時 |
|---|---|---|
| fixed_tp | +TP_PCT | **-SL_pct (損切り・確実な負値)** |
| time_exit | +TP_PCT | **time_exit_median (時間切れ・market drift・正負両方有り得る)** |

両者は「TP 設定 + 不発火時の出口戦略」として並立する独立戦略。CP4 監査推奨数式と一致 (handoff v30 §2 案 A Critical-1)。

### §2.4 fold 内 returns 分散の理論計算

修正後 time_exit method の fold 内 returns 分散:

```
Var(r[i]) = (tp_hit_prob.std())² × (TP_PCT - time_exit_median)² / 100²
```

tp_hit_prob.std() > 0 (Step I-2.1 smoke で確認済・mean=0.4-0.6 / std=0.1-0.2 範囲) かつ TP_PCT ≠ time_exit_median である限り、Var(r[i]) > 0 が保証される。

DSR 計算 (`mean / std`) が正常動作 → Critical-2 dsr.py × 定数 returns 相互作用 (L-212b) も解消方向に作用。

---

## §3 修正対象ファイル

### §3.1 compute_simulated_pnl_v2 (`run_phase1_v5_purged_kfold.py` L388-395)

**変更前**:
```python
elif method == "time_exit":
    returns_per_trade = pd.Series(
        (time_exit_return_median / 100.0) - cost_per_trade,
        index=tp_hit_prob.index,
        name=f"return_v2_{method}",
    )
```

**変更後**:
```python
elif method == "time_exit":
    # 期待値式: E[return] = p × TP_PCT + (1-p) × time_exit_median - cost (予測装置化)
    # tp_pct パラメータを必須化 (旧式 dummy 0.0 渡しは禁止)
    if tp_pct <= 0.0:
        raise ValueError(
            "time_exit method requires positive tp_pct (Critical-1 修正・L-212c)"
        )
    returns_per_trade = (
        tp_hit_prob * (tp_pct / 100.0)
        + (1.0 - tp_hit_prob) * (time_exit_return_median / 100.0)
        - cost_per_trade
    )
```

ガード追加: `tp_pct <= 0.0` で `raise ValueError` (旧式 dummy 渡し検出 + L-181 設計転換時の旧経路混入防止)。

### §3.2 case_a_v2_v3 新規ファイル (既存 case_a_v2 保護)

ファイル名: `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2_v3.py`

既存 case_a_v2 からの変更点 (3 箇所):

**変更 1**: time_exit grid を N × TP_PCT に拡張 (L253-298)
```python
# 旧 (case_a_v2):
# for ratio in n_ratios:  # 2 grid (K/2, K)
#     train_probs_dummy = pd.Series(0.5, index=train_ts)  # dummy
# 新 (case_a_v2_v3):
for tp_pct in tp_pct_grid:  # 6 grid (0.3, 0.5, 0.8, 1.2, 1.8, 2.5)
    df_tp = tp_hit_df_combo_fold[tp_hit_df_combo_fold["TP_PCT"] == tp_pct]
    if df_tp.empty:
        continue
    df_tp_indexed = df_tp.set_index("trade_ts")["tp_hit_prob"]
    train_probs = df_tp_indexed.reindex(train_ts).fillna(...)
    test_probs = df_tp_indexed.reindex(test_ts).fillna(...)
    for ratio in n_ratios:  # 2 grid (K/2, K)
        N = max(1, int(K * ratio))
        median_pct = time_exit_medians.get((K, side, N))
        if median_pct is None:
            continue
        # compute_simulated_pnl_v2 を tp_pct + tp_hit_prob 込みで呼び出し
        _, train_year_usd, train_diag = compute_simulated_pnl_v2(
            tp_hit_prob=train_probs,
            tp_pct=tp_pct,         # NEW: dummy 0.0 でなく実 tp_pct
            sl_pct=0.0,            # time_exit method では未使用
            time_exit_return_median=median_pct,
            method="time_exit",
            ...
        )
        # ... test 側も同様 ...
        time_exit_grids.append(MethodGridResult(
            method="time_exit",
            tp_pct=tp_pct,   # NEW: 集約後に tp_pct も保持
            N=N,
            ...
        ))
```

**変更 2**: MethodFoldMetrics に `best_tp_pct` を time_exit method でも保持 (L102 dataclass 拡張)

```python
@dataclass
class MethodFoldMetrics:
    ...
    best_tp_pct: Optional[float] = None  # method=fixed_tp / time_exit 両方で使用
    best_sl_pct: Optional[float] = None  # method=fixed_tp のみ
    best_N: Optional[int] = None         # method=time_exit のみ
```

**変更 3**: `_aggregate_grid_idxmax` で time_exit grid 集約時に `best_tp_pct` も記録 (L316-351)

grid 数の変化: time_exit は 2 → **12** (N 2 × TP_PCT 6) / fixed_tp は 18 のまま / 合計 30 grid/組合せ。
calc コスト: 1 fold あたり sim_pnl 計算 30 回 (旧 20 回の 1.5 倍・smoke で実測 < 10 秒/組合せ想定)。

### §3.3 merge_step_i_summaries.py L162-176 改修

**変更後**:
```python
elif method == "time_exit":
    N = fold_summary.get("best_N")
    tp_pct = fold_summary.get("best_tp_pct")  # NEW: time_exit でも tp_pct 必須
    if N is None or tp_pct is None:
        return None
    median_pct = time_exit_medians.get((K, side, N))
    if median_pct is None:
        return None
    df = predictions_df[
        (predictions_df["K"] == K)
        & (predictions_df["side"] == side)
        & (predictions_df["fold_idx"] == fold_idx)
        & (predictions_df["TP_PCT"] == tp_pct)
    ]
    if df.empty:
        return None
    p = df["tp_hit_prob"].to_numpy()
    returns = (
        p * (tp_pct / 100.0)
        + (1.0 - p) * (median_pct / 100.0)
        - cost_per_trade
    )
    return returns
```

evaluate_fold (L210-272) の time_exit 分岐で `tp_precision_pass = True (自動 PASS)` は維持 (TP 約定率は time_exit method の主目的でなく副次指標)。

---

## §4 受け入れ基準 (Step I-4.1 完了判定)

### §4.1 fold 内 returns 分散非ゼロ assertion (必須 verify)

smoke (sample K=12 LONG / 1 fold) で:
```python
returns = compute_simulated_pnl_v2(method="time_exit", ...).returns
assert returns.std() > 1e-10, "time_exit method 予測装置化失敗・naive baseline 残存"
```

これ 1 つで Critical-1 修正の即時 verify が可能 (Day 2 中間 verify ポイント)。

### §4.2 関所 A 異常値スメル 0/8 維持

smoke 完走後の `anomaly_smell_per_combination` で month_pnl > $3,800 件数 = 0 を維持。
予測装置化で月次 NET 中央値が変動するため、関所 A ② 件数が増加する可能性あり (Day 4 中間 verify ポイント)。

### §4.3 §4.1 v5.1 4 指標 ALL PASS 再判定 (本走後)

修正後 Step I-3.5 full 完走で:
- fixed_tp ALL PASS: ??? / 8 (現状 0/8・案 W SL_PCT 拡張効果と合算)
- time_exit ALL PASS: ??? / 8 (現状 0/8・本仕様書 + 案 W + 案 V 効果と合算)
- meets_6plus_any_method: True / False

case_a_v2_v3 単独効果 (Critical-1 のみ・案 W/V 不実施) では time_exit method の sim_pnl 値変動 + DSR 計算正常化が期待される。0-3 組合せの改善幅を観察 → 案 W/V/Critical-2 と並列実施で総合 6+ ALL PASS を狙う。

### §4.4 完了報告必須証跡 8 点

WORKFLOW.md §作業完了報告 8 点全部 (grep 結果 / 数値二重提示 / ファイル実体 / 実行ログ / 絞り込み示唆語彙 / train→test 変化表 / 異常値スメルテスト / 全工程未来参照 verify) を case_a_v2_v3 完了報告で提示。

---

## §5 リスクと安全装置 (1 週間並列の中間 verify)

### §5.1 Day 2 中間 verify (Critical-1 修正単独完了直後)

- smoke (sample K=12 LONG / 1 fold) で time_exit method の `returns.std() > 1e-10` assertion 通過
- 通過 → Critical-2 / 案 W / 案 V を並列着手
- FAIL → 即 stop して数式再 review (CP5 監査で見落としあり)

### §5.2 Day 4 中間 verify (全 4 修正完了直後)

- smoke (sample 8 組合せ / 1 fold) で関所 A 異常値スメル件数 = 0/8 維持
- 月次 NET 中央値が「全組合せ赤字」 (= 評価式直してもエッジなし) なら Day 5 stop + 案 Z (meta-labeling) / 案 X (Layer 3) に切替検討
- 「赤字レンジが現状 $-30K → $-100K オーダーまで悪化」も stop 条件 (修正が状況悪化させる構造欠陥)

### §5.3 Day 5 早期撤退条件

Day 4 verify で全組合せ赤字 + 中央値 $-50K 以下なら、Day 6-7 の full 走を中止し:
- 案 Z e (meta-labeling) を K96 fold0 部分成功活用に転用
- 案 X (Layer 3 CPCV + Focal loss + アルゴ多様化) 設計仕様書起案に切替

L-208 の撤退ライン文言適用判定をここで再起動。

---

## §6 CP5 監査依頼項目 (Step I-4.1 仕様書起案後・Plan サブエージェント)

CP5 監査 (`/audit` または Plan サブエージェント) で以下を独立 verify:

1. **数式の予測装置性 verify**: §2.2 修正後数式が「予測モデル出力 (tp_hit_prob) を直接消費する経路」を持つか・fold 内 returns 分散の理論計算が妥当か
2. **数式の数学的等価性 verify**: fixed_tp と time_exit が「TP 不発火時処理のみ差分」として正しく分離できているか
3. **Critical-1 単独効果の現実性 verify**: 25-30% 寄与の推定が CP4 監査結果と整合するか・case_a_v2_v3 単独で 0/8 → 何件改善が期待できるか
4. **dummy 0.0 渡し検出ガード verify**: `compute_simulated_pnl_v2` の `tp_pct <= 0.0 → raise ValueError` が L-181 設計転換時の旧経路混入を防げるか
5. **case_a_v2_v3 別ファイル化判断 verify**: 既存 case_a_v2 保護 + Step I-3 結果保持の妥当性 (Phase 4-b-1 で破棄予定なので過剰防衛でないか)
6. **grid 数増加 (20 → 30) の calc コスト verify**: smoke で 10 秒 / 組合せ以内に収まるか・full 走で 10 時間 (L-212a 1 並列順次) を超過しないか
7. **fold 数 3 → 5 の整合性 verify**: §4.1 v5.1 仕様 (5 fold) と現状実装 (3 fold) のズレが Critical-1 修正と別問題として残存しないか
8. **L-212c 関所 B 拡張 (予測装置性宣言) の本仕様書での適用 verify**: 評価式の各 method について「予測モデル出力を直接消費する経路」が明示されているか
9. **同型バイアス警戒**: 本仕様書が「v2.1 §6 で同じ間違いをした CC」と同じ思考枠で書かれていないか (Critical-1 と本質的に同じ穴を別形で残していないか)

監査推奨フォーマット: 各項目 PASS / FAIL / CONDITIONAL + 1-2 行コメント。CONDITIONAL の場合は条件明示。

---

## §7 着手手順 (明日 fresh head)

### Step I-4.1.1: CP5 監査依頼 (今夜実施・並列起動)

- 本仕様書 + 数値証跡 (case_a_v2_v3 P1 results) を Plan サブエージェントに渡す
- 9 項目の独立 verify を依頼
- 想定時間: 30-60 分

### Step I-4.1.2: 監査結果反映 (明日朝・1-2 時間)

- CP5 監査結果 (Critical / Major / Minor 分類) を 100% 反映
- 反映後 v2 確定 (まこさん最終 GO 取得)

### Step I-4.1.3: 実装 (明日午後・3-5 時間)

- compute_simulated_pnl_v2 の time_exit method 修正
- case_a_v2_v3 新規ファイル作成 (case_a_v2 から 597 行コピー + 3 箇所変更)
- merge_step_i_summaries.py L162-176 改修

### Step I-4.1.4: smoke + assertion verify (明日夕方・30 分)

- `python -u run_lgbm_phase1_v5_case_a_v2_v3.py --smoke > log_v3_smoke.log 2>&1`
- assertion `returns.std() > 1e-10` 通過確認
- 関所 A 異常値スメル件数 verify

### Step I-4.1.5: git commit (明日夕方・10 分)

- ファイル単位で add (config/bitget_keys.json 等除外)
- commit msg: `feat: Step I-4.1 case_a_v2_v3 Critical-1 修正 (time_exit 予測装置化・L-212c)`

---

## §8 改訂サマリー

| 版 | 日付 | 内容 |
|---|---|---|
| v1 | 2026-05-23 22:45 | 初版・CP4 監査 Critical-1 反映・CP5 監査前ドラフト |

---

以上。

# 2026-05-23_step_i4_1_critical1_cp5_audit_report.md — CP5 監査結果

**監査実施**: 2026-05-23 22:55 (Plan サブエージェント独立評価)
**監査対象**: `.claude/instructions/2026-05-23_step_i4_1_case_a_v2_v3_critical1_spec.md` v1 (417 行)
**監査者**: Plan サブエージェント (cold start・CC 整理 rederive 禁止指示)
**版**: v1 (まこさん共有用・本ファイルは記録目的・v2 反映タスクは明日 fresh head)

---

## §0 監査結論

**CONDITIONAL GO** — 数式の予測装置化は妥当だが、(i) `time_exit_median` の単一 N → fold 内分散ゼロ温存リスク、(ii) fold 数 3 vs 5 の非整合、(iii) §0-1 Prime Directive 観点の `time_exit_median` 因果性宣言欠落の 3 件を v2 で必ず塞いでから本走。

---

## §1 9 項目判定サマリー

| # | 項目 | 判定 | 主要コメント |
|---|---|---|---|
| 1 | 数式予測装置性 | **PASS** | `Var(aX+b) = a²Var(X)` 標準展開と一致・std(p)>0 で >0 保証 |
| 2 | 数式数学的等価性 | **PASS** | Bernoulli(p) 混合戦略として両 method 独立並立可 |
| 3 | Critical-1 単独効果 | **CONDITIONAL** | 25-30% 推定は CP4 引き写し・下限 0 件可能性併記要 |
| 4 | dummy 0.0 検出ガード | **PASS** (Minor) | `tp_pct is None` 経路強化 + fixed_tp 対称ガード推奨 |
| 5 | case_a_v2_v3 別ファイル化 | **PASS** | rollback + 差分検証用途で過剰防衛でない |
| 6 | grid 数 20→30 calc コスト | **CONDITIONAL** | smoke 実測義務化 (10 秒/組合せ根拠が外挿) |
| 7 | fold 数 3→5 整合性 | **FAIL (Major)** | 仕様書未言及・スコープ明示要 |
| 8 | L-212c 関所 B 拡張 | **FAIL (Critical)** | 予測装置性宣言が §1.1 で欠落 |
| 9 | 同型バイアス警戒 | **CONDITIONAL** | 新規穴 2 件検出 (CP4 見逃し) |

---

## §2 Critical (本走前必須修正・v2 反映)

### C1: 関所 B 拡張「評価式の予測装置性宣言」を §1.1 に追記

仕様書 §1.1 Prime Directive 適合表は変数の t 時点取得可能性のみ宣言。**L-212c 新規拡張要件 = 「評価式の各 method が予測モデル出力を直接消費する経路を持つ」を仕様書本文で明示要**。

追記文 (草案):
- fixed_tp: 「tp_hit_prob[i] が trade-level に変動 → returns_per_trade が非定数」
- time_exit (修正後): 「tp_hit_prob[i] が線形係数 (TP − median)/100 で returns に伝播・係数 ≠0 である限り予測装置として機能」

### C2: TP_PCT ≒ median 重複ガード (新規穴-α・CP5 独自検出)

**CP4 監査が見逃していた穴**: `time_exit_return_median: 0.0034405` (K12_LONG fold 0 N=12) は TP_PCT=0.3% と差 ε=0.04% で危険域。修正後数式でも特定 grid で naive baseline 再演リスクあり。

例 (LONG):
```
TP_PCT = 0.3% / median = 0.34% の組合せ:
r[i] = p[i] × 0.003 + (1 - p[i]) × 0.0034 - cost
     = 0.0034 - p[i] × 0.0004 - cost
     ≈ ほぼ定数 (係数 0.0004 で分散がほぼゼロ)
```

修正案: `compute_simulated_pnl_v2` 内に
```python
if method == "time_exit" and abs(tp_pct - time_exit_return_median) < 0.05:
    return ... skip + warning  # naive baseline 再演グリッドの除外
```

または `case_a_v2_v3` grid loop 内で除外。

---

## §3 Major (本走前推奨修正・v2 反映)

| # | 項目 | 反映先 |
|---|---|---|
| M1 | fold 数 3→5 是正のスコープ明示 (本タスク内 or 別タスク) | §0.4 非スコープ or §3 |
| M2 | ガード強化 `is None or <= 0.0` + fixed_tp 対称化 | §3.1 |
| M3 | Day 2 smoke で 30 grid 実測時間機械的証跡 (CPU + RSS) | §4.1 完了報告必須証跡 9 点目 |
| M4 | 寄与率 25-30% に下限 0 件可能性併記 | §0.3 |

---

## §4 Minor (Step I-4.1 完了報告までに対応)

| # | 項目 | 反映先 |
|---|---|---|
| m1 | §2.4 末尾の Critical-2 言及削除 (スコープ宣言違反) | §2.4 |
| m2 | §0.3 寄与率出典を「CP4 監査推定 (CC 独立再算出未実施)」と明記 | §0.3 |
| m3 | `_aggregate_grid_idxmax` の 12 grid 対応 verify | §3.2 実装メモ追加 |

---

## §5 CC 同型バイアス検出 (CP5 独立性証跡)

### CP4 監査と異なる結論を出したポイント (1 件)

**新規穴-α (項目 9・C2)**: TP_PCT ≒ median 重複時の naive baseline 再演リスク。CP4 監査は「予測装置化すれば Critical-1 解消」と結論したが、TP_PCT grid (0.3, 0.5, 0.8, 1.2, 1.8, 2.5) と train 期間 median の数値的重複可能性を verify していなかった。CP5 が独立 verify (証跡 `time_exit_return_median: 0.0034405`) で TP_PCT=0.3% と差 ε=0.04% を検出。

→ CC + CP4 + CP5 の 3 段階を経て初めて検出された穴。同型バイアス回避経路として機能した実証。

### CP4 と一致した結論 (auto-trust 回避済)

数式の予測装置性 (1)・数学的等価性 (2)・dummy ガード方向性 (4)・別ファイル化 (5) は CP4 と同方向だが、CP5 が独立に rederive:
- 項目 1: `Var(aX+b)` 標準展開で再計算
- 項目 2: Bernoulli mixture model で再構成

して PASS 確認 → auto-trust 回避済。

---

## §6 仕様書 v2 反映タスク (明日 fresh head)

### Step I-4.1.0 (新規追加): CP5 監査結果反映 → 仕様書 v2 確定

1. C1 反映: §1.1 に「評価式の予測装置性宣言」section 追加
2. C2 反映: §3.1 に `abs(tp_pct - median) < 0.05% → skip + warning` ガード追加
3. M1-M4 反映: §0.3 / §0.4 / §3.1 / §4.1
4. m1-m3 反映: §0.3 / §2.4 / §3.2

想定時間: 1-2 時間 (明日朝・cold head 想定)

### Step I-4.1.3: 実装着手 (明日午後)

- 仕様書 v2 確定後に compute_simulated_pnl_v2 / case_a_v2_v3 / merge_step_i_summaries.py 改修
- C2 ガード実装も忘れず含める

---

## §7 監査者所感

- 仕様書 v1 の数式自体は妥当 (CP5 独立 rederive で PASS)
- ただし「fold 数 3→5 非整合」「TP_PCT ≒ median 重複」は CC が見落とした穴
- 特に新規穴-α (C2) は **Critical-1 修正と同じ穴の別形** で、L-212c の同型構造を含む (= CC 同型バイアスの再演リスク)
- 仕様書 v2 で 2 件の Critical を必ず塞ぐこと
- v2 確定後の本走前に再度 CP5.5 監査が必要か否か → 監査者判断: **C1/C2 反映が「機械的反映 (新規判断なし)」であれば再監査不要** (cc_role §1.5.5 light 枠整合)・「新規 verify / 新規ガード追加」を含む場合 (= C2 ガード実装) は CP5.5 を実施推奨

---

以上。

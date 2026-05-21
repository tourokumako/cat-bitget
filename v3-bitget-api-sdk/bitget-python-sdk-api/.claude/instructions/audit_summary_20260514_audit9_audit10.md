# 監査履歴サマリー (audit#9 / audit#10) — 2026-05-14

新セッションの CC / Web Claude が次タスク (選択肢5 vs 7 再評価 → Phase 4-b 着手) に進む前に全文読むこと。

---

## §1. 直前の確定事項 (audit#9 まで)

### audit#8 で確定 (前提)

- K12 LONG refit (commit d9d322c) **維持**
  - §8 違反 (test 由来数値で学習データ変更) だが影響限定的・撤回せず
- Phase 2 正式判定 = **改訂後 spec で 4 指標 ALL PASS**
  - q99 8 組合せ加重 +21.28pp / positive 7/8
  - 公式 source: `results/priority_rebuild/ml_phase2_rerun_postrefit/phase2_summary.json` (sha256 4245de8bc9e1)
  - audit#8 で `run_phase2_precision.py` が案 G (commit b14be88) の §1.6 改訂を未実装と発覚 → 案 A で改修済

### audit#9 で確定: 絶対閾値 drift 対処 = **固定維持 + K96 SHORT q99 除外**

- **rolling 却下**: §1.6.1 メタルール抵触の疑い + signal quality 全面低下 (8/8 組合せ低下・K24 LONG マイナス転落・K96 SHORT 深化)
- **ハイブリッド却下**: selection bias 構造
- **K96 SHORT q99 除外**: test 発火 0 件 (BTC 2.4 倍上昇で予測値 % 圧縮・test ratio max 2.39 < train q99 3.05) → 数学的に発火不可能
- **損失影響**: 年 $169,400 (q99 全体の 9.6%)・全 12 月で月次 $1,900 維持継続
- **明文化**: cc_ml_design_spec.md §1.6.2 + phase_compliance_checklist.md §4a.5 拡張 (test 発火 0 件を発動条件追加)

### audit#9 で look-ahead 検証 (rolling 実装)

- `shift(1).rolling(window).quantile(0.99)` を独立 grep 検証 → **数学的に正しい・look-ahead leak なし** ✅
- ただし rolling 自体は採用見送りのため、検証は記録としてのみ

---

## §2. audit#10 指摘: 選択肢5 vs 7 再評価ドラフトへの **必須改訂 4 項目**

ドラフトは骨子妥当だが、CC 発注前に以下 4 項目を修正必要。修正せずに発注すると「件数だけで 5 圧勝 → signal quality 弱いまま Phase 4-b 着手」の selection bias リスク。

### 必須改訂 1: 軸2 を signal quality 軸まで拡張

- 現状: 軸2 はサンプル数 (count) のみ
- 問題: rolling 採用時に判明したように、件数だけでは signal quality 全面低下を見落とす
- 修正: 軸2 を「(a) test 件数 + (b) per-組合せ net_quality / MFE_lift / MAE_lift」に拡張

### 必須改訂 2: 軸1 の framing 中立化

- 現状: 「5=band 救済 / 7=フォールバック除外」という対比
- 問題: 前回データで K96_SHORT_q95-q99 band も test 0 件 (救済できない) なのに、5 を有利に framing
- 前回 CC 推奨「7+rolling」→ rolling 却下後の反動「5 を救おう」bias の可能性
- 修正: 「両案とも K96 SHORT q99 をどう処理するか」と中立化・前回データの事実 (q95-q99 band も 0 件) を本文明示

### 必須改訂 3: サンプル数閾値を足切り条件として明示

- 現状: 「test<100 件セルを一覧化」のみ
- 問題: audit#2 既定基準 (<100 件 = 統計的有意性なし) を運用に反映せず「測ったが使わない」状態
- 修正: 「test<100 件セルは Phase 4-b で no-trade」をデフォルト・代替策 (補完・緩和) を別軸で比較

### 必須改訂 4: K96 SHORT q99 除外の band 化適用ルール明示

- 現状: 選択肢5 で「K96 SHORT q99 除外」の band 化適用が曖昧
- 解釈 A: q99 単独のみ除外 / B: K96 SHORT 全 q-level 除外 / C: q99 + q95-q99 band 除外 (test 0 件) / q90-q95 band 別判定
- 推奨: 解釈 C を明示・§1.6.2 改訂で正式化

---

## §3. audit#10 推奨改訂 (CC 発注前)

5. 完了報告テンプレ改訂を本タスク Step 1 に組み込み (audit#9 懸念2 由来・「個別組合せ train→test 変化表」必須化)
6. 「CC 推奨」要求を撤廃 (Web Claude + CC 収束バイアス防止・Web Claude 独自評価 → 監査経路)
7. 軸3 の参照ライン分離 (5 用 fire ratio / 7 用 max_diff)
8. signal quality vs 件数 統合表追加 (per-組合せ contribution = fire × net_quality)
9. 並行タスク (§4b.4-b simulate_predicted_mfe_tp) は本タスク結論待ち・並走不可
10. ハイブリッド (5 + 7 部分採用) を選択肢に追加検討

---

## §4. 未解決事項 (次タスクで扱う)

| 項目 | 出所 | 状態 |
|---|---|---|
| 選択肢5 vs 7 確定 | audit#9 順序指示 | ⏭️ 次タスク (ドラフト改訂 → CC 発注 → 監査経路) |
| Phase 4-b 方針確定 | 選択肢5 vs 7 確定後 | ⏭️ |
| §4b.4-b simulate_predicted_mfe_tp 実装 | audit#8 | ⏭️ 選択肢確定後 |
| §1.6.1 メタルール script guard | audit#8 | ⏭️ Phase 4-b 着手時 |
| K24 LONG (14) / K24 SHORT (63) / K96 LONG (15) test<100 件取扱 | audit#9 見落とし E | ⏭️ 選択肢5 vs 7 再評価の中で扱う |
| 完了報告テンプレ 6 点目追記 (train→test 変化表) | audit#9 懸念2 | ⏭️ 選択肢5 vs 7 タスク Step 1 で実施 |

---

## §5. 構造的注意点 (新セッション必読)

### Web Claude + CC 収束バイアス

- audit#3〜#9 で繰り返し flag した構造的問題
- procedural fix (CSV 先読み・self_check) では完全には防げない
- **重大判断は監査経路必須**

### 監査者自身の anchoring bias

- 本サマリー作成者 (audit#1〜#10 担当) は同 session で 10 回連続 audit
- 「自分の過去 framing への anchor」リスクあり
- 次の重大 audit は **新セッションの独立監査者**で実施することを推奨 (まこさんがこの方針で次セッション移行決定)

### Web Claude のミスパターン (handoff_v5 §6 より)

- 数値・ファイルの出所未確認 (フォルダ取り違え)
- ドキュメントと実装の乖離見逃し
- §8 違反 (test 由来数値を train 問題と誤認)
- 対策: `.claude/rules/web_claude_self_check.md` チェック A/B を毎回機械的に通す

---

## §6. 関連ファイル (新セッション CC が読むべき順)

1. このサマリー (audit_summary_20260514_audit9_audit10.md)
2. WORKFLOW.md §🔴 現在のフェーズ + 次のタスク
3. handoff_to_web_claude_v5_session_20260514.md (前セッションからの引き継ぎ全体)
4. cc_ml_design_spec.md §1.6 / §1.6.1 / §1.6.2
5. phase_compliance_checklist.md §4a.5 / §4b
6. `.claude/rules/web_claude_self_check.md`
7. audit#9 完了報告: `.claude/instructions/2026-05-14_threshold_drift_eval_completion.md`
8. 選択肢評価データ: `results/priority_rebuild/clustering_alternatives/option5_K_side_qlevel.csv` / `option7_short_clu_long_perentry.csv`

---

## §7. 推奨次アクション (新セッション Web Claude 向け)

1. 本サマリー + handoff_v5 + WORKFLOW.md を読む
2. 選択肢5 vs 7 再評価ドラフトに audit#10 指摘 4 項目 + 推奨 6 項目を反映
3. 修正後ドラフトを **新セッション独立監査** に通す
4. 監査通過後に CC 発注
5. CC 完了報告受領 → Web Claude self_check (B) → 監査経路 → まこさん GO
6. 選択肢確定後に Phase 4-b 指示書策定 (§4b.4-b 実装含む)

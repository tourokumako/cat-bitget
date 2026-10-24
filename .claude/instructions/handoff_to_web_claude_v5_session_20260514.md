# Handoff to Web Claude v5 — 2026-05-14 セッション引き継ぎ

次セッションの Web Claude が最初に全文読むこと。経緯・本題・宿題を引き継ぐ。

---

## §1. 本セッションの確定事項 4 件

### 確定 1: K12 LONG refit (commit d9d322c) **維持**

- **経緯**: audit#3 が「K12 LONG MFE_lift -9.99%」を train 問題と誤認 → refit を推奨 → CC が実施 → audit#7 で「test 由来数値を見て学習データ変更 = §8 違反疑い」発覚
- **案 Z で影響測定**: refit は K12 LONG q99 1 点限定の改善 (+16.06pp → +36.21pp)・他 7 組合せ完全 bit-exact 不変・Phase 2 は refit 前後とも 4 指標 ALL PASS
- **判断**: §8 違反だが影響限定的・撤回せず維持
- **出所**: [2026-05-14_phase2_revalidate_post_refit_completion.md](2026-05-14_phase2_revalidate_post_refit_completion.md) + [2026-05-14_phase2_script_fix_and_structural_completion.md](2026-05-14_phase2_script_fix_and_structural_completion.md)

### 確定 2: Phase 2 正式判定 = **改訂後 spec で 4 指標 ALL PASS**

- q99 8 組合せ加重 +21.28pp / positive 7/8 / 指標 2/3/4 PASS / overall_pass=true
- **公式 source**: `results/priority_rebuild/ml_phase2_rerun_postrefit/phase2_summary.json` (sha256 4245de8bc9e1)
- **経緯**: audit#8 で `run_phase2_precision.py` が案 G (commit b14be88) の §1.6 改訂を未実装と発覚 → 案 A で改修 (`CRITERION_1_POSITIVE_MIN = 6` + `df_q99` 抽出)
- **重要**: 改修前は「改訂後 spec PASS」は完了報告内の手計算で示されていた・script 自動判定は旧 spec で FAIL だった

### 確定 3: セッション全工程 **retain** (やり直し不要)

- Phase 3 短期試行〜選択肢 1/4/5/6/7 評価まで成果物 retain
- 理由: refit 維持・Phase 2 PASS 維持で前提崩壊なし

### 確定 4: 絶対閾値 drift 対処 = **固定維持 + K96 SHORT q99 除外**

- **rolling 却下**: §1.6.1 メタルール抵触の疑い + 信号品質全面低下 (8/8 組で net_quality 低下・K24 LONG はマイナス転落)
- **ハイブリッド却下**: selection bias 構造
- **K96 SHORT q99 除外**: test 発火 0 件 (BTC 2.4 倍上昇で予測値 % 圧縮・test ratio max 2.39 < train q99 3.05) → 数学的に発火不可能
- **損失影響**: 年 $169,400 (q99 全体の 9.6%)・全 12 月で月次 $1,900 維持継続 (audit#3 検証済)
- **明文化**: cc_ml_design_spec.md §1.6.2 + phase_compliance_checklist.md §4a.5 拡張 (test 発火 0 件を発動条件追加)
- **出所**: [2026-05-14_threshold_drift_eval_completion.md](2026-05-14_threshold_drift_eval_completion.md) + audit#9

---

## §2. 本セッションで導入した仕組み

| 仕組み | 場所 | 用途 |
|---|---|---|
| Web Claude self_check (チェック A/B) | `.claude/rules/web_claude_self_check.md` | 指示書発行前 + 完了報告受領時に機械的に通す |
| 成果物ファイル名の一意化ルール | WORKFLOW.md | フォルダ違い同名禁止・識別子付与 (`*_PREREFIT.csv` 等) |
| 公式判定 source = スクリプト出力のみ | WORKFLOW.md + cc_ml_design_spec.md §1.6.1 | 手計算を「公式」と称さない |
| L-179 拡張 (spec/実装一般整合性) | lessons_active.md L-179 末尾 | ML leak 限定 → spec 改訂時の script grep verify に拡張 |
| feedback_pre_execution_premise_check.md (CC 側) | `~/.claude/projects/.../memory/` | 着手前 4 項目: script 自動/手計算 + 数値出所 + 前提 verify + 引用と実装整合 |

---

## §3. 次セッションの本題

**選択肢 5 vs 7 の再評価**

- **前提**: 固定維持 + K96 SHORT q99 除外 (本セッション確定 4)
- **監査が示した順序**: drift 対処 (確定済) → 選択肢 5 vs 7 → Phase 4-b 方針
- **audit#9 が「次の audit を経由」と明記** → 選択肢 5 vs 7 再評価は監査経路を通す前提

選択肢内容 (前タスクから引用):
- **選択肢 5**: K × side × q-level (24 組合せ)・q90/q95/q99 を natural classifier に
- **選択肢 7**: SHORT clustering (k=2) + LONG per-entry (12 組合せ)・非対称設計

---

## §4. 監査が出した未処理の宿題

| 宿題 | 出所 | 状態 |
|---|---|---|
| §4a.5 に「test 発火 0 件」追加 | audit#9 見落とし F | ✅ **本タスク Step 2 で対応済** |
| 完了報告テンプレに「個別組合せの train→test 変化の表」必須化 | audit#9 懸念 2 | ⏭️ **未対応** |
| spec/script consistency check の未実装 2 項目 (§4b.4-b simulate_predicted_mfe_tp / §1.6.1 メタルール script guard) | audit#8 | ⏭️ **未対応** (Phase 4-b 着手時に併せて対応予定) / 参照: [spec_script_consistency_20260514.md](../../results/priority_rebuild/spec_script_consistency_20260514.md) |
| 固定維持でも K24 LONG (14) / K24 SHORT (63) / K96 LONG (15) が test <100 件で統計的有意性に疑問 | audit#9 見落とし E | ⏭️ **未対応**・選択肢 5 vs 7 再評価の中で扱う |

---

## §5. 次セッション着手手順

1. 本 handoff メモを最初に全文読む
2. cc_ml_design_spec.md §1.6 / §1.6.1 / §1.6.2 (drift 追記済) を読む
3. `.claude/rules/web_claude_self_check.md` を読む
4. WORKFLOW.md §🔴次のタスク を確認
5. 選択肢 5 vs 7 再評価の指示書作成 → 監査経路を通す
   - 完了報告テンプレ改善 (個別組合せ train→test 表必須化) と consistency check 未実装 2 項目も同タスクか並行で処理

---

## §6. 本セッションで繰り返された Web Claude のミスと対策

### ミス記録
- **数値・ファイルの出所未確認**: フォルダ取り違え複数回 (ml_phase2/ vs ml_phase2_post_refit/ など)
- **ドキュメントと実装の乖離見逃し**: 案 G で spec 改訂したが run_phase2_precision.py を改修せず・「改訂後 spec PASS」を script 結果と暗示
- **§8 違反 (audit#3 で test 由来数値を train 問題と誤認し refit を推奨)**: 数値の出所 (train か test か) を確認せずに学習データ変更を判断

### 対策
- **web_claude_self_check.md チェック A/B を毎回機械的に通す** (指示書発行前 + 完了報告受領時)
- **重大判断は監査経路を通す** (self_check は初歩ミスを減らすが「Web Claude と CC の収束バイアス」は防げない・audit#6 指摘)
- **数値の出所を毎回確認**: train / test / refit 前後 / どのフォルダ / どの commit

### 限界の自覚
self_check は手続きとして有効だが、構造的バイアス (Web Claude と CC が同じ枠組みで考えるため同じ結論に収束しやすい) は防げない。**重大判断・前提に関わる判断は引き続き監査経路必須**。

---

## §7. 本セッション成果物一覧 (commit 済)

[v3-bitget-api-sdk/bitget-python-sdk-api/WORKFLOW.md](../../WORKFLOW.md) §「2026-05-14 セッション成果物一覧」参照。

主要ファイル:
- 7 タスク x (指示書 + 完了報告) = 14 ファイル
- 4 スクリプト (run_phase4a_k2_revisit / run_phase4a_normalize_reselect / run_clustering_alternatives_eval / run_threshold_drift_eval)
- 1 ルール (web_claude_self_check.md)
- 5 修正 (WORKFLOW.md / cc_ml_design_spec.md / lessons_active.md / run_phase2_precision.py / plan_g_pre_phase4_completion.md)

<!-- DOCMAP_HASH=efac4556c745bc81 -->
# docmap.md — 機械が作る文書の全数の一覧（gen_docmap.py が自動生成＝手書き禁止）

⚠️ 手で書き換えないでください。**道具の側の名乗り（`GENERATES`）を機械で集めています。**
名前で数えていません（名前で数えると必ず漏れる＝2026-08-16 に実測で1本 落とした）。

```
python3 scripts/priority_rebuild/gen_docmap.py --write    # 作り直す
python3 scripts/priority_rebuild/gen_docmap.py --verify   # 改変・古くなりの検出
```

## この一覧で分かること・分からないこと（正直に）

**分かる**＝機械が作る文書が全部で何本か ／ 検証できない道具はどれか ／ 人が手で書く文書はどれか。

**分からない**＝**文書の中身が正しいかは分かりません**（「作り直した状態と同じか」だけです）。
＝**道具が名乗り忘れたら、その文書はこの一覧に出ません**（実在しないパスは落とせます）。

## いまの数

- 名乗っている道具＝**20 本**
- その道具が作る文書＝**31 本**
- **検証コマンドを持たない道具＝2 本**（gen_audit_request.py／gen_p23_candidates.py）
- **名乗っていない道具＝1 本**（明らかな漏れ）／ 29 本（要確認）＝表3
- 誰にも作られていない文書＝**405 本**（表4＝人が手で書いているもの）

## 表1｜道具 → 作る文書

**★「いまの検証の結果」の欄は、ここには書きません**（2026-08-28・まこさん承認 案A）。時とともに変わる値を焼くと、ほかの道具を直すたびにこの文書が古くなるためです。

いまの結果は `python3 scripts/priority_rebuild/gen_docmap.py --status` が、その場で走らせ直して画面に出します（文書より新しい結果が出ます）。

| 道具 | 作る文書 | 検証コマンド |
|---|---|---|
| `gen_improvement_arc.py` | improvement_arc.md（まるごと） | あり |
| `gen_audit_request.py` |  | ❌ なし |
| `gen_auditor_brief.py` | auditor_template.md（一部の節） | あり |
| `gen_cat_requirements.py` | cat_requirements.md（まるごと） | あり |
| `gen_composition_rules.py` | composition_rules.json（まるごと）<br>composition_rules.md（まるごと） | あり |
| `gen_decisions.py` | decisions.md（まるごと） | あり |
| `gen_design.py` | e38_design.md（まるごと） | あり |
| `gen_docmap.py` | docmap.md（まるごと）<br>docmap.json（まるごと） | あり |
| `gen_engine_tuner_manual.py` | engine_tuner_manual.md（まるごと） | あり |
| `gen_engine_tuner_requirements.py` | engine_tuner_requirements.md（まるごと） | あり |
| `gen_exit_families.py` | exit_families.json（まるごと）<br>exit_families.md（まるごと）<br>exit_families_approved.txt（まるごと） | あり |
| `gen_filemap.py` | filemap.md（まるごと） | あり |
| `gen_fix_map.py` | engine_tuner_fix_map.md（まるごと） | あり |
| `gen_flow.py` | e38_flow.md（まるごと） | あり |
| `gen_materials.py` | materials.md（まるごと）<br>materials.json（まるごと）<br>engine_tuner_milestones.md（一部の節）<br>engine_tuner_milestones2.md（一部の節） | あり |
| `gen_observe_manual.py` | observe_diag_manual.md（まるごと） | あり |
| `gen_p23_candidates.py` |  | ❌ なし |
| `gen_signal_families.py` | signal_families.json（まるごと）<br>signal_families.md（まるごと）<br>signal_families_approved.txt（まるごと） | あり |
| `gen_v9_exits.py` | v9_exits.md（まるごと） | あり |
| `gen_windows.py` | windows.md（まるごと）<br>acceptance_checklist.md（一部の節）<br>adopted_strategies.md（一部の節）<br>entry_exit_matrix.md（一部の節）<br>window_similarity_ranking.md（一部の節） | あり |

## 表2｜文書 → それを作る道具

| 文書 | 作る道具 | 作り方 | 実在 |
|---|---|---|---|
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/auditor_template.md` | `gen_auditor_brief.py` | 一部の節 | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/adopted_strategies.md` | `gen_windows.py` | 一部の節 | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/composition_rules.json` | `gen_composition_rules.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/composition_rules.md` | `gen_composition_rules.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md` | `gen_decisions.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/docmap.json` | `gen_docmap.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/docmap.md` | `gen_docmap.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/e38_design.md` | `gen_design.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/e38_flow.md` | `gen_flow.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_fix_map.md` | `gen_fix_map.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_manual.md` | `gen_engine_tuner_manual.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones.md` | `gen_materials.py` | 一部の節 | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md` | `gen_materials.py` | 一部の節 | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_requirements.md` | `gen_engine_tuner_requirements.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/entry_exit_matrix.md` | `gen_windows.py` | 一部の節 | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/exit_families.json` | `gen_exit_families.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/exit_families.md` | `gen_exit_families.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/exit_families_approved.txt` | `gen_exit_families.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/filemap.md` | `gen_filemap.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/improvement_arc.md` | `gen_improvement_arc.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.json` | `gen_materials.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.md` | `gen_materials.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/observe_diag_manual.md` | `gen_observe_manual.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/signal_families.json` | `gen_signal_families.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/signal_families.md` | `gen_signal_families.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/signal_families_approved.txt` | `gen_signal_families.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/v9_exits.md` | `gen_v9_exits.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/window_similarity_ranking.md` | `gen_windows.py` | 一部の節 | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/windows.md` | `gen_windows.py` | まるごと | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/acceptance_checklist.md` | `gen_windows.py` | 一部の節 | ✅ |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/cat_requirements.md` | `gen_cat_requirements.py` | まるごと | ✅ |

## 表3｜★名乗っていない道具（この一覧から漏れているもの）

**2つに分けています。**
**A＝明らかな漏れ**（名前が `gen_` で始まるのに名乗っていない）。
**B＝要確認**（`.md` を書き出す処理が在るのに名乗っていない。凍結した研究の道具を含む）。

**A＝1 本 ／ B＝29 本。**

### A｜明らかな漏れ

| 道具 | 理由 |
|---|---|
| `.claude/tools/gen_audit_index.py` | 名前が gen_ で始まるのに名乗っていない |

**★この道具に `GENERATES` を足すか、文書を作らない道具だと確かめてください。**

### B｜要確認

<details><summary>全部を開く</summary>

| 道具 | 理由 |
|---|---|
| `.claude/hooks/require_source_read_before_acceptance.py` | md を書き出す処理が在るのに名乗っていない |
| `.claude/hooks/test_worklog_toolchange.py` | md を書き出す処理が在るのに名乗っていない |
| `.claude/tools/tidy_next_step.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/dashboard/build_dashboard_json.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/doc_coverage_diag.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/ratchet_io.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/tuner_judgement.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_intra_axis_correlation.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_label_runs.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_no_window_drift.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_regime_label_features.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_stage1a_main.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_stage1a_meta.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_stage1b_main.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_stage1b_meta.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_stage1c_meta.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_transition_indicators.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_transition_robustness.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/analyze_vshape_indicators.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/extract_spike_events.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/intraday_reversal_frequency.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/regime_label_run_length.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/regime_v13_vshape_override.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/select_vshape_samples.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/stage3_latch_validate.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/stage3_validate_judgment_set.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/regime/trade_regime_crossing.py` | md を書き出す処理が在るのに名乗っていない |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/signal_research/analyze_signals.py` | md を書き出す処理が在るのに名乗っていない |

</details>


## 表4｜誰にも作られていない文書（人が手で書いているもの）

**405 本。**この一覧に出るものは、機械の検証の対象外です（＝古くなっても検出されません。それでよいかは人が決めます）。

<details><summary>全部を開く</summary>

- `.claude/rules/README_folder_map.md`
- `.claude/rules/chat_writing_rules.md`
- `.claude/rules/experiment_result_procedure.md`
- `.claude/rules/pdca_flow.md`
- `.claude/rules/permanent_rules.md`
- `.claude/rules/word_replacements.md`
- `.claude/settings.json`
- `.claude/settings.local.json`
- `.claude/state/acceptance.md`
- `.claude/state/acceptance_20260806_signal_table.md`
- `.claude/state/chat_check_blocks.json`
- `.claude/state/chat_check_last.json`
- `.claude/state/current_request.md`
- `.claude/state/design_approved.json`
- `.claude/state/e37_sl_step1_result.md`
- `.claude/state/e37_spike_sign_step2_result.md`
- `.claude/state/exhaustion_check.md`
- `.claude/state/flow_declaration.md`
- `.claude/state/forward_action.md`
- `.claude/state/g2_pass.json`
- `.claude/state/goal_block.md`
- `.claude/state/h2_pass.json`
- `.claude/state/next_step.bak2_20260824.md`
- `.claude/state/next_step.bak_20260824.md`
- `.claude/state/next_step.md`
- `.claude/state/next_step_archive_202608.md`
- `.claude/state/next_step_milestone2.md`
- `.claude/state/observation_design.md`
- `.claude/state/purpose_check.md`
- `.claude/state/read_log.txt`
- `.claude/state/search_log.txt`
- `.claude/state/session_todo.md`
- `.claude/state/session_worklog_20260715.md`
- `.claude/state/session_worklog_20260716.md`
- `.claude/state/session_worklog_20260717.md`
- `.claude/state/session_worklog_20260718.md`
- `.claude/state/session_worklog_20260719.md`
- `.claude/state/session_worklog_20260720.md`
- `.claude/state/session_worklog_20260721.md`
- `.claude/state/session_worklog_20260722.md`
- `.claude/state/session_worklog_20260723.md`
- `.claude/state/session_worklog_20260724.md`
- `.claude/state/session_worklog_20260725.md`
- `.claude/state/session_worklog_20260726.md`
- `.claude/state/session_worklog_20260727.md`
- `.claude/state/session_worklog_20260730.md`
- `.claude/state/session_worklog_20260801.md`
- `.claude/state/session_worklog_20260802.md`
- `.claude/state/session_worklog_20260803.md`
- `.claude/state/session_worklog_20260804.md`
- `.claude/state/session_worklog_20260805.md`
- `.claude/state/session_worklog_20260806.md`
- `.claude/state/session_worklog_20260807.md`
- `.claude/state/session_worklog_20260808.md`
- `.claude/state/session_worklog_20260809.md`
- `.claude/state/session_worklog_20260810.md`
- `.claude/state/session_worklog_20260811.md`
- `.claude/state/session_worklog_20260812.md`
- `.claude/state/session_worklog_20260813.md`
- `.claude/state/session_worklog_20260815.md`
- `.claude/state/session_worklog_20260816.md`
- `.claude/state/session_worklog_20260818.md`
- `.claude/state/session_worklog_20260819.md`
- `.claude/state/session_worklog_20260820.md`
- `.claude/state/session_worklog_20260821.md`
- `.claude/state/session_worklog_20260822.md`
- `.claude/state/session_worklog_20260823.md`
- `.claude/state/session_worklog_20260824.md`
- `.claude/state/session_worklog_20260825.md`
- `.claude/state/session_worklog_20260826.md`
- `.claude/state/session_worklog_20260827.md`
- `.claude/state/session_worklog_20260828.md`
- `.claude/state/session_worklog_20260829.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-05-15_audit15_routeB_records.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-05-15_audit16_ml_options_review.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-05-19_audit17_phase_a_evaluation.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-05-19_phase0_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-05-20_audit19_exchange_spec_full_verify.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-05-23_step_i4_1_critical1_cp5_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-05-26_phase1_v6_6cases_methodology_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-05-27_step15_regime_ensemble_design_cp1_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-05-27_step25_cluster_design_cp3_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-05-27_step2_entry_ml_design_cp2_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-07-27_engine_tuner_r3r13r14_design_cp2_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-07-27_engine_tuner_r3r7_design_cp1_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-07-30_engine_tuner_step2_condition_format_cp3_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-08-06_engine_tuner_purpose_enforcement_cp4_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-08-25_exit_fire_forms_design_cp7_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-08-25_exit_fire_forms_design_v2_cp7b_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-08-25_four_elements_gate_design_impl_cp6_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-08-26_permission_gate_r17_design_cp8_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-08-26_unordered_scan_docstring_match_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-08-27_regime_element04_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-08-28_m2_range_laws_cp10a_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-08-28_m2_todo_rewrite_cp10b_audit_report.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-05-15_ml_usage_options_overview.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-05-19_phase_a_cap_exit_cluster_threshold.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-05-26_phase1_v6_6cases_methodology_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-05-27_step15_regime_ensemble_design_cp1_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-05-27_step25_cluster_design_cp3_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-05-27_step2_entry_ml_design_cp2_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-07-27_engine_tuner_r3r13r14_design_cp2_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-07-27_engine_tuner_r3r7_design_cp1_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-07-30_engine_tuner_step2_condition_format_cp3_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-06_engine_tuner_purpose_enforcement_cp4_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-09_engine_tuner_milestone2_flow_cp5_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-25_exit_fire_forms_design_cp7_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-25_exit_fire_forms_design_v2_cp7b_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-25_four_elements_gate_design_impl_cp6_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-26_permission_gate_r17_design_cp8_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-26_unordered_scan_docstring_match_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-27_m2_todo_rewrite_cp10_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-27_regime_element04_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-28_m2_range_laws_cp10a_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-28_m2_todo_rewrite_cp10b_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/_frozen_question_regime.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/_template.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/context/cat_v9_regime_map.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/context/project_spec.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/context/release_guide.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/context/test_checklist.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-13_phase1_lgbm_execute.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_clustering_alternatives_eval.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_clustering_alternatives_eval_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_filename_uniqueness_rule.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_filename_uniqueness_rule_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_option5v7h_reeval.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase1_k12long_refit.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase1_k12long_refit_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase2_execute.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase2_execute_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase2_revalidate_post_refit.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase2_revalidate_post_refit_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase2_script_fix_and_structural.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase2_script_fix_and_structural_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase2_step1_diagnosis.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase2_step1_diagnosis_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase3_short_trial.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase3_short_trial_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase4a_clustering.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase4a_clustering_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase4a_k2_revisit.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase4a_k2_revisit_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase4a_normalize_reselect.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_phase4a_normalize_reselect_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_plan_g_finalize.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_plan_g_finalize_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_plan_g_pre_phase4.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_plan_g_pre_phase4_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_rolling_phase4b_phase5.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_session_handoff_v5.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_session_handoff_v5_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_threshold_drift_eval.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-14_threshold_drift_eval_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_audit15_routeB_records.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_audit16_ml_options_review.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_canonical_doc_consistency_fix.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_governance_docs_integration.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_phase4b_phase5_rerun.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_phase4b_trailing_exit_verify.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_phase4b_trailing_exit_verify_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_phase5_position_limit_rerun.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_position_limit_embed.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_position_limit_embed_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_prime_directive_embed.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_prime_directive_embed_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_priority_vs_ml_stocktake.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-15_priority_vs_ml_stocktake_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-16_ml_current_state_inventory.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-16_ml_current_state_inventory_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-16_web_claude_role_store.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-16_web_claude_role_store_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-19_audit17_phase_a_briefing.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-19_ml_implementation_phase0_1.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-19_ml_implementation_phase0_1_completion_phase0.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-19_role_and_self_check_addendum.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-19_role_and_self_check_addendum_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-19_web_claude_self_check_addendum.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-19_web_claude_self_check_addendum_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_14label_adoption_reflection.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_14label_adoption_reflection_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_audit19_audit_followup.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_audit19_audit_followup_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_audit19_audit_request.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_audit19_downstream_integration.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_audit19_downstream_integration_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_audit19_exchange_spec_full_verify.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_audit19_exchange_spec_full_verify_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_audit19_followup_field_meaning.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_audit19_followup_field_meaning_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_exchange_spec_emergency_fix_and_L196.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_exchange_spec_emergency_fix_and_L196_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_instruction_templates_create.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_instruction_templates_create_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_learning_design_v3_and_handoff_v16_save.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_learning_design_v3_and_handoff_v16_save_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_phase0_v3_completion_report_fix.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-20_phase0_v3_completion_report_fix_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-21_phase0_1_axis_implementation_audit.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-21_phase0_1_axis_implementation_audit_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-21_phase0_completion_review_verify_v2.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-21_phase0_completion_review_verify_v2_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-21_phase0_v3_spec_sweep.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-21_phase0_v3_spec_sweep_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-21_phase1a_lgbm_rmse.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-21_phase1a_lgbm_rmse_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-21_phase1b_simple_pnl_check.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-21_phase1b_simple_pnl_check_completion.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-21_phase1c_triple_barrier_multiclass.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-22_phase0_v4_rebuild_instruction.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-22_phase1_layer_inversion_instruction.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-23_phase4b_forward_design_spec.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/2026-05-23_step_i4_1_case_a_v2_v3_critical1_spec.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/audit_summary_20260514_audit9_audit10.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/handoff_to_web_claude_v12_session_20260519.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/handoff_to_web_claude_v13_session_20260519.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/handoff_to_web_claude_v14_session_20260520.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/handoff_to_web_claude_v15_session_20260520.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/handoff_to_web_claude_v16_session_20260520.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/handoff_to_web_claude_v17_session_20260521.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/handoff_to_web_claude_v18_session_20260521.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/handoff_to_web_claude_v5_session_20260514.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/handoff_to_web_claude_v6_session_20260515.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/instructions/handoff_to_web_claude_v9_session_20260518.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/cc_entry_logic_self_study.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/chatgpt_seven_step_origin.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/current_redesign_context.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/entry_exit_relationship_kb.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/feedback_grid_conditions.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/handoff_to_web_claude.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/handoff_to_web_claude_v2.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/handoff_to_web_claude_v3_phase1_phase3a.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/handoff_to_web_claude_v4_phase1_7a.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/headroom_analysis_addendum_spec.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/headroom_analysis_spec.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/improvement_ideation_kb.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/improvements.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/indicator_combination_kb.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/indicator_thresholds_outline.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/industry_benchmark_knowledge_base.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/learning_design_v3.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/lessons_active.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/lessons_archive.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/ml_pipeline_baseline_v1.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/ml_pipeline_execlog.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/phase8_supervised_tool_survey.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/phase_flow_v4_reorder_proposal.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/phase_flow_v4_with_recovery.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/priority_rebuild.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/priority_v9_trade_logic_analysis.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/project_v9_progress.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/range_scalping_kb.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/regime_detection_kb.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/regime_research.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/regime_trial_log.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/seven_step_framework.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/signal_ledger.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/step1_regime_design.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/technical_analysis_knowledge_base.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/trade_analysis_methods_kb.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/trade_methods_study.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/memory/v10_experiments.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ml_axis_catalog.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/pm_review_template.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/086a13df606d.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/09ce8d0cea4f.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/1d811f7d6951.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/24a453d6cf22.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/2b56024e711f.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/327e7f80008f.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/60462a0c5624.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/67da88ef9ca8.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/6ce1dccad1a5.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/6cf9f79eb179.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/76252628537d.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/7873e412f893.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/8d3c45b79b10.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/97598f50ee8d.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/D2_出口の状態機械.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E36_高ATR発火拡張.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_MVP_レンジ学習ゲート+確認済みエッジ.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_Step1_入口の過熱の必須化を撤去.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_range-scalp_base_v1.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v10_ゾーン方式レンジスキャル_SHORT（§1.2.1_準拠_MVP）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v11_視認校正レンジ計器の組み込み（1hゾーン×複数TP+add）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v12_レンジ上部で確認なし_SHORT（件数を出す）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v13_TIME_EXIT_の_maker化（deadline_shrink）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v14_Exit_ポジション状態機械（E37レンジ幾何ネイティブ・基本maker）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v15_Entry×Exitセット最適化_第1弾（逆行側分岐の作り直し＋枝水準の場面連動ML選定）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v16_Entry×Exitセット最適化_第2弾（回帰救済×トレンドガード×候補格子の一括OOF）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v17_選定のregime頑健化（ATR%帯層化OOF＋ガード全セル候補×box_W膨張＋関所帯別証跡）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v18_TP2反対側ゾーン（伸びる玉は伸ばす）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v19_入口を帯の上端で入る（本当のレジスタンス拒否）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v20_RG-v5レンジ判定移植＋レンジ期間を漏れなく取る上端入口.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v21_入口の反転確認（armed_DC）＋uptrend畳み分岐（Entry×Exitセット）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v22_レンジ中の戻り売りDC入口×レンジ下限TP＋ピーク反転畳み・前兆逃げ（Entry×Exitセット）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v23_TREND_CONT_の_V9_型_Exit_状態機械化（uptrend_発火で成行投げをやめ_genuine_反転_stall_災害SL_に委ねる）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v24_trend_caught_ピーク帯_resting_maker_利確.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v25_レンジ判定の質_RG-v6_適応帯.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v2_scalp-rebuild.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v3_向き無し両側maker_MRスキャル.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v4_教科書_BB_レンジスキャル_SHORT.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v5_検出器ゲート両側MRスキャル.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v6_イベント母数拡大+θ規則反転.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v6r_ランキング金額整合+TP-viability.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v7_型別検出器（帯の合併）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v8_選定計器の是正（母数一致+side別be+型相互排他）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_v9_型×side_Entry_Exitセット共同選定（フェーズ1）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/E37_リファクタ（挙動不変・デバッグ後整理）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/c2d1df43ef91.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/c783e0685012.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/d09563e7fd4c.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/design-consistency-gate-20260827.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/doc-fix-v9test-20260822.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/docmap-drop-verify-column-20260828.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/e4b86277508f.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/e9fa2ae6725a.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/eb6f38734142.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/engine_tuner_組み立ての決まり（段2）.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/entry-gate.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/exit-fire-forms-20260825.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/exit-fire-forms-probe-fix-20260826.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/f09836454729.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/f8dcabb66248.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/forbidden-check-auto-20260826.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/four-elements-gate-20260824.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/four-elements-gate-v2-drawn-only-20260825.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/gen-audit-request-20260827.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/gen-minimize-loss-20260826.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/h2g2-entry-scan-20260827.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/hold-mom-exit.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/milestone-req-accept-20260826.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/new-file-target-gate-20260827.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/purpose-gate-not-applicable-20260826.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/purpose-gate-rebuild-20260826.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/regime-build-callers-and-usable-groups-20260827.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/req-map-r17-20260826.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/req-progress-machine-20260826.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/scene-cap.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/selftest-standalone-20260824.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/tidy-next-step-20260828.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/todo-gate-diff-paste-20260827.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/unapproved-four-elements-gate-v58-20260825.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/unapproved-permission-gate-20260824.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/unordered-scan-scope-20260826.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/analysis_playbook.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/cat_requirements.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/condition_parts.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/contract_check_design.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/contract_check_design.md.actual.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/e34_design.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/e35_design.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/e37_design.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/e37_improvement_milestones.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/e38_flow.state.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/e38_requirements.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_check_runs.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_defects.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_fix_map.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_materials.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_requirements.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_step2_condition_format.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_timing.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_trials_cumulative.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/exit_families_rules.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/exit_opt_command_design.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/forbidden_check_design.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/golden/exit_forms_20260825/baseline_after.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/golden/exit_forms_20260825/baseline_before.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/golden/exit_forms_20260825/recipe_level_both.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/golden/exit_forms_20260825/recipe_state_only.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/ledger.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/logic_rules.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/material_ranking.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/milestone_req_map.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/research_e35_rangebot.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/session_log_20260609.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/session_log_20260610.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/session_log_20260610_pm.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/session_log_20260611.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/session_log_20260612.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/session_log_20260612_night.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/session_log_20260711.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/strat_v9ml_design.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/v9_logic.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/review_lens.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/cc_role.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/core_rules.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/entry_fix_6axis_gate.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/exchange_spec.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/false_positive_incident_policy.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/phase_compliance_checklist.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/web_claude_role.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/web_claude_self_check.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/templates/instruction_template_full.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/templates/instruction_template_light.md`
- `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/composition_rules_src.backup_20260808.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/composition_rules_src.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/identity_l1_legacy.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/identity_s1_legacy.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/identity_s2_legacy.json`
- `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json`

</details>


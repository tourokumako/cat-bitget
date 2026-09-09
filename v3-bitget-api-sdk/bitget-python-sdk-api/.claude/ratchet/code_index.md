# コードの目次（読む箇所を指定するための表）

**なぜ在るか**＝2026-09-09 に、CC が 6,310行 のプログラムを「全文 読んだ」と書いて、実際には一部しか見ていませんでした。そのせいで、まこさんが承認済みの仕組みを見落としました。

**使い方**＝設計書を書く前の読むもの宣言に、この表の節の名前と行を書きます。

**作り直し方**＝`python3 .claude/tools/gen_code_index.py --write`。手で書き換えると `--verify` が見つけます。

<!-- CODE_INDEX_START hash=275dfea419ab3025 gen_code_index.py が自動生成＝手で書き換えない -->
**★この表はプログラムが作ります（手で書き換えない）。**出どころ＝コードの `# ══` の見出しと、構文の木で拾った関数。

**読むもの宣言には、ファイル名でなく節の名前を書きます。**「全文を読んだ」と書けなくするためです。

### engine_tuner_gen.py（6,310行・節 23・関数とクラス 131）

| 節の名前 | 行 | 関数とクラス | 数 |
|---|---|---|---|
| （見出しの無い区間） | 1〜189 | `_ordered_like`・`load_limits`・`HoldRangeError`・`resolve_hold_range`・`hold_bars` | 5 |
| 材料の候補プール | 190〜225 | `material_pool` | 1 |
| 材料のパラメータの「範囲」（段A の A-4・2026-08-13） | 226〜942 | `material_ranges`・`param_in_range`・`draw_param`・`_allowed_tfs`・`_check_tf`・`_mat_drawn`・`_mat_two_drawn`・`_mat_pair_drawn`・`_mat_with_pre`・`_mat_fixture`・`_thr_drawn`・`_thr_band_drawn`・`_thr_fixture`・`_nv`・`_iv`・`_iv_from`・`_nvs`・`_nvd`・`_walk_dicts`・`_walk_materials`・`_current_num_bounds`・`assert_provenance`・`assert_roles`・`assert_exit_roles`・`_gate_recipe`・`_is_identity_recipe`・`_cc`・`validate_drawn`・`_vr`・`_scan_direct_validate_calls`・`strip_marks`・`int_range_of`・`draw_int` | 33 |
| 出口の枝などで使う数字の範囲（段A の A-5-2・2026-08-15） | 943〜1023 | `num_range_of`・`draw_num`・`ladder_min_frac`・`max_ladder_steps` | 4 |
| 閾値の段（分位）の範囲（段A の A-5-3・2026-08-15） | 1024〜1148 | `q_range_of`・`quantile_list`・`draw_q`・`q_in_range`・`num_in_range`・`_pool_families`・`_pool_families_by_lineage`・`_as_param_list`・`_from_param_list`・`_range_has_two` | 10 |
| 構造のランダムサンプリング（第1段） | 1149〜1181 | `SampleError`・`_lineage_of`・`_kubun_of` | 3 |
| 型の表（signal_families）＝D1 の閉じ込めの正本（2026-08-07 まこさん承認・指紋つき） | 1182〜1232 | `load_signal_table` | 1 |
| 材料の順位を読む（M2-3-4・2026-08-22 まこさん承認・acceptance 086a13df606d…） | 1233〜1745 | `load_material_ranking`・`ranked_materials`・`_role_tfs`・`_insufficient_samples`・`_banned_pair`・`_banned_name`・`_lineage_candidates`・`_pick_material`・`_pkey`・`same_fn_family_pairs`・`pair_allowed`・`_pair_materials`・`_q`・`_dc1_side`・`_dc2_q`・`_loose_q`・`_make_hysteresis`・`_make_cond`・`_const100` | 19 |
| 出口の表（exit_families）＝D2 の枝の組み立ての正本（2026-08-07 まこさん承認・指紋つき） | 1746〜2094 | `load_exit_table`・`_floor_pct`・`_state_cond`・`_pick_exit_material`・`_exit_indicator_cond`・`_make_exits` | 6 |
| 場面の判定の束を組む（M2-5-1・2026-08-23 まこさん承認 2b56024e711f…） | 2095〜2547 | `_family_tf_from_col`・`_group_usable`・`ranked_groups`・`_ranked_material_at`・`regime_draw_order`・`_flip_loose`・`sample_regime_build`・`default_regime`・`sample_structure`・`recipe_hash`・`write_kakikudashi` | 11 |
| 構造の内訳（機械出力・R3 完了の線⑤） | 2548〜2591 | `structure_breakdown` | 1 |
| 分位の解決表（値決め窓・探索開始時に1回固定・設計書 §5-4） | 2592〜2793 | `_qspec`・`_tree_conds`・`needed_qkeys`・`_geo_of`・`build_qtable` | 5 |
| 材料の組み立て（observe_diag build_features の再利用＝コピー禁止・H2） | 2794〜2893 | `attach_materials` | 1 |
| BH 法（偽発見率の制御・CP1 提案4(e)・監査 4-20） | 2894〜2925 | `pvalue_daily`・`bh_select` | 2 |
| 層化の門（CP1・候補1本1本を ATR% 帯の非悪化で弾く・監査 4-22） | 2926〜2949 | `strat_gate` | 1 |
| journal（途中再開 R12） | 2950〜2982 | `Journal` | 1 |
| 減らしたい損失（要件 R8・まこさん確定 2026-07-27・実装 2026-08-26） | 2983〜3024 | `assert_known_exit_reason`・`_focus_net`・`_obj_key` | 3 |
| 試行の実行（1本＝実行器で売買 → 審判で net） | 3025〜3116 | `run_trial`・`run_trial_guarded`・`reject_code`・`zero_trade_gate`・`per_day_gate` | 5 |
| 第2段（TPE）用＝値スロットの列挙と適用 | 3117〜3307 | `_int_range`・`_q_range`・`suggest_slot`・`value_slots`・`_slot_ref`・`apply_slots`・`read_slots` | 7 |
| 本体＝2段サンプリング | 3308〜3713 | `run_generation` | 1 |
| 検収専用（selftest／--dry-run）＝採否・本走に使わない | 3714〜5715 | `synth_df`・`_selftest_extra_gate`・`selftest_rank_demand`・`selftest` | 4 |
| 本走（2026-08-05 新設・next_step §6.5 の13番） | 5716〜5974 | `pre_run_gate`・`run_main`・`main` | 3 |
| 4要素ゲートの検査の道具（59回目・設計書 v2 の K1〜K9・K14） | 5975〜6310 | `lint_provenance`・`_stage_of`・`gate_matrix`・`verify_provenance` | 4 |

### engine_tuner_exec.py（4,968行・節 15・関数とクラス 104）

| 節の名前 | 行 | 関数とクラス | 数 |
|---|---|---|---|
| （見出しの無い区間） | 1〜69 | — | 0 |
| 形の性質表（M2-2-3b・2026-08-21 まこさん承認 e4b86277…） | 70〜306 | `forms_where`・`forms_pair_in`・`load_indicator_switch`・`indicator_enabled`・`geo_enabled`・`demand_enabled`・`time_enabled`・`indicator_switch_fingerprint`・`_template_from_pattern`・`build_name`・`RecipeError`・`_fail` | 12 |
| ① スキーマ検証器（G1〜G6・設計書 §4） | 307〜391 | `_is_cond`・`_check_not_node`・`_walk`・`_conds_under_not`・`_tree_depth` | 5 |
| 材料の前処理（部品・2026-08-13・段C の C-6） | 392〜509 | `pre_ops`・`_since_stat`・`_apply_pre`・`_pre_of` | 4 |
| 材料2本を組む部品（2026-08-12・段C の C-6・部品 div・corr） | 510〜1033 | `pair_ops`・`_pair_op_of`・`_pair_key`・`_pair_series`・`_material_name`・`_check_int_range`・`_check_param_range`・`_check_num_range`・`_check_q_range`・`_material_family`・`_check_value`・`_check_hysteresis`・`_has_ref`・`_check_exit_fire_cond`・`_check_cond` | 15 |
| 相場の宣言（監査 4-19／要件 R5・2026-08-03 新設） | 1034〜1093 | `_check_bool_cond`・`_walk_build_tree` | 2 |
| G7 場面ごとの相場の法則（M2-B0・2026-08-30 まこさん承認 iter="m2-b0-law-reader-20260830"） | 1094〜1858 | `_dirless_parts`・`_refs_prop`・`regime_law_counts`・`_validate_law`・`load_regime_laws`・`_upper_tfs`・`_law_count_and`・`_law_count`・`_scene_scan`・`_check_scene_rules`・`_check_regime_meta`・`regime_cols`・`_regime_series`・`cap_of`・`validate_recipe`・`_check_level` | 16 |
| ② 実行器（共通の売買ループ・設計書 §1〜§7 の意味論） | 1859〜1912 | `_side_cmp`・`_vnum`・`_vnum_q` | 3 |
| 材料をその場で作る（段A の A-2b・2026-08-13） | 1913〜2879 | `material_array`・`_col_array`・`_mat_key`・`_hold_state`・`_eval_cond`・`_eval_tree`・`build_regime_columns`・`_entry_fire`・`_swing_key`・`_swing_specs`・`_static_level_px`・`_resolve_levels`・`_ceiling_fire`・`_guards_ok`・`_peak_giveback_level`・`_fire_key`・`_collect_fire_cols`・`_exit_fire_ok`・`run_recipe` | 19 |
| ③ 恒等検収（設計書 §8・fix_map 歩3 の検収の定義） | 2880〜3046 | `identity_recipe`・`engine_params_from_recipe`・`_sentinel_df`・`_ordering_sentinel`・`_md5_trades`・`run_identity` | 6 |
| 材料列の付け足し（歩6・監査 4-17 の接続・まこさん GO 2026-08-02） | 3047〜3185 | `legacy_cols_in`・`demand_cols_in`・`attach_demand_columns`・`source_logic`・`attach_recipe_columns` | 5 |
| ③-2 恒等検収 L1（歩6-1・まこさん GO 2026-08-02＝採用中 L1 をレシピで書き写す・fix_map 歩6） | 3186〜3275 | `identity_l1_recipe`・`l1_engine_params`・`_l1_attach_legacy_cols`・`run_identity_l1` | 4 |
| ③-3 恒等検収 S1 里程標1（歩6-1 後半・まこさん指示 2026-08-02「S1 の書き写しを続けて」） | 3276〜3613 | `identity_s1_recipe`・`s1_engine_params`・`_attach_v59_cols`・`_attach_v47_cols`・`run_identity_s1` | 5 |
| 手数料の分類の食い違い検査（2026-08-02 まこさん OK で「丸ごと比較」から直した） | 3614〜3698 | `maker_taker_sync_check`・`e36_maker_taker_behavior_check` | 2 |
| 自己検査（番人＝わざと壊したレシピ18種で全部止まる・正しい2種は通る・設計書 §10＋歩4 拡張） | 3699〜4968 | `_base_ok_recipe`・`_selftest_4_19`・`_selftest_roundtrip`・`unordered_iteration_scan`・`selftest`・`main` | 6 |
<!-- CODE_INDEX_END -->

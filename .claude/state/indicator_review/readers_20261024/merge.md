# 指標の情報に触る行の一覧（読む係9人の報告から gen_reader_merge.py が作った・手で書き替えない）

振り分け＝持つ→①（okd_plan5:V15）と②（okd_plan5:V05・V30）／読む→③（okd_plan5:V04・V28）／作る・自前で計算ほか→OK の返信に書いていない。

行の合計＝721（①② 282・③ 245・OK の返信に書いていない 194）

## ファイルごとの数

| ファイル | ①② | ③ | OK の返信に書いていない |
|---|---|---|---|
| observe_diag.py | 59 | 51 | 52 |
| engine_tuner_exec.py | 21 | 36 | 14 |
| indicator_reference_diag.py | 23 | 10 | 26 |
| e37_range_scalp.py | 16 | 9 | 26 |
| e38_logic_parts.py | 3 | 10 | 12 |
| gen_materials.py | 0 | 15 | 7 |
| e36_short_oscillation.py | 9 | 3 | 9 |
| e35_range_oscillation.py | 6 | 6 | 7 |
| e38_logics.json | 16 | 0 | 0 |
| e37.py | 7 | 4 | 4 |
| gen_signal_families.py | 4 | 3 | 8 |
| gen_indicator_table.py | 5 | 7 | 2 |
| gen_acceptance.py | 4 | 9 | 1 |
| regime_r9_diag.py | 3 | 10 | 0 |
| leak_causality_diag.py | 2 | 6 | 2 |
| engine_tuner_fire_diag.py | 3 | 6 | 1 |
| gen_regime_kb.py | 1 | 7 | 2 |
| gen_indicator_switch.py | 1 | 7 | 2 |
| regime_label.py | 2 | 3 | 4 |
| signal_families.json | 9 | 0 | 0 |
| indicator_fix_plan.json | 9 | 0 | 0 |
| pre_audit_check.py | 3 | 2 | 4 |
| gen_observe_manual.py | 2 | 6 | 0 |
| e38.py | 0 | 6 | 2 |
| engine_tuner.py | 2 | 5 | 0 |
| observe_config.json | 7 | 0 | 0 |
| materials.json | 6 | 0 | 0 |
| check_indicator_sources.py | 2 | 4 | 0 |
| gen_stage0_match.py | 2 | 3 | 1 |
| gen_s22_combi.py | 1 | 5 | 0 |
| analyze.py | 3 | 0 | 2 |
| condition_parts_diag.py | 3 | 1 | 1 |
| regime_laws.json | 5 | 0 | 0 |
| gen_v9_exits.py | 2 | 2 | 1 |
| gen_audit_request.py | 3 | 1 | 0 |
| report.py | 3 | 0 | 1 |
| tuner_judgement.py | 1 | 2 | 1 |
| indicator_switch.json | 4 | 0 | 0 |
| material_ranking.json | 4 | 0 | 0 |
| precheck.py | 2 | 0 | 1 |
| tuner_backcalc.py | 0 | 2 | 0 |
| ratchet_guards.py | 2 | 0 | 0 |
| identity_s1_legacy.json | 2 | 0 | 0 |
| identity_s2_legacy.json | 2 | 0 | 0 |
| r9_demand_fixture.json | 2 | 0 | 0 |
| composition_rules_src.backup_20260808.json | 2 | 0 | 0 |
| exit_families.json | 2 | 0 | 0 |
| m2_stage_candidates.json | 2 | 0 | 0 |
| indicator_params_review.json | 2 | 0 | 0 |
| gen_audit_docs.py | 0 | 1 | 1 |
| gen_exit_families.py | 0 | 2 | 0 |
| gen_composition_rules.py | 1 | 1 | 0 |
| search_limits.json | 1 | 0 | 0 |
| identity_l1_legacy.json | 1 | 0 | 0 |
| exit_families_rules.json | 1 | 0 | 0 |
| composition_rules.json | 1 | 0 | 0 |
| condition_parts.json | 1 | 0 | 0 |
| indicator_roles_thresholds.json | 1 | 0 | 0 |
| indicator_params_by_strategy.json | 1 | 0 | 0 |

## 全部の行

| 報告 | ファイル | 行 | 名前 | 持つ／読む／作る（報告の欄のまま） | どの情報か（報告の欄のまま） | 振り分け |
|---|---|---|---|---|---|---|
| a385a4c | analyze.py | 54-55 | _load | 自前で計算 | ATR% | OK の返信に書いていない |
| a385a4c | analyze.py | 65-75 | _auto_ind_cols | 自前で判断 | どの列が指標か | OK の返信に書いていない |
| a385a4c | condition_parts_diag.py | 46-212 | p_value〜p_cross_val | 自前で計算 | 前処理の式・条件の形の式 | OK の返信に書いていない |
| aac5aa5 | e35_range_oscillation.py | 85-93 | add_choppiness | 自前で計算 | Choppiness Index | OK の返信に書いていない |
| aac5aa5 | e35_range_oscillation.py | 96-105 | add_jump_model | 自前で計算 | Efficiency Ratio | OK の返信に書いていない |
| aac5aa5 | e35_range_oscillation.py | 144-171 | _build_signals_for_tf | 作る | er の分位・chop>61.8・adx<25・stoch k<30 で上向き／k>70 で下向き | OK の返信に書いていない |
| aac5aa5 | e35_range_oscillation.py | 174-181 | _w_band | 作る | 箱の幅の分位 | OK の返信に書いていない |
| aac5aa5 | e35_range_oscillation.py | 250-262 | _hold_feat_vec | 作る | atr/close×100 ほか | OK の返信に書いていない |
| aac5aa5 | e35_range_oscillation.py | 466-474 | _load | 作る | 指標の列を付ける順番 | OK の返信に書いていない |
| aac5aa5 | e35_range_oscillation.py | 477-488 | add_htf_macd | 自前で計算 | 1h MACD line の符号 | OK の返信に書いていない |
| aac5aa5 | e36_short_oscillation.py | 74-82 | add_choppiness | 自前で計算 | Choppiness | OK の返信に書いていない |
| aac5aa5 | e36_short_oscillation.py | 85-94 | add_jump_model | 自前で計算 | ER | OK の返信に書いていない |
| aac5aa5 | e36_short_oscillation.py | 132-159 | _build_signals_for_tf | 作る | e35 と同じ（30・70 は :153-154） | OK の返信に書いていない |
| aac5aa5 | e36_short_oscillation.py | 175-186 | add_htf_macd | 自前で計算 | 1h MACD の符号 | OK の返信に書いていない |
| aac5aa5 | e36_short_oscillation.py | 280-303 | _hold_arrays | 自前で計算 | realized vol（log リターンの二乗和の平方根）（:286-291）・htf_macd_up | OK の返信に書いていない |
| aac5aa5 | e36_short_oscillation.py | 378-396 | _widen_short_zone | 作る | er の分位でゾーンを広げる | OK の返信に書いていない |
| aac5aa5 | e36_short_oscillation.py | 400-427 | _short_rev_nofloor | 作る | stoch_k の下降（:422-423） | OK の返信に書いていない |
| aac5aa5 | e36_short_oscillation.py | 469-477 | donchian_pos | 自前で計算 | donchian の位置（20 本） | OK の返信に書いていない |
| aac5aa5 | e36_short_oscillation.py | 1081-1096 | scene | 作る | atr_14/entry_price・stoch_k の中央値 | OK の返信に書いていない |
| aac5aa5 | e37.py | 159-167 | coverage | 作る | 指標の列の名前 | OK の返信に書いていない |
| aac5aa5 | e37.py | 175-180 | series_bank | 自前で計算 | 基準線 26 からの乖離%（(高値26の最大＋安値26の最小)/2） | OK の返信に書いていない |
| aac5aa5 | e37.py | 257-275 | _apply_s1 | 作る（レシピの値） | th_down_di14 → V59DOWN、th_flat_kijun26 → V59FLAT | OK の返信に書いていない |
| aac5aa5 | e37.py | 305-321 | run | 作る | 指標の名前を定数の名前へ言い換える | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 248-255 | micro_rev_event | 作る | dev_z の閾値から候補を作る | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 259-268 | _add_htf_macd | 自前で計算 | 1h MACD line の符号 | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 271-307 | _gen_events_v6 | 自前で計算 | BB(20,2σ) のバンド＝sma±BB_K×std・donchian 20（rolling max/min の shift(1)）・dev_z | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 311-322 | _tp_viable | 作る | sma∓0.5σ の TP に届くか | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 326-377 | _teacher_labels | 作る | SL＝ATR×2、TP＝sma∓0.5σ | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 734-749 | _entry_variants_v9 | 自前で計算 | 足の実体比 >0.5・htf_macd_up | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 752-759 | _tp_viable_k | 作る | sma∓tp_k σ | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 762-812 | _teacher_labels_v9 | 作る | ATR の SL・sma/std の TP | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1329-1335 | _rsi9_v10 | 自前で計算 | RSI9（rolling(9) の単純平均） | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1338-1412 | _zones_v10 | 自前で計算 | ピボットのゾーン・出来高の 20 平均（:1349） | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1423-1432 | v10_entry_candidates | 作る | RSI9 の前の値 >70 かつ下向き | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1493-1551 | _zones_v11_1h | 自前で計算 | 1h リサンプル（label=right）の fractal ゾーン | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1554-1570 | _apply_v11_to_5m | 作る | v11_res_lo/hi・sup_lo/hi・mid・range_ok_v11 | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1591-1608 | v22_uptrend_warning | 自前で計算 | 15分足の高安の切り上げ・陽線2本・90分の最小 close | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1625-1641 | v11_entry_candidates | 作る | RSI9 の前の値 >70（:1638） | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1686-1698 | range_break_check_v15 | 作る | 出来高 > 20 平均 | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1751-1765 | _attach_v16_bb | 自前で計算 | BB20 2σ・BBW＝4×sd20/mid20×100・rolling(288) の q0.9 の shift(1)・出来高 20 平均の shift(1) | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1802-1804 | （v15） | 自前で計算 | 出来高 rolling(20) の shift(1) | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1839-1843 | dc21 | 自前で計算 | stoch(9,3) の %K・%D とデッドクロス | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1862-1865 | _hh26・_ll26 | 自前で計算 | 直近の高安（v26_touch_hours×12 本） | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1872-1874 | _rhdn26 | 自前で計算 | 直近の高値（v26_down_hours×12 本）の shift(1) | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1895-1897 | low22 | 自前で計算 | 直近 M 本の low の shift(1) | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 1906-1910 | k9・d9 | 自前で計算 | stoch(9,3)（:1839 と同じ式） | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 2631-2637 | _v17_band_idx | 作る | ATR% の帯 | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 3066-3067 | （v17） | 作る | CSV からの ATR%・帯 | OK の返信に書いていない |
| aac5aa5 | e37_range_scalp.py | 4309-4315 | _load | 作る | atr_pct＝atr/close×100（:4314） | OK の返信に書いていない |
| aac5aa5 | e38.py | 178-190 | coverage | 作る | 確認部品の名前（confirm_htf・confirm_vol の choices）。注記に「96種 × 8足 = 768列」とある | OK の返信に書いていない |
| aac5aa5 | e38.py | 246-256 | series_bank | 自前で計算 | dev_z_abs・ret12_abs_down（close.pct_change(12)）・e38_htf_*/e38_vol_* の列 | OK の返信に書いていない |
| aac5aa5 | e38_logic_parts.py | 37-39 | _resample_htf | 自前で計算 | 上位足（label=left・closed=left） | OK の返信に書いていない |
| aac5aa5 | e38_logic_parts.py | 42-52 | _adx_di_htf | 自前で計算 | ADX/DI（Wilder の ewm） | OK の返信に書いていない |
| aac5aa5 | e38_logic_parts.py | 61 | e38_stoch_d | 自前で計算 | stoch_k の rolling(3) | OK の返信に書いていない |
| aac5aa5 | e38_logic_parts.py | 62 | e38_vol_ma20 | 自前で計算 | 出来高の rolling(20) | OK の返信に書いていない |
| aac5aa5 | e38_logic_parts.py | 74 | e38_htf_roc24_2h | 自前で計算 | ROC 24・2h | OK の返信に書いていない |
| aac5aa5 | e38_logic_parts.py | 75-76 | e38_htf_macd_2h | 自前で計算 | MACD 2h | OK の返信に書いていない |
| aac5aa5 | e38_logic_parts.py | 77-78 | e38_htf_di7_4h | 自前で計算 | DI 差 7・4h | OK の返信に書いていない |
| aac5aa5 | e38_logic_parts.py | 79-80 | e38_htf_adx14_2h | 自前で計算 | ADX 14・2h | OK の返信に書いていない |
| aac5aa5 | e38_logic_parts.py | 81-83 | e38_htf_stochd14_2h | 自前で計算 | stoch %K14 の rolling(3)・2h | OK の返信に書いていない |
| aac5aa5 | e38_logic_parts.py | 84-85 | e38_vol_volr20_15m・volr50_15m | 自前で計算 | 出来高比 20・50・15m | OK の返信に書いていない |
| aac5aa5 | e38_logic_parts.py | 86 | e38_vol_bbw50_1d | 自前で計算 | BB 幅 50・1D | OK の返信に書いていない |
| aac5aa5 | e38_logic_parts.py | 87-88 | e38_vol_donch20_1d | 自前で計算 | donchian 幅 20・1D | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 250〜265 | _template_from_pattern・FAMILY_TEMPLATES | 作る | 列名の組み立ての型（種類ごと） | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 268〜286 | build_name | 作る | 列名（family と param から作る） | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 298 | GEO_COLS | 作る | レンジ幾何の列名の一覧 | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 1213〜1219 | _refs_prop | 作る | 種類から性質（prop）への対応 | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 2105〜2115 | _mat_key | 作る | 分位の表の鍵（列名と前処理） | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 2187〜2190 | _eval_cond の candle_dir | 作る | ローソクの向き | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 2212・2220・2244 | slope・slope_avg・diff の鍵 | 作る | 分位の表の鍵の形 | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 2477〜2479 | _ceiling_fire | 作る | 直近高値（rolling max）と、下落型の判定 | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 2684〜2692 | run_recipe の geo | 作る | レンジ幾何の式 | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 2697〜2703 | run_recipe の swing | 作る | 直近 m 本の安値・高値 | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 2727〜2730 | run_recipe の range_break | 作る | 出来高の平均（当該バーを除く） | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 3322〜3340 | _l1_attach_legacy_cols | 作る | L1 の材料列（e37_l1_in_sup・e37_l1_isdn） | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 3435〜3454 | _attach_v59_cols | 作る | DI差14（Wilder の alpha 1/14）と 基準線26 の乖離% | OK の返信に書いていない |
| a2fcbbd | engine_tuner_exec.py | 3457〜3477 | _attach_v47_cols | 作る | 15分足の RSI9（alpha 1/9）と BB(20, 2σ) の上抜け | OK の返信に書いていない |
| a385a4c | engine_tuner_fire_diag.py | 155-169 | build_geo | 自前で計算 | レンジ幾何の列名と式 | OK の返信に書いていない |
| aa6cd8e | gen_acceptance.py | 801-809 | _hit_names | 作る | 文の中の指標名を当てる（長い名前から当てる） | OK の返信に書いていない |
| aa6cd8e | gen_audit_docs.py | 1048-1053・:1463・:1877 | need_reads ほか | ファイル名だけ | — | OK の返信に書いていない |
| ace0f74 | gen_indicator_switch.py | 101-132 | `_abbrev`・`ta_map_by_abbrev` | 作る（候補だけ） | ta の略号との対応 | OK の返信に書いていない |
| ace0f74 | gen_indicator_switch.py | 298-352 | `build` | 作る | オン・オフの印 | OK の返信に書いていない |
| a97a087 | gen_indicator_table.py | 133-142 | `render` | 作る | INDICATOR_TABLE の本文と hash | OK の返信に書いていない |
| a97a087 | gen_indicator_table.py | 212-258 | `main`（--add は 236-237） | 作る・書く | 新しい行 | OK の返信に書いていない |
| ace0f74 | gen_materials.py | 185-206 | `_row_engine` | 作る（判定） | 指標ごとに選べるか | OK の返信に書いていない |
| ace0f74 | gen_materials.py | 222-266 | `_gaps` A〜G | 作る | 足りない指標・時間足 | OK の返信に書いていない |
| ace0f74 | gen_materials.py | 613-632 | `_param_kinds` | 作る | パラメータが整数か小数か | OK の返信に書いていない |
| ace0f74 | gen_materials.py | 908-931 | 番人④ | 直書き | RSI 14 5m・閾値 70 | OK の返信に書いていない |
| ace0f74 | gen_materials.py | 1227-1327 | `build_body` | 作る | 1行に1つの family の、系統・答える問い・使える役割・出どころ・状態 | OK の返信に書いていない |
| ace0f74 | gen_materials.py | 1275-1285 | `_extra` | 作る | 需給・時間帯・レンジ幾何の行 | OK の返信に書いていない |
| ace0f74 | gen_materials.py | 2131-2169 | `bans_count_block` | 作る | 向きを持たない部品の数・指標の種類の数・部品の数 | OK の返信に書いていない |
| aa6cd8e | gen_regime_kb.py | 1088-1107 | match_families | 作る | 名前の対応表（語から正本の指標名へ） | OK の返信に書いていない |
| aa6cd8e | gen_regime_kb.py | 1266-1372 | build_stage | 作る（文書） | 語・指標名・系統・前処理の表 | OK の返信に書いていない |
| ace0f74 | gen_signal_families.py | 93-101 | `_window_days` | 作る | 部品×時間足の窓の日数 | OK の返信に書いていない |
| ace0f74 | gen_signal_families.py | 111-123 | ban_direction・ban_note・kubun | 作る | 方向の区分と、向きの禁止 | OK の返信に書いていない |
| ace0f74 | gen_signal_families.py | 125-134 | ban_samples | 作る | 標本が足りない部品×時間足 | OK の返信に書いていない |
| ace0f74 | gen_signal_families.py | 141-145 | lineage_of | 作る | 部品ごとの系統（鍵は部品の名前） | OK の返信に書いていない |
| ace0f74 | gen_signal_families.py | 157-171 | limits_copy | 写す | 閾値・格子 | OK の返信に書いていない |
| ace0f74 | gen_signal_families.py | 199-225 | extra_parts geo/time/demand | 作る | 別枠の部品 | OK の返信に書いていない |
| ace0f74 | gen_signal_families.py | 691-738 | `_families_of`・`table_ranges` | 作る | family ごとのパラメータの範囲（表の数字の最小と最大） | OK の返信に書いていない |
| ace0f74 | gen_signal_families.py | 741-764 | `_part_allowed` | 判定する | 部品が表の範囲の中か | OK の返信に書いていない |
| aa6cd8e | gen_stage0_match.py | 64 | CANDS | 在るかだけ見る | §2.2 の段の候補 | OK の返信に書いていない |
| aac5aa5 | gen_v9_exits.py | 80-109 | _indicator_aliases | 作る | 変数の名前から指標の列の名前へ | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 55-116 | `_swv`・`_roll`・`_wilder`・`_ema_rec`・`_tr`・`_div` ほか | 作る | tb の計算の部品 | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 120-191 | `_mk`・`_up`・`_dn`・`_flat`・`_alt_pm1`・`_range_case`・`_vp_case`・`_VP_LO`〜`_VP_D_HI` | 作る | known の入力 | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 195-754 | `_tb_rsi`(195)〜`_tb_sr_touch`(747)、`_known_sr_touch_atr1h`(717) | 作る | tb（照らすための独立の実装） | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 758-853 | `_ext_rsi`〜`_ext_keltner` | 作る | ext（ta との照合） | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 862-915 | `_x2_*` | 作る | ext2（2つ目の照合） | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 1321-1759 | `_r` 71行（ループ 1700-1715 の f 文字列の `_r` 3行で6種） | 作る | トレンド・モメンタム（1321-1392）、ボラ（1393-1418）、出来高（1419）、ローソク（1423-1457）、形（1458-1489）、山と谷（1490-1517）、位置（1518-1602）、構造（1603-1680）、日で区切る VP（1700-1715）、MMI・S-R（1727-1772） | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 1701 | `_r(rf"close vs {_vpk}POC%" …)` | 作る（ループの中） | 前日POC・当日POC | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 1706 | `_r(rf"close vs {_vpk}VAH%" …)` | 作る（ループの中） | 前日VAH・当日VAH | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 1711 | `_r(rf"close vs {_vpk}VAL%" …)` | 作る（ループの中） | 前日VAL・当日VAL | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 1777-2028 | `_tb_fractal_marks`・`_tb_w_fr`・`_tb_sr_fr`・`_tb_sr_fr_atr1h`・`_tb_smc_fr`・`_tb_tol_1h`・`_tb_band_swing` | 作る | tb | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 1931-1948 | `_r` 3行 | 作る | W字確定谷・S-Rタッチ確定数・S-Rタッチ確定1時間ATR | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 2173-2224 | `_r` 11行 | 作る | 帯の部品8種・LeeMykland 2種・SMC_SWEEP確定 | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 2232-2372 | `_tb_rvol_rv`〜`_thermo_in_case` | 作る | K-3c の tb | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 2375-2440 | `_r` 15行 | 作る | K-3c の教科書の版。例＝realized_vol_rv、SQZ_ON_Carter | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 2454-3355 | `_lin`〜`_tb_slp_zlma` | 作る | 業界の指標の tb | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 3359-3591 | `_tb_pos_hilo`〜`_ext_cci` | 作る | tb と ext | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 3595-4076 | `_r` 143行 | 作る | ao〜lrsi（3595-3675）、macdext〜stc（3682-3760）、stochf〜willr（3766-3800）、overlap 3回（3818-3978）、trend（3984-4076） | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 4093-4280 | `_clv_ad`〜`_bar_vslope`・`_ext_efi`・`_ext_eom`・`_ext_pvt_slope` | 作る | 出来高の tb・ext・合成バー | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 4287-4408 | `_r` 14行 | 作る | ADOSC比〜出来高変化率% | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 4415-4483 | statistics の tb | 作る | tb | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 4486-4515 | `_r` 7行 | 作る | skew〜VOSC | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 4533-4703 | volatility の tb | 作る | tb | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 4706-4785 | `_r` 16行 | 作る | close vs ABER_ZG%〜UI | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 4814-4993 | `_ht_indep`・`_tb_ebsw`・`_msw_indep` ほか | 作る | tb | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 4996-5052 | `_r` 10行 | 作る | EBSW〜MSW_LEAD | OK の返信に書いていない |
| a97a087 | indicator_reference_diag.py | 5146-5194 | `_r` 8行 | 作る | 実体幅比〜HA下ヒゲ比 | OK の返信に書いていない |
| a385a4c | leak_causality_diag.py | 383,407 | _sab・_sab_hl | 自前で計算（テスト用にわざと壊す） | 列の名前 | OK の返信に書いていない |
| a385a4c | leak_causality_diag.py | 560-583 | _sab_local・_sab_global・_sab_lucky | 自前で計算（テスト用） | 列の名前 | OK の返信に書いていない |
| aecb27a | observe_diag.py | 263-269 | `_rsi` | 作る | 計算の式（RSI） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 272-274 | `_atr` | 作る | 計算の式（ATR・ewm 版） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 277-285 | `_adx_di` | 作る | 計算の式（ADX・+DI・−DI） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 288-293 | `_rci_slow` | 作る | 計算の式（RCI・答え合わせ用の遅い版） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 296-328 | `_rci` | 作る | 計算の式（RCI・速い版） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 331-358 | `_supertrend` | 作る | 計算の式（Supertrend） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 361-374 | `_vp_levels` | 作る | 計算の式（POC・VAH・VAL・移動窓） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 377-398 | `_vp_one` | 作る | 計算の式（出来高プロファイルの1窓） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 401-428 | `_vp_by_day` | 作る | 計算の式（前日・当日の POC・VAH・VAL） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 431-449 | `_sr_touch` | 作る | 計算の式（S-Rタッチ数） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 493-509 | `_atr_pct_1h_on` | 作る | 計算の式（1時間足の ATR%） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 512-521 | `_sr_touch_atr` | 作る | 計算の式（S-Rタッチ1時間ATR） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 524-565 | `_mmi` | 作る | 計算の式（MMI） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 568-578 | `_w_flag` | 作る | 計算の式（W字） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 581-603 | `_fractal_levels` | 作る | 計算の式（直近と1つ前の山・谷） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 606-622 | `_fractal_marks` | 作る | 計算の式（確定した山・谷） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 625-654 | `_w_fractal` | 作る | 計算の式（W字確定谷） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 657-675 | `_sr_touch_fractal` | 作る | 計算の式（S-Rタッチ確定数） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 678-683 | `_sr_touch_fractal_atr` | 作る | 計算の式（S-Rタッチ確定1時間ATR） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 715-728 | `_band_cluster` | 作る | 計算の式（スイングを束ねて帯にする） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 731-752 | `_band_swing` | 作る | 計算の式（帯スイング） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 755-769 | `_band_lines` | 作る | 計算の式（帯pivot・帯VA） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 772-775 | `_band_tol_1h` | 作る | 計算の式（帯の許容幅＝1時間足の ATR%） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 793-797 | `_band_material` | 作る | 名前・方向＋計算の式 | OK の返信に書いていない |
| aecb27a | observe_diag.py | 809-816 | `spike_threshold` | 作る | 閾値（Lee-Mykland の L*） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 819-831 | `spike_stat` | 作る | 計算の式（LeeMykland_E36版） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 834-850 | `lee_mykland_stat` | 作る | 計算の式（LeeMykland・論文の版） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 853-864 | `_smc_sweep_fractal` | 作る | 計算の式（SMC_SWEEP確定） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 922-925 | `_tdseq` | 作る | 計算の式（TD_SEQ） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 928-969 | `_mama`・`_ck`・`_ps`・`_kv`・`_ab`・`_acb`・`_cel`・`_hw`・`_th`・`_ha` | 作る | ライブラリとの対応・計算の式 | OK の返信に書いていない |
| aecb27a | observe_diag.py | 973-981 | `_vfi` | 作る | 計算の式（VFI・教科書の版） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 984-1010 | `_ebsw` | 作る | 計算の式（EBSW） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 1018-1022 | `_reg` | 作る | 種類を表に1行登録する | OK の返信に書いていない |
| aecb27a | observe_diag.py | 1025-1048 | `_MAT_RE`・`find_material` | 作る | 名前の対応（列の名前→種類とパラメータ） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 1051-1065 | `make_material` | 作る | 列の名前・計算の式・方向 | OK の返信に書いていない |
| aecb27a | observe_diag.py | 1219-1241 | `_pivot_prev_period` | 作る | 計算の式（前の日・月・年・週の pivot） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 1539-1544 | for で `_reg` | 作る | 種類・名前の型 | OK の返信に書いていない |
| aecb27a | observe_diag.py | 1964-1980 | `build_catalog` の帯の部分 | 作る | 帯8種の組 | OK の返信に書いていない |
| aecb27a | observe_diag.py | 2061-2067 | FWMA の本数の判定 | 作る | パラメータの範囲 | OK の返信に書いていない |
| aecb27a | observe_diag.py | 2088-2090 | MMAR の重複の除外 | 作る | オン・オフ | OK の返信に書いていない |
| aecb27a | observe_diag.py | 2233-2235 | `_resample` | 作る | 時間足の集計 | OK の返信に書いていない |
| aecb27a | observe_diag.py | 2356-2379 | `insp5_frame` | 作る | 時間足の枠 | OK の返信に書いていない |
| aecb27a | observe_diag.py | 2382-2423 | `build_features` | 作る | 列の名前（`{名前}__{足}`）・時間足・方向 | OK の返信に書いていない |
| aecb27a | observe_diag.py | 2459-2481 | `build_range_geometry` | 作る | レンジ幾何の列8本 | OK の返信に書いていない |
| aecb27a | observe_diag.py | 3494-3499 | `_sk_crash_rebound_long` | 作る | 指標（出来高の平均・値動きの率） | OK の返信に書いていない |
| aecb27a | observe_diag.py | 4424-4448 | `_insp_close_leak` | 作る | 時間足（上の足が漏れないか） | OK の返信に書いていない |
| af05308 | observe_diag.py | 4987-5015 | `_direction_gap`・`_insp_direction_gap` | 作る | 「距離%」が在って「傾き」が無い種類 | OK の返信に書いていない |
| af05308 | observe_diag.py | 5260-5344 | `_dup_pairs`・`_insp_duplicates` | 作る | 同じ挙動の組・暖機の本数 | OK の返信に書いていない |
| af05308 | observe_diag.py | 5368-5373 | `_v9_families` | 作る | V9 が計算している family | OK の返信に書いていない |
| af05308 | observe_diag.py | 6073 | `_OSC_BOUNDS` | 作る | 値域（有界） | OK の返信に書いていない |
| af05308 | observe_diag.py | 6076 | `_OSC_PCTL` | 作る | 値域（分位） | OK の返信に書いていない |
| af05308 | observe_diag.py | 6873-6918 | `_insp_regime_rank` | 作る（書く） | 材料の順位 | OK の返信に書いていない |
| aa6cd8e | pre_audit_check.py | 46-55 | ORDER | 作る（道具を走らせる） | 型の表・印・材料の文書・G2・H2 を作り直す順番 | OK の返信に書いていない |
| aa6cd8e | pre_audit_check.py | 63-98 | CHECKS | 作る（走らせる） | 指標の検査 | OK の返信に書いていない |
| aa6cd8e | pre_audit_check.py | 232-252 | materials_row | 作る | 材料の検査が通ったときの指紋 | OK の返信に書いていない |
| aa6cd8e | pre_audit_check.py | 705-709 | --check-indicator-sources | 作る（走らせる） | 照らしの道具を、そのまま呼ぶ | OK の返信に書いていない |
| a385a4c | precheck.py | 121,167 | main | 自前で計算 | ATR% | OK の返信に書いていない |
| a385a4c | regime_label.py | 109-126 | er_median | 自前で計算 | ER（まっすぐ進んだ距離 ÷ 実際に歩いた距離）と、値動きの大きさの比 | OK の返信に書いていない |
| a385a4c | regime_label.py | 130-197 | _line・band_range | 自前で計算 | 山と谷・跳ね返しの帯・帯の幅 | OK の返信に書いていない |
| a385a4c | regime_label.py | 217-357 | local_scale・zigzag_adaptive・legs_of・trend_mask・box_stats・step_mask・oscillates・_range_on | 自前で計算 | 値動きの幅・ジグザグ・箱・段差・行き来 | OK の返信に書いていない |
| a385a4c | regime_label.py | 367-371 | hindsight_range | 自前で計算 | 時間足のまとめ（resample） | OK の返信に書いていない |
| a385a4c | report.py | 362-365 | G節 | 自前で計算 | ATR%・stoch のギャップ | OK の返信に書いていない |
| a385a4c | tuner_judgement.py | 208-232 | atr_bands | 自前で計算 | ATR% と帯ごとの比べ | OK の返信に書いていない |
| a385a4c | analyze.py | 40-44 | BANDS | 持つ | 指標ごとの帯の区切り | ①② |
| a385a4c | analyze.py | 61-62 | _NON_IND | 持つ | 指標でない列の一覧 | ①② |
| a385a4c | analyze.py | 231-232,251 | N6・N8 | 持つ | 入った時の指標の列名 | ①② |
| aa6cd8e | check_indicator_sources.py | 37-41 | TABLES | 持つ（パス） | 資料の表3つの置き場 | ①② |
| aa6cd8e | check_indicator_sources.py | 97・:100 | span の目印 | 持つ | 設定ファイルの塊の目印 | ①② |
| a9b159e | composition_rules.json | — | `body.grids.material_param_ranges.<種類>[]` と `body.grids.*` の全部 | 持つ | search_limits.json の全体の写し（説明文 `_*` も込み） | ①② |
| a9b159e | composition_rules_src.backup_20260808.json | — | `roles[].使える系統[]` | 持つ | 役割ごとに使える系統 | ①② |
| a9b159e | composition_rules_src.backup_20260808.json | — | `question_map.対応.<系統>` | 持つ | 系統ごとの問い | ①② |
| a9b159e | condition_parts.json | — | `classic_crosses[].{name,a,b,note}` | 持つ | 定番のクロスの指標の組 | ①② |
| a385a4c | condition_parts_diag.py | 217-359 | _c_*・COMPOSE・_PRE_PARTS | 持つ／自前で計算 | 条件の形の名前と式 | ①② |
| a385a4c | condition_parts_diag.py | 363-507 | _cases | 持つ（テスト用） | 閾値・パラメータ | ①② |
| a385a4c | condition_parts_diag.py | 534-536 | run | 持つ | 材料の書き方と列名の形 | ①② |
| aac5aa5 | e35_range_oscillation.py | 67-68 | CI_N・CI_THRESH | 持つ | Choppiness の窓・閾値 | ①② |
| aac5aa5 | e35_range_oscillation.py | 70-72 | ER_N・ER_SMOOTH・ER_Q | 持つ | Efficiency Ratio の窓・平滑・分位 | ①② |
| aac5aa5 | e35_range_oscillation.py | 73-75 | ZONE_FRAC・W_Q_LO・W_Q_HI | 持つ | 箱のゾーン・幅の分位 | ①② |
| aac5aa5 | e35_range_oscillation.py | 228-230 | _HOLD_FEATS | 持つ | 特徴量の名前 | ①② |
| aac5aa5 | e35_range_oscillation.py | 639-640・:712-713・:785-786 | params | 持つ | LightGBM の設定 | ①② |
| aac5aa5 | e35_range_oscillation.py | 654・:720・:761-762・:834 | θ・k の格子 | 持つ | 判別の閾値の候補 | ①② |
| aac5aa5 | e36_short_oscillation.py | 57-70 | HOLD_5M・CI_N・CI_THRESH・ADX_MAX・ER_N・ER_SMOOTH・ER_Q・ZONE_FRAC・W_Q_*・TFS | 持つ（一部は読む） | e35 :67-80 と同じ値 | ①② |
| aac5aa5 | e36_short_oscillation.py | 97-102 | _entry_contract | 持つ | 入口の組み合わせ | ①② |
| aac5aa5 | e36_short_oscillation.py | 262-264 | _HOLD_FEATS | 持つ | 特徴量の名前 | ①② |
| aac5aa5 | e36_short_oscillation.py | 269-272 | USE_RV・_RV_SHORT_BARS・_RV_MID_BARS | 持つ | realized vol の窓 | ①② |
| aac5aa5 | e36_short_oscillation.py | 327-329・:337-349 | _ENTRY_FEATS・_entry_feat_vec | 持つ・作る | 入口の特徴量の名前と値 | ①② |
| aac5aa5 | e36_short_oscillation.py | 356・:359-367 | _SCENE_TIERS・_scene_unit | 持つ・作る | ATR%×stoch_k の場面の倍率 | ①② |
| aac5aa5 | e36_short_oscillation.py | 1111-1112 | HME_M・HME_TH_GRID | 持つ | donchian の閾値の候補 | ①② |
| aac5aa5 | e36_short_oscillation.py | 1212-1214 | --spike-lm-k・alpha・gate | 持つ | 急騰の窓・有意水準 | ①② |
| aac5aa5 | e36_short_oscillation.py | 1217・:1219 | --zone-wide・--zone-er-q | 持つ | ゾーン幅・er の分位 | ①② |
| aac5aa5 | e37.py | 37-45 | BASE_KW | 持つ | v26 の値 | ①② |
| aac5aa5 | e37.py | 47 | _SIGS | 持つ | 急騰の判定に使う指標の名前 | ①② |
| aac5aa5 | e37.py | 82-88 | space | 持つ | 閾値の範囲 | ①② |
| aac5aa5 | e37.py | 108-110 | V59_DOWN_WIN_MIN・FLAT_WIN_MIN・WAIT_MIN | 持つ | 決まった数字だけの一覧 | ①② |
| aac5aa5 | e37.py | 123-125 | S1 の鍵 | 持つ | th_down_di14・th_flat_kijun26 | ①② |
| aac5aa5 | e37.py | 135-142 | STOP_RULES | 持つ・読む | atr_band_edges | ①② |
| aac5aa5 | e37.py | 201 | REGIME | 持つ | 相場の列の名前 | ①② |
| aac5aa5 | e37_range_scalp.py | 107 | SIG_Z | 持つ | dev_z の閾値 | ①② |
| aac5aa5 | e37_range_scalp.py | 108 | K_SL | 持つ | ATR の倍率（SL） | ①② |
| aac5aa5 | e37_range_scalp.py | 109 | TP_OVERSHOOT | 持つ | σ（std20）の倍率（TP） | ①② |
| aac5aa5 | e37_range_scalp.py | 110 | T_MAX | 持つ | 保有本数 | ①② |
| aac5aa5 | e37_range_scalp.py | 114-118 | V10_LOOKBACK・V10_ZONE_TOL・V10_TOUCH_MIN・V10_SL_BUF・V10_MIN_RANGE_W | 持つ | ピボットのゾーン（窓・束ね幅・タッチ数） | ①② |
| aac5aa5 | e37_range_scalp.py | 121-124 | V11_ZONE_LOOKBACK・TOL・TOUCH・MIN_W | 持つ | 1h fractal のゾーン | ①② |
| aac5aa5 | e37_range_scalp.py | 153-154 | V15_BREAK_BARS・V15_BREAK_VOL_N | 持つ | レンジ破れの持続本数・出来高平均の窓 | ①② |
| aac5aa5 | e37_range_scalp.py | 159 | V16_GUARD | 持つ | BB 拡大ガード | ①② |
| aac5aa5 | e37_range_scalp.py | 178 | V17_ATR_BAND_EDGES | 持つ | ATR%（atr/close×100）の帯の境界 | ①② |
| aac5aa5 | e37_range_scalp.py | 195 | V21_RSI_LO | 持つ | RSI9 の下限の候補 | ①② |
| aac5aa5 | e37_range_scalp.py | 213 | V25_K | 持つ | 1h ATR% の倍率（帯の束ね幅） | ①② |
| aac5aa5 | e37_range_scalp.py | 221-224 | SHALLOW_Z・BB_K・BREAK_N・BREAK_LOOKBACK | 持つ | dev_z の浅い閾値・BB のσ・donchian の窓・本数 | ①② |
| aac5aa5 | e37_range_scalp.py | 225 | EVENT_TYPES | 持つ | イベント型の名前 | ①② |
| aac5aa5 | e37_range_scalp.py | 235-240 | PARQUETS・_BL_FAM | 持つ | parquet の指標列の名前で、除外する族 | ①② |
| aac5aa5 | e37_range_scalp.py | 721-731 | _exit_templates_v9 | 持つ | TP の σ 倍率・保有本数 | ①② |
| aac5aa5 | e37_range_scalp.py | 4347・:4367 | （診断） | 持つ | ADX≥40 | ①② |
| aac5aa5 | e38_logic_parts.py | 20-26 | import・SCALP_FLOOR・V11_SL_BUF・BE_TTL_BARS・UNIT_LOT | 読む・持つ | 手数料の床・SL のバッファ | ①② |
| aac5aa5 | e38_logic_parts.py | 33-34 | HTF_PARTS・VOL_PARTS | 持つ | 部品の名前（名前に期間と時間足が入っている） | ①② |
| aac5aa5 | e38_logic_parts.py | 308・:476 | gap | 持つ | 型を判定する gap | ①② |
| aac5aa5 | e38_logics.json | 7 | box_tf | 持つ | 時間足 | ①② |
| aac5aa5 | e38_logics.json | 10-20 | global.regime | 持つ | 相場の判定 | ①② |
| aac5aa5 | e38_logics.json | 47 | S1.entry.summary | 持つ（文） | stoch(9,3) のデッドクロス・v26 の gap 0.5% | ①② |
| aac5aa5 | e38_logics.json | 64-88 | S1.engine_flags | 持つ | v26_gap 0.5・v26_down_hours 1.0・v26_max_age_hours 6.0・v59_adx_cut | ①② |
| aac5aa5 | e38_logics.json | 89-100 | S1.const_overrides | 持つ | V59_DOWN_ADX7_TH 28.1029…・V59_FLAT_DID7_TH 0.28335…・V59_DOWN_SIG di14・V59_FLAT_SIG kijun26・ADV_PCT 0.1558…/0.1502…・WAIT 20・FLAT_WIN 240・DOWN_WIN 0 | ①② |
| aac5aa5 | e38_logics.json | 130-142 | L1 | 持つ | v57_long_flat_up_only・tmax_bars 48・gap_pct 0.5・sl_zone_k 1.0 | ①② |
| aac5aa5 | e38_logics.json | 155-166 | S2.entry.params | 持つ | confirm・confirm_htf・confirm_vol・ceil_filter flat_up・*_th（null） | ①② |
| aac5aa5 | e38_logics.json | 228 | S4.source | 持つ（文） | 「dev_z＝BB20 と同窓」 | ①② |
| aac5aa5 | e38_logics.json | 474-516 | common_exit | 持つ | tp1_frac 0.2〜0.8・sl_zone_k 0.5〜2.0・tmax_bars 1〜12・be_wait 0〜0・tp_pct_k 1.0〜3.0 | ①② |
| aac5aa5 | e38_logics.json | 519-608 | logics.S2 | 持つ | confirm の選択肢（stoch_dc/rsi9_down/bear_bar/none）・confirm_htf の選択肢5つ・th_*（quantile、series は e38_htf_*、q 0.2〜0.8、stochd14 だけ 0.95）・confirm_vol の選択肢4つ・th_*（e38_vol_*） | ①② |
| aac5aa5 | e38_logics.json | 610-622・:673-685 | S3・L3 | 持つ | over_min 0.0〜0.5・confirm_bars 0〜1 | ①② |
| aac5aa5 | e38_logics.json | 623-638 | S5・L5 | 持つ | grid_n lo/hi null | ①② |
| aac5aa5 | e38_logics.json | 639-653・:686-700 | S4・L4 | 持つ | z_th quantile dev_z_abs 0.7〜0.995・trigger imm/rev | ①② |
| aac5aa5 | e38_logics.json | 654-672 | L2 | 持つ | k_bars 6〜24・drop_th quantile ret12_abs_down 0.9〜0.995・vol_mult 1.0〜4.0 | ①② |
| aac5aa5 | e38_logics.json | 701-784 | logics.L1i | 持つ | S2 と同じ確認部品と th_* の宣言＋fresh_only | ①② |
| aac5aa5 | e38_logics.json | 794-799 | tuner.atr_band_edges | 持つ | [0.15,0.2,0.3,0.4] | ①② |
| a385a4c | engine_tuner.py | 90-91 | FINGERPRINT_FILES | 持つ | データの作り方に関わるファイル | ①② |
| a385a4c | engine_tuner.py | 99 | WARM | 持つ | 指標の計算の助走 | ①② |
| a2fcbbd | engine_tuner_exec.py | 162 | INDICATOR_SWITCH_PATH | 持つ | オン・オフの印のパス | ①② |
| a2fcbbd | engine_tuner_exec.py | 289〜297 | RUNTIME_ALIAS | 持つ | 列名の別名（カタログ名を prepare_df の列名へ写す） | ①② |
| a2fcbbd | engine_tuner_exec.py | 417〜449 | MATERIAL_PRE・SINCE_OPS・NO_ARG_OPS | 持つ | 前処理の部品（指標の種類ごとではなく、全部の指標に共通） | ①② |
| a2fcbbd | engine_tuner_exec.py | 563〜567 | PAIR_OPS | 持つ | 材料2本の組み方（指標に共通） | ①② |
| a2fcbbd | engine_tuner_exec.py | 647 | `_excl` の鍵の一覧 | 持つ | 材料の種別の鍵 | ①② |
| a2fcbbd | engine_tuner_exec.py | 795〜810 | _material_family | 持つ | 系統の判定に使う名前 | ①② |
| a2fcbbd | engine_tuner_exec.py | 1059〜1066 | _check_cond の時刻の範囲 | 持つ・読む | 時間帯「時刻」の閾値の範囲 | ①② |
| a2fcbbd | engine_tuner_exec.py | 1198〜1208 | LAWS_PATH・_LAW_SCENES・_LAW_TYPES・_LAW_FORMS・_LAW_PICK_KEYS・_LAW_SIDES | 持つ | 法則で指標を名指しするときの鍵 | ①② |
| a2fcbbd | engine_tuner_exec.py | 2386 | _static_level_px（zone opp） | 持つ | 余白の既定 | ①② |
| a2fcbbd | engine_tuner_exec.py | 2521 | _guards_ok | 持つ | 手数料の床の既定 | ①② |
| a2fcbbd | engine_tuner_exec.py | 3008〜3022 | engine_params_from_recipe | 持つ・読む | S2 の材料名 | ①② |
| a2fcbbd | engine_tuner_exec.py | 3044〜3049 | _sentinel_df | 持つ | 合成の指標列 | ①② |
| a2fcbbd | engine_tuner_exec.py | 3174〜3178 | _LEGACY_COL_SOURCE | 持つ | legacy の材料列の名前と作り方 | ①② |
| a2fcbbd | engine_tuner_exec.py | 3496〜3611 | run_identity_s1 の checks | 読む・持つ | v59・v47・v22・v24・v48 ほかの指標の閾値と名前 | ①② |
| a2fcbbd | engine_tuner_exec.py | 3822〜3854 | _base_ok_recipe | 持つ | 見本の材料と定数 | ①② |
| a2fcbbd | engine_tuner_exec.py | 4318〜4360・4447 | selftest の壊したレシピ | 持つ | 見本の材料 | ①② |
| a2fcbbd | engine_tuner_exec.py | 4478〜4481 | selftest の _geo9 | 持つ | 合成の幾何 | ①② |
| a2fcbbd | engine_tuner_exec.py | 4521〜4539 | selftest の df4・qt | 持つ | 合成の列と分位の表 | ①② |
| a2fcbbd | engine_tuner_exec.py | 4790・4842〜4866 | selftest の T-STREAK-TREE・G7 | 持つ | 見本の材料 | ①② |
| a2fcbbd | engine_tuner_exec.py | 4954〜4955・4971〜4979 | selftest の B0 | 持つ | 法則の差し替えの見本 | ①② |
| a2fcbbd | engine_tuner_exec.py | 5014〜5022・5066〜5067・5112〜5124 | selftest の 97番 | 持つ | 見本の材料と列名 | ①② |
| a385a4c | engine_tuner_fire_diag.py | 81-82 | cond_label の role | 持つ | 役割の名前と日本語の対応表 | ①② |
| a385a4c | engine_tuner_fire_diag.py | 493-503 | _synth_recipe | 持つ（テスト用） | 場面の判定の列名・SL の幅 | ①② |
| a385a4c | engine_tuner_fire_diag.py | 514,529-530 | selftest | 持つ（テスト用） | 条件の形と閾値 | ①② |
| a9b159e | exit_families.json | — | `branch_types.<id>.fire[].{indicator,lineage_any[],reverse_of_side,state,grid,const,side,forms[]}` | 持つ | 出口の枝で使う指標の系統 | ①② |
| a9b159e | exit_families.json | — | `v9.coverage.<V9の決済理由>[]` | 持つ | V9 の決済理由と枝の対応 | ①② |
| a9b159e | exit_families_rules.json | — | `branch_types.<id>.fire[].lineage_any[]`、`v9_coverage.<id>[]` | 持つ | 上と同じ | ①② |
| aa6cd8e | gen_acceptance.py | 150-156 | SWITCH・LAWS・FAMILIES・RANKING・LIMITS | 持つ（パス） | 指標の置き場 | ①② |
| aa6cd8e | gen_acceptance.py | 523-525 | KIND1_WORDS | 持つ | ファイル名だけ（工事の種類を決める語） | ①② |
| aa6cd8e | gen_acceptance.py | 527-533 | PARAMS・ROLES・THRESHOLD_KEY・OBS_CFG | 持つ（パス・鍵） | 資料の表2本・閾値の鍵・時間足の置き場 | ①② |
| aa6cd8e | gen_acceptance.py | 3054-3097 | 自己テストの見本 | 持つ | 見本の指標の行 | ①② |
| a385a4c | gen_audit_request.py | 123 | N_LAWS | 持つ | 法則の件数 | ①② |
| a385a4c | gen_audit_request.py | 125-138 | SOURCES | 持つ | 指標と場面の判定のコードの場所 | ①② |
| a385a4c | gen_audit_request.py | 157-174 | READING・REFERENCE | 持つ | 指標の情報の資料のファイル名 | ①② |
| ace0f74 | gen_composition_rules.py | 114-122 | `_extra_lineage` | 持つ | geo と time の系統 | ①② |
| ace0f74 | gen_indicator_switch.py | 473-490 | `_ON_KINDS`・`_OFF_KINDS` | 持つ | 材料の種類の区分 | ①② |
| a97a087 | gen_indicator_table.py | 44-48 | IREF・ROLES・R1MAP・START・END | 持つ | 読み書きする相手 | ①② |
| a97a087 | gen_indicator_table.py | 49-50 | CAT2LIN | 持つ | 役割の区分から札への対応 | ①② |
| a97a087 | gen_indicator_table.py | 51 | HOUKOU2PROP | 持つ | 方向の区分から性質への対応 | ①② |
| a97a087 | gen_indicator_table.py | 52 | POS_MAX | 持つ | `_r` の位置引数の数 | ①② |
| a97a087 | gen_indicator_table.py | 188 | LINEAGE_KINDS_FALLBACK | 持つ | 札の10区分 | ①② |
| a385a4c | gen_observe_manual.py | 66-106 | GLOSSARY | 持つ | 指標・時間足・パラメータ・閾値の説明の文 | ①② |
| a385a4c | gen_observe_manual.py | 129-140 | SCENE_TYPE_JP | 持つ | 場面の型の日本語名 | ①② |
| aa6cd8e | gen_regime_kb.py | 75-76 | _FOREIGN | 持つ | gen_materials.py が書く件数の囲み（部品・指標の件数） | ①② |
| aa6cd8e | gen_s22_combi.py | 56 | DROP_TFS | 持つ | 時間足（外す物） | ①② |
| ace0f74 | gen_signal_families.py | 90 | `_TF_MIN` | 持つ | 時間足の分数 | ①② |
| ace0f74 | gen_signal_families.py | 229-273 | role_lineage | 持つ | 役割ごとの系統と時間足 | ①② |
| ace0f74 | gen_signal_families.py | 275-297 | direction_conflict DC1-4 | 持つ | 向きの決まり | ①② |
| ace0f74 | gen_signal_families.py | 1268-1288 | `V9_FAMILY_MAP` | 持つ | V9 の名前から family への対応 | ①② |
| aa6cd8e | gen_stage0_match.py | 66 | ROLES | 持つ（直書き） | 役割の名前 | ①② |
| aa6cd8e | gen_stage0_match.py | 92 | "レンジ幾何" | 持つ | 系統の名前の直書き | ①② |
| aac5aa5 | gen_v9_exits.py | 57-64 | VARS | 持つ（名前の対応表） | 列名から日本語の名前へ | ①② |
| aac5aa5 | gen_v9_exits.py | 65 | IND_COLS | 持つ | 指標の列の名前7つ | ①② |
| a9b159e | identity_l1_legacy.json | — | `entry.connective.all[].material[].{family,legacy_col}` | 持つ | 指標の名指し | ①② |
| a9b159e | identity_s1_legacy.json | — | `exits[].fire.all[].material[].{family,legacy_col,imi}` | 持つ | 指標の名指し・列の名前・計算式の説明 | ①② |
| a9b159e | identity_s1_legacy.json | — | `exits[].fire.all[].value.legacy` | 持つ | 指標ごとの閾値 | ①② |
| a9b159e | identity_s2_legacy.json | — | `entry.connective.all[].material[].{family,param,tf,legacy_col,geo,imi}` | 持つ | 指標の名指し・パラメータ・時間足 | ①② |
| a9b159e | identity_s2_legacy.json | — | `entry.connective.all[].{role,form,side,value.legacy,value.direction}` | 持つ | 役割・形・閾値 | ①② |
| a9b159e | indicator_fix_plan.json | — | `指標[].パラメータ.*` | 持つ | indicator_params_by_strategy の写し | ①② |
| a9b159e | indicator_fix_plan.json | — | `指標[].パラメータの証拠.*` | 持つ | indicator_params_review の写し | ①② |
| a9b159e | indicator_fix_plan.json | — | `指標[].役割と閾値.*` | 持つ | indicator_roles_thresholds の写し | ①② |
| a9b159e | indicator_fix_plan.json | — | `指標[].役割と閾値の証拠.{役割[],閾値.{既定,スキャル,デイトレ}[]}.{URL,逐語,値,意味,出どころの順位,何を見るか}` | 持つ | 役割と閾値の教科書の逐語（out_w1〜4 から） | ①② |
| a9b159e | indicator_fix_plan.json | — | `指標[].役割と閾値の照らした結果[]` | 持つ | 照らした判定 | ①② |
| a9b159e | indicator_fix_plan.json | — | `指標[].作り.{教科書と違うか,何を変えたか,判定,理由}` | 持つ | 計算の作り | ①② |
| a9b159e | indicator_fix_plan.json | — | `指標[].何をするか.{パラメータ,作り.*,役割,閾値}` | 持つ | 直すこと | ①② |
| a9b159e | indicator_fix_plan.json | — | `指標[].対象.{保存してある on,今の源で作り直した on,承認済みの型の表に在る}` | 持つ | オン・オフ | ①② |
| a9b159e | indicator_fix_plan.json | — | `対象の照らし.{on_built,on_saved,table_fams,counts_built,fp_*}` | 持つ | オンの照らし | ①② |
| a9b159e | indicator_params_by_strategy.json | — | `指標[].{種類,系統,元の指標,軸の数,今の値,パラメータの名前,ライブラリの既定.{関数,値},候補（スキャル）,最初の値（スキャル）,最初の値の出どころ（スキャル）,候補（デイトレ）,最初の値（デイトレ）,最初の値の出どころ（デイトレ）,範囲[].{下限,上限,出どころ},印,文のため使っていない値,結果}` | 持つ | パラメータの今の値・最初の値・範囲・ライブラリの既定 | ①② |
| a9b159e | indicator_params_review.json | — | `[].{種類,元の指標,系統,パラメータの名前[],今のパラメータの組[],メモ}` | 持つ | パラメータの名前と今の値 | ①② |
| a9b159e | indicator_params_review.json | — | `[].{既定,スキャル,デイトレ,範囲}[].{値,URL,逐語,出どころの質,照らした印,原文の足}` | 持つ | 教科書の値と範囲の逐語と URL | ①② |
| a97a087 | indicator_reference_diag.py | 51 | `_IDX0` | 持つ | known の合成バーの開始日 | ①② |
| a97a087 | indicator_reference_diag.py | 919-933 | EXT2 | 持つ | ext2 | ①② |
| a97a087 | indicator_reference_diag.py | 942 | REFS | 持つ（`_r` が足す） | 定義表の全部 | ①② |
| a97a087 | indicator_reference_diag.py | 946-953 | MAKO_K3・K7・K3B・B1S1・K3C | 持つ | mako の欄 | ①② |
| a97a087 | indicator_reference_diag.py | 956-1260 | INDICATOR_TABLE | 持つ | 役割・札・方向・性質・値域・注記 | ①② |
| a97a087 | indicator_reference_diag.py | 1720-1726 | `_SR_TOUCH_ATR_REMOVED` | 持つ | 外した S-RタッチATR の控え | ①② |
| a97a087 | indicator_reference_diag.py | 4525-4530 | `_ABER_L`・`_ABER_A`・`_ACCB_L`・`_ACCB_C`・`_CE_L`・`_CE_M`・`_HW_*`・`_MASSI_F`・`_MASSI_S`・`_THERMO_L` | 持つ | 6種の指標のパラメータ | ①② |
| a97a087 | indicator_reference_diag.py | 4800-4804 | `_CYC_SYN_NOTE`・`_HT_START_A`=12・`_HT_START_B`=37・`_EBSW_L`=40・`_EBSW_B`=10・`_MSW_P`=5 | 持つ | サイクル系のパラメータ | ①② |
| a97a087 | indicator_reference_diag.py | 5060-5061 | `_CDLZ_N`=30・`_DOJI_N`=10 | 持つ | cdl_z・cdl_doji のパラメータ | ①② |
| a97a087 | indicator_reference_diag.py | 5202-5217 | MAKO_R1・R1_KEEP_ON・その後のループ | 持つ・作る | REFS の mako の欄 | ①② |
| a97a087 | indicator_reference_diag.py | 5226-5251 | DEMAND_REF | 持つ | 需給 | ①② |
| a97a087 | indicator_reference_diag.py | 5259-5337 | AXIS_EC | 持つ | 軸カタログ E-c との対応 | ①② |
| a97a087 | indicator_reference_diag.py | 5346-5348 | RANGE_GEO_TF | 持つ | レンジ幾何の時間足 | ①② |
| a97a087 | indicator_reference_diag.py | 5349-5367 | RANGE_GEO_REF | 持つ | レンジ幾何の列 | ①② |
| a97a087 | indicator_reference_diag.py | 5437-5464 | TA_CLASS_MAP | 持つ | ta のクラスとの対応 | ①② |
| a97a087 | indicator_reference_diag.py | 5484 | LINEAGE_KINDS | 持つ | 札の区分 | ①② |
| a97a087 | indicator_reference_diag.py | 5488-5512 | LINEAGE_QUESTION | 持つ | 系統ごとに、相場の何を見ているか | ①② |
| a97a087 | indicator_reference_diag.py | 5528-5837 | INDUSTRY_MAP | 持つ | ライブラリの関数との対応 | ①② |
| a97a087 | indicator_reference_diag.py | 5846-5883 | SKIP_APPROVED_20260809・SKIP_POLICY_DUP_20260809・SKIP_APPROVED_20260810・SKIP_APPROVED | 持つ | 入れないライブラリの関数 | ①② |
| a97a087 | indicator_reference_diag.py | 5885-5969 | INDUSTRY_SKIP | 持つ | 入れない理由 | ①② |
| a97a087 | indicator_reference_diag.py | 6003-6020 | CONST_REGISTRY | 持つ | 指標ごとの固定の水準 | ①② |
| a97a087 | indicator_reference_diag.py | 6037-6041 | TIME_REF | 持つ | 時間帯 | ①② |
| a97a087 | indicator_reference_diag.py | 6052-6053 | STATE_COLS | 持つ | ポジションの状態の列 | ①② |
| a9b159e | indicator_roles_thresholds.json | — | `[].{種類,今の系統,今の答える問いの区分,今の向き,出どころの役割,役割の印,閾値}` | 持つ | 系統（7種）・問いの区分（7種）・向き（文）・役割の出どころ・閾値（文） | ①② |
| a9b159e | indicator_switch.json | — | `on[]`・`off[]` | 持つ | オン・オフ | ①② |
| a9b159e | indicator_switch.json | — | `geo_on[]`・`demand_on[]`・`time_on[]` | 持つ | オンの別枠 | ①② |
| a9b159e | indicator_switch.json | — | `sources.{ta,law,identity,mako}[]` | 持つ | オンにした根拠ごとの種類 | ①② |
| a9b159e | indicator_switch.json | — | `ta_unresolved[]` | 持つ | ta のクラスで対応が決まらない物 | ①② |
| a385a4c | leak_causality_diag.py | 22-25 | docstring | 持つ | 列の数 | ①② |
| a385a4c | leak_causality_diag.py | 244-263 | WATCHED | 持つ | 指標の情報を持つファイルの一覧（ハッシュ値を作る相手） | ①② |
| a9b159e | m2_stage_candidates.json | — | `段[].語[].{探す,当て方,pre,pre_win.{op,months},geo_cols[],§2.2}` | 持つ | 段ごとの指標を探す語・前処理 | ①② |
| a9b159e | m2_stage_candidates.json | — | `段[].{key,stage,role,law,law_or,law_tf,law_width,lineages[],bool_col}` | 持つ | 段の役割・法則・系統 | ①② |
| a9b159e | material_ranking.json | — | `順位.<役割>.<向き/大きさ/強さ>.<12/120>[]`（[列__時間足, 点]） | 持つ | 列ごとの成績の順位 | ①② |
| a9b159e | material_ranking.json | — | `省いた列.<列>` | 持つ | 測れなかった列と理由 | ①② |
| a9b159e | material_ranking.json | — | `どの役割にも入らなかった列[]` | 持つ | 列 | ①② |
| a9b159e | material_ranking.json | — | `需給の被覆.<種類>` | 持つ | 需給のデータの期間 | ①② |
| a9b159e | materials.json | — | `body.rows[].{名前,系統,答える問い,使える役割,計算の出どころ,グループ,状態,engine_tuner}` | 持つ | 系統・問い・役割・ライブラリとの対応・選べるか | ①② |
| a9b159e | materials.json | — | `body.skip_rows[].{名前,理由,承認}` | 持つ | 入れないライブラリの関数と理由 | ①② |
| a9b159e | materials.json | — | `body.engine.期間.<種類>[]` | 持つ | パラメータの値（カタログ） | ①② |
| a9b159e | materials.json | — | `body.engine.レンジ幾何[]`・`body.engine.時間帯[]` | 持つ | 名前 | ①② |
| a9b159e | materials.json | — | `body.lineage_question.<系統>.{問い,出典}` | 持つ | 系統ごとの問いと教科書の逐語 | ①② |
| a9b159e | materials.json | — | `body.gaps[].{印,何を足すか,数,中身,…}` | 持つ | 足りない指標の一覧（文） | ①② |
| a9b159e | observe_config.json | — | `material_params.<種類>` | 持つ | パラメータの値の一覧。名前に出る軸の組で、最初の値（スキャル∪デイトレ）と残す名前を合わせた物 | ①② |
| a9b159e | observe_config.json | — | `material_first_hidden.<種類>.{スキャル,デイトレ}` | 持つ | 名前に出ない軸の最初の値 | ①② |
| a9b159e | observe_config.json | — | `_material_params_pending[]` | 持つ | 範囲が1点のまま、または値が決まらない種類（文字列） | ①② |
| a9b159e | observe_config.json | — | `material_keep.V9[]`・`material_keep.採用中の戦略と確認のレシピ[]` | 持つ | 残す名前。パラメータ込みの列の名前 | ①② |
| a9b159e | observe_config.json | — | `rsi_periods`・`stoch_periods`・`atr_periods`・`bb_periods`・`bb_sigma`・`donchian_periods`・`ema_periods`・`sma_periods`・`roc_periods`・`macd_params`・`mfi_periods`・`cmf_periods`・`obv_slope_periods`・`rci_periods`・`zscore_periods`・`realized_vol_periods`・`volume_ratio_periods`・`swing_windows`・`fractal_k`・`vwap_windows`・`keltner`・`supertrend`・`vp_windows`・`sr_windows`・`sr_tol`・`sr_atr1h_k`・`band_touch`・`band_fee_mult`・`lee_mykland_k`・`mmi_periods`・`w_tol`・`fib_windows`・`pivot_windows`・`ichimoku`・`mmar_periods`・`rainbow`・`cdl_z_periods`・`body_ratio_periods`・`volume_change_periods`・`lrsi_gamma` | 持つ | 指標ごと、または指標の系列ごとの期間・倍率・窓 | ①② |
| a9b159e | observe_config.json | — | `drop_columns[]`（[省く列, 残す列]） | 持つ | 同じ挙動の列の対応 | ①② |
| a9b159e | observe_config.json | — | `scenes.<id>.{type,z_th,k_bars,drop_pct,vol_mult…}` | 持つ（半分は設定） | 場面の定義。z_th は zscore の閾値 | ①② |
| aecb27a | observe_diag.py | 178-180 | `TF_RULE` | 持つ | 時間足 | ①② |
| aecb27a | observe_diag.py | 186 | `SUB_5M_TF` | 持つ | 時間足（1分足から作る足） | ①② |
| aecb27a | observe_diag.py | 187 | `ONE_MIN_CSV` | 持つ | 前処理（1m・3m の元データ） | ①② |
| aecb27a | observe_diag.py | 200 | `BARS_CSV` | 持つ | 前処理（元の5分足） | ①② |
| aecb27a | observe_diag.py | 250-259 | `_DEMAND_FILES` | 持つ | 需給の指標3種（名前・ファイル・列） | ①② |
| aecb27a | observe_diag.py | 471 | `_SR_ATR_TOL_LO, _SR_ATR_TOL_HI` | 持つ | 閾値（許容幅の下限と上限） | ①② |
| aecb27a | observe_diag.py | 490 | `_H1_BASE` | 持つ | 前処理（1時間足の元になる5分足） | ①② |
| aecb27a | observe_diag.py | 781-790 | `_BAND_IMPL` | 持つ | 計算の式（帯8種・床を引数で受ける版） | ①② |
| aecb27a | observe_diag.py | 873-890 | `_CYC_MEMO`・`_cyc` | 持つ | 前処理（サイクル系の計算を使い回す） | ①② |
| aecb27a | observe_diag.py | 903 | `MATERIAL_FAMILIES` | 持つ | 種類の名前・列の名前の型・方向・計算の式 | ①② |
| aecb27a | observe_diag.py | 1069-1100 | `_reg`（トレンド・モメンタム） | 持つ | 種類・名前の型・方向・式 | ①② |
| aecb27a | observe_diag.py | 1102-1121 | `_reg`（ボラ） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1123-1124 | `_reg`（出来高） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1127-1146 | `_reg`（ローソク） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1148-1159 | `_reg`（形） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1163-1177 | `_reg`（山と谷） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1179-1208 | `_reg`（位置）＋ `_vwap_day`（1189-1193） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1210-1216 | `_reg`（移動窓の pivot） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1244-1250 | `_reg`（前期間・前週の pivot） | 持つ | 種類・式 | ①② |
| aecb27a | observe_diag.py | 1251-1274 | `_reg`（fib・出来高プロファイル・S-R） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1278-1291 | `_reg`（MMI・S-R 系・SMC_SWEEP確定） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1295-1309 | `_reg`（帯8種） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1313-1314 | `_reg`（LeeMykland・LeeMykland_E36版） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1321-1360 | `_reg`（業界の1回目） | 持つ | 種類・式・ライブラリとの対応 | ①② |
| aecb27a | observe_diag.py | 1364-1395 | `_reg`（業界の2回目） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1400-1421 | `_atr_wilder`・`_sqz_carter`・`_reg("SQZ_ON_Carter")` | 作る・持つ | 計算の式・パラメータ | ①② |
| aecb27a | observe_diag.py | 1424-1429 | `_reg`（SQZPRO_ON_WIDE・NARROW） | 持つ | 種類・式 | ①② |
| aecb27a | observe_diag.py | 1430-1456 | `_stc_textbook`・`_reg("STC")`・`_reg("STCstoch")` | 作る・持つ | 計算の式・パラメータ | ①② |
| aecb27a | observe_diag.py | 1460-1501 | `_reg`（業界の3回目）＋ `_trix_ema` | 持つ | 種類・式 | ①② |
| aecb27a | observe_diag.py | 1507-1538 | `_MA_FUNCS` | 持つ | 計算の式（移動平均24種） | ①② |
| aecb27a | observe_diag.py | 1546-1586 | `_ssf_avg`・`_trima_ta`・`_vidya_cmo`・`_reg` | 作る・持つ | 計算の式 | ①② |
| aecb27a | observe_diag.py | 1590-1610 | `_reg`（LRangle・HILO・MAMA ほか）＋ `_mama_hl` | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1618-1634 | `_reg`（MMAR・RAINBOW） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1639-1679 | `_reg`（trend） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1683-1710 | `_reg`（volume） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1712-1719 | `_reg`（statistics） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1722-1753 | `_reg`（volatility）＋ `_thermo_orig` | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1755-1770 | `_reg`（cycles） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 1773-1787 | `_reg`（candles） | 持つ | 同上 | ①② |
| aecb27a | observe_diag.py | 3388-3400 | `_category` | 持つ | 区分（部品のカテゴリ5つ） | ①② |
| aecb27a | observe_diag.py | 3469・3990 | down 型の判定 | 持つ | 閾値 | ①② |
| af05308 | observe_diag.py | 4983-4984 | `_DIST_PAT`・`_SLOPE_PAT` | 持つ | 名前の規則 | ①② |
| af05308 | observe_diag.py | 5063-5096 | `_V9_PERIOD_PATTERNS`・`_V9_PERIOD_PARAMS` | 持つ | V9 の名前 → 設定の鍵 → V9 のファイル・正規表現 | ①② |
| af05308 | observe_diag.py | 5355-5365 | `_V9_LABEL_TO_FAMILIES` | 持つ | V9 の名前 → family | ①② |
| af05308 | observe_diag.py | 5406-5413 | `_USE_PATTERNS` | 持つ | family → 探す語 | ①② |
| af05308 | observe_diag.py | 5759-5761 | `_V9_MATCH_*`・`_V9_INPUT_COLS` | 持つ | V9 の列のうち対象外にする物 | ①② |
| af05308 | observe_diag.py | 5856-5882 | `_v9_part_variants` | 持つ | 部品の式（slope・slope_avg） | ①② |
| af05308 | observe_diag.py | 6068 | `_HOUKOU2PROP` | 持つ | 方向 → 性質の区分の決まり | ①② |
| af05308 | observe_diag.py | 6069-6070 | `_V9_SOURCES`・`_V9_RECORD_SINCE` | 持つ | v9_logic.md の出どころ3本 | ①② |
| af05308 | observe_diag.py | 6478-6513 | `check_materials_meta` | 持つ | 壊すために選ぶ種類 | ①② |
| af05308 | observe_diag.py | 6961-7114 | `DEMAND_RANK_TF`・`rank_demand_for_regime`・`merge_demand_into_ranking`・`add_demand_to_ranking` | 持つ／読む／書く | 需給の時間足・系統「需給」 | ①② |
| af05308 | observe_diag.py | 7117-7201 | `selftest_rank_demand` | 持つ | 需給の名前と元の列 | ①② |
| af05308 | observe_diag.py | 7277-7441 | `selftest_insp5` | 持つ | 種類の名前 | ①② |
| af05308 | observe_diag.py | 7484-7555 | `selftest_band` | 持つ／読む | 帯の部品と S1 の 10 種 | ①② |
| af05308 | observe_diag.py | 7558-7677 | `selftest_atr1h` | 持つ／読む | S-Rタッチ1時間ATR | ①② |
| af05308 | observe_diag.py | 7680-7751 | `_insp_hidden_params` | 持つ／読む | 名前に出さない引数 | ①② |
| af05308 | observe_diag.py | 7812-7943 | `selftest_catalog` | 持つ／読む | 名前の型・期間・範囲・残す名前 | ①② |
| af05308 | observe_diag.py | 7946-8940 | `selftest` | 持つ／読む | 種類と期間の既知答え | ①② |
| af05308 | observe_diag.py | 8942-8981 | `build_parser` | 持つ | 需給の名前（説明の文） | ①② |
| aa6cd8e | pre_audit_check.py | 58-62 | INDICATOR_SOURCES_CHECK・KNOWN_MATERIALS_PATH・MATERIALS_CSV・MATERIALS_CHECK | 持つ（パス） | 指標の照らしの道具・分かっている ❌ の一覧・材料の検査 | ①② |
| aa6cd8e | pre_audit_check.py | 161-171 | KNOWN_NG | 持つ | 指標の資料と設定ファイルの、分かっている食い違い | ①② |
| aa6cd8e | pre_audit_check.py | 177・:180-189 | KNOWN_MATERIALS | 持つ／読む | 分かっている ❌ の一覧の sha256 | ①② |
| a385a4c | precheck.py | 41-45 | BANDS | 持つ | 指標ごとの帯の区切り | ①② |
| a385a4c | precheck.py | 46 | V17_LOWVOL_BANDS | 持つ | ATR% の低ボラ帯の数 | ①② |
| a9b159e | r9_demand_fixture.json | — | `meta.regime.build.entry.tree.all[].{on.all[],off.any[],on.all[].not,on.all[].inner}.material[].{family,param,tf,pre.op,geo}`・`value.threshold_q`・`value.n` | 持つ | 判定の束の中の指標・パラメータ・時間足・前処理 | ①② |
| a9b159e | r9_demand_fixture.json | — | `entry.connective.all[].material[].demand` | 持つ | 需給の材料 | ①② |
| a385a4c | ratchet_guards.py | 114-121 | report_vol_importance | 持つ | 指標の系統（ボラ系）の分け方 | ①② |
| a385a4c | ratchet_guards.py | 175 | _selftest | 持つ（テスト用） | 指標の列名 | ①② |
| a385a4c | regime_label.py | 47-53 | LABEL_NAMES・BAND_KEYS・TAG_KEYS・BASE_TF | 持つ | 正解ラベルの見方の名前・設定の鍵・時間足 | ①② |
| a385a4c | regime_label.py | 518-600 | selftest の値 | 持つ（テスト用） | 帯のパラメータ | ①② |
| a9b159e | regime_laws.json | — | `法則[].機械が読む判定.数える部品.family[]` | 持つ | 法則での指標の名指し | ①② |
| a9b159e | regime_laws.json | — | `法則[].機械が読む判定.数える部品.側.<種類>` | 持つ | 指標ごとの向き（above・below） | ①② |
| a9b159e | regime_laws.json | — | `法則[].機械が読む判定.数える部品.{geo,系統[],時間足,向きを持つ,性質,かつ}`・`除く系統`・`除く部品.法則`・`型`・`形`・`本数`・`上限`・`掛かる場面` | 持つ | 系統・性質での名指し | ①② |
| a9b159e | regime_laws.json | — | `法則[].根拠[].{指標,材料,逐語,出どころ,読み,理由,外したもの}` | 持つ | 教科書の逐語と URL | ①② |
| a9b159e | regime_laws.json | — | `出どころ_2026-08-20に新しく開いたもの[].{名前,url,級}` | 持つ | 出どころ | ①② |
| a385a4c | regime_r9_diag.py | 275-277 | measure | 持つ | 比べる相手の判定の列名 | ①② |
| a385a4c | regime_r9_diag.py | 888-892,901-902 | selftest ⑪ | 持つ（テスト用） | レンジ幾何の列名・帯の条件 | ①② |
| a385a4c | regime_r9_diag.py | 917-920 | selftest ⑭ | 持つ（テスト用） | 材料と分位 | ①② |
| a385a4c | report.py | 30-35 | EXIT_JP | 持つ | 指標の名前が入った決済の理由 | ①② |
| a385a4c | report.py | 292,295-297 | _ind・_cjp | 持つ | 指標の列名と表示名の対応 | ①② |
| a385a4c | report.py | 367-372 | bands | 持つ | 指標ごとの帯の区切り | ①② |
| a9b159e | search_limits.json | — | `material_param_ranges.<種類>[].{kind,lo,hi,dec}` | 持つ | パラメータの範囲（名前の軸ごと） | ①② |
| a9b159e | signal_families.json | — | `parts[]` | 持つ | 部品（パラメータ込みの列の名前）の一覧 | ①② |
| a9b159e | signal_families.json | — | `kubun.<部品名>` | 持つ | 性質（向き） | ①② |
| a9b159e | signal_families.json | — | `inventory.lineage_of.<部品名>` | 持つ | 系統 | ①② |
| a9b159e | signal_families.json | — | `inventory.limits_copy.grids.material_param_ranges.<種類>[].{kind,lo,hi,dec}` | 持つ | パラメータの範囲（search_limits の写し） | ①② |
| a9b159e | signal_families.json | — | `bans.direction_note.parts[]` | 持つ | 向きの禁止の部品 | ①② |
| a9b159e | signal_families.json | — | `bans.direction_stateful.parts[]` | 持つ | 向きの禁止の部品 | ①② |
| a9b159e | signal_families.json | — | `bans.insufficient_samples.pairs[].{part,tf,n_eff}` | 持つ | 標本不足の部品×時間足 | ①② |
| a9b159e | signal_families.json | — | `extra_parts.{demand,geo,time}.parts[]` | 持つ | 需給・レンジ幾何・時間帯の部品 | ①② |
| a9b159e | signal_families.json | — | `role_lineage.roles.<役割>.{lineages[],tfs,geo}` | 持つ | 役割ごとの系統と時間足 | ①② |
| a385a4c | tuner_judgement.py | 788-833,1104-1138 | _nb_stable・_nb_fragile・_atr_case・_sentinels | 持つ（テスト用） | パラメータの名前と値 | ①② |
| aa6cd8e | check_indicator_sources.py | 36 | SWJ | 読む | オン・オフ | ③ |
| aa6cd8e | check_indicator_sources.py | 46-49 | kinds_of | 読む | 種類の名前（1種1行） | ③ |
| aa6cd8e | check_indicator_sources.py | 52-67 | check1 | 読む | オンの一覧と、表3つの種類の照合 | ③ |
| aa6cd8e | check_indicator_sources.py | 90-103 | check2 | 読む／作る | パラメータの値と範囲（設定ファイルに写した塊） | ③ |
| a385a4c | condition_parts_diag.py | 510-527 | _load_df | 読む | 指標の作り方・時間足 | ③ |
| aac5aa5 | e35_range_oscillation.py | 47-57 | import | 読む | 指標の土台 | ③ |
| aac5aa5 | e35_range_oscillation.py | 60・:109-114 | DESIGN_MD・_entry_contract | 読む | 入口の組み合わせ（must_combine） | ③ |
| aac5aa5 | e35_range_oscillation.py | 69 | ADX_MAX | 読む | ADX の上限 | ③ |
| aac5aa5 | e35_range_oscillation.py | 76 | TFS | 読む | 箱の時間足 | ③ |
| aac5aa5 | e35_range_oscillation.py | 80 | HOLD_5M | 読む | 保有本数 | ③ |
| aac5aa5 | e35_range_oscillation.py | 233-247 | _hold_arrays | 読む | atr・adx・stoch_k/d・er・chop・bb_mid_slope_pct・bb_width・box_sup_dist__1h/4h | ③ |
| aac5aa5 | e36_short_oscillation.py | 40-47 | import | 読む | 同上 | ③ |
| aac5aa5 | e36_short_oscillation.py | 374 | import | 読む | Lee-Mykland の急騰の統計 | ③ |
| aac5aa5 | e36_short_oscillation.py | 479-484 | Lj・Lstar | 読む | spike_stat・spike_threshold を呼ぶ | ③ |
| aac5aa5 | e37.py | 26-27 | RECIPES | 読む | S1・L1 のレシピ | ③ |
| aac5aa5 | e37.py | 128-129 | L1 | 読む | sl_zone_k | ③ |
| aac5aa5 | e37.py | 209-224 | assert_regime_agrees | 読む | 上と json の照合 | ③ |
| aac5aa5 | e37.py | 236-254 | _prepared | 読む | v25_adaptive_band・h1_edge・V25_K | ③ |
| aac5aa5 | e37_range_scalp.py | 88-96 | import | 読む | 原価・指標の土台 | ③ |
| aac5aa5 | e37_range_scalp.py | 92 | structure_features | 読む | fractal ピボット | ③ |
| aac5aa5 | e37_range_scalp.py | 381-411 | _load_features | 読む | parquet の 2603 列 | ③ |
| aac5aa5 | e37_range_scalp.py | 982-984・:1255-1257 | run_continuous_v9・run_continuous | 読む | atr・adx・stoch_k・sma・std・箱の列 | ③ |
| aac5aa5 | e37_range_scalp.py | 1573-1581 | _import_rg5 | 読む | RG-v5 の判定 | ③ |
| aac5aa5 | e37_range_scalp.py | 1588 | import | 読む | _apply_rg5_to_5m・_rg5_frames | ③ |
| aac5aa5 | e37_range_scalp.py | 1846 | rsi9_21 | 読む | rsi9 | ③ |
| aac5aa5 | e37_range_scalp.py | 2339-2368 | _fit_v15_branch_policy | 読む | stoch_k_at_entry・atr_14/entry_price・box_W | ③ |
| aac5aa5 | e37_range_scalp.py | 3513-3544 | _rg5_gate_desc | 読む | RG の定数（rg.v17.ZONE_*・rg.TREND_*） | ③ |
| aac5aa5 | e38.py | 25 | CONFIG | 読む | 設定 | ③ |
| aac5aa5 | e38.py | 97-131 | space | 読む | 探す範囲 | ③ |
| aac5aa5 | e38.py | 134-147 | hold_space | 読む | 保有の範囲 | ③ |
| aac5aa5 | e38.py | 150-160 | stop_rules | 読む | atr_band_edges | ③ |
| aac5aa5 | e38.py | 277-293 | regime | 読む | 相場の列 | ③ |
| aac5aa5 | e38.py | 296-309 | load_windows | 読む | e37._load・e37.V25_K・v25_adaptive_band・h1_edge・parts.prepare_df | ③ |
| aac5aa5 | e38_logic_parts.py | 58 | prepare_df | 読む | RSI9 | ③ |
| aac5aa5 | e38_logic_parts.py | 60 | prepare_df | 読む | RG の帯 | ③ |
| aac5aa5 | e38_logic_parts.py | 95-114 | _pullback_short | 読む | stoch k/d のデッドクロス・rsi9 の下向き・陰線 | ③ |
| aac5aa5 | e38_logic_parts.py | 117-134 | _confirm_2axis | 読む | htf_*・vol_* と th_* | ③ |
| aac5aa5 | e38_logic_parts.py | 149-154・:181-186 | _zscore_short/long | 読む | dev_z と z_th | ③ |
| aac5aa5 | e38_logic_parts.py | 157-166 | _crash_rebound_long | 読む | 出来高の平均・drop_th・vol_mult | ③ |
| aac5aa5 | e38_logic_parts.py | 216-234 | config_regime | 読む | 相場の列の名前 | ③ |
| aac5aa5 | e38_logic_parts.py | 255-268 | ctx | 読む | atr・adx・stoch_k・e38_stoch_d・rsi9・dev_z・volume・v11_* | ③ |
| aac5aa5 | e38_logic_parts.py | 269-280 | 番人 | 読む | 部品の名前と th_ の存在 | ③ |
| aac5aa5 | e38_logic_parts.py | 460-463 | grid | 読む | atr・adx・stoch_k・v11_* | ③ |
| a385a4c | engine_tuner.py | 157-187 | catalog_size・catalog_columns | 読む／作る | 指標の種類の数・時間足・列名の形 | ③ |
| a385a4c | engine_tuner.py | 199-216 | _print_regime | 読む | 場面の名前・判定の列名 | ③ |
| a385a4c | engine_tuner.py | 235-265 | _print_coverage | 読む | 探索が動かせる列・ロジックが読む列 | ③ |
| a385a4c | engine_tuner.py | 428-449,583-585 | _resolve_space・main | 読む | 探す範囲（int・float・cat・quantile） | ③ |
| a385a4c | engine_tuner.py | 595,614,750-751 | main | 読む | 固定値・ATR% の帯の区切り | ③ |
| a2fcbbd | engine_tuner_exec.py | 37〜41 | import 文（e37・parts・iref・_score・strat_base） | 読む | 指標の参照表・系統・定数の表、prepare_df の材料 | ③ |
| a2fcbbd | engine_tuner_exec.py | 166〜185 | load_indicator_switch | 読む | 指標のオン・オフ（本体・レンジ幾何・需給・時間帯） | ③ |
| a2fcbbd | engine_tuner_exec.py | 188〜197 | indicator_enabled | 読む | 本体の指標のオン・オフ | ③ |
| a2fcbbd | engine_tuner_exec.py | 200〜227 | geo_enabled・demand_enabled・time_enabled | 読む | レンジ幾何・需給・時間帯のオン・オフ | ③ |
| a2fcbbd | engine_tuner_exec.py | 230〜232 | indicator_switch_fingerprint | 読む | 印のハッシュ値 | ③ |
| a2fcbbd | engine_tuner_exec.py | 606〜708 | _material_name | 読む | 種別の決め方と、名前の検査 | ③ |
| a2fcbbd | engine_tuner_exec.py | 714〜730 | _check_int_range | 読む | 本数の範囲（指標に共通） | ③ |
| a2fcbbd | engine_tuner_exec.py | 733〜744 | _check_param_range | 読む | 指標ごとのパラメータの範囲 | ③ |
| a2fcbbd | engine_tuner_exec.py | 750〜792 | _check_num_range・_check_q_range | 読む | 数字・分位の範囲（指標に共通） | ③ |
| a2fcbbd | engine_tuner_exec.py | 830〜851 | _check_value（ref・const） | 読む | 閾値の材料と、名前つき定数 | ③ |
| a2fcbbd | engine_tuner_exec.py | 1100〜1102 | _check_cond | 読む | レンジ幾何のうち、価格水準の列を拒否する | ③ |
| a2fcbbd | engine_tuner_exec.py | 1182〜1195 | _dirless_parts | 読む | 向きを持たない部品（指標の性質） | ③ |
| a2fcbbd | engine_tuner_exec.py | 1228〜1286 | _validate_law | 読む | 法則が名指しする系統名と性質 | ③ |
| a2fcbbd | engine_tuner_exec.py | 1289〜1339 | load_regime_laws | 読む | 法則の「機械が読む判定」（family・geo・側・系統・性質・本数） | ③ |
| a2fcbbd | engine_tuner_exec.py | 1342〜1347 | _upper_tfs | 読む | 時間足の並び | ③ |
| a2fcbbd | engine_tuner_exec.py | 1350〜1417 | _law_count_and・_law_count | 読む | 法則が数える部品（系統・時間足・向き・family・側・性質） | ③ |
| a2fcbbd | engine_tuner_exec.py | 1420〜1483 | _scene_scan | 読む | 束の中の部品（family・tf・geo・系統・名前） | ③ |
| a2fcbbd | engine_tuner_exec.py | 1486〜1542 | _check_scene_rules | 読む | 法則による審査（G7） | ③ |
| a2fcbbd | engine_tuner_exec.py | 1552 | REGIME_NAMES | 読む | 場面の名前 | ③ |
| a2fcbbd | engine_tuner_exec.py | 1779〜1810 | validate_recipe の G3 | 読む | 指標の系統（k）と、系統ごとの本数 | ③ |
| a2fcbbd | engine_tuner_exec.py | 1812〜1828 | validate_recipe の G2 | 読む | 列ごとの補正後独立標本数 | ③ |
| a2fcbbd | engine_tuner_exec.py | 1978〜1987 | _vnum | 読む | 名前つき定数の値 | ③ |
| a2fcbbd | engine_tuner_exec.py | 1990〜2017 | _vnum_q | 読む | 分位の閾値（列ごと） | ③ |
| a2fcbbd | engine_tuner_exec.py | 2032〜2068 | material_array | 読む・作る | 指標の計算（その場で計算する） | ③ |
| a2fcbbd | engine_tuner_exec.py | 2071〜2102 | _col_array | 読む | 列の値の取り出し | ③ |
| a2fcbbd | engine_tuner_exec.py | 2247〜2250 | touch の許容幅 | 読む | 定数 | ③ |
| a2fcbbd | engine_tuner_exec.py | 2483〜2485・2503 | _ceiling_fire | 読む | 材料列（v35_range_top・rg5_uptrend） | ③ |
| a2fcbbd | engine_tuner_exec.py | 2676〜2683 | run_recipe | 読む | prepare_df の指標の列 | ③ |
| a2fcbbd | engine_tuner_exec.py | 2756〜2757 | run_recipe | 読む | 記録用の指標（atr_entry・adx_entry・k_entry） | ③ |
| a2fcbbd | engine_tuner_exec.py | 3707 | box_tf | 読む | 時間足 | ③ |
| a2fcbbd | engine_tuner_exec.py | 3964〜3974 | _with_parts_cols | 読む | prepare_df の部品名 | ③ |
| a2fcbbd | engine_tuner_exec.py | 4003〜4052 | _selftest_roundtrip | 読む | 材料カタログの全部の列名、往復の照らし | ③ |
| a2fcbbd | engine_tuner_exec.py | 4190〜4279 | selftest の T-f・T-g・T-h・T-d | 読む | オン・オフと定義表 | ③ |
| a2fcbbd | engine_tuner_exec.py | 4541〜4542 | const_registry_live_check | 読む | 定数の表と実装の値の照らし | ③ |
| a2fcbbd | engine_tuner_exec.py | 4606〜4608 | lineage_coverage | 読む | 全部の種類に系統が付いているか | ③ |
| a2fcbbd | engine_tuner_exec.py | 5147 | selftest の需給 | 読む | 需給の元データの名前 | ③ |
| a385a4c | engine_tuner_fire_diag.py | 84,106 | cond_label | 読む | 条件の形の性質の表 | ③ |
| a385a4c | engine_tuner_fire_diag.py | 101 | cond_label | 読む | 材料の名前を列の名前にする規則 | ③ |
| a385a4c | engine_tuner_fire_diag.py | 209 | funnel_one | 読む | 場面の判定の列 | ③ |
| a385a4c | engine_tuner_fire_diag.py | 357 | run_main | 読む | 役割と件数/日の下限 | ③ |
| a385a4c | engine_tuner_fire_diag.py | 384,393,416,436-437 | run_main | 読む／作る | 材料の候補・時間足・材料の列・分位の一覧・分位から閾値を出す表 | ③ |
| a385a4c | engine_tuner_fire_diag.py | 425-433 | run_main | 読む／作る | 名前の別名の対応表 | ③ |
| aa6cd8e | gen_acceptance.py | 812-826 | _table_kinds | 読む | 型の表の部品から指標の種類を引く | ③ |
| aa6cd8e | gen_acceptance.py | 829-840 | _timeframe_rows | 読む | 使える時間足と、役割ごとの時間足 | ③ |
| aa6cd8e | gen_acceptance.py | 843-878 | _indicator_rows | 読む | 指標ごとのパラメータの名前・範囲（下限・上限・出どころ）・代表の値（スキャル／デイトレ）と出どころ・役割（出どころの役割・役割の印）・閾値の値・オンかオフか・カタログに在るか | ③ |
| aa6cd8e | gen_acceptance.py | 881-922 | _auto_rows | 読む | 法則（番号・場面・一文・説明・機械が読む判定）・型の id と name | ③ |
| aa6cd8e | gen_acceptance.py | 965-1028 | build_materials | 読む | オンの指標・geo_on・demand_on・time_on・役割ごとの系統と時間足とレンジ幾何・探す範囲の鍵 | ③ |
| aa6cd8e | gen_acceptance.py | 1031-1077 | build_laws | 読む | 機械が読む判定の「数える部品」 | ③ |
| aa6cd8e | gen_acceptance.py | 1080-1108 | build_ranking | 読む | 成績表の役割ごと・"強さ"・先読みの列の本数と、分離力の上位 | ③ |
| aa6cd8e | gen_acceptance.py | 1319-1361 | build_stages | 読む | §2.2 の段の材料（系統）・時間足・値の範囲 | ③ |
| aa6cd8e | gen_acceptance.py | 1673-1682 | indicator_sources_problems | 読む | check_indicator_sources.check1 を呼ぶ | ③ |
| aa6cd8e | gen_audit_docs.py | 1655-1676 | _design_five_questions（Q2） | 読む | 設計書の 4-6・4-21・4-7 の表（指標・閾値・パラメータ・時間足の扱い）を依頼書へ写す | ③ |
| a385a4c | gen_audit_request.py | 286-318 | copy_all_laws | 読む | 法則の一覧 | ③ |
| ace0f74 | gen_composition_rules.py | 98-103 | lineage の照合 | 読む | 系統の2か所のずれ | ③ |
| ace0f74 | gen_exit_families.py | 114-183 | `exec_capability` | 読む | 状態列・形・FAMILY_TEMPLATES | ③ |
| ace0f74 | gen_exit_families.py | 403-410 | confirm_conditions | 読む | 確認の条件の材料・閾値 | ③ |
| ace0f74 | gen_indicator_switch.py | 64-74 | `ta_classes` | 読む | ta のクラス | ③ |
| ace0f74 | gen_indicator_switch.py | 77-83 | `families` | 読む | family の一覧 | ③ |
| ace0f74 | gen_indicator_switch.py | 86-98 | `ta_map_from_ext` | 読む | ta のクラスから family | ③ |
| ace0f74 | gen_indicator_switch.py | 135-143 | `ta_map_approved` | 読む | 承認済みの対応 | ③ |
| ace0f74 | gen_indicator_switch.py | 158-210 | `law_named`・`law_geo`・`source_law` | 読む | 法則が名指しする family・系統・性質・geo | ③ |
| ace0f74 | gen_indicator_switch.py | 213-250 | `source_identity` | 読む | 恒等レシピの材料 | ③ |
| ace0f74 | gen_indicator_switch.py | 253-295 | `source_mako`・`source_time`・`source_mako_geo` | 読む | まこさんの決定・時間帯・geo | ③ |
| a97a087 | gen_indicator_table.py | 55-63 | `read_block` | 読む | INDICATOR_TABLE | ③ |
| a97a087 | gen_indicator_table.py | 66-73 | `scan_rows` | 読む | `_r` の呼び出し | ③ |
| a97a087 | gen_indicator_table.py | 76-97 | `load_families` | 読む | REFS の family | ③ |
| a97a087 | gen_indicator_table.py | 100-112 | `role_of` | 読む | 役割 | ③ |
| a97a087 | gen_indicator_table.py | 115-130 | `compute` | 読む・作る | 役割・札・性質（方向から） | ③ |
| a97a087 | gen_indicator_table.py | 145-185 | `problems` | 読む | ①〜⑥の照らし | ③ |
| a97a087 | gen_indicator_table.py | 192-209 | `counts` | 読む | 表の数 | ③ |
| ace0f74 | gen_materials.py | 92-135 | `_engine_view` | 読む | 選べる指標・パラメータ・時間足・カタログの列 | ③ |
| ace0f74 | gen_materials.py | 115 | `demand=od._DEMAND_FILES` | 読む | 需給の名前 | ③ |
| ace0f74 | gen_materials.py | 117-121 | geo_ok・time_ok・demand_ok | 読む | 別枠の部品 | ③ |
| ace0f74 | gen_materials.py | 175-182 | `_dropped_columns` | 読む | 同じ挙動として省いた列 | ③ |
| ace0f74 | gen_materials.py | 269-277 | `_roles_by_lineage` | 読む | 系統から役割への対応 | ③ |
| ace0f74 | gen_materials.py | 280-286 | `_lib_funcs` | 読む | ライブラリの関数とカテゴリ | ③ |
| ace0f74 | gen_materials.py | 289-300 | `_source_note` | 読む | 計算の出どころ・照合の相手 | ③ |
| ace0f74 | gen_materials.py | 454-478 | `_catalog_keys` | 読む（AST） | パラメータの設定の鍵 | ③ |
| ace0f74 | gen_materials.py | 481-492 | `_a1_place1` | 読む | 指標のパラメータの並び | ③ |
| ace0f74 | gen_materials.py | 495-531 | `_a1_place2` | 読む | 閾値の分位・本数の格子・範囲 | ③ |
| ace0f74 | gen_materials.py | 682-775 | `param_range_both_ways` | 読む・確かめる | パラメータの範囲と、列名の組み立て | ③ |
| ace0f74 | gen_materials.py | 778-839 | `forms_table` | 読む | 条件の形 | ③ |
| ace0f74 | gen_materials.py | 944-1001 | `parts_matrix` | 読む | 指標ごとのパラメータの数・定番のクロス | ③ |
| ace0f74 | gen_materials.py | 1062-1139 | `_regime_decl_view` | 読む | 相場の判定の列 | ③ |
| ace0f74 | gen_materials.py | 1194-1200 | `_m2_baseline_view` | 読む | 部品・時間足の数 | ③ |
| a385a4c | gen_observe_manual.py | 147-149 | _catalog_names | 読む | 指標の種類の名前 | ③ |
| a385a4c | gen_observe_manual.py | 153-159 | _mode_rows | 読む | 探索の系統 | ③ |
| a385a4c | gen_observe_manual.py | 162-172 | _pair_cols | 読む | 玉と玉の間の特徴の列名 | ③ |
| a385a4c | gen_observe_manual.py | 337-338 | build | 読む | 時間足と分位の数 | ③ |
| a385a4c | gen_observe_manual.py | 368,378 | build | 読む | 需給のデータ・場面の型 | ③ |
| a385a4c | gen_observe_manual.py | 418-422 | build | 読む | 設定の全部の項目 | ③ |
| aa6cd8e | gen_regime_kb.py | 32-40 | SRC | 読む | 法則・段の候補 | ③ |
| aa6cd8e | gen_regime_kb.py | 236-249 | coverage | 読む | 法則の「機械が読む判定」と「判定の置き場」 | ③ |
| aa6cd8e | gen_regime_kb.py | 540-631 | build_premise | 読む／作る（文書） | 法則の「機械が読む判定」と「掛かる場面」 | ③ |
| aa6cd8e | gen_regime_kb.py | 735-844 | build_laws | 読む／作る（KB §11） | 法則（一文・見ているもの・使う段）と、名前が出ていない指標の注記 | ③ |
| aa6cd8e | gen_regime_kb.py | 1063-1085 | _load_indicator_refs | 読む | 指標名から系統への対応・系統の集合・レンジ幾何の比率の列・前処理の名前 | ③ |
| aa6cd8e | gen_regime_kb.py | 1110-1205 | expand_stage | 読む／作る | 段ごとの役割・法則（law・law_or・law_width・law_tf）・指標名・系統・前処理（pre）・窓つきの前処理（pre_win＝op と months）・geo_cols・bool_col | ③ |
| aa6cd8e | gen_regime_kb.py | 1208-1263 | _actual_candidates | 読む | 実際の候補・オンかオフか・成績表の役割の列 | ③ |
| aa6cd8e | gen_s22_combi.py | 53・:123-138 | LIMITS・width | 読む | 閾値の分位・続く本数・保つ上限の lo と hi | ③ |
| aa6cd8e | gen_s22_combi.py | 69-71 | laws_for_scene・_law_families | 読む | 法則が名指しする family | ③ |
| aa6cd8e | gen_s22_combi.py | 77-79 | load_signal_table()["tfs"] | 読む | 使える時間足 | ③ |
| aa6cd8e | gen_s22_combi.py | 85-94・:114-121 | groups・ranked_groups | 読む | 役割ごとの（family, tf）の組 | ③ |
| aa6cd8e | gen_s22_combi.py | 106-115 | STAGES の import | 読む（失敗する） | 段1 の候補 | ③ |
| ace0f74 | gen_signal_families.py | 53-62 | `_catalog` | 読む | 部品の名前・時間足 | ③ |
| ace0f74 | gen_signal_families.py | 999-1011 | 禁止3 の見本選び | 読む | 印のオン・オフ | ③ |
| ace0f74 | gen_signal_families.py | 1291-1305 | `_v9_indicators` | 読む | V9 の指標10種 | ③ |
| aa6cd8e | gen_stage0_match.py | 53 | RANKING | 読む | 成績表の列名（指標名＋期間＋札）を、役割・性質ごとに | ③ |
| aa6cd8e | gen_stage0_match.py | 69-105 | load_stages | 読む | 段ごとの指標名・系統・レンジ幾何の列・真偽の列 | ③ |
| aa6cd8e | gen_stage0_match.py | 115-131 | columns_of・count_hits | 読む | 列名に、その文字が含まれるか | ③ |
| aac5aa5 | gen_v9_exits.py | 41-42 | SRC・PARAMS | 読む | V9 の決済のコード・設定 | ③ |
| aac5aa5 | gen_v9_exits.py | 161-181 | _tp_keys・_param_value | 読む | 利確の設定の鍵と値 | ③ |
| a97a087 | indicator_reference_diag.py | 28-49 | `_ta`・`_pta`・`_sps`、TA_OK・PTA_OK・SCIPY_OK | 読む | ext と ext2 で照らす相手 | ③ |
| a97a087 | indicator_reference_diag.py | 1263-1283 | `_r` | 読む・作る | REFS の1件 | ③ |
| a97a087 | indicator_reference_diag.py | 1286-1317 | `_num`・`_FIND_MEMO`・`find`・`coverage` | 読む | 名前からパラメータを取り出す | ③ |
| a97a087 | indicator_reference_diag.py | 1954-1960 | `_tb_band_floor` | 読む | 帯の部品の床 | ③ |
| a97a087 | indicator_reference_diag.py | 5370-5415 | `_range_geo_case`・`range_geo_known_check` | 読む・作る | レンジ幾何の known | ③ |
| a97a087 | indicator_reference_diag.py | 5475-5481 | `_lineage_from_table`・FAMILY_LINEAGE | 読む・作る | 札（系統） | ③ |
| a97a087 | indicator_reference_diag.py | 5515-5517 | `lineage_coverage` | 読む | FAMILY_LINEAGE | ③ |
| a97a087 | indicator_reference_diag.py | 5972-5994 | `industry_gap` | 読む | INDUSTRY_MAP・INDUSTRY_SKIP | ③ |
| a97a087 | indicator_reference_diag.py | 6023-6033 | `const_registry_live_check` | 読む | CONST_REGISTRY | ③ |
| a97a087 | indicator_reference_diag.py | 6056-6102 | `tokenize_ec`・`axis_ec_check` | 読む | AXIS_EC | ③ |
| a385a4c | leak_causality_diag.py | 164-173 | load_features | 読む | 指標の列を付けたデータ | ③ |
| a385a4c | leak_causality_diag.py | 199-200,209 | run_e38_trades | 読む | 帯の1時間足の区切り（h1_edge）・前処理 | ③ |
| a385a4c | leak_causality_diag.py | 207 | adaptive_k | 読む | 帯のパラメータ | ③ |
| a385a4c | leak_causality_diag.py | 323 | load_tuner_df | 読む | 指標の列を付けたデータ | ③ |
| a385a4c | leak_causality_diag.py | 337,344 | tuner_recipes | 読む | 材料の候補・時間足 | ③ |
| a385a4c | leak_causality_diag.py | 442-444,454 | tuner_check | 読む | 分位の一覧と、分位から閾値を出す表 | ③ |
| aecb27a | observe_diag.py | 115 | `import indicator_reference_diag as iref` | 読む | 照合・既知答え・定義表 | ③ |
| aecb27a | observe_diag.py | 203-224 | `load_config` | 読む | 時間足 | ③ |
| aecb27a | observe_diag.py | 709-712 | `_band_fee_floor` | 読む | 閾値（帯の、取れる距離の床） | ③ |
| aecb27a | observe_diag.py | 908-917 | `_pta6`・`_load_pta` | 読む | ライブラリとの対応 | ③ |
| aecb27a | observe_diag.py | 1792-2229 | `build_catalog` | 読む・作る | パラメータの値・名前・オン・オフ | ③ |
| aecb27a | observe_diag.py | 2214-2216 | 使われない material_params の検査 | 読む | パラメータ | ③ |
| aecb27a | observe_diag.py | 2220-2228 | `drop_columns` | 読む | オン・オフ（同じ挙動の列を省く） | ③ |
| aecb27a | observe_diag.py | 2326-2353 | `load_1m` | 読む | 前処理（1m・3m の元データ） | ③ |
| aecb27a | observe_diag.py | 2426-2448 | `load_demand` | 読む | 需給の指標3種 | ③ |
| aecb27a | observe_diag.py | 2452-2456 | `_rg_zone_consts` | 読む | レンジ幾何のパラメータ | ③ |
| aecb27a | observe_diag.py | 2484-2526 | `_insp_range_geo` | 読む | 照合・既知答え | ③ |
| aecb27a | observe_diag.py | 2579-2580 | `rank_separation_independent` | 読む | 時間足 | ③ |
| aecb27a | observe_diag.py | 2933-2950 | `_one_side` の保有中のシグナル | 読む | 方向・閾値（分位） | ③ |
| aecb27a | observe_diag.py | 3419-3424 | `_scene_floor` | 読む | 閾値 | ③ |
| aecb27a | observe_diag.py | 3427-3443 | `_scene_data` | 読む | 前処理・時間足の区切り | ③ |
| aecb27a | observe_diag.py | 3489-3511 | `_sk_zscore_short/long` | 読む | 指標（dev_z）と閾値 | ③ |
| aecb27a | observe_diag.py | 3540-3550 | `_grid_touch` | 読む | パラメータ | ③ |
| aecb27a | observe_diag.py | 3777-3869 | `_conf_search` | 読む | 区分・時間足・閾値（分位） | ③ |
| aecb27a | observe_diag.py | 3914-3925 | `plan_scene` | 読む | 区分 | ③ |
| aecb27a | observe_diag.py | 4109・4132-4136 | `plan` | 読む | 種類の名前 | ③ |
| aecb27a | observe_diag.py | 4451-4500 | `_insp_resample` | 読む | 時間足 | ③ |
| af05308 | observe_diag.py | 4510-4642 | `_insp_indicator_match` | 読む | 照合（ライブラリ ta・2つ目の照合・独立実装・既知答え・許容差・写しの印） | ③ |
| af05308 | observe_diag.py | 4645-4692 | `_insp_property` | 読む | 性質（trend／vol／それ以外） | ③ |
| af05308 | observe_diag.py | 4695-4740 | `_ref_coverage_counts`・`_insp_ref_coverage` | 読む | 照合の相手の有無（ext・EXT2・known） | ③ |
| af05308 | observe_diag.py | 4743-4770 | `_insp_indicator_stage` | 読む | 定義・流儀・方向の印字と、3区分 | ③ |
| af05308 | observe_diag.py | 4773-4820 | `_insp_lookahead` | 読む | 列（名前__時間足）の作り方 | ③ |
| af05308 | observe_diag.py | 4823-4831 | `_nominal_wlen` | 読む | パラメータの値（名前の文字から取る） | ③ |
| af05308 | observe_diag.py | 4834-4873 | `_insp_samples` | 読む | 列の名前の型 `f"{name}__{tf}"`・時間足 | ③ |
| af05308 | observe_diag.py | 4882-4958 | `_insp_demand` | 読む | 需給の定義・流儀・方向・出典 | ③ |
| af05308 | observe_diag.py | 4961-4977 | `_insp_axis` | 読む | 軸カタログ E-c との対応表 | ③ |
| af05308 | observe_diag.py | 5018-5052 | `_insp_industry` | 読む | ライブラリとの対応表・入れない候補 | ③ |
| af05308 | observe_diag.py | 5099-5126 | `_v9_periods` | 読む | V9 が使う期間 | ③ |
| af05308 | observe_diag.py | 5129-5155 | `_insp_v9_periods` | 読む | 設定の期間の一覧 | ③ |
| af05308 | observe_diag.py | 5170-5230 | 検査13 `_price_scale_check` | 読む | カタログの全種（H6） | ③ |
| af05308 | observe_diag.py | 5376-5399 | `_recipe_families` | 読む | レシピが使う family | ③ |
| af05308 | observe_diag.py | 5416-5457 | `_dup_used_in_strategies` | 読む | 戦略のファイルで使っている行の数 | ③ |
| af05308 | observe_diag.py | 5485-5511 | `_dup_used_in_repo` | 読む | レシピ・設定で使っているか | ③ |
| af05308 | observe_diag.py | 5514-5558 | `_dup_keep_of_group` | 読む | V9 か・レシピか・業界の関数の有無・暖機 | ③ |
| af05308 | observe_diag.py | 5583-5627 | `_tol_saturation_cells`・`_insp_tol_saturation`（検査16） | 読む | S-R の帯の許容幅の上下限（閾値） | ③ |
| af05308 | observe_diag.py | 5630-5742 | `inspect_data` | 読む | カタログを名前で絞る | ③ |
| af05308 | observe_diag.py | 5764-5809 | `_v9_preprocess_frame`・`_v9_price_kinds` | 読む | V9 の指標の列 | ③ |
| af05308 | observe_diag.py | 5844-5853 | `_v9_part_grid` | 読む | 部品の n・m | ③ |
| af05308 | observe_diag.py | 5930-6061 | `_v9_col_matches`・`_insp_v9_columns` | 読む | V9 の列とうちの列の対応 | ③ |
| af05308 | observe_diag.py | 6080-6092 | `_SWITCH_PATH`・`_switch_on` | 読む | オン・オフ | ③ |
| af05308 | observe_diag.py | 6119-6286 | `_insp_direction_known`（材料の検査1） | 読む | 方向・性質・既知答え・役割・オン | ③ |
| af05308 | observe_diag.py | 6289-6341 | `_insp_lineage_range`（材料の検査2） | 読む | 系統と値域 | ③ |
| af05308 | observe_diag.py | 6675-6679 | `_role_lineage_table` | 読む | 役割ごとの系統と時間足 | ③ |
| af05308 | observe_diag.py | 6682-6694 | `_independent_step` | 読む | 時間足の長さ | ③ |
| af05308 | observe_diag.py | 6768-6870 | `rank_materials_for_regime` | 読む／作る | 系統と役割の時間足による絞り | ③ |
| af05308 | observe_diag.py | 7454-7481 | `selftest_lineage` | 読む | 系統の区分・系統の表・答える問い | ③ |
| af05308 | observe_diag.py | 7754-7809 | `selftest_match` | 読む | 既知答えと写しの印 | ③ |
| aa6cd8e | pre_audit_check.py | 108-122 | FINGERPRINT_FILES | 読む（バイト） | 指標の置き場の指紋 | ③ |
| aa6cd8e | pre_audit_check.py | 200-229 | _v9_sources・materials_fingerprint | 読む | 材料の検査が読むファイルの指紋 | ③ |
| a385a4c | regime_label.py | 46,61-81 | load_config | 読む | 正解ラベルの式の版と数字 | ③ |
| a385a4c | regime_label.py | 84-87,313 | fee_floor | 読む | 手数料の床（帯の幅の基準に使う） | ③ |
| a385a4c | regime_label.py | 578,647 | selftest T8・T17 | 読む | 役割ごとの保有の範囲（2か所に書いてある値を照らす） | ③ |
| a385a4c | regime_r9_diag.py | 202-215 | _labels_for | 読む | 正解ラベル | ③ |
| a385a4c | regime_r9_diag.py | 228,260-263,269,299-302 | measure・_qtable | 読む／作る | レンジ幾何・需給の列・分位から閾値を出す表 | ③ |
| a385a4c | regime_r9_diag.py | 305-332 | print_stage_candidates | 読む | 段ごとの指標の候補 | ③ |
| a385a4c | regime_r9_diag.py | 354-361 | _q50_width_cond | 読む | 帯の幅の条件 | ③ |
| a385a4c | regime_r9_diag.py | 364-398 | _loosened_off | 読む／作る | 分位を1段 緩めた閾値 | ③ |
| a385a4c | regime_r9_diag.py | 511-515 | run_stage | 読む | 成績表の正解ラベルの版と先を見るバー数 | ③ |
| a385a4c | regime_r9_diag.py | 550 | run_stage | 読む | 状態を保つ上限 | ③ |
| a385a4c | regime_r9_diag.py | 568 | run_stage | 読む | 場面の法則の審査（G7） | ③ |
| a385a4c | regime_r9_diag.py | 719-743 | run_nan_check | 読む／作る | 動く線の材料の前処理 | ③ |
| a385a4c | regime_r9_diag.py | 1009 | main | 読む | 助走の長さ | ③ |
| a385a4c | tuner_backcalc.py | 147-158 | analyse ⑤ | 読む／自前で計算 | 帯の幅の列名（2通り）と取り分の式 | ③ |
| a385a4c | tuner_backcalc.py | 187 | analyse ⑦ | 読む | 枠の占有 | ③ |
| a385a4c | tuner_judgement.py | 131-168 | role_of・role_floor | 読む | 役割と件数/日の下限 | ③ |
| a385a4c | tuner_judgement.py | 354-453 | neighbor_points | 読む／作る | パラメータ・閾値の前後の点 | ③ |

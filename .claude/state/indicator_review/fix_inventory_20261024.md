# 直す相手の一覧（gen_fix_inventory.py が実物から作った・手で書き替えない）

範囲＝engine_tuner の入口から import でたどれるファイルと、その json と INDICATOR_TABLE を書くプログラム・資料の表（gen_fix_inventory.py の頭の説明）。
振り分け＝持つ→①写す→②消す ／ 直書き・読む・自前で計算→③向け直す ／ json は表のとおり。

## プログラム（ファイルごとの数）

| ファイル | 持つ | 読む | 直書き | 自前で計算 |
|---|---|---|---|---|
| analyze.py | 2 | 8 | 5 | 0 |
| check_indicator_sources.py | 0 | 13 | 0 | 0 |
| count_builder_literals.py | 0 | 1 | 0 | 0 |
| e38.py | 0 | 0 | 0 | 1 |
| e38_logic_parts.py | 0 | 0 | 7 | 19 |
| enforce_g2_pass.py | 0 | 3 | 0 | 0 |
| engine_tuner.py | 0 | 0 | 0 | 0 |
| engine_tuner_exec.py | 10 | 76 | 37 | 24 |
| engine_tuner_fire_diag.py | 0 | 2 | 0 | 0 |
| engine_tuner_gen.py | 7 | 71 | 21 | 1 |
| gen_acceptance.py | 0 | 12 | 6 | 0 |
| gen_audit_docs.py | 0 | 1 | 0 | 0 |
| gen_audit_request.py | 2 | 3 | 0 | 0 |
| gen_composition_rules.py | 0 | 18 | 0 | 0 |
| gen_decisions.py | 0 | 2 | 0 | 0 |
| gen_docmap.py | 0 | 0 | 0 | 0 |
| gen_exit_families.py | 0 | 9 | 0 | 0 |
| gen_indicator_switch.py | 0 | 11 | 0 | 0 |
| gen_indicator_table.py | 3 | 10 | 0 | 0 |
| gen_materials.py | 1 | 47 | 2 | 0 |
| gen_observe_manual.py | 0 | 2 | 0 | 0 |
| gen_regime_kb.py | 0 | 8 | 0 | 0 |
| gen_s22_combi.py | 0 | 3 | 0 | 0 |
| gen_signal_families.py | 2 | 49 | 1 | 0 |
| gen_stage0_match.py | 0 | 3 | 0 | 0 |
| indicator_reference_diag.py | 318 | 27 | 0 | 0 |
| leak_causality_diag.py | 0 | 7 | 0 | 0 |
| observe_diag.py | 317 | 79 | 300 | 0 |
| pre_audit_check.py | 0 | 7 | 0 | 0 |
| precheck.py | 1 | 2 | 3 | 0 |
| ratchet_guards.py | 1 | 2 | 0 | 0 |
| regime_label.py | 1 | 3 | 0 | 16 |
| regime_r9_diag.py | 1 | 2 | 0 | 0 |
| report.py | 3 | 4 | 2 | 0 |
| score.py | 0 | 0 | 0 | 0 |
| tuner_backcalc.py | 0 | 0 | 0 | 0 |
| tuner_judgement.py | 0 | 0 | 3 | 0 |

## json（指標の名前が出てくる鍵の道の数）

| ファイル | 名前が出てくる所（一番外の鍵ごと） | 数 | すること |
|---|---|---|---|
| composition_rules.json | body 117 | 117 | ②消す（指標1種ごとの欄） |
| condition_parts.json | classic_crosses 22 | 22 | ③記録の名前で引く |
| exit_families.json | capability 301 | 301 | ②消す（指標1種ごとの欄） |
| exit_families_rules.json |  | 0 | ③記録の名前で引く |
| identity_s1_legacy.json | exits 3 | 3 | ③記録の名前で引く |
| identity_s2_legacy.json | entry 4 | 4 | ③記録の名前で引く |
| indicator_fix_plan.json | 対象の照らし 664・指標 185 | 849 | ②消す（売買のプログラムが読まない記録） |
| indicator_params_by_strategy.before_153.json | 指標 141 | 141 | ②消す（売買のプログラムが読まない記録） |
| indicator_params_by_strategy.json | 指標 185 | 185 | ①写す→②消す（資料の表） |
| indicator_params_review.json | []/種類 185・[]/元にした種類 39 | 224 | ①写す→②消す（資料の表） |
| indicator_roles_thresholds.json | []/種類 185 | 185 | ①写す→②消す（資料の表） |
| indicator_source_map.json | 項目 161 | 161 | ②消す（売買のプログラムが読まない記録） |
| indicator_switch.json | sources 226・on 185・off 116 | 527 | ①写す→②消す（ファイルごと） |
| m2_stage_candidates.json | 段 34 | 34 | ③記録の名前で引く |
| material_ranking.json |  | 0 | ③列の名前を記録から作る（成績の記録は残す） |
| materials.json | body 519 | 519 | ②消す（指標1種ごとの欄） |
| observe_config.json | material_params 87・material_first_hidden 43・material_keep 29・drop_columns 17 | 176 | ①写す→②消す（指標の部分） |
| r1_role_map.json | []/種類 90 | 90 | ①写す→②消す |
| r9_demand_fixture.json | meta 6 | 6 | ③記録の名前で引く |
| read_plan_src_m2c15-hidden-params-20261004.json | 読むもの 4 | 4 | ②消す（売買のプログラムが読まない記録） |
| regime_laws.json | 法則 45 | 45 | ③記録の名前で引く |
| search_limits.json | material_param_ranges 117 | 117 | ①写す→②消す（範囲） |
| signal_families.json | bans 1019・inventory 769・kubun 652・parts 652 | 3092 | ②消す（指標1種ごとの欄） |

## observe_config.json の古い鍵（値は数だけで、種類の名前を持たない・33個・すること＝①写す→②消す）

| 鍵 | 期間を決める種類の数 | 種類 |
|---|---|---|
| atr_periods | 17 | ADX・AROOND・AROONOSC・AROONU・ATR%・CHOP・DI差・S-Rタッチ1時間ATR・S-Rタッチ確定1時間ATR・UI・VHF・VTXM・VTXP・帯VA1時間ATR・帯pivot1時間ATR・帯pivot前週1時間ATR・帯スイング1時間ATR |
| band_touch | 2 | 帯スイング・帯スイング1時間ATR |
| bb_periods | 2 | BB%b・BB幅 |
| bb_sigma | 2 | BB%b・BB幅 |
| cmf_periods | 1 | CMF |
| donchian_periods | 3 | DPO%・DPO教科書%・Donchian幅 |
| ema_periods | 2 | EMA傾き・close vs EMA |
| fib_windows | 1 | fib位置 |
| fractal_k | 5 | fractal安値距離%・fractal高値距離%・安値切り上げ幅%・構造破断距離%・高値切り上げ幅% |
| ichimoku | 2 | 基準線・転換線 |
| keltner | 2 | Keltner上・Keltner下 |
| lee_mykland_k | 2 | LeeMykland・LeeMykland_E36版 |
| macd_params | 18 | KSTシグナル・MACDシグナル線%・MACDヒスト%・MACD線%・PPO・PPOシグナル・PPOヒスト・PVO・PVOシグナル・PVOヒスト・TRIX・TRIX_EMAシグナル・TRIX_EMAヒスト・TRIXシグナル・TRIXヒスト・TSI・TSIシグナル・TSIヒスト |
| mfi_periods | 1 | MFI |
| mmar_periods | 1 | close vs MMAR% |
| mmi_periods | 1 | MMI |
| obv_slope_periods | 5 | EFI比・EOM比・NVI傾き・OBV傾き・PVT傾き |
| pivot_windows | 3 | pivotPP・pivotR1・pivotS1 |
| rainbow | 1 | close vs RAINBOW% |
| rci_periods | 1 | RCI |
| realized_vol_periods | 4 | MAD比・realized_vol・realized_vol_rv・stdev% |
| roc_periods | 1 | ROC |
| rsi_periods | 11 | CCI・ER・RSI・StochRSI%D・StochRSI%K・StochRSI素%K・TRIX・TRIX_EMAシグナル・TRIX_EMAヒスト・TRIXシグナル・TRIXヒスト |
| sma_periods | 31 | KAMA傾き%・WMA傾き%・close vs ALMA%・close vs DEMA%・close vs FWMA%・close vs HMA%・close vs JMA%・close vs KAMA%・close vs LINREG%・close vs LRb%・close vs MCGD%・close vs MEDIAN%・close vs MIDPOINT%・close vs MIDPRICE%・close vs PWMA%・close vs RMA%・close vs SINWMA%・close vs SMA・close vs SSF%・close vs SSF平均%・close vs SWMA%・close vs T3%・close vs TEMA%・close vs TRIMA%・close vs TRIMA_TA%・close vs TSF%・close vs VIDYA%・close vs VIDYA_CMO%・close vs VWMA%・close vs WMA%・close vs ZLMA% |
| sr_atr1h_k | 6 | S-Rタッチ1時間ATR・S-Rタッチ確定1時間ATR・帯VA1時間ATR・帯pivot1時間ATR・帯pivot前週1時間ATR・帯スイング1時間ATR |
| sr_tol | 6 | S-Rタッチ数・S-Rタッチ確定数・帯VA・帯pivot・帯pivot前週・帯スイング |
| sr_windows | 6 | S-Rタッチ1時間ATR・S-Rタッチ数・S-Rタッチ確定1時間ATR・S-Rタッチ確定数・帯スイング・帯スイング1時間ATR |
| stoch_periods | 2 | Stoch%D・Stoch%K |
| swing_windows | 9 | W字・W字確定谷・n本安値・n本高値・swing安値距離・swing高値距離・安値からの経過バー・形スコア・高値からの経過バー |
| volume_ratio_periods | 1 | volume_ratio |
| vp_windows | 3 | POC・VAH・VAL |
| vwap_windows | 2 | close vs VWAP・close vs VWAP典型 |
| w_tol | 2 | W字・W字確定谷 |

## コードの中のパラメータ（設定の鍵から読まない種類・52種・すること＝①写す→②消す）

| ファイル | 行（_reg の行） | 中身 |
|---|---|---|
| observe_diag.py | 1723 | ABER位置 のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1728 | ABER原作位置 のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1347 | AO% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1758 | HT_DCPHASE のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1734 | HWC位置 のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1735 | HWC幅% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1346 | KST のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1736 | MASSI のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1674 | PSAR加速 のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1675 | PSAR反転 のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1390 | SMC_SWEEP のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1291 | SMC_SWEEP確定 のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1395 | SQZ_ON のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1420 | SQZ_ON_Carter のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1455 | STC のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1456 | STCstoch のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1740 | THERMO% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1750 | THERMO_EMA% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1748 | THERMO原作% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1739 | TR% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1485 | UO のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1722 | close vs ABER_ZG% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1730 | close vs ACCBL% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1731 | close vs ACCBU% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1732 | close vs CE_L% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1733 | close vs CE_S% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1668 | close vs CKSPl% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1669 | close vs CKSPs% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1602 | close vs FAMA% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1610 | close vs FAMA_HL% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1593 | close vs HILO% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1595 | close vs HT_TRENDLINE% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1598 | close vs HT_TRENDLINE_HL% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1600 | close vs HWMA% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1601 | close vs MAMA% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1609 | close vs MAMA_HL% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1670 | close vs PMAX% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1672 | close vs PSAR% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1678 | close vs SAREXT% のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1262 | 前日POC のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1264 | 前日VAH のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1266 | 前日VAL のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1244 | 前期間pivotPP のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1245 | 前期間pivotR1 のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1246 | 前期間pivotS1 のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1248 | 前週pivotPP のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1249 | 前週pivotR1 のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1250 | 前週pivotS1 のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1268 | 当日POC のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1270 | 当日VAH のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1272 | 当日VAL のパラメータ（計算の関数の既定値・設定の鍵から読まない） |
| observe_diag.py | 1198 | 当日VWAP のパラメータ（計算の関数の既定値・設定の鍵から読まない） |

## 照らし（エージェントの報告の行）

範囲の中の報告の行（持つ・読む・自前で計算）402 行のうち、このプログラムが拾えなかった行 220 行

- e38_logic_parts.py:37-39  _resample_htf  [自前で計算]  上位足（label=left・closed=left）
- engine_tuner_fire_diag.py:155-169  build_geo  [自前で計算]  レンジ幾何の列名と式
- leak_causality_diag.py:383,407  _sab・_sab_hl  [自前で計算（テスト用にわざと壊す）]  列の名前
- leak_causality_diag.py:560-583  _sab_local・_sab_global・_sab_lucky  [自前で計算（テスト用）]  列の名前
- regime_label.py:367-371  hindsight_range  [自前で計算]  時間足のまとめ（resample）
- analyze.py:231-232,251  N6・N8  [持つ]  入った時の指標の列名
- e38_logic_parts.py:20-26  import・SCALP_FLOOR・V11_SL_BUF・BE_TTL_BARS・UNIT_LOT  [読む・持つ]  手数料の床・SL のバッファ
- e38_logic_parts.py:33-34  HTF_PARTS・VOL_PARTS  [持つ]  部品の名前（名前に期間と時間足が入っている）
- e38_logic_parts.py:308・:476  gap  [持つ]  型を判定する gap
- engine_tuner.py:90-91  FINGERPRINT_FILES  [持つ]  データの作り方に関わるファイル
- engine_tuner.py:99  WARM  [持つ]  指標の計算の助走
- engine_tuner_exec.py:417〜449  MATERIAL_PRE・SINCE_OPS・NO_ARG_OPS  [持つ]  前処理の部品（指標の種類ごとではなく、全部の指標に共通）
- engine_tuner_exec.py:563〜567  PAIR_OPS  [持つ]  材料2本の組み方（指標に共通）
- engine_tuner_exec.py:647  `_excl` の鍵の一覧  [持つ]  材料の種別の鍵
- engine_tuner_exec.py:795〜810  _material_family  [持つ]  系統の判定に使う名前
- engine_tuner_exec.py:1059〜1066  _check_cond の時刻の範囲  [持つ・読む]  時間帯「時刻」の閾値の範囲
- engine_tuner_exec.py:2386  _static_level_px（zone opp）  [持つ]  余白の既定
- engine_tuner_exec.py:2521  _guards_ok  [持つ]  手数料の床の既定
- engine_tuner_exec.py:3008〜3022  engine_params_from_recipe  [持つ・読む]  S2 の材料名
- engine_tuner_exec.py:3174〜3178  _LEGACY_COL_SOURCE  [持つ]  legacy の材料列の名前と作り方
- engine_tuner_exec.py:3496〜3611  run_identity_s1 の checks  [読む・持つ]  v59・v47・v22・v24・v48 ほかの指標の閾値と名前
- engine_tuner_exec.py:4478〜4481  selftest の _geo9  [持つ]  合成の幾何
- engine_tuner_fire_diag.py:81-82  cond_label の role  [持つ]  役割の名前と日本語の対応表
- engine_tuner_fire_diag.py:493-503  _synth_recipe  [持つ（テスト用）]  場面の判定の列名・SL の幅
- engine_tuner_fire_diag.py:514,529-530  selftest  [持つ（テスト用）]  条件の形と閾値
- gen_audit_request.py:123  N_LAWS  [持つ]  法則の件数
- gen_audit_request.py:125-138  SOURCES  [持つ]  指標と場面の判定のコードの場所
- gen_composition_rules.py:114-122  `_extra_lineage`  [持つ]  geo と time の系統
- gen_indicator_switch.py:473-490  `_ON_KINDS`・`_OFF_KINDS`  [持つ]  材料の種類の区分
- gen_indicator_table.py:52  POS_MAX  [持つ]  `_r` の位置引数の数
- gen_observe_manual.py:66-106  GLOSSARY  [持つ]  指標・時間足・パラメータ・閾値の説明の文
- gen_observe_manual.py:129-140  SCENE_TYPE_JP  [持つ]  場面の型の日本語名
- gen_regime_kb.py:75-76  _FOREIGN  [持つ]  gen_materials.py が書く件数の囲み（部品・指標の件数）
- gen_s22_combi.py:56  DROP_TFS  [持つ]  時間足（外す物）
- gen_signal_families.py:90  `_TF_MIN`  [持つ]  時間足の分数
- gen_signal_families.py:229-273  role_lineage  [持つ]  役割ごとの系統と時間足
- gen_signal_families.py:275-297  direction_conflict DC1-4  [持つ]  向きの決まり
- gen_stage0_match.py:66  ROLES  [持つ（直書き）]  役割の名前
- gen_stage0_match.py:92  "レンジ幾何"  [持つ]  系統の名前の直書き
- indicator_reference_diag.py:51  `_IDX0`  [持つ]  known の合成バーの開始日
- indicator_reference_diag.py:942  REFS  [持つ（`_r` が足す）]  定義表の全部
- indicator_reference_diag.py:946-953  MAKO_K3・K7・K3B・B1S1・K3C  [持つ]  mako の欄
- indicator_reference_diag.py:1720-1726  `_SR_TOUCH_ATR_REMOVED`  [持つ]  外した S-RタッチATR の控え
- indicator_reference_diag.py:5346-5348  RANGE_GEO_TF  [持つ]  レンジ幾何の時間足
- indicator_reference_diag.py:5846-5883  SKIP_APPROVED_20260809・SKIP_POLICY_DUP_20260809・SKIP_APPROVED_20260810・SKIP_APPROVED  [持つ]  入れないライブラリの関数
- indicator_reference_diag.py:5885-5969  INDUSTRY_SKIP  [持つ]  入れない理由
- indicator_reference_diag.py:6052-6053  STATE_COLS  [持つ]  ポジションの状態の列
- leak_causality_diag.py:22-25  docstring  [持つ]  列の数
- observe_diag.py:178-180  `TF_RULE`  [持つ]  時間足
- observe_diag.py:186  `SUB_5M_TF`  [持つ]  時間足（1分足から作る足）
- observe_diag.py:187  `ONE_MIN_CSV`  [持つ]  前処理（1m・3m の元データ）
- observe_diag.py:200  `BARS_CSV`  [持つ]  前処理（元の5分足）
- observe_diag.py:250-259  `_DEMAND_FILES`  [持つ]  需給の指標3種（名前・ファイル・列）
- observe_diag.py:471  `_SR_ATR_TOL_LO, _SR_ATR_TOL_HI`  [持つ]  閾値（許容幅の下限と上限）
- observe_diag.py:490  `_H1_BASE`  [持つ]  前処理（1時間足の元になる5分足）
- observe_diag.py:873-890  `_CYC_MEMO`・`_cyc`  [持つ]  前処理（サイクル系の計算を使い回す）
- observe_diag.py:903  `MATERIAL_FAMILIES`  [持つ]  種類の名前・列の名前の型・方向・計算の式
- observe_diag.py:1507-1538  `_MA_FUNCS`  [持つ]  計算の式（移動平均24種）
- observe_diag.py:3469・3990  down 型の判定  [持つ]  閾値
- observe_diag.py:4983-4984  `_DIST_PAT`・`_SLOPE_PAT`  [持つ]  名前の規則
- observe_diag.py:5759-5761  `_V9_MATCH_*`・`_V9_INPUT_COLS`  [持つ]  V9 の列のうち対象外にする物
- observe_diag.py:5856-5882  `_v9_part_variants`  [持つ]  部品の式（slope・slope_avg）
- observe_diag.py:6069-6070  `_V9_SOURCES`・`_V9_RECORD_SINCE`  [持つ]  v9_logic.md の出どころ3本
- observe_diag.py:7558-7677  `selftest_atr1h`  [持つ／読む]  S-Rタッチ1時間ATR
- pre_audit_check.py:58-62  INDICATOR_SOURCES_CHECK・KNOWN_MATERIALS_PATH・MATERIALS_CSV・MATERIALS_CHECK  [持つ（パス）]  指標の照らしの道具・分かっている ❌ の一覧・材料の検査
- pre_audit_check.py:161-171  KNOWN_NG  [持つ]  指標の資料と設定ファイルの、分かっている食い違い
- pre_audit_check.py:177・:180-189  KNOWN_MATERIALS  [持つ／読む]  分かっている ❌ の一覧の sha256
- precheck.py:46  V17_LOWVOL_BANDS  [持つ]  ATR% の低ボラ帯の数
- ratchet_guards.py:175  _selftest  [持つ（テスト用）]  指標の列名
- regime_r9_diag.py:275-277  measure  [持つ]  比べる相手の判定の列名
- regime_r9_diag.py:888-892,901-902  selftest ⑪  [持つ（テスト用）]  レンジ幾何の列名・帯の条件
- report.py:30-35  EXIT_JP  [持つ]  指標の名前が入った決済の理由
- check_indicator_sources.py:46-49  kinds_of  [読む]  種類の名前（1種1行）
- check_indicator_sources.py:52-67  check1  [読む]  オンの一覧と、表3つの種類の照合
- e38.py:25  CONFIG  [読む]  設定
- e38.py:97-131  space  [読む]  探す範囲
- e38.py:134-147  hold_space  [読む]  保有の範囲
- e38.py:150-160  stop_rules  [読む]  atr_band_edges
- e38.py:277-293  regime  [読む]  相場の列
- e38.py:296-309  load_windows  [読む]  e37._load・e37.V25_K・v25_adaptive_band・h1_edge・parts.prepare_df
- e38_logic_parts.py:58  prepare_df  [読む]  RSI9
- e38_logic_parts.py:60  prepare_df  [読む]  RG の帯
- e38_logic_parts.py:95-114  _pullback_short  [読む]  stoch k/d のデッドクロス・rsi9 の下向き・陰線
- e38_logic_parts.py:117-134  _confirm_2axis  [読む]  htf_*・vol_* と th_*
- e38_logic_parts.py:149-154・:181-186  _zscore_short/long  [読む]  dev_z と z_th
- e38_logic_parts.py:157-166  _crash_rebound_long  [読む]  出来高の平均・drop_th・vol_mult
- e38_logic_parts.py:216-234  config_regime  [読む]  相場の列の名前
- e38_logic_parts.py:255-268  ctx  [読む]  atr・adx・stoch_k・e38_stoch_d・rsi9・dev_z・volume・v11_*
- e38_logic_parts.py:269-280  番人  [読む]  部品の名前と th_ の存在
- e38_logic_parts.py:460-463  grid  [読む]  atr・adx・stoch_k・v11_*
- engine_tuner.py:157-187  catalog_size・catalog_columns  [読む／作る]  指標の種類の数・時間足・列名の形
- engine_tuner.py:199-216  _print_regime  [読む]  場面の名前・判定の列名
- engine_tuner.py:235-265  _print_coverage  [読む]  探索が動かせる列・ロジックが読む列
- engine_tuner.py:428-449,583-585  _resolve_space・main  [読む]  探す範囲（int・float・cat・quantile）
- engine_tuner.py:595,614,750-751  main  [読む]  固定値・ATR% の帯の区切り
- engine_tuner_exec.py:37〜41  import 文（e37・parts・iref・_score・strat_base）  [読む]  指標の参照表・系統・定数の表、prepare_df の材料
- engine_tuner_exec.py:166〜185  load_indicator_switch  [読む]  指標のオン・オフ（本体・レンジ幾何・需給・時間帯）
- engine_tuner_exec.py:188〜197  indicator_enabled  [読む]  本体の指標のオン・オフ
- engine_tuner_exec.py:200〜227  geo_enabled・demand_enabled・time_enabled  [読む]  レンジ幾何・需給・時間帯のオン・オフ
- engine_tuner_exec.py:230〜232  indicator_switch_fingerprint  [読む]  印のハッシュ値
- engine_tuner_exec.py:733〜744  _check_param_range  [読む]  指標ごとのパラメータの範囲
- engine_tuner_exec.py:750〜792  _check_num_range・_check_q_range  [読む]  数字・分位の範囲（指標に共通）
- engine_tuner_exec.py:1100〜1102  _check_cond  [読む]  レンジ幾何のうち、価格水準の列を拒否する
- engine_tuner_exec.py:1289〜1339  load_regime_laws  [読む]  法則の「機械が読む判定」（family・geo・側・系統・性質・本数）
- engine_tuner_exec.py:1342〜1347  _upper_tfs  [読む]  時間足の並び
- engine_tuner_exec.py:1552  REGIME_NAMES  [読む]  場面の名前
- engine_tuner_exec.py:1812〜1828  validate_recipe の G2  [読む]  列ごとの補正後独立標本数
- engine_tuner_exec.py:1990〜2017  _vnum_q  [読む]  分位の閾値（列ごと）
- engine_tuner_exec.py:2032〜2068  material_array  [読む・作る]  指標の計算（その場で計算する）
- engine_tuner_exec.py:2247〜2250  touch の許容幅  [読む]  定数
- engine_tuner_exec.py:2483〜2485・2503  _ceiling_fire  [読む]  材料列（v35_range_top・rg5_uptrend）
- engine_tuner_exec.py:2676〜2683  run_recipe  [読む]  prepare_df の指標の列
- engine_tuner_exec.py:2756〜2757  run_recipe  [読む]  記録用の指標（atr_entry・adx_entry・k_entry）
- engine_tuner_exec.py:3707  box_tf  [読む]  時間足
- engine_tuner_exec.py:3964〜3974  _with_parts_cols  [読む]  prepare_df の部品名
- engine_tuner_exec.py:4541〜4542  const_registry_live_check  [読む]  定数の表と実装の値の照らし
- engine_tuner_exec.py:5147  selftest の需給  [読む]  需給の元データの名前
- engine_tuner_fire_diag.py:84,106  cond_label  [読む]  条件の形の性質の表
- engine_tuner_fire_diag.py:101  cond_label  [読む]  材料の名前を列の名前にする規則
- engine_tuner_fire_diag.py:209  funnel_one  [読む]  場面の判定の列
- engine_tuner_fire_diag.py:357  run_main  [読む]  役割と件数/日の下限
- engine_tuner_fire_diag.py:384,393,416,436-437  run_main  [読む／作る]  材料の候補・時間足・材料の列・分位の一覧・分位から閾値を出す表
- gen_acceptance.py:829-840  _timeframe_rows  [読む]  使える時間足と、役割ごとの時間足
- gen_acceptance.py:843-878  _indicator_rows  [読む]  指標ごとのパラメータの名前・範囲（下限・上限・出どころ）・代表の値（スキャル／デイトレ）と出どころ・役割（出どころの役割・役割の印）・閾値の
- gen_acceptance.py:881-922  _auto_rows  [読む]  法則（番号・場面・一文・説明・機械が読む判定）・型の id と name
- gen_acceptance.py:965-1028  build_materials  [読む]  オンの指標・geo_on・demand_on・time_on・役割ごとの系統と時間足とレンジ幾何・探す範囲の鍵
- gen_acceptance.py:1031-1077  build_laws  [読む]  機械が読む判定の「数える部品」
- gen_acceptance.py:1080-1108  build_ranking  [読む]  成績表の役割ごと・"強さ"・先読みの列の本数と、分離力の上位
- gen_acceptance.py:1319-1361  build_stages  [読む]  §2.2 の段の材料（系統）・時間足・値の範囲
- gen_audit_docs.py:1655-1676  _design_five_questions（Q2）  [読む]  設計書の 4-6・4-21・4-7 の表（指標・閾値・パラメータ・時間足の扱い）を依頼書へ写す
- gen_audit_request.py:286-318  copy_all_laws  [読む]  法則の一覧
- gen_exit_families.py:403-410  confirm_conditions  [読む]  確認の条件の材料・閾値
- gen_indicator_switch.py:64-74  `ta_classes`  [読む]  ta のクラス
- gen_indicator_switch.py:135-143  `ta_map_approved`  [読む]  承認済みの対応
- gen_indicator_switch.py:213-250  `source_identity`  [読む]  恒等レシピの材料
- gen_indicator_table.py:55-63  `read_block`  [読む]  INDICATOR_TABLE
- gen_indicator_table.py:66-73  `scan_rows`  [読む]  `_r` の呼び出し
- gen_indicator_table.py:192-209  `counts`  [読む]  表の数
- gen_materials.py:115  `demand=od._DEMAND_FILES`  [読む]  需給の名前
- gen_materials.py:117-121  geo_ok・time_ok・demand_ok  [読む]  別枠の部品
- gen_materials.py:280-286  `_lib_funcs`  [読む]  ライブラリの関数とカテゴリ
- gen_materials.py:289-300  `_source_note`  [読む]  計算の出どころ・照合の相手
- gen_materials.py:454-478  `_catalog_keys`  [読む（AST）]  パラメータの設定の鍵
- gen_materials.py:778-839  `forms_table`  [読む]  条件の形
- gen_materials.py:1062-1139  `_regime_decl_view`  [読む]  相場の判定の列
- gen_observe_manual.py:147-149  _catalog_names  [読む]  指標の種類の名前
- gen_observe_manual.py:153-159  _mode_rows  [読む]  探索の系統
- gen_observe_manual.py:162-172  _pair_cols  [読む]  玉と玉の間の特徴の列名
- gen_observe_manual.py:337-338  build  [読む]  時間足と分位の数
- gen_observe_manual.py:368,378  build  [読む]  需給のデータ・場面の型
- gen_observe_manual.py:418-422  build  [読む]  設定の全部の項目
- gen_regime_kb.py:236-249  coverage  [読む]  法則の「機械が読む判定」と「判定の置き場」
- gen_regime_kb.py:1110-1205  expand_stage  [読む／作る]  段ごとの役割・法則（law・law_or・law_width・law_tf）・指標名・系統・前処理（pre）・窓つきの前処理（pre_win
- gen_regime_kb.py:1208-1263  _actual_candidates  [読む]  実際の候補・オンかオフか・成績表の役割の列
- gen_s22_combi.py:69-71  laws_for_scene・_law_families  [読む]  法則が名指しする family
- gen_s22_combi.py:77-79  load_signal_table()["tfs"]  [読む]  使える時間足
- gen_s22_combi.py:85-94・:114-121  groups・ranked_groups  [読む]  役割ごとの（family, tf）の組
- gen_s22_combi.py:106-115  STAGES の import  [読む（失敗する）]  段1 の候補
- gen_signal_families.py:53-62  `_catalog`  [読む]  部品の名前・時間足
- gen_signal_families.py:999-1011  禁止3 の見本選び  [読む]  印のオン・オフ
- gen_signal_families.py:1291-1305  `_v9_indicators`  [読む]  V9 の指標10種
- gen_stage0_match.py:69-105  load_stages  [読む]  段ごとの指標名・系統・レンジ幾何の列・真偽の列
- gen_stage0_match.py:115-131  columns_of・count_hits  [読む]  列名に、その文字が含まれるか
- indicator_reference_diag.py:28-49  `_ta`・`_pta`・`_sps`、TA_OK・PTA_OK・SCIPY_OK  [読む]  ext と ext2 で照らす相手
- leak_causality_diag.py:164-173  load_features  [読む]  指標の列を付けたデータ
- leak_causality_diag.py:199-200,209  run_e38_trades  [読む]  帯の1時間足の区切り（h1_edge）・前処理
- leak_causality_diag.py:207  adaptive_k  [読む]  帯のパラメータ
- leak_causality_diag.py:323  load_tuner_df  [読む]  指標の列を付けたデータ
- leak_causality_diag.py:337,344  tuner_recipes  [読む]  材料の候補・時間足
- leak_causality_diag.py:442-444,454  tuner_check  [読む]  分位の一覧と、分位から閾値を出す表
- observe_diag.py:115  `import indicator_reference_diag as iref`  [読む]  照合・既知答え・定義表
- observe_diag.py:203-224  `load_config`  [読む]  時間足
- observe_diag.py:709-712  `_band_fee_floor`  [読む]  閾値（帯の、取れる距離の床）
- observe_diag.py:908-917  `_pta6`・`_load_pta`  [読む]  ライブラリとの対応
- observe_diag.py:2214-2216  使われない material_params の検査  [読む]  パラメータ
- observe_diag.py:2220-2228  `drop_columns`  [読む]  オン・オフ（同じ挙動の列を省く）
- observe_diag.py:2326-2353  `load_1m`  [読む]  前処理（1m・3m の元データ）
- observe_diag.py:2426-2448  `load_demand`  [読む]  需給の指標3種
- observe_diag.py:2452-2456  `_rg_zone_consts`  [読む]  レンジ幾何のパラメータ
- observe_diag.py:2484-2526  `_insp_range_geo`  [読む]  照合・既知答え
- observe_diag.py:2579-2580  `rank_separation_independent`  [読む]  時間足
- observe_diag.py:2933-2950  `_one_side` の保有中のシグナル  [読む]  方向・閾値（分位）
- observe_diag.py:3419-3424  `_scene_floor`  [読む]  閾値
- observe_diag.py:3427-3443  `_scene_data`  [読む]  前処理・時間足の区切り
- observe_diag.py:3489-3511  `_sk_zscore_short/long`  [読む]  指標（dev_z）と閾値
- observe_diag.py:3540-3550  `_grid_touch`  [読む]  パラメータ
- observe_diag.py:3777-3869  `_conf_search`  [読む]  区分・時間足・閾値（分位）
- observe_diag.py:3914-3925  `plan_scene`  [読む]  区分
- observe_diag.py:4109・4132-4136  `plan`  [読む]  種類の名前
- observe_diag.py:4510-4642  `_insp_indicator_match`  [読む]  照合（ライブラリ ta・2つ目の照合・独立実装・既知答え・許容差・写しの印）
- observe_diag.py:4645-4692  `_insp_property`  [読む]  性質（trend／vol／それ以外）
- observe_diag.py:4773-4820  `_insp_lookahead`  [読む]  列（名前__時間足）の作り方
- observe_diag.py:4823-4831  `_nominal_wlen`  [読む]  パラメータの値（名前の文字から取る）
- observe_diag.py:4834-4873  `_insp_samples`  [読む]  列の名前の型 `f"{name}__{tf}"`・時間足
- observe_diag.py:4882-4958  `_insp_demand`  [読む]  需給の定義・流儀・方向・出典
- observe_diag.py:4961-4977  `_insp_axis`  [読む]  軸カタログ E-c との対応表
- observe_diag.py:5129-5155  `_insp_v9_periods`  [読む]  設定の期間の一覧
- observe_diag.py:5170-5230  検査13 `_price_scale_check`  [読む]  カタログの全種（H6）
- observe_diag.py:5376-5399  `_recipe_families`  [読む]  レシピが使う family
- observe_diag.py:5485-5511  `_dup_used_in_repo`  [読む]  レシピ・設定で使っているか
- observe_diag.py:5514-5558  `_dup_keep_of_group`  [読む]  V9 か・レシピか・業界の関数の有無・暖機
- observe_diag.py:5583-5627  `_tol_saturation_cells`・`_insp_tol_saturation`（検査16）  [読む]  S-R の帯の許容幅の上下限（閾値）
- observe_diag.py:5630-5742  `inspect_data`  [読む]  カタログを名前で絞る
- observe_diag.py:5764-5809  `_v9_preprocess_frame`・`_v9_price_kinds`  [読む]  V9 の指標の列
- observe_diag.py:6682-6694  `_independent_step`  [読む]  時間足の長さ
- regime_label.py:46,61-81  load_config  [読む]  正解ラベルの式の版と数字
- regime_label.py:84-87,313  fee_floor  [読む]  手数料の床（帯の幅の基準に使う）
- regime_r9_diag.py:202-215  _labels_for  [読む]  正解ラベル
- regime_r9_diag.py:228,260-263,269,299-302  measure・_qtable  [読む／作る]  レンジ幾何・需給の列・分位から閾値を出す表
- regime_r9_diag.py:305-332  print_stage_candidates  [読む]  段ごとの指標の候補
- regime_r9_diag.py:354-361  _q50_width_cond  [読む]  帯の幅の条件
- regime_r9_diag.py:364-398  _loosened_off  [読む／作る]  分位を1段 緩めた閾値
- regime_r9_diag.py:550  run_stage  [読む]  状態を保つ上限
- regime_r9_diag.py:568  run_stage  [読む]  場面の法則の審査（G7）
- regime_r9_diag.py:719-743  run_nan_check  [読む／作る]  動く線の材料の前処理
- regime_r9_diag.py:1009  main  [読む]  助走の長さ
- tuner_backcalc.py:147-158  analyse ⑤  [読む／自前で計算]  帯の幅の列名（2通り）と取り分の式
- tuner_backcalc.py:187  analyse ⑦  [読む]  枠の占有
- tuner_judgement.py:131-168  role_of・role_floor  [読む]  役割と件数/日の下限
- tuner_judgement.py:354-453  neighbor_points  [読む／作る]  パラメータ・閾値の前後の点

## エージェントの行で、このプログラムが拾えなかった物（220行・文は報告のまま・実物の最初の行を付けた）

| ファイル | 行 | 報告の欄 | 名前 | 報告の中身 | 実物の最初の行 | 振り分け |
|---|---|---|---|---|---|---|
| e38_logic_parts.py | 37-39 | 自前で計算 | _resample_htf | 上位足（label=left・closed=left） | def _resample_htf(d5: pd.DataFrame, rule: str) -> pd.DataFrame: | 振り分けが無い |
| engine_tuner_fire_diag.py | 155-169 | 自前で計算 | build_geo | レンジ幾何の列名と式 | def build_geo(df: pd.DataFrame) -> dict: | ③向け直す |
| leak_causality_diag.py | 383,407 | 自前で計算（テスト用にわざと壊す） | _sab・_sab_hl | 列の名前 | x["stoch_k"] = pd.Series(x["stoch_k"]).shift(-6).to_numpy()   # H2OK: 番人の細工＝わざと未来を見せて検査が落ち | 振り分けが無い |
| leak_causality_diag.py | 560-583 | 自前で計算（テスト用） | _sab_local・_sab_global・_sab_lucky | 列の名前 | def _sab_local(df: pd.DataFrame) -> pd.DataFrame: | 振り分けが無い |
| regime_label.py | 367-371 | 自前で計算 | hindsight_range | 時間足のまとめ（resample） | w2 = pd.DataFrame({"high": win["high"].resample(tf, label="left", closed="left").max(), | 外す（B・指標の情報ではない） |
| analyze.py | 231-232,251 | 持つ | N6・N8 | 入った時の指標の列名 | cols = [c for c in ["entry_time", "exit_reason", "hold_min", "net_usd", "adx_at_entry", | ③向け直す（C・読む所） |
| e38_logic_parts.py | 20-26 | 読む・持つ | import・SCALP_FLOOR・V11_SL_BUF・BE_TTL_BARS・UNIT_LOT | 手数料の床・SL のバッファ | import e37_scalp as e37 | 振り分けが無い |
| e38_logic_parts.py | 33-34 | 持つ | HTF_PARTS・VOL_PARTS | 部品の名前（名前に期間と時間足が入っている） | HTF_PARTS = ("roc24_2h", "macd_2h", "di7_4h", "adx14_2h", "stochd14_2h")   # ≤ 側 | 振り分けが無い |
| e38_logic_parts.py | 308・:476 | 持つ | gap | 型を判定する gap | gap = 0.5 / 100.0                                      # 型判定 gap（v26_gap と同じ・診断列 ceil_type | 振り分けが無い |
| engine_tuner.py | 90-91 | 持つ | FINGERPRINT_FILES | データの作り方に関わるファイル | FINGERPRINT_FILES = ("e37_scalp.py", "e38_logic_parts.py", "build_regime_gate_rg.py", | 外す（B・指標の情報ではない） |
| engine_tuner.py | 99 | 持つ | WARM | 指標の計算の助走 | WARM = pd.Timedelta(days=60)                 # 助走（RG 168h＋rolling を満たす a-priori） | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 417〜449 | 持つ | MATERIAL_PRE・SINCE_OPS・NO_ARG_OPS | 前処理の部品（指標の種類ごとではなく、全部の指標に共通） | MATERIAL_PRE = { | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 563〜567 | 持つ | PAIR_OPS | 材料2本の組み方（指標に共通） | PAIR_OPS = { | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 647 | 持つ | `_excl` の鍵の一覧 | 材料の種別の鍵 | _excl = [k for k in ("legacy_col", "geo", "state", "time", "demand") if k in m] | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 795〜810 | 持つ | _material_family | 系統の判定に使う名前 | def _material_family(m: dict) -> str: | ③向け直す（C・読む所） |
| engine_tuner_exec.py | 1059〜1066 | 持つ・読む | _check_cond の時刻の範囲 | 時間帯「時刻」の閾値の範囲 | if lane != "legacy" and any(m.get("time") == "時刻" for m in mats): | ①写す→②消す（A・指標の情報） |
| engine_tuner_exec.py | 2386 | 持つ | _static_level_px（zone opp） | 余白の既定 | buf = _vnum(lv.get("buf", {"const": "V11_SL_BUF"})) | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 2521 | 持つ | _guards_ok | 手数料の床の既定 | floor = _vnum(guards.get("fee_floor", {"const": "SCALP_FLOOR"})) | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 3008〜3022 | 持つ・読む | engine_params_from_recipe | S2 の材料名 | def engine_params_from_recipe(recipe: dict) -> tuple[dict, dict, int]: | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 3174〜3178 | 持つ | _LEGACY_COL_SOURCE | legacy の材料列の名前と作り方 | _LEGACY_COL_SOURCE = {                      # 材料列の名前 → それを作る処理の名前 | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 3496〜3611 | 読む・持つ | run_identity_s1 の checks | v59・v47・v22・v24・v48 ほかの指標の閾値と名前 | lg = next(x for x in ad.config()["logics"] if x["id"] == "S1") | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 4478〜4481 | 持つ | selftest の _geo9 | 合成の幾何 | _geo9 = {"mid": np.array([97.0, 97.0]), "sup_hi": np.array([96.0, 96.0]), | 外す（B・指標の情報ではない） |
| engine_tuner_fire_diag.py | 81-82 | 持つ | cond_label の role | 役割の名前と日本語の対応表 | role = {"trigger": "引き金", "env": "環境認識", "sufficiency": "十分性", "location": "位置"}.get( | 外す（B・指標の情報ではない） |
| engine_tuner_fire_diag.py | 493-503 | 持つ（テスト用） | _synth_recipe | 場面の判定の列名・SL の幅 | def _synth_recipe(conds: list[dict]) -> dict: | 外す（B・指標の情報ではない） |
| engine_tuner_fire_diag.py | 514,529-530 | 持つ（テスト用） | selftest | 条件の形と閾値 | bull_cond = {"role": "trigger", "form": "candle_dir", "value": {"dir": "bull"}} | 外す（B・指標の情報ではない） |
| gen_audit_request.py | 123 | 持つ | N_LAWS | 法則の件数 | N_LAWS = 50                                   # §11 の法則の件数（C10＋R10＋U10＋D9＋S6＋T5） | 振り分けが無い |
| gen_audit_request.py | 125-138 | 持つ | SOURCES | 指標と場面の判定のコードの場所 | SOURCES = [ | 振り分けが無い |
| gen_composition_rules.py | 114-122 | 持つ | `_extra_lineage` | geo と time の系統 | def _extra_lineage(sig: dict) -> dict: | 振り分けが無い |
| gen_indicator_switch.py | 473-490 | 持つ | `_ON_KINDS`・`_OFF_KINDS` | 材料の種類の区分 | _ON_KINDS = {"family", "geo", "demand", "time"}      # 印で切り替える（一律＝M2-C の見出し） | 外す（B・指標の情報ではない） |
| gen_indicator_table.py | 52 | 持つ | POS_MAX | `_r` の位置引数の数 | POS_MAX = 4                                     # _r の位置引数＝pat・family・teigi・ryugi（方向・性質は表か | 外す（B・指標の情報ではない） |
| gen_observe_manual.py | 66-106 | 持つ | GLOSSARY | 指標・時間足・パラメータ・閾値の説明の文 | GLOSSARY: list[tuple[str, str]] = [ | 振り分けが無い |
| gen_observe_manual.py | 129-140 | 持つ | SCENE_TYPE_JP | 場面の型の日本語名 | SCENE_TYPE_JP = { | 振り分けが無い |
| gen_regime_kb.py | 75-76 | 持つ | _FOREIGN | gen_materials.py が書く件数の囲み（部品・指標の件数） | _FOREIGN = (("<!-- BANS_COUNT_START", "<!-- BANS_COUNT_END -->"), | 外す（B・指標の情報ではない） |
| gen_s22_combi.py | 56 | 持つ | DROP_TFS | 時間足（外す物） | DROP_TFS = ("1m", "3m", "10m") | 振り分けが無い |
| gen_signal_families.py | 90 | 持つ | `_TF_MIN` | 時間足の分数 | _TF_MIN = {"5m": 5, "10m": 10, "15m": 15, "30m": 30, "1h": 60, "2h": 120, "4h": 240, "6h": | 外す（B・指標の情報ではない） |
| gen_signal_families.py | 229-273 | 持つ | role_lineage | 役割ごとの系統と時間足 | role_lineage=dict( | ①写す→②消す（A・指標の情報） |
| gen_signal_families.py | 275-297 | 持つ | direction_conflict DC1-4 | 向きの決まり | direction_conflict=dict( | ①写す→②消す（A・指標の情報） |
| gen_stage0_match.py | 66 | 持つ（直書き） | ROLES | 役割の名前 | ROLES = ("env", "location", "sufficiency", "trigger") | 振り分けが無い |
| gen_stage0_match.py | 92 | 持つ | "レンジ幾何" | 系統の名前の直書き | if f == "レンジ幾何": | 振り分けが無い |
| indicator_reference_diag.py | 51 | 持つ | `_IDX0` | known の合成バーの開始日 | _IDX0 = "2026-03-01" | 外す（B・指標の情報ではない） |
| indicator_reference_diag.py | 942 | 持つ（`_r` が足す） | REFS | 定義表の全部 | REFS: list[dict] = [] | ①写す→②消す（A・指標の情報） |
| indicator_reference_diag.py | 946-953 | 持つ | MAKO_K3・K7・K3B・B1S1・K3C | mako の欄 | MAKO_K3 = '2026-10-07 まこさん決定「A」（K-3 を3つの工事に分け、K-3a で監査 CP60 の修正41 の (b)(c) と修正42 の比べる版を、今の | ①写す→②消す（A・指標の情報） |
| indicator_reference_diag.py | 1720-1726 | 持つ | `_SR_TOUCH_ATR_REMOVED` | 外した S-RタッチATR の控え | _SR_TOUCH_ATR_REMOVED = """（この節は 2026-09-06 に外した登録の控え。次に作る人が参照するために残す） | 外す（B・指標の情報ではない） |
| indicator_reference_diag.py | 5346-5348 | 持つ | RANGE_GEO_TF | レンジ幾何の時間足 | RANGE_GEO_TF = ("5m（1h ゾーンは label=right・closed=right で5分足の始まりの時刻を束ねる＝1時間足の区切りは正時から5分ずれる" | ①写す→②消す（A・指標の情報） |
| indicator_reference_diag.py | 5846-5883 | 持つ | SKIP_APPROVED_20260809・SKIP_POLICY_DUP_20260809・SKIP_APPROVED_20260810・SKIP_APPROVED | 入れないライブラリの関数 | SKIP_APPROVED_20260809: frozenset = frozenset({ | ①写す→②消す（A・指標の情報） |
| indicator_reference_diag.py | 5885-5969 | 持つ | INDUSTRY_SKIP | 入れない理由 | INDUSTRY_SKIP: dict[str, str] = { | ①写す→②消す（A・指標の情報） |
| indicator_reference_diag.py | 6052-6053 | 持つ | STATE_COLS | ポジションの状態の列 | STATE_COLS = ("unreal_pct", "mfe_pct", "mfe_prev_pct", "mae_pct", "peak_age_bars", "hold_m | 外す（B・指標の情報ではない） |
| leak_causality_diag.py | 22-25 | 持つ | docstring | 列の数 | 検査1-a｜指標の突き合わせ（速い・列の名前まで分かる） | 振り分けが無い |
| observe_diag.py | 178-180 | 持つ | `TF_RULE` | 時間足 | TF_RULE = {"1m": "1min", "3m": "3min", | 外す（B・指標の情報ではない） |
| observe_diag.py | 186 | 持つ | `SUB_5M_TF` | 時間足（1分足から作る足） | SUB_5M_TF = ("1m", "3m")                      # 5分足より短い足＝1分足の元データが材料 | 外す（B・指標の情報ではない） |
| observe_diag.py | 187 | 持つ | `ONE_MIN_CSV` | 前処理（1m・3m の元データ） | ONE_MIN_CSV = "data/BTCUSDT-1m-binance-taker-2023-06-01_2026-06-30.csv"   # ★2026-09-08（設計 | 外す（B・指標の情報ではない） |
| observe_diag.py | 200 | 持つ | `BARS_CSV` | 前処理（元の5分足） | BARS_CSV = "data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv" | 外す（B・指標の情報ではない） |
| observe_diag.py | 250-259 | 持つ | `_DEMAND_FILES` | 需給の指標3種（名前・ファイル・列） | _DEMAND_FILES = { | ①写す→②消す（A・指標の情報） |
| observe_diag.py | 471 | 持つ | `_SR_ATR_TOL_LO, _SR_ATR_TOL_HI` | 閾値（許容幅の下限と上限） | _SR_ATR_TOL_LO, _SR_ATR_TOL_HI = 0.0015, 0.006 | ①写す→②消す（A・指標の情報） |
| observe_diag.py | 490 | 持つ | `_H1_BASE` | 前処理（1時間足の元になる5分足） | _H1_BASE: dict = {"bars": None} | 外す（B・指標の情報ではない） |
| observe_diag.py | 873-890 | 持つ | `_CYC_MEMO`・`_cyc` | 前処理（サイクル系の計算を使い回す） | _CYC_MEMO: dict = {"sig": None, "v": {}} | 外す（B・指標の情報ではない） |
| observe_diag.py | 903 | 持つ | `MATERIAL_FAMILIES` | 種類の名前・列の名前の型・方向・計算の式 | MATERIAL_FAMILIES: dict[str, tuple] = {} | ①写す→②消す（A・指標の情報） |
| observe_diag.py | 1507-1538 | 持つ | `_MA_FUNCS` | 計算の式（移動平均24種） | _MA_FUNCS = [ | ①写す→②消す（A・指標の情報） |
| observe_diag.py | 3469・3990 | 持つ | down 型の判定 | 閾値 | isdn = np.isfinite(x["g"]["res_lo"]) & (x["g"]["res_lo"] > x["c"] * 1.005)   # down 型（天井が遠 | 外す（B・指標の情報ではない） |
| observe_diag.py | 4983-4984 | 持つ | `_DIST_PAT`・`_SLOPE_PAT` | 名前の規則 | _DIST_PAT = re.compile(r"^close vs (.+?)%")   # 「終値と◯◯の距離%」の部品 | ①写す→②消す（A・指標の情報） |
| observe_diag.py | 5759-5761 | 持つ | `_V9_MATCH_*`・`_V9_INPUT_COLS` | V9 の列のうち対象外にする物 | _V9_MATCH_SAME = 0.99999   # これを超えたら「うちのカタログに同じ意味の列が在る」 | ③向け直す |
| observe_diag.py | 5856-5882 | 持つ | `_v9_part_variants` | 部品の式（slope・slope_avg） | def _v9_part_variants(grid: list[int]) -> list[dict]: | ①写す→②消す（A・指標の情報） |
| observe_diag.py | 6069-6070 | 持つ | `_V9_SOURCES`・`_V9_RECORD_SINCE` | v9_logic.md の出どころ3本 | _V9_SOURCES = ("strategies/cat_v9_decider.py", "runner/replay_csv.py", "config/cat_params_ | 外す（B・指標の情報ではない） |
| observe_diag.py | 7558-7677 | 持つ／読む | `selftest_atr1h` | S-Rタッチ1時間ATR | def selftest_atr1h(exit_: bool = True, bars_csv: str ／ None = None) -> list: | 外す（B・指標の情報ではない） |
| pre_audit_check.py | 58-62 | 持つ（パス） | INDICATOR_SOURCES_CHECK・KNOWN_MATERIALS_PATH・MATERIALS_CSV・MATERIALS_CHECK | 指標の照らしの道具・分かっている ❌ の一覧・材料の検査 | INDICATOR_SOURCES_CHECK = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tool | 振り分けが無い |
| pre_audit_check.py | 161-171 | 持つ | KNOWN_NG | 指標の資料と設定ファイルの、分かっている食い違い | KNOWN_NG = { | 振り分けが無い |
| pre_audit_check.py | 177・:180-189 | 持つ／読む | KNOWN_MATERIALS | 分かっている ❌ の一覧の sha256 | KNOWN_MATERIALS = dict(path=KNOWN_MATERIALS_PATH, sha="0c99daaa705d62f2918391952189ad59007 | 振り分けが無い |
| precheck.py | 46 | 持つ | V17_LOWVOL_BANDS | ATR% の低ボラ帯の数 | V17_LOWVOL_BANDS = 2   # ATR% 帯の低ボラ側（<0.2 の2帯）＝帯別証跡の合算対象（E37 v17 acceptance 2026-07-07 承認） | 外す（B・指標の情報ではない） |
| ratchet_guards.py | 175 | 持つ（テスト用） | _selftest | 指標の列名 | r = report_vol_importance({"atr_pct_7": 111939, "bb_slope_pct_20": 5000, "adx_14": 4000}) | 外す（B・指標の情報ではない） |
| regime_r9_diag.py | 275-277 | 持つ | measure | 比べる相手の判定の列名 | if "range_ok_rg5" in df.columns: | 外す（B・指標の情報ではない） |
| regime_r9_diag.py | 888-892,901-902 | 持つ（テスト用） | selftest ⑪ | レンジ幾何の列名・帯の条件 | _df11 = pd.DataFrame({"ts": pd.date_range("2024-03-01", periods=_n11, freq="5min"), "close | 外す（B・指標の情報ではない） |
| report.py | 30-35 | 持つ | EXIT_JP | 指標の名前が入った決済の理由 | EXIT_JP = {"TP_FILLED": "利確(TP)", "SL_FILLED": "損切(SL)", "TIME_EXIT": "時間切れ", "MFE_STALE_C | 外す（B・指標の情報ではない） |
| check_indicator_sources.py | 46-49 | 読む | kinds_of | 種類の名前（1種1行） | def kinds_of(p: Path) -> list: | 振り分けが無い |
| check_indicator_sources.py | 52-67 | 読む | check1 | オンの一覧と、表3つの種類の照合 | def check1(on=None, tables=None) -> list: | 振り分けが無い |
| e38.py | 25 | 読む | CONFIG | 設定 | CONFIG = HERE / "e38_logics.json" | 振り分けが無い |
| e38.py | 97-131 | 読む | space | 探す範囲 | def space(logic_id: str) -> dict: | 振り分けが無い |
| e38.py | 134-147 | 読む | hold_space | 保有の範囲 | def hold_space() -> dict: | 振り分けが無い |
| e38.py | 150-160 | 読む | stop_rules | atr_band_edges | def stop_rules(logic_id: str) -> dict: | 振り分けが無い |
| e38.py | 277-293 | 読む | regime | 相場の列 | def regime(logic_id: str) -> dict: | 振り分けが無い |
| e38.py | 296-309 | 読む | load_windows | e37._load・e37.V25_K・v25_adaptive_band・h1_edge・parts.prepare_df | def load_windows(windows, warm: pd.Timedelta) -> list[pd.DataFrame]: | 振り分けが無い |
| e38_logic_parts.py | 58 | 読む | prepare_df | RSI9 | df = e37._rsi9_v10(df) | 振り分けが無い |
| e38_logic_parts.py | 60 | 読む | prepare_df | RG の帯 | df = e37._apply_rg5_to_5m(df, adaptive_k=adaptive_k, h1_edge=h1_edge) | 振り分けが無い |
| e38_logic_parts.py | 95-114 | 読む | _pullback_short | stoch k/d のデッドクロス・rsi9 の下向き・陰線 | def _pullback_short(ctx, i, p): | 振り分けが無い |
| e38_logic_parts.py | 117-134 | 読む | _confirm_2axis | htf_*・vol_* と th_* | def _confirm_2axis(ctx, i, p) -> bool: | 振り分けが無い |
| e38_logic_parts.py | 149-154・:181-186 | 読む | _zscore_short/long | dev_z と z_th | def _zscore_short(ctx, i, p): | 振り分けが無い |
| e38_logic_parts.py | 157-166 | 読む | _crash_rebound_long | 出来高の平均・drop_th・vol_mult | def _crash_rebound_long(ctx, i, p): | 振り分けが無い |
| e38_logic_parts.py | 216-234 | 読む | config_regime | 相場の列の名前 | def config_regime() -> dict: | 振り分けが無い |
| e38_logic_parts.py | 255-268 | 読む | ctx | atr・adx・stoch_k・e38_stoch_d・rsi9・dev_z・volume・v11_* | ctx = { | 振り分けが無い |
| e38_logic_parts.py | 269-280 | 読む | 番人 | 部品の名前と th_ の存在 | _ch = entry_params.get("confirm_htf") or "none"        # 番人＝未知の部品名・閾値欠落は走らせない | 振り分けが無い |
| e38_logic_parts.py | 460-463 | 読む | grid | atr・adx・stoch_k・v11_* | atr_e = df["atr"].to_numpy(float); adx_e = df["adx"].to_numpy(float); k_e = df["stoch_k"]. | 振り分けが無い |
| engine_tuner.py | 157-187 | 読む／作る | catalog_size・catalog_columns | 指標の種類の数・時間足・列名の形 | def catalog_size() -> tuple[int, int] ／ None: | ③向け直す |
| engine_tuner.py | 199-216 | 読む | _print_regime | 場面の名前・判定の列名 | from tuner_adapters import REGIME_NAMES, check_regime | 外す（B・指標の情報ではない） |
| engine_tuner.py | 235-265 | 読む | _print_coverage | 探索が動かせる列・ロジックが読む列 | cov = getattr(ad, "coverage", None) | 外す（B・指標の情報ではない） |
| engine_tuner.py | 428-449,583-585 | 読む | _resolve_space・main | 探す範囲（int・float・cat・quantile） | def _resolve_space(space_decl: dict, bank: dict) -> dict: | ③向け直す |
| engine_tuner.py | 595,614,750-751 | 読む | main | 固定値・ATR% の帯の区切り | fixed_ep, fixed_xp = ad.fixed(a.logic, set(space)) | ③向け直す |
| engine_tuner_exec.py | 37〜41 | 読む | import 文（e37・parts・iref・_score・strat_base） | 指標の参照表・系統・定数の表、prepare_df の材料 | import e37_scalp as e37                      # noqa: E402  _record（記録＝会計の既存系）・SCALP_FLOOR  | ③向け直す |
| engine_tuner_exec.py | 166〜185 | 読む | load_indicator_switch | 指標のオン・オフ（本体・レンジ幾何・需給・時間帯） | def load_indicator_switch() -> dict: | ③向け直す |
| engine_tuner_exec.py | 188〜197 | 読む | indicator_enabled | 本体の指標のオン・オフ | def indicator_enabled(name: str) -> bool: | ③向け直す |
| engine_tuner_exec.py | 200〜227 | 読む | geo_enabled・demand_enabled・time_enabled | レンジ幾何・需給・時間帯のオン・オフ | def geo_enabled(name: str) -> bool: | ③向け直す |
| engine_tuner_exec.py | 230〜232 | 読む | indicator_switch_fingerprint | 印のハッシュ値 | def indicator_switch_fingerprint() -> str: | ③向け直す |
| engine_tuner_exec.py | 733〜744 | 読む | _check_param_range | 指標ごとのパラメータの範囲 | def _check_param_range(fam: str, param) -> None: | ③向け直す |
| engine_tuner_exec.py | 750〜792 | 読む | _check_num_range・_check_q_range | 数字・分位の範囲（指標に共通） | def _check_num_range(key: str, v, where: str) -> None: | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 1100〜1102 | 読む | _check_cond | レンジ幾何のうち、価格水準の列を拒否する | if kind == "geo" and iref.RANGE_GEO_REF[name]["kind"] != "ratio": | ③向け直す |
| engine_tuner_exec.py | 1289〜1339 | 読む | load_regime_laws | 法則の「機械が読む判定」（family・geo・側・系統・性質・本数） | def load_regime_laws(path: pathlib.Path ／ None = None) -> list: | ③向け直す |
| engine_tuner_exec.py | 1342〜1347 | 読む | _upper_tfs | 時間足の並び | def _upper_tfs() -> set: | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 1552 | 読む | REGIME_NAMES | 場面の名前 | from tuner_adapters import REGIME_NAMES | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 1812〜1828 | 読む | validate_recipe の G2 | 列ごとの補正後独立標本数 | used_cols = [] | ③向け直す |
| engine_tuner_exec.py | 1990〜2017 | 読む | _vnum_q | 分位の閾値（列ごと） | def _vnum_q(v: dict, qkey: str, qtable: dict ／ None, ctx: tuple ／ None = None): | ③向け直す |
| engine_tuner_exec.py | 2032〜2068 | 読む・作る | material_array | 指標の計算（その場で計算する） | def material_array(df: pd.DataFrame, full: str) -> np.ndarray: | ③向け直す |
| engine_tuner_exec.py | 2247〜2250 | 読む | touch の許容幅 | 定数 | if form == "touch": | ③向け直す |
| engine_tuner_exec.py | 2483〜2485・2503 | 読む | _ceiling_fire | 材料列（v35_range_top・rg5_uptrend） | if "v35_range_top" not in df.columns:                            # 今のレンジ開始以降の実測高値×(1−tol) | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 2676〜2683 | 読む | run_recipe | prepare_df の指標の列 | atr = df["atr"].to_numpy(float) | ③向け直す |
| engine_tuner_exec.py | 2756〜2757 | 読む | run_recipe | 記録用の指標（atr_entry・adx_entry・k_entry） | "atr_entry": atr[i], "adx_entry": adx[i], | ③向け直す |
| engine_tuner_exec.py | 3707 | 読む | box_tf | 時間足 | box_tf = ad.config()["global"]["box_tf"] | 外す（B・指標の情報ではない） |
| engine_tuner_exec.py | 3964〜3974 | 読む | _with_parts_cols | prepare_df の部品名 | def _with_parts_cols(d): | ③向け直す |
| engine_tuner_exec.py | 4541〜4542 | 読む | const_registry_live_check | 定数の表と実装の値の照らし | ng += iref.const_registry_live_check({"SCALP_FLOOR": e37.SCALP_FLOOR, "V11_SL_BUF": e37.V1 | ③向け直す |
| engine_tuner_exec.py | 5147 | 読む | selftest の需給 | 需給の元データの名前 | _dname = next(iter(_od9._DEMAND_FILES)) | 外す（B・指標の情報ではない） |
| engine_tuner_fire_diag.py | 84,106 | 読む | cond_label | 条件の形の性質の表 | if form in ex.NEST_FORMS: | 外す（B・指標の情報ではない） |
| engine_tuner_fire_diag.py | 101 | 読む | cond_label | 材料の名前を列の名前にする規則 | names = " と ".join(ex._mat_key(m, lane) for m in mats) if mats else "（材料なし）" | ③向け直す |
| engine_tuner_fire_diag.py | 209 | 読む | funnel_one | 場面の判定の列 | ok, up = ex._regime_series(df, recipe) | 外す（B・指標の情報ではない） |
| engine_tuner_fire_diag.py | 357 | 読む | run_main | 役割と件数/日の下限 | role, rfloor = tj.role_floor(a.strategy) | 外す（B・指標の情報ではない） |
| engine_tuner_fire_diag.py | 384,393,416,436-437 | 読む／作る | run_main | 材料の候補・時間足・材料の列・分位の一覧・分位から閾値を出す表 | pool, tfs, cat_total = gen.material_pool() | ③向け直す |
| gen_acceptance.py | 829-840 | 読む | _timeframe_rows | 使える時間足と、役割ごとの時間足 | def _timeframe_rows() -> list: | 振り分けが無い |
| gen_acceptance.py | 843-878 | 読む | _indicator_rows | 指標ごとのパラメータの名前・範囲（下限・上限・出どころ）・代表の値（スキャル／デイトレ）と出どころ・役割（出どころの役割・役割の印）・閾値の値・オンかオフか・カ | def _indicator_rows(text: str) -> list: | 振り分けが無い |
| gen_acceptance.py | 881-922 | 読む | _auto_rows | 法則（番号・場面・一文・説明・機械が読む判定）・型の id と name | def _auto_rows(no: str, lines: list, d: dict) -> list: | 振り分けが無い |
| gen_acceptance.py | 965-1028 | 読む | build_materials | オンの指標・geo_on・demand_on・time_on・役割ごとの系統と時間足とレンジ幾何・探す範囲の鍵 | def build_materials(d: dict) -> str: | 振り分けが無い |
| gen_acceptance.py | 1031-1077 | 読む | build_laws | 機械が読む判定の「数える部品」 | def build_laws(d: dict) -> str: | 振り分けが無い |
| gen_acceptance.py | 1080-1108 | 読む | build_ranking | 成績表の役割ごと・"強さ"・先読みの列の本数と、分離力の上位 | def build_ranking(d: dict) -> str: | 振り分けが無い |
| gen_acceptance.py | 1319-1361 | 読む | build_stages | §2.2 の段の材料（系統）・時間足・値の範囲 | def build_stages(d: dict) -> str: | 振り分けが無い |
| gen_audit_docs.py | 1655-1676 | 読む | _design_five_questions（Q2） | 設計書の 4-6・4-21・4-7 の表（指標・閾値・パラメータ・時間足の扱い）を依頼書へ写す | t46 = _md_tables(_md_sec(md, "4-6")) | 振り分けが無い |
| gen_audit_request.py | 286-318 | 読む | copy_all_laws | 法則の一覧 | def copy_all_laws() -> list[str]: | 振り分けが無い |
| gen_exit_families.py | 403-410 | 読む | confirm_conditions | 確認の条件の材料・閾値 | confirm_conditions=dict( | ③向け直す |
| gen_indicator_switch.py | 64-74 | 読む | `ta_classes` | ta のクラス | def ta_classes() -> list[tuple[str, str]]: | ②消す（プログラムごと無くなる） |
| gen_indicator_switch.py | 135-143 | 読む | `ta_map_approved` | 承認済みの対応 | def ta_map_approved() -> dict[str, set[str]]: | ②消す（プログラムごと無くなる） |
| gen_indicator_switch.py | 213-250 | 読む | `source_identity` | 恒等レシピの材料 | def source_identity() -> tuple[set[str], set[str]]: | ②消す（プログラムごと無くなる） |
| gen_indicator_table.py | 55-63 | 読む | `read_block` | INDICATOR_TABLE | def read_block(text: str) -> tuple[dict, int, int]: | ②消す（プログラムごと無くなる） |
| gen_indicator_table.py | 66-73 | 読む | `scan_rows` | `_r` の呼び出し | def scan_rows(text: str) -> list[dict]: | ②消す（プログラムごと無くなる） |
| gen_indicator_table.py | 192-209 | 読む | `counts` | 表の数 | def counts(table: dict) -> dict: | ②消す（プログラムごと無くなる） |
| gen_materials.py | 115 | 読む | `demand=od._DEMAND_FILES` | 需給の名前 | demand=list(od._DEMAND_FILES), tf_list=list(cfg["timeframes"])) | 振り分けが無い |
| gen_materials.py | 117-121 | 読む | geo_ok・time_ok・demand_ok | 別枠の部品 | extra = (_j.loads(_SIGFAM.read_text(encoding="utf-8")).get("extra_parts") or {}) | 振り分けが無い |
| gen_materials.py | 280-286 | 読む | `_lib_funcs` | ライブラリの関数とカテゴリ | def _lib_funcs() -> dict[str, str]: | 振り分けが無い |
| gen_materials.py | 289-300 | 読む | `_source_note` | 計算の出どころ・照合の相手 | def _source_note(fam: str, ext_ok: bool) -> str: | 振り分けが無い |
| gen_materials.py | 454-478 | 読む（AST） | `_catalog_keys` | パラメータの設定の鍵 | def _catalog_keys(od_src: str ／ None = None) -> set[str]: | 振り分けが無い |
| gen_materials.py | 778-839 | 読む | `forms_table` | 条件の形 | def forms_table() -> list[dict]: | 振り分けが無い |
| gen_materials.py | 1062-1139 | 読む | `_regime_decl_view` | 相場の判定の列 | def _regime_decl_view(names: tuple ／ None = None, decls: list ／ None = None, | 振り分けが無い |
| gen_observe_manual.py | 147-149 | 読む | _catalog_names | 指標の種類の名前 | def _catalog_names(cfg: dict) -> list[str]: | 振り分けが無い |
| gen_observe_manual.py | 153-159 | 読む | _mode_rows | 探索の系統 | """探索の系統ごとに（今オンか・名前・何を検証するロジックか・検証する値）を実体から取る。""" | 振り分けが無い |
| gen_observe_manual.py | 162-172 | 読む | _pair_cols | 玉と玉の間の特徴の列名 | def _pair_cols() -> list[str]: | 振り分けが無い |
| gen_observe_manual.py | 337-338 | 読む | build | 時間足と分位の数 | L.append(f"この{len(names)}種に、時間足{len(cfg['timeframes'])}種を掛けて " | 振り分けが無い |
| gen_observe_manual.py | 368,378 | 読む | build | 需給のデータ・場面の型 | for k in od._DEMAND_FILES: | 振り分けが無い |
| gen_observe_manual.py | 418-422 | 読む | build | 設定の全部の項目 | for k, v in cfg.items(): | 振り分けが無い |
| gen_regime_kb.py | 236-249 | 読む | coverage | 法則の「機械が読む判定」と「判定の置き場」 | def coverage(d: dict) -> tuple[int, list[str]]: | ③向け直す |
| gen_regime_kb.py | 1110-1205 | 読む／作る | expand_stage | 段ごとの役割・法則（law・law_or・law_width・law_tf）・指標名・系統・前処理（pre）・窓つきの前処理（pre_win＝op と mont | def expand_stage(stage_key: str ／ None = None) -> dict: | ③向け直す |
| gen_regime_kb.py | 1208-1263 | 読む | _actual_candidates | 実際の候補・オンかオフか・成績表の役割の列 | def _actual_candidates(stage_key: str) -> list: | ③向け直す |
| gen_s22_combi.py | 69-71 | 読む | laws_for_scene・_law_families | 法則が名指しする family | laws = gen.laws_for_scene("range") | 振り分けが無い |
| gen_s22_combi.py | 77-79 | 読む | load_signal_table()["tfs"] | 使える時間足 | table = gen.load_signal_table() | 振り分けが無い |
| gen_s22_combi.py | 85-94・:114-121 | 読む | groups・ranked_groups | 役割ごとの（family, tf）の組 | def groups(role, fams=None, tf_ok=None, label=None): | 振り分けが無い |
| gen_s22_combi.py | 106-115 | 読む（失敗する） | STAGES の import | 段1 の候補 | sys.path.insert(0, str(ROOT / ".claude" / "tools")) | 振り分けが無い |
| gen_signal_families.py | 53-62 | 読む | `_catalog` | 部品の名前・時間足 | def _catalog(): | ③向け直す |
| gen_signal_families.py | 999-1011 | 読む | 禁止3 の見本選び | 印のオン・オフ | import engine_tuner_exec as _ex_ban                      # 印の判定は実行器の1つの関数だけ（書き写さない） | ③向け直す |
| gen_signal_families.py | 1291-1305 | 読む | `_v9_indicators` | V9 の指標10種 | def _v9_indicators() -> list[str]: | ③向け直す |
| gen_stage0_match.py | 69-105 | 読む | load_stages | 段ごとの指標名・系統・レンジ幾何の列・真偽の列 | def load_stages() -> list: | 振り分けが無い |
| gen_stage0_match.py | 115-131 | 読む | columns_of・count_hits | 列名に、その文字が含まれるか | def columns_of(rank: dict, role: str) -> list: | 振り分けが無い |
| indicator_reference_diag.py | 28-49 | 読む | `_ta`・`_pta`・`_sps`、TA_OK・PTA_OK・SCIPY_OK | ext と ext2 で照らす相手 | try: | 外す（B・指標の情報ではない） |
| leak_causality_diag.py | 164-173 | 読む | load_features | 指標の列を付けたデータ | orig = e37.load_5m | 振り分けが無い |
| leak_causality_diag.py | 199-200,209 | 読む | run_e38_trades | 帯の1時間足の区切り（h1_edge）・前処理 | if cfg["global"]["regime"]["h1_edge"] != "right": | 振り分けが無い |
| leak_causality_diag.py | 207 | 読む | adaptive_k | 帯のパラメータ | adaptive_k = e37.V25_K if cfg["global"].get("regime", {}).get("v25_adaptive_band") else No | 振り分けが無い |
| leak_causality_diag.py | 323 | 読む | load_tuner_df | 指標の列を付けたデータ | (dfp,) = tuner.load_windows_cached(ad, [(s, e)], tuner.WARM, use_cache=False) | 振り分けが無い |
| leak_causality_diag.py | 337,344 | 読む | tuner_recipes | 材料の候補・時間足 | pool, _rej, _n = gen.material_pool() | 振り分けが無い |
| leak_causality_diag.py | 442-444,454 | 読む | tuner_check | 分位の一覧と、分位から閾値を出す表 | lm, _ = gen.load_limits() | 振り分けが無い |
| observe_diag.py | 115 | 読む | `import indicator_reference_diag as iref` | 照合・既知答え・定義表 | import indicator_reference_diag as iref   # noqa: E402 | ③向け直す |
| observe_diag.py | 203-224 | 読む | `load_config` | 時間足 | def load_config(path: str ／ None = None) -> dict: | ③向け直す |
| observe_diag.py | 709-712 | 読む | `_band_fee_floor` | 閾値（帯の、取れる距離の床） | def _band_fee_floor(cfg: dict ／ None = None) -> float: | 外す（B・指標の情報ではない） |
| observe_diag.py | 908-917 | 読む | `_pta6`・`_load_pta` | ライブラリとの対応 | _pta6 = None | 外す（B・指標の情報ではない） |
| observe_diag.py | 2214-2216 | 読む | 使われない material_params の検査 | パラメータ | _unused = sorted(set(_per) - _per_done) | ③向け直す |
| observe_diag.py | 2220-2228 | 読む | `drop_columns` | オン・オフ（同じ挙動の列を省く） | drop = {d: k for d, k in (cfg.get("drop_columns") or [])} | ③向け直す |
| observe_diag.py | 2326-2353 | 読む | `load_1m` | 前処理（1m・3m の元データ） | def load_1m(start, end, path: str ／ None = None) -> pd.DataFrame: | 外す（B・指標の情報ではない） |
| observe_diag.py | 2426-2448 | 読む | `load_demand` | 需給の指標3種 | def load_demand(bars_index, files: dict ／ None = None) -> tuple[pd.DataFrame, dict]: | ③向け直す |
| observe_diag.py | 2452-2456 | 読む | `_rg_zone_consts` | レンジ幾何のパラメータ | def _rg_zone_consts() -> tuple[float, int, int]: | ③向け直す |
| observe_diag.py | 2484-2526 | 読む | `_insp_range_geo` | 照合・既知答え | def _insp_range_geo(bars: pd.DataFrame, cfg: dict) -> list[str]: | ③向け直す |
| observe_diag.py | 2579-2580 | 読む | `rank_separation_independent` | 時間足 | tf = c.rsplit("__", 1)[1] if "__" in c else "5m" | 外す（B・指標の情報ではない） |
| observe_diag.py | 2933-2950 | 読む | `_one_side` の保有中のシグナル | 方向・閾値（分位） | names, mats, sig_dirs = [], [], [] | ③向け直す |
| observe_diag.py | 3419-3424 | 読む | `_scene_floor` | 閾値 | def _scene_floor(cfg) -> float: | 外す（B・指標の情報ではない） |
| observe_diag.py | 3427-3443 | 読む | `_scene_data` | 前処理・時間足の区切り | def _scene_data(cfg): | 外す（B・指標の情報ではない） |
| observe_diag.py | 3489-3511 | 読む | `_sk_zscore_short/long` | 指標（dev_z）と閾値 | if x["g"]["dev_z"] is None: | ③向け直す |
| observe_diag.py | 3540-3550 | 読む | `_grid_touch` | パラメータ | def _grid_touch(scene, x, up: bool): | ③向け直す |
| observe_diag.py | 3777-3869 | 読む | `_conf_search` | 区分・時間足・閾値（分位） | def _conf_search(sdf, feat_cols, cfg, first, second, base1, base2, d1, d2, floor): | ③向け直す |
| observe_diag.py | 3914-3925 | 読む | `plan_scene` | 区分 | cat = build_catalog(cfg) | ③向け直す |
| observe_diag.py | 4109・4132-4136 | 読む | `plan` | 種類の名前 | cat = build_catalog(cfg) | ③向け直す |
| observe_diag.py | 4510-4642 | 読む | `_insp_indicator_match` | 照合（ライブラリ ta・2つ目の照合・独立実装・既知答え・許容差・写しの印） | def _insp_indicator_match(bars: pd.DataFrame, cfg: dict, catalog: list ／ None = None) -> t | ③向け直す |
| observe_diag.py | 4645-4692 | 読む | `_insp_property` | 性質（trend／vol／それ以外） | def _insp_property(cfg: dict, catalog: list ／ None = None) -> tuple[set, dict]: | ③向け直す |
| observe_diag.py | 4773-4820 | 読む | `_insp_lookahead` | 列（名前__時間足）の作り方 | def _insp_lookahead(bars: pd.DataFrame, cfg: dict, catalog: list ／ None = None) -> list[st | ③向け直す |
| observe_diag.py | 4823-4831 | 読む | `_nominal_wlen` | パラメータの値（名前の文字から取る） | def _nominal_wlen(name: str, lead: int) -> int: | ③向け直す |
| observe_diag.py | 4834-4873 | 読む | `_insp_samples` | 列の名前の型 `f"{name}__{tf}"`・時間足 | def _insp_samples(bars: pd.DataFrame, cfg: dict, catalog: list ／ None = None) -> None: | ③向け直す |
| observe_diag.py | 4882-4958 | 読む | `_insp_demand` | 需給の定義・流儀・方向・出典 | def _insp_demand(bars: pd.DataFrame, files: dict ／ None = None) -> list[str]: | ③向け直す |
| observe_diag.py | 4961-4977 | 読む | `_insp_axis` | 軸カタログ E-c との対応表 | def _insp_axis(cfg: dict) -> list[str]: | ③向け直す |
| observe_diag.py | 5129-5155 | 読む | `_insp_v9_periods` | 設定の期間の一覧 | def _insp_v9_periods(cfg: dict, rows: list[dict] ／ None = None) -> list[str]: | ③向け直す |
| observe_diag.py | 5170-5230 | 読む | 検査13 `_price_scale_check` | カタログの全種（H6） | def _price_scale_check(bars: pd.DataFrame, cfg: dict, catalog: list ／ None = None, | ③向け直す |
| observe_diag.py | 5376-5399 | 読む | `_recipe_families` | レシピが使う family | def _recipe_families() -> set: | ③向け直す |
| observe_diag.py | 5485-5511 | 読む | `_dup_used_in_repo` | レシピ・設定で使っているか | def _dup_used_in_repo(name: str) -> int: | ③向け直す |
| observe_diag.py | 5514-5558 | 読む | `_dup_keep_of_group` | V9 か・レシピか・業界の関数の有無・暖機 | def _dup_keep_of_group(grp: list[str], warm: dict ／ None = None) -> tuple[str, str, str]: | ③向け直す |
| observe_diag.py | 5583-5627 | 読む | `_tol_saturation_cells`・`_insp_tol_saturation`（検査16） | S-R の帯の許容幅の上下限（閾値） | def _tol_saturation_cells(k, x) -> list: | ③向け直す |
| observe_diag.py | 5630-5742 | 読む | `inspect_data` | カタログを名前で絞る | def inspect_data(bars_csv: str, config_path: str ／ None = None, only: str ／ None = None, | ③向け直す |
| observe_diag.py | 5764-5809 | 読む | `_v9_preprocess_frame`・`_v9_price_kinds` | V9 の指標の列 | def _v9_preprocess_frame(bars: pd.DataFrame, calc_rows: int = 30000) -> tuple[pd.DataFrame | ③向け直す |
| observe_diag.py | 6682-6694 | 読む | `_independent_step` | 時間足の長さ | def _independent_step(tf: str, n: int) -> int: | 外す（B・指標の情報ではない） |
| regime_label.py | 46,61-81 | 読む | load_config | 正解ラベルの式の版と数字 | CONFIG = HERE / "recipes" / "regime_label.json" | 外す（B・指標の情報ではない） |
| regime_label.py | 84-87,313 | 読む | fee_floor | 手数料の床（帯の幅の基準に使う） | def fee_floor() -> float: | 外す（B・指標の情報ではない） |
| regime_r9_diag.py | 202-215 | 読む | _labels_for | 正解ラベル | def _labels_for(df_win: pd.DataFrame) -> dict: | 外す（B・指標の情報ではない） |
| regime_r9_diag.py | 228,260-263,269,299-302 | 読む／作る | measure・_qtable | レンジ幾何・需給の列・分位から閾値を出す表 | geo = g._geo_of(df) | ③向け直す |
| regime_r9_diag.py | 305-332 | 読む | print_stage_candidates | 段ごとの指標の候補 | def print_stage_candidates(stage: str) -> int: | ③向け直す |
| regime_r9_diag.py | 354-361 | 読む | _q50_width_cond | 帯の幅の条件 | def _q50_width_cond(limits) -> dict: | ③向け直す |
| regime_r9_diag.py | 364-398 | 読む／作る | _loosened_off | 分位を1段 緩めた閾値 | def _loosened_off(conds: list[dict], limits, frames: list ／ None = None) -> dict: | ③向け直す |
| regime_r9_diag.py | 550 | 読む | run_stage | 状態を保つ上限 | "保つ上限": int(g._nv_fixed(lm, "state_hold_bars_range", "n", j)["n"]), | 外す（B・指標の情報ではない） |
| regime_r9_diag.py | 568 | 読む | run_stage | 場面の法則の審査（G7） | ex._check_scene_rules({"name": "range", "build": g.strip_marks(bd)}, "") | ③向け直す |
| regime_r9_diag.py | 719-743 | 読む／作る | run_nan_check | 動く線の材料の前処理 | moving = [c for c in cands if c.get("pre_win")] | ③向け直す |
| regime_r9_diag.py | 1009 | 読む | main | 助走の長さ | _warm = g.stage_warm(et.WARM) | 外す（B・指標の情報ではない） |
| tuner_backcalc.py | 147-158 | 読む／自前で計算 | analyse ⑤ | 帯の幅の列名（2通り）と取り分の式 | # 帯幅の列名は戦略によって違う（E37 は box_W_pct_at_entry／レシピ実行器は W_entry）。 | 振り分けが無い |
| tuner_backcalc.py | 187 | 読む | analyse ⑦ | 枠の占有 | su = slot_usage(t, start, end) | 振り分けが無い |
| tuner_judgement.py | 131-168 | 読む | role_of・role_floor | 役割と件数/日の下限 | def role_of(strategy: str) -> str ／ None: | 外す（B・指標の情報ではない） |
| tuner_judgement.py | 354-453 | 読む／作る | neighbor_points | パラメータ・閾値の前後の点 | def neighbor_points(space_decl: dict, best: dict, rules: dict ／ None = None, | ③向け直す |

## 全部の行

| ファイル | 行 | 種類 | 中身 | 振り分け |
|---|---|---|---|---|
| analyze.py | 40 | 持つ | BANDS（名前 2・例 ADX, ATR%） | ①写す→②消す |
| analyze.py | 54 | 直書き | atr_14 | ③向け直す |
| analyze.py | 55 | 直書き | atr_14 | ③向け直す |
| analyze.py | 61 | 持つ | _NON_IND（名前 1・例 atr_14） | ①写す→②消す |
| analyze.py | 71 | 読む | _NON_IND | ③向け直す |
| analyze.py | 102 | 読む | BANDS | ③向け直す |
| analyze.py | 122 | 読む | BANDS | ③向け直す |
| analyze.py | 173 | 直書き | ADX | ③向け直す |
| analyze.py | 173 | 直書き | ATR% | ③向け直す |
| analyze.py | 173 | 直書き | ATR% | ③向け直す |
| analyze.py | 173 | 読む | BANDS | ③向け直す |
| analyze.py | 173 | 読む | BANDS | ③向け直す |
| analyze.py | 174 | 読む | BANDS | ③向け直す |
| analyze.py | 174 | 読む | BANDS | ③向け直す |
| analyze.py | 199 | 読む | BANDS | ③向け直す |
| check_indicator_sources.py | 36 | 読む | json の名前「.claude/ratchet/indicator_switch.json」 | ③向け直す |
| check_indicator_sources.py | 38 | 読む | json の名前「indicator_params_review.json」 | ③向け直す |
| check_indicator_sources.py | 38 | 読む | json の名前「indicator_params_review.json」 | ③向け直す |
| check_indicator_sources.py | 39 | 読む | json の名前「indicator_params_by_strategy.json」 | ③向け直す |
| check_indicator_sources.py | 39 | 読む | json の名前「indicator_params_by_strategy.json」 | ③向け直す |
| check_indicator_sources.py | 40 | 読む | json の名前「indicator_roles_thresholds.json」 | ③向け直す |
| check_indicator_sources.py | 40 | 読む | json の名前「indicator_roles_thresholds.json」 | ③向け直す |
| check_indicator_sources.py | 42 | 読む | json の名前「scripts/priority_rebuild/observe_config.json」 | ③向け直す |
| check_indicator_sources.py | 43 | 読む | json の名前「scripts/priority_rebuild/recipes/search_limits.json」 | ③向け直す |
| check_indicator_sources.py | 96 | 読む | json の名前「observe_config.json の material_params〜_material_params_pendi」 | ③向け直す |
| check_indicator_sources.py | 97 | 読む | json の名前「observe_config.json の material_params の塊」 | ③向け直す |
| check_indicator_sources.py | 99 | 読む | json の名前「search_limits.json の material_param_ranges」 | ③向け直す |
| check_indicator_sources.py | 100 | 読む | json の名前「search_limits.json の material_param_ranges の塊」 | ③向け直す |
| count_builder_literals.py | 51 | 読む | json の名前「regime_laws.json」 | ③向け直す |
| e38.py | 248 | 自前で計算 | pct_change | ③向け直す |
| e38_logic_parts.py | 48 | 自前で計算 | ewm | ③向け直す |
| e38_logic_parts.py | 49 | 自前で計算 | ewm | ③向け直す |
| e38_logic_parts.py | 50 | 自前で計算 | ewm | ③向け直す |
| e38_logic_parts.py | 52 | 自前で計算 | ewm | ③向け直す |
| e38_logic_parts.py | 61 | 自前で計算 | rolling | ③向け直す |
| e38_logic_parts.py | 62 | 自前で計算 | rolling | ③向け直す |
| e38_logic_parts.py | 74 | 直書き | e38_htf_roc24_2h | ③向け直す |
| e38_logic_parts.py | 74 | 自前で計算 | pct_change | ③向け直す |
| e38_logic_parts.py | 75 | 自前で計算 | ewm | ③向け直す |
| e38_logic_parts.py | 75 | 自前で計算 | ewm | ③向け直す |
| e38_logic_parts.py | 78 | 直書き | e38_htf_di7_4h | ③向け直す |
| e38_logic_parts.py | 80 | 直書き | e38_htf_adx14_2h | ③向け直す |
| e38_logic_parts.py | 81 | 自前で計算 | rolling | ③向け直す |
| e38_logic_parts.py | 82 | 自前で計算 | rolling | ③向け直す |
| e38_logic_parts.py | 82 | 自前で計算 | rolling | ③向け直す |
| e38_logic_parts.py | 83 | 直書き | e38_htf_stochd14_2h | ③向け直す |
| e38_logic_parts.py | 83 | 自前で計算 | rolling | ③向け直す |
| e38_logic_parts.py | 84 | 直書き | e38_vol_volr20_15m | ③向け直す |
| e38_logic_parts.py | 84 | 自前で計算 | rolling | ③向け直す |
| e38_logic_parts.py | 85 | 直書き | e38_vol_volr50_15m | ③向け直す |
| e38_logic_parts.py | 85 | 自前で計算 | rolling | ③向け直す |
| e38_logic_parts.py | 86 | 自前で計算 | rolling | ③向け直す |
| e38_logic_parts.py | 86 | 自前で計算 | rolling | ③向け直す |
| e38_logic_parts.py | 87 | 直書き | e38_vol_donch20_1d | ③向け直す |
| e38_logic_parts.py | 87 | 自前で計算 | rolling | ③向け直す |
| e38_logic_parts.py | 87 | 自前で計算 | rolling | ③向け直す |
| enforce_g2_pass.py | 51 | 読む | json の名前「/signal_families.json」 | ③向け直す |
| enforce_g2_pass.py | 304 | 読む | json の名前「/signal_families.json」 | ③向け直す |
| enforce_g2_pass.py | 367 | 読む | json の名前「/signal_families.json」 | ③向け直す |
| engine_tuner_exec.py | 162 | 読む | json の名前「indicator_switch.json」 | ③向け直す |
| engine_tuner_exec.py | 265 | 読む | REFS | ③向け直す |
| engine_tuner_exec.py | 275 | 読む | FAMILY_TEMPLATES | ③向け直す |
| engine_tuner_exec.py | 289 | 持つ | RUNTIME_ALIAS（名前 7・例 e38_htf_adx14_2h, e38_htf_di7_4h, e38_htf_roc24_2h） | ①写す→②消す |
| engine_tuner_exec.py | 524 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 527 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 532 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 536 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 540 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 541 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 602 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 623 | 読む | json の名前「／正本＝condition_parts.json）」 | ③向け直す |
| engine_tuner_exec.py | 664 | 読む | json の名前「 は、指標のオン・オフの印で「使わない」になっている（印＝indicator_switch.json の geo_on・」 | ③向け直す |
| engine_tuner_exec.py | 678 | 読む | json の名前「 は、指標のオン・オフの印で「使わない」になっている（印＝indicator_switch.json の time_on」 | ③向け直す |
| engine_tuner_exec.py | 689 | 読む | json の名前「 は、指標のオン・オフの印で「使わない」になっている（印＝indicator_switch.json の demand_」 | ③向け直す |
| engine_tuner_exec.py | 704 | 読む | json の名前「 は、指標のオン・オフの印で「使わない」になっている（印＝indicator_switch.json の on・作り直し」 | ③向け直す |
| engine_tuner_exec.py | 730 | 読む | json の名前「・recipes/search_limits.json の int_range）」 | ③向け直す |
| engine_tuner_exec.py | 850 | 読む | CONST_REGISTRY | ③向け直す |
| engine_tuner_exec.py | 1049 | 読む | json の名前「／正本＝condition_parts.json）」 | ③向け直す |
| engine_tuner_exec.py | 1186 | 読む | json の名前「向きを持たない部品の一覧（型の表 signal_families.json の bans が正本＝2026-08-06 」 | ③向け直す |
| engine_tuner_exec.py | 1198 | 読む | json の名前「regime_laws.json」 | ③向け直す |
| engine_tuner_exec.py | 1210 | 持つ | _REFS_PROP（名前が定義の表） | ①写す→②消す |
| engine_tuner_exec.py | 1216 | 読む | _REFS_PROP | ③向け直す |
| engine_tuner_exec.py | 1217 | 持つ | _REFS_PROP（名前が定義の表） | ①写す→②消す |
| engine_tuner_exec.py | 1219 | 読む | _REFS_PROP | ③向け直す |
| engine_tuner_exec.py | 1242 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_exec.py | 1396 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_exec.py | 1480 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_exec.py | 1487 | 読む | json の名前「G7＝場面ごとの相場の法則（正本＝regime_laws.json の「機械が読む判定」・M2-B0・2026-08-3」 | ③向け直す |
| engine_tuner_exec.py | 1542 | 読む | json の名前「（正本＝regime_laws.json の「機械が読む判定」・M2-B0 まこさん承認 2026-08-30）」 | ③向け直す |
| engine_tuner_exec.py | 1786 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_exec.py | 1797 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_exec.py | 1797 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_exec.py | 1983 | 読む | CONST_REGISTRY | ③向け直す |
| engine_tuner_exec.py | 2097 | 読む | RUNTIME_ALIAS | ③向け直す |
| engine_tuner_exec.py | 2170 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 2182 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 2217 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 2479 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 2702 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 2702 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 2729 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 3004 | 読む | json の名前「identity_s2_legacy.json」 | ③向け直す |
| engine_tuner_exec.py | 3049 | 直書き | e38_htf_roc24_2h | ③向け直す |
| engine_tuner_exec.py | 3049 | 直書き | e38_vol_volr20_15m | ③向け直す |
| engine_tuner_exec.py | 3400 | 読む | json の名前「identity_s1_legacy.json」 | ③向け直す |
| engine_tuner_exec.py | 3447 | 自前で計算 | ewm | ③向け直す |
| engine_tuner_exec.py | 3448 | 自前で計算 | ewm | ③向け直す |
| engine_tuner_exec.py | 3449 | 自前で計算 | ewm | ③向け直す |
| engine_tuner_exec.py | 3450 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 3450 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 3467 | 自前で計算 | ewm | ③向け直す |
| engine_tuner_exec.py | 3468 | 自前で計算 | ewm | ③向け直す |
| engine_tuner_exec.py | 3473 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 3473 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 3830 | 直書き | Stoch%K | ③向け直す |
| engine_tuner_exec.py | 3831 | 直書き | Stoch%D | ③向け直す |
| engine_tuner_exec.py | 3833 | 直書き | RSI | ③向け直す |
| engine_tuner_exec.py | 3835 | 直書き | volume_ratio | ③向け直す |
| engine_tuner_exec.py | 3839 | 直書き | ADX | ③向け直す |
| engine_tuner_exec.py | 3841 | 直書き | ROC | ③向け直す |
| engine_tuner_exec.py | 4043 | 直書き | RSI | ③向け直す |
| engine_tuner_exec.py | 4043 | 直書き | RSI | ③向け直す |
| engine_tuner_exec.py | 4043 | 読む | FAMILY_TEMPLATES | ③向け直す |
| engine_tuner_exec.py | 4043 | 読む | FAMILY_TEMPLATES | ③向け直す |
| engine_tuner_exec.py | 4044 | 読む | FAMILY_TEMPLATES | ③向け直す |
| engine_tuner_exec.py | 4046 | 読む | FAMILY_TEMPLATES | ③向け直す |
| engine_tuner_exec.py | 4051 | 読む | FAMILY_TEMPLATES | ③向け直す |
| engine_tuner_exec.py | 4251 | 直書き | RSI | ③向け直す |
| engine_tuner_exec.py | 4257 | 直書き | RSI | ③向け直す |
| engine_tuner_exec.py | 4259 | 直書き | RSI | ③向け直す |
| engine_tuner_exec.py | 4270 | 直書き | RSI | ③向け直す |
| engine_tuner_exec.py | 4318 | 直書き | Stoch%K | ③向け直す |
| engine_tuner_exec.py | 4319 | 直書き | Stoch%D | ③向け直す |
| engine_tuner_exec.py | 4325 | 直書き | ROC | ③向け直す |
| engine_tuner_exec.py | 4333 | 直書き | RSI | ③向け直す |
| engine_tuner_exec.py | 4345 | 直書き | ROC | ③向け直す |
| engine_tuner_exec.py | 4353 | 直書き | ATR% | ③向け直す |
| engine_tuner_exec.py | 4357 | 直書き | ATR% | ③向け直す |
| engine_tuner_exec.py | 4359 | 直書き | ATR% | ③向け直す |
| engine_tuner_exec.py | 4447 | 直書き | RSI | ③向け直す |
| engine_tuner_exec.py | 4524 | 持つ | bandc（名前 1・例 RSI） | ①写す→②消す |
| engine_tuner_exec.py | 4527 | 読む | bandc | ③向け直す |
| engine_tuner_exec.py | 4529 | 読む | bandc | ③向け直す |
| engine_tuner_exec.py | 4532 | 読む | bandc | ③向け直す |
| engine_tuner_exec.py | 4536 | 持つ | slc（名前 1・例 RSI） | ①写す→②消す |
| engine_tuner_exec.py | 4538 | 読む | slc | ③向け直す |
| engine_tuner_exec.py | 4606 | 読む | FAMILY_TEMPLATES | ③向け直す |
| engine_tuner_exec.py | 4774 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_exec.py | 4789 | 持つ | _st_lvl（名前 1・例 RSI） | ①写す→②消す |
| engine_tuner_exec.py | 4793 | 読む | _st_lvl | ③向け直す |
| engine_tuner_exec.py | 4795 | 読む | _st_lvl | ③向け直す |
| engine_tuner_exec.py | 4798 | 読む | _st_lvl | ③向け直す |
| engine_tuner_exec.py | 4798 | 読む | _st_lvl | ③向け直す |
| engine_tuner_exec.py | 4800 | 読む | _st_lvl | ③向け直す |
| engine_tuner_exec.py | 4804 | 読む | _st_lvl | ③向け直す |
| engine_tuner_exec.py | 4814 | 読む | _st_lvl | ③向け直す |
| engine_tuner_exec.py | 4842 | 直書き | BB幅 | ③向け直す |
| engine_tuner_exec.py | 4843 | 直書き | BB幅 | ③向け直す |
| engine_tuner_exec.py | 4844 | 持つ | _g7_struct（名前 1・例 S-Rタッチ数） | ①写す→②消す |
| engine_tuner_exec.py | 4847 | 直書き | DI差 | ③向け直す |
| engine_tuner_exec.py | 4848 | 直書き | DI差 | ③向け直す |
| engine_tuner_exec.py | 4849 | 直書き | DI差 | ③向け直す |
| engine_tuner_exec.py | 4850 | 直書き | DI差 | ③向け直す |
| engine_tuner_exec.py | 4851 | 直書き | ADX | ③向け直す |
| engine_tuner_exec.py | 4852 | 直書き | ADX | ③向け直す |
| engine_tuner_exec.py | 4853 | 直書き | ADX | ③向け直す |
| engine_tuner_exec.py | 4861 | 直書き | BB幅 | ③向け直す |
| engine_tuner_exec.py | 4863 | 持つ | _g7_struct5m（名前 1・例 S-Rタッチ数） | ①写す→②消す |
| engine_tuner_exec.py | 4866 | 直書き | ATR% | ③向け直す |
| engine_tuner_exec.py | 4867 | 読む | _g7_struct | ③向け直す |
| engine_tuner_exec.py | 4877 | 読む | _g7_struct | ③向け直す |
| engine_tuner_exec.py | 4879 | 読む | _g7_struct | ③向け直す |
| engine_tuner_exec.py | 4883 | 読む | _g7_struct | ③向け直す |
| engine_tuner_exec.py | 4885 | 読む | _g7_struct5m | ③向け直す |
| engine_tuner_exec.py | 4887 | 読む | _g7_struct | ③向け直す |
| engine_tuner_exec.py | 4889 | 読む | _g7_struct | ③向け直す |
| engine_tuner_exec.py | 4891 | 読む | _g7_struct | ③向け直す |
| engine_tuner_exec.py | 4895 | 読む | _g7_struct | ③向け直す |
| engine_tuner_exec.py | 4897 | 読む | _g7_struct | ③向け直す |
| engine_tuner_exec.py | 4971 | 直書き | ADX | ③向け直す |
| engine_tuner_exec.py | 4971 | 直書き | ADX | ③向け直す |
| engine_tuner_exec.py | 4973 | 直書き | ADX | ③向け直す |
| engine_tuner_exec.py | 5014 | 持つ | _xm14（名前 1・例 RSI） | ①写す→②消す |
| engine_tuner_exec.py | 5015 | 持つ | _xm7（名前 1・例 RSI） | ①写す→②消す |
| engine_tuner_exec.py | 5036 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5037 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5043 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5043 | 読む | _xm7 | ③向け直す |
| engine_tuner_exec.py | 5052 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5052 | 読む | _xm7 | ③向け直す |
| engine_tuner_exec.py | 5065 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5076 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5089 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5090 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5092 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5092 | 読む | _xm7 | ③向け直す |
| engine_tuner_exec.py | 5112 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5114 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5115 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5115 | 読む | _xm7 | ③向け直す |
| engine_tuner_exec.py | 5117 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5118 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5118 | 読む | _xm7 | ③向け直す |
| engine_tuner_exec.py | 5119 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5122 | 読む | _xm14 | ③向け直す |
| engine_tuner_exec.py | 5124 | 読む | _xm14 | ③向け直す |
| engine_tuner_fire_diag.py | 361 | 読む | json の名前「[発火の関門] 走らせられない＝search_limits.json の値がまこさん待ち:」 | ③向け直す |
| engine_tuner_fire_diag.py | 426 | 読む | RUNTIME_ALIAS | ③向け直す |
| engine_tuner_gen.py | 47 | 読む | json の名前「search_limits.json」 | ③向け直す |
| engine_tuner_gen.py | 215 | 読む | FAMILY_TEMPLATES | ③向け直す |
| engine_tuner_gen.py | 382 | 読む | json の名前「使える時間足の全部（observe_config.json の timeframes）。1回だけ読む。」 | ③向け直す |
| engine_tuner_gen.py | 759 | 読む | json の名前「（indicator_switch.json・M2-C-2）」 | ③向け直す |
| engine_tuner_gen.py | 823 | 読む | json の名前「（indicator_switch.json の geo_on）」 | ③向け直す |
| engine_tuner_gen.py | 830 | 読む | json の名前「（indicator_switch.json の demand_on）」 | ③向け直す |
| engine_tuner_gen.py | 837 | 読む | json の名前「（indicator_switch.json の time_on）」 | ③向け直す |
| engine_tuner_gen.py | 1035 | 読む | json の名前「[本数の範囲エラー] int_range も int_grid も無い（recipes/search_limits.js」 | ③向け直す |
| engine_tuner_gen.py | 1073 | 読む | json の名前「 も無い（recipes/search_limits.json）」 | ③向け直す |
| engine_tuner_gen.py | 1078 | 読む | json の名前「 より小さい（recipes/search_limits.json）」 | ③向け直す |
| engine_tuner_gen.py | 1149 | 読む | json の名前「[分位の範囲エラー] quantile_range も quantile_grid も無い（recipes/search」 | ③向け直す |
| engine_tuner_gen.py | 1158 | 読む | json の名前「 より小さい（recipes/search_limits.json の quantile_range）」 | ③向け直す |
| engine_tuner_gen.py | 1183 | 読む | json の名前「 の書き方が違う（q と整数＝例 q37・recipes/search_limits.json の quantile_r」 | ③向け直す |
| engine_tuner_gen.py | 1188 | 読む | json の名前「・recipes/search_limits.json の quantile_range）」 | ③向け直す |
| engine_tuner_gen.py | 1198 | 読む | json の名前「・recipes/search_limits.json の 」 | ③向け直す |
| engine_tuner_gen.py | 1200 | 読む | json の名前「 は整数でない（範囲は整数・recipes/search_limits.json の 」 | ③向け直す |
| engine_tuner_gen.py | 1225 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 1270 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 1348 | 読む | json の名前「material_ranking.json」 | ③向け直す |
| engine_tuner_gen.py | 1356 | 読む | json の名前「[材料の順位] material_ranking.json が無い（observe_diag.py --rank-reg」 | ③向け直す |
| engine_tuner_gen.py | 1607 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 1707 | 読む | json の名前「出る線（off）の分位＝入る線（on）より緩い側を、分位の範囲の中から引く（法則 C6 の②）。

    above（」 | ③向け直す |
| engine_tuner_gen.py | 1854 | 読む | CONST_REGISTRY | ③向け直す |
| engine_tuner_gen.py | 1890 | 持つ | _EXIT_LEVEL_CONST（名前 4・例 ADX, RSI, Stoch%D） | ①写す→②消す |
| engine_tuner_gen.py | 1908 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 1949 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 1961 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 1963 | 直書き | Stoch%D | ③向け直す |
| engine_tuner_gen.py | 1963 | 直書き | Stoch%K | ③向け直す |
| engine_tuner_gen.py | 1966 | 直書き | Stoch%D | ③向け直す |
| engine_tuner_gen.py | 1966 | 直書き | Stoch%K | ③向け直す |
| engine_tuner_gen.py | 1982 | 読む | _EXIT_LEVEL_CONST | ③向け直す |
| engine_tuner_gen.py | 2031 | 読む | CONST_REGISTRY | ③向け直す |
| engine_tuner_gen.py | 2239 | 読む | FAMILY_TEMPLATES | ③向け直す |
| engine_tuner_gen.py | 2343 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 2345 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 2426 | 読む | json の名前「 に掛かる相場の法則が1件も無い（regime_laws.json・fail-closed）」 | ③向け直す |
| engine_tuner_gen.py | 2475 | 読む | json の名前「m2_stage_candidates.json」 | ③向け直す |
| engine_tuner_gen.py | 2892 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 2894 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 2905 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 3043 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 3051 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 3091 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 3093 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 3095 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 3135 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 3137 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 3331 | 読む | json の名前「 が系統を名指ししていない（regime_laws.json・fail-closed）」 | ③向け直す |
| engine_tuner_gen.py | 3404 | 読む | json の名前「C6（hysteresis の形）が法則に無い（regime_laws.json・fail-closed）」 | ③向け直す |
| engine_tuner_gen.py | 3406 | 読む | json の名前「（not の形）が法則に無い（regime_laws.json・fail-closed）」 | ③向け直す |
| engine_tuner_gen.py | 3451 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 3876 | 読む | RUNTIME_ALIAS | ③向け直す |
| engine_tuner_gen.py | 3970 | 読む | RUNTIME_ALIAS | ③向け直す |
| engine_tuner_gen.py | 4062 | 直書き | atr_14 | ③向け直す |
| engine_tuner_gen.py | 4892 | 自前で計算 | rolling | ③向け直す |
| engine_tuner_gen.py | 4899 | 直書き | e38_htf_roc24_2h | ③向け直す |
| engine_tuner_gen.py | 4899 | 直書き | e38_vol_volr20_15m | ③向け直す |
| engine_tuner_gen.py | 5000 | 持つ | fake（区分の言葉 2（例 向き, 強さ）） | ①写す→②消す |
| engine_tuner_gen.py | 5006 | 読む | fake | ③向け直す |
| engine_tuner_gen.py | 5359 | 直書き | Stoch%K | ③向け直す |
| engine_tuner_gen.py | 5362 | 持つ | _want5（名前 16・例 DI+, DI-, FISHER） | ①写す→②消す |
| engine_tuner_gen.py | 5365 | 読む | _want5 | ③向け直す |
| engine_tuner_gen.py | 5368 | 直書き | ADX | ③向け直す |
| engine_tuner_gen.py | 5368 | 直書き | RSI | ③向け直す |
| engine_tuner_gen.py | 5403 | 直書き | RSI | ③向け直す |
| engine_tuner_gen.py | 5545 | 直書き | RSI | ③向け直す |
| engine_tuner_gen.py | 5553 | 直書き | RSI | ③向け直す |
| engine_tuner_gen.py | 5566 | 直書き | RSI | ③向け直す |
| engine_tuner_gen.py | 5567 | 直書き | RSI | ③向け直す |
| engine_tuner_gen.py | 5711 | 直書き | atr_14 | ③向け直す |
| engine_tuner_gen.py | 5716 | 直書き | atr_14 | ③向け直す |
| engine_tuner_gen.py | 5860 | 読む | json の名前「T7: いまの search_limits.json に値待ちが残っている＝本走は始められない: 」 | ③向け直す |
| engine_tuner_gen.py | 5975 | 読む | RUNTIME_ALIAS | ③向け直す |
| engine_tuner_gen.py | 5987 | 持つ | rec11（名前 1・例 ADX） | ①写す→②消す |
| engine_tuner_gen.py | 5997 | 読む | rec11 | ③向け直す |
| engine_tuner_gen.py | 6120 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 6537 | 読む | RUNTIME_ALIAS | ③向け直す |
| engine_tuner_gen.py | 6587 | 持つ | _r22（名前 4・例 ADX, DI差, ROC） | ①写す→②消す |
| engine_tuner_gen.py | 6597 | 読む | _r22 | ③向け直す |
| engine_tuner_gen.py | 6604 | 読む | _r22 | ③向け直す |
| engine_tuner_gen.py | 6613 | 持つ | _r22c（名前 2・例 ATR%, fractal安値距離%） | ①写す→②消す |
| engine_tuner_gen.py | 6618 | 読む | _r22c | ③向け直す |
| engine_tuner_gen.py | 6622 | 読む | _r22c | ③向け直す |
| engine_tuner_gen.py | 6638 | 持つ | _r22e（名前 1・例 RSI） | ①写す→②消す |
| engine_tuner_gen.py | 6643 | 読む | _r22e | ③向け直す |
| engine_tuner_gen.py | 6845 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 6847 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 6854 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 6871 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 7471 | 直書き | DI差 | ③向け直す |
| engine_tuner_gen.py | 7478 | 直書き | DI差 | ③向け直す |
| engine_tuner_gen.py | 7524 | 直書き | BB幅 | ③向け直す |
| engine_tuner_gen.py | 7531 | 直書き | BB幅 | ③向け直す |
| engine_tuner_gen.py | 7731 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 7733 | 読む | FAMILY_LINEAGE | ③向け直す |
| engine_tuner_gen.py | 8100 | 読む | json の名前「[歩4 本走] 走らせられない＝search_limits.json の値がまこさん待ち:」 | ③向け直す |
| engine_tuner_gen.py | 8109 | 読む | json の名前「 から決めた（設定 recipes/search_limits.json の hold_range_by_role が正」 | ③向け直す |
| engine_tuner_gen.py | 8317 | 読む | json の名前「[歩4] 本走はまだ始められない＝search_limits.json の値がまこさん待ち:」 | ③向け直す |
| engine_tuner_gen.py | 8444 | 読む | FAMILY_LINEAGE | ③向け直す |
| gen_acceptance.py | 150 | 読む | json の名前「indicator_switch.json」 | ③向け直す |
| gen_acceptance.py | 151 | 読む | json の名前「regime_laws.json」 | ③向け直す |
| gen_acceptance.py | 152 | 読む | json の名前「signal_families.json」 | ③向け直す |
| gen_acceptance.py | 153 | 読む | json の名前「material_ranking.json」 | ③向け直す |
| gen_acceptance.py | 154 | 読む | json の名前「search_limits.json」 | ③向け直す |
| gen_acceptance.py | 525 | 読む | json の名前「materials.json」 | ③向け直す |
| gen_acceptance.py | 527 | 読む | json の名前「indicator_params_by_strategy.json」 | ③向け直す |
| gen_acceptance.py | 528 | 読む | json の名前「indicator_roles_thresholds.json」 | ③向け直す |
| gen_acceptance.py | 533 | 読む | json の名前「observe_config.json」 | ③向け直す |
| gen_acceptance.py | 813 | 読む | json の名前「承認済みの型の表（signal_families.json の parts）に部品が在る、指標の種類。
    部品の名」 | ③向け直す |
| gen_acceptance.py | 1673 | 読む | json の名前「scripts/priority_rebuild/observe_config.json」 | ③向け直す |
| gen_acceptance.py | 1673 | 読む | json の名前「scripts/priority_rebuild/recipes/search_limits.json」 | ③向け直す |
| gen_acceptance.py | 3054 | 直書き | ADX | ③向け直す |
| gen_acceptance.py | 3059 | 直書き | ADX | ③向け直す |
| gen_acceptance.py | 3060 | 直書き | POC | ③向け直す |
| gen_acceptance.py | 3063 | 直書き | ADX | ③向け直す |
| gen_acceptance.py | 3063 | 直書き | POC | ③向け直す |
| gen_acceptance.py | 3063 | 直書き | 前日POC | ③向け直す |
| gen_audit_docs.py | 3097 | 読む | json の名前「scripts/priority_rebuild/observe_config.json」 | ③向け直す |
| gen_audit_request.py | 169 | 読む | json の名前「signal_families.json」 | ③向け直す |
| gen_audit_request.py | 496 | 持つ | _REF_MD_RE（名前が定義の表） | ①写す→②消す |
| gen_audit_request.py | 497 | 持つ | _REF_SEC_RE（名前が定義の表） | ①写す→②消す |
| gen_audit_request.py | 513 | 読む | _REF_MD_RE | ③向け直す |
| gen_audit_request.py | 514 | 読む | _REF_SEC_RE | ③向け直す |
| gen_composition_rules.py | 62 | 読む | json の名前「signal_families.json」 | ③向け直す |
| gen_composition_rules.py | 63 | 読む | json の名前「search_limits.json」 | ③向け直す |
| gen_composition_rules.py | 64 | 読む | json の名前「exit_families.json」 | ③向け直す |
| gen_composition_rules.py | 65 | 読む | json の名前「composition_rules.json」 | ③向け直す |
| gen_composition_rules.py | 74 | 読む | json の名前「v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/comp」 | ③向け直す |
| gen_composition_rules.py | 101 | 読む | FAMILY_LINEAGE | ③向け直す |
| gen_composition_rules.py | 208 | 読む | json の名前「signal_families.json」 | ③向け直す |
| gen_composition_rules.py | 209 | 読む | json の名前「search_limits.json」 | ③向け直す |
| gen_composition_rules.py | 210 | 読む | json の名前「exit_families.json」 | ③向け直す |
| gen_composition_rules.py | 238 | 読む | json の名前「> - 同じ説明文に「`composition_rules.json` … **engine_tuner が読む完成品*」 | ③向け直す |
| gen_composition_rules.py | 254 | 読む | json の名前「## ★場面ごとの読み込ませる法則は、このファイルから regime_laws.json へ移した（M2-B0・2026」 | ③向け直す |
| gen_composition_rules.py | 273 | 読む | json の名前「[未生成] composition_rules.json が無い（--write で作る）」 | ③向け直す |
| gen_composition_rules.py | 276 | 読む | json の名前「[改変] composition_rules.json の本文が手で書き換えられている」 | ③向け直す |
| gen_composition_rules.py | 328 | 読む | json の名前「signal_families.json」 | ③向け直す |
| gen_composition_rules.py | 338 | 読む | json の名前「T7: composition_rules_src.json に scene_rules が戻っている＝M2-B0（まこ」 | ③向け直す |
| gen_composition_rules.py | 352 | 読む | json の名前「regime_laws.json」 | ③向け直す |
| gen_composition_rules.py | 356 | 読む | json の名前「T10: 移した7件（C1・C4・C6・R1・R8・R7・S1）の「機械が読む判定」が regime_laws.json」 | ③向け直す |
| gen_composition_rules.py | 396 | 読む | json の名前「  場面ごとの法則＝regime_laws.json の「機械が読む判定」へ移した（M2-B0・2026-08-30）」 | ③向け直す |
| gen_decisions.py | 80 | 読む | json の名前「observe_config.json」 | ③向け直す |
| gen_decisions.py | 102 | 読む | json の名前「行から飾りを落として1文にする（表・箇条書き・JSON の記号を外す）。

    at＝印（まこさん確定 等）が行のど」 | ③向け直す |
| gen_exit_families.py | 43 | 読む | json の名前「.claude/ratchet/signal_families.json」 | ③向け直す |
| gen_exit_families.py | 44 | 読む | json の名前「.claude/ratchet/exit_families_rules.json」 | ③向け直す |
| gen_exit_families.py | 45 | 読む | json の名前「recipes/search_limits.json」 | ③向け直す |
| gen_exit_families.py | 53 | 読む | json の名前「v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/exit」 | ③向け直す |
| gen_exit_families.py | 58 | 読む | json の名前「.claude/ratchet/exit_families.json」 | ③向け直す |
| gen_exit_families.py | 182 | 読む | FAMILY_TEMPLATES | ③向け直す |
| gen_exit_families.py | 393 | 読む | json の名前「signal_families.json（入口の型の表＝確認条件の材料と禁止3 を共有）」 | ③向け直す |
| gen_exit_families.py | 394 | 読む | json の名前「recipes/search_limits.json（まこさん承認 2026-08-01）」 | ③向け直す |
| gen_exit_families.py | 587 | 読む | json の名前「出口の表（exit_families.json）が無い」 | ③向け直す |
| gen_indicator_switch.py | 46 | 読む | json の名前「.claude/ratchet/regime_laws.json」 | ③向け直す |
| gen_indicator_switch.py | 47 | 読む | json の名前「recipes/identity_s1_legacy.json」 | ③向け直す |
| gen_indicator_switch.py | 48 | 読む | json の名前「recipes/identity_s2_legacy.json」 | ③向け直す |
| gen_indicator_switch.py | 50 | 読む | json の名前「.claude/ratchet/indicator_switch.json」 | ③向け直す |
| gen_indicator_switch.py | 54 | 読む | json の名前「v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/indi」 | ③向け直す |
| gen_indicator_switch.py | 80 | 読む | REFS | ③向け直す |
| gen_indicator_switch.py | 89 | 読む | REFS | ③向け直す |
| gen_indicator_switch.py | 207 | 読む | FAMILY_LINEAGE | ③向け直す |
| gen_indicator_switch.py | 209 | 読む | REFS | ③向け直す |
| gen_indicator_switch.py | 269 | 読む | REFS | ③向け直す |
| gen_indicator_switch.py | 315 | 読む | json の名前「regime_laws.json の「機械が読む判定」の family と geo」 | ③向け直す |
| gen_indicator_table.py | 45 | 読む | json の名前「indicator_roles_thresholds.json」 | ③向け直す |
| gen_indicator_table.py | 46 | 読む | json の名前「indicator_review/r1_role_map.json」 | ③向け直す |
| gen_indicator_table.py | 49 | 持つ | CAT2LIN（区分の言葉 11（例 オシレーター, トレンド, ボラ）） | ①写す→②消す |
| gen_indicator_table.py | 51 | 持つ | HOUKOU2PROP（区分の言葉 8（例 none, reversal, trend）） | ①写す→②消す |
| gen_indicator_table.py | 94 | 読む | REFS | ③向け直す |
| gen_indicator_table.py | 106 | 読む | json の名前「R-1（封つき r1_role_map.json・」 | ③向け直す |
| gen_indicator_table.py | 124 | 読む | CAT2LIN | ③向け直す |
| gen_indicator_table.py | 124 | 読む | CAT2LIN | ③向け直す |
| gen_indicator_table.py | 128 | 読む | HOUKOU2PROP | ③向け直す |
| gen_indicator_table.py | 134 | 読む | json の名前「 hash=@@HASH@@ gen_indicator_table.py が自動生成＝手で書き換えない（役割＝資料の表」 | ③向け直す |
| gen_indicator_table.py | 183 | 読む | LINEAGE_KINDS_FALLBACK | ③向け直す |
| gen_indicator_table.py | 188 | 持つ | LINEAGE_KINDS_FALLBACK（区分の言葉 10（例 オシレーター, トレンド, ボラ）） | ①写す→②消す |
| gen_indicator_table.py | 239 | 読む | json の名前「 の役割が資料の表（または r1_role_map.json）に無いので、札が決まらない＝先に資料の表に役割を足す（書か」 | ③向け直す |
| gen_materials.py | 62 | 読む | json の名前「v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/mate」 | ③向け直す |
| gen_materials.py | 69 | 読む | json の名前「materials.json」 | ③向け直す |
| gen_materials.py | 70 | 読む | json の名前「signal_families.json」 | ③向け直す |
| gen_materials.py | 113 | 読む | FAMILY_TEMPLATES | ③向け直す |
| gen_materials.py | 122 | 読む | REFS | ③向け直す |
| gen_materials.py | 176 | 読む | json の名前「同じ挙動なので省いた列の一覧（左＝省いた列・右＝残した列）。出どころ＝observe_config.json。」 | ③向け直す |
| gen_materials.py | 178 | 読む | json の名前「observe_config.json」 | ③向け直す |
| gen_materials.py | 270 | 読む | json の名前「signal_families.json の role_lineage から「系統 → 使える役割」を作る（書き写さない」 | ③向け直す |
| gen_materials.py | 323 | 読む | json の名前「observe_config.json」 | ③向け直す |
| gen_materials.py | 324 | 読む | json の名前「search_limits.json」 | ③向け直す |
| gen_materials.py | 482 | 読む | json の名前「場所1＝`observe_config.json` の、指標のパラメータ（材料カタログを作る関数が読む鍵）。

    」 | ③向け直す |
| gen_materials.py | 496 | 読む | json の名前「場所2＝`recipes/search_limits.json`（使い方の中の本数・閾値の段・上限）。」 | ③向け直す |
| gen_materials.py | 649 | 読む | json の名前「scripts/priority_rebuild/observe_config.json」 | ③向け直す |
| gen_materials.py | 651 | 読む | json の名前「scripts/priority_rebuild/recipes/search_limits.json」 | ③向け直す |
| gen_materials.py | 721 | 読む | MATERIAL_FAMILIES | ③向け直す |
| gen_materials.py | 729 | 読む | MATERIAL_FAMILIES | ③向け直す |
| gen_materials.py | 773 | 読む | MATERIAL_FAMILIES | ③向け直す |
| gen_materials.py | 863 | 読む | json の名前「condition_parts.json」 | ③向け直す |
| gen_materials.py | 908 | 持つ | _m14（名前 1・例 RSI） | ①写す→②消す |
| gen_materials.py | 920 | 読む | _m14 | ③向け直す |
| gen_materials.py | 922 | 読む | _m14 | ③向け直す |
| gen_materials.py | 968 | 読む | json の名前「condition_parts.json」 | ③向け直す |
| gen_materials.py | 1195 | 読む | json の名前「signal_families.json」 | ③向け直す |
| gen_materials.py | 1212 | 読む | json の名前「`signal_families.json` の `parts`」 | ③向け直す |
| gen_materials.py | 1214 | 読む | json の名前「`signal_families.json` の `timeframes`」 | ③向け直す |
| gen_materials.py | 1252 | 読む | REFS | ③向け直す |
| gen_materials.py | 1254 | 読む | FAMILY_LINEAGE | ③向け直す |
| gen_materials.py | 1269 | 読む | FAMILY_LINEAGE | ③向け直す |
| gen_materials.py | 1335 | 読む | json の名前「★6｜条件の部品の一覧（段C の C-1）。中身は condition_parts.json＝ここで新しい事実を書かない」 | ③向け直す |
| gen_materials.py | 1337 | 読む | json の名前「**★この節は機械が作ります（手書きゼロ）。**中身の正本＝`.claude/ratchet/condition_par」 | ③向け直す |
| gen_materials.py | 1548 | 読む | json の名前「> 生成器が実際にその部品を引くかどうかは、承認済みの型の表（`signal_families.json`）に」 | ③向け直す |
| gen_materials.py | 1565 | 読む | json の名前「- 検収専用の値は数えません＝`engine_tuner_gen.py` の `selftest` と `KENSHU_」 | ③向け直す |
| gen_materials.py | 1686 | 読む | json の名前「`recipes/search_limits.json` の `int_grid` に並んだ数字だけです。**ここも ★」 | ③向け直す |
| gen_materials.py | 1734 | 読む | json の名前「／ 使える役割 ／ `.claude/ratchet/signal_families.json` の `role_lin」 | ③向け直す |
| gen_materials.py | 1738 | 読む | json の名前「／ engine_tuner ／ `engine_tuner_exec.FAMILY_TEMPLATES`（生成器が名前」 | ③向け直す |
| gen_materials.py | 2142 | 読む | json の名前「signal_families.json」 | ③向け直す |
| gen_materials.py | 2165 | 読む | json の名前「**） ／ signal_families.json の parts と extra_parts ／
／ 8 ／ ★」 | ③向け直す |
| gen_materials.py | 2283 | 読む | json の名前「materials.json の指紋が正本と合わない（--write で作り直す）」 | ③向け直す |
| gen_materials.py | 2285 | 読む | json の名前「materials.json が無い（--write で作る）」 | ③向け直す |
| gen_materials.py | 2353 | 読む | REFS | ③向け直す |
| gen_materials.py | 2360 | 読む | REFS | ③向け直す |
| gen_materials.py | 2385 | 読む | REFS | ③向け直す |
| gen_materials.py | 2422 | 読む | FAMILY_TEMPLATES | ③向け直す |
| gen_materials.py | 2424 | 直書き | RSI | ③向け直す |
| gen_materials.py | 2424 | 読む | FAMILY_TEMPLATES | ③向け直す |
| gen_materials.py | 2432 | 読む | FAMILY_TEMPLATES | ③向け直す |
| gen_materials.py | 2433 | 読む | FAMILY_TEMPLATES | ③向け直す |
| gen_materials.py | 2559 | 読む | _m14 | ③向け直す |
| gen_materials.py | 2560 | 直書き | RSI | ③向け直す |
| gen_materials.py | 2628 | 読む | json の名前「signal_families.json」 | ③向け直す |
| gen_observe_manual.py | 55 | 読む | json の名前「observe_config.json」 | ③向け直す |
| gen_observe_manual.py | 246 | 読む | json の名前「⚠️ このファイルを手で書き換えないでください。中身は observe_diag.py と observe_config」 | ③向け直す |
| gen_regime_kb.py | 35 | 読む | json の名前「regime_laws.json」 | ③向け直す |
| gen_regime_kb.py | 37 | 読む | json の名前「regime_laws.json」 | ③向け直す |
| gen_regime_kb.py | 38 | 読む | json の名前「m2_stage_candidates.json」 | ③向け直す |
| gen_regime_kb.py | 605 | 読む | json の名前「件を regime_laws.json から読み込んで審査します**（読み込み＝`engine_tuner_exec.l」 | ③向け直す |
| gen_regime_kb.py | 631 | 読む | json の名前「**★判定の正本はこのファイル（regime_laws.json）です。**コードに直書きの判定は 2026-08-30」 | ③向け直す |
| gen_regime_kb.py | 754 | 読む | json の名前「**元データ**＝`.claude/ratchet/regime_laws.json` ／ **作り方**＝`」 | ③向け直す |
| gen_regime_kb.py | 1081 | 読む | FAMILY_LINEAGE | ③向け直す |
| gen_regime_kb.py | 1289 | 読む | json の名前「**元データ**＝`.claude/ratchet/m2_stage_candidates.json` ／ **作り方*」 | ③向け直す |
| gen_s22_combi.py | 53 | 読む | json の名前「search_limits.json」 | ③向け直す |
| gen_s22_combi.py | 168 | 読む | json の名前「**★この表はプログラムが作ります（手で書き換えない）。**出どころ＝`gen_s22_combi.py --write」 | ③向け直す |
| gen_s22_combi.py | 192 | 読む | json の名前「## 値の幅（`search_limits.json` の実物）」 | ③向け直す |
| gen_signal_families.py | 34 | 読む | json の名前「recipes/search_limits.json」 | ③向け直す |
| gen_signal_families.py | 41 | 読む | json の名前「v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/sign」 | ③向け直す |
| gen_signal_families.py | 46 | 読む | json の名前「.claude/ratchet/signal_families.json」 | ③向け直す |
| gen_signal_families.py | 86 | 読む | json の名前「[生成エラー] search_limits.json の n_min が読めない」 | ③向け直す |
| gen_signal_families.py | 145 | 読む | FAMILY_LINEAGE | ③向け直す |
| gen_signal_families.py | 147 | 持つ | table（区分の言葉 10（例 オシレーター, トレンド, ボラ）） | ①写す→②消す |
| gen_signal_families.py | 300 | 読む | table | ③向け直す |
| gen_signal_families.py | 304 | 読む | table | ③向け直す |
| gen_signal_families.py | 322 | 読む | table | ③向け直す |
| gen_signal_families.py | 332 | 読む | table | ③向け直す |
| gen_signal_families.py | 334 | 読む | table | ③向け直す |
| gen_signal_families.py | 338 | 読む | table | ③向け直す |
| gen_signal_families.py | 345 | 読む | table | ③向け直す |
| gen_signal_families.py | 345 | 読む | table | ③向け直す |
| gen_signal_families.py | 345 | 読む | table | ③向け直す |
| gen_signal_families.py | 350 | 読む | table | ③向け直す |
| gen_signal_families.py | 352 | 読む | table | ③向け直す |
| gen_signal_families.py | 353 | 読む | table | ③向け直す |
| gen_signal_families.py | 356 | 読む | table | ③向け直す |
| gen_signal_families.py | 358 | 読む | table | ③向け直す |
| gen_signal_families.py | 368 | 読む | table | ③向け直す |
| gen_signal_families.py | 391 | 読む | table | ③向け直す |
| gen_signal_families.py | 393 | 読む | table | ③向け直す |
| gen_signal_families.py | 406 | 読む | json の名前「### 探索のパラメータの格子（正本＝recipes/search_limits.json・まこさん承認 2026-08」 | ③向け直す |
| gen_signal_families.py | 461 | 読む | table | ③向け直す |
| gen_signal_families.py | 462 | 読む | table | ③向け直す |
| gen_signal_families.py | 494 | 読む | table | ③向け直す |
| gen_signal_families.py | 494 | 読む | table | ③向け直す |
| gen_signal_families.py | 501 | 読む | table | ③向け直す |
| gen_signal_families.py | 504 | 読む | table | ③向け直す |
| gen_signal_families.py | 505 | 読む | table | ③向け直す |
| gen_signal_families.py | 508 | 読む | table | ③向け直す |
| gen_signal_families.py | 508 | 読む | table | ③向け直す |
| gen_signal_families.py | 508 | 読む | table | ③向け直す |
| gen_signal_families.py | 512 | 読む | table | ③向け直す |
| gen_signal_families.py | 515 | 読む | table | ③向け直す |
| gen_signal_families.py | 518 | 読む | table | ③向け直す |
| gen_signal_families.py | 582 | 読む | json の名前「表（signal_families.json）が無い」 | ③向け直す |
| gen_signal_families.py | 809 | 読む | table | ③向け直す |
| gen_signal_families.py | 810 | 読む | table | ③向け直す |
| gen_signal_families.py | 811 | 読む | table | ③向け直す |
| gen_signal_families.py | 812 | 読む | table | ③向け直す |
| gen_signal_families.py | 986 | 読む | table | ③向け直す |
| gen_signal_families.py | 987 | 読む | table | ③向け直す |
| gen_signal_families.py | 988 | 読む | table | ③向け直す |
| gen_signal_families.py | 989 | 読む | table | ③向け直す |
| gen_signal_families.py | 1262 | 読む | FAMILY_TEMPLATES | ③向け直す |
| gen_signal_families.py | 1268 | 持つ | V9_FAMILY_MAP（名前 14・例 ADX, ATR%, BB%b） | ①写す→②消す |
| gen_signal_families.py | 1320 | 読む | table | ③向け直す |
| gen_signal_families.py | 1321 | 読む | table | ③向け直す |
| gen_signal_families.py | 1331 | 読む | V9_FAMILY_MAP | ③向け直す |
| gen_signal_families.py | 1362 | 直書き | Stoch%K | ③向け直す |
| gen_stage0_match.py | 53 | 読む | json の名前「material_ranking.json」 | ③向け直す |
| gen_stage0_match.py | 64 | 読む | json の名前「m2_stage_candidates.json」 | ③向け直す |
| gen_stage0_match.py | 143 | 読む | json の名前「**★この表はプログラムが作ります（手で書き換えない）。**出どころ＝`engine_tuner_milestones2」 | ③向け直す |
| indicator_reference_diag.py | 919 | 持つ | EXT2（名前 12・例 OBV傾き, RCI, fib位置） | ①写す→②消す |
| indicator_reference_diag.py | 957 | 持つ | INDICATOR_TABLE（区分の言葉 21（例 none, reversal, trend）） | ①写す→②消す |
| indicator_reference_diag.py | 957 | 持つ | INDICATOR_TABLE（名前 301・例 ABER位置, ABER原作位置, ADOSC比） | ①写す→②消す |
| indicator_reference_diag.py | 1278 | 読む | INDICATOR_TABLE | ③向け直す |
| indicator_reference_diag.py | 1282 | 読む | REFS | ③向け直す |
| indicator_reference_diag.py | 1306 | 読む | REFS | ③向け直す |
| indicator_reference_diag.py | 1321 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1325 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1328 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1331 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1343 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1346 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1349 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1352 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1356 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1359 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1362 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1368 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1373 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1376 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1379 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1389 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1394 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1398 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1401 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1404 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1407 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1411 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1414 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1420 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1424 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1431 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1438 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1443 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1446 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1450 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1454 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1459 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1462 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1465 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1470 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1475 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1482 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1491 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1497 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1501 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1506 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1510 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1519 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1522 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1525 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1562 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1569 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1574 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1577 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1580 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1595 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1599 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1604 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1608 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1613 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1631 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1634 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1636 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1653 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1656 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1658 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1660 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1663 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1670 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1676 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1701 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1706 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1711 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1727 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1751 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1759 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1931 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1939 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1944 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 1955 | 読む | json の名前「取れる距離の床（独立の実装の側）＝e37_scalp.SCALP_FLOOR × 設定ファイル observe_conf」 | ③向け直す |
| indicator_reference_diag.py | 1959 | 読む | json の名前「observe_config.json」 | ③向け直す |
| indicator_reference_diag.py | 2173 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2178 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2182 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2188 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2191 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2195 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2198 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2202 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2205 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2212 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2217 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2375 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2380 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2384 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2387 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2389 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2391 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2394 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2397 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2400 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2407 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2414 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2421 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2428 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2432 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 2437 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3595 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3598 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3601 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3604 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3607 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3610 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3613 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3616 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3619 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3622 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3625 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3628 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3631 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3635 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3638 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3641 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3644 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3647 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3651 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3654 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3659 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3662 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3664 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3666 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3669 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3672 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3682 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3685 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3688 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3691 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3694 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3698 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3701 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3703 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3707 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3710 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3712 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3714 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3717 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3719 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3721 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3725 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3729 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3733 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3739 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3742 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3746 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3749 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3757 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3766 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3769 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3771 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3774 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3776 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3779 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3781 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3783 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3786 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3788 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3791 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3794 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3797 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3799 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3818 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3824 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3829 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3832 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3834 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3837 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3839 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3845 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3848 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3850 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3854 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3857 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3861 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3864 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3866 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3869 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3871 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3885 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3888 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3889 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3892 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3896 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3899 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3902 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3903 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3906 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3907 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3910 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3911 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3914 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3915 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3918 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3921 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3924 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3926 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3929 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3934 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3937 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3938 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3941 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3942 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3945 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3946 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3949 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3950 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3953 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3954 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3957 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3958 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3962 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3963 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3966 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3967 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3970 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3971 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3974 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3975 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3978 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3984 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3987 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3990 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3992 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 3995 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4001 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4004 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4006 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4008 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4025 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4030 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4033 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4042 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4046 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4051 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4054 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4058 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4061 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4066 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4069 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4072 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4075 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4287 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4292 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4297 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4301 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4307 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4312 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4318 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4322 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4326 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4330 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4334 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4342 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4393 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4403 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4486 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4491 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4495 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4500 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4504 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4508 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4511 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4530 | 持つ | _THERMO_L（パラメータの定数 20） | ①写す→②消す |
| indicator_reference_diag.py | 4679 | 読む | _THERMO_L | ③向け直す |
| indicator_reference_diag.py | 4706 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4711 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4715 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4720 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4723 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4727 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4730 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4735 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4740 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4744 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4749 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4755 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4760 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4767 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4777 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4781 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 4801 | 持つ | _HT_START_A（パラメータの定数 12） | ①写す→②消す |
| indicator_reference_diag.py | 4802 | 持つ | _HT_START_B（パラメータの定数 37） | ①写す→②消す |
| indicator_reference_diag.py | 4804 | 持つ | _MSW_P（パラメータの定数 5） | ①写す→②消す |
| indicator_reference_diag.py | 4903 | 読む | _HT_START_A | ③向け直す |
| indicator_reference_diag.py | 4907 | 読む | _HT_START_B | ③向け直す |
| indicator_reference_diag.py | 4912 | 読む | _HT_START_A | ③向け直す |
| indicator_reference_diag.py | 4917 | 読む | _HT_START_A | ③向け直す |
| indicator_reference_diag.py | 4921 | 読む | _HT_START_B | ③向け直す |
| indicator_reference_diag.py | 4925 | 読む | _HT_START_B | ③向け直す |
| indicator_reference_diag.py | 4929 | 読む | _HT_START_B | ③向け直す |
| indicator_reference_diag.py | 4966 | 読む | _MSW_P | ③向け直す |
| indicator_reference_diag.py | 4996 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5005 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5012 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5018 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5022 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5026 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5030 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5034 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5040 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5048 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5060 | 持つ | _CDLZ_N（パラメータの定数 30） | ①写す→②消す |
| indicator_reference_diag.py | 5061 | 持つ | _DOJI_N（パラメータの定数 10） | ①写す→②消す |
| indicator_reference_diag.py | 5146 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5153 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5158 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5168 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5172 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5176 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5184 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5189 | 持つ | _r(...) の呼び出し | ①写す→②消す |
| indicator_reference_diag.py | 5204 | 持つ | R1_KEEP_ON（名前 34・例 ABER位置, close vs ABER_ZG%, close vs ALMA%） | ①写す→②消す |
| indicator_reference_diag.py | 5212 | 読む | R1_KEEP_ON | ③向け直す |
| indicator_reference_diag.py | 5212 | 読む | REFS | ③向け直す |
| indicator_reference_diag.py | 5215 | 読む | REFS | ③向け直す |
| indicator_reference_diag.py | 5216 | 読む | R1_KEEP_ON | ③向け直す |
| indicator_reference_diag.py | 5226 | 持つ | DEMAND_REF（名前が定義の表） | ①写す→②消す |
| indicator_reference_diag.py | 5259 | 持つ | AXIS_EC（区分の言葉 5（例 ボラ, ローソク, 位置）） | ①写す→②消す |
| indicator_reference_diag.py | 5259 | 持つ | AXIS_EC（名前 28・例 ADX, ATR%, BB%b） | ①写す→②消す |
| indicator_reference_diag.py | 5349 | 持つ | RANGE_GEO_REF（名前が定義の表） | ①写す→②消す |
| indicator_reference_diag.py | 5409 | 読む | RANGE_GEO_REF | ③向け直す |
| indicator_reference_diag.py | 5412 | 読む | RANGE_GEO_REF | ③向け直す |
| indicator_reference_diag.py | 5437 | 持つ | TA_CLASS_MAP（名前 39・例 AROOND, AROONOSC, AROONU） | ①写す→②消す |
| indicator_reference_diag.py | 5476 | 読む | INDICATOR_TABLE | ③向け直す |
| indicator_reference_diag.py | 5484 | 持つ | LINEAGE_KINDS（区分の言葉 10（例 オシレーター, トレンド, ボラ）） | ①写す→②消す |
| indicator_reference_diag.py | 5488 | 持つ | LINEAGE_QUESTION（区分の言葉 10（例 オシレーター, トレンド, ボラ）） | ①写す→②消す |
| indicator_reference_diag.py | 5517 | 読む | FAMILY_LINEAGE | ③向け直す |
| indicator_reference_diag.py | 5528 | 持つ | INDUSTRY_MAP（名前 301・例 ABER位置, ABER原作位置, ADOSC比） | ①写す→②消す |
| indicator_reference_diag.py | 5979 | 読む | INDUSTRY_MAP | ③向け直す |
| indicator_reference_diag.py | 5982 | 読む | INDUSTRY_MAP | ③向け直す |
| indicator_reference_diag.py | 6003 | 持つ | CONST_REGISTRY（名前が定義の表） | ①写す→②消す |
| indicator_reference_diag.py | 6028 | 読む | CONST_REGISTRY | ③向け直す |
| indicator_reference_diag.py | 6037 | 持つ | TIME_REF（名前が定義の表） | ①写す→②消す |
| indicator_reference_diag.py | 6087 | 読む | AXIS_EC | ③向け直す |
| indicator_reference_diag.py | 6092 | 読む | AXIS_EC | ③向け直す |
| leak_causality_diag.py | 249 | 読む | json の名前「/recipes/identity_s2_legacy.json」 | ③向け直す |
| leak_causality_diag.py | 249 | 読む | json の名前「/recipes/search_limits.json」 | ③向け直す |
| leak_causality_diag.py | 250 | 読む | json の名前「/recipes/identity_s1_legacy.json」 | ③向け直す |
| leak_causality_diag.py | 251 | 読む | json の名前「v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/sign」 | ③向け直す |
| leak_causality_diag.py | 252 | 読む | json の名前「v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/exit」 | ③向け直す |
| leak_causality_diag.py | 255 | 読む | json の名前「/observe_config.json」 | ③向け直す |
| leak_causality_diag.py | 262 | 読む | json の名前「v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/regi」 | ③向け直す |
| observe_diag.py | 177 | 読む | json の名前「/observe_config.json」 | ③向け直す |
| observe_diag.py | 781 | 持つ | _BAND_IMPL（名前 8・例 帯VA, 帯VA1時間ATR, 帯pivot） | ①写す→②消す |
| observe_diag.py | 796 | 読む | _BAND_IMPL | ③向け直す |
| observe_diag.py | 1020 | 読む | MATERIAL_FAMILIES | ③向け直す |
| observe_diag.py | 1022 | 読む | MATERIAL_FAMILIES | ③向け直す |
| observe_diag.py | 1036 | 読む | MATERIAL_FAMILIES | ③向け直す |
| observe_diag.py | 1056 | 読む | MATERIAL_FAMILIES | ③向け直す |
| observe_diag.py | 1058 | 読む | MATERIAL_FAMILIES | ③向け直す |
| observe_diag.py | 1060 | 読む | MATERIAL_FAMILIES | ③向け直す |
| observe_diag.py | 1069 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1070 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1071 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1073 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1076 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1079 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1080 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1081 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1083 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1086 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1090 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1093 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1095 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1097 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1099 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1100 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1102 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1104 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1106 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1108 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1112 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1114 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1116 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1119 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1123 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1127 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1132 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1136 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1139 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1142 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1143 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1145 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1148 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1149 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1150 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1152 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1156 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1159 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1163 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1165 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1167 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1169 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1176 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1179 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1181 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1182 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1196 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1198 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1198 | 持つ | 当日VWAP のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1199 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1201 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1203 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1207 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1208 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1210 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1213 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1215 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1244 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1244 | 持つ | 前期間pivotPP のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1245 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1245 | 持つ | 前期間pivotR1 のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1246 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1246 | 持つ | 前期間pivotS1 のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1248 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1248 | 持つ | 前週pivotPP のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1249 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1249 | 持つ | 前週pivotR1 のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1250 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1250 | 持つ | 前週pivotS1 のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1251 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1253 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1255 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1257 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1262 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1262 | 持つ | 前日POC のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1264 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1264 | 持つ | 前日VAH のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1266 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1266 | 持つ | 前日VAL のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1268 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1268 | 持つ | 当日POC のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1270 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1270 | 持つ | 当日VAH のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1272 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1272 | 持つ | 当日VAL のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1274 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1278 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1282 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1287 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1288 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1289 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1291 | 持つ | SMC_SWEEP確定 のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1291 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1295 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1296 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1299 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1300 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1302 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1303 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1307 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1308 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1313 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1314 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1321 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1322 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1324 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1326 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1327 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1328 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1329 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1330 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1331 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1332 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1333 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1334 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1336 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1338 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1344 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1345 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1346 | 持つ | KST のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1346 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1347 | 持つ | AO% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1347 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1348 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1349 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1350 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1352 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1354 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1355 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1357 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1359 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1364 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1365 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1366 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1367 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1368 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1369 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1371 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1373 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1375 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1377 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1379 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1381 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1383 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1385 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1388 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1389 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1390 | 持つ | SMC_SWEEP のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1390 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1393 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1395 | 持つ | SQZ_ON のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1395 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1420 | 持つ | SQZ_ON_Carter のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1420 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1424 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1427 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1455 | 持つ | STC のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1455 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1456 | 持つ | STCstoch のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1456 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1460 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1462 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1466 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1468 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1470 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1472 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1481 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1482 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1483 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1484 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1485 | 持つ | UO のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1485 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1486 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1488 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1490 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1493 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1496 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1499 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1540 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1543 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1584 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1585 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1586 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1590 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1592 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1593 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1593 | 持つ | close vs HILO% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1595 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1595 | 持つ | close vs HT_TRENDLINE% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1598 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1598 | 持つ | close vs HT_TRENDLINE_HL% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1600 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1600 | 持つ | close vs HWMA% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1601 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1601 | 持つ | close vs MAMA% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1602 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1602 | 持つ | close vs FAMA% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1609 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1609 | 持つ | close vs MAMA_HL% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1610 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1610 | 持つ | close vs FAMA_HL% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1618 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1620 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1629 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1632 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1639 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1641 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1643 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1645 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1646 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1647 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1648 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1649 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1650 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1651 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1653 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1655 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1657 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1662 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1664 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1667 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1668 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1668 | 持つ | close vs CKSPl% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1669 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1669 | 持つ | close vs CKSPs% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1670 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1670 | 持つ | close vs PMAX% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1672 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1672 | 持つ | close vs PSAR% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1674 | 持つ | PSAR加速 のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1674 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1675 | 持つ | PSAR反転 のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1675 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1678 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1678 | 持つ | close vs SAREXT% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1683 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1686 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1689 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1691 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1692 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1693 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1695 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1697 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1700 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1702 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1704 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1705 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1706 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1707 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1710 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1712 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1713 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1714 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1715 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1716 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1718 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1722 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1722 | 持つ | close vs ABER_ZG% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1723 | 持つ | ABER位置 のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1723 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1728 | 持つ | ABER原作位置 のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1728 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1730 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1730 | 持つ | close vs ACCBL% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1731 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1731 | 持つ | close vs ACCBU% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1732 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1732 | 持つ | close vs CE_L% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1733 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1733 | 持つ | close vs CE_S% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1734 | 持つ | HWC位置 のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1734 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1735 | 持つ | HWC幅% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1735 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1736 | 持つ | MASSI のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1736 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1737 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1739 | 持つ | TR% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1739 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1740 | 持つ | THERMO% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1740 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1741 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1748 | 持つ | THERMO原作% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1748 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1750 | 持つ | THERMO_EMA% のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1750 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1751 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1752 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1753 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1755 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1756 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1758 | 持つ | HT_DCPHASE のパラメータ（計算の関数の既定値・設定の鍵から読まない） | ①写す→②消す |
| observe_diag.py | 1758 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1760 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1762 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1764 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1765 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1767 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1769 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1770 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1773 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1775 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1780 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1783 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1784 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1786 | 持つ | _reg(...) の呼び出し | ①写す→②消す |
| observe_diag.py | 1793 | 読む | json の名前「指標カタログ。期間・パラメータは observe_config.json から取る（コードに焼かない）。

    ★2」 | ③向け直す |
| observe_diag.py | 1821 | 直書き | ADX | ③向け直す |
| observe_diag.py | 1822 | 直書き | DI差 | ③向け直す |
| observe_diag.py | 1824 | 直書き | MACD線% | ③向け直す |
| observe_diag.py | 1825 | 直書き | MACDシグナル線% | ③向け直す |
| observe_diag.py | 1826 | 直書き | MACDヒスト% | ③向け直す |
| observe_diag.py | 1828 | 直書き | RSI | ③向け直す |
| observe_diag.py | 1839 | 直書き | ROC | ③向け直す |
| observe_diag.py | 1841 | 直書き | Stoch%K | ③向け直す |
| observe_diag.py | 1842 | 直書き | Stoch%D | ③向け直す |
| observe_diag.py | 1844 | 直書き | MFI | ③向け直す |
| observe_diag.py | 1846 | 直書き | CMF | ③向け直す |
| observe_diag.py | 1848 | 直書き | OBV傾き | ③向け直す |
| observe_diag.py | 1850 | 直書き | close vs 転換線% | ③向け直す |
| observe_diag.py | 1851 | 直書き | close vs 基準線% | ③向け直す |
| observe_diag.py | 1853 | 直書き | RCI | ③向け直す |
| observe_diag.py | 1855 | 直書き | EMA傾き | ③向け直す |
| observe_diag.py | 1858 | 直書き | ATR% | ③向け直す |
| observe_diag.py | 1861 | 直書き | BB%b | ③向け直す |
| observe_diag.py | 1862 | 直書き | BB幅 | ③向け直す |
| observe_diag.py | 1864 | 直書き | realized_vol | ③向け直す |
| observe_diag.py | 1865 | 直書き | realized_vol_rv | ③向け直す |
| observe_diag.py | 1867 | 直書き | Donchian幅% | ③向け直す |
| observe_diag.py | 1869 | 直書き | zscore | ③向け直す |
| observe_diag.py | 1870 | 直書き | zscore_return | ③向け直す |
| observe_diag.py | 1873 | 直書き | volume_ratio | ③向け直す |
| observe_diag.py | 1875 | 直書き | 包み足 | ③向け直す |
| observe_diag.py | 1876 | 直書き | 孕み足 | ③向け直す |
| observe_diag.py | 1877 | 直書き | pinbar | ③向け直す |
| observe_diag.py | 1878 | 直書き | 連続本数 | ③向け直す |
| observe_diag.py | 1879 | 直書き | body比 | ③向け直す |
| observe_diag.py | 1880 | 直書き | 上ヒゲ比 | ③向け直す |
| observe_diag.py | 1881 | 直書き | 下ヒゲ比 | ③向け直す |
| observe_diag.py | 1884 | 直書き | swing高値距離% | ③向け直す |
| observe_diag.py | 1885 | 直書き | swing安値距離% | ③向け直す |
| observe_diag.py | 1886 | 直書き | 高値からの経過バー | ③向け直す |
| observe_diag.py | 1887 | 直書き | 安値からの経過バー | ③向け直す |
| observe_diag.py | 1888 | 直書き | 形スコア | ③向け直す |
| observe_diag.py | 1890 | 直書き | W字 | ③向け直す |
| observe_diag.py | 1891 | 直書き | W字確定谷 | ③向け直す |
| observe_diag.py | 1894 | 直書き | fractal高値距離% | ③向け直す |
| observe_diag.py | 1895 | 直書き | fractal安値距離% | ③向け直す |
| observe_diag.py | 1896 | 直書き | 高値切り上げ幅% | ③向け直す |
| observe_diag.py | 1897 | 直書き | 安値切り上げ幅% | ③向け直す |
| observe_diag.py | 1898 | 直書き | 構造破断距離% | ③向け直す |
| observe_diag.py | 1901 | 直書き | close vs EMA | ③向け直す |
| observe_diag.py | 1903 | 直書き | close vs SMA | ③向け直す |
| observe_diag.py | 1905 | 直書き | close vs VWAP% | ③向け直す |
| observe_diag.py | 1906 | 直書き | close vs VWAP典型% | ③向け直す |
| observe_diag.py | 1907 | 直書き | close vs 当日VWAP% | ③向け直す |
| observe_diag.py | 1909 | 直書き | close vs Keltner上% | ③向け直す |
| observe_diag.py | 1910 | 直書き | close vs Keltner下% | ③向け直す |
| observe_diag.py | 1912 | 直書き | close vs Supertrend% | ③向け直す |
| observe_diag.py | 1914 | 直書き | close vs 本高値% | ③向け直す |
| observe_diag.py | 1915 | 直書き | close vs 本安値% | ③向け直す |
| observe_diag.py | 1918 | 直書き | close vs pivotPP% | ③向け直す |
| observe_diag.py | 1919 | 直書き | close vs pivotR1% | ③向け直す |
| observe_diag.py | 1920 | 直書き | close vs pivotS1% | ③向け直す |
| observe_diag.py | 1922 | 直書き | close vs 前期間pivotPP% | ③向け直す |
| observe_diag.py | 1923 | 直書き | close vs 前期間pivotR1% | ③向け直す |
| observe_diag.py | 1924 | 直書き | close vs 前期間pivotS1% | ③向け直す |
| observe_diag.py | 1925 | 直書き | close vs 前週pivotPP% | ③向け直す |
| observe_diag.py | 1926 | 直書き | close vs 前週pivotR1% | ③向け直す |
| observe_diag.py | 1927 | 直書き | close vs 前週pivotS1% | ③向け直す |
| observe_diag.py | 1929 | 直書き | fib位置 | ③向け直す |
| observe_diag.py | 1931 | 直書き | close vs POC% | ③向け直す |
| observe_diag.py | 1932 | 直書き | close vs VAH% | ③向け直す |
| observe_diag.py | 1933 | 直書き | close vs VAL% | ③向け直す |
| observe_diag.py | 1935 | 直書き | close vs 前日POC% | ③向け直す |
| observe_diag.py | 1936 | 直書き | close vs 前日VAH% | ③向け直す |
| observe_diag.py | 1937 | 直書き | close vs 前日VAL% | ③向け直す |
| observe_diag.py | 1938 | 直書き | close vs 当日POC% | ③向け直す |
| observe_diag.py | 1939 | 直書き | close vs 当日VAH% | ③向け直す |
| observe_diag.py | 1940 | 直書き | close vs 当日VAL% | ③向け直す |
| observe_diag.py | 1943 | 直書き | S-Rタッチ数 | ③向け直す |
| observe_diag.py | 1944 | 直書き | S-Rタッチ確定数 | ③向け直す |
| observe_diag.py | 1950 | 直書き | MMI | ③向け直す |
| observe_diag.py | 1956 | 直書き | S-Rタッチ1時間ATR | ③向け直す |
| observe_diag.py | 1957 | 直書き | S-Rタッチ確定1時間ATR | ③向け直す |
| observe_diag.py | 1968 | 直書き | 帯スイング | ③向け直す |
| observe_diag.py | 1971 | 直書き | 帯スイング1時間ATR | ③向け直す |
| observe_diag.py | 1973 | 直書き | 帯pivot | ③向け直す |
| observe_diag.py | 1974 | 直書き | 帯pivot前週 | ③向け直す |
| observe_diag.py | 1975 | 直書き | 帯VA | ③向け直す |
| observe_diag.py | 1978 | 直書き | 帯pivot1時間ATR | ③向け直す |
| observe_diag.py | 1979 | 直書き | 帯pivot前週1時間ATR | ③向け直す |
| observe_diag.py | 1980 | 直書き | 帯VA1時間ATR | ③向け直す |
| observe_diag.py | 1984 | 直書き | LeeMykland | ③向け直す |
| observe_diag.py | 1985 | 直書き | LeeMykland_E36版 | ③向け直す |
| observe_diag.py | 1995 | 直書き | AR | ③向け直す |
| observe_diag.py | 1995 | 直書き | BIAS | ③向け直す |
| observe_diag.py | 1995 | 直書き | BR | ③向け直す |
| observe_diag.py | 1995 | 直書き | CCI | ③向け直す |
| observe_diag.py | 1995 | 直書き | CFO | ③向け直す |
| observe_diag.py | 1995 | 直書き | CG | ③向け直す |
| observe_diag.py | 1995 | 直書き | CMO | ③向け直す |
| observe_diag.py | 1995 | 直書き | CTI | ③向け直す |
| observe_diag.py | 1996 | 直書き | DM+% | ③向け直す |
| observe_diag.py | 1996 | 直書き | DM-% | ③向け直す |
| observe_diag.py | 1996 | 直書き | ER | ③向け直す |
| observe_diag.py | 1996 | 直書き | ERI弱気% | ③向け直す |
| observe_diag.py | 1996 | 直書き | ERI強気% | ③向け直す |
| observe_diag.py | 1996 | 直書き | INERTIA | ③向け直す |
| observe_diag.py | 1999 | 直書き | LRSI | ③向け直す |
| observe_diag.py | 2000 | 直書き | BOP | ③向け直す |
| observe_diag.py | 2001 | 直書き | KST | ③向け直す |
| observe_diag.py | 2003 | 直書き | APO% | ③向け直す |
| observe_diag.py | 2006 | 直書き | COPC | ③向け直す |
| observe_diag.py | 2007 | 直書き | FISHER | ③向け直す |
| observe_diag.py | 2008 | 直書き | FISHERシグナル | ③向け直す |
| observe_diag.py | 2009 | 直書き | KSTシグナル | ③向け直す |
| observe_diag.py | 2011 | 直書き | KDJ%K | ③向け直す |
| observe_diag.py | 2012 | 直書き | KDJ%D | ③向け直す |
| observe_diag.py | 2013 | 直書き | KDJ%J | ③向け直す |
| observe_diag.py | 2016 | 直書き | AO% | ③向け直す |
| observe_diag.py | 2020 | 直書き | MOM% | ③向け直す |
| observe_diag.py | 2020 | 直書き | PGO | ③向け直す |
| observe_diag.py | 2020 | 直書き | PO | ③向け直す |
| observe_diag.py | 2020 | 直書き | PSL | ③向け直す |
| observe_diag.py | 2020 | 直書き | RSX | ③向け直す |
| observe_diag.py | 2020 | 直書き | RVGI | ③向け直す |
| observe_diag.py | 2020 | 直書き | RVGIシグナル | ③向け直す |
| observe_diag.py | 2020 | 直書き | RVGIヒスト | ③向け直す |
| observe_diag.py | 2023 | 直書き | PPO | ③向け直す |
| observe_diag.py | 2023 | 直書き | PPOシグナル | ③向け直す |
| observe_diag.py | 2023 | 直書き | PPOヒスト | ③向け直す |
| observe_diag.py | 2023 | 直書き | PVO | ③向け直す |
| observe_diag.py | 2023 | 直書き | PVOシグナル | ③向け直す |
| observe_diag.py | 2023 | 直書き | PVOヒスト | ③向け直す |
| observe_diag.py | 2025 | 直書き | QQE | ③向け直す |
| observe_diag.py | 2025 | 直書き | QQE_RSIMA | ③向け直す |
| observe_diag.py | 2025 | 直書き | SMC_SWEEP | ③向け直す |
| observe_diag.py | 2025 | 直書き | SQZ% | ③向け直す |
| observe_diag.py | 2025 | 直書き | SQZ_ON | ③向け直す |
| observe_diag.py | 2026 | 直書き | SQZPRO_ON_NARROW | ③向け直す |
| observe_diag.py | 2026 | 直書き | SQZPRO_ON_WIDE | ③向け直す |
| observe_diag.py | 2026 | 直書き | STC | ③向け直す |
| observe_diag.py | 2026 | 直書き | STCstoch | ③向け直す |
| observe_diag.py | 2028 | 直書き | SMC_SWEEP確定 | ③向け直す |
| observe_diag.py | 2029 | 直書き | SQZ_ON_Carter | ③向け直す |
| observe_diag.py | 2033 | 直書き | StochRSI%K | ③向け直す |
| observe_diag.py | 2034 | 直書き | StochRSI%D | ③向け直す |
| observe_diag.py | 2035 | 直書き | StochRSI素%K | ③向け直す |
| observe_diag.py | 2037 | 直書き | TRIX | ③向け直す |
| observe_diag.py | 2038 | 直書き | TRIXシグナル | ③向け直す |
| observe_diag.py | 2039 | 直書き | TRIXヒスト | ③向け直す |
| observe_diag.py | 2040 | 直書き | TRIX_EMAシグナル | ③向け直す |
| observe_diag.py | 2041 | 直書き | TRIX_EMAヒスト | ③向け直す |
| observe_diag.py | 2042 | 直書き | TD_SEQ_UP | ③向け直す |
| observe_diag.py | 2043 | 直書き | TD_SEQ_DN | ③向け直す |
| observe_diag.py | 2044 | 直書き | UO | ③向け直す |
| observe_diag.py | 2046 | 直書き | TSI | ③向け直す |
| observe_diag.py | 2046 | 直書き | TSIシグナル | ③向け直す |
| observe_diag.py | 2046 | 直書き | TSIヒスト | ③向け直す |
| observe_diag.py | 2047 | 直書き | VWMACDシグナル% | ③向け直す |
| observe_diag.py | 2047 | 直書き | VWMACDヒスト% | ③向け直す |
| observe_diag.py | 2047 | 直書き | VWMACD線% | ③向け直す |
| observe_diag.py | 2056 | 直書き | LRangle | ③向け直す |
| observe_diag.py | 2066 | 直書き | close vs FWMA% | ③向け直す |
| observe_diag.py | 2067 | 直書き | FWMA傾き | ③向け直す |
| observe_diag.py | 2068 | 直書き | close vs HILO% | ③向け直す |
| observe_diag.py | 2069 | 直書き | close vs HT_TRENDLINE% | ③向け直す |
| observe_diag.py | 2070 | 直書き | close vs HT_TRENDLINE_HL% | ③向け直す |
| observe_diag.py | 2071 | 直書き | close vs HWMA% | ③向け直す |
| observe_diag.py | 2078 | 直書き | LRslope% | ③向け直す |
| observe_diag.py | 2079 | 直書き | close vs MAMA% | ③向け直す |
| observe_diag.py | 2080 | 直書き | close vs FAMA% | ③向け直す |
| observe_diag.py | 2081 | 直書き | close vs MAMA_HL% | ③向け直す |
| observe_diag.py | 2082 | 直書き | close vs FAMA_HL% | ③向け直す |
| observe_diag.py | 2091 | 直書き | close vs MMAR% | ③向け直す |
| observe_diag.py | 2092 | 直書き | MMAR傾き | ③向け直す |
| observe_diag.py | 2095 | 直書き | close vs RAINBOW% | ③向け直す |
| observe_diag.py | 2096 | 直書き | RAINBOW傾き | ③向け直す |
| observe_diag.py | 2104 | 直書き | close vs SSF平均% | ③向け直す |
| observe_diag.py | 2105 | 直書き | close vs TRIMA_TA% | ③向け直す |
| observe_diag.py | 2106 | 直書き | close vs VIDYA_CMO% | ③向け直す |
| observe_diag.py | 2110 | 直書き | ADXR | ③向け直す |
| observe_diag.py | 2110 | 直書き | AROOND | ③向け直す |
| observe_diag.py | 2110 | 直書き | AROONOSC | ③向け直す |
| observe_diag.py | 2110 | 直書き | AROONU | ③向け直す |
| observe_diag.py | 2110 | 直書き | DI+ | ③向け直す |
| observe_diag.py | 2110 | 直書き | DI- | ③向け直す |
| observe_diag.py | 2110 | 直書き | DX | ③向け直す |
| observe_diag.py | 2111 | 直書き | CHOP | ③向け直す |
| observe_diag.py | 2111 | 直書き | VHF | ③向け直す |
| observe_diag.py | 2111 | 直書き | VTXM | ③向け直す |
| observe_diag.py | 2111 | 直書き | VTXP | ③向け直す |
| observe_diag.py | 2114 | 直書き | QSTICK% | ③向け直す |
| observe_diag.py | 2116 | 直書き | DPO% | ③向け直す |
| observe_diag.py | 2117 | 直書き | DPO教科書% | ③向け直す |
| observe_diag.py | 2118 | 直書き | TTM_TREND | ③向け直す |
| observe_diag.py | 2119 | 直書き | AMAT_LR | ③向け直す |
| observe_diag.py | 2119 | 直書き | close vs CKSPl% | ③向け直す |
| observe_diag.py | 2119 | 直書き | close vs CKSPs% | ③向け直す |
| observe_diag.py | 2119 | 直書き | close vs PMAX% | ③向け直す |
| observe_diag.py | 2120 | 直書き | PSAR加速 | ③向け直す |
| observe_diag.py | 2120 | 直書き | PSAR反転 | ③向け直す |
| observe_diag.py | 2120 | 直書き | close vs PSAR% | ③向け直す |
| observe_diag.py | 2120 | 直書き | close vs SAREXT% | ③向け直す |
| observe_diag.py | 2133 | 直書き | EFI比 | ③向け直す |
| observe_diag.py | 2133 | 直書き | EOM比 | ③向け直す |
| observe_diag.py | 2133 | 直書き | MARKETFI比 | ③向け直す |
| observe_diag.py | 2133 | 直書き | NVI傾き | ③向け直す |
| observe_diag.py | 2133 | 直書き | PVI傾き | ③向け直す |
| observe_diag.py | 2134 | 直書き | PVOL比 | ③向け直す |
| observe_diag.py | 2134 | 直書き | PVT傾き | ③向け直す |
| observe_diag.py | 2134 | 直書き | WAD傾き | ③向け直す |
| observe_diag.py | 2136 | 直書き | ADOSC比 | ③向け直す |
| observe_diag.py | 2136 | 直書き | AOBV_LR | ③向け直す |
| observe_diag.py | 2136 | 直書き | KVOシグナル比 | ③向け直す |
| observe_diag.py | 2136 | 直書き | KVO比 | ③向け直す |
| observe_diag.py | 2136 | 直書き | VOSC | ③向け直す |
| observe_diag.py | 2141 | 直書き | VFI | ③向け直す |
| observe_diag.py | 2143 | 直書き | 出来高変化率% | ③向け直す |
| observe_diag.py | 2151 | 直書き | MAD比 | ③向け直す |
| observe_diag.py | 2151 | 直書き | kurtosis | ③向け直す |
| observe_diag.py | 2151 | 直書き | skew | ③向け直す |
| observe_diag.py | 2151 | 直書き | stdev% | ③向け直す |
| observe_diag.py | 2154 | 直書き | close vs MEDIAN% | ③向け直す |
| observe_diag.py | 2155 | 直書き | MEDIAN傾き% | ③向け直す |
| observe_diag.py | 2166 | 直書き | ABER位置 | ③向け直す |
| observe_diag.py | 2166 | 直書き | close vs ABER_ZG% | ③向け直す |
| observe_diag.py | 2166 | 直書き | close vs ACCBL% | ③向け直す |
| observe_diag.py | 2166 | 直書き | close vs ACCBU% | ③向け直す |
| observe_diag.py | 2167 | 直書き | close vs CE_L% | ③向け直す |
| observe_diag.py | 2167 | 直書き | close vs CE_S% | ③向け直す |
| observe_diag.py | 2169 | 直書き | ABER原作位置 | ③向け直す |
| observe_diag.py | 2174 | 直書き | HWC位置 | ③向け直す |
| observe_diag.py | 2174 | 直書き | HWC幅% | ③向け直す |
| observe_diag.py | 2174 | 直書き | MASSI | ③向け直す |
| observe_diag.py | 2174 | 直書き | PDIST% | ③向け直す |
| observe_diag.py | 2174 | 直書き | THERMO% | ③向け直す |
| observe_diag.py | 2174 | 直書き | THERMO比 | ③向け直す |
| observe_diag.py | 2174 | 直書き | TR% | ③向け直す |
| observe_diag.py | 2176 | 直書き | THERMO原作% | ③向け直す |
| observe_diag.py | 2177 | 直書き | THERMO_EMA% | ③向け直す |
| observe_diag.py | 2179 | 直書き | CVI | ③向け直す |
| observe_diag.py | 2180 | 直書き | RVI | ③向け直す |
| observe_diag.py | 2181 | 直書き | UI | ③向け直す |
| observe_diag.py | 2192 | 直書き | EBSW | ③向け直す |
| observe_diag.py | 2192 | 直書き | HT_DCPERIOD | ③向け直す |
| observe_diag.py | 2192 | 直書き | HT_DCPHASE | ③向け直す |
| observe_diag.py | 2192 | 直書き | HT_INPHASE% | ③向け直す |
| observe_diag.py | 2192 | 直書き | HT_QUAD% | ③向け直す |
| observe_diag.py | 2193 | 直書き | HT_LEADSINE | ③向け直す |
| observe_diag.py | 2193 | 直書き | HT_SINE | ③向け直す |
| observe_diag.py | 2193 | 直書き | HT_TRENDMODE | ③向け直す |
| observe_diag.py | 2193 | 直書き | MSW_LEAD | ③向け直す |
| observe_diag.py | 2193 | 直書き | MSW_SINE | ③向け直す |
| observe_diag.py | 2206 | 直書き | 実体幅比 | ③向け直す |
| observe_diag.py | 2207 | 直書き | 内側バー | ③向け直す |
| observe_diag.py | 2211 | 直書き | HA実体% | ③向け直す |
| observe_diag.py | 2212 | 直書き | HA上ヒゲ比 | ③向け直す |
| observe_diag.py | 2213 | 直書き | HA下ヒゲ比 | ③向け直す |
| observe_diag.py | 3391 | 直書き | ATR% | ③向け直す |
| observe_diag.py | 3391 | 直書き | BB幅 | ③向け直す |
| observe_diag.py | 3391 | 直書き | Donchian幅 | ③向け直す |
| observe_diag.py | 3391 | 直書き | realized_vol | ③向け直す |
| observe_diag.py | 3393 | 直書き | CMF | ③向け直す |
| observe_diag.py | 3393 | 直書き | MFI | ③向け直す |
| observe_diag.py | 3393 | 直書き | volume_ratio | ③向け直す |
| observe_diag.py | 3395 | 直書き | body比 | ③向け直す |
| observe_diag.py | 3395 | 直書き | pinbar | ③向け直す |
| observe_diag.py | 3395 | 直書き | 包み足 | ③向け直す |
| observe_diag.py | 3395 | 直書き | 連続本数 | ③向け直す |
| observe_diag.py | 3397 | 直書き | fib位置 | ③向け直す |
| observe_diag.py | 3398 | 直書き | BB%b | ③向け直す |
| observe_diag.py | 3398 | 直書き | pivotPP | ③向け直す |
| observe_diag.py | 3398 | 直書き | zscore | ③向け直す |
| observe_diag.py | 3398 | 直書き | 形スコア | ③向け直す |
| observe_diag.py | 3569 | 読む | json の名前「場面バーの抽出（型は登録表 _SCENE_KINDS・パラメータは observe_config.json の scen」 | ③向け直す |
| observe_diag.py | 3900 | 読む | json の名前「 が無い（observe_config.json・定義済み 」 | ③向け直す |
| observe_diag.py | 3929 | 読む | json の名前「
  ⚠️ この計画の外は検証しない。場面・バリア・探索条件を変えるのは observe_config.json を編集」 | ③向け直す |
| observe_diag.py | 3937 | 読む | json の名前「 が無い（observe_config.json）」 | ③向け直す |
| observe_diag.py | 4101 | 読む | json の名前「検証計画の自動生成＝検証する内容・項目・条件を実値から出す1枚。検証する前にまこさんへ提出する。
    CC は計画を」 | ③向け直す |
| observe_diag.py | 4149 | 読む | json の名前「
  ⚠️ この計画の外は検証しない。項目を足す/減らすのは observe_config.json を編集して計画を再」 | ③向け直す |
| observe_diag.py | 4477 | 読む | json の名前「  足の内訳（observe_config.json の timeframes・全 」 | ③向け直す |
| observe_diag.py | 4711 | 読む | REFS | ③向け直す |
| observe_diag.py | 4712 | 読む | REFS | ③向け直す |
| observe_diag.py | 4714 | 読む | REFS | ③向け直す |
| observe_diag.py | 4723 | 読む | REFS | ③向け直す |
| observe_diag.py | 4750 | 読む | REFS | ③向け直す |
| observe_diag.py | 5032 | 読む | REFS | ③向け直す |
| observe_diag.py | 5033 | 読む | fams | ③向け直す |
| observe_diag.py | 5036 | 読む | fams | ③向け直す |
| observe_diag.py | 5039 | 読む | fams | ③向け直す |
| observe_diag.py | 5064 | 持つ | _V9_PERIOD_PATTERNS（名前 4・例 ADX, ATR%, RCI） | ①写す→②消す |
| observe_diag.py | 5092 | 持つ | _V9_PERIOD_PARAMS（名前 1・例 RSI） | ①写す→②消す |
| observe_diag.py | 5102 | 読む | _V9_PERIOD_PATTERNS | ③向け直す |
| observe_diag.py | 5119 | 読む | _V9_PERIOD_PARAMS | ③向け直す |
| observe_diag.py | 5355 | 持つ | _V9_LABEL_TO_FAMILIES（名前 15・例 ADX, ATR%, BB%b） | ①写す→②消す |
| observe_diag.py | 5372 | 読む | _V9_LABEL_TO_FAMILIES | ③向け直す |
| observe_diag.py | 5406 | 持つ | _USE_PATTERNS（名前 15・例 ADX, ATR%, BB%b） | ①写す→②消す |
| observe_diag.py | 5431 | 読む | _USE_PATTERNS | ③向け直す |
| observe_diag.py | 5844 | 読む | json の名前「search_limits.json」 | ③向け直す |
| observe_diag.py | 5848 | 読む | json の名前「部品の n・m に使う数字を recipes/search_limits.json の int_grid から引く（手で」 | ③向け直す |
| observe_diag.py | 6028 | 読む | json の名前「  ★『対応なし』の列だけ、うちの材料に条件の部品を当てた列とも比べる（部品4種＝そのまま／n本前との差／m本の平均／m」 | ③向け直す |
| observe_diag.py | 6068 | 持つ | _HOUKOU2PROP（区分の言葉 8（例 none, reversal, trend）） | ①写す→②消す |
| observe_diag.py | 6073 | 読む | INDICATOR_TABLE | ③向け直す |
| observe_diag.py | 6076 | 読む | INDICATOR_TABLE | ③向け直す |
| observe_diag.py | 6080 | 読む | json の名前「.claude/ratchet/indicator_switch.json」 | ③向け直す |
| observe_diag.py | 6184 | 読む | INDICATOR_TABLE | ③向け直す |
| observe_diag.py | 6196 | 読む | _HOUKOU2PROP | ③向け直す |
| observe_diag.py | 6200 | 読む | _HOUKOU2PROP | ③向け直す |
| observe_diag.py | 6303 | 読む | FAMILY_LINEAGE | ③向け直す |
| observe_diag.py | 6317 | 読む | _OSC_BOUNDS | ③向け直す |
| observe_diag.py | 6318 | 読む | _OSC_PCTL | ③向け直す |
| observe_diag.py | 6488 | 直書き | DI差 | ③向け直す |
| observe_diag.py | 6496 | 直書き | ATR% | ③向け直す |
| observe_diag.py | 6497 | 直書き | ATR% | ③向け直す |
| observe_diag.py | 6543 | 持つ | REGIME_LABELS（区分の言葉 2（例 向き, 強さ）） | ①写す→②消す |
| observe_diag.py | 6678 | 読む | json の名前「signal_families.json」 | ③向け直す |
| observe_diag.py | 6732 | 読む | REGIME_LABELS | ③向け直す |
| observe_diag.py | 6818 | 読む | REGIME_LABELS | ③向け直す |
| observe_diag.py | 6846 | 読む | FAMILY_LINEAGE | ③向け直す |
| observe_diag.py | 6850 | 読む | REGIME_LABELS | ③向け直す |
| observe_diag.py | 6884 | 読む | REGIME_LABELS | ③向け直す |
| observe_diag.py | 6911 | 読む | json の名前「material_ranking.json」 | ③向け直す |
| observe_diag.py | 6993 | 読む | REGIME_LABELS | ③向け直す |
| observe_diag.py | 7040 | 読む | REGIME_LABELS | ③向け直す |
| observe_diag.py | 7075 | 読む | json の名前「material_ranking.json」 | ③向け直す |
| observe_diag.py | 7148 | 読む | REGIME_LABELS | ③向け直す |
| observe_diag.py | 7169 | 読む | REGIME_LABELS | ③向け直す |
| observe_diag.py | 7174 | 読む | REGIME_LABELS | ③向け直す |
| observe_diag.py | 7176 | 読む | REGIME_LABELS | ③向け直す |
| observe_diag.py | 7177 | 読む | REGIME_LABELS | ③向け直す |
| observe_diag.py | 7419 | 直書き | HT_INPHASE% | ③向け直す |
| observe_diag.py | 7461 | 読む | FAMILY_LINEAGE | ③向け直す |
| observe_diag.py | 7473 | 読む | FAMILY_LINEAGE | ③向け直す |
| observe_diag.py | 7496 | 持つ | fams（名前 10・例 LeeMykland, LeeMykland_E36版, 帯VA） | ①写す→②消す |
| observe_diag.py | 7501 | 読む | fams | ③向け直す |
| observe_diag.py | 7503 | 読む | fams | ③向け直す |
| observe_diag.py | 7708 | 持つ | _cases（名前 1・例 W字確定谷） | ①写す→②消す |
| observe_diag.py | 7712 | 直書き | 帯スイング | ③向け直す |
| observe_diag.py | 7712 | 直書き | 帯スイング1時間ATR | ③向け直す |
| observe_diag.py | 7713 | 読む | _cases | ③向け直す |
| observe_diag.py | 7715 | 読む | MATERIAL_FAMILIES | ③向け直す |
| observe_diag.py | 7730 | 読む | _cases | ③向け直す |
| observe_diag.py | 7730 | 読む | _cases | ③向け直す |
| observe_diag.py | 7785 | 読む | REFS | ③向け直す |
| observe_diag.py | 7858 | 読む | REFS | ③向け直す |
| observe_diag.py | 7875 | 直書き | AO% | ③向け直す |
| observe_diag.py | 7878 | 直書き | RCI | ③向け直す |
| observe_diag.py | 7878 | 読む | REFS | ③向け直す |
| observe_diag.py | 7899 | 読む | MATERIAL_FAMILIES | ③向け直す |
| observe_diag.py | 7912 | 読む | json の名前「search_limits.json」 | ③向け直す |
| observe_diag.py | 7915 | 読む | MATERIAL_FAMILIES | ③向け直す |
| observe_diag.py | 7934 | 直書き | ROC | ③向け直す |
| observe_diag.py | 7936 | 直書き | ROC | ③向け直す |
| observe_diag.py | 8360 | 持つ | _fake（名前 1・例 RSI） | ①写す→②消す |
| observe_diag.py | 8362 | 読む | _fake | ③向け直す |
| observe_diag.py | 8374 | 直書き | fractal安値距離% | ③向け直す |
| observe_diag.py | 8374 | 直書き | fractal高値距離% | ③向け直す |
| observe_diag.py | 8374 | 直書き | 高値切り上げ幅% | ③向け直す |
| observe_diag.py | 8375 | 直書き | 安値切り上げ幅% | ③向け直す |
| observe_diag.py | 8375 | 直書き | 構造破断距離% | ③向け直す |
| observe_diag.py | 8429 | 直書き | POC | ③向け直す |
| observe_diag.py | 8429 | 直書き | VAH | ③向け直す |
| observe_diag.py | 8429 | 直書き | VAL | ③向け直す |
| observe_diag.py | 8450 | 直書き | POC | ③向け直す |
| observe_diag.py | 8450 | 直書き | VAH | ③向け直す |
| observe_diag.py | 8450 | 直書き | VAL | ③向け直す |
| observe_diag.py | 8451 | 読む | REFS | ③向け直す |
| observe_diag.py | 8502 | 読む | CONST_REGISTRY | ③向け直す |
| observe_diag.py | 8593 | 直書き | 包み足 | ③向け直す |
| observe_diag.py | 8594 | 直書き | 包み足 | ③向け直す |
| observe_diag.py | 8600 | 直書き | EMA9傾き% | ③向け直す |
| observe_diag.py | 8600 | 直書き | RSI14 | ③向け直す |
| observe_diag.py | 8600 | 直書き | close vs EMA9% | ③向け直す |
| observe_diag.py | 8609 | 直書き | RSI14 | ③向け直す |
| observe_diag.py | 8620 | 読む | REFS | ③向け直す |
| observe_diag.py | 8685 | 直書き | RCI | ③向け直す |
| observe_diag.py | 8707 | 持つ | _want14（名前 3・例 BB幅(20,2.0), RSI21, fib位置20） | ①写す→②消す |
| observe_diag.py | 8708 | 読む | _want14 | ③向け直す |
| observe_diag.py | 8709 | 読む | _want14 | ③向け直す |
| observe_diag.py | 8717 | 読む | _want14 | ③向け直す |
| observe_diag.py | 8745 | 直書き | RSI21 | ③向け直す |
| observe_diag.py | 8777 | 直書き | RCI | ③向け直す |
| observe_diag.py | 8780 | 直書き | RCI | ③向け直す |
| observe_diag.py | 8951 | 読む | json の名前「Entry 候補観察＝場面ID（observe_config.json の scenes・例 S2＝まだ玉のない新候補の」 | ③向け直す |
| observe_diag.py | 8972 | 読む | json の名前「observe_config.json のパス（既定は同ディレクトリ）」 | ③向け直す |
| pre_audit_check.py | 109 | 読む | json の名前「observe_config.json」 | ③向け直す |
| pre_audit_check.py | 113 | 読む | json の名前「recipes/search_limits.json」 | ③向け直す |
| pre_audit_check.py | 114 | 読む | json の名前「/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/s」 | ③向け直す |
| pre_audit_check.py | 115 | 読む | json の名前「/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/s」 | ③向け直す |
| pre_audit_check.py | 116 | 読む | json の名前「/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/s」 | ③向け直す |
| pre_audit_check.py | 117 | 読む | json の名前「/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget」 | ③向け直す |
| pre_audit_check.py | 214 | 読む | json の名前「.claude/ratchet/indicator_switch.json」 | ③向け直す |
| precheck.py | 41 | 持つ | BANDS（名前 2・例 ADX, ATR%） | ①写す→②消す |
| precheck.py | 54 | 直書き | ATR% | ③向け直す |
| precheck.py | 54 | 読む | BANDS | ③向け直す |
| precheck.py | 121 | 直書き | atr_14 | ③向け直す |
| precheck.py | 167 | 直書き | atr_14 | ③向け直す |
| precheck.py | 170 | 読む | BANDS | ③向け直す |
| ratchet_guards.py | 117 | 持つ | vol_keys（名前 1・例 realized_vol） | ①写す→②消す |
| ratchet_guards.py | 118 | 読む | vol_keys | ③向け直す |
| ratchet_guards.py | 120 | 読む | vol_keys | ③向け直す |
| regime_label.py | 47 | 持つ | LABEL_NAMES（区分の言葉 2（例 向き, 強さ）） | ①写す→②消す |
| regime_label.py | 120 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 171 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 172 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 178 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 179 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 220 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 220 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 221 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 287 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 288 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 292 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 293 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 301 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 302 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 306 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 340 | 自前で計算 | rolling | ③向け直す |
| regime_label.py | 578 | 読む | json の名前「search_limits.json」 | ③向け直す |
| regime_label.py | 582 | 読む | json の名前「 の保有の範囲が search_limits.json の hold_range_by_role と違う」 | ③向け直す |
| regime_label.py | 648 | 読む | json の名前「 の保有の範囲が search_limits.json の hold_range_by_role と違う」 | ③向け直す |
| regime_r9_diag.py | 514 | 読む | json の名前「[R9] 成績表 material_ranking.json（札の版 」 | ③向け直す |
| regime_r9_diag.py | 917 | 持つ | _c14（名前 1・例 ADX） | ①写す→②消す |
| regime_r9_diag.py | 919 | 読む | _c14 | ③向け直す |
| report.py | 292 | 持つ | _ind（名前 1・例 atr_14） | ①写す→②消す |
| report.py | 294 | 読む | _ind | ③向け直す |
| report.py | 295 | 持つ | _cjp（名前 3・例 ADX, RSI, atr_14） | ①写す→②消す |
| report.py | 300 | 読む | _ind | ③向け直す |
| report.py | 302 | 読む | _cjp | ③向け直す |
| report.py | 362 | 直書き | atr_14 | ③向け直す |
| report.py | 363 | 直書き | atr_14 | ③向け直す |
| report.py | 367 | 持つ | bands（名前 2・例 ADX, ATR%） | ①写す→②消す |
| report.py | 373 | 読む | bands | ③向け直す |
| tuner_judgement.py | 216 | 直書き | atr_14 | ③向け直す |
| tuner_judgement.py | 828 | 直書き | atr_14 | ③向け直す |
| tuner_judgement.py | 832 | 直書き | atr_14 | ③向け直す |

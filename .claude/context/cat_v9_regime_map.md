# cat_v9_regime_map.md — CAT_v9_regime.py 構造マップ

パス: /Users/tachiharamasako/Documents/GitHub/cat-swing-sniper/strategies/CAT_v9_regime.py

## Exit 条件一覧（run_backtest 内）

| # | exit_reason | 行番号 | 条件サマリー |
|---|------------|--------|------------|
| 1 | MFE_EXIT(P22_SHORT) | L923-950 | P22 SHORT + hold≥TIME_EXIT×0.6 + mfe_max≥20USD |
| 2 | BREAKOUT_CUT(P22_SHORT) | L1003-1016 | P22 SHORT + add==3 + bb_width≥0.03 + rsi≥70 |
| 3 | BREAKOUT_CUT(P23_SHORT) | L1018-1033 | P23 SHORT + add==3 + bb_width≥0.03 + rsi≥70 |
| 4 | SL到達 | L1037-1044 | add≥2 + low<=sl（LONG）/ high>=sl（SHORT） |
| 5 | RSI下降Exit(SHORT) | L1047-1141 | FEAT_SHORT_RSI_REVERSE_EXIT=True + 各種条件 |
| 6 | MFE_STALE_CUT(P22_SHORT) | L1125 | P22 SHORT + add≥5 + hold≥120min + mfe_max<12USD |
| 7 | MAE_CUT(P23_SHORT) | L1152-1168 | P23 SHORT + add≥4 + hold≥300min + high>=entry+50/size |
| 8 | PROFIT_LOCK(P23_SHORT) | L1170-1193 | P23 SHORT + add==5 + armed(mfe≥10) + low<=lock_price |
| 9 | PROFIT_LOCK(P22_SHORT) | L1195-1219 | P22 SHORT + add==5 + armed(mfe≥10) + low<=lock_price |
| 10 | PROFIT_LOCK(P22_SHORT_V2) | L1221-1249 | P22 SHORT + ENABLE=1 + armed(mfe≥ARM_USD) + high>=lock_price |
| 11 | PROFIT_LOCK(LONG) | L1251-1276 | LONG + ENABLE=1 + armed(mfe≥15) + high>=lock_price |
| 12 | P4_DEAD_CUT_30M | L1430-1432 | if False → **実質無効** |
| 13 | STAGNATION_CUT(P4_MFE) | L1443-1459 | P4 LONG + P4_STAGNATION_WIDE_ENABLE=1 + hold≥45min + mfe≤3USD |
| 14 | STAGNATION_CUT(MFE<=1@30m) | L1461-1477 | 全サイド + hold≥30min + mfe≤1USD |
| 15 | P4_BREAK_EXIT | L1479-1510 | P4 LONG + j==entry_i+hold_bars + bb_mid_slope≤-20 |
| 16 | TIME_EXIT（LONG） | L1512-1617 | hold≥hold_limit_min（P4延長ロジック含む） |
| 17 | TIME_EXIT（SHORT） | L1633-1636 | hold≥hold_limit_min |
| 18 | EXIT_GUARD_FORCED | L1659 | 上記全て非該当の場合の強制出口（ガード） |

## 移植版（run_once_v9.py _check_exits）との既知ギャップ（2026-03-24確認）

| ID | 内容 | 優先度 |
|----|------|-------|
| G-1 | BREAKOUT_CUT P22: add==3限定 + bb_width/rsi条件が欠落 | 🔴 |
| G-2 | MAE_CUT: high>=entry+50/size の価格条件が欠落 | 🔴 |
| G-3 | PROFIT_LOCK(P23_SHORT) / PROFIT_LOCK(P22_SHORT)（add==5版）: 未実装 | 🟡 |
| G-4 | P4_BREAK_EXIT: 未実装 | 🟡 |
| G-5 | STAGNATION_CUT 通常: 原本コード30minハードコード、移植版はSTAG_MIN_Mパラメータ参照 → **✅ 30.0に修正済み（2026-03-24）** | ✅ |

## 主要関数の場所

| 関数 | 行番号 | 内容 |
|------|--------|------|
| run_backtest() | L610〜 | メインの Exitループ |
| check_entry_priority() | L219〜 | エントリー判断（cat_v9_decider.py に移植済み） |
| params dict | L2829-2935 | パラメータ一次ソース |
# signal_ledger.md — シグナル候補検証台帳

scripts/analyze_signals.py の実行結果を追記する。
L-118 対応: 干渉率・調整後NET・判定を必ず記録すること。

判定基準:
- GO   : 調整後NET ≥ $3/dt-day かつ 干渉率 < 0.3
- WARN : 調整後NET ≥ $1/dt-day または 干渉率 0.3〜0.5（実装前に Replay 干渉テスト必須）
- NO-GO: 上記以外

| date | signal | ohlcv | replay_csv | regime | side | tp/sl/hold | fires/reg-day | avgHold | interference | raw_net | discount | adj_net | 判定 | memo |
|------|--------|-------|-----------|--------|------|-----------|---------------|---------|--------------|---------|----------|---------|------|------|
| 2026-04-25 | n6_adx50 | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | all | SHORT | 0.01/0.02/120 | 5.50 | 106.8 | 0.134 | -1.40 | 0.3 | -1.35 | NO-GO | N6 smoke test (tp=0.010/sl=0.020/hold=120) |
| 2026-04-25 | n6_adx50 | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | SHORT | 0.01/0.02/120 | 2.81 | 102.5 | 0.261 | +0.02 | 0.3 | +0.02 | NO-GO | N6 DT-only (tp=1%/sl=2%/hold=120) |
| 2026-04-25 | n2_bb_trap | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | SHORT | 0.01/0.02/120 | 15.50 | 109.2 | 0.174 | -3.78 | 0.3 | -3.59 | NO-GO | batch DT tp=1%/sl=2%/h=120 |
| 2026-04-25 | n2_bb_trap | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | LONG | 0.01/0.02/120 | 17.76 | 109.1 | 0.219 | -21.09 | 0.3 | -19.70 | NO-GO | batch DT tp=1%/sl=2%/h=120 |
| 2026-04-25 | n8_donchian | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | SHORT | 0.01/0.02/120 | 16.81 | 103.2 | 0.245 | -5.90 | 0.3 | -5.47 | NO-GO | batch DT tp=1%/sl=2%/h=120 |
| 2026-04-25 | n8_donchian | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | LONG | 0.01/0.02/120 | 14.87 | 108.1 | 0.191 | -28.55 | 0.3 | -26.91 | NO-GO | batch DT tp=1%/sl=2%/h=120 |
| 2026-04-25 | n12_vol_spike | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | SHORT | 0.01/0.02/120 | 25.15 | 105.2 | 0.210 | -10.68 | 0.3 | -10.00 | NO-GO | batch DT tp=1%/sl=2%/h=120 |
| 2026-04-25 | n9_macd_zero | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | SHORT | 0.01/0.02/120 | 11.39 | 108.9 | 0.207 | -2.17 | 0.3 | -2.04 | NO-GO | batch2 DT tp=1%/sl=2%/h=120 |
| 2026-04-25 | n9_macd_zero | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | LONG | 0.01/0.02/120 | 11.38 | 109.6 | 0.239 | -13.91 | 0.3 | -12.91 | NO-GO | batch2 DT tp=1%/sl=2%/h=120 |
| 2026-04-25 | n11_pinbar | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | SHORT | 0.01/0.02/120 | 23.13 | 109.5 | 0.232 | -5.50 | 0.3 | -5.12 | NO-GO | batch2 DT tp=1%/sl=2%/h=120 |
| 2026-04-25 | n11_pinbar | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | LONG | 0.01/0.02/120 | 23.55 | 111.6 | 0.243 | -35.70 | 0.3 | -33.09 | NO-GO | batch2 DT tp=1%/sl=2%/h=120 |
| 2026-04-25 | n13_atr_squeeze | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | SHORT | 0.01/0.02/120 | 0.03 | 120.0 | 0.200 | -0.22 | 0.3 | -0.20 | NO-GO | batch2 DT tp=1%/sl=2%/h=120 |
| 2026-04-25 | n13_atr_squeeze | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | LONG | 0.01/0.02/120 | 0.01 | 120.0 | 0.000 | -0.01 | 0.3 | -0.01 | NO-GO | batch2 DT tp=1%/sl=2%/h=120 |
| 2026-04-25 | n15_adx_di_cross | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | SHORT | 0.01/0.02/120 | 0.13 | 104.4 | 0.167 | -0.84 | 0.3 | -0.80 | NO-GO | batch2 DT tp=1%/sl=2%/h=120 |
| 2026-04-25 | n15_adx_di_cross | BTCUSDT-5m-2025-04-01_03-31_365d.csv | replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv | downtrend | LONG | 0.01/0.02/120 | 0.11 | 112.2 | 0.188 | -0.65 | 0.3 | -0.61 | NO-GO | batch2 DT tp=1%/sl=2%/h=120 |

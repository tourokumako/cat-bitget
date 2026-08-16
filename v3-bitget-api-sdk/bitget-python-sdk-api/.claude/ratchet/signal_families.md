<!-- SIGNAL_FAMILIES hash=02e3b5d9aac19214 gen_signal_families.py が自動生成＝手で書き換えない -->
# signal_families.md — 型の表（許可の一覧・全自動生成・CC の手書きの行ゼロ）

作り（まこさん確定 2026-08-06）＝ 表の本体は広く展開 ／ 削るのは機械生成の禁止だけ ／ 検算は V9 の実物。

## 表の本体（広さ）＝型 8 種 × 部品 535 種 × 時間足 9 本

| 型 | 中身（軸カタログ E-a の逐語） |
|---|---|
| E-a1 | 逆張り＝平均回帰 MR（レンジ端/行き過ぎを fade） |
| E-a2 | 順張り＝モメンタム/トレンドフォロー |
| E-a3 | ブレイクアウト（レンジ/ATH 超え＋出来高） |
| E-a4 | 戻り売り・押し目（プルバック） |
| E-a5 | グリッド（往復を仕組みで刻む） |
| E-a6 | マーケットメイク（両側 maker・在庫制御＝Avellaneda-Stoikov/Cartea・スプレッド収益） |
| E-a7 | order-flow/需給（Institutional Accumulation・Flow Momentum） |
| E-a8 | レンジ内 value（stable range で仕込む） |

部品と時間足＝observe_diag のカタログ（2026-08-06 材料検査済み）の全部。**下の禁止に当たらない組み合わせは全部 許可。**

## そもそもの一覧（目的の4要素＝指標・閾値・時間足・パラメータ・機械の写し）

（指標と時間足の正本＝observe_diag のカタログ。閾値と探索の格子の正本＝recipes/search_limits.json（まこさん承認 2026-08-01『たたき台でOK』・r_min は 2026-08-01 OK で 0.25）。ここは機械の写し）

### 指標 … 535 種（系統ごと・括弧の中は方向の区分）

- **トレンド**（190 種）: ADX7(状態量)、DI差7(順張り値)、ADX14(状態量)、DI差14(順張り値)、ADX21(状態量)、DI差21(順張り値)、MACD線%(12,26)(順張り値)、MACDシグナル線%(12,26,9)(順張り値)、MACDヒスト%(12,26,9)(順張り値)、close vs 転換線%(9)(順張り値)、close vs 基準線%(26)(順張り値)、EMA9傾き%(順張り値)、EMA20傾き%(順張り値)、EMA50傾き%(順張り値)、EMA200傾き%(順張り値)、close vs Supertrend%(10,3.0)(順張り値)、CTI7(順張り値)、DM+%7(順張り値)、DM-%7(状態量)、ERI強気%7(順張り値)、ERI弱気%7(状態量)、INERTIA7(順張り値)、CTI9(順張り値)、DM+%9(順張り値)、DM-%9(状態量)、ERI強気%9(順張り値)、ERI弱気%9(状態量)、INERTIA9(順張り値)、CTI14(順張り値)、DM+%14(順張り値)、DM-%14(状態量)、ERI強気%14(順張り値)、ERI弱気%14(状態量)、INERTIA14(順張り値)、CTI21(順張り値)、DM+%21(順張り値)、DM-%21(状態量)、ERI強気%21(順張り値)、ERI弱気%21(状態量)、INERTIA21(順張り値)、KST(順張り値)、AO%(12,26)(順張り値)、COPC(9,12,26)(順張り値)、KSTシグナル9(順張り値)、MOM%7(順張り値)、MOM%9(順張り値)、MOM%14(順張り値)、MOM%21(順張り値)、PPO(12,26,9)(順張り値)、PPOヒスト(12,26,9)(状態量)、PPOシグナル(12,26,9)(順張り値)、STC(順張り値)、STCstoch(順張り値)、TRIX(7,9)(順張り値)、TRIXシグナル(7,9)(順張り値)、TRIXヒスト(7,9)(状態量)、TRIX(9,9)(順張り値)、TRIXシグナル(9,9)(順張り値)、TRIXヒスト(9,9)(状態量)、TRIX(14,9)(順張り値)、TRIXシグナル(14,9)(順張り値)、TRIXヒスト(14,9)(状態量)、TRIX(21,9)(順張り値)、TRIXシグナル(21,9)(順張り値)、TRIXヒスト(21,9)(状態量)、TSI(12,26,9)(順張り値)、TSIシグナル(12,26,9)(順張り値)、TSIヒスト(12,26,9)(状態量)、VWMACD線%(12,26,9)(順張り値)、VWMACDヒスト%(12,26,9)(状態量)、VWMACDシグナル%(12,26,9)(順張り値)、ALMA20傾き%(順張り値)、DEMA20傾き%(順張り値)、HMA20傾き%(順張り値)、KAMA20傾き%(順張り値)、LINREG20傾き%(順張り値)、FWMA20傾き%(順張り値)、ALMA50傾き%(順張り値)、DEMA50傾き%(順張り値)、HMA50傾き%(順張り値)、KAMA50傾き%(順張り値)、LINREG50傾き%(順張り値)、ALMA200傾き%(順張り値)、DEMA200傾き%(順張り値)、HMA200傾き%(順張り値)、KAMA200傾き%(順張り値)、LINREG200傾き%(順張り値)、LRb20傾き%(順張り値)、MCGD20傾き%(順張り値)、MIDPOINT20傾き%(順張り値)、MIDPRICE20傾き%(順張り値)、PWMA20傾き%(順張り値)、RMA20傾き%(順張り値)、LRslope%20(順張り値)、LRb50傾き%(順張り値)、MCGD50傾き%(順張り値)、MIDPOINT50傾き%(順張り値)、MIDPRICE50傾き%(順張り値)、PWMA50傾き%(順張り値)、RMA50傾き%(順張り値)、LRslope%50(順張り値)、LRb200傾き%(順張り値)、MCGD200傾き%(順張り値)、MIDPOINT200傾き%(順張り値)、MIDPRICE200傾き%(順張り値)、PWMA200傾き%(順張り値)、RMA200傾き%(順張り値)、LRslope%200(順張り値)、MMAR10傾き%(順張り値)、MMAR15傾き%(順張り値)、MMAR25傾き%(順張り値)、MMAR30傾き%(順張り値)、MMAR35傾き%(順張り値)、RAINBOW(2,1)傾き%(順張り値)、RAINBOW(2,2)傾き%(順張り値)、RAINBOW(2,3)傾き%(順張り値)、RAINBOW(2,4)傾き%(順張り値)、RAINBOW(2,5)傾き%(順張り値)、RAINBOW(2,6)傾き%(順張り値)、RAINBOW(2,7)傾き%(順張り値)、RAINBOW(2,8)傾き%(順張り値)、RAINBOW(2,9)傾き%(順張り値)、RAINBOW(2,10)傾き%(順張り値)、SINWMA20傾き%(順張り値)、SSF20傾き%(順張り値)、SWMA20傾き%(順張り値)、T320傾き%(順張り値)、TEMA20傾き%(順張り値)、TRIMA20傾き%(順張り値)、TSF20傾き%(順張り値)、VIDYA20傾き%(順張り値)、VWMA20傾き%(順張り値)、WMA20傾き%(順張り値)、ZLMA20傾き%(順張り値)、SINWMA50傾き%(順張り値)、SSF50傾き%(順張り値)、SWMA50傾き%(順張り値)、T350傾き%(順張り値)、TEMA50傾き%(順張り値)、TRIMA50傾き%(順張り値)、TSF50傾き%(順張り値)、VIDYA50傾き%(順張り値)、VWMA50傾き%(順張り値)、WMA50傾き%(順張り値)、ZLMA50傾き%(順張り値)、SINWMA200傾き%(順張り値)、SSF200傾き%(順張り値)、SWMA200傾き%(順張り値)、T3200傾き%(順張り値)、TEMA200傾き%(順張り値)、TRIMA200傾き%(順張り値)、VIDYA200傾き%(順張り値)、VWMA200傾き%(順張り値)、WMA200傾き%(順張り値)、ZLMA200傾き%(順張り値)、ADXR7(状態量)、DI+7(順張り値)、DI-7(状態量)、DX7(状態量)、AROONU7(順張り値)、AROOND7(状態量)、AROONOSC7(順張り値)、VTXP7(順張り値)、VTXM7(状態量)、ADXR14(状態量)、DI+14(順張り値)、DI-14(状態量)、DX14(状態量)、AROONU14(順張り値)、AROOND14(状態量)、AROONOSC14(順張り値)、VTXP14(順張り値)、VTXM14(状態量)、ADXR21(状態量)、DI+21(順張り値)、DI-21(状態量)、DX21(状態量)、AROONU21(順張り値)、AROOND21(状態量)、AROONOSC21(順張り値)、VTXP21(順張り値)、VTXM21(状態量)、TTM_TREND20(順張り値)、TTM_TREND48(順張り値)、AMAT_LR(状態量)、PSAR加速(状態量)、MEDIAN傾き%20(順張り値)、MEDIAN傾き%50(順張り値)、MEDIAN傾き%200(順張り値)、HT_TRENDMODE(状態量)
- **構造・位置**（144 種）: 高値からの経過バー24(状態量)、安値からの経過バー24(状態量)、形スコア24(V=+/M=−)(反転サイン)、W字(24,0.003)(反転サイン)、高値からの経過バー48(状態量)、安値からの経過バー48(状態量)、形スコア48(V=+/M=−)(反転サイン)、W字(48,0.003)(反転サイン)、高値からの経過バー96(状態量)、安値からの経過バー96(状態量)、形スコア96(V=+/M=−)(反転サイン)、W字(96,0.003)(反転サイン)、close vs EMA9%(順張り値)、close vs EMA20%(順張り値)、close vs EMA50%(順張り値)、close vs EMA200%(順張り値)、close vs SMA20%(順張り値)、close vs SMA50%(順張り値)、close vs SMA200%(順張り値)、close vs VWAP%288(順張り値)、close vs Keltner上%(20,2.0)(順張り値)、close vs Keltner下%(20,2.0)(順張り値)、close vs 24本高値%(順張り値)、close vs 24本安値%(順張り値)、close vs 48本高値%(順張り値)、close vs 48本安値%(順張り値)、close vs 96本高値%(順張り値)、close vs 96本安値%(順張り値)、close vs pivotPP%288(順張り値)、close vs pivotR1%288(順張り値)、close vs pivotS1%288(順張り値)、fib位置20(順張り値)、fib位置96(順張り値)、close vs POC%288(順張り値)、close vs VAH%288(順張り値)、close vs VAL%288(順張り値)、S-Rタッチ数(288,0.003)(状態量)、SMC_SWEEP(反転サイン)、close vs ALMA%20(反転サイン)、close vs DEMA%20(反転サイン)、close vs HMA%20(反転サイン)、close vs JMA%20(反転サイン)、close vs KAMA%20(反転サイン)、close vs LINREG%20(反転サイン)、close vs FWMA%20(反転サイン)、close vs ALMA%50(反転サイン)、close vs DEMA%50(反転サイン)、close vs HMA%50(反転サイン)、close vs JMA%50(反転サイン)、close vs KAMA%50(反転サイン)、close vs LINREG%50(反転サイン)、close vs ALMA%200(反転サイン)、close vs DEMA%200(反転サイン)、close vs HMA%200(反転サイン)、close vs JMA%200(反転サイン)、close vs KAMA%200(反転サイン)、close vs LINREG%200(反転サイン)、close vs HILO%(反転サイン)、close vs HT_TRENDLINE%(反転サイン)、close vs HWMA%(反転サイン)、close vs LRb%20(反転サイン)、close vs MCGD%20(反転サイン)、close vs MIDPOINT%20(反転サイン)、close vs MIDPRICE%20(反転サイン)、close vs PWMA%20(反転サイン)、close vs RMA%20(反転サイン)、close vs LRb%50(反転サイン)、close vs MCGD%50(反転サイン)、close vs MIDPOINT%50(反転サイン)、close vs MIDPRICE%50(反転サイン)、close vs PWMA%50(反転サイン)、close vs RMA%50(反転サイン)、close vs LRb%200(反転サイン)、close vs MCGD%200(反転サイン)、close vs MIDPOINT%200(反転サイン)、close vs MIDPRICE%200(反転サイン)、close vs PWMA%200(反転サイン)、close vs RMA%200(反転サイン)、close vs MAMA%(反転サイン)、close vs FAMA%(反転サイン)、close vs MMAR%10(反転サイン)、close vs MMAR%15(反転サイン)、close vs MMAR%25(反転サイン)、close vs MMAR%30(反転サイン)、close vs MMAR%35(反転サイン)、close vs RAINBOW%(2,1)(反転サイン)、close vs RAINBOW%(2,2)(反転サイン)、close vs RAINBOW%(2,3)(反転サイン)、close vs RAINBOW%(2,4)(反転サイン)、close vs RAINBOW%(2,5)(反転サイン)、close vs RAINBOW%(2,6)(反転サイン)、close vs RAINBOW%(2,7)(反転サイン)、close vs RAINBOW%(2,8)(反転サイン)、close vs RAINBOW%(2,9)(反転サイン)、close vs RAINBOW%(2,10)(反転サイン)、close vs SINWMA%20(反転サイン)、close vs SSF%20(反転サイン)、close vs SWMA%20(反転サイン)、close vs T3%20(反転サイン)、close vs TEMA%20(反転サイン)、close vs TRIMA%20(反転サイン)、close vs TSF%20(反転サイン)、close vs VIDYA%20(反転サイン)、close vs VWMA%20(反転サイン)、close vs WMA%20(反転サイン)、close vs ZLMA%20(反転サイン)、close vs SINWMA%50(反転サイン)、close vs SSF%50(反転サイン)、close vs SWMA%50(反転サイン)、close vs T3%50(反転サイン)、close vs TEMA%50(反転サイン)、close vs TRIMA%50(反転サイン)、close vs TSF%50(反転サイン)、close vs VIDYA%50(反転サイン)、close vs VWMA%50(反転サイン)、close vs WMA%50(反転サイン)、close vs ZLMA%50(反転サイン)、close vs SINWMA%200(反転サイン)、close vs SSF%200(反転サイン)、close vs SWMA%200(反転サイン)、close vs T3%200(反転サイン)、close vs TEMA%200(反転サイン)、close vs TSF%200(反転サイン)、close vs VIDYA%200(反転サイン)、close vs VWMA%200(反転サイン)、close vs WMA%200(反転サイン)、close vs ZLMA%200(反転サイン)、close vs CKSPl%(反転サイン)、close vs CKSPs%(反転サイン)、close vs PMAX%(反転サイン)、close vs PSAR%(反転サイン)、PSAR反転(状態量)、close vs SAREXT%(反転サイン)、close vs MEDIAN%20(順張り値)、close vs MEDIAN%50(順張り値)、close vs MEDIAN%200(順張り値)、close vs ABER_ZG%(順張り値)、ABER位置(順張り値)、close vs ACCBL%(順張り値)、close vs ACCBU%(順張り値)、close vs CE_L%(順張り値)、close vs CE_S%(順張り値)、HWC位置(状態量)、HT_DCPHASE(状態量)
- **オシレーター**（109 種）: RSI7(順張り値)、RSI9(順張り値)、RSI14(順張り値)、RSI21(順張り値)、ROC6(順張り値)、ROC12(順張り値)、ROC24(順張り値)、Stoch%K5(順張り値)、Stoch%D5(順張り値)、Stoch%K9(順張り値)、Stoch%D9(順張り値)、Stoch%K14(順張り値)、Stoch%D14(順張り値)、MFI14(順張り値)、RCI7(順張り値)、RCI9(順張り値)、RCI26(順張り値)、RCI52(順張り値)、BB%b(20,2.0)(順張り値)、BB%b(50,2.0)(順張り値)、zscore_return20(状態量)、zscore_return50(状態量)、BIAS7(順張り値)、AR7(状態量)、CCI7(順張り値)、CFO7(反転サイン)、CG7(状態量)、CMO7(順張り値)、BIAS9(順張り値)、AR9(状態量)、CCI9(順張り値)、CFO9(反転サイン)、CG9(状態量)、CMO9(順張り値)、BIAS14(順張り値)、AR14(状態量)、CCI14(順張り値)、CFO14(反転サイン)、CG14(状態量)、CMO14(順張り値)、BIAS21(順張り値)、AR21(状態量)、CCI21(順張り値)、CFO21(反転サイン)、CG21(状態量)、CMO21(順張り値)、LRSI(0.5)(順張り値)、FISHER(12,9)(順張り値)、FISHERシグナル(12,9)(順張り値)、KDJ%K(5,9)(順張り値)、KDJ%D(5,9)(順張り値)、KDJ%J(5,9)(順張り値)、KDJ%K(9,9)(順張り値)、KDJ%D(9,9)(順張り値)、KDJ%J(9,9)(順張り値)、KDJ%K(14,9)(順張り値)、KDJ%D(14,9)(順張り値)、KDJ%J(14,9)(順張り値)、PGO7(順張り値)、PO7(反転サイン)、PSL7(順張り値)、RSX7(順張り値)、RVGI(7,4)(順張り値)、RVGIシグナル(7,4)(順張り値)、RVGIヒスト(7,4)(状態量)、PGO9(順張り値)、PO9(反転サイン)、PSL9(順張り値)、RSX9(順張り値)、RVGI(9,4)(順張り値)、RVGIシグナル(9,4)(順張り値)、RVGIヒスト(9,4)(状態量)、PGO14(順張り値)、PO14(反転サイン)、PSL14(順張り値)、RSX14(順張り値)、RVGI(14,4)(順張り値)、RVGIシグナル(14,4)(順張り値)、RVGIヒスト(14,4)(状態量)、PGO21(順張り値)、PO21(反転サイン)、PSL21(順張り値)、RSX21(順張り値)、RVGI(21,4)(順張り値)、RVGIシグナル(21,4)(順張り値)、RVGIヒスト(21,4)(状態量)、QQE(順張り値)、QQE_RSIMA(順張り値)、StochRSI%K7(順張り値)、StochRSI%D7(順張り値)、StochRSI%K9(順張り値)、StochRSI%D9(順張り値)、StochRSI%K14(順張り値)、StochRSI%D14(順張り値)、StochRSI%K21(順張り値)、StochRSI%D21(順張り値)、UO(順張り値)、DPO%20(反転サイン)、DPO%48(反転サイン)、EBSW(順張り値)、HT_INPHASE%(順張り値)、HT_QUAD%(状態量)、HT_SINE(状態量)、HT_LEADSINE(状態量)、MSW_SINE(順張り値)、MSW_LEAD(状態量)、open_Z30(順張り値)、high_Z30(順張り値)、low_Z30(順張り値)
- **ボラ**（46 種）: ATR%7(ボラ量)、ATR%14(ボラ量)、ATR%21(ボラ量)、BB幅(20,2.0)(ボラ量)、BB幅(50,2.0)(ボラ量)、realized_vol20(ボラ量)、realized_vol50(ボラ量)、Donchian幅%20(ボラ量)、Donchian幅%48(ボラ量)、ER7(状態量)、ER9(状態量)、ER14(状態量)、ER21(状態量)、SQZ%(順張り値)、SQZ_ON(状態量)、SQZPRO_ON_WIDE(状態量)、SQZPRO_ON_NARROW(状態量)、CHOP7(状態量)、VHF7(状態量)、CHOP14(状態量)、VHF14(状態量)、CHOP21(状態量)、VHF21(状態量)、skew20(状態量)、kurtosis20(状態量)、MAD比20(ボラ量)、skew50(状態量)、kurtosis50(状態量)、MAD比50(ボラ量)、stdev%50(ボラ量)、HWC幅%(ボラ量)、MASSI(状態量)、PDIST%(状態量)、TR%(ボラ量)、THERMO%(ボラ量)、THERMO比(状態量)、CVI7(状態量)、RVI7(順張り値)、UI7(ボラ量)、CVI14(状態量)、RVI14(順張り値)、UI14(ボラ量)、CVI21(状態量)、RVI21(順張り値)、UI21(ボラ量)、HT_DCPERIOD(状態量)
- **出来高**（31 種）: CMF20(順張り値)、OBV傾き10(順張り値)、OBV傾き20(順張り値)、volume_ratio20(状態量)、volume_ratio50(状態量)、PVO(12,26,9)(状態量)、PVOヒスト(12,26,9)(状態量)、PVOシグナル(12,26,9)(状態量)、EFI比10(順張り値)、EOM比10(順張り値)、MARKETFI比10(状態量)、NVI傾き10(順張り値)、PVI傾き10(順張り値)、PVOL比10(状態量)、PVT傾き10(順張り値)、WAD傾き10(順張り値)、EFI比20(順張り値)、EOM比20(順張り値)、MARKETFI比20(状態量)、NVI傾き20(順張り値)、PVI傾き20(順張り値)、PVT傾き20(順張り値)、WAD傾き20(順張り値)、ADOSC比(順張り値)、AOBV_LR(順張り値)、KVO比(状態量)、KVOシグナル比(状態量)、VOSC(状態量)、VFI10(順張り値)、VFI20(順張り値)、出来高変化率%1(状態量)
- **ローソク**（15 種）: 包み足(反転サイン)、孕み足(反転サイン)、pinbar(反転サイン)、連続本数(順張り値)、body比(状態量)、上ヒゲ比(反転サイン)、下ヒゲ比(反転サイン)、BOP(順張り値)、TD_SEQ_UP(順張り値)、TD_SEQ_DN(状態量)、実体幅比10(状態量)、内側バー(反転サイン)、HA実体%(順張り値)、HA上ヒゲ比(反転サイン)、HA下ヒゲ比(反転サイン)

### 時間足 … 9 本

5m、10m、15m、30m、1h、2h、4h、6h、1d

### 閾値 … 分位 **範囲 q10〜q90**（81 通り・★段A の A-5-3 で 9段のメニューから範囲にした）

（閾値は USD の生の値でなく、値決め窓の分位（データを小さい順に並べた何%点か）で引く（H6 価格非依存）。★2026-08-15（段A の A-5-3）に 9段のメニューから範囲（quantile_range）へ変えた。直す前ここに書いてあった理由『9段より細かくしないのは、試す数が増えるほど合格の線が厳しくなる（多重検定の罰）ため』は事実と違う＝合格の線 DSR の N は tuner_stats.py の n_for_dsr ＝ n_eff（実際に走らせた試行を似た動きでまとめた数）＋ 過去の累積試行であって、候補の広さは入っていない）

### 探索のパラメータの格子（正本＝recipes/search_limits.json・まこさん承認 2026-08-01）

| 名前 | 値 | 何の格子か |
|---|---|---|
| count_range | 無制限 | 条件の本数の範囲 |
| role_max | "無制限" | 役割ごとの本数の上限（引き金は常に1本） |
| k_max | 無制限 | 同じ系統を重ねられる上限 |
| depth_max | 無制限 | 入れ子の深さの上限 |
| p_max | 無制限 | 発火経路の数の上限（探索の既定は1経路） |
| int_range | 3 〜 24（小数） | 本数の範囲（傾き・連続などの N） |
| hour_range | 6 〜 18（整数） | 時刻の境界の範囲 |
| hold_range_by_role | {"scalp": {"lo_bars": 1, "hi_bars": 12}, "daytrade": {"lo_bars": 12, "hi_bars": 120}} | 保有時間の上限の範囲（役割ごと・5分足の本数） |
| state_mult_range | 1.0 〜 3.0（小数） | 出口の名前つき定数の倍数の範囲 |
| frac_range | 25.0 〜 75.0（小数） | 部分利確の割合の範囲（%） |
| exit_mult_range | 50.0 〜 150.0（小数） | SL の帯幅の倍数の範囲（%） |
| max_adds_range | 1 〜 5（整数） | 積み増しの回数の範囲 |
| hold_frac_range | 0.25 〜 0.75（小数） | 保有の門＝満期に対する割合の範囲 |
| giveback_range | 0.25 〜 0.75（小数） | 含み益のピークから戻す割合の範囲 |
| loss_cap_range | 0.4 〜 0.8（小数） | 1トレードの最大許容損失の範囲（%） |
| ladder_steps_range | 1 〜 3（整数） | 部分利確の段数の範囲 |
| n_min | 30 | 列の有効標本数の下限（禁止3 の材料） |
| r_min | 0.25 | リスクリワード比の下限 |
| fdr_q | 0.1 | BH 法の偽発見率の線 |

## 追加の部品（D12・2026-08-07）＝カタログの外に在る入口の材料（機械抽出）

### レンジ幾何 … 2 列（W%、帯内位置%）
規則: レンジ幾何の列は kind=ratio（W%・帯内位置%）だけ入口の条件の材料に使える。kind=price（帯の4隅 res_hi/res_lo/sup_hi/sup_lo・mid）は placement の幾何参照専用（H6 価格非依存）＝条件の材料に使えない
根拠: indicator_reference_diag.RANGE_GEO_REF の kind の欄（実行器 engine_tuner_exec.py 152行 G6 が登録済み列だけ通し、259行が ratio 以外を条件の材料に使うのを既に止めている＝その決まりを表にも写した）

### 時間帯 … 2 列（時刻、曜日）
規則: カレンダー由来の列（時刻・曜日）は入口の条件の材料に使える（計算なし・因果性自明）
根拠: indicator_reference_diag.TIME_REF ＋ entry_exit_matrix.md 軸カタログ E-j（逐語＝「時刻と曜日は既存データから列を作れる（材料の列としても追加する）」）

（保有時間などのポジション状態列は出口の材料＝この表（入口の表）の対象外。G2 は件数だけ出す）

## 削る（全部 機械生成・根拠つき）

### 禁止1 向きの条件に使えない部品（区分＝状態量・ボラ量）… 115 種
根拠: indicator_reference_diag の「方向」の欄（2026-08-06 材料検査1＝合成系列＋実データの2本柱で全種検証済み・❌0件）
ADX14、ADX21、ADX7、ADXR14、ADXR21、ADXR7、AMAT_LR、AR14、AR21、AR7、AR9、AROOND14、AROOND21、AROOND7、ATR%14、ATR%21、ATR%7、BB幅(20,2.0)、BB幅(50,2.0)、CG14、CG21、CG7、CG9、CHOP14、CHOP21、CHOP7、CVI14、CVI21、CVI7、DI-14、DI-21、DI-7、DM-%14、DM-%21、DM-%7、DM-%9、DX14、DX21、DX7、Donchian幅%20、Donchian幅%48、ER14、ER21、ER7、ER9、ERI弱気%14、ERI弱気%21、ERI弱気%7、ERI弱気%9、HT_DCPERIOD、HT_DCPHASE、HT_LEADSINE、HT_QUAD%、HT_SINE、HT_TRENDMODE、HWC位置、HWC幅%、KVOシグナル比、KVO比、MAD比20、MAD比50、MARKETFI比10、MARKETFI比20、MASSI、MSW_LEAD、PDIST%、PPOヒスト(12,26,9)、PSAR加速、PSAR反転、PVO(12,26,9)、PVOL比10、PVOシグナル(12,26,9)、PVOヒスト(12,26,9)、RVGIヒスト(14,4)、RVGIヒスト(21,4)、RVGIヒスト(7,4)、RVGIヒスト(9,4)、S-Rタッチ数(288,0.003)、SQZPRO_ON_NARROW、SQZPRO_ON_WIDE、SQZ_ON、TD_SEQ_DN、THERMO%、THERMO比、TR%、TRIXヒスト(14,9)、TRIXヒスト(21,9)、TRIXヒスト(7,9)、TRIXヒスト(9,9)、TSIヒスト(12,26,9)、UI14、UI21、UI7、VHF14、VHF21、VHF7、VOSC、VTXM14、VTXM21、VTXM7、VWMACDヒスト%(12,26,9)、body比、kurtosis20、kurtosis50、realized_vol20、realized_vol50、skew20、skew50、stdev%50、volume_ratio20、volume_ratio50、zscore_return20、zscore_return50、出来高変化率%1、実体幅比10

### 禁止2 カタログ注記による向きの除外 … 6 種
根拠: 2026-08-06 材料検査1 の実測（普通の相場で向きの差が四分位幅の半分以下）＋まこさん OK
安値からの経過バー24、安値からの経過バー48、安値からの経過バー96、高値からの経過バー24、高値からの経過バー48、高値からの経過バー96

### 禁止3 有効標本数の不足（部品×時間足）… 419 組
規則: 値決め窓 549 日で有効標本数 n_eff < 30 の（部品×時間足）は条件の候補にしない
根拠: CP2 監査 4-4 の算術＋search_limits.json の n_min（まこさん OK 2026-08-01）。恒久の接続（検査5 の実測表）は D9 の直しで行う

| 部品 | 時間足 | n_eff |
|---|---|---|
| ADX21 | 1d | 26.1 |
| DI差21 | 1d | 26.1 |
| MACD線%(12,26) | 1d | 21.1 |
| MACDシグナル線%(12,26,9) | 1d | 21.1 |
| MACDヒスト%(12,26,9) | 1d | 21.1 |
| RSI21 | 1d | 26.1 |
| ROC24 | 1d | 22.9 |
| CMF20 | 1d | 27.4 |
| OBV傾き20 | 1d | 27.4 |
| close vs 基準線%(26) | 1d | 21.1 |
| RCI26 | 1d | 21.1 |
| RCI52 | 1d | 10.6 |
| EMA20傾き% | 1d | 27.4 |
| EMA50傾き% | 1d | 11.0 |
| EMA200傾き% | 4h | 16.5 |
| EMA200傾き% | 6h | 11.0 |
| EMA200傾き% | 1d | 2.7 |
| ATR%21 | 1d | 26.1 |
| BB%b(20,2.0) | 1d | 27.4 |
| BB幅(20,2.0) | 1d | 27.4 |
| BB%b(50,2.0) | 1d | 11.0 |
| BB幅(50,2.0) | 1d | 11.0 |
| realized_vol20 | 1d | 27.4 |
| realized_vol50 | 1d | 11.0 |
| Donchian幅%20 | 1d | 27.4 |
| Donchian幅%48 | 1d | 11.4 |
| zscore_return20 | 1d | 27.4 |
| zscore_return50 | 1d | 11.0 |
| volume_ratio20 | 1d | 27.4 |
| volume_ratio50 | 1d | 11.0 |
| 高値からの経過バー24 | 1d | 22.9 |
| 安値からの経過バー24 | 1d | 22.9 |
| 形スコア24(V=+/M=−) | 1d | 22.9 |
| W字(24,0.003) | 1d | 22.9 |
| 高値からの経過バー48 | 1d | 11.4 |
| 安値からの経過バー48 | 1d | 11.4 |
| 形スコア48(V=+/M=−) | 1d | 11.4 |
| W字(48,0.003) | 1d | 11.4 |
| 高値からの経過バー96 | 6h | 22.9 |
| 高値からの経過バー96 | 1d | 5.7 |
| 安値からの経過バー96 | 6h | 22.9 |
| 安値からの経過バー96 | 1d | 5.7 |
| 形スコア96(V=+/M=−) | 6h | 22.9 |
| 形スコア96(V=+/M=−) | 1d | 5.7 |
| W字(96,0.003) | 6h | 22.9 |
| W字(96,0.003) | 1d | 5.7 |
| close vs EMA20% | 1d | 27.4 |
| close vs EMA50% | 1d | 11.0 |
| close vs EMA200% | 4h | 16.5 |
| close vs EMA200% | 6h | 11.0 |
| close vs EMA200% | 1d | 2.7 |
| close vs SMA20% | 1d | 27.4 |
| close vs SMA50% | 1d | 11.0 |
| close vs SMA200% | 4h | 16.5 |
| close vs SMA200% | 6h | 11.0 |
| close vs SMA200% | 1d | 2.7 |
| close vs VWAP%288 | 2h | 22.9 |
| close vs VWAP%288 | 4h | 11.4 |
| close vs VWAP%288 | 6h | 7.6 |
| close vs VWAP%288 | 1d | 1.9 |
| close vs Keltner上%(20,2.0) | 1d | 27.4 |
| close vs Keltner下%(20,2.0) | 1d | 27.4 |
| close vs 24本高値% | 1d | 22.9 |
| close vs 24本安値% | 1d | 22.9 |
| close vs 48本高値% | 1d | 11.4 |
| close vs 48本安値% | 1d | 11.4 |
| close vs 96本高値% | 6h | 22.9 |
| close vs 96本高値% | 1d | 5.7 |
| close vs 96本安値% | 6h | 22.9 |
| close vs 96本安値% | 1d | 5.7 |
| close vs pivotPP%288 | 2h | 22.9 |
| close vs pivotPP%288 | 4h | 11.4 |
| close vs pivotPP%288 | 6h | 7.6 |
| close vs pivotPP%288 | 1d | 1.9 |
| close vs pivotR1%288 | 2h | 22.9 |
| close vs pivotR1%288 | 4h | 11.4 |
| close vs pivotR1%288 | 6h | 7.6 |
| close vs pivotR1%288 | 1d | 1.9 |
| close vs pivotS1%288 | 2h | 22.9 |
| close vs pivotS1%288 | 4h | 11.4 |
| close vs pivotS1%288 | 6h | 7.6 |
| close vs pivotS1%288 | 1d | 1.9 |
| fib位置20 | 1d | 27.4 |
| fib位置96 | 6h | 22.9 |
| fib位置96 | 1d | 5.7 |
| close vs POC%288 | 2h | 22.9 |
| close vs POC%288 | 4h | 11.4 |
| close vs POC%288 | 6h | 7.6 |
| close vs POC%288 | 1d | 1.9 |
| close vs VAH%288 | 2h | 22.9 |
| close vs VAH%288 | 4h | 11.4 |
| close vs VAH%288 | 6h | 7.6 |
| close vs VAH%288 | 1d | 1.9 |
| close vs VAL%288 | 2h | 22.9 |
| close vs VAL%288 | 4h | 11.4 |
| close vs VAL%288 | 6h | 7.6 |
| close vs VAL%288 | 1d | 1.9 |
| S-Rタッチ数(288,0.003) | 2h | 22.9 |
| S-Rタッチ数(288,0.003) | 4h | 11.4 |
| S-Rタッチ数(288,0.003) | 6h | 7.6 |
| S-Rタッチ数(288,0.003) | 1d | 1.9 |
| BIAS21 | 1d | 26.1 |
| AR21 | 1d | 26.1 |
| CCI21 | 1d | 26.1 |
| CFO21 | 1d | 26.1 |
| CG21 | 1d | 26.1 |
| CMO21 | 1d | 26.1 |
| CTI21 | 1d | 26.1 |
| DM+%21 | 1d | 26.1 |
| DM-%21 | 1d | 26.1 |
| ER21 | 1d | 26.1 |
| ERI強気%21 | 1d | 26.1 |
| ERI弱気%21 | 1d | 26.1 |
| INERTIA21 | 1d | 26.1 |
| AO%(12,26) | 1d | 21.1 |
| COPC(9,12,26) | 1d | 21.1 |
| MOM%21 | 1d | 26.1 |
| PGO21 | 1d | 26.1 |
| PO21 | 1d | 26.1 |
| PSL21 | 1d | 26.1 |
| RSX21 | 1d | 26.1 |
| RVGI(21,4) | 1d | 26.1 |
| RVGIシグナル(21,4) | 1d | 26.1 |
| RVGIヒスト(21,4) | 1d | 26.1 |
| PPO(12,26,9) | 1d | 21.1 |
| PPOヒスト(12,26,9) | 1d | 21.1 |
| PPOシグナル(12,26,9) | 1d | 21.1 |
| PVO(12,26,9) | 1d | 21.1 |
| PVOヒスト(12,26,9) | 1d | 21.1 |
| PVOシグナル(12,26,9) | 1d | 21.1 |
| StochRSI%K21 | 1d | 26.1 |
| StochRSI%D21 | 1d | 26.1 |
| TRIX(21,9) | 1d | 26.1 |
| TRIXシグナル(21,9) | 1d | 26.1 |
| TRIXヒスト(21,9) | 1d | 26.1 |
| TSI(12,26,9) | 1d | 21.1 |
| TSIシグナル(12,26,9) | 1d | 21.1 |
| TSIヒスト(12,26,9) | 1d | 21.1 |
| VWMACD線%(12,26,9) | 1d | 21.1 |
| VWMACDヒスト%(12,26,9) | 1d | 21.1 |
| VWMACDシグナル%(12,26,9) | 1d | 21.1 |
| close vs ALMA%20 | 1d | 27.4 |
| ALMA20傾き% | 1d | 27.4 |
| close vs DEMA%20 | 1d | 27.4 |
| DEMA20傾き% | 1d | 27.4 |
| close vs HMA%20 | 1d | 27.4 |
| HMA20傾き% | 1d | 27.4 |
| close vs JMA%20 | 1d | 27.4 |
| close vs KAMA%20 | 1d | 27.4 |
| KAMA20傾き% | 1d | 27.4 |
| close vs LINREG%20 | 1d | 27.4 |
| LINREG20傾き% | 1d | 27.4 |
| close vs FWMA%20 | 1d | 27.4 |
| FWMA20傾き% | 1d | 27.4 |
| close vs ALMA%50 | 1d | 11.0 |
| ALMA50傾き% | 1d | 11.0 |
| close vs DEMA%50 | 1d | 11.0 |
| DEMA50傾き% | 1d | 11.0 |
| close vs HMA%50 | 1d | 11.0 |
| HMA50傾き% | 1d | 11.0 |
| close vs JMA%50 | 1d | 11.0 |
| close vs KAMA%50 | 1d | 11.0 |
| KAMA50傾き% | 1d | 11.0 |
| close vs LINREG%50 | 1d | 11.0 |
| LINREG50傾き% | 1d | 11.0 |
| close vs ALMA%200 | 4h | 16.5 |
| close vs ALMA%200 | 6h | 11.0 |
| close vs ALMA%200 | 1d | 2.7 |
| ALMA200傾き% | 4h | 16.5 |
| ALMA200傾き% | 6h | 11.0 |
| ALMA200傾き% | 1d | 2.7 |
| close vs DEMA%200 | 4h | 16.5 |
| close vs DEMA%200 | 6h | 11.0 |
| close vs DEMA%200 | 1d | 2.7 |
| DEMA200傾き% | 4h | 16.5 |
| DEMA200傾き% | 6h | 11.0 |
| DEMA200傾き% | 1d | 2.7 |
| close vs HMA%200 | 4h | 16.5 |
| close vs HMA%200 | 6h | 11.0 |
| close vs HMA%200 | 1d | 2.7 |
| HMA200傾き% | 4h | 16.5 |
| HMA200傾き% | 6h | 11.0 |
| HMA200傾き% | 1d | 2.7 |
| close vs JMA%200 | 4h | 16.5 |
| close vs JMA%200 | 6h | 11.0 |
| close vs JMA%200 | 1d | 2.7 |
| close vs KAMA%200 | 4h | 16.5 |
| close vs KAMA%200 | 6h | 11.0 |
| close vs KAMA%200 | 1d | 2.7 |
| KAMA200傾き% | 4h | 16.5 |
| KAMA200傾き% | 6h | 11.0 |
| KAMA200傾き% | 1d | 2.7 |
| close vs LINREG%200 | 4h | 16.5 |
| close vs LINREG%200 | 6h | 11.0 |
| close vs LINREG%200 | 1d | 2.7 |
| LINREG200傾き% | 4h | 16.5 |
| LINREG200傾き% | 6h | 11.0 |
| LINREG200傾き% | 1d | 2.7 |
| close vs LRb%20 | 1d | 27.4 |
| LRb20傾き% | 1d | 27.4 |
| close vs MCGD%20 | 1d | 27.4 |
| MCGD20傾き% | 1d | 27.4 |
| close vs MIDPOINT%20 | 1d | 27.4 |
| MIDPOINT20傾き% | 1d | 27.4 |
| close vs MIDPRICE%20 | 1d | 27.4 |
| MIDPRICE20傾き% | 1d | 27.4 |
| close vs PWMA%20 | 1d | 27.4 |
| PWMA20傾き% | 1d | 27.4 |
| close vs RMA%20 | 1d | 27.4 |
| RMA20傾き% | 1d | 27.4 |
| LRslope%20 | 1d | 27.4 |
| close vs LRb%50 | 1d | 11.0 |
| LRb50傾き% | 1d | 11.0 |
| close vs MCGD%50 | 1d | 11.0 |
| MCGD50傾き% | 1d | 11.0 |
| close vs MIDPOINT%50 | 1d | 11.0 |
| MIDPOINT50傾き% | 1d | 11.0 |
| close vs MIDPRICE%50 | 1d | 11.0 |
| MIDPRICE50傾き% | 1d | 11.0 |
| close vs PWMA%50 | 1d | 11.0 |
| PWMA50傾き% | 1d | 11.0 |
| close vs RMA%50 | 1d | 11.0 |
| RMA50傾き% | 1d | 11.0 |
| LRslope%50 | 1d | 11.0 |
| close vs LRb%200 | 4h | 16.5 |
| close vs LRb%200 | 6h | 11.0 |
| close vs LRb%200 | 1d | 2.7 |
| LRb200傾き% | 4h | 16.5 |
| LRb200傾き% | 6h | 11.0 |
| LRb200傾き% | 1d | 2.7 |
| close vs MCGD%200 | 4h | 16.5 |
| close vs MCGD%200 | 6h | 11.0 |
| close vs MCGD%200 | 1d | 2.7 |
| MCGD200傾き% | 4h | 16.5 |
| MCGD200傾き% | 6h | 11.0 |
| MCGD200傾き% | 1d | 2.7 |
| close vs MIDPOINT%200 | 4h | 16.5 |
| close vs MIDPOINT%200 | 6h | 11.0 |
| close vs MIDPOINT%200 | 1d | 2.7 |
| MIDPOINT200傾き% | 4h | 16.5 |
| MIDPOINT200傾き% | 6h | 11.0 |
| MIDPOINT200傾き% | 1d | 2.7 |
| close vs MIDPRICE%200 | 4h | 16.5 |
| close vs MIDPRICE%200 | 6h | 11.0 |
| close vs MIDPRICE%200 | 1d | 2.7 |
| MIDPRICE200傾き% | 4h | 16.5 |
| MIDPRICE200傾き% | 6h | 11.0 |
| MIDPRICE200傾き% | 1d | 2.7 |
| close vs PWMA%200 | 4h | 16.5 |
| close vs PWMA%200 | 6h | 11.0 |
| close vs PWMA%200 | 1d | 2.7 |
| PWMA200傾き% | 4h | 16.5 |
| PWMA200傾き% | 6h | 11.0 |
| PWMA200傾き% | 1d | 2.7 |
| close vs RMA%200 | 4h | 16.5 |
| close vs RMA%200 | 6h | 11.0 |
| close vs RMA%200 | 1d | 2.7 |
| RMA200傾き% | 4h | 16.5 |
| RMA200傾き% | 6h | 11.0 |
| RMA200傾き% | 1d | 2.7 |
| LRslope%200 | 4h | 16.5 |
| LRslope%200 | 6h | 11.0 |
| LRslope%200 | 1d | 2.7 |
| close vs MMAR%25 | 1d | 22.0 |
| MMAR25傾き% | 1d | 22.0 |
| close vs MMAR%30 | 1d | 18.3 |
| MMAR30傾き% | 1d | 18.3 |
| close vs MMAR%35 | 1d | 15.7 |
| MMAR35傾き% | 1d | 15.7 |
| close vs SINWMA%20 | 1d | 27.4 |
| SINWMA20傾き% | 1d | 27.4 |
| close vs SSF%20 | 1d | 27.4 |
| SSF20傾き% | 1d | 27.4 |
| close vs SWMA%20 | 1d | 27.4 |
| SWMA20傾き% | 1d | 27.4 |
| close vs T3%20 | 1d | 27.4 |
| T320傾き% | 1d | 27.4 |
| close vs TEMA%20 | 1d | 27.4 |
| TEMA20傾き% | 1d | 27.4 |
| close vs TRIMA%20 | 1d | 27.4 |
| TRIMA20傾き% | 1d | 27.4 |
| close vs TSF%20 | 1d | 27.4 |
| TSF20傾き% | 1d | 27.4 |
| close vs VIDYA%20 | 1d | 27.4 |
| VIDYA20傾き% | 1d | 27.4 |
| close vs VWMA%20 | 1d | 27.4 |
| VWMA20傾き% | 1d | 27.4 |
| close vs WMA%20 | 1d | 27.4 |
| WMA20傾き% | 1d | 27.4 |
| close vs ZLMA%20 | 1d | 27.4 |
| ZLMA20傾き% | 1d | 27.4 |
| close vs SINWMA%50 | 1d | 11.0 |
| SINWMA50傾き% | 1d | 11.0 |
| close vs SSF%50 | 1d | 11.0 |
| SSF50傾き% | 1d | 11.0 |
| close vs SWMA%50 | 1d | 11.0 |
| SWMA50傾き% | 1d | 11.0 |
| close vs T3%50 | 1d | 11.0 |
| T350傾き% | 1d | 11.0 |
| close vs TEMA%50 | 1d | 11.0 |
| TEMA50傾き% | 1d | 11.0 |
| close vs TRIMA%50 | 1d | 11.0 |
| TRIMA50傾き% | 1d | 11.0 |
| close vs TSF%50 | 1d | 11.0 |
| TSF50傾き% | 1d | 11.0 |
| close vs VIDYA%50 | 1d | 11.0 |
| VIDYA50傾き% | 1d | 11.0 |
| close vs VWMA%50 | 1d | 11.0 |
| VWMA50傾き% | 1d | 11.0 |
| close vs WMA%50 | 1d | 11.0 |
| WMA50傾き% | 1d | 11.0 |
| close vs ZLMA%50 | 1d | 11.0 |
| ZLMA50傾き% | 1d | 11.0 |
| close vs SINWMA%200 | 4h | 16.5 |
| close vs SINWMA%200 | 6h | 11.0 |
| close vs SINWMA%200 | 1d | 2.7 |
| SINWMA200傾き% | 4h | 16.5 |
| SINWMA200傾き% | 6h | 11.0 |
| SINWMA200傾き% | 1d | 2.7 |
| close vs SSF%200 | 4h | 16.5 |
| close vs SSF%200 | 6h | 11.0 |
| close vs SSF%200 | 1d | 2.7 |
| SSF200傾き% | 4h | 16.5 |
| SSF200傾き% | 6h | 11.0 |
| SSF200傾き% | 1d | 2.7 |
| close vs SWMA%200 | 4h | 16.5 |
| close vs SWMA%200 | 6h | 11.0 |
| close vs SWMA%200 | 1d | 2.7 |
| SWMA200傾き% | 4h | 16.5 |
| SWMA200傾き% | 6h | 11.0 |
| SWMA200傾き% | 1d | 2.7 |
| close vs T3%200 | 4h | 16.5 |
| close vs T3%200 | 6h | 11.0 |
| close vs T3%200 | 1d | 2.7 |
| T3200傾き% | 4h | 16.5 |
| T3200傾き% | 6h | 11.0 |
| T3200傾き% | 1d | 2.7 |
| close vs TEMA%200 | 4h | 16.5 |
| close vs TEMA%200 | 6h | 11.0 |
| close vs TEMA%200 | 1d | 2.7 |
| TEMA200傾き% | 4h | 16.5 |
| TEMA200傾き% | 6h | 11.0 |
| TEMA200傾き% | 1d | 2.7 |
| TRIMA200傾き% | 4h | 16.5 |
| TRIMA200傾き% | 6h | 11.0 |
| TRIMA200傾き% | 1d | 2.7 |
| close vs TSF%200 | 4h | 16.5 |
| close vs TSF%200 | 6h | 11.0 |
| close vs TSF%200 | 1d | 2.7 |
| close vs VIDYA%200 | 4h | 16.5 |
| close vs VIDYA%200 | 6h | 11.0 |
| close vs VIDYA%200 | 1d | 2.7 |
| VIDYA200傾き% | 4h | 16.5 |
| VIDYA200傾き% | 6h | 11.0 |
| VIDYA200傾き% | 1d | 2.7 |
| close vs VWMA%200 | 4h | 16.5 |
| close vs VWMA%200 | 6h | 11.0 |
| close vs VWMA%200 | 1d | 2.7 |
| VWMA200傾き% | 4h | 16.5 |
| VWMA200傾き% | 6h | 11.0 |
| VWMA200傾き% | 1d | 2.7 |
| close vs WMA%200 | 4h | 16.5 |
| close vs WMA%200 | 6h | 11.0 |
| close vs WMA%200 | 1d | 2.7 |
| WMA200傾き% | 4h | 16.5 |
| WMA200傾き% | 6h | 11.0 |
| WMA200傾き% | 1d | 2.7 |
| close vs ZLMA%200 | 4h | 16.5 |
| close vs ZLMA%200 | 6h | 11.0 |
| close vs ZLMA%200 | 1d | 2.7 |
| ZLMA200傾き% | 4h | 16.5 |
| ZLMA200傾き% | 6h | 11.0 |
| ZLMA200傾き% | 1d | 2.7 |
| ADXR21 | 1d | 26.1 |
| DI+21 | 1d | 26.1 |
| DI-21 | 1d | 26.1 |
| DX21 | 1d | 26.1 |
| AROONU21 | 1d | 26.1 |
| AROOND21 | 1d | 26.1 |
| AROONOSC21 | 1d | 26.1 |
| CHOP21 | 1d | 26.1 |
| VHF21 | 1d | 26.1 |
| VTXP21 | 1d | 26.1 |
| VTXM21 | 1d | 26.1 |
| DPO%20 | 1d | 27.4 |
| TTM_TREND20 | 1d | 27.4 |
| DPO%48 | 1d | 11.4 |
| TTM_TREND48 | 1d | 11.4 |
| EFI比20 | 1d | 27.4 |
| EOM比20 | 1d | 27.4 |
| MARKETFI比20 | 1d | 27.4 |
| NVI傾き20 | 1d | 27.4 |
| PVI傾き20 | 1d | 27.4 |
| PVT傾き20 | 1d | 27.4 |
| WAD傾き20 | 1d | 27.4 |
| VFI20 | 1d | 27.4 |
| skew20 | 1d | 27.4 |
| kurtosis20 | 1d | 27.4 |
| MAD比20 | 1d | 27.4 |
| skew50 | 1d | 11.0 |
| kurtosis50 | 1d | 11.0 |
| MAD比50 | 1d | 11.0 |
| stdev%50 | 1d | 11.0 |
| close vs MEDIAN%20 | 1d | 27.4 |
| MEDIAN傾き%20 | 1d | 27.4 |
| close vs MEDIAN%50 | 1d | 11.0 |
| MEDIAN傾き%50 | 1d | 11.0 |
| close vs MEDIAN%200 | 4h | 16.5 |
| close vs MEDIAN%200 | 6h | 11.0 |
| close vs MEDIAN%200 | 1d | 2.7 |
| MEDIAN傾き%200 | 4h | 16.5 |
| MEDIAN傾き%200 | 6h | 11.0 |
| MEDIAN傾き%200 | 1d | 2.7 |
| CVI21 | 1d | 26.1 |
| RVI21 | 1d | 26.1 |
| UI21 | 1d | 26.1 |
| open_Z30 | 1d | 18.3 |
| high_Z30 | 1d | 18.3 |
| low_Z30 | 1d | 18.3 |

## 役割×系統×時間足（D1 の対応表・2026-08-07 CC の案＝出典つき・承認の指紋がまこさんの判断の記録）

規則: レンジ系の型（E-a1 逆張り／E-a4 戻り売り・押し目／E-a5 グリッド／E-a8 レンジ内 value）の構造は、役割ごとに下の系統×時間足だけから材料を引く。行が無い型（E-a2・E-a3・E-a6・E-a7）は生成不可
対象の型: E-a1、E-a4、E-a5、E-a8 ／ 行が無い型（生成不可）: E-a2、E-a3、E-a6、E-a7
（根拠（実測・WebResearch）が未収集＝生成不可（fail-closed）。順張り（E-a2）の引き金＝トレンド系は V9 P21 の実物が在るが、局面が下げトレンド＝レンジの表には書かない。材料を揃えたら行を足して再承認）

| 役割 | 使える系統 | 時間足 | 出典 |
|---|---|---|---|
| 引き金 | オシレーター、ローソク | 5m、10m、15m | technical KB §2.4（V9 P3 実物＝『Stoch ゴールデンクロス ← オシレーター系・トリガー』）／range_scalping_kb §3（拒否の確認材料＝反転ローソク足パターン＋モメンタム・『5分足は RSI9』）／technical KB §2.1（『短期足でタイミング』）＝スキャルの保有は分単位（range_scalping_kb §1・§4）＝上位足の引き金では入る瞬間を決められない |
| 環境認識 | トレンド、ボラ、時間帯 | 全部 | technical KB §2.1（『長期足で方向性確認』＝環境認識）／§2.4（V9 P3 実物＝『BB middle slope ← トレンド系・トレンド確認』『ADX ∈ [30,50) ← トレンド系・強さ確認』＝5分足）／WebResearch 2026-08-07（上位足のトレンドフィルタ・ADX でレンジ/トレンドを分類・レンジは ADX 低）※時間足は 5m を含む全部＝V9 の実物が 5m の環境認識で稼いでいるため締め出さない（v9-selftest の原則） |
| 十分性 | ボラ、出来高、需給、オシレーター | 全部 | technical KB §2.4（V9 P3 実物＝『ATR ≥ 250 ← ボラ系・ボラ十分性』）／range_scalping_kb §3（拒否の確認材料に出来高）／§6.7（需給フィルタ＝このプロジェクトで既に効いている確定エッジ）／WebResearch 2026-08-07（ATR のボラゲート＝動かない場面のスキャル失敗を避ける）※オシレーターは行き過ぎの量（zscore_return 等の状態量）を数える用途 |
| 位置 | 構造・位置＋レンジ幾何（extra_parts） | 全部 | range_scalping_kb §3（手順＝『①ゾーンに到達 → ②拒否の確認 → ③エントリー』）／§7（上位足で機械検出したゾーンの間にいる時だけ入口を開く）／レンジ幾何2列と時刻は extra_parts |

## 向きの矛盾の定義（D1 の対応表の向きの部分・2026-08-07 CC の案＝出典つき）

規則: 型の狙う向きと逆の条件を作らない。機械で判定できる4つの決まり

| # | 決まり | 出典 |
|---|---|---|
| DC1 | 順張り値の部品（プラス＝上昇優勢）を side 付きの形（level・diff・slope・slope_avg）で 環境認識・十分性に使うとき、SHORT は below だけ・LONG は above だけ（逆＝狙いと逆の地合いの要求） | V9 P23 実物（SHORT＝『BB中央線 下向き』∩ 陰線・range_scalping_kb §9.1）／V9 P3 実物（LONG＝『BB middle slope > 10』・technical KB §2.4） |
| DC2 | レンジ系の型の引き金のオシレーター（level 形）は、行き過ぎを逆に取る＝SHORT は above かつ 高分位（q70・q80・q90）・LONG は below かつ 低分位（q10・q20・q30） | E-a1 の逐語（『レンジ端/行き過ぎを fade』）／range_scalping_kb §3（『レンジ相場の RSI は 70/30 が有効』）／WebResearch 2026-08-07（MR＝RSI>70 で売り・<30 で買いが入口）※70/30 の絶対値を分位（q70/q30）へ写すのは実装の形式＝絶対値そのものではないことを明示 |
| DC3 | cross の direction は side と揃える＝up は LONG だけ・down は SHORT だけ | V9 P3 実物（Stoch ゴールデンクロス＝LONG の引き金）／V9 P23 実物（stoch デッドクロス＝SHORT の引き金・range_scalping_kb §9.1） |
| DC4 | ローソクの反転サイン・candle_dir は SHORT＝bear だけ・LONG＝bull だけ | range_scalping_kb §3（『ショート＝レジスタンスゾーンで確認された拒否』＝反転ローソク）／V9 P23 実物（陰線 ∩ SHORT・range_scalping_kb §9.1） |

## 承認

- 指紋: None（まこさんの承認の指紋が入るまで、この表は無効（G1 が生成器のコードの書き込みを止める））

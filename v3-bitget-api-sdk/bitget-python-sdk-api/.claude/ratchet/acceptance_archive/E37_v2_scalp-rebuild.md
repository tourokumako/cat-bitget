# acceptance.md — E37 v2（スキャル入口ゼロ設計＝出来高伸び切り×上位足条件×浅スキャル出口）2026-06-29

TARGET: scripts/priority_rebuild/e37_range_scalp_short.py

DESIGN_CONTRACT:
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp_short.py",
  "self_check_calls": ["vol_z", "SCALP_FLOOR", "atr_sl"],
  "must_combine": {"short_entry": ["over", "vol_exh", "rev", "er_ok"]}
}
```

> 設計書: e37_design.md v2（Peterson・base-up 反映）。本 acceptance は実装チェック基準。判定は score.py の数字のみ（CC は net 計算に触れない＝import）。

## A. ヘッダ
- TARGET = e37_range_scalp_short.py（v2 で入口/出口を作り直し・E37 ローカル＝strat_base/E36/E35 触らない）。
- DESIGN_CONTRACT: short_entry が over∩vol_exh∩rev∩er_ok を連結（must_combine・成分欠落で自停止）／self_check_calls=出来高 vol_z・手数料床 SCALP_FLOOR・ATR-SL の識別子。

## B. 深掘り4点
- **① 真因（root cause）**: v1（iter0）の損の本体＝戻らず price が上に走る玉（採点窓 mfe<0.08% の43玉 −$341・probe 確定）。原因＝「dev_z 買われすぎ→ショート」の単純逆張りが BTC で弱く（base-up＝RSI/z-score 逆張りは BTC で機能せず）、出来高の質ゲートも上位足条件も甘くトレンドを fade した。
- **② 期待値分解**: v1 期待値 −$1.38（勝率49.7%×勝ち$4.99 − 敗率×負け$7.68）。v2 は **出来高伸び切り＋反転バーで「戻る過熱」だけ選別**＝勝率を必要勝率（tight R:R の 1/(1+R:R)）側へ上げ、**浅TP＋短time-exit で平均負けを縮める**。動かすレバー＝勝率↑（入口の質）＋平均負け↓（短time・ATR-SL）。
- **③ root か symptom か**: **root**。入口信号そのものを「過熱単独（弱い）」から「過熱＋出来高 climax＋反転＋range/short-regime」へ替える＝患部（戻らない玉を入れていた）直撃（Y）。
- **④ ベースアップ**: ①QuantifiedStrategies＝BTC で RSI/z-score 逆張りは弱い・順張りは効く ②arxiv 2602.00776＝短期反転は order flow/VWAP/流動性（板）由来＝5m OHLCV では出来高/VWAP が代理 ③QuantPedia＝BTC は中期トレンド優勢＝強い上昇を fade しない ④entry_exit_relationship_kb §7/§9/§18/§19＝平均回帰は小さく速く・バリアは ATR/σ・スキャルは短保有。本セッション Read/WebFetch 済。

## C. 変更の単位（v2＝入口ゼロ設計・スキャルの1コヒーレント構築）
- **入口（SHORT）= 次の AND（must_combine）＝「直近の setup（climax）→ 現在の trigger（反転）」を分離**:
  - `over`: **直近 L_LOOK=3 本以内**に dev_z ≥ 学習窓 q0.75（rolling max・**軽い過熱の setup**・v1 の q0.90 より浅い）。
  - `vol_exh`: **直近 L_LOOK=3 本以内**に vol_z ≥ 1.0（rolling max・**出来高スパイク＝買い climax の伸び切り**・質の主役・a-priori）。
  - `rev`: **現在バー**が反転（close<open ∧ close<前close＝下げに転じた trigger）。
  - `er_ok`: ER < 学習窓分位（レンジ regime）∧ `macd_ok`: 1h MACD≤0（SHORT 寄り＝上位足条件・強い上昇を fade しない）。
  - ＝v1 の box（in_box）・遅い %K は廃止。**過熱＆出来高 climax は「直近に起きた」を取り、反転バーで今のトリガを取る（同一バー要求の機構ミスを回避＝base-up の exhaustion→reversal は別バー）**。過熱は浅く頻度。L_LOOK は a-priori（climax→反転の近接窓・15分）。
- **出口（スキャル＝浅く速く）**:
  - TP（TP_FILLED・maker）: 平均（SMA）へ戻り＝小さい戻りで即利確。**手数料床 SCALP_FLOOR=0.0008（0.08%≒実 maker 往復0.028%の約3倍）を超える時だけ武装**（手数料負け回避）。
  - 時間切れ（TIME_EXIT・taker）: 初回 entry から **T_MAX=6本（30分）**（v1 60分より短い）。
  - SL（SL_FILLED・maker＝V9 placePosTpsl 指値）: entry×(1 + 1.5×atr_pct)＝**ATR スケール**（固定%でない・base-up §18・k_sl=1.5 a-priori）。
  - size: UNIT 0.024・MAX_ADDS=1（単発）。
- **★疑似シミュ由来の固定値ゼロ宣言**: probe（Part A/B）は当たり付け専用＝採否でない。(a) 過熱 q0.75・ER 分位は**学習窓分位**（採点窓不参照）／出来高 vol_z≥1.0・床0.08%・k_sl1.5・T_MAX6 は **a-priori（出来高σ・実コストの倍数・ATR 倍率・スキャル保有＝構造/コスト由来）**＝採点窓で最良値を選ぶスイープでない（L-267 非該当）。(b) probe の特定数値（件数・mfe帯）を閾値に焼いていない。(c) 採否は **実エンジン両窓 score.py**。
- **過去の不再演**: 「切る/早切り/片流れ判別」系（L-309・5回）でない＝入口の質と浅出口。freq-iter2（入口だけ広げ長保有で崩壊）でない＝出口を短く・出来高で質を担保。
- **★ARC マーカー**:
  `<!-- ARC order=13 iter="E37 v2 scalp-rebuild" 前提="新戦略E37・入口ゼロ設計" 採否="検証中" base_csv="trades_e37_range_scalp_short_v1_002" score_csv="" train_csv="" 狙い="BTCで弱い単純逆張りを脱し、出来高climaxの伸び切りで戻る過熱だけをショート・浅TP/短time-exit/ATR-SLで速く回しスキャル頻度と黒字を出す" 内容="入口を 直近3本以内の over(dev_z≥q0.75浅)∩vol_exh(vol_z≥1スパイク=climax setup)∩現在barのrev(反転trigger)∩er_ok∩macd_okへ作り直し(box/遅%K廃止・同一bar要求の機構ミス回避)・出口=SMA浅TP(床0.08%)/T_MAX6本/ATR-SL(1.5×)" 方法="smoke会計保存→学習窓--diagnosticで件数/breakeven/出来高ON-OFF対照→precheck→両窓score.pyでv1(-266)超え＋件数E36(1.05)超え" -->`

## D. 審判（score.py / eval_engine）整合
- **新 exit_reason を出すか**: 出さない。TP_FILLED（maker）/ TIME_EXIT（taker）/ **SL_FILLED（maker・MAKER_EXIT_REASONS に登録済＝V9 placePosTpsl 指値）**。全て登録済＝score.py 改造・既知答えテスト再pass 不要（出戻り防止）。
- **コスト種別**: TP=maker・SL=maker（指値）・time-exit=taker+slip（_record の is_taker 判定＝MAKER_EXIT_REASONS で自動）。
- **judge 不変**（H13・触れない・net は import のみ）。
- **命名規約**: e37_range_scalp_short.py（既存・--tag で連番＝require_tag_for_experiment クリア・pdca_mark e3N 検知）。
- **サイドカー params.json**: 新パラメータ（過熱分位/vol_z/床/T_MAX/k_sl/Entry・Exit ロジック）を params_sidecar に出す（report 節0 自動表示）。
- **共通の書き出し処理 / strat_base**: `_output_and_report`・load_5m・_verify_cap・_funding_cost・定数を strat_base から import（命名/archive/上書き防止 踏襲・E35/E36 と同）。

## E. §4.6 ハード制約 照合
- **H1** cap: MAX_ADDS=1・size 0.024≤0.12＋_verify_cap 実測 assert。
- **H2** leak: dev_z/vol_z/ER/atr/反転バーは当該足まで・1h は確定足 resample（attach_upper_tf）・出口は約定 bar の次以降・負shift/中央窓 grep assert。
- **H5** 約定: entry=指値maker TTL3 / TP=指値maker / SL=指値maker / time-exit=成行taker+slip。
- **H6** 価格非依存: dev_z/ER/vol_z/atr_pct/床%＝無次元。USD 絶対値の閾値/ラベルなし。
- **H8** 期間: 過熱/ER/vol 分位は学習窓(<2025-03)fit・採点 2025-06〜2026-02・封印不参照。
- **H13** judge 固定。
- **H15** ボラ逃げ: 方向＝過熱＋出来高 climax＋反転（方向シグナル）。vol_z/atr は質ゲート・出口幅＝大きさ予測でない・SHORT 単独。
- **H16** 不再演: 切る系/freq-iter2 型でない（上記C）。

## F. 受け入れ判定（採点前ゲート）
- **自己検査**: ①smoke で会計保存（戦略の自作集計 gross/fee/net が eval_engine と一致）②cap≤0.12 実測 ③leak grep pass ④**出来高 ON/OFF 対照**（vol_exh を外すと net/勝率が悪化＝H-d＝出来高が「戻る過熱」を選別している確認・smoke）⑤must_combine 自停止（成分を1つ抜くと停止）。
- **件数/日（一級・スキャル・最優先）**: 採点窓で **E36（1.05）を明確に上回るスキャル頻度（目安 ≥2〜3/日）**。増えなければスキャル要件未達＝採用せず（地面は維持・次の作り込みへ・ROLE_CHECK e37=scalp）。--diagnostic で先に件数確認。
- **学習窓で純増を先に**（採点窓 不参照・H8）: precheck breakeven >1（手数料負け解消）＋ time-exit 比率が v1（87%）から下がる。
- **公式判定は score.py 両窓**: 採点窓で v1（−$266）超え＝黒字側＋件数スキャル＋件数×avg 両立（freq-iter2 型崩壊でない）を確認するまで「効いた」と言わない。
- **degenerate でない**: 件数が増える（薄めて損を小さく見せるのでない）。

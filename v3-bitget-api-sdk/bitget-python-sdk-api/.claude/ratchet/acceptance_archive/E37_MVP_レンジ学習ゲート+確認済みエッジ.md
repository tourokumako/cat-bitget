TARGET: scripts/priority_rebuild/e37_range_scalp.py

# acceptance — E37 レンジ・スキャル MVP（入口を確認済みエッジ＋レンジ学習ゲートに差し替え）

役割: E37＝レンジ局面・スキャル型（件数を上げて小さく多数取る＝高頻度が役割・§1.2.1）。E36（デイトレ）と別戦略。
方針: E37 v2（出来高スパイク fade SHORT）の入口を、両窓で手数料を超えた確認済みレンジ逆張りエッジ＋S/R幾何のレンジ学習ゲートに差し替える。判定は最後に実エンジン両窓 score.py。

## 深掘り4点
- **真因（root cause）**: E37 v2 の net赤の真因は ①戦略欠陥＝入口の向きが逆（analysis N11: SL233件の含み益≧含み損が4%＝出来高スパイク fade SHORT が上昇継続に轢かれてSL）。②執行（手数料負け・breakeven0.45）は入口が当たれば TP玉 +$516 が示す通り解ける。根は「入口が方向を当てられていない」こと（v1/v2 の2例＝N11 方向ミス）。
- **期待値分解**: v2 は必要勝率57.8% vs 実38%＝不足19.8pt（N7）。動かす主レバーは勝率（方向の的中）。平均勝ち$3.52・平均負け$4.82。入口を両窓+の確認済みエッジに差し替えて勝率を上げる（平均勝ち/負けの微調整＝symptom患いはしない）。
- **root か symptom か**: root（入口の方向）を直す。SL幅/TP幅の微調整（symptom）は方向ミスが主因のため患い＝やらない（Y=root）。
- **ベースアップ**: (i) 前セッション regime_scalp probe＝確認済みエッジ（レンジ日ゲート時の下端＋強気ダイバ＋高ATR）が両窓で手数料超え・OOS頑健。(ii) WebResearch＝BTC は順張り優位・逆張りは regime 条件付きでのみ有効（[QuantPedia BTC trend vs MR](https://quantpedia.com/revisiting-trend-following-and-mean-reversion-strategies-in-bitcoin/)）・逆張りは z-score±2σ/RSI/バンドで入口・ADF/半減期でレンジ確認（[QuantInsti mean-reversion](https://blog.quantinsti.com/mean-reversion-strategies-introduction-building-blocks/)）・メタラベリングは一次で方向/二次で取捨＋サイズ（[Hudson&Thames](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/)）。(iii) analysis N10-N12＝stoch_k 両窓再現/atr_pct 両窓不一致。

## ★疑似シミュ由来の固定値ゼロ宣言
設計の各値の出所を1つずつ明示（probe の特定数値を焼かない・採否は probe でなく実エンジン両窓 score.py）:
- **range_score 閾値 THR** ＝ 学習窓の range 比率に一致させる分位（a-priori base-rate match・ラベルに sweep で合わせない）。probe の AUC/一致率を焼かない。
- **dev_z 下端 Z_LO ＝ 学習窓 q25 / 上端 Z_HI ＝ 学習窓 q75**（a-priori 分位・採点窓不参照）。
- **ATR_HI ＝ 学習窓 q2/3**（a-priori 分位）。
- **TP/SL ＝ ATR比・SCALP_FLOOR ＝ 建値比%**（分析の構造由来 a-priori・固定USD値でない・H6）。
- 確認済みエッジの数値（+bps）は仮説の動機であり、設計の固定閾値に焼かない。

## やること（実装仕様）
1. **共通土台**: `strat_base` から load_5m / _verify_cap / _funding_cost / _output_and_report / 取引所・予算定数 を import。`ratchet_io` の --tag 連番で出力（採用前＝毎回タグ）。`params_sidecar.write_sidecar` で使用パラメータを出力（report 節0）。個別に命名/archive/コスト定数を書かない（E35/E36 が手本）。
2. **期間**: `from periods import`（TRAIN_END/SCORE_START/SCORE_END/SEAL_START）。自前の日付リテラル禁止（H8・require_period_source）。
3. **レンジ学習ゲート range_score（構造レバー・関門の答え）**: `e35_box.add_box_features` で S/R幾何（box_strength 5m/1h/4h・box_sup/res_dist）＋ causal な donchian幅・往復回数（過去W=288本）を作る。教師＝`regime_ground_truth_daily_human.csv` の range ラベル。`LogisticRegression` を**学習窓の行だけで fit**（採点窓は不参照・leak-safe）・全行に range_score を predict。THR は学習窓の range 比率分位（a-priori）。特徴は causal（過去のみ）。
4. **入口（両サイド・確認済みエッジ）**:
   - `long_sig` = (range_score≥THR) ∧ (dev_z≤Z_LO) ∧ bull_div ∧ (atr_pct≥ATR_HI)
   - `short_sig` = (range_score≥THR) ∧ (dev_z≥Z_HI) ∧ bear_div ∧ (atr_pct≥ATR_HI)
   - bull_div（強気ダイバ）= 価格が12本安値を更新 ∧〔taker_ls あり→ taker_ls は12本安値を更新せず ／ taker_ls 無し(2026-01以降)→ RSI14 が直近安値時の値より高い（price/RSI fallback）〕。bear_div は mirror。
   - dev_z=(close−SMA20)/std20 ／ atr_pct=ATR14/close×100（H6 価格非依存）。
5. **出口（maker・スキャル短保有・新 exit_reason を作らない）**:
   - `TP_FILLED`（maker指値）= SMA20 への戻りで即利確（浅TP）。建値比 SCALP_FLOOR 超のときだけ TP を武装（小TPの手数料割れ防止）。
   - `TIME_EXIT`（成行taker）= 初回entryから 6本=30分で撤退（スキャル短保有・v2 の time-exit 87%持ちすぎを短縮）。
   - `SL_FILLED`（maker指値）= 建値±1.5×ATR で損切り（ATRスケール）。
   - 全て v2 で score.py 登録済の既存 exit_reason（＝新規登録不要・D審判整合）。
6. **サイズ**: 0.024 BTC 固定（比較用・H10）・MAX_ADDS=1（単発スキャル）。cap 合計 0.12 を `_verify_cap` で実測（H1）。
7. **出力**: `_output_and_report` で trades CSV＋report/analyze/png。--tag で連番。

## DESIGN_CONTRACT
```json
{
  "impl_file": "scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["from periods import", "add_box_features", "LogisticRegression", "range_score", "regime_ground_truth_daily_human", "TP_FILLED", "SL_FILLED", "TIME_EXIT", "write_sidecar", "_verify_cap"],
  "must_combine": {"long_sig": ["range_score", "dev_z", "atr", "div"]}
}
```

## D 審判整合（出戻り防止）
- **新 exit_reason を出すか → NO**（TP_FILLED / SL_FILLED / TIME_EXIT は v2 で score.py 登録済＝再登録不要）。
- コスト種別: entry 指値maker ／ TP・SL 指値maker ／ TIME 成行taker+slip（eval_engine の _TAKER_REASONS={"TIME","ACTIVE"} と一致）。
- judge（score.py / eval_engine）は触らない（H13）。

## §4.6 ハード制約 照合
- **H1** cap: `_verify_cap` で任意 t の sum(active BTC)≤0.12 を実測（違反は採点拒否）。
- **H2** leak: 特徴量 causal（過去のみ）・range_score の fit は学習窓の行のみ・出口判定は eval_engine が次bar以降。`shift(-` / `center=True` 不使用。
- **H5** 約定: entry 指値maker TTL3 ／ TP・SL maker ／ TIME taker（eval_engine.simulate_trade）。
- **H6** 価格非依存: dev_z・atr_pct・box系=%/比率、TP/SL=ATR比・SCALP_FLOOR=建値比%、divergence=符号のみ。USD絶対値の閾値なし。
- **H8** 期間: `from periods import`。学習窓でのみ fit・採点窓は評価のみ・封印不参照。
- **H13** judge固定（改造なし）。
- **H15** ボラ逃げ禁止: 方向は dev_z（レンジ内の位置）＋divergence（需給/価格の背離）＋range_score（S/R幾何）が決める。atr_pct は「高ATR時のみ入口を許すフィルタ」であって方向スコアの主役ではない（将来サイズにも回す）。＝方向は位置/ダイバ、ボラはフィルタ＝軸1整合。ラベルは方向ベース（net金額/MFEの大きさで学習しない）。
- **H16** 1変更: E37 の入口を1つ新設。過去に不採用となった手（v1/v2 の出来高fade＝入口の向きが的中しない・N11 方向ミス／L-308/L-309 の切る/判別系）の再演でない（入口新設・別種＝確認済みレンジ逆張り）。

## F 受け入れ判定（採点前ゲート）
- **自己検査**: (a) range_score の fit が学習窓の行のみか（leak grep）(b) cap≤0.12（`_verify_cap`）(c) exit_reason が既存3種のみ (d) --smoke で恒等でなく発火する。番人＝わざと壊して落ちるかをメタ確認。
- **学習窓で純増を先に測る**（採点窓不参照）→ プラスかつ非degenerate なら採点。
- **公式判定＝score.py 両窓**（CC は net 計算に触れない＝import のみ）。地面＝E37 v2 net−$936／月−$104 を明確に上回ること、できれば黒字。**両窓で改善を確認するまで「効いた」と言わない**。
- **件数/日（一級基準・スキャル役割）**: E37 v2 は 2.08/日。MVP は両サイド化＋レンジ日で候補を出し、**件数/日が現状を上回る**（E36 1.05/日を超え、できれば v2 の 2.08/日以上）ことを合格条件にする。件数/日が現状を下回れば degenerate 扱いで不採用。件数が不足なら直後の iteration で取り方（ブレイク/継続）を足して件数/日を上げる（役割固定・スキャル頻度）。
- **degenerate 点検**: near-inaction（ほぼ無取引で損が小さいだけ）でないか（件数/日と net の両方で確認）。

<!-- ARC order=14 iter="E37 MVP レンジ学習ゲート+確認済みエッジ" 前提="E37 v2(出来高fade)は手数料負け・入口を別種へ差し替え" 採否="未(実装前)" base_csv="trades_e37_range_scalp_short_v2_003_score.csv" score_csv="" train_csv="" 狙い="v2 の方向ミス(N11)を、両窓で手数料を超えた確認済みレンジ逆張りエッジ+S/R幾何のレンジ学習ゲートに入口を差し替えて直す" 内容="レンジ判定=S/R幾何のLogisticRegression学習スコア/入口=両サイド 下端上端+ダイバ+高ATR/出口=maker浅TP+30分TIME+ATR-SL" 方法="学習窓でfit・両窓score.pyで採否・件数/日を一級基準" -->

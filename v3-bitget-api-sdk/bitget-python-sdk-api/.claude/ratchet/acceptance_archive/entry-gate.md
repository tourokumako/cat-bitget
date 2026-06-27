TARGET: scripts/priority_rebuild/e36_short_oscillation.py

# acceptance — E36 entry-gate: 新規 SHORT entry を「戻る/片流れ」入口判別器でゲート

DESIGN_CONTRACT:
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e36_short_oscillation.py",
  "self_check_calls": ["entry_gate", "_entry_feat_vec", "_egm"]
}
```

---

## 設計（1レバー・entry-gate）
広い入口（nofloor ON＝%K>70 下限なし下降のみ）で SHORT 候補を増やし、**新規 entry を建てる瞬間**に、入口時点の特徴だけで学習した二次分類器（戻る label=1 / 片流れ label=0）の predict が θ 未満（=片流れ判別）なら、その新規 entry を**建てない**（de Prado メタラベリング・入口版）。add は別ゲート（本レバーは新規 entry のみ）。

- **新しい入口専用分類器**（既存 hold-ML 判別器とは別物）: 既存 hold-ML は保有経路特徴（bars_held/unreal_pct/dist_to_tp）を使うので入口時点では 0 で無意味。入口時点だけで決まる特徴で別の booster を学習する。
- **入口特徴 `_entry_feat_vec`（全て当該バー i≤entry の値＝leak-safe・%/比率＝H6）**: 箱 5m/1h/4h の S/R・箱幅W・ER・stoch_k・stoch_d・ADX・chop・bb_slope_pct・atr_pct・1h MACD符号。
- **ラベル**: 教師 run（nofloor ON・entry-gate OFF）の各玉を exit_reason で二値化。戻る＝{TP_FILLED, EDGE_TP, CENTER_LOCK}→1 / 片流れ（時間切れ・SPIKE_SL・BOX_BREAK_SL 等）→0。学習は entry_time<TRAIN_END の玉のみ（H8）。
- **適用点**: `run_continuous` の `open_or_add`、`pos[side] is None`（=新規建て）の SHORT 分岐。`entry_gate is not None ∩ side=="SHORT" ∩ _egm.predict(_entry_feat_vec(...,i)) < _egth` → return（建てない）。booster/feats/θ を `_egm,_egf,_egth` に unpack。add 分岐（pos 既存）は本レバー対象外。
- **θ 選定**: 学習窓<2025-03 で `ENTRY_GATE_GRID=[0.30,0.40,0.50,0.60,0.70,0.80]` をスイープし net 最大の θ* を採用。OFF を基準に含め、改善時のみ採用（採点窓不参照 L-267）。
- **新パラメータ `entry_gate=None` で既定 OFF＝base freq-iter1 と byte 一致（恒等）**。primary を広げるのは `--rev-nofloor` 既存フラグ（本レバーは entry_gate のみ追加）。
- **新 exit_reason を出さない**（建てる/建てないだけ・出口ラベル不変）→ score.py 改変不要（D 出戻りなし）。

## 取引所仕様の整合（exchange_spec ★決済方法 / cat_requirements §6.1・6.1.1 read 済）
- 予算 0.12 BTC は**全建玉の合計上限**（1建玉でない・H1）。本レバーは新規を建てない方向＝合計を増やさない（cap 余裕増）。
- 同サイド SHORT は1ポジに merge・平均建値（add＝平均建値の積み上げ・最大5段）。本レバーは「新規の1ポジ目を建てるか」のゲート＝merge 構造・add・部分決済（複数 TP scale out）は不変。
- 決済（全体/部分・EDGE_TP/CENTER_LOCK/PARTIAL_TP 等）は一切変えない（入口だけ）。

## ★疑似シミュ由来の固定値ゼロ宣言（必須）
probe（疑似シミュ・静的後処理）は **あたり付け専用＝決定的根拠でない**。各値の出所:
- **θ**: probe 値を焼かない。実エンジンの**学習窓グリッド選定**（ENTRY_GATE_GRID・OFF基準・採点窓不参照）。
- **入口特徴の閾値**: 固定値で線引きしない（atr_pct>X 等を置かない）。木が複数特徴の AND で学習（N10 固定値手調整禁止と整合）。
- **predict**: 木が学習した確率（固定値でない）。
- **採否**: AUC や probe の数字を根拠にしない。**実エンジン再走＋両窓 score.py の数字だけ**で決める（STRUCT_SL 近似 +$895 が実エンジンで消失した轍）。

## ★ARC マーカー（改善アーク自動生成の源・承認時に凍結保存）
<!-- ARC order=8 iter="entry-gate" 前提="nofloor ON" 採否="採用に至らず" base_csv="trades_e36_short_oscillation_5m_shortset1_score.csv" score_csv="trades_e36_short_oscillation_entrygate_008_score.csv" train_csv="trades_e36_short_oscillation_entrygate_008_train.csv" 狙い="nofloor で広げた間口を質を保って活かし片流れ時間切れ −$1,053 を削る（入口で戻る玉だけ通す）" 内容="新規 SHORT entry を入口時点特徴の二次分類器（戻る/片流れ）でゲート＝predict<θ は建てない（de Prado メタラベリング・入口版）" 方法="入口専用 booster を学習窓 fit・θ 学習窓グリッド選定→両窓 score.py で base $549 超え＋非degenerate・守る勝ち玉 133玉+$1,804 を弾かないか確認" -->

## B. 深掘り4点
- **① 真因**: base freq-iter1 の最大出血＝片流れ時間切れ −$1,053（J節 gross −$946 本体＝①戦略欠陥＝入口が片流れ方向を拾う）。nofloor で間口を広げると片流れ新規が増え net 悪化（freq-iter3 $497<$549）。freq-iter3 の add ゲートは新規 entry の片流れを止められなかった。
- **② 期待値分解**: 平均負け（base $19.36）を、片流れ新規を建てないことで縮める。勝率（76.1%）・平均勝ち（$8.59）・fat-tail（+$339）は触らない。狙い＝平均負けの縮小＋（nofloor の件数を質を保って加える）。
- **③ root か symptom か**: root。出口で損切り（symptom 患い＝戻り玉を巻き込む・2回失敗）でなく、片流れを**建てない**＝損の発生源を断つ。N9 出口効率正常（0.63）も「入口を直せ」を支持。
- **④ ベースアップ**: メタラベリング（de Prado・Joubert）＝二次モデルが primary の false positive を弾き勝ち玉を残す [Hudson&Thames](https://hudsonthames.org/meta-labeling-a-toy-example/)。先例 E8（P23 入口メタラベル AUC 0.733）。過剰適合警告＝学習窓で全選定を閉じ両窓乖離で検出 [arxiv 2604.15531](https://arxiv.org/html/2604.15531v1)。

## C. 変更の単位（H16）
- 変更は **1レバー**（entry_gate）。既定 OFF で恒等（entry_gate=None で base と byte 一致）。自己検査で確認。
- 過去に採用に至らなかった手の不再演: DYING_CUT/STRUCT_SL は**出口で切る**（戻り勝ち玉を巻き込む）／freq-iter3 は **add** をゲート（新規 entry は素通り）。本案は**新規 entry を建てる前にゲート**＝適用点が出口・add → 新規 entry（差分1行）。
- filter only で勝ち玉を削る P23 リスク＝両窓 net additive で確認（⑨巻き込み）。

## D. ★審判（score.py / eval_engine）整合
- **新 exit_reason を出すか？ → NO**（建てる/建てないだけ）→ score.py 登録不要・既知答えテスト再 pass 不要。
- entry/exit のコスト種別（maker/taker）は変わらない。judge の計算式に触れない（H13）。
- サイドカー（params.json）に entry-gate（入口専用判別器・θ 学習窓選定・特徴一覧）を Entry ロジックとして追記（report 節0 自動表示・read 専用）。
- 出力は共通の書き出し処理（_output_and_report・ratchet_io）＝--tag で連番・base 上書きしない。E36 ファイルのみ（E35/strat_base 不変）。
- 命名規約: 実験は既存 e36_short_oscillation.py（pdca_mark 検知済）・分析 probe を使うなら *_probe.py（python 実行時）。

## E. §4.6 ハード制約 照合
- **H1 cap**: 新規を建てない＝玉が減る方向→合計 0.12 を超えない。_verify_cap で実測。
- **H2 leak**: `_entry_feat_vec` は当該バー i≤entry の値のみ（leak-safe）。θ は学習窓 fit（採点窓不参照）。ラベルは exit_reason＝教師の答え（既存 hold-ML と同じ扱い・特徴でない）。run_e36 冒頭の `shift(-`/`center=True` grep assert で担保。
- **H5 約定**: 変更なし（建てる時は既存の指値 maker・TTL3・不約定モデル不変）。
- **H6 価格非依存**: 入口特徴は%/比率・箱は距離%・MACD は符号・predict は確率。USD 絶対値の閾値なし。
- **H8 期間分割**: 教師ラベル・分類器 fit・θ グリッドは学習窓<2025-03。採点窓は評価のみ・封印不参照。periods.py から取得。
- **H13 judge 固定**: score.py/eval_engine 改造なし。
- **H15 ボラ逃げ**: ⚠️本丸。本ゲートは「戻る/片流れ」判別＝reversion 方向の二次判定。atr_pct は複数特徴（箱/MTF/ER/stoch）の1つで、単独支配させない。学習後 feature_importance で atr_pct が上位を独占しないことを確認（独占なら箱/MTF を主役化・H15 §軸1 ①）。
- **H16 1変更・不再演**: 上記 C。

## F. 受け入れ判定（採点前ゲート）
- **自己検査**: ① 恒等（entry_gate=None で base freq-iter1 と net byte 一致）② cap（_verify_cap）③ leak grep assert ④ SHORT 専用（entry_gate は SHORT のみ・LONG 玉/net=0 不変）⑤「わざと壊して落ちるか」メタ確認（θ=1.0 で全 SHORT 新規を止め新規件数が激減することを確認）⑥ teacher==runtime 特徴 source 一致（_entry_feat_vec を教師生成と open_or_add で共用）。
- **学習窓で純増を先に測る**（採点窓不参照）→ OFF を基準に含め改善時のみ採点へ。
- **公式判定は両窓 score.py**（学習窓 純増＋採点窓 base $549 超えを確認するまで「効いた」と言わない）。⚠️ 疑似シミュ禁止＝必ず実エンジン再走。
- **⑨巻き込み**: 守る勝ち玉 133玉 +$1,804（CENTER_LOCK 58/EDGE_TP 75・fat-tail +$339 含む）を入口ゲートが過剰に弾いていないか玉単位で確認。両窓 net additive が条件。
- **degenerate 検査**: 新規を弾きすぎて件数が freq-iter1 より大きく減って見かけ net が良いだけでないか（件数/日と net を両方・nofloor で広げた効果が残るか）を確認。
- **AUC 確認**（参考）: 入口分類器の学習窓/採点窓 AUC（E8 の 0.733 が目安・低すぎれば入口時点で片流れは予測困難＝撤退）。AUC は採否根拠でない（採否は両窓 score.py）。

# acceptance — E37 v10 ゾーン方式レンジスキャル SHORT（§1.2.1 準拠 MVP・2026-07-04）

TARGET: scripts/priority_rebuild/e37_range_scalp.py

## ★戦略照合（STRATEGY_ANCHOR: e37=range,short_only,scalp）
- 台帳マーカー逐語: e37=range,short_only,scalp（adopted_strategies.md・cat_requirements §1.2.1 の機械可読形）
- 局面（range）: GATE_IDENT=range_ok_v10 ＝タッチ実績（3回以上・ピボット束ね・24h窓）のあるレジスタンス／サポートゾーンが上下に揃い、ゾーン間の幅が最低幅以上の時だけ入口を開く列。レンジ判定を実装の物理 AND として持つ（判定は明示のルール列＝ML に任せない）。
- 方向（short_only）: SIDE_IDENT=short_only_v10 ＝LONG 入口の生成経路を持たない（上限ゾーンのみ使用・E36 の short_only フラグと同型）。
- 頻度（scalp）: 件数/日を上げることが役割（受け入れ F に件数/日基準を明記・低頻度で net を作る形は受け入れ不可）。
- 経緯の係留: 直近 iter: E37 v9 型×side Entry/Exitセット共同選定（フェーズ1）（ledger ARC order=23 読了）。
- 知識の係留: range_scalping_kb.md（読了済み）§7 対応表に1行ずつ準拠（下の「やること」に対応を明記)。

## 方針/狙い/目的
v9 の確定（学習窓 be の帯が採点窓の低ボラドリフトで持続しない・稼ぐ玉0・レンジ判定を欠いた土台)を受け、**検出器で帯を作る路線をやめ、§1.2.1 と range_scalping_kb §7 を字義どおり実装する素ルール MVP で E37 の地面を出す**。
LEVER 逐語引き継ぎ: E37 v10 ゾーン方式レンジスキャル（タッチ実績ゾーンの range_ok でレンジと判定した場面のみ・上限ゾーン拒否確認で SHORT のみ・TP幅≥SL幅）

## 深掘り4点
- ① 真因: レンジ判定を欠いた入口（ADX40+ で建てた玉 48.5%）と向きの選択（SL 130件は含み益≥含み損 0%＝N11）・トレンド文脈イベントが母数の主力＝場と向きの選択そのもの。
- ② 期待値分解: (a) 場の選択（レンジのみ）で MFE≤5 玉（58.6%・−$1,136）を減らして勝率側を押し上げ、(b) TP幅≥SL幅の物理条件で必要勝率そのものを 50% 以下へ下げる（現行 63.2% 要求 vs 実 52.6%＝差 10.6pt を両側から縮める）。
- ③ root か symptom か: root（入口の場と向き）。Y。出口の微調整（symptom）から入らない。
- ④ ベースアップ: range_scalping_kb（2026-07-04 新設・LuxAlgo/FXOpen/QuantifiedStrategies/Babypips）＋学術裏付け（Osler, SSRN 888805＝S/R レベルはイントラデイのトレンド中断を予測・arxiv 2606.29591＝短期反転は向きが予測不能＝到達だけで入らず拒否確認が必要）＋probe 実測（学習窓・箱内 SHORT イベント 7.54件/日・SMA 回帰幅 med 0.213%・0.08% 超え 98%＝頻度と幅の桁の確認のみ）。

## ★疑似シミュ由来の固定値ゼロ
- (a) probe の数値（7.54件/日・0.213%・回帰率 53.5% 等）は桁の確認のみ＝設計の固定値・採否根拠に焼かない。
- (b) 各値の出所: タッチ回数 3回以上＝range_scalping_kb §2（業界の検証標準・a-priori）／ピボット窓 LOOKBACK=288本(24h)・ゾーン束ね幅 tol=0.10%・SL バッファ=0.05%＝a-priori の丸い値（スイープしない）／ゾーン間の最低幅=2×SCALP_FLOOR＝幾何由来（TP 幅と SL 幅の両立に必要な最小幅）／SCALP_FLOOR 0.08%・TTL 3本・TIME 60分・UNIT 0.024・MAX_ADDS=1＝既存定数。
- (c) 採否は実エンジンの学習窓 → 採点窓の score.py の数字のみで決める。

## やること（実装項目・各行に KB §7 対応）
1. --v10 フラグ追加（既定 OFF＝v9 恒等・trades CSV md5 一致で確認）
2. _zones_v10: 過去 LOOKBACK 本のピボット高値・安値（structure_features の fractal j+2 確定＝当該足までで確定・H2)を価格帯 tol で束ね、タッチ回数（束ねたピボット数＋帯への接触回数）≥3 のゾーンを列化（KB §2＝機能実績のあるゾーン）
3. range_ok_v10: 上下ゾーンあり ∩ ゾーン間幅 ≥ 2×SCALP_FLOOR ∩ ゾーン破れ無効化（出来高が20期間平均超 ∩ 終値がゾーン外 → 当該ゾーンを無効化＝KB §5 破れたら黙る＝E32b を邪魔しない）
4. 入口: range_ok_v10 ∩ 高値が上限ゾーン帯に接触 ∩ 陰転の反転バー ∩ RSI9 の買われすぎ（>70）からの下向き反転 → SHORT 指値 maker（close×(1+0.0001)・TTL3・サイドごと単一スロット・MAX_ADDS=1）（KB §3＝到達＋拒否確認・5分足設定 RSI9＝technical_kb §4）
5. short_only_v10: LONG 入口の生成経路なし（§1.2.1 ショートのみ）
6. 出口: TP=レンジ中央（maker・TP 幅が SCALP_FLOOR=0.08% 未満なら建てない＝手数料 maker 往復を超える幅の物理保証）／SL=上限ゾーン上端＋バッファ（maker・浅い＝KB §4 ゾーンのすぐ外）／**tp_ge_sl_check_v10: TP 幅 ≥ SL 幅 でなければ建てない**（KB §1 の R:R＝勝ち側を大きく・逆 R:R の物理禁止）／TIME_EXIT 60分（taker・保有は分単位＝短保有）
7. RSI9 列を add（pandas 標準計算・当該足まで・H2。既存 add_indicators に無ければ v10 専用に追加）
8. 出力: 共通 _output_and_report（--tag v10・連番・params_sidecar・§3.1 準拠）
9. 新 exit_reason なし（TP_FILLED / SL_FILLED / TIME_EXIT の既存登録のみ＝D 審判整合・score.py 変更なし・H13）

## DESIGN_CONTRACT
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["range_ok_v10", "short_only_v10", "_zones_v10", "tp_ge_sl_check_v10"]
}
```
GATE_IDENT=range_ok_v10 / SIDE_IDENT=short_only_v10（require_design_contract_before_run が実行前に実装ソースと機械照合）

## E. §4.6 ハード制約 照合（1項目ずつ）
- H1 cap: 単発 0.024・サイドごと単一スロット・strat_base._verify_cap＋score.assert_hard_constraints（既存）
- H2 leak: ピボットは fractal j+2 確定・ゾーン/破れ判定は当該足まで・.shift(- と center=True は書かない（書く場合は H2OK 因果性宣言＝require_leak_annotation）・RSI9 も当該足まで
- H3 net 判定/H4 コスト: score.py/eval_engine 既存（改造しない）
- H5 約定モデル: entry 指値 maker close×(1+0.0001)・TTL3・不約定は建てない／TP・SL=指値 maker／TIME=成行 taker+slip（既存 eval_engine どおり）
- H6 価格非依存: ゾーンは距離%・幅は%・USD 絶対値の閾値なし
- H7 足: 5m（ゾーン構築も 5m ピボット・上位足の追加は本 iter ではしない＝1変更）
- H8 期間: periods import（既存）・学習窓 fit なし（素ルール・分位選定なし）・採点窓は score.py のみ
- H9/H10/H12: score.py 既存ゲートが担保（最小注文・サイズ配分・異常値 STOP）
- H13 judge 固定: score.py/eval_engine/precheck 触らない・新 exit_reason なし
- H15 ボラ逃げ: 方向判定に ATR/ボラ系を使わない（ゾーン幾何＋反転バー＋RSI9）・SL も ATR でなくゾーン基準
- H16 1変更: v10 は新規 MVP 一式（§8.4 アジャイル＝Entry/Exit は一式で作る）・既定 OFF 恒等・検出器/θ/教師の変更なし
- H11/H14: 合格ライン・発注フラグは非該当（バックテスト・実発注なし）

## F. 受け入れ判定（実験前固定・後出し変更なし）
- 自己検査: ① --v10 OFF 恒等（v9_015 系 CSV と md5 一致） ② cap 実測 ③ leak grep 0件 ④ py_compile ⑤ 番人メタ確認（タッチ下限を 99 に壊すとゾーン0＝発火0になるか／tp_ge_sl_check を反転すると件数が変わるか）
- 学習窓 --diagnostic: 件数/日・保有時間分布（分単位か）・range_ok 通過率・エントリー時 ADX 分布（**ADX40+ 混入が v9 の 48.5% から大幅減しているか＝レンジ判定の実効の受け入れ確認**）
- precheck（学習窓）→ 公式 score.py（採点窓）→ report --vs v8_013 / analyze --vs --train / viz PNG（**上げ・下げ相場でのエントリーが消えているかを画像で確認**）
- 合格ライン: **件数/日 > 0.41（スキャル役割＝件数/日を上げる・目標桁 3件/日）かつ 採点窓 net > v8_013（月−$2.28）かつ 非degenerate**
- 1回で黒字未達でも MVP 地面として ratchet（次レバー＝教師②[range_ok 通過後の母数で学習] or 出口③・1つずつ）

<!-- ARC order=24 iter="E37 v10 ゾーン方式レンジスキャル SHORT（§1.2.1 準拠 MVP）" 前提="E37未採用・v9=net大幅未達・§1.2.1違反5段階ドリフトの確定とrange_scalping_kb新設の上" 採否="未(実装前)" base_csv="trades_e37_range_scalp_v8_013_score.csv" score_csv="" train_csv="" 狙い="検出器で帯を作る路線をやめ§1.2.1とrange_scalping_kb§7を字義どおり実装する素ルールMVPでE37の地面を出す（レンジ判定・ショートのみ・短保有・手数料超え幅・小刻みに大量・E32bを邪魔しない）" 内容="--v10=タッチ実績（3回以上・ピボット束ね・24h窓）ゾーンのrange_ok_v10∩上限ゾーン到達∩拒否確認（陰転反転バー+RSI9買われすぎ反転）でSHORTのみ・TP=レンジ中央（幅≥SCALP_FLOOR0.08%）・SL=ゾーンすぐ外・TP幅≥SL幅必須・TIME60分・ML不使用・既定OFF=v9恒等" 方法="自己検査（OFF恒等md5・cap・leakgrep・メタ確認）→学習窓diagnostic（件数/日・保有分布・range_ok通過率・ADX40+混入がv9の48.5%から大幅減）→precheck→両窓score.py（件数/日>0.41かつnet>v8_013かつ非degenerate）→report/analyze/vizPNGで上げ下げ相場エントリー消滅を確認" -->

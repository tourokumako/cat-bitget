# acceptance.md — E37 v12: レンジ上部で確認なし SHORT（件数を出す・Exit は次段で締める）（2026-07-06）

TARGET: scripts/priority_rebuild/e37_range_scalp.py

## LEVER（improvement_plan から逐語引き継ぎ・enforce_pdca_chain 接続②）
入口の拒否確認(陰転∩RSI9下向き反転)を外し、range_ok_v11∩上限ゾーンでレンジ上部に確認なし SHORT を多く入れて件数を出す(方向選別しない・Exitは次段で締める)
- 本手＝この LEVER を1変更で実装＝v11_entry_candidates の拒否確認(rev)要求を外す新モード（既定OFF=v11oe 恒等）。

DESIGN_CONTRACT:
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["range_ok_v11", "short_only_v11", "v11_entry_candidates", "v12_open_range"]
}
```

## ★戦略照合（enforce_strategy_anchor）
- STRATEGY_ANCHOR: e37=range,short_only,scalp（cat_requirements §1.2.1 逐語再掲）
- 局面：range ＝ range_ok_v11（v17 視認校正済み計器）で入口を制約。GATE_IDENT=range_ok_v11（不変・DESIGN_CONTRACT self_check_calls 登録済）。
- 方向：short_only ＝ 上限ゾーンの反落のみ・LONG 入口の生成経路なし。SIDE_IDENT=short_only_v11（不変・DESIGN_CONTRACT self_check_calls 登録済）。
- 頻度：scalp ＝ 件数が役割。本手はレンジ上部で件数/日を上げる（薄利多売・確認なしで間口を戻す）。
- ledger 直近 ARC 係留（鉤括弧で逐語引用）: 「E37 v11oe 入口の過熱の必須化を撤去（Step1 Do）」。本手はその続き＝過熱の必須化に続き拒否確認も外し、方向選別を完全にやめて件数を出す（Exit で締めるのは次段）。

## スキャル要件（enforce_e37_pdca ⑦⑨⑫・本手は入口のみ変更＝出口/足は v11 不変で維持）
- ⑦ 手数料を超える TP幅（maker往復）：v11 出口不変＝TP1幅 ≥ SCALP_FLOOR 0.08%（maker 往復0.028%の約2.9倍）を tp_ge_sl_check_v11 が建てる前に判定＝手数料の壁を超える幅のみ建てる。TP2=レンジ中央。入口を緩めても TP幅≥手数料の物理条件は維持。
- ⑨ 短保有（分単位・数分）：v11 出口不変＝TIME 60分 backstop（分単位）・実測保有 中央値 PARTIAL_TP 48分/SL 22分＝分〜数十分の scalp 保有。件数は増えるが保有時間は延ばさない（保有4h をスキャルと称した再演でない）。
- ⑫ 5分足設定 RSI9/MTF：v11 不変＝執行足5分・RSI9（rsi9・technical_kb §4）・MTF＝1h ゾーン range_ok_v11（technical_kb §5）。本手は入口の拒否確認(rev)を外すのみ＝RSI9 指標自体・MTF ゾーンは維持。
- 決済方法（exchange_spec ★決済方法・§6.1/§6.1.1 読了）：同サイド merge・平均建値／部分決済 scale out（複数TP最大20）／予算0.12は全建玉合計＝本手は入口のみで決済/add/cap は v11 不変（同時最大0.048 BTC＜0.12）。

## B 深掘り4点
① 真因：入口 SL −$871（最大出血）は N11 で含み益≥含み損 1%＝過熱fade の直行逆行（方向）。probe で静的テクニカル（stoch_k AUC 0.61＝弱）も需給（taker_ls AUC 0.52＝ほぼ0.5で分けられなかった）も、負けSL玉と勝ちPARTIAL玉を分けられないと両窓で判明＝入口で方向を選り分けるのは有効でない（KB §6.6/§6.7＝crypto の短期方向はランダムウォーク相当）。
② 期待値分解：方向を当てられない以上、勝率はコイン投げ相当（実46.8%）。黒字化は R:R とコストで作る＝平均勝ち$5.58 を伸ばす／平均負け$6.11 を浅く／TIME の taker手数料負けを maker化。本手（この周回）はその前提づくり＝件数（PARTIAL_TP +$772 の母数）を増やす（net の締めは次段の Exit）。
③ root か symptom：root（入口で方向を当てる路線そのものが効かないと確定＝方向選別を捨てる）。symptom パッチ（SL幅の手調整）でない＝N9 出口効率0.78 正常・深SLは直行逆行玉を救えない。
④ ベースアップ（今セッションで Read した KB／probe／WebSearch・WebFetch の証跡）：
   - range_scalping_kb §1（薄利多売＝小さく短く回数で積む）／§6.6・§6.7（方向は予測困難・taker_ls は E28 LONG で効いたが SHORT 対称は本 probe で分けられなかった）／§3（レンジ上部＝上限ゾーンでの SHORT）。
   - trade_analysis_methods_kb §0（前後比較）・§3（MAE/MFE 較正）・§7（原因3分類）。
   - probe（e37_sl_winner_separation_probe.py・両窓）：静的 stoch_k 0.61／需給 taker_ls 0.52／過熱選別は勝ちPARTIAL の42-45%を巻き込む。
   - WebSearch/WebFetch（今セッション・3件3種別＝次段 Exit 設計のベースアップ）：①arxiv 1411.5062 Leung&Li（学術）＝手数料下で SL と TP は逆相関（浅SL→低TP が最適）・entry 領域は SL の上に有界＝TP/SL は対称でなく joint 較正。②arxiv 1707.03498（学術）＝deadline 型出口（E35 iter8-9 の元・次段 TIME の maker 化の根拠）。③epchan/alphaarchitect（有名クオンツ）＝「cut your losses は明確な優位なし」＝切る系を足さない方針を支持（L-309 と一致）・exit を管理し target を固定しない。

## ★疑似シミュ由来の固定値ゼロ
- 本手は入口の拒否確認(rev=陰転∩RSI9下向き)を外すだけ＝新しい閾値・段数・分位は一切足さない。
- (a) 各値：新規の固定値なし（range_ok_v11/上限ゾーン/SCALP_FLOOR/TIME/SL バッファは v11 の既存値をそのまま維持）。
- (b) probe の数値（AUC 0.61/0.52 等）を設計の固定値に焼いていない＝probe は「入口で方向は選り分けられない」の確認に使っただけ。
- (c) 採否は probe でなく実エンジン両窓 score.py の数字で決める。

## C 変更の単位（H16・1ターン1変更）
- 1レバー：入口の拒否確認(rev)要求を外す（新モード v12_open_range・新フラグ --v12-open-range・既定OFF=v11oe 恒等）。実装＝v11_entry_candidates に open_range 引数を追加し、True のとき rejected を常時 True にして entry = range_ok_v11 ∩ 上限ゾーン接触 のみにする（rev を要求しない）。
- 既定 OFF で恒等：--v12-open-range を付けない時は v11oe と完全一致（md5 3本一致で確認）。
- 過去失敗の不再演：v2〜v11oe（ARC11〜26）は全て入口で方向を当てる設計。本手は初めて方向予測を放棄する＝同型再演でない。切る/早切り系（L-309）でもない（入口を緩める＝件数を増やす方向）。

## D 審判（score.py / eval_engine）整合
- 新しい exit_reason を出すか？ → 出さない（入口のみ変更・出口は v11 の PARTIAL_TP/TP_FILLED/SL_FILLED/TIME_EXIT 不変）＝score.py 登録・既知答えテストの追加は不要。
- entry/exit のコスト種別（maker/taker）が変わるか？ → 変わらない（entry=指値maker・出口=v11 不変）。
- judge の計算式に触れるか？ → 触らない（H13）。
- 命名：同一 e37_range_scalp.py に新フラグ＝pdca 命名規約に乗る（e[0-9][0-9]_ 実験検知）。実験出力は --tag v12 で連番。
- サイドカー：params.json を write_sidecar で出す（入口ロジックに「確認なし（open_range）」を記録）。
- 出力：共通の書き出し処理 _output_and_report（ratchet_io・命名/archive/上書き防止を踏襲）。strat_base の import は既存のまま。

## E §4.6 ハード制約 照合
- H1 cap：同時最大 0.048 BTC（2 lot・V11_MAX_ADDS=2）＜0.12＝不変。_verify_cap / score.assert_hard_constraints で実測。
- H2 leak：入口条件（range_ok_v11・上限ゾーン接触・rsi9）は全て当該足まで＝未来参照なし。新規の shift(-)/center=True を足さない（grep assert）。学習末 < 採点始（periods）。
- H5 約定モデル：不変（entry 指値maker・TTL3 / 出口 v11 不変）。
- H6 価格非依存：range_ok_v11/ゾーン/rsi9 は %・比率・価格帯（USD 絶対値の閾値/ラベルを足さない）。
- H8 期間分割：periods.py 由来（学習〜2025-03・採点2025-06〜2026-03・封印）。自前リテラルなし。
- H13 judge 固定：score.py/eval_engine 不変。
- H15 ボラ逃げ禁止：方向スコアを持たない（入口は「レンジ判定∩上限ゾーンの位置」のみ・atr/ボラで方向を判定しない）。むしろ方向選別を捨てる手＝ボラ逃げの余地なし。
- H16 1変更・過去失敗の不再演：上記 C の通り。

## F 受け入れ判定（採点前ゲート・PDCA §8.4・enforce_role_criteria scalp）
- 自己検査：①--v12-open-range OFF で v11oe と md5 3本一致（恒等）②cap 0.048≤0.12 ③leak grep（新規未来参照0）④番人メタ確認（open_range=False で rejected が rev 要求に戻るか・True で ok&touched のみか）。
- 学習窓 diagnostic：入口候補が拒否確認撤去で増えるか（件数/日）を先に確認（採点窓不参照）。
- 公式判定：score.py 両窓。**成功基準（scalp 役割＝件数を上げる・enforce_role_criteria）＝件数/日が v11oe（決済1.85/日）から増える ∩ degenerate でない（near-inaction でない）**。net はこの周回では黒字化を問わない（Exit の作り込みが次段の本体＝まこさん方針「雑に入って Exit で締める」）。次段（Exit maker化・R:R）で両窓 net プラスを狙う。
- 結果は build_trades_overlay.py で⑪ダッシュボードに重ねて目視（前回同様・まこさん要望）。

<!-- ARC order=27 iter="E37 v12 レンジ上部で確認なし SHORT（件数を出す）" 前提="base v8_013・v11oe の続き・入口の方向選別を放棄" 採否="未（実装前）" base_csv="trades_e37_range_scalp_v8_013" 狙い="入口で方向は選り分けられない(probe 両窓 stoch_k0.61/taker_ls0.52)と確定＝方向選別を捨て、レンジ上部で確認なしに件数を出し、Exit で締める薄利多売へ" 内容="v11_entry_candidates の拒否確認(rev)要求を外す新モード v12_open_range（range_ok_v11∩上限ゾーンのみで SHORT・既定OFF恒等）" 方法="自己検査(OFF恒等md5・cap・leak・番人)→学習窓diagnostic(件数増)→両窓 score.py(件数/日>1.85・非degenerate・netは次段Exitで締める)" -->

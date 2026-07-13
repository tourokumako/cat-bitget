# acceptance — E37 v23「TREND_CONT の V9 型 Exit 状態機械化（uptrend 発火で成行投げをやめ genuine 反転/stall/災害SL に委ねる）」2026-07-15

TARGET: scripts/priority_rebuild/e37_range_scalp.py

## DESIGN_CONTRACT
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": [
    "v23_trend_exit",
    "STOCH_REVERSE_EXIT",
    "MFE_STALE_CUT",
    "range_ok_rg5",
    "short_only_v11"
  ]
}
```

## 網羅マトリクス参照
- 網羅マトリクス（entry_exit_matrix）「グリッド: E37」の **#30（v23）** を実装する（improvement_plan 記載）＝#7 遠SL・時間切れ主体 ＋ #8 SLなし・レンジ破れ撤退 ＋ V9 の genuine 反転利確 を実証固定値で組む。**未試行: あり**（#11〜#20 ほか＝潰し切るまで閉じない）。
- **Exit 状態機械として設計**（軸を1つ選ぶのでなく分岐表・下記）。Entry は現行維持（armed DC 据え置き）。

## ★戦略照合（enforce_strategy_anchor・§1.2.1 係留）
- アンカー逐語: STRATEGY_ANCHOR: e37=range,short_only,scalp
- 局面: GATE_IDENT=range_ok_rg5（RG-v5 の range 判定・入口据え置き）＝レンジ担当に整合（uptrend 発火で新規停止は不変）。
- 方向: SIDE_IDENT=short_only_v11（LONG 入口の生成経路なし・据え置き）＝short_only に整合。
- 頻度: 入口据え置き＝新規 3.19件/日 維持（件数を減らして net を作らない・scalp 一級基準）。出口のみ作り替え。
- 経緯の係留（ledger 直近 ARC 逐語）: ledger ARC37「E37 v22 レンジ中の戻り売りDC入口×レンジ下限TP＋ピーク反転畳み・前兆逃げ（Entry×Exitセット）」＝precheck FAIL・**TREND_CONT 337件 −$1,353 が主因のまま**。本 v23 はその TREND_CONT の畳み方だけを V9 型へ差し替える次段（入口・TPアンカーは v22 のまま据え置き）。

## LEVER（improvement_plan から逐語引き継ぎ）
E37 出口を V9 状態機械へ差し替え（uptrend force-close[TREND_CONT 即taker]とアグレッシブ trailing[MFE_DRAWDOWN_CUT]を廃止・切るのは真の構造破れ RANGE_BREAK＋災害SL だけ・それ以外は持ち切り・genuine 指標反転[stoch/RSI]で利確・益が出ない B型の stall cut・固定値は V9 実証レンジ a-priori で学習窓選定なし・入口 armed DC 据え置き）

## Exit 状態機械（entry 後のポジション状態 → 発火枝の分岐表・v23 での変更点）
| ポジションの状態（entry 後の動き） | 発火する Exit | v23 での扱い |
|---|---|---|
| 含み益が乗って TP1/TP2 到達 | PARTIAL_TP / TP_FILLED（maker） | 現行維持（v22 のレンジ下限アンカー据え置き） |
| **uptrend 発火時に保有していた玉**（trend_caught） | ↓ 下記4状態へ委ねる（**即成行クローズを廃止**） | **★本 v23 の変更点** |
| 　└ 含み益が乗った状態で指標反転（stoch GC） | **STOCH_REVERSE_EXIT（maker・新設）** | 新設＝genuine 反転で利確（トレーリングでない離散イベント・勝ち玉を早切りしない） |
| 　└ 益が一度も費用超えに達しない（失速） | **MFE_STALE_CUT（taker・新設）** | 新設＝B型を小さく切る（保有≥30分∩含み益<gate） |
| 　└ 深い逆行（本物の上昇継続） | 災害SL（res_hi＋1.0×W・現行） | 現行維持＝深い災害SLまで持つ（最悪点で成行投げしない・浅SLは足さない L-331） |
| 　└ どれも当たらず時間経過 | TIME backstop（240分・現行） | 現行維持 |
| レンジ破れ（出来高∩帯外持続） | RANGE_BREAK_EXIT（taker・現行） | 現行維持（真の破れは切って E32b に譲る） |
| 含み益ピークから割戻し（trailing） | ~~MFE_DRAWDOWN_CUT~~ | **廃止/不使用**（両窓で符号反転＝勝ち玉を切る・L-341） |

## 深掘り4点
- **① 真因**: TREND_CONT 337件 −$1,353 の正体＝uptrend 発火で保有 SHORT 玉を **c[i] の成行（taker）で即クローズ**（e37_range_scalp.py 約 line 1939）＝最悪点で確定。64%（307/478）は投げる前に往復手数料超えの含み益ピーク（逃げ場）があったのに取れていない（traj_diag）。＝**執行の欠陥**（入口でなく畳み方）。
- **② 期待値分解**: 動かすのは (a) 平均負け＝即成行投げをやめ深い災害SL/TIME まで持つ＋genuine 反転で益側に逃がす→TREND_CONT の実損を回収 (b) 平均勝ち＝64%の含み益ピークを STOCH_REVERSE で取る。勝率・件数は入口据え置きで不変。
- **③ root か symptom か**: root。即成行クローズという執行そのものを状態機械へ変える（浅SL いじり[symptom]でなく畳み方の構造）。
- **④ ベースアップ**: WebSearch 3本（arxiv/ssrn 学術＋quantstart/hudsonthames＋quantpedia＝3種別）＋WebFetch 2本（2026-07-15）＝(i) OU 平均回帰の最適 exit は mean 対称の利確水準＋**stop は「取引長が期待長＋Nσ を超えた時＝構造破れ/duration」で置く＝浅stopでない**（hudsonthames Optimal Trading Thresholds／arxiv 1411.5062）＝**深い災害SL＋TIME backstop を支持** (ii) 反転は %K が %D を上抜く/下抜くで判定＝**stoch reversal exit を支持**（quantinsti Stochastic Oscillator） (iii) trailing stop は sell limit と併用が最適だが drawdown 型＝本 E37 では両窓で符号反転（勝ち玉を切る）と実測＝**trailing は採らず genuine 反転（離散イベント）を採る**（arxiv 1701.03960＋traj_branch_diag の実測が優先）。range_scalping_kb §9（V9 実証出口）と整合。

## やること（実装項目・--v23-trend-exit・既定 OFF＝v22_042 構成と恒等）
1. **CLI フラグ --v23-trend-exit 新設**（既定 OFF＝v22_042 構成と md5 恒等）。--v20-rg5 --v18-tp2-far --v22-set 必須（v22 構成の上に載る）。
2. **uptrend 発火の close site（run_continuous_v11・約 line 1921〜1953）を変更**: v23 ON 時、uptrend 発火（v20_uptrend[i]）で保有 lot を `_record(...,"TREND_CONT",...)` の即成行クローズ**しない**。`pend=None`・armed 封鎖（新規停止）は維持。各 lot に `lot["trend_caught"]=True` を立てて keep（`_keep20` に残す）＝下の Exit ループに委ねる。v21_uptrend_fold（maker 逃げ）・v22_peak_fold（ピーク畳み）は v23 ON 時は不使用（trend_caught 玉は新設枝が担う）。
3. **STOCH_REVERSE_EXIT（新設・maker）を Exit ループに追加**: `lot["trend_caught"]` の玉に対し、`unreal>0`（含み益あり）∩ 含み益ピーク（lot["max_fav"] 由来）≥ 往復 maker fee ∩ **stoch(9,3) ゴールデンクロス**（k9 が d9 を前バー下→当バー上＝既存 k9/d9 配列・当該バーまで＝H2）で maker 利確（close で決済）。＝V9 §9.2 STOCH_REVERSE_EXIT の移植（コンフルエンス＝単一閾値で組まない・基本原則①）。
4. **MFE_STALE_CUT（新設・taker）を Exit ループに追加**: `lot["trend_caught"]` の玉に対し、`hold_min≥30` ∩ 含み益ピークが往復 fee 未満（益が一度も出ていない B型）で taker で小さく切る。＝V9 §9.2 MFE_STALE_CUT の移植。
5. **災害SL・TIME backstop は現行を流用**（trend_caught 玉も既存の SL[res_hi＋1.0×W]・TIME[240分] に当たる＝浅SLは足さない）。**MFE_DRAWDOWN_CUT（trailing）は v23 では発火させない**（両窓符号反転・L-341）。
6. **固定値の出所（★学習窓選定なし）**: stoch GC＝V9 同（指標のイベント）・MFE_STALE の 30分/往復fee gate＝V9 の 30分/$4 相当を E37 の fee 単位へ a-priori 変換・災害SL/TIME＝既存。**メニュー選定・学習窓 OOF・θ は一切使わない**（1セット固定・悪ければ構造を考え直す）。
7. §0 自動生成（_param_sections）に v23 の分岐（trend_caught の4状態→枝）と固定値の出所を実値から追記（スキーマ selftest 断言）。
8. 番人（メタ確認・--v23-guard-check）: (a) OFF 恒等 md5（--v23-trend-exit 無し＝v22_042 と完全一致） (b) uptrend 全 True 強制で trend_caught 玉が即成行(TREND_CONT)0 件・新設枝へ流れる（force-close 廃止の配線証明） (c) STOCH_REVERSE の GC を全 False 強制で発火0（配線） (d) MFE_STALE gate 極端値（gate=∞）で全 trend_caught 玉が即 stall cut（枝の実効）。
9. 走行は --tag v23（連番）・_output_and_report（strat_base 経由）・両窓 CSV→report --vs archive/v22_042 --train→analyze を必ず出す（どの判定でも・9a4d348）。

## ★疑似シミュ由来の固定値ゼロ
- (a) stoch GC・30分・往復fee gate・災害SL・240分 TIME は **V9 実証レンジ（cat_params_v9.json／replay_csv `_check_exits_replay`）の a-priori 移植** or 既存定数＝probe で出した特定数値を焼いていない。
- (b) traj 診断の数値（64%・+$289・+0.318% 等）は現状把握のあたり付けのみ＝設計の固定値・採否根拠に使わない。
- (c) 採否は **学習窓選定でなく実エンジン両窓 score.py の数字**＋まこさんの目で決める（固定値ゆえスイープしない）。

## ML_DECL（enforce_ml_honesty・本レバーは ML不使用）
<!-- ML_DECL
目的: TREND_CONT（uptrend 発火で保有 SHORT を成行投げ −$1,353）を、V9 実証の出口状態機械（genuine 反転利確/stall cut/深い災害SL/TIME）へ差し替え net 最大化。§1.2.1 レンジで net プラスの幅を取る指示。
教師: なし（出口は固定値・V9 a-priori・ラベル学習しない）。取り逃し/leak の議論は該当なし（学習を行わない）。
学習内容: なし（V9 §9.2 の優先順位つき状態機械＝手書き固定ルール）。
学習方法: ML不使用（予測を出口決定に使わない・飾りでもない＝置かない・手置きgreedy でもない＝学習窓 net 最大の選定をしない）。※入口の場面セル LightGBM は既存だが本レバー（出口）では不使用。
自己申告: 素ルール（ML不使用・固定値）。ML最適化は次段の入口改善で行う。
-->

## D. 審判整合（acceptance_checklist・出戻り防止の最頻点）
- **新しい exit_reason: STOCH_REVERSE_EXIT（maker・指値利確）／ MFE_STALE_CUT（taker・成行）**＝**score.py の MAKER_EXIT_REASONS / TAKER_EXIT_REASONS に登録＋既知答えテスト（test_eval_engine_known_answers）再pass を「やること」に含める（H3/H13）**。実装時に score.py の現行登録を grep 確認し、未登録なら追加（STOCH_REVERSE_EXIT は v14 で登録済みの可能性・要確認／MFE_STALE_CUT は要確認）。**判定器(score/eval_engine/precheck)のロジックは触らない＝登録リストへの語追加のみ**。
- コスト種別: STOCH_REVERSE=maker（有利価格の指値利確）／MFE_STALE=taker（成行止血）＝約定方式で分類。
- 命名: --tag v23 連番（require_tag_for_experiment 準拠）。
- サイドカー: _output_and_report（strat_base・ratchet_io）で <stem>_params.json 自動出力（§0 に v23 実値）。
- 共通土台: strat_base import（現行のまま）。

## E. §4.6 ハード制約 照合
- H1 cap: 合計 0.12・本戦略同時最大 0.048 不変＝_verify_cap＋score.assert_hard_constraints。
- H2 leak: stoch GC は k9/d9 の当該バーまで／mfe は lot["max_fav"]（前バーまでのピーク pk_prev を使い同一バー楽観を排除）／hold_min は経過本数。`.shift(-`・`center=True` は使わない（該当なし）。
- H5 約定モデル: STOCH_REVERSE=maker 指値・MFE_STALE=taker+slip・災害SL/TIME 現行＝eval_engine 準拠。
- H6 価格非依存: 30分=本数・fee gate=比率・stoch=指標＝USD 絶対値なし。
- H8 期間: periods.py import・**本レバーは学習窓選定なし＝固定値**（採点窓/封印 不参照は自明）。
- H13 judge 固定: score.py/eval_engine/precheck のロジック無変更（exit_reason 登録リストへの語追加のみ＝既知答えテスト再pass で担保）。
- H15 ボラ逃げ: 出口レバー＝入口の方向スコアに触れない（非該当）。
- H16 1変更: TREND_CONT の畳み方1つ（Exit 状態機械化）。過去の轍回避＝トレーリング不使用（L-341）・浅SL足さない（L-331）・学習窓選定しない（L-320/L-341）・v14 の枝並べ中立化は優先順位つき状態機械＋固定値で回避。

## F. 受け入れ判定（採点前ゲート）
- 自己検査: OFF 恒等 md5（--v23-trend-exit 無し＝v22_042 一致）／py_compile／DESIGN_CONTRACT 5識別子／番人4枝（やること8）／cap 実測／leak 自己 grep／§0 スキーマ selftest／既知答えテスト再pass（新 exit_reason 登録後）。
- **学習窓選定なし**＝固定値1セットで直接本走（選定表なし）。
- precheck: 学習窓 be・--target（FAIL なら採点温存・それでも両窓 CSV→report/analyze は必ず出す＝9a4d348）。**固定 a-priori 戦略ゆえ precheck の be≥1.0 は参考＝判定は両窓 score.py＋まこさんの目**。
- 両窓 score.py: **採点窓 net が v22_042 −$456 を上回る ∩ TREND_CONT の net が改善（−$1,353 が縮む）∩ 他の出口（PARTIAL_TP +$973）を毀損しない ∩ 新規件数/日 3.19 維持（入口据え置き＝件数不変）∩ 非 degenerate**。report C/K 節で TREND_CONT・PARTIAL_TP の net を確認。
- ⑨ 巻き込み: STOCH_REVERSE が勝ち玉（837玉 +$1,632）を早切りしていないか＝report K 節 平均勝ち＋PARTIAL_TP 件数/net の非毀損で確認。毀損が回収を超えるなら不採択のまま走らせ結果を記録（データ捨て禁止）。
- スキャル一級基準: ⑦ TP 幅（レンジ下限・v22 据え置き）≥手数料床／⑨ 短保有＝TIME backstop 240分内維持／⑫ 5分足設定＝stoch(9,3)・RSI9・RG-v5 MTF。

<!-- ARC order=38 iter="E37 v23 TREND_CONT の V9 型 Exit 状態機械化（uptrend 発火で成行投げをやめ genuine 反転/stall/災害SL に委ねる）" 前提="base=v22_042構成（採点窓 net −$456・TREND_CONT 337件 −$1,353 が主因のまま・地面v8_013維持）・まこさん指示2026-07-15＝TREND_CONT −$1,353 の改善だけに絞る・V9 実証出口を固定値で移植（ML/学習窓選定を使わない）" 採否="未（実装前）" base_csv="trades_e37_range_scalp_v22_042" score_csv="" train_csv="" 狙い="uptrend 発火で保有 SHORT を成行で最悪点投げしている TREND_CONT −$1,353（64%に含み益ピークの逃げ場が実在）を、V9 実証の出口状態機械（genuine 反転利確/stall cut/深い災害SL/TIME・トレーリング不使用）へ差し替えて回収する。入口・件数は据え置き" 内容="uptrend 発火の即成行クローズを廃止し保有玉を trend_caught として keep→STOCH_REVERSE_EXIT(maker・stoch GC∩含み益)/MFE_STALE_CUT(taker・保有30分∩益なし)/災害SL(深い・現行)/TIME(240分・現行) の優先順位つき状態機械へ委ねる。MFE_DRAWDOWN_CUT(trailing) は不使用。固定値は V9 a-priori・学習窓選定なし" 方法="OFF恒等md5(v22_042一致)→新 exit_reason(STOCH_REVERSE_EXIT/MFE_STALE_CUT)を score.py 登録＋既知答えテスト再pass→番人4枝→固定値で直接本走→precheck(参考)→両窓 score.py(採点窓 net>−$456 ∩ TREND_CONT 改善 ∩ PARTIAL_TP 非毀損 ∩ 件数3.19維持)→report/analyze --vs v22_042" -->

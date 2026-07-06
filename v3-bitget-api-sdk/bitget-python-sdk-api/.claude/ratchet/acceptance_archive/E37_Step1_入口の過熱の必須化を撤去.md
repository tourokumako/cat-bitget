# acceptance.md — E37 Step 1 Do: 入口から「過熱を必須にする確認」を撤去（拒否確認は残す）（2026-07-05）

TARGET: scripts/priority_rebuild/e37_range_scalp.py

## LEVER（improvement_plan から逐語引き継ぎ・enforce_pdca_chain 接続②）
入口3条件（上端到達/陰転/RSI9>70反転）のうち、probe で特定した「最も発火を殺しているが質(N10過熱・N12幅)を損なわない1条件」を緩めて件数を出す
- 本手＝この LEVER の「1条件」＝probe で特定した「過熱を必須にする確認」を撤去する（反転確認 陰転∩RSI9下向き は残す）。

DESIGN_CONTRACT:
```json
{
  "impl_file": "scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["v11_open_entry", "v11_entry_candidates", "range_ok_v11", "short_only_v11", "rsi9"]
}
```

## ★戦略照合（enforce_strategy_anchor）
- STRATEGY_ANCHOR: e37=range,short_only,scalp（cat_requirements §1.2.1 逐語再掲）
- 局面：range ＝ range_ok_v11（v17 視認校正済み計器）で入口を制約（GATE_IDENT=range_ok_v11・不変）。
- 方向：short_only ＝ 上限ゾーンの反落のみ（SIDE_IDENT=short_only_v11・不変）。
- 頻度：scalp ＝ 件数が役割。本手は件数/日 0.80 を増やす（過熱の必須化を外し入口の間口を戻す）。
- ledger 直近 ARC：ARC25「E37 v11 視認校正レンジ計器の組み込み（1hゾーン×複数TP+add）」。

## スキャル要件（enforce_e37_pdca ⑦⑨⑫・本手は入口のみ変更＝出口/足は v11 不変で維持）
- ⑦ 手数料を超える TP幅（maker往復）：v11 出口不変＝TP1幅 ≥ SCALP_FLOOR 0.08%（maker 往復0.028%の約2.9倍）を tp_ge_sl_check_v11 が建てる前に判定＝手数料の壁を超える幅のみ建てる。TP2=レンジ中央。入口を変えても TP幅≥手数料の物理条件は維持。
- ⑨ 短保有（分単位・数分）：v11 出口不変＝TIME 60分 backstop（分単位）・実測保有 中央値 PARTIAL_TP 51分/SL 21分（report C）＝分〜数十分の scalp 保有。件数は増えるが保有時間は変えない（保有4h をスキャルと称した再演でない）。
- ⑫ 5分足設定 RSI9/MTF：v11 不変＝執行足5分・RSI9（rsi9・technical_kb §4）・MTF＝1h ゾーン range_ok_v11（technical_kb §5）。本手が触るのは rsi9 の過熱確認のみ＝RSI9 指標自体・MTF ゾーンは維持。
- 決済方法（exchange_spec ★決済方法・§6.1/§6.1.1 読了）：同サイド merge・平均建値／部分決済 scale out（複数TP最大20）／予算0.12は全建玉合計＝本手は入口のみで決済/add/cap は v11 不変（変更しない）。

## B 深掘り4点
① 真因：入口 v11_entry_candidates の「過熱を必須にする確認」が過熱玉（最終入口の stoch_k 高側 82%・上端接触段は46%）を選別＝過熱 fade で継続に轢かれ方向ミス（N11 89%・勝率45%＝コイン投げ以下）。probe（Step1 ファネル）で実証。
② 期待値分解：勝率を上げる（過熱玉を減らし N12 黒字象限=非過熱を入れる）＋件数を増やす（最終確認の73%脱落を緩める）。必要勝率53.3% vs 実45.1%（不足8.2pt）＝勝率を上げるか母数を増やす。
③ root か symptom：root（入口の選別が過熱域に偏る＝負ける方向を選ぶ構造）。symptom パッチ（SL幅/出口）でない（N9 出口効率0.73 正常）。
④ ベースアップ（WebSearch3本＋WebFetch2本・複数ソース種別・今セッション）：
   - KB §3（到達＋拒否確認）／§6.6（方向は予測不能）／N10（過熱域ほど負ける・両窓再現✓）。
   - ★教科書 vs 実データの緊張：教科書（LuxAlgo range-bound 精読）は「過熱オシレーターが拒否ローソクを validate＝過熱確認を残せ」。だが実データ（probe：最終入口 stoch_k 高側82%・勝率45%）＋学術（arxiv 2606.29591 精読：crypto は最もクリーンなランダムウォーク・過熱fadeは統計的根拠なし・continuation≈0.496 コイン投げ／QuantifiedStrategies：強トレンドで過熱は継続）は「過熱 fade は負ける」＝BTC では教科書の過熱確認が逆効果。
   - ★設計判断：教科書の「rejection＋momentum の2確認」は残す（陰転＋RSI9下向き反転）が、「過熱域であることの必須化」は外す（実データ＋学術を教科書より優先＝KB §6.8「教科書案をそのまま実装しない」と同型）。

## C 変更の単位
- 1レバー：入口の拒否確認から「過熱していることを必須にする確認」を撤去（新フラグ --v11-open-entry・既定OFF=現行v11恒等）。実装＝v11_entry_candidates の rsi9 過熱判定項を外す。反転確認（陰転 close<open ∩ RSI9 下向き rsi9<rsi9_prev）は残す。
- ＝**採点窓で値を選ばず「過熱を入口の必須にするのをやめる（確認の有無を変えるだけ）」**。probe の数値は焼かず、確認の有無だけを実エンジン両窓 score.py で測る（採点窓で値を選ぶ L-267 に当たらない）。
- 既定OFF恒等：--v11-open-entry なしは v11 と完全一致（trades/report/analysis の md5 3本一致で自己検査）。
- 過去失敗の不再演：過去20回は「過熱を選ぶ（fade）」＝本手は逆（過熱の必須化を外す）＝再演でない。

## ★疑似シミュ由来の固定値ゼロ（require_acceptance ゲート）
- 各値の出所：本手は新しい閾値/段数/パラメータを足さない＝「過熱を必須にする確認（rsi9_prev>70）の撤去」＝条件を1つ外すだけ。反転確認（陰転∩RSI9下向き）・ゾーン4値・出口・add・cap は v11 の a-priori 定数を不変で維持。
- probe の数値（stoch_k 高側82%・最終入口2.85件/日）は設計に焼いていない＝あたり付け専用（どの条件を外すかの判断材料）。実装は「条件の撤去」で probe の数値を閾値化しない。
- 採否は probe でなく実エンジン両窓 score.py の数字（件数/net/勝率・degenerate）で決める。

## D 審判整合
- 新 exit_reason なし（入口の候補生成のみ変更・出口 TP/SL/TIME/PARTIAL_TP 不変）。
- コスト種別不変（maker entry・maker TP/SL・taker TIME）。judge（score.py/eval_engine）に触れない。
- 出力は共通の書き出し処理 _output_and_report（--tag で連番・上書き防止）。サイドカーは既存の _param_sections が自動表示。

## E ハード制約 照合
- H1 cap：入口のみ変更・出口/サイズ/add 不変＝同時最大 0.048 BTC ≤0.12（_verify_cap 維持）。
- H2 leak：入口条件は t 時点の close/open/rsi9（過去のみ・未来参照なし）。
- H5 約定：不変。
- H6 価格非依存：rsi9 無次元・条件は比率/符号。
- H8 期間：v11 は fit なし素ルール・periods import（不変）。
- H13 judge 固定：触れない。
- H15 ボラ逃げ：入口に atr/ボラの方向スコアなし（過熱の必須化を外すのはボラ選別を減らす方向）。
- H16 1変更：入口の1確認（過熱の必須化）の撤去のみ。

## F 受け入れ判定
- 自己検査：--v11-open-entry OFF で v11 恒等（md5 3本一致）。番人メタ確認＝diagnostic で最終入口の過熱側比率が実際に下がる／件数が増える。cap/leak grep。
- 学習窓で純増（件数増）を先に測る（採点窓 不参照）。
- 公式判定：score.py 両窓。件数（0.80/日から増）・net（地面 v8_013 −$18 超え）・degenerate でない・勝率（45%から改善）。
- Step 1 の成功基準：件数が増える（degenerate 除く）。net はまだ一級に問わない（Step 2 で黒字化）。net・勝率も改善方向か観測。

<!-- ARC order=26 iter="E37 Step1 入口の過熱の必須化を撤去" 前提="v11未採用・入口が過熱側82%を選別と probe で確定" 採否="未" base_csv="" score_csv="" train_csv="" 狙い="入口が過熱fadeで負ける方向を選んでいた(勝率45%コイン投げ以下)のを直す＝過熱の必須化を外し非過熱の反落も取り件数と質を両立" 内容="v11_entry_candidates の過熱を必須にする確認(rsi9 過熱判定項)を撤去・反転確認(陰転∩RSI9下向き)は残す・新フラグ既定OFF恒等" 方法="OFF恒等md5→diagnostic(件数増・過熱比率減)→precheck→両窓score.py(件数>0.80/net>−18/非degenerate/勝率改善)" -->

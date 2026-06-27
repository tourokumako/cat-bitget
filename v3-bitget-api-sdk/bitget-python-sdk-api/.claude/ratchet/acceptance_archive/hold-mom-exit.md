TARGET: scripts/priority_rebuild/e36_short_oscillation.py
TARGET: scripts/priority_rebuild/score.py

# acceptance — E36 時間切れ止血：保有中 momentum反転 早期Exit（網羅分析の突破口・両窓AUC0.9+）

DESIGN_CONTRACT:
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e36_short_oscillation.py",
  "self_check_calls": ["hold_mom_exit", "HOLD_MOM_EXIT", "donchian_pos"]
}
```

---

## 趣旨（網羅分析の突破口を実装＝決め打ちで間引かない）
2026-06-28 の保有経路 全2724指標 sweep（両窓）で出た突破口を実エンジンで数字にする：
- **建てた時点（k=0）は全指標ほぼ無分離**（時間切れ玉 vs 勝ち玉 AUC 0.5-0.68）＝entryゲートも配分も限界だった理由。
- **保有+60分（k=12）で momentum/オシレーター系が一気に分離（AUC 0.89-0.95）し両窓一致**（RCI_26 採点0.95/学習0.92・donchian_position 0.895/0.865・RSI14 0.894/0.900・vortex/TSI/MACD/stoch も同様・全て rise>0＝保有で分離が育つ）。
- ＝「建てる時は見分けられないが、~60分持てば momentum が SHORT の反転前提が壊れたことを両窓ロバストに教える」。240分の時間切れを待たず手仕舞える。

## 実装するレバー（既定OFF＝base scene_009 と byte 一致・恒等）
### `hold_mom_exit=(M, θ_don)`・新 exit_reason `HOLD_MOM_EXIT`（成行 taker）
- 機構: SHORT 保有・初回entryから **M バー**経過時点で、**含み損側（c[i]>avg）** かつ **donchian_pos[i] ≥ θ_don**（価格が直近20本レンジの上端付近に居続ける＝反転していない＝SHORT 前提が壊れた）→ 成行カット。
- `donchian_pos[i] = (c[i]−min(low[i−19:i+1])) / (max(high[i−19:i+1])−min(low[i−19:i+1]))`（5m・全て≤i＝leak-safe・0-1比＝H6 価格非依存）。＝突破口の momentum 分離指標群を、戦略が自前で計算できる1本（donchian_position・両窓 AUC0.895/0.865）に代表させる。
- 優先順位: 出口判定で TIME_EXIT より前（早く切る）。BE_EXIT（建値撤退）の後（建値に戻る玉は守る）。
- パラメータ（採点窓不参照 L-267）: M∈{6,12}本（30/60分）は a-priori 候補・θ_don は学習窓で「時間切れ捕捉と勝ち玉巻き込み」から選定（or a-priori 0.8）。学習窓で当たりを付け、両窓 score.py で採否。

## 取引所仕様の整合（exchange_spec ★決済方法 / cat_requirements §6.1・6.1.1 read 済）
- HOLD_MOM_EXIT は SHORT 1ポジ（同サイド merge・平均建値）の **全 size を一括成行決済**（部分決済でない＝段階利確 scale out とは別の能動クローズ）。avg=平均建値で含み損判定（c>avg）。
- 予算 0.12 BTC は全建玉合計の上限（H1）＝決済はそれを下げる方向のみ＝cap 不変（_verify_cap で max≤0.12 を実測）。
- add で積み上げた合計 size を HOLD_MOM_EXIT が一括クローズ（reduce 方向）＝取引所仕様（close_market_order・size 指定可）と整合。

## ★疑似シミュ由来の固定値ゼロ宣言（必須）
- M・θ_don は学習窓選定 or a-priori。probe で出した特定数値（AUC0.9・+60分・donchian0.89 等）を設計の固定値に焼かない＝それらは「どの指標・いつ効くか」の当たり付けで、閾値は学習窓 or a-priori。
- 採否は probe/AUC でなく **実エンジン両窓 score.py の数字だけ**（学習窓 純増＋採点窓 base $1043 超え＋⑨巻き込み＋非degenerate）。

## ★ARC マーカー（承認時に凍結保存）
<!-- ARC order=10 iter="hold-mom-exit" 前提="nofloor OFF (base=scene_009)" 採否="検証中" base_csv="trades_e36_short_oscillation_scene_009_score.csv" score_csv="" train_csv="" 狙い="時間切れ −$1,122 の本体（反転しない片流れ）を、entry時点でなく保有~60分の momentum 反転（両窓AUC0.9+で死ぬ玉を教える）で早期手仕舞い＝過去4回の『entry時点/固定深ストップ』と別物" 内容="SHORT 保有M バー経過＋含み損側＋donchian_pos≥θ_don（反転せずレンジ上端に居続ける＝前提崩壊）で成行カット HOLD_MOM_EXIT" 方法="θ_don/M は学習窓選定/a-priori→両窓 score.py で base scene_009 超え＋⑨巻き込み（勝ち玉133玉+$2,407を切らない）＋非degenerate を確認・割れたら不採用" -->

## B. 深掘り4点
- **① 真因**: 時間切れ −$1,122 の本体は「Entry後に反転せず逆行し続ける玉」を 4h 持つこと。Entry時点指標では勝ち玉と分離不能（網羅で確定）＝分離できるのは保有経路のみ。保有~60分で momentum（donchian/RSI/RCI 等）が両窓 AUC0.9+ で分離＝「反転前提が壊れた」を教える。
- **② 期待値分解**: 敗率×平均損失を下げる（反転しない玉を60分で −数$〜十数$に圧縮・勝ち玉は反転して順行するので donchian が下がり残る）。
- **③ root か symptom か**: 「切る」family（過去4回採用に至らず）だが過去は「entry時点 or ML予測 or 固定深ストップ」。本件は **保有経路 momentum・両窓 AUC0.9+・a-priori 指標**＝formulation が別。⚠️反証（Baur & Dimpfl: 損切りは買い持ちに負けがち＝弱い損玉も必ずしも落ち続けない）を踏まえ、両窓ロバスト性を最初に疑う規律を維持（学習窓で純増を先に確認・固定損切りでなく momentum 反転確認で切る）。
- **④ ベースアップ**: [Leung & Li 1411.5062（mean-reversion 最適 Exit＝前提崩壊で早期手仕舞い）](https://arxiv.org/abs/1411.5062)／[QuantPedia（momentum 否定で Exit）](https://quantpedia.com/cryptocurrency-trading-research/)／[Baur & Dimpfl（cut losers の反証＝規律の根拠）](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4233700)／網羅 sweep（2724指標両窓・一次ソース）。

## C. 変更の単位（H16）
- 変更は **1レバー**（hold_mom_exit）。既定 OFF（hold_mom_exit=None）で base scene_009 と byte 一致・恒等。自己検査で確認。
- 不再演: DYING_CUT（ML predict・含み損側）/ STRUCT_SL（固定深%）/ entry-gate（入口分類器）と差分＝本件は **保有経路の a-priori momentum 指標（donchian）で M バー後に判定**（ML予測でも固定深ストップでもentry時点でもない）。両窓 AUC0.9+ の分離が過去案（entry時点 AUC0.66）と桁違い。

## D. ★審判（score.py / eval_engine）整合
- **新 exit_reason `HOLD_MOM_EXIT` を出す → score.py の TAKER_EXIT_REASONS に登録＋既知答えテスト再pass（H3/H13・§2.9）**。成行カット=taker+slip（_record_lots が maker群以外を自動 taker 化）。
- judge（score.py/eval_engine）の計算式に触れない（H13・登録のみ）。eval_engine 不変。
- サイドカー params.json に hold_mom_exit(M,θ_don) を追記（report 節0 自動表示・read 専用）。
- 出力は共通の書き出し処理（_output_and_report・ratchet_io）＝--tag で連番・base scene_009 を上書きしない。E36 ファイルのみ（E35/strat_base 不変・score.py は登録のみ）。

## E. §4.6 ハード制約 照合
- **H1 cap**: 決済のみ＝cap 不変。_verify_cap で max≤0.12 assert。
- **H2 leak**: donchian_pos は ≤i のみ（min/max は過去20本＝未来参照なし）。閾値は学習窓 fit。冒頭 `shift(-`/`center=True` grep assert。
- **H5 約定**: HOLD_MOM_EXIT=成行 taker+slip。他は不変。
- **H6 価格非依存**: donchian_pos=0-1比・含み損判定は c>avg（比較）＝無次元。USD 絶対値なし。
- **H8 期間分割**: M/θ_don は学習窓<2025-03。採点窓 評価のみ・封印不参照。periods.py。
- **H9 最小注文**: size 不変（決済）。
- **H13 judge 固定**: score.py は HOLD_MOM_EXIT 登録＋既知答えテスト再pass のみ。eval_engine 不変。
- **H15 ボラ逃げ**: donchian は方向スコアでなく **Exit 判定**に使う（保有中の前提崩壊検知・§軸1 フィルタ用途は明示許可）。entry 方向シグナル不変。
- **H16 1変更・不再演**: 上記 C。

## F. 受け入れ判定（採点前ゲート）
- **自己検査**: ① 恒等（hold_mom_exit=None で base scene_009 と net byte 一致）② size保存 ③ cap ④ leak grep assert ⑤「わざと壊して落ちるか」＝θ_don を 0 にすると含み損側の全玉が M バーで即カットされ件数・出口が激変するのを確認（メタ確認）。
- **学習窓で純増を先に測る**（採点窓不参照・「切る」family なので学習窓過剰適合の兆候を最初に確認）。
- **公式判定は両窓 score.py**: M×θ_don の a-priori 候補を採点 → **学習窓 純増＋採点窓 base $1043 超え＋⑨巻き込み（勝ち玉133玉+$2,407 を切らない＝donchian で守られる）＋非degenerate** を満たすものだけ採用。割れたら正直に不採用と記録（probe で諦めず実エンジンの数字を出してから判定）。
- **数字表をチャットに出す**（M×θ_don 別・採点net/学習net/件数/勝率/出口内訳/⑨巻き込み）＝結果を全部 提示してから採否。

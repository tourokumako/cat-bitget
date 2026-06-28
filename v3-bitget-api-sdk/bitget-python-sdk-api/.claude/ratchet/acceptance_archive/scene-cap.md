# acceptance.md — ②勝ち場面を cap まで厚く（scene-size top tier 2.0→2.5）

TARGET: scripts/priority_rebuild/e36_short_oscillation.py

DESIGN_CONTRACT:
```json
{
  "impl_file": "scripts/priority_rebuild/e36_short_oscillation.py",
  "self_check_calls": ["_SCENE_TIERS", "_scene_unit", "scene_cap", "held_total"]
}
```

## 変更の単位（H16・1ターン1変更）
- 変更は **1レバー**＝scene-size の最良バケット倍率を 2.0→2.5（勝ち場面が予算 cap を使い切る）。
- **既定 OFF で恒等**：新フラグ `scene_cap`（既定 False）＝`_SCENE_TIERS=[0.5,1.0,1.5,2.0]` のまま＝scene_009 と byte 一致。ON で top tier のみ 2.5。
- 過去に不採用とした手の再演でない（経緯照合は B 深掘り④・analysis_block ⑧）。

## B 深掘り4点
### ① 真因（root cause）
net が勝ち場面 add2玉に超集中（採点窓 9%玉で83%net・$865/$1043）。現状 最良バケット倍率2.0×で勝ち場面 add2＝0.096 BTC＝**予算 cap 0.12 を使い切れていない**（add3 は 0.144>cap で既にブロック＝cap が天井）。＝最も robust なエッジに予算を全振りできていない取りこぼし。同サイドは1ポジに merge・平均建値で積み上げ（exchange_spec 決済方法・§6.1.1）＝add2 で size 0.12 に到達できる。
### ② 期待値分解（どの要素を何 pt 動かすか）
勝率・avg勝ち・avg負けは不変（size のみ・出口/方向不変）。**勝ち場面玉の size を ×1.25（0.096→0.12）＝その net を比例して ×1.25**。採点窓 勝ち場面77玉 +$809 → 約+$1011（+$202／全 net $1043→約$1245・~月+$22）。件数+0%。
### ③ root か symptom か（Y/N＋理由）
root。symptom（出口で取りこぼし回収＝iter8-12 で枯渇）でなく、robust な勝ち場面に予算を集中する配分の本丸（E13/scene-size 系＝効いた型）。
### ④ ベースアップ（KB/WebSearch 証跡）
WebSearch（直近・allowed_domains＝quantinsti/quantpedia/arxiv/ssrn 等）: **Kelly/fractional Kelly＝per-trade edge で sizing・signal-strength sizing＝強いシグナルで full・弱いで half**（[quantinsti position-sizing](https://blog.quantinsti.com/position-sizing/) / [quantpedia position-sizing](https://quantpedia.com/position-sizing/)）。edge は過大評価されがちなので **fractional（f<1）で保守**＝②の a-priori 上限つき（full Kelly でない）と整合。overbet 回避＝cap 0.12 を超えない（H1）。

## ★疑似シミュ由来の固定値ゼロ（必須）
- (a) 倍率 2.5 は probe の数値でなく **幾何由来の a-priori**＝CAP/(2×UNIT)=0.12/(2×0.024)=2.5（最良バケットが add2 で cap を使い切る値）。probe（疑似シミュ）の特定数値（θ/AUC/net 等）を設計に焼いていない。
- (b) バケット割当（どれが最良か）は **学習窓 expectancy 順**（既存 scene-size と同じ・採点窓不参照 H8）。倍率値 [0.5,1.0,1.5,2.5] は a-priori。
- (c) 採否は probe でなく **実エンジン両窓 score.py の数字のみ**（学習窓 純増→採点窓 base $1043 超え）。

## D 審判（score.py / eval_engine）整合
- **新しい exit_reason を出すか？ → No**（size のみ・出口理由は不変）。score.py の MAKER/TAKER 登録・既知答えテスト変更は**不要**。
- **コスト種別（maker/taker）が変わるか？ → No**（出口不変）。
- **judge（score.py/eval_engine）に触れるか？ → No**（H13・計器不変）。
- **サイドカー**: scene 倍率は既存 params_sidecar に記録済（scene_size 節）＝top tier 値を反映。
- **共通の書き出し処理 `_output_and_report`／`strat_base` import**: 既存踏襲（変更なし）。出力は `--tag scenecap` で連番（base scene_009 を上書きしない）。

## E §4.6 ハード制約 照合
- **H1**（cap 0.12 合計）: ✅ 既存 `held_total()+u>CAP: return` が entry/add で各時点合計を実測しブロック＝2.5× でも add3 が skip され H1 厳守。予算0.12は全建玉合計（§6.1）。score.assert_hard_constraints が採点時に時系列 cap を再検証。
- **H6**（価格非依存）: ✅ 倍率は無次元・size は BTC 単位。
- **H8**（期間分割）: ✅ バケット最良判定は学習窓 expectancy・採点窓不参照。
- **H9**（最小注文）: ✅ `_scene_unit` は MIN_ORDER_BTC でフロア。
- **H13**（judge 固定）: ✅ eval_engine/score.py 不変。
- **H15**（ボラ逃げ禁止）: ✅ size のみ・**方向は不変**（atr を方向スコアに使わない＝scene-size と同じ安全形）。
- **H16**（1変更・不再演）: ✅ 1レバー・L-267/L-297/freq-iter の再演でない（④/⑧）。
- 非該当: H2/H5/H7/H10/H11/H12/H14（出口・約定・足・期間・発注フラグ 変更なし）。

## F 受け入れ判定（採点前ゲート）
- **自己検査**: ① 恒等＝`scene_cap=False` で `_SCENE_TIERS` 不変→売買記録が scene_009 と byte 一致（diff 0）。② cap＝2.5× で全玉 size 合計 ≤0.12（assert_hard_constraints PASS・わざと cap 超データで停止するか番人確認）。③ size 保存 assert 既存。
- **学習窓で純増を先に確認**（$2079 超＋件数+0%＝degenerate でない）→ ダメなら即見切り。
- **公式判定は score.py 両窓**（採点窓 $1043 超を確認するまで「効いた」と言わない）＋⑨巻き込み（勝ち玉 fat-tail を刈らない＝size 増のみ）。

<!-- ARC order=10 iter="scene-cap" 前提="nofloor OFF (base=scene_009)" 採否="検証中" base_csv="trades_e36_short_oscillation_scene_009" score_csv="" train_csv="" 狙い="net が勝ち場面 add2玉に超集中(9%玉で83%net)＝robust な勝ち場面に予算cap を使い切れていない取りこぼしを、最良バケット倍率を cap 使い切りまで上げて規模拡大(E13/scene-size の cap 活用・取り高で月$500 への step1)" 内容="scene-size 最良バケット倍率 2.0→2.5(=CAP/(2×UNIT)・幾何由来a-priori)＝勝ち場面 add2 が 0.096→0.12(cap)。size のみ・方向不変・既定OFF恒等" 方法="学習窓 純増(>2079)→両窓 score.py(採点窓>1043)＋H1 cap厳守＋⑨巻き込み(勝ち玉を刈らない)＋恒等byte一致。割れたら採用に至らずと記録" -->

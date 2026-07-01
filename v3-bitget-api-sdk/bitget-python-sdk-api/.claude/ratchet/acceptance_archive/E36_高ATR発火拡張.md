# acceptance.md — E36 高ATRレンジ発火拡張（W正常帯の上限を緩め広い高ATR箱を入口に取り込む・2026-06-30）

TARGET: scripts/priority_rebuild/e36_short_oscillation.py

```DESIGN_CONTRACT
{
  "impl_file": "scripts/priority_rebuild/e36_short_oscillation.py",
  "self_check_calls": ["wide_box_q", "_box_w_band"]
}
```

## B. 深掘り4点
- **① 真因**: E36 のエッジは高ATRレンジに集中（G節 ATR%0.2-0.4 で avg+$14〜16・N12 atr≥中×stoch_k<中 net$1,004=全体の81%・N10 atr_pct+0.213 両窓✓）。だが入口の W正常帯が学習窓 in_box 箱幅 W を [q0.25, q0.75] に限定し、**高ATR＝箱幅が広い箱が上限 q0.75 を超えて入口候補に通らない**（e36 `_build_signals_for_tf` line150 `w_ok: in_box & W>=w_lo & W<=w_hi`）。結果 低ATR(0-0.2)が285件中210件(74%)で avg+$0.98 と薄く、濃い高ATRを構造的に取りこぼす。
- **② 期待値分解**: 動かすのは「件数」（高ATR帯の新規 SHORT を増やす）。高ATR玉は avg+$14〜16＝既存の +$EV をそのまま件数で積む。勝率(76%>必要64%)・平均勝ち($13.31)・平均負け($20.78)は維持狙い（希釈したら学習窓で純増にならず不採用）。期待＝総net = 件数↑ × avg維持。
- **③ root か symptom か**: root。最易パッチ（時間切れ片流れを切る）は L-309 で5回不採用＝symptom 追い。本案は「在るエッジ(高ATR)の取りこぼし」という入口設計の root を直す。
- **④ ベースアップ（WebSearch/WebFetch 2026-06-30）**: Hudson&Thames メタラベリング（[toy](https://hudsonthames.org/meta-labeling-a-toy-example/)/[efficacy](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/)）＝**primary を広め(高recall)で発火させ secondary が precision を保つ。広げて効くのは false positive が予測可能に偏る時／ランダムだと希釈・primary が黒字なのが前提**（E36 は黒字 primary＝適格・既存 hold-ML 判別器が secondary）。QuantPedia＝BTC 平均回帰は短horizonで効くが trending regime で劣化＝上位足momentum条件づけが要る（E36 の 1h MACD≤0 ゲートと整合）。QuantifiedStrategies Rectangle＝箱が背が高い時だけ取る（高ATR=値幅が手数料を超える）。⚠️ メタラベ OOS gain は modest（precision 0.17→0.20）＝判別器の希釈除去は完全でない→**採否は両窓 score.py で確認（効くと仮定しない）**。

### ★疑似シミュ由来の固定値ゼロ
- W正常帯の上限分位は **学習窓 in_box の箱幅 W 分布から `_box_w_band` がデータ駆動で算出**（freq-iter1 と同じ・採点窓不参照 H8/L-267）。probe で出した特定数値を焼かない。
- (a) 値＝学習窓分位 or a-priori（既定は現行 q0.75=恒等）。(b) probe の数値を設計の固定値に焼いていない。(c) 採否は probe でなく**実エンジン両窓 score.py**。

## ★ 決済方法の確認（exchange_spec ★決済方法 / cat_requirements §6.1.1・just-in-time 読了 2026-06-30）
- 同サイドは1ポジに merge・平均建値／予算0.12は全建玉 size の合計上限（H1）／決済は全体も部分も可（複数TP scale out 最大20）。本レバーは**入口（新規 SHORT の発火）を増やすだけで、add(merge平均建値)・部分利確・cap0.12・出口は一切変えない**＝決済設計に手を入れない（L-255 の誤解に該当しない）。

<!-- ARC order=15 iter="E36 高ATR発火拡張" 前提="nofloor OFF (base=scenecap_012)" 採否="検証中" base_csv="trades_e36_short_oscillation_scenecap_012_score.csv" score_csv="" train_csv="" 狙い="エッジが集中する高ATRレンジ(avg$14-16)を W正常帯の上限が通さず取りこぼしている分を拾い件数側で net を伸ばす(サイジングはcap使い切り済)" 内容="W正常帯の上限を学習窓分位で緩め広い高ATR箱を入口候補(w_ok)に通す新フラグ wide_box_q を追加・既定は現行q0.75=恒等・保有/出口/add/判別器/サイジングは不変" 方法="--diagnostic で高ATR admit 件数増を確認→学習窓で純増→両窓 score.py で base$1237超え＋⑨非該当(勝ち玉を切らない)＋恒等byte一致＋H1cap厳守。割れたら採用に至らずと記録" -->

## C. 変更の単位（H16・1ターン1変更）
- 変更は **1レバー**＝W正常帯の上限分位を緩める新フラグ `--wide-box-q`（dest `wide_box_q`）。`_box_w_band` の上限 q を `wide_box_q`（既定 None=現行 W_Q_HI=0.75）で置換し、広い高ATR箱を `w_ok` に通す。下限・zone・反転確認・add・出口・hold-ML・scene-cap・spike は一切不変。
- **既定 OFF で恒等**: `wide_box_q=None` で現行 q0.75 と完全一致（base scenecap_012 と byte 一致を自己検査）。
- 過去失敗の不再現: freq-iter2（全体で件数増→希釈・採用せず）と差分＝**高ATR(広い箱)限定で増やす**（全体を緩めない）。entry-gate（絞る→過剰適合）と逆方向（広げる）。DYING_CUT/STRUCT_SL/hold-mom-exit（切る系・L-309）は触らない。

## D. 審判（score.py / eval_engine）整合
- **新しい exit_reason を出すか？ → NO**（入口を増やすだけ・出口は既存の TP/SL/TIME/BE/SPIKE/CENTER/EDGE/PARTIAL のまま）。score.py の EXIT_REASONS 登録・既知答えテスト再pass は不要。
- entry/exit のコスト種別（maker/taker）は不変。judge（score.py/eval_engine）の計算式に触れない（H13）。
- 出力は共通の書き出し処理 `_output_and_report`（strat_base 経由 ratchet_io）を使い `--tag` で連番（採用前＝base 名を pre-declare しない）。サイドカー `<stem>_params.json` に wide_box_q の実使用値＋W正常帯 [lo,hi] を記録（report 節0 が自動表示）。
- e35/strat_base は触らない（E36 独立）。採用 base CSV（scenecap・085d4b2f 系）を上書きしない（--tag 必須）。

## E. §4.6 ハード制約 照合
- **H1** cap 合計 0.12 BTC＝`_verify_cap` で実測（高ATR玉が増えても scene-cap が cap 0.12 厳守・self check max≤0.1200）。
- **H2** leak なし＝`_box_w_band` は学習窓（<TRAIN_END）の W 分布のみで分位算出（採点窓不参照）。特徴量に未来参照なし（`shift(-`/`center=True` grep clean）。
- **H5** 約定モデル不変（entry 指値maker close×(1+0.0001)・TTL3 / 出口は既存）。
- **H6** 価格非依存＝W は箱幅%（box_W_pct）・分位ベース＝USD絶対値でない。
- **H8** 期間分割＝periods 由来（学習<2025-03 で fit・採点 2025-06〜2026-02 評価のみ）。
- **H13** judge 固定（score.py/eval_engine 改造なし）。
- **H15** ボラ逃げ禁止＝**非該当を確認**: 本案は方向スコアに atr/ボラを支配させるのでなく、入口の「箱の広さ（高ATR=うまみのある swing）」を通すだけ。方向判定（stoch反転・1h MACD≤0）は不変。atr_pct は方向でなく場面選別＝H15 罠回避（scene-size と同じ役割）。
- **H16** 1変更（W正常帯上限のみ）・過去失敗の不再現（freq-iter2/entry-gate/切る系と差分明記済）。

## F. 受け入れ判定（採点前ゲート・PDCA §8.4）
- **自己検査**: ① 恒等＝`wide_box_q=None` の採点CSV が base scenecap と byte 一致（diff 0）。② SHORT専用（LONG玉0）。③ size 保存（Σsize=add×UNIT×倍率）。④ cap max≤0.1200。⑤ leak grep（shift(-)/center=True）clean。⑥ 番人メタ＝`_box_w_band` にわざと採点窓データを渡すと分位がズレる（H8 違反検出）ことを確認。
- **--diagnostic**: 高ATR(ATR%≥0.2)帯の admit 件数が増えるか・全体件数の増分・W正常帯 [lo,hi] の変化を表示（degenerate=低ATRノイズ大量増でないか）。
- **学習窓で純増を先に測る**（採点窓不参照）→ プラスかつ非degenerate なら採点へ。
- **公式判定＝両窓 score.py**（CC は net 計算に触れない）。採点窓 base $1237 超え＋学習窓純増の**両窓改善**を確認するまで「効いた」と言わない。割れたら採用に至らずと記録（地面 scenecap 維持）。
- degenerate でないか（件数増が高ATRの+EV玉か・低ATRの薄い玉の水増しでないか玉単位で確認）。

---
**進め方**: 本 acceptance 承認（approve_impl）→ 実装（1ファイル・既定OFF恒等）→ --diagnostic → 学習窓純増 → precheck → 両窓 score.py。承認待ち。

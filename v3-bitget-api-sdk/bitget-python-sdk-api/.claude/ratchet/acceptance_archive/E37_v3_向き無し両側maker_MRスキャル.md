# acceptance — E37 v3 作り直し（向き無し両側 maker MR スキャル・高頻度）

TARGET: scripts/priority_rebuild/e37_range_scalp.py
TARGET: scripts/priority_rebuild/score.py

（score.py は新 exit_reason `TREND_CONT` を TAKER_EXIT_REASONS に1語追加するのみ＝判定器の計算式は不変・既知答えテスト再pass で担保・H13。）

```json DESIGN_CONTRACT
{
  "impl_file": "e37_range_scalp.py",
  "self_check_calls": ["not_trend", "micro_rev", "TREND_CONT", "SCALP_FLOOR", "ADX_HI_Q"]
}
```

## 位置づけ（§1.2.1 局面3 レンジ・スキャル型・E36 デイトレと住み分け）
E37 は「入口で向きを当てる」路線（v1深入口/v2出来高fade/総当たり検証/MVPレンジ学習ゲート）で ARC11/13/14/16 いずれも採用に至らず（地面マイナスを ratchet で維持）。base-up（arxiv 2606.29591）＝**短期反転の向き（sign）は予測不能、幅（magnitude）は予測可能**。→ 路線転換＝**向きを賭けず、両側 maker で行き過ぎの戻り幅を高頻度に取る**。最大の欠陥＝0.32件/日＝スキャル役割違反を、件数を仕組みから出して直す。新 MVP（アジャイル・地面を作り直す）。

## B. 深掘り4点
- **① 真因**: net 赤の真因は2つ。(a) 0.32件/日＝スキャルになっていない（4選別ゲートの重ね掛け）。(b) 入口で向きを当てにいって当たらない＝base-up が示す通り短期反転の向きは予測不能（コイン投げ）・幅は予測可能。
- **② 期待値分解**: MVP 必要勝率53.5%/実43.5%/不足10pt。向き当てで勝率を上げるのでなく（向きは予測不能・幅は予測可能）、**「多数の件数×小さい確実な戻り幅（maker で手数料勝ち）」で expectancy を作る**。1件あたり期待値は小でも件数（数十/日）で総 net を積む（KB §0#4・MR は勝率60-85%だが1件小・件数で積む）。
- **③ root か symptom か**: root＝入口の設計思想（向き当て・選別過多）。symptom パッチでなく、入口を「向き無し両側 micro 反転・緩い非トレンド地合い」に作り直す root fix。
- **④ ベースアップ**: [QuantifiedStrategies](https://www.quantifiedstrategies.com/bitcoin-mean-reversion-strategies-outperform-momentum-in-low-volume-regimes/)（MR は低出来高consolidation で勝率60-85%・コスト最大の敵・maker/件数で積む）／[arxiv 2606.29591](https://arxiv.org/html/2606.29591)（向き不能・幅可）／[arxiv 2512.12924](https://arxiv.org/html/2512.12924)（OHLCV微細エッジは小・高ボラで機能・purged CV で過剰適合防止）／[QuantPedia](https://quantpedia.com/revisiting-trend-following-and-mean-reversion-strategies-in-bitcoin/)（BTC は短窓MRが頑健・meta-labeling が効く）／[Hudson&Thames](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/)（Triple Barrier で TP/SL/time ラベル・secondary で取捨）。

## C. 変更の単位
- **1変更**: E37 の入口/出口を「向き無し両側 maker MR スキャル」に作り直す（新 MVP・E37 は未採用＝地面マイナスなので恒等制約なし＝アジャイル MVP 差し替え）。
- **★疑似シミュ由来の固定値ゼロ**: (a) 全パラメータは **a-priori** or **学習窓分位**（Z_HI/Z_LO=学習窓 dev_z 分位・ADX_HI_Q=学習窓 adx 分位）＝probe で出した特定数値を焼かない。(b) probe（rejection/frequency）の数値はあたり付け専用で設計の固定値にしない。(c) 採否は probe でなく **実エンジン両窓 score.py**。採点窓でのスイープ禁止（L-267）。
- **過去失敗の不再演**: 向き当て（S/R幾何レンジ学習ゲート・ダイバ・出来高fade）を繰り返さない＝撤去。切る系（DYING_CUT/STRUCT_SL）の広い早切りを繰り返さない＝早切りは「トレンド化」限定（⑨巻き込み検証）。

<!-- ARC order=17 iter="E37 v3 向き無し両側maker MRスキャル" 前提="新MVP・E37未採用・地面マイナスから作り直し" 採否="未(実装前)" base_csv="trades_e37_range_scalp_mvp_004_score.csv" score_csv="" train_csv="" 狙い="入口で向きを当てる路線(ARC11/13/14/16 いずれも採用に至らず)を捨て、base-up(向き不能・幅可)に沿って向きを賭けず両側makerで行き過ぎの戻り幅を高頻度(数十/日)に取り、0.32件/日=スキャル役割違反を件数を仕組みから出して直す" 内容="入口=緩い非トレンド地合い(adx<学習窓分位)∩短期dev_z行き過ぎ∩反転バーで反対側にmaker指値(両側)。厳格な箱/range_score/ダイバ/高ATRの4ゲート撤去。出口=平均へ浅いmaker TP＋トレンド化早切りTREND_CONT＋短time-exit＋ATR-SL" 方法="--diagnostic で件数(数十/日)確認→本走→precheck→両窓score.py。件数を一級基準・両窓でE36+E37合算月600へ・probe値は焼かない" -->

## D. 審判整合
- **新 exit_reason**: `TREND_CONT`（トレンド化 早切り・成行 taker）を出す → **score.py の TAKER_EXIT_REASONS へ登録＋既知答えテスト再pass** を「やること」に含める（H3/H13・未登録は §2.9 STOP）。他は既存名（TP_FILLED/SL_FILLED=maker・TIME_EXIT=taker）。
- **コスト種別**: entry=指値maker / TP=指値maker / SL=指値maker / TIME_EXIT・TREND_CONT=成行taker+slip（eval_engine 分類と一致）。judge の計算式は触らない（import のみ）。
- **命名/出力**: 実験は `--tag <名前>` で連番（require_tag_for_experiment）。出力・サイドカーは `strat_base._output_and_report` 経由。共通土台 `strat_base` を import。
- **サイドカー**: _param_sections を新設計に更新（実使用の入口/出口ロジック・閾値・TP/SL/TimeExit を記録・report 節0）。

## E. §4.6 ハード制約 照合
- **H1 cap**: MAX_ADDS=1・size=UNIT 0.024・単一スロット＝合計≤0.12 自明＋_verify_cap 実測 assert。
- **H2 leak**: dev_z/adx/atr/sma は当該足まで（causal）・分位 fit は学習窓の行のみ・出口は約定 bar の次以降・`shift(-`/`center=True` 自己 grep assert。
- **H5 約定**: entry=指値maker(close×(1∓ENTRY_OFFSET))・TTL3・不約定は積まない（maker限定）／TP・SL=指値maker／TIME・TREND_CONT=成行taker+slip。
- **H6 価格非依存**: dev_z（σ比）・adx（無次元）・atr_pct（%）・TP=SMA・SL=ATR比・TREND_DZ=σ比。USD 絶対値の閾値/ラベルなし。
- **H8 期間**: 分位 fit は学習窓（periods import・手打ちなし）・採点窓不参照・封印不参照。
- **H13 judge**: 新 exit_reason `TREND_CONT` は score.py の理由リストへ登録＋既知答えテスト再pass のみ（計算式は不変）。
- **H15 ボラ逃げ**: **向きスコアを持たない設計**（向きを当てない＝両側）。atr は SL/TREND_DZ のスケール＝方向スコアの主役でない。adx は「強トレンド除外」フィルタ（方向でなく地合い）。
- **H16 1変更**: E37 入口/出口を1本の新 MVP に作り直す（過去失敗の向き当て/広い早切りを再演しない）。

## F. 受け入れ判定（採点前ゲート・PDCA §8.4）
- **自己検査**: cap 実測 max≤0.12（_verify_cap・H1）／leak 自己 grep（H2）／--diagnostic で件数（**目標 数十/日＝スキャル頻度**・degenerate でない）を先に確認。
- **学習窓で先に測る**（採点窓不参照・H8）: precheck の breakeven 倍率・件数。**件数がスキャル水準（数十/日）に達しているか**を第一に確認（達しなければ入口を直す＝net の前に件数）。
- **公式判定は score.py 両窓**（CC は net 計算に触れない＝import のみ）。**この iter の合格基準（enforce_role_criteria・scalp）＝件数/日を大きく上げる（数十/日＝スキャル頻度を実現）**こと。net はマイナスでも「スキャル頻度を満たした地面 MVP」として残し、次 iter で net を ratchet。頻度を上げる設計を第一義とする（低頻度のまま net を後回しにする尻すぼみは役割違反として却下）。
- **⑨巻き込み検証**: TREND_CONT 早切りが勝ち玉（MFE大の反転往復玉）を切っていないか、実装後 analyze で数字確認。
- degenerate でない（件数を玉単位で確認）。

## やること（実装項目・1つずつ照合）
1. 入口を作り直す: `not_trend`（adx<学習窓分位 ADX_HI_Q）∩ `micro_rev`（dev_z 行き過ぎ＋反転バー・両側）で反対側に maker 指値。range_score/ダイバ/高ATR/厳格箱ゲートを撤去。
2. 出口: 浅TP=SMA戻り（maker・SCALP_FLOOR 武装）／`TREND_CONT`（保有中 dev_z が entry から TREND_DZ 拡大＝トレンド化で成行 taker 撤退）／短 time-exit（T_MAX・taker）／ATR-SL backstop（maker）。
3. score.py の TAKER_EXIT_REASONS に `TREND_CONT` 追加 → 既知答えテスト再pass。
4. パラメータは a-priori/学習窓分位のみ（Z_HI/Z_LO/ADX_HI_Q=学習窓分位・TREND_DZ/SCALP_FLOOR/T_MAX/K_SL=a-priori）。probe 値を焼かない。
5. _param_sections を新設計に更新（サイドカー）。
6. --diagnostic で件数（数十/日）→ 本走 --tag → precheck → 両窓 score.py → report --vs → analyze。

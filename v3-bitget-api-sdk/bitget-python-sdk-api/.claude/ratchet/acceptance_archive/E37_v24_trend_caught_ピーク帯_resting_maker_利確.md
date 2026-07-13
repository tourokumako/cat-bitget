# acceptance — E37 v24（trend_caught 玉のピーク帯 resting maker 利確・全固定値）

TARGET: scripts/priority_rebuild/e37_range_scalp.py, scripts/priority_rebuild/score.py

## 網羅マトリクス参照（enforce_combo_matrix）
- **entry_exit_matrix.md グリッド E37 の #31 を実装**（入口据え置き＝#28/#29 継承・Exit＝v23 V9型出口＋trend_caught 玉に建値+0.08% resting maker 利確）。未試行: あり（#7〜#20 ほか＝潰し切るまで続ける）。
- **Exit 状態機械（V9 §9.2 雛形・分岐表）**: v24 が変えるのは trend_caught 玉（uptrend 発火で畳む玉）の分岐だけ:
  - 含み益が建値+0.08% 到達（ピーク帯・費用超え）→ **resting maker 利確 TREND_CAUGHT_TP（★新・反転待ちを置換）**
  - 保有30分 ∩ 含み益が費用未満（B型）→ MFE_STALE_CUT（維持）／ 含み損が災害SL到達 → SL_FILLED（維持）／ 保有240分 → TIME_EXIT（維持）／ stoch GC 反転 → **廃止（遅行で取り逃す）**
  - **稼ぐ玉（通常経路 PARTIAL_TP/TP_FILLED/RANGE_BREAK）の状態機械は現行維持**（v24 は触らない）。
- **単一値 0.08% で足る根拠（コンフルエンス vs 単一閾値）**: 利確ラインの値は単一固定値で足る＝**場面は既にコンフルエンス**（RG-v5 レンジ判定 ∩ armed DC stoch(9,3) ∩ RSI9 ∩ uptrend 状態機械発火＝複数指標×場面別×条件別）で絞り込み済み。この上で利確水準を場面別に細かく変えるのは過剰適合（学習窓選定は採点窓で消える・L-320・v14/v16/v17 実証）＝単一 a-priori 値（0.08%）で足る。Exit の発火自体は上表の優先順位つき複数枝（単一枝でない）。**ML 最適化について＝まこさん指示で v24 は Exit を ML 最適化しない（学習窓が採点窓を予測しないため全固定値）＝L-267 の固定値手調整でなく a-priori 値の実エンジン両窓判定**。
- **決済方式（exchange_spec ★決済方法 読了済）**: trend_caught 玉は SHORT の平均建値1ポジ。resting maker 利確は建値+0.08% の TP 指値（部分決済 scale out 可・maker・Reduce-only・最大20個の枠内）＝既存 PARTIAL_TP/TP_FILLED と同じ maker 決済方式。cap 0.12（合計）は size を変えず維持（§6.1・H1）。

DESIGN_CONTRACT:
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["v24_trend_maker_tp", "TREND_CAUGHT_TP", "V24_TREND_TP_PCT", "V24_FIXED_V22", "range_ok_rg5", "short_only_v11"]
}
```

## LEVER（improvement_plan から逐語引き継ぎ）
<!-- LEVER: trend_caught 玉（uptrend 発火で畳む玉）に建値+0.08% の resting maker 利確を優先枝で置き、反転待ち STOCH_REVERSE_EXIT を置換する（全固定値・学習窓選定なし・MFE_STALE と稼ぐ玉は不変） -->

## ★戦略照合（§1.2.1 係留・enforce_strategy_anchor）
- STRATEGY_ANCHOR 逐語: **e37=range,short_only,scalp**（台帳マーカー・cat_requirements §1.2.1 局面3レンジ）。
- **GATE_IDENT=range_ok_rg5**（入口を担当局面 range で制約する関数＝RG-v5 レンジ判定・v24 は据え置き＝触らない）。
- **SIDE_IDENT=short_only_v11**（SHORT のみの方向機構・v24 は据え置き）。
- 局面/方向/頻度: レンジ（RG-v5 据え置き）／ SHORT のみ（据え置き）／ scalp（件数 3.18/日 維持＝入口据え置きで減らさない・v24 は Exit レバー）。
- **v24 は Exit レバー** <!-- ROLE_EXIT_LEVER --> ＝入口を触らない（件数は入口が決める）。**件数/日を維持**（3.18/日・scalp 頻度を減らさない）＝減れば不採用（尻すぼみでない）。件数増（高頻度化）は入口レバーで扱う（後日の入口 iteration・まこさん承認 2026-07-16・enforce_role_criteria Exit レバー例外）。
- **直近 iter: E37 v23 TREND_CONT の V9 型 Exit 状態機械化（uptrend 発火で成行投げをやめ genuine 反転/stall/災害SL に委ねる）（ledger 読了）**（ARC order=38＝force-close 廃止は方向正しいが V9 stoch 反転が速い5分レンジで遅行し損が STOCH_REVERSE/MFE_STALE へ移動しただけ・ledger 問5 次仮説＝「ピーク到達時点で取る仕組み（利確指値をピーク帯＝往復fee 超えに resting maker で置く・反転を待たない）」＝v24 はこれを実装）。

## ML 宣言（v24 は機械学習を使わない）
- v24 は **ML/教師/分類器/LightGBM を一切使わない＝全固定値**（まこさん指示 2026-07-16＝学習窓が採点窓を予測しないため）。疑似ML でも本物ML でもなく **ML 不使用**。利確ライン L=0.08% は下記の a-priori（学習窓 fit・net 最大選定を一切しない）。**＋v24 は土台の v22 学習窓選定も定数化する（下記やること7）＝入口〜出口すべて固定値**。

## 深掘り4点
- **① 真因**: v23 の採点窓 net −$420 の主因は trend_caught 玉（uptrend 発火で畳む玉）373件 −$1,370。うち STOCH_REVERSE_EXIT 224件 −$906＝**V9 の stoch(9,3) ゴールデンクロス反転を待つ間に、速い5分レンジでは価格が反転して含み益が消え、最悪点で損切りする（遅行）**。この玉の 採点77%/学習86%（両窓）が一度は往復費(0.028%)超えの含み益を持っていた＝逃げ場が実在。
- **② 期待値分解**: trend_caught 玉の平均負け（現状 −$3.67/件）を、反転を待たず費用超えのピーク帯で確定して縮める。crude あたり付けで L=0.08% なら採点窓 対現状 +$724／学習窓 +$2,960（実エンジンで目減り見込み）。稼ぐ玉（平均勝ち）は触らない。
- **③ root か symptom か**: **symptom 寄りだが正当**。根本（root）は「uptrend 相場をレンジ誤認して SHORT を入れる」入口の regime 判定（PNG 2025-09-29〜10-06 で実証・入口レバーで後日）。v24 は「入ってしまった玉の損を止める」執行（②執行）の改善＝まこさん指示「2（Exit）から改善」。入口の根本は次レバー。
- **④ ベースアップ**: range_scalping_kb §9（V9 出口状態機械・読了済）／ trade_analysis_methods_kb §3（MFE 較正＝MFE中央値×60-70%＝TP 較正基準・読了済）／ analysis_playbook §2（読了済）。**＋WebResearch 2026-07-16（3種別）**: (a) 学術 arxiv 1411.5062（Leung & Li・Optimal Mean Reversion Trading with Transaction Costs and Stop-Loss Exit）＝**「深い stop-loss は浅い最適 take-profit を要求」**＝v24 の深い災害SL維持＋浅い利確 L=0.08% と理論整合 (b) QuantifiedStrategies＝**平均回帰は「利を早く取り、損は走らせる」性質**＝反転を待たず取る v24 と整合（損の走りは深い災害SL/TIME で抑える） (c) Hudson & Thames（Minimum Profit Optimization）＝利確境界は「頻度 vs 利益/件」のトレードオフ（低い L=高頻度・小利）＝crude の単調性と一致。L=0.08% は §9.3 の「robust な固定値は広い・粗い・単一水準」＋§3 較正基準に整合。

## ★疑似シミュ由来の固定値ゼロ（require_acceptance hook・まこさん承認 2026-06-26）
- **(a) 各値の出所**: L=0.08% は **既存の手数料床 SCALP_FLOOR（=0.08%・往復 maker 0.028% の約2.9倍・戦略に既存の a-priori 定数）** ∩ **MFE 較正の業界基準（trend_caught MFE 中央値 0.095-0.135% × 60-70% = 0.057-0.095%）** の a-priori。probe（trend_exit_peak_diag）で出した特定の数値ではない。V24_FIXED_V22 の値（cell0/M24）は v22_042 で既に採択された値の定数継承（新規スイープでない）。
- **(b) probe の数値を焼いていない**: trend_exit_peak_diag / entry_pos_diag は分布の**あたり付け専用**（費用超えの含み益が両窓 77-86% 存在すること・L が低いほど損を止めることの確認）。採点窓 net が最大の L の一点（crude では L=0.028）を焼かない（L-267）。
- **(c) 採否は実エンジン両窓 score.py**: L=0.08% を固定で実装し、precheck＋両窓 score.py の数字で採否を決める（学習窓選定なし）。

## スキャル一級基準（enforce_e37_pdca acceptance 段・⑦⑨⑫）
- **⑦ 手数料を超える TP 幅**: 利確幅 L=0.08% ≥ maker 往復 0.028%（2.9倍）＝手数料負けしない（KB §4/§6）。
- **⑨ 短保有（分単位）**: trend_caught 玉を反転待ち（保有 60分〜）から建値+0.08% 到達で早く畳む＝保有短縮（分単位・保有4h再演防止）。
- **⑫ 5分足設定 RSI9/MTF**: 据え置き（RG-v5 1h S/R×5分執行・armed DC stoch(9,3)・RSI9・MTF＝v23 と同一・technical_kb §4/§5）。

## D 審判整合（acceptance_checklist D・出戻り防止）
- **新 exit_reason `TREND_CAUGHT_TP`（maker 指値決済）を出す** → score.py の **MAKER_EXIT_REASONS に登録＋既知答えテスト（test_eval_engine_known_answers or score self-test）を再pass**（H3/H13・未登録 exit_reason は §2.9 で採点 STOP）。約定方式＝resting 指値 maker（建値+0.08% に置く post-only）。★TARGET に score.py を含める（この登録の編集）。
- 廃止する STOCH_REVERSE_EXIT は登録済み（残す玉が無くなるだけ・登録は消さない）。MFE_STALE_CUT（taker）・SL_FILLED（maker）・TIME_EXIT（taker）は不変。
- eval_engine / score.py の計算式には触れない（H13・追加は MAKER_EXIT_REASONS への1語のみ）。

## やること（実装項目・1レバー＋学習排除）
1. **フラグ `--v24-trend-maker-tp`（既定 OFF=v23_043 恒等）** を追加。OFF で v23 と md5 一致（恒等）を自己検査で確認。
2. **trend_caught 玉（uptrend 発火で `_keep20` に残る玉）の Exit ループに、優先枝 `v24_trend_maker_tp` を追加**＝建値×(1−`V24_TREND_TP_PCT`/100) に resting maker 指値（SHORT の利確＝価格が下がる方向）を置き、到達したら `TREND_CAUGHT_TP`（maker）で決済。`V24_TREND_TP_PCT = 0.08`（a-priori 固定値・スイープでない・単一値の根拠は上の網羅マトリクス節）。
3. **STOCH_REVERSE_EXIT 枝を trend_caught 玉について無効化**（v24 ON 時・stoch GC 待ちを廃止）。MFE_STALE_CUT（保有30分∩含み益<gate）・災害SL・TIME backstop は現行のまま残す。
4. **通常経路（稼ぐ玉）の PARTIAL_TP/TP_FILLED/RANGE_BREAK は一切触らない**（v24 は trend_caught 分岐のみ）。
5. **H2 leak なし**: resting maker 指値は建値（entry 時に確定）+ 固定% ＝その時点で取得可能（未来参照なし）。mfe/mae は使わない（実装は建値基準の固定水準）。
6. **サイドカー**（params.json）に v24 の枝・L=0.08% を記録（report §0 自動表示）。共通の書き出し処理 `_output_and_report`（ratchet_io）を使う。
7. **★v22 の学習窓選定を定数化（まこさん指摘 2026-07-16・入口〜出口すべて固定値＝学習ゼロ）**＝v24 ON 時は `_select_v22_params`（v22 greedy 選定＝①入口 ②TP アンカー ③peak_fold ④warn）を走らせず、v22_042 の採択値を `V24_FIXED_V22 = {"v22_anchor": {0: 24}}`（他は None＝v22_042 採択どおり・`V22_FIXED_V21_*` と同型）として定数継承する。v21 の採択は既に定数継承済み。＝入口（v21 armed DC）〜TP アンカー（cell0/M24）〜出口すべて固定値・**学習ゼロ**。数字は v22 選定結果（cell0/M24）と一致＝**数字を変えるのは resting maker 利確のみ**（v22 定数化は学習排除・数字不変・H16 の1変更を守る）。自己検査で「v24 ON かつ V24_FIXED_V22 継承 の学習窓 CSV が v23_043（v22 選定走行）と数字一致（学習排除は数字を変えない）」を確認。

## §4.6 ハード制約 照合
- **H1** cap 0.12（同時 0.048・v24 は size を変えない・据え置き）。
- **H2** leak なし（建値+固定% は entry 時確定値・未来参照なし・上記5）。
- **H3/H13** net 判定・judge 固定（score.py に TREND_CAUGHT_TP 登録のみ＝計算式不変・既知答えテスト再pass）。
- **H5** 約定モデル（resting maker 指値＝maker・到達で約定・不約定は既存枝へ）。
- **H6** 価格非依存（L は %・USD 絶対値なし）。
- **H8** 期間分割（periods.py 正本・v24 は学習窓 fit しない＝分位選定なし・v22 選定も定数化）。
- **H15** ボラ逃げ（非該当＝方向スコアを触らない・Exit の利確水準のみ）。
- **H16** 1変更（数字を変えるのは resting maker 利確枝1つ・v22 定数化は数字不変の学習排除）・過去失敗の不再演（トレーリング#13＝両窓符号反転を採らない・学習窓選定#22/v14＝中立化を採らない＝全固定値）。

## 受け入れ判定（採点前ゲート）
- **自己検査**: ①OFF 恒等 md5（v24 OFF = v23_043 一致）②v22 定数化の数字一致（v24 ON+V24_FIXED_V22 の学習窓 CSV = v23_043 と一致＝学習排除は数字を変えない）③番人メタ確認（V24_TREND_TP_PCT を極端値にすると TREND_CAUGHT_TP が支配 or 恒等退行）④cap 実測 ⑤leak grep（.shift(-/center=True なし）⑥TREND_CAUGHT_TP score.py 登録＋既知答えテスト再pass。
- **件数/日を維持**（3.18/日・scalp 頻度を減らさない＝減れば不採用）＝v24 は Exit レバー（件数を入口が決める・件数増は入口レバーで扱う）。
- **両窓 score.py**: 採点窓 net > −$420（v23）∩ trend_caught 系（STOCH_REVERSE→TREND_CAUGHT_TP）の改善∩ **PARTIAL_TP/TP_FILLED 非毀損（⑨巻き込みゼロ）**∩ 非degenerate。precheck FAIL でも両窓CSV→report/analyze を出す（データ捨て禁止 9a4d348）。

## ARC マーカー
<!-- ARC order=39 iter="E37 v24 trend_caught ピーク帯 resting maker 利確" 前提="v23_043構成(base=v22_042)・nofloor概念なし" 採否="未" base_csv="trades_e37_range_scalp_v23_043" score_csv="" train_csv="" 狙い="反転待ち STOCH_REVERSE の遅行(速い5分レンジ)で取り逃す trend_caught −$1,270 を建値+0.08% の固定 resting maker 利確で回収・v22 学習も定数化し入口〜出口すべて固定値" 内容="trend_caught 玉に resting maker 利確枝 v24_trend_maker_tp(Xa1・TREND_CAUGHT_TP)を優先で追加・STOCH_REVERSE_EXIT 廃止・MFE_STALE/災害SL/TIME 維持・稼ぐ玉不変・v22学習窓選定を V24_FIXED_V22 で定数化・全固定値(学習ゼロ)" 方法="a-priori L=0.08%(手数料床SCALP_FLOOR∩MFE較正基準∩両窓crude∩学術Leung&Li:深SL→浅TP)で本走→両窓 score.py(学習窓選定なし)" -->

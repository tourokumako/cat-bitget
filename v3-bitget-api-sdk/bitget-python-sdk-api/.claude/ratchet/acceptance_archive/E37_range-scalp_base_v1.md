# acceptance — E37 レンジ・スキャル ショート ベース v1（MVP・新戦略）

TARGET: scripts/priority_rebuild/e37_range_scalp_short.py

> 設計書: e37_design.md（Peterson 形式・全12節）。本 acceptance は実装チェックの基準（acceptance_checklist.md A-F 準拠）。判定は score.py の数字のみ（CC は net 計算に触れない＝import のみ）。

## A. ヘッダ（hook 物理強制）
- **TARGET（上の素のラインが正・hook 検出用）**: scripts/priority_rebuild/e37_range_scalp_short.py（新規1ファイル）。
- **DESIGN_CONTRACT**（§5.2 と一致・実装と機械照合）:
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp_short.py",
  "self_check_calls": ["_entry_contract(", "_assemble_signals("],
  "must_combine": {
    "range_ok": ["er_ok", "in_box"],
    "short_entry": ["range_ok", "macd_ok", "ob_dev", "short_rev"]
  }
}
```

## B. 深掘り4点
- **① 真因（root cause）**: freq-iter2（広い入口×E36 長保有出口）の net 崩壊（$549→$79）の真因は**入口の広さでなく長保有出口**＝低品質玉が240分 time-exit まで走り 70件 −$2,921／平均負け $28.93 に肥大（report C/J/N7）。勝ち玉（EDGE_TP 52分・CENTER_LOCK 48分）は約50分で決着。
- **② 期待値分解**: freq-iter2 期待値/件 $0.17（勝率75.4% × avg勝ち$9.95 − 敗率 × avg負け$26.45）。E37 が動かすレバー＝**avg負けを縮める**（60分時間切れで逆行を早期に止める＝240分→60分で adverse excursion を圧縮）＋**件数を増やす**（広い dev_z 入口）＋浅TPで avg勝ちは小さくなる（z_exit 戻り）。狙い＝avg負けの大幅縮小で期待値/件をプラスに反転。
- **③ root か symptom か**: root（出口の保有時間そのもの＝最易パッチでない）。symptom 患い（atr_pct で帯を手切り等）でなく、出口構造（スキャル＝浅TP・短時間切れ）を設計する。
- **④ ベースアップ**: WebSearch 6本（arxiv 1411.5062 最適 MR＋コスト＋stop／arxiv 1707.03498 deadline＋コスト／quantinsti mean reversion building blocks・half-life＝保有時間／quantpedia grid primer＝刻みが細かいと手数料で消える・レンジでのみ機能／TradingView range scalping）＋ freq-iter2/scene-cap の report/analysis（analysis_block.md・improvement_plan.md）。記憶ベースでない。

## C. 変更の単位（H16・1ターン1変更）
- 変更は **新戦略 E37 のベース v1 を1本**（新しい器を1本＝E34/E35 と同じ扱い・複数レバーを混ぜない）。以後の改善（浅 add・複数TP刻み・dev_z 窓 ML・z 分位 ML）は1つずつ。
- **既定 OFF 恒等の起点なし**＝新戦略はゼロから（既存 base と恒等比較する対象がない）。代わりに自己検査＝① cap 実測（_verify_cap≤0.12）② leak grep（shift(-/center=True 0件）③ 発火件数の妥当性（--diagnostic）④ **会計保存**（lot 合計＝net・gross−手数料−slip−funding が score.py と一致）。
- **過去失敗の不再演**: freq-iter2（広い入口×長保有＝崩壊）を再演しない＝E37 は出口をスキャル化（60分・浅TP）で差別化。「切る系5回不採用」（DYING_CUT/STRUCT_SL/entry-gate/freq-iter3/hold-mom-exit）とは別物＝E37 は切る系でなく「入口を広げ小さく速く取る」新戦略。
- **★疑似シミュ由来の固定値ゼロ**（必須・require_acceptance 物理強制）:
  - (a) z_entry/z_exit/q_er は **probe で出した特定数値でなく学習窓の分位（quantile）由来 a-priori**。T_max=12本(60分)・k_hi=70・SMA20/std20・%K9 は a-priori 固定（スキャル＝短保有という設計仕様から・データ sweep でない）。
  - (b) **probe の数値（θ/段数/AUC 等）を設計の固定値に焼いていない**＝E37 のために probe は走らせていない（分析は freq-iter2 の実エンジン CSV のみ）。
  - (c) **採否は probe でなく実エンジン両窓 score.py の数字**で決める（学習窓純増→採点窓 base 比較）。
- **★ARC マーカー**（approve_impl が凍結保存・gen が改善アーク自動生成）:
```
<!-- ARC order=11 iter="E37 range-scalp base v1" 前提="新戦略・nofloor 概念なし・ゼロから" 採否="検証中" base_csv="" score_csv="" train_csv="" 狙い="E36(デイトレ)が取らないレンジ内の小波を、広い入口×スキャル出口(浅TP・60分時間切れ)で取り、freq-iter2 が長保有出口で崩した net を回避して E37 単独の地面を出す(E36+E37 合算 月600ドルへ)" 内容="新戦略 e37_range_scalp_short.py＝ER<分位∩in_box∩1h MACD<=0∩dev_z>=分位∩速い%K反転 で SHORT・出口=dev_z戻りで浅TP(maker)＋60分 time-exit(taker)＋箱ブレイクSL・MAX_ADDS=1" 方法="連続モード score.py で学習窓純増→両窓・freq-iter2(79ドル)比較・件数とgross/fee採算・割れたら no-edge と記録" -->
```

## D. ★審判（score.py / eval_engine）整合
- **新しい exit_reason を出すか？ → NO（新規追加しない）**。E37 の出口は既存 exit_reason に揃える＝TP（短期平均へ戻り浅利確・maker）は **TP_FILLED**（maker 群）／時間切れは **TIME_EXIT**（taker）／箱ブレイク SL は **BOX_BREAK_SL**（既に E36 で taker 登録済）。**新 exit_reason を作らない**＝score.py の MAKER/TAKER 登録・既知答えテスト再pass は不要（出戻り防止）。⚠️ 実装で既存名と1字でも違う名を使わない（未登録 exit_reason は §2.9 STOP）。
- entry/exit のコスト種別: entry/add/TP=指値 maker（close×(1∓0.0001)・TTL3）／時間切れ・箱ブレイク=成行 taker＋slip。eval_engine の maker/taker 分類（_record_lots: TP_FILLED/EDGE_TP/BE_EXIT/PARTIAL_TP=maker・他=taker）と一致。
- **judge（score.py / eval_engine）の計算式に触れない**（H13）＝import のみ・改造禁止。
- **命名規約**: 実験＝戦略本体は e37_range_scalp_short.py（pdca_mark 検知は e3N_ で実験扱い）／審判＝score.py CLI／分析＝report.py・analyze.py。read-only probe は本実装では使わない。
- **サイドカー出力**（新戦略必須）: 売買記録CSVの隣に <stem>_params.json を params_sidecar.write_sidecar で出す。sections に実使用の 指標/閾値(ER分位・dev_z分位・z_exit・k_hi)/TP(浅・平均戻り)/SL(箱ブレイク)/TimeExit(60分)/期間/サイズ ＋ Entry/Exit ロジックの流れ・exit_reason を入れる（report.py 節0 が自動表示）。
- **共通の書き出し処理を使う**: strat_base の _output_and_report を thin wrapper 経由で呼ぶ（命名タグ連番・archive・上書き防止を自動踏襲・個別に書かない）。
- **共通土台 strat_base を import**: ①load_5m ⑤_verify_cap・_funding_cost ⑥_output_and_report ⑦定数（UNIT/CAP/TTL/ENTRY_OFFSET/COST_FLOOR）。戦略固有（箱・入口信号・スキャル売買エンジン）だけ自前。⛔ e36_short_oscillation は import しない。

## E. §4.6 ハード制約 照合
- **H1** cap: 全建玉合計 ≤0.12（MAX_ADDS=1＝size 0.024 で自明）・_verify_cap 実測 assert ＋ score.assert_hard_constraints。
- **H2** leak: 1h は確定足のみ（attach_upper_tf 同型）・dev_z/ER/stoch/box は当該足まで・出口は約定 bar の次以降・grep assert（shift(-/center=True 0件）。
- **H5** 約定: entry/add/TP=指値maker・時間切れ/箱ブレイク=成行taker＋slip。
- **H6** 価格非依存: dev_z（無次元）・z 分位・ER（無次元）・距離%・W%。USD 絶対値の閾値/ラベルなし。
- **H8** 期間: 分位は学習<2025-03 で fit（periods import・手打ちなし）・採点 2025-06〜2026-02 は評価のみ・封印不参照。
- **H13** judge 固定: score.py/eval_engine は改造しない（新 exit_reason も作らない）。
- **H15** ボラ逃げ: ラベル=方向（短期平均へ戻り到達・二値）・dev_z は方向（買われすぎ）＝ボラ大きさ予測でない・ATR/std は SL/ゾーン/時間のみ・ショート単独。
- **H16** 1変更（新戦略1本）・過去失敗（freq-iter2 長保有）不再演。
- 非該当: H3/H4/H7/H9/H10/H11/H12/H14 は判定器・既定で担保（戦略側で新たに触らない）。

## F. 受け入れ判定（採点前ゲート・PDCA §8.4）
- **自己検査**（「わざと壊して落ちるか」のメタ確認込み §2.9③）: ① _verify_cap≤0.12 ② leak grep 0件 ③ DESIGN_CONTRACT 自己チェック（_entry_contract/_assemble_signals が成分欠落で自停止＝わざと成分を抜いて停止するか確認）④ 会計保存（lot 合計＝score.py net）。
- **学習窓で純増を先に測る**（採点窓 不参照）→ プラスかつ非degenerate なら採点。
- **公式判定は score.py**（CC は net 計算に触れない＝import のみ）・**両窓**（学習窓→採点窓）で freq-iter2(79ドル) を超えるか＋件数が高頻度（スキャルの宣言）＋ gross/fee で小TP が採算するか（report.py J）を確認するまで「効いた」と言わない。
- degenerate（near-inaction）でないか＝件数/日が E36 の数倍方向に増えているか（--diagnostic ＋ report F4）。
- 割れたら正直に「レンジ・スキャル ショートは no-edge（出口スキャル化でも freq-iter2 を救えない）」と ledger に記録（block_premature_giveup＝事前却下しない）。

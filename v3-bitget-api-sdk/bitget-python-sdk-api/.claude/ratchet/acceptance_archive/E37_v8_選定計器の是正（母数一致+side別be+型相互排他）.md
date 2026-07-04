# acceptance — E37 v8 選定計器の是正（フェーズ0・母数一致＋side別be＋型相互排他）2026-07-04

TARGET: scripts/priority_rebuild/e37_range_scalp.py

LEVER（improvement_plan から逐語）: 選定計器の是正＝①イベント5型を相互排他化②θ選定フロンティアを実行同一規則（単一スロット・TTL・pending占有）の執行後頻度で作る③be≥1.0判定とθを型×side別に分ける（--v8・既定OFF=v7恒等・新レバーなし＝物差しの是正・帯なしの型×sideは執行しない・全帯なしなら停止）

## 位置付け（改善フロー内）
- E36+E37 合算 月$600 への改善フローのフェーズ0（まこさん OK 2026-07-04）。フェーズ1（型×side の Entry/Exit セット共同選定）の前に、選定の物差しを直す。
- E37 の役割＝スキャル（件数が一級基準）。本是正は**件数/日を上げる**ための正しい物差し作り（現行計器は頻度を過大に見積もり赤字sideを覆い隠す＝件数と質の判定が両方歪む）。合格ラインに 件数/日を上げること（>0.41）を含める（下記F）。

## 深掘り4点
### ① 真因
θ・帯の選定計器が実行と別世界にある: (a) フロンティアの「イベント/日」は教師の独立疑似執行（全候補を同時執行可能とみなす）で、実行は サイドごと単一スロット＋pending占有＋TTL3＝学習窓1.82イベント/日が採点窓0.41件/日に消える構造 (b) be≥1.0 判定が LONG/SHORT プール＝LONG be1.5+SHORT be0.6 でもプール be≥1.0 なら両方執行（採点窓 B節: 買い65件−$3/売り45件−$53 の非対称を計器が見えない） (c) 5型が入れ子（深MR⊂浅MR 等）＝型別教師が重複し帯の合併で最も緩い帯が支配。
### ② 期待値分解
本是正は新レバーでなく計器是正＝期待値を直接動かす主張はしない。効くのは選定の質: 赤字 side の帯を執行しない（平均負け側の混入源を選定段階で遮断）・頻度見積りが実行実態と一致（フェーズ1の組選定が正しい件数/日で行える）。
### ③ root か symptom か
root。個々の負け玉（symptom）でなく、負け玉を選ばせている物差しそのものを直す。
### ④ ベースアップ（証跡・WebSearch/WebFetch 2026-07-04）
- **fill 前提の歪みは定量的に巨大**: 指値の 100%約定仮定は実利益を 850% 過大評価・約定は逆選択を伴う（買い fill は下落局面で 100%・有利局面では 1.8%）＝**fill・執行制約で条件付けない頻度/期待値の見積りは物差しとして壊れている**（arxiv 2407.16527 The Negative Drift of a Limit Order Fill・WebFetch 精読）。
- 約定確率はキュー位置と市場状態に強く依存＝執行を無視した戦略評価はコスト過小・リスク誤認を生む（arxiv 2403.02572 Fill Probabilities in a LOB・WebFetch 精読）。OHLC バー内の fill 曖昧性等、執行前提の簡略化が結果を作為する（ssrn 6240638 When Backtests Guess）。
- 閾値（θ）選定は out-of-sample で行い評価データの情報を使わない（nested CV の実務・arxiv 検索 2026-07-04）＝学習窓 OOF 選定の継続根拠。
- **crypto の LONG/SHORT は構造的に非対称**: 強制清算はロング 3.51%/日 vs ショート 1.89%/日・清算カスケードは下方向を増幅（arxiv 検索 2026-07-04・kaiko research）＝side 別判定の裏付け。cat-bitget 固有の実証＝手動 V9 は LONG/SHORT 別の値設定（§6）・E36 は SHORT 専用化で機能・E28 は反発 LONG 専用・採点窓 B節の side 非対称（上記①b）。

## やること（実装項目・--v8 新フラグ・既定 OFF＝v7 恒等）
1. **型の相互排他化** _gen_events_v8_exclusive: 同一バー・同一 side で複数型が立つ場合、特異度順（evt_pull・evt_brk・evt_bb・evt_mr・evt_mr_sh の順＝a-priori＝条件が多い型を優先）で1型に割当て。教師母数を互いに素にする。assert: 型マスクのペア重複0（自己検査）。
2. **執行後フロンティア** _frontier_exec_consistent: θ 候補ごとに、学習窓イベントへ実行同一規則（サイドごと単一スロット・pending占有・TTL3 タッチ約定・不約定は建てない＝run_continuous と同一）を適用した逐次パスで「執行後の件数/日・be」を算出し、フロンティア・θ選定・BE_FLOOR 判定をこの執行後系列で行う（教師ラベル生成自体は per-event のまま＝ラベルは業界標準・直すのは選定の物差し）。
3. **型×side 別の θ・be 判定** _select_theta_per_type_side: フロンティア・θ・be≥1.0 判定を型×side 別に分離（検出器 fit は型別のまま・side は特徴列として不変＝fit の side 分割はフェーズ1の共同選定で扱う）。帯なしの型×side は執行しない。全型×side 帯なしなら SystemExit 停止（採点温存・停止ガード継承）。
- 変えないもの: 検出器の教師定義（エンジン同一執行 Triple Barrier）・特徴（2603列＝RSI9・複数TF=MTF 整合を含む 5分足設定・technical_kb §4/§5）・執行（指値 maker・TTL3）・出口（TP=SMA∓0.5σ maker・手数料を超えるTP幅のみ武装＝SCALP_FLOOR maker往復超・TP-viability 同梱・SL=2×ATR maker・TIME 12本=60分 taker＝短保有・分単位）・サイズ 0.024・MAX_ADDS=1・OOF 測定系・periods 参照。

## ★疑似シミュ由来の固定値ゼロ
- (a) 新規の数値パラメータなし: 相互排他の優先順は a-priori（条件の特異度順）・執行後フロンティアは実行と同一規則の適用（新定数なし）・side 分割は判定の分割のみ（新しい数値なし）。BE_FLOOR=1.0（損益分岐の定義値）・θ 分位グリッドは既存のまま。
- (b) probe（出口検算 probe 含む）の数値を設計の固定値に焼いていない（probe は SL 幅変更案を採らない判断と時間切れ取り漏れの実在確認＝方向の当たり付けにのみ使用）。
- (c) 採否は実エンジン両窓 score.py の数字で決める。

## C. 変更の単位（H16）
- 1変更＝「選定計器の是正」1本（3項目は同一目的＝計器の正しさ・いずれも新レバーなし・E0.1 計器修正で複数項目を1本で直した前例）。既定 OFF で v7 恒等（trades CSV md5 一致を自己検査）。
- 過去に採用に至らなかった手の再演なし: 切る系でない（L-309 非該当）・混合母数へ戻さない（ARC20 の型別化は維持し side 判定を追加）・採点窓の値選定なし（L-267）・「学習窓だけ良い」型は執行後フロンティアでむしろ検出しやすくなる（L-308/L-320 対策側）。

## D. 審判整合
- 新 exit_reason なし（TP_FILLED/SL_FILLED/TIME_EXIT/FORCE_CLOSE_EOD 既存のみ）・コスト種別変更なし・score.py/eval_engine に触れない（H13）。
- 命名: 実験は --v8 --tag v8 で ratchet_io 連番（require_tag_for_experiment 準拠）・サイドカー params_sidecar は既存配線のまま（v8 設定を sections に反映）。
- 出力は共通書き出し _output_and_report（strat_base 経由・ratchet_io）を継続使用。

## E. §4.6 ハード制約 照合
- H1 cap: 不変（_verify_cap＋score.assert_hard_constraints 実測）/ H2 leak: 教師・fit・θ 全て学習窓・OOF・label_exclude_assert/shift grep 継続・執行後フロンティアも学習窓内のみ / H3 net: score.py のみ / H4 コスト: eval_engine 定数不変 / H5 約定モデル: 不変（指値 maker TTL3・TIME=taker+slip） / H6 価格非依存: 新規数値なし（%・σ・本数のみ） / H7 5m 標準のまま / H8 periods.py 参照不変 / H9 最小注文: size 0.024 不変 / H10 サイズ固定値扱いなし（配分レバーは後続フェーズ） / H11 判定: 両窓 score.py・比較地面=E37 v7_011 / H12 異常値 STOP: score anomaly 継続 / H13 judge 固定: 触れない / H14 発注フラグ: 非該当（バックテストのみ） / H15 ボラ逃げ: 方向スコア構造不変・使用型の重要度 top10 に ATR/vol 系 0 列を確認（v7 同様） / H16: 上記C。

## F. 受け入れ判定（実験前に固定・後出し変更しない）
- 自己検査: ① --v8 OFF 恒等＝trades CSV 3本 md5 一致（vs v7 恒等走行） ② 型マスク相互排他 assert（ペア重複0） ③ 停止ガードメタ確認（BE_FLOOR を故意に 99 にして全型×side None＝停止するか） ④ cap/leak grep/label_exclude_assert/DESIGN_CONTRACT ⑤ 執行後フロンティアの整合＝選定時の件数/日と本走の実件数/日の乖離をログ出力（計器の是正確認・±30%目安は観測値として記録）。
- 学習窓: 型×side 執行後フロンティアで be≥1.0 帯の有無。帯あり→precheck（学習窓 be≥1.0）→公式 両窓 score.py。
- **合格ライン**: 両窓で v7_011（110件 0.41件/日・月−$6.20）超え ＋ **件数/日を上げる（>0.41・scalp 役割＝一級基準）** ＋ 非 degenerate。届かなければ「採用に至らず（地面は ratchet で維持）＋次の作り込み案」と記録（基準の後出し変更・尻すぼみ容認をしない）。
- **分岐（事前固定）**: 全型×side 帯なし停止→型×side フロンティアを ledger に記録し、フェーズ1（型×side の Entry/Exit セット共同選定＝入口深さ・反転確認強化・トレンドゲート・クールダウン×出口 TP固定/移動・TP幅・TIME 本数の組を side 別メニューで学習窓共同選定）へ直行。是正済み計器の上で組を選ぶ。
- ⑨巻き込み検証: 該当なし（切る系・Exit 縮小レバーでない・執行の物差し是正。side 帯なしによる不執行が出た場合は L 限界分解で勝ち玉巻き込みを数字で報告する）。

## DESIGN_CONTRACT
```json
{
  "impl_file": "scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["--v8", "_gen_events_v8_exclusive", "_frontier_exec_consistent", "_select_theta_per_type_side", "label_exclude_assert"]
}
```

<!-- ARC order=22 iter="E37 v8 選定計器の是正（母数一致+side別be+型相互排他）" 前提="E37未採用・v7採点で稼ぎ玉0・実装総点検で選定計器の歪み3点を特定した上（フェーズ0）" 採否="採用に至らず（採点窓70件0.26件/日 月−$2.28＝件数合格ライン>0.41未達・計器是正3点は実証＝頻度乖離−1%・side非対称の帯実証[bb=S/brk=L/pull=Sのみ]・帯の絶対量0.89件/日が真因と確定・v8計器は以後の選定標準・次=フェーズ1型×sideセット共同選定）" base_csv="trades_e37_range_scalp_v7_011_score.csv" score_csv="trades_e37_range_scalp_v8_013_score.csv" train_csv="trades_e37_range_scalp_v8_013_train.csv" 狙い="選定計器の歪み（教師と実行の母数不一致・be判定のsideプール・5型の入れ子重複）を止め、θ・帯の選定を実行実態とside別の損益分岐で行う＝以後の全選定の物差しを直す（まこさんのLONG/SHORT非対称指摘と実装総点検を受けた土台是正・E36+E37合算$600フローのフェーズ0）" 内容="--v8=①5型を特異度順で相互排他化（教師母数を互いに素に）②θ選定フロンティアを実行同一規則（単一スロット・pending占有・TTL3）の執行後件数/日とbeで作る③be≥1.0判定とθを型×side別に分け帯なしの型×sideは執行しない（全帯なしなら停止）。検出器fit/特徴/執行/出口/サイズは不変・既定OFF=v7恒等" 方法="自己検査(OFF恒等md5・相互排他assert・停止ガードメタ確認・cap/leak/label_exclude・選定vs実走の件数乖離ログ)→学習窓の型×side執行後フロンティア→帯あればprecheck→両窓score.pyでv7_011比（件数/日>0.41・非degenerate・後出し変更なし）・帯なしなら停止を記録しフェーズ1（型×side Entry/Exitセット共同選定）へ" -->

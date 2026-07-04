# acceptance — E37 v9 型×side の Entry/Exit セット共同選定（フェーズ1）2026-07-04

TARGET: scripts/priority_rebuild/e37_range_scalp.py

LEVER（improvement_plan から逐語）: 型×sideごとに入口バリアント（現行／実体過半の反転確認／上位足整合／クールダウン＝a-priori入れ子）×出口テンプレ（TP移動0.5σ／entry時固定0.5σ／固定1.0σ × TIME 60分／30分＝a-priori少数）の組を、v8計器（執行後フロンティア・学習窓OOF・型×side別be≥1.0）で共同選定し帯が立った組だけ執行する（--v9・既定OFF=v8恒等・帯なしの型×sideは執行しない・全帯なしなら停止）

## 位置付け（改善フロー・フェーズ1＝まこさん GO 2026-07-04）
- フェーズ0（v8・ledger ARC22）で確定した真因＝**現行の入口×出口セットでは be≥1.0 帯が 0.89件/日分しか無い（帯の絶対量の不足）**に対し、入口と出口を「組」で動かして帯を作る（片側調整の禁止＝まこさん指示・L-300）。
- E37 の役割＝スキャル（**件数/日を上げる**が一級基準）。機構＝(a) 出口幅が広がれば1件 gross が上がり be≥1.0 に届く分位が下がる→帯が広がる (b) 入口確認の強化で SL 方向ミス玉（v8 でも 26件 −$334・N11 含み益≥含み損 0%）を減らし be を押し上げる→同じ分位でも帯化。両側から帯の絶対量を作る。
- 実装総点検の残欠陥のうち 5件（反転確認1本足・トレンドゲート不在・TP移動目標・RR逆・クールダウン無し）を本フェーズの候補メニューとして扱う（合意済みの割当）。

## 深掘り4点
### ① 真因
帯の絶対量の不足（v8 で計器の歪みを除いて確定した残高＝0.89件/日）。内訳は (i) 出口幅 0.5σ が低ボラ場面で手数料床を超えず候補ごと痩せる（TP-viability が正しく弾く） (ii) 入口の反転確認が単一足の陰陽のみで SL 方向ミス玉を通す（勝率を作れず be が届かない） (iii) LONG/SHORT・型ごとに最適な組が違うのに全型共通の1セット固定。
### ② 期待値分解
動かすのは (a) 1件 gross（出口幅・TP anchor）と (b) 勝率（入口確認・上位足整合・クールダウン）と (c) 件数（be≥1.0 に届く分位の拡大）。選定は組ごとの執行後 be と件数/日で行い、どのレバーが効いたかは選定ログ（型×side×組）と lever-bites（v9 OFF 恒等）で分離。
### ③ root か symptom か
root。個別の負け玉でなく「帯を作る自由度（入口×出口の組）」そのものを設計に入れる。v5〜v7 の入口単独・案Bの出口単独の両方の轍を避ける。
### ④ ベースアップ（証跡・WebSearch/WebFetch 2026-07-04）
- SL と最適 TP は逆相関＝entry/exit/stop は同時決定（arxiv 1411.5062 abs 精読・optimal double stopping）＝組で選ぶ理論根拠。
- OU 平均回帰の最適 entry/exit 水準は**建値側で確定される固定境界**として導かれる（arxiv 1602.05858 abs 精読）＝TP を fill 時に固定する anchor 案の根拠（現行の毎バー移動目標は総点検欠陥5）。
- メタラベリング実務: primary（入口）は高リコール・secondary はフィルタ・**上昇局面と下降局面で異なるモデルを並行運用可能**（hudsonthames.org meta-labeling toy example 精読）＝side 別の組選定の実務裏付け。
- 反転確認の実務: ハンマー等の教科書反転パターンは実体とヒゲの比を要求（arxiv 検索 2026-07-04・candlestick 系）＝単一足の陰陽だけは最弱の確認（総点検欠陥1）。
- 実行制約を選定に反映する必然（arxiv 2407.16527: 100% fill 仮定は利益850%過大・前回精読）＝v8 計器で選定を続ける根拠。
- cat-bitget 固有: E36 shortset1 の 1h MACD ゲート採用済み（上位足整合の部品）・E28 急落反発 LONG・v8_013 の実測（時間切れ+$78 黒字化＝TIME 本数を候補に・SL較正済み＝SL は動かさない・N10 atr_pct/stoch_k 両窓✓は特徴で木に既存）。

## やること（実装項目・--v9 新フラグ・既定 OFF＝v8 恒等）
1. **出口テンプレ** _exit_templates_v9（a-priori 4案・SL=2×ATR は全案共通＝probe で勝ち玉 MAE p80 と較正済みのため動かさない）:
   - X-a: 現行＝TP 毎バー SMA∓0.5σ・TIME 12本（現行組も候補に残す＝選定が現行を選べば正直にそう出る）
   - X-b: TP を fill 時に固定＝SMA∓0.5σ@fill・TIME 12本
   - X-c: TP fill 時固定＝SMA∓1.0σ@fill・TIME 12本（教科書の1σ）
   - X-d: TP fill 時固定＝SMA∓1.0σ@fill・TIME 6本＝30分（短保有側）
   - 全案で TP 武装は SCALP_FLOOR（**手数料を超えるTP幅**のみ・maker往復）と TP-viability を継続。
2. **入口バリアント** _entry_variants_v9（a-priori 入れ子4段＝多重検定を抑える）:
   - E-0: 現行（相互排他済み5型・v8 同一）
   - E-1: E-0 ∩ 実体過半の反転バー（|close−open| がバーレンジの過半＝0.5 は「過半」の定義値・単一足陰陽の強化＝総点検欠陥1）
   - E-2: E-1 ∩ 上位足整合（SHORT＝1h MACD≤0／LONG＝1h MACD>0・符号のみ＝E36 採用済み機構の流用・トレンドに轢かれる玉の門＝総点検欠陥3の入口版）
   - E-3: E-2 ∩ クールダウン（同 side の SL 決済から T_MAX 本＝既存定数は新規建て禁止＝総点検欠陥7）
3. **教師・fit**: 型×出口テンプレごとに教師を再生成（エンジン同一執行・出口が変われば「稼げたか」が変わる）し型別 fit（5型×4テンプレ＝20 fit・実行時間 v8 の約4倍＝1〜1.5時間見込み）。**入口バリアントは母数のサブセット＝fit は再利用し、執行後フロンティアだけをサブセットで引き直す**（計算量の抑制・選定は全て学習窓 OOF）。
4. **組の共同選定** _select_combo_per_type_side: 型×side ごとに（入口4×出口4×θ分位6）の執行後フロンティア（v8 計器 _frontier_exec_consistent・クールダウンは逐次パス内で適用）から **be≥1.0 を満たす組のうち執行後件数/日 最大**を選定。帯なしの型×side は執行しない・全型×side 帯なしなら SystemExit（停止ガード）。
5. **エンジン適用**: ポジションごとに自分の型×side の選定組（TP anchor/幅・TIME 本数・クールダウン）を適用（_record・サイドカーに組を記録＝lever-bites）。
6. 変えないもの: 検出器（型別 LightGBM・特徴2603列＝**RSI9・MTF** 上位足整合を含む **5分足**設定・technical_kb §4/§5）・執行（指値 maker・TTL3）・SL（2×ATR maker）・サイズ 0.024・MAX_ADDS=1・相互排他・OOF 測定系・停止ガード・periods 参照。

## ★疑似シミュ由来の固定値ゼロ
- (a) メニュー値は全て a-priori: 0.5σ/1.0σ＝教科書の半σ/1σ・実体過半の 0.5＝「過半」の定義値・TIME 6/12本＝既存定数とその半分・上位足整合＝MACD 符号のみ・クールダウン長＝T_MAX 既存定数。**どの組を使うかは学習窓 OOF の執行後フロンティアが選ぶ**（手で決めない）。
- (b) probe の数値（SL較正・時間切れ取り漏れ等）は方向の当たり付けにのみ使用し設計の固定値に焼いていない（SL を動かさない判断の根拠として引用のみ）。
- (c) 採否は実エンジン両窓 score.py の数字で決める。

## C. 変更の単位（H16）
- 1変更＝「型×side の組共同選定」機構1本（メニューの中身は §5 設計パラメータ＝本 acceptance で確定・実験中に足さない）。既定 OFF で v8 恒等（v9off の trades CSV md5 一致を自己検査・v8 OFF=v7 恒等の連鎖も維持）。
- 過去に採用に至らなかった手の再演なし: 入口単独調整（v5〜v7 の轍）でも出口単独でもない・切る系でない（L-309）・混合母数へ戻さない（ARC20）・独立カウントへ戻さない（ARC22）・採点窓の値選定なし（L-267）。

## D. 審判整合
- 新 exit_reason なし（TP_FILLED/SL_FILLED/TIME_EXIT/FORCE_CLOSE_EOD 既存のみ・TIME 6本も TIME_EXIT）・コスト種別変更なし・score.py/eval_engine に触れない（H13）。
- 命名: --v9 --tag v9 で ratchet_io 連番・サイドカー params_sidecar に v9 組選定ログ（型×side×選定組）を sections で出力・共通書き出し _output_and_report 継続。

## E. §4.6 ハード制約 照合
- H1 cap: 不変（0.024×両側 ≤0.048・_verify_cap＋score.assert_hard_constraints）/ H2 leak: 教師・fit・組選定すべて学習窓 OOF・TP anchor は fill 時点値のみ（t 因果）・上位足整合は closed-bar merge_asof（L-128 型）・grep assert 継続 / H3 net: score.py のみ / H4 コスト: eval_engine 定数不変 / H5 約定モデル: 不変（entry/TP/SL=指値 maker・TIME=taker+slip） / H6 価格非依存: σ 倍率・実体比・本数・符号のみ（USD 絶対値なし） / H7 **5分足**標準のまま / H8 periods.py 不変 / H9 最小注文: 不変 / H10 サイズ配分なし（フェーズ2以降の控え） / H11 判定: 両窓 score.py・比較地面＝v8_013（と v7_011） / H12 異常値 STOP 継続 / H13 judge 固定 / H14 非該当 / H15 ボラ逃げ: 方向スコアなし（両側 MR）・出口幅は σ スケール（サイジング/フィルタ用途でなく執行可否は検出器）・使用型 top10 に ATR/vol 非支配を確認 / H16: 上記C。
- E37 特有（enforce_e37_pdca）: ⑦ **手数料を超えるTP幅（maker往復）**＝SCALP_FLOOR 武装＋TP-viability を全テンプレで継続 ⑨ **短保有（分単位）**＝TIME 30/60分・保有中央 20-30分想定（4h 再演なし） ⑫ **5分足設定・RSI9・MTF**＝検出器特徴に RSI9/複数TF 整合・上位足整合は 1h MACD 符号。

## F. 受け入れ判定（実験前に固定・後出し変更しない）
- 自己検査: ① --v9 OFF 恒等＝trades CSV 3本 md5 一致（vs v8_013 走行） ② 停止ガードメタ確認（BE_FLOOR=99 破壊で全組 None→SystemExit） ③ 相互排他 assert 継承 ④ cap/leak grep/label_exclude/DESIGN_CONTRACT ⑤ 計器整合ログ＝選定時の執行後見積り vs 本走 学習窓 実件数/日（観測値記録） ⑥ 選定ログに型×side×組（入口/出口/θ/be/件数日）を全出力。
- 学習窓: 型×side×組の執行後フロンティアで be≥1.0 帯の有無 → 帯あり→precheck（学習窓 be≥1.0）→ 公式 両窓 score.py。
- **合格ライン**: 両窓で v8_013（70件 0.26件/日・月−$2.28）超え ＋ **件数/日を上げる（>0.41＝v7 比でも上・scalp 役割＝一級基準）** ＋ 非 degenerate。届かなければ「採用に至らず（地面は ratchet で維持）＋次の作り込み案」と記録。
- **分岐（事前固定）**: 全型×side 帯なし停止→組別フロンティアを ledger に記録し、フェーズ2（型の追加＝セッション境界リバーサル等の非逆張り軸を同じ枠組みへ）に進む。
- ⑨巻き込み検証: 該当なし（執行を増やす側のレバー・出口テンプレの選定は学習窓。採点後の L 限界分解で勝ち玉の増減を数字で報告する）。

## DESIGN_CONTRACT
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["--v9", "_exit_templates_v9", "_entry_variants_v9", "_select_combo_per_type_side", "_frontier_exec_consistent", "label_exclude_assert"]
}
```

<!-- ARC order=23 iter="E37 v9 型×side Entry/Exitセット共同選定（フェーズ1）" 前提="E37未採用・v8（計器是正）で帯の絶対量0.89件/日が真因と確定した上・改善フローのフェーズ1（まこさんGO 2026-07-04）" 採否="採用に至らず（採点窓367件1.35件/日 月−$59.40＝net大幅未達・件数レバーとしては初機能[合格ライン0.41超え]・固定TP6/8組＝セット選定は出口を動かした・主戦線=学習窓beが低ボラドリフトで採点窓に持続しない[L-320]・次=選定基準にregime頑健性）" base_csv="trades_e37_range_scalp_v8_013_score.csv" score_csv="trades_e37_range_scalp_v9_015_score.csv" train_csv="trades_e37_range_scalp_v9_015_train.csv" 狙い="帯の絶対量の不足（v8で確定した真因）に対し、入口と出口を片側ずつでなく組で動かして帯を作る＝出口幅で1件grossを・入口確認で勝率を押し上げ be≥1.0 に届く分位を広げ件数/日を上げる（まこさん指示のEntry/Exitセット設計・side別・総点検残欠陥5件をメニュー化）" 内容="--v9=型×sideごとに入口バリアント（現行/実体過半反転/上位足整合/クールダウン=a-priori入れ子4段）×出口テンプレ（TP移動0.5σ/fill固定0.5σ/固定1.0σ×TIME60分/30分=a-priori4案・SL2×ATR共通）の組を、型×出口テンプレごとに教師再生成+型別fit（20fit）し v8計器（執行後フロンティア・学習窓OOF）で be≥1.0 内執行後件数/日最大の組を選定・エンジンは型×sideの選定組を適用（既定OFF=v8恒等・停止ガード維持）" 方法="自己検査(OFF恒等md5・停止ガードメタ確認・相互排他・cap/leak/label_exclude・計器整合ログ・組選定ログ全出力)→学習窓の型×side×組フロンティア→帯あればprecheck→両窓score.pyでv8_013比（件数/日>0.41・非degenerate・後出し変更なし）・全帯なしなら停止を記録しフェーズ2（型追加）へ" -->

# acceptance.md — E37 v13: TIME_EXIT の maker化（deadline shrink・出口で締めて黒字化・Step2）（2026-07-06）

TARGET: scripts/priority_rebuild/e37_range_scalp.py
（審判 score.py の変更なし＝新 exit_reason を作らず既存の maker/taker 理由を再利用。詳細は D 審判整合。）

## LEVER（improvement_plan から逐語引き継ぎ・enforce_pdca_chain 接続②）
TIME_EXIT の maker化（deadline 接近で TP を残り時間比で建値側へ縮め maker 指値で取り切る・E35 iter8-9 型・taker→maker）
- 本手＝この LEVER を1変更で実装＝v12 の出口に「deadline 型 縮む maker TP」を足し、TIME 域に残った玉を成行 taker でなく maker 指値で取り切る新モード（既定 OFF=v12 恒等）。

DESIGN_CONTRACT:
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["range_ok_v11", "short_only_v11", "v13_time_maker"]
}
```

## ★戦略照合（enforce_strategy_anchor）
- STRATEGY_ANCHOR: e37=range,short_only,scalp（cat_requirements §1.2.1 逐語再掲）
- 局面：range ＝ range_ok_v11（1h S/R ゾーン∩5分ブレイク離脱・v17 視認校正済み）で入口を制約。GATE_IDENT=range_ok_v11（v12 不変・DESIGN_CONTRACT self_check_calls 登録済）。本手は出口のみ＝担当局面を変えない。
- 方向：short_only ＝ 上限ゾーンの反落 SHORT のみ・LONG 入口の生成経路なし。SIDE_IDENT=short_only_v11（v12 不変・DESIGN_CONTRACT self_check_calls 登録済）。
- 頻度：scalp ＝ 件数が役割。件数/日は Step1（v12）で達成済み（決済 3.46/日）。本 Step2 は出口の約定方式を変えるだけ＝件数/日 3.46 を維持（減らさない）しつつ net を上げる（薄利多売の net 締め）。
- ledger 直近 ARC 係留（鉤括弧で逐語引用）: 「E37 v12 レンジ上部で確認なし SHORT（件数を出す）」。本手はその続き＝v12 で件数の母数（PARTIAL_TP +$1566）を出した上で、残る唯一の taker 出口 TIME_EXIT を maker 化して net を締める（$600 ロードマップ Step1→Step2）。

## スキャル要件（enforce_e37_pdca ⑦⑨⑫）
- ⑦ 手数料を超える TP幅（maker往復）：縮む maker TP は建値フロア（損ゼロ）で下限を守る＝maker 往復 0.028% を割る決済を建てない（手数料の壁を超える幅でのみ maker 決済・§1.2.1「net がプラスになる幅以上」）。TIME の taker手数料負け（lot 393玉 gross +$486 を fee $518 で失う）を maker で回収するのが本手の目的。
- ⑨ 短保有（分単位・数分）：TIME backstop は 60分で不変（分単位）。deadline shrink はむしろ deadline 前に maker 決済させる＝保有をむしろ短くする（保有4h をスキャルと称した再演でない・§1.2.1「長く持たず」を強める）。
- ⑫ 5分足設定 RSI9/MTF：入口は v12 不変＝執行足5分・RSI9（rsi9・technical_kb §4）・MTF＝1h ゾーン range_ok_v11（technical_kb §5）。本手は出口のみ＝入口の RSI9・MTF ゾーンは触らない。
- 決済方法（exchange_spec ★決済方法・§6.1/§6.1.1 読了）：同サイド merge・平均建値／部分決済 scale out（複数TP最大20）／予算0.12は全建玉合計。本手は出口の約定方式のみ＝add/cap は v12 不変（同時最大0.048 BTC＜0.12・H1）。maker 指値決済＝post_only（成行 backstop のみ taker）。

## B 深掘り4点
① 真因：TIME_EXIT は lot 単位 393玉で gross +$486 と順行しているのに、成行 taker 手数料 $518 で net −$31（実質トントンを手数料が沈める）＝執行コスト負け（原因3分類の②執行・J 節）。SL −$1829 の方向ミス（N11・①戦略欠陥）は入口で「方向は当てられない」と両窓確定済み＝Step1 で決着・本手では触らない。
② 期待値分解：TIME を maker 化すると、手数料だけの下限（exit_price 不変）で net が −$31 から +$249 へ改善（節約 +$280・probe 実測）。R:R の必要勝率不足（N7・平均勝ち$6.25<平均負け$6.32・不足6.1pt）はコイン投げ勝率の下でコストを削って埋める＝TIME の taker手数料 −$406 を maker で回収する分が期待値/件を押し上げる。件数は変えず（母数 3.46/日 維持）net を上げる。
③ root か symptom：root（残る唯一の taker 出口＝執行コストの構造を直す）。symptom パッチでない＝N9 出口効率 中央値1.07 正常＝取り逃しでなく執行コストが問題。SL幅の手調整や入口いじりに逃げない（入口は Step1 決着）。
④ ベースアップ（今セッションで Read した KB／probe／WebSearch・WebFetch の証跡）：
   - range_scalping_kb §4（time-stop はスキャル分単位・TP は手数料を超える幅）／§6（高コストがスキャル最大の敵＝maker 前提）／§7 対応表（長く持たず・net がプラスになる幅以上）。
   - trade_analysis_methods_kb §0（前後比較）・§2（fat-tail は件数削り/勝率上げで大勝ちを切ると逆効果＝巻き込み注意）・§7（原因3分類＝②執行）。
   - probe（e37_timeexit_maker_deep_analysis.py・v12 score CSV・lot 単位）：TIME 393玉 gross +$486／fee $518／net −$31・fee のみ maker化 下限 net +$249（節約 +$280）・順行 TIME 玉 251件（+$651）・fat-tail TIME winners 172玉 +$426（巻き込み対象）。
   - WebSearch/WebFetch（今セッション・3クエリ3種別＝学術／実装／有名クオンツ・WebFetch 2本）：
     ①arxiv 1604.04963 Cartea-Jaimungal（学術）＝最適執行は limit(maker・スプレッド取得)＋market(taker・スケジュール維持)の混合で、forward/backward 境界が「いつ市場注文に切り替えるか」を決める＝deadline が近づくほど market へ寄る（＝縮む maker TP＋最終 deadline の成行 backstop の理論根拠）。
     ②freqtrade issue #12175（実装）＝maker 指値 exit を置き、timeout（例60秒）で未約定なら成行に強制切替＝maker 主・taker は最終フォールバックの実装パターン（本手の backstop 設計と一致）。
     ③QuantPedia／Alpha Architect（有名クオンツ）＝固定の時間切れ出口より、保有・出口の最適化が risk 調整後リターンを上げる／maker 規律で手数料を下げる（time-sensitive でない出口は maker）＝本手の方向を支持。

## ★疑似シミュ由来の固定値ゼロ
- probe（e37_timeexit_maker_deep_analysis.py）の数値（+$280 節約・+$426 巻き込み）は量の把握＝あたり付け専用。設計の閾値・幅・時間には焼かない。
- (a) 縮め方は a-priori な時間機構＝残り時間比 r（fill 時 r=1＝通常 TP・deadline で建値）＝arxiv 1707.03498／1604.04963 由来の構造（probe で選んだ数値でない）。
- (b) 建値フロア＝手数料床 COST_FLOOR（既存定数・損ゼロ maker）＝probe 数値でない。deadline T_MAX=60分は v12 の既存定数（動かさない・スイープしない L-267）。
- (c) 採否は probe でなく実エンジン両窓 score.py の数字で決める（学習窓で純増→採点窓で地面 v8_013 −$18 超え）。

## C 変更の単位（H16・1ターン1変更）
- 1レバー：v12 の出口に「deadline 型 縮む maker TP」を足す（新モード v13_time_maker・新フラグ --v13-time-maker・既定OFF=v12 恒等）。入口／ゾーン／SL／add／cap は v12 不変。
- 既定 OFF で恒等：--v13-time-maker を付けない時は v12 と完全一致（md5 一致で確認）。
- 過去失敗の不再演：切る/早切り系（L-309・玉を捨てる）と別物＝時間切れ玉を捨てず maker で取り切る（玉数を減らさない）。判別器で「死ぬ玉を選ぶ」路線でもない（全玉一律の時間機構＝E35 iter8-9 型）。

## D 審判整合（新 exit_reason・コスト種別・出戻り防止）
- 新 exit_reason を作らない＝score.py 改造なし（H13・出戻り回避）：縮む maker TP に当たった決済は既存の maker 理由 TP_FILLED（時間減衰した TP 目標への maker 約定＝意味的に TP）で記録。絶対 deadline（60分）で maker が当たらず成行で閉じる玉は既存 TIME_EXIT（taker・backstop）のまま。→ MAKER_EXIT_REASONS/TAKER_EXIT_REASONS の登録変更なし＝既知答えテスト再pass は不要（judge 不変・H13）。
- コスト種別：TP_FILLED＝maker（0.014%・slip 0）／TIME_EXIT backstop＝taker（0.042%＋slip 0.005%）＝eval_engine の既存分類と一致（H5）。
- 分析での識別：TIME から TP_FILLED へ玉が移るのは report C／analyze で件数シフトとして見える（hold_min が 60分近傍の TP_FILLED＝deadline shrink 由来）。新理由を作らず既存 report/analyze で追える。
- 命名/出力：--v13-time-maker（既定 OFF）・出力は共通の書き出し処理 _output_and_report（ratchet_io・タグ連番 --tag v13）＝命名/archive/上書き防止を自動踏襲。サイドカー params.json に v13 の出口ロジック（縮む maker TP・r・建値フロア・TIME backstop）を記録。
- 共通土台：strat_base（load_5m・_verify_cap・_funding_cost・_output_and_report・定数）を import（既存・変更なし）。

## E §4.6 ハード制約 照合
- H1 cap 合計 0.12：add/size は v12 不変（同時最大0.048 BTC）＝_verify_cap／score.assert_hard_constraints で実測。増加なし。
- H2 leak なし：deadline shrink は保有中の経過本数 r と当該バーの high/low のみ参照＝未来参照なし。新規の未来参照（shift 負方向・center 集計）を足さない（grep assert）。学習 fit なし（素ルール）。
- H5 約定モデル：入口 指値maker・TTL3／TP=指値maker（縮む TP も指値maker）／TIME backstop=成行taker+slip＝既存分類と一致。
- H6 価格非依存：r（比率）・建値フロア（%）・レンジ中央（価格帯由来）＝USD 絶対値の閾値を作らない。
- H8 期間分割：periods.py 正本（学習<2025-03／採点2025-06〜2026-02／封印不参照）＝import で取得（自前リテラルなし）。
- H13 judge 固定：score.py/eval_engine を触らない（新 exit_reason なし・上記 D）。
- H15 ボラ逃げ：出口レバー＝方向スコアに触れない（入口 v12 不変）＝非該当。
- H16 1変更・不再演：変更は1レバー（TIME の maker化）のみ。切る系（L-309）と別物（玉を捨てない）。

## F 受け入れ判定（採点前ゲート・PDCA §8.4）
- 自己検査（メタ確認込み）：① 既定 OFF で v12 恒等（--v13-time-maker OFF の売買記録が v12_022 と md5 一致）② cap 0.048 厳守 ③ leak grep（新規 shift 負方向/center 集計 0件）④ 番人メタ確認＝わざと r を壊して（r<0 等）建値フロアが損決済を弾くか ⑤ DESIGN_CONTRACT 3識別子（range_ok_v11／short_only_v11／v13_time_maker）が実装に実在。
- 学習窓で純増を先に測る（採点窓 不参照・H8）→ 学習窓 net が v12 学習窓を上回り degenerate でないなら採点。
- 公式判定は score.py 両窓（CC は net 計算に触れない）：採点窓 net が地面 v8_013（−$18）を上回ること。上回らなければ採用に至らずと記録（地面は ratchet 維持）。
- 件数/日の一級基準（scalp 役割）：決済 件数/日 3.46 を維持し下回らないこと（下回ったら degenerate＝採用に至らず）。出口を maker 化しても同じ玉が出る＝件数/日は減らさない設計。
- ⑨ 巻き込み検証（fat-tail を刈らないか）：I 節 MFE 帯で、maker化後に MFE 5〜15／15〜30 の勝ち玉 net（前 +$644／+$114）が減っていないこと＝172 の順行 TIME 玉（+$426）を建値側 shrink で刈って net を落としていないかを両窓で確認。刈って net が地面割れなら採用に至らずと記録。

<!-- ARC order=28 iter="E37 v13 TIME_EXIT の maker化（deadline shrink）" 前提="base v8_013・v12 の続き・Step2 出口" 採否="未（実装前）" base_csv="v8_013" score_csv="" train_csv="" 狙い="残る唯一の taker 出口 TIME_EXIT を deadline shrink で maker 化し、gross プラスを手数料で失う執行負け(lot 393玉 net−31/fee518)を回収して net を締める(方向は当てない・薄利多売のExit)" 内容="v12 出口に deadline 型 縮む maker TP(残り時間比 r・建値フロア)を足し、TIME 域の玉を成行taker でなく maker指値(TP_FILLED)で取り切る。当たらない玉のみ 60分成行 TIME_EXIT backstop。入口/ゾーン/SL/add/cap は v12 不変・新 exit_reason なし(score.py 不変)" 方法="既定OFF恒等md5→学習窓純増→両窓 score.py(採点窓 net>v8_013 −$18・件数/日 3.46 維持・⑨巻き込みで fat-tail 勝ち玉を刈っていない)。probe値は焼かず a-priori(r・建値フロア)＋両窓で採否" -->

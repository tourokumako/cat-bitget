# acceptance.md — E37 v11 視認校正レンジ計器の組み込み（1hゾーン×複数TP+add）（2026-07-05）

TARGET: scripts/priority_rebuild/e37_range_scalp.py

## LEVER（improvement_plan から逐語引き継ぎ・enforce_pdca_chain 接続②）
E37 入口の局面ゲート range_ok を v17 計器（1h タッチ実績S/Rゾーン ∩ 5分ゾーンブレイク離脱）に差し替え、出口を複数TP2段+add(MAX_ADDS=2)のセットで件数を仕組み化する

## ★戦略照合（STRATEGY_ANCHOR: e37=range,short_only,scalp）
- 台帳マーカー逐語再掲: **e37=range,short_only,scalp**（adopted_strategies.md STRATEGY_ANCHOR・cat_requirements §1.2.1 の機械可読形）。
- 局面（range）: GATE_IDENT=range_ok_v11（局面ゲート識別子＝1h タッチ実績 S/R ゾーンが close の上下に揃いその間 ∩ 5分足ゾーンブレイクなし、の物理 AND。入口候補は range_ok_v11 が False なら生成されない・レンジ判定は明示のルール列＝ML に任せない）。
- 方向（short_only）: SIDE_IDENT=short_only_v11（方向機構識別子＝LONG 入口の生成経路なし・全玉 SHORT を assert・v10 の short_only_v10 と同型）。
- 頻度（scalp）: 件数/日を上げることが役割＝下の F に件数/日基準を必須で明記（低頻度で net を作る形＝尻すぼみは受け入れ不可）。
- 経緯の係留（ledger 直近 ARC エントリ iter 名の逐語引用）: 直近 ARC order=24 iter="**E37 v10 ゾーン方式レンジスキャル SHORT（§1.2.1 準拠 MVP）**"（採否=採用に至らず・precheck FAIL 学習窓 be−0.63・§1.2.1 準拠の土台は初めて立った＝必要勝率 63.2% から 45.9% への逆R:R是正実証）。本 v11 はこの土台の上でレンジ判定だけを視認校正済み計器に差し替え＋出口を KB §6.5 の複数TP+add に拡張する続き。
- 知識の係留: range_scalping_kb.md 読了済み（§2 ゾーン/§3 入口/§4 出口/§6.5 add+部分決済/§7 対応表）。

## B. 深掘り4点
- **① 真因**: range_ok_v10（自前24hゾーン・束ね0.10%・接触バー込みタッチ≥3）にトレンド排除が無く、トレンド中でも直近の小帯がゾーンとして立つ → トレンド中の上限ショートが過熱継続に轢かれる（採点窓 N11＝SL 142件の含み益≥含み損 11%＝方向ミス89%・ADX40+ 混入 38.5%・range_ok 通過率 53.1%）。
- **② 期待値分解**: 必要勝率 45.9% vs 実際 39.7%＝不足 6.2pt（N7）。動かすのは主に勝率（局面ゲートの質。probe のあたり付けでは採点窓の v17 帯生存玉の勝率 46.7%＝+7.0pt）と件数（複数TP+add で1入口を最大4決済行に展開＝0.97件/日を押し上げ）。平均勝ち/負けの幾何（TP幅≥SL幅）は v10 の是正を維持。
- **③ root か symptom か**: root。stoch_k 高で負ける症状（N10 相関−0.170）の根＝局面判定のトレンド混入を構造で差し替える。stoch_k の閾値いじり（symptom・L-267 の型）はしない。
- **④ ベースアップ**: range_scalping_kb §2（レンジ＝タッチ実績ゾーン・上位足で構築→5分執行）/§3（到達＋拒否確認）/§6.5（add＋部分決済＝V9型・件数を仕組みから作る）＋ WebSearch/WebFetch 2026-07-05:
  - 学術: SSRN Osler「Support for Resistance: Technical Analysis and Intraday Exchange Rates」＝S/R レベルはイントラデイのトレンド中断（跳ね返り）を有意に予測する実証＝タッチ実績ゾーン方式の裏付け／arxiv 2606.29591（反発の向きは予測難・幅は予測可＝確認バー＋ゾーン幾何で向きの負担を減らす設計方針と整合）。
  - クオンツ実戦: QuantPedia grid primer＝グリッドは上下動が頻繁なレンジで最も利益・トレンドで赤字化（＝レンジ判定との併用が前提・v11 の設計と同型）。
  - 実務ブログ: luxalgo Scaling In/Out＝部分決済は2〜3分割が標準・手数料増がデメリット→各段に手数料の壁を超える武装条件／luxalgo Pyramiding＝トレンド型ピラミッディングはレンジ不適・追加は同量以下・負けに足すな→**v11 の add はトレンド型ピラミッドでなく「上限ゾーン再テストでの拒否確認の再発火を同一ポジに統合」＝Bitget の同サイド merge 仕様（exchange_spec ★決済方法 (1)）の写像であり、追加は同量 UNIT・追加時も TP/SL 幾何チェックを課す**／babypips Pyramiding。

## 設計詳細（§5 パラメータ・全て a-priori/既存定数/視認校正由来＝スイープしない）

### 入口（レンジ局面 ∩ 到達 ∩ 拒否確認・SHORT のみ）
1. **レンジ局面 range_ok_v11**＝v17 計器と同一ロジックを e37 内に移植（_zones_v11_1h）:
   - 1時間足（5m を label=right/closed=right で resample）・fractal j+2 確定スイング（structure_features・leak-safe）を過去 **168h（7日）** 窓で価格帯 **0.3%** に束ね、**スイング数≥2** のゾーンを機能実績とみなす。close の上（レジスタンス）と下（サポート）の両方にゾーンが揃い、間の幅 **≥0.4%** の時レンジ局面（close に近いゾーン優先）。
   - **5分足の即離脱**: close が上限ゾーン上抜け or 下限ゾーン下抜け（ブレイク）で range_ok_v11 オフ＝**新規候補を生成しない**（1h の遅れを執行足で補う・E32b に道を譲る）。
   - 数値の出所: 前セッションの**視認校正**（まこさん「概ね良い」・build_range_gate_dashboard.py v17 の ZONE_LOOKBACK/TOL/TOUCH/MIN_W をそのまま）＝採点数字で選定していない（L-267 非該当）。
2. **到達＋拒否確認**（v10 の実証部品を維持）: high ≥ 上限ゾーン下端（到達）∩ 陰転バー ∩ RSI9>70 からの下向き反転（5分足スキャル設定・technical_kb §4）。
3. **発注**: 指値 close×(1+0.0001)・TTL 3本（15分）・不約定は建てない（maker 限定・H5）。

### 出口（レンジ幾何・複数TP 2段＋ゾーン外SL・新 exit_reason なし）
- **手数料の壁の見積もり（スキャルの本質・⑦）**: 往復コスト＝**手数料 maker往復 0.028%**（0.014%×2・eval_engine 確定値・TP/SL は指値 maker で滑りゼロ）。TP の最低幅＝**SCALP_FLOOR 0.08%＝手数料（maker 往復 0.028%）の約2.9倍**＝1段あたり net が正になる幅を建てる前に判定（幅が足りない候補・段は置かない）。レンジ最低幅 0.4%（ゾーン間）＞ 2×SCALP_FLOOR＝TP1/TP2 の2段とも手数料を超える幅が幾何的に確保できるレンジだけを対象にする。
- **TP1（PARTIAL_TP・maker 指値・score.py 登録済み）**: (建値＋レンジ中央)/2＝上限から中央への中間で **lot の半分（0.012 BTC）** を決済。武装条件＝TP1 幅 ≥ SCALP_FLOOR。
- **TP2（TP_FILLED・maker 指値）**: レンジ中央（(上限ゾーン下端＋下限ゾーン上端)/2・v10 と同じ）で残り半分を決済。
- **SL（SL_FILLED・maker 指値・gap 反映・SL 優先）**: 上限ゾーン上端×(1+0.05%)＝ゾーンのすぐ外（V10_SL_BUF 維持・lot 全量）。
- **R:R 物理条件 tp_ge_sl_check_v11**: TP2 幅 ≥ SL 幅 ∩ TP1 幅 ≥ SCALP_FLOOR を満たさない候補は建てない（逆 R:R 禁止＝v10 の実証を維持）。
- **時間切れ（TIME_EXIT・成行 taker）**: lot の初回 entry から 12本＝60分 backstop（短保有・分単位・v10 実績 保有中央値22分を崩さない）。
- 最小注文チェック: 部分決済 0.012 BTC ≥ 0.0001 BTC・名目 ≥$5（H9・score.assert_min_order が実測）。

### add（同一ポジへの積み増し・V11_MAX_ADDS=2）
- スロット占有中（SHORT 保有）に**入口条件の完全再発火**（range_ok_v11 ∩ 上限到達 ∩ 拒否確認）で追加 lot（UNIT 0.024・同量）を指値 TTL 発注。**最大 2 lot＝合計 0.048 BTC**（H1: 0.048 ≤ 0.12・E32b との共有枠に配慮した a-priori・V9 MAX_ADDS=5 の前例の縮小版）。
- 追加 lot にも TP1/TP2/SL の同じ幾何チェック（tp_ge_sl_check_v11）を課す＝条件を満たさない再発火は積まない。SL は全 lot 共通のゾーン構造基準（リスクは「ゾーン破れ」1点に集約）。
- 位置づけ: トレンド型ピラミッディング（高値更新で追加・レンジ不適）ではなく、**レンジの上限ゾーン再テストで小刻みに売り増して複数TP で刻む**＝§1.2.1「小刻みに大量」と KB §6.5（V9 型 add＋部分決済）の実装形。Bitget 実仕様では同サイド merge＝平均建値1ポジ＋複数TP（最大20個・exchange_spec ★決済方法 (2)）に写像可能。

### フラグ・恒等
- **--v11 で ON・既定 OFF＝v10 恒等**（v10/v9/…全経路不変・md5 一致で確認）。
- 対照フラグ（diagnostic 専用・寄与分離）: **--v11-no-add**（MAX_ADDS=1）・**--v11-single-tp**（TP2 のみ＝v10 出口）。

## C. 変更の単位（H16）
- 変更は **1レバー＝v11 セット（入口局面ゲートの差し替え＋それに整合する出口一式）**。Entry/Exit は一式で作る（CLAUDE.md アジャイル節・L-285「入口だけ分割しない」）。寄与は対照フラグで分解（採否は一式で判定）。
- 既定 OFF で恒等: --v11 なし実行が v10_017 と CSV バイト一致（md5）を自己検査で確認。
- 過去失敗の不再演: 検出器・θ・学習窓分位選定なし（L-320 の構造に乗らない）／切る系でない（L-309 非該当）／固定値スイープなし（L-267・全値 a-priori/視認校正/既存定数）／手動レンジ日ラベル不使用。
- **★疑似シミュ由来の固定値ゼロ**: (a) ゾーン4値（168h/0.3%/タッチ2/幅0.4%）＝視認校正由来の a-priori・TP1/TP2/SL＝レンジ幾何・V11_MAX_ADDS=2＝cap 幾何と V9 前例・SCALP_FLOOR/TTL/T_MAX/UNIT＝既存定数 (b) probe（v17_gate_overlap_probe）の数値（生存率36/47%等）は**どの固定値にも焼いていない**（トレンド排除の向きのあたり付けのみ） (c) 採否は実エンジン両窓 score.py の数字で決める。

## D. 審判整合
- **新 exit_reason なし**: TP1=PARTIAL_TP（score.py MAKER_EXIT_REASONS 登録済み・2026-06-18 iter6）・TP2=TP_FILLED・SL=SL_FILLED・TIME=TIME_EXIT＝全て既存登録。judge（score.py/eval_engine）に触れない（H13・既知答えテスト不要）。
- コスト種別: entry=maker（指値 TTL）／TP1・TP2・SL=maker（resting 指値）／TIME=taker+slip＝eval_engine/score の分類と一致（H5）。
- 出力: 共通の書き出し処理（strat_base 経由 _output_and_report・ratchet_io）＋ **--tag v11 で連番**（採用前・base 語なし）＋ params_sidecar（実使用値・Entry/Exit ロジック・v11 節を追加）。
- 命名: 実験検知は e[0-9][0-9]_ 一般化済みで pdca_mark に乗る。

## E. §4.6 ハード制約照合（1項目ずつ）
- **H1** cap: 同時最大 2 lot×0.024＝**0.048 BTC ≤ 0.12**・_verify_cap 実測 assert＋score.assert_hard_constraints（時系列）。
- **H2** leak: ゾーン＝fractal j+2 確定（過去のみ）・1h→5m は ffill（過去方向）・resample label=right/closed=right（バー確定時刻）・拒否確認＝当該足確定値・発注/約定/出口判定は次 bar 以降。leak grep（.shift(-/center=True）assert・該当行を書く場合は H2OK 因果性宣言（require_leak_annotation）。
- **H3/H4** net 判定・コスト確定値: score.py/eval_engine（不変）。
- **H5** 約定モデル: entry 指値 maker TTL3・TTL 内不約定は建てない／TP・SL 指値 maker／TIME 成行 taker+slip＝上記 D のとおり一致。
- **H6** 価格非依存: ゾーン束ね・幅・SL バッファ・SCALP_FLOOR 全て%基準・USD 絶対値の閾値なし。
- **H7** 5m 標準（1h はゾーン構築の上位足・執行は 5m）。
- **H8** 期間: periods.py import（学習 fit なし＝素ルール・診断は学習窓のみ・採点は score_official 窓）。
- **H9** 最小注文: 部分決済 0.012 BTC ≥ 0.0001・名目 ≥$5（score.assert_min_order 実測）。
- **H10** サイズ: UNIT は比較用・cap 内配分（add 2 lot）。
- **H11/H12** 合格ライン・異常値 STOP: score.py 自動。
- **H13** judge 固定: 触れない（新 exit_reason なし）。
- **H14** 発注フラグ: 非該当（バックテストのみ・run_once/replay 実行なし）。
- **H15** ボラ逃げ: 非該当を照合済み＝v11 は方向スコア/ML なしの素ルール。①揺れ幅（ATR/ボラ）は入口判定に不使用（ゾーン幾何と RSI9 のみ・SL もゾーン基準で ATR 不使用）②SHORT 専用（分離不要）③ボラ系はどこにも接続しない。
- **H16** 1変更・不再演: 上記 C のとおり。

## F. 受け入れ判定（実験前固定・審判の門）
1. **自己検査（実装後・実行前）**:
   - --v11 OFF 恒等＝v10_017 と CSV md5 一致（既定/診断/採点の3経路）。
   - **1h ゾーン一致 assert**＝_zones_v11_1h の range_ok/res/sup が計器出力 labels_v17.csv と全期間一致（移植の正しさを機械担保＝視認校正した物と同じ判定である証明）。
   - 番人メタ確認＝わざと壊して落ちるか（short_only assert に LONG 玉・cap に 0.13・tp_ge_sl_check に逆 R:R を渡して停止確認）。
   - leak grep assert・py_compile・DESIGN_CONTRACT 照合（require_design_contract_before_run が実行前に機械照合）。
2. **学習窓 diagnostic**（採点窓不参照）: 件数/日（対照: v11 / v11-no-add / v11-single-tp）・保有分布（分単位維持）・range_ok_v11 通過率と ADX40+ 混入率（v10 の 53.1%/38.5% から低下すること）・TP1/TP2/SL/TIME の内訳。
3. **precheck**（学習窓 breakeven）: **be ≥ 1.0 で PASS のみ採点へ**。FAIL なら採点温存・停止し「採用に至らず」と記録（v5/v6/v10 と同じ停止ガード＝赤字帯の採点浪費を防ぐ）。
4. **両窓 score.py（公式・唯一の判定）**: 合格ライン＝
   - **件数/日 > 0.97（v10 超え＝scalp 役割：件数/日を上げる。決済行ベース）** ∩ **net > v8_013（−$18＝E37 現地面）** ∩ 非degenerate（玉数・入口数を確認）
   - 短保有維持（保有中央値が分単位・60分 backstop 内）・H12 異常値 STOP（勝率>70% 等は調査）。
   - 割れたら「採用に至らず」と記録し ratchet 維持（数字のまま出す）。
5. E36+E37 合算 $600 マイルストーンへの位置づけ: v11 が黒字地面を作れたら次レバー（taker_ls 需給フィルタ＝v12 第一候補・件数積み増し）へ。

<!-- ARC order=25 iter="E37 v11 視認校正レンジ計器の組み込み（1hゾーン×複数TP+add）" 前提="E37未採用・v10 precheck FAIL be−0.63＝レンジ判定にトレンド排除なしが確定・レンジ判定計器を作り直しまこさんが視認校正で概ね良いとした上" 採否="未(実装前)" base_csv="trades_e37_range_scalp_v8_013_score.csv" score_csv="" train_csv="" 狙い="v10 の敗因＝range_ok_v10 のトレンド混入（通過率53.1%・ADX40+38.5%・N11方向ミス89%）を、まこさん視認校正済みの v17 計器（1hタッチ実績S/Rゾーン∩5分ゾーンブレイク離脱・トレンド排除はゾーンが立つか否かが担う）への差し替えで直し、同時に §1.2.1「小刻みに大量」を KB §6.5（複数TP部分決済+add＝V9型）で仕組み化して E37 初の黒字地面を出す" 内容="--v11=①range_ok_v11（1h 168h窓・束ね0.3%・タッチ≥2・幅≥0.4%・5分ブレイク離脱＝v17計器と同一ロジック・labels_v17.csv 一致assert）②入口=到達∩陰転∩RSI9>70反転（v10維持）SHORTのみ ③出口=TP1(中間・半分・PARTIAL_TP)+TP2(中央・残り・TP_FILLED)+SL(ゾーン外0.05%)+TIME60分・TP幅≥SL幅∩TP1幅≥SCALP_FLOOR必須 ④add=入口再発火で同量UNIT追加・V11_MAX_ADDS=2(0.048BTC)・既定OFF=v10恒等" 方法="自己検査(OFF恒等md5・1hゾーンlabels_v17一致・番人メタ確認・cap/leak grep)→学習窓diagnostic(件数/日・ADX40+混入がv10比減・対照=no-add/single-tp)→precheck be≥1.0(FAILなら採点温存停止)→両窓score.py(件数/日>0.97∩net>v8_013(−$18)∩非degenerate∩短保有維持・割れたら採用に至らず)" -->

## DESIGN_CONTRACT
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["range_ok_v11", "short_only_v11", "tp_ge_sl_check_v11", "_zones_v11_1h", "PARTIAL_TP", "V11_MAX_ADDS"]
}
```

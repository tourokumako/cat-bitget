# acceptance.md — E37 v4 教科書 BB レンジスキャル（SHORT のみ）

TARGET: scripts/priority_rebuild/e37_range_scalp.py

DESIGN_CONTRACT:
```json
{
  "impl_file": "e37_range_scalp.py",
  "self_check_calls": ["BAND_K", "RSI_HI", "ADX_MAX", "K_SL", "TP_FILLED", "SL_FILLED", "short_sig"]
}
```

## A. これは何か（1行）
v3（向き無し両側 maker MR スキャル・月−$807・サイコロ以下）を捨て、**教科書どおりの BB レンジ逆張りを SHORT 単側で1本**組み直す。上バンド(+2σ)超えで売り・RSI>70 確認・ADX<20 で非トレンド地合いのみ・中央線(SMA20)で利確・ATR-SL。

## B. 深掘り4点
- **① 真因**: v3 の壊滅は入口の作りにある。(a) 「行き過ぎ」を dev_z 浅い乖離(±0.8σ・q30/q70)＝ただのノイズで判定し無差別にばら撒いた。(b) maker 売り指値が close のすぐ上＝価格がさらに上がった時だけ約定＝**逆選択で逆行玉ばかり掴んだ**（N11 含み益になった玉 0%）。(c) ADX<q60(=37.54) で強トレンドをほぼ通し band walk に轢かれた。(d) TREND_CONT の taker 早切りが逆行玉を高コストで損確定（−$5,510）。＝壁（レジスタンス）を使わない、コンフルエンス無しの逆張りもどき。
- **② 期待値分解**: v3 は 平均勝ち$3.50 / 平均負け$5.45 / 勝率41.5% ＝ 必要勝率60.9%に19.4pt不足。教科書 MR は「小さい勝ち多数・稀に大負け＝高勝率型」（WebResearch 全ソース一致）。動かすのは**勝率**（本物の壁+2σ×RSI>70×ADX<20 で反転する場面だけに絞る）と**平均負けを ATR-SL で限定**。R:R は中央線までの戻り幅（≈2σ）vs 2×ATR ＝ おおむね 1:1・教科書 min。
- **③ root か symptom か**: root。v3 の入口（浅い乖離＋逆選択＋トレンド混入）を根から差し替える。symptom パッチ（R:R だけ弄る）は前セッションで的外れと確認済み。
- **④ ベースアップ**: 直近読了＝entry_exit_relationship_kb §7/§8/§9/§18・trade_methods_study §1-3・cc_entry_logic_self_study §1-3・trade_analysis_methods_kb §0-7・analysis_playbook §2・exchange_spec 決済方法・cat_requirements §6.1。WebResearch 4種別＝(教育)LuxAlgo Fading Extremes／(バックテスト)QuantifiedStrategies BTC BB／(学術/クオンツ)arxiv BB・Ernie Chan・QuantStart（上バンド売り→移動平均決済・手数料10bps で Sharpe 4.8→3.5・トレンドで劣化）／(学術・crypto)SSRN/QuantPedia（★BTC は高値で trend・安値で revert＝**負のリターンの方が強く戻る**＝SHORT の上バンド fade は MR の弱い側・要監視）。

## C. 変更の単位
- **1レバー**: E37 の戦略ロジック（入口＋出口）を教科書 BB レンジ逆張り SHORT 単側に丸ごと差し替え（v3 は不採用＝ratchet 対象でなく、新しい MVP を作る＝アジャイル「動くベースを作る」段）。
- **★疑似シミュ由来の固定値ゼロ**: (a) 全ての値は**教科書の業界標準 a-priori**＝BB 20期間/2σ・RSI>70・ADX<20・SL 1.5-2×ATR（WebResearch 複数ソース＋辞典）。(b) probe（疑似シミュ）で出した特定数値（θ/段数/AUC 等）を焼いていない＝probe を一切使っていない。(c) 採否は probe でなく**実エンジン両窓 score.py の数字**で決める。
- **過去失敗の不再演**: 入口で「向きを当てる」路線（v1 z-score/v2 climax/v3 両側 fade）は捨てる。本 MVP は「壁（+2σ）で反転を確認して逆張り」＝向き当てでなくレンジ逆張り。選別で件数を潰す MVP（0.32件/日）の轍は、頻度を diagnostic→本走 で先に確認して監視（低すぎれば教科書枠内で緩めるのは次 iter）。
- **★ARC マーカー**:
<!-- ARC order=18 iter="E37 v4 教科書 BB レンジスキャル SHORT" 前提="新規MVP・base無し(iter1地面がv3)" 採否="未定(採点で判定)" base_csv="" score_csv="" train_csv="" 狙い="v3の入口破綻(浅い乖離+maker逆選択+トレンド混入+taker早切り)を捨て教科書BBレンジ逆張りSHORT単側を最小で組み地面を測る" 内容="BB(20,2sigma)上バンド超え売り∩RSI>70∩ADX<20 / TP=中央線SMA20 / SL=K_SL×ATR / 両側・range_score・メタ・TREND_CONT全撤去" 方法="WebResearch(LuxAlgo/QuantifiedStrategies/arxiv/ErnieChan/QuantStart/SSRN)準拠・実エンジン両窓score.pyで採否" -->

## D. 審判（score.py / eval_engine）整合
- **新しい exit_reason を出すか？ → NO**。使う出口は既存登録の **TP_FILLED（maker）/ SL_FILLED（maker）/ TIME_EXIT（taker backstop）** のみ。TREND_CONT は撤去。score.py 登録・既知答えテストの変更は**不要**。
- **決済方法（exchange_spec / cat_requirements §6.1.1）整合**: SHORT 単側・MAX_ADDS=1＝同サイド merge の心配なし（1建玉）。部分決済（scale out）は使わず全量1TPで決済（MVP・教科書）。予算0.12は全採用戦略の共有枠だが本 CSV は E37 単独 cap 実測（_verify_cap）。
- **コスト種別**: entry=指値maker / TP=指値maker / SL=指値maker / TIME=成行taker+slip（H5・eval_engine と一致）。judge の計算式は触らない（H13）。
- **命名**: e37_range_scalp.py（既存・pdca_mark 登録済 e3N）／実験は --tag で連番。分析は既存の report.py / analyze.py。
- **サイドカー**: strat_base._output_and_report 経由で <stem>_params.json を出す（report.py 節0 が表示）。使用パラメータに BB/RSI/ADX/TP/SL/期間/サイズ ＋ Entry/Exit ロジックを載せる。
- **共通土台**: strat_base から UNIT/CAP/TTL/ENTRY_OFFSET/load_5m/_verify_cap/_funding_cost/_output_and_report を import（個別に命名/archive/コスト定数を書かない）。

## E. §4.6 ハード制約 照合
- **H1 cap**: MAX_ADDS=1・size=UNIT(0.024)・単一スロット ＝ 合計≤0.12 自明 ＋ _verify_cap 実測 assert。
- **H2 leak**: 指標は当該足まで（sma/std/dev_z/atr/adx/rsi は rolling・負shift/center=True を grep assert）。分位 fit なし（閾値は a-priori 定数）＝学習窓不要だが periods は import。出口は約定 bar の次以降。
- **H5 約定**: entry 指値maker / TP・SL 指値maker / TIME 成行taker+slip。
- **H6 価格非依存**: dev_z（標準化）・RSI（0-100）・ADX・TP=SMA価格への戻り（比率）・SL=ATR比。USD 絶対値の閾値/ラベルなし。
- **H8 期間**: 定数 a-priori なので学習窓 fit なし。採点は periods 正本（採点窓 2025-06〜2026-02）・封印不参照。
- **H13 judge**: score.py/eval_engine を触らない（import のみ）・新 exit_reason なし。
- **H15 ボラ逃げ**: 方向＝位置（dev_z＝+2σ）＋RSI＝方向シグナル。ATR は SL 幅（大きさ）にのみ使用＝方向スコアに ATR を支配させない。SHORT 単側。
- **H16 1変更**: E37 の入口＋出口を教科書 BB レンジ逆張り SHORT に差し替え（1戦略ロジック）。

## F. 受け入れ判定
- **自己検査**: (a) cap 実測 max≤0.12（_verify_cap）(b) leak grep assert（shift(-/center=True なし）(c) SHORT のみ（long_sig を出さない）を件数で確認。
- **頻度 diagnostic 先出し**: --diagnostic で 上バンド+RSI>70+ADX<20 の発火件数/日を先に確認（degenerate/過しぼり点検・0.32件/日 の轍防止）。
- **公式判定**: score.py で採点窓（2025-06〜2026-02）net ＋ precheck（breakeven 倍率）。CC は net 計算に触れない（import のみ）。学習窓 net もあわせて出す（両窓）。
- **採否**: 実エンジン両窓 score.py の数字で判定（probe でない）。v3（月−$807）を明確に上回るか・手数料負けを脱するかを見る。degenerate（件数ほぼゼロで損が小さいだけ）でないか件数で確認。

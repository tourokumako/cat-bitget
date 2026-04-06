# lessons.md — 過去の失敗・教訓（V8移行時含む）

## V8移行時の教訓

### L-1: pandas/numpy 互換性
- V8移行時に Option B（adapter）で詰まった主因はライブラリバージョン不一致
- 解決策: .venv 内のバージョンを先に確認してから進める
- 現状: pandas 2.3.3 / numpy 2.4.0 / ta 0.11.0 → V9と互換性あり（確認済み）

### L-2: マーケット発注の手数料インパクト
- V8はマーケットエントリー → taker手数料が積み重なり利益を圧迫
- V9対策: 指値エントリー + 指値TP（maker）で手数料を抑制
- FEE_MARGIN=1.5 を TP計算に組み込んで手数料分を回収

### L-3: state ファイルの中途半端更新
- API失敗時に open_position.json が半端に更新されると二重EXIT等が発生
- 対策: API呼び出し後にレスポンスを確認してから state 更新（アトミックに）

## Claude との作業ルール

### L-4: ドキュメントは草案→承認→書き込みの順
- 「突然資料まとめだすのやめて」— 合意なしにファイルを作成しない
- 草案をチャットに提示 → OK をもらってから Write ツールで書き込む

### L-5: 1ターン1箇所変更
- core_rules.md にも記載: 一度に複数箇所変更しない
- 理由: デバッグ時にどの変更が原因か追えなくなる

### L-6: パラメータ値は必ず一次ソースで確認
- validate_archive.py の値（分析用）と CAT_v9_regime.py 本体の値が異なる場合がある
- 正本: `strategies/CAT_v9_regime.py` の params dict（2829-2935行付近）

### L-7: S-7待機中の runner STOP は「TP/SL約定」が第一候補
- S-7テスト待機中（EXIT発火待ち）に runner が STOP した場合、まず「TP/SL約定でポジションが消えた」可能性を疑う
- `tp_order_missing` + ポジション消滅 = S-7シナリオ（エラーではない）
- **Why:** WORKFLOW.mdに次タスクが明記されていても、STOPログを見た瞬間にエラーと誤判断してしまった
- **How to apply:** runnerがSTOPしたら、まずWORKFLOW.mdの「次のタスク」と照合してから原因を判断する

### L-9: Phase 2テストは手動1回実行。autoループはテスト中禁止

- `while true` autoループはPhase 5（常時稼働）用。Phase 2テスト中は使わない
- テスト中は `.venv/bin/python3 runner/run_once_v9.py` を1回ずつ手動実行する
- 各runの前にClaudeが「何が起きるか・成功条件」を提示 → GOをもらってから実行
- autoループ中はTPやSL約定など外部イベントが予告なく発生し、テスト状態が崩れる

**Why:** autoループ中にTP約定でポジションが消え、S-8テストの機会を失った。
overrideバグとの組み合わせで意図しない2回目発注も発生した。
**How to apply:** Phase 2テストでrunを実行するたびに必ずGOを得る。
1回のrunで何が起きるかを事前に明示してからBashを叩く。

### L-10: Bitget hedge_mode の能動クローズは close-positions エンドポイントを使う

- `place-order + tradeSide: "close"` は one-way mode 専用。hedge_mode では **22002 "暂无仓位可平"** エラーになる
- 正しいエンドポイント: POST `/api/v2/mix/order/close-positions`
  - パラメータ: `symbol` / `productType` / `holdSide`（"long"/"short"）
  - SDK: `self.api.closePositions({...})`（bitget/v2/mix/order_api.py L25）
- **Why:** `tradeSide: "close"` は get_single_position レスポンスにも存在するフィールド名で、
  place-order のリクエストパラメータとして使えると誤解しやすい
- **How to apply:** close 処理を変更・確認するときは `closePositions` エンドポイントを使っているか確認する

### L-8: 実行コマンドは `.venv/bin/python3` を使い、冒頭に RUN START を入れる
- システムの `python3` には `requests` 等がインストールされていない → 即終了・無音で失敗する
- cron・whileループ・手動実行コマンドを提示する際は必ず `.venv/bin/python3` を使う
- 実行コマンドの冒頭には必ず以下を付ける（CLAUDE.md MUST項目）:
  ```
  echo "=====🚀  RUN START $(date) =====" && .venv/bin/python3 runner/run_once_v9.py
  ```
- **Why:** `python3` で無音失敗した際、ユーザーが何も出ないと報告するまで気づけなかった。RUN STARTがあれば即座にPython到達前の失敗と判別できる

### L-11: 特定・実装・記録の分離による抜け漏れ防止

**再発防止フロー（以下の順を必ず守る）:**

1. **特定したらすぐ書く** — ギャップ・修正案・未確認項目を発見した瞬間に
   `project_v9_progress.md` の未完了リストへ記録する。実装より先。
2. **1トピック完結してから次へ** — 「特定→実装→チェックリスト追記→文書更新」が
   揃ってから次のトピックに移る。途中で別トピックに引っ張られない。
3. **「次に進みますか？」の前に確認** — 次トピックを提案する前に、
   今のトピックで特定した全項目が未完了リストまたはチェックリストに記載済みかを確認する。
4. **セッション終了前の読み合わせ** — `project_v9_progress.md` 未完了リストを
   声に出して読み、会話中に出た項目と照合する。漏れがあれば追記してから終了する。

**Why:** 複数トピックを並走させると、特定済みだが未記録の項目が会話の流れで消える。
今セッションでは hedge_mode 固有テスト項目（5件）を特定後に別実装に移ったため未追加になった。

**How to apply:** 何かを「発見・特定」した時点でそれをトリガーとして
project_v9_progress.md を開き、未完了リストに書いてから実装に入る。

### L-12: TTLキャンセル後の PARTIAL_FILL_TP_SET 誤発火

ADDのpendingがTTL切れキャンセルされた際、既存ポジションがあると
`remaining_sz > 0` が True になり PARTIAL_FILL_TP_SET が誤発火する。

修正: `remaining_sz > existing_sz`（ADD前のポジションサイズを基準にする）
- `open_pos is None` → 新規ENTRYの部分約定 → TP設定が必要
- `remaining_sz > open_pos["size_btc"]` → ADDの部分約定 → TP再設定が必要
- `remaining_sz == open_pos["size_btc"]` → ADDは未約定 → 何もしない

**Why:** TTLキャンセル後のポジション残存チェックが「増加分」でなく「存在有無」だった。
**How to apply:** S-1③テスト時に必ず PARTIAL_FILL_TP_SET が出ないことを確認する。

### L-13: SL_PCT が小さすぎると 40917 エラーで confirm_entry STOPループになる

SL_PCT が極小（例: 0.0003）の場合、ADD約定後〜SL設定の数秒間に
価格がSL圏内まで下落すると Bitget が 40917 "SL価格 < mark_price" を返す。
このとき `_confirm_entry` は STOP するが `pending_entry.json` が未クリアのまま残り、
次回 run でも同じフローを繰り返す無限 STOP ループになる。

**Why:** SL_PCT=0.0003 でテストしたところ、ADD約定後に価格がSL圏内まで急落して発生。
本番では SL_PCT=0.05 のため通常起きないが、極端な急落（5%超/数秒）時には可能性あり。
**How to apply:**
- `_place_sl` で 40917 を検知したら即 closePositions を呼ぶ（✅ 修正済み 2026-03-23）
- STOP 前に pending_entry.json を必ずクリアする（✅ 修正済み 2026-03-23）
- SL_PCT テスト値は 0.001 以上を目安にする（0.0003 は小さすぎる）

**修正内容（2026-03-23）:**
1. `filled` + `_confirm_entry` 例外時に `_PENDING_PATH.unlink()` を except ブロック先頭に追加（STOPループ防止）
2. `_place_sl` が 40917 を受け取ると `RuntimeError("SL_PRICE_INVALID:40917: ...")` を raise
3. 呼び出し元 except ブロックで `"SL_PRICE_INVALID:40917"` を検知 → `_do_close` で即クローズ → `EXIT_COMPLETE(exit_reason=SL_PRICE_INVALID)` ログ

### L-14: Bitget デモ口座では SL plan order が「消滅するだけでポジションを閉じない」バグがある

デモ口座で SL が発動価格を超えた際、plan order が entrustedList から消えるが
ポジション（total > 0）はそのまま残存する。本番では再現しない可能性が高い。

**観測内容（2026-03-23 セッション20）:**
- SL plan order が mark_price ~68627 で entrustedList から消滅（planStatus="executed" に移行）
- しかし exchange の position.total = 0.0719 のまま残存
- exchange レスポンス: `stopLoss=""`, `stopLossId=""` → SL設定が消えている
- fill-history は `fillList: null` → close 約定なし（実際に決済されていない）

**Why:** Bitget デモ環境固有の制限と推定。本番 API との挙動差異。
plan order の「消滅」= 約定証拠とするのは危険（デモでは偽陽性になる）。

**How to apply:**
- SL_FILLED の証拠は plan history の消滅ではなく fill-history の close 約定のみとする（Change A）
- SL 消滅 + ポジション残存 = 異常状態 → `STOP(sl_order_missing_pos_exists)`（Change B）
- デモで SL_FILLED の自動確定テスト（S-7②）は不可。本番でのみ確認する
- fill-history の `fillList: null` はデモ口座では正常レスポンス（エラーではない）

### L-16: 改善は「集計分析→個別分析→仮説→検証」の順で行う（当てずっぽう禁止）

パラメータを直感で変えてReplayを回すと悪化することが多い。必ず以下の順を守る：
1. 集計分析（Priority別・Exit reason別）
2. 個別分析（勝ちvs負けのエントリー時指標分布を比較）
3. 差が大きい指標を根拠に仮説を立てる
4. 変更件数を事前に計算して提示する
5. Replay で検証

**Why:** TIME_EXIT の早期カット試行など、根拠なしの変更が連続して悪化した。
**How to apply:** Step 2.5（個別分析）なしに Step 3（改善案提示）に進まない。

### L-17: P2 LONG は ADX < 25 での発火が損失の主体

ADX 15-20帯（218件）が -$1,098 の損失源。ADX >= 25 フィルターで +$608 改善を確認（2026-04-03）。
フィルター追加後の P2 NET: -$1,392 → -$784。

**Why:** トレンドが弱い局面でのストキャスゴールデンクロスはダマシが多い。
**How to apply:** P2 ADX_MIN は 25.0 で設定済み。他の Priority でも ADX分布を先に確認する。

### L-18: cat_v9_decider.py の RSI カラム名は rsi_short

- `get("rsi")` ではなく `get("rsi_short")` が正しいカラム名
- `get("rsi")` は存在しないカラム → `nan` → `nan <= 60.0` = `False` → 全件除外
- **Why:** P4_RSI_MAXフィルター追加時に `get("rsi")` と書いてP4が0件になった
- **How to apply:** cat_v9_decider.py でRSIを参照する際は `rsi_short` を使う。
  他の指標も正しいカラム名を事前に確認してから書く（replay_csv.py L541付近参照）

### L-19: Priority間の相互作用を必ず考慮する（フィルター追加前にチェック順を確認）

P4フィルターを追加すると、除外トレードが P2 に流れ込む（decider のチェック順: P2→P22→P24→P23→P4 ではなく P4が途中に入るため）。単一Priority での試算が他Priority への流入で相殺・逆転することがある。

**失敗例（再現2件）:**
- P4_RSI_MAX=55: P4 +$103 改善 → P2 -$167 悪化、トータル -$65（2026-04-03）
- P4_RET5_MAX=0.25: P4 ±0改善（+$91→+$91） → P2 -$47 悪化（+$138→+$91）、トータル +$76→+$29（2026-04-04）

**CSVシミュレーションの限界:** CSV上では P4 単独 +$34 改善と計算されるが、Replay では P4 を除外したバーで P2 が代わりに発火するため実際の改善は発生しない。CSVシミュレーションは同一バーの Priority 流入を考慮しない。

**Why:** P4 と P2 はどちらも LONG。同じバーで P4 が弾かれると P2 条件を満たすケースがある。
**How to apply:**
- P4単独フィルターを追加する前に「同バーでP2が発火する可能性があるか」を cat_v9_decider.py のコードフローで確認する
- P4フィルターは P2 と同時適用（ret_5 > 0.25 なら P2 も除外）しないと L-19 を防げない
- Priority 間に重複するエントリー条件がある場合は特に注意

**失敗例（再現3件目）:**
- P4_ADX_MAX=30（ADX>=30 P4 除外）: P4 +$77 改善 → P2 -$318 悪化（12件流入・avg -$26/件）、トータル -$241（2026-04-05）
- L-19 はシミュレーション(+$123) を Replay(-$241) が大きく下回る形で発動。P2 が ADX>=30 スロットを埋めた。
- **打開策:** P4_ADX_MAX + P2_ADX_MAX を同時設定してL-19 フローを塞ぐ（同条件を両方弾く）か、エントリーフィルターでなくエグジットロジックを変える。

### L-20: TIME_EXIT_MIN 短縮は再エントリー増と早期TP機会損失を招く

P2_TIME_EXIT_MIN 480→200 にしたところ TIME_EXIT 件数が +39件増、TP件数 -16件減でトータル悪化（-$80）。早期カットが「次のエントリー機会」を生み件数が膨らむ。また一部TP到達できたはずのトレードも失う。

**Why:** 「早くカットすれば損失が浅くなる」という直感が正しくない。相場が一時逆行後に回復してTPに届くパターンを潰してしまう（L-15 と同じ構造）。
**How to apply:** TIME_EXIT_MIN 変更は件数変動・TP件数変動も含めて評価する。試算前に「カットされたトレードがTPに届いていたか」をデータで確認してから変更する。

### L-15: P23 SHORT MIDTERM_CUT は TIME_EXIT より早い段階で損失を固定しやすい

hold=240min 時点でカットすると、360min TIME_EXIT より大きい損失になるケースが多い。
相場が一時的に逆行して最悪値を付け、その後部分回収するパターンに干渉してしまう。

**観測内容（2026-04-03）:**
- P23 SHORT MIDTERM_CUT（hold≥240min, unreal<-$25）を replay_csv.py に追加してテスト
- 結果: NET -$146.60 → -$187.96（悪化）
- TIME_EXIT 16件 -$529 → 10件 -$158（改善）だが MIDTERM_CUT 7件 -$449 が新たに発生
- 例: 240min 時点 -$50 だが 360min には -$27 まで回収したケース → MIDTERM_CUT が損失を固定

**Why:** TIME_EXIT の「360min時点の損失」は一時的な最悪値を過ぎた後の価格を見ている。
MIDTERM_CUT で早期カットすると最悪値付近で決済するリスクが高い。

**How to apply:**
- P23 SHORT の損失削減は「カットタイミング調整（MIDTERM_CUT）」よりも
  「エントリー制御」または「ADD 上限削減」で攻める
- MIDTERM_CUT を使うなら TIME_EXIT 直前（≥310min）かつ深い損失（<-$50）の
  閾値が最低ライン。それ以外は逆効果になる可能性が高い

### L-21: Replay の SL シミュレーション欠陥（SL 縮小時に露呈）

SL=5% 時代は add_count=1 の `sl_price=None` でも実害なし（SL 到達がほぼゼロ）。
SL を縮小すると2つの欠陥が露呈した:
1. add_count=1 の新規エントリーで `sl_price=None`（SL が設定されない）
2. TP/SL 判定が close ベース（high/low ではない）→ 狭い幅で検知漏れ

**修正済み（2026-04-03）:**
- `sl_price`: 常に `_calc_sl_price()` でセット（add_count=1 でも）
- TP 判定: `high_p >= tp`（LONG）/ `low_p <= tp`（SHORT）
- SL 判定: `low_p <= sl`（LONG）/ `high_p >= sl`（SHORT）

**Why:** SL=5% では修正前でも誤差が無視できたため、SL 縮小検証まで気づけなかった。
**How to apply:** SL 幅を変更する前に Replay の SL シミュレーション精度を確認する。

### L-22: シグナルの edge 検証は「Replay エントリー固定 → bar-by-bar グリッドサーチ」

1. Replay を走らせてエントリーポイントを確定（entry_time / entry_price / side）
2. そこから bar-by-bar で TP/SL 先着を計算（ohlcv の high/low を順に追う）
3. 各 TP%/SL% 組み合わせで TP 到達率 vs ランダムウォーク理論値を比較
   - 理論値: `SL_pct / (TP_pct + SL_pct)`
   - 実測が理論値を +5% 以上上回れば edge あり

全 Priority でランダムウォーク理論値を **+10〜23% 上回る edge を確認**（2026-04-03）。

**Why:** Replay 実走は出口ロジックが絡んで「シグナルの純粋な edge」が見えにくい。
**How to apply:** 出口設計を変える前に、まずこの方法で edge の有無・大きさを確認する。

### L-23: add=1 制限はシグナルの edge を殺す

ADD の本来の効果: 逆行時に平均エントリーを改善 → TP ヒット率が上がる設計。
add=1 に制限すると「即 TP or 即 SL」設計になり、ATR より狭い SL 幅では連続被弾。

2026-04-03 セッションでは add=1 のまま TP/SL 設計を変えようとしたが、
エントリー頻度が 3.5件/day に低下し EV 上限が ~$21/day になった。

**Why:** add 制限はフィルタリング改善の一環として導入したが、ADD 本来の役割（逆行吸収）を失わせる。
**How to apply:** 次セッションでは add=3 を復活させてから TP/SL を設計する。

### L-25: post_only maker 指値のfill rate は33%しかない（モメンタム系シグナルと相性が最悪）

ENTRY_SEND 278件 → ENTRY_CONFIRMED 92件 = fill rate 33%（2026-04-03 ライブログ確認）。

**Why:** post_only 指値は close ±0.01% に置かれる。LONG シグナルはモメンタム上昇時に発火するため、
価格はさらに上昇して指値には戻ってこない。Replay は全約定前提なので 3× 過大評価になっていた。
パラメータをいくらチューニングしても fill rate 問題が解決されない限り実効 NET は改善しない。

**How to apply:**
- エントリーを taker（成行 or aggressive limit）に変更する（run_once_v9.py + replay_csv.py 両方）
- Replay でも taker 想定（= close 価格で即約定）に統一してから TP/SL を最適化する
- fill rate < 50% の状態でパラメータチューニングをしない

### L-26: Entry フィルターのバーズレ問題（signal バー vs fill バー）

CSV シミュレーションと Replay で `ret_5`/`atr_14` の参照バーがズレる。

- CSV シミュレーション: fill バー(i+1)の値で判定（_calc_entry_states）
- check_entry_priority フィルター: signal バー(i)の値で判定

特に `ret_5` のような短期リターン系は1バーで大きく変わるため、
シミュレーション +$143 改善 → Replay 実質 +$2 という乖離が発生（2026-04-04）。

**Why:** Replay は「シグナル発火後に約定を試みる」設計のため、約定が確定するのは
シグナルバーの次のバー以降。シグナル時点のモメンタム指標は約定時には陳腐化している。

**失敗例（再現2件）:**
- P23 transit_A × ret_5>0 フィルター: CSV +$143 → Replay +$2（2026-04-04）
- P23 ret_5 ≤ 0.05 フィルター: CSV期待値 +$242 → Replay +$6。TP 40件が余計に除外（2026-04-05）

**結論: `ret_5` を Entry フィルターに使うことは禁止。** CSV と Replay で件数が大きく乖離するため検証不能。

**How to apply:**
- `ret_5` を Entry フィルターとして提案しない（CSV シミュレーション値が信頼できない）
- Exit タイミング変更（TIME_EXIT_MIN 短縮）はバーズレがなく、Entry フィルターより CSV 精度が高い（ただし L-20 も参照）
- Entry フィルターに使える指標は atr_14（14本平均で変化が緩やか）のみ実績あり

### L-27: ~~Replay CSV の entry_time / exit_time は JST、candles.csv は UTC~~（2026-04-05 根絶済み）

**修正済み**: `replay_csv.py` の `_ts_to_str` を `tz=timezone.utc` に変更。
entry_time / exit_time は UTC で出力されるようになった（candles.csv と一致）。
entry_hour は引き続き JST（時間帯分析用）。MFEマッチ率 54% → 100% に改善。

**観測（2026-04-05）:**
- P23 entry_time "2026-01-07 11:20:00"（JST）で candles を検索 → 実際は UTC の 11:20バー（JST 20:20）を参照
- 「届かずグループ8件・MFE>1%」と誤判断 → UTC修正後は届かず0件・全件が逆行グループ
- 逆行グループの誤った MFE（CSVの low が entry_price より大幅低い別日のバー）が「TP到達」と見えた

**Why:** replay_csv.py が JST タイムスタンプを出力するが、candles CSV は UTC。この差を考慮しないと 9 時間ずれたバーで MFE/追跡計算をしてしまう。

**How to apply:**
- 分析スクリプトで candles を参照する際は `entry_time_utc = entry_time_jst - pd.Timedelta(hours=9)` に変換する
- MFE計算・延長追跡・バー単位確認は必ず UTC 時刻で行う
- Replay CSV のタイムスタンプを candles に当てる前に「entry_price が entry_time バーの high/low 範囲内か」を確認してタイムゾーンを検証する

### L-24: 現設計の理論的な収益上限

```
エントリー頻度 × EV/trade = 日次収益
3.5件/day × $6/trade = $21/day （add=1, TP+2%/SL-1% 設計）
```

$120/day 達成には以下のいずれかが必要:
1. **ポジションサイズ拡大**: 0.024 → 0.16 BTC（資金・リスク増）
2. **エントリー頻度増加**: add 復活・Priority 条件緩和
3. **EV/trade 向上**: add による平均改善 or より精度の高いシグナル

add=3 復活はエントリー頻度・EV/trade 両方に効く可能性がある。

**Why:** add=1 制限 + narrow SL の組み合わせで設計的な収益上限が $21/day に低下した。
**How to apply:** 設計変更前に「件数 × EV/trade の天井」を試算してから進む。

### L-28: P22 TIME_EXIT短縮のシミュレーション限界（hold_min分析の欠陥）

**失敗内容（2026-04-05）:** P22のTP hold_min≤180minを「180min短縮でもTP safe」と判定したが、Replayで悪化（-$112）。

**Why:** hold_min分析は「最終的な保有時間」しか見えない。「途中（180min時点）でunreal<0だが、その後TPに到達する」トレードの存在を見落とす。P22 TP hold_min=180min近辺の件数が多く、このゾーンで意図しないカットが発生した。

**How to apply:** P22（SHORT干渉が強い）でのTIME_EXIT変更は孤立シミュレーション不正確に加え、hold_min分析自体も不正確。P22のExit変更はReplayのみで判断し、シミュレーション期待値を信頼しない。

---

## V10 開発の失敗教訓（2026-04-06〜）

### L-30: Bitget の 1m 足は約31日分しか取得できない

Bitget API で `granularity=1m` を指定すると、約31日以前は `data: []` を返す。
180日分リクエストしても31日しか取れない。

**How to apply:** 1m 足の長期データは Binance の公開 API（`fapi.binance.com/fapi/v1/klines`）を使う。
認証不要・1リクエスト1500本・180日分が約2分で取得可能（`tools/fetch_binance_1m.py`）。

### L-31: ストキャスのみのエントリーはコイントスに等しい（TP率47%）

フィルターなしのストキャスクロスは 90件/日 以上出るが、
エントリー後の短期方向性はほぼランダム（TP率47%）。
1:1 RR で損益分岐50%に届かず、手数料込みで必ず赤字。

**How to apply:** ストキャス単独でのシグナル設計は禁止。必ず方向性フィルターと組み合わせる。

### L-32: 重い指標（200EMA + BB タッチ）の同時成立は件数を激減させる

`close > 200EMA` + `close <= BB下限(-2σ)` + `Stoch クロスアップ` の3条件同時成立は
1分足では非常に稀（最終的に **1.7件/日** まで低下）。
BB_ENTRY_STD を 2.0σ → 1.5σ → 1.0σ と緩めても TP率は 46〜47% で変わらず、
件数が増えるだけで収益性は改善しない。

**Why:** Stoch が OB/OS に達するタイミングと BB 外側タッチが同時に起きることが本質的に稀。

**How to apply:**
- 1m 足には「軽くて反応が速い」フィルターを使う（20EMA・RSI9 等）
- 200EMA + BB の組み合わせは 1m には重すぎる。5m 以上の足向け
- 件数が 10件/日 を下回ったら条件が厳しすぎるサイン → 組み合わせ自体を見直す

### L-33: どのフィルターを加えても TP率42〜45% から動かない

20EMA / RSI9 / 200EMA+BB / trend_follow / mean_reversion と様々なフィルターを試したが、
TP率は **42〜45% で収束**。損益分岐（1:1 RR で50%）に届くフィルターが見つかっていない。

| MODE | TP率 | NET/日 |
|------|------|--------|
| ema20 | 42% | -$18.9 |
| rsi9 | 42% | -$8.1 |
| mean_reversion | 45% | -$5.0 |
| trend_follow | 23% | -$41.0 |

**Why:** 1m 足のランダムウォーク性が強く、短期方向性をフィルターで改善する余地が小さい。

**How to apply:**
- 新しいフィルターを試す前に L-22 の方法でシグナルの edge を先に確認する
- TP率改善が難しければ TP/SL の非対称設計（TP を広げて SL を狭く）で RR 比で補う

### L-34: SL なし（TIME_EXIT のみ）は逆行した損失を長時間抱えるため悪化する

SL を廃止すると TIME_EXIT avg が **-$4.15/件** になった（SLあり時は -$1.27）。
逆行したポジションを最大20分保有し続けるため損失が膨らむ。

**How to apply:**
- SL は必ず設定する。SL なし設計は 1m スキャルでは機能しない
- 「TP か SL のどちらかで決着・TIME_EXIT なし」の設計を先に検証すること

### L-29: スキャル化（TP縮小＋SL縮小）はadd構造と根本的に競合する

**失敗内容（2026-04-05）:** TP=0.003, SL=0.02でReplay実走 → NET $1,828→$464（-$1,364悪化）。SL_FILLED 2件→15件（avg -$53/件）。

**Why:** addが積み上がるほど同じSL幅での損失が倍増する（add=5でSL=2%発動 → size=0.12BTC × 2% × 65000 = $156/件）。スキャル型SLとadd構造は根本的に非互換。

**How to apply:** TP幅縮小とSL幅縮小を同時にやるときは「MAX_ADDSを0か1に制限」しないと設計崩壊する。add構造を維持するなら現行SL=5%は正当な設計（addの砦として機能）。

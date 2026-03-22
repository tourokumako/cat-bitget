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

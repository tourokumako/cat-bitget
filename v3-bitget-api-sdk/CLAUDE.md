# CLAUDE.md — cat-bitget

## Priority設計の根本思想（変更・廃止判断の前に必ず確認）

各 Priority は異なる相場局面に対応するために設計されている。
特定の Priority が特定の期間に負けていることは **設計上ありえる**。

| Priority | シグナル特性 | 得意な相場 |
|----------|------------|-----------|
| P2 LONG  | ストキャス GC + ADX フィルター | トレンド転換初動 |
| P4 LONG  | プルバックエントリー（BB slope + RSI） | 強いアップトレンド中の押し目 |
| P22 SHORT | RCI + BB 急落初動 | 高ボラ急騰後の反落 |
| P23 SHORT | BB + RSI 複合（じわ下げ） | 継続的な下落トレンド |
| P24 SHORT | RSI 過熱反転 | 過熱相場のピーク |

**廃止・削除の判断基準:**
- 廃止提案は「あらゆる改善手段を尽くしても edge がゼロと確認できた後」のみ許可
- Priority 単体が特定期間に負けているだけでは廃止の根拠にならない
- 廃止を提案する前に「なぜその Priority の edge が出ていないか」を必ず分析する

**ポジションサイズ制約:**
- 総ポジション上限: **0.12 BTC**（LONG/SHORT 各サイド独立）
- エントリーサイズ × (1 + MAX_ADDS) ≤ 0.12 BTC を守ること
- 例: 0.024 BTC → add 最大4回 / 0.02 BTC → add 最大5回
- BT での MAX_ADDS = 5（設計意図）。add は逆行時の平均エントリー改善が目的。

---

## 最終目標（常にこれを念頭に置くこと）

**Bitget本番運用で以下を同時に満たす状態にする:**
- 平均 NET ≥ $120 / day
- 15日 cumulative NET ≥ $1,800

## 現在のアプローチ（2026-04-03 更新）

`replay_csv.py` は `run_once_v9.py` を過去 CSV データで動かすツールとして位置づける。

1. 過去 CSV で `replay_csv.py` を実行 → 改善案を検証
2. Replay で改善確認 → 同じ変更を `run_once_v9.py` / `cat_params_v9.json` に直接適用
3. BT（cat-swing-sniper）は参照しない

**前提条件（これが崩れると改善が本番に反映されない）:**
- `replay_csv.py` の `_check_exits_replay` と `run_once_v9.py` の `_check_exits` が常に同期していること
- パラメータは `cat_params_v9.json` を一次ソースとし、両者が同じファイルを読むこと
- Exit ロジックを変更したときは必ず両ファイルを同時に更新する

## 目的（2026-04-03 更新）
**run_once_v9.py（Live BOT）のシグナル・Exit設計を改善し、
Bitget 本番で NET ≥ $120/day を達成すること。**

### BT（cat-swing-sniper / CAT_v9_regime.py）を参照しない理由
- close 即時約定前提のため Live BOT では構造的に再現不可能
- BT と Replay の乖離は解消できない（確認済み）
- BT の数値を持ち出した改善提案は無効

### 改善の唯一の指標
- `replay_csv.py` のみ（= run_once_v9.py の CSV バージョン・ロジック完全一致）
- Replay で改善確認 → `run_once_v9.py` / `cat_params_v9.json` に直接反映

---

## 入出力仕様

- 入力:
  - Bitget APIから取得した現在データ（価格・ポジション・残高・注文状態）
  - OHLCVローソク足データ（指標計算用・Bitget APIから取得）
- 出力:
  - 発注内容（side / size / price / tp / sl）
  - または `no_action`

## テストの位置づけ
本番稼働前のリリースゲートとして、本番環境と同一条件下のデモ画面でBOTを実行し、
注文・約定・ポジション管理が想定通りに動作し、資金リスクを発生させないことを
事前に検証する。テスト完了（Phase 3）後は本番稼働（Phase 4）が主目的となる。

**DRY_RUN（ALLOW_LIVE_ORDERS=False）は本番安全性の証明にならない。**
全S-xテストは `ALLOW_LIVE_ORDERS=True` + `paper_trading=true` での実API実行が必須。

---

## 絶対禁止（NEVER）

### 安全装置
- `ALLOW_LIVE_ORDERS=False` を True に変更しない（ユーザーのみ変更可）
- `paper_trading` フラグをコードで変更しない
- `run_once_v9.py` をユーザー確認なしに実行しない

### API・認証情報
- `config/bitget_keys.json` の中身をログ・画面に出力しない
- APIキー・シークレットをコードに直書きしない

### ファイル操作
- `state/open_position.json` を直接書き換えない（runner経由のみ）
- `state/` 配下のファイルを削除しない
- `config/` 配下のファイルを編集しない（読み取りのみ）
- `cat/indicators.py` / `cat/const.py` を変更しない

---

## AI行動ルール（MUST）

- コード変更は1回につき1箇所のみ
- 変更前に差分を提示してGOを待つ
- テスト実行前に以下を順番に確認してGOを得る：
  1. `paper_trading=true` をユーザーが目視確認
  2. `ALLOW_LIVE_ORDERS=True` をClaudeがRead確認
  3. `open_position.json` の現状をClaudeがRead
  4. 実行コマンドを提示 → GO待ち ← ここで必ず��まる
  5. 実行後、APIレスポンス（code=00000）をログからコピペして確認
- DRY_RUNで実施したテストを完了扱いにしない
- セッション終了前に以下を更新する（この3ファイルが唯一の正本。auto-memoryのproject_status_*.mdは廃止済み）:
  1. `WORKFLOW.md` — 現在のパラメータ・Replay成績・次のタスクを最新状態に
  2. `.claude/memory/project_v9_progress.md` — 今セッションの変更点・発見を追記
  3. `.claude/memory/lessons.md` — 失敗・再発防止ルール（草案提示→GO後に書き込み）
- セッション終了前に、今セッションで判明した失敗・予想外の結果・再発防止ルールを
  `.claude/memory/lessons.md` に追記する（草案提示→GOを得てから書き込む）。
  書くべきタイミング: バグ発見時・検証結果が予想と逆だったとき・仮説が外れたとき
- バグ修正・誤り指摘・API仕様の想定外・プロセス問題が発生したら、lessons.mdへの追記を能動的に提案する（草案提示→GOを得てから書き込む）
- 実行コマンドを提示する際は以下を必ずセットで示す：
  1. 何を実行するか（コマンド1行）
  2. 実行後に何が起きるか（期待する挙動）
  3. 成功条件（何が出たら✅か）
  4. コマンドの先頭に必ず以下を付ける：
     `echo "=====🚀  RUN START $(date) ====="` && （本コマンド）
     例: `echo "=====🚀  RUN START $(date) =====" && python runner/run_once_v9.py`

---

## セッション開始時に必ず読むこと

| ファイル | 内容 |
|---------|------|
| @bitget-python-sdk-api/WORKFLOW.md | 現在の状態・フェーズ・次のタスク |
| @bitget-python-sdk-api/.claude/memory/project_v9_progress.md | 実装進捗・未完了タス�� |
| @bitget-python-sdk-api/.claude/rules/core_rules.md | MUST/NEVERルール |
| @bitget-python-sdk-api/.claude/memory/lessons.md | 過去の失敗・行動ルール |

## 必要に応じて読むこと

| ファイル | タイミング |
|---------|-----------|
| `.claude/context/test_checklist.md` | テスト実行前 |
| `.claude/context/project_spec.md` | ファイル構成確認時 |
| `.claude/context/cat_v9_regime_map.md` | 原本 Exit 条件確認・Logic Parity 作業時 |
| `.claude/rules/exchange_spec.md` | APIエラー発生時・コード変更時 |
| `config/cat_params_v9.json` | パラメータ確認時 |
| `.claude/context/release_guide.md` | 本番切り替え時（Phase 4） |

---

## ファイル構成（V9）

| ファイル | 役割 | 変更可否 |
|---------|------|---------|
| `runner/run_once_v9.py` | 実行エンジン（発注・exit判定） | GO後のみ |
| `strategies/cat_v9_decider.py` | エントリー判断 | GO後のみ |
| `runner/bitget_adapter.py` | Bitget SDKラッパー | 原則変更しない |
| `config/bitget_keys.json` | APIキー（機密） | 読み取りのみ |
| `config/cat_params_v9.json` | V9パラメータ | GO後のみ |
| `state/open_position.json` | ポジション状態 | runner経由のみ |
| `cat/indicators.py` / `cat/const.py` | 指標計算・定数 | 変更しない |

---

## 急騰・異常検知時
- P23 SHORT add_count≥4 保有中に +$800/BTC/5min 以上 → 即アラート
- +$1,200/BTC/5min 以上 → 手動介入を促す
- Claudeは自動で決済・注文変更を行わない

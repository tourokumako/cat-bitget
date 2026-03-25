# CLAUDE.md — cat-bitget

## 目的
Bitget本番環境（BTCUSDT先物）において、CAT_v9_regime.pyのロジックを
**本番で再現可能な範囲で一致させて移植し、自動売買BOTを安全に継続稼働させること。**

### 再現の定義
- エントリー条件・決済条件・ポジション管理ロジックを一致させる
- 本番で観測可能な値のみを使用（未来値・MFE/MAE禁止）
- 約定・手数料・スリッページを含めた実運用挙動を前提とする

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
- セッション終了前にWORKFLOW.mdとproject_v9_progress.mdを更新する
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

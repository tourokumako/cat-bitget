# CLAUDE.md — cat-bitget（開発中）

---

## 現在の方針

V9シグナルをベースに、V10の設計思想（スキャル型・小利確）で調整する。
詳細な検証結果・パラメータ・次のタスクは WORKFLOW.md を参照。

---

## このBOTの存在意義

人間が24時間監視・執行できない相場を、ルール通りに動き続けることで稼ぐ。
- 感情に左右されない規律ある取引
- 24時間365日の自動監視・自動執行
- 人間が張り付かなくてよい時間コストの削減

---

## 設計思想

**V9シグナル × スキャル型TP（小刻みに利確を積み上げる）**

- タイムフレーム: 5分足
- シグナル: V9エントリーロジック（P2/P4/P22/P23）
- TP: スキャル幅（手堅く確実に取れる幅）で調整
- 広いTP・長い保有はスイング化するため避ける
- 検証は必ず複数レジーム（最低180日）で行う

---

## 目標

| 指標 | 基準 |
|------|------|
| 本番 NET 目標 | **$60/day** |
| 手数料コスト想定 | 100件/日 × $0.60 = $60/day |
| 必要 GROSS | **$120/day 以上** |

---

## 開発フロー

```
1. 5分足データ取得
2. 戦略設計（シグナル・TP/SL・add構造・フィルター）
3. シミュレーター構築（5分足対応）
4. バックテスト（複数レジーム・最低180日）
5. 本番投入判断
```

**検証は必ず複数レジーム（急騰/急落/レンジ）で行う。**

---

## 絶対禁止（NEVER）

- `ALLOW_LIVE_ORDERS=False` を True に変更しない（ユーザーのみ）
- `paper_trading` フラグをコードで変更しない
- `config/bitget_keys.json` の中身をログ・画面に出力しない
- `runner/replay_csv.py` / `runner/run_once_v9.py` をユーザー確認なしに実行しない

---

## AI行動ルール（MUST）

- 変更前に差分を提示して GO を待つ
- 実行コマンドは「何を実行するか・期待する挙動・成功条件」をセットで提示
- コマンド先頭に必ず `echo "=====🚀 RUN START $(date) ====="` を付ける

### セッション終了時に必ず行うこと（順番通りに）

1. **`lessons.md` を更新する**
   - このセッションで発見した失敗・教訓を L-XX 形式で追記する
   - 「同じミスを次セッションで繰り返さないか？」を自問してから書く
   - パス: `bitget-python-sdk-api/.claude/memory/lessons.md`

2. **`WORKFLOW.md` を更新する**
   - 現在の設計・パラメータ・Replay結果・次のタスクを最新状態に書き直す
   - パス: `bitget-python-sdk-api/WORKFLOW.md`

3. **Git コミットする**（ユーザーの明示 OK なしに commit しない）

   **コミット対象**
   - ロジックコード（.py）
   - パラメータファイル（cat_params*.json）

   **コミット禁止**
   - `config/bitget_keys.json`（機密）
   - `results/` 配下すべて
   - `*.csv`（過去データ・バックテスト結果）

   **コマンド制約**
   - `git add .` / `git add -A` 禁止。必ずファイル単位で add する
   - 作業前に `git status` を表示し、変更ファイル一覧を提示してから add する

   **コミットメッセージ**
   - 日本語で簡潔に（例: `refactor: エントリーロジック修正` / `feat: ADXレジーム判定追加`）

   **危険ファイル検知**
   - `bitget_keys.json` が変更されていたら必ず警告する

---

## セッション開始時に必ず読むこと

| ファイル | 内容 |
|---------|------|
| `bitget-python-sdk-api/WORKFLOW.md` | 現在の状態・次のタスク（**唯一の正本**） |
| `bitget-python-sdk-api/.claude/memory/lessons.md` | 過去の失敗・再発防止（V9含む） |
| `bitget-python-sdk-api/.claude/memory/project_v9_progress.md` | V9実装進捗（参照用） |

---

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `runner/run_once_v9.py` | 実行エンジン |
| `runner/replay_csv.py` | 過去CSV検証エンジン |
| `strategies/cat_v9_decider.py` | エントリー判断（P2/P4/P22/P23） |
| `config/cat_params_v9.json` | パラメータ（唯一の正本） |
| `runner/bitget_adapter.py` | Bitget SDKラッパー |
| `config/bitget_keys.json` | APIキー（機密） |
| `cat/indicators.py` / `cat/const.py` | 指標計算・定数 |

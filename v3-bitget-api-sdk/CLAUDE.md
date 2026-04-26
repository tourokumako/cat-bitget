# CLAUDE.md — cat-bitget（開発中）

---

## ⛔ 提案禁止リスト（NEVER SUGGEST AGAIN）← 提案前に必ず確認

以下は検証済みの失敗・却下済み方針。**理由を問わず再提案しない。**

- **ポジションサイズ増加でスケール（0.024→0.12BTC）**：Entry/Exitロジックが未完成の状態でのサイズ増加は論外。提案禁止。
- **既存Priority(P1/P2/P3/P4/P21/P22/P23/P24)の 1m足回帰**：1m MACD はエッジゼロ確認済み・手数料負け確定。これら既存Priorityを 1m に戻す提案は禁止。
  ※ 新規Priority・新規シグナルでは 1m/3m/15m/1h 等の他足検証は許容（手数料計算・エッジ証明を伴うこと）
- **マルチシンボル化（ETH/SOL等の追加）**：ユーザーが明示的に却下。提案禁止。
- **ポジションサイズを「固定値」として計算・提案する**：0.024 BTC は現在の検証サイズであり固定ではない。上限0.12 BTC/trade内でPriority別に自由に配分できる（例: P23=0.06、P3=0.01）。$60/day計算時はこの配分最適化を織り込む。

---

## ⛔ 絶対禁止（NEVER）

- `ALLOW_LIVE_ORDERS=False` を True に変更しない（ユーザーのみ）
- `paper_trading` フラグをコードで変更しない
- `config/bitget_keys.json` の中身をログ・画面に出力しない
- `runner/replay_csv.py` / `runner/run_once_v9.py` をユーザー確認なしに実行しない

---

## AI行動ルール（MUST）

### 目標達成へのコミットメント
- 目標$60/dayに対して、あらゆる手段を講じてコミットする

### 提案を出す前に毎回・例外なく実行すること

```
[提案前チェック]
1. 上記「提案禁止リスト」に該当しないか → 該当すれば提案しない
2. 直近のユーザー指示と矛盾しないか   → 矛盾すれば提案しない
3. 設計思想（Priority特性別最適化・5m足を現行標準とする）と整合しているか → 非整合なら提案しない
   ※ 5m以外の足を採用する場合は「5mでは目標到達不可」のデータ根拠と手数料計算を添えること
```

**このチェックを省略した提案は出さない。チェック通過を確認してから提案する。**

### その他の行動ルール

- 変更前に差分を提示して GO を待つ
- 実行コマンドは「何を実行するか・期待する挙動・成功条件」をセットで提示
- コマンド先頭に必ず `echo "=====🚀 RUN START $(date) ====="` を付ける
- **1ターン1変更（L-5）**

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
| `bitget-python-sdk-api/.claude/memory/signal_ledger.md` | **シグナル候補・レジーム×方向マッピング・検証実績の唯一の正本**（51候補マスター） |
| `bitget-python-sdk-api/.claude/memory/lessons.md` | 過去の失敗・再発防止（V9含む） |
| `bitget-python-sdk-api/.claude/memory/project_v9_progress.md` | V9実装進捗（参照用） |

---

## 現在の方針

### レジーム切り替え方針（2026-04-21 確定）
- **日足MA70を基準に downtrend / range / uptrend の3レジームに切り替える**
- 各レジームに方向性の合う Priority を割り当て、個別に最適化・設計する
- 現状 Priority は「方向性が近いもの」をスタート地点として育てる
- 最終検証: 365d Replay で GO/NO（ここでの再チューニング禁止）

### 実装方針
V9シグナルをベースに、**Priority特性別に最適化**する。
- **現行標準は 5m足**。既存Priority(P1〜P4/P21〜P24)の 1m足回帰は禁止（エッジゼロ確認済み）
- 新規Priority・新規シグナルでは、5m が誤検知過多で目標到達を妨げる場合に限り
  他足（1m除く・3m/15m/1h 等）を検証可。採用条件は ① 手数料計算が正 ② 5m同条件で
  劣ることをデータで示す ③ analyze_signals.py で干渉率 < 0.3
- 各Priority: 型は事前定義せず検証結果から決定する（スキャル/スイング分類は廃止）
- P2: TP=0.0006（現在の検証値）/ P4/P22/P23/P24: TP幅・保有時間はPriority単位で検証して最適化
- P1/P21: 5m足・MACD(12,26,9)クロス・TRAIL_EXIT設計

詳細な検証結果・パラメータ・次のタスクは WORKFLOW.md を参照。

---

## このBOTの存在意義

人間が24時間監視・執行できない相場を、ルール通りに動き続けることで稼ぐ。
- 感情に左右されない規律ある取引
- 24時間365日の自動監視・自動執行
- 人間が張り付かなくてよい時間コストの削減

---

## 目標

| 指標 | 基準 |
|------|------|
| 本番 NET 目標 | **$60/day** |
| 手数料コスト想定 | 100件/日 × $0.60 = $60/day |
| 必要 GROSS | **$120/day 以上** |

---

## TP_PCT提案時の必須チェック（L-40）

TP_PCTを提案・変更する前に**必ずこの計算を先に実施・提示する**：

```
position_usd = POSITION_SIZE_BTC × 現在価格
往復fee      = position_usd × FEE_RATE_MAKER × 2
TP gross     = position_usd × TP_PCT
net per TP   = TP gross - 往復fee  ← これが正でないと提案しない
```

**「戦略全体のNETがマイナス」≠「手数料負け」**
TIME_EXIT / SL損失 と 手数料 を必ず切り分けて報告する。

---

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `runner/run_once_v9.py` | 実行エンジン |
| `runner/replay_csv.py` | 過去CSV検証エンジン |
| `strategies/cat_v9_decider.py` | エントリー判断（P1/P2/P4/P21/P22/P23） |
| `config/cat_params_v9.json` | パラメータ（唯一の正本） |
| `runner/bitget_adapter.py` | Bitget SDKラッパー |
| `config/bitget_keys.json` | APIキー（機密） |
| `cat/indicators.py` / `cat/const.py` | 指標計算・定数 |

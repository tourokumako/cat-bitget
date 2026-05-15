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

- **【最大級・Prime Directive】本番運用で再現不可能な実装の使用禁止**
  バックテスト・学習・Replay・PnL計算・採用判定など、すべての工程において、本番運用の推論時点 t で因果的に取得不可能な値を計算式・判定式・採用ロジックに使用することを禁止する。
  使えない例: MFE/MAE等の保有期間中最大値、K本後の値、期間全体集計値、test 結果を見て決めたパラメータ
  使える例: shift(1)で当該時点を除外した過去集計、過去発生イベントのフラグ、train だけで決めた定数
  判定基準と詳細: `.claude/rules/false_positive_incident_policy.md` §0-1
  違反は同 §2 類型 A として最重大インシデント扱い。
- **【最大級・第二絶対規定】ポジション上限 0.12 BTC 合計厳守**
  任意の時点 t で保有中の全ポジションの合計 BTC サイズが 0.12 BTC を超えてはならない。1 ポジあたりではなく合計上限。
  各ポジの個別サイズは combo 別・予測強度別で柔軟に配分してよい（例: 強い combo に 0.04 BTC、弱い combo に 0.01 BTC）。合計が 0.12 BTC 以内であることのみが絶対制約。
  実装は全エントリー時点で `sum(active_position_btc) ≤ 0.12` を verify する義務を負う。
  違反は `.claude/rules/false_positive_incident_policy.md` §2 類型 H として最重大インシデント扱い。
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

### 作業完了報告の必須3点（2026-05-08 追加）

ファイル出力で完結する作業は、以下3点を全部チャットに出して初めて完了とする:

1. **完了フラグとファイル名**
2. **結果中身のサマリー**
   - 主要数値・上位 5-10 件を表またはリストで
   - 集計結果は次元（軸/カテゴリ/N窓 等）を保持して提示
3. **結果ファイル提示**（クリック可能なリンクで navigable に）

「ファイルに書いた」だけでは報告完了とみなさない。
チャット側に結果中身が届いて初めて「報告完了」とする。

### セッション終了時に必ず行うこと（順番通りに）

1. **`lessons_active.md` を更新する**
   - このセッションで発見した失敗・教訓を L-XX 形式で追記する
   - 「同じミスを次セッションで繰り返さないか？」を自問してから書く
   - パス: `bitget-python-sdk-api/.claude/memory/lessons_active.md`（直近36件・現役）
   - 古いものは `lessons_archive.md`（L-102以前・参照用）。active が約40件超えたら最古を archive に移送する

2. **`WORKFLOW.md` を更新する**
   - 現在の設計・パラメータ・Replay結果・次のタスクを最新状態に書き直す
   - パス: `bitget-python-sdk-api/WORKFLOW.md`

3. **Priority 再構築フェーズの進捗を WORKFLOW.md に反映する**
   - ML pipeline Phase 0 (ラベル再生成) / Phase 1〜3 (LightGBM 学習+ハイパラ) / Phase 4 (クラスタリング+Exit) / Phase 5 (Replay) / Phase 6 (本テスト) / Phase 7 (Bot 統合) のどこまで進んだか
   - 残課題・次セッション着手項目
   - `regime_research.md` / `priority_rebuild.md` (旧 A-1〜D framework) は凍結中なので更新不要

**⛔ セッション終了前に以下を必ずチャットに出力する（省略禁止）:**
```
セッション終了チェック:
[ ] lessons_active.md 更新完了
[ ] WORKFLOW.md 更新完了（Priority 再構築フェーズの進捗反映）
```
→ 2つ全て [ ] に ✓ が入るまでセッション終了を宣言しない。

4. **Git コミットする**（ユーザーの明示 OK なしに commit しない）

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
| `bitget-python-sdk-api/WORKFLOW.md` | 現在の状態・次のタスク（**唯一の正本**・現在は **⛔ Phase 1〜7-a leak で無効化**警告ブロックあり）|
| `~/.claude/projects/.../memory/feedback_ml_leak_mandatory_check.md` | **【最重要】ML 系作業前の leak 4 点チェック必須** (L-179・2026-05-13 fractal j±2 未来参照事案) |
| `bitget-python-sdk-api/results/priority_rebuild/leak_incident_20260513.md` | Leak 全 14 件ミス記録 + 防止策 (新セッション再開前に必読) |
| `bitget-python-sdk-api/.claude/memory/lessons_active.md` | 過去の失敗・再発防止（**L-179 最新 + L-159〜L-166 重点** + 常時参照） |
| `bitget-python-sdk-api/.claude/memory/lessons_archive.md` | L-102以前のアーカイブ（必要時のみ） |
| `bitget-python-sdk-api/.claude/rules/exchange_spec.md` | Bitget USDT-FUTURES スペック正本 (手数料・最小単位・Funding時刻・メンテ時間) |
| `bitget-python-sdk-api/.claude/memory/signal_ledger.md` | シグナル候補・検証実績（参考・regime マッピングは凍結中） |
| `bitget-python-sdk-api/.claude/memory/regime_research.md` | 🧊 **凍結中**（素材として参照のみ・新規調査禁止） |
| `bitget-python-sdk-api/.claude/rules/false_positive_incident_policy.md` | **【最重大・CC/Web Claude 共通正本】虚偽達成・虚偽報告インシデント方針** — 類型 A〜G・発見時強制手順・防止関所 7 つ（2026-05-15 制定） |
| `bitget-python-sdk-api/.claude/rules/web_claude_self_check.md` | Web Claude 読了ゲート・チェック A/B/C（新版 140 行・audit#12/14 反映・2026-05-15 更新） |

---

## 現在の方針（2026-05-11 大方針転換）

### Priority ゼロから再構築 — MTF × 1,432 指標で Entry 規則を最適化

**旧方針（凍結）**: 日足 MA70 ベース regime 判定 → 既存 Priority(P1-P24) 振り分け

**新方針**:
- regime 判定研究は**凍結**（v14 56% / stage3 33% の精度天井に対し $60/day 到達への寄与が見えない）
- 蓄積した素材（1,432 指標列・k=2 探索フレーム）を **Priority Entry 規則の最適化**に転用
- 既存 P1/P2/P4/P21/P23/P24 は**改修ではなく解体・再設計**
- 5m bar × 全 1,432 指標 × 未来 MFE/MAE で Entry 規則を網羅探索

### ML pipeline フローの骨格（Phase 0 〜 7・2026-05-13 改訂）

> ⚠️ 旧 framework「段階 A-1〜D」は 2026-05-13 ML pipeline 切替で廃止。
> A-1 → Phase 0 統合 / A-2 (k=2 探索) は ML 不合格時の保険 (cc_ml_design_spec §0) / A-3〜D → Phase 1〜7 に再編。
> 2026-05-13 leak (fractal j±2 未来参照) 修正完了・Phase 1〜7-a 旧成果は無効・**Phase 0 から再開**。

- **Phase 0**: ラベル再生成 (5y × 5m × 1,432 指標 × 未来 MFE/MAE・leak フリー)
- **Phase 1**: LightGBM × 16 ラベル × デフォルトハイパラ
- **Phase 2**: 精度判定 (仮テスト 2025 月次 $500 以上か)
- **Phase 3-a/3-b**: ハイパラ調整 (K 窓別 num_leaves)
- **Phase 4-a**: k-means クラスタリング (Entry 性質分類)
- **Phase 4-b**: Exit 設計 (cluster × K × side 最適 Exit・データ駆動)
- **Phase 5/5-b/5-c**: 365d Replay (cap なし → FIFO cap → 質駆動 cap)
- **Phase 5-d**: ポジションサイズ正解版 (0.12 BTC = 合計上限) で再計算
- **Phase 5-e**: Funding Rate 控除 (8h 毎・0.01% 概算)
- **Phase 6-a/6-b**: 本テスト 2026 Q1 (月次 NET ≥ $1,900 全月クリア判定)
- **Phase 7-a〜e**: Bot 統合 (推論再現性 → ML Decider → run_once_ml → デモ → 本番)

詳細・現在のステップは [WORKFLOW.md](bitget-python-sdk-api/WORKFLOW.md) と [cc_ml_design_spec.md](bitget-python-sdk-api/cc_ml_design_spec.md) を参照。

### 実装方針

- **現行標準は 5m足**。1m 足回帰は禁止（エッジゼロ確認済み）
- ポジションサイズ上限 **合計 0.12 BTC**（1 ポジションあたりではなく合計上限・cap=N なら 1 pos = 0.12/N BTC）
- 特徴量は 1,432 指標全部投入 (事前絞り込み禁止)
- Exit 設計は Phase 4-b で cluster × K × side ごとデータ駆動 (Phase 4-b 実測で time_exit N=K×2 bar が支配解だったが leak 修正後再検証)

詳細な検証結果・パラメータ・次のタスクは [WORKFLOW.md](bitget-python-sdk-api/WORKFLOW.md) を参照。

---

## このBOTの存在意義

人間が24時間監視・執行できない相場を、ルール通りに動き続けることで稼ぐ。
- 感情に左右されない規律ある取引
- 24時間365日の自動監視・自動執行
- 人間が張り付かなくてよい時間コストの削減

---

## 目標（一次ソース: MEMORY/project_goal.md）

| 項目 | 値 |
|------|------|
| 合格ライン（本番投入可判定）| **月次 NET ≥ $1,900/月** |
| デイリー参考値 | $60/day（月次÷30の目安・日次絶対下限ではない）|
| 凍結ベースライン | 月次平均 $370/月（$12.34/day × 30）|
| 設計姿勢 | 合格ライン超えマージン厚く・ジャスト達成設計禁止 |

### 禁止する誤読
- ❌ 「日次 $60 を 1 日も下回らない」（変動相場で物理不可能）
- ❌ 「$60/day = 100 trade/日」（件数は目標ではない）
- ❌ 旧記載「$120/day」「15日累計 $1,800」（廃止）

### ML pipeline Phase 5/6-b Replay 合格条件
- 365d Replay で **全 12 ヶ月**が月次 NET ≥ $1,900/月 (Phase 5 = 仮テスト 2025)
- 本テスト 2026 Q1 (Phase 6-b) で全 3 ヶ月が月次 NET ≥ $1,900/月
- 単月でも未達なら不合格
- 通算 NET だけで判定しない

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

# CLAUDE.md — cat-bitget（開発中）

---

## ⛔ 提案禁止リスト（NEVER SUGGEST AGAIN）← 提案前に必ず確認

以下は検証済みの失敗・却下済み方針。**理由を問わず再提案しない。**

- **ポジションサイズ増加でスケール（0.024→0.12BTC）**：Entry/Exitロジックが未完成の状態でのサイズ増加は論外。提案禁止。
- **既存Priority(P1/P2/P3/P4/P21/P22/P23/P24)の 1m足回帰**：1m MACD はエッジゼロ確認済み・手数料負け確定（これは ML 転向前の手動 Priority の話）。
  ※ **ML 学習で 1m/3m が有効と実証されれば有効化可**（2026-06-02 まこさん・撤回）。旧「1m禁止」はブランケットでなく、エッジ証明＋手数料計算を伴えば 1m/3m/15m/1h の検証・採用は可。
- **マルチシンボル化（ETH/SOL等の追加）**：ユーザーが明示的に却下。提案禁止。
- **ポジションサイズを「固定値」として計算・提案する**：0.024 BTC は現在の検証サイズであり固定ではない。上限0.12 BTC/trade内でPriority別に自由に配分できる（例: P23=0.06、P3=0.01）。月次 NET ≥ $1,900 全月クリア達成計算時はこの配分最適化を織り込む。

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
- まこさんが掲げた目標（**月次 NET ≥ $1,900 全月クリア達成**）に対して、あらゆる手段を尽くして全力でコミットし、目標達成すること（cc_role.md §1.0 と整合・$60/day はデイリー参考値・判定基準ではない）
- 「あらゆる手段」: 自分の知見だけに頼らない / web 検索・WebFetch・業界カタログ・学術文献・OSS 実装・最新研究を能動的に活用 / 過去事例調査 / 監査経路 (ChatGPT 等独立第三者 AI) を遠慮なく使う / 知らない領域は「知らない」と正直に言って調べる
- 「全力でコミット」: 目標を下げる方向の提案をしない / 「現実的な落とし所」を出す前に目標達成案を最低 1 つ出す / 達成への思考に集中し、達成できない理由の整理に時間を使わない

### アジャイル開発で進める（新規戦略＝MVPベース→反復改善・最重要・2026-06-13・L-278）

- 新規戦略は「動く最小限のベース(MVP)」をまず作り、**反復で作り込む**。① ベース v1 を作る → ② 連続モード `score.py` で月次 net の地面を出す（一発の○×でなく数字）→ ③ 改善レバーを**1つずつ**入れ、地面を超えた分だけ残す（ratchet＝継続的改善）。**動くベースは捨てない。**
- ⛔ **1回の判定（per-trade or 1回の score）で「no-edge → 破棄」と新規戦略ごと切り捨てない**（ウォーターフォール＝一発で正解を当て外れたら捨てる癖・L-278）。素朴版が一発で黒字にならないのは当然＝出発点。標準戦略（レンジ/逆張り/グリッド）は「エッジが有るか」でなく「**黒字に作れるか＝作り方**」で取り組む（L-277）。
- 詳細・例外（leak/cap/軸1ボラ逃げ/degenerate/配管確認の捨て駒は即破棄可）は cat_requirements §8.4 アジャイル節。

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

3. **ML pipeline Phase 進捗を WORKFLOW.md に反映する** (旧表記「Priority 再構築フェーズ」)
   - ML pipeline Phase 0 (ラベル再生成 14 ラベル独立) / Phase 1〜3 (LightGBM 学習+ハイパラ) / Phase 4 (クラスタリング+Exit) / Phase 5 (Replay) / Phase 6 (本テスト) / Phase 7 (Bot 統合) のどこまで進んだか
   - 残課題・次セッション着手項目
   - `regime_research.md` / `priority_rebuild.md` (旧 A-1〜D framework) は凍結中なので更新不要

4. **`ml_pipeline_execlog.md` 実行ログ + 現在地を更新する**（工程の実装・実測・設計修正があったセッションのみ）
   - 実行ログに時系列 1 エントリ追加：**実行内容 + 実測値 + 決定/修正 + リンク**（生データは書かず lessons L-XXX / results/*/summary.json へのリンクで・肥大化防止）
   - **設計 §6 (baseline) が実装で覆ったら、§6 本文を直す前にまず execlog に「設計 X → 実測 Y → 修正 Z」を経緯記録**（= 設計通りにやらなかった理由を必ず追える状態に）
   - execlog 末尾の「現在地 + 次セッション着手」を最新化（= 新セッションが最初に読む正本・WORKFLOW 改訂N と同期）
   - パス: `bitget-python-sdk-api/.claude/memory/ml_pipeline_execlog.md`
   - **3 層分離 (2026-05-30)**：`ml_pipeline_baseline_v1.md` §6=設計の正本 / §7=文書改訂履歴（WebSearch hook 対象）｜ `ml_pipeline_execlog.md`=実装の実行・実測・現在地ログ + フロー意図（hook 対象外・新セッション最初に読む）
   - **【L-239 実行可能テンプレ強制】「次セッション着手」は必ず以下5列の表で書く**（曖昧記述＝ずれ＝トークン浪費を物理的に防ぐ）:
     | 優先 | 使う/直すファイル(パス) | 入力データ(パス) | 存在✅ | 最初の一手(具体コマンド/関数) | 完了条件 |
     - 「パス」「最初の一手」「完了条件」が埋まっていないタスクは**引き継ぎ未完成**（commit/終了を宣言しない）
     - 「存在✅」は実際に `ls` で確認した結果を書く（記憶ベース禁止・今日の「学習済み」誤断定の再発防止）
     - 思い込み（例: 「当てはめるだけ」）でなく、スクリプトが再実行で済むか改修が要るかまで書く
   - **【L-239 自動検証】SessionStart hook `verify_handoff_paths.sh` が開始時にこの表のパスを ls チェックし ✅/❌ 表示**（ずれ・古い参照を機械的に検出）

**⛔ セッション終了前に以下を必ずチャットに出力する（省略禁止）:**
```
セッション終了チェック:
[ ] .claude/state/next_step.md 上書き更新完了（次セッションの起点・SessionStart 表示・必須＝①本筋 ②今セッションの確定=ledger E番号参照 ③やってはいけないこと ④数字の出典。毎回上書き=最新1枚。ledger 編集後は pdca_gate が物理強制・cat_requirements §8.3）
[ ] lessons_active.md 更新完了
[ ] WORKFLOW.md 更新完了（現在地5行・改訂N active）
[ ] ml_pipeline_execlog.md（旧8工程フローの記録＝廃止・参照のみ＝原則「該当なし」）
```
→ 全て [ ] に ✓ が入るまでセッション終了を宣言しない。

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

## セッション開始時に必ず読むこと (3 層構造・2026-05-22 改訂22)

> ⚠️ **L-200 / L-204 警告**: system reminder で auto-load されるファイル (本 CLAUDE.md / WORKFLOW.md / cc_role.md / web_claude_self_check.md / false_positive_incident_policy.md / exchange_spec.md / phase_compliance_checklist.md) も、**Read tool で全文 view + 機械的証跡 (wc -l + 0/25/50/75/100% 引用 + 1 行要約)** を Step 0 で取り直すこと。「system reminder で表示されている = 読了済」と内部処理する違反は L-200 / L-204 で禁止。

### Layer 1 — 毎セッション必読

> **⚠️【2026-06-12 スリム化・cat_requirements §8.1 が正本＝下表に優先】** 毎セッション Read 強制（読了ゲート）は **3本のみ＝① cat_requirements.md ② WORKFLOW.md ③ ledger.md**（require_read_before_work.sh / reset_read_log.sh と一致）。下の旧10本テーブルは **8工程フロー時代の名残・参照のみ**（phase_flow_v4 / ml_pipeline_execlog / ml_pipeline_baseline_v1 は旧フロー＝廃止／technical・industry KB はトレード議論時のみ Layer 2 扱い）。**毎セッション全文必読ではない**。設計=strat_v9ml_design、分析手順=analysis_playbook、教訓=lessons_active は必要時に開く。
>
> **【2026-05-26 重大改訂】** `handoff_to_cc_v*` は廃止 (伝言ゲーム化経路の物理排除・L-216)。前セッション引き継ぎは **WORKFLOW.md 改訂N active ブロックに集約**。learning_design_v4.md は phase_flow_v4_with_recovery.md に統合し archive 移動。

> 🧊 下表は旧10本（8工程フロー時代）の履歴。現役の毎セッション必読は上記3本（§8.1）。

| ファイル | 内容 | 取得方法 |
|---------|------|------|
| **`bitget-python-sdk-api/.claude/rules/cat_requirements.md`** | **【最初に読む・要件定義書】CC の立ち位置 / 業務 As-Is To-Be / 機能 / 非機能 / ハード制約 14 (H1-H14) / 運用ガイド・全設計は §4.6 に照合** (2026-06-02 新規・SessionStart 強制 cat ①) | Read 全文 |
| `bitget-python-sdk-api/WORKFLOW.md` | 現フェーズ・次のタスク・本セッション完了事項・引き継ぎリソース (改訂N active ブロック・履歴は archive) | Read 全文 |
| `v3-bitget-api-sdk/CLAUDE.md` (本ファイル) | 提案禁止・目標・必読リスト・セッション終了チェック | Read 全文 |
| `bitget-python-sdk-api/.claude/memory/phase_flow_v4_with_recovery.md` | **ML 学習フロー正本** (Phase 0〜7 / 6 案並列 + Walk-forward Purged K-Fold 5 fold + DSR + 5 指標) | Read 全文 |
| `bitget-python-sdk-api/.claude/memory/priority_v9_trade_logic_analysis.md` | **旧 Priority v9 トレードロジック構造分析** (= cat-bitget 唯一の実利資産・最低スタートライン・cat_v9_decider.py 823 行 + cat_params_v9.json 169 行を CC が構造分析・2026-05-26 v2 で Replay 365 日データ起点で書き直し済) ⚠️ [[feedback_cat_v9_no_modification]] = 改造対象ではない | Read 全文 |
| **`bitget-python-sdk-api/.claude/memory/ml_pipeline_execlog.md`** | **【新セッション最初に読む】実行ログ + 現在地 + 次セッション着手 + フロー意図** (= 旧 baseline §8 を分離・2026-05-30・経緯理解の起点・誤解防止) | Read 全文 |
| `bitget-python-sdk-api/.claude/memory/ml_pipeline_baseline_v1.md` | **ML pipeline 設計の正本** (= §1-§7・工程の「どう作るか」・WebSearch hook 対象・§8 実行ログは execlog.md に分離) | Read 全文 |
| `bitget-python-sdk-api/.claude/memory/technical_analysis_knowledge_base.md` | **テクニカル辞典 + 閾値設計論** (1691 行・§A-D 個別指標 + §I 閾値設計論・トレード議論前のインプット必須・2026-05-26 Layer 1 格上げ・L-230) | Read 全文 |
| `bitget-python-sdk-api/.claude/memory/industry_benchmark_knowledge_base.md` | **業界相場 + 5 レバー定量根拠** (420 行・出典 47 件・Phase 別合格基準 PnL 紐付け手法・BTC 5m 業界実証・トレード議論前のインプット必須・2026-05-26 Layer 1 格上げ・L-230) | Read 全文 |
| `bitget-python-sdk-api/.claude/memory/lessons_active.md` **直近 5 件のみ** | 最新教訓・本セッション着手前に読む | Read 先頭 ~300 行のみ |

### Layer 2 — タスク特有 (該当タスク時のみ精読)

| タスク | 読むファイル |
|---|---|
| ML 学習着手 (Phase 1 等) | `cc_ml_design_spec.md` + `~/.claude/projects/.../memory/feedback_ml_leak_mandatory_check.md` + `results/priority_rebuild/leak_incident_20260513.md` (※ learning_design_v4.md は phase_flow_v4 §2/§3 に統合済・原本は `archive/learning_design_v4_20260526.md`) |
| Phase 着手 (各 Phase 共通) | `bitget-python-sdk-api/.claude/rules/phase_compliance_checklist.md` の該当 Phase 行 + `bitget-python-sdk-api/.claude/memory/phase_flow_v4_with_recovery.md` (= Layer 1 必読・ML 学習正本) |
| 重大設計判断・指示書発行・完了報告受領 | `cc_role.md` §1.5/§1.6/§1.7 + `web_claude_self_check.md` チェック A/B/C |
| 取引所スペック引用 | `bitget-python-sdk-api/.claude/rules/exchange_spec.md` (audit#19 確定値) |
| 監査依頼 (`/audit`) | `bitget-python-sdk-api/.claude/rules/auditor_template.md` |
| テクニカル指標・閾値設計判断 | `bitget-python-sdk-api/.claude/memory/technical_analysis_knowledge_base.md` (本プロジェクト製テクニカル辞典・§A-D 個別 + §I 閾値設計論・1691 行) |
| **業界相場・戦略レバー値見積もり (= 数値根拠)** (2026-05-26 新規) | `bitget-python-sdk-api/.claude/memory/industry_benchmark_knowledge_base.md` (業界相場・経験則ナレッジ・5 レバー定量根拠 + Phase 別合格基準 PnL 紐付け手法 + BTC 5m 業界実証・WebSearch 18 件統合) |
| 23 軸深掘り (ML 設計判断時) | `bitget-python-sdk-api/.claude/memory/CAT−指標マトリックス - 一覧.csv` (164 KB・古い情報混在・参照のみ・23 軸構成要素カタログ) |
| シグナル設計 | `bitget-python-sdk-api/.claude/memory/signal_ledger.md` (regime マッピングは凍結) |

### Layer 3 — リファレンス (検索 + 引用 verify)

| ファイル | 用途 |
|---|---|
| `bitget-python-sdk-api/.claude/rules/false_positive_incident_policy.md` | 類型 A-H・関所 A-G・§0-1 Prime Directive / §0-2 0.12 BTC 合計厳守 (本ファイル §⛔ にダイジェスト統合済・引用時のみ本体 verify) |
| `bitget-python-sdk-api/.claude/memory/lessons_archive.md` | 古い lessons archive (必要時のみ・Layer 1 で L-204〜L-200 が読了済なら基本不要) |
| `bitget-python-sdk-api/.claude/rules/web_claude_role.md` | Web Claude (機械照合担当・降格) 冒頭注記のみ参照・本体は archive 参照 |
| `bitget-python-sdk-api/.claude/memory/regime_research.md` | 🧊 凍結中・素材参照のみ |
| `bitget-python-sdk-api/.claude/memory/seven_step_framework.md` | ⛔ 破綻判定済 (= 2026-05-26 L-230)・参照用 (cat-bitget 制約矛盾発覚) |
| `bitget-python-sdk-api/.claude/memory/chatgpt_seven_step_origin.md` | ⛔ 破綻判定済 (= 2026-05-26 L-230)・参照用 (= 7 工程フレームの ChatGPT 出典) |

---

## 現在の方針（2026-05-11 大方針転換）

### Priority ゼロから再構築 — MTF × 1,432 指標で Entry 規則を最適化

**旧方針（凍結）**: 日足 MA70 ベース regime 判定 → 既存 Priority(P1-P24) 振り分け

**新方針**:
- regime 判定研究は**凍結**（v14 56% / stage3 33% の精度天井に対し合格ライン月次 NET ≥ $1,900 全月クリア達成への寄与が見えない）
- 蓄積した素材（1,432 指標列・k=2 探索フレーム）を **Priority Entry 規則の最適化**に転用
- 既存 P1/P2/P4/P21/P23/P24 は**改修ではなく解体・再設計**
- 5m bar × 全 1,432 指標 × 未来 MFE/MAE で Entry 規則を網羅探索

### ML pipeline フローの骨格（Phase 0 〜 7・2026-05-13 改訂）

> ⚠️ 旧 framework「段階 A-1〜D」は 2026-05-13 ML pipeline 切替で廃止。
> A-1 → Phase 0 統合 / A-2 (k=2 探索) は ML 不合格時の保険 (cc_ml_design_spec §0) / A-3〜D → Phase 1〜7 に再編。
> 2026-05-13 leak (fractal j±2 未来参照) 修正完了・Phase 1〜7-a 旧成果は無効・**Phase 0 から再開**。

- **Phase 0**: ラベル再生成 (5y × 5m × 1,432 指標 × 未来 MFE/MAE・leak フリー)
- **Phase 1**: LightGBM × **14 ラベル独立学習** (対称性活用・LONG_MFE/MAE × K=7・SHORT は Phase 5 で流用) × デフォルトハイパラ
- **Phase 2**: 精度判定 (仮テスト 2025 月次 NET ≥ $1,900 全月クリア)
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

- **現行標準は 5m足**。1m/3m は **ML 学習で有効と実証されれば有効化可**（旧「1m足回帰禁止」は ML 転向前ルールにつき撤回・2026-06-02 まこさん・採用は net 実証で判断）
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

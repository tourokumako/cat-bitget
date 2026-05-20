# handoff_to_web_claude_v14_session_20260520

セッション: 2026-05-20 (Phase 0 v3 完了報告レビュー + L-196 緊急訂正)
作成者: Web Claude
保存先: `.claude/instructions/handoff_to_web_claude_v14_session_20260520.md`

---

## §0 前提認識 (v12 §0 + v13 §0 を継承・必読)

### §0.1 23 軸 First Principles
詳細は `web_claude_role.md` §1.6 (431 行) を全文 view。

### §0.2 手動 Priority の位置づけ
詳細は `web_claude_role.md` §1.7 を全文 view。

### §0.3 Web Claude のデザイン責任
詳細は `web_claude_role.md` §1.5 を全文 view。

### §0.4 前セッション (v12/v13) で陥った誤解パターン
v12 §0.4 (全 12 件) + v13 §0.4 (L-194 / L-195) を継承。本セッション (v14) で新規追加: **L-196 (Claude 想定値が正本化されて世代間伝播)**。

### §0.5 (本セッションで判明) 読了ゲート違反の連鎖を起こすな
v14 開始直後 (handoff v12 受領後の初動) で「読了ゲート起動」と書きながら、WORKFLOW.md は部分 view のみ・CLAUDE.md / cc_ml_design_spec.md / false_positive_incident_policy.md / lessons_active.md 未読のままレビュー突入 → まこさんから「ちゃんと読め」と指摘されて再起動 (false_positive §3 #7 同型再発)。

**対応**: 新セッション開始時に必ず handoff §0 + コア 5 本 (WORKFLOW.md / CLAUDE.md / cc_ml_design_spec.md / 最新 handoff / lessons_active.md) を機械的証跡 (wc -l + 0/25/50/75/100% 引用 + 1 行要約) 付きで全文 view する。「読了ゲート通過: 2026-MM-DD」宣言を出すまでレビュー・指示書発行に進まない。

### §0.6 (本セッションで判明) completion report の文字を信用するな
「公式 source の CSV/JSON 10 ファイル」を実物 view せず・report の文字だけで Phase 0 完了レビュー「合格項目 7 点」を判定した事案発生。まこさんから「これは確認しなくていいの?」と指摘されてインシデント自覚。

**対応**: レビュー着手時点で公式 source パスの一覧抽出 → `ls` で物理アクセス可否確認 → アクセス不可なら最初にまこさんに同期依頼 (判定出力前に物理 view 環境を整える)。

---

## §1 本セッション確定事項

### §1.1 Bitget USDT-M futures 仕様 (出典別状態)

| 項目 | 値 | 出典 | 状態 |
|---|---|---|---|
| Maker fee 適用値 | 0.014% (0.00014) | まこさん発注画面 (2026-05-20 スクショ) | ✅ verify 済 |
| Taker fee 適用値 | 0.042% (0.00042) | 同上 | ✅ verify 済 |
| Maker fee 標準値 | 0.02% (0.0002) | ⚠️ 出典なし・Claude 想定値 | ⚠️ audit#19 対象 |
| Taker fee 標準値 | 0.06% (0.0006) | ⚠️ 出典なし・Claude 想定値 | ⚠️ audit#19 対象 |
| 最小注文 / 最小注文額 / Tick / 最大レバ / マージンモード / 最大同時保有 | 既存記述 (0.0001 / 5USDT / 0.1 / 125x / isolated / 200) | API response 例の保存未実施 | ⚠️ audit#19 対象 |
| Funding 8h 間隔 | 8 時間ごと | 公式ガイド (2026-01-08) | ✅ verify 済 |
| Funding 0.01% rate | 0.01%/8h | phase_compliance L13 暫定値・出典なし | ⚠️ audit#19 対象 |
| 取引時間 | **24/7 (定期メンテなし)** | 公式ガイド「中断のない年中無休の取引」(Bitget 株式無期限先物完全ガイド・2026-01-08・2026-05-20 まこさん確認) | ✅ verify 済 |
| 定期メンテ (旧記述) | 「火/水/木 05:00-08:00 UTC」 | ⛔ Claude 想定値・削除済 | ⛔ L-196 |

### §1.2 Phase 0 v3 メンテ flag の扱い (2026-05-20 確定)

- parquet 内 `is_maintenance` 列は **残置** (再生成コスト 2h40m 回避)
- ただし Phase 5 Replay 以降では **使わない** (Bitget は 24/7 取引・L-196 参照)
- Phase 5 設計時に「メンテ flag 不使用」を明示する

### §1.3 本番再現性 7 項目 (2026-05-20 訂正版)

| # | 項目 | 状態 |
|---|---|---|
| 1 | 最小注文 0.0001 BTC | ⚠️ API verify 要 (audit#19) |
| 2 | 最小注文額 5 USDT | ⚠️ API verify 要 |
| 3 | Tick 0.1 USDT | ⚠️ API verify 要 |
| 4 | Maker 指値 TTL 3 本 + 同一 side pending 禁止 | 既存 |
| 5 | SL は add_count ≥ 2 のみ | 既存 |
| 6 | **メンテ = なし (24/7 取引)** | ✅ 公式ガイド確認済 |
| 7 | Maker 剥落 stress: 適用 0.014% ✅ + **⚠️ 想定 0.02% (要 verify)** | 適用値 ✅ / 剥落値 ⚠️ audit#19 |

### §1.4 価格非依存性 6 項目 (Phase 0 適用済)

v13 §1.6 継承・変更なし。

### §1.5 23 軸 ML 学習デザイン v3

v12 §1.1 表継承・変更なし。

---

## §2 本セッション commit (緊急訂正タスク)

| commit | 内容 |
|---|---|
| 2026-05-20 緊急訂正 | exchange_spec.md L9-10 ⚠️ マーク + L35 24/7 化 + 出典項目別表化 |
| 同上 | web_claude_self_check.md L99-106 本番再現性 #6/#7 訂正 + L208 見落とし #11 追加 |
| 同上 | lessons_active.md L-196 新規追加 + ヘッダ L-196〜L-103 更新 |
| 同上 | handoff v12 §1.6 / §4.1 + v13 §1.7 / §4.1 訂正注記 |
| 同上 | WORKFLOW.md L343 Phase 0 v3 メンテ flag Phase 5 不使用宣言 |
| 同上 | 指示書 + 完了報告 (2026-05-20_exchange_spec_emergency_fix_and_L196*) |

memory ルール 23 (line 26) は Web Claude 側 memory_user_edits で訂正済 (#6 = 24/7 / #7 = ⚠️ 想定値)。

---

## §3 pending tasks (次セッション着手対象・優先順位固定)

### §3.1 優先 1: audit#19 設計・発注

**exchange_spec.md 全項目の体系的 verify**。⚠️ マーク 8 項目を 1 つずつ verify する。

監査経路必須 (Web Claude + CC の 2 者では発見できない構造的問題・false_positive §3 「発見者列を見れば内部 2 者だけで発見できた事例が一件もない」)。

verify 手段:
- Bitget API `GET /api/v2/mix/market/contracts?productType=usdt-futures&symbol=BTCUSDT` 実行 → JSON response 例を保存・commit
- Bitget API `GET funding-history` で過去 30 日実測 → 平均・中央値・p95 を統計化
- まこさん発注画面で Maker/Taker 標準値表示確認 (剥落条件・BGB 非適用時の表示)
- 監査経路 (audit#19) で独立再現

成果物:
- `.claude/instructions/2026-05-2X_audit19_exchange_spec_full_verify.md` (指示書)
- `.claude/audits/2026-05-2X_audit19_exchange_spec_full_verify.md` (監査報告)
- `results/exchange_api/bitget_contracts_btcusdt_20260520.json` (API response 保存)
- `results/exchange_api/bitget_funding_history_30d.csv` (Funding 実測)
- まこさん発注画面スクショ (標準手数料表示時・BGB 非適用時)

### §3.2 優先 2: Phase 0 v3 spec sweep 本体

本セッション当初の目的・L-196 インシデントで中断していたタスク。

修正対象 (本セッション中盤の私の文案・前ターン提示済):

#### cc_ml_design_spec.md 機械的書き換え 9 箇所
- §1.1 L23: 16 → 28 ラベル / §1.1 L25: K={6,12,24,48,96,144,288}
- §1.1 L31-35 ラベル定義: USD 絶対値 → pct 化定義
- §1.1 L37-40 parquet 名 + 行数: pct 版 + 新行数 (394,561 / 105,120 / 25,631)
- §1.2 L44 指標数: 1,432 → 1,462 → 1,414 + Phase -1 参照
- §1.3 L54: 28 ラベル独立モデル (※ 対称性 verify 後にラベル削減判断は Web Claude が別途行う)
- §1.4 L62-66 期間分割表: 新行数 + 期間範囲補正 (起点 23:55・終点 03-30 23:50)
- §1.6 L80-85: 「28 ラベル / 14 組合せ (K=7 × LONG/SHORT)」+ 閾値・重み再評価は Phase 1 完了後注記
- §5 L204-225 Phase 1/2 = 28 ラベル
- §9 L330-334 データ表

#### WORKFLOW.md 機械的書き換え 4 箇所
- §🔴現在のフェーズ: 2026-05-20 改訂13 として Phase 0 v3 完了・Phase 1 着手判定待ち追加
- L555-561 Phase 0 達成サマリー: Phase 0 v3 追加 (旧 v1 は 🧊 旧注記)
- L569-583 並行タスク改修: Phase 0 v3 追加
- L584-600 次セッション最初: Phase 1 着手判定 (28 ラベル)

#### phase_compliance_checklist.md 3 箇所 + Phase -1 確認
- Phase 0 (L16-28): Phase 0 v3 チェック項目追加
- Phase 1 (L30-38): 16 → 28 ラベル
- Phase -1 セクション: CC 既存追加状況確認・未追加なら本タスクで追加

#### Phase 0 完了報告 / audit report への訂正注記 (本セッション持ち越し)
- `2026-05-19_ml_implementation_phase0_1_completion_phase0.md:56` 「05-07 UTC」に L-196 参照注記
- `2026-05-19_phase0_audit_report.md:105 + 214` 同上注記
- handoff v13 §1.1 表 L32「Step 2 メンテ時間帯除外設計 (火/水/木 05-07 UTC...)」に L-196 参照注記

#### L-196 How to apply 補追 (本セッション持ち越し)
- 私の前ターン文案 8 項目 → CC 実装 3 項目に圧縮されている
- 特に「**出典記述の係り先 (どの項目に係るか) を項目別に明示しないと暗黙範囲拡大が起きる**」が欠落 (今回インシデントの直接原因)
- audit#19 設計時 or 別タスクで 1 項目追補

#### 私のデザイン判断 (spec sweep に書かない・Phase 1 設計時に別途)
- ラベル数 14 採用 (LONG_MFE_pct = SHORT_MAE_pct の数式上の必然) は Phase 0 完了レビュー後 (公式 source の対称性実物 verify 後) に確定

### §3.3 優先 3: Phase 0 完了レビュー本体

spec sweep 完了後 (= レビュー基準が定まってから) 再開。

レビュー観点 (本セッションで判明した未解決事項):
- 行数差分 (起点 07:55 → 23:55 / 終点 03-31 15:50 → 03-30 23:50 = 各 192 bars) の実装上の理由 (おそらく 1d 足 attach の確定遅延)
- K288 max 35-40% の該当日付特定 (BTC が 24h で 35-40% 動いた日 = flash crash / pump 日特定)
- ラベル対称性 (LONG_MFE_pct = SHORT_MAE_pct) の公式 source 実物 verify (`label_stats.csv` + `sample_rows_K*.csv`)
- 異常値スメル ⚠️ 2 件が §0 サマリ「全条件クリア」に反映されていない (不利な情報の末尾配置)
- メンテ flag は §1.2 通り「Phase 5 不使用」前提でレビュー (5.20-5.38% の整合性は架空仕様との一致だったため再評価不要)

### §3.4 優先 4: 次セッション 開始時の読了ゲート完全運用

本セッションの最大の失敗は handoff v12 受領後の読了ゲート違反 (§0.5)。**次セッション開始時に必ず**:
1. v14 (本ファイル) §0 全文 view
2. WORKFLOW.md / CLAUDE.md / cc_ml_design_spec.md / lessons_active.md / web_claude_role.md / web_claude_self_check.md / false_positive_incident_policy.md / exchange_spec.md (8 ファイル) 全文 view
3. 機械的証跡 (wc -l + 0/25/50/75/100% 引用 + 1 行要約) 出力
4. 「読了ゲート通過: 2026-MM-DD」宣言
5. 進む

省略 = false_positive §3 #7 同型再発 (本セッション再発実証あり)。

---

## §4 次セッション Web Claude (私) への警告

### §4.1 設計提案前 3 系列 verify (v12/v13 §4.1 継承・2026-05-20 訂正反映)

設計提案・指示書発行前に必ず以下 3 系列 18 項目を 1 行ずつ提示:
1. 本番再現性 7 項目 (memory ルール 23・self_check L99-107)・**#6 = 24/7・#7 = ⚠️ 想定値 (2026-05-20 訂正)**
2. 価格非依存性 6 項目 (self_check L108-115)
3. 23 軸 First Principles 6 項目 (self_check L116-134)

省略 = 重大インシデント (類型 G + 類型 H 近接)。

### §4.2 デザイン責任を持つ (v12/v13 §4.2 継承)

23 軸から学習対象 / 固定 / 探索 / 優先順位を Web Claude が判断。

### §4.3 手動 Priority への言及禁止 (v12/v13 §4.3 継承)

### §4.4 23 軸の本旨 (v12/v13 §4.4 継承)

### §4.5 「アハ体験」防止 (v12/v13 §4.5 継承)

### §4.6 選択肢併置は不正容認 (v13 §4.6 = L-194 継承)

### §4.7 gitignore 4 行構造 (v13 §4.7 = L-195 継承)

### §4.8 (本セッションで判明・L-196) exchange_spec.md の ⚠️ マーク項目を「verify 済」と扱うな

⚠️ マーク項目 (Maker/Taker 標準値・最小注文系・Funding rate) は audit#19 完了まで「暫定値」扱い。本番再現性 7 項目を「全件 ✅」として書かない・⚠️ マーク項目は「⚠️ 暫定値・要 verify」として併記。「ドキュメントに書いてあったから」は理由にならない (L-180 の外部仕様への拡張)。

### §4.9 (本セッションで判明) Phase 0 完了レビューの公式 source 物理 view 義務

CC が「公式 source: results/...」と書いたパスは、レビュー着手時点で `ls` 物理アクセス可否確認 → アクセス不可なら判定出力前にまこさんに同期依頼。completion report の文字だけで「合格」判定しない (本セッション再発実証あり)。

### §4.10 (本セッションで判明) Phase 0 完了レビューに残存する未確認事項

§3.3 レビュー観点を参照。spec sweep 完了後に再開する際、上記 5 点を必ず実物 verify。

---

## §5 セッション履歴サマリ (本セッション 2026-05-20)

| 時刻概算 | 出来事 |
|---|---|
| 開始 | handoff v12 受領 → 読了ゲート起動宣言だけ出して部分 view でレビュー突入 |
| 序盤 | Phase 0 完了報告レビュー「合格項目 7 点」「条件付き合格」「14 ラベル採用」「アドダム案」を文字だけで判定 |
| 序盤 | まこさんから「公式 source の CSV/JSON 10 ファイルは確認しなくていいの?」指摘 → 物理 view 漏れ自己申告 |
| 中盤 | まこさんから「ちゃんと読め (6 ファイル)」指摘 → 読了ゲート違反 / 類型 G 同型再発 自己申告 → 読了ゲート再通過 (機械的証跡含む) |
| 中盤 | cc_ml_design_spec.md / WORKFLOW.md の旧記述放置発覚 (L-181 違反) → spec sweep 設計開始 |
| 中盤 | spec sweep 修正 4 (メンテ時間統一) でまこさんから「このメンテ情報はどこから取得した?」と問われた |
| 後半 | web 検索 + Bitget 公式ガイドコピペ → 「火/水/木 05-08 UTC」は架空値・Claude セルフ汚染インシデント発覚 (L-196 候補) |
| 後半 | 緊急訂正タスク (A) 設計 → 指示書発行 → CC 完了報告 → レビュー合格 ✅ |
| 後半 | memory ルール 23 訂正 (memory_user_edits replace line 26) |
| 終盤 | handoff v14 作成 (本ファイル) |

---

## §6 改訂履歴

| バージョン | 日付 | 内容 |
|---|---|---|
| v11 | 2026-05-19 (午前) | 連続セッション 1 本目 |
| v12 | 2026-05-19 PM-EVE | 連続セッション 2 本目 (compaction 後) |
| v13 | 2026-05-19 PM-EVE 続き | Phase 0 v3 Step 1-6 完了・Step 3d 着手待ち |
| **v14** | **2026-05-20** | **Phase 0 v3 完了報告レビュー (公式 source 物理 view 漏れインシデント発覚) + L-196 緊急訂正 (Claude セルフ汚染・世代間誤情報伝播) (本ファイル)** |

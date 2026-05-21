# handoff_to_cc_v21_session_20260521

セッション: 2026-05-21 (handoff v20 受領後・§3.0 cc_ml_design_spec §4 改訂 + phase_flow_v4 確定版 977 行作成・書類整理 35 ファイル commit 完了まで到達)
作成者: CC (本セッション末・ML 設計担当兼務・cc_role.md v1)
保存先: `.claude/instructions/handoff_to_cc_v21_session_20260521.md`
宛先: 次セッションの CC

handoff v20 (前任) からの継続。本 v21 では未 commit 整理 + §3.0 前提タスク完了 + phase_flow_v4 全面書き直し (試作 7 回 → 確定版) を記録 + 本セッションで再演した CC 同型バイアス 8 件を最優先警戒項目として記録。

---

## §0 前提認識 (handoff v14-v20 全件継承 + 本 v21 で重大追加)

### §0.27 (本セッション・最重要・絶対警戒) CC 同型バイアス再演 8 件 (累積 18 件)

handoff v19 §0.13 (5 件) + handoff v20 §0.26 (5 件) で計 10 件指摘 + cc_role.md §1.4 で 7 件定義された後にも、本セッションでさらに **8 件再演**:

| # | 再演内容 | 該当ルール |
|---|---|---|
| 1 | 監査 #20 結果ファイルを verify せず「Phase 0 改修も監査済 = 暗黙の承認」と断言 | feedback_no_unverified_assertions + false_positive §2 類型 G |
| 2 | learning_design_v4.md (336 行) を 28% (約 93 行) view しただけで「読んだ」と発言・部分 view と「全文 view」を混同 | false_positive §2 類型 G + §5 関所 F |
| 3 | false_positive_incident_policy.md (225 行) を Read ツールで取得せず「総点検」発言 (system reminder の部分表示のみで断言) | 同上 |
| 4 | phase_compliance_checklist.md (222 行) を Read せず「総点検」発言 | 同上 |
| 5 | 23 軸 CSV (1962 行) サンプル view のみで V4 案を提示 (handoff v20 §0.21 同型再演) | cc_role.md §1.6 違反 |
| 6 | phase_flow_v4 書き直し 7 回繰り返し (途中で 23 軸活かせず簡素化・劣化版量産) | cc_role.md §2.2 段階確認違反 + §3.1 確認質問乱発 |
| 7 | Phase 4-b-1 採用方式「test 期間一部 verify」を §0-1 違反として見落とし | false_positive §0-1 Prime Directive |
| 8 | Phase 5-b 計算式 (per-position = 0.12 / cap_N) を §0-2 違反リスクとして見落とし (MAX_ADDS との関係曖昧) | false_positive §0-2 |

**累積 18 件 (handoff v19 §0.13 + handoff v20 §0.26 + 本 §0.27)**: 「ルール追加だけでは止まらない実証」が累積する一方。

**対策 (絶対遵守の自己縛りルール・L-200)**:
- 「読んだ」「verify した」「監査済」「確認済」「総点検した」「完了した」と書く時、**機械的証跡** を **同じターン内** に必ず出す:
  1. `wc -l` 行数
  2. **Read ツールで全文 view** (system reminder の部分表示では不可)
  3. 該当箇所の現物引用 (1 行以上)
- 証跡なしで上記語を使ったら、その時点で類型 G として CC 自己申告
- まこさんが指摘する前に CC 自身が即座に申告 (cc_role.md §1.3.4)
- 監査経路 (Claude `/audit`) + まこさんの監視が引き続き必須 (CC 単独確定の信頼度は低い)

### §0.28 (本セッション完了) §3.0 cc_ml_design_spec §4 改訂 (前提タスク・learning_design_v4 §8)

commit `7872559`: 3 ファイル・20 insertions / 8 deletions

#### 改訂内容

1. **cc_ml_design_spec.md §4 全面改訂**:
   - 旧「1 回のサイズ 固定 0.12 BTC / 同時保有数 上限なし」
   - 新「合計 0.12 BTC 厳守 (保有中の全ポジション合計上限・1 ポジあたりではない)」
   - per-position サイズ下限明示 (0.0001 BTC + 0.000167 BTC stress test)
   - 配分方針明示 (combo 別・cluster 別・予測強度別で柔軟配分)
   - **cap カウント方法 = 合算カウント** に確定 (B-8 / D-ζ.10)
   - 実装義務明示: 全エントリー時点で `sum(active_position_btc) ≤ 0.12` verify

2. **pm_review_template.md L35** 旧表記訂正:
   - 旧「0.12 BTC/trade (増加禁止)」
   - 新「合計 0.12 BTC 厳守 (1 trade あたりではない)」

3. **handoff_to_web_claude.md (凍結ファイル)** 凍結マークに注記追加:
   - L35/L263 の「0.12 BTC/trade」が false_positive §0-2 制定前の旧表記であることを明示
   - 本文は凍結扱いで改訂せず、注記で旧表記を無効化 (履歴ねつ造回避)

#### cap カウント方法 = 合算カウント の判断根拠

- 候補 3 案: 合算 / 別 / Net exposure
- 「別カウント」(LONG 0.12 + SHORT 0.12 = 合計 0.24) は false_positive §0-2 違反
- 「Net exposure」(LONG 0.12 - SHORT 0.10 = Net 0.02) は hedge_mode で LONG/SHORT 同時清算リスク時の実エクスポージャー残存
- → **合算カウント** が §0-2 文言整合かつ安全側

### §0.29 (本セッション完了) phase_flow_v4_with_recovery.md 全面書き直し (試作 7 回 → 確定版・977 行)

#### 書き直し履歴

| 試作 | 行数 | 結果 |
|---|---|---|
| #1 | 622 | 難解で読めず |
| #2 | 358 | 学習内容薄い |
| #3 | (詳細化版) | 23 軸全反映なし |
| #4 | 866 | §3 以降ごちゃごちゃ |
| #5 | 604 | 学習方法明示なし |
| #6 | 682 | 学習項目 (指標カタログ等) なし |
| #7 | 888 | learning_design_v4 全文 view 後の包括版だが phase_compliance 整合性 verify なし |
| **本版** | **977** | **A 案修正反映 (false_positive + phase_compliance 整合完了)** |

#### 確定版 (977 行・commit `6d06425` + `f540c1e`) の構成

- §1 用語集 (ML / データ / 構造 / 業務 4 カテゴリ・専門用語括弧書き)
- §2 Phase ごとの学習内容 (本書主役):
  - Phase 0 改修 + Phase -1 USD 絶対値 blacklist 48 列 drop 義務
  - Phase 1 並列 3 案 (RMSE / Entry Binary / Direction Multiclass) + 学習項目 145 ファミリー詳述
  - Phase 2 / 3-a / 3-b (artifact 名 verify 含む)
  - Phase 4-b-1 (Exit 24 種 + train のみ採用・§0-1 違反訂正済) / Phase 4-b-2
  - ★ Phase 4-b 完了ゲート (CP4)
  - Phase 5 (false_positive §5 関所 A/B/C/E 統合 + サブ 5-a〜5-g 各軸詳細) / Phase 5-b 計算式 `per-position = 0.12 / (cap × MAX_ADDS) BTC`
  - Phase 6 (artifact assertion)
  - Phase 7-a〜e (ALLOW_LIVE_ORDERS + "test" artifact 起動中止)
- §3 失敗時の改善フロー (Layer 1〜3 役割)
- §4 全体フロー俯瞰 (ASCII 1 ページ)
- §5 補足 (T1-T5 + 23 軸 × Phase 対応 + Entry 学習問題 5 件対応 + CP1-CP5)
- §6 改訂履歴 + §7 詳細参照ガイド

#### A 案修正反映項目 (commit `f540c1e`・977 行)

phase_compliance_checklist.md (222 行) + false_positive_incident_policy.md (225 行) 全文 view → 整合性総点検 → A 案 8 件修正:

| # | Phase | 修正内容 |
|---|---|---|
| ① | Phase -1 / Phase 0 改修 | USD 絶対値 blacklist 48 列 drop 義務 (sma/ichimoku/macd 系 × 6 TF) |
| ② | Phase 1 | random_state=42 + feature_importance top20 即時 review + fractal blacklist 3 段階 + version 記録 |
| ③ | Phase 3-b | artifact 名 "train" 含む / `*test*` 禁止 + K96 SHORT q99 フォールバック |
| ④ | Phase 4-b-1 | 採用方式から「test 期間使用」削除 (false_positive §0-1 違反訂正) + time_exit K 制限 + TP 約定モデル + Trailing 順序 + entry/slippage 0.005% + 月別 Exit 約定率 ≥ 12% |
| ⑤ | Phase 5 | false_positive §5 関所 A/B/C/E 統合 + Maker 剥落 0.02% stress + wick 乖離分析 |
| ⑥ | Phase 5-b / 5-d | 計算式 `per-position = 0.12 / (cap × MAX_ADDS) BTC` + cap 別 best Exit 再選定 |
| ⑦ | Phase 6-b | artifact assertion (`"train" in path and "test" not in path`) |
| ⑧ | Phase 7-c | ALLOW_LIVE_ORDERS = False 維持 + `"test"` 含む artifact 起動中止 + verify_ml_inference.py |

---

## §1 本セッション commit 履歴

| commit | 内容 | ファイル数 |
|---|---|---|
| `6510231` | Phase 0/1-a/1-b/1-c smoke 実行ログ 7 件 | 7 |
| `91317c5` | priority_rebuild scripts 3 件 (Phase 0 集計 + option5 v2/v3) | 3 |
| `c16005f` | 過去 audits + 指示書 一括 (audit15/16/19 + 13 指示書 + modified 3) | 23 |
| `9638c26` | audit17 phase_a §0.13 #1 違反成果物 (記録として保持) | 2 |
| `7872559` | §3.0 cc_ml_design_spec §4 改訂 + 関連 2 ファイル旧表記訂正 | 3 |
| `6d06425` | phase_flow_v4_with_recovery.md 新規作成 (888 行) + V3 archive 移動 | 2 |
| `f540c1e` | phase_flow_v4 A 案修正反映 (888 → 977 行・false_positive + phase_compliance 整合) | 1 |
| (予定) | セッション終了処理 (lessons_active L-200 + WORKFLOW 改訂18 + 本 handoff v21) | 3 |

合計 commit 8 件・約 40 ファイル変更

---

## §2 本セッション 未 commit 成果物 (commit 範囲判断待ち)

なし (全成果物 commit 済 / セッション終了処理 3 件を本 v21 commit に統合予定)

ただし `results/` ディレクトリは CLAUDE.md「コミット禁止」対象で意図的に除外。

---

## §3 pending tasks (次セッション CC への優先順位)

### §3.1 (最優先) Phase 0 改修指示書発注

**内容**: build_labels_pct.py を改修する作業指示書を作成・保存
- 8 欠損指標追加 (RCI(7/9/52) / RSI(21) / RSI_slope / BB_slope / Stoch(5m))
- まこさん発振系 3 件 (RSI ROC / Stoch K-D 差分 / MACD ヒストグラム slope)
- 業界カタログ追加 (TA-Lib / pandas-ta / Murphy / Lopez de Prado)
- 1w/1M MTF 拡張 + ffill 初期実装
- Fractional differentiation (d=0.3/0.5・Lopez de Prado AFML Ch.5)
- PCA 補助列
- パラメータ並列展開 (rsi21 / adx7/21 / bb_window_10/50 / macd 別パラ)

**結果見込み**: 1432 → 約 2000-2500 列・parquet 再生成 (train + test 2025 + test 2026 Q1・約 3-6 時間)

**CP1 監査** (Phase 0 改修着手前 or 完了後):
- 列数 verify (約 2000-2500 範囲)
- leak 4 点チェック (.shift(-N) / fractal j±2 / train→test 侵入 / Fractional weights)
- Claude `/audit` 経由独立検証 (特徴量空間拡張妥当性・1w/1M MTF 4 方式選定 + Fractional differentiation 本プロジェクト適合性)

**指示書フォーマット**:
- 保存先: `.claude/instructions/2026-05-22_phase0_v4_rebuild_instruction.md`
- サイズ: full テンプレ 300-400 行 (新規 verify + 新規ガード追加含む・cc_role.md §1.5.5)
- phase_flow_v4 §2 Phase 0 改修 + Phase -1 USD 絶対値 blacklist 48 整合

### §3.2 (Layer 1 着手) Phase 1 並列学習 (約 1-2 週間)

learning_design_v4 §4 Layer 1 + §11 CP2 (V4.1 監査 #20 反映済):

**3 案並列実装**:
- 案 a: 14 ラベル独立 RMSE (比較ベースライン・Phase 1-a 既存方式の特徴量拡張版で再学習)
- 案 b: Entry Binary Classification (1/0 直接学習・LightGBM Binary objective + class balancing)
- 案 c: Direction Multiclass (LONG/SHORT/Flat 3 クラス分類・LightGBM Multiclass objective)

**並行**:
- B-11 cluster B 案 (LONG/SHORT 差分 4 個追加・16→20 次元) Phase 1 予備学習
- Layer 1 ① (trailing 究明 / 欠落 combo 究明 / 発火頻度可視化) + Layer 1 ② (損 combo 切り捨て) + Layer 1 ③ (K 窓追加) + Layer 1 ④ (特徴量拡張)

**CP2 監査** (Phase 2 着手前):
- 3 案物理証跡対比 (entropy lift / TP Precision / Direction accuracy / simulated PnL)
- 分岐判定:
  - 改善案採用 → Phase 2 進行
  - 3 案とも未達 → **Layer 3 投入** (Triple Barrier multiclass + Meta-labeling 2 段階・Lopez de Prado AFML Ch.3 推奨)

### §3.3 (将来) Phase 2 着手前 smoothing 設計再 audit

handoff v17/v18/v19 から継承・learning_design_v3 §B-15 修正履歴 #13 注記。Sharpe maximizing 復活検討。

### §3.4 (将来継承) Phase 7-d 着手前 maxMarketOrderQty paper trading test

v15-v20 から継承・phase_compliance_checklist.md Phase 7-d セクション記録済。

---

## §4 次セッション CC への警告 (handoff v14-v20 全件継承 + 本 v21 新規)

### §4.34 (本セッション §0.27) CC 同型バイアス再演 **累積 18 件**・ルール追加だけでは止まらない実証

handoff v19 §0.13 (5 件) + handoff v20 §0.26 (5 件) + 本 §0.27 (8 件) = 累積 **18 件**:
- 確認質問乱発・教条主義・まこさん発言翻訳・計算ミス・専門用語括弧書き違反・読了スキップ・部分 view で「全文 view」断言・監査済 verify せず断言・整合性 verify せず「総点検」発言・書き直し 7 回繰り返し

**対策 (本セッション学習・L-200)**:
- 「ルール追加で止まる」と期待しない
- **機械的証跡 3 点** (`wc -l` + Read 全文 view + 該当行引用) を「読んだ」「verify した」「総点検した」と書く前に必ず出す
- 監査経路 (Claude 監査モード `/audit`) を能動的に・早期に通す (CC 単独で確定させない)
- まこさんの「分からない」「やめてほしい」「これも確認して」「整理して」を **字面通り** 受け取る (cc_role §3.3 翻訳禁止)
- 数値・整合性を書く前に **必ず実測再計算 + 全文 view + 該当箇所引用**

### §4.35 (本セッション §0.28) Phase 5-b 計算式は MAX_ADDS 込み

旧 V3 の「per-position = 0.12 / cap_N」は MAX_ADDS = 1 前提の計算式。MAX_ADDS = 5 (平均建値型) と組み合わせると **規定 5 倍超過** リスク (合計 0.6 BTC = §0-2 違反)。

正しい計算式 (cc_ml_design_spec §4 改訂後 + phase_flow_v4 §2 Phase 5-b 反映済):
```
per-position = 0.12 / (cap_N × MAX_ADDS) BTC
```

例: cap=6 × MAX_ADDS=5 → per-position = 0.12 / 30 = 0.004 BTC → 1 トレード = 0.004 × 5 = 0.02 BTC × 6 トレード = 0.12 BTC ✅

### §4.36 (本セッション §0.29) phase_flow_v4 確定版 977 行は本 v21 commit `f540c1e` で確定

次セッション CC は **読まずに「読んだ」と言わない**。`wc -l` + Read 全文 view + 該当箇所引用の 3 点機械的証跡を必ず出す。

### §4.37 (本セッション総括) Phase 0 改修着手前必読リスト (機械的証跡必須)

| ファイル | 行数 | 役割 |
|---|---|---|
| `WORKFLOW.md` | 約 460 行 | 現フェーズ・改訂18 ブロック・次タスク優先順位 |
| `learning_design_v4.md` | 336 行 | V4.1 設計図 (本書 phase_flow_v4 の連携) |
| `phase_flow_v4_with_recovery.md` | 977 行 | 各 Phase 学習内容詳細 (本 v21 で確定) |
| `cc_ml_design_spec.md` | 約 250 行 | §4 改訂反映済 (合計 0.12 BTC + cap 合算カウント) |
| `cc_role.md` | 366 行 | CC 役割定義 (§1.4 同型バイアス + §1.6 23 軸 + §3.6 専門用語) |
| `false_positive_incident_policy.md` | 225 行 | §0-1 / §0-2 + §2 類型 A〜H + §5 関所 A〜G |
| `phase_compliance_checklist.md` | 222 行 | Phase 別 verify 項目リスト |
| `auditor_template.md` | 520 行 | Claude `/audit` 監査エージェント用 (CP1〜CP5 で起動) |
| `CAT−指標マトリックス - 一覧.csv` | 1962 行 | 23 軸構成要素カタログ |
| `10_indicator_families.md` | 174 行 | 1432 指標 145 ファミリーリスト |
| `lessons_active.md` | 約 1900 行 | 本 v21 で L-200 追加 + 累積教訓 |
| 本 handoff v21 | (本ファイル) | 宛先 = 次セッション CC |

---

## §5 セッション履歴サマリ (本セッション 2026-05-21)

| 時刻概算 | 出来事 |
|---|---|
| 開始 | handoff v20 受領 → まこさん「続きできる？」確認 → CC が Step 0 セッション開始プロトコル実行 |
| 序盤 | §2.4 handoff v19 残課題 commit 4 件 (logs 7 / scripts 3 / audits + 指示書 23 / audit17 phase_a 2) |
| 序盤 | §3.0 cc_ml_design_spec §4 改訂 (cap カウント = 合算 確定) commit `7872559` |
| 中盤 | §3.1 Phase 0 改修指示書発注準備で `/audit` CP1 前監査を提案 → まこさん「前回でも監査だしたよね」指摘 → CC 教条主義の再演自己申告 |
| 中盤 | phase_flow_v3_with_recovery.md (455 行) を V4 版に書き直し依頼 → CC が試作 #1 (622 行・難解版) 書き → まこさん「難解で読めない」 |
| 中盤 | 試作 #2 (358 行・簡略版) → まこさん「Entry 改善されてない」「23 軸活かせてない」「前チャットで決まった内容反映できてない」3 連続指摘 |
| 中盤 | CC が learning_design_v4.md (336 行) 全文 view 完了申告 → 試作 #3〜#5 (詳細化 / 簡素化 / フロー主役) で書き直し |
| 中盤 | まこさん「フローごとに学習内容を詳細に」指摘 → 試作 #6 (682 行・学習方法明示) |
| 後半 | まこさん「Phase 1 なら (以下は例)」+ 145 ファミリー + A-3 + A-5 例示 → 試作 #7 (770 → 888 行・10_indicator_families.md 反映) |
| 後半 | まこさん「MAX_ADDS 6 ってどういうこと？5 の間違いなのでは？」 → CC 表記訂正 (= 6 種類のバリエーション) |
| 後半 | まこさん「上限合計0.12BTCは守られてるよね？」 → CC 自己 verify で Phase 5-b 計算式の §0-2 違反リスク発見 |
| 後半 | まこさん「他、禁止事項使ってないよね？本番反映可能なロジックのみだよね？未来値とか、バックテストトリック使ってないよね？」 → CC が CLAUDE.md §⛔ 旧 Priority 時代の禁止リストで照合違反 → まこさん「この禁止条項って古くないか？false_positive_incident_policy.md は読んだ？」指摘 |
| 後半 | CC が false_positive_incident_policy.md (225 行) 全文 view → §0-1 / §0-2 / §2 類型 A〜H / §5 関所 A〜G で再 verify → 重大 2 件 + CC 新規発見 3 件 (異常値 STOP / NET 実体 verify / 報告先行) を報告 |
| 後半 | まこさん「phase_compliance_checklist.md これも読んでから、総点検してみて」 → CC が 222 行全文 view → A 案 / B 案 提示 → まこさん「A」GO |
| 終盤 | A 案 8 件修正 commit `f540c1e` (888 → 977 行・+89 行) |
| 終盤 | まこさん「切る」 → セッション終了処理 3 件 (lessons_active L-200 / WORKFLOW 改訂18 / 本 handoff v21) |

---

## §6 改訂履歴

| バージョン | 日付 | 内容 |
|---|---|---|
| v14 | 2026-05-20 | Phase 0 v3 完了報告レビュー + L-196 緊急訂正 |
| v15 | 2026-05-20 | audit#19 全工程完了 + L-198 指示書サイズ規律 |
| v16 | 2026-05-20 | 学習内容 v3 確定 (exchange_spec.md 準拠化) |
| v17 | 2026-05-21 | Phase 0-1a/1b 完了 + audit#18 + v3 §B-15 書き換え + Phase 1-c 発注 |
| v18 | 2026-05-21 | Phase 1-c smoke NO-GO + Web Claude 役割降格 + Phase 0-1 軸実装監査タスク発注 |
| v19 | 2026-05-21 | ML 設計担当 Web Claude → CC 完全移譲確定 + Entry/Exit 両側学習方法改善議論 + CC 同型バイアス 5 件記録 (宛先 CC) |
| v20 | 2026-05-21 後半 | 書類整理 11 件 + WORKFLOW.md スリム化 + learning_design_v4.md 新規 + 監査 #20 で V4.1 化 + auditor 更新 + CC 同型バイアス 5 件記録 |
| **v21** | **2026-05-21** | **§3.0 cc_ml_design_spec §4 改訂 (cap 合算カウント確定) + phase_flow_v4_with_recovery.md 全面書き直し (試作 7 回 → 確定版 977 行・false_positive + phase_compliance 整合 A 案 8 件修正反映) + 書類整理 35 ファイル commit + CC 同型バイアス再演 8 件記録 (累積 18 件)** |

---

## §7 次セッション CC への最初の指示 (= 本ファイル読了後にやること)

1. **本 handoff v21 を物理 view 完了 (機械的証跡)**:
   - `wc -l .claude/instructions/handoff_to_cc_v21_session_20260521.md`
   - Read ツールで全文 view
   - §0.27〜§0.29 + §4.34〜§4.37 を最優先で頭に固定
2. **次タスク (§3.1 Phase 0 改修指示書発注) 着手前に必読**:
   - 上記 §4.37 リストの 12 ファイル全部 (機械的証跡 3 点遵守)
3. **§3.1 Phase 0 改修指示書発注** または **まこさん指示の確認**
4. **未 commit 成果物の commit 範囲をまこさんに確認** (results/ 以外あれば)
5. **CC 同型バイアス再演 累積 18 件を毎ターン警戒**:
   - L-200 自己縛りルール遵守 (機械的証跡 3 点)
   - cc_role.md §1.4 + handoff v20 §0.26 + 本 v21 §0.27 を毎ターン再読

---

以上。

**本 handoff v21 は CC (= 次セッションの私) 宛て**。設計判断は CC 単独 + まこさん + Claude 監査モード `/audit` で確定する。

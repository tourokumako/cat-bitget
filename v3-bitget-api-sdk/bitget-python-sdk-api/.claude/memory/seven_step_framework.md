# 7 工程フレーム全体構成 (= ⛔ 破綻判定済・参照用)

最終更新: 2026-05-26 (= 破綻判定追記)
位置付け: **⛔ 破綻判定済・参照用** (= 2026-05-26 セッション末で破綻判定)。当初は「工程 1-7 の全体フレーム正本」として作成されたが、cat-bitget 制約 (= 月 $1,900 達成のため月 100+ 件必要) と矛盾する設計 (= 3 段階振り落としで月 25 件まで減る試算) と発覚し、L-230 で破綻判定 → 「新フローは旧 Priority 実態 + cat-bitget 制約から CC が独自設計」が引き継ぎ方針。

**新フローの正本ではない**。本ファイルは「過去にこの設計案が提示されていた」という履歴参照用としてのみ残置。新セッション CC が本ファイルをベースに設計を進めることは禁止 (= L-230 整合)。

参照: lessons_active.md L-230 / WORKFLOW.md 改訂42 active 優先 4 / chatgpt_seven_step_origin.md (= 同じく破綻判定済・参照用)

---

## 1. 全体構成表 (= WORKFLOW.md 改訂 35 active L639-649 で確定・改訂 41 active まで継続中)

| 工程 | 構成 |
|---|---|
| 1. 市場状態判定 | 固定ルール (ADX > 25 + DI 差)・後に ML 化検討 |
| 2. Entry 候補生成 | 固定ロジック (= テクニカル全体から構築・旧 Priority 素材化禁止) |
| 3. Entry ML | ML (LightGBM Classifier・TP first 確率) |
| 4. Position Sizing | 動的合成式 (Half-Kelly + Volatility targeting + cluster 配分) |
| 5. Exit ML | ML (単一 multiclass で TP/損切/STALE 判定・必要なら 3 系統分離) |
| 6. Risk 管理 | 固定ルール (spread / ATR 急変 / volume spike)・後に ML 化検討 |
| 7. Online 監視 | 運用層 (監視スクリプト + アラート) |

> **重要**: 本表は改訂 35 で確定した時点の文言。各工程の最新の詳細仕様 (= 上記から発展した内容) は §2 の詳細設計書を参照。
> 例: 工程 1 は改訂 35 時点で「固定ルール (ADX > 25 + DI 差)」だったが、step1_regime_design.md v2.2 で HMM 教師なし学習に進化 (= 2026-05-25 議論で更新)。表自体の文言を CC が独断で書き換えることは禁止 (= L-229 改善 5 整合)。表を更新する場合は議論を経てから本ファイルに改訂を記録。

---

## 2. 各工程の詳細設計書

| 工程 | 詳細設計書 | 状態 |
|---|---|---|
| 1 市場状態判定 | `step1_regime_design.md` | v2.2 確定 → 実装済 (= train_hmm_regime.py) → 視認チェック結果「精度微妙」で **一旦保留** (2026-05-26) |
| 2 Entry 候補生成 | `step2_entry_candidate_design.md` | 未作成 (= 2026-05-26 議論開始予定) |
| 3 Entry ML | `step3_entry_ml_design.md` | 未作成 |
| 4 Position Sizing | `step4_position_sizing_design.md` | 未作成 |
| 5 Exit ML | `step5_exit_ml_design.md` | 未作成 |
| 6 Risk 管理 | `step6_risk_management_design.md` | 未作成 |
| 7 Online 監視 | `step7_online_monitoring_design.md` | 未作成 |

---

## 3. 関連ファイル

| ファイル | 役割 |
|---|---|
| **`chatgpt_seven_step_origin.md`** | **本フレームの決定根拠** (= ChatGPT 提案要約・2026-05-26 新設) |
| `current_redesign_context.md` | 経緯サマリ (= なぜこのフレームに至ったか・SessionStart hook auto-load) |
| `cc_entry_logic_self_study.md` v6 | 業界知識カタログ (= 案 B 学習資料・2485 行・7 工程の業界整合 verify 済) |
| `step1_regime_design.md` 等 | 各工程の詳細設計書 (= §2 参照) |
| `WORKFLOW.md` 改訂 N active | 現フェーズ・本セッション完了事項・次タスク |
| `lessons_active.md` | 教訓 (= 過去議論で出た改善事項・直近 5 件は SessionStart で auto-load) |

---

## 4. このファイルの運用ルール

- **表の文言を CC が独断で書き換えることは禁止** (= L-229 改善 5「まこさん OK 内容そのまま反映する義務」整合)
- 表を更新する場合は議論で OK を取ってから改訂履歴 §5 に追記
- 各工程の詳細議論 → 該当 step{N}_*.md に集約 (= 本ファイルには概要のみ)
- 状態欄 (= §2) は議論進展に合わせて更新可

---

## 5. 改訂履歴

| 日付 | バージョン | 内容 |
|---|---|---|
| 2026-05-26 | v1 | 初版作成 (= WORKFLOW 改訂 35 active L639-649 の表を正本化 + 工程 1 = step1_regime_design.md v2.2 状態反映) |

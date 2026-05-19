# handoff_to_web_claude_v12_session_20260519

セッション: 2026-05-19 PM-EVE (連続セッション 2 本目・compaction 後の延長)
作成者: Web Claude (v3 化セッション・12 回見落とし起こした本人)
保存先: `.claude/instructions/handoff_to_web_claude_v12_session_20260519.md`

---

## §0 前提認識 (これを読まずに設計議論に入ると毎回チャットの大半を消費する・必読)

### §0.1 23 軸 First Principles
詳細は `/mnt/project/web_claude_role.md` §1.6 (431 行・2026-05-19 commit 済) を **全文 view** で読む。

要約:
- 23 軸 = ML 設計の構成要素カタログ (まこさんが提示・Web Claude の思考シュリンク矯正のため)
- 23 軸全部一気が正解とは限らない (まこさん明示 2026-05-19)
- **Web Claude が ML 知見でデザイン責任** (学習対象 / 固定 / 探索 / 優先順位を判断)
- まこさんに確認すべきは **戦略本丸のみ** (D 固定軸変更・目標値変更・Layer 順序)

### §0.2 手動 Priority の位置づけ
詳細は `/mnt/project/web_claude_role.md` §1.7 を全文 view で読む。

要約:
- 手動 Priority (cat_v9) = **ML 学習の最低スタートライン**
- ベンチマークではない (超えたか評価する対象ではない)
- 学習対象でも・押し付け対象でもない
- スタートライン未達 = ML 設計の重大欠陥 (再設計必須)

### §0.3 Web Claude のデザイン責任
詳細は `/mnt/project/web_claude_role.md` §1.5 を全文 view で読む。

要約:
- Web Claude が判断: 23 軸からの選定・軸優先順位・アルゴ・cluster・目的関数・ハイパラ範囲
- まこさんに確認すべきは戦略本丸のみ
- **禁止フレーズ**:
  - 「学習範囲定義 OK か」「Tier 構造 OK か」「○項目限定 OK か」「核は X で OK か」
  - 「私の推奨で OK か」連発 (責任転送)

### §0.4 前セッションで Web Claude が陥った誤解パターン (反面教師・全 12 件)

| # | パターン | 回避策 |
|---|---|---|
| 1 | v11 §3.1 6 項目に視野狭窄 → 18 項目に拡大 → 全部除外と振り回された | 23 軸全体マップを毎ターン再掲 |
| 2 | 手動 Priority 全部除外と過剰反応 | §0.2 スタートライン理解で対処 |
| 3 | 手動指標カバレッジを ML 議題化 (「stoch_k 5m 不在・P○○ 依存」) | §0.2 + 禁止フレーズで対処 |
| 4 | 手動整合性を議題化 (「P25 cat_v9 に存在しない・矛盾」) | §0.2 + 禁止フレーズで対処 |
| 5 | 「Priority 別 AND フラグ」「手動 Exit 11 種を学習対象」と押し付け | §0.2 で対処 |
| 6 | 手動 Priority を「ベンチマーク」と扱う (超えたか評価) | §0.2 スタートライン理解で対処 |
| 7 | 「核は A-1 × A-3 × A-4 × A-5」と決めつけて新規ルールファイル化 | §0.3 デザイン責任は判断・核宣言はしない |
| 8 | 「学習範囲定義 OK か」「Tier 構造 OK か」「○項目限定 OK か」「核 OK か」確認質問乱発 | §0.3 確認質問禁止 |
| 9 | memory ルール 24 を 4 回再修正 (押し付け→ベンチマーク→スタートライン→AND 構造目安) | memory ルールだけでは効かない実証 |
| 10 | 23 軸の本旨見失い・Tier 配置で外形整える | §0.1 で対処 |
| 11 | 毎セッション「アハ体験」状態 (前提認識継承されず) | 本 handoff §0 必読で対処 |
| 12 | role + self_check addendum 生成直後に MAX_ADDS = {1,2,3,5,8,10} を本番再現性 7 項目 verify せずに並べた (重大インシデント・memory ルール 23 違反・handoff v11 §2.1 完全同型再発) | 設計提案前 3 系列 verify を 1 行ずつ提示義務 (簡単版でも省略禁止) |

---

## §1 確定事項 (本セッション 2026-05-19 PM-EVE)

### §1.1 ML 学習デザイン v3 確定 (23 軸振り分け)

| 軸 | 戦略 | 内容 |
|---|---|---|
| A-1 Entry 指標 | A 全投入 | 1432 指標 + 業界カタログ (TA-Lib / pandas-ta / Murphy / Lopez de Prado) |
| A-2 Exit 指標 | A + B 探索 | 業界カタログ 16 サブカテゴリから 12 種以上 |
| A-3 閾値・パラメータ | A + C 学習 | パラメータ違い並列 + 閾値 LightGBM 自動分割 + D-γ 統合 |
| A-4 時間軸 K | B 探索 | K={6,12,24,48,96,144,288} = 28 ラベル |
| A-5 時間足 bar | A 全投入 | 8 TF (5m/15m/30m/1h/4h/1d + 1w/1M 追加検討・3m Layer 2・1m 禁止) |
| A-6 MAX_ADDS | B+C+制約 | {1,2,3,5,8,10} + n_sim 上限制約 + add トリガ TTL 整合 |
| A-7 サイジング | D+B+C | 0.12 BTC 固定・per-position ≥ 0.000167 BTC (BTC=$30k stress) + 8 方式並列 |
| B-8 cap | B 探索 | 静的+combo別+動的並列 |
| B-9 組み合わせ深さ | C 学習 | Optuna num_leaves{7,15,31,63,127}×max_depth{3,5,7,10,-1} |
| B-10 学習アルゴ | B (Layer 3) | LightGBM 主軸 + XGBoost/CatBoost 比較・MiniROCKET 不合格時 |
| B-11 cluster | B 探索 | KMeans k=3/k=4 並列 + 入力 B 案 16→20 次元 |
| B-12 特徴量変換 | A+B 探索 | Fractional diff/PCA/Wavelet + MTF 4 方式 |
| B-13 ratio 閾値 | B+C 学習 | rolling 365日 q90/95/99 + cluster別 + Triple Barrier (Layer 3) |
| B-14 学習データ範囲 | D+B | 期間固定 + Walk-forward/Purged K-fold/CPCV (Layer 3) |
| B-15 目的関数 | D+B 探索 | 月次 NET ≥ $1,900 固定 + **train で RMSE + 直接 PnL + Sharpe maximizing 並列実装 (Phase 1 から・C 案)** |
| D-α 発火頻度 | C 学習 | per-day ≥ 10 件制約 (L-117) |
| D-γ Entry 位置 | A-3 統合 | location_prev / entry_risk_score 特徴量化 |
| D-δ 時間帯曜日 | B (Layer 2) | 統合フェーズで時間帯分布可視化 |
| D-ε regime | B (Layer 2) | B-11 B 案結果次第 |
| D-ζ マルチサイド | D+C | hedge_mode 許可・LONG/SHORT 動的配分 ML 学習 |
| D-η 手数料 | D | Maker 0.014%/0.02% stress / Taker 0.042% / Funding 8h 0.01% |
| D-θ 発注タイプ | D+Layer 3 | Maker 指値前提・不約定モデル化 Layer 3 |

### §1.2 MAX_ADDS verify 通過版 (memory ルール 23 違反インシデント対応・確定)

- per-position ≥ 0.000167 BTC (BTC=$30k stress)
- MAX_ADDS × n_sim ≤ 718 (BTC=$30k 想定・phase_compliance §5d.2 の 1200 より厳しい)
- add トリガ「前回 add 約定確認 + 時間経過 ≥ 15 分」必須 (TTL 整合)
- MAX_ADDS=1 combo は SL なし運用 (time_exit / TP のみ)
- per-position × current_BTC_price ≥ 5 USDT 発注時 verify

### §1.3 Phase 別優先順位

| Phase | 着手軸 | 状態 |
|---|---|---|
| **Phase 0-1** | A-1/A-3/A-4/A-5/B-12/B-14/B-15 (組み合わせ探索空間 + ラベル pct + leak verify + B-15 3 系列並列) | **指示書作成完了・CC commit 待ち** |
| Phase 2 | B-9 (Optuna 主導ハイパラ確定) | Phase 1 完了報告後・指示書未作成 |
| Phase 3 | B-10/B-11 (cluster k=3/k=4 並列 + 入力 B 案) | Phase 2 完了後 |
| Phase 4-b | A-2 (Exit 12 種) / B-13 | Phase 3 完了後 |
| Phase 5 | A-6/A-7/B-8/D-ζ/D-α | Phase 4-b 完了後 |
| Phase 6-7 (Bot 統合) | D-δ/D-ε/D-θ | Phase 5 完了後 |

### §1.4 削除類型 11 種 (Phase 5 必須)

1. 物理枠独占 / 2. leak 由来 / 3. 構造的逆行 / 4. train/test 反転 / 5. 手数料負け
6. 最小単位違反 (per-position < 0.000167 BTC) / 7. 最小注文額違反 / 8. TTL 整合違反
9. SL 設定違反 / 10. メンテ時間帯混入 / 11. 価格依存違反 (USD 絶対値ラベル/Exit)

### §1.5 価格非依存性 6 項目 (commit 済・web_claude_self_check.md line 107-114)

1. ラベル MFE/MAE pct ベース / 2. PROFIT_LOCK_USD → PROFIT_LOCK_PCT
3. cluster 入力 pct 化 / 4. feature_importance USD 絶対値系 blacklist
5. add トリガ % 表現 / 6. TP_FEE_FLOOR BTC 価格動的計算

### §1.6 本番再現性 7 項目 (commit 済・web_claude_self_check.md line 98-106・memory ルール 23)

1. 最小注文 0.0001 BTC / 2. 最小注文額 5 USDT / 3. Tick 0.1 USDT
4. Maker TTL 3 本 + 同一 side pending 禁止 / 5. SL は add_count ≥ 2 のみ
6. メンテ 火/水/木 05-08 UTC / 7. Maker 剥落 0.014%/0.02% stress

### §1.7 手動 Priority スタートライン (web_claude_role.md §1.7・commit 済)

- AND 段数 3-7 ✅ (B-9 num_leaves 7-127 Optuna)
- 指標多様性 8-10 種 ✅ (1432 + 業界カタログ拡張)
- Exit 多様性 12 種 ✅ (業界カタログ 16 サブカテゴリ)
- MAX_ADDS 1 と 5 ✅ ({1,2,3,5,8,10} 並列)
- 共通事前フィルタ ✅ (A-3 内 D-γ 統合)

全項目クリア = スタートライン到達・**ここから先が本題**

---

## §2 commit 済ファイル (本セッション)

| ファイル | 変更 | 状態 |
|---|---|---|
| `web_claude_role.md` | 278 → 431 行 (+153): §1.5/§1.6/§1.7 + v3 行 | ✅ commit 済 |
| `web_claude_self_check.md` | 189 → 231 行 (+42): 23 軸 First Principles verify + 見落とし再発記録 #3-10 + アハ体験防止 + ヘッダー更新 | ✅ commit 済 |
| `.claude/instructions/2026-05-19_role_and_self_check_addendum.md` | 新規 (見落とし #11 追記版) | ✅ commit 済 |
| `.claude/instructions/2026-05-19_role_and_self_check_addendum_completion.md` | 新規 | ✅ commit 済 |
| `web_claude_self_check.md` line 98-106 本番再現性 7 項目 + line 107-114 価格非依存性 6 項目 | 過去セッションで commit 済 (本セッション開始時に既存) | ✅ commit 済 |

---

## §3 pending tasks (次セッション着手対象)

### §3.1 まこさんが CC に commit 指示する待機ファイル

| # | ファイル | 内容 |
|---|---|---|
| 1 | `/mnt/user-data/outputs/2026-05-19_ml_implementation_phase0_1.md` | **Phase 0-1 実装指示書** (本セッション最終確定版・結果詳細レポート方式) |

CC commit 先: `.claude/instructions/2026-05-19_ml_implementation_phase0_1.md`

### §3.2 未確認事項

- `phase_compliance_checklist.md` の Phase -1 セクション (= leak verify チェックリスト + USD 絶対値系 blacklist リスト) commit 状態 → **未 commit の可能性高い** (本セッション grep 結果ヒットゼロ)
- **対応**: Phase 0 Step 5 で CC が phase_compliance_checklist.md を更新する指示が指示書に含まれている → CC commit 時に解消

### §3.3 次タスク (順序固定)

1. **まこさんが CC に Phase 0-1 指示書を発注**
2. CC が必読 14 ファイル全文読了 (wc -l 証跡)
3. CC が Step 0 (3 系列 verify) 完了報告冒頭に提示
4. CC が Phase 0 Step 1-6 実装
5. CC が `phase0_audit_report.md` 提出 + 完了報告 commit
6. **Web Claude (次セッション・私) がレビュー**: 結果詳細レポートのチェック (BTC サイズ上限違反・未来値使用・本番再現性・価格非依存性・やってるフリ・過去 incident 同型)
7. レビュー OK で CC が Phase 1 Step 7-13 着手
8. CC が `phase1_audit_report.md` 提出 + 完了報告 commit
9. **Web Claude (次セッション・私) がレビュー + audit#18 監査経路送付**
10. Phase 2 指示書作成 (Optuna ハイパラ確定)

### §3.4 audit#18 (独立評価) の対象

本セッションで Web Claude が 12 回見落としを起こした事実を踏まえ、以下を audit#18 で必須評価:

| Phase | 監査対象 |
|---|---|
| Phase 0 | leak verify 機械化 (Step 5) |
| Phase 1 | B-15 3 系列 custom objective 数式 verify (Step 10) |
| Phase 1 | feature_importance 価格非依存性 (Step 11) |

監査経路: `auditor_template.md` § 7 主エージェント作業バイアス監査 / §3 leak verify 監査 / §5 数式 verify 監査

---

## §4 次セッション Web Claude (私) への警告

### §4.1 設計提案前 3 系列 verify (絶対遵守・「簡単版」でも省略禁止)

設計提案・指示書発行前に **必ず以下 3 系列 18 項目を 1 行ずつチャットに提示**:

1. **本番再現性 7 項目** (memory ルール 23 / self_check line 98-106)
2. **価格非依存性 6 項目** (self_check line 107-114)
3. **23 軸 First Principles 6 項目** (self_check addendum チェック A)

省略 = 重大インシデント (類型 G + 類型 H 近接・false_positive_incident_policy §4 手順起動)

### §4.2 デザイン責任を持つ (確認質問乱発禁止)

23 軸から学習対象 / 固定 / 探索 / 優先順位を **Web Claude が判断**。
まこさんに「○○で OK か」を聞くのは戦略本丸 (D 固定変更・目標値変更・Layer 順序) のみ。

### §4.3 手動 Priority への言及禁止 (5 ファイル読了済の知識は持っていても ML 議題化禁止)

- 手動カバレッジ ("stoch_k 5m 不在・P○○ 依存") を ML 議題化しない
- 手動整合性 (P25 矛盾) を ML 議題化しない
- 押し付け (Priority 別 AND フラグ・手動 Exit 学習対象) しない
- ベンチマーク扱い (超えたか評価) しない
- 唯一許容: スタートライン到達 verify (§1.7) のみ

### §4.4 23 軸の本旨

23 軸 = 判断材料素材 (Web Claude の思考シュリンク矯正のため)。
全部一気が正解とは限らない (まこさん明示)。
Tier 配置で外形整えるだけは本旨を外す。
「核は X」と決めつけて新規ルールファイル化しない。

### §4.5 Phase 0 Step 5 で phase_compliance Phase -1 commit (未対応)

CC が phase_compliance_checklist.md に Phase -1 セクション (leak verify チェックリスト + USD 絶対値系 blacklist リスト) を追加する指示が Phase 0-1 指示書 Step 5 に含まれている。
Phase 0 完了報告レビュー時に Web Claude (次セッション) が verify 必須。

### §4.6 「アハ体験」防止

23 軸の存在理由・参照すべき理由・手動 Priority の位置づけを毎セッション忘れて再発見する状態 = まこさんが「Claude が一人でアハ体験みたいな状態」と指摘。

**対応**: 本 handoff §0 を **読了ゲートで必読**。読まずに設計議論に入ったらまこさんに「23 軸の存在理由を 1 行で言って」と確認させる権限あり (即答不可なら前提認識スキップ確定・差し戻し)。

---

## §5 セッション履歴サマリ (本セッション PM-EVE)

| 時刻 (概算) | 出来事 |
|---|---|
| 開始 | 連続セッション 2 本目・compaction 後の延長 |
| 序盤 | 5 ファイル読了 (10_indicator_families / 09_stocktake / cat_params_v9 / cat_v9_decider / indicator_catalogue) |
| 中盤 | ML 学習デザイン v3 提示 → まこさん指摘「P23 指標が入っていない論外」「手動ロジック混ぜ込むな」 |
| 中盤 | 12 回見落とし発覚 (視野狭窄 / 過剰反応 / 手動カバレッジ ML 議題化 / 押し付け / ベンチマーク誤解 / 核決めつけ / 確認質問乱発 / memory ルール 24 4 回再修正 / 23 軸本旨見失い / アハ体験) |
| 後半 | `2026-05-19_role_and_self_check_addendum.md` 生成 → まこさん commit 済 |
| 終盤 | ML 実装指示書本体作成着手 → ML 学習デザイン簡単版で MAX_ADDS verify 省略 (重大インシデント) |
| 終盤 | 本番再現性 7 項目 verify 実施 → MAX_ADDS verify 通過版確定 |
| 終盤 | Phase 0-1 実装指示書生成 (ダッシュボード → 結果詳細レポート修正) |
| 終了 | handoff v12 作成 (本ファイル) |

---

## §6 改訂履歴

| バージョン | 日付 | 内容 |
|---|---|---|
| v11 | 2026-05-19 (午前) | 連続セッション 1 本目 (compaction 前) |
| v12 | 2026-05-19 PM-EVE | 連続セッション 2 本目 (本セッション・compaction 後の延長・本ファイル) |

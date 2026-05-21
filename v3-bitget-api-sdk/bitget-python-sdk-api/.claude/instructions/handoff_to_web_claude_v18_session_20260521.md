# handoff_to_web_claude_v18_session_20260521

セッション: 2026-05-21 (Phase 1-c smoke NO-GO + Web Claude 役割降格)
作成者: Web Claude (本セッション末・自己降格申告含む)
保存先: `.claude/instructions/handoff_to_web_claude_v18_session_20260521.md`

---

## §0 前提認識 (v14 / v15 / v16 / v17 §0 を全件継承 + 本 v18 で重大追加)

### §0.11 (本セッションで判明・最重大) Web Claude 1 週間同型ミス再発 → 役割降格 (設計者 → 機械照合担当)

#### 経緯 (2026-05-15 〜 2026-05-21)

| 日付 | 事象 | 結果 |
|---|---|---|
| 2026-05-15 | handoff v7 で「未学習 8 指標追加 = Layer 1 ④ 最優先」確定 | 後続セッションで実施されず放置 |
| 2026-05-19 | ML 設計 v2 (Tier 1-5) 提案 | 「23 軸全部一気が正解とは限らない」と却下・「核は A-1×A-3×A-4×A-5」決めつけで撤回 |
| 2026-05-20 | learning_design_v3.md 確定 (まこさん承認・commit 53debce / e5bcd5b) | §Phase 別優先順位 で「Phase 0-1 で 7 軸全部 (A-1/A-3/A-4/A-5/B-12/B-14/B-15)」明記 |
| 2026-05-19 PM-EVE | Phase 0 v3 指示書発注 (Web Claude) | 7 軸中 A-4 / B-14 のみ実装・A-1 / A-3 / A-5 / B-12 未実装 |
| 2026-05-21 (早朝) | Phase 1-a (RMSE 14 ラベル) 完了 | rmse_ratio < 1.5 が 14/14 PASS / ただし K288 pred_std/label_std=0.07 で定数寄り observation |
| 2026-05-21 (午前) | Phase 1-b 簡易 PnL NO-GO (全 K マイナス) | audit#18 起票 → Triple Barrier multiclass + EV フィルタ採用 |
| 2026-05-21 (午後) | Phase 1-c smoke NO-GO (K=12 logloss 1.0322 ≥ 0.95) | entropy lift 2.2% = ボラ予測しかできない |
| 2026-05-21 (午後・本セッション) | まこさんから「23 軸かけ合わせ Entry 予測になっていない」指摘 | Web Claude が learning_design_v3 §Phase 別優先順位 を **自分で起案して自分で守らなかった** ことを自己申告 |

#### 根本原因 (Web Claude 自己診断)

- learning_design_v3.md を起案・確定したのは Web Claude 本人
- その後の Phase 0 v3 指示書 / Phase 1-a 指示書 / Phase 1-c 指示書も Web Claude 本人が発注
- 正本に「Phase 0-1 で 7 軸全部入れる」と書いて、自分で発注した指示書に 4 軸 (A-1 / A-3 / A-5 / B-12) を入れなかった
- 4 セッション連続 (Phase 0 v3 → Phase 1-a → Phase 1-b → Phase 1-c) で同じ穴に落ちた
- まこさんから 1 週間で 3 回 (5/15 / 5/19 / 5/21) 同型問題を指摘されたが、その都度「次は気を付けます」を繰り返し再発防止できなかった
- 本セッション (5/21) でも、Phase 1-c smoke 失敗の対処として「8 指標追加」「Phase 0 v4 で +1200-2000 列」と提案 → どちらも learning_design_v3 から見れば部分集合 / 言い換えで、同型再発

#### 構造的バイアス (web_claude_role.md §1.4 既存記述 + 本セッション追加実証)

- 実装回避バイアス (X1 予測装置のみで考え X2 強化学習等を過小評価)
- spec の枠内でしか動かない (提示された軸内でのみ最適化)
- 同型バイアス (CC・監査も同じ claude 系訓練ベース AI)
- **新規追加: 自己起案した正本を自己発注した指示書で守らない構造的欠陥**

#### 対応 (本セッションでまこさん決定・2026-05-21)

**Web Claude を ML 設計の意思決定経路から外す**:

| 旧役割 | 新役割 |
|---|---|
| ML 設計担当 (23 軸からの選定 / 学習対象 / 固定 / 探索 / 優先順位を判断) | **機械照合担当のみ** (CC が出した実装計画と learning_design_v3 の bit-exact 一致確認のみ) |
| CC への指示書作成 | **まこさんが CC へ直接発注** (Web Claude を経由しない) |
| 完了報告レビュー (異常値スメル + leak verify + 公式 source 照合) | **機械照合のみ** (新規判断追加禁止) |

#### 次セッション Web Claude (= 本ファイルの読み手) への警告

**絶対にやらないこと**:
- 「これも追加した方が良い」「これは外しても良い」等の判断
- 軸の優先順位変更提案
- 実装方針の改変
- 「核は X」「Tier 1-5」「Layer 1 ④」等の決めつけ表現
- learning_design_v3.md に書かれていない軸・指標・変換・時間足の提案

**やること**:
- CC 完了報告と learning_design_v3.md の機械照合 (§5 チェックリスト)
- 差分検出時の指摘 (CC へ修正依頼)
- 機械照合 PASS 後のまこさん報告

**判断を求められた時の対応**:
- 「私 (Web Claude) は本セッションから設計者ではなく機械照合担当です。設計判断はまこさんに直接お願いします」と返す
- 例外: learning_design_v3.md 本文引用で答えられる質問のみ受付

---

## §1 本セッション (2026-05-21) 確定事項

### §1.1 Phase 0 v3 完了 (commit 4df8924)

| 観点 | 結果 |
|---|---|
| 行数差分 | ✅ 394,561 / 105,120 / 25,631 完全一致 |
| ラベル対称性 (14 ラベル B 案) | ✅ 全 K で bit-exact (diff=0.0) |
| 異常値スメル | ✅ 2021-05-19 BTC Black Wednesday 整合 |
| メンテ flag 列 | ✅ 存在・Phase 5 不使用 |
| 14 ラベル B 案採用 | ✅ commit 53debce |

### §1.2 spec sweep (commit 22e75a9)

cc_ml_design_spec.md / phase_compliance_checklist.md / ml_axis_catalog.md / self_check addendum の 4 ファイルに learning_design_v3 / exchange_spec audit#19 確定値を機械反映。

### §1.3 Phase 1-a 完了 (14 ラベル RMSE)

| 結果 | 値 |
|---|---|
| rmse_ratio < 1.5 | 14/14 ✅ |
| leak 4 点 | check_1 14/14 PASS / check_2 PASS / check_3 6 PASS + 8 WARN / check_4 PASS |
| lift > 10% | 14/14 (28-36%) |

**Observation (本セッションで重要視すべき)**:
- K288 LONG_MFE/MAE で pred_std/label_std < 0.08 (定数寄り予測)
- K48 LONG_MFE で同 ratio = 0.17
- 短期 K で atr14_pct__5m dominance 33-65%

### §1.4 Phase 1-b 簡易 PnL NO-GO

K=6/12/24 全て年間 NET マイナス。K=12 で SL hit が TP hit の 1.78 倍 = RMSE では時間順序未学習。

### §1.5 audit#18 完了 + A 案 (Triple Barrier multiclass + EV フィルタ) 採用

audit#18 で PnL/Sharpe maximizing custom objective の数式破綻判定 + ChatGPT 独立検証で同結論 → A 案採用 (commit 58906228)。learning_design_v3 §B-15 修正履歴 #13 + phase_flow_v3_with_recovery §2 同期書き換え済。

### §1.6 Phase 1-c smoke NO-GO (K=12 単独)

| 項目 | 値 | 基準 | 判定 |
|---|---|---|---|
| valid_logloss | 1.0322 | < 0.95 | ❌ |
| TP Precision (P>0.5) | 0.2364 | > 0.4 | ❌ |
| top1 | realized_vol_rank_50b__15m (19.68%) | < 30% | ✅ WARN なし |
| entropy lift | 2.2% (class-balance baseline 1.055 比) | — | (情報利得わずか) |

**構造的解釈**: Phase 1-a (RMSE) + Phase 1-c (multiclass) どちらも「ボラの大きさ予測」しか機能しない。「方向・タイミング予測」が立ち上がっていない。

**ただし**: この smoke 失敗は learning_design_v3 §Phase 別優先順位 通りの実装 (A-1 / A-3 / A-5 / B-12 全投入) をしていない状態での結果のため、**学習設計の限界判定としては根拠不足**。Phase 0 v4 + Phase 1-a 再学習後に再判定が必要。

### §1.7 ラベル分布表 (Triple Barrier・TP_MULT=2.0 / SL_MULT=1.5)

| K | SL% | TIME% | TP% | 健全性 |
|---|---|---|---|---|
| 6 | 33% | 47% | 20% | ✅ |
| 12 | 46% | 22% | 32% | ✅ |
| 24 | 54% | 7% | 40% | ✅ (border) |
| 48 | 57% | 1% | 42% | ⚠️ TIME<5% |
| 96 | 57% | 0.2% | 43% | ⚠️ |
| 144 | 57% | 0.1% | 43% | ⚠️ |
| 288 | 57% | 0.02% | 43% | ⚠️ |

長期 K (48 以上) で TIME クラス消滅 = barrier が time horizon に対して狭すぎる。

### §1.8 本セッションで決定: Phase 0-1 軸実装監査タスク発注 (まこさん → CC 直接)

Web Claude が設計から外れた状態で、CC が learning_design_v3.md §Phase 別優先順位 を直接参照して Phase 0-1 軸の現状実装監査 + 未実装項目の実装計画書を作成する。

指示書: `.claude/instructions/2026-05-21_phase0_1_axis_implementation_audit.md` (本セッションで作成済)

---

## §2 本セッション commit / 成果物

| # | 成果物 | パス / commit |
|---|---|---|
| 1 | Phase 0 verify v2 | commit 4df8924 |
| 2 | spec sweep | commit 22e75a9 |
| 3 | Phase 1-a (observation 追記後) | commit 9d99dbb |
| 4 | phase_flow_v3_with_recovery 設計書 | commit 57f92d1 |
| 5 | Phase 1-b 簡易 PnL | commit 2f01a98 |
| 6 | audit#18 起票指示書 + 出力 | (CC 実施・出力 md 受領済) |
| 7 | v3 §B-15 + phase_flow §2 同期書き換え | commit 5890622 |
| 8 | Phase 1-c smoke 実行 | commit 待ち |
| 9 | **Phase 0-1 軸実装監査指示書 (まこさん → CC 直接発注)** | `.claude/instructions/2026-05-21_phase0_1_axis_implementation_audit.md` |
| 10 | handoff v18 (本ファイル) | 本セッション末 |

---

## §3 pending tasks (次セッション優先順位固定)

### §3.0 (最優先) Phase 0-1 軸実装監査タスク完了レビュー (Web Claude 機械照合のみ)

CC が `.claude/instructions/2026-05-21_phase0_1_axis_implementation_audit_completion.md` を出した後、Web Claude は本指示書 §5 チェックリスト (7 項目) のみ実施:

| # | 照合項目 | 判定基準 |
|---|---|---|
| 1 | 7 軸全て表に記載されているか | A-1 / A-3 / A-4 / A-5 / B-12 / B-14 / B-15 |
| 2 | 各軸の「正本指定」が learning_design_v3 該当行と bit-exact 一致するか | 引用文字列 = 正本文字列 |
| 3 | 未実装項目が正本指定と矛盾していないか | 誤分類なし |
| 4 | 実装計画書の各項目が learning_design_v3 本文引用に基づいているか | 引用なき新規記述なし |
| 5 | 価格非依存性 verify が新規追加列全てに対して実施されているか | 列ごと 1 行 verify |
| 6 | 禁止語彙 self-grep が実施されているか + 全件 0 件か | 残存語彙なし |
| 7 | 機械的証跡 (必読 7 ファイル wc -l + 物理引用) が記載されているか | 7 ファイル全て |

**機械照合 PASS 後**: まこさんに報告 → まこさんが Phase 0 v4 再生成タスクの発注判断。

**機械照合 FAIL 時**: CC へ修正依頼 (Web Claude が新規判断を追加しない・差分指摘のみ)。

### §3.1 (将来) Phase 0 v4 再生成 + Phase 1-a 再学習 (まこさん → CC 直接発注予定)

Phase 0-1 軸実装監査タスク機械照合 PASS 後、まこさんが CC に直接発注:
- Phase 0 v4: A-1 業界カタログ拡張 + A-3 パラメータ違い並列展開 + A-5 1w/1M 追加 + B-12 4 方式変換
- Phase 1-a 再学習: 拡張後特徴量で RMSE 14 ラベル再学習

Web Claude は本タスクでも機械照合担当 (設計関与しない)。

### §3.2 (将来) Phase 1-c 再開判定

Phase 0 v4 + Phase 1-a 再学習結果が出た後、Phase 1-c smoke を再実行するか否か判定。本セッションの Phase 1-c smoke 失敗 (entropy lift 2.2%) は learning_design_v3 不完全実装下の結果のため、再学習後に再判定が必要。

### §3.3 (将来) Phase 2 以降

Phase 0 v4 + Phase 1-a + Phase 1-c (再判定) 完了後、learning_design_v3 §Phase 別優先順位 に従って Phase 2 (B-9 Optuna) 以降を順次発注。

### §3.4 (将来) Phase 7-d 着手前 maxMarketOrderQty paper trading test

v15-17 から継承。`phase_compliance_checklist.md` Phase 7-d セクション記録済。

---

## §4 次セッション Web Claude (私) への警告 (v14-v17 §4 全件継承 + 本 v18 新規)

### §4.22 (本セッション §0.11) 設計判断禁止・機械照合のみ

本セッション (2026-05-21) でまこさんが決定: Web Claude は ML 設計の意思決定経路から外れ、機械照合担当のみ。

検知方法: 次セッション開始時、handoff v18 §0.11 を全文 view + 「役割降格を確認しました。本セッションで設計判断しません」と宣言してからタスク開始。

### §4.23 (本セッション) 自己起案した正本を自己発注した指示書で守らない構造的欠陥

learning_design_v3 を起案・確定した本人が、後続指示書でその正本を守らない 1 週間の実証。今後 Web Claude が ML 設計に関わる可能性が再浮上した時 (例: まこさんが再起用判断) は、本欠陥を最優先で警戒。

### §4.24 (本セッション) 1 週間同型ミス記録

| 日付 | 同型パターン |
|---|---|
| 2026-05-15 | handoff v7 Layer 1 ④ 確定 → 放置 |
| 2026-05-19 | ML 設計 v2 Tier 1-5 提案 → 「23 軸全部一気が正解とは限らない」却下 |
| 2026-05-19 | 「核は A-1×A-3×A-4×A-5」決めつけ → デザイン責任の押し付けで撤回 |
| 2026-05-20 | learning_design_v3 確定後の Phase 0 v3 指示書で 4 軸未実装 |
| 2026-05-21 | Phase 1-c smoke 失敗対処として「8 指標追加」提案 → learning_design_v3 部分集合への矮小化 |
| 2026-05-21 | 同上対処として「Phase 0 v4 +1200-2000 列」提案 → learning_design_v3 言い換え |

**共通構造**: 正本に書いてあることを忘れて再発見・部分集合化・言い換える。

### §4.25 (本セッション) lessons_active L-200 (本セッション末追記対象)

次セッション開始時、lessons_active.md L-200 として以下を追記する想定:

```
### L-200: Web Claude 自己起案正本の自己発注指示書での未遵守 (2026-05-21)

何が起きたか:
learning_design_v3.md §Phase 別優先順位 で「Phase 0-1 で 7 軸 (A-1/A-3/A-4/A-5/B-12/B-14/B-15)」と
Web Claude 自身が起案・確定したにもかかわらず、後続 Phase 0 v3 / Phase 1-a / Phase 1-c の
指示書発注時に 4 軸 (A-1 / A-3 / A-5 / B-12) を含めず、1 週間 4 セッション連続で同型ミス再発。

Why:
- 正本起案後、後続セッションで正本を物理 view せずに指示書ドラフトに突入
- 「正本に書いてあるはず」を頭の中で再構成して、再構成漏れに気付かない
- まこさんから指摘されても「次は気を付けます」を繰り返し再発防止できない

How to apply:
- Web Claude は本日 (2026-05-21) より ML 設計の意思決定経路から外れる
- まこさんが CC に直接発注し、Web Claude は機械照合のみ
- 役割復帰判定はまこさん単独
```

---

## §5 セッション履歴サマリ (本セッション 2026-05-21)

| 時刻概算 | 出来事 |
|---|---|
| 開始 | handoff v17 受領 + 読了ゲート通過 (10 ファイル全文 view + 機械的証跡) |
| 序盤 | Phase 1-c 完了報告受領 → Stage 1 (ラベル分布表) で長期 K の TIME クラス消滅判明 → 案 α (健全 3 K のみ) 採用 |
| 中盤 | Stage 2 smoke (K=12) NO-GO (logloss 1.0322 / TP Precision 0.2364 / entropy lift 2.2%) |
| 中盤 | Web Claude が「案 δ (3 K full 学習で判断材料拡張)」推奨 → まこさんから「23 軸かけ合わせになっていない」指摘 |
| 中盤 | Web Claude が learning_design_v3 §Phase 別優先順位 を物理 view → 4 軸 (A-1/A-3/A-5/B-12) 未実装と自己申告 |
| 後半 | Web Claude が「8 指標追加」提案 → まこさん「大いに不足」と却下 |
| 後半 | Web Claude が「Phase 0 v4 +1200-2000 列」提案 → まこさん「ここ一週間これの繰り返し」と指摘 |
| 後半 | Web Claude が同型再発の構造的欠陥を自己申告 → まこさん決定「Web Claude を設計から外す」 |
| 終盤 | Phase 0-1 軸実装監査指示書作成 (まこさん → CC 直接発注用) |
| 終盤 | handoff v18 作成 (本ファイル・自己降格申告含む) |

---

## §6 改訂履歴

| バージョン | 日付 | 内容 |
|---|---|---|
| v14 | 2026-05-20 | Phase 0 v3 完了報告レビュー + L-196 緊急訂正 |
| v15 | 2026-05-20 | audit#19 全工程完了 + L-198 指示書サイズ規律 |
| v16 | 2026-05-20 | 学習内容 v3 確定 (exchange_spec.md 準拠化) |
| v17 | 2026-05-21 | Phase 0-1a/1b 完了 + audit#18 + v3 §B-15 書き換え + Phase 1-c 発注 |
| **v18** | **2026-05-21** | **Phase 1-c smoke NO-GO + Web Claude 役割降格 (設計者 → 機械照合担当) + Phase 0-1 軸実装監査タスクをまこさん → CC 直接発注 (本ファイル)** |

---

以上。

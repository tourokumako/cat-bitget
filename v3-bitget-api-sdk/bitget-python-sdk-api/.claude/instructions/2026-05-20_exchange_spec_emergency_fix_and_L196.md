# 【タスク】exchange_spec.md 緊急訂正 + L-196 新規 lesson 化

発行日: 2026-05-20
発行者: Web Claude
背景: 本セッション (2026-05-20) で exchange_spec.md L35「定期メンテ 火/水/木 05:00-08:00 UTC」が出典なき Claude 想定値であることが発覚 (Bitget 公式ガイドで 24/7 確定)。L9-10 標準手数料も同様疑い。即時暫定対応として 6 ファイル修正 + 新規 lesson L-196 化。

## 必読 (省略禁止・wc -l + 全文 view + 機械的証跡)

1. exchange_spec.md (224 行・更新対象)
2. web_claude_self_check.md (231 行・更新対象)
3. lessons_active.md (1801 行・L-196 追加対象)
4. false_positive_incident_policy.md (225 行・§2 類型 G + §3 #5 + §5 関所 F)
5. handoff_to_web_claude_v12_session_20260519.md (256 行・§1.6 + §4.1 訂正注記対象)
6. handoff_to_web_claude_v13_session_20260519.md (213 行・§1.7 + §4.1 訂正注記対象)
7. CLAUDE.md (239 行・必読リスト L130-135 確認)
8. WORKFLOW.md (772 行・Phase 0 メンテ flag の Phase 5 不使用化 追記対象)

## 修正対象 6 箇所

### 修正 1: exchange_spec.md L9-10 標準手数料に ⚠️ マーク追加

| Maker fee | 0.014% (0.00014) ✅ まこさん画面確認 (2026-05-20) | **⚠️ 0.02% (0.0002) — 出典未確認・Claude 想定値・stress test 用暫定使用・audit#19 対象** | (注釈変更) |
| Taker fee | 0.042% (0.00042) ✅ 同上 | **⚠️ 0.06% (0.0006) — 同上** | (注釈変更) |

### 修正 2: exchange_spec.md L35 メンテ時間削除 + 24/7 default 明文化

旧: `| 定期メンテナンス | 火/水/木 05:00-08:00 UTC |` + `⚠️ メンテナンス時間帯はリトライ機構必須`

新: `| 定期メンテナンス | なし (24/7 取引) ✅ 公式ガイド「中断のない年中無休の取引」(Bitget 株式無期限先物完全ガイド・2026-01-08・2026-05-20 まこさん確認) |` + `> 個別アナウンスは Support > Maintenance (https://www.bitget.com/support/sections/12508313404950) を都度確認。Bot 起動時は最新アナウンス取得を実装に含める (Phase 7-c 要件)。` + `> ⚠️ **削除した旧記述「火/水/木 05:00-08:00 UTC」は出典なき Claude 想定値だった (2026-05-20 発覚・L-196 参照)**`

### 修正 3: exchange_spec.md 出典セクション (L39-43) を項目別に強化

| 項目 | 出典 | 状態 |
|---|---|---|
| Maker/Taker 適用値 | まこさん発注画面スクショ (2026-05-20) | ✅ verify 済 |
| Maker/Taker 標準値 | ⚠️ 出典なし・Claude 想定値 | ⚠️ audit#19 対象 |
| 最小注文 / 最小注文額 / Tick size / 最大レバ / マージンモード / 最大同時保有 | 公式 API `GET /api/v2/mix/market/contracts` (response 例保存未実施) | ⚠️ audit#19 対象 |
| Funding 8h 間隔 | 公式ガイド (2026-01-08) | ✅ verify 済 |
| Funding 0.01% rate | ⚠️ phase_compliance L13 暫定値・出典なし | ⚠️ audit#19 対象 |
| 取引時間 24/7 | 公式ガイド (2026-01-08・2026-05-20 まこさん確認) | ✅ verify 済 |
| 定期メンテ (旧記述) | ⛔ Claude 想定値・削除済 (L-196) | ⛔ |

### 修正 4: web_claude_self_check.md L99-106 本番再現性 7 項目訂正

#6 修正後: **メンテ時間帯 = なし (24/7 取引・公式ガイド 2026-01-08 確認済)**。個別アナウンスは Support 都度確認・Bot 起動時に最新アナウンス取得を実装。**旧記述「火/水/木 05:00-08:00 UTC」は Claude 想定値で削除済 (L-196 参照)**

#7 修正後: **Maker 剥落 stress test**: 適用値 0.014% (verify 済) と **⚠️ 想定剥落値 0.02% (出典未確認・stress 用暫定値・要 verify)** の両方で月次 NET ≥ $1,900 全月クリア。剥落値の公式 source 確定は audit#19 対象

### 修正 5: web_claude_self_check.md 末尾「見落とし再発記録」追記

| 11 | 2026-05-20 | exchange_spec.md L35 「定期メンテ 火/水/木 05-08 UTC」を出典確認せず正本扱い・本セッションで何度も「本番再現性 #6・合格項目」として書き続けた・まこさん公式コピペでインシデント発覚 | まこさん | L-180 は実装 verify に限定・外部仕様 verify 手続きがなかった |

### 修正 6: lessons_active.md L-196 新規追加

(L-192 の前に挿入。L1 ヘッダ「直近50件の現役教訓（L-192〜L-103）」を「L-196〜L-103」に更新)

### 修正 7 (追加): handoff v12/v13 訂正注記

- handoff v12 §1.6 / §4.1 該当行に「※ 2026-05-20 訂正済・L-196 参照」を 1 行追記
- handoff v13 §1.7 / §4.1 該当行に同上追記

### 修正 8 (追加): WORKFLOW.md に Phase 0 v3 メンテ flag 扱い記載

WORKFLOW.md §🔴現在のフェーズ末尾に追記:
> **Phase 0 v3 メンテ flag (28,152 bar・5.35%) の扱い (2026-05-20 確定)**: parquet 内 `is_maintenance` 列は残置 (再生成コスト 2h40m 回避)。ただし Phase 5 Replay 以降では **使わない** (Bitget は 24/7 取引・L-196 参照)。Phase 5 設計時に「メンテ flag 不使用」を明示する。

## Step

1. 必読 8 ファイル全文 view (機械的証跡 wc -l + 0/25/50/75/100% 引用 + 1 行要約)
2. 修正 1-3: exchange_spec.md (3 commit に分けるか 1 commit にまとめるかは CC 判断)
3. 修正 4-5: web_claude_self_check.md
4. 修正 6: lessons_active.md L-196 追加 + ヘッダ更新
5. 修正 7: handoff v12/v13 訂正注記
6. 修正 8: WORKFLOW.md メンテ flag 不使用明記
7. 完了 grep verify:
   - `grep -rn '05:00-08:00 UTC\|05-08 UTC\|05-07 UTC' .claude/rules/ .claude/memory/ .claude/instructions/2026-05-19_* WORKFLOW.md`
   - `grep -n '0.02%.*標準\|0.06%.*標準' .claude/rules/exchange_spec.md`
   - `grep -n 'L-196' .claude/memory/lessons_active.md`
   - `grep -n '24/7\|年中無休\|中断のない' .claude/rules/exchange_spec.md`
   - `grep -n 'is_maintenance.*Phase 5\|メンテ flag' WORKFLOW.md`
8. completion report 作成
9. commit + Web Claude レビュー待ち

## 完了報告必須証跡 (WORKFLOW L53-76)

1. コード総点検 grep 結果: Step 7 の 5 種 grep を全件報告 ("no matches" 含む)
2. 数値の二重提示: 修正前後 diff (行番号付き)
3. 成果物ファイル実体: 6 ファイル + completion report
4. 実行ログ: commit hash・時刻・git diff 行数
5. 絞り込み示唆語彙 grep: 適用外 (本タスクは設計判断なし)
6. 個別組合せ train→test 変化表: 適用外
7. 異常値スメル: 適用外 (数値生成なし)
8. 全工程の未来参照 verify: 適用外 (spec/doc 文書修正のみ)

## 禁止

- 「Claude 想定値」を「公式値」のように書き換える・必ず ⚠️ マーク + 要 verify を併記
- Phase 0 v3 メンテ flag (28,152 bar・5.35%) を残置正当化しない・Phase 5 不使用化を WORKFLOW.md に明示
- exchange_spec.md L9-10 標準手数料を「同上」で済まさない・項目別に出典を明記
- handoff v12/v13 の該当箇所への訂正注記を省略しない
- L-196 を曖昧記述で済まさない

## 保存先

- 本指示書: `.claude/instructions/2026-05-20_exchange_spec_emergency_fix_and_L196.md`
- 完了報告: `.claude/instructions/2026-05-20_exchange_spec_emergency_fix_and_L196_completion.md`

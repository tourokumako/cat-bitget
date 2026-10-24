# 【CC タスク】学習内容 v3 + handoff v16 保存 + commit (機械的反映タスク・light 枠)

## メタ情報

| 項目 | 値 |
|---|---|
| 発行日 | 2026-05-20 |
| 発行者 | Web Claude (PM エージェント) |
| 承認 | まこさん (2026-05-20) |
| タスク種別 | **機械的反映 (新規判断ゼロ・新規 verify ゼロ・新規ガード追加ゼロ)** |
| 想定サイズ | light 枠 80-120 行 (memory ルール 24 / L-198 準拠) |
| 関連必読 | 添付 2 ファイル + memory ルール 19 (指示書保管義務) |

## 保存・commit 指示 (memory ルール 19・必須)

本指示書を以下のパスに**そのまま保存し commit する**:

```
.claude/instructions/2026-05-20_learning_design_v3_and_handoff_v16_save.md
```

完了報告は以下のパス:

```
.claude/instructions/2026-05-20_learning_design_v3_and_handoff_v16_save_completion.md
```

チャットテキストだけで終わらせない。

---

## タスク内容

添付された 2 ファイルをリポジトリ内の指定パスに保存 + git commit する。**ファイル内容は一字一句変更しない** (機械的反映のみ)。

### 着手前必読 (3 件・省略禁止)

1. 本指示書本体 (このファイル)
2. 添付ファイル 1: `learning_design_v3_final.md` (学習内容 v3 完成版・exchange_spec.md 準拠化済)
3. 添付ファイル 2: `handoff_to_web_claude_v16_session_20260520.md` (次セッション引き継ぎ)

---

## Step

### Step 1: ファイル配置

| 添付ファイル | 保存先 |
|---|---|
| `learning_design_v3_final.md` | `.claude/memory/learning_design_v3.md` |
| `handoff_to_web_claude_v16_session_20260520.md` | `.claude/instructions/handoff_to_web_claude_v16_session_20260520.md` |

**ファイル内容は変更しない**。コピーのみ。

### Step 2: 旧バージョンの archive 確認

以下のファイルが `.claude/instructions/` 配下に存在する場合、削除せず archive 注記を冒頭に追加 (本指示書では archive 操作は行わない・参照のみ):

- `2026-05-19_ml_design_proposal_v2.md` (Web Claude が将来 archive 化判断・本指示書では触らない)

### Step 3: git commit

```bash
git add .claude/memory/learning_design_v3.md
git add .claude/instructions/handoff_to_web_claude_v16_session_20260520.md
git add .claude/instructions/2026-05-20_learning_design_v3_and_handoff_v16_save.md
git commit -m "docs: 学習内容 v3 (exchange_spec 準拠化) + handoff v16 保存"
```

`git add .` / `git add -A` 禁止 (CLAUDE.md L111 遵守・ファイル単位で add)。

### Step 4: 完了報告作成

`.claude/instructions/2026-05-20_learning_design_v3_and_handoff_v16_save_completion.md` を作成し、以下 4 点を含める:

1. 完了フラグ + 3 ファイルのパス・行数・更新時刻
2. `ls -la .claude/memory/learning_design_v3.md .claude/instructions/handoff_to_web_claude_v16_session_20260520.md` の出力
3. `git log -1 --stat` の出力 (commit 確定確認)
4. `wc -l` で 3 ファイルの行数 (添付ファイルとの bit-exact 一致確認用)

---

## 完了報告必須証跡 (light 枠・4 点)

1. **ファイル実体**: `ls -la` でパス + 行数 + 更新時刻
2. **bit-exact 確認**: `wc -l` で保存後ファイル行数が添付ファイルと一致 (内容変更なし証跡)
3. **git commit 証跡**: `git log -1 --stat` の commit hash + 変更ファイル一覧
4. **MD5 / sha256 hash** (推奨・bit-exact 確認補強): 保存後 3 ファイルの hash 値

---

## ガード (light 枠・最小限)

- **ファイル内容変更禁止**: 添付ファイルと保存後ファイルは bit-exact 一致必須 (機械的反映タスクのため)
- **git add 単位**: ファイル単位 (`git add .` / `git add -A` 禁止・CLAUDE.md L111)
- **commit メッセージ**: 日本語簡潔 (CLAUDE.md L115)

---

## このタスクで「やらないこと」(誤実装防止)

- 学習内容 v3 の内容を CC 側で再評価・修正しない (機械的保存のみ)
- exchange_spec.md / cc_ml_design_spec.md / WORKFLOW.md / phase_compliance_checklist.md は **触らない** (本タスクの対象外・次セッションで spec sweep として別タスク)
- 旧 v2 系ファイル (`2026-05-19_ml_design_proposal_v2.md` 等) の archive 化は本タスクで行わない (Web Claude 判断待ち)
- memory_user_edits は触らない (Web Claude 側で完了済・memory #28)

---

## 次タスク (本タスク完了後・次セッション Web Claude が判断)

handoff v16 §3 pending tasks 参照:
1. 優先 1: Phase 0 v3 Step 3d フル実行 (未着手なら) or 完了レビュー本体 (完了済なら)
2. 優先 2: Phase 0 v3 spec sweep 本体 (16 ラベル → 28 ラベル機械反映)
3. 優先 3: Phase 1 着手指示書発注 (学習内容 v3 §B-15 準拠・28 ラベル LightGBM 学習)

本指示書は機械的保存タスクのため、次タスクの判断は次セッション開始時に Web Claude (新インスタンス) が handoff v16 を読んで実施する。

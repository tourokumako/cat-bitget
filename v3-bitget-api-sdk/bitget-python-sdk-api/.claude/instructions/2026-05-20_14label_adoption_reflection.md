# 【CC タスク】14 ラベル化反映 + Phase 0 完了報告 §7.2 確定 (機械的反映・light 枠)

## メタ情報

| 項目 | 値 |
|---|---|
| 発行日 | 2026-05-20 |
| 発行者 | Web Claude (PM エージェント) |
| 承認 | まこさん (2026-05-20・14 ラベル採用確定) |
| タスク種別 | **機械的反映 (新規判断ゼロ・新規 verify ゼロ・新規ガード追加ゼロ)** |
| 想定サイズ | light 枠 80-120 行 (memory ルール 24 / L-198 準拠) |
| 前提タスク | 2026-05-20_learning_design_v3_and_handoff_v16_save (commit e5bcd5b) 完了済 |

## 背景

Phase 0 v3 §3.2 で対称性発見 (LONG_MFE_pct_K ≡ SHORT_MAE_pct_K / LONG_MAE_pct_K ≡ SHORT_MFE_pct_K の数学的恒等式・全 K bit-exact 一致確認済)。学習効果同等・学習時間半減のため、まこさんが **14 ラベル採用 (B 案)** を確定。

前回 commit e5bcd5b で保存された 3 ファイルは旧 28 ラベル前提で書かれているため、14 ラベル前提に上書き更新する。同時に Phase 0 完了報告 §7.2 を「Web Claude 決定待ち」から「14 ラベル B 案確定」に更新する。

## 保存・commit 指示 (memory ルール 19・必須)

本指示書を以下のパスに**そのまま保存し commit する**:

```
.claude/instructions/2026-05-20_14label_adoption_reflection.md
```

完了報告は以下のパス:

```
.claude/instructions/2026-05-20_14label_adoption_reflection_completion.md
```

---

## タスク内容

添付 2 ファイル (14 ラベル化反映済) で前回 commit e5bcd5b の対応ファイルを上書き + Phase 0 完了報告 §7.2 を確定文に書き換える。

### 着手前必読 (3 件・省略禁止)

1. 本指示書本体
2. 添付ファイル 1: `learning_design_v3_final.md` (14 ラベル化反映版・本セッション再生成)
3. 添付ファイル 2: `handoff_to_web_claude_v16_session_20260520.md` (14 ラベル化反映版・本セッション再生成)

---

## Step

### Step 1: 既存ファイル上書き (添付ファイル → リポジトリ内)

| 添付ファイル | 保存先 (既存上書き) |
|---|---|
| `learning_design_v3_final.md` | `.claude/memory/learning_design_v3.md` |
| `handoff_to_web_claude_v16_session_20260520.md` | `.claude/instructions/handoff_to_web_claude_v16_session_20260520.md` |

**ファイル内容は変更しない**。添付ファイルでそのまま上書き。

### Step 2: Phase 0 完了報告 §7.2 を確定文に書き換え

ファイル: `.claude/instructions/2026-05-19_ml_implementation_phase0_1_completion_phase0.md`

§7.2 (現状 L195-202) の表本体を以下に書き換え:

```markdown
### §7.2 ラベル数の選択肢 (Web Claude 判断完了・2026-05-20 まこさん承認)

**確定: B 案 14 ラベル採用**

| 案 | ラベル数 | 学習モデル数 | 状態 |
|---|---:|---:|---|
| A. 元定義通り 28 ラベル | 28 | 28 | ⛔ 不採用 (冗長・学習時間倍増・情報量同じ) |
| **B. 対称性活用 14 ラベル** | **14** | **14** | **✅ 採用** (§3.2 対称性 bit-exact 確認済・学習時間半減・情報量同等) |

採用根拠: §3.2 で全 K・全 3 期間で LONG_MFE_pct_K ≡ SHORT_MAE_pct_K / LONG_MAE_pct_K ≡ SHORT_MFE_pct_K の対称性 bit-exact (diff=0.0000e+00) 確認済。SHORT 側予測値は LONG 側予測値を流用 (推論時)。Phase 5 Replay 時に Funding 非対称性 (median +0.0002%/8h・LONG 払い・SHORT 受取) を方向別適用。

Phase 1 着手指示書は 14 ラベル独立回帰モデル前提で発行する。
```

### Step 3: git commit

```bash
git add .claude/memory/learning_design_v3.md
git add .claude/instructions/handoff_to_web_claude_v16_session_20260520.md
git add .claude/instructions/2026-05-19_ml_implementation_phase0_1_completion_phase0.md
git add .claude/instructions/2026-05-20_14label_adoption_reflection.md
git commit -m "docs: 14ラベル採用確定 (対称性活用) + Phase 0 完了報告 §7.2 更新"
```

`git add .` / `git add -A` 禁止。

### Step 4: 完了報告作成

`.claude/instructions/2026-05-20_14label_adoption_reflection_completion.md` に以下 4 点:

1. 完了フラグ + 更新 3 ファイル + 新規 1 ファイルのパス・行数・更新時刻
2. `ls -la` 4 ファイル
3. `git log -1 --stat` 出力
4. 14 ラベル化が反映された行の grep 確認 (`grep -n "14 ラベル" .claude/memory/learning_design_v3.md`)

---

## 完了報告必須証跡 (light 枠・4 点)

1. **ファイル実体**: `ls -la` 4 ファイル
2. **bit-exact 確認**: `wc -l` + sha256 で添付ファイルとの内容一致
3. **git commit 証跡**: `git log -1 --stat`
4. **14 ラベル化反映確認**: `grep -n "14 ラベル"` で 3 ファイル各々の反映行表示

---

## ガード (light 枠・最小限)

- 添付 2 ファイルの内容変更禁止 (bit-exact 上書きのみ)
- Phase 0 完了報告 §7.2 以外は触らない (本タスクの範囲外)
- git add 単位 (CLAUDE.md L111)
- commit メッセージ日本語簡潔

---

## このタスクで「やらないこと」

- cc_ml_design_spec.md / WORKFLOW.md / phase_compliance_checklist.md の 16 → 14 ラベル機械反映は **別タスク** (handoff v16 §3.2 spec sweep として後続)
- ml_axis_catalog.md / 2026-05-19_ml_design_proposal_v2.md / Phase -1 addendum / self_check addendum 等の旧記述更新も **別タスク**
- memory_user_edits は触らない (Web Claude 側で memory #28 update 完了済)

---

## 次タスク (本タスク完了後・次セッション Web Claude 判断)

handoff v16 §3 pending tasks に従う:
1. 優先 1: Phase 0 完了レビュー本体 (Step 3d 既に完了済・公式 source 物理 view 含む)
2. 優先 2: Phase 0 v3 spec sweep 本体 (16 → **14** ラベル機械反映 + Funding 0.01% 固定 → median baseline 等)
3. 優先 3: Phase 1 着手指示書発注 (**14 ラベル**独立回帰モデル前提・学習内容 v3 §B-15 準拠)

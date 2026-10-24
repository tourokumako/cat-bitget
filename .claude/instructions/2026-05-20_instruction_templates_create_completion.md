# 【完了報告】指示書サイズ規律 3 経路固定

完了日時: 2026-05-20
担当: CC (Claude Code)
対応指示書: `.claude/instructions/2026-05-20_instruction_templates_create.md`

---

## §0 着手前確認 (3 件)

1. `.claude/instructions/2026-05-14_option5v7h_reeval.md` — 376 行・full テンプレの基準元 ✅ 確認
2. `lessons_active.md` memory ルール 24 — 指示書サイズ規律の直接動機 ✅ 確認 (grep で L-198 直前の L-196 確認)
3. 本指示書 `2026-05-20_instruction_templates_create.md` — Step 1-5 全項目 ✅ 読了

---

## §1 Step 1: `.claude/templates/` ディレクトリ作成

```
mkdir -p .claude/templates
ls -la .claude/templates/
# → drwxr-xr-x 2 tachiharamasako staff 64 May 20 18:16 .
```
✅ 作成完了

---

## §2 Step 2: `instruction_template_light.md` 作成

- **内容**: 機械的反映タスク用テンプレ骨格 (80-120 行目安)
- **構成**: 保存先 / 着手前必読 2-3 件 / 背景 / Step 1-N / ガード (1-2 件のみ) / 完了報告 3-4 点 / 構造的チェック / light vs full 判断基準

---

## §3 Step 3: `instruction_template_full.md` 作成

- **手順**: `cp 2026-05-14_option5v7h_reeval.md instruction_template_full.md`
- **一般化変更**:
  - タイトル: `# 【タスク】選択肢 5/7...` → `# 【タスク名】(本テンプレは「verify/audit/新規設計タスク」用・300-400 行目安)`
  - 冒頭: `(監査#10...GO 待ち 2026-05-14)` → `(起案者・YYYY-MM-DD)`
  - 着手前必読 7 件: 具体的パス → `<具体値>` プレースホルダ化
  - 冒頭に「機械的反映タスクは light テンプレを使うこと」の注記追加
- **保持**: 章立て / ガード A-I 構造 / 物理証跡 / 完了報告必須証跡 (骨格は維持)

---

## §4 Step 4: `web_claude_role.md` §1.5.5 追加

**挿入位置**: §1.5 末尾 `---` と `### §1.6 23 軸リストの存在理由` の間
**追加内容 (要点)**:

```
### §1.5.5 指示書サイズ規律 (2026-05-20 追加)

| 種別 | 行数目安 | テンプレ |
|---|---|---|
| 機械的反映 | 80-120 行 | instruction_template_light.md |
| 監査 follow-up / 再設計 | 150-250 行 | light を膨らませて対応 |
| verify / audit 本体 / 新規設計 | 300-400 行 | instruction_template_full.md |
```

### Guard H verify

```
grep -n "指示書サイズ規律" .claude/rules/web_claude_role.md
# → 125: ### §1.5.5 指示書サイズ規律 (2026-05-20 追加)
```
✅ 1 件のみ — 正しい位置に挿入確認

### 前後 5 行確認 (挿入位置確認)

```
L120: これらは全て **デザイン責任の転送**。...
L121:
L122: ---
L123:
L124: (空行)
L125: ### §1.5.5 指示書サイズ規律 (2026-05-20 追加)
...
L148: ### §1.6 23 軸リストの存在理由と参照すべき理由 (絶対遵守・2026-05-19 追加)
```

---

## §5 Step 5: `lessons_active.md` L-198 追加

**ヘッダ更新**: `L-196〜L-103` → `L-198〜L-105` ✅

**L-198 追加位置**: L-196 の直前 (最新教訓として先頭近くに配置)

### Guard H verify

```
grep -n "L-198" .claude/memory/lessons_active.md
# →  1: # lessons_active.md — 直近50件の現役教訓（L-198〜L-105）
# →  5: ### L-198: 指示書サイズ規律違反 — 機械的タスクに full 版 376 行を適用 (2026-05-20)
# → 18: - 3 経路で固定: memory ルール 24 + `web_claude_role.md §1.5.5` + 本 lesson L-198
```
✅ 3 箇所 — ヘッダ + lesson 本体 + How to apply 内参照確認

### 前後 5 行確認 (新規追加)

```
L1:  # lessons_active.md — 直近50件の現役教訓（L-198〜L-105）
L3:  ---
L5:  ### L-198: 指示書サイズ規律違反 — 機械的タスクに full 版 376 行を適用 (2026-05-20)
...
L25: ---
L27: ### L-196: 外部仕様（取引所スペック）を「出典なし」のまま正本扱いした...
```

---

## §6 成果物 6 本 (物理証跡)

| # | ファイル | sha256 | 行数 |
|---|---|---|---|
| 1 | `.claude/templates/instruction_template_light.md` (新規) | `c4722617f564f6715dee5fff2174ea741ffe58dc494f4796a9f261e115ec99a2` | 97 |
| 2 | `.claude/templates/instruction_template_full.md` (新規) | `05ea75708469ac5b34617c89753eee03828350cf1c79a4d02e46f98e4416c276` | 379 |
| 3 | `.claude/rules/web_claude_role.md` (更新版) | `c1ea1959c25c3f69017b420f056096ab9f55b2d6586dd05ab3aee32f06940821` | 455 |
| 4 | `.claude/memory/lessons_active.md` (更新版) | `85979da15ed2a1684b2aef8605cf831c89298cbb37d1379d7a9a0b95d899bab5` | 1904 |
| 5 | `.claude/instructions/2026-05-20_instruction_templates_create.md` (指示書) | — | 25 |

(本 completion report 自体は 6 本目)

**ls -la `.claude/templates/` 出力**:
```
-rw-r--r-- 1 tachiharamasako staff 23990 May 20 18:18 instruction_template_full.md
-rw-r--r-- 1 tachiharamasako staff  3189 May 20 18:17 instruction_template_light.md
```
✅ 2 ファイル存在確認

---

## §7 git diff 自己 verify

変更ファイル一覧 (本タスク範囲):
- `.claude/templates/instruction_template_light.md`: 新規作成 (97 行)
- `.claude/templates/instruction_template_full.md`: 新規作成 (379 行)
- `.claude/rules/web_claude_role.md`: §1.5.5 挿入 (+26 行)
- `.claude/memory/lessons_active.md`: L-198 追加 + ヘッダ更新 (+22 行)
- `.claude/instructions/2026-05-20_instruction_templates_create.md`: 新規 (指示書)

本タスク範囲を超えた変更: なし ✅

---

## §8 3 経路固定確認

| 経路 | 内容 | 状態 |
|---|---|---|
| memory ルール 24 | (前セッションで追加済み) | ✅ 既存 |
| `web_claude_role.md §1.5.5` | 指示書サイズ規律セクション | ✅ 今回追加 |
| `lessons_active.md L-198` | 機械的タスクに full 版適用の失敗事例 | ✅ 今回追加 |
| `.claude/templates/` | light / full 2 テンプレ物理ファイル | ✅ 今回作成 |

次セッション以降: 読了ゲート (web_claude_role.md + lessons_active.md) で §1.5.5 / L-198 が自動発火。

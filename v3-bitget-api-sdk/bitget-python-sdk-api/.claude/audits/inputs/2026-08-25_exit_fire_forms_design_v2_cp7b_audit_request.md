# 【監査依頼】実行器の出口の発火条件を「形ごとの評価」にする設計 v2（97番・cp7 NO-GO の反映版・実装前）の再監査

---

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 5 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-Q4 + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて結果ファイル `.claude/audits/2026-08-25_exit_fire_forms_design_v2_cp7b_audit_report.md` を Write
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / NO-GO / PIVOT / OTHER)
   - 最優先指摘 (Critical) 件数

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)

---

## 監査依頼メタ情報

- 依頼日: 2026-08-25
- 依頼者: CC (起案)。発意＝cp7 の Verdict「検査と完成の条件を直して再提出すれば GO」を受けた再提出
- 監査区分: cp7b（**設計 v2 だけの監査・実装前**。実装は1行も入っていない）
- 監査対象タスク: 実行器（engine_tuner_exec.py）の出口の発火条件の評価を、入口と同じ「形ごとの評価」にする設計の v2
- 結果ファイル保存先: `.claude/audits/2026-08-25_exit_fire_forms_design_v2_cp7b_audit_report.md`
- 入力ファイル保存先 (本依頼書): `.claude/audits/inputs/2026-08-25_exit_fire_forms_design_v2_cp7b_audit_request.md`

---

## 監査依頼の経緯

1. cp7（`.claude/audits/2026-08-25_exit_fire_forms_design_cp7_audit_report.md`）の Verdict＝**NO-GO**（方向は正しい＝維持。Critical 2・Major 5・Minor 1）。
2. 起案 CC が cp7 の指摘を全部 実物で裏取りし（一致＝`.claude/state/session_worklog_20260825.md` §32）、設計書を v2 に書き直した（同 §33）。**v2 の §1b に「監査 §6 の8件 → v2 のどこで直したか」の対応を書いてある。**
3. 実装はまだ1行も入れていない。歯止め（探索の本走をしない）は続いている。

---

## 着手前必読 (省略禁止・auditor 用・5 件)

> パスは、リポジトリの根（cat-bitget/）からのもの。

1. `.claude/state/acceptance.md`（279行）— 監査対象の設計書 v2（未承認・実装前）
2. `.claude/audits/2026-08-25_exit_fire_forms_design_cp7_audit_report.md` — cp7 の報告書（v2 が反映したはずの8件の原文）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py`（4,004行）— 直す対象の実物。特に `FORM_SPEC`（:98-116）・`SIDES`（:136）・`_walk`（:245-271）・`_check_cond`（:783・:858-859）・`_side_cmp`（:1471）・`_vnum_q`（:1494-1507）・`_eval_cond`（:1642-1738）・`validate_recipe` の出口の検査（:1334-1387）・`_collect_fire_cols`（:2036-2052）・`_exit_fire_ok`（:2055-2111）・売買ループ（:2301〜:2386）・`selftest`（:3491）
4. `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py`（5,402行）— 生成器（今回は触らない）。特に `strip_marks`（:813-820）・`_state_cond`（:1632）・`_exit_indicator_cond`（:1656-1726）・`_cond_keys`／`needed_qkeys`（:2404-2461）・案1本を走らせる関数の except（:2759）・`synth_df`（:3386）・T6（:3841-3877）
5. `.claude/state/session_worklog_20260825.md` §32〜§33 — 起案 CC の裏取りと v2 の記録

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = **設計書 v2 が、cp7 の8件を意味を変えずに反映し、かつ「検査が通す × 実行が黙って別物」の型を直した先に残さない設計になっているか**。net の数字・各戦略の性能・engine_tuner のその他の欠陥（96・98〜105番＝next_step §6 で別管理）の判定は対象外。

---

## 監査対象の事実データ

### 対象ファイルの実測（2026-08-25・機械の出力）

| ファイル | 行数 | sha256（先頭16桁） |
|---|---|---|
| `.claude/state/acceptance.md`（v2） | 279 | 8eff7af3b2c16ada |
| `scripts/priority_rebuild/engine_tuner_exec.py` | 4,004 | 8a606184d6ed4cf8（cp7 と同じ＝実装は入っていない） |
| `scripts/priority_rebuild/engine_tuner_gen.py` | 5,402 | 6bf0bc251d9ea521（cp7 と同じ） |

### v2 が cp7 の8件をどこで直したと主張しているか（設計書 §1b からの複写）

Critical-1 → やること3(c)・C1・C7・101番／Critical-2 → やること3(d)・C7・105番／Major-3 → やること2・C13／Major-4 → C6／Major-5 → C3・C8／Major-6 → C11・102番／Major-7 → C12・§7(a)・103番／Minor-8 → やること3(e)(f)・§2 の数と行番号・やること1 の鍵の作り方。

---

## 監査観点 (一般・auditor_template ①〜⑦)

- ①統計学的妥当性
- ②リスク管理
- ③認知バイアス
- ④ソフトウェア工学
- ⑤再現性
- ⑥実行プロセス
- ⑦主エージェントバイアス

---

## 監査観点 (本監査固有・Q1-Q4)

### Q1 — cp7 の8件は、意味を変えずに反映されたか

cp7 §6 の8件（Critical 2・Major 5・Minor 1）を1件ずつ、v2 の該当箇所（§1b の対応表が指す やること・完成の条件・next_step の番号）と突き合わせ、①反映されている ②形だけで中身が無い ③別の意味に変わっている、のどれかを判定せよ。

### Q2 — 直した先に「検査が通す × 実行が黙って別物」が残っていないか（攻撃者の目）

v2 の検査6つ（やること3 の (a)〜(f)）と `_ev` の not の追加で、cp7 が見つけた5件（strict・状態の pre・not・ref・混在）が全部 止まるかを実物の関数（`_check_cond`・`_walk`・`_vnum_q`・`_col_array`）で確かめよ。加えて、**cp7 が見ていない新しい穴**（例＝`FORM_SPEC` の他の欄＝state_free・needs_side・band が出口で意味を持つか／hysteresis・入れ子形が出口の fire に置かれたときの行き先／`any`・`if-then` の中の状態と指標の混在）を探せ。

### Q3 — 完成の条件 C1〜C13 は目的を担保し、書いてあるとおりに測れるか

特に C2（入口の評価器との一致 10組）・C3(ii)（cross の案 ≥1本 の前提）・C6（付け替える道の恒等・基準値を実装の前に測る）・C11（新しい未来参照ゼロ＝H2 全体の担保ではない、と限定した文）・C12（分位の直呼び）について、①満たしても目的に届かない穴 ②測れない・曖昧、を判定せよ。

### Q4 — 設計書 v2 と実物は一致しているか

v2 の §2（行番号・関数名・数）と実物を1件ずつ突き合わせ、食い違いを全部 挙げよ。v2 の中で記述どうしが矛盾している箇所も挙げよ（cp6 の P-1・cp7 の Q3 と同じ観点）。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

内部知識に閉じない。auditor は以下の **外部検索を必ず実施** すること。ChatGPT 等の外部 AI 使用不可 (まこさん課金外)。

### 検索対象 (例・auditor 適宜拡張)

1. **回帰テストの設計（既存の道を別の実装へ付け替えるときの恒等の取り方）**:
   - クエリ案: refactoring characterization test golden master hash comparison before after
   - 期待発見: 付け替えの前に基準値を固定する手順（golden master）の標準と落とし穴
2. **fail-closed のバリデーション設計（許可リスト方式）**:
   - クエリ案: validation allowlist vs denylist fail-closed design rule engine
   - 期待発見: 拒否の列挙（denylist）だけでは新しい穴が残る理由・許可の列挙（allowlist）との使い分け

---

## 結果ファイルフォーマット (auditor 用)

`.claude/audits/2026-08-25_exit_fire_forms_design_v2_cp7b_audit_report.md` に以下 7 セクションを出力:

1. **Step -1 監査対象の型宣言** (文書型: 設計書 v2。実装前)
2. **Step 0 指摘前提確認** (事実データ verify + spec 文言 verify)
3. **観点 ①〜⑦ + Q1-Q4 の所見** (各観点・各 Q に対し「数値根拠ある断言」or「データ不足 (理由)」)
   - 観点 = PASS / FAIL 明示
   - Q = 一致 / 食い違い N 件 明示（該当行の逐語引用つき）
4. **外部検索結果サマリー** (検索クエリ + 主要発見 5-10 件・URL or 論文出典)
5. **総合判定**:
   - Verdict: GO / NO-GO / PIVOT / OTHER
   - 根拠
6. **改善方向性** (具体提案 3-7 件・優先度明示 Critical/Major/Minor)
7. **CC プロセス欠陥対策** (cc_role §1.4.6 改訂提案・該当があれば)

---

## 必ず守ること (auditor 守則)

- **目標 ($1,900/月) 達成可能性判定は対象外**（本監査は設計の監査）
- 月次 NET ≥ $1,900 を下げる方向の提案禁止 (cc_role §1.0 / auditor_template L15)
- 「可能性がある」「かもしれない」「検討の余地」は禁止 (auditor_template L20)
- 数値根拠の断言 or 「データ不足 (理由: 〇〇)」で答える
- 同型バイアス警告: 同一訓練ベース AI として CC の論理に共感しすぎないこと (auditor_template L24-30)
- ChatGPT 等の外部 AI 使用不可
- **外部検索は WebSearch / WebFetch ツールで必ず実施**
- 指摘には必ず**実物の行番号と逐語引用**を付ける（まこさんが英語とコードを読めない前提で、日本語の説明も1行 添える）

---

依頼書終わり。

## まこさん向け呼びかけ例文 (新規セッション起動時)

別 Claude Code セッションを開き、本依頼書のフルパスを明示して以下のように依頼:

```
監査してほしい
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-25_exit_fire_forms_design_v2_cp7b_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

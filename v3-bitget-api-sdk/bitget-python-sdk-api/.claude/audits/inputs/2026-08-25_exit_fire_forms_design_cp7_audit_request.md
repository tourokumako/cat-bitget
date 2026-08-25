# 【監査依頼】実行器の出口の発火条件を「形ごとの評価」にする設計（97番・実装前）の監査

---

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 5 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-Q4 + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて結果ファイル `.claude/audits/2026-08-25_exit_fire_forms_design_cp7_audit_report.md` を Write
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
- 依頼者: CC (起案)。発意＝まこさん決定の手順（実物を読む → 量を出す → 設計書 → **監査** → 承認 → 実装・逐語「その順番でOKなので進めて」）
- 監査区分: cp7（**設計だけの監査・実装前**。★cp6 と違い、実装は1行も入っていない）
- 監査対象タスク: 実行器（engine_tuner_exec.py）の出口の発火条件の評価を、入口と同じ「形ごとの評価」（水準・傾き・交差・差・ローソク）にする設計
- 結果ファイル保存先: `.claude/audits/2026-08-25_exit_fire_forms_design_cp7_audit_report.md`
- 入力ファイル保存先 (本依頼書): `.claude/audits/inputs/2026-08-25_exit_fire_forms_design_cp7_audit_request.md`

---

## 監査依頼の経緯

1. 2026-08-25（60回目）に、**実行器が出口の発火条件で「形」を見ていない**ことが実測で確定した（`next_step.md` §6 の**97番**）。①slope（傾き）は「材料の値 vs 本数 n」の比較に化ける（黙って別物）②cross（交差）は値を解けず案ごと拒否 ③diff は2本目の材料が無視される。実測の記録＝リポジトリ直下 `.claude/state/session_worklog_20260825.md` §25・§27。
2. まこさん決定（逐語 2026-08-25）＝「(う) にして、次のセッションで (あ) をやる」＝(あ)＝実行器を直して出口でも形を見るようにする。**歯止め＝97番が直るまで engine_tuner の探索の本走をしない**（走らせると出口の「傾き」条件の net が嘘になるため）。
3. 61回目（本セッション）に起案 CC が実物を読み、量を出し、設計書 `.claude/state/acceptance.md`（リポジトリ直下）を書いた。**実装はまだ1行も入れていない。**本監査は承認の前・実装の前。

---

## 着手前必読 (省略禁止・auditor 用・5 件)

> パスは、リポジトリの根（cat-bitget/）からのもの。

1. `.claude/state/acceptance.md`（245行）— 監査対象の設計書（未承認・実装前）
2. `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py`（4,004行）— 直す対象の実物。特に `_eval_cond`（:1642-1738＝入口の形ごとの評価）・`_eval_tree`（:1741-1779）・`validate_recipe` の出口の検査（:1334-1387）・`_collect_fire_cols`（:2036-2052）・`_exit_fire_ok`（:2055-2111）・`run_recipe` の呼び出し（:2174・:2301・:2337・:2356・:2371・:2386）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py`（5,402行）— 生成器（今回は触らない）。特に `_state_cond`（:1632）・`_exit_indicator_cond`（:1656-1726）・`_EXIT_LEVEL_CONST`（:1624）・`needed_qkeys` の出口の歩き（:2452-2461）
4. `.claude/state/session_worklog_20260825.md` §25〜§27・§30 — 97番の実測（機械の出力の逐語）と、起案 CC が量を出した記録
5. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/exit_families_rules.json`（906行）— 出口の表の元。指標の条件を持つ枝（REVERSE_IND・BREAKOUT）の fire の欄と confirm_conditions.rule（「閾値は分位」）

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = **設計書 `.claude/state/acceptance.md` が、97番（出口の発火条件が形を見ない＝黙って別物の評価）を、意味を変えずに・穴なく直せる設計になっているか**。net の数字・各戦略の性能・engine_tuner のその他の欠陥（96番・98番ほか）の判定は対象外。

---

## 監査対象の事実データ

### 対象ファイルの実測（2026-08-25・機械の出力）

| ファイル | 行数 | sha256（先頭16桁） |
|---|---|---|
| `.claude/state/acceptance.md` | 245 | 99f2056e79d4fd08 |
| `scripts/priority_rebuild/engine_tuner_exec.py` | 4,004 | 8a606184d6ed4cf8 |
| `scripts/priority_rebuild/engine_tuner_gen.py` | 5,402 | 6bf0bc251d9ea521 |

### 97番の実測（60回目・worklog §27 からの複写・機械の出力の逐語）

```
材料の列の名前: RSI14__5m
  form=slope・side=above・value.n=5 ／ 上がり続ける列（最後の値 90）→ 成立: True
  form=slope・side=above・value.n=5 ／ 下がり続ける列（最後の値 50）→ 成立: True
  form=level・side=above・value.n=5 ／ 上がり続ける列（最後の値 90）→ 成立: True
  form=level・side=above・value.n=5 ／ 下がり続ける列（最後の値 50）→ 成立: True
  form=slope・side=above・value.n=95 ／ 上がり続ける列（最後の値 90）→ 成立: False
  form=slope・side=above・value.n=95 ／ 下がり続ける列（最後の値 50）→ 成立: False
```

＝傾きの向きが逆でも結果が同じ／level と slope の結果が同じ／比べているのは「材料の値」と「value の数字」。

### 設計の骨子（設計書 §4 からの複写）

1. `_collect_fire_cols` を「条件ごとの真偽の配列」の事前計算に置き換える（材料に state を含まない条件を `_eval_cond(c, df, geo, lane, qtable)` で全バー評価・鍵＝条件の canonical JSON）
2. `_exit_fire_ok` の `_ev` の指標の道を「配列の i 番目を引く」に置き換える（玉の状態の条件の1点比較は不変・引数の形も不変）
3. `validate_recipe` に出口の形の検査2つを足す（指標の条件は exit_ok の形だけ／状態の条件は level だけ・fail-closed）
4. 自己テストに「形が効くこと」の実測を足す

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

### Q1 — 完成の条件は目的を担保するか

設計書 §5（完成の条件 C1〜C11）について、①その条件を全部 満たしても目的（出口の発火条件が形を正しく評価し、黙って別物になる評価が残らない）に届かない穴が無いか ②書いてあるとおりに測れない条件・曖昧な条件が無いか、を1件ずつ判定せよ。

### Q2 — 設計の方式に意味を変える穴が無いか（攻撃者の目で）

「条件ごとの真偽の配列を事前に計算し、ループの中で i 番目を引く」方式について、**評価の意味が現行または入口と食い違う道**を実物のコードで探せ。少なくとも次を確かめること＝(a) 分位の解決表（qtable）の鍵は出口の条件のぶんも `needed_qkeys` が集めるか（gen:2452-2461）(b) 欠損の既定（na=fail／na=pass）の扱いが入口と出口で一致するか（exec:1685・:2102-2103）(c) 評価のタイミング（on_close・cross は i-1 と i）に新しい未来参照が無いか（H2）(d) 状態の条件と指標の条件が同じ木に混在するとき・同じ条件が2つの枝に現れるとき、鍵（canonical JSON）の衝突や取り違えが起きないか (e) scope（adds・hold_min・ceil_type）との組み合わせで挙動が変わらないか。

### Q3 — 設計書と実物は一致しているか

設計書の記述（行番号・「実測」の主張・§2 の表・SPEC の関数一覧）を、実物のコードと1件ずつ突き合わせ、食い違いを全部 挙げよ。設計書の中で記述どうしが矛盾している箇所も挙げよ（cp6 の P-1 と同じ観点）。

### Q4 — 97番を独立に再現せよ

設計書の表を写さず、**自分で** `_exit_fire_ok` を直に呼ぶ再現（worklog §27 と同じ型＝上がり続ける列と下がり続ける列）を組み、直す前の実行器で ①slope が向きを見ないこと ②cross が拒否されること ③diff の2本目が無視されること を確かめよ。また、設計書 §5 の C6（恒等＝状態だけの枝は直す前と同じ売買記録）が、回帰を検出するのに十分かを判定せよ。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

内部知識に閉じない。auditor は以下の **外部検索を必ず実施** すること。ChatGPT 等の外部 AI 使用不可 (まこさん課金外)。

### 検索対象 (例・auditor 適宜拡張)

1. **バックテストの出口条件の評価方式（事前のベクトル計算 vs ループ内の逐次評価）**:
   - クエリ案: backtesting exit signal evaluation vectorized precomputed boolean series vs per-bar loop correctness pitfalls
   - 期待発見: 事前計算に切り替えるときの落とし穴（状態依存の条件・シグナルのタイミング・NaN の扱い）
2. **交差（crossover）条件の実装の落とし穴**:
   - クエリ案: crossover signal implementation lookahead bias previous bar comparison NaN handling
   - 期待発見: i-1 と i の比較で入る境界・欠損の扱いの標準

---

## 結果ファイルフォーマット (auditor 用)

`.claude/audits/2026-08-25_exit_fire_forms_design_cp7_audit_report.md` に以下 7 セクションを出力:

1. **Step -1 監査対象の型宣言** (文書型: 設計書。実装前)
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
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-25_exit_fire_forms_design_cp7_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

# 【監査依頼・再監査】M2-C-4＝cp21 の指摘19件を、実際に直せているか

---

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 の件数のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-Q5 + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて結果ファイル `.claude/audits/2026-09-05_m2c4_cp22_reaudit_report.md` を Write
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / NO-GO / PIVOT / OTHER)
   - 最優先指摘 (Critical) 件数

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施

---

## 監査依頼メタ情報

- 依頼日: 2026-09-05
- 依頼者: まこさん（逐語＝「承認したので、速やかに進めて。これ以上ミスをせず、事前に確認をして進めて」）
- 監査区分: CP22（再監査＝cp21 の指摘19件が直っているか）
- 監査対象タスク: M2-C-4（決まった部品と形を実装する）
- 前回の監査: `.claude/audits/2026-09-05_m2c4_add_parts_cp21_audit_report.md`（Verdict＝**NO-GO**・Critical 3・Major 5・Minor 5・プロセス 6）
- 結果ファイル保存先: `.claude/audits/2026-09-05_m2c4_cp22_reaudit_report.md`
- 入力ファイル保存先 (本依頼書): `.claude/audits/inputs/2026-09-05_m2c4_cp22_reaudit_request.md`

---

## 0. この再監査で答えてほしいこと（1行）

**cp21 が挙げた19件のうち、実際に直っているのは何件で、直っていないのは何件か。**そして **CC が「直していない」と自己申告した5件（M2・m4・P5・P6・T-d/T-f の未測定）が、本当に「この回の範囲の外」なのか、それとも逃げなのか。**

---

## 1. 着手前必読（6件・これ以外は参考）

| # | ファイル | なぜ読むか |
|---|---|---|
| 1 | `.claude/audits/2026-09-05_m2c4_add_parts_cp21_audit_report.md` | 前回の指摘19件の本文。★**見出しをそのまま数える**（CC が選り分けた件数を信じない） |
| 2 | `.claude/state/acceptance.md` | 直したあとの設計書（目印 `iter="m2c4-add-parts-20260905"`）。§0-A の対応表・§6 の完成の条件16行・§7 のわざと壊すテスト |
| 3 | `.claude/state/session_worklog_20260904.md` の §36 | CC が出した実測の全部。★**この節の数字を1件ずつ実物と突き合わせる** |
| 4 | `scripts/priority_rebuild/observe_diag.py` | `_mmi`（C2）・`_sr_touch_atr`・`selftest` の T-e（M4）・`_DEMAND_FILES` |
| 5 | `scripts/priority_rebuild/engine_tuner_exec.py` と `engine_tuner_gen.py` | `demand_enabled` と `_material_name`（M1①）・`assert_provenance`（M1②） |
| 6 | `scripts/priority_rebuild/indicator_reference_diag.py` | MMI と S-RタッチATR の既知答え（C2・M3） |

---

## 2. 実測の材料（CC が出した数字・そのまま貼る）

**★この表は CC の自己申告です。監査は1件ずつ実物で確かめてください。**

| # | 完成の条件 | その数字を出したコマンド | CC の申告 |
|---|---|---|---|
| 1 | 需給3種が材料として選べる | `gen_signal_families.py --verify` | 別枠 3枠・需給3件 |
| 2 | MMI の計算が原典と合っている | `observe_diag.py --inspect <5分足CSV> --only 3` | MMI200・300・400・500 とも **既知3/3**。向きを戻すと rc=1（期待 0.502513 ／ 実測 0.0） |
| 3 | MMI が部品として出てくる | 同上 | 0件 → 4件 |
| 4 | 帯の許容幅が ATR に連動する | 同上 | **18件とも 既知2/2**（2水準＝0.5% と 1.0%） |
| 5 | 場面の判定に前処理を付けられる | `verify_design_contract.py` | 道は通った。**実際に組むのは M2-E＝未測定** |
| 6 | 既存のものが1バーも変わっていない | `engine_tuner_exec.py --identity` | **S2 の md5 `7b01f51b5a9b29b3c05a7b340c203ba1`**＝cp21 が名指しした基準値と一致 |
| 7 | 印（G2・H2） | `gen_signal_families.py --verify` ／ `leak_causality_diag.py` | G2＝`d5cdb24a23ac06bb…`（対象38件・25秒）／H2＝`14f11027997dd3a2…`（4分45秒） |
| 8 | わざと壊すテスト | 各コマンドの rc | T-a・T-b・T-c・T-e＝rc=1 ／ **T-d・T-f は未測定** |
| 9 | 文書の食い違いが0件 | `gen_materials.py --verify` | ✅ 一致（在る263／足す0／指紋 `245d3e37e7850ef1`） |
| 10 | 印の「使う」に4件とも入っている | `indicator_switch.json` | 4件とも（`demand_on` に3件） |
| 11 | 凍結された impl_functions | `impl_functions_frozen.json` | **7ファイル・22件** |
| 12 | 禁止事項2 の件数 | `git diff` で `observe_config.json` を見る | 36件 → 38件のまま（cp21 の直しでは並びを足していない） |
| 13 | 設計書と実物の齟齬 | `verify_design_contract.py .claude/state/acceptance.md` | RESULT: PASS |
| 14 | 変更の大きさ | `git diff --stat` | **31 files changed, 2049 insertions(+), 959 deletions(-)** |
| 15 | 選べる列と種類の前後（m5） | `git show HEAD:…materials.md` と いま | 6061列（100.0%）→ 3520列（55.8%）／種類 249 → 140 |
| 16 | 需給が印と型の表の両方と照らされる | `verify_design_contract.py` の must_use | `_material_name` が `demand_enabled` を呼ぶ（AST で PASS）。**壊して落ちるかは未測定** |

**そのほか**＝`engine_tuner_exec.py --selftest` ✅（5秒）／`observe_diag.py --selftest` ✅（1分49秒）／`--inspect --only 3` は指標 573種とも一致検証済み・未検証 0・❌ 0件（1分20秒）。

---

## 3. 監査の問い（Q1〜Q5）

### Q1｜Critical 3件は本当に直っているか

| # | 直したと言っていること | 確かめ方の案 |
|---|---|---|
| C1 | KB の件数を **148件**にし、機械が型の表から書き出す形にした | `regime_detection_kb.md` の `BANS_COUNT_START/END` の中身と、`signal_families.json` の `bans.direction_stateful.parts` ＋ `bans.direction_note.parts` の件数を数えて突き合わせる。**わざと数字を書き換えて `gen_materials.py --verify` が落ちるかも確かめる** |
| C2 | MMI の向きを原典に直し、既知答えを **向きが違うと落ちる見本**に差し替えた | `observe_diag.py` の `_mmi` を原典の C のコードと1行ずつ突き合わせる。**cp21 が挙げた例（9点の並び）で 37.5 と 62.5 のどちらが出るかを、実際に計算して確かめる** |
| C3 | `engine_tuner_exec.py --identity` で S2 の md5 が基準値と一致した | 実際に走らせて md5 を見る。**L1・S1 は測っていない**（CC の申告）＝それが許されるかを判断する |

### Q2｜Major 5件のうち、直していない2件は妥当か

- **M2**（帯の許容幅の上下限）＝CC は「この回では直さず、`next_step.md` §6 の136番に記録して M2-E で実装する」と判断した。**★CC は張り付きの割合を1度も測っていない。**「測る節が観察の道具に無い」という理由が本当かを確かめてほしい。**もし安く測れるなら、それは逃げ**。
- **M5**（禁止事項2 の白黒）＝CC は「実物で確かめて、当たらないと確定した」と言う。根拠2つ（`search_limits.json` の `material_param_ranges` が空／`engine_tuner_gen.py`:290 の `min(vals)`・`max(vals)`）が本当にその結論を支えるかを確かめてほしい。

### Q3｜M1（需給の3層の配線）は、geo と同じ形になったか

- CC は ①`demand_enabled` を新設して `_material_name` で印と照らす ②`assert_provenance` で型の表の `demand_ok` と照らす、の2つを実装した。
- **③生成器が `{"demand": …}` を自分で組み立てる道は作っていない**（理由＝乱数で引く形になるため・違反の記録 #14・#24）。
- **問い**＝この2つで「需給を engine_tuner の材料にする」という やること1 の目的は達せられているか。**それとも、生成器が引けない以上、まだ材料になっていないのか。**

### Q4｜測っていない3件は、本当に「範囲の外」か

| 何 | CC の理由 |
|---|---|
| T-d（前処理を付けた束の部品名を1文字 変える） | 束を組む工程が M2-E だから |
| T-f（印から需給を1件 抜くと G6 が拒否する） | 実行器の自己テストに需給の見本が無く、足すと承認がもう1回 要る |
| M2 の列の実分布 | 張り付き割合を出す節が無い |

**★cp21 の P3 は「駆動側の都合を『検査そのものが走れない』に一般化する」を欠陥として挙げた。**同じ型を繰り返していないかを見てほしい。

### Q5｜プロセス対策 P1〜P4 は、実際に効く形になったか

| # | やったこと | 見てほしい所 |
|---|---|---|
| P1 | KB の件数を機械生成にした | **手で数字を書ける場所が本当に消えたか**（別の文書に同じ数字が手書きで残っていないか） |
| P2 | 完成の条件の表に「その数字を出したコマンド」の欄を足した | 16行とも埋まっているか。**性質の違うコマンドが書かれていないか**（cp21 の C3 と同じ型） |
| P3 | 「測れない」と書いた所を訂正した（`next_step.md` の134番） | 訂正の文が、事実と合っているか |
| P4 | 「まこさん決定」の行に逐語と日付を入れた | 4か所。**逐語が本当に記録に在るか。**うち1か所は「逐語が無いので『まこさん決定』の書き方をやめた」と CC が書いている＝それが妥当か |

---

## 4. 外部検索の要請（1件）

- **MMI（Market Meanness Index）の原典**＝The Financial Hacker。**記事が2本 在る**。①「The Market Meanness Index」（計算の式）②「Boosting Strategies with MMI」（`int MMIPeriod = optimize(0,200,500,100);`）。**CC は cp21 の m1 で出典の記事名を直した。**その直しが正しいかを、原典を開いて確かめてほしい。

---

## 5. 監査に必要な事実（CC が正直に書く）

- **売買は1件も回していません。net はゼロのまま**（この工事は材料と形を足すもので、成績を測る工程ではありません）。
- **累積の試行数は増えていません**（走らせたのは全部「確認する」目的＝`--selftest`・`--verify`・`--identity`・`--inspect`）。
- **CC が「直った」と判定していません**（恒久の決まり64番）。完成の条件の「いまの状態」の欄は全部「未着手」のままです。
- **CC の自己申告の誤りが cp21 で3件 見つかりました**（C1・C2・M4）。今回も同じ型が無いかを疑ってください。

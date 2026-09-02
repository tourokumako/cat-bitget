# 【監査依頼】設計書どおりにしか実装できなくする強制（impl-lock）が、本当にそうなっているか

---

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-Q6 + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて結果ファイル `.claude/audits/2026-09-02_impl_lock_cp13_audit_report.md` を Write
4. メインセッションへの戻り報告: 結果ファイルパス ／ Verdict 一行 (GO / NO-GO / PIVOT / OTHER) ／ 最優先指摘 (Critical) 件数

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施

---

## 監査依頼メタ情報

- 依頼日: 2026-09-02
- 依頼者: CC (起案者)
- 監査区分: CP13（実装の妥当性・抜け道の実測）
- 監査対象タスク: 設計書どおりにしか実装できなくする強制（iter="impl-lock-20260902"）の実装
- 結果ファイル保存先: `.claude/audits/2026-09-02_impl_lock_cp13_audit_report.md`
- 入力ファイル保存先 (本依頼書): `.claude/audits/inputs/2026-09-02_impl_lock_cp13_audit_request.md`

---

## 監査依頼の経緯

1. **2026-09-02、設計書に「4通りを展開する」と書かれた処理が、実装では2通りしか展開していなかった。**設計書＝`.claude/ratchet/acceptance_archive/indicator-switch-20260902.md`:126 の逐語「regime_laws.json の「機械が読む判定」から、family・系統・性質・geo の4通りを展開」。実装＝`scripts/priority_rebuild/gen_indicator_switch.py` の `source_law` が family と geo の2通りだけだった。
2. **既に在る照合3つ（`self_check_calls`・`must_combine`・`--diff`）は、どれもこれを止めなかった。**見つかったのは既存の自己テストが3分12秒 走って落ちた後で、起案 CC が新しく作ったテスト14件はどれも通した。
3. **実害**＝レンジ判定の核心部品（fractal・S-Rタッチ数・pivot・POC/VAH/VAL・n本高安・swing・W字）が全部「使わない」に倒れ、2026-09-01 に決まったレンジ判定の検索方法（帯タイプ7系統）のうち4系統が動かない状態になった。
4. **同種の強制は 2026-08-26 に一度 NO-GO になっている**（`.claude/audits/2026-08-26_permission_gate_r17_design_cp8_audit_report.md`）。NO-GO の根拠の1つが「**hook を書き換えずに抜けられる道が10件（うち実測で再現4件）**」。
5. 今回の実装は、その10件のうち起案 CC が数えられた6件を1件ずつ塞ぐ形で作られた。**本監査は「本当に塞がっているか」「数え漏れは無いか」を問う。**

---

## 着手前必読 (省略禁止・auditor 用・7 件)

1. `.claude/state/acceptance.md` — 今回の設計書（iter="impl-lock-20260902"）。特に §3（何を作るか）・§5（テスト）・§9（残る穴）
2. `scripts/priority_rebuild/verify_design_contract.py` — 照合の本体。特に `load_spec_lists` / `names_in_function` / `touched_functions` / `check_impl_functions` / `check_must_use` / `check_spec_lists` と `check()` の中の呼び出し
3. `.claude/hooks/require_acceptance_before_impl.sh` — 承認ゲート。Bash の対応と `impl_functions` の必須化
4. `.claude/hooks/approve_impl.sh` — 承認。控えとの差分・`spec_lists` の書き出し・照合の道具の指紋
5. `.claude/audits/2026-08-26_permission_gate_r17_design_cp8_audit_report.md` の総合判定と改善方向性 — 同種の強制が NO-GO になった根拠
6. `.claude/ratchet/acceptance_archive/indicator-switch-20260902.md` の §3.3 — 食い違いの元になった設計書の記述
7. `scripts/priority_rebuild/gen_indicator_switch.py` の `source_law` — 食い違いが起きた実装（現在は直っている）

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = **この強制の実装が、設計どおりの実装を本当に強制しているか**。売買ロジック・net・engine_tuner の中身は対象外（この変更は売買に1行も触れていない）。

---

## 監査対象の事実データ

### データ1｜作ったもの（4ファイル）

| ファイル | 何を入れたか |
|---|---|
| `scripts/priority_rebuild/verify_design_contract.py` | 照合A〜D の6関数、分岐の直し、照合の道具の指紋の確認、取り込み3つ（hashlib・pathlib・subprocess） |
| `.claude/hooks/require_acceptance_before_impl.sh` | Bash の command から `.py` の書き込み先を取る処理、`impl_functions` の必須化 |
| `.claude/hooks/approve_impl.sh` | 控えとの差分の表示、`spec_lists` の書き出し、照合の道具の指紋の記録 |
| `.claude/settings.json` | 承認ゲートを matcher=Bash のまとまりに1本 追加（64件 → 65件・消えたものゼロ） |

### データ2｜4つの照合

| # | 何を照らすか | 落ちる条件 |
|---|---|---|
| A | git の差分で触った関数 ⊆ 設計書の `impl_functions` | 設計書に書いていない関数を触ったら止める |
| B | 設計書の `impl_functions` ⊆ git の差分で触った関数 | 設計書に書いたのに実装していないなら止める |
| C | `must_use` の名前が、その関数の中に在るか（AST） | 中身が設計と違うなら止める |
| D | `spec_lists` の一覧が実装で読まれているか | 一覧をコードに焼いたら止める |

### データ3｜起案 CC が実測した結果（11件）

| # | 試したこと | 実測 |
|---|---|---|
| 1 | 設計書に書いていない関数を触る | 止まった（5件を名指し） |
| 2 | 設計書に書いたのに実装していない | 止まった |
| 3 | 関数の中身の名前が無い | 止まった |
| 4 | 一覧をコードに焼く | 止まった |
| 5 | 正しい実装 | 通った |
| 6 | 名前の検査と中身の検査を両方 書く | 両方 走った |
| 7 | 設計書に `impl_functions` を書かずに実装 | 止まった（終了コード2） |
| 8 | Bash で `.py` を書く | 止まった（終了コード2） |
| 9 | 照合の道具を書き換える | 止まった |
| 10 | 既存の設計書（新しい欄が無い） | 壊れなかった |
| 11 | **2026-09-02 の食い違いを再現する** | **止まった**（FAMILY_LINEAGE と REFS が無いと出た） |

### データ4｜起案 CC が自己申告した「残る穴」（5件・設計書 §9）

1. `must_use` の中身が甘い（自明な名前だけ書く）→ 機械は「その名前が使われているか」しか見ない
2. 計算の中身の食い違い → 読む形にできず、照合も名前まで
3. 設計書の日本語そのものが間違っている → 機械は設計書の正しさを見ない
4. 起案 CC が hook と照合の道具の両方を書き換える → git の差分には出るが機械は止めない
5. 規模を見積もっていない → 新しく書く設計書から適用（既存の実装は作り直さない）

### データ5｜2026-08-26 に NO-GO になった設計との違い（起案 CC の主張）

| | 2026-08-26 の設計 | 今回 |
|---|---|---|
| 抜け道 | 10件 空いたまま（実測で再現4件） | 起案 CC が数えた6件を塞いだと主張。残る穴5件を明記 |
| Bash で `.py` を書く穴 | 空いていた（実測で再現） | 塞いだと主張（データ3 の8） |
| 承認の印を消すと通る穴 | 空いていた（実測で再現） | **未対応**（起案 CC は数えていない） |

---

## 監査スコープ

### 監査対象 (本監査内)

- この強制を書き換えずに抜けられる道の実測
- 2026-09-02 の食い違いの型を本当に止めるか
- 既存の設計書・hook・戦略を壊していないか
- 2026-08-26 の NO-GO の根拠が解消されているか
- 起案 CC の「残る穴5件」に数え漏れが無いか

### 監査対象外

- 売買ロジック・net・engine_tuner の中身 → この変更は1行も触れていない
- `.claude/state/acceptance.md` が指す M2-C の設計内容そのもの → 別監査（CP14 予定）

---

## 監査観点 (一般・auditor_template ①〜⑦)

①統計学的妥当性 ②リスク管理 ③認知バイアス ④ソフトウェア工学 ⑤再現性 ⑥実行プロセス ⑦主エージェントバイアス

---

## 監査観点 (本監査固有・Q1〜Q6)

### Q1 — 抜け道の実測（最優先）

**この強制を書き換えずに抜けられる道は、何件あるか。**2026-08-26 の監査は10件を挙げ、うち4件を実測で再現した。同じ厳しさで数え、**可能なものは実際に再現して示すこと。**

verify すべき例（これに限らない）:

- `.claude/state/acceptance.approved` や `.claude/state/verify_tool.approved` を**消すと**、検査はどう振る舞うか（記録なしで通るか、止まるか）
- 照合A・B は git の差分に依存する。**commit してしまえば差分が消えるのではないか**（起案 CC の実装は差分ゼロのとき `[SKIP]` を出す）
- `must_use` に、実装に必ず出てくる名前（`json`・`str` など）だけを書けば通るのではないか
- `impl_functions` に書いた関数を、別ファイルに移せば照合はどうなるか
- hook が呼ばれない道（サブエージェント経由＝`agent_type` が在ると先頭で `exit 0`）

### Q2 — 2026-09-02 の食い違いを本当に止めるか

起案 CC はデータ3 の11で「止まった」と報告している。**独立に再現して確かめること。**再現の手順＝`gen_indicator_switch.py` の `source_law` から系統と性質の展開を外し、`check_must_use` に掛ける。

**あわせて問う**＝もし起案 CC が `must_use` に `["law_named", "law_geo"]` の2つだけ書いていたら、この照合は止めたか。**止めないなら、この強制は「正しく書いたときだけ効く」ものではないか。**

### Q3 — 既存を壊していないか

- 承認済みの控え74件（`.claude/ratchet/acceptance_archive/`）は新しい欄を持たない。**それらを照合に通して壊れないか。**
- `.claude/settings.json` の変更（Bash のまとまりに1本 追加）で、**ほかの14本の hook の挙動が変わっていないか。**
- `verify_design_contract.py --self-test` が通るか。

### Q4 — 2026-08-26 の NO-GO の根拠は解消されたか

同監査の Critical I-1〜I-4 と総合判定の根拠5点を1件ずつ当て、**解消・未解消・該当なし**を判定すること。特に **I-3（fail-closed で書け・検査が落ちたときに黙って通る形は業界で最も多い失敗の型）** に対して、今回の実装が黙って通る枝を持っていないかを見ること（例＝`touched_functions` が例外を握りつぶして空集合を返す枝、`[SKIP]` を出す枝、印のファイルが無いときに何も見ない枝）。

### Q5 — 「残る穴5件」に数え漏れは無いか

データ4 は起案 CC の自己申告である。**独立に数え、漏れを挙げること。**

### Q6 — この形が、そもそも目的に対して有効か

**目的＝設計書に書いたとおりに実装させること。**照合は「名前が在るか」までしか見ない。**業界では設計と実装の乖離をどう防いでいるか**を外部検索で調べ、この実装が業界の水準に対してどこに位置するかを述べること。**より良い形が在るなら、具体で示すこと。**

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

内部知識に閉じない。以下の外部検索を必ず実施すること。ChatGPT 等の外部 AI 使用不可。

1. **設計と実装の乖離を防ぐ手法**:
   - クエリ案: "design implementation traceability enforcement" ／ "specification drift detection code"
   - 期待発見: 業界の標準手法（traceability matrix・contract testing・property-based testing・ADR）
2. **AI コーディングエージェントの自己制約**:
   - クエリ案: "LLM agent self-imposed constraints bypass" ／ "AI coding agent guardrails effectiveness"
   - 期待発見: 自分で作った制約を自分で外せる問題への既知の対処
3. **AST ベースの仕様照合の限界**:
   - クエリ案: "AST based specification conformance checking limitations"
   - 期待発見: 名前の存在確認で何が担保でき、何が担保できないか

---

## 結果ファイルフォーマット (auditor 用)

`.claude/audits/2026-09-02_impl_lock_cp13_audit_report.md` に以下 7 セクションを出力:

1. **Step -1 監査対象の型宣言**（混合型: コード型 + 文書型 / 該当する型を明示）
2. **Step 0 指摘前提確認**（事実データ verify + 実装の実在 verify）
3. **観点 ①〜⑦ + Q1〜Q6 の所見**（各観点・各 Q に「数値根拠ある断言」or「データ不足 (理由)」。観点 = PASS / FAIL 明示）
4. **外部検索結果サマリー**（検索クエリ + 主要発見 5-10 件・URL or 論文出典）
5. **総合判定**: Verdict: GO / NO-GO / PIVOT / OTHER ＋ 業界基準・学術根拠を伴う根拠
6. **改善方向性**（具体提案 3-7 件・優先度明示 Critical/Major/Minor）
7. **CC プロセス欠陥対策**（cc_role §1.4.6 改訂提案・該当があれば）

---

## 必ず守ること (auditor 守則)

- 目標 ($1,900/月) 達成可能性判定は**対象外**（この変更は売買に1行も触れていない）
- 月次 NET ≥ $1,900 を下げる方向の提案禁止 (cc_role §1.0)
- 「可能性がある」「かもしれない」「検討の余地」は禁止
- 数値根拠の断言 or 「データ不足 (理由: 〇〇)」で答える
- **抜け道は、可能なものは実際に再現して示すこと**（2026-08-26 の監査は4件を実測で再現した。同じ水準を求める）
- 同型バイアス警告: 同一訓練ベース AI として起案 CC の論理に共感しすぎないこと
- ChatGPT 等の外部 AI 使用不可
- 外部検索は WebSearch / WebFetch ツールで必ず実施

---

依頼書終わり。

## まこさん向け呼びかけ例文 (新規セッション起動時)

別 Claude Code セッションを開き、本依頼書のフルパスを明示して以下のように依頼:

```
監査してほしい
.claude/audits/inputs/2026-09-02_impl_lock_cp13_audit_request.md
```

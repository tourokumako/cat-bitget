# 【監査依頼】許可制（要件定義に在るものだけを作れるようにする・R17）の設計の監査（実装前）

---

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 5 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-Q5 + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて結果ファイル `.claude/audits/2026-08-26_permission_gate_r17_design_cp8_audit_report.md` を Write
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

- 依頼日: 2026-08-26
- 依頼者: CC (起案)。発意＝**まこさん指示（逐語 2026-08-26）「了解R17を足すでいいよ。この設計を書いたあとに、監査チェックをする」**
- 監査区分: cp8（**設計だけの監査・実装前**。実装は1行も入っていない）
- 監査対象タスク: 設計書 `.claude/state/acceptance.md`＝**要件定義（R1〜R17）に在るものだけを作れるようにする仕組み（許可制）**
- 結果ファイル保存先: `.claude/audits/2026-08-26_permission_gate_r17_design_cp8_audit_report.md`
- 入力ファイル保存先 (本依頼書): `.claude/audits/inputs/2026-08-26_permission_gate_r17_design_cp8_audit_request.md`

---

## 監査依頼の経緯

1. まこさんの問い（逐語 2026-08-24）＝「作ってはいけないものを上げだすとキリがないな。**とにかく要件定義した内容以外のものを作るなという強制のほうがいいのか？**」→ 決定（逐語）＝「**１，許可制にする ２，残す ３，順番は変えない**」。
2. まこさん OK（逐語 2026-08-24）＝「**１はOK**」＝許可制の本体を「番号＋`accept` の逐語を、要件の json からプログラムが差し込む」にする。
3. 57回目（2026-08-24）に起案 CC が設計書を書いたが**未承認のまま**で、実装は1行も入らなかった（控え＝`.claude/ratchet/acceptance_archive/unapproved-permission-gate-20260824.md`）。そのとき残った未決の1件＝「この仕組み自身が要件16件のどれにも当てはまらない」。
4. 63回目（2026-08-26・本セッション）＝まこさん決定「了解R17を足すでいいよ」で **R17 を要件の json に足した**（要件 16件 → 17件）。そのうえで設計書 `.claude/state/acceptance.md` を書いた。**実装はまだ1行も入れていない。**本監査は承認の前・実装の前。

---

## 着手前必読 (省略禁止・auditor 用・5 件)

> パスは、リポジトリの根（cat-bitget/）からのもの。

1. `.claude/state/acceptance.md`（304行）— **監査対象の設計書**（未承認・実装前）
2. `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/verify_design_contract.py`（772行）— 直す対象の実物。特に `extract_block`（:76）・`extract_contract`（:173）・`scan_contracts`（:223）・`spec_from_impl`（:273）・`diff_spec`（:341）・`write_actual`（:377）・`check_approval`（:488）・`check`（:526）・`self_test`（:569）・コマンドの入口（:725〜）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_requirements.json`（438行・要件17件）— 逐語の出どころ。特に R17（末尾）と、1件が持つ8つの欄（`id`／`title`／`source`／`decided`／`why`／`accept`／`state`／`progress`）
4. `.claude/hooks/require_design_contract_before_run.sh`（177行）と `.claude/hooks/require_acceptance_before_impl.sh`（169行）— 止める所の2つ目と3つ目（既存の作り）
5. `.claude/hooks/approve_impl.sh`（44行）と `.claude/hooks/approve_design.sh`（54行）— 止める所の1つ目（承認の作り）

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = **設計書 `.claude/state/acceptance.md` が「要件定義に在るものだけを作れるようにする」を、抜け道なく・既存を壊さずに実現する設計になっているか**。net の数字・各戦略の性能・engine_tuner のその他の欠陥の判定は対象外。

---

## 監査対象の事実データ（2026-08-26・全部 機械の出力の複写。起案 CC の手打ちではない）

### 対象ファイルの実測

| ファイル | 行数 | sha256（先頭16桁） |
|---|---|---|
| `.claude/state/acceptance.md` | 304 | 5cf1c70eacaebd69 |
| `scripts/priority_rebuild/verify_design_contract.py` | 772 | a9628b77cfa5a926 |
| `.claude/ratchet/engine_tuner_requirements.json` | 438 | 030aa8b1ba051d8d |
| `.claude/hooks/approve_impl.sh` | 44 | 1d33a7da3e8404b9 |
| `.claude/hooks/approve_design.sh` | 54 | 05c51ed429684da0 |
| `.claude/hooks/require_acceptance_before_impl.sh` | 169 | 22a0187ac6faf60c |
| `.claude/hooks/require_design_contract_before_run.sh` | 177 | dd68f1ed88b700b9 |

### いま在る設計書の一覧（`verify_design_contract.py --scan-contracts` の出力の複写）

```
読めた契約: 4件
    e35_design.md -> scripts/priority_rebuild/e35_range_oscillation.py
    e37_design.md -> scripts/priority_rebuild/e37_range_scalp.py
    e38_design.md -> scripts/priority_rebuild/e38_priority_stack.py
    acceptance.md -> scripts/priority_rebuild/verify_design_contract.py
読めない契約: 0件
対象外: 6件
```

### 直す前の自己検査（`--self-test` の出力の複写・11/11）

```
  T1 期待どおり : 目印を囲みの見出しに書いた文書を読める
  T2 期待どおり : json の閉じ括弧を消すと読めない側に入る
  T3 期待どおり : impl_file が空だと読めない側に入る
  T4 期待どおり : 目印が文章の中だけの文書は対象外に入る
  T5 期待どおり : 設計の SPEC から関数を1つ消すと『実物にあるが設計に無い関数』で落ちる
  T6 期待どおり : 実物から関数を1つ消すと『設計にあるが実物に無い関数』で落ちる
  T7 期待どおり : 関数の中身を空にすると『呼ぶはずの名前が実物に無い』で落ちる
  T8 期待どおり : 全部そろっていれば通る
  T9 期待どおり : SPEC が無い設計書は『SPEC が無い』と分かる（engine_tuner はこれで止める）
  T10 期待どおり : 設計書を1文字 書き換えると承認が外れる
  T11 期待どおり : --write が書き出した SPEC を使うと、突き合わせが 0件 になる
テスト 11/11 期待どおり
```

### いまの設計書と実物の食い違い（`--diff` の出力の複写・13件＝これから作るもの）

```
齟齬: 13件
    設計にあるが実物に無い関数: check_requirements
    設計にあるが実物に無い関数: extract_requirements
    設計にあるが実物に無い関数: req_coverage
    設計にあるが実物に無い関数: requirement_block
    設計にあるが実物に無い関数: requirements_index
    設計にあるが実物に無い関数: write_requirements
    self_test が呼ぶはずの check_requirements が実物に無い
    self_test が呼ぶはずの req_coverage が実物に無い
    self_test が呼ぶはずの write_requirements が実物に無い
    定数 REQ_MARK が実物に無い
    コマンドの旗 --check-requirements が実物に無い
    コマンドの旗 --req-coverage が実物に無い
    コマンドの旗 --write-requirements が実物に無い
```

### 設計の骨子（設計書 §3 からの複写）

1. 設計書に `REQUIREMENTS: R17` の行を必須にする。
2. その番号の `title`・`decided`・`accept`・`state` を、要件の json から**プログラムが差し込む**（`<!-- REQ_START hash=… -->` 〜 `<!-- REQ_END -->`・形は `gen_windows.py` の `WINDOWS_START/END` と同じ）。
3. 止める所は3つ＝**①承認**（`approve_impl.sh`・`approve_design.sh`）**②実装の書き込み**（`require_acceptance_before_impl.sh`）**③engine_tuner の実行の前**（`require_design_contract_before_run.sh`）。
4. 許可制が掛かる相手＝`.claude/state/acceptance.md` の1本だけ。既存の3本（`e35_design.md`・`e37_design.md`・`e38_design.md`）は対象外にする（＝既存の戦略が走らなくなるのを避けるため）。ただし `--req-coverage` の数え上げには入れる。

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

## 監査観点 (本監査固有・Q1-Q5)

### Q1 — 完成の条件は目的を担保するか

設計書 §6（完成の条件 1〜10）について、①その条件を全部 満たしても目的（要件に無いものを作れない・合格の条件を CC が自分の言葉で書けない）に届かない穴が無いか ②書いてあるとおりに測れない条件・曖昧な条件が無いか、を1件ずつ判定せよ。

### Q2 — 抜け道を探せ（攻撃者の目・最重要）

**この許可制を、CC が「hook のファイルを書き換える」以外の方法ですり抜ける道**を、実物のコードと hook を読んで全部 挙げよ。少なくとも次を確かめること。

- (a) **`REQUIREMENTS:` の行の見分け方**＝全角の記号、大文字小文字、行の途中、複数行に分ける、`REQUIREMENTS:` の後ろが空、番号の重複・空白の混入、などで検査が誤って通る／誤って止まる道が無いか。設計書は「行の先頭・囲みの中と引用は数えない」としか書いていない。
- (b) **差し込みの `hash=` の作り方**＝何を対象にハッシュ値を取るのかを設計書は書いていない。既存の同じ形（`gen_windows.py` の `WINDOWS_START/END`・`gen_improvement_arc.py` の `ARC_TABLE_START`）を読み、**範囲の決め方しだいで書き換えを見逃す道**が無いかを判定せよ。
- (c) **承認の順番**＝承認（`approve_design.sh` がハッシュ値を記録）のあとに設計書を書き換えて実装に入る道が塞がっているか。`check_approval`（`verify_design_contract.py`:488）と組み合わせて判定せよ。
- (d) **hook 側の黙った素通り**＝`require_design_contract_before_run.sh` には過去に「読めないときに何も言わずに通る」穴が在った（同ファイルの冒頭のコメント参照）。新しく足す `--check-requirements` の呼び出しが、同じ型の穴（コマンドが失敗したときに `exit 0` してしまう・出力を捨てる）を作らない書き方になっているかを判定せよ。
- (e) **要件そのものの捏造**＝CC は `engine_tuner_requirements.json` を書き換えられる。要件を自分で足して「許可された」状態を作る道を、何が止めるか（止めないなら、そう書け）。
- (f) **`--req-coverage` の数え方**＝どの設計書を数えるかの決め方（`--scan-contracts` が読めたもの＋`acceptance.md`）で、指していない要件を「指している」と誤って数える道が無いか。

### Q3 — 設計書と実物は一致しているか

設計書の記述（行番号・「実測」の主張・§1 の表・SPEC の関数一覧・DESIGN_CONTRACT）を、実物と1件ずつ突き合わせ、食い違いを全部 挙げよ。**設計書の中で記述どうしが矛盾している箇所**も挙げよ（cp6 の P-1 と同じ観点）。

### Q4 — 既存を壊さないか（独立に再現せよ）

設計書 §7 の4件の主張を、起案 CC の表を写さず、自分で確かめよ。

1. この設計書に上書きした時点で、engine_tuner を指す設計書が0本になり、engine_tuner は走らなくなる（fail-closed）
2. e35・e37・e38 の実行は変わらない
3. H2 の印（`.claude/state/h2_pass.json`・対象21ファイル）と G2 の印（`.claude/state/g2_pass.json`・対象37ファイル）に `verify_design_contract.py` も `engine_tuner_requirements.json` も入っていない＝印の取り直しは要らない
4. 売買記録・net は1バイトも変わらない

**さらに**＝止める所の②（`require_acceptance_before_impl.sh`）に検査を足すと、**いま在る診断の免除（`*_diag.py`）や、既存の戦略ファイルの修正が、意図せず止まる**ことが無いかを、同ファイルを読んで判定せよ。

### Q5 — 範囲の決め方が、CC の裁量が増える方向に寄っていないか

`permanent_rules.md` §0 の3番＝「範囲を決めるとき、私（CC）の裁量が増える読み方を取らない」。
設計書 §3.5 は、許可制の対象を **`acceptance.md` の1本だけ**に決め、既存の設計書3本を外している。この決め方が、①まこさんの指示（「要件定義した内容以外のものを作るな」）に対して狭すぎないか ②起案 CC の裁量が増える方向に寄っていないか ③代わりに取るべき範囲の決め方が在るか、を判定せよ。**判定は「妥当」または「狭すぎる（理由と、代わりの範囲）」のどちらかで断言せよ。**

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

内部知識に閉じない。auditor は以下の **外部検索を必ず実施** すること。ChatGPT 等の外部 AI 使用不可 (まこさん課金外)。

### 検索対象 (例・auditor 適宜拡張)

1. **要件と実装のひも付け（requirements traceability）の標準**:
   - クエリ案: requirements traceability matrix machine enforced commit design document mapping practice
   - 期待発見: 番号のひも付けだけでは「嘘の番号」を止められないことへの、業界での対処（レビュー・双方向の追跡・カバレッジの数え方）
2. **policy as code（決まりをプログラムで強制する）の落とし穴**:
   - クエリ案: policy as code gate bypass failure modes fail-open silent pass CI enforcement pitfalls
   - 期待発見: 検査が「黙って通る」型の失敗（fail-open）の典型と、その防ぎ方
3. **文書に機械が差し込んだ節を守る方法**:
   - クエリ案: generated block in markdown checksum tamper detection managed section pitfalls
   - 期待発見: ハッシュ値の対象範囲の決め方の定石と、見逃しやすい書き換え

---

## 結果ファイルフォーマット (auditor 用)

`.claude/audits/2026-08-26_permission_gate_r17_design_cp8_audit_report.md` に以下 7 セクションを出力:

1. **Step -1 監査対象の型宣言** (文書型: 設計書。実装前)
2. **Step 0 指摘前提確認** (事実データ verify + spec 文言 verify)
3. **観点 ①〜⑦ + Q1-Q5 の所見** (各観点・各 Q に対し「数値根拠ある断言」or「データ不足 (理由)」)
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
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-08-26_permission_gate_r17_design_cp8_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

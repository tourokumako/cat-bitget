# 【監査依頼】CP57 — 段の候補を作る側と測る側の不具合6つを直し、渡す本数を10本にする（実装の監査）

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 18 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて、結果ファイルを次の順で書く（手で1から書かない）:
   - 結果の骨組みを道具で作業場に作る: `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-01_m2f_label_builder_stages_20261001_impl_cp57_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp57_work/cp57_result.md`
   - 骨組みの「<監査が書く>」などの印を全部 埋める（見出しと並びは変えない）
   - 食い違い0件を確かめる: `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-01_m2f_label_builder_stages_20261001_impl_cp57_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>`
   - 出す前に見直す: `python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` で見直し表を作り、全部の行（結果の見出しごと）に ①意味が通じるか ②実物と合うか（根拠＝ファイル名:行番号・実際に開いた行）③争点（この依頼書の結論を決める問い）に合うか と判定（OK／直した／該当なし（理由））を書き、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通す（結果を直したら表を作り直す・hook 11 が同じ照らしを掛ける）
   - 埋めた結果の全文を、結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-01_m2f_label_builder_stages_20261001_impl_cp57_audit_report.md` に Write で1回だけ書く（hook 11 が同じ照らしを掛ける。書いた後は書き替えられない）
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / CONDITIONAL-GO / NO-GO)
   - 重さごとの件数 (Critical / Major / Minor / Process)

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)
- 本物のファイルを書き替えること (写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp57_work/` に作る。最後に `git status --short` で書き替えていないことを示す)

### この監査の作業場

**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp57_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました（CC は依頼書の文を書いていません）。**問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望（逐語）を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・要望の逐語が在る工事だけ）です。

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-01
- 依頼者: CC（起案者）
- 監査区分: 実装の監査
- 監査対象タスク: M2-F-7・M2-F-13b／設計書 m2f-label-builder-stages-20261001
- 監査の相手と版: `.claude/state/acceptance.md` ／ ハッシュ値 cbfd521a0b8f294749bddb4e85f9f97d1d6b1279b368c107e6122e220aaaf853
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-01_m2f_label_builder_stages_20261001_impl_cp57_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-01_m2f_label_builder_stages_20261001_impl_cp57_audit_request.md`

---

## この監査で答えてほしいこと

### 結論を決める問い

- **問い1**＝設計書の実装の指示（23 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けていれば NO。

- **問い2**＝下に並べた まこさんの要望（逐語・5 回の発言・11 行）を、この工事の後の実装が満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。1つでも満たしていなければ NO（Q7 で照らす）。
  - 発言 `req_14b_20260928`（まこさんの発言・外した行と CC の文の引用を除いた 3 行）
    - `req_14b_20260928:V01` 直す範囲は全部
    - `req_14b_20260928:V02` 決めることはCCのおすすめでOK
    - `req_14b_20260928:V03` ではその不具合は修正して、ミッション達成できるようにしてほしい
  - 発言 `req_k1_20260918`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_k1_20260918:V02` →とりあえず１０本にする
    - `req_k1_20260918:V03` 結果を見て変更すると思う
  - 発言 `req_m27_20260928`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_m27_20260928:V04` 了解。状況は理解した。
    - `req_m27_20260928:V05` M2-F-7 の進め方はCCの案でOK
  - 発言 `req_m2_20261001`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_m2_20261001:V01` じゃあ、milestone２の残りを早く進めてくれ。
    - `req_m2_20261001:V02` やってるふりじゃなく、ちゃんと完成しろ
  - 発言 `req_split_20261001`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_split_20261001:V01` なんだそれ。
    - `req_split_20261001:V02` じゃあ修正せずに、分けてすすめれば

(結論を決めるのは、これらの問いだけ。結果の「7. 総合判定」で、問いごとに YES / NO と根拠を書く)

### 結論の決め方

- **GO**＝問い1 と 問い2 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 と 問い2 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 と 問い2 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の逐語と実物の行で示してください。

### この監査の前提

1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（工事のフォルダ `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001`（やることの表.md と、まこさんが OK した案の逐語））に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。
5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。

---

## 監査依頼の経緯

1. 設計書 `m2f-label-builder-stages-20261001`（段の候補を作る側と測る側の不具合6つを直し、渡す本数を10本にする）は、工事のフォルダ `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001`（やることの表.md と、まこさんが OK した案の逐語） から `gen_acceptance.py` が作りました。
2. 設計のもと（やることの番号 M2-F-7・M2-F-13b・逐語のファイル m2f-label-builder-stages-20261001/ok_stages_20261001・m2f-label-builder-stages-20261001/ok_todo_20261001・m2f-label-builder-stages-20261001/okd_stages_20261001・m2f-label-builder-stages-20261001/req_14b_20260928・m2f-label-builder-stages-20261001/req_k1_20260918・m2f-label-builder-stages-20261001/req_m27_20260928・m2f-label-builder-stages-20261001/req_m2_20261001・m2f-label-builder-stages-20261001/req_split_20261001）は、設計書の §0-1 に道具が写しました（CC は写していません）。逐語のファイルは `gen_verbatim.py` がやり取りの記録から抜き出したものです。
3. この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました（CC は依頼書の元データを書いていません）。
4. 承認の印（`acceptance.approved`）は、いまの設計書の sha256 と同じです（同じでなければ、この依頼書は作れません）。
5. 承認した版の設計書の控えは 2 本（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.01.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.md`）。当てる道具が当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2f-label-builder-stages-20261001`）は 23 件。
6. 実装の前＝HEAD の commit e31d6e8（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる） ／ 実装の後＝作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる）（承認の控えを入れた commit と、その親を git から読んだ。控えが commit されていなければ HEAD と作業中の変更）。

---

## 着手前必読 (省略禁止・auditor 用・18 件)

**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `.claude/state/acceptance.md` — 監査の相手（設計書・プログラムが作った）
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/やることの表.md` — 設計書の元（やることの表＝手書きの5項目と割り当ての表）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/要件のまとめ.md` — 要件のまとめ（まこさんの逐語と OK された案）
4. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/ok_stages_20261001.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
5. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/ok_todo_20261001.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
6. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/okd_stages_20261001.txt` — まこさんが OK した CC の文（逐語・gen_verbatim.py が記録から抜き出した）
7. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/req_14b_20260928.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
8. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/req_k1_20260918.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
9. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/req_m27_20260928.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
10. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/req_m2_20261001.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
11. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/req_split_20261001.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
12. `SDK/.claude/ratchet/m2_todo.json` — やることリスト（番号 M2-F-7・M2-F-13b の行）
13. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.01.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
14. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
15. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:m2f-label-builder-stages-20261001 の行）
16. `SDK/scripts/priority_rebuild/engine_tuner_gen.py` — 直す相手
17. `SDK/scripts/priority_rebuild/regime_r9_diag.py` — 直す相手
18. `SDK/scripts/priority_rebuild/recipes/search_limits.json` — 直す相手

★直す相手になりうるファイルを必ず入れる (結果の「修正の指示」の「直す前の文字」を、監査が実物から写すため)。プログラムが作る文書 (設計書など) を監査するときは、その元データ (設計書なら、工事のフォルダ `.claude/state/verbatim/<工事名>/` の `やることの表.md`。承認の後は `SDK/.claude/ratchet/acceptance_archive/verbatim/<工事名>/`) も入れる。`acceptance_src.json` は 2026-09-30 から使っていない (ratchet に無い) ので、直す相手に書かない。

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = 設計書 `m2f-label-builder-stages-20261001` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。あわせて、まこさんの要望（逐語）を、この工事の後の実装が満たしているか（問い2・Q7）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `m2f-label-builder-stages-20261001` の中身です。

---

## 監査対象の事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | stage_keep_of の上端の検査（B-1） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | stage_keep_of の説明の文（B-1） | 直した後の文字 |
| 3 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | sample_regime_build の off_c（B-2） | 直した後の文字 |
| 4 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | build_stage_candidates の見た条件の入れ物（B-5） | 足す文字 |
| 5 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | build_stage_candidates の条件を作った後（B-5） | 足す文字 |
| 6 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | STAGE_SPEC の段1（B-6） | 直した後の文字 |
| 7 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | STAGE_SPEC の段2c（B-6） | 直した後の文字 |
| 8 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | selftest の前に、T48 の本体 selftest_stages を足す（B-1・B-2・B-5・B-6） | 直した後の文字 |
| 9 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | selftest の T46 の後ろで T48 を呼ぶ（B-1・B-2・B-5・B-6） | 足す文字 |
| 10 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 旗 --selftest-stages を足す | 足す文字 |
| 11 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 旗 --selftest-stages の口 | 足す文字 |
| 12 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | _loosened_off の not の中身の緩める向き（B-2） | 直した後の文字 |
| 13 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_stage の前に、段1 の両側と差し戻しの枠の関数を足す（B-3・B-4） | 直した後の文字 |
| 14 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_stage の段1 で両側の帯を測る（B-3） | 足す文字 |
| 15 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の _measure_one の印に枠も持たせる（B-4） | 直した後の文字 |
| 16 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の枠の入れ直し（B-4）（1/6） | 直した後の文字 |
| 17 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の枠の入れ直し（B-4）（2/6） | 直した後の文字 |
| 18 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の枠の入れ直し（B-4）（3/6） | 直した後の文字 |
| 19 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の枠の入れ直し（B-4）（4/6） | 直した後の文字 |
| 20 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の枠の入れ直し（B-4）（5/6） | 直した後の文字 |
| 21 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の枠の入れ直し（B-4）（6/6） | 直した後の文字 |
| 22 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | selftest の⑤の前に ⑭⑮⑯ を足す（B-2・B-3・B-4） | 直した後の文字 |
| 23 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | stage_keep_range の hi（K-1） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:m2f-label-builder-stages-20261001）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 2 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 3 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 4 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 5 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 6 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 7 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 8 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 9 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 10 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 11 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 12 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 13 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 14 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 15 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 16 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 17 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 18 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 19 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 20 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 21 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 22 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 23 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-01T17:54:40 |

---

## 監査スコープ

### 監査対象 (本監査内)

- Q1：実装の指示を当てた結果が、実装の後と1文字も同じか
- Q2：実装の指示のどれにも当たらない行（設計書に無い変更）が無いか
- Q3：当てた記録が、実装の指示の全部と1件ずつ合うか
- Q4：承認した版の設計書どうしで、実装の指示が同じか
- Q5：実装の指示が、やることの表の要件を全部 満たすか
- Q6：完成の条件が、実装の後に本当に成り立つか
- Q7：まこさんの要望（逐語）を、この工事の後の実装が満たしているか（問い2）

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- 答え合わせの札の構造（14a＝札の部品・設定・版）を、この工事に入れない（案が1回の返信に収まらない（実装の指示が約10万文字）。別の工事に分ける）
- 固定のレシピ r9_demand_fixture.json の出る線を直さない（このレシピは需給の列が足されるかを測るための物で、出る線の向きは測る中身に関係しない。直すと、直す前と同じ結果が出ることを確かめる条件（壊すプログラム b97）が崩れる）
- 段の走行（M2-F-8〜15）は、この工事の実装に入れない（実装の後に、時間の見込みをフロー宣言に書いてから走らせる（恒久60〜62番））

---

## 監査観点 (一般・auditor_template ①〜⑦)

該当なし（この監査は、実装が設計書のとおりかと、まこさんの要望を満たしているかだけを問う。①〜⑦の観点は、この争点に関係しない。結果の所見の「一般の観点」にも「該当なし」と書く）

---

## 監査観点 (本監査固有・Q1-QN)

★問いごとに優先度を付ける＝A（結論を変える）／B（実装の前に直す）／C（完成の測り方以外の書き漏れ）／D（結論に効かせない）。結果の所見は、この問いの番号をそのまま見出しにし、優先度の順に書く。時間が足りずに省いた問いは、結果にその番号を書く。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**優先度の理由**＝違えば、実装は設計書のとおりに作られていない

実装の前（HEAD の commit e31d6e8（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる））の対象のファイル（`SDK/scripts/priority_rebuild/engine_tuner_gen.py`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`・`SDK/scripts/priority_rebuild/regime_r9_diag.py`）に、設計書 4-20 の実装の指示（23 件）を番号の順に当てた結果が、実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる））と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**優先度の理由**＝在れば、設計書に無い変更が実装に混ざっている

実装の前（HEAD の commit e31d6e8（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる））と実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる））の差分（`SDK/scripts/priority_rebuild/engine_tuner_gen.py`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`・`SDK/scripts/priority_rebuild/regime_r9_diag.py`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**優先度の理由**＝合わなければ、どの件を道具が当てたかを後から確かめられない

当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2f-label-builder-stages-20261001`）が、実装の指示の 23 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**優先度の理由**＝当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない

承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.01.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.md`）と、いまの設計書の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**優先度の理由**＝要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない

実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**優先度の理由**＝成り立たなければ、承認のときの「済」が根拠にならない

設計書の完成の条件（3 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest-stages`・`python3 scripts/priority_rebuild/regime_r9_diag.py --selftest`・`jq '.stage_keep_range.hi' scripts/priority_rebuild/recipes/search_limits.json`

### Q7 — まこさんの要望（逐語）を、この工事の後の実装が満たしているか（問い2）（優先度 A）

**優先度の理由**＝満たしていない要望が在れば、まこさんの要望が届いていない（この答えが問い2 の答えになる）

下に並べた まこさんの要望（逐語）を、この工事の後の実装が満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。この問いの答えが、結論を決める問い2 の答えになる。

  - 発言 `req_14b_20260928`（まこさんの発言・外した行と CC の文の引用を除いた 3 行）
    - `req_14b_20260928:V01` 直す範囲は全部
    - `req_14b_20260928:V02` 決めることはCCのおすすめでOK
    - `req_14b_20260928:V03` ではその不具合は修正して、ミッション達成できるようにしてほしい
  - 発言 `req_k1_20260918`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_k1_20260918:V02` →とりあえず１０本にする
    - `req_k1_20260918:V03` 結果を見て変更すると思う
  - 発言 `req_m27_20260928`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_m27_20260928:V04` 了解。状況は理解した。
    - `req_m27_20260928:V05` M2-F-7 の進め方はCCの案でOK
  - 発言 `req_m2_20261001`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_m2_20261001:V01` じゃあ、milestone２の残りを早く進めてくれ。
    - `req_m2_20261001:V02` やってるふりじゃなく、ちゃんと完成しろ
  - 発言 `req_split_20261001`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_split_20261001:V01` なんだそれ。
    - `req_split_20261001:V02` じゃあ修正せずに、分けてすすめれば

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

件数: 0 件 (結果の外部検索の節にも「該当なし」と書く)

該当なし（この監査は、実装が設計書のとおりかを実物で照らす。外部の知見は答えに要らない。設計の理由を調べる外部検索は、設計書の監査で行う）

---

## 依頼を出した CC の自己申告

1. **承認の後に設計書を作り直した**＝前の版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.01.md` と いまの版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.md` の違い＝ACC_CODEREF の囲みの中で 6 行・ACC_SPEC の囲みの中で 13 行・囲みの外で 6 行（実装の指示の囲み ACC_IMPL は同じ）
2. **この工事の外の作業中の変更**＝`.claude/hooks/enforce_audit_docs.py`・`.claude/hooks/enforce_g2_pass.py`・`.claude/hooks/enforce_h2_pass.py`・`.claude/hooks/require_acceptance_before_impl.sh`・`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_confirm_before_act.py`・`.claude/hooks/require_read_plan_before_design.py`・`.claude/hooks/require_read_used.py`・`.claude/hooks/require_read_used.sh`・`.claude/hooks/require_request_understood.sh`・`.claude/tools/gen_audit_docs.py`・`.claude/tools/gen_review.py`・`.claude/tools/gen_verbatim.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）

(結果は、この番号ごとに1件ずつ答える)

---

## 結果ファイルフォーマット (auditor 用)

`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-01_m2f_label_builder_stages_20261001_impl_cp57_audit_report.md` に、次の 11 節をこの順で出力する。★節の名前と並びは変えない。どの種類の監査でも同じ。

| # | 結果の節 | 依頼書の対応する項目 |
|---|---|---|
| 1 | **監査の相手と版**（依頼書のパス・監査の相手・ハッシュ値を照らした結果・実施日） | 監査依頼メタ情報 |
| 2 | **監査対象の型宣言**（数値型・コード型・文書型のうち該当するもの全部） | —（結果だけ） |
| 3 | **監査対象の事実データの確認**（依頼書の事実データを、自分で確かめた結果） | 監査対象の事実データ |
| 4 | **所見**（依頼書の問いの番号をそのまま見出しにし、依頼書の優先度の順に書く。一般の観点 ①〜⑦ は PASS / FAIL。各所見の末尾に、対応する修正の番号を書く。直し方の文は書かない。省いた問いは番号を書く） | 監査観点（一般・本監査固有）と優先度 |
| 5 | **外部検索**（依頼書の件数の検索対象に1つずつ・URL と逐語） | 外部検索要請 |
| 6 | **依頼を出した CC の自己申告への答え**（依頼書の番号ごとに1件ずつ） | 依頼を出した CC の自己申告 |
| 7 | **総合判定**（結論を決める問いへの答え〔問いごとに YES / NO と根拠〕・下の「結論の決め方」の3つのどれか・重さごとの件数） | この監査で答えてほしいこと・auditor 宣言の戻り報告 |
| 8 | **修正の指示**（下の「修正の指示の書き方」の形だけで書く。重さは Critical・Major・Minor） | 着手前必読（直す相手のファイル） |
| 9 | **CC プロセス欠陥対策**（下の「修正の指示の書き方」の形だけで書く。重さは Process） | —（結果だけ） |
| 10 | **開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由** | 着手前必読 |
| 11 | **本物のファイルを書き替えていないこと**（`git status --short` の出力） | auditor 宣言の禁止（本物を書き替えない） |

依頼書だけの項目＝監査依頼の経緯・この監査の前提・この監査の作業場・大目的・監査スコープ・必ず守ること。

### 結論の決め方

依頼書の「この監査で答えてほしいこと」に結論の決め方が在れば、それを使う。無ければ次の3つ。

- **GO**＝Critical が0件。
- **CONDITIONAL-GO**＝Critical が在る。直せば先に進める。
- **NO-GO**＝直し方の向きが違う。何が違うかを、4 の所見で、指摘の文と実物の行で示す。

### 重さの決め方

- **Critical**＝結論を変える。
- **Major**＝直すべきだが、結論は変えない。
- **Minor**＝結論に効かせない（前の「別枠」もここに入れる）。
- **Process**＝CC の進め方の欠陥。9 に書く。

### 修正の指示の書き方（★この形以外では書けない）

- **目的**：監査が書いた修正方法のとおりに、CC の改ざん・虚偽・矮小化・不正を通さずに直すため。
- **監査の種類**：設計書の内容確認、設計書どおりに実装できているかの確認など、どの種類の監査でも同じ欄で書く。
- **直す相手**：設計書・コード・実装データ（設定・json・法則ファイルなど）・文書・走らせるコマンドなど。どの相手の直しも同じ欄で書く。
- **直し方**：どの修正指示も、プログラムがそのまま実行できる形で書く。プログラムが欄のとおりに直しを当てる。CC は文も数も打たない。
- **直す範囲**：まこさんが結果ファイルを見て決める（Critical だけか、Major もか、Minor もか）。そのため修正は、重さの見出し（「### Critical」「### Major」「### Minor」「### Process」）の下に並べる。Process は 9 に書く。
- **所見との結び付き**：修正の番号は、4 の所見の末尾に書いた番号と同じにする。所見の無い修正は書かない。所見に書いた修正の番号は、必ず 8 か 9 に在るようにする。

1件は次の形で書く。

```text
### Critical

#### 修正 <番号>
対象のファイル: <リポジトリの中のパス>
直す箇所: <監査が読んだ時点の行番号の範囲>
直す前の文字:
~~~
<実物から1文字も変えずに写す>
~~~
直した後の文字:
~~~
<そのまま当てられる全文>
~~~
根拠の抜き書き: <ファイル名>:<行番号>「<その行の逐語>」
状態: <確定 / 未決 / 案が複数 のどれか>
```

**欄の決まり（6つ）**

1. **対象のファイル**：直すファイルを1つだけ書く。プログラムが作る文書（設計書など）は書けない。その文書の元データの直し1件と、作り直すコマンド1件の2件に分けて書く。作り直すコマンドの件は、元データを直す件と同じ重さの見出しの中で、その件のすぐ後ろに書く。
2. **直す箇所**：監査が読んだ時点の行番号の範囲。走らせるコマンドのときは「なし」。
3. **直す前の文字**：対象のファイルの中で1か所だけに当たる文字を、実物から写す。新しいファイルを作るときと、走らせるコマンドのときは「なし」。
4. **直した後の文字**：見出しを次の4つから1つ選ぶ。
   - **直した後の文字**：直す前の文字を、この全文に置き換える。
   - **足す文字**：直す前の文字のすぐ後ろに足す。新しいファイルを作るときは、ここに全文を書く。
   - **消す文字**：直す前の文字の中から、この文字を消す。
   - **走らせるコマンド**：1行のコマンドをそのまま書く。承認のスクリプトなど、まこさんが打つコマンドもここに書く。監査が走らせたときにかかった時間を、根拠の抜き書きに書く（恒久61番）。
5. **根拠の抜き書き**：「ファイル名:行番号」と、その行の逐語。
6. **状態**：「確定」「未決」「案が複数」の3つだけ。
   - **未決**：まこさんが決めるもの。
   - **案が複数**：4の欄を「案A」「案B」のように、案の数だけ並べる。

**プログラムが止めて、まこさんに報告するとき（2つだけ）**

1. 直す前の文字か、根拠の抜き書きが、実物と合わないとき。
2. 状態が「未決」か「案が複数」のとき。

止めた後どうするかは、まこさんが決める。

**書けないもの**

- 行番号と向きだけの指示（例＝「78-114行を〜の形にする」）。
- 散文の「修正の方向性」「直し方（案）」「対策＝〜にする」。
- 取り下げ。一度出した結果ファイルに、あとから指示の取り下げを書き足さない。
- 1件に2つ以上のファイル。ファイルごとに件を分ける。
- 行ごとに残す・直す・消す・足すを並べた表。1行を1件にする。

**当てる順番**＝修正の番号の順。

---

## 必ず守ること (auditor 守則)

- 目標 ($1,900/月) の達成可能性の判定＝該当なし（この監査は、実装が設計書のとおりかを照らす）
- 月次 NET ≥ $1,900 を下げる方向の提案禁止 (cc_role §1.0 / auditor_template L15)
- 「可能性がある」「かもしれない」「検討の余地」は禁止 (auditor_template L20)
- 数値根拠の断言 or 「データ不足 (理由: 〇〇)」で答える
- 同型バイアス警告: 同一訓練ベース AI として CC の論理に共感しすぎないこと (auditor_template L24-30)
- ChatGPT 等の外部 AI 使用不可
- 外部検索＝該当なし（この監査では外部検索を求めない）
- トレードの外部認知＝該当なし（この監査は、実装が設計書のとおりかを照らす）

---

依頼書終わり。

---

## まこさん向け呼びかけ例文 (新規セッション起動時)

別 Claude Code セッションを開き、本依頼書のフルパスを明示して以下のように依頼:

```
監査してほしい
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-01_m2f_label_builder_stages_20261001_impl_cp57_audit_request.md
```

または

```
本依頼書を読んで監査して
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-01_m2f_label_builder_stages_20261001_impl_cp57_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp57_work/cp57_src.gen.md src_sha256=6ef4f8dc1b1a318b8ef81e97846d419fa648758208b7f8bc92058ea5fca25f51 body_sha256=9f8a44ea3f27d9d1c24812448e759d8d0690731e7d9753488410f774b348a26e -->

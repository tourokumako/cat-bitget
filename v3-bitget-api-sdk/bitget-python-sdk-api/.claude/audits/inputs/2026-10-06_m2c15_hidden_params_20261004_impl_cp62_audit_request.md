# 【監査依頼】CP62 — 指標の修正の2つ目の工事＝パラメータを、名前に出さない引数で受け取る形にする。M2-C-15（実装の監査）

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 26 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて、結果ファイルを次の順で書く（手で1から書かない）:
   - 結果の骨組みを道具で作業場に作る: `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-06_m2c15_hidden_params_20261004_impl_cp62_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp62_work/cp62_result.md`
   - 骨組みの「<監査が書く>」などの印を全部 埋める（見出しと並びは変えない）
   - 食い違い0件を確かめる: `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-06_m2c15_hidden_params_20261004_impl_cp62_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>`
   - 出す前に見直す: `python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` で見直し表を作り、全部の行（結果の見出しごと）に ①意味が通じるか ②実物と合うか（根拠＝ファイル名:行番号・実際に開いた行）③争点（この依頼書の結論を決める問い）に合うか と判定（OK／直した／該当なし（理由））を書き、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通す（結果を直したら表を作り直す・hook 11 が同じ照らしを掛ける）
   - 埋めた結果の全文を、結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-06_m2c15_hidden_params_20261004_impl_cp62_audit_report.md` に Write で1回だけ書く（hook 11 が同じ照らしを掛ける。書いた後は書き替えられない）
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / CONDITIONAL-GO / NO-GO)
   - 重さごとの件数 (Critical / Major / Minor / Process)

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)
- 本物のファイルを書き替えること (写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp62_work/` に作る。最後に `git status --short` で書き替えていないことを示す)

### この監査の作業場

**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp62_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました。**判断が要る4つ（この工事は何のためか・必読・工事ごとの問い・要望のまとめ）は、CC が工事のフォルダの 監査依頼の手書き（実装の監査）.md に書き、まこさんが OK した文を写しました。ほかは道具が実物から作りました。問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・まこさんの要望が在る工事だけ）と、この工事で確かめてほしいことを問う工事ごとの問い（Q8〜Q12）です。

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-06
- 依頼者: CC（起案者）
- 監査区分: 実装の監査
- 監査対象タスク: M2-C-15／設計書 m2c15-hidden-params-20261004
- 監査の相手と版: `.claude/state/acceptance.md` ／ ハッシュ値 9c82c505833fd09a06f98bca7b4c981fe1a9fea6d2ceb850336cbd52e8012753
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-06_m2c15_hidden_params_20261004_impl_cp62_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-06_m2c15_hidden_params_20261004_impl_cp62_audit_request.md`

---

## この監査で答えてほしいこと

### 結論を決める問い

- **問い1**＝設計書の実装の指示（56 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。あわせて、この工事で確かめてほしいこと（Q8〜Q12 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けている・工事ごとの問いで設計書と違う所が見つかれば NO。

(結論を決めるのは、この問いだけ。結果の「7. 総合判定」で、問いごとに YES / NO と根拠を書く)

### 結論の決め方

- **GO**＝問い1 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の番号と実物の行で示してください。

### この監査の前提

1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-hidden-params-20261004/やることの表.md`）に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。
5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。

---

## 監査依頼の経緯

1. **この工事は何のためか**＝指標・閾値・パラメータ・時間足の4つを、役割に基づき法則に則って組み合わせて、Entry・Exit やレジーム判定の条件を作れる状態にする（6項目）。6項目の3番（パラメータが、範囲から探されている）のために、指標がパラメータを受け取れる状態にする。この工事は、その指標の側の土台＝47種類の登録が、パラメータを「名前に出さない引数」で受け取る形にする（何も渡さなければ今と同じ計算）。探す側（engine_tuner）が範囲から渡す仕組みは、次の工事2
   指標の名前に閾値やパラメータの値を固定で入れて指標の数を増やす形は取らない。151回目に名前に値が入った EMA の傾き4種と、値違いの列を足した AO を、名前に値を入れない形へ戻す（AO は AO% の1列・まこさん「A」）
   CKSP の値の組を TradingView の形（10・1・9・rma）にそろえる（まこさん「２はC」）。前の工事の RCI を「使う」にする直しと、検査2 の上位足のずらし bar_close の確かめを、外されても落ちる番人で守る（監査 CP61 の Q10）
2. **この工事は何か**＝指標の修正の2つ目の工事です。指標が、パラメータを受け取れる状態にします。中身は4つです。①資料のパラメータを受け取っていない指標を、パラメータを「名前に出さない引数」で受け取る形にする（何も渡さなければ今と同じ計算。名前も種類の数も変えない）。傾きの比べる本数も同じ形にする（H-1）。②CKSP の値の組を、TradingView の形にそろえる（まこさん「２はC」・H-2）。③151回目に名前に値が入った EMA の傾きと、値違いの列を足した AO を、名前に値を入れない形へ戻す（AO は、まこさん「A」・H-3）。④RCI を「使う」に保つ番人と、検査2 の上位足のずらしの確かめを守る番人を足す（H-4）。列の値が変わるのは、CKSP の2列だけです。名前が変わるのは、EMA の傾きと AO だけです。探す側（engine_tuner）へつなぐ直しは、この工事に入れません（工事2）。最後に表を作り直し、型の表を再承認していただき、自己テスト・G2・H2 を取り直します。（やることの番号 M2-C-15）
   **この工事の位置**＝全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝材料を直す（監査 CP60 の修正・法則どおりの帯の部品・S1 の部品） → この工事

---

## 着手前必読 (省略禁止・auditor 用・26 件)

**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `.claude/state/acceptance.md` — 監査の相手（設計書・プログラムが作った）
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-hidden-params-20261004.01.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-hidden-params-20261004.02.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
4. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-hidden-params-20261004.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
5. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:m2c15-hidden-params-20261004 の行）
6. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-hidden-params-20261004/やることの表.md` — 設計書の元（やることの表）＝修正の指示を書く先
7. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — 目標（全月 net ≥ $1,900）と全体戦略、ハード制約（§4.6＝H2 未来参照なし ほか）。引数を受け取る形にした計算式が未来を使わないかを照らす
8. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-103） — engine_tuner の目的と、作ってはいけないもの（乱数・探す値を点の一覧で限定するもの）
9. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:95-146） — M2 が M1〜M6 のどこに当たり、何ができたら終わりか
10. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:3-46・:995-1040） — M2 で作っている物と、この工事（M2-C-15＝材料を直す）の行
11. `.claude/state/acceptance.md`（全文） — 承認済みの設計書（実装の指示56件・完成の条件6行は ✅済・承認のプログラムが測った）
12. `SDK/scripts/priority_rebuild/observe_diag.py`（:355-390・:636-680・:790-1000・:1100-1280・:1360-1375・:1465-1495・:6925-7075） — 名前に出さない引数を受け取る登録と自前の関数（_vp_levels・_mama・_ck・_ps・_ab・_acb・_cel・_hw）・材料の一覧（EMA の傾き・AO）・新しい番人 _insp_hidden_params・軽い口 selftest_catalog に足した番人5つ
13. `SDK/scripts/priority_rebuild/indicator_reference_diag.py`（:315-320・:832-838・:1055-1072・:1433-1440・:2523-2540） — 参照表の EMA の傾きと AO の行（名前の型と、名前に本数が無いときの値）・RCI の行の mako の欄
14. `SDK/scripts/priority_rebuild/observe_config.json`（:130-170） — 外した設定（ema_slope_lookbacks・ao_params）の周り。残っている設定が当てる前と同じか
15. `SDK/scripts/priority_rebuild/gen_signal_families.py`（:90-135） — 型の表の禁止3（標本不足）の n_eff が、部品の名前の数字から計算されること（Q11 の元）
16. `SDK/.claude/ratchet/signal_families.md`（全文） — 作り直して再承認された型の表（部品 576種・禁止3 514組）。前の版（577種・516組）との差
17. `SDK/.claude/ratchet/indicator_switch.json`（全文） — 作り直した後の印。使う 145種・使わない 116種（前と同じ）
18. `.claude/breaks/b132_hidden_param_not_passed.sh` — 壊すプログラム。HWMA の登録が受け取った引数を渡さないと、番人が落ちるか（Q10）
19. `.claude/breaks/b133_cksp_mixed_set.sh` — 壊すプログラム。CKSP を引数なしの呼び方に戻すと、番人が落ちるか（Q10）
20. `.claude/breaks/b134_ao_name_with_value.sh` — 壊すプログラム。AO の名前に値を入れると、番人が落ちるか（Q10）
21. `.claude/breaks/b135_rci_mako_gone.sh` — 壊すプログラム。参照表の RCI の行から mako の欄を外すと、番人が落ちるか（Q10）
22. `.claude/breaks/b136_insp2_bar_close_dropped.sh` — 壊すプログラム。検査2 から bar_close の確かめを外すと、番人が落ちるか（Q10）
23. `.claude/breaks/b128_k1_copc_back_in_ao_loop.sh` — 書き直した壊すプログラム。COPC の組の並びを入れ替えると、K-1 の番人が落ちるか（Q10）
24. `.claude/state/reviews/acceptance.review.md`（全文） — CC の見直し表（止める理由0件）
25. `.claude/state/session_worklog_20261006.md`（:3-14・:24-53） — この工事の当て方・止まった所・走らせた結果（§1・§3〜§6）。当てる道具の穴2つと直し（Q12 の元）
26. `.claude/state/session_worklog_20261004.md`（:593-639） — 案を組んだ道具（r2_draft_build.py）が写しで確かめた中身（§50〜§52）。574列が直す前と同じ・CKSP の2列が TradingView の形と同じ、の実測

★直す相手になりうるファイルを必ず入れる (結果の「修正の指示」の「直す前の文字」を、監査が実物から写すため)。プログラムが作る文書 (設計書など) を監査するときは、その元データ (設計書なら、工事のフォルダ `.claude/state/verbatim/<工事名>/` の `やることの表.md`。承認の後は `SDK/.claude/ratchet/acceptance_archive/verbatim/<工事名>/`) も入れる。`acceptance_src.json` は 2026-09-30 から使っていない (ratchet に無い) ので、直す相手に書かない。

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = 設計書 `m2c15-hidden-params-20261004` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `m2c15-hidden-params-20261004` の中身です。

---

## 監査対象の事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_diag.py` | 361行（_vp_levels・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/observe_diag.py` | 373行（_vp_levels・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 3 | `SDK/scripts/priority_rebuild/observe_diag.py` | 381行（_vp_levels・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 4 | `SDK/scripts/priority_rebuild/observe_diag.py` | 641〜642行（_mama・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 5 | `SDK/scripts/priority_rebuild/observe_diag.py` | 646〜647行（_ck・CKSP を TradingView の形（10・1・9・rma）にそろえ、3つの値を名前に出さない引数で受け取る（まこさん「２はC」）） | 直した後の文字 |
| 6 | `SDK/scripts/priority_rebuild/observe_diag.py` | 650〜651行（_ps・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 7 | `SDK/scripts/priority_rebuild/observe_diag.py` | 658〜659行（_ab・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 8 | `SDK/scripts/priority_rebuild/observe_diag.py` | 662〜663行（_acb・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 9 | `SDK/scripts/priority_rebuild/observe_diag.py` | 666〜667行（_cel・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 10 | `SDK/scripts/priority_rebuild/observe_diag.py` | 670〜671行（_hw・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 11 | `SDK/scripts/priority_rebuild/observe_diag.py` | 792〜795行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 12 | `SDK/scripts/priority_rebuild/observe_diag.py` | 811行（<モジュール直下>・EMA の傾きの名前を EMA◯傾き% に戻し、比べる本数を名前に出さない引数で受け取る） | 直した後の文字 |
| 13 | `SDK/scripts/priority_rebuild/observe_diag.py` | 891〜894行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 14 | `SDK/scripts/priority_rebuild/observe_diag.py` | 935〜940行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 15 | `SDK/scripts/priority_rebuild/observe_diag.py` | 982〜983行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る／AO の名前を AO% にし、2つの本数を名前に出さない引数で受け取る（まこさん「A」）） | 直した後の文字 |
| 16 | `SDK/scripts/priority_rebuild/observe_diag.py` | 990行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 17 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1026行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 18 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1031行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 19 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1065〜1066行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 20 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1070〜1073行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 21 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1082行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 22 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1108行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 23 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1111〜1112行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 24 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1115行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 25 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1121行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 26 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1125〜1126行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 27 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1138行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 28 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1141行（<モジュール直下>・移動平均の登録が、受け取った引数を計算式へ渡す。傾きの比べる本数も名前に出さない引数で受け取る） | 直した後の文字 |
| 29 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1148〜1149行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 30 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1152〜1154行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 31 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1207〜1208行（<モジュール直下>・CKSP を TradingView の形（10・1・9・rma）にそろえ、3つの値を名前に出さない引数で受け取る（まこさん「２はC」）） | 直した後の文字 |
| 32 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1210行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 33 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1212〜1214行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 34 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1218行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 35 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1261行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 36 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1263〜1270行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 37 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1368〜1369行（build_catalog・EMA の傾きの名前を EMA◯傾き% に戻し、比べる本数を名前に出さない引数で受け取る） | 直した後の文字 |
| 38 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1472〜1473行（build_catalog・AO の名前を AO% にし、2つの本数を名前に出さない引数で受け取る（まこさん「A」）） | 直した後の文字 |
| 39 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1485〜1488行（build_catalog・AO の名前を AO% にし、2つの本数を名前に出さない引数で受け取る（まこさん「A」）） | 直した後の文字 |
| 40 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6926〜6927行（selftest_atr1h・番人の関数 _insp_hidden_params を足す（名前に出さない引数が計算に届いているか）） | 直した後の文字 |
| 41 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6979〜6980行（selftest_catalog・軽い口 selftest_catalog に、この工事の番人を足す） | 直した後の文字 |
| 42 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 318行（_tb_ema_slope・EMA の傾きの名前を EMA◯傾き% に戻し、比べる本数を名前に出さない引数で受け取る） | 直した後の文字 |
| 43 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 836行（_ext_ema_slope・EMA の傾きの名前を EMA◯傾き% に戻し、比べる本数を名前に出さない引数で受け取る） | 直した後の文字 |
| 44 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1066〜1068行（<モジュール直下>・EMA の傾きの名前を EMA◯傾き% に戻し、比べる本数を名前に出さない引数で受け取る） | 直した後の文字 |
| 45 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1070行（<モジュール直下>・EMA の傾きの名前を EMA◯傾き% に戻し、比べる本数を名前に出さない引数で受け取る） | 直した後の文字 |
| 46 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1435行（_tb_ao・AO の名前を AO% にし、2つの本数を名前に出さない引数で受け取る（まこさん「A」）） | 直した後の文字 |
| 47 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2524行（_ext_ao・AO の名前を AO% にし、2つの本数を名前に出さない引数で受け取る（まこさん「A」）） | 直した後の文字 |
| 48 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 2534〜2536行（<モジュール直下>・AO の名前を AO% にし、2つの本数を名前に出さない引数で受け取る（まこさん「A」）／パラメータを、名前に出さない引数で受け取る） | 直した後の文字 |
| 49 | `SDK/scripts/priority_rebuild/observe_config.json` | 136〜139行（設定・名前に値を出すための設定（ema_slope_lookbacks・ao_params）を外す） | 直した後の文字 |
| 50 | `SDK/scripts/priority_rebuild/observe_config.json` | 161〜167行（設定・名前に値を出すための設定（ema_slope_lookbacks・ao_params）を外す） | 直した後の文字 |
| 51 | `.claude/breaks/b128_k1_copc_back_in_ao_loop.sh` | 1〜27行（全文・探す文字が AO の直しで変わるので書き直す） | 直した後の文字 |
| 52 | `.claude/breaks/b132_hidden_param_not_passed.sh` | なし（新しいファイル） | 直した後の文字 |
| 53 | `.claude/breaks/b133_cksp_mixed_set.sh` | なし（新しいファイル） | 直した後の文字 |
| 54 | `.claude/breaks/b134_ao_name_with_value.sh` | なし（新しいファイル） | 直した後の文字 |
| 55 | `.claude/breaks/b135_rci_mako_gone.sh` | なし（新しいファイル） | 直した後の文字 |
| 56 | `.claude/breaks/b136_insp2_bar_close_dropped.sh` | なし（新しいファイル） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:m2c15-hidden-params-20261004）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 2 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 3 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 4 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 5 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 6 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 7 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 8 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 9 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 10 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 11 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 12 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 13 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 14 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 15 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 16 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 17 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 18 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 19 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 20 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 21 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 22 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 23 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 24 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 25 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 26 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 27 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 28 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 29 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 30 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 31 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 32 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 33 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 34 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 35 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 36 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 37 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 38 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 39 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 40 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 41 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 42 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 43 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 44 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 45 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 46 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 47 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 48 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-06T11:21:19 |
| 49 | `SDK/scripts/priority_rebuild/observe_config.json` | 当てた | 2026-10-06T11:21:19 |
| 50 | `SDK/scripts/priority_rebuild/observe_config.json` | 当てた | 2026-10-06T11:21:19 |
| 51 | `.claude/breaks/b128_k1_copc_back_in_ao_loop.sh` | 当てた | 2026-10-06T11:21:19 |
| 52 | `.claude/breaks/b132_hidden_param_not_passed.sh` | 当てた | 2026-10-06T11:21:19 |
| 53 | `.claude/breaks/b133_cksp_mixed_set.sh` | 当てた | 2026-10-06T11:21:19 |
| 54 | `.claude/breaks/b134_ao_name_with_value.sh` | 当てた | 2026-10-06T11:21:19 |
| 55 | `.claude/breaks/b135_rci_mako_gone.sh` | 当てた | 2026-10-06T11:21:19 |
| 56 | `.claude/breaks/b136_insp2_bar_close_dropped.sh` | 当てた | 2026-10-06T11:21:19 |

### 必読に要るファイル（道具が設計書と実装から拾った）

| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15） | 入れる |
| `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_config.json` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_diag.py` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b128_k1_copc_back_in_ao_loop.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b132_hidden_param_not_passed.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b133_cksp_mixed_set.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b134_ao_name_with_value.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b135_rci_mako_gone.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b136_insp2_bar_close_dropped.sh` | 直す相手（TARGET） | 入れる |

---

## 監査スコープ

### 監査対象 (本監査内)

- Q1：実装の指示を当てた結果が、実装の後と1文字も同じか
- Q2：実装の指示のどれにも当たらない行（設計書に無い変更）が無いか
- Q3：当てた記録が、実装の指示の全部と1件ずつ合うか
- Q4：承認した版の設計書どうしで、実装の指示が同じか
- Q5：実装の指示が、やることの表の要件を全部 満たすか
- Q6：完成の条件が、実装の後に本当に成り立つか
- Q8：名前に出さない引数は、47種類の登録で、その列の計算に本当に届いているか
- Q9：CKSP は TradingView の形（10・1・9・rma）になっているか。引数の既定 None で、ライブラリの既定どおりの列になるか
- Q10：完成の条件6行は、設計書の4つの直し（H-1〜H-4）を全部 覆っているか。壊すプログラム6本は、直しを外したときだけ落ちるか
- Q11：名前に出さない引数は、探す側のほかに、どこで見えなくなったか。型の表の禁止3（標本不足）が AO% を見逃す件の影響
- Q12：当てる道具（apply_audit_fix.py）に当てる途中で入れた直し2つは、ほかの件の当て方を変えていないか

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- engine_tuner へのつなぎ込み（名前に出さない引数を、探す側が範囲から渡す仕組み）（指標の修正の範囲外＝工事2。この工事の後も、名前に出さない引数は、まだ探す対象にならない）
- 別の値を渡した列を、参照表で照らすこと（探す側の工事で、別の値を使い始めるときに決める。今の参照表は、何も渡さないときの列だけを照らす）
- パラメータの最初の値と範囲を設定に書く直し（P-1・P-2）・教科書の版を足す直し（K-3）・帯の部品（B-1）・S1 の部品（S-1）・役割と閾値（R-1・T-1）（後の回）
- THERMO%・swing高値距離・swing安値距離・close vs VIDYA%・close vs ZLMA% を直すこと（その列の計算に使う、受け取っていない数のパラメータが無い（道具が、登録の文とライブラリの引数から判定した））
- その列の計算に使われない引数を受け取ること（KST の signal・SQZ_ON の mom_length と mom_smooth・ABER_ZG の atr_length・StochRSI%K の %D の本数・POC の出来高の割合）（値を変えても列が変わらない引数は、その指標のパラメータではない（154回目に道具が測って一覧に書いた））
- オフの指標だけの登録（MMAR傾き・RAINBOW傾き・MEDIAN傾き%）の傾きの本数（今は対応しない）
- RSI7・RSI9・RSI14・RSI21 と、V9 が使う指標の名前を変えること（そのままでよい）
- 成績表（material_ranking.json）の作り直し（M2-D-8 で、まこさんの OK の後に走らせる）
- 前の工事の設計書の古い数字（監査 CP61 の修正2）（当てない）
- 検査2 の確かめそのものを強くすること（今は、決まった2つの時刻だけを見る）（この工事は、今の確かめが外されないように守る番人を足すだけ。確かめを強くするのは、上位足のずらしを切り替えて比べる前（M2-F-10f）に決める）

---

## 監査観点 (一般・auditor_template ①〜⑦)

該当なし（この監査は、実装が設計書のとおりかと、まこさんの要望を満たしているかだけを問う。①〜⑦の観点は、この争点に関係しない。結果の所見の「一般の観点」にも「該当なし」と書く）

---

## 監査観点 (本監査固有・Q1-QN)

★問いごとに優先度を付ける＝A（結論を変える）／B（実装の前に直す）／C（完成の測り方以外の書き漏れ）／D（結論に効かせない）。結果の所見は、この問いの番号をそのまま見出しにし、優先度の順に書く。時間が足りずに省いた問いは、結果にその番号を書く。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**優先度の理由**＝違えば、実装は設計書のとおりに作られていない

実装の前（HEAD の commit e353f27（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる））の対象のファイル（`.claude/breaks/b128_k1_copc_back_in_ao_loop.sh`・`.claude/breaks/b132_hidden_param_not_passed.sh`・`.claude/breaks/b133_cksp_mixed_set.sh`・`.claude/breaks/b134_ao_name_with_value.sh`・`.claude/breaks/b135_rci_mako_gone.sh`・`.claude/breaks/b136_insp2_bar_close_dropped.sh`・`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/observe_diag.py`）に、設計書 4-20 の実装の指示（56 件）を番号の順に当てた結果が、実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる））と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**優先度の理由**＝在れば、設計書に無い変更が実装に混ざっている

実装の前（HEAD の commit e353f27（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる））と実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる））の差分（`.claude/breaks/b128_k1_copc_back_in_ao_loop.sh`・`.claude/breaks/b132_hidden_param_not_passed.sh`・`.claude/breaks/b133_cksp_mixed_set.sh`・`.claude/breaks/b134_ao_name_with_value.sh`・`.claude/breaks/b135_rci_mako_gone.sh`・`.claude/breaks/b136_insp2_bar_close_dropped.sh`・`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/observe_diag.py`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**優先度の理由**＝合わなければ、どの件を道具が当てたかを後から確かめられない

当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2c15-hidden-params-20261004`）が、実装の指示の 56 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**優先度の理由**＝当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない

承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-hidden-params-20261004.01.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-hidden-params-20261004.02.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-hidden-params-20261004.md`）と、いまの設計書の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**優先度の理由**＝要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない

実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-hidden-params-20261004/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**優先度の理由**＝成り立たなければ、承認のときの「済」が根拠にならない

設計書の完成の条件（6 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog`

### Q8 — 名前に出さない引数は、47種類の登録で、その列の計算に本当に届いているか（優先度 A）

**優先度の理由**＝引数を受け取るだけで計算に渡していない登録が残ると、工事2 で探す側が値を渡しても列が変わらず、「パラメータを範囲から探している」が嘘になる

当てた後の observe_diag.py の登録（790〜1000行・1100〜1280行）と自前の関数（636〜680行）を1つずつ読み、既定つきの引数が全部ライブラリの関数か自前の式へ渡っているかを確かめてください。番人 _insp_hidden_params（6929〜6992行）は、引数を1つずつ別の値にして列が変わるかを見ますが、「別の値が全部 計算できなかった引数」は数えません（設計書の 6-2 の2番）。その除外で見逃している引数が無いか（例＝for が取り込んだ列の番号を既定に持つ引数 c と、本当のパラメータの見分け）を見てください。何も渡さないときの列が、当てる前と同じか（CKSP の2列を除く 574列・設計書の 4-0 の③）を、写しの作業場で当てる前の版（git の 78af94f）と比べてください。

### Q9 — CKSP は TradingView の形（10・1・9・rma）になっているか。引数の既定 None で、ライブラリの既定どおりの列になるか（優先度 A）

**優先度の理由**＝値の組の写し違いで列が変わると、成績表と判定の材料が静かに変わる（154回目に起きた）

_ck（646〜650行）が tvmode=True で呼び、ライブラリ（pandas_ta_classic の cksp.py）の tvmode=True のときの値とならし方が TradingView の形か、ライブラリの実物で確かめてください。番人⑦（selftest_catalog の中）が、p=10・x=1・q=9・tvmode=True で直接 呼んだ列と比べていることも見てください。None を渡す登録（KST・UO・SMC_SWEEP・SQZ_ON ほか）で、ライブラリが None を「引数なし」と同じに扱うか（既定の決め方が同じか）を、ライブラリの該当の関数で確かめてください。

### Q10 — 完成の条件6行は、設計書の4つの直し（H-1〜H-4）を全部 覆っているか。壊すプログラム6本は、直しを外したときだけ落ちるか（優先度 A）

**優先度の理由**＝覆っていない直し・落ちない壊し方が在ると、同じ壊れ（引数が届かない・混ざった組に戻る・名前に値が入る・RCI が使わないに戻る・検査2 の確かめが消える）が黙って戻る

壊すプログラム6本を写しの作業場で走らせ、宣言した文（EXPECT_MSG）で落ちるか、壊す対象の行がちょうど1か所かを見てください。番人⑩（検査2）は「bar_close の形で誤検出しない」と「_insp_resample と selftest のソースに mode="bar_close" が在る」の2つで守ります＝検査2 の確かめそのものを強くはしていません（設計書の 3-1 の10番）。この守り方で、検査2 の確かめが外される形を取りこぼすものが無いかを見てください。★CC の自己申告＝番人⑧の1行（observe_diag.py:7057）は、設計書の実装41 では材料の名前の set をそのまま上から順に回す形でした。engine_tuner_exec.py の自己テスト（並びの決まらない入れ物の番人）に止められたため、承認の後に まこさんが `sorted(_nm_k1)` で回す形に手で直しました（恒久の決まり74番）。設計書と実物は、この1語だけ違います。この直しで番人⑧の判定が変わらないかも見てください。

### Q11 — 名前に出さない引数は、探す側のほかに、どこで見えなくなったか。型の表の禁止3（標本不足）が AO% を見逃す件の影響（優先度 B）

**優先度の理由**＝名前に出ていた数字を頼りにしていた仕組みが、名前から数字が消えたことで黙って変わる

gen_signal_families.py の _window_days（93〜101行）は、部品の名前の数字の最大値を窓の本数として n_eff を計算し、数字が無ければ 1本とします。この工事で AO の本数（5・34）が名前から消えたので、AO% の 1日足は禁止3 に入らなくなりました（前は AO%(5,34)__1d が n_eff 16.1 で禁止・いまの表は 514組）。CC は設計書にこれを書いていませんでした（next_step §6 の 248番に記録）。ほかに、名前の数字を頼りにしている仕組み（成績表の名前の照合・探す範囲の表 material_ranges・参照表の known の計算・材料の文書の決まった数字の一覧）で、この工事の名前の変わり（EMA の傾き・AO）と引数の隠れで、黙って挙動が変わった所が無いかを洗ってください。

### Q12 — 当てる道具（apply_audit_fix.py）に当てる途中で入れた直し2つは、ほかの件の当て方を変えていないか（優先度 B）

**優先度の理由**＝当てる道具は、この工事の後も全部の工事で使う。直しが別の件を「当て終わり」と誤判定すれば、以後の工事で当て漏れが出る

コミット 3f0ac4c（_done_in＝直す前の文字がまだ実物に在り、直した後の文字が直す前の文字を含まないなら当て終わりではない）と e353f27（check_one＝行を消す直しで、当てた記録に在る件は当て終わり）の差分を読み、自己テスト（--selftest 44件）がこの2つの直しを覆っているかを見てください。覆っていなければ、どの形の件が見られていないかを書いてください。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

件数: 0 件 (結果の外部検索の節にも「該当なし」と書く)

該当なし（この監査は、実装が設計書のとおりかを実物で照らす。外部の知見は答えに要らない。設計の理由を調べる外部検索は、設計書の監査で行う）

---

## 依頼を出した CC の自己申告

1. **承認の後に設計書を作り直した**＝前の版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-hidden-params-20261004.01.md` と いまの版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-hidden-params-20261004.md` の違い＝囲みの外で 12 行（実装の指示の囲み ACC_IMPL は同じ）
2. **承認の後に設計書を作り直した**＝前の版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-hidden-params-20261004.02.md` と いまの版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-hidden-params-20261004.md` の違い＝囲みの外で 12 行（実装の指示の囲み ACC_IMPL は同じ）
3. **この工事の外の作業中の変更**＝`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_request_understood.sh`・`.claude/tools/gen_acceptance.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）

(結果は、この番号ごとに1件ずつ答える)

---

## 結果ファイルフォーマット (auditor 用)

`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-06_m2c15_hidden_params_20261004_impl_cp62_audit_report.md` に、次の 11 節をこの順で出力する。★節の名前と並びは変えない。どの種類の監査でも同じ。

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
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-06_m2c15_hidden_params_20261004_impl_cp62_audit_request.md
```

または

```
本依頼書を読んで監査して
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-06_m2c15_hidden_params_20261004_impl_cp62_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp62_work/cp62_src.gen.md src_sha256=8a9009f00b91b401d8f0595d00427e1d4764103acc46be4d90c5a8290774b400 body_sha256=0a48d84e9a9fc0389700e91cdde7bf92d352ff1e63dba726404b35ca9ce1df49 -->

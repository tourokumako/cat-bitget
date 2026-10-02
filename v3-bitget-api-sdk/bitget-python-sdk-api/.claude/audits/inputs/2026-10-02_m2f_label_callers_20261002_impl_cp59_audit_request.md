# 【監査依頼】CP59 — 観察の道具と測る道具を、札の部品 regime_label.py を呼ぶ形に切り替え、札の版の名前を順位表・落ちた候補・成績表に書く＝14a の工事 B（実装の監査）

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 19 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて、結果ファイルを次の順で書く（手で1から書かない）:
   - 結果の骨組みを道具で作業場に作る: `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-02_m2f_label_callers_20261002_impl_cp59_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp59_work/cp59_result.md`
   - 骨組みの「<監査が書く>」などの印を全部 埋める（見出しと並びは変えない）
   - 食い違い0件を確かめる: `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-02_m2f_label_callers_20261002_impl_cp59_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>`
   - 出す前に見直す: `python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` で見直し表を作り、全部の行（結果の見出しごと）に ①意味が通じるか ②実物と合うか（根拠＝ファイル名:行番号・実際に開いた行）③争点（この依頼書の結論を決める問い）に合うか と判定（OK／直した／該当なし（理由））を書き、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通す（結果を直したら表を作り直す・hook 11 が同じ照らしを掛ける）
   - 埋めた結果の全文を、結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-02_m2f_label_callers_20261002_impl_cp59_audit_report.md` に Write で1回だけ書く（hook 11 が同じ照らしを掛ける。書いた後は書き替えられない）
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / CONDITIONAL-GO / NO-GO)
   - 重さごとの件数 (Critical / Major / Minor / Process)

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)
- 本物のファイルを書き替えること (写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp59_work/` に作る。最後に `git status --short` で書き替えていないことを示す)

### この監査の作業場

**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp59_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました。**判断が要る4つ（この工事は何のためか・必読・工事ごとの問い・要望のまとめ）は、CC が工事のフォルダの 監査依頼の手書き（実装の監査）.md に書き、まこさんが OK した文を写しました。ほかは道具が実物から作りました。問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・まこさんの要望が在る工事だけ）と、この工事で確かめてほしいことを問う工事ごとの問い（Q8〜Q13）です。

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-02
- 依頼者: CC（起案者）
- 監査区分: 実装の監査
- 監査対象タスク: M2-F-6d・M2-F-5／設計書 m2f-label-callers-20261002
- 監査の相手と版: `.claude/state/acceptance.md` ／ ハッシュ値 4067f16f7c3eb1233f2b604fa48a1cc5bebbbc8d08bc7a4248e5b4be8d5df033
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-02_m2f_label_callers_20261002_impl_cp59_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-02_m2f_label_callers_20261002_impl_cp59_audit_request.md`

---

## この監査で答えてほしいこと

### 結論を決める問い

- **問い1**＝設計書の実装の指示（30 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。あわせて、この工事で確かめてほしいこと（Q8〜Q13 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けている・工事ごとの問いで設計書と違う所が見つかれば NO。

- **問い2**＝この工事の後の実装が、下に並べた まこさんの要望（4 件）を満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。1つでも満たしていなければ NO（Q7 で照らす）。
  1. 目的：札が不適切だと分かったとき、直しやすい状態にする。工事 B が受け持つのは、札を作る場所を1つにすることと、どの版の札で選んだかを成績表の側に残すこと
  2. 札を作る場所を1つにする。観察の道具の中にある式を、⑪タブの道具と成績表の道具が別々に呼ぶ形をやめる（⑪タブの道具の切り替えは工事 C）
  3. どの版の札で作った成績表かを、成績表の側に残す。順位表と落ちた候補のファイルに、札の版の名前を書く
  4. 札の数字は設定ファイルに置き、値を書き替えて走らせ直せば札を作り直せる（工事 A で作った設定を、観察の道具と測る道具も読む）

(結論を決めるのは、これらの問いだけ。結果の「7. 総合判定」で、問いごとに YES / NO と根拠を書く)

### 結論の決め方

- **GO**＝問い1 と 問い2 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 と 問い2 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 と 問い2 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の番号と実物の行で示してください。

### この監査の前提

1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-callers-20261002/やることの表.md`）に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。
5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。

---

## 監査依頼の経緯

1. **この工事は何のためか**＝札（正解ラベル）が正しいかは、最後に M2-L で入口と出口を固定して売買し、net を見るまで分からない。外れていたら、札を直して段1から並べ直す。だから札は、売買の結果を見て不適切だと分かったときに、直しやすい構造にする（2026-09-28 まこさん決定・やることリスト M2-F-6d の注意）
   直しやすい構造のうち、工事 B が受け持つのは2つ。①札を作る場所を1つにする（観察の道具と測る道具が、それぞれの式で札を作っていると、札を直したときに片方だけ変わる）②どの版の札で選んだかを、順位表・落ちた候補・成績表の側に残す（売買の結果を見て札を疑うときに、どの札で選んだ束かをたどれる）。あわせて、役割ごとの札のときは役割ごとに測り、段ごとに役割ごとに上位を残す（OK された表の L-6・worklog 20260928 §51 の1）。工事 A は札を作る部品と設定を作った。⑪タブは工事 C
2. **この工事は何か**＝M2 は、4つの場面（レンジ・上げ・下げ・スパイク）の判定を、全部の戦略のために組む段です。組んだ判定の良し悪しは、答え合わせに使う札（そのバーが後から見て実際にレンジだったかの答え）と照らして測ります。工事 A で、札を作る部品 regime_label.py と設定 recipes/regime_label.json を作りました。しかし、観察の道具（observe_diag.py の _regime_labels）と測る道具（regime_r9_diag.py の _labels_for）は、まだ自分の式と search_limits.json の本数で札を作っています。札を直しても、片方だけが変わる形のままです。この工事 B は、2つの道具を部品を呼ぶ形に切り替え、どの版の札で作ったかを順位表・落ちた候補・成績表に書き、役割ごとの札のときは役割ごとに上位を残すようにします。採点に使う版は er_median のままなので、札・順位表・成績表の数字は変わりません。⑪タブは工事 C です。（やることの番号 M2-F-6d・M2-F-5）
   **この工事の位置**＝全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-F｜段ごとに測って並べ、上位を次の段へ渡す（段1〜段4）＝1本ずつの成績と順位を出す → M2-F-6d｜案B の4＝直す（M2-F-6c で変えると決まったときだけ）＝正解の作り方と測る道具を直し、指標の成績表を作り直す → M2-F-5｜実走＝段1 の束を数本 測り、3つの割合の表・順位表・落ちた候補の理由が5つの場面とも出ることを確かめる → この工事

---

## 着手前必読 (省略禁止・auditor 用・19 件)

**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `.claude/state/acceptance.md` — 監査の相手（設計書・プログラムが作った）
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-callers-20261002.01.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-callers-20261002.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
4. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:m2f-label-callers-20261002 の行）
5. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-callers-20261002/やることの表.md` — 設計書の元（やることの表）＝修正の指示を書く先
6. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — 目標（全月 net ≥ $1,900・単月判定・通算でない）と全体戦略（§1.2・§1.2.1）、ハード制約（§4.6＝H2 未来参照なし・H6 価格非依存ほか）。この工事が目標と制約に沿っているかを照らす
7. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-103） — engine_tuner の目的と、作ってはいけないもの（乱数ほか）
8. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:95-146） — M2 が M1〜M6 のどこに当たり、何ができたら終わりか
9. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:3-46・:498-619・:1342-1392・:2021-2368） — M2 のミッションと作っている物・M2 の一覧（§0-0）・正解の作り方を決めた段（M2-A）・この工事が入っているフロー（M2-F と M2-F-6d の行）
10. `SDK/.claude/ratchet/m2_todo.json`（:1155-1170） — M2-F-6d の注意＝札の構造の文の原文（札を作る場所を1つにする・どの版の札で作った成績表かを残す）。Q8・Q10 で照らす
11. `.claude/state/session_worklog_20260928.md`（:1402-1439） — §50・§51＝役割ごとに測って、段ごとに役割ごとに10本ずつ残す（§51 の1）・成績表にも札の版を書く理由（§51 の2）。Q11 で照らす
12. `SDK/scripts/priority_rebuild/regime_r9_diag.py`（全文） — 測る道具。札を部品から受け取る（_labels_for）・列の名前・役割ごとの並べ（rank_key・rank_rows）・札の版を書く（write_outputs）・差し戻しの止め（run_sweep）・自己検査⑤⑫⑬
13. `SDK/scripts/priority_rebuild/observe_diag.py`（:108-120・:5786-5850・:6071-6125・:6266-6315） — 観察の道具。部品の読み込み・先を見る本数と札（_regime_horizons・_regime_labels）・成績表の書き出しに札の版（_insp_regime_rank・add_demand_to_ranking）
14. `SDK/scripts/priority_rebuild/regime_label.py`（全文） — 札の部品（工事 A で作った）。呼ぶ側の口（keys・labels_for_key・labels_at_bars・bars_keys・version_tag・groups）と、足した自己検査 T6
15. `SDK/scripts/priority_rebuild/recipes/regime_label.json`（全文） — 札の設定。採点に使う版（er_median）と、版2 の使う値（空）。Q8・Q11 で書き替える相手
16. `SDK/scripts/priority_rebuild/engine_tuner_gen.py`（:1340-1355） — 成績表を読む側 load_material_ranking。成績表に札の版の欄を足しても読めるか（Q10）
17. `.claude/breaks/b122_obs_formula_copied.sh` — 壊すプログラム。観察の道具に札の式を書き写すと、自己検査 T6 が落ちるか（Q12）
18. `.claude/breaks/b123_label_tag_dropped.sh` — 壊すプログラム。順位表に札の版を書かないと、自己検査⑬が落ちるか（Q12）
19. `.claude/breaks/b124_role_keep_off.sh` — 壊すプログラム。役割ごとに残さないと、自己検査⑫が落ちるか（Q12）

★直す相手になりうるファイルを必ず入れる (結果の「修正の指示」の「直す前の文字」を、監査が実物から写すため)。プログラムが作る文書 (設計書など) を監査するときは、その元データ (設計書なら、工事のフォルダ `.claude/state/verbatim/<工事名>/` の `やることの表.md`。承認の後は `SDK/.claude/ratchet/acceptance_archive/verbatim/<工事名>/`) も入れる。`acceptance_src.json` は 2026-09-30 から使っていない (ratchet に無い) ので、直す相手に書かない。

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = 設計書 `m2f-label-callers-20261002` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。あわせて、まこさんの要望を、この工事の後の実装が満たしているか（問い2・Q7）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `m2f-label-callers-20261002` の中身です。

---

## 監査対象の事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 11〜14行（<モジュール直下>） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 49行（<モジュール直下>） | 足す文字 |
| 3 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 94〜104行（rank_key） | 直した後の文字 |
| 4 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 107〜127行（rank_rows） | 直した後の文字 |
| 5 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 139行（write_outputs） | 足す文字 |
| 6 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 176〜184行（_labels_for） | 直した後の文字 |
| 7 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 203〜208行（measure） | 直した後の文字 |
| 8 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 534行（run_stage） | 直した後の文字 |
| 9 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 588行（run_sweep） | 直した後の文字 |
| 10 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 639行（run_sweep） | 直した後の文字 |
| 11 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 969行（main） | 直した後の文字 |
| 12 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 780行（selftest） | 足す文字 |
| 13 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 805行（selftest） | 足す文字 |
| 14 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 861行（selftest） | 直した後の文字 |
| 15 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 556行（run_sweep） | 直した後の文字 |
| 16 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 856〜859行（selftest） | 直した後の文字 |
| 17 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 860行（selftest） | 直した後の文字 |
| 18 | `SDK/scripts/priority_rebuild/observe_diag.py` | 115行（<モジュール直下>） | 足す文字 |
| 19 | `SDK/scripts/priority_rebuild/observe_diag.py` | 5791〜5792行（<モジュール直下>） | 直した後の文字 |
| 20 | `SDK/scripts/priority_rebuild/observe_diag.py` | 5806〜5814行（_regime_horizons） | 直した後の文字 |
| 21 | `SDK/scripts/priority_rebuild/observe_diag.py` | 5831〜5848行（_regime_labels） | 直した後の文字 |
| 22 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6090行（_insp_regime_rank） | 直した後の文字 |
| 23 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6119行（_insp_regime_rank） | 足す文字 |
| 24 | `SDK/scripts/priority_rebuild/observe_diag.py` | 6307行（add_demand_to_ranking） | 足す文字 |
| 25 | `SDK/scripts/priority_rebuild/regime_label.py` | 25行（<モジュール直下>） | 直した後の文字 |
| 26 | `SDK/scripts/priority_rebuild/regime_label.py` | 340行（selftest） | 直した後の文字 |
| 27 | `SDK/scripts/priority_rebuild/regime_label.py` | 380行（selftest） | 直した後の文字 |
| 28 | `.claude/breaks/b122_obs_formula_copied.sh` | なし（新しいファイル） | 直した後の文字 |
| 29 | `.claude/breaks/b123_label_tag_dropped.sh` | なし（新しいファイル） | 直した後の文字 |
| 30 | `.claude/breaks/b124_role_keep_off.sh` | なし（新しいファイル） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:m2f-label-callers-20261002）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 2 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 3 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 4 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 5 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 6 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 7 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 8 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 9 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 10 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 11 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 12 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 13 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 14 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 15 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 16 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 17 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 18 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 19 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 20 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 21 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 22 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 23 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 24 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-02T08:29:46 |
| 25 | `SDK/scripts/priority_rebuild/regime_label.py` | 当てた | 2026-10-02T08:29:46 |
| 26 | `SDK/scripts/priority_rebuild/regime_label.py` | 当てた | 2026-10-02T08:29:46 |
| 27 | `SDK/scripts/priority_rebuild/regime_label.py` | 当てた | 2026-10-02T08:29:46 |
| 28 | `.claude/breaks/b122_obs_formula_copied.sh` | 当てた | 2026-10-02T08:29:46 |
| 29 | `.claude/breaks/b123_label_tag_dropped.sh` | 当てた | 2026-10-02T08:29:46 |
| 30 | `.claude/breaks/b124_role_keep_off.sh` | 当てた | 2026-10-02T08:29:46 |

### 必読に要るファイル（道具が設計書と実装から拾った）

| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-F-6d・M2-F-5） | 入れる |
| `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/regime_label.py` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b122_obs_formula_copied.sh` | 新しく作るファイル（NEW_FILE） | 入れる |
| `.claude/breaks/b123_label_tag_dropped.sh` | 新しく作るファイル（NEW_FILE） | 入れる |
| `.claude/breaks/b124_role_keep_off.sh` | 新しく作るファイル（NEW_FILE） | 入れる |
| `SDK/scripts/priority_rebuild/recipes/regime_label.json` | `SDK/scripts/priority_rebuild/regime_r9_diag.py` が名前を出す（実装の前後の差分） | 入れる |
| `SDK/scripts/priority_rebuild/recipes/search_limits.json` | `SDK/scripts/priority_rebuild/observe_diag.py` が名前を出す（実装の前後の差分） | 入れない（観察の道具が先を見る本数を読まなくなった元。説明の文に名前が残るだけ（keep を読む stage_keep_range は直していない）） |

---

## 監査スコープ

### 監査対象 (本監査内)

- Q1：実装の指示を当てた結果が、実装の後と1文字も同じか
- Q2：実装の指示のどれにも当たらない行（設計書に無い変更）が無いか
- Q3：当てた記録が、実装の指示の全部と1件ずつ合うか
- Q4：承認した版の設計書どうしで、実装の指示が同じか
- Q5：実装の指示が、やることの表の要件を全部 満たすか
- Q6：完成の条件が、実装の後に本当に成り立つか
- Q7：まこさんの要望を、この工事の後の実装が満たしているか（問い2）
- Q8：工事 B の後、札を作る場所が1つになり、札を直すと観察の道具と測る道具の両方が同じ札で動くか
- Q9：採点に使う版が er_median のとき、測る道具と成績表の数字が直す前と同じか
- Q10：札の版の名前が、順位表・落ちた候補・成績表に書かれ、たどれるか
- Q11：採点に使う版が役割を持つとき（band_hold）、役割ごとに測り、段ごとに役割ごとに keep 本ずつ残すか
- Q12：自己検査 T6・⑫・⑬ と壊すプログラム b122〜b124 が、それぞれの判定を外したときに落ちるか
- Q13：観察の道具と札の部品を書き替えたことで、H2 の印が取り直されているか

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- ⑪タブの道具 build_regime_label_dashboard.py を部品に切り替えること（9/29 の控えの実装の指示 23〜27）（工事 C でやる）
- 役割ごとの札（band_hold）のときの差し戻し（--sweep）を作ること（差し戻しは「良くなったか」を1つの並べる鍵で比べる。役割ごとの札のとき、どの役割の鍵で比べるかは、まだどの文書にも決まっていない（§51 の1 は段ごとに残す本数だけ）。役割の列を黙って混ぜて比べないよう、band_hold のときは止まる形にし、採点に使う版を切り替えるときに作る）
- 版2 の使う値を選ぶこと・採点に使う版を band_hold に切り替えること（使う値は まこさんが⑪タブの目と検査15 で選ぶ。選ぶまでは版1 のまま）
- 上げ・下げ・スパイクの札を作ること（範囲は M2-M-1 で まこさんが決める）
- 観察の道具の中で _regime_labels と _regime_horizons を呼んでいる8か所を直すこと（呼ぶ名前と戻りの形を変えないので、8か所は直さずに部品を通る）

---

## 監査観点 (一般・auditor_template ①〜⑦)

該当なし（この監査は、実装が設計書のとおりかと、まこさんの要望を満たしているかだけを問う。①〜⑦の観点は、この争点に関係しない。結果の所見の「一般の観点」にも「該当なし」と書く）

---

## 監査観点 (本監査固有・Q1-QN)

★問いごとに優先度を付ける＝A（結論を変える）／B（実装の前に直す）／C（完成の測り方以外の書き漏れ）／D（結論に効かせない）。結果の所見は、この問いの番号をそのまま見出しにし、優先度の順に書く。時間が足りずに省いた問いは、結果にその番号を書く。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**優先度の理由**＝違えば、実装は設計書のとおりに作られていない

実装の前（commit fefb00e）の対象のファイル（`.claude/breaks/b122_obs_formula_copied.sh`・`.claude/breaks/b123_label_tag_dropped.sh`・`.claude/breaks/b124_role_keep_off.sh`・`SDK/scripts/priority_rebuild/observe_diag.py`・`SDK/scripts/priority_rebuild/regime_label.py`・`SDK/scripts/priority_rebuild/regime_r9_diag.py`）に、設計書 4-20 の実装の指示（30 件）を番号の順に当てた結果が、実装の後（commit 19d1bd7）と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**優先度の理由**＝在れば、設計書に無い変更が実装に混ざっている

実装の前（commit fefb00e）と実装の後（commit 19d1bd7）の差分（`.claude/breaks/b122_obs_formula_copied.sh`・`.claude/breaks/b123_label_tag_dropped.sh`・`.claude/breaks/b124_role_keep_off.sh`・`SDK/scripts/priority_rebuild/observe_diag.py`・`SDK/scripts/priority_rebuild/regime_label.py`・`SDK/scripts/priority_rebuild/regime_r9_diag.py`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**優先度の理由**＝合わなければ、どの件を道具が当てたかを後から確かめられない

当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2f-label-callers-20261002`）が、実装の指示の 30 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**優先度の理由**＝当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない

承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-callers-20261002.01.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-callers-20261002.md`）と、いまの設計書の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**優先度の理由**＝要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない

実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-callers-20261002/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**優先度の理由**＝成り立たなければ、承認のときの「済」が根拠にならない

設計書の完成の条件（4 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 scripts/priority_rebuild/regime_label.py --selftest`・`python3 scripts/priority_rebuild/regime_r9_diag.py --selftest`・`python3 scripts/priority_rebuild/regime_r9_diag.py --stage stage1 --limit 2 --purpose check`

### Q7 — まこさんの要望を、この工事の後の実装が満たしているか（問い2）（優先度 A）

**優先度の理由**＝満たしていない要望が在れば、まこさんの要望が届いていない（この答えが問い2 の答えになる）

下に並べた まこさんの要望を、この工事の後の実装が満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。この問いの答えが、結論を決める問い2 の答えになる。

  1. 目的：札が不適切だと分かったとき、直しやすい状態にする。工事 B が受け持つのは、札を作る場所を1つにすることと、どの版の札で選んだかを成績表の側に残すこと
  2. 札を作る場所を1つにする。観察の道具の中にある式を、⑪タブの道具と成績表の道具が別々に呼ぶ形をやめる（⑪タブの道具の切り替えは工事 C）
  3. どの版の札で作った成績表かを、成績表の側に残す。順位表と落ちた候補のファイルに、札の版の名前を書く
  4. 札の数字は設定ファイルに置き、値を書き替えて走らせ直せば札を作り直せる（工事 A で作った設定を、観察の道具と測る道具も読む）

### Q8 — 工事 B の後、札を作る場所が1つになり、札を直すと観察の道具と測る道具の両方が同じ札で動くか（優先度 A）

**優先度の理由**＝場所が2つ残っていれば、M2-L で札が外れていたと分かって直したとき、片方だけが変わる（この工事の目的が満たされない）

写しの作業場で、次の3つを試してください。①regime_label.json の数字だけを書き替える（例＝er_median の先を見る本数）と、コードを1文字も変えずに、observe_diag._regime_horizons・observe_diag._regime_labels と regime_r9_diag._labels_for の3つが同じ新しい札・本数を返すか。②観察の道具と測る道具の中に、札の式（中央値で切る式）や先を見る本数の数字が残っていないか。③札を作る部品以外に、regime_label.json を読む所が無いか。直した後も2か所に残る所や、黙って古い札を使う所が在れば、全部 挙げてください。

### Q9 — 採点に使う版が er_median のとき、測る道具と成績表の数字が直す前と同じか（優先度 A）

**優先度の理由**＝違えば、札の呼び方を変えただけで M2-F-1〜M2-F-5 で測った数と比べられなくなる

同じデータで、直す前（commit c44ac3a の版）と直した後の測る道具（--stage stage1 --limit 2 --purpose check）の3つの割合と列の名前を比べてください（直した後の印字は worklog 20261002 §8 の 8-8 に在る）。観察の道具の _regime_labels と _regime_horizons も、直す前と後で同じ答えを返すかを見てください。

### Q10 — 札の版の名前が、順位表・落ちた候補・成績表に書かれ、たどれるか（優先度 A）

**優先度の理由**＝書かれなければ、売買の結果を見て札を疑うときに、どの札で選んだ束かをたどれない（まこさんの構造の文の3つ目）

順位表と落ちた候補の各行の「札の版」が regime_label.version_tag と同じか。成績表を書く口（_insp_regime_rank）と需給を足す口（add_demand_to_ranking）が札の版を書くか。版の違う成績表に需給を足そうとしたら止まるか。札の版の欄が無い成績表（いまの material_ranking.json）を、版1 で作った物として読むことが正しいか。成績表を読む側（engine_tuner_gen.load_material_ranking）が、札の版の欄を足しても読めるかも見てください。

### Q11 — 採点に使う版が役割を持つとき（band_hold）、役割ごとに測り、段ごとに役割ごとに keep 本ずつ残すか（優先度 A）

**優先度の理由**＝役割が違えば使う戦略が違うので、混ぜて並べると片方の役割に合う束が落ちる（worklog 20260928 §51 の1）

写しの作業場で、regime_label.json の採点に使う版を band_hold にし、役割ごとの「使う値」を範囲の中の1組に書いて、測る道具の --stage を走らせてください。列の名前の括弧の中が役割の名前になるか・rank_rows が役割ごとに keep 本ずつ残すか・差し戻し（--sweep）が止まるか（役割ごとの比べ方は決まっていないので止まる作り）を見てください。観察の道具の先を見る本数（_regime_horizons）が役割ごとの本数を返し、_regime_labels がその役割の札を返すかも見てください。

### Q12 — 自己検査 T6・⑫・⑬ と壊すプログラム b122〜b124 が、それぞれの判定を外したときに落ちるか（優先度 B）

**優先度の理由**＝判定を外しても落ちなければ、札の式の書き写し・札の版の書き忘れ・役割ごとの残し忘れが黙って入る

b122（観察の道具に札の式を書き写す → T6）・b123（順位表に札の版を書かない → ⑬）・b124（役割ごとに残さない → ⑫）を写しの作業場で走らせ、期待どおりに落ちるか、壊す対象の行がちょうど1か所かを見てください。T6 が測る道具の _labels_for も見ているかも確かめてください。

### Q13 — 観察の道具と札の部品を書き替えたことで、H2 の印が取り直されているか（優先度 B）

**優先度の理由**＝取り直していなければ、未来参照の検査を通らない形で engine_tuner が回る

h2_pass.json の指紋が、いまの observe_diag.py と regime_label.py を含む24件と合うかを見てください（enforce_h2_pass.py --check-fingerprint）。G2 の印の対象が38件から39件に増えた理由（増えたファイル）も示してください。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

件数: 0 件 (結果の外部検索の節にも「該当なし」と書く)

該当なし（この監査は、実装が設計書のとおりかを実物で照らす。外部の知見は答えに要らない。設計の理由を調べる外部検索は、設計書の監査で行う）

---

## 依頼を出した CC の自己申告

1. **測っていない見積もり**＝自己検査と b122〜b124（測っていない・4-14）
2. **承認の後に設計書を作り直した**＝前の版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-callers-20261002.01.md` と いまの版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-callers-20261002.md` の違い＝ACC_SPEC の囲みの中で 6 行・囲みの外で 12 行（実装の指示の囲み ACC_IMPL は同じ）
3. **この工事の外の作業中の変更**＝`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_request_understood.sh`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）

(結果は、この番号ごとに1件ずつ答える)

---

## 結果ファイルフォーマット (auditor 用)

`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-02_m2f_label_callers_20261002_impl_cp59_audit_report.md` に、次の 11 節をこの順で出力する。★節の名前と並びは変えない。どの種類の監査でも同じ。

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
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-02_m2f_label_callers_20261002_impl_cp59_audit_request.md
```

または

```
本依頼書を読んで監査して
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-02_m2f_label_callers_20261002_impl_cp59_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp59_work/cp59_src.gen.md src_sha256=4475af0e2a6c33a76d60f384f64f700e20c6ffbbc6145edcd65e978a69fcf484 body_sha256=e24bec1c990158616cd73c67647a851f58f009e30ac2405485634713afb33187 -->

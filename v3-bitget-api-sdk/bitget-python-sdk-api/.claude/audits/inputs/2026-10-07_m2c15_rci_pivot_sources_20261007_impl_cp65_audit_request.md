# 【監査依頼】CP65 — 資料に足した4種を設定ファイルに写す。M2-C-15（実装の監査）

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 25 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて、結果ファイルを次の順で書く（手で1から書かない）:
   - 結果の骨組みを道具で作業場に作る: `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_rci_pivot_sources_20261007_impl_cp65_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp65_work/cp65_result.md`
   - 骨組みの「<監査が書く>」などの印を全部 埋める（見出しと並びは変えない）
   - 食い違い0件を確かめる: `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_rci_pivot_sources_20261007_impl_cp65_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>`
   - 出す前に見直す: `python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` で見直し表を作り、全部の行（結果の見出しごと）に ①意味が通じるか ②実物と合うか（根拠＝ファイル名:行番号・実際に開いた行）③争点（この依頼書の結論を決める問い）に合うか と判定（OK／直した／該当なし（理由））を書き、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通す（結果を直したら表を作り直す・hook 11 が同じ照らしを掛ける）
   - 埋めた結果の全文を、結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-07_m2c15_rci_pivot_sources_20261007_impl_cp65_audit_report.md` に Write で1回だけ書く（hook 11 が同じ照らしを掛ける。書いた後は書き替えられない）
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / CONDITIONAL-GO / NO-GO)
   - 重さごとの件数 (Critical / Major / Minor / Process)

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)
- 本物のファイルを書き替えること (写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp65_work/` に作る。最後に `git status --short` で書き替えていないことを示す)

### この監査の作業場

**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp65_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました。**判断が要る4つ（この工事は何のためか・必読・工事ごとの問い・要望のまとめ）は、CC が工事のフォルダの 監査依頼の手書き（実装の監査）.md に書き、まこさんが OK した文を写しました。ほかは道具が実物から作りました。問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・まこさんの要望が在る工事だけ）と、この工事で確かめてほしいことを問う工事ごとの問い（Q8〜Q11）です。

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-07
- 依頼者: CC（起案者）
- 監査区分: 実装の監査
- 監査対象タスク: M2-C-15・M2-F-10b・M2-D-8／設計書 m2c15-rci-pivot-sources-20261007
- 監査の相手と版: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-rci-pivot-sources-20261007.md` ／ ハッシュ値 bacbf466c28304bbb3f5a98296b4ea865c2c9b8e0454de54609fbf9e1750d95e
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-07_m2c15_rci_pivot_sources_20261007_impl_cp65_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_rci_pivot_sources_20261007_impl_cp65_audit_request.md`

---

## この監査で答えてほしいこと

### 結論を決める問い

- **問い1**＝設計書の実装の指示（5 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。あわせて、この工事で確かめてほしいこと（Q8〜Q11 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けている・工事ごとの問いで設計書と違う所が見つかれば NO。

- **問い2**＝この工事の後の実装が、下に並べた まこさんの要望（2 件）を満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。1つでも満たしていなければ NO（Q7 で照らす）。
  1. 目的：「使う」にした4種を資料に足し、資料から設定ファイルに写して、engine_tuner が4種を資料の値で扱えるようにする
  2. 資料と設定ファイルのずれを、毎回 チェックで見つけられる形にし、やり直しの時間を減らす

(結論を決めるのは、これらの問いだけ。結果の「7. 総合判定」で、問いごとに YES / NO と根拠を書く)

### 結論の決め方

- **GO**＝問い1 と 問い2 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 と 問い2 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 と 問い2 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の番号と実物の行で示してください。

### この監査の前提

1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-rci-pivot-sources-20261007/やることの表.md`）に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。
5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。

---

## 監査依頼の経緯

1. **この工事は何のためか**＝「使う」にしたのに資料（指標ごとに調べた値の表3つ）に行が無かった4種（RCI・前期間pivotPP・前期間pivotR1・前期間pivotS1）を資料に足し、資料から設定ファイル（observe_config.json・search_limits.json）に写す。engine_tuner が読むのは設定ファイルなので、写さないと資料を足しても engine_tuner の動きは変わらない
   同じ抜けを二度と起こさない。資料は 2026-10-04 に1回だけ作り、指標を「使う」にしても資料に行を足す手順も、知らせる検査も無かった。資料が変わっても設定ファイルを写し直したかを見る検査も無かった。この2つを照らす道具（check_indicator_sources.py の①②）を作り、監査に出す前のチェックと設計書を作る道具に入れた
2. **この工事は何か**＝指標の資料（指標ごとに調べた値の表）は 2026-10-04 に1回だけ作りました。そのあと RCI と前期間pivot の3種を「使う」にしましたが、資料に行がありませんでした。まこさんの「追加して」で、調べる係が4種の値を集め、プログラムがページを開き直して照らし、資料の表3つに4種の行を足しました（前の141種の行は1文字も変えていません）。あわせて、まこさんの「とにかくすべて完璧に修正して」で、「使う」の指標が資料に全部 在るか（①）と、設定ファイルが資料から写したものと同じか（②）を照らす道具を作り、監査に出す前のチェックに入れました。いま②が、設定ファイルと資料の食い違いを出しています。この工事は、その食い違いを直します。observe_config.json の指標ごとの一覧と値を埋めない種類の並び、search_limits.json の探す範囲を、資料から道具が写し直します。コードは1行も変えません。RCI の列が1本 増えるので、型の表の再承認が要る見込みです。（やることの番号 M2-C-15・M2-F-10b・M2-D-8）
   **この工事の位置**＝全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝材料を直す（監査 CP60 の修正・法則どおりの帯の部品・S1 の部品） → M2-F｜段ごとに測って並べ、上位を次の段へ渡す（段1〜段4）＝1本ずつの成績と順位を出す → M2-F-10b｜測る道具を直す（工事2）＝①正解ラベル2本との一致率で並べる ②手で組んだ土台を置いて、その上に候補を足して測る口 ③確認の窓でも測る口 ④段4 を役割ごとに動かす ⑤6項目のチェックを通す → M2-D｜場面を分ける材料の順位を engine_tuner に渡す → M2-D-8｜直した材料で、成績表（material_ranking.json）を作り直す → この工事

---

## 着手前必読 (省略禁止・auditor 用・25 件)

**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-rci-pivot-sources-20261007.md` — 監査の相手（設計書・プログラムが作った）
2. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:m2c15-rci-pivot-sources-20261007 の行）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-rci-pivot-sources-20261007/やることの表.md` — 設計書の元（やることの表）＝修正の指示を書く先
4. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — 目標（全月 net ≥ $1,900）と全体戦略、ハード制約（§4.6＝H2 未来参照なし・H6 値段の高さで値が変わらない ほか）。計算式は変えていないが、RCI の列が増えることが制約に触れないかを照らす
5. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-103） — engine_tuner の目的と、作ってはいけないもの（乱数・探す値を CC が点の一覧で限定するもの）。RCI が値を埋めない種類の並びから外れて範囲になる直しを照らす
6. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:95-146） — M2 が M1〜M6 のどこに当たり、何ができたら終わりか
7. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:3-46・:995-1040・:1173-1183） — M2 で作っている物と、この工事（M2-C-15＝材料を直す）の行と中身
8. `SDK/.claude/ratchet/acceptance_archive/m2c15-rci-pivot-sources-20261007.md`（全文） — 承認済みの設計書の控え（実装の指示5件・完成の条件2行・承認のプログラムが測った）
9. `SDK/scripts/priority_rebuild/observe_config.json`（:160-335） — 指標ごとの一覧に入った RCI の組・値を埋めない種類の並び（24種）・RCI の列をこれまで作っていた rci_periods（Q8）
10. `SDK/scripts/priority_rebuild/recipes/search_limits.json`（:44-160） — 探す範囲に入った RCI 5〜52（Q8）
11. `.claude/state/indicator_params_by_strategy.md`（:155-164） — 資料の表（パラメータの最初の値と範囲）に足した4種の行（Q8・Q9）
12. `.claude/state/indicator_params_review.md`（:155-166） — 資料の表（調べた値）に足した4種の行（Q9）
13. `.claude/state/indicator_roles_thresholds.md`（:155-164） — 資料の表（役割と閾値）に足した4種の行（Q9）
14. `.claude/state/indicator_review/research/out_g7.json` — 調べる係が集めた4種のパラメータの逐語（URL つき）（Q9）
15. `.claude/state/indicator_review/research/verify_out_g7.json` — プログラムがページを開き直して、パラメータの逐語を照らした結果（一致50・不一致2）（Q9）
16. `.claude/state/indicator_review/research/out_w3.json` — 調べる係が集めた4種の役割と閾値の逐語（URL つき）（Q9）
17. `.claude/state/indicator_review/research/verify_out_w3.json` — プログラムがページを開き直して、役割と閾値の逐語を照らした結果（一致75・不一致4）（Q9）
18. `.claude/tools/check_indicator_sources.py`（全文） — 照らしの道具（①「使う」の指標が資料の表3つに全部 在るか・②設定ファイルの資料から写した部分が、いまの資料から写し直したものと同じか）（Q10）
19. `.claude/tools/pre_audit_check.py`（:50-90・:470-490） — 照らしの道具を CHECKS と _MUST_IN_CHECKS に入れた所と、照らしだけを走らせる口 --check-indicator-sources（Q10）
20. `.claude/tools/gen_acceptance.py`（:1115-1132） — 設計書を作る前に①を照らす所 indicator_sources_problems（Q10）
21. `.claude/state/indicator_review/r3_draft_build.py`（:149-200・:396-440） — 資料から設定ファイルの中身を作る写し方 compute・cfg_block・lim_ranges（照らしの②がこれを使う）（Q8・Q10）
22. `.claude/breaks/b142_rci_list_stale.sh` — 壊すプログラム。一覧の RCI を rci_periods の組に戻すと、照らしの②が落ちるか（Q11）
23. `.claude/breaks/b143_rci_range_short.sh` — 壊すプログラム。RCI の範囲の上限を縮めると、番人⑬が落ちるか（Q11）
24. `SDK/.claude/ratchet/signal_families.md`（全文） — 作り直して再承認された型の表（部品 476 → 477・中身の指紋 0bdadafa…）（Q11）
25. `.claude/state/session_worklog_20261007.md`（:102-158） — この工事の経緯（§11〜§15）＝資料を調べた手順・道具の直し・照らしの道具・当てた結果・型の表の再承認・G2 が落ちた件

★直す相手になりうるファイルを必ず入れる (結果の「修正の指示」の「直す前の文字」を、監査が実物から写すため)。プログラムが作る文書 (設計書など) を監査するときは、その元データ (設計書なら、工事のフォルダ `.claude/state/verbatim/<工事名>/` の `やることの表.md`。承認の後は `SDK/.claude/ratchet/acceptance_archive/verbatim/<工事名>/`) も入れる。`acceptance_src.json` は 2026-09-30 から使っていない (ratchet に無い) ので、直す相手に書かない。

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = 設計書 `m2c15-rci-pivot-sources-20261007` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。あわせて、まこさんの要望を、この工事の後の実装が満たしているか（問い2・Q7）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `m2c15-rci-pivot-sources-20261007` の中身です。

---

## 監査対象の事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_config.json` | 247行（設定・資料に足した4種を写す＝指標ごとの一覧と値を埋めない種類の並びを、資料から道具が写し直す（照らしの道具の②が見る中身）） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/observe_config.json` | 293行（設定・資料に足した4種を写す＝指標ごとの一覧と値を埋めない種類の並びを、資料から道具が写し直す（照らしの道具の②が見る中身）） | 直した後の文字 |
| 3 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 148行（設定・資料に足した RCI の範囲を写す＝探す範囲を、資料から道具が写し直す（照らしの道具の②が見る中身）） | 直した後の文字 |
| 4 | `.claude/breaks/b142_rci_list_stale.sh` | なし（新しいファイル） | 直した後の文字 |
| 5 | `.claude/breaks/b143_rci_range_short.sh` | なし（新しいファイル） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:m2c15-rci-pivot-sources-20261007）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_config.json` | 当てた | 2026-10-07T14:19:24 |
| 2 | `SDK/scripts/priority_rebuild/observe_config.json` | 当てた | 2026-10-07T14:19:24 |
| 3 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-07T14:19:24 |
| 4 | `.claude/breaks/b142_rci_list_stale.sh` | 当てた | 2026-10-07T14:19:24 |
| 5 | `.claude/breaks/b143_rci_range_short.sh` | 当てた | 2026-10-07T14:19:24 |

### 必読に要るファイル（道具が設計書と実装から拾った）

| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15・M2-F-10b・M2-D-8） | 入れる |
| `SDK/scripts/priority_rebuild/observe_config.json` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b142_rci_list_stale.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b143_rci_range_short.sh` | 直す相手（TARGET） | 入れる |

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
- Q8：RCI の一覧と範囲は、資料から漏れなく・余計なく写っているか
- Q9：資料に足した4種の行は、調べた逐語とページの照らしのとおりか。前の141種の行は変わっていないか
- Q10：照らしの道具①②は、資料と設定ファイルのずれを毎回 見つけられるか
- Q11：壊すプログラム2本は、直しを外したときだけ落ちるか。RCI5 が増えた影響は、設計書に書いたものだけか

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- 前期間pivot の3種の計算の作り（前の週を使う足の扱い）（資料のメモは「外の2つ（StockCharts・TradingView）は、30分足より上の足を前の週から作る」と書くが、計算を変えるのは別の工事（指標の修正の3回目以降）。この工事は値を埋めない種類の並びから外すだけ（パラメータを持たない））
- 役割と閾値の資料を設定ファイルに写すこと（役割と閾値を設定に写す仕組みは今は無い。RCI の役割（勢い・向き・強さ・行き過ぎ）と閾値（±80・0）は資料の表に在るまま）
- 範囲の「短い方 < 長い方」の決まり（RCI は軸が1つなので当たらない。MACD・TSI の分は工事2）
- 成績表（material_ranking.json）の作り直し（M2-D-8。増える RCI の列は、作り直すまで成績表に行が無く、段の候補の順位に出ない）
- 監査に出す前のチェックの自己テストの P7-1 の落ち（この工事の前から在る（壊した見本の設計書を渡しても、設計書の形の誤りで止まらない）。next_step §6 に積む）

---

## 監査観点 (一般・auditor_template ①〜⑦)

該当なし（この監査は、実装が設計書のとおりかと、まこさんの要望を満たしているかだけを問う。①〜⑦の観点は、この争点に関係しない。結果の所見の「一般の観点」にも「該当なし」と書く）

---

## 監査観点 (本監査固有・Q1-QN)

★問いごとに優先度を付ける＝A（結論を変える）／B（実装の前に直す）／C（完成の測り方以外の書き漏れ）／D（結論に効かせない）。結果の所見は、この問いの番号をそのまま見出しにし、優先度の順に書く。時間が足りずに省いた問いは、結果にその番号を書く。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**優先度の理由**＝違えば、実装は設計書のとおりに作られていない

実装の前（HEAD の commit a6f8167（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる）。★同じファイルに、この工事より前に当てた別の工事の直しが重なっている＝m2c15-param-values-fix-20261007（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-fix-20261007.md` の 4-20・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）。実装の前は、HEAD の版に、その工事の実装の指示を当てた時刻の順に当てた版）の対象のファイル（`.claude/breaks/b142_rci_list_stale.sh`・`.claude/breaks/b143_rci_range_short.sh`・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）に、設計書 4-20 の実装の指示（5 件）を番号の順に当てた結果が、実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる））と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**優先度の理由**＝在れば、設計書に無い変更が実装に混ざっている

実装の前（HEAD の commit a6f8167（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる）。★同じファイルに、この工事より前に当てた別の工事の直しが重なっている＝m2c15-param-values-fix-20261007（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-fix-20261007.md` の 4-20・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）。実装の前は、HEAD の版に、その工事の実装の指示を当てた時刻の順に当てた版）と実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる））の差分（`.claude/breaks/b142_rci_list_stale.sh`・`.claude/breaks/b143_rci_range_short.sh`・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**優先度の理由**＝合わなければ、どの件を道具が当てたかを後から確かめられない

当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2c15-rci-pivot-sources-20261007`）が、実装の指示の 5 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**優先度の理由**＝当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない

承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-rci-pivot-sources-20261007.md`）と、監査の相手の設計書（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-rci-pivot-sources-20261007.md`。★`.claude/state/acceptance.md` は、この工事の後に別の工事の設計書で上書きされたので比べない）の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**優先度の理由**＝要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない

実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-rci-pivot-sources-20261007/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**優先度の理由**＝成り立たなければ、承認のときの「済」が根拠にならない

設計書の完成の条件（2 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources`・`python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog`

### Q7 — まこさんの要望を、この工事の後の実装が満たしているか（問い2）（優先度 A）

**優先度の理由**＝満たしていない要望が在れば、まこさんの要望が届いていない（この答えが問い2 の答えになる）

下に並べた まこさんの要望を、この工事の後の実装が満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。この問いの答えが、結論を決める問い2 の答えになる。

  1. 目的：「使う」にした4種を資料に足し、資料から設定ファイルに写して、engine_tuner が4種を資料の値で扱えるようにする
  2. 資料と設定ファイルのずれを、毎回 チェックで見つけられる形にし、やり直しの時間を減らす

### Q8 — RCI の一覧と範囲は、資料から漏れなく・余計なく写っているか（優先度 A）

**優先度の理由**＝写し誤ると、engine_tuner が教科書の値から組み始められないか、資料に無い値を探す

指標ごとの一覧の RCI は [[5], [7], [9], [26], [52]] です。資料の最初の値（スキャル 5・9・26／デイトレ 9）に、残す名前（V9 の RCI7・RCI9・RCI52）を足した形です。範囲は 5〜52 です（見つかった値と今の値の最小〜最大）。これが資料の行と、まこさんが OK した選び方（okd_param_rule_20261004）のとおりかを見てください。写したのは道具（r3_draft_build.py の compute・cfg_block・lim_ranges）で、私は値を書いていません。前期間pivot の3種は「パラメータを持たない」として、値を埋めない種類の並びから外れました。この扱いで、3種の列の作り方が変わっていないか（前から在る列の値の違い 0本）も見てください。

### Q9 — 資料に足した4種の行は、調べた逐語とページの照らしのとおりか。前の141種の行は変わっていないか（優先度 A）

**優先度の理由**＝資料の値が誤っていれば、照らしの道具は誤った資料と設定ファイルを同じ誤り方で比べ、誤りを見つけられない（設計書の 7-4）

調べる係が集めた逐語を、こちらの道具（verify_quotes.py・verify_quotes_w.py）がページを開き直して照らしました。一致しなかった逐語（外為どっとコムとザイFX! の2ページ）は、印 ✗ になり値に使っていません。足した4行の値が、印 ✓ の逐語だけから来ているかを見てください。表を作る道具は4本 直しました（list_on_families.py に --add・build_role_threshold_table.py と make_fix_plan.py は結果のファイルを決め打ちにせず全部 読む・extract_threshold_role_add.py は新しく作った）。前の141種の行は、控えと jq -S で比べて違い0でした。この比べ方で、行の中身の変化を見逃していないかを見てください。

### Q10 — 照らしの道具①②は、資料と設定ファイルのずれを毎回 見つけられるか（優先度 A）

**優先度の理由**＝まこさんの要望は「毎回チェックでミスがあり、やりなおしで膨大な時間がかかるのを改善してほしい」。照らしが働かなければ、同じ抜けがまた数日 気づかれない

①は「使う」の指標と資料の表3つの種類を、両方の向きで比べます（重複も止めます）。②は設定ファイルの2つの塊を、資料から写し直したものと1文字ずつ比べます。①は設計書を作る道具（TARGET に設定ファイルが在る工事だけ）と監査に出す前のチェックで、②は監査に出す前のチェックでだけ走ります。この置き場で、ずれが入る道（例＝指標を「使う」にする工事・資料を作り直す工事・設定ファイルを手で直す工事）を全部 捕まえられるかを見てください。★CC の自己申告＝照らしの道具は、Bash から直接 走らせられません（新しく作った .claude/tools の道具は、土台ゲートの一覧に入っていない）。そのため、監査に出す前のチェックの口（pre_audit_check.py --check-indicator-sources）から呼ぶ形にしました。★CC の自己申告（2つ目）＝監査に出す前のチェックの自己テストは、この工事の前から P7-1 の1件が落ちています（壊した見本の設計書を渡しても、設計書の形の誤りで止まらない）。next_step §6 に積みました。

### Q11 — 壊すプログラム2本は、直しを外したときだけ落ちるか。RCI5 が増えた影響は、設計書に書いたものだけか（優先度 B）

**優先度の理由**＝落ちない壊し方が在ると、写し直しが黙って戻る。書いていない影響が在ると、ほかの仕組みが黙って変わる

壊すプログラム b142・b143 を写しの作業場で走らせ、宣言した文で落ちるか、壊す対象がちょうど1か所かを見てください。RCI5 の列が増えたので、型の表の部品は 476 → 477 になり、まこさんに型の表と出口の型の表を再承認していただきました。★CC の自己申告＝再承認の後の監査に出す前のチェックで、G2 の番人が「差し替えられる材料が構造に無い」で落ちました。番人が乱数（種は固定）で作った構造の1本目を使う作りで、材料が1本 増えただけで1本目が変わったためです。番人の直しは、次の工事 g2-sentinel-material-pick-20261007 で行いました（別の依頼書）。この落ち方のほかに、材料が1本 増えたことで変わった所が無いかを見てください。★CC の自己申告（3つ目）＝4種を調べる係（サブエージェント1本）は 192,718 トークンを使いました。私の見込み（約8万〜15万）を超えました。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

件数: 0 件 (結果の外部検索の節にも「該当なし」と書く)

該当なし（この監査は、実装が設計書のとおりかを実物で照らす。外部の知見は答えに要らない。設計の理由を調べる外部検索は、設計書の監査で行う）

---

## 依頼を出した CC の自己申告

1. **この工事の外の作業中の変更**＝`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_request_understood.sh`・`.claude/tools/check_indicator_sources.py`・`.claude/tools/gen_acceptance.py`・`.claude/tools/gen_audit_docs.py`・`.claude/tools/pre_audit_check.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_signal_families.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）

(結果は、この番号ごとに1件ずつ答える)

---

## 結果ファイルフォーマット (auditor 用)

`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-07_m2c15_rci_pivot_sources_20261007_impl_cp65_audit_report.md` に、次の 11 節をこの順で出力する。★節の名前と並びは変えない。どの種類の監査でも同じ。

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
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_rci_pivot_sources_20261007_impl_cp65_audit_request.md
```

または

```
本依頼書を読んで監査して
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_rci_pivot_sources_20261007_impl_cp65_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp65_work/cp65_src.gen.md src_sha256=60a4017b17a295c17fbe70b4e0003943fc2a17544b30ec7b941611886c59fe5f body_sha256=c51582dd5f60b9fe5d744dd98fd60c4db1c39c24eb26dc6787f1532b76eec04d -->

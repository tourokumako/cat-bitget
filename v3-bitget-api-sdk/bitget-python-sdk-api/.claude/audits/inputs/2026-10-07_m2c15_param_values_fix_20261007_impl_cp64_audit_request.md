# 【監査依頼】CP64 — 監査 CP63 の修正1・4・6 を案 A で直す。M2-C-15（実装の監査）

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 19 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて、結果ファイルを次の順で書く（手で1から書かない）:
   - 結果の骨組みを道具で作業場に作る: `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_param_values_fix_20261007_impl_cp64_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp64_work/cp64_result.md`
   - 骨組みの「<監査が書く>」などの印を全部 埋める（見出しと並びは変えない）
   - 食い違い0件を確かめる: `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_param_values_fix_20261007_impl_cp64_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>`
   - 出す前に見直す: `python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` で見直し表を作り、全部の行（結果の見出しごと）に ①意味が通じるか ②実物と合うか（根拠＝ファイル名:行番号・実際に開いた行）③争点（この依頼書の結論を決める問い）に合うか と判定（OK／直した／該当なし（理由））を書き、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通す（結果を直したら表を作り直す・hook 11 が同じ照らしを掛ける）
   - 埋めた結果の全文を、結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-07_m2c15_param_values_fix_20261007_impl_cp64_audit_report.md` に Write で1回だけ書く（hook 11 が同じ照らしを掛ける。書いた後は書き替えられない）
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / CONDITIONAL-GO / NO-GO)
   - 重さごとの件数 (Critical / Major / Minor / Process)

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)
- 本物のファイルを書き替えること (写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp64_work/` に作る。最後に `git status --short` で書き替えていないことを示す)

### この監査の作業場

**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp64_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました。**判断が要る4つ（この工事は何のためか・必読・工事ごとの問い・要望のまとめ）は、CC が工事のフォルダの 監査依頼の手書き（実装の監査）.md に書き、まこさんが OK した文を写しました。ほかは道具が実物から作りました。問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・まこさんの要望が在る工事だけ）と、この工事で確かめてほしいことを問う工事ごとの問い（Q8〜Q11）です。

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-07
- 依頼者: CC（起案者）
- 監査区分: 実装の監査
- 監査対象タスク: M2-C-15・M2-F-10b・M2-D-8／設計書 m2c15-param-values-fix-20261007
- 監査の相手と版: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-fix-20261007.md` ／ ハッシュ値 ccc86b5472fea2eb970c7933580e2788145af1782444ab47138673068bfe284d
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-07_m2c15_param_values_fix_20261007_impl_cp64_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_param_values_fix_20261007_impl_cp64_audit_request.md`

---

## この監査で答えてほしいこと

### 結論を決める問い

- **問い1**＝設計書の実装の指示（16 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。あわせて、この工事で確かめてほしいこと（Q8〜Q11 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けている・工事ごとの問いで設計書と違う所が見つかれば NO。

- **問い2**＝この工事の後の実装が、下に並べた まこさんの要望（2 件）を満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。1つでも満たしていなければ NO（Q7 で照らす）。
  1. 目的：監査 CP63 の修正を全部 直し、前の工事の目的（パラメータが範囲から探されている）を実物で成り立たせる
  2. 修正1・4・6 を、まこさんが選んだ案 A で直す（範囲を作る道具を元から直し、ほかの5種類の範囲も変える）

(結論を決めるのは、これらの問いだけ。結果の「7. 総合判定」で、問いごとに YES / NO と根拠を書く)

### 結論の決め方

- **GO**＝問い1 と 問い2 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 と 問い2 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 と 問い2 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の番号と実物の行で示してください。

### この監査の前提

1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-param-values-fix-20261007/やることの表.md`）に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。
5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。

---

## 監査依頼の経緯

1. **この工事は何のためか**＝前の工事（m2c15-param-values-20261006）の目的＝まこさんの6項目の3番（パラメータが、範囲から探されている）を、実物でも成り立たせる。前の工事の実装の監査 CP63 は NO-GO だった（Critical 1・Major 3）。この工事は、その修正1・4・6 を案 A で直す。①段の候補を作る所が、列の数字が範囲の外なら使わない ②TSI の3種の範囲を名前の軸に正しく当てる ③VIDYA と T3 の範囲がカタログの列の数字を含む。②③の元＝範囲を作る道具が、今の値を資料の軸の順にそろえずに混ぜ、軸の数が違う今の値を捨てていた。元から直したので、StochRSI%K・%D・ALMA・MCGD・SSF の範囲も変わる（まこさん「全部OK」）
2. **この工事は何か**＝工事 m2c15-param-values-20261006（指標の修正の全体の表の2回目）の実装の監査 CP63 は NO-GO でした。この工事は、その修正1・4・6 を、まこさんが選んだ案 A で直します（まこさん「全部直す」）。前の工事に指示を足すと、前の17件の直した後の文字の塊の中を書き替え、設計書を作る道具の照らしが止まるので、新しい工事名にしました（まこさん「全部OK」）。中身は4つです。①修正1（Critical）＝段の候補を作る所（engine_tuner_gen.py の _group_usable_col）が、成績表の列の数字が範囲の外なら使わない形にします。前の工事の設計書 4-13 の3 に書いたのに、実物は禁止3（標本不足）しか見ていませんでした。②修正4（Major）＝TSI の3種の範囲を、名前の軸に正しく当てます（短い方 7〜25・長い方 4〜26 → 短い方 4〜13・長い方 7〜26）。③修正6（Major）＝VIDYA と T3 の範囲が、カタログの列（20・50・200）を含む形にします（VIDYA 14〜14 → 14〜200・T3 8〜34 → 8〜200）。④修正4・6 の元＝範囲を作る道具が、今の値と資料の値の軸の順をそろえずに混ぜ、軸の数が違う今の値を捨てていたので、元から直して修正対応表を作り直しました。同じ原因で、StochRSI%K・%D（14〜14 → 7〜21）・ALMA（9〜18 → 9〜200）・MCGD（10〜10 → 10〜200）・SSF（10〜10 → 10〜200）の範囲も変わります（まこさん「全部OK」）。材料の名前は1本も変わらず、カタログは 476 列のままです。前の工事の監査の修正2・5・7（前の工事の設計書の作り直し）は、この工事の設計書で受けます。（やることの番号 M2-C-15・M2-F-10b・M2-D-8）
   **この工事の位置**＝全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝材料を直す（監査 CP60 の修正・法則どおりの帯の部品・S1 の部品） → M2-F｜段ごとに測って並べ、上位を次の段へ渡す（段1〜段4）＝1本ずつの成績と順位を出す → M2-F-10b｜測る道具を直す（工事2）＝①正解ラベル2本との一致率で並べる ②手で組んだ土台を置いて、その上に候補を足して測る口 ③確認の窓でも測る口 ④段4 を役割ごとに動かす ⑤6項目のチェックを通す → M2-D｜場面を分ける材料の順位を engine_tuner に渡す → M2-D-8｜直した材料で、成績表（material_ranking.json）を作り直す → この工事

---

## 着手前必読 (省略禁止・auditor 用・19 件)

**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-fix-20261007.md` — 監査の相手（設計書・プログラムが作った）
2. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:m2c15-param-values-fix-20261007 の行）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-param-values-fix-20261007/やることの表.md` — 設計書の元（やることの表）＝修正の指示を書く先
4. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — 目標（全月 net ≥ $1,900）と全体戦略、ハード制約（§4.6＝H2 未来参照なし・H6 値段の高さで値が変わらない ほか）。計算式は変えていないが、範囲と段の候補の直しが制約に触れないかを照らす
5. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-103） — engine_tuner の目的と、作ってはいけないもの（乱数・探す値を CC が点の一覧で限定するもの）。範囲が1点だった5種類が範囲になる直しを照らす
6. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:95-146） — M2 が M1〜M6 のどこに当たり、何ができたら終わりか
7. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:3-46・:995-1040・:1173-1183） — M2 で作っている物と、この工事（M2-C-15＝材料を直す）の行と中身
8. `SDK/.claude/audits/2026-10-06_m2c15_param_values_20261006_impl_cp63_audit_report.md`（全文） — この工事が直す相手。修正1・4・6 の中身と、修正2・5・7（前の工事の設計書の作り直し）をこの工事の設計書で受けたこと
9. `SDK/.claude/ratchet/acceptance_archive/m2c15-param-values-fix-20261007.md`（全文） — 承認済みの設計書の控え（実装の指示16件・完成の条件2行・承認のプログラムが測った）
10. `SDK/scripts/priority_rebuild/engine_tuner_gen.py`（:231-330・:420-471） — 範囲を作る関数 material_ranges・範囲の照らし param_in_range・説明を直した _mat_from_col・範囲の照らしを足した _group_usable_col（Q8）
11. `SDK/scripts/priority_rebuild/observe_diag.py`（:7100-7142） — 軽い口 selftest_catalog の番人⑬（カタログの名前の全部に広げた）と⑭（段の候補は範囲の外の列を使わない）（Q8・Q10）
12. `SDK/scripts/priority_rebuild/recipes/search_limits.json`（:44-160） — 写し直した範囲 material_param_ranges（TSI の3種・StochRSI の2種・ALMA・MCGD・SSF・T3・VIDYA）と注記（Q9・Q10）
13. `SDK/scripts/priority_rebuild/observe_config.json`（:167-300） — 残す名前の行と、値を埋めない種類の並び（_material_params_pending）の写し直し
14. `.claude/state/indicator_review/apply_param_rule.py`（:250-300） — 範囲を作る道具の直し＝今の値を、名前の軸と資料の軸の対応で資料の軸へ入れてから混ぜる（Q9）
15. `.claude/state/indicator_review/r3_draft_build.py`（:56-100） — 名前の軸と資料の軸の対応 AXIS_MAP に足した TSI の3種（[1, 0, 2]）（Q9）
16. `.claude/state/indicator_params_by_strategy.md`（:30-45・:130-150） — 作り直した修正対応表の TSI・StochRSI・ALMA・MCGD・SSF・T3・VIDYA の行（Q9・Q10）
17. `.claude/breaks/b140_group_range_ignored.sh` — 壊すプログラム。_group_usable_col の範囲の照らしを外すと、⑭が落ちるか（Q11）
18. `.claude/breaks/b141_catalog_out_of_range.sh` — 壊すプログラム。T3 の範囲の上限を 34 に戻すと、⑬が落ちるか（Q11）
19. `.claude/state/session_worklog_20261007.md`（:3-101） — この工事の経緯（§1〜§10）＝監査の結果の読み方・範囲を作る道具を元から直した経緯・承認が一度止まった件・当てた結果

★直す相手になりうるファイルを必ず入れる (結果の「修正の指示」の「直す前の文字」を、監査が実物から写すため)。プログラムが作る文書 (設計書など) を監査するときは、その元データ (設計書なら、工事のフォルダ `.claude/state/verbatim/<工事名>/` の `やることの表.md`。承認の後は `SDK/.claude/ratchet/acceptance_archive/verbatim/<工事名>/`) も入れる。`acceptance_src.json` は 2026-09-30 から使っていない (ratchet に無い) ので、直す相手に書かない。

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = 設計書 `m2c15-param-values-fix-20261007` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。あわせて、まこさんの要望を、この工事の後の実装が満たしているか（問い2・Q7）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `m2c15-param-values-fix-20261007` の中身です。

---

## 監査対象の事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_diag.py` | 7115行（selftest_catalog・修正6＝軽い口の⑬（範囲がカタログの数字を含む）を、カタログの名前の全部に広げる） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/observe_diag.py` | 7125行（selftest_catalog・修正1＝軽い口に⑭（段の候補は範囲の外の列を使わない・範囲の中の列は使う）を足す） | 直した後の文字 |
| 3 | `SDK/scripts/priority_rebuild/observe_config.json` | 250行（設定・残す名前を写し直す（監査 CP63 の修正9 で正規表現を直したので、確認のレシピの MACDヒスト%(12,26,9) が入る・カタログの列は変わらない）） | 直した後の文字 |
| 4 | `SDK/scripts/priority_rebuild/observe_config.json` | 293行（設定・P-4＝値を埋めずに並べる種類を、作り直した修正対応表から道具が写し直す（範囲が1点でなくなった種類が外れる）） | 直した後の文字 |
| 5 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 60〜62行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す） | 直した後の文字 |
| 6 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 83〜84行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す） | 直した後の文字 |
| 7 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 123行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す） | 直した後の文字 |
| 8 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 131行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す） | 直した後の文字 |
| 9 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 139行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す） | 直した後の文字 |
| 10 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 141行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す） | 直した後の文字 |
| 11 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 145行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す） | 直した後の文字 |
| 12 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 150行（設定・修正4・6＝範囲を、作り直した修正対応表と名前の軸の対応から道具が写し直す（TSI・VIDYA・T3 ほか）。注記に広げる決まりを足す） | 直した後の文字 |
| 13 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 430行（_mat_from_col・修正1＝_mat_from_col の説明の文を事実に合わせる（範囲を照らすのは _group_usable_col）） | 直した後の文字 |
| 14 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 462〜463行（_group_usable_col・修正1＝_group_usable_col が、列の数字が範囲の外なら段の候補に使わない） | 直した後の文字 |
| 15 | `.claude/breaks/b140_group_range_ignored.sh` | なし（新しいファイル） | 直した後の文字 |
| 16 | `.claude/breaks/b141_catalog_out_of_range.sh` | なし（新しいファイル） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:m2c15-param-values-fix-20261007）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-07T11:43:47 |
| 2 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-07T11:43:47 |
| 3 | `SDK/scripts/priority_rebuild/observe_config.json` | 当てた | 2026-10-07T11:43:47 |
| 4 | `SDK/scripts/priority_rebuild/observe_config.json` | 当てた | 2026-10-07T11:43:47 |
| 5 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-07T11:43:47 |
| 6 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-07T11:43:47 |
| 7 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-07T11:43:47 |
| 8 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-07T11:43:47 |
| 9 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-07T11:43:47 |
| 10 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-07T11:43:47 |
| 11 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-07T11:43:47 |
| 12 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-07T11:43:47 |
| 13 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-07T11:43:47 |
| 14 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-07T11:43:47 |
| 15 | `.claude/breaks/b140_group_range_ignored.sh` | 当てた | 2026-10-07T11:43:47 |
| 16 | `.claude/breaks/b141_catalog_out_of_range.sh` | 当てた | 2026-10-07T11:43:47 |

### 必読に要るファイル（道具が設計書と実装から拾った）

| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15・M2-F-10b・M2-D-8） | 入れる |
| `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_config.json` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b140_group_range_ignored.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b141_catalog_out_of_range.sh` | 直す相手（TARGET） | 入れる |
| `SDK/.claude/ratchet/material_ranking.json` | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` が名前を出す（実装の前後の差分） | 入れない（成績表。この工事では作り直していない（設計書の 3-1 の3番）。範囲の外の列は、作り直すまで成績表に残り、段の候補で外れる） |

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
- Q8：段の候補は、範囲の外の列を全部の呼ぶ所で外すか。外したことで、通る案が変わっていないか
- Q9：TSI の3種の範囲は、名前の軸に正しく当たっているか。範囲を作る道具の直しで、ほかの種類の範囲が誤って変わっていないか
- Q10：VIDYA と T3 の範囲は、カタログの列の数字を全部 含むか。番人⑬を広げたことで、見逃す形が残っていないか
- Q11：壊すプログラム2本は、直しを外したときだけ落ちるか。監査 CP63 のほかの修正の扱いは正しいか

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- 範囲の「短い方 < 長い方」の決まり（MACD の3種＝短い方 3〜12・長い方 10〜26／TSI の3種＝短い方 4〜13・長い方 7〜26）（範囲を作る関数は軸どうしの関係を持たない（engine_tuner_gen.py の material_ranges の説明）。探す側をつなぐ工事2 に入れる。TSI は、資料のスキャルの値 [7,4,2] の長い方 7 が、デイトレの短い方 13 より小さいので、軸を正しく当てても 7〜13 で重なる）
- 材料の名前の一覧（material_params）を変えること（この工事は範囲と段の候補の直し。カタログは 476 列のまま（写しで同じと確かめた））
- 成績表（material_ranking.json）の作り直し（M2-D-8 で、まこさんの OK の後に走らせる。この工事の後は、範囲の外の列（ROC3・ROC6 ほか）は段の候補に出ない）
- 指標の修正の3回目・4回目（K-3・B-1・S-1・K-7・K-4・R-1・T-1）（まこさん「分ける」）
- 前の工事の設計書を作り直すこと（監査 CP63 の修正2・5・7）（前の工事の設計書を作り直しても、この工事の設計書で上書きされ、承認もしないので記録に残らない。修正1・4・6 の決定は、この工事の 3-2 に書く）
- 監査 CP63 の Minor-5（出口の型の表の元データ exit_families_rules.json の説明の文の古い数）と Minor-6（依頼書の自己申告の書き方）（監査が修正の指示を書いていない（表示だけ・書き方だけ））

---

## 監査観点 (一般・auditor_template ①〜⑦)

該当なし（この監査は、実装が設計書のとおりかと、まこさんの要望を満たしているかだけを問う。①〜⑦の観点は、この争点に関係しない。結果の所見の「一般の観点」にも「該当なし」と書く）

---

## 監査観点 (本監査固有・Q1-QN)

★問いごとに優先度を付ける＝A（結論を変える）／B（実装の前に直す）／C（完成の測り方以外の書き漏れ）／D（結論に効かせない）。結果の所見は、この問いの番号をそのまま見出しにし、優先度の順に書く。時間が足りずに省いた問いは、結果にその番号を書く。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**優先度の理由**＝違えば、実装は設計書のとおりに作られていない

実装の前（HEAD の commit a6f8167（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる））の対象のファイル（`.claude/breaks/b140_group_range_ignored.sh`・`.claude/breaks/b141_catalog_out_of_range.sh`・`SDK/scripts/priority_rebuild/engine_tuner_gen.py`・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/observe_diag.py`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）に、設計書 4-20 の実装の指示（16 件）を番号の順に当てた結果が、実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる）。★同じファイルに、この工事より後に当てた別の工事の直しも入っている＝m2c15-rci-pivot-sources-20261007（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-rci-pivot-sources-20261007.md` の 4-20・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）。実装の後は、実装の前にこの工事の実装の指示を当てた版。作業中の変更と比べるときは、後の工事の実装の指示を同じ順に当ててから比べる（後の工事の行は、その工事の依頼書で照らす））と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**優先度の理由**＝在れば、設計書に無い変更が実装に混ざっている

実装の前（HEAD の commit a6f8167（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる））と実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる）。★同じファイルに、この工事より後に当てた別の工事の直しも入っている＝m2c15-rci-pivot-sources-20261007（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-rci-pivot-sources-20261007.md` の 4-20・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）。実装の後は、実装の前にこの工事の実装の指示を当てた版。作業中の変更と比べるときは、後の工事の実装の指示を同じ順に当ててから比べる（後の工事の行は、その工事の依頼書で照らす））の差分（`.claude/breaks/b140_group_range_ignored.sh`・`.claude/breaks/b141_catalog_out_of_range.sh`・`SDK/scripts/priority_rebuild/engine_tuner_gen.py`・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/observe_diag.py`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**優先度の理由**＝合わなければ、どの件を道具が当てたかを後から確かめられない

当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2c15-param-values-fix-20261007`）が、実装の指示の 16 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**優先度の理由**＝当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない

承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-fix-20261007.md`）と、監査の相手の設計書（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-param-values-fix-20261007.md`。★`.claude/state/acceptance.md` は、この工事の後に別の工事の設計書で上書きされたので比べない）の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**優先度の理由**＝要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない

実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-param-values-fix-20261007/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**優先度の理由**＝成り立たなければ、承認のときの「済」が根拠にならない

設計書の完成の条件（2 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog`

### Q7 — まこさんの要望を、この工事の後の実装が満たしているか（問い2）（優先度 A）

**優先度の理由**＝満たしていない要望が在れば、まこさんの要望が届いていない（この答えが問い2 の答えになる）

下に並べた まこさんの要望を、この工事の後の実装が満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。この問いの答えが、結論を決める問い2 の答えになる。

  1. 目的：監査 CP63 の修正を全部 直し、前の工事の目的（パラメータが範囲から探されている）を実物で成り立たせる
  2. 修正1・4・6 を、まこさんが選んだ案 A で直す（範囲を作る道具を元から直し、ほかの5種類の範囲も変える）

### Q8 — 段の候補は、範囲の外の列を全部の呼ぶ所で外すか。外したことで、通る案が変わっていないか（優先度 A）

**優先度の理由**＝外れなければ、範囲の外の数字の列で案が組まれ、案を作った後の出どころの検査で止まる（監査 CP63 の Critical-1）。外し方が強すぎれば、範囲の中の列まで候補から消える

_group_usable_col は、列の数字が範囲の外なら False を返す形にしました（param_in_range を呼ぶ）。この関数を呼ぶ所は6か所です（設計書の 4-13 の2・道具が構文木で数えた）。6か所のどれでも、範囲の外の列が外れるかを見てください。設計書は「止まる所が前に来るだけで、通る案は変わらない見込み」と書きましたが、走らせて確かめてはいません（段の本走は M2-F）。番人⑭は ROC3（外）と ROC12（中）の2本だけで働きを見ます。数字が2つ以上の列（例＝MACD の3つの数字）で、param_in_range が軸ごとに正しく照らすかも見てください。

### Q9 — TSI の3種の範囲は、名前の軸に正しく当たっているか。範囲を作る道具の直しで、ほかの種類の範囲が誤って変わっていないか（優先度 A）

**優先度の理由**＝軸を取り違えると、短い方の期間の範囲で長い方を探すことになる

名前の軸は tsi(fast, slow, signal) です。資料の軸は first（長い方・先にならす）・second（短い方）・signal です。私は、ライブラリ（pandas_ta_classic の momentum/tsi.py）が slow を先に、fast を後に掛けることを見て、AXIS_MAP の TSI を [1, 0, 2] にしました。この対応が正しいかを、ライブラリの実物で確かめてください。範囲を作る道具（apply_param_rule.py）は、今の値を資料の軸へ入れてから混ぜる形にしました。1回目の直しでは EMA傾き の範囲が「決まらない」に落ちたので、同じ軸の数なら今までどおり混ぜる枝を残しました（worklog §3）。修正対応表で変わったのは9行です（TSI の3種・StochRSI の2種・ALMA・MCGD・SSF・VIDYA）。この9行のほかに、誤って変わった行が無いかを、直す前の表と比べてください。

### Q10 — VIDYA と T3 の範囲は、カタログの列の数字を全部 含むか。番人⑬を広げたことで、見逃す形が残っていないか（優先度 A）

**優先度の理由**＝範囲がカタログの数字を含まないと、engine_tuner はカタログに在る列の値に届かない

⑬は、カタログの名前の全部（set(_nm_k1)）を見る形にしました。ただし、設定の範囲が無い種類は飛ばします（指標ごとの一覧の種類だけは止める）。この飛ばしで、範囲を書くべきなのに書いていない種類を見逃さないかを見てください。T3 は「教科書の範囲」8〜34 でしたが、カタログの数字（20・50・200）を含むように 8〜200 に広げました。範囲を広げる決まりが、一覧に入らない種類にも掛かる形にしたこと（r3_draft_build.py の直し）が、設計書の 4-0 の⑥のとおり2軸（ROC・T3）だけに効いているかを見てください。

### Q11 — 壊すプログラム2本は、直しを外したときだけ落ちるか。監査 CP63 のほかの修正の扱いは正しいか（優先度 B）

**優先度の理由**＝落ちない壊し方が在ると、直しが黙って戻る。修正の扱いを誤ると、CP63 の指摘が直らないまま残る

壊すプログラム b140・b141 を写しの作業場で走らせ、宣言した文で落ちるか、壊す対象がちょうど1か所かを見てください。CP63 の修正2・5・7（前の工事の設計書の作り直し）は、まこさんの決定でこの工事の設計書で受けました（設計書の 3-1 の5番）。修正3（require_design_check_before_approval.py）と修正13（gen_acceptance.py）は、当てる道具が守りの仕組みとして当てないと出したので、私が手で直しました（コミット a6f8167）。★CC の自己申告＝修正3 の hook には自己テストの口が無く、直した行の働き（T 以外の ❌ と T6 が一緒に出たら止める）は、承認の前の検査の仮当てで初めて通ります。★CC の自己申告（2つ目）＝この工事の承認は1回、「新しく作るはずの壊すプログラムが、もう在る」で止まりました。私が返信を出した直後の仮当て（本物に約4分半 書いて戻す）と承認が重なったためです（worklog §9）。止まった後、b140・b141 が残っていないこと・直す相手4本の git の差分が0であることを確かめてから、承認を打ち直していただきました。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

件数: 0 件 (結果の外部検索の節にも「該当なし」と書く)

該当なし（この監査は、実装が設計書のとおりかを実物で照らす。外部の知見は答えに要らない。設計の理由を調べる外部検索は、設計書の監査で行う）

---

## 依頼を出した CC の自己申告

1. **この工事の外の作業中の変更**＝`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_request_understood.sh`・`.claude/tools/check_indicator_sources.py`・`.claude/tools/gen_acceptance.py`・`.claude/tools/gen_audit_docs.py`・`.claude/tools/pre_audit_check.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_signal_families.py`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）

(結果は、この番号ごとに1件ずつ答える)

---

## 結果ファイルフォーマット (auditor 用)

`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-07_m2c15_param_values_fix_20261007_impl_cp64_audit_report.md` に、次の 11 節をこの順で出力する。★節の名前と並びは変えない。どの種類の監査でも同じ。

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
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_param_values_fix_20261007_impl_cp64_audit_request.md
```

または

```
本依頼書を読んで監査して
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_param_values_fix_20261007_impl_cp64_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp64_work/cp64_src.gen.md src_sha256=0d1ea464c746b40cdbcdfbce8dcc6084339673f85044c899054a5339aa43fae6 body_sha256=0853e9db79d4ae9c5b27ae6fc616015f6b9a6ea2da74dfed06d152cac535083a -->

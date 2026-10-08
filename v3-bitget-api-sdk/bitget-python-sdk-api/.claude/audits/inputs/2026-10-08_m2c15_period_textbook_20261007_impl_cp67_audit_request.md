# 【監査依頼】CP67 — K-3a 期間の区切り＝教科書の期間の版を別の材料として11種 足す・範囲の直しを設定に写す。M2-C-15（実装の監査）

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 23 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて、結果ファイルを次の順で書く（手で1から書かない）:
   - 結果の骨組みを道具で作業場に作る: `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-08_m2c15_period_textbook_20261007_impl_cp67_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp67_work/cp67_result.md`
   - 骨組みの「<監査が書く>」などの印を全部 埋める（見出しと並びは変えない）
   - 食い違い0件を確かめる: `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-08_m2c15_period_textbook_20261007_impl_cp67_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>`
   - 出す前に見直す: `python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` で見直し表を作り、全部の行（結果の見出しごと）に ①意味が通じるか ②実物と合うか（根拠＝ファイル名:行番号・実際に開いた行）③争点（この依頼書の結論を決める問い）に合うか と判定（OK／直した／該当なし（理由））を書き、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通す（結果を直したら表を作り直す・hook 11 が同じ照らしを掛ける）
   - 埋めた結果の全文を、結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-08_m2c15_period_textbook_20261007_impl_cp67_audit_report.md` に Write で1回だけ書く（hook 11 が同じ照らしを掛ける。書いた後は書き替えられない）
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / CONDITIONAL-GO / NO-GO)
   - 重さごとの件数 (Critical / Major / Minor / Process)

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)
- 本物のファイルを書き替えること (写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp67_work/` に作る。最後に `git status --short` で書き替えていないことを示す)

### この監査の作業場

**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp67_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました。**判断が要る4つ（この工事は何のためか・必読・工事ごとの問い・要望のまとめ）は、CC が工事のフォルダの 監査依頼の手書き（実装の監査）.md に書き、まこさんが OK した文を写しました。ほかは道具が実物から作りました。問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・まこさんの要望が在る工事だけ）と、この工事で確かめてほしいことを問う工事ごとの問い（Q8〜Q11）です。

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-08
- 依頼者: CC（起案者）
- 監査区分: 実装の監査
- 監査対象タスク: M2-C-15・M2-F-10f・M2-D-8・M2-F-10b／設計書 m2c15-period-textbook-20261007
- 監査の相手と版: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-period-textbook-20261007.md` ／ ハッシュ値 8855d4edb960e5814d9cbe7409eec680a3a1e898a00bfb1b1296a097f5b9da7e
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-08_m2c15_period_textbook_20261007_impl_cp67_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-08_m2c15_period_textbook_20261007_impl_cp67_audit_request.md`

---

## この監査で答えてほしいこと

### 結論を決める問い

- **問い1**＝設計書の実装の指示（24 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。あわせて、この工事で確かめてほしいこと（Q8〜Q11 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けている・工事ごとの問いで設計書と違う所が見つかれば NO。

(結論を決めるのは、この問いだけ。結果の「7. 総合判定」で、問いごとに YES / NO と根拠を書く)

### 結論の決め方

- **GO**＝問い1 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の番号と実物の行で示してください。

### この監査の前提

1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-period-textbook-20261007/やることの表.md`）に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。
5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。

---

## 監査依頼の経緯

1. **この工事は何のためか**＝監査 CP60 が「教科書と違う作り」と指摘した材料のうち、期間の区切りに当たる11種（UTC 0時から積み上げる当日VWAP・典型価格の移動窓の VWAP典型・前日と当日の POC・VAH・VAL・前週pivot の PP・R1・S1）を、今の版を残したまま別の材料として足す。engine_tuner が教科書の版と今の版の両方を材料として扱えるようにし、どちらが良いかを後の段（M2-F-10f）で比べられるようにする
   K-7 で決まった範囲の直し（BB%b の本数 10〜50・倍率 1.9〜2.1、W字 の深さ 0〜0.06 ほか）を、資料から設定ファイルに写す。engine_tuner が教科書の値まで探せるようにする
   11種の資料の行は新しく調べず、同じ指標の今の行の調べた結果を使う
2. **この工事は何か**＝監査 CP60 は、今の材料のいくつかが教科書と違う作りだと指摘しました。VWAP は教科書ではセッションの始まりから積み上げる典型価格ですが、今の材料は終値の288本の移動窓です。出来高プロファイル（POC・VAH・VAL）は教科書では前のセッションの値を後のセッションで使いますが、今の材料は直前288本の移動窓です。まこさんは、今の版を残し、教科書の版を別の材料として足して、後で比べる形を決めました（K-3 の「A」）。K-7 では、前期間pivot に前の週の版を足すこと、BB と W字 の範囲を教科書の値に届くように広げることも決まりました。この工事は、その11種を観察の道具と参照表に足し、範囲の直しを設定ファイルに写します。11種の資料の行は、新しく調べずに同じ指標の今の行の調べた結果を使います（まこさん「B」）。前から在る列の値は1本も変えません。どちらの版が良いかを比べるのは、この工事ではなく M2-F-10f です。（やることの番号 M2-C-15・M2-F-10f・M2-D-8・M2-F-10b）
   **この工事の位置**＝全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝材料を直す（監査 CP60 の修正・法則どおりの帯の部品・S1 の部品） → M2-F｜段ごとに測って並べ、上位を次の段へ渡す（段1〜段4）＝1本ずつの成績と順位を出す → M2-F-10f｜教科書の版と今の版で値が違う指標を、一致率で比べ、レジーム判定に使う版を決める（上位足の1本の遅れも、直す前と後で比べる） → M2-D｜場面を分ける材料の順位を engine_tuner に渡す → M2-D-8｜直した材料で、成績表（material_ranking.json）を作り直す → M2-F-10b｜測る道具を直す（工事2）＝①正解ラベル2本との一致率で並べる ②手で組んだ土台を置いて、その上に候補を足して測る口 ③確認の窓でも測る口 ④段4 を役割ごとに動かす ⑤6項目のチェックを通す → この工事

---

## 着手前必読 (省略禁止・auditor 用・23 件)

**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-period-textbook-20261007.md` — 監査の相手（設計書・プログラムが作った）
2. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:m2c15-period-textbook-20261007 の行）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-period-textbook-20261007/やることの表.md` — 設計書の元（やることの表）＝修正の指示を書く先
4. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — 目標（全月 net ≥ $1,900）と全体戦略、ハード制約（§4.6＝H2 未来参照なし・H6 値段の高さで値が変わらない ほか）。足した11種が、今の足より先の値を使っていないかを照らす
5. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-103） — engine_tuner の目的と、作ってはいけないもの（乱数・探す値を CC が点の一覧で限定するもの）
6. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:95-146） — M2 が M1〜M6 のどこに当たり、何ができたら終わりか
7. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:3-46・:995-1040・:1173-1183） — M2 で作っている物と、この工事（M2-C-15＝材料を直す）の行と中身
8. `SDK/.claude/ratchet/acceptance_archive/m2c15-period-textbook-20261007.md`（全文） — 承認済みの設計書の控え（実装の指示24件・完成の条件4行・3-2 で決めた5つ）
9. `SDK/scripts/priority_rebuild/observe_diag.py`（:361-430・:935-1025・:1500-1545） — 出来高プロファイルの切り出し（_vp_one）と日で区切る版（_vp_by_day）・当日VWAP（_vwap_day）・前の週を選べる pivot（_pivot_prev_period）・11種の登録とカタログ（Q8・Q9）
10. `SDK/scripts/priority_rebuild/indicator_reference_diag.py`（:925-935・:1236-1460・:4716・:5031-5032） — 11種の定義と既知答え（合成の足の手計算）・pandas-ta の vwap との2つ目の照合・系統（Q8）
11. `SDK/scripts/priority_rebuild/recipes/search_limits.json`（:44-152） — 資料から写した探す範囲（BB%b・W字 ほか K-7 の直し）（Q10）
12. `.claude/state/indicator_review/k7_range_fix.json` — まこさんが OK した範囲の直し（K-7）。資料に写した元（Q10）
13. `.claude/state/indicator_review/research/alias_map.json` — 11種の資料の行を、どの指標の今の行から作ったかの対応（まこさん「B」）（Q10）
14. `.claude/state/indicator_params_by_strategy.md`（:165-175） — 資料の表（パラメータの最初の値と範囲）に足した11種の行（Q10）
15. `.claude/state/indicator_review/r3_draft_build.py`（:152-200・:399-440） — 資料から設定ファイルの中身を作る写し方 compute・cfg_block・lim_ranges（照らしの②がこれを使う）（Q10）
16. `SDK/.claude/memory/regime_detection_kb.md`（:1290-1295） — 指標の種類・材料の一覧・部品の件数の囲み（gen_materials.py が書き出す）（Q9）
17. `.claude/breaks/b145_vwap_day_no_reset.sh` — 壊すプログラム。積み上げを日で区切らない形に戻すと、既知答えが落ちるか（Q11）
18. `.claude/breaks/b146_pivot_week_as_day.sh` — 壊すプログラム。前の週の区切りを外すと、既知答えが落ちるか（Q11）
19. `.claude/breaks/b147_vp_today_from_start.sh` — 壊すプログラム。当日の出来高プロファイルの窓をデータの始まりからにすると、既知答えが落ちるか（Q11）
20. `.claude/breaks/b148_bb_range_not_widened.sh` — 壊すプログラム。BB%b の範囲を直す前に戻すと、照らしの②が落ちるか（Q11）
21. `SDK/.claude/ratchet/signal_families.md`（全文） — 作り直して再承認された型の表（部品 477 → 488・中身の指紋 49f9feba…）（Q9）
22. `.claude/state/session_worklog_20261007.md`（:240-267） — この工事の経緯（§25〜§26）＝K-3 を3つに分けた・読むもの宣言・資料の道具の直し・写しで確かめる道具
23. `.claude/state/session_worklog_20261008.md`（:3-49） — この工事の経緯（§1〜§4）＝写しの確かめ・工事を2つに分けた・承認が2回 止まった件・当てた結果・型の表の再承認・G2・H2

★直す相手になりうるファイルを必ず入れる (結果の「修正の指示」の「直す前の文字」を、監査が実物から写すため)。プログラムが作る文書 (設計書など) を監査するときは、その元データ (設計書なら、工事のフォルダ `.claude/state/verbatim/<工事名>/` の `やることの表.md`。承認の後は `SDK/.claude/ratchet/acceptance_archive/verbatim/<工事名>/`) も入れる。`acceptance_src.json` は 2026-09-30 から使っていない (ratchet に無い) ので、直す相手に書かない。

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = 設計書 `m2c15-period-textbook-20261007` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `m2c15-period-textbook-20261007` の中身です。

---

## 監査対象の事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_diag.py` | 367〜391行（_vp_levels・監査 CP60 の修正42＝出来高プロファイルの1つの窓の計算を _vp_one に切り出し（計算は変えない）、日で区切る版 _vp_by_day を足す） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/observe_diag.py` | 891〜892行（<モジュール直下>・監査 CP60 の修正41 の (b)(c)＝典型価格の移動窓の VWAP と、UTC 0時から積み上げる VWAP を、今の版を残して足す） | 直した後の文字 |
| 3 | `SDK/scripts/priority_rebuild/observe_diag.py` | 913行（_pivot_prev_period・K-7 の決定＝前期間pivot の作りに「前の週」を選べる引数を足す（渡さなければ今までと同じ）） | 直した後の文字 |
| 4 | `SDK/scripts/priority_rebuild/observe_diag.py` | 918〜920行（_pivot_prev_period・K-7 の決定＝unit="W" のときは前の週（月曜0時 UTC 始まり）で区切る） | 直した後の文字 |
| 5 | `SDK/scripts/priority_rebuild/observe_diag.py` | 934行（<モジュール直下>・K-7 の決定＝前の週で固定する pivot の3種を、今の前の日の版を残して足す） | 直した後の文字 |
| 6 | `SDK/scripts/priority_rebuild/observe_diag.py` | 941〜942行（<モジュール直下>・監査 CP60 の修正42＝前の日で固定・その日の0時から育つ POC・VAH・VAL の6種を、今の版を残して足す） | 直した後の文字 |
| 7 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1429〜1430行（build_catalog・足した VWAP の2種をカタログに入れる（典型価格の移動窓は今の VWAP と同じ窓の一覧で作る）） | 直した後の文字 |
| 8 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1447行（build_catalog・足した前週pivot の3種をカタログに入れる） | 直した後の文字 |
| 9 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1450〜1453行（build_catalog・足した日で区切る出来高プロファイルの6種をカタログに入れる） | 直した後の文字 |
| 10 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 942行（_r・足す11種の「使う」の決定（まこさんの逐語のファイル）を、登録の mako の欄から1か所で引けるようにする） | 直した後の文字 |
| 11 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1226〜1227行（<モジュール直下>・監査 CP60 の修正41 の (b)(c)＝参照表に登録し、手計算の既知答え・教科書の独立実装・ta との照合を付ける） | 直した後の文字 |
| 12 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1299〜1301行（<モジュール直下>・K-7 の決定＝前週pivot の3種を参照表に登録し、週と日を見分ける手計算の既知答えを付ける） | 直した後の文字 |
| 13 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1320〜1325行（<モジュール直下>・監査 CP60 の修正42＝日で区切る POC・VAH・VAL の6種を参照表に登録し、日の区切りを見分ける手計算の既知答えを付ける） | 直した後の文字 |
| 14 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4604行（<モジュール直下>・足す11種の系統（構造・位置）を書く） | 直した後の文字 |
| 15 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4914行（<モジュール直下>・足す11種の業界のライブラリとの対応を書く（観察の道具の検査10 が全部の種類に求める）） | 直した後の文字 |
| 16 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 929〜930行（<モジュール直下>・当日VWAP を pandas-ta の vwap と値で照らす（2つ目の照合）） | 直した後の文字 |
| 17 | `.claude/memory/regime_detection_kb.md` | 1290〜1295行（文書・足す11種で材料の種類と一覧の行の数が変わる＝KB の件数の囲み（gen_materials.py --write が書き出す所）を、写しで数えた文に置き換える（材料の文書の自己テストの B3・B4 と承認の前の検査 A12 が見る）） | 直した後の文字 |
| 18 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 77行（設定・資料の範囲の直し（BB%b・BB幅・W字＝まこさん「OK」）を、探す範囲に道具が写し直す（照らしの道具の②が見る中身）） | 直した後の文字 |
| 19 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 91行（設定・資料の範囲の直し（BB%b・BB幅・W字＝まこさん「OK」）を、探す範囲に道具が写し直す（照らしの道具の②が見る中身）） | 直した後の文字 |
| 20 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 104行（設定・資料の範囲の直し（BB%b・BB幅・W字＝まこさん「OK」）を、探す範囲に道具が写し直す（照らしの道具の②が見る中身）） | 直した後の文字 |
| 21 | `.claude/breaks/b145_vwap_day_no_reset.sh` | なし（新しいファイル） | 直した後の文字 |
| 22 | `.claude/breaks/b146_pivot_week_as_day.sh` | なし（新しいファイル） | 直した後の文字 |
| 23 | `.claude/breaks/b147_vp_today_from_start.sh` | なし（新しいファイル） | 直した後の文字 |
| 24 | `.claude/breaks/b148_bb_range_not_widened.sh` | なし（新しいファイル） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:m2c15-period-textbook-20261007）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 2 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 3 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 4 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 5 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 6 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 7 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 8 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 9 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 10 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 11 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 12 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 13 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 14 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 15 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 16 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-08T09:29:04 |
| 17 | `.claude/memory/regime_detection_kb.md` | 当てた | 2026-10-08T09:29:04 |
| 18 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-08T09:29:04 |
| 19 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-08T09:29:04 |
| 20 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-08T09:29:04 |
| 21 | `.claude/breaks/b145_vwap_day_no_reset.sh` | 当てた | 2026-10-08T09:29:04 |
| 22 | `.claude/breaks/b146_pivot_week_as_day.sh` | 当てた | 2026-10-08T09:29:04 |
| 23 | `.claude/breaks/b147_vp_today_from_start.sh` | 当てた | 2026-10-08T09:29:04 |
| 24 | `.claude/breaks/b148_bb_range_not_widened.sh` | 当てた | 2026-10-08T09:29:04 |

### 必読に要るファイル（道具が設計書と実装から拾った）

| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15・M2-F-10f・M2-D-8・M2-F-10b） | 入れる |
| `SDK/.claude/memory/regime_detection_kb.md` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b145_vwap_day_no_reset.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b146_pivot_week_as_day.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b147_vp_today_from_start.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b148_bb_range_not_widened.sh` | 直す相手（TARGET） | 入れる |

---

## 監査スコープ

### 監査対象 (本監査内)

- Q1：実装の指示を当てた結果が、実装の後と1文字も同じか
- Q2：実装の指示のどれにも当たらない行（設計書に無い変更）が無いか
- Q3：当てた記録が、実装の指示の全部と1件ずつ合うか
- Q4：承認した版の設計書どうしで、実装の指示が同じか
- Q5：実装の指示が、やることの表の要件を全部 満たすか
- Q6：完成の条件が、実装の後に本当に成り立つか
- Q8：足した11種の計算は、教科書の作りと、3-2 で決めた区切りのとおりか
- Q9：前から在る列の値は、1本も変わっていないか。増えたのは11種だけか
- Q10：範囲の直しと11種の資料の行は、まこさんの決定から漏れなく・余計なく写っているか
- Q11：壊すプログラム4本は、直しを外したときだけ落ちるか

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- 監査 CP60 の修正41 の説明の直し（修正41 の状態は「未決」で、監査の修正を当てる道具は未決の件を当てない（apply_audit_fix.py:37・883）。まこさんが状態を決めた後に、その道具で当てる）
- 足した版と今の版を比べること（比べるのは M2-F-10f。この工事は材料を足すだけ）
- 法則の帯で教科書の pivot・VAH/VAL を使うこと（4つの工事の最後（B-1＋S-1））
- 成績表（material_ranking.json）の作り直し（M2-D-8。増える11列は、作り直すまで段の候補の順位に出ない）
- 出来高プロファイルの区画24・70% を探す範囲にすること（今の POC・VAH・VAL と同じく、名前に出さない引数のまま（値を埋めない種類の並びに載る）。値を渡すのは工事2（M2-F-10b））
- ta のクラスの対応（TA_CLASS_MAP）を変えること（「使う」の印の源1 を変えると、ほかの種類の印も作り直しになる。11種の「使う」は参照表の mako の欄で付ける）
- K-3b・K-3c の種類（次の工事）
- 監査に出す前のチェックの自己テストの P7-1 の落ち（この工事の前から在る。next_step §6 に積んである）

---

## 監査観点 (一般・auditor_template ①〜⑦)

該当なし（この監査は、実装が設計書のとおりかと、まこさんの要望を満たしているかだけを問う。①〜⑦の観点は、この争点に関係しない。結果の所見の「一般の観点」にも「該当なし」と書く）

---

## 監査観点 (本監査固有・Q1-QN)

★問いごとに優先度を付ける＝A（結論を変える）／B（実装の前に直す）／C（完成の測り方以外の書き漏れ）／D（結論に効かせない）。結果の所見は、この問いの番号をそのまま見出しにし、優先度の順に書く。時間が足りずに省いた問いは、結果にその番号を書く。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**優先度の理由**＝違えば、実装は設計書のとおりに作られていない

実装の前（commit 2f75845（依頼書を作った時点の HEAD。承認の控えをまだ commit していないので、実装の前はこの commit の版。`git show 2f75845:<パス>` で出せる。★この後に commit しても、この番号で出せる））の対象のファイル（`.claude/breaks/b145_vwap_day_no_reset.sh`・`.claude/breaks/b146_pivot_week_as_day.sh`・`.claude/breaks/b147_vp_today_from_start.sh`・`.claude/breaks/b148_bb_range_not_widened.sh`・`.claude/memory/regime_detection_kb.md`・`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_diag.py`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）に、設計書 4-20 の実装の指示（24 件）を番号の順に当てた結果が、実装の後（依頼書を作った時点の作業中の変更（まだ commit していない。`git diff 2f75845 -- <パス>` で見られる。★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、`git diff 2f75845 <その commit> -- <パス>` で見る）。★同じファイルに、この工事より後に当てた別の工事の直しも入っている＝m2c15-period-settings-20261008（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-period-settings-20261008.md` の 4-20・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）。実装の後は、実装の前にこの工事の実装の指示を当てた版。作業中の変更と比べるときは、後の工事の実装の指示を同じ順に当ててから比べる（後の工事の行は、その工事の依頼書で照らす））と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**優先度の理由**＝在れば、設計書に無い変更が実装に混ざっている

実装の前（commit 2f75845（依頼書を作った時点の HEAD。承認の控えをまだ commit していないので、実装の前はこの commit の版。`git show 2f75845:<パス>` で出せる。★この後に commit しても、この番号で出せる））と実装の後（依頼書を作った時点の作業中の変更（まだ commit していない。`git diff 2f75845 -- <パス>` で見られる。★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、`git diff 2f75845 <その commit> -- <パス>` で見る）。★同じファイルに、この工事より後に当てた別の工事の直しも入っている＝m2c15-period-settings-20261008（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-period-settings-20261008.md` の 4-20・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）。実装の後は、実装の前にこの工事の実装の指示を当てた版。作業中の変更と比べるときは、後の工事の実装の指示を同じ順に当ててから比べる（後の工事の行は、その工事の依頼書で照らす））の差分（`.claude/breaks/b145_vwap_day_no_reset.sh`・`.claude/breaks/b146_pivot_week_as_day.sh`・`.claude/breaks/b147_vp_today_from_start.sh`・`.claude/breaks/b148_bb_range_not_widened.sh`・`.claude/memory/regime_detection_kb.md`・`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_diag.py`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**優先度の理由**＝合わなければ、どの件を道具が当てたかを後から確かめられない

当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2c15-period-textbook-20261007`）が、実装の指示の 24 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**優先度の理由**＝当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない

承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-period-textbook-20261007.md`）と、監査の相手の設計書（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-period-textbook-20261007.md`。★`.claude/state/acceptance.md` は、この工事の後に別の工事の設計書で上書きされたので比べない）の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**優先度の理由**＝要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない

実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-period-textbook-20261007/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**優先度の理由**＝成り立たなければ、承認のときの「済」が根拠にならない

設計書の完成の条件（4 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 scripts/priority_rebuild/observe_diag.py --selftest`・`python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources`

### Q8 — 足した11種の計算は、教科書の作りと、3-2 で決めた区切りのとおりか（優先度 A）

**優先度の理由**＝作りが教科書と違えば、教科書の版と今の版を比べる M2-F-10f の比べ方そのものが意味を失う。今の足より先の値が混ざれば、ハード制約 H2（未来参照なし）に反する

当日VWAP は UTC 0時から今の足までを積み上げる典型価格です（3-2 の3・pandas-ta の vwap と値で照らした）。前日と当日の POC・VAH・VAL は、前の UTC の日で固定する版と、その日の0時から1本前の足までで育つ版です（3-2 の2＝今の足を入れない）。前週pivot は月曜0時 UTC に始まる前の週の高値・安値・終値で作ります（3-2 の1）。★CC の自己申告＝週の始まりは、出どころの逐語がありません。資料の逐語（StockCharts・TradingView）は「前の週」とだけ書いています。既知答えは手で計算できる合成の足で作りました。計算の作り・区切り・今の足の扱いが、資料の逐語と 3-2 のとおりか、そして今の足より先の値を使っていないかを見てください。

### Q9 — 前から在る列の値は、1本も変わっていないか。増えたのは11種だけか（優先度 A）

**優先度の理由**＝前から在る列の値が変われば、成績表・型の表・ほかの工事の結果が黙って変わる

今の出来高プロファイル（_vp_levels）の中の計算を _vp_one に切り出しました。_pivot_prev_period には、前の週を選べる引数を足しました（渡さなければ今までと同じ）。写しで測ったとき、前から在る列の値の違いは0本で、材料は 477 列 → 488 列でした。型の表の部品は 477 → 488 になり、まこさんに型の表と出口の型の表を再承認していただきました（G2・H2 は通った）。切り出しと引数の足し方で、前の値が変わる道が残っていないかを見てください。

### Q10 — 範囲の直しと11種の資料の行は、まこさんの決定から漏れなく・余計なく写っているか（優先度 A）

**優先度の理由**＝写し誤ると、engine_tuner が教科書の値まで探せないか、資料に無い値を探す

範囲は、まこさんが OK した直し（k7_range_fix.json）を資料に写し、道具（r3_draft_build.py の写し方）が設定ファイルに写しました。CC は値を書いていません。11種の資料の行は、alias_map.json の対応で、同じ指標の今の行の調べた結果から道具が作りました（まこさん「B」）。照らしの道具（check_indicator_sources.py）の①②は食い違い0件です。写す道のどこかで、まこさんの決定と違う値が入っていないかを見てください。

### Q11 — 壊すプログラム4本は、直しを外したときだけ落ちるか（優先度 B）

**優先度の理由**＝落ちない壊し方が在ると、直しが黙って戻っても誰も気づかない

b145〜b148 を写しの作業場で走らせ、宣言した文で落ちるか、壊す対象がちょうど1か所かを見てください。★CC の自己申告＝承認が2回 止まりました。原因は、承認の前の検査（ターンの終わり・上限600秒）が約17分かかる仮当て（A12）を走らせて打ち切られ、本物に仮当ての中身と壊すプログラム4本が残ったことです。2回とも控えから戻してから承認していただきました。同じ日に、ターンの終わりの検査は A12 を走らせず、--try で A12 まで通した記録（.claude/state/a12_try_ok.json）を見る形に直しました（require_design_check_before_approval.py・インフラの直しで、この工事の設計書には入っていません）。戻した後の実物に、仮当ての残りが無いかも見てください。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

件数: 0 件 (結果の外部検索の節にも「該当なし」と書く)

該当なし（この監査は、実装が設計書のとおりかを実物で照らす。外部の知見は答えに要らない。設計の理由を調べる外部検索は、設計書の監査で行う）

---

## 依頼を出した CC の自己申告

1. **測っていない見積もり**＝2つ目の工事（時間は測っていない。流れは158回目の同じ形の工事（資料に足した4種を設定に写す・r5_draft_build.py）と同じ（案 → OK → 設計書 → 承認 → 当てる）・worklog 20261007 §11〜§13）
2. **この工事の外の作業中の変更**＝`.claude/hooks/hook_health_check.sh`・`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_design_check_before_approval.py`・`.claude/hooks/require_request_understood.sh`・`.claude/hooks/trial_design.py`・`.claude/tools/gen_hook_cheatsheet.py`・`.claude/tools/try_hooks.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）

(結果は、この番号ごとに1件ずつ答える)

---

## 結果ファイルフォーマット (auditor 用)

`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-08_m2c15_period_textbook_20261007_impl_cp67_audit_report.md` に、次の 11 節をこの順で出力する。★節の名前と並びは変えない。どの種類の監査でも同じ。

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
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-08_m2c15_period_textbook_20261007_impl_cp67_audit_request.md
```

または

```
本依頼書を読んで監査して
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-08_m2c15_period_textbook_20261007_impl_cp67_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp67_work/cp67_src.gen.md src_sha256=ce42af15d7922d9ccd6b5b5582bbeed61c3a25d1e444e2f8bc7f17ce62ad60e9 body_sha256=94e7ec64c15d2fd1ed81a6ba3abfcf8f5d01326a0a5e0a6f38be1feff26e8a72 -->

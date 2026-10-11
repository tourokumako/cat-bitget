# 【監査依頼】CP72 — K-3c の2つ目の工事＝1つ目の工事で「使う」に入った15種の設定を、資料から observe_config.json と search_limits.json に写す。M2-C-15（実装の監査）

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 35 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて、結果ファイルを次の順で書く（手で1から書かない）:
   - 結果の骨組みを道具で作業場に作る: `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-11_m2c15_formula_settings_20261011_impl_cp72_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp72_work/cp72_result.md`
   - 骨組みの「<監査が書く>」などの印を全部 埋める（見出しと並びは変えない）
   - 食い違い0件を確かめる: `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-11_m2c15_formula_settings_20261011_impl_cp72_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>`
   - 出す前に見直す: `python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` で見直し表を作り、全部の行（結果の見出しごと）に ①意味が通じるか ②実物と合うか（根拠＝ファイル名:行番号・実際に開いた行）③争点（この依頼書の結論を決める問い）に合うか と判定（OK／直した／該当なし（理由））を書き、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通す（結果を直したら表を作り直す・hook 11 が同じ照らしを掛ける）
   - 埋めた結果の全文を、結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-11_m2c15_formula_settings_20261011_impl_cp72_audit_report.md` に Write で1回だけ書く（hook 11 が同じ照らしを掛ける。書いた後は書き替えられない）
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / CONDITIONAL-GO / NO-GO)
   - 重さごとの件数 (Critical / Major / Minor / Process)

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)
- 本物のファイルを書き替えること (写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp72_work/` に作る。最後に `git status --short` で書き替えていないことを示す)

### この監査の作業場

**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp72_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました。**判断が要る4つ（この工事は何のためか・必読・工事ごとの問い・要望のまとめ）は、CC が工事のフォルダの 監査依頼の手書き（実装の監査）.md に書き、まこさんが OK した文を写しました。ほかは道具が実物から作りました。問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・まこさんの要望が在る工事だけ）と、この工事で確かめてほしいことを問う工事ごとの問い（Q8〜Q11）です。

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-11
- 依頼者: CC（起案者）
- 監査区分: 実装の監査
- 監査対象タスク: M2-C-15・M2-F-10b・M2-F-10f・M2-E-8・M2-D-8／設計書 m2c15-formula-settings-20261011
- 監査の相手と版: `.claude/state/acceptance.md` ／ ハッシュ値 eef16bee8034539f09853f045295c0e7af43b05e8e5a5eeacd1e0ebea069329c
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-11_m2c15_formula_settings_20261011_impl_cp72_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-11_m2c15_formula_settings_20261011_impl_cp72_audit_request.md`

---

## この監査で答えてほしいこと

### 結論を決める問い

- **問い1**＝設計書の実装の指示（12 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。あわせて、この工事で確かめてほしいこと（Q8〜Q11 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けている・工事ごとの問いで設計書と違う所が見つかれば NO。

(結論を決めるのは、この問いだけ。結果の「7. 総合判定」で、問いごとに YES / NO と根拠を書く)

### 結論の決め方

- **GO**＝問い1 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の番号と実物の行で示してください。

### この監査の前提

1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-formula-settings-20261011/やることの表.md`）に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。
5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。

---

## 監査依頼の経緯

1. **この工事は何のためか**＝1つ目の工事（m2c15-formula-textbook-20261011）で「使う」に入った15種の設定（指標ごとの一覧・名前に出ない軸の最初の値・値を埋めない種類の並び・探す範囲）を、資料から設定ファイル2本（observe_config.json・search_limits.json）に写す。engine_tuner が読むのは設定ファイルなので、写さないと、15種は代表の値の列を持たず（ほかの指標の期間の一覧を借りて作った列のまま）、探す範囲もカタログの数字の最小〜最大のままになる。写した後は、照らしのプログラムの②（設定ファイルが、いまの資料から写したものと同じか）が食い違い0件になる
   StochRSI素%K と close vs SSF平均% は、元の種類（StochRSI%K・close vs SSF%）と同じ扱いで写し、代表の値と探す範囲を持たせる。探し方の要件（最初の段階は代表の固定値で探し、最後の段階で指標ごとに1つの範囲から探す）に合わせるため
2. **この工事は何か**＝K-3c の1つ目の工事（m2c15-formula-textbook-20261011）で、計算式が教科書と違う種類に教科書の版を足し、G-1 で「使う」の表と資料の表3つを作り直しました。資料が変わったので、照らしのプログラムの②が、設定ファイル2本（observe_config.json・search_limits.json）と資料の食い違いを出しています。これは1つ目の工事の設計書に書いた見込みどおりで、まこさんが OK した分け方（コードの工事と、G-1 の後に設定を写す工事）の後半が、この工事です。StochRSI素%K と close vs SSF平均% は、まこさんの決定「Bで進めてよい」のとおり、元の種類と同じ扱いで写します。そのために、写し方のプログラムの対応表が、対応表の元の種類の軸の対応を引く形に、案の前に直しました。指標ごとの一覧に行が入った種類は、ほかの指標の期間を借りて作っていた列が消え、資料の最初の値（最初の段階で使う代表の値）の列になります。だから、この工事では材料の列が変わります。探す範囲には、最後の段階で探す、指標ごとに1つの範囲が入ります。設定の行が変わると、前からの壊すプログラム b142・b149・b158 が探す行も変わるので、3本を同じ形に直します。コードは1行も変えません。この工事の後、1つ目の工事とこの工事を、工事ごとに1通ずつ実装の監査に出します。（やることの番号 M2-C-15・M2-F-10b・M2-F-10f・M2-E-8・M2-D-8）
   **この工事の位置**＝全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝材料を直す（監査 CP60 の修正・パラメータ・法則どおりの帯の部品・S1 の部品・役割・閾値） → M2-F｜段ごとに測って並べ、上位を次の段へ渡す（段1〜段4）＝1本ずつの成績と順位を出す → M2-F-10b｜測る道具を直す（工事2）＝①正解ラベル2本との一致率で並べる ②手で組んだ土台を置いて、その上に候補を足して測る口 ③確認の窓でも測る口 ④段4 を役割ごとに動かす ⑤6項目のチェックを通す → M2-F-10f｜教科書の版と今の版で値が違う指標を、一致率で比べ、レジーム判定に使う版を決める（上位足の1本の遅れも、直す前と後で比べる） → M2-E｜相場の法則から組ませる ＋ 読み込ませる法則の審査を相場の法則で動かす → M2-E-8｜探す側を、段階的に候補を絞る探し方に直す（工事2）＝最初の段階はパラメータも閾値も戦略ごとの代表的な固定値で組み、最後の段階でパラメータと閾値を範囲から探す → M2-D｜場面を分ける材料の順位を engine_tuner に渡す → M2-D-8｜直した材料で、成績表（material_ranking.json）を作り直す → この工事

---

## 着手前必読 (省略禁止・auditor 用・35 件)

**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `.claude/state/acceptance.md` — 監査の相手（設計書・プログラムが作った）
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-formula-settings-20261011.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
3. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:m2c15-formula-settings-20261011 の行）
4. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-formula-settings-20261011/やることの表.md` — 設計書の元（やることの表）＝修正の指示を書く先
5. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — 目標（全月 net ≥ $1,900）と全体戦略、ハード制約（§4.6）
6. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-232） — engine_tuner の目的、探し方の要件（最初の段階は代表の固定値・最後の段階で指標ごとに1つの範囲・指標の名前に値を固定で入れて数を増やさない）、作ってはいけないもの（探す値を CC が決まった数字の一覧で限定するもの）
7. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:124-146） — M2 が M1〜M6 のどこに当たり、何ができたら終わりか
8. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:81-109・:1173-1187） — M2 で作っている物と、この工事（M2-C-15＝材料を直す）の中身
9. `SDK/.claude/ratchet/acceptance_archive/m2c15-formula-settings-20261011.md`（全文） — 承認済みの設計書の控え（実装の指示12件・完成の条件8行・4-0 に列の違いの名前）
10. `SDK/.claude/ratchet/acceptance_archive/m2c15-formula-textbook-20261011.md`（:204-212・:255-282） — 1つ目の工事の 3-2 の4番（監査は工事ごとに1通）と、4-0 の⑦（この工事で写す設定の見込み。StochRSI素%K と close vs SSF平均% の扱いは、この見込みから変わった＝Q8）
11. `SDK/scripts/priority_rebuild/observe_config.json`（:167-305） — 写した3つの欄（指標ごとの一覧 material_params・名前に出ない軸の最初の値 material_first_hidden・値を埋めない種類の並び _material_params_pending）（Q8）
12. `SDK/scripts/priority_rebuild/recipes/search_limits.json`（:44-163） — 写した探す範囲 material_param_ranges（足した8行と、S-Rタッチ確定1時間ATR の行の末尾の「,」）（Q8）
13. `SDK/scripts/priority_rebuild/observe_diag.py`（:1602-1630・:4287-4292・:4364-4381） — 材料のカタログを作る build_catalog が、指標ごとの一覧に在る種類を、その一覧の組だけで作る所（材料の列が変わる理由）（Q9）。自己テストが、カタログの全部の列を参照表と照らし、「不一致」の文の頭に列の名前を付ける所（Q11）
14. `SDK/scripts/priority_rebuild/engine_tuner_gen.py`（:231-305） — 探す範囲を読む material_ranges（設定に範囲が無い種類は、カタログの数字の最小〜最大を使う）（Q8）
15. `.claude/state/indicator_params_by_strategy.md`（:180-194） — 写す元の資料の15種の行（Q8）
16. `.claude/state/indicator_review/research/alias_map_k3c.json` — 15種の対応表（元の種類・パラメータを写さないと決めた種類）（Q8）
17. `.claude/state/indicator_review/r3_draft_build.py`（:56-95・:162-260・:409-484） — 資料から設定ファイルの中身を作る写し方（名前の軸と資料の軸の対応表 AXIS_MAP・対応表の元の種類の対応を引く所・compute・cfg_block・lim_ranges）。照らしの②がこれを使う（Q8）
18. `.claude/state/indicator_review/_w2_before_20261011/r3_draft_build.py`（:56-90） — 写し方のプログラムの、直す前の版の対応表（直しの前後を比べる相手）（Q8）
19. `.claude/state/indicator_review/apply_param_rule.py`（:28-36・:275-295） — 資料を作るプログラムが、同じ対応表 AXIS_MAP を読む所（対応表を直すと資料の範囲も変わる理由）（Q8）
20. `.claude/state/indicator_review/k3cs_draft_build.py`（全文） — 指示を写しに当てて確かめたプログラム（自己テストの一覧と許しを、承認の前の検査 A12 の本体から読む）（Q8・Q9・Q10）
21. `.claude/tools/check_indicator_sources.py`（全文） — 照らしのプログラム（①「使う」の指標が資料の表3つに全部 在るか・②設定ファイルが、いまの資料から写したものと同じか）（Q8・Q10）
22. `.claude/breaks/b142_rci_list_stale.sh` — 前からの壊すプログラム。探す行と壊した行の末尾に「,」を足した（Q10）
23. `.claude/breaks/b149_pending_not_copied.sh` — 前からの壊すプログラム。探す行を、当てた後の値を埋めない種類の並びの行に置き換えた（Q10）
24. `.claude/breaks/b158_shape_ranges_missing.sh` — 前からの壊すプログラム。探す行と壊した行の末尾に「,」を足した（Q10）
25. `.claude/breaks/b167_formula_params_missing.sh` — 新しい壊すプログラム。指標ごとの一覧から足した行を外すと、照らしの②が止まるか（Q10）
26. `.claude/breaks/b168_formula_hidden_missing.sh` — 新しい壊すプログラム。名前に出ない軸の最初の値から足した行を外すと、照らしの②が止まるか（Q10）
27. `.claude/breaks/b169_formula_ranges_missing.sh` — 新しい壊すプログラム。探す範囲から足した行を外すと、照らしの②が止まるか（Q10）
28. `.claude/breaks/b170_alias_axis_list_dropped.sh` — 新しい壊すプログラム。指標ごとの一覧から StochRSI素%K の行を外すと、照らしの②が止まるか（Q10）
29. `.claude/breaks/b171_alias_axis_range_dropped.sh` — 新しい壊すプログラム。探す範囲から close vs SSF平均% の行を外すと、照らしの②が止まるか（Q10）
30. `.claude/breaks/b162_stochrsi_raw_smoothed.sh` — 1つ目の工事の壊すプログラム。決めた文（EXPECT_MSG）が、この工事で消えた列の名前（StochRSI素%K7）のまま（Q11）
31. `.claude/breaks/b163_trix_ema_signal_sma.sh` — 1つ目の工事の壊すプログラム。決めた文が、この工事で消えた列の名前（TRIX_EMAシグナル(7,9)）のまま（Q11）
32. `.claude/breaks/b165_ssf_avg_single_input.sh` — 1つ目の工事の壊すプログラム。決めた文が、この工事で消えた列の名前（close vs SSF平均%20）のまま（Q11）
33. `SDK/.claude/ratchet/signal_families.md`（全文） — 作り直して再承認された型の表（部品 548 → 534）（Q9）
34. `SDK/.claude/memory/regime_detection_kb.md`（:705・:1290-1295） — 材料の文書を作るプログラムが書き直した囲み2つ（向きを持たない部品の件数・部品の件数）（Q9）
35. `.claude/state/session_worklog_20261011.md`（:181-319） — この工事の経緯（§20〜§30）＝読むもの宣言・対応表の直し・写しの確かめ・案・承認・当てた結果・表の作り直し・G2・H2・1つ目の工事の壊すプログラムの測り直し・監査に出す前のチェック

★直す相手になりうるファイルを必ず入れる (結果の「修正の指示」の「直す前の文字」を、監査が実物から写すため)。プログラムが作る文書 (設計書など) を監査するときは、その元データ (設計書なら、工事のフォルダ `.claude/state/verbatim/<工事名>/` の `やることの表.md`。承認の後は `SDK/.claude/ratchet/acceptance_archive/verbatim/<工事名>/`) も入れる。`acceptance_src.json` は 2026-09-30 から使っていない (ratchet に無い) ので、直す相手に書かない。

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = 設計書 `m2c15-formula-settings-20261011` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `m2c15-formula-settings-20261011` の中身です。

---

## 監査対象の事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_config.json` | 248行（設定・1つ目の工事で「使う」に入った種類の、指標ごとの一覧・名前に出ない軸の最初の値・値を埋めない種類の並びを、資料からプログラムが写し直す（照らしのプログラムの②が見る中身）） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/observe_config.json` | 291行（設定・1つ目の工事で「使う」に入った種類の、指標ごとの一覧・名前に出ない軸の最初の値・値を埋めない種類の並びを、資料からプログラムが写し直す（照らしのプログラムの②が見る中身）） | 直した後の文字 |
| 3 | `SDK/scripts/priority_rebuild/observe_config.json` | 294行（設定・1つ目の工事で「使う」に入った種類の、指標ごとの一覧・名前に出ない軸の最初の値・値を埋めない種類の並びを、資料からプログラムが写し直す（照らしのプログラムの②が見る中身）） | 直した後の文字 |
| 4 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 153行（設定・1つ目の工事で「使う」に入った種類の探す範囲を、資料からプログラムが写し直す（照らしのプログラムの②が見る中身）） | 直した後の文字 |
| 5 | `.claude/breaks/b142_rci_list_stale.sh` | 19〜20行（壊すプログラム・探す行と壊した行の末尾に「,」を付ける＝observe_config.json の当てた後の行に合わせる） | 直した後の文字 |
| 6 | `.claude/breaks/b149_pending_not_copied.sh` | 19〜20行（壊すプログラム・探す行を、当てた後の「値を埋めない種類の並び」の行に置き換える（壊した行は変えない）＝observe_config.json の当てた後の行に合わせる） | 直した後の文字 |
| 7 | `.claude/breaks/b158_shape_ranges_missing.sh` | 19〜20行（壊すプログラム・探す行と壊した行の末尾に「,」を付ける＝search_limits.json の当てた後の行に合わせる） | 直した後の文字 |
| 8 | `.claude/breaks/b167_formula_params_missing.sh` | なし（新しいファイル） | 直した後の文字 |
| 9 | `.claude/breaks/b168_formula_hidden_missing.sh` | なし（新しいファイル） | 直した後の文字 |
| 10 | `.claude/breaks/b169_formula_ranges_missing.sh` | なし（新しいファイル） | 直した後の文字 |
| 11 | `.claude/breaks/b170_alias_axis_list_dropped.sh` | なし（新しいファイル） | 直した後の文字 |
| 12 | `.claude/breaks/b171_alias_axis_range_dropped.sh` | なし（新しいファイル） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:m2c15-formula-settings-20261011）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_config.json` | 当てた | 2026-10-11T10:29:11 |
| 2 | `SDK/scripts/priority_rebuild/observe_config.json` | 当てた | 2026-10-11T10:29:11 |
| 3 | `SDK/scripts/priority_rebuild/observe_config.json` | 当てた | 2026-10-11T10:29:11 |
| 4 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-11T10:29:11 |
| 5 | `.claude/breaks/b142_rci_list_stale.sh` | 当てた | 2026-10-11T10:29:11 |
| 6 | `.claude/breaks/b149_pending_not_copied.sh` | 当てた | 2026-10-11T10:29:11 |
| 7 | `.claude/breaks/b158_shape_ranges_missing.sh` | 当てた | 2026-10-11T10:29:11 |
| 8 | `.claude/breaks/b167_formula_params_missing.sh` | 当てた | 2026-10-11T10:29:11 |
| 9 | `.claude/breaks/b168_formula_hidden_missing.sh` | 当てた | 2026-10-11T10:29:11 |
| 10 | `.claude/breaks/b169_formula_ranges_missing.sh` | 当てた | 2026-10-11T10:29:11 |
| 11 | `.claude/breaks/b170_alias_axis_list_dropped.sh` | 当てた | 2026-10-11T10:29:11 |
| 12 | `.claude/breaks/b171_alias_axis_range_dropped.sh` | 当てた | 2026-10-11T10:29:11 |

### 必読に要るファイル（道具が設計書と実装から拾った）

| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15・M2-F-10b・M2-F-10f・M2-E-8・M2-D-8） | 入れる |
| `SDK/scripts/priority_rebuild/observe_config.json` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b142_rci_list_stale.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b149_pending_not_copied.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b158_shape_ranges_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b167_formula_params_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b168_formula_hidden_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b169_formula_ranges_missing.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b170_alias_axis_list_dropped.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b171_alias_axis_range_dropped.sh` | 直す相手（TARGET） | 入れる |

---

## 監査スコープ

### 監査対象 (本監査内)

- Q1：実装の指示を当てた結果が、実装の後と1文字も同じか
- Q2：実装の指示のどれにも当たらない行（設計書に無い変更）が無いか
- Q3：当てた記録が、実装の指示の全部と1件ずつ合うか
- Q4：承認した版の設計書どうしで、実装の指示が同じか
- Q5：実装の指示が、やることの表の要件を全部 満たすか
- Q6：完成の条件が、実装の後に本当に成り立つか
- Q8：15種の設定は、資料から漏れなく・余計なく写っているか。StochRSI素%K と close vs SSF平均% は、元の種類と同じ扱いで写っているか
- Q9：材料の列の変わり方は、設計書の 4-0 のとおりか。残る列の値は変わっていないか
- Q10：この工事の壊すプログラム8本は、直しを外したときだけ、決めた文で止まるか
- Q11：この工事で列が変わったことで、1つ目の工事の壊すプログラム3本の決めた文が古くなった。実際に出る文を確かめ、直し方を修正の指示に書いてほしい

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- 1つ目の工事で当てたコード・参照表を変えること（もう当てた。この工事は設定の写しだけ）
- 資料の決まりで最初の値も範囲も出ない種類と、名前に軸が無い種類の値を埋めること（この工事の後の T-2・T-3・P-6・P-7・H-1 で扱う。CC は数字を作らない）
- close vs VIDYA_CMO%・THERMO_EMA%・ABER原作位置 に、元の種類のパラメータを写すこと。名前に出さない引数に範囲を渡すこと（対応表の決定「パラメータは写さない」のまま。名前に出さない引数を範囲から渡すのは工事2（M2-F-10b））
- 教科書の版と今の版を比べること（M2-F-10f）
- 探す側の直し（最初の段階に代表の値を渡す・最後の段階でパラメータを動かす）（M2-E-8）
- 成績表（material_ranking.json）の作り直し（M2-D-8。増える列は、作り直すまで成績表に行が無く、段の候補の順位に出ない）
- K-4・B-1＋S-1・R-1・T-1（この工事の後）

---

## 監査観点 (一般・auditor_template ①〜⑦)

該当なし（この監査は、実装が設計書のとおりかと、まこさんの要望を満たしているかだけを問う。①〜⑦の観点は、この争点に関係しない。結果の所見の「一般の観点」にも「該当なし」と書く）

---

## 監査観点 (本監査固有・Q1-QN)

★問いごとに優先度を付ける＝A（結論を変える）／B（実装の前に直す）／C（完成の測り方以外の書き漏れ）／D（結論に効かせない）。結果の所見は、この問いの番号をそのまま見出しにし、優先度の順に書く。時間が足りずに省いた問いは、結果にその番号を書く。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**優先度の理由**＝違えば、実装は設計書のとおりに作られていない

実装の前（commit a0972e3（依頼書を作った時点の HEAD。承認の控えをまだ commit していないので、実装の前はこの commit の版。`git show a0972e3:<パス>` で出せる。★この後に commit しても、この番号で出せる））の対象のファイル（`.claude/breaks/b142_rci_list_stale.sh`・`.claude/breaks/b149_pending_not_copied.sh`・`.claude/breaks/b158_shape_ranges_missing.sh`・`.claude/breaks/b167_formula_params_missing.sh`・`.claude/breaks/b168_formula_hidden_missing.sh`・`.claude/breaks/b169_formula_ranges_missing.sh`・`.claude/breaks/b170_alias_axis_list_dropped.sh`・`.claude/breaks/b171_alias_axis_range_dropped.sh`・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）に、設計書 4-20 の実装の指示（12 件）を番号の順に当てた結果が、実装の後（依頼書を作った時点の作業中の変更（まだ commit していない。`git diff a0972e3 -- <パス>` で見られる。★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、`git diff a0972e3 <その commit> -- <パス>` で見る）。★この工事の中で、設計書の 4-4 の手順（G-1 の表の作り直しほか）の道具が、TARGET のファイルを書き出し直すことがある（例＝gen_materials.py --write が regime_detection_kb.md の件数の囲みを書き出す）。その行は実装の指示ではなく、設計書の 4-4・5 で照らす）と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**優先度の理由**＝在れば、設計書に無い変更が実装に混ざっている

実装の前（commit a0972e3（依頼書を作った時点の HEAD。承認の控えをまだ commit していないので、実装の前はこの commit の版。`git show a0972e3:<パス>` で出せる。★この後に commit しても、この番号で出せる））と実装の後（依頼書を作った時点の作業中の変更（まだ commit していない。`git diff a0972e3 -- <パス>` で見られる。★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、`git diff a0972e3 <その commit> -- <パス>` で見る）。★この工事の中で、設計書の 4-4 の手順（G-1 の表の作り直しほか）の道具が、TARGET のファイルを書き出し直すことがある（例＝gen_materials.py --write が regime_detection_kb.md の件数の囲みを書き出す）。その行は実装の指示ではなく、設計書の 4-4・5 で照らす）の差分（`.claude/breaks/b142_rci_list_stale.sh`・`.claude/breaks/b149_pending_not_copied.sh`・`.claude/breaks/b158_shape_ranges_missing.sh`・`.claude/breaks/b167_formula_params_missing.sh`・`.claude/breaks/b168_formula_hidden_missing.sh`・`.claude/breaks/b169_formula_ranges_missing.sh`・`.claude/breaks/b170_alias_axis_list_dropped.sh`・`.claude/breaks/b171_alias_axis_range_dropped.sh`・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**優先度の理由**＝合わなければ、どの件を道具が当てたかを後から確かめられない

当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2c15-formula-settings-20261011`）が、実装の指示の 12 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**優先度の理由**＝当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない

承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-formula-settings-20261011.md`）と、いまの設計書の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**優先度の理由**＝要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない

実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-formula-settings-20261011/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**優先度の理由**＝成り立たなければ、承認のときの「済」が根拠にならない

設計書の完成の条件（8 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources`

### Q8 — 15種の設定は、資料から漏れなく・余計なく写っているか。StochRSI素%K と close vs SSF平均% は、元の種類と同じ扱いで写っているか（優先度 A）

**優先度の理由**＝写し誤ると、engine_tuner が15種を資料と違う代表の値・範囲で扱う。2種に対応が掛からないと、2種は代表の値も探す範囲も持たず、探し方の要件（最初の段階は代表の固定値・最後の段階で指標ごとに1つの範囲）に合わない

写したのはプログラム（r3_draft_build.py の写し方・k3cs_draft_build.py）で、照らしの②と同じ写し方です。CC は値を書いていません。対応表 alias_map_k3c.json でパラメータを写さないと決めた種類（ABER原作位置・THERMO_EMA%・close vs VIDYA_CMO% の CMO の本数）には、名前に出ない軸の最初の値を写していません。★CC の自己申告（1）＝写し方のプログラム r3_draft_build.py の対応表（AXIS_MAP）は、種類の名前だけで対応を探す作りで、元の行の調べた結果を使う新しい種類（StochRSI素%K・close vs SSF平均%）に対応が掛かっていませんでした。対応表 alias_map_k3c.json の元の種類の対応を引く形に直しました（:86-94）。この直しは、.claude/state の下のプログラムの直しとして案の前に済ませ、資料（indicator_params_by_strategy）を作り直しました（承認の前の検査 A12 は設計書の指示だけを本物に仮に当てるので、写し方のプログラムの直しを指示に入れると資料が作り直されず、照らしの②が狙いまで届かないため）。設計書の実装の指示には入っていません。直す前の版は _w2_before_20261011 に控えました。作り直した資料で変わったのは、2種の範囲（StochRSI素%K は 14〜14 から 7〜21・close vs SSF平均% は 10〜10 から 10〜200）と、「範囲が1点のまま」の種類の数（23 から 21）でした。この直しで、前からの種類の資料の行と設定が変わっていないか、元の種類の対応を引く道が、パラメータを写さないと決めた種類に掛かっていないかを見てください。★CC の自己申告（2）＝1つ目の工事の設計書の 4-0 の⑦は、2種が値を埋めない種類の並びに載る見込みでした。この工事では、2種を元の種類と同じ扱いに変えたので、写した結果はその見込みと違います（observe_config.json は見込みの13行から17行・search_limits.json は8行から10行）。写した後の照らしの①②は食い違い0件です。

### Q9 — 材料の列の変わり方は、設計書の 4-0 のとおりか。残る列の値は変わっていないか（優先度 A）

**優先度の理由**＝指標ごとの一覧に行が入った種類は、観察のプログラムがその一覧の組だけで列を作る。設計書に無い列が消えたり、残る列の値が変わったりすると、型の表・成績表・ほかの工事の結果が黙って変わる

材料は 548 列から 534 列になりました（消えた18列・増えた4列。名前は設計書の 4-0 の④）。型の表の部品も同じ名前で変わり、まこさんに型の表と出口の型の表を再承認していただきました（G2・H2 は通りました）。写しで測ったとき、当てた後も残る列の値の違いは0本でした。消えた列と増えた列が設計書の名前と同じか、残る列の値が変わる道が残っていないかを見てください。★CC の自己申告（1）＝知識の文書 regime_detection_kb.md で、材料の文書を作るプログラム（gen_materials.py --write）が書き直した囲みは2つでした（部品の件数 548件 → 534件・向きを持たない部品の件数 163件 → 160件）。設計書の 4-2 と 4-13 に書いたのは、部品の件数の囲みだけでした。★CC の自己申告（2）＝成績表（material_ranking.json）は作り直していません。増えた4列は、作り直す（M2-D-8）まで段の候補の順位に出ません。

### Q10 — この工事の壊すプログラム8本は、直しを外したときだけ、決めた文で止まるか（優先度 B）

**優先度の理由**＝止まらない壊し方が在ると、写し直しが黙って戻っても誰も気づかない

新しい5本（b167〜b171）と、探す行を当てた後の設定の行に合わせた前からの3本（b142・b149・b158）を写しの作業場で走らせ、決めた文で止まるか、壊す対象がちょうど1か所かを見てください。当てた後の実物で測ったとき、8本とも期待どおりでした（終了コード 1）。前からの3本は、壊し方と決めた文を変えていません。★CC の自己申告＝承認の前（当てる前）に測った b142・b149・b158 の結果は、弱い証拠です。当てる前は、壊さなくても照らしの②が食い違いを出す状態だったためです。

### Q11 — この工事で列が変わったことで、1つ目の工事の壊すプログラム3本の決めた文が古くなった。実際に出る文を確かめ、直し方を修正の指示に書いてほしい（優先度 A）

**優先度の理由**＝決めた文が実物と合わない壊すプログラムは、走らせるたびに「期待と違う」と出る。本当に守りが外れたときと見分けが付かなくなる

★CC の自己申告＝当てた後の実物で、1つ目の工事の壊すプログラム7本（b160〜b166）を測り直しました。4本（b160・b161・b164・b166）は期待どおりでした。3本（b162・b163・b165）は「期待と違う」でした。3本とも終了コードは 1（期待 1）で、壊すと観察のプログラムの自己テストは今も止まります。合わなかったのは、出力に決めた文（EXPECT_MSG）の文字が在るかの照らしです。3本の決めた文は、列の名前（StochRSI素%K7・TRIX_EMAシグナル(7,9)・close vs SSF平均%20）を頭に持ちます。自己テストの「教科書の独立実装と不一致」の文は、カタログの列の名前を頭に付けて出ます（observe_diag.py の :4380）。この工事で、その3つの列は消えました（残る列は StochRSI素%K14・TRIX_EMAシグナル(15,9)・close vs SSF平均%10）。CC が確かめていない所＝壊したときに実際に出る文そのものです（承認ゲートが、壊すプログラムを1本ずつ走らせる Bash を止めます。走らせるプログラム run_breaks.py は出力を画面に出しません）。だから「残る列の名前で同じ文が出ている」は、コードと列の名前から読んだ見立てです。3本は、この工事の設計書の TARGET に無いので、直していません。原因は、設計のときに、決めた文に列の名前を持つ壊すプログラムを探さなかったことです（直すファイルの名前を本文に持つ壊すプログラムだけを探しました）。写しの作業場で3本を走らせて実際に出る文を確かめ、決めた文の直し方を、修正の指示に書いてください。あわせて、決めた文に列の名前を持つ壊すプログラムが、ほかにも古くなっていないかを見てください。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

件数: 0 件 (結果の外部検索の節にも「該当なし」と書く)

該当なし（この監査は、実装が設計書のとおりかを実物で照らす。外部の知見は答えに要らない。設計の理由を調べる外部検索は、設計書の監査で行う）

---

## 依頼を出した CC の自己申告

1. **この工事の外の作業中の変更**＝`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_request_understood.sh`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）

(結果は、この番号ごとに1件ずつ答える)

---

## 結果ファイルフォーマット (auditor 用)

`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-11_m2c15_formula_settings_20261011_impl_cp72_audit_report.md` に、次の 11 節をこの順で出力する。★節の名前と並びは変えない。どの種類の監査でも同じ。

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
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-11_m2c15_formula_settings_20261011_impl_cp72_audit_request.md
```

または

```
本依頼書を読んで監査して
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-11_m2c15_formula_settings_20261011_impl_cp72_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp72_work/cp72_src.gen.md src_sha256=a2a5068177d19fb0efdf0e18aa187bd7e6dfdc2ee4d4d4194651695253342594 body_sha256=6b56921acc73f7a507834c4d741ba34a7b41a48f1890dce314d8f0cd96790f6b -->

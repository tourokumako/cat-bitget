# 【監査依頼】CP73 — K-3c 計算式の違い＝計算式が教科書と違う15種に、教科書の版を今の版を残して足す。M2-C-15（実装の監査）

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 22 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて、結果ファイルを次の順で書く（手で1から書かない）:
   - 結果の骨組みを道具で作業場に作る: `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-11_m2c15_formula_textbook_20261011_impl_cp73_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp73_work/cp73_result.md`
   - 骨組みの「<監査が書く>」などの印を全部 埋める（見出しと並びは変えない）
   - 食い違い0件を確かめる: `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-11_m2c15_formula_textbook_20261011_impl_cp73_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>`
   - 出す前に見直す: `python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` で見直し表を作り、全部の行（結果の見出しごと）に ①意味が通じるか ②実物と合うか（根拠＝ファイル名:行番号・実際に開いた行）③争点（この依頼書の結論を決める問い）に合うか と判定（OK／直した／該当なし（理由））を書き、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通す（結果を直したら表を作り直す・hook 11 が同じ照らしを掛ける）
   - 埋めた結果の全文を、結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-11_m2c15_formula_textbook_20261011_impl_cp73_audit_report.md` に Write で1回だけ書く（hook 11 が同じ照らしを掛ける。書いた後は書き替えられない）
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / CONDITIONAL-GO / NO-GO)
   - 重さごとの件数 (Critical / Major / Minor / Process)

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)
- 本物のファイルを書き替えること (写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp73_work/` に作る。最後に `git status --short` で書き替えていないことを示す)

### この監査の作業場

**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp73_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました。**判断が要る4つ（この工事は何のためか・必読・工事ごとの問い・要望のまとめ）は、CC が工事のフォルダの 監査依頼の手書き（実装の監査）.md に書き、まこさんが OK した文を写しました。ほかは道具が実物から作りました。問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・まこさんの要望が在る工事だけ）と、この工事で確かめてほしいことを問う工事ごとの問い（Q8〜Q11）です。

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-11
- 依頼者: CC（起案者）
- 監査区分: 実装の監査
- 監査対象タスク: M2-C-15・M2-F-10f・M2-F-10b・M2-D-8／設計書 m2c15-formula-textbook-20261011
- 監査の相手と版: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-formula-textbook-20261011.md` ／ ハッシュ値 c09bda62bd0c0f9d8e7e5ec4518a63737f5fe9b255e1e5b6e477e7f10d72c90a
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-11_m2c15_formula_textbook_20261011_impl_cp73_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-11_m2c15_formula_textbook_20261011_impl_cp73_audit_request.md`

---

## この監査で答えてほしいこと

### 結論を決める問い

- **問い1**＝設計書の実装の指示（33 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。あわせて、この工事で確かめてほしいこと（Q8〜Q11 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けている・工事ごとの問いで設計書と違う所が見つかれば NO。

(結論を決めるのは、この問いだけ。結果の「7. 総合判定」で、問いごとに YES / NO と根拠を書く)

### 結論の決め方

- **GO**＝問い1 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の番号と実物の行で示してください。

### この監査の前提

1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-formula-textbook-20261011/やることの表.md`）に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。
5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。

---

## 監査依頼の経緯

1. **この工事は何のためか**＝監査 CP60 が「計算式が教科書と違う」と指摘した材料15種（DPO・Aberration・THERMO・SQZ_ON・StochRSI・TRIX のシグナルとヒスト・realized_vol・SSF・TRIMA・VIDYA・HT_TRENDLINE・MAMA・FAMA と、THERMO を EMA でならした版）に、教科書の版を、今の版を残したまま別の材料として足す。engine_tuner が教科書の版と今の版の両方を材料として扱えるようにし、どちらが良いかを後の段（M2-F-10f）で、レジーム判定は正解ラベルとの一致率、Entry/Exit は net で比べられるようにする
   新しいパラメータ（THERMO の EMA の本数・VIDYA の CMO の本数・Aberration 原作の本数と倍率・Carter の4つの数）は名前に出さない引数にし、指標の名前に値を入れて数を増やさない。PMAX 原作は、原典のコードの全文が資料に無いので入れない
2. **この工事は何か**＝監査 CP60 は、今の材料のうち15種の計算式が教科書と違うと指摘しました。DPO は、教科書を時点 t で作れる形に書くと「k本前の終値 − いまの n本平均」ですが、今の材料は「いまの終値 − k本前の n本平均」です。THERMO は、教科書（Elder）では前の足から外へはみ出した幅だけで内はらみ足は 0 ですが、今の材料は絶対値を取ります。SQZ_ON は、Carter の作りではケルトナーの中心を代表値段の SMA・幅を ATR にしますが、今の材料は終値の SMA と真の値幅の SMA です。StochRSI は原式ではならしませんが、今の材料は SMA3 でならします。TRIX のシグナルは教科書では EMA ですが、今の材料は単純移動平均です。realized_vol は教科書の実現ボラは平均を引きませんが、今の材料は引きます。SSF は Ehlers の式では入力を2本の平均にしますが、今の材料はしません。TRIMA は TA-Lib では偶数の本数で窓が違い、VIDYA は CMO の本数を別に持ちます。HT_TRENDLINE・MAMA・FAMA は Ehlers の入力が (高値＋安値)/2 ですが、今の材料は終値です。Aberration は原作が80本・標準偏差2倍のボリンジャーバンドですが、今の材料はライブラリ独自の作りです。まこさんは、今の版を残し、教科書の版を別の材料として足して、後で比べる形を決めました（K-3 の「A」）。K-7 の決定で、THERMO% に EMA でならした版も足します。作りの5点（新しいパラメータは名前に出さない引数・EMA の本数の最初の値は既定の値・式は監査の本文と原典の逐語から・Aberration 原作は別の材料・対応表と既知答えは K-3b と同じ形）にも「進めて良い」をいただきました。この工事は、その15種を観察の道具と参照表に足します。前から在る列の値は1本も変えません。どちらの版が良いかを比べるのは、この工事ではなく M2-F-10f です。（やることの番号 M2-C-15・M2-F-10f・M2-F-10b・M2-D-8）
   **この工事の位置**＝全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝材料を直す（監査 CP60 の修正・パラメータ・法則どおりの帯の部品・S1 の部品・役割・閾値） → M2-F｜段ごとに測って並べ、上位を次の段へ渡す（段1〜段4）＝1本ずつの成績と順位を出す → M2-F-10f｜教科書の版と今の版で値が違う指標を、一致率で比べ、レジーム判定に使う版を決める（上位足の1本の遅れも、直す前と後で比べる） → M2-F-10b｜測る道具を直す（工事2）＝①正解ラベル2本との一致率で並べる ②手で組んだ土台を置いて、その上に候補を足して測る口 ③確認の窓でも測る口 ④段4 を役割ごとに動かす ⑤6項目のチェックを通す → M2-D｜場面を分ける材料の順位を engine_tuner に渡す → M2-D-8｜直した材料で、成績表（material_ranking.json）を作り直す → この工事

---

## 着手前必読 (省略禁止・auditor 用・22 件)

**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-formula-textbook-20261011.md` — 監査の相手（設計書・プログラムが作った）
2. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:m2c15-formula-textbook-20261011 の行）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-formula-textbook-20261011/やることの表.md` — 設計書の元（やることの表）＝修正の指示を書く先
4. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — 目標（全月 net ≥ $1,900）と全体戦略、ハード制約（§4.6＝H2 未来参照なし・H6 値段の高さで値が変わらない ほか）。足した15種が、今の足より先の値を使っていないかを照らす
5. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-232） — engine_tuner の目的、探し方の要件（指標の名前に値を固定で入れて数を増やさない）、作ってはいけないもの
6. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:124-146） — M2 が M1〜M6 のどこに当たり、何ができたら終わりか
7. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:81-109・:1173-1187） — M2 で作っている物と、この工事（M2-C-15＝材料を直す）の中身
8. `SDK/.claude/ratchet/acceptance_archive/m2c15-formula-textbook-20261011.md`（全文） — 承認済みの設計書の控え（実装の指示33件・完成の条件7行・3-2 で決めた4つ・4-0 に15種の作りと出どころ）
9. `SDK/.claude/audits/2026-10-03_indicator_textbook_check_cp60_audit_report.md`（:1249-1274・:1408-1425・:1441-1580・:1786-1827） — 15種の作りの出どころ＝監査 CP60 の修正37・45・47〜53・58・71 の本文と、監査が引いた原典の逐語（Q8）
10. `SDK/scripts/priority_rebuild/observe_diag.py`（:941-952・:1204-1238・:1272-1296・:1353-1424・:1467-1478・:1533-1564・:1602-1630・:1670-1678・:1806-1826・:1848-1866・:1882-1902・:1947-1961・:7264-7400） — 15種の計算と登録（realized_vol_rv・Carter の作りのスクイーズ・ならさない StochRSI・EMA のシグナルの TRIX・SSF と TRIMA と VIDYA・入力を (高値＋安値)/2 にした3種・教科書の DPO・Aberration 原作と THERMO の2種）、カタログへの足し方、名前に出さない引数の番人と軽い口（Q8・Q9・Q10）
11. `SDK/scripts/priority_rebuild/indicator_reference_diag.py`（:949-951・:1686-1880・:4895-4902・:5119-5127・:5454-5475） — 「使う」の決定の欄・15種の参照表（独立の実装と既知答え）・ta の DPOIndicator の対応・系統・業界のライブラリとの対応（Q8・Q10）
12. `SDK/.claude/memory/regime_detection_kb.md`（:1290-1295） — 指標の種類・材料の一覧・部品の件数の囲み（gen_materials.py が書き出す）（Q10）
13. `.claude/state/indicator_review/research/alias_map_k3c.json` — 15種の資料の行を、同じ指標の今の行から作る対応表（パラメータを写さないと決めた種類を含む）（Q9）
14. `.claude/breaks/b160_dpo_tb_lib_shift.sh` — 壊すプログラム。DPO教科書% を今の版に戻すと、既知答えが止まるか（Q11）
15. `.claude/breaks/b161_thermo_orig_abs.sh` — 壊すプログラム。THERMO原作% を絶対値に戻すと、内はらみ足の既知答えが止まるか（Q11）
16. `.claude/breaks/b162_stochrsi_raw_smoothed.sh` — 壊すプログラム。StochRSI素%K をならす形に戻すと、独立の実装との照らしが止まるか（Q11）
17. `.claude/breaks/b163_trix_ema_signal_sma.sh` — 壊すプログラム。TRIX_EMAシグナル のシグナルを単純移動平均に戻すと、独立の実装との照らしが止まるか（Q11）
18. `.claude/breaks/b164_rvol_rv_mean_subtracted.sh` — 壊すプログラム。realized_vol_rv を平均を引く形に戻すと、既知答えが止まるか（Q11）
19. `.claude/breaks/b165_ssf_avg_single_input.sh` — 壊すプログラム。close vs SSF平均% の入力を1本に戻すと、独立の実装との照らしが止まるか（Q11）
20. `.claude/breaks/b166_sqz_carter_scalar_fixed.sh` — 壊すプログラム。SQZ_ON_Carter の倍率を固定で書くと、名前に出さない引数の番人が止まるか（Q11）
21. `SDK/.claude/ratchet/signal_families.md`（全文） — 作り直して再承認された型の表（この工事の後は部品 548。2つ目の工事の後のいまは 534）（Q10）
22. `.claude/state/session_worklog_20261011.md`（:63-180・:293-306） — この工事の経緯（§6〜§19）＝読むもの宣言・作りの5点・写しの確かめ・見直しで足した b166・承認・当てた結果・表の作り直し・型の表の再承認・G2・H2。2つ目の工事の後の壊すプログラムの測り直し（§29）

★直す相手になりうるファイルを必ず入れる (結果の「修正の指示」の「直す前の文字」を、監査が実物から写すため)。プログラムが作る文書 (設計書など) を監査するときは、その元データ (設計書なら、工事のフォルダ `.claude/state/verbatim/<工事名>/` の `やることの表.md`。承認の後は `SDK/.claude/ratchet/acceptance_archive/verbatim/<工事名>/`) も入れる。`acceptance_src.json` は 2026-09-30 から使っていない (ratchet に無い) ので、直す相手に書かない。

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = 設計書 `m2c15-formula-textbook-20261011` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `m2c15-formula-textbook-20261011` の中身です。

---

## 監査対象の事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_diag.py` | 941〜942行（<モジュール直下>・監査 CP60 の修正50＝平均を引かない実現ボラを、今の版を残して足す） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1201行（<モジュール直下>・監査 CP60 の修正47＝Carter の作りのスクイーズを、今の版を残して足す（4つの数は名前に出さない引数）） | 直した後の文字 |
| 3 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1240〜1243行（<モジュール直下>・監査 CP60 の修正48＝ならさない StochRSI を、今の版を残して足す） | 直した後の文字 |
| 4 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1248〜1249行（<モジュール直下>・監査 CP60 の修正49＝シグナルを EMA にした TRIX のシグナルとヒストを、今の版を残して足す） | 直した後の文字 |
| 5 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1309〜1311行（<モジュール直下>・監査 CP60 の修正51・52＝SSF（入力を2本の平均）・TRIMA（TA-Lib の偶数の形）・VIDYA（CMO の本数を別に持つ）を、今の版を残して足す） | 直した後の文字 |
| 6 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1320〜1321行（<モジュール直下>・監査 CP60 の修正53＝入力を (高値＋安値)/2 にした HT_TRENDLINE を、今の版を残して足す） | 直した後の文字 |
| 7 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1323〜1324行（<モジュール直下>・監査 CP60 の修正53＝入力を (高値＋安値)/2 にした MAMA・FAMA を、今の版を残して足す） | 直した後の文字 |
| 8 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1371〜1372行（<モジュール直下>・監査 CP60 の修正37・45＝教科書の DPO（k本前の終値 − いまの n本平均）を、今の版を残して足す） | 直した後の文字 |
| 9 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1432〜1433行（<モジュール直下>・監査 CP60 の修正45・71＝Fitschen の原作の Aberration の帯の中の位置を、今の版を残して足す（本数と倍率は名前に出さない引数）） | 直した後の文字 |
| 10 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1444〜1445行（<モジュール直下>・監査 CP60 の修正45・58＝Elder の原作の温度計と、K-7 の決定＝EMA でならした版を、今の版を残して足す） | 直した後の文字 |
| 11 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1558〜1559行（build_catalog・realized_vol_rv をカタログに入れる（今の realized_vol と同じ本数の一覧で作る）） | 直した後の文字 |
| 12 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1698〜1699行（build_catalog・StochRSI素%K をカタログに入れる（今の StochRSI と同じ本数の一覧で作る）） | 直した後の文字 |
| 13 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1703行（build_catalog・TRIX_EMAシグナル・TRIX_EMAヒスト をカタログに入れる（今の TRIX と同じ一覧で作る）） | 直した後の文字 |
| 14 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1731行（build_catalog・close vs HT_TRENDLINE_HL% をカタログに入れる） | 直した後の文字 |
| 15 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1740〜1741行（build_catalog・close vs MAMA_HL%・close vs FAMA_HL% をカタログに入れる） | 直した後の文字 |
| 16 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1758〜1762行（build_catalog・close vs SSF平均%・TRIMA_TA%・VIDYA_CMO% をカタログに入れる（今の移動平均と同じ本数の一覧で作る）） | 直した後の文字 |
| 17 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1772〜1773行（build_catalog・DPO教科書% をカタログに入れる（今の DPO% と同じ本数の一覧で作る）） | 直した後の文字 |
| 18 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1694行（build_catalog・SQZ_ON_Carter をカタログに入れる（名前に出る軸は無い）） | 直した後の文字 |
| 19 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1821〜1823行（build_catalog・ABER原作位置 をカタログに入れる（名前に出る軸は無い）） | 直した後の文字 |
| 20 | `SDK/scripts/priority_rebuild/observe_diag.py` | 1828〜1829行（build_catalog・THERMO原作%・THERMO_EMA% をカタログに入れる（名前に出る軸は無い）） | 直した後の文字 |
| 21 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 948行（<モジュール直下>・15種の「使う」の決定（まこさんの逐語のファイル）を、mako の欄から1か所で引けるようにする） | 直した後の文字 |
| 22 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1673〜1681行（<モジュール直下>・監査 CP60 の修正37・45・47〜53 と K-7 の決定＝15種を参照表に登録し、独立の実装と手計算の既知答えを付ける） | 直した後の文字 |
| 23 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4920行（<モジュール直下>・15種の系統（元の種類と同じ）を書く） | 直した後の文字 |
| 24 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 5247〜5248行（<モジュール直下>・15種の業界のライブラリとの対応を書く（観察の道具の検査10 が全部の種類に求める）） | 直した後の文字 |
| 25 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4699行（<モジュール直下>・全体の表 G-1＝ta の DPOIndicator を教科書の版の DPO に対応させる（今の DPO% は比べるために残す）） | 直した後の文字 |
| 26 | `.claude/memory/regime_detection_kb.md` | 1290〜1295行（文書・足す15種で、材料の種類・一覧の行・部品の数が変わる＝KB の件数の囲み（gen_materials.py --write が書き出す所）を、写しで数えた文に置き換える（材料の文書の自己テストの B3・B4 と承認の前の検査 A12 が見る）） | 直した後の文字 |
| 27 | `.claude/breaks/b160_dpo_tb_lib_shift.sh` | なし（新しいファイル） | 直した後の文字 |
| 28 | `.claude/breaks/b161_thermo_orig_abs.sh` | なし（新しいファイル） | 直した後の文字 |
| 29 | `.claude/breaks/b162_stochrsi_raw_smoothed.sh` | なし（新しいファイル） | 直した後の文字 |
| 30 | `.claude/breaks/b163_trix_ema_signal_sma.sh` | なし（新しいファイル） | 直した後の文字 |
| 31 | `.claude/breaks/b164_rvol_rv_mean_subtracted.sh` | なし（新しいファイル） | 直した後の文字 |
| 32 | `.claude/breaks/b165_ssf_avg_single_input.sh` | なし（新しいファイル） | 直した後の文字 |
| 33 | `.claude/breaks/b166_sqz_carter_scalar_fixed.sh` | なし（新しいファイル） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:m2c15-formula-textbook-20261011）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 2 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 3 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 4 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 5 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 6 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 7 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 8 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 9 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 10 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 11 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 12 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 13 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 14 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 15 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 16 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 17 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 18 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 19 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 20 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 21 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 22 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 23 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 24 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 25 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-11T08:19:33 |
| 26 | `.claude/memory/regime_detection_kb.md` | 当てた | 2026-10-11T08:19:33 |
| 27 | `.claude/breaks/b160_dpo_tb_lib_shift.sh` | 当てた | 2026-10-11T08:19:33 |
| 28 | `.claude/breaks/b161_thermo_orig_abs.sh` | 当てた | 2026-10-11T08:19:33 |
| 29 | `.claude/breaks/b162_stochrsi_raw_smoothed.sh` | 当てた | 2026-10-11T08:19:33 |
| 30 | `.claude/breaks/b163_trix_ema_signal_sma.sh` | 当てた | 2026-10-11T08:19:33 |
| 31 | `.claude/breaks/b164_rvol_rv_mean_subtracted.sh` | 当てた | 2026-10-11T08:19:33 |
| 32 | `.claude/breaks/b165_ssf_avg_single_input.sh` | 当てた | 2026-10-11T08:19:33 |
| 33 | `.claude/breaks/b166_sqz_carter_scalar_fixed.sh` | 当てた | 2026-10-11T08:19:33 |

### 必読に要るファイル（道具が設計書と実装から拾った）

| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15・M2-F-10f・M2-F-10b・M2-D-8） | 入れる |
| `SDK/.claude/memory/regime_detection_kb.md` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_diag.py` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b160_dpo_tb_lib_shift.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b161_thermo_orig_abs.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b162_stochrsi_raw_smoothed.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b163_trix_ema_signal_sma.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b164_rvol_rv_mean_subtracted.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b165_ssf_avg_single_input.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b166_sqz_carter_scalar_fixed.sh` | 直す相手（TARGET） | 入れる |

---

## 監査スコープ

### 監査対象 (本監査内)

- Q1：実装の指示を当てた結果が、実装の後と1文字も同じか
- Q2：実装の指示のどれにも当たらない行（設計書に無い変更）が無いか
- Q3：当てた記録が、実装の指示の全部と1件ずつ合うか
- Q4：承認した版の設計書どうしで、実装の指示が同じか
- Q5：実装の指示が、やることの表の要件を全部 満たすか
- Q6：完成の条件が、実装の後に本当に成り立つか
- Q8：足した15種の計算は、監査 CP60 の修正の文と、監査が引いた原典の逐語のとおりか
- Q9：新しいパラメータは名前に出さない引数になっていて、最初の値が資料の既定かライブラリの既定で、計算に届いているか
- Q10：前から在る列の値は、1本も変わっていないか。この工事で増えたのは15種の32列だけか
- Q11：壊すプログラム7本は、直しを外したときだけ、決めた文で止まるか

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- 足した版と今の版を比べること（比べるのは M2-F-10f。この工事は材料を足すだけ）
- PMAX 原作の版（原典のコードの全文が資料に無く、新しく Web を調べない）
- 名前に出さない引数を範囲で探すこと（値を渡すのは工事2（M2-F-10b））
- TSIヒスト・STC の期間の比べ方（修正49 の残り）（K-3c の16種に入っていない）
- BB%b の範囲を 80 まで広げること（範囲は資料の規則で決める。原作の 80本は名前に出さない引数で持つ）
- 成績表（material_ranking.json）の作り直し（M2-D-8。増える列は、作り直すまで段の候補の順位に出ない）
- K-4 から先の工事（この工事の後）
- 監査に出す前のチェックの自己テストの P7-1 の落ち（この工事の前から在る。next_step §6 に積んである）

---

## 監査観点 (一般・auditor_template ①〜⑦)

該当なし（この監査は、実装が設計書のとおりかと、まこさんの要望を満たしているかだけを問う。①〜⑦の観点は、この争点に関係しない。結果の所見の「一般の観点」にも「該当なし」と書く）

---

## 監査観点 (本監査固有・Q1-QN)

★問いごとに優先度を付ける＝A（結論を変える）／B（実装の前に直す）／C（完成の測り方以外の書き漏れ）／D（結論に効かせない）。結果の所見は、この問いの番号をそのまま見出しにし、優先度の順に書く。時間が足りずに省いた問いは、結果にその番号を書く。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**優先度の理由**＝違えば、実装は設計書のとおりに作られていない

実装の前（commit b812bab）の対象のファイル（`.claude/breaks/b160_dpo_tb_lib_shift.sh`・`.claude/breaks/b161_thermo_orig_abs.sh`・`.claude/breaks/b162_stochrsi_raw_smoothed.sh`・`.claude/breaks/b163_trix_ema_signal_sma.sh`・`.claude/breaks/b164_rvol_rv_mean_subtracted.sh`・`.claude/breaks/b165_ssf_avg_single_input.sh`・`.claude/breaks/b166_sqz_carter_scalar_fixed.sh`・`.claude/memory/regime_detection_kb.md`・`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_diag.py`）に、設計書 4-20 の実装の指示（33 件）を番号の順に当てた結果が、実装の後（commit 2b0c31b）と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**優先度の理由**＝在れば、設計書に無い変更が実装に混ざっている

実装の前（commit b812bab）と実装の後（commit 2b0c31b）の差分（`.claude/breaks/b160_dpo_tb_lib_shift.sh`・`.claude/breaks/b161_thermo_orig_abs.sh`・`.claude/breaks/b162_stochrsi_raw_smoothed.sh`・`.claude/breaks/b163_trix_ema_signal_sma.sh`・`.claude/breaks/b164_rvol_rv_mean_subtracted.sh`・`.claude/breaks/b165_ssf_avg_single_input.sh`・`.claude/breaks/b166_sqz_carter_scalar_fixed.sh`・`.claude/memory/regime_detection_kb.md`・`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_diag.py`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**優先度の理由**＝合わなければ、どの件を道具が当てたかを後から確かめられない

当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2c15-formula-textbook-20261011`）が、実装の指示の 33 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**優先度の理由**＝当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない

承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-formula-textbook-20261011.md`）と、監査の相手の設計書（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-formula-textbook-20261011.md`。★`.claude/state/acceptance.md` は、この工事の後に別の工事の設計書で上書きされたので比べない）の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**優先度の理由**＝要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない

実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-formula-textbook-20261011/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**優先度の理由**＝成り立たなければ、承認のときの「済」が根拠にならない

設計書の完成の条件（7 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 scripts/priority_rebuild/observe_diag.py --selftest`・`python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog`

### Q8 — 足した15種の計算は、監査 CP60 の修正の文と、監査が引いた原典の逐語のとおりか（優先度 A）

**優先度の理由**＝作りが教科書と違えば、教科書の版と今の版を比べる M2-F-10f の比べ方そのものが意味を失う。今の足より先の値が混ざれば、ハード制約 H2（未来参照なし）に反する

15種の作りと出どころは、設計書の 4-0 の①の表に在ります。式が逐語で在る種類（realized_vol_rv・THERMO原作%・DPO教科書%）は監査 CP60 の修正の本文の文字から、作りの文だけの種類は監査が引いた原典の逐語から書きました。DPO教科書% は「k本前の終値 − いまの n本平均」で、教科書の式を、未来の足を見ずに時点 t で作れる形に書いたものです。計算の作りが出どころの文のとおりか、今の足より先の値を使っていないか、参照表の独立の実装が観察のプログラムの計算と別の書き方になっているかを見てください。★CC の自己申告（1）＝設計書の 3-2 で、CC の案のまま進めた作りが2つ在ります。SQZ_ON_Carter の ATR は Wilder の作りにしました（監査の文は「幅を ATR」）。THERMO_EMA% は、原作の温度計（THERMO原作%）を EMA でならしました。★CC の自己申告（2）＝HT_TRENDLINE_HL%・MAMA_HL%・FAMA_HL% は、ライブラリの関数に渡す入力を (高値＋安値)/2 に変えただけで、独立の実装は在りません。既知答えは「値段が一定なら 0」だけです（今の版と同じ見方）。

### Q9 — 新しいパラメータは名前に出さない引数になっていて、最初の値が資料の既定かライブラリの既定で、計算に届いているか（優先度 A）

**優先度の理由**＝名前に値を入れると、探し方の要件（指標の名前に値を固定で入れて数を増やさない）に反する。引数が計算に届いていないと、後の工事（M2-F-10b）で値を渡しても列が変わらない

名前に出さない引数は、Carter の4つ（20・2.0・20・1.5）・Aberration 原作の本数と倍率（80・2.0）・VIDYA の CMO の本数（9）・THERMO の EMA の本数（20）です。最初の値は、資料の既定か、資料に最初の値が無いときはライブラリの既定です（THERMO の EMA の本数は、資料の2つの値がどちらも最初の値にならない出どころだったので、ライブラリの既定 20）。観察のプログラムの番人（名前に出さない引数を変えると列が変わるか）で見ています。最初の値が出どころのとおりか、番人が8つの引数を全部 見ているかを見てください。

### Q10 — 前から在る列の値は、1本も変わっていないか。この工事で増えたのは15種の32列だけか（優先度 A）

**優先度の理由**＝前から在る列の値が変われば、成績表・型の表・ほかの工事の結果が黙って変わる

今の版のコードは変えず、教科書の版を別の名前で足しました。写しで測ったとき、前から在る列の値の違いは0本で、材料は 516 列から 548 列になりました（増えた32列の名前は設計書の 4-0 の④）。オン・オフの表は「使う」が 160 種から 175 種になり、型の表と出口の型の表を まこさんに再承認していただきました（G2・H2 は通りました）。今の版に手が入っていないか、増えた列が15種だけかを見てください。★CC の自己申告（1）＝この工事の後、2つ目の工事（m2c15-formula-settings-20261011）で15種の設定を写したので、いまの実物の材料は 534 列です（32列のうち18列が消え、資料の最初の値の4列が増えました。別の依頼書で見ます）。★CC の自己申告（2）＝ta の DPOIndicator の対応を（DPO教科書%・DPO%）の2つにしました。今の DPO% を対応から外すと「使う」から外れるためです（設計書の 3-2 の3番）。

### Q11 — 壊すプログラム7本は、直しを外したときだけ、決めた文で止まるか（優先度 B）

**優先度の理由**＝止まらない壊し方が在ると、教科書の版が今の版に黙って戻っても誰も気づかない

b160〜b166 を写しの作業場で走らせ、決めた文で止まるか、壊す対象がちょうど1か所かを見てください。この工事を当てた直後の実物では、7本とも期待どおりでした（終了コード 1）。★CC の自己申告（1）＝2つ目の工事を当てた後の実物で測り直すと、3本（b162・b163・b165）が「期待と違う」になりました。終了コードは 1 のままで、合わなかったのは決めた文（EXPECT_MSG）です。決めた文が頭に持つ列の名前（StochRSI素%K7・TRIX_EMAシグナル(7,9)・close vs SSF平均%20）が、2つ目の工事で消えた列だったためです。直し方は、2つ目の工事の依頼書の問いで見ていただきます。いまの実物でこの3本を測るときは、この点を踏まえてください。★CC の自己申告（2）＝b166 は、見直しのときに足しました（最初の案には無く、名前に出さない引数が計算に届くことを覆う完成の条件が無かったため）。b166 だけは、全体の自己テストでなく軽い口（--selftest-catalog）で測ります。7本とも全体の自己テストで測ると、承認の前の検査の上限の時間を超えたためです。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

件数: 0 件 (結果の外部検索の節にも「該当なし」と書く)

該当なし（この監査は、実装が設計書のとおりかを実物で照らす。外部の知見は答えに要らない。設計の理由を調べる外部検索は、設計書の監査で行う）

---

## 依頼を出した CC の自己申告

1. **この工事の外の作業中の変更**＝`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_request_understood.sh`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）

(結果は、この番号ごとに1件ずつ答える)

---

## 結果ファイルフォーマット (auditor 用)

`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-11_m2c15_formula_textbook_20261011_impl_cp73_audit_report.md` に、次の 11 節をこの順で出力する。★節の名前と並びは変えない。どの種類の監査でも同じ。

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
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-11_m2c15_formula_textbook_20261011_impl_cp73_audit_request.md
```

または

```
本依頼書を読んで監査して
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-11_m2c15_formula_textbook_20261011_impl_cp73_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp73_work/cp73_src.gen.md src_sha256=562efad4459980db4794e743486c1f458980d5fd910b036e660c041dc2fb1df5 body_sha256=df55559a0634ff668e4b07060bf5b356ecba6f769052bbcbdd8e933e8558de68 -->

# 【監査依頼】CP68 — K-3a の2つ目の工事＝1つ目の工事で「使う」に入った11種の設定を、資料から設定ファイルに写す。M2-C-15（実装の監査）

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 18 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて、結果ファイルを次の順で書く（手で1から書かない）:
   - 結果の骨組みを道具で作業場に作る: `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-08_m2c15_period_settings_20261008_impl_cp68_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp68_work/cp68_result.md`
   - 骨組みの「<監査が書く>」などの印を全部 埋める（見出しと並びは変えない）
   - 食い違い0件を確かめる: `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-08_m2c15_period_settings_20261008_impl_cp68_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>`
   - 出す前に見直す: `python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` で見直し表を作り、全部の行（結果の見出しごと）に ①意味が通じるか ②実物と合うか（根拠＝ファイル名:行番号・実際に開いた行）③争点（この依頼書の結論を決める問い）に合うか と判定（OK／直した／該当なし（理由））を書き、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通す（結果を直したら表を作り直す・hook 11 が同じ照らしを掛ける）
   - 埋めた結果の全文を、結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-08_m2c15_period_settings_20261008_impl_cp68_audit_report.md` に Write で1回だけ書く（hook 11 が同じ照らしを掛ける。書いた後は書き替えられない）
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / CONDITIONAL-GO / NO-GO)
   - 重さごとの件数 (Critical / Major / Minor / Process)

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)
- 本物のファイルを書き替えること (写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp68_work/` に作る。最後に `git status --short` で書き替えていないことを示す)

### この監査の作業場

**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp68_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました。**判断が要る4つ（この工事は何のためか・必読・工事ごとの問い・要望のまとめ）は、CC が工事のフォルダの 監査依頼の手書き（実装の監査）.md に書き、まこさんが OK した文を写しました。ほかは道具が実物から作りました。問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・まこさんの要望が在る工事だけ）と、この工事で確かめてほしいことを問う工事ごとの問い（Q8〜Q9）です。

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-08
- 依頼者: CC（起案者）
- 監査区分: 実装の監査
- 監査対象タスク: M2-C-15・M2-F-10b・M2-D-8／設計書 m2c15-period-settings-20261008
- 監査の相手と版: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-period-settings-20261008.md` ／ ハッシュ値 d3bcbaf0398f5ccaed7419e85e5b2c70eea5d69222a37dd9a8c313e47989a64f
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-08_m2c15_period_settings_20261008_impl_cp68_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-08_m2c15_period_settings_20261008_impl_cp68_audit_request.md`

---

## この監査で答えてほしいこと

### 結論を決める問い

- **問い1**＝設計書の実装の指示（5 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。あわせて、この工事で確かめてほしいこと（Q8〜Q9 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けている・工事ごとの問いで設計書と違う所が見つかれば NO。

(結論を決めるのは、この問いだけ。結果の「7. 総合判定」で、問いごとに YES / NO と根拠を書く)

### 結論の決め方

- **GO**＝問い1 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の番号と実物の行で示してください。

### この監査の前提

1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-period-settings-20261008/やることの表.md`）に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。
5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。

---

## 監査依頼の経緯

1. **この工事は何のためか**＝1つ目の工事（m2c15-period-textbook-20261007・CP67）で「使う」に入った11種のうち、設定を持つ種類を、資料から設定ファイル（observe_config.json・search_limits.json）に写す。engine_tuner が読むのは設定ファイルなので、写さないと11種を資料どおりに扱えない。写した後は、照らしの道具の②（設定ファイルが、いまの資料から写したものと同じか）が食い違い0件になる
2. **この工事は何か**＝K-3a の1つ目の工事（m2c15-period-textbook-20261007）で、教科書の期間の区切りの版11種を材料に足し、G-1 で「使う」の表と資料の表3つを作り直しました。資料が変わったので、照らしの道具の②が、設定ファイルと資料の食い違いを2件 出しています（observe_config.json の値を埋めない種類の並び・search_limits.json の探す範囲）。これは1つ目の工事の設計書に書いた見込みどおりで、まこさんが OK した分け方（K-3a の 3-2 の4番）の後半が、この工事です。2つの設定ファイルの、資料から写す塊を道具が写し直します。探す範囲の行が増えると、前からの壊すプログラム b143 が探す行の末尾が変わるので、b143 も同じ形に直します。コードは1行も変えず、材料の列も変わりません。この工事の後、2つの工事をまとめて実装の監査 CP67 に出します。（やることの番号 M2-C-15・M2-F-10b・M2-D-8）
   **この工事の位置**＝全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝材料を直す（監査 CP60 の修正・法則どおりの帯の部品・S1 の部品） → M2-F｜段ごとに測って並べ、上位を次の段へ渡す（段1〜段4）＝1本ずつの成績と順位を出す → M2-F-10b｜測る道具を直す（工事2）＝①正解ラベル2本との一致率で並べる ②手で組んだ土台を置いて、その上に候補を足して測る口 ③確認の窓でも測る口 ④段4 を役割ごとに動かす ⑤6項目のチェックを通す → M2-D｜場面を分ける材料の順位を engine_tuner に渡す → M2-D-8｜直した材料で、成績表（material_ranking.json）を作り直す → この工事

---

## 着手前必読 (省略禁止・auditor 用・18 件)

**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-period-settings-20261008.md` — 監査の相手（設計書・プログラムが作った）
2. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:m2c15-period-settings-20261008 の行）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-period-settings-20261008/やることの表.md` — 設計書の元（やることの表）＝修正の指示を書く先
4. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — 目標（全月 net ≥ $1,900）と全体戦略、ハード制約（§4.6）
5. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-103） — engine_tuner の目的と、作ってはいけないもの（探す値を CC が点の一覧で限定するもの）
6. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:95-146） — M2 が M1〜M6 のどこに当たり、何ができたら終わりか
7. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:3-46・:1173-1183） — M2 で作っている物と、この工事（M2-C-15＝材料を直す）の中身
8. `SDK/.claude/ratchet/acceptance_archive/m2c15-period-settings-20261008.md`（全文） — 承認済みの設計書の控え（実装の指示5件・完成の条件3行）
9. `SDK/scripts/priority_rebuild/observe_config.json`（:294） — 値を埋めない種類の並び（8種を足して32種）（Q8）
10. `SDK/scripts/priority_rebuild/recipes/search_limits.json`（:44-152） — 探す範囲の RCI の行と、足した close vs VWAP典型 の範囲 288〜288（Q8）
11. `.claude/state/indicator_params_by_strategy.md`（:165-175） — 写す元の資料の11種の行（Q8）
12. `.claude/state/indicator_review/r3_draft_build.py`（:152-200・:399-440） — 資料から設定ファイルの中身を作る写し方 compute・cfg_block・lim_ranges（照らしの②がこれを使う）（Q8）
13. `.claude/state/indicator_review/k3s_draft_build.py`（全文） — 写しに当てて確かめた道具（自己テストの一覧と許しを承認の前の検査 A12 の本体から読む）（Q8）
14. `.claude/tools/check_indicator_sources.py`（全文） — 照らしの道具（①「使う」の指標が資料の表3つに全部 在るか・②設定ファイルがいまの資料から写したものと同じか）（Q8・Q9）
15. `.claude/breaks/b143_rci_range_short.sh` — 前からの壊すプログラム。探す範囲の行の末尾が変わるので、直す前と後の文字に「,」を足した（Q9）
16. `.claude/breaks/b149_pending_not_copied.sh` — 新しい壊すプログラム。値を埋めない種類の並びを写す前に戻すと、照らしの②が落ちるか（Q9）
17. `.claude/breaks/b150_vwaptp_range_missing.sh` — 新しい壊すプログラム。探す範囲から close vs VWAP典型 の行を外すと、照らしの②が落ちるか（Q9）
18. `.claude/state/session_worklog_20261008.md`（:50-58） — この工事の経緯（§5）＝読むもの宣言・案・承認の前の検査・当てた結果・G2

★直す相手になりうるファイルを必ず入れる (結果の「修正の指示」の「直す前の文字」を、監査が実物から写すため)。プログラムが作る文書 (設計書など) を監査するときは、その元データ (設計書なら、工事のフォルダ `.claude/state/verbatim/<工事名>/` の `やることの表.md`。承認の後は `SDK/.claude/ratchet/acceptance_archive/verbatim/<工事名>/`) も入れる。`acceptance_src.json` は 2026-09-30 から使っていない (ratchet に無い) ので、直す相手に書かない。

---

## 大目的 (不変・基準の味方として絶対遵守)

**月次 NET ≥ $1,900 全 12 ヶ月クリア達成** (cc_role §1.0)

⚠️ 本監査スコープ = 設計書 `m2c15-period-settings-20261008` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `m2c15-period-settings-20261008` の中身です。

---

## 監査対象の事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_config.json` | 294行（設定・1つ目の工事で「使う」に入った11種の、値を埋めない種類の並びを、資料から道具が写し直す（照らしの道具の②が見る中身）） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 149行（設定・1つ目の工事で足した close vs VWAP典型 の範囲を、資料から道具が写し直す（照らしの道具の②が見る中身）） | 直した後の文字 |
| 3 | `.claude/breaks/b143_rci_range_short.sh` | 19〜20行（壊すプログラム・探す行と壊した行の末尾に「,」を付ける＝search_limits.json の当てた後の行に合わせる） | 直した後の文字 |
| 4 | `.claude/breaks/b149_pending_not_copied.sh` | なし（新しいファイル） | 直した後の文字 |
| 5 | `.claude/breaks/b150_vwaptp_range_missing.sh` | なし（新しいファイル） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:m2c15-period-settings-20261008）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/observe_config.json` | 当てた | 2026-10-08T19:21:49 |
| 2 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-08T19:21:49 |
| 3 | `.claude/breaks/b143_rci_range_short.sh` | 当てた | 2026-10-08T19:21:49 |
| 4 | `.claude/breaks/b149_pending_not_copied.sh` | 当てた | 2026-10-08T19:21:49 |
| 5 | `.claude/breaks/b150_vwaptp_range_missing.sh` | 当てた | 2026-10-08T19:21:49 |

### 必読に要るファイル（道具が設計書と実装から拾った）

| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15・M2-F-10b・M2-D-8） | 入れる |
| `SDK/scripts/priority_rebuild/observe_config.json` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b143_rci_range_short.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b149_pending_not_copied.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b150_vwaptp_range_missing.sh` | 直す相手（TARGET） | 入れる |

---

## 監査スコープ

### 監査対象 (本監査内)

- Q1：実装の指示を当てた結果が、実装の後と1文字も同じか
- Q2：実装の指示のどれにも当たらない行（設計書に無い変更）が無いか
- Q3：当てた記録が、実装の指示の全部と1件ずつ合うか
- Q4：承認した版の設計書どうしで、実装の指示が同じか
- Q5：実装の指示が、やることの表の要件を全部 満たすか
- Q6：完成の条件が、実装の後に本当に成り立つか
- Q8：11種の設定は、資料から漏れなく・余計なく写っているか
- Q9：壊すプログラム3本は、直しを外したときだけ落ちるか

### 監査対象外 (現時点で判定不可能 or 別監査スコープ)

- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- 1つ目の工事で当てたコード・参照表・範囲の直しを変えること（もう当てた。この工事は設定の写しだけ）
- 値が決まらない種類（前日POC ほか）に値を渡すこと（名前に出さない引数へ値を渡すのは工事2（M2-F-10b）。この工事では並びに載せるだけ）
- K-3b・K-3c・K-4・B-1＋S-1（次の工事）
- 成績表（material_ranking.json）の作り直し（M2-D-8。増えた11列は、作り直すまで成績表に行が無く、段の候補の順位に出ない）
- 監査に出す前のチェックの自己テストの P7-1 の落ち（この工事の前から在る（壊した見本の設計書を渡しても、設計書の形の誤りで止まらない）。next_step §6 に積んである）

---

## 監査観点 (一般・auditor_template ①〜⑦)

該当なし（この監査は、実装が設計書のとおりかと、まこさんの要望を満たしているかだけを問う。①〜⑦の観点は、この争点に関係しない。結果の所見の「一般の観点」にも「該当なし」と書く）

---

## 監査観点 (本監査固有・Q1-QN)

★問いごとに優先度を付ける＝A（結論を変える）／B（実装の前に直す）／C（完成の測り方以外の書き漏れ）／D（結論に効かせない）。結果の所見は、この問いの番号をそのまま見出しにし、優先度の順に書く。時間が足りずに省いた問いは、結果にその番号を書く。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**優先度の理由**＝違えば、実装は設計書のとおりに作られていない

実装の前（commit 2f75845（依頼書を作った時点の HEAD。承認の控えをまだ commit していないので、実装の前はこの commit の版。`git show 2f75845:<パス>` で出せる。★この後に commit しても、この番号で出せる）。★同じファイルに、この工事より前に当てた別の工事の直しが重なっている＝m2c15-period-textbook-20261007（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-period-textbook-20261007.md` の 4-20・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）。実装の前は、HEAD の版に、その工事の実装の指示を当てた時刻の順に当てた版）の対象のファイル（`.claude/breaks/b143_rci_range_short.sh`・`.claude/breaks/b149_pending_not_copied.sh`・`.claude/breaks/b150_vwaptp_range_missing.sh`・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）に、設計書 4-20 の実装の指示（5 件）を番号の順に当てた結果が、実装の後（依頼書を作った時点の作業中の変更（まだ commit していない。`git diff 2f75845 -- <パス>` で見られる。★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、`git diff 2f75845 <その commit> -- <パス>` で見る））と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**優先度の理由**＝在れば、設計書に無い変更が実装に混ざっている

実装の前（commit 2f75845（依頼書を作った時点の HEAD。承認の控えをまだ commit していないので、実装の前はこの commit の版。`git show 2f75845:<パス>` で出せる。★この後に commit しても、この番号で出せる）。★同じファイルに、この工事より前に当てた別の工事の直しが重なっている＝m2c15-period-textbook-20261007（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-period-textbook-20261007.md` の 4-20・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）。実装の前は、HEAD の版に、その工事の実装の指示を当てた時刻の順に当てた版）と実装の後（依頼書を作った時点の作業中の変更（まだ commit していない。`git diff 2f75845 -- <パス>` で見られる。★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、`git diff 2f75845 <その commit> -- <パス>` で見る））の差分（`.claude/breaks/b143_rci_range_short.sh`・`.claude/breaks/b149_pending_not_copied.sh`・`.claude/breaks/b150_vwaptp_range_missing.sh`・`SDK/scripts/priority_rebuild/observe_config.json`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**優先度の理由**＝合わなければ、どの件を道具が当てたかを後から確かめられない

当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2c15-period-settings-20261008`）が、実装の指示の 5 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**優先度の理由**＝当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない

承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-period-settings-20261008.md`）と、監査の相手の設計書（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-period-settings-20261008.md`。★`.claude/state/acceptance.md` は、この工事の後に別の工事の設計書で上書きされたので比べない）の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**優先度の理由**＝要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない

実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-period-settings-20261008/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**優先度の理由**＝成り立たなければ、承認のときの「済」が根拠にならない

設計書の完成の条件（3 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --check-indicator-sources`・`python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog`

### Q8 — 11種の設定は、資料から漏れなく・余計なく写っているか（優先度 A）

**優先度の理由**＝写し誤ると、engine_tuner が11種を資料と違う値で扱うか、値を埋めない種類なのに値を探す

値を埋めない種類の並びに足したのは8種です（当日VWAP・前日と当日の POC・VAH・VAL・close vs VWAP典型）。前週pivot の3種は「パラメータを持たない」ので並びに入りません。探す範囲には close vs VWAP典型 の 288〜288 を足しました。CC は値を書いていません。写したのは道具（r3_draft_build.py の写し方・k3s_draft_build.py）で、照らしの②と同じ写し方です。★CC の自己申告＝close vs VWAP典型 は、値を埋めない種類の並び（「範囲が1点のまま」）と探す範囲（288〜288）の両方に載ります。前から在る close vs VWAP も同じ扱いです。この2か所に載る扱いが、資料と engine_tuner の読み方に合っているかを見てください。写した後の照らしの①②は食い違い0件です。

### Q9 — 壊すプログラム3本は、直しを外したときだけ落ちるか（優先度 B）

**優先度の理由**＝落ちない壊し方が在ると、写し直しが黙って戻っても誰も気づかない

b149・b150 を写しの作業場で走らせ、宣言した文で落ちるか、壊す対象がちょうど1か所かを見てください。b143 は、探す範囲の RCI の行の末尾に「,」が付いたので、直す前と後の文字にも「,」を足しました。壊し方と落ちる文は変えていません。この直しで、b143 が狙う行と落ち方が変わっていないかも見てください。★CC の自己申告＝承認の前の検査を設計書を書いた直後にかけたとき、やり取りの記録を渡さずにかけたので、壊すプログラムと自己テストを走らせた跡が見つからず「不足2件」と出ました。記録を渡すと0件でした。A12 まで含めた検査は 258.1秒で不足0件でした。★CC の自己申告（2つ目）＝経緯の2の「2つの工事をまとめて実装の監査 CP67 に出します」は、承認済みの設計書の概要を写した文です。依頼書を作る道具は1つの工事につき1通を作るので、まこさんの決定で2通（CP67＝1つ目の工事・CP68＝この工事）に分けました。

---

## 外部検索要請 (必須・WebSearch / WebFetch ツール使用)

件数: 0 件 (結果の外部検索の節にも「該当なし」と書く)

該当なし（この監査は、実装が設計書のとおりかを実物で照らす。外部の知見は答えに要らない。設計の理由を調べる外部検索は、設計書の監査で行う）

---

## 依頼を出した CC の自己申告

1. **この工事の外の作業中の変更**＝`.claude/hooks/hook_health_check.sh`・`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_design_check_before_approval.py`・`.claude/hooks/require_request_understood.sh`・`.claude/hooks/trial_design.py`・`.claude/tools/gen_hook_cheatsheet.py`・`.claude/tools/try_hooks.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）

(結果は、この番号ごとに1件ずつ答える)

---

## 結果ファイルフォーマット (auditor 用)

`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-08_m2c15_period_settings_20261008_impl_cp68_audit_report.md` に、次の 11 節をこの順で出力する。★節の名前と並びは変えない。どの種類の監査でも同じ。

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
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-08_m2c15_period_settings_20261008_impl_cp68_audit_request.md
```

または

```
本依頼書を読んで監査して
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-08_m2c15_period_settings_20261008_impl_cp68_audit_request.md
```

→ auditor session の CC が冒頭 auditor 宣言を読んで即 Plan agent 起動・結果ファイル書き出しまで自走。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp68_work/cp68_src.gen.md src_sha256=2dc3ceeb93d02c74cb122ed5e05d16f7d8efbb807212dabcca14e735316c7239 body_sha256=8572025d6b224aad6bdff52abbcba9180f577d1f69903291e00968a6451e9460 -->

# 監査結果 cp65 — CP65 — 資料に足した4種を設定ファイルに写す。M2-C-15（実装の監査）

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_rci_pivot_sources_20261007_impl_cp65_audit_request.md`
- 依頼書のハッシュ値: 1250b9d3fd54a0b75e0b12ca91282bbd1e18b86a59a0d88437d3d9a1c3e448c3
- 監査の相手と版（依頼書に書いてあるもの）: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-rci-pivot-sources-20261007.md` ／ ハッシュ値 bacbf466c28304bbb3f5a98296b4ea865c2c9b8e0454de54609fbf9e1750d95e
- 監査が照らしたハッシュ値: bacbf466c28304bbb3f5a98296b4ea865c2c9b8e0454de54609fbf9e1750d95e（`shasum -a 256` の結果。依頼書と一致。952行。控えに触れた commit は 85b7e1f の1つだけ）
- 実施日: 2026-10-07

★版の読み替え＝依頼書は「実装の前＝HEAD a6f8167・実装の後＝作業中の変更（git diff HEAD）」と書いています。実物では、依頼書を作った後に実装が commit 85b7e1f（2026-10-07 16:59:26・親 a6f8167）に入り、HEAD は f38759b です。対象の4ファイルの `git diff HEAD` は空です。そのため監査は、実装の前＝a6f8167、実装の後＝HEAD の版（＝作業ツリー）として比べました（`git log -1 --format='%h %p %ci' -- <控え>` の出力＝「85b7e1f a6f8167 2026-10-07 16:59:26 +0900」）。


## 2. 監査対象の型宣言

- 数値型＝RCI の一覧 [[5],[7],[9],[26],[52]]・範囲 5〜52・材料の列 476→477。
- コード型＝壊すプログラムの .sh を2本 新しく作った（コードの .py は0行）。
- 文書型＝設計書の控えと、資料の表3つ（indicator_params_by_strategy.md・indicator_params_review.md・indicator_roles_thresholds.md）。


## 3. 監査対象の事実データの確認

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

依頼書の表5件は、設計書の控え 425〜555行の実装1〜5と、番号・対象のファイル・行（247・293・148・新しいファイル2つ）が全部 一致しました。

### 当てた記録（applied_fixes.json の名前 design:m2c15-rci-pivot-sources-20261007）

`SDK/.claude/audits/applied_fixes.json` の 2846〜2880行の num 1〜5 が、依頼書の表5件と一致しました。5件とも当て方は「当てた」、時刻は 2026-10-07T14:19:24 です。同じファイルに重なった前の工事 m2c15-param-values-fix-20261007 の16件は 11:43:47 に当たっていて、こちらより先です。

### 必読に要るファイル（道具が設計書と実装から拾った）

依頼書の表8件は全部 実在し、開きました。必読25件も全部 開きました。ただし次の2つは一部だけ読みました。

- `cat_requirements.md`＝H2・H6 と目標の行だけ。
- `signal_families.md`＝見出し・RCI の部品の行・承認の指紋の行だけ。


## 4. 所見

### 一般の観点

該当なし（依頼書のとおり）

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

合う。重さ＝Process 1件（照らしの結論には効かない）。

- 前の工事の実装4の直した後（m2c15-param-values-fix-20261007.md:545）と、この工事の実装2の直す前（m2c15-rci-pivot-sources-20261007.md:447）は、diff で同じでした。この工事は、前の工事を当てた版の上に当たっています。
- 直す前の文字は、実装の前の版（a6f8167 ＋前の工事）にちょうど1か所ずつ在りました（`  "close vs MEDIAN%": [[30]]`＝1・`"close vs MEDIAN%": [{"kind": "int", "lo": 4, "hi": 200}]`＝1・`"_material_params_pending"`＝1）。
- 当てた後の文字と実物を diff で比べ、5組とも同じでした。observe_config.json 247〜248行＝設計書 435〜436行／pending の行（294行）＝設計書 452行／search_limits.json 148〜149行＝設計書 468〜469行／b142 の全27行＝設計書 484〜510行／b143 の全27行＝設計書 525〜551行。
- 実物の確かめ＝observe_config.json:248「  "RCI": [[5], [7], [9], [26], [52]]」・search_limits.json:149「    "RCI": [{"kind": "int", "lo": 5, "hi": 52}]」。
- 【Process】依頼書の版の書き方が実物と合いません。依頼書は「実装の前＝HEAD a6f8167・実装の後＝作業中の変更（git diff HEAD）」と書きますが、依頼書を作った後に実装と控えが commit 85b7e1f に入り、対象4ファイルの `git diff HEAD` は空です（1 の「版の読み替え」）。依頼書の文は gen_audit_docs.py:1109 の決まった文から作られていて、依頼書を作った後の commit を想定していません。

修正の番号＝2

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

合う。重さ＝なし。

- `git diff a6f8167 HEAD` の対象4ファイルの差分を全部 見ました。
- observe_config.json の差分は3か所です。RCI の行（この工事の実装1）・material_keep（前の工事の実装3）・pending（前の工事の実装4の後に、この工事の実装2）。
- search_limits.json の差分は、TSI・StochRSI・ALMA・MCGD・SSF・T3・VIDYA・注記（前の工事の実装5〜12）と、RCI の行（この工事の実装3）です。
- b142・b143 は新しいファイルです。
- どの実装の指示にも当たらない行は0行でした。

修正の番号＝なし

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

合う。重さ＝なし。

- applied_fixes.json の num 1〜5 と、実装の指示5件が、番号・対象のファイルで1対1に合います。
- 「もう当て終わっていた」は0件、抜けも0件です。
- 2つの .sh のファイルの時刻も 14:19 で、記録と合います。

修正の番号＝なし

### Q7 — まこさんの要望を、この工事の後の実装が満たしているか（問い2）（優先度 A）

満たす。重さ＝Minor 1件（Q10 と同じもの）。

- 要望1＝満たしています。設定の一覧の RCI は [[5],[7],[9],[26],[52]] です（observe_config.json:248）。範囲は 5〜52 です（search_limits.json:149）。engine_tuner_gen.py の material_ranges（297〜303行）が、この範囲を `"src": "makosan"` として使います。前期間pivot の3種は、パラメータを持たないとして `_material_params_pending` から外れました。
- 要望2＝満たしています。照らしの①②は pre_audit_check.py の CHECKS（55〜76行）に入っていて、`--run` のたびに走ります。①は gen_acceptance.py 1121〜1128行でも、設計書を作る前に走ります。
- 足りない所＝`--run` の後に資料や search_limits.json が変わっても、依頼書を作るときの `--verify` が古い「通った」を使い続けます（Q10 の所見）。要望2 の満たし方を弱めますが、結論は変えません。

修正の番号＝1

### Q8 — RCI の一覧と範囲は、資料から漏れなく・余計なく写っているか（優先度 A）

合う。重さ＝なし。

- 資料 indicator_params_by_strategy.md:161 の RCI の行は、スキャル [[5],[9],[26]]・デイトレ [[9]]・範囲「5〜52（見つかった値と今の値の最小〜最大）」です。
- 写し方は r3_draft_build.py の compute（178〜211行）です。最初の値（5・9・26・9）と残す名前（V9 の RCI7・RCI9・RCI52）を合わせると {5,7,9,26,52} になり、写った一覧と一致します。範囲 5〜52 は一覧の値を全部 含むので、広げていません。
- まこさんが OK した選び方（okd_param_rule＝違うサイト2つ以上・✅だけ）とも合います。5＝mql5 と pineify、9＝wikibit・oanda・ebc、26＝mql5 と oanda です。14 と 52 は1サイトだけなので最初の値に使っていません。デイトレの 26・52 は zai（✗）を除くと wikibit だけになるので使っていません。
- 前期間pivot の3種の列の作り方は変わっていません。`_material_params_pending` を読むコードは、scripts の .py に0件です（grep で当たったのは check_indicator_sources.py だけ）。3種は material_params に入っていないので、build_catalog の addf（observe_diag.py:1335〜1343）を通る道は前と同じです。
- RCI7・9・26・52 は同じ make_material で作られ、増えた列は RCI5 だけです（signal_families.json の差分は RCI5 の部品と範囲の写しだけ）。

修正の番号＝なし

### Q9 — 資料に足した4種の行は、調べた逐語とページの照らしのとおりか。前の141種の行は変わっていないか（優先度 A）

足した4行は合う。前の141行は、設定に写る欄は変わっていないが、ほかの欄はデータ不足。重さ＝Process 1件（修正なし）。

- ページの照らしは、verify_out_g7.json が一致50・不一致2（外為どっとコムの既定 #1・ザイFX! のデイトレ #4）、verify_out_w3.json が一致75・不一致4（外為どっとコム #1・ザイFX! #12〜14）で、依頼書と一致します。
- 不一致の逐語は indicator_params_review.md:163 で ✗ の印が付き、indicator_params_by_strategy の値には使われていません。閾値の13件は全部 一致です。
- 141行のうち設定に写る欄（最初の値・範囲・軸の数）は変わっていません。根拠＝照らしの②が食い違い0件（Q6）と、この工事の実装の指示が RCI と pending だけであること（設計書 4-0 の③④⑤）。
- 141行のほかの欄（逐語・メモ・md の行）はデータ不足です。理由＝①比べた控え（worklog 20261007 §11:111 の scratchpad の before_src）が残っていません（find で0件）②資料の表は git の外です（.gitignore:45「.claude/state/*」）。
- 【Process・修正なし】worklog 20261007 §11:116 の比べ方は `jq -S`＝JSON だけで、md の表の行は比べていません。監査が同じ比べ方をやり直せる控えも残っていません。

修正の番号＝なし

### Q10 — 照らしの道具①②は、資料と設定ファイルのずれを毎回 見つけられるか（優先度 A）

合う。重さ＝Minor 1件。

- 照らしの①は「使う」の指標と資料の表3つの種類を、両方の向きで比べ、重複も見ます（check_indicator_sources.py:52〜67）。
- 照らしの②は設定の2つの塊を、資料から写し直したものと1文字ずつ比べます（同 90〜103行）。写し方は r3_draft_build.py と同じ関数です。
- 依頼書が例に挙げた3つの道（指標を「使う」にする工事・資料を作り直す工事・設定ファイルを手で直す工事）は、どれも次の `pre_audit_check.py --run` の CHECKS で見つかります。
- 【Minor】依頼書を作るときの関門は `pre_audit_check.py --verify` です（gen_audit_docs.py:294〜297）。`--verify` が見る指紋の一覧 FINGERPRINT_FILES（pre_audit_check.py:86〜90）に、search_limits.json・資料の json 3つ・indicator_switch.json・r3_draft_build.py が入っていません。そのため `--run` の後にこれらが変わっても、前の「通った」がそのまま使われます。
- 守りの穴探しは対象外（恒久65番）なので、結論には効かせていません。

修正の番号＝1

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

合う。重さ＝なし。

- この工事の控えは acceptance_archive に1版だけです（.md は1つ・時刻 14:18）。
- 設計書の 4-20 と、元データ okd_r5_20261007.txt の 179〜233行（4-20 の JSON）とで、5件の直す前の文字と中身が一致しました。
- `.claude/state/acceptance.md` は、いまは g2-sentinel-material-pick-20261007 の設計書（1行目の ARC iter）なので、依頼書のとおり比べていません。

修正の番号＝なし

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

合う。重さ＝なし。

- F-1 は実装1・2・3で満たし、b142 が守っています。F-2 は実装3で満たし、b143 が守っています。
- G-1・G-2 は手順で、実装の指示ではありません。G-1 は worklog 20261007 §14:148 のとおり行われ、型の表の承認は 0bdadafa です（signal_families_approved.txt）。G-2 は pre_audit_check.json（16:27:26）で13本 全部 rc=0、check_indicator_sources も rc=0 です。
- 3-2 の1（CP64 と1回に出す）は、worklog 20261007 §17 で まこさんが「A」（工事ごとに出す）を決めたので変わっています。食い違いではありません。

修正の番号＝なし

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

成り立つ。重さ＝Minor 1件（修正なし）。

- SDK のフォルダで2本を走らせました。`python3 …/pre_audit_check.py --check-indicator-sources` は「✅ 指標の資料と設定ファイルの照らし: 食い違い 0 件」・rc=0・5秒。`python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` は「K-1・K-8・G-2 の番人（--selftest-catalog）: ❌ 0 件」・rc=0・8秒。
- 設計書 2-1 の grep 3本も実装の後の版で取り直しました。observe_config.json:248 に RCI の行が在る（rc=0）・「RCI＝資料（修正対応表）に行が無い」は無い（rc=1）・search_limits.json:149 に RCI の範囲が在る（rc=0）。
- 【Minor・修正なし】設計書 346行「3. 壊すプログラムが、全部 決めた文で落ちる。コマンド＝python3 .claude/tools/run_breaks.py --design。」は、`--design` の値が無いので走りません（run_breaks.py:624「    ap.add_argument("--design", default=str(DESIGN))」＝値が1つ要る）。完成の条件（7-6）の外の文で、控えは承認の後に凍結されているので、修正の指示は出していません。

修正の番号＝なし

### Q11 — 壊すプログラム2本は、直しを外したときだけ落ちるか。RCI5 が増えた影響は、設計書に書いたものだけか（優先度 B）

合う。重さ＝Process 1件（修正なし）。

- 直しが在るときは、測るコマンド2本がどちらも rc=0 です（Q6）。
- 壊す相手の文字は、どちらも実物にちょうど1か所です。b142 の `  "RCI": [[5], [7], [9], [26], [52]]` は observe_config.json に1か所、b143 の `    "RCI": [{"kind": "int", "lo": 5, "hi": 52}]` は search_limits.json に1か所です。
- 中身を読むと、壊したときは宣言した文で落ちます。b142 は、compute が資料の最初の値5を入れて一覧を作るので設定と食い違い、「❌ ②observe_config.json の material_params〜」で rc=1 になります。b143 は、番人⑬（observe_diag.py:7114〜7128）が「❌ P-2: RCI52 の 1 番目の数字 52 が、設定の範囲 5〜26 の外」で rc=1 になります。
- 2本は走らせていません。理由は 10 に書きました（lib.sh が本物のパスを決め打ちにして本物を書き替えるため）。
- RCI5 の影響は、設計書 4-13 に書いたものと同じでした。部品 476→477・出口の表の parts_count 477・材料の列 5236→5247（＋11＝時間足11本）・選べる組 226→227。組み立ての表は正本の指紋を書き直しただけです。H2 は 16:27 の走行で rc=0 です。
- CC が自己申告した G2 の落ちのほかに、変わった所は見つかりませんでした。
- 【Process・修正なし】G2 の落ちは、gen_signal_families.py の `_real_structures`（841行〜）が、種を固定した乱数で構造を作る作りなので起きました（同 991行「    sts = _real_structures(30, seed=20260807)」）。設計書 4-13 に書かれておらず、4-14 の「写しで確かめた」に G2 の `--verify` が入っていなかったので、承認の前に見つけられませんでした。直しは別の工事 g2-sentinel-material-pick-20261007（当てた時刻 16:09:37）で済んでいます。この工事は乱数を足していません（コードは0行）。

修正の番号＝なし


## 5. 外部検索

該当なし（依頼書のとおり）


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

申告どおりです。並んでいる10ファイルは、この工事の TARGET の外です。Q1・Q2 の差分は、対象の4ファイルだけで取りました。いまの状態は次のとおりです。

- check_indicator_sources.py・gen_acceptance.py・gen_audit_docs.py・pre_audit_check.py は commit 430641c に入っています。
- engine_tuner_gen.py・observe_diag.py は前の工事の分、gen_signal_families.py は g2-sentinel の分として commit 85b7e1f に入っています。当てた記録 2735〜2895行と合います。
- hook 2本と e38_logics.backup_20260802_005140.json は、まだ git に入っていません（??）。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ YES（根拠＝Q1〜Q6・Q8〜Q11 が全部 合う。実装は実装の指示5件と1文字も違わず、設計書に無い変更も抜けも0件。Q9 のデータ不足は、食い違いを見つけたものではない）
- 問い2 ＝ YES（根拠＝要望1・2とも満たす（Q7）。要望2 の指紋の不足は Minor で、照らしそのものは `--run` のたびに走る）

### 結論と件数

- 結論＝GO
- Critical＝0
- Major＝0
- Minor＝2
- Process＝3


## 8. 修正の指示

### Critical

なし

### Major

なし

### Minor

#### 修正 1
対象のファイル: .claude/tools/pre_audit_check.py
直す箇所: 86〜90行
直す前の文字:
~~~
FINGERPRINT_FILES = [
    "observe_diag.py", "indicator_reference_diag.py", "observe_config.json",
    "gen_signal_families.py", "gen_indicator_switch.py", "gen_materials.py",
    "gen_exit_families.py", "engine_tuner_gen.py", "engine_tuner_exec.py",
]
~~~
直した後の文字:
~~~
FINGERPRINT_FILES = [
    "observe_diag.py", "indicator_reference_diag.py", "observe_config.json",
    "gen_signal_families.py", "gen_indicator_switch.py", "gen_materials.py",
    "gen_exit_families.py", "engine_tuner_gen.py", "engine_tuner_exec.py",
    # ★照らしの道具（check_indicator_sources.py）が読む相手も指紋に入れる＝--run の後に設定・資料・写し方が変われば --verify が止める
    "recipes/search_limits.json",
    "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_params_review.json",
    "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_params_by_strategy.json",
    "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_roles_thresholds.json",
    "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/indicator_switch.json",
    "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_review/r3_draft_build.py",
]
~~~
根拠の抜き書き: .claude/tools/pre_audit_check.py:97「        p = PR / name」
状態: 確定


## 9. CC プロセス欠陥対策

### Process

#### 修正 2
対象のファイル: .claude/tools/gen_audit_docs.py
直す箇所: 1109行
直す前の文字:
~~~
        post_desc = "作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる）"
~~~
直した後の文字:
~~~
        post_desc = ("作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる。"
                     "★依頼書を作った後に承認の控えを commit したときは、`git log -1 --format='%h %p' -- <承認の控えのパス>` の"
                     "1つ目を実装の後、2つ目を実装の前として比べる）")
~~~
根拠の抜き書き: .claude/tools/gen_audit_docs.py:1107「        pre_desc = (f"HEAD の commit {head or '（読めない）'}（承認の控えをまだ commit していないので、実装の前は HEAD の版。"」
状態: 確定


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

### 開いたファイルと行

- 依頼書（全436行）・設計書の控え（1〜952行の全部）・m2c15-param-values-fix-20261007.md（519〜688行）・やることの表.md（全99行）・okd_r5_20261007.txt（1〜12・145〜279行）。
- applied_fixes.json（2730〜2896行）・observe_config.json（247〜248・294・326〜334行）・search_limits.json（差分の範囲の全部）。
- indicator_params_by_strategy.md（1〜12・150〜166行）・indicator_params_review.md（1〜30・155〜166行）・indicator_roles_thresholds.md（1〜12・159〜164行）・out_g7.json（全424行）・verify_out_g7.json と verify_out_w3.json（不一致の行と数）。
- check_indicator_sources.py（全166行）・pre_audit_check.py（40〜100・183〜216・440〜491行）・gen_acceptance.py（1110〜1135行）・gen_audit_docs.py（280〜300・1085〜1125行）・r3_draft_build.py（36〜250・390〜440行）・apply_audit_fix.py（60〜260・669〜700行）・gen_audit_docs.py の item_fields（1823〜1850行）。
- b142・b143（全27行ずつ）・.claude/breaks/lib.sh（1〜80行）・observe_diag.py（1326〜1385・4515〜4526・7011・7095〜7142行）・engine_tuner_gen.py（231〜320行）・gen_signal_families.py（838〜860・991行）・run_breaks.py（624行）。
- worklog 20261007（95〜185行）・cat_requirements.md（H2・H6・目標の行）・engine_tuner_requirements.md（作ってはいけないもの）・engine_tuner_milestones.md（95〜146 の見出し）・engine_tuner_milestones2.md（3〜46・995〜1040・1173〜1183行）・signal_families.md（RCI の部品と指紋の行）・okd_param_rule・okd_source_rule。

### 走らせたコマンドと結果と秒数

- `pre_audit_check.py --check-indicator-sources`（SDK のフォルダ）＝食い違い0件・rc=0・5秒。
- `observe_diag.py --selftest-catalog`（SDK のフォルダ）＝❌ 0 件・rc=0・8秒。
- 読むだけのコマンド（git status・git log・git show・git diff・shasum・grep・sed・diff・stat・find）＝秒数は測っていない。
- 走らせた2本は本物を書き替えていません（indicator_params_by_strategy の json と md・pre_audit_check.json・.pyc の時刻が前後で同じ）。

### 走らせられなかったものと理由

- b142・b143＝.claude/breaks/lib.sh:21〜23 が ROOT を本物のパスに決め打ちにし、本物の設定ファイルをその場で書き替えます。check_indicator_sources.py:33 も ROOT を決め打ちにしています。写しで走らせても本物を書き替えて本物を読むので、中身を読んで判定しました。
- `--check-indicator-sources --selftest`＝一時ファイルに書くので、読むだけの約束（Plan のサブエージェント）に反するため走らせていません。
- cp65_work への写し＝Plan のサブエージェントはファイルを作れないので、比べる作業は git show・git diff・diff で行いました。cp65_work に在るのは、結果の cp65_result.md と、見直し表の cp65_result.review.md と、依頼書の元 cp65_src.gen.md だけです。
- hook に止められたもの＝python のコードを標準入力から渡す形は設計↔実装ゲートに、.claude/breaks を指す for の繰り返しは土台ゲートに止められました。同じ確かめは読むだけのコマンドでやり直しました。


## 11. 本物のファイルを書き替えていないこと

- `git status --short` は、監査の前も後も177行で、同じ並びでした。
- 全部「??」（git の外のファイル）で、追跡しているファイルの変更（「 M」の行）は前も後も0行です。`git diff HEAD --stat` も空です。
- 監査の後に書いたのは、作業場の `cp65_work/cp65_result.md` と `cp65_work/cp65_result.review.md`（どちらも git の外）と、この結果ファイルだけです。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_m2c15_rci_pivot_sources_20261007_impl_cp65_audit_request.md request_sha256=1250b9d3fd54a0b75e0b12ca91282bbd1e18b86a59a0d88437d3d9a1c3e448c3 -->

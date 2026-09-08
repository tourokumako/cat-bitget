<!-- ARC iter="approval-audit-plumbing-20260907" -->

# 設計書｜承認と監査の仕組みの7件＋作業を止めている6件を、まとめて直す（2026-09-07・§6 の修正対応）

TARGET: .claude/tools/gen_regime_kb.py, .claude/tools/pre_audit_check.py, .claude/tools/run_breaks.py, scripts/priority_rebuild/gen_audit_request.py, scripts/priority_rebuild/verify_design_contract.py, scripts/priority_rebuild/engine_tuner_gen.py, .claude/breaks/b06_tool_changed.sh, .claude/breaks/b41_req_frozen_section_gone.sh, .claude/breaks/b42_pre_audit_list_gone.sh, .claude/breaks/b43_approve_empty_freeze_gone.sh, .claude/breaks/b44_approve_record_write_gone.sh, .claude/breaks/b45_measure_only_gone.sh, .claude/breaks/b46_spec_lineno_gone.sh, .claude/breaks/b47_dirty_baseline_gone.sh, .claude/breaks/b48_fence_skip_gone.sh, .claude/breaks/b49_foreign_block_gone.sh, .claude/breaks/b50_fixture_name_gone.sh, .claude/breaks/b51_dirty_json_unguarded.sh
NEW_FILE: .claude/breaks/b51_dirty_json_unguarded.sh
MODEL: .claude/breaks/b45_measure_only_gone.sh, .claude/breaks/lib.sh


MODEL: .claude/breaks/b36_demand_attach_gone.sh, .claude/breaks/b37_marks_from_json_gone.sh, .claude/breaks/lib.sh

REQUIREMENTS: `next_step.md` の §6「★★あとで直すことの一覧」。まこさんの指示（逐語 2026-09-07）＝「ここでやることは、M-2-Eではなく、§6 ★★あとで直すことの一覧の修正対応とする」「「承認と監査の仕組み」の7件を1本の設計書でまとめて直す →OK」「他にも作業に支障がでているものがあれば、まとめて直して」。

## 0. 承認の往復について

**往復：2回／内訳＝1回目で書く権利をもらい、2回目で機械が測ります。**

**なぜ1回で終わらないか**＝壊すプログラム10本（b41〜b50）は、これから作るファイルです。承認のプログラムは、承認を打ったその場で壊すプログラムを走らせて終了コードを記録します。まだ実在しないファイルは走らせられないので、1回目は「未着手」のまま残ります。`.claude/breaks/*.sh` は承認ゲートの相手なので、承認の前に置けません。b36〜b40 と同じ形です。

**net に直結するか**＝しません。売買のロジックには1行も触れません。直すのは、承認・監査・照合の配管と、文書を作るプログラムです。

**★私の懸念（先に書きます）**＝13件は8つのファイルにまたがります。1回の実装で11行すべてを「済」にできる見込みは高くありません。**届かなかった行は「未着手」のまま この設計書に残します。**工程表の順番は、止まっている度合いが強いものから並べました。

**★まこさんの決定（逐語 2026-09-07）**＝「**今回は Web Claudeチェックは飛ばす。監査で修正が要件通りにできてるかをチェックする。**」

**＝この設計書は、恒久の決まり §0-3 の①（設計書ができたら Web Claude が見る）を通しません。**まこさんの決定です。**②（実装ができたら監査に出す）は行います。****監査に問うのは「直したものが、§6 に書かれた要件のとおりになっているか」です。**だから監査の依頼書には、13件それぞれについて「§6 の何番が何を求めていたか」と「実装が何をしたか」を1対1で並べます。

## 1. 何を作るか

`next_step.md` の §6 に溜まった13件を直します。**まこさんが承認した7件**（131・121・92・141・146・150・93）と、**作業を止めている6件**（154・155・138・113・145・149）です。

**13件は、4つのまとまりです。**

1. **監査の依頼書を、プログラムで作れるようにする**（121・92・141）
2. **承認のときの測りが、本当に測っていることを確かめる**（131 の b06・146・150）
3. **設計書を書く道・照らす道が、自分自身で塞がらないようにする**（138・113・93）
4. **文書を作るプログラムどうしが、上書きし合わないようにする**（154・155・145・149）

**入れなかったもの（正直に）**＝①129・135（既に直っている＝`grep -n 'identity' .claude/hooks/require_design_contract_before_run.sh` の 67-68行 に `--identity-l1` と `--identity-s1` が在る。§6 の欄を ✅済 にするだけ）②134（観察の検査5 が落ちる＝走らせて測る時間の見込みが立っていない。恒久の決まり61番）③80・84・107・125（まこさんが「直さない」と決めた、または方針の話）④140（監査が直している最中）。

## 2. なぜ作るか（実測）

**（あ）監査の依頼書を作るプログラムが壊れています。**実測＝`python3 scripts/priority_rebuild/gen_audit_request.py --selftest` の逐語「❌ Q6: 作れたのは 0/13」「❌ Q11: 存在しない節を指しても、問題として返さない」「❌ わざと壊して止まるか試すテスト -4/11 pass」。原因＝13要素に分ける形をやめたので、複写元の見出し `## 3.4 …` が正本に無くなりました。**この赤は cp24・cp25・cp26 の3回の監査をまたいでいます。**

**（い）その赤が画面に出ません。**実測＝`grep -c 'gen_audit_request' .claude/tools/pre_audit_check.py` が **0**。監査の前の検査の一覧（`CHECKS`）に入っていないので、気づけません。同じ理由で、新しい検査 `engine_tuner_gen.py --selftest-extra-gate` も走りません（実測＝`grep -c 'selftest-extra-gate' .claude/tools/pre_audit_check.py` が **0**）。

**（う）照合の道具を書き換えても止まりません。**実測＝壊すプログラム b06 は `python3 verify_design_contract.py --diff <設計書>` を測りますが、道具の指紋を照らす処理は `check_impl_functions`（928〜942行）の中に在り、`--diff` の道には在りません。だから b06 は rc=0 で「止まらなかった」と出ます。

**（え）承認より後にコードを直すと、測り直せるのが まこさんだけです。**実測＝`grep -n '_TOOL_OK_J' .claude/hooks/require_acceptance_before_impl.sh` の一覧に `run_breaks.py` が無いので、CC の Bash から走らせると止まります。2026-09-07 に監査 cp27 が、これを理由に「壊し方を1文字も変えずに写した再現プログラム」で代行しました。

**（お）並走している別のセッションが .py を触っていると、どの設計書でも照合が止まります。**実測＝`verify_design_contract.py` の 1044〜1051行 は `git status --porcelain` の .py を全部 見て、設計書の `impl_functions` に無ければ「設計書に書いていないファイルを触った」を返します。**その .py が中で何を呼ぶかは見ていません。**

**（か）設計書に書き方の見本を書くと、自分が止まります。**実測＝`grep -c 'in_fence' .claude/hooks/require_source_read_before_acceptance.py` が **0**＝囲みを読み飛ばす処理がありません。

**（き）設計書に書く行番号を、人が手で写しています。**実測＝`grep -n 'def cmd_write' -A 24 v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/verify_design_contract.py` の 561〜582行＝公開する関数・定数・コマンドの旗は書き出しますが、定義の行番号を出しません。

**（く）2つのプログラムが、同じ節に書き込み合っています。**実測（2026-09-07・私が実際に踏んだ）＝`python3 ../../.claude/tools/gen_regime_kb.py --write` を走らせたら、`gen_materials.py` が書いていた囲みの中身が古い数字に戻りました（17行・部品 555件 → 551件 ほか）。`git checkout` で戻しました。**そのため `gen_regime_kb.py --verify` は毎回 ❌ を出し、文言は「手で書き換えられています」＝人のせいにする誤った説明になります。**

**（け）その ❌ の中に、直せる行番号のずれが1件あります。**実測＝`gen_regime_kb.py --verify` の逐語「❌ R7: `engine_tuner_exec.py:2464` の前後5行に `wpct_arr` が無い」。実物は 2568行です（`grep -n 'wpct_arr' scripts/priority_rebuild/engine_tuner_exec.py` ＝ 2568行と 2570行の2件。2568行の中身は W% を作る式）。

**（こ）生成器の静的検査が赤のままです。**実測＝`python3 .claude/audits/m2d_lint_check.py` の逐語「見本の関数: 1 件 行=[3815]」。3815行は `_check_extra_gate` の中で、この関数名に `selftest` が入っていないため、静的検査（`lint_provenance` の⑤・6010行）が「自己テストの外で見本を使った」と数えます。

## 3. 深掘り4点

**① 真因**＝**強制の仕組みを、そのつど1本ずつ足してきたことです。**足すたびに「誰が走らせるか」「誰が測るか」「どこに書くか」を決めますが、**既に在る仕組みとの重なりを毎回は見ていませんでした。**その結果、①同じファイルの同じ節に2つのプログラムが書き込み（154）②測るはずの壊すプログラムが別の道を測り（131）③走らせる口が土台ゲートに塞がれ（150）④照らす側が並走を考えていない（138）という形で出ました。

**② 期待値分解**＝この工事は売買のロジックに1行も触れません。勝率・平均利益・敗率・平均損失は動きません。動くのは、**赤のまま放置されている検査の本数**（`gen_audit_request.py --selftest` が -4/11 → 11/11 ／ `gen_regime_kb.py --verify` が3件 ❌ → 0件 ／ `m2d_lint_check.py` が1件 → 0件）と、**CC が自分で走らせられる測りの本数**（壊すプログラムの測り直し 0 → 1本の口）です。

**③ root か symptom か**＝root です。「今回だけ手で直す」のではなく、①依頼書は凍結ファイルから作る形にする ②壊すプログラムが本当の道を測る ③測り直しの口を作る ④照らす側に並走の基準を持たせる ⑤囲みを読み飛ばす ⑥行番号は機械が出す ⑦囲みの持ち主を尊重する、という形に直します。

**④ ベースアップ**＝外の検索は使いません。手本は同じリポジトリの実物で、この設計書を書く前に Read tool で開きました。壊すプログラムの形＝`.claude/breaks/lib.sh`（`guard`・`measure`・`finish` と、戻した後にハッシュ値を照らして違えば exit 99）・`b36_demand_attach_gone.sh`・`b37_marks_from_json_gone.sh`（どちらも「壊す対象の行が見つからない」ときは止まる形）。測る相手は 120秒 に収まる口にする（`run_breaks.py` の `TIMEOUT_SEC = 120`・打ち切りは強制終了で戻す処理が走らないため）。指紋の照らし＝`verify_design_contract.py` の `check_impl_functions`（928〜942行）。土台ゲートの通す判定＝`require_acceptance_before_impl.sh` の `_readonly_seg` と `_TOOL_OK_J`。

## 4. やること（12）

| # | 触るファイル | 何をするか | §6 の番号 |
|---|---|---|---|
| **A** | `scripts/priority_rebuild/gen_audit_request.py` | **13要素に分ける形（要素の番号を指定する道）を外し、`--frozen <凍結ファイル>` の道にする。**凍結ファイルには CC が書ける4節だけを置き、事実データ（ファイルのハッシュ値・行数・件数・承認の状態）はプログラムが実物から埋める。`--selftest` の Q6 は「凍結ファイルから依頼書を作れるか」に、Q11 は「存在しない節を指したら問題として返すか」に作り替える | 121・92・141 |
| **B** | `.claude/tools/pre_audit_check.py` | **`CHECKS` に2行 足す**＝`gen_audit_request.py --selftest` と `engine_tuner_gen.py --selftest-extra-gate`。あわせて `--selftest` に「その2つが `CHECKS` に在るか」を見る枝を足す（一覧から消したら番人が落ちる） | 145・141 |
| **C** | `.claude/breaks/b06_tool_changed.sh` | **測る道を `--diff` から本物の照合に変える**＝`python3 verify_design_contract.py <設計書>`（`check` の道＝`check_impl_functions` を通る）にする。これで「照合の道具を1文字 変えると止まる」を本当に測る | 131 |
| **D** | `.claude/tools/run_breaks.py` ＋ `.claude/hooks/require_acceptance_before_impl.sh` | **`--measure-only` を作る**＝凍結の照合を先に行い、壊すプログラムを走らせて終了コードを画面に出すだけ。**`<iter>.breaks.json` にも凍結の記録にも1バイトも書かない。**あわせて土台ゲートの通す判定に「`run_breaks.py` は `--measure-only` が在るときだけ通す」を足す（hook の直しは承認不要） | 150 |
| **E** | 壊すプログラム2本（b43・b44） | **承認スクリプトの直しを守る条件を作る**＝b43（空の `impl_functions` を凍結しようとすると止まる枝を消すと、承認が通ってしまう）と b44（承認のときに壊し方の記録を設計書へ書き込む処理を消すと、記録が残らない）。**承認スクリプト自体は直さない＝足すのは壊すプログラムと完成の条件** | 146 |
| **F** | `scripts/priority_rebuild/verify_design_contract.py` | **`--write` の SPEC に「関数の名前 → 定義の行」の表を足す**＝設計書は行番号を手で写さず、この表を引く | 93 |
| **G** | `scripts/priority_rebuild/verify_design_contract.py` ＋ `.claude/hooks/approve_impl.sh` | **照合A(双方向) に「承認の時点で既に汚れていた .py」の基準を持たせる**＝承認のときに `git status --porcelain` の .py の一覧を `<iter>.dirty.json` に凍結し、照合A(双方向) はその一覧に在るファイルを数えない | 138 |
| **I** | `.claude/hooks/require_source_read_before_acceptance.py` | **囲みの中を読み飛ばす**＝`_line_values`（`TARGET:`・`NEW_FILE:`・`MODEL:` を読む所）と `claimed_files` の2か所に入れる | 113 |
| **J** | `.claude/tools/gen_regime_kb.py` | **他のプログラムが持つ囲みを、壊さず・数えない**＝①`--write` のとき、いまの文書に在る `BANS_COUNT` と `COUNTS` の囲みの中身を、そのまま新しい本文へ差し戻す ②指紋を出すときは、その囲みの中身を決まった文字に置き換えてから数える（＝`gen_materials.py` が中を書き替えても指紋が変わらない） | 154 |
| **K** | `.claude/ratchet/regime_laws.json` | **R7 の引用の行番号を 2464 → 2568 に直す**（J を入れた後に `gen_regime_kb.py --write` を走らせる） | 155 |
| **L** | `scripts/priority_rebuild/engine_tuner_gen.py` | **`_check_extra_gate` を `_selftest_extra_gate` に改名し、静的検査の⑤の判定を「囲っている関数の名前に selftest が含まれるか」に変える**（いまは名前がちょうど `selftest` のときだけ許す）。★検査を緩める側ではない＝「自己テストの中でだけ見本を使う」という決まりはそのまま | 149 |
| **M** | `.claude/breaks/b41〜b50` | **壊すプログラム10本を新しく作る**（手本＝b36・b37・lib.sh）。それぞれ、上の直しの1本を消して、対応する検査が落ちることを測る。測る相手は 120秒 に収まる口だけにする | 全件 |
| **N** | `.claude/hooks/require_acceptance_before_impl.sh` ＋ `.claude/breaks/b51_dirty_json_unguarded.sh` | **★2026-09-08 に足した（監査 cp28 の C-1・Critical）。**G が新しく作った「汚れの記録」（`<設計書の名前>.dirty.json`）が、土台ゲートの守りに入っていなかった。**兄弟2本（`.breaks.json`・`.frozen.json`）は止まるのに、この1本だけ Write でも Bash でも書けた。**書けば、照合A(双方向) が読む「数えない一覧」に任意の .py を足せる＝設計書に書いていない .py を触っても照合が落ちない。**直す中身**＝①Bash 側の一覧（`BASE_SUFFIX`）に `'.dirty.json'` を足す ②Write 側の場合分け（`case`）に `*.dirty.json` を足す ③画面に出す文言に1行 足す ④壊すプログラム b51 を作る（②の1行を消すと、Write が素通りすることを測る）。**★同じ型は 2026-09-04（監査 cp17 の G-1）で一度 塞いである。**3本目を作りながら、その型を当てなかった | 監査 cp28 の C-1 |

**工程表（止まっている度合いが強いものから）**

| 順 | 何を | 理由 |
|---|---|---|
| 1 | **I（囲みを読み飛ばす）と D の hook 側** | この2つが直らないと、以後の設計書を書くたびに同じ所で止まる |
| 2 | **G（並走の基準）** | 並走中はどの設計書でも照合が止まるので、実装の前に要る |
| 3 | **J・K（囲みの持ち主と行番号）** | 文書を作り直すたびに数字が壊れるのを止める |
| 4 | **L（静的検査の赤）** | 1行の改名。生成器の印を取り直す（G2 → H2） |
| 5 | **B（監査の前の一覧）・C（b06 の道）・D の道具側** | 測りの配管 |
| 6 | **E（承認の直しを守る条件）・F（行番号の表）** | |
| 7 | **A（依頼書の作り直し）** | いちばん大きい。ここまでで時間が尽きたら「未着手」で残す |
| 8 | M（壊すプログラム10本）→ 2回目の承認 → 記録 → 監査 | |

## 5. ★疑似シミュ由来の固定値ゼロ宣言

疑似シミュ（probe）から出た数字を、1つも固定値にしていません。

- **(a)** この工事で新しく決める数字は 0個です。閾値・期間・パラメータを1つも決めていません。K の 2568 は、実物のコードの行番号を機械で読んだ値です。
- **(b)** probe の数値を設計の固定値に焼いていません。probe を1本も走らせていません。
- **(c)** 採否は probe でなく、検査の終了コードと、壊すプログラムの終了コードで決めます。

## 6. 変更の単位（H16）

**1レバーではありません。13件をまとめた工事です。**まこさんの指示（逐語 2026-09-07）＝「「承認と監査の仕組み」の7件を1本の設計書でまとめて直す →OK」「他にも作業に支障がでているものがあれば、まとめて直して」。

**★H16（1ターン1変更）との関係を、正直に書きます。**この工事は H16 の字面には合いません。合わせるために、**1件ずつ独立に測れる形にしました**＝完成の条件の行を11本に分け、それぞれに別の壊すプログラムを付けます。1本が止まっても、ほかの行の判定は変わりません。

**過去に破棄した失敗の再演ではありません。**乱数は1つも増えません。売買のロジック・審判（score.py・eval_engine）・発注には触れません。

**入っていないもの（正直に）**＝①134（観察の検査5）②80（fast-mode で止まっている35本）③84・107・125（まこさんが直さないと決めた）④140（監査が直している）。

## 7. 塞げないもの

| # | 問い | 塞げないこと |
|---|---|---|
| **監査 Q5 の1** | 直した後、承認と監査の配管は本当に守れているか | **全部は測れません。**測れるのは、11本の壊すプログラムが名指しした通り道だけです。**監査が別に作る通り道は、今回も素通りする見込みがあります**（cp16:2／cp17:10／cp18:17／cp19:15＝減っていない・`lessons_active.md` の L-586） |
| **監査 Q5 の2** | 凍結の記録や印が正しいか | **手で偽造されたら見抜けません**（H2・G2 と同じ限界）。この工事は偽造の検出を足しません |
| **監査 Q5 の3** | 直しを打ち忘れたら | **完成の条件の行が「未着手」のまま残ります。**承認のプログラムは、条件のコマンドを実際に走らせて終了コードを見るので、打ち忘れは「済」になりません |
| **監査 Q5 の4** | 直す対象の道具自身を書き換えられたら | **無効にできます。**`.claude/tools/*.py` と `scripts/priority_rebuild/*.py` は承認ゲートの相手なので承認は要りますが、hook（`.claude/hooks/*.sh`・`.py`）は まこさんの決定（2026-09-06）で承認が要りません。**＝hook 側の直し（D の hook 側・I）は、CC が後からいつでも戻せます。**git の差分には必ず出ます |
| **監査 Q5 の5** | G（並走の基準）で、照合が甘くならないか | **甘くなります。**承認の時点で既に汚れていた .py は、以後 数えません。**＝承認の前にわざと .py を汚しておけば、その1本は照合A(双方向) の外に出ます。**★ただし `scripts/priority_rebuild/*.py` と `.claude/tools/*.py` は承認の前に書けない（承認ゲート）ので、この道が使えるのは hook の .py だけです。それも まこさんの決定（hook は承認不要）から来るもので、この工事が新しく開ける穴ではありません |
| **補1** | J（囲みの持ち主）で、`gen_regime_kb.py` の指紋の守りが弱くなるか | **弱くなります。**囲みの中身を数えないので、その中だけは手で書き換えても `gen_regime_kb.py --verify` は気づきません。**代わりに `gen_materials.py --verify` が同じ囲みを見ています**（実測＝`python3 scripts/priority_rebuild/gen_materials.py --verify` が「✅ 一致（手で書き換えられていない）」）。＝守るのは持ち主の側という形にします |
| **補3** | **★2026-09-08 に足した（監査 cp28 の C-3）。**触る関数の一覧を埋めるまで、この設計書で設計↔実装の照合は効いていたか | **効いていませんでした。**承認の 2026-09-07 の時点で一覧は空で、凍結された中身も0件でした。**＝関数の欠落・余分・組み合わせを見る守りは、この工事に対して空振りでした。**監査の逐語＝「理由を1行 書けば、設計↔実装の照合を丸ごと無効にできます」。**★2026-09-08 に一覧を埋めた**（`gen_impl_functions.py` の出力・5ファイル・CC は1文字も手で書いていない）。**まだ塞げていないこと**＝「理由を1行 書けば空で通る」という道そのものは残っています。閉じるには「触った .py に関数の変更が在るのに一覧が空なら承認が止まる」形にします＝道具と承認の直し（`next_step.md` の §6 の158番） |
| **補4** | **★2026-09-08 に足した（監査 cp28 の M-2）。**「この道が使えるのは hook の .py だけ」は正しかったか | **正しくありませんでした。**汚れの記録の7本のうち **6本が hook 以外**でした（道具3本・生成器や照合の道具3本）。**理由**＝この設計書の承認は2回目以降が本番で、1回目で書く権利をもらって `.py` を直し、そのうえで2回目を打ちます。**そのとき、直した `.py` は全部 汚れています。**＝「承認の前には書けない」は1回目の承認にしか当てはまりません。**結果として、この工事で触った `.py` は7本とも照合A(双方向) の外に出ました。**監査の逐語＝「塞げないことを書く節ほど、実物で数えてから書いてください」 |
| **補2** | A（依頼書の作り直し）で、CC の自由記述が本当に減るか | **減りますが、0にはなりません。**凍結ファイルの4節は CC が書きます。まこさん指示 2026-08-25 の形（事実データは機械が埋める・CC の自由記述の欄を作らない）に近づけますが、監査への問いの文面は CC が書いて凍結する形のままです |

## 8. §4.6 ハード制約の照合

**H1〜H16 の16件を1件ずつ照らします（該当2件・非該当14件）。**触るのは、承認・監査・照合の配管と、文書を作るプログラムです。売買のロジック・審判（score.py・eval_engine）・発注には触りません。`acceptance_checklist.md` の【群2】（同ファイル19行の逐語「売買のロジックか審判を触るときだけ、1件ずつ照合する。触らないときは「まとめて非該当（理由）」の1行でよい」・18件）は、同じ理由でまとめて非該当です。

| H | 何の決まりか | この工事 | 理由 |
|---|---|---|---|
| H1 | ポジション合計 0.12 BTC | 非該当 | 売買を1件も回さない |
| **H2** | leak なし | **該当** | `engine_tuner_gen.py`（L）と `verify_design_contract.py`（F・G）は H2 の印の対象。直したら G2 → H2 の順で印を取り直す。未来を見る計算は1つも足さない |
| H3 | net 判定（gross 禁止） | 非該当 | net を計算しない |
| H4 | コスト確定値 | 非該当 | 手数料・funding・slippage に触れない |
| H5 | 約定モデル | 非該当 | 約定を模さない |
| H6 | 価格非依存 | 非該当 | 価格の列を1本も作らない |
| H7 | 足の標準＝5m | 非該当 | 時間足に触れない |
| H8 | 期間分割 | 非該当 | 期間の境界に触れない。走らせるのは検査だけ |
| H9 | 最小注文 | 非該当 | 注文を出さない |
| H10 | サイズ固定値扱い禁止 | 非該当 | サイズに触れない |
| H11 | 合格ライン／地面 | 非該当 | 合否を判定しない |
| H12 | 異常値 STOP | 非該当 | 勝率・月 net を出さない |
| H13 | judge 固定 | 非該当 | score.py・eval_engine に触れない |
| H14 | 発注フラグ | 非該当 | 発注のコードに触れない |
| H15 | Entry のボラ逃げ禁止 | 非該当 | Entry のスコアもラベルも作らない |
| **H16** | 1変更・過去失敗の不再演 | **該当** | 上の §6 に正直に書いた |

## 9. 完成の条件

**★状態は全部「未着手」です。**「済」にするのは機械です（恒久の決まり64番）。

**★触る関数の一覧（`impl_functions`）は、実装の後に確定させる。**いまは空です。理由＝どの関数に行を足すかは、実装しながら決まる所が残っています（とくに A の作り直しと G の基準の持たせ方）。**実装の後に、実物の `git diff -U0` の塊の見出しから「触った関数だけ」を手で列挙して埋めます**（全関数の写しにしない＝`next_step.md` §6 の132番の決まり）。

**★コマンドに数秒で走る口を選んだ理由**＝`engine_tuner_gen.py --selftest` は約6分半かかり、承認のときの打ち切り（120秒）を超えます。しかも既知の ❌（T24②・T26・T30＝M2-E で直す）で終了コードが 0 ではないので、「壊すと落ちる」の測りに使えません。だから、枝だけを走らせる口（`--lint-provenance`・`--selftest-extra-gate`）を測ります。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | AUDIT-1＝監査の依頼書を作るプログラムの自己テストが全部 通る（直す前は -4/11・Q6 は 0/13） | `python3 scripts/priority_rebuild/gen_audit_request.py --selftest` | 実経路 | 凍結ファイルから節を1つ消すと、依頼書を作れずに落ちる | `b41_req_frozen_section_gone.sh` | 対象 | **✅済**＝壊すと rc=1／条件のコマンドも rc=0（承認のときに機械が2つとも測った） |
| 2 | 監査の前の検査の一覧に、依頼書の自己テストと別枠3種の審査のテストが入っている（直す前は0件） | `python3 ../../.claude/tools/pre_audit_check.py --selftest` | 実経路 | 一覧からその2行を消すと、番人が落ちる | `b42_pre_audit_list_gone.sh` | 終了コードが0でない | **✅済**＝壊すと rc=1／条件のコマンドも rc=0（承認のときに機械が2つとも測った） |
| 3 | 承認のときに空の impl_functions を凍結しない判定（承認スクリプトが呼ぶ `contract_for_freeze`）が、番人で確かめられる | `python3 scripts/priority_rebuild/verify_design_contract.py --self-test` | 実経路 | その判定から「理由の無い空」を止める2行を消すと、番人 N17 が落ちる | `b43_approve_empty_freeze_gone.sh` | 終了コードが0でない | **✅済**＝壊すと rc=1／条件のコマンドも rc=0（承認のときに機械が2つとも測った） |
| 4 | 承認の「済」の材料になる記録（壊すプログラムの終了コード）を、機械が書く | `python3 ../../.claude/tools/run_breaks.py --selftest` | 実経路 | 記録を書く処理（`write_record`）の中身を消すと、番人 T8 が落ちる | `b44_approve_record_write_gone.sh` | 終了コードが0でない | **✅済**＝壊すと rc=1／条件のコマンドも rc=0（承認のときに機械が2つとも測った） |
| 5 | 壊すプログラムを、書き込みなしで測り直す口が CC の Bash から走る | `python3 ../../.claude/tools/run_breaks.py --measure-only --iter approval-audit-plumbing-20260907` | 実経路 | 土台ゲートの通す判定から、その旗の条件を消すと止まる | `b45_measure_only_gone.sh` | 終了コードが0でない | **✅済**＝壊すと rc=2／条件のコマンドも rc=0（承認のときに機械が2つとも測った） |
| 6 | AUDIT-2＝照合の道具が承認のときのままなら、本物の照合が通る（直す前は b06 が rc=0＝測れていない） | `python3 scripts/priority_rebuild/verify_design_contract.py .claude/state/acceptance.md` | 実経路 | 照合の道具の末尾に1行 足すと、道具の指紋が承認のときと合わずに照合が rc≠0 になる | `b06_tool_changed.sh` | 対象 | **✅済**＝壊すと rc=1／条件のコマンドも rc=0（承認のときに機械が2つとも測った） |
| 7 | 照合の道具が書き出す SPEC に「関数の名前 → 定義の行」が入っている | `python3 scripts/priority_rebuild/verify_design_contract.py --self-test` | 実経路 | その表を書き出す処理を消すと、番人が落ちる | `b46_spec_lineno_gone.sh` | 終了コードが0でない | **✅済**＝壊すと rc=1／条件のコマンドも rc=0（承認のときに機械が2つとも測った） |
| 8 | AUDIT-3＝承認の時点で既に汚れていた .py を、照合A(双方向) が「設計書に書いていないファイルを触った」に数えない | `python3 scripts/priority_rebuild/verify_design_contract.py --self-test` | 実経路 | その一覧を数えない2行を消すと、番人 N18 が落ちる（N19 は通ったまま＝緩めていない） | `b47_dirty_baseline_gone.sh` | 対象 | **✅済**＝壊すと rc=1／条件のコマンドも rc=0（承認のときに機械が2つとも測った） |
| 9 | 設計書の囲みの中に書いた見本の行を、宣言として読まない | `python3 ../../.claude/hooks/require_source_read_before_acceptance.py --selftest` | 実経路 | 囲みを読み飛ばす処理を消すと、番人が落ちる | `b48_fence_skip_gone.sh` | 終了コードが0でない | **✅済**＝壊すと rc=1／条件のコマンドも rc=0（承認のときに機械が2つとも測った） |
| 10 | AUDIT-4＝文書を作る2つのプログラムの検査が、同時に両方とも通る（直す前は片方が3件 ❌） | `python3 ../../.claude/tools/gen_regime_kb.py --verify` | 実経路 | 他のプログラムの囲みを差し戻す処理を消すと、片方の検査が落ちる | `b49_foreign_block_gone.sh` | 対象 | **✅済**＝壊すと rc=1／条件のコマンドも rc=0（承認のときに機械が2つとも測った） |
| 11 | 生成器の静的検査が0件になる（直す前は「見本の関数」1件） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --lint-provenance` | 実経路 | 関数の名前を元に戻すと、静的検査が1件に戻る | `b50_fixture_name_gone.sh` | 終了コードが0でない | **✅済**＝壊すと rc=1／条件のコマンドも rc=0（承認のときに機械が2つとも測った） |
| 12 | AUDIT-5＝汚れの記録（`<設計書の名前>.dirty.json`）が、土台ゲートの守りに入っている（直す前は Write でも Bash でも書けた） | `python3 ../../.claude/tools/run_breaks.py --measure-only --iter approval-audit-plumbing-20260907` | 実経路 | Write 側の場合分けから `*.dirty.json` を消すと、その形のファイルへの Write が素通りする | `b51_dirty_json_unguarded.sh` | 対象 | **未着手** |

<!-- ACCEPT_TABLE_END -->

**自己検査（完成の条件の外で、実装の後に必ず走らせて記録するもの）**＝①`engine_tuner_gen.py --selftest`（約6分半・❌ が既知の件のまま増えない）②`engine_tuner_exec.py --identity`（S2・直す前と後で結果が同じか確かめる走行・md5 不変）③`gen_signal_families.py --verify`（G2）と `leak_causality_diag.py`（H2）④`gen_materials.py --verify`（J の後も通ること）⑤直した hook の文法を `bash -n` で確かめる。

## 10. DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/gen_audit_request.py",
  "impl_functions": {
    ".claude/tools/gen_regime_kb.py": [
      "<モジュール直下>", "_begin", "_begin_re", "_end", "_esc", "_foreign_span", "_h",
      "_kakeru", "_kinds", "_pass_json", "apply_marks", "build", "build_body", "build_flow",
      "build_laws", "build_premise", "build_todo", "check_citations", "coverage",
      "keep_foreign", "main", "marks_checks", "marks_now", "mask_foreign", "selftest",
      "selftest_marks", "verify", "verify_one", "write", "write_one"
    ],
    ".claude/tools/pre_audit_check.py": [
      "<モジュール直下>", "_input_shape_miss", "_run", "approve_problem", "check_design",
      "code_fingerprint", "design_hooks", "main", "run", "selftest", "verify", "verify_problems"
    ],
    ".claude/tools/run_breaks.py": [
      "<モジュール直下>", "break_scripts", "check_frozen", "freeze_breaks", "main",
      "parse_table", "run_one", "selftest", "sha", "write_record"
    ],
    "scripts/priority_rebuild/gen_audit_request.py": [
      "<モジュール直下>", "_facts", "_headline", "_line_of", "_meta", "_reading", "_sha",
      "_table_rows", "_tmp_md", "approval_matches", "build_request", "copy_all_laws",
      "copy_measure", "copy_template_section", "copy_todo_rows", "frozen_title",
      "load_frozen_question", "main", "print_source", "section_refs_missing", "selftest",
      "template_heads"
    ],
    "scripts/priority_rebuild/verify_design_contract.py": [
      "<モジュール直下>", "_fence_body", "_next_fence_json", "_resolve_impl", "check",
      "check_approval", "check_impl_functions", "check_must_use", "check_spec_lists",
      "contract_for_freeze", "counts_as_touched", "diff_spec", "dirty_baseline",
      "extract_block", "extract_contract", "extract_requirements", "format_req_map",
      "frozen_impl_functions", "functions_ast", "head_source", "load_spec_lists",
      "must_use_from_source", "names_in_function", "outside_fence_lines", "probe_spec_lists",
      "req_map", "requirements_index", "resolve_spec_list", "rhs_names_for_symbol",
      "scan_contracts", "self_test", "spec_from_design", "spec_from_impl",
      "touched_functions", "write_actual"
    ]
  },
  "must_use": {
    "section_refs_missing": ["extra_dirs"],
    "selftest": ["_tmp_md"],
    "write_one": ["keep_foreign", "mask_foreign"],
    "verify_one": ["mask_foreign"],
    "counts_as_touched": ["baseline"],
    "spec_from_impl": ["def_lines"],
    "write_record": ["json"],
    "main": ["write_record"]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は値の一覧を持たない（直すのは配管の判定で、閾値も期間も1つも決めない）",
  "generated_from": {
    "impl_functions": "gen_impl_functions.py の出力をそのまま（2026-09-08・監査 cp28 の C-3 で埋めた）。CC は1文字も手で書いていない・関数を足しも消しもしていない。★出るのは『いまファイルに在る全関数』なので、この工事で触っていない関数も入る＝承認の画面に ⚠️ が出るのが正しい状態（まこさん指定 2026-09-03）。★engine_tuner_gen.py は入れていない＝この工事での変更は関数1つの名前を変えただけで、そのファイルを入れると SPEC（作る関数と、その関数が呼ぶもの・定数・コマンドの旗の一覧）が必須になり、この工事の範囲を超えるため",
    "must_use": "★手で書いた（機械で照らせないに数える）。正本の json から作る道（must_use_from）は、この工事に外から取る一覧が無いので使えない。★選び方＝この工事で実際に直した所だけを要求する＝その直しを消すと照合が落ちる形。8件の中身＝section_refs_missing が extra_dirs を使う（番人だけが探す場所を足せる・Q11 の直し）／selftest が _tmp_md を使う（見本を一時のファイルにした・Q11 の直し）／write_one が keep_foreign と mask_foreign を使う（他のプログラムの囲みを差し戻す・指紋から外す＝J）／verify_one が mask_foreign を使う（同じ考え方で照らす＝J）／counts_as_touched が baseline を使う（承認のときに汚れていた .py を数えない＝G）／spec_from_impl が def_lines を使う（関数の定義の行を書き出す＝F）／write_record が json を使う（壊し方の記録を本当に書く＝E）／main が write_record を使う（呼び出しを消させない＝E）",
    "spec_lists": "空。外から取る一覧が無い"
  }
}
```

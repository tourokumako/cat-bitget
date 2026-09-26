# session_worklog_20260926.md — 120回目の続き（2026-09-25 の §6 の続き・日付が変わったので新しいファイル）

## §1 commit と、47番の説明（2026-09-26・120回目）

### 1-1 commit（まこさん OK「コミットはOK」）

- commit＝`d85942e`（26件）。中身＝コード3本（engine_tuner_exec.py・engine_tuner_gen.py・streak_scope_diag.py）／壊すプログラム3本（b99・b100・b103）／ratchet の元データ acceptance_src.json／承認の控え m2e-bundle1-20260925 の一式（.md・.01.md・.01.diff.txt・.01.sha.txt・.breaks.json・.dirty.json・.frozen.json）／承認のプログラムが書いた breaks_frozen.json・impl_functions_frozen.json／材料の文書 materials.md・materials.json・engine_tuner_milestones.md・engine_tuner_milestones2.md／decisions.md／worklog 20260925／next_step の3ファイル。
- 登録の仕方＝追跡中のファイルは `git add -u <フォルダ>`（engine_tuner の名前をコマンドに書くと設計↔実装ゲートが止めるため＝§6 の156番）。新しいファイルは名前で add。

### 1-2 47番の説明を まこさんに出した

- まこさんの問い（逐語）＝「47番の位置（束2 の後・M2-E-6 の前）で、やることリストに足してよいか。→どういうこと？わかりやすく説明してほしい」。
- 説明の中身＝チャットの返信（やることリストの正本 m2_todo.json に新しい番号を足す位置の話）。

### 1-3 まこさん「この案でOK」→ M2-E-4e を足した（2026-09-26）

- m2_todo.json に M2-E-4e を1件足した（M2-E-4c の後・M2-E-6 の前）。依存の表に M2-E-4e の行を足し、M2-E-6 の依存を「M2-E-3〜M2-E-5 と M2-E-4e が要る」にした。まとまりの分け方の文にも 4e を入れた。
- `gen_regime_kb.py --write todo`＝§3（やることリスト）を engine_tuner_milestones2.md に書いた（本文 1555行・hash=9f4b1339d0d73324）。
- `gen_regime_kb.py --verify all`＝§2・§3・§2.2-0・§11・§12 は ✅。★❌1件＝「R7: 引用の行の前後5行に `wpct_arr` が無い」（file:line 引用の実在検査＝9件のうち ずれ 1件）。`--selftest`＝14/15（落ちたのは T11「引用の実在検査 いまの引用に ❌ が在る」＝同じ件）。
- 原因＝束1 の実装で engine_tuner_exec.py に行が足され、`wpct_arr` の行が動いた。いまは `engine_tuner_exec.py:2669`（sed -n '2664,2672p' で開いた）。古い行番号（2626）の所は、いまは出口の発火条件の評価の中（sed -n '2621,2631p' で開いた）。古い行番号を書いているのは regime_laws.json の758行（R7 の注意）と regime_detection_kb.md の868行（R7 の説明）。★束1 の設計書の影響範囲（4-13）にも、監査 CP39 の B3-c にも無かった影響。
- ★法則ファイルの文字を直す話なので、直す前に まこさんに出した（この工事は「法則ファイルは1文字も触らない」と書いていた）。

### 1-4 まこさん「直してよい」→ R7 のメモの行番号を直した（2026-09-26）

- regime_laws.json の R7 の注意（758行）の `engine_tuner_exec.py:2626` を `:2669` に直した（Edit・行番号の数字だけ・法則の判定の中身は変えていない）。
- regime_detection_kb.md の868行も同じに直した。★この行は `gen_regime_kb.py` が法則ファイルから作る §11 の中だった（道具の "laws": KB）＝手で直す相手ではなかった。`--write laws` で作り直した結果の指紋（a7191b68…）は、手で直した版と同じ。
- `gen_regime_kb.py --verify all`＝全部 ✅・file:line 引用の実在検査＝9件のうち ずれ 0件。
- 法則ファイルを読む道具の自己テスト7本（hook が求めた）＝gen_regime_kb 15/15・gen_composition_rules 全部 pass・gen_indicator_switch 11/11・engine_tuner_exec 全部 pass・leak_causality_diag 全部 pass・gen_acceptance 9/9・engine_tuner_gen 全部 pass。
- H2（`leak_causality_diag.py`）＝注記なし未来参照 0件・打ち切り再現テストの食い違い 0件・印 892e9bac…。`tidy_next_step.py --write` で next_step の印の欄を書き直した。G2 は法則ファイルが印の対象に無いので取り直していない（g2_pass.json に regime_laws.json の名前が0件）。

### 1-5 commit と、実装の監査 CP43 の依頼書の元データ（2026-09-26）

- commit＝`84a6341`（7件＝next_step の2ファイル・この worklog・KB・milestones2・m2_todo.json・regime_laws.json）。まこさん OK「コミットOK」。h2_pass.json は git の外なので入れていない。
- 依頼書の元データ＝`SDK/.claude/audits/cp43_work/cp43_src.md`。手本＝CP42 の元データ（`cp42_work/cp42_src.md`・実装の監査の型）。問い2つ（実装が設計書の決めた動きをしているか／設計書と実装の食い違いの全件）・観点 A0〜A5・B1〜B3・C1・外部検索なし・自己申告6件・事実データ10行・着手前必読14件。
- `gen_audit_docs.py request` の1回目＝「監査に出す前のチェック（pre_audit_check.py --verify）が通っていない」で書かなかった。`pre_audit_check.py --run` を裏で走らせた（前回の記録＝leak_causality_diag 約340秒・observe_diag の自己テスト 約120秒＝合計で10分を超える見込みのため）。

### 1-6 監査の前のチェックと、CP43 の依頼書（2026-09-26）

- `pre_audit_check.py --run`＝全部 rc=0（leak_causality_diag 303.9秒・observe_diag の自己テスト 110.4秒・gen_materials の自己テスト 68.5秒・gen_signal_families --verify 25.1秒 ほか）・記録 pre_audit_check.json（指紋 22b50027…）。★「まこさんの承認を待つもの 2件」＝型の表と出口の表の `--write`・`--approve`（この道具が打たないと決めている手順）。同じチェックの `gen_signal_families.py --verify`・`gen_exit_families.py --verify` が rc=0＝表は正本と合っている＝いまは作り直しが要らない。
- `pre_audit_check.py --verify`＝「監査に出せます（チェックの1枚が新しく、全部 rc=0）」。
- `gen_audit_docs.py request`（2回目）＝依頼書 `SDK/.claude/audits/inputs/2026-09-26_m2e_bundle1_impl_cp43_audit_request.md` を書いた（問い10件・事実データ1件・外部検索1件・自己申告6件）。
- チェックが H2 の検査を走らせ直して印を書き直したので、`tidy_next_step.py --write` で next_step の印の欄を書き直した。0-1 の「いまここ」と「次の一手」を、依頼書を作った状態（まこさんのチェック待ち）に書き替えた（--verify 7つ ✅・自己テスト 19/19）。

### 1-7 教訓と commit（まこさん「コミットOK」「教訓も書いて」・2026-09-26）

- 教訓＝lessons_active.md に L-619（道具が何を走らせるかを、作りを確かめずに書かない＝承認のプログラムは壊すプログラムの無い行のコマンドを走らせない）と L-620（コードに行を足す工事では、ファイル名:行番号の引用が古くなる＝影響範囲に入れ、実装の直後に引用の実在検査を走らせる）を足した。
- commit＝依頼書・元データ・この worklog・next_step・教訓（次の commit）。

## §2 監査 CP43 の結果と、まこさんの決定（2026-09-26・121回目）

### 2-1 監査 CP43 の結果（別のセッションで監査が終わっていた）

- 結果ファイル＝`SDK/.claude/audits/2026-09-26_m2e_bundle1_impl_cp43_audit_report.md`（git の外・まだ commit していない）。
- 結論＝GO。Critical 0件・Major 9件・Minor 19件・Process 2件＝修正の指示30件。
- 状態の内訳＝確定23件・案が複数2件（修正5・6）・未決5件（修正8・9・26・27・28）。
- 監査の見立て＝コードと設計書の食い違いは0件（28件の diff・壊すプログラム3本の sha256・触った関数）。食い違いは全部 文書の側（設計書の元データ・やることリスト・法則ファイル）。
- 範囲外の指摘（B3-c）＝承認の前の検査 B1 は、この設計書では満たせない。壊すプログラム4本で約16分（b77・b99 が各 約7分半）・前面の上限10分・裏で走らせると結果の文字が検査の見る所に残らない・run_breaks.py に1本ずつ測る口が無い（536〜565行）。

### 2-2 まこさんの決定（逐語）

- 直す範囲＝「１．すべて修正する」＝30件を全部。
- 案が複数の修正＝「２，A」＝修正5・修正6 とも案A（私がそう読んだことを返信の1行目に書いた）。
- 未決の5件＝「5件とも「確定」→修正するということだよね？」＝私の説明（確定＝道具が書き込む）への確認。私は「確定」として書き込むと読み、返信の1行目に書いた。
- 範囲外＝「範囲外の話もこのSessionで修正してほしい」＝run_breaks.py に、壊すプログラムを1本ずつ測る口を足す。

### 2-3 順番（ToDo の意図）

- 道具の直しを先にする＝⑥の承認2回の前に、壊すプログラムを私が1本ずつ先に測れるようにするため（まこさん指示 2026-09-21「何度も同じ承認をさせることをしないでほしい」）。
- 代わりに、元データの置き場（ratchet の acceptance_src.json）の入れ替えで まこさんに cp を2回お願いする。理由＝CP43 の「確定」の修正がその元データに当たっていないうちは、hook 12 が私の Write を止める（enforce_audit_fix.py＝直す相手の一覧に在るファイル）。Bash で入れ替えると hook 12 を迂回することになるので、しない。

### 2-4 読むもの宣言への OK と、読んで分かったこと（2026-09-26）

- まこさんの OK（逐語）＝「OK」。宣言（設計書 breaks-measure-one-20260926・15件）に写し、貼った証拠のファイルを作り直した（0497794a…）。15件を全部 Read tool で開いた。
- 分かったこと。
  - 検査 B1（require_design_check_before_approval.py の 304〜306行）は、コマンドに「run_breaks.py」と「--measure-only」が在り、出力に「期待どおり…名前」が在る記録を、壊すプログラムごとに探す＝1本ずつ測っても数えられる。
  - run_breaks.py の測るだけの口の出力の行＝「✅ 期待どおり #番号 名前 rc=…（期待 …）」（740行）。B1 の正規表現に当たる形。
  - 土台ゲート（require_acceptance_before_impl.sh の 267〜271行）は、先頭の .py が run_breaks.py で、--measure-only が在り、書き込みの旗が無ければ通す。足す旗の値（名前）はこの条件を変えない＝hook を直さずに通る。
  - 承認のプログラム（approve_impl.sh の 401行）は `--design --iter` で表の全部を走らせる。--only を渡さないので動きは変わらない。
  - run_breaks.py を相手にする壊すプログラムの探す文字（`--count-targets` の出力）＝b01（parse_table の定義）・b44（write_record）・b52（expect_of）・b90（match_of）・b95（lint_expect）。触る予定の main・SELF_TESTS・selftest の行を探すものは0本（grep で8語を探して0件）。
  - 当てる道具 apply_audit_fix.py の書かない相手（NEVER_WRITE・67〜73行）に `.claude/tools/` が在る＝この工事は実装の指示の欄を使わず、承認の後に私が Edit で書く。
  - 束1 の元データの控え `.claude/state/acceptance_src_m2e-bundle1-20260925_cp39.json` は、ratchet の acceptance_src.json と同じ sha256（f9b98764…）＝新しい控えは要らない。戻すときはこの控えを cp する。

### 2-5 道具の直しの設計書の元データを作った（2026-09-26）

- `.claude/state/acceptance_src_breaks-measure-one-20260926.json` を書いた（iter＝breaks-measure-one-20260926・TARGET＝run_breaks.py の1本・完成の条件4行＝全部 壊すプログラム「—」・手本＝breaks-target-count-20260917 の元データ）。
- 確かめ＝jq で読めた（完成の条件 4行）。「なぜ作るか」の読み方に数字 0件（gen_acceptance.py の fail-closed）。「なぜ作るか」のコマンド6本を1本ずつ走らせ、全部 実物の行に当たった。
- 次＝まこさんに cp をお願いする（hook 12 が ratchet の acceptance_src.json への Write を止めるため）。

### 2-6 cp の1回目のあと、設計書を作る道具が止まった＝私の元データの抜け（2026-09-26）

- まこさん「コマンド打ったよ」。sha256 が控えと同じ（d2ac5bbd…）ことを確かめた。
- `gen_acceptance.py --write`＝「書いていない項目に、理由が在りません（fail-closed 8・9）＝4-20」で止まった。設計書は書かれていない（あとに出た承認の前の検査の不足9件は、書き替わる前の束1 の設計書を見たもの）。
- **原因＝私の元データの抜け。**§4 の項目の正本 `design_section_map.json` に 4-20（実装の指示・段＝条件）が在る。手本の breaks-target-count-20260917（2026-09-17）の後に足された項目で、手本には無かった。私は手本の鍵をそのまま写し、正本の項目の一覧を開かずに元データを書いた。束1 の元データは 4-20 を持たないが「実装の指示」が在るので通っていた（gen_acceptance.py の 714行）。
- **直し**＝控えの元データに `"4-20": {"非該当": …}` を足した（理由＝直す相手は当てる道具の NEVER_WRITE の `.claude/tools/` に在る）。§4 の項目 21件がそろったことを jq で数えた。道具の止まり所（fail-closed 1〜10・「なぜ作るか」の読むだけのコマンドの検査・読み方の数字）を全部 読み、ほかに当たるものが無いことを確かめた。書く前の禁止語の一覧（list_banned_words.py acceptance）と元データを照らし、0件。
- ★この抜けのために、まこさんに cp を もう1回（2回目）お願いすることになった。

### 2-7 cp の2回目のあと、設計書はできたが、承認の前の検査で不足が出た（2026-09-26）

- まこさん「再度、コマンド打ったよ」。sha256 が控えと同じ（dfa58271…）。`gen_acceptance.py --write`＝設計書 637行・囲み 12個・法則の件数 51件／51行。
- 書いた直後の検査（show_design_check_after_write）＝不足1件（A2・設計書の門の検査 rc=1）。中身は2つ。
  - ①require_acceptance_before_impl.sh の B-6（1137〜1168行）＝「✅ か『実測＝』の在る行に、実行コマンドの語（python3 ほか）が無い」。当たったのは、私が出力の形の見本として書いた「✅ 期待どおり …」の行。この検査は最初の1行で止まるので、設計書の全部を同じ条件で grep した＝3行（概要・4-0・4-2）。
  - ②必読ゲートの C＝「『読んだ』と書いたのに開いていない: engine_tuner_gen.py」。当たった文は道具が自動で入れる 2-4 の節の「engine_tuner_gen.py を構文の木で読んだ結果」（設計書 105行）。
- **原因＝①は私の元データの書き方。**B-6 の検査を読まずに、出力の見本に ✅ を書いた。②は 2026-09-24 に同じ型が在った（worklog 20260924）のに、読むもの宣言に入れていなかった。
- **直し**＝①3行に、その出力を出すコマンド（`python3 .claude/tools/run_breaks.py …`）を書き添えた（結果の行ではなく出力の形の説明なので、出すコマンドを添えるのが検査の狙いにも合う）。元データで「✅ の在る行のうちコマンドの語の無い行」を数え直して 0行。②engine_tuner_gen.py の冒頭（1〜40行）を Read tool で開いた（宣言の15件の外・まこさんに報告）。
- ★この2つのために、まこさんに cp を もう1回（3回目）お願いすることになった。元データの sha256＝d9d46e5d…。

### 2-8 cp の3回目のあと、承認の前の検査が不足0件になった（2026-09-26）

- まこさん「コマンド打った。３回目」。sha256 が控えと同じ（d9d46e5d…）。
- `gen_acceptance.py --write`＝設計書 637行・囲み 12個・法則の件数 51件／51行。書いた直後の検査は何も出さなかった。
- `pre_audit_check.py --check-design .claude/state/acceptance.md`＝「設計書の中身は通ります（不足0件）（TARGET 1 本 × 群1 38 本 ／ 群2 37 本を全部 試しました）」。
- `require_design_check_before_approval.py --try`＝「承認のプログラムの止まり所 A1〜A8・B1・B2 は全部 通ります（不足0件）」（4.9秒）。
- 設計書の sha256＝2bcd5e56…。目印＝breaks-measure-one-20260926。次＝まこさんに承認をお願いする（往復1回目）。
- ★教訓の候補＝元データを書く前に、①§4 の項目の正本（design_section_map.json）の全部 ②承認の前の検査の全部（B-6 など）を読む。今回は手本の元データだけを見て書き、cp を3回お願いした。

### 2-9 承認（1回目）・監査に出さない決定・実装・自己テスト（2026-09-26）

- まこさんの問い「監査に出さなくても問題ないということ？」→ 私の答え＝失うもの（第三者の確かめ・恒久64番）と、失っても偽の「済」は出ない理由（承認の経路は --only を使わない）を出した。
- まこさんの決定（逐語）＝「では。監査には出さないことにする。」「承認したよ」。承認の記録＝acceptance.approved と design_approved.json が 2bcd5e56…（設計書と同じ）・控え acceptance_archive/breaks-measure-one-20260926.md。
- 実装（Edit・run_breaks.py）＝①冒頭の説明の「使い方」に1行 ②関数 `pick_rows`（`main` の前）③旗 `--only`（append）と、`--measure-only` なしなら rc=2 で止める枝 ④表を読んだ後に `pick_rows` で絞り、表に無い名前なら rc=2 ⑤測るだけの口の最後に「--only で選んだ N 本だけ」の1行 ⑥SELF_TESTS に T17 ⑦selftest に T17a〜d。
- `python3 .claude/tools/run_breaks.py --selftest`＝「✅ 番人 17/17 pass」（T17 を含む）。
- 次のコマンド（--count-targets）は設計↔実装ゲートに止められた。1回目＝設計書の SPEC（実装の前のコードから作った）に pick_rows が無い。設計書の 7-6 の注記「触る関数の一覧は、実装の後に確定させます＝作り直して置き替えます」のとおり `gen_acceptance.py --write` で作り直した（641行・sha256 efa0f8c2…）。承認の控えとの違いは、道具が作る3か所（2-1 の実測の結果・7-7 の行番号・SPEC）だけ（diff で確かめた）。
- 2回目＝ゲートは、いまの設計書の承認が合わないとき「最後に承認され git に登録された控え」で照らす（require_design_contract_before_run.sh の 333〜350行・design_gate_fallback.py）。今日の控えは git に未登録なので、9/17 の breaks-fix-found-20260917 の控えが選ばれて止まった。
- 作り直した設計書で＝`require_design_check_before_approval.py --try` 不足0件（5.2秒）・`verify_design_contract.py --diff` 齟齬 0件。
- **★私の誤り＝承認のお願いの時に、2回目の承認が要ることを先に言っていなかった。**新しい関数を足す設計書は、実装の後に SPEC を作り直すので、承認が2回になる（設計書の 7-6 の注記に在る・手本 breaks-target-count-20260917 の控えの SPEC も実装の後の形）。検査 B1・B2 は壊すプログラムの行しか見ないので、この2回目は検査に出なかった。まこさんの指示（2026-09-05「条件は先に全部 出す」）に反した。

### 2-10 承認（2回目）と、完成の条件の出力（2026-09-26）

- まこさん「２回目の承認した」。acceptance.approved と design_approved.json が efa0f8c2…（設計書と同じ）。
- 完成の条件の4行（どれも壊すプログラム「—」＝承認のプログラムは済にしない。完成は まこさんが出力を見て決める）。
  - #1 `python3 .claude/tools/run_breaks.py --selftest`＝「✅ 番人 17/17 pass」（T17 を含む・2-9 で走らせた出力）。
  - #2 `python3 .claude/tools/run_breaks.py --design v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2e-bundle1-20260925.md --measure-only --only b100_streak_tree_eval.sh`＝「✅ 期待どおり # 2 b100_streak_tree_eval.sh rc=1（期待 1）」「止まった 1/1」「（--only で選んだ 1 本だけを測りました）」・11.8秒。
  - #3 同じ控えで `--only b00_not_in_table.sh`＝「[STOP] --only の名前が、設計書の完成の条件の表に載っていません: b00_not_in_table.sh」・rc=2。
  - #4 `python3 .claude/tools/run_breaks.py --count-targets`＝b01・b44・b52・b90・b95 とも「1か所」。全体＝「1か所 64 本 ／ 0か所か2か所以上 0 本 ／ 数えない 35 本（合計 99 本）」＝直す前と同じ。
  - `--measure-only` の無い `--only` は、土台ゲートが私の Bash から走らせない（run_breaks.py は --measure-only か --selftest が無いと通さない）。自己テスト T17d（rc=2）で見ている。
- 監査には出さない（まこさん決定 2026-09-26）。
- ★6番の手順を実物で確かめた＝当てる道具 apply_audit_fix.py の `--report` は、承認の印を照らさずに、監査結果の修正の指示を相手のファイル（設計書の元データとコード）に1回で書く（冒頭の「使い方」）。未決と案は `--choose <番号>=<案の記号 または 確定>` で選ぶ（369・433〜441行）。＝CP43 の修正23〜26（コード）も `--report` で当たる。ToDo の7番・8番は「承認2回」の前提で書いていたので、書き直す。

### 2-11 束1 の元データを戻し、CP43 の修正を当てた（6段の⑥・2026-09-26）

- まこさん「コマンド打ったよ」（束1 の元データを戻す cp）。sha256 が控えと同じ（f9b98764…）。
- `apply_audit_fix.py --report <CP43> --severity Critical,Major,Minor,Process --choose 5=A,6=A,8=確定,9=確定,26=確定,27=確定,28=確定 --dry`＝「当たる 25 件／当てない 5 件（実物と合わない件は0）」。
- 書き込む前に、コードを直す修正（23〜27）の相手の行を探している壊すプログラムを grep した（L-605）＝b53・b55（observe_diag の別の T-h）・b76（法則 R1・R3 の系統の欄）の3本だけ当たり、どれも今回直す行を探していない。
- 本番＝「当てた 25 件／当てなかった 5 件」。相手＝acceptance_src.json（修正1〜6・10〜21・29）・m2_todo.json（8）・engine_tuner_exec.py（23）・engine_tuner_gen.py（24）・streak_scope_diag.py（25・26）・regime_laws.json（27）。
- 走らせるコマンドの件＝`gen_regime_kb.py --write todo`（§3・1555行・hash=98a87f0b…）・`gen_regime_kb.py --write laws`（§11・477行・hash=ea11cc69…）・`gen_acceptance.py --write`（修正7・22・30＝設計書 2081行・sha256 d1dea6c1…）。
- 書いた直後の検査＝不足10件。A群2件＋B群8件。
  - A2 ①必読ゲートの A＝engine_tuner_exec.py・streak_scope_diag.py を開いていない → Read tool で開いた（exec 4215〜4254行・diag 全文）。②読むもの宣言ゲート＝宣言の設計書が breaks-measure-one-20260926 のまま → **原因＝私が束1 の宣言（9/25・32件・OK 済み）を、道具の直しの宣言で上書きし、控えを取っていなかった**（design_read_plan.md は git の外）。今日⑥で開いた13件で宣言を出し直した（まこさんの OK 待ち）。道具の直しの宣言は `design_read_plan_breaks-measure-one-20260926.md` に控えた。
  - A9 照合A〜D＝「impl_functions が承認のときから変わっています（設計書 5b171ec4… ／ 凍結 a7485354…）」。**原因＝道具の直しの承認で、承認のプログラムが1つだけの凍結ファイル（impl_functions_frozen.json）を run_breaks.py の一覧に書き替えた**（git の HEAD の版は束1 の exec・gen・diag の一覧）。束1 の元データの関数の一覧は CP43 の修正の前後で同じで、HEAD の凍結とも同じ（jq で確かめた）。＝凍結を HEAD の版に戻せば解ける。凍結は土台のファイルなので、私の Bash からは書けない（土台ゲート）＝まこさんに `git checkout` をお願いする。ほかの土台のファイル（breaks_frozen.json・spec_lists.json）は git の HEAD から変わっていない（git status で確かめた）。
  - B群8件＝壊すプログラム4本（b77・b99・b100・b103）と、その行のコマンド（gen と exec の自己テスト）を、まだ走らせていない（A群が解けてから走らせる）。
- ★設計を2つ（束1 と道具の直し）交互に承認すると、1つだけの土台のファイル（凍結・読むもの宣言・承認の印）が後の方で上書きされる＝教訓の候補。

### 2-12 凍結を戻したあとの A9（2026-09-26）

- まこさん「コマンド打った」（凍結を git の HEAD に戻す git checkout）。`git status --short` と `git diff --stat HEAD` が空＝HEAD の版に戻った。読むもの宣言13件への OK は、まだいただいていない（返信に OK の語が無い＝私の読み方を返信の1行目に書いた）。
- `require_design_check_before_approval.py --try`＝不足10件のまま。A2＝宣言の OK が空・貼った証拠のファイルが無い。A9＝照合B「設計書に書いたのに実装していない」（exec の6つ・diag の3つ）と照合A「設計書の impl_functions に書いていないファイルを触った＝run_breaks.py」。
- **原因**＝照合は git の HEAD との差分を相手にする。束1 の本体は d85942e で commit 済みで、いまの差分は CP43 の修正（exec の自己テスト・gen の説明の1行・diag の2か所）と、道具の直し（run_breaks.py・まだ commit していない）だけ。gen は「差分がゼロ（commit 済み）＝照合B だけをファイルの中の全関数と行いました」の道で通っている。
- **直し方の見込み**＝道具の直しと CP43 の修正を commit すれば、exec と diag も gen と同じ道になり、run_breaks.py の差分も消える。commit は まこさんの OK が要る。

<!-- ARC iter="point2-design-to-impl-20260930" -->

# 設計書｜2点目＝設計書から実装を作る

TARGET: .claude/tools/apply_audit_fix.py, .claude/hooks/enforce_audit_fix.py, .claude/tools/gen_acceptance.py

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `point2-design-to-impl-20260930/ok_fix_point2_20260930`・`point2-design-to-impl-20260930/ok_point2_20260930`・`point2-design-to-impl-20260930/okd_fix_point2_20260930`・`point2-design-to-impl-20260930/okd_point2_20260930`・`point2-design-to-impl-20260930/req_point2_20260930`・`point2-design-to-impl-20260930/req_point2b_20260930`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/point2-design-to-impl-20260930/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work point2-design-to-impl-20260930 --write`。検出＝`--work point2-design-to-impl-20260930 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=4822cf68e092fd19 gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/point2-design-to-impl-20260930/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/point2-design-to-impl-20260930/ok_fix_point2_20260930.txt`（まこさんの発言）・`verbatim/point2-design-to-impl-20260930/ok_point2_20260930.txt`（まこさんの発言）・`verbatim/point2-design-to-impl-20260930/okd_fix_point2_20260930.txt`（まこさんが OK した CC の文）・`verbatim/point2-design-to-impl-20260930/okd_point2_20260930.txt`（まこさんが OK した CC の文）・`verbatim/point2-design-to-impl-20260930/req_point2_20260930.txt`（まこさんの発言）・`verbatim/point2-design-to-impl-20260930/req_point2b_20260930.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝640 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_fix_point2_20260930` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_point2_20260930` | V01〜V03（3 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_fix_point2_20260930` | V01〜V02（2 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_fix_point2_20260930` | V03〜V09（7 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V10〜V13（4 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V14〜V26（13 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V27〜V34（8 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V35〜V40（6 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V41〜V46（6 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V47〜V241（195 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V242〜V248（7 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V249〜V255（7 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V256〜V260（5 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V261〜V262（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V263〜V273（11 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V274〜V294（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V295〜V301（7 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_fix_point2_20260930` | V302〜V317（16 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V01〜V03（3 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_point2_20260930` | V04〜V08（5 行） | 4-0 | 後の案（okd_fix_point2_20260930）で置き換えた【4-0】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V09〜V11（3 行） | 4-1 | 後の案（okd_fix_point2_20260930）で置き換えた【4-1】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V12〜V14（3 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V15〜V22（8 行） | 4-3 | 後の案（okd_fix_point2_20260930）で置き換えた【4-3】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V23〜V29（7 行） | 4-4 | 後の案（okd_fix_point2_20260930）で置き換えた【4-4】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V30〜V34（5 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V35〜V36（2 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V37〜V38（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V39〜V40（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V41〜V42（2 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V43〜V44（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V45〜V46（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V47〜V50（4 行） | 4-12 | 後の案（okd_fix_point2_20260930）で置き換えた【4-12】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V51〜V54（4 行） | 4-13 | 後の案（okd_fix_point2_20260930）で置き換えた【4-13】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V55〜V56（2 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V57〜V58（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V59〜V60（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V61〜V62（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V63〜V64（2 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V65〜V209（145 行） | 4-20 | 後の案（okd_fix_point2_20260930）で置き換えた【4-20】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V210〜V215（6 行） | 5 | 後の案（okd_fix_point2_20260930）で置き換えた【5】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V216〜V221（6 行） | 6-2 | 後の案（okd_fix_point2_20260930）で置き換えた【6-2】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V222〜V226（5 行） | 6-3 | 後の案（okd_fix_point2_20260930）で置き換えた【6-3】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V227〜V233（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V234〜V235（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_point2_20260930` | V236〜V237（2 行） | 7-3 | 後の案（okd_fix_point2_20260930）で置き換えた【7-3】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V238〜V247（10 行） | 7-4 | 後の案（okd_fix_point2_20260930）で置き換えた【7-4】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V248〜V268（21 行） | 7-5 | 後の案（okd_fix_point2_20260930）で置き換えた【7-5】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V269〜V274（6 行） | 7-6 | 後の案（okd_fix_point2_20260930）で置き換えた【7-6】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V275〜V288（14 行） | 7-8 | 後の案（okd_fix_point2_20260930）で置き換えた【7-8】の行＝設計書には写していない（道具が決めた） |
| `okd_point2_20260930` | V289〜V293（5 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `req_point2_20260930` | V01〜V23（23 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `req_point2b_20260930` | V01〜V03（3 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
5点の2点目（設計書から実装を作る）。承認された設計書の実装の指示（4-20）を、当てる道具 apply_audit_fix.py の --design が実物に当てる形にする。いまの道具は、新しいファイルを作れず、hook と壊すプログラムには当てず、当てた件を記録しない。そのため直近の設計書は全部 4-20 を「非該当＝承認の後に CC が Edit で当てる」にしていた。直した後は、新しいファイル・hook・壊すプログラムも、承認と TARGET／NEW_FILE がそろったときだけ道具が当て、当てた件を記録に残す。さらに、承認済みの設計書に実装の指示が在る間は hook 12 が CC の手の直しを止め、設計書の道具は 4-20 が0件の設計書を作らない。＝CC が手でコードを書く道を、両方とも機械で塞ぐ。この工事の実装そのものも、4-20 に書いて道具で当てる。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 新しいファイルを作る道があるか | `grep -c 'def new_file_check' .claude/tools/apply_audit_fix.py` | 実装の前は無い（新しいファイルを作る道が無い）。実装の後は在る | 1（終了コード 0） |
| hook と壊すプログラムの置き場を照らしているか | `grep -c 'BREAKS_DIR' .claude/tools/apply_audit_fix.py` | 実装の前は無い（道具の .py だけに当てる）。実装の後は在る | 7（終了コード 0） |

### 2-2 探す材料・成績表・乱数（2-2〜2-4＝この工事では非該当）

［自動］TARGET と NEW_FILE から非該当を決めた
<!-- ACC_MATERIALS_START hash=146f46ddc53368ac gen_acceptance.py が自動生成＝手で書き換えない -->
**非該当。**この工事の直す相手（TARGET・NEW_FILE）に、売買のロジック（scripts/priority_rebuild・engine_tuner）が無い（プログラムが TARGET と NEW_FILE から決めました）。
<!-- ACC_MATERIALS_END -->
<!-- ACC_RANKING_START hash=146f46ddc53368ac gen_acceptance.py が自動生成＝手で書き換えない -->
**非該当。**この工事の直す相手（TARGET・NEW_FILE）に、売買のロジック（scripts/priority_rebuild・engine_tuner）が無い（プログラムが TARGET と NEW_FILE から決めました）。
<!-- ACC_RANKING_END -->
<!-- ACC_RANDOM_START hash=146f46ddc53368ac gen_acceptance.py が自動生成＝手で書き換えない -->
**非該当。**この工事の直す相手（TARGET・NEW_FILE）に、売買のロジック（scripts/priority_rebuild・engine_tuner）が無い（プログラムが TARGET と NEW_FILE から決めました）。
<!-- ACC_RANDOM_END -->

## 3｜目標と、やらないこと

### 3-1 やらないこと（1件ずつ・理由と出どころ）

［手書き］やることの表の「3-1 やらないこと」
| # | やらないこと | 理由 | 出どころ |
|---|---|---|---|
| 1 | hook 12 の、監査結果の道の直しはしない | 監査結果から実装を直すのは5点目の相手。この工事で足すのは設計書の道の分だけ | next_step.md の 0-2 の「5点目」の行 |
| 2 | コードの中身を道具が作る形にはしない | 道具がするのは、設計書に書いたコードを実物に書き写すことだけ。中身は案の【4-20】に CC が書き、まこさんの OK・写しで走らせた自己テスト・監査で確かめる | worklog 20260930 §36 |
| 3 | 設計↔実装ゲートを直さない | 当てる道具そのものを直す工事でだけ止まる。承認の後に まこさんの端末で当てる道具を2回 打っていただいて進める | worklog 20260930 §35・§24 |
| 4 | 監査結果の道（--report）で新しいファイルを作らない | 監査結果から直すのは4点目・5点目の相手 | next_step.md の 0-2 の「4点目」「5点目」の行 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 承認の後、当てる道具を まこさんの端末で2回 打っていただいてよいか（当てる道具そのものを直す工事では、設計↔実装ゲートが実装の前に私の実行を止めるため） | 打っていただく。同じコマンドを2回（1回目で道具2本を直し、2回目で直った道具が hook 12 を直す）。リポジトリの直下で python3 .claude/tools/apply_audit_fix.py --design; python3 .claude/tools/apply_audit_fix.py --design | worklog 20260930 §35・§36 |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
当てる道具 apply_audit_fix.py の --design（設計書の実装の指示を実物に当てる口）を直し、設計書に書いた実装を、CC が Edit で書かずに道具が当てる形にする。あわせて、CC が手でコードを書く道を2つとも機械で塞ぐ。
1つ目＝新しいファイル（直す前の文字が「なし」）を作れるようにする。
2つ目＝hook と壊すプログラムにも、承認と TARGET／NEW_FILE がそろったときだけ当てられるようにする。
3つ目＝設計書の道で当てた件を当てた記録に書き、もう当て終わった件を失敗に数えないようにする。
4つ目＝承認済みの設計書に実装の指示が在る間、hook 12 がその TARGET と NEW_FILE を CC の手の直しから止める。
5つ目＝設計書の道具が、直すファイルが在るのに 4-20 が0件の設計書を作らない。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
動かすのは まこさん（承認の後に端末で当てる道具を2回）と CC（自己テスト・--dry）。
読むのは、承認の印・設計書・工事のフォルダの実装の指示。書くのは、設計書の TARGET／NEW_FILE に在るファイルと、当てた記録 applied_fixes.json。
hook 12 は、CC の Write・Edit・MultiEdit のたびに設計書と承認の印を読む。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
入力＝承認された設計書の 4-20 の実装の指示（6つの欄）と、承認の印。
出力＝TARGET と NEW_FILE のファイル（直した中身・新しいファイル）と、当てた記録に足した行（名前は「design:<工事名>」）。

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
- apply_audit_fix の置き場の定数（HOOKS_DIR・BREAKS_DIR を足す）＝hook と壊すプログラムの置き場。
- apply_audit_fix.tool_target_ok＝道具の .py に加えて、hook（.py・.sh）と壊すプログラム（.sh）も、承認と TARGET／NEW_FILE がそろったときだけ真にする。
- apply_audit_fix.new_file_check（新しく作る）＝新しいファイルの件が作れるかを見る。
- apply_audit_fix.design_key（新しく作る）＝設計書の道の当てた記録の名前「design:<ARC の iter>」を作る。
- apply_audit_fix.check_one＝設計書の道だけ、直す前の文字が「なし」の件を new_file_check に回す。
- apply_audit_fix.main＝新しいファイルは全文を書く・権限は .sh なら 755・設計書の道でも記録に書く・もう当て終わった件は失敗に数えない。
- apply_audit_fix.selftest＝本物の記録に書かない形にし、場面 T26〜T31 を足す。
- enforce_audit_fix.pending（hook 12）＝承認済みの設計書に実装の指示が在れば、その TARGET と NEW_FILE を止める一覧に入れる。
- enforce_audit_fix.main（hook 12）＝止めたときの案内に、設計書の道の当て方を足す。
- gen_acceptance.page＝直すファイルが在るのに実装の指示が0件なら止まる。
- gen_acceptance._sample_work＝自己テストの見本にも実装の指示を1件 持たせる。
- gen_acceptance.selftest＝4-20 が0件なら止まる場面を足す。

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
- ①承認の印と設計書のハッシュ値を照らす（今までどおり）。
- ②実装の指示を全部 先に確かめる。新しいファイルの件は、まだ無いか・同じ中身で在るか・別の中身で在るかを見る。
- ③実物と合わない件が1件でも在れば、1件も当てない（今までどおり）。
- ④当てる。新しいファイルは全文を書く。
- ⑤当てた件と、もう当て終わっていた件を、当てた記録に「design:<工事名>」で書く。
- ⑥もう当て終わっていた件だけが残ったときは rc=0。
- ⑦この後、承認済みの設計書に実装の指示が在る間は、CC が TARGET と NEW_FILE を Write・Edit しようとすると hook 12 が止める。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝この工事の設計書。①まこさんが承認する ②まこさんが端末で当てる道具を2回 打つ ③1回目＝道具が承認の印と設計書のハッシュ値を照らし、全件を先に確かめてから apply_audit_fix.py と gen_acceptance.py に当てる（hook 12 は古い道具では当てられないので飛ばす）④2回目＝直った道具が hook 12 に当て、1回目の件は「もう当て終わっている」で飛ばす ⑤当てた件を当てた記録に「design:point2-design-to-impl-20260930」で書く ⑥この後、私が apply_audit_fix.py を Edit で直そうとすると hook 12 が止める ⑦私が自己テストを走らせ、全部 pass を出す。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
- 新しいファイルの件は「修正 N（設計書）: 新しいファイルを作った」とパスつきで出る。
- もう当て終わった件は「もう当て終わっている」と出て、終了コードの失敗に数えない。
- 最後に「当てた記録に N 件を足した」が、設計書の道でも出る。
- hook 12 が止めたときは、止めた理由に「設計書の実装の指示」と当て方のコマンドが出る。
- 設計書の道具は、4-20 が0件の設計書を作らずに理由を出して止まる。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
- 新しいファイルが別の中身でもう在る＝上書きせず、1件も当てない（rc=1）。
- 新しいファイルの置き場のフォルダが無い＝1件も当てない（rc=1）。
- 同じ新しいファイルに2件＝1件も当てない（rc=1）。
- 新しいファイルが NEW_FILE に無い・承認の印が違う＝当てずに一覧に出す（rc=1）。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
当てた記録＝SDK/.claude/audits/applied_fixes.json に書き足す（今までの監査結果の道と同じ置き場・消さない）。新しいファイル＝設計書の NEW_FILE に書いた置き場。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
- 直すファイルの名前で壊すプログラムを grep すると、当てる道具は b101・b102・b118・b119、設計書の道具は b72・b73・b89。探す行（approved_ok の行・_recheck の行・if hard の行・tool_target_ok の定義の行・command_argv の定義の行・verify の定義の行・build_coderef の定義の行）は変えない。
- b89 は、いまの設計書の表の行を壊す壊すプログラムで、この工事の完成の条件には載せない。
- hook 12 は tool_target_ok を呼ぶ。広げた後は、承認済みの設計書の TARGET に在る hook と壊すプログラムにも、監査の修正が当たるまで CC の手の直しを止める。
- 承認済みの過去の設計書（4-20 が非該当）は、この後 --verify で作り直すと止まる。控えは直さない。
- 依頼書の道具（gen_audit_docs.py）は、設計書の道具の見本の工事のフォルダを使う。写しで自己テスト 12/12 を確かめた。

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
手本＝今日 道具の .py に当てる形を足した tool_target_ok と、その自己テスト T17〜T19（worklog 20260930 §8）。

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=0c31e681aebf37ee gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: TOOLS_DIR の定義
直す前の文字:
~~~
TOOLS_DIR = os.path.join(ROOT, ".claude", "tools")                          # 自己テストが一時の置き場に替える
~~~
足す文字:
~~~

# ★2026-09-30（設計書 point2-design-to-impl-20260930）＝hook と壊すプログラムにも、承認と TARGET／NEW_FILE がそろったときだけ当てる
HOOKS_DIR = os.path.join(ROOT, ".claude", "hooks")                          # 自己テストが一時の置き場に替える
BREAKS_DIR = os.path.join(ROOT, ".claude", "breaks")                        # 自己テストが一時の置き場に替える
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:86「TOOLS_DIR = os.path.join(ROOT, ".claude", "tools")                          # 自己テストが一時の置き場に替える」
状態: 確定

#### 実装 2
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: tool_target_ok
直す前の文字:
~~~
    real = os.path.realpath(repo_path(raw))
    if not real.endswith(".py") or os.path.dirname(real) != os.path.realpath(TOOLS_DIR):
        return False
    others = [k for k in NEVER_WRITE if k != ".claude/tools/"]
~~~
直した後の文字:
~~~
    real = os.path.realpath(repo_path(raw))
    # ★2026-09-30（設計書 point2-design-to-impl-20260930）＝道具の .py に加えて、hook（.py・.sh）と壊すプログラム（.sh）にも当てる
    kinds = {os.path.realpath(TOOLS_DIR): (".py",), os.path.realpath(HOOKS_DIR): (".py", ".sh"),
             os.path.realpath(BREAKS_DIR): (".sh",)}
    ends = kinds.get(os.path.dirname(real))
    if not ends or not real.endswith(ends):
        return False
    others = [k for k in NEVER_WRITE if k not in (".claude/tools/", ".claude/hooks/", ".claude/breaks/")]
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:216「real = os.path.realpath(repo_path(raw))」
状態: 確定

#### 実装 3
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: check_one の前
直す前の文字:
~~~
def check_one(f: dict, chosen: dict = None, run_ok: bool = False) -> tuple:
~~~
直した後の文字:
~~~
def design_key(design_text: str, design_path: str) -> str:
    """設計書の道の、当てた記録の名前＝「design:<ARC の iter>」（目印が無ければ設計書のファイル名）。"""
    m = re.search(r'<!-- ARC iter="([^"]+)" -->', design_text)
    return "design:" + (m.group(1) if m else os.path.basename(design_path))


def new_file_check(f: dict, path: str) -> tuple:
    """新しいファイル（直す前の文字が「なし」）の件が作れるか。戻り＝(作れるか, 理由, "")。★設計書の道だけ。

    作れる＝4つ目が「直した後の文字」1つだけ・中身が空でない・ファイルがまだ無い・置き場のフォルダが在る。
    同じ中身でもう在れば当て済み。別の中身で在れば止める（上書きしない）。
    """
    plans = [(k, b) for _a, k, b in f["4つ目"]]
    if len(plans) != 1 or plans[0][0] != "直した後の文字" or not plans[0][1]:
        return False, "新しいファイルの件は、4つ目が「直した後の文字」1つ（ファイルの全文）であること", ""
    body = plans[0][1]
    if os.path.exists(path):
        if open(path, encoding="utf-8").read().rstrip("\n") == body.rstrip("\n"):
            return False, "もう当て終わっている（新しいファイルが同じ中身で在る）", ""
        return False, f"新しいファイルのはずが、別の中身でもう在る（{path}）＝上書きしない", ""
    if not os.path.isdir(os.path.dirname(path)):
        return False, f"新しいファイルの置き場のフォルダが無い（{os.path.dirname(path)}）", ""
    return True, "新しいファイル", ""


def check_one(f: dict, chosen: dict = None, run_ok: bool = False, new_ok: bool = False) -> tuple:
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:392「def check_one(f: dict, chosen: dict = None, run_ok: bool = False) -> tuple:」
状態: 確定

#### 実装 4
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: check_one の中（実在の確かめの前）
直す前の文字:
~~~
    path = repo_path(rel)
    if not os.path.isfile(path):
~~~
直した後の文字:
~~~
    path = repo_path(rel)
    # ★2026-09-30（設計書 point2-design-to-impl-20260930）＝新しいファイル（直す前の文字が「なし」）は、設計書の道でだけ作る
    if new_ok and (f["直す前の文字"] or "").strip() == "なし":
        return new_file_check(f, path)
    if not os.path.isfile(path):
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:417「path = repo_path(rel)」
状態: 確定

#### 実装 5
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: main の全件の確かめ
直す前の文字:
~~~
        ok, why, cur = check_one(f, chosen, run_ok=not design_mode)
~~~
直した後の文字:
~~~
        ok, why, cur = check_one(f, chosen, run_ok=not design_mode, new_ok=design_mode)
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:660「ok, why, cur = check_one(f, chosen, run_ok=not design_mode)」
状態: 確定

#### 実装 6
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: main の当てる前の組み立て
直す前の文字:
~~~
    for f, _w, _c in ready:
        path = repo_path(f["対象のファイル"])
        if path not in mem:
~~~
直した後の文字:
~~~
    for f, _w, _c in ready:
        path = repo_path(f["対象のファイル"])
        if _w == "新しいファイル":
            # ★2026-09-30（設計書 point2-design-to-impl-20260930）＝新しいファイルは中身の全文を書く（同じファイルに2件は止める）
            if path in mem:
                print(f"\n❌ 修正 {f['番号']}: 新しいファイル {os.path.relpath(path, ROOT)} に2件 当てようとしています＝1件も当てません")
                return 1
            mem[path] = next(b for _a, k, b in f["4つ目"] if k == "直した後の文字").rstrip("\n") + "\n"
            plan.append((f, "新しいファイルを作った", path))
            continue
        if path not in mem:
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:698「for f, _w, _c in ready:」
状態: 確定

#### 実装 7
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: main の --dry の終わり
直す前の文字:
~~~
        return 1 if (design_mode and stopped) else 0
~~~
直した後の文字:
~~~
        return 1 if (design_mode and [x for x in stopped if not x[1].startswith("もう当て終わっている")]) else 0
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:718「return 1 if (design_mode and stopped) else 0」
状態: 確定

#### 実装 8
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: main の書き込み（権限）
直す前の文字:
~~~
                os.chmod(tmp_path, os.stat(path).st_mode & 0o7777)
~~~
直した後の文字:
~~~
                os.chmod(tmp_path, (os.stat(path).st_mode & 0o7777) if os.path.exists(path)
                         else (0o755 if path.endswith(".sh") else 0o644))
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:728「os.chmod(tmp_path, os.stat(path).st_mode & 0o7777)」
状態: 確定

#### 実装 9
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: main の当てた記録と終了コード
直す前の文字:
~~~
    if not design_mode:
        rep = os.path.basename(a.report)
        rec = [{"report": rep, "num": f["番号"], "file": f["対象のファイル"] or "", "how": "当てた"}
               for f, _what, _path in plan]
        rec += [{"report": rep, "num": f["番号"], "file": f["対象のファイル"] or "", "how": "もう当て終わっていた"}
                for f, why, _c in stopped if why.startswith("もう当て終わっている")]
        n_rec = _record_applied(rec)
        print(f"— 当てた記録に {n_rec} 件を足した（{os.path.relpath(APPLIED_RECORD, ROOT)}）")
    rc_cmd = run_commands(cmds)
    # ★設計書の道（設計書 4-4 の 10）＝当てなかった件が1件でも在れば rc=1（当て忘れを機械で見つける）
    return 1 if ((design_mode and stopped) or rc_cmd) else 0
~~~
直した後の文字:
~~~
    # ★2026-09-30（設計書 point2-design-to-impl-20260930）＝設計書の道でも記録に書く（名前は「design:<iter>」）
    rep = design_key(text, a.design) if design_mode else os.path.basename(a.report)
    rec = [{"report": rep, "num": f["番号"], "file": f["対象のファイル"] or "", "how": "当てた"}
           for f, _what, _path in plan]
    rec += [{"report": rep, "num": f["番号"], "file": f["対象のファイル"] or "", "how": "もう当て終わっていた"}
            for f, why, _c in stopped if why.startswith("もう当て終わっている")]
    n_rec = _record_applied(rec)
    print(f"— 当てた記録に {n_rec} 件を足した（{os.path.relpath(APPLIED_RECORD, ROOT)}）")
    rc_cmd = run_commands(cmds)
    # ★設計書の道（設計書 4-4 の 10）＝当てなかった件が1件でも在れば rc=1（当て忘れを機械で見つける）
    #   ★2026-09-30＝もう当て終わっていた件は数えない（2回目の承認の後に、足した件だけを当てられる）
    left = [x for x in stopped if not x[1].startswith("もう当て終わっている")]
    return 1 if ((design_mode and left) or rc_cmd) else 0
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:742「if not design_mode:」
状態: 確定

#### 実装 10
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: selftest の一時の置き場
直す前の文字:
~~~
    tmp = tempfile.mkdtemp(prefix="_selftest_impl_apply_", dir=os.path.join(ROOT, ".claude", "state"))
    try:
~~~
直した後の文字:
~~~
    tmp = tempfile.mkdtemp(prefix="_selftest_impl_apply_", dir=os.path.join(ROOT, ".claude", "state"))
    rec_saved = globals()["APPLIED_RECORD"]
    globals()["APPLIED_RECORD"] = os.path.join(tmp, "applied_selftest.json")   # ★本物の記録には書かない
    try:
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:797「tmp = tempfile.mkdtemp(prefix="_selftest_impl_apply_", dir=os.path.join(ROOT, ".claude", "state"))」
状態: 確定

#### 実装 11
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: selftest の終わりの片付け
直す前の文字:
~~~
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
~~~
直した後の文字:
~~~
    finally:
        globals()["APPLIED_RECORD"] = rec_saved
        shutil.rmtree(tmp, ignore_errors=True)
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:1147「finally:」
状態: 確定

#### 実装 12
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: selftest の置き場の差し替え
直す前の文字:
~~~
        g_saved = (globals()["TOOLS_DIR"], globals()["DESIGN"], globals()["APPROVED"])
        tdir = os.path.join(tmp, ".claude", "tools")
        os.makedirs(tdir, exist_ok=True)
        globals()["TOOLS_DIR"], globals()["DESIGN"], globals()["APPROVED"] = tdir, md, mark
~~~
直した後の文字:
~~~
        g_saved = (globals()["TOOLS_DIR"], globals()["DESIGN"], globals()["APPROVED"],
                   globals()["HOOKS_DIR"], globals()["BREAKS_DIR"])
        tdir = os.path.join(tmp, ".claude", "tools")
        os.makedirs(tdir, exist_ok=True)
        globals()["TOOLS_DIR"], globals()["DESIGN"], globals()["APPROVED"] = tdir, md, mark
        globals()["HOOKS_DIR"] = os.path.join(tmp, ".claude", "hooks")
        globals()["BREAKS_DIR"] = os.path.join(tmp, ".claude", "breaks")
        os.makedirs(globals()["HOOKS_DIR"], exist_ok=True)
        os.makedirs(globals()["BREAKS_DIR"], exist_ok=True)
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:1006「g_saved = (globals()["TOOLS_DIR"], globals()["DESIGN"], globals()["APPROVED"])」
状態: 確定

#### 実装 13
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: selftest の置き場を戻す
直す前の文字:
~~~
            globals()["TOOLS_DIR"], globals()["DESIGN"], globals()["APPROVED"] = g_saved
~~~
直した後の文字:
~~~
            (globals()["TOOLS_DIR"], globals()["DESIGN"], globals()["APPROVED"],
             globals()["HOOKS_DIR"], globals()["BREAKS_DIR"]) = g_saved
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:1145「globals()["TOOLS_DIR"], globals()["DESIGN"], globals()["APPROVED"] = g_saved」
状態: 確定

#### 実装 14
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: selftest の T25 の後
直す前の文字:
~~~
                fails.append(f"❌ 当てた記録 T{total}: 前={before25} 足した={n25} 後={after25}")
~~~
足す文字:
~~~


            # ★T26〜T30（2026-09-30・設計書 point2-design-to-impl-20260930）＝hook と、新しいファイル
            hpy = os.path.join(globals()["HOOKS_DIR"], "h.sh")
            hrel = os.path.relpath(hpy, ROOT)
            hfix = {**tfix, "対象のファイル": hrel, "根拠の抜き書き": f"{hrel}:1「x = 1」"}

            def hook_case(good_mark):
                open(hpy, "w", encoding="utf-8").write("x = 1\n")
                open(md, "w", encoding="utf-8").write(f"# 見本\n\nTARGET: {hrel}\n")
                mark_of(md, mark) if good_mark else open(mark, "w", encoding="utf-8").write("0" * 64)
                return check_one(hfix)

            # T26 承認と TARGET がそろった hook には当てる／印が違えば当てない
            total += 1
            ok26a, _w, _c = hook_case(True)
            ok26b, why26b, _c = hook_case(False)
            if ok26a and not ok26b and "守りの仕組みなので当てない" in why26b:
                ok += 1
                print(f"   T{total} hook は承認と TARGET がそろったときだけ当てる → pass")
            else:
                fails.append(f"❌ 道具のファイル T{total}: hook の照らしが違う（そろった={ok26a}・印が違う={ok26b}）")

            # T27 新しいファイル（直す前の文字「なし」）を、承認と NEW_FILE がそろえば作る
            total += 1
            npath = os.path.join(globals()["BREAKS_DIR"], "b_new.sh")
            nrel = os.path.relpath(npath, ROOT)
            nitems = [item(1, nrel, "なし", "直した後の文字", "#!/bin/bash\necho new", ev)]
            open(code, "w", encoding="utf-8").write("x = 1\n")
            open(md, "w", encoding="utf-8").write(design(nitems, rel).replace(
                f"TARGET: {rel}\n", f"TARGET: {rel}\nNEW_FILE: {nrel}\n"))
            mark_of(md, mark)
            rc, out = run(["--design", md], mark)
            if rc == 0 and os.path.isfile(npath) and open(npath).read() == "#!/bin/bash\necho new\n":
                ok += 1
                print(f"   T{total} 新しいファイルを作る（承認と NEW_FILE がそろったとき） → pass")
            else:
                fails.append(f"❌ 新しいファイル T{total}: 作れない（rc={rc}）{out[-200:]}")

            # T28 同じ設計書をもう1回 当てると、当て済みとして rc=0（2回目の承認の後に、足した件だけを当てられる）
            total += 1
            rc, out = run(["--design", md], mark)
            if rc == 0 and "もう当て終わっている" in out:
                ok += 1
                print(f"   T{total} もう当て終わった件は失敗に数えない（rc=0） → pass")
            else:
                fails.append(f"❌ 新しいファイル T{total}: 2回目で rc={rc}")

            # T29 新しいファイルが別の中身でもう在れば、上書きせず1件も当てない
            total += 1
            open(npath, "w", encoding="utf-8").write("other\n")
            rc, out = run(["--design", md], mark)
            if rc == 1 and open(npath).read() == "other\n":
                ok += 1
                print(f"   T{total} 別の中身の既存ファイルは上書きしない → pass")
            else:
                fails.append(f"❌ 新しいファイル T{total}: 上書きした／rc={rc}")

            # T30 NEW_FILE に無い新しいファイルは作らない
            total += 1
            os.remove(npath)
            open(md, "w", encoding="utf-8").write(design(nitems, rel))
            mark_of(md, mark)
            rc, out = run(["--design", md], mark)
            if rc == 1 and not os.path.exists(npath):
                ok += 1
                print(f"   T{total} NEW_FILE に無い新しいファイルは作らない → pass")
            else:
                fails.append(f"❌ 新しいファイル T{total}: NEW_FILE の外なのに作った（rc={rc}）")

            # T31 承認済みの設計書に実装の指示が在る間は、hook 12 がその TARGET を CC の手の直しから守る
            total += 1
            fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
            saved31 = (e12.REPORTS, a12.DESIGN, a12.APPROVED)
            e12.REPORTS, a12.DESIGN, a12.APPROVED = os.path.join(tmp, "none_*_audit_report.md"), md, mark
            try:
                in31 = os.path.realpath(code) in e12.pending()
                open(mark, "w", encoding="utf-8").write("0" * 64)
                out31 = os.path.realpath(code) in e12.pending()
            finally:
                e12.REPORTS, a12.DESIGN, a12.APPROVED = saved31
            if in31 and not out31:
                ok += 1
                print(f"   T{total} 承認済みの設計書の TARGET は hook 12 が守る（承認が外れたら守らない） → pass")
            else:
                fails.append(f"❌ hook 12 T{total}: 承認中={in31} 承認が外れた後={out31}")
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:1143「fails.append(f"❌ 当てた記録 T{total}: 前={before25} 足した={n25} 後={after25}")」
状態: 確定

#### 実装 15
対象のファイル: .claude/hooks/enforce_audit_fix.py
直す箇所: pending の頭
直す前の文字:
~~~
    out = {}
    done = a.applied_keys()                                  # ★当てた記録（案A）
~~~
足す文字:
~~~

    # ★2026-09-30（設計書 point2-design-to-impl-20260930・2点目）＝承認済みの設計書に実装の指示（4-20）が在る間は、
    #   その設計書の TARGET と NEW_FILE を CC の手で直させない（実装は当てる道具だけが書く）。
    #   直しが要るときは、案の【4-20】に足して設計書を作り直し、承認を通して当てる。
    try:
        dtext = open(a.DESIGN, encoding="utf-8").read()
        if a.approved_ok(a.DESIGN)[0] and a.read_design_fixes(dtext):
            key = a.design_key(dtext, a.DESIGN)
            for p in a.design_targets(dtext):
                out.setdefault(p, []).append((key, "（設計書の実装の指示）"))
    except Exception:                                        # noqa: BLE001
        pass                                                 # 設計書が読めないときは止めない（fail-open・上と同じ）
~~~
根拠の抜き書き: .claude/hooks/enforce_audit_fix.py:75「out = {}」
状態: 確定

#### 実装 16
対象のファイル: .claude/hooks/enforce_audit_fix.py
直す箇所: main の案内の文
直す前の文字:
~~~
    print("   ＝先に当ててください:", file=e)
~~~
直した後の文字:
~~~
    print("   ＝先に当ててください（設計書の実装の指示なら python3 .claude/tools/apply_audit_fix.py --design）:", file=e)
~~~
根拠の抜き書き: .claude/hooks/enforce_audit_fix.py:128「print("   ＝先に当ててください:", file=e)」
状態: 確定

#### 実装 17
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: page の検査
直す前の文字:
~~~
    _ib = impl_before_problems(d)
~~~
直した後の文字:
~~~
    # ★2026-09-30（設計書 point2-design-to-impl-20260930・2点目）＝直すファイル（TARGET・NEW_FILE）が在るのに、
    #   実装の指示（4-20）を「非該当」にした設計書は作らない（実装を CC が手で書く道を残さない）。
    if (d.get("TARGET") or d.get("NEW_FILE")) and not (d.get("実装の指示") or []):
        raise SystemExit("[gen_acceptance] 直すファイル（TARGET・NEW_FILE）が在るのに、実装の指示（4-20）が0件です"
                         "（fail-closed・2点目）。案の【4-20】に、当てる道具が当てる形で実装を書いてください。")
    _ib = impl_before_problems(d)
~~~
根拠の抜き書き: .claude/tools/gen_acceptance.py:1303「_ib = impl_before_problems(d)」
状態: 確定

#### 実装 18
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: _sample_work の非該当の一覧
直す前の文字:
~~~
    for k in ("4-6", "4-7", "4-8", "4-9", "4-10", "4-11", "4-14", "4-15", "4-16", "4-17", "4-18", "4-20"):
        prop += [f"【{k}】", na]
~~~
直した後の文字:
~~~
    for k in ("4-6", "4-7", "4-8", "4-9", "4-10", "4-11", "4-14", "4-15", "4-16", "4-17", "4-18"):
        prop += [f"【{k}】", na]
    # ★2026-09-30（設計書 point2-design-to-impl-20260930）＝TARGET が在る設計書は 4-20 を非該当にできないので、見本も1件持つ
    #   （見本の置き場の中の、まだ無い新しいファイル＝本物のファイルに頼らない）
    prop += ["【4-20】", "```json",
             json.dumps([{"番号": 1, "対象のファイル": str(Path(base) / "sample_new.txt"), "直す箇所": "新しいファイル",
                          "直す前の文字": "なし", "種類": "直した後の文字", "中身": "見本",
                          "根拠の抜き書き": "見本:1「見本」", "状態": "確定"}], ensure_ascii=False),
             "```"]
~~~
根拠の抜き書き: .claude/tools/gen_acceptance.py:1871「for k in ("4-6", "4-7", "4-8", "4-9", "4-10", "4-11", "4-14", "4-15", "4-16", "4-17", "4-18", "4-20"):」
状態: 確定

#### 実装 19
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: selftest の T12 の前
直す前の文字:
~~~
        # T12（2026-09-29・まこさん指示「設計の元となるデータは明確にして」）＝0-1 に、要件のまとめ.md への参照と、
~~~
直した後の文字:
~~~
        # T17（2026-09-30・設計書 point2-design-to-impl-20260930）＝直すファイルが在るのに 4-20 が0件なら止まる
        total += 1
        d17 = _copy.deepcopy(base_d)
        d17["実装の指示"] = []
        try:
            page(d17)
            print(f"   T{total} 4-20 が0件でも書ける → fail")
        except SystemExit as e:
            if "実装の指示（4-20）が0件" in str(e):
                ok += 1
                print(f"   T{total} 直すファイルが在るのに 4-20 が0件だと止まる → pass")
            else:
                print(f"   T{total} 別の理由で止まった → fail（{str(e)[:120]}）")

        # T12（2026-09-29・まこさん指示「設計の元となるデータは明確にして」）＝0-1 に、要件のまとめ.md への参照と、
~~~
根拠の抜き書き: .claude/tools/gen_acceptance.py:2119「# T12（2026-09-29・まこさん指示「設計の元となるデータは明確にして」）＝0-1 に、要件のまとめ.md への参照と、」
状態: 確定

<!-- ACC_IMPL_END -->

［自動］まこさんが OK した案の【番号】の「非該当＝」の後ろの文と、項目の正本の名前
**非該当の項目（理由と出どころ）**＝4-6 制約（従う決まりの全件と、その出どころ）＝相場の法則・型の表・承認済みの設定を使わない道具の直し／4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）＝値の範囲を探す工事ではない／4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）＝旗を足さない（--design の中身だけが変わる）／4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）＝当てた記録の形は変えない（report の欄に「design:<工事名>」の値が増えるだけ）／4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）＝時刻の列・足の区切りに触らない／4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）＝当てる件数が増えるだけで、読むファイルは今までと同じ／4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）＝同時に2つ走らせない／4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）＝鍵・本番の発注に触らない。承認の印・凍結の記録・settings には今までどおり当てない／4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）＝4-12 の出力だけ

### 4-A この節に何を書いたか（一覧）

［自動］項目の正本と、OK された案・やることの表の有無
| 番号 | 段 | 項目 | 書いたか |
|---|---|---|---|
| 4-0 | 必ず | この仕組みは何か（全体・一続きの文章で書く） | 書いた |
| 4-1 | 必ず | システムの境界（誰が動かし、誰が結果を使うか） | 書いた |
| 4-2 | 必ず | 入力と出力（受け取るもの・出すもの・その形） | 書いた |
| 4-6 | 条件 | 制約（従う決まりの全件と、その出どころ） | 非該当（相場の法則・型の表・承認済みの設定を使わない道具の直し） |
| 4-3 | 必ず | 部品と責任の割り当て（どの部品が何をやるか） | 書いた |
| 4-4 | 必ず | 処理の流れ（うまくいったとき、何がどの順に起きるか） | 書いた |
| 4-19 | 必ず | 通しの例（最初から最後まで、1件を追いかけた例） | 書いた |
| 4-7 | 条件 | 探索の範囲（決める値と、その探し方＝範囲・並び・本数） | 非該当（値の範囲を探す工事ではない） |
| 4-9 | 条件 | 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗） | 非該当（旗を足さない（--design の中身だけが変わる）） |
| 4-12 | 必ず | 出る結果の姿（完成したとき、何がどう表示されるか） | 書いた |
| 4-5 | 必ず | 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか） | 書いた |
| 4-8 | 条件 | データ構造（表や JSON の列と中身を、新しく作るか・変えるか） | 非該当（当てた記録の形は変えない（report の欄に「design:<工事名>」の値が増えるだけ）） |
| 4-10 | 条件 | 保存先（出したものをどこに置くか・上書きか、書き足すか） | 書いた |
| 4-11 | 条件 | 時刻の扱い（時間帯・足の区切りをどこで切るか） | 非該当（時刻の列・足の区切りに触らない） |
| 4-14 | 条件 | 性能（どれくらい時間が掛かり、どれくらい容量を使うか） | 非該当（当てる件数が増えるだけで、読むファイルは今までと同じ） |
| 4-15 | 条件 | 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか） | 非該当（同時に2つ走らせない） |
| 4-16 | 条件 | セキュリティ（人に見せてはいけない値と、書き換えられては困る記録） | 非該当（鍵・本番の発注に触らない。承認の印・凍結の記録・settings には今までどおり当てない） |
| 4-17 | 省ける | ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか） | 非該当（4-12 の出力だけ） |
| 4-13 | 必ず | 影響範囲（この直しで、ほかのどれが壊れるか） | 書いた |
| 4-18 | 省ける | 再利用（手本にした、既にあるものの形） | 書いた |
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 19 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 新しいファイルは、直す前の文字「なし」の件として書く | 設計書の道具（impl_before_problems）が既に「なし」を新しいファイルとして扱っている。欄の形（gen_audit_docs）を変えずに済む | 4つ目の欄に新しい見出しを足す（欄の読み取りの道具を直すことになる） |
| 2 | hook と壊すプログラムは、道具の .py と同じ照らし（承認と TARGET／NEW_FILE）に入れる | 照らしを1か所にまとめる。承認の無い書き込みは今までどおり止まる | 別の照らしを作る（同じ判定が2か所になる） |
| 3 | hook 12 は、承認済みの設計書に実装の指示が在る間、TARGET を丸ごと止める | 当て終わった後も、私が手で書き足す道を残さない。直しは案の【4-20】に足して承認を通す | 当て終わった件だけ止めを外す（当てた後に手で直せてしまう） |
| 4 | 当てる道具は、まこさんの端末で2回 打っていただく | 1回目は古い道具なので hook 12 に当てられない。2回目は直った道具が当て、1回目の件は当て済みとして飛ばす | 設計↔実装ゲートに例外を足す（守りを緩める） |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=f2b622b929a52041 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b118_audit_fix_tools_target.sh` | #1 | tool_target_ok をいつも真にする |
| `b102_design_apply_no_precheck.sh` | #2 | 全件を先に確かめる処理と当てる直前の確かめを外す |
| `b101_design_apply_no_approval.sh` | #3 | 承認の印の照らしをいつも真にする |
| `b72_acceptance_handwritten.sh` | #4 | verify を中身を見ずに通す形にする |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | hook と壊すプログラムにも道具が書けるので、守りが1本の書き込みで外れる | 承認の印と TARGET／NEW_FILE がそろったときだけ。settings・承認の印・凍結の記録は今までどおり当てない（T8・T15・T26） |
| 2 | hook 12 が、承認中の設計書の TARGET を私の手から止めるので、直しのたびに承認が1回 要る | 案を出す前に写しで自己テストを走らせ、承認の後に直す回数を減らす（この工事でも写しで確かめた） |
| 3 | 直す前の文字の写し間違い | 案を出す前に一時の道具で19件とも実物にちょうど1か所を確かめた。設計書を作るときにも道具が照らす |
| 4 | 当てた後のコードの誤り | 案を出す前に、当てた後の写しで自己テスト（31/31・17/17・12/12）を確かめた |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（まこさんの端末で2回） | 1分以内 | 当てる19件は3本のファイル。当てる道具は全件を読んでから1回だけ書く |
| 自己テスト | 1分以内 | 当てた後の写しで走らせて、待ち時間なく終わった（秒は測っていない） |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝当てる道具の --design が、新しいファイル・hook・壊すプログラムを当てられず、当てた件も記録しなかった。そのため設計書の 4-20 を「非該当＝CC が Edit で当てる」にするしかなかった

**② 期待値分解**＝売買に触れないので、勝率・平均利益・敗率・平均損失は動かない

**③ root か symptom か**＝root。4-20 を非該当にせざるを得なかった原因（道具が当てられない相手）を直す

**④ ベースアップ**＝手本は同じ道具の tool_target_ok と自己テスト T17〜T19（4-18）

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
疑似シミュから取った値は1つもない。数字を決める工事ではない。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝設計書の実装を、当てる道具だけが書く形にする（道具が当てられる相手を広げ、手で書く道を2つ塞ぐ）。記録と当て済みの扱いは、そのための部品。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

［自動］TARGET と NEW_FILE から非該当を決めた
**非該当。**この工事の直す相手（TARGET・NEW_FILE）に、売買のロジック（scripts/priority_rebuild・engine_tuner）が無い（プログラムが TARGET と NEW_FILE から決めました）。

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **当てた後のコードが正しいか** | 見ない。道具は設計書に書いた文字をそのまま入れる。正しさは自己テスト・監査・まこさんの目が見る |
| **コードの中身を誰が書くか** | 案の【4-20】に CC が書く。道具で作ることはできない |
| **承認済みの設計書が無いときの手の直し** | hook 12 は、承認済みの設計書に実装の指示が在る間だけ止める。承認の要らない hook と道具（gen_ の名前）は、設計書が無ければ止めない |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=e88c1f3443158e47 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝道具2本と hook 1本（apply_audit_fix.py・gen_acceptance.py・enforce_audit_fix.py）。売買のロジックに触らない。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝apply_audit_fix.py）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しいファイルを作らない（NEW_FILE・MODEL の行は無い）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（設計書の実装を、当てる道具だけが書く形にする）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝案を出す前に写しで試した（1点目で、承認の後に自己テストが落ちて承認を繰り返した型を避ける）。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 非該当（売買のロジックの部品・前処理を足さない）。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 非該当（売買の実行器と生成器を直さない）。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前で壊すプログラムを grep した。探す行は変えない（4-13）。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 非該当（壊すプログラムを足さない。自己テストは一時の置き場だけに書く）。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 触る関数は DESIGN_CONTRACT の impl_functions に全部 在る（3本とも git の差分が無い状態から数えた）。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足す旗は無い。完成の条件の4行が --selftest で通る。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 非該当（2回目の承認の前に書き直す＝その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=point2-design-to-impl-20260930）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝当てる道具と設計書の道具の --selftest と、承認の前の検査の --try。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 承認と TARGET／NEW_FILE がそろった道具・hook・壊すプログラムにだけ当てる | `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | 道具 | tool_target_ok をいつも真にする | `b118_audit_fix_tools_target.sh` | 要 | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝道具のファイルに当ててよいかの照らし（承認の印と TARGET）を常に真にすると、当てる道具の自己テスト T18・T19（印が違う・TARGET の外なら当てない）が落ちた |
| 2 | 実物と合わない件が1件でも在れば1件も当てない | `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | 道具 | 全件を先に確かめる処理と当てる直前の確かめを外す | `b102_design_apply_no_precheck.sh` | 要 | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝全件を先に確かめる処理と当てる直前の確かめを外して、確かめながら当てる形にすると、当てる道具の自己テスト T13・T16（半分だけ当てない）が落ちた |
| 3 | 承認の印が合わなければ1件も当てない | `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | 道具 | 承認の印の照らしをいつも真にする | `b101_design_apply_no_approval.sh` | 要 | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝承認の印を照らす処理を常に真にすると、当てる道具の自己テスト T4（印が違えば当てない）が落ちた |
| 4 | 設計書の道具の自己テストが、4-20 が0件の設計書を止め、今までの場面も通る | `python3 ../../.claude/tools/gen_acceptance.py --selftest` | 道具 | verify を中身を見ずに通す形にする | `b72_acceptance_handwritten.sh` | 要 | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝その検査が落ちた（守りが働いた） |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=307a1e74b7667ce6 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`../../.claude/tools/apply_audit_fix.py`

| 触る関数 | 定義の行 |
|---|---|
| `new_file_check` | 405 |
| `design_key` | 399 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 22件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=5e897083dd85d59c gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "../../.claude/tools/apply_audit_fix.py",
  "self_check_calls": [
    "new_file_check",
    "design_key"
  ],
  "impl_functions": {
    "../../.claude/tools/apply_audit_fix.py": [
      "<モジュール直下>",
      "tool_target_ok",
      "design_key",
      "new_file_check",
      "check_one",
      "main",
      "selftest"
    ],
    "../../.claude/hooks/enforce_audit_fix.py": [
      "pending",
      "main"
    ],
    "../../.claude/tools/gen_acceptance.py": [
      "page",
      "_sample_work",
      "selftest"
    ]
  },
  "must_use": {
    "check_one": [
      "new_file_check"
    ],
    "main": [
      "design_key"
    ]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "この工事の道具が外から読む一覧（承認の印・設計書の TARGET と NEW_FILE・当てた記録の形）の形は変えない",
  "generated_from": {
    "impl_functions": "4-3 に書いた、この工事で触る関数（3本とも git の差分が無い状態から数えた）",
    "must_use": "直した後に呼ぶ名前（4-3）",
    "spec_lists": "空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "../../.claude/tools/apply_audit_fix.py",
 "public_functions": {
  "repo_path": [],
  "never_write": [
   "repo_path"
  ],
  "read_fixes": [],
  "read_design_blocks": [],
  "read_design_fixes": [
   "read_design_blocks"
  ],
  "approved_ok": [],
  "design_targets": [
   "repo_path"
  ],
  "tool_target_ok": [
   "approved_ok",
   "design_targets",
   "repo_path"
  ],
  "command_argv": [],
  "run_commands": [],
  "impl_src_mismatch": [],
  "applied_keys": [],
  "design_key": [],
  "new_file_check": [],
  "check_one": [
   "check_evidence",
   "command_argv",
   "never_write",
   "new_file_check",
   "repo_path",
   "tool_target_ok"
  ],
  "check_evidence": [
   "repo_path"
  ],
  "apply_one": [],
  "main": [
   "apply_one",
   "approved_ok",
   "check_one",
   "command_argv",
   "design_key",
   "design_targets",
   "impl_src_mismatch",
   "read_design_blocks",
   "read_design_fixes",
   "read_fixes",
   "repo_path",
   "run_commands",
   "selftest"
  ],
  "selftest": [
   "applied_keys",
   "check_one",
   "command_argv",
   "main",
   "read_design_blocks",
   "run_commands"
  ]
 },
 "constants": {
  "ROOT": "/Users/tachiharamasako/Documents/GitHub/cat-bitget",
  "AUDITED_DESIGN": ""
 },
 "cli_flags": [
  "--dry-run",
  "--selftest",
  "--summary",
  "--verify",
  "--work",
  "--write"
 ]
}
```

<!-- ACC_SPEC_END -->

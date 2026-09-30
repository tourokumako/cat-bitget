<!-- ARC iter="point5-report-direct-20260930" -->

# 設計書｜5点目＝監査結果から直接、当てる道具が実装を直せるようにする

TARGET: .claude/tools/apply_audit_fix.py

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `point5-report-direct-20260930/ok_point5b_20260930`・`point5-report-direct-20260930/okd_point5b_20260930`・`point5-report-direct-20260930/req_point5b_20260930`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/point5-report-direct-20260930/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work point5-report-direct-20260930 --write`。検出＝`--work point5-report-direct-20260930 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=ddeb1f67cb8eb08f gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/point5-report-direct-20260930/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/point5-report-direct-20260930/ok_point5b_20260930.txt`（まこさんの発言）・`verbatim/point5-report-direct-20260930/okd_point5b_20260930.txt`（まこさんが OK した CC の文）・`verbatim/point5-report-direct-20260930/req_point5b_20260930.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝274 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_point5b_20260930` | V01〜V03（3 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_point5b_20260930` | V01〜V03（3 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_point5b_20260930` | V04〜V08（5 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V09〜V11（3 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V12〜V16（5 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V17〜V23（7 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V24〜V29（6 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V30〜V33（4 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V34〜V35（2 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V36〜V37（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V38〜V39（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V40〜V41（2 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V42〜V43（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V44〜V45（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V46〜V50（5 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V51〜V54（4 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V55〜V56（2 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V57〜V58（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V59〜V60（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V61〜V62（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V63〜V64（2 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V65〜V179（115 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V180〜V186（7 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V187〜V191（5 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V192〜V196（5 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V197〜V203（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V204〜V205（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V206〜V207（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V208〜V219（12 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V220〜V240（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V241〜V251（11 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V252〜V265（14 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_point5b_20260930` | V266〜V269（4 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `req_point5b_20260930` | V01〜V02（2 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
まこさんの要望「監査結果から直接自動生成で実装を修正できるようにしろ」に対し、当てる道具の --report の道の穴3つを塞ぐ。①使わなくなった元データの件で全件が止まる ②確かめのコマンドの多くを走らせない ③印の取り直しを走らせない。承認のプログラムは まこさんだけが打つので入れない。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 当てる道具に、scripts の道具の一覧が在るか | `grep -c 'RUN_SCRIPTS' .claude/tools/apply_audit_fix.py` | 実装の前は無い。実装の後は在る | 4（終了コード 0） |

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
| 1 | 承認のプログラムを走らせる形にはしない | 承認は まこさんだけが打つ | worklog 20260930 §73 |
| 2 | pre_audit_check.py の --run は入れない | 何をするかを、この工事で確かめていない | worklog 20260930 §73 |
| 3 | 守りの仕組みに、承認なしで当てる形にはしない | 承認済みの設計書の TARGET のときだけ当てる守りを外さない | worklog 20260930 §73 |
| 4 | 新しい壊すプログラムを作らない | 恒久71番＝BOT の中身に関わらない道具に過剰なテストを付けない | worklog 20260930 §64 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 承認の後、当てる道具を まこさんの端末で1回 打っていただいてよいか（当てる道具そのものが相手なので、設計↔実装ゲートが私の実行を止めるため） | 打っていただく。リポジトリの直下で python3 .claude/tools/apply_audit_fix.py --design | worklog 20260930 §35 |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
当てる道具 apply_audit_fix.py の --report の道で、監査結果から直接 実装を直すときの穴3つを塞ぐ。
①使わなくなった元データ（acceptance_src.json）の件で全件を止めず、［手書き］で分けてほかの件は当てる。
②確かめのコマンド（scripts/priority_rebuild の一覧に載せた道具・パスを値に取るもの）も、一覧の形なら走らせる。承認のプログラムは入れない。
③印（G2・H2）の対象のファイルを直したら、G2 → H2 の順で印を取り直す。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
動かすのは まこさん（承認と、当てる道具を1回）と CC（自己テスト）。
書くのは当てる道具だけ（TARGET の1本）。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
入力＝承認された設計書の 4-20 の実装の指示11件と、承認の印。
出力＝当てる道具の定数3つ（RETIRED_SOURCES・SCRIPTS_DIR と RUN_SCRIPTS・PASS_MARKS）。
あわせて check_one・hand_label・command_argv・main・selftest を直す。
当てた記録には11行を書く（名前 design:point5-report-direct-20260930）。

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
- apply_audit_fix の <モジュール直下>＝定数 RETIRED_SOURCES・SCRIPTS_DIR・RUN_SCRIPTS・PASS_MARKS を足す。RUN_TOOLS に2本を足す。
- apply_audit_fix.check_one＝使わなくなった元データの件を「使わなくなった元データなので当てない」で返す。
- apply_audit_fix.hand_label＝この理由に「［手書き］CC が写す」の印を付ける。
- apply_audit_fix.command_argv＝RUN_SCRIPTS の道具も通す。値にリポジトリの中のパスを許す（「..」は不可）。
- apply_audit_fix.main＝使わなくなった元データの件で全件を止めない。当てたファイルが印の対象なら、G2 → H2 を走らせるコマンドに足す。
- apply_audit_fix.selftest＝T37・T38・T39 を足す。

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
- ①まこさんが承認する。
- ②まこさんが端末で当てる道具を1回 打つ。
- ③道具が実装の指示11件を当て、当てた記録に書く。
- ④CC が設計書を作り直し、自己テストと壊すプログラムを走らせる。
- ⑤2回目の承認。壊すプログラムが「—」の行は、承認のプログラムが測らないので未着手のまま残る（run_breaks.py:176）＝中身は自己テストで見る。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝実装の監査結果に engine_tuner_gen.py の直しと、確かめのコマンド engine_tuner_gen.py --selftest が書いてある。①道具が直しを当てる ②engine_tuner_gen.py は印の対象なので、G2 → H2 を走らせるコマンドに足す ③照合が通れば、確かめのコマンド → G2 → H2 の順に走らせる ④acceptance_src.json の件は［手書き］で分ける。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
- 使わなくなった元データの件は「［手書き］CC が写す」で出て、全件が止まらない。
- 確かめのコマンドは、道具が走らせて終了コードを出す。
- 印の対象を直したときは「G2 → H2 の印を取り直す」と出る。
- 自己テストが 39/39 になる。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
- 直す前の文字がちょうど1か所でない＝当てる道具が1件も当てない。
- 走らせる前の照合が通らない＝コマンドを1つも走らせない。
- ほかの在らないファイル・一覧に無いコマンド＝いままでどおり止める。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
当てた記録＝SDK/.claude/audits/applied_fixes.json に書き足す。ほかに新しいファイルは作らない。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
4-12 の出力が増える。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
- 直すファイルの名前で壊すプログラムを grep すると、b101・b102・b118・b119・b121。どれも、この工事で直す行を探していない（b118 は説明の行に語が在るだけ）。
- 自己テストの T20（一覧の形のコマンドだけ通す）は、直した後も通る（写しで 39/39）。
- hook 12 は、この工事では変えない。

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
手本＝RUN_TOOLS と command_argv の形・前の工事の逐語のファイルの分かれ道と自己テストの T35。

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=accd43d02c0e8088 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 当てた監査結果の名前の定数の後ろに、使わなくなった元データの定数を足す
直す前の文字:
~~~
#   already_applied が当てた記録と照らす（当てた後の工事で同じ所が書き替わっても、当て終わりと分かる）。
CURRENT_REPORT = ""
~~~
足す文字:
~~~

# ★2026-09-30（工事 point5-report-direct-20260930）＝使わなくなった元データ（ratchet に無い）。監査結果の修正がこれを相手にしていたら、
#   全件を止める理由にせず、当てずに［手書き］で分ける（直す前は「対象のファイルが実在しない」で全件が止まった＝cp47・cp49）。
RETIRED_SOURCES = ("acceptance_src.json",)
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:103「#   already_applied が当てた記録と照らす（当てた後の工事で同じ所が書き替わっても、当て終わりと分かる）。」
状態: 確定

#### 実装 2
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: check_one の守りの仕組みの分かれ道の後ろで、使わなくなった元データを見分ける
直す前の文字:
~~~
        return False, f"守りの仕組みなので当てない（{rel}）＝私が Write ツールで直す", ""
~~~
足す文字:
~~~

    # ★2026-09-30（工事 point5-report-direct-20260930）＝使わなくなった元データを相手にした件は当てない（全件を止める理由にしない）
    if os.path.basename((rel or "").strip().strip("`")) in RETIRED_SOURCES and not os.path.isfile(repo_path(rel)):
        return False, f"使わなくなった元データなので当てない（{rel}）＝直す中身を、工事のフォルダの元へ写す", ""
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:463「return False, f"守りの仕組みなので当てない（{rel}）＝私が Write ツールで直す", ""」
状態: 確定

#### 実装 3
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: hand_label に、使わなくなった元データの印を足す
直す前の文字:
~~~
        return "［手書き］次の案に まこさんの OK が要る"
~~~
足す文字:
~~~

    if why.startswith("使わなくなった元データ"):
        return "［手書き］CC が写す（手書きの項目は やることの表.md へ・自動の項目は次の案に まこさんの OK が要る）"
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:626「return "［手書き］次の案に まこさんの OK が要る"」
状態: 確定

#### 実装 4
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: main の全件を止めない理由に、使わなくなった元データを足す
直す前の文字:
~~~
"TARGET の外", "逐語のファイル"))]
~~~
直した後の文字:
~~~
"TARGET の外", "逐語のファイル", "使わなくなった元データ"))]
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:775「"もう当て終わっている", "--choose で", "TARGET の外", "逐語のファイル"))]」
状態: 確定

#### 実装 5
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: selftest の T36 の後ろに T37 を足す
直す前の文字:
~~~
                fails.append(f"❌ 当てた記録 T{total}: 記録あり={why36} 記録を見ない={why36b}")
~~~
足す文字:
~~~


            # T37（2026-09-30・工事 point5-report-direct-20260930）＝使わなくなった元データを相手にした件は全件を止めず［手書き］で分け、ほかの件は当てる
            total += 1
            fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev),
                   item(2, "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json", "zz_old", "直した後の文字", "zz_new", ev)])
            rc37, out37 = run(["--design", md], mark)
            if (open(code).read() == "x = 2\n" and "使わなくなった元データなので当てない" in out37
                    and "［手書き］CC が写す" in out37 and "実物と合わない件が" not in out37):
                ok += 1
                print(f"   T{total} 使わなくなった元データの件は［手書き］で分け、ほかの件は当てる → pass")
            else:
                fails.append(f"❌ 使わなくなった元データ T{total}: rc={rc37} {out37[-200:]}")

            # T38（2026-09-30・工事 point5-report-direct-20260930）＝確かめのコマンド（scripts の道具・パスの値）も決まった形なら通し、外は止める
            total += 1
            sdk38, td38 = os.path.relpath(SDK, ROOT), os.path.relpath(tdir, ROOT)
            good38 = [f"python3 {td38}/gen_s22_map.py --verify",
                      f"python3 {td38}/run_breaks.py --design .claude/state/acceptance.md --measure-only",
                      f"cd {sdk38} && python3 scripts/priority_rebuild/verify_design_contract.py --diff {ROOT}/.claude/state/acceptance.md",
                      f"cd {sdk38} && python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest",
                      f"cd {sdk38} && python3 scripts/priority_rebuild/leak_causality_diag.py"]
            bad38 = [f"python3 {td38}/run_breaks.py --design ../../x --measure-only",
                     f"cd {sdk38} && python3 scripts/priority_rebuild/verify_design_contract.py --diff /etc/passwd",
                     f"cd {sdk38} && python3 scripts/priority_rebuild/score.py --selftest",
                     f"python3 {td38}/gen_acceptance.py"]
            miss38 = [c for c in good38 if command_argv(c) is None] + [c for c in bad38 if command_argv(c) is not None]
            if not miss38:
                ok += 1
                print(f"   T{total} 確かめのコマンドも決まった形なら通し、外は止める（通す {len(good38)}・止める {len(bad38)}） → pass")
            else:
                fails.append(f"❌ 確かめのコマンド T{total}: 見分けを誤った {miss38}")

            # T39（2026-09-30・工事 point5-report-direct-20260930）＝印の対象のファイルを直したら G2 → H2 を走らせるコマンドに足す（対象でなければ足さない）
            total += 1
            g39 = os.path.join(tmp, "g2_zz.json")
            json.dump({"files": [rel]}, open(g39, "w", encoding="utf-8"))
            got39 = []
            saved39 = (globals()["PASS_MARKS"], globals()["run_commands"])
            globals()["run_commands"] = lambda cmds, *a, **k: (got39.append(" ".join(" ".join(x[1][1][1:]) for x in cmds)) or 0)
            try:
                globals()["PASS_MARKS"] = (g39,)
                fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
                rc39, out39 = run(["--design", md], mark)
                globals()["PASS_MARKS"] = ()
                fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2", ev)])
                rc39b, out39b = run(["--design", md], mark)
            finally:
                globals()["PASS_MARKS"], globals()["run_commands"] = saved39
            if (len(got39) == 2 and "gen_signal_families.py --verify" in got39[0] and "leak_causality_diag.py" in got39[0]
                    and got39[1] == "" and "G2 → H2 の印を取り直す" in out39):
                ok += 1
                print(f"   T{total} 印の対象のファイルを直したら G2 → H2 を走らせる（対象でなければ走らせない） → pass")
            else:
                fails.append(f"❌ 印の取り直し T{total}: {got39} rc={rc39}/{rc39b}")
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:1406「fails.append(f"❌ 当てた記録 T{total}: 記録あり={why36} 記録を見ない={why36b}")」
状態: 確定

#### 実装 6
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 走らせる道具の一覧に、確かめのコマンドを足し、scripts の一覧と印の置き場の定数を足す
直す前の文字:
~~~
    "gen_verbatim.py": {"--verify": 1, "--summary": 1},
}
~~~
直した後の文字:
~~~
    "gen_verbatim.py": {"--verify": 1, "--summary": 1},
    "gen_s22_map.py": {"--verify": 0},
    "run_breaks.py": {"--design": 1, "--measure-only": 0},
}
# ★2026-09-30（工事 point5-report-direct-20260930）＝監査結果の「走らせるコマンド」のうち、確かめのコマンドは scripts/priority_rebuild の道具も走らせる
#   （直す前は .claude/tools の2本だけで、verify_design_contract・engine_tuner_gen・印の取り直しは まこさんが打った）。承認のプログラムは入れない。
SCRIPTS_DIR = os.path.join(SDK, "scripts", "priority_rebuild")
RUN_SCRIPTS = {
    "verify_design_contract.py": {"--diff": 1},
    "engine_tuner_gen.py": {"--selftest": 0},
    "gen_signal_families.py": {"--verify": 0},
    "leak_causality_diag.py": {},
}
# ★同＝印（G2・H2）の対象のファイルの一覧の置き場。ここに在るファイルを直したら、G2 → H2 の順で印を取り直す
PASS_MARKS = (os.path.join(ROOT, ".claude", "state", "g2_pass.json"), os.path.join(ROOT, ".claude", "state", "h2_pass.json"))
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:92「"gen_verbatim.py": {"--verify": 1, "--summary": 1},」
状態: 確定

#### 実装 7
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: command_argv の説明の文を、広げた形に合わせる
直す前の文字:
~~~
    その道具の旗（旗ごとに決まった数の値＝英数字・_・.・- だけ）。区切り・置き換え・リダイレクトの記号が在れば None。
~~~
直した後の文字:
~~~
    その道具の旗（旗ごとに決まった数の値＝英数字・_・.・-・/ だけ。「..」は不可・/ で始まる値はリポジトリの中だけ）。
    scripts/priority_rebuild の道具は RUN_SCRIPTS の分だけ（旗の無い道具も一覧に在れば通す）。区切り・置き換え・リダイレクトの記号が在れば None。
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:249「その道具の旗（旗ごとに決まった数の値＝英数字・_・.・- だけ）。区切り・置き換え・リダイレクトの記号が在れば None。」
状態: 確定

#### 実装 8
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: command_argv で、旗の無い道具も数に入れる
直す前の文字:
~~~
    if len(toks) < 3 or toks[0] != "python3":
~~~
直した後の文字:
~~~
    if len(toks) < 2 or toks[0] != "python3":
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:268「if len(toks) < 3 or toks[0] != "python3":」
状態: 確定

#### 実装 9
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: command_argv で、scripts/priority_rebuild の一覧も見る
直す前の文字:
~~~
    rule = RUN_TOOLS.get(os.path.basename(tool))
    if rule is None or os.path.dirname(tool) != os.path.realpath(TOOLS_DIR):
        return None
    rest, i = toks[2:], 0
~~~
直した後の文字:
~~~
    # ★2026-09-30（工事 point5-report-direct-20260930）＝.claude/tools は RUN_TOOLS、scripts/priority_rebuild は RUN_SCRIPTS
    table = {os.path.realpath(TOOLS_DIR): RUN_TOOLS, os.path.realpath(SCRIPTS_DIR): RUN_SCRIPTS}.get(os.path.dirname(tool)) or {}
    rule = table.get(os.path.basename(tool))
    if rule is None:
        return None
    rest, i = toks[2:], 0
    if not rest and rule:
        return None                                        # 旗を持つ道具を旗なしで走らせない
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:271「rule = RUN_TOOLS.get(os.path.basename(tool))」
状態: 確定

#### 実装 10
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: command_argv で、値にリポジトリの中のパスを許す
直す前の文字:
~~~
        if n and (i + 1 >= len(rest) or not re.fullmatch(r"[A-Za-z0-9_.-]+", rest[i + 1])):
~~~
直した後の文字:
~~~
        v = rest[i + 1] if i + 1 < len(rest) else ""
        if n and (not re.fullmatch(r"[A-Za-z0-9_./-]+", v) or ".." in v.split("/")
                  or (v.startswith("/") and not os.path.realpath(v).startswith(ROOT + os.sep))):
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:279「if n and (i + 1 >= len(rest) or not re.fullmatch(r"[A-Za-z0-9_.-]+", rest[i + 1])):」
状態: 確定

#### 実装 11
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: main で、印の対象のファイルを直したら G2 → H2 の取り直しを走らせるコマンドに足す
直す前の文字:
~~~
    rc_cmd = run_commands(cmds)
~~~
直した後の文字:
~~~
    # ★2026-09-30（工事 point5-report-direct-20260930）＝印（G2・H2）の対象のファイルを直したら、G2 → H2 の順で印を取り直す（next_step の決まり）
    touched = {os.path.relpath(p, ROOT) for _f, _w, p in plan}
    hit = False
    for mk in PASS_MARKS:
        try:
            hit = hit or bool(touched & set(json.load(open(mk, encoding="utf-8")).get("files") or []))
        except (OSError, ValueError):
            pass
    if hit:
        print("— 印の対象のファイルを直したので、G2 → H2 の印を取り直す")
        for s in ("gen_signal_families.py --verify", "leak_causality_diag.py"):
            cmds.append(({"番号": "印"}, command_argv(
                f"cd v3-bitget-api-sdk/bitget-python-sdk-api && python3 scripts/priority_rebuild/{s}")))
    rc_cmd = run_commands(cmds)
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:859「rc_cmd = run_commands(cmds)」
状態: 確定

<!-- ACC_IMPL_END -->

［自動］まこさんが OK した案の【番号】の「非該当＝」の後ろの文と、項目の正本の名前
**非該当の項目（理由と出どころ）**＝4-6 制約（従う決まりの全件と、その出どころ）＝相場の法則・型の表・承認を受けた設定を使わない道具の直し／4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）＝値の範囲を探す工事ではない／4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）＝旗を足さない／4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）＝表や JSON の形は変えない／4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）＝時刻の列・足の区切りに触らない／4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）＝印の取り直しは H2 が約5分かかるが、印の対象を直したときだけ走る／4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）＝同時に2つ走らせない／4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）＝鍵・本番の発注に触らない。承認のプログラムは走らせない。値のパスはリポジトリの中だけ

### 4-A この節に何を書いたか（一覧）

［自動］項目の正本と、OK された案・やることの表の有無
| 番号 | 段 | 項目 | 書いたか |
|---|---|---|---|
| 4-0 | 必ず | この仕組みは何か（全体・一続きの文章で書く） | 書いた |
| 4-1 | 必ず | システムの境界（誰が動かし、誰が結果を使うか） | 書いた |
| 4-2 | 必ず | 入力と出力（受け取るもの・出すもの・その形） | 書いた |
| 4-6 | 条件 | 制約（従う決まりの全件と、その出どころ） | 非該当（相場の法則・型の表・承認を受けた設定を使わない道具の直し） |
| 4-3 | 必ず | 部品と責任の割り当て（どの部品が何をやるか） | 書いた |
| 4-4 | 必ず | 処理の流れ（うまくいったとき、何がどの順に起きるか） | 書いた |
| 4-19 | 必ず | 通しの例（最初から最後まで、1件を追いかけた例） | 書いた |
| 4-7 | 条件 | 探索の範囲（決める値と、その探し方＝範囲・並び・本数） | 非該当（値の範囲を探す工事ではない） |
| 4-9 | 条件 | 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗） | 非該当（旗を足さない） |
| 4-12 | 必ず | 出る結果の姿（完成したとき、何がどう表示されるか） | 書いた |
| 4-5 | 必ず | 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか） | 書いた |
| 4-8 | 条件 | データ構造（表や JSON の列と中身を、新しく作るか・変えるか） | 非該当（表や JSON の形は変えない） |
| 4-10 | 条件 | 保存先（出したものをどこに置くか・上書きか、書き足すか） | 書いた |
| 4-11 | 条件 | 時刻の扱い（時間帯・足の区切りをどこで切るか） | 非該当（時刻の列・足の区切りに触らない） |
| 4-14 | 条件 | 性能（どれくらい時間が掛かり、どれくらい容量を使うか） | 非該当（印の取り直しは H2 が約5分かかるが、印の対象を直したときだけ走る） |
| 4-15 | 条件 | 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか） | 非該当（同時に2つ走らせない） |
| 4-16 | 条件 | セキュリティ（人に見せてはいけない値と、書き換えられては困る記録） | 非該当（鍵・本番の発注に触らない。承認のプログラムは走らせない。値のパスはリポジトリの中だけ） |
| 4-17 | 省ける | ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか） | 書いた |
| 4-13 | 必ず | 影響範囲（この直しで、ほかのどれが壊れるか） | 書いた |
| 4-18 | 省ける | 再利用（手本にした、既にあるものの形） | 書いた |
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 11 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 使わなくなった元データは、名前の一覧で見分ける | 在らないファイルを全部 見逃すと、打ち間違いの件まで黙って飛ばす | 在らないファイルの件を全部［手書き］にする |
| 2 | 走らせるコマンドは、道具と旗の一覧で決める | 一覧の外のコマンドを走らせない守りを保つ | どのコマンドも走らせる |
| 3 | 承認のプログラムは入れない | 承認は まこさんだけが打つ | 承認も道具が打つ |
| 4 | 新しい壊すプログラムは作らない | 恒久71番 | 壊すプログラムを足す |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=8089bc81b35c59b7 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `—` | #1・#2・#3 | — |
| `b118_audit_fix_tools_target.sh` | #4 | tool_target_ok をいつも真にする |
| `b102_design_apply_no_precheck.sh` | #5 | 全件を先に確かめる処理と当てる直前の確かめを外す |
| `b101_design_apply_no_approval.sh` | #6 | 承認の印の照らしをいつも真にする |
| `b119_audit_fix_command_allow.sh` | #7 | command_argv がどのコマンドにも置き場と引数を返す |
| `b121_hook12_design_guard.sh` | #8 | pending の「承認中の設計書の TARGET を守る」を外す |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 新しい定数と関数の直しで、承認がもう1回 要る | 2回目の承認で完成の条件の行を済にする |
| 2 | 壊すプログラムが「—」の行は承認で済にならない | 承認の後に自己テストを直接 走らせる |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（まこさんの端末で1回） | 1分以内 | 11件の直し（写しで当てた） |
| 自己テストと壊すプログラム5本 | 数分 | 前の工事で同じ自己テストと壊すプログラムを測った（秒は測っていない） |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝当てる道具が、使わなくなった元データの件で全件を止め、確かめのコマンドと印の取り直しを走らせなかった

**② 期待値分解**＝売買に触れないので、勝率・平均利益・敗率・平均損失は動かない

**③ root か symptom か**＝root。止める理由・走らせる一覧・印の取り直しを道具に入れる

**④ ベースアップ**＝手本は RUN_TOOLS と command_argv の形（4-18）

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
疑似シミュから取った値は1つもない。数字を決める工事ではない。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝当てる道具が、監査結果から直接 実装を直すときの穴を塞ぐ。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

［自動］TARGET と NEW_FILE から非該当を決めた
**非該当。**この工事の直す相手（TARGET・NEW_FILE）に、売買のロジック（scripts/priority_rebuild・engine_tuner）が無い（プログラムが TARGET と NEW_FILE から決めました）。

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **承認のプログラム** | 道具は走らせない。まこさんが打つ |
| **当てた後の文の正しさ** | 道具は見ない（監査が書いた文字をそのまま入れる） |
| **同じ事実を書いたほかの場所** | 道具は揃えない |
| **一覧に無い名前の使わなくなった元データ** | いままでどおり全件を止める |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=2f5770ba2ec5fd04 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝道具1本（apply_audit_fix.py）。売買のロジックに触らない。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝apply_audit_fix.py）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しいファイルは作らない。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（監査結果から直接 実装を直すときの穴を塞ぐ）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝直す前の文字11件が実物にちょうど1か所ずつ在ること、壊すプログラムが直す行を探していないことを確かめた（worklog 20260930 §74）。定数を関数の外に足すので impl_functions に「<モジュール直下>」を書いた。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 非該当（売買のロジックの部品・前処理を足さない）。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 非該当（売買の実行器と生成器を直さない）。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前で壊すプログラムを grep した。探す行は変えない（4-13）。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 非該当（壊すプログラムを新しく作らない）。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 触る所＝モジュール直下・check_one・hand_label・command_argv・main・selftest。DESIGN_CONTRACT の impl_functions に全部 在る。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足す旗は無い。完成の条件の行が --selftest で通る。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 非該当（2回目の承認の前に書き直す＝その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=point5-report-direct-20260930）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝当てる道具の --selftest と、承認の前の検査の --try。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 使わなくなった元データを相手にした件は、全件を止めず［手書き］で分け、ほかの件は当てる | `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | 道具 | — | `—` | 要 | **未着手** |
| 2 | 確かめのコマンドも一覧の形なら走らせ、一覧の外とリポジトリの外のパスは止める | `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | 道具 | — | `—` | 要 | **未着手** |
| 3 | 印の対象のファイルを直したら G2 → H2 を走らせる | `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | 道具 | — | `—` | 要 | **未着手** |
| 4 | 承認と TARGET／NEW_FILE がそろった道具・hook・壊すプログラムにだけ当てる | `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | 道具 | tool_target_ok をいつも真にする | `b118_audit_fix_tools_target.sh` | 要 | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝道具のファイルに当ててよいかの照らし（承認の印と TARGET）を常に真にすると、当てる道具の自己テスト T18・T19（印が違う・TARGET の外なら当てない）が落ちた |
| 5 | 実物と合わない件が1件でも在れば1件も当てない | `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | 道具 | 全件を先に確かめる処理と当てる直前の確かめを外す | `b102_design_apply_no_precheck.sh` | 要 | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝全件を先に確かめる処理と当てる直前の確かめを外して、確かめながら当てる形にすると、当てる道具の自己テスト T13・T16（半分だけ当てない）が落ちた |
| 6 | 承認の印が合わなければ1件も当てない | `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | 道具 | 承認の印の照らしをいつも真にする | `b101_design_apply_no_approval.sh` | 要 | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝承認の印を照らす処理を常に真にすると、当てる道具の自己テスト T4（印が違えば当てない）が落ちた |
| 7 | 一覧に無い形のコマンドは走らせない | `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | 道具 | command_argv がどのコマンドにも置き場と引数を返す | `b119_audit_fix_command_allow.sh` | 要 | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝走らせるコマンドの形の照らしを常に通すと、当てる道具の自己テスト T20（決まった形だけ通す）が落ちた |
| 8 | hook 12 が、承認中の設計書の TARGET を CC の手の直しから守る | `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | hook | pending の「承認中の設計書の TARGET を守る」を外す | `b121_hook12_design_guard.sh` | 要 | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝hook 12 が承認済みの設計書の TARGET を守る処理を外すと、当てる道具の自己テスト T31 が落ちた |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=6b33034a82e80de5 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`../../.claude/tools/apply_audit_fix.py`

| 触る関数 | 定義の行 |
|---|---|
| `RETIRED_SOURCES` | （この関数は実物に無い） |
| `RUN_SCRIPTS` | （この関数は実物に無い） |
| `PASS_MARKS` | （この関数は実物に無い） |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 25件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=8b7ac9eade985006 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "../../.claude/tools/apply_audit_fix.py",
  "self_check_calls": [
    "RETIRED_SOURCES",
    "RUN_SCRIPTS",
    "PASS_MARKS"
  ],
  "impl_functions": {
    "../../.claude/tools/apply_audit_fix.py": [
      "<モジュール直下>",
      "check_one",
      "hand_label",
      "command_argv",
      "main",
      "selftest"
    ]
  },
  "must_use": {
    "check_one": [
      "RETIRED_SOURCES"
    ],
    "command_argv": [
      "RUN_SCRIPTS"
    ],
    "main": [
      "PASS_MARKS"
    ]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "この工事の道具が外から読む一覧（承認の印・設計書の TARGET・当てた記録の形）の形は変えない",
  "generated_from": {
    "impl_functions": "4-3 に書いた、この工事で触る所（git の差分が無い状態から数えた）",
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
   "already_applied",
   "check_evidence",
   "command_argv",
   "is_verbatim",
   "never_write",
   "new_file_check",
   "repo_path",
   "tool_target_ok"
  ],
  "check_evidence": [
   "repo_path"
  ],
  "apply_one": [],
  "already_applied": [
   "applied_keys",
   "repo_path"
  ],
  "is_verbatim": [
   "repo_path"
  ],
  "hand_label": [],
  "main": [
   "apply_one",
   "approved_ok",
   "check_one",
   "command_argv",
   "design_key",
   "design_targets",
   "hand_label",
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
   "hand_label",
   "main",
   "read_design_blocks",
   "repo_path",
   "run_commands"
  ]
 },
 "constants": {
  "ROOT": "/Users/tachiharamasako/Documents/GitHub/cat-bitget",
  "AUDITED_DESIGN": "",
  "CURRENT_REPORT": ""
 },
 "cli_flags": [
  "--design",
  "--diff",
  "--dry-run",
  "--measure-only",
  "--selftest",
  "--summary",
  "--verify",
  "--work",
  "--write"
 ]
}
```

<!-- ACC_SPEC_END -->

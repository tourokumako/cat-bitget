#!/usr/bin/env python3
"""gen_audit_docs.py — 監査の依頼書をテンプレから作り、依頼書から結果の骨組みを作り、2つを照らす。

まこさん指示 2026-09-15（逐語）＝「じゃあ、監査の依頼書と結果で項目をそろえて、テンプレ以外では書かないように
  強制すればいいじゃん。」／置き場所＝「案AでOK」（.claude/tools に新しい道具を作る）。

なぜ要るか
  監査レポート CP37 を監査結果のテンプレに当てはめたら、齟齬とヌケモレが多数出た（worklog 20260915 §11）。
  原因の1つ＝依頼書をテンプレから作っていなかった（cp37 の依頼書は CC が手で書いた）。
  gen_audit_request.py は中身の取り出し元が RG-v5 に決め打ちで（102〜109行の SOURCES）、ほかの監査の依頼書を作れない。

テンプレ＝SDK/.claude/audits/inputs/_template.md
  依頼の側＝「## 」の見出しの節。結果の側＝「## 結果ファイルフォーマット」の11節の表。
  ★節の名前はテンプレから読む。この道具に節の名前の一覧を焼かない（下の SECTION_KIND は「どう埋めるか」だけ）。

使い方
  python3 .claude/tools/gen_audit_docs.py request-design <design|impl> --work <工事名> [--design <承認の控えの設計書>]
    → ★2026-10-07（まこさん「A」）＝--design を付けると、いまの設計書の代わりに その設計書（acceptance_archive/<工事名>.md）を読む。
    → ★2026-09-29（まこさん指示「監査依頼書を自動生成」）＝設計書（.claude/state/acceptance.md）と
      その工事のフォルダ（やることの表.md と逐語のファイル）から、依頼書の元データと依頼書を道具が作る。CC は元データを書かない。
      ★2026-09-30（設計書 point1-one-way-20260930-2）＝--work だけを受ける（元データの JSON から作る古い口は消した）。
      問いは、設計のもとの1行ごと（V）・完成の条件の1行ごと（C）・実装の指示の1件ごと（I）・
      やらないことの1件ごと（N）・CC が決めたことの1件ごと（D）に1つずつ作る。監査の番号（cp）は次の空き番号。
      元データは作業場 SDK/.claude/audits/cp<N>_work/cp<N>_src.gen.md に、依頼書は inputs に書く。
  python3 .claude/tools/gen_audit_docs.py request <元データ.md> <依頼書.md>
    → 元データ（下の形）とテンプレから依頼書を作る。★2026-09-29 から、元データは request-design が作った物だけを受ける
      （1行目の目印と本文のハッシュ値を照らす＝CC が手で書いた元データの口は閉じた）。
    → ★2026-10-18（ToDo の15番・まこさん「設計書ナシや、例外的監査は、項目以外は手書きにすれば？」）＝設計書の無い直しの監査
      （メタの監査の種類＝「手書きの依頼」・依頼書の名前に _nodesign_・元データは作業場）だけは、CC が手で書いた元データを受ける。
      ★2026-10-18（192回目・まこさん決定「b」）＝手書きの依頼は、まこさんが指定した監査なら何でも使える。ひな型＝inputs/_hand_request_template.md。
  python3 .claude/tools/gen_audit_docs.py check-request <依頼書.md>
    → ★2026-10-18（ToDo の15番）＝出来上がった依頼書を、元データ（設計書から作った依頼書なら、設計書と設計書の元も）と照らす。何も書かない。
  python3 .claude/tools/gen_audit_docs.py result <依頼書.md> <結果.md>
    → 依頼書から結果の骨組み（11節・問いの見出し・事実データと外部検索と自己申告の見出し）を作る。中身は監査が書く。
  python3 .claude/tools/gen_audit_docs.py check <依頼書.md> <結果.md>
    → 2つが1対1で対応しているかを照らす。1件でも食い違えば rc=1。
  python3 .claude/tools/gen_audit_docs.py form <結果.md>
    → 中身を書いた結果が、テンプレの形（修正の指示の6つの欄・書けないもの・「<監査が書く>」の残り）かを見る。
      hook 11（enforce_audit_report_form）が、結果ファイルを書く瞬間に check と同じ判定を掛ける。

inputs に依頼書を書くときの照らし（★いまの監査依頼書ゲート＝require_acceptance_before_impl.sh の691〜772行と同じ）
  この道具は Python の中からファイルを書くので、Write の hook を通らない。守りを減らさないため、道具の中で同じことを見る。
  ①名前に _design_ を含まない依頼書＝設計書（.claude/state/acceptance.md）が承認の印（acceptance.approved）と同じ
  ②名前に _design_ を含む依頼書＝「監査の相手と版」のハッシュ値が設計書の sha256（「設計書のハッシュ値」の行は 2026-10-18 に消した＝同じ値を2回 出していた）
    （監査の相手が作業場の写しの設計書でもよい＝前の版の設計書を監査させる形。まこさん決定 2026-09-15「案A」）
  ③どちらも＝監査に出す前のチェック（pre_audit_check.py --verify）が rc=0

元データの形（CC が書くのは文だけ。ハッシュ値・保存先・件数・並びはプログラムが入れる）
  ★2026-10-18（192回目・ToDo の52番・まこさん「４つともOK」）＝依頼書の節を、監査の役割から組み直した
    （`.claude/state/audit_request_format_plan_20261018.md` の 3）。問う事は「確かめてほしいこと」の1か所。
    「結論を決める問い」「結論の決め方」「この監査の前提」「大目的の注記」「監査対象」「案内」は無くした。
  <!-- 項目: メタ -->                「キー: 値」の行＝日付・task・cp・題・依頼者・監査の種類・監査対象タスク・監査の相手（・直す相手）
  <!-- 項目: 作業場の指示 -->          無くてよい（監査人への宣言の「作業場」に入る）
  <!-- 項目: 目的と経緯 -->            「1. **この工事は何のためか**＝」「2. **この工事は何か**＝」から始める（3 結ぶ要件・4 経緯・5 なぜこの監査が要るか）
  <!-- 項目: 範囲の中 -->              監査の相手と、直す相手
  <!-- 項目: 範囲の外 -->              理由つき
  <!-- 項目: 問い 番号=Q1 優先度=A 理由=… 名前=… -->   何件でも（理由と名前は空白を含んでよい。この順に、名前を最後に書く）
                                      ★設計書の監査でない依頼には、固定の問い R0（要件定義の何番を満たす物か・反する所は無いか）が要る
  <!-- 項目: 外部検索 名前=… -->        何件でも（本文に「検索の言葉：」「調べる物：」の行）
  <!-- 項目: 外の基準が無い理由 -->    外部検索が0件のときだけ要る
  <!-- 項目: 自己申告 -->               1件につき1つ・何件でも（依頼書では「CC がまだ確かめていないこと」）
  <!-- 項目: 着手前必読 -->
  <!-- 項目: 事実データ 名前=… -->      何件でも
  <!-- 項目: 修正をどこに書くか -->    設計書は直接 直せないので、修正をどのファイルに書くか
  ★この一覧に無い項目は「テンプレに置き場が無い」として ❌ を出す（rc=1）。

書いてよい先（★この道具は Bash から走らせられるので、書く先を監査の置き場だけに限る）
  依頼書（request）＝①SDK/.claude/audits/inputs/<名前>_audit_request.md（「_」で始まる名前＝テンプレは書かない・
    既に在るファイルは、道具が作ったまま書き替えられておらず、その結果ファイルがまだ無いときだけ上書きする・
    下の照らしに ❌ が1件でもあれば書かない）②SDK/.claude/audits/<何か>_work/ の中の .md
  結果の骨組み（result）＝SDK/.claude/audits/<何か>_work/ の中の .md だけ
    （結果ファイルの置き場に骨組みを置くと、中身の無い結果が hook 11 を通らずに出来てしまうため）。

限界（正直に書く）
  ①依頼書の文の中身が正しいかは見ない（見るのは形と対応だけ）。
  ②プログラムが作る文書と元データの組は、設計書（.claude/state/acceptance.md → 工事のフォルダの やることの表.md）の1組だけを知っている。
  ③この道具自身を書き換えれば無効にできる（git diff には出る）。
  ④恒久71番＝文書を作る道具なので、壊すプログラムと自己テストは付けない。走らせて確かめる。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
AUDITS = os.path.join(SDK, ".claude", "audits")
TEMPLATE = os.path.join(AUDITS, "inputs", "_template.md")
DESIGN = os.path.join(ROOT, ".claude", "state", "acceptance.md")
APPROVED = os.path.join(ROOT, ".claude", "state", "acceptance.approved")
PRE_AUDIT_CHECK = os.path.join(ROOT, ".claude", "tools", "pre_audit_check.py")
INPUT_REQUEST_RE = re.compile(r"/\.claude/audits/inputs/[^/_][^/]*_audit_request\.md$")

# テンプレの依頼の側の見出し（先頭一致）→ どう埋めるか。この表に無い見出しがテンプレに在れば止める。
SECTION_KIND = (
    ("## ⚠️ 監査人への宣言", "宣言"),
    ("## 監査依頼メタ情報", "メタ"),
    ("## この監査は何のためか", "目的"),
    ("## 監査の範囲", "範囲"),
    ("## 確かめてほしいこと", "問い"),
    ("## 問いの外から当てる視点", "視点"),
    ("## CC がまだ確かめていないこと", "自己申告"),
    ("## 着手前必読", "着手前必読"),
    ("## 事実データ", "事実データ"),
    ("## 答えの出し方", "答え方"),
    ("## 起動の仕方", "テンプレ"),
)
KEYS_ONE = ("メタ", "目的と経緯", "着手前必読", "範囲の中", "範囲の外", "作業場の指示", "修正をどこに書くか", "外の基準が無い理由")
KEYS_MANY = ("事実データ", "問い", "外部検索", "自己申告")
META_KEYS = ("日付", "task", "cp", "題", "依頼者", "監査の種類", "監査対象タスク", "監査の相手")
# ★2026-10-18（192回目・まこさん「OK」）＝どの種類の監査にも入れる、要件定義を指す問い。設計書の監査には F1 と R が在るので、
#   設計書の監査でない依頼（実装の監査・手書きの依頼）に、道具（実装）か CC（手書き）が入れる。consistency_errors が在るかを見る。
# ★2026-10-21（199回目・まこさん「その書き方で良いので、依頼書の文章はすべてこの書き方にするように」）＝この下の決まった文は全部、
#   公用文作成の考え方の「文の書き方」13項目で書く（正本＝.claude/rules/chat_writing_rules.md の A2）。1つの文に、主語と目的語と述語を1つずつ入れる。
REQ_Q = ("R0", "A", "要件定義に反する直しや、要件のどれにも結び付かない直しが、そのまま進む",
         "この工事は、要件定義の何番を満たすための物か。要件定義に反する所は無いか",
         ("この工事が結ぶ要件は、この依頼書の「この監査は何のためか」の 3 に書いてあります。"
          "3 に「欄が無い」と書いてあるときは、3 に書いた読み方で、結ぶ要件を読み取ってください。",
          "要件定義の要約は、この依頼書の上の方に載っています。要件定義の全文は、`.claude/rules/core_requirements_full.md` に在ります。",
          "",
          "次の2つを確かめてください。",
          "",
          "- **R0-1**：結ぶ要件が、工事の目的と中身に合っているかを確かめてください。もっと合う要件や、抜けている要件があれば、挙げてください。",
          "- **R0-2**：設計と実装と直しに、要件定義に反する所が無いかを確かめてください。反する所があれば、ファイルの名前と行で挙げてください。"))
# 依頼書の一般の観点（テンプレの「### 一般の観点」の行を写す。結果は観点ごとに「見つけた事と根拠」を書く）
GENERAL_RE = re.compile(r"^- [①-⑦]")
PRIORITIES = ("A", "B", "C", "D")
SEVERITY_FIX = ("Critical", "Major", "Minor")
SEVERITY_PROCESS = ("Process",)
# 結果の節の名前（テンプレの表の太字）→ 骨組みの中身の作り方。表の名前がこの一覧に当たらなければ止める。
RESULT_KIND = (
    ("監査の相手と版", "版"),
    ("監査対象の型宣言", "空"),
    ("監査対象の事実データの確認", "事実データ"),
    ("所見", "所見"),
    ("外部検索", "外部検索"),
    ("依頼を出した CC の自己申告への答え", "自己申告"),
    ("総合判定", "総合判定"),
    ("修正の指示", "修正"),
    ("CC プロセス欠陥対策", "プロセス"),
    ("開いたファイルと行", "空"),
    ("本物のファイルを書き替えていないこと", "空"),
)
# プログラムが作る文書 → その元データ（依頼書の必読に元データの名前が無ければ止める）
# ★2026-09-30（設計書 point1-one-way-20260930-2）＝設計書の元は工事のフォルダの やることの表.md（acceptance_src.json は使わない）
GENERATED = {".claude/state/acceptance.md": "やることの表.md"}
PLACE = "<監査が書く>"
# 結果の骨組みに入れる、監査が埋める所の印の全部（form はどれが残っていても止める）
PLACEHOLDERS = (PLACE, "<PASS / FAIL>", "<YES / NO>", "<GO / CONDITIONAL-GO / NO-GO>", "<件数>")
MARK = "<!-- gen_audit_docs:"
# ★2026-09-29＝request-design（設計書と元データから依頼書の元データを作る口）
GEN_MARK = "<!-- gen_audit_docs request-design"
# ★2026-09-30（設計書 point1-one-way-20260930-2）＝元データの JSON（SRC_JSON）は消した。読むのは工事のフォルダだけ。
PRE_JSON = os.path.join(ROOT, ".claude", "state", "pre_audit_check.json")
KINDS = {"design": ("設計書の監査", "_design"), "impl": ("実装の監査", "_impl")}
# ★2026-09-30（3点目-a・まこさん OK「OK」）＝実装の監査の問いは、設計書と実装の照合の決まった6問だけ。
#   （番号, 優先度, 名前, 優先度の理由, 本文）。本文の {…} は build_design_src が工事の値で埋める。
#   まこさん（2026-09-30）「設計書の通りに自動生成で実装できてるのかを監査で確認してもらうんじゃないのか？」
#   「守りの穴探しは永遠に終わらないから、優先度低いはずだが」＝穴探しの問いは入れない。
IMPL_QUESTIONS = (
    ("Q1", "A", "実装の指示を当てた結果が、実装の後と1文字も同じか",
     "違えば、実装は設計書のとおりに作られていない",
     "設計書の 4-20 には、実装の指示が {ni} 件あります。\n"
     "実装の前の対象のファイルに、この {ni} 件を番号の順に当ててください。実装の前の版は、{pre}です。対象のファイルは、{files}です。\n"
     "当てた結果が、実装の後の版と1文字も同じかを確かめてください。実装の後の版は、{post}です。\n"
     "確かめ方の例は、次のとおりです。まず、作業場に、git show で実装の前のファイルを出します。"
     "次に、直す前の文字を、直した後の文字に置き替えます。足す文字の指示なら、直す前の文字の後ろに、足す文字を足します。"
     "最後に、置き替えた結果と実装の後の版の差を、diff で取ります。"),
    ("Q2", "A", "実装の指示のどれにも当たらない行（設計書に無い変更）が無いか",
     "在れば、設計書に無い変更が実装に混ざっている",
     "実装の前の版と実装の後の版の差分を取ってください。実装の前の版は、{pre}です。実装の後の版は、{post}です。差分を取るファイルは、{files}です。\n"
     "差分のうち、実装の指示のどれにも当たらない行が在るかを確かめてください。在れば、全部を挙げてください。"),
    ("Q3", "A", "当てた記録が、実装の指示の全部と1件ずつ合うか",
     "合わなければ、どの件を道具が当てたかを後から確かめられない",
     "当てる道具は、実装の指示を当てるたびに、`SDK/.claude/audits/applied_fixes.json` に記録を書きます。この工事の記録の名前は、`design:{iter}` です。\n"
     "この記録が、実装の指示の {ni} 件と、番号と対象のファイルで1件ずつ合うかを確かめてください。\n"
     "記録に「当てた」とも「もう当て終わっていた」とも書かれていない件が在るかを確かめてください。\n"
     "「もう当て終わっていた」の件について、その件がどの実行で当たったかを確かめてください。確かめる材料は、当てる道具の出力と、git の差分です。"),
    ("Q4", "B", "承認した版の設計書どうしで、実装の指示が同じか",
     "当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない",
     "まこさんが承認した版の設計書の控えは、{archives}です。\n"
     "この控えの 4-20 の実装の指示と、{now}の 4-20 の実装の指示が同じかを確かめてください。"
     # ★2026-10-21（監査 CP84 の修正10・まこさん「他は当てる」）＝2つが同じファイルを指すと、問いが何も確かめない
     "★2つが同じファイルを指すときは、控えのハッシュ値と、承認の印（`.claude/state/acceptance.approved`）の値と、控えのコミットの版が同じかを確かめてください。"
     "違うなら、その違いが実装に影響するかを答えてください。"),
    ("Q5", "B", "実装の指示が、やることの表の要件を全部 満たすか",
     "要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない",
     "やることの表（`{todo}`）の一覧には、この工事でやることが書いてあります。\n"
     "実装の指示が、この一覧のやることを全部満たすかを確かめてください。\n"
     "一覧に在るのに実装の指示に無い物と、実装の指示に在るのに一覧に無い物を、全部挙げてください。"),
    ("Q6", "B", "完成の条件が、実装の後に本当に成り立つか",
     "成り立たなければ、承認のときの「済」が根拠にならない",
     "設計書の完成の条件の表には、{nc} 行の条件が書いてあります。\n"
     "この条件が、実装の後に本当に成り立つかを確かめてください。\n"
     "各行のコマンドを、作業場で走らせるか、読むだけの形で走らせてください。"
     "コマンドの中のパスは、`SDK` のフォルダからの相対です。そのため、どのコマンドも `SDK` のフォルダで走らせます。\n"
     "走らせるコマンドは、次のとおりです。{cmds}"),
)
# ★2026-10-12（170回目・まこさん「OK」＝直し方の案 B-1〜B-3）＝設計書の監査の決まった問い Q7（名前, 優先度の理由, 本文）。
#   まこさん（2026-10-12）「設計書の中身が正しいかをチェックしなくて、目標達成できると思ったわけ？」
#   「『設計の中身が正しいか』は設計書の監査の時に問うもので、設計書の監査結果で対応すべきことだよね？」
#   ＝設計の中身は設計書の監査で問う。実装の監査（IMPL_QUESTIONS）は、設計書のとおりに実装できているかだけを問う（直さない）。
DESIGN_Q7 = (
    "設計の中身が、上の要件定義に合っていて、正しいか",
    "設計の中身が誤っていれば、誤りがそのまま実装に入る",
    "この設計書の中身が、依頼書の上の方の「要件定義と工事の流れ」に合っているかを確かめてください。"
    "設計の中身に誤りが無いかも確かめてください。\n"
    "次の4つを見てください。\n"
    "1つ目に、この設計が、要件定義の 1〜8 の項目に反していないかを見てください。"
    "設計書に「要件定義との照らし」の表が在れば、その表の1行ずつを、設計書と実物で確かめてください。\n"
    "2つ目に、設計書に書いた数字と式と出どころが、教科書・法則・実物のコードと合っているかを見てください。\n"
    "3つ目に、この直しで壊れるほかの物を、設計書が書き漏らしていないかを見てください。\n"
    "4つ目に、やると決めたことの全部を、完成の条件の表が確かめる形になっているかを見てください。\n"
    "見つけた誤りと抜けを全部、設計書の行と、根拠にした実物の行を添えて書いてください。",
)
# ★2026-10-18（192回目・まこさん「同じ内容を２度聞いてるなら消して良い」）＝新しい形の設計書の監査には、要件ごとの問い R が在るので、
#   Q7 から「①要件定義に反していないか」を外す（R と同じ事を2か所で聞いていた）。数字・式・影響範囲・完成の条件は、R に無いので残す。
DESIGN_Q7_NEW = (
    "設計の中身が正しいか（数字・式・出どころ・影響範囲・完成の条件）",
    DESIGN_Q7[1],
    "設計書に書いた設計の中身に、誤りが無いかを確かめてください。"
    "要件定義に合っているかは、下の R の問いで1件ずつ聞きます。そのため、この問いでは要件定義を見なくてかまいません。\n"
    "次の3つを見てください。\n"
    "1つ目に、設計書に書いた数字と式と出どころが、教科書・法則・実物のコードと合っているかを見てください。\n"
    "2つ目に、この直しで壊れるほかの物を、設計書の「4-13 影響範囲」が書き漏らしていないかを見てください。\n"
    "3つ目に、やると決めたことの全部を、完成の条件の表が確かめる形になっているかを見てください。\n"
    "見つけた誤りと抜けを全部、設計書の行と、根拠にした実物の行を添えて書いてください。",
)
# ★2026-10-18（ToDo の15番・別セッションの監査 2026-10-12 の M-11 と Q9・まこさん「最低限伝わるのでこれで進めていいよ」）
#   ＝新しい形の設計書（目標・工事の種類・要件定義の索引・確かめていないこと が在る設計書）の監査の、決まった問い。
#   要件ごとの問い（R）は、要件定義の正本の行・設計書の索引の対応（gen_acceptance.INDEX_MAP）・工事の種類から、プログラムが組む。
#   どの工事にも出す問い（F）と、検査やプログラムを直す工事にだけ出す問い（K）は、決まった文（worklog 20261018 §16 の文）。
#   問いごとに、誤りを直す修正の書き先を書く。修正を当てるプログラム（apply_audit_fix.py）は、やることの表.md には当て、
#   まこさんが OK した案の写し（逐語のファイル）には当てない（apply_audit_fix.py の is_verbatim）。
#   直す前は、設計の中身を問う決まった問いが Q7 の1問だけで、ほかは工事ごとに CC が手で書いた（CC が問いを選ぶ形＝9月29日・30日と同じ道）。
FIX_AUTO = ("プログラムは、設計書を作り直すときに、この修正を自動で入れます。",)
FIX_OK = ("プログラムは、この修正を自動では入れません。", "CC が案を直し、まこさんの OK をいただいてから、プログラムが設計書を作り直します。")
NEW_WHY_R = "要件定義に反する設計や、書き漏れが、そのまま実装に進む"
# (番号, 名前, 優先度の理由, 本文の行, 書き先)。書き先＝goal（やることの表の目標）／any（前提の3の表）／案の見出し名／None（修正を書かない）
DESIGN_F = (
    ("F1", "この設計書のとおりに作ると、要件に沿って目標に近づく工事になるか",
     "目標につながらない工事が、実装に進む（まこさん 2026-10-13「そもそもの問いはいらないの？」）",
     ("CAT プロジェクトの目標は、本番で全月 net ≥ $1,900 を達成することです。",
      "CC は、設計書の「3-0 目標」に、2つのことを書きました。1つ目は、この工事が済むと何ができるようになるか（②）です。"
      "2つ目は、それが net までどうつながるか（③）です。",
      "この2つを読み、この工事が要件定義に沿って目標に近づく工事になっているかを確かめてください。",
      "あわせて、④と⑥に抜けが無いかも見てください。④は、無駄だったと後から分かる物です。⑥は、この工事が損なう恐れのある要件です。"), "goal"),
    ("F2", "設計書の文に、根拠が付いているか",
     "CC が結論だけを書いた文が在ると、監査も まこさんも、その文が正しいかを確かめられない",
     ("設計書の中に、CC が「合っています」「当たりません」「変わりません」のように、結論だけを書いた文が無いかを見てください。",
      "そういう文には、根拠か、確かめ直すコマンドが付いていなければなりません。根拠は、ファイルの名前と行番号です。",
      "根拠もコマンドも付いていない文を、設計書の行番号で全部挙げてください。"), "any"),
    ("F3", "CC がまだ確かめていないことを、確かめないまま進めてよいか",
     "確かめていないことの中に、実装の前に確かめるべき物が在ると、誤りが実装の後に出る",
     ("CC は、設計書の「6-5 確かめていないこと」に、まだ確かめていないことを書きました。",
      "その1件ずつを読み、確かめないまま実装に進んでよいかを判断してください。",
      "進めてはいけない件があれば、その理由と、先に走らせるべきコマンドを書いてください。",
      "6-5 に書かれていない、確かめていないことを見つけたら、それも挙げてください。"), "確かめていないこと"),
    ("F4", "採らなかった案を、理由なく捨てていないか",
     "より良い案を理由なく捨てていると、目標から遠い作りのまま実装に進む",
     ("CC は、設計書の「5 決めたことと理由」に、決めたことと、採らなかった案と、その理由を書きました。",
      "CC が、採った案より良い案を、理由なく捨てていないかを確かめてください。",
      "設計書に書かれていない別の案のほうが良いと考えたら、その案も挙げてください。"), "5"),
    ("F5", "設計書を全部 書く前に、まこさんに向きを見せたか",
     "まこさんが向きを見ないまま設計の中身が書かれると、向きの誤りが設計書の監査の後まで残る",
     ("CC は、設計書の中身を全部書く前に、概要と目標とやらないことを、まこさんに見せる決まりになっています。",
      "まこさんの OK の発言は、逐語のファイルとして、工事のフォルダに置かれます。工事のフォルダは、設計書の元（やることの表.md）と同じフォルダです。"
      "逐語のファイルの名前は、ok_ で始まります。",
      "そのときの まこさんの OK の発言の逐語のファイルが、工事のフォルダに在るかを確かめてください。",
      "逐語のファイルが無ければ、CC は、まこさんが向きを見ないまま、設計の中身を書いたことになります。",
      "",
      "逐語のファイルが無いときは、そのことを所見に書いてください。"
      "この問いには、修正の指示を書きません。足りないのは まこさんの発言で、監査人には書けないためです。"),
     None),
    # ★2026-10-18（まこさん「工事の内容、目的が正しいのかという問い」「その３つは追加」「F678はOK」）＝工事そのものの正しさを問う。
    #   F1 は「設計書のとおりに作ると目標に近づくか」で、工事の目的と中身が正しいことを前提にしていた（10月12日の誤りと同じ型）。
    ("F6", "この工事の目的は正しいか",
     "目的そのものが誤っていると、設計書がどれだけ正しくても、目標につながらない工事が実装に進む",
     ("CC は、この工事が何のための工事かを、設計書の「§1 概要」に書きました。依頼書の「この監査は何のためか」の1にも、同じ目的が書いてあります。",
      "その目的が、要件定義と目標から見て正しいかを確かめてください。目標は、全月 net ≥ $1,900 です。",
      "目的が目標につながらない所や、要件定義に反する所があれば、それを挙げてください。"), "概要"),
    ("F7", "この工事が満たそうとしている要件は正しいか",
     "結ぶ要件を取り違えると、要件ごとの問いが見る所も取り違える",
     ("設計書の「結ぶ要件」には、この工事が要件定義の何番を満たすための工事かが書いてあります。",
      "その要件が、この工事の目的と中身に合っているかを確かめてください。",
      "もっと合う要件や、満たすべきなのに抜けている要件があれば、それを挙げてください。"), "plan"),
    ("F8", "この工事でやることが、目的に対して過不足ないか",
     "目的に要る直しが抜けると、工事が済んでも目的が果たされない。要らない直しが入ると、守りを壊す恐れが増える",
     ("CC は、設計書の「やることの一覧」に、この工事でやることを1件ずつ書きました。",
      "この一覧を、工事の目的と照らしてください。",
      "目的を果たすのに要るのに一覧に無い直しがあれば、それを挙げてください。",
      "目的に要らないのに一覧に入っている直しがあれば、それも挙げてください。",
      "あわせて、「やらないこと」に回した直しの中に、この工事でやるべき物が無いかも見てください。"), "一覧"),
)
DESIGN_K = (
    ("K1", "この検査が守る相手は正しいか", "守る相手を取り違えると、直した検査が守るべき物を守らない",
     ("CC は、設計書の「4-22」の①に、この工事で直す検査やプログラムが何を守るための物かを書きました。守る相手は、要件か材料です。",
      "直すプログラムの実物を開き、書いてある守る相手と合っているかを確かめてください。")),
    ("K2", "直す前に通っていた誤りは、本当に在るか", "本当は無い誤りを直す工事は、無駄な工事になる",
     ("CC は、設計書の「4-22」の②に、直す前のプログラムが通してしまっていた誤りの実例と、それを確かめたコマンドを書きました。",
      "写しの作業場でそのコマンドを走らせ、書いてある誤りが本当に通るかを確かめてください。")),
    ("K3", "直した後に止まる誤りと、まだ通る誤りは、正しく書かれているか", "まだ通る誤りが書かれていないと、直ったと思い込んだまま進む",
     ("CC は、設計書の「4-22」の③に、直した後に止まるようになる誤りと、直した後もまだ通る誤りを書きました。",
      "その2つが設計の中身と合っているかを確かめてください。",
      "あわせて、まだ通る誤りのうち、書かれていない物が無いかも見てください。")),
    ("K4", "この直しで弱くなる守りに、抜けが無いか", "弱くなる守りが書かれていないと、守りを減らしたことに誰も気づかない",
     ("CC は、設計書の「4-22」の④に、この直しのせいで確かめなくなる事と、弱くなる守りを書きました。",
      "その一覧に抜けが無いかを確かめてください。")),
)
# 元データの外部検索の行の頭（build_design_src が書き、build_request が「検索の言葉」と「何と照らすか」に分ける）
SEARCH_WORDS = "検索の言葉："
SEARCH_WHAT = "調べる物："
SEARCH_NONE = "（案に検索の言葉の列が無い。「何と照らすか」から、監査が検索の言葉を決めてください）"
# ★2026-10-18（ToDo の15番・まこさん「設計書ナシや、例外的監査は、項目以外は手書きにすれば？」。192回目・まこさん決定「b」＝
#   まこさんが指定した監査なら何でも）＝手書きの依頼。項目（見出しと並び）と決まった文はプログラムが出し、項目の中身は CC が手で書く。
#   依頼書の名前に _nodesign_ を入れ、元データは作業場（SDK/.claude/audits/<何か>_work/）に置く。
NODESIGN_LABEL = "手書きの依頼"
# ★2026-10-12（A-2）＝固定で載せる文が依頼書に入っているかを見る文字（正本の先頭の見出し。gen_core_requirements.embed_lines が太字の行にする）
CORE_MARK = "**■ 要件定義と工事の流れ（固定・毎回 読む・消さない）**"
# 依頼書に足す節の見出し（テンプレには無い。build_request が、メタ情報の節のすぐ下に足す）
CORE_HEAD = "## 要件定義と工事の流れ (固定・消さない・まこさん指示 2026-10-12)"
# ★2026-10-18（192回目・まこさん「４つともOK」）＝実装の監査でも、一般の観点①〜⑦と、外の基準で確かめること（外部検索）を出す
#   （2026-10-01 の「該当なし」は置き替わった）。外部検索が0件なら、なぜ無いかを書く。
CP_RE = re.compile(r"_cp(\d+)_audit_(?:request|report)\.md$")
PATH_TOKEN =re.compile(r"`([^`\s]+/[^`\s]*\.(?:md|py|json|jsonl|sh|txt|csv))`")


# ───────────── 共通 ─────────────

def sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def repo_path(p: str) -> str:
    p = p.strip().strip("`")
    if p.startswith("SDK/"):
        return os.path.join(SDK, p[4:])
    return os.path.join(ROOT, p)


def rel_of(path: str) -> str:
    return os.path.relpath(os.path.realpath(path), os.path.realpath(ROOT))


def body_strip(lines: list) -> list:
    ls = list(lines)
    while ls and ls[-1].strip() in ("", "---"):
        ls.pop()
    while ls and ls[0].strip() == "":
        ls.pop(0)
    return ls


def split_sections(text: str):
    """「## 」の見出しで分ける（囲み ``` の中は見出しと数えない）。戻り＝(見出しの前の行, [(見出し, 本文の行)])。"""
    head, secs, cur, fence = [], [], None, False
    for ln in text.splitlines():
        if ln.startswith("```"):
            fence = not fence
        if not fence and ln.startswith("## "):
            cur = (ln, [])
            secs.append(cur)
        elif cur is None:
            head.append(ln)
        else:
            cur[1].append(ln)
    return head, secs


def split_mark(text: str):
    """末尾の目印の行を外す。戻り＝(本文, 目印の属性の辞書)。目印が無ければ属性は空。"""
    idx = text.rfind("\n" + MARK)
    if idx < 0:
        return text, {}
    body = text[:idx]
    attrs = dict(re.findall(r"(\S+?)=(\S+)", text[idx + 1:].split("-->")[0]))
    return body, attrs


def out_ok(path: str, kind: str):
    """書いてよい先か。kind＝request（依頼書）／result（結果の骨組み）。戻り＝(よいか, 理由)。
    ★結果の骨組みは作業場にだけ書く＝結果ファイルの置き場（audits の *_audit_report.md）に骨組みを置くと、
      中身の無い結果が hook 11（テンプレの形の照らし）を通らずに出来てしまうため。"""
    p = os.path.realpath(path)
    a = os.path.realpath(AUDITS)
    if not p.startswith(a + os.sep):
        return False, "監査の置き場（SDK/.claude/audits）の外"
    parts = os.path.relpath(p, a).split(os.sep)
    if (kind == "request" and len(parts) == 2 and parts[0] == "inputs"
            and parts[1].endswith("_audit_request.md") and not parts[1].startswith("_")):
        if not os.path.exists(p):
            return True, ""
        # 既に在る依頼書を上書きしてよいのは、①道具が作ったまま書き替えられていない ②その依頼書の結果ファイルがまだ無い、の両方のときだけ
        report = os.path.join(a, parts[1].replace("_audit_request.md", "_audit_report.md"))
        body, mark = split_mark(open(p, encoding="utf-8").read())
        untouched = bool(mark.get("body_sha256")) and mark.get("body_sha256") == sha256_text(body)
        if untouched and not os.path.exists(report):
            return True, ""
        return False, ("既に在る依頼書は上書きしない（上書きしてよいのは、道具が作ったまま書き替えられておらず、"
                       "結果ファイルがまだ無いときだけ）")
    if len(parts) >= 2 and parts[0].endswith("_work") and p.endswith(".md"):
        return True, ""
    if kind == "request":
        return False, "依頼書を書いてよい先（inputs の <名前>_audit_request.md・作業場の .md）ではない"
    return False, "結果の骨組みを書いてよい先（作業場 <何か>_work の .md）ではない"


def write_out(path: str, text: str, kind: str) -> bool:
    ok, why = out_ok(path, kind)
    if not ok:
        print(f"❌ 書かなかった: {path}（{why}）")
        return False
    os.makedirs(os.path.dirname(os.path.realpath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"書いた: {rel_of(path)}")
    return True


def inputs_gate(out_path: str, target: str = "") -> list:
    """inputs に依頼書を書くときの照らし（いまの監査依頼書ゲートと同じ）。inputs でなければ何も見ない。
    target＝依頼書の元データのメタ「監査の相手」（リポジトリからの相対のパス）。"""
    if not INPUT_REQUEST_RE.search(os.path.realpath(out_path)):
        return []
    errs = []
    # ★2026-10-20（196回目・まこさん「OK」）＝監査の相手が承認の控え（acceptance_archive の .md）のときは、その控えを照らす。
    #   直す前は、前の工事の控えの依頼書でも、いまの設計書（acceptance.md＝別の工事）を照らして落ちた（K-4・記録 20261020 §12）。
    arch = os.path.join(ROOT, target) if (target and "/acceptance_archive/" in target and target.endswith(".md")) else ""
    # ★2026-10-18（ToDo の15番）＝設計書の無い直しの監査（名前に _nodesign_）は、承認する設計書が無いので、承認との照らしをしない。
    #   監査に出す前のチェック（下）は、ほかの監査と同じく掛ける。
    if "_design_" not in os.path.basename(out_path) and "_nodesign_" not in os.path.basename(out_path):
        if arch:
            # 控えは承認のときに作られて git に入る＝git の版（HEAD）と1文字も違わなければ、承認した版のまま
            r = subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{target}"], capture_output=True)
            now = sha256_file(arch) if os.path.isfile(arch) else ""
            want = hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else ""
            if not want or now != want:
                errs.append(f"承認の控えが git の版と食い違うので、依頼書を作れない（git {want[:16]}… ／ 控え {now[:16]}…・{target}）")
        else:
            now = sha256_file(DESIGN) if os.path.isfile(DESIGN) else ""
            want = open(APPROVED, encoding="utf-8").read().strip() if os.path.isfile(APPROVED) else ""
            if not want or now != want:
                errs.append(f"設計書が承認と食い違うので、依頼書を作れない（承認 {want[:16]}… ／ いまの設計書 {now[:16]}…）")
    if os.path.isfile(PRE_AUDIT_CHECK):
        # ★2026-10-20（199回目・まこさん「OK」）＝設計書の監査（名前に _design_）は実装の前なので、設計書と実物の照合の行を見ない旗を付ける
        r = subprocess.run([sys.executable, PRE_AUDIT_CHECK, "--verify"] + (["--design", arch] if arch else [])
                           + (["--before-impl"] if "_design_" in os.path.basename(out_path) else []),
                           capture_output=True, text=True)
        if r.returncode != 0:
            errs.append("監査に出す前のチェック（pre_audit_check.py --verify）が通っていない。"
                        "python3 .claude/tools/pre_audit_check.py --run" + (f" --design {arch}" if arch else "")
                        + " を打ち、全部 rc=0 にしてから作る")
    return errs


def kind_of(head: str, table) -> str | None:
    for pre, kind in table:
        if head.startswith(pre):
            return kind
    return None


# ───────────── 元データ ─────────────

BLOCK_RE = re.compile(r"^<!--\s*項目:\s*(.*?)\s*-->\s*$")


def parse_attrs(s: str) -> dict:
    s = s.strip()
    attrs = {}
    if "名前=" in s:
        s, name = s.split("名前=", 1)
        attrs["名前"] = name.strip()
    if "理由=" in s:
        s, why = s.split("理由=", 1)
        attrs["理由"] = why.strip()
    for tok in s.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            attrs[k] = v
    return attrs


def parse_src(path: str):
    errs, blocks, cur = [], [], None
    for ln in open(path, encoding="utf-8").read().splitlines():
        m = BLOCK_RE.match(ln)
        if m:
            # 項目の名前は、最初の「属性=値」の手前まで（名前に空白が在ってもよい）
            key_attr = re.split(r"\s+(?=\S+=)", m.group(1), maxsplit=1)
            cur = {"key": key_attr[0].strip(), "attrs": parse_attrs(key_attr[1] if len(key_attr) > 1 else ""),
                   "lines": []}
            blocks.append(cur)
        elif cur is not None:
            cur["lines"].append(ln)
    src = {k: None for k in KEYS_ONE}
    for k in KEYS_MANY:
        src[k] = []
    for b in blocks:
        body = "\n".join(body_strip(b["lines"]))
        if b["key"] in KEYS_ONE:
            if src[b["key"]] is not None:
                errs.append(f"項目「{b['key']}」が2つ在る")
            src[b["key"]] = body
        elif b["key"] in KEYS_MANY:
            src[b["key"]].append({"attrs": b["attrs"], "body": body})
        else:
            errs.append(f"項目「{b['key']}」はテンプレに置き場が無い（{b['attrs'].get('名前', '')}）")
    meta = {}
    for ln in (src["メタ"] or "").splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            meta[k.strip()] = v.strip()
    return src, meta, errs


# ───────────── 依頼書を作る ─────────────

def gen_mark_problem(src_path: str) -> str:
    """元データが request-design の作った物のままか。戻り＝問題の文（無ければ空）。"""
    text = open(src_path, encoding="utf-8").read()
    first, _, rest = text.partition("\n")
    if not first.startswith(GEN_MARK):
        return ("元データの1行目に request-design の目印が無い＝CC が手で書いた元データの口は閉じました"
                "（python3 .claude/tools/gen_audit_docs.py request-design <design|impl> で作る）")
    want = dict(re.findall(r"(\S+?)=(\S+)", first)).get("body_sha256", "")
    if want != sha256_text(rest):
        return "元データが、request-design で作った後に書き替えられている（本文のハッシュ値が目印と違う）"
    return ""


def consistency_errors(src: dict) -> list:
    """依頼書の節どうしの食い違い（結論の問い・問いの一覧・監査対象・スコープ・自己申告）。1件でも在れば inputs に書かない。

    ★2026-10-01（工事 point5-q5label-20261001・まこさん指示「自動生成なのにミスがあっては本末転倒なんだが、なぜミスが出た？原因究明して修正して」）
      ＝直す前は、道具に節どうしを照らす仕組みが無く、私が道具を手で直したときの抜け（問い2 に当たる問いが無い・
      スコープの外・自己申告の出どころの無い番号）が、そのまま依頼書に出た（cp54）。
    """
    # ★2026-10-18（192回目）＝問いの置き場を1か所にしたので、結論の問い・監査対象・大目的の注記との照らしは無くなった。
    #   見るのは、①問いの番号が重ならない ②設計書の監査でない依頼に、要件定義を指す固定の問い R0 が在る ③外部検索が0件なら理由が在る。
    errs = []
    ids = [q["attrs"].get("番号") for q in src["問い"]]
    dup = sorted({n for n in ids if ids.count(n) > 1})
    if dup:
        errs.append(f"問いの番号が重なっている（{'・'.join(dup)}）")
    meta = {}
    for ln in (src["メタ"] or "").splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            meta[k.strip()] = v.strip()
    if meta.get("監査の種類", "") != KINDS["design"][0] and REQ_Q[0] not in ids:
        errs.append(f"設計書の監査でない依頼に、要件定義を指す固定の問い {REQ_Q[0]}（{REQ_Q[3]}）が無い")
    if not src["外部検索"] and not (src["外の基準が無い理由"] or "").strip():
        errs.append("外部検索が0件なのに、「外の基準が無い理由」が無い（なぜ外で調べる物が無いかを書く）")
    for it in src["自己申告"]:
        if re.match(r"\*\*塞げないもの\*\*＝Q\d+ の\d+＝", it["body"]):
            errs.append("自己申告の塞げないものに、出どころの無い番号（Q5 の1＝ など）が在る＝依頼書の問いの番号と取り違える")
    return errs


# ★2026-10-18（192回目）＝依頼書の頭の案内（guide_lines）は無くした。問いの置き場が「確かめてほしいこと」の1か所になり、案内が要らなくなった。


def nodesign_errors(src_path: str, out_path: str, meta: dict) -> list:
    """手書きの依頼（2026-10-18・まこさん「設計書ナシや、例外的監査は、項目以外は手書きにすれば？」・同日 決定「b」＝まこさんが指定した監査なら何でも）
    の手書きの元データの照らし。手書きを受けるのは、この種類だけ。ほかの監査の元データは、今までどおり request-design が作った物だけを受ける。"""
    errs = []
    p = os.path.realpath(src_path)
    a = os.path.realpath(AUDITS)
    parts = os.path.relpath(p, a).split(os.sep) if p.startswith(a + os.sep) else []
    if not (len(parts) >= 2 and parts[0].endswith("_work")):
        errs.append("手書きの依頼の元データは、作業場（SDK/.claude/audits/<何か>_work/）に置く")
    if "_nodesign_" not in os.path.basename(out_path):
        errs.append("手書きの依頼の依頼書は、名前に _nodesign_ を入れる（設計書の監査・実装の監査と取り違えない）")
    if os.path.basename(meta.get("監査の相手", "")) == os.path.basename(DESIGN):
        errs.append("手書きの依頼の相手に、設計書（acceptance.md）を書かない（設計書の監査か実装の監査にする）")
    m = re.search(r"cp(\d+)", meta.get("cp", ""))
    task = meta.get("task", "")
    if m:
        for d in (AUDITS, os.path.join(AUDITS, "inputs")):
            for n in os.listdir(d):
                if re.search(rf"_cp{m.group(1)}_audit_(?:request|report)\.md$", n) and f"_{task}_cp" not in n:
                    errs.append(f"監査の番号 cp{m.group(1)} は、ほかの監査（{n}）が使っている")
    return errs


def question_dup_errors(qs: list) -> list:
    """同じ中身の問いを見つける（2026-10-21・199回目・まこさん「同じ問いを繰り返してるけど。いいの？」）。
    直す前は、依頼書 CP83 で、割り当ての問い W01〜W25（項目の名前だけが違う2種類の文）と、要件の問い R3-1〜R3-5・R4
    （同じ「4-7」を読ませる同じ文）が並び、問いが57件になった。見直しでも見つからなかった。
    比べ方＝問いの本文から、その問いの名前の「」の中の語（＝で分けた各部分）を消し、「要件定義の<番号>番」を
    「要件定義のN番」にする。残りの本文が1文字も同じ問いが2つ以上あれば、まとめずに並べたものとして止める。
    戻り＝止める理由の文（無ければ空）。"""
    sig: dict = {}
    for q in qs:
        a = q.get("attrs") or {}
        num, nm, s = str(a.get("番号") or ""), str(a.get("名前") or ""), str(q.get("body") or "")
        for part in re.findall(r"「([^」]+)」", nm):
            for p in sorted((x.strip() for x in part.split("＝")), key=len, reverse=True):
                if len(p) >= 2:
                    s = s.replace(p, "")
        if num.startswith("R") and len(num) > 1:
            s = s.replace(f"要件定義の{num[1:]}番", "要件定義のN番")
        sig.setdefault(re.sub(r"\s+", " ", s).strip(), []).append(num)
    return [f"同じ中身の問いが {len(v)} 件在る（{'・'.join(v)}）＝名前と番号を除くと本文が同じ。"
            "1つの問いにまとめ、違う所（項目・要件の番号）は問いの中に並べる（まこさん 2026-10-21「今後二度とこのようなミスを繰り返せないような作りに」）"
            for v in sig.values() if len(v) >= 2]


def build_request(src_path: str, out_path: str) -> int:
    src, meta, errs = parse_src(src_path)
    # ★2026-10-18（ToDo の15番・まこさん「設計書ナシや、例外的監査は、項目以外は手書きにすれば？」）
    #   ＝設計書の無い直しの監査だけは、CC が手で書いた元データを受ける（項目と決まった文は、この道具がテンプレから出す）
    nodesign = meta.get("監査の種類", "") == NODESIGN_LABEL
    if nodesign:
        errs += nodesign_errors(src_path, out_path, meta)
    _gm = "" if nodesign else gen_mark_problem(src_path)
    if _gm:
        # ★口を閉じる＝どの置き場にも1バイトも書かない（直す前は inputs 以外の置き場なら ❌ でも書いていた）
        print(f"❌ {_gm}")
        print(f"❌ 書かなかった: {out_path}")
        return 1
    for k in META_KEYS:
        if not meta.get(k):
            errs.append(f"メタに「{k}」が無い")
    for k in ("目的と経緯", "着手前必読", "範囲の中", "範囲の外", "修正をどこに書くか"):
        if not src[k]:
            errs.append(f"項目「{k}」が無い")
    for k in ("事実データ", "問い"):
        if not src[k]:
            errs.append(f"項目「{k}」が1件も無い")
    # ★外部検索が0件のときは「外の基準が無い理由」が要る（consistency_errors が見る）
    ids = []
    for q in src["問い"]:
        a = q["attrs"]
        if not a.get("番号") or not a.get("名前"):
            errs.append(f"問いに番号か名前が無い（{a}）")
        if not a.get("理由"):
            errs.append(f"問い {a.get('番号')} に優先度の理由（理由=…）が無い")
        if a.get("優先度") not in PRIORITIES:
            errs.append(f"問い {a.get('番号')} の優先度が A〜D でない（{a.get('優先度')}）")
        if a.get("番号") in ids:
            errs.append(f"問いの番号 {a.get('番号')} が2つ在る")
        ids.append(a.get("番号"))
    # ★2026-10-21（199回目・まこさん「今後二度とこのようなミスを繰り返せないような作りに」）＝同じ中身の問いが2つ以上あれば書かない。
    #   どの作り方の問い（W・R・F・手書きの Q8〜）も、ここを通らないと依頼書にならない。
    errs += question_dup_errors(src["問い"])
    for k in ("事実データ", "外部検索"):
        for it in src[k]:
            if not it["attrs"].get("名前"):
                errs.append(f"{k} に名前が無い")
    target = meta.get("監査の相手", "")
    tpath = repo_path(target) if target else ""
    if target and not os.path.isfile(tpath):
        errs.append(f"監査の相手のファイルが無い: {target}")
    reading = src["着手前必読"] or ""
    for tok in PATH_TOKEN.findall(reading):
        if not os.path.exists(repo_path(tok)):
            errs.append(f"着手前必読のファイルが無い: {tok}")
    for gen, raw in GENERATED.items():
        # 作業場に写した前の版の設計書でも同じ（名前で見る）
        # ★2026-09-29（135回目）＝工事のフォルダ（--work）から作った設計書は、元が やることの表.md（acceptance_src.json は使わない）
        if os.path.basename(target) == os.path.basename(gen) and raw not in reading \
                and not (os.path.basename(gen) == "acceptance.md" and "/verbatim/" in reading and "やることの表.md" in reading):
            errs.append(f"監査の相手 {gen} はプログラムが作る文書。着手前必読に元データ {raw} が無い")

    if not os.path.isfile(TEMPLATE):
        print(f"❌ テンプレが無い: {TEMPLATE}")
        return 1
    _, secs = split_sections(open(TEMPLATE, encoding="utf-8").read())
    base = f"{meta.get('日付', '')}_{meta.get('task', '')}_{meta.get('cp', '')}"

    # ★2026-09-29（まこさん指摘「監査の依頼内容が変じゃないか？」・worklog 20260929 §40 の10・11・§41）
    #   ①テンプレの「N 件」を、着手前必読の表の行の数で埋める ②結果と依頼書の置き場を、根からの全パスにそろえる
    #   （直す前は SDK からの相対と全パスが混ざり、根で起動した監査が置き場を取り違えうる）
    #   ③売買のロジックに触らない工事（メタ「売買に触るか: いいえ」）では、トレードの外部認知を求める守則を出さない
    # ★2026-09-30（3点目-a）＝必読はテンプレの形（番号つきの行）。古い形（表の行）も数える
    n_read = sum(1 for ln in (src["着手前必読"] or "").splitlines() if re.match(r"^(?:\|\s*\d+\s*\||\d+\. )", ln))
    # ★2026-10-18（192回目・まこさん「４つともOK」）＝監査の種類で出し分ける物は3つ。①固定の文の2段（売買に触る工事は4〜6・9も）
    #   ②必読の★注記（相手がプログラムの作る設計書のときだけ）③守ることの売買の行（net は M2-L まで・トレードの外部認知）。
    #   一般の観点・外の基準で確かめることは、どの種類にも出す（2026-10-01 の実装の監査の「該当なし」は置き替わった）。
    engine = meta.get("売買に触るか", "") == "はい"
    kind_label = meta.get("監査の種類", "")
    gen_doc = kind_label in (KINDS["design"][0], KINDS["impl"][0])

    def rep(s: str) -> str:
        if s.startswith(".claude/audits/"):
            s = "v3-bitget-api-sdk/bitget-python-sdk-api/" + s
        return (s.replace("<本依頼書のパス>", f"v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/{base}_audit_request.md")
                .replace("`.claude/audits/", "`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/")
                .replace("N 件", f"{n_read} 件")
                .replace("2026-XX-XX_<task>_cpN", base).replace("<cpN>", meta.get("cp", "")))

    out = [f"# 【監査依頼】{meta.get('題', '')}", ""]
    for head, lines in secs:
        kind = kind_of(head, SECTION_KIND)
        body = body_strip(lines)
        if kind is None:
            errs.append(f"テンプレの見出し「{head}」の埋め方が道具に無い（テンプレが変わった）")
            continue
        out += [rep(head), ""]                      # ★見出しの「N 件」も埋める（2026-09-29・自己テスト T9 で見つけた）
        if kind == "テンプレ":
            out += [rep(x) for x in body]
        elif kind == "宣言":
            for x in body:
                if x.startswith("<作業場のパス"):
                    # ★2026-10-18（192回目・別の CC の冷たい読み）＝手書きの依頼で作業場のパスが無かった。無ければ道具が既定のパスを出す
                    out += (src["作業場の指示"] or (f"写しは、作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/{meta.get('cp', '')}_work/` に作ってください。"
                                                   "必要なファイルは、自分で開いてください。確かめるときは、写しで走らせてください。")).splitlines()
                else:
                    out.append(rep(x))
        elif kind == "目的":
            out += (src["目的と経緯"] or "").splitlines()
        elif kind == "範囲":
            heads = [x for x in body if x.startswith("### ")]
            if len(heads) != 2:
                errs.append("テンプレの「監査の範囲」に「### 」の見出しが2つ無い")
                heads = ["### 範囲の中", "### 範囲の外（理由つき）"]
            out += [heads[0], ""] + (src["範囲の中"] or "").splitlines() + [""]
            out += [heads[1], ""] + (src["範囲の外"] or "").splitlines()
        elif kind == "メタ":
            h = sha256_file(tpath) if tpath and os.path.isfile(tpath) else "（ファイルが無い）"
            out += [f"- 依頼日: {meta.get('日付', '')}",
                    f"- 依頼者: {meta.get('依頼者', '')}",
                    f"- 監査の種類: {kind_label}",
                    f"- 売買に触るか: {meta.get('売買に触るか', '（書いていない）')}",
                    f"- 監査対象タスク: {meta.get('監査対象タスク', '')}",
                    f"- 監査の相手と版: `{target}` ／ ハッシュ値 {h}",
                    f"- 直す相手: {meta.get('直す相手', '（着手前必読の★に書いた直す相手）')}",
                    f"- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/{base}_audit_report.md`",
                    f"- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/{base}_audit_request.md`"]
            # ★2026-10-18（192回目）＝「設計書のハッシュ値」の行は消した（「監査の相手と版」と同じ値を2回 出していた）
        elif kind == "着手前必読":
            out += reading.splitlines()
            notes = [x for x in body if x.startswith("★")]
            if notes and gen_doc:                        # ★注記（直す相手・元データ）は、相手がプログラムの作る文書のときだけ
                out += [""] + notes
        elif kind == "事実データ":
            for it in src["事実データ"]:
                out += [f"### {it['attrs'].get('名前', '')}", ""] + it["body"].splitlines() + [""]
        elif kind == "視点":
            # 一般の観点①〜⑦＝テンプレの小見出し・説明・7行をそのまま写す（どの種類にも出す）。
            # 外の基準で確かめること＝元データの外部検索。0件なら、なぜ無いかを書く（まこさん 2026-10-18「必須の視点」）
            heads = [x for x in body if x.startswith("### ")]
            if len(heads) != 2:
                errs.append("テンプレの「問いの外から当てる視点」に「### 」の見出しが2つ無い")
            i_ext = body.index(heads[1]) if len(heads) == 2 else len(body)
            out += body_strip(body[:i_ext])
            ext = body[i_ext:]
            out += [""] + body_strip([x for x in ext if not (x.startswith("件数:") or re.match(r"^\d+\. ", x) or x.startswith("   - "))]) + [""]
            n = len(src["外部検索"])
            out += [f"件数: {n} 件" + ("。外で調べる物はありません。理由は、下の行に書いてあります。結果の5「外部検索」に、「0件」と、この理由を写してください。"
                                       if not n else "。結果の外部検索で、この件数の調べる物に1つずつ答えてください。"), ""]
            if not n:
                out += (src["外の基準が無い理由"] or "").splitlines()
            for i, it in enumerate(src["外部検索"], 1):
                bl = it["body"].splitlines()
                qw = next((x[len(SEARCH_WORDS):].strip() for x in bl if x.startswith(SEARCH_WORDS)), None)
                what = next((x[len(SEARCH_WHAT):].strip() for x in bl if x.startswith(SEARCH_WHAT)), None)
                q = qw if qw is not None else (" ".join(it["body"].split()) or it["attrs"].get("名前", ""))
                out += [f"{i}. **{it['attrs'].get('名前', '')}**:",
                        f"   - 検索の言葉: {q}",
                        f"   - 何と照らすか: {what or it['attrs'].get('名前', '')}"]
        elif kind == "問い":
            out += [x for x in body if x.startswith("★")] + [""]
            for q in src["問い"]:
                a = q["attrs"]
                # ★2026-10-21（199回目）＝「優先度の理由＝…」の詰めた行を、文にした
                _why = str(a.get("理由", "")).rstrip("。")
                out += [f"### {a.get('番号', '')} — {a.get('名前', '')}（優先度 {a.get('優先度', '')}）", "",
                        f"**この問いが要る理由**：{_why}。", ""]
                out += q["body"].splitlines() + [""]
        elif kind == "自己申告":
            # ★2026-10-18（192回目）＝手書きの依頼（設計書が無い）では「設計書に書いていない事」を出さない
            out += body_strip([x.replace("・設計書に書いていない事", "") if nodesign else x
                               for x in body if not re.match(r"^\d+\. ", x)]) + [""]
            for i, it in enumerate(src["自己申告"], 1):
                ls = it["body"].splitlines() or [""]
                out.append(f"{i}. {ls[0]}")
                out += ["   " + x if x.strip() else x for x in ls[1:]]
            if not src["自己申告"]:
                out.append("（無い）")
        elif kind == "答え方":
            for x in body:
                if x.startswith("<監査の種類ごとに道具が書く"):
                    out += (src["修正をどこに書くか"] or "").splitlines()
                elif x.startswith("- <売買のロジックに触る工事のときだけ道具が足す"):
                    if engine:
                        out += ["- net を、M2-L の段まで判断の材料に使いません（まこさん決定 2026-09-01）。",
                                "- トレードについての外の知識を踏まえて判断します。外の知識は、暗号資産の先物の自動売買（Crypto futures algo trading）の業界の実情です。"]
                else:
                    out.append(rep(x))
        out = body_strip(out) + ["", "---", ""]
        if kind == "メタ":
            # ★2026-10-12（A-2・まこさん「OK」）＝メタ情報のすぐ下に、固定で載せる文（要件定義と工事の流れ）を、正本から写して載せる。
            #   正本が無い・逐語のファイルと違うときは、ここで止まる（fail-closed）。位置はこのまま（まこさん決定 2026-10-18）。
            # ★2026-10-18（192回目）＝固定の文は要約。売買のロジックに触る工事だけ、探し方・言葉・指標の扱い・工事の流れも足す。
            import gen_core_requirements as gcr
            out += [CORE_HEAD, ""] + gcr.embed_lines("all" if engine else "core") + ["", "---", ""]

    text = "\n".join(body_strip(out)) + "\n"
    text += (f"\n{MARK} request src={rel_of(src_path)} src_sha256={sha256_file(src_path)} "
             f"body_sha256={sha256_text(text)} -->\n")
    errs += consistency_errors(src)                   # ★2026-10-01（工事 point5-q5label-20261001）＝節どうしの食い違いが在れば書かない
    errs += request_content_errors(text)              # ★2026-10-02（144回目）＝中身（必読・経緯・問い2）が監査に要る形でなければ書かない
    errs += inputs_gate(out_path, meta.get("監査の相手", ""))
    for e in errs:
        print(f"❌ {e}")
    if errs and INPUT_REQUEST_RE.search(os.path.realpath(out_path)):
        print(f"❌ 書かなかった: {out_path}（inputs には ❌ が1件も無いときだけ書く）")
        wrote = False
    else:
        wrote = write_out(out_path, text, "request")
    if not errs and wrote:
        print(f"✅ 依頼書を作った（問い {len(src['問い'])} 件・事実データ {len(src['事実データ'])} 件・"
              f"外部検索 {len(src['外部検索'])} 件・自己申告 {len(src['自己申告'])} 件）")
    return 0 if (not errs and wrote) else 1


# ───────────── 設計書から依頼書の元データを作る（2026-09-29）─────────────
#   まこさん指示（2026-09-29・逐語）「監査依頼書を自動生成」「OKなのですべて完璧に上記チャットの１から５の各要件の通りに修正をすること」。
#   ★CC は依頼書の元データを1文字も書かない。中身は全部、設計書（acceptance.md）と工事のフォルダから作る。
#   ★設計のもとの行と対応の表は gen_acceptance.py の関数で読む（同じ判定を2か所に書かない・抜けが在れば止まる）。

def next_cp() -> int:
    """監査の番号の次の空き番号（inputs と audits の依頼書・結果の名前から数える）。"""
    nums = [0]
    for d in (AUDITS, os.path.join(AUDITS, "inputs")):
        for n in os.listdir(d):
            m = CP_RE.search(n)
            if m:
                nums.append(int(m.group(1)))
    return max(nums) + 1


def repo_ref(p: str) -> str:
    """設計書のパス（リポジトリ直下か SDK からの相対）を、依頼書の書き方（SDK/… か直下）に直す。無ければ空。"""
    p = (p or "").strip().strip("`")
    # ★2026-10-18（ToDo の15番・記録 20261013 の 368行「直す相手の3本のパスが SDK/../../.claude/tools/… の形で出ている」）
    #   ＝実物のパスに直してから、依頼書の書き方（_req_style）にそろえる。直す前は SDK からの相対の「../../」を、そのまま SDK/ の後ろに付けた。
    for base in (ROOT, SDK):
        full = os.path.normpath(os.path.join(base, p))
        if full.startswith(ROOT + os.sep) and os.path.exists(full):
            return _req_style(full)
    return ""


def _one_line(s) -> str:
    """元データの1行に入れる形（改行を ⏎ に・目印の区切りを壊さない）。"""
    return str(s if s is not None else "").replace("\n", " ⏎ ").replace("-->", "―>").strip()


def _attr(s) -> str:
    """問いの属性（理由・名前）に入れる形（属性の区切りの語と = を使わない）。"""
    return _one_line(s).replace("=", "＝").replace("名前＝", "名前：").replace("理由＝", "理由：")



# ★2026-10-01（142回目・cp57）＝設計書の「塞げないもの」の「Q5 の1＝」〜の行（設計書を書くときに止める hook が書かせる5件）
GATE_Q5_RE = re.compile(r"^Q(\d+) の(\d+)＝")
# ★2026-10-21（199回目）＝「＝」でつながず、文にした（公用文作成の考え方の書き方）
GATE_Q5_TO = (r"監査 cp14 の Q\1 の\2。この問いは、設計書を書くときに止める hook（require_acceptance_before_impl.sh）が、"
              r"どの設計書にも書かせる問いです。問いの中身は、")


def _cc_voice(s) -> str:
    """CC が書いた文の「私」を「依頼を出した CC」にする（依頼書の読み手には、私が誰か分からない・cp57）。
    ★「私的」「私たち」「私達」は置き替えない。"""
    # ★後ろに空白を1つ入れる（「依頼を出した CC の導出」の書き方にそろえる。直す前の試しで「CCの導出」になった）
    return re.sub(r"私(?![的たち達])\s?", "依頼を出した CC ", str(s if s is not None else ""))


def _version_diff(old: str, new: str) -> str:
    """承認した2つの版の設計書の違い＝違う行が どの囲み（ACC_<名前>）の中か、囲みの外かを数える。"""
    import difflib
    def blocks(path):
        cur, out = "囲みの外", []
        for ln in open(path, encoding="utf-8").read().splitlines():
            m = re.search(r"<!-- ACC_([A-Z0-9_]+)_START", ln)
            if m:
                cur = m.group(1)
            out.append((cur, ln))
            if re.search(r"<!-- ACC_[A-Z0-9_]+_END", ln):
                cur = "囲みの外"
        return out
    a, b = blocks(old), blocks(new)
    cnt: dict = {}
    sm = difflib.SequenceMatcher(None, [x[1] for x in a], [x[1] for x in b], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        for k in [x[0] for x in a[i1:i2]] + [x[0] for x in b[j1:j2]]:
            cnt[k] = cnt.get(k, 0) + 1
    if not cnt:
        return "無し（同じ）"
    parts = [(f"囲みの外で {v} 行" if k == "囲みの外" else f"ACC_{k} の囲みの中で {v} 行") for k, v in sorted(cnt.items())]
    return "・".join(parts) + f"（実装の指示の囲み ACC_IMPL は{'同じ' if 'IMPL' not in cnt else '違う'}）"


def _dirty_outside(targets: list) -> list:
    """この工事の対象（TARGET）の外で、作業中の変更が在るコード（.py・.sh・.json）の一覧（git status から）。"""
    import subprocess
    st = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
    out = []
    for line in st.splitlines():
        f = line[3:].strip().split(" -> ")[-1].strip('"')
        if not f.endswith((".py", ".sh", ".json")):
            continue
        if not any(s in f for s in ("scripts/priority_rebuild/", ".claude/hooks/", ".claude/tools/")):
            continue
        # ★2026-10-13（174回目・まこさん「いいけど」）＝TARGET が「../../.claude/…」（SDK からの相対）の形でも、同じファイルと見分ける。
        #   直す前＝git の出すパス（根からの形）の末尾と文字が合わず、工事 design-origin-form-20261013 の直す相手2本が「工事の外」に並んだ。
        if any(f.endswith(str(t).strip().replace('../../', '', 1)) for t in targets if str(t).strip()):
            continue
        out.append(f)
    return sorted(out)


M2_TODO = os.path.join(SDK, ".claude", "ratchet", "m2_todo.json")


def todo_numbers_from_table(wdir) -> list:
    """やることの表の項目の節（「## 一覧」から「## 手書きの項目」の前まで）に書いてある やることの番号のうち、
    m2_todo.json に在るもの（出てきた順）。
    ★2026-10-01（142回目・cp57）＝設計書を作る道具は「やることの番号」をいつも空にする（gen_acceptance.py の src_from_work）ので、
      依頼書が「やることの番号なし」と出た（実物はやることの表の B-1 の行に M2-F-13b・M2-F-7 が在る）。
      ★手書きの項目の節（次にやること M2-F-8 など）は数えない。"""
    try:
        t = open(os.path.join(str(wdir), "やることの表.md"), encoding="utf-8").read()
        known = {str(r.get("番号")) for r in (json.load(open(M2_TODO, encoding="utf-8")).get("やること") or [])}
    except (OSError, ValueError):
        return []
    m = re.search(r"^## 一覧.*?(?=^## 手書きの項目)", t, re.S | re.M)
    seen: list = []
    for n in re.findall(r"M2-[A-Z]+-\d+[a-z]?", m.group(0) if m else ""):
        if n in known and n not in seen:
            seen.append(n)
    return seen


def _sdk(p) -> str:
    """設計書の「対象のファイル」（SDK からの相対）を、依頼書の決まり（パスは根からの相対・SDK＝略称）に合わせる。
    ★2026-10-01（142回目・cp57）＝直す前は scripts/… のまま出し、依頼書の「パスはリポジトリの根からの相対」と食い違った。"""
    s = _one_line(p)
    return s if (not s or s.startswith(("SDK/", "v3-bitget-api-sdk/", ".claude/", "/"))) else "SDK/" + s


# ★2026-10-02（144回目・まこさん「以前の監査依頼書のほうが精度が高かった。自動生成にして精度がだいぶ下がった」「私の提案の通りに修正する」）
#   ＝判断が要る4つ（この工事は何のためか・必読・工事ごとの問い・要望のまとめ）は、CC が工事のフォルダの1本のファイルに手で書き、
#     まこさんの OK をもらう。経緯は1＝この工事は何のためか（手書き）・2＝この工事は何か＋目標からのつながり（道具）だけ
#     （まこさん「１は必要な情報だと思うが他はよくわからない」「前回の経緯にあった１の内容はかなり重要な要件なんだが」）。
#     道具はそれをそのまま写し、事実（パス・commit・承認の印・当てた記録）だけを実物から写す。
#   直す前（2026-09-29〜10-02）は4つとも道具が自動で作り、経緯は道具の出どころの説明、必読は逐語のファイルの列、
#   問いはどの工事でも同じ6問になった（cp58）。手書きの元データから作った cp49 は、必読16件に範囲となぜ要るかが在り、問いも工事ごとに10問あった。
HAND_MD = "監査依頼の手書き（{label}）.md"
HAND_FORM = """# 監査依頼の手書き（実装の監査）｜工事 <工事名>

## この工事は何のためか
| 何のためか | 出どころ |
|---|---|
| <この工事の目的（まこさんの決定・要望から。手段ではなく、なぜ作るのか）> | req_x_20260101:V03 |

## 経緯
<この監査に至るまでに何があったか（日付・誰が・何を決めたか・前の監査の結果・見つかった問題）を 3〜5 行。無くてよい>

## なぜこの監査が要るか
<設計書の無い直しなど、要るときだけ。無くてよい>

## 必読
| ファイルと範囲 | なぜ要るか |
|---|---|
| `SDK/scripts/priority_rebuild/x.py`（:10-20・:35） | <何を照らすために読むか> |

## 必読に入れないもの
| ファイル | 理由 |
|---|---|
| y.json | <実装が名前を出すが、この監査では読まない理由> |

## 工事ごとの問い
### Q8 — <名前>（優先度 A）
理由：<この問いが外れると何が起きるか>
<監査に見てほしいこと>

## 要望のまとめ
| 要望 | 出どころ |
|---|---|
| 目的：<1件目は、この工事の目的を要望の形で書く> | req_x_20260101:V03 |
| <まこさんの要望を CC がまとめた文（まこさんが OK）> | req_x_20260101:V04 |
"""
# まこさんとのやり取りの逐語のファイルの名前（req_・ok_・okd_）。監査は逐語を読まない（設計書の監査の okd_ だけは問い W で照らす）
VERBATIM_NAME_RE = re.compile(r"(?<![A-Za-z0-9_])(?:req|okd?)_[A-Za-z0-9]+(?:_\d{8})?")
NEED_NAME = "必読に要るファイル（道具が設計書と実装から拾った）"
READ_NAME_RE = re.compile(r"[A-Za-z0-9_./\-]+\.(?:json|jsonl|csv|parquet|py)\b")
IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_]\w*)", re.M)
RANGE_RE = re.compile(r":(\d+)(?:[-〜](\d+))?")
FIND_DIRS = (os.path.join(SDK, "scripts"), os.path.join(SDK, ".claude", "ratchet"), os.path.join(SDK, ".claude", "memory"),
             os.path.join(SDK, ".claude", "rules"), os.path.join(ROOT, ".claude", "state"))


def _req_style(full: str) -> str:
    """実物のパスを、依頼書の書き方（SDK/… か根からの相対）にする。"""
    rel = os.path.relpath(os.path.realpath(full), os.path.realpath(ROOT))
    sdk = os.path.relpath(SDK, ROOT)
    return "SDK/" + rel[len(sdk) + 1:] if rel.startswith(sdk + os.sep) else rel


def _find_file(name: str, base: str) -> str:
    """実装の中の名前（パスつきか名前だけ）から、実在するファイルを探す。無ければ空。控え（archive・監査の作業場）は見ない。"""
    import glob
    for d in (base, ROOT, SDK, os.path.join(SDK, "scripts", "priority_rebuild")):
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return _req_style(p)
    b = os.path.basename(name)
    for d in FIND_DIRS:
        hit = [h for h in glob.glob(os.path.join(d, "**", b), recursive=True)
               if "/archive" not in h and "/audits/cp" not in h and "_selftest" not in h]
        if hit:
            return _req_style(sorted(hit)[0])
    return ""


def need_reads(d: dict, ev: dict, kind: str, todos: list = ()) -> list:
    """必読に要るファイル＝目標と目的を書いた文書・直す相手（TARGET）・新しく作るファイル（NEW_FILE）と、
    実装の監査では実装が名前を出す json・py。
    ★2026-10-02（144回目・まこさん「実装データや必要なjsonデータなども確認すべきでは？」）
      ＝新しく作った .py は全文、直した .py は実装の前後の差分の足した行から、ファイルの名前と読み込むモジュールを拾う。
    ★2026-10-02（144回目・まこさん「全月 net ≥ $1,900（単月判定・通算でない）を達成するために、要件定義を踏まえたうえで、
      マイルストーン＞フロー＞やることリストへと落とし込んでおり…なぜ、大前提となる文書を読まずに判定を依頼するという判断になるのか不明」）
      ＝売買のロジックに触る工事は、要件定義書・engine_tuner の要件・マイルストーンが要る。milestones2 は、やることの番号が M2 の工事だけ
      （まこさん「milestone２の内容の監査なら必要だが、それ以外の監査では不要」）。
    戻り＝[(パス, どこから拾ったか, 必読に入れないことを手書きで決めてよいか)]。"""
    import subprocess
    import gen_acceptance as ga
    tg, nf = list(d.get("TARGET") or []), list(d.get("NEW_FILE") or [])
    out, seen = [], set()
    docs = []
    if ga.touches_trading(d):
        docs += [("SDK/.claude/rules/cat_requirements.md", "要件定義書（売買のロジックに触る工事）"),
                 ("SDK/.claude/ratchet/engine_tuner_requirements.md", "engine_tuner の要件（売買のロジックに触る工事）"),
                 ("SDK/.claude/ratchet/engine_tuner_milestones.md", "engine_tuner のマイルストーン（売買のロジックに触る工事）")]
    if any(str(t).startswith("M2-") for t in todos):
        docs.append(("SDK/.claude/ratchet/engine_tuner_milestones2.md", f"M2 のマイルストーン（やることの番号 {'・'.join(todos)}）"))
    for p, why in docs:
        out.append((p, why, False))
        seen.add(os.path.basename(p))
    for p, why in [(p, "直す相手（TARGET）") for p in tg] + [(p, "新しく作るファイル（NEW_FILE）") for p in nf]:
        r = repo_ref(p)
        if r and os.path.basename(r) not in seen:
            out.append((r, why, False))
            seen.add(os.path.basename(r))
    if kind != "impl":
        return out
    for p in dict.fromkeys(tg + nf):
        r = repo_ref(p)
        if not r or not r.endswith(".py"):
            continue
        full = repo_path(r)
        if p in nf:
            text = open(full, encoding="utf-8").read()
        else:
            rng_ = [ev["pre"], ev["post"]] if ev.get("post") else ["HEAD"]
            diff = subprocess.run(["git", "diff", *rng_, "--", full], cwd=ROOT, capture_output=True, text=True).stdout
            text = "\n".join(ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++"))
        names = set(READ_NAME_RE.findall(text)) | {m + ".py" for m in IMPORT_RE.findall(text)}
        for n in sorted(names):
            b = os.path.basename(n)
            if b in seen:
                continue
            loc = _find_file(n, os.path.dirname(full))
            if loc:
                out.append((loc, f"`{r}` が名前を出す（{'全文' if p in nf else '実装の前後の差分'}）", True))
                seen.add(b)
    return out


def _position_chain(todos: list) -> str:
    """この工事の位置＝目標から やることの番号までのつながり。マイルストーン2本の見出しと、やることリストの一文を道具が写す。
    ★2026-10-02（144回目・まこさん「経緯の定義がよくわからないんだが。１は必要な情報だと思うが他はよくわからない」）
      ＝経緯は「この工事は何か」の1つにし、目標からのつながりを添える。"""
    rat = os.path.join(SDK, ".claude", "ratchet")

    def head(name: str, pat: str) -> str:
        try:
            for ln in open(os.path.join(rat, name), encoding="utf-8"):
                if re.match(pat, ln):
                    # 見出しの後ろの日付つきの注記（「（2026-09-06 まこさん OK…）｜21件」ほか）は写さない＝何の段かだけを写す
                    return _one_line(ln.lstrip("#").strip().split("（20", 1)[0].rstrip("｜ "))
        except OSError:
            pass
        return ""
    try:
        stack = [json.load(open(os.path.join(rat, "m2_todo.json"), encoding="utf-8"))]
    except Exception:                                        # noqa: BLE001
        stack = []
    ones = {}
    while stack:
        x = stack.pop()
        if isinstance(x, dict):
            if x.get("番号") and x.get("一文"):
                ones.setdefault(str(x["番号"]), str(x["一文"]))
            stack += list(x.values())
        elif isinstance(x, list):
            stack += x
    parts = ["全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2）"]
    for t in todos:
        m = re.match(r"(M\d)-([A-Z]+)", str(t))
        if not m:
            continue
        for x in (head("engine_tuner_milestones.md", rf"^## {m.group(1)}｜"),
                  head("engine_tuner_milestones2.md", rf"^## {m.group(1)}-{m.group(2)}｜") if m.group(1) == "M2" else "",
                  f"{t}｜{_one_line(ones[t])}" if ones.get(t) else ""):
            if x and x not in parts:
                parts.append(x)
    return " → ".join(parts + ["この工事"])


def read_hand(wdir, label: str, kind: str, names: list, gv) -> dict:
    """工事のフォルダの「監査依頼の手書き（…）.md」を読む（CC が書き、まこさんが OK した4つ＝この工事は何のためか・必読・工事ごとの問い・要望のまとめ）。
    ★「この工事は何のためか」は経緯の1に、要望のまとめの1件目（「目的：」で始める）は問い2 の1件目に写す
      （2026-10-02・まこさん「前回の経緯にあった１の内容はかなり重要な要件なんだが」「本質を理解できてないのか？」）。
    ★経緯のほかの行は手で書かない。「## 経緯」が在れば止める（書いても写されないため）。
    止める所（fail-closed）＝ファイルが無い／経緯の節が在る／何のためかが無い・出どころが無い／必読の表が読めない・パスが無い・範囲がファイルの外／
      実装の監査で工事ごとの問いが無い・形が違う／要望のまとめ（req_ の逐語が在るとき）が無い・1件目が「目的：」でない・出どころが逐語の行に無い。"""
    import gen_acceptance as ga
    p = wdir / HAND_MD.format(label=label)
    if not p.is_file():
        raise SystemExit(f"工事のフォルダに {p.name} が無い（fail-closed）。判断が要る4つは CC が書き、まこさんの OK をもらう。形＝\n{HAND_FORM}")
    sec = ga._sections(p.read_text(encoding="utf-8").splitlines(), re.compile(r"^##\s+(?!#)(.+)$"))
    bad: list = []
    # ★2026-10-18（192回目・まこさん「「監査依頼の経緯」の説明文は入れたほうがいいのでは」）＝「## 経緯」（この監査に至るまでに
    #   何があったか・3〜5行）と「## なぜこの監査が要るか」を、手書きで書けるようにした。
    #   直す前（2026-10-02）は「## 経緯」が在れば止めていた（道具が作る経緯と二重になるため）。いまは道具の作る物（何か・位置・種類・目標）と
    #   手書きの経緯を、1つの「この監査は何のためか」の中に並べる。
    # ★同日（まこさん「必須にする」）＝「## 経緯」は必須。無ければ止まる（「なぜこの監査が要るか」は要るときだけ）。
    history = [ln for ln in (sec.get("経緯") or []) if ln.strip()]
    why_audit = [ln for ln in (sec.get("なぜこの監査が要るか") or []) if ln.strip()]
    if not history:
        bad.append("「## 経緯」が無い（この監査に至るまでに何があったかを、日付つきで3〜5行 書く・まこさん決定 2026-10-18「必須にする」）")
    reqs = [n for n in names if n.split("/")[-1].startswith("req_")]
    valid = {vid for n in reqs for vid, _l in gv.lines(n)}

    def check_src(src: str, where: str) -> None:
        """出どころ＝要望の逐語の行の番号（req_ の逐語が無い工事では、空でなければよい）。"""
        if not src.strip():
            bad.append(f"{where}に出どころが無い")
            return
        if not reqs:
            return
        for tok in re.split(r"[・,、\s]+", src.strip()):
            m = re.fullmatch(r"(\S+):V(\d+)(?:〜V?(\d+))?", tok)
            if not m:
                bad.append(f"{where}の出どころが番号の形でない（例 req_x_20260101:V03）: {tok}")
                continue
            for k in range(int(m.group(2)), int(m.group(3) or m.group(2)) + 1):
                if f"{m.group(1)}:V{k:02d}" not in valid:
                    bad.append(f"{where}の出どころ {m.group(1)}:V{k:02d} が、要望の逐語（req_ のファイル）の行に無い")
    purposes = []
    for r in ga._md_table(sec.get("この工事は何のためか") or [], ("何のためか", "出どころ"), "この工事は何のためか", bad):
        check_src(r["出どころ"], "この工事は何のためか")
        purposes.append(r["何のためか"])
    if not purposes:
        bad.append("「## この工事は何のためか」に行が無い（目的を先頭に書く）")
    reads = []
    for r in ga._md_table(sec.get("必読") or [], ("ファイルと範囲", "なぜ要るか"), "必読", bad):
        m = re.match(r"`([^`]+)`(.*)$", r["ファイルと範囲"])
        if not m or not r["なぜ要るか"]:
            bad.append(f"必読の行に「`パス`」か、なぜ要るかが無い: {r['ファイルと範囲'][:50]}")
            continue
        full = repo_path(m.group(1))
        if not os.path.isfile(full):
            bad.append(f"必読のファイルが無い: {m.group(1)}")
            continue
        n = sum(1 for _ in open(full, encoding="utf-8", errors="replace"))
        for a, b in RANGE_RE.findall(m.group(2)):
            if not (1 <= int(a) <= int(b or a) <= n):
                bad.append(f"必読の範囲がファイルの外: {m.group(1)}:{a}{'-' + b if b else ''}（{n} 行）")
        reads.append((m.group(1), m.group(2).strip(), r["なぜ要るか"]))
    skips = ga._md_table(sec["必読に入れないもの"], ("ファイル", "理由"), "必読に入れないもの", bad) if "必読に入れないもの" in sec else []
    qs, cur = [], None
    for ln in sec.get("工事ごとの問い") or []:
        m = re.match(r"^###\s+(Q\d+)\s+—\s+(.+?)（優先度 ([A-D])）\s*$", ln)
        if m:
            cur = {"番号": m.group(1), "名前": m.group(2), "優先度": m.group(3), "理由": "", "body": []}
            qs.append(cur)
        elif cur is not None and ln.startswith("理由："):
            cur["理由"] = ln[len("理由："):].strip()
        elif cur is not None:
            cur["body"].append(ln)
    for i, q in enumerate(qs):
        q["body"] = "\n".join(q["body"]).strip()
        if q["番号"] != f"Q{8 + i}":
            bad.append(f"工事ごとの問いの番号は Q8 から順に（いま {q['番号']}・{i + 1} 件目）")
        if not q["理由"] or not q["body"]:
            bad.append(f"工事ごとの問い {q['番号']} に「理由：」の行か、見てほしいことが無い")
    if kind == "impl" and not qs:
        bad.append("「## 工事ごとの問い」に「### Q8 — 名前（優先度 A）」の問いが1つも無い")
    wants = []
    if kind == "impl" and reqs:
        for r in ga._md_table(sec.get("要望のまとめ") or [], ("要望", "出どころ"), "要望のまとめ", bad):
            check_src(r["出どころ"], "要望のまとめ")
            if not r["要望"].startswith("対象外："):
                wants.append(r["要望"])
        if not wants:
            bad.append("要望のまとめに、この工事の要望が1件も無い（全部「対象外：」か、表が無い）")
        elif not wants[0].startswith("目的："):
            bad.append("要望のまとめの1件目が「目的：」で始まらない（この工事の目的を一番上の要望にする）")
    if bad:
        raise SystemExit(f"{p.name} を読めない（fail-closed）:\n  " + "\n  ".join(bad))
    return {"目的": purposes, "必読": reads, "入れない": skips, "問い": qs, "要望": wants, "path": p,
            "経緯": history, "なぜ要る": why_audit}


def want_list(wants: list) -> str:
    """問い2・Q7 に並べる要望（1件ずつ番号つき）。"""
    return "\n".join(f"  {i}. {_one_line(w)}" for i, w in enumerate(wants, 1))


def request_content_errors(text: str) -> list:
    """できた依頼書の中身のチェック。build_request（書く前）と gen_review.check（見直し表の照らし・Stop hook）の両方が呼ぶ。
    ★2026-10-02（144回目・まこさん「監査依頼書のなにをチェックしてるわけ？」「監査依頼書が出来たあとにチェックする強制もなおせ」）
      ＝直す前のチェックは形だけ（節が在るか・番号・ファイルが実在するか・見直し表の欄が埋まっているか）で、
        必読に要る文書が無くても、まこさんの発言の逐語が並んでいても通った（cp58）。
      見るもの＝必読に設計書・直す相手・実装が名前を出す json と py が在るか（「必読に要るファイル」の事実データと照らす）／
        必読の範囲がファイルの中か／逐語のファイルと要件のまとめが無いか／経緯に「この工事は何か」が在るか／問い2 と Q7。"""
    errs = []

    def sec(head: str) -> str:
        return text.split(f"\n## {head}", 1)[1].split("\n## ", 1)[0] if f"\n## {head}" in text else ""
    reads = sec("着手前必読")
    # ★2026-10-07（まこさん「A」）＝監査の相手は、依頼書の「監査の相手と版」に書いた設計書（--design で控えを渡すと、その控え）
    _tm = re.search(r"- 監査の相手と版: `([^`]+)`", text)
    _tgt = _tm.group(1) if _tm else ".claude/state/acceptance.md"
    if f"`{_tgt}`" not in reads:
        errs.append(f"着手前必読に、監査の相手の設計書（{_tgt}）が無い")
    read_names = {os.path.basename(t) for t in re.findall(r"`([^`]+)`", reads)}
    need = text.split(f"\n### {NEED_NAME}", 1)[1].split("\n## ", 1)[0].split("\n### ", 1)[0] if f"\n### {NEED_NAME}" in text else ""
    # ★2026-10-18（ToDo の15番）＝設計書の無い直しの監査は、道具が設計書から要るファイルを拾えない（必読は CC が手で書く）
    nodesign = f"- 監査の種類: {NODESIGN_LABEL}" in text
    if not need and not nodesign:
        errs.append(f"事実データに「{NEED_NAME}」が無い＝必読に要るファイルを照らせない")
    for row in re.findall(r"^\| `([^`]+)` \| [^|]* \| ([^|]+) \|$", need, re.M):
        if row[1].strip().startswith("入れる") and os.path.basename(row[0]) not in read_names:
            errs.append(f"着手前必読に、要るファイル {row[0]} が無い（{NEED_NAME}）")
    for tok, rest in re.findall(r"`([^`\s]+)`((?:（[^）]*）)?)", reads):
        full = repo_path(tok)
        if rest and os.path.isfile(full):
            n = sum(1 for _ in open(full, encoding="utf-8", errors="replace"))
            for a, b in RANGE_RE.findall(rest):
                if not (1 <= int(a) <= int(b or a) <= n):
                    errs.append(f"着手前必読の範囲がファイルの外: {tok}:{a}{'-' + b if b else ''}（{n} 行）")
    if "要件のまとめ.md" in reads:
        errs.append("着手前必読に 要件のまとめ.md（逐語のまとめ）が在る＝監査は逐語を読まない")
    impl = "（実装の監査）" in text.split("\n", 1)[0]
    for name, part in (("着手前必読", reads), ("監査依頼の経緯", sec("監査依頼の経緯"))):
        for m in VERBATIM_NAME_RE.findall(part):
            if impl or not m.startswith("okd_"):
                errs.append(f"{name}に、まこさんとのやり取りの逐語のファイル（{m}）が在る＝監査は逐語を読まない（要望は問い2 にまとめて書く）")
    # ★2026-10-18（192回目）＝「監査依頼の経緯」は「この監査は何のためか（目的と経緯）」になった。問い2 と Q7 の組の検査は無くした
    #   （結論を決める問いの段そのものを無くしたため）。
    # ★2026-10-21（199回目）＝見出しの語の後ろは「：」（公用文作成の考え方の書き方に直した・「＝」でつながない）
    if not re.search(r"^1\. \*\*この工事は何のためか\*\*：\S", sec("この監査は何のためか"), re.M):
        errs.append("「この監査は何のためか」の1が「この工事は何のためか」でない（目的が先頭に無い）")
    if "**この工事は何か**：" not in sec("この監査は何のためか"):
        errs.append("「この監査は何のためか」に「この工事は何か」が無い")
    # ★2026-10-12（A-2・まこさん「OK」）＝固定で載せる文（要件定義と工事の流れ）が依頼書に無ければ書かない
    if CORE_MARK not in text:
        errs.append(f"依頼書に、固定で載せる文（{CORE_MARK}）が無い＝正本 .claude/rules/core_requirements.md から写す節が抜けている")
    # ★2026-10-12＝要望の並びの照らしは、実装の監査の要望の問い（Q7）だけに掛ける（2026-10-18＝置き場が問い2 から Q7 の本文に移った）
    q7 = text.split("### Q7 — まこさんの要望", 1)[-1].split("\n### ", 1)[0] if "### Q7 — まこさんの要望" in text else ""
    if q7 and impl:
        if not re.search(r"^  \d+\. \S", q7, re.M):
            errs.append("Q7 の下に要望が1件も無い")
        if not re.search(r"^  1\. 目的：\S", q7, re.M):
            errs.append("Q7 の要望の1件目が「目的：」でない（この工事の目的が先頭に無い）")
        if re.search(r"発言 `|`[^`]+:V\d+`", q7):
            errs.append("Q7 に逐語の行（発言の名前・V番号）がそのまま在る＝まこさんが OK した要望のまとめを書く")
    return errs


def _speaker(gv, name: str) -> str:
    """逐語のファイルの話し手（控えの who）から、誰の文かを言葉にする。"""
    try:
        _t, m = gv.paths(name)
        who = set(json.load(open(m, encoding="utf-8")).get("who") or [])
    except Exception:                                        # noqa: BLE001
        who = set()
    if who == {"まこさん"}:
        return "まこさんの発言"
    if who == {"CC"}:
        return "まこさんが OK した CC の文"
    return "まこさんの発言と CC の文"


def _impl_evidence(iter_: str) -> dict:
    """実装の監査の材料＝承認の控え・実装の前と後の commit・当てた記録（道具が実物から数える）。

    ★2026-09-30（3点目-a・まこさん OK「OK」）＝実装の監査は「設計書のとおりに、道具が実装を作れているか」だけを問う。
      その照合に要る材料（どの版の設計書で当てたか・実装の前と後・当てた記録）を、CC が書かずに実物から出す。
    """
    import glob
    import subprocess
    arc = os.path.join(SDK, ".claude", "ratchet", "acceptance_archive")
    archives = sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(arc, f"{glob.escape(iter_)}*.md"))
                      if re.fullmatch(rf"{re.escape(iter_)}(\.\d+)?\.md", os.path.basename(p)))
    post = pre = ""
    if archives:
        r = subprocess.run(["git", "log", "-1", "--format=%h %p", "--", os.path.join(ROOT, archives[0])],
                           cwd=ROOT, capture_output=True, text=True)
        parts = r.stdout.split()
        if len(parts) >= 2:
            post, pre = parts[0], parts[1]
    try:
        rows = json.load(open(os.path.join(AUDITS, "applied_fixes.json"), encoding="utf-8")).get("applied") or []
    except Exception:                                        # noqa: BLE001
        rows = []
    applied = [r for r in rows if isinstance(r, dict) and r.get("report") == f"design:{iter_}"]
    # ★2026-10-01（142回目・cp57）＝直す前は、承認の控えをまだ commit していないと pre・post が空になり、
    #   依頼書に「commit （まだ commit していない）」とだけ出た＝監査は、どの版と比べればよいか決められなかった。
    #   いま＝控えが commit されていなければ、実装の前＝HEAD の版、実装の後＝作業中の変更（git diff HEAD）と書く。
    if post:
        pre_desc, post_desc = f"commit {pre}", f"commit {post}"
    else:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        pre_desc = (f"commit {head or '（読めない）'}（依頼書を作った時点の HEAD。承認の控えをまだ commit していないので、実装の前はこの commit の版。"
                    f"`git show {head or 'HEAD'}:<パス>` で出せる。★この後に commit しても、この番号で出せる）")
        post_desc = (f"依頼書を作った時点の作業中の変更（まだ commit していない。`git diff {head or 'HEAD'} -- <パス>` で見られる。"
                     "★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、"
                     f"`git diff {head or 'HEAD'} <その commit> -- <パス>` で見る）")
    return {"archives": archives, "pre": pre, "post": post, "applied": applied,
            "pre_desc": pre_desc, "post_desc": post_desc}


def _stack_note(ev: dict, iter_: str, targets: list) -> None:
    """同じファイルに、まだ commit していない別の工事の直しが重なっていれば、Q1・Q2 の「実装の前・後」の文に書き足す。
    ★2026-10-07（まこさん「A」＝同じ日の3つの工事を工事ごとに監査する）＝直す前は、実装の前＝HEAD・実装の後＝作業中の変更と
      だけ書いたので、同じ設定ファイルを続けて直した2つ目の工事の行が、1つ目の工事の依頼書で「設計書に無い変更」に見えた。
    重なりの判定＝当てた記録（applied_fixes.json）の design:<別の工事> の行のうち、時刻が HEAD の commit より後で、
      ファイルがこの工事の TARGET と同じもの。前と後は、当てた時刻で分ける。"""
    if ev.get("post"):                                       # 承認の控えが commit 済み＝commit どうしで比べられる
        # ★監査 CP73 の修正3＝commit どうしで比べる形でも、実装の後の commit に G-1 の作り直しが入る。
        #   この関数の末尾の注記（監査 CP69 の修正10）は、ここで戻るので、この形の依頼書には出ていなかった。
        ev["post_desc"] += ("。★この工事の中で、設計書の 4-4 の手順（G-1 の表の作り直しほか）の道具が、TARGET のファイルを書き出し直すことがある"
                            "（例＝gen_materials.py --write が regime_detection_kb.md の件数の囲みを書き出す）。その行は実装の指示ではなく、設計書の 4-4・5 で照らす")
        return
    import subprocess
    head_at = subprocess.run(["git", "log", "-1", "--format=%cd", "--date=format:%Y-%m-%dT%H:%M:%S", "HEAD"],
                             cwd=ROOT, capture_output=True, text=True).stdout.strip()
    try:
        rows = json.load(open(os.path.join(AUDITS, "applied_fixes.json"), encoding="utf-8")).get("applied") or []
    except Exception:                                        # noqa: BLE001
        return
    mine = [r for r in (ev.get("applied") or []) if r.get("at")]
    if not head_at or not mine:
        return
    tset = {_sdk(t) for t in targets}
    my_first, my_last = min(r["at"] for r in mine), max(r["at"] for r in mine)
    before, after = {}, {}
    for r in rows:
        rep = str(r.get("report") or "")
        if not (isinstance(r, dict) and rep.startswith("design:") and rep != f"design:{iter_}"):
            continue
        if str(r.get("at") or "") <= head_at or _sdk(r.get("file")) not in tset:
            continue
        box = before if r["at"] < my_first else after if r["at"] > my_last else None
        if box is not None:
            box.setdefault(rep[len("design:"):], set()).add(_sdk(r.get("file")))

    def _names(box: dict) -> str:
        return "・".join(f"{w}（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/{w}.md` の 4-20・"
                        f"{'・'.join(f'`{f}`' for f in sorted(fs))}）" for w, fs in sorted(box.items()))
    if before:
        ev["pre_desc"] += (f"。★同じファイルに、この工事より前に当てた別の工事の直しが重なっている＝{_names(before)}。"
                           "実装の前は、HEAD の版に、その工事の実装の指示を当てた時刻の順に当てた版")
    if after:
        ev["post_desc"] += (f"。★同じファイルに、この工事より後に当てた別の工事の直しも入っている＝{_names(after)}。"
                            "実装の後は、実装の前にこの工事の実装の指示を当てた版。作業中の変更と比べるときは、"
                            "後の工事の実装の指示を同じ順に当ててから比べる（後の工事の行は、その工事の依頼書で照らす）")

    ev["post_desc"] += ("。★この工事の中で、設計書の 4-4 の手順（G-1 の表の作り直しほか）の道具が、TARGET のファイルを書き出し直すことがある"
                        "（例＝gen_materials.py --write が regime_detection_kb.md の件数の囲みを書き出す）。その行は実装の指示ではなく、設計書の 4-4・5 で照らす")


def _head_name(md: str, sec: str) -> str:
    """索引の対応の書き方の節（「4-3」「3-0 目標の③」ほか）を、設計書の見出しの文字（「4-3 部品と責任の割り当て」ほか）にする。
    見出しが見つからなければ、節の番号のまま。"""
    base, _, tail = sec.partition(" ")
    # 書いた見出しは「### 4-3 …」、非該当の項目は見出しが無いので 4-A の一覧の表（| 4-7 | 条件 | 探索の範囲（…） | …）から探す
    m = (re.search(rf"^### {re.escape(base)} (.+?)\s*$", md, re.M)
         or re.search(rf"^\| {re.escape(base)} \| [^|]+ \| ([^|]+?) \|", md, re.M))
    name = f"{base} {m.group(1).split('（')[0].strip()}" if m else base
    if tail.startswith("目標の"):
        name += tail[len("目標"):]                 # 「3-0 目標」＋「の③」
    return name


def _fix_lines(secs: list, src_label: str, okd: str) -> list:
    """節の誤りを直す修正の書き先（文の行）。やることの表.md の物は自動で直る。まこさんが OK した案の写しの物は直らない
    （修正を当てるプログラムは、逐語のファイルに当てない＝apply_audit_fix.py の is_verbatim）。"""
    import gen_acceptance as ga
    L: list = []
    # ★2026-10-21（199回目）＝文を、公用文作成の考え方の書き方に直した（主語＝あなた・プログラム・CC を書く）
    if any(s in ("2-0", "3-0 目標の①") for s in secs):
        L += [f"「この工事が結ぶ要件と、減らす違い」の誤りを見つけたら、修正の指示を、設計書の元（{src_label}）の"
              "「### この工事が結ぶ要件と、減らす違い」の表に書いてください。", *FIX_AUTO,
              "やることの番号と結ぶ要件は、プログラムが、読むもの宣言から写しています。"
              "この2つの誤りを見つけたら、修正の指示にせず、所見に書いてください。"]
    if any(s.startswith("3-0 目標の") and s != "3-0 目標の①" for s in secs) or "goal" in secs:
        L += [f"目標の誤りを見つけたら、修正の指示を、設計書の元（{src_label}）の「### 目標」の表に書いてください。", *FIX_AUTO]
    if "概要" in secs:
        L += [f"目的の誤りを見つけたら、修正の指示を、設計書の元（{src_label}）の「### §1 概要」に書いてください。", *FIX_AUTO]
    if "一覧" in secs:
        L += [f"一覧の誤りを見つけたら、修正の指示を、設計書の元（{src_label}）の「## 一覧」の表に書いてください。", *FIX_AUTO]
    if "plan" in secs:
        L.append("設計書の「結ぶ要件」は、プログラムが、読むもの宣言から写しています。結ぶ要件の誤りを見つけたら、修正の指示にせず、所見に書いてください。")
    heads = [{"4-21": ga.HEAD_NUMS, "4-22": ga.HEAD_FIVE}.get(s, s) for s in secs
             if s.startswith(("4-", "7-")) or s in ("5", ga.HEAD_UNVERIFIED)]
    if heads:
        L += [f"誤りを見つけたら、修正の指示を、まこさんが OK した案の写し（{okd}）の、"
              + "か".join(f"【{h}】" for h in dict.fromkeys(heads)) + "の見出しの下に書いてください。", *FIX_OK]
    if any(s in ("4-6", "4-7") for s in secs):
        L.append("ただし、設計書で［自動］の印が付いた行のうち、置き場のファイルから写した行の誤りは、"
                 "案の写しではなく、写した元の置き場のファイルに書いてください。"
                 "置き場のファイルは、法則のファイル・型の表・指標のオンとオフの表・資料の表です。")
    if "any" in secs:
        L.append("修正の指示を、その文が在る見出しの書き先に書いてください。"
                 "見出しごとの書き先は、この依頼書の「修正をどこに書くか」の節に書いてあります。")
    return L


def _design_new_questions(d: dict, md: str, src_label: str, okd: str) -> list:
    """新しい形の設計書の監査の、決まった問い（要件ごとの問い R・どの工事にも出す問い F・検査やプログラムを直す工事の問い K）。
    戻り＝[(番号, 優先度, 優先度の理由, 名前, 本文)]。★問いの文は CC が書かない（正本の要件の行・索引の対応・工事の種類から組む）。"""
    import gen_acceptance as ga
    import gen_core_requirements as gcr
    kind = ga.work_kind(d)
    out = []
    na_only: list = []                                   # 設計書の節が全部「非該当」の要件＝1つの問い RN にまとめる

    def hn(ss: list) -> str:
        return "」と「".join(_head_name(md, s) for s in ss)
    # ★2026-10-21（199回目・まこさん「同じ問いを繰り返してるけど。いいの？」「今後二度とこのようなミスを繰り返せないような作りに」）
    #   ＝見る節が同じ要件は、1つの問いにまとめる。直す前は要件の番号ごとに1問を作り、依頼書 CP83 で R3-1〜R3-5・R4 の6問が、
    #   同じ「4-7 探索の範囲」を読ませる同じ文になった。まとめた問いの番号は、いちばん前の要件の番号（例＝R3-1）。
    groups: dict = {}
    for no, raw_name in gcr.requirement_items(full=True):
        # ★2026-10-18（192回目・別の CC の冷たい読み）＝全文の見出しの括弧の注記（「★この節は私の言葉です」ほか）は、問いの題に出さない
        name = re.sub(r"（[^（）]*）\s*$", "", raw_name).strip()
        secs = ga.INDEX_MAP.get(no)
        if not secs:
            raise SystemExit(f"要件定義の {no}（{name}）を書く節が、索引の対応（gen_acceptance.INDEX_MAP）に無い（fail-closed）")
        st = {s: ga.sec_state(d, s)[0] for s in secs}
        wr = [s for s in secs if st[s] == "書いた"]
        empty = [s for s in secs if st[s] in ("書いていない", "空")]
        na = [s for s in secs if st[s] == "非該当"]
        if na and not wr and not empty:
            # ★2026-10-18（192回目・まこさん「まとめる」）＝触らない要件は、同じ15行の問いを要件の数だけ並べず、1つの問い RN にまとめる
            na_only.append((no, name, hn(na), na))
            continue
        groups.setdefault((tuple(wr), tuple(empty), tuple(na)), []).append((no, name))
    for (wr_t, empty_t, na_t), reqs in groups.items():
        wr, empty, na = list(wr_t), list(empty_t), list(na_t)
        nos = [n for n, _m in reqs]
        no = nos[0]
        # ★2026-10-21（199回目）＝文を、公用文作成の考え方の書き方に直した（主語＝あなた・CC を書く）
        many = "" if len(reqs) == 1 else "要件ごとに1行で答えてください。"
        if len(reqs) == 1:
            L = [f"要件定義の{no}番は、「{reqs[0][1]}」です。", "要件定義の要約は、この依頼書の上の方に載っています。", ""]
            subj, it = f"要件定義の{no}番", "この要件"
        else:
            L = ["次の要件は、設計書の同じ見出しに書いてあります。見る見出しが同じなので、この問いは、次の要件を1つにまとめました。", ""]
            L += [f"- 要件定義の{n}番「{m}」" for n, m in reqs]
            L += ["", "要件定義の要約は、この依頼書の上の方に載っています。", ""]
            subj, it = "上の要件のどれか", "これらの要件"
        if len(wr) == 1:
            L += [f"CC は、{it}に当たる中身を、設計書の「{hn(wr)}」の見出しに書きました。",
                  f"この見出しを読み、{subj}に反する所や、書き漏れが無いかを確かめてください。" + many]
        elif wr:
            L += [f"CC は、{it}に当たる中身を、設計書の{len(wr)}つの見出しに書きました。", f"その見出しは、「{hn(wr)}」です。",
                  f"この{len(wr)}つの見出しを読み、{subj}に反する所や、書き漏れが無いかを確かめてください。" + many]
        if empty:
            L.append(f"設計書の「{hn(empty)}」の見出しは、中身が空です。CC がこの見出しに中身を書くべきだったかを確かめてください。")
        if na and (wr or empty):
            # ★2026-10-18（192回目）＝「書いてある」と「当たらない」が1つの問いに混ざるときは、つなぎの文を入れる
            L += ["", f"{it}に当たる見出しは、もう1つあります。その見出しは「{hn(na)}」で、CC は「この工事には当たらない」と書きました。"]
        if na and kind == 2:
            L += ["この工事は、検査やプログラムを直す工事です。",
                  f"そのため、CC は、設計書の「{hn(na)}」の見出しに、「この工事には当たらない」と書きました。"] * (not (wr or empty)) + [
                  "その代わりに、CC は、設計書の「4-22 検査やプログラムを直す工事で書く5つ」の⑤に、根拠を書きました。",
                  f"その根拠は、この工事が{subj if len(reqs) == 1 else 'これらの要件'}に触らないと言える根拠です。",
                  "根拠は、走らせたコマンドと、その結果です。",
                  "その根拠で、本当に触らないと言えるかを確かめてください。"]
        elif na:
            L += [f"CC は、設計書の「{hn(na)}」の見出しに、「この工事には当たらない」と、その理由を書きました。",
                  "その理由で、本当に当たらないと言えるかを確かめてください。"]
        L += [""] + _fix_lines(wr + empty + (["4-22"] if (na and kind == 2) else na), src_label, okd)
        _title = (f"要件定義の{no}番「{reqs[0][1]}」が、設計書に正しく書かれているか" if len(reqs) == 1
                  else f"要件定義の{'・'.join(nos)}番が、設計書の同じ見出しに正しく書かれているか")
        out.append((f"R{no}", "A", NEW_WHY_R, _title, "\n".join(L).strip()))
    if na_only:
        verb = "触らない" if kind == 2 else "当たらない"
        nos = "・".join(no for no, _n, _h, _s in na_only)
        L = ["CC は、次の要件について、設計書に「この工事には当たらない」と書きました。", ""]
        L += [f"- 要件定義の{no}番「{name}」：設計書の見出しは、「{h}」です。" for no, name, h, _s in na_only]
        L.append("")
        if kind == 2:
            L += ["この工事は、検査やプログラムを直す工事です。",
                  "CC は、当たらない根拠を、設計書の「4-22 検査やプログラムを直す工事で書く5つ」の⑤に書きました。根拠は、走らせたコマンドと、その結果です。",
                  "その根拠で、上の要件のどれにも本当に触らないと言えるかを、要件ごとに1行で答えてください。"]
            fix_secs = ["4-22"]
        else:
            L += ["CC は、それぞれの見出しに、当たらない理由を書きました。",
                  "その理由で本当に当たらないと言えるかを、要件ごとに1行で答えてください。"]
            fix_secs = [s for _n, _m, _h, ss in na_only for s in ss]
        L += [""] + _fix_lines(list(dict.fromkeys(fix_secs)), src_label, okd)
        out.append(("RN", "A", NEW_WHY_R, f"この工事が{verb}と書いてある要件（{nos}）に、本当に{verb}か", "\n".join(L).strip()))
    for num, name, why, body, place in DESIGN_F:
        fx = [] if place is None else _fix_lines([place], src_label, okd)
        out.append((num, "A", why, name, "\n".join(list(body) + ([""] + fx if fx else [])).strip()))
    if kind == 2:
        for num, name, why, body in DESIGN_K:
            out.append((num, "A", why, name, "\n".join(list(body) + [""] + _fix_lines(["4-22"], src_label, okd)).strip()))
    return out


# ══ 2026-10-21（199回目）＝新しい形の設計書の監査の問い（固定の問い F1〜F13 と、設計書の主張から作る問い C1〜C3）══════════
#   まこさん（2026-10-21・逐語）「工事の内容に対して、監査でチェックを依頼する内容がミスマッチだよね？」「依頼内容がおかしいって言ってんの」
#   「今後も汎用的に中身を問えるような仕組みができないと意味がないんだが」「じゃあ中身に対する問いは自動生成できるということでいいよ」
#   「この問いはどの工事に対しても共通で問えると思うので、毎回固定で入れるようにすれば？」「他にも固定で入れられる問いがあれば、いれておけば？」
#   → CC が出した固定の問いの表（13行）に「OK」、実装の指示のファイルごとの問いに「よい」。
#   直す前は、問いの大半を設計書の形（割り当ての表の行・要件の番号と見出しの対応）から作り、工事の中身を問う問いが29問中8問だった（依頼書 CP83）。
#   ★同じ文の問いを並べない（question_dup_errors）。施策・制約・数字・ファイルは、1つの問いの中に表で並べる。

def _md_sec(md: str, head: str) -> list:
    """設計書の本文から、見出し「### <head> 」の節の行を出す（次の「### 」か「## 」の前まで）。"""
    out, on = [], False
    for ln in md.splitlines():
        if ln.startswith(f"### {head} ") or ln.strip() == f"### {head}":
            on = True
            continue
        if on and (ln.startswith("### ") or ln.startswith("## ")):
            break
        if on:
            out.append(ln)
    return out


def _md_tables(lines: list) -> list:
    """行の並びから、表を [(見出しの升の並び, [行の升の並び…])] で出す（区切りの行は見ない）。"""
    tabs, cur = [], None
    for ln in lines:
        t = ln.strip()
        if t.startswith("|"):
            cells = [c.strip() for c in t.strip("|").split("|")]
            if cur is None:
                cur = (cells, [])
                tabs.append(cur)
            elif not re.fullmatch(r"[\s\-:|]*", t):
                cur[1].append(cells)
        else:
            cur = None
    return tabs


def _cell(s) -> str:
    return _one_line(s).replace("|", "／")


HAND_TARGET_RE = re.compile(r"^対象の問い[：:]\s*([23])\s*$")


def _hand_points(hand_qs: list, target: str) -> list:
    """手書きの問い（Q8〜）のうち、「対象の問い：<target>」の行を持つ物を、「特に見てほしい点」の行にする（行が無い物は 2 に入れる）。"""
    out = []
    for hq in hand_qs:
        lines = str(hq.get("body") or "").splitlines()
        tg = next((m.group(1) for m in (HAND_TARGET_RE.match(x.strip()) for x in lines) if m), "2")
        if tg != target:
            continue
        body = [x for x in lines if not HAND_TARGET_RE.match(x.strip())]
        why = str(hq.get("理由") or "").rstrip("。")
        out += ["", f"- **{hq.get('番号', '')}　{hq.get('名前', '')}**（優先度 {hq.get('優先度', '')}）",
                f"  この点が要る理由：{why}。"] + ["  " + x if x.strip() else x for x in body]
    return (["", "**特に見てほしい点**（CC が設計書とコードを読んで見つけた点です。1点ずつ答えてください）"] + out) if out else []


def _design_five_questions(d: dict, md: str, src_label: str, okd: str, engine: bool, assign: list, hand_qs: list) -> list:
    """新しい形の設計書の監査の問い（Q1〜Q5・まこさん 2026-10-21「よい」）。
    まこさん（逐語）「簡単に言うと、工事内容に対して設計書に不備が無く適切かを問いたいわけだが、こんなに質問項目が必要なの？」
    → 同じ日に作った13問＋3問の形（F1〜F13・C1〜C3）を、同じことを問う物ごとに5問へまとめた。表の中身だけが工事ごとに変わる。
    戻り＝[(番号, 優先度, この問いが要る理由, 名前, 本文)]。★文は公用文作成の考え方の書き方（chat_writing_rules.md の A2）。"""
    import gen_acceptance as ga
    import gen_core_requirements as gcr
    out = []

    def q(num, why, name, body, fix):
        out.append((num, "A", why, name, "\n".join(list(body) + ([""] + _fix_lines(fix, src_label, okd) if fix else [])).strip()))
    todo = d.get("やることの一覧") or []
    tab_todo = ["| 番号 | 施策（一文） | 出どころ |", "|---|---|---|"] + [
        f"| {_cell(r.get('番号'))} | {_cell(r.get('一文'))} | {_cell(r.get('出どころ'))} |" for r in todo]
    # ── 1. 目的と施策 ──
    q("Q1", "目的や施策が誤っていると、設計書がどれだけ正しくても、目標につながらない工事が実装に進む",
      "目的と施策は正しいか",
      ["CC は、この工事の目的を、設計書の「§1 概要」に書きました。結ぶ要件は、設計書の「結ぶ要件」に書いてあります。"
       "施策は、次の表のとおりです。CC は、この表を、設計書の元の「## 一覧」に書きました。", "", *tab_todo, "",
       "次の4つを確かめてください。",
       "1つ目に、目的が、要件定義と目標から見て正しいかを確かめてください。目標は、全月 net ≥ $1,900 です。結ぶ要件が目的に合っているかも確かめてください。",
       "2つ目に、施策ごとに、次の3つを1行で答えてください。出どころの文がその施策を支えているか。その施策が目的を果たす正しい手段か。もっと良い手段は無いか。",
       "3つ目に、目的を果たすのに要るのに表に無い直しと、目的に要らないのに表に入っている直しを挙げてください。"
       "「やらないこと」に回した直しの中に、この工事でやるべき物が無いかも見てください。",
       "4つ目に、設計書の「3-0 目標」の②③④⑥を読み、この工事が目標に近づく工事になっているかを確かめてください。"],
      ["概要", "plan", "一覧", "goal"])
    # ── 2. 設計の主張と出どころ ──
    body2 = ["CC は、設計書に、法則・教科書・要件定義・数字の出どころを書きました。次の表は、その主張と出どころです。"]
    t46 = _md_tables(_md_sec(md, "4-6"))
    if t46:
        laws = {r[0]: r for r in (t46[1][1] if len(t46) > 1 else []) if r}
        body2 += ["", "**法則と制約**（設計書の 4-6）", "", "| 決まり | 原文 | 設計書の主張（この設計でどう守るか） |", "|---|---|---|"]
        for r in t46[0][1]:
            if len(r) >= 4:
                lw = laws.get(r[1])
                src_txt = f"{lw[2]}（{lw[3]}）" if lw and len(lw) >= 4 else r[2]
                body2.append(f"| {_cell(r[1] if r[1] != '—' else r[0])} | {_cell(src_txt)} | {_cell(r[3])} |")
    t21 = _md_tables(_md_sec(md, "4-21"))
    rows21 = [r for r in (t21[0][1] if t21 else []) if len(r) >= 3
              and not re.search(r"数の値ではない|説明の文|既知答えの合成の足の値", r[2])]
    if rows21:
        body2 += ["", "**新しく入る数字**（設計書の 4-21 のうち、値として使う数字。説明の文の数字と、既知答えの足の値は外した）", "",
                  "| 番号 | 数字か式 | 出どころ |", "|---|---|---|"] + [f"| {_cell(r[0])} | {_cell(r[1])} | {_cell(r[2])} |" for r in rows21]
    t47 = _md_sec(md, "4-7")
    tabs47 = _md_tables(t47)
    no_ind = any("指標の名前" in ln and "見つかりません" in ln for ln in t47)
    if tabs47:
        body2 += ["", "**指標・閾値・パラメータ・時間足の扱い**（設計書の 4-7）", "",
                  "| 何 | この工事が関わるか | どう扱うか | 探し方のどの段階か |", "|---|---|---|---|"] + [
            f"| {' | '.join(_cell(c) for c in r[:4])} |" for r in tabs47[0][1] if len(r) >= 4]
    rq = ["", "**要件定義と、設計書で当たる見出し**（設計書を作るプログラムの対応の表から写した）", "",
          "| 要件定義の番号 | 要件 | 設計書で当たる見出しと、その状態 |", "|---|---|---|"]
    for no, raw in gcr.requirement_items(full=True):
        name = re.sub(r"（[^（）]*）\s*$", "", raw).strip()
        secs = ga.INDEX_MAP.get(no) or []
        st = "・".join(f"{_head_name(md, s)}（{ga.sec_state(d, s)[0]}）" for s in secs) or "（対応の表に無い）"
        rq.append(f"| {no} | {_cell(name)} | {_cell(st)} |")
    body2 += rq + ["", "次の3つを確かめてください。",
                   "1つ目に、法則と制約と数字の表の行ごとに、設計書の主張が出どころの文に合っているかを、1行で答えてください。"
                   "合っていない行は、出どころのどの言葉と、設計のどこが食い違うかを書いてください。",
                   "2つ目に、指標・閾値・パラメータ・時間足の扱いが、要件定義の3番（範囲から探す）と4番（最初は代表の固定値・最後は範囲）に合っているかを、行ごとに答えてください。",
                   *(["★設計書の 4-7 では、プログラムが資料の表から行を写せませんでした（「指標の名前が見つかりません」と出ています）。"
                      "この工事で足す指標に、資料の表の役割と代表の値と範囲が在るかも確かめてください。"] if no_ind else []),
                   "3つ目に、要件定義の1〜10番に反する所が無いかを、要件ごとに1行で答えてください。対応の表そのものの誤り（当たる見出しが違う要件）も挙げてください。"]
    body2 += _hand_points(hand_qs, "2")
    q("Q2", "設計の主張が出どころと違うと、法則や教科書に則らない条件や、出どころの無い数字が、材料と売買のロジックに入る",
      "設計の主張は、出どころに合っているか", body2, ["4-6", "4-7", "4-21", "any"])
    # ── 3. コードと施策 ──
    impl = d.get("実装の指示") or []
    by: dict = {}
    for it in impl:
        by.setdefault(_sdk(it.get("対象のファイル")), []).append(str(it.get("番号", "")))
    body3 = ["CC は、設計書の「4-20 実装の指示」に、直すコードの全文を書きました。次の表は、直すファイルごとの、実装の指示の番号です。", "",
             "| 直すファイル | 実装の指示の番号 |", "|---|---|"] + [f"| `{f}` | {'・'.join(ns)} |" for f, ns in by.items()] + (
             [] if by else ["| — | （実装の指示がありません） |"])
    body3 += ["", "次のことを確かめてください。",
              "1つ目に、ファイルごとに、その直しが Q1 の表のどの施策のための直しかと、直しのコードがその施策と法則と教科書のとおりかを、1行で答えてください。"
              "誤りがあれば、実装の指示の番号と、コードの行を書いてください。",
              "2つ目に、直すファイルを使っている所を実物で探し、設計書の「4-13 影響範囲」に書かれていない壊れる物が無いかを確かめてください。"]
    if engine:
        body3.append("3つ目に、実装の指示の全部について、ハード制約の H2 と H6 に反する所が無いかを確かめてください。"
                     "H2 は、その時点で手に入らない値（未来のデータ）を使わないという制約です。"
                     "H6 は、値段の高さで値が変わる形（USD の絶対値など）にしないという制約です。")
    fix3 = ["4-20", "4-13"]
    if ga.work_kind(d) == 2:
        body3 += ["", "この工事は、検査やプログラムを直す工事です。CC は、設計書の「4-22」に、次の4つを書きました。それぞれが正しいかも確かめてください。",
                  "- ①は、直す検査やプログラムが守る相手です。直すプログラムの実物を開き、守る相手と合っているかを確かめてください。",
                  "- ②は、直す前に通っていた誤りの実例です。写しの作業場でそのコマンドを走らせ、誤りが本当に通るかを確かめてください。",
                  "- ③は、直した後に止まる誤りと、まだ通る誤りです。まだ通る誤りのうち、書かれていない物が無いかも見てください。",
                  "- ④は、この直しで弱くなる守りです。抜けが無いかを確かめてください。"]
        fix3.append("4-22")
    body3 += _hand_points(hand_qs, "3")
    q("Q3", "コードが施策や法則と違うと、設計書どおりに当てても、目的を果たさない実装になる",
      "コードは施策のとおりか", body3, fix3)
    # ── 4. 完成の条件と確かめていないこと ──
    q("Q4", "確かめ方が施策を測っていないと、済んだと言っても、施策が効いたかは分からない",
      "完成の条件で、施策が効いたと言えるか",
      ["CC は、設計書の「7-6 完成の条件」に完成の条件を書き、「3-0 目標」の⑤に、済んだ直後に何で確かめるかを書きました。"
       "「6-5 確かめていないこと」には、まだ確かめていないことを書きました。",
       "次の2つを確かめてください。",
       "1つ目に、完成の条件と⑤の確かめ方で、Q1 の表の施策のそれぞれが効いたと言えるかを、施策ごとに1行で答えてください。確かめ方の無い施策があれば、挙げてください。",
       # ★2026-10-21（199回目・まこさん「OK」）＝答える場所を結果の6節の1か所にする（自己申告の節の頭の文と同じ問いを2か所に置かない）
       "2つ目に、6-5 の1件ずつについて、確かめないまま実装に進んでよいかを、結果の6節（自己申告への答え）で答えてください。"],
      ["7-6", "goal", "確かめていないこと"])
    # ── 5. 書き方と捨てた案 ──
    hand_rows = [r for r in assign if r["手書き／自動"].strip() == "手書き"]
    auto_rows = [r for r in assign if r["手書き／自動"].strip() != "手書き"]
    q("Q5", "根拠の無い文や、決めた作り方と違う文や、理由なく捨てた案が在ると、監査も まこさんも、設計書が正しいかを確かめられない",
      "設計書の書き方は正しいか",
      ["次の4つを確かめてください。",
       "1つ目に、CC が「合っています」「当たりません」「変わりません」のように、結論だけを書いた文が無いかを見てください。"
       "そういう文には、根拠（ファイルの名前と行番号）か、確かめ直すコマンドが付いていなければなりません。",
       f"2つ目に、設計書の項目が、決めた作り方のとおりに作られているかを見てください。CC が手で書く項目は {len(hand_rows)} 件、"
       f"プログラムが写して作る項目は {len(auto_rows)} 件です。項目の一覧は、事実データの「手書きと自動の割り当ての表」に在ります。"
       f"確かめるには、作業場の写しで `python3 .claude/tools/gen_acceptance.py --work {d.get('iter', '')} --dry-run` を走らせ、出た文と設計書を比べます。",
       "3つ目に、CC が設計書の中身を全部書く前に、まこさんに向きを見ていただいたかを見てください。"
       "まこさんの OK の発言は、工事のフォルダ（設計書の元と同じフォルダ）に、ok_ で始まる名前の逐語のファイルとして置かれます。"
       "逐語のファイルが無いときは、修正の指示は書きません。足りないのは まこさんの発言で、監査人には書けないためです。",
       "4つ目に、設計書の「5 決めたことと理由」を読み、CC が、採った案より良い案を、理由なく捨てていないかを確かめてください。"],
      ["5", "any"])
    return out


def build_design_src(kind: str, cp: int, work: str, design_path: str = None, show_path: str = None) -> tuple:
    """設計書と元データから、依頼書の元データ（本文）を作る。戻り＝(本文, 依頼書の名前の頭)。

    ★2026-09-29（まこさん指摘「監査の依頼内容が変じゃないか？」・worklog 20260929 §40〜§42）で直したこと
      ①工事の相手を見ずに engine_tuner の文（前提の5・大目的・監査に出す前のチェック）を出さない
      ②設計書で非該当の節を監査の相手に入れない ③設計のもとの問いは S の番号にし、優先度を行の中身で決める
      ④逐語のファイルの話し手を分けて書く ⑤先に直した道具の変更に問い（G）を作る
      ⑥壊すプログラムの無い完成の条件は、無いことを前提に問う ⑦やらないことの問いに「見てほしいこと」を付ける
      ⑧外部検索は元データの「外部検索」（何を調べるかは手で決める）から作り、無ければ止める
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_acceptance as ga                      # ★設計のもとの読み方は1か所（抜けが在れば SystemExit）
    # ★2026-09-29（135回目）＝設計書の道具と同じ読み方で工事のフォルダから読む。
    # ★2026-09-30（設計書 point1-one-way-20260930-2）＝工事のフォルダの1本だけ（元データの JSON の分かれ道を消した）。
    if not work:
        raise SystemExit("工事名がありません（request-design は --work <工事名> だけを受ける）")
    ga.WORK = work
    d = ga.src_from_work(work)
    wdir = ga.gv.work_dir(work)
    src_file = str(wdir / ga.TODO_MD)
    # ★2026-10-02（144回目）＝監査は逐語を読まないので、修正の指示を書く先は やることの表.md だけを指す
    src_label = f"`{os.path.relpath(src_file, ROOT)}`"
    md = open(design_path or DESIGN, encoding="utf-8").read()
    engine = ga.touches_trading(d)
    label, suffix = KINDS[kind]
    iter_ = d.get("iter", "")
    if f'iter="{iter_}"' not in md:
        raise SystemExit(f"設計書の目印（ARC iter）が元データの iter（{iter_}）と違う＝元データから作り直した設計書ではない")
    title = d.get("設計書の題", "")
    today = time.strftime("%Y-%m-%d")
    task = iter_.replace("-", "_") + suffix
    base = f"{today}_{task}_cp{cp}"
    rows = ga.source_rows(d)
    bad = ga.match_problems(d, rows)
    if bad:
        raise SystemExit("設計のもとの対応が足りない（設計書を作る道具と同じ判定）:\n  " + "\n  ".join(bad))
    impl = d.get("実装の指示") or []
    conds = d.get("完成の条件") or []
    nots = d.get("やらないこと") or []
    src = d.get("設計のもと") or {}
    names = [str(n) for n in (src.get("逐語のファイル") or [])]
    # ★2026-10-21（199回目）＝設計書の 2-0 と同じく、読むもの宣言の やることの番号を先に使う。直す前は やることの表の本文に
    #   出てくる番号を全部 拾い、設計書に無い M2-F-10b・M2-F-10f が「監査対象タスク」に入った（依頼書 CP83）。
    todos = ([str(n) for n in (src.get("やることの番号") or [])]
             or re.findall(r"M\d-[A-Z]+-\d+[a-z]?", str(d.get("やることの番号の文") or ""))
             or todo_numbers_from_table(wdir))
    # ★2026-10-18（ToDo の15番）＝まこさんが OK した案の写し（設計の中身の誤りを直す修正の書き先。自動では直らない）
    okd_paths = [os.path.relpath(str(wdir / (n.split("/")[-1] + ".txt")), ROOT) for n in names if n.split("/")[-1].startswith("okd_")]
    okd = "・".join(f"`{p}`" for p in okd_paths) or "工事のフォルダの okd_ で始まるファイル"
    # ★同＝新しい形の設計書の監査は、要件ごとの問い（R）・どの工事にも出す問い（F）・検査やプログラムを直す工事の問い（K）を出す
    new_form = kind == "design" and d.get("形") == "新"
    new_qs: list = []                                  # ★2026-10-21＝新しい形の問いは、割り当ての表を読んだ後に作る（下の「if only_table:」）
    B = []
    add = B.append
    add("<!-- 項目: メタ -->")
    add(f"日付: {today}")
    add(f"task: {task}")
    add(f"cp: cp{cp}")
    add(f"題: CP{cp} — {_one_line(title)}（{label}）")
    add("依頼者: CC（起案者）")
    add(f"監査の種類: {label}")
    add(f"監査対象タスク: {'・'.join(todos) or '（やることの番号なし）'}／設計書 {iter_}")
    # ★2026-10-07（まこさん「A」）＝--design で控えの設計書を渡したときは、その設計書が監査の相手
    #   （show_path＝コマンドの --design だけが渡す。自己テストの design_path は「いまの設計書の代わり」なので、相手の名前は変えない）
    target_rel = os.path.relpath(os.path.abspath(show_path), ROOT) if show_path else ".claude/state/acceptance.md"
    add(f"監査の相手: {target_rel}")
    add(f"売買に触るか: {'はい' if engine else 'いいえ'}")
    # ★2026-10-18（192回目）＝直す相手（修正を書く先）をメタに出す。設計書の監査＝設計書の元。実装の監査＝実装のファイル
    fix_targets = ("・".join(f"`{_sdk(f)}`" for f in (d.get("TARGET") or [])) if kind == "impl" else "") or src_label
    add(f"直す相手: {fix_targets}")
    add("")
    speakers = {n: _speaker(ga.gv, n) for n in names}
    ev = _impl_evidence(iter_) if kind == "impl" else {}
    if ev:
        _stack_note(ev, iter_, d.get("TARGET") or [])
    # ★2026-10-02（144回目）＝判断が要る4つは、CC が手で書き まこさんが OK したファイルから読む（無ければ止まる）
    hand = read_hand(wdir, label, kind, names, ga.gv)
    need = need_reads(d, ev, kind, todos)
    hand_names = {os.path.basename(p) for p, _r, _w in hand["必読"]}
    skip_why = {os.path.basename(r["ファイル"].strip("`")): r["理由"] for r in hand["入れない"]}
    lack = [f"{p}（{w}）" for p, w, can in need
            if os.path.basename(p) not in hand_names and not (can and skip_why.get(os.path.basename(p)))]
    if lack:
        raise SystemExit(f"{hand['path'].name} の必読に、要るファイルが無い（fail-closed）。必読に足すか、"
                         "実装が名前を出すだけのファイルなら「必読に入れないもの」に理由を書く:\n  " + "\n  ".join(lack))
    # ★2026-10-18（192回目・まこさん「４つともOK」）＝外の基準で確かめること（外部検索）は、実装の監査にも出す（2026-10-01 の「該当なし」は置き替わった）。
    #   中身は、設計書の案が挙げた外の出どころ（教科書・公式の文書）。実装の監査では「実装がその出どころと合うか」を照らす。
    #   設計書の監査で案に【外部検索】が無ければ止まる（何を調べるかは手で決める・worklog 20260929 §42）。実装の監査で無ければ、理由を書く。
    searches = d.get("外部検索") or []
    if not searches and kind != "impl":
        raise SystemExit("元データに「外部検索」（何を調べるか）が無い＝何を調べるかは手で決める（worklog 20260929 §42）。"
                         "形＝[{\"名前\": \"…\", \"中身\": \"…\"}]")
    add("<!-- 項目: 作業場の指示 -->")
    add(f"写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp{cp}_work/` に作る。必要なファイルは自分で開き、写しで走らせて確かめる。")
    add("")
    # ★2026-09-29（135回目・まこさん「CCはこの監査依頼書を見て正確に監査できるのか？」「構造がぐちゃぐちゃで汚いまま」）
    #   ＝工事のフォルダから作った設計書の監査は、割り当ての表の確かめだけにする（問い S・G・C・I・N・D は出さない）
    # ★2026-09-30（設計書 point1-one-way-20260930-2）＝工事のフォルダの1本だけ＝設計書の監査はいつも割り当ての表の確かめ
    only_table = kind == "design"
    ni, nc = len(impl), len(conds)
    # ★2026-09-29（135回目・まこさん指示「設計書の項目ごとに手書きと自動生成に仕分けた表があったよね？ その通りになってるかを見てもらえよ」）
    #   ＝工事のフォルダから作った設計書は、やることの表の「手書きと自動の割り当て」の表の1行ごとに問い（W）を作る
    tl = (ga.gv.work_dir(work) / ga.TODO_MD).read_text(encoding="utf-8").splitlines()
    sec = ga._sections(tl, re.compile(r"^##\s+(?!#)(.+)$"))
    body = next((v for k, v in sec.items() if k.startswith("手書きと自動の割り当て")), None)
    if body is None:
        raise SystemExit(f"{ga.TODO_MD} に「## 手書きと自動の割り当て」の節が無い（fail-closed）")
    _bad: list = []
    assign = ga._md_table(body, ("項目", "手書き／自動"), "手書きと自動の割り当て", _bad)
    if _bad or not assign:
        raise SystemExit("手書きと自動の割り当ての表を読めない（fail-closed）: " + "／".join(_bad))
    # ★2026-10-18（192回目）＝「結論を決める問い」「結論の決め方」「この監査の前提」の段は無くした。結論は、重さ（Critical の有無）で決まる。
    #   前提に在った物のうち、修正の書き先は「修正をどこに書くか」へ。乱数禁止・CC 判定せず・1工事1回・net は M2-L は、テンプレの「守ること」へ。
    want = want_list(hand["要望"]) if kind == "impl" else ""
    add("<!-- 項目: 修正をどこに書くか -->")
    # ★2026-10-18（ToDo の15番・まこさん「監査結果からは自動で設計書と実装データを直せるようにしているので、この監査依頼書の問いも
    #   上記に対応できるよう考慮すること」）＝修正の書き先を、直る道ごとに書く。直す前は「設計書の元に書く」の1つだけで、
    #   案から写した見出しの誤りの書き先が無かった（修正を当てるプログラムは、案の写し＝逐語のファイルに当てない）。
    if kind == "design":
        # ★2026-10-21（199回目）＝文を、公用文作成の考え方の書き方に直した
        add("設計書は、プログラムが作ります。そのため、修正の指示を設計書に直接書けません。")
        add("**修正の指示の書き先は、設計書の見出しの種類で決まります**。見出しの種類ごとに、次のファイルに修正の指示を書いてください。")
        add("")
        add(f"- 手書きの見出しの誤りは、設計書の元（{src_label}）に書きます。手書きの見出しは、事実データの割り当ての表で「手書き」の項目です。{FIX_AUTO[0]}")
        # ★2026-10-18（192回目・まこさん「行番号だけにすればいいのでは」）＝「直す箇所」は行番号だけ（見出しの番号を書かせる文は消した）
        add(f"- まこさんが OK した案から写した見出しの誤りは、まこさんが OK した案の写し（{okd}）に書きます。"
            f"案から写した見出しは、割り当ての表で「自動」の項目のうち、案から写した物です。{FIX_OK[0]}{FIX_OK[1]}")
        add("- 置き場から写した行の誤りは、その置き場のファイルに書きます。置き場から写した行は、設計書で［自動］の印が付き、"
            "法則のファイル・型の表・指標のオンとオフの表・資料の表のどれかから写した行です。")
    else:
        add("実装が設計書と違う所の修正は、その実装のファイルに書いてください。修正を当てるプログラムが、その修正を当てます。")
        add("ただし、修正を当てるプログラムは、.claude/hooks と .claude/tools と .claude/breaks のファイルには当てません。"
            "そのファイルの修正は、CC が書きます。")
        add(f"設計書の誤りの修正は、設計書の元（{src_label}）に書いてください。設計書はプログラムが作るので、設計書に直接書けません。")
    add("")
    add("<!-- 項目: 目的と経緯 -->")
    # ★2026-10-02（144回目・まこさん「## 監査依頼の経緯 の文章も意味不明だよね。これで監査は理解できるの？」）
    #   ＝直す前は、どの道具が何を作ったか・逐語のファイルの名前の列・「CC は書いていない」だけで、この工事が何のためかが1行も無かった（cp58）。
    #   いま＝①この工事は何か（やることの表の §1 概要＝まこさんが OK した手書きの文）と、目標からのつながり（道具が文書の見出しから写す）。
    # ★2026-10-02（144回目・まこさん「経緯の定義がよくわからないんだが。１は必要な情報だと思うが他はよくわからない」）
    #   ＝何があったか（日付・決定）と、承認・実装・比べる commit の行を外した。承認と commit は Q1〜Q4 の本文に同じ事実が在る。
    # ★2026-10-02（144回目・まこさん「前回の経緯にあった１の内容はかなり重要な要件なんだが」「本質を理解できてないのか？」）
    #   ＝1は「この工事は何のためか」（CC が手で書き、出どころの逐語の行つきで まこさんが OK）。直す前は、この工事の目的
    #     （例＝札が正しいかは M2-L の net まで分からない→外れたら直して並べ直す→だから直しやすい構造にする）が依頼書のどこにも無く、
    #     監査は手段（定義・設定・版）が設計書どおりかだけを照らす形になっていた。
    # ★2026-10-21（199回目）＝見出しの語と中身を「＝」でつながず、「：」の後に文を書く（公用文作成の考え方の書き方）
    add(f"1. **この工事は何のためか**：{_one_line(hand['目的'][0])}")
    for x in hand["目的"][1:]:
        add(f"   {_one_line(x)}")
    # ★2026-10-06（157回目・まこさん「Aでよい」）＝2は設計書の §1 概要をそのまま写すので、§1 に逐語のファイルの名前
    #   （例＝「決めていただいたときの案（okd_p1a_20261006）」）が在ると、下の照らし（request_content_errors）が止める。
    #   設計書は承認済みで直せないので、写すときに名前を「逐語のファイル」に置き換える（照らしと同じ VERBATIM_NAME_RE）。
    # ★2026-10-21（199回目・まこさん「この段階で怪しいなら修正してよ」）＝新しい形の設計書では、§1 概要を写さない。
    #   §1 は1の目的と Q1 の施策の表と同じ中身で、写すと「＝」で詰めた長い文が依頼書に入る（CP83 の 128行）。設計書の場所だけ書く
    if new_form:
        add(f"2. **この工事は何か**：この工事の中身は、設計書の「§1 概要」に書いてあります。施策の一覧は、Q1 の表に載せました。"
            f"やることの番号は、{'・'.join(todos) or '無し'}です。")
    else:
        add(f"2. **この工事は何か**：{VERBATIM_NAME_RE.sub('逐語のファイル', _one_line(d.get('何を作るか')))}"
            f"（やることの番号は、{'・'.join(todos) or '無し'}です）")
    add(f"   **この工事の位置**：目標からこの工事までのつながりは、次のとおりです。{_position_chain(todos)}")
    # ★2026-10-18（192回目）＝3 結ぶ要件・4 経緯（手書き）・5 なぜこの監査が要るか（手書き・要るときだけ）。固定の問い R0 が 3 を読む
    # ★2026-10-18（192回目）＝欄が無いときは、監査に読み取り方を書く（R0 が「3 に書いてある」と指すため）
    add(f"3. **この工事が結ぶ要件**：{_one_line(d.get('結ぶ要件')) or 'この設計書の形には、結ぶ要件の欄がありません。設計書の §1 概要と、やることの表から、結ぶ要件を読み取ってください。'}")
    add("4. **経緯**：この監査に至るまでの経緯は、次のとおりです。")   # read_hand が無ければ止める（必須・まこさん決定 2026-10-18）
    for x in hand["経緯"]:
        add(f"   {_one_line(x)}")
    # ★2026-10-18（192回目）＝5（要るときだけ）・工事の種類・目標の番号は、飛ばさずに続ける（直す前は 1・2・3・4・6・7 と飛んだ）
    n_item = 5
    if hand["なぜ要る"]:
        add(f"{n_item}. **なぜこの監査が要るか**：{_one_line(hand['なぜ要る'][0])}")
        for x in hand["なぜ要る"][1:]:
            add(f"   {_one_line(x)}")
        n_item += 1
    # ★2026-10-18（ToDo の15番・14番の設計書 design-doc-gen-form-20261013.md の 347行「監査依頼書を作るプログラムは、設計書の新しい節
    #   （目標・確かめていないこと）を、依頼書の問いと自己申告へ写しません。次の工事で直します」）＝新しい形の設計書の、工事の種類と目標を写す
    if new_form:
        _kd = ga.work_kind(d)
        add(f"{n_item}. **工事の種類**：この工事は、{ga.KIND_TEXT.get(_kd, _kd)}です。プログラムが、直すファイルの一覧から決めました。")
        # ★2026-10-21（199回目）＝目標は写さない。Q1 の4つ目と Q4 が、設計書の 3-0 を読んで確かめるよう頼む（写すと同じ文が2か所に入る）
        add(f"{n_item + 1}. **目標**：CC は、目標を、設計書の「3-0 目標」に①〜⑥の6行で書きました。"
            "監査人は、Q1 の4つ目と Q4 で、この目標を確かめます。")
    add("")
    add("<!-- 項目: 着手前必読 -->")
    add("**パスは、リポジトリの根（`cat-bitget/`）からの相対です。**`SDK` は、`v3-bitget-api-sdk/bitget-python-sdk-api` の略です。")
    add("")
    # ★2026-10-02（144回目・まこさん「本来監査に必要な文書を書けよ」「私の提案の通りに修正する」）
    #   ＝必読は手書き（ファイル・範囲・なぜ要るか）。道具が足すのは、照合に要る事実の3つ（設計書・承認の控え・当てた記録）だけ。
    #   直す前は道具が全部を作り、逐語のファイル7本と要件のまとめが並び、照らす相手のコードと決まりが無かった（cp58）。
    reads = [(target_rel, "", "監査の相手の設計書です。プログラムが作りました")]
    if kind == "impl":
        # ★2026-09-30（3点目-a）＝実装の監査の照合に要るもの（承認した版の控え・当てた記録）
        # ★どの版で当てたかは道具には分からない（2回目の承認の版は実装の後に作る）＝Q4 で照らしてもらう
        reads += [(a, "", "まこさんが承認した版の設計書の控えです。どの版の 4-20 で当てたかは、Q4 で照らします") for a in (ev.get("archives") or [])]
        reads.append(("SDK/.claude/audits/applied_fixes.json", "", f"当てる道具が書いた、当てた記録です。この工事の行の名前は design:{iter_} です"))
    # 前提の3（修正の指示は設計書の元に書く）の書く先＝いつも要る
    reads.append((os.path.relpath(src_file, ROOT), "", "設計書の元（やることの表）です。監査人は、修正の指示をこのファイルに書きます"))
    if kind == "design":
        # ★2026-10-18（ToDo の15番）＝案から写した見出しの誤りの書き先（前提の3）を、監査が開けるようにする
        reads += [(p, "", "まこさんが OK した案の写しです。案から写した見出しに誤りがあれば、監査人は、修正の指示をこのファイルに書きます。プログラムは、この修正を自動では入れません")
                  for p in okd_paths]
    reads += hand["必読"]
    # ★2026-10-18（ToDo の15番・記録 20261013 の 158・368・490行「必読に、設計書と やることの表が2回ずつ出ている」）
    #   ＝同じファイルは1行にまとめる（範囲と「なぜ」を足し合わせる）。直す前は重なりを消す鍵が（パス, 範囲）の組で、
    #   道具が足した行（範囲なし）と、手書きの行（範囲つき）が別の行になった。
    merged: dict = {}
    for p, rng_txt, why in reads:
        key = os.path.realpath(repo_path(p))
        _p0, rngs, whys = merged.setdefault(key, (p, [], []))
        r = rng_txt.strip().strip("（）()").strip()
        if r and r not in rngs:
            rngs.append(r)
        w = _one_line(why)
        if w and w not in whys:
            whys.append(w)
    for i, (p, rngs, whys) in enumerate(merged.values(), 1):
        # ★2026-09-30（3点目-a）＝テンプレの形（番号つきの「パス — 1行要約」）。直す前は表だった（worklog 20260929 §67 の②）
        # ★2026-10-21（199回目）＝「なぜ要るか」は文なので、「／」でつながず、句点で区切る
        _why_txt = "".join(w if w.endswith("。") else w + "。" for w in whys)
        add(f"{i}. `{p}`{'（' + '・'.join(rngs) + '）' if rngs else ''} — {_why_txt}")
    add("")
    # ★2026-10-18（192回目）＝「大目的の注記」は無くし、「範囲の中」（相手と直す相手）に替えた。問いの置き場は「確かめてほしいこと」の1か所
    add("<!-- 項目: 範囲の中 -->")
    add(f"- 監査の相手は、`{target_rel}` です（設計書 `{iter_}`・{label}）。"
        + ("設計書が割り当ての表のとおりに作られているかと、設計の中身が正しいかを確かめます。" if only_table
           else "当てる道具が、設計書の実装の指示のとおりに実装を作れているかを確かめます。"))
    add(f"- 直す相手は、{fix_targets} です。")
    if engine:
        add("- この工事は、売買のロジックに触る工事です。engine_tuner の目的は、まこさんの言葉で"
            "「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的」です"
            "（まこさん確定 2026-08-06）。")
    else:
        add("- この工事は、売買のロジックに触らない工事です。直す相手（TARGET）には、scripts/priority_rebuild のファイルも、engine_tuner もありません。")
    add("")
    if only_table:
        add(f"<!-- 項目: 事実データ 名前=手書きと自動の割り当ての表（{ga.TODO_MD}・まこさんが OK した表） -->")
        add("| 項目 | 手書き／自動 |")
        add("|---|---|")
        for r in assign:
            add(f"| {_one_line(r['項目'])} | {_one_line(r['手書き／自動'])} |")
    else:
        # ★2026-09-30（3点目-a・まこさん OK）＝実装の監査の事実データ＝実装の指示の一覧と、当てた記録（どちらも実物から）
        add("<!-- 項目: 事実データ 名前=設計書の実装の指示の一覧（4-20・当てる道具が当てる相手） -->")
        add("| 番号 | 対象のファイル | 直す箇所 | 種類 |")
        add("|---|---|---|---|")
        for it in impl:
            add(f"| {_one_line(it.get('番号'))} | `{_sdk(it.get('対象のファイル'))}` | "
                f"{_one_line(it.get('直す箇所', 'なし'))} | {_one_line(it.get('種類', '直した後の文字'))} |")
        if not impl:
            add("| — | （設計書に実装の指示が無い） | — | — |")
        add("")
        add(f"<!-- 項目: 事実データ 名前=当てた記録（applied_fixes.json の名前 design:{_attr(iter_)}） -->")
        add("| 番号 | 対象のファイル | 当て方 | 時刻 |")
        add("|---|---|---|---|")
        for r in ev.get("applied") or []:
            add(f"| {_one_line(r.get('num'))} | `{_sdk(r.get('file'))}` | {_one_line(r.get('how'))} | {_one_line(r.get('at'))} |")
        if not ev.get("applied"):
            add("| — | （当てた記録が無い） | — | — |")
        add("")
        # ★2026-10-18（192回目）＝「実装の前」「実装の後」の版の定義（git のコマンド込み）は、ここに1回だけ書く。
        #   直す前は Q1 と Q2 の本文に同じ長い括弧が2回 入り、1文が200字を超えていた。
        add("<!-- 項目: 事実データ 名前=実装の前と後の版（git） -->")
        add(f"- **実装の前**：{ev.get('pre_desc', '')}")
        add(f"- **実装の後**：{ev.get('post_desc', '')}")
    add("")
    if only_table:
        add("<!-- 項目: 事実データ 名前=監査に出す前のチェック（pre_audit_check.json） -->")
        dmt = os.path.getmtime(design_path or DESIGN)
        if not engine:
            add("この工事には当たりません。pre_audit_check.json は、売買のロジックの道具の検査です。この工事は、売買のロジックに触りません。")
        elif not os.path.isfile(PRE_JSON):
            add("pre_audit_check.json がありません。")
        elif os.path.getmtime(PRE_JSON) <= dmt:
            add("pre_audit_check.json は、設計書より前に走らせた物です。そのため、この設計書の検査ではないので、道具は載せません。"
                "CC は、チェックを走らせ直してから、依頼書を作り直します。")
        else:
            pj = json.load(open(PRE_JSON, encoding="utf-8"))
            add(f"CC は、このチェックを {pj.get('at', '')} に走らせました。")
            add("設計書の監査は、実装の前に出します。そのため、設計書と実物の照合（verify_design_contract.py --diff）の終了コードは、"
                "設計書に書いた新しい関数がまだ実物に無いので、1 になります。道具は、設計書の監査の依頼書では、この1本を見ません。"
                if kind == "design" else "")
            add("")
            add("| コマンド | 種類 | 終了コード |")
            add("|---|---|---|")
            # ★2026-10-21（199回目）＝分かっている食い違い（known の印）の行は、終了コードの欄に印を出し、表の下に理由を載せる
            #   （載せないと、照合の1本のほかに rc=1 の行が在る理由が依頼書から読めない）
            known = []
            for r in pj.get("rows") or []:
                rc_cell = f"{r.get('rc')}（分かっている食い違い）" if r.get("known") else f"{r.get('rc')}"
                add(f"| `{_one_line(r.get('cmd'))}` | {_one_line(r.get('kind'))} | {rc_cell} |")
                if r.get("known"):
                    known.append(r)
            for r in known:
                add("")
                add(f"`{_one_line(r.get('cmd'))}` の終了コードは 1 です。この1本は、まこさんが決めた「分かっている食い違い」です。"
                    "チェックは、出力が決めたときと1文字も同じときだけ、この1本で止まりません。"
                    f"理由と決めた発言は、次のとおりです。{_one_line(r.get('note') or '（記録に理由がありません）')}")
        add("")
    # ★2026-10-02（144回目・まこさん「実装データや必要なjsonデータなども確認すべきでは？」）＝必読に要るファイルを道具が拾って載せる。
    #   依頼書を作った後のチェック（request_content_errors）は、この表の「入れる」の行が必読に在るかを見る。
    add(f"<!-- 項目: 事実データ 名前={_attr(NEED_NAME)} -->")
    add("| ファイル | どこから拾ったか | 必読か |")
    add("|---|---|---|")
    for p, w, _can in need:
        b = os.path.basename(p)
        add(f"| `{p}` | {w} | {'入れる' if b in hand_names else '入れない（' + _one_line(skip_why.get(b, '')).replace('|', '／') + '）'} |")
    if not need:
        add("| — | （直す相手が無い） | — |")
    add("")
    # ★2026-10-18（192回目）＝「監査対象」（問いの名前の一覧）は無くした。問いは「確かめてほしいこと」の1か所
    add("<!-- 項目: 範囲の外 -->")
    # ★2026-10-12（B-2）＝ここに在った「設計書の中身そのものが正しいか」（対象外）の行を消した。設計の中身は、設計書の監査で問う（Q7・Q8〜）。
    add("- 守りの穴探し（すり抜けの道を新しく探すこと）は、範囲の外です。穴探しは、探すたびに新しい穴が出て、終わらないためです（恒久の決まり65番）。"
        "CC は、作業が実際に止まったときに、その穴を直します。")
    # ★2026-10-21（199回目）＝「中身（理由）」と括弧でつながず、「中身は、範囲の外です。」の後に理由の文を書く
    for r in nots:
        _r = _one_line(r.get('理由'))
        add(f"- {_one_line(r.get('中身'))}は、範囲の外です。{_r if _r.endswith('。') else _r + '。'}")
    add("")
    # ★2026-10-21（199回目・まこさん「同じ問いを繰り返してるけど。いいの？」「今後二度とこのようなミスを繰り返せないような作りに」）
    #   ＝割り当ての表の行ごとに1問を作るのをやめ、「手書きの項目」1問と「自動の項目」1問にまとめる（項目は問いの中の表に並べる）。
    #   直す前は、依頼書 CP83 で W01〜W25 の25問が、項目の名前だけが違う同じ2種類の文になった。
    #   ★2026-10-21（同日・まこさん「その書き方で良い」）＝文は、まこさんが OK した W01 の例の書き方（1つの文に主語・目的語・述語を1つずつ）。
    wn = 0
    for key in (("手書き", "自動") if (only_table and not new_form) else ()):   # ★新しい形は F12 に1問でまとめる（2026-10-21）
        rows_w = [r for r in assign if (r["手書き／自動"].strip() == "手書き") == (key == "手書き")]
        if not rows_w:
            continue
        wn += 1
        n_w = len(rows_w)
        title = "CC が手で書く項目" if key == "手書き" else "プログラムが写して作る項目"
        add(f"<!-- 項目: 問い 番号=W{wn:02d} 優先度=A 理由=CC が手で書いた文が、プログラムが写すはずの項目に混ざると、自動で作る仕組みの目的が崩れる "
            f"名前=設計書の「{title}」（{n_w}件）が、決めたとおりに作られているか -->")
        add("この工事の設計書は、プログラムが作ります。")
        if key == "手書き":
            add(f"ただし、設計書のうち、次の{n_w}件の項目は、CC が手で文を書きます。")
        else:
            add(f"設計書のうち、次の{n_w}件の項目は、プログラムが写して作ります。CC は、この{n_w}件の項目の文を書きません。")
        add("")
        add("| 項目 | 決めた作り方 |")
        add("|---|---|")
        for r in rows_w:
            add(f"| {_one_line(r['項目']).replace('|', '／')} | {_one_line(r['手書き／自動']).replace('|', '／')} |")
        add("")
        if key == "手書き":
            add(f"CC は、この{n_w}件の項目の文を、{ga.TODO_MD} というファイルの「## 手書きの項目」に書きました。")
            add(f"プログラムは、{ga.TODO_MD} に書かれた文を、1文字も変えずに設計書へ写すはずです。")
            add("")
            add("次の2つを確かめてください。")
            add("")
            add(f"1つ目に、{n_w}件の項目の見出しのすぐ下に、［手書き］という印が付いているかを確かめてください。")
            add(f"2つ目に、設計書に書かれた{n_w}件の項目の文が、{ga.TODO_MD} に書かれた文と1文字も違わないかを確かめてください。")
            add("")
            add("2つ目を、次の3つの手順で確かめることができます。")
            add("まず、作業場のフォルダに、設計書と工事のフォルダの写しを作ります。")
            add("次に、その写しを使って、設計書を作るプログラムを、ファイルに書き込まない形で走らせます。"
                f"コマンドは `python3 .claude/tools/gen_acceptance.py --work {iter_} --dry-run` です。")
            add("最後に、プログラムが画面に出した文と、設計書の文を比べます。")
        else:
            add("プログラムが写す元は、次の2つのどちらかです。")
            add("")
            add("- 1つ目の元は、実物です。実物は、コードと設定と、プログラムを走らせた結果です。")
            add("- 2つ目の元は、まこさんが OK した案の文です。案の文は、工事のフォルダの okd_ で始まるファイルの中の、【番号】の見出しの下に在ります。")
            add("")
            add("次の2つを確かめてください。")
            add("")
            add(f"1つ目に、{n_w}件の項目の見出しのすぐ下に、［自動］という印が付いているかを確かめてください。")
            add("2つ目に、項目の中の1行ずつが、上の2つの元のどちらかから写した文かを確かめてください。")
        add("")
        add("違う所を見つけたら、その項目の名前と設計書の行の番号を、結果の所見に書いてください。")
        add("")
    # ★2026-10-12（170回目・まこさん「OK」＝直し方の案 B-1〜B-3）＝設計書の監査で、設計の中身を問う。
    #   直す前（2026-09-29・30）は、設計書の監査の問いが割り当ての表の確かめ（W）だけで、監査対象外に「設計書の中身そのものが
    #   正しいか」を入れていた。CC が、1回の監査（設計書を自動で作る仕組みの工事）についての まこさんの言葉を、全部の工事に広げた物。
    #   2026-10-12 まで、設計の中身を実装の前に CC 以外が確かめた工事が無かった（session_worklog_20261012.md §7〜§10）。
    #   いま＝決まった問い Q7（設計の中身が要件定義に合っていて正しいか＝問い2）と、手書きの工事ごとの問い（Q8〜）を出す。
    # ★2026-10-18（192回目）＝設計書の監査でも、新しい形でない設計書（F1・R が無い）には、要件定義を指す固定の問い R0 を出す
    if only_table and not new_form:
        add(f"<!-- 項目: 問い 番号={REQ_Q[0]} 優先度={REQ_Q[1]} 理由={_attr(REQ_Q[2])} 名前={_attr(REQ_Q[3])} -->")
        add("\n".join(REQ_Q[4]))
        add("")
    if only_table:
        if new_form:
            # ★2026-10-21（199回目・まこさん「OK」「よい」）＝新しい形の設計書は、固定の問い F1〜F13 と、設計書の主張から作る問い C1〜C3。
            #   Q7 の3つの見る所は F5〜F7 に分けたので、Q7 は出さない。検査やプログラムを直す工事（種類②）には K1〜K4 も出す。
            # ★同日（まこさん「こんなに質問項目が必要なの？」→ 5問の案に「よい」）＝5問の形。手書きの問い（Q8〜）は、
            #   Q2 か Q3 の中の「特に見てほしい点」に入る（手書きの問いの「対象の問い：2」「対象の問い：3」の行で決める）。
            #   検査やプログラムを直す工事（種類②）の4つの確かめは、Q3 の中に入る。
            new_qs = _design_five_questions(d, md, src_label, okd, engine, assign, hand["問い"])
        else:
            add(f"<!-- 項目: 問い 番号=Q7 優先度=A 理由={_attr(DESIGN_Q7[1])} 名前={_attr(DESIGN_Q7[0])} -->")
            add(DESIGN_Q7[2])
            add("")
        for num, pr, why, name, body in new_qs:
            add(f"<!-- 項目: 問い 番号={num} 優先度={pr} 理由={_attr(why)} 名前={_attr(name)} -->")
            add(body)
            add("")
        for q in (hand["問い"] if not new_form else []):      # ★新しい形は Q2・Q3 の中に入れた（上）
            add(f"<!-- 項目: 問い 番号={q['番号']} 優先度={q['優先度']} 理由={_attr(q['理由'])} 名前={_attr(q['名前'])} -->")
            add(q["body"])
            add("")
    # ★2026-09-30（3点目-a・まこさん OK）＝実装の監査の問いは、設計書と実装の照合の決まった6問（IMPL_QUESTIONS）だけ。
    #   直す前は、設計のもとの1行ずつ（S）・先に直した道具（G）・完成の条件（C）・実装の指示（I）・やらないこと（N）・
    #   CC が決めたこと（D）を1つずつ問いにし、cp53 で問いが686件（うち S が640件）になった。
    if not only_table:
        vals = {"pre": "事実データ「実装の前と後の版」の実装の前",
                "post": "事実データ「実装の前と後の版」の実装の後",
                "files": "・".join(sorted({f"`{_sdk(it.get('対象のファイル'))}`" for it in impl})) or "（無い）",
                "ni": ni, "nc": nc, "iter": iter_,
                "archives": "・".join(f"`{a}`" for a in (ev.get("archives") or [])) or "（無い）",
                "todo": os.path.relpath(src_file, ROOT),
                # ★2026-10-07（まこさん「A」）＝--design で控えを渡したときは、いまの acceptance.md は後の工事の版なので比べない
                # ★2026-10-21（201回目・まこさん「よい」）＝直す前の「この工事の後に別の工事の設計書で上書きされたので」は、
                #   上書きされる前に依頼書を作ると事実と違った（CP84）。acceptance.md の状態で文を変えると、check-request の
                #   作り直し（:2333）が後で食い違うので、いつも正しい文にした
                "now": (f"監査の相手の設計書（`{target_rel}`。★比べる相手は、承認の控えです。`.claude/state/acceptance.md` は、"
                        "後の工事の設計書で上書きされることがあるので、比べる相手にしません）" if show_path else "いまの設計書"),
                # 同じコマンドは1回だけ並べる（完成の条件の行ごとに同じコマンドが在ると、同じものが何回も並んだ）
                "cmds": "・".join(dict.fromkeys(f"`{_one_line(r.get('コマンド'))}`" for r in conds)) or "（無い）"}
        # ★2026-10-18（192回目・まこさん「OK」）＝実装の監査にも、要件定義を指す固定の問い R0 を出す（固定の文が使われるのは、問いが指すとき）
        add(f"<!-- 項目: 問い 番号={REQ_Q[0]} 優先度={REQ_Q[1]} 理由={_attr(REQ_Q[2])} 名前={_attr(REQ_Q[3])} -->")
        add("\n".join(REQ_Q[4]))
        add("")
        for num, pr, name, why, body in IMPL_QUESTIONS:
            add(f"<!-- 項目: 問い 番号={num} 優先度={pr} 理由={_attr(why)} 名前={_attr(name)} -->")
            if num == "Q4" and not ev.get("archives"):
                # ★2026-10-18（192回目）＝控えが無いときは「（（無い））」でなく、答え方を書く
                add("承認した版の設計書の控えは、まだ無い（承認の控えを commit していない）。"
                    f"この問いは、所見に「控え無し」と書いてください。比べる相手は、{vals['now']}の 4-20 です。")
            else:
                add(body.format(**vals))
            add("")
        # ★2026-10-01（工事 point5-q7-20261001）＝問い2 を照らす問い Q7（直す前は問い2 に当たる問いが無く、所見の見出しが決まらなかった）
        if want:
            add("<!-- 項目: 問い 番号=Q7 優先度=A 理由=満たしていない要望が在れば、まこさんの要望が届いていない 名前=まこさんの要望を、この工事の後の実装が満たしているか -->")
            add("下に並べた まこさんの要望を、この工事の後の実装が満たしているかを確かめてください。"
                "満たしていない要望があれば、その全部について、要望の番号と、足りない実装の行を示してください。"
                "1つでも満たしていない要望があれば、その指摘を Critical にします。")
            add("")
            add(want)
            add("")
        # ★2026-10-02（144回目）＝工事ごとの問い（手書き・まこさんが OK）。cp49 の A0〜C1 の形。問い1 が Q8〜 で照らす
        for q in hand["問い"]:
            add(f"<!-- 項目: 問い 番号={q['番号']} 優先度={q['優先度']} 理由={_attr(q['理由'])} 名前={_attr(q['名前'])} -->")
            add(q["body"])
            add("")
    # ★何を調べるかは手で決める（worklog §42）＝元データの「外部検索」から作る（直す前は題の40文字で切れた＝§40 の9）
    # ★2026-10-18（ToDo の15番・監査 CP75 の外部検索の Process「クエリ案が、検索の言葉でない」）＝クエリ案は、案の「検索の言葉」の列から写す。
    #   列が無い古い形の案は、無いと書き、調べる物の文から監査が検索の言葉を決める（直す前は、CC の文をそのままクエリ案にしていた）。
    for s in searches:
        s = s if isinstance(s, dict) else {"名前": str(s), "中身": ""}
        add(f"<!-- 項目: 外部検索 名前={_attr(_cc_voice(s.get('名前', '')))} -->")
        add(f"{SEARCH_WORDS}{_one_line(s.get('検索の言葉')) or SEARCH_NONE}")
        # ★実装の監査では、設計書が指した外の出どころと、実装が合うかを照らす
        add(f"{SEARCH_WHAT}{_cc_voice(_one_line(s.get('中身') or s.get('名前', '')))}"
            + ("。実装の監査では、この出どころと、実装の該当の所が合うかを照らします" if kind == "impl" else ""))
        add("")
    if not searches:
        add("<!-- 項目: 外の基準が無い理由 -->")
        add("設計書の案の【外部検索】の表には、外の出どころが1つもありません。この工事の設計書は、教科書・公式の文書・業界の標準を根拠にしていません。")
        add("")
    # ★自己申告＝設計書の「塞げないもの」と、見積もりの「測っていない」の行（OK をもらった提案の28行目）
    for r in d.get("塞げないもの") or []:
        q = _one_line(r.get("問い"))
        # ★2026-10-01（142回目・cp57）＝「Q5 の1＝」〜「Q5 の5＝」は、設計書を書くときに止める hook が どの設計書にも書かせる
        #   監査 cp14 の Q5 の5件（その hook そのものの限界）。実装の監査（設計書のとおりに実装したか）と関係が無いので、実装の監査では出さない。
        #   設計書の監査では出す（設計書の中身なので）。使わない語「門」はやめ、hook の名前で書く。
        # ★2026-10-01（142回目・まこさん「今回の争点に対して不要な論点は削除でOK」）＝塞げないものは設計の限界なので、
        #   実装の監査（設計書のとおりに実装したか）では1件も出さない（設計書の監査で問う）
        if kind == "impl":
            continue
        # ★2026-10-21（199回目・まこさん「監査が答えられない質問するな」「OK」）＝「Q5 の1＝」〜「Q5 の5＝」は、設計書を書くときに
        #   止める hook そのものの限界で、どの設計書にも同じ文が入る。工事の設計とは関係が無く、設計書の監査人にも答えようがないので、
        #   設計書の監査でも出さない（2026-10-01 の「設計書の監査では出す」は、この決定で置き替わる）
        if GATE_Q5_RE.match(q):
            continue
        add("")
        add("<!-- 項目: 自己申告 -->")
        # ★2026-10-01（工事 point5-q5label-20261001）＝番号を外さず、出どころを書いて写す（依頼書の Q5 とも取り違えない）
        _sn = _cc_voice(_one_line(r.get('塞げないこと')))
        add(f"**塞げないもの**：問いは、「{_cc_voice(GATE_Q5_RE.sub(GATE_Q5_TO, q))}」です。塞げないことは、次のとおりです。"
            f"{_sn if _sn.endswith('。') else _sn + '。'}")
    # ★2026-10-18（ToDo の15番・14番の設計書の 347行）＝設計書の「確かめていないこと」（6-5）を、自己申告に1件ずつ写す
    if kind == "design":
        for r in d.get("確かめていないこと") or []:
            add("")
            add("<!-- 項目: 自己申告 -->")
            _e = lambda t: t if t.endswith("。") else t + "。"   # noqa: E731  ★文の終わりに句点を付ける
            add(_cc_voice(f"**確かめていないこと**：{_e(_one_line(r.get('確かめていないこと')))}"))
            add(_cc_voice(f"   確かめていない理由は、次のとおりです。{_e(_one_line(r.get('なぜ確かめていないか')))}"))
            add(_cc_voice(f"   確かめるには、次の物を走らせます。{_e(_one_line(r.get('確かめるなら、何を走らせるか')))}"))
    for r in d.get("見積もり") or []:
        if "測っていない" in f"{r.get('見込み', '')}{r.get('根拠', '')}":
            add("")
            add("<!-- 項目: 自己申告 -->")
            add(_cc_voice(f"**測っていない見積もり**：{_one_line(r.get('何'))}。見込みは、{_one_line(r.get('見込み'))}です。"
                          f"根拠は、{_one_line(r.get('根拠'))}です。"))
    if kind == "impl":
        # ★2026-10-01（142回目・cp57）＝監査が知るべき事実のうち、道具が実物から出せるもの2つを申告する（直す前は無かった）
        #   ①承認した版が2本以上（承認の後に設計書を作り直した）＝どの版とどこが違うか
        #   ②この工事の外で、作業中の変更が在るコード（Q2 の「手で書いた疑い」と取り違えないため）
        arcs = ev.get("archives") or []
        newest = [a for a in arcs if re.fullmatch(rf"{re.escape(iter_)}\.md", os.path.basename(a))]
        for a in arcs:
            if newest and a != newest[0]:
                add("")
                add("<!-- 項目: 自己申告 -->")
                add(f"**承認の後に設計書を作り直した**：CC は、承認の後に設計書を作り直しました。前の版は `{a}` で、いまの版は `{newest[0]}` です。"
                    f"違いは、次のとおりです。{_version_diff(os.path.join(ROOT, a), os.path.join(ROOT, newest[0]))}")
        outside = _dirty_outside(d.get("TARGET") or [])
        if outside:
            add("")
            add("<!-- 項目: 自己申告 -->")
            add(f"**この工事の外の作業中の変更**：次のファイルには、作業中の変更があります。{'・'.join('`' + p + '`' for p in outside)}。"
                "この変更は、この工事の実装の指示が当てた物ではありません。そのため、Q1 と Q2 の差分を、この工事の対象のファイルだけで取ってください。")
    # ★2026-09-29＝工事のフォルダに在るのに設計書に名前が出ていない逐語のファイル（設計書を作った後に写した物）を、道具が数えて申告する
    # ★2026-10-02（144回目）＝設計書の §0-1 の話なので、設計書の監査だけに出す（実装の監査には逐語のファイルの名前を出さない）
    # ★2026-10-20（199回目・まこさん「外す」）＝設計書に 0-1（逐語のファイルの名前の一覧）を出さなくなったので、この申告は出さない
    late = []
    if late:
        add("")
        add("<!-- 項目: 自己申告 -->")
        add(f"**設計書を作った後に写した逐語**＝{'・'.join(n.split('/')[-1] for n in late)}（工事のフォルダには在るが、"
            "設計書の §0-1 に名前が無い。設計書を作り直すまで、設計書の §0-1 はこの分だけ元と違う）")
    body = "\n".join(B) + "\n"
    head = (f"{GEN_MARK} kind={kind} work={work} design_sha256={sha256_file(design_path or DESIGN)} "
            f"src_sha256={sha256_file(src_file)} "
            f"body_sha256={sha256_text(body)} -->")
    return head + "\n" + body, base


def request_design(kind: str, work: str, design_path: str = None) -> int:
    """設計書と工事のフォルダから、依頼書の元データを作業場に書き、依頼書を inputs に作る。
    ★2026-09-30（設計書 point1-one-way-20260930-2）＝工事名は必須（元データの JSON から工事名を読む古い口は消した）。
    ★2026-10-07（まこさん「A」）＝design_path＝読む設計書（承認の控え acceptance_archive/<工事名>.md）。
      無ければ いまの設計書（acceptance.md）。同じ日に続けて承認した前の工事の依頼書を、工事ごとに作るため。"""
    if design_path and not os.path.isfile(design_path):
        print(f"❌ --design の設計書が無い: {design_path}")
        return 2
    if kind not in KINDS:
        print(f"❌ 種類は design か impl（{kind}）")
        return 2
    if not work:
        print("❌ 工事名がありません（request-design <design|impl> --work <工事名>）")
        return 2
    # ★同じ工事（同じ task）の依頼書が在り、その結果ファイルがまだ無ければ、その番号を使う（作り直すたびに番号を進めない）
    iter0 = work
    task0 = iter0.replace("-", "_") + KINDS[kind][1]
    cp = 0
    for n in sorted(os.listdir(os.path.join(AUDITS, "inputs"))):
        m = re.search(rf"_{re.escape(task0)}_cp(\d+)_audit_request\.md$", n)
        if m and not os.path.exists(os.path.join(AUDITS, n.replace("_audit_request.md", "_audit_report.md"))):
            cp = int(m.group(1))
    cp = cp or next_cp()
    try:
        text, base = build_design_src(kind, cp, work=work, design_path=design_path, show_path=design_path)
    except SystemExit as e:
        print(f"❌ 依頼書の元データを作れない: {e}")
        return 1
    work = os.path.join(AUDITS, f"cp{cp}_work")
    os.makedirs(work, exist_ok=True)
    src_path = os.path.join(work, f"cp{cp}_src.gen.md")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"書いた（依頼書の元データ・道具が作った）: {rel_of(src_path)}")
    return build_request(src_path, os.path.join(AUDITS, "inputs", f"{base}_audit_request.md"))


def check_request(req_path: str) -> list:
    """出来上がった依頼書を、元データと照らす（2026-10-18・ToDo の15番）。戻り＝「✅ …」「❌ …」の行。本物には何も書かない。
    まこさん（2026-10-17・記録 20261017 §35）「チェックするとしたら、自動生成の不備で、元データと生成後のデータで齟齬があるかどうかくらい？」
    直す前は、依頼書の目印に元データと設計書のハッシュ値を書いていたが、照らす所が0件だった。
    見ること＝①依頼書と元データが、作った後に書き替えられていない ②設計書から作った依頼書なら、監査の相手の設計書と設計書の元が、
      元データを作った時と同じで、いま作り直した元データと1文字も同じ ③元データから作り直した依頼書と1文字も同じ。"""
    import contextlib
    import io
    import shutil
    import tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    lines: list = []

    def ok(cond: bool, what: str, detail: str = "") -> None:
        lines.append(("✅ " if cond else "❌ ") + what + (f"（{detail}）" if detail and not cond else ""))

    def first_diff(a: str, b: str) -> str:
        al, bl = a.splitlines(), b.splitlines()
        for i, (x, y) in enumerate(zip(al, bl), 1):
            if x != y:
                return f"{i} 行目が違う＝いま「{x[:60]}」／作り直した物「{y[:60]}」"
        return f"行の数が違う（いま {len(al)} 行／作り直した物 {len(bl)} 行）"

    text = open(req_path, encoding="utf-8").read()
    body, mark = split_mark(text)
    ok(bool(mark.get("body_sha256")) and mark.get("body_sha256") == sha256_text(body), "依頼書は、道具が作った後に書き替えられていない")
    src_rel = mark.get("src", "")
    src_path = os.path.join(ROOT, src_rel) if src_rel else ""
    if not src_path or not os.path.isfile(src_path):
        ok(False, "依頼書の目印の元データが在る", src_rel or "目印に src が無い")
        return lines
    ok(mark.get("src_sha256") == sha256_file(src_path), "元データは、依頼書を作った後に書き替えられていない")
    src_text = open(src_path, encoding="utf-8").read()
    first = src_text.partition("\n")[0]
    _s, smeta, _e = parse_src(src_path)
    if first.startswith(GEN_MARK):
        import gen_acceptance as ga
        a = dict(re.findall(r"(\S+?)=(\S+)", first))
        work = a.get("work") or re.sub(r"^.*／設計書 ", "", smeta.get("監査対象タスク", ""))
        tgt = smeta.get("監査の相手", "")
        dpath = repo_path(tgt) if tgt else ""
        ok(bool(dpath) and os.path.isfile(dpath) and a.get("design_sha256") == sha256_file(dpath),
           "監査の相手の設計書は、元データを作った時と同じ", tgt or "元データのメタに監査の相手が無い")
        tpath = ga.gv.work_dir(work) / ga.TODO_MD
        ok(tpath.is_file() and a.get("src_sha256") == sha256_file(str(tpath)),
           "設計書の元（やることの表.md）は、元データを作った時と同じ", str(tpath))
        cp = int((re.search(r"\d+", smeta.get("cp", "")) or [0])[0] or 0)
        show = dpath if os.path.basename(tgt) != os.path.basename(DESIGN) else None
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                again, _b = build_design_src(a.get("kind", ""), cp, work, design_path=show, show_path=show)
            again = re.sub(r"^日付: .*$", f"日付: {smeta.get('日付', '')}", again, count=1, flags=re.M)
            same = again.partition("\n")[2] == src_text.partition("\n")[2]
            ok(same, "元データは、設計書と工事のフォルダから作り直した物と1文字も同じ",
               "" if same else first_diff(src_text.partition("\n")[2], again.partition("\n")[2]))
        except SystemExit as e:
            ok(False, "元データを、設計書と工事のフォルダから作り直せる", str(e)[:200])
    else:
        ok(smeta.get("監査の種類", "") == NODESIGN_LABEL, "目印の無い（手書きの）元データは、手書きの依頼の物",
           f"監査の種類＝{smeta.get('監査の種類', '')}")
    tmpd = tempfile.mkdtemp(prefix="gad_check_", suffix="_work", dir=AUDITS)
    try:
        out = os.path.join(tmpd, os.path.basename(req_path))
        with contextlib.redirect_stdout(io.StringIO()):
            build_request(src_path, out)
        again_req = open(out, encoding="utf-8").read() if os.path.isfile(out) else ""
        ok(again_req == text, "依頼書は、元データから作り直した物と1文字も同じ",
           "作り直せなかった" if not again_req else first_diff(text, again_req))
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    return lines


# ───────────── 依頼書を読む ─────────────

Q_RE = re.compile(r"^### (\S+) — (.*)（優先度 ([A-D])）$")
# ★2026-10-21（199回目・まこさん「監査が答えられない質問するな」）＝問いの中の「特に見てほしい点」（Q8 など）の行。
#   結果の骨組みに点ごとの欄（#### Q8 — …）を作り、照らしで点ごとの答えが在るかを見る（直す前は Q1〜Q5 の欄しか無く、点を飛ばせた）
POINT_RE = re.compile(r"^- \*\*(Q\d+)　(.+?)\*\*（優先度 ([A-D])）$")
POINT_HEAD_RE = re.compile(r"^#### (Q\d+) — ")
S_RE = re.compile(r"^### 検索 (\d+) — (.*)$")
S_ITEM_RE = re.compile(r"^(\d+)\. \*\*(.+?)\*\*:\s*$")          # ★2026-09-30＝依頼書の外部検索のテンプレの形


def parse_request(path: str):
    errs = []
    text = open(path, encoding="utf-8").read()
    body, mark = split_mark(text)
    if not mark or mark.get("body_sha256") is None:
        errs.append("依頼書に道具の目印が無い（道具で作った依頼書ではない）")
    elif mark.get("body_sha256") != sha256_text(body):
        errs.append("依頼書が、道具で作った後に書き替えられている（本文のハッシュ値が目印と違う）")
    head, secs = split_sections(body)
    info = {"title": "", "meta": {}, "facts": [], "general": [], "questions": [], "searches": [],
            "search_n": None, "self_n": 0, "conclusions": [], "heads": [h for h, _ in secs], "points": {}}
    for ln in head:
        if ln.startswith("# 【監査依頼】"):
            info["title"] = ln[len("# 【監査依頼】"):]
    for h, lines in secs:
        kind = kind_of(h, SECTION_KIND)
        if kind == "メタ":
            for ln in lines:
                m = re.match(r"^- (.+?): (.*)$", ln)
                if m:
                    info["meta"][m.group(1)] = m.group(2)
        elif kind == "事実データ":
            info["facts"] = [ln[4:] for ln in lines if ln.startswith("### ")]
        elif kind == "視点":
            # ★2026-10-18（192回目）＝一般の観点①〜⑦と、外の基準で確かめること（外部検索）は、同じ節の2つの小見出し
            info["general"] = [ln[2:] for ln in lines if GENERAL_RE.match(ln)]
            for ln in lines:
                m = S_ITEM_RE.match(ln)
                if m:
                    info["searches"].append((int(m.group(1)), m.group(2)))
                m = re.match(r"^件数: (\d+) 件", ln)
                if m:
                    info["search_n"] = int(m.group(1))
        elif kind == "問い":
            cur = None
            for ln in lines:
                m = Q_RE.match(ln)
                if m:
                    info["questions"].append((m.group(1), m.group(2), m.group(3)))
                    cur = m.group(1)
                    continue
                p = POINT_RE.match(ln)
                if p and cur:
                    info["points"].setdefault(cur, []).append((p.group(1), p.group(2), p.group(3)))
        elif kind == "自己申告":
            info["self_n"] = sum(1 for ln in lines if re.match(r"^\d+\. ", ln))
    return info, errs


def result_names():
    """テンプレの「## 結果ファイルフォーマット」の表から、11節の番号と名前を読む。"""
    _, secs = split_sections(open(TEMPLATE, encoding="utf-8").read())
    for h, lines in secs:
        if h.startswith("## 答えの出し方"):
            return [(int(m.group(1)), m.group(2))
                    for m in (re.match(r"^\|\s*(\d+)\s*\|\s*\*\*(.+?)\*\*", ln) for ln in lines) if m]
    return []


def sorted_questions(qs: list) -> list:
    return sorted(qs, key=lambda q: PRIORITIES.index(q[2]))


# ───────────── 結果の骨組みを作る ─────────────

def build_result(req_path: str, out_path: str) -> int:
    info, errs = parse_request(req_path)
    names = result_names()
    if len(names) != 11:
        errs.append(f"テンプレの結果の表から節が11個 読めない（{len(names)} 個）")
    cp = re.sub(r"^.*_(cp\w+)_audit_request\.md$", r"\1", os.path.basename(req_path))
    out = [f"# 監査結果 {cp} — {info['title']}", ""]
    for n, name in names:
        kind = kind_of(name, RESULT_KIND)
        if kind is None:
            errs.append(f"結果の節「{name}」の骨組みの作り方が道具に無い（テンプレが変わった）")
            continue
        out += [f"## {n}. {name}", ""]
        if kind == "空":
            out += [PLACE]
        elif kind == "版":
            out += [f"- 依頼書: `{rel_of(req_path)}`",
                    f"- 依頼書のハッシュ値: {sha256_file(req_path)}",
                    f"- 監査の相手と版（依頼書に書いてあるもの）: {info['meta'].get('監査の相手と版', '（依頼書に無い）')}",
                    f"- 監査が照らしたハッシュ値: {PLACE}",
                    f"- 実施日: {PLACE}"]
        elif kind == "事実データ":
            for f in info["facts"]:
                out += [f"### {f}", "", PLACE, ""]
        elif kind == "所見":
            # ★2026-10-18（192回目・まこさん「一般の観点→この内容は一番外してはいけない」）＝観点ごとに「見つけた事と根拠」を書かせる
            #   （直す前は PASS／FAIL だけで、形だけ埋まる原因だった）。依頼書に観点が無ければ「該当なし」（見出しは残す）
            out += ["### 一般の観点", ""] + ([f"- {g} ＝ {PLACE}" for g in info["general"]]
                                            or ["該当なし（依頼書のとおり）"]) + [""]
            for qid, qname, pr in sorted_questions(info["questions"]):
                out += [f"### {qid} — {qname}（優先度 {pr}）", "", PLACE, ""]
                for pid, pname, ppr in info["points"].get(qid, []):
                    out += [f"#### {pid} — {pname}（優先度 {ppr}）", "", PLACE, ""]
                out += [f"修正の番号＝{PLACE}", ""]
        elif kind == "外部検索":
            for i, s in info["searches"]:
                out += [f"### 検索 {i} — {s}", "", PLACE, ""]
            if not info["searches"]:
                out += ["該当なし（依頼書のとおり）", ""]
        elif kind == "自己申告":
            for i in range(1, info["self_n"] + 1):
                out += [f"### 自己申告 {i}", "", PLACE, ""]
        elif kind == "総合判定":
            # ★2026-10-18（192回目）＝「結論を決める問い」の段は無くした。結論は、重さ（Critical の有無）で決まる
            out += ["### 結論と件数", "", f"- 結論＝<GO / CONDITIONAL-GO / NO-GO>（根拠＝{PLACE}）"]
            out += [f"- {s}＝<件数>" for s in SEVERITY_FIX + SEVERITY_PROCESS]
        elif kind == "修正":
            for s in SEVERITY_FIX:
                out += [f"### {s}", "", "（無ければ「なし」）", ""]
        elif kind == "プロセス":
            out += ["### Process", "", "（無ければ「なし」）"]
        out = body_strip(out) + ["", ""]
    text = "\n".join(body_strip(out)) + "\n"
    text += f"\n{MARK} result request={rel_of(req_path)} request_sha256={sha256_file(req_path)} -->\n"
    for e in errs:
        print(f"❌ {e}")
    wrote = write_out(out_path, text, "result")
    if not errs and wrote:
        print(f"✅ 結果の骨組みを作った（節 {len(names)}・問い {len(info['questions'])}・"
              f"事実データ {len(info['facts'])}・外部検索 {len(info['searches'])}・自己申告 {info['self_n']}）")
    return 0 if (not errs and wrote) else 1


# ───────────── 照らす ─────────────

def check_lines(req_path: str, rtext: str) -> list:
    """依頼書（ファイル）と結果（文字列）を照らす。戻り＝「✅ …」「❌ …」の行。hook 11 もこれを呼ぶ。"""
    info, errs = parse_request(req_path)
    lines_out = []

    def ok(cond: bool, what: str, detail: str = "") -> None:
        lines_out.append(("✅ " if cond else "❌ ") + what + (f"（{detail}）" if detail and not cond else ""))

    for e in errs:
        ok(False, e)
    rbody, rmark = split_mark(rtext)
    _, rsecs = split_sections(rbody)
    names = result_names()
    want = [f"## {n}. {name}" for n, name in names]
    got = [h for h, _ in rsecs]
    ok(got == want, "結果の節の名前と並びが、テンプレの11節と同じ",
       f"違う所＝{[g for g in got if g not in want] + [w for w in want if w not in got]}")
    ok(rmark.get("request_sha256") == sha256_file(req_path), "結果は、いまの依頼書に対して書かれている",
       "結果の目印の依頼書のハッシュ値が、いまの依頼書と違う")
    sec = {h: "\n".join(ls) for h, ls in rsecs}

    def body_of(kind: str) -> str:
        for n, name in names:
            if kind_of(name, RESULT_KIND) == kind:
                return sec.get(f"## {n}. {name}", "")
        return ""

    q_want = [q[0] for q in sorted_questions(info["questions"])]
    q_got = [m.group(1) for m in (Q_RE.match(ln) for ln in body_of("所見").splitlines()) if m]
    ok(q_got == q_want, f"所見の見出し＝依頼書の問いの番号を、優先度の順に並べたもの（{len(q_want)} 件）",
       f"依頼書＝{q_want} ／ 結果＝{q_got}")
    p_want = [p[0] for q in q_want for p in info["points"].get(q, [])]
    p_got = [m.group(1) for m in (POINT_HEAD_RE.match(ln) for ln in body_of("所見").splitlines()) if m]
    ok(p_got == p_want, f"所見の「特に見てほしい点」の見出し＝依頼書の点の番号を、問いの順に並べたもの（{len(p_want)} 件）",
       f"依頼書＝{p_want} ／ 結果＝{p_got}")
    g_got = len(re.findall(r"^- [①-⑦]", body_of("所見"), re.M))
    ok(g_got == len(info["general"]), f"所見の一般の観点＝依頼書の ①〜⑦（{len(info['general'])} 件）",
       f"結果＝{g_got} 件")
    f_got = re.findall(r"^### (.+)$", body_of("事実データ"), re.M)
    ok(f_got == info["facts"], f"事実データの確認の見出し＝依頼書の事実データ（{len(info['facts'])} 件）",
       f"依頼書＝{info['facts']} ／ 結果＝{f_got}")
    ok(info["search_n"] == len(info["searches"]), "依頼書の外部検索の件数の行＝検索対象の数",
       f"件数の行＝{info['search_n']} ／ 検索対象＝{len(info['searches'])}")
    s_got = [(int(m.group(1)), m.group(2)) for m in (S_RE.match(ln) for ln in body_of("外部検索").splitlines()) if m]
    ok(s_got == info["searches"], f"外部検索の見出し＝依頼書の検索対象（{len(info['searches'])} 件）",
       f"依頼書＝{info['searches']} ／ 結果＝{s_got}")
    ok(bool(re.search(r"^- 結論＝", body_of("総合判定"), re.M)), "総合判定に「- 結論＝」の行が在る")
    a_got = len(re.findall(r"^### 自己申告 \d+$", body_of("自己申告"), re.M))
    ok(a_got == info["self_n"], f"自己申告への答えの数＝依頼書の自己申告の数（{info['self_n']} 件）",
       f"結果＝{a_got} 件")
    fix_heads = re.findall(r"^### (\S+)$", body_of("修正"), re.M)
    ok(fix_heads == list(SEVERITY_FIX), "修正の指示の重さの見出し＝Critical・Major・Minor", f"結果＝{fix_heads}")
    pro_heads = re.findall(r"^### (\S+)$", body_of("プロセス"), re.M)
    ok(pro_heads == list(SEVERITY_PROCESS), "CC プロセス欠陥対策の重さの見出し＝Process", f"結果＝{pro_heads}")
    refs = set()
    for v in re.findall(r"^修正の番号＝(.+)$", body_of("所見"), re.M):
        if PLACE in v or v.strip() in ("なし", ""):
            continue
        refs |= set(re.findall(r"\d+", v))
    defs = set(re.findall(r"^#### 修正 (\d+)$", body_of("修正") + "\n" + body_of("プロセス"), re.M))
    if refs or defs:
        ok(refs == defs, "所見に書いた修正の番号＝修正の指示と CC プロセス欠陥対策に在る番号",
           f"所見だけ＝{sorted(refs - defs)} ／ 修正だけ＝{sorted(defs - refs)}")
    else:
        lines_out.append("（所見と修正の番号は、まだ中身が無いので照らさない）")
    return lines_out


# ───────────── 中身を書いた結果の形 ─────────────

FOURTH = ("直した後の文字", "足す文字", "消す文字", "走らせるコマンド")
STATES = ("確定", "未決", "案が複数")
BANNED = ("修正の方向性", "直し方（案）", "対策＝", "取り下げ")   # テンプレの「書けないもの」の語
FOURTH_RE = re.compile(r"^(?:案([A-Z]) )?(直した後の文字|足す文字|消す文字|走らせるコマンド):\s*\n~~~\n", re.M)
EVIDENCE_RE = re.compile(r"\S+:\d+.*「.+」")


def item_fields(num: str, block: str) -> dict:
    """修正の指示1件から、6つの欄を読み取って返す（形は見ない・読むだけ）。

    ★2026-09-16（設計書 audit-autofix-apply-20260916 の 4-3）＝当てる道具（apply_audit_fix.py）と
      この道具の `item_errors` が、同じ読み取りを呼ぶ形にするために切り出した。
      同じ正規表現を2か所に書くと、片方だけ直って食い違うため。

    戻り＝{"番号", "対象のファイル", "直す箇所", "直す前の文字"（囲みの中・無ければ None）,
           "4つ目"＝[(案の記号 or "", 見出し, 中身), …], "根拠の抜き書き", "状態"}
    """
    block = re.split(r"^### ", block, flags=re.M)[0]

    def field(label: str):
        m = re.search(rf"^{label}:[ \t]*(.*)$", block, re.M)
        return m.group(1).strip() if m else None

    before = re.search(r"^直す前の文字:[ \t]*\n~~~\n(.*?)\n?~~~", block, re.S | re.M)
    fourth = []
    for m in re.finditer(r"^(?:案([A-Z]) )?(直した後の文字|足す文字|消す文字|走らせるコマンド):"
                         r"[ \t]*\n~~~\n(.*?)\n?~~~", block, re.S | re.M):
        fourth.append((m.group(1) or "", m.group(2), m.group(3)))
    return {"番号": num,
            "対象のファイル": field("対象のファイル"),
            "直す箇所": field("直す箇所"),
            "直す前の文字": before.group(1) if before else None,
            "4つ目": fourth,
            "根拠の抜き書き": field("根拠の抜き書き"),
            "状態": field("状態")}


def item_errors(num: str, block: str) -> list:
    """修正の指示1件の欄を見る。★読み取りは item_fields（2か所に書かない）。"""
    e = []
    f = item_fields(num, block)
    block = re.split(r"^### ", block, flags=re.M)[0]

    def field(label: str):
        m = re.search(rf"^{label}:[ \t]*(.*)$", block, re.M)
        return m.group(1).strip() if m else None

    tgt = field("対象のファイル")
    if not tgt:
        e.append("対象のファイルが無い")
    elif re.search(r"\s", tgt):
        e.append(f"対象のファイルが1つのパスでない（{tgt}）")
    loc = field("直す箇所")
    if not loc:
        e.append("直す箇所が無い")
    before = f["直す前の文字"]
    if before is None:
        e.append("直す前の文字の囲み（~~~）が無い")
    fourth = [(a, k) for a, k, _ in f["4つ目"]]
    if not fourth:
        e.append(f"4つ目の欄（{'・'.join(FOURTH)} のどれか）が無い")
    ev = field("根拠の抜き書き")
    # 新しいファイルを作る指示（直す前の文字が「なし」で、直した後の文字か足す文字を書く）には、
    # 開ける行がまだ無い。だから「ファイル名:行番号「逐語」」の形を求めない。根拠の欄が在ることだけを見る。
    # 決定＝まこさん 2026-10-02「じゃあAでいいよ」（147回目・工事 D の修正 24 がこの形で当たらなかった）。
    new_file = (before is not None and before.strip() == "なし"
                and any(k in ("直した後の文字", "足す文字") for _, k in fourth))
    if not ev or (not new_file and not EVIDENCE_RE.search(ev)):
        e.append("根拠の抜き書きが「ファイル名:行番号「その行の逐語」」の形でない")
    st = field("状態")
    if st not in STATES:
        e.append(f"状態が「確定」「未決」「案が複数」のどれでもない（{st}）")
    n_plans = sum(1 for a, _ in fourth if a)
    if st == "案が複数" and n_plans < 2:
        e.append("状態が「案が複数」なのに、案が2つ以上 無い")
    if st != "案が複数" and n_plans:
        e.append("案A などが在るのに、状態が「案が複数」でない")
    if any(k == "走らせるコマンド" for _, k in fourth):
        if before is None or before.strip() != "なし":
            e.append("走らせるコマンドなのに、直す前の文字が「なし」でない")
        if loc != "なし":
            e.append("走らせるコマンドなのに、直す箇所が「なし」でない")
    return [f"修正 {num}: {x}" for x in e]


def form_errors(rtext: str) -> list:
    """中身を書いた結果が、テンプレの形かを見る。戻り＝食い違いの文の一覧。hook 11 もこれを呼ぶ。"""
    errs = []
    body, _ = split_mark(rtext)
    for ph in PLACEHOLDERS:
        if ph in body:
            errs.append(f"「{ph}」が残っている（中身を書いていない所が在る）")
    _, secs = split_sections(body)
    sec = {h: "\n".join(ls) for h, ls in secs}
    for n, name in result_names():
        kind = kind_of(name, RESULT_KIND)
        text = sec.get(f"## {n}. {name}", "")
        if kind == "総合判定":
            if not re.search(r"^- 結論＝(GO|CONDITIONAL-GO|NO-GO)(（.*）)?[ \t]*$", text, re.M):
                errs.append(f"{n}. {name} の結論が「GO」「CONDITIONAL-GO」「NO-GO」のどれでもない")
            for c, yn in re.findall(r"^- (.+?) ＝ (\S+?)（", text, re.M):
                if yn not in ("YES", "NO"):
                    errs.append(f"{n}. {name} の「{c}」の答えが YES / NO でない（{yn}）")
        if kind in ("所見", "修正", "プロセス"):
            for w in BANNED:
                if w in text:
                    errs.append(f"{n}. {name} に「{w}」が在る（テンプレの「書けないもの」）")
        if kind in ("修正", "プロセス"):
            parts = re.split(r"^#### 修正 (\d+)[ \t]*$", text, flags=re.M)
            for num, block in zip(parts[1::2], parts[2::2]):
                errs += item_errors(num, block)
    return errs


def selftest(keep: bool = False) -> int:
    """request-design の自己テスト（2026-09-29・まこさん指摘「監査の依頼内容が変じゃないか？」を測る）。

    ★本物の inputs にも設計書にも書かない。依頼書は一時の置き場に作る。
    ★2026-09-30（設計書 point1-one-way-20260930-2）＝本物の元データ（acceptance_src.json）と本物の設計書を読むのをやめた。
      設計書の道具の見本の工事のフォルダ（gen_acceptance._sample_work）と、そこから作った見本の設計書だけで試す。
    """
    import shutil
    import tempfile
    from pathlib import Path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_acceptance as ga
    # ★置き場は監査の置き場の中（外だと依頼書を書かず、空の依頼書で「出さない」の試しが素通りした＝2026-09-29 に実測）
    tmpd = tempfile.mkdtemp(prefix="gad_selftest_", suffix="_work", dir=AUDITS)
    # 見本の工事のフォルダはリポジトリの中の一時の置き場（設計書の道具がリポジトリからの相対のパスを書くため）
    vtmp = Path(tempfile.mkdtemp(prefix="_selftest_gad_verbatim_", dir=os.path.join(ROOT, ".claude", "state")))
    saved = (ga.WORK, ga.gv.VERBATIM_DIR, ga.gv.ARCHIVE_DIR, ga.src_from_work)
    ok = total = 0
    fails = []
    req = ""

    def case(name, good):
        nonlocal ok, total
        total += 1
        good = bool(good) and bool(req)          # ★依頼書が空なら、どの試しも通さない
        ok += bool(good)
        print(f"   {'✅' if good else '❌'} T{total} {name}")
        if not good:
            fails.append(name)

    try:
        ga.gv.VERBATIM_DIR, ga.gv.ARCHIVE_DIR = vtmp / "verbatim", vtmp / "archive"
        work = ga._sample_work(vtmp)
        ga.WORK = work
        design_path = str(vtmp / "acceptance_sample.md")
        ga.write(dest=Path(design_path))
        d = ga.src_from_work(work)
        # ★2026-10-02（144回目）＝判断が要る4つは手書きのファイルから読む。見本の必読は、道具が拾う要るファイルを全部 入れる
        _need = need_reads(d, _impl_evidence(d.get("iter", "")), "impl")
        _rl = [v for v, _l in ga.gv.lines(f"{work}/req_s")]
        hand_body = ("# 見本\n\n## この工事は何のためか\n| 何のためか | 出どころ |\n|---|---|\n| 見本の目的の文。 | "
                     + "・".join(_rl) + " |\n"
                     + "\n## 必読\n| ファイルと範囲 | なぜ要るか |\n|---|---|\n"
                     + "".join(f"| `{p}` | 見本の理由 |\n" for p, _w, _c in _need)
                     + "| `.claude/tools/gen_acceptance.py`（:1-5） | 見本の範囲 |\n"
                     + "\n## 経緯\n見本の経緯。\n"
                     + "\n## 工事ごとの問い\n### Q8 — 見本の問い（優先度 A）\n理由：見本の理由\n見本の見てほしいこと\n"
                     + "\n## 要望のまとめ\n| 要望 | 出どころ |\n|---|---|\n| 目的：見本の目的を満たす | " + "・".join(_rl) + " |\n")
        hand_i = ga.gv.work_dir(work) / HAND_MD.format(label="実装の監査")
        for lb in ("実装の監査", "設計書の監査"):
            (ga.gv.work_dir(work) / HAND_MD.format(label=lb)).write_text(hand_body, encoding="utf-8")
        engine = ga.touches_trading(d)
        text, base = build_design_src("design", 999, work, design_path)
        sp = os.path.join(tmpd, "src.gen.md")
        open(sp, "w", encoding="utf-8").write(text)
        op = os.path.join(tmpd, f"{base}_audit_request.md")
        rc = build_request(sp, op)
        req = open(op, encoding="utf-8").read() if os.path.isfile(op) else ""
        case("依頼書が作れる（rc=0）", rc == 0 and bool(req))
        case("売買に触らない工事では「net は M2-L」の前提を出さない（§40 の1）", engine or "M2-L" not in req)
        case("売買に触らない工事では engine_tuner の目的の文を大目的に出さない（§40 の1）",
             engine or "engine_tuner の目的は" not in req)
        case("売買に触らない工事では前の工事の検査の表を事実データに出さない（§40 の3）",
             engine or "| コマンド | 種類 | 終了コード |" not in req)
        w = re.findall(r"^### W\d+ — ", req, re.M)
        tl = (ga.gv.work_dir(work) / ga.TODO_MD).read_text(encoding="utf-8").splitlines()
        assign = ga._md_table(ga._sections(tl, re.compile(r"^##\s+(?!#)(.+)$")).get("手書きと自動の割り当て") or [],
                              ("項目", "手書き／自動"), "割り当て", [])
        case("問いは割り当ての表の1行ごと（W）に1つずつ在る", bool(assign) and len(w) == len(assign))
        case("テンプレの「N 件」を残さない（§40 の10）", "N 件" not in req)
        case("置き場は根からの全パスにそろえる（§40 の11）", "`.claude/audits/" not in req)
        names = [(s.get("名前") if isinstance(s, dict) else str(s)) for s in (d.get("外部検索") or [])]
        case("外部検索は OK された案の【外部検索】から作る（§40 の9）", bool(names) and all(n in req for n in names))
        case("売買に触らない工事では「Crypto futures」の守則を出さない（§41）", engine or "Crypto futures" not in req)
        # ★テンプレの注記（_template.md 97行目）は書き替えない決まり（設計書 3-1 の6）なので、必読の表の行だけを見る
        case("必読に古い元データ（acceptance_src.json）を入れない（1本のやり方）",
             not any(re.match(r"^\d+\. ", ln) and "acceptance_src.json" in ln for ln in req.splitlines()))
        # ★2026-09-30（3点目-a・まこさん OK）＝依頼書の中身をテンプレの形にした（worklog 20260929 §67 の①〜⑤）
        rd = req.split("## 着手前必読", 1)[-1].split("\n## ", 1)[0]
        case("必読はテンプレの形（番号つきの行・表でない）",
             bool(re.search(r"^1\. `", rd, re.M)) and not re.search(r"^\|", rd, re.M))
        info_d, _e = parse_request(op)
        case("外部検索は「外の基準で確かめること」の下に番号つきで、読み取りの数が検索の数と同じ",
             "### 外の基準で確かめること" in req and not re.search(r"^### 検索 \d+ — ", req, re.M)
             and len(info_d["searches"]) == len(names) and info_d["search_n"] == len(names))
        # ★2026-10-18（192回目）＝問いの置き場は1か所。大目的の注記・監査対象は無く、範囲の中・範囲の外が在る
        case("監査の範囲に「範囲の中」「範囲の外」が在り、大目的の注記と監査対象が無い（問いは1か所）",
             "### 範囲の中" in req and "### 範囲の外" in req and "守りの穴探し" in req
             and "⚠️ 本監査スコープ" not in req and "### 監査対象 (本監査内)" not in req and "## はじめに読む案内" not in req)
        # 実装の監査の依頼書＝問いは決まった6問（Q1〜Q6）だけ。設計のもとの1行ずつの問い（S ほか）は出さない
        text_i, base_i = build_design_src("impl", 998, work, design_path)
        sp_i = os.path.join(tmpd, "src_impl.gen.md")
        open(sp_i, "w", encoding="utf-8").write(text_i)
        op_i = os.path.join(tmpd, f"{base_i}_audit_request.md")
        rc_i = build_request(sp_i, op_i)
        req_i = open(op_i, encoding="utf-8").read() if os.path.isfile(op_i) else ""
        qs_i = re.findall(r"^### (\S+) — ", req_i, re.M)
        case("実装の監査の依頼書が作れて、問いは R0・Q1〜Q6（要望が在れば Q7）と工事ごとの問い Q8〜 だけ（S・G・C・I・N・D・W は出さない）",
             rc_i == 0 and qs_i == [REQ_Q[0]] + [q[0] for q in IMPL_QUESTIONS]
             + (["Q7"] if "### Q7 — まこさんの要望" in req_i else []) + ["Q8"])
        case("実装の監査の依頼書に、実装の指示の一覧と当てた記録の事実データが在る",
             "### 設計書の実装の指示の一覧" in req_i and "### 当てた記録" in req_i)
        # ★2026-09-30（工事 point5-audit-q2-20260930）＝まこさんの要望（req_ の逐語）を問う問い2 が在り、結論の決め方も2つの問いを見る
        # ★2026-10-01（142回目・cp57）＝要望は「」で1行につながず、発言ごとに1行ずつ番号つきで並べる形に変えた
        case("実装の監査の依頼書に、まこさんの要望を問う Q7 が在り、「結論を決める問い」の節は無い",
             "### Q7 — まこさんの要望を、この工事の後の実装が満たしているか" in req_i and "結論を決める問い" not in req_i)
        # ★2026-10-02（144回目・cp58 の直し）＝必読・経緯・問い2 の中身と、作った後の中身のチェック
        rd_i = req_i.split("## 着手前必読", 1)[-1].split("\n## ", 1)[0]
        kei_i = req_i.split("## この監査は何のためか", 1)[-1].split("\n## ", 1)[0]
        case("実装の監査の必読は手書きの行と照合の事実（設計書・控え・当てた記録・やることの表）で、逐語と要件のまとめが無い・中身のチェックが0件",
             "`.claude/state/acceptance.md`" in rd_i and "applied_fixes.json" in rd_i and "（:1-5） — 見本の範囲" in rd_i
             and not VERBATIM_NAME_RE.search(rd_i) and "要件のまとめ" not in rd_i and request_content_errors(req_i) == [])
        # ★2026-10-02（144回目・まこさん「前回の経緯にあった１の内容はかなり重要な要件なんだが」「本質を理解できてないのか？」）
        #   ＝経緯の1は「この工事は何のためか」（手書き・出どころつき）、2は「この工事は何か」と目標からのつながり
        case("「この監査は何のためか」の1は「この工事は何のためか」、2は「この工事は何か」と位置、3は結ぶ要件、4は経緯で、逐語のファイルの名前を出さない",
             # ★2026-10-21＝見出しの語の後ろは「：」。経緯は「次のとおりです」の行の下に1件ずつ並ぶ
             "1. **この工事は何のためか**：見本の目的の文。" in kei_i and "2. **この工事は何か**：見本の概要。" in kei_i
             and "**この工事の位置**：目標からこの工事までのつながりは、次のとおりです。全月 net ≥ $1,900" in kei_i
             and "3. **この工事が結ぶ要件**：" in kei_i
             and "4. **経緯**：" in kei_i and "   見本の経緯。" in kei_i and not VERBATIM_NAME_RE.search(kei_i))
        # ★2026-10-18（192回目）＝実装の前と後の版は事実データに1回だけ。Q1・Q2 はそれを指す。控えが無い Q4 は答え方を書く
        case("実装の監査の Q1・Q2 は「実装の前と後の版」の事実データを指し、git のコマンドは事実データに1回だけ。控えの無い Q4 は「控え無し」の答え方",
             "### 実装の前と後の版（git）" in req_i and req_i.count("`git show") == 1
             and "事実データ「実装の前と後の版」の実装の前" in req_i and "（（" not in req_i
             and "所見に「控え無し」と書いてください" in req_i)
        _nd = [p for p, _w, _c in need_reads({"TARGET": ["scripts/priority_rebuild/regime_label.py"]}, {}, "design", ["M2-F-6d"])]
        _pc = _position_chain(["M2-F-6d"])
        case("売買のロジックに触る M2 の工事は、要件定義書・engine_tuner の要件・マイルストーン2本が必読に要り、位置は M2 → M2-F → M2-F-6d",
             all(f"SDK/.claude/{x}" in _nd for x in ("rules/cat_requirements.md", "ratchet/engine_tuner_requirements.md",
                                                       "ratchet/engine_tuner_milestones.md", "ratchet/engine_tuner_milestones2.md"))
             and "→ M2｜" in _pc and "→ M2-F｜" in _pc and "→ M2-F-6d｜" in _pc)
        case("問い2 は手書きの要望のまとめを番号つきで並べ（1件目は目的）、逐語の行（V番号）を出さない",
             "  1. 目的：見本の目的を満たす" in req_i and ":V01" not in req_i)
        case("工事ごとの問い Q8 が、問いの1か所にだけ在り（監査対象には並べない）、必読に要るファイルの事実データが在る",
             "### Q8 — 見本の問い" in req_i and "- Q8：見本の問い" not in req_i and f"### {NEED_NAME}" in req_i)
        # 作った後のチェック＝逐語のファイル・要るファイルの抜け・範囲の外を見つける
        bad_req = re.sub(r"(## 着手前必読[^\n]*\n)", r"\1\n1. `x/req_s.txt` — 逐語\n", req_i, count=1).replace(
            "`.claude/tools/gen_verbatim.py` — 見本の理由", "`x.py` — 見本の理由").replace("（:1-5）", "（:1-999999）")
        _ce = request_content_errors(bad_req)
        case("作った後のチェックが、必読の逐語のファイル・要るファイル（直す相手）の抜け・範囲の外を見つける",
             any("req_s" in e for e in _ce) and any("gen_verbatim.py" in e and "要るファイル" in e for e in _ce)
             and any("範囲がファイルの外" in e for e in _ce))
        _keep = hand_i.read_text(encoding="utf-8")
        stops = []
        for body_w in (None, _keep.replace("目的：見本の目的を満たす | " + "・".join(_rl), "目的：見本の目的を満たす | req_s:V99"),
                       _keep.replace("| `.claude/tools/gen_verbatim.py` | 見本の理由 |\n", ""),
                       _keep.replace("### Q8 — 見本の問い（優先度 A）", "### Q9 — 見本の問い（優先度 A）"),
                       _keep.replace("## この工事は何のためか", "## 何か"),
                       _keep.replace("| 目的：見本の目的を満たす |", "| 見本の目的を満たす |")):
            if body_w is None:
                hand_i.unlink()
            else:
                hand_i.write_text(body_w, encoding="utf-8")
            try:
                build_design_src("impl", 998, work, design_path)
                stops.append(False)
            except SystemExit as e:
                stops.append("監査依頼の手書き" in str(e))
        hand_i.write_text(_keep, encoding="utf-8")
        case("手書きのファイルが無い・要望の出どころが逐語の行に無い・直す相手が必読に無い・問いの番号が Q8 からでない・"
             "何のためかが無い・要望の1件目が目的でないなら止まる",
             stops == [True, True, True, True, True, True])
        # ★2026-09-30（工事 point5-q2-place-20260930）＝問い2 は結論を決める問いの節に在り（骨組みが拾う）、注記も2つの問いに合う
        info_i, _e_i = parse_request(op_i)
        case("依頼書に「結論を決める問い」の節が無く（読み取りも空）、答え方に「重さと結論」が在る",
             not info_i.get("conclusions") and "## この監査で答えてほしいこと" not in req_i and "### 重さと結論" in req_i)
        # ★2026-10-18（192回目）＝要望の問い Q7 は問いの1か所にだけ在る。自己申告に「Q5 の1＝」が残らない
        case("要望の問い Q7 が問いの1か所にだけ在り、自己申告に設計書の表だけの番号が残らない",
             "### Q7 — " in req_i and "- Q7：" not in req_i and "問い2・Q7" not in req_i
             and not re.search(r"\*\*塞げないもの\*\*＝Q\d+ の\d+＝", req_i)
             # ★2026-10-01（工事 point5-q5label-20261001）＝設計書の門の5件は、出どころ（監査 cp14 の Q5）をつけて写す
             and ("Q5 の1" not in req_i or "監査 cp14 の Q5 の1" in req_i))
        # ★2026-10-01（工事 point5-q5label-20261001）＝節どうしの食い違いを道具自身が見る（いまは0件・壊すと見つける）
        src_i, _m_i, _e_i2 = parse_src(sp_i)
        ok_now = consistency_errors(src_i) == []
        src_i["問い"] = [q for q in src_i["問い"] if q["attrs"].get("番号") != REQ_Q[0]]
        broken = any(REQ_Q[0] in e for e in consistency_errors(src_i))
        src_i["問い"] = src_i["問い"] + src_i["問い"][-1:]
        broken2 = any("重なっている" in e for e in consistency_errors(src_i))
        case("固定の問い R0 が無い・問いの番号が重なる実装の監査の元データを、道具自身が見つけて止める", ok_now and broken and broken2)
        # 【外部検索】が無ければ止まる＝src_from_work の戻りから外して試す（見本の逐語は書き替えない）
        orig_sfw = ga.src_from_work
        ga.src_from_work = lambda wk: {k: v for k, v in orig_sfw(wk).items() if k != "外部検索"}
        try:
            build_design_src("design", 999, work, design_path)
            stopped = False
        except SystemExit as e:
            stopped = "外部検索" in str(e)
        finally:
            ga.src_from_work = orig_sfw
        case("OK された案に【外部検索】が無ければ止まる（何を調べるかは手で決める）", stopped)
        # 工事名が無ければ止まる（古い元データへは戻らない）
        try:
            build_design_src("design", 999, "", design_path)
            stopped2 = False
        except SystemExit as e:
            stopped2 = "工事名" in str(e)
        case("工事名が無ければ止まる（依頼書の作り方は工事のフォルダの1本だけ）", stopped2)
        # ★2026-10-01（142回目・まこさん「意味が伝わらない依頼内容を書いちゃ駄目だろ」・cp57 で見つけた6つ）
        # ①まこさんが貼った CC の文の引用（書き方の記号が落ちた形）を見分け、外した行と一緒に要望から除く
        jl = os.path.join(tmpd, "quote_sample.jsonl")
        with open(jl, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "assistant", "uuid": "a1", "timestamp": "2026-01-01T00:00:00Z", "message": {"content": [
                {"type": "text", "text": "- **起きること**：設定の上端に 10 を書くと、組む側の `x_gen.py` が束を組めなくなります。続き"}]}}) + "\n")
        rows_q = [("s:V01", "起きること：設定の上端に 10 を書くと、組む側の x_gen.py が束を組めなくなります。"),
                  ("s:V02", "→とりあえず１０本にする"), ("s:V03", "OK")]
        qset = ga.gv.quoted_cc({"who": ["まこさん"], "time": ["2026-01-02T00:00:00Z"], "session": jl}, rows_q)
        case("①まこさんが貼った CC の文の引用（記号が落ちた形）を見分け、自分の言葉と短い行は残す", qset == {"V01"})
        case("①Q7 の要望は「」でつながず、発言ごとに1行ずつ番号つきで並べる",
             "まこさんの要望（逐語）「" not in req_i
             and " ／ " not in req_i.split("### Q7 — ", 1)[-1].split("\n### ", 1)[0])
        # ②実装の前と後の版が空のまま出ない（控えが commit されていなければ HEAD と作業中の変更）
        case("②実装の前と後の版を「commit （まだ commit していない）」で出さない", "commit （まだ commit していない）" not in req_i)
        # ③実装の監査では、設計書を書くときに止める hook の5件（監査 cp14 の Q5）を出さず、使わない語「門」も書かない
        case("③実装の監査に監査 cp14 の Q5 の5件を出さない・依頼書に「門が書かせる」を書かない",
             "監査 cp14 の Q5" not in req_i and "門が書かせる" not in req_i and "門が書かせる" not in req)
        # ④承認した2つの版の違いを、囲みの中か外かで数える
        v1, v2 = os.path.join(tmpd, "v1.md"), os.path.join(tmpd, "v2.md")
        blk = "<!-- ACC_{0}_START hash=1 -->\n{1}\n<!-- ACC_{0}_END -->\n"
        open(v1, "w", encoding="utf-8").write("見出し\n" + blk.format("IMPL", "a") + blk.format("SPEC", "b") + "外 1\n")
        open(v2, "w", encoding="utf-8").write("見出し\n" + blk.format("IMPL", "a") + blk.format("SPEC", "c") + "外 2\n")
        vd = _version_diff(v1, v2)
        case("④承認した2つの版の違いを、囲みの中（SPEC）と外に分けて数え、実装の指示の囲みが同じと書く",
             "ACC_SPEC の囲みの中で" in vd and "囲みの外で" in vd and "ACC_IMPL は同じ" in vd)
        case("④この工事の外の作業中の変更は、対象（TARGET）を除いた一覧", all(not p.endswith("gen_audit_docs.py")
             for p in _dirty_outside([".claude/tools/gen_audit_docs.py"])))
        # ⑤やることの表の項目の節から やることの番号を読む（手書きの項目の節は数えない）
        tdir = os.path.join(tmpd, "todo_sample")
        os.makedirs(tdir, exist_ok=True)
        open(os.path.join(tdir, "やることの表.md"), "w", encoding="utf-8").write(
            "# 表\n\n## 一覧\n\n| B-1 | 出どころ＝M2-F-7 と M2-Z-99 |\n\n## 手書きの項目\n\n次は M2-F-8\n")
        case("⑤やることの表の項目の節から、やることリストに在る番号だけを読む（手書きの項目の節は数えない）",
             todo_numbers_from_table(tdir) == ["M2-F-7"])
        # ⑥「私」を「依頼を出した CC」にする
        # ⑦（依頼書を読んで見つけた）パスは根からの相対の決まりにそろえる＝表に scripts/… のまま出さず、Q6 は SDK で走らせると書く
        case("⑦実装の監査の表と Q1・Q2 のパスは SDK/ を付け、Q6 は SDK のフォルダで走らせると書く",
             not re.search(r"\| `scripts/", req_i) and "`SDK` のフォルダで走らせます" in req_i)
        # ⑧（まこさん「自動生成できてるかどうかはどうでもよいのでは？」）実装の監査の問いに、自動生成の物差しを出さない
        case("⑧実装の監査の Q7 は要望を満たしているかだけを問い、「手書きせざるを得ない」「道具に入れられる」を出さない",
             "### Q7 — まこさんの要望" in req_i and "手書きせざるを得ない" not in req_i and "道具に入れられる" not in req_i)
        # ⑨★2026-10-18（192回目・まこさん「４つともOK」）＝実装の監査にも、一般の観点①〜⑦（定義つき）と外の基準で確かめることを出す
        #   （2026-10-01 の「該当なし」は置き替わった）。売買に触らない工事では Crypto futures を出さない。塞げないもの・自動生成の物差しは出さない
        case("⑨実装の監査にも一般の観点①〜⑦（定義つき）と外の基準の節が出て、売買に触らない工事では Crypto futures を出さず、塞げないもの・自動生成の物差しを出さない",
             # ★2026-10-21＝ひな型の文を公用文作成の考え方の書き方に直した（「＝」でつながず「：」の後に文を書く）
             "### 一般の観点" in req_i and "- ①統計学的妥当性：" in req_i and "### 外の基準で確かめること" in req_i
             and f"件数: {len(names)} 件" in req_i and "Crypto futures" not in req_i
             and "**塞げないもの**" not in req_i
             and "自動生成" not in req_i.split("## 確かめてほしいこと", 1)[-1].split("## 問いの外から当てる視点", 1)[0])
        # ⑨ 結果の骨組み＝一般の観点は観点ごとの「見つけた事と根拠」の欄、外部検索は検索ごとの見出し、「結論を決める問いへの答え」は無い
        rp_i = os.path.join(tmpd, "result_impl.md")
        rc_r = build_result(op_i, rp_i)
        res_i = open(rp_i, encoding="utf-8").read() if os.path.isfile(rp_i) else ""
        case("結果の骨組みに、一般の観点7つの欄と外部検索の見出しが出て、「結論を決める問いへの答え」が無く、結論に根拠の欄が在る",
             rc_r == 0 and len(re.findall(r"^- [①-⑦]", res_i, re.M)) == 7 and "### 検索 1 — " in res_i
             and "結論を決める問いへの答え" not in res_i and "- 結論＝<GO / CONDITIONAL-GO / NO-GO>（根拠＝" in res_i)
        _v6 = _cc_voice("私の導出・私的な・私たち")
        case(f"⑥CC が書いた文の「私」を「依頼を出した CC」にする（私的・私たちは置き替えない）＝{_v6}",
             _v6 == "依頼を出した CC の導出・私的な・私たち")
        # ★2026-10-12（170回目・まこさん「OK」＝直し方の案 A-2・B-1〜B-3）＝設計書の監査で設計の中身を問い、固定で載せる文を載せる。
        #   上の試しが手書きの文書を書き替えていても効くように、設計書の監査の手書きの文書を書き直してから、依頼書を作り直す。
        (ga.gv.work_dir(work) / HAND_MD.format(label="設計書の監査")).write_text(hand_body, encoding="utf-8")
        text_d2, base_d2 = build_design_src("design", 997, work, design_path)
        sp_d2 = os.path.join(tmpd, "src_design2.gen.md")
        open(sp_d2, "w", encoding="utf-8").write(text_d2)
        op_d2 = os.path.join(tmpd, f"{base_d2}_audit_request.md")
        rc_d2 = build_request(sp_d2, op_d2)
        req_d2 = open(op_d2, encoding="utf-8").read() if os.path.isfile(op_d2) else ""
        case("設計書の監査の依頼書（いままでの形）に、固定の問い R0・設計の中身を問う Q7・手書きの工事ごとの問い Q8 が在る",
             rc_d2 == 0 and bool(re.search(r"^### R0 — ", req_d2, re.M)) and bool(re.search(r"^### Q7 — 設計の中身が", req_d2, re.M))
             and bool(re.search(r"^### Q8 — ", req_d2, re.M)) and "結論を決める問い" not in req_d2)
        case("設計書の監査の対象外に「設計書の中身そのものが正しいか」を入れない",
             bool(req_d2) and "設計書の中身そのものが正しいか" not in req_d2)
        case("設計書の監査と実装の監査の依頼書に、固定で載せる文（要件定義と工事の流れ）が在る",
             CORE_MARK in req_d2 and CORE_MARK in req_i)
        # ★2026-10-18（ToDo の15番）＝新しい形の設計書の監査の依頼書（見本＝検査やプログラムを直す工事・種類②）
        import gen_core_requirements as gcr
        work_n = ga._sample_work(vtmp, new=True)
        ga.WORK = work_n
        design_n = str(vtmp / "acceptance_sample_new.md")
        ga.write(dest=Path(design_n))
        (ga.gv.work_dir(work_n) / HAND_MD.format(label="設計書の監査")).write_text(hand_body, encoding="utf-8")
        try:
            text_n, base_n = build_design_src("design", 996, work_n, design_n, show_path=design_n)
        except SystemExit as e:                          # 止まっても、残りの試しを ❌ にして数える（自己テストごと落とさない）
            print(f"   ❌ 新しい形の見本から、依頼書の元データを作れない: {e}")
            text_n, base_n = "", "2026-10-18_selftest_new_design_cp996"
        sp_n = os.path.join(tmpd, "src_design_new.gen.md")
        open(sp_n, "w", encoding="utf-8").write(text_n)
        op_n = os.path.join(tmpd, f"{base_n}_audit_request.md")
        rc_n = build_request(sp_n, op_n)
        req_n = open(op_n, encoding="utf-8").read() if os.path.isfile(op_n) else ""
        qs_n = re.findall(r"^### (\S+) — ", req_n, re.M)
        # ★2026-10-18（192回目）＝要件の行は、自分の問い R{no} か、まとめの問い RN の本文（「要件定義の{no}番「」）のどちらかに在る
        _rn_body = req_n.split("### RN — ", 1)[-1].split("\n### ", 1)[0] if "### RN — " in req_n else ""
        # ★2026-10-21（199回目・まこさん「OK」「よい」）＝新しい形の設計書の監査は、固定の問い F1〜F12（売買に触る工事は F13 も）と、
        #   検査やプログラムを直す工事の K1〜K4。要件ごとの R・割り当ての W・Q7・R0 は出さない。要件定義は F9 の表に全部の行が在る
        # ★同日（まこさん「こんなに質問項目が必要なの？」→ 5問の案に「よい」）＝新しい形の設計書の監査の問いは Q1〜Q5 の5問だけ。
        #   要件ごとの R・W・Q7・R0・F・C・K・手書きの Q8〜 の見出しは出さない（手書きの問いは Q2・Q3 の中、K は Q3 の中）
        _q2 = req_n.split("### Q2 — ", 1)[-1].split("\n### ", 1)[0] if "### Q2 — " in req_n else ""
        case("新しい形の設計書の監査の依頼書の問いは Q1〜Q5 の5問だけで、Q2 の表に要件定義の全部の行が在り、手書きの問いは Q2 か Q3 の中に在る",
             rc_n == 0 and qs_n == ["Q1", "Q2", "Q3", "Q4", "Q5"]
             and all(f"| {no} |" in _q2 for no, _nm in gcr.requirement_items(full=True))
             and "**特に見てほしい点**" in req_n and "見本の問い" in req_n)
        # ★2026-10-21（199回目・まこさん「監査が答えられない質問するな」）＝結果の骨組みに「特に見てほしい点」の欄が点ごとに出て、
        #   点の欄を消した結果は、照らしが ❌ を出す
        _pn = parse_request(op_n)[0]["points"] if req_n else {}
        _pids = [p[0] for v in _pn.values() for p in v]
        rp_n = os.path.join(tmpd, "result_new.md")
        build_result(op_n, rp_n) if req_n else 1
        res_n = open(rp_n, encoding="utf-8").read() if os.path.isfile(rp_n) else ""
        _ok_n = any(x.startswith("✅ 所見の「特に見てほしい点」") for x in check_lines(op_n, res_n)) if res_n else False
        _bad_n = re.sub(r"^#### Q\d+ — .*$", "", res_n, count=1, flags=re.M)
        _ng_n = any(x.startswith("❌ 所見の「特に見てほしい点」") for x in check_lines(op_n, _bad_n)) if res_n else False
        case("結果の骨組みに「特に見てほしい点」の欄が点ごとに出て、欄を消すと照らしが ❌ を出す",
             bool(_pids) and all(f"#### {p} — " in res_n for p in _pids) and _ok_n and _ng_n)
        # ★2026-10-21（199回目・まこさん「今後二度とこのようなミスを繰り返せないような作りに」）＝同じ中身の問いの止め
        _wq = lambda n, it, v: {"attrs": {"番号": n, "名前": f"割り当て「{it}＝{v}」のとおりか"},   # noqa: E731
                                "body": f"**割り当て**＝項目「{it}」は **{v}**（表）\n\n**見てほしいこと**＝印が［{v}］か。"}
        _rq = lambda no, nm: {"attrs": {"番号": f"R{no}", "名前": f"要件定義の{no}番「{nm}」が、設計書に正しく書かれているか"},  # noqa: E731
                              "body": f"要件定義の{no}番は「{nm}」です。\n「4-7 探索の範囲」に書いています。\n【4-7】に対して書いてください。"}
        _old_w = question_dup_errors([_wq("W01", "§1 概要", "手書き"), _wq("W02", "4-19 通しの例", "手書き")])
        _old_r = question_dup_errors([_rq("3-1", "指標が"), _rq("3-2", "閾値が"), _rq("4", "探し方")])
        _diff = question_dup_errors([_rq("1", "目標"), {"attrs": {"番号": "R10", "名前": "要件定義の10番「違い」が"},
                                                         "body": "要件定義の10番は「違い」です。\n「2-0 結ぶ要件」に書いています。"}])
        case("同じ中身の問い（名前だけが違う割り当ての問い・同じ見出しを読む要件の問い）が在れば依頼書を書かず、違う見出しを読む問いは通す。"
             "作った新しい形の依頼書には、同じ中身の問いが無い",
             len(_old_w) == 1 and "W01・W02" in _old_w[0] and len(_old_r) == 1 and "R3-1・R3-2・R4" in _old_r[0]
             and _diff == [] and rc_n == 0 and "同じ中身の問い" not in req_n)

        def qbody(text: str, num: str) -> str:
            return text.split(f"### {num} — ", 1)[-1].split("\n### ", 1)[0] if f"### {num} — " in text else ""
        # ★2026-10-21（199回目）＝固定の問いの中身と書き先（目的＝§1 概要・結ぶ要件＝読むもの宣言・施策＝一覧の表・
        #   書き方＝割り当ての件数と --dry-run と OK の逐語・K は 4-22 の書き先＝案の写しで自動では入らない）
        q1n, q3n, q5n = qbody(req_n, "Q1"), qbody(req_n, "Q3"), qbody(req_n, "Q5")
        case("5問が、目的と施策の表・出どころ・コードと検査の直しの4つ・完成の条件・書き方を問い、修正の書き先（やることの表は自動で入る／案の写しは自動では入らない）を出す",
             "「### §1 概要」" in q1n and FIX_AUTO[0] in q1n and "読むもの宣言から写しています" in q1n
             and "| 番号 | 施策（一文） | 出どころ |" in q1n and "正しい手段か" in q1n and "「## 一覧」の表" in q1n
             and "| 直すファイル | 実装の指示の番号 |" in q3n and "「4-22」" in q3n and f"【{ga.HEAD_FIVE}】" in q3n and FIX_OK[0] in q3n
             and "完成の条件" in qbody(req_n, "Q4") and "--dry-run" in q5n and "修正の指示は書きません" in q5n)
        case("設計書の「確かめていないこと」が、自己申告に1件ずつ写る",
             "**確かめていないこと**：見本の確かめ。" in req_n and "確かめていない理由は、次のとおりです。見本。" in req_n
             and "確かめるには、次の物を走らせます。見本のコマンド" in req_n)
        kei_n = req_n.split("## この監査は何のためか", 1)[-1].split("\n## ", 1)[0]
        _nums_n = [int(m) for m in re.findall(r"^(\d+)\. \*\*", kei_n, re.M)]
        # ★2026-10-21（199回目）＝新しい形では、§1 概要と目標の①〜⑥を写さず、設計書の場所を書く（Q1・Q4 が設計書を読ませる）
        case("「この監査は何のためか」に、結ぶ要件・経緯・工事の種類・目標の場所が在り、番号が飛ばず、§1 と目標の文を写さない",
             "3. **この工事が結ぶ要件**：" in kei_n and "4. **経緯**：" in kei_n and "   見本の経緯。" in kei_n
             and "5. **工事の種類**：この工事は、種類②" in kei_n and "6. **目標**：CC は、目標を、設計書の「3-0 目標」" in kei_n
             and "2. **この工事は何か**：この工事の中身は、設計書の「§1 概要」" in kei_n
             and "③ net までのつながり：見本のつながり" not in kei_n
             and _nums_n == list(range(1, len(_nums_n) + 1)))
        case("外部検索の検索の言葉は、案の「検索の言葉」の列から作る（古い形の案は、無いと書く）",
             "検索の言葉: 見本 検索の言葉" in req_n and "何と照らすか: 見本の中身" in req_n and SEARCH_NONE in req)
        rd_n = req_n.split("## 着手前必読", 1)[-1].split("\n## ", 1)[0]
        paths_n = re.findall(r"^\d+\. `([^`]+)`", rd_n, re.M)
        case("必読に、同じファイルを2回出さない（範囲と「なぜ」は1行にまとめる）・案の写しが在る",
             bool(paths_n) and len(paths_n) == len(set(paths_n)) and any("okd_s.txt" in p for p in paths_n)
             and len(re.findall(r"^\d+\. `[^`]*gen_verbatim\.py`", rd_n, re.M)) == 1)
        case("パスを直す関数が「../../.claude/…」を実物のパスにする",
             repo_ref("../../.claude/tools/gen_acceptance.py") == ".claude/tools/gen_acceptance.py"
             and repo_ref("scripts/priority_rebuild/periods.py") == "SDK/scripts/priority_rebuild/periods.py"
             and repo_ref("no/such/file.py") == "")
        # ★2026-10-18（192回目）＝案内の節は無い。固定の文（要約）はメタ情報のすぐ下。売買に触らない工事では 4〜6・9 を載せない
        case("案内の節が無く、固定の文（要約）がメタ情報のすぐ下に在り、売買に触らない工事では 4〜6・9 を載せない",
             "## はじめに読む案内" not in req_n and req_n.index(CORE_HEAD) < req_n.index("## この監査は何のためか")
             and "**■ 1. CAT プロジェクトの目標**" in req_n and "**■ 4. 探し方**" not in req_n
             and len(gcr.embed_lines("core")) < len(gcr.embed_lines("all")))
        case("「修正をどこに書くか」に、設計書の監査は書き先が3通り（設計書の元・案の写し・置き場）、実装の監査は実装のファイル",
             "### 修正をどこに書くか" in req_n and "修正の指示の書き先は、設計書の見出しの種類で決まります" in req_n and "okd_s.txt" in req_n
             and "置き場から写した行" in req_n and "実装が設計書と違う所の修正は、その実装のファイル" in req_i)
        cr = check_request(op_n) if req_n else []
        tl_n = ga.gv.work_dir(work_n) / ga.TODO_MD
        _keep_n = tl_n.read_text(encoding="utf-8")
        tl_n.write_text(_keep_n + "\n", encoding="utf-8")
        cr_bad = check_request(op_n) if req_n else []
        tl_n.write_text(_keep_n, encoding="utf-8")
        case("依頼書を元データと照らす口が、いまの依頼書は全部 ✅・設計書の元を書き替えると ❌ を出す",
             bool(cr) and all(x.startswith("✅ ") for x in cr) and any(x.startswith("❌ ") and "設計書の元" in x for x in cr_bad))
        # ★2026-10-18（まこさん「よい」＝指定どおりかを見本で照らす）＝指標や売買のロジックに触る工事（種類①）の要件ごとの問い。
        #   見本の工事は種類②なので、直すファイルの一覧と 4-6・4-7 だけを差し替えた中身で、問いを組む（本物には書かない）
        d1 = ga.src_from_work(work_n)
        d1["TARGET"] = ["scripts/priority_rebuild/observe_config.json"]
        d1["設計の中身"].update({"4-6": ["- 見本の制約。"], "4-7": ["- 見本の探索の範囲。"]})
        qs1 = _design_new_questions(d1, open(design_n, encoding="utf-8").read(), "`やることの表.md`", "`okd_s.txt`")
        q1 = {n: b for n, _p, _w, _nm, b in qs1}
        case("指標や売買のロジックに触る工事（種類①）では、K を出さず、R3-1 は「4-7 探索の範囲」を読ませ、書き先に置き場の行を添える",
             not any(n.startswith("K") for n in q1) and "「4-7 探索の範囲」の見出しに書きました" in q1.get("R3-1", "")
             and "写した元の置き場のファイル" in q1.get("R3-1", "") and "検査やプログラムを直す工事です" not in q1.get("R3-1", "")
             and any(n == "RN" and "本当に当たらないか" in nm and "5" in nm for n, _p, _w, nm, _b in qs1))
        if keep:
            open(os.path.join(tmpd, "kind1_questions.md"), "w", encoding="utf-8").write(
                "\n\n".join(f"### {n} — {nm}（優先度 {p}）\n\n**優先度の理由**＝{w}\n\n{b}" for n, p, w, nm, b in qs1) + "\n")
        # 設計書の無い直しの監査＝項目は道具・中身は手書き。名前・作業場・監査区分が合わなければ作らない
        hs = os.path.join(tmpd, "hand_nodesign.md")
        hand_src = "\n".join([
            "<!-- 項目: メタ -->", "日付: 2026-10-18", "task: selftest_nodesign", "cp: cp995", "題: CP995 — 見本（手書きの依頼）",
            "依頼者: CC（起案者）", f"監査の種類: {NODESIGN_LABEL}", "売買に触るか: いいえ", "監査対象タスク: 見本",
            "監査の相手: .claude/tools/gen_audit_docs.py", "直す相手: `.claude/tools/gen_audit_docs.py`",
            "<!-- 項目: 目的と経緯 -->", "1. **この工事は何のためか**：見本の目的。", "2. **この工事は何か**：見本の工事。",
            "3. **この工事が結ぶ要件**：要件定義の9番（見本）。", "4. **経緯**：見本の経緯。",
            "<!-- 項目: 範囲の中 -->", "- 監査の相手＝`.claude/tools/gen_audit_docs.py`。", "<!-- 項目: 範囲の外 -->", "- 見本の対象外（理由）",
            "<!-- 項目: 問い 番号=R0 優先度=A 理由=見本の理由 名前=この工事は、要件定義の何番を満たすための物か。要件定義に反する所は無いか -->",
            "見本の R0。",
            "<!-- 項目: 問い 番号=Q1 優先度=A 理由=見本の理由 名前=見本の問い -->", "見本の見てほしいこと。",
            "<!-- 項目: 外の基準が無い理由 -->", "見本の理由（外の基準）。",
            "<!-- 項目: 自己申告 -->", "見本の自己申告。",
            "<!-- 項目: 着手前必読 -->", "1. `.claude/tools/gen_audit_docs.py` — 監査の相手",
            "<!-- 項目: 事実データ 名前=見本の事実 -->", "見本の事実。",
            "<!-- 項目: 修正をどこに書くか -->", "見本の書き先。"]) + "\n"
        open(hs, "w", encoding="utf-8").write(hand_src)
        op_h = os.path.join(tmpd, "2026-10-18_selftest_nodesign_cp995_audit_request.md")
        rc_h = build_request(hs, op_h)
        req_h = open(op_h, encoding="utf-8").read() if os.path.isfile(op_h) else ""
        rc_h2 = build_request(hs, os.path.join(tmpd, "2026-10-18_selftest_other_cp995_audit_request.md"))
        hs3 = os.path.join(tmpd, "hand_not_nodesign.md")
        open(hs3, "w", encoding="utf-8").write(hand_src.replace(f"監査の種類: {NODESIGN_LABEL}", "監査の種類: 設計書の監査"))
        rc_h3 = build_request(hs3, os.path.join(tmpd, "2026-10-18_selftest_nodesign_cp994_audit_request.md"))
        case("手書きの依頼は、手書きの元データから作れ（項目と決まった文は道具・一般の観点と固定の文が出る・0件の外部検索に理由が出る）、"
             "名前に _nodesign_ が無い・種類が違う手書きの元データでは作らない",
             rc_h == 0 and CORE_MARK in req_h and "### 一般の観点" in req_h and "件数: 0 件" in req_h
             and "見本の理由（外の基準）" in req_h and "### R0 — " in req_h and "### 修正をどこに書くか" in req_h
             and rc_h2 == 1 and rc_h3 == 1 and all(x.startswith("✅ ") for x in check_request(op_h)))
    finally:
        ga.WORK, ga.gv.VERBATIM_DIR, ga.gv.ARCHIVE_DIR, ga.src_from_work = saved
        # ★2026-10-18（ToDo の15番）＝--selftest --keep で、見本の依頼書を消さずに残す（読む人の目で、出来上がった文を1回 見るため）
        if keep:
            print(f"（--keep）見本の依頼書と元データを残した: {rel_of(tmpd)}（見本の工事のフォルダ＝{rel_of(str(vtmp))}）")
        else:
            shutil.rmtree(tmpd, ignore_errors=True)
            shutil.rmtree(str(vtmp), ignore_errors=True)
    print(f"\n{'✅' if ok == total else '❌'} selftest {ok}/{total} pass")
    return 0 if ok == total else 1


def main(argv: list) -> int:
    if argv and argv[0] == "--selftest":
        # ★2026-09-30（設計書 point1-one-way-20260930-2）＝控えの元データを受ける口は消した（見本の工事のフォルダだけで試す）
        return selftest(keep=argv[1:] == ["--keep"])
    if len(argv) == 2 and argv[0] == "request-design":
        print("❌ request-design は --work <工事名> が要ります（元データの JSON から作る古い口は消した）")
        return 2
    # ★2026-09-29（135回目）＝request-design <design|impl> --work <工事名>＝工事のフォルダから作った設計書の依頼書
    if len(argv) == 4 and argv[0] == "request-design" and argv[2] == "--work":
        return request_design(argv[1], argv[3])
    # ★2026-10-07（まこさん「A」）＝… --work <工事名> --design <承認の控えの設計書>＝前の工事の依頼書を、控えの設計書から作る
    if len(argv) == 6 and argv[0] == "request-design" and argv[2] == "--work" and argv[4] == "--design":
        return request_design(argv[1], argv[3], argv[5])
    # ★2026-10-18（ToDo の15番）＝check-request <依頼書>＝出来上がった依頼書を、元データ（と設計書・設計書の元）と照らす。何も書かない
    if len(argv) == 2 and argv[0] == "check-request":
        if not os.path.isfile(argv[1]):
            print(f"❌ ファイルが無い: {argv[1]}")
            return 1
        res = check_request(argv[1])
        for ln in res:
            print(ln)
        bad = sum(1 for ln in res if ln.startswith("❌ "))
        print(f"食い違い {bad} 件")
        return 1 if bad else 0
    ok_shape = (len(argv) == 3 and argv[0] in ("request", "result", "check")) or (len(argv) == 2 and argv[0] == "form")
    if not ok_shape:
        print(__doc__)
        return 2
    cmd, files = argv[0], argv[1:]
    for p in (files if cmd in ("check", "form") else files[:1]):
        if not os.path.isfile(p):
            print(f"❌ ファイルが無い: {p}")
            return 1
    if cmd == "request":
        return build_request(files[0], files[1])
    if cmd == "result":
        return build_result(files[0], files[1])
    if cmd == "check":
        lines = check_lines(files[0], open(files[1], encoding="utf-8").read())
        for ln in lines:
            print(ln)
        bad = sum(1 for ln in lines if ln.startswith("❌ "))
        print(f"食い違い {bad} 件")
        return 1 if bad else 0
    errs = form_errors(open(files[0], encoding="utf-8").read())
    for e in errs:
        print(f"❌ {e}")
    print(f"形の食い違い {len(errs)} 件")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

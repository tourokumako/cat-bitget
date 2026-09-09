<!-- ARC iter="gen-acceptance-tool-20260909" -->

# 設計書｜設計書を作るプログラム（gen_acceptance.py）の残る不具合2件を直す

TARGET: .claude/tools/gen_acceptance.py, .claude/tools/list_banned_words.py, .claude/breaks/b72_acceptance_handwritten.sh, .claude/breaks/b73_acceptance_stale_lines.sh
NEW_FILE: .claude/breaks/b72_acceptance_handwritten.sh, .claude/breaks/b73_acceptance_stale_lines.sh
MODEL: .claude/breaks/lib.sh, .claude/breaks/b33_extra_switch_off.sh

REQUIREMENTS: まこさん指示 2026-09-09（逐語）＝「手で書かざるを得ない部分以外は自動生成にしろ」「手書きはするな」。設計書の形＝7つの節（恒久の決まり70番）。

**承認の状態＝未承認。**

**★この設計書は、2026-09-09 の1本目（gen_acceptance.py を作る）の続きです。**目印（`gen-acceptance-tool-20260909`）は同じにしました。読むもの宣言（`design_read_plan.md`・まこさん OK 2026-09-09）と同じ10件を読んでいます。

## 0｜まこさんの決定（逐語）

> 手で書かざるを得ない部分以外は自動生成にしろよ。
> 手書きはするな
> B（＝先に gen_acceptance.py を直す）
> M2-E-2 はランダム製造機＝デタラメ設計なので、作り直しだ。実装などもってのほか。

## 1｜概要

設計書を作るプログラム `gen_acceptance.py` の、残る不具合2件を直します。あわせて、この道具を守る壊すプログラム2本を作り、`list_banned_words.py` の骨組みを7つの節に合わせます。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測った）

`gen_acceptance.py` は 2026-09-09 に承認をいただいて作りました。動きます。設計書を643行 書き出し、指標141種・法則51件・乱数を使う関数21個・成績表の本数・関数の行番号を、全部 正本から出しました。

自己テスト8件のうち、6件が通り、2件が落ちました。

| # | テスト | 結果 | 中身 |
|---|---|---|---|
| T1 | いまの状態で `--verify` | 落ちた | 書くときと読むときで、囲みの末尾の改行の扱いが違う。同じ中身でも指紋が食い違う |
| T7 | 実物との突き合わせ | 落ちた | テストが `--diff` を走らせるが、いまの設計書は実装前なので齟齬が出る。期待値の書き方が違う |

**★2件とも、設計書の中身には影響しません。**書き出した設計書は正しく出ています。

### 2-2 この設計書が直す範囲

`gen_acceptance.py` の2件と、壊すプログラム2本と、`list_banned_words.py` の骨組みだけです。設計書の中身（M2-E-2 で何を組むか）は、この設計書では決めません。

## 3｜目標と、やらないこと

### 3-1 目標

1. 自己テスト8件が全部 通る。
2. 壊すプログラム2本が、直しを戻すと落ちる。
3. `list_banned_words.py --skeleton` が、7つの節の骨組みを出す。

### 3-2 やらないこと（理由つき）

| # | やらないこと | 理由 |
|---|---|---|
| 1 | M2-E-2 の設計書の中身を直すこと | まこさん指摘 2026-09-09＝「M2-E-2 はランダム製造機＝デタラメ設計なので、作り直しだ」。中身は、この道具を直した後に、元データ（`acceptance_src.json`）を作り直して決めます。**この工事では元データに1文字も触りません** |
| 2 | engine_tuner の実装（`engine_tuner_gen.py`） | 同上。まこさん指摘＝「実装などもってのほか」 |
| 3 | 書き出し先を設計書そのもの（`acceptance.md`）から下書きに変えること | 承認の流れが変わります。いまの流れ（設計書は1本・上書き＝恒久 §0-2）を保ちます。**★ただし、この工事の途中で道具が設計書を上書きしないよう、`--write` は走らせません**（`--dry-run` と、控えを相手にした自己テストだけを使います） |
| 4 | hook 4本（承認・食い違い・必読・読むもの宣言）を変えること | 1文字も触りません |

### 3-3 決めてほしいこと

| # | 中身 | 私の案 |
|---|---|---|
| 1 | 道具を直している最中に、設計書が入れ替わる行き止まりをどう避けるか | この工事では `--write` を走らせません。自己テストは、控えを相手にします。**次の工事（元データの作り直し）で、書き出し先を下書きにするかを決めてもらいます** |

## 4｜設計の中身

### 4-1 直す2件

| # | どこ | いま | 直した後 |
|---|---|---|---|
| 1 | `gen_acceptance.py` の `_h` と `verify` | 書くときは本文の後ろに改行を足し、読むときは末尾の改行を落とす。指紋を数える対象がずれる | 指紋を数える前に、必ず末尾の改行を落とす（`_h` の中で `rstrip`）。読むときと書くときで同じにする |
| 2 | 同 `selftest` の T7 | `--diff` を、いまの設計書に対して走らせる。実装前なので齟齬が出て落ちる | 齟齬の中身を見る。**「実物に無い関数」だけの齟齬なら通す**（実装前だから正しい）。ほかの齟齬（設計書と実物の食い違い）が在れば落とす |

### 4-2 作る壊すプログラム2本

| # | 名前 | 壊し方 | 落ちるテスト |
|---|---|---|---|
| 1 | `b72_acceptance_handwritten.sh` | `verify` の指紋の照合を消す（囲みを手で書き換えても通るようにする） | T2 |
| 2 | `b73_acceptance_stale_lines.sh` | `build_coderef` の行番号を、`def_lines` でなく固定の数字にする | T1 |

### 4-3 `list_banned_words.py` の骨組み

`skeleton()` が出す節の並びを、いまの11節（hook の点検の一覧）から、7つの節（恒久70番）に変えます。hook から項目を抽出する処理（`checklist_items`・`_extract_banned`・`_extract_required`）は1文字も触りません。

## 5｜決めたことと理由・捨てた案

| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | この工事では `--write` を走らせない | 走らせると設計書が上書きされ、この設計書の承認が外れて、道具を直せなくなる（2026-09-09 に実際に起きた） | `--write` で確かめる。捨てた理由＝同じ行き止まりに入る |
| 2 | T7 は「実物に無い関数」だけの齟齬を通す | 実装前は、設計書に書いた関数が実物に無いのが正しい状態 | T7 を消す。捨てた理由＝設計書と実物の食い違いを見る検査が無くなる |
| 3 | 元データ（`acceptance_src.json`）に触らない | 中身は まこさんが「デタラメ」と判定したもの。作り直しは次の工事 | ついでに直す。捨てた理由＝1変更に混ぜない（H16） |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

**★下の表は、これから走らせるテストです。終了コードは直した後に測ります。**

| # | 何を試すか | どうなれば通ったと言えるか |
|---|---|---|
| T1〜T8 | `python3 .claude/tools/gen_acceptance.py --selftest` | 8件とも pass（いまは6件） |
| B1 | `bash .claude/breaks/b72_acceptance_handwritten.sh` | 終了コード 1（T2 が落ちる） |
| B2 | `bash .claude/breaks/b73_acceptance_stale_lines.sh` | 終了コード 1（T1 が落ちる） |
| S1 | `python3 .claude/tools/list_banned_words.py --skeleton` | 7つの節の見出しが出る |

### 6-2 リスク

| # | リスク | どうするか |
|---|---|---|
| 1 | 直している最中に設計書が上書きされ、承認が外れる | `--write` を走らせません（やらないこと3） |
| 2 | 骨組みを変えると、hook の点検の項目が落ちる | 抽出の処理は触りません。付録の節に、いままでどおり項目を並べます |

### 6-3 見積もり

| 何 | 見込み | 根拠 |
|---|---|---|
| 不具合2件の直し | 30分 | 1件は指紋の数え方の1行、1件は齟齬の見分け |
| 壊すプログラム2本 | 30分 | 手本 `b33_extra_switch_off.sh` |
| 骨組みを7節に | 30分 | 節の並びを書き替えるだけ |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

**① 真因（root cause）**＝道具を作ったときに、書くときと読むときで同じ処理を使いませんでした。指紋を数える所が2か所に分かれ、末尾の改行の扱いがずれました。T7 は、実装前の状態を期待値に入れていませんでした。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は動きません。動くのは、自己テストの通る件数（いま6件 → 8件）と、この道具を守る壊すプログラムの本数（いま0本 → 2本）です。

**③ root か symptom か**＝root です。指紋を数える処理を1か所にまとめます。2か所に分かれている限り、また同じずれが出ます。

**④ ベースアップ**＝外の検索は使いません。手本は同じリポジトリの実物です。この設計書を書く前に Read tool で開きました＝`.claude/tools/gen_acceptance.py`（直す相手）／`.claude/tools/gen_regime_kb.py`（同じ作りの道具・1,180行）／`.claude/tools/list_banned_words.py`（骨組みを出す道具）／`scripts/priority_rebuild/verify_design_contract.py`（齟齬の出し方）／`.claude/hooks/require_acceptance_before_impl.sh`・`enforce_design_consistency.py`・`require_source_read_before_acceptance.py`・`require_read_plan_before_design.py`（4本の hook）／`.claude/ratchet/acceptance_archive/tm-scope-and-g2-fingerprint-20260908.md`（承認が通った設計書）／`.claude/rules/acceptance_checklist.md`／`.claude/ratchet/engine_tuner_milestones.md` と `engine_tuner_milestones2.md`。読むもの宣言＝`design_read_plan.md`（まこさん OK 2026-09-09）。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

**この工事に、疑似シミュから取った値は1つもありません。**閾値・段数・AUC のたぐいを1つも決めません。採否は score.py ではなく、自己テスト8件と壊すプログラム2本の終了コードで決まります。

### 7-3 変更の単位（H16）

**変更は1つです**＝設計書を作るプログラムの不具合を直すこと。触るファイルは4本ですが、直す相手は1つです。

**過去に取りやめた失敗の再演か**＝いいえ。**★近い型が1つあります**＝2026-09-09 に、この道具で設計書を上書きして、道具を直せなくなりました。今回は `--write` を走らせません（やらないこと3）。

### 7-4 塞げないもの

| 問い | 塞げないこと |
|---|---|
| **監査 Q5 の1** | 直した後、設計書の中身は正しいか。**分かりません。**この工事は道具の不具合だけを直します。中身（M2-E-2 で何を組むか）は次の工事です |
| **監査 Q5 の2** | 元データの文の中で範囲を狭めないか。**塞げません。**「やらないこと」が空だと止まる検査は在りますが、理由の文が正しいかは見ません |
| **監査 Q5 の3** | 骨組みを7節にすると、hook の点検が漏れないか。**漏れます。**骨組みは私が読む見本で、hook は読みません。hook の点検は、いままでどおり承認のときに走ります |
| **監査 Q5 の4** | 壊すプログラムを手で書き換えられたら。**見抜けません**（印の偽造と同じ限界）。git の差分には出ます |
| **監査 Q5 の5** | この道具自身を書き換えられたら。**無効にできます。**`.claude/tools/*.py` は承認ゲートの相手なので、書き換えには承認が要ります |

### 7-5 §4.6 ハード制約の照合

**群2（18件・売買のロジックか審判を触るときだけ照合するもの）は、まとめて非該当です。**理由＝この工事は文書を作るプログラムだけを触ります。戦略・審判・売買記録に1行も触れません。

**★H2・H8 は非該当**＝材料の列も期間も触りません。

### 7-6 完成の条件

**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。**★触る関数の一覧は、実装の後に確定させます**＝`verify_design_contract.py --write` の出力で置き替えます。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | AUDIT-1＝自己テストが8件とも pass | `python3 .claude/tools/gen_acceptance.py --selftest` | 実経路 | 指紋の照合を消すと T2 が落ちる | `b72_acceptance_handwritten.sh` | 対象 | **未着手** |
| 2 | AUDIT-2＝行番号が `def_lines` から出ている | `python3 .claude/tools/gen_acceptance.py --dry-run` | 実経路 | 行番号を固定の数字にすると T1 が落ちる | `b73_acceptance_stale_lines.sh` | 対象 | **未着手** |
| 3 | AUDIT-3＝骨組みが7つの節を出す | `python3 .claude/tools/list_banned_words.py --skeleton` | 実経路 | 節の並びを11節に戻すと、7つの節の見出しが出ない | `b72_acceptance_handwritten.sh` | 対象 | **未着手** |

<!-- ACCEPT_TABLE_END -->

**★どの壊すプログラムが、どの行を守るか**

| 壊すプログラム | 守る行 | 壊し方 | 期待する終了コード |
|---|---|---|---|
| `b72_acceptance_handwritten.sh` | **#1・#3** | `verify` の指紋の照合を消す | **1** |
| `b73_acceptance_stale_lines.sh` | **#2** | 行番号を固定の数字にする | **1** |

### 7-7 プログラムが読む設定（2つ）

DESIGN_CONTRACT

```json
{
  "impl_file": ".claude/tools/list_banned_words.py",
  "impl_functions": {},
  "no_impl_functions_reason": "この工事の本体（gen_acceptance.py）は今日 作ったばかりで、直す関数は _h・verify・selftest・build_coderef の4つ。ただし直した後に名前と行が変わりうるので、実装の後に確定させます＝verify_design_contract.py --write の出力で置き替えます",
  "self_check_calls": ["skeleton", "checklist_items"],
  "must_use": {},
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は外から一覧を読みません。読むのは設計書と元データだけです",
  "generated_from": {
    "impl_functions": "実装の前なので空（理由＝no_impl_functions_reason）。実装の後に verify_design_contract.py --write の出力で置き替えます",
    "must_use": "impl_functions が空なので空（承認ゲートの決まり）",
    "spec_lists": "外から読む一覧が無いので空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": ".claude/tools/list_banned_words.py",
 "public_functions": {
  "acceptance_target": [],
  "needs_group2": [],
  "checklist_items": [],
  "skeleton": [
   "acceptance_target",
   "checklist_items",
   "needs_group2"
  ],
  "main": [
   "acceptance_target",
   "checklist_items",
   "needs_group2",
   "skeleton"
  ]
 },
 "constants": {},
 "cli_flags": []
}
```

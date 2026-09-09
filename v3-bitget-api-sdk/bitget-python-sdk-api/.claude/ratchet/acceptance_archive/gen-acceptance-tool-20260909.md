<!-- ARC iter="gen-acceptance-tool-20260909" -->

# 設計書｜大きなプログラムに目次を付けて、必要な箇所だけ読めるようにする

TARGET: .claude/tools/gen_code_index.py, .claude/tools/gen_acceptance.py, .claude/tools/list_banned_words.py, .claude/breaks/b72_acceptance_handwritten.sh, .claude/breaks/b73_acceptance_stale_lines.sh, .claude/breaks/b74_skeleton_old_sections.sh, .claude/breaks/b75_code_index_stale.sh
MODEL: .claude/tools/gen_acceptance.py, .claude/breaks/lib.sh, .claude/breaks/b33_extra_switch_off.sh

REQUIREMENTS: まこさん指示 2026-09-09（逐語）＝「長くて読むのがだるいなら、メニューつけて、必要な箇所だけ読めるようにしたら？」。あわせて「手で書かざるを得ない部分以外は自動生成にしろ」（恒久の決まり69番）。

**承認の状態＝3回まで承認済み（`c0d30b8b…`・`2cc8155a…`・`386d14d8…`）。この版は4回目の承認を待っています。**

**★NEW_FILE の行を外しました。**3回目の承認で作る権利をいただき、`gen_code_index.py` と `b75_code_index_stale.sh` を実際に作ったためです。2本とも Read tool で開いています。

## 0｜まこさんの決定（逐語）

> 長くて読むのがだるいなら、メニューつけて、必要な箇所だけ読めるようにしたら？
> よい
> なにを読んでいなかった？ 今後必読にする
> 手で書かざるを得ない部分以外は自動生成にしろよ

## 1｜概要

**6,310行のプログラムに目次を付けて、読むもの宣言で箇所を指定できるようにします。**

## 2｜背景と範囲

### 2-1 何が起きたか（2026-09-09 の実測）

私は `engine_tuner_gen.py` を「全文6,310行 読んだ」と記録に書きました。**実際には乱数を使う場所だけを探し、それ以外を見ていません。**

その結果、**まこさんが 2026-08-24 に承認された4つの要素の強制の仕組みを、丸ごと見落としました。**その仕組みはコードの 345行から365行に在り、まこさんの逐語がそのまま書いてあります。私は1日かけて「その仕組みは無い」と言い続けました。

**根っこは、長すぎて読み切れないのに「全文を読んだ」と書けることです。**

### 2-2 作った後に走らせて出た数

| ファイル | 行数 | 節 | 関数とクラス |
|---|---|---|---|
| `engine_tuner_gen.py` | 6,310 | 23 | 131 |
| `engine_tuner_exec.py` | 4,968 | 15 | 104 |

**★私が見落とした3か所は、見出しの無い区間ではありませんでした。**「材料のパラメータの範囲」という節（226行から942行）の中に在りました。**その1節に関数が33個 入っています。**節の平均は5.7個なので、この節だけが飛び抜けています。

### 2-3 この設計書が直す範囲

目次を作るプログラムを1本 作ります。**engine_tuner の売買のロジックには1行も触りません。**

## 3｜目標と、やらないこと

### 3-1 目標

1. 目次が、コードから機械で作られる。手で書かない。
2. 目次に、節の名前と行の範囲とその節に在る関数の名前が載る。
3. 見出しの無い区間が、目次に出る。

### 3-2 やらないこと（理由つき）

| # | やらないこと | 理由 |
|---|---|---|
| 1 | engine_tuner の売買のロジックを変えること | 目次は読むための道具です。動きを変えません |
| 2 | 読むもの宣言のゲートを変えること | hook は1文字も触りません。宣言の書き方を変えるのは、目次ができた後に別で決めます |
| 3 | 元データ `acceptance_src.json` を作り直すこと | M2-E-2 の本体です。この工事とは別です |
| 4 | 壊すプログラム b72・b73 の作り直し | 2026-09-09 に守りとして働かないことが分かりましたが、net に効かないので後回しにします。**完成の条件の #1 と #2 は「未着手」のまま残ります** |
| 5 | 大きすぎる節（33関数）を分けること | コードのコメントを足す工事になります。**一覧を出したので、分けるかどうかは まこさんに決めていただきます** |

### 3-3 決めてほしいこと

| # | 中身 | 私の案 |
|---|---|---|
| 1 | 大きすぎる節を分けるか | **分けるべきだと思います。**「材料のパラメータの範囲」という名前の節に、4つの要素を検査する処理が入っています。名前から中身が読み取れません。ただしコードを触るので、別の工事にします |

## 4｜設計の中身

### 4-1 目次を作るプログラム（`gen_code_index.py`）

**読む相手**＝`engine_tuner_gen.py` と `engine_tuner_exec.py`。

**出すもの**＝ファイルごとの表。列は4つです。節の名前・行の範囲・その節に在る関数の名前・関数の数。

**節の切り方**＝`# ══` で始まる行を節の始まりとします。次の `# ══` の直前までが、その節です。

**関数の拾い方**＝構文の木で `def` と `class` を拾い、その行番号が節の範囲に入るかで振り分けます。**正規表現では拾いません。**入れ子になった関数は数えません。

**見出しの無い区間**＝最初の `# ══` より前を「見出しの無い区間」として、同じ表に出します。そこに在る関数も並べます。

**書き方**＝`--write` で `.claude/ratchet/code_index.md` に書きます。`--verify` で、コードが変わったのに目次が古いままかを見ます。手本は `gen_acceptance.py` です。

### 4-2 守るもの（fail-closed）

| # | どうなったら止まるか |
|---|---|
| 1 | 読む相手のファイルが無い |
| 2 | 節の見出しが1つも見つからない |
| 3 | 表に並べた関数の数が、構文の木で数えた総数と合わない |

### 4-3 壊すプログラム（`b75_code_index_stale.sh`）

**壊し方**＝目次の中の行の範囲を、実物と違う数字に書き換える。

**期待**＝`--verify` が食い違いを見つけて、終了コード 1 を返す。

## 5｜決めたことと理由・捨てた案

| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 目次は機械で作る | 手で書くと、コードが変わったときに腐ります。恒久69番 | 手で目次を書く。捨てた理由＝今日と同じことが起きます |
| 2 | 節の見出しは、いまコードに在る `# ══` を使う | 既に23個と15個 在ります。新しい印を作りません | 新しい印の形を決める。捨てた理由＝既存の見出しが全部 載らなくなります |
| 3 | 見出しの無い所は、目次に出す | 隠さずに出します | 見出しの無い所を飛ばす。捨てた理由＝見落とした所が目次にも出ません |
| 4 | 壊すプログラム b72・b73 の作り直しは後回し | net に1円も効きません。恒久65番の3番 | いま直す。捨てた理由＝残り時間を配管に使い切ります |
| 5 | 入れ子になった関数は数えない | 目次が細かくなりすぎます | 全部の `def` を拾う。捨てた理由＝表が読めなくなります |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

| # | 何を試すか | どうなれば通ったと言えるか |
|---|---|---|
| S1 | `python3 .claude/tools/gen_code_index.py --write` | 目次が書き出され、2つのファイル分の表が出る |
| S2 | `python3 .claude/tools/gen_code_index.py --verify` | 終了コード 0 |
| S3 | `python3 .claude/tools/gen_code_index.py --selftest` | 6件とも pass |
| B1 | `bash .claude/breaks/b75_code_index_stale.sh` | 終了コード 1 |

### 6-2 リスク

| # | リスク | どうするか |
|---|---|---|
| 1 | 目次を作っても、私が読まずに「読んだ」と書く | **塞げません。**読んだかは機械には分かりません。減るのは「全文」と書ける余地だけです |
| 2 | 節が大きすぎて、名前から中身が読み取れない | **実際に起きています**（33関数の節）。分けるかは §3-3 で まこさんに決めていただきます |
| 3 | 目次が腐る | `--verify` が食い違いを見つけます |

### 6-3 見積もり

| 何 | 見込み | 使った時間 |
|---|---|---|
| 目次を作るプログラム | 1時間 | 約40分 |
| 壊すプログラム1本 | 20分 | 約10分 |
| 走らせて数を出す | 20分 | 約10分 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

**① 真因（root cause）**＝大きなプログラムに、読む前に中身を見渡す手立てがありませんでした。だから「全文を読む」以外の宣言ができず、読み切れないまま「読んだ」と書きました。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は動きません。動くのは、読むもの宣言に書ける単位です。ファイル1本から、節ごとに変わります。

**③ root か symptom か**＝root です。読み切れない量を「読んだ」と書ける状態そのものを変えます。**ただし、節が大きすぎる問題は残ります。**そこは別の工事です。

**④ ベースアップ**＝外の検索は使いません。手本は同じリポジトリの実物です。この設計書を書く前に Read tool で開きました＝`.claude/tools/gen_acceptance.py`（手本）／`.claude/tools/gen_code_index.py`（この工事で作ったもの）／`.claude/tools/gen_regime_kb.py`／`.claude/tools/list_banned_words.py`／`scripts/priority_rebuild/verify_design_contract.py`／`scripts/priority_rebuild/engine_tuner_gen.py` の 325〜800行・2215〜2334行・2488〜2499行／`scripts/priority_rebuild/engine_tuner_exec.py` の 1396〜1436行／`.claude/hooks/require_acceptance_before_impl.sh`・`enforce_design_consistency.py`・`require_source_read_before_acceptance.py`・`require_read_plan_before_design.py`／`.claude/breaks/lib.sh`・`b33_extra_switch_off.sh`・`b72_acceptance_handwritten.sh`・`b73_acceptance_stale_lines.sh`・`b74_skeleton_old_sections.sh`・`b75_code_index_stale.sh`／`.claude/ratchet/acceptance_archive/tm-scope-and-g2-fingerprint-20260908.md`／`.claude/rules/acceptance_checklist.md`／`.claude/ratchet/engine_tuner_milestones.md` と `engine_tuner_milestones2.md`。読むもの宣言＝`design_read_plan.md`（まこさん OK 2026-09-09）。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

**この工事に、疑似シミュから取った値は1つもありません。**閾値・段数・AUC のたぐいを1つも決めません。採否は score.py ではなく、走らせて出る表と壊すプログラムの終了コードで決まります。

### 7-3 変更の単位（H16）

**変更は1つです**＝大きなプログラムに目次を付けること。

**過去に取りやめた失敗の再演か**＝いいえ。**★近い型が1つあります**＝2026-09-09 に、この工事で壊すプログラムの設計を3回 間違えました。今回は壊すプログラムを1本だけにし、測る相手も1つ（`--verify` の終了コード）にしました。

### 7-4 塞げないもの

| 問い | 塞げないこと |
|---|---|
| **監査 Q5 の1** | 目次を作っても、私が読むとは限らない。**塞げません。**読んだかどうかは機械には分かりません |
| **監査 Q5 の2** | 見出しの名前が中身と合っているか。**見ません。**見出しはコードに書いてある文字をそのまま写します。**実際に合っていない節が1つ在ります**（33関数の節） |
| **監査 Q5 の3** | 大きすぎる節を分けるか。**私が決めません。**一覧を出したので、まこさんに決めていただきます |
| **監査 Q5 の4** | 目次を手で書き換えられたら。**`--verify` が見つけます。**ただし目次と実物を同時に書き換えれば通ります |
| **監査 Q5 の5** | この道具自身を書き換えられたら。**無効にできます。**`.claude/tools/*.py` は承認ゲートの相手なので、書き換えには承認が要ります |

### 7-5 §4.6 ハード制約の照合

**群2（18件・売買のロジックか審判を触るときだけ照合するもの）は、まとめて非該当です。**理由＝この工事は読むための道具だけを作ります。戦略・審判・売買記録に1行も触れません。

**★H2・H8 は非該当**＝材料の列も期間も触りません。

### 7-6 完成の条件

**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

**★#1 と #2 は、前の工事から引き継いだ行です。**壊すプログラムが守りとして働かないことが 2026-09-09 に分かりました。**この工事では直しません**（§3-2 の4）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | AUDIT-1＝自己テストが8件とも pass | `python3 .claude/tools/gen_acceptance.py --selftest` | 実経路 | ハッシュ値の照合を消すと T2 が落ちる | `b72_acceptance_handwritten.sh` | 対象 | **未着手** |
| 2 | AUDIT-2＝関数の行番号が実物から出ている | `python3 .claude/tools/gen_acceptance.py --selftest` | 実経路 | 行番号を固定の数字にすると T1 が落ちる | `b73_acceptance_stale_lines.sh` | 対象 | **未着手** |
| 3 | AUDIT-3＝骨組みが7つの節を出す | `python3 .claude/tools/list_banned_words.py --skeleton` | 実経路 | 7つ目の節の見出しを古い名前に戻すと節が欠ける | `b74_skeleton_old_sections.sh` | 対象 | **未着手** |
| 4 | AUDIT-4＝目次が実物のコードから作られている | `python3 .claude/tools/gen_code_index.py --verify` | 実経路 | 目次の行番号を実物と違う数字にすると食い違いが出る | `b75_code_index_stale.sh` | 対象 | **未着手** |

<!-- ACCEPT_TABLE_END -->

**★どの壊すプログラムが、どの行を守るか**

| 壊すプログラム | 守る行 | 壊し方 | 期待する終了コード |
|---|---|---|---|
| `b72_acceptance_handwritten.sh` | **#1** | `verify` のハッシュ値の照合を消す | **1** |
| `b73_acceptance_stale_lines.sh` | **#2** | 行番号を固定の数字にする | **1** |
| `b74_skeleton_old_sections.sh` | **#3** | 7つ目の節の見出しを古い名前に戻す | **1** |
| `b75_code_index_stale.sh` | **#4** | 目次の行の範囲を実物と違う数字にする | **1** |

### 7-7 プログラムが読む設定（2つ）

DESIGN_CONTRACT

```json
{
  "impl_file": ".claude/tools/gen_code_index.py",
  "impl_functions": {
    ".claude/tools/gen_code_index.py": [
      "_h", "_esc", "read_src", "find_sections", "find_defs",
      "build_rows", "build_table", "build_body", "page",
      "write", "verify", "selftest", "main"
    ]
  },
  "self_check_calls": ["find_sections", "find_defs", "build_rows"],
  "must_use": {
    "build_body": ["build_table"],
    "page": ["build_body"]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は外から一覧を読みません。読むのはコードのファイルだけです",
  "generated_from": {
    "impl_functions": "実装の後に確定させました。新しく作ったファイルなので、触った関数＝ファイルの中の全部です",
    "must_use": "表を作る処理と、それを束ねる処理が、実際に呼ばれているかを見ます",
    "spec_lists": "外から読む一覧が無いので空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": ".claude/tools/gen_code_index.py",
 "public_functions": {
  "read_src": [],
  "find_sections": [],
  "find_defs": [],
  "build_rows": [
   "find_defs",
   "find_sections",
   "read_src"
  ],
  "build_table": [
   "build_rows",
   "read_src"
  ],
  "build_body": [
   "build_table"
  ],
  "page": [
   "build_body"
  ],
  "write": [
   "build_rows",
   "page"
  ],
  "verify": [
   "build_body"
  ],
  "selftest": [
   "build_rows",
   "find_defs",
   "find_sections",
   "read_src",
   "verify",
   "write"
  ],
  "main": [
   "selftest",
   "verify",
   "write"
  ]
 },
 "constants": {},
 "cli_flags": []
}
```

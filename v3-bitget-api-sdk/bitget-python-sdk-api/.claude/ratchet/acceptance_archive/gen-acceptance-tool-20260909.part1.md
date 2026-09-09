<!-- ARC iter="gen-acceptance-tool-20260909" -->

# 設計書｜engine_tuner の設計書を、プログラムが作る形にする（gen_acceptance.py）

TARGET: .claude/tools/list_banned_words.py, .claude/tools/gen_acceptance.py, .claude/ratchet/acceptance_src.json, .claude/breaks/b72_acceptance_handwritten.sh, .claude/breaks/b73_acceptance_stale_lines.sh
NEW_FILE: .claude/tools/gen_acceptance.py, .claude/ratchet/acceptance_src.json, .claude/breaks/b72_acceptance_handwritten.sh, .claude/breaks/b73_acceptance_stale_lines.sh
MODEL: .claude/tools/gen_regime_kb.py, .claude/breaks/lib.sh, .claude/breaks/b33_extra_switch_off.sh

REQUIREMENTS: まこさん指示 2026-09-09（逐語）＝「ヌケモレがおおいから、手で書かざるを得ない部分以外は自動生成にしろよ。」「この自動生成の件、毎回言ってるんだけど。いい加減覚えろよ」「手書きはするな」。設計書の形＝まこさん決定 2026-09-09（逐語「いいよ」）＝7つの節（恒久の決まり70番）。

**承認の状態＝未承認。**実装はまだ1行も入れていません。

## 0｜まこさんの決定（逐語）

> ヌケモレがおおいから、手で書かざるを得ない部分以外は自動生成にしろよ。。。。なんで最低限守って。虚偽、ヌケモレ、不正予防のために自動生成にしろって言ってだけど。なんでできない。
> この自動生成の件、毎回言ってるんだけど。いい加減覚えろよ
> 手書きはするな
> （設計書の形の案に対して）いいよ

**あわせて効く決定**＝「M2-Cでオンにしてる指標と、閾値と、パラメータと時間軸から、役割に沿って、レンジの法則に則った組み合わせを作れって言ってんだよ。なんで勝手に検索範囲を狭める」「お前が法則を決めるな」「WEB検索をして根拠のある法則であるのか確かめたうえで、決めようよ」。

## 1｜概要

**engine_tuner の設計書を、私が手で書くのをやめます。**元データ（json）と実物（コード・法則ファイル・型の表・印・成績表）から、プログラムが設計書を組み立てます。私が手で書くのは、元データの中の5つだけです。何を作るか、なぜ作るか、組み方、やらないことと理由、決めてほしいこと。

## 2｜背景と範囲

### 2-1 いまの状態（実測）

**M2-E-2 の設計書（577行・2026-09-09 に書いたもの）で、プログラムが作ったのは SPEC の囲みだけでした。**それ以外は全部 手書きです。

| 実測 | 中身 |
|---|---|
| 設計書の行数 | 577行。うちプログラムが作った SPEC の囲み＝約250行。残り約327行は手書き |
| 手で写した行番号 | `sample_regime_build` 2283・`_ranked_material_at` 2215・`regime_draw_order` 2256 ほか。**`verify_design_contract.py --write` は走らせるたびに「関数の定義の行を書き出した: 131件（★設計書はこの表を引く＝行番号を手で写さない・93番）」と画面に出す。**その表を使わずに手で写した |
| 手で並べた一覧 | 法則21件の表・売買を回すプログラムの数え方・格子と範囲・乱数の場所。**このうち法則の表は、2件（R11・C8）を落として まこさんに指摘された** |
| 手で切った候補 | §2.2 の候補のうち12件（強さ3種・3枠目の「なし」・出来高・BB%b・経過バー・時間足の範囲・転換線と基準線・ATR%・realized_vol・stdev%・時刻・需給・転がし窓の順位）。**「入りません」と設計書に書き、まこさんに「ありえないよね」「他にもあるだろ」と指摘された** |

**同じ日に、同じ型の間違いを4回 しました。**乱数を「承認済み」と書いた。候補を切った。行番号を手で写した。§2.2 の説明を都合よく書いた。過去の違反25件のうち、私が自分で気づいたのは1件です。

### 2-2 この設計書が直す範囲

engine_tuner の設計書（`.claude/state/acceptance.md`）を作る仕組みです。設計書の中身（M2-E-2 で何を作るか）は、この設計書では決めません。それは次の工事です。

## 3｜目標と、やらないこと

### 3-1 目標

1. **設計書の中で、私が手で書く所を5つに限る。**何を作るか・なぜ作るか・組み方・やらないことと理由・決めてほしいこと。
2. **残りは全部、正本から作る。**行番号・関数名・法則の一覧・材料の一覧・格子と範囲・件数・SPEC・テストの表。
3. **手で書き換えたら検出する。**`--verify` が、囲みの中が機械の書いたままかを見る。
4. **形は7つの節に固定する**（恒久70番）。

### 3-2 やらないこと（理由と出どころつき）

| # | やらないこと | 理由 |
|---|---|---|
| 1 | 設計書の**中身**（M2-E-2 で何を組むか）を決めること | この工事は仕組みだけ。中身は次の工事で、元データ（json）に書く |
| 2 | 既に在る設計書の hook を変えること | 承認ゲート・食い違いゲート・必読ゲート・読むもの宣言ゲートは1文字も触らない。**作る設計書が、いまの hook を通る形にする**（節7 の付録） |
| 3 | 承認済みの控え（`acceptance_archive`）を作り直すこと | 過去の控えは、そのときの承認の証拠。触らない |
| 4 | 戦略の設計書（Peterson の7節・雛形 e34_design.md）の形を変えること | あれは売買の戦略用。まこさん決定 2026-06-13 のまま残す。この工事は道具の設計書だけ |
| 5 | `list_banned_words.py` の**抽出の処理**（`checklist_items`・`_extract_banned`・`_extract_required`）を変えること | hook の実体から項目を抜き出す仕組み。**節7（付録）の元として使う**。触るのは `skeleton()` が出す節の並びだけ |
| 6 | 元データ（json）に、正本から作れる値を書くこと | 行番号・件数・一覧を json に書いたら、手書きと同じ。**json に書くのは、正本のどこを引くかの指定だけ** |

### 3-3 決めてほしいこと

| # | 中身 | 私の案（決まるまでこれで進める） |
|---|---|---|
| 1 | 元データ（json）の置き場 | `.claude/ratchet/acceptance_src.json`。理由＝`m2_todo.json`・`regime_laws.json` と同じ場所で、git に入る |
| 2 | 設計書を1本だけにするか、工事ごとに元データを分けるか | 元データは工事ごとに1つの節（`iter` の名前が鍵）。設計書は今までどおり `acceptance.md` に上書き（恒久 §0-2 の1） |

## 4｜設計の中身

### 4-1 作るもの（3つ）

| # | ファイル | 何か |
|---|---|---|
| 1 | `.claude/tools/gen_acceptance.py` | 設計書を作るプログラム。`--write`／`--verify`／`--dry-run`／`--selftest` |
| 2 | `.claude/ratchet/acceptance_src.json` | 元データ。手で書く5つと、正本のどこを引くかの指定 |
| 3 | `.claude/breaks/b72_*.sh`・`b73_*.sh` | わざと壊して止まるか試すプログラム |
| 4 | `.claude/tools/list_banned_words.py`（既存・直す） | `--skeleton` が出す骨組みを、7つの節（恒久70番）に合わせる。**いまは hook の点検の一覧を11節で出す**＝人が読む形ではない（まこさん指摘 2026-09-09）。★hook から項目を抽出する処理（`checklist_items`）は1文字も触らない＝付録の元として残す。**触る関数＝`skeleton`（定義の行＝215。出どころ＝`--write` が書き出した「関数の定義の行」の表・手で写していない）** |

### 4-2 プログラムが作る節（囲みの中・手で触れない）

**手本＝`gen_regime_kb.py`。**目印（`<!-- ACCEPTANCE_<節>_START hash=… -->` 〜 `_END`）で囲み、`--write` が中を書き、`--verify` が本文の sha256 と目印の値を照らします。

| 囲み | 中身 | 何から作るか（正本） |
|---|---|---|
| MATERIALS | 探す材料の一覧＝印がオンの指標（種類の数・一覧）・別枠（geo・需給・時間帯）・役割ごとの系統・時間足・パラメータの範囲・閾値の格子と範囲 | `indicator_switch.json`（`on`・`geo_on`・`demand_on`・`time_on`）／`signal_families.json`（`role_lineage`）／`search_limits.json`（`quantile_grid`・`int_grid`・各 `*_range`）／`engine_tuner_gen.material_ranges()` |
| LAWS | 場面の法則の一覧＝番号・一文・機械が読む判定（型・数える部品・本数）・掛かる場面・根拠の有無 | `regime_laws.json`（全件。**落とさない**＝`jq` ではなくプログラムが全部 並べる） |
| RANKING | 成績表に載っている本数＝役割 × 上位足 × 札ごとの列の本数と、上位の例 | `material_ranking.json`（`ranked_materials` を import して、印の絞りを通した後の並び） |
| CODEREF | 触る関数の名前と定義の行 | `verify_design_contract.spec_from_impl()` の `def_lines`（★手で写さない・93番） |
| RANDOM | 乱数を使っている場所＝`rng`・`draw_param` の行数と関数名 | `engine_tuner_gen.py` を構文の木で読む |
| ACCEPT_TABLE | 完成の条件の表（欄＝# ／ 完成の条件 ／ コマンド ／ 経路 ／ 壊し方 ／ 壊すプログラム ／ 監査確認 ／ いまの状態） | 元データの「完成の条件」＋壊し方の記録（`<iter>.breaks.json`） |
| SELFTEST | わざと壊して止まるか試すテストの一覧 | `verify_design_contract.SELF_TESTS` と、元データの「壊すプログラム」 |
| SPEC | SPEC と DESIGN_CONTRACT | `verify_design_contract.write_actual()` の出力を読む |
| CHECKLIST | 節7 の照合の項目（群1・群2） | `list_banned_words.checklist_items()`（hook の実体から抽出） |

### 4-3 手で書く元データ（5つだけ・json）

```json
{
  "iter": "<ARC iter の名前>",
  "何を作るか": "1つの文",
  "なぜ作るか": ["実測の行（コマンドつき）"],
  "組み方": ["法則を満たす組み合わせを、どう並べるか"],
  "やらないこと": [{"中身": "", "理由": "", "出どころ": ""}],
  "決めてほしいこと": [{"中身": "", "私の案": ""}],
  "完成の条件": [{"条件": "", "コマンド": "", "経路": "実経路", "壊し方": "", "壊すプログラム": "", "監査確認": "対象"}]
}
```

**★「やらないこと」は、この json に書かないと設計書に出ません。**空なら `--write` が止まります（後述の fail-closed）。

### 4-4 fail-closed（黙って通さない・4つ）

1. 正本のファイルが読めない → 止まる（手本＝`gen_regime_kb._pass_json`）。
2. 元データの「やらないこと」が空 → 止まる。**理由＝私が候補を切ったのに何も書かない、を防ぐ**（2026-09-09 の矮小化の再演）。
3. 置き換えられない目印が本文に残った → 止まる（手本＝`gen_regime_kb.apply_marks`）。
4. 法則ファイルの件数と、LAWS の囲みに出た件数が違う → 止まる。**理由＝法則を落として並べる、を防ぐ**（今日 R11・C8 を落とした）。

### 4-5 作るとどうなるか（例）

M2-E-2 の設計書を、この仕組みで作り直すと、こうなります。

- 節4（設計の中身）の材料の一覧に、「印がオンの指標 141種」がプログラムの数字で出ます。私が「4つだけ」と書く道がありません。
- 節3（やらないこと）に、§2.2 の候補と実際に探す範囲の差が、1件ずつ理由つきで並びます。差が0でなければ、隠せません。
- 節7（付録）の行番号は、`--write` を走らせた時点の実物です。手で写した古い番号が入りません。

## 5｜決めたことと理由・捨てた案

| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 手本を `gen_regime_kb.py` にする | 同じ作り（囲み・hash・fail-closed・他のプログラムの囲みを壊さない）が既に動いていて、`--verify` の番人も在る | 白紙から書く。捨てた理由＝同じ穴（囲みの壊し合い＝154番）を踏み直す |
| 2 | 元データを json 1本にする | `m2_todo.json`（やることリスト）と同じ形。git の差分で中身が見える | 設計書の中に元データを書く。捨てた理由＝それは手書きに戻る |
| 3 | 行番号は `def_lines` から引く | 実装のたびにずれる。`--write` が毎回 出している | grep の出力を写す。捨てた理由＝今日それをやって、また写した |
| 4 | 節の形を7つに固定する | まこさん決定 2026-09-09（恒久70番） | hook の骨組み（11節）をそのまま使う。捨てた理由＝人が読む形ではない（まこさん指摘） |
| 5 | hook の項目は付録に置く | hook を通す必要がある。ただし本文に混ぜると読めない | hook の項目を本文に散らす。捨てた理由＝いまの設計書がそれで読めなくなった |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

**★下の表は、これから作るテストの一覧です。まだ1件も走らせていません**（本体のプログラムがまだ無いため）。終了コードは実装の後に測ります。

| # | 何を試すか | どうなれば通ったと言えるか |
|---|---|---|
| T1 | いまの状態で `python3 .claude/tools/gen_acceptance.py --verify` | 終了コード 0 |
| T2 | 囲みに1行 足して `python3 .claude/tools/gen_acceptance.py --verify` | 終了コード 1（手本 `gen_regime_kb.py` の T2 と同じ形） |
| T3 | 元データの「やらないこと」を空にして `python3 .claude/tools/gen_acceptance.py --write` | 終了コード 1 |
| T4 | 法則ファイルの控えから1件 消して `python3 .claude/tools/gen_acceptance.py --write` | 終了コード 1（件数の照合） |
| T5 | 正本（印の json）の控えを読めなくして `python3 .claude/tools/gen_acceptance.py --write` | 終了コード 1 |
| T6 | 置き換えない目印を元データに書いて `python3 .claude/tools/gen_acceptance.py --write` | 終了コード 1 |
| T7 | 作った設計書を `python3 scripts/priority_rebuild/verify_design_contract.py --diff` に通す | 齟齬 0件 |
| T8 | 作った設計書を `python3 .claude/hooks/enforce_design_consistency.py --check` に通す | 終了コード 0 |

**壊すプログラム**＝`b72`（囲みを手で書き換えても `--verify` が通るように緩める → T2 が落ちる）・`b73`（行番号を `def_lines` でなく固定の数字にする → T7 が落ちる）。

### 6-2 リスク

| # | リスク | どうするか |
|---|---|---|
| 1 | 元データの文の中で、私が範囲を狭める | 塞げません。まこさんの目と、監査 cp34 の問いで見てもらう（依頼書に「切ったものは何か」を入れる） |
| 2 | プログラム自身を書き換えれば無効にできる | 塞げません。git の差分には出ます |
| 3 | 作った設計書が hook を通らない | T7・T8 で先に確かめる。通らなければ、hook でなく生成の側を直す |

### 6-3 見積もり

| 何 | 見込み | 根拠 |
|---|---|---|
| `gen_acceptance.py` を書く | 3時間 | 手本 `gen_regime_kb.py` は1,180行。今回は囲み9つ＝同じ規模 |
| `list_banned_words.py` の `skeleton()` を7節に直す | 30分 | 節の並びを書き替えるだけ（抽出の処理は触らない） |
| 元データ（M2-E-2 の分）を書く | 1時間 | 手で書く5つだけ。控え（scratchpad の手書き版）から写す |
| テスト8件と壊すプログラム2本 | 1時間 | 手本 `b33_extra_switch_off.sh` |
| M2-E-2 の設計書を作り直す | 30分 | `--write` を走らせて確かめる |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

**① 真因（root cause）**＝設計書を「書く文章」として扱ったことです。正本から作れる値（行番号・一覧・件数）を、私が手で写しました。写した値は、実物が動いた瞬間に嘘になります。並べた一覧は落ちます（今日 法則2件を落とした）。まこさんは、手書きの文書を人の目で確かめられません。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は動きません。動くのは、設計書のうち手で書く行の数（いま約327行 → 元データの5項目だけ）と、実物と食い違ったときに止まるかどうか（いま止まらない → `--verify` が止める）です。

**③ root か symptom か**＝root です。「次から気をつける」は symptom です。今日だけで4回 破りました。正本から作る形にすれば、写す手が無くなります。

**④ ベースアップ**＝読むもの宣言10件（`design_read_plan.md`・まこさん OK 2026-09-09）を全部 Read tool で開きました。`.claude/tools/gen_regime_kb.py`（1,180行）／`scripts/priority_rebuild/verify_design_contract.py`（1,825行）／`.claude/tools/list_banned_words.py`（400行）／`.claude/hooks/require_acceptance_before_impl.sh`（1,149行）／`.claude/hooks/enforce_design_consistency.py`（326行）／`.claude/hooks/require_source_read_before_acceptance.py`（467行）／`.claude/hooks/require_read_plan_before_design.py`（220行）／`.claude/ratchet/acceptance_archive/tm-scope-and-g2-fingerprint-20260908.md`（承認が通った設計書）／`.claude/rules/acceptance_checklist.md`／`.claude/ratchet/engine_tuner_milestones.md`（M1〜M6）と `engine_tuner_milestones2.md`（§2.2・§3 の M2-E）。**外の検索**＝設計書の汎用の雛形4件を本文まで開きました（IEEE 1016-2009 の SDD／Google の design doc／Range の Tech Spec／日本語の基本設計書。逐語と URL＝`session_worklog_20260909.md` §69-13）。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

**この工事に、疑似シミュから取った値は1つもありません。**閾値・段数・AUC のたぐいを1つも決めません。**採否は score.py ではなく、①テスト8件 ②壊すプログラム2本の終了コード ③作った設計書が承認ゲートと食い違いゲートを通るか、で決まります。**

### 7-3 変更の単位（H16）

**変更は1つです**＝**engine_tuner の設計書を、プログラムが作る形にすること。**触るファイルは4本ですが、直す相手は1つです（設計書の作り方）。

**過去に取りやめた失敗の再演か**＝いいえ。**★近い型が1つあります**＝`gen_regime_kb.py` が他のプログラムの囲みを消し合った件（154番）です。今回は、既に在る囲み（SPEC の目印）を壊さない形にします（手本の `keep_foreign` と同じ）。

### 7-4 既存を壊さないこと（副作用）

| 何 | どうなるか |
|---|---|
| いまの `acceptance.md`（手書きの M2-E-2） | 控えを scratchpad に写しました。作り直すときに元データへ写します |
| 承認済みの控え（`acceptance_archive` 58件） | 触りません |
| hook 4本 | 1文字も触りません |
| `list_banned_words.py` の抽出の処理 | 触りません。`skeleton()` の節の並びだけを7節に直します。**`--skeleton` の出力の形が変わります**（11節 → 7節）。この出力を読むのは私だけで、hook は読みません（実測＝`grep -rl "skeleton" .claude/hooks/` が0件） |

### 7-5 塞げないもの

| # | 問い | 塞げないこと |
|---|---|---|
| **監査 Q5 の1** | 作った設計書の中身は正しいか | **分かりません。**プログラムが保証するのは、正本と食い違わないことだけです。中身（何を作るか・組み方）は私が元データに書きます |
| **監査 Q5 の2** | 元データの文の中で範囲を狭めないか | **塞げません。**「やらないこと」を空にできない検査は入れますが、理由の文が正しいかは見ません。まこさんの目と監査で見てもらいます |
| **監査 Q5 の3** | 正本そのものが間違っていたら | **見ません。**法則ファイル・型の表・印は正本で、この工事は読むだけです |
| **監査 Q5 の4** | 囲みの外を手で書き換えたら | **`--verify` は囲みの中だけを見ます。**外（節の見出しなど）を書き換えても止まりません |
| **監査 Q5 の5** | プログラム自身を書き換えられたら | **見抜けません**（凍結の対象ですが、印の偽造と同じ限界）。git の差分には出ます |

### 7-6 §4.6 ハード制約の照合

**群2（18件・売買のロジックか審判を触るときだけ1件ずつ照合するもの）は、まとめて非該当です。**理由＝この工事は文書を作るプログラムだけを触ります。戦略・審判（score.py・eval_engine）・売買記録に1行も触れません。

**群1（12件）**＝TARGET・NEW_FILE・MODEL（この節の冒頭）／深掘り4点（7-1）／1変更と過去の失敗の不再演（7-3）／疑似シミュ由来の固定値ゼロ（7-2）／ARC マーカー（冒頭）／自己検査の列挙（6-1）／DESIGN_CONTRACT（7-8）。

**★H2・H8 は非該当**＝この工事は材料の列も期間も触りません。**★`.claude/tools/*.py` は H2・G2 の印の対象ではありません**（印の対象＝`h2_pass.json` の files）。新しく作る `gen_acceptance.py` は新規なので印の一覧に入っていません（確かめ方＝`grep -c gen_acceptance .claude/state/h2_pass.json`）。

### 7-7 完成の条件

**★状態は全部「未着手」です。**私が測った数字は根拠として書きますが、**「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。**★触る関数の一覧（`impl_functions`）は、実装の後に確定させる**＝`verify_design_contract.py --write` の出力で置き替えます。いまは空です（本体のプログラムがまだ無いため）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | AUDIT-1＝**`--selftest` が8件とも pass**（T1〜T8） | `python3 .claude/tools/gen_acceptance.py --selftest` | 実経路 | 囲みを手で書き換えても `--verify` が通るように緩めると T2 が落ちる | `b72_acceptance_handwritten.sh` | 対象 | **未着手** |
| 2 | AUDIT-2＝**作った設計書の行番号が、`--write` の `def_lines` と1件も違わない** | `python3 .claude/tools/gen_acceptance.py --verify` | 実経路 | 行番号を固定の数字にすると、照らして ❌ になる | `b73_acceptance_stale_lines.sh` | 対象 | **未着手** |
| 3 | AUDIT-3＝**手で書く所が、元データの5項目だけ**＝作った設計書のうち、囲みの外の行が元データの文と1文字も違わない | `python3 .claude/tools/gen_acceptance.py --verify` | 実経路 | 囲みの外の照合を消すと、手で足した行が通る | `b72_acceptance_handwritten.sh` | 対象 | **未着手** |
| 4 | AUDIT-4＝**法則ファイルの件数と、作った設計書の法則の件数が同じ**（今日 2件 落とした件の再演を止める） | `python3 .claude/tools/gen_acceptance.py --selftest` | 実経路 | 件数の照合を消すと、1件 消しても通る | `b72_acceptance_handwritten.sh` | 対象 | **未着手** |
| 5 | AUDIT-5＝**作った設計書が、承認ゲートと食い違いゲートを通る** | `python3 .claude/hooks/enforce_design_consistency.py --check .claude/state/acceptance.md` | 実経路 | 付録の項目を落とすと、承認ゲートが止める | `b73_acceptance_stale_lines.sh` | 対象 | **未着手** |

<!-- ACCEPT_TABLE_END -->

**★どの壊すプログラムが、どの行を守るか**

| 壊すプログラム | 守る行 | 壊し方 | 期待する終了コード |
|---|---|---|---|
| `b72_acceptance_handwritten.sh` | **#1・#3・#4** | `--verify` の照合を緩める（囲みの中／囲みの外／件数） | **1** |
| `b73_acceptance_stale_lines.sh` | **#2・#5** | 行番号を `def_lines` でなく固定の数字にする | **1** |

### 7-8 DESIGN_CONTRACT

**★`impl_file` に `list_banned_words.py` を書く理由**＝設計↔実装ゲート（`verify_design_contract.scan_contracts`:370）は、`impl_file` の実物が無いと「読めない契約」として止めます。**新しく作るファイルは、まだ実物がありません。**だから、この工事で確実に触る既存のファイル（`list_banned_words.py`＝骨組みを7節に直す）を `impl_file` にします。**新しく作る `gen_acceptance.py` は `spec_lists` に置き、実装の後に `impl_file` を差し替えます。**

```json
{
  "impl_file": ".claude/tools/list_banned_words.py",
  "impl_functions": {},
  "no_impl_functions_reason": "この工事の本体（gen_acceptance.py）はまだ在りません。実物が無いので、触る関数の一覧を正しく書けません（承認ゲートの決まり＝監査 cp15 の C-4＝正直に空で出す）。★実装の後に確定させる＝verify_design_contract.py --write の出力で置き替えます。設計の段階で分かっているものは、節4-1 の表（作るもの4つ）と節4-2 の表（囲み9つ）に書きました",
  "self_check_calls": ["skeleton", "checklist_items"],
  "must_use": {},
  "spec_lists": {},
  "no_spec_lists_reason": "この工事が読む正本（印・法則ファイル・実物のコード）は、新しく作る gen_acceptance.py が読みます。そのプログラムがまだ無いので、一覧を1件 減らして出力が変わるかを測れません。★実装の後に spec_lists を書いて照らします",
  "generated_from": {
    "impl_functions": "実装の前なので空にしました（理由＝no_impl_functions_reason）。★実装の後に確定させる＝verify_design_contract.py --write の出力で置き替えます",
    "must_use": "impl_functions が空なので空にしました（承認ゲートの決まり＝監査 cp15 の C-4 の対）。実装の後に、節1〜7 の見出し（恒久70番）から書きます",
    "spec_lists": "実装の前なので空にしました（理由＝no_spec_lists_reason）。実装の後に、gen_acceptance.py が読む正本を書きます"
  }
}
```

### 7-9 SPEC（★手書きしない＝`verify_design_contract.py --write` の出力を写した）

**出どころ**＝`python3 scripts/priority_rebuild/verify_design_contract.py --write ../../.claude/state/acceptance.md`（2026-09-09 21:05・公開する関数5件・定数0件・コマンドの旗0件）。**1文字も手で直していません。**この工事で `skeleton` の中身を書き替えますが、呼ぶ相手（`acceptance_target`・`checklist_items`・`needs_group2`）は変えません。

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

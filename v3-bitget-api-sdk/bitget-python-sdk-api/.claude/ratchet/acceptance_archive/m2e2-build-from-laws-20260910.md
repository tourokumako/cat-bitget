<!-- ARC iter="m2e2-build-from-laws-20260910" -->

# 設計書｜束を組む処理に、相場の法則を読ませる（M2-E-2）

TARGET: scripts/priority_rebuild/engine_tuner_gen.py, .claude/breaks/b76_build_ignores_laws.sh, .claude/breaks/b77_build_random_param.sh
NEW_FILE: .claude/breaks/b76_build_ignores_laws.sh, .claude/breaks/b77_build_random_param.sh
MODEL: .claude/breaks/lib.sh, .claude/breaks/b33_extra_switch_off.sh

REQUIREMENTS: まこさんの指示（逐語 2026-08-24）＝「指標、閾値、パラメータ、時間足の役割に基づき、法則に則って４つを組み合わせ、Entry/Exit やレジーム判定などの条件を作る」。まこさんの指摘（逐語 2026-09-09）＝「法則に則って組めって１００回くらい言ってるのに、どうしてもそのとおりにやろうとしないよな」。

**承認の状態＝未承認。**

**読むもの宣言**＝`design_read_plan.md`（目印 `m2e2-build-from-laws-20260910`・まこさんの OK「OK」2026-09-10）。12件を全部 Read tool で開いてから、この設計書を書いています。

## 0｜まこさんの決定（逐語）

> 指標、閾値、パラメータ、時間足の役割に基づき、法則に則って４つを組み合わせ、Entry/Exit やレジーム判定などの条件を作る
> 法則に則って組めって１００回くらい言ってるのに、どうしてもそのとおりにやろうとしないよな
> 総当りで検索ができないから、ネット利益最大化出来る可能性の高い法則を検索して、その法則に当てはめて、組み合わせロジックを見つけようとしてるんだけど
> 乱数は禁止用語にするレベル。絶対に使うな

## 1｜概要

**束を組む処理に、相場の法則を読ませます。**いまは読んでいません。

## 2｜背景と範囲

### 2-1 いまの状態（実物の逐語）

`engine_tuner_gen.py` の 2302行から2303行です。

```
2302行  ex.load_regime_laws()   # 相場の法則の正本が読めることを確かめる
2303行  #   読んだ法則から組むのは M2-E＝ここではまだ使わない
```

**読めることを確かめるだけで、中身を1つも使っていません。**代わりに、束の形が 2330行にそのまま書いてあります。

```
2330行  "on": {"all": [cond_a, cond_b, cond_c]},
```

**法則を書き替えても、組む処理は変わりません。**変わるのは落とす側だけです。

### 2-2 だから何が起きているか

| 誰が | 法則を | どうしている |
|---|---|---|
| 組む処理（`sample_regime_build`） | 読まない | コードに直書きされた3つの条件で組む |
| 落とす側（G7＝`_check_scene_rules`） | 読む | 組まれた束を見て、法則に反していれば落とす |

**組んでから審判に聞く形です。**2026-09-09 の実測では、20回 引き直して**通った束は0本**でした。全部「R4：streak の形が束に無い」で落ちました。

### 2-3 レンジに掛かる法則は10件です（実物から数えた）

| 番号 | 型 | 何を求めるか |
|---|---|---|
| C4 | 部品を数える | 執行足より上の時間足が1本 |
| C6 | 形を持つ | hysteresis の形 |
| R1 | 部品を数える | 構造・位置の系統 または geo が1本 |
| R2 | 系統を重ねない | 構造・位置を除く系統は1本まで |
| R3 | 部品を数える | 同じ1本が「構造・位置」かつ「上位足」 |
| R4 | 形を持つ | **streak の形** |
| R5 | 部品を数える | トレンドの強さ8種のどれかが、決まった側に1本 |
| R6 | 部品を数える | ボラの6種のどれかが、決まった側に1本 |
| R7 | 部品を数える | geo の W% が above に1本 |
| R8 | 形を持つ | not の形 |

**いまの束が満たしていないのは R4（streak）です。**組む処理に streak を作る道がありません。

### 2-4 この設計書が直す範囲

`engine_tuner_gen.py` の1本だけです。**落とす側には1行も触りません。**売買のループにも審判にも触りません。

## 3｜目標と、やらないこと

### 3-1 目標

1. **束を組む処理が、法則ファイルを読んで組む。**法則を1件 書き替えると、組まれる束が変わる。
2. **パラメータと閾値を、範囲の中の決まった並びから取る。**乱数を使わない。
3. **段2c が location からも材料を引ける。**経過バーが引けるようになる。

### 3-2 やらないこと（理由つき）

| # | やらないこと | 理由 |
|---|---|---|
| 1 | 法則ファイルの中身を変えること | **まこさんが決めるものです**（逐語 2026-09-09「お前が法則を決めるな」）。R5・R6・R7 は 2026-09-09 に根拠つきで決めていただきました |
| 2 | 落とす側（G7）を変えること | 組む側と落とす側の二重の守りを保ちます。組む側が満たしても、落とす側がもう一度 見ます |
| 3 | 転換線・基準線を段1 で使えるようにすること | **法則 R2 が禁じています。**トレンドの系統なので、段2a と合わせて2本になり上限1を超えます |
| 4 | 入口と出口の乱数を外すこと | **M3 と M4 の仕事です。**この工事は場面の判定の束だけを直します |
| 5 | 段4（差し戻し）と段5（詰め）を作ること | §2.2 の段0〜段3 が先です。段4・段5 は回数が読めないので、段3 まで動いてから測って決めます |
| 6 | 上げ・下げ・スパイクの束を組むこと | M2-M の仕事です。いまはレンジだけ（実物の 2300行が止めています） |

### 3-3 決めてほしいこと

| # | 中身 | 私の案 |
|---|---|---|
| 1 | 法則を満たせない案が出たとき、どうするか | **その案を作らずに次の番号へ進みます。**いまと同じ形です。**ただし理由を法則の番号で書きます**（いまは「引き直す」としか出ません） |

## 4｜設計の中身

### 4-1 組む処理が法則を読む形（3段）

**第1段｜法則を読んで、要るものの一覧にする。**`ex.load_regime_laws()` が返す法則から、場面が range のものだけを取ります。型ごとに分けます。「形を持つ」は形の名前、「部品を数える」は数える条件と本数、「系統を重ねない」は上限です。

**第2段｜要るものを満たす部品を、成績表の順位から取る。**法則が「トレンドの強さ8種のどれかが below に1本」と言うなら、その8種に当たる材料を、成績表の順位の上から探します。見つかった1本目を使います。**私が名前を選びません。**

**第3段｜形を組み立てる。**法則が求める形を、束の中に必ず入れます。いまは hysteresis と not は在り、**streak が無いので R4 で落ちています。**

### 4-2 パラメータと閾値の乱数を外す

| 何 | いま | 直した後 |
|---|---|---|
| パラメータ | `draw_param` が範囲から乱数で引く | 範囲の中を、案の番号で決まる並びで埋める |
| 閾値（分位） | `_thr_drawn` が範囲から乱数で引く | 同じ |
| 緩め方 | `_loose_q` が乱数 | 同じ |
| 保つ上限 | `_nv` が乱数 | 同じ |

**並び方は `regime_draw_order` と同じ考え方にします。**案の番号から決まる順番で、範囲の中を順に埋めます。**新しい数字を作りません。**範囲の両端は承認済みのものをそのまま使います。

### 4-3 段2c が location からも引ける形

**経過バーは構造・位置の系統なので location に在ります。**段2c は sufficiency から引くので、いまは引けません。

**法則 R2 の「除く系統」に構造・位置が入っています。**だから何本 重ねても上限に掛かりません。**段2c が2つの役割から引ける形にします。**

### 4-4 作るとどうなるか（例を1つ）

案の番号 0 で組むと、こうなります。

| 枠 | 何が入るか | どの法則から |
|---|---|---|
| A | geo の W% が分位より上 | R7 |
| B | location の1位の材料 | R1・R3 |
| C | env「強さ」の1位を not で包む | R5・R8 |
| D | 上位足から引く | C4 |
| E | hysteresis で包む | C6 |
| **F** | **何本 続いたかの条件（streak）** | **R4 ★これが新しく入る** |

**いまの束に無いのは F だけです。**それが「20回とも R4 で落ちた」理由です。

## 5｜決めたことと理由・捨てた案

| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 法則をファイルから読んで組む | 法則を書き替えたら組まれる束が変わる状態にします | 法則の番号をコードに書く。捨てた理由＝いまと同じで、法則を変えても組む処理が変わりません |
| 2 | 材料は成績表の順位から取る | 私が名前を選ぶと、2026-09-09 のように8種に減ります | 私が候補を書く。捨てた理由＝矮小化の再演です |
| 3 | 落とす側は変えない | 二重の守りを保ちます | 落とす側を消す。捨てた理由＝組む側の不具合を検出できなくなります |
| 4 | 転換線と基準線は段1 で使わない | 法則 R2 の上限1を超えます | 型の表で系統を変える。捨てた理由＝承認済みの表を変えることになります |
| 5 | 乱数を外すのはこの束だけ | 1変更を守ります（H16）。入口と出口は M3・M4 | 全部の乱数を一度に外す。捨てた理由＝1変更に混ざります |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

| # | 何を試すか | どうなれば通ったと言えるか |
|---|---|---|
| S1 | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | 全部 pass |
| S2 | `python3 scripts/priority_rebuild/engine_tuner_exec.py --selftest` | 全部 pass |
| S3 | `python3 scripts/priority_rebuild/regime_r9_diag.py --build 3` | **束が3本 出る**（いまは0本） |
| B1 | `bash .claude/breaks/b76_build_ignores_laws.sh` | 終了コード 1 |
| B2 | `bash .claude/breaks/b77_build_random_param.sh` | 終了コード 1 |

**B1 の壊し方**＝組む処理が法則を読む所を消す。すると R4 を満たさない束が出て、落とす側が落とす。

**B2 の壊し方**＝パラメータを乱数で引く形に戻す。すると同じ案の番号でも走らせるたびに違う束が出る。

### 6-2 リスク

| # | リスク | どうするか |
|---|---|---|
| 1 | 法則を全部 満たす束が1本も組めない | **段0 の①で材料が在ることは確かめました。**組めない場合は、どの法則で詰まったかを番号で出します |
| 2 | 乱数を外すと、同じ案しか出なくなる | 案の番号で並びが変わります。番号を進めれば別の束が出ます |
| 3 | 直した後に H2 の検査をやり直す必要がある | この道具は H2 の印の対象です。**約72分 かかります**（2026-09-09 の実測） |

### 6-3 見積もり

| 何 | 見込み | 根拠 |
|---|---|---|
| 法則を読んで組む形にする | 3時間 | 3段の作りを新しく書きます |
| 乱数を外す | 1時間 | 4か所 |
| 段2c が2つの役割から引く | 30分 | 引く役割を増やすだけ |
| 壊すプログラム2本 | 40分 | 手本＝`b33_extra_switch_off.sh` |
| H2 の検査をやり直す | 72分 | 2026-09-09 の実測 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

**① 真因（root cause）**＝組む処理と落とす処理で、法則の扱いが違いました。落とす処理はファイルから読み、組む処理はコードに書いた形を使っていました。だから法則を書き替えても、組まれる束が変わりませんでした。

**② 期待値分解**＝この工事では売買を1件も回しません。勝率・平均利益・敗率・平均損失は動きません。動くのは、法則を全部 満たす束の本数です。いまは0本です。

**③ root か symptom か**＝root です。組む処理が法則を読む形にします。読まない限り、何を直しても「組んでみて落とされる」が続きます。

**④ ベースアップ**＝外の検索は使いません。読むもの宣言の12件を Read tool で開きました＝`.claude/ratchet/code_index.md`／`engine_tuner_gen.py` の4つの節（束を組む 2095〜2547・順位を読む 1233〜1745・パラメータの範囲 226〜942・型の表 1182〜1232 と分位の範囲 1024〜1148）／`engine_tuner_exec.py` の G7 の節（1094〜1858）／`regime_laws.json`／`stage0_match.md`／`stage0_timing.md`／`search_limits.json`／`engine_tuner_milestones.md` の M1〜M6／`engine_tuner_milestones2.md` の §2.2・§2.2-1・M2-E。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

**この工事に、疑似シミュから取った値は1つもありません。**閾値・段数・AUC のたぐいを1つも決めません。範囲の両端は承認済みのものをそのまま使います。採否は、法則を満たす束が出るかどうかで決まります。

### 7-3 変更の単位（H16）

**変更は1つです**＝束を組む処理に法則を読ませること。乱数を外すのも段2c の役割も、その中の一部です。

**過去に取りやめた失敗の再演か**＝いいえ。**★近い型が2つあります。**①2026-09-09 に、法則の中身を私が8種に絞りました。今回は法則をファイルから読むので、私が絞れません。②違反の記録の13番・21番・23番＝「審判に通ること」を目的にした型。今回は組む側に法則を写すので、通ることが目的ではなく、法則に従うことが目的になります。

### 7-4 塞げないもの

| 問い | 塞げないこと |
|---|---|
| **監査 Q5 の1** | 法則を読んで組んでも、net が出るとは限らない。**分かりません。**net は M2-L まで測りません |
| **監査 Q5 の2** | 法則の中身が正しいか。**この工事では見ません。**法則は まこさんが決めたものをそのまま使います |
| **監査 Q5 の3** | 成績表の順位が正しいか。**見ません。**順位は M2-D で作ったものをそのまま使います |
| **監査 Q5 の4** | 乱数を外しても、並びの決め方が恣意的でないか。**塞げません。**案の番号から決まる並びにしますが、その並び方が最善かは分かりません |
| **監査 Q5 の5** | この工事の後、上げ・下げ・スパイクは組めない。**組めません。**M2-M の仕事です |

### 7-5 §4.6 ハード制約の照合

| # | 制約 | 照合 |
|---|---|---|
| **H2** | leak なし | **該当。**材料の列も期間も新しく作りません。既存の処理を使います。**印を取り直します**（約72分） |
| **H8** | 期間分割 | **該当。**値決め窓だけを使います。採点窓には触りません |
| **H16** | 1変更・過去失敗の不再演 | **該当。**§7-3 に書きました |

**そのほかの群2（15件）は非該当です。**理由＝この工事は場面の判定の束を組む処理だけを触ります。売買のループ・審判・売買記録に1行も触れません。

### 7-6 完成の条件

**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。**★触る関数の一覧は、実装の後に確定させます。**

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | AUDIT-1＝法則ファイルを書き替えると、組まれる束が変わる | `python3 scripts/priority_rebuild/regime_r9_diag.py --build 3` | 実経路 | 組む処理が法則を読む所を消すと、R4 を満たさない束が出て落ちる | `b76_build_ignores_laws.sh` | 対象 | **未着手** |
| 2 | AUDIT-2＝同じ案の番号なら、走らせるたびに同じ束が出る | `python3 scripts/priority_rebuild/regime_r9_diag.py --build 3` | 実経路 | パラメータを乱数で引く形に戻すと、同じ番号でも違う束が出る | `b77_build_random_param.sh` | 対象 | **未着手** |

<!-- ACCEPT_TABLE_END -->

**★どの壊すプログラムが、どの行を守るか**

| 壊すプログラム | 守る行 | 壊し方 | 期待する終了コード |
|---|---|---|---|
| `b76_build_ignores_laws.sh` | **#1** | 組む処理が法則を読む所を消す | **1** |
| `b77_build_random_param.sh` | **#2** | パラメータを乱数で引く形に戻す | **1** |

### 7-7 プログラムが読む設定（2つ）

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
  "impl_functions": {},
  "no_impl_functions_reason": "組む処理を3段に作り直すので、新しく作る関数の名前がまだ決まっていません。実装の後に確定させます＝verify_design_contract.py --write の出力で置き替えます",
  "self_check_calls": ["sample_regime_build", "ranked_groups", "regime_draw_order"],
  "must_use": {},
  "spec_lists": {},
  "no_spec_lists_reason": "外から一覧を読む所は既に在ります（法則ファイル・成績表・型の表）。この工事で新しく足しません",
  "generated_from": {
    "impl_functions": "実装の前なので空（理由＝no_impl_functions_reason）。実装の後に確定させます",
    "must_use": "impl_functions が空なので空（承認ゲートの決まり）",
    "spec_lists": "外から読む一覧を新しく足さないので空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
 "public_functions": {
  "load_limits": [],
  "HoldRangeError": [],
  "resolve_hold_range": [
   "HoldRangeError"
  ],
  "hold_bars": [
   "HoldRangeError"
  ],
  "material_pool": [],
  "material_ranges": [
   "load_limits"
  ],
  "param_in_range": [
   "material_ranges"
  ],
  "draw_param": [
   "material_ranges"
  ],
  "assert_provenance": [
   "SampleError",
   "material_ranges",
   "param_in_range",
   "q_range_of"
  ],
  "assert_roles": [
   "SampleError"
  ],
  "assert_exit_roles": [
   "SampleError"
  ],
  "validate_drawn": [
   "strip_marks"
  ],
  "strip_marks": [],
  "int_range_of": [],
  "draw_int": [
   "int_range_of"
  ],
  "num_range_of": [],
  "draw_num": [
   "num_range_of"
  ],
  "ladder_min_frac": [],
  "max_ladder_steps": [
   "ladder_min_frac",
   "num_range_of"
  ],
  "q_range_of": [],
  "quantile_list": [
   "q_range_of"
  ],
  "draw_q": [
   "q_range_of"
  ],
  "q_in_range": [
   "q_range_of"
  ],
  "num_in_range": [
   "num_range_of"
  ],
  "SampleError": [],
  "load_signal_table": [],
  "load_material_ranking": [],
  "ranked_materials": [
   "load_material_ranking"
  ],
  "same_fn_family_pairs": [],
  "pair_allowed": [
   "same_fn_family_pairs"
  ],
  "load_exit_table": [],
  "ranked_groups": [
   "ranked_materials"
  ],
  "regime_draw_order": [
   "SampleError"
  ],
  "sample_regime_build": [
   "SampleError",
   "regime_draw_order"
  ],
  "default_regime": [],
  "sample_structure": [
   "SampleError",
   "default_regime",
   "load_signal_table",
   "sample_regime_build"
  ],
  "recipe_hash": [
   "strip_marks"
  ],
  "write_kakikudashi": [],
  "structure_breakdown": [],
  "needed_qkeys": [],
  "build_qtable": [
   "needed_qkeys"
  ],
  "attach_materials": [],
  "pvalue_daily": [],
  "bh_select": [],
  "strat_gate": [],
  "Journal": [],
  "assert_known_exit_reason": [],
  "run_trial": [
   "strip_marks"
  ],
  "run_trial_guarded": [
   "run_trial"
  ],
  "reject_code": [],
  "zero_trade_gate": [],
  "per_day_gate": [
   "zero_trade_gate"
  ],
  "suggest_slot": [],
  "value_slots": [
   "hold_bars",
   "int_range_of",
   "num_range_of",
   "q_range_of"
  ],
  "apply_slots": [],
  "read_slots": [],
  "run_generation": [
   "Journal",
   "apply_slots",
   "bh_select",
   "build_qtable",
   "load_signal_table",
   "per_day_gate",
   "pvalue_daily",
   "quantile_list",
   "read_slots",
   "recipe_hash",
   "reject_code",
   "run_trial",
   "run_trial_guarded",
   "sample_structure",
   "strat_gate",
   "strip_marks",
   "structure_breakdown",
   "suggest_slot",
   "value_slots",
   "write_kakikudashi"
  ],
  "synth_df": [],
  "selftest_rank_demand": [
   "load_signal_table",
   "ranked_groups",
   "ranked_materials"
  ],
  "selftest": [
   "Journal",
   "apply_slots",
   "assert_known_exit_reason",
   "assert_provenance",
   "bh_select",
   "build_qtable",
   "gate_matrix",
   "ladder_min_frac",
   "lint_provenance",
   "load_exit_table",
   "load_limits",
   "load_material_ranking",
   "load_signal_table",
   "material_pool",
   "material_ranges",
   "max_ladder_steps",
   "needed_qkeys",
   "num_in_range",
   "pair_allowed",
   "param_in_range",
   "per_day_gate",
   "pre_run_gate",
   "pvalue_daily",
   "q_in_range",
   "q_range_of",
   "quantile_list",
   "ranked_groups",
   "ranked_materials",
   "read_slots",
   "regime_draw_order",
   "reject_code",
   "resolve_hold_range",
   "run_generation",
   "run_trial_guarded",
   "sample_structure",
   "selftest_rank_demand",
   "strat_gate",
   "strip_marks",
   "structure_breakdown",
   "synth_df",
   "validate_drawn",
   "value_slots",
   "verify_provenance",
   "zero_trade_gate"
  ],
  "pre_run_gate": [],
  "run_main": [
   "assert_known_exit_reason",
   "hold_bars",
   "load_limits",
   "material_pool",
   "pre_run_gate",
   "resolve_hold_range",
   "run_generation"
  ],
  "main": [
   "gate_matrix",
   "lint_provenance",
   "load_limits",
   "load_signal_table",
   "material_pool",
   "run_main",
   "sample_structure",
   "selftest",
   "selftest_rank_demand",
   "strip_marks",
   "structure_breakdown",
   "verify_provenance"
  ],
  "lint_provenance": [],
  "gate_matrix": [
   "apply_slots",
   "load_limits",
   "load_signal_table",
   "material_pool",
   "material_ranges",
   "resolve_hold_range",
   "run_trial_guarded",
   "sample_structure",
   "value_slots"
  ],
  "verify_provenance": [
   "load_limits",
   "load_signal_table",
   "resolve_hold_range"
  ]
 },
 "constants": {
  "PARAM_SRC": "_param_src",
  "Q_SRC": "_q_src",
  "NUM_SRC": "_num_src",
  "LIN_SRC": "_lineage_src",
  "ATTACH_CALLS": 0
 },
 "cli_flags": []
}
```

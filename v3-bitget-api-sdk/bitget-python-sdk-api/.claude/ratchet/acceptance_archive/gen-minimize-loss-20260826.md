# acceptance.md — 形を組み立てる方に「減らしたい損失」の指定を足す（要件 R8）

TARGET: scripts/priority_rebuild/engine_tuner_gen.py

<!-- ARC order=67 iter="gen-minimize-loss-20260826" 前提="engine_tuner_gen は合計 net だけを目的にしている" 採否="未" 狙い="出血している決済の理由を名指しして、その損を小さくする形を探せるようにする（要件 R8 の①②が、形を組み立てる方に無い）" 内容="run_trial に focus（その決済理由の玉だけの net 合計）を足し、--minimize 指定時は目的の値と並びと最後の best を focus に切り替える" 方法="恒等（指定なしで直す前と一致）＋番人8件＋わざと壊すメタ確認＋H2/G2 の印の取り直し" -->

---

## 何を作るか（1文）

**`engine_tuner_gen.py`（売買ルールの形を組み立てるプログラム）に、「この決済した理由の損を減らして」と指示できる口を足し、その損の額と合計 net の両方を画面に出す。**

## なぜ作るか

**まこさんの逐語（2026-07-27・要件 R8 の `decided`）**

> 損失最小化というのは、例えばTIMEExitの損失が大きい場合に、その損失額を最小化させるために、指標、閾値、時間足、パラメータ等を調整して損失を最小限にするために調整するという意味

**まこさんの決定（2026-08-26・逐語）**＝「それでOKだけど、対応するタイミングは今が最適なの？」→ 私の答え「M2 の後が私の案」→ **「では今やっておく」**。
**動かす値は入口も出口も両方**（同日・逐語「それでOK」）。

## 何ができたら完成か（8つ・全部 測れる形）

| # | 完成の条件 | どう確かめるか |
|---|---|---|
| 1 | **指定しなければ、直す前と結果が同じ**（恒等） | ★確かめ方を変えました（下の「★恒等の確かめ方を変えた理由」）＝①`git diff` で、案を作る所（`sample_structure` ほか）に差分が1行も無い ②指定が無いとき、新しい値を1つも作らない（番人 T28 で実測）③指定が無いとき、再開の記録に足す欄が1つも増えない（コードの `if minimize` の内側だけ） |
| 2 | 指定すると、**損の額と合計 net の両方**が画面に出る | 合成データの走行で、両方が並んだ行が出る |
| 3 | 審判が知らない決済の理由を渡すと**止まる** | 番人 S2 |
| 4 | 再開の記録と指定が食い違うと**止まる** | 番人 S3 |
| 5 | 損の額の計算が、審判に絞った売買記録を通した値と**一致する** | 番人 S4 |
| 6 | 番人8件が全部 pass し、**わざと壊すと全部 落ちる** | メタ確認 |
| 7 | `--selftest` が**全部 pass** | 走らせて確認 |
| 8 | **探せる範囲が1つも狭まっていない** | 材料・閾値・時間足・パラメータの宣言に差分ゼロ（`git diff` で確認） |

---

### ★恒等の確かめ方を変えた理由（2026-08-26・承認のあとに変えたので、ここに書きます）

**直す前の版を走らせられなくなったためです。**
設計↔実装の検査（`require_design_contract_before_run`）は、**設計書が要求した名前が実装に無いと実行を止めます。**
**直す前の版にはその名前が在りません。**だから「直す前の版で1回 走らせて突き合わせる」ができません（実際に止められました）。

**★これは条件を緩めるための書き換えです。**まこさんが読んで、緩すぎると判断されたら止めてください。
**私の考え**＝①案を作る所に差分が1行も無いことを `git diff` で示す ②指定が無いときに新しい値を1つも作らないことを番人で実測する、の2つで、
「指定が無ければ直す前と同じ」は示せます。**ただし「出力を突き合わせた」わけではありません。**

## やること（6件）

| # | やること | 触る行（実物） |
|---|---|---|
| 1 | `run_trial()` が `minimize` を受け、`focus`（その決済した理由の玉だけの net 合計）と `focus_n`（その玉数）を返す | 2723-2736 |
| 2 | `run_trial_guarded()` が `minimize` を素通しする | 2739-2761 |
| 3 | 呼ぶ所4か所に渡す（第1段・第2段・確認窓の2走） | 3107 ／ 3253 ／ 3298 ／ 3300 |
| 4 | 指定時は、目的の値・第2段へ送る並び・最後の best を `focus` に切り替える | 3229 ／ 3249 ／ 3268 ／ 3295 |
| 5 | `--minimize` の引数と、起動時の表示（何を目標にするか・歯止めが無いときの警告） | 5013 の隣 |
| 6 | **歯止め2つ**＝①審判が知らない名前なら走らせる前に止める ②再開の記録の食い違いに `minimize` を足す | 起動時 ／ 再開の食い違いを見る所 |

**計算式は、すでに動いている `engine_tuner.py`（数字を調整する方）の写しです**（491-495行）。売買記録をその決済した理由で絞り、審判 `judge.score()` にかけて net 合計を出します。**net の計算は審判がします＝この直しは net を1行も計算しません（H13）。**

---

## ① 真因（root cause）

**形を組み立てるプログラムの目的の値が、合計 net の1つしか無いことです。**
だから「時間切れ決済で $500 損している」と分かっても、その損を小さくする形を探せません。
**要件 R8 の①②（減らしたい損失を指定できる・損の額と合計 net の両方が出る）が、このプログラムに実装されていません**（`minimize`・`focus` の語が **0件**・2026-08-26 実測）。

## ② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか）

**★この直し自体は、4つのどれも動かしません。玉を1本も作らないためです。**
**動くのは、この道具を使って次に選ぶ形が変わったときです。**

| 何を動かす道が開くか | どこに効くか |
|---|---|
| 名指しした決済の理由の損を小さくする形を選べる | **敗率 × 平均損失**（その決済の理由の分） |
| 歯止め（件数の下限・利益の下限）はそのまま効く | 建てない形に逃げるのを捨てる |

**★数字の見込みは書きません。**走らせていないためです（恒久の決まり8番＝手で足した数字を書かない）。

## ③ root か symptom か

**root です。**目的の値そのものが1つしか無いことが原因だからです。
**symptom の直し方＝画面に損の額を表示するだけ。**それでは探す向きが変わらないので、採りません。

## ④ ベースアップ（★実際に Read tool で開いた実物だけを書きます）

| 何を開いたか | 何を取ったか |
|---|---|
| `engine_tuner.py` | 損の額の計算式（491-495行）と、指定の引数（531行）と、両方を並べる画面の形（659・666・717行） |
| `score.py` | 審判が知っている決済の理由の一覧（44行・57行＝**27種**） |
| `engine_tuner_gen.py` | 足す場所7か所（2723-2761・3095-3129・3220-3309・5013行） |
| `.claude/ratchet/engine_tuner_requirements.json` | 要件 R8 の逐語と、まこさんの `decided` |

**WebSearch は使っていません。**すでに動いているプログラムの写しなので、外の知識を要しないためです。

## 変更は1レバーか（H16・1ターン1変更）

**はい。1つです**＝「何を目標にして探すか」を切り替えられるようにすること。
**探す範囲・案の作り方・審判・戦略には1バイトも触りません。**

## 過去に破棄した失敗の不再演（H16）

| 過去の失敗 | 再演していないか |
|---|---|
| **L-267**（採点窓で値を選ばない） | 採点窓に触らない。値決め窓のまま |
| **D14**（探す値を点の一覧で限定する） | 探す値の宣言に1バイトも触らない |
| **L-330／L-356**（落とした案を黙って消す） | 落とした案の件数と理由の表示はそのまま残す |
| **違反 #13**（本体を切り落として形式だけ直す） | 画面表示だけで済ませず、目的の値そのものを切り替える |

## ★疑似シミュ由来の固定値ゼロ

**この設計に、私が決めた固定値は1つもありません。**

| 何 | どこから来るか |
|---|---|
| 決済した理由の27種 | **審判 `score.py` の実物から機械で読む**（CC が並べた一覧ではない） |
| 件数の下限 | 既に在る（`e38_logics.json` の 5.0・まこさん確定 2026-08-07） |
| 利益の下限 | 実行時の `--net-floor`（既定は指定なし） |

**閾値・段数・確率の線を1つも入れていません。**疑似シミュ（probe）の数字も1つも使っていません。
**採否は、この道具ではなく審判 `score.py` の数字で決めます。**

## 群2（売買のロジック・審判の照合 18件）

**H1〜H16 と審判整合は、まとめて非該当です**（理由＝触る相手は探索の道具であって、戦略でも審判でもないため）。
**★ただし、次の2つだけは非該当にしません**（探索の経路のファイルなので実際に効きます）。

| # | 制約 | この設計での扱い |
|---|---|---|
| **H2** | 未来のデータを使わない | **新しい材料を1つも作らない。**売買記録が出た**後**に、決済した理由で絞って審判にかけるだけ＝未来参照が入る余地なし。**印は取り直す**（このファイルは H2 の21件に入っている） |
| **H13** | 審判を実験で改造しない | **`score.py` を1バイトも触らない。**損の額は `judge.score()` を呼んで出す＝計算は審判がする |

---

## 自己検査（番人8件・★わざと壊して落ちるかをメタ確認する）

| # | 何を確かめるか | わざと壊す形 |
|---|---|---|
| S1 | **恒等**＝指定しなければ直す前と結果が同じ | 既定値を変えると落ちる |
| S2 | 審判が知らない決済の理由を渡すと止まる | 検査を外すと通ってしまう |
| S3 | 再開の記録と指定が食い違うと止まる | 食い違いの検査から名前を外すと通る |
| S4 | 損の額が、審判に絞った売買記録の値と一致する | 絞る条件を変えると合わない |
| S5 | 指定した理由が1本も出なければ警告が出る | 警告を消すと出ない |
| S6 | 指定時、第2段の目的が損の額を返す | 合計 net を返すようにすると落ちる |
| S7 | 指定時、最後の best が損の額で選ばれる | 合計 net で選ぶと落ちる |
| S8 | 探せる範囲が1つも狭まっていない | 材料の一覧を1件 減らすと落ちる |

**★メタ確認**＝8件それぞれについて、わざと壊した版で番人が落ちることを実際に走らせて確かめます（形だけ通す検査を作らないため）。

---

## DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
  "self_check_calls": ["_focus_net", "assert_known_exit_reason", "focus_n", "--minimize"],
  "must_combine": {}
}
```

**★実装が終わったら `verify_design_contract.py --write` で書き出し直します**（手書きの一覧を残さないため・恒久の決まり §0-2 の3番）。

---

## 走らせるもの・時間の見込み

| 何を走らせるか | 見込み | 過去の実測（記録からの逐語） |
|---|---|---|
| `engine_tuner_gen.py --selftest` | **★走らせる前に記録から探します**（恒久の決まり62番） | — |
| `leak_causality_diag.py`（H2） | **約5分** | 「H2 は `leak_causality_diag.py`（**実測 4分49秒**）」 |
| `gen_signal_families.py --verify`（G2） | **約30秒** | 「G2 は `gen_signal_families.py --verify`（**実測 29.6秒**）」 |

**★engine_tuner の本走（値を選ぶ走行）は1回もしません。**累積の試行数を1本も増やしません。

## ★入っていないもの（都合の悪い事実も書きます）

1. **「どの損失を減らすべきか」の判断は入れません。**それは診断を見て まこさんが決めます（R10 で「人が読んで設定する」と決定済み）。
2. **複数の決済した理由を同時に指定する形は作りません**（1つだけ）。数字を調整する方と同じ形に揃えます。
3. **数字を調整する方（`engine_tuner.py`）には触りません。**既に在るためです。
4. **この直しで net は増えません。**探し方が増えるだけです。

---

## SPEC（★手書きしない＝verify_design_contract.py --write が実物のコードから書き出したもの・2026-08-26）

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
  "load_scene_rules": [],
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
   "load_scene_rules",
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
  "selftest": [
   "Journal",
   "apply_slots",
   "assert_known_exit_reason",
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
   "strat_gate",
   "strip_marks",
   "structure_breakdown",
   "synth_df",
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
   "material_pool",
   "run_main",
   "sample_structure",
   "selftest",
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

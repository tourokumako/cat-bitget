<!-- ARC iter="demand-attach-shared-path-20260907" -->

# 設計書｜需給の列を、実行器の共通の道でも載せる（2026-09-07・next_step §6 の139番）

TARGET: scripts/priority_rebuild/engine_tuner_exec.py, scripts/priority_rebuild/engine_tuner_gen.py, .claude/breaks/b36_demand_attach_gone.sh

MODEL: .claude/breaks/b35_gate_branch_gone.sh, .claude/breaks/lib.sh

★新しく作るファイルの宣言（NEW_FILE）の行は外しました＝壊すプログラム `b36_demand_attach_gone.sh` は、1回目の承認のあとに作り終えて実在するためです。中身は Read tool で開いて確かめました（48行）。

## 0. 承認の往復について

**往復：2回目／内訳＝1回目で書く権利をもらい、2回目で機械が測ります。**

**なぜ1回で終わらなかったか**＝壊すプログラム `b36_demand_attach_gone.sh` は、1回目の承認の時点では存在しませんでした。承認のプログラムは、承認を打ったその場で壊すプログラムを走らせて終了コードを記録します。**実在しないファイルは走らせられないので、1回目は「未着手」のまま残りました**（記録＝`rc=None`）。

**net に直結するか**＝しません。売買のロジックには1行も触れていません。

## 1. 何を作るか

**需給の列（別枠）を載せる処理を、実行器の共通の道に移しました。**直す前は生成器の本走の道にしかありませんでした。

## 2. なぜ作るか（実測）

**実測（2026-09-07・H2 の印を取り直したときの出力）**＝種を固定した生成の案3本のうち、**2本が突き合わせの対象外**になりました。逐語は「両方 走れない（同じ理由）＝突き合わせ対象外: 走れない（RecipeError: [実行器] 需給の列が実行データに無い: L-S比）」です。**＝H2 の生成の道の見張りが 3本 → 1本 に薄くなりました。**その数字を出したコマンドは `python3 scripts/priority_rebuild/leak_causality_diag.py` です。

**原因**＝需給の列を載せる関数 `_attach_demand` を呼んでいたのは、`engine_tuner_gen.py` の `run_generation` の1か所だけでした。実行器の共通の道 `engine_tuner_exec.attach_recipe_columns` には入っていませんでした。

**共通の道を呼んでいる所は5か所です**（`grep -rn "attach_recipe_columns"` で数えた実測）。`engine_tuner_exec.py` の2か所、`leak_causality_diag.py` の2か所、`tuner_adapters/e37.py` の1か所です。**共通の道に置けば、5か所ぜんぶが同じように動きます。**

**なぜ私が作った穴か**＝2026-09-06 の cp24 の直し（需給の部品を足す）で、本走が落ちないことだけを確かめ、**本走の外の道を1つも確かめませんでした。**

## 2-2. ★実装の途中で見つかった、もう1つの不具合

**移した処理は、移す前から動いていませんでした。**

`observe_diag.load_demand` に渡していたのは `pd.to_datetime(df["ts"])` で、これは **Series（行番号を持つ）** です。`load_demand` の中は、まず `s.reindex(bars_index)` で行の並びを時刻に張り替え、そのあと `s[bars_index > 元データの終端] = NaN` をします。渡したものが Series だと、この2つの並びが合わず、pandas が `Unalignable boolean Series provided as indexer` で落ちます。

**この検査を足して初めて分かりました。**それまで、本走の外から需給の列を作らせたことが1度も無かったためです。その数字を出したコマンドは `python3 scripts/priority_rebuild/engine_tuner_exec.py --selftest` です。

**直し**＝渡すものを `pd.DatetimeIndex(pd.to_datetime(df["ts"]))` にしました。**計算の式は1つも変えていません。**

## 3. 深掘り4点

**① 真因**＝列を用意する処理を、**呼ぶ側（生成器の本走）に置いた**ことです。列が要るかどうかを知っているのは案（レシピ）で、案を受け取るのは実行器です。**置き場所が1段 上でした。**

**② 期待値分解**＝この工事は売買のロジックに1行も触れません。勝率・平均利益・敗率・平均損失は動きません（net への影響はゼロ）。動くのは、需給の条件を持つ案を走らせられる道具の数です。

**③ root か symptom か**＝root です。「H2 だけ通す」のではなく、**共通の道に置いて、呼ぶ側 5か所ぜんぶに効かせます。**

**④ ベースアップ**＝外の検索は使いません。根拠は H2 の走行の出力と、実物のコード（`engine_tuner_exec.py` の `_col_array` の需給の枝・`attach_recipe_columns`・`legacy_cols_in`／`engine_tuner_gen.py` の `run_generation`）です。

## 4. やったこと（4つ）

| # | 触るファイル | 何をしたか |
|---|---|---|
| **A** | `engine_tuner_exec.py` | **`demand_cols_in(recipe)` を新しく作った**＝案の中で使っている需給の列の名前を、入れ子の中まで全部 拾う。手本＝同じファイルの `legacy_cols_in`。形をそろえた |
| **B** | `engine_tuner_exec.py` | **`attach_demand_columns(df, names)` を新しく作った**＝需給の列を走らせるデータに載せる。中身は生成器から そのまま移した（式は書き写さず `observe_diag.load_demand` を呼ぶ・既に在る列は触らない）。あわせて §2-2 の不具合を直した |
| **C** | `engine_tuner_exec.py` | **`attach_recipe_columns` が、その案が需給の列を使うときだけ B を呼ぶ。**使わない案では元データを読みに行かない（速さを変えない） |
| **D** | `engine_tuner_gen.py` | **`_attach_demand` を消して、`ex.attach_demand_columns` を呼ぶ形にした。**生成器の本走は、分位の解決表を作る前に候補になりうる需給の列が全部 要るので、呼ぶこと自体は残した（型の表の `demand_ok` を渡す）。**同じ処理を2か所に置いていません** |

**★あわせて足したテスト**＝実行器の自己検査（`selftest`）に、番人139番として4つの枝を足しました。①名前を拾う ②需給を使う案には列が付く ③その列に値が入る ④需給を使わない案には付けない、です。

## 5. ★疑似シミュ由来の固定値ゼロ宣言

疑似シミュ（probe）から出た数字を、1つも固定値にしていません。

- **(a)** この工事で新しく決める数字は 0個です。閾値・期間・パラメータを1つも決めていません。
- **(b)** probe の数値を設計の固定値に焼いていません。probe を1本も走らせていません。
- **(c)** 採否は probe でなく、自己検査の終了コードと、壊すプログラムの終了コードで決めます。

## 6. 変更の単位（H16）

1レバーです。「**需給の列を用意する処理を、呼ぶ側から共通の道へ移す**」1つです。A・B・C・D は、その1つを成り立たせる部品です。

**過去に破棄した失敗の再演ではありません。**むしろ 2026-09-06 の直しが本走だけで閉じていたのを、共通の道へ広げるものです。

## 7. 塞げないもの

| # | 問い | 塞げないこと |
|---|---|---|
| **監査 Q5 の1** | 共通の道に置けば、全部の道具で需給が使えるか | **共通の道を通る5か所だけです。**共通の道を通らずに自分で列を組み立てる道具が将来 現れたら、そこは別に直します |
| **監査 Q5 の2** | 需給の元データが無い期間 | **`observe_diag.load_demand` が返す被覆に任せます。**被覆が足りない期間の扱いは、この工事では変えません |
| **監査 Q5 の3** | 自己検査の枝が「本物か」 | **壊すプログラム b36 が測ります。**ただし b36 が壊すのは C の呼び出し1か所だけです。A・B・D を壊しても落ちるかは、この1本では測れません |
| **監査 Q5 の4** | この道具自身を書き換えられたら | **無効にできます**（承認ゲートの対象なので承認は要ります） |
| **監査 Q5 の5** | H2 の生成の案が3本とも走るようになったか | **完成の条件では測りません。**その走行は約13分かかり、承認のときの打ち切り（120秒）を超えるためです。直したあと私が走らせて worklog に実測を書きますが、**「直った」の判定はしません**（恒久の決まり64番）。判定は監査に出します |

## 8. §4.6 ハード制約の照合

まとめて非該当です（理由＝売買のロジックにも審判にも触りません）。触るのは、案を走らせる前に列を用意する道と、実行器の自己検査です。売買記録・net の計算・約定モデル・期間分割のどれにも関わりません。

**H16（1変更・過去失敗の不再演）だけ該当します**＝上の §6 に書きました。

**H2（未来参照なし）について1行**＝載せる列は `observe_diag.load_demand` が作るもので、この工事では作り方を1文字も変えていません。載せる場所と、渡す入れ物の型が変わるだけです。

**H8（期間の手打ち禁止）について1行**＝自己検査で使う時刻は `periods.SEARCH_START`（値決め窓の先頭）から作ります。日付を手で書いていません。

## 9. 完成の条件

**★状態は「未着手」です。**「済」にするのは機械です（恒久の決まり64番）。

**★コマンドに実行器の自己検査を選んだ理由**＝この工事のあとで測ると 8.7秒で終わり、終了コードは 0 です（コマンド＝`python3 scripts/priority_rebuild/engine_tuner_exec.py --selftest`）。承認のときの打ち切り（120秒）に収まります。**b35 が 6分23秒の走行を測って打ち切りに掛かり、壊した実物が戻らなかった事故を繰り返さないためです。**

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 需給の列を使う案が、実行器の共通の道を通ると走る（番人139番の4つの枝が1つも ❌ を出さない） | `python3 scripts/priority_rebuild/engine_tuner_exec.py --selftest` | 実経路 | 共通の道から需給を載せる呼び出しを消すと、自己検査が落ちる | `b36_demand_attach_gone.sh` | 終了コードが0でない | **未着手**（この工事の前は、共通の道に需給を載せる処理が無い） |

<!-- ACCEPT_TABLE_END -->

## 10. DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/engine_tuner_exec.py",
  "impl_functions": {
    "scripts/priority_rebuild/engine_tuner_exec.py": [
      "demand_cols_in",
      "attach_demand_columns",
      "attach_recipe_columns",
      "selftest"
    ],
    "scripts/priority_rebuild/engine_tuner_gen.py": [
      "run_generation"
    ]
  },
  "self_check_calls": ["attach_demand_columns", "demand_cols_in", "attach_recipe_columns"],
  "must_use": {
    "attach_recipe_columns": ["attach_demand_columns"],
    "run_generation": ["attach_demand_columns"]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は値の一覧を持たない（列を用意する場所を移すだけ）",
  "generated_from": {
    "impl_functions": "実装のあとに、直した行がどの関数に入っているかを引いて書いた。実行器の4つ（新しく作った2つ＋直した2つ）と、生成器の1つ（呼び出しを差し替えた run_generation）で、実際に触った関数と一致している"
  }
}
```

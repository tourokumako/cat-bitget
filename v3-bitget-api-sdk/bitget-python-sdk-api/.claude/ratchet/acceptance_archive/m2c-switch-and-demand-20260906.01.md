<!-- ARC iter="m2c-switch-and-demand-20260906" -->

# 設計書｜M2-C を満たす＝オン・オフを別枠にも効かせ、足した部品を engine_tuner が実際に使えるようにする（2026-09-06）

TARGET: scripts/priority_rebuild/engine_tuner_gen.py, scripts/priority_rebuild/engine_tuner_exec.py, scripts/priority_rebuild/gen_indicator_switch.py, scripts/priority_rebuild/gen_materials.py, .claude/breaks/b33_extra_switch_off.sh, .claude/breaks/b34_identity_name_missing.sh

NEW_FILE: .claude/breaks/b33_extra_switch_off.sh, .claude/breaks/b34_identity_name_missing.sh

MODEL: .claude/breaks/b27_skipped_not_counted.sh, .claude/breaks/lib.sh

## 1. 何を作るか

**M2-C の見出し2つを、engine_tuner が実際に満たす状態にします。**

> M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す

**①一律の切り替え**＝オン・オフの印を、指標だけでなく**別枠3種（レンジ幾何・需給・時間帯）にも効かせます。**
**②部品を足す**＝足した部品（需給3件・MMI 4件）が、**engine_tuner の案に実際に出てくる状態にします。**

## 2. なぜ作るか（監査 cp24 の実測・NO-GO）

| 見出し | 監査の実測 | 何が足りないか |
|---|---|---|
| ①一律の切り替え | オン・オフが効いているのは `family`（指標）だけ | レンジ幾何の判定関数の呼び出しが 0件／需給は生成器で 0件／時間帯は欄も判定関数も無い |
| ②部品を足す | engine_tuner が使えるようになった部品は 0件 | 部品を足しただけで、案に1回も出てこない |

**②の証拠は私が出しました**＝直す前と後で結果が同じか確かめる走行の md5 が一致しました（S2 `7b01f51b…`／L1 `96a9102e…`／S1 `18b3d31a…`）。**＝動きが1バーも変わっていません。**

## 3. 深掘り4点

**① 真因**＝オン・オフの判定と、材料を引く処理が、指標（`family`）だけを見る形でできています。別枠3種は「型の表に在るか」しか見ておらず、印を見ていません。需給は引く枝そのものが在りません。

**② 期待値分解**＝この工事は売買のコードを1行も触りません。勝率・平均利益・敗率・平均損失は、この工事だけでは動きません（net への影響はゼロ）。動くのは「engine_tuner が探せる候補の中身」です。net が動くのは、この後に探索を走らせたときです。

**③ root か symptom か**＝root です。「需給の枝を1本 足す」だけでなく、別枠の引き方そのものを、承認済みの型の表が宣言している形に合わせます。

**④ ベースアップ**＝外の検索は使いません。根拠は全部 このプロジェクトの中の正本です。①型の表 `signal_families.json` の `roles.<役割>.lineages` と `extra_parts` ②知識の正本 `range_scalping_kb.md` §6.7（需給の使い方の実測）③材料の定義表 `indicator_reference_diag.py`:4478 の `LINEAGE_KINDS`（8系統）。

## 4. やること（8つ）

| # | 触るファイル | 何をするか |
|---|---|---|
| **A-1** | `engine_tuner_exec.py` | `load_indicator_switch` に `_time_set`（時間帯の印）を足す |
| **A-2** | `engine_tuner_exec.py` | `time_enabled(name)` を新設（`geo_enabled` と同じ形） |
| **A-3** | `gen_indicator_switch.py` | 印に `time_on` の欄を新設。中身＝`時刻` と `曜日`（まこさん決定 2026-09-06・逐語「3は時刻と曜日を入れる」）。型の表の `extra_parts.time.parts` と一致 |
| **A-4** | `engine_tuner_gen.py` | 案の審査（`geo`／`demand`／`time` の枝）で、型の表に加えて判定関数も見る |
| **B** | `engine_tuner_gen.py` | 材料を引く処理を、役割ごとに使える系統を表から引き、系統を選んでから その系統の部品を選ぶ形にする。別枠3種は判定関数がオフなら候補から外す。CC が書いた割合の数字（`0.5`・`0.10`）を消す |
| **C** | `gen_indicator_switch.py` | オン・オフの対象を、機械で数えられる形にする＝対象4系統（指標・レンジ幾何・需給・時間帯）と対象外3つ（玉の状態・昔からの列・`tf`／`param`）の合計が、実物の分岐の数と一致するかを自己検査で見る |
| **D** | `gen_indicator_switch.py` | `source_identity` が、`legacy_col` を持つ材料の `family` ラベルを拾わないようにする。`counts.源3_恒等レシピ` を「オンに入った数」にする。定義表に無い名前が混じったら落ちる検査を1本 足す |
| **E** | `engine_tuner_gen.py` | 再開の食い違いの検査（T33-e）を、印の指紋だけ変えた `meta` で `Journal` を作り、`SystemExit` が出ることを確かめる形にする |
| **H** | `gen_materials.py` | 「参照表に在るのに材料カタログに列が無い」の数から、別枠（`extra_parts`）で使えるようになったものを除く |

**★別に走らせるもの（コードを触らない・承認不要）**＝成績表の作り直し `observe_diag.py --rank-regime`。時間の見込み＝1時間〜2時間15分（根拠の逐語＝`session_worklog_20260823.md`:262「1回目＝56分19秒」／`session_worklog_20260822.md`:1555「約2時間15分」）。

**★やることリストに足す文（M2-C-4 の確かめ方の4つ目・監査 §6-4 の文をそのまま）**

> **④ 足した部品が、engine_tuner の案に実際に出てくる。**測り方＝`engine_tuner_gen.py` を `--purpose check` で走らせて案を N 本 作り、足した部品名（MMI200 ほか・需給3件）が条件に1回以上 出ることを機械で数える。0件なら未達。

## 5. ★疑似シミュ由来の固定値ゼロ宣言

疑似シミュ（probe）から出た数字を、1つも固定値にしていません。

- **(a)** この工事で新しく決める数字は 0個です。閾値・期間・パラメータを1つも決めていません。
- **(b)** probe の数値を設計の固定値に焼いていません。probe を1本も走らせていません。
- **(c)** 採否は probe でなく、自己検査の件数・壊すプログラムの終了コード・案に出た回数で決めます。
- **(d)** むしろ、出どころの記録が無い数字を2つ 消します（`0.5`＝レンジ幾何を2回に1回・`0.10`＝時間帯を10回に1回）。実測＝`git log -S` で、どちらも commit `863935a`（乱数のくじ引きを作った回）に入り、決定の記録がありません。

## 6. 変更の単位（H16）

1レバーです。「材料の候補の作り方を、承認済みの型の表の宣言どおりにする」1つです。A〜E・H は、その1つを効かせるための同じ場所の工事です。

過去に破棄した失敗の再演ではありません。むしろ、違反の記録 #14／#24（乱数のくじ引き）の一部である「CC が書いた割合の数字」を2つ 減らします。

## 7. 塞げないもの

| # | 問い | 塞げないこと |
|---|---|---|
| **監査 Q5 の1** | 入口・出口の条件の束を法則で組むか | この工事では直りません。直るのは「どの材料を候補にするか」までです。条件どうしを法則でつなぐのは M2-E 以降です（D14 は未修正のまま） |
| **監査 Q5 の2** | 需給が本当に効くか | 測りません。知識の正本 §6.7 に「同じ需給フィルタが SHORT 側でも対称に効くかは未検証」と書いてあります。効くかどうかは net が決めます |
| **監査 Q5 の3** | 系統を選んでから部品を選ぶ形が最良か | 私が決めた構造です。表は「どの系統を使えるか」を宣言していますが、選ぶ重みは宣言していません。別の形（部品を全部 並べて一様に選ぶ）にすると、需給は3件しかないので ほとんど選ばれません |
| **監査 Q5 の4** | 成績表に需給を載せるか | 載せません。成績表を作る本体が需給を測らないためです。監査 §6-2 の3 とは道が違います |
| **監査 Q5 の5** | 印を手で作られたら | 見抜けません。印の偽造はプログラムでは分かりません（H2・G2 と同じ限界） |

## 8. §4.6 ハード制約の照合

まとめて非該当です（理由＝売買のロジックにも審判にも触りません）。触るのは、案を作るときの材料の候補と、印の作り方と、自己検査です。売買記録・net の計算・約定モデル・期間分割のどれにも関わりません。

**H16（1変更・過去失敗の不再演）だけ該当します**＝上の §6 に書きました。

## 9. 完成の条件

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 別枠3種の判定関数が、生成器から呼ばれる（0件でない） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | 実経路 | 印の別枠の欄を空にして、案に別枠が出ないことを見る | `b33_extra_switch_off.sh` | 終了コードが0でない | **未着手**（いま 0件） |
| 2 | 別枠3種を試すテストの枝が在る（0件でない） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | 実経路 | 同上 | `b33_extra_switch_off.sh` | 枝の数が0でない | **未着手**（いま 0件） |
| 3 | 需給が案に出る（0回でない） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --purpose check` | 実経路 | 印の `demand_on` を空にすると0回になる | `b33_extra_switch_off.sh` | 回数が0でない | **未着手**（いま 0回） |
| 4 | MMI が場面の判定で引ける（0本でない） | `python3 scripts/priority_rebuild/observe_diag.py --rank-regime <5分足CSV>` | 実経路 | 印の MMI をオフにすると順位から消える | `b33_extra_switch_off.sh` | 行数が0でない | **未着手**（いま 0本） |
| 5 | 材料名の実在テストが在り、源3 の数が実物と合う | `python3 scripts/priority_rebuild/gen_indicator_switch.py --write` | 実経路 | 定義表に無い名前を印に混ぜる | `b34_identity_name_missing.sh` | 終了コードが0でない | **未着手**（いま 8・実態 6） |
| 6 | オン・オフの対象の件数が、実装の分岐の数と一致する | `python3 scripts/priority_rebuild/gen_indicator_switch.py --selftest` | 実経路 | 分岐を1つ増やして件数を合わなくする | `b34_identity_name_missing.sh` | 終了コードが0でない | **未着手** |
| 7 | 再開の食い違いで止まる | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | 実経路 | 止める行を外すと T33-e が ❌ を出さなくなる | `b33_extra_switch_off.sh` | ❌ の件数が変わる | **未着手**（いま 指紋が空でないことしか見ていない） |
| 8 | 既存が壊れていない（3本の md5 が変わらない） | `python3 scripts/priority_rebuild/engine_tuner_exec.py --identity` | 実経路 | 別枠の材料を恒等レシピの経路にも入る形にすると md5 が変わる | `b33_extra_switch_off.sh` | 3本とも一致 | **未着手**（直す前の値は測ってある＝S2 `7b01f51b5a9b29b3c05a7b340c203ba1`／L1 `96a9102ec8a34f94cf01e9e463f6aade`／S1 `18b3d31a5fe71c4a4b5f83cf1771a46c`。**直した後に測り直して、同じ値であることを確かめる**） |
| 9 | 材料の一覧の「これから足す候補」の需給が0件になる | `python3 scripts/priority_rebuild/gen_materials.py --write` | 実経路 | 除く処理を外すと3件に戻る | `b34_identity_name_missing.sh` | 数が0 | **未着手**（いま 3件） |
| 10 | `impl_functions`（触る関数の一覧）は実装の後に確定させる＝実装が終わってから `verify_design_contract.py --write` が実物から書き出す（手書きしない） | `python3 scripts/priority_rebuild/verify_design_contract.py --write .claude/state/acceptance.md` | 実経路 | 凍結に在る関数を実装から消す | `b01_missing_func.sh` | 終了コードが0でない | **未着手** |

<!-- ACCEPT_TABLE_END -->

## 10. DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
  "impl_functions": {},
  "no_impl_functions_reason": "verify_design_contract.py --write で実物から書き出す（手書きしない）",
  "self_check_calls": ["_pick_material", "_lineage_of", "_lineage_candidates", "material_pool"],
  "must_use": {},
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は値の一覧を持たない（引く先は型の表 signal_families.json が正本）",
  "generated_from": {
    "impl_functions": "verify_design_contract.py --write"
  }
}
```

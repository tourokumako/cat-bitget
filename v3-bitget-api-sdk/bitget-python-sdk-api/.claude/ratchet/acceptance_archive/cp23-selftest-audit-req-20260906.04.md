<!-- ARC iter="cp23-selftest-audit-req-20260906" -->

# 設計書｜再々監査 cp23 の X-5 と X-9後半を直す（2026-09-06）

TARGET: scripts/priority_rebuild/gen_materials.py, scripts/priority_rebuild/gen_audit_request.py, .claude/breaks/b27_skipped_not_counted.sh, .claude/breaks/b28_counts_break_dead.sh, .claude/breaks/b29_dirty_verify_stops.sh, .claude/breaks/b30_missing_section.sh

（壊すプログラム4本は 2026-09-06 に作りました。手本＝`.claude/breaks/b01_missing_func.sh` と `.claude/breaks/lib.sh`）

## 1. 何を作るか（2つ）

**（1）X-5＝飛ばした番人を、合否行に出す。**いま `python3 scripts/priority_rebuild/gen_materials.py --selftest` は、当てる相手が1件も無い番人（S5 ほか）を画面に出すだけで、合否の数に入れていません。**＝「✅ 全部 pass」が「番人を全部 当てた」を意味していません。**

**（2）X-9後半＝監査の依頼書が指す節が、本当に在るかを機械で確かめる。**cp23 の依頼書は `session_worklog_20260904.md` の §38 を指しましたが、**その節は存在しませんでした。**

## 2. なぜ作るか

**（1）の理由**＝監査 cp23 の X-5 の逐語＝「飛ばした番人が `ng` に積まれないので、『✅ 全部 pass』が『番人を全部 当てた』を意味しなくなった。同じファイルの :988・:2411 が禁じている状態」。

**（2）の理由**＝監査 cp23 の X-9 の逐語＝「依頼書 §1 の3が『§36 と §38 ← CC が出した実測』と指示しているが、**§38 は存在しない**」。**＝申告を突き合わせる相手が無い状態で監査に出しました。**

## 3. 深掘り4点

**① 真因**＝番人の合否を数える所（`ng`）と、番人を飛ばす所（`print` だけ）が別々に書かれていて、飛ばした数がどこにも集まっていませんでした。依頼書の側は、指した節が在るかを一度も確かめていませんでした。

**② 期待値分解**＝この工事は売買のコードを1行も触りません。**勝率・平均利益・敗率・平均損失のどれも動きません（net への影響はゼロ）。**動くのは「番人が当たっていない件数が画面に出るか」だけです。

**③ root か symptom か**＝root です。X-5 は「合否の数え方」そのもの、X-9 は「依頼書を作る手順」そのものを直します。飛ばした番人を1件ずつ直す（symptom）のではありません。

**④ ベースアップ**＝外の資料は使いません。直す中身は、監査 cp23 の X-5・X-9 の逐語と、`gen_materials.py` 自身の :988・:2411 の決まりから来ています。

## 4. やること（4つ）

| # | 触るファイル | 何をするか |
|---|---|---|
| **4-1** | `gen_materials.py`（`selftest`） | 飛ばした番人の名前を集め、合否行を `✅ 全部 pass（該当なし N件: S5）` の形にする（確かめ方＝`python3 scripts/priority_rebuild/gen_materials.py --selftest`） |
| **4-2** | `gen_materials.py`（`selftest`） | COUNTS のブロックに、B1・B2 と同じ壊し方を足す |
| **4-3** | `gen_materials.py`（`selftest`） | T6・B1 の冒頭で `verify()` が空でなければ、番人を実行せず不合格に数える |
| **4-4** | `gen_audit_request.py` | 依頼書が指した節（`§NN`）が、指した先のファイルに実在するかを確かめ、無ければ依頼書を書かない |

## 5. ★疑似シミュ由来の固定値ゼロ宣言

**疑似シミュ（probe）から出た数字を、1つも固定値にしていません。**

- **(a)** この工事で出る数字は、番人の件数（プログラムが数えた結果）だけです。閾値・期間・パラメータを1つも決めていません。
- **(b)** probe の数値（θ・段数・AUC ほか）を設計の固定値に焼いていません。probe を1本も走らせていません。
- **(c)** 採否は probe でなく、`--selftest` と `--verify` の終了コードで決めます。

## 6. 変更の単位（H16）

**1レバーです。**「番人の合否の数え方」1つを直します。4-4（依頼書の節の実在確認）は同じ型の直し（数えていないものを数える）で、触るファイルが別なので混ざりません。

**過去に破棄した失敗の再演ではありません。**cp22 の N-4・N-5 で番人を足した続きです。

## 7. 塞げないもの

| # | 監査の問い | 塞げないこと |
|---|---|---|
| **Q5 の1** | 番人の中身が本物か | **番人が「当てられる相手」を選ぶ規則は、私が書いています。**相手の選び方が狭ければ、飛ばした数は出ても、守りは薄いままです |
| **Q5 の2** | 「該当なし」の件数が正しいか | **飛ばした番人を集め忘れれば、その1件は見えません。**集め忘れを機械では見つけられません |
| **Q5 の3** | 依頼書の節の実在確認の範囲 | **確かめるのは「その節が在るか」だけです。**節の中身が申告と合っているかは見ません |
| **Q5 の4** | 節の書き方のゆれ | **`## §43` の形だけを探します。**別の書き方（`### 43-1` など）で指すと、見つけられません |
| **Q5 の5** | この設計書の外 | **X-7（承認の機械が列数を数える）は、この設計書に入れていません。**`approve_impl.sh` は hook なので、承認なしで直せるためです |
| **Q5 の6** | 壊すプログラムが本当に効いているか | **壊し方は私が選んでいます。**別の壊し方（たとえば `skipped` の中身を空文字にする）では、この4本は落ちません。**＝「この4通りの壊し方では落ちる」ことしか言えません** |

## 8. §4.6 ハード制約の照合

**まとめて非該当です（理由＝売買のロジックにも審判にも触りません）。**触るのは、材料の文書を作るプログラムの自己テストと、監査の依頼書を作るプログラムだけです。売買記録・net の計算・約定モデル・期間分割のどれにも関わりません。

**H16（1変更・過去失敗の不再演）だけ該当します**＝上の §6 に書きました。

## 9. 完成の条件

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | `--selftest` の合否行に「該当なし N件」が出る | `python3 scripts/priority_rebuild/gen_materials.py --selftest` | 実経路 | `skipped` に積む行を消すと、合否行から「該当なし」が消える | `b27_skipped_not_counted.sh` | 終了コードが0でない | **未着手**（実装の実測＝合否行に「全部 pass（該当なし 1件: S5）」が出た。壊し方は承認のときに機械が走らせる） |
| 2 | COUNTS のブロックをわざと書き換えると `--verify` が ❌ を出し、戻すと出ない | `python3 scripts/priority_rebuild/gen_materials.py --selftest` | 実経路 | COUNTS の食い違いを見る判定を殺すと、B3 が落ちる | `b28_counts_break_dead.sh` | 終了コードが0でない | **未着手**（実装の実測＝B3・B4 とも ❌ 0件） |
| 3 | 素の状態で `--verify` が鳴っていれば、T6・B1 は実行せず不合格に数える | `python3 scripts/priority_rebuild/gen_materials.py --selftest` | 実経路 | `materials.md` に1行 足してから `--selftest` を打つ | `b29_dirty_verify_stops.sh` | 終了コードが0でない | **未着手**（実装の実測＝T6・B1 とも ❌ 0件） |
| 4 | 依頼書が指す節が無いとき、`gen_audit_request.py` が依頼書を書かない | `python3 scripts/priority_rebuild/gen_audit_request.py --selftest` | 実経路 | 節の実在確認を空返しにすると、Q11 が落ちる | `b30_missing_section.sh` | 終了コードが0でない | **未着手**（実装の実測＝Q11 は ❌ 0件） |
| 5 | 上の4つを直した後も、`--verify` が ✅ 一致のまま | `python3 scripts/priority_rebuild/gen_materials.py --verify` | 実経路 | `materials.md` に1行 足す | `b29_dirty_verify_stops.sh` | 終了コードが0でない | **未着手**（実装の実測＝「一致（手で書き換えられていない）」が出た） |
| 6 | `impl_functions`（触る関数の一覧）は**実装の後に確定させる**＝実装が終わってから `verify_design_contract.py --write` が実物から書き出す（手書きしない） | `python3 scripts/priority_rebuild/verify_design_contract.py --write .claude/state/acceptance.md` | 実経路 | 凍結に在る関数を実装から消す | `b01_missing_func.sh` | 終了コードが0でない | **未着手**（実装の実測＝関数 25件／定数 20件を書き出した） |

<!-- ACCEPT_TABLE_END -->

## 10. DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/gen_materials.py",
  "impl_functions": {},
  "no_impl_functions_reason": "verify_design_contract.py --write で実物から書き出す（手書きしない）",
  "self_check_calls": ["selftest", "verify"],
  "must_use": {},
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は番人の合否の数え方と依頼書の節の確認だけで、値の一覧を持たない",
  "generated_from": {
    "impl_functions": "verify_design_contract.py --write"
  }
}
```

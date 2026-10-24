# 設計書｜生成器の自己テストの静的検査 T25 を通す（見本の関数に「使わない」指標の分岐を足す）

TARGET: scripts/priority_rebuild/engine_tuner_gen.py

REQUIREMENTS: 直接 当たる要件の番号はありません（M2-C-2 の承認済みの設計書＝acceptance_archive の indicator-switch-20260902 の検収の残り）。効く先＝R17（CC が要件どおりに作っているかを、プログラムが確かめられるようにする）の一部＝生成器の自己テストが「落ちたまま」だと、次の工程で自己テストを完成の条件に使えない。

**承認の状態＝未承認。実装はまだ1行も入れていません。**

<!-- ARC order=1 iter="t25-fixture-off-20260904" 前提="M2-C-2 の印を作り直したあと、生成器の自己テストで静的検査 T25 が落ちた（82回目・worklog 20260904 §9.2）" 採否="未定" 狙い="78回目に足した印のテスト T33 が、材料の辞書を直に書いていて静的検査に当たる。見本の関数を通す形に直し、静的検査を通す" 内容="_mat_fixture に off_ok の分岐を足す（1か所）＋ T33 の材料の辞書を _mat_fixture に替える（1か所）＋ T33 に6つ目 (f)＝「使う」指標に off_ok を渡すと止まる恒久テストを足す（1か所・まこさんの条件 2026-09-04）" 方法="--lint-provenance が合計 0件・--selftest の T33 が (a)〜(f) の6つとも pass・恒等3本の md5 不変・G2 → H2 の印" -->

**★2026-09-04 の再提出（まこさんの条件・逐語「§5 の 3 を恒久テストにする」「T33 の6つ目（T33-f）として足し、以後 --selftest で毎回走る形にすること」「§6 の完成の条件 4 を「部品」から「実経路」に変えること」）**＝§3.3・§5 の3・§6 の4 を直した。**理由（まこさんの逐語）**＝「この変更に対して verify_design_contract の突き合わせは監視力を持たない（SPEC は公開関数だけが対象で _mat_fixture は対象外）。must_use の indicator_enabled も実装後に足す申告のみ。つまり off_ok の fail-closed を機械で守るものが現状ゼロになる。T33-f を恒久で置けば、そこが唯一かつ十分な番人になる」。

---

## 0｜まこさんの決定（逐語）

| # | 逐語 | いつ | この設計のどこに効くか |
|---|---|---|---|
| 1 | 「直すべきなら直せば？」 | 2026-09-04 | この設計を書く根拠（生成器の自己テストの ❌ を直す） |
| 2 | 「書いてよい」 | 2026-09-04 | 設計書を書く許可 |
| 3 | 「とにかく、不具合はすべて直すように」 | 2026-08-21 | 恒久の決まり59番＝「いま実害が無い」を理由に置かない |

**★私が まこさんに言った「テストの1行」は誤りでした。**見本の関数 `_mat_fixture` は「使わない」指標の見本を作れない（範囲の表に無い指標は作れない作り）ので、**直す場所は3か所**です（§3.1・§3.2・§3.3＝T33-f はまこさんの条件で足した）。

---

## 1｜いまの状態（実測・2026-09-04 に私が数えた）

| 何を | 実測 | 数え方 |
|---|---|---|
| `engine_tuner_gen.py --selftest` | ❌ 4件（T24②・T25・T26・T30） | 82回目に走らせた（21:08〜21:14・worklog §9.1） |
| T25 の中身 | `--lint-provenance` 合計 1件＝「材料の辞書: 1 件 行=[5307]」 | 同じ走行の出力 |
| 5307行の実物 | `"material": [{"family": _off[0], "param": None, "tf": "5m"}]`＝family と tf の両方の鍵を持つ辞書リテラル | Read tool で開いた（5306-5308行） |
| その行を足した commit | `4ac4405`（78回目・2026-09-02）＝T33 のテストと同時に入った | `git show 4ac4405` の差分（115行目） |
| 材料の辞書を書いてよい関数 | `_MAT_CTORS = {"_mat_drawn", "_mat_fixture"}`（5573行） | Read tool で開いた |
| 見本の関数 `_mat_fixture` が「使わない」指標で何を返すか | `SampleError("[見本] 範囲の表に無い指標: …")`（473-474行）＝範囲の表 `material_ranges` が印で「使わない」を除くため（275-276行） | Read tool で開いた |
| T33 の5つ (a)〜(e) | 全部 pass（この T25 は T33 の書き方の問題で、印の仕組みの問題ではない） | 同じ走行の出力 |

**★T24②・T26・T30 はこの設計に入れません**（原因が別＝場面の判定の束を組む関数に法則 R4 の形 streak が無い＝M2-E の工程・next_step §6 の128番）。

---

## 2｜深掘り4点

### ① 真因（root cause）

**T33 のテストが、見本の関数を使わずに材料の辞書を直に書いた**（78回目）。静的検査 `lint_provenance` は「引く関数と見本の関数の外で材料の辞書を書いてはいけない」と決めている（59回目の設計書 v2 の K1）。**78回目は T33 を書いたあとに `--selftest` を走らせていない**（走らせていれば T25 でその場で落ちた）。

**なぜ見本の関数を使わなかったか**＝見本の関数 `_mat_fixture` は、印が「使わない」の指標では作れない（範囲の表に無いため止まる）。T33 の (b)（「使わない」指標を使った案を審査が捨てる）は、まさに「使わない」指標の見本が要る。＝**見本の関数に、その用途の道が無かった。**

### ② 期待値分解

**★この設計は売買のロジックを1行も変えません。**勝率・平均利益・敗率・平均損失は1つも動きません。動くのは「生成器の自己テストが通るか」だけです。

| 何が | 直す前 | 直した後（見込み） |
|---|---|---|
| `--lint-provenance` の合計 | 1件（★不合格） | 0件（合格） |
| `--selftest` の ❌ | 4件 | 3件（T24②・T26・T30＝別の原因・M2-E） |

**★net の数字は書けません**（M2 は売買を1件も回していない）。

### ③ root か symptom か

**root を直します。**

- symptom の直し方＝T33 のその1行を消す（テストを減らす）。**取りません**（印の審査 (b) を確かめるテストが消える＝守りが減る・恒久の決まり59番）。
- symptom の直し方2＝静的検査の免除の一覧 `_MAT_CTORS` に `selftest` を足す。**取りません**（自己テストの中で材料の辞書を自由に書ける道が開く＝K1 が緩む）。
- root＝**見本の関数に「使わない」指標の見本を作る道を足す。**その道は「使わない」指標でしか使えない（「使う」指標では、いままでどおり範囲の中の数字しか作れない）＝守りは減らない。

### ④ ベースアップ（このセッションで Read tool を使って開いたもの）

| 何を確かめたか | 出どころ |
|---|---|
| T25 が指す行と、静的検査の免除の一覧 | scripts/priority_rebuild/engine_tuner_gen.py（5290-5344行・5571-5576行・5579-5626行） |
| 見本の関数の作り | 同（460-499行） |
| 範囲の表が印で「使わない」を除く所 | 同（262-291行） |
| 審査が印で止める順番（印 → 印の鍵 → 範囲の表） | 同（617-653行） |
| 印を読む判定4つ | scripts/priority_rebuild/engine_tuner_exec.py（150-201行） |
| 印を作る道具の源2の展開 | scripts/priority_rebuild/gen_indicator_switch.py（185-215行） |
| ta のクラスと材料の対応 | scripts/priority_rebuild/indicator_reference_diag.py（4195-4219行） |
| いまの印（140種） | v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/indicator_switch.json |
| 元の設計（M2-C-2） | v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/indicator-switch-20260902.md |
| 78回目の記録（印を作り直していない件） | .claude/state/session_worklog_20260902.md（185-215行） |

**★WebSearch は使っていません。**うちの実物を読む話だからです。

---

## 3｜何を作るか（2か所・どちらも `engine_tuner_gen.py`）

### 3.1 見本の関数 `_mat_fixture` に、「使わない」指標の見本の道を足す（466-482行）

```
直す前
    def _mat_fixture(family, param, tf, **kw):
        ranges = material_ranges()
        spec = ranges.get(family)
        if spec is None:
            raise SampleError(f"[見本] 範囲の表に無い指標: {family}")
        ...

直した後
    def _mat_fixture(family, param, tf, off_ok=False, **kw):
        if off_ok:
            # ★「使わない」指標の見本＝印の審査（T33-b）を試すためだけの道。
            #   印が「使う」の指標では作れない（fail-closed）＝範囲の検査を飛ばす道にならない。
            if ex.indicator_enabled(family):
                raise SampleError(f"[見本] {family} は印が「使う」＝off_ok の見本は作れない")
            m = {"family": family, "param": param, "tf": str(tf)}
            m.update(kw)
            return m
        ranges = material_ranges()
        ...（以下 1文字も変えない）
```

- **足す分岐は「印が使わない」のときだけ動く。**「使う」指標に `off_ok=True` を渡すと止まる＝この道で範囲の検査を飛ばすことはできない。
- 印の鍵（PARAM_SRC）は付けない＝T33 が試す「印で止まる」は、審査の**先頭**（641-642行）で止まるため、鍵の有無は結果に関係ない（直す前の辞書も鍵を持っていない＝挙動は同じ）。

### 3.2 T33 の材料の辞書を、見本の関数に替える（5306-5308行）

```
直す前
    _bad33 = {"role": "trigger", "form": "level", "side": "above",
              "material": [{"family": _off[0], "param": None, "tf": "5m"}],
              "value": {"threshold_q": 0.7}}

直した後
    _bad33 = {"role": "trigger", "form": "level", "side": "above",
              "material": [_mat_fixture(_off[0], None, "5m", off_ok=True)],
              "value": {"threshold_q": 0.7}}
```

- 外側の辞書（role・form・side・value）は family と tf を持たないので、静的検査の対象ではない。
- `_mat_fixture` は `_FIXTURE_CTORS`（自己テストの見本だけが呼んでよい関数）に在り、呼ぶ場所は `selftest` の中＝静的検査の⑤（見本の関数を selftest の外で呼ぶ）にも当たらない。

### 3.3 T33 に6つ目 (f) を足す＝「使う」指標に `off_ok=True` を渡すと止まる恒久テスト（5326行の (d) の前・★まこさんの条件 2026-09-04）

```
足す行（T33 の (c) と (d) の間）
            # (f) 「使う」指標に off_ok=True を渡すと止まる＝off_ok が範囲の検査を飛ばす道にならない
            #     ★恒久のテスト（まこさんの条件 2026-09-04）＝この fail-closed を機械で守るのは、ここだけ
            #     （SPEC は下線で始まる _mat_fixture を見ない・must_use は申告）。
            try:
                _mat_fixture(_on[0], None, "5m", off_ok=True)
                t33.append(f"T33-f: 「使う」指標 {_on[0]} に off_ok=True を渡しても止まらない（fail-closed が崩れている）")
            except SampleError as _e33f:
                print(f"  T33-f 実測: SampleError: {_e33f}")
                if "off_ok" not in str(_e33f):
                    t33.append(f"T33-f: 止まったが理由が off_ok ではない: {str(_e33f)[:60]}")

直す行（T33 の説明の印字・5343-5344行）
    直す前  " (d)順位から外れる (e)指紋が記録に入る"
    直した後 " (d)順位から外れる (e)指紋が記録に入る (f)「使う」指標に off_ok は作れない"
```

- **`_on[0]` は印の on の先頭（いまの印では ADX）**＝印を作り直して先頭が変わっても、テストは「使う」指標の先頭を毎回 引く（名前を焼かない）。
- **止まった理由をそのまま印字する**＝標準出力に `SampleError: [見本] ADX は印が「使う」＝off_ok の見本は作れない` が出る（まこさんの求める「実際の標準出力」）。
- 止まらなければ T33-f が ng に入り、`--selftest` が ❌ になる＝以後 毎回 走る。
- **★まこさんの条件（2026-09-04・逐語）**＝「「使う」指標に off_ok=True を渡して SampleError が上がらなかった場合、T33-f が ❌ として --selftest の失敗件数に加算される作りにしてください。印字するだけで pass してしまうと、番人になりません」。**上の足す行がそれ**＝`try` の中で `_mat_fixture(...)` が止まらずに返ってきたら、次の行の `t33.append(...)` が走り、`ng += t33` で失敗件数に加算される。印字（`print`）は止まったときだけ動く。

### 3.4 触らないもの

- 静的検査 `lint_provenance` と免除の一覧（`_MAT_CTORS`・`_MARK_WRITERS`・`_FIXTURE_CTORS`・`_DRAW_CTORS`）＝**1文字も変えない**。
- 本走の経路（`sample_structure`・`assert_provenance`・`material_pool`・`material_ranges`・`_mat_drawn`）＝**1文字も変えない**。
- 印（`indicator_switch.json`）と印を読む判定（`engine_tuner_exec.py`）＝**触らない**。

---

## 4｜★疑似シミュ由来の固定値ゼロ

- **疑似シミュ（probe）を1回も使っていません。**この設計に出てくる数字は全部、実物のファイルの行番号と、自己テストの出力です。
- **閾値・段数・確率の数字を1つも作っていません。**見本の `param` は `None`（直す前と同じ）。
- **採否は score.py の数字で決めます。**ただしこの工程では売買を回さないので、採否の判定は M2-L 以降です。

---

## 5｜わざと壊して止まるか試すテスト

| # | 何を試すか | 期待する結果 |
|---|---|---|
| 1 | `engine_tuner_gen.py --lint-provenance` | 合計 0件（合格） |
| 2 | `engine_tuner_gen.py --selftest` の T33 | (a)〜(e) 5つとも pass のまま（T33-b＝「使わない」指標の案を審査が「印が「使わない」」で捨てる） |
| 3 | **T33-f（恒久・3.3）**＝`--selftest` の中で、「使う」指標の先頭（印の on の先頭＝いまは ADX）を `_mat_fixture(..., off_ok=True)` で作る | `SampleError`（印が「使う」＝off_ok の見本は作れない）で止まり、その文が標準出力に出る＝この道で範囲の検査を飛ばせない。**一時的な行ではなく、以後 毎回 走る** |
| 4 | 直す前の形（材料の辞書を直に書く）を1行 足して `--lint-provenance` | 合計 1件（★不合格）に戻る＝静的検査が生きている |
| 5 | 恒等3本（`--identity`・`--identity-l1`・`--identity-s1`） | md5 が 2026-08-05 以来の基準値と同じ（S2 7b01f51b…／L1 96a9102e…／S1 18b3d31a…） |
| 6 | `engine_tuner_exec.py --selftest` | 全部 pass のまま |
| 7 | **T33-f が本当に番人か（★まこさんの条件 2026-09-04）**＝3.1 の `raise SampleError(...)`（off_ok の中の止める行）を一時的に外して `--selftest` を走らせる | `--selftest` の ❌ が **1件 増える**（T33-f が失敗件数に加算される）。前後の ❌ の件数を報告に貼る。**確認のあと元に戻し、`git diff` で戻ったことを示す** |

**★4 と 7 は、一時的に書いた（外した）行をテストの後に元へ戻します**（設計の外の行を残さない）。**3 は恒久のテスト（T33-f）です。件数は実装のときに「◯/◯ pass」の形で出します。**

---

## 6｜何ができたら完成か

<!-- ACCEPT_TABLE_START -->

**★「経路」＝`実経路`（コマンドで走らせた）か `部品`（関数を直接 呼んだ）。**
**★「壊すプログラム」＝この回は `.claude/breaks/` に新しく足しません（.py の2か所の直しで、既存の20本が承認のたびに走ります）。壊し方は §5 のコマンドで、出力をそのまま貼ります。**

| # | 完成の条件 | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|
| 1 | `--lint-provenance` の合計が 0件 | 実経路 | §5 の4（直す前の形を1行 戻すと 1件 に戻る） | — | — | **未着手** |
| 2 | `--selftest` の ❌ が T24②・T26・T30 の3件だけ（T25 が消える） | 実経路 | §5 の2 | — | — | **未着手** |
| 3 | T33 の (a)〜(e) が5つとも pass のまま | 実経路 | §5 の2 | — | — | **未着手** |
| 4 | **T33-f**＝「使う」指標に `off_ok=True` を渡すと止まり、その `SampleError` の文が `--selftest` の標準出力に出る | **実経路**（`--selftest` の中で毎回 走る） | §5 の3 | — | — | **未着手** |
| 5 | 恒等3本の md5 が基準値と同じ | 実経路 | §5 の5 | — | — | **未着手** |
| 6 | 実行器の自己テストが全部 pass のまま | 実経路 | §5 の6 | — | — | **未着手** |
| 7 | G2 → H2 の印を取り直して pass | 実経路 | 印の指紋が新しくなる | — | — | **未着手** |
| 8 | **T33-f が番人として効く**＝3.1 の止める行を一時的に外すと `--selftest` の ❌ が1件 増え、戻すと元の件数に戻る（★まこさんの条件 2026-09-04） | 実経路 | §5 の7 | — | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

**★私が自分で合格ラインを引いていないこと**＝全部「壊していないか」の確認で、いくつなら合格という数字を私は作っていません。
**★「完成」の判定は私がしません**（恒久の決まり64番・§0-3 の体制）。数字を貼るだけです。

---

## 7｜既存を壊さないこと（副作用）

| 何が | どうなるか |
|---|---|
| 型の表の承認 | **取り直しは起きません**（表を変えないため） |
| 印（`indicator_switch.json`） | **変わりません**（触らない） |
| H2 の印 | **取り直しが要ります**（`engine_tuner_gen.py` は H2 の印の対象22ファイルの中）。走らせ方＝`leak_causality_diag.py`（約5分） |
| G2 の印 | **取り直しが要ります**。順番は G2 → H2（L-565） |
| 恒等3本 | 変わりません（§5 の5で確かめます） |
| いま採用している戦略（E36 ほか） | 触りません |
| `_mat_fixture` を使っている既存の自己テスト（T22 ほか） | `off_ok` の既定値は False＝**既存の呼び出しの挙動は1つも変わりません** |

---

## 8｜照合（群2＝まとめて非該当の1行）

**H1〜H16 と審判整合（群2の18件）は、まとめて非該当です。**理由＝TARGET は戦略でも審判でもない道具（`engine_tuner_gen.py`）で、直すのは自己テストの見本の作り方だけ。売買記録を1本も書かず、`score.py` と `eval_engine.py` に1行も触れないためです。

**★1変更か（H16）**＝1つです。「見本の関数に、使わない指標の見本の道を足す」だけです。T24②・T26・T30 の直し（M2-E）は入れていません。

**★過去に破棄した失敗の再演か**＝当たりません。過去の失敗は「CC が候補を点の一覧で限定した」（D14・決まり42番）ですが、この設計は探す値に触れません。

---

## 9｜★正直に書く｜それでも塞げないもの（限界と、まこさんに知っておいてほしいこと）

**塞げないもの（この設計の後も残る穴・3つ）**

| # | 塞げないもの | なぜ塞げないか | 何が代わりに守るか |
|---|---|---|---|
| A | `off_ok` の道を本走のコードから呼ぶこと（自己テストの外で見本を作る） | 書く瞬間には止まらない（hook は関数の呼び方を見ない） | 静的検査⑤（`_FIXTURE_CTORS` を selftest の外で呼ぶと `--lint-provenance` が数える）＝走らせたときにだけ分かる |
| B | `_mat_fixture` の中身を、後から誰かが書き換えて fail-closed を外すこと | `verify_design_contract` の SPEC は下線で始まる関数を見ない（この設計書 §12 の記述どおり）。`must_use` は申告 | **T33-f だけ**（`--selftest` で毎回 走る・まこさんの逐語「唯一かつ十分な番人」）。T33-f 自身を消されたら守れない |
| C | T33-f が見るのは印の「使う」の**先頭1種**（いまは ADX）だけ | 140種 全部を回すと自己テストが長くなる。1種で fail-closed の分岐そのものは試せる | 分岐は `ex.indicator_enabled(family)` の1行で、指標ごとに分かれていない＝1種で足りる。ただし「印の on が空」のときは試せない（T33 は `_off` が空のとき既に止まる作り） |

**★強制の土台そのものの穴（監査 cp14 の Q5 の5件・cp19 で「閉じない部分」として確定＝`lessons_active.md` の L-586。この設計は1つも塞がない・受け入れ条件ゲートが毎回 書かせる）**

| # | 塞げないもの | この設計での扱い |
|---|---|---|
| D | **照合D が実経路で1度も走っていない**（監査 Q5 の1） | この設計書も `spec_lists` は空（理由は §10 の `no_spec_lists_reason`）＝照合D はこの回も走らない |
| E | **照合の道具と印を、私が書ける場所に置いたまま**（監査 Q5 の2） | 触らない。J-6（外部CI）は まこさん決定で着手しない（L-586） |
| F | **照合A・B の期待値が、実装から作られる**（監査 Q5 の3） | `impl_functions` は実物の全関数の写し＝承認の画面に ⚠️ が出続けるのが正しい状態（まこさんの指定 2026-09-03） |
| G | **語を並べて迂回を塞ぐやり方は、原理的に閉じない**（監査 Q5 の4） | 触らない。この設計は hook を1文字も変えない |
| H | **承認の記録を全部 消したときを測っていない**（監査 Q5 の5） | 測らない（まこさんの一覧の外・cp19 で確定） |

1. **私の説明の誤り**＝チャットで「テストの1行を直す」と言いましたが、3か所です（§0・§3）。
2. **この設計が確かめないこと**＝T24②・T26・T30（場面の判定の束）は直りません。生成器の自己テストは、この設計の後も ❌3件 のままです。それは M2-E の工程で直します（next_step §6 の128番）。
3. **恒等 L1・S1 は、この設計書が承認されるまで走らせられません**（hook `require_design_contract_before_run` が engine_tuner を指す設計書を求めるため）。承認のあと、実装の前に1回、実装の後に1回 走らせます（実装の前の1回＝M2-C-2 の検収の残り）。
4. **`off_ok` の道は自己テスト専用です。**本走のコードから呼ぶと静的検査の⑤（見本の関数を selftest の外で呼ぶ）で止まります。ただし、静的検査を通すかどうかは `--selftest` を走らせたときに分かるもので、書く瞬間には止まりません。

---

## 10｜DESIGN_CONTRACT

**★`impl_functions` は `python3 .claude/tools/gen_impl_functions.py scripts/priority_rebuild/engine_tuner_gen.py` の出力をそのまま貼ったものです（2026-09-04・手打ちしていません）。**触るのはそのうち `_mat_fixture` と `selftest` の2つで、関数を足しも消しもしません。

```json
{
  "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
  "impl_functions": {
    "scripts/priority_rebuild/engine_tuner_gen.py": [
      "<モジュール直下>",
      "Journal.__init__",
      "Journal.get",
      "Journal.put",
      "_allowed_tfs",
      "_as_param_list",
      "_banned_name",
      "_banned_pair",
      "_cc",
      "_check_tf",
      "_const100",
      "_current_num_bounds",
      "_dc1_side",
      "_dc2_q",
      "_exit_indicator_cond",
      "_family_tf_from_col",
      "_flip_loose",
      "_floor_pct",
      "_focus_net",
      "_from_param_list",
      "_gate_recipe",
      "_geo_of",
      "_group_usable",
      "_insufficient_samples",
      "_int_range",
      "_is_identity_recipe",
      "_iv",
      "_iv_from",
      "_kubun_of",
      "_lineage_of",
      "_loose_q",
      "_make_cond",
      "_make_exits",
      "_make_hysteresis",
      "_mat_drawn",
      "_mat_fixture",
      "_mat_pair_drawn",
      "_mat_two_drawn",
      "_mat_with_pre",
      "_nv",
      "_nvd",
      "_nvs",
      "_obj_key",
      "_ordered_like",
      "_pair_materials",
      "_pick_exit_material",
      "_pick_material",
      "_pkey",
      "_pool_families",
      "_pool_families_by_lineage",
      "_q",
      "_q_range",
      "_qspec",
      "_range_has_two",
      "_ranked_material_at",
      "_role_tfs",
      "_scan_direct_validate_calls",
      "_slot_ref",
      "_stage_of",
      "_state_cond",
      "_thr_band_drawn",
      "_thr_drawn",
      "_thr_fixture",
      "_tree_conds",
      "_vr",
      "_walk_dicts",
      "_walk_materials",
      "apply_slots",
      "assert_exit_roles",
      "assert_known_exit_reason",
      "assert_provenance",
      "assert_roles",
      "attach_materials",
      "bh_select",
      "build_qtable",
      "default_regime",
      "draw_int",
      "draw_num",
      "draw_param",
      "draw_q",
      "gate_matrix",
      "hold_bars",
      "int_range_of",
      "ladder_min_frac",
      "lint_provenance",
      "load_exit_table",
      "load_limits",
      "load_material_ranking",
      "load_signal_table",
      "main",
      "material_pool",
      "material_ranges",
      "max_ladder_steps",
      "needed_qkeys",
      "num_in_range",
      "num_range_of",
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
      "recipe_hash",
      "regime_draw_order",
      "reject_code",
      "resolve_hold_range",
      "run_generation",
      "run_main",
      "run_trial",
      "run_trial_guarded",
      "same_fn_family_pairs",
      "sample_regime_build",
      "sample_structure",
      "selftest",
      "strat_gate",
      "strip_marks",
      "structure_breakdown",
      "suggest_slot",
      "synth_df",
      "validate_drawn",
      "value_slots",
      "verify_provenance",
      "write_kakikudashi",
      "zero_trade_gate"
    ]
  },
  "self_check_calls": [
    "_mat_fixture",
    "lint_provenance",
    "indicator_enabled"
  ],
  "must_use": {
    "selftest": ["_mat_fixture"]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "この設計で作るものは、正本の一覧を読む形ではない（自己テストの見本の作り方を直すだけ）。照合D の相手になる正本の配列が存在しない。",
  "generated_from": {
    "impl_functions": "gen_impl_functions.py の出力をそのまま（2026-09-04）。関数を足しも消しもしない",
    "must_use": "selftest が _mat_fixture を使うこと（3.2）。_mat_fixture が indicator_enabled を使うこと（3.1）は、実装の後に must_use へ足す（実装の前は無い名前を要求できないため）",
    "spec_lists": "無し（理由は no_spec_lists_reason）"
  }
}
```

---

## 11｜まこさんにお願いすること

**実装に入ってよいか、の1点です。**承認は `approve_impl.sh` と `approve_design.sh` の両方が要ります（next_step §6 の126番＝承認の仕組みが2つ在る）。

**承認のあとに私がやること（順番）**＝①恒等 L1・S1 を実装の前に走らせて md5 を貼る（M2-C-2 の検収の残り）②3.1 → 3.2 → 3.3 の順に直す ③§5 の1〜6 ④G2 → H2 ⑤記録（worklog・next_step）。**報告は §5 の1〜6 と G2 → H2 を終えてから1回**（まこさん指示 2026-09-04「中間報告は不要」）＝「◯/◯ pass」・恒等3本の md5・T33-f の標準出力を、そのまま貼る。

---

## 12｜SPEC（★`verify_design_contract.py --write acceptance.md --dry-run` が実物から書き出したもの・2026-09-04・手で直していない）

**★この設計は公開する関数を足しも消しもしないので、実装の後も この SPEC と実物の突き合わせは 0件 のままの見込みです**（触る `_mat_fixture` は下線で始まる関数＝SPEC の対象外・`selftest` が呼ぶ公開の関数は変わらない）。

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

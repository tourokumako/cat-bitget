# acceptance.md — M2-4-2〜M2-4-3＝場面ごとの決まり7件をプログラムの強制にする（2026-08-22・52回目）

TARGET: scripts/priority_rebuild/engine_tuner_exec.py

```json DESIGN_CONTRACT
{"impl_file": "scripts/priority_rebuild/engine_tuner_exec.py",
 "self_check_calls": ["_check_scene_rules", "scene_rules", "G7"]}
```

**この変更は1レバーです**＝「場面ごとの組み立ての決まり（K-1〜K-7・まこさん承認 2026-08-22・逐語「どちらもOK」「進めていいよ」）を、プログラムの強制にする」。触るファイルは3本＋元データ1本ですが、全部この1レバーの部品です（主ファイル＝TARGET・複数ファイルは本欄に明記＝acceptance_checklist A）。

## ① 真因

- engine_tuner の場面の判定の束（meta.regime.build）には、**場面ごとの決まりが0件**（52回目に実測・worklog 20260822 §29.3）。
- ＝形のおかしい判定（5分足だけ・帯なし・成立と解除の区別なし）でも生成できる。**要件が名指しで禁止する「ランダムに条件をつなぐだけのもの」が、判定の束で起きうる状態。**

## ② 期待値分解

- **net を直接 動かす変更ではありません**（実験ゼロ・採点ゼロのまま）。
- 期待値の経路＝場面の判定の質（「実はトレンドだった割合」を下げる・R9 の測るもの）→ レンジ判定の張り付き損の回避（milestones2 の 0.3.3）。**数字は M2-11（判定だけ差し替えて net で比べる）で出す。ここでは主張しない。**

## ③ root か symptom か

**root です。**生成の構造そのものに制約を入れる変更で、個別の悪い案を1本ずつ潰す対症ではない。

## ④ ベースアップ

- 法則の正本＝regime_detection_kb.md §11（44回目に Web の本文まで開いて作成・まこさん OK 済み）。
- 50件の仕分けの全数と、決まり1件ごとの「何を潰すか」＝session_worklog_20260822.md §30（恒久の決まり46番）。
- 記憶ベースの断定なし＝出典は §11 の法則番号（C1・C4・R3・C6・U10・D8・R1・R8・R7・S1）。

## 読んだもの（Read tool で開いた実物）

engine_tuner_exec.py（_check_regime_meta・_walk_build_tree・_check_hysteresis・G3）／engine_tuner_gen.py（default_regime・sample_structure）／gen_composition_rules.py（T10＝455〜479行）／recipes/composition_rules_src.json（形式）／regime_detection_kb.md §11／engine_tuner_milestones2.md／eval_engine.py（冒頭）／cat_requirements.md（冒頭）／exchange_spec.md（冒頭）。

## やること（5件）

| # | やること | 触るファイル |
|---|---|---|
| 1 | 新しい区分 `scene_rules`（K-1〜K-7 の7件）を足す。各行＝id・決まり・掛かる場面・出典（§11 の法則番号と逐語）・仕分け「①まこさんが決めた制約（2026-08-22 承認）」・機械が強制するか=true。`_手で書いた行数` 23 → 30 | recipes/composition_rules_src.json |
| 2 | **番人 T10 を新しい正解に直す**＝仕分け済み 23 → 30件・強制 2 → 9件・中身 {Q-1, RD-2} → {Q-1, RD-2, K-1〜K-7}。★T10 の目的（まこさんの確認なしに強制を変えたら止める）は保つ＝新しい正解も固定値で書き、次に黙って変えたら また落ちる | gen_composition_rules.py |
| 3 | **G7（場面ごとの決まりの照合）を新設**＝`_check_scene_rules` を作り、`_check_regime_meta` の build 検査から呼ぶ。meta.regime.name（range／uptrend／downtrend／spike）ごとに K-1〜K-7 を照合し、満たさない束は `_fail("G7", …)`（fail-closed） | engine_tuner_exec.py |
| 4 | 生成側が決まりを読む口（`load_scene_rules`＝composition_rules.json の scene_rules を返す）を足す。★生成そのもの（決まりを満たす束を組む）は M2-5 の工程＝ここでは読む口と照合だけ | engine_tuner_gen.py |
| 5 | 番人＝**わざと決まりを破った束7通り（K-1〜K-7 を1件ずつ破る）が G7 で止まる**ことを `--selftest` に足す（M2-4-5 の拒否の実測の土台） | engine_tuner_exec.py |

## 既定 OFF で恒等（既存を壊さない）

- **G7 が照合するのは `meta.regime.build` が在るレシピだけ。**build の無いレシピ（列名の宣言だけ＝いまの E38 の全レシピ・後方互換の道）は照合の対象外＝**既存レシピの挙動は1ビットも変わらない。**
- **恒等検収レーン（lane=legacy＝RG-v5 の写し）にも掛けない。**比べる相手の写しは生成物ではないため（G6 の legacy の扱いと同じ思想）。
- 確かめ方＝M2-4-6 の3本の走行（S2・L1・S1）のハッシュ値が48回目と一致すること。

## ★疑似シミュ由来の固定値ゼロ

- (a) 決まり7件に**数字は1つも入れない**（閾値・本数・保つ長さは全部 範囲＝既存の仕組みのまま）。K-6 の幅の下限も分位の範囲から探索。
- (b) probe の数値の焼き込み＝なし。T10 の新しい正解（30件・9件）は数えた事実で、性能の数字ではない。
- (c) 採否は実エンジン両窓の score.py の数字で決める（M2-11）＝この変更自体は採否の主張をしない。

## D 審判整合

- 新しい exit_reason＝出さない。コスト種別＝触らない。**score.py・eval_engine.py は1バイトも触らない**（H13）。
- 新スクリプト＝作らない（既存4ファイルの中だけ）。サイドカー＝該当なし（売買を走らせない）。

## E ハード制約の照合（H1〜H16）

- H1（cap）＝非該当（建玉に触れない）。H2（leak）＝**該当・守る**＝G7 の照合は束の形（部品の系統・時間足・hysteresis の有無）だけを見る。`.shift(-`・`center=True` は書かない。未来参照の実測は M2-4-4（H2 の検査・印の書き直し）。
- H3〜H5・H9〜H12・H14＝非該当（net 計算・約定・発注に触れない）。
- H6（価格非依存）＝該当・守る＝K-7 がドル絶対値の閾値を拒否する側の変更。
- H7（足の標準）＝非該当。H8（期間）＝非該当（期間に触れない）。H13（judge 固定）＝守る（score.py 不変）。
- H15（ボラ逃げ）＝非該当（Entry の方向スコアを作らない）。
- H16（1変更・不再演）＝**1レバー**（上のとおり）。過去失敗の不再演＝#15（決まり21件で基本ロジックを潰した）は、46番の「何を潰すか」列挙（worklog §30.2）と50件の仕分け全数（§30.3）で照合済み。

## F 受け入れ判定（自己検査）

1. py_compile＝4ファイル全部 通る。
2. `engine_tuner_exec.py --selftest`＝既存の番人 全部 pass ＋ 新しい番人（K-1〜K-7 を1件ずつ破った束7通りが G7 で止まる）pass。
3. `gen_composition_rules.py --verify`＝✅（T10 の新しい正解で）。`--selftest` も pass。
4. 機械生成の文書の検証（22番の決まり）＝`gen_materials` ほか該当の `--verify` を通す。
5. 恒等＝M2-4-6 の3本の走行のハッシュ値一致（★H2 の印の書き直し＝M2-4-4 の後でないと物理的に回らない・やることリストの順のとおり）。
6. net の主張はしない（採点を走らせない）。

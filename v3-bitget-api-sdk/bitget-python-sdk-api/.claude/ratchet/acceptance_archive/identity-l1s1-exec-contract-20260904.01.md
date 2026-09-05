# 設計書｜恒等 L1・S1 を走らせるための最小の設計書（impl_file＝engine_tuner_exec.py・コードは1文字も触らない）

TARGET: scripts/priority_rebuild/engine_tuner_exec.py

REQUIREMENTS: R14（恒等＝V9 の写しが元と同じ売買記録を出すことを md5 で確かめる検収）。M2-C-2 の承認済みの設計書（acceptance_archive の indicator-switch-20260902）の §5 のテスト5「恒等3本（S1・S2・L1）を走らせる → ハッシュ値が直す前と同じ」の残り2本。

**承認の状態＝未承認。この設計書では engine_tuner_exec.py を1文字も書き換えません。**

<!-- ARC order=1 iter="identity-l1s1-exec-contract-20260904" 前提="82回目に恒等 S2 は完全一致したが、L1・S1 は走らせる門（require_design_contract_before_run）が「engine_tuner を指す DESIGN_CONTRACT が1本もありません」で止めた（worklog 20260904 §9.4・§14.9）" 採否="未定" 狙い="engine_tuner_exec.py を impl_file に持つ設計書を置いて門を通し、L1・S1 の md5 が 2026-08-05 以来の基準値と同じことを実測する" 内容="設計書だけ（コードの変更 0行）。impl_functions・SPEC は道具の出力をそのまま貼る" 方法="engine_tuner_exec.py --identity-l1 と --identity-s1 の標準出力（md5）を、そのまま貼る。一致しなければ止めて報告" -->

---

## 0｜まこさんの決定（逐語・2026-09-04）

| # | 逐語 | この設計のどこに効くか |
|---|---|---|
| 1 | 「impl_file を engine_tuner_exec.py にした設計書を1本 出すこと。」 | この設計書そのもの（§11 の impl_file） |
| 2 | 「今回の実装は exec.py を1文字も触っていないので、md5 は基準値と一致するはずです。一致しなければ別の問題が見つかったということなので、その時点で止めて報告すること。」 | §5・§6 の完成の条件＝一致しなければ止める（次の工程に進まない） |
| 3 | 「あわせて1行 説明してください＝同じ日に S2 は走れて、L1・S1 だけが門で止まったのはなぜか。」 | §1.2 |

---

## 1｜いまの状態

### 1.1 実測（2026-09-04・82回目）

| 何を | 結果 | 出どころ |
|---|---|---|
| 恒等 S2（`python3 engine_tuner_exec.py --identity`） | 165行 md5 7b01f51b5a9b29b3c05a7b340c203ba1＝2026-08-05 以来の基準値と同じ（全部一致） | worklog 20260904 §9.4・§14.2（22:26 に2回目） |
| 恒等 L1（`python3 engine_tuner_exec.py --identity-l1`） | 走らせる前に門が止めた（下の逐語） | worklog 20260904 §9.4 |
| 恒等 S1（`python3 engine_tuner_exec.py --identity-s1`） | 同上 | 同上 |
| `engine_tuner_exec.py` の差分 | `git diff --stat -- scripts/priority_rebuild/engine_tuner_exec.py` が空＝最後の commit `4ac4405`（2026-09-02）から1文字も変わっていない | 82回目に `git` で数えた |

門の逐語＝「🔒 [設計↔実装ゲート] engine_tuner を指す DESIGN_CONTRACT が1本もありません（fail-closed・2026-08-23・まこさん承認）。走らせようとしたもの: engine_tuner_exec.py engine_tuner_exec.py」。

### 1.2 ★なぜ S2 は走れて、L1・S1 だけが止まったか（まこさんの問い3・1行＋根拠）

**門は「走らせる .py に付いた旗」が確認用の一覧に**完全一致**するときだけ契約なしで通し、`--identity` はその一覧に在るが `--identity-l1`・`--identity-s1` は無い。**
根拠＝`.claude/hooks/require_design_contract_before_run.sh` の 58-59行（Read tool で開いた）＝`CHECK = set(['--selftest', '--self-test', '--verify', '--identity', '--help', '--scan-contracts', '--diff', '--write', '--dry-run'])`。2026-09-02（監査 cp13 の A-2）で「旗は独立した語として一致したときだけ」に狭められたので、`--identity-l1` は `--identity` の部分一致では通らない。だから S2 だけ「確認のための走行」として通り、L1・S1 は「契約が要る走行」として、engine_tuner_exec.py を impl_file に持つ設計書を求めた。**82回目の設計書 t25 の impl_file は engine_tuner_gen.py だったので、それでも止まった。**

---

## 2｜深掘り4点

### ① 真因（root cause）

**恒等 L1・S1 が測れていない真因は、engine_tuner_exec.py を指す設計書が1本も無いこと。**2026-09-02 の cp13〜cp19 の工事で `acceptance.md` は hook を相手にした設計書に上書きされ、それ以来 engine_tuner を指す契約が消えていた（next_step §6 の90番と同じ状態）。

### ② 期待値分解

**この設計書はコードを1行も変えない。**勝率・平均利益・敗率・平均損失は1つも動かない。動くのは「恒等 L1・S1 が測れる状態になるか」だけ。

### ③ root か symptom か

**root（契約を置く）を選ぶ。**symptom の直し方＝門の旗の一覧に `--identity-l1`・`--identity-s1` を足す（next_step §6 の129番）。**取らない**＝hook を触る＝別の設計書と承認が要り、しかも「確認用の旗を増やす」は門を緩める向き。契約を置く方は門を1文字も緩めない。

### ④ ベースアップ（このセッションで Read tool を使って開いたもの）

| 何を確かめたか | 出どころ |
|---|---|
| 恒等3本の引数が実行器の側に在ること | scripts/priority_rebuild/engine_tuner_exec.py（4736-4752行） |
| 門の旗の一覧 | .claude/hooks/require_design_contract_before_run.sh（1-60行） |
| 照合の道具が契約と SPEC を「目印の行」で取り出すこと・--diff が SPEC の impl_file を使うこと | scripts/priority_rebuild/verify_design_contract.py（141-236行・238-241行・406-439行・1622行） |
| 承認スクリプトが「最後の impl_file の囲み」から凍結を作ること | .claude/hooks/approve_impl.sh（62-73行・105-115行） |
| 実行器の SPEC の書き出し（21:33・実行器は以後 変わっていない） | v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/indicator-switch-20260902.md.actual.md（171-278行） |

**★WebSearch は使っていません。**うちの実物を読む話だからです。

---

## 3｜何を作るか

### 3.1 作るもの＝この設計書1本（コードの変更 0行）

- `impl_file`＝`scripts/priority_rebuild/engine_tuner_exec.py`。
- `impl_functions`＝`python3 .claude/tools/gen_impl_functions.py scripts/priority_rebuild/engine_tuner_exec.py` の出力をそのまま（§11）。**関数を足しも消しもしない。**
- SPEC＝実行器から機械で書き出したもの（§10）。**★この設計書では SPEC の節（§10）を DESIGN_CONTRACT の節（§11）より前に置く**（理由＝§9 の I）。

### 3.2 走らせるもの（承認のあと）

| 順 | コマンド | 何が出るか |
|---|---|---|
| 1 | `python3 engine_tuner_exec.py --identity-l1` | L1 の売買記録の行数と md5・「完全一致」か |
| 2 | `python3 engine_tuner_exec.py --identity-s1` | S1 の同上 |
| 3 | `python3 engine_tuner_exec.py --identity` | S2（もう1回・同じ日に3本 並べるため） |

**基準値（2026-08-05 以来・worklog 20260812:532-534・20260821:502-503・20260825:537）**＝S2 165行 7b01f51b5a9b29b3c05a7b340c203ba1／L1 367行 96a9102ec8a34f94cf01e9e463f6aade／S1 6,569行 18b3d31a5fe71c4a4b5f83cf1771a46c。

### 3.3 触らないもの

- `engine_tuner_exec.py`・`engine_tuner_gen.py`・hook・道具＝**1文字も変えない**。
- 印（`indicator_switch.json`）・型の表・H2/G2 の印＝**取り直さない**（コードを触らないため）。

---

## 4｜★疑似シミュ由来の固定値ゼロ

- **疑似シミュ（probe）を1回も使っていません。**この設計書に出てくる数字は、過去の記録の md5 と行番号だけです。
- **閾値・段数・確率の数字を1つも作っていません。**
- **採否は score.py の数字で決めます。**ただしこの工程は検収（恒等）で、売買の採否は M2-L 以降です。

---

## 5｜わざと壊して止まるか試すテスト

| # | 何を試すか | 期待する結果 |
|---|---|---|
| 1 | `python3 engine_tuner_exec.py --identity-l1` | 367行・md5 96a9102ec8a34f94cf01e9e463f6aade・「完全一致」 |
| 2 | `python3 engine_tuner_exec.py --identity-s1` | 6,569行・md5 18b3d31a5fe71c4a4b5f83cf1771a46c・「完全一致」 |
| 3 | `python3 engine_tuner_exec.py --identity` | 165行・md5 7b01f51b5a9b29b3c05a7b340c203ba1・「完全一致」 |
| 4 | 承認のあと、`python3 verify_design_contract.py .claude/state/acceptance.md` | PASS（凍結の impl_functions が §11 と同じ＝§9 の I の回り道が効いたかの確認） |
| 5 | 承認の前に、同じ照合 | FAIL（凍結は まだ t25 の空のまま）＝門が生きている |

**★1〜3 のどれかが「完全一致」でなければ、そこで止めて報告する（まこさんの決定2）。次の工程に進まない。**

---

## 6｜何ができたら完成か

<!-- ACCEPT_TABLE_START -->

**★「経路」＝`実経路`（コマンドで走らせた）か `部品`（関数を直接 呼んだ）。**
**★「壊すプログラム」＝この回は `.claude/breaks/` に新しく足しません（コードを触らない設計書のため。既存の20本が承認のたびに走ります）。**

| # | 完成の条件 | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|
| 1 | 恒等 L1 の md5 が基準値 96a9102e… と同じ（完全一致） | 実経路 | §5 の1（一致しなければ止める） | — | — | **未着手** |
| 2 | 恒等 S1 の md5 が基準値 18b3d31a… と同じ（完全一致） | 実経路 | §5 の2 | — | — | **未着手** |
| 3 | 恒等 S2 の md5 が基準値 7b01f51b… と同じ（同じ日に3本 並ぶ） | 実経路 | §5 の3 | — | — | **未着手** |
| 4 | 承認のあと、単体の照合が PASS（凍結の impl_functions が空でない） | 実経路 | §5 の5（承認の前は FAIL） | — | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

**★私が自分で合格ラインを引いていないこと**＝1〜3 の基準値は 2026-08-05 以来の記録の値で、私が今日 作った数字ではありません。
**★「完成」の判定は私がしません**（恒久の決まり64番）。md5 をそのまま貼るだけです。

---

## 7｜既存を壊さないこと（副作用）

| 何が | どうなるか |
|---|---|
| `engine_tuner_exec.py`・`engine_tuner_gen.py` | **1文字も変えない** |
| H2 の印・G2 の印 | **取り直し不要**（コードを触らない） |
| 型の表の承認・印（indicator_switch.json） | 変わらない |
| いま採用している戦略（E36 ほか） | 触らない |
| t25 の設計書の控え（acceptance_archive/t25-fixture-off-20260904.md） | 残る（この設計書は別の iter 名） |

---

## 8｜照合（群2＝まとめて非該当の1行）

**H1〜H16 と審判整合（群2の18件）は、まとめて非該当です。**理由＝コードを1行も変えず、売買記録を1本も書かず、`score.py` と `eval_engine.py` に1行も触れないためです。

**★1変更か（H16）**＝1つです。「engine_tuner_exec.py を指す設計書を置く」だけです。恒等はその設計書で走らせる検収で、変更ではありません。

**★過去に破棄した失敗の再演か**＝当たりません。恒等は「写しが元と同じか」を測る検収（要件 R14）で、V9 のコピーを作る工程ではありません。

---

## 9｜★正直に書く｜それでも塞げないもの

**塞げないもの（この設計の範囲で残る穴）**

| # | 塞げないもの | なぜ塞げないか | 何が代わりに守るか |
|---|---|---|---|
| I | **承認スクリプトが「最後の impl_file の囲み」から凍結を作る**（worklog 20260904 §15）＝SPEC の囲み（impl_file は在るが impl_functions は無い）が DESIGN_CONTRACT より後ろに在ると、空を凍結する | 道具を直すのは別の設計書（next_step §6 の131番・まこさんが決める）。★SPEC の json から impl_file を外す道は使えない（`--diff` が SPEC の impl_file を読む＝`verify_design_contract.py`:1622・82回目に実測して落ちた） | **この設計書では SPEC の節（§10）を DESIGN_CONTRACT の節（§11）より前に置く**＝承認スクリプトが最後に見る impl_file の囲みが DESIGN_CONTRACT になる。照合の道具は目印の行（見出し）で取り出すので、順番に影響されない（`verify_design_contract.py`:141-236）。効いたかは §5 の4（承認のあとの照合が PASS）で分かる |
| J | 恒等が一致しても「engine_tuner が V9 と同じ売買をする」と言えるのは、恒等レシピ3本（S1・S2・L1）の範囲だけ | 恒等は3本しか無い | M2 の以後の工程（M2-L で net を測る） |
| K | 門の旗の一覧に `--identity-l1`・`--identity-s1` が無い件（129番）は、この設計書では直らない＝engine_tuner_exec.py を指す設計書が無くなれば、また止まる | hook を触らない | 記録（129番）。直すかは まこさんが決める |

**★強制の土台そのものの穴（監査 cp14 の Q5 の5件・cp19 で「閉じない部分」として確定＝`lessons_active.md` の L-586。この設計は1つも塞がない・受け入れ条件ゲートが毎回 書かせる）**

| # | 塞げないもの | この設計での扱い |
|---|---|---|
| D | **照合D が実経路で1度も走っていない**（監査 Q5 の1） | この設計書も `spec_lists` は空（理由は §11 の `no_spec_lists_reason`）＝照合D はこの回も走らない |
| E | **照合の道具と印を、私が書ける場所に置いたまま**（監査 Q5 の2） | 触らない。J-6（外部CI）は まこさん決定で着手しない（L-586） |
| F | **照合A・B の期待値が、実装から作られる**（監査 Q5 の3） | `impl_functions` は実物の全関数の写し＝承認の画面に ⚠️ が出続けるのが正しい状態（まこさんの指定 2026-09-03） |
| G | **語を並べて迂回を塞ぐやり方は、原理的に閉じない**（監査 Q5 の4） | 触らない。この設計は hook を1文字も変えない |
| H | **承認の記録を全部 消したときを測っていない**（監査 Q5 の5） | 測らない（まこさんの一覧の外・cp19 で確定） |

---

## 10｜SPEC（★`verify_design_contract.py --write --dry-run` が 2026-09-04 21:33 に実行器から書き出したものをそのまま。実行器は以後 変わっていない＝`git diff` が空。★この節を DESIGN_CONTRACT より前に置く理由＝§9 の I）

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/engine_tuner_exec.py",
 "public_functions": {
  "forms_where": [],
  "forms_pair_in": [],
  "load_indicator_switch": [],
  "indicator_enabled": [
   "load_indicator_switch"
  ],
  "geo_enabled": [
   "load_indicator_switch"
  ],
  "indicator_switch_fingerprint": [
   "load_indicator_switch"
  ],
  "build_name": [],
  "RecipeError": [],
  "pre_ops": [],
  "pair_ops": [],
  "regime_law_counts": [
   "load_regime_laws"
  ],
  "load_regime_laws": [],
  "regime_cols": [],
  "cap_of": [],
  "validate_recipe": [
   "cap_of"
  ],
  "material_array": [
   "RecipeError"
  ],
  "build_regime_columns": [
   "RecipeError"
  ],
  "run_recipe": [
   "RecipeError",
   "build_regime_columns",
   "validate_recipe"
  ],
  "identity_recipe": [],
  "engine_params_from_recipe": [],
  "run_identity": [
   "engine_params_from_recipe",
   "identity_recipe",
   "run_recipe"
  ],
  "legacy_cols_in": [],
  "source_logic": [
   "RecipeError"
  ],
  "attach_recipe_columns": [
   "RecipeError",
   "legacy_cols_in",
   "regime_cols",
   "source_logic"
  ],
  "identity_l1_recipe": [],
  "l1_engine_params": [],
  "run_identity_l1": [
   "attach_recipe_columns",
   "identity_l1_recipe",
   "l1_engine_params",
   "run_recipe"
  ],
  "identity_s1_recipe": [],
  "s1_engine_params": [],
  "run_identity_s1": [
   "attach_recipe_columns",
   "identity_s1_recipe",
   "run_recipe",
   "s1_engine_params"
  ],
  "maker_taker_sync_check": [],
  "e36_maker_taker_behavior_check": [],
  "unordered_iteration_scan": [],
  "selftest": [
   "e36_maker_taker_behavior_check",
   "identity_l1_recipe",
   "identity_recipe",
   "identity_s1_recipe",
   "load_regime_laws",
   "maker_taker_sync_check",
   "regime_law_counts",
   "unordered_iteration_scan",
   "validate_recipe"
  ],
  "main": [
   "run_identity",
   "run_identity_l1",
   "run_identity_s1",
   "selftest",
   "validate_recipe"
  ]
 },
 "constants": {
  "NO_CAP": "無制限"
 },
 "cli_flags": []
}
```

---

## 11｜DESIGN_CONTRACT

**★`impl_functions` は `python3 .claude/tools/gen_impl_functions.py scripts/priority_rebuild/engine_tuner_exec.py` の出力をそのまま貼ったものです（2026-09-04・手打ちしていません）。関数を足しも消しもしません。**

```json
{
  "impl_file": "scripts/priority_rebuild/engine_tuner_exec.py",
  "impl_functions": {
    "scripts/priority_rebuild/engine_tuner_exec.py": [
      "<モジュール直下>",
      "_apply_pre",
      "_attach_v47_cols",
      "_attach_v59_cols",
      "_base_ok_recipe",
      "_ceiling_fire",
      "_check_bool_cond",
      "_check_cond",
      "_check_exit_fire_cond",
      "_check_hysteresis",
      "_check_int_range",
      "_check_level",
      "_check_not_node",
      "_check_num_range",
      "_check_param_range",
      "_check_q_range",
      "_check_regime_meta",
      "_check_scene_rules",
      "_check_value",
      "_col_array",
      "_collect_fire_cols",
      "_conds_under_not",
      "_dirless_parts",
      "_entry_fire",
      "_eval_cond",
      "_eval_tree",
      "_exit_fire_ok",
      "_fail",
      "_fire_key",
      "_guards_ok",
      "_has_ref",
      "_hold_state",
      "_is_cond",
      "_l1_attach_legacy_cols",
      "_law_count",
      "_law_count_and",
      "_mat_key",
      "_material_family",
      "_material_name",
      "_md5_trades",
      "_ordering_sentinel",
      "_pair_key",
      "_pair_op_of",
      "_pair_series",
      "_peak_giveback_level",
      "_pre_of",
      "_refs_prop",
      "_regime_series",
      "_resolve_levels",
      "_scene_scan",
      "_selftest_4_19",
      "_selftest_roundtrip",
      "_sentinel_df",
      "_side_cmp",
      "_since_stat",
      "_static_level_px",
      "_swing_key",
      "_swing_specs",
      "_template_from_pattern",
      "_tree_depth",
      "_upper_tfs",
      "_validate_law",
      "_vnum",
      "_vnum_q",
      "_walk",
      "_walk_build_tree",
      "attach_recipe_columns",
      "build_name",
      "build_regime_columns",
      "cap_of",
      "e36_maker_taker_behavior_check",
      "engine_params_from_recipe",
      "forms_pair_in",
      "forms_where",
      "geo_enabled",
      "identity_l1_recipe",
      "identity_recipe",
      "identity_s1_recipe",
      "indicator_enabled",
      "indicator_switch_fingerprint",
      "l1_engine_params",
      "legacy_cols_in",
      "load_indicator_switch",
      "load_regime_laws",
      "main",
      "maker_taker_sync_check",
      "material_array",
      "pair_ops",
      "pre_ops",
      "regime_cols",
      "regime_law_counts",
      "run_identity",
      "run_identity_l1",
      "run_identity_s1",
      "run_recipe",
      "s1_engine_params",
      "selftest",
      "source_logic",
      "unordered_iteration_scan",
      "validate_recipe"
    ]
  },
  "self_check_calls": [
    "run_identity",
    "run_identity_l1",
    "run_identity_s1",
    "identity_l1_recipe",
    "identity_s1_recipe"
  ],
  "must_use": {
    "main": ["run_identity_l1", "run_identity_s1"]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "この設計書はコードを変えない（恒等を走らせるための契約を置くだけ）。照合D の相手になる正本の配列が存在しない。",
  "generated_from": {
    "impl_functions": "gen_impl_functions.py の出力をそのまま（2026-09-04）。関数を足しも消しもしない",
    "must_use": "main が run_identity_l1 と run_identity_s1 を呼ぶこと（engine_tuner_exec.py:4751-4760 を Read tool で確認済み・手書き）",
    "spec_lists": "無し（理由は no_spec_lists_reason）"
  }
}
```

---

## 12｜まこさんにお願いすること

**承認の1点です**（`approve_design.sh` と `approve_impl.sh`）。承認のあと、§3.2 の3本を走らせ、標準出力（行数・md5・完全一致か）をそのまま貼って報告します。1本でも一致しなければ、その時点で止めて報告します。

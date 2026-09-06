# indicator-switch-20260902.md.actual.md — 実物から書き出した文書（手で書き換えない）

> このファイルはプログラムが実物から作ります（`--write`）。**手で書き換えないでください。**
> 手書きの設計書と突き合わせるための相手です。違いは `--diff` が出します。

## §1 制約（要件定義書 §4.6 から引いた）

| # | 制約 |
|---|---|
| H1 | ポジション合計上限 |
| H2 | leak なし / 本番再現性 |
| H3 | net 判定 |
| H4 | コスト確定値 |
| H5 | 約定モデル |
| H6 | 価格非依存 |
| H7 | 足の標準 |
| H8 | 期間分割 |
| H9 | 最小注文 |
| H10 | サイズ固定値扱い禁止 |
| H11 | 合格ライン / 地面 |
| H12 | 異常値STOP |
| H13 | judge 固定 |
| H14 | 発注フラグ |
| H15 | Entry ボラ逃げ禁止 |
| H16 | 過去失敗の不再演 ＋ 1ターン1変更 |

## §2 ベンチマーク（いまの実測）

- DESIGN_CONTRACT が読める文書: 4本
    - e35_design.md -> scripts/priority_rebuild/e35_range_oscillation.py
    - e37_design.md -> scripts/priority_rebuild/e37_range_scalp.py
    - e38_design.md -> scripts/priority_rebuild/e38_priority_stack.py
    - acceptance.md -> .claude/hooks/require_acceptance_before_impl.sh
- 読めない文書: 0本
- 対象外（目印の行が無い）: 6本
    - adopted_strategies.md
    - contract_check_design.md
    - e38_flow.md
    - forbidden_check_design.md
    - improvement_arc.md
    - ledger.md

## §5 仕様（実物のコードから書き出した）

| 公開する関数 | その中で呼んでいる公開の名前 |
|---|---|
| `RecipeError` | （無し） |
| `attach_recipe_columns` | RecipeError・legacy_cols_in・regime_cols・source_logic |
| `build_name` | （無し） |
| `build_regime_columns` | RecipeError |
| `cap_of` | （無し） |
| `e36_maker_taker_behavior_check` | （無し） |
| `engine_params_from_recipe` | （無し） |
| `forms_pair_in` | （無し） |
| `forms_where` | （無し） |
| `geo_enabled` | load_indicator_switch |
| `identity_l1_recipe` | （無し） |
| `identity_recipe` | （無し） |
| `identity_s1_recipe` | （無し） |
| `indicator_enabled` | load_indicator_switch |
| `indicator_switch_fingerprint` | load_indicator_switch |
| `l1_engine_params` | （無し） |
| `legacy_cols_in` | （無し） |
| `load_indicator_switch` | （無し） |
| `load_regime_laws` | （無し） |
| `main` | run_identity・run_identity_l1・run_identity_s1・selftest・validate_recipe |
| `maker_taker_sync_check` | （無し） |
| `material_array` | RecipeError |
| `pair_ops` | （無し） |
| `pre_ops` | （無し） |
| `regime_cols` | （無し） |
| `regime_law_counts` | load_regime_laws |
| `run_identity` | engine_params_from_recipe・identity_recipe・run_recipe |
| `run_identity_l1` | attach_recipe_columns・identity_l1_recipe・l1_engine_params・run_recipe |
| `run_identity_s1` | attach_recipe_columns・identity_s1_recipe・run_recipe・s1_engine_params |
| `run_recipe` | RecipeError・build_regime_columns・validate_recipe |
| `s1_engine_params` | （無し） |
| `selftest` | e36_maker_taker_behavior_check・identity_l1_recipe・identity_recipe・identity_s1_recipe・load_regime_laws・maker_taker_sync_check・regime_law_counts・unordered_iteration_scan・validate_recipe |
| `source_logic` | RecipeError |
| `unordered_iteration_scan` | （無し） |
| `validate_recipe` | cap_of |

| 定数 | 値 |
|---|---|
| `NO_CAP` | `'無制限'` |

- コマンドの旗: （無し）

## §6 テスト一覧（わざと壊して止まるか試すテスト）

| # | 中身 |
|---|---|
| T1 | 目印を囲みの見出しに書いた文書を読める |
| T2 | json の閉じ括弧を消すと読めない側に入る |
| T3 | impl_file が空だと読めない側に入る |
| T4 | 目印が文章の中だけの文書は対象外に入る |
| T5 | 設計の SPEC から関数を1つ消すと『実物にあるが設計に無い関数』で落ちる |
| T6 | 実物から関数を1つ消すと『設計にあるが実物に無い関数』で落ちる |
| T7 | 関数の中身を空にすると『呼ぶはずの名前が実物に無い』で落ちる |
| T8 | 全部そろっていれば通る |
| T9 | SPEC が無い設計書は『SPEC が無い』と分かる（engine_tuner はこれで止める） |
| T10 | 設計書を1文字 書き換えると承認が外れる |
| T11 | --write が書き出した SPEC を使うと、突き合わせが 0件 になる |
| T12 | 目印を囲みの中だけに書いた設計書は、要件の番号を数えない |
| T13 | 引用の行・全角の目印・行の途中の目印は、どれも数えない |
| T14 | 目印の行が2つあれば番号を合わせ、同じ番号は1件に畳む |
| T15 | 要件に無い番号は『要件に無い番号』として表に出る（止めない） |
| T16 | 表に出る要件の言葉は、要件の json からの複写である |
| T17 | どの設計書も指していない要件が、表で分かる |
| N1 | 照合A＝触っていない関数を『触った』と言わない（誤検出しない） |
| N2 | 照合A＝新しく足した関数を拾う（見落とさない） |
| N3 | 照合B＝設計書に書いた関数が実装に無ければ落ちる |
| N4 | 照合C＝正本から作った名前が中身に無ければ落ちる（自明な名前では通らない） |
| N5 | 照合D＝一覧の一部だけを直書きすると落ちる |
| N6 | 照合A＝道具の承認の印が無ければ落ちる |
| N7 | 差分がゼロ（commit 済み）でも照合B は走る |
| N8 | 照合A・B＝設計書の impl_functions が凍結された版と違えば落ちる（B-1） |
| N9 | 照合A・B＝凍結された版が無ければ落ちる（B-1・fail-closed） |
| N10 | 照合C＝kind の掘り下げの経路で正本から名前が取れる（B-3） |
| N11 | 照合C＝正本に無い kind は、黙って全体に落ちずに落ちる（B-3） |
| N12 | 承認と同じ形＝{from,kind} を配列へ展開できる（B-2・resolve_spec_list） |
| N5b | 照合D＝承認が書き出す形（展開済みの配列）で成立する（B-2） |

## DESIGN_CONTRACT（実物から作った）

DESIGN_CONTRACT

```json
{
 "impl_file": "scripts/priority_rebuild/engine_tuner_exec.py",
 "self_check_calls": [
  "RecipeError",
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
}
```

## SPEC（実物から作った・★次の設計書はここを出発点にする）

> **手で書く欄を減らすための節です。**この中身を設計書の SPEC に写し、
> 今回 変えるところだけを手で直します。写したあと `--diff` が「齟齬: 0件」になります。

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

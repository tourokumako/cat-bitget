# contract_check_design.md.actual.md — 実物から書き出した文書（手で書き換えない）

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

- DESIGN_CONTRACT が読める文書: 5本
    - contract_check_design.md -> scripts/priority_rebuild/verify_design_contract.py
    - e35_design.md -> scripts/priority_rebuild/e35_range_oscillation.py
    - e37_design.md -> scripts/priority_rebuild/e37_range_scalp.py
    - e38_design.md -> scripts/priority_rebuild/e38_priority_stack.py
    - acceptance.md -> scripts/priority_rebuild/verify_design_contract.py
- 読めない文書: 0本
- 対象外（目印の行が無い）: 4本
    - adopted_strategies.md
    - e38_flow.md
    - improvement_arc.md
    - ledger.md

## §5 仕様（実物のコードから書き出した）

| 公開する関数 | その中で呼んでいる公開の名前 |
|---|---|
| `check` | extract_contract・rhs_names_for_symbol |
| `check_approval` | （無し） |
| `diff_spec` | （無し） |
| `extract_block` | （無し） |
| `extract_contract` | extract_block |
| `rhs_names_for_symbol` | （無し） |
| `scan_contracts` | extract_block |
| `self_test` | check_approval・diff_spec・extract_block・scan_contracts・spec_from_design・spec_from_impl・write_actual |
| `spec_from_design` | extract_block |
| `spec_from_impl` | （無し） |
| `write_actual` | extract_block・scan_contracts・spec_from_impl |

| 定数 | 値 |
|---|---|
| `CONTRACT_MARK` | `'DESIGN_CONTRACT'` |
| `SPEC_MARK` | `'SPEC'` |

- コマンドの旗: --check-approval・--diff・--scan-contracts・--self-test・--write

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

## DESIGN_CONTRACT（実物から作った）

DESIGN_CONTRACT

```json
{
 "impl_file": "scripts/priority_rebuild/verify_design_contract.py",
 "self_check_calls": [
  "check",
  "check_approval",
  "diff_spec",
  "extract_block",
  "extract_contract",
  "rhs_names_for_symbol",
  "scan_contracts",
  "self_test",
  "spec_from_design",
  "spec_from_impl",
  "write_actual"
 ]
}
```

## SPEC（実物から作った・★次の設計書はここを出発点にする）

> **手で書く欄を減らすための節です。**この中身を設計書の SPEC に写し、
> 今回 変えるところだけを手で直します。写したあと `--diff` が「齟齬: 0件」になります。

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/verify_design_contract.py",
 "public_functions": {
  "extract_block": [],
  "extract_contract": [
   "extract_block"
  ],
  "rhs_names_for_symbol": [],
  "scan_contracts": [
   "extract_block"
  ],
  "spec_from_impl": [],
  "spec_from_design": [
   "extract_block"
  ],
  "diff_spec": [],
  "write_actual": [
   "extract_block",
   "scan_contracts",
   "spec_from_impl"
  ],
  "check_approval": [],
  "check": [
   "extract_contract",
   "rhs_names_for_symbol"
  ],
  "self_test": [
   "check_approval",
   "diff_spec",
   "extract_block",
   "scan_contracts",
   "spec_from_design",
   "spec_from_impl",
   "write_actual"
  ]
 },
 "constants": {
  "CONTRACT_MARK": "DESIGN_CONTRACT",
  "SPEC_MARK": "SPEC"
 },
 "cli_flags": [
  "--check-approval",
  "--diff",
  "--scan-contracts",
  "--self-test",
  "--write"
 ]
}
```

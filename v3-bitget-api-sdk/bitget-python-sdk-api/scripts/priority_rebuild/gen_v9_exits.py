#!/usr/bin/env python3
"""gen_v9_exits.py — V9 の Exit 実装を実コードから機械で表にする（まこさん指摘 2026-07-27 を受けて新設）

なぜ作ったか
--------------------------------------------------------------------------
CC が「V9 が実際にやっている形です」と5点を言い切り、実コードで検証したら2点が誤りだった
（2026-07-27・worklog §18）。出どころの entry_exit_matrix ③-2「V9 Exit 最適化5原則」が
**手書きの要約**で、実装とずれていたのが原因。CC はそれを検証せずに引用した。

誤っていた例:
  ・「各枝は 利益の状態 × 保有時間 × 指標 の AND」→ 実際は枝ごとに使う要素が違う。指標を使うのは3枝だけ。
  ・「負けは前倒し・勝ちは満期まで伸ばす」→ 含み益は通常の満期。伸ばしていない。

だから手書きの要約をやめ、**実コードから機械で抽出する**。今日作った gen_windows／gen_filemap と同じ思想。

何をするか
--------------------------------------------------------------------------
  runner/replay_csv.py の `_check_exits_replay` と `_calc_tp_price` を AST で読み、枝ごとに
  ① 返す exit_reason ② 発火条件に使っている変数 ③ 参照している params のキー を抜き出して表にする。
  ★意味づけ（「これは失速の枝」等）はしない＝解釈を挟むと手書きの要約に戻るため。事実だけ出す。

V9 は改造禁止（H13）＝本ツールは読むだけ。書き込むのは出力の .md のみ。

使い方
--------------------------------------------------------------------------
  python3 scripts/priority_rebuild/gen_v9_exits.py --write     # 作り直す
  python3 scripts/priority_rebuild/gen_v9_exits.py --verify    # 改変・未更新の検出
  python3 scripts/priority_rebuild/gen_v9_exits.py --selftest  # 材料が実体から取れているかの番人
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent                                   # bitget-python-sdk-api/
SRC = ROOT / "runner" / "replay_csv.py"                     # V9 の Exit 実装（改造禁止・読むだけ）
PARAMS = ROOT / "config" / "cat_params_v9.json"             # V9 の値（改造禁止・読むだけ）
# ★GENERATES＝この道具が作る文書の名乗り（2026-08-16 新設・まこさん決定 A）。
#   なぜ要るか＝名前で数えると必ず漏れる（出力先の変数名が道具ごとにバラバラで、
#   読むファイルと作るファイルが同じ形で並んでいる＝外から見分けられない）。
#   だから道具の側に名乗らせる。集める道具＝gen_docmap.py。
#   形＝(リポジトリの根からのパス, "まるごと" か "一部の節")。
GENERATES = [
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/v9_exits.md", "まるごと"),
]

OUT = ROOT / ".claude" / "ratchet" / "v9_exits.md"

FUNCS = ("_check_exits_replay", "_calc_tp_price")

# 変数の意味（実装の識別子 → 読み手向けの言葉）。ここだけは対応表＝意味づけでなく訳語。
VARS = {
    "hold_min": "保有時間（分）", "mfe_usd": "含み益の最大（ドル）", "unreal": "いまの含み損益（ドル）",
    "add_count": "積み増した回数", "priority": "Priority 番号", "side": "売り買いの別",
    "mark_price": "いまの価格", "entry_p": "建値", "size_btc": "枚数（BTC）",
    "adx": "ADX", "atr_14": "ATR14", "bb_width": "BB幅", "rsi_short": "RSI（ショート用）",
    "rsi_slope_short": "RSI の傾き", "stoch_k": "ストキャス %K", "stoch_d": "ストキャス %D",
    "i": "バーの位置", "df": "価格データ", "params": "設定値",
}
IND_COLS = {"adx", "atr_14", "bb_width", "rsi_short", "rsi_slope_short", "stoch_k", "stoch_d"}
STATE_VARS = {"hold_min", "mfe_usd", "unreal", "add_count"}


def _tree() -> ast.Module:
    return ast.parse(SRC.read_text(encoding="utf-8"))


def _func(name: str) -> ast.FunctionDef:
    for n in ast.walk(_tree()):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    raise SystemExit(f"[エラー] {name} が {SRC.name} に無い＝実装が動いた（本ツールを直す）")


def _indicator_aliases(fn: ast.FunctionDef) -> dict[str, str]:
    """`bw = _col("bb_width")` のような代入を辿って、変数名 → 指標の列名 の対応を作る。

    ★2026-07-27 の是正＝当初これが無く、条件に出るのは代入後の変数名（bw）だったため
      「指標を使う枝は0件」と誤って出していた。BREAKOUT_CUT は bb_width と rsi を使っている。
    """
    alias: dict[str, set[str]] = {}
    changed = True
    while changed:                       # 変数が変数を経由する場合があるので落ち着くまで回す
        changed = False
        for node in ast.walk(fn):
            if not isinstance(node, ast.Assign):
                continue
            found: set[str] = set()
            for sub in ast.walk(node.value):
                # _col("bb_width") / df.at[i, "stoch_k"] / 文字列リテラルの列名
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and sub.value in IND_COLS:
                    found.add(sub.value)
                # 既に指標だと分かっている変数を経由する場合（_golden_cross = ... _sk_now ...）
                if isinstance(sub, ast.Name) and sub.id in alias:
                    found |= alias[sub.id]
            if not found:
                continue
            for t in node.targets:
                if isinstance(t, ast.Name):
                    before = alias.get(t.id, set())
                    if not found <= before:
                        alias[t.id] = before | found
                        changed = True
    return alias


def _branches() -> list[dict]:
    """`return "EXIT_REASON"` を返す枝ごとに、条件で使っている値と設定キーを集める。"""
    fn = _func("_check_exits_replay")
    alias = _indicator_aliases(fn)
    out = []
    for node in ast.walk(fn):
        if not (isinstance(node, ast.Return) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            continue
        reason = node.value.value
        # その return を含む if 群を、関数の中から包含関係で探す（AST は親を持たないため走査で復元）
        conds, keys, inds = set(), set(), set()
        for anc in ast.walk(fn):
            if not isinstance(anc, ast.If):
                continue
            if not any(n is node for n in ast.walk(anc)):
                continue
            for sub in ast.walk(anc.test):
                if isinstance(sub, ast.Name):
                    if sub.id in alias:
                        inds |= alias[sub.id]         # 指標を入れた変数（経由も追う）
                    elif sub.id in IND_COLS:
                        inds.add(sub.id)
                    else:
                        conds.add(sub.id)
                if isinstance(sub, ast.Call):
                    for a in sub.args:
                        if isinstance(a, ast.Constant) and isinstance(a.value, str):
                            (inds if a.value in IND_COLS else keys).add(a.value)
                if isinstance(sub, ast.Subscript):
                    if isinstance(sub.slice, ast.Constant) and isinstance(sub.slice.value, str):
                        (inds if sub.slice.value in IND_COLS else keys).add(sub.slice.value)
                    if isinstance(sub.slice, ast.Tuple):
                        for e in sub.slice.elts:
                            if isinstance(e, ast.Constant) and isinstance(e.value, str):
                                (inds if e.value in IND_COLS else keys).add(e.value)
        out.append({"reason": reason, "line": node.lineno,
                    "vars": sorted(v for v in conds if v in STATE_VARS or v == "priority"),
                    "inds": sorted(inds),
                    "keys": sorted(k for k in keys
                                   if k not in IND_COLS and k not in ("LONG", "SHORT"))})
    out.sort(key=lambda b: b["line"])                  # 実装の順（上から順に評価される順）
    seen: dict[str, int] = {}
    for b in out:
        seen[b["reason"]] = seen.get(b["reason"], 0) + 1
        b["n"] = seen[b["reason"]]
    return out


def _tp_keys() -> list[str]:
    fn = _func("_calc_tp_price")
    ks = set()
    for sub in ast.walk(fn):
        if isinstance(sub, ast.Call):
            for a in sub.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    ks.add(a.value)
        if isinstance(sub, ast.Subscript) and isinstance(sub.slice, ast.Constant) \
                and isinstance(sub.slice.value, str):
            ks.add(sub.slice.value)
    return sorted(ks)


def _param_value(key: str) -> str:
    try:
        d = json.loads(PARAMS.read_text(encoding="utf-8"))
    except Exception:
        return "—"
    v = d.get(key)
    return "—" if v is None else str(v)


def doc() -> str:
    br = _branches()
    L = ["<!-- V9_EXITS_HASH={h} -->",
         "# v9_exits.md — V9 の Exit 実装（gen_v9_exits.py が実コードから機械生成＝手書き禁止）",
         "",
         "⚠️ 手で書き換えないでください。中身は `runner/replay_csv.py` と `config/cat_params_v9.json` から",
         "機械で抜いています。V9 は改造禁止です。本書は読むだけの道具が作っています。",
         "",
         "```",
         "python3 scripts/priority_rebuild/gen_v9_exits.py --write    # 作り直す",
         "python3 scripts/priority_rebuild/gen_v9_exits.py --verify   # 改変の検出",
         "```",
         "",
         "## なぜこの文書があるか",
         "",
         "V9 の Exit について、手書きの要約が実装とずれていました（2026-07-27）。",
         "その要約を引用した結果、5つの説明のうち2つが誤りでした。だから要約をやめて、",
         "**実装から機械で抜いた事実だけ**を置きます。意味づけ（この枝は失速の枝、など）はしません。",
         "",
         "## 決済の枝（上から順に見て、最初に成立した枝で決済する）",
         "",
         "| # | 決済の名前 | 玉の状態 | 指標 | 参照している設定キー |",
         "|---|---|---|---|---|"]
    for i, b in enumerate(br, 1):
        vs = "／".join(VARS.get(v, v) for v in b["vars"]) or "—"
        ind_s = "／".join(VARS.get(x, x) for x in b["inds"]) or "**使わない**"
        ks = "／".join(f"`{k}`" for k in b["keys"][:5]) or "—"
        more = f" ほか{len(b['keys'])-5}件" if len(b["keys"]) > 5 else ""
        nm = b["reason"] + (f"（{b['n']}件目）" if b["n"] > 1 else "")
        L.append(f"| {i} | {nm} | {vs} | {ind_s} | {ks}{more} |")
    ind = [b for b in br if b["inds"]]
    L += ["",
          f"枝は全部で {len(br)} 件です。",
          "",
          "## 事実として言えること（数えただけ・解釈なし）",
          "",
          f"- **指標を条件に使っている枝は {len(ind)} 件**です"
          f"（{'／'.join(sorted({b['reason'] for b in ind})) or 'なし'}）。"
          "残りの枝は、含み益・含み損益・保有時間・積み増し回数だけで決まります。",
          "- **Priority 番号を条件に使っている枝は "
          f"{len([b for b in br if 'priority' in b['vars']])} 件**です＝枝が Priority ごとに分かれています。",
          "- **同じ決済の名前が複数の枝から返ります**（Priority 別に別々の条件で書かれているため）。",
          "",
          "## 利確の値の決まり方（`_calc_tp_price`）",
          "",
          "| 参照している設定キー | いまの値 |",
          "|---|---|"]
    for k in _tp_keys():
        L.append(f"| `{k}` | {_param_value(k)} |")
    L += ["",
          "## この文書の限界（正直に）",
          "",
          "- 抜いているのは「条件に出てくる名前」と「参照している設定キー」だけです。",
          "  条件の意味（大なりか小なりか、どちらの向きか）は抜いていません。そこは実コードを読みます。",
          "- V9 が良い設計だという保証ではありません。実装がこうなっている、という事実だけです。",
          f"- 出どころ＝`{SRC.relative_to(ROOT)}` の {'／'.join(FUNCS)} と `{PARAMS.relative_to(ROOT)}`。",
          ""]
    body = "\n".join(L)
    h = hashlib.sha256(body.replace("<!-- V9_EXITS_HASH={h} -->\n", "").encode("utf-8")).hexdigest()[:16]
    return body.replace("{h}", h) + "\n"


def selftest() -> int:
    ng = []
    if not SRC.exists():
        ng.append(f"{SRC} が無い")
    for f in FUNCS:
        try:
            _func(f)
        except SystemExit as e:
            ng.append(str(e))
    br = _branches()
    if len(br) < 8:
        ng.append(f"枝が少なすぎる（{len(br)} 件）＝抽出が壊れている疑い")
    if not any(b["reason"] == "TIME_EXIT" for b in br):
        ng.append("TIME_EXIT が抽出できていない")
    if not _tp_keys():
        ng.append("利確の設定キーが抽出できていない")
    if doc() != doc():
        ng.append("実行のたびに中身が変わる")
    if ng:
        print("❌ 自己検査 NG:")
        for x in ng:
            print(f"   - {x}")
        return 1
    print(f"✅ 自己検査 OK（枝 {len(br)} 件・利確キー {len(_tp_keys())} 件・実コードから抽出・hash 安定）")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="V9 の Exit 実装を実コードから機械で表にする（読むだけ）")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.verify:
        if not OUT.exists():
            print(f"❌ {OUT.name} が無い（--write で作る）"); sys.exit(1)
        if OUT.read_text(encoding="utf-8") != doc():
            print(f"❌ {OUT.name} が実体と食い違う＝手で書き換えたか V9 の実装が動いた")
            print("   直し方: python3 scripts/priority_rebuild/gen_v9_exits.py --write"); sys.exit(1)
        print(f"✅ {OUT.name} は実体と一致"); sys.exit(0)
    if a.write:
        OUT.write_text(doc(), encoding="utf-8")
        print(f"[書いた] {OUT.relative_to(ROOT)}（{len(doc().splitlines())} 行）")
        sys.exit(0)
    print(doc())


if __name__ == "__main__":
    main()

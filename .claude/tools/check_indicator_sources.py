#!/usr/bin/env python3
"""check_indicator_sources.py — 指標の資料と設定ファイルが食い違っていないかを照らす（2026-10-07・158回目）。

まこさんの指示（2026-10-07）「とにかくすべて完璧に修正して。毎回チェックでミスがあり、やりなおしで膨大な時間がかかるのを改善してほしい」。

★なぜ要るか（実測 2026-10-07）＝指標の資料（調べた値の表3つ）は 2026-10-04 に1回だけ作った。そのあと RCI と前期間pivot の3種を
  「使う」にしたが、資料に行を足す手順も、足りないことを知らせる検査も無かった。気づいたのは、修正対応表（make_fix_plan.py）を
  作り直そうとして止まったとき（3日後）。資料が変わっても設定ファイル（observe_config.json・search_limits.json）を写し直したかを
  見る検査も無かった（資料の表の名前を読む検査・hook は0件）。

照らすもの（2つ）
  ①「使う」の指標（indicator_switch.json の on）が、資料の表3つ（indicator_params_review.json・indicator_params_by_strategy.json・
    indicator_roles_thresholds.json）に全部 在るか。表3つに、「使う」でない指標の行が在っても止める（どちらの向きの食い違いも出す）。
  ②設定ファイルの、資料から写した部分が、いまの資料から写し直したものと1文字も同じか。
    observe_config.json の material_params〜_material_params_pending の塊、search_limits.json の material_param_ranges の塊。
    写し直しは r3_draft_build.py の compute・cfg_block・lim_ranges（設定ファイルに写した道具そのもの）で作る＝同じ写し方を2か所に書かない。

使い方: python3 .claude/tools/check_indicator_sources.py           （照らして、食い違いを全部 出す・あれば終了コード 1）
        python3 .claude/tools/check_indicator_sources.py --only-1   （①だけ）
        python3 .claude/tools/check_indicator_sources.py --selftest （食い違いを入れた見本で、照らしが止まるかを見る）
★書き込みはしない（照らすだけ）。恒久71番＝BOT の中身に触らない道具なので、壊すプログラムは作らない。
  ★自己テストは、正しく働くときに「食い違いを見つけて終了コード 1」を返す道具なので、書いた後に働きを確かめる口として置く。
"""
import contextlib
import difflib
import io
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
ST = ROOT / ".claude/state"
SWJ = SDK / ".claude/ratchet/indicator_switch.json"
TABLES = {
    "indicator_params_review.json": ST / "indicator_params_review.json",
    "indicator_params_by_strategy.json": ST / "indicator_params_by_strategy.json",
    "indicator_roles_thresholds.json": ST / "indicator_roles_thresholds.json",
}
CFG = SDK / "scripts/priority_rebuild/observe_config.json"
LIM = SDK / "scripts/priority_rebuild/recipes/search_limits.json"


def kinds_of(p: Path) -> list:
    d = json.loads(p.read_text(encoding="utf-8"))
    rows = d["指標"] if isinstance(d, dict) else d
    return [r["種類"] for r in rows]


def check1(on=None, tables=None) -> list:
    """①。on と tables を渡さなければ本物を読む（自己テストは見本を渡す）。"""
    ng = []
    on = set(json.loads(SWJ.read_text(encoding="utf-8"))["on"]) if on is None else set(on)
    for name, p in (TABLES if tables is None else tables).items():
        ks = kinds_of(p)
        dup = sorted({k for k in ks if ks.count(k) > 1})
        if dup:
            ng.append(f"①{name} に同じ種類の行が2つ以上: {dup}")
        miss = sorted(on - set(ks))
        extra = sorted(set(ks) - on)
        if miss:
            ng.append(f"①「使う」なのに {name} に行が無い（{len(miss)}種）: {miss}")
        if extra:
            ng.append(f"①{name} に行が在るのに「使う」でない（{len(extra)}種）: {extra}")
    return ng


def span(text: str, start: str, end_pat: str, what: str):
    a = text.find(start)
    if a < 0 or text.count(start) != 1:
        raise SystemExit(f"❌ {what} の始まりが1か所でない（照らせない＝止まる）")
    m = re.compile(end_pat).search(text, a)
    if not m:
        raise SystemExit(f"❌ {what} の終わりが見つからない（照らせない＝止まる）")
    return text[a:m.end()]


def diff_pair(what: str, real: str, want: str):
    """②の1組。同じなら None、違えば食い違いの文（違う行と、その中身の先頭40行）。"""
    if real == want:
        return None
    d = list(difflib.unified_diff(real.splitlines(), want.splitlines(), "いまの設定ファイル", "いまの資料から写し直したもの", lineterm="", n=0))
    n = sum(1 for x in d if x[:1] in "+-" and x[:3] not in ("+++", "---"))
    return (f"②{what} が、いまの資料から写し直したものと違う（違う行 {n}）:\n      "
            + "\n      ".join(x[:300] for x in d[:40]) + ("\n      …（41行目から先は省いた）" if len(d) > 40 else ""))


def check2() -> list:
    sys.path.insert(0, str(ST / "indicator_review"))
    with contextlib.redirect_stdout(io.StringIO()):
        import r3_draft_build as r3
        D = r3.compute()
    pairs = [
        ("observe_config.json の material_params〜_material_params_pending",
         span(CFG.read_text(encoding="utf-8"), ' "material_params": {\n', r' "_material_params_pending": .*,\n', "observe_config.json の material_params の塊"),
         r3.cfg_block(D)),
        ("search_limits.json の material_param_ranges",
         span(LIM.read_text(encoding="utf-8"), '  "material_param_ranges": {\n', r'\n  },\n', "search_limits.json の material_param_ranges の塊"),
         r3.lim_ranges(D)),
    ]
    return [x for x in (diff_pair(w, r, t) for w, r, t in pairs) if x]


def selftest() -> int:
    """見本の表と見本の文字で、①と②の照らしが食い違いを見つけるか・同じなら通すかを見る（本物は読まない・書かない）。"""
    ng, n = [], 0
    with tempfile.TemporaryDirectory() as td:
        def tab(rows, wrap):
            p = Path(td) / f"t{len(list(Path(td).iterdir()))}.json"
            p.write_text(json.dumps({"指標": rows} if wrap else rows, ensure_ascii=False), encoding="utf-8")
            return p
        ab = [{"種類": "A"}, {"種類": "B"}]
        t_ok = {"表1": tab(ab, True), "表2": tab(ab, False)}
        cases = [
            ("T1 「使う」と表が同じなら通す", check1({"A", "B"}, t_ok), 0, ""),
            ("T2 「使う」に在って表に無い種類を出す（表ごと）", check1({"A", "B", "C"}, t_ok), 2, "行が無い"),
            ("T3 表に在って「使う」に無い種類を出す（表ごと）", check1({"A"}, t_ok), 2, "「使う」でない"),
            ("T4 同じ種類の行が2つ以上なら出す", check1({"A", "B"}, {"表3": tab(ab + [{"種類": "A"}], True)}), 1, "2つ以上"),
        ]
        for name, got, want_n, word in cases:
            n += 1
            if len(got) != want_n or (word and not all(word in g for g in got)):
                ng.append(f"{name}: 期待 {want_n} 件「{word}」／実際 {got}")
    n += 1
    if diff_pair("見本", "a\nb\n", "a\nb\n") is not None:
        ng.append("T5 同じ文字なのに②が食い違いを出した")
    n += 1
    g = diff_pair("見本", "a\nb\n", "a\nc\n")
    if not g or "違う行 2" not in g:
        ng.append(f"T6 違う文字なのに②が食い違いを出さない・違う行の数が違う: {g}")
    n += 1
    if span("x\n START\n y\n END,\n z", " START\n", r" END,\n", "見本") != " START\n y\n END,\n":
        ng.append("T7 塊の切り出しが違う")
    n += 1
    try:
        span("x\n y\n", " START\n", r" END,\n", "見本")
        ng.append("T8 始まりが無いのに止まらない")
    except SystemExit:
        pass
    for x in ng:
        print(f"  ❌ {x}")
    print(f"{'✅' if not ng else '❌'} check_indicator_sources の自己テスト {n - len(ng)}/{n} pass")
    return 1 if ng else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    ng = check1()
    if "--only-1" not in sys.argv:
        ng += check2()
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        print(f"❌ 指標の資料と設定ファイルの照らし: 食い違い {len(ng)} 件"
              "（①は資料に行を足す・②は r3_draft_build.py の写し方で設定ファイルを写し直す＝設計書と承認が要る）")
        return 1
    print("✅ 指標の資料と設定ファイルの照らし: 食い違い 0 件（①「使う」の指標が資料の表3つに全部 在る"
          + ("" if "--only-1" in sys.argv else "・②設定ファイルが、いまの資料から写したものと同じ") + "）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

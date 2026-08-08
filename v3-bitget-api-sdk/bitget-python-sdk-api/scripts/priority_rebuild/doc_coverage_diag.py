#!/usr/bin/env python3
"""doc_coverage_diag.py — 文書を作り直したときに「消えた中身」を機械で一覧に出す（読み取り専用の診断）

なぜ要るか
--------------------------------------------------------------------------
2026-08-08 に CC は cat_requirements.md の1行（H1）を「まこさんが読める日本語」に
書き直す例を出した。その1行の書き直しだけで、元に在った4つを落とした。

  1. 2つ目の守る仕組み（eval_engine.assert_position_cap）
  2. その検査が正しいと確かめてあること（既知答えテスト担保）
  3. 出典（CLAUDE §0-2 ／ 類型H）
  4. 「任意の時点で」の意味（「いつでも」に縮めて、元の意味が消えた）

落としたことに気づいたのは まこさんで、CC ではない。cat_requirements.md は 374 行ある。
この形のまま作り直すと、まこさんが 374 行ぜんぶを旧版と突き合わせることになる。
＝この道具は、その突き合わせを機械にやらせるためのもの。

何をするか / 何をしないか
--------------------------------------------------------------------------
  する   : 旧版の中身が新版に見当たらないものを、全部 一覧にして出す
  しない : 消してよいかどうかの判断。★それは まこさんが1件ずつ決める。
           この道具は「見当たりません」と言うだけで、消す・残すを決めない。

どうやって「見当たらない」と判定するか（★恣意で選ばない）
--------------------------------------------------------------------------
文字列の完全一致で見ると、書き直した瞬間に全部が「消えた」になって使えない。
そこで「書き直しても消えないはずのもの」を粒として機械で抜き、新版に在るかを見る。

  粒A 名前     : 関数名・ファイル名・設定名（例 score.assert_hard_constraints / periods.py）
  粒B 数値     : 0.12 / $1,900 / 0.00014 / 70%
  粒C 出典     : §0-2 / 類型H / H1 / L-179 / E31
  粒D 逐語     : かぎ括弧「」の中身（まこさんの発言はここに入る）

粒で捕まらない中身（上の 4 番のような言い換え）は、粒とは別に
「文そのものの対応」を語の重なり率で出す。旧版の各行に対して、新版で一番 近い行と
その重なり率を並べる。重なり率が低い行＝新版に対応が無い疑いが濃い行。

★出しすぎる側に倒してある（fail-closed）。見落として通すより、多めに出して
まこさんに切ってもらうほうが安全。

使い方
--------------------------------------------------------------------------
  python3 doc_coverage_diag.py --old <旧版.md> --new <新版.md>            # 一覧を画面に出す
  python3 doc_coverage_diag.py --old <旧版.md> --new <新版.md> --out X.md # ファイルにも書く
  python3 doc_coverage_diag.py --selftest                                  # 番人（既知答え）
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

# --- 粒を抜く規則（★ここに書いていない種類は抜けない＝規則を足すときは番人も足す）------------
GRAIN_RULES: list[tuple[str, str]] = [
    # (種類, 正規表現)
    ("名前", r"`([^`\n]{2,80})`"),                                  # バッククォートで囲まれたもの
    ("名前", r"\b([A-Za-z_][A-Za-z0-9_]*\.(?:py|md|json|csv|sh|parquet))\b"),
    ("名前", r"\b([A-Za-z_][A-Za-z0-9_]*\.[a-z_][A-Za-z0-9_]*)\s*\("),   # 関数の呼び出し
    ("名前", r"\b([A-Z][A-Z0-9_]{3,})\b"),                          # 大文字の設定名 ALLOW_LIVE_ORDERS
    ("数値", r"(\$[\d,]+(?:\.\d+)?)"),                              # $1,900
    ("数値", r"(\d+\.\d+)"),                                        # 0.12 / 0.00014
    ("数値", r"(\d+(?:,\d{3})+)"),                                  # 1,432
    ("数値", r"(\d+ *%)"),                                          # 70%
    ("出典", r"(§[\dA-Za-z][\d.\-A-Za-z]*)"),                       # §0-2 / §4.6
    ("出典", r"(類型[A-H])"),
    ("出典", r"\b(H1[0-6]|H[1-9]|L-\d+|E\d+[a-z]?|R1[0-6]|R[1-9]|D1[0-4]|D[1-9])\b"),
    ("逐語", r"「([^」\n]{6,200})」"),
]

# 抜けても意味を持たない、どの文書にも出る語（★ここを増やすと見落としが増えるので最小限）
GRAIN_STOP = {"CC", "OK", "NG", "TODO", "NOTE", "JSON", "CSV", "BTC", "USDT", "API", "URL", "AND", "OR"}

_WORD = re.compile(r"[0-9A-Za-z_§.%$,\-]+|[ぁ-んァ-ヶ一-龥]{2,}")


def _lines(path: pathlib.Path) -> list[tuple[int, str]]:
    """行番号つきで中身の行だけ返す（空行・区切り線・表の罫線は落とす）。"""
    out = []
    for i, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = ln.strip()
        if not s or set(s) <= set("-|= "):        # 空行・---- ・ |---|---| 等
            continue
        out.append((i, s))
    return out


def grains(text: str) -> set[tuple[str, str]]:
    """1行から粒を抜く。戻りは (種類, 中身) の集合。"""
    got: set[tuple[str, str]] = set()
    for kind, pat in GRAIN_RULES:
        for m in re.finditer(pat, text):
            g = m.group(1).strip()
            if not g or g in GRAIN_STOP:
                continue
            if kind == "名前" and len(g) < 3:
                continue
            got.add((kind, g))
    return got


def _words(s: str) -> set[str]:
    return {w for w in _WORD.findall(s) if len(w) >= 2}


def _best_match(old_line: str, new_index: list[tuple[int, str, set[str]]]) -> tuple[float, int, str]:
    """旧版の1行に一番 近い新版の行と、語の重なり率を返す。"""
    ow = _words(old_line)
    if not ow:
        return (1.0, 0, "")
    best = (0.0, 0, "")
    for ln, s, nw in new_index:
        if not nw:
            continue
        r = len(ow & nw) / len(ow)
        if r > best[0]:
            best = (r, ln, s)
    return best


def run(old_path: pathlib.Path, new_path: pathlib.Path, thresh: float = 0.5) -> tuple[str, int]:
    old = _lines(old_path)
    new = _lines(new_path)
    new_text = "\n".join(s for _, s in new)
    new_index = [(ln, s, _words(s)) for ln, s in new]

    # --- 検査1 粒が新版に見当たらない ---
    missing_grains: list[tuple[int, str, str, str]] = []   # (旧行番号, 種類, 粒, 旧行)
    seen_ok: set[tuple[str, str]] = set()
    for ln, s in old:
        for kind, g in sorted(grains(s)):
            if (kind, g) in seen_ok:
                continue
            if g in new_text:
                seen_ok.add((kind, g))
                continue
            missing_grains.append((ln, kind, g, s))

    # --- 検査3 旧版に在る語が、新版に1文字も無い ---
    #     粒（名前・数値・出典・逐語）で捕まらない日本語のかたまりを拾う。
    #     例＝「既知答えテスト担保」は名前でも数値でも出典でも逐語でもないので検査1 では出ない。
    #     ★語に分けるのは機械なので、CC が「重要な語」を選ぶ余地がない（恣意が入らない）。
    old_words: dict[str, tuple[int, str]] = {}
    for ln, s in old:
        for w in _words(s):
            old_words.setdefault(w, (ln, s))
    missing_words = sorted(
        ((w, old_words[w][0], old_words[w][1]) for w in old_words if w not in new_text),
        key=lambda x: (-len(x[0]), x[1]),
    )

    # --- 検査2 行そのものの対応が薄い ---
    weak_lines: list[tuple[int, float, str, int, str]] = []
    for ln, s in old:
        r, nln, ns = _best_match(s, new_index)
        if r < thresh:
            weak_lines.append((ln, r, s, nln, ns))

    L: list[str] = []
    L.append(f"# 消えた中身の一覧 — {old_path.name} → {new_path.name}")
    L.append("")
    L.append("**この一覧は「見当たりません」と言うだけです。消してよいかどうかは決めません。**")
    L.append("**1件ずつ決めるのは まこさんです。**")
    L.append("")
    L.append(f"- 旧版の中身の行: {len(old)} 行（{old_path}）")
    L.append(f"- 新版の中身の行: {len(new)} 行（{new_path}）")
    L.append("")
    L.append("## 検査1｜旧版に在った「名前・数値・出典・逐語」が、新版に1文字も無い")
    L.append("")
    L.append(f"**{len(missing_grains)} 件。**")
    L.append("")
    if missing_grains:
        L.append("| 旧版の行 | 種類 | 見当たらないもの | 旧版のその行 |")
        L.append("|---|---|---|---|")
        for ln, kind, g, s in missing_grains:
            L.append(f"| {ln} | {kind} | `{g}` | {s[:110].replace('|', '\\|')} |")
    else:
        L.append("なし。")
    L.append("")
    L.append("## 検査3｜旧版に在った語が、新版に1文字も無い（長い語＝重い語から順に）")
    L.append("")
    L.append(f"**{len(missing_words)} 件。**")
    L.append("")
    if missing_words:
        L.append("| 旧版の行 | 見当たらない語 | 旧版のその行 |")
        L.append("|---|---|---|")
        for w, ln, s in missing_words:
            L.append(f"| {ln} | {w} | {s[:110].replace('|', '\\|')} |")
    else:
        L.append("なし。")
    L.append("")
    L.append(f"## 検査2｜旧版の行に対応しそうな行が、新版に見当たらない（語の重なりが {thresh:.0%} 未満）")
    L.append("")
    L.append(f"**{len(weak_lines)} 行。**")
    L.append("")
    if weak_lines:
        L.append("| 旧版の行 | 重なり | 旧版のその行 | 新版で一番 近い行 |")
        L.append("|---|---|---|---|")
        for ln, r, s, nln, ns in sorted(weak_lines, key=lambda x: x[1]):
            near = f"{nln}: {ns[:60]}" if ns else "（無し）"
            L.append(f"| {ln} | {r:.0%} | {s[:90].replace('|', '\\|')} | {near.replace('|', '\\|')} |")
    else:
        L.append("なし。")
    L.append("")
    return "\n".join(L) + "\n", len(missing_grains) + len(missing_words) + len(weak_lines)


# --------------------------------------------------------------------------
# 番人（既知答え）＝わざと落として、実際に見つかるかを確かめる
# --------------------------------------------------------------------------
_OLD = """# 見本
| H1 | ポジション合計上限 | 任意 t で `sum(active_btc) <= 0.12 BTC`（合計） | CLAUDE §0-2 / 類型H | `score.assert_hard_constraints`（売買記録の時系列 cap・違反は採点拒否・既知答えテスト担保）＋ `eval_engine.assert_position_cap`（点版） |
| H4 | コスト確定値 | maker 0.00014 / taker 0.00042 | exchange_spec | eval_engine 定数 |
まこさんの逐語は「数字が変わってもいいので正しい計算式にしてほしい」です。
"""

_NEW_OK = """# 見本（言い換えただけ・中身は全部 残っている）
H1 は建玉の合計の上限です。任意 t で `sum(active_btc) <= 0.12 BTC` を守ります。
守る仕組みは2つあります。`score.assert_hard_constraints` が売買記録の時系列 cap を見て、
違反したら採点を拒否します。既知答えテスト担保つきです。もう1つは `eval_engine.assert_position_cap` です。
出典は CLAUDE §0-2 と 類型H です。
H4 はコストの確定値です。maker 0.00014 / taker 0.00042。出典は exchange_spec、実装は eval_engine 定数です。
まこさんの逐語は「数字が変わってもいいので正しい計算式にしてほしい」です。
"""

_NEW_BAD = """# 見本（2026-08-08 に CC が実際にやった書き方＝4つ落ちている）
H1 は建玉の合計の上限です。いつでも合計 0.12 BTC を超えません。
`score.assert_hard_constraints` が守ります。
H4 はコストの確定値です。maker 0.00014 / taker 0.00042。出典は exchange_spec、実装は eval_engine 定数です。
まこさんの逐語は「数字が変わってもいいので正しい計算式にしてほしい」です。
"""


def selftest() -> int:
    import tempfile
    ng: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / "old.md").write_text(_OLD, encoding="utf-8")
        (d / "ok.md").write_text(_NEW_OK, encoding="utf-8")
        (d / "bad.md").write_text(_NEW_BAD, encoding="utf-8")

        # 番人1 言い換えただけなら、粒は1件も消えたと言わない
        rep_ok, _ = run(d / "old.md", d / "ok.md")
        n_ok = int(re.search(r"新版に1文字も無い\n\n\*\*(\d+) 件", rep_ok).group(1))
        if n_ok != 0:
            ng.append(f"番人1 失敗＝言い換えただけなのに粒が {n_ok} 件 消えたと言った（誤検知）")

        # 番人2 実際に落とした版なら、落とした中身が名指しで出る
        rep_bad, _ = run(d / "old.md", d / "bad.md")
        for must in ("eval_engine.assert_position_cap", "既知答えテスト担保", "§0-2", "類型H"):
            if must not in rep_bad:
                ng.append(f"番人2 失敗＝落としたのに見つけられなかった: {must}")

        # 番人3 「任意の時点で」を「いつでも」に縮めた行は、検査2 で薄いと出る
        if "任意 t で" not in rep_bad:
            ng.append("番人3 失敗＝言い換えで意味が縮んだ行を、検査2 が拾えていない")

        # 番人4 逐語（かぎ括弧）が消えたら見つける
        (d / "noquote.md").write_text(_NEW_OK.replace(
            "「数字が変わってもいいので正しい計算式にしてほしい」", "（略）"), encoding="utf-8")
        rep_nq, _ = run(d / "old.md", d / "noquote.md")
        if "数字が変わってもいいので正しい計算式にしてほしい" not in rep_nq:
            ng.append("番人4 失敗＝まこさんの逐語が消えたのに見つけられなかった")

    print("=" * 78)
    print("doc_coverage_diag 番人（既知答え）")
    print("=" * 78)
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 4件とも pass（誤検知なし／落とした4つを名指しで検出／逐語の消失も検出）")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="文書を作り直したときに消えた中身を一覧に出す（読み取り専用）")
    ap.add_argument("--old", type=pathlib.Path, help="旧版の .md")
    ap.add_argument("--new", type=pathlib.Path, help="新版の .md")
    ap.add_argument("--out", type=pathlib.Path, help="一覧を書き出す先（省略時は画面のみ）")
    ap.add_argument("--thresh", type=float, default=0.5, help="検査2 の語の重なりの下限（既定 0.5）")
    ap.add_argument("--selftest", action="store_true", help="番人（既知答え）")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(selftest())
    if not a.old or not a.new:
        ap.error("--old と --new の両方が要ります（または --selftest）")
    for p in (a.old, a.new):
        if not p.exists():
            sys.exit(f"❌ ファイルが無い: {p}")

    report, total = run(a.old, a.new, a.thresh)
    print(report)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(report, encoding="utf-8")
        print(f"✅ 書き出した: {a.out}")
    print(f"★合計 {total} 件。消してよいかどうかは この道具は決めません。まこさんが1件ずつ決めます。")


if __name__ == "__main__":
    main()

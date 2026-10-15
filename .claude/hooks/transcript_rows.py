#!/usr/bin/env python3
"""transcript_rows — やり取りの記録（.jsonl）から、会話の本物の行だけを読む共通の関数（2026-10-15・181回目）。

なぜ要るか（実測 2026-10-15）＝この日から、やり取りの記録に api-request-blob の行（Claude Code が API に送った中身の控え）が
入るようになった（10-14 までの記録 53本は0行・10-15 の記録7本で 1,177行）。この行には、それまでの呼び出し（tool_use）と
結果がもう一度 書かれている。行の種類を見ずに数える hook は、1回の呼び出しを2回と数えた
（block_repeat_failure・block_repeat_kind が、1回しか失敗していない相手を「2回 失敗」と止めた）。
まこさん「強制で解決できないの？」「じゃあ、先に直して」（2026-10-15）。

決まり＝type が user か assistant の行だけを返す。同じ uuid の行は1回だけ返す。
  ★記録を読む hook は、json.loads で行を自分で読まず、この rows() を使う（新しい種類の行が足されても、ここだけ直せば済む）。
使い方: from transcript_rows import rows ／ python3 transcript_rows.py --count <記録>（種類ごとの行の数と、返す行の数を出す）
"""
import collections
import json
import sys

KEEP = ("user", "assistant")


def rows(path):
    """会話の本物の行（type が user か assistant）を、記録の順に1回ずつ返す。"""
    seen = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except Exception:                                # noqa: BLE001
                continue
            if not isinstance(o, dict) or o.get("type") not in KEEP:
                continue
            u = o.get("uuid")
            if u:
                if u in seen:
                    continue
                seen.add(u)
            yield o


def _count(path) -> int:
    kinds = collections.Counter()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                kinds[str(json.loads(line).get("type"))] += 1
            except Exception:                                # noqa: BLE001
                kinds["(読めない行)"] += 1
    kept = sum(1 for _ in rows(path))
    print("種類ごとの行の数＝" + "・".join(f"{k} {v}" for k, v in kinds.most_common()))
    print(f"rows() が返す行＝{kept}")
    return 0


if __name__ == "__main__":
    if "--count" in sys.argv:
        sys.exit(_count(sys.argv[sys.argv.index("--count") + 1]))
    print(__doc__)

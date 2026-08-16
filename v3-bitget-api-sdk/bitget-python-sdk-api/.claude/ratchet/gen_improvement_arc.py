#!/usr/bin/env python3
"""gen_improvement_arc.py — 改善アーク表を「改ざんできない源」から自動生成する。

源（まこさん指示 2026-06-27）:
  - テキスト（前提/狙い/内容/方法/採否ラベル）＝ ARC マーカー（<!-- ARC ... -->）。
      今回・過去 iter は ledger.md（git 追跡・追記型・tamper-evident）から。
      今後 iter は acceptance_archive/<iter>.md（承認済み・git 永続・指紋保護）を優先（フォールバック=ledger）。
  - 数字（結果・採点窓 base 比較）＝ score CSV の net_usd（戦略エンジンが eval_engine コストで出した実値・score.py と一致）。
      CC は数字を手書きしない＝改ざん不可。採否ラベルを改ざんしても隣の score.py 数字と矛盾して一目で分かる。
  - 前提 ＝ ARC マーカー（実行引数由来）。

CC は改善アーク表を一切手書きしない（next_step の ARC_TABLE_START〜END を本スクリプトが上書き＝--write）。
"""
import re, sys, glob, hashlib, pandas as pd
from pathlib import Path

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api")
RAT = ROOT / "results/priority_rebuild/ratchet"
LEDGER = ROOT / ".claude/ratchet/ledger.md"
ACC_ARCHIVE = ROOT / ".claude/ratchet/acceptance_archive"
NEXT_STEP = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/next_step.md")

# ★GENERATES＝この道具が作る文書の名乗り（2026-08-16 新設・まこさん決定 A）。
#   ★この道具は next_step.md の ARC_TABLE_START〜END の間だけを書き換えます＝「一部の節」。
#   ★この道具には --verify がありません（2026-08-16 実測）＝古くなっても検出できない。
#     足すかどうかは まこさんが決めます。集める道具＝gen_docmap.py。
GENERATES = [
    (".claude/state/next_step.md", "一部の節"),
]

ARC_RE = re.compile(r"<!--\s*ARC\b(.*?)-->", re.DOTALL)
KV_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"|(\w+)\s*=\s*(\S+)')


def parse_markers(text):
    out = []
    for m in ARC_RE.finditer(text):
        d = {}
        for km in KV_RE.finditer(m.group(1)):
            if km.group(1) is not None:
                d[km.group(1)] = km.group(2)
            else:
                d[km.group(3)] = km.group(4)
        if "iter" in d:
            out.append(d)
    return out


def find_csv(name):
    if not name:
        return None
    for c in (RAT / name, RAT / "archive" / name):
        if c.exists():
            return c
    hits = glob.glob(str(RAT / "**" / name), recursive=True)
    return Path(hits[0]) if hits else None


def win_net(csv_name):
    """CSV（score.py が読む実値）の net 合計・玉数・月数・件数日。CC は手書きしない。"""
    p = find_csv(csv_name)
    if p is None:
        return None
    df = pd.read_csv(p, parse_dates=["entry_time", "exit_time"])
    net = float(df["net_usd"].sum())
    pos = int(df["position_id"].nunique())
    months = int(df["entry_time"].dt.to_period("M").nunique())
    days = max(1, (df["exit_time"].max() - df["entry_time"].min()).days)
    return {"net": net, "month_avg": net / months if months else 0.0, "pos": pos,
            "per_day": pos / days}


def result_str(d):
    s = win_net(d.get("score_csv"))
    return f"月${s['month_avg']:.2f}/${s['net']:.0f}/玉{s['pos']}/{s['per_day']:.2f}日" if s else "（CSV不在）"


def score_vs_base(d):
    """採点窓 net で candidate vs base（score.py 由来の数字・採否ラベルの自己検証用）。"""
    c, b = win_net(d.get("score_csv")), win_net(d.get("base_csv"))
    if c is None:
        return "（CSV不在）"
    if b is None:
        return f"採点窓 ${c['net']:.0f}"
    return f"採点窓 ${c['net']:.0f} vs base ${b['net']:.0f}（{c['net']-b['net']:+.0f}）"


def row(d):
    # 採否＝記録ラベル(マーカー・git tamper-evident) ＋ score.py 採点窓数字(改ざん不可・ラベルの自己検証)
    verdict = f"{d.get('採否','?')}｜{score_vs_base(d)}"
    return (f"| {d['iter']} | {d.get('前提','?')} | {d.get('狙い','?')} | {d.get('内容','?')} | "
            f"{d.get('方法','?')} | {result_str(d)} | {verdict} |")


def collect():
    by_iter = {}
    for d in parse_markers(LEDGER.read_text(encoding="utf-8")):
        by_iter[d["iter"]] = d
    if ACC_ARCHIVE.exists():
        for f in ACC_ARCHIVE.glob("*.md"):
            for d in parse_markers(f.read_text(encoding="utf-8")):
                by_iter[d["iter"]] = d   # acceptance archive 優先（今後・承認済み）
    return sorted(by_iter.values(), key=lambda d: float(d.get("order", 999)))


def build_table():
    markers = collect()
    if not markers:
        sys.exit("ARC マーカーなし（ledger/acceptance_archive に <!-- ARC ... --> を埋める）")
    header = ("| iter | 前提 | 狙い[源:ARCマーカー] | 内容[源:ARCマーカー] | 方法[源:ARCマーカー] | "
              "結果[源:score.py] | 採否[記録ラベル｜score.py採点窓数字] |")
    sep = "|---|---|---|---|---|---|---|"
    return "\n".join([header, sep] + [row(d) for d in markers]), len(markers)


def write_next_step(table):
    txt = NEXT_STEP.read_text(encoding="utf-8")
    h = hashlib.sha256(table.encode("utf-8")).hexdigest()[:12]
    block = (f"<!-- ARC_TABLE_START hash={h} gen=gen_improvement_arc.py ★手書き禁止="
             f"本表は ledger/acceptance の ARC マーカーから自動生成・CC は触らない -->\n{table}\n<!-- ARC_TABLE_END -->")
    pat = re.compile(r"<!-- ARC_TABLE_START.*?<!-- ARC_TABLE_END -->", re.DOTALL)
    if not pat.search(txt):
        sys.exit("next_step に <!-- ARC_TABLE_START --> 〜 <!-- ARC_TABLE_END --> がありません（先に設置）")
    NEXT_STEP.write_text(pat.sub(lambda _: block, txt), encoding="utf-8")
    return h


def main():
    table, n = build_table()
    if "--write" in sys.argv:
        h = write_next_step(table)
        print(f"[next_step に書き込み] {n} iter / hash={h}", file=sys.stderr)
    else:
        print(table)
        print(f"\n[{n} iter 生成・数字=score.py・テキスト=ARCマーカー・--write で next_step 反映]", file=sys.stderr)


if __name__ == "__main__":
    main()

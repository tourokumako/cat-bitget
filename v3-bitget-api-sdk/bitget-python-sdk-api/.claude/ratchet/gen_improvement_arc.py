#!/usr/bin/env python3
"""gen_improvement_arc.py — 改善の経緯の表を「改ざんできない源」から自動生成する。

★2026-08-16（29回目）に作り直しました。まこさんの案（逐語）＝
  「今はengine_tunerそのものを制作中だから改善アークに記録されないということであれば、
    session_worklogから改善経緯を自動生成するとかにしたらいいのでは？」

作る表は2つです。

  表1｜戦略の改善（実験がある回）
    源＝ARC マーカー（<!-- ARC ... -->）。ledger.md（git 追跡・追記型）と
        acceptance_archive/<iter>.md（承認済み・git 永続・指紋保護）から読みます。
    数字＝売買記録CSVの net_usd（戦略エンジンが eval_engine のコストで出した実値・score.py と一致）。
    ★CC は数字を手書きしません＝改ざん不可。
    ★最後の記録は 2026-07-16 です。engine_tuner を作っている間は1件も増えません。

  表2｜道具を作った経緯（実験が無い回）
    源＝ARC-WL マーカー（<!-- ARC-WL ... -->）。.claude/state/session_worklog_YYYYMMDD.md から読みます。
    ★守れること＝あとから worklog を書き換えると、git の差分に出ます。この表も --verify でずれを見つけます。
    ★守れないこと＝最初から嘘を書くことは止められません。worklog は CC が手で書くからです。
      段10 で実験が始まったら、表1（売買記録CSVが源）へ戻します。

出す先（2026-08-16 に変えました）:
  .claude/ratchet/improvement_arc.md ＝ 機械が作る文書。手で書き換えたら --verify が見つけます。
  ★next_step.md には書きません。理由＝next_step.md は毎セッション上書きされるので、
    恒久の記録を置く場所として構造的に弱いためです（恒久の決まり L-410 と同じ理由）。

★pdca_gate.sh / pdca_mark.py には繋いでいません（安全側の hook＝まこさんの承認が別に要る）。
  この2つは いまも next_step.md の ARC_TABLE の区画を見る条件を持ったままです。
  fast-mode を切ると、その条件を満たせずセッションを閉じられません。
  記録先＝next_step.md の §6 の59番。

使い方:
  python3 gen_improvement_arc.py            # 画面に出すだけ
  python3 gen_improvement_arc.py --write    # improvement_arc.md を作り直す
  python3 gen_improvement_arc.py --verify   # 手で書き換えられていないかを見る（ずれたら exit 1）
  python3 gen_improvement_arc.py --selftest # 番人（わざと壊して見つかるか）
"""
import glob
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api")
REPO = ROOT.parent.parent
RAT = ROOT / "results/priority_rebuild/ratchet"
LEDGER = ROOT / ".claude/ratchet/ledger.md"
ACC_ARCHIVE = ROOT / ".claude/ratchet/acceptance_archive"
WORKLOG_DIR = REPO / ".claude/state"
OUT = ROOT / ".claude/ratchet/improvement_arc.md"

# ★GENERATES＝この道具が作る文書の名乗り（2026-08-16 新設・まこさん決定 A）。集める道具＝gen_docmap.py。
GENERATES = [
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/improvement_arc.md", "まるごと"),
]

# ★「ARC」と「ARC-WL」を取り違えないように、後ろの文字まで見て分けます。
ARC_RE = re.compile(r"<!--\s*ARC[ \t]+(.*?)-->", re.DOTALL)
ARCWL_RE = re.compile(r"<!--\s*ARC-WL[ \t]+(.*?)-->", re.DOTALL)
KV_RE = re.compile(r'(\S+?)\s*=\s*"([^"]*)"|(\S+?)\s*=\s*(\S+)')
HASH_RE = re.compile(r"<!--\s*ARC_DOC hash=([0-9a-f]+)[^>]*-->")


def parse_markers(text, rx):
    out = []
    for m in rx.finditer(text):
        d = {}
        for km in KV_RE.finditer(m.group(1)):
            if km.group(1) is not None:
                d[km.group(1)] = km.group(2)
            else:
                d[km.group(3)] = km.group(4)
        out.append(d)
    return out


# ---------------- 表1｜戦略の改善（源＝ARC マーカー＋売買記録CSV） ----------------

def find_csv(name):
    if not name:
        return None
    for c in (RAT / name, RAT / "archive" / name):
        if c.exists():
            return c
    hits = glob.glob(str(RAT / "**" / name), recursive=True)
    return Path(hits[0]) if hits else None


def win_net(csv_name):
    """売買記録CSVの net 合計・玉数・月数・件数日。CC は手書きしない。

    ★行が0本のときは {"empty": True} を返す（None ではない）。
      理由＝「CSVが無い」と「CSVは在るが売買が0本」は別のことなので、表に分けて出す。
      2026-08-16 まで、行が0本のCSVを日付として読もうとして道具が丸ごと落ちていた
      （AttributeError: Can only use .dt accessor with datetimelike values）。
      落ちていた相手＝trades_e36_short_oscillation_5m_shortset1_score.csv（見出し1行だけ）。
    """
    p = find_csv(csv_name)
    if p is None:
        return None
    df = pd.read_csv(p, parse_dates=["entry_time", "exit_time"])
    if len(df) == 0:
        return {"empty": True}
    net = float(df["net_usd"].sum())
    pos = int(df["position_id"].nunique())
    months = int(df["entry_time"].dt.to_period("M").nunique())
    days = max(1, (df["exit_time"].max() - df["entry_time"].min()).days)
    return {"empty": False, "net": net, "month_avg": net / months if months else 0.0,
            "pos": pos, "per_day": pos / days}


def result_str(d):
    s = win_net(d.get("score_csv"))
    if s is None:
        return "（CSV不在）"
    if s["empty"]:
        return "（売買記録0行）"
    return f"月${s['month_avg']:.2f}/${s['net']:.0f}/玉{s['pos']}/{s['per_day']:.2f}日"


def score_vs_base(d):
    """採点窓 net で candidate vs base（売買記録CSV 由来の数字・採否ラベルの自己検証用）。"""
    c, b = win_net(d.get("score_csv")), win_net(d.get("base_csv"))
    if c is None:
        return "（CSV不在）"
    if c["empty"]:
        return "（売買記録0行）"
    if b is None:
        return f"採点窓 ${c['net']:.0f}"
    if b["empty"]:
        return f"採点窓 ${c['net']:.0f}（比べる相手は売買記録0行）"
    return f"採点窓 ${c['net']:.0f} vs base ${b['net']:.0f}（{c['net']-b['net']:+.0f}）"


def collect_strategy():
    by_iter = {}
    if LEDGER.exists():
        for d in parse_markers(LEDGER.read_text(encoding="utf-8"), ARC_RE):
            if "iter" in d:
                by_iter[d["iter"]] = d
    if ACC_ARCHIVE.exists():
        for f in sorted(ACC_ARCHIVE.glob("*.md")):
            for d in parse_markers(f.read_text(encoding="utf-8"), ARC_RE):
                if "iter" in d:
                    by_iter[d["iter"]] = d   # acceptance archive 優先（承認済み）
    return sorted(by_iter.values(), key=lambda d: float(d.get("order", 999)))


def table_strategy(markers):
    head = ("| iter | 前提 | 狙い[源:ARCマーカー] | 内容[源:ARCマーカー] | 方法[源:ARCマーカー] | "
            "結果[源:売買記録CSV] | 採否[記録ラベル｜採点窓の数字] |")
    sep = "|---|---|---|---|---|---|---|"
    rows = [
        (f"| {d['iter']} | {d.get('前提','?')} | {d.get('狙い','?')} | {d.get('内容','?')} | "
         f"{d.get('方法','?')} | {result_str(d)} | {d.get('採否','?')}｜{score_vs_base(d)} |")
        for d in markers
    ]
    return "\n".join([head, sep] + rows)


# ---------------- 表2｜道具を作った経緯（源＝ARC-WL マーカー） ----------------

def collect_tooling():
    """worklog の ARC-WL マーカーを集める。

    ★sec が無いものは数えない。理由＝説明の文章の中に `<!-- ARC-WL ... -->` と書くと、
      それも印として数えてしまうため。実際に 2026-08-16 に2件 混ざり、表2 が 7件 のはずが
      9件 と出た（`session_worklog_20260816.md` の 1044行目・1059行目）。
      表1 が `iter` の有無で同じことをしているので、そろえた。
    """
    out = []
    for f in sorted(WORKLOG_DIR.glob("session_worklog_*.md")):
        m = re.search(r"session_worklog_(\d{8})\.md$", f.name)
        day = m.group(1) if m else "00000000"
        for d in parse_markers(f.read_text(encoding="utf-8"), ARCWL_RE):
            if "sec" not in d:
                continue
            d["_day"] = f"{day[:4]}-{day[4:6]}-{day[6:]}"
            out.append(d)
    return sorted(out, key=lambda d: (d["_day"], float(d.get("order", 999))))


def table_tooling(markers):
    head = ("| 日付 | 節 | 種類 | 狙い[源:worklog] | 内容[源:worklog] | 方法[源:worklog] | "
            "結果[源:worklog] | 採否[源:worklog] |")
    sep = "|---|---|---|---|---|---|---|---|"
    rows = [
        (f"| {d['_day']} | {d.get('sec','?')} | {d.get('種類','?')} | {d.get('狙い','?')} | "
         f"{d.get('内容','?')} | {d.get('方法','?')} | {d.get('結果','?')} | {d.get('採否','?')} |")
        for d in markers
    ]
    return "\n".join([head, sep] + rows)


# ---------------- 文書を組み立てる ----------------

def build_doc():
    st, tl = collect_strategy(), collect_tooling()
    if not st and not tl:
        sys.exit("マーカーが1件もありません（ledger/acceptance に <!-- ARC ... -->、"
                 "worklog に <!-- ARC-WL ... --> を埋める）")

    body = "\n".join([
        "# improvement_arc.md — 改善の経緯（機械生成・手で書き換えない）",
        "",
        "⚠️ **この文書は `gen_improvement_arc.py` が作ります。手で書き換えないでください。**",
        "`--verify` が、手で書き換えられていないかを見ます（ずれたら止まります）。",
        "",
        "**なぜ手で書かないか。** CC が自分の記憶で書くと、間違えます。都合よく書くこともできます。",
        "まこさん指示 2026-06-27・逐語「全列を改ざんできないように・自動生成」。",
        "",
        "---",
        "",
        f"## 表1｜戦略の改善（{len(st)} 件）",
        "",
        "**源**＝`ledger.md` と `acceptance_archive/` の `<!-- ARC ... -->` マーカー。",
        "**数字の源**＝売買記録CSVの `net_usd`（`score.py` と同じ実値）。**CC は数字を手書きしません。**",
        "",
        table_strategy(st) if st else "（マーカー 0件）",
        "",
        "---",
        "",
        f"## 表2｜道具を作った経緯（{len(tl)} 件）",
        "",
        "**源**＝`.claude/state/session_worklog_YYYYMMDD.md` の `<!-- ARC-WL ... -->` マーカー。",
        "**★守れること**＝あとから worklog を書き換えると、git の差分に出ます。この表も `--verify` がずれを見つけます。",
        "**★守れないこと**＝最初から嘘を書くことは止められません。worklog は CC が手で書くからです。",
        "段10 で実験が始まったら、表1（売買記録CSVが源）へ戻します。",
        "",
        table_tooling(tl) if tl else "（マーカー 0件）",
        "",
    ])
    h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    return body, h, len(st), len(tl)


def doc_text(body, h):
    # body は末尾に改行を1つ持つ（build_doc の join の最後が空文字）。ここで足さない。
    return f"<!-- ARC_DOC hash={h} gen=gen_improvement_arc.py 手書き禁止 -->\n{body}"


def verify():
    if not OUT.exists():
        print(f"❌ {OUT.name} がありません（--write で作る）", file=sys.stderr)
        return 1
    txt = OUT.read_text(encoding="utf-8")
    m = HASH_RE.search(txt)
    if not m:
        print("❌ 指紋の行（ARC_DOC hash=…）がありません＝手で書き換えられた疑い", file=sys.stderr)
        return 1
    # 指紋の行の直後の改行1つだけを外す（rstrip すると本文の末尾の改行まで落ちて必ず不一致になる）
    body = txt[m.end():]
    if body.startswith("\n"):
        body = body[1:]
    now = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    if now != m.group(1):
        print(f"❌ 中身が指紋と合いません（書いてある {m.group(1)} ／ いまの中身 {now}）"
              "＝手で書き換えられた", file=sys.stderr)
        return 1
    fresh, h, ns, nt = build_doc()
    if fresh != body:
        print(f"❌ 源（マーカー・売買記録CSV）が変わっています。`--write` で作り直してください"
              f"（いまの文書 {m.group(1)} ／ 源から作り直すと {h}）", file=sys.stderr)
        return 1
    print(f"✅ improvement_arc.md は源と一致（表1 {ns} 件／表2 {nt} 件・指紋 {h}）")
    return 0


# ---------------- 番人（わざと壊して、見つかることを確かめる） ----------------

def selftest():
    import shutil
    import tempfile
    ng = 0

    def chk(name, cond, extra=""):
        nonlocal ng
        print(f"  {'✅' if cond else '❌'} {name}" + ("" if cond else f"   {extra}"))
        if not cond:
            ng += 1

    # T1 ARC と ARC-WL を取り違えない
    s = '<!-- ARC order=1 iter="x" -->\n<!-- ARC-WL order=1 sec="§1" -->'
    chk("T1 ARC マーカーだけを拾う（ARC-WL を混ぜない）",
        [d.get("iter") for d in parse_markers(s, ARC_RE)] == ["x"])
    chk("T2 ARC-WL マーカーだけを拾う（ARC を混ぜない）",
        [d.get("sec") for d in parse_markers(s, ARCWL_RE)] == ["§1"])

    # T2b 説明の文章の中の `<!-- ARC-WL ... -->` を印として数えない（2026-08-16 に実際に2件 混ざった）
    import shutil as _sh
    import tempfile as _tf
    _d2 = Path(_tf.mkdtemp())
    (_d2 / "session_worklog_20260101.md").write_text(
        '<!-- ARC-WL order=1 sec="§1" 狙い="ほんもの" -->\n'
        "説明の文章です。新しい印＝`<!-- ARC-WL ... -->` と書きます。\n"
        '<!-- ARC-WL order=2 sec="§2" 狙い="ほんもの2" -->\n', encoding="utf-8")
    global WORKLOG_DIR
    _k2 = WORKLOG_DIR
    WORKLOG_DIR = _d2
    try:
        _got = [d.get("sec") for d in collect_tooling()]
        chk("T2b 説明の文章の中の印を数えない（sec が無いものは飛ばす）",
            _got == ["§1", "§2"], f"← {_got}")
    finally:
        WORKLOG_DIR = _k2
        _sh.rmtree(_d2, ignore_errors=True)

    # T3〜T6 行が0本の売買記録CSVで落ちない（2026-08-16 に道具が丸ごと落ちていた原因）
    tmp = Path(tempfile.mkdtemp())
    cols = "entry_time,exit_time,position_id,net_usd\n"
    (tmp / "empty.csv").write_text(cols, encoding="utf-8")
    (tmp / "one.csv").write_text(cols + "2026-03-01 00:00:00,2026-03-01 01:00:00,1,10.5\n",
                                encoding="utf-8")
    global RAT
    keep_rat = RAT
    RAT = tmp
    try:
        e = win_net("empty.csv")
        chk("T3 行が0本の売買記録CSVでも落ちない", isinstance(e, dict) and e.get("empty") is True, f"← {e}")
        chk("T4 行が0本は「（売買記録0行）」と出す（CSV不在と混ぜない）",
            result_str({"score_csv": "empty.csv"}) == "（売買記録0行）",
            f"← {result_str({'score_csv': 'empty.csv'})}")
        o = win_net("one.csv")
        chk("T5 ふつうの売買記録CSVはこれまでどおり数える",
            bool(o) and not o["empty"] and abs(o["net"] - 10.5) < 1e-9 and o["pos"] == 1, f"← {o}")
        chk("T6 無いCSVは「（CSV不在）」のまま",
            result_str({"score_csv": "no_such_file.csv"}) == "（CSV不在）")
    finally:
        RAT = keep_rat
        shutil.rmtree(tmp, ignore_errors=True)

    # T7・T8 指紋が中身に対応する／1文字 変えると合わなくなる
    body, h, ns, nt = build_doc()
    chk("T7 指紋は中身から作られている",
        hashlib.sha256(body.encode("utf-8")).hexdigest()[:12] == h)
    chk("T8 中身を1文字 変えると指紋が合わなくなる",
        hashlib.sha256((body + " ").encode("utf-8")).hexdigest()[:12] != h)

    # T9 --verify が「手で書き換えられた文書」を見つける
    global OUT
    keep_out = OUT
    tmp2 = Path(tempfile.mkdtemp())
    OUT = tmp2 / "improvement_arc.md"
    try:
        OUT.write_text(doc_text(body, h), encoding="utf-8")
        chk("T9 作り直した直後は --verify が通る", verify() == 0)
        OUT.write_text(doc_text(body, h).replace("改善の経緯", "改善の経緯（手で足した文）", 1),
                       encoding="utf-8")
        chk("T10 手で1行 書き換えると --verify が見つける", verify() == 1)
        OUT.write_text(body, encoding="utf-8")          # 指紋の行ごと消す
        chk("T11 指紋の行を消しても --verify が見つける", verify() == 1)
        OUT.unlink()
        chk("T12 文書が無ければ --verify が止まる", verify() == 1)
    finally:
        OUT = keep_out
        shutil.rmtree(tmp2, ignore_errors=True)

    # T13 源が空だと止まる
    keep = (LEDGER, ACC_ARCHIVE, WORKLOG_DIR)
    try:
        globals()["LEDGER"] = Path("/no/such/ledger.md")
        globals()["ACC_ARCHIVE"] = Path("/no/such/acc")
        globals()["WORKLOG_DIR"] = Path("/no/such/state")
        try:
            build_doc()
            chk("T13 マーカーが0件だと止まる", False, "← 止まらなかった")
        except SystemExit:
            chk("T13 マーカーが0件だと止まる", True)
    finally:
        globals()["LEDGER"], globals()["ACC_ARCHIVE"], globals()["WORKLOG_DIR"] = keep

    chk("T14 実物で表が2つとも作れる", ns > 0 and nt > 0, f"← 表1 {ns} 件／表2 {nt} 件")

    total = 15
    print(f"\n番人: {total - ng}/{total} pass")
    sys.exit(1 if ng else 0)


def main():
    if "--selftest" in sys.argv:
        selftest()
    if "--verify" in sys.argv:
        sys.exit(verify())
    body, h, ns, nt = build_doc()
    if "--write" in sys.argv:
        OUT.write_text(doc_text(body, h), encoding="utf-8")
        print(f"[書き込み] {OUT.name} ／ 表1 {ns} 件・表2 {nt} 件・指紋 {h}", file=sys.stderr)
    else:
        print(doc_text(body, h))
        print(f"[表1 {ns} 件・表2 {nt} 件・--write で {OUT.name} に反映]", file=sys.stderr)


if __name__ == "__main__":
    main()

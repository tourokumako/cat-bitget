#!/usr/bin/env python3
# require_read_plan_before_design.py — 設計書を書く前に「読むもの」を まこさんに宣言したか（読むもの宣言ゲート）
#
# まこさん指示（2026-09-09・逐語）＝「全体を把握下うえで設計書書けよ。まじでとんでもないな。。話にならない。
#   設計書書く前に読むものを私に宣言するというフローを入れろ」。
# なぜ要るか＝93回目の CC は、M1 の文書（engine_tuner_milestones.md＝マイルストーン M1〜M6 の一覧）を
#   開かずに M2-E-2 の設計書を書いた。乱数を消す工事を「M2-E-2 の直後に別の1変更」と提案し、
#   まこさんが決めたマイルストーンの順番（M3・M4 がその工事そのもの）を勝手に入れ替える形になった。
#   既存の必読ゲート（require_source_read_before_acceptance）は「本文で読んだと書いたものを開いたか」を見るだけで、
#   「何を読むべきか」を まこさんに先に見せる所が無かった。
#
# 何をするか＝.claude/state/acceptance.md（と *_design.md）を Write/Edit する瞬間に、次を見る。
#   1. 読むもの宣言 .claude/state/design_read_plan.md が在る
#   2. 宣言の「設計書:」の名前が、書こうとしている設計書の目印（ARC iter="…"）と同じ
#   3. 宣言に「まこさんの OK:」の行が在り、空でない（★逐語を写す。真偽は機械には分からない＝限界）
#   4. 宣言をチャットに貼った印（design_read_plan_posted＝宣言の sha256）が一致する
#   5. （2026-10-01 に外した）宣言の表に書いた「読むもの」を、全部 Read tool で開いている（read_log.txt）
#      ＝開いた記録しか見ず、開くだけの読みでトークンを使わせていた。中身を使ったかは Stop の require_read_used が見る
#   6. 設計書の中身に engine_tuner の文字が在れば、宣言に engine_tuner_milestones.md と
#      engine_tuner_milestones2.md（全体のマイルストーン）が入っている
#
# 宣言の型（.claude/state/design_read_plan.md）
#   【読むもの宣言】
#   設計書: <ARC iter の名前>
#   まこさんの OK: <逐語>（OK が出るまでは空のままにする＝空だと止まる）
#   | # | 読むもの（パス） | 範囲 | なぜ |
#   |---|---|---|---|
#   | 1 | .claude/ratchet/engine_tuner_milestones.md | 全文 | 全体のマイルストーン |
#
# 印の作り方（チャットに貼ったあと）
#   shasum -a 256 .claude/state/design_read_plan.md | awk '{print $1}' > .claude/state/design_read_plan_posted
#
# 限界（正直に）＝「まこさんの OK:」の逐語は CC が書く＝嘘を書けば通る（やり取りの記録で まこさんが見分ける）。
#   read_log は「1行でも開けば読んだ」になる（既存の必読ゲートと同じ）。印の偽造は見抜けない。
#
# 使い方＝hook（stdin に json）／ --selftest（番人）／ --check（宣言の中身だけ見る・貼る前の口）

import glob
import hashlib
import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
STATE = os.path.join(ROOT, ".claude", "state")
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
PLAN = os.path.join(STATE, "design_read_plan.md")
MARK = os.path.join(STATE, "design_read_plan_posted")
READ_LOG = os.path.join(STATE, "read_log.txt")
MILESTONE_DOCS = ("engine_tuner_milestones.md", "engine_tuner_milestones2.md")


def _read(p):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def plan_rows(text):
    """表の行（| # | パス | 範囲 | なぜ |）からパスを返す。"""
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2 or not re.fullmatch(r"\d+", cells[0]):
            continue
        p = cells[1].strip("`").strip()
        if p:
            out.append(p)
    return out


def _line(text, prefix):
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith(prefix):
            return s[len(prefix):].strip()
    return None


def _opened(path, log):
    base = os.path.basename(path.rstrip("/"))
    tail = path.lstrip("./")
    for l in log:
        l = l.strip()
        if not l:
            continue
        if l.endswith(tail) or os.path.basename(l) == base:
            return True
    return False


def check(plan_text, mark_text, log_lines, design_text, need_milestones):
    """問題の一覧を返す（空なら通る）。"""
    ng = []
    if not plan_text.strip():
        return ["読むもの宣言（design_read_plan.md）が無い＝設計書を書く前に、読むものを まこさんに宣言する"]
    if "【読むもの宣言】" not in plan_text:
        ng.append("宣言の1行目に【読むもの宣言】が無い")
    name = _line(plan_text, "設計書:")
    m = re.search(r'ARC iter="([^"]+)"', design_text or "")
    iter_name = m.group(1) if m else None
    if not name:
        ng.append("「設計書:」の行が無い（ARC iter の名前を書く）")
    elif iter_name and name != iter_name:
        ng.append(f"宣言の設計書（{name}）と、書こうとしている設計書の目印（{iter_name}）が違う")
    ok = _line(plan_text, "まこさんの OK:")
    if ok is None:
        ng.append("「まこさんの OK:」の行が無い")
    elif not ok:
        ng.append("「まこさんの OK:」が空＝まこさんの OK が出るまで設計書は書けない（逐語を写す）")
    h = hashlib.sha256(plan_text.encode("utf-8")).hexdigest()
    if (mark_text or "").strip() != h:
        ng.append("宣言をチャットに貼った印（design_read_plan_posted）が無い、または宣言を書き換えた後で貼り直していない")
    rows = plan_rows(plan_text)
    if not rows:
        ng.append("宣言の表に読むものが1つも無い")
    # ★2026-10-01（142回目・まこさん「開くだけは確認ではない」「修正しろ」）＝「宣言の全部を Read で開いたか」の検査を外した。
    #   開いた記録だけを数えるので、中身を使わない開き直しでトークンを使わせていた（54本を開いた事案）。
    #   読んだ中身を判断に使ったかは、Stop の require_read_used が返信の「ファイル名:行番号」で見る。
    if need_milestones:
        for d in MILESTONE_DOCS:
            if not any(r.endswith(d) for r in rows):
                ng.append(f"engine_tuner の設計書なのに、宣言に全体のマイルストーン {d} が無い")
    return ng


def cli_check():
    plan = _read(PLAN)
    log = _read(READ_LOG).splitlines()
    ng = check(plan, _read(MARK), log, _read(os.path.join(STATE, "acceptance.md")), True)
    ng = [x for x in ng if "印（design_read_plan_posted）" not in x]   # 貼る前の口＝印は見ない
    if ng:
        print(f"❌ 不足 {len(ng)} 件")
        for i, x in enumerate(ng, 1):
            print(f"   {i}. {x}")
        return 1
    print("✅ 宣言の中身は通ります。チャットに貼って印を作れば hook を通ります。")
    return 0


def hook_main():
    raw = sys.stdin.read()
    try:
        d = json.loads(raw)
    except Exception:
        sys.exit(0)
    if d.get("agent_type"):
        sys.exit(0)
    ti = d.get("tool_input") or {}
    fp = str(ti.get("file_path") or "")
    if not fp:
        sys.exit(0)
    fpn = os.path.normpath(fp if os.path.isabs(fp) else os.path.join(ROOT, fp))
    base = os.path.basename(fpn)
    if not (base == "acceptance.md" or base.endswith("_design.md")):
        sys.exit(0)
    body = ti.get("content")
    if not isinstance(body, str):
        body = _read(fpn)
    need_ms = "engine_tuner" in (body or "")
    plan = _read(PLAN)
    ng = check(plan, _read(MARK), _read(READ_LOG).splitlines(), body, need_ms)
    if not ng:
        sys.exit(0)
    e = sys.stderr
    print("🔒 [読むもの宣言ゲート] 設計書を書く前に、読むものを まこさんに宣言して OK をもらってください（まこさん指示 2026-09-09「設計書書く前に読むものを私に宣言するというフローを入れろ」）。", file=e)
    for x in ng:
        print("   ・" + x, file=e)
    print(f"   宣言の置き場＝{PLAN}（型は この hook の冒頭）", file=e)
    print(f"   印の作り方＝shasum -a 256 \"{PLAN}\" | awk '{{print $1}}' > \"{MARK}\"", file=e)
    print("（解除の合言葉はありません）", file=e)
    sys.exit(2)


def selftest():
    import tempfile
    tmp = tempfile.mkdtemp()
    design = '<!-- ARC iter="x-20260909" -->\nengine_tuner を直す\n'
    good = ("【読むもの宣言】\n設計書: x-20260909\nまこさんの OK: 「OK」\n"
            "| # | 読むもの | 範囲 | なぜ |\n|---|---|---|---|\n"
            "| 1 | .claude/ratchet/engine_tuner_milestones.md | 全文 | 全体 |\n"
            "| 2 | .claude/ratchet/engine_tuner_milestones2.md | 全文 | M2 |\n")
    log = ["/a/.claude/ratchet/engine_tuner_milestones.md", "/a/.claude/ratchet/engine_tuner_milestones2.md"]
    h = hashlib.sha256(good.encode("utf-8")).hexdigest()
    cases = [
        ("T1 正しい宣言＋印＋全部 開いた → 通る", good, h, log, design, True, None),
        ("T2 宣言が無い → 止まる", "", h, log, design, True, "宣言（design_read_plan.md）が無い"),
        ("T3 OK が空 → 止まる", good.replace("まこさんの OK: 「OK」", "まこさんの OK:"), None, log, design, True, "OK が出るまで"),
        ("T4 印が古い → 止まる", good, "deadbeef", log, design, True, "印（design_read_plan_posted）"),
        ("T5 開いていないものが在っても止めない（2026-10-01 に開いたかの検査を外した）→ 通る", good, h, log[:1], design, True, None),
        ("T6 設計書の名前が違う → 止まる", good, h, log, design.replace("x-20260909", "y-1"), True, "目印"),
        ("T7 engine_tuner の設計書なのに全体のマイルストーンが無い → 止まる",
         good.replace("| 1 | .claude/ratchet/engine_tuner_milestones.md | 全文 | 全体 |\n", ""), None, log, design, True, "全体のマイルストーン"),
        ("T8 engine_tuner でない設計書はマイルストーンを求めない → 通る",
         good.replace("| 1 | .claude/ratchet/engine_tuner_milestones.md | 全文 | 全体 |\n", ""), None,
         log, '<!-- ARC iter="x-20260909" -->\nhook を直す\n', False, None),
    ]
    ng = 0
    for name, plan, mark, lg, ds, need, want in cases:
        if mark is None:
            mark = hashlib.sha256(plan.encode("utf-8")).hexdigest()
        r = check(plan, mark, lg, ds, need)
        ok = (not r) if want is None else any(want in x for x in r)
        print(f"  {'✅' if ok else '❌'} {name}" + ("" if ok else f" ← {r}"))
        ng += not ok
    print(f"\n番人: {len(cases) - ng}/{len(cases)} pass")
    return 1 if ng else 0


# ════════════════════════════════════════════════════════════════════════════
# 宣言を作る口（2026-09-28・132回目・まこさん指示「自動生成」「ヌケモレ出るから、手打ちしない」）
#
# 元データ .claude/state/read_plan_src.json に人が書くのは、文（何の設計書か・なぜ読むか・入れないもの）と、
# 読むものごとの「パス・探す語・なぜ」だけ。行番号・行数・パスの実在は、この口が実物から出す。
#   --write        元データから宣言を作る（パスが無い・探す語が無い・名前が2つ以上 当たる → 書かずに止まる）
#   --verify       いまの宣言が、元データと実物から作った物と同じか（手の書き換え・行のずれを見る）
#   --ok "逐語"    まこさんの OK の逐語を元データに書き、宣言を作り直す
# ★全体のマイルストーン2本は、元データに無くても必ず先頭に足す（入れ忘れを防ぐ）。
# ★（2026-10-01 にやめた）「壊すプログラムを探す相手」に書いたファイル名で、壊すプログラムを全部 足す形は外した。
# ★印（design_read_plan_posted）は作らない＝チャットに貼った後に作る物だから。
# ════════════════════════════════════════════════════════════════════════════

PLAN_SRC = os.path.join(STATE, "read_plan_src.json")
BREAKS = os.path.join(ROOT, ".claude", "breaks")
MILESTONE_PATHS = [
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones.md",
     ["## M2｜"], "全体のマイルストーン（恒久68番で必ず読む）"),
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md",
     ["## 🔴 ★M2 で作っている物"], "M2 の全体（恒久68番で必ず読む・M2 の作業の前に毎回 開く節）"),
]
SKIP_DIRS = {".git", "__pycache__", "node_modules", "audits", "archive"}


def _resolve(p):
    """パス（リポジトリからの相対・または名前だけ）を実物に当てる。戻り＝(相対パス, 問題)。"""
    full = os.path.join(ROOT, p)
    if "/" in p:
        return (p, None) if os.path.isfile(full) else (p, f"ファイルが無い: {p}")
    hits = []
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        if p in fns:
            hits.append(os.path.relpath(os.path.join(dp, p), ROOT))
    if len(hits) == 1:
        return hits[0], None
    if not hits:
        return p, f"名前だけのファイルが見つからない: {p}"
    return p, f"名前だけのファイルが {len(hits)} か所に在る（パスで書く）: {p} → {', '.join(hits[:3])}"


def _lines_of(rel):
    return _read(os.path.join(ROOT, rel)).splitlines()


def _where(rel, words):
    """探す語ごとの最初の行番号。戻り＝(「語」＝N行目 の並び, 問題の並び)。"""
    lines = _lines_of(rel)
    got, ng = [], []
    for w in words:
        n = next((i for i, ln in enumerate(lines, 1) if w in ln), None)
        if n is None:
            ng.append(f"探す語が {rel} に無い: {w}")
        else:
            got.append(f"「{w}」＝{n}行目")
    return got, ng


def _breaks_for(names):
    """壊すプログラムのうち、names のどれかの名前を本文に持つ物（相対パス）。"""
    out = []
    for p in sorted(glob.glob(os.path.join(BREAKS, "*.sh"))):
        body = _read(p)
        if any(n in body for n in names):
            out.append(os.path.relpath(p, ROOT))
    return out


def build_plan(src):
    """元データから宣言の本文を作る。戻り＝(本文, 問題の並び)。"""
    ng = []
    items = list(src.get("読むもの") or [])
    have = {it.get("パス") for it in items}
    for mp, words, why in reversed(MILESTONE_PATHS):
        if mp not in have:
            items.insert(0, {"パス": mp, "探す語": words, "なぜ": why})
    # ★2026-10-01（142回目）＝壊すプログラムを名前の一致で全部 宣言に足すのをやめた。直す相手と関係の無い物まで入り
    #   （54本のうち直す行を探すのは約10本）、全部を開かせていた。壊すプログラムは承認のときに承認のプログラムが走らせる。
    rows = []
    for i, it in enumerate(items, 1):
        rel, prob = _resolve(str(it.get("パス") or ""))
        if prob:
            ng.append(prob)
            continue
        n_all = len(_lines_of(rel))
        words = it.get("探す語") or []
        got, bad = _where(rel, words)
        ng += bad
        rng = "・".join(got) if words else f"全文（{n_all}行）"
        if words:
            rng += f"（全{n_all}行）"
        rows.append(f"| {i} | {rel} | {rng} | {str(it.get('なぜ') or '').replace('|', '／')} |")
    if not src.get("設計書"):
        ng.append("元データに「設計書」（ARC iter の名前）が無い")
    head = [
        "【読むもの宣言】",
        f"設計書: {src.get('設計書', '')}",
        f"まこさんの OK: {src.get('まこさんの OK', '')}",
        "",
        "★この宣言は require_read_plan_before_design.py --write が、元データ .claude/state/read_plan_src.json と実物から作った（手で書き換えない・--verify で見る）。",
        f"★**何の設計書か**：{src.get('何の設計書か', '')}",
        f"★**なぜ読むか（全体）**：{src.get('なぜ読むか', '')}",
        f"★**入れないもの**：{src.get('入れないもの', '')}",
    ]
    if src.get("前の宣言"):
        head.append(f"★**前の宣言**：{src['前の宣言']}")
    body = "\n".join(head + ["", "| # | 読むもの（パス） | 範囲 | なぜ読むか |", "|---|---|---|---|"] + rows) + "\n"
    return body, ng


def _load_src():
    try:
        return json.loads(_read(PLAN_SRC))
    except Exception as e:
        print(f"❌ 元データが読めない: {PLAN_SRC}（{e}）")
        return None


def cli_write():
    src = _load_src()
    if src is None:
        return 1
    body, ng = build_plan(src)
    if ng:
        print(f"❌ 書きません。問題 {len(ng)} 件:")
        for x in ng:
            print(f"   ・{x}")
        return 1
    with open(PLAN, "w", encoding="utf-8") as f:
        f.write(body)
    n = sum(1 for ln in body.splitlines() if re.match(r"^\| \d+ \|", ln))
    print(f"✅ --write: {PLAN}（読むもの {n} 件）。チャットに貼ったら印を作る:")
    print(f"   shasum -a 256 \"{PLAN}\" | awk '{{print $1}}' > \"{MARK}\"")
    return 0


def cli_verify():
    src = _load_src()
    if src is None:
        return 1
    body, ng = build_plan(src)
    if ng:
        print(f"❌ 元データか実物に問題 {len(ng)} 件:")
        for x in ng:
            print(f"   ・{x}")
        return 1
    if _read(PLAN) != body:
        print("❌ --verify: いまの宣言は、元データと実物から作った物と違う（手で書き換えた・行がずれた）。--write で作り直す")
        return 1
    print("✅ --verify: 宣言は元データと実物から作ったまま")
    return 0


def cli_ok(words):
    src = _load_src()
    if src is None:
        return 1
    src["まこさんの OK"] = words
    with open(PLAN_SRC, "w", encoding="utf-8") as f:
        json.dump(src, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return cli_write()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--check" in sys.argv:
        sys.exit(cli_check())
    if "--write" in sys.argv:
        sys.exit(cli_write())
    if "--verify" in sys.argv:
        sys.exit(cli_verify())
    if "--ok" in sys.argv:
        sys.exit(cli_ok(sys.argv[sys.argv.index("--ok") + 1]))
    hook_main()

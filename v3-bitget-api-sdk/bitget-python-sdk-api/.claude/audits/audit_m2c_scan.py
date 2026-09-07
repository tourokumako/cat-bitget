#!/usr/bin/env python3
"""audit_m2c_scan.py — M2-C の監査の数え上げを、全部 機械で作る（2026-09-06・監査 CP24）

なぜ在るか:
  監査 CP24 で、CC が一覧を手で並べたため3回 漏れた（材料の種類を4つと書いた／実物は6つ、
  time_on を「null」と書いた／実物は鍵が無い、時間帯の抜けを聞かれるまで報告しなかった）。
  まこさん指摘＝「監査のくせに自動生成にしてないって一番ありえないわ」。
  ★だから「何を数えるか」を実物の構造から機械で引く。CC が一覧を書かない。

使い方:
  python3 .claude/audits/audit_m2c_scan.py            # 数え上げを画面に出す
  python3 .claude/audits/audit_m2c_scan.py --write <出力先.md>   # 目印の間に差し込む
  python3 .claude/audits/audit_m2c_scan.py --selftest # ★読み取りが実物と噛み合っているか（0.1秒）

正直な限界:
  ・「どのファイルを見るか」は、このプログラムの中の SOURCES に書いてある（人が選んだ）。
    ただし SOURCES に無いファイルを見に行った所は1つも無い＝出どころは全部このファイルに在る。
  ・意味の判定（その穴が重いか）はしない。数えるだけ。
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

SDK = pathlib.Path(__file__).resolve().parents[2]
REPO = SDK.parents[1]
PR = SDK / "scripts/priority_rebuild"
RAT = SDK / ".claude/ratchet"

SOURCES = {
    "exec": PR / "engine_tuner_exec.py",
    "gen": PR / "engine_tuner_gen.py",
    "switch_gen": PR / "gen_indicator_switch.py",
    "switch": RAT / "indicator_switch.json",
    "families": RAT / "signal_families.json",
    "ranking": RAT / "material_ranking.json",
    "milestones": RAT / "engine_tuner_milestones2.md",
    "materials": RAT / "materials.md",
}
RECIPES = sorted((PR / "recipes").glob("identity_*_legacy.json"))
MARKS = {"G2": REPO / ".claude/state/g2_pass.json", "H2": REPO / ".claude/state/h2_pass.json"}


def txt(k: str) -> str:
    p = SOURCES[k]
    return p.read_text(encoding="utf-8") if p.exists() else ""


def jsn(k: str) -> dict:
    p = SOURCES[k]
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def func_body(src: str, name: str) -> str:
    """def name(...) から次の def までを切り出す。"""
    m = re.search(rf"^def {re.escape(name)}\(.*?^(?=def )", src, re.S | re.M)
    return m.group(0) if m else ""


# ── 1) 材料の種類＝実装が分岐する鍵（人が並べない）──────────────────────────
def material_kinds() -> list[str]:
    body = func_body(txt("exec"), "_material_name")
    keys = re.findall(r'"(\w+)" in m\b', body) + re.findall(r'm\.get\("(\w+)"', body)
    keys += re.findall(r'\("([\w", ]+)"\) if k in m', body)  # _excl の並び
    out: list[str] = []
    for k in keys:
        for kk in re.split(r'["\s,]+', k):
            if kk and kk not in out:
                out.append(kk)
    return out


# ── 2) オン・オフの表が持つ欄 ─────────────────────────────────────────────
def switch_fields() -> list[str]:
    return sorted(k for k in jsn("switch") if re.fullmatch(r"on|off|\w+_on", k))


# ── 3) 判定する関数と、その呼び出し ───────────────────────────────────────
def enable_funcs() -> list[str]:
    return re.findall(r"^def (\w+_enabled)\(", txt("exec"), re.M)


def enable_calls() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for p in sorted(PR.glob("*.py")):
        for i, ln in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for m in re.finditer(r"(\w+_enabled)\(", ln):
                if ln.lstrip().startswith("def "):
                    continue
                out.setdefault(m.group(1), []).append(f"{p.name}:{i}")
    return out


# ── 4) 材料を引く枝／審査で見る枝 ─────────────────────────────────────────
def draw_keys() -> list[str]:
    """生成器が別枠（レンジ幾何・需給・時間帯）を候補に入れている鍵。

    ★2026-09-07（監査 cp26 の 6-1）に直した。**直す前は 0件しか返さなかった。**
      直す前＝`_pick_material` の中を `m = {"…"` の形で探していた。
      実装は 2026-09-06 に「系統を引く → その系統の中を引く」へ変わり、その形をやめた
      （候補を作るのは `_lineage_candidates`）。そのため A-1 の「生成器で引く」が
      レンジ幾何・需給・時間帯とも ❌ と出ていた（**実物は3種とも引いている**）。
      監査 cp25 が N-7 として報告したのに直らず、cp26 でも同じ誤りが出た（まこさん指示
      2026-09-07「これはすぐに直して」）。
    ★指標（family）はここに出ない＝dict でなく種類名で候補に入るため
      （実物＝`cand += [str(f) for f in by_lineage.get(k, [])]`）。出す側が別に扱う。
    """
    body = func_body(txt("gen"), "_lineage_candidates")
    return sorted(set(re.findall(r'cand \+= \[\{"(\w+)"', body)))


def gate_keys() -> list[str]:
    """4要素ゲート（案の審査）が分岐する材料の鍵。"""
    g = txt("gen")
    m = re.search(r"for m in _walk_materials\(obj\):(.*?)\n\n", g, re.S)
    return re.findall(r'"(\w+)" in m\b', m.group(1)) if m else []


# ── 5) オン・オフのテストの枝 ─────────────────────────────────────────────
def t33_branches() -> list[str]:
    """自己検査の T33 系の枝の名前。**足し方2通りの両方を拾う。**

    ★2026-09-07（監査 cp26 の 6-1）に直した。**直す前は T33-g を取りこぼしていた。**
      直す前＝`t33.append(f"T33…` の形だけを探していた。
      2026-09-07 に足された T33-g は `t33 += [f"T33-g: …" for … in _check_extra_gate()]`
      という別の形なので、7つしか見つからず「枝は7つ・全部 family を試す」と出ていた。
      **実物は8つで、T33-g は別枠3種（レンジ幾何・需給・時間帯）を試す。**
    """
    g = txt("gen")
    names = re.findall(r't33\.append\(f?"(T33[-a-z]*)', g)
    names += re.findall(r't33 \+= \[f?"(T33[-a-z]*)', g)
    return sorted(set(names))


def t33_extra_branches() -> list[str]:
    """そのうち、別枠3種の審査（`_check_extra_gate`）を呼ぶ枝。

    ★どの枝が別枠を試すかを、監査が手で決めない＝その行が `_check_extra_gate` を
      呼んでいるかで機械が決める。
    """
    out = []
    for m in re.finditer(r't33 (?:\+=|\.append\()\s*\[?f?"(T33[-a-z]*)[^\n]*', txt("gen")):
        if "_check_extra_gate" in m.group(0):
            out.append(m.group(1))
    return sorted(set(out))


# ── 6) 直す前と後で結果が同じか確かめる走行の材料 ────────────────────────
def identity_materials() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for p in RECIPES:
        fams: set[str] = set()

        def walk(o):
            if isinstance(o, dict):
                if isinstance(o.get("family"), str):
                    fams.add(o["family"])
                if isinstance(o.get("geo"), str):
                    fams.add(o["geo"])
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(json.loads(p.read_text(encoding="utf-8")))
        out[p.stem.replace("identity_", "").replace("_legacy", "").upper()] = sorted(fams)
    return out


# ── 7) 部品・成績表 ───────────────────────────────────────────────────────
def parts_report() -> dict:
    d = jsn("families")
    parts = [str(x.get("name", x)) if isinstance(x, dict) else str(x) for x in d.get("parts", [])]
    extra = {k: (v.get("parts") if isinstance(v, dict) else v)
             for k, v in (d.get("extra_parts") or {}).items()}
    return {"部品の合計": len(parts), "別枠": extra,
            "MMI を含む部品": sorted(p for p in parts if "MMI" in p),
            "S-RタッチATR を含む部品": sorted(p for p in parts if "S-RタッチATR" in p)}


def ranking_report() -> dict:
    p = SOURCES["ranking"]
    if not p.exists():
        return {"成績表": "無い"}
    raw = p.read_text(encoding="utf-8", errors="ignore")
    d = json.loads(raw)
    return {"作られた窓": d.get("窓"), "行数": d.get("行数"),
            "測れた列": d.get("測れた列"), "順位に載った列": d.get("順位に載った列"),
            **{f"「{k}」を含む行": raw.count(k) for k in ("MMI", "taker_ls", "L-S比", "CVD")}}


# ── 8) 検査に通った記録のハッシュ値を、hook と同じ計算式で作り直す ────────
def mark_check() -> list[str]:
    out = []
    for name, p in MARKS.items():
        if not p.exists():
            out.append(f"{name}: 記録が無い")
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        h = hashlib.sha256()
        newer = []
        mt = p.stat().st_mtime
        for rel in sorted(d.get("files", [])):
            f = REPO / rel
            h.update(rel.encode())
            h.update(hashlib.sha256(f.read_bytes()).digest() if f.exists() else b"<missing>")
            if f.exists() and f.stat().st_mtime > mt:
                newer.append(rel)
        ok = "一致" if h.hexdigest() == d.get("fingerprint") else "食い違い"
        out.append(f"{name}: 対象 {len(d.get('files', []))} 本／再計算 {ok}"
                   f"／記録より新しい対象 {len(newer)} 本 {newer if newer else ''}")
    return out


# ── 9) 検査のコマンドを走らせて終了コードを取る ──────────────────────────
CHECKS = ["gen_materials.py --verify", "gen_materials.py --selftest",
          "gen_indicator_switch.py --verify", "gen_exit_families.py --verify",
          "gen_audit_request.py --selftest"]


def run_checks() -> list[str]:
    out = []
    for c in CHECKS:
        a = c.split()
        r = subprocess.run([sys.executable, str(PR / a[0])] + a[1:],
                           cwd=str(SDK), capture_output=True, text=True)
        tail = [x for x in (r.stdout + r.stderr).strip().splitlines() if x.strip()]
        out.append(f"`{c}` → rc={r.returncode} ／ {tail[-1][:90] if tail else ''}")
    return out


# ── 10) 要件（M2-C の段の状態）を正本から引く ────────────────────────────
def milestone_rows() -> list[tuple[str, str]]:
    rows = []
    for ln in txt("milestones").splitlines():
        m = re.match(r"\|\s*\*\*(M2-C-\d)\*\*\s*\|([^|]*)\|(.*)\|", ln)
        if m:
            rows.append((m.group(1), m.group(3).strip()[:70]))
    return rows


# ── 出力 ──────────────────────────────────────────────────────────────────
def build() -> str:
    kinds = material_kinds()
    fields = switch_fields()
    funcs = enable_funcs()
    calls = enable_calls()
    draw = draw_keys()
    gate = gate_keys()

    L: list[str] = []
    L.append("<!-- SCAN_START audit_m2c_scan.py が実物から書き出す＝手で書き換えない -->")
    L.append("")
    L.append("### A-1｜材料の種類（`engine_tuner_exec._material_name` が分岐する鍵）"
             f"＝**{len(kinds)} 種類**")
    L.append("")
    L.append("| 材料の種類 | オン・オフの欄 | 判定する関数 | 生成器で引く | 審査で見る |"
             " 判定関数の呼び出し |")
    L.append("|---|---|---|---|---|---|")
    for k in kinds:
        fld = next((f for f in fields if f == f"{k}_on"), "on / off" if k == "family" else "**無し**")
        fn = next((f for f in funcs if f.startswith(k)), None)
        if k == "family":
            fn = "indicator_enabled" if "indicator_enabled" in funcs else None
        cs = calls.get(fn or "", [])
        gen_cs = [c for c in cs if c.startswith("engine_tuner_gen")]
        L.append(f"| `{k}` | {fld} | {('`' + fn + '`') if fn else '**無し**'} "
                 f"| {'✅' if k in draw or k == 'family' else '**❌**'} "
                 f"| {'✅' if k in gate or k == 'family' else '**❌**'} "
                 f"| {len(cs)} 件（生成器 {len(gen_cs)}）{'＝**0**' if not cs else ''} |")
    L.append("")
    L.append(f"- オン・オフの表が持つ欄＝`{'` / `'.join(fields)}`")
    L.append(f"- 判定する関数＝`{'` / `'.join(funcs)}`")
    for f in funcs:
        cs = calls.get(f, [])
        L.append(f"  - `{f}` の呼び出し＝**{len(cs)} 件** {('／'.join(cs)) if cs else '（0件）'}")
    L.append(f"- 生成器が材料を引く枝＝`{'` / `'.join(draw)}`")
    L.append(f"- 案の審査が見る鍵＝`{'` / `'.join(sorted(set(gate)))}`")
    L.append("")

    L.append("### A-2｜オン・オフのテストの枝")
    b = t33_branches()
    be = t33_extra_branches()
    L.append(f"- 枝＝{len(b)} つ＝`{'` / `'.join(b)}`")
    # ★2026-09-07（監査 cp26 の 6-1）＝「全部 family を試す」という決め打ちの文をやめた。
    #   直す前＝どの枝が何を試すかを数えずに、文字で断定していた（T33-g が足された後も同じ文が出た）。
    if be:
        L.append(f"- うち**別枠3種（レンジ幾何・需給・時間帯）の審査を試す枝**＝{len(be)} つ＝"
                 f"`{'` / `'.join(be)}`／残り {len(b) - len(be)} つは `family` を試す")
    else:
        L.append(f"- うち別枠3種の審査を試す枝＝**0つ**（{len(b)} つとも `family` を試す）")
    L.append(f"- 生成器が別枠の判定関数を呼ぶ回数＝"
             f"**{sum(len(calls.get(f, [])) for f in funcs if f != 'indicator_enabled')} 件**")
    L.append("")

    L.append("### A-3｜直す前と後で結果が同じか確かめる走行が使う材料と、オン・オフの表")
    sw = jsn("switch")
    on, off = set(sw.get("on") or []), set(sw.get("off") or [])
    L.append("")
    L.append("| 走行 | 材料 | オンに在る | オフに在る | 定義表に無い |")
    L.append("|---|---|---|---|---|")
    for rec, fams in identity_materials().items():
        miss = [f for f in fams if f not in on and f not in off]
        L.append(f"| {rec} | {' / '.join(fams)} | {len([f for f in fams if f in on])} "
                 f"| {len([f for f in fams if f in off])} "
                 f"| {('**' + ' / '.join(miss) + '**') if miss else 'なし'} |")
    L.append("")
    L.append(f"- `counts` ＝ {json.dumps(sw.get('counts', {}), ensure_ascii=False)}")
    L.append(f"- オン {len(on)} ＋ オフ {len(off)} ＝ {len(on) + len(off)}")
    L.append("")

    L.append("### A-4｜部品と成績表")
    pr = parts_report()
    L.append(f"- 部品の合計＝**{pr['部品の合計']}**")
    L.append(f"- 別枠＝{json.dumps(pr['別枠'], ensure_ascii=False)}")
    L.append(f"- MMI を含む部品＝{pr['MMI を含む部品'] or '**0件**'}")
    L.append(f"- S-RタッチATR を含む部品＝{pr['S-RタッチATR を含む部品'] or '**0件**'}")
    for k, v in ranking_report().items():
        L.append(f"- 成績表 {k}＝**{v}**")
    L.append("")

    L.append("### A-5｜検査に通った記録（hook と同じ計算式で作り直した）")
    for x in mark_check():
        L.append(f"- {x}")
    L.append("")

    L.append("### A-6｜検査のコマンドの終了コード")
    for x in run_checks():
        L.append(f"- {x}")
    L.append("")

    L.append("### A-7｜M2-C の段の状態（正本の逐語・先頭70字）")
    for n, s in milestone_rows():
        L.append(f"- **{n}**｜{s}")
    L.append("")
    L.append("<!-- SCAN_END -->")
    return "\n".join(L) + "\n"


# ── 11) わざと壊して止まるか試すテスト（2026-09-07・監査 cp26 の 6-1）──────
def selftest() -> int:
    """このプログラムの読み取りが、実物の形と噛み合っているかを確かめる。

    ★なぜ足すか（まこさん指示 2026-09-07「これはすぐに直して」）
      このプログラムは実物のコードを正規表現で読む。**実物の書き方が変わると黙って0件を返し、
      在る守りを「無い」と報告する。**実際に2か所で起きた（cp25 の N-7 ／ cp26 の 6-1）。
      文章で注意しても止まらないので、噛み合わなくなったら鳴る形にする。

    ★期待する一覧を手で並べない＝オン・オフの表の欄と、実物のコードから導く。
    """
    ng: list[str] = []
    g = txt("gen")

    # T1＝実物から関数を切り出せるか（関数名が変わったら空になる）
    for fn in ("_lineage_candidates", "_pick_material"):
        if not func_body(g, fn):
            ng.append(f"T1: 実物の生成器から {fn} を切り出せない（関数名が変わった？）")
    if not func_body(txt("exec"), "_material_name"):
        ng.append("T1: 実物の実行器から _material_name を切り出せない（関数名が変わった？）")

    # T2＝オン・オフの欄が在る別枠は、全部「生成器で引く」枝として見つかるはず
    #     ★期待の一覧は switch_fields() から導く（監査が手で並べない）
    want = sorted(f[:-3] for f in switch_fields() if f.endswith("_on"))
    got = draw_keys()
    miss = [k for k in want if k not in got]
    if miss:
        ng.append(f"T2: オン・オフの欄が在るのに、生成器で引く枝として見つからない {miss}"
                  f"（見つかったもの＝{got}）")

    # T3＝同じ別枠が、材料の種類としても見つかるはず
    kinds = material_kinds()
    miss2 = [k for k in want if k not in kinds]
    if miss2:
        ng.append(f"T3: 材料の種類として見つからない {miss2}（見つかったもの＝{kinds}）")

    # T4＝実物に _check_extra_gate が在るなら、それを呼ぶ T33 の枝が1つ以上 在るはず
    if "def _check_extra_gate" in g and not t33_extra_branches():
        ng.append("T4: 実物に _check_extra_gate が在るのに、それを呼ぶ T33 の枝を拾えない")

    # T5＝T33 の枝が1つも拾えないのは、探し方が壊れた合図
    branches = t33_branches()
    if not branches:
        ng.append("T5: T33 の枝を1つも拾えない（探し方が実物と噛み合っていない）")

    # T6＝別枠の審査を試す枝は、枝の一覧にも必ず入っているはず
    #     ★2026-09-07＝T1〜T5 を足した直後、わざと壊して試したら **T33-g の取りこぼしを
    #       1つも捕まえなかった**（枝の一覧と別枠の一覧が別々の探し方だったため）。
    #       ＝いちばん起きた壊れ方（cp26 の 6-1 そのもの）が素通りしていた。ここで塞ぐ。
    lost = [x for x in t33_extra_branches() if x not in branches]
    if lost:
        ng.append(f"T6: 別枠の審査を試す枝 {lost} が、枝の一覧に入っていない"
                  f"（一覧＝{branches}）")

    for x in ng:
        print(f"  ❌ {x}")
    print(f"{'❌' if ng else '✅'} audit_m2c_scan の読み取り＝ダメだった件 {len(ng)}")
    return 1 if ng else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    body = build()
    if "--write" in sys.argv:
        out = pathlib.Path(sys.argv[sys.argv.index("--write") + 1])
        s = out.read_text(encoding="utf-8")
        if "<!-- SCAN_START" in s:
            s = re.sub(r"<!-- SCAN_START.*?<!-- SCAN_END -->\n", body, s, flags=re.S)
        else:
            s += "\n" + body
        out.write_text(s, encoding="utf-8")
        print(f"[差し込み] {out}")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())

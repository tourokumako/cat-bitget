#!/usr/bin/env python3
"""指標の修正対応表を作る（M2-C-15）。資料を写すだけのプログラム。

★CC は値・判定・説明の文を手で書かない。何をどこから写すかは、下の COPY の表だけに書く。
  写す処理・出力の頭書き・書く前の照らしの3つは、全部 COPY から作る＝説明と処理が食い違わない。
★値ごとの証拠（出どころの URL・逐語・照らした印）も、資料からそのまま写す＝表で値の正しさが見える。
★「何をするか」の欄は、next_step の控えのファイル next_step_reference.md（2026-10-12 より前は next_step.md）の「指標の修正の中身（4つ・元は前回の資料）」の文を、そのまま写す。
  作りの欄だけは M2-C-14 の決定（m2_todo.json の状態の文・まこさん「それでよい」）の仕分けを使う＝監査 CP60 の判定が
  「反する」→直す／「分からない」→教科書の版を別の材料として足して比べる／それ以外→そのまま。状態の文は出力に逐語で写す。
★対象の照らし（153回目に足した）＝使える指標は「承認済みの型の表 ∩ 印がオン」（gen_indicator_switch.py の頭書き）。
  ①表3つの種類が、保存してある indicator_switch.json の on と同じか（違えば止まる）
  ②今の源で作り直した on（gen_indicator_switch.build・書き込みなし）と比べ、増える種類は「資料に無い」の行として並べる（値は埋めない）
  ③種類ごとに、承認済みの型の表（signal_families.json の部品）に在るかを出す。型の表の承認の状態と照合の結果も出す
★書く前に、写した値と証拠を、読み直した資料と全部 照らす。1件でも違えば、書かずに止まる（fail-closed）。
★本物（observe_config.json・参照表・表3つ・調べた結果の元・オン・オフの表・型の表）は書かない。
  書くのは .claude/state/indicator_fix_plan.md と .json だけ。
"""
import contextlib
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import seal_outputs

HERE = Path(__file__).resolve().parent
ST = HERE.parent
RS = HERE / "research"
VB = ST / "verbatim" / "indicator-params-by-strategy-20261004"
SDK = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api")
PR = SDK / "scripts/priority_rebuild"
CP60 = SDK / ".claude/audits/2026-10-03_indicator_textbook_check_cp60_audit_report.md"
APPLIED = SDK / ".claude/audits/applied_fixes.json"
M2TODO = SDK / ".claude/ratchet/m2_todo.json"
SWJ = SDK / ".claude/ratchet/indicator_switch.json"
SFJ = SDK / ".claude/ratchet/signal_families.json"
SFA = SDK / ".claude/ratchet/signal_families_approved.txt"
NEXT = ST / "next_step.md"
NEXT_REF = ST / "next_step_reference.md"      # ★2026-10-12＝next_step の控えのファイル（「指標の修正の中身」は、いまここに在る）
OUT = ST / "indicator_fix_plan"
NO_SRC = "資料に無い（今の源で作り直した on に入るが、表3つと調べた結果に行が無い）"

# ── 何をどこから写すか（この表だけが正本） ──
#   欄の名前 → (資料のファイルの並び, その資料の中で写す項目の名前の並び)
COPY = {
    "パラメータ": ([ST / "indicator_params_by_strategy.json"],
              ["結果", "軸の数", "今の値", "最初の値（スキャル）", "最初の値の出どころ（スキャル）",
               "最初の値（デイトレ）", "最初の値の出どころ（デイトレ）", "範囲", "ライブラリの既定", "文のため使っていない値"]),
    "パラメータの証拠": ([ST / "indicator_params_review.json"], ["パラメータの名前", "既定", "スキャル", "デイトレ", "範囲", "メモ"]),
    "役割と閾値": ([ST / "indicator_roles_thresholds.json"],
              ["今の系統", "今の答える問いの区分", "今の向き", "出どころの役割", "役割の印", "閾値"]),
    # ★2026-10-07（158回目・まこさん「追加して」）＝係の結果の組を決め打ちにしない（out_w3＝RCI と前期間pivot の3種を足した）。
    "役割と閾値の証拠": (sorted(RS.glob("out_w*.json")), ["役割", "閾値"]),
    "役割と閾値の照らした結果": (sorted(RS.glob("verify_out_w*.json")), ["区分", "名前", "欄", "番号", "URL", "判定"]),
    "作り": ([CP60], ["教科書と違うか", "何を変えたか", "判定", "理由"]),
}
RULES = ["okd_param_rule_20261004.txt", "ok_param_rule_20261004.txt", "okd_source_rule_20261004.txt", "ok_source_rule_20261004.txt"]
SOURCES = sorted({p for ps, _f in COPY.values() for p in ps} | {VB / f for f in RULES} | {APPLIED, M2TODO, SWJ, SFJ, SFA})


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_rows(name):
    """種類 → 行。照らした結果だけは 種類 → 行の並び（区分が パラメータ 以外）。"""
    out = {}
    for src in COPY[name][0]:
        data = json.loads(src.read_text(encoding="utf-8"))
        rows = data["指標"] if isinstance(data, dict) else data
        for r in rows:
            if name == "役割と閾値の照らした結果":
                if r.get("区分") != "パラメータ":
                    out.setdefault(r["種類"], []).append(r)
            else:
                out[r["種類"]] = r
    return out


def load_cp60():
    """監査 CP60 の4節の143行（「**143件の表**」から「行の数＝」まで）。欄の名前は表の見出しのまま。"""
    lines = CP60.read_text(encoding="utf-8").splitlines()
    i0 = next(i for i, ln in enumerate(lines) if ln.startswith("**143件の表**"))
    head, out = None, {}
    for ln in lines[i0:]:
        if ln.startswith("行の数＝"):
            break
        if ln.startswith("| # |"):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            continue
        m = re.match(r"^\| (\d+) \| (.+?) \|", ln)
        if not m or head is None:
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) != len(head):
            sys.exit(f"❌ 監査 CP60 の行の欄の数が見出しと違う（{m.group(2)}）＝読み違える恐れ・止まる")
        out[cells[1]] = dict(zip(head, cells))
    return out


def next_step_items():
    """「指標の修正の中身（4つ・元は前回の資料）」の4行を、文のまま返す。
    ★2026-10-12（172回目）＝この節は、next_step.md から、控えのファイル next_step_reference.md へ移った（文は1文字も変えていない。
      next_step を作るプログラム tidy_next_step.py が、見出し「# 控え（」から後ろを控えのファイルに出す）。両方を読んで、在る方から写す。"""
    mark = "**指標の修正の中身（4つ・元は前回の資料）**"
    t = "".join(p.read_text(encoding="utf-8") for p in (NEXT, NEXT_REF) if p.exists())
    if mark not in t:
        sys.exit("❌ next_step.md と next_step_reference.md のどちらにも「指標の修正の中身」の節が無い＝止まる")
    sec = t.split(mark, 1)[1].split("\n\n**", 1)[0]
    items = {m.group(1): m.group(0).strip() for m in re.finditer(r"^([1-4])\. .+$", sec, re.M)}
    if sorted(items) != ["1", "2", "3", "4"]:
        sys.exit("❌ next_step_reference.md（または next_step.md）の「指標の修正の中身」の4行が読めない＝止まる")
    return items


def m2c14_text():
    """m2_todo.json の M2-C-14 の状態の文（まこさんの決定の記録）を、そのまま返す。"""
    def walk(o):
        if isinstance(o, dict):
            if o.get("番号") == "M2-C-14" and "状態" in o:
                return o["状態"]
            o = list(o.values())
        if isinstance(o, list):
            for x in o:
                got = walk(x)
                if got:
                    return got
        return None
    got = walk(json.loads(M2TODO.read_text(encoding="utf-8")))
    if not got:
        sys.exit("❌ m2_todo.json の M2-C-14 の状態の文が読めない＝止まる")
    return got


def mod_nums(s: str):
    """理由の欄の「修正 1〜6」「修正 13・14」の番号（文の中の数字だけを広げる）。"""
    out = set()
    for m in re.finditer(r"修正\s*([0-9][0-9〜・、, ]*)", s):
        for part in re.split(r"[・、, ]+", m.group(1)):
            if "〜" in part:
                a, b = part.split("〜")[:2]
                if a.isdigit() and b.isdigit():
                    out |= set(range(int(a), int(b) + 1))
            elif part.isdigit():
                out.add(int(part))
    return sorted(out)


def load_all():
    return {k: load_rows(k) for k in COPY if k != "作り"} | {"作り": load_cp60()}


def copy_row(k, s):
    """1つの種類について、COPY の欄を全部 写す（形を変えない）。"""
    row = {"種類": k}
    for col, (_ps, fs) in COPY.items():
        got = s[col].get(k)
        if got is None:
            row[col] = None
        elif col == "役割と閾値の照らした結果":
            row[col] = [{f: x.get(f) for f in fs} for x in got]
        else:
            row[col] = {f: got.get(f) for f in fs}
    return row


def check_targets():
    """対象の照らし。オン・オフの表は道具の関数で作り直して読む（書き込む関数は呼ばない）。
    ★型の表の道具（gen_signal_families）は読み込まない＝engine_tuner につながるので、G2 の hook（enforce_g2_pass）が止める。
      型の表は json の部品だけを読む。承認と照合の状態は、道具のコマンド（--status・--verify）で別に見る。"""
    sys.path.insert(0, str(PR))
    with contextlib.redirect_stdout(io.StringIO()):
        import gen_indicator_switch as gis
        import indicator_reference_diag as iref
        built = gis.build()
    saved = json.loads(SWJ.read_text(encoding="utf-8"))
    fams, no_fam = set(), []
    for p in json.loads(SFJ.read_text(encoding="utf-8"))["inventory"]["lineage_of"]:
        ent = iref.find(p)[0]
        (fams.add(ent["family"]) if ent is not None else no_fam.append(p))
    return dict(on_saved=list(saved["on"]), fp_saved=saved.get("fingerprint"),
                on_built=list(built["on"]), fp_built=built["fingerprint"], counts_built=built["counts"],
                table_fams=fams, table_no_family=no_fam)


# ── 0. 封と、資料の走らせる前のハッシュ値 ──
if not seal_outputs.verify(quiet=True):
    sys.exit("❌ 封が合わない＝表を作らない")
before = {p.name: sha(p) for p in SOURCES}

src = load_all()
ns, c14 = next_step_items(), m2c14_text()
rules = {f: (VB / f).read_text(encoding="utf-8") for f in RULES}
applied = sorted({int(a["num"]) for a in json.loads(APPLIED.read_text(encoding="utf-8"))["applied"]
                  if "cp60" in a.get("report", "")})
names = list(src["パラメータの証拠"])               # 使う141種（indicator_params_review.json の並び）
if set(names) != set(src["パラメータ"]) or set(names) != set(src["役割と閾値"]):
    sys.exit("❌ 表3つの種類がそろわない＝止まる")
tg = check_targets()
if set(names) != set(tg["on_saved"]):
    sys.exit(f"❌ 表3つの種類が、保存してある indicator_switch.json の on と違う＝止まる: {sorted(set(names) ^ set(tg['on_saved']))}")
added = [f for f in tg["on_built"] if f not in set(tg["on_saved"])]
removed = [f for f in tg["on_saved"] if f not in set(tg["on_built"])]

# ── 1. 写す ──
rows = []
for k in names:
    row = copy_row(k, src)
    pp, rr, c = row["パラメータ"], row["役割と閾値"], row["作り"]
    has = bool(pp["範囲"]) or bool(pp["最初の値（スキャル）"]) or bool(pp["最初の値（デイトレ）"])
    row["何をするか"] = {
        "パラメータ": ns["1"] if pp["結果"] == "当てた" and has else
        ("表の結果＝パラメータを持たない" if pp["結果"] != "当てた" else "表で最初の値も範囲も空"),
        "作り": None,
        "役割": ns["3"] if rr.get("役割の印") in ("食い違い", "食い違いの疑い") else "表に食い違いの印が無い",
        "閾値": ns["4"] if re.match(r"^(既定|スキャル|デイトレ)：", rr.get("閾値") or "") else "表の閾値が数字でない（文だけ・無い）"}
    if c:
        head = c["判定"].replace("*", "").strip()
        nums = mod_nums(c["理由"])
        row["何をするか"]["作り"] = {
            "M2-C-14 の仕分け": ("直す" if head.startswith("反する") else
                              "教科書の版を別の材料として足し、一致率で比べる" if head.startswith("分からない") else "そのまま"),
            "修正": nums, "当てた修正": [n for n in nums if n in applied], "当てていない修正": [n for n in nums if n not in applied]}
    row["対象"] = {"保存してある on": True, "今の源で作り直した on": k in set(tg["on_built"]),
                 "承認済みの型の表に在る": k in tg["table_fams"]}
    rows.append(row)
for k in added:                                   # 資料に行が無い＝値は埋めない
    row = copy_row(k, src)
    row["何をするか"] = {"パラメータ": NO_SRC, "作り": None, "役割": NO_SRC, "閾値": NO_SRC}
    row["対象"] = {"保存してある on": False, "今の源で作り直した on": True,
                 "承認済みの型の表に在る": k in tg["table_fams"]}
    rows.append(row)

# ── 2. 書く前に、写した値と証拠を、読み直した資料と全部 照らす（1件でも違えば止まる） ──
src2 = load_all()
bad = []
for row in rows:
    want = copy_row(row["種類"], src2)
    for col in COPY:
        if json.dumps(row[col], ensure_ascii=False, sort_keys=True) != json.dumps(want[col], ensure_ascii=False, sort_keys=True):
            bad.append(f"{row['種類']}／{col}")
if bad:
    sys.exit(f"❌ 写した値が資料と {len(bad)} 件 違う＝書かない: {bad[:10]}")
for f, t in rules.items():
    if (VB / f).read_text(encoding="utf-8") != t:
        sys.exit(f"❌ 決まりの逐語 {f} が読み直すと違う＝書かない")
after = {p.name: sha(p) for p in SOURCES}
if before != after:
    sys.exit("❌ 走らせている間に資料のハッシュ値が変わった＝書かない")

# ── 3. 数（写した値から数えるだけ） ──
base = [r for r in rows if r["対象"]["保存してある on"]]
cnt = {
    "使う種類（保存してある indicator_switch.json の on）": len(base),
    "使う種類（今の源で作り直した on）": len(tg["on_built"]),
    "作り直すと on に入る（資料に無い）": len(added),
    "作り直すと on から外れる": len(removed),
    "on の中で、承認済みの型の表に無い種類": sum(not r["対象"]["承認済みの型の表に在る"] for r in rows),
    "パラメータ：表の値を持たせる": sum(r["何をするか"]["パラメータ"] == ns["1"] for r in base),
    "パラメータ：表の結果＝パラメータを持たない": sum(r["何をするか"]["パラメータ"].startswith("表の結果") for r in base),
    "パラメータ：表で最初の値も範囲も空": sum(r["何をするか"]["パラメータ"].startswith("表で最初の値") for r in base),
    "役割：表の印＝食い違い": sum(r["役割と閾値"]["役割の印"] == "食い違い" for r in base),
    "役割：表の印＝食い違いの疑い": sum(r["役割と閾値"]["役割の印"] == "食い違いの疑い" for r in base),
    "閾値：表で数字": sum(r["何をするか"]["閾値"] == ns["4"] for r in base),
    "役割と閾値の証拠（調べた結果の元 out_w）が在る種類": sum(r["役割と閾値の証拠"] is not None for r in base),
}
for j in ("直す", "教科書の版を別の材料として足し、一致率で比べる", "そのまま"):
    cnt[f"作り：{j}"] = sum((r["何をするか"]["作り"] or {}).get("M2-C-14 の仕分け") == j for r in base)
cnt["作り：監査 CP60 の143件に無い"] = sum(r["作り"] is None for r in base)


def cell(v):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return (s or "").replace("|", "／").replace("\n", " ")


def mark_count(items):
    """証拠の欄の、照らした印ごとの件数（写した値から数えるだけ）。欄が「無い」なら 無い。"""
    if not isinstance(items, list):
        return "無い"
    c = {}
    for it in items:
        m = it.get("照らした印", "?") if isinstance(it, dict) else "?"
        c[m] = c.get(m, 0) + 1
    return "・".join(f"{k}{v}" for k, v in sorted(c.items())) or "無い"


def role_ev(r):
    """役割の証拠＝out_w の役割の欄（何を見るか・URL）に、照らした結果の判定を番号で添える（写すだけ）。"""
    ev = (r["役割と閾値の証拠"] or {}).get("役割")
    if not isinstance(ev, list):
        return "調べた結果の元 out_w に無い（調べた70種の外）"
    ver = {(v["欄"], v["番号"]): v["判定"] for v in (r["役割と閾値の照らした結果"] or []) if v["区分"] == "役割"}
    return "<br>".join(f"{it.get('何を見るか')}（{it.get('URL')}・照らし＝{ver.get(('役割', i), '記録なし')}）" for i, it in enumerate(ev))


md = ["<!-- INDICATOR_FIX_PLAN make_fix_plan.py が自動生成＝手で書き換えない -->",
      "# 指標の修正対応表（M2-C-15）", "",
      "## このプログラムがしたこと（COPY の表から書き出した）", ""]
for col, (ps, fs) in COPY.items():
    md.append(f"- {col}＝{'・'.join('`' + p.name + '`' for p in ps)} の {'・'.join(fs)} を、形を変えずに写した")
md += ["- 「何をするか」の欄＝next_step の控えのファイル `next_step_reference.md`（2026-10-12 より前は `next_step.md`）の「指標の修正の中身」の文を、その行に当たるときだけ写した",
       "- 作りの仕分け＝`m2_todo.json` の M2-C-14 の状態の文（下に逐語）＝監査 CP60 の判定の先頭が「反する」→直す・「分からない」→教科書の版を足して比べる・それ以外→そのまま",
       f"- 当てた修正の番号＝`applied_fixes.json` の CP60 の記録＝{applied}",
       "- 書く前の照らし＝写した値と証拠を、読み直した資料と全部 照らした＝違い 0 件（違いがあれば書かずに止まる作り）",
       f"- 資料のハッシュ値＝走らせる前と後で同じ（{len(after)} ファイル）・封の照らし＝合う",
       "", "## 対象の照らし（使える指標＝承認済みの型の表 ∩ 印がオン・gen_indicator_switch.py の頭書き）", "",
       f"- 表3つの種類＝保存してある `indicator_switch.json` の on（指紋 {tg['fp_saved']}）と同じ {len(base)} 種",
       f"- 今の源で作り直した on（`gen_indicator_switch.build`・書き込みなし・指紋 {tg['fp_built']}）＝{len(tg['on_built'])} 種",
       f"- 作り直すと on に入る＝{added}（表には「{NO_SRC}」の行として並べた）",
       f"- 作り直すと on から外れる＝{removed}",
       f"- 作り直した on の内訳＝{tg['counts_built']}",
       f"- 型の表の部品のうち、今の定義表で種類に直せない名前＝{tg['table_no_family']}",
       f"- on の中で、承認済みの型の表に無い種類＝{[r['種類'] for r in rows if not r['対象']['承認済みの型の表に在る']]}",
       "", "## 決まりとまこさんの言葉（逐語・`verbatim/indicator-params-by-strategy-20261004/` から写した）", ""]
for f, t in rules.items():
    md += [f"### {f}", ""] + [f"> {ln}" if ln else ">" for ln in t.rstrip("\n").split("\n")] + [""]
md += ["## next_step の「指標の修正の中身」（逐語）", ""] + [f"> {ns[i]}" for i in "1234"] + [
       "", "## M2-C-14 の状態の文（逐語）", "", f"> {c14}",
       "", "## 数（写した値から数えた）", "", "| 数 | 件数 |", "|---|---|"] + [f"| {k} | {v} |" for k, v in cnt.items()] + [
       "", "## 指標ごと（値ごとの逐語と URL の全部は indicator_fix_plan.json）", "",
       "| 種類 | 対象（保存の on／作り直した on／承認済みの型の表） | 今の値 | 最初の値（スキャル） | 最初の値（デイトレ） | 範囲 | パラメータの証拠（照らした印の数＝既定／スキャル／デイトレ／範囲） | パラメータで何をするか | 作り（監査 CP60 の判定／M2-C-14 の仕分け／修正の番号） | 今の系統（問い） | 出どころの役割（表） | 役割の印 | 役割の証拠（何を見るか・URL・照らし） | 役割で何をするか | 閾値（表） | 閾値で何をするか |",
       "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    p, ev, rr, w, t = r["パラメータ"] or {}, r["パラメータの証拠"] or {}, r["役割と閾値"] or {}, r["何をするか"], r["対象"]
    cw = (f"{r['作り']['判定']}／{w['作り']['M2-C-14 の仕分け']}／修正 {w['作り']['修正']}・当てた {w['作り']['当てた修正']}・まだ {w['作り']['当てていない修正']}"
          if r["作り"] else "監査 CP60 の143件に無い")
    pev = "／".join(mark_count(ev.get(c)) for c in ("既定", "スキャル", "デイトレ", "範囲"))
    tgt = "／".join("在る" if t[x] else "無い" for x in ("保存してある on", "今の源で作り直した on", "承認済みの型の表に在る"))
    md.append("| " + " | ".join(cell(x) for x in (
        r["種類"], tgt, p.get("今の値"), p.get("最初の値（スキャル）"), p.get("最初の値（デイトレ）"), p.get("範囲"), pev, w["パラメータ"], cw,
        f"{rr.get('今の系統')}（{rr.get('今の答える問いの区分')}）", rr.get("出どころの役割"), rr.get("役割の印") or "なし", role_ev(r), w["役割"],
        rr.get("閾値"), w["閾値"])) + " |")
OUT.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8")
OUT.with_suffix(".json").write_text(json.dumps({"COPY": {k: [[str(p) for p in v[0]], v[1]] for k, v in COPY.items()},
                                                "決まりの逐語": rules, "数": cnt, "当てた修正": applied,
                                                "対象の照らし": {k: (sorted(v) if isinstance(v, set) else v) for k, v in tg.items()},
                                                "資料のハッシュ値": after, "指標": rows},
                                               ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(cnt, ensure_ascii=False, indent=1))
print(f"照らし＝違い 0 件／資料 {len(after)} ファイルのハッシュ値は同じ")

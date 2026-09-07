#!/usr/bin/env python3
"""監査 CP27（M2-D 需給を順位に入れる）＝①②を機械で測る（read-only・手で数えない）。

使い方:
  python3 .claude/audits/audit_m2d_cp27_scan.py --a1   # (1) 成績表の中の需給（18組・役割・位置）
  python3 .claude/audits/audit_m2d_cp27_scan.py --a2   # (1) 指標の列が足す前後で1つも変わっていないか
  python3 .claude/audits/audit_m2d_cp27_scan.py --a3   # (1) 分離力を監査が独立に計算し直して一致するか
  python3 .claude/audits/audit_m2d_cp27_scan.py --a4   # (1) 値決め窓だけか（窓・採点窓との重なり・未来参照）
  python3 .claude/audits/audit_m2d_cp27_scan.py --b1   # (2) 生成器の読み＋印の入り切り＋群の混入
  python3 .claude/audits/audit_m2d_cp27_scan.py --b2   # (2) location・env が不変か
  python3 .claude/audits/audit_m2d_cp27_scan.py --all

★読むだけ。--b1 だけは indicator_switch.json を一時的に書き替えて必ず元に戻し、
  終わりに md5 が同じことを機械で確かめる。
"""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]      # bitget-python-sdk-api
SCRIPTS = ROOT / "scripts" / "priority_rebuild"
RANK = ROOT / ".claude" / "ratchet" / "material_ranking.json"
BEFORE = ROOT / ".claude" / "ratchet" / "material_ranking.before_add_demand.json"
SWITCH = ROOT / ".claude" / "ratchet" / "indicator_switch.json"
BARS = ROOT / "data" / "BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv"

sys.path.insert(0, str(SCRIPTS))

FAILS: list[str] = []


def ok(cond: bool, msg: str) -> bool:
    print(("  OK  " if cond else "  NG  ") + msg)
    if not cond:
        FAILS.append(msg)
    return bool(cond)


def load(p: pathlib.Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def demand_names() -> list[str]:
    """需給の名前の正本＝indicator_reference_diag.DEMAND_REF（監査が手で書かない）。"""
    import indicator_reference_diag as iref
    return sorted(iref.DEMAND_REF)


def split_name(col: str) -> str:
    return col.rsplit("__", 1)[0] if "__" in col else col


def demand_cols_of(mod, names, role):
    return sorted({str(c) for c, _a, _l, _h in mod.ranked_materials(role) if split_name(str(c)) in names})


# ---------------------------------------------------------------- (1) A1
def a1() -> None:
    print("=" * 96)
    print("[A1] 成績表の中の需給＝役割・ラベル・先読みごとに何本 載っているか（json をそのまま数える）")
    print("=" * 96)
    d = load(RANK)
    names = set(demand_names())
    order = d["順位"]
    print(f"  需給の名前の正本（DEMAND_REF）= {sorted(names)}")
    total = 0
    per_role: dict = {}
    for role, bl in order.items():
        for lab, bn in bl.items():
            for hor, got in bn.items():
                for col, acc in got:
                    if split_name(str(col)) in names:
                        total += 1
                        per_role.setdefault(role, []).append((lab, str(hor), str(col), float(acc)))
    print(f"  成績表の全役割で 需給の行は 合計 {total} 件。役割の内訳 = "
          f"{ {k: len(v) for k, v in sorted(per_role.items())} }")
    ok(sorted(per_role) == ["sufficiency"],
       f"需給が載っている役割は sufficiency だけ（実測 {sorted(per_role)}）")
    ok(total == 18, f"需給の行は全部で 18 件（3列 x ラベル3 x 先読み2）（実測 {total}）")
    if "sufficiency" in per_role:
        labs = sorted({x[0] for x in per_role["sufficiency"]})
        hors = sorted({x[1] for x in per_role["sufficiency"]}, key=int)
        cols = sorted({x[2] for x in per_role["sufficiency"]})
        ok(len(labs) == 3, f"ラベルが3本（実測 {labs}）")
        ok(len(hors) == 2, f"先読みが2本（実測 {hors}）")
        ok(len(cols) == 3, f"列が3本（実測 {cols}）")
        ok(sorted(split_name(c) for c in cols) == sorted(names),
           f"列の名前が DEMAND_REF の3件と一致（実測 {sorted(split_name(c) for c in cols)}）")
        print("  --- 需給3列の生の位置（役割 sufficiency の中）---")
        print(f"  {'ラベル':<8} {'先読み':>6} {'列':<16} {'分離力':>8} {'位置':>7} / {'本数':>7}")
        for lab in labs:
            for hor in hors:
                dd = order["sufficiency"][lab]
                key = str(hor) if str(hor) in dd else int(hor)
                got = dd[key]
                for i, (col, acc) in enumerate(got, 1):
                    if split_name(str(col)) in names:
                        print(f"  {lab:<8} {hor:>6} {str(col):<16} {float(acc):>8.3f} {i:>7} / {len(got):>7}")
    import observe_diag as od
    roles = od._role_lineage_table()
    have = sorted(r for r, s in roles.items() if "需給" in (s.get("lineages") or []))
    ok(have == sorted(per_role),
       f"型の表で系統「需給」を持つ役割 {have} と、成績表で需給が載った役割 {sorted(per_role)} が一致")
    for k in ("測れた列", "順位に載った列", "需給の被覆", "需給の重複のふるい"):
        print(f"  {k} = {json.dumps(d.get(k), ensure_ascii=False)}")


# ---------------------------------------------------------------- (1) A2
def a2() -> None:
    print("=" * 96)
    print("[A2] 足す前（控え）と今を突き合わせ、指標の列が1つも変わっていないか")
    print("=" * 96)
    if not BEFORE.exists():
        ok(False, f"控えが無い: {BEFORE}")
        return
    b, a = load(BEFORE), load(RANK)
    names = set(demand_names())

    def strip(o: dict) -> dict:
        return {ro: {la: {str(nn): [[str(c), float(v)] for c, v in got if split_name(str(c)) not in names]
                          for nn, got in bl.items()} for la, bl in blk.items()} for ro, blk in o.items()}

    sb, sa = strip(b["順位"]), strip(a["順位"])
    ok(sb == sa, "需給を除いた順位の中身（列名・分離力・並び順）が、足す前と完全一致")
    if sb != sa:
        for ro in sorted(set(sb) | set(sa)):
            for la in sorted(set(sb.get(ro, {})) | set(sa.get(ro, {}))):
                for nn in sorted(set(sb.get(ro, {}).get(la, {})) | set(sa.get(ro, {}).get(la, {}))):
                    x = sb.get(ro, {}).get(la, {}).get(nn)
                    y = sa.get(ro, {}).get(la, {}).get(nn)
                    if x != y:
                        print(f"     - 食い違い {ro}/{la}/{nn}: 前 {len(x or [])} 本 -> 後 {len(y or [])} 本")
    n_ind_b = len({str(c) for blk in b["順位"].values() for bl in blk.values()
                   for got in bl.values() for c, _ in got if split_name(str(c)) not in names})
    n_ind_a = len({str(c) for blk in a["順位"].values() for bl in blk.values()
                   for got in bl.values() for c, _ in got if split_name(str(c)) not in names})
    print(f"  照らした指標の列（重複を除いた列名の数）= 前 {n_ind_b} 本 / 後 {n_ind_a} 本")
    ok(n_ind_b == n_ind_a, f"指標の列の本数が変わっていない（{n_ind_b} -> {n_ind_a}）")
    n_rows_b = sum(len(got) for blk in b["順位"].values() for bl in blk.values() for got in bl.values())
    n_rows_a = sum(len(got) for blk in a["順位"].values() for bl in blk.values() for got in bl.values())
    print(f"  順位の行の総数 = 前 {n_rows_b} -> 後 {n_rows_a}（差 {n_rows_a - n_rows_b}）")
    ok(n_rows_a - n_rows_b == 18, f"増えた行が ちょうど 18（実測 {n_rows_a - n_rows_b}）")
    for k in ("窓", "行数", "先を見るバー数", "時間足"):
        ok(b.get(k) == a.get(k), f"{k} が足す前後で同じ（前={b.get(k)} 後={a.get(k)}）")
    print(f"  測れた列: {b.get('測れた列')} -> {a.get('測れた列')} / 載った列: "
          f"{b.get('順位に載った列')} -> {a.get('順位に載った列')} / 省いた列: "
          f"{len(b.get('省いた列') or {})} -> {len(a.get('省いた列') or {})}")


# ---------------------------------------------------------------- (1) A3
def a3() -> None:
    print("=" * 96)
    print("[A3] 監査が独立に分離力を計算し直し、成績表の値と一致するか（式の書き写しの検出）")
    print("=" * 96)
    import pandas as pd
    import observe_diag as od
    od.load_config(None)
    bars = pd.read_csv(BARS, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    _nm, a0, b0 = od._insp_windows()[0]
    win = bars.loc[(bars.index >= a0) & (bars.index < b0)]
    print(f"  監査が使う窓 = {win.index.min()} 〜 {win.index.max()}（{len(win)} 本）")
    dem, cov = od.load_demand(win.index)
    df = dem.copy()
    df.columns = [f"{c}__{od.DEMAND_RANK_TF}" for c in dem.columns]
    cols = list(df.columns)
    hors = od._regime_horizons()
    mine: dict = {}
    for n in hors:
        labels = od._regime_labels(win, n)
        step = od._independent_step(od.DEMAND_RANK_TF, n)
        grid = df.iloc[::step]
        for lab in od.REGIME_LABELS:
            mask, usable = labels[lab]
            keep = usable.reindex(grid.index).fillna(False).to_numpy()
            sub = grid.loc[keep, cols]
            m = mask.reindex(sub.index)
            if int(m.sum()) < 10 or int((~m).sum()) < 10:
                continue
            r = od.rank_separation(sub, m, cols, set(), top=len(cols))
            for _i, row in r.iterrows():
                mine.setdefault(str(row["特徴"]), {}).setdefault(lab, {})[int(n)] = round(float(row["分離力"]), 9)
    d = load(RANK)
    names = set(demand_names())
    theirs: dict = {}
    for lab, bn in d["順位"]["sufficiency"].items():
        for hor, got in bn.items():
            for col, acc in got:
                if split_name(str(col)) in names:
                    theirs.setdefault(str(col), {}).setdefault(lab, {})[int(hor)] = round(float(acc), 9)
    print(f"  監査が測れた列 = {sorted(mine)}")
    print(f"  成績表に在る列 = {sorted(theirs)}")
    ok(sorted(mine) == sorted(theirs), "監査が測れた列と、成績表に載っている列が一致")
    same, diff = 0, []
    for c in sorted(set(mine) & set(theirs)):
        for lab in sorted(set(mine[c]) | set(theirs[c])):
            for n in sorted(set(mine[c].get(lab, {})) | set(theirs[c].get(lab, {})), key=int):
                x, y = mine[c].get(lab, {}).get(n), theirs[c].get(lab, {}).get(n)
                if x is not None and y is not None and abs(x - y) < 1e-9:
                    same += 1
                else:
                    diff.append((c, lab, n, x, y))
    print(f"  一致 {same} 組 / 食い違い {len(diff)} 組")
    for c, lab, n, x, y in diff:
        print(f"     - {c} / {lab} / N={n}: 監査={x} 成績表={y}")
    ok(same == 18 and not diff,
       f"18組すべてが 監査の再計算と完全一致（実測 一致 {same} 組・食い違い {len(diff)} 組）")
    print("  --- 被覆（監査が load_demand から取り直した値）---")
    for k, v in dict(cov).items():
        print(f"     {k}: {v}")
    ok(dict(cov) == dict(d.get("需給の被覆") or {}),
       "成績表に書かれた需給の被覆が、監査の取り直しと一致")


# ---------------------------------------------------------------- (1) A4
def a4() -> None:
    print("=" * 96)
    print("[A4] 値決め窓だけで測っているか（採点窓・確認窓を1バーも使っていないか）")
    print("=" * 96)
    import observe_diag as od
    import periods
    d = load(RANK)
    _nm, a0, b0 = od._insp_windows()[0]
    print(f"  値決め窓（_insp_windows()[0]）= {_nm} {a0} 〜 {b0}")
    print(f"  成績表の窓 = {d.get('窓')} / 行数 = {d.get('行数')}")
    w = [str(x) for x in (d.get("窓") or [])]
    ok(len(w) == 2 and str(a0) <= w[0] and w[1] < str(b0),
       f"成績表の窓が値決め窓の中に収まっている（{w}）")
    sc_s, sc_e = str(periods.SCORE_START), str(periods.SCORE_END)
    print(f"  採点窓 = {sc_s} 〜 {sc_e}")
    ok(w[1] < sc_s, f"成績表の窓の末尾（{w[1]}）が採点窓の始まり（{sc_s}）より前")
    src = (SCRIPTS / "observe_diag.py").read_text(encoding="utf-8")
    i = src.index("def rank_demand_for_regime")
    j = src.index("def merge_demand_into_ranking")
    body = src[i:j]
    for nm in ("_insp_windows()[0]", "_assert_search_window_only", "load_demand",
               "_regime_labels", "_independent_step", "rank_separation"):
        ok(nm in body, f"rank_demand_for_regime の中に {nm} が在る")
    ok("shift(-" not in body and "center=True" not in body,
       "rank_demand_for_regime の中に未来参照の型（shift(- / center=True）が無い")


# ---------------------------------------------------------------- (2) B1
def b1() -> None:
    print("=" * 96)
    print("[B1] 生成器が順位から需給3列を読めるか + 印の入り切り + 群の混入")
    print("=" * 96)
    md5_before = hashlib.md5(SWITCH.read_bytes()).hexdigest()
    import engine_tuner_gen as g
    names = set(demand_names())
    got = demand_cols_of(g, names, "sufficiency")
    print(f"  ranked_materials('sufficiency') の需給の列 = {got}")
    ok(len(got) == 3, f"sufficiency に需給3列が出る（実測 {len(got)} 本）")
    print(f"  sufficiency の順位の全本数 = {len(g.ranked_materials('sufficiency'))}")
    for role in ("sufficiency", "location", "env"):
        try:
            grp = [r for r in g.ranked_groups(role) if str(r[0]) in names]
            n = len(grp)
        except SystemExit as e:
            print(f"     - {role}: 読めない（{e}）")
            n, grp = -1, []
        if role == "sufficiency":
            ok(n > 0, f"ranked_groups('sufficiency') に需給の組が出る（実測 {n} 組）")
            print(f"     {sorted({(str(r[0]), str(r[1])) for r in grp})}")
        else:
            ok(n == 0, f"ranked_groups('{role}') に需給の組が1つも混ざらない（実測 {n} 組）")
    for nm in sorted(names):
        col = f"{nm}__5m"
        try:
            fam, tf = g._family_tf_from_col(col)
            ok((fam, tf) == (nm, "5m"), f"_family_tf_from_col('{col}') = ('{nm}', '5m')（実測 {(fam, tf)}）")
        except Exception as e:                                   # noqa: BLE001
            ok(False, f"_family_tf_from_col('{col}') が落ちた: {e!r}")

    target = sorted(names)[0]
    raw = SWITCH.read_text(encoding="utf-8")
    sw = json.loads(raw)
    key = "demand_on"
    ok(key in sw, f"indicator_switch.json に {key} が在る（在る鍵 = {sorted(sw)}）")
    try:
        cur = list(sw[key])
        print(f"  いまの demand_on = {cur}")
        sw[key] = [x for x in cur if x != target]
        SWITCH.write_text(json.dumps(sw, ensure_ascii=False, indent=1), encoding="utf-8")
        for m in ("engine_tuner_exec", "engine_tuner_gen"):
            if m in sys.modules:
                importlib.reload(sys.modules[m])
        import engine_tuner_gen as g2
        g2._RANKED_GROUPS_MEMO.clear()
        off = demand_cols_of(g2, names, "sufficiency")
        print(f"  {target} を False にしたときの需給の列 = {off}")
        ok(len(off) == 2 and all(split_name(c) != target for c in off),
           f"印から {target} を外すと その列だけ消える（実測 {off}）")
    finally:
        SWITCH.write_text(raw, encoding="utf-8")
        md5_after = hashlib.md5(SWITCH.read_bytes()).hexdigest()
        ok(md5_before == md5_after,
           f"indicator_switch.json を元に戻した（md5 {md5_before[:12]} -> {md5_after[:12]}）")
    for m in ("engine_tuner_exec", "engine_tuner_gen"):
        if m in sys.modules:
            importlib.reload(sys.modules[m])
    import engine_tuner_gen as g3
    g3._RANKED_GROUPS_MEMO.clear()
    back = demand_cols_of(g3, names, "sufficiency")
    ok(len(back) == 3, f"印を戻すと 需給3列が戻る（実測 {len(back)} 本）")


# ---------------------------------------------------------------- (2) B2
def b2() -> None:
    print("=" * 96)
    print("[B2] location・env ほかの順位が、需給を足す前後で変わっていないか")
    print("=" * 96)
    b, a = load(BEFORE), load(RANK)
    names = set(demand_names())
    for role in sorted(a["順位"]):
        rb = {(la, str(nn)): [[str(c), float(v)] for c, v in got]
              for la, bl in b["順位"].get(role, {}).items() for nn, got in bl.items()}
        ra = {(la, str(nn)): [[str(c), float(v)] for c, v in got]
              for la, bl in a["順位"].get(role, {}).items() for nn, got in bl.items()}
        if role == "sufficiency":
            print(f"  役割 {role} は需給を足した先なので、ここでは比べない（A2 で需給を除いて照合済み）")
            continue
        ok(rb == ra, f"役割 {role} の順位が足す前後で完全一致（表 {len(ra)} 枚）")
    import engine_tuner_gen as g
    for role in ("location", "env"):
        rows = g.ranked_materials(role)
        top = rows[0]
        print(f"  {role} の1位 = {top[0]}（分離力 {top[1]:.3f} / ラベル {top[2]} / 先読み {top[3]}）"
              f" / 並びの本数 {len(rows)}")
        ok(not any(split_name(str(c)) in names for c, _a, _l, _h in rows),
           f"{role} の順位に需給の列が1本も混ざらない")


# ---------------------------------------------------------------- (2) B3
def b3() -> None:
    """需給を足したことで、束が使う「◯位」の指し先がずれていないか（_ranked_material_at の並び）。"""
    print("=" * 96)
    print("[B3] 束が引く順位（_ranked_material_at のふるいを通る組の並び）が、需給でずれていないか")
    print("=" * 96)
    import engine_tuner_gen as g
    import indicator_reference_diag as iref
    names = set(demand_names())
    ranges = g.material_ranges()
    table = g.load_signal_table()
    ok(not (names & set(ranges)),
       f"需給の3件はパラメータの範囲の表に無い（＝fam not in ranges で飛ぶ）"
       f"（実測の重なり {sorted(names & set(ranges))}）")
    for role in ("sufficiency", "location", "env"):
        rr = table["roles"][role]
        tfs_ok = set(g._role_tfs(list(table.get("tfs") or []), table, role)) if False else None
        seq = []
        n_demand_seen = 0
        for fam, tf, lab, hor, med, ncol, col in g.ranked_groups(role):
            if fam in names:
                n_demand_seen += 1
            if fam not in iref.FAMILY_LINEAGE or fam not in ranges:
                continue
            if iref.FAMILY_LINEAGE[fam]["k"] not in rr["lineages"]:
                continue
            seq.append((fam, tf, lab, hor))
        h = hashlib.md5(json.dumps(seq, ensure_ascii=False).encode()).hexdigest()[:16]
        print(f"  {role}: 順位の組 {len(g.ranked_groups(role))} 件（うち需給 {n_demand_seen} 件）"
              f" → ふるいを通る組 {len(seq)} 件 / 並びの指紋 {h}")
        ok(all(f not in names for f, _t, _l, _h in seq),
           f"{role} の「ふるいを通る組」に需給が1つも入らない（＝◯位の指し先が需給に化けない）")
        _ = tfs_ok


# ---------------------------------------------------------------- C1
def c1() -> None:
    """H2・G2 の「検査済みの印」が、いまのファイルとまだ合っているか（印の失効の検出）。"""
    print("=" * 96)
    print("[C1] H2・G2 の検査済みの印が、いまのファイルと合っているか")
    print("=" * 96)
    repo = ROOT.parents[1]
    for nm in ("h2_pass.json", "g2_pass.json"):
        p = repo / ".claude" / "state" / nm
        d = json.loads(p.read_text(encoding="utf-8"))
        files = d.get("files") or {}
        if isinstance(files, list):                       # 一覧だけ持つ形（h2_pass）
            files = {x: None for x in files}
        print(f"  {nm}: 印 {str(d.get('fingerprint'))[:16]}… / 対象 {len(files)} 件"
              f"（1件ずつのハッシュ値を持つか = {any(v for v in files.values())}）")
        ng = []
        digest = hashlib.sha256()
        for rel in sorted(files):
            h = files[rel]
            f = repo / rel
            if not f.exists():
                ng.append((rel, "無い"))
                continue
            now = hashlib.sha256(f.read_bytes()).hexdigest()
            digest.update(f"{rel}:{now}\n".encode())
            if h and now != h:
                ng.append((rel, f"{h[:12]} -> {now[:12]}"))
        # ★印の作り方（enforce_h2_pass.fingerprint と同じ）で取り直して照らす＝印が今も有効か
        h = hashlib.sha256()
        for rel in sorted(files):
            f = repo / rel
            h.update(rel.encode())
            h.update(hashlib.sha256(f.read_bytes()).digest() if f.exists() else b"<missing>")
        now_fp = h.hexdigest()
        print(f"     監査が取り直した指紋 = {now_fp[:16]}… / 印 = {str(d.get('fingerprint'))[:16]}…")
        ok(now_fp == d.get("fingerprint"),
           f"{nm} の印が、いまのファイルと一致（＝印は失効していない）")
        for rel, why in ng:
            print(f"     - 食い違い {rel}: {why}")
        ok(not ng, f"{nm} の対象ファイルが、印を取ったときから1つも変わっていない（食い違い {len(ng)} 件）")


def main() -> int:
    ap = argparse.ArgumentParser()
    for f in ("a1", "a2", "a3", "a4", "b1", "b2", "b3", "c1"):
        ap.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    run = [k for k in ("a1", "a2", "a3", "a4", "b1", "b2", "b3", "c1") if getattr(a, k) or a.all]
    if not run:
        ap.print_help()
        return 2
    for k in run:
        globals()[k]()
        print()
    print("=" * 96)
    print(f"監査の測り: NG {len(FAILS)} 件")
    for m in FAILS:
        print(f"  NG {m}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())

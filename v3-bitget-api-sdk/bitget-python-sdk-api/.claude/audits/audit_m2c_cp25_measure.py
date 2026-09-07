#!/usr/bin/env python3
"""audit_m2c_cp25_measure.py — 監査 CP25 の2段目（M2-C の要件①②）を機械で測る

なぜ在るか:
  まこさん指示 2026-09-06「手で数えるのを禁じる → audit_m2c_scan.py」。
  cp24 の `audit_m2c_scan.py` が数えるのは「実装の形」（欄・関数・呼び出しの件数）だけで、
  **「案に実際に出てくるか」「印から外すと案から消えるか」は数えていません。**
  要件①②はそこでしか判定できないので、その2つを測る口をこのファイルに足しました。

測るもの（2つ）:
  ① 印（indicator_switch.json）から材料を外すと、案に1件も出なくなるか
     ＝指標（family）・レンジ幾何（geo）・需給（demand）・時間帯（time）の4種類
  ② 足した部品（需給3件・MMI）が、案に実際に何回 出てくるか

やり方（正直に書く）:
  ・案は `engine_tuner_gen.py --dry-run N` を子プロセスで走らせて作り、
    その出力の「使った材料と回数」をそのまま読みます（監査は手で数えません）。
  ・材料の名前 → 種類（family/geo/demand/time）の対応は、実物の定義表
    （indicator_reference_diag の RANGE_GEO_REF・TIME_REF・DEMAND_REF・find）から引きます。
    ＝一覧を監査が手で並べません。
  ・候補の数（母数）は `--probe` モードで実物の関数（material_pool・_lineage_candidates）を
    呼んで数えます。乱数に左右されないので、案に出た回数が 0 でも「候補から消えたか」を
    はっきり言えます。
  ・印は一時的に書き替えます。**必ず元に戻し、戻ったことを sha256 で確かめて印字します。**

正直な限界:
  ・案は乱数で作るので、回数の絶対値は N と種で変わります（比較は同じ N・同じ種で行います）。
  ・「案に出る」＝「net が増える」ではありません。ここで測るのは出るかどうかだけです。
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve()
SDK = HERE.parents[2]
PR = SDK / "scripts/priority_rebuild"
SW = SDK / ".claude/ratchet/indicator_switch.json"

N_DRY = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--n=")), "50"))


# ══ probe（子プロセス側）＝実物の関数を呼んで候補の数を数える ════════════════════════════
def probe() -> int:
    sys.path.insert(0, str(PR))
    import engine_tuner_gen as gen                       # noqa: E402
    import indicator_reference_diag as iref              # noqa: E402

    pool, _tfs, _cat = gen.material_pool()
    fam_pool: dict[str, int] = {}
    for p in pool:
        fam_pool[str(p["family"])] = fam_pool.get(str(p["family"]), 0) + 1

    tbl = gen.load_signal_table()
    by = gen._pool_families_by_lineage(pool)
    lm = dict(gen.KENSHU_LIMITS)
    extra: dict[str, int] = {}
    detail: dict[str, dict] = {}
    for role, rr in tbl["roles"].items():
        cands_by_lin = gen._lineage_candidates(role, rr, tbl, by, lm)
        detail[role] = {k: {"別枠": sum(1 for c in v if isinstance(c, dict)),
                            "指標": sum(1 for c in v if not isinstance(c, dict))}
                        for k, v in cands_by_lin.items()}
        for _k, cands in cands_by_lin.items():
            for c in cands:
                if isinstance(c, dict):
                    kind = next(iter(c))
                    extra[kind] = extra.get(kind, 0) + 1
    print(json.dumps({
        "pool_件数": len(pool),
        "pool_指標の種類数": len(fam_pool),
        "pool_MMI": {k: v for k, v in fam_pool.items() if k.startswith("MMI")},
        "別枠の候補": extra,
        "別枠の候補_合計": sum(extra.values()),
        "定義表_geo": sorted(iref.RANGE_GEO_REF),
        "定義表_time": sorted(iref.TIME_REF),
        "定義表_demand": sorted(iref.DEMAND_REF),
        "役割ごとの系統の候補": detail,
    }, ensure_ascii=False))
    return 0


# ══ 親プロセス側 ══════════════════════════════════════════════════════════════════════
def gate_probe() -> int:
    """案の審査（`assert_provenance`）が、別枠3種を印で捨てるか を直に試す。

    ★T33-a〜c は指標（family）しか試していない（実測＝`grep -n "T33" engine_tuner_gen.py`）。
      別枠3種の審査の枝（gen:716・723・730）を試す枝は自己検査に1件も無いので、監査が直に呼ぶ。
    """
    sys.path.insert(0, str(PR))
    import engine_tuner_gen as gen                       # noqa: E402
    import engine_tuner_exec as ex                       # noqa: E402

    tbl = gen.load_signal_table()
    sw = ex.load_indicator_switch()
    plan = [("geo", "_geo_set", (tbl.get("geo_ok") or [None])[0]),
            ("demand", "_demand_set", (tbl.get("demand_ok") or [None])[0]),
            ("time", "_time_set", (tbl.get("time_ok") or [None])[0])]
    out = {}
    for kind, setkey, name in plan:
        if name is None:
            out[kind] = "型の表に候補が無い"
            continue
        cond = {"role": "trigger", "form": "level", "side": "above", "material": [{kind: name}]}

        def call() -> str:
            try:
                gen.assert_provenance(cond, where="監査")
                return "通した"
            except gen.SampleError as e:
                return ("印で止めた" if "印が「使わない」" in str(e) else "別の理由で止めた: "
                        + str(e)[:60])
        on_res = call()
        keep = set(sw[setkey])
        try:
            sw[setkey] = set()
            off_res = call()
        finally:
            sw[setkey] = keep
        back_res = call()
        out[kind] = {"材料": name, "印がオン": on_res, "印がオフ": off_res, "戻した後": back_res}
    print(json.dumps(out, ensure_ascii=False))
    return 0


def rank_probe() -> int:
    """成績表の順位のどこに MMI と需給が居るかを数える。

    ★場面の判定の束は「成績表の1位から順に使う」（`ranked_materials` の逐語・2026-08-23 まこさん決定）。
      ＝成績表に**載っている**ことと、束に**引かれる**ことは別。順位を出さないと後者は言えない。
    """
    sys.path.insert(0, str(PR))
    import engine_tuner_gen as gen                       # noqa: E402

    out = {}
    for role in ("env", "location", "sufficiency", "trigger"):
        try:
            rk = gen.ranked_materials(role)
        except Exception as e:                            # noqa: BLE001
            out[role] = f"引けない: {type(e).__name__} {str(e)[:60]}"
            continue
        names = [str(c) for c, _a, _l, _h in rk]
        best = {}
        for tag in ("MMI", "taker_ls", "L-S比", "CVD"):
            hits = [i + 1 for i, n in enumerate(names) if n.split("__")[0].startswith(tag)]
            best[tag] = {"最上位": hits[0] if hits else None, "件数": len(hits)}
        out[role] = {"順位の全件数": len(names), "上位5件": names[:5], **best}
    print(json.dumps(out, ensure_ascii=False))
    return 0


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def run_probe() -> dict:
    r = subprocess.run([sys.executable, str(HERE), "--probe"], cwd=str(PR),
                       capture_output=True, text=True)
    if r.returncode != 0:
        return {"エラー": (r.stderr or r.stdout).strip()[-400:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def run_dry(n: int) -> dict:
    """--dry-run を走らせて「使った材料と回数」を返す。"""
    r = subprocess.run([sys.executable, str(PR / "engine_tuner_gen.py"), "--dry-run", str(n)],
                       cwd=str(PR), capture_output=True, text=True)
    lines = (r.stdout or "").splitlines()
    try:
        s = next(i for i, x in enumerate(lines) if x.strip() == "{")
        e = max(i for i, x in enumerate(lines) if x.strip() == "}")
        d = json.loads("\n".join(lines[s:e + 1]))
    except Exception:
        return {"エラー": (r.stderr or r.stdout).strip()[-400:], "rc": r.returncode}
    d["_拒否"] = next((x for x in lines if x.startswith("[生成拒否]")), "")
    d["_rc"] = r.returncode
    return d


def classify(used: dict, refs: dict) -> dict:
    """使った材料の名前を、実物の定義表を使って 4種類に分ける（一覧を手で並べない）。"""
    sys.path.insert(0, str(PR))
    import indicator_reference_diag as iref              # noqa: E402
    out = {"family": {}, "geo": {}, "time": {}, "demand": {}, "?": {}}
    for key, cnt in used.items():
        base = str(key).split("__")[0]
        if base in refs["定義表_geo"]:
            out["geo"][base] = out["geo"].get(base, 0) + cnt
            continue
        if base in refs["定義表_time"]:
            out["time"][base] = out["time"].get(base, 0) + cnt
            continue
        if base in refs["定義表_demand"]:
            out["demand"][base] = out["demand"].get(base, 0) + cnt
            continue
        ent, _p = iref.find(base)
        if ent is not None:
            f = str(ent["family"])
            out["family"][f] = out["family"].get(f, 0) + cnt
        else:
            out["?"][base] = out["?"].get(base, 0) + cnt
    return out


def with_switch(mutate) -> tuple[dict, dict]:
    """印を書き替えて（probe, dry）を測り、必ず元に戻す。"""
    raw = SW.read_bytes()
    try:
        d = json.loads(raw.decode("utf-8"))
        mutate(d)
        SW.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        return run_probe(), run_dry(N_DRY)
    finally:
        SW.write_bytes(raw)


def _off_mmi(d: dict) -> None:
    """印から MMI を外す（`on` から抜いて `off` に入れる）。★順に書く＝先に抜くと集合が空になる。"""
    mmi = [x for x in d["on"] if str(x).startswith("MMI")]
    d["on"] = [x for x in d["on"] if not str(x).startswith("MMI")]
    d["off"] = sorted(set(d["off"]) | set(mmi))


def main() -> int:
    if "--probe" in sys.argv:
        return probe()
    if "--gate-probe" in sys.argv:
        return gate_probe()
    if "--rank-probe" in sys.argv:
        return rank_probe()

    before = sha(SW)
    L: list[str] = []
    L.append("<!-- SCAN25_START audit_m2c_cp25_measure.py が実物を走らせて書き出す＝手で書き換えない -->")
    L.append("")
    L.append(f"**測り方**＝`engine_tuner_gen.py --dry-run {N_DRY}` を走らせ、その出力の"
             "「使った材料と回数」を読む。材料 → 種類の対応は実物の定義表から引く。"
             "候補の数は `material_pool` と `_lineage_candidates` を直に呼んで数える。")
    L.append("")

    base_probe = run_probe()
    base_dry = run_dry(N_DRY)
    base_used = base_dry.get("使った材料と回数", {})
    base_cls = classify(base_used, base_probe)

    L.append("### B-1｜いまの印のまま（基準）")
    L.append("")
    L.append(f"- 案＝**{base_dry.get('構造数')} 本**／触れた列＝**{base_dry.get('触れた列')}**"
             f"／{base_dry.get('_拒否', '')}")
    L.append(f"- 材料の候補（`material_pool`）＝**{base_probe.get('pool_件数')} 件**"
             f"／指標の種類＝**{base_probe.get('pool_指標の種類数')}**")
    L.append(f"- 別枠の候補（`_lineage_candidates` が返す dict）＝"
             f"**{base_probe.get('別枠の候補_合計')} 件** {json.dumps(base_probe.get('別枠の候補', {}), ensure_ascii=False)}")
    L.append(f"- MMI の候補＝{json.dumps(base_probe.get('pool_MMI', {}), ensure_ascii=False) or '**0件**'}")
    L.append("")
    L.append("| 種類 | 案に出た回数の合計 | 内訳 |")
    L.append("|---|---|---|")
    for k in ("family", "geo", "demand", "time", "?"):
        v = base_cls[k]
        inner = json.dumps(v, ensure_ascii=False) if k != "family" else \
            json.dumps(dict(sorted(v.items(), key=lambda x: -x[1])[:6]), ensure_ascii=False) + " …"
        L.append(f"| `{k}` | **{sum(v.values())}** | {inner if v else '**0件**'} |")
    L.append("")
    mmi_used = {k: v for k, v in base_cls["family"].items() if k.startswith("MMI")}
    L.append(f"- **足した部品が案に出た回数**＝需給 {json.dumps(base_cls['demand'], ensure_ascii=False) or '0'}"
             f" ／ MMI {json.dumps(mmi_used, ensure_ascii=False) or '**0件**'}")
    L.append("")

    # ★オフにする指標は、基準でいちばん多く出たものを機械で選ぶ（監査が手で選ばない）
    top_fam = max(base_cls["family"].items(), key=lambda x: x[1])[0] if base_cls["family"] else None

    cases = [
        ("指標（family）＝基準で最多の " + str(top_fam),
         "family", top_fam,
         lambda d, f=top_fam: (d.__setitem__("on", [x for x in d["on"] if x != f]),
                               d.__setitem__("off", sorted(set(d["off"]) | {f})))),
        ("指標（family）＝MMI（足した部品）",
         "family", "MMI", _off_mmi),
        ("レンジ幾何（geo）を空にする", "geo", None, lambda d: d.__setitem__("geo_on", [])),
        ("需給（demand）を空にする", "demand", None, lambda d: d.__setitem__("demand_on", [])),
        ("時間帯（time）を空にする", "time", None, lambda d: d.__setitem__("time_on", [])),
        ("別枠3種を全部 空にする（b33 と同じ壊し方）", "extra", None,
         lambda d: [d.__setitem__(k, []) for k in ("geo_on", "demand_on", "time_on")]),
    ]

    L.append(f"### B-2｜印から外したときに、案から消えるか（同じ N={N_DRY}・同じ種）")
    L.append("")
    L.append("| 壊し方 | 候補の数（前 → 後） | 案に出た回数（前 → 後） | 判定 |")
    L.append("|---|---|---|---|")
    for title, kind, target, mut in ([] if "--quick" in sys.argv else cases):
        pr, dr = with_switch(mut)
        used = dr.get("使った材料と回数", {})
        cls = classify(used, base_probe) if used else {k: {} for k in
                                                       ("family", "geo", "time", "demand", "?")}
        if kind == "family" and target == "MMI":
            b = sum(v for k, v in base_cls["family"].items() if k.startswith("MMI"))
            a = sum(v for k, v in cls["family"].items() if k.startswith("MMI"))
            cb = sum(base_probe.get("pool_MMI", {}).values())
            ca = sum(pr.get("pool_MMI", {}).values())
        elif kind == "family":
            b = base_cls["family"].get(target, 0)
            a = cls["family"].get(target, 0)
            cb = base_probe.get("pool_指標の種類数", 0)
            ca = pr.get("pool_指標の種類数", 0)
        elif kind == "extra":
            b = sum(base_cls[x].get(y, 0) for x in ("geo", "demand", "time") for y in base_cls[x])
            a = sum(sum(cls[x].values()) for x in ("geo", "demand", "time"))
            cb = base_probe.get("別枠の候補_合計", 0)
            ca = pr.get("別枠の候補_合計", 0)
        else:
            b = sum(base_cls[kind].values())
            a = sum(cls[kind].values())
            cb = base_probe.get("別枠の候補", {}).get(kind, 0)
            ca = pr.get("別枠の候補", {}).get(kind, 0)
        ok = "✅ 消えた" if a == 0 and b > 0 else (
            "⚠️ 基準で0件＝測れない" if b == 0 else "❌ 残っている")
        L.append(f"| {title} | {cb} → **{ca}** | {b} → **{a}** | {ok} |")
    L.append("")

    # ★B-4＝引く確率が、系統の中の候補の数でどれだけ違うかを機械で出す。
    #   引き方＝①役割の使える系統から一様に1つ ②その系統の中から一様に1つ（実物 _pick_material）。
    L.append("### B-4｜役割ごとの「系統 → その中の候補」の数と、1回引いたときにその部品が出る確率")
    L.append("")
    L.append("| 役割 | 系統 | 別枠の候補 | 指標の候補 | 系統の数 | 別枠1件が引かれる確率 |")
    L.append("|---|---|---|---|---|---|")
    for role, lins in (base_probe.get("役割ごとの系統の候補") or {}).items():
        nlin = len(lins)
        for lin, c in lins.items():
            if c["別枠"] == 0:
                continue
            p = (1.0 / nlin) * (1.0 / (c["別枠"] + c["指標"]))
            L.append(f"| {role} | {lin} | **{c['別枠']}** | {c['指標']} | {nlin} | "
                     f"**{p * 100:.2f}%** |")
    L.append("")

    after = sha(SW)
    L.append(f"### B-3｜印を元に戻したか（sha256 の先頭16文字）")
    L.append(f"- 測る前＝`{before}` ／ 測った後＝`{after}` ／ "
             f"{'✅ 同じ（作業ツリーへの正味の変更ゼロ）' if before == after else '❌ 戻っていない'}")
    L.append("")
    L.append("<!-- SCAN25_END -->")
    print("\n".join(L))
    return 0 if before == after else 1


if __name__ == "__main__":
    sys.exit(main())

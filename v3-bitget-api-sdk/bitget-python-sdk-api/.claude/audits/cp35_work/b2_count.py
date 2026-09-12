"""B2＝段ごとの候補の本数（設計書の 630／112／1／289）を、監査が自分で数え直す。"""
import sys
sys.path.insert(0, "scripts/priority_rebuild")
import engine_tuner_gen as g            # noqa: E402
import engine_tuner_exec as ex          # noqa: E402
import indicator_reference_diag as iref  # noqa: E402

table = g.load_signal_table()
pool, tfs, _ = g.material_pool()
ranges = g.material_ranges()
tfs_all = list(table["tfs"])
upper = [t for t in tfs_all if tfs_all.index(t) > tfs_all.index("5m")]
drop = {"1m", "3m", "10m"}
upper_kept = [t for t in upper if t not in drop]
print("型の表の時間足:", tfs_all)
print("執行足より上:", upper, " ／ 1m・3m・10m を外した後:", upper_kept)

STAGE1 = ["W%", "帯内位置%", "S-Rタッチ数", "pivotPP", "pivotR1", "pivotS1",
          "n本高値", "n本安値", "close vs EMA", "close vs SMA",
          "Keltner上", "Keltner下", "POC", "VAH", "VAL"]


def usable(role, fams, label=None, tf_ok=None):
    rr = table["roles"][role]
    ok = set(tf_ok if tf_ok is not None else g._role_tfs(tfs, table, role))
    n = 0
    seen = []
    for fam, tf, lab, hor, med, ncol, col in g.ranked_groups(role, label):
        if fams and fam not in set(fams):
            continue
        if tf not in ok or fam not in iref.FAMILY_LINEAGE or fam not in ranges:
            continue
        if iref.FAMILY_LINEAGE[fam]["k"] not in rr["lineages"]:
            continue
        if not g._group_usable(fam, tf, ranges, table):
            continue
        n += 1
        seen.append((fam, tf, lab, hor))
    return n, seen


laws = g.laws_for_scene("range")
fams_r5, _s5 = g._law_families(laws, "R5")
fams_r6, _s6 = g._law_families(laws, "R6")
print("R5 が名指しした family:", list(fams_r5))
print("R6 が名指しした family:", list(fams_r6))
print()

n1a, _ = usable("location", STAGE1, None, upper)
n1b, _ = usable("location", STAGE1, None, upper_kept)
n1all, _ = usable("location", None, None, upper_kept)
print(f"段1（帯）  §2.2 の候補で絞る・上位足7本         = {n1b} 本（1m/3m/10m を落とす前は {n1a}）")
print(f"           ★絞らず location の全部だと            = {n1all} 本")

n2a, _ = usable("env", fams_r5, "強さ", upper_kept)
n2a_all, _ = usable("env", fams_r5, None, upper_kept)
print(f"段2a（強さの否定）R5 の8つ・札「強さ」・上位足   = {n2a} 本（札を絞らないと {n2a_all}）")

n2c, _ = usable("sufficiency", fams_r6, None, upper_kept)
n2c_lab, _ = usable("sufficiency", fams_r6, "強さ", upper_kept)
print(f"段2c（3枠目）R6 の6つ・上位足                    = {n2c} 本（+「なし」で {n2c+1}）／札「強さ」だけなら {n2c_lab}")

lm, _w = g.load_limits()
print()
print("段3 の範囲:", {k: lm.get(k) for k in ("int_range", "state_hold_bars_range", "quantile_grid", "quantile_range")})

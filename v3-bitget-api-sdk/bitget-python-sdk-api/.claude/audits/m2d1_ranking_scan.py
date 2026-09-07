#!/usr/bin/env python3
"""m2d1_ranking_scan.py — M2-D-1（いまの繋がりと成績表の中身を、実物で数える）の数え上げを機械で出す（2026-09-06）

なぜ在るか:
  M2-D-1 の中身5つ（milestones2 §3 の M2-D-1）のうち ①②④⑤ を、CC が手で数えずに実物から引くため。
  前例＝audit_m2c_scan.py（監査 CP24・まこさん指摘「自動生成にしてないって一番ありえない」）と同じ置き場・同じ考え。
  ★読むだけ。何も書かない。material_ranking.json・signal_families.json・indicator_switch.json は1文字も変えない。

使い方:
  python3 .claude/audits/m2d1_ranking_scan.py
  python3 .claude/audits/m2d1_ranking_scan.py --assert-demand   # 需給3列が成績表に載っていなければ rc=1（設計書 demand-in-ranking-20260907 の完成の条件1）

正直な限界:
  ・⑤の「候補」の一覧（CANDIDATES）は、worklog 20260901 §19 の逐語から CC が名前を写したもの＝人が書いた。
    候補 → 部品の当て方は「部品名にその文字が入っているか」だけ＝意味の照合ではない。当たった部品名は全部 出す。
  ・印の判定は engine_tuner_exec.indicator_enabled をそのまま呼ぶ（判定を書き写さない）。
"""
from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

SDK = pathlib.Path(__file__).resolve().parents[2]
PR = SDK / "scripts/priority_rebuild"
sys.path.insert(0, str(PR))
import engine_tuner_exec as ex          # noqa: E402  印の判定（indicator_enabled ほか）
import indicator_reference_diag as iref  # noqa: E402  部品名 → 種類

RANK = SDK / ".claude/ratchet/material_ranking.json"
SF = SDK / ".claude/ratchet/signal_families.json"
SW = SDK / ".claude/ratchet/indicator_switch.json"

# ⑤ 候補（worklog 20260901 §19「検索方法」の逐語から名前だけ写した・段2b の rg5_uptrend は部品ではないので載せない）
#   ★当て方＝部品名の先頭に対する正規表現（re.match）。文字の一致だけ（「W%」が RAINBOW% に当たる等）を避けるため。
CANDIDATES: list[tuple[str, str, list[str]]] = [
    ("段1 帯", "レンジ幾何 W%・帯内位置%（別枠 geo）", [r"W%（", r"帯内位置%（"]),
    ("段1 帯", "S-Rタッチ数（窓144〜288×許容幅0.0015〜0.006）", [r"S-Rタッチ数\("]),
    ("段1 帯", "pivot 3種（PP・R1・S1）", [r"close vs pivot(PP|R1|S1)%"]),
    ("段1 帯", "n本高安（20〜96）", [r"close vs \d+本(高値|安値)%", r"fractal(高値|安値)距離%"]),
    ("段1 帯", "close vs EMA%・SMA%・Keltner", [r"close vs EMA\d+%", r"close vs SMA\d+%", r"close vs Keltner"]),
    ("段1 帯", "POC・VAH・VAL", [r"close vs (POC|VAH|VAL)%"]),
    ("段1 帯", "転換線・基準線", [r"close vs (転換線|基準線)%"]),
    ("段2a 強さの否定", "ADX", [r"ADX\d+$"]),
    ("段2a 強さの否定", "CHOP", [r"CHOP\d+$"]),
    ("段2a 強さの否定", "ER", [r"ER\d+$"]),
    ("段2a 強さの否定", "VHF", [r"VHF\d+$"]),
    ("段2a 強さの否定", "MACDヒスト%", [r"MACDヒスト%"]),
    ("段2a 強さの否定", "EMA傾き", [r"EMA\d+傾き%"]),
    ("段2a 強さの否定", "DI差の絶対値", [r"DI差\d+$"]),
    ("段2a 強さの否定", "MMI（M2-C-4 で足した）", [r"MMI\d+$"]),
    ("段2c 3枠目・ばらつき", "BB幅", [r"BB幅\("]),
    ("段2c 3枠目・ばらつき", "ATR%", [r"ATR%\d+$"]),
    ("段2c 3枠目・ばらつき", "realized_vol", [r"realized_vol\d+$"]),
    ("段2c 3枠目・ばらつき", "Donchian幅", [r"Donchian幅"]),
    ("段2c 3枠目・ばらつき", "stdev%", [r"stdev%\d+$"]),
    ("段2c 3枠目・出来高", "volume_ratio", [r"volume_ratio\d+$"]),
    ("段2c 3枠目・出来高", "CMF", [r"CMF\d+$"]),
    ("段2c 3枠目・出来高", "EFI比", [r"EFI比\d+$"]),
    ("段2c 3枠目・出来高", "EOM比", [r"EOM比\d+$"]),
    ("段2c 3枠目・出来高", "PVT傾き", [r"PVT傾き\d+$"]),
    ("段2c 3枠目・位置・形", "BB%b と 0.5 の差", [r"BB%b\("]),
    ("段2c 3枠目・位置・形", "高安からの経過（10〜40本）", [r"(高値|安値)からの経過バー\d+$"]),
    ("段2c 3枠目・時刻", "時刻（hour_range 6〜18）・曜日（別枠 time）", [r"時刻（", r"曜日（"]),
    ("段2c 3枠目・需給", "需給3件（taker_ls・L-S比・CVD＝別枠 demand・M2-C-4 で足した）", [r"(taker_ls|L-S比|CVD)（"]),
]


def _name(n: str) -> str:
    return n.rsplit("__", 1)[0] if "__" in n else n


def assert_demand() -> int:
    """需給3列（DEMAND_REF の鍵）が成績表の順位に載っているか。載っていなければ rc=1（承認のプログラムが走らせる口）。

    ★測るのは実物の成績表（material_ranking.json）＝合成データではない。
    ★載ったかどうかだけを見る（分離力の良し悪しは見ない＝線を引かない）。
    """
    rk = json.loads(RANK.read_text(encoding="utf-8"))
    listed: set[str] = set()
    for labs in rk["順位"].values():
        for hors in labs.values():
            for rows in hors.values():
                for col, _acc in rows:
                    listed.add(_name(col))
    want = sorted(iref.DEMAND_REF)
    hit = [n for n in want if n in listed]
    miss = [n for n in want if n not in listed]
    print(f"[--assert-demand] 需給 {len(want)} 列のうち成績表の順位に載っているのは {len(hit)} 列: 載っている={hit} 載っていない={miss}")
    return 0 if not miss else 1


def diff_before() -> int:
    """控え（material_ranking.before_add_demand.json）と いまの成績表を比べ、需給以外の列が1本も変わっていないかを照らす。

    ★差分の走行（--rank-regime --add-demand）の前後の突き合わせ（設計書 demand-in-ranking-20260907 の自己検査④）。
    変わっていれば rc=1。
    """
    bak = RANK.with_name("material_ranking.before_add_demand.json")
    if not bak.exists():
        print(f"[--diff-before] 控えが無い: {bak}")
        return 1
    a = json.loads(bak.read_text(encoding="utf-8"))
    b = json.loads(RANK.read_text(encoding="utf-8"))

    def _wo(o):
        return {ro: {la: {hn: [x for x in rows if _name(str(x[0])) not in iref.DEMAND_REF]
                          for hn, rows in hors.items()} for la, hors in labs.items()} for ro, labs in o["順位"].items()}

    same = json.dumps(_wo(a), sort_keys=True, ensure_ascii=False) == json.dumps(_wo(b), sort_keys=True, ensure_ascii=False)
    keys = ["窓", "行数", "先を見るバー数", "時間足", "どの役割にも入らなかった列"]
    same_meta = all(a.get(k) == b.get(k) for k in keys)
    print(f"[--diff-before] 需給以外の順位の中身: {'一致' if same else '違う'} ／ 窓・行数・先読み・時間足・役割外の列: {'一致' if same_meta else '違う'}")
    print(f"[--diff-before] 測れた列 {a.get('測れた列')} → {b.get('測れた列')} ／ 載った列 {a.get('順位に載った列')} → {b.get('順位に載った列')}"
          f" ／ 省いた列 {len(a.get('省いた列') or {})} → {len(b.get('省いた列') or {})}")
    return 0 if (same and same_meta) else 1


def main() -> int:
    if "--assert-demand" in sys.argv:
        return assert_demand()
    if "--diff-before" in sys.argv:
        return diff_before()
    rk = json.loads(RANK.read_text(encoding="utf-8"))
    sf = json.loads(SF.read_text(encoding="utf-8"))
    sw = json.loads(SW.read_text(encoding="utf-8"))

    print("═══ ① 成績表 material_ranking.json ═══")
    print("窓", rk["窓"], "／ 行数", rk["行数"], "／ 先を見るバー数", rk["先を見るバー数"])
    print("時間足", len(rk["時間足"]), "本 =", rk["時間足"])
    print("測れた列", rk["測れた列"], "／ 順位に載った列", rk["順位に載った列"],
          "／ どの役割にも入らなかった列", len(rk["どの役割にも入らなかった列"]))
    allcols: set[str] = set()
    per_role: dict[str, set[str]] = {}
    for role, labs in rk["順位"].items():
        s: set[str] = set()
        for lab, hors in labs.items():
            for hor, rows in hors.items():
                for col, _acc in rows:
                    s.add(col)
                    allcols.add(col)
        per_role[role] = s
        hs = sorted({h for l in labs.values() for h in l}, key=int)
        print(f"役割 {role}: ラベル={sorted(labs)} 先読み={hs} 一意の列={len(s)}")
    print("一意の列の合計（役割をまたいで重複を除く）", len(allcols))

    print("═══ ② M2-C-4 で足した部品・外した部品が、成績表と型の表に何本 在るか ═══")
    parts = sf.get("parts") or []
    names = [p if isinstance(p, str) else p.get("name", str(p)) for p in parts]
    ep = sf.get("extra_parts") or {}

    def c_rank(pred) -> int:
        return sum(1 for c in allcols if pred(_name(c)))

    def c_tbl(pred) -> int:
        return sum(1 for n in names if pred(n))

    rows2 = [
        ("MMI（足した）", lambda n: n.startswith("MMI")),
        ("S-RタッチATR（2026-09-06 に外した）", lambda n: "S-R" in n and "ATR" in n),
        ("需給 taker_ls／L-S比／CVD（足した・別枠）", lambda n: any(k in n for k in ("taker_ls", "L-S比", "CVD"))),
    ]
    for label, pred in rows2:
        print(f"{label}: 成績表 {c_rank(pred)} 本 ／ 型の表 parts {c_tbl(pred)} 本")
    print("型の表 parts 総数", len(names), "／ MMI の部品名", [n for n in names if n.startswith("MMI")])
    for k, v in ep.items():
        print(f"型の表 extra_parts.{k} =", v.get("parts") if isinstance(v, dict) else v)

    print("═══ ④ 印（indicator_switch.json）で「使わない」を外した後に、役割ごとに何本 残るか ═══")
    print("印 counts", sw["counts"])
    print("印 geo_on", sw.get("geo_on"), "／ demand_on", sw.get("demand_on"), "／ time_on", sw.get("time_on"))
    for role in sorted(per_role):
        before = per_role[role]
        keep = [c for c in before if ex.indicator_enabled(_name(c))]
        print(f"{role}: 印を当てる前 {len(before)} 本 → 後 {len(keep)} 本（外れた {len(before) - len(keep)} 本）")
    keep_all = [c for c in allcols if ex.indicator_enabled(_name(c))]
    print("合計（重複を除く）: 前", len(allcols), "→ 後", len(keep_all))
    # 役割 × 種類（印がオンの列だけ・種類ごとの列数）
    print("── 印を当てた後の 役割 × 種類 の列数（上位20種類だけ表示） ──")
    for role in sorted(per_role):
        fam_cnt: collections.Counter = collections.Counter()
        for c in per_role[role]:
            nm = _name(c)
            if not ex.indicator_enabled(nm):
                continue
            ent, _ = iref.find(nm)
            fam_cnt[ent["family"] if ent else "?"] += 1
        top = ", ".join(f"{f}={n}" for f, n in fam_cnt.most_common(20))
        print(f"{role}: 種類 {len(fam_cnt)} ／ {top}")

    print("═══ ⑤ 候補×部品の突き合わせ（§2.2 の段0①） ═══")
    on_parts = [n for n in names if ex.indicator_enabled(n)]
    print("いまの範囲＝型の表 parts のうち 印がオンの部品", len(on_parts), "本（M2-B-4 の実測 2026-09-01 は 147 本）")
    extra_names: list[str] = []
    for k, v in ep.items():
        for n in (v.get("parts") if isinstance(v, dict) else v) or []:
            extra_names.append(f"{n}（別枠 {k}）")
    print("別枠の部品", len(extra_names), "本 =", extra_names)
    pool = on_parts + extra_names
    print("| 段 | 候補 | 当たった部品（範囲＝印オン＋別枠） | 本数 | 成績表に在る本数 |")
    print("|---|---|---|---|---|")
    for stage, cand, keys in CANDIDATES:
        pats = [re.compile(k) for k in keys]
        hit = [n for n in pool if any(p.match(n) for p in pats)]
        in_rank = sum(1 for c in allcols if any(p.match(_name(c)) for p in pats))
        shown = ", ".join(hit[:12]) + (f" …ほか{len(hit) - 12}" if len(hit) > 12 else "")
        print(f"| {stage} | {cand} | {shown if hit else '（0件）'} | {len(hit)} | {in_rank} |")

    # ⑥ 生成器が実際に使う順位（M2-D-2 (c)＝まこさんが目で見る材料・2026-09-06 決定「目で見る形にする」）
    #   engine_tuner_gen.ranked_groups をそのまま呼ぶ（順位の式を書き写さない）。
    #   並び＝種類×時間足×正解ラベル×先読み ごとに、その組の列の分離力の中央値を取り、|中央値−0.5| の大きい順。
    #   場面の判定の束が使うのは location と env だけ（M2-D の前提「この段でできないこと」）。
    print("═══ ⑥ 生成器が実際に使う順位（役割 location と env・上位15組）＝まこさんが目で見る材料 ═══")
    import engine_tuner_gen as gen  # noqa: E402
    #   ★env は正解ラベル「強さ」だけ＝sample_regime_build が env を引くときの実物（label="強さ"）と同じにする。
    #     location はラベルを絞らない（同じく実物の呼び出しどおり）。
    for role, label in (("location", None), ("env", "強さ")):
        rows = gen.ranked_groups(role, label)
        print(f"| {role}{'（ラベル＝' + label + '）' if label else '（ラベル全部）'} の順位 | 種類 | 時間足 | 正解ラベル | 先読み | 分離力の中央値 | 列の本数 | 代表の列 |")
        print("|---|---|---|---|---|---|---|---|")
        for i, (fam, tf, lab, hor, med, n, col) in enumerate(rows[:15], 1):
            print(f"| {i} | {fam} | {tf} | {lab} | {hor} | {med:.3f} | {n} | {col} |")
        print(f"（{role} の組の総数＝{len(rows)}）")

    # ⑥b 需給3列が、成績表の生の順位（json そのまま・印を当てない）で何位か（設計書 demand-in-ranking-20260907・工程表 3 の目視の材料）
    #   ★生成器の ranked_groups を通さない＝読む側（E）を直す前でも見える。並びは |分離力−0.5| の降順（json に書かれた順）。
    print("═══ ⑥b 需給3列の、成績表の生の順位（役割×ラベル×先読み ごとの位置と分離力・印は当てない） ═══")
    found = 0
    for role, labs in rk["順位"].items():
        for lab, hors in labs.items():
            for hor, rows2 in hors.items():
                for i, (col, acc) in enumerate(rows2, 1):
                    if _name(col) in iref.DEMAND_REF:
                        found += 1
                        print(f"| {role} | {lab} | {hor} | {col} | {float(acc):.3f} | {i} 位 ／ {len(rows2)} 本 |")
    print(f"（需給の行＝{found} 件。0 件なら、まだ成績表に需給は載っていない）")
    if rk.get("需給の被覆"):
        for nm, cv in rk["需給の被覆"].items():
            print(f"  被覆 {nm}: {cv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

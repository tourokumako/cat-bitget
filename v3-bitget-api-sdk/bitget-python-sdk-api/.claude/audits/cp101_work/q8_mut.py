#!/usr/bin/env python3
"""CP101 の Q8 の3つ目＝CP100 の Q8 の表の壊し方と Q9 の操作を、メモリの上の写しで試す。本物には1バイトも書かない。

CP100 が「素通り」と測った壊し方が、いま _s1_diff（T44 の本体）か読む口で止まるかを1件ずつ出す。
"""
import copy, json, pathlib, sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
sys.path.insert(0, str(ROOT / ".claude" / "tools"))
import check_one_path as cop  # noqa: E402

laws, r = cop._laws_reader()
real = r.ind
OFF = {"状態": "オフ"}


class Reader:
    """指標データの読む口の写し。使い方の行だけ差し替える。"""
    def __init__(self, usages):
        self._u = usages

    def __getattr__(self, n):
        return getattr(real, n)

    def usages(self, name=None):
        return [u for u in self._u if name is None or (u.get("指す物") or {}).get("指標の記録") == name
                or (u.get("指す物") or {}).get("部品の記録") == name]


def base_usages():
    return copy.deepcopy(real.usages())


def row(d, no):
    return next(x for x in d["法則の行"] if x["番号"] == no)


def s1diff(d, usages=None):
    """(止まったか, 文) を返す。"""
    try:
        rd = laws.Laws(d, reader=Reader(usages if usages is not None else base_usages()))
        why, same, _u, _s = cop._s1_diff(rd)
        return (bool(why), f"same={same}/12 " + "・".join(why)[:170])
    except SystemExit as e:
        return (True, f"読む口が止まった: {str(e)[:170]}")


def fresh():
    return copy.deepcopy(r.data)


def usage(us, name):
    return next(u for u in us if (u.get("指す物") or {}).get("指標の記録") == name and u.get("使い方の種類") == "前提崩れの印"
                and (u.get("場面と型") or {}).get("型") in ("flat_up", "down"))


print("=== 無傷の版の _s1_diff")
print(s1diff(fresh()))

print("=== CP100 Q8 の2つ目の表（修正3）")
results = []


def case(label, stopped_info):
    stopped, info = stopped_info
    results.append((label, stopped))
    print(f"{'止まる' if stopped else '素通り'} | {label} | {info}")


d = fresh()
row(d, "枝S1-MTFCUT")["動く条件"]["全部満たす"].pop()
case("条件の本数: MTFCUT の BB%b の条件を消す", s1diff(d))
d = fresh()
c = row(d, "枝S1-MTFCUT")["動く条件"]["全部満たす"][0]
c["側"] = "以上"
case("状態の条件の側: より下→以上", s1diff(d))
d = fresh()
cands = [x for x in row(d, "枝S1-TIME")["動く条件"]["全部満たす"]]
cands[0]["側"] = "より下"
case("状態の条件の側: 以上→より下（TIME）", s1diff(d))
us = base_usages()
usage(us, "RSI")["向き"] = "下側"
case("使い方の行の向き: RSI 上側→下側", s1diff(fresh(), us))
for nm, ax, val, lab in (("RSI", "n", 14, "RSI の n 9→14"), ("DI差", "n", 7, "DI差 14→7"), ("基準線", "k_", 13, "基準線 26→13")):
    us = base_usages()
    usage(us, nm)["パラメータの代表の値"][ax]["スキャル"] = [val]
    case(f"パラメータ: {lab}", s1diff(fresh(), us))
us = base_usages()
usage(us, "RSI")["玉の向き"] = "LONG"
case("玉の向き: RSI SHORT→LONG", s1diff(fresh(), us))
us = base_usages()
usage(us, "BB%b")["閾値"][0]["代表の値"]["スキャル"] = 0.5
case("BB%b の閾値 1.0129892→0.5", s1diff(fresh(), us))
d = fresh()
row(d, "枝S1-SL")["決済のしかた"]["側"] = "利の側"
case("決済の側: 損→利（SL）", s1diff(d))
d = fresh()
row(d, "枝S1-SL")["決済のしかた"].pop("値段が飛んだときの約定")
case("約定の見方: 欄を消す（SL）", s1diff(d))
d = fresh()
row(d, "枝S1-SHRINK")["値段の決め方"]["縮み始めの枝"] = "枝S1-TP1"
case("shrink の縮み始めの枝: TP2→TP1", s1diff(d))
d = fresh()
row(d, "枝S1-SL")["値段の決め方"].pop("幅の取り方")
case("zone_sl の幅の取り方: 欄を消す", s1diff(d))
d = fresh()
next(x for x in row(d, "売り方S1")["売り方の決まり"] if x["種類"] == "年齢を見ない型")["値"] = "flat_up"
case("年齢を見ない型: down→flat_up", s1diff(d))
d = fresh()
next(n for n in d["法則の中の数"] if n["名前"] == "S1_床の倍数")["代表の値"]["スキャル"] = 3
case("床の倍数 1→3", s1diff(d))

print("=== CP100 Q9 の1つ目（修正1・修正7）＝止めずに読めるのが正しい操作")


def reads(d, usages=None):
    try:
        return True, [x["番号"] for x in laws.Laws(d, reader=Reader(usages if usages is not None else base_usages())).rows()]
    except SystemExit as e:
        return False, str(e)[:160]


d = fresh()
for x in d["法則の行"]:
    if x["番号"] in ("枝S1-TP2", "枝S1-SHRINK", "確認S1"):
        x["オン/オフと注意"] = OFF
ok, out = reads(d)
print(f"読める={ok} 枝S1-TP2 を返さない={'枝S1-TP2' not in out if ok else out} | 枝S1-TP2・SHRINK・確認S1 を全部オフ")
d = fresh()
row(d, "売り方S1")["オン/オフと注意"] = OFF
ok, out = reads(d)
print(f"読める={ok} 売り方S1 を返さない={'売り方S1' not in out if ok else out} | 売り方S1 だけオフ")
d = fresh()
n = 0
for x in d["法則の行"]:
    if "S1" in str(x["番号"]):
        x["オン/オフと注意"] = OFF
        n += 1
ok, out = reads(d)
print(f"読める={ok} 残りの行数={len(out) if ok else out} | S1 の行 {n} 行を全部オフ")
d = fresh()
row(d, "枝S1-TP2")["オン/オフと注意"] = OFF
ok, out = reads(d)
print(f"止まる={not ok} {out if not ok else ''} | オンの行が指す枝S1-TP2 だけオフ（止まるのが正しい）")

rsi = next(u for u in real.usages("RSI") if (u.get("場面と型") or {}).get("型") == "flat_up")
for label, extra in (("RSI の LONG の行を足す", dict(copy.deepcopy(rsi), **{"玉の向き": "LONG"})),
                     ("別のオシレーター CCI の行を足す", dict(copy.deepcopy(rsi), **{"指す物": {"指標の記録": "CCI"}})),
                     ("部品 帯pivot の行を足す", dict(copy.deepcopy(rsi), **{"指す物": {"部品の記録": "帯pivot"}}))):
    try:
        s = laws.Laws(fresh(), reader=Reader(base_usages() + [extra])).solve("枝S1-MTFCUT")
        print(f"落ちない | {label} | 使い方の行={len(s['使い方の行'])} 使える物が無い={len(s['使える物が無い'])} 候補が複数={len(s['候補が複数'])}")
    except SystemExit as e:
        print(f"落ちた | {label} | {str(e)[:160]}")
us = [u for u in base_usages() if (u.get("指す物") or {}).get("指標の記録") != "RSI"]
s = laws.Laws(fresh(), reader=Reader(us)).solve("枝S1-MTFCUT")
print(f"RSI の使い方の行が返らない（オフの指標）| 使い方の行={len(s['使い方の行'])} 使える物が無い={len(s['使える物が無い'])} 候補が複数={len(s['候補が複数'])}（止まらないのが正しい）")

print("=== 修正2 FINSTOP の負の印")
print("  実物の 値を負にするか:", [c.get("値を負にするか") for c in row(fresh(), "枝型-FINSTOP")["動く条件"]["全部満たす"]])
d = fresh()
row(d, "枝型-FINSTOP")["動く条件"]["全部満たす"][0].pop("値を負にするか")
ng = laws.Laws(d, reader=real).check_sources()
print("  印を消すと --check-sources:", ng)

print("=== CP100 Q9 の3つ目（修正8）")


def must_stop(label, mutate):
    d = fresh()
    mutate(d)
    try:
        rd = laws.Laws(d, reader=real)
        extra = ""
        if label.startswith("オフの判定"):
            extra = f" 枝型-TP_PCT を返す={'枝型-TP_PCT' in [x['番号'] for x in rd.rows()]}"
        print(f"素通り | {label}{extra}")
    except SystemExit as e:
        print(f"止まる | {label} | {str(e)[:150]}")


must_stop("オフの判定: 文字の「オフ」", lambda d: row(d, "枝型-TP_PCT").__setitem__("オン/オフと注意", "オフ"))
must_stop("オフの判定: 打ち間違い「おふ」", lambda d: row(d, "枝型-TP_PCT").__setitem__("オン/オフと注意", {"状態": "おふ"}))


def num(d, name):
    return next(n for n in d["法則の中の数"] if n["名前"] == name)


must_stop("範囲に文字", lambda d: num(d, "int_range").__setitem__("範囲", {"kind": "int", "lo": "a", "hi": 24}))
must_stop("lo と hi の逆", lambda d: num(d, "int_range").__setitem__("範囲", {"kind": "int", "lo": 24, "hi": 3}))
must_stop("範囲の外の代表の値", lambda d: num(d, "int_range").__setitem__("代表の値", {"スキャル": 99}))
must_stop("数の名前の重なり", lambda d: d["法則の中の数"].append(copy.deepcopy(num(d, "int_range"))))
must_stop("単位 ドル", lambda d: num(d, "int_range").__setitem__("単位", "ドル"))
must_stop("単位 値段", lambda d: num(d, "int_range").__setitem__("単位", "値段"))


def cond0(d):
    return row(d, "枝S1-MTFCUT")["動く条件"]["全部満たす"][1]


must_stop("部品の名前 が無い名前", lambda d: cond0(d)["指す物"].__setitem__("部品の名前", "無い部品"))
must_stop("指す物に 値の読み方", lambda d: cond0(d)["指す物"].__setitem__("値の読み方", "何か"))
must_stop("指す物の 時間足 が選べない", lambda d: cond0(d)["指す物"].__setitem__("時間足", "7m"))
must_stop("指す物の 場面 が選べない", lambda d: cond0(d)["指す物"].__setitem__("場面", "無い場面"))
must_stop("側 が選べない", lambda d: row(d, "枝S1-MTFCUT")["動く条件"]["全部満たす"][0].__setitem__("側", "斜め"))

print("=== 枝S1-TCTP の幅の出どころ（Q11 の2つ目）: 値の在る行 :89 と出どころの :88")
print("  ", next(n for n in r.data["法則の中の数"] if n["名前"] == "S1_TCTP_幅"))
s1 = json.loads((cop.SCRIPTS / "recipes" / "identity_s1_legacy.json").read_text(encoding="utf-8"))
tctp = next(e for e in s1["exits"] if e["name"] == "TCTP")
print("   float として同じか V59DOWN", 0.0015588160549621896 == 0.0015588160549621895, "V59FLAT", 0.0015024814839103248 == 0.0015024814839103247)
print("   TCTP の k", tctp["exec"]["placement"]["level"]["k"])
print("素通りの件数:", [l for l, s in results if not s])

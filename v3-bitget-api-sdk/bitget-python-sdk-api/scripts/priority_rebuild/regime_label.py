#!/usr/bin/env python3
"""regime_label.py — 答え合わせに使う正解ラベル（札）を作る、ただ1つの場所（M2-F-6d・2026-09-29）。

なぜ在るか（まこさん 2026-09-28・逐語は m2_todo.json の M2-F-6d の注意）
  札が正しいかは、最後は M2-L の net で分かる。外れていたら札を直して段1から並べ直す。
  そのときに直しやすく・どの札で選んだかをたどれるように、札を作る場所を1つにし、数字は設定ファイルに置き、
  札の式そのものを版として持つ。

何をするか
  ・設定ファイル recipes/regime_label.json を読む（数字はコードに1つも書かない）。
  ・版1「er_median」＝いままでの札（observe_diag._regime_labels の式をそのまま移した）。
      そのバーから先 n本の値動きを3つの見方で真偽にする（強さ・向き・大きさ・中央値で切る）。n＝設定の「先を見る本数」。
  ・版2「band_hold」＝1411行目の定義（役割ごと・帯・幅・続く）。
      帯＝そのバーの前（保有の上限 × 倍率 本）の山と谷。山＝前後 m 本で最も高いバー（谷は最も低い）。
      上の線＝近い山（「まとめる幅」以内）を1つにまとめ、c 個以上の群のうち終値に いちばん近い上の群（_line）。下の線は谷で同じ。
      幅＝(上の線 − 下の線) ÷ 終値 が「幅の線」以上。続く＝次のバーから「続く本数」本の終値が全部 帯の中。
      そのバーの終値が帯の中 ∧ 幅 ∧ 続く ＝「レンジだった」。「強さ」の真偽＝レンジだった の否定（使える行だけ）。
      「向き」「大きさ」は版1 と同じ式（先の本数＝続く本数）＝上げ・下げ・スパイクの札は M2-M-1 で決める。
      まとめる幅と幅の線は「手数料の床（e38_logic_parts.SCALP_FLOOR）の何倍か」で書く（構造の文＝手数料の床は既存の定数を読む）。
  ・採点に使う版は設定ファイルの「採点に使う版」の1行（既定＝er_median＝いままでと同じ）。

呼ぶ側
  observe_diag._regime_labels・_regime_horizons（中身はここを呼ぶだけ）／regime_r9_diag._labels_for／
  scripts/dashboard/build_regime_label_dashboard.py（⑪タブの版）。
  ★呼ぶ側を切り替えるのは工事 B（観察の道具・測る道具）と工事 C（⑪タブ）。呼ぶ側の確かめ（自己検査 T6）は工事 B で足す。

★札は先を見るのが仕事（評価にだけ使う・判定の条件や入口には入れない）＝未来参照の行には H2OK を付ける。
★乱数は使わない（恒久67番）。
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
CONFIG = HERE / "recipes" / "regime_label.json"
LABEL_NAMES = ("強さ", "向き", "大きさ")
BAND_KEYS = ("倍率", "m", "c", "まとめる幅", "幅の線", "続く本数")
# 版の名前に入れる略（版の名前は⑪タブのファイル名になるので英字だけにする・日本語の名前と値は⑪タブの仕様に出す）
TAG_KEYS = {"倍率": "x", "m": "m", "c": "c", "まとめる幅": "mw", "幅の線": "wl", "続く本数": "h"}


class LabelError(SystemExit):
    """札の設定が読めない・足りない（fail-closed）。"""


# ══ 設定 ═══════════════════════════════════════════════════════════════════════════
def load_config(path=None) -> dict:
    """設定ファイルを読む。無い・採点に使う版が無い・版2 の使う値が無い → 止まる。"""
    p = pathlib.Path(path) if path else CONFIG
    if not p.exists():
        raise LabelError(f"[札] 設定ファイルが無い: {p}（fail-closed）")
    d = json.loads(p.read_text(encoding="utf-8"))
    vers = d.get("版") or {}
    use = d.get("採点に使う版")
    if use not in vers:
        raise LabelError(f"[札] 採点に使う版 {use} が設定の「版」に無い（在る版＝{sorted(vers)}・fail-closed）")
    if use == "band_hold":
        for role, rc in (vers["band_hold"].get("役割") or {}).items():
            if not rc.get("使う値"):
                raise LabelError(f"[札] 採点に使う版が band_hold なのに、役割 {role} の「使う値」が空（⑪タブで まこさんが選ぶ・fail-closed）")
    return d


def fee_floor() -> float:
    """手数料の床＝既存の定数を読む（構造の文・e38_logic_parts.py:23）。"""
    import e38_logic_parts as lp
    return float(lp.SCALP_FLOOR)


def horizons(cfg=None) -> tuple:
    """版1 の先を見る本数。"""
    cfg = cfg or load_config()
    return tuple(int(x) for x in cfg["版"]["er_median"]["先を見る本数"])


def roles(cfg=None) -> list:
    cfg = cfg or load_config()
    return list((cfg["版"].get("band_hold") or {}).get("役割") or {})


def role_bars(cfg, role: str, values: dict | None = None) -> int:
    """その役割の札が先を見る本数＝保有の上限 × 続く本数（成績表の鍵に使う）。"""
    rc = cfg["版"]["band_hold"]["役割"][role]
    v = values or rc["使う値"]
    return int(round(int(rc["保有の上限"]) * float(v["続く本数"])))


# ══ 版1＝いままでの札（observe_diag._regime_labels の式をそのまま移した）══════════════════════
def er_median(win: pd.DataFrame, n: int) -> dict:
    """そのバーから先 n本の値動きの性質を、3つの見方で真偽に直す（＝正解の印）。

    ①強さ   … 先 n本の ER（まっすぐ進んだ距離 ÷ 実際に歩いた距離）が、この窓の中央値以上か
    ②向き   … 先 n本の終値が、いまの終値より上か
    ③大きさ … 先 n本で動いた幅 ÷ 直前 n本で動いた幅 が、この窓の中央値以上か
    戻り＝{名前: (真偽の並び, その行が使えるか)}。先が足りない末尾は「使えない」になる。
    ★どれも比か上下だけ＝ドルの絶対値を1つも使わない（H6）。
    """
    c = win["close"].astype(float)
    fwd = c.shift(-n) - c  # H2OK: 正解の印（ラベル）を作る側＝本番の判断には入らない。build_labels_pct の Triple Barrier と同じ作り。値決め窓に閉じ、窓の外へはみ出す分は欠損になって落ちる
    walk = c.diff().abs().rolling(n).sum().shift(-n)  # H2OK: 同上（ラベル側の未来参照）。材料の列は build_features が当該バーまでの確定値だけで作る＝判断に未来は入らない
    er = (fwd.abs() / walk).where(walk > 0)
    past = (c - c.shift(n)).abs()                             # 直前 n本で動いた幅（未来を見ない）
    size = (fwd.abs() / past).where(past > 0)
    return {"強さ": (er >= er.median(), er.notna()),
            "向き": (fwd > 0, fwd.notna()),
            "大きさ": (size >= size.median(), size.notna())}


# ══ 版2＝帯・幅・続く（1411行目の定義）════════════════════════════════════════════════════
def _line(vals, merge_w: float, c_min: int, x: float, above: bool):
    """近い山（谷）を1つにまとめ、c 個以上の群を線にする。終値 x に いちばん近い上（下）の線を返す。無ければ None。

    定義の文（.claude/state/label_structure_definition_verbatim_20260929.txt）＝「帯は、近い山を1つにまとめ、
    c 個以上なら上の線、谷で下の線を作ります」。
    ★文に無いので CC が決めたこと（2026-09-29・依頼書の自己申告）＝①まとめ方＝高い山から順に並べ、
      群の先頭の山から「まとめる幅」以内の山を同じ群に入れる（谷は低い方から）②線の値＝群の先頭の山（谷）
      ③線が2本以上あるとき＝終値に いちばん近い上の線と下の線を使う。
    """
    v = np.sort(np.asarray(vals, float))
    if above:
        v = v[::-1]
    best = None
    i = 0
    while i < len(v):
        j = i + 1
        while j < len(v) and abs(v[j] - v[i]) <= v[i] * merge_w:
            j += 1
        if j - i >= c_min:
            line = float(v[i])
            if (above and line >= x) or ((not above) and line <= x):
                best = line                                   # 先頭から遠い順に見るので、最後に残るのが いちばん近い線
        i = j
    return best


def band_range(win: pd.DataFrame, hi_bars: int, values: dict, floor: float) -> tuple:
    """「レンジだった」の真偽と、使えるか。戻り＝(pd.Series[bool], pd.Series[bool])。"""
    a = float(values["倍率"])
    m = int(values["m"])
    c_min = int(values["c"])
    merge_w = floor * float(values["まとめる幅"])
    width_line = floor * float(values["幅の線"])
    hold_n = int(round(hi_bars * float(values["続く本数"])))
    look = int(round(hi_bars * a))
    h = win["high"].astype(float)
    lo = win["low"].astype(float)
    cl = win["close"].astype(float).to_numpy()
    n_all = len(cl)
    is_pk = (h == h.rolling(2 * m + 1, center=True).max()).to_numpy()   # H2OK: 札を作る側＝山は前後 m 本で決める（評価にだけ使う・判断に入らない）
    is_tr = (lo == lo.rolling(2 * m + 1, center=True).min()).to_numpy()  # H2OK: 同上（谷）
    pk_idx = np.flatnonzero(is_pk)
    tr_idx = np.flatnonzero(is_tr)
    hv = h.to_numpy()
    lv = lo.to_numpy()
    cs = pd.Series(cl)
    fmax = cs.rolling(hold_n).max().shift(-hold_n).to_numpy()  # H2OK: 札を作る側＝続くを見る（次のバーから hold_n 本の終値の最大）
    fmin = cs.rolling(hold_n).min().shift(-hold_n).to_numpy()  # H2OK: 同上（最小）
    rng = np.zeros(n_all, bool)
    ok = np.zeros(n_all, bool)
    for t in range(look, n_all - hold_n):
        ok[t] = True
        p0, p1 = np.searchsorted(pk_idx, t - look), np.searchsorted(pk_idx, t)   # 山は t より前（t を含まない）
        q0, q1 = np.searchsorted(tr_idx, t - look), np.searchsorted(tr_idx, t)
        if p1 - p0 < c_min or q1 - q0 < c_min:
            continue
        x = cl[t]
        top = _line(hv[pk_idx[p0:p1]], merge_w, c_min, x, True)    # 上の線＝近い山を1つにまとめ、c 個以上の群
        bot = _line(lv[tr_idx[q0:q1]], merge_w, c_min, x, False)   # 下の線＝谷で同じ
        if top is None or bot is None:
            continue
        if not (bot <= x <= top) or (top - bot) / x < width_line:
            continue
        if fmax[t] <= top and fmin[t] >= bot:
            rng[t] = True
    return pd.Series(rng, index=win.index), pd.Series(ok, index=win.index)


def band_hold(win: pd.DataFrame, cfg: dict, role: str, values: dict | None = None) -> dict:
    """版2 の札（3つの見方の形で返す＝呼ぶ側を変えない）。"""
    rc = cfg["版"]["band_hold"]["役割"][role]
    v = values or rc["使う値"]
    rng, ok = band_range(win, int(rc["保有の上限"]), v, fee_floor())
    er = er_median(win, role_bars(cfg, role, v))
    return {"強さ": (ok & ~rng, ok), "向き": er["向き"], "大きさ": er["大きさ"]}


# ══ 呼ぶ側の口 ═══════════════════════════════════════════════════════════════════════
def keys(cfg=None) -> list:
    """採点に使う版の札の鍵＝版1 は先を見る本数（24・288）／版2 は役割（scalp・daytrade）。"""
    cfg = cfg or load_config()
    return list(horizons(cfg)) if cfg["採点に使う版"] == "er_median" else roles(cfg)


def key_bars(key, cfg=None) -> int:
    """鍵を、先を見る本数に直す（成績表の鍵・間引きの間隔に使う）。"""
    cfg = cfg or load_config()
    return int(key) if cfg["採点に使う版"] == "er_median" else role_bars(cfg, str(key))


def key_label(key, cfg=None) -> str:
    """鍵を、行の名前に入れる文字にする（版1＝「先24本」＝いままでと同じ／版2＝役割の名前）。"""
    cfg = cfg or load_config()
    return f"先{int(key)}本" if cfg["採点に使う版"] == "er_median" else str(key)


def groups(cfg=None):
    """役割ごとに並べるときの組（版1＝None＝いままでどおり／版2＝役割の名前の並び）。"""
    cfg = cfg or load_config()
    return None if cfg["採点に使う版"] == "er_median" else [key_label(k, cfg) for k in keys(cfg)]


def labels_for_key(win: pd.DataFrame, key, cfg=None) -> dict:
    cfg = cfg or load_config()
    if cfg["採点に使う版"] == "er_median":
        return er_median(win, int(key))
    return band_hold(win, cfg, str(key))


def labels_at_bars(win: pd.DataFrame, n: int, cfg=None) -> dict:
    """先を見る本数 n の札（observe_diag._regime_labels が呼ぶ）。n が版2 の役割の本数に当たればその役割の札、
    当たらなければ版1 の式（自己検査が小さな n で呼ぶ所を壊さない）。"""
    cfg = cfg or load_config()
    if cfg["採点に使う版"] == "band_hold":
        for role in roles(cfg):
            if role_bars(cfg, role) == int(n):
                return band_hold(win, cfg, role)
    return er_median(win, int(n))


def bars_keys(cfg=None) -> tuple:
    """採点に使う版の、先を見る本数の並び（observe_diag._regime_horizons が返す物）。"""
    cfg = cfg or load_config()
    return tuple(sorted(key_bars(k, cfg) for k in keys(cfg)))


def version_tag(cfg=None, version=None, role=None, values=None) -> str:
    """札の版の名前＝版＋役割＋値（⑪タブの版の名前・順位表・成績表に書く）。"""
    cfg = cfg or load_config()
    ver = version or cfg["採点に使う版"]
    if ver == "er_median":
        return "label-er" + "-".join(str(x) for x in horizons(cfg)) if role is None else f"label-er{int(role)}"
    rs = [role] if role else roles(cfg)
    parts = []
    for r in rs:
        v = values or cfg["版"]["band_hold"]["役割"][r].get("使う値") or {}
        parts.append(f"{r}-" + "-".join(f"{TAG_KEYS[k]}{v.get(k)}" for k in BAND_KEYS))
    return "label-band-" + "_".join(parts)


def spec(cfg=None) -> dict:
    """設定ファイルの中身そのまま（⑪タブの仕様に出す＝手で書き写さない）。"""
    return json.loads(json.dumps(cfg or load_config()))


def variants(cfg, role: str) -> list:
    """⑪タブに出す値の組＝範囲の両端と真ん中を1つずつ動かす（ほかの値は真ん中）。乱数なし。"""
    rng = cfg["版"]["band_hold"]["役割"][role]["範囲"]

    def mid(k):
        lo, hi = rng[k]["lo"], rng[k]["hi"]
        return (lo + hi) // 2 if isinstance(lo, int) and isinstance(hi, int) else (lo + hi) / 2.0

    base = {k: mid(k) for k in BAND_KEYS}
    out = [dict(base)]
    for k in BAND_KEYS:
        for end in (rng[k]["lo"], rng[k]["hi"]):
            v = dict(base)
            v[k] = end
            if v not in out:
                out.append(v)
    return out


# ══ 自己検査（答えの分かるデータ・乱数なし）═══════════════════════════════════════════════
def _synth(kind: str, n: int = 1200) -> pd.DataFrame:
    """答えの分かる値動き。range＝100〜101 を8本ごとに往復／trend＝1本ごとに +0.1 で上がる／
    range80＝前の8割が range・後ろ2割が trend。"""
    if kind == "range":
        cyc = np.array([100.0, 100.25, 100.5, 100.75, 101.0, 100.75, 100.5, 100.25])
        c = np.tile(cyc, n // len(cyc) + 1)[:n]
    elif kind == "trend":
        c = 100.0 + 0.1 * np.arange(n)
    else:
        k = int(n * 0.8)
        a = _synth("range", k)["close"].to_numpy()
        c = np.concatenate([a, a[-1] + 0.1 * np.arange(1, n - k + 1)])
    idx = pd.date_range("2024-06-01", periods=n, freq="5min")
    return pd.DataFrame({"high": c, "low": c, "close": c}, index=idx)


def selftest() -> int:
    ng = []
    cfg = load_config()
    fl = fee_floor()
    vals = {"倍率": 5, "m": 3, "c": 2, "まとめる幅": 1.0, "幅の線": 1.0, "続く本数": 1.0}
    # T1 全部レンジ＝使える行はほぼ全部「レンジだった」
    r, ok = band_range(_synth("range"), 12, vals, fl)
    share = float(r[ok].mean()) if ok.any() else float("nan")
    if not share >= 0.95:
        ng.append(f"T1: 全部レンジのデータで、レンジだった の割合が {share:.3f}（0.95 以上のはず）")
    # T2 全部トレンド＝1本も「レンジだった」にならない
    r2, ok2 = band_range(_synth("trend"), 12, vals, fl)
    if bool(r2[ok2].any()):
        ng.append(f"T2: 全部トレンドのデータで、レンジだった が {int(r2[ok2].sum())} 本 出た（0本のはず）")
    # T3 レンジが8割＝版2 は8割近く、版1 は中央値で切るので約半分（版1 の弱点を見える形で残す）
    d3 = _synth("range80")
    r3, ok3 = band_range(d3, 12, vals, fl)
    s3 = float(r3[ok3].mean())
    e3m, e3u = er_median(d3, 12)["強さ"]
    e3 = float((~e3m[e3u]).mean())
    if not (s3 >= 0.7 and e3 <= 0.6):
        ng.append(f"T3: レンジが8割のデータで、版2 {s3:.3f}（0.7 以上のはず）・版1 {e3:.3f}（中央値で切るので 0.6 以下のはず）")
    # T4 幅の線を帯の幅（1%）より高くすると、1本も「レンジだった」にならない
    v4 = dict(vals)
    v4["幅の線"] = 0.02 / fl
    r4, ok4 = band_range(_synth("range"), 12, v4, fl)
    if bool(r4[ok4].any()):
        ng.append("T4: 幅の線を帯より広くしても、レンジだった が出た")
    # T5 版1 は前の式と同じ（observe_diag のニセのデータの N1 と同じ見本で、強さが区間の答えと一致）
    import observe_diag as od
    sdf, strend = od._synth_regime_bars()
    em, eu = er_median(sdf, 24)["強さ"]
    same = (strend.shift(-24) == strend) & (strend.shift(-1) == strend)  # H2OK: ニセのデータの中だけで完結する検査
    use = eu & same.fillna(False)
    if int(use.sum()) < 10 or float((em[use] == strend[use]).mean()) < 1.0:
        ng.append("T5: 版1 の強さが、答えの分かるニセのデータの区間と一致しない")
    # T7 採点に使う版が band_hold なのに使う値が空なら止まる
    import tempfile
    bad = json.loads(json.dumps(cfg))
    bad["採点に使う版"] = "band_hold"
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "x.json"
        p.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
        try:
            load_config(p)
            ng.append("T7: 使う値が空の band_hold を採点に使う版にしても止まらない")
        except SystemExit:
            pass
    # T8 版の名前に値が入る・役割の保有の範囲が組む側の設定と同じ（2か所に書いた値の食い違いを見る）
    tag = version_tag(cfg, "band_hold", "scalp", vals)
    if not all(f"{TAG_KEYS[k]}{vals[k]}" in tag for k in BAND_KEYS) or "scalp" not in tag or not tag.isascii():
        ng.append(f"T8: 版の名前に役割と値が入っていない（か英字でない）: {tag}")
    sl = json.loads((HERE / "recipes" / "search_limits.json").read_text(encoding="utf-8"))["hold_range_by_role"]
    for role in roles(cfg):
        rc = cfg["版"]["band_hold"]["役割"][role]
        if role not in sl or (int(rc["保有の下限"]), int(rc["保有の上限"])) != (int(sl[role]["lo_bars"]), int(sl[role]["hi_bars"])):
            ng.append(f"T8: 役割 {role} の保有の範囲が search_limits.json の hold_range_by_role と違う")
    # T9 ⑪タブの値の組＝真ん中1つ＋両端（重なりは除く）・乱数なし（2回 呼んで同じ）
    for role in roles(cfg):
        v1, v2 = variants(cfg, role), variants(cfg, role)
        if v1 != v2 or not v1:
            ng.append(f"T9: {role} の値の組が決まった並びでない")
    # T10 続くの確かめ＝レンジが終わる直前のバー（次の保有の上限の本数のうちに帯を抜ける）は「レンジだった」にならない
    k3 = int(len(d3) * 0.8)
    if not bool(ok3.iloc[k3 - 1]):
        ng.append("T10: レンジが終わる直前のバーが、使える行に入っていない（検査が空振りする）")
    elif bool(r3.iloc[k3 - 1]):
        ng.append("T10: レンジが終わる直前のバー（次の12本で帯を抜ける）が レンジだった になった")
    # T11 近い山を1つにまとめ、c 個以上の群を線にする＝いちばん高い山が1つだけでも、下の群（3個）が上の線になる
    if _line(np.array([103.0, 101.0, 101.01, 101.02]), 0.0008, 2, 100.5, True) != 101.02:
        ng.append("T11: いちばん高い山の群が c 個に足りないとき、下の群（c 個以上）が上の線にならない")
    if _line(np.array([97.0, 99.0, 98.99, 98.98]), 0.0008, 2, 99.5, False) != 98.98:
        ng.append("T11: いちばん低い谷の群が c 個に足りないとき、上の群（c 個以上）が下の線にならない")
    if _line(np.array([101.0, 101.01]), 0.0008, 3, 100.5, True) is not None:
        ng.append("T11: c 個に足りない群だけなのに、線ができた")
    print("[regime_label selftest] T1 全部レンジ ／ T2 全部トレンド ／ T3 レンジ8割（版1 の弱点）／ T4 幅の線 ／ "
          "T5 版1 は前の式と同じ ／ T7 使う値が空なら止まる ／ T8 版の名前・保有の範囲 ／ T9 値の組 ／ T10 続くの確かめ ／ T11 近い山のまとめ方")
    print(f"  参考＝T1 {share:.3f} ／ T3 版2 {s3:.3f}・版1 {e3:.3f}")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print(json.dumps({"採点に使う版": load_config()["採点に使う版"], "版の名前": version_tag()}, ensure_ascii=False))

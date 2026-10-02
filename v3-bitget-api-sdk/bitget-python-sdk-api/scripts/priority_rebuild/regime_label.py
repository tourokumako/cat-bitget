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
  ・版3「hindsight_box」＝後から全部 見て作る札（M2-F-6c・まこさん「OK」2026-10-02＝⑪タブの label-c24b-scalp・label-c24b-daytrade）。
      役割ごと（スキャル＝5分足・箱24本／デイトレ＝15分足・箱40本）。①水平な箱に入ったバーをレンジ ②大きくて速い脚を外す
      ③段と段の間の移る所を外す ④箱の中で上下に2回ずつ行き来している所は、②の脚の中でもレンジに戻す。
      式は CC の調べの道具（.claude/state/_labelC5・C14・C20・C24・C25・_labelD_rule・_labelD_c24b_probe.py）から、式を変えずに移した。
      「強さ」の真偽＝レンジだった の否定（全部の行が使える）。「向き」「大きさ」は版1 と同じ式（先の本数＝その役割の保有の上限）。
  ・採点に使う版は設定ファイルの「採点に使う版」の1行（2026-10-02 から hindsight_box＝版3）。

呼ぶ側
  observe_diag._regime_labels・_regime_horizons（中身はここを呼ぶだけ）／regime_r9_diag._labels_for／
  scripts/dashboard/build_regime_label_dashboard.py（⑪タブの版）。
  ★呼ぶ側の切り替え＝観察の道具と測る道具は、工事 B（2026-10-02）で部品を呼ぶ形にした
    （自己検査 T6 が、呼ぶ側が部品を呼び、札の式を書き写していないかを見る）。⑪タブの道具は工事 C。

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
HINDSIGHT = "hindsight_box"                       # 版3＝後から全部 見て作る札（役割ごと）
FORMULA_VERSIONS = ("er_median", "band_hold", HINDSIGHT)   # 式が在る版
BASE_TF = "5min"                                  # 読む足（5分足）＝版3 の数える足がこれと違えば、まとめて数える


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
    if use not in FORMULA_VERSIONS:
        raise LabelError(f"[札] 採点に使う版 {use} の式が regime_label.py に無い（式が在る版＝{'・'.join(FORMULA_VERSIONS)}・fail-closed）")
    if use == HINDSIGHT:
        for k in ("値動きの大きさ", "箱", "脚", "移る所", "行き来", "役割"):
            if not (vers[HINDSIGHT] or {}).get(k):
                raise LabelError(f"[札] 版 {HINDSIGHT} に「{k}」が無い（fail-closed）")
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

    定義の文＝まこさんの原文（m2_todo.json の M2-F-6d の注意の「帯の上と下」の文）＝「上の線は、高さの差が手数料の床…
    以内にある山を1つにまとめた所です。下の線は谷で同じことをします。まとめた山が2つ以上あれば上の線が在るとし、谷も同じです。
    …これが法則 R1 の跳ね返しの帯です。」。終値 x の上と下に線を取るのは、法則 R1（regime_detection_kb.md の R1）の
    「その線が close の上下に揃っていたらレンジ」に従う。label_structure_definition_verbatim_20260929.txt は CC の要約（原文ではない）。
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
    if not v:
        raise LabelError(f"[札] 役割 {role} の「使う値」が空なので、版2 の札を作れない（⑪タブで まこさんが選ぶ・fail-closed）")
    rng, ok = band_range(win, int(rc["保有の上限"]), v, fee_floor())
    er = er_median(win, role_bars(cfg, role, v))
    return {"強さ": (ok & ~rng, ok), "向き": er["向き"], "大きさ": er["大きさ"]}


# ══ 版3＝後から全部 見て作る札（M2-F-6c で まこさんが決めた label-c24b-scalp・label-c24b-daytrade）══════════════
#   まこさん決定（2026-10-02）＝⑪タブの2本を見て「OK」。前の版 label-trial-c24（「確認したけど、視覚的にはほぼOKに見えるので、
#   これでいいよ」）を土台に、9/28 の構造の文「役割ごとに、保有時間の下限と上限、倍率、m、c を持たせます」に合わせて役割ごとにした。
#   式は CC の調べの道具から、式を変えずに移した（工事 D の案を作る道具が、⑪タブの2本と1本ずつ同じかを数えた）。
#   数字は全部 設定ファイルの版 hindsight_box に置く（構造の文＝「数字は全部、設定ファイルに置きます。コードには1つも書きません。」）。
#   ★先を見るのが仕事（答え合わせにだけ使う・判定の条件や入口には入れない）＝先を見る行には H2OK を付ける。乱数は使わない。
def local_scale(win: pd.DataFrame, sc: dict) -> np.ndarray:
    """その時期の値動きの大きさ s＝（n本の最高値 − 最安値）÷ 終値 の、前後 m本の中央値（窓の端は近い値で埋める）。"""
    n = int(sc["幅を測る本数"])
    w = (win["high"].rolling(n).max() - win["low"].rolling(n).min()) / win["close"]
    s = w.rolling(int(sc["中央値を取る本数"]), center=True, min_periods=int(sc["最小の本数"])).median()  # H2OK: 札を作る側＝前後を見て s を決める（評価にだけ使う・判断に入らない）
    return s.bfill().ffill().to_numpy(float)  # H2OK: 同上（窓の頭の欠けを後ろの値で埋める）


def zigzag_adaptive(h: np.ndarray, lo: np.ndarray, theta: np.ndarray) -> list:
    """戻りがその時の theta[i]（割合）以上で向きが変わるジグザグ。戻り＝[(位置, 値, +1 山 / -1 谷)]。"""
    piv = []
    trend = 0
    hi_i, hi_v, lo_i, lo_v = 0, h[0], 0, lo[0]
    for i in range(1, len(h)):
        if h[i] > hi_v:
            hi_i, hi_v = i, h[i]
        if lo[i] < lo_v:
            lo_i, lo_v = i, lo[i]
        th = theta[i]
        if trend >= 0 and lo[i] <= hi_v * (1 - th) and (trend == 1 or hi_i < i):
            if trend == 0 and lo_i < hi_i:
                piv.append((lo_i, lo_v, -1))
            piv.append((hi_i, hi_v, 1))
            trend = -1
            lo_i, lo_v = i, lo[i]
        elif trend <= 0 and h[i] >= lo_v * (1 + th) and (trend == -1 or lo_i < i):
            if trend == 0 and hi_i < lo_i:
                piv.append((hi_i, hi_v, 1))
            piv.append((lo_i, lo_v, -1))
            trend = 1
            hi_i, hi_v = i, h[i]
    piv.append((hi_i, hi_v, 1) if trend == 1 else (lo_i, lo_v, -1))
    return piv


def legs_of(win: pd.DataFrame, s: np.ndarray, a: float, per: int) -> list:
    """ジグザグ（戻り a×s）の脚。戻り＝[(始まり, 終わり, 始値, 終値, 大きさ÷s, 速さ＝大きさ÷（本数÷per）)]。"""
    h = win["high"].to_numpy(float)
    lo = win["low"].to_numpy(float)
    piv = zigzag_adaptive(h, lo, a * s)
    out = []
    for (i0, v0, _), (i1, v1, _) in zip(piv[:-1], piv[1:]):
        if i1 <= i0:
            continue
        amp = abs(v1 - v0) / v0 / s[i0]
        out.append((i0, i1, v0, v1, amp, amp / ((i1 - i0) / float(per))))
    return out


def trend_mask(c: np.ndarray, legs: list, a0: float, v0_: float, f: float) -> np.ndarray:
    """大きさ ≥ a0 かつ 速さ ≥ v0_ の脚を、終値が脚の f〜(1−f) 進んだ所だけ真にする（脚の両端の止まった所は除く）。"""
    m = np.zeros(len(c), bool)
    for i0, i1, v0, v1, amp, spd in legs:
        if amp < a0 or spd < v0_:
            continue
        d = 1.0 if v1 > v0 else -1.0
        p = (c[i0: i1 + 1] - v0) * d / abs(v1 - v0)
        st = np.flatnonzero(p >= f)
        en = np.flatnonzero(p >= 1 - f)
        if len(st) == 0 or len(en) == 0:
            continue
        a_, b_ = i0 + st[0], i0 + en[0]
        if b_ >= a_:
            m[a_: b_ + 1] = True
    return m


def box_stats(win: pd.DataFrame, s: np.ndarray, n_box: int):
    """バー i から n_box 本の箱の高さ（÷終値÷s）と、前半と後半の終値の平均の差（÷箱の幅）。"""
    c = win["close"]
    hh = win["high"][::-1].rolling(n_box).max()[::-1]  # H2OK: 札を作る側＝バーから先 n_box 本の最高値（後ろから数える）
    ll = win["low"][::-1].rolling(n_box).min()[::-1]   # H2OK: 同上（最安値）
    width = (hh - ll)
    h = (width / c).to_numpy() / s
    a = n_box // 2
    m1 = c[::-1].rolling(a).mean()[::-1]               # H2OK: 同上（前半の終値の平均）
    m2 = c[::-1].rolling(n_box - a).mean()[::-1].shift(-a)  # H2OK: 同上（後半の終値の平均）
    d = ((m1 - m2).abs() / width).where(width > 0).to_numpy()
    return np.nan_to_num(h, nan=np.inf), np.nan_to_num(d, nan=np.inf)


def step_mask(win: pd.DataFrame, s: np.ndarray, k: int, x: float) -> np.ndarray:
    """前の k本と後の k本の終値の平均の差 ≥ x×s のバーと、その前後 k÷2 本（段と段の間の移る所）。"""
    c = win["close"]
    before = c.rolling(k).mean()
    after = c[::-1].rolling(k).mean()[::-1]            # H2OK: 札を作る側＝後の k本の平均（後ろから数える）
    mv = ((after - before).abs() / c).to_numpy() / s
    hit = np.nan_to_num(mv, nan=0) >= x
    half = max(k // 2, 1)
    return pd.Series(hit.astype(float)).rolling(2 * half + 1, center=True, min_periods=1).max().to_numpy() > 0  # H2OK: 同上（前後へ広げる）


def oscillates(c: np.ndarray, n_box: int, v: dict) -> np.ndarray:
    """長さ n_box の区間（始まり a）ごとに、終値の帯（区間の最高と最安）の上と下の近く（端の近く×高さ）へ、行ったり来たりの順で
    それぞれ回数の下限以上 入り、前半と後半の終値の平均の差 ≤ 高さ×前後の差の上限、高さ÷平均 ≥ 手数料の床 か。"""
    from numpy.lib.stride_tricks import sliding_window_view
    near, need, shift, floor = float(v["端の近く"]), int(v["回数の下限"]), float(v["前後の差の上限"]), fee_floor()
    w = sliding_window_view(c, n_box)                  # 札を作る側＝区間の中（先を見る＝答え合わせにだけ使う）
    mx, mn = w.max(1), w.min(1)
    hgt = mx - mn
    rows = len(mx)
    prev = np.zeros(rows, np.int8)
    n_top = np.zeros(rows, np.int16)
    n_bot = np.zeros(rows, np.int16)
    hi_th, lo_th = mx - near * hgt, mn + near * hgt
    for j in range(n_box):
        cj = c[j:j + rows]
        code = np.where(cj >= hi_th, 1, np.where(cj <= lo_th, -1, 0)).astype(np.int8)
        new = (code != 0) & (code != prev)
        n_top += new & (code == 1)
        n_bot += new & (code == -1)
        prev = np.where(code != 0, code, prev)
    cs = np.concatenate([[0.0], np.cumsum(c)])
    a = np.arange(rows)
    half = n_box // 2
    m1 = (cs[a + half] - cs[a]) / half
    m2 = (cs[a + n_box] - cs[a + half]) / (n_box - half)
    mean = (cs[a + n_box] - cs[a]) / n_box
    return (n_top >= need) & (n_bot >= need) & (np.abs(m1 - m2) <= shift * hgt) & (hgt / mean >= floor) & (hgt > 0)


def _spread(flag, n_box: int) -> np.ndarray:
    """始まりの印を、その区間の n_box 本 全部へ広げる（バー i は、始まりが i−n_box+1〜i のどれかなら真）。"""
    return pd.Series(np.asarray(flag, float)).rolling(n_box, min_periods=1).max().to_numpy() > 0


def _range_on(win: pd.DataFrame, v: dict, n_box: int) -> np.ndarray:
    """1つの足の上で「レンジだった」を作る。①箱 ②脚を外す ③移る所を外す ④行き来している箱は、脚の中でもレンジに戻す。"""
    c = win["close"].to_numpy(float)
    s = local_scale(win, v["値動きの大きさ"])
    lg, bx, st = v["脚"], v["箱"], v["移る所"]
    tm = trend_mask(c, legs_of(win, s, float(lg["戻り"]), int(lg["速さを測る本数"])),
                    float(lg["大きさの下限"]), float(lg["速さの下限"]), float(lg["端を除く割合"]))
    h, d = box_stats(win, s, n_box)
    ok = (h <= float(bx["高さの上限"])) & (d <= float(bx["前後の差の上限"]))
    stp = step_mask(win, s, int(st["前後の本数"]), float(st["差の下限"]))
    lab = _spread(ok, n_box) & ~tm & ~stp
    q = np.zeros(len(c), bool)
    qq = oscillates(c, n_box, v["行き来"])
    q[:len(qq)] = qq
    return lab | (_spread(ok & q, n_box) & ~stp)


def hindsight_range(win: pd.DataFrame, cfg: dict, role: str) -> pd.Series:
    """版3 の「レンジだった」の真偽（役割ごと）。数える足が5分足でなければ、その足にまとめて数え、5分足の各バーへ写す。"""
    v = cfg["版"][HINDSIGHT]
    rc = v["役割"][role]
    tf, n_box = str(rc["数える足"]), int(rc["箱の本数"])
    if pd.to_timedelta(tf) == pd.to_timedelta(BASE_TF):
        return pd.Series(_range_on(win, v, n_box), index=win.index)
    w2 = pd.DataFrame({"high": win["high"].resample(tf, label="left", closed="left").max(),
                       "low": win["low"].resample(tf, label="left", closed="left").min(),
                       "close": win["close"].resample(tf, label="left", closed="left").last()}).dropna()
    m2 = pd.Series(_range_on(w2, v, n_box), index=w2.index)
    return pd.Series(m2.reindex(win.index.floor(tf)).fillna(False).to_numpy(bool), index=win.index)


def hindsight_roles(cfg=None) -> list:
    cfg = cfg or load_config()
    return list(cfg["版"][HINDSIGHT]["役割"])


def hindsight_bars(cfg, role: str) -> int:
    """版3 の役割の先を見る本数＝保有の上限（向き・大きさの札と、成績表の鍵に使う）。"""
    return int(cfg["版"][HINDSIGHT]["役割"][role]["保有の上限"])


def hindsight(win: pd.DataFrame, cfg: dict, role: str) -> dict:
    """版3 の札（3つの見方の形で返す＝呼ぶ側を変えない）。強さ＝レンジだった の否定（全部の行が使える）。"""
    rng = hindsight_range(win, cfg, role)
    er = er_median(win, hindsight_bars(cfg, role))
    return {"強さ": (~rng, pd.Series(True, index=win.index)), "向き": er["向き"], "大きさ": er["大きさ"]}


# ══ 呼ぶ側の口 ═══════════════════════════════════════════════════════════════════════
def keys(cfg=None) -> list:
    """採点に使う版の札の鍵＝版1 は先を見る本数（24・288）／版2・版3 は役割（scalp・daytrade）。"""
    cfg = cfg or load_config()
    if cfg["採点に使う版"] == "er_median":
        return list(horizons(cfg))
    return hindsight_roles(cfg) if cfg["採点に使う版"] == HINDSIGHT else roles(cfg)


def key_bars(key, cfg=None) -> int:
    """鍵を、先を見る本数に直す（成績表の鍵・間引きの間隔に使う）。"""
    cfg = cfg or load_config()
    if cfg["採点に使う版"] == "er_median":
        return int(key)
    return hindsight_bars(cfg, str(key)) if cfg["採点に使う版"] == HINDSIGHT else role_bars(cfg, str(key))


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
    if cfg["採点に使う版"] == HINDSIGHT:
        return hindsight(win, cfg, str(key))
    return band_hold(win, cfg, str(key))


def labels_at_bars(win: pd.DataFrame, n: int, cfg=None) -> dict:
    """先を見る本数 n の札（observe_diag._regime_labels が呼ぶ）。n が版2 の役割の本数に当たればその役割の札、
    当たらなければ版1 の式（自己検査が小さな n で呼ぶ所を壊さない）。"""
    cfg = cfg or load_config()
    if cfg["採点に使う版"] == HINDSIGHT:
        for role in hindsight_roles(cfg):
            if hindsight_bars(cfg, role) == int(n):
                return hindsight(win, cfg, role)
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
    if ver == HINDSIGHT:
        v = cfg["版"][HINDSIGHT]
        rs = [role] if role else hindsight_roles(cfg)
        common = (f"w{v['値動きの大きさ']['幅を測る本数']}-m{v['値動きの大きさ']['中央値を取る本数']}-h{v['箱']['高さの上限']}"
                  f"-g{v['箱']['前後の差の上限']}-r{v['脚']['戻り']}-a{v['脚']['大きさの下限']}-v{v['脚']['速さの下限']}"
                  f"-k{v['移る所']['前後の本数']}-x{v['移る所']['差の下限']}-q{v['行き来']['端の近く']}")
        return "label-hind-" + "_".join(f"{r}-{v['役割'][r]['数える足']}-b{v['役割'][r]['箱の本数']}" for r in rs) + "-" + common
    rs = [role] if role else roles(cfg)
    parts = []
    for r in rs:
        v = values or cfg["版"]["band_hold"]["役割"][r].get("使う値") or {}
        if not v:
            raise LabelError(f"[札] 役割 {r} の「使う値」が空なので、版2 の版の名前を作れない（⑪タブで まこさんが選ぶ・fail-closed）")
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
    # T6 呼ぶ側が、ここを呼んでいる（作る場所が1つ＝式を書き写していない）
    import ast
    for fn, path in (("_regime_labels", HERE / "observe_diag.py"), ("_regime_horizons", HERE / "observe_diag.py"),
                     ("_labels_for", HERE / "regime_r9_diag.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        f = [x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef) and x.name == fn]
        calls = [x for x in ast.walk(f[0]) if isinstance(x, ast.Attribute)
                 and isinstance(x.value, ast.Name) and x.value.id == "rl"] if f else []
        if not calls:
            ng.append(f"T6: {path.name} の {fn} が、札を作る場所（regime_label）を呼んでいない")
        if f and any(isinstance(x, ast.Attribute) and x.attr == "median" for x in ast.walk(f[0])):
            ng.append(f"T6: {path.name} の {fn} に、札の式（median）が書き写されている")
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
    # ══ 版3（hindsight_box・M2-F-6d の工事 D）＝答えの分かる作り物のチャート ══
    if HINDSIGHT not in (cfg.get("版") or {}):
        ng.append(f"T12: 設定ファイルに版 {HINDSIGHT} が無い")
    else:
        hr = hindsight_roles(cfg)
        # T12 全部レンジ＝役割ごとに、ほぼ全部「レンジだった」
        for role in hr:
            s12 = float(hindsight_range(_synth("range"), cfg, role).mean())
            if not s12 >= 0.95:
                ng.append(f"T12: 全部レンジのデータで、{role} の レンジだった の割合が {s12:.3f}（0.95 以上のはず）")
        # T13 全部トレンド＝1本も「レンジだった」にならない
        for role in hr:
            n13 = int(hindsight_range(_synth("trend"), cfg, role).sum())
            if n13:
                ng.append(f"T13: 全部トレンドのデータで、{role} の レンジだった が {n13} 本 出た（0本のはず）")
        # T14 レンジ8割＝前8割はほぼレンジ・後ろ2割（上げ）はほぼレンジでない
        for role in hr:
            r14 = hindsight_range(d3, cfg, role).to_numpy()
            a14, b14 = float(r14[:k3].mean()), float(r14[k3:].mean())
            if not (a14 >= 0.9 and b14 <= 0.05):
                ng.append(f"T14: レンジ8割のデータで、{role} の前8割 {a14:.3f}（0.9 以上のはず）・後ろ2割 {b14:.3f}（0.05 以下のはず）")
        # T15 階段（observe_diag の答えの分かるニセのデータ＝上げの区間と横ばいの区間を交互）
        #   箱の長さが区間より短い役割＝横ばいはレンジ・上げはレンジでない。長い役割＝その長さの帯が無いので全部 レンジでない。
        #   ★前の版 label-trial-c24 は、スキャルの尺で横ばいのうち 0.208 しかレンジと言えなかった（脚が階段の全体を1本と見た）
        sdf15, st15 = od._synth_regime_bars()
        up = st15.to_numpy()
        inner = ((st15.shift(-12) == st15) & (st15.shift(12) == st15)).fillna(False).to_numpy()  # H2OK: ニセのデータの中だけで完結する検査
        blk_min = int(np.argmax(up != up[0])) * 5            # 区間1つの長さ（分）＝本数 × 5分
        for role in hr:
            rc = cfg["版"][HINDSIGHT]["役割"][role]
            box_min = int(rc["箱の本数"]) * pd.to_timedelta(str(rc["数える足"])).total_seconds() / 60
            r15 = hindsight_range(sdf15, cfg, role).to_numpy()
            f15, u15 = float(r15[inner & ~up].mean()), float(r15[inner & up].mean())
            want = (f15 >= 0.9) if box_min <= blk_min else (f15 <= 0.05)
            if not (want and u15 <= 0.05):
                ng.append(f"T15: 階段のデータで、{role}（箱 {box_min:.0f}分・区間 {blk_min}分）の横ばいのうちレンジ {f15:.3f}・上げのうちレンジ {u15:.3f}"
                          f"（{'横ばい 0.9 以上' if box_min <= blk_min else '横ばい 0.05 以下'}・上げ 0.05 以下のはず）")
        # T16 数字は設定ファイルから読む＝箱の高さの上限を 0 にすると、1本も「レンジだった」にならない
        bad16 = json.loads(json.dumps(cfg))
        bad16["版"][HINDSIGHT]["箱"]["高さの上限"] = 0
        for role in hr:
            if bool(hindsight_range(_synth("range"), bad16, role).any()):
                ng.append(f"T16: 箱の高さの上限を 0 にしても、{role} で レンジだった が出た（設定の数字を読んでいない）")
        # T17 役割の保有の範囲が、組む側の設定（search_limits.json の hold_range_by_role）と同じ
        for role in hr:
            rc = cfg["版"][HINDSIGHT]["役割"][role]
            if role not in sl or (int(rc["保有の下限"]), int(rc["保有の上限"])) != (int(sl[role]["lo_bars"]), int(sl[role]["hi_bars"])):
                ng.append(f"T17: 版3 の役割 {role} の保有の範囲が search_limits.json の hold_range_by_role と違う")
    print("[regime_label selftest] T1 全部レンジ ／ T2 全部トレンド ／ T3 レンジ8割（版1 の弱点）／ T4 幅の線 ／ "
          "T5 版1 は前の式と同じ ／ T6 呼ぶ側がここを呼ぶ ／ T7 使う値が空なら止まる ／ T8 版の名前・保有の範囲 ／ T9 値の組 ／ T10 続くの確かめ ／ T11 近い山のまとめ方"
          " ／ T12〜T16 版3 の作り物のチャート（全部レンジ・全部トレンド・レンジ8割・階段・設定の数字）／ T17 版3 の保有の範囲")
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

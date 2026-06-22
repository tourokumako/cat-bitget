#!/usr/bin/env python3
"""e36_short_oscillation.py — E36 SHORT専用柱 ＋ 急騰Exit（SPIKE_SL・Lee-Mykland jump 検定）

位置づけ（acceptance.md・正直に）:
  net 最大化でなく、テールリスク（破滅的大負け）を切る Risk 管理レバー（cat_requirements F5）。
  まこさん指示「8/22 の急騰 TimeExit（青玉・−$101）を回避」。判定は score.py の数字。

★E35（e35_range_oscillation.py・両建て iter9 base・採用済み）は一切触らない（まこさん明示・混乱回避）。
  E36 は e35 から helper/定数/eval_engine を import 流用し、run_continuous「相当」だけを本ファイルにコピーして
  SPIKE_SL を BOX_BREAK_SL 判定の直後に1ブロック足す（spike_lm=None で e35 と完全恒等＝独立ファイル化で挙動不変）。

流用（import・コードを書き直さない・e35 を改造しない）:
  - e35_range_oscillation: _load / _attach_entry_cols / _hold_arrays / _hold_feat_vec / _HOLD_FEATS
                           / _record / _record_lots / _verify_cap / _output_and_report
                           / 定数 TRAIN_END/SC_START/SCORE_END/SEAL_START/UNIT/CAP/HOLD_5M/BE_ARM_BARS/COST_FLOOR/ENTRY_OFFSET/TTL/MAX_ADDS/PRIORITY
  - eval_engine(ee): 確定コスト定数（改造禁止・import のみ）
  - e35_box: 箱の距離%列 sup_col/res_col

急騰検知＝Lee-Mykland (2008) jump 検定（論文精読・正確式・acceptance §2）:
  r_i = log(c_i/c_{i−1})。局所 bipower ボラ（jump 頑健・直近 K 本）:
    V̂_i = (π/(2(K−1))) Σ_{j=i−K+2}^{i} |r_j||r_{j−1}|
  jump 統計 L_i = r_i/√V̂_i。閾値（Gaussian EVT・α から a-priori・データで sweep しない L-267）:
    C_n = √(2lnK) − (lnπ+lnlnK)/(2√(2lnK)) ／ a_n = 1/√(2lnK) ／ β* = −log(−log(1−α)) ／ L* = C_n+β*·a_n
  発火: SHORT 保有中・含み損側（c_i>avg）かつ L_i>L* → 成行カット（exit_reason=SPIKE_SL・fill=c_i・検知バー終値）。
  a-priori 既定: α=0.01（β*≈4.60）／ K=270（≈1日）。ゆっくり深くなる玉は L_i 伸びず不発＝急騰だけ切る（深さ stop でない）。

H 制約（acceptance §5）:
  H1 cap … SPIKE_SL は決済のみ（新規/add/size 変更なし）＝合計≤0.12 不変（_verify_cap 実測 assert）。
  H2 leak … r_i・V̂_i は bars≤i（過去〜現在）のみ。mae（保有終了まで未確定の未来値）は発火に使わない。教師生成は spike OFF。
  H5 約定 … SPIKE_SL=成行 taker+slip（_record_lots が maker群=("TP_FILLED","EDGE_TP","BE_EXIT","PARTIAL_TP")以外を自動 taker 化）。fill=c_i。
  H6 価格非依存 … L_i・L* は log リターン/ボラ＝無次元。USD 絶対値の閾値なし。
  H8 期間 … periods import（手打ちなし・e35 経由）。α・K は a-priori。封印窓不参照。
  H13 judge … score.py に SPIKE_SL を TAKER 登録＋既知答えテスト再pass（②別承認）。本ファイルは judge を触らない。
  H15 ボラ逃げ … 非該当（Entry 方向スコアでなく保有中の損切り）。
  H16 1変更 … 1レバー（SPIKE_SL）。深さ stop（勝ち巻き込み・6方向で否定）でなく jump 統計（急騰のみ）に限定＝別物。
"""
from __future__ import annotations
import argparse
import math
import pathlib
import sys
from datetime import timezone

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import eval_engine as ee                       # noqa: E402  確定コスト定数（改造禁止・import のみ）
import e35_range_oscillation as e35            # noqa: E402  ★流用元（helper/定数を import・e35 は一切触らない）
import e35_box                                 # noqa: E402  箱の距離%列
import periods                                 # noqa: E402  検証期間の唯一の正本（表示用）

# ── 期間（periods.py が唯一の正本・SSOT・手打ち禁止・e35 と同一定義＝require_period_source 準拠）──
TRAIN_END = periods.TRAIN_END              # 学習境界（< TRAIN_END で fit）
SC_START = periods.SCORE_START             # 採点窓 開始（2025-06-01）
SCORE_END = periods.SEAL_START             # 採点スライスの排他終端＝封印開始（entry < SCORE_END）
SEAL_START = periods.SEAL_START            # 封印開始（full 出力は < SEAL_START・封印は不参照）
# ── その他の定数（e35 から流用＝同一値・E36 で別定義しない＝e35 と一致を保証）──────────────
UNIT = e35.UNIT
CAP = e35.CAP
HOLD_5M = e35.HOLD_5M
BE_ARM_BARS = e35.BE_ARM_BARS        # ★mutable（run_e36 が教師生成で OFF=10**9 にする・run_continuous が読む）
COST_FLOOR = e35.COST_FLOOR
ENTRY_OFFSET = e35.ENTRY_OFFSET
TTL = e35.TTL
MAX_ADDS = e35.MAX_ADDS
PRIORITY = e35.PRIORITY

# ── helper（import 流用・e35 の実体をそのまま使う）─────────────────────────────────────
_load = e35._load
_attach_entry_cols = e35._attach_entry_cols
_hold_arrays = e35._hold_arrays
_hold_feat_vec = e35._hold_feat_vec
_HOLD_FEATS = e35._HOLD_FEATS
_record = e35._record
_record_lots = e35._record_lots
_verify_cap = e35._verify_cap
_output_and_report = e35._output_and_report


# ── 急騰検知 Lee-Mykland jump（全 bars≤i の値のみ＝leak-safe・a-priori 閾値・スイープしない）──
def spike_threshold(K: int, alpha: float) -> float:
    """Gaussian EVT 閾値 L* = C_n + β*·a_n（K・α から a-priori・データで決めない・L-267）。"""
    lnK = math.log(K)
    s = math.sqrt(2.0 * lnK)
    Cn = s - (math.log(math.pi) + math.log(lnK)) / (2.0 * s)
    an = 1.0 / s
    beta = -math.log(-math.log(1.0 - alpha))
    return Cn + beta * an


def spike_stat(c: np.ndarray, K: int) -> np.ndarray:
    """各バーの jump 統計 L_i = r_i/√V̂_i（V̂=局所 bipower・直近 K 本・全て過去〜現在＝H2 leak-safe）。
    r_i=log(c_i/c_{i−1})・|r_j||r_{j−1}| を窓 K−1 で和（warmup は NaN→発火しない）。"""
    n = len(c)
    r = np.full(n, np.nan)
    r[1:] = np.log(c[1:] / c[:-1])              # log リターン（過去 close のみ）
    absr = np.abs(r)
    bpv = np.full(n, np.nan)
    bpv[1:] = absr[1:] * absr[:-1]              # bpv[i] = |r_i||r_{i−1}|（jump 頑健の bipower 項）
    bp_sum = pd.Series(bpv).rolling(K - 1).sum().to_numpy()   # Σ_{j=i−K+2}^{i}（K−1 項・当該バーまで）
    V = (math.pi / (2.0 * (K - 1))) * bp_sum
    with np.errstate(invalid="ignore", divide="ignore"):
        return r / np.sqrt(V)


# ── 件数レバー（E36 freq-iter1）: 強レンジ限定で SHORT 反転ゾーンを広げて新規発火を増やす ──
def _widen_short_zone(df, box_tf, z_wide, er_strong_q):
    """強レンジ（ER が学習窓 q(er_strong_q) 未満＝強い平均回帰）のバーだけ、SHORT 反転ゾーンを
    W×e35.ZONE_FRAC(=0.25) → W×z_wide に広げて short_entry を再計算する（zone_short レバー）。
    e35 の入口成分（range_ok / short_rev / up_zone / in_box / W）を流用＝重複実装しない・e35 base は不変。
    全て当該足までの値＝leak-safe（H2）／ er 閾値は学習窓 fit＝採点窓不参照（H8）／ LONG は触らない（SHORT 専用）。
    返り値: (er_strong閾値, strongバー数, 拡大前SHORT発火数, 拡大後SHORT発火数)。"""
    assert z_wide > e35.ZONE_FRAC, f"z_wide({z_wide}) は現行 ZONE_FRAC({e35.ZONE_FRAC}) より大きく（広げる方向のみ）"
    res = df[e35_box.res_col(box_tf)]
    lo, hi, _nW = e35._w_band(df, box_tf, df["ts"] < TRAIN_END)
    sig = e35._build_signals_for_tf(df, box_tf, lo, hi)            # range_ok / short_rev / up_zone / in_box / W
    in_box = sig["in_box"]; W = sig["W"]
    er_strong = float(df["er"][df["ts"] < TRAIN_END].quantile(er_strong_q))   # 学習窓 fit（採点窓不参照・H8）
    strong = (df["er"] < er_strong).fillna(False)                 # 強い平均回帰のバーだけ広げる（弱レンジは 0.25 のまま）
    up_zone_wide = (in_box & (res <= z_wide * W)).fillna(False)
    up_zone_eff = sig["up_zone"].where(~strong, up_zone_wide)      # ~strong=現行up_zone(0.25) / strong=拡大up_zone
    short_entry_wide = sig["range_ok"] & up_zone_eff & sig["short_rev"]
    n_before = int(sig["short_entry"].sum()); n_after = int(short_entry_wide.sum())
    df["short_entry"] = short_entry_wide.to_numpy()
    return er_strong, int(strong.sum()), n_before, n_after


def run_continuous(df, box_tf, max_adds, hold_ctx=None, be_gate=None, partial_tp=None,
                   short_htf=False, short_only=False, spike_lm=None, spike_gate=None):
    """★e35.run_continuous の逐語コピー＋ SPIKE_SL を1ブロック追加（spike_lm=None で e35 と完全恒等）。
    spike_lm=(K, alpha) を渡すと、SHORT 保有中・含み損側で Lee-Mykland jump 統計が L* を超えたら成行カット（SPIKE_SL）。
    他の挙動（pending fill・出口優先順位・部分利確・建値撤退・cap 合算停止）は e35 iter9/shortset1 と1ビットも変えない。"""
    n = len(df)
    ts = df["ts"].to_numpy()
    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    atr = df["atr"].to_numpy(float); adx = df["adx"].to_numpy(float); kk = df["stoch_k"].to_numpy(float)
    sup = df[e35_box.sup_col(box_tf)].to_numpy(float)
    res = df[e35_box.res_col(box_tf)].to_numpy(float)
    long_sig = df["long_entry"].to_numpy(bool); short_sig = df["short_entry"].to_numpy(bool)
    htf_up = df["htf_macd_up"].to_numpy(bool) if (short_htf and "htf_macd_up" in df.columns) else None
    S = c / (1.0 + sup / 100.0)
    R = c * (1.0 + res / 100.0)
    Cc = (S + R) / 2.0
    Wpct = sup + res
    A = _hold_arrays(df, box_tf) if (hold_ctx is not None or be_gate is not None or partial_tp is not None) else None
    _hm, _hf, _hth = hold_ctx if hold_ctx is not None else (None, None, None)
    _bm, _bf, _bth = be_gate if be_gate is not None else (None, None, None)
    _ptup = partial_tp if partial_tp is not None else (None, None, None, None, None, None)
    _pm, _pf, _pgate, _ptp, _pfrac = _ptup[:5]
    _pshrink = _ptup[5] if len(_ptup) > 5 else None
    _pfull = _ptup[6] if len(_ptup) > 6 else None
    _pgb = _ptup[7] if len(_ptup) > 7 else None
    # ── 急騰Exit（Lee-Mykland jump）: 統計と閾値は全 bars≤i＝leak-safe・None で未計算＝e35 恒等 ──
    if spike_lm is not None:
        _spk_K, _spk_alpha = spike_lm
        Lj = spike_stat(c, _spk_K)
        Lstar = spike_threshold(_spk_K, _spk_alpha)
    else:
        Lj = None; Lstar = None

    trades = []
    pos = {"LONG": None, "SHORT": None}
    pend = {"LONG": None, "SHORT": None}
    events = []

    def held_total():
        return (pos["LONG"]["size"] if pos["LONG"] else 0.0) + (pos["SHORT"]["size"] if pos["SHORT"] else 0.0)

    def open_or_add(side, fp, i):
        sdir = 1 if side == "LONG" else -1
        if pos[side] is None:
            if not (np.isfinite(atr[i]) and np.isfinite(Cc[i])):
                return
            if held_total() + UNIT > CAP + 1e-9:
                return
            pos[side] = {"side": side, "avg": fp, "size": UNIT, "add_count": 1, "first_idx": i, "last_fill_idx": i,
                         "atr_entry": atr[i], "adx_entry": adx[i], "k_entry": kk[i], "W_entry": Wpct[i],
                         "max_fav": h[i] if side == "LONG" else l[i], "max_adv": l[i] if side == "LONG" else h[i], "extended": False, "be_armed": False,
                         "partial_done": False,
                         "lots": [(i, fp, UNIT)]}
            events.append((pd.Timestamp(ts[i]), UNIT))
        else:
            if held_total() + UNIT > CAP + 1e-9:
                return
            p = pos[side]; new_sz = p["size"] + UNIT
            p["avg"] = (p["avg"] * p["size"] + fp * UNIT) / new_sz
            p["size"] = new_sz; p["add_count"] += 1; p["last_fill_idx"] = i
            p["lots"].append((i, fp, UNIT))
            events.append((pd.Timestamp(ts[i]), UNIT))

    for i in range(n):
        # ── 1. pending fill ──
        for side in ("LONG", "SHORT"):
            pd_ = pend[side]
            if pd_ is None:
                continue
            el = i - pd_["placed_idx"]
            if el > TTL:
                pend[side] = None
            elif el >= 1 and ((side == "LONG" and l[i] <= pd_["limit"]) or (side == "SHORT" and h[i] >= pd_["limit"])):
                open_or_add(side, pd_["limit"], i)
                pend[side] = None

        # ── 2. MFE/MAE 極値更新（記録用）──
        for side in ("LONG", "SHORT"):
            p = pos[side]
            if p is None:
                continue
            if side == "LONG":
                p["max_fav"] = max(p["max_fav"], h[i])
                p["max_adv"] = min(p["max_adv"], l[i])
            else:
                p["max_fav"] = min(p["max_fav"], l[i])
                p["max_adv"] = max(p["max_adv"], h[i])

        # ── 3. 出口 ──
        for side in ("LONG", "SHORT"):
            p = pos[side]
            if p is None or i <= p["last_fill_idx"]:
                continue
            avg = p["avg"]; sdir = 1 if side == "LONG" else -1
            broke = (side == "LONG" and np.isfinite(S[i]) and c[i] < S[i]) or \
                    (side == "SHORT" and np.isfinite(R[i]) and c[i] > R[i])
            if broke:                                       # 箱ブレイク＝構造的 SL（成行 taker）
                _record(trades, p, c[i], "BOX_BREAK_SL", i, ts)
                events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None
                continue
            # ── ★急騰Exit（SPIKE_SL）: BOX_BREAK_SL 判定の直後・保有中の各バー ──
            #   SHORT 保有・含み損側(c_i>avg)・Lee-Mykland 統計 L_i>L* ＝統計的に異常な上向き急騰 → 成行カット（taker）。
            #   spike_lm=None では Lj/Lstar が None＝この分岐に入らず e35 恒等。LONG には掛けない（E36 SHORT専用・acceptance §2）。
            if Lj is not None and side == "SHORT" and c[i] > avg and np.isfinite(Lj[i]) and Lj[i] > Lstar:
                # 判別器ゲート（spike_gate set 時・iter2）: 急騰でも「中心に戻る=TP できる」と判別された玉は切らない。
                #   _pm（部分利確の hold-ML booster 流用）predict 高=戻る/低=死ぬ。spike_gate 未満(=死ぬ判別)のみカット。
                #   spike_gate=None or _pm/A 無し＝ゲート無し＝現行 spike 恒等（戻る玉も含め急騰なら全部切る）。
                spike_die = True
                if spike_gate is not None and _pm is not None and A is not None:
                    spike_die = _pm.predict(np.asarray(
                        [_hold_feat_vec(A, sdir, avg, p["first_idx"], p["add_count"], i)]))[0] < spike_gate
                if spike_die:
                    _record(trades, p, c[i], "SPIKE_SL", i, ts)
                    events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None
                    continue
            if not p["extended"]:
                n_lots = len(p["lots"])
                if _pm is not None and not p["partial_done"] and np.isfinite(Cc[i]) and \
                        (n_lots >= 2 or (_pfrac is not None and n_lots == 1)):
                    pgate_s = _pgate[side] if isinstance(_pgate, dict) else _pgate
                    ptp_s = _ptp[side] if isinstance(_ptp, dict) else _ptp
                    if _pshrink:
                        r = max((HOLD_5M - (i - p["first_idx"])) / HOLD_5M, 0.0)
                        ktp = ptp_s * r; mk = ee.MAKER_FEE
                        ptp = max(avg * (1.0 + ktp), avg * (1.0 + mk) / (1.0 - mk)) if side == "LONG" \
                            else min(avg * (1.0 - ktp), avg * (1.0 - mk) / (1.0 + mk))
                    else:
                        ptp = avg * (1.0 + ptp_s) if side == "LONG" else avg * (1.0 - ptp_s)
                    hit_ptp = (side == "LONG" and h[i] >= ptp) or (side == "SHORT" and l[i] <= ptp)
                    if hit_ptp:
                        dying = _pm.predict(np.asarray(
                            [_hold_feat_vec(A, sdir, avg, p["first_idx"], p["add_count"], i)]))[0] < pgate_s
                        gave_back = False
                        if _pgb is not None:
                            peak_exc = (p["max_fav"] - avg) * sdir
                            if peak_exc > avg * COST_FLOOR:
                                cur_exc = (c[i] - avg) * sdir
                                gave_back = (peak_exc - cur_exc) / peak_exc >= _pgb
                    if hit_ptp and (dying or gave_back):
                        if _pfull:
                            _record_lots(trades, p, list(p["lots"]), ptp, "PARTIAL_TP", i, ts)
                            events.append((pd.Timestamp(ts[i]), -p["size"]))
                            pos[side] = None
                            continue
                        if n_lots >= 2:
                            lot = p["lots"].pop()
                            _record_lots(trades, p, [lot], ptp, "PARTIAL_TP", i, ts)
                            p["size"] -= UNIT
                            events.append((pd.Timestamp(ts[i]), -UNIT))
                        else:
                            li, lp_, lsz = p["lots"][0]
                            close_sz = UNIT * _pfrac
                            _record_lots(trades, p, [(li, lp_, close_sz)], ptp, "PARTIAL_TP", i, ts)
                            p["lots"][0] = (li, lp_, lsz - close_sz)
                            p["size"] -= close_sz
                            events.append((pd.Timestamp(ts[i]), -close_sz))
                        p["partial_done"] = True
                armed = np.isfinite(Cc[i]) and ((side == "LONG" and Cc[i] >= avg * (1.0 + COST_FLOOR)) or
                                                (side == "SHORT" and Cc[i] <= avg * (1.0 - COST_FLOOR)))
                hit_center = armed and ((side == "LONG" and h[i] >= Cc[i]) or (side == "SHORT" and l[i] <= Cc[i]))
                if hit_center:
                    p["extended"] = True
                    continue
                if _hm is not None and np.isfinite(Cc[i]) and \
                        _hm.predict(np.asarray([_hold_feat_vec(A, sdir, avg, p["first_idx"], p["add_count"], i)]))[0] < _hth:
                    _record(trades, p, c[i], "ML_STANCH", i, ts)
                    events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None
                    continue
                mk = ee.MAKER_FEE
                bp = avg * (1.0 + mk) / (1.0 - mk) if side == "LONG" else avg * (1.0 - mk) / (1.0 + mk)
                if p["be_armed"] and ((side == "LONG" and h[i] >= bp) or (side == "SHORT" and l[i] <= bp)):
                    _record(trades, p, bp, "BE_EXIT", i, ts)
                    events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None
                else:
                    if (i - p["first_idx"]) >= BE_ARM_BARS and not p["be_armed"] and \
                            ((side == "LONG" and c[i] < bp) or (side == "SHORT" and c[i] > bp)) and \
                            (_bm is None or _bm.predict(np.asarray(
                                [_hold_feat_vec(A, sdir, avg, p["first_idx"], p["add_count"], i)]))[0] < _bth):
                        p["be_armed"] = True
                    if (i - p["first_idx"]) >= HOLD_5M:
                        _record(trades, p, c[i], "TIME_EXIT", i, ts)
                        events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None
            else:
                hit_edge = (side == "LONG" and np.isfinite(R[i]) and h[i] >= R[i]) or \
                           (side == "SHORT" and np.isfinite(S[i]) and l[i] <= S[i])
                if hit_edge:
                    _record(trades, p, R[i] if side == "LONG" else S[i], "EDGE_TP", i, ts)
                    events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None
                    continue
                back_center = np.isfinite(Cc[i]) and ((side == "LONG" and l[i] <= Cc[i]) or (side == "SHORT" and h[i] >= Cc[i]))
                if back_center:
                    _record(trades, p, Cc[i], "CENTER_LOCK", i, ts)
                    events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None
                elif (i - p["first_idx"]) >= HOLD_5M:
                    _record(trades, p, c[i], "TIME_EXIT", i, ts)
                    events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None

        # ── 4. 入口/add ──
        if (not short_only) and long_sig[i] and pend["LONG"] is None and (pos["LONG"] is None or pos["LONG"]["add_count"] < max_adds):
            pend["LONG"] = {"limit": c[i] * (1.0 - ENTRY_OFFSET), "placed_idx": i}
        if short_sig[i] and (htf_up is None or not htf_up[i]) and pend["SHORT"] is None and (pos["SHORT"] is None or pos["SHORT"]["add_count"] < max_adds):
            pend["SHORT"] = {"limit": c[i] * (1.0 + ENTRY_OFFSET), "placed_idx": i}

    # ── 期間末 強制クローズ ──
    for side in ("LONG", "SHORT"):
        if pos[side] is not None:
            _record(trades, pos[side], c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
            events.append((pd.Timestamp(ts[n - 1]), -pos[side]["size"]))
    return trades, events


def run_e36(df, box_tf, max_adds, spike_lm=None, spike_gate=None, zone_short=None):
    """E36 SHORT専用（shortset1[SHORT 1h MACD ゲート]＋iter9 出口を内包）＋急騰Exit。
    e35.run_partial_tp の shortset1+short_only パスの逐語相当（short_htf=True・short_only=True 固定）。
    教師生成・grid 選定は spike OFF（iter3 基底のまま＝教師を急騰Exitで歪めない）／最終 scored run だけ spike_lm を渡す。"""
    import lightgbm as lgb   # python3.13 のみ
    global BE_ARM_BARS
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    _p1 = "shift(" + "-"; _p2 = "center" + "=True"
    assert _p1 not in src and _p2 not in src, "leak 疑い（未来参照 shift/center）"
    A = _hold_arrays(df, box_tf)
    idx_of = {x: i for i, x in enumerate(df["ts"].tolist())}
    feats = _HOLD_FEATS; BE_TH = 0.40
    SH = True; FU = True                       # shortset1=iter9 ベース（shrink+full・θ/k は iter9 のまま）
    ADD1_FRAC = 0.5
    TG_GRID = [0.30, 0.40, 0.50]               # θ_gate（iter11/以前グリッド＝shortset1 と同一）
    KT_GRID = [0.0010, 0.0015, 0.0020]         # k_tp（同上）

    # ① 教師＝iter3基底（建値撤退OFF・spike OFF）→ booster（e35 shortset1 と同一手順）
    saved = BE_ARM_BARS; BE_ARM_BARS = 10 ** 9
    base_trades, _ = run_continuous(df, box_tf, max_adds)   # spike_lm 未指定＝教師は急騰Exit OFF（H2）
    BE_ARM_BARS = saved
    bt = pd.DataFrame(base_trades)
    bt["entry_time"] = pd.to_datetime(bt["entry_time"]); bt["exit_time"] = pd.to_datetime(bt["exit_time"])
    WIN = {"TP_FILLED", "EDGE_TP", "CENTER_LOCK"}
    rows = []
    for pid, g in bt.groupby("position_id"):
        g = g.sort_values("entry_time")
        lot_idx = [idx_of[x] for x in g["entry_time"]]; lot_px = g["entry_price"].astype(float).tolist()
        exit_idx = idx_of[g["exit_time"].iloc[0]]; sdir = 1 if g["side"].iloc[0] == "LONG" else -1
        label = 1 if g["exit_reason"].iloc[0] in WIN else 0; first_idx = lot_idx[0]
        for i in range(first_idx + 1, exit_idx):
            filled = [(li, lp) for li, lp in zip(lot_idx, lot_px) if li <= i]
            if not filled or not (np.isfinite(A["Cc"][i]) and np.isfinite(A["atr"][i])):
                continue
            avg_i = sum(lp for _, lp in filled) / len(filled)
            rows.append([g["entry_time"].iloc[0], label] + _hold_feat_vec(A, sdir, avg_i, first_idx, len(filled), i))
    snaps = pd.DataFrame(rows, columns=["entry_time", "label"] + _HOLD_FEATS)
    tr = snaps[snaps.entry_time < TRAIN_END].reset_index(drop=True)
    params = dict(n_estimators=300, num_leaves=15, min_child_samples=200, reg_alpha=1.0, reg_lambda=1.0,
                  learning_rate=0.03, random_state=42, verbose=-1)
    model = lgb.LGBMClassifier(**params); model.fit(tr[_HOLD_FEATS], tr["label"].to_numpy())
    booster = model.booster_
    print(f"  教師(iter3基底・spike OFF) {bt['position_id'].nunique()} 玉 / 学習スナップ {len(tr):,} / 戻る率 {tr.label.mean():.3f}")

    # ② 自己検査(a) 恒等: θ_gate=-1(partial 不発火) で iter5a と net 一致（spike OFF・5要素 plumbing 検証）
    df_tr = df[df.ts < TRAIN_END].reset_index(drop=True)
    base5a, _ = run_continuous(df_tr, box_tf, max_adds, be_gate=(booster, feats, BE_TH), short_htf=True, short_only=True)
    base5a_net = float(pd.DataFrame(base5a)["net_usd"].sum())
    chk, _ = run_continuous(df_tr, box_tf, max_adds, be_gate=(booster, feats, BE_TH),
                            partial_tp=(booster, feats, -1.0, 0.0015, None, SH, FU), short_htf=True, short_only=True)
    chk_net = float(pd.DataFrame(chk)["net_usd"].sum())
    ok_a = abs(chk_net - base5a_net) < 1e-6
    print(f"  [自己検査a 恒等] θ_gate=-1(不発火) net ${chk_net:.2f} == be_gate-only ${base5a_net:.2f} : {'✅' if ok_a else '⛔不一致'}")
    assert ok_a, "partial 不発火が be_gate-only と不一致＝恒等崩れ"

    # ③ θ_gate × k_tp グリッド（学習窓 純増最大・spike OFF・採点窓不参照・shortset1 と同一選定）
    print(f"  学習窓 baseline(be_gate-only) net ${base5a_net:.0f}（純増の基準・be_th={BE_TH}・add1_frac={ADD1_FRAC}）")
    best = None
    for tg in TG_GRID:
        for k in KT_GRID:
            q, _ = run_continuous(df_tr, box_tf, max_adds, be_gate=(booster, feats, BE_TH),
                                  partial_tp=(booster, feats, tg, k, ADD1_FRAC, SH, FU), short_htf=True, short_only=True)
            qd = pd.DataFrame(q); net = float(qd["net_usd"].sum())
            ptp = int((qd["exit_reason"] == "PARTIAL_TP").sum()); gain = net - base5a_net
            print(f"   θ_gate={tg} k_tp={k}: net ${net:.0f}（純増 {gain:+.0f}）/ PARTIAL_TP {ptp}")
            if best is None or gain > best[0]:
                best = (gain, tg, k)
    gain, btg, bk = best
    print(f"  → θ_gate*={btg} k_tp*={bk} add1_frac={ADD1_FRAC}（学習窓 純増 {gain:+.0f}）")

    # ④ 自己検査(a_e36) SHORT専用配線: short_only=True で LONG 玉/net=0（短絡未配線でない）
    qe = pd.DataFrame(run_continuous(df_tr, box_tf, max_adds, be_gate=(booster, feats, BE_TH),
                                     partial_tp=(booster, feats, btg, bk, ADD1_FRAC, SH, FU), short_htf=True, short_only=True)[0])
    nL = qe[qe.side == "LONG"]["position_id"].nunique(); eL = float(qe[qe.side == "LONG"]["net_usd"].sum())
    print(f"  [自己検査a_e36 SHORT専用] LONG 玉 {nL} / LONG net ${eL:.2f} : {'✅(LONG=0)' if (nL == 0 and abs(eL) < 1e-9) else '⛔LONG 残存'}")
    assert nL == 0 and abs(eL) < 1e-9, "short_only=True なのに LONG 玉/net が残存（未配線）"

    # ⑤ 自己検査(a_spike) 急騰Exit 配線（学習窓・採点窓不参照）: spike OFF と ON を比べ、SPIKE_SL が SHORT 玉に出る・size 保存・SPIKE_SL は SHORT のみ
    L_star = spike_threshold(spike_lm[0], spike_lm[1]) if spike_lm is not None else None
    if spike_lm is not None:
        q_off = pd.DataFrame(run_continuous(df_tr, box_tf, max_adds, be_gate=(booster, feats, BE_TH),
                                            partial_tp=(booster, feats, btg, bk, ADD1_FRAC, SH, FU), short_htf=True, short_only=True, spike_lm=None)[0])
        q_on = pd.DataFrame(run_continuous(df_tr, box_tf, max_adds, be_gate=(booster, feats, BE_TH),
                                           partial_tp=(booster, feats, btg, bk, ADD1_FRAC, SH, FU), short_htf=True, short_only=True, spike_lm=spike_lm)[0])
        n_off = float(q_off["net_usd"].sum()); n_on = float(q_on["net_usd"].sum())
        spk = int((q_on["exit_reason"] == "SPIKE_SL").sum())
        spk_short = int(((q_on["exit_reason"] == "SPIKE_SL") & (q_on["side"] == "SHORT")).sum())
        print(f"  [自己検査a_spike] L*={L_star:.3f}（K={spike_lm[0]}/α={spike_lm[1]}）/ spike OFF net ${n_off:.0f} → ON net ${n_on:.0f}"
              f"（急騰由来 {n_on-n_off:+.0f}）/ SPIKE_SL {spk}件(SHORT {spk_short}) : "
              f"{'✅効いている（SPIKE_SL 発火・全て SHORT）' if (spk > 0 and spk == spk_short) else '⚠️SPIKE_SL 未発火 or LONG混入'}")
        assert spk == spk_short, "SPIKE_SL が SHORT 以外で発火（E36 SHORT専用違反）"

    # ⑤' 判別器ゲート θ を学習窓でスイープ選定（iter2・採点窓不参照＝L-267）。
    #     spike_gate が set（CLI 値はゲート ON のトリガ）なら GRID から学習窓 net 最大の θ* を選ぶ。
    #     ゲート無し(spike_gate=None)＝現行 spike-ON。θ↑＝多く切る／θ↓＝戻る判別玉を多く残す。
    GATE_GRID = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
    if spike_lm is not None and spike_gate is not None:
        q_g0 = pd.DataFrame(run_continuous(df_tr, box_tf, max_adds, be_gate=(booster, feats, BE_TH),
                                           partial_tp=(booster, feats, btg, bk, ADD1_FRAC, SH, FU), short_htf=True, short_only=True, spike_lm=spike_lm, spike_gate=None)[0])
        s0 = int((q_g0["exit_reason"] == "SPIKE_SL").sum()); ng0 = float(q_g0["net_usd"].sum())
        print(f"  [自己検査a_spike_gate] ゲート無し(現行spike) SPIKE_SL {s0}件 / 学習窓 net ${ng0:.0f}（基準）")
        gbest = (ng0, None)   # ゲート無しを基準に含める（改善しないなら採用しない）
        for th in GATE_GRID:
            qg = pd.DataFrame(run_continuous(df_tr, box_tf, max_adds, be_gate=(booster, feats, BE_TH),
                                             partial_tp=(booster, feats, btg, bk, ADD1_FRAC, SH, FU), short_htf=True, short_only=True, spike_lm=spike_lm, spike_gate=th)[0])
            s1 = int((qg["exit_reason"] == "SPIKE_SL").sum()); ng1 = float(qg["net_usd"].sum())
            print(f"   θ={th}: SPIKE_SL {s1}件（除外 {s0-s1}玉）/ 学習窓 net ${ng1:.0f}（純増 {ng1-ng0:+.0f}）")
            assert s1 <= s0, "ゲートで SPIKE_SL が増えた（配線異常）"
            if ng1 > gbest[0]:
                gbest = (ng1, th)
        spike_gate = gbest[1]   # 学習窓 net 最大の θ*（ゲート無しが最良なら None＝ゲート不採用）
        print(f"  → spike_gate θ*={spike_gate}（学習窓 net 最大 ${gbest[0]:.0f}・None=ゲート無しが最良＝不採用）")

    # ⑥ 最終 scored run（spike_lm/spike_gate を最終 run だけに渡す）→ size 保存 → cap → 出力
    trades, _ = run_continuous(df, box_tf, max_adds, be_gate=(booster, feats, BE_TH),
                               partial_tp=(booster, feats, btg, bk, ADD1_FRAC, SH, FU, None),
                               short_htf=True, short_only=True, spike_lm=spike_lm, spike_gate=spike_gate)
    t = pd.DataFrame(trades); t["entry_time"] = pd.to_datetime(t["entry_time"])
    rc = t.groupby("position_id").agg(sz=("size_btc", "sum"), addc=("add_count", "max"))
    bad = int((np.abs(rc["sz"] - rc["addc"] * UNIT) > 1e-9).sum())
    print(f"  [自己検査b size保存] Σsize_btc≠add_count×UNIT の玉 {bad}（0=総量保存 ✅）")
    assert bad == 0, "size 保存違反"
    mx = _verify_cap(trades)
    print(f"  [自己検査c cap] 同時保有 max = {mx:.4f} BTC {'✅' if mx <= CAP + 1e-9 else '⛔超過'}（予算 {CAP}）")
    assert mx <= CAP + 1e-9, f"同時保有 {mx:.4f} > cap {CAP}"
    print(f"  約定 {len(t)} / 出口 {dict(t['exit_reason'].value_counts())} / θ_gate*={btg} k_tp*={bk} spike={spike_lm}")

    _xp = {"be_th": BE_TH, "θ_gate*": btg, "k_tp*": bk, "add1_frac": ADD1_FRAC}
    _xp["ptp_shrink（部分利確目標の時間縮小）"] = "iter8: ptp=avg×(1±k_tp×r)・r=(HOLD_5M−経過バー)/HOLD_5M（線形・a-priori）・建値でフロア"
    _xp["full_close（縮む目標到達で全閉鎖）"] = "iter9: 死ぬ判別玉が縮む目標 ptp に到達したら残り全玉を maker 決済（arxiv 1707.03498 Thm3.3）"
    _xp["short_htf_gate（SHORT入口の1h MACDフィルタ）"] = "SHORT は直近で閉じた 1h MACD line≤0 のときのみ入口（1h上向き=MACD>0 では SHORT 抑制）・符号のみ=価格非依存(H6)"
    _xp["short_only（E36 SHORT専用＝LONG入口を切る）"] = "LONG 入口を出さず SHORT のみ取引＝予算0.12 が SHORT に解放"
    if spike_lm is not None:
        _xp["spike_lm（急騰Exit・Lee-Mykland jump SPIKE_SL）"] = (
            f"K={spike_lm[0]}本/α={spike_lm[1]}・L*={L_star:.3f}（a-priori・データで sweep しない L-267）。"
            f"SHORT 保有・含み損側(c>avg)・L_i=r_i/√(局所bipower)>L* で成行カット（taker）＝統計的急騰のみ・深さ stop でない")
    if spike_gate is not None:
        _xp["spike_gate（急騰Exit の判別器ゲート・iter2）"] = (
            f"θ={spike_gate}（partial の hold-ML booster 流用・predict<θ=死ぬ判別の玉のみ SPIKE_SL）。"
            f"急騰でも判別器が「中心に戻る=TP できる」と言った玉は切らない＝戻り玉の巻き込みを減らす（de Prado メタラベリング）")
    if zone_short is not None:
        _xp["zone_short（件数レバー・強レンジで SHORT 反転ゾーン拡大・freq-iter1）"] = (
            f"z_wide={zone_short[0]}（通常 ZONE_FRAC={e35.ZONE_FRAC}）・er_strong_q={zone_short[1]}（学習窓 ER 分位）。"
            f"ER<学習窓 q(er_strong_q)=強い平均回帰のバーだけ up_zone を res≤z_wide·W に拡大→新規 SHORT 発火増。"
            f"弱レンジは 0.25 のまま・LONG は不変（SHORT 専用・arXiv 1607.00454）")
    _output_and_report(t, f"_{box_tf}_shortset1", extra_params=_xp, stem="e36_short_oscillation")


def main():
    global BE_ARM_BARS
    ap = argparse.ArgumentParser()
    ap.add_argument("--box-tf", choices=e35.TFS, default="5m")
    ap.add_argument("--max-adds", type=int, default=MAX_ADDS)
    ap.add_argument("--smoke", type=int, default=0, help="先頭 N バーだけで動作確認")
    # ★採用（2026-06-21 まこさん GO）= gated spike が既定（判別器ゲート付き急騰Exit・採点窓 $539.06・最大DD改善・勝率不変）。
    ap.add_argument("--no-spike", action="store_true", help="急騰Exit を OFF（=spike-OFF 恒等参照・E36 base $427.66）")
    ap.add_argument("--spike-lm", action="store_true", help="（既定ON・後方互換の no-op）")
    ap.add_argument("--spike-lm-k", type=int, default=270, help="Lee-Mykland 窓 K 本（既定270≈1日・a-priori）")
    ap.add_argument("--spike-lm-alpha", type=float, default=0.01, help="有意水準 α（既定0.01・a-priori・データで sweep しない L-267）")
    ap.add_argument("--spike-gate", type=float, default=0.5, help="判別器ゲート θ トリガ（既定0.5＝採用・実際の θ は学習窓スイープ選定 L-267）。hold-ML predict<θ=死ぬ判別の玉だけ SPIKE_SL（戻る玉は急騰でも残す）")
    # ★採用（2026-06-22 まこさん GO）= 件数レバー freq-iter1 が既定（強レンジで SHORT 反転ゾーン拡大・採点窓 $548.74・両窓 net 改善・件数 1.05/日）。
    ap.add_argument("--no-zone", action="store_true", help="件数レバー（freq-iter1）を OFF（=ゾーン拡大なし恒等参照・E36 gated spike $539.06）")
    ap.add_argument("--zone-wide", type=float, default=0.35, help="件数レバー（freq-iter1・既定 0.35＝採用）: 強レンジで SHORT 反転ゾーンを W×0.25→W×この値 に拡大")
    ap.add_argument("--zone-er-q", type=float, default=0.25, help="強レンジ判定の学習窓 ER 分位（ER<この分位=強い平均回帰のバーだけ拡大・a-priori 0.25・採点窓スイープ禁止 L-267）")
    a = ap.parse_args()

    if a.no_spike:
        spike_lm = None; spike_gate = None
    else:
        spike_lm = (a.spike_lm_k, a.spike_lm_alpha); spike_gate = a.spike_gate   # 採用＝gated spike が既定
    print("=" * 100)
    print(f"[E36] SHORT専用 オシレーション（shortset1[1h MACDゲート]＋iter9 出口）＋急騰Exit "
          f"{'OFF（=E36 base 恒等 $427.66）' if a.no_spike else 'ON gated（採用・spike_lm=(K%d/α%.3g)・判別器ゲート学習窓選定）' % (a.spike_lm_k, a.spike_lm_alpha)}")
    df = _load(a.smoke)
    print(f"  価格 {e35.e34v1.CSV.name}（{len(df):,}本・{df.ts.iloc[0].date()}〜{df.ts.iloc[-1].date()}）")
    print(f"  計器 maker {ee.MAKER_FEE} / taker {ee.TAKER_FEE} / slip {ee.SLIPPAGE} / funding {ee.FUNDING_RATE_8H}/8h / unit {UNIT}")

    lo, hi, nW, _sig = _attach_entry_cols(df, a.box_tf)
    print(f"  box={a.box_tf} W正常帯=[{lo:.3f}%,{hi:.3f}%]（in_box 学習 {nW:,}本）/ 入口発火 SHORT {int(df['short_entry'].sum())}")
    if a.no_zone:
        zone_short = None
        print(f"  [zone拡大 OFF＝恒等参照] 反転ゾーン {e35.ZONE_FRAC} のまま（E36 gated spike $539.06 と一致）")
    else:
        er_s, n_strong, n_b, n_a = _widen_short_zone(df, a.box_tf, a.zone_wide, a.zone_er_q)
        zone_short = (a.zone_wide, a.zone_er_q)
        print(f"  [zone拡大 ON・freq-iter1＝採用] 強レンジ(er<q{a.zone_er_q}={er_s:.3f}) {n_strong:,}本で反転ゾーン {e35.ZONE_FRAC}→{a.zone_wide}"
              f" / SHORT 入口発火 {n_b}→{n_a}（+{n_a-n_b}）")
    run_e36(df, a.box_tf, a.max_adds, spike_lm=spike_lm, spike_gate=spike_gate, zone_short=zone_short)
    print("=" * 100)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""e35_range_oscillation.py — E35 レンジ上下オシレーション BOT（一式・連続モード両方向・採点まで）

設計書: .claude/ratchet/e35_design.md（Peterson hypothesis-driven・deep-research baseup・まこさん GO）。
進め方（E34 と同じアジャイル）: Entry/Exit を一式で連続モードで回し、score.py の月次 net を「地面」にして反復改善。
  ⛔ 件数診断だけ分割しない（Entry/Exit はセットで net が決まる=不可分）。--diagnostic は採点前の発火確認の補助。

★判定は score.py の数字だけ（本スクリプトは eval_engine 定数を import のみ・審判が独立再計算）。
  CSV の net_usd は self-check 用（score.py が再計算して差を表示）。

流用（実体 Read 済 2026-06-14・新規ロジックを足さない）:
  - e34_range_zscore_taker: CSV / add_indicators(sma/std/dev_z/atr/adx・taker 不使用)
  - e34_range_base: add_analysis_features(stoch等) / 連続モードの作法(pending fill・約定barの次出口・cap停止・_verify_cap・_funding_cost)
  - e35_box: 箱 3列×3足(fractal j+2 / attach_upper_tf / volume_at_support・leak assert 内蔵)
  - eval_engine: 確定コスト定数（改造禁止・import のみ）

入口（a priori 単一・スイープしない・hook L-267／反転確認は診断 0.06/日 を受け「クロス→oversoldで上向き」に緩めた）:
  RANGE_OK   = (Choppiness>61.8) ∩ (ADX<25) ∩ in_box ∩ (W∈学習[q25,q75])
  LONG_ENTRY  = RANGE_OK ∩ 下限ゾーン(sup≤0.25W) ∩ (%K<30 ∩ %K>前%K)   ← クロスでなく oversold で上向き
  SHORT_ENTRY = RANGE_OK ∩ 上限ゾーン(res≤0.25W) ∩ (%K>70 ∩ %K<前%K)
出口（両サイド・v1 は単一TP=中心C 全ロット／改善で複数TP分割）:
  TP = 箱中心 C=(S+R)/2 へ戻り（動く・LONG high≥C / SHORT low≤C・C が建値±コスト床を超える時だけ武装）=指値 maker
  SL = 箱ブレイク（LONG 終値<S / SHORT 終値>R・構造的）=能動撤退 成行 taker
  時間切れ = 48本(4h)・成行 taker
add: 同サイド再発火で merge・平均建値・unit 0.024・★cap=LONG+SHORT 合算≤0.12 で停止。

H 制約（コード内 assert / コメント）:
  H1 cap   … 任意 t で LONG+SHORT 合算 ≤0.12（fill 時に held+UNIT>cap で add 停止 ＋ _verify_cap 実測 assert ＋ score.py 物理ゲート）。
  H2 leak  … 箱は e35_box が j+2/attach/破壊テストで担保・指標は shift ベース・出口は約定 bar の次以降（i>last_fill_idx）。
  H5 約定   … entry/TP=指値 maker（close×(1∓offset)）／箱ブレイク SL・時間切れ=成行 taker+slip。
  H6 価格非依存 … 入口は距離%/比/無次元。箱の価格(S/R/C)は「現値との距離%」由来で TP/SL の比較に使うのみ（閾値化しない）。
  H8 期間分割 … W 分位は学習 ts<2025-01。採点 2025-06〜12・封印 2026-03〜05 不参照。
  H15 ボラ逃げ … 入口=方向（ゾーン+反転）・ボラ(ATR)は使わない（SL は箱ブレイク=構造／時間のみ）・LONG/SHORT 分離。
  H16 1変更 … 新構造のベース v1 を一式1本（E34 と同じ「正しい器を1本」）。以後 複数TP/多TF重み/固定値ML は1つずつ。
"""
from __future__ import annotations
import argparse
import pathlib
import sys
from datetime import timezone

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import eval_engine as ee                    # noqa: E402  確定コスト定数 + funding 境界（改造禁止・import のみ）
import e34_range_zscore_taker as e34v1      # noqa: E402  CSV / add_indicators（taker は呼ばない）
import e34_range_base as e34b               # noqa: E402  add_analysis_features（stoch 等）
import e35_box                              # noqa: E402  箱 3列×3足（leak/H6 assert 内蔵）
import verify_design_contract as _vdc       # noqa: E402  設計↔実装 自己チェック（設計書の部品リストを読む）

RATCHET = ROOT / "results" / "priority_rebuild" / "ratchet"
DESIGN_MD = ROOT / ".claude" / "ratchet" / "e35_design.md"   # 入口組み立ての唯一の正（設計書 DESIGN_CONTRACT）
TRAIN_END = e34v1.TRAIN_END                 # 2025-01-01（W 分位・診断の学習境界・H8）
SC_START = pd.Timestamp("2025-06-01")       # 採点窓 開始（新窓・taker 実被覆内）
SCORE_END = pd.Timestamp("2026-01-01")      # 採点窓 終了（2025-12-31 まで）
SEAL_START = pd.Timestamp("2026-03-01")     # 封印 2026-03〜05 は出力に含めない（最終1回まで温存）

# ── a priori 単一固定（最良値スイープしない・hook L-267）─────────────────────────────
CI_N = 14
CI_THRESH = 61.8          # Choppiness>61.8 = 横ばい（フィボ 61.8・E.W.Dreiss 代表閾値）
ADX_MAX = e34v1.ADX_MAX   # 25.0（※レンジ判定からは外した・Jump Model 近似に置換・KB §I 固定ADX25 削除）
ER_N = 20                 # Kaufman Efficiency Ratio 窓（レンジ判定の主役・低効率=レンジ）
ER_SMOOTH = 5             # 持続性（過去のみ平滑化＝flicker 抑制・Jump penalty 近似・research C4/C5）
ER_Q = 0.5                # レンジ閾値＝学習期間 ER の分位（ER<この分位=レンジ・a priori 単一・スイープしない）
ZONE_FRAC = 0.25          # 箱の下/上 25% を反転ゾーンに
W_Q_LO = 0.25
W_Q_HI = 0.75
TFS = e35_box.TFS         # ['5m','1h','4h']

CAP = 0.12                # 予算=全建玉（LONG+SHORT）合計の上限（H1・CLAUDE §0-2）
UNIT = e34v1.SIZE         # 0.024 BTC（add 単位・H10）
MAX_ADDS = 5              # 1 サイドの最大段数（cap 合算が別途常に有効）
TTL = ee.DEFAULT_TTL      # 指値 TTL 3 本
ENTRY_OFFSET = ee.ENTRY_LIMIT_OFFSET   # 0.0001
COST_FLOOR = e34v1.COST_FLOOR          # 0.0020（TP が建値±床を超える時だけ武装）
HOLD_5M = e34v1.HOLD_5M                # 48 本（4h・初回 entry 起点）
BE_ARM_BARS = 12          # iter4 建値撤退 arm（1h・含み損玉が建値へ戻ったら損ゼロ maker 撤退・学習窓上限 N=12 最良・両窓一致・a-priori 固定・スイープしない L-267）
PRIORITY = 35


def add_choppiness(df: pd.DataFrame) -> pd.DataFrame:
    """Choppiness Index(14)（横ばい度・CI>61.8=レンジ・全て当該足まで＝leak-safe）。"""
    c, h, l = df["close"], df["high"], df["low"]
    pc = c.shift(1)
    tr = np.maximum(h - l, np.maximum((h - pc).abs(), (l - pc).abs()))   # true range（過去 close のみ）
    tr_sum = tr.rolling(CI_N).sum()
    rng = (h.rolling(CI_N).max() - l.rolling(CI_N).min()).replace(0, np.nan)
    df["chop"] = 100.0 * np.log10(tr_sum / rng) / np.log10(CI_N)
    return df


def add_jump_model(df: pd.DataFrame) -> pd.DataFrame:
    """Jump Model 近似＝レンジ判定の主役（research C4/C5・固定閾値でなく適応・leak-safe）。
    Kaufman Efficiency Ratio = |C_t − C_{t−N}| / Σ|ΔC|（低い=往復=レンジ / 高い=一方向=トレンド）。
    過去のみの平滑化(ER_SMOOTH)で regime のちらつき(flicker)を抑える＝jump penalty の近似。
    """
    c = df["close"]
    change = (c - c.shift(ER_N)).abs()
    vol = c.diff().abs().rolling(ER_N).sum().replace(0, np.nan)
    df["er"] = (change / vol).rolling(ER_SMOOTH).mean()   # 持続性（過去のみ＝leak-safe）
    return df


# ── 設計↔実装 自己チェック（設計書の部品リストで入口を組み立てる・部品が欠けたらプログラムが自分で停止）──
def _entry_contract() -> dict:
    """設計書 e35_design.md の DESIGN_CONTRACT(must_combine) を読む＝入口組み立ての唯一の正。"""
    c = _vdc.extract_contract(open(DESIGN_MD, encoding="utf-8").read())
    if not c or "must_combine" not in c:
        raise RuntimeError(f"[設計↔実装ゲート] e35_design.md に DESIGN_CONTRACT(must_combine) が無い: {DESIGN_MD}")
    return c["must_combine"]


def _assemble_signals(components: dict, must_combine: dict) -> dict:
    """設計書 must_combine の通りに合成シグナル（range_ok/long_entry/short_entry）を AND 組み立てる。
    設計が要求した成分が components に無ければ即停止＝設計通りに実装しないと動かない（自己チェック・類型G物理防止）。"""
    built, pending = {}, dict(must_combine)
    for _ in range(len(pending) + 1):
        progressed = False
        for sym, parts in list(pending.items()):
            srcs = [components.get(p, built.get(p)) for p in parts]
            if any(s is None for s in srcs):
                continue
            res = srcs[0]
            for s in srcs[1:]:
                res = res & s
            built[sym] = res
            del pending[sym]
            progressed = True
        if not pending:
            return built
        if not progressed:
            missing = {sym: [p for p in parts if p not in components and p not in built]
                       for sym, parts in pending.items()}
            raise RuntimeError(
                "[設計↔実装ゲート・自己チェック] 設計書 DESIGN_CONTRACT が要求する成分が実装に無い → "
                f"{missing}。設計通りに実装してから実行（プログラムが自分で停止）。")
    return built


def _build_signals_for_tf(df: pd.DataFrame, tf: str, w_lo: float, w_hi: float) -> dict:
    """1 足分（tf）の入口系列（bool Series 辞書）。合成（range_ok/long_entry/short_entry）は設計書の部品リスト通りに組み立てる。"""
    sup = df[e35_box.sup_col(tf)]
    res = df[e35_box.res_col(tf)]
    chop = df["chop"]; adx = df["adx"]; k = df["stoch_k"]; er = df["er"]

    in_box = sup.notna() & (sup > 0) & res.notna() & (res > 0)
    W = sup + res
    fill = lambda s: s.fillna(False)
    er_thr = er[df["ts"] < TRAIN_END].quantile(ER_Q)   # レンジ閾値＝学習期間の ER 分位（データ駆動・覗き見なし H8）

    # base 成分（jm_ok=Jump Model 近似がレンジ判定の主役・固定 chop_ok/adx_ok はレンジ判定から外した）
    components = {
        "jm_ok": fill(er < er_thr),
        "chop_ok": fill(chop > CI_THRESH),
        "adx_ok": fill(adx < ADX_MAX),
        "in_box": fill(in_box),
        "w_ok": fill(in_box & (W >= w_lo) & (W <= w_hi)),
        "low_zone": fill(in_box & (sup <= ZONE_FRAC * W)),
        "up_zone": fill(in_box & (res <= ZONE_FRAC * W)),
        # 反転確認（oversold/overbought で %K が反転）
        "long_rev": fill((k < 30) & (k > k.shift(1))),
        "short_rev": fill((k > 70) & (k < k.shift(1))),
    }
    # ★設計書 DESIGN_CONTRACT の部品リスト通りに合成（成分が欠けたら停止＝設計通りに実装しないと動かない）
    built = _assemble_signals(components, _entry_contract())

    return {**components, **built, "W": W}


def _w_band(df: pd.DataFrame, tf: str, tr_mask: pd.Series) -> tuple:
    """学習(<2025-01)の in_box バーの W 分布から [q0.25, q0.75]（データ駆動・覗き見なし H8）。"""
    sup = df[e35_box.sup_col(tf)]; res = df[e35_box.res_col(tf)]
    in_box = sup.notna() & (sup > 0) & res.notna() & (res > 0)
    W = (sup + res)[(in_box & tr_mask).fillna(False)]
    if len(W) == 0:
        return float("nan"), float("nan"), 0
    return float(W.quantile(W_Q_LO)), float(W.quantile(W_Q_HI)), int(len(W))


def _funding_cost(side: int, entry_ts, exit_ts, size: float, mark: float) -> float:
    """保有中 8h 境界ごと funding（LONG dir=+1 払い / SHORT dir=-1 受取）。score.py と同式。"""
    e = pd.Timestamp(entry_ts).to_pydatetime().replace(tzinfo=timezone.utc)
    x = pd.Timestamp(exit_ts).to_pydatetime().replace(tzinfo=timezone.utc)
    cost = 0.0
    for _ in ee._funding_boundaries(e, x):
        cost += side * size * mark * ee.FUNDING_RATE_8H
    return cost


def _record_lots(trades, pos, lots, exit_price, reason, exit_idx, ts_arr):
    """指定 lots を fill(lot)単位で複数行に記録（部分決済 PARTIAL_TP 対応・cap 会計を実保有に忠実化・H1）。LONG/SHORT 両対応。
    TP/逆側端/建値撤退/部分利確=maker・箱ブレイク/中心戻り/時間切れ=taker。net 合計は merge と恒等（gross/手数料は lot 分割で一致・funding は各 lot fill 起点）。"""
    side = pos["side"]; sdir = 1 if side == "LONG" else -1
    exit_ts = pd.Timestamp(ts_arr[exit_idx]); exit_px = float(exit_price)
    is_taker = reason not in ("TP_FILLED", "EDGE_TP", "BE_EXIT", "PARTIAL_TP")  # 指値 maker 群（部分利確 PARTIAL_TP も maker）・SL(箱ブレイク)/中心戻り/時間切れ/EOD は成行 taker
    pos_id = f"{side}_{int(pos['first_idx'])}"            # 玉ID（玉単位分析で束ねる）
    add_count = int(pos["add_count"]); max_fav = float(pos["max_fav"])
    atr14 = round(float(pos["atr_entry"]), 2)
    adx_e = round(float(pos["adx_entry"]), 3) if np.isfinite(pos["adx_entry"]) else None
    k_e = round(float(pos["k_entry"]), 2) if np.isfinite(pos["k_entry"]) else None
    w_e = round(float(pos["W_entry"]), 5) if np.isfinite(pos["W_entry"]) else None
    for lot_idx, lot_price in lots:
        entry_ts = pd.Timestamp(ts_arr[lot_idx]); lp = float(lot_price)
        gross = (exit_px - lp) * UNIT * sdir
        entry_fee = lp * UNIT * ee.MAKER_FEE             # entry は指値 maker
        exit_fee = exit_px * UNIT * (ee.TAKER_FEE if is_taker else ee.MAKER_FEE)
        slip = (exit_px * UNIT * ee.SLIPPAGE) if is_taker else 0.0
        funding = _funding_cost(sdir, entry_ts, exit_ts, UNIT, lp)
        net = gross - entry_fee - exit_fee - slip - funding
        trades.append({
            "entry_time": entry_ts, "exit_time": exit_ts, "side": side,
            "priority": PRIORITY, "regime": "range", "position_id": pos_id, "add_count": add_count,
            "size_btc": round(UNIT, 6), "entry_price": round(lp, 2), "exit_price": round(exit_px, 2),
            "exit_reason": reason, "hold_min": int((exit_idx - lot_idx) * 5),
            "atr_14": atr14, "adx_at_entry": adx_e, "stoch_k_at_entry": k_e, "box_W_pct_at_entry": w_e,
            "entry_hour": int(entry_ts.hour), "entry_weekday": int(entry_ts.weekday()),
            "mfe_usd": round((max_fav - lp) * UNIT * sdir, 4),
            "gross_usd": round(gross, 4), "fee_usd": round(entry_fee + exit_fee + slip, 4), "net_usd": round(net, 4),
        })


def _record(trades, pos, exit_price, reason, exit_idx, ts_arr):
    """1 ポジ全 lots を記録（_record_lots へ委譲・従来動作不変）。"""
    _record_lots(trades, pos, pos["lots"], exit_price, reason, exit_idx, ts_arr)


# ── 保有中判定 ML（iteration-2 フェーズ2）の特徴量＝教師作成と runtime 予測で共用（整合保証・全て t 時点＝leak-safe）──
_HOLD_FEATS = ["bars_held", "unreal_pct", "dist_to_tp_pct", "box_sup_5m", "box_res_5m", "box_w_5m",
               "box_sup_1h", "box_res_1h", "box_sup_4h", "box_res_4h", "atr_pct", "adx", "er",
               "stoch_k", "stoch_d", "chop", "bb_slope_pct", "bb_width", "add_count_so_far"]


def _hold_arrays(df: pd.DataFrame, box_tf: str) -> dict:
    """保有中特徴の素配列（教師作成・runtime 予測で同一 source＝整合保証）。全て当該バーまでの値。"""
    sup = df[e35_box.sup_col(box_tf)].to_numpy(float); res = df[e35_box.res_col(box_tf)].to_numpy(float)
    c = df["close"].to_numpy(float)
    S = c / (1.0 + sup / 100.0); R = c * (1.0 + res / 100.0)
    return {
        "close": c, "atr": df["atr"].to_numpy(float), "adx": df["adx"].to_numpy(float),
        "k": df["stoch_k"].to_numpy(float), "d": df["stoch_d"].to_numpy(float),
        "er": df["er"].to_numpy(float), "chop": df["chop"].to_numpy(float),
        "bbs": df["bb_mid_slope_pct"].to_numpy(float), "bbw": df["bb_width"].to_numpy(float),
        "sup5": sup, "res5": res,
        "sup1": df["box_sup_dist__1h"].to_numpy(float), "res1": df["box_res_dist__1h"].to_numpy(float),
        "sup4": df["box_sup_dist__4h"].to_numpy(float), "res4": df["box_res_dist__4h"].to_numpy(float),
        "Cc": (S + R) / 2.0,
    }


def _hold_feat_vec(A: dict, sdir: int, avg_i: float, first_idx: int, nlot: int, i: int) -> list:
    """保有中 1 バーの特徴ベクトル（_HOLD_FEATS 順・%/比率＝H6・全て t 時点＝leak-safe）。"""
    cl = A["close"][i]
    return [
        float(i - first_idx),
        (cl - avg_i) / avg_i * sdir * 100.0,                # 含み益%（順方向+）
        (A["Cc"][i] - cl) / cl * sdir * 100.0,              # 中心Cまでの残り%（+=未到達）
        A["sup5"][i], A["res5"][i], A["sup5"][i] + A["res5"][i],
        A["sup1"][i], A["res1"][i], A["sup4"][i], A["res4"][i],
        A["atr"][i] / cl * 100.0,
        A["adx"][i], A["er"][i], A["k"][i], A["d"][i], A["chop"][i],
        A["bbs"][i], A["bbw"][i], float(nlot),
    ]


def run_continuous(df: pd.DataFrame, box_tf: str, max_adds: int, hold_ctx=None, be_gate=None, partial_tp=None):
    """連続モード両方向。LONG/SHORT を並行管理（merge・cap 合算停止）・TP=箱中心C・SL=箱ブレイク・時間切れ。
    hold_ctx=(booster, feats, theta) を渡すと、保有中の各バーで P(TP)<theta の玉を早期撤退（ML_STANCH・成行 taker）。
    be_gate=(booster, feats, theta) を渡すと、iter4 建値撤退の武装を「戻らないと判別(predict<theta)した含み損玉」だけに絞る
      ＝戻ると判別した玉は武装せず延長/時間切れへ（iter5a 諦め除外・切らない・損ゼロ建値の限定は不変）。
    既定 None＝iter4 と完全同一（be_gate 分岐は _bm is None で素通り＝恒等）。"""
    n = len(df)
    ts = df["ts"].to_numpy()
    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    atr = df["atr"].to_numpy(float); adx = df["adx"].to_numpy(float); kk = df["stoch_k"].to_numpy(float)
    sup = df[e35_box.sup_col(box_tf)].to_numpy(float)     # 現値より下の支えまでの距離%
    res = df[e35_box.res_col(box_tf)].to_numpy(float)     # 現値より上の抵抗までの距離%
    long_sig = df["long_entry"].to_numpy(bool); short_sig = df["short_entry"].to_numpy(bool)
    # 箱の価格（距離%→価格・動く箱）。サポート/レジ無し（NaN）の足は箱中心/ブレイク判定をしない。
    S = c / (1.0 + sup / 100.0)
    R = c * (1.0 + res / 100.0)
    Cc = (S + R) / 2.0
    Wpct = sup + res
    A = _hold_arrays(df, box_tf) if (hold_ctx is not None or be_gate is not None or partial_tp is not None) else None   # 保有中判定 ML 特徴の素
    _hm, _hf, _hth = hold_ctx if hold_ctx is not None else (None, None, None)
    _bm, _bf, _bth = be_gate if be_gate is not None else (None, None, None)   # iter5a 建値撤退の武装ゲート（諦め除外）
    _pm, _pf, _pgate, _ptp = partial_tp if partial_tp is not None else (None, None, None, None)   # iter6 部分利確（死ぬ判別玉の前半含み益を1ロット maker 利確）

    trades = []
    pos = {"LONG": None, "SHORT": None}
    pend = {"LONG": None, "SHORT": None}
    events = []        # (ts, +/-size) 実 add/決済タイムライン（cap 合算 honest 検証）

    def held_total():
        return (pos["LONG"]["size"] if pos["LONG"] else 0.0) + (pos["SHORT"]["size"] if pos["SHORT"] else 0.0)

    def open_or_add(side, fp, i):
        sdir = 1 if side == "LONG" else -1
        if pos[side] is None:
            if not (np.isfinite(atr[i]) and np.isfinite(Cc[i])):
                return
            if held_total() + UNIT > CAP + 1e-9:          # ★新規建ても cap=LONG+SHORT 合算で停止（H1・両branch）
                return
            pos[side] = {"side": side, "avg": fp, "size": UNIT, "add_count": 1, "first_idx": i, "last_fill_idx": i,
                         "atr_entry": atr[i], "adx_entry": adx[i], "k_entry": kk[i], "W_entry": Wpct[i],
                         "max_fav": h[i] if side == "LONG" else l[i], "extended": False, "be_armed": False,
                         "partial_done": False,           # iter6 部分利確を1玉1回に制限
                         "lots": [(i, fp)]}               # ★fill 単位記録（each lot＝その fill 時刻・size UNIT）
            events.append((pd.Timestamp(ts[i]), UNIT))
        else:
            if held_total() + UNIT > CAP + 1e-9:          # ★cap=LONG+SHORT 合算で停止（H1）
                return
            p = pos[side]; new_sz = p["size"] + UNIT
            p["avg"] = (p["avg"] * p["size"] + fp * UNIT) / new_sz
            p["size"] = new_sz; p["add_count"] += 1; p["last_fill_idx"] = i
            p["lots"].append((i, fp))                     # ★fill 単位記録
            events.append((pd.Timestamp(ts[i]), UNIT))

    for i in range(n):
        # ── 1. pending fill（LONG: low≤limit / SHORT: high≥limit・約定 bar の次 bar から TTL）──
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

        # ── 2. MFE 極値更新（記録用）──
        for side in ("LONG", "SHORT"):
            p = pos[side]
            if p is None:
                continue
            if side == "LONG":
                p["max_fav"] = max(p["max_fav"], h[i])
            else:
                p["max_fav"] = min(p["max_fav"], l[i])

        # ── 3. 出口（約定 bar の次以降・SL 箱ブレイク → [未延長]中心C到達=延長アーム/ML/時間切れ → [延長]逆側端/中心戻り/時間切れ）──
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
            if not p["extended"]:
                # iter6 部分利確（賢いB）: 死ぬ判別玉(_pm.predict<θ_gate)が前半に小利TP(avg±k_tp・maker)に到達したら 1ロットだけ maker 利確。
                #   残りは avg 不変で現行出口へ（勝ち判別玉は触らない＝運び無傷／玉会計=部分1+残りで総size保存）。1玉1回。≥2ロットのみ。
                if _pm is not None and not p["partial_done"] and len(p["lots"]) >= 2 and np.isfinite(Cc[i]):
                    ptp = avg * (1.0 + _ptp) if side == "LONG" else avg * (1.0 - _ptp)
                    hit_ptp = (side == "LONG" and h[i] >= ptp) or (side == "SHORT" and l[i] <= ptp)
                    if hit_ptp and _pm.predict(np.asarray(
                            [_hold_feat_vec(A, sdir, avg, p["first_idx"], p["add_count"], i)]))[0] < _pgate:
                        lot = p["lots"].pop()                       # 1ロット部分決済（avg は不変＝残り平均そのまま・triggers 正しい）
                        _record_lots(trades, p, [lot], ptp, "PARTIAL_TP", i, ts)
                        p["size"] -= UNIT
                        events.append((pd.Timestamp(ts[i]), -UNIT))
                        p["partial_done"] = True
                # 中心 C へ戻り（C が建値±床を超える時だけ武装）＝勝ち延長アーム（即決済しない・この bar は保持・次 bar から延長判定）
                armed = np.isfinite(Cc[i]) and ((side == "LONG" and Cc[i] >= avg * (1.0 + COST_FLOOR)) or
                                                (side == "SHORT" and Cc[i] <= avg * (1.0 - COST_FLOOR)))
                hit_center = armed and ((side == "LONG" and h[i] >= Cc[i]) or (side == "SHORT" and l[i] <= Cc[i]))
                if hit_center:
                    p["extended"] = True                    # 延長アーム（中心到達＝最低限の利確圏・逆側端まで運ぶ）
                    continue
                if _hm is not None and np.isfinite(Cc[i]) and \
                        _hm.predict(np.asarray([_hold_feat_vec(A, sdir, avg, p["first_idx"], p["add_count"], i)]))[0] < _hth:
                    _record(trades, p, c[i], "ML_STANCH", i, ts)   # 保有中判定：中心Cに戻らない玉を早期撤退（成行 taker）
                    events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None
                    continue
                # iter4 建値撤退（損側・含み損玉のみ建値 maker 撤退・arm 次 bar から fire＝leak-safe・諦め抑制）
                mk = ee.MAKER_FEE
                bp = avg * (1.0 + mk) / (1.0 - mk) if side == "LONG" else avg * (1.0 - mk) / (1.0 + mk)
                if p["be_armed"] and ((side == "LONG" and h[i] >= bp) or (side == "SHORT" and l[i] <= bp)):
                    _record(trades, p, bp, "BE_EXIT", i, ts)       # 建値へ戻り＝損ゼロ maker 撤退（指値）
                    events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None
                else:
                    if (i - p["first_idx"]) >= BE_ARM_BARS and not p["be_armed"] and \
                            ((side == "LONG" and c[i] < bp) or (side == "SHORT" and c[i] > bp)) and \
                            (_bm is None or _bm.predict(np.asarray(
                                [_hold_feat_vec(A, sdir, avg, p["first_idx"], p["add_count"], i)]))[0] < _bth):
                        p["be_armed"] = True                        # 戻らない(predict<θ)含み損のみ武装・戻る玉は守る（iter5a be_gate）
                    if (i - p["first_idx"]) >= HOLD_5M:             # 時間切れ（成行 taker）
                        _record(trades, p, c[i], "TIME_EXIT", i, ts)
                        events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None
            else:
                # 延長中：逆側端到達=利確（maker 指値）→ 中心へ戻り=元TP益確保（taker stop）→ 時間切れ（taker）
                hit_edge = (side == "LONG" and np.isfinite(R[i]) and h[i] >= R[i]) or \
                           (side == "SHORT" and np.isfinite(S[i]) and l[i] <= S[i])
                if hit_edge:
                    _record(trades, p, R[i] if side == "LONG" else S[i], "EDGE_TP", i, ts)
                    events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None
                    continue
                back_center = np.isfinite(Cc[i]) and ((side == "LONG" and l[i] <= Cc[i]) or (side == "SHORT" and h[i] >= Cc[i]))
                if back_center:
                    _record(trades, p, Cc[i], "CENTER_LOCK", i, ts)   # 中心へ戻り＝元TP益を確保（保護 stop・成行 taker）
                    events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None
                elif (i - p["first_idx"]) >= HOLD_5M:       # 時間切れ（成行 taker）
                    _record(trades, p, c[i], "TIME_EXIT", i, ts)
                    events.append((pd.Timestamp(ts[i]), -p["size"])); pos[side] = None

        # ── 4. 入口/add（cap は fill 時に判定）──
        if long_sig[i] and pend["LONG"] is None and (pos["LONG"] is None or pos["LONG"]["add_count"] < max_adds):
            pend["LONG"] = {"limit": c[i] * (1.0 - ENTRY_OFFSET), "placed_idx": i}
        if short_sig[i] and pend["SHORT"] is None and (pos["SHORT"] is None or pos["SHORT"]["add_count"] < max_adds):
            pend["SHORT"] = {"limit": c[i] * (1.0 + ENTRY_OFFSET), "placed_idx": i}

    # ── 期間末 強制クローズ（成行）──
    for side in ("LONG", "SHORT"):
        if pos[side] is not None:
            _record(trades, pos[side], c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
            events.append((pd.Timestamp(ts[n - 1]), -pos[side]["size"]))
    return trades, events


def _verify_cap(trades) -> float:
    """出力 trades の区間会計（score.py.assert_position_cap と同式）で同時保有 max（LONG+SHORT 合算）を実測。
    fill 単位記録なので区間会計＝実保有。自己チェックを審判と一致させ false pass を防ぐ。"""
    ev = []
    for t in trades:
        sz = float(t["size_btc"])
        ev.append((pd.Timestamp(t["entry_time"]), sz))
        ev.append((pd.Timestamp(t["exit_time"]), -sz))
    ev.sort(key=lambda x: (x[0], x[1]))                   # 同時刻は決済(マイナス)を先に（score.py と同じ）
    cur = mx = 0.0
    for _t, s in ev:
        cur = round(cur + s, 9); mx = max(mx, cur)
    return mx


def _load(smoke: int) -> pd.DataFrame:
    df = pd.read_csv(e34v1.CSV)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df = df.reset_index(drop=True)
    if smoke:
        df = df.iloc[:smoke].reset_index(drop=True)
    df = e34v1.add_indicators(df)                 # sma/std/dev_z/atr/adx（taker は呼ばない）
    df = e34b.add_analysis_features(df)           # bb_mid_slope_pct/stoch 等
    df = e35_box.add_box_features(df, verify_leak=(smoke > 0 and smoke <= 60000))
    df = add_choppiness(df)
    df = add_jump_model(df)
    return df


def _attach_entry_cols(df: pd.DataFrame, box_tf: str) -> tuple:
    """指定 box_tf の入口系列（long_entry/short_entry）を df に付与し W 帯を返す。"""
    tr_mask = df.ts < TRAIN_END
    lo, hi, nW = _w_band(df, box_tf, tr_mask)
    sig = _build_signals_for_tf(df, box_tf, lo, hi)
    df["long_entry"] = sig["long_entry"].to_numpy()
    df["short_entry"] = sig["short_entry"].to_numpy()
    return lo, hi, nW, sig


def run_diagnostic(df: pd.DataFrame) -> None:
    """発火ファネル（採点しない・学習 ts<2025-01・補助）。Entry/Exit は一式で回す＝採点が本筋（§8.4）。"""
    tr_mask = df.ts < TRAIN_END
    tr_days = max((df.ts[tr_mask].max() - df.ts[tr_mask].min()).total_seconds() / 86400.0, 1.0)
    def cnt(m):
        return int((m & tr_mask).sum())
    print(f"\n  ── 発火ファネル（採点しない・学習 {df.ts[tr_mask].min().date()}〜{df.ts[tr_mask].max().date()}・{tr_days:.0f}日・補助）──")
    print(f"    {'段':<40}: " + "  ".join(f"{tf:>9}" for tf in TFS))
    bands = {tf: _w_band(df, tf, tr_mask) for tf in TFS}
    sig = {tf: _build_signals_for_tf(df, tf, bands[tf][0], bands[tf][1]) for tf in TFS}
    def row(label, key_expr):
        print(f"    {label:<40}: " + "  ".join(f"{cnt(key_expr(tf)):>9,}" for tf in TFS))
    row("RANGE_OK", lambda tf: sig[tf]["range_ok"])
    row("LONG_ENTRY", lambda tf: sig[tf]["long_entry"])
    row("SHORT_ENTRY", lambda tf: sig[tf]["short_entry"])
    print(f"    {'LONG+SHORT /日':<40}: " + "  ".join(
        f"{(cnt(sig[tf]['long_entry'])+cnt(sig[tf]['short_entry']))/tr_days:>9.2f}" for tf in TFS))


def _output_and_report(t: pd.DataFrame, suffix: str) -> None:
    """trades を 全期間/採点窓/precheck に分けて出力＋月別サマリ（main と run_hold_ml で共用）。"""
    RATCHET.mkdir(parents=True, exist_ok=True)
    base = RATCHET / f"trades_e35_oscillation{suffix}.csv"
    out_full = base
    out_train = base.with_name(base.stem + "_train.csv")
    out_score = base.with_name(base.stem + "_score.csv")
    t_full = t[t.entry_time < SEAL_START].reset_index(drop=True)
    t_score = t[(t.entry_time >= SC_START) & (t.entry_time < SCORE_END)].reset_index(drop=True)
    t_full.to_csv(out_full, index=False)
    t_score.to_csv(out_score, index=False)
    t[t.entry_time < TRAIN_END].reset_index(drop=True).to_csv(out_train, index=False)
    n_days = max((t_score.entry_time.max() - t_score.entry_time.min()).total_seconds() / 86400.0, 1.0) if len(t_score) else 1.0
    print(f"  [出力] 全期間 {out_full.name}（封印除外後 {len(t_full)}）/ 採点窓 {out_score.name}({len(t_score)}・{len(t_score)/n_days:.2f}/日) / precheck {out_train.name}")
    if len(t_score):
        sm = t_score.assign(m=t_score.entry_time.dt.strftime("%Y-%m")).groupby("m")["net_usd"].agg(["count", "sum"]).round(1)
        print("\n  採点窓 2025-06〜12 月別（CSV net・参考＝正式は score.py）:\n" + sm.to_string())
        print(f"  採点窓 合計 CSV net ${t_score.net_usd.sum():.1f} / 件 {len(t_score)} / 勝率 {(t_score.net_usd > 0).mean():.1%}")
        print(f"  出口別 件数: {dict(t_score['exit_reason'].value_counts())}")
    print("\n  → 判定は score.py（precheck → score.py の数字）:")
    print(f"     precheck.py {out_train.name} --authorize {out_score.name}")
    print(f"     score.py {out_score} --start 2025-06-01 --end 2025-12-31")


def run_be_gate(df: pd.DataFrame, box_tf: str, max_adds: int) -> None:
    """iteration-5(a) 諦め除外: hold-ML(保有中・戻る/戻らない判別)を建値撤退の武装ゲートに（KB §11・acceptance）。
    教師=建値撤退OFF(iter3基底)の玉・ラベル=中心到達系(TP_FILLED/EDGE_TP/CENTER_LOCK=戻る)=1 / TIME・箱ブレイク=0。
    戻ると判別(predict≥θ)した含み損玉は武装しない（守る）。ML_STANCH(成行で切る・iter2 で効かず)は使わない。
    θ=学習窓で『救い純増(be_gate net − iter4 ゲートなし net)』最大（採点窓不参照・ML使用＝固定値hook対象外）。"""
    import lightgbm as lgb   # python3.13 のみ
    global BE_ARM_BARS
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    _p1 = "shift(" + "-"; _p2 = "center" + "=True"   # 動的構築＝自分のソースに leak リテラルを残さず誤検出を防ぐ
    assert _p1 not in src and _p2 not in src, "leak 疑い（未来参照 shift/center）"
    A = _hold_arrays(df, box_tf)
    idx_of = {x: i for i, x in enumerate(df["ts"].tolist())}

    # ① 教師＝建値撤退OFF(iter3基底)の玉（建値撤退の挙動を学習に混ぜない＝循環回避）
    saved = BE_ARM_BARS
    BE_ARM_BARS = 10 ** 9                          # OFF＝iter3 基底（勝ち延長のみ・建値撤退なし）
    base_trades, _ = run_continuous(df, box_tf, max_adds)
    BE_ARM_BARS = saved
    bt = pd.DataFrame(base_trades)
    bt["entry_time"] = pd.to_datetime(bt["entry_time"]); bt["exit_time"] = pd.to_datetime(bt["exit_time"])
    print(f"  教師＝建値撤退OFF基底 {bt['position_id'].nunique()} 玉 / 出口 {dict(bt['exit_reason'].value_counts())}")

    # ② 保有中スナップ（ラベル=中心到達系=戻る=1）
    WIN = {"TP_FILLED", "EDGE_TP", "CENTER_LOCK"}
    rows = []
    for pid, g in bt.groupby("position_id"):
        g = g.sort_values("entry_time")
        lot_idx = [idx_of[x] for x in g["entry_time"]]; lot_px = g["entry_price"].astype(float).tolist()
        exit_idx = idx_of[g["exit_time"].iloc[0]]
        sdir = 1 if g["side"].iloc[0] == "LONG" else -1
        label = 1 if g["exit_reason"].iloc[0] in WIN else 0        # 中心到達系=戻る=1 / TIME・箱ブレイク=0
        first_idx = lot_idx[0]
        for i in range(first_idx + 1, exit_idx):
            filled = [(li, lp) for li, lp in zip(lot_idx, lot_px) if li <= i]
            if not filled or not (np.isfinite(A["Cc"][i]) and np.isfinite(A["atr"][i])):
                continue
            avg_i = sum(lp for _, lp in filled) / len(filled)
            rows.append([g["entry_time"].iloc[0], label] + _hold_feat_vec(A, sdir, avg_i, first_idx, len(filled), i))
    snaps = pd.DataFrame(rows, columns=["entry_time", "label"] + _HOLD_FEATS)
    tr = snaps[snaps.entry_time < TRAIN_END].reset_index(drop=True)        # H8 学習期間のみ
    print(f"  学習スナップ {len(tr):,} / 戻る率 {tr.label.mean():.3f}")

    # ③ 学習（学習期間のみ＝H8・特徴量は t 時点＝H2/leak grep 済）
    params = dict(n_estimators=300, num_leaves=15, min_child_samples=200, reg_alpha=1.0, reg_lambda=1.0,
                  learning_rate=0.03, random_state=42, verbose=-1)
    model = lgb.LGBMClassifier(**params); model.fit(tr[_HOLD_FEATS], tr["label"].to_numpy())
    booster = model.booster_
    fi = pd.Series(model.feature_importances_, index=_HOLD_FEATS).sort_values(ascending=False)
    atr_rank = list(fi.index).index("atr_pct") + 1
    print(f"  feature importance top8:\n{fi.head(8).to_string()}")
    print(f"  atr_pct 順位 {atr_rank}/{len(_HOLD_FEATS)}（上位独占でなければ H15 OK）")

    # ④ θ＝学習窓で救い純増（be_gate net − iter4 ゲートなし net）最大
    df_tr = df[df.ts < TRAIN_END].reset_index(drop=True)
    base4, _ = run_continuous(df_tr, box_tf, max_adds)                     # iter4（BE_ARM_BARS=12・ゲートなし）
    base4_net = float(pd.DataFrame(base4)["net_usd"].sum())
    print(f"  学習窓 iter4(ゲートなし) net ${base4_net:.0f}（救い純増の基準）")
    best_th, best_net = None, None
    for th in [0.30, 0.40, 0.50, 0.60, 0.70]:
        trq, _ = run_continuous(df_tr, box_tf, max_adds, be_gate=(booster, _HOLD_FEATS, th))
        q = pd.DataFrame(trq); net = float(q["net_usd"].sum()) if len(q) else 0.0
        be = int((q["exit_reason"] == "BE_EXIT").sum()) if len(q) else 0
        print(f"   θ={th}: 学習 net ${net:.0f}（救い純増 {net - base4_net:+.0f}）/ BE_EXIT {be}")
        if best_net is None or net > best_net:
            best_net, best_th = net, th
    gain = best_net - base4_net
    print(f"  → θ*={best_th}（救い純増 {gain:+.0f}）")
    if gain <= 0:
        print("  ⚠️ 救い純増がプラスでない＝学習窓で改善せず（採用せず・iter4 維持・(b)時間依存収縮へ）。")

    # ⑤ 全期間 再走（be_gate 適用）→ cap 検証 → 出力
    trades, _ = run_continuous(df, box_tf, max_adds, be_gate=(booster, _HOLD_FEATS, best_th))
    t = pd.DataFrame(trades); t["entry_time"] = pd.to_datetime(t["entry_time"])
    mx = _verify_cap(trades)
    print(f"  [cap 検証] 同時保有 max = {mx:.4f} BTC {'✅' if mx <= CAP + 1e-9 else '⛔超過'}（予算 {CAP}）")
    assert mx <= CAP + 1e-9, f"同時保有 {mx:.4f} > cap {CAP}"
    print(f"  約定 {len(t)} / 出口 {dict(t['exit_reason'].value_counts())} / θ*={best_th}")
    _output_and_report(t, f"_{box_tf}_iter5a")


def run_hold_ml(df: pd.DataFrame, box_tf: str, max_adds: int) -> None:
    """iteration-2 フェーズ2: 保有中判定 ML で中心Cに戻らない玉を早期撤退（学習する Exit・KB §11）。
    教師=基底 run_continuous の玉 → 保有中スナップ（学習期のみ）→ LightGBM → θ=学習net最大 → 全期間再走。"""
    import lightgbm as lgb   # python3.13 のみ（基底 e35 実行では import しない）
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    _p1 = "shift(" + "-"; _p2 = "center" + "=True"   # 動的構築＝自分のソースに leak リテラルを残さず誤検出を防ぐ
    assert _p1 not in src and _p2 not in src, "leak 疑い（未来参照 shift/center）"
    A = _hold_arrays(df, box_tf)
    idx_of = {x: i for i, x in enumerate(df["ts"].tolist())}

    # ① 教師＝基底の玉（早期撤退なし）
    base_trades, _ = run_continuous(df, box_tf, max_adds)
    bt = pd.DataFrame(base_trades)
    bt["entry_time"] = pd.to_datetime(bt["entry_time"]); bt["exit_time"] = pd.to_datetime(bt["exit_time"])
    print(f"  教師＝基底 {bt['position_id'].nunique()} 玉 / 出口 {dict(bt['exit_reason'].value_counts())}")

    # ② 保有中スナップ（玉の lot から avg 再構成・_hold_feat_vec で特徴・ラベル=最終 TP）
    rows = []
    for pid, g in bt.groupby("position_id"):
        g = g.sort_values("entry_time")
        lot_idx = [idx_of[x] for x in g["entry_time"]]; lot_px = g["entry_price"].astype(float).tolist()
        exit_idx = idx_of[g["exit_time"].iloc[0]]
        sdir = 1 if g["side"].iloc[0] == "LONG" else -1
        label = 1 if g["exit_reason"].iloc[0] == "TP_FILLED" else 0
        first_idx = lot_idx[0]
        for i in range(first_idx + 1, exit_idx):
            filled = [(li, lp) for li, lp in zip(lot_idx, lot_px) if li <= i]
            if not filled or not (np.isfinite(A["Cc"][i]) and np.isfinite(A["atr"][i])):
                continue
            avg_i = sum(lp for _, lp in filled) / len(filled)
            rows.append([g["entry_time"].iloc[0], label] + _hold_feat_vec(A, sdir, avg_i, first_idx, len(filled), i))
    snaps = pd.DataFrame(rows, columns=["entry_time", "label"] + _HOLD_FEATS)
    tr = snaps[snaps.entry_time < TRAIN_END].reset_index(drop=True)        # H8 学習期間のみ
    print(f"  学習スナップ {len(tr):,} / TP率 {tr.label.mean():.3f}")

    # ③ 学習（学習期間のみ＝H8・特徴量は t 時点＝H2/leak grep 済）
    params = dict(n_estimators=300, num_leaves=15, min_child_samples=200, reg_alpha=1.0, reg_lambda=1.0,
                  learning_rate=0.03, random_state=42, verbose=-1)
    model = lgb.LGBMClassifier(**params); model.fit(tr[_HOLD_FEATS], tr["label"].to_numpy())
    booster = model.booster_

    # ④ θ＝学習期間 net 最大（採点窓を見ない＝覗き見なし／ML 使用＝固定値 hook 対象外）
    df_tr = df[df.ts < TRAIN_END].reset_index(drop=True)
    best_th, best_net = None, None
    for th in [0.30, 0.40, 0.50, 0.60]:
        trq, _ = run_continuous(df_tr, box_tf, max_adds, hold_ctx=(booster, _HOLD_FEATS, th))
        q = pd.DataFrame(trq)
        net = float(q["net_usd"].sum()) if len(q) else 0.0
        npos = q["position_id"].nunique() if len(q) else 0
        stanch = int((q["exit_reason"] == "ML_STANCH").sum()) if len(q) else 0
        print(f"   θ={th}: 学習 net ${net:.0f} / 玉 {npos} / 早期撤退 {stanch}")
        if best_net is None or net > best_net:
            best_net, best_th = net, th
    print(f"  → θ*={best_th}（学習 net 最大 ${best_net:.0f}）")

    # ⑤ 全期間 再走（撤退適用）→ cap 検証 → 出力
    trades, _events = run_continuous(df, box_tf, max_adds, hold_ctx=(booster, _HOLD_FEATS, best_th))
    t = pd.DataFrame(trades); t["entry_time"] = pd.to_datetime(t["entry_time"])
    mx = _verify_cap(trades)
    print(f"  [cap 検証] 同時保有 max = {mx:.4f} BTC {'✅' if mx <= CAP + 1e-9 else '⛔超過'}（予算 {CAP}）")
    assert mx <= CAP + 1e-9, f"同時保有 {mx:.4f} > cap {CAP}"
    print(f"  約定 {len(t)} / 出口 {dict(t['exit_reason'].value_counts())} / θ*={best_th}")
    _output_and_report(t, f"_{box_tf}_holdml")


def run_partial_tp(df: pd.DataFrame, box_tf: str, max_adds: int) -> None:
    """iteration-6 賢いB: 死ぬ判別玉の前半含み益を1ロット maker 部分利確（be_gate booster 流用・iter5a の上に重畳・acceptance）。
    教師=建値撤退OFF(iter3基底)→booster（iter5a と同一手順）。be_th=0.40（iter5a 確定・a-priori 固定）。
    θ_gate × k_tp を学習窓『純増(partial − iter5a)』最大で選定（採点窓不参照・ML/学習窓選定=L-267対象外）。"""
    import lightgbm as lgb   # python3.13 のみ
    global BE_ARM_BARS
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    _p1 = "shift(" + "-"; _p2 = "center" + "=True"
    assert _p1 not in src and _p2 not in src, "leak 疑い（未来参照 shift/center）"
    A = _hold_arrays(df, box_tf)
    idx_of = {x: i for i, x in enumerate(df["ts"].tolist())}
    feats = _HOLD_FEATS; BE_TH = 0.40

    # ① 教師＝iter3基底（建値撤退OFF）→ booster（iter5a と同一手順）
    saved = BE_ARM_BARS; BE_ARM_BARS = 10 ** 9
    base_trades, _ = run_continuous(df, box_tf, max_adds)
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
    print(f"  教師(iter3基底) {bt['position_id'].nunique()} 玉 / 学習スナップ {len(tr):,} / 戻る率 {tr.label.mean():.3f}")

    # ② 自己検査(a) 恒等: θ_gate=-1（partial 不発火）で iter5a と net 一致
    df_tr = df[df.ts < TRAIN_END].reset_index(drop=True)
    base5a, _ = run_continuous(df_tr, box_tf, max_adds, be_gate=(booster, feats, BE_TH))
    base5a_net = float(pd.DataFrame(base5a)["net_usd"].sum())
    chk, _ = run_continuous(df_tr, box_tf, max_adds, be_gate=(booster, feats, BE_TH), partial_tp=(booster, feats, -1.0, 0.0015))
    chk_net = float(pd.DataFrame(chk)["net_usd"].sum())
    ok_a = abs(chk_net - base5a_net) < 1e-6
    print(f"  [自己検査a 恒等] θ_gate=-1(不発火) net ${chk_net:.2f} == iter5a ${base5a_net:.2f} : {'✅' if ok_a else '⛔不一致'}")
    assert ok_a, "partial 不発火が iter5a と不一致＝恒等崩れ"

    # ③ θ_gate × k_tp グリッド（学習窓 純増最大・採点窓不参照）
    base_edge = int((pd.DataFrame(base5a)["exit_reason"] == "EDGE_TP").sum())
    base_cen = int((pd.DataFrame(base5a)["exit_reason"] == "CENTER_LOCK").sum())
    print(f"  学習窓 iter5a(baseline) net ${base5a_net:.0f} / EDGE {base_edge} CENTER {base_cen}（純増の基準・be_th={BE_TH}）")
    best = None
    for tg in [0.30, 0.40, 0.50]:
        for k in [0.0010, 0.0015, 0.0020]:
            q, _ = run_continuous(df_tr, box_tf, max_adds, be_gate=(booster, feats, BE_TH), partial_tp=(booster, feats, tg, k))
            qd = pd.DataFrame(q); net = float(qd["net_usd"].sum())
            ptp = int((qd["exit_reason"] == "PARTIAL_TP").sum())
            edge = int((qd["exit_reason"] == "EDGE_TP").sum()); cen = int((qd["exit_reason"] == "CENTER_LOCK").sum())
            gain = net - base5a_net
            print(f"   θ_gate={tg} k_tp={k}: net ${net:.0f}（純増 {gain:+.0f}）/ PARTIAL_TP {ptp} / EDGE {edge} CENTER {cen}")
            if best is None or gain > best[0]:
                best = (gain, tg, k)
    gain, btg, bk = best
    print(f"  → θ_gate*={btg} k_tp*={bk}（学習窓 純増 {gain:+.0f}）")
    if gain <= 0:
        print("  ⚠️ 学習窓 純増がプラスでない＝採用せず（iter5a 維持）。次案へ（add1 は射程外＝別iter）。")

    # ④ 全期間 再走 → 自己検査(b)玉会計保存 → cap → 出力
    trades, _ = run_continuous(df, box_tf, max_adds, be_gate=(booster, feats, BE_TH), partial_tp=(booster, feats, btg, bk))
    t = pd.DataFrame(trades); t["entry_time"] = pd.to_datetime(t["entry_time"])
    rc = t.groupby("position_id").agg(nrows=("net_usd", "size"), addc=("add_count", "max"))
    bad = int((rc["nrows"] != rc["addc"]).sum())
    print(f"  [自己検査b 玉会計] 行数≠add_count の玉 {bad}（0=総ロット数保存 ✅）")
    assert bad == 0, "玉会計保存違反（部分+残りの行数が add 総数と不一致）"
    mx = _verify_cap(trades)
    print(f"  [自己検査c cap] 同時保有 max = {mx:.4f} BTC {'✅' if mx <= CAP + 1e-9 else '⛔超過'}（予算 {CAP}）")
    assert mx <= CAP + 1e-9, f"同時保有 {mx:.4f} > cap {CAP}"
    print(f"  約定 {len(t)} / 出口 {dict(t['exit_reason'].value_counts())} / θ_gate*={btg} k_tp*={bk}")
    _output_and_report(t, f"_{box_tf}_iter6")


def main():
    global BE_ARM_BARS
    ap = argparse.ArgumentParser()
    ap.add_argument("--box-tf", choices=TFS, default="5m", help="箱に使う足（連続モード・診断で比較→ここで選ぶ）")
    ap.add_argument("--max-adds", type=int, default=MAX_ADDS)
    ap.add_argument("--diagnostic", action="store_true", help="発火ファネル（採点しない・補助）。一式は採点が本筋")
    ap.add_argument("--smoke", type=int, default=0, help="先頭 N バーだけで動作確認")
    ap.add_argument("--hold-ml", action="store_true", help="保有中判定MLで早期撤退（iteration-2 フェーズ2・python3.13）")
    ap.add_argument("--be-arm-bars", type=int, default=BE_ARM_BARS, help="iter4 建値撤退 arm 本数（self-check: 大きくすると建値撤退OFF＝iter3 恒等）")
    ap.add_argument("--be-gate", action="store_true", help="iteration-5(a) 諦め除外: hold-ML を建値撤退の武装ゲートに（python3.13）")
    ap.add_argument("--partial-tp", action="store_true", help="iteration-6 賢いB: 死ぬ判別玉の前半含み益を1ロット maker 部分利確（iter5a 重畳・python3.13）")
    a = ap.parse_args()
    BE_ARM_BARS = a.be_arm_bars

    print("=" * 100)
    print(f"[E35 一式] レンジ上下オシレーション 連続モード両方向（box={a.box_tf}・merge・cap{CAP}合算・TP中心C/SL箱ブレイク/時間切れ）")
    df = _load(a.smoke)
    print(f"  価格 {e34v1.CSV.name}（{len(df):,}本・{df.ts.iloc[0].date()}〜{df.ts.iloc[-1].date()}）")
    print(f"  計器 maker {ee.MAKER_FEE} / taker {ee.TAKER_FEE} / slip {ee.SLIPPAGE} / funding {ee.FUNDING_RATE_8H}/8h / unit {UNIT}")

    if a.diagnostic:
        run_diagnostic(df)
        if not a.smoke:
            print("=" * 100); return

    # ── 入口系列を box_tf で付与 → 連続モード両方向 ──
    lo, hi, nW, _sig = _attach_entry_cols(df, a.box_tf)
    print(f"  box={a.box_tf} W正常帯[q{W_Q_LO},q{W_Q_HI}]=[{lo:.3f}%,{hi:.3f}%]（in_box 学習 {nW:,}本）/ "
          f"入口 CI>{CI_THRESH} & ADX<{ADX_MAX} & ゾーン≤{ZONE_FRAC}W & 反転(緩)%K<30↑/>70↓")
    print(f"  入口発火（全系列）: LONG {int(df['long_entry'].sum())} / SHORT {int(df['short_entry'].sum())}")

    if a.hold_ml:                                    # iteration-2 フェーズ2: 保有中判定 ML で早期撤退
        run_hold_ml(df, a.box_tf, a.max_adds); print("=" * 100); return

    if a.be_gate:                                    # iteration-5(a) 諦め除外: 建値撤退の武装ゲート
        run_be_gate(df, a.box_tf, a.max_adds); print("=" * 100); return

    if a.partial_tp:                                 # iteration-6 賢いB: 死ぬ判別玉の前半含み益を部分利確
        run_partial_tp(df, a.box_tf, a.max_adds); print("=" * 100); return

    trades, events = run_continuous(df, a.box_tf, a.max_adds)
    t = pd.DataFrame(trades)
    if len(t) == 0:
        print("  ⛔ 取引 0 件（入口が発火していない or 箱が立たない）。"); print("=" * 100); return
    t["entry_time"] = pd.to_datetime(t["entry_time"])

    mx = _verify_cap(trades)
    cap_ok = mx <= CAP + 1e-9
    print(f"  [cap 検証] 同時保有 max(LONG+SHORT) = {mx:.4f} BTC {'✅' if cap_ok else '⛔超過'}（予算 {CAP}）")
    assert cap_ok, f"同時保有 {mx:.4f} > cap {CAP}（add 停止バグ）"
    print(f"  約定 {len(t)}件 / side {dict(t['side'].value_counts())} / 出口 {dict(t['exit_reason'].value_counts())} "
          f"/ add分布 {dict(t['add_count'].value_counts().sort_index())}")

    # ── 出力（全期間=採点用 + 学習<2025-01=precheck 用・封印 2026-03+ 除外）──
    _output_and_report(t, f"_{a.box_tf}" + (f"_max{a.max_adds}" if a.max_adds != MAX_ADDS else ""))
    print("=" * 100)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""e34_levels.py — E34 iteration-3 レジサポ特徴量（成分B＝盲点情報・H6 価格非依存・leak-safe）

設計書: .claude/ratchet/e34_design.md §11.3（まこさん GO 2026-06-14・実装前プレゼン GO 済）。
位置付け（6軸ゲート §11.0 軸6）: primary=dwell（固定ルール・値動き系）が見ない「価格の節目（レジサポ）」を
  secondary（LightGBM）の盲点情報入力として足す。深い乖離でも強サポ直上なら反発／遠ければナイフ（§11.1 仮説）。

流用（新規ロジックを足さない・既存 leak 修正済を再利用）:
  - structure_features.compute_c1_features(df, N)（L-179 leak 修正済・phase_compliance §5.3 verify 済）
    ＝ support_distance_pct_N / resistance_distance_pct_N / nearest_level_distance_pct_N
      ＋ nearest_level_touch_count_N_t{thr}（4閾値・サポート/レジの強さ＝過去タッチ回数）。
    fractal は j バーピボットを j+2 で確定記録（_detect_fractals L44-67）＝未来参照なし。
    compute_c1_features の窓は [i-N+1, i+1]・touch_count も過去 N バーのみ＝leak なし。

新規追加（structure_features に未実装＝本ファイルで新規 leak assert を書く・§11.7(4)）:
  - volume_at_support … 直下サポート帯 ±tol の窓内出来高 ÷ 窓出来高（無次元＝出来高プロファイルの節・H6）。
    窓は [i-N+1, i]（★現バー i を含むが未来 i+1 以降は不参照）。
    ★leak 経路の懸念（reviewer note #4）: 「shift で当該足を含むなら i 終値確定後の量である」＝
      本実装は窓を l[i-N+1:i+1]（i を含む）で取るが、これは「バー i 確定後（5m close 時点）に
      過去 N バーの OHLCV が全部確定している」＝本番でバー確定後に推論する E34 と同契約（H2）。
      未来バー（i+1 以降）は一切参照しない（assert で物理担保）。

窓 N・タッチ許容バンドは a priori 単一固定（構造パラメータ・SMA期間と同格・スイープしない・hook L-267）:
  - N = 100（structure_features.N_CANDIDATES の中央値 100・C-1 既定の代表値）。
  - VOL_TOL = 0.005（0.5%＝structure_features.TOUCH_THRESHOLDS の中央値・サポート帯のバンド幅）。

H 制約照合（§11.5）:
  H2 leak  … fractal は j+2 確定・compute_c1 窓 [i-N+1,i+1]・volume_at_support 窓 [i-N+1,i]・未来不参照を assert。
  H6 価格非依存 … 全カラム %（距離）/ 回数（タッチ）/ 比（出来高シェア）。USD 絶対値の列を assert で禁止。
"""
from __future__ import annotations
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "regime"))
import structure_features as sf   # noqa: E402  C-1 レジサポ（L-179 leak 修正済・compute_c1_features L70-130）

# ── a priori 単一固定（構造パラメータ・スイープしない・hook L-267）──────────────────
LEVEL_N = 100        # src: structure_features.N_CANDIDATES=[50,100,200] の中央値（C-1 窓の代表）
VOL_TOL = 0.005      # src: structure_features.TOUCH_THRESHOLDS=[0.003,0.005,0.010,0.020] の中央（サポート帯バンド0.5%）

# 出力カラム（成分B＝レジサポ・C-1 から距離3＋強さ1（最良タッチ閾値 t050=0.5%）＋ volume_at_support）
SUPPORT_DIST = f"support_distance_pct_N{LEVEL_N}"
RESIST_DIST = f"resistance_distance_pct_N{LEVEL_N}"
NEAREST_DIST = f"nearest_level_distance_pct_N{LEVEL_N}"
TOUCH_T050 = f"nearest_level_touch_count_N{LEVEL_N}_t050"   # 0.5%バンドのタッチ回数（サポートの強さ）
VOL_AT_SUPPORT = "volume_at_support"

# secondary が使うレジサポ特徴の最終セット（§11.3 成分B）。
LEVEL_FEATS = [SUPPORT_DIST, RESIST_DIST, NEAREST_DIST, TOUCH_T050, VOL_AT_SUPPORT]


def _compute_volume_at_support(df: pd.DataFrame, support_level: np.ndarray, N: int, tol: float) -> np.ndarray:
    """volume_at_support[i] = 直下サポート価格 ±tol 帯に入る過去 N バーの出来高 ÷ 窓出来高（無次元・H6）。

    leak-safe: 窓は [i-N+1, i]（現バー i を含むが未来 i+1 以降は不参照）。
    サポートが無い（NaN）バーは NaN（後段 LightGBM は欠損を扱える）。
    """
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    v = df["volume"].to_numpy(float)
    rep = (h + l) / 2.0                                    # バー代表価格（structure_features._volume_profile_one と同流儀）
    n = len(df)
    out = np.full(n, np.nan)
    for i in range(N, n):
        lvl = support_level[i]
        if not np.isfinite(lvl):
            continue
        s = i - N + 1                                      # 窓 [i-N+1, i]（現バーまで・未来不参照）
        win_rep = rep[s:i + 1]
        win_v = v[s:i + 1]
        tot = win_v.sum()
        if tot <= 0:
            continue
        band = abs(lvl) * tol
        in_band = (win_rep >= lvl - band) & (win_rep <= lvl + band)
        out[i] = float(win_v[in_band].sum() / tot)        # 出来高シェア（0〜1・無次元）
    return out


def _assert_no_future_volume_leak(df: pd.DataFrame, support_level: np.ndarray) -> None:
    """新規列 volume_at_support の leak を物理 verify（reviewer note #4・既存 compute_c1 とは別に新規に書く）。

    検査: ランダムな複数 i について、価格・出来高の i+1 以降を破壊した df' でも volume_at_support[i] が不変＝
          未来バーを参照していない（参照していれば値が変わる）。
    """
    rng = np.random.default_rng(0)
    n = len(df)
    base = _compute_volume_at_support(df, support_level, LEVEL_N, VOL_TOL)
    # i+1 以降を破壊（10倍に膨らませる）した df' で再計算
    df2 = df.copy()
    df2["high"] = df2["high"].to_numpy(float)
    df2["low"] = df2["low"].to_numpy(float)
    df2["volume"] = df2["volume"].to_numpy(float)
    # サポートが立っている（base が有限な）バーを対象に検査
    cand = np.where(np.isfinite(base))[0]
    cand = cand[(cand > LEVEL_N + 5) & (cand < n - 10)]
    if len(cand) == 0:
        return
    test_idx = rng.choice(cand, size=min(20, len(cand)), replace=False)
    for i in test_idx:
        d3 = df.copy()
        hh = d3["high"].to_numpy(float); ll = d3["low"].to_numpy(float); vv = d3["volume"].to_numpy(float)
        hh[i + 1:] = hh[i + 1:] * 10.0 + 1e6              # 未来バーを破壊
        ll[i + 1:] = ll[i + 1:] * 10.0 + 1e6
        vv[i + 1:] = vv[i + 1:] * 10.0 + 1e6
        d3["high"] = hh; d3["low"] = ll; d3["volume"] = vv
        re = _compute_volume_at_support(d3, support_level, LEVEL_N, VOL_TOL)
        if not (np.isnan(base[i]) and np.isnan(re[i])):
            assert abs(base[i] - re[i]) < 1e-12, (
                f"H2 leak: volume_at_support[{i}] が未来バー破壊で変化 "
                f"({base[i]} -> {re[i]})＝未来参照あり")


def _assert_price_independent(out: pd.DataFrame) -> None:
    """H6: 全カラムが価格非依存（%/回数/比）であることを assert（USD 絶対値の混入を物理禁止）。

    距離(%)・タッチ(回数・整数〜N)・出来高シェア(0〜1) はいずれも BTC 価格絶対値に依存しない。
    値域チェックで USD 絶対値（数千〜数十万）の混入を検出する。
    """
    for col in out.columns:
        s = out[col].dropna()
        if len(s) == 0:
            continue
        mx = float(s.abs().max())
        if col == VOL_AT_SUPPORT:
            assert s.min() >= -1e-9 and s.max() <= 1.0 + 1e-9, f"H6: {col} は出来高比(0〜1)のはず: [{s.min()},{s.max()}]"
        elif col.startswith("nearest_level_touch_count"):
            assert mx <= LEVEL_N + 1, f"H6: {col} はタッチ回数(≤N)のはず: max {mx}"
        else:  # *_distance_pct_N… ＝ % 距離（数十%まで・USD絶対値は数千以上で弾く）
            assert mx < 1000.0, f"H6: {col} は%距離のはず（USD絶対値疑い）: max {mx}"


def add_level_features(df: pd.DataFrame, N: int = LEVEL_N, tol: float = VOL_TOL) -> pd.DataFrame:
    """df（OHLCV＋既存指標）に成分B（レジサポ）を付与して返す。leak/価格非依存を内部 assert で物理担保。

    必要列: high / low / close / volume（OHLCV）。compute_c1_features は high/low/close を使う。
    """
    # ── C-1（流用・L-179 leak 修正済）: 距離 + タッチ回数 ──────────────────────────
    c1 = sf.compute_c1_features(df, N)
    # 直下サポート価格を再構成（compute_c1 の sup_dist から復元: sup = close /(1 + sup_dist/100)）
    close = df["close"].to_numpy(float)
    sup_dist = c1[f"support_distance_pct_N{N}"].to_numpy(float)
    support_level = close / (1.0 + sup_dist / 100.0)        # sup_dist=(close−sup)/close×100 の逆算（サポート無しは NaN）

    # ── volume_at_support（新規・leak assert を新規に書く・§11.7(4)）─────────────
    _assert_no_future_volume_leak(df, support_level)        # ★新規列の未来参照を物理 verify
    vol_at_sup = _compute_volume_at_support(df, support_level, N, tol)

    out = pd.DataFrame(index=df.index)
    out[SUPPORT_DIST] = c1[f"support_distance_pct_N{N}"]
    out[RESIST_DIST] = c1[f"resistance_distance_pct_N{N}"]
    out[NEAREST_DIST] = c1[f"nearest_level_distance_pct_N{N}"]
    out[TOUCH_T050] = c1[f"nearest_level_touch_count_N{N}_t050"]
    out[VOL_AT_SUPPORT] = vol_at_sup

    _assert_price_independent(out)                          # ★H6 価格非依存（USD 絶対値の混入禁止）
    for col in LEVEL_FEATS:
        df[col] = out[col].to_numpy()
    return df


if __name__ == "__main__":
    # スモーク: 正本 5m で leak/価格非依存 assert が通り、サポートが立つ件数を表示。
    import e34_range_zscore_taker as e34v1   # noqa: E402
    print("[e34_levels smoke] N=%d tol=%.3f" % (LEVEL_N, VOL_TOL))
    d = pd.read_csv(e34v1.CSV)
    d["ts"] = pd.to_datetime(d["timestamp"])
    d = d.iloc[:20000].reset_index(drop=True)
    d = add_level_features(d)
    for col in LEVEL_FEATS:
        s = d[col].dropna()
        print(f"  {col}: 有効 {len(s):,} / range [{s.min():.4f}, {s.max():.4f}]")
    print("  ✅ leak assert / H6 価格非依存 assert PASS")

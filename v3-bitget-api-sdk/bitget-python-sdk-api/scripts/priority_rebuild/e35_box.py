#!/usr/bin/env python3
"""e35_box.py — E35 レンジ上下オシレーション「箱」定義（下限S・上限R を 5m/1h/4h で別々に作り 5m に整列）

設計書: .claude/ratchet/e35_design.md（Peterson hypothesis-driven・deep-research baseup・まこさん GO）。
スコープ（今回）: 箱の「特徴量」だけ（売買ループ・部分決済・箱ブレイクSL・採点 score.py は別段）。

何を作るか:
  3 つの足 5m/1h/4h で別々に箱（=現値の下に直近フラクタル安値 S・上に直近フラクタル高値 R）を作り、
  全部 5m に整列して返す。**決め打ち合議はしない**（どの足が良いかは診断 e35_range_oscillation.py で比較する）。

流用（新規ロジックを足さない・関数シグネチャは実体 Read 済 2026-06-14）:
  - structure_features.compute_c1_features(df, N)（L-179 leak 修正済・fractal j+2 確定）
    ＝ support_distance_pct_N{N} / resistance_distance_pct_N{N}（現値からの距離%・H6）。
  - build_labels_pct.resample_ohlcv(df5m, rule) / attach_upper_tf(base, feat_upper, tf)
    ＝ 上位足を「足が閉じた時刻=index+freq」で merge_asof backward に貼る（leak-safe・L-128 修正済）。
  - e34_levels._compute_volume_at_support（出来高プロファイルの濃さ＝箱の強さ・窓[i-N+1,i]・未来不参照）。

出力列（全 tf・全て価格非依存＝距離%・比 0〜1・H6）:
  box_sup_dist__{tf}  … 現値より下の直近フラクタル安値までの距離%（compute_c1 の support_distance）
  box_res_dist__{tf}  … 現値より上の直近フラクタル高値までの距離%（compute_c1 の resistance_distance）
  box_strength__{tf}  … サポート帯 ±tol の窓内出来高シェア（volume_at_support・0〜1・上位足は当該足で計算し貼る）

H 制約（コード内 assert / コメントで物理担保）:
  H2 leak  … fractal j+2 確定（_detect_fractals 既存）/ 上位足は attach_upper_tf(+freq・merge_asof backward)
              / box 列は「i+1 以降の OHLCV を破壊しても box_*[i] が不変」をランダム複数 i で物理 verify。
  H6 価格非依存 … 全 box 列が 距離%(絶対値<1000) / 比(0〜1)。USD 絶対値の列を作らない（assert で禁止）。
  L-267 固定値手調整禁止 … BOX_N=100 は a priori 単一固定（N_CANDIDATES の中央 100）・スイープしない。
"""
from __future__ import annotations
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "regime"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import structure_features as sf            # noqa: E402  C-1 レジサポ（compute_c1_features・fractal j+2 leak-safe）
import build_labels_pct as bl              # noqa: E402  resample_ohlcv / attach_upper_tf / FREQ_TD（上位足 leak-safe attach）
import e34_levels as lv                    # noqa: E402  _compute_volume_at_support（出来高シェア・窓[i-N+1,i]・leak assert 済）

# ── a priori 単一固定（構造パラメータ・SMA 期間と同格・最良値スイープしない・hook L-267）──────
BOX_N = 100              # src: structure_features.N_CANDIDATES=[50,100,200] の中央値（C-1 窓の代表）
BOX_VOL_TOL = lv.VOL_TOL  # 0.005（0.5%・サポート帯バンド幅・e34_levels と同一・流用）

# 箱を作る足（決め打ち合議しない＝3 足を診断で比較するため全部出す）。文字列リスト＝L-267 数値スイープに非該当。
TFS = ['5m', '1h', '4h']
# resample 規則（build_labels_pct.RESAMPLE_RULE の流儀に合わせる: '1h'→'1h' / '4h'→'4h'）
RESAMPLE_RULE = {'1h': bl.RESAMPLE_RULE['1h'], '4h': bl.RESAMPLE_RULE['4h']}

# 出力カラム名（tf 別）
def sup_col(tf: str) -> str: return f"box_sup_dist__{tf}"
def res_col(tf: str) -> str: return f"box_res_dist__{tf}"
def strength_col(tf: str) -> str: return f"box_strength__{tf}"

BOX_COLS = [f(tf) for tf in TFS for f in (sup_col, res_col, strength_col)]


def _box_one_tf_native(df_tf: pd.DataFrame) -> pd.DataFrame:
    """1 足分（5m そのもの or 上位足 resample 後）の箱 3 列を、その足の index で計算して返す。

    sup/res は compute_c1_features の距離%。strength は volume_at_support（その足の OHLCV で計算）。
    全て当該足 [i-N+1, i+1)（fractal は j+2 確定）までで確定＝未来不参照（attach 前の段階で leak-safe）。
    必要列: high / low / close / volume。
    """
    c1 = sf.compute_c1_features(df_tf, BOX_N)             # 距離%（fractal j+2 確定・窓[i-N+1,i+1]・leak-safe）
    sup_dist = c1[f"support_distance_pct_N{BOX_N}"].to_numpy(float)
    res_dist = c1[f"resistance_distance_pct_N{BOX_N}"].to_numpy(float)
    close = df_tf["close"].to_numpy(float)
    # サポート価格を距離%から復元（sup = close/(1+sup_dist/100)・サポート無し=NaN）→ 出来高シェア（窓[i-N+1,i]・未来不参照）
    support_level = close / (1.0 + sup_dist / 100.0)
    lv._assert_no_future_volume_leak(df_tf, support_level)  # ★volume_at_support の未来参照を物理 verify（流用 assert）
    strength = lv._compute_volume_at_support(df_tf, support_level, BOX_N, BOX_VOL_TOL)

    out = pd.DataFrame(index=df_tf.index)
    out["__sup"] = sup_dist
    out["__res"] = res_dist
    out["__strength"] = strength
    return out


def _assert_no_future_box_leak(df5m_idx: pd.DataFrame, tf: str, base_cols: dict) -> None:
    """新規 box 列（当該 tf）の leak を物理 verify（e34_levels._assert_no_future_volume_leak と同型・新規に書く）。

    検査: ランダムな複数 i について、5m の OHLCV を i+1 以降だけ破壊した df' で box_*__tf を再計算し、
          box_*__tf[i] が不変であること（変われば未来参照＝H2 違反で停止）。
    上位足列もこの 5m 起点の破壊で同時に verify する（resample/attach の +freq シフト漏れをここで殺す）。
    df5m_idx は DatetimeIndex（'timestamp'）を持つ 5m OHLCV。base_cols は破壊前に計算した {col: np.ndarray}。
    """
    rng = np.random.default_rng(0)
    n = len(df5m_idx)
    cols = [sup_col(tf), res_col(tf), strength_col(tf)]
    base = {col: base_cols[col] for col in cols}
    # 当該 tf で「箱が立っている」（sup or res が有限な）バーを検査対象にする
    sup_b = base[sup_col(tf)]
    res_b = base[res_col(tf)]
    finite = np.where(np.isfinite(sup_b) | np.isfinite(res_b))[0]
    # 暖機（上位足 N 本ぶん 5m に換算しても十分に過ぎた）かつ末尾から離れたバーに限る
    margin = BOX_N * 48 + 50      # 4h=48本/5m 換算 × N + 余裕（破壊点を作れる範囲）
    finite = finite[(finite > margin) & (finite < n - 50)]
    if len(finite) == 0:
        return
    test_idx = rng.choice(finite, size=min(8, len(finite)), replace=False)
    for i in test_idx:
        d = df5m_idx.copy()
        hh = d["high"].to_numpy(float); ll = d["low"].to_numpy(float)
        cc = d["close"].to_numpy(float); vv = d["volume"].to_numpy(float)
        hh[i + 1:] = hh[i + 1:] * 10.0 + 1e6     # ★未来バー（i+1 以降）だけ破壊
        ll[i + 1:] = ll[i + 1:] * 10.0 + 1e6
        cc[i + 1:] = cc[i + 1:] * 10.0 + 1e6
        vv[i + 1:] = vv[i + 1:] * 10.0 + 1e6
        d["high"] = hh; d["low"] = ll; d["close"] = cc; d["volume"] = vv
        re_cols = _build_one_tf_on_5m(d, tf)      # 同じ経路（5m直 or resample→c1→attach）で再計算
        for col in cols:
            b = base[col][i]
            r = re_cols[col].to_numpy(float)[i]
            if np.isnan(b) and np.isnan(r):
                continue
            assert abs(b - r) < 1e-9, (
                f"H2 leak: {col}[{i}] が未来バー破壊で変化 ({b} -> {r})＝未来参照あり（tf={tf}）")


def _build_one_tf_on_5m(df5m_idx: pd.DataFrame, tf: str) -> dict:
    """5m（DatetimeIndex='timestamp'・OHLCV）から 1 足分の box 3 列を 5m に整列して返す（{col: pd.Series}）。

    5m: その足で直接 compute_c1 + volume_at_support。
    1h/4h: resample_ohlcv → その足で box 計算 → attach_upper_tf（+freq・merge_asof backward）で 5m に貼る。
           ★ここが leak の山＝必ず attach_upper_tf を通す（自前 reindex で前方に漏らさない・H2）。
    """
    if tf == '5m':
        b = _box_one_tf_native(df5m_idx)
        return {
            sup_col(tf): b["__sup"].reindex(df5m_idx.index),
            res_col(tf): b["__res"].reindex(df5m_idx.index),
            strength_col(tf): b["__strength"].reindex(df5m_idx.index),
        }
    # 上位足: resample → box 計算（その足の OHLCV で）→ attach（leak-safe）
    df_tf = bl.resample_ohlcv(df5m_idx, RESAMPLE_RULE[tf])
    b_tf = _box_one_tf_native(df_tf)
    b_tf = b_tf.rename(columns={"__sup": sup_col(tf), "__res": res_col(tf), "__strength": strength_col(tf)})
    base5 = df5m_idx[["close"]].copy()                    # attach のキャリア（close は使わず index 整列のみ）
    merged = bl.attach_upper_tf(base5, b_tf, tf)          # ★+freq シフト + merge_asof backward（L-128 修正済）
    return {
        sup_col(tf): merged[sup_col(tf)],
        res_col(tf): merged[res_col(tf)],
        strength_col(tf): merged[strength_col(tf)],
    }


def _assert_price_independent(df: pd.DataFrame) -> None:
    """H6: 全 box 列が価格非依存（距離% は絶対値<1000・strength は比 0〜1）であることを assert。

    距離% は USD 絶対値（数千〜数十万）なら弾く。strength は出来高シェアなので [0,1]。
    """
    for tf in TFS:
        for col in (sup_col(tf), res_col(tf)):
            s = df[col].dropna()
            if len(s) == 0:
                continue
            mx = float(s.abs().max())
            assert mx < 1000.0, f"H6: {col} は%距離のはず（USD 絶対値疑い）: max {mx}"
        s = df[strength_col(tf)].dropna()
        if len(s) > 0:
            assert s.min() >= -1e-9 and s.max() <= 1.0 + 1e-9, \
                f"H6: {strength_col(tf)} は出来高比(0〜1)のはず: [{s.min()},{s.max()}]"


def add_box_features(df: pd.DataFrame, verify_leak: bool = True) -> pd.DataFrame:
    """df（e34 系・'ts' 列 + OHLCV）に 3 足（5m/1h/4h）の箱 9 列を付与して返す。

    付与列: box_sup_dist__{tf} / box_res_dist__{tf} / box_strength__{tf}（tf=5m,1h,4h）。
    leak/価格非依存は内部 assert で物理担保（verify_leak=False で leak 破壊テストのみ省略＝大規模時の時短用）。

    必要列: ts（or timestamp）/ open / high / low / close / volume。
    """
    # ── 5m を DatetimeIndex('timestamp') 化（resample / attach が index ベースで動くため）──────
    ts = df["ts"] if "ts" in df.columns else pd.to_datetime(df["timestamp"])
    df5m_idx = (df[["open", "high", "low", "close", "volume"]]
                .copy()
                .set_axis(pd.DatetimeIndex(pd.to_datetime(ts), name="timestamp")))

    built = {}
    for tf in TFS:
        cols = _build_one_tf_on_5m(df5m_idx, tf)
        built.update(cols)
        if verify_leak:
            base_cols = {k: v.to_numpy(float) for k, v in cols.items()}
            _assert_no_future_box_leak(df5m_idx, tf, base_cols)   # ★新規 box 列の未来参照を物理 verify

    # ── 元 df の行順（RangeIndex）に貼り戻す（5m と 1:1・整列は timestamp 経由で担保）──────────
    out = df.copy()
    for col in BOX_COLS:
        out[col] = built[col].to_numpy()
    _assert_price_independent(out)                                # ★H6 価格非依存（USD 絶対値の混入禁止）
    return out


if __name__ == "__main__":
    # スモーク: 正本 5m の先頭 2 万本で leak/H6 assert PASS と各 box 列の有効件数を print。
    import e34_range_zscore_taker as e34v1   # noqa: E402  CSV パス（正本 5m）
    print(f"[e35_box smoke] BOX_N={BOX_N} tol={BOX_VOL_TOL} tfs={TFS}")
    d = pd.read_csv(e34v1.CSV)
    d["ts"] = pd.to_datetime(d["timestamp"])
    d = d.iloc[:20000].reset_index(drop=True)
    print(f"  入力 {len(d):,} 本（{d.ts.iloc[0]} 〜 {d.ts.iloc[-1]}）")
    d = add_box_features(d, verify_leak=True)
    for tf in TFS:
        for col in (sup_col(tf), res_col(tf), strength_col(tf)):
            s = d[col].dropna()
            if len(s):
                print(f"  {col:<22}: 有効 {len(s):>6,} / range [{s.min():.4f}, {s.max():.4f}]")
            else:
                print(f"  {col:<22}: 有効 0（暖機域不足の可能性・本走では全期間で立つ）")
    print("  ✅ leak 破壊テスト（未来 i+1 破壊で box 不変）/ H6 価格非依存 assert PASS")

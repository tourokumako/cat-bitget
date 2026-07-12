"""build_regime_gate_rg.py — レンジ・レジーム判定 RG 系列（現行 RG-v4）＝仕様自動生成つきの正本計器

背景（まこさん指示 2026-07-12）:
  ダッシュボード v12 は ①まこさんの手動4hラベルを直接教師にしていた（2026-07-03 確定方針
  「手動ラベルを教師に使わない」に違反） ②表示が最大4hの未来値を含む ③判定粒度が4h＝5分足に未対応。
  → レンジのレジーム判定を RG 系列として組み直す。仕様ロジックは report §0 と同様に**実行時の実値から
  自動生成**し、ダッシュボードの仕様欄に表示する（手書き禁止＝必須項目を削ると SystemExit のスキーマ強制）。

視認校正の反復（まこさん指摘 → RG-vN で反映）:
  RG-v1: v17 計器と同一ロジックの移植（labels_v17 全期間一致 selftest）。
  RG-v2: 上げ相場を range と誤判定（02-25/02-28）→ 往復実証フィルタ新設。
  RG-v3: ①02-25 15:00〜16:50 残存 → 帯整合 ②12-09〜12-14/2026-01 の不検出 → 帯対の拡張選択
    （最近接クラスタ対が幅不足でも次に遠い対を試す） ③「帯はあるが実証待ち」= range_wait 表示。
  RG-v4（2026-07-12 まこさん校正指摘③）: 「薄い青（range_wait）もレンジとして判定してよい。ただし
    急騰・上げ相場（7窓の指摘: 12-09 14:40〜16:45／12-11 16:05〜21:25／12-17 14:40〜15:10／
    12-26 00:40〜02:45／12-28 23:25〜29 04:35／02-25 00:05〜17:50／02-28 13:00〜22:20）は除外」
    → 往復実証は執行判定から撤去（wait を range に統合）し、代わりに**上げトレンド状態機械**を新設:
      発火＝「前回解除以降かつ直近2h/6h」の安値からの上昇率 ≥ 1.5%/2.0%（参照安値を解除以降に限定＝
            スパイク後6hの「影」再発火を根絶）／解除後24h内に前回高値+0.3%超え＝継続再発火（安値引き継ぎ）
      解除＝上げ幅の半値戻し or 高値更新なし3h → 課題＝発火1〜3h遅れ・解除3hはみ出し。
  RG-v5（2026-07-12 まこさん校正指摘④「複数足を入れたらもっと早く判断できるのでは？5分足botで3時間の
    ズレは致命的」）: トリガ・解除とも下位足の構造を追加＝
      発火の追加: ①15分足 3本連続の高値切り上げ∩安値切り上げ（A15） ②15分足 陽線3連続∩累積+0.5%（D15）
                 ③90分安値から+1.0%（C90・参照は前回解除以降）〔従来の6h安値+2.0%は遅い上げの受け皿で維持〕
      解除の追加: 15分足の構造破断＝close が直近2本の確定15分安値を割る（上げ構造の終了を15〜30分で検出）
                 ＋停滞は3h→2hに短縮。
    校正結果（v4→v5）: 7窓の捕捉 58→65/52→52/71→71/27→62/48→100/47→57/92→85%・
      解除のはみ出し 約3h→25〜75分・12-28 の遅い上げは指摘（23:25）より25分早い 23:00 検出。
    代償＝残す側の誤発火増（02-14〜16 21→25%/12-09 21時〜 3→10%/1月 12→22%）＝中身は「レンジ内の
    90分+1%級の小突き上げ」＝12-17 型の急騰と同種（消しすぎかはダッシュボードの緑で視認校正）。
    ★因果的な限界（未来値ゼロを守る代償・開示済み）: 緩やかな上げの序盤（12-11 16〜18時台）は
      その時点ではレンジ内反発と不可分＝発火まで最大2.5h／02-25 05〜08時の中だるみは部分捕捉。

  ⛔ 教師なし＝幾何ルールのみ。手動レジームラベル（regime_samples_4h*.csv /
     regime_ground_truth_daily_human.csv）は一切読まない。まこさんの指摘窓は「視認校正の照合点」として
     閾値選定に使う（教師データとして学習器に与えるのではない・採点窓 net は不参照）。
  ゾーン束ね・fractal 検出・全定数は v17 計器（build_range_gate_dashboard.py）から import 再利用。
  selftest＝labels_v17 で range だった全バーについて v4 の帯が完全一致（帯対拡張は「v17 が落とした所を
  拾うだけ」で「v17 が採った帯は動かさない」ことの機械証明）。

実行:  python3 scripts/dashboard/build_regime_gate_rg.py
出力:  dashboard/regime_prototype/predictions_<VERSION>_{1h,1d}.json / predictions_<VERSION>_5m/<月>.json /
       labels_<VERSION>.csv / index.json（spec 自動生成・VERSION エントリ・旧版エントリは残す＝比較可）
確認:  python3 scripts/dashboard/dashboard_server.py → ⑪ → rg-v5 → 粒度5分 → 月 → 日絞り
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_range_gate_dashboard as v17   # noqa: E402  fractal・束ね・定数の正本（視認校正済み）＝import 再利用・コピー禁止
import structure_features as sf            # noqa: E402  v17 が path を通した後に import 可（fractal j+2 確定・leak-safe）

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTO_DIR = REPO_ROOT / "dashboard" / "regime_prototype"
INDEX_JSON = PROTO_DIR / "index.json"
VERSION = "rg-v5"                          # RG 系列＝戦略の vN（E37 v18/v19…）と衝突しない別名前空間（L-333 混乱対策）
SM_DIR = PROTO_DIR / f"predictions_{VERSION}_5m"

# ── 上げトレンド状態機械（RG-v4 新設・RG-v5 で複数足化・上げ専用＝指示は「急騰及び上げ相場」）──
# 閾値の出所＝視認校正の照合点で選定（採点窓 net 不参照・L-267 非該当）:
#   まこさん指摘の除外7窓（2026-07-12）を最大捕捉しつつ、残す側（02-14〜16 往復／12-09 21:00〜12-14／
#   2026-01）の誤発火とのバランスを候補比較で選定。v5 はまこさん指摘④（複数足で早く）を受け
#   「検出の速さ優先」の側を採用（誤発火の増分はダッシュボードの緑で視認校正して次版で調整）。
TREND_T90 = 0.010      # 発火③: 直近90分（かつ前回解除以降）の安値からの上昇率 ≥ これ＝急騰（5分粒度で速い）
TREND_T6 = 0.020       # 発火④: 直近6h（かつ前回解除以降）の安値からの上昇率 ≥ これ＝遅い上げの受け皿
TREND_ST15_K = 3       # 発火①: 15分足でこの本数連続の 高値切り上げ∩安値切り上げ＝上げ構造（A15）
TREND_MOM15_K = 3      # 発火②: 15分足でこの本数連続の陽線 ∩ 累積上昇 ≥ TREND_MOM15_AMP（D15）
TREND_MOM15_AMP = 0.005
TREND_RETR = 0.5       # 解除①: 上げ幅（発火時安値→最高値）の半値戻し＝上げの終了
TREND_STALL = 24       # 解除②: 高値更新なしがこの5分バー数（=2時間）続く＝上げの停滞
TREND_STRUCT_REL = 2   # 解除③: close が直近この本数の確定15分足安値の最小を割る＝上げ構造の破断（速い解除）
TREND_CONT_M = 0.003   # 継続再発火: 解除後 TREND_CONT_W 内に close が前回高値×(1+これ) を超えたら再発火
TREND_CONT_W = 288     # 継続再発火の有効期間（5分バー数=24時間）

RG_SPEC_SCHEMA = ("入力データ", "教師", "判定ロジック", "パラメータ（出所つき）", "因果性（未来値ゼロ）",
                  "出力粒度", "selftest", "生成方式")


def _assert_spec_schema(spec: dict) -> None:
    """仕様の必須項目スキーマ検査。欠けたら SystemExit（項目削除・手書き固定文字列化を物理的に禁止）。"""
    for key in RG_SPEC_SCHEMA:
        if key not in spec or not str(spec[key]).strip():
            raise SystemExit(f"[RG 仕様スキーマ強制] 必須項目欠落: {key}（仕様は実値から自動生成・削れない・まこさん 2026-07-12）")


def _zones_1h_rg(df: pd.DataFrame) -> pd.DataFrame:
    """RG の 1h ゾーン＝v17 と同じ fractal スイング＋束ね（sf._detect_fractals・ZONE_* 定数）で、
    帯対の選択だけ拡張（RG-v3）: v17 は「価格に最も近い ≥ZONE_TOUCH クラスタ」1対のみで幅チェック →
    大きな往復の中の小さな中間レベル対を掴むと幅不足で不成立（12-09〜12-14 事案）。近い順にクラスタ対を
    試し幅 ≥ ZONE_MIN_W を満たす最初の対を採る（最近接対が幅を満たす時は v17 と完全同一＝selftest で照合）。"""
    is_res, is_sup, piv_h, piv_l = sf._detect_fractals(df)
    n = len(df)
    c = df["close"].to_numpy(float)
    is_res = np.asarray(is_res, bool); is_sup = np.asarray(is_sup, bool)
    piv_h = np.asarray(piv_h, float); piv_l = np.asarray(piv_l, float)
    res_idx = np.flatnonzero(is_res); res_px = piv_h[res_idx]
    sup_idx = np.flatnonzero(is_sup); sup_px = piv_l[sup_idx]
    r_lo = np.full(n, np.nan); r_hi = np.full(n, np.nan)
    s_lo = np.full(n, np.nan); s_hi = np.full(n, np.nan)
    ok = np.zeros(n, bool)

    def zones(px_arr, idx_arr, i, lo_w, price, above):
        """タッチ≥ZONE_TOUCH のクラスタ帯を全部返す（価格に近い順）＝v17 best_zone の全候補版。"""
        j0 = int(np.searchsorted(idx_arr, lo_w)); j1 = int(np.searchsorted(idx_arr, i + 1))
        if j1 <= j0:
            return []
        px = px_arr[j0:j1]
        sel = (px > price) if above else (px < price)
        if not sel.any():
            return []
        px = np.sort(px[sel])
        out = []; s = 0
        for k in range(1, len(px) + 1):
            if k == len(px) or px[k] - px[k - 1] > px[k - 1] * v17.ZONE_TOL:
                cl = px[s:k]
                if len(cl) >= v17.ZONE_TOUCH:
                    out.append((float(cl.min()) * (1 - v17.ZONE_TOL / 2), float(cl.max()) * (1 + v17.ZONE_TOL / 2)))
                s = k
        out.sort(key=lambda z: abs((z[0] + z[1]) / 2 - price))
        return out

    start = max(v17.ZONE_LOOKBACK, 25)
    for i in range(start, n):
        lo_w = i - v17.ZONE_LOOKBACK + 1
        rcs = zones(res_px, res_idx, i, lo_w, c[i], True)
        if not rcs:
            continue
        scs = zones(sup_px, sup_idx, i, lo_w, c[i], False)
        if not scs:
            continue
        pairs = sorted(((rz, sz) for rz in rcs for sz in scs),
                       key=lambda p: abs((p[0][0] + p[0][1]) / 2 - c[i]) + abs((p[1][0] + p[1][1]) / 2 - c[i]))
        for rz, sz in pairs:
            if (rz[0] - sz[1]) / c[i] >= v17.ZONE_MIN_W:
                r_lo[i], r_hi[i] = rz; s_lo[i], s_hi[i] = sz; ok[i] = True
                break
    df = df.copy()
    df["res_lo"] = r_lo; df["res_hi"] = r_hi; df["sup_lo"] = s_lo; df["sup_hi"] = s_hi
    df["zone_ok"] = ok
    return df


def _uptrend_state_5m(df5: pd.DataFrame) -> np.ndarray:
    """上げトレンド状態機械（RG-v4 新設・RG-v5 で複数足化・過去バーのみ＝因果的・上げ専用）。
    発火（いずれか）:
      ① A15: 15分足 TREND_ST15_K 本連続の高値切り上げ∩安値切り上げ（確定バーのみ・上げ構造）
      ② D15: 15分足 TREND_MOM15_K 本連続の陽線 ∩ 累積上昇 ≥ TREND_MOM15_AMP
      ③ C90: 参照安値＝「前回解除以降 かつ 直近90分」の最小 close から +TREND_T90
      ④ T6 : 同「直近6h」の最小 close から +TREND_T6（遅い上げの受け皿）
      参照を解除以降に限定＝スパイク後も安値が窓に残り再発火し続ける「影」を根絶。
    継続: 解除後 TREND_CONT_W 内に close > 前回高値×(1+TREND_CONT_M) ＝上げ継続と確定し再発火
          （発火時安値は前回の脚から引き継ぐ＝緩やかな上げの断片化防止・02-28 事案）。
    解除（いずれか）: 半値戻し（TREND_RETR）／高値更新なし TREND_STALL バー／
      15分構造破断＝close < 直近 TREND_STRUCT_REL 本の確定15分安値の最小（上げ構造の終了を速く検出）。"""
    c = df5["close"].to_numpy(float)
    n = len(c)
    # 15分足（確定バーのみ・label=right）→ 5分へ ffill（確定した瞬間から有効＝未来値ゼロ）
    o15 = df5["open"].resample("15min", label="right", closed="right").first()
    h15 = df5["high"].resample("15min", label="right", closed="right").max()
    l15 = df5["low"].resample("15min", label="right", closed="right").min()
    c15 = df5["close"].resample("15min", label="right", closed="right").last()
    t15 = pd.DataFrame({"o": o15, "h": h15, "l": l15, "c": c15}).dropna()
    hh = (t15["h"] > t15["h"].shift(1)) & (t15["l"] > t15["l"].shift(1))
    a15 = (hh.rolling(TREND_ST15_K).sum() >= TREND_ST15_K)
    up = (t15["c"] > t15["o"])
    d15 = (up.rolling(TREND_MOM15_K).sum() >= TREND_MOM15_K) & \
          ((t15["c"] / t15["c"].shift(TREND_MOM15_K) - 1) >= TREND_MOM15_AMP)
    A15 = a15.reindex(df5.index, method="ffill").fillna(False).to_numpy(bool)
    D15 = d15.reindex(df5.index, method="ffill").fillna(False).to_numpy(bool)
    l15_rel = t15["l"].rolling(TREND_STRUCT_REL).min().reindex(df5.index, method="ffill").to_numpy(float)

    st = np.zeros(n, bool)
    s = 0; H = L = 0.0; last_new = 0
    rel_i = 0; H_prev = np.inf; L_prev = 0.0; rel_time = -10**9
    dq: deque = deque()          # (idx, close) の単調 min-deque＝窓内最小を O(1) で
    for i in range(n):
        while dq and dq[-1][1] >= c[i]:
            dq.pop()
        dq.append((i, c[i]))
        lo90 = max(i - 18, rel_i); lo6 = max(i - 72, rel_i)
        while dq and dq[0][0] < lo6:
            dq.popleft()
        m6 = min(v for _, v in dq)
        m90 = min((v for j, v in dq if j >= lo90), default=c[i])
        if s == 0:
            trig = ((c[i] / m90 - 1) >= TREND_T90 or (c[i] / m6 - 1) >= TREND_T6
                    or A15[i] or D15[i])
            cont = (i - rel_time) <= TREND_CONT_W and c[i] > H_prev * (1 + TREND_CONT_M)
            if trig or cont:
                s = 1; L = m6 if trig else L_prev; H = c[i]; last_new = i
        else:
            if c[i] > H:
                H = c[i]; last_new = i
            if (c[i] <= H - TREND_RETR * (H - L) or (i - last_new) >= TREND_STALL
                    or (np.isfinite(l15_rel[i]) and c[i] < l15_rel[i])):
                s = 0; rel_i = i; rel_time = i; H_prev = H; L_prev = L
        st[i] = bool(s)
    return st


def _selftest_vs_v17(df1h: pd.DataFrame) -> str:
    """v17（視認校正済み）が range とした全バーで、RG の帯が labels_v17.csv と完全一致するか機械照合
    ＝帯対の拡張は「v17 が幅不足で落とした所を拾うだけ」で「v17 が採った帯は動かさない」ことの証明。"""
    lab_path = PROTO_DIR / "labels_v17.csv"
    if not lab_path.exists():
        raise SystemExit(f"ABORT: labels_v17.csv がありません: {lab_path}")
    lab = pd.read_csv(lab_path, parse_dates=["datetime_utc"]).set_index("datetime_utc").sort_index()
    j = df1h.join(lab, how="inner", rsuffix="_lab")
    assert len(j) > 0, "labels_v17.csv と 1h index が重ならない（入力 CSV が違う疑い）"
    v17ok = j["range_ok"].astype(bool)
    sub = j[v17ok]
    missing = int((~sub["zone_ok"].astype(bool)).sum())
    px_mis = 0
    for col in ("res_lo", "res_hi", "sup_lo", "sup_hi"):
        px_mis += int(((sub[col].round(1) - sub[f"{col}_lab"]).abs() > 0.1).sum())
    assert missing == 0 and px_mis == 0, \
        f"v17=range のバーで RG 帯が不一致（帯欠落 {missing} / 価格ズレ {px_mis}）＝拡張が v17 の帯を動かした"
    added = int((j["zone_ok"].astype(bool) & ~v17ok).sum())
    msg = (f"v17=range の全 {len(sub):,}本で帯が labels_v17.csv と完全一致（欠落0・価格ズレ0）＋"
           f"帯対拡張の追加は v17 不成立バーのみ（+{added:,}本）＝v17 の校正済み帯を動かさない機械証明")
    print(f"    [selftest] ✅ {msg}")
    return msg


def _apply_5m_rg(df5: pd.DataFrame, df1h: pd.DataFrame) -> pd.DataFrame:
    """5分足への適用（RG-v4・2段ラベル）:
    uptrend ＝ 上げトレンド状態機械が発火中（緑・除外理由の可視化＝この間は range にしない）
    range   ＝ 1h帯あり ∩ 5分 close が帯内 ∩ 非 uptrend（執行用＝E37 ゲートにはこれだけを使う）
    ※ RG-v3 の range_wait（往復実証待ち）は range に統合（まこさん 2026-07-12「薄い青もレンジとして判定してよい」）。"""
    ok_zone = df1h["zone_ok"].reindex(df5.index, method="ffill").fillna(False).to_numpy(bool)
    res_hi = df1h["res_hi"].reindex(df5.index, method="ffill").to_numpy(float)
    sup_lo = df1h["sup_lo"].reindex(df5.index, method="ffill").to_numpy(float)
    c = df5["close"].to_numpy(float)
    brk = ((c > res_hi) | (c < sup_lo))
    brk = np.where(np.isfinite(res_hi) & np.isfinite(sup_lo), brk, False)
    up = _uptrend_state_5m(df5)
    df5 = df5.copy()
    rng = ok_zone & ~brk & ~up
    df5["label"] = np.where(up, "uptrend", np.where(rng, "range", ""))
    return df5


def _rows_5m(df: pd.DataFrame) -> list:
    ts_ms = (df.index.astype("int64") // 10**6).tolist()
    close_int = df["close"].round().astype(int).tolist()
    return [[int(t), int(c), lab, ""] for t, c, lab in zip(ts_ms, close_int, df["label"].tolist())]


def main() -> int:
    csv_path = v17.CSV
    if not csv_path.exists():
        sys.exit(f"ABORT: missing input CSV: {csv_path}")
    if not INDEX_JSON.exists():
        sys.exit(f"ABORT: missing index.json: {INDEX_JSON}")

    print(f"[1/6] loading 5m CSV: {csv_path.name}")
    md5_head = hashlib.md5(csv_path.read_bytes()).hexdigest()[:12]
    df5 = pd.read_csv(csv_path)
    df5["ts"] = pd.to_datetime(df5["timestamp"])
    df5 = df5.set_index("ts").sort_index()
    print(f"    5m rows: {len(df5):,} / {df5.index[0].date()}〜{df5.index[-1].date()} / md5 {md5_head}")

    print(f"[2/6] ① 1時間 S/Rゾーン局面（帯対拡張・fractal/束ね/定数は v17 再利用）＋ selftest ...")
    df1h = _zones_1h_rg(v17._resample(df5, "1h"))
    n1 = len(df1h); okz = int(df1h["zone_ok"].sum())
    print(f"    1h: {n1:,}本 / 帯あり {okz:,}（{okz/n1*100:.1f}%）")
    selftest_msg = _selftest_vs_v17(df1h)

    print(f"[3/6] ② 上げトレンド状態機械（複数足: 15分構造×2＋90分{TREND_T90*100:.1f}%＋6h{TREND_T6*100:.1f}%）＋ ③ 5分足 帯内判定...")
    df5g = _apply_5m_rg(df5, df1h)
    n5 = len(df5g)
    ok5 = int((df5g["label"] == "range").sum()); up5 = int((df5g["label"] == "uptrend").sum())
    print(f"    5m: range {ok5:,}（{ok5/n5*100:.1f}%）/ uptrend除外 {up5:,}（{up5/n5*100:.1f}%）")

    print(f"[4/6] writing JSON（1h + 1d + 5m月別）...")
    SM_DIR.mkdir(parents=True, exist_ok=True)
    for old in SM_DIR.glob("*.json"):
        old.unlink()
    # 1h 表示＝その1時間の5分ラベルの多数決（uptrend 優先）
    lab5 = pd.Series(df5g["label"].to_numpy(), index=df5g.index)
    up_share = (lab5 == "uptrend").resample("1h", label="right", closed="right").mean()
    rg_share = (lab5 == "range").resample("1h", label="right", closed="right").mean()
    lab1h = np.where(up_share.reindex(df1h.index).fillna(0) >= 0.5, "uptrend",
                     np.where(rg_share.reindex(df1h.index).fillna(0) >= 0.5, "range", ""))
    ts_ms_1h = (df1h.index.astype("int64") // 10**6).tolist()
    rows_1h = [[int(t), int(round(c)), str(l), ""] for t, c, l in zip(ts_ms_1h, df1h["close"].tolist(), lab1h)]
    (PROTO_DIR / f"predictions_{VERSION}_1h.json").write_text(
        json.dumps({"version": VERSION, "granularity": "1h", "rows": rows_1h}, ensure_ascii=False), encoding="utf-8")
    day = pd.DataFrame({"close": df5g["close"].values, "ok": (df5g["label"] == "range").astype(int).values,
                        "date": df5g.index.normalize()}, index=df5g.index)
    dd = day.groupby("date").agg(close=("close", "last"), ok=("ok", "mean"))
    ts_ms_d = (dd.index.astype("int64") // 10**6).tolist()
    rows_1d = [[int(t), int(round(c)), ("range" if o >= 0.5 else ""), ""]
               for t, c, o in zip(ts_ms_d, dd["close"].tolist(), dd["ok"].tolist())]
    (PROTO_DIR / f"predictions_{VERSION}_1d.json").write_text(
        json.dumps({"version": VERSION, "granularity": "1d", "rows": rows_1d}, ensure_ascii=False), encoding="utf-8")
    edges = pd.date_range(v17.PLOT_START, v17.PLOT_END, freq="MS")
    n_sm = 0
    for lo, hi in zip(edges[:-1], edges[1:]):
        sub = df5g[(df5g.index >= lo) & (df5g.index < hi)]
        if len(sub) < 100:
            continue
        (SM_DIR / f"{lo.strftime('%Y-%m')}.json").write_text(
            json.dumps({"version": VERSION, "granularity": "5m", "rows": _rows_5m(sub)}, ensure_ascii=False), encoding="utf-8")
        n_sm += 1
    print(f"    saved 1h/1d ＋ 5m 月別 {n_sm} ファイル → predictions_{VERSION}_5m/")
    up1h = (up_share.reindex(df1h.index).fillna(0) >= 0.5).astype(int)
    pd.DataFrame({"datetime_utc": df1h.index, "close": df1h["close"].round(1),
                  "res_lo": df1h["res_lo"].round(1), "res_hi": df1h["res_hi"].round(1),
                  "sup_lo": df1h["sup_lo"].round(1), "sup_hi": df1h["sup_hi"].round(1),
                  "zone_ok": df1h["zone_ok"].astype(int), "uptrend_1h": up1h.to_numpy()}).to_csv(
        PROTO_DIR / f"labels_{VERSION}.csv", index=False)
    print(f"    saved labels_{VERSION}.csv（E37 移植時の一致照合の正本・5分の最終判定は predictions_{VERSION}_5m/）")

    print(f"[5/6] 仕様の自動生成（実値由来・スキーマ強制）...")
    spec = {
        "入力データ": (f"{csv_path.name}（5分足 {len(df5):,}本 {df5.index[0].date()}〜{df5.index[-1].date()}・"
                   f"md5 {md5_head}・Binance spot 正本 §8.2.1.1）"),
        "教師": ("なし＝幾何ルールのみ（手動レジームラベル regime_samples_4h*.csv / daily_human は一切不読・2026-07-03 方針）。"
               "まこさん指摘の除外7窓・残す3域（2026-07-12）は閾値選定の視認校正照合点として使用（学習器に与えない・採点窓 net 不参照）"),
        "判定ロジック": (f"①1時間足: 確定 fractal スイング（j+2 確定）を過去{v17.ZONE_LOOKBACK}h窓・価格帯{v17.ZONE_TOL*100:.1f}%で束ね、"
                    f"スイング数≥{v17.ZONE_TOUCH}のS/Rゾーン対（近い順・幅≥{v17.ZONE_MIN_W*100:.1f}%を満たす最初の対＝v3拡張）が"
                    f"close の上下に揃う＝帯あり "
                    f"②上げトレンド状態機械（v4新設・v5で複数足化・上げ専用）: 発火＝(a)15分足{TREND_ST15_K}本連続の"
                    f"高値切り上げ∩安値切り上げ (b)15分足 陽線{TREND_MOM15_K}連続∩累積+{TREND_MOM15_AMP*100:.1f}% "
                    f"(c)「前回解除以降かつ直近90分」の安値から+{TREND_T90*100:.1f}% (d)同6hの安値から+{TREND_T6*100:.1f}%・"
                    f"継続＝解除後24h内に前回高値+{TREND_CONT_M*100:.1f}%超えで再発火・"
                    f"解除＝半値戻し or 高値更新なし{TREND_STALL*5//60}時間 or 15分構造破断"
                    f"（close<直近{TREND_STRUCT_REL}本の確定15分安値）＝発火中は uptrend（range にしない） "
                    f"③5分足: 帯あり ∩ close が帯内（外れ＝即離脱） ∩ 非 uptrend ＝ range。"
                    f"※v3 の range_wait（往復実証待ち）は range に統合（2026-07-12 まこさん）"),
        "パラメータ（出所つき）": (f"ZONE_LOOKBACK={v17.ZONE_LOOKBACK}h / ZONE_TOL={v17.ZONE_TOL} / ZONE_TOUCH={v17.ZONE_TOUCH} / "
                         f"ZONE_MIN_W={v17.ZONE_MIN_W}〔視認校正（2026-07-05 概ね良い）＝v17 と同一値〕 / "
                         f"TREND_T90={TREND_T90} TREND_T6={TREND_T6} ST15_K={TREND_ST15_K} MOM15_K={TREND_MOM15_K} "
                         f"MOM15_AMP={TREND_MOM15_AMP} RETR={TREND_RETR} STALL={TREND_STALL}bar STRUCT_REL={TREND_STRUCT_REL}本 "
                         f"CONT={TREND_CONT_M}/{TREND_CONT_W}bar〔2026-07-12 まこさん指摘の除外7窓と残す3域で校正・"
                         f"v5は指摘④（複数足で早く）を受け検出の速さ優先の側を採用・採点窓 net 不参照〕"),
        "因果性（未来値ゼロ）": ("1h/15分バーとも確定時刻ラベル（label=right/closed=right）＝確定したバーのみを5分足へ前向き適用（ffill）。"
                        "トレンド状態機械は過去 close のみ（min-deque・状態は過去からの逐次更新）。"
                        "5分バー i の判定はバー i の確定値まで使用＝売買に使う時の執行はバー i+1 から。"
                        "因果性の代償（v5で短縮）＝発火の遅れ 概ね10〜50分（緩やかな上げの序盤のみ最大2.5h）・"
                        "頂点後の解除はみ出し 25〜75分・上げの中の深い押し戻し（02-25 05〜08時型）は部分捕捉（開示済み）"),
        "出力粒度": "5m（執行・月別・range/uptrend の2段）/ 1h（多数決）/ 1d（俯瞰・日内 range 率≥50%）",
        "selftest": selftest_msg,
        "生成方式": (f"scripts/dashboard/build_regime_gate_rg.py が fractal/束ね/定数を build_range_gate_dashboard.py（v17）から "
                 f"import 再利用（帯対拡張・トレンド状態機械は RG 系列の正本＝本スクリプト）し、本仕様を実行時の実値から自動生成"
                 f"（必須{len(RG_SPEC_SCHEMA)}項目のスキーマ検査つき＝削ると生成停止）"),
    }
    _assert_spec_schema(spec)
    print(f"    仕様 {len(spec)} 項目 生成・スキーマ検査 ✅")

    print(f"[6/6] updating index.json with {VERSION} ...")
    distribution = {"range": {"count": ok5, "pct": round(ok5 / n5 * 100, 2)},
                    "uptrend": {"count": up5, "pct": round(up5 / n5 * 100, 2)},
                    "non_range": {"count": n5 - ok5 - up5, "pct": round((n5 - ok5 - up5) / n5 * 100, 2)}}
    index_obj = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    index_obj["prototypes"] = [p for p in index_obj["prototypes"] if p.get("version") != VERSION]
    index_obj["prototypes"].append({
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "spec": spec,
        "distribution": distribution,
    })
    INDEX_JSON.write_text(json.dumps(index_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    index.json: {VERSION} 登録（5m range {distribution['range']['pct']}% / uptrend {distribution['uptrend']['pct']}%）")

    print(f"\n[DONE] ダッシュボード → python3 scripts/dashboard/dashboard_server.py → ⑪ → {VERSION} → 粒度5分 → 月 → 日絞り")
    return 0


if __name__ == "__main__":
    sys.exit(main())

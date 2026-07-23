#!/usr/bin/env python3
"""observe_diag.py — 建玉の観察と探索を、決まった型で機械が全部出す道具（read-only 診断）

実装しているフロー（まこさん指定・この3段を全部やる）
--------------------------------------------------------------------------
1. すべての Exit ごとに、下の分岐・視点で観察する
   ・入口の型（down=天井は直近高値 / flat_up=天井は res_hi）ごとに分類
   ・「エントリーの瞬間」「入ってから決済まで」「決済の瞬間」の3場面
   ・特徴は 指標 × 時間軸 × 閾値 × パラメータ の4軸で当てる
   ・入った前後の玉の差異（価格差・時間間隔・勝敗・レンジ内で何番目・前玉entryから相場が上がったか）
2. 各特徴をテーブルに載せて分類・分析する（分離力で順位づけ）
3. 利益最大化・損失最小化のロジックを組む
   ・4軸のあらゆる組み合わせで検証
   ・時間・閾値・パラメータは probe であたりを付けてから Optuna の探索で最適値を出す

呼び出し側が渡せるもの / 渡せないもの
--------------------------------------------------------------------------
渡せる  : 売買記録CSVのパスと、設定ファイル observe_config.json のパス。
探索範囲（足・分位・SL候補・TP候補・待ち・窓・各指標の期間・探索の分岐 search_modes）は
observe_config.json で決める。走らせる前に編集して足す/減らす。値をコードに焼かない。
検証期間も observe_config.json の period で指定できる（未指定なら periods.py の採点窓全部）。
★使った設定と期間は出力の先頭に全部印字する＝狭めたら見える。
渡せない: 採点窓の外の期間（学習窓・封印期間は指定しても止まる）／
          side・入口の型・出口理由（売買記録から取る）／
          出す節（SECTIONS 固定）／ 結果の言い換えを分離力に混ぜること／
          切る探索と取る探索のシグナルを混ぜること（切る=逆行側・取る=順行側に固定）／
          探索の side×型 4分岐を混ぜること（分岐ごとに別々の探索で回す）。

守っていること
--------------------------------------------------------------------------
・売買記録CSVを書かない。score を呼ばない。金額を出さない（件数と価格に対する % のみ）。
  勝敗の分類にだけ net_usd の符号を使う。
・結果の言い換え（最大逆行・一度も利にならず 等）は TAUTOLOGY_COLS で隔離し、
  分離力の順位づけに入れない。勝った玉に利が出るのは定義上そうなるだけで、発見ではない。
・保有中の判定は「建ててから何分以内に発火したか」で見る。負けが確定した後の発火を混ぜない。
・逆行の向きは side で決まる（SHORT は上・LONG は下）。指標の向きは道具側が反転させる。
・エントリー/決済の瞬間の特徴は、約定バーの1本前＝その時点で確定している値を使う（H2）。
・計算できない節は黙って消さず、理由を印字する。
・探索は前半で行い後半で確認する（同じ窓で最良値を選んで良く見せない・L-267）。
・探索のモードは search_modes で選ぶ＝**一気に回さず、順番に1系統ずつ**（まこさん指示 2026-07-21。
  独立探索の寄せ集めは全体の最適解にならず、試行が増えるほど運を拾う数も増えるため）。
・**取る（建値からの % TP）は削除した**＝TP を変えろという指示は無い（まこさん 2026-07-21）。
  TP は現行ロジック（レンジ幾何の2段利確）のまま＝この道具では触らない。
  利益最大化側の探索が要る時は、形をまこさんと決めてから作る。selftest が sc_take の不在を検査する。
・★最適化の単位は side（ショート/ロング）× 入口の型（down/flat_up）の4分岐。ロングとショートは
  玉の動きと特徴が違う＝混ぜて最適化しない（cat_requirements §6＝閾値は LONG/SHORT 別・H15 分離・
  V9 原則3＝値は型別に別調整）。シグナルは逆行側/順行側を別プールで生成し、
  切る探索は逆行側だけ・取る探索は順行側だけを使う（上下対を1つの探索空間に混ぜない）。

⚠️ これは疑似シミュ。切った玉のぶんスロットが空いて次の玉が入る効果（L-330）を再現していない。
   采否の根拠にしない。采否は実装して score.py の採点窓で決める。

使い方（この順番・まこさん確定 2026-07-21）
--------------------------------------------------------------------------
① 計画  : python3 observe_diag.py --plan <trades_csv> <bars_csv>
          検証する内容・項目・条件を実値から自動生成して印字＝走らせる前にまこさんへ提出する。
          CC が計画を手書きしない。足す/減らすは observe_config.json を編集して再生成。
② 本走  : まこさんの OK が出てから python3 observe_diag.py <trades_csv> <bars_csv>
          出力の先頭に計画と同じ設定が印字される＝計画と実行を機械的に突き合わせられる。
③ 結果  : 末尾の「結果サマリ」節が機械集計で自動生成される＝CC の手書き要約を挟まない。

自己検査: python3 observe_diag.py --selftest
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd

# 検証期間は periods.py が正本（H8・手打ち禁止）
from periods import SCORE_START, SCORE_END   # noqa: E402

warnings.filterwarnings("ignore")

# ══ 呼び出し側から変更できない定数 ═══════════════════════════════════════
SECTIONS = [
    "0 母集団（型 × 出口理由 × 勝敗）",
    "1 機構別分解（TREND_CONT を どの撤退機構が切ったかで再導出・概算＝価格水準と保有時間から・実装の分岐ログではない）",
    "2 出口ごと × 型ごと ─ エントリーの瞬間",
    "3 出口ごと × 型ごと ─ 入ってから決済まで",
    "4 出口ごと × 型ごと ─ 決済の瞬間",
    "5 出口ごと × 型ごと ─ 決済の後（切った/決済した後に価格がどうなったか＝episode_gap_h 時間の追跡）",
    "6 出口ごと × 型ごと ─ 入った前後の玉の差異",
    "7 巻き込み（負けを切る量と勝ちを切る量）",
    "8 ロジック構築（side×型の分岐ごとに search_modes で選んだ系統だけを probe→Optuna・前半探索/後半確認）",
    "9 結果サマリ（自動生成＝両半期プラスの候補だけを機械抽出・手書きなし）",
]
# 探索モードの定義＝「どのロジックに対して・どの値の候補から最適を検証するか」（計画と本走の両方に印字）
MODE_INFO = {
    "exit_cut": ("切る（損失最小化）",
                 "『急騰急落と判定された玉だけをエントリー価格からの % で早く切る』ロジック（まこさん指示 2026-07-20）の"
                 "『急騰急落の判定シグナル』そのものを候補プールから探す＝実装済みの急騰判定（v47）は使わない。"
                 "急落判定は未実装＝ロング側は指標の向きを反転した下向き候補から探す（設計の材料を出す）。"
                 "v47 と同族の候補（RSI9_15分・BB%b 高分位）もプール内で他候補と同じ土俵で対決する",
                 "判定シグナル候補（逆行側プール＝指標96種×時間足×分位 quantiles・ショートは上向き/ロングは下向き）"
                 " × 待ち分 wait_grid × 判定窓 early_windows × 切る% sl_grid（エントリー価格からの%）"),
    "entry_filter": ("入らない（入口フィルタ）",
                     "entry 直前の特徴が閾値の側にある玉は建てないロジックに対し、どの特徴・どの閾値が最適かを検証する。"
                     "プールには指標×時間足に加え、玉間の特徴（レンジ内で何番目・前玉との価格差%・前玉との時間間隔分"
                     "[エピソード内/通し]・前玉entryから相場変化%＝entry 時点で確定している因果 OK 列のみ・"
                     "前玉の勝敗依存は入れない）を含む（2026-07-23 まこさん選択3＝観察で最強だった玉間隔を同じ土俵で対決させる）",
                     "entry 直前の特徴（指標×時間足＋玉間5列）× 分位 quantiles（前半の分布で閾値化）× 上下側"),
    "set": ("セット（入口フィルタ＋切るの同時）",
            "入らない と 切る を同時に効かせた組み合わせを検証する",
            "入口フィルタの条件 × 切るの条件（同時）"),
}
MODE_JP = {k: v[0] for k, v in MODE_INFO.items()}


def _print_mode_info(cfg: dict) -> None:
    """検証するロジックと値の対応を実値から印字（計画・本走ヘッダ共通・手書きしない）。"""
    print("\n  ── 検証するロジックと値（search_modes で選んだ系統だけ・順番に1系統ずつ）──")
    for m in cfg["search_modes"]:
        name, logic, values = MODE_INFO.get(m, (m, "定義なし", "定義なし"))
        print(f"     ▶ {name}")
        print(f"        ロジック: {logic}")
        print(f"        検証する値: {values}")
    off = [v[0] for k, v in MODE_INFO.items() if k not in cfg["search_modes"]]
    if off:
        print(f"     （今回やらない系統: {' / '.join(off)}＝順番に。次に回すかはまこさんが決める）")
    print("     ▶ TP（利確）は現行ロジック（レンジ幾何の2段利確）のまま＝この検証では触らない。")
    print("        建値からの % TP の探索は削除済み（まこさん指示 2026-07-21・selftest が不在を検査）。")
# ★探索範囲は observe_config.json（走らせる前に編集して足す/減らす）。
#   probe は広く試すためのものなので、値をコードに焼かない。
#   使った値は出力の先頭に全部印字する＝狭めたら見える。
CONFIG_PATH = __file__.rsplit("/", 1)[0] + "/observe_config.json"
TF_RULE = {"5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h",
           "2h": "2h", "4h": "4h", "6h": "6h", "12h": "12h", "1d": "1D"}


def load_config(path: str | None = None) -> dict:
    import json
    p = path or CONFIG_PATH
    with open(p, encoding="utf-8") as f:
        cfg = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    cfg["_source"] = p
    bad = [t for t in cfg["timeframes"] if t not in TF_RULE]
    if bad:
        raise SystemExit(f"[設定] 知らない足: {bad}（使えるのは {list(TF_RULE)}）")
    if "1m" in cfg["timeframes"]:
        raise SystemExit("[設定] 1m は使わない（CLAUDE.md 提案禁止リスト）")
    return cfg


def _resolve_period(cfg: dict):
    """検証期間。config の period で指定できるが、採点窓の外（学習窓・封印期間）は物理で止める。
    fast-mode §8.5＝学習窓は使わない・見ない／ H8＝期間の正本は periods.py。"""
    p = cfg.get("period") or {}
    s = pd.Timestamp(p["start"]) if p.get("start") else SCORE_START
    e = pd.Timestamp(p["end"]) if p.get("end") else SCORE_END
    if s < SCORE_START or e > SCORE_END:
        raise SystemExit(
            f"[設定] 期間 {s.date()}〜{e.date()} が採点窓 {SCORE_START.date()}〜{SCORE_END.date()} の外に出ている。"
            "学習窓・封印期間は観察にも使わない（fast-mode §8.5 / H8）。")
    if s >= e:
        raise SystemExit(f"[設定] 期間の start {s.date()} が end {e.date()} 以降になっている")
    return s, e


TAUTOLOGY_COLS = {"最大逆行%", "最大順行%", "最大逆行まで分", "一度も利にならず", "決済位置%",
                  "hold_min", "net_usd", "gross_usd", "fee_usd", "mfe_usd", "mae_usd"}


def _tautology(cfg) -> set:
    return (TAUTOLOGY_COLS
            | {f"{m}%逆行まで分" for m in cfg["adverse_marks"]}
            | {f"{m}%順行まで分" for m in cfg["favorable_marks"]})
_DEMAND_FILES = {
    "taker_ls": ("../../data/oi_BTCUSDT_5y.csv", "time", "taker_ls"),
    "L-S比": ("../../data/oi_BTCUSDT_5y.csv", "time", "ls_global"),
    "CVD": ("../../data/BTCUSDT-1m-binance-taker-2025-06-01_2026-02-28.csv", "timestamp", None),
}


# ══ 指標の部品 ══════════════════════════════════════════════════════════
def _rsi(c, n):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def _atr(h, l, c, n=14):
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def _adx_di(h, l, c, n=14):
    up, dn = h.diff(), -l.diff()
    p = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=h.index)
    m = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=h.index)
    a = _atr(h, l, c, n)
    pdi = 100 * p.ewm(alpha=1 / n, adjust=False).mean() / a
    mdi = 100 * m.ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean(), pdi, mdi


def _rci(c, n=9):
    r = c.rolling(n).apply(
        lambda x: 1 - 6 * ((pd.Series(x).rank() - pd.Series(range(1, n + 1))) ** 2).sum() / (n * (n * n - 1)),
        raw=True)
    return r * 100


def _supertrend(h, l, c, n=10, k=3.0):
    a = _atr(h, l, c, n)
    return (h + l) / 2 - k * a          # 上側バンド基準の簡易版（close との差を見る）


def _vp_levels(c, v, win=288):
    """出来高プロファイル。窓内で出来高が最も厚い価格＝POC、上下 70% 帯＝VAH/VAL の近似。"""
    poc, vah, val = [], [], []
    ca, va = c.to_numpy(), v.to_numpy()
    for i in range(len(ca)):
        if i < win:
            poc.append(np.nan); vah.append(np.nan); val.append(np.nan); continue
        cw, vw = ca[i - win:i], va[i - win:i]
        bins = np.linspace(cw.min(), cw.max(), 25)
        idx = np.clip(np.digitize(cw, bins) - 1, 0, len(bins) - 2)
        agg = np.bincount(idx, weights=vw, minlength=len(bins) - 1)
        centers = (bins[:-1] + bins[1:]) / 2
        order = np.argsort(agg)[::-1]
        cum = np.cumsum(agg[order]) / max(agg.sum(), 1e-9)
        keep = centers[order[:max(1, int(np.searchsorted(cum, 0.7)) + 1)]]
        poc.append(centers[order[0]]); vah.append(keep.max()); val.append(keep.min())
    return (pd.Series(poc, index=c.index), pd.Series(vah, index=c.index), pd.Series(val, index=c.index))


def _sr_touch(c, h, l, win=288, tol=0.003):
    """いまの価格帯に、窓内で何回タッチしているか。"""
    out = np.full(len(c), np.nan)
    ca, ha, la = c.to_numpy(), h.to_numpy(), l.to_numpy()
    for i in range(win, len(ca)):
        lvl = ca[i]
        band = lvl * tol
        out[i] = int(((ha[i - win:i] >= lvl - band) & (la[i - win:i] <= lvl + band)).sum())
    return pd.Series(out, index=c.index)


# ══ 指標カタログ（この道具が正本・呼び出し側は足せない/減らせない）══════
# (表示名, 計算関数, 方向あり?)  方向あり＝値が大きいほど「価格が上」を意味する
def build_catalog(cfg: dict) -> list[tuple]:
    """指標カタログ。期間・パラメータは observe_config.json から取る（コードに焼かない）。"""
    C = []

    def add(name, fn, directional):
        C.append((name, fn, directional))

    # ── トレンド/モメンタム ──
    for n in cfg["atr_periods"]:
        add(f"ADX{n}", lambda d, n=n: _adx_di(d.high, d.low, d.close, n)[0], False)
        add(f"DI差{n}", lambda d, n=n: (lambda a: a[1] - a[2])(_adx_di(d.high, d.low, d.close, n)), True)
    for (f_, s_, g_) in cfg["macd_params"]:
        add(f"MACD線%({f_},{s_})", lambda d, f_=f_, s_=s_:
            (d.close.ewm(span=f_).mean() - d.close.ewm(span=s_).mean()) / d.close * 100, True)
        add(f"MACDヒスト%({f_},{s_},{g_})", lambda d, f_=f_, s_=s_, g_=g_:
            (lambda m: (m - m.ewm(span=g_).mean()) / d.close * 100)(
                d.close.ewm(span=f_).mean() - d.close.ewm(span=s_).mean()), True)
    for n in cfg["rsi_periods"]:
        add(f"RSI{n}", lambda d, n=n: _rsi(d.close, n), True)
    for n in cfg["roc_periods"]:
        add(f"ROC{n}", lambda d, n=n: d.close.pct_change(n) * 100, True)
    for n in cfg["stoch_periods"]:
        add(f"Stoch%K{n}", lambda d, n=n: 100 * (d.close - d.low.rolling(n).min())
            / (d.high.rolling(n).max() - d.low.rolling(n).min()).replace(0, np.nan), True)
        add(f"Stoch%D{n}", lambda d, n=n: (100 * (d.close - d.low.rolling(n).min())
            / (d.high.rolling(n).max() - d.low.rolling(n).min()).replace(0, np.nan)).rolling(3).mean(), True)
    for n in cfg["mfi_periods"]:
        add(f"MFI{n}", lambda d, n=n: (lambda tp: 100 - 100 / (1 + (
            (tp * d.volume).where(tp > tp.shift(), 0).rolling(n).sum()
            / (tp * d.volume).where(tp < tp.shift(), 0).rolling(n).sum().replace(0, np.nan)
        )))((d.high + d.low + d.close) / 3), True)
    for n in cfg["cmf_periods"]:
        add(f"CMF{n}", lambda d, n=n: (((d.close - d.low) - (d.high - d.close))
                                       / (d.high - d.low).replace(0, np.nan) * d.volume).rolling(n).sum()
            / d.volume.rolling(n).sum().replace(0, np.nan), True)
    for n in cfg["obv_slope_periods"]:
        add(f"OBV傾き{n}", lambda d, n=n: (np.sign(d.close.diff()) * d.volume).fillna(0).cumsum().diff(n)
            / d.volume.rolling(n).sum().replace(0, np.nan), True)
    for (t_, k_) in cfg["ichimoku"]:
        add(f"close vs 転換線%({t_})", lambda d, t_=t_:
            (d.close / ((d.high.rolling(t_).max() + d.low.rolling(t_).min()) / 2) - 1) * 100, True)
        add(f"close vs 基準線%({k_})", lambda d, k_=k_:
            (d.close / ((d.high.rolling(k_).max() + d.low.rolling(k_).min()) / 2) - 1) * 100, True)
    for n in cfg["rci_periods"]:
        add(f"RCI{n}", lambda d, n=n: _rci(d.close, n), True)
    for n in cfg["ema_periods"]:
        add(f"EMA{n}傾き%", lambda d, n=n: d.close.ewm(span=n, adjust=False).mean().pct_change(5) * 100, True)
    # ── ボラ ──
    for n in cfg["atr_periods"]:
        add(f"ATR%{n}", lambda d, n=n: _atr(d.high, d.low, d.close, n) / d.close * 100, False)
    for n in cfg["bb_periods"]:
        for s in cfg["bb_sigma"]:
            add(f"BB%b({n},{s})", lambda d, n=n, s=s: (d.close - (d.close.rolling(n).mean()
                - s * d.close.rolling(n).std())) / (2 * s * d.close.rolling(n).std()).replace(0, np.nan), True)
            add(f"BB幅({n},{s})", lambda d, n=n, s=s:
                2 * s * d.close.rolling(n).std() / d.close.rolling(n).mean(), False)
    for n in cfg["realized_vol_periods"]:
        add(f"realized_vol{n}", lambda d, n=n: np.log(d.close / d.close.shift()).rolling(n).std() * 100, False)
    for n in cfg["donchian_periods"]:
        add(f"Donchian幅%{n}", lambda d, n=n:
            (d.high.rolling(n).max() - d.low.rolling(n).min()) / d.close * 100, False)
    for n in cfg["zscore_periods"]:
        add(f"zscore{n}", lambda d, n=n:
            (d.close - d.close.rolling(n).mean()) / d.close.rolling(n).std().replace(0, np.nan), True)
    # ── 出来高 ──
    for n in cfg["volume_ratio_periods"]:
        add(f"volume_ratio{n}", lambda d, n=n: d.volume / d.volume.rolling(n).mean().replace(0, np.nan), False)
    # ── ローソク ──
    add("包み足", lambda d: ((d.close > d.open.shift()) & (d.open < d.close.shift())).astype(float)
        - ((d.close < d.open.shift()) & (d.open > d.close.shift())).astype(float), True)
    add("pinbar", lambda d: ((d[["open", "close"]].min(axis=1) - d.low)
                             - (d.high - d[["open", "close"]].max(axis=1))) / (d.high - d.low).replace(0, np.nan), True)
    add("連続本数", lambda d: (np.sign(d.close - d.open)
                             .groupby((np.sign(d.close - d.open) != np.sign(d.close - d.open).shift()).cumsum())
                             .cumcount() + 1) * np.sign(d.close - d.open), True)
    add("body比", lambda d: (d.close - d.open).abs() / (d.high - d.low).replace(0, np.nan), False)
    add("上ヒゲ比", lambda d: (d.high - d[["open", "close"]].max(axis=1)) / (d.high - d.low).replace(0, np.nan), False)
    add("下ヒゲ比", lambda d: (d[["open", "close"]].min(axis=1) - d.low) / (d.high - d.low).replace(0, np.nan), False)
    # ── 形 ──
    for n in cfg["swing_windows"]:
        add(f"swing高値距離%{n}", lambda d, n=n: (d.close / d.high.rolling(n).max() - 1) * 100, True)
        add(f"swing安値距離%{n}", lambda d, n=n: (d.close / d.low.rolling(n).min() - 1) * 100, True)
        add(f"高値からの経過バー{n}", lambda d, n=n:
            d.high.rolling(n).apply(lambda x: len(x) - 1 - int(np.argmax(x)), raw=True), False)
        add(f"安値からの経過バー{n}", lambda d, n=n:
            d.low.rolling(n).apply(lambda x: len(x) - 1 - int(np.argmin(x)), raw=True), False)
        add(f"形スコア{n}(V=+/M=−)", lambda d, n=n:
            np.sign(d.close - d.close.shift(n // 2)) + np.sign(d.close.shift(n // 2) - d.close.shift(n)), True)
    # ── 位置 ──
    for n in cfg["ema_periods"]:
        add(f"close vs EMA{n}%", lambda d, n=n: (d.close / d.close.ewm(span=n, adjust=False).mean() - 1) * 100, True)
    for n in cfg["sma_periods"]:
        add(f"close vs SMA{n}%", lambda d, n=n: (d.close / d.close.rolling(n).mean() - 1) * 100, True)
    for n in cfg["vwap_windows"]:
        add(f"close vs VWAP%{n}", lambda d, n=n: (d.close / ((d.close * d.volume).rolling(n).sum()
            / d.volume.rolling(n).sum().replace(0, np.nan)) - 1) * 100, True)
    for (n, k) in cfg["keltner"]:
        add(f"close vs Keltner上%({n},{k})", lambda d, n=n, k=k: (d.close / (d.close.ewm(span=n, adjust=False).mean()
            + k * _atr(d.high, d.low, d.close)) - 1) * 100, True)
        add(f"close vs Keltner下%({n},{k})", lambda d, n=n, k=k: (d.close / (d.close.ewm(span=n, adjust=False).mean()
            - k * _atr(d.high, d.low, d.close)) - 1) * 100, True)
    for (n, k) in cfg["supertrend"]:
        add(f"close vs Supertrend%({n},{k})", lambda d, n=n, k=k:
            (d.close / _supertrend(d.high, d.low, d.close, n, k) - 1) * 100, True)
    for n in cfg["swing_windows"]:
        add(f"close vs {n}本高値%", lambda d, n=n: (d.close / d.high.rolling(n).max() - 1) * 100, True)
        add(f"close vs {n}本安値%", lambda d, n=n: (d.close / d.low.rolling(n).min() - 1) * 100, True)
    # ── 構造 ──
    for n in cfg["pivot_windows"]:
        add(f"close vs pivotPP%{n}", lambda d, n=n: (d.close / ((d.high.rolling(n).max()
            + d.low.rolling(n).min() + d.close.shift(1)) / 3) - 1) * 100, True)
    for n in cfg["fib_windows"]:
        add(f"fib位置{n}", lambda d, n=n: (d.close - d.low.rolling(n).min())
            / (d.high.rolling(n).max() - d.low.rolling(n).min()).replace(0, np.nan), True)
    for n in cfg["vp_windows"]:
        add(f"close vs POC%{n}", lambda d, n=n: (d.close / _vp_levels(d.close, d.volume, n)[0] - 1) * 100, True)
        add(f"close vs VAH%{n}", lambda d, n=n: (d.close / _vp_levels(d.close, d.volume, n)[1] - 1) * 100, True)
        add(f"close vs VAL%{n}", lambda d, n=n: (d.close / _vp_levels(d.close, d.volume, n)[2] - 1) * 100, True)
    for n in cfg["sr_windows"]:
        for t in cfg["sr_tol"]:
            add(f"S-Rタッチ数({n},{t})", lambda d, n=n, t=t: _sr_touch(d.close, d.high, d.low, n, t), False)
    return C


# ══ 指標の組み立て（全時間軸）════════════════════════════════════════════
def _resample(df, rule):
    return df.resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()


def build_features(bars: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, dict]:
    """指標 × 時間軸 を全部つくる。上位足は『足が閉じた時刻』から使う（未来を見ない）。"""
    out, meta = {}, {}
    catalog = build_catalog(cfg)
    for tf in cfg["timeframes"]:
        src = bars if tf == "5m" else _resample(bars, TF_RULE[tf])
        for name, fn, directional in catalog:
            col = f"{name}__{tf}"
            try:
                s = fn(src)
            except Exception as e:                       # 黙って消さない
                meta[col] = ("計算できず", str(e)[:60]); continue
            if tf != "5m":
                s = s.copy()
                s.index = src.index + pd.Timedelta(TF_RULE[tf])
                s = s.reindex(bars.index, method="ffill")
            out[col] = pd.to_numeric(s, errors="coerce")
            meta[col] = ("ok", directional)
    return pd.DataFrame(out, index=bars.index), meta


def load_demand(bars_index) -> tuple[pd.DataFrame, dict]:
    """需給。元データが期間を覆っていない分は NaN のまま残し、被覆率を報告する。"""
    import pathlib
    base = pathlib.Path(__file__).resolve().parent
    out, cov = {}, {}
    for name, (rel, tcol, vcol) in _DEMAND_FILES.items():
        p = (base / rel).resolve()
        if not p.exists():
            cov[name] = "ファイルなし"; continue
        try:
            use = [tcol] + ([vcol] if vcol else ["taker_buy_base", "volume"])
            d = pd.read_csv(p, usecols=use, parse_dates=[tcol]).set_index(tcol).sort_index()
            d.index = d.index.tz_localize(None) if d.index.tz is not None else d.index
            s = (d[vcol] if vcol else (2 * d["taker_buy_base"] - d["volume"]).cumsum())
            s = s.reindex(bars_index, method="ffill")
            # 元データの終端より後は ffill で埋めない（実データが無い区間を持たない）
            s[bars_index > d.index.max()] = np.nan
            out[name] = pd.to_numeric(s, errors="coerce")
            cov[name] = f"{d.index.min().date()}〜{d.index.max().date()} / 対象期間の被覆 {s.notna().mean()*100:.1f}%"
        except Exception as e:
            cov[name] = f"読めず: {str(e)[:50]}"
    return pd.DataFrame(out, index=bars_index), cov


# ══ 分離力 ═════════════════════════════════════════════════════════════
def _auc(a: pd.Series, b: pd.Series) -> float:
    """b の値が a より大きくなる確率。0.5=分離なし。"""
    a, b = a.dropna(), b.dropna()
    if len(a) < 10 or len(b) < 10:
        return np.nan
    r = pd.concat([a, b]).rank()
    return float((r.iloc[len(a):].sum() - len(b) * (len(b) + 1) / 2) / (len(a) * len(b)))


def rank_separation(df: pd.DataFrame, mask: pd.Series, cols: list[str], taut: set | None = None, top: int = 15) -> pd.DataFrame:
    """mask の群 と それ以外 を分ける特徴を順位づけ。結果の言い換えは除外する。"""
    rows = []
    for c in cols:
        if c in (taut or TAUTOLOGY_COLS) or c not in df.columns:
            continue
        if not pd.api.types.is_numeric_dtype(df[c]):
            continue
        a = _auc(df.loc[~mask, c], df.loc[mask, c])
        if np.isnan(a):
            continue
        rows.append({"特徴": c, "分離力": round(a, 3), "|0.5との差|": round(abs(a - 0.5), 3),
                     "この出口の中央": round(float(df.loc[mask, c].median()), 4),
                     "それ以外の中央": round(float(df.loc[~mask, c].median()), 4)})
    if not rows:
        return pd.DataFrame()
    return (pd.DataFrame(rows).sort_values("|0.5との差|", ascending=False)
            .head(top).reset_index(drop=True))


# ══ 印字 ════════════════════════════════════════════════════════════════
def _h(t):
    print("\n" + "=" * 100); print(f"■ {t}"); print("=" * 100)


def _sub(t):
    print(f"\n── {t} " + "─" * max(0, 84 - len(t)))


def _skip(r):
    print(f"     ⚠️ 計算できず: {r}")


# ══ 軌跡・玉間 ══════════════════════════════════════════════════════════
def trajectory(tr, bars, sig_mat, sig_names, cfg):
    idx = bars.index
    pos = {t: i for i, t in enumerate(idx)}
    hi, lo = bars.high.to_numpy(), bars.low.to_numpy()
    n = len(sig_names)
    fired = np.zeros((len(tr), n), bool)
    fmin = np.full((len(tr), n), np.nan)
    recs = []
    for j, (_, t) in enumerate(tr.iterrows()):
        i0, i1 = pos.get(t.entry_time), pos.get(t.exit_time)
        r = {"_ok": False}
        if i0 is not None and i1 is not None and i1 > i0:
            seg = np.arange(i0 + 1, i1 + 1)
            ep = t.entry_price
            if t.side == "LONG":
                adv, fav = (1 - lo[seg] / ep) * 100, (hi[seg] / ep - 1) * 100
            else:
                adv, fav = (hi[seg] / ep - 1) * 100, (1 - lo[seg] / ep) * 100
            r.update({"_ok": True, "最大逆行%": float(adv.max()), "最大順行%": float(fav.max()),
                      "最大逆行まで分": int((int(np.argmax(adv)) + 1) * 5),
                      "一度も利にならず": bool(fav.max() < 0.028)})
            for m in cfg["adverse_marks"]:
                k = int(np.argmax(adv >= m)) if (adv >= m).any() else -1
                r[f"{m}%逆行まで分"] = int((k + 1) * 5) if k >= 0 else np.nan
            for m in cfg["favorable_marks"]:
                k = int(np.argmax(fav >= m)) if (fav >= m).any() else -1
                r[f"{m}%順行まで分"] = int((k + 1) * 5) if k >= 0 else np.nan
            sm = sig_mat[seg]
            any_ = sm.any(axis=0)
            fired[j] = any_
            first = np.where(any_, sm.argmax(axis=0), -1)
            fmin[j] = np.where(any_, (first + 1) * 5, np.nan)
        recs.append(r)
    traj = pd.DataFrame(recs, index=tr.index)
    return traj, fired, fmin


def post_exit(tr, bars, cfg):
    """決済の後の追跡（節5）＝決済から episode_gap_h 時間、価格がどうなったかの記述。
    建値回帰＝決済しなければ損ゼロ級に戻れた玉（SHORT は安値が建値以下・LONG は高値が建値以上）。
    さらに逆行＝決済価格からさらに逆行した玉（この決済が損の拡大を止めた）。
    ⚠️ 決済より後のバーを読む＝記述専用（何が起きたかの観察）。売買判定・シグナルには使わない。"""
    idx = bars.index
    pos = {t: i for i, t in enumerate(idx)}
    hi, lo = bars.high.to_numpy(), bars.low.to_numpy()
    steps = int(cfg["episode_gap_h"] * 12)          # 5分足で episode_gap_h 時間ぶん
    recs = []
    for _, t in tr.iterrows():
        i1 = pos.get(t.exit_time)
        r = {"後_ok": False}
        if i1 is not None and i1 + 1 < len(idx):
            seg = np.arange(i1 + 1, min(i1 + 1 + steps, len(idx)))
            ep, xp = t.entry_price, t.exit_price
            if t.side == "LONG":
                fav_e = (hi[seg] / ep - 1) * 100          # 建値比の順行（戻り）
                adv_x = (1 - lo[seg] / xp) * 100          # 出口比のさらなる逆行
                back = hi[seg] >= ep
            else:
                fav_e = (1 - lo[seg] / ep) * 100
                adv_x = (hi[seg] / xp - 1) * 100
                back = lo[seg] <= ep
            k = int(np.argmax(back)) if back.any() else -1
            r.update({"後_ok": True,
                      "後_建値回帰": bool(back.any()),
                      "後_建値回帰まで分": int((k + 1) * 5) if k >= 0 else np.nan,
                      "後_建値比最大順行%": float(fav_e.max()),
                      "後_出口比さらに逆行%": float(adv_x.max())})
        recs.append(r)
    return pd.DataFrame(recs, index=tr.index)


# 入口フィルタ探索に足す玉間の特徴（entry 時点で因果的に確定している列だけ・2026-07-23 まこさん選択3）。
# ⛔「前玉は勝ち」「前玉より高い」等の勝敗依存は入れない＝前玉が保有中なら entry 時点で未確定（未来参照）。
NEI_FILTER_COLS = ["レンジ内で何番目", "前玉との価格差%", "前玉との時間間隔分", "前玉との時間間隔分_通し", "前玉entryから相場変化%"]


def neighbors(tr, cfg, bars):
    d = tr.sort_values("entry_time").copy()
    gap = d.entry_time.diff().dt.total_seconds() / 3600
    d["_ep"] = (gap.isna() | (gap > cfg["episode_gap_h"])).cumsum()
    o = pd.DataFrame(index=d.index)
    o["レンジ内で何番目"] = d.groupby("_ep").cumcount() + 1
    pe = d.groupby("_ep").entry_price.shift(1)
    o["前玉との価格差%"] = (d.entry_price / pe - 1) * 100
    o["前玉より高い"] = o["前玉との価格差%"] > 0
    o["前玉との時間間隔分"] = d.groupby("_ep").entry_time.diff().dt.total_seconds() / 60
    # エピソード（6時間区切り）を跨いだ通しの間隔＝「静けさの後の初回タッチ」はエピソード先頭に来て
    # 上の within-episode 間隔では NaN になる。フィルタ探索用に区切りなしの間隔も持つ（entry 時点で確定・因果 OK）。
    o["前玉との時間間隔分_通し"] = d.entry_time.diff().dt.total_seconds() / 60
    o["前玉は勝ち"] = d.groupby("_ep").is_win.shift(1)
    # 相場そのものの動き（自玉の entry 価格でなく 5分足 close・約定前に確定した1本前の値）
    d["_c0"] = bars.close.reindex(d.entry_time - pd.Timedelta("5min")).to_numpy()
    o["前玉entryから相場変化%"] = (d["_c0"] / d.groupby("_ep")["_c0"].shift(1) - 1) * 100
    o["前玉entryから相場が上昇"] = o["前玉entryから相場変化%"] > 0
    return o.reindex(tr.index)


# ══ 本体 ════════════════════════════════════════════════════════════════
def observe(trades_csv: str, bars_csv: str, title: str = "", config_path: str | None = None) -> None:
    cfg = load_config(config_path)
    p0, p1 = _resolve_period(cfg)
    tr_all = pd.read_csv(trades_csv, parse_dates=["entry_time", "exit_time"])
    tr_all = tr_all[(tr_all.entry_time >= p0) & (tr_all.entry_time <= p1)].copy()
    bars = pd.read_csv(bars_csv, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    # 期間の手前は指標の暖機（最長 SMA200×1d 等）に必要な分だけ持つ（5年全部だとメモリが数GBで走らない）。
    # 暖機はデータを狭める操作ではない＝観察対象の玉は period で決まり、暖機日数は出力に印字される。
    bars = bars.loc[p0 - pd.Timedelta(days=int(cfg["warmup_days"])):p1]

    src_txt = "config で指定" if (cfg.get("period") or {}).get("start") or (cfg.get("period") or {}).get("end") \
        else "periods.py の採点窓全部"
    print("#" * 100)
    print(f"# 建玉の観察と探索  {title}")
    print(f"# 期間: {p0.date()} 〜 {p1.date()}（{src_txt}・採点窓 {SCORE_START.date()}〜{SCORE_END.date()} の外は指定しても止まる）")
    print(f"# 売買記録 {len(tr_all)} 行 / side {tr_all.side.value_counts().to_dict()}")
    _cat = build_catalog(cfg)
    print(f"# 指標 {len(_cat)} 種 × 足 {cfg['timeframes']} = {len(_cat)*len(cfg['timeframes'])} 列 ＋ 需給3種")
    print(f"# 設定ファイル: {cfg['_source']}（走らせる前に編集して足す/減らす）")
    for k, v in cfg.items():
        if k != "_source":
            print(f"#    {k} = {v}")
    print(f"# 出す節: " + " | ".join(SECTIONS))
    _print_mode_info(cfg)
    print("# ⚠️ 疑似シミュ＝あたり付け専用。采否は実装して score.py の採点窓で決める。金額は出さない。")
    print("#" * 100)

    print("\n[指標を計算中...]", flush=True)
    feat, meta = build_features(bars, cfg)
    dem, cov = load_demand(bars.index)
    feat = pd.concat([feat, dem], axis=1)
    ng = [k for k, v in meta.items() if v[0] != "ok"]
    print(f"  指標 {feat.shape[1]} 列を用意（計算できず {len(ng)} 列）")
    for k in ng[:10]:
        _skip(f"{k}: {meta[k][1]}")
    print("  需給データの被覆:")
    for k, v in cov.items():
        print(f"     {k}: {v}")

    dir_map = {c: meta[c][1] for c in meta if meta[c][0] == "ok"}
    all_res = {}
    for s in ["SHORT", "LONG"]:
        sub = tr_all[tr_all.side == s]
        if not len(sub):
            print(f"\n★ side={s} は売買記録に0行"); continue
        print("\n\n" + "★" * 50)
        print(f"★ side = {s}   {len(sub)} 行")
        print("★" * 50)
        all_res[s] = _one_side(sub.copy(), bars, feat, dir_map, s, cfg) or []

    _summary(all_res)
    print("\n" + "#" * 100)
    print("# ⚠️ 疑似シミュ。スロット再回転（L-330）を再現していない＝実エンジンより良く出る。")
    print("#   采否は実装して score.py の採点窓で決める。")
    print("#" * 100)


def _one_side(tr, bars, feat, dir_map, side, cfg):
    tr["is_win"] = tr.net_usd > 0
    sign = -1.0 if side == "LONG" else 1.0
    tr["決済位置%"] = (tr.exit_price / tr.entry_price - 1) * 100 * sign
    if "ceil_type" not in tr.columns:
        tr["ceil_type"] = "不明"
    types = sorted(tr.ceil_type.dropna().unique())
    exits = tr.exit_reason.value_counts()
    print(f"  入口の型（売買記録から取得）: {types}")
    print(f"  出口理由（売買記録から取得）: {dict(exits)}")

    # ── 保有中シグナル＝指標 × 時間軸 × 閾値（逆行側と順行側を別プールで生成）──
    # side ごとに逆行方向を正へ揃えた上で、切る探索は逆行側プール・取る探索は順行側プールだけを使う。
    # 上下対を1つの探索空間に混ぜない（ロングとショートで玉の動きが違う＝片側ずつ最適化・まこさん 2026-07-21）。
    names, mats, sig_dirs = [], [], []
    for c, directional in dir_map.items():
        v = feat[c]
        if v.notna().sum() < 1000:
            continue
        vv = v * (-1.0 if (directional and side == "LONG") else 1.0)   # 逆行方向を正に揃える
        for q in cfg["quantiles"]:
            th = vv.quantile(q)
            if np.isfinite(th):
                names.append(f"{c} ≥ q{int(q*100)}")            # 逆行方向（切る側の材料）
                sig_dirs.append("adv")
                mats.append((vv >= th).fillna(False).to_numpy())
            tl = vv.quantile(round(1.0 - q, 4))
            if np.isfinite(tl):
                names.append(f"{c} ≤ q{int(round((1.0 - q) * 100))}")  # 順行方向（取る側の材料）
                sig_dirs.append("fav")
                mats.append((vv <= tl).fillna(False).to_numpy())
    sig_mat = np.column_stack(mats) if mats else np.zeros((len(bars), 0), bool)
    print(f"  保有中シグナル: 逆行側 {sig_dirs.count('adv')} 本（切る探索用）＋"
          f" 順行側 {sig_dirs.count('fav')} 本（取る探索用）＝別プール・混ぜない")

    traj, fired, fmin = trajectory(tr, bars, sig_mat, names, cfg)
    tr = pd.concat([tr.reset_index(drop=True), traj.reset_index(drop=True)], axis=1)
    tr = pd.concat([tr, post_exit(tr, bars, cfg)], axis=1)
    tr = pd.concat([tr, neighbors(tr, cfg, bars)], axis=1)
    # entry / 決済 時点の特徴（約定バーの1本前＝その時点で確定している値・H2）
    ecols = [c for c in feat.columns if feat[c].notna().sum() >= 1000]
    ef = feat.reindex(tr.entry_time - pd.Timedelta("5min"))[ecols]
    ef.index = tr.index
    tr = pd.concat([tr, ef], axis=1)
    xf = feat.reindex(tr.exit_time - pd.Timedelta("5min"))[ecols]
    xf.index = tr.index
    print("  entry/決済の瞬間の特徴は約定バーの1本前の確定値（約定より後の情報を含まない）")
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)

    # ── 0 母集団 ──
    _h(SECTIONS[0])
    print(pd.crosstab([tr.ceil_type, tr.exit_reason], tr.is_win)
          .rename(columns={False: "負け", True: "勝ち"}).to_string())

    # ── 1 機構別分解（TREND_CONT）──
    _h(SECTIONS[1])
    _mech_decompose(tr, side, cfg)

    # ── 2〜6: 出口ごと × 型ごと ──
    for ex in exits.index:
        for ty in types:
            m = (tr.exit_reason == ex) & (tr.ceil_type == ty)
            g = tr[tr.ceil_type == ty]
            _h(f"出口 {ex} × 型 {ty}   （{int(m.sum())} 行 / この型 {len(g)} 行）")
            if m.sum() < cfg["min_n"]:
                _skip(f"{int(m.sum())} 行しかない（{cfg['min_n']} 未満は数字を出さない）"); continue
            mm = m[tr.ceil_type == ty]

            _sub(SECTIONS[2] + "：この出口になる玉 vs 同じ型のそれ以外")
            r = rank_separation(g, mm, ecols, _tautology(cfg))
            print(r.to_string(index=False) if len(r) else "     分離する特徴なし")

            _sub(SECTIONS[3] + "：結果の記述（見分けには使えない）")
            base = ["最大逆行%", "最大順行%", "最大逆行まで分"] + [f"{x}%逆行まで分" for x in cfg["adverse_marks"]]
            print(tr.loc[m, base].median().round(2).to_frame("中央値").T.to_string())
            _sub(SECTIONS[3] + "：判断に使える材料＝建ててから何分以内に発火したか")
            for w in cfg["early_windows"]:
                e = pd.DataFrame(fmin[np.asarray(m)] <= w, columns=names)
                o = pd.DataFrame(fmin[np.asarray((tr.ceil_type == ty) & ~m)] <= w, columns=names)
                d = (e.mean() * 100 - o.mean() * 100).sort_values(ascending=False)
                t = pd.DataFrame({f"{w}分以内_この出口%": (e.mean() * 100).round(1),
                                  f"{w}分以内_それ以外%": (o.mean() * 100).round(1),
                                  "差": d.round(1)}).loc[d.index[:8]]
                print(f"\n     ── {w} 分以内 ── 上位8本")
                print(t.to_string())

            _sub(SECTIONS[4] + "：決済位置と保有時間")
            print(tr.loc[m, ["決済位置%", "hold_min"]].describe(percentiles=[.5, .9]).round(2).to_string())
            _sub(SECTIONS[4] + "：決済直前の指標（決済バーの1本前の確定値）で分離する特徴")
            r3 = rank_separation(xf[tr.ceil_type == ty], mm, ecols, _tautology(cfg))
            print(r3.to_string(index=False) if len(r3) else "     分離する特徴なし")

            _sub(SECTIONS[5] + f"：追跡 {cfg['episode_gap_h']} 時間（記述専用＝決済より後のバー・シグナルには使わない）")
            pm = tr.loc[m & tr["後_ok"]]
            if len(pm) < cfg["min_n"]:
                _skip(f"追跡できる玉が {len(pm)} 行（{cfg['min_n']} 未満は数字を出さない）")
            else:
                print("     建値回帰＝決済しなければ損ゼロ級に戻れた玉／出口比さらに逆行＝この決済が損の拡大を止めた玉")
                head = {"追跡玉数": len(pm),
                        "建値回帰率%": round(pm["後_建値回帰"].mean() * 100, 1),
                        "建値回帰まで分_中央値": float(pm["後_建値回帰まで分"].median()),
                        "建値比最大順行%_中央値": round(pm["後_建値比最大順行%"].median(), 2),
                        "出口比さらに逆行%_中央値": round(pm["後_出口比さらに逆行%"].median(), 2)}
                print("     " + pd.Series(head).to_string().replace("\n", "\n     "))
                rows5 = [{"刻み": f"出口からさらに {x}% 逆行", "該当率%": round((pm["後_出口比さらに逆行%"] >= x).mean() * 100, 1)}
                         for x in cfg["adverse_marks"]]
                rows5 += [{"刻み": f"建値から {x}% 順行へ回復", "該当率%": round((pm["後_建値比最大順行%"] >= x).mean() * 100, 1)}
                          for x in cfg["favorable_marks"]]
                print(pd.DataFrame(rows5).to_string(index=False))

            _sub(SECTIONS[6])
            ncols = ["レンジ内で何番目", "前玉との価格差%", "前玉との時間間隔分", "前玉entryから相場変化%"]
            print(pd.concat([tr.loc[m, ncols].median().rename("この出口"),
                             tr.loc[(tr.ceil_type == ty) & ~m, ncols].median().rename("それ以外")],
                            axis=1).round(2).to_string())
            r4 = rank_separation(g, mm, ncols, _tautology(cfg), top=6)
            if len(r4):
                print("\n     玉間の特徴の分離力（指標特徴と同じ物差し）")
                print("     " + r4.to_string(index=False).replace("\n", "\n     "))
            for flag in ["前玉より高い", "前玉は勝ち"]:
                s2 = g.dropna(subset=[flag])
                if len(s2) < cfg["min_n"]:
                    _skip(f"{flag} を判定できる玉が少ない"); continue
                print(f"\n     {flag} 別のこの出口になる率(%)")
                print((s2.groupby(flag).apply(lambda x: (x.exit_reason == ex).mean() * 100)
                       ).round(1).to_string())

    # ── 7 巻き込み ──
    _h(SECTIONS[7])
    print("  損切りを手前へ動かすと、その線に触れた玉は勝ち負けに関わらず全部切れる。")
    print("  負けだけを切ることは原理的にできないので、両方を同じ表に出す。")
    ok = tr[tr._ok]
    for ty in types:
        _sub(f"型 {ty}")
        g = ok[ok.ceil_type == ty]
        if len(g) < cfg["min_n"]:
            _skip(f"{len(g)} 行しかない"); continue
        rows = []
        for x in cfg["sl_grid"]:
            cut = g["最大逆行%"] >= x
            rows.append({"X%": x, "切る負け": int((cut & ~g.is_win).sum()), "切る勝ち": int((cut & g.is_win).sum()),
                         "負けの何%を切る": round((cut & ~g.is_win).sum() / max((~g.is_win).sum(), 1) * 100, 1),
                         "勝ちの何%を切る": round((cut & g.is_win).sum() / max(g.is_win.sum(), 1) * 100, 1),
                         "負けの逆行を平均何%浅く": round((g.loc[cut & ~g.is_win, "決済位置%"] - x).mean(), 2)
                         if (cut & ~g.is_win).any() else np.nan,
                         "勝ちを切ると失う順行%": round(g.loc[cut & g.is_win, "最大順行%"].mean(), 2)
                         if (cut & g.is_win).any() else np.nan})
        print(pd.DataFrame(rows).to_string(index=False))

    # ── 8 探索 ──
    _h(SECTIONS[8])
    # 入口フィルタ／セット探索のプール＝指標特徴＋玉間の因果 OK 列（NEI_FILTER_COLS・勝敗依存は入れない）
    fcols = ecols + [c for c in NEI_FILTER_COLS if c in tr.columns]
    return _search(tr, fmin, names, sig_dirs, fcols, side, cfg, types)


def _mech_decompose(tr, side, cfg):
    """節1＝TREND_CONT を「どの撤退機構が切ったか」で分ける（概算）。
    分類は 価格水準（建値からの決済位置%）と保有時間からの再導出＝実装の分岐ログではない。
    境界の玉は誤分類しうる（その注記ごと読む）。閾値の定数は e37_scalp から import（手打ちしない）。"""
    tc = tr[tr.exit_reason == "TREND_CONT"]
    if not len(tc):
        _skip("TREND_CONT の玉が 0 行（この side には撤退機構の玉が無い）"); return
    if side != "SHORT":
        _skip(f"side={side} は TREND_CONT {len(tc)} 行あるが撤退機構はショート用＝分解しない"); return
    try:
        from e37_scalp import (V53_FAST_MIN, V53_ADV_PCT, V59_WAIT_MIN,
                               V59_FLAT_WIN_MIN, V59_DOWN_ADV_PCT, V59_FLAT_ADV_PCT)
    except Exception as e:
        _skip(f"e37_scalp の定数を import できない: {e}"); return
    TOL = 0.02   # 水準一致の許容%（stop はギャップで水準より不利側に約定しうる＝下側のみ緩める・診断専用）
    print(f"  分類規則（概算・上から順に判定）: "
          f"v53={{flat_up ∩ 未搭乗 ∩ 保有≤{V53_FAST_MIN}分 ∩ 決済位置≥+{V53_ADV_PCT}−{TOL}%}} → "
          f"v59_down={{down ∩ 保有≥{V59_WAIT_MIN}分 ∩ 決済位置≥+{round(V59_DOWN_ADV_PCT,3)}−{TOL}%}} → "
      f"v59_flat={{flat_up ∩ 保有{V59_WAIT_MIN}〜{V59_FLAT_WIN_MIN}分 ∩ 決済位置≥+{round(V59_FLAT_ADV_PCT,3)}−{TOL}%}} → "
          f"残り=その他（uptrend 畳み・v50 待機後 等）")
    tc = tc.copy()
    def _cls(t):
        p = t["決済位置%"]
        if t.ceil_type == "flat_up" and t.hold_min <= V53_FAST_MIN \
                and bool(t.get("一度も利にならず", False)) and p >= V53_ADV_PCT - TOL:
            return "v53 幾何早切り"
        if t.ceil_type == "down" and t.hold_min >= V59_WAIT_MIN and p >= V59_DOWN_ADV_PCT - TOL:
            return "v59 急騰早切り(down)"
        if t.ceil_type == "flat_up" and V59_WAIT_MIN <= t.hold_min <= V59_FLAT_WIN_MIN \
                and p >= V59_FLAT_ADV_PCT - TOL:
            return "v59 急騰早切り(flat)"
        return "その他(uptrend畳み/v50等)"
    tc["機構"] = tc.apply(_cls, axis=1)
    for ty in sorted(tc.ceil_type.dropna().unique()):
        _sub(f"型 {ty}（TREND_CONT {int((tc.ceil_type == ty).sum())} 行）")
        g = tc[tc.ceil_type == ty]
        agg = g.groupby("機構").agg(件数=("機構", "size"), 勝ち=("is_win", "sum"),
                                    決済位置pct中央値=("決済位置%", "median"),
                                    保有分中央値=("hold_min", "median"))
        agg["割合%"] = (agg.件数 / len(g) * 100).round(1)
        print(agg.round(2).to_string())
    print("  ⚠️ 概算＝価格水準と保有時間からの再導出。実装の分岐ログではない＝境界の玉は誤分類しうる。金額は出さない。")


def _search(tr, fmin, names, sig_dirs, ecols, side, cfg, types):
    """★side × 型 の分岐ごとに、切る / 取る / 入らない / セット を別々の探索で回す
    （ショート×down / ショート×flat_up / ロング×down / ロング×flat_up＝計4分岐・混ぜない）。
    切る探索は逆行側プール・取る探索は順行側プールのシグナルだけを使う。
    前半で探索し後半で確認する（L-267）。目的関数の単位は % の合計（金額は出さない）。正＝改善方向。"""
    try:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
    except Exception as e:
        _skip(f"optuna が使えない: {e}"); return []
    ok = tr._ok.to_numpy()
    if ok.sum() < 100:
        _skip(f"軌跡を再現できた玉が {int(ok.sum())} 行"); return []
    mid = tr.entry_time.quantile(0.5)
    first = (tr.entry_time <= mid).to_numpy() & ok
    second = (tr.entry_time > mid).to_numpy() & ok
    print(f"  探索 {tr.entry_time.min().date()}〜{mid.date()} {int(first.sum())}行 ／"
          f" 確認 {mid.date()}〜{tr.entry_time.max().date()} {int(second.sum())}行")
    pool_adv = [i for i, d_ in enumerate(sig_dirs) if d_ == "adv"]
    pool_fav = [i for i, d_ in enumerate(sig_dirs) if d_ == "fav"]
    if not pool_adv or not pool_fav:
        _skip("シグナルのプール（逆行側/順行側）が空"); return []
    adv = tr["最大逆行%"].to_numpy()
    fav = tr["最大順行%"].to_numpy()
    win = tr.is_win.to_numpy()
    exitp = tr["決済位置%"].to_numpy()
    ev = {c: pd.to_numeric(tr[c], errors="coerce").to_numpy(dtype=float) for c in ecols}

    # 切る＝損失最小化: シグナル発火 ∩ 逆行 X% で切る
    def sc_cut(mask, si, wait, wm, x):
        f = fmin[:, si]
        hit = mask & (f >= wait) & (f <= wm) & (adv >= x)
        if not hit.any():
            return 0.0, 0, 0
        gain = np.nansum(exitp[hit & ~win] - x)      # 負けの逆行が浅くなった分
        loss = np.nansum(fav[hit & win])             # 勝ちを切って失った順行
        return float(gain - loss), int((hit & ~win).sum()), int((hit & win).sum())

    # 入らない＝入口フィルタ: entry 直前の特徴が閾値の側なら建てない（閾値は前半の分布で決める）
    def _entry_th(col, q):
        base = ev[col][first]
        return np.nanquantile(base, q) if np.isfinite(base).any() else np.nan

    def sc_entry(mask, col, q, hi):
        th = _entry_th(col, q)
        if not np.isfinite(th):
            return 0.0, 0, 0
        v = ev[col]
        skip = mask & ((v >= th) if hi else (v <= th))
        if not skip.any():
            return 0.0, 0, 0
        gain = np.nansum(exitp[skip])                # 建てなければ避けた損（正）と失った勝ち（負）
        return float(gain), int((skip & ~win).sum()), int((skip & win).sum())

    # セット＝入口フィルタ＋切るの同時
    def sc_set(mask, col, q, hi, si, wait, wm, x):
        th = _entry_th(col, q)
        if not np.isfinite(th):
            return 0.0, 0, 0, 0, 0
        v = ev[col]
        skip = mask & ((v >= th) if hi else (v <= th))
        g1 = float(np.nansum(exitp[skip])) if skip.any() else 0.0
        s2, l2, w2 = sc_cut(mask & ~skip, si, wait, wm, x)
        return g1 + s2, int((skip & ~win).sum()), int((skip & win).sum()), l2, w2

    def _study(objective):
        st = optuna.create_study(direction="maximize",
                                 sampler=optuna.samplers.TPESampler(seed=42))
        st.optimize(objective, n_trials=cfg["optuna_trials"], show_progress_bar=False)
        return sorted(st.trials, key=lambda z: -(z.value if z.value is not None else -1e9))[:10]

    # ★分岐＝side × 入口の型。この関数は1つの side を受け取るので、ここでは型ごとに別探索を回す
    #  （観察の節0〜5と同じ4分岐。混ぜて最適化しない）。
    out = []
    for ty in types:
        tmask = (tr.ceil_type == ty).to_numpy()
        f1, f2 = first & tmask, second & tmask
        _sub(f"探索の分岐: side {side} × 型 {ty}（前半 {int(f1.sum())} 行 / 後半 {int(f2.sum())} 行）")
        if f1.sum() < cfg["min_n"] or f2.sum() < cfg["min_n"]:
            _skip(f"この分岐の玉が少ない（前半{int(f1.sum())}/後半{int(f2.sum())}・{cfg['min_n']} 未満は探索しない）")
            continue
        for mode in cfg["search_modes"]:
            rows = []
            if mode == "exit_cut":
                _sub(f"  [{side}×{ty}] 探索A 切る（損失最小化）＝逆行側シグナル × 待ち × 窓 × SL%")
                top = _study(lambda t: sc_cut(f1, pool_adv[t.suggest_int("signal", 0, len(pool_adv) - 1)],
                                              t.suggest_categorical("wait", cfg["wait_grid"]),
                                              t.suggest_categorical("window", cfg["early_windows"]),
                                              t.suggest_categorical("sl_pct", cfg["sl_grid"]))[0])
                for t in top:
                    p = t.params
                    si = pool_adv[p["signal"]]
                    s1, l1, w1 = sc_cut(f1, si, p["wait"], p["window"], p["sl_pct"])
                    s2, l2, w2 = sc_cut(f2, si, p["wait"], p["window"], p["sl_pct"])
                    rows.append({"シグナル": names[si], "待ち分": p["wait"], "窓分": p["window"],
                                 "SL%": p["sl_pct"], "前半_正味%": round(s1, 1), "前半_負け/勝ち": f"{l1}/{w1}",
                                 "後半_正味%": round(s2, 1), "後半_負け/勝ち": f"{l2}/{w2}"})
            elif mode == "entry_filter":
                _sub(f"  [{side}×{ty}] 探索C 入らない（入口フィルタ）＝entry直前の特徴 × 分位 × 上下側")
                top = _study(lambda t: sc_entry(f1, ecols[t.suggest_int("col", 0, len(ecols) - 1)],
                                                t.suggest_categorical("q", cfg["quantiles"]),
                                                t.suggest_categorical("hi", [True, False]))[0])
                for t in top:
                    p = t.params
                    col = ecols[p["col"]]
                    s1, l1, w1 = sc_entry(f1, col, p["q"], p["hi"])
                    s2, l2, w2 = sc_entry(f2, col, p["q"], p["hi"])
                    rows.append({"特徴": col, "側": ("≥" if p["hi"] else "≤") + f"q{int(p['q']*100)}",
                                 "前半_正味%": round(s1, 1), "前半_消す負け/勝ち": f"{l1}/{w1}",
                                 "後半_正味%": round(s2, 1), "後半_消す負け/勝ち": f"{l2}/{w2}"})
            elif mode == "set":
                _sub(f"  [{side}×{ty}] 探索D セット（入口フィルタ＋切るの同時）")
                top = _study(lambda t: sc_set(f1, ecols[t.suggest_int("col", 0, len(ecols) - 1)],
                                              t.suggest_categorical("q", cfg["quantiles"]),
                                              t.suggest_categorical("hi", [True, False]),
                                              pool_adv[t.suggest_int("signal", 0, len(pool_adv) - 1)],
                                              t.suggest_categorical("wait", cfg["wait_grid"]),
                                              t.suggest_categorical("window", cfg["early_windows"]),
                                              t.suggest_categorical("sl_pct", cfg["sl_grid"]))[0])
                for t in top:
                    p = t.params
                    col = ecols[p["col"]]
                    si = pool_adv[p["signal"]]
                    s1, a1, b1, c1, d1 = sc_set(f1, col, p["q"], p["hi"], si, p["wait"], p["window"], p["sl_pct"])
                    s2, a2, b2, c2, d2 = sc_set(f2, col, p["q"], p["hi"], si, p["wait"], p["window"], p["sl_pct"])
                    rows.append({"入口": f"{col} {'≥' if p['hi'] else '≤'}q{int(p['q']*100)}",
                                 "シグナル": names[si], "待ち/窓": f"{p['wait']}/{p['window']}", "SL%": p["sl_pct"],
                                 "前半_正味%": round(s1, 1), "後半_正味%": round(s2, 1),
                                 "後半_消す負け/勝ち": f"{a2}/{b2}", "後半_切る負け/勝ち": f"{c2}/{d2}"})
            else:
                _skip(f"知らない search_mode: {mode}"); continue
            df = pd.DataFrame(rows).drop_duplicates() if rows else pd.DataFrame()
            out.append((ty, mode, df))
            if len(df):
                print("\n  前半で探索した上位10（重複除去後・後半は同じ設定をそのまま当てた確認）")
                print(df.to_string(index=False))
            else:
                _skip("候補が1件も残らなかった")
            if mode == "entry_filter":
                print("  ⚠️ 入口フィルタは件数を減らす。スキャルの役割（件数/日≥5）を割る候補は正味が良くても採らない。")

    print("\n  ⚠️ 前半で良くて後半で崩れる行は、前半に合わせただけ（L-267）。両方でプラスの行だけを候補にする。")
    print("  ⚠️ ここは疑似シミュ。スロット再回転（L-330）を再現しない。候補が出ても采否は実装して score.py の採点窓で決める。")
    return out


def _summary(all_res: dict) -> None:
    """結果サマリの自動生成（手書きなし）。各分岐×モードの上位10（重複除去後）から
    前半・後半の両方で正味プラスの行だけを機械抽出して1枚に出す。CC の要約を挟まない。"""
    _h(SECTIONS[9])
    print("  機械集計＝各分岐×モードの上位10のうち、前半と後半の両方で正味プラスの行。解釈と採否はまこさん＋score.py。")
    for side, res in all_res.items():
        if not res:
            print(f"\n  side {side}: 探索なし"); continue
        for ty, mode, df in res:
            label = f"{side} × {ty} × {MODE_JP.get(mode, mode)}"
            if df is None or not len(df):
                print(f"  {label}: 候補 0 行"); continue
            c1 = next(c for c in df.columns if c.startswith("前半_正味"))
            c2 = next(c for c in df.columns if c.startswith("後半_正味"))
            both = df[(df[c1] > 0) & (df[c2] > 0)]
            if not len(both):
                print(f"  {label}: 両半期プラス 0 行 ＝ 前半に合わせただけの疑い（候補にしない）")
            else:
                best = both.sort_values(c2, ascending=False).iloc[0]
                desc = " / ".join(f"{k}={best[k]}" for k in both.columns)
                print(f"  {label}: 両半期プラス {len(both)} 行。後半最良 → {desc}")
    print("\n  ⚠️ 疑似シミュの機械集計＝候補の提示まで。採否は実装して score.py の採点窓で決める。")


def plan(trades_csv: str, bars_csv: str, title: str = "", config_path: str | None = None) -> None:
    """検証計画の自動生成＝検証する内容・項目・条件を実値から出す1枚。検証する前にまこさんへ提出する。
    CC は計画を手書きしない。足す/減らすは observe_config.json を編集して再生成する。
    本走の出力先頭にも同じ設定が印字される＝計画と実行を機械的に突き合わせられる。"""
    import pathlib
    cfg = load_config(config_path)
    p0, p1 = _resolve_period(cfg)
    tr = pd.read_csv(trades_csv, parse_dates=["entry_time", "exit_time"])
    tr = tr[(tr.entry_time >= p0) & (tr.entry_time <= p1)]
    cat = build_catalog(cfg)
    _h(f"検証計画（自動生成・実値ベース・手書きなし） {title}")
    print(f"  対象の売買記録: {trades_csv}（期間内 {len(tr)} 行）")
    print(f"  5分足: {bars_csv}（実在 {pathlib.Path(bars_csv).exists()}）")
    print(f"  期間: {p0.date()} 〜 {p1.date()}（採点窓の範囲内のみ・periods.py）／ 指標の暖機 {cfg['warmup_days']} 日")
    mid = tr.entry_time.quantile(0.5) if len(tr) else None
    if mid is not None:
        print(f"  探索の分割: 前半 {p0.date()}〜{mid.date()}＝探索 ／ 後半 〜{p1.date()}＝同じ設定を当てる確認（L-267）")
    print(f"  出口理由（実データ）: {tr.exit_reason.value_counts().to_dict()}")

    print("\n  ── 検証の分岐（side × 入口の型・実データの件数・混ぜない）──")
    for s in sorted(tr.side.dropna().unique()):
        sub = tr[tr.side == s]
        for ty in sorted(sub.ceil_type.dropna().unique()):
            g = sub[sub.ceil_type == ty]
            f1 = int((g.entry_time <= mid).sum()); f2 = len(g) - f1
            run = "観察＋探索" if min(f1, f2) >= cfg["min_n"] else f"観察のみ（前半{f1}/後半{f2}＝min_n {cfg['min_n']} 未満で探索しない）"
            print(f"     {s} × {ty}: {len(g)} 行 → {run}")

    print("\n  ── 出す節（固定・減らせない）──")
    for sct in SECTIONS:
        print(f"     {sct}")

    print(f"\n  ── 観察に当てる指標カタログ（全 {len(cat)} 種 × 足 {cfg['timeframes']}"
          f" = {len(cat)*len(cfg['timeframes'])} 列 ＋ 需給 {list(_DEMAND_FILES)}・呼び出し側は減らせない）──")
    names_all = [n for n, _, _ in cat]
    for i in range(0, len(names_all), 5):
        print("     " + " | ".join(names_all[i:i + 5]))

    print(f"\n  ── 保有中シグナル（機械生成・見込み）──")
    print(f"     逆行側（切る探索用）と順行側（取る探索用）を別プールで各 指標列×分位{len(cfg['quantiles'])} 本＝混ぜない")

    _print_mode_info(cfg)

    print("\n  ── 探索の条件（config の実値）──")
    for k in ("search_modes", "quantiles", "sl_grid", "wait_grid",
              "early_windows", "adverse_marks", "favorable_marks", "optuna_trials", "episode_gap_h", "min_n"):
        print(f"     {k} = {cfg[k]}")
    print("     ※ sl_grid＝エントリー価格からの% ／ adverse_marks・favorable_marks＝逆行/順行の記述の刻み（探索の値ではない）")

    print("\n  ⚠️ この計画の外は検証しない。項目を足す/減らすのは observe_config.json を編集して計画を再生成してから。")
    print("  ⚠️ まこさんの OK が出たら本走する。本走の先頭に同じ設定が印字される＝計画との差分は突き合わせで見える。")


# ══ 自己検査 ════════════════════════════════════════════════════════════
def selftest() -> None:
    """この道具が守ると言っていることを機械で確かめる。まこさんはこれを叩けばよい。"""
    ng = []
    import inspect
    src = inspect.getsource(sys.modules[__name__])
    sig = inspect.signature(observe)
    for bad in ("start", "end", "side", "entry_features", "hold_signals", "types", "exit_reason"):
        if bad in sig.parameters:
            ng.append(f"observe() が {bad} を受け取れてしまう（呼び出し側が絞れる）")
    # 期間の出所も AST で見る（コメントアウトしても文字列は残るので一致検査では素通りする）
    import ast as _ast
    _tree0 = _ast.parse(src)
    _from_periods = {n for node in _ast.walk(_tree0) if isinstance(node, _ast.ImportFrom)
                     and node.module == "periods" for n in [a.name for a in node.names]}
    for need in ("SCORE_START", "SCORE_END"):
        if need not in _from_periods:
            ng.append(f"{need} を periods.py から import していない（手打ちの疑い）")
    for node in _ast.walk(_tree0):   # 期間を Timestamp リテラルで作っていないか
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Attribute) \
                and node.func.attr == "Timestamp" and node.args \
                and isinstance(node.args[0], _ast.Constant) and isinstance(node.args[0].value, str):
            ng.append(f"期間を手打ちしている: pd.Timestamp('{node.args[0].value}')")
    cfg = load_config()
    cat = build_catalog(cfg)
    if len(cat) < 40:
        ng.append(f"指標カタログが {len(cat)} 種しかない")
    if len(cfg["timeframes"]) < 3 or "1m" in cfg["timeframes"]:
        ng.append(f"足が不正: {cfg['timeframes']}")
    for key in ("quantiles", "sl_grid", "favorable_marks", "wait_grid", "early_windows"):
        if key not in cfg or len(cfg[key]) < 3:
            ng.append(f"{key} の候補が足りない（probe は広く試す）")
    if "_source" not in cfg:
        ng.append("設定の出所が記録されていない")
    # 探索の分岐＝空でない・未知のモードが無い（順番に1系統ずつ＝1つでもよい・まこさん 2026-07-21）
    modes = set(cfg.get("search_modes", []))
    if not modes:
        ng.append("search_modes が空＝何も検証しない計画になっている")
    unknown = modes - set(MODE_INFO)
    if unknown:
        ng.append(f"search_modes に定義の無いモード {sorted(unknown)}（MODE_INFO に無い＝計画に説明が出ない）")
    # ⚠️ 実装の有無は _search のソースだけを見る（src 全体だと selftest 自身の検査文字列に自己一致する）
    _src_srch = inspect.getsource(_search)
    for fn_need in ("sc_cut", "sc_entry", "sc_set"):
        if f"def {fn_need}" not in _src_srch:
            ng.append(f"探索 {fn_need} が実装されていない")
    # 建値% TP の探索は削除済み（まこさん指示 2026-07-21＝TP は現行ロジックのまま・宣言と実装の一致を機械担保）
    if "sc_take" in _src_srch:
        ng.append("建値% TP の探索 sc_take が残っている（TP を変えろという指示は無い）")
    # ⚠️ 以下は selftest 自身の検査文字列に一致しないよう、対象関数のソースだけを見る
    #   （src 全体への文字列一致は自分の検査文に当たって番人が死ぬ＝2026-07-21 実測）
    src_one = inspect.getsource(_one_side)
    src_search = inspect.getsource(_search)
    if "≤ q" not in src_one:
        ng.append("シグナルの順行側プールを生成していない（切る側だけになっている）")
    # ★探索の分岐＝side×型（観察と同じ4分岐）で回っているか
    if "for ty in types" not in src_search or "ceil_type" not in src_search:
        ng.append("探索が型（down/flat_up）で分岐していない＝side×型の4分岐になっていない")
    # ★切る=逆行側プール・取る=順行側プールの分離があるか（上下対を1つの探索空間に混ぜない）
    #   定義だけでなく「選択の瞬間」がプール経由かまで見る（定義が残ったまま混ぜる改変を弾く）
    if "pool_adv[t.suggest_int" not in src_search:
        ng.append("切る探索がシグナルの逆行側プールから選んでいない（向きの分離が無い）")
    # entry/決済の特徴が約定バーの終値（約定より後の情報）を含んでいないか
    if 'tr.entry_time - pd.Timedelta("5min")' not in src_one:
        ng.append("entry の特徴が約定バーの終値を含む（1本前の確定値を使っていない）")
    if 'tr.exit_time - pd.Timedelta("5min")' not in src_one:
        ng.append("決済の瞬間の特徴が無い か 決済バーの終値を含む")
    # 玉間の「相場が上がったか」が相場（bars）を見ているか
    if "bars" not in inspect.signature(neighbors).parameters:
        ng.append("neighbors が bars を受けない＝相場変化を自玉の価格で代用している")
    # 期間＝採点窓の外（学習窓・封印）を指定したら止まるか（機能テスト）
    try:
        _resolve_period({"period": {"start": "2021-01-01", "end": None}})
        ng.append("採点窓の外の期間（学習窓）が通ってしまう")
    except SystemExit:
        pass
    # ★計画と結果の自動生成（まこさん指示 2026-07-21＝計画を検証前に提出・結果も手書きなし）
    if "plan" not in globals() or not callable(globals().get("plan")):
        ng.append("検証計画の自動生成 plan が無い")
    else:
        src_plan = inspect.getsource(plan)
        if "検証計画" not in src_plan or "names_all" not in src_plan:
            ng.append("plan が指標カタログの全列挙を印字していない（計画に載らない項目ができる）")
    if "_summary" not in globals() or not callable(globals().get("_summary")):
        ng.append("結果サマリの自動生成 _summary が無い")
    else:
        src_sum = inspect.getsource(_summary)
        if "両半期プラス" not in src_sum:
            ng.append("結果サマリが両半期プラスの機械抽出をしていない")
    if "_summary(all_res)" not in inspect.getsource(observe):
        ng.append("observe が結果サマリを呼んでいない（結果の要約が CC の手書きに戻る）")
    if "for k, v in cfg.items()" not in inspect.getsource(observe):
        ng.append("使った設定を出力に印字していない（狭めても見えない）")
    if not TAUTOLOGY_COLS:
        ng.append("結果の言い換えの隔離が空")
    d = pd.DataFrame({"最大逆行%": [1, 2, 3] * 10, "普通の特徴": [1, 2, 3] * 10})
    m = pd.Series([True, False, True] * 10)
    if "最大逆行%" in set(rank_separation(d, m, list(d.columns))["特徴"] if len(rank_separation(d, m, list(d.columns))) else []):
        ng.append("結果の言い換えが分離力の順位表に入っている")
    # 書き出し・score 呼びは AST の実呼び出しで見る（文字列一致だと自分の説明文に当たる）
    import ast
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ("to_csv", "to_parquet", "write_sidecar"):
            ng.append(f"read-only 診断なのに書き出しを呼んでいる: {node.func.attr}")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in node.names] + ([node.module] if isinstance(node, ast.ImportFrom) else [])
            if any(m and m.split(".")[0] == "score" for m in mods):
                ng.append("read-only 診断なのに score を import している")
    # ★節5 決済の後（2026-07-23 追加）＝追跡が配線され、かつ記述専用（探索に混ぜない＝決済後の情報で候補を選ばない）
    if "def post_exit" not in src:
        ng.append("決済の後の追跡 post_exit が無い")
    if "post_exit(tr, bars, cfg)" not in inspect.getsource(_one_side):
        ng.append("決済の後の追跡が observe に配線されていない")
    if "後_" in inspect.getsource(_search):
        ng.append("決済の後の列（後_*）が探索に混ざっている（決済後の情報で候補を選んではいけない）")
    # ★入口フィルタのプール拡張（2026-07-23 まこさん選択3）＝玉間の因果 OK 列が配線され、勝敗依存の列が混ざっていない
    if "NEI_FILTER_COLS" not in inspect.getsource(_one_side):
        ng.append("玉間の特徴が入口フィルタ探索のプールに配線されていない")
    for bad_col in ("前玉は勝ち", "前玉より高い", "前玉entryから相場が上昇"):
        if bad_col in NEI_FILTER_COLS:
            ng.append(f"入口フィルタのプールに勝敗/bool 依存の列 {bad_col}（前玉が保有中なら entry 時点で未確定＝未来参照の疑い）")
    if "前玉との時間間隔分_通し" not in inspect.getsource(neighbors):
        ng.append("エピソード跨ぎの通し間隔が neighbors に無い（静けさの後の初回タッチが NaN で探索から漏れる）")
    # ★節1 機構別分解（2026-07-23 追加）＝配線され、閾値は e37_scalp から import（手打ち禁止）
    if "_mech_decompose" not in inspect.getsource(_one_side):
        ng.append("機構別分解が observe に配線されていない")
    if "from e37_scalp import" not in inspect.getsource(_mech_decompose):
        ng.append("機構別分解の閾値が e37_scalp から import されていない（手打ちの疑い）")
    for need in SECTIONS:
        if need not in src:
            ng.append(f"節が実装されていない: {need}")
    print("=" * 80)
    print("observe_diag 自己検査")
    print("=" * 80)
    print(f"  指標カタログ {len(cat)} 種 × 足 {cfg['timeframes']} = {len(cat)*len(cfg['timeframes'])} 列")
    p0, p1 = _resolve_period(cfg)
    print(f"  期間 {p0.date()} 〜 {p1.date()}（採点窓 {SCORE_START.date()}〜{SCORE_END.date()} の範囲内のみ・periods.py）")
    print(f"  節 {len(SECTIONS)} / 分位 {cfg['quantiles']} / SL候補 {cfg['sl_grid']}（エントリー価格からの%）")
    print(f"  探索 {cfg.get('search_modes')} × side×型の分岐 / 切る探索＝逆行側プールのみ / 建値%TP探索なし")
    print(f"  設定ファイル {cfg['_source']}")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        raise SystemExit(1)
    print("  ✅ 全部 pass")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        import argparse
        ap = argparse.ArgumentParser(description="建玉の観察と探索（read-only 診断・売買記録CSVを書かない）")
        ap.add_argument("trades_csv", help="実エンジンが出した売買記録CSV")
        ap.add_argument("bars_csv", help="5分足CSV（Binance Spot 正本）")
        ap.add_argument("--plan", action="store_true",
                        help="検証計画だけを自動生成して印字（本走しない・まこさんへ提出する1枚）")
        ap.add_argument("--config", default=None, help="observe_config.json のパス（既定は同ディレクトリ）")
        ap.add_argument("--title", default="")
        a = ap.parse_args()
        if a.plan:
            plan(a.trades_csv, a.bars_csv, a.title, a.config)
        else:
            observe(a.trades_csv, a.bars_csv, a.title, a.config)

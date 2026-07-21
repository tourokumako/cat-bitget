#!/usr/bin/env python3
"""plot_trades.py — 売買記録CSVを価格チャートに重ねて視覚化（read-only・net計算/審判に不関与）。

実際にどこで建てて・どこで・どの理由で決済したかを目で確認するための可視化ツール。
score.py/eval_engine には一切触れない（CSVを読んで描くだけ）。

使い方:
  python3 plot_trades.py <trades.csv> --price <price.csv> --start 2025-10-01 --end 2025-10-08 [--out out.png] [--side LONG|SHORT]

表示:
  - 灰線 = 5分足 close
  - 建玉マーカー（entry_price）: LONG=緑●（上向き）/ SHORT=橙●（下向き）
  - 決済マーカー（exit_price）: 利確系(EDGE_TP/CENTER_LOCK/PARTIAL_TP)=水色▽ / 時間切れ(TIME_EXIT)=灰×
    建値撤退(BE_EXIT)=黒□ / その他=赤▽
  - 建玉→決済を細線で結ぶ（緑=その玉net+ / 赤=net−）＝勝ち負けが一目で分かる
"""
import argparse
import pathlib
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager

# 日本語フォント（豆腐文字回避・macOS Hiragino 系を優先・無ければ英字フォント）
for _jp in ["Hiragino Sans", "Hiragino Maru Gothic Pro", "YuGothic", "Arial Unicode MS", "AppleGothic"]:
    if _jp in {f.name for f in font_manager.fontManager.ttflist}:
        plt.rcParams["font.family"] = _jp
        break
plt.rcParams["axes.unicode_minus"] = False  # マイナス記号の豆腐回避

# 色 = 方向（LONG=青 / SHORT=赤）。形 = イベント種別。
SIDE_COLOR = {"LONG": "#1565c0", "SHORT": "#d32f2f"}
TP_REASONS = {"EDGE_TP", "CENTER_LOCK", "PARTIAL_TP"}   # 利確系はまとめて TP=▼


def exit_marker(reason: str) -> str:
    """出口理由 → マーカー形（まこさん指定: TP=▼ / TimeExit=■ / SL=✗ / その他=◆）。"""
    r = str(reason).upper()
    if reason in TP_REASONS:
        return "v"            # TP ▼
    if r == "TIME_EXIT":
        return "s"            # TimeExit ■
    if "SL" in r:
        return "x"            # SL ✗
    return "D"                # その他 ◆（BE_EXIT / FORCE_CLOSE_EOD 等）


# リポジトリ既定パス（どの検証でも 1コマンドで出せるよう既定化・2026-06-20 正式フォーマット）
ROOT = pathlib.Path(__file__).resolve().parents[2]   # bitget-python-sdk-api/
DEFAULT_PRICE = ROOT / "data" / "BTCUSDT-5m-2021-04-01_2026-05-31_V9FULL_safe.csv"  # 全期間 Binance Spot 正本（2026-05-31 まで＝採点窓を覆う。旧 _03-31_1826d 版は 2026-03-31 で切れ、採点窓後半の週次PNGが作れず report M節が exit 2 になっていた＝まこさん指示で差し替え 2026-07-21）
RATCHET = ROOT / "results" / "priority_rebuild" / "ratchet"   # 売買記録の置き場
VIZ_DIR = ROOT / "results" / "priority_rebuild" / "viz"       # チャートPNGの置き場（クリックで開ける）

import sys                                                    # noqa: E402
sys.path.insert(0, str(ROOT / "scripts" / "priority_rebuild"))
import ratchet_io                                             # noqa: E402  出力の上書き防止（書く前に既存を archive へ・全戦略汎用）


def _resolve_trades(name: str) -> pathlib.Path:
    """売買記録CSVを解決: フルパス → そのまま / 素のファイル名 → ratchet 直下を探す。"""
    p = pathlib.Path(name)
    if p.exists():
        return p
    cand = RATCHET / name
    if cand.exists():
        return cand
    if not name.endswith(".csv") and (RATCHET / f"{name}.csv").exists():
        return RATCHET / f"{name}.csv"
    raise SystemExit(f"売買記録CSVが見つかりません: {name}（フルパス or {RATCHET} 直下の名前で指定）")


def main():
    ap = argparse.ArgumentParser(description="売買記録を価格チャートに重ねて視覚化（共通フォーマット・read-only）")
    ap.add_argument("trades", help="売買記録CSV（フルパス or ratchet 直下の名前。例: trades_e35_oscillation_5m_iter12_score.csv）")
    ap.add_argument("--price", default=None, help=f"価格CSV（既定={DEFAULT_PRICE.name}）")
    ap.add_argument("--start", default=None, help="表示開始 YYYY-MM-DD（省略時=データ末尾から1週間）")
    ap.add_argument("--end", default=None, help="表示終了 YYYY-MM-DD（省略時=データ末尾）")
    ap.add_argument("--side", default=None, choices=["LONG", "SHORT"], help="片方向だけ表示（既定=両方）")
    ap.add_argument("--out", default=None, help=f"出力PNG（既定={VIZ_DIR} に自動命名）")
    ap.add_argument("--label", default=None, help="タイトル先頭に付けるカテゴリ名（例: トレード数最大／net利益最小）。表示のみ＝net/売買データは一切変えない")
    a = ap.parse_args()

    trades_path = _resolve_trades(a.trades)
    price_path = pathlib.Path(a.price) if a.price else DEFAULT_PRICE
    if not price_path.exists():
        raise SystemExit(f"価格CSVが見つかりません: {price_path}")

    # 売買記録（先に読み、期間省略時のデフォルト窓を決める）
    tr = pd.read_csv(trades_path)
    tr["et"] = pd.to_datetime(tr["entry_time"]); tr["xt"] = pd.to_datetime(tr["exit_time"])
    if a.end:
        end = pd.Timestamp(a.end)
    else:
        end = tr["et"].max().normalize() + pd.Timedelta(days=1)   # データ末尾翌日
    start = pd.Timestamp(a.start) if a.start else (end - pd.Timedelta(days=7))   # 既定=1週間

    # 価格
    px = pd.read_csv(price_path)
    px["t"] = pd.to_datetime(px["timestamp"], unit="ms") if px["timestamp"].dtype != object else pd.to_datetime(px["timestamp"])
    px = px[(px["t"] >= start) & (px["t"] <= end)].reset_index(drop=True)
    if len(px) == 0:
        raise SystemExit(f"価格データが空（{start.date()}〜{end.date()}）。期間を確認してください。")

    tr = tr[(tr["et"] >= start) & (tr["et"] <= end)].copy()
    if a.side:
        tr = tr[tr["side"] == a.side].copy()

    fig, ax = plt.subplots(figsize=(22, 8))
    ax.plot(px["t"], px["close"], color="#9e9e9e", lw=0.7, zorder=1, label="_price")

    # 建玉→決済の線（方向色・薄く）＋ Entry●（方向色）＋ 決済（形=理由・色=方向）
    n_win = 0; n_loss = 0
    for _, r in tr.iterrows():
        sc = SIDE_COLOR.get(r["side"], "#666666")
        if r["net_usd"] >= 0: n_win += 1
        else: n_loss += 1
        ax.plot([r["et"], r["xt"]], [r["entry_price"], r["exit_price"]],
                color=sc, lw=0.7, alpha=0.22, zorder=2)
        ax.scatter(r["et"], r["entry_price"], c=sc, marker="o", s=40,
                   edgecolors="white", linewidths=0.4, zorder=5)          # Entry ●
        ax.scatter(r["xt"], r["exit_price"], c=sc, marker=exit_marker(r["exit_reason"]),
                   s=48, linewidths=1.2, zorder=4)                        # Exit（形=理由）

    net = tr["net_usd"].sum()
    wr = 100 * n_win / max(1, n_win + n_loss)
    stem = trades_path.stem
    days = max(1, (end - start).days)
    npos = tr["position_id"].nunique() if "position_id" in tr.columns else len(tr)
    pos_pd = npos / days; leg_pd = len(tr) / days   # 建玉/日・決済レグ/日（頻度＝一級の制約）
    s_lbl = start.strftime("%Y-%m-%d"); e_lbl = end.strftime("%Y-%m-%d")
    ttl = (f"{stem}  {s_lbl}〜{e_lbl}（{days}日）  "
           f"建玉{npos}（{pos_pd:.1f}/日）・レグ{len(tr)}（{leg_pd:.1f}/日）・net ${net:.1f}・勝率{wr:.0f}%")
    if a.side:
        ttl += f"（{a.side}のみ）"
    if a.label:
        ttl = f"【{a.label}】 " + ttl        # カテゴリ名を先頭に（表示のみ・データ不変）
    ax.set_title(ttl, fontsize=12)
    ax.set_xlabel("時刻"); ax.set_ylabel("Price (USD)")

    # 凡例: 形=イベント種別（灰色で示す）／ 色=方向
    from matplotlib.lines import Line2D
    shape_leg = [
        Line2D([], [], color="#555", marker="o", ls="None", ms=7, label="Entry（建玉）"),
        Line2D([], [], color="#555", marker="v", ls="None", ms=7, label="TP（利確）"),
        Line2D([], [], color="#555", marker="s", ls="None", ms=7, label="TimeExit（時間切れ）"),
        Line2D([], [], color="#555", marker="x", ls="None", ms=7, label="SL（損切り）"),
        Line2D([], [], color="#555", marker="D", ls="None", ms=7, label="その他Exit"),
    ]
    side_leg = [
        Line2D([], [], color=SIDE_COLOR["LONG"], marker="s", ls="None", ms=8, label="LONG（買い・青）"),
        Line2D([], [], color=SIDE_COLOR["SHORT"], marker="s", ls="None", ms=8, label="SHORT（売り・赤）"),
    ]
    leg1 = ax.legend(handles=shape_leg, loc="upper left", ncol=5, fontsize=8, framealpha=0.9)
    ax.add_artist(leg1)
    ax.legend(handles=side_leg, loc="upper right", fontsize=8, framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.autofmt_xdate(); ax.grid(alpha=0.2)

    if a.out:
        out = pathlib.Path(a.out)
    else:
        VIZ_DIR.mkdir(parents=True, exist_ok=True)
        out = VIZ_DIR / f"{stem}_{s_lbl}_{e_lbl}{'_'+a.side if a.side else ''}.png"
    ratchet_io.archive_if_exists(out)                # 既存 png を archive へ逃がす（上書きしない・過去保全）
    fig.tight_layout(); fig.savefig(out, dpi=110)
    print(f"[出力] {out}")
    print(f"  期間 {s_lbl}〜{e_lbl}（{days}日）/ 建玉 {npos}（{pos_pd:.1f}/日）/ 決済レグ {len(tr)}（{leg_pd:.1f}/日）")
    print(f"  net ${net:.2f} / 勝率 {wr:.0f}%（勝{n_win}:負{n_loss}）/ 出口内訳 {dict(tr['exit_reason'].value_counts())}")


if __name__ == "__main__":
    main()

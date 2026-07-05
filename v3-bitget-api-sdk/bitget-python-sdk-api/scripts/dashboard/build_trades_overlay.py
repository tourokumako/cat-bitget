"""build_trades_overlay.py — 売買記録CSVを ⑪ レジーム試作タブに重ねる結果オーバーレイJSONへ変換。

目的（まこさん 2026-07-05「レジーム判定したチャート上に結果表示でいい」）:
  E37 のレンジ判定計器（⑪ v17・粒度5分・月/日絞り）を目視校正したのと同じチャート上に、
  戦略のトレード結果（Entry/Exit マーカー）を重ねて、レンジ判定と実際の売買を突き合わせる。
  plot_trades.py の静的PNG（週次）を、⑪ の対話的な同粒度ビュー（バージョン×粒度×日絞り）に載せ替える。

入力: results/priority_rebuild/ratchet/<trades>.csv（entry_time/exit_time/side/entry_price/exit_price/exit_reason/net_usd）
出力: dashboard/regime_prototype/trades/<stem>.json（トレード配列）＋ index.json の trade_overlays に登録
確認: python3 scripts/dashboard/dashboard_server.py → ⑪ → 結果重ね で選択 → 粒度5分 → 月 → 日絞り
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTO_DIR = REPO_ROOT / "dashboard" / "regime_prototype"
TRADES_DIR = PROTO_DIR / "trades"
INDEX_JSON = PROTO_DIR / "index.json"


def build(csv_path: Path) -> None:
    if not csv_path.exists():
        sys.exit(f"ABORT: missing trades CSV: {csv_path}")
    if not INDEX_JSON.exists():
        sys.exit(f"ABORT: missing index.json: {INDEX_JSON}")
    df = pd.read_csv(csv_path, parse_dates=["entry_time", "exit_time"])
    stem = csv_path.stem   # 例: trades_e37_range_scalp_v11_019_score

    def ms(t):
        return int(pd.Timestamp(t).value // 10**6)

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "et": ms(r["entry_time"]),
            "xt": ms(r["exit_time"]),
            "s": -1 if str(r["side"]).upper().startswith("S") else 1,   # SHORT=-1 / LONG=1
            "ep": round(float(r["entry_price"]), 1),
            "xp": round(float(r["exit_price"]), 1),
            "r": str(r["exit_reason"]),
            "n": round(float(r["net_usd"]), 2),
        })
    rows.sort(key=lambda x: x["et"])

    TRADES_DIR.mkdir(parents=True, exist_ok=True)
    out = TRADES_DIR / f"{stem}.json"
    tot_net = round(df["net_usd"].sum(), 1)
    win = int((df["net_usd"] > 0).sum())
    obj = {
        "stem": stem,
        "n_trades": len(rows),
        "net": tot_net,
        "win_rate": round(win / max(len(rows), 1) * 100, 1),
        "start": df["entry_time"].min().isoformat(),
        "end": df["exit_time"].max().isoformat(),
        "trades": rows,
    }
    out.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    print(f"    saved {out.relative_to(REPO_ROOT)}（{len(rows):,} トレード / net ${tot_net} / 勝率 {obj['win_rate']}%）")

    # index.json の trade_overlays に登録（重複は stem で置換・⑪ のバージョン選択と同型）
    index_obj = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    overlays = [o for o in index_obj.get("trade_overlays", []) if o.get("stem") != stem]
    overlays.append({
        "stem": stem, "file": f"trades/{stem}.json",
        "n_trades": len(rows), "net": tot_net, "win_rate": obj["win_rate"],
        "start": obj["start"][:10], "end": obj["end"][:10],
    })
    overlays.sort(key=lambda o: o["stem"])
    index_obj["trade_overlays"] = overlays
    INDEX_JSON.write_text(json.dumps(index_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    index.json trade_overlays: {stem} 登録（計 {len(overlays)} 件）")


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("usage: build_trades_overlay.py <trades.csv> [<trades2.csv> ...]")
    for p in sys.argv[1:]:
        build(Path(p) if Path(p).is_absolute() else REPO_ROOT / p)
    print("\n[DONE] ダッシュボード → ⑪ レジーム試作 → 「結果重ね」で選択 → 粒度5分 → 表示期間で月 → 日絞り")
    return 0


if __name__ == "__main__":
    sys.exit(main())

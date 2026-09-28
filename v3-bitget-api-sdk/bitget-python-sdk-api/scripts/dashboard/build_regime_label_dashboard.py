#!/usr/bin/env python3
"""build_regime_label_dashboard.py — 答え合わせに使う正解ラベル（いまの作り方）を、⑪タブの版として出す

2026-09-28（132回目）・まこさん「OK」（逐語＝「まず、現状に正解ラベルの精度を視覚で判断したいので、
ダッシュボードに表示させるとかできない？」→ 作り方を出して「OK」）。

何をするか（4つ）
  1. 5分足 CSV を読み、値決め窓（periods.SEARCH_START〜SEARCH_END）だけを切り出す
       ＝observe_diag の検査15（_insp_regime_label_oneway）と同じ切り出し方
  2. いまの正解ラベルを付ける ＝ observe_diag._regime_labels(win, n)["強さ"]
       （先 n本の ER が窓の中央値以上なら「トレンドだった」。★式はここに写さない＝observe_diag を呼ぶだけ）
       n＝observe_diag._regime_horizons()（= recipes/search_limits.json の state_hold_bars_range の両端＝24・288）
       ⑪タブに色を付けるのは「レンジだった」＝強さが偽 かつ 使える（先が足りる）バー
  3. 版のファイル4種類を書き出す ＝ build_regime_from_tuner.write_version_files（同じ形・同じ決まり）
       predictions_<版>_1h.json ／ _1d.json ／ predictions_<版>_5m/<年月>.json ／ labels_<版>.csv
  4. 版の一覧（index.json）に足す ＝ build_regime_from_tuner.update_index（同じ名前が在れば消してから足す）

版の名前＝label-er<n>（例＝label-er24・label-er288）

★絵にするのは値決め窓だけ（採点窓・封印窓は1本も出さない＝やってはいけないこと13番）。
★これは読むための道具（恒久の決まり71番）＝壊すプログラムは付けない。動くことを1回 確かめる。
★正解ラベルの式は observe_diag.py の1か所だけ（ここに書き写さない＝式を2か所に持たない）。
★売買記録CSV を書かない・審判（score.py）を呼ばない・engine_tuner を呼ばない。

使い方:
  python3 scripts/dashboard/build_regime_label_dashboard.py
  python3 scripts/dashboard/build_regime_label_dashboard.py --csv data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys
import time

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
SDK = HERE.parents[1]
sys.path.insert(0, str(SDK / "scripts" / "priority_rebuild"))
sys.path.insert(0, str(HERE))

DEFAULT_CSV = SDK / "data" / "BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv"
VERSION_PREFIX = "label-er"


def load_window(csv_path: pathlib.Path):
    """5分足 CSV を読み、値決め窓だけを返す（検査15 と同じ切り出し方）。"""
    import observe_diag as od
    from periods import SEARCH_END, SEARCH_START

    bars = pd.read_csv(csv_path, usecols=["timestamp", "open", "high", "low", "close"],
                       parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    win = bars.loc[(bars.index >= SEARCH_START) & (bars.index < SEARCH_END)]
    od._assert_search_window_only(win.index, "正解ラベルの版")
    return win


def label_frame(win: pd.DataFrame, n: int) -> tuple[pd.DataFrame, str, dict]:
    """いまの正解ラベルを付けた表を返す。列＝ts・close・<列名>（レンジだった＝True）。"""
    import observe_diag as od

    mask, usable = od._regime_labels(win, n)["強さ"]        # 強さ＝真ならトレンドだった
    col = f"label_range_{n}"
    is_range = (usable.fillna(False) & ~mask.fillna(False)).astype(bool)
    df = pd.DataFrame({"ts": win.index, "close": win["close"].to_numpy(), col: is_range.to_numpy()})
    counts = {"レンジだった": int(is_range.sum()),
              "トレンドだった": int((usable.fillna(False) & mask.fillna(False)).sum()),
              "使えない（先が足りない）": int((~usable.fillna(False)).sum()),
              "全部": int(len(df))}
    return df, col, counts


def spec_of(csv_path: pathlib.Path, win: pd.DataFrame, n: int, counts: dict, start, end) -> dict:
    """画面に出す仕様＝実物から作る（手で書かない）。"""
    md5 = hashlib.md5(csv_path.read_bytes()).hexdigest()[:12]
    return {
        "これは何か": ("engine_tuner の判定ではなく、判定の答え合わせに使う「正解ラベル」そのもの。"
                    "M2-A-3（2026-08-29）で決まった いまの作り方を、そのまま絵にした"),
        "入力データ": f"{csv_path.name}（5分足・値決め窓 {len(win):,}本・md5 {md5}）",
        "期間（絵にした所）": (f"値決め窓 {pd.Timestamp(start).date()}〜{(pd.Timestamp(end) - pd.Timedelta(days=1)).date()}"
                      "（periods.py が正本。採点窓・封印窓は1本も出していない）"),
        "正解ラベルの作り方": (f"そのバーから先 {n} 本（5分足なので {n * 5} 分）の ER（まっすぐ進んだ距離 ÷ 実際に歩いた距離）が、"
                      "この窓の中央値以上なら「トレンドだった」、未満なら「レンジだった」。★中央値で切るので、使えるバーの半分がレンジになる"),
        "色が付くバー": "「レンジだった」＝強さが偽 かつ 先が足りて使えるバー。末尾の先が足りないバーは色なし",
        "先を見る本数の出どころ": ("recipes/search_limits.json の state_hold_bars_range の両端（observe_diag._regime_horizons）"
                          "＝RG-v5 の停滞 2h と継続の窓 24h から取った値"),
        "式の在る所": "scripts/priority_rebuild/observe_diag.py の _regime_labels（この道具は呼ぶだけ・式を写していない）",
        "数えた結果": counts,
        "教師": "なし＝過去チャートの先の値動きから付けた札（手動のラベルは1件も読まない）",
        "出力粒度": "5m（月別）/ 1h（5分の多数決）/ 1d（日内のレンジ率 0.5 以上）",
        "生成方式": "scripts/dashboard/build_regime_label_dashboard.py が実行時の実物から本仕様を作る（手で書かない）",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="いまの正解ラベルを ⑪タブの版として出す")
    ap.add_argument("--csv", default=str(DEFAULT_CSV), help="5分足 CSV（既定＝Binance spot の正本）")
    a = ap.parse_args()
    csv_path = pathlib.Path(a.csv)
    if not csv_path.exists():
        print(f"❌ CSV が無い: {csv_path}")
        return 2

    import observe_diag as od
    from build_regime_from_tuner import INDEX_JSON, PROTO_DIR, update_index, write_version_files
    from periods import SEARCH_END, SEARCH_START

    t0 = time.time()
    print(f"[1/3] 5分足を読み、値決め窓を切り出す ... {csv_path.name}")
    win = load_window(csv_path)
    print(f"    値決め窓 {len(win):,}本（{win.index.min()} 〜 {win.index.max()}）・{time.time() - t0:.1f}秒")

    n_ver = None
    for n in od._regime_horizons():
        version = f"{VERSION_PREFIX}{n}"
        t1 = time.time()
        print(f"[2/3] {version}: 正解ラベルを付ける（先 {n} 本）...")
        df, col, counts = label_frame(win, n)
        st = write_version_files(PROTO_DIR, version, df, col, SEARCH_START, SEARCH_END)
        dist = {"range": {"count": st["range_count"], "pct": st["range_pct"]},
                "non_range": {"count": len(df) - st["range_count"],
                              "pct": round((len(df) - st["range_count"]) / max(len(df), 1) * 100, 2)}}
        n_ver = update_index(INDEX_JSON, version, spec_of(csv_path, win, n, counts, SEARCH_START, SEARCH_END),
                             dist, st["months"])
        print(f"    数えた結果＝{counts}")
        print(f"    月のファイル {st['n_month_files']} 本／5分 {st['n_5m_rows']:,}行／1時間 {st['n_1h_rows']:,}行／"
              f"レンジ {st['range_pct']}%／版の合計 {n_ver}／{time.time() - t1:.1f}秒")

    print(f"\n[3/3] 完了（{time.time() - t0:.1f}秒）。⑪タブ → 版 {VERSION_PREFIX}24・{VERSION_PREFIX}288 → 粒度5分 → 月を選ぶ")
    print("      比べる相手＝同じ⑪タブの rg-v5（いま E38 が使っている判定）")
    print("      画面の出し方＝python3 scripts/dashboard/dashboard_server.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

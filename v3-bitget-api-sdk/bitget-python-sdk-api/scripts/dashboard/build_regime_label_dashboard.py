#!/usr/bin/env python3
"""build_regime_label_dashboard.py — 答え合わせに使う正解ラベル（札）の版を、⑪タブの版として出す

2026-09-28（132回目）・まこさん「OK」（逐語＝「まず、現状に正解ラベルの精度を視覚で判断したいので、
ダッシュボードに表示させるとかできない？」→ 作り方を出して「OK」）。
2026-10-02（M2-F-6d の工事 A〜C）・札を作る場所を regime_label.py の1か所にし、数字を recipes/regime_label.json に置いた
（まこさん決定 2026-09-28＝m2_todo.json の M2-F-6d の注意に逐語）。

何をするか（4つ）
  1. 5分足 CSV を読み、値決め窓（periods.SEARCH_START〜SEARCH_END）だけを切り出す
       ＝observe_diag の検査15（_insp_regime_label_oneway）と同じ切り出し方
  2. 札を付ける ＝ regime_label.py を呼ぶだけ（★式はここに写さない）
       版1 er_median＝先を見る本数ごと（設定の「先を見る本数」）
       版2 band_hold＝役割ごと × 設定の範囲の両端と真ん中の値の組（regime_label.variants）＝まこさんが目で見て「使う値」を選ぶ
       ⑪タブに色を付けるのは「レンジだった」＝強さが偽 かつ 使えるバー
       版ごとに検査15（片道の度合いの中央値・レンジの札とトレンドの札）を数えて仕様に出す
       ＝値を選ぶのは、⑪タブの まこさんの目と検査15（定義の原文＝m2_todo.json の M2-F-6d の注意）
  3. 版のファイル4種類を書き出す ＝ build_regime_from_tuner.write_version_files（同じ形・同じ決まり）
       predictions_<版>_1h.json ／ _1d.json ／ predictions_<版>_5m/<年月>.json ／ labels_<版>.csv
  4. 版の一覧（index.json）に足す ＝ build_regime_from_tuner.update_index（同じ名前が在れば消してから足す）

版の名前＝regime_label.version_tag（版1＝label-er24・label-er288／版2＝label-band-<役割>-<値の組>＝使った値が名前に入る）
画面の「仕様」＝設定ファイルの中身を、そのまま出す（手で書き写さない）

★絵にするのは値決め窓だけ（採点窓・封印窓は1本も出さない＝やってはいけないこと13番）。
★これは読むための道具（恒久の決まり71番）＝壊すプログラムは付けない。動くことを1回 確かめる。
★札の式は regime_label.py の1か所だけ（ここに書き写さない＝式を2か所に持たない）。
★売買記録CSV を書かない・審判（score.py）を呼ばない・engine_tuner を呼ばない。

使い方:
  python3 scripts/dashboard/build_regime_label_dashboard.py
  python3 scripts/dashboard/build_regime_label_dashboard.py --csv data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv
  python3 scripts/dashboard/build_regime_label_dashboard.py --version er_median   （版1 だけ）
  python3 scripts/dashboard/build_regime_label_dashboard.py --version band_hold   （版2 だけ＝役割ごとに、設定の範囲の両端と真ん中の値の組を全部）
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
import regime_label as rl   # noqa: E402  札を作る、ただ1つの場所（M2-F-6d）


def load_window(csv_path: pathlib.Path):
    """5分足 CSV を読み、値決め窓だけを返す（検査15 と同じ切り出し方）。"""
    import observe_diag as od
    from periods import SEARCH_END, SEARCH_START

    bars = pd.read_csv(csv_path, usecols=["timestamp", "open", "high", "low", "close"],
                       parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    win = bars.loc[(bars.index >= SEARCH_START) & (bars.index < SEARCH_END)]
    od._assert_search_window_only(win.index, "正解ラベルの版")
    return win


def check15(win: pd.DataFrame, n: int, mask: pd.Series, usable: pd.Series) -> dict:
    """検査15 と同じ数え方を、この版の札に掛ける（値を選ぶ材料＝まこさんの目と検査15）。

    片道の度合い＝observe_diag._oneway_ratio、重なった区間を数えない間隔＝observe_diag._independent_step（式は写さない）。
    ★判定はしない（数を出すだけ）。レンジの札の中央値がトレンドの札より低いほど、札がレンジらしさを捉えている。
    """
    import observe_diag as od
    ratio = od._oneway_ratio(win, n)
    step = od._independent_step("5m", n)
    idx = win.index[::step]
    r = ratio.reindex(idx)
    m = mask.reindex(idx)
    u = usable.reindex(idx).fillna(False) & r.notna()
    rng = r[u & ~m.fillna(True)]
    trd = r[u & m.fillna(False)]
    out = {"先の本数": int(n), "数える間隔（本）": int(step),
           "レンジの札の本数": int(len(rng)), "トレンドの札の本数": int(len(trd))}
    if len(rng) and len(trd):
        out["片道の度合いの中央値（レンジの札）"] = round(float(rng.median()), 3)
        out["片道の度合いの中央値（トレンドの札）"] = round(float(trd.median()), 3)
    return out


def label_frame(win: pd.DataFrame, version: str, key, values: dict | None = None) -> tuple[pd.DataFrame, str, dict]:
    """札を付けた表を返す。列＝ts・close・<列名>（レンジだった＝True）。★札の式は regime_label.py（呼ぶだけ）。

    version＝"er_median"（key＝先を見る本数）か "band_hold"（key＝役割・values＝⑪タブに出す値の組）。
    """
    cfg = rl.load_config()
    if version == "er_median":
        mask, usable = rl.er_median(win, int(key))["強さ"]        # 強さ＝真ならトレンドだった
    else:
        mask, usable = rl.band_hold(win, cfg, str(key), values)["強さ"]
    col = "label_range"
    is_range = (usable.fillna(False) & ~mask.fillna(False)).astype(bool)
    df = pd.DataFrame({"ts": win.index, "close": win["close"].to_numpy(), col: is_range.to_numpy()})
    counts = {"レンジだった": int(is_range.sum()),
              "トレンドだった": int((usable.fillna(False) & mask.fillna(False)).sum()),
              "使えない（先か前が足りない）": int((~usable.fillna(False)).sum()),
              "全部": int(len(df))}
    n15 = int(key) if version == "er_median" else rl.role_bars(cfg, str(key), values)
    counts["検査15（片道の度合い）"] = check15(win, n15, mask, usable)
    return df, col, counts


def spec_of(csv_path: pathlib.Path, win: pd.DataFrame, version: str, key, values, counts: dict, start, end) -> dict:
    """画面に出す仕様＝設定ファイルと実物から作る（手で書かない）。"""
    md5 = hashlib.md5(csv_path.read_bytes()).hexdigest()[:12]
    cfg = rl.load_config()
    ver = rl.spec(cfg)["版"][version]
    out = {
        "これは何か": ("engine_tuner の判定ではなく、判定の答え合わせに使う「正解ラベル（札）」そのもの。"
                    "札を作る場所は regime_label.py の1か所（M2-F-6d）"),
        "札の版": rl.version_tag(cfg, version, key, values),
        "入力データ": f"{csv_path.name}（5分足・値決め窓 {len(win):,}本・md5 {md5}）",
        "期間（絵にした所）": (f"値決め窓 {pd.Timestamp(start).date()}〜{(pd.Timestamp(end) - pd.Timedelta(days=1)).date()}"
                      "（periods.py が正本。採点窓・封印窓は1本も出していない）"),
        "札の作り方（設定の説明）": ver.get("説明"),
        "採点に使う版（いまの設定）": cfg["採点に使う版"],
        "色が付くバー": "「レンジだった」＝強さが偽 かつ 使えるバー。先か前のバーが足りないバーは色なし",
        "式の在る所": "scripts/priority_rebuild/regime_label.py（この道具は呼ぶだけ・式を写していない）",
        "設定の在る所": ("scripts/priority_rebuild/recipes/regime_label.json（値を書き替えて走らせ直すと、"
                     "札と⑪タブの版が作り直される）"),
        "数えた結果": counts,
        "教師": "なし＝過去チャートの先の値動きから付けた札（手動のラベルは1件も読まない）",
        "出力粒度": "5m（月別）/ 1h（5分の多数決）/ 1d（日内のレンジ率 0.5 以上）",
        "生成方式": "scripts/dashboard/build_regime_label_dashboard.py が実行時の設定ファイルと実物から本仕様を作る（手で書かない）",
    }
    if version == "er_median":
        out["先を見る本数"] = f"{int(key)} 本（5分足なので {int(key) * 5} 分）"
        out["設定ファイルの中身（この版・そのまま）"] = ver
    else:
        out["役割"] = str(key)
        out["使った値"] = values
        out["手数料の床（e38_logic_parts.SCALP_FLOOR）"] = rl.fee_floor()
        out["設定ファイルの中身（この役割・そのまま）"] = ver["役割"][str(key)]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="札の版を ⑪タブの版として出す")
    ap.add_argument("--csv", default=str(DEFAULT_CSV), help="5分足 CSV（既定＝Binance spot の正本）")
    ap.add_argument("--version", choices=("all", "er_median", "band_hold"), default="all",
                    help="出す版（既定＝全部。band_hold は役割ごとに設定の範囲の両端と真ん中の値の組を全部）")
    a = ap.parse_args()
    csv_path = pathlib.Path(a.csv)
    if not csv_path.exists():
        print(f"❌ CSV が無い: {csv_path}")
        return 2

    from build_regime_from_tuner import INDEX_JSON, PROTO_DIR, update_index, write_version_files
    from periods import SEARCH_END, SEARCH_START

    cfg = rl.load_config()
    jobs = []
    if a.version in ("all", "er_median"):
        jobs += [("er_median", n, None) for n in rl.horizons(cfg)]
    if a.version in ("all", "band_hold"):
        jobs += [("band_hold", role, v) for role in rl.roles(cfg) for v in rl.variants(cfg, role)]

    t0 = time.time()
    print(f"[1/3] 5分足を読み、値決め窓を切り出す ... {csv_path.name}")
    win = load_window(csv_path)
    print(f"    値決め窓 {len(win):,}本（{win.index.min()} 〜 {win.index.max()}）・{time.time() - t0:.1f}秒")

    names = []
    n_ver = None
    for i, (version, key, values) in enumerate(jobs, start=1):
        name = rl.version_tag(cfg, version, key, values)
        t1 = time.time()
        print(f"[2/3] {i}/{len(jobs)} {name}: 札を付ける ...")
        df, col, counts = label_frame(win, version, key, values)
        st = write_version_files(PROTO_DIR, name, df, col, SEARCH_START, SEARCH_END)
        dist = {"range": {"count": st["range_count"], "pct": st["range_pct"]},
                "non_range": {"count": len(df) - st["range_count"],
                              "pct": round((len(df) - st["range_count"]) / max(len(df), 1) * 100, 2)}}
        n_ver = update_index(INDEX_JSON, name, spec_of(csv_path, win, version, key, values, counts,
                                                       SEARCH_START, SEARCH_END), dist, st["months"])
        names.append(name)
        print(f"    数えた結果＝{counts}")
        print(f"    月のファイル {st['n_month_files']} 本／5分 {st['n_5m_rows']:,}行／1時間 {st['n_1h_rows']:,}行／"
              f"レンジ {st['range_pct']}%／版の合計 {n_ver}／{time.time() - t1:.1f}秒")

    print(f"\n[3/3] 完了（{time.time() - t0:.1f}秒）。⑪タブ → 版（{len(names)} 本）→ 粒度5分 → 月を選ぶ")
    for nm in names:
        print(f"      {nm}")
    print("      比べる相手＝同じ⑪タブの rg-v5（いま E38 が使っている判定）")
    print("      画面の出し方＝python3 scripts/dashboard/dashboard_server.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

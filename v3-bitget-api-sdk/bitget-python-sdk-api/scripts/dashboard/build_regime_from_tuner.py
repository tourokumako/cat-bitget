#!/usr/bin/env python3
"""build_regime_from_tuner.py — engine_tuner が組み立てた場面の判定を、⑪タブの版として出す（M2-10-1）

2026-08-27（68回目）・まこさん承認「OK実装していいよ」・設計書 iter=regime-build-dashboard-20260827。

何をするか（5つ）
  1. 値決め窓（periods.SEARCH_START〜SEARCH_END）の指標つきデータを読む
       ＝engine_tuner.load_windows_cached（R9 の診断 regime_r9_diag.py と同じ1行）
  2. 判定の束を組む
       ＝engine_tuner_gen.sample_structure(..., build_regime=True, regime_order_n=i)
         ★成績表の1位から順（乱数で指標を選ばない・まこさん決定 2026-08-23）
  3. 束を真偽の列にする ＝ engine_tuner_exec.build_regime_columns
  4. ⑪タブの版のファイル4種類を書き出す（build_regime_gate_rg.py と同じ形）
       predictions_<版>_1h.json ／ _1d.json ／ predictions_<版>_5m/<年月>.json ／ labels_<版>.csv
  5. 版の一覧（index.json）に足す（同じ名前の行が在れば消してから足す＝走らせ直しても増えない）

★絵にするのは値決め窓だけ（18ヶ月）
  値を選んでよいのは値決め窓だけ（periods.py）。まこさんが絵を見て「この判定はおかしい」と言うのは、
  値を選ぶ行為そのもの。だから採点窓（2026-03〜06）と封印窓（2026-07〜）は1本も出さない
  （やってはいけないこと13番＝採点窓を探索や選定に使わない）。確認窓も出さない（選び直さない窓）。

★検査の印（H2・G2）は、このプログラムでは確かめない
  2026-08-27 の直しで、H2・G2 の見張りが「走らせる .py が engine の入口を使うか」で止めるようになった。
  このプログラムは load_windows を使うので見張りの対象＝印が古ければ走る前に止まる（実測で確認済み）。
  だから自前の確認は書かない（二重になるため）。

決まり
  売買記録CSV を書かない・_output_and_report を呼ばない・審判（score.py）は呼ばない。
  値決め窓だけ（採点窓は1バーも使わない・H8）。出た絵で案を選ぶのは まこさん（M2-10-2）。

使い方:
  python3 scripts/dashboard/build_regime_from_tuner.py --build 3 --seed 53
  python3 scripts/dashboard/build_regime_from_tuner.py --selftest
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
SDK = HERE.parents[1]
PROTO_DIR = SDK / "dashboard" / "regime_prototype"
INDEX_JSON = PROTO_DIR / "index.json"
sys.path.insert(0, str(SDK / "scripts" / "priority_rebuild"))

VERSION_PREFIX = "et-r"                     # ⑪タブの3つ目の名前の並び（v◯ / rg-v◯ に続く）


# ══ 期間の見張り（値決め窓だけ）════════════════════════════════════════════════════
def assert_window_only(ts: pd.Series, start, end) -> None:
    """書き出す行が、値決め窓の中だけであることを確かめる（外が1本でも在れば止める）。"""
    t = pd.to_datetime(pd.Series(ts))
    bad = int(((t < pd.Timestamp(start)) | (t >= pd.Timestamp(end))).sum())
    if bad:
        raise SystemExit(f"[M2-10] 値決め窓の外の行が {bad} 本ある（採点窓・封印窓は1本も出さない）")


# ══ 絵のデータの形（build_regime_gate_rg.py と同じ）══════════════════════════════════
def rows_5m(df: pd.DataFrame, col: str) -> list:
    ts_ms = (pd.to_datetime(df["ts"]).astype("int64") // 10**6).tolist()
    close_int = df["close"].round().astype(int).tolist()
    lab = ["range" if bool(v) else "" for v in df[col].tolist()]
    return [[int(t), int(c), s, ""] for t, c, s in zip(ts_ms, close_int, lab)]


def _hourly(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """1時間ごとの close（最後）と、その1時間の5分の判定の割合。"""
    d = df.copy()
    d["ts"] = pd.to_datetime(d["ts"])
    d = d.set_index("ts").sort_index()
    out = pd.DataFrame({
        "close": d["close"].resample("1h", label="right", closed="right").last(),
        "share": d[col].astype(float).resample("1h", label="right", closed="right").mean(),
    }).dropna(subset=["close"])
    return out


def rows_1h(df: pd.DataFrame, col: str) -> list:
    """1時間の判定＝その1時間の5分の多数決（RG-v5 と同じ 0.5 の線）。"""
    h = _hourly(df, col)
    ts_ms = (h.index.astype("int64") // 10**6).tolist()
    lab = ["range" if s >= 0.5 else "" for s in h["share"].fillna(0).tolist()]
    return [[int(t), int(round(c)), s, ""] for t, c, s in zip(ts_ms, h["close"].tolist(), lab)]


def rows_1d(df: pd.DataFrame, col: str) -> list:
    """1日の判定＝日内のレンジ率 0.5 以上（RG-v5 と同じ）。"""
    d = df.copy()
    d["ts"] = pd.to_datetime(d["ts"])
    day = pd.DataFrame({"close": d["close"].to_numpy(), "ok": d[col].astype(int).to_numpy(),
                        "date": d["ts"].dt.normalize().to_numpy()})
    dd = day.groupby("date").agg(close=("close", "last"), ok=("ok", "mean"))
    ts_ms = (pd.to_datetime(dd.index).astype("int64") // 10**6).tolist()
    return [[int(t), int(round(c)), ("range" if o >= 0.5 else ""), ""]
            for t, c, o in zip(ts_ms, dd["close"].tolist(), dd["ok"].tolist())]


def assert_1h_matches_5m(df: pd.DataFrame, col: str, rows: list) -> None:
    """1時間の判定が、5分の多数決と食い違っていないかを確かめる（作り方どおりか）。"""
    want = rows_1h(df, col)
    bad = [(a[0], a[2], b[2]) for a, b in zip(rows, want) if a[2] != b[2]]
    if len(rows) != len(want) or bad:
        raise SystemExit(f"[M2-10] 1時間の判定が5分の多数決と食い違う（{len(bad)} 本・例 {bad[:2]}）")


# ══ 書き出し ══════════════════════════════════════════════════════════════════════
def write_version_files(proto_dir: pathlib.Path, version: str, df: pd.DataFrame, col: str,
                        start, end) -> dict:
    """版のファイル4種類を書き出し、数えた結果を返す。"""
    assert_window_only(df["ts"], start, end)
    sm_dir = proto_dir / f"predictions_{version}_5m"
    sm_dir.mkdir(parents=True, exist_ok=True)
    for old in sm_dir.glob("*.json"):
        old.unlink()

    r1h = rows_1h(df, col)
    assert_1h_matches_5m(df, col, r1h)
    (proto_dir / f"predictions_{version}_1h.json").write_text(
        json.dumps({"version": version, "granularity": "1h", "rows": r1h}, ensure_ascii=False),
        encoding="utf-8")
    (proto_dir / f"predictions_{version}_1d.json").write_text(
        json.dumps({"version": version, "granularity": "1d", "rows": rows_1d(df, col)},
                   ensure_ascii=False), encoding="utf-8")

    d = df.copy()
    d["ts"] = pd.to_datetime(d["ts"])
    months, n5 = [], 0
    for ym, sub in d.groupby(d["ts"].dt.strftime("%Y-%m"), sort=True):
        (sm_dir / f"{ym}.json").write_text(
            json.dumps({"version": version, "granularity": "5m", "rows": rows_5m(sub, col)},
                       ensure_ascii=False), encoding="utf-8")
        months.append(str(ym))
        n5 += len(sub)

    pd.DataFrame({"datetime_utc": d["ts"], "close": d["close"].round(1),
                  "range_built": d[col].astype(int)}).to_csv(
        proto_dir / f"labels_{version}.csv", index=False)

    ok = int(d[col].astype(bool).sum())
    return {"months": months, "n_month_files": len(months), "n_5m_rows": n5,
            "n_1h_rows": len(r1h), "range_count": ok, "range_pct": round(ok / max(len(d), 1) * 100, 2)}


def update_index(index_path: pathlib.Path, version: str, spec: dict, dist: dict,
                 months: list) -> int:
    """版の一覧に1行 足す（同じ名前が在れば消してから足す）。戻り＝足した後の版の数。"""
    obj = json.loads(index_path.read_text(encoding="utf-8"))
    obj["prototypes"] = [p for p in obj["prototypes"] if p.get("version") != version]
    obj["prototypes"].append({
        "version": version,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "spec": spec,
        "distribution": dist,
        "months": months,          # ★この版が出している年月だけ（app.js が月の選択肢に使う）
    })
    index_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(obj["prototypes"])


# ══ 束を組む・列にする（engine_tuner の道をそのまま呼ぶ）════════════════════════════
def build_bundles(n: int, seed: int, strategy: str = "e38") -> tuple:
    """判定の束を n 本 組む（R9 の診断と同じ呼び方＝成績表の1位から順）。戻り＝(df, geo, recipes)。"""
    import engine_tuner as et
    import engine_tuner_exec as ex
    import engine_tuner_gen as g
    from periods import SEARCH_END, SEARCH_START

    ad = et.load_adapter(strategy)
    df, = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END)], et.WARM)
    pool, tfs, _ = g.material_pool()
    lm, _w = g.load_limits()
    lm = g.resolve_hold_range(lm, strategy)
    lim = {"n_min": None, "p_max": lm.get("p_max"), "count_range": lm.get("count_range"),
           "role_max": lm.get("role_max"), "depth_max": lm.get("depth_max"),
           "k_max": lm.get("k_max"), "r_min": lm.get("r_min")}
    regime = ad.regime("S2")
    recipes, i, tries = [], 0, 0
    while len(recipes) < n and tries < n * 20:
        rng = np.random.default_rng([seed, 1, tries])
        tries += 1
        try:
            r = g.sample_structure(rng, lm, pool, tfs, side="SHORT", regime=regime,
                                   logic_id=f"R9_{i}", build_regime=True, regime_order_n=i)
            ex.validate_recipe(r, limits=lim)
        except (g.SampleError, ex.RecipeError) as e:
            print(f"  [組めない] 案 {i}: {str(e)[:80]}（同じ番号で引き直す）")
            continue
        recipes.append(r)
        i += 1
    if len(recipes) < n:
        raise SystemExit(f"[M2-10] 束を {n} 本 組めなかった（組めたのは {len(recipes)} 本）")
    return df, g._geo_of(df), recipes


def build_columns(df: pd.DataFrame, geo: dict, rec: dict, start, end) -> tuple:
    """束を真偽の列にする。戻り＝(列を持つ df, 列の名前)。"""
    import engine_tuner_exec as ex
    import engine_tuner_gen as g
    lm, _w = g.load_limits()
    qt = g.build_qtable(df, geo, [rec], g.quantile_list(lm), start, end)
    d = df.copy()
    d.attrs = {}
    ex.build_regime_columns(d, rec, geo, qt)
    return d, rec["meta"]["regime"]["build"]["entry"]["out_col"]


def spec_of(rec: dict, df: pd.DataFrame, start, end, seed: int, order_n: int) -> dict:
    """画面に出す仕様＝実物から作る（手で書かない）。"""
    rg = rec["meta"]["regime"]
    md5 = hashlib.md5(json.dumps(rec, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    return {
        "入力データ": (f"engine_tuner の指標つきデータ {len(df):,}本 "
                   f"{pd.to_datetime(df['ts']).min().date()}〜{pd.to_datetime(df['ts']).max().date()}"
                   f"（助走を含む・束の md5 {md5}）"),
        "期間（絵にした所）": (f"値決め窓 {pd.Timestamp(start).date()}〜"
                      f"{(pd.Timestamp(end) - pd.Timedelta(days=1)).date()}"
                      "（periods.py が正本。採点窓・封印窓は1本も出していない）"),
        "判定の中身（束そのもの）": json.dumps(rg["build"]["entry"]["tree"], ensure_ascii=False),
        "引いた材料": json.dumps((rec.get("meta") or {}).get("regime_draw") or {}, ensure_ascii=False),
        "作り方": (f"engine_tuner_gen.sample_structure(build_regime=True, regime_order_n={order_n}) で組み、"
                f"engine_tuner_exec.build_regime_columns で列にした（種 {seed}・成績表の1位から順・"
                f"指標は乱数で選んでいない）"),
        "教師": "なし＝engine_tuner が組み立てた条件の束だけ（手動のラベルは1件も読まない）",
        "出力粒度": "5m（月別）/ 1h（5分の多数決）/ 1d（日内のレンジ率 0.5 以上）",
        "生成方式": "scripts/dashboard/build_regime_from_tuner.py が実行時の実物から本仕様を作る（手で書かない）",
    }


# ══ 本走 ═══════════════════════════════════════════════════════════════════════════
def main() -> int:
    ap = argparse.ArgumentParser(description="組み立てた場面の判定を ⑪タブの版として出す（M2-10-1）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--build", type=int, default=3, help="絵にする束の本数（既定 3＝53回目の R9 と同じ）")
    ap.add_argument("--seed", type=int, default=53, help="閾値の分位・続く長さの種（既定 53＝同上）")
    ap.add_argument("--strategy", default="e38")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    from periods import SEARCH_END, SEARCH_START
    print(f"[1/4] データと束（{a.build}本・種 {a.seed}）を用意する ...")
    df, geo, recipes = build_bundles(a.build, a.seed, a.strategy)
    print(f"    5分足 {len(df):,}本（助走を含む）／束 {len(recipes)} 本")

    n_ver = None
    for i, rec in enumerate(recipes):
        version = f"{VERSION_PREFIX}{i + 1}"
        print(f"[2/4] {version}: 束を真偽の列にする ...")
        d, col = build_columns(df, geo, rec, SEARCH_START, SEARCH_END)
        t = pd.to_datetime(d["ts"])
        win = d[(t >= pd.Timestamp(SEARCH_START)) & (t < pd.Timestamp(SEARCH_END))].reset_index(drop=True)
        print(f"[3/4] {version}: 絵のデータを書き出す（{len(win):,}本）...")
        st = write_version_files(PROTO_DIR, version, win, col, SEARCH_START, SEARCH_END)
        dist = {"range": {"count": st["range_count"], "pct": st["range_pct"]},
                "non_range": {"count": len(win) - st["range_count"],
                              "pct": round((len(win) - st["range_count"]) / max(len(win), 1) * 100, 2)}}
        n_ver = update_index(INDEX_JSON, version, spec_of(rec, df, SEARCH_START, SEARCH_END, a.seed, i),
                             dist, st["months"])
        print(f"    月のファイル {st['n_month_files']} 本／5分 {st['n_5m_rows']:,}行／"
              f"レンジ {st['range_pct']}%／版の合計 {n_ver}")

    print(f"\n[4/4] 完了。⑪タブ → {VERSION_PREFIX}1〜{VERSION_PREFIX}{len(recipes)} → 粒度5分 → 月を選ぶ")
    print("      （画面の出し方＝python3 scripts/dashboard/dashboard_server.py）")
    return 0


# ══ わざと壊して止まるか試すテスト ════════════════════════════════════════════════
def _fake(start="2024-03-01", end="2025-09-01", seed=0) -> pd.DataFrame:
    ts = pd.date_range(start, end, freq="5min", inclusive="left")
    rng = np.random.default_rng(seed)
    close = 60000 + np.cumsum(rng.normal(0, 5, len(ts)))
    ok = (np.arange(len(ts)) % 7) < 4
    return pd.DataFrame({"ts": ts, "close": close, "c": ok})


def selftest() -> int:
    import shutil
    import tempfile

    from periods import SCORE_START, SEARCH_END, SEARCH_START

    ng: list[str] = []
    df = _fake()

    # T1 判定の束を持たないレシピは止まる（fail-closed）
    try:
        build_columns(pd.DataFrame({"ts": [], "close": []}), {},
                      {"meta": {"logic_id": "x", "regime": {"name": "range", "build": None}}},
                      SEARCH_START, SEARCH_END)
        ng.append("T1: 束が無いレシピで止まらない")
    except Exception:
        pass

    with tempfile.TemporaryDirectory() as td:
        proto = pathlib.Path(td)
        st = write_version_files(proto, "et-test", df, "c", SEARCH_START, SEARCH_END)
        # T2 月のファイルの本数＝値決め窓の月数
        want_m = len(pd.period_range(SEARCH_START, pd.Timestamp(SEARCH_END) - pd.Timedelta(days=1), freq="M"))
        if st["n_month_files"] != want_m:
            ng.append(f"T2: 月のファイルが {st['n_month_files']} 本（{want_m} 本のはず）")
        # T3 5分の行の合計＝元の本数（重複0・欠け0）
        if st["n_5m_rows"] != len(df):
            ng.append(f"T3: 5分の行が {st['n_5m_rows']}（{len(df)} のはず）")
        # T4 採点窓の時刻を混ぜると止まる
        bad = pd.concat([df, pd.DataFrame({"ts": [pd.Timestamp(SCORE_START)], "close": [1.0], "c": [True]})])
        try:
            write_version_files(proto, "et-test2", bad, "c", SEARCH_START, SEARCH_END)
            ng.append("T4: 採点窓の時刻が混ざっても止まらない")
        except SystemExit:
            pass
        # T5 1時間の判定を1本 書き換えると止まる
        r = rows_1h(df, "c")
        r[0] = [r[0][0], r[0][1], ("" if r[0][2] == "range" else "range"), ""]
        try:
            assert_1h_matches_5m(df, "c", r)
            ng.append("T5: 1時間の判定を書き換えても止まらない")
        except SystemExit:
            pass
        # T6 版の一覧の、既に在る行が変わらない
        idx = proto / "index.json"
        before = [{"version": f"v{i}", "spec": {"a": i}} for i in range(24)]
        idx.write_text(json.dumps({"prototypes": before}, ensure_ascii=False), encoding="utf-8")
        n = update_index(idx, "et-test", {"x": 1}, {"range": {"count": 1, "pct": 1.0}}, ["2024-03"])
        after = json.loads(idx.read_text(encoding="utf-8"))["prototypes"]
        if n != 25:
            ng.append(f"T6: 版が {n} 件（25 のはず）")
        if [p for p in after if p.get("version", "").startswith("v")] != before:
            ng.append("T6: 既に在る24版の中身が変わった")
        n2 = update_index(idx, "et-test", {"x": 2}, {"range": {"count": 1, "pct": 1.0}}, ["2024-03"])
        if n2 != 25:
            ng.append(f"T6b: 走らせ直すと版が増えた（{n2} 件）")
        # T8 同じ入力なら、出るファイルの md5 が同じ
        a_dir, b_dir = proto / "a", proto / "b"
        a_dir.mkdir(); b_dir.mkdir()
        write_version_files(a_dir, "et-test", df, "c", SEARCH_START, SEARCH_END)
        write_version_files(b_dir, "et-test", df, "c", SEARCH_START, SEARCH_END)
        def md5s(d):
            return {p.name: hashlib.md5(p.read_bytes()).hexdigest()
                    for p in sorted(d.rglob("*")) if p.is_file()}
        if md5s(a_dir) != md5s(b_dir):
            ng.append("T8: 同じ入力なのに、出るファイルの md5 が違う")
        shutil.rmtree(a_dir, ignore_errors=True)

    # T7 このプログラムに未来参照の式が無い（構文木で見る＝説明の文には反応しない）
    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    bad7 = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "shift":
            if node.args and isinstance(node.args[0], ast.UnaryOp) and isinstance(node.args[0].op, ast.USub):
                bad7.append(f"shift(-…) 行 {node.lineno}")
        if isinstance(node, ast.keyword) and node.arg == "center" and \
                isinstance(node.value, ast.Constant) and node.value.value is True:
            bad7.append(f"center=True 行 {node.lineno}")
    if bad7:
        ng.append(f"T7: 未来参照の式が在る: {bad7}")

    print("[selftest] T1 束なしは止まる ／ T2 月のファイル18本 ／ T3 行の欠け0 ／ T4 採点窓は止まる ／"
          " T5 1時間の食い違いは止まる ／ T6 既存24版は不変・走らせ直しても増えない ／"
          " T7 未来参照0件 ／ T8 同じ入力は同じ md5")
    for x in ng:
        print(f"  ❌ {x}")
    print(f"  {'❌' if ng else '✅'} わざと壊して止まるか試すテスト {9 - len(ng)}/9 pass")
    return 1 if ng else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""report.py — 結果レポート1本化（V9検証時代の散らばった出力を A〜I に統合）

使い方:
  python3 report.py <trades.csv> [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--vs <v9_full.csv>]

役割: 売買記録CSVを食わせると整理された結果一覧を出すだけ（戦略ロジックなし・replay呼ばない=安全）。
  - 公式 net / NET/day / 月別 は score.py（固定審判・改造しない）から取得
  - 内訳（A リスク指標・B〜L）は**全節 審判式**（score.py と同じコスト式・現行計器・funding 除く）で行単位に再計算して集計
    ⚠️ 旧仕様（CSV の net_usd 列をそのまま集計）は E0.4 trail maker 化以降 P21 の trail 行が旧計器の値になり
    誤表示だった（2026-06-12 まこさん指摘「間違った数字を出すレポートはゴミ以下」→ 全節を審判式に統一）
出力: 0使用パラメータ / 0bこの表の数字の作り方 / A全体 / B優先度別 / C出口理由別 / C2 side×入口型(4分割) /
      Dサイズ・add別 / Eベスト・ワースト / F月別(--vs で基準と比較) / F2〜F4時系列 / G指標帯別 /
      H予測確率帯別(p列があれば) / I MFE/MAE別 / Jコスト分解 / K期待値4要素 / L限界分解 / M週次チャート
⚠️ 表示は実データ由来を原則にする（手書きの固有名詞を置かない）。F節の列名は旧「AI vs V9」＝ML戦略×手動戦略V9
   時代の手書き固定値で、--vs に何を渡しても "V9" と出て本番の手動V9と混同しうるため 2026-07-20 に
   比較相手のファイル名からの自動生成へ是正。EXIT_JP(翻訳辞書)の追従漏れは _check_exit_jp が毎回自動検出する。
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score as judge                                    # 固定審判（import のみ）
import eval_engine as ee                                 # 確定コスト定数（import のみ・改造禁止）
import ratchet_io                                        # 出力の上書き防止（書く前に既存を archive へ・全戦略汎用・net 不関与）
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30)
SIDE_JP = {"LONG": "買い", "SHORT": "売り"}
EXIT_JP = {"TP_FILLED": "利確(TP)", "SL_FILLED": "損切(SL)", "TIME_EXIT": "時間切れ", "MFE_STALE_CUT": "含み益失速",
           "STOCH_REVERSE_EXIT": "ストキャス反転", "RSI_REVERSE_EXIT": "RSI反転", "TRAIL_EXIT": "トレール",
           "PROFIT_LOCK": "利益確保", "MAE_CUT": "含み損切", "MIDTERM_CUT": "中期切", "FORCE_CLOSE_EOD": "期末強制",
           # 2026-07-20 追記＝_check_exit_jp が「英語のまま出ている6件」を自動検出したため（訳語は §0 の実装説明から）
           "PARTIAL_TP": "部分利確(TP1)", "BE_EXIT": "建値撤退", "MFE_DRAWDOWN_CUT": "ピーク反転",
           "RANGE_BREAK_EXIT": "レンジ破れ", "TREND_CAUGHT_TP": "トレンド玉利確", "TREND_CONT": "トレンド撤退"}


def _check_exit_jp(d):
    """出口理由の日本語訳の追従漏れを機械が検出して警告（2026-07-20 まこさん指摘「手書きは入れてないはず」）。

    EXIT_JP は翻訳辞書なので手書きが避けられない。だが戦略に出口枝を足すたび辞書が古くなり、
    レポートに英語の exit_reason が黙って増える（2026-07-20 実測＝6件が英語のまま出ていた）。
    黙って古くなるのを防ぐため、CSV に実在する出口理由と辞書の差分を毎回機械が出す（表示のみ・net 不関与）。
    """
    unknown = sorted(set(d["exit_reason"].dropna().astype(str).unique()) - set(EXIT_JP))
    if unknown:
        print(f"  ⚠️ 日本語訳が未登録の出口理由 {len(unknown)}件（以降の表に英語のまま出ます）: {', '.join(unknown)}")
        print("     → 戦略に出口枝を足したら report.py の EXIT_JP にも追記が要る（この検出は自動・手書きの追従漏れ対策）")


class _Tee:
    """print 出力を端末とファイルの両方へ流す（結果一覧を書類として保存する）。"""
    def __init__(self, *streams): self.streams = streams
    def write(self, x):
        for s in self.streams: s.write(x)
    def flush(self):
        for s in self.streams: s.flush()


def _load(path, start, end):
    d = pd.read_csv(path)
    d["entry_time"] = pd.to_datetime(d["entry_time"]); d["exit_time"] = pd.to_datetime(d["exit_time"])
    if start: d = d[d["entry_time"] >= pd.Timestamp(start)]
    if end:   d = d[d["entry_time"] < pd.Timestamp(end) + pd.Timedelta(days=1)]
    return d.reset_index(drop=True)


def _band(s, edges, labels):
    return pd.cut(s, bins=edges, labels=labels, right=False)


def _collapse_positions(d):
    """position_id があれば玉(取引)単位に集約（fill/add 複数行を1取引に・position-level accounting）。
    金額(net/gross/fee/size/_netj等)=合計・hold_min=最大・入口特徴/出口理由/entry_time=最初。
    position_id 無し or 既に1行1玉(P23/E34)はそのまま返す（後方互換・退化させない）。"""
    if "position_id" not in d.columns or d["position_id"].nunique() == len(d):
        return d
    agg = {}
    for c in d.columns:
        if c == "position_id":
            continue
        agg[c] = "sum" if c in ("net_usd", "gross_usd", "fee_usd", "size_btc", "_gross", "_fee", "_slip", "_netj") \
            else ("max" if c == "hold_min" else "first")
    return d.groupby("position_id", as_index=False).agg(agg)


def _funding_collapse(d):
    """公式 score.py と揃える(funding込み net)＋取引(玉)単位に集約＝analyze.py と整合・KB §0。"""
    import numpy as np
    if "_netj" in d.columns and "side" in d.columns:
        fund = np.array([judge._funding_for_trade(r["entry_time"], r["exit_time"],
                         1 if r["side"] == "LONG" else -1, r["size_btc"], r["entry_price"]) for _, r in d.iterrows()])
        d = d.copy(); d["net_usd"] = d["_netj"] - fund
    return _collapse_positions(d)


def _print_accounting_note(d_raw, d, r):
    """【0b】売買記録CSVの列を単純合計した値と、本レポートの審判値が違う理由を毎回出す（表示のみ・net 計算に不関与）。
    背景（2026-07-20 まこさん指示「report に CSV をどのように処理してるのか毎回書いておけば？」）＝
    CC が採点窓CSVを自前集計して審判値と食い違い、それを「発見」と誤認して原因調査にトークンを浪費した。
    本ファイルの docstring には書いてあったが**出力に無かった**＝読む人の目に入らなかったのが原因。
    全部 実値から自動生成する（手書きドリフト禁止・§0 param schema と同じ思想）。
    maker 決済の一覧は score.py の MAKER_EXIT_REASONS から読む＝出口理由が増えたら自動追従（手書きしない）。"""
    n_row, n_pos = len(d_raw), len(d)
    print("\n  0b. 【この表の数字の作り方】売買記録CSVの列を単純合計した値とは一致しません（実値から自動生成・表示のみ）")
    if n_row != n_pos:
        print(f"     件数の単位: 玉(取引)単位。CSV {n_row} 約定行 → position_id で集約 → {n_pos} 玉。"
              f"部分利確・add で1玉が複数行に分かれるため、行数と玉数は一致しません。")
    else:
        print(f"     件数の単位: 玉(取引)単位。CSV {n_row} 行 ＝ {n_pos} 玉（1行1玉のCSV＝集約なし）。")
    print("     金額の出所: CSV の net_usd / fee_usd 列は使いません。score.py と同じ式で"
          " entry_price / exit_price / size_btc から再計算します。")
    if "net_usd" in d_raw.columns:
        print(f"                 CSV net_usd 列の単純合計 ${float(d_raw['net_usd'].sum()):.0f}"
              f"  ≠  本レポートの審判 net ${r['total']:.0f}  ← 違って正常です。審判値（右）が正本（H13）。")
    print(f"     手数料判定: exit_reason が maker 決済なら maker {ee.MAKER_FEE*100:.3f}%、"
          f"それ以外は taker {ee.TAKER_FEE*100:.3f}% ＋ slippage {ee.SLIPPAGE*100:.3f}%。")
    print(f"                 maker 決済 ＝ {', '.join(sorted(judge.MAKER_EXIT_REASONS))}"
          " （score.py の MAKER_EXIT_REASONS から取得＝手書きしない）")
    print(f"     funding:    込み。{ee.FUNDING_RATE_8H*100:.4f}%/8h を保有期間分（LONG 払い / SHORT 受取）。")
    print("     ⚠️ CSV から分析に使ってよいのは 件数・保有時間・MFE/MAE・入口特徴 などの"
          "**金額でない**分布のみ。金額は必ず本レポート（審判値）を使う。")


def _judge_cols(t):
    """審判（score.py）と同じ式で gross/手数料/slip/net を行単位に再計算し、内訳用の列を上書きする。
    CSV の net_usd は「生成時の計器」の値＝E0.4（trail maker 化）以降 trail 行が旧値のため表示に使わない。"""
    t = t.copy()
    mk = getattr(judge, "MAKER_EXIT_REASONS", {"TP_FILLED", "SL_FILLED", "TRAIL_EXIT"})
    dirn = t["side"].map({"LONG": 1, "SHORT": -1}).fillna(-1)
    tk = (~t["exit_reason"].isin(mk)).astype(float)
    t["_gross"] = (t["exit_price"] - t["entry_price"]) * t["size_btc"] * dirn
    t["_fee"] = t["entry_price"] * t["size_btc"] * ee.MAKER_FEE \
        + t["exit_price"] * t["size_btc"] * (tk * ee.TAKER_FEE + (1 - tk) * ee.MAKER_FEE)
    t["_slip"] = t["exit_price"] * t["size_btc"] * ee.SLIPPAGE * tk
    t["_netj"] = t["_gross"] - t["_fee"] - t["_slip"]
    t["net_usd"] = t["_netj"]; t["gross_usd"] = t["_gross"]; t["fee_usd"] = t["_fee"] + t["_slip"]
    return t


def _grp(d, by, net="net_usd"):
    g = d.groupby(by, observed=True)
    out = pd.DataFrame({"件数": g.size(), "純益": g[net].sum().round(0),
                        "平均": g[net].mean().round(2), "勝率%": (g[net].apply(lambda x: (x > 0).mean()) * 100).round(1)})
    if "p" in d.columns: out["平均prob"] = g["p"].mean().round(3)
    if "hold_min" in d.columns: out["平均保有"] = g["hold_min"].mean().round(0)
    return out


def _print_params(csv_path):
    """節0: 戦略が記録した使用パラメータ サイドカー（<stem>_params.json）を表示（params_sidecar.write_sidecar が出力）。
    無ければ注記して継続（後方互換）。戦略名で分岐せず JSON の sections を汎用に列挙する（E36/E37 でもそのまま効く）。"""
    sp = Path(csv_path).with_name(f"{Path(csv_path).stem}_params.json")
    print("\n  0. 使用パラメータ（戦略が実行時に記録した実使用値・指標/閾値/TP/SL/TimeExit）")
    if not sp.exists():
        print(f"     （パラメータ記録なし: {sp.name} が無い。戦略にサイドカー出力を足して再走すると表示されます）")
        return
    try:
        pj = json.loads(sp.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"     （パラメータJSON 読み込み失敗: {e}）")
        return
    print(f"     戦略 {pj.get('strategy', '?')} / script {pj.get('script', '?')} / 実験 {pj.get('experiment', '?')}")
    if pj.get("run_args"):
        print(f"     実行引数: {pj['run_args']}")
    for sec, params in (pj.get("sections") or {}).items():
        print(f"     [{sec}]")
        if isinstance(params, dict):
            for k, v in params.items():
                print(f"        {k}: {v}")
        else:
            print(f"        {params}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv"); ap.add_argument("--start"); ap.add_argument("--end"); ap.add_argument("--vs")
    a = ap.parse_args()
    d = _load(a.csv, a.start, a.end)
    if not len(d):
        print("空CSV"); return
    d_raw = d.copy()                                     # 審判（score.py）には CSV 原本を渡す（fill単位・公式 total用）
    d = _judge_cols(d)                                   # 内訳は全節 審判式（現行計器）で集計
    d = _funding_collapse(d)                             # ★公式 funding込み net ＋ 取引(玉)単位に集約（analyze.py と整合・KB §0 取引単位）
    has_p = "p" in d.columns
    name = Path(a.csv).name
    out_path = Path(a.csv).with_name(f"report_{Path(a.csv).stem}.txt")   # 結果一覧を書類保存
    ratchet_io.archive_if_exists(out_path)             # 既存 report を archive へ逃がす（上書きしない・過去保全）
    _rf = open(out_path, "w", encoding="utf-8"); _orig = sys.stdout; sys.stdout = _Tee(_orig, _rf)

    # ===== 0. 使用パラメータ（戦略が記録したサイドカー・指標/閾値/TP/SL/TimeExit）=====
    _print_params(a.csv)

    r = judge.score(d_raw)          # 公式 net / 月別（原本で採点）★0b と A で共用＝重い iterrows を2回呼ばない
    # 比較相手（--vs）は C2（型別）と F（月別）で共用＝1回だけ読む（2026-07-20 C2 に前後比較を足した際に前倒し）
    v = _funding_collapse(_judge_cols(_load(a.vs, a.start, a.end))) if a.vs else None

    # ===== 0b. この表の数字の作り方（CSV列と審判値が違う理由・毎回出す・2026-07-20 まこさん指示）=====
    _print_accounting_note(d_raw, d, r)

    # ===== A. 全体サマリー =====
    days = max(1, (d["exit_time"].max() - d["entry_time"].min()).days)
    eq = d.sort_values("exit_time")["net_usd"].cumsum()
    dd = (eq.cummax() - eq).max()
    sign = (d.sort_values("exit_time")["net_usd"] < 0).astype(int)
    streak = (sign * (sign.groupby((sign != sign.shift()).cumsum()).cumcount() + 1)).max()
    daily = d.groupby(d["exit_time"].dt.date)["net_usd"].sum()
    dn = d.groupby(d["exit_time"].dt.normalize())["net_usd"].sum()
    dn = dn.reindex(pd.date_range(dn.index.min(), dn.index.max(), freq="D"), fill_value=0)
    _sd, _dsd = dn.std(), dn[dn < 0].std()
    sharpe = dn.mean() / _sd * (365 ** 0.5) if _sd and _sd > 0 else 0.0
    sortino = dn.mean() / _dsd * (365 ** 0.5) if _dsd and _dsd > 0 else 0.0
    _w = d.loc[d["net_usd"] > 0, "net_usd"].sum(); _l = abs(d.loc[d["net_usd"] < 0, "net_usd"].sum())
    pf = _w / _l if _l > 0 else float("inf")
    recov = r["total"] / dd if dd > 0 else float("inf")
    print("=" * 70); print(f"  結果レポート: {name}   期間 {d['entry_time'].min().date()}〜{d['entry_time'].max().date()} ({days}日)")
    print("=" * 70)
    _check_exit_jp(d)                                     # 出口理由の日本語訳の追従漏れを機械が検出（表示のみ・net 不関与）
    print(f"  A. 全体  トレード数 {len(d)} / 粗利 ${d['gross_usd'].sum():.0f} / 手数料 ${d['fee_usd'].sum():.0f}"
          f"（{d['fee_usd'].sum()/max(1,abs(d['gross_usd'].sum()))*100:.0f}% ・ ${d['fee_usd'].mean():.2f}/件）")
    print(f"         純益(審判) ${r['total']:.0f} / 月平均 ${r['monthly_avg']:.0f} / 日次純益 ${r['total']/days:.2f}"
          f" / 内訳net(審判式・funding込み・公式一致) ${d['net_usd'].sum():.0f}")
    print(f"         勝率 {(d['net_usd']>0).mean()*100:.1f}% / 最大DD ${dd:.0f} / 最大連敗 {int(streak)} / 日次最悪 ${daily.min():.0f}")
    print(f"         Sharpe {sharpe:.2f} / Sortino {sortino:.2f} / Profit Factor {pf:.2f} / Recovery {recov:.2f}（日次USD純益・年率365）")

    # ===== B. 優先度別 =====
    print("\n  B. 優先度別")
    print(_grp(d, ["priority", "side"]).rename(index=SIDE_JP).rename_axis(["優先度", "方向"]).to_string())

    # ===== C. 出口理由別（LONG/SHORT 列）=====
    print("\n  C. 出口理由別")
    piv = d.pivot_table(index="exit_reason", columns="side", values="net_usd", aggfunc="sum", observed=True).round(0)
    cnt = d.pivot_table(index="exit_reason", columns="side", values="net_usd", aggfunc="size", observed=True)
    piv.columns = [f"純益_{SIDE_JP.get(c, c)}" for c in piv.columns]; cnt.columns = [f"件数_{SIDE_JP.get(c, c)}" for c in cnt.columns]
    cm = pd.concat([cnt, piv], axis=1).fillna(0)
    cm["平均保有"] = d.groupby("exit_reason")["hold_min"].mean().round(0)
    print(cm.rename(index=EXIT_JP).rename_axis("出口理由").to_string())

    # ===== C2. 入口 side × 型別（枝分かれは必ず型で分けて見る・両側戦略は side×型の4分割・見落とし防止 2026-07-15/2026-07-20）=====
    if "ceil_type" in d.columns and d["ceil_type"].notna().any():
        ct = d.copy(); ct["ceil_type"] = ct["ceil_type"].fillna("(不明)")
        _two = ("side" in ct.columns) and (ct["side"].nunique() > 1)   # 両側（ロング＋ショート）が居る＝side×型の4分割で見る（まこさん 2026-07-20）
        if _two:
            print("\n  C2. 入口 side × 型別（down=下落系[天井=直近高値] / flat_up=平坦上昇系[天井=res_hi]・売り/買い × 型 の4分割で分けて見る）")
            print(_grp(ct, ["side", "ceil_type"]).rename(index=SIDE_JP).rename_axis(["方向", "入口型"]).to_string())
            ct["_st"] = ct["side"].map(SIDE_JP).fillna(ct["side"]).astype(str) + "_" + ct["ceil_type"].astype(str)
            piv2 = ct.pivot_table(index="exit_reason", columns="_st", values="net_usd", aggfunc="sum", observed=True).round(0).fillna(0)
            piv2.columns = [f"純益_{c}" for c in piv2.columns]
            print("\n     ├ 出口理由 × 方向_型（純益・4分割）")
        else:
            print("\n  C2. 入口型別（down=下落系[天井=直近高値] / flat_up=平坦上昇系[天井=res_hi]・型で成績が違うので分けて見る）")
            print(_grp(ct, "ceil_type").rename_axis("入口型").to_string())
            piv2 = ct.pivot_table(index="exit_reason", columns="ceil_type", values="net_usd", aggfunc="sum", observed=True).round(0).fillna(0)
            piv2.columns = [f"純益_{c}" for c in piv2.columns]
            print("\n     ├ 出口理由 × 入口型（純益）")
        print(piv2.rename(index=EXIT_JP).rename_axis("出口理由").to_string())

        # ── 型別の前後比較（--vs）＝2026-07-20 新設。
        # 背景: 型別だけ基準との比較が無く、CC が2ファイルを手で引き算して報告し虚偽になった事案
        # （災害SLが無効化されて損失計上が消えただけの変化を「改善」と報告）。機械が差まで出せば手計算の余地が消える。
        # 軸（方向・入口型）の値はデータから取る＝手書きしない。
        if v is not None and "ceil_type" in v.columns and v["ceil_type"].notna().any():
            vt = v.copy(); vt["ceil_type"] = vt["ceil_type"].fillna("(不明)")
            _keys = ["side", "ceil_type"] if _two else ["ceil_type"]
            _n = ct.groupby(_keys, observed=True)["net_usd"].agg(["size", "sum"])
            _b = vt.groupby(_keys, observed=True)["net_usd"].agg(["size", "sum"])
            cmp2 = pd.DataFrame({"今回_件数": _n["size"], "今回_純益": _n["sum"].round(0),
                                 "基準_件数": _b["size"], "基準_純益": _b["sum"].round(0)}).fillna(0)
            cmp2["差_件数"] = (cmp2["今回_件数"] - cmp2["基準_件数"]).astype(int)
            cmp2["差_純益"] = (cmp2["今回_純益"] - cmp2["基準_純益"]).round(0)
            _idx = ["方向", "入口型"] if _two else ["入口型"]
            print(f"\n     ├ 型別の前後比較（基準 --vs = {Path(a.vs).name}）")
            print(cmp2.rename(index=SIDE_JP).rename_axis(_idx).to_string())
            # 出口理由 × 型 の差（どの出口が増減して差が出たか＝「net が良くなった理由」を機械が示す）
            _nx = ct.groupby(_keys + ["exit_reason"], observed=True)["net_usd"].sum()
            _bx = vt.groupby(_keys + ["exit_reason"], observed=True)["net_usd"].sum()
            dx = (_nx.subtract(_bx, fill_value=0.0)).round(0)
            dx = dx[dx != 0].sort_values()
            if len(dx):
                print("\n     ├ 出口理由 × 型 の差（今回−基準・0以外／マイナス＝この出口で悪化・プラス＝改善）")
                _df = dx.reset_index(); _df.columns = _idx + ["出口理由", "差_純益"]
                _df["出口理由"] = _df["出口理由"].map(EXIT_JP).fillna(_df["出口理由"])
                if _two: _df["方向"] = _df["方向"].map(SIDE_JP).fillna(_df["方向"])
                print("     " + _df.to_string(index=False).replace("\n", "\n     "))

    # ===== D. サイズ / add 別（増強）=====
    print("\n  D. サイズ・add別（mean が右肩上がりなら買い増しが効いている）")
    dd2 = _grp(d, "size_btc"); dd2["平均買増"] = d.groupby("size_btc")["add_count"].mean().round(2)
    print(dd2.rename_axis("サイズ").to_string())

    # ===== E. ベスト / ワースト（入った時の指標値＝閾値の組み合わせ付き・ベスト/ワースト10）=====
    _ind = ["adx_at_entry", "bb_mid_slope_at_entry", "stoch_k_at_entry", "stoch_d_at_entry", "atr_14", "rsi_at_entry"]
    cols = [c for c in ["entry_time", "exit_reason", "hold_min", "add_count", "net_usd"] if c in d.columns] \
        + [c for c in _ind if c in d.columns]
    _cjp = {"entry_time": "日時", "exit_reason": "出口理由", "hold_min": "保有分", "add_count": "add数", "net_usd": "純益",
            "adx_at_entry": "ADX", "bb_mid_slope_at_entry": "bb傾き", "stoch_k_at_entry": "stochK",
            "stoch_d_at_entry": "stochD", "atr_14": "ATR", "rsi_at_entry": "RSI"}
    def _disp(t):
        t = t.copy()
        for c in _ind + ["hold_min", "net_usd"]:
            if c in t.columns: t[c] = t[c].round(1)
        t = t.rename(columns=_cjp)
        if "出口理由" in t.columns: t["出口理由"] = t["出口理由"].map(EXIT_JP).fillna(t["出口理由"])
        return t
    print("\n  E. ベスト10（入った時の指標値＝どの閾値の組み合わせで勝ち負けしたか）")
    print(_disp(d.nlargest(10, "net_usd")[cols]).to_string(index=False))
    print("     ワースト10")
    print(_disp(d.nsmallest(10, "net_usd")[cols]).to_string(index=False))

    # ===== F. 月別（+AI vs V9）=====
    print("\n  F. 月別 純益（審判）")
    mo = (d.assign(_m=d["entry_time"].dt.strftime("%Y-%m")).groupby("_m")["net_usd"]    # ★玉単位（A節・合計と整合）
          .agg(純益="sum", 件数="size").rename_axis("月")); mo["純益"] = mo["純益"].round(0)
    if a.vs:
        # 比較相手 v は 196行で読み込み済み（C2 と共用＝2回読まない）・玉単位/funding込みで今回と単位を揃えてある
        dm = d.assign(_m=d["entry_time"].dt.strftime("%Y-%m")).groupby("_m")["net_usd"].agg(["sum", "size"])
        vm = v.assign(_m=v["entry_time"].dt.strftime("%Y-%m")).groupby("_m")["net_usd"].agg(["sum", "size"])
        # 列名は比較相手のファイル名から自動生成（旧「AI vs V9」は ML戦略×手動戦略V9 時代の手書き固定値＝
        # --vs に何を渡しても "V9" と表示され本番の手動V9と混同しうる・2026-07-20 まこさん指摘で是正）
        print(f"   今回 = {Path(a.csv).name}   /   基準(--vs) = {Path(a.vs).name}")
        cmp = pd.DataFrame({"今回_純益": dm["sum"].round(0), "今回_件数": dm["size"],
                            "基準_純益": vm["sum"].round(0), "基準_件数": vm["size"]}).fillna(0).rename_axis("月")
        print(cmp.to_string()); print(f"   合計  今回 ${d['net_usd'].sum():.0f}({len(d)}件)  vs  基準 ${v['net_usd'].sum():.0f}({len(v)}件)  → 差 ${d['net_usd'].sum()-v['net_usd'].sum():+.0f}")
    else:
        print(mo.to_string())

    # ===== F2/F3/F4. 時系列（月別×出口理由/サイズ・1日あたり）=====
    d["_m"] = d["entry_time"].dt.strftime("%Y-%m")
    print("\n  F2. 月別 × 出口理由（純益）")
    print(d.pivot_table(index="_m", columns="exit_reason", values="net_usd", aggfunc="sum", observed=True)
          .rename(columns=EXIT_JP).round(0).fillna(0).rename_axis("月").to_string())
    print("\n  F3. 月別 × サイズ・add（純益／件数）")
    pvs = d.pivot_table(index="_m", columns="size_btc", values="net_usd", aggfunc=["sum", "size"]).fillna(0).round(0)
    pvs.columns = [f"{'純益' if a=='sum' else '件数'}_{b}" for a, b in pvs.columns]
    print(pvs.rename_axis("月").to_string())
    adays = d["entry_time"].dt.date.nunique()
    print(f"\n  F4. 1日あたり（取引のあった {adays} 日で平均）")
    print(f"   トレード数 {len(d)/adays:.2f} 件/日 ・ 純益 ${r['total']/adays:.2f}/取引日")
    # エントリー数（新規建て玉 ＋ 買い増し）＝まこさんが見る頻度の単位（2026-06-21・暦日基準で 10/日 目標と照合）
    if "position_id" in d_raw.columns and "add_count" in d_raw.columns:
        def _ecnt(df):
            return df["position_id"].nunique(), int(df.groupby("position_id")["add_count"].max().sum())
        _no, _ef = _ecnt(d_raw)
        print(f"   エントリー数（暦{days}日平均・新規建て玉 / 新規+買い増し）: 全体 {_no/days:.2f} / {_ef/days:.2f} 件/日")
        if "side" in d_raw.columns:
            _parts = []
            for _sd in ("SHORT", "LONG"):
                _sub = d_raw[d_raw["side"] == _sd]
                if len(_sub):
                    _n2, _e2 = _ecnt(_sub)
                    _parts.append(f"{_sd} {_n2/days:.2f} / {_e2/days:.2f}")
            if _parts:
                print("     方向別（新規建て玉 / 新規+買い増し 件/日）: " + " ・ ".join(_parts))
    er = (d["exit_reason"].map(EXIT_JP).value_counts() / adays).round(2)
    print("   出口理由別 件数/日: " + " / ".join(f"{k} {v}" for k, v in er.items()))
    sz = (d["size_btc"].value_counts().sort_index() / adays).round(2)
    print("   サイズ別 件数/日: " + " / ".join(f"{k} {v}" for k, v in sz.items()))

    # ===== G. 指標帯別 net/勝率 =====
    print("\n  G. 指標帯別（エッジがどの帯に居るか・帯の区切りは実験間で固定＝版をまたいで同じ物差しで比べる）")
    d = d.copy()
    if "atr_14" in d.columns and "entry_price" in d.columns:
        d["atr_pct"] = (d["atr_14"] / d["entry_price"] * 100)
    if "stoch_d_at_entry" in d.columns and "stoch_k_at_entry" in d.columns:
        d["stoch_gap"] = (d["stoch_d_at_entry"] - d["stoch_k_at_entry"])
    _e = lambda x: "" if abs(x) >= 9e8 else f"{x:g}"
    bands = {
        "ADX":       ("adx_at_entry",          [0, 20, 25, 30, 35, 40, 50, 9e9]),
        "ATR%":      ("atr_pct",               [0, 0.2, 0.3, 0.4, 0.5, 0.7, 9e9]),
        "stochギャップ": ("stoch_gap",          [0, 0.3, 1, 3, 6, 9e9]),
        "bb傾き":    ("bb_mid_slope_at_entry",  [-9e9, -30, -20, -10, 0, 9e9]),
    }
    for label, (col, edges) in bands.items():
        if col not in d.columns: continue
        lab = [f"{_e(edges[i])}〜{_e(edges[i+1])}" for i in range(len(edges) - 1)]
        d["_b"] = _band(d[col], edges, lab)
        print(f"   [{label}]")
        print("   " + _grp(d, "_b").drop(columns=["平均保有"], errors="ignore").rename_axis("帯").to_string().replace("\n", "\n   "))

    # ===== H. 予測確率帯別（ML のとき）=====
    if has_p:
        print("\n  H. 予測確率帯別（予測の自信度が儲けと対応しているか＝較正・p列がある時だけ出る）")
        d["_pb"] = _band(d["p"], [0, 0.4, 0.5, 0.56, 0.6, 0.7, 1.01], ["〜0.4", "0.4〜0.5", "0.5〜0.56", "0.56〜0.6", "0.6〜0.7", "0.7〜"])
        print("   " + _grp(d, "_pb").drop(columns=["平均保有"], errors="ignore").rename_axis("確率帯").to_string().replace("\n", "\n   "))

    # ===== I. MFE/MAE 別 =====
    if "mfe_usd" in d.columns and "mae_usd" in d.columns:
        print("\n  I. MFE(含み益ピーク)/MAE(含み損ピーク)別（出口が利益を取り逃していないか）")
        d["_mfe"] = _band(d["mfe_usd"], [-1, 5, 15, 30, 60, 9e9], ["〜5", "5〜15", "15〜30", "30〜60", "60〜"])
        gm = _grp(d, "_mfe").drop(columns=["平均保有"], errors="ignore").rename_axis("MFE帯")
        gm["平均MFE"] = d.groupby("_mfe", observed=True)["mfe_usd"].mean().round(1)
        gm["取り逃し率%"] = (100 * (1 - d.groupby("_mfe", observed=True)["net_usd"].mean() /
                                    d.groupby("_mfe", observed=True)["mfe_usd"].mean())).round(0)
        print("   " + gm.to_string().replace("\n", "\n   "))

    # ===== J. コスト分解（審判式・出口別・②執行の判定材料・2026-06-12 まこさん承認）=====
    dj = d                                                # 全節 審判式に統一済み（_judge_cols）
    print("\n  J. コスト分解（審判式＝現行計器・funding除く・gross黒字なのにnet赤=②執行＝手数料負け）")
    gj = dj.groupby("exit_reason")
    jt = pd.DataFrame({"件数": gj.size(), "gross": gj["_gross"].sum().round(0), "手数料": gj["_fee"].sum().round(0),
                       "slip": gj["_slip"].sum().round(0), "net": gj["_netj"].sum().round(0)})
    print(jt.rename(index=EXIT_JP).rename_axis("出口理由").to_string())
    print(f"   合計: gross ${dj['_gross'].sum():,.0f} / 手数料 ${dj['_fee'].sum():,.0f}"
          f"（gross比 {dj['_fee'].sum()/max(1e-9, abs(dj['_gross'].sum()))*100:.0f}%）"
          f" / slip ${dj['_slip'].sum():,.0f} / net ${dj['_netj'].sum():,.0f}")

    # ===== K. 期待値4要素（勝率×平均勝ち−負率×平均負け・trade_analysis_methods_kb §1）=====
    def _exp_row(t, label):
        win = t[t["_netj"] > 0]; los = t[t["_netj"] <= 0]
        wr = len(win) / max(1, len(t))
        aw = float(win["_netj"].mean()) if len(win) else 0.0
        al = abs(float(los["_netj"].mean())) if len(los) else 0.0
        return {"集団": label, "件数": len(t), "勝率%": round(wr * 100, 1), "平均勝ち$": round(aw, 2),
                "平均負け$": round(al, 2), "期待値$/件": round(wr * aw - (1 - wr) * al, 2),
                "コスト$/件": round(float((t["_fee"] + t["_slip"]).mean()), 2),
                "gross$/件": round(float(t["_gross"].mean()), 2)}
    rows_k = [_exp_row(dj, "今回")]
    if a.vs:
        vj = v                                            # _judge_cols 済み
        rows_k.append(_exp_row(vj, "ベースライン"))
    print("\n  K. 期待値4要素（どのレバーが動いたかを特定・--vs でベースライン比較）")
    print("   " + pd.DataFrame(rows_k).set_index("集団").to_string().replace("\n", "\n   "))

    # ===== L. 限界分解（--vs 時のみ・追加/削除した玉だけの採算・件数レバーの事前/事後ゲート）=====
    if a.vs:
        vset = set(v["entry_time"]); dset = set(d["entry_time"])
        print("\n  L. 限界分解（ベースラインとの集合差・breakeven倍率=平均gross÷往復コスト・<1=手数料負け確定/<1.5=危険域）")
        for lbl, t in (("追加した玉", dj[~dj["entry_time"].isin(vset)]), ("削った玉", vj[~vj["entry_time"].isin(dset)])):
            if not len(t):
                print(f"   {lbl}: なし"); continue
            ag = float(t["_gross"].mean()); ac = float((t["_fee"] + t["_slip"]).mean())
            be = ag / ac if ac > 0 else float("inf")
            print(f"   {lbl}: {len(t)}件 / gross ${t['_gross'].sum():,.0f} / net ${t['_netj'].sum():,.0f}"
                  f" / 平均gross ${ag:.2f}/件 / 往復コスト ${ac:.2f}/件 / breakeven倍率 {be:.2f}")

    # ===== M. 週次チャート（売買記録を価格に重ねた PNG・report とセット・read-only）=====
    # plot_trades.py を呼び、ISO週（月曜始まり）で トレード数 最多/最少 ＋ NET利益 最大/最小 の週を1枚ずつ出力（同一週は統合＝最大4枚）。トレード数は玉単位（A節 件数と整合）。
    print("\n  M. 週次チャート（plot_trades.py 自動出力・トレード最多/最少＋NET最大/最小の週＝results/priority_rebuild/viz/）")
    try:
        import subprocess
        wkg = d.assign(_wk=d["entry_time"].dt.to_period("W-SUN")).groupby("_wk")
        cnt = wkg.size(); net = wkg["net_usd"].sum()
        cand = []                                           # (タグ, 週)・同一週は下で統合
        if len(cnt):
            cand += [("トレード数最大", cnt.idxmax()), ("トレード数最小", cnt.idxmin()),
                     ("net利益最大", net.idxmax()), ("net利益最小", net.idxmin())]
        seen = {}; order = []                               # 週→タグ群（重複週を1枚に統合＝最大4枚）
        for tag, w in cand:
            if w not in seen: seen[w] = []; order.append(w)
            if tag not in seen[w]: seen[w].append(tag)
        plot_script = Path(__file__).resolve().parent.parent / "dashboard" / "plot_trades.py"
        for w in order:
            tags = "・".join(seen[w]); ws = w.start_time.normalize(); we = ws + pd.Timedelta(days=7)
            rp = subprocess.run([sys.executable, str(plot_script), str(a.csv),
                                 "--start", ws.strftime("%Y-%m-%d"), "--end", we.strftime("%Y-%m-%d"),
                                 "--label", tags],                       # カテゴリ名を PNG タイトルに（表示のみ・net/売買データ不変）
                                capture_output=True, text=True)
            lines = [l for l in rp.stdout.splitlines() if l.strip()]
            png = next((l.split("[出力]", 1)[1].strip() for l in lines if "[出力]" in l), "")
            summ = next((l.strip() for l in reversed(lines) if "net" in l), "")
            print(f"   [{tags}] {ws.date()}〜{we.date()}（{int(cnt[w])}トレード・NET ${net[w]:+.0f}）→ {png or '(出力なし)'}")
            if summ:
                print(f"      {summ}")
            # ★ PNG 強制出力（黙って表示だけ＝データ改ざん禁止・まこさん 2026-07-02）: 実ファイルが無ければ STOP
            if not png or not Path(png).exists():
                sys.stderr.write(f"[STOP] 週次チャート PNG 未生成（{tags} {ws.date()}〜{we.date()}）: stderr={rp.stderr.strip()}\n")
                sys.exit(2)
    except Exception as e:
        sys.stderr.write(f"[STOP] 週次チャート生成 失敗（PNG は強制・黙って skip しない・まこさん 2026-07-02）: {e}\n")
        sys.exit(2)

    sys.stdout = _orig; _rf.close()
    print(f"\n[保存] この結果一覧を書類化 → {out_path}（IDEで開いて確認できます）")


if __name__ == "__main__":
    main()

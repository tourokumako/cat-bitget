#!/usr/bin/env python3
"""strat_base.py — 全戦略（E35 / E36 / 今後 E37…）共通の土台モジュール（中立）。

★ここを直すと全戦略に効く。戦略固有のロジック（箱づくり・売買エンジン run_continuous・
  hold-ML 判別・出口・件数レバー等）は各戦略ファイル（e35_range_oscillation.py /
  e36_short_oscillation.py …）に置く。
  ＝「E36 を直すつもりで E35 を触る／E35 と E36 を取り違える」混乱を物理的に防ぐための
  土台分離（まこさん 2026-06-23・E35/E36 切り分け）。各戦略はこの土台を import するだけで始められる。

役割（全戦略で不変なものだけ・YAGNI＝今分かる共通項のみ・新戦略で足りなければその時足す）:
  ① データ読み込み方   : load_5m（5分足 CSV を読む・指標付与は各戦略＝使う指標が戦略ごとに違う）
  ⑤ cap検査・funding   : _verify_cap（H1・全建玉合計≤0.12）/ _funding_cost（取引所 funding・8h 境界）
  ⑥ 出力処理           : _output_and_report（命名/archive/上書き防止は ratchet_io へ委譲・
                          strategy/script/sections は各戦略が渡す＝各戦略が自分を describe）
  ⑦ 取引所・予算の定数 : UNIT / CAP / TTL / ENTRY_OFFSET / COST_FLOOR（eval_engine / e34v1 由来・全戦略不変）

net 計算には不関与（売買ロジックは各戦略・最終 net は score.py が独立再計算）。
"""
from __future__ import annotations
import pathlib
import sys
from datetime import timezone

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import eval_engine as ee                    # noqa: E402  確定コスト定数 + funding 境界（改造禁止・import のみ）
import e34_range_zscore_taker as e34v1      # noqa: E402  CSV / SIZE / COST_FLOOR（読み込み方・定数の出所）
import periods                              # noqa: E402  検証期間の唯一の正本（学習/採点/封印・E31 窓・SSOT）
import params_sidecar as _psc              # noqa: E402  使用パラメータ サイドカー（read専用メタ・審判に不関与）
import ratchet_io                          # noqa: E402  出力の命名/archive/上書き防止（全戦略共通・net 不関与）

RATCHET = ROOT / "results" / "priority_rebuild" / "ratchet"

# ── 検証期間（periods.py が唯一の正本・SSOT・手打ち禁止）──────────────────────────────
TRAIN_END = periods.TRAIN_END               # 学習境界（< TRAIN_END で fit）＝periods 正本（E31: 〜2025-02）
SC_START = periods.SCORE_START              # 採点窓 開始＝periods 正本（2025-06-01）
SCORE_END = periods.SEAL_START              # 採点スライスの排他終端＝封印開始（entry < SCORE_END）
SEAL_START = periods.SEAL_START             # 封印開始＝periods 正本（full 出力は < SEAL_START・封印は不参照）

# ── ⑦ 取引所・予算の定数（全戦略不変）──────────────────────────────────────────────
CAP = 0.12                                  # 予算=全建玉（LONG+SHORT）合計の上限（H1・CLAUDE §0-2）
UNIT = e34v1.SIZE                           # 0.024 BTC（add 単位・H10）
TTL = ee.DEFAULT_TTL                        # 指値 TTL 3 本
ENTRY_OFFSET = ee.ENTRY_LIMIT_OFFSET        # 0.0001
COST_FLOOR = e34v1.COST_FLOOR               # 0.0020（TP が建値±床を超える時だけ武装）


def load_5m(smoke: int) -> pd.DataFrame:
    """① 5分足 CSV を読み ts 付与（smoke 指定で先頭 N バーのみ）。
    指標付与（add_indicators / 箱 / レンジ判定 等）は各戦略が行う＝戦略ごとに使う指標が違うため土台では行わない。"""
    df = pd.read_csv(e34v1.CSV)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df = df.reset_index(drop=True)
    if smoke:
        df = df.iloc[:smoke].reset_index(drop=True)
    return df


def _funding_cost(side: int, entry_ts, exit_ts, size: float, mark: float) -> float:
    """⑤ 保有中 8h 境界ごと funding（LONG dir=+1 払い / SHORT dir=-1 受取）。score.py と同式。"""
    e = pd.Timestamp(entry_ts).to_pydatetime().replace(tzinfo=timezone.utc)
    x = pd.Timestamp(exit_ts).to_pydatetime().replace(tzinfo=timezone.utc)
    cost = 0.0
    for _ in ee._funding_boundaries(e, x):
        cost += side * size * mark * ee.FUNDING_RATE_8H
    return cost


def _verify_cap(trades) -> float:
    """⑤ 出力 trades の区間会計（score.py.assert_position_cap と同式）で同時保有 max（LONG+SHORT 合算）を実測。
    fill 単位記録なので区間会計＝実保有。自己チェックを審判と一致させ false pass を防ぐ（H1）。"""
    ev = []
    for t in trades:
        sz = float(t["size_btc"])
        ev.append((pd.Timestamp(t["entry_time"]), sz))
        ev.append((pd.Timestamp(t["exit_time"]), -sz))
    ev.sort(key=lambda x: (x[0], x[1]))                   # 同時刻は決済(マイナス)を先に（score.py と同じ）
    cur = mx = 0.0
    for _t, s in ev:
        cur = round(cur + s, 9); mx = max(mx, cur)
    return mx


def _output_and_report(t: pd.DataFrame, suffix: str, *, stem: str, strategy: str, script: str,
                       sections: dict, tag: str | None = None) -> None:
    """⑥ trades を 全期間/採点窓/precheck に分けて出力＋月別サマリ（全戦略共通・各戦略の thin wrapper が呼ぶ）。
    stem=出力ファイル名の幹（例 e35_oscillation / e36_short_oscillation＝report 自動E番号化）。
    strategy/script/sections=各戦略が渡す（戦略の identity・サイドカー内容＝各戦略が自分を describe）。
    ★命名/archive/上書き防止は ratchet_io（全戦略共通・net 不関与・命名/ファイル移動のみ）:
      - tag 指定時: suffix を `_<tag>_<NNN>` 連番化（ユニーク）＋同 stem の旧実験出力を archive へ退避（直下=現役のみ）。
      - 書き出し前に既存があれば archive へ逃がす（上書きしない・過去保全）＝全呼び出し元に効く。
      新しい戦略（e37/38/39…）もこの関数を thin wrapper 経由で呼べば同じ仕組みを自動で踏襲する。"""
    RATCHET.mkdir(parents=True, exist_ok=True)
    if tag:                                                     # 実験タグ指定時のみ連番化＋旧実験退避（tag 無=安定名 base は不変）
        suffix = ratchet_io.tagged_suffix(stem, suffix, tag, RATCHET)
        ratchet_io.archive_prior_experiments(stem, suffix, RATCHET)
    base = RATCHET / f"trades_{stem}{suffix}.csv"
    out_full = base
    out_train = base.with_name(base.stem + "_train.csv")
    out_score = base.with_name(base.stem + "_score.csv")
    t_full = t[t.entry_time < SEAL_START].reset_index(drop=True)
    t_score = t[(t.entry_time >= SC_START) & (t.entry_time < SCORE_END)].reset_index(drop=True)
    for _p in (out_full, out_score, out_train):                # 上書きしない＝既存は archive へ逃がしてから書く
        ratchet_io.archive_if_exists(_p)
    t_full.to_csv(out_full, index=False)
    t_score.to_csv(out_score, index=False)
    t[t.entry_time < TRAIN_END].reset_index(drop=True).to_csv(out_train, index=False)
    # 使用パラメータをサイドカー出力（report.py 節0 が表示・read専用メタ・net 計算に不関与）
    _exp = suffix.lstrip("_")
    for _cp in (out_full, out_score, out_train):
        _psc.write_sidecar(_cp, strategy=strategy, script=script, experiment=_exp, sections=sections)
    print(f"  [params] 使用パラメータを各CSVの隣に記録（report.py 節0 で表示）: {out_full.stem}_params.json 他")
    n_days = max((t_score.entry_time.max() - t_score.entry_time.min()).total_seconds() / 86400.0, 1.0) if len(t_score) else 1.0
    print(f"  [出力] 全期間 {out_full.name}（封印除外後 {len(t_full)}）/ 採点窓 {out_score.name}({len(t_score)}・{len(t_score)/n_days:.2f}/日) / precheck {out_train.name}")
    if len(t_score):
        sm = t_score.assign(m=t_score.entry_time.dt.strftime("%Y-%m")).groupby("m")["net_usd"].agg(["count", "sum"]).round(1)
        print(f"\n  採点窓 {periods.SCORE_START_STR}〜{periods.SCORE_END_STR} 月別（CSV net・参考＝正式は score.py）:\n" + sm.to_string())
        print(f"  採点窓 合計 CSV net ${t_score.net_usd.sum():.1f} / 件 {len(t_score)} / 勝率 {(t_score.net_usd > 0).mean():.1%}")
        print(f"  出口別 件数: {dict(t_score['exit_reason'].value_counts())}")
    print("\n  → 判定は score.py（precheck → score.py の数字）:")
    print(f"     precheck.py {out_train.name} --authorize {out_score.name}")
    print(f"     score.py {out_score} --start {periods.SCORE_START_STR} --end {periods.SCORE_END_STR}（既定で正本窓・periods）")

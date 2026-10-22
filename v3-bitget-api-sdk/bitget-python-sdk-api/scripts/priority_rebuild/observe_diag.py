#!/usr/bin/env python3
"""observe_diag.py — 建玉の観察と探索を、決まった型で機械が全部出す道具（read-only 診断）

この道具の目的（まこさん確定 2026-07-26・逐語・ここが正本）
--------------------------------------------------------------------------
・新規で Entry/Exit ロジックを構築する際に、
  設定した戦略や条件に沿った、指標、閾値、時間足、パラメータの組み合わせロジックを見つける
・既存 Entry/Exit に対しては、目標達成するために改善すべき点を見つける

経緯: この目的がどこにも書かれていなかったため、何ができて何ができないかが誰にも整理できず、
  出力が「取り逃しがある」のような目標と無関係な当たり前の指摘に留まっていた
  （まこさん「次へつなげるためになにをすべきかよくわからない」2026-07-26）。
  以後、この道具に足す機能は上の2つの目的に紐づける。紐づかない機能は足さない。

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
・**既存ロジックの検証では 取る（建値からの % TP）を削除したままにする**＝現行ロジックの TP を変えろという
  指示は無い（まこさん 2026-07-21）。TP は現行ロジック（レンジ幾何の2段利確）のまま＝ここでは触らない。
  selftest が sc_take の不在を検査する（この検査は残す）。
・**新規ロジックの検証では 出口の組み合わせを探す**（まこさん OK 2026-07-26＝「新しい入口候補に対して出口の
  組み合わせを探す機能がない」の是正）。上の削除は「既に動いている E37 の TP を触るな」であって、まだ玉の無い
  新しい入口候補の出口まで固定しろという意味ではない＝適用範囲を分ける。振るのは 利確 × 損切り × 保有の上限 の
  3軸で、刻みは config（場面ごとに上書き可）。順位づけは勝率でなく概算期待値。値決めは層3・採否は採点窓のまま。
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

Entry 候補観察（まだ玉のない新候補の層1・2026-07-25 まこさん承認）
--------------------------------------------------------------------------
① 計画  : python3 observe_diag.py --scene S2 --plan
② 本走  : まこさんの OK が出てから python3 observe_diag.py --scene S2
場面バー（例＝レンジ内で mid 以上への戻り）を母集団に、機械ラベル（Triple Barrier 型）で勝ち負けを付け、
カタログ全体で 1次元の分離力 → 異種カテゴリ AND（2〜3条件・時間足2種以上）のコンフルエンス探索まで出す。
場面の定義・バリア・探索条件は observe_config.json の scenes / conf_*（レンジ専用でなく場面を足せば他戦略でも使える）。
出た組は材料まで＝値決めは層3 engine_tuner・採否は採点窓 score.py（まこさん）。

データと指標の検査（歩0・2026-07-30 まこさん OK）
--------------------------------------------------------------------------
python3 observe_diag.py --inspect <5分足CSV>
5段＝①元データ（欠け・重複・価格の整合・段差） ②足の組み立て（集計・区切り・閉じる前の漏れ・内訳）
③指標の計算式（代表指標の独立計算との突き合わせ＋性質テスト＋全列の3区分） ④未来参照（切り詰め再計算＋静的検査）
⑤欠損と有効標本数（歩2 の適合制約の基礎データ）。read-only・結果は機械出力・上流で間違いが出たら下流は全部疑う。

自己検査: python3 observe_diag.py --selftest
"""
from __future__ import annotations

import datetime
import hashlib
import pathlib
import re
import sys
import tempfile          # ★2026-09-08（監査 cp32）＝番人 T-n・T-o が一時のフォルダで試す
import warnings

import numpy as np
import pandas as pd

# 検証期間は periods.py が正本（H8・手打ち禁止）。SEARCH/CONFIRM はデータ検査（歩0）の
# 「欠けと窓の重なり判定」「有効標本数の集計」だけに使う＝観察・探索は採点窓のまま。
from periods import (SCORE_START, SCORE_END, SEARCH_START, SEARCH_END,   # noqa: E402
                     CONFIRM_START, CONFIRM_END)
# 出力の保管は全戦略・全ツール共通の書き出し処理に委譲する（命名/archive/上書き防止・§3.1）
import ratchet_io   # noqa: E402
# 指標カタログの正しさの証明に使う参照表（定義表・外部ライブラリ照合・独立実装・既知答え・歩0）
import indicator_reference_diag as iref   # noqa: E402
import regime_label as rl   # noqa: E402  答え合わせに使う正解ラベル（札）を作る、ただ1つの場所（M2-F-6d）

warnings.filterwarnings("ignore")

# ══ 呼び出し側から変更できない定数 ═══════════════════════════════════════
# フェーズの名前は「何をするか」を動詞で書く（まこさん指示 2026-07-26）。
#   旧名は「母集団」「機構別分解」のように、読んでも何をするか分からない言葉だった。
#   英語をそのまま日本語にした言葉と CC の造語は使わない。
SECTIONS = [
    "0 分析する玉の全体を、型と出口理由と勝ち負けで数える",
    "1 どの撤退の仕組みが切ったかを分ける（概算・ものさしはその走行で実際に使った値から解決する）",
    "2 建てた瞬間の相場の状態を、出口と型ごとに見る",
    "3 保有している間の値動きを、出口と型ごとに見る",
    "4 決済した瞬間の相場の状態を、出口と型ごとに見る",
    "5 決済した後に価格がどうなったかを追う（episode_gap_h 時間）",
    "6 前後の玉との違いを見る（価格差・時間間隔・レンジ内で何番目か）",
    "7 負けを切ったときに勝ち玉に当たる量を測る",
    "8 改善の条件の候補を探す（side×型ごとに search_modes で選んだ系統だけ・前半で探して後半で確認）",
    "9 両方の期間でプラスの候補だけを抜き出す（機械が抽出・手書きなし）",
    "10 この結果から次に何をすべきかを出す（戦略名を見ず、売買記録の共通列だけを使う）",
    "11 増やす方向＝建てなかった場面のうち、建てていれば取れた条件を探す（建値からの%で判定・枠は見ない）",
    "12 まとめ＝上の節で機械が出した数字のうち、次の調整に使う3つだけを1画面に並べる（新しい計算はしない）",
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
TF_RULE = {"1m": "1min", "3m": "3min",
           "5m": "5min", "10m": "10min", "15m": "15min", "30m": "30min", "1h": "1h",
           "2h": "2h", "4h": "4h", "6h": "6h", "12h": "12h", "1d": "1D"}
# ↑ 10m は 2026-08-07 まこさん指示「時間足に10mも追加したい」で追加（5m データからの resample＝他の足と同じ作り）
# ↑ 1m・3m は 2026-08-16 の段7 で追加（要件 R15「扱う時間足を1分足から1日足まで広げる」）。
#   ★この2つだけは 5分足から作れない（5分足を細かく割ることはできない）＝1分足の元データを読む。
#   作り方＝1m はそのまま／3m は1分足からの resample。未来を見ない式は他の足と同じものを使う
#   （足が閉じた時刻まで index を進めてから 5分足の index へ ffill）。
SUB_5M_TF = ("1m", "3m")                      # 5分足より短い足＝1分足の元データが材料
ONE_MIN_CSV = "data/BTCUSDT-1m-binance-taker-2023-06-01_2026-06-30.csv"   # ★2026-09-08（設計書 insp5-frame-and-table-tidy-20260908 の G）＝助走250日を覆うよう 2023-06 から取り足した（旧＝2023-11-01 から。値決め窓 2024-03-01 の250日前＝2023-06-25 に約4か月 足りなかった）
# ↑ 段7 の 7-1 で作ったもの（2026-08-11・1,226,880本・1分グリッドの欠け0・重複0・境目の段差0）。
#   5分足の正本（Binance Spot 系列）と同じ作りで、時刻はバーの始まりの時刻。

# ★2026-09-08（監査 cp31 の Critical 1・設計書 insp5-path-and-tidy-head-20260908 の A）
#   ＝5分足の正本のパスを、ここ1か所に置く。
#   直す前＝番人 T-i を呼ぶコマンドの6か所（壊すプログラム3本と、完成の条件3行）に
#     同じファイル名が書き写してあった。このプロジェクトは5分足を取り足すとき
#     「新ファイルを別名で保存」する決まりなので（要件定義書 §8.2.1.1 の④）、
#     取り足すと6か所とも古いファイルを指したままになる。
#     ＝番人は古いファイルの末を見て「覆っている」と言い、検査5 は新しいファイルで走って落ちる
#     （監査 cp31 が、その状態を実際に作って再現した）。
#   ★取り足したら、ここだけを直す。直し忘れは番人 T-m が見つける（_newer_5m_files）。
BARS_CSV = "data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv"


def load_config(path: str | None = None) -> dict:
    import json
    p = path or CONFIG_PATH
    with open(p, encoding="utf-8") as f:
        cfg = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    cfg["_source"] = p
    bad = [t for t in cfg["timeframes"] if t not in TF_RULE]
    if bad:
        raise SystemExit(f"[設定] 知らない足: {bad}（使えるのは {list(TF_RULE)}）")
    # ★2026-08-16（段7）＝「1m は使わない」の拒否を外した。
    #   外した根拠は2つ。①CLAUDE.md の 1m 禁止は 2026-06-02 に まこさんが撤回している
    #   （逐語「ML 学習で 1m/3m が有効と実証されれば有効化可」）②engine_tuner の要件 R15
    #   ＝「扱う時間足を1分足から1日足まで広げる」（まこさん指示 2026-08-08）。
    #   代わりに、1m・3m を使うなら元データが実在することを、走らせる前に確かめる。
    if any(t in cfg["timeframes"] for t in SUB_5M_TF):
        import pathlib
        p = (pathlib.Path(__file__).resolve().parent.parent.parent / ONE_MIN_CSV)
        if not p.exists():
            raise SystemExit(
                f"[設定] {sorted(set(cfg['timeframes']) & set(SUB_5M_TF))} を使う設定だが、"
                f"1分足の元データが無い: {p}")
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
    # 2026-07-30 取り直し（2024-04〜2026-06）。旧 2025-06〜2026-02 版は data/ に温存
    # ★2026-09-05（M2-C-4）＝値決め窓の先頭（2024-03-01）から在るファイルへ指し先を移した。
    #   直す前は 2024-04-01 版で、値決め窓の最初の1ヶ月が空のままだった（next_step §6 の26番）。
    #   ★データの取り足しはしていない＝2024-03-01 版のファイルは既に在った（実測＝1,226,881行・
    #   先頭 2024-03-01 00:00:00／末尾 2026-06-30 23:59:00）。
    "CVD": ("../../data/BTCUSDT-1m-binance-taker-2024-03-01_2026-06-30.csv", "timestamp", None),
}


# ══ 指標の部品 ══════════════════════════════════════════════════════════
def _rsi(c, n):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    # 全部上昇の窓は RS=∞ → RSI=100（世界標準の慣例・TradingView / ta と同じ）。
    # 旧式は 0 を NaN に置換して欠損にしていた＝標準とずれるので是正（2026-07-30・検査3 で発見）。
    return 100 - 100 / (1 + up / dn)


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


def _rci_slow(c, n=9):
    """RCI の元の実装（1本ずつ Python で回す形）。★速い方の答え合わせ専用に残す（消さない）。"""
    r = c.rolling(n).apply(
        lambda x: 1 - 6 * ((pd.Series(x).rank() - pd.Series(range(1, n + 1))) ** 2).sum() / (n * (n * n - 1)),
        raw=True)
    return r * 100


def _rci(c, n=9):
    """RCI＝時間の並びと値段の並びの順位相関 ×100。

    ★2026-08-11（段6 の 6-8）に、計算のしかたを変えた。**値は1つも変えない。**
      前は1本ずつ Python の関数で回していて、実測で **250,000本・1つの本数につき 114 秒** かかった。
      本数を1つ足すたびに同じだけ増える（V9 が使う RCI7・RCI52 を足すと +228 秒）。
      いまは窓をまとめて作り、順位を一度に出す。★同じ値段があるときの順位の付け方（平均順位）も
      元のまま（pandas の rank と同じ流儀・scipy の rankdata の既定）。
      番人＝`--selftest` で元の実装と突き合わせて最大差 0 であることを毎回 確かめる。
      scipy が無い環境では元の実装をそのまま使う（答えは同じ・遅いだけ）。
    """
    try:
        from scipy.stats import rankdata as _rankdata
    except Exception:                                            # noqa: BLE001
        return _rci_slow(c, n)
    x = pd.to_numeric(c, errors="coerce").to_numpy(dtype=float)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return pd.Series(out, index=c.index)
    win = np.lib.stride_tricks.sliding_window_view(x, n)         # 窓を作る（値のコピーはしない）
    t = np.arange(1, n + 1, dtype=float)
    const = float(n * (n * n - 1))
    res = np.empty(len(win))
    step = max(1, int(4_000_000 // n))                           # メモリを抑えて分けて計算する
    for s in range(0, len(win), step):
        blk = win[s:s + step]
        r = _rankdata(blk, axis=1)                               # 平均順位（同値の扱いが元と同じ）
        d2 = ((r - t) ** 2).sum(axis=1)
        v = 1.0 - 6.0 * d2 / const
        v[np.isnan(blk).any(axis=1)] = np.nan                    # 窓に欠けがあれば欠け（元と同じ）
        res[s:s + step] = v
    out[n - 1:] = res * 100.0
    return pd.Series(out, index=c.index)


def _supertrend(h, l, c, n=10, k=3.0):
    """本物の Supertrend（教科書の式）＝バンドの切り上げ切り下げ＋終値の抜けで反転。
    旧実装は反転の仕組みの無い下側バンド固定で、コメントは上側バンドと書かれていた
    ＝名前と中身の食い違い（2026-07-30 検査3 で発見・まこさん承認で是正）。
    上昇トレンド中は下側バンド（価格の下＝乖離%はプラス）・下降中は上側バンド（マイナス）。"""
    a = _atr(h, l, c, n).to_numpy()
    hl2 = ((h + l) / 2).to_numpy()
    cl = c.to_numpy(dtype=float)
    ub, lb = hl2 + k * a, hl2 - k * a
    line = np.full(len(cl), np.nan)
    fu = fl = np.nan
    up = True
    for i in range(len(cl)):
        if np.isnan(a[i]):
            continue
        if np.isnan(fu):                      # 最初の有効バー＝バンドの初期化だけ
            fu, fl = ub[i], lb[i]
            line[i] = fl if up else fu
            continue
        pu, pl = fu, fl                       # 1本前の確定バンド（過去のみ参照＝H2）
        fu = ub[i] if (ub[i] < pu or cl[i - 1] > pu) else pu
        fl = lb[i] if (lb[i] > pl or cl[i - 1] < pl) else pl
        if cl[i] > fu:
            up = True
        elif cl[i] < fl:
            up = False
        line[i] = fl if up else fu
    return pd.Series(line, index=c.index)


def _vp_levels(c, v, win=288, va_pct=0.7, rows=24):
    """出来高プロファイル。窓内で出来高が最も厚い区画＝POC。VAH/VAL＝POC から始めて、上と下の隣の区画のうち
    出来高の多い方を1つずつ足し、窓の出来高の70%に届いた所の上端・下端（監査 CP60）。
    出どころ＝CQG の逐語「The value area begins calculating at the POC. The system expands the value area one price
    at a time in either direction until the value area represents 70% ...」。同量なら POC に近い側・距離も同じなら上
    （TradingView の逐語「choose the row closer to the POC」）。区画は24（端が25個）。"""
    poc, vah, val = [], [], []
    ca, va = c.to_numpy(), v.to_numpy()
    for i in range(len(ca)):
        if i < win:
            poc.append(np.nan); vah.append(np.nan); val.append(np.nan); continue
        p_, h_, l_ = _vp_one(ca[i - win:i], va[i - win:i], va_pct, rows)
        poc.append(p_); vah.append(h_); val.append(l_)
    return (pd.Series(poc, index=c.index), pd.Series(vah, index=c.index), pd.Series(val, index=c.index))


def _vp_one(cw, vw, va_pct=0.7, rows=24):
    """1つの窓の出来高プロファイル＝(POC・VAH・VAL の価格)。決まりは _vp_levels の説明のとおり。
    ★2026-10-07（工事 m2c15-period-textbook-20261007）に _vp_levels の中から切り出した（計算は1文字も変えていない）。
      n 本の移動窓（_vp_levels）と、日で区切る版（_vp_by_day・監査 CP60 の修正42）が同じ決まりを使うため。"""
    bins = np.linspace(cw.min(), cw.max(), rows + 1)
    idx = np.clip(np.digitize(cw, bins) - 1, 0, len(bins) - 2)
    agg = np.bincount(idx, weights=vw, minlength=len(bins) - 1)
    centers = (bins[:-1] + bins[1:]) / 2
    p = int(np.argsort(agg)[::-1][0])
    last = len(agg) - 1
    tot = max(agg.sum(), 1e-9)
    lo, hi, acc = p, p, agg[p]
    while acc / tot < va_pct and (lo > 0 or hi < last):
        up = agg[hi + 1] if hi < last else -1.0
        dn = agg[lo - 1] if lo > 0 else -1.0
        if up > dn or (up == dn and (hi + 1 - p) <= (p - lo + 1)):
            hi += 1
            acc += agg[hi]
        else:
            lo -= 1
            acc += agg[lo]
    return centers[p], centers[hi], centers[lo]


def _vp_by_day(c, v, mode, va_pct=0.7, rows=24):
    """日で区切る出来高プロファイル（監査 CP60 の修正42 の比べる版・2026-10-07・工事 m2c15-period-textbook-20261007）。
    区切り＝UTC の日（データの時刻は UTC）。戻り＝(POC・VAH・VAL の価格の列)。決まり（区画・70%）は _vp_one。
    mode="前日"＝1つ前の日の足ぜんぶで作り、その日のあいだ動かない（監査 CP60 の修正42「前の UTC の日で固定（教科書の
      『前のセッションの値を後のセッションの参照にする』）」）。1つ前の日＝データに在る1つ前の日（_pivot_prev_period の
      shift(1) と同じ）。データの最初の日は NaN。
    mode="当日"＝その日の0時から、今の足の1本前までの足で作る（同「その日の0時から育つ版」）。今の足は窓に入れない
      （_vp_levels と同じ＝未来を見ない）。その日の最初の足は NaN。"""
    if mode not in ("前日", "当日"):
        raise ValueError(f"_vp_by_day の mode は 前日 か 当日（{mode}）")
    ca, va = c.to_numpy(float), v.to_numpy(float)
    dv = c.index.floor("D").to_numpy()
    out = np.full((3, len(ca)), np.nan)
    bounds, s = [], 0
    for i in range(1, len(ca) + 1):
        if i == len(ca) or dv[i] != dv[s]:
            bounds.append((s, i))
            s = i
    for k, (s, e) in enumerate(bounds):
        if mode == "前日":
            if k == 0:
                continue
            ps, pe = bounds[k - 1]
            out[:, s:e] = np.array(_vp_one(ca[ps:pe], va[ps:pe], va_pct, rows))[:, None]
        else:
            for i in range(s + 1, e):
                out[:, i] = _vp_one(ca[s:i], va[s:i], va_pct, rows)
    return tuple(pd.Series(out[j], index=c.index) for j in range(3))


def _sr_touch(c, h, l, win=288, tol=0.003):
    """いまの価格帯に、窓内で何回タッチしているか。

    ★2026-09-05（M2-C-4・まこさん承認 iter="m2c4-add-parts-20260905"）＝tol は
      「数」（値段に対する固定の割合）でも「並び」（バーごとに変わる割合）でもよくした。
      直す前は数だけで、相場の荒れ方が変わっても帯の幅が動かなかった。
      ★判定そのものは1文字も変えていない＝tol が数のときの結果は、直す前と同じ。
    """
    out = np.full(len(c), np.nan)
    ca, ha, la = c.to_numpy(), h.to_numpy(), l.to_numpy()
    ta = np.asarray(tol, dtype=float) if np.ndim(tol) else None   # 並びなら配列・数なら None
    for i in range(win, len(ca)):
        lvl = ca[i]
        t = tol if ta is None else ta[i]
        if t != t:                                   # NaN（ATR がまだ出ていない区間）は空のまま
            continue
        band = lvl * t
        out[i] = int(((ha[i - win:i] >= lvl - band) & (la[i - win:i] <= lvl + band)).sum())
    return pd.Series(out, index=c.index)


# ★2026-09-06（再監査 cp22 の N-1）＝S-RタッチATR（帯の許容幅が値動きの幅に連動する部品）を、
#   部品の一覧から外した。ここに理由を残すのは、次に作る人が同じ誤りを繰り返さないため。
#
#   【外した理由】実装が出どころの逐語と違っていた。
#     出どころ＝`e37_scalp.py`:213 の逐語 `V25_K = 0.5 # 束ね幅 tol=clamp(K×ATR%_1h,0.15%,0.6%)`
#       ＝許容幅は「1時間足の値動きの幅（ATR%_1h）× 倍率」で決める。
#     直す前の実装＝`_atr(d.high, d.low, d.close, atr_n) / d.close`
#       ＝渡された足の値動きの幅。5分足に展開されると 5分足の ATR% になる。
#   【何が起きたか】5分足の値動きの幅は1時間足より小さいので、0.5×それ は下端 0.15% を割る。
#     すると許容幅がいつも 0.15% に固定され、既存の部品 `S-Rタッチ数(288,0.0015)`（固定 0.15%）と
#     同じ列になった。実測（検査12・値決め窓 20000本×571列）＝相関 +0.9999978。
#     この工事は、材料カタログで唯一の「実質 同じもの」5組を作っていた（工事の前は0組）。
#   【正しい形】許容幅は1時間足の値動きの幅で決め、タッチはその足の高安で数える
#     （RG-v6 と同じ混ぜ方）。上位足の値を引く仕組みが要るので、M2-E で作る
#     （`next_step.md` §6 の136番）。
#   ★`_sr_touch` の「許容幅を並びでも受けられる」直しは残してある（実害なし・正しい形で使う）。
#   ★下の `_sr_touch_atr` も関数としては残す（どこからも呼ばれない）。理由＝正しい形を M2-E で
#     作るとき、直すのは「ATR をどの足で測るか」の1行だけで済むため。**部品の一覧には登録しない**
#     ＝`_reg` の登録と `build_catalog` の展開を外したので、材料カタログには1列も出ない。
_SR_ATR_TOL_LO, _SR_ATR_TOL_HI = 0.0015, 0.006


# ★2026-09-26（M2-E-4c・束2・設計書 m2e-bundle2-20260926）＝上の【正しい形】で作り直した。
#   まこさん決定（2026-09-26・逐語「CCの案の通りで進める」「BでOK」）＝新しい部品は全部の時間足で作る。
#   許容幅は1時間足の値動きの幅（ATR%）で決め、タッチはその足の高値・安値で数える（next_step §6 の136番）。
#   ★上の「★下の `_sr_touch_atr` も関数としては残す（どこからも呼ばれない）」と「部品の一覧には登録しない」は
#     2026-09-26 までの話。いまは新しい名前 S-Rタッチ1時間ATR で `_reg` と `build_catalog` に登録している
#     （外した名前 S-RタッチATR とは別の名前にした＝外した記録と混ざらないため）。
#   ★1時間足の作り方（2つ）
#     ①渡された足が1時間足以下（1m〜1h）＝その足のバーを1時間足にまとめ直す
#     ②渡された足が1時間足より長い（2h〜1d）＝その足のバーからは1時間足を作れない。
#       だから、列を作る道（build_features・insp5_frame）が下の置き場に入れた5分足から作る。
#       入っていない・期間を覆っていないときは止める（黙って別の値を使わない）。
#   ★未来を見ない＝1時間足の値は、その1時間足が閉じた時刻（始まり＋1時間）から使う。
#     バー s には、s が閉じた時刻（s＋その足の長さ）までに閉じた1時間足のうち、いちばん新しいものを当てる
#     （build_features が上位足を「足が閉じた時刻」から使うのと同じ考え）。
#   ★置き場を関数の外に置いた理由＝部品の関数は「その足のバー」だけを受け取る形で呼ばれ、引数を足せない。
#     pandas の attrs に5分足を持たせる形は、派生の計算のたびに中身が複製されて全部の部品が遅くなるので取らない。
_H1_BASE: dict = {"bars": None}


def _atr_pct_1h_on(d, atr_n):
    """d の各バーに、そのバーが閉じた時刻までに閉じた1時間足の ATR%（ATR ÷ その1時間足の終値）を当てた並びを返す。"""
    step = pd.Series(d.index).diff().median()
    if pd.isna(step):
        step = pd.Timedelta(0)
    if step <= pd.Timedelta("1h"):
        src = d
    else:
        src = _H1_BASE.get("bars")
        if (src is None or len(src) == 0 or src.index[0] >= d.index[0] + step
                or src.index[-1] < d.index[-1]):
            raise ValueError("1時間足より長い足には、1時間足の元になる5分足が要る"
                             "（_H1_BASE が空か、期間を覆っていない）")
    h1 = _resample(src[["open", "high", "low", "close", "volume"]], "1h")
    a = _atr(h1.high, h1.low, h1.close, atr_n) / h1.close
    a.index = h1.index + pd.Timedelta("1h")                # 1時間足が閉じた時刻
    return a.reindex(d.index + step, method="ffill").to_numpy(float)


def _sr_touch_atr(d, win, k, atr_n):
    """S-Rタッチ1時間ATR＝帯の許容幅を「1時間足の ATR% × 倍率」で決め、0.15%〜0.6% に収めた S-R タッチ数。

    ★2026-09-26（M2-E-4c・束2）に直した。直す前（2026-09-06 に部品の一覧から外した形）の `_atr(d…)` は「渡された足」の値動きの幅で、
      出どころの逐語 `tol=clamp(K×ATR%_1h,0.15%,0.6%)` の「1時間足」ではない。
      いまは `_atr_pct_1h_on` が1時間足の ATR% を引いてくる（正しい形）。タッチは、渡された足の高値・安値で数える（`_sr_touch` をそのまま使う）。
    """
    atr_pct = pd.Series(_atr_pct_1h_on(d, atr_n), index=d.index)
    tol = (k * atr_pct).clip(lower=_SR_ATR_TOL_LO, upper=_SR_ATR_TOL_HI)
    return _sr_touch(d.close, d.high, d.low, win, tol.to_numpy(float))


def _mmi(c, n):
    """Market Meanness Index（MMI）＝値動きがランダムに近いかの割合（0〜100）。高いほどレンジ寄り。

    ★2026-09-05（M2-C-4・まこさん決定「1・2・4・5・6 を足す」）に足した。
    ★計算は原典のとおり（The Financial Hacker「The Market Meanness Index」の本文の C のコードの逐語）。
      ★2026-09-06（再監査 cp22 の N-6）＝落ちていた2行（宣言の行と、並び順の注意書き）を足した:
        double m = Median(Data,Length);
        int i, nh=0, nl=0;
        for(i=1; i<Length; i++) {
          if(Data[i] > m && Data[i] > Data[i-1]) // mind Data order: Data[0] is newest!
            nl++;
          else if(Data[i] < m && Data[i] < Data[i-1])
            nh++;
        }
        return 100.*(nl+nh)/(Length-1);
    ★向きは測らない（regime_detection_kb.md §A-4 の逐語「向きは測りません」）。
    ★建てる合図には使わない＝原典の書いた人自身の逐語
      「Predicting the next price with the MMI would work as well as flipping a coin.」。
    ★未来を見ない＝窓は「いまのバーまでの n本」だけ（H2）。
    """
    a = c.to_numpy(float)
    med = c.rolling(n).median().to_numpy(float)      # いまのバーを含む n本の中央値
    # ★2026-09-05（監査 cp21 の C2）＝向きを原典に合わせて直した。
    #   原典（Zorro）の Data は **Data[0] が最新・Data[i] が i 本前**の並び。だから原典の
    #   `Data[i] > Data[i-1]` は「i 本前の値 > (i-1) 本前の値」＝**時系列では『その値が、次の値より大きい』**。
    #   直す前の私の実装は時系列順に読み替えて「前の値より大きい」で数えていた＝**原典と向きが逆**。
    #   監査の実測＝[0,1,0,1,0,1,5,6,7] で 原典 37.5 ／ 直す前 62.5（別物）。
    gt = np.zeros(len(a), dtype=bool)
    lt = np.zeros(len(a), dtype=bool)
    gt[:-1] = a[:-1] > a[1:]                         # 原典の Data[i] > Data[i-1]
    lt[:-1] = a[:-1] < a[1:]                         # 原典の Data[i] < Data[i-1]
    out = np.full(len(a), np.nan)
    for i in range(n - 1, len(a)):
        m = med[i]
        if m != m:
            continue
        # ★原典の i=1..Length-1 ＝ Data[0]（最新）を除く n-1 本＝時系列では「最新のバーを除く」
        s = slice(i - n + 1, i)
        w = a[s]
        cnt = int(((w > m) & gt[s]).sum() + ((w < m) & lt[s]).sum())
        out[i] = 100.0 * cnt / (n - 1)
    return pd.Series(out, index=c.index)


def _w_flag(c, h, l, n, tol):
    """W字（ダブルボトム）の完成フラグ（2026-07-30 案A＝教科書定義で実装・まこさん判断不能のため
    feedback_design_judgment_owner に基づき CC が確定）。窓 n の前半の最安値と後半の最安値が
    同水準（許容幅=tol×終値）で、終値が中央 n/2 区間の最高値（ネックラインの近似・流儀）を
    上抜けたら 1・それ以外 0。全部 過去方向の rolling/shift＝未来参照なし。"""
    half, q = n // 2, (n // 2) // 2
    lo1 = l.shift(half).rolling(n - half).min()
    lo2 = l.rolling(half).min()
    neck = h.shift(q).rolling(half).max()
    ok = ((lo1 - lo2).abs() <= tol * c) & (c > neck)
    return ok.astype(float).where(lo1.notna() & lo2.notna() & neck.notna())


def _fractal_levels(s, k: int, is_high: bool):
    """前後 k本 より高い（安い）中央のバーを山（谷）とし、**k本 遅らせて確定**させる。

    戻り＝(直近で確定した水準, その1つ前に確定した水準) の2本。どちらも値段そのもの＝
    使う側が終値で割って % にする（H6・値段の絶対値を列にしない）。

    ★未来を見ません（M2-2-6・法則 C10 の②）。使っているずらしは全部 過去向き（ずらす本数は正の数だけ）で、
      `.shift(-` も `center=True` も1つも使っていません。バー t で見ているのは high[t-2k] 〜 high[t] だけです。
      ★この2つの語を説明の文章に書けるようになったのは 2026-08-21 に41番の不具合を直したからです
        （直す前は、説明の文章に書いただけで書き込みが止まりました）。

    ★確定の仕組み。中央のバー j が山かどうかは、j より後ろの k本 が出そろうまで決まりません。
      だからバー t＝j+k になって初めて「バー j は山だった」と分かります。この関数は、その t で
      初めて水準を書き込みます。＝実例の「j+2 確定」（k=2）と同じ形です。

    ★1つ前の水準の作り方＝確定したバーで「その直前まで有効だった水準」を写し、あとは持ち回します。
      直近の水準と1つ前の水準の2本があると、「終値が直近2本の確定安値を割った」（法則 U9・構造破断）が
      条件の束として書けます。
    """
    lvl, hit = _fractal_marks(s, k, is_high)       # 確定したバーにだけ、その山（谷）の値段が入る
    last = lvl.ffill()                             # 直近で確定した水準
    prev = last.shift(1).where(hit).ffill()        # その1つ前に確定した水準
    return last, prev


def _fractal_marks(s, k: int, is_high: bool):
    """確定した山（谷）の値段を、確定したバー（中央のバー j の k本 後）にだけ置いた列と、その印（真偽）を返す。
    ★2026-10-09（工事 m2c15-shape-structure-20261009・K-3b）に _fractal_levels の中から切り出した（計算は1文字も変えていない）。
      窓の中で確定した山・谷を全部 使う教科書の版（W字確定谷・S-Rタッチ確定数・SMC_SWEEP確定）と、今の _fractal_levels が
      同じ確定の決まりを使うため。"""
    k = int(k)
    if k < 1:
        raise SystemExit(f"[材料カタログ] 山と谷の確定の本数は 1 以上（渡された＝{k}）")
    if is_high:
        left = s.rolling(k).max().shift(1)         # 中央のバー j の直前 k本（j の時点で分かる）
        right = s.rolling(k).max()                 # j+1 〜 j+k（バー j+k の時点で分かる）
        hit = (s.shift(k) > left.shift(k)) & (s.shift(k) > right)
    else:
        left = s.rolling(k).min().shift(1)
        right = s.rolling(k).min()
        hit = (s.shift(k) < left.shift(k)) & (s.shift(k) < right)
    return s.shift(k).where(hit), hit


def _w_fractal(c, h, l, n, tol, k=2):
    """W字確定谷＝ダブルボトムの教科書の版（監査 CP60 の修正43・2026-10-09・工事 m2c15-shape-structure-20261009）。
    ①2つの底＝窓 n 本（今の足まで）の中で確定した谷（_fractal_marks・前後 k 本）のうち、直近の2つ
    ②2つの底の値段の差が tol×終値 以内（今の W字 と同じ許容幅の決まり）
    ③ネック＝2つの谷の間の足の最高値
    ④完成＝2つ目の谷の後で、終値がネックを最初に上抜けた足だけ 1。それ以外は 0（今の W字 は条件が続く間ずっと1）。
    出どころ＝StockCharts の逐語「Breaking resistance from the highest point between the troughs completes the Double Bottom Reversal.」
    （監査 CP60 の表 27）。★未来を見ない＝谷はその k 本 後の足で確定してから使う。
    ★k は名前に出さない引数（最初の値 2＝資料の fractal の既定・まこさん「よい」2026-10-09 の1）。"""
    lv, hit = _fractal_marks(l, k, False)
    ca, ha = c.to_numpy(float), h.to_numpy(float)
    tv = np.flatnonzero(hit.to_numpy(bool))        # 谷が確定した足の番号
    pv = lv.to_numpy(float)[tv]                    # その谷の値段
    jv = tv - int(k)                               # 谷そのものの足の番号
    n = int(n)
    out = np.full(len(ca), np.nan)
    m = 0
    for i in range(n - 1, len(ca)):
        while m < len(tv) and tv[m] <= i:
            m += 1
        out[i] = 0.0
        if m < 2:
            continue
        j1, j2 = jv[m - 2], jv[m - 1]
        if j1 < i - n + 1 or j2 - j1 < 2 or abs(pv[m - 2] - pv[m - 1]) > tol * ca[i]:
            continue
        neck = ha[j1 + 1:j2].max()
        if ca[i] > neck and not (ca[j2 + 1:i] > neck).any():
            out[i] = 1.0
    return pd.Series(out, index=c.index)


def _sr_touch_fractal(d, n, tol, k=2):
    """S-Rタッチ確定数＝S-Rタッチの教科書の数え方（監査 CP60 の修正44・2026-10-09・工事 m2c15-shape-structure-20261009）。
    今の足の前の n 本（確定した足が [i−n, i)）の中で確定した山（高値）と谷（安値）のうち、今の終値 ± 許容幅（tol×終値）に入るものの数。
    今の S-Rタッチ数（_sr_touch）は、帯に掛かった足の本数（滞在時間）を数える＝監査 CP60 の表 48・49。
    ★今の足は窓に入れない（_sr_touch と同じ）。山・谷は前後 k 本で確定してから使う（未来を見ない）。
    ★tol は数でも並び（足ごとの割合）でもよい（_sr_touch と同じ）。k は名前に出さない引数（最初の値 2）。"""
    hv = _fractal_marks(d.high, k, True)[0].to_numpy(float)
    lv = _fractal_marks(d.low, k, False)[0].to_numpy(float)
    ca = d.close.to_numpy(float)
    ta = np.asarray(tol, dtype=float) if np.ndim(tol) else None   # 並びなら配列・数なら None
    n = int(n)
    out = np.full(len(ca), np.nan)
    for i in range(n, len(ca)):
        t = tol if ta is None else ta[i]
        if t != t:                                   # NaN（ATR がまだ出ていない区間）は空のまま
            continue
        band = ca[i] * t
        out[i] = float(np.sum(np.abs(hv[i - n:i] - ca[i]) <= band) + np.sum(np.abs(lv[i - n:i] - ca[i]) <= band))
    return pd.Series(out, index=d.index)


def _sr_touch_fractal_atr(d, n, m, a, k=2):
    """S-Rタッチ確定1時間ATR＝S-Rタッチ確定数 の許容幅を「1時間足の ATR% × 倍率」で決め、0.15%〜0.6% に収めた版（K-3b）。
    許容幅の作りは _sr_touch_atr と同じ（_atr_pct_1h_on・_SR_ATR_TOL_LO〜_SR_ATR_TOL_HI）。"""
    atr_pct = pd.Series(_atr_pct_1h_on(d, a), index=d.index)
    tol = (m * atr_pct).clip(lower=_SR_ATR_TOL_LO, upper=_SR_ATR_TOL_HI)
    return _sr_touch_fractal(d, n, tol.to_numpy(float), k)


# ★2026-10-20（工事 m2c15-band-s1-20261020・B-1）＝法則 R1（価格が何回も跳ね返された線が上下に在るか）と
#   R7（帯の幅が往復の手数料を超えるか・幅は「取れる距離」で測る＝まこさん「OK」worklog 20261003 §36）の部品＝帯の部品。
#   取れる距離（上の帯の下端 − 下の帯の上端）÷ 終値 が「手数料の床 × 倍数」以上で、今の終値がその間に在れば 1・それ以外 0。
#   線の種類は3つ（まこさん「すべて案どおりでよい」ok_d1_20261004 の③・worklog 20261003 §37・§38）。★2026-10-21＝②に前の週の版（帯pivot前週）を足した＝帯の部品は4種（監査 CP83 の修正12）
#     ①確定したスイングを許容幅で束ねた帯＝上の線と下の線のそれぞれに、確定したスイング（_fractal_marks＝前後 k 本で確定してから
#       使う＝H2）が m 回以上（法則 R1）。重なった帯は1つにまとめ、タッチの回数を足す（LuxAlgo の逐語
#       "Overlapping zones merge into one consolidated zone and their test counts are added together"）
#     ②前の日で固定の pivot R1（上の線）・S1（下の線）＝_pivot_prev_period
#     ③前の UTC の日で固定の VAH（上の線）・VAL（下の線）＝_vp_by_day の「前日」
#     ★②③は触れた回数を数えない（まこさん「Aでいい」ok_pivot_a_20261020）＝前もって推定する支持線・抵抗線（StockCharts の逐語
#       「Pivot Points use the prior period's high, low, and close to estimate future support and resistance levels.」）
#   帯の幅は、どの種類も許容幅 t（線の ± 値段×t/2）。許容幅は固定の版と、1時間足の ATR% × 倍率を 0.15%〜0.6% に収める版の2つ
#   （まこさん「１は案ア」＝両方・ok_three_points_20261020 の2＝3種類の全部に両方）。
#   ★RG-v5 の帯の数字（タッチ2回・幅0.4%）は使わない（違反の記録 #23）。
#   ★手数料の床＝e37_scalp.SCALP_FLOOR（0.08%）を読む（数字を2か所に書かない）。倍数は設定の band_fee_mult
#     （名前に出さない値・まこさん「OK」ok_three_points_20261020 の1＝最初の値 2・範囲は §2.2 の段1 の 2〜6倍）。
#   ★2026-10-21（監査 CP83 の修正14・まこさん「案B」）＝床は、build_catalog に渡した設定の band_fee_mult から作り、部品の関数へ
#     引数で渡す（既定の設定ファイルを1回だけ読んで覚える作りにしない）。make_material を直に呼ぶ入口（設定を持たない）は、
#     設定ファイルをその都度 読む。★床は登録の計算式の引数にしない（名前に出さない引数の番人＝_insp_hidden_params は、
#     既定つきの引数を全部ずらして列が変わるかを見る。床は帯の幅より小さい値では列を変えないので、番人が止める）＝
#     カタログを作る所（_band_material）で結び付ける。


def _band_fee_floor(cfg: dict | None = None) -> float:
    """取れる距離の床＝手数料の床（e37_scalp.SCALP_FLOOR）× 設定の倍数 band_fee_mult。cfg を渡さなければ設定ファイルを読む（覚えない）。"""
    import e37_scalp as _e37b                       # lazy（build_range_geometry と同じ読み込み方）
    return float(_e37b.SCALP_FLOOR) * float((load_config() if cfg is None else cfg)["band_fee_mult"])


def _band_cluster(px, price, t, m, above):
    """price より上（above＝True）か下の、確定したスイングの値段 px を、隣との差が「値段 × t」以下なら同じ帯に束ね、
    price に近い帯（帯の平均と price の差が小さい順・同じなら値段の低い側）から見て、スイングが m 回以上の最初の帯の
    （下端, 上端）を返す。帯の端＝束ねたスイングの最小 ×(1−t/2)・最大 ×(1+t/2)。無ければ None。"""
    s = np.sort(px[px > price] if above else px[px < price])
    if len(s) < m:
        return None
    best = None
    for cl in np.split(s, np.flatnonzero(np.diff(s) > s[:-1] * t) + 1):
        if len(cl) >= m:
            dist = abs(float(cl.mean()) - price)
            if best is None or dist < best[0]:
                best = (dist, float(cl.min()) * (1 - t / 2), float(cl.max()) * (1 + t / 2))
    return None if best is None else (best[1], best[2])


def _band_swing(d, n, tol, m, k=2, floor=None):
    """帯スイング＝確定したスイングを束ねた上の帯と下の帯（①）。今の足の前の n 本（確定した足が [i−n, i)）で数える。
    ★今の足は窓に入れない（_sr_touch_fractal と同じ）。tol は数でも並び（足ごとの割合）でもよい。k は名前に出さない引数（最初の値 2）。
    floor＝取れる距離の床（None なら設定ファイルから作る）。"""
    hv = _fractal_marks(d.high, k, True)[0].to_numpy(float)     # 帯の上の線＝確定した山（前後 k 本で確定してから使う）
    lv = _fractal_marks(d.low, k, False)[0].to_numpy(float)     # 帯の下の線＝確定した谷
    ca = d.close.to_numpy(float)
    ta = np.asarray(tol, dtype=float) if np.ndim(tol) else None
    n, m = int(n), int(m)
    floor = _band_fee_floor() if floor is None else float(floor)
    out = np.full(len(ca), np.nan)
    for i in range(n, len(ca)):
        t = tol if ta is None else ta[i]
        if t != t:                                   # NaN（ATR がまだ出ていない区間）は空のまま
            continue
        hw, lw = hv[i - n:i], lv[i - n:i]
        up = _band_cluster(hw[hw == hw], ca[i], t, m, True)
        dn = _band_cluster(lw[lw == lw], ca[i], t, m, False)
        ok = (up is not None and dn is not None and dn[1] < ca[i] < up[0]
              and (up[0] - dn[1]) / ca[i] >= floor)
        out[i] = 1.0 if ok else 0.0
    return pd.Series(out, index=d.index)


def _band_lines(d, upper, lower, tol, floor=None):
    """線が前もって決まっている帯（②前の日の pivot R1・S1／③前の UTC の日の VAH・VAL）。
    ★2026-10-20（まこさん「Aでいい」ok_pivot_a_20261020）＝線に過去のスイングが触れた回数は求めない。pivot の役割は、前の期間から
      前もって推定する支持線・抵抗線（StockCharts の逐語「Pivot Points use the prior period's high, low, and close to estimate future
      support and resistance levels.」）＝その日に初めて引かれる線なので、過去の山・谷が触れていることは役割に入らない。
    帯＝線の ± 値段×t/2。上の帯の下端（上の線 ×(1−t/2)）と下の帯の上端（下の線 ×(1+t/2)）の間に終値が在り、取れる距離（その2つの差）÷ 終値
    が床（法則 R7）以上なら 1・それ以外 0。線が無い足（前の日が無い）は空。floor＝取れる距離の床（None なら設定ファイルから作る）。"""
    U, L = np.asarray(upper, dtype=float), np.asarray(lower, dtype=float)
    ca = d.close.to_numpy(float)
    ta = np.asarray(tol, dtype=float) if np.ndim(tol) else np.full(len(ca), float(tol))
    floor = _band_fee_floor() if floor is None else float(floor)
    top, bot = U * (1 - ta / 2), L * (1 + ta / 2)
    with np.errstate(invalid="ignore"):
        ok = (bot < ca) & (ca < top) & ((top - bot) / ca >= floor)
    return pd.Series(np.where(np.isfinite(top) & np.isfinite(bot), ok.astype(float), np.nan), index=d.index)


def _band_tol_1h(d, km, a):
    """帯の許容幅を「1時間足の ATR% × 倍率」で決め、0.15%〜0.6% に収めた並び（_sr_touch_atr と同じ作り）。"""
    atr_pct = pd.Series(_atr_pct_1h_on(d, a), index=d.index)
    return (km * atr_pct).clip(lower=_SR_ATR_TOL_LO, upper=_SR_ATR_TOL_HI).to_numpy(float)


# ★2026-10-21（監査 CP83 の修正14・まこさん「案B」）＝カタログの帯の部品は、渡した設定から作った床を結び付けて作る。
#   計算式は登録の計算式と同じ関数（_band_swing・_band_lines）＝床だけを引数で渡す（登録の計算式は床を設定ファイルから読む）。
#   ★前の週の版（帯pivot前週）＝監査 CP83 の修正12・まこさん「ウ」＝先例 K-7 の前週pivot（_pivot_prev_period(d, "W")）と同じ線。
_BAND_IMPL = {
    "帯スイング": lambda d, fl, n, t, m: _band_swing(d, n, t, m, 2, fl),
    "帯スイング1時間ATR": lambda d, fl, n, km, a, m: _band_swing(d, n, _band_tol_1h(d, km, a), m, 2, fl),
    "帯pivot": lambda d, fl, t: _band_lines(d, *_pivot_prev_period(d)[1:], t, fl),
    "帯pivot1時間ATR": lambda d, fl, km, a: _band_lines(d, *_pivot_prev_period(d)[1:], _band_tol_1h(d, km, a), fl),
    "帯pivot前週": lambda d, fl, t: _band_lines(d, *_pivot_prev_period(d, "W")[1:], t, fl),
    "帯pivot前週1時間ATR": lambda d, fl, km, a: _band_lines(d, *_pivot_prev_period(d, "W")[1:], _band_tol_1h(d, km, a), fl),
    "帯VA": lambda d, fl, t: _band_lines(d, *_vp_by_day(d.close, d.volume, "前日")[1:], t, fl),
    "帯VA1時間ATR": lambda d, fl, km, a: _band_lines(d, *_vp_by_day(d.close, d.volume, "前日")[1:], _band_tol_1h(d, km, a), fl),
}


def _band_material(family: str, floor: float, *params) -> tuple:
    """帯の部品を1組 作る（名前と向きは make_material と同じ・計算式は床を結び付けた _BAND_IMPL）。"""
    name, _fn, directional = make_material(family, *params)
    impl = _BAND_IMPL[family]
    return (name, (lambda d, _i=impl, _fl=float(floor), _p=params: _i(d, _fl, *_p)), directional)


# ★2026-10-20（工事 m2c15-band-s1-20261020・S-1・まこさん「OK」ok_direction_20261020 の3・ok_three_points_20261020 の3）
#   ＝スパイクの法則 S1 の部品の式の置き場を、E36（e36_short_oscillation.py）から材料の表（ここ）へ移した。式は1文字も変えていない。
#   E36 は `from observe_diag import spike_threshold, spike_stat` で同じ関数を呼ぶ（値は1ビットも変わらない＝写しで突き合わせる）。
#   ★2026-10-21（監査 CP83 の修正1・まこさん「案A」）＝E36 の式（spike_stat）は、ふだんの揺れに今の1本を入れる。Lee-Mykland（2008）の
#     式(8)は入れない＝論文の版（lee_mykland_stat）を下に足し、材料は2つ（LeeMykland＝論文の版／LeeMykland_E36版＝E36 の式）。
import math  # noqa: E402


# ── 急騰検知 Lee-Mykland jump（全 bars≤i の値のみ＝leak-safe・a-priori 閾値・スイープしない）──
def spike_threshold(K: int, alpha: float) -> float:
    """Gaussian EVT 閾値 L* = C_n + β*·a_n（K・α から a-priori・データで決めない・L-267）。"""
    lnK = math.log(K)
    s = math.sqrt(2.0 * lnK)
    Cn = s - (math.log(math.pi) + math.log(lnK)) / (2.0 * s)
    an = 1.0 / s
    beta = -math.log(-math.log(1.0 - alpha))
    return Cn + beta * an


def spike_stat(c: np.ndarray, K: int) -> np.ndarray:
    """各バーの jump 統計 L_i = r_i/√V̂_i（V̂=局所 bipower・直近 K 本・全て過去〜現在＝H2 leak-safe）。
    r_i=log(c_i/c_{i−1})・|r_j||r_{j−1}| を窓 K−1 で和（warmup は NaN→発火しない）。"""
    n = len(c)
    r = np.full(n, np.nan)
    r[1:] = np.log(c[1:] / c[:-1])              # log リターン（過去 close のみ）
    absr = np.abs(r)
    bpv = np.full(n, np.nan)
    bpv[1:] = absr[1:] * absr[:-1]              # bpv[i] = |r_i||r_{i−1}|（jump 頑健の bipower 項）
    bp_sum = pd.Series(bpv).rolling(K - 1).sum().to_numpy()   # Σ_{j=i−K+2}^{i}（K−1 項・当該バーまで）
    V = (math.pi / (2.0 * (K - 1))) * bp_sum
    with np.errstate(invalid="ignore", divide="ignore"):
        return r / np.sqrt(V)


def lee_mykland_stat(c: np.ndarray, K: int) -> np.ndarray:
    """Lee-Mykland（2008, Review of Financial Studies v21 n6）の jump の検定統計 L(i)＝r_i ÷ √V_i（論文の式(7)・式(8)）。
    r_i＝log(c_i / c_{i−1})・V_i＝π/(2(K−2)) × Σ_{j=i−K+2}^{i−1} |r_j||r_{j−1}|（直前の K−1 本の値動き＝今の1本の項を入れない）。
    論文の逐語「With realized returns in the window consisting of the previous K − 1 observations just before a testing time ti,
    the instantaneous volatility is estimated」（2540ページ・監査 CP83 の外部検索2）。係数 π/2 は、論文の閾値の定数 c＝√(2/π) を
    分母の側に移した物（E36 の spike_stat と同じ置き方＝spike_threshold の閾値をそのまま当てられる）。K 本そろう前は空。
    ★E36 の spike_stat との違いは、和の窓の終わり（今の1本を入れない）と項の数（K−2 項）だけ。"""
    n = len(c)
    r = np.full(n, np.nan)
    r[1:] = np.log(c[1:] / c[:-1])              # log リターン（過去 close のみ）
    absr = np.abs(r)
    bpv = np.full(n, np.nan)
    bpv[1:] = absr[1:] * absr[:-1]              # bpv[j] = |r_j||r_{j−1}|
    bp_prev = pd.Series(bpv).rolling(K - 2).sum().shift(1).to_numpy()   # Σ_{j=i−K+2}^{i−1}（K−2 項・今の1本の項を入れない）
    V_lm = (math.pi / (2.0 * (K - 2))) * bp_prev
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(V_lm > 0, r / np.sqrt(V_lm), np.nan)   # ★監査 CP84 の修正6＝ふだんの揺れが 0 の足は ±inf にせず空


def _smc_sweep_fractal(d, k=2):
    """SMC_SWEEP確定＝流動性の刈り取りの教科書の版（監査 CP60 の修正46・2026-10-09・工事 m2c15-shape-structure-20261009）。
    1本前までに確定した直近の谷（前後 k 本）を安値で割り、終値でその上に戻した足＝+1。
    1本前までに確定した直近の山を高値で抜き、終値でその下に戻した足＝−1。どちらでもない足＝0。
    出どころ＝LuxAlgo の逐語「The classic anatomy is a wick through a prior swing high or low…followed by a close back inside
    the old range.」（監査 CP60 の表 61）。ライブラリの版（直前15本の高安・陽線陰線・ヒゲが実体の1.5倍）の条件は使わない
    （まこさん「よい」2026-10-09 の2）。★値の向き（+1＝下側の刈り取り）はライブラリの版と同じ。山・谷が1つも確定していない足は欠損。"""
    hi = _fractal_levels(d.high, k, True)[0].shift(1)
    lo = _fractal_levels(d.low, k, False)[0].shift(1)
    bull = ((d.low < lo) & (d.close > lo)).astype(float)
    bear = ((d.high > hi) & (d.close < hi)).astype(float)
    return (bull - bear).where(hi.notna() | lo.notna())


# ══ cycles（サイクル系）の重い計算を使い回す入れもの ══════════════════════
# ★なぜ要るか＝ヒルベルト変換の関数は1本 250,000 本で 12.8 秒かかる（2026-08-11 実測）。
#   ht_phasor と ht_sine は1回の計算で2つの列を返すので、列ごとに呼ぶと同じ計算を2回する。
# ★未来を見る心配は無い＝入れものの鍵は「渡された終値そのものの指紋」なので、
#   データを1本でも切ると鍵が変わって計算し直す（検査4 の切り詰め再計算がこれを確かめる）。
# ★持つのは直近の1組だけ＝入力が変われば捨てる（記憶が膨らまない）。
_CYC_MEMO: dict = {"sig": None, "v": {}}


def _cyc(d: pd.DataFrame, name: str, fn):
    # ★2026-09-08（設計書 insp5-frame-and-table-tidy-20260908 の B・§6 の134番の②）
    #   ＝鍵に「並んでいる時刻の指紋」を足した。
    #   直す前＝鍵は「本数」と「終値」の2つだけ。終値が同じで時刻だけ違う枠を続けて渡すと、
    #   前の結果がそのまま返る。返ってきた列は前の枠の時刻を持つので、次の枠の終値で割ると
    #   pandas が2つの時刻をつなげて本数が膨らむ（実測 2026-09-08＝317,376 → 528,960）。
    #   直した後＝時刻が1本でも違えば鍵が変わって計算し直す。
    #   ★番人＝T-h（終値が同じで時刻だけ違う2つを渡すと、別の値が返る）。
    sig = (len(d), hashlib.md5(d.close.to_numpy(dtype=float).tobytes()).hexdigest(),
           hashlib.md5(np.ascontiguousarray(d.index.values).tobytes()).hexdigest())
    if _CYC_MEMO["sig"] != sig:
        _CYC_MEMO["sig"], _CYC_MEMO["v"] = sig, {}
    if name not in _CYC_MEMO["v"]:
        _CYC_MEMO["v"][name] = fn(d)
    return _CYC_MEMO["v"][name]


# ══ 材料の表（指標の種類 → 名前の組み立て・計算式・方向あり?）════════════════════
# ★2026-08-13（段A の A-2）に新設。build_catalog の for の中に埋まっていた計算式を、ここへ出した。
#   ★計算式は1文字も変えていない。変えたのは数字の渡し方だけ＝
#     いま（数字を式の中に固定する）  lambda d, n=n: _rsi(d.close, n)
#     直したあと（数字を引数で受ける） lambda d, n:   _rsi(d.close, n)
#   ★なぜ要るか＝前の形では、設定ファイルに並んだ数字（RSI なら 7・9・14・21）以外の列名が
#     どこにも作られず、engine_tuner が RSI12 を何回 走っても引けなかった
#     （要件「作ってはいけないもの」2番＝探す値を先に「決まった数字だけ」で限定するもの）。
#   ★名前の組み立て＝`{}` の個数がパラメータの個数。組み立てた名前は、前と1文字も違わない
#     （番人＝535本の名前・方向・値の指紋を、直す前と突き合わせる）。
MATERIAL_FAMILIES: dict[str, tuple] = {}

# ★業界のライブラリ（pandas-ta-classic）は重いので、実際に材料を作る時に読み込む。
#   ★計算式の中の書き方（`_pta6.rsi(...)`）は、直す前と1文字も変えない。
#   変えたのは「いつ読み込むか」だけ＝前は build_catalog の中で読み込んでいた。
_pta6 = None


def _load_pta():
    """業界のライブラリを1回だけ読み込む（式が使う名前は `_pta6` のまま）。"""
    global _pta6
    if _pta6 is None:
        import pandas_ta_classic as _m
        _pta6 = _m
    return _pta6


# ★td_seq は行の見出しを整数に作り直して返す（ほかの列は日付）。そのまま入れると
#   日付の表と突き合わせできず全部 欠損になる。日付を付け直す（2026-08-09 実測で発見）。
def _tdseq(d, i):
    r = _pta6.td_seq(close=d.close).iloc[:, i]
    r.index = d.index
    return r


def _mama(d, **kw):
    return _pta6.mama(close=d.close, **kw)


# ★1回の計算で複数の列を返すもの＝呼び出しを1か所にまとめる（式は直す前と同じ）
# ★CKSP（2026-10-04・まこさん「２はC」）＝TradingView の形（10・1・9・rma）にそろえる。直す前は引数なしで呼び、
#   値は本の形（10・3・20）・ならし方は TradingView の形（rma）という混ざった組だった（ライブラリ cksp.py:22〜35）。
def _ck(d, **kw):
    return _pta6.cksp(high=d.high, low=d.low, close=d.close, tvmode=True, **kw)


def _ps(d, **kw):
    return _pta6.psar(high=d.high, low=d.low, close=d.close, **kw)


def _kv(d):
    return _pta6.kvo(high=d.high, low=d.low, close=d.close, volume=d.volume)


def _ab(d, **kw):
    return _pta6.aberration(high=d.high, low=d.low, close=d.close, **kw)


def _acb(d, **kw):
    return _pta6.accbands(high=d.high, low=d.low, close=d.close, **kw)


def _cel(d, **kw):
    return _pta6.ce(high=d.high, low=d.low, close=d.close, **kw)


def _hw(d, **kw):
    return _pta6.hwc(close=d.close, channel_eval=True, **kw)


def _th(d):
    return _pta6.thermo(high=d.high, low=d.low)


def _ha(d):
    return _cyc(d, "ha", lambda x: _pta6.ha(open_=x.open, high=x.high, low=x.low, close=x.close))


# ★VFI＝教科書の式（Markos Katsanos）。ライブラリの実装は使わない（足切りが終値の20%で、
#   5分足では一度も超えず全部ゼロになる＝2026-08-10 実測 157,851本すべて 0）。
def _vfi(d, n):
    typ = (d.high + d.low + d.close) / 3.0
    inter = np.log(typ) - np.log(typ.shift(1))
    cutoff = 0.2 * inter.rolling(30).std() * d.close        # 教科書＝標準偏差30本・係数 0.2
    vave = d.volume.rolling(n).mean().shift(1)              # 前の足まで（未来を見ない）
    vc = d.volume.clip(upper=vave * 2.5)                    # 教科書＝出来高の上を 2.5 倍で切る
    mf = typ - typ.shift(1)
    vcp = vc * np.sign(mf.where(mf.abs() > cutoff, 0.0))
    return (vcp.rolling(n).sum() / vave.replace(0, np.nan)).ewm(span=3, adjust=False).mean()


def _ebsw(d, length=40, bars=10):
    """Even Better SineWave（J.F.Ehlers, Cycle Analytics for Traders 2014）。
    ①ハイパスで length 本より長い波を落とす ②スーパースムーザー（2極）で bars 本より短い波を落とす
    ③3本の平均を3本の実効値で割って −1〜1 にする。角度は度（教科書どおり）。"""
    c = d.close.to_numpy(dtype=float)
    m = len(c)
    out = np.full(m, np.nan)
    if m <= length:
        return pd.Series(out, index=d.index)
    out[length - 1] = 0.0
    a_hp = (1.0 - np.sin(np.radians(360.0 / length))) / np.cos(np.radians(360.0 / length))
    a1 = np.exp(-np.sqrt(2.0) * np.pi / bars)
    c2 = 2.0 * a1 * np.cos(np.radians(np.sqrt(2.0) * 180.0 / bars))
    c3 = -a1 * a1
    c1 = 1.0 - c2 - c3
    last_c = last_hp = 0.0
    hist = [0.0, 0.0]
    for i in range(length, m):
        hp = 0.5 * (1.0 + a_hp) * (c[i] - last_c) + a_hp * last_hp
        filt = c1 * (hp + last_hp) / 2.0 + c2 * hist[1] + c3 * hist[0]
        wave = (filt + hist[1] + hist[0]) / 3.0
        pwr = (filt * filt + hist[1] * hist[1] + hist[0] * hist[0]) / 3.0
        out[i] = wave / np.sqrt(pwr) if pwr > 0 else 0.0
        hist.append(filt)
        hist.pop(0)
        last_hp, last_c = hp, c[i]
    return pd.Series(out, index=d.index)


# ★2026-08-16（段A の A-6）＝ここに在った直書きの2つ（_DOJI_N=10・_CDLZ_N=30）を消した。
#   いまは設定ファイル observe_config.json の `body_ratio_periods`・`cdl_z_periods` から読む。
#   数字そのものは 10・30 のままで変えていない（CC は数字を作らない）。


def _reg(family: str, name_tpl: str, directional: bool, fn):
    """指標の種類を1つ登録する（表に1行 足す）。"""
    if family in MATERIAL_FAMILIES:
        raise SystemExit(f"[材料カタログ] 指標の種類が二重に登録された: {family}")
    MATERIAL_FAMILIES[family] = (name_tpl, bool(directional), fn)


_MAT_RE: dict = {}


def find_material(name: str):
    """列の名前（例＝`RSI12` `BB%b(20,2.0)`）→ (指標の種類, パラメータ)。無ければ (None, None)。

    ★参照表（indicator_reference_diag）の family 名と、この表の鍵が違うものが在る
      （例＝参照表は `VAH`／この表は `close vs VAH%`）。だから名前の組み立ての型で照合する。
    ★番人＝535本の名前を全部 分解して組み立て直し、1文字も違わないことを確かめる。
    """
    if not _MAT_RE:
        for fam, (tpl, _d, _f) in MATERIAL_FAMILIES.items():
            parts = tpl.split("{}")
            _MAT_RE[fam] = re.compile("^" + r"(-?\d+(?:\.\d+)?)".join(re.escape(p) for p in parts) + "$")
    hits = []
    for fam, rx in _MAT_RE.items():
        m = rx.match(name)
        if m:
            hits.append((fam, tuple(float(g) if "." in g else int(g) for g in m.groups())))
    if not hits:
        return None, None
    if len(hits) > 1:                      # 型が重なっている＝表の作りが悪い（黙って選ばない）
        raise SystemExit(f"[材料カタログ] 名前 {name} に当たる指標の種類が複数ある: {[h[0] for h in hits]}")
    return hits[0]


def make_material(family: str, *params) -> tuple:
    """指標の種類とパラメータ → (列名, 計算式, 方向あり?)。

    ★設定ファイルに並んでいない数字でも作れる（A-3・A-4 が使う入口）。
    """
    if family not in MATERIAL_FAMILIES:
        raise SystemExit(f"[材料カタログ] 知らない指標の種類: {family}"
                         f"（登録済み＝{len(MATERIAL_FAMILIES)} 種類）")
    _load_pta()
    tpl, directional, fn = MATERIAL_FAMILIES[family]
    need = tpl.count("{}")
    if need != len(params):
        raise SystemExit(f"[材料カタログ] {family} のパラメータの個数が合わない"
                         f"（要る＝{need} 個 ／ 渡された＝{list(params)}）")
    return (tpl.format(*params), (lambda d, _f=fn, _p=params: _f(d, *_p)), directional)


# ── トレンド/モメンタム ──
_reg("ADX", "ADX{}", False, lambda d, n: _adx_di(d.high, d.low, d.close, n)[0])
_reg("DI差", "DI差{}", True, lambda d, n: (lambda a: a[1] - a[2])(_adx_di(d.high, d.low, d.close, n)))
_reg("MACD線%", "MACD線%({},{})", True, lambda d, f_, s_:
     (d.close.ewm(span=f_).mean() - d.close.ewm(span=s_).mean()) / d.close * 100)
_reg("MACDシグナル線%", "MACDシグナル線%({},{},{})", True, lambda d, f_, s_, g_:
     (d.close.ewm(span=f_).mean() - d.close.ewm(span=s_).mean())
     .ewm(span=g_).mean() / d.close * 100)
_reg("MACDヒスト%", "MACDヒスト%({},{},{})", True, lambda d, f_, s_, g_:
     (lambda m: (m - m.ewm(span=g_).mean()) / d.close * 100)(
         d.close.ewm(span=f_).mean() - d.close.ewm(span=s_).mean()))
_reg("RSI", "RSI{}", True, lambda d, n: _rsi(d.close, n))
_reg("ROC", "ROC{}", True, lambda d, n: d.close.pct_change(n) * 100)
_reg("Stoch%K", "Stoch%K{}", True, lambda d, n, smooth_k=1: (lambda k: k if smooth_k == 1 else k.rolling(smooth_k).mean())(100 * (d.close - d.low.rolling(n).min())
     / (d.high.rolling(n).max() - d.low.rolling(n).min()).replace(0, np.nan)))
_reg("Stoch%D", "Stoch%D{}", True, lambda d, n, smooth_k=1, d_n=3: (lambda k: (k if smooth_k == 1 else k.rolling(smooth_k).mean()).rolling(d_n).mean())(100 * (d.close - d.low.rolling(n).min())
     / (d.high.rolling(n).max() - d.low.rolling(n).min()).replace(0, np.nan)))
# 全部上昇の窓は 100（世界標準の慣例）。旧式は分母0を NaN に置換して欠損にしていた＝是正（2026-07-30）
_reg("MFI", "MFI{}", True, lambda d, n: (lambda tp: 100 - 100 / (1 + (
     (tp * d.volume).where(tp > tp.shift(), 0).rolling(n).sum()
     / (tp * d.volume).where(tp < tp.shift(), 0).rolling(n).sum()
     )))((d.high + d.low + d.close) / 3))
_reg("CMF", "CMF{}", True, lambda d, n: (((d.close - d.low) - (d.high - d.close))
                                         / (d.high - d.low).replace(0, np.nan) * d.volume).rolling(n).sum()
     / d.volume.rolling(n).sum().replace(0, np.nan))
_reg("OBV傾き", "OBV傾き{}", True, lambda d, n: (np.sign(d.close.diff()) * d.volume).fillna(0).cumsum().diff(n)
     / d.volume.rolling(n).sum().replace(0, np.nan))
_reg("close vs 転換線%", "close vs 転換線%({})", True, lambda d, t_:
     (d.close / ((d.high.rolling(t_).max() + d.low.rolling(t_).min()) / 2) - 1) * 100)
_reg("close vs 基準線%", "close vs 基準線%({})", True, lambda d, k_:
     (d.close / ((d.high.rolling(k_).max() + d.low.rolling(k_).min()) / 2) - 1) * 100)
_reg("RCI", "RCI{}", True, lambda d, n: _rci(d.close, n))
_reg("EMA傾き", "EMA{}傾き%", True, lambda d, n, slope_n=5: d.close.ewm(span=n, adjust=False).mean().pct_change(slope_n) * 100)
# ── ボラ ──
_reg("ATR%", "ATR%{}", False, lambda d, n: _atr(d.high, d.low, d.close, n) / d.close * 100)
# 標準偏差は母集団（ddof=0）＝TradingView・ta と同じ世界標準（2026-07-30 に標本 ddof=1 から統一）
_reg("BB%b", "BB%b({},{})", True, lambda d, n, s: (d.close - (d.close.rolling(n).mean()
     - s * d.close.rolling(n).std(ddof=0))) / (2 * s * d.close.rolling(n).std(ddof=0)).replace(0, np.nan))
_reg("BB幅", "BB幅({},{})", False, lambda d, n, s:
     2 * s * d.close.rolling(n).std(ddof=0) / d.close.rolling(n).mean())
_reg("realized_vol", "realized_vol{}", False, lambda d, n:
     np.log(d.close / d.close.shift()).rolling(n).std() * 100)
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正50 の直した後の文字）＝平均を引かない実現ボラ √(Σr²/n)。
#   今の版（平均を引いた標本の標準偏差）は残す。どちらが良いかは M2-F-10f で比べる。
_reg("realized_vol_rv", "realized_vol_rv{}", False, lambda d, n:
     np.sqrt((np.log(d.close / d.close.shift()) ** 2).rolling(n).sum() / n) * 100)
_reg("Donchian幅%", "Donchian幅%{}", False, lambda d, n:
     (d.high.rolling(n).max() - d.low.rolling(n).min()) / d.close * 100)
_reg("zscore", "zscore{}", True, lambda d, n:
     (d.close - d.close.rolling(n).mean()) / d.close.rolling(n).std().replace(0, np.nan))
# 対数リターン基準の zスコア（軸カタログ E-c の zscore_return・2026-07-30 検査7 を受けて追加）
_reg("zscore_return", "zscore_return{}", True, lambda d, n:
     (lambda r: (r - r.rolling(n).mean()) / r.rolling(n).std().replace(0, np.nan))
     (np.log(d.close / d.close.shift())))
# ── 出来高 ──
_reg("volume_ratio", "volume_ratio{}", False, lambda d, n:
     d.volume / d.volume.rolling(n).mean().replace(0, np.nan))
# ── ローソク ──
# 教科書の包み足＝前バーと逆の色で実体を包む（2026-07-30 に前バーの色を問わない簡略形から是正）
_reg("包み足", "包み足", True, lambda d: (((d.close.shift() < d.open.shift()) & (d.open < d.close.shift())
                                       & (d.close > d.open.shift())).astype(float)
                                      - ((d.close.shift() > d.open.shift()) & (d.open > d.close.shift())
                                         & (d.close < d.open.shift())).astype(float)))
# 教科書の孕み足＝前バーと逆の色で実体が前バーの実体の中に収まる（2026-07-30 検査7 の軸カタログ照合で追加）
_reg("孕み足", "孕み足", True, lambda d: (((d.close.shift() < d.open.shift()) & (d.close > d.open)
                                       & (d.open > d.close.shift()) & (d.close < d.open.shift())).astype(float)
                                      - ((d.close.shift() > d.open.shift()) & (d.close < d.open)
                                         & (d.open < d.close.shift()) & (d.close > d.open.shift())).astype(float)))
_reg("pinbar", "pinbar", True, lambda d: ((d[["open", "close"]].min(axis=1) - d.low)
                                          - (d.high - d[["open", "close"]].max(axis=1)))
     / (d.high - d.low).replace(0, np.nan))
_reg("連続本数", "連続本数", True, lambda d: (np.sign(d.close - d.open)
     .groupby((np.sign(d.close - d.open) != np.sign(d.close - d.open).shift()).cumsum())
     .cumcount() + 1) * np.sign(d.close - d.open))
_reg("body比", "body比", False, lambda d: (d.close - d.open).abs() / (d.high - d.low).replace(0, np.nan))
_reg("上ヒゲ比", "上ヒゲ比", False, lambda d:
     (d.high - d[["open", "close"]].max(axis=1)) / (d.high - d.low).replace(0, np.nan))
_reg("下ヒゲ比", "下ヒゲ比", False, lambda d:
     (d[["open", "close"]].min(axis=1) - d.low) / (d.high - d.low).replace(0, np.nan))
# ── 形 ──
_reg("swing高値距離%", "swing高値距離%{}", True, lambda d, n: (d.close / d.high.rolling(n).max() - 1) * 100)
_reg("swing安値距離%", "swing安値距離%{}", True, lambda d, n: (d.close / d.low.rolling(n).min() - 1) * 100)
_reg("高値からの経過バー", "高値からの経過バー{}", False, lambda d, n:
     d.high.rolling(n).apply(lambda x: len(x) - 1 - int(np.argmax(x)), raw=True))
_reg("安値からの経過バー", "安値からの経過バー{}", False, lambda d, n:
     d.low.rolling(n).apply(lambda x: len(x) - 1 - int(np.argmin(x)), raw=True))
# 名前どおり V=+2（下げて上げ）・M=−2（上げて下げ）・一方向=0。旧式は和になっていて
# V も M も 0 になる符号の間違いだった（2026-07-30 検査3 の定義照合で発見・是正）
_reg("形スコア", "形スコア{}(V=+/M=−)", True, lambda d, n:
     np.sign(d.close - d.close.shift(n // 2)) - np.sign(d.close.shift(n // 2) - d.close.shift(n)))
# W字＝ダブルボトムの完成フラグ（2026-07-30 追加・定義と流儀は参照表）
_reg("W字", "W字({},{})", True, lambda d, n, t: _w_flag(d.close, d.high, d.low, n, t))
# ── 山と谷（2026-08-21・M2-2-6・受け入れ条件 24a453d6… の C-1 と D）──
# ★山と谷は k本 遅らせて確定させる（法則 C10 の②）。確定の中身は _fractal_levels に1か所だけ在る。
# ★全部 % で持つ（H6・値段の絶対値を列にしない）。真偽にするのは既存の形（level・cross）＝部品と形を混ぜない。
_reg("fractal高値距離%", "fractal高値距離%({})", True, lambda d, k:
     (d.close / _fractal_levels(d.high, k, True)[0] - 1) * 100)
_reg("fractal安値距離%", "fractal安値距離%({})", True, lambda d, k:
     (d.close / _fractal_levels(d.low, k, False)[0] - 1) * 100)
_reg("高値切り上げ幅%", "高値切り上げ幅%({})", True, lambda d, k:
     (lambda a: (a[0] / a[1] - 1) * 100)(_fractal_levels(d.high, k, True)))
_reg("安値切り上げ幅%", "安値切り上げ幅%({})", True, lambda d, k:
     (lambda a: (a[0] / a[1] - 1) * 100)(_fractal_levels(d.low, k, False)))
# ★構造破断＝終値と「1つ前に確定した谷」との距離。直近の谷との距離は fractal安値距離% が持つので、
#   2本を AND で束ねると法則 U9 の実例「close < 直近2本の確定安値」がそのまま書ける。
#   ★受け入れ条件の本文は「直近で確定した谷」と書いてあるが、そのとおりに作ると fractal安値距離% と
#     1ビットも変わらない重複列になる（47回目の swing高値距離% と同じ型・L-518）。法則 U9 の本文
#     （regime_detection_kb.md §11 の逐語「close < 直近2本の確定15分安値」）に合わせて1つ前の谷にした。
_reg("構造破断距離%", "構造破断距離%({})", True, lambda d, k:
     (d.close / _fractal_levels(d.low, k, False)[1] - 1) * 100)
# ── 位置 ──
_reg("close vs EMA", "close vs EMA{}%", True, lambda d, n:
     (d.close / d.close.ewm(span=n, adjust=False).mean() - 1) * 100)
_reg("close vs SMA", "close vs SMA{}%", True, lambda d, n: (d.close / d.close.rolling(n).mean() - 1) * 100)
_reg("close vs VWAP%", "close vs VWAP%{}", True, lambda d, n: (d.close / ((d.close * d.volume).rolling(n).sum()
     / d.volume.rolling(n).sum().replace(0, np.nan)) - 1) * 100)
# ★2026-10-07（工事 m2c15-period-textbook-20261007・監査 CP60 の修正41 の (b)(c)）＝教科書の VWAP（値段は典型価格）の2つの版を、
#   今の版（終値・n 本の移動窓）を残して別の材料として足す。どちらが良いかは M2-F-10f で比べる（この工事は材料を足すだけ）。
#   (b) 典型価格＝(高値＋安値＋終値)÷3 の n 本の移動窓＝ta の VolumeWeightedAveragePrice の作り
#   (c) UTC の日の0時から積み上げる典型価格＝StockCharts の逐語「VWAP calculations start fresh at the open」「(H+L+C)/3」
#       ＝pandas-ta の vwap（anchor の既定 D）の作り。今の足までを含む（今の版の移動窓も今の足を含む）。
def _vwap_day(d):
    """UTC の日の0時から積み上げる VWAP（値段は典型価格・今の足までを含む）。"""
    key = d.index.floor("D")
    tp = (d.high + d.low + d.close) / 3
    return (tp * d.volume).groupby(key).cumsum() / d.volume.groupby(key).cumsum().replace(0, np.nan)


_reg("close vs VWAP典型%", "close vs VWAP典型%{}", True, lambda d, n: (d.close / ((((d.high + d.low + d.close) / 3) * d.volume)
     .rolling(n).sum() / d.volume.rolling(n).sum().replace(0, np.nan)) - 1) * 100)
_reg("close vs 当日VWAP%", "close vs 当日VWAP%", True, lambda d: (d.close / _vwap_day(d) - 1) * 100)
_reg("close vs Keltner上%", "close vs Keltner上%({},{})", True, lambda d, n, k, atr_n=14:
     (d.close / (d.close.ewm(span=n, adjust=False).mean() + k * _atr(d.high, d.low, d.close, atr_n)) - 1) * 100)
_reg("close vs Keltner下%", "close vs Keltner下%({},{})", True, lambda d, n, k, atr_n=14:
     (d.close / (d.close.ewm(span=n, adjust=False).mean() - k * _atr(d.high, d.low, d.close, atr_n)) - 1) * 100)
_reg("close vs Supertrend%", "close vs Supertrend%({},{})", True, lambda d, n, k:
     (d.close / _supertrend(d.high, d.low, d.close, n, k) - 1) * 100)
# 教科書（StockCharts Price Channels）の逐語「Price Channels are based on prices prior to the current period.」＝今の足を含まない。
# 今の足を含むと close ≤ 高値 なので値は 0 で頭打ちになり、前 n 本の高値の上抜けとその幅が書けない（監査 CP60）。
_reg("close vs 本高値%", "close vs {}本高値%", True, lambda d, n: (d.close / d.high.rolling(n).max().shift(1) - 1) * 100)
_reg("close vs 本安値%", "close vs {}本安値%", True, lambda d, n: (d.close / d.low.rolling(n).min().shift(1) - 1) * 100)
# ── 構造 ──
_reg("close vs pivotPP%", "close vs pivotPP%{}", True, lambda d, n: (d.close / ((d.high.rolling(n).max()
     + d.low.rolling(n).min() + d.close.shift(1)) / 3) - 1) * 100)
# R1/S1 は PP と同じ移動窓の変形（教科書は前期間の高安・終値＝流儀は参照表に明記・2026-07-30 追加）
_reg("close vs pivotR1%", "close vs pivotR1%{}", True, lambda d, n: (d.close / (2 * ((d.high.rolling(n).max()
     + d.low.rolling(n).min() + d.close.shift(1)) / 3) - d.low.rolling(n).min()) - 1) * 100)
_reg("close vs pivotS1%", "close vs pivotS1%{}", True, lambda d, n: (d.close / (2 * ((d.high.rolling(n).max()
     + d.low.rolling(n).min() + d.close.shift(1)) / 3) - d.high.rolling(n).max()) - 1) * 100)


def _pivot_prev_period(d, unit=None):
    """教科書のピボット（StockCharts「Pivot Points」）＝前の期間の高値・安値・終値から作り、その期間のあいだ動かない線。
    逐語「the prior day's high, low, and close」「do not change and remain in play throughout the day」。
    日中の足＝前の UTC の日・日足＝前の月・それより長い足＝前の年（監査 CP60）。
    ★未来を見ない＝前の期間が閉じてから使う（shift(1) で1つ前の期間の値だけを当てる）。"""
    step = pd.Series(d.index).diff().median()
    # ★unit="W"（2026-10-07・工事 m2c15-period-textbook-20261007・K-7 の決定「前期間pivot の3種に前の週の版を別の材料として足す」）＝
    #   足の長さによらず、前の週（月曜0時 UTC に始まる7日）の高値・安値・終値で作る。StockCharts の逐語「Pivot Points for 30-, 60-,
    #   and 120-minute charts use the prior week's high, low, and close.」。週の始まりを月曜にしたのは ISO 8601 の週の決まり
    #   （出どころの逐語は無い＝設計書の「決めたこと」に書いた）。unit を渡さなければ今までと同じ（日中の足は前の日）。
    if unit == "W":
        key = d.index.to_period("W-SUN").to_timestamp()
    elif pd.isna(step) or step < pd.Timedelta("1D"):
        key = d.index.floor("D")
    elif step < pd.Timedelta("7D"):
        key = d.index.to_period("M").to_timestamp()
    else:
        key = d.index.to_period("Y").to_timestamp()
    per = d.groupby(key).agg(high=("high", "max"), low=("low", "min"), close=("close", "last")).shift(1)
    m = per.reindex(key)
    m.index = d.index
    pp = (m["high"] + m["low"] + m["close"]) / 3
    return pp, 2 * pp - m["low"], 2 * pp - m["high"]


_reg("close vs 前期間pivotPP%", "close vs 前期間pivotPP%", True, lambda d: (d.close / _pivot_prev_period(d)[0] - 1) * 100)
_reg("close vs 前期間pivotR1%", "close vs 前期間pivotR1%", True, lambda d: (d.close / _pivot_prev_period(d)[1] - 1) * 100)
_reg("close vs 前期間pivotS1%", "close vs 前期間pivotS1%", True, lambda d: (d.close / _pivot_prev_period(d)[2] - 1) * 100)
# ★2026-10-07（工事 m2c15-period-textbook-20261007・K-7 の決定）＝前の週で固定する版（今の前の日の版は残す）
_reg("close vs 前週pivotPP%", "close vs 前週pivotPP%", True, lambda d: (d.close / _pivot_prev_period(d, "W")[0] - 1) * 100)
_reg("close vs 前週pivotR1%", "close vs 前週pivotR1%", True, lambda d: (d.close / _pivot_prev_period(d, "W")[1] - 1) * 100)
_reg("close vs 前週pivotS1%", "close vs 前週pivotS1%", True, lambda d: (d.close / _pivot_prev_period(d, "W")[2] - 1) * 100)
_reg("fib位置", "fib位置{}", True, lambda d, n: (d.close - d.low.rolling(n).min())
     / (d.high.rolling(n).max() - d.low.rolling(n).min()).replace(0, np.nan))
_reg("close vs POC%", "close vs POC%{}", True, lambda d, n, rows=24:
     (d.close / _vp_levels(d.close, d.volume, n, rows=rows)[0] - 1) * 100)
_reg("close vs VAH%", "close vs VAH%{}", True, lambda d, n, va_pct=0.7, rows=24:
     (d.close / _vp_levels(d.close, d.volume, n, va_pct=va_pct, rows=rows)[1] - 1) * 100)
_reg("close vs VAL%", "close vs VAL%{}", True, lambda d, n, va_pct=0.7, rows=24:
     (d.close / _vp_levels(d.close, d.volume, n, va_pct=va_pct, rows=rows)[2] - 1) * 100)
# ★2026-10-07（工事 m2c15-period-textbook-20261007・監査 CP60 の修正42）＝出来高プロファイルを日で区切る2つの版を、
#   今の版（n 本の移動窓）を残して別の材料として足す。前日＝前の UTC の日で固定／当日＝その日の0時から育つ（_vp_by_day）。
#   区画の数・70% は今の版と同じ既定（名前に出さない引数）。POC は 70% を使わないので、今の POC と同じく区画の数だけを持つ。
_reg("close vs 前日POC%", "close vs 前日POC%", True, lambda d, rows=24:
     (d.close / _vp_by_day(d.close, d.volume, "前日", rows=rows)[0] - 1) * 100)
_reg("close vs 前日VAH%", "close vs 前日VAH%", True, lambda d, va_pct=0.7, rows=24:
     (d.close / _vp_by_day(d.close, d.volume, "前日", va_pct, rows)[1] - 1) * 100)
_reg("close vs 前日VAL%", "close vs 前日VAL%", True, lambda d, va_pct=0.7, rows=24:
     (d.close / _vp_by_day(d.close, d.volume, "前日", va_pct, rows)[2] - 1) * 100)
_reg("close vs 当日POC%", "close vs 当日POC%", True, lambda d, rows=24:
     (d.close / _vp_by_day(d.close, d.volume, "当日", rows=rows)[0] - 1) * 100)
_reg("close vs 当日VAH%", "close vs 当日VAH%", True, lambda d, va_pct=0.7, rows=24:
     (d.close / _vp_by_day(d.close, d.volume, "当日", va_pct, rows)[1] - 1) * 100)
_reg("close vs 当日VAL%", "close vs 当日VAL%", True, lambda d, va_pct=0.7, rows=24:
     (d.close / _vp_by_day(d.close, d.volume, "当日", va_pct, rows)[2] - 1) * 100)
_reg("S-Rタッチ数", "S-Rタッチ数({},{})", False, lambda d, n, t: _sr_touch(d.close, d.high, d.low, n, t))
# ── 2026-09-05（M2-C-4・まこさん承認 iter="m2c4-add-parts-20260905"）に足した ──
#   ★向きを持たない（False）＝状態量。MMI は原典が「向きは測らない」と書いている。
#   ★S-RタッチATR は 2026-09-06（再監査 cp22 の N-1）に外した（理由は _sr_touch の下のコメント）。
_reg("MMI", "MMI{}", False, lambda d, n: _mmi(d.close, n))
# ── 2026-09-26（M2-E-4c・束2・まこさん決定「CCの案の通りで進める」「BでOK」）に足した ──
#   ★S-Rタッチ1時間ATR＝帯の許容幅を「1時間足の ATR% × 倍率」で決め、0.15%〜0.6% に収める。
#     タッチは、その足の高値・安値で数える。向きを持たない（False）＝状態量（S-Rタッチ数と同じ）。
_reg("S-Rタッチ1時間ATR", "S-Rタッチ1時間ATR({},{},{})", False,
     lambda d, n, k, a: _sr_touch_atr(d, n, k, a))
# ── 2026-10-09（工事 m2c15-shape-structure-20261009・K-3b・監査 CP60 の修正43・44・46）＝確定した山・谷で作る教科書の版を、
#   今の版を残して別の材料として足す。どちらが良いかは M2-F-10f で比べる（この工事は材料を足すだけ）。
#   ★確定の本数 k は名前に出さない引数（最初の値 2＝資料の fractal の既定・まこさん「よい」2026-10-09 の1）。向きの印は今の版と同じ。
_reg("W字確定谷", "W字確定谷({},{})", True, lambda d, n, t, k=2: _w_fractal(d.close, d.high, d.low, n, t, k))
_reg("S-Rタッチ確定数", "S-Rタッチ確定数({},{})", False, lambda d, n, t, k=2: _sr_touch_fractal(d, n, t, k))
_reg("S-Rタッチ確定1時間ATR", "S-Rタッチ確定1時間ATR({},{},{})", False,
     lambda d, n, m, a, k=2: _sr_touch_fractal_atr(d, n, m, a, k))
_reg("SMC_SWEEP確定", "SMC_SWEEP確定", False, lambda d, k=2: _smc_sweep_fractal(d, k))
# ── 2026-10-20（工事 m2c15-band-s1-20261020・B-1＋S-1）＝帯の部品4種 × 許容幅の作り2つと、S1 の部品2つ ──
#   ★名前に出すのは 窓・許容幅（または倍率と ATR の期間）・タッチの回数。手数料の倍数は設定ファイル band_fee_mult（名前に出さない）・
#     確定の本数 k も名前に出さない引数（最初の値 2＝資料の fractal の既定・K-3b と同じ）。向きを持たない（False）＝状態量（1/0）。
_reg("帯スイング", "帯スイング({},{},{})", False, lambda d, n, t, m, k=2: _band_swing(d, n, t, m, k))
_reg("帯スイング1時間ATR", "帯スイング1時間ATR({},{},{},{})", False,
     lambda d, n, km, a, m, k=2: _band_swing(d, n, _band_tol_1h(d, km, a), m, k))
#   ★帯pivot・帯VA は、触れた回数を数えない（まこさん「Aでいい」ok_pivot_a_20261020）＝名前に出すのは許容幅（または倍率と ATR の期間）だけ。
_reg("帯pivot", "帯pivot({})", False, lambda d, t: _band_lines(d, *_pivot_prev_period(d)[1:], t))
_reg("帯pivot1時間ATR", "帯pivot1時間ATR({},{})", False,
     lambda d, km, a: _band_lines(d, *_pivot_prev_period(d)[1:], _band_tol_1h(d, km, a)))
_reg("帯VA", "帯VA({})", False, lambda d, t: _band_lines(d, *_vp_by_day(d.close, d.volume, "前日")[1:], t))
_reg("帯VA1時間ATR", "帯VA1時間ATR({},{})", False,
     lambda d, km, a: _band_lines(d, *_vp_by_day(d.close, d.volume, "前日")[1:], _band_tol_1h(d, km, a)))
#   ★2026-10-21（監査 CP83 の修正12・まこさん「ウ」）＝前の週の版（StockCharts の逐語「Pivot Points for 30-, 60-, and 120-minute charts
#     use the prior week's high, low, and close.」）。先例 K-7 の前週pivot と同じく、足の長さによらず全部の足で計算する。
_reg("帯pivot前週", "帯pivot前週({})", False, lambda d, t: _band_lines(d, *_pivot_prev_period(d, "W")[1:], t))
_reg("帯pivot前週1時間ATR", "帯pivot前週1時間ATR({},{})", False,
     lambda d, km, a: _band_lines(d, *_pivot_prev_period(d, "W")[1:], _band_tol_1h(d, km, a)))
#   ★S1＝Lee-Mykland の jump の統計 L_i（今の1本の対数の値動き ÷ ふだんの揺れの平方根）。向きを持つ（上げの jump が正）。
#     閾値 L*（spike_threshold）は材料に入れない（閾値は探す側で扱う・まこさん「OK」ok_direction_20261020 の4）。
#   ★2026-10-21（監査 CP83 の修正1・まこさん「案A」）＝論文の版（LeeMykland）と E36 の版（LeeMykland_E36版）の2つ。どちらが良いかは M2-F-10f で比べる。
_reg("LeeMykland", "LeeMykland{}", True, lambda d, K: pd.Series(lee_mykland_stat(d.close.to_numpy(float), int(K)), index=d.index))
_reg("LeeMykland_E36版", "LeeMykland_E36版{}", True, lambda d, K: pd.Series(spike_stat(d.close.to_numpy(float), int(K)), index=d.index))
# ── 業界の指標（pandas-ta 由来・フロー 段6-2・1回目＝アルファベット順 ao〜lrsi の19関数）──
# ★ローソク足の本数は、ここで新しい数字を作らない。既にある一覧をそのまま使う
#   （rsi_periods / stoch_periods / macd_params）。本数を3つ以上 使う指標（KST）は
#   ライブラリの既定をそのまま使う。★どちらもマイルストーン③で「範囲で探す」に置き換える。
# ★ドルの金額で出る指標（AO・APO・DM・ERI）は、その場で終値で割って%にする（H6・段6-3）。
# ★照合の相手は参照表 indicator_reference_diag が持つ（pandas-ta 同士では照合にならないため）。
_reg("BIAS", "BIAS{}", True, lambda d, n: _pta6.bias(d.close, length=n))
_reg("AR", "AR{}", False, lambda d, n: _pta6.brar(open_=d.open, high=d.high, low=d.low,
                                                  close=d.close, length=n).iloc[:, 0])
_reg("BR", "BR{}", False, lambda d, n: _pta6.brar(open_=d.open, high=d.high, low=d.low,
                                                  close=d.close, length=n).iloc[:, 1])
_reg("CCI", "CCI{}", True, lambda d, n: _pta6.cci(high=d.high, low=d.low, close=d.close, length=n))
_reg("CFO", "CFO{}", False, lambda d, n: _pta6.cfo(close=d.close, length=n))
_reg("CG", "CG{}", False, lambda d, n: _pta6.cg(close=d.close, length=n))
_reg("CMO", "CMO{}", True, lambda d, n: _pta6.cmo(close=d.close, length=n))
_reg("CTI", "CTI{}", True, lambda d, n: _pta6.cti(close=d.close, length=n))
_reg("DM+%", "DM+%{}", True, lambda d, n: _pta6.dm(high=d.high, low=d.low, length=n).iloc[:, 0] / d.close * 100)
_reg("DM-%", "DM-%{}", False, lambda d, n: _pta6.dm(high=d.high, low=d.low, length=n).iloc[:, 1] / d.close * 100)
_reg("ER", "ER{}", False, lambda d, n: _pta6.er(close=d.close, length=n))
_reg("ERI強気%", "ERI強気%{}", True, lambda d, n: _pta6.eri(high=d.high, low=d.low, close=d.close,
                                                          length=n).iloc[:, 0] / d.close * 100)
_reg("ERI弱気%", "ERI弱気%{}", False, lambda d, n: _pta6.eri(high=d.high, low=d.low, close=d.close,
                                                           length=n).iloc[:, 1] / d.close * 100)
_reg("INERTIA", "INERTIA{}", True, lambda d, n: _pta6.inertia(close=d.close, high=d.high, low=d.low, length=n))
# ★LRSI はローソク足の本数を計算に使わない（実物＝length は入力の長さの確認にしか使われず、
#   計算に効くのは gamma だけ）。本数で4通り作ったら4本とも同じ値になった＝1本にした（2026-08-09 実測）。
# ★2026-08-16（段A の A-6）＝gamma をコードの直書き（0.5）から設定ファイル observe_config.json の
#   `lrsi_gamma` へ出した。名前の型に {} を作ったので engine_tuner が gamma を動かせる。
#   いまの値 0.5 は直す前と同じ（CC は数字を作っていない）。広げるのは まこさん。
_reg("LRSI", "LRSI({})", True, lambda d, g_: _pta6.lrsi(close=d.close, gamma=g_))
_reg("BOP", "BOP", True, lambda d: _pta6.bop(open_=d.open, high=d.high, low=d.low, close=d.close))
_reg("KST", "KST", True, lambda d, roc1=None, roc2=None, roc3=None, roc4=None, sma1=None, sma2=None, sma3=None, sma4=None: _pta6.kst(close=d.close, roc1=roc1, roc2=roc2, roc3=roc3, roc4=roc4, sma1=sma1, sma2=sma2, sma3=sma3, sma4=sma4).iloc[:, 0])
_reg("AO%", "AO%", True, lambda d, fast=None, slow=None: _pta6.ao(high=d.high, low=d.low, fast=fast, slow=slow) / d.close * 100)
_reg("APO%", "APO%({},{})", True, lambda d, f_, s_: _pta6.apo(close=d.close, fast=f_, slow=s_) / d.close * 100)
_reg("COPC", "COPC({},{},{})", True, lambda d, g_, f_, s_: _pta6.coppock(close=d.close, length=g_, fast=f_, slow=s_))
_reg("FISHER", "FISHER({},{})", True, lambda d, f_, g_:
     _pta6.fisher(high=d.high, low=d.low, length=f_, signal=g_).iloc[:, 0])
_reg("FISHERシグナル", "FISHERシグナル({},{})", True, lambda d, f_, g_:
     _pta6.fisher(high=d.high, low=d.low, length=f_, signal=g_).iloc[:, 1])
_reg("KSTシグナル", "KSTシグナル{}", True, lambda d, g_, roc1=None, roc2=None, roc3=None, roc4=None, sma1=None, sma2=None, sma3=None, sma4=None: _pta6.kst(close=d.close, signal=g_, roc1=roc1, roc2=roc2, roc3=roc3, roc4=roc4, sma1=sma1, sma2=sma2, sma3=sma3, sma4=sma4).iloc[:, 1])
_reg("KDJ%K", "KDJ%K({},{})", True, lambda d, n, g_:
     _pta6.kdj(high=d.high, low=d.low, close=d.close, length=n, signal=g_).iloc[:, 0])
_reg("KDJ%D", "KDJ%D({},{})", True, lambda d, n, g_:
     _pta6.kdj(high=d.high, low=d.low, close=d.close, length=n, signal=g_).iloc[:, 1])
_reg("KDJ%J", "KDJ%J({},{})", True, lambda d, n, g_:
     _pta6.kdj(high=d.high, low=d.low, close=d.close, length=n, signal=g_).iloc[:, 2])
# ── 業界の指標（2回目＝アルファベット順 macdext〜stc）──
# ★入れなかったもの＝macdext・macdfix・stc の MACD列（うちの MACD と同じ）／slope（mom と同じ）／
#   smi（tsi を 100 で割っただけ）／rocp・rocr・rocr100（うちの ROC）。全部 実データで確かめた。
_reg("MOM%", "MOM%{}", True, lambda d, n: _pta6.mom(close=d.close, length=n) / d.close * 100)
_reg("PGO", "PGO{}", True, lambda d, n: _pta6.pgo(high=d.high, low=d.low, close=d.close, length=n))
_reg("PO", "PO{}", False, lambda d, n: _pta6.po(close=d.close, length=n))
_reg("PSL", "PSL{}", True, lambda d, n: _pta6.psl(close=d.close, length=n))
_reg("RSX", "RSX{}", True, lambda d, n: _pta6.rsx(close=d.close, length=n))
_reg("RVGI", "RVGI({},4)", True, lambda d, n: _pta6.rvgi(open_=d.open, high=d.high, low=d.low,
                                                         close=d.close, length=n).iloc[:, 1])
_reg("RVGIシグナル", "RVGIシグナル({},4)", True, lambda d, n: _pta6.rvgi(open_=d.open, high=d.high, low=d.low,
                                                                     close=d.close, length=n).iloc[:, 2])
_reg("RVGIヒスト", "RVGIヒスト({},4)", True, lambda d, n: _pta6.rvgi(open_=d.open, high=d.high, low=d.low,
                                                                 close=d.close, length=n).iloc[:, 0])
_reg("PPO", "PPO({},{},{})", True, lambda d, f_, s_, g_:
     _pta6.ppo(close=d.close, fast=f_, slow=s_, signal=g_).iloc[:, 0])
_reg("PPOヒスト", "PPOヒスト({},{},{})", True, lambda d, f_, s_, g_:
     _pta6.ppo(close=d.close, fast=f_, slow=s_, signal=g_).iloc[:, 1])
_reg("PPOシグナル", "PPOシグナル({},{},{})", True, lambda d, f_, s_, g_:
     _pta6.ppo(close=d.close, fast=f_, slow=s_, signal=g_).iloc[:, 2])
_reg("PVO", "PVO({},{},{})", False, lambda d, f_, s_, g_:
     _pta6.pvo(volume=d.volume, fast=f_, slow=s_, signal=g_).iloc[:, 0])
_reg("PVOヒスト", "PVOヒスト({},{},{})", False, lambda d, f_, s_, g_:
     _pta6.pvo(volume=d.volume, fast=f_, slow=s_, signal=g_).iloc[:, 1])
_reg("PVOシグナル", "PVOシグナル({},{},{})", False, lambda d, f_, s_, g_:
     _pta6.pvo(volume=d.volume, fast=f_, slow=s_, signal=g_).iloc[:, 2])
# ★下はライブラリの既定の設定をそのまま使う（本数を3つ以上 使う指標＝私が数字を選ばない）
_reg("QQE", "QQE", True, lambda d: _pta6.qqe(close=d.close).iloc[:, 0])
_reg("QQE_RSIMA", "QQE_RSIMA", True, lambda d: _pta6.qqe(close=d.close).iloc[:, 1])
_reg("SMC_SWEEP", "SMC_SWEEP", False, lambda d, length=None, wick_mult=None: _pta6.smc_sweep(open_=d.open, high=d.high, low=d.low, close=d.close, length=length, wick_mult=wick_mult))
# ★SQZ は値段の単位で出る（実測＝4本値を2倍にすると値も2倍・検査13）。H6 に直して % で入れる
#   （2026-08-11・段6 の 6-9①）。前は `SQZ` の名前で値段のまま材料に入っていた。
_reg("SQZ%", "SQZ%", False, lambda d: _pta6.squeeze(high=d.high, low=d.low, close=d.close).iloc[:, 0]
     / d.close * 100)
_reg("SQZ_ON", "SQZ_ON", False, lambda d, bb_length=None, bb_std=None, kc_length=None, kc_scalar=None: _pta6.squeeze(high=d.high, low=d.low, close=d.close, bb_length=bb_length, bb_std=bb_std, kc_length=kc_length, kc_scalar=kc_scalar).iloc[:, 1])
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正47）＝Carter の作り（StockCharts の逐語「Carter uses 20 periods
#   for the moving average and ATR, and 1.5 for the ATR multiplier」）＝ボリンジャー（終値の SMA ± 倍率×σ・ddof 0）が、ケルトナー
#   （代表値段 (H+L+C)/3 の SMA ± 倍率×ATR（Wilder））の内側なら 1。ライブラリの版（中心を終値の SMA・幅を真の値幅の SMA）は残す。
#   ★4つの数は名前に出さない引数（最初の値＝資料の既定 20・2.0・20・1.5）。
def _atr_wilder(d, n):
    """Wilder の ATR（最初の n 本の真の値幅の単純平均を種に (前×(n−1)＋今)/n）。真の値幅の1本目は欠損。"""
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(axis=1).to_numpy(float)
    tr[0] = np.nan
    out = np.full(len(tr), np.nan)
    if len(tr) > n:
        out[n] = np.nanmean(tr[1:n + 1])
        for i in range(n + 1, len(tr)):
            out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return pd.Series(out, index=d.index)


def _sqz_carter(d, bb_length=20, bb_std=2.0, kc_length=20, kc_scalar=1.5):
    tp = (d.high + d.low + d.close) / 3.0
    mid, sd = d.close.rolling(bb_length).mean(), d.close.rolling(bb_length).std(ddof=0)
    km, atr = tp.rolling(kc_length).mean(), _atr_wilder(d, kc_length)
    on = ((mid - bb_std * sd) > (km - kc_scalar * atr)) & ((mid + bb_std * sd) < (km + kc_scalar * atr))
    return on.astype(float).where(atr.notna() & sd.notna())


_reg("SQZ_ON_Carter", "SQZ_ON_Carter", False,
     lambda d, bb_length=20, bb_std=2.0, kc_length=20, kc_scalar=1.5: _sqz_carter(d, bb_length, bb_std, kc_length, kc_scalar))
# ★SQZ_OFF（=1−SQZ_ON）・SQZ_NO（実測で2,000本すべて0）・SQZPRO_OFF（=1−SQZPRO_ON_WIDE）は
#   情報が増えないので入れない（2026-08-09 実測）。
_reg("SQZPRO_ON_WIDE", "SQZPRO_ON_WIDE", False, lambda d, k="WIDE":
     (lambda t: t[[c for c in t.columns if c.endswith(k)][0]])(
         _pta6.squeeze_pro(high=d.high, low=d.low, close=d.close)))
_reg("SQZPRO_ON_NARROW", "SQZPRO_ON_NARROW", False, lambda d, k="NARROW":
     (lambda t: t[[c for c in t.columns if c.endswith(k)][0]])(
         _pta6.squeeze_pro(high=d.high, low=d.low, close=d.close)))
def _stc_textbook(close, tcl=10, f_=12, s_=26, fac=0.5):
    """Schaff Trend Cycle（教科書＝TA-Lib stc の式・Schaff 2008）。戻り＝(STC, 1段目をならした値)。
    ★範囲（窓の最大−最小）が 0 か欠損のときだけ、前の値を持ち越す（TA-Lib の逐語
      「When a range is zero, the fraction keeps its previous value (0 before any).」）。
    ★pandas_ta_classic の stc は1段目を「MACD の窓の最小値 > 0」のときだけ計算する（momentum/stc.py:180）＝
      MACD が窓の中で1回でも 0 以下なら値が凍る（監査 CP60 の実測＝直近10万本の63.87%で凍る・STC の中央値 0.0）。
      だからライブラリの stc を呼ばない。期間 12/26 は直す前と同じ（23/50 にするかは修正 49 で比べる）。"""
    xm = (_pta6.ema(close, length=f_) - _pta6.ema(close, length=s_)).to_numpy(float)
    m = len(xm)

    def stage(x):
        s = pd.Series(x)
        lo = s.rolling(tcl).min().to_numpy(float)
        rng = s.rolling(tcl).max().to_numpy(float) - lo
        st = np.zeros(m)
        sm = np.zeros(m)
        for i in range(1, m):
            st[i] = 100.0 * (x[i] - lo[i]) / rng[i] if rng[i] > 0 else st[i - 1]
            sm[i] = sm[i - 1] + fac * (st[i] - sm[i - 1])
        return sm

    pf = stage(xm)
    return pd.Series(stage(pf), index=close.index), pd.Series(pf, index=close.index)


_reg("STC", "STC", True, lambda d, tcl=10, f_=12, s_=26, fac=0.5: _stc_textbook(d.close, tcl=tcl, f_=f_, s_=s_, fac=fac)[0])
_reg("STCstoch", "STCstoch", True, lambda d, tcl=10, f_=12, s_=26, fac=0.5: _stc_textbook(d.close, tcl=tcl, f_=f_, s_=s_, fac=fac)[1])
# ── 業界の指標（3回目＝アルファベット順 stochf〜willr）──
# ★入れなかったもの＝stochf（うちの Stoch そのもの）／willr（うちの Stoch%K − 100・まこさん決定）／
#   trixh の本体とシグナル（trix と同じ）。
_reg("StochRSI%K", "StochRSI%K{}", True, lambda d, n, k=None:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=k).iloc[:, 0])
_reg("StochRSI%D", "StochRSI%D{}", True, lambda d, n, k=None, d_=None:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=k, d=d_).iloc[:, 1])
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正48）＝原式のならさない値（StockCharts「StochRSI =
#   (RSI - Lowest Low RSI) / (Highest High RSI - Lowest Low RSI)」・0〜100）＝ならしの本数 k を 1 にしたもの。今の %K（SMA3）は残す。
_reg("StochRSI素%K", "StochRSI素%K{}", True, lambda d, n:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=1).iloc[:, 0])
_reg("TRIX", "TRIX({},{})", True, lambda d, n, g_:
     _pta6.trix(close=d.close, length=n, signal=g_).iloc[:, 0])
_reg("TRIXシグナル", "TRIXシグナル({},{})", True, lambda d, n, g_:
     _pta6.trix(close=d.close, length=n, signal=g_).iloc[:, 1])
_reg("TRIXヒスト", "TRIXヒスト({},{})", False, lambda d, n, g_:
     _pta6.trixh(close=d.close, length=n, signal=g_).iloc[:, 2])
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正49）＝シグナルを EMA にした版（StockCharts「The signal line
#   is a 9-day EMA of the TRIX.」）。ライブラリの版（シグナルは単純移動平均）は残す。EMA はライブラリの ema（種＝最初の g 本の単純平均）。
def _trix_ema(d, n, g_):
    tx = _pta6.trix(close=d.close, length=n, signal=g_).iloc[:, 0]
    return tx, _pta6.ema(close=tx, length=g_)


_reg("TRIX_EMAシグナル", "TRIX_EMAシグナル({},{})", True, lambda d, n, g_: _trix_ema(d, n, g_)[1])
_reg("TRIX_EMAヒスト", "TRIX_EMAヒスト({},{})", False, lambda d, n, g_: (lambda t: t[0] - t[1])(_trix_ema(d, n, g_)))
_reg("TD_SEQ_UP", "TD_SEQ_UP", True, lambda d: _tdseq(d, 0))
_reg("TD_SEQ_DN", "TD_SEQ_DN", False, lambda d: _tdseq(d, 1))
_reg("UO", "UO", True, lambda d, fast=None, medium=None, slow=None, fast_w=None, medium_w=None, slow_w=None: _pta6.uo(high=d.high, low=d.low, close=d.close, fast=fast, medium=medium, slow=slow, fast_w=fast_w, medium_w=medium_w, slow_w=slow_w))
_reg("TSI", "TSI({},{},{})", True, lambda d, f_, s_, g_:
     _pta6.tsi(close=d.close, fast=f_, slow=s_, signal=g_).iloc[:, 0])
_reg("TSIシグナル", "TSIシグナル({},{},{})", True, lambda d, f_, s_, g_:
     _pta6.tsi(close=d.close, fast=f_, slow=s_, signal=g_).iloc[:, 1])
_reg("TSIヒスト", "TSIヒスト({},{},{})", False, lambda d, f_, s_, g_:
     (lambda t: t.iloc[:, 0] - t.iloc[:, 1])(
         _pta6.tsi(close=d.close, fast=f_, slow=s_, signal=g_)))
_reg("VWMACD線%", "VWMACD線%({},{},{})", True, lambda d, f_, s_, g_:
     _pta6.vwmacd(close=d.close, volume=d.volume, fast=f_, slow=s_,
                  signal=g_).iloc[:, 0] / d.close * 100)
_reg("VWMACDヒスト%", "VWMACDヒスト%({},{},{})", False, lambda d, f_, s_, g_:
     _pta6.vwmacd(close=d.close, volume=d.volume, fast=f_, slow=s_,
                  signal=g_).iloc[:, 1] / d.close * 100)
_reg("VWMACDシグナル%", "VWMACDシグナル%({},{},{})", True, lambda d, f_, s_, g_:
     _pta6.vwmacd(close=d.close, volume=d.volume, fast=f_, slow=s_,
                  signal=g_).iloc[:, 2] / d.close * 100)
# ── 業界の指標（overlap＝移動平均のなかま）──
# ★移動平均は値段そのもの（H6 違反）なので、必ず2つの形にして入れる。
#   ①close vs X%（終値との距離%）②X傾き%（5本前からの変化率%）＝うちの EMA・SMA と同じ形。
# ★本数は既にある sma_periods（20・50・200）をそのまま使う。新しい数字を作らない。
#   本数を持たない指標（HILO・HT_TRENDLINE・HWMA）はライブラリの既定をそのまま使う。
_MA_FUNCS = [
    # ★ALMA（監査 CP60）＝ライブラリは重みを w_norm[::-1] で逆向きに当てる（overlap/alma.py:37）。
    #   ずらし 0.85 を渡すと山が古い側に来る＝Legoux の定義と逆。0.15 を渡すと、教科書の offset 0.85
    #   （山が新しい側）と同じ重みになる（ガウスの重みは左右対称なので、0.15 の逆向き＝0.85 の正向き）。
    ("ALMA", lambda d, n, distribution_offset=0.15, sigma=None: _pta6.alma(close=d.close, length=n, distribution_offset=distribution_offset, sigma=sigma)),
    ("DEMA", lambda d, n: _pta6.dema(close=d.close, length=n)),
    ("HMA", lambda d, n: _pta6.hma(close=d.close, length=n)),
    ("JMA", lambda d, n, phase=None: _pta6.jma(close=d.close, length=n, phase=phase)),
    ("KAMA", lambda d, n, fast=None, slow=None: _pta6.kama(close=d.close, length=n, fast=fast, slow=slow)),
    ("LINREG", lambda d, n: _pta6.linreg(close=d.close, length=n)),
    ("LRb", lambda d, n: _pta6.linregintercept(close=d.close, length=n)),
    ("MCGD", lambda d, n, c=None: _pta6.mcgd(close=d.close, length=n, c=c)),
    ("MIDPOINT", lambda d, n: _pta6.midpoint(close=d.close, length=n)),
    ("MIDPRICE", lambda d, n: _pta6.midprice(high=d.high, low=d.low, length=n)),
    ("PWMA", lambda d, n: _pta6.pwma(close=d.close, length=n)),
    ("RMA", lambda d, n: _pta6.rma(close=d.close, length=n)),
    ("SINWMA", lambda d, n: _pta6.sinwma(close=d.close, length=n)),
    ("SSF", lambda d, n, poles=None: _pta6.ssf(close=d.close, length=n, poles=poles)),
    ("SWMA", lambda d, n: _pta6.swma(close=d.close, length=n)),
    # ★t3 は先頭の欠損を落とした短い列を返す（実測）。日付で突き合わせ直して長さをそろえる。
    #   データが短くて計算できないときは None を返すので、全部 欠損の列にして落ちないようにする。
    ("T3", lambda d, n, a=None: (lambda r: pd.Series(np.nan, index=d.index) if r is None
                         else r.reindex(d.index))(_pta6.t3(close=d.close, length=n, a=a))),
    ("TEMA", lambda d, n: _pta6.tema(close=d.close, length=n)),
    ("TRIMA", lambda d, n: _pta6.trima(close=d.close, length=n)),
    ("TSF", lambda d, n: _pta6.tsf(close=d.close, length=n)),
    ("VIDYA", lambda d, n: _pta6.vidya(close=d.close, length=n)),
    ("VWMA", lambda d, n: _pta6.vwma(close=d.close, volume=d.volume, length=n)),
    ("WMA", lambda d, n: _pta6.wma(close=d.close, length=n)),
    ("ZLMA", lambda d, n: _pta6.zlma(close=d.close, length=n)),
    ("FWMA", lambda d, n: _pta6.fwma(close=d.close, length=n)),
]
for _nm, _mafn in _MA_FUNCS:
    _reg(f"close vs {_nm}%", f"close vs {_nm}%{{}}", True,
         lambda d, n, f=_mafn, **kw: (d.close / f(d, n, **kw) - 1) * 100)
    if _nm not in ("JMA",):        # JMA は独立実装を書いていない＝傾きも作らない
        _reg(f"{_nm}傾き", f"{_nm}{{}}傾き%", True,
             lambda d, n, f=_mafn, slope_n=5, **kw: f(d, n, **kw).pct_change(slope_n) * 100)
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正51・52）＝教科書の式の版（今の版は残す・傾きの形は作らない）。
def _ssf_avg(c, n):
    """Ehlers のスーパースムーザー（2極）で、入力を2本の平均にしたもの（linnsoft の逐語「Filt = c1*(Close + Close[1]) / 2 + c2*Filt[1] + c3*Filt[2]」）。"""
    x = np.pi * np.sqrt(2.0) / n
    a0 = np.exp(-x)
    b0 = 2.0 * a0 * np.cos(x)
    c2, c3 = b0, -a0 * a0
    c1 = 1.0 - c2 - c3
    v = c.to_numpy(float)
    out = v.copy()
    for i in range(2, len(v)):
        out[i] = c1 * (v[i] + v[i - 1]) / 2.0 + c2 * out[i - 1] + c3 * out[i - 2]
    return pd.Series(out, index=c.index)


def _trima_ta(c, n):
    """TA-Lib の TRIMA（偶数の n＝SMA(SMA(x, n/2), n/2+1)・ta-lib.org の逐語「even: SMA(SMA(x,period/2),period/2+1)」）。奇数の n は今の版と同じ。"""
    if n % 2 == 0:
        return c.rolling(n // 2).mean().rolling(n // 2 + 1).mean()
    h = n // 2 + 1
    return c.rolling(h).mean().rolling(h).mean()


def _vidya_cmo(c, n, m=9):
    """VIDYA で CMO の本数 m を n と別に持つ版（ta-lib.org の逐語「n = optInTimePeriod, m = optInCMOPeriod」）。m は名前に出さない引数（最初の値 9＝資料の既定）。"""
    dif = c.diff()
    up, dn = dif.clip(lower=0).rolling(m).sum(), (-dif).clip(lower=0).rolling(m).sum()
    k = ((up - dn) / (up + dn)).abs().to_numpy(float)
    v = c.to_numpy(float)
    a = 2.0 / (n + 1)
    out = np.full(len(v), np.nan)
    if len(v) >= n:
        out[n - 1] = float(np.nanmean(v[:n]))
        for i in range(n, len(v)):
            kk = 0.0 if np.isnan(k[i]) else k[i]
            out[i] = a * kk * v[i] + (1 - a * kk) * out[i - 1]
    return pd.Series(out, index=c.index)


_reg("close vs SSF平均%", "close vs SSF平均%{}", True, lambda d, n: (d.close / _ssf_avg(d.close, n) - 1) * 100)
_reg("close vs TRIMA_TA%", "close vs TRIMA_TA%{}", True, lambda d, n: (d.close / _trima_ta(d.close, n) - 1) * 100)
_reg("close vs VIDYA_CMO%", "close vs VIDYA_CMO%{}", True, lambda d, n, m=9: (d.close / _vidya_cmo(d.close, n, m) - 1) * 100)
# ★LRangle（直線あてはめの角度）＝2026-08-11 に一度 材料から外したが、同じ日に戻した。
#   ★正しい形＝要件のハード制約（H6）に反する指標は、外すのではなく直して使う。
#   だから「1本あたり何%動くか」の傾きの角度に直して入れる（SQZ% と同じ直し方）。
_reg("LRangle", "LRangle{}", True, lambda d, n: np.degrees(np.arctan(
     _pta6.linregslope(close=d.close, length=n) / d.close * 100)))
_reg("LRslope%", "LRslope%{}", True, lambda d, n: _pta6.linregslope(close=d.close, length=n) / d.close * 100)
_reg("close vs HILO%", "close vs HILO%", True, lambda d, high_length=None, low_length=None: (d.close / _pta6.hilo(high=d.high, low=d.low,
                                                                              close=d.close, high_length=high_length, low_length=low_length).iloc[:, 0] - 1) * 100)
_reg("close vs HT_TRENDLINE%", "close vs HT_TRENDLINE%", True,
     lambda d: (d.close / _pta6.ht_trendline(close=d.close) - 1) * 100)
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正53）＝Ehlers の入力 (高値＋安値)/2 の版（今の版は残す）。
_reg("close vs HT_TRENDLINE_HL%", "close vs HT_TRENDLINE_HL%", True,
     lambda d: (d.close / _pta6.ht_trendline(close=(d.high + d.low) / 2.0) - 1) * 100)
_reg("close vs HWMA%", "close vs HWMA%", True, lambda d, na=None, nb=None, nc=None: (d.close / _pta6.hwma(close=d.close, na=na, nb=nb, nc=nc) - 1) * 100)
_reg("close vs MAMA%", "close vs MAMA%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama(d, fastlimit=fastlimit, slowlimit=slowlimit).iloc[:, 0] - 1) * 100)
_reg("close vs FAMA%", "close vs FAMA%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama(d, fastlimit=fastlimit, slowlimit=slowlimit).iloc[:, 1] - 1) * 100)
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正53）＝Ehlers の入力 (高値＋安値)/2 の版
#   （MAMA.pdf のコードの逐語「Inputs: Price((H+L)/2), FastLimit(.5), SlowLimit(.05);」）。今の版（入力が終値）は残す。
def _mama_hl(d, **kw):
    return _pta6.mama(close=(d.high + d.low) / 2.0, **kw)


_reg("close vs MAMA_HL%", "close vs MAMA_HL%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama_hl(d, fastlimit=fastlimit, slowlimit=slowlimit).iloc[:, 0] - 1) * 100)
_reg("close vs FAMA_HL%", "close vs FAMA_HL%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama_hl(d, fastlimit=fastlimit, slowlimit=slowlimit).iloc[:, 1] - 1) * 100)
# ★MMAR（2026-08-16・段A の A-6 で直した）
#   直す前＝`mmar(close=d.close)` を引数なしで呼び、ライブラリの既定の帯（10・15・20・25・30・35）
#     から1本 取り出していた。だから engine_tuner が範囲 10〜35 から 21 を引くと `MMAR_21` が
#     存在せず KeyError で走行が丸ごと止まった（2026-08-16 実測＝案100本の33本目で停止）。
#   直したあと＝本数 k を `length` で渡し `num_ribbons=1` で1本だけ作る。実物の式は
#     `period = length + i*step` の i=0 ＝ `ema(close, length=k)` なので、k がいまの一覧の
#     どれであっても値は直す前と1ビットも変わらない（恒等の確認は gen_materials の番人）。
_reg("close vs MMAR%", "close vs MMAR%{}", True,
     lambda d, k: (d.close / _pta6.mmar(close=d.close, length=k, num_ribbons=1)[f"MMAR_{k}"] - 1) * 100)
_reg("MMAR傾き", "MMAR{}傾き%", True,
     lambda d, k: _pta6.mmar(close=d.close, length=k, num_ribbons=1)[f"MMAR_{k}"].pct_change(5) * 100)
# ★RAINBOW（2026-08-16・段A の A-6 で直した）
#   RAINBOW は数字を2つ持つ＝①1回あたりの本数 L（ライブラリの既定 2）②何回 重ねがけするか i。
#   直す前＝名前に i しか出ておらず、L はライブラリの既定に隠れていた。L を変えると
#     `close vs RAINBOW%3` という同じ名前のまま中身が別の指標になる（名前の一意性が壊れる）。
#   直したあと＝L も名前に出す（`close vs RAINBOW%(2,3)`＝BB%b(20,2.0) と同じ書き方）。
#     `num_ribbons=i` で i 本目まで作るので、i がいくつでも作れる（重ねがけは前段の結果を
#     さらに平均する漸化式なので、i 本目の値は何本まで作っても同じ）。
_reg("close vs RAINBOW%", "close vs RAINBOW%({},{})", True,
     lambda d, L_, k: (d.close / _pta6.rainbow(close=d.close, length=L_,
                                               num_ribbons=k)[f"RAINBOW_{k}"] - 1) * 100)
_reg("RAINBOW傾き", "RAINBOW({},{})傾き%", True,
     lambda d, L_, k: _pta6.rainbow(close=d.close, length=L_,
                                    num_ribbons=k)[f"RAINBOW_{k}"].pct_change(5) * 100)
# ── 業界の指標（trend 16関数）──
# ★入れなかったもの＝plus_dm・minus_dm（うちの DM+% / DM-% と同じ・実測 最大差 1e-15）。
# ★dpo は既定の centered=True が未来を見る（値を未来の足の方へずらす書き方を使う）ので、
#   必ず centered=False で呼ぶ。
_reg("ADXR", "ADXR{}", False, lambda d, n: _pta6.adxr(high=d.high, low=d.low, close=d.close,
                                                      length=n).iloc[:, 0])
_reg("DI+", "DI+{}", True, lambda d, n: _pta6.adxr(high=d.high, low=d.low, close=d.close,
                                                   length=n).iloc[:, 1])
_reg("DI-", "DI-{}", False, lambda d, n: _pta6.adxr(high=d.high, low=d.low, close=d.close,
                                                    length=n).iloc[:, 2])
_reg("DX", "DX{}", False, lambda d, n: _pta6.dx(high=d.high, low=d.low, close=d.close, length=n))
_reg("AROONU", "AROONU{}", True, lambda d, n: _pta6.aroon(high=d.high, low=d.low, length=n).iloc[:, 1])
_reg("AROOND", "AROOND{}", False, lambda d, n: _pta6.aroon(high=d.high, low=d.low, length=n).iloc[:, 0])
_reg("AROONOSC", "AROONOSC{}", True, lambda d, n: _pta6.aroon(high=d.high, low=d.low, length=n).iloc[:, 2])
_reg("CHOP", "CHOP{}", False, lambda d, n: _pta6.chop(high=d.high, low=d.low, close=d.close, length=n))
_reg("VHF", "VHF{}", False, lambda d, n: _pta6.vhf(close=d.close, length=n))
_reg("VTXP", "VTXP{}", True, lambda d, n: _pta6.vortex(high=d.high, low=d.low, close=d.close,
                                                       length=n).iloc[:, 0])
_reg("VTXM", "VTXM{}", False, lambda d, n: _pta6.vortex(high=d.high, low=d.low, close=d.close,
                                                        length=n).iloc[:, 1])
_reg("QSTICK%", "QSTICK%{}", True, lambda d, n:
     _pta6.qstick(open_=d.open, close=d.close, length=n) / d.close * 100)
_reg("DPO%", "DPO%{}", False, lambda d, n:
     _pta6.dpo(close=d.close, length=n, centered=False) / d.close * 100)
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正37・45 の補足の式）＝教科書の DPO を時点 t で計算できる形
#   「k本前の終値 − いまの n本平均」（k=n/2+1・StockCharts「Price - X-period SMA from {X/2 + 1} periods in the future」）。今の版（いまの終値 −
#   k本前の n本平均＝TradingView の中心化しない版）は残す。未来は見ない。
_reg("DPO教科書%", "DPO教科書%{}", False, lambda d, n:
     (d.close.shift(int(0.5 * n) + 1) - _pta6.sma(close=d.close, length=n)) / d.close * 100)
_reg("TTM_TREND", "TTM_TREND{}", True, lambda d, n: _pta6.ttm_trend(high=d.high, low=d.low, close=d.close,
                                                                    length=n).iloc[:, 0])
# ★AMAT は LR の1列だけ入れる（理由は式で決まる＝slow が打ち消されて効かない・2026-08-09 実測）。
_reg("AMAT_LR", "AMAT_LR", True, lambda d: _pta6.amat(close=d.close).iloc[:, 0])
_reg("close vs CKSPl%", "close vs CKSPl%", True, lambda d, p=None, x=None, q=None: (d.close / _ck(d, p=p, x=x, q=q).iloc[:, 0] - 1) * 100)
_reg("close vs CKSPs%", "close vs CKSPs%", True, lambda d, p=None, x=None, q=None: (d.close / _ck(d, p=p, x=x, q=q).iloc[:, 1] - 1) * 100)
_reg("close vs PMAX%", "close vs PMAX%", True,
     lambda d, length=None, multiplier=None: (d.close / _pta6.pmax(high=d.high, low=d.low, close=d.close, length=length, multiplier=multiplier) - 1) * 100)
_reg("close vs PSAR%", "close vs PSAR%", True,
     lambda d, af0=None, af=None, max_af=None: (d.close / (lambda t: t.iloc[:, 0].fillna(t.iloc[:, 1]))(_ps(d, af0=af0, af=af, max_af=max_af)) - 1) * 100)
_reg("PSAR加速", "PSAR加速", False, lambda d, af0=None, af=None, max_af=None: _ps(d, af0=af0, af=af, max_af=max_af).iloc[:, 2])
_reg("PSAR反転", "PSAR反転", False, lambda d, af0=None, af=None, max_af=None: _ps(d, af0=af0, af=af, max_af=max_af).iloc[:, 3])
# ★ライブラリは売り側の SAR を負の数で返す（pandas_ta_classic 0.6.52 trend/sarext.py:137・TA-Lib の逐語
#   「TA_SAREXT returns negative values when the position is short」）＝絶対値に直してから割る（監査 CP60）。
_reg("close vs SAREXT%", "close vs SAREXT%", True,
     lambda d, startvalue=None, offsetonreverse=None, accelerationinitlong=None, accelerationlong=None, accelerationmaxlong=None, accelerationinitshort=None, accelerationshort=None, accelerationmaxshort=None: (d.close / _pta6.sarext(high=d.high, low=d.low, startvalue=startvalue, offsetonreverse=offsetonreverse, accelerationinitlong=accelerationinitlong, accelerationlong=accelerationlong, accelerationmaxlong=accelerationmaxlong, accelerationinitshort=accelerationinitshort, accelerationshort=accelerationshort, accelerationmaxshort=accelerationmaxshort).abs() - 1) * 100)
# ── 業界の指標（volume 16関数）──
# ★出来高系は、ライブラリの値をそのままでは材料にできない（積み上げは増え続ける・
#   出来高と値段の大きさに引きずられる＝H6 違反）。既に在る OBV傾き と同じ形にそろえる。
_reg("EFI比", "EFI比{}", True, lambda d, n: _pta6.efi(close=d.close, volume=d.volume, length=n)
     / (d.close * d.volume.rolling(n).mean()) * 100)
# ★係数は 1e4＝%が2つ（中値の動き% × 値幅%）の積だから 100×100（100 だと片方ぶんしか戻らない）
_reg("EOM比", "EOM比{}", True, lambda d, n: _pta6.eom(high=d.high, low=d.low, close=d.close,
                                                      volume=d.volume, length=n)
     * d.volume.rolling(n).mean() * 1e4 / (d.close * d.close * 1e8))
_reg("MARKETFI比", "MARKETFI比{}", False, lambda d, n: _pta6.marketfi(high=d.high, low=d.low, volume=d.volume)
     * d.volume.rolling(n).mean() * 100 / d.close)
_reg("NVI傾き", "NVI傾き{}", True, lambda d, n: _pta6.nvi(close=d.close, volume=d.volume).diff(n))
_reg("PVI傾き", "PVI傾き{}", True, lambda d, n: _pta6.pvi(close=d.close, volume=d.volume).diff(n))
_reg("PVOL比", "PVOL比{}", False, lambda d, n: (lambda pv: pv / pv.rolling(n).mean())(
     _pta6.pvol(close=d.close, volume=d.volume)))
_reg("PVT傾き", "PVT傾き{}", True, lambda d, n: _pta6.pvt(close=d.close, volume=d.volume).diff(n)
     / d.volume.rolling(n).sum().replace(0, np.nan))
_reg("WAD傾き", "WAD傾き{}", True, lambda d, n: _pta6.wad(high=d.high, low=d.low, close=d.close).diff(n)
     / d.close * 100)
# 本数を2つ以上 自分で持つ指標＝ライブラリの既定をそのまま使う（本数を私が新しく作らない）
_reg("ADOSC比", "ADOSC比", True, lambda d: _pta6.adosc(high=d.high, low=d.low, close=d.close, volume=d.volume)
     / d.volume.rolling(10).mean())
_reg("AOBV_LR", "AOBV_LR", True, lambda d: _pta6.aobv(close=d.close, volume=d.volume)["AOBV_LR_2"].astype(float))
# ★KVO は「向きを持つ列」ではない（2026-08-10 実測）。理由は参照表の流儀の欄。
_reg("KVO比", "KVO比", False, lambda d: _kv(d).iloc[:, 0] / d.volume.rolling(55).mean())
_reg("KVOシグナル比", "KVOシグナル比", False, lambda d: _kv(d).iloc[:, 1] / d.volume.rolling(55).mean())
_reg("VOSC", "VOSC", False, lambda d: _pta6.vosc(volume=d.volume))
_reg("VFI", "VFI{}", True, lambda d, n: _vfi(d, n))
# ★出来高変化率%＝pvr（1〜4 の区分）の中身の半分。本数は pvr の定義どおり 1 本。
# ★2026-08-16（段A の A-6）＝その 1 を設定ファイルの `volume_change_periods` へ出した。
_reg("出来高変化率%", "出来高変化率%{}", False, lambda d, n: (d.volume / d.volume.shift(n) - 1) * 100)
# ── 業界の指標（statistics 13関数）──
_reg("skew", "skew{}", False, lambda d, n: _pta6.skew(close=d.close, length=n))
_reg("kurtosis", "kurtosis{}", False, lambda d, n: _pta6.kurtosis(close=d.close, length=n))
_reg("MAD比", "MAD比{}", False, lambda d, n: _pta6.mad(close=d.close, length=n) / d.close * 100)
_reg("stdev%", "stdev%{}", False, lambda d, n: _pta6.stdev(close=d.close, length=n) / d.close * 100)
_reg("close vs MEDIAN%", "close vs MEDIAN%{}", True,
     lambda d, n: (d.close / _pta6.median(close=d.close, length=n) - 1) * 100)
_reg("MEDIAN傾き%", "MEDIAN傾き%{}", True,
     lambda d, n: _pta6.median(close=d.close, length=n).pct_change(5) * 100)
# ── 業界の指標（volatility 12関数）──
# ★帯（中心線・上下の帯）は値段そのものなので、終値との距離%にする（H6・close vs SMA% と同じ流儀）。
_reg("close vs ABER_ZG%", "close vs ABER_ZG%", True, lambda d, length=None: (d.close / _ab(d, length=length).iloc[:, 0] - 1) * 100)
_reg("ABER位置", "ABER位置", True,
     lambda d, length=None, atr_length=None: (lambda a: (d.close - a.iloc[:, 2]) / (a.iloc[:, 1] - a.iloc[:, 2]))(_ab(d, length=length, atr_length=atr_length)))
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正45・71）＝Fitschen の原作の Aberration＝80本・標準偏差2倍の
#   ボリンジャーバンドの中の位置（%b と同じ作り・ddof 0）。ライブラリの版（HLC3 の5本 SMA ± ATR15）は残す。
#   ★本数と倍率は名前に出さない引数（最初の値＝原作の既定 80・2.0＝監査の逐語「80本・標準偏差2倍」）。BB%b の範囲は触らない（案の4）。
_reg("ABER原作位置", "ABER原作位置", True, lambda d, length=80, std=2.0:
     (lambda m, s: (d.close - (m - std * s)) / (2.0 * std * s))(d.close.rolling(length).mean(), d.close.rolling(length).std(ddof=0)))
_reg("close vs ACCBL%", "close vs ACCBL%", True, lambda d, length=None, c=None: (d.close / _acb(d, length=length, c=c).iloc[:, 0] - 1) * 100)
_reg("close vs ACCBU%", "close vs ACCBU%", True, lambda d, length=None, c=None: (d.close / _acb(d, length=length, c=c).iloc[:, 2] - 1) * 100)
_reg("close vs CE_L%", "close vs CE_L%", True, lambda d, length=None, multiplier=None: (d.close / _cel(d, length=length, multiplier=multiplier).iloc[:, 0] - 1) * 100)
_reg("close vs CE_S%", "close vs CE_S%", True, lambda d, length=None, multiplier=None: (d.close / _cel(d, length=length, multiplier=multiplier).iloc[:, 1] - 1) * 100)
_reg("HWC位置", "HWC位置", False, lambda d, na=None, nb=None, nc=None, nd=None, scalar=None: _hw(d, na=na, nb=nb, nc=nc, nd=nd, scalar=scalar)["HWPCT"])
_reg("HWC幅%", "HWC幅%", False, lambda d, na=None, nb=None, nc=None, nd=None, scalar=None: _hw(d, na=na, nb=nb, nc=nc, nd=nd, scalar=scalar)["HWW"] / d.close * 100)
_reg("MASSI", "MASSI", False, lambda d, fast=None, slow=None: _pta6.massi(high=d.high, low=d.low, fast=fast, slow=slow))
_reg("PDIST%", "PDIST%", False, lambda d: _pta6.pdist(open_=d.open, high=d.high, low=d.low,
                                                      close=d.close) / d.close * 100)
_reg("TR%", "TR%", False, lambda d: _pta6.true_range(high=d.high, low=d.low, close=d.close) / d.close * 100)
_reg("THERMO%", "THERMO%", False, lambda d: _th(d).iloc[:, 0] / d.close * 100)
_reg("THERMO比", "THERMO比", False, lambda d: (lambda t: t.iloc[:, 0] / t.iloc[:, 1])(_th(d)))
# ★2026-10-11（工事 m2c15-formula-textbook-20261011・K-3c・監査 CP60 の修正45 の直した後の文字）＝Elder の原作＝外へはみ出した幅だけ
#   （max(max(High − PrevHigh, 0), max(PrevLow − Low, 0))・内はらみ足は 0）。ライブラリの版（絶対値）は残す。
def _thermo_orig(d):
    return np.maximum((d.high - d.high.shift(1)).clip(lower=0), (d.low.shift(1) - d.low).clip(lower=0))


_reg("THERMO原作%", "THERMO原作%", False, lambda d: _thermo_orig(d) / d.close * 100)
# ★K-7 の決定（ok_k7_pivot_thermo_20261007）＝EMA でならした版。EMA の本数は名前に出さない引数（最初の値＝ライブラリの既定 20・資料の既定は 20 と 22）。
_reg("THERMO_EMA%", "THERMO_EMA%", False, lambda d, ema_n=20: _pta6.ema(close=_thermo_orig(d), length=ema_n) / d.close * 100)
_reg("CVI", "CVI{}", False, lambda d, n: _pta6.cvi(high=d.high, low=d.low, length=n))
_reg("RVI", "RVI{}", True, lambda d, n: _pta6.rvi(close=d.close, length=n))
_reg("UI", "UI{}", False, lambda d, n: _pta6.ui(close=d.close, length=n))
# ── 業界の指標（cycles 8関数）──
_reg("EBSW", "EBSW", True, lambda d: _ebsw(d))
_reg("HT_DCPERIOD", "HT_DCPERIOD", False,
     lambda d: _cyc(d, "dcperiod", lambda x: _pta6.ht_dcperiod(close=x.close)))
_reg("HT_DCPHASE", "HT_DCPHASE", False,
     lambda d: _cyc(d, "dcphase", lambda x: _pta6.ht_dcphase(close=x.close)))
_reg("HT_INPHASE%", "HT_INPHASE%", True,
     lambda d: _cyc(d, "phasor", lambda x: _pta6.ht_phasor(close=x.close)).iloc[:, 0] / d.close * 100)
_reg("HT_QUAD%", "HT_QUAD%", False,
     lambda d: _cyc(d, "phasor", lambda x: _pta6.ht_phasor(close=x.close)).iloc[:, 1] / d.close * 100)
_reg("HT_SINE", "HT_SINE", False, lambda d: _cyc(d, "htsine", lambda x: _pta6.ht_sine(close=x.close)).iloc[:, 0])
_reg("HT_LEADSINE", "HT_LEADSINE", False,
     lambda d: _cyc(d, "htsine", lambda x: _pta6.ht_sine(close=x.close)).iloc[:, 1])
_reg("HT_TRENDMODE", "HT_TRENDMODE", False,
     lambda d: _cyc(d, "trendmode", lambda x: _pta6.ht_trendmode(close=x.close)))
_reg("MSW_SINE", "MSW_SINE", True, lambda d: _cyc(d, "msw", lambda x: _pta6.msw(close=x.close)).iloc[:, 0])
_reg("MSW_LEAD", "MSW_LEAD", False, lambda d: _cyc(d, "msw", lambda x: _pta6.msw(close=x.close)).iloc[:, 1])
# ── 業界の指標（candles 4関数）──
# ★2026-08-16（段A の A-6）＝本数を直書き（_DOJI_N=10）から設定ファイルの `body_ratio_periods` へ出した。
_reg("実体幅比", "実体幅比{}", False, lambda d, n: (d.close - d.open).abs()
     / (d.high - d.low).rolling(n).mean().shift(1).replace(0, np.nan))
_reg("内側バー", "内側バー", True, lambda d: (((d.high.diff() < 0) & (d.low.diff() > 0)).astype(float)
                                        * np.where(d.close >= d.open, 1.0, -1.0)))
# ★2026-08-16（段A の A-6）＝本数を直書き（_CDLZ_N=30）から設定ファイルの `cdl_z_periods` へ出し、
#   ライブラリにも `length` を渡す形にした（直す前は既定の30が使われていた＝値は変わらない）。
for _k, _c in (("open", 0), ("high", 1), ("low", 2)):
    _reg(f"{_k}_Z", f"{_k}_Z{{}}", True,
         lambda d, n, c=_c: _pta6.cdl_z(open_=d.open, high=d.high, low=d.low,
                                        close=d.close, length=n).iloc[:, c])
_reg("HA実体%", "HA実体%", True, lambda d: (lambda a: (a.iloc[:, 3] - a.iloc[:, 0]) / d.close * 100)(_ha(d)))
_reg("HA上ヒゲ比", "HA上ヒゲ比", False, lambda d: (lambda a: (a.iloc[:, 1] - a.iloc[:, [0, 3]].max(axis=1))
                                           / (a.iloc[:, 1] - a.iloc[:, 2]).replace(0, np.nan))(_ha(d)))
_reg("HA下ヒゲ比", "HA下ヒゲ比", False, lambda d: (lambda a: (a.iloc[:, [0, 3]].min(axis=1) - a.iloc[:, 2])
                                           / (a.iloc[:, 1] - a.iloc[:, 2]).replace(0, np.nan))(_ha(d)))


# ══ 指標カタログ（この道具が正本・呼び出し側は足せない/減らせない）══════
# (表示名, 計算関数, 方向あり?)  方向あり＝値が大きいほど「価格が上」を意味する
def build_catalog(cfg: dict) -> list[tuple]:
    """指標カタログ。期間・パラメータは observe_config.json から取る（コードに焼かない）。

    ★2026-08-13（A-2）＝計算式は上の材料の表（MATERIAL_FAMILIES）に在る。
      この関数がやるのは「設定ファイルの数字を読んで、その組を1つずつ作る」ことだけ。
    """
    C = []

    def add(name, fn, directional):
        C.append((name, fn, directional))

    # ★P-1（2026-10-06・工事 m2c15-param-values-20261006・まこさん決定「A」）＝指標ごとの一覧 material_params に在る種類は、
    #   ほかの指標の期間の一覧（rsi_periods・atr_periods・sma_periods など）を使わず、その一覧の組だけを、最初に出てきた場所で作る。
    #   一覧＝修正対応表の最初の値（スキャル∪デイトレ）＋残す名前（V9・採用中の戦略・確認のレシピ）。プログラムが書いた（CC は値を書いていない）。
    _per = cfg.get("material_params") or {}
    _per_done = set()

    def addf(family, *params):
        """材料の表から1組 作って足す（パラメータは引数で渡す）。指標ごとの一覧に在る種類は、その一覧の組を作る。"""
        if family in _per:
            if family not in _per_done:
                _per_done.add(family)
                for _p in _per[family]:
                    C.append(make_material(family, *_p))
            return
        C.append(make_material(family, *params))

    # ── トレンド/モメンタム ──
    for n in cfg["atr_periods"]:
        addf("ADX", n)
        addf("DI差", n)
    for (f_, s_, g_) in cfg["macd_params"]:
        addf("MACD線%", f_, s_)
        addf("MACDシグナル線%", f_, s_, g_)
        addf("MACDヒスト%", f_, s_, g_)
    for n in cfg["rsi_periods"]:
        addf("RSI", n)
        # ★2026-08-11 に「RSI の差」の列を8本 足したが、同じ日に省いた（まこさん OK・逐語「１はOK」）。
        #   理由＝engine_tuner には元から「いまの値 − n本前の値」を作る形が在った
        #   （engine_tuner_exec.py の form="slope"＝`d = a - np.roll(a, n)`・n は条件ごとの欄）。
        #   ＝列で持つと、同じものを「列」と「形」の2通りで持つことになる（まこさん決定
        #   2026-08-09 の逐語「同じ挙動の指標があれば紛らわしいので片方を省いていく」に当たる）。
        #   ★私が「engine_tuner はこの形を作れない」と報告したのは間違いだった（実物を見ずに、
        #   材料カタログに列が無いことだけを見て言った）。教訓＝材料（列）に無い＝作れない、ではない。
        #   本当の穴は「使い方の側」＝slope の本数が 3・6・12・24 の4つに限定されていること
        #   （recipes/search_limits.json の int_grid）＝マイルストーン③で範囲にする。
    for n in cfg["roc_periods"]:
        addf("ROC", n)
    for n in cfg["stoch_periods"]:
        addf("Stoch%K", n)
        addf("Stoch%D", n)
    for n in cfg["mfi_periods"]:
        addf("MFI", n)
    for n in cfg["cmf_periods"]:
        addf("CMF", n)
    for n in cfg["obv_slope_periods"]:
        addf("OBV傾き", n)
    for (t_, k_) in cfg["ichimoku"]:
        addf("close vs 転換線%", t_)
        addf("close vs 基準線%", k_)
    for n in cfg["rci_periods"]:
        addf("RCI", n)
    for n in cfg["ema_periods"]:
        addf("EMA傾き", n)
    # ── ボラ ──
    for n in cfg["atr_periods"]:
        addf("ATR%", n)
    for n in cfg["bb_periods"]:
        for s in cfg["bb_sigma"]:
            addf("BB%b", n, s)
            addf("BB幅", n, s)
    for n in cfg["realized_vol_periods"]:
        addf("realized_vol", n)
        addf("realized_vol_rv", n)        # 監査 CP60 の修正50（K-3c・2026-10-11）
    for n in cfg["donchian_periods"]:
        addf("Donchian幅%", n)
    for n in cfg["zscore_periods"]:
        addf("zscore", n)
        addf("zscore_return", n)
    # ── 出来高 ──
    for n in cfg["volume_ratio_periods"]:
        addf("volume_ratio", n)
    # ── ローソク ──
    addf("包み足")
    addf("孕み足")
    addf("pinbar")
    addf("連続本数")
    addf("body比")
    addf("上ヒゲ比")
    addf("下ヒゲ比")
    # ── 形 ──
    for n in cfg["swing_windows"]:
        addf("swing高値距離%", n)
        addf("swing安値距離%", n)
        addf("高値からの経過バー", n)
        addf("安値からの経過バー", n)
        addf("形スコア", n)
        for t in cfg["w_tol"]:
            addf("W字", n, t)
            addf("W字確定谷", n, t)           # 監査 CP60 の修正43（K-3b・2026-10-09）
    # ── 山と谷（2026-08-21・M2-2-6）──
    for k in cfg["fractal_k"]:
        addf("fractal高値距離%", k)
        addf("fractal安値距離%", k)
        addf("高値切り上げ幅%", k)
        addf("安値切り上げ幅%", k)
        addf("構造破断距離%", k)
    # ── 位置 ──
    for n in cfg["ema_periods"]:
        addf("close vs EMA", n)
    for n in cfg["sma_periods"]:
        addf("close vs SMA", n)
    for n in cfg["vwap_windows"]:
        addf("close vs VWAP%", n)
        addf("close vs VWAP典型%", n)         # 監査 CP60 の修正41 の (b)（2026-10-07）
    addf("close vs 当日VWAP%")                # 同 (c)
    for (n, k) in cfg["keltner"]:
        addf("close vs Keltner上%", n, k)
        addf("close vs Keltner下%", n, k)
    for (n, k) in cfg["supertrend"]:
        addf("close vs Supertrend%", n, k)
    for n in cfg["swing_windows"]:
        addf("close vs 本高値%", n)
        addf("close vs 本安値%", n)
    # ── 構造 ──
    for n in cfg["pivot_windows"]:
        addf("close vs pivotPP%", n)
        addf("close vs pivotR1%", n)
        addf("close vs pivotS1%", n)
    # 教科書のピボット（前の期間で固定の線・監査 CP60）
    addf("close vs 前期間pivotPP%")
    addf("close vs 前期間pivotR1%")
    addf("close vs 前期間pivotS1%")
    addf("close vs 前週pivotPP%")             # K-7 の決定＝前の週の版（2026-10-07）
    addf("close vs 前週pivotR1%")
    addf("close vs 前週pivotS1%")
    for n in cfg["fib_windows"]:
        addf("fib位置", n)
    for n in cfg["vp_windows"]:
        addf("close vs POC%", n)
        addf("close vs VAH%", n)
        addf("close vs VAL%", n)
    # 監査 CP60 の修正42＝日で区切る2つの版（2026-10-07）
    addf("close vs 前日POC%")
    addf("close vs 前日VAH%")
    addf("close vs 前日VAL%")
    addf("close vs 当日POC%")
    addf("close vs 当日VAH%")
    addf("close vs 当日VAL%")
    for n in cfg["sr_windows"]:
        for t in cfg["sr_tol"]:
            addf("S-Rタッチ数", n, t)
            addf("S-Rタッチ確定数", n, t)     # 監査 CP60 の修正44（K-3b・2026-10-09）
    # ★2026-09-06（再監査 cp22 の N-1）＝S-RタッチATR の展開をここから外した。
    #   理由＝実装が出どころの逐語（ATR%_1h）と違い、5分足で既存の部品の複製になっていた
    #   （相関 +0.9999978）。正しい形は M2-E で作る。詳しくは _sr_touch の下のコメント。
    # ★2026-09-05（M2-C-4）＝MMI（値動きがランダムに近いかの割合）。
    for n in cfg["mmi_periods"]:
        addf("MMI", n)
    # ★2026-09-26（M2-E-4c・束2）＝S-Rタッチ1時間ATR（許容幅＝倍率 × 1時間足の ATR% を 0.15%〜0.6% に収める）。
    #   窓＝sr_windows・倍率＝sr_atr1h_k・ATR の期間＝atr_periods（まこさん決定 2026-09-26 の②）。
    for n in cfg["sr_windows"]:
        for k in cfg["sr_atr1h_k"]:
            for a in cfg["atr_periods"]:
                addf("S-Rタッチ1時間ATR", n, k, a)
                addf("S-Rタッチ確定1時間ATR", n, k, a)   # 監査 CP60 の修正44（K-3b・2026-10-09）
    # ★2026-10-20（工事 m2c15-band-s1-20261020・B-1）＝帯の部品4種 × 許容幅の作り2つ（まこさん「OK」ok_three_points_20261020 の1・2）。
    #   窓＝sr_windows・固定の許容幅＝sr_tol・倍率＝sr_atr1h_k・ATR の期間＝atr_periods（ok_direction_20261020 の2＝今の設定の値）・
    #   タッチの回数＝band_touch（まこさん「1,2OK」＝3・4回・worklog 20261003 §35）。
    #   ★帯pivot・帯VA は窓とタッチの回数を持たない（触れた回数を数えない＝まこさん「Aでいい」ok_pivot_a_20261020）。
    #   ★2026-10-21（監査 CP83 の修正14・まこさん「案B」）＝床は、この関数に渡した設定の band_fee_mult から作り、部品へ結び付ける。
    #   ★2026-10-21（監査 CP83 の修正12・まこさん「ウ」）＝前の週の版の帯pivot（帯pivot前週）も作る。
    _bfl = _band_fee_floor(cfg)
    for n in cfg["sr_windows"]:
        for m in cfg["band_touch"]:
            for t in cfg["sr_tol"]:
                C.append(_band_material("帯スイング", _bfl, n, t, m))
            for k in cfg["sr_atr1h_k"]:
                for a in cfg["atr_periods"]:
                    C.append(_band_material("帯スイング1時間ATR", _bfl, n, k, a, m))
    for t in cfg["sr_tol"]:
        C.append(_band_material("帯pivot", _bfl, t))
        C.append(_band_material("帯pivot前週", _bfl, t))
        C.append(_band_material("帯VA", _bfl, t))
    for k in cfg["sr_atr1h_k"]:
        for a in cfg["atr_periods"]:
            C.append(_band_material("帯pivot1時間ATR", _bfl, k, a))
            C.append(_band_material("帯pivot前週1時間ATR", _bfl, k, a))
            C.append(_band_material("帯VA1時間ATR", _bfl, k, a))
    # ★2026-10-20（S-1）＝スパイクの法則 S1 の部品（Lee-Mykland・K＝lee_mykland_k）。
    #   ★2026-10-21（監査 CP83 の修正1・修正7・まこさん「案A」「案B」「甲」）＝論文の版と E36 の版の2つを、論文の K の推奨値の全部で作る。
    for K in cfg["lee_mykland_k"]:
        addf("LeeMykland", K)
        addf("LeeMykland_E36版", K)

    # ── 業界の指標（pandas-ta 由来・フロー 段6-2・1回目＝アルファベット順 ao〜lrsi の19関数）──
    # ★ローソク足の本数は、ここで新しい数字を作らない。既にある一覧をそのまま使う
    #   （rsi_periods / stoch_periods / macd_params）。本数を3つ以上 使う指標（KST）は
    #   ライブラリの既定をそのまま使う。★どちらもマイルストーン③で「範囲で探す」に置き換える。
    # ★ドルの金額で出る指標（AO・APO・DM・ERI）は、その場で終値で割って%にする（H6・段6-3）。
    # ★照合の相手は参照表 indicator_reference_diag が持つ（pandas-ta 同士では照合にならないため）。
    _load_pta()
    for n in cfg["rsi_periods"]:
        for _fam in ("BIAS", "AR", "BR", "CCI", "CFO", "CG", "CMO", "CTI",
                     "DM+%", "DM-%", "ER", "ERI強気%", "ERI弱気%", "INERTIA"):
            addf(_fam, n)
    for _g in cfg["lrsi_gamma"]:                     # 段A の A-6＝直書き 0.5 を設定ファイルへ出した
        addf("LRSI", _g)
    addf("BOP")
    addf("KST")
    for (f_, s_, g_) in cfg["macd_params"]:
        addf("APO%", f_, s_)
        # ★K-1（2026-10-04・工事 m2c15-indicator-six-items-20261004）＝監査 CP60 の修正13 を当てたとき、下の7種が AO の for の中に入り、
        #   AO の 5・34 と、上の for から漏れた g_ で作られていた（COPC(9,5,34) ほか）。修正13 の前（commit 4656de3）と同じ場所に戻す。
        addf("COPC", g_, f_, s_)
        addf("FISHER", f_, g_)
        addf("FISHERシグナル", f_, g_)
        addf("KSTシグナル", g_)
        for n in cfg["stoch_periods"]:
            addf("KDJ%K", n, g_)
            addf("KDJ%D", n, g_)
            addf("KDJ%J", n, g_)
    # ★AO（2026-10-04・工事 m2c15-hidden-params-20261004・まこさん「A」）＝名前は AO% の1列。2つの本数は名前に出さない引数で受け取る
    #   （何も渡さないときはライブラリの既定＝教科書の 5・34）。
    addf("AO%")

    # ── 業界の指標（2回目＝アルファベット順 macdext〜stc）──
    for n in cfg["rsi_periods"]:
        for _fam in ("MOM%", "PGO", "PO", "PSL", "RSX", "RVGI", "RVGIシグナル", "RVGIヒスト"):
            addf(_fam, n)
    for (f_, s_, g_) in cfg["macd_params"]:
        for _fam in ("PPO", "PPOヒスト", "PPOシグナル", "PVO", "PVOヒスト", "PVOシグナル"):
            addf(_fam, f_, s_, g_)
    for _fam in ("QQE", "QQE_RSIMA", "SMC_SWEEP", "SQZ%", "SQZ_ON",
                 "SQZPRO_ON_WIDE", "SQZPRO_ON_NARROW", "STC", "STCstoch"):
        addf(_fam)
    addf("SMC_SWEEP確定")                     # 監査 CP60 の修正46（K-3b・2026-10-09）
    addf("SQZ_ON_Carter")                     # 監査 CP60 の修正47（K-3c・2026-10-11）

    # ── 業界の指標（3回目＝アルファベット順 stochf〜willr）──
    for n in cfg["rsi_periods"]:
        addf("StochRSI%K", n)
        addf("StochRSI%D", n)
        addf("StochRSI素%K", n)           # 監査 CP60 の修正48（K-3c・2026-10-11）
        for (_f, _s, g_) in cfg["macd_params"]:
            addf("TRIX", n, g_)
            addf("TRIXシグナル", n, g_)
            addf("TRIXヒスト", n, g_)
            addf("TRIX_EMAシグナル", n, g_)   # 監査 CP60 の修正49（K-3c・2026-10-11）
            addf("TRIX_EMAヒスト", n, g_)
    addf("TD_SEQ_UP")
    addf("TD_SEQ_DN")
    addf("UO")
    for (f_, s_, g_) in cfg["macd_params"]:
        for _fam in ("TSI", "TSIシグナル", "TSIヒスト",
                     "VWMACD線%", "VWMACDヒスト%", "VWMACDシグナル%"):
            addf(_fam, f_, s_, g_)

    # ── 業界の指標（overlap 1回目＝アルファベット順 alma〜linregangle）──
    for n in cfg["sma_periods"]:
        for _nm in ("ALMA", "DEMA", "HMA", "JMA", "KAMA", "LINREG"):
            addf(f"close vs {_nm}%", n)
            if _nm not in ("JMA",):            # JMA は独立実装を書いていない＝傾きも作らない
                addf(f"{_nm}傾き", n)
        addf("LRangle", n)
        # ★FWMA はフィボナッチの重みが急に大きくなるので、本数を増やすと古い足の重みが
        #   数値の下限を割ってゼロになり、値が変わらなくなる（実測 2026-08-09＝n=200 では
        #   200本中144本の重みがゼロ・FWMA50 と最大差 8.6e-08＝実質 同じ）。
        #   ゼロになる足が1本でも出る本数は入れない（私の好みでなく、機械で判定できる基準）。
        _fw = [1.0, 1.0]
        while len(_fw) < n:
            _fw.append(_fw[-1] + _fw[-2])
        _fwn = np.array(_fw[:n]) / np.sum(_fw[:n])
        if not (_fwn < 1e-12).any():
            addf("close vs FWMA%", n)
            addf("FWMA傾き", n)
    addf("close vs HILO%")
    addf("close vs HT_TRENDLINE%")
    addf("close vs HT_TRENDLINE_HL%")      # 監査 CP60 の修正53（K-3c・2026-10-11）
    addf("close vs HWMA%")

    # ── 業界の指標（overlap 2回目＝linregintercept〜rma）──
    for n in cfg["sma_periods"]:
        for _nm in ("LRb", "MCGD", "MIDPOINT", "MIDPRICE", "PWMA", "RMA"):
            addf(f"close vs {_nm}%", n)
            addf(f"{_nm}傾き", n)
        addf("LRslope%", n)
    addf("close vs MAMA%")
    addf("close vs FAMA%")
    addf("close vs MAMA_HL%")               # 監査 CP60 の修正53（K-3c・2026-10-11）
    addf("close vs FAMA_HL%")
    # ★mavp は入れない＝既定の使い方が未来を見る（実物の逐語＝periods を
    #   np.linspace(minperiod, maxperiod, len(close)) で作る＝各足で使う本数がデータ全体の
    #   本数で決まる。データが増えると過去の足の値まで変わる）。2026-08-09 実測で検出。
    # ★段A の A-6（2026-08-16）＝本数の一覧をコードの直書きから設定ファイルへ出した。
    #   一覧の数字は直す前と同じ（CC は数字を作っていない）。広げるのは まこさん。
    for _k in cfg["mmar_periods"]:
        if _k in cfg["ema_periods"]:                 # ★既にある EMA と同じ本数は入れない（実測で一致）
            continue
        addf("close vs MMAR%", _k)
        addf("MMAR傾き", _k)
    for _L, _nrib in cfg["rainbow"]:                 # [1回あたりの本数, 何回 重ねがけするか]
        for _k in range(1, int(_nrib) + 1):
            addf("close vs RAINBOW%", _L, _k)
            addf("RAINBOW傾き", _L, _k)

    # ── 業界の指標（overlap 3回目＝sinwma〜zlma）──
    for n in cfg["sma_periods"]:
        for _nm in ("SINWMA", "SSF", "SWMA", "T3", "TEMA", "TRIMA",
                    "TSF", "VIDYA", "VWMA", "WMA", "ZLMA"):
            addf(f"close vs {_nm}%", n)
            addf(f"{_nm}傾き", n)
        addf("close vs SSF平均%", n)       # 監査 CP60 の修正51（K-3c・2026-10-11）
        addf("close vs TRIMA_TA%", n)      # 監査 CP60 の修正52（K-3c・2026-10-11）
        addf("close vs VIDYA_CMO%", n)     # 監査 CP60 の修正52（K-3c・2026-10-11）

    # ── 業界の指標（trend 16関数）──
    for n in cfg["atr_periods"]:
        for _fam in ("ADXR", "DI+", "DI-", "DX", "AROONU", "AROOND", "AROONOSC",
                     "CHOP", "VHF", "VTXP", "VTXM"):
            addf(_fam, n)
    for n in cfg["roc_periods"]:
        addf("QSTICK%", n)
    for n in cfg["donchian_periods"]:
        addf("DPO%", n)
        addf("DPO教科書%", n)              # 監査 CP60 の修正37・45（K-3c・2026-10-11）
        addf("TTM_TREND", n)
    for _fam in ("AMAT_LR", "close vs CKSPl%", "close vs CKSPs%", "close vs PMAX%",
                 "close vs PSAR%", "PSAR加速", "PSAR反転", "close vs SAREXT%"):
        addf(_fam)

    # ── 業界の指標（volume 16関数）──
    # ★出来高系は、ライブラリの値をそのままでは材料にできない（積み上げは増え続ける・
    #   出来高と値段の大きさに引きずられる＝H6 違反）。既に在る OBV傾き と同じ形にそろえる。
    #   無次元にする理由と やり方の一覧＝indicator_reference_diag の volume の節。
    # ★入れなかったもの3件（理由は参照表の INDUSTRY_SKIP に1件ずつ）＝
    #   ad（★うちの CMF そのもの＝重複。総当たりの検出で見つかった）／emv（eom の1万分の1・実測で重複）／
    #   pvr（1〜4 の区分で大小に意味が無い。★中身の半分は下の「出来高変化率%」として入れた）。
    # ★vfi は「入れない」から「入れる」に変えた（まこさん承認 2026-08-10・逐語「１，２は修正して残す」）。
    #   ライブラリの実装は使わず、教科書の式（足切り＝対数リターンの標準偏差×0.2×終値）で下に書いた。
    for n in cfg["obv_slope_periods"]:
        for _fam in ("EFI比", "EOM比", "MARKETFI比", "NVI傾き", "PVI傾き",
                     "PVOL比", "PVT傾き", "WAD傾き"):
            addf(_fam, n)
    for _fam in ("ADOSC比", "AOBV_LR", "KVO比", "KVOシグナル比", "VOSC"):
        addf(_fam)

    # ── まこさん承認で足した2件（2026-08-10・逐語「１，２は修正して残す」）──
    for n in cfg["obv_slope_periods"]:
        addf("VFI", n)
    for n in cfg["volume_change_periods"]:           # 段A の A-6＝直書き 1 を設定ファイルへ出した
        addf("出来高変化率%", n)

    # ── 業界の指標（statistics 13関数）──
    # ★入れなかったもの8件（理由は参照表の INDUSTRY_SKIP に1件ずつ）＝
    #   tos_stdevall（★未来を見る＝既定で「データ全部」に回帰直線を引く）／beta・correl（別の銘柄が要る）／
    #   entropy（★実データでほとんど動かない）／md（mad と同じ）／quantile（median と同じ）／
    #   stderr（stdev の定数倍）／variance（stdev の2乗＝条件として同じ並び）。
    for n in cfg["realized_vol_periods"]:
        for _fam in ("skew", "kurtosis", "MAD比", "stdev%"):
            addf(_fam, n)
    for n in cfg["sma_periods"]:
        addf("close vs MEDIAN%", n)
        addf("MEDIAN傾き%", n)

    # ── 業界の指標（volatility 12関数）──
    # ★帯（中心線・上下の帯）は値段そのものなので、終値との距離%にする（H6・close vs SMA% と同じ流儀）。
    #   値幅（真の値幅・PDIST・温度計）も値段の単位なので、終値で割って%にする。
    # ★入れなかったもの1件（関数まるごと・理由は参照表の INDUSTRY_SKIP）＝
    #   avolume（うちの realized_vol の定数倍＝実測で比が全区間 1つの値）。
    # ★関数の返す列の一部だけ入れなかったもの4件（理由は対応表 INDUSTRY_MAP に1件ずつ）＝
    #   aberration の ATR 列（うちの ATR% と同じ指標）／accbands の中心線（うちの close vs SMA% と実測 差 0）／
    #   hwc の上下の帯（HWC位置 と HWC幅% で表す＝BB%b・BB幅 と同じ流儀）／
    #   thermo の 0/1 の2列（THERMO比 に固定の閾値 2・0.5 を当てただけ＝閾値は engine_tuner が探す）。
    for _fam in ("close vs ABER_ZG%", "ABER位置", "close vs ACCBL%", "close vs ACCBU%",
                 "close vs CE_L%", "close vs CE_S%"):
        addf(_fam)
    addf("ABER原作位置")                     # 監査 CP60 の修正45・71（K-3c・2026-10-11）
    # ★hwc の中心線（HWM）は入れない＝うちに既に在る close vs HWMA% の HWMA と同じ値だった
    #   （2026-08-10 実測＝40,000本すべて 最大差 0.0）。hwc から足すのは、HWMA には無い「帯」の2列だけ。
    #   ★総当たりの重複検出（定数倍＋定数）では捕まらなかった＝終値で割る形が入ると関係が曲がるため。
    #   捕まえたのは「相関 0.999 超の近い組」の報告（相関 −0.999973）。教訓 L-438。
    for _fam in ("HWC位置", "HWC幅%", "MASSI", "PDIST%", "TR%", "THERMO%", "THERMO比"):
        addf(_fam)
    addf("THERMO原作%")                       # 監査 CP60 の修正45・58（K-3c・2026-10-11）
    addf("THERMO_EMA%")                      # K-7 の決定（ok_k7_pivot_thermo_20261007・K-3c・2026-10-11）
    for n in cfg["atr_periods"]:
        addf("CVI", n)
        addf("RVI", n)
        addf("UI", n)

    # ── 業界の指標（cycles 8関数）──
    # ★入れなかったもの1件（関数まるごと・理由は参照表の INDUSTRY_SKIP）＝
    #   dsp（うちの close vs EMA% の単調変換＝実測でスピアマン相関 1.0000000000）。
    # ★ebsw だけ ライブラリの関数を使わない＝角度の単位が違う（教科書 J.F.Ehlers の式は「度」だが、
    #   ライブラリは 360/length などの度の数字を そのままラジアンとして sin/cos に入れている。
    #   2026-08-11 実測＝係数 alpha1 が 教科書 +0.854081 ／ ライブラリ −0.645222 で、
    #   出てくる系列の相関は +0.5878＝別物）。VFI と同じ扱いで、教科書の式で書き直す。
    # ★ヒルベルト変換の5関数は1回の計算で複数の列を返すものがある（ht_phasor・ht_sine）ので、
    #   同じ入力なら計算を使い回す（_cyc）。1本 250,000 本で 12.8 秒かかる重い計算のため。
    for _fam in ("EBSW", "HT_DCPERIOD", "HT_DCPHASE", "HT_INPHASE%", "HT_QUAD%",
                 "HT_SINE", "HT_LEADSINE", "HT_TRENDMODE", "MSW_SINE", "MSW_LEAD"):
        addf(_fam)

    # ── 業界の指標（candles 4関数）──
    # ★入れなかったもの（理由は参照表の INDUSTRY_MAP／INDUSTRY_SKIP に1件ずつ）＝
    #   ①cdl_doji の 0/1 そのもの＝「実体 ≤ 直前10本の平均値幅の10%」という固定の閾値を当てただけ。
    #     閾値は engine_tuner が探すもの（教訓 L-408）。だから中身の連続値 実体幅比10 を入れる。
    #   ②cdl_z の終値の z 値＝うちの zscore の本数違い（2026-08-11 実測＝本数30 のうちの式と
    #     スピアマン相関 1.0000000・最大差 5.3e-07）。始値・高値・安値の z 値は うちに無いので入れる。
    #   ③ha の4本値そのもの＝値段（H6）。実体%と上下のヒゲ比で表す。
    #   ④cdl_pattern＝うちの 包み足・孕み足 で既に入っている。
    # ★段A の A-6（2026-08-16）＝本数の直書き（実体幅比＝10／cdl_z＝30）を設定ファイルへ出した。
    for n in cfg["body_ratio_periods"]:
        addf("実体幅比", n)
    addf("内側バー")
    for _k in ("open", "high", "low"):
        for n in cfg["cdl_z_periods"]:
            addf(f"{_k}_Z", n)
    addf("HA実体%")
    addf("HA上ヒゲ比")
    addf("HA下ヒゲ比")
    _unused = sorted(set(_per) - _per_done)
    if _unused:
        raise SystemExit(f"[材料カタログ] 指標ごとの一覧 material_params の種類が、カタログを作る所で1度も出てこない: {_unused}")
    # ★同じ挙動の列を省く（まこさん OK 2026-08-11・逐語「同じ挙動ならどちらかは使わないように
    #   していいよ」）。どれを省くかは observe_config.json の drop_columns（左＝省く・右＝残す）。
    #   ★ここで消す前に、残す側が本当にカタログに在るかを確かめる（書き間違いで両方 消えないため）。
    drop = {d: k for d, k in (cfg.get("drop_columns") or [])}
    if drop:
        have = {n for n, _f, _d in C}
        # ★P-1（2026-10-06）＝残す側が、指標ごとの一覧で外した名前のときは止めない（省く側も同じ値の列なので、一緒に外れたままにする）。
        _gone = {k for k in drop.values() if k not in have and find_material(k)[0] in _per}
        bad = [f"{d}→{k}" for d, k in drop.items() if k not in have and k not in _gone]
        if bad:
            raise SystemExit(f"[材料カタログ] 省く設定の『残す側』がカタログに無い: {bad}")
        C = [(n, f, d) for n, f, d in C if n not in drop]
    return C


# ══ 指標の組み立て（全時間軸）════════════════════════════════════════════
def _resample(df, rule):
    return df.resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()


def _tail_timestamps(path, n: int = 6) -> list:
    """CSV の末尾の n 本の時刻を返す（★末尾の 8KB だけを読む＝全部は読まない）。

    ★2026-09-08（監査 cp31 の Critical 1・設計書 insp5-path-and-tidy-head-20260908 の B・C・D）。
    読めなければ空の一覧を返す（呼ぶ側が「読めない」として扱う）。
    """
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)                                   # 2 ＝ ファイルの末
            size = f.tell()
            f.seek(max(0, size - 8192))
            tail = f.read().decode("utf-8", "ignore").splitlines()
    except Exception:                                      # noqa: BLE001
        return []
    out: list = []
    for ln in reversed(tail):
        s = ln.split(",")[0].strip()
        try:
            t = pd.Timestamp(s)
        except Exception:                                  # noqa: BLE001
            continue
        if not pd.isna(t):
            out.append(t)
        if len(out) >= n:
            break
    return list(reversed(out))


def _bars_step_minutes(path) -> float | None:
    """その CSV のバーの間隔（分）を返す。測れなければ None。

    ★2026-09-08（監査 cp31 の別枠 F）＝番人 T-i は「渡されたのが5分足か」を見ていなかった。
      1分足のファイルを渡しても通っていた（監査が実測）。末尾の数本の差の中央値で見分ける。
    """
    ts = _tail_timestamps(path, n=6)
    if len(ts) < 2:
        return None
    d = [(ts[i + 1] - ts[i]).total_seconds() for i in range(len(ts) - 1)]
    d = sorted(x for x in d if x > 0)
    if not d:
        return None
    return d[len(d) // 2] / 60.0


def _newer_5m_files(base_end, data_dir=None) -> tuple:
    """data の中に、5分足の正本より後まで在る5分足が置かれていないかを見る。

    ★2026-09-08（監査 cp31 の Critical 1）＝取り足したのに BARS_CSV の指し先が古いままだと、
      番人は古いファイルの末を見て「覆っている」と言い、検査5 は新しいファイルで走って落ちる。
      その状態を番人 T-m が見つける。
    ★2026-09-08（監査 cp32・設計書 tm-scope-and-g2-fingerprint-20260908 の A・B・C）
      ＝見る範囲を3つ直した。
      A＝**Binance Spot 系列だけを見る**（名前に bitget を含むものを外す）。
        要件定義書 §8.2.1.1 の②の逐語＝「採点に使うのは Binance Spot 系列だけ」。
        直す前は Bitget 先物の足まで当たり、「BARS_CSV の指し先を直す」と言っていた
        ＝読んだ人を、禁じられている方へ導く形だった（監査 cp32 の Major）。
      B＝**data の下の階層も見る**（rglob）。直す前は直下だけだったので、
        下の階層に置かれた5分足を見つけられなかった（監査 cp32 の別枠 A）。
      C＝**末の時刻が読めないファイルを、黙って飛ばさない**（名前を返す）。
        直す前は、読めなければ何も言わずに飛ばしていた（同 別枠 B）。
    戻り＝(後まで在るファイルの一覧, 末が読めなかったファイルの名前の一覧)。
    ★data_dir＝見るフォルダ（既定は data）。番人が一時のフォルダで試すために受け取る。
    ★限界＝名前で見分ける（BTCUSDT-5m-… で始まるもの）。data の外は見ない。
    """
    out: list = []
    bad: list = []
    d = (pathlib.Path(data_dir) if data_dir
         else pathlib.Path(__file__).resolve().parent.parent.parent / "data")
    if not d.exists():
        return out, bad
    keep = pathlib.Path(BARS_CSV).name
    for p in sorted(d.rglob("BTCUSDT-5m-*.csv")):          # ★B＝下の階層も見る
        if p.name == keep:
            continue
        if "bitget" in p.name.lower():                     # ★A＝Binance Spot 系列だけを見る
            continue
        ts = _tail_timestamps(p, n=1)
        if not ts:                                         # ★C＝読めないものを黙って飛ばさない
            bad.append(str(p.relative_to(d)))
            continue
        if ts[-1] > base_end:
            out.append((str(p.relative_to(d)), ts[-1]))
    return out, bad


_ONE_MIN_CACHE: dict = {}


def load_1m(start, end, path: str | None = None) -> pd.DataFrame:
    """1分足の元データを読む（1m・3m の材料・2026-08-16 段7 で新設）。

    ★なぜ要るか。5分足のバーは、1分足へ細かく割れない。だから 1m と 3m だけは
    元データを別に読む。ほかの足（10m 以上）は、いままで通り5分足からまとめて作る。
    start・end は5分足のバーの範囲。その範囲だけを切り出して返す（全部を持たない）。
    path はデータ検査の番人が別のファイルを入れるためだけの引数＝通常は渡さない。"""
    import pathlib
    p = pathlib.Path(path) if path else (
        pathlib.Path(__file__).resolve().parent.parent.parent / ONE_MIN_CSV)
    key = (str(p), pd.Timestamp(start), pd.Timestamp(end))
    if key in _ONE_MIN_CACHE:
        return _ONE_MIN_CACHE[key]
    if not p.exists():
        raise SystemExit(f"[1分足] 元データが無い: {p}")
    d = pd.read_csv(p, usecols=["timestamp", "open", "high", "low", "close", "volume"],
                    parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    if d.index.tz is not None:
        d.index = d.index.tz_localize(None)
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    # ★元データが5分足の範囲を覆っていなければ、黙って NaN を作らずに止める。
    if d.index.min() > s or d.index.max() < e:
        raise SystemExit(
            f"[1分足] 元データが5分足の範囲を覆っていない: 元データ {d.index.min()}〜{d.index.max()} ／ "
            f"必要 {s}〜{e}（取り足しが要る）")
    d = d.loc[s:e]
    _ONE_MIN_CACHE[key] = d
    return d


def insp5_frame(span: pd.DataFrame, tf: str, one: pd.DataFrame | None = None):
    """検査5 が使う「その足の枠」を作る（2026-09-08・設計書 insp5-frame-and-table-tidy-20260908 の A）。

    ★なぜ切り出したか＝直す前は、検査5 が 1m・3m を「5分足を入れ直したもの」で作っていた
      （`src = span if tf == "5m" else _resample(span, TF_RULE[tf])`）。5分足は1分・3分に割れないので、
      本数も終値も5分足のまま＝1m・3m の欄を偽の足で数えていた。
      実測（2026-09-08 の やること H）＝`HT_DCPERIOD__1m` の有効本数が 158,112＝5分足と同じ
      （1分足なら 790,560本・3分足なら 263,520本）。
      正しい作りは build_features に在ったのに、検査5 だけ古い形で取り残されていた。
    ★同じ判定を2か所に書き写さないため、検査5 と番人（T-g・T-j）が この関数を呼ぶ。
    返すもの＝(src, closed)。closed＝その足が閉じた時刻（5分足は index そのまま＝未来を見ない）。
    one＝1分足の元データ（渡さなければ、要るときだけ読む）。
    """
    if tf == "5m":
        src = span
    elif tf in SUB_5M_TF:                                # 5分足より短い足＝1分足の元データから作る
        if one is None:
            one = load_1m(span.index[0], span.index[-1])
        src = one if tf == "1m" else _resample(one, TF_RULE[tf])
    else:
        src = _resample(span, TF_RULE[tf])
    _H1_BASE["bars"] = span                          # ★2026-09-26（M2-E-4c）＝build_features と同じ（1時間足の元の5分足）
    closed = src.index if tf == "5m" else src.index + pd.Timedelta(TF_RULE[tf])
    return src, closed


def build_features(bars: pd.DataFrame, cfg: dict, catalog: list | None = None) -> tuple[pd.DataFrame, dict]:
    """指標 × 時間軸 を全部つくる。上位足は『足が閉じた時刻』から使う（未来を見ない）。
    catalog はデータ検査（歩0）の番人がわざと壊した式を注入するためだけの引数＝通常は渡さない。"""
    out, meta = {}, {}
    catalog = catalog or build_catalog(cfg)
    # ★1m・3m を使うときだけ、1分足の元データを読む（使わないなら読まない＝重いので）。
    # ★2026-09-26（M2-E-4c・束2）＝1時間足の値動きの幅の元になる5分足を、部品へ渡す置き場に入れる。
    #   部品の関数はその足のバーしか受け取らないので、2時間足より上では1時間足を作れない（_atr_pct_1h_on）。
    _H1_BASE["bars"] = bars
    one = (load_1m(bars.index[0], bars.index[-1])
           if any(t in cfg["timeframes"] for t in SUB_5M_TF) else None)
    for tf in cfg["timeframes"]:
        if tf == "5m":
            src = bars
        elif tf in SUB_5M_TF:                            # 5分足より短い足＝1分足から作る
            src = one if tf == "1m" else _resample(one, TF_RULE[tf])
        else:
            src = _resample(bars, TF_RULE[tf])
        for name, fn, directional in catalog:
            col = f"{name}__{tf}"
            # ★囲いは「上位足へのずらし」まで含める（2026-08-10 まこさん OK で広げた）。
            #   前は fn(src) の1行だけを囲っていたので、関数が None を そのまま返すと
            #   囲いの外の s.copy() で全体が止まった（実測＝69日ぶんのデータで停止）。
            #   ライブラリには、データが短いと例外でなく None を返す関数がある（t3 ほか）。
            try:
                s = fn(src)
                if s is None:                            # ★例外を出さずに None を返す関数がある
                    meta[col] = ("計算できず", "None を返した（データが短いと起きる）")
                    continue
                if tf != "5m":
                    s = s.copy()
                    s.index = src.index + pd.Timedelta(TF_RULE[tf])
                    # ★K-8（監査 CP60 の修正68・まこさん決定 2026-10-04）＝設定 htf_shift_mode が "bar_close" のときだけ、5分足1本ぶん早める
                    #   （今の作りは1本遅れて届く）。どちらも未来は使わない（5分足の行 R は R+5分に閉じるので、閉じた時刻 ≤ R+5分 の上位足だけが当たる）。
                    if cfg.get("htf_shift_mode", "now") == "bar_close":
                        s.index = s.index - (bars.index[1] - bars.index[0])
                    s = s.reindex(bars.index, method="ffill")
                out[col] = pd.to_numeric(s, errors="coerce")
            except Exception as e:                       # 黙って消さない
                meta[col] = ("計算できず", str(e)[:60]); continue
            meta[col] = ("ok", directional)
    return pd.DataFrame(out, index=bars.index), meta


def load_demand(bars_index, files: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """需給。元データが期間を覆っていない分は NaN のまま残し、被覆率を報告する。
    files はデータ検査（歩0）の番人がわざと壊したファイルを注入するためだけの引数＝通常は渡さない。"""
    import pathlib
    base = pathlib.Path(__file__).resolve().parent
    out, cov = {}, {}
    for name, (rel, tcol, vcol) in (files or _DEMAND_FILES).items():
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


# ══ レンジ幾何列（歩3 冒頭①・CP3 提案2-(a)・設計書 §2.3・2026-08-01）══════════════════════
def _rg_zone_consts() -> tuple[float, int, int]:
    """RG ゾーンビルダーの束ね定数（tol・touch・lookback）を正本 v17 から取る（手打ちしない）。"""
    import e37_scalp as e37                     # lazy＝観察経路と同じ（重い import を必要時だけ）
    rgmod = e37._import_rg5()
    return float(rgmod.v17.ZONE_TOL), int(rgmod.v17.ZONE_TOUCH), int(rgmod.v17.ZONE_LOOKBACK)


def build_range_geometry(bars: pd.DataFrame, adaptive_k=None, h1_edge: str = "right") -> pd.DataFrame:
    """レンジ幾何列を作る（正本ロジック＝build_regime_gate_rg を e37._rg5_frames 経由で import 再利用・
    コピー禁止）。列＝indicator_reference_diag.RANGE_GEO_REF が正本（登録なしの列は足せない＝selftest）。
    adaptive_k=None（既定）＝RG-v5 固定束ね幅。エンジン E38 は RG-v6（e37.V25_K）を渡す＝流儀の違いは
    定義表に記載。全て当該バーまでの確定値（H2）＝検査8 の切り詰め再計算が機械確認する。"""
    import e37_scalp as e37                     # lazy
    d = bars[["open", "high", "low", "close", "volume"]].copy()
    d.insert(0, "ts", bars.index)
    d = d.reset_index(drop=True)
    # ★2026-10-20（工事 m2c15-band-s1-20261020・F-4・監査 CP60 の修正69）＝h1_edge＝帯の1時間足の区切り（right＝今・hour＝正時）
    _z, _up, _rng, res_lo, res_hi, sup_lo, sup_hi = e37._rg5_frames(d, adaptive_k, h1_edge=h1_edge)
    c = bars["close"].to_numpy(float)
    mid = (res_lo + sup_hi) / 2.0               # エンジン v11_mid と同式
    span = res_hi - mid
    with np.errstate(invalid="ignore", divide="ignore"):
        pos = np.where(np.isfinite(span) & (span > 0), (c - mid) / span, np.nan)
        wpct = np.where(np.isfinite(res_hi) & np.isfinite(sup_lo), (res_hi - sup_lo) / c * 100.0, np.nan)
        # ★2026-10-09（工事 m2c15-shape-structure-20261009・監査 CP60 の修正65）＝下半分の位置（下半分の幅＝mid − sup_lo で割る）。
        #   帯内位置% は下半分も上半分の幅で割る（今の版は残す）。定義表＝indicator_reference_diag.RANGE_GEO_REF の 下半分位置
        dn = mid - sup_lo
        low = np.where(np.isfinite(dn) & (dn > 0), (c - mid) / dn, np.nan)
    return pd.DataFrame({"res_hi": res_hi, "res_lo": res_lo, "sup_hi": sup_hi, "sup_lo": sup_lo,
                         "mid": mid, "W%": wpct, "帯内位置%": pos, "下半分位置": low}, index=bars.index)


def _insp_range_geo(bars: pd.DataFrame, cfg: dict) -> list[str]:
    """検査8 レンジ幾何列。①定義表（RANGE_GEO_REF が正本） ②既知答え（合成バー＝電卓式と一致）
    ③切り詰め再計算（検査4 と同じ機構＝未来参照の機械確認） ④値決め窓・採点窓の被覆、を機械出力。"""
    ng = []
    print(f"  定義と流儀（正本＝indicator_reference_diag.RANGE_GEO_REF・時間軸: {iref.RANGE_GEO_TF}）:")
    for nm, r in iref.RANGE_GEO_REF.items():
        print(f"     ◆ {nm} [{'比率＝条件の材料可' if r['kind'] == 'ratio' else '価格水準＝placement 幾何参照専用（H6）'}] … {r['teigi']}")
        print(f"        流儀: {r['ryugi']} ／ 方向: {r['houkou']}")
    tol, touch, lookback = _rg_zone_consts()
    print(f"  束ね定数（正本 v17）: tol {tol} ／ touch {touch} ／ lookback {lookback}")
    ng += iref.range_geo_known_check(build_range_geometry, tol, touch, lookback)
    print(f"  既知答え（合成バー＝電卓式）: {'一致' if not ng else '不一致あり'}")
    # 切り詰め再計算（検査4 と同じ機構・レンジ幾何7列）
    span = bars.loc[bars.index.max() - pd.Timedelta(days=int(cfg["warmup_days"]) + 3):]
    import e37_scalp as _e37g                   # engine_tuner は RG-v6（adaptive_k=V25_K）の帯を使う＝そちらも切り詰めで確かめる（監査 CP60）
    picks = [span.index[-1], span.index[-100], span.index[-400]]
    suspects: dict = {}
    # ★2026-10-20（工事 m2c15-band-s1-20261020・F-4）＝帯の1時間足の区切り2つ（right＝今・hour＝正時）の両方を切り詰めで確かめる
    for _ak in (None, _e37g.V25_K):
        for _edge in ("right", "hour"):
            geo_full = build_range_geometry(span, _ak, _edge)
            for t in picks:
                geo_tr = build_range_geometry(span.loc[:t], _ak, _edge)
                a, b = geo_full.loc[t], geo_tr.loc[t]
                for col in geo_full.columns:
                    x, y = a.get(col), b.get(col)
                    if pd.isna(x) and pd.isna(y):
                        continue
                    if pd.isna(x) != pd.isna(y) or abs(float(x) - float(y)) > 1e-9 * max(1.0, abs(float(x))):
                        suspects.setdefault(f"{col}(adaptive_k={_ak}・h1_edge={_edge})", []).append(str(t))
    print(f"  切り詰め再計算: サンプル時点 {len(picks)}点 × {geo_full.shape[1]} 列 × 帯2種（RG-v5・RG-v6）× 区切り2つ（今・正時） → 不一致 {len(suspects)} 列")
    for col, ts in suspects.items():
        ng.append(f"切り詰めで値が変わるレンジ幾何列（未来参照の疑い）: {col}（時点 {ts}）")
    # 被覆（値決め窓・採点窓＝G2 の基礎データ・判定はしない）
    span2 = bars.loc[SEARCH_START - pd.Timedelta(days=int(cfg["warmup_days"])):]
    geo = build_range_geometry(span2)
    for wname, w0, w1 in _insp_windows():
        seg = geo[(geo.index >= w0) & (geo.index < w1)]
        if not len(seg):
            continue
        pct = 100.0 * seg["帯内位置%"].notna().mean()
        print(f"     被覆 {wname}（帯内位置%＝帯あり∩分母>0）: {pct:.1f}%（有効 {int(seg['帯内位置%'].notna().sum())} バー）")
    return ng


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


def rank_separation_independent(df: pd.DataFrame, mask: pd.Series, cols: list[str], times,
                                taut: set | None = None, top: int = 15) -> pd.DataFrame:
    """分離力の順位づけを、独立な標本だけで出す（★2026-08-22 新設・まこさん指示「今直してほしい」）。

    ★何を直すか。
      上位足の列は、5分足の並びへ引き伸ばして（前の値で埋めて）持っている。
      そのまま1行ずつ数えると、同じ値を何百回も数えることになり、分離力が実力より離れて出る。
      実測（M2-3-3 の1回目の本走）＝日足の分離力が 0.803 と出た。同じ計算を独立な標本だけに
      直したら 0.44〜0.54 に落ちた（worklog 20260822 の §6）。
    ★どう直すか。
      列ごとに時間足が違うので、時間足ごとにまとめて、**その足のバー1本につき1行だけ残して**測る。
      戻り値に「標本数」の欄を足す＝何個で測ったかが必ず見える（黙って数を減らさない）。
    ★限界（正直に）＝勝ち負けの決着が重なる分（保有が長い玉どうし）は、ここでは直していない。
      決着までの長さが玉ごとに違うので、間引く間隔を1つに決められないため。
    """
    ts = pd.DatetimeIndex(times)
    if len(ts) != len(df):
        raise SystemExit(f"[分離力] 行数と時刻の本数が合わない: {len(df)} 行 と {len(ts)} 本")
    by_tf: dict = {}
    for c in cols:
        tf = c.rsplit("__", 1)[1] if "__" in c else "5m"
        by_tf.setdefault(tf if tf in TF_RULE else "5m", []).append(c)
    out = []
    for tf, cs in by_tf.items():
        keep = ~pd.Series(ts).dt.floor(TF_RULE[tf]).duplicated().to_numpy()
        sub, m = df.loc[keep], mask[keep]
        if int(m.sum()) < 10 or int((~m).sum()) < 10:
            continue
        r = rank_separation(sub, m, cs, taut, top=len(cs))
        if len(r):
            r = r.copy()
            r["標本数"] = int(len(sub))
            out.append(r)
    if not out:
        return pd.DataFrame()
    return (pd.concat(out, ignore_index=True).sort_values("|0.5との差|", ascending=False)
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

    mech = mech_thresholds(trades_csv)   # フェーズ1 のものさし＝その走行で実際に使った値から解決
    dir_map = {c: meta[c][1] for c in meta if meta[c][0] == "ok"}
    all_res = {}
    for s in ["SHORT", "LONG"]:
        sub = tr_all[tr_all.side == s]
        if not len(sub):
            print(f"\n★ side={s} は売買記録に0行"); continue
        print("\n\n" + "★" * 50)
        print(f"★ side = {s}   {len(sub)} 行")
        print("★" * 50)
        all_res[s] = _one_side(sub.copy(), bars, feat, dir_map, s, cfg, mech) or []

    picked = _summary(all_res)

    _h(SECTIONS[10])                       # 節10 判定＝この結果はどうなのかを機械が出す（手書き判定を挟まない）
    vd = verdict(tr_all)

    _h(SECTIONS[11])                       # フェーズ11 増やす方向（2026-07-26 まこさん OK）
    grown = grow_search(tr_all, bars, feat, cfg, p0, p1)

    _h(SECTIONS[12])                       # 節12 まとめ（2026-08-03 まこさん「案１でやってみて」・監査 4-18）
    next_actions(vd, picked, grown, p0, p1)

    print("\n" + "#" * 100)
    print("# ⚠️ 疑似シミュ。スロット再回転（L-330）を再現していない＝実エンジンより良く出る。")
    print("#   采否は実装して score.py の採点窓で決める。")
    print("#" * 100)


def next_actions(vd: dict, picked: list, grown: dict, p0, p1) -> None:
    """節12 まとめ＝上の節が機械で出した数字のうち、次の調整に使う3つだけを1画面に並べる。

    経緯（2026-08-03・監査 4-18＝要件 R10）: この道具の出力は節0 から節11 まで長く、
      「次に何をすべきか」が埋もれていた。まこさん指摘「observe_diag ここでの診断結果を
      Report のような文書にまとめて出せば良くないか？」→「案１でやってみて」。

    ★守ること（この関数の設計の芯）:
      ① 新しい計算を1つもしない。上の節が出した値をそのまま並べる（CC の要約・判断を挟まない）。
      ② 順位も付け直さない。①は節10 ③の並び、②は節9 の抽出、③は節11 の抽出をそのまま使う。
      ③ 採否を書かない。ここは材料の提示まで（采否は score.py の採点窓でまこさんが決める）。
      ④ この数字を作った期間を必ず印字する（採点窓）。値を選ぶ窓（値決め窓）とは別だと分かる形にする。
    """
    print(f"  この数字を作った期間: {p0.date()} 〜 {p1.date()}（採点窓）")
    print(f"  値を選ぶ期間はここではない: 値決め窓 {SEARCH_START.date()} 〜 "
          f"{(SEARCH_END - pd.Timedelta(days=1)).date()}（engine_tuner が使う）")
    print("  ⚠️ ここに出るのは材料です。採否は score.py の採点窓でまこさんが決めます。")

    print("\n  ① 減らす方向＝損している区分（節10 ③ の並びのまま・上位5）")
    wr = vd.get("worst_rows")
    if wr is None or not len(wr):
        print("     出せない（売買記録が0行、または区分に使える列が無い）")
    else:
        print("     " + wr.to_string(index=False).replace("\n", "\n     "))
        print("     ＝engine_tuner で調整するなら、この区分に効く値を動かす")

    print("\n  ② 入口の質＝前半と後半の両方でプラスだった候補（節9 の抽出のまま）")
    if not picked:
        print("     0 件（両半期プラスの候補が無い＝前半に合わせただけの疑い・候補にしない）")
    else:
        for label, n, desc in picked:
            print(f"     ・{label}: {n} 行。後半最良 → {desc}")

    print("\n  ③ 増やす方向＝建てなかったが建てていれば取れた場面（節11 の抽出のまま）")
    if not grown:
        print("     0 件（両半期とも概算期待値がプラスの組が無い、または母集団が min_n 未満）")
    else:
        for side, g in grown.items():
            print(f"     ・side {side}: {g['n']} 組（使った出口＝{g['exit']}）")
            print("       " + g["top"].to_string(index=False).replace("\n", "\n       "))

    print("\n  ★この3つを見て、engine_tuner で何を調整するかはまこさんが決めます。"
          "この道具は決めません（要件 R10・診断と探索の受け渡しは人が読んで設定する）。")


def _free_bars(tr_all, bars, p0, p1):
    """建てられたのに建てなかったバー＝期間内のバーから、建てたバーと保有中のバーを除く。

    枠（予算 0.12 BTC）は全部の玉で共有なので、side を分けずに全玉の保有時間で埋める
    （まこさん確認 2026-07-26）。保有中は現実には建てられない＝ここを候補に数えると
    取り逃しを多く見積もりすぎる。"""
    idx = bars.index
    free = np.asarray((idx >= p0) & (idx <= p1))
    for e, x in zip(pd.to_datetime(tr_all.entry_time), pd.to_datetime(tr_all.exit_time)):
        free &= ~np.asarray((idx >= e) & (idx <= x))
    return free


def _pct_exit_scan(sel_idx, bars, side, tp_pcts, sl_pcts, tmax_max):
    """レンジ幾何を使わない走査＝建値からの%だけで到達本数を測る（どの戦略の売買記録でも動く）。
    帯（レンジ中央・災害線）は NaN を渡す＝比較が成立せず「着かなかった」扱いになる。"""
    nan = np.full(len(bars), np.nan)
    g0 = {"res_hi": nan, "res_lo": nan, "sup_hi": nan, "sup_lo": nan}
    return _scene_exit_scan(sel_idx, bars, g0, side, 0.0, nan, list(tp_pcts), list(sl_pcts), tmax_max)


def grow_search(tr_all, bars, feat, cfg, p0, p1):
    """フェーズ11＝増やす方向。建てなかったバーで「建てていれば取れた」条件を探す。

    ここまでのフェーズは建てた玉しか見ていない＝探せるのは減らす方向だけだった（まこさん指摘 2026-07-26）。
    売買記録には建てた玉しか載らないので、建てなかった場面は機械ラベルで勝ち負けを付けて見る。
    判定は建値からの%だけ＝レンジの帯を使わない（戦略に依らず動く・フェーズ10 と同じ思想）。

    ⚠️ 疑似シミュ＝枠の取り合いを見ていない。保有中のバーを母集団から外して近づけるだけ。
       出るのは候補まで＝実際に件数と net が増えるかは層3 の実エンジンでしか分からない。"""
    floor, cost_note = round_trip_cost()      # 概算期待値から引くのは実コスト（設計上の下限ではない）
    print(f"  1往復の実コスト: {cost_note}")
    tps = [float(x) for x in cfg["scene_exit_tp_pcts"]]
    sls = [float(x) for x in cfg["scene_exit_sl_pcts"]]
    tmaxs = [int(x) for x in cfg["scene_exit_tmax_bars"]]
    free = _free_bars(tr_all, bars, p0, p1)
    days = max((p1 - p0).days + 1, 1)
    print(f"  母集団: 期間内のバーのうち、建てたバーと保有中のバーを除いた {int(free.sum())} バー"
          f"（{int(free.sum()) / days:.1f} バー/日）／ 除いた {int(((bars.index >= p0) & (bars.index <= p1)).sum()) - int(free.sum())} バー")
    print(f"  出口: 利確 {tps}% × 損切り {sls}% × 保有の上限 {[t * 5 for t in tmaxs]} 分"
          f"（レンジ中央・災害線は使わない＝帯に依らない）")
    if int(free.sum()) < cfg["min_n"]:
        _skip("建てなかったバーが min_n 未満"); return {}
    grown: dict = {}          # ★まとめ（節12）へ渡す＝画面に出したものと同じ値（2026-08-03・監査 4-18 案1）
    sel = np.where(free)[0]
    times = bars.index[sel]
    half_t = times[len(times) // 2]
    first = np.asarray(times <= half_t)
    second = ~first
    d1 = max((half_t - times.min()).days + 1, 1)
    d2 = max((times.max() - half_t).days + 1, 1)
    for side in sorted(tr_all.side.dropna().unique()):
        print("\n" + "─" * 90)
        print(f"  ■ side = {side}（この向きで建てていたら、の観察）")
        sc = _pct_exit_scan(sel, bars, side, tps, sls, max(tmaxs))
        keep = np.ones(len(sel), bool)
        tbl = _scene_exit_rows(sc, keep, first, second, d1, d2, floor, tps, sls, tmaxs, cfg)
        if not len(tbl):
            _skip("出口の組み合わせが min_n を満たさない"); continue
        print("  ── 条件なし（建てなかったバー全部）＝出口別の期待値 上位5 ──")
        print(tbl.head(5).to_string(index=False))
        # 条件探索に使う出口は「前半の期待値が最良」の1つ＝後半で選び直さない（L-267）
        best = tbl.sort_values("前半_期待値%", ascending=False).iloc[0]
        b_tp = "mid" if best["利確"] == "レンジ中央" else float(str(best["利確"]).rstrip("%"))
        b_sl = "zone" if best["損切り"] == "災害線" else float(str(best["損切り"]).rstrip("%"))
        b_tmax = int(best["保有上限分"]) // 5
        print(f"  条件探索に使う出口（前半の期待値が最良・後半で選び直さない）: "
              f"利確 {best['利確']} / 損切り {best['損切り']} / 保有の上限 {best['保有上限分']}分")
        win, res = _scene_exit_eval(sc, b_tp, b_sl, b_tmax)
        ok = sc["ok"]
        sdf = feat.reindex(times).copy()
        sdf["win"], sdf["res_pct"] = win, res
        sdf = sdf[ok].reset_index(drop=True)
        f1, f2 = first[ok], second[ok]
        base1 = float(win[ok][f1].mean() * 100) if f1.any() else np.nan
        base2 = float(win[ok][f2].mean() * 100) if f2.any() else np.nan
        fcols = [c for c in feat.columns if sdf[c].notna().sum() >= max(int(len(sdf) * 0.5), cfg["min_n"])]
        rows, _raw = _conf_search(sdf, fcols, cfg, f1, f2, base1, base2, d1, d2, floor)
        df = pd.DataFrame(rows)
        if not len(df):
            _skip("足す候補が1件も残らなかった"); continue
        print(f"\n  ── 足す候補（前半で探索・後半は同じ実値で確認）素の勝率 前半 {base1:.1f}% / 後半 {base2:.1f}% ──")
        print(df.to_string(index=False))
        good = df[(df["前半_期待値%"] > 0) & (df["後半_期待値%"] > 0)]
        print(f"\n  └ 両半期とも 概算期待値がプラス: {len(good)} 組 ＝ここが入口を足す候補（勝率だけで渡さない）")
        if len(good):
            print(good.to_string(index=False))
            print("     ※ バー/日 がそのまま増える件数ではない（枠が空いている時しか建たない）。"
                  "件数の実力は層3 の実エンジンで見る。")
            grown[side] = {"n": len(good), "exit": f"利確 {best['利確']} / 損切り {best['損切り']}"
                                                   f" / 保有の上限 {best['保有上限分']}分",
                           "top": good.head(3)}
    print("\n  ⚠️ 枠の取り合いを見ていない疑似シミュ＝候補の材料まで。値決めは層3・採否は採点窓 score.py。")
    return grown


def _one_side(tr, bars, feat, dir_map, side, cfg, mech):
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
    _mech_decompose(tr, side, cfg, mech)

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


_MECH_KEYS = ("V53_FAST_MIN", "V53_ADV_PCT", "V59_WAIT_MIN",
              "V59_FLAT_WIN_MIN", "V59_DOWN_ADV_PCT", "V59_FLAT_ADV_PCT")


def mech_thresholds(trades_csv: str):
    """フェーズ1 のものさし（撤退機構の閾値）を、その走行で実際に使った値から解決する。

    ★取り違え防止（2026-07-26 まこさん OK）＝以前は e37_scalp のモジュール定数を無条件で import して
      いた。E38 が段4/段5 で値を変えると、変えたあとの売買記録を古い E37 の値で分類してしまい、
      出血がどの仕組みから出ているかを読み違える。しかも表は普通に出るので間違いに気づけない。

    解決の順番:
      ① 売買記録の隣の <stem>_params.json（その走行で実際に使った値の記録）から6つ全部を読めたら、それを使う。
      ② 読めない時は、そのサイドカーの script が e37_scalp.py の時に限り、e37_scalp のモジュール定数を使う
         （その売買記録を出した実装そのものなので取り違えにならない）。
      ③ どちらでもない時は None を返す＝表を出さない（黙って別の戦略の値で分類しない）。
    返す: (値の dict, 出所の説明) ／ 解決できなければ (None, 理由)。"""
    import json
    import pathlib
    import re
    p = pathlib.Path(trades_csv)
    side_car = p.with_name(p.stem + "_params.json")
    if not side_car.exists():
        return None, f"使用パラメータの記録が無い: {side_car.name}"
    raw = side_car.read_text(encoding="utf-8")
    got = {}
    for k in _MECH_KEYS:                       # キー名の中に「名前 = 値」で入る形（E38）にも当たる
        m = re.search(rf"{k}\s*=\s*(-?[0-9]+(?:\.[0-9]+)?)", raw)
        if m:
            got[k] = float(m.group(1))
    src = f"{side_car.name}（その走行で実際に使った値）"
    if len(got) < len(_MECH_KEYS):
        try:
            script = str(json.loads(raw).get("script", ""))
        except Exception as e:
            return (got, f"{src}／使用パラメータの記録を読めない: {e}") if got else \
                (None, f"使用パラメータの記録を読めない: {e}")
        if script == "e37_scalp.py":     # その売買記録を出した実装そのもの＝取り違えにならない
            try:
                import e37_scalp as _e37
                for k in _MECH_KEYS:
                    got.setdefault(k, float(getattr(_e37, k)))
                src = "e37_scalp のモジュール定数（この売買記録を出した実装そのもの）"
            except Exception as e:
                src = f"{src}／e37_scalp の定数を読めない: {e}"
    if not got:
        return None, ("ものさしが1つも決まらない＝使用パラメータの記録に閾値が載っておらず、"
                      "この売買記録を出した実装の定数も使えない（別の戦略の値で分類しない）")
    miss = [k for k in _MECH_KEYS if k not in got]
    if miss:
        src += f"／値が無くて分類できない仕組みあり（{', '.join(miss)}）"
    return got, src


def _mech_decompose(tr, side, cfg, mech):
    """節1＝TREND_CONT を「どの撤退機構が切ったか」で分ける（概算）。
    分類は 価格水準（建値からの決済位置%）と保有時間からの再導出＝実装の分岐ログではない。
    境界の玉は誤分類しうる（その注記ごと読む）。閾値は mech_thresholds が解決した値（手打ちしない）。"""
    tc = tr[tr.exit_reason == "TREND_CONT"]
    if not len(tc):
        _skip("TREND_CONT の玉が 0 行（この side には撤退機構の玉が無い）"); return
    if side != "SHORT":
        _skip(f"side={side} は TREND_CONT {len(tc)} 行あるが撤退機構はショート用＝分解しない"); return
    th, src = mech
    if th is None:
        _skip(f"ものさしが解決できないので分解しない（黙って別の値で分類しない）: {src}"); return
    TOL = 0.02   # 水準一致の許容%（stop はギャップで水準より不利側に約定しうる＝下側のみ緩める・診断専用）
    # 仕組みごとに要る値が揃っている分だけ分類する（揃わない仕組みは分類しない＝その他へ落ちる・黙らない）
    can53 = all(k in th for k in ("V53_FAST_MIN", "V53_ADV_PCT"))
    can59d = all(k in th for k in ("V59_WAIT_MIN", "V59_DOWN_ADV_PCT"))
    can59f = all(k in th for k in ("V59_WAIT_MIN", "V59_FLAT_WIN_MIN", "V59_FLAT_ADV_PCT"))
    print(f"  ものさしの出所: {src}")
    print("  ものさしの値: " + " / ".join(f"{k}={th[k]:g}" for k in _MECH_KEYS if k in th))
    if not (can53 or can59d or can59f):
        _skip("値が揃う仕組みが1つも無いので分解しない（黙って別の値で分類しない）"); return
    rules = []
    if can53:
        rules.append(f"v53={{flat_up ∩ 未搭乗 ∩ 保有≤{th['V53_FAST_MIN']:g}分 "
                     f"∩ 決済位置≥+{th['V53_ADV_PCT']:g}−{TOL}%}}")
    if can59d:
        rules.append(f"v59_down={{down ∩ 保有≥{th['V59_WAIT_MIN']:g}分 "
                     f"∩ 決済位置≥+{round(th['V59_DOWN_ADV_PCT'], 3)}−{TOL}%}}")
    if can59f:
        rules.append(f"v59_flat={{flat_up ∩ 保有{th['V59_WAIT_MIN']:g}〜{th['V59_FLAT_WIN_MIN']:g}分 "
                     f"∩ 決済位置≥+{round(th['V59_FLAT_ADV_PCT'], 3)}−{TOL}%}}")
    print("  分類規則（概算・上から順に判定）: " + " → ".join(rules) + " → 残り=その他")
    for _nm, _ok in (("v53 幾何早切り", can53), ("v59 急騰早切り(down)", can59d),
                     ("v59 急騰早切り(flat)", can59f)):
        if not _ok:
            print(f"  ⚠️ {_nm} は値が無いので分類しない＝この仕組みの玉は「その他」に入る（見かけ上ゼロになる）")
    tc = tc.copy()
    def _cls(t):
        p = t["決済位置%"]
        if can53 and t.ceil_type == "flat_up" and t.hold_min <= th["V53_FAST_MIN"] \
                and bool(t.get("一度も利にならず", False)) and p >= th["V53_ADV_PCT"] - TOL:
            return "v53 幾何早切り"
        if can59d and t.ceil_type == "down" and t.hold_min >= th["V59_WAIT_MIN"] \
                and p >= th["V59_DOWN_ADV_PCT"] - TOL:
            return "v59 急騰早切り(down)"
        if can59f and t.ceil_type == "flat_up" and th["V59_WAIT_MIN"] <= t.hold_min <= th["V59_FLAT_WIN_MIN"] \
                and p >= th["V59_FLAT_ADV_PCT"] - TOL:
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


def _summary(all_res: dict) -> list:
    """結果サマリの自動生成（手書きなし）。各分岐×モードの上位10（重複除去後）から
    前半・後半の両方で正味プラスの行だけを機械抽出して1枚に出す。CC の要約を挟まない。

    戻り値＝まとめ（節12）へ渡す (ラベル, 行数, 後半最良の説明) の一覧。
    ★画面に出したものと同じ値をそのまま返すだけ＝新しい計算をしない（2026-08-03・監査 4-18 案1）。"""
    _h(SECTIONS[9])
    print("  機械集計＝各分岐×モードの上位10のうち、前半と後半の両方で正味プラスの行。解釈と採否はまこさん＋score.py。")
    picked: list = []
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
                picked.append((label, len(both), desc))
    print("\n  ⚠️ 疑似シミュの機械集計＝候補の提示まで。採否は実装して score.py の採点窓で決める。")
    return picked


# ══ Entry 候補観察（--scene・2026-07-25 まこさん承認「それでOK」）═══════════
# まだ玉のない新 Entry 候補（S2〜/L2〜）の層1 観察＝場面バーを母集団にし、機械ラベルで勝ち負けを付け、
# カタログ全体で 1次元の分離力 → 異種カテゴリ AND のコンフルエンス探索まで出す。
# 1軸のみ検索の失敗（確認候補の決め打ち・単一条件探索＝worklog 20260724 §25/§26）を構造で防ぐ:
#  - 部品＝「指標×パラメータ×時間足×閾値の位置」の4軸が決まって1個（閾値は分位＝値を手で決めない）。
#  - 組＝別カテゴリ（ボラ/トレンド/位置構造/出来高需給/ローソク）から 2〜3個＝同族の二度掛け禁止。
#  - 時間足は1つの組に2種類以上を強制（5分×上位足の MTF コンフルエンス・§25 実測の2軸と同型）。
#  - 閾値は前半の分布で実値化し、後半は同じ実値のまま確認（L-267）。評価は勝率の持ち上げ×件数下限（金額なし）。
# 出た組は材料まで＝値決めは層3 engine_tuner（探索窓）・採否は採点窓 score.py（まこさん）。

SECTIONS_SCENE = [
    "0 その場面が1日に何回あるかと、条件なしの勝ち負け・負けの中身・概算の期待値を数える",
    "1 指標1つずつで勝ち負けがどれだけ分かれるかを順位づける（材料出しのみ＝ここでは決めない）",
    "2 種類の違う指標を2〜3個重ねて、勝率が上がる組を探す（時間足2種以上・前半で探して後半で確認）",
    "3 両方の期間で勝率も期待値もプラスの組だけを抜き出す（機械が抽出・手書きなし）",
    "4 出口の組み合わせを比べる（利確 × 損切り × 保有の上限・期待値で順位づけ・入口の条件とセットでも見る）",
]

# 場面の型は _SCENE_KINDS（登録表）が正本＝この一覧は登録表から機械で作る（手で並べない・ずれない）。
# 型を足す手順＝関数を1つ書いて登録表に1行足す。★型を足すのはまこさんの承認が要る（2026-07-26 確認）。


def _category(col: str) -> str:
    """列名から部品カテゴリを機械分類（1つの組は別カテゴリから選ぶ＝同族の二度掛け禁止）。"""
    base = col.split("__")[0]
    if any(k in base for k in ("ATR%", "BB幅", "realized_vol", "Donchian幅")):
        return "ボラ"
    if any(k in base for k in ("volume_ratio", "OBV", "CMF", "MFI", "taker_ls", "L-S比", "CVD")):
        return "出来高需給"
    if any(k in base for k in ("包み足", "pinbar", "連続本数", "body比", "ヒゲ比")):
        return "ローソク"
    if any(k in base for k in ("close vs", "swing", "経過バー", "fib位置", "S-Rタッチ",
                               "pivotPP", "形スコア", "zscore", "BB%b")):
        return "位置構造"
    return "トレンド"


def round_trip_cost() -> tuple[float, str]:
    """1往復の実コスト%（概算期待値から引く額）。値は eval_engine の確定値から取る＝手打ちしない。

    ★2026-07-26 まこさん指示で是正。それまでは e37 の SCALP_FLOOR（0.080%）を「手数料床」として
      引いていたが、あれは**利確をこれより狭く置くなという設計上の下限**であって手数料ではない。
      実コストの約2.9倍を引いていた＝全部の期待値が実際より悪く見えていた。

    まこさんの指示（2026-07-26 逐語）＝「基本出口はtakerでもいいけど、入口はmaker以外では立てない」。
      入口＝指値 maker（post_only・約定しなければ建たない）
      出口＝成行 taker ＋ 滑り（保守側に寄せる。指値で利確できた玉はこれより安く済む）"""
    from eval_engine import MAKER_FEE, TAKER_FEE, SLIPPAGE
    c = (MAKER_FEE + TAKER_FEE + SLIPPAGE) * 100.0
    return c, (f"入口 maker {MAKER_FEE * 100:.3f}% ＋ 出口 taker {TAKER_FEE * 100:.3f}%"
               f" ＋ 滑り {SLIPPAGE * 100:.3f}% ＝ {c:.3f}%（eval_engine の確定値・まこさん指示 2026-07-26）")


def _scene_floor(cfg) -> float:
    """S2 の戻り幅の下限%。config が null なら e37 の手数料床 SCALP_FLOOR を実行時に解決（手打ちしない）。"""
    if cfg.get("scene_floor_pct") is not None:
        return float(cfg["scene_floor_pct"])
    import e37_scalp as e37
    return float(e37.SCALP_FLOOR) * 100.0


def _scene_data(cfg):
    """5分足とレンジ幾何＝e37 の計器（_load/_rg5_frames）を import 再利用（自前で再実装しない）。
    暖機は warmup_days 日（最長指標 SMA200×日足のため・観察対象は採点窓のバーのみ）。"""
    import e37_scalp as e37
    p0, p1 = _resolve_period(cfg)
    warm = (p0 - pd.Timedelta(days=int(cfg["warmup_days"]))).strftime("%Y-%m-%d")
    df = e37._load(0, start_override=warm)
    # ★監査 CP84 の修正5＝帯の1時間足の区切りを、E38 の設定（global.regime.h1_edge）から読む（測る道具と同じ区切りの帯にする）
    import json as _json_h1
    _h1e = _json_h1.loads((pathlib.Path(__file__).resolve().parent / "e38_logics.json").read_text(encoding="utf-8"))["global"]["regime"]["h1_edge"]
    _z, _up, rng, res_lo, res_hi, sup_lo, sup_hi = e37._rg5_frames(df, adaptive_k=e37.V25_K, h1_edge=_h1e)
    ts = pd.DatetimeIndex(df["ts"])
    bars = df.set_index(ts)[["open", "high", "low", "close", "volume"]]
    g = {"rng": rng, "res_lo": res_lo, "res_hi": res_hi, "sup_lo": sup_lo, "sup_hi": sup_hi,
         "dev_z": df["dev_z"].to_numpy(float) if "dev_z" in df.columns else None}
    w = np.asarray((ts >= p0) & (ts < p1 + pd.Timedelta(days=1)))
    return bars, g, w, p0, p1


# ══ 場面の型（1つの型＝1つの関数・登録表 _SCENE_KINDS に並べる）════════════
#   型を足す手順＝下に関数を1つ書いて _SCENE_KINDS に1行足すだけ（一覧・エラー文言・説明書は自動で追従）。
#   ★型を足すのはまこさんの承認が要る（2026-07-26 確認）＝CC が思いついた型を勝手に増やさない。
#   関数の約束＝(scene, x) を受け取り、場面バーの bool 配列を返す。x は _scene_ctx が作る共通の材料。

def _scene_ctx(bars, g, floor_pct: float) -> dict:
    """型の関数が共通で使う材料。レンジの帯・価格・出来高・戻り幅の床。"""
    c = bars.close.to_numpy()
    return {
        "h": bars.high.to_numpy(), "l": bars.low.to_numpy(), "c": c,
        "v": bars.volume.to_numpy(), "bars": bars, "g": g, "floor": floor_pct,
        "base": (g["rng"] & np.isfinite(g["res_hi"]) & np.isfinite(g["sup_hi"])
                 & np.isfinite(g["res_lo"]) & np.isfinite(g["sup_lo"])),
        "mid": (g["res_lo"] + g["sup_hi"]) / 2.0,
    }


def _touch_filter(scene: dict, x: dict, touch):
    """帯タッチ系の共通の絞り込み。帯に入った最初のバーだけにする／入口の型で限定する。"""
    m = touch
    if scene.get("fresh_only"):                        # 帯に入った最初のバー＝1バー1発注（実装と同じ）
        prev = np.concatenate([[False], touch[:-1]])
        m = touch & ~prev
    isdn = np.isfinite(x["g"]["res_lo"]) & (x["g"]["res_lo"] > x["c"] * 1.005)   # down 型（天井が遠い下落系）
    if scene.get("flat_up_only"):                      # 現行 L1 と同じ flat_up 型限定（down=落ちるナイフ回避）
        m = m & ~isdn
    if scene.get("down_only"):
        m = m & isdn
    return m


def _sk_pullback_short(scene, x):
    """レンジの中で mid 以上へ戻ったところを売る（戻り幅が床以上）。"""
    return x["base"] & (x["c"] >= x["mid"]) & ((x["c"] - x["mid"]) / x["c"] * 100.0 >= x["floor"])


def _sk_fade_short(scene, x):
    """レンジの上に抜けかけて失敗したところを売る。"""
    return x["base"] & (x["h"] > x["g"]["res_hi"]) & (x["c"] < x["g"]["res_hi"])


def _sk_zscore_short(scene, x):
    """平均から統計的に離れすぎた上側を売る。"""
    if x["g"]["dev_z"] is None:
        raise SystemExit("[場面] dev_z 列が無い（e37._load の指標に依存）")
    return x["base"] & (x["g"]["dev_z"] >= float(scene["z_th"]))


def _sk_crash_rebound_long(scene, x):
    """急落したあとの反発を買う（k_bars 本で drop_pct% 以上下げ ∩ 出来高が平均の vol_mult 倍以上）。"""
    ret = (x["bars"].close / x["bars"].close.shift(int(scene["k_bars"])) - 1) * 100.0
    vol_avg = x["bars"].volume.rolling(20).mean()
    return (x["base"] & (ret.to_numpy() <= -float(scene["drop_pct"]))
            & (x["v"] >= float(scene["vol_mult"]) * vol_avg.to_numpy()))


def _sk_fade_long(scene, x):
    """レンジの下に抜けかけて失敗したところを買う。"""
    return x["base"] & (x["l"] < x["g"]["sup_lo"]) & (x["c"] > x["g"]["sup_lo"])


def _sk_zscore_long(scene, x):
    """平均から統計的に離れすぎた下側を買う。"""
    if x["g"]["dev_z"] is None:
        raise SystemExit("[場面] dev_z 列が無い（e37._load の指標に依存）")
    return x["base"] & (x["g"]["dev_z"] <= -float(scene["z_th"]))


def _sk_support_touch_long(scene, x):
    """レンジの下端の帯に触れたところを買う。
    L1 の入口幾何そのまま（e38_logic_parts support_fresh_touch＝low≤sup_hi ∩ close>sup_lo）。"""
    touch = x["base"] & (x["l"] <= x["g"]["sup_hi"]) & (x["c"] > x["g"]["sup_lo"])
    return _touch_filter(scene, x, touch)


def _sk_resistance_touch_short(scene, x):
    """レンジの上端の帯に触れたところを売る（2026-07-26 まこさん OK で新設）。
    下端タッチの鏡像＝高値が帯の下端以上に届き（触れた）、終値はまだ帯の上端より下（抜け切っていない）。"""
    touch = x["base"] & (x["h"] >= x["g"]["res_lo"]) & (x["c"] < x["g"]["res_hi"])
    return _touch_filter(scene, x, touch)


def _sk_grid_short(scene, x):
    """グリッド売り（2026-07-26 まこさん OK で新設・段3 候補 S5 に対応する型）。
    レンジの内側（下端の帯の上〜上端の帯の下）を grid_n 等分し、その線に下から上へ触れたバー。
    線をまたいだ判定は「前のバーの終値が線より下 ∩ このバーの高値が線以上」＝過去のみ（H2）。"""
    return _grid_touch(scene, x, up=True)


def _sk_grid_long(scene, x):
    """グリッド買い（同上・段3 候補 L5 に対応する型）。線に上から下へ触れたバー。"""
    return _grid_touch(scene, x, up=False)


def _grid_touch(scene, x, up: bool):
    lo_edge, hi_edge = x["g"]["sup_hi"], x["g"]["res_lo"]        # レンジの内側の下端と上端
    n = int(scene["grid_n"])
    if n < 2:
        raise SystemExit(f"[設定] grid_n は2以上（線が引けない）: {n}")
    prev_c = np.concatenate([[np.nan], x["c"][:-1]])             # 前のバーの終値＝過去のみ
    m = np.zeros(len(x["c"]), bool)
    for k in range(1, n):                                        # 内側を n 等分する n-1 本の線
        lv = lo_edge + (hi_edge - lo_edge) * (k / n)
        m |= ((prev_c < lv) & (x["h"] >= lv)) if up else ((prev_c > lv) & (x["l"] <= lv))
    return x["base"] & np.isfinite(prev_c) & m


_SCENE_KINDS = {                      # ★型の正本（順番＝説明書と一覧に出る順）
    "pullback_short": _sk_pullback_short,
    "fade_short": _sk_fade_short,
    "zscore_short": _sk_zscore_short,
    "crash_rebound_long": _sk_crash_rebound_long,
    "fade_long": _sk_fade_long,
    "zscore_long": _sk_zscore_long,
    "support_touch_long": _sk_support_touch_long,
    "resistance_touch_short": _sk_resistance_touch_short,
    "grid_short": _sk_grid_short,
    "grid_long": _sk_grid_long,
}
_SCENE_TYPES = tuple(_SCENE_KINDS)    # 一覧は登録表から作る（手で並べない＝ずれない）


def _scene_mask(scene: dict, bars, g, floor_pct: float):
    """場面バーの抽出（型は登録表 _SCENE_KINDS・パラメータは observe_config.json の scenes）。"""
    t = scene["type"]
    fn = _SCENE_KINDS.get(t)
    if fn is None:
        raise SystemExit(f"[設定] 知らない場面型: {t}（使えるのは {_SCENE_TYPES}）")
    x = _scene_ctx(bars, g, floor_pct)
    return fn(scene, x), x["mid"]


def _scene_labels(sel_idx, bars, g, side: str, lose_w: float, tmax: int, mid,
                  win_target: str = "mid", win_pct: float | None = None):
    """機械ラベル（Triple Barrier 型）。entry＝次バー open（場面はバー確定で判定→建てるのは次のバー）。
    勝ち＝win_target="mid" なら場面バー時点の mid に先着／"pct" なら建値から win_pct%（床×k・
    手数料負けしない幅＝k≥1 を呼び出し側の番人で保証・2026-07-25 まこさん OK）の順行に先着。
    負け＝災害線（SHORT: res_hi+w×レジ帯厚・LONG: sup_lo−w×サポ帯厚）に先着 or 時間切れ。
    同バーで両方に到達した時は 負け優先（保守）。

    ★不利側の測定（2026-07-26 まこさん OK・「観察器が有利側しか測っていない」の是正）:
      勝率だけでは、小さい負けと大きい負けが同じ1件になる（L1ap 勝率62%→実エンジン −$70 の乖離の正体）。
      そこで勝ち負けの判定式は1文字も変えず、下の3つを「追加で」返す（既存の wins/oks は不変）:
        res_pct  決着時の損益幅%（符号つき）＝勝ち:+勝ち幅／災害線:−災害線までの幅／時間切れ:終値までの実現幅
        mae_pct  保有中の最大逆行幅%（0以上・勝ち玉がどこまで踏まれたかも見える）
        kinds    決着の種類（勝ち／災害線／時間切れ）＝負けの中身を2つに分ける
      これで 概算の期待値（平均 res_pct − 手数料床）が出せる＝有利側だけの表示に戻れなくする。"""
    hi, lo = bars.high.to_numpy(), bars.low.to_numpy()
    op, cl = bars.open.to_numpy(), bars.close.to_numpy()
    n = len(bars)
    res_hi, res_lo = g["res_hi"], g["res_lo"]
    sup_lo, sup_hi = g["sup_lo"], g["sup_hi"]
    wins, oks, res_pct, mae_pct, kinds = [], [], [], [], []
    for i in sel_idx:
        entry_i = i + 1                       # 次バー open で建てる（同バー約定＝未来参照を避ける）
        if entry_i >= n:
            wins.append(False); oks.append(False)
            res_pct.append(np.nan); mae_pct.append(np.nan); kinds.append(""); continue
        ep = op[entry_i]
        if win_target == "pct":               # 浅い戻り＝スキャル幾何（実装の浅TP型と同じ）
            wt = ep * (1 - win_pct / 100.0) if side == "SHORT" else ep * (1 + win_pct / 100.0)
        else:
            wt = mid[i]
        lb = (res_hi[i] + lose_w * (res_hi[i] - res_lo[i]) if side == "SHORT"
              else sup_lo[i] - lose_w * (sup_hi[i] - sup_lo[i]))
        end = min(i + int(tmax), n - 1)
        win = False
        kind, worst, j_end = "時間切れ", 0.0, end
        for j in range(entry_i, end + 1):
            # 不利側の最大到達（SHORT は上ヒゲ・LONG は下ヒゲ）＝順行と対で持つ（片側だけを出さない）
            adv = ((hi[j] - ep) if side == "SHORT" else (ep - lo[j])) / ep * 100.0
            if adv > worst:
                worst = adv
            lose_hit = (hi[j] >= lb) if side == "SHORT" else (lo[j] <= lb)
            win_hit = (lo[j] <= wt) if side == "SHORT" else (hi[j] >= wt)
            if lose_hit:                      # 同バー両到達は 負け優先（保守）
                win = False; kind = "災害線"; j_end = j; break
            if win_hit:
                win = True; kind = "勝ち"; j_end = j; break
        px = wt if kind == "勝ち" else (lb if kind == "災害線" else cl[j_end])
        r = ((ep - px) if side == "SHORT" else (px - ep)) / ep * 100.0
        wins.append(win); oks.append(True)    # 時間切れ＝負け（取れなかった＝機会として失敗）
        res_pct.append(r); mae_pct.append(max(worst, 0.0)); kinds.append(kind)
    return (np.asarray(wins, bool), np.asarray(oks, bool), np.asarray(res_pct, float),
            np.asarray(mae_pct, float), np.asarray(kinds, object))


def _scene_exit_grid(scene: dict, cfg: dict):
    """出口の組み合わせの刻み（まこさん確定 2026-07-26・粗い版）。
    場面の定義に同名キーがあればそれを使い、無ければ config の共通値を使う（まこさん OK＝場面ごとに上書き可）。
    段4/段5 で細かく刻みたい時は、その場面の定義に細かい配列を書くだけでよい（コードは触らない）。

    返す3つ: 利確の候補／損切りの候補／保有の上限（5分足の本数）。
      利確  = "mid"（レンジ中央に先着＝従来の形）＋ 建値からの順行%（複数）
      損切り = "zone"（災害線に先着＝従来の形）＋ 建値からの逆行%（複数）"""
    def _pick(key):
        v = scene.get(key, cfg.get(key))
        if v is None:
            raise SystemExit(f"[設定] {key} が config にも場面定義にも無い（出口の組み合わせを作れない）")
        return list(v)
    tps = ["mid"] + [float(x) for x in _pick("scene_exit_tp_pcts")]
    sls = ["zone"] + [float(x) for x in _pick("scene_exit_sl_pcts")]
    tmaxs = [int(x) for x in _pick("scene_exit_tmax_bars")]
    if len(tps) * len(sls) * len(tmaxs) < 2:
        raise SystemExit("[設定] 出口の組み合わせが1通りしかない（比べる意味がない＝探索を消した状態）")
    return tps, sls, tmaxs


def _scene_exit_scan(sel_idx, bars, g, side: str, lose_w: float, mid, tps, sls, tmax_max: int):
    """出口の組み合わせを1回のバー走査で全部測る（組み合わせの数だけ辿り直さない）。

    やっていること＝場面バーの次バー open で建て、tmax_max 本先まで1回だけ辿りながら
      ・レンジ中央／災害線／各 利確%／各 損切り% に「何本目で最初に着いたか」
      ・各本数で決済したときの実現幅%と、そこまでの最大逆行%
    を記録する。組み合わせ (利確, 損切り, 保有の上限) の勝ち負けは、この記録から後で引ける
    ＝走査は1回で足りる（利確10×損切り14×上限6 でも走査は増えない）。

    返す dict の中身（全部 玉数 n の配列・届かなければ tmax_max+1 を入れる＝「期間内に着かなかった」）:
      ok        建てられたか（最終バーで次バーが無い玉は False）
      t_mid     レンジ中央に先着した本数 ／ gain_mid  その時の実現幅%
      t_zone    災害線に先着した本数     ／ loss_zone その時の実現幅%（負の値）
      t_tp      (n, 利確の数) 先着本数   ／ t_sl (n, 損切りの数) 先着本数
      res_at    (n, tmax_max) その本数で決済したときの実現幅%
      mae_at    (n, tmax_max) そこまでの最大逆行%"""
    hi, lo = bars.high.to_numpy(), bars.low.to_numpy()
    op, cl = bars.open.to_numpy(), bars.close.to_numpy()
    n_all = len(bars)
    res_hi, res_lo = g["res_hi"], g["res_lo"]
    sup_lo, sup_hi = g["sup_lo"], g["sup_hi"]
    tp_pcts = [x for x in tps if x != "mid"]
    sl_pcts = [x for x in sls if x != "zone"]
    n = len(sel_idx)
    NEVER = tmax_max + 1                      # 「期間内に着かなかった」を表す本数
    out = {
        "ok": np.zeros(n, bool),
        "t_mid": np.full(n, NEVER, int), "gain_mid": np.full(n, np.nan),
        "t_zone": np.full(n, NEVER, int), "loss_zone": np.full(n, np.nan),
        "t_tp": np.full((n, len(tp_pcts)), NEVER, int),
        "t_sl": np.full((n, len(sl_pcts)), NEVER, int),
        "res_at": np.full((n, tmax_max), np.nan),
        "mae_at": np.full((n, tmax_max), np.nan),
        "tp_pcts": tp_pcts, "sl_pcts": sl_pcts, "NEVER": NEVER,
    }
    for r, i in enumerate(sel_idx):
        entry_i = i + 1                       # 次バー open で建てる（同バー約定＝未来参照を避ける・H2）
        if entry_i >= n_all:
            continue
        ep = op[entry_i]
        wt = mid[i]
        lb = (res_hi[i] + lose_w * (res_hi[i] - res_lo[i]) if side == "SHORT"
              else sup_lo[i] - lose_w * (sup_hi[i] - sup_lo[i]))
        out["ok"][r] = True
        out["gain_mid"][r] = ((ep - wt) if side == "SHORT" else (wt - ep)) / ep * 100.0
        out["loss_zone"][r] = ((ep - lb) if side == "SHORT" else (lb - ep)) / ep * 100.0
        worst = 0.0
        for t in range(tmax_max):             # t=0 が建てたバー（次バー）＝保有1本
            j = entry_i + t
            if j >= n_all:
                break
            fav = ((ep - lo[j]) if side == "SHORT" else (hi[j] - ep)) / ep * 100.0   # 順行の最大到達
            adv = ((hi[j] - ep) if side == "SHORT" else (ep - lo[j])) / ep * 100.0   # 逆行の最大到達
            worst = max(worst, adv)
            out["res_at"][r, t] = ((ep - cl[j]) if side == "SHORT" else (cl[j] - ep)) / ep * 100.0
            out["mae_at"][r, t] = max(worst, 0.0)
            if out["t_mid"][r] == NEVER and ((lo[j] <= wt) if side == "SHORT" else (hi[j] >= wt)):
                out["t_mid"][r] = t
            if out["t_zone"][r] == NEVER and ((hi[j] >= lb) if side == "SHORT" else (lo[j] <= lb)):
                out["t_zone"][r] = t
            for k, p in enumerate(tp_pcts):
                if out["t_tp"][r, k] == NEVER and fav >= p:
                    out["t_tp"][r, k] = t
            for k, p in enumerate(sl_pcts):
                if out["t_sl"][r, k] == NEVER and adv >= p:
                    out["t_sl"][r, k] = t
    return out


def _scene_exit_eval(sc, tp, sl, tmax: int):
    """走査の記録から、1つの組み合わせ (利確, 損切り, 保有の上限) の勝ち負けと決着幅%を引く。
    同じ本数で両方に着いたときは 負け優先（保守・_scene_labels と同じ扱い）。
    保有の上限に着く前にどちらにも着かなければ 時間切れ＝負け扱い（取れなかった機会）。"""
    NEVER = sc["NEVER"]
    t_win = sc["t_mid"] if tp == "mid" else sc["t_tp"][:, sc["tp_pcts"].index(tp)]
    t_los = sc["t_zone"] if sl == "zone" else sc["t_sl"][:, sc["sl_pcts"].index(sl)]
    gain = sc["gain_mid"] if tp == "mid" else np.full(len(t_win), float(tp))
    loss = sc["loss_zone"] if sl == "zone" else np.full(len(t_los), -float(sl))
    last = min(int(tmax), sc["res_at"].shape[1]) - 1
    res_to = sc["res_at"][:, last]
    win = (t_win <= last) & (t_win < t_los)                      # 利確が先＝勝ち（同着は負け優先）
    los = (t_los <= last) & (t_los <= t_win)                     # 損切りが先 or 同着＝負け
    res = np.where(win, gain, np.where(los, loss, res_to))       # どちらも無ければ時間切れの実現幅
    return win, res


def _cond_mask(sdf, conds):
    """フェーズ3 で残った入口の条件を、そのままの実値でマスクに戻す（表示用の丸めた文字列から復元しない）。"""
    m = np.ones(len(sdf), bool)
    for col, _q, hi_side, th in conds:
        v = pd.to_numeric(sdf[col], errors="coerce").to_numpy(float)
        m &= np.isfinite(v) & ((v >= th) if hi_side else (v <= th))
    return m


def _scene_exit_rows(sc, keep, first, second, days1, days2, floor, tps, sls, tmaxs, cfg):
    """出口の組み合わせを全部評価して1行ずつの表にする。順位づけは概算期待値（勝率では並べない）。
    keep＝入口の条件で残した玉のマスク（条件なしのときは全部 True）。"""
    rows = []
    for tp in tps:
        for sl in sls:
            for tmax in tmaxs:
                win, res = _scene_exit_eval(sc, tp, sl, tmax)
                m = keep & sc["ok"]
                m1, m2 = m & first, m & second
                if int(m.sum()) < int(cfg["min_n"]):
                    continue
                rows.append({
                    "利確": ("レンジ中央" if tp == "mid" else f"{tp}%"),
                    "損切り": ("災害線" if sl == "zone" else f"{sl}%"),
                    "保有上限分": int(tmax) * 5,
                    "件数": int(m.sum()),
                    "件数/日": round(float(m.sum()) / max(days1 + days2, 1), 2),
                    "勝率%": round(float(win[m].mean() * 100), 1),
                    "平均決着幅%": round(float(np.nanmean(res[m])), 3),
                    "期待値%": round(float(np.nanmean(res[m]) - floor), 3),
                    "前半_期待値%": round(float(np.nanmean(res[m1]) - floor), 3) if int(m1.sum()) else np.nan,
                    "後半_期待値%": round(float(np.nanmean(res[m2]) - floor), 3) if int(m2.sum()) else np.nan,
                })
    df = pd.DataFrame(rows)
    return df.sort_values("期待値%", ascending=False).reset_index(drop=True) if len(df) else df


def _conf_search(sdf, feat_cols, cfg, first, second, base1, base2, d1, d2, floor):
    """異種カテゴリ AND のコンフルエンス探索。閾値は前半の分布で実値化（_th_first）→後半は同じ実値で確認。
    評価＝勝率の持ち上げ（pt）を最大化・成立バー/日 conf_min_bars_per_day 未満はゲートで棄却（金額なし）。

    ★不利側の併記（2026-07-26 まこさん OK）＝各組に概算期待値%（平均 決着幅 − 手数料床）を必ず並べる。
      勝率が上がっても負けの幅が広がって期待値がマイナスの組を、表を見て弾けるようにする。
      探索の目的関数は勝率のまま（変更は別途まこさん判断）＝ここは表示の追加。"""
    try:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
    except Exception as e:
        _skip(f"optuna が使えない: {e}"); return [], []
    from itertools import combinations
    cats: dict[str, list] = {}
    for c in feat_cols:
        cats.setdefault(_category(c), []).append(c)
    combos = ["+".join(x) for r in range(int(cfg["conf_and_min"]), int(cfg["conf_and_max"]) + 1)
              for x in combinations(sorted(cats), r)]
    if not combos:
        _skip("カテゴリが足りない"); return [], []
    win = sdf["win"].to_numpy(bool)
    resv = pd.to_numeric(sdf["res_pct"], errors="coerce").to_numpy(float)   # 決着幅%（不利側込み）
    ev = {c: pd.to_numeric(sdf[c], errors="coerce").to_numpy(float) for c in feat_cols}
    min_day = float(cfg["conf_min_bars_per_day"])

    def _th_first(col, q, hi_side):
        v = ev[col][first]
        v = v[np.isfinite(v)]
        return float(np.quantile(v, q if hi_side else round(1.0 - q, 4))) if len(v) else np.nan

    def _mask(conds):
        m = np.ones(len(sdf), bool)
        for col, _q, hi_side, th in conds:
            v = ev[col]
            m &= np.isfinite(v) & ((v >= th) if hi_side else (v <= th))
        return m

    def _eval(conds, half, days):
        m = _mask(conds) & half
        n = int(m.sum())
        wr = float(win[m].mean() * 100) if n else np.nan
        evp = float(np.nanmean(resv[m]) - floor) if n else np.nan   # 概算期待値%＝不利側込み
        return wr, n, n / max(days, 1), evp

    def _conds_of(params):
        conds, tfs = [], set()
        for cat in params["cats"].split("+"):
            col = cats[cat][params[f"col_{cat}"]]
            th = _th_first(col, params[f"q_{cat}"], params[f"hi_{cat}"])
            conds.append((col, params[f"q_{cat}"], params[f"hi_{cat}"], th))
            tfs.add(col.split("__")[1] if "__" in col else "外部")
        return conds, tfs

    def objective(t):
        combo = t.suggest_categorical("cats", combos)
        for cat in combo.split("+"):
            t.suggest_int(f"col_{cat}", 0, len(cats[cat]) - 1)
            t.suggest_categorical(f"q_{cat}", cfg["quantiles"])
            t.suggest_categorical(f"hi_{cat}", [True, False])
        conds, tfs = _conds_of(t.params)
        if any(not np.isfinite(th) for *_x, th in conds):
            return -1e9
        if len(tfs) < 2:
            return -1e9                       # 時間足2種以上を強制（MTF コンフルエンス）
        wr, _n, per_day, _evp = _eval(conds, first, d1)
        if per_day < min_day or not np.isfinite(wr):
            return -1e9                       # 件数下限＝conf_min_bars_per_day（勝率だけ最大化の逃げ禁止）
        return wr - base1
    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
    st.optimize(objective, n_trials=int(cfg["conf_trials"]), show_progress_bar=False)
    rows, raw, seen = [], [], set()
    for tr_ in sorted(st.trials, key=lambda z: -(z.value if z.value is not None else -1e9)):
        if tr_.value is None or tr_.value <= -1e8:
            continue
        try:
            conds, _tfs = _conds_of(tr_.params)
        except Exception:
            continue
        key = tuple((c, q, h) for c, q, h, _ in conds)
        if key in seen:
            continue
        seen.add(key)
        w1, _n1, pd1_, ev1 = _eval(conds, first, d1)
        w2, _n2, pd2_, ev2 = _eval(conds, second, d2)
        rows.append({"条件の組": " AND ".join(
            f"{c} {'≥' if h else '≤'}q{int(q * 100) if h else int(round((1 - q) * 100))}[{th:.4g}]"
            for c, q, h, th in conds),
            "前半_勝率%": round(w1, 1), "前半_期待値%": round(ev1, 3), "前半_バー/日": round(pd1_, 1),
            "後半_勝率%": round(w2, 1), "後半_期待値%": round(ev2, 3), "後半_バー/日": round(pd2_, 1)})
        raw.append(list(conds))    # フェーズ4 が同じ条件でマスクを作り直すための生の条件（表示は上の文字列）
        if len(rows) >= 10:
            break
    return rows, raw


def _scene_header(scene_id, scene, cfg, floor, p0, p1, planning: bool):
    print("#" * 100)
    print(f"# Entry 候補観察 {'検証計画（自動生成・本走しない）' if planning else '本走'}  場面 {scene_id}")
    print(f"# 期間: {p0.date()} 〜 {p1.date()}（採点窓の範囲内のみ・periods.py）／ 指標の暖機 {cfg['warmup_days']} 日")
    print(f"# 場面定義: type={scene['type']} / side={scene['side']} / パラメータ={ {k: v for k, v in scene.items() if k not in ('type', 'side')} }")
    print(f"# 戻り幅の床: {floor:.3f}%（{'config 指定' if cfg.get('scene_floor_pct') is not None else 'e37_scalp.SCALP_FLOOR から解決'}）")
    if scene.get("win_target", "mid") == "pct":
        k = float(scene.get("win_pct_k", 0))
        print(f"# 機械ラベル: entry=場面バーの次バー open ／ 勝ち=建値から {k:.1f}×床＝{k * floor:.3f}% の順行に先着"
              f"（浅い戻り＝スキャル幾何・maker往復 0.028% の約{k * floor / 0.028:.0f}倍＝手数料負けしない幅）／")
    else:
        print("# 機械ラベル: entry=場面バーの次バー open ／ 勝ち=場面バー時点の mid に先着 ／")
    print("#            負け=災害線（SHORT: res_hi+w×レジ帯厚・LONG: sup_lo−w×サポ帯厚）に先着 or 時間切れ（負け扱い）")
    print("#            同バー両到達は負け優先（保守）。レンジ幾何は e37 の計器（RG-v5＋V25_K）を import 再利用。")
    print(f"# コンフルエンス探索: AND {cfg['conf_and_min']}〜{cfg['conf_and_max']} 条件・異種カテゴリのみ・時間足2種以上・"
          f"件数下限 {cfg['conf_min_bars_per_day']} バー/日・試行 {cfg['conf_trials']}")
    print(f"# 閾値の候補（分位）: {cfg['quantiles']}（上下側・実値化は前半の分布のみ＝後半で選び直さない）")
    print(f"# 設定ファイル: {cfg['_source']}（場面・バリア・探索条件はここを編集して再生成）")
    print("# ⚠️ 疑似シミュ＝スロット・手数料・約定を含まない。出た組は材料まで＝値決めは層3・採否は採点窓 score.py。")
    print("#" * 100)


def plan_scene(scene_id: str, config_path: str | None = None) -> None:
    """Entry 候補観察の検証計画（自動生成）＝場面の定義・母集団の件数・探索条件を実値から印字して
    まこさんに提出する1枚。ラベル付け・分離力・探索は本走でだけ回す（計画に観察結果を混ぜない）。"""
    cfg = load_config(config_path)
    scene = (cfg.get("scenes") or {}).get(scene_id)
    if not scene:
        raise SystemExit(f"[設定] scenes に {scene_id} が無い（observe_config.json・定義済み {list((cfg.get('scenes') or {}))}）")
    floor = _scene_floor(cfg)
    bars, g, w, p0, p1 = _scene_data(cfg)
    mask_all, _mid = _scene_mask(scene, bars, g, floor)
    sel = np.where(mask_all & w)[0]
    days = max((p1 - p0).days + 1, 1)
    _scene_header(scene_id, scene, cfg, floor, p0, p1, planning=True)
    print(f"# 1往復の実コスト: {round_trip_cost()[1]}")
    times = bars.index[sel]
    half_t = times[len(times) // 2] if len(times) else None
    print(f"\n  場面バー: {len(sel)} バー（{len(sel) / days:.1f} バー/日）")
    if half_t is not None:
        n1 = int((times <= half_t).sum())
        print(f"  探索の分割: 前半 {p0.date()}〜{half_t.date()} {n1} バー＝探索 ／ 後半 〜{p1.date()} {len(sel) - n1} バー＝同じ実値で確認（L-267）")
    cat = build_catalog(cfg)
    names_all = [n for n, _f, _d in cat]
    print(f"\n  ── 観察に当てる指標カタログ（全 {len(cat)} 種 × 足 {cfg['timeframes']} = {len(cat) * len(cfg['timeframes'])} 列 ＋ 需給 {list(_DEMAND_FILES)}・減らせない）──")
    for i in range(0, len(names_all), 5):
        print("     " + " | ".join(names_all[i:i + 5]))
    bycat: dict[str, int] = {}
    for tf in cfg["timeframes"]:
        for nme in names_all:
            bycat[_category(f"{nme}__{tf}")] = bycat.get(_category(f"{nme}__{tf}"), 0) + 1
    print(f"\n  ── 部品のカテゴリ内訳（1つの組は別カテゴリから選ぶ＝同族の二度掛け禁止）──")
    for k, v in sorted(bycat.items()):
        print(f"     {k}: {v} 列")
    print("\n  ── 出す節（固定・減らせない）──")
    for sct in SECTIONS_SCENE:
        print(f"     {sct}")
    print("\n  ⚠️ この計画の外は検証しない。場面・バリア・探索条件を変えるのは observe_config.json を編集して計画を再生成してから。")
    print("  ⚠️ まこさんの OK が出たら本走する。本走の先頭に同じ設定が印字される＝計画との差分は突き合わせで見える。")


def observe_scene(scene_id: str, config_path: str | None = None) -> None:
    cfg = load_config(config_path)
    scene = (cfg.get("scenes") or {}).get(scene_id)
    if not scene:
        raise SystemExit(f"[設定] scenes に {scene_id} が無い（observe_config.json）")
    floor_cond = _scene_floor(cfg)            # 場面の条件に使う戻り幅の下限（手数料ではない）
    floor, cost_note = round_trip_cost()       # 概算期待値から引く1往復の実コスト
    bars, g, w, p0, p1 = _scene_data(cfg)
    mask_all, mid = _scene_mask(scene, bars, g, floor_cond)
    sel = np.where(mask_all & w)[0]
    days = max((p1 - p0).days + 1, 1)
    _scene_header(scene_id, scene, cfg, floor_cond, p0, p1, planning=False)
    print(f"# 1往復の実コスト: {cost_note}")
    if len(sel) < cfg["min_n"]:
        raise SystemExit(f"[場面] 場面バーが {len(sel)} 行（min_n {cfg['min_n']} 未満＝観察しない）")

    print("\n[指標を計算中...]", flush=True)
    feat, meta = build_features(bars, cfg)
    dem, cov = load_demand(bars.index)
    feat = pd.concat([feat, dem], axis=1)
    ng = [k for k, v in meta.items() if v[0] != "ok"]
    print(f"  指標 {feat.shape[1]} 列を用意（計算できず {len(ng)} 列）")
    print("  需給データの被覆:")
    for k, v in cov.items():
        print(f"     {k}: {v}")

    win_target = scene.get("win_target", "mid")
    win_pct = None
    if win_target == "pct":
        k = float(scene.get("win_pct_k", 0))
        if k < 1.0:                            # 床割れの勝ち定義＝手数料負けの動きを「勝ち」と数える設計を物理禁止
            raise SystemExit(f"[設定] win_pct_k が 1.0 未満: {k}（勝ちの幅は床×1以上＝手数料負けしない幅）")
        win_pct = k * floor_cond
    wins, oks, res_pct, mae_pct, kinds = _scene_labels(
        sel, bars, g, scene["side"], float(scene["lose_barrier_w"]),
        int(scene["tmax_bars"]), mid, win_target, win_pct)
    sel, wins = sel[oks], wins[oks]
    res_pct, mae_pct, kinds = res_pct[oks], mae_pct[oks], kinds[oks]
    times = bars.index[sel]
    sdf = feat.reindex(times).copy()   # 場面バーの確定値（entry は次バー open＝当バー確定値は因果 OK・H2）
    sdf["win"] = wins
    sdf["res_pct"] = res_pct           # 決着時の損益幅%（符号つき）＝節2/節3 の概算期待値の材料（不利側を必ず併記）
    sdf.reset_index(drop=True, inplace=True)
    half_t = times[len(times) // 2]
    first = np.asarray(times <= half_t)
    second = ~first
    d1 = max((half_t - times.min()).days + 1, 1)
    d2 = max((times.max() - half_t).days + 1, 1)
    base_all = float(wins.mean() * 100)
    base1 = float(wins[first].mean() * 100) if first.any() else np.nan
    base2 = float(wins[second].mean() * 100) if second.any() else np.nan

    _h(SECTIONS_SCENE[0])
    print(f"  場面バー {len(sel)}（{len(sel) / days:.1f} バー/日）／ 素の勝率 {base_all:.1f}%")
    print(f"  前半 {times.min().date()}〜{half_t.date()}: {int(first.sum())} バー・素の勝率 {base1:.1f}%")
    print(f"  後半 〜{times.max().date()}: {int(second.sum())} バー・素の勝率 {base2:.1f}%")
    # 型内訳（down=下落系レンジ / flat_up=平坦上昇系・実装と同じ gap 0.5% 判定・型を混ぜた場面でも内訳が見える）
    isdn_all = np.isfinite(g["res_lo"]) & (g["res_lo"] > bars.close.to_numpy() * 1.005)
    isdn_sel = isdn_all[sel]
    for ty, msk in [("down", isdn_sel), ("flat_up", ~isdn_sel)]:
        n_ty = int(msk.sum())
        wr_ty = float(wins[msk].mean() * 100) if n_ty else float("nan")
        ev_ty = float(np.nanmean(res_pct[msk]) - floor) if n_ty else float("nan")
        print(f"  型内訳 {ty}: {n_ty} バー（{n_ty / days:.1f} バー/日）・素の勝率 {wr_ty:.1f}%"
              f"・概算期待値 {ev_ty:+.3f}%/件")
    print("  ＝素で五分なら確認条件が必須という判定材料。時間切れは負け扱い（取れなかった機会）。")

    # ★不利側（2026-07-26 まこさん OK）＝勝率だけを出すのを止める。
    #   背景＝観察の勝率62%が実エンジンで −$70 になった乖離の正体は「有利側しか測っていない」こと。
    #   小さい負けと大きい負けが勝率では同じ1件になるので、負けの中身と概算期待値を必ず併記する。
    print("\n  ── 不利側（勝率だけでは見えない負けの中身・有利側と必ず対で出す）")
    w_m = wins.astype(bool)
    for nm, m in [("勝ち", w_m), ("負け", ~w_m)]:
        if int(m.sum()):
            print(f"  {nm}  {int(m.sum())}件（{m.mean()*100:.1f}%）・平均 決着幅 {np.nanmean(res_pct[m]):+.3f}%")
    for kd in ("災害線", "時間切れ"):
        m = (kinds == kd)
        if int(m.sum()):
            print(f"    └ 負けの内訳 {kd}: {int(m.sum())}件・平均 決着幅 {np.nanmean(res_pct[m]):+.3f}%"
                  f"・最大逆行 中央 {np.nanmedian(mae_pct[m]):.3f}%")
    print(f"  保有中の最大逆行%: 全体 中央 {np.nanmedian(mae_pct):.3f} / q75 {np.nanquantile(mae_pct, .75):.3f}"
          f" / q90 {np.nanquantile(mae_pct, .90):.3f}"
          + (f" ／ 勝ち玉 中央 {np.nanmedian(mae_pct[w_m]):.3f}" if int(w_m.sum()) else "")
          + (f" ／ 負け玉 中央 {np.nanmedian(mae_pct[~w_m]):.3f}" if int((~w_m).sum()) else ""))
    ev_all = float(np.nanmean(res_pct)) - floor
    print(f"  概算の期待値 ＝ 平均 決着幅 {np.nanmean(res_pct):+.3f}% − 手数料床 {floor:.3f}% "
          f"＝ {ev_all:+.3f}%/件")
    print("  ⚠️ 概算です。スロットの取り合い・約定の不確実・funding は含みません。"
          "勝率が高くても期待値がマイナスなら候補にしない。実力は層3 の実エンジン・採否は採点窓 score.py。")

    _h(SECTIONS_SCENE[1])
    fcols = [c for c in feat.columns if sdf[c].notna().sum() >= max(int(len(sdf) * 0.5), cfg["min_n"])]
    # ★独立な標本だけで測る（2026-08-22・まこさん指示「今直してほしい」）。
    #   直す前は、上位足の列を5分足の並びに引き伸ばしたまま1行ずつ数えていた＝同じ値を重複して数え、
    #   分離力が実力より離れて出る（M2-3-3 の1回目の本走で実際に踏んだ・worklog 20260822 の §6）。
    r = rank_separation_independent(sdf, sdf["win"].astype(bool), fcols, times,
                                    TAUTOLOGY_COLS, top=20)
    print(r.to_string(index=False) if len(r) else "     分離する特徴なし")
    print("  ＝1個ずつの材料。ここでは決めない（前回の1軸検索の失敗を繰り返さない）。")
    print("  ★標本数＝その列の時間足のバー1本につき1行だけ残して数えた個数"
          "（上位足の値を重複して数えない・2026-08-22 に直した）。")

    _h(SECTIONS_SCENE[2])
    rows, conds_raw = _conf_search(sdf, fcols, cfg, first, second, base1, base2, d1, d2, floor)
    df_rows = pd.DataFrame(rows)
    if len(df_rows):
        print("  前半で探索した上位10（重複除去後・後半は同じ実値をそのまま当てた確認）")
        print(f"  素の勝率: 前半 {base1:.1f}% / 後半 {base2:.1f}%"
              f" ／ 素の概算期待値: 前半 {float(np.nanmean(res_pct[first])) - floor:+.3f}%"
              f" / 後半 {float(np.nanmean(res_pct[second])) - floor:+.3f}%")
        print(df_rows.to_string(index=False))
    else:
        _skip("候補が1件も残らなかった")

    _h(SECTIONS_SCENE[3])
    if len(df_rows):
        both = df_rows[(df_rows["前半_勝率%"] > base1) & (df_rows["後半_勝率%"] > base2)]
        if len(both):
            print(f"  両半期で素の勝率超え: {len(both)} 組")
            print(both.to_string(index=False))
        else:
            print("  両半期で素の勝率超え 0 組 ＝ 前半に合わせただけの疑い（候補にしない）")
        # ★不利側の合格（2026-07-26 まこさん OK）＝勝率で選んだ組が、期待値でも生き残るかを別に出す。
        #   勝率が上がっても負けの幅が広がれば期待値はマイナスになる（観察と実エンジンの乖離の正体）。
        ev_ok = both[(both["前半_期待値%"] > 0) & (both["後半_期待値%"] > 0)] if len(both) else both
        print(f"  └ そのうち 両半期とも 概算期待値がプラス: {len(ev_ok)} 組"
              " ＝ここが層3 に渡す候補（勝率だけで渡さない）")
        if len(ev_ok):
            print(ev_ok.to_string(index=False))
    else:
        print("  候補 0 組")

    # ★フェーズ4＝出口の組み合わせ（まこさん OK 2026-07-26）。
    #   背景＝ここまでのフェーズは出口を1組に固定したまま入口だけを見ていた＝入口の順位が出口の仮定に
    #   引きずられる（Entry と Exit はセットで net が決まる・L-285）。刻みはまこさん確定の粗い版。
    _h(SECTIONS_SCENE[4])
    tps, sls, tmaxs = _scene_exit_grid(scene, cfg)
    print(f"  振る軸: 利確 {['レンジ中央' if t == 'mid' else f'{t}%' for t in tps]}"
          f" × 損切り {['災害線' if s == 'zone' else f'{s}%' for s in sls]}"
          f" × 保有の上限 {[t * 5 for t in tmaxs]} 分"
          f" ＝ {len(tps) * len(sls) * len(tmaxs)} 通り")
    print("  ＝走査は1回だけ（組み合わせの数だけ辿り直さない）。順位づけは概算期待値（勝率では並べない）。")
    sc = _scene_exit_scan(sel, bars, g, scene["side"], float(scene["lose_barrier_w"]),
                          mid, tps, sls, max(tmaxs))
    all_keep = np.ones(len(sel), bool)
    tbl = _scene_exit_rows(sc, all_keep, first, second, d1, d2, floor, tps, sls, tmaxs, cfg)
    if len(tbl):
        print("\n  ── 入口の条件なし（場面バー全部）＝出口だけの効き・期待値の上位10 ──")
        print(tbl.head(10).to_string(index=False))
        both_ex = tbl[(tbl["前半_期待値%"] > 0) & (tbl["後半_期待値%"] > 0)]
        print(f"\n  └ 両半期とも 概算期待値がプラス: {len(both_ex)} 通り ＝ここが層3 に渡す出口の候補")
        if len(both_ex):
            print(both_ex.to_string(index=False))
    else:
        _skip("出口の組み合わせが1通りも min_n を満たさなかった")

    # 入口の条件とセットで見る（フェーズ3 で両半期プラスが残った時だけ・上位3条件まで）
    if len(df_rows) and len(ev_ok):
        print("\n  ── 入口の条件 × 出口（フェーズ3 で残った条件の上位3・各条件の出口 上位3）──")
        for idx, cond in ev_ok.head(3).iterrows():
            keep = _cond_mask(sdf, conds_raw[idx])
            t2 = _scene_exit_rows(sc, keep, first, second, d1, d2, floor, tps, sls, tmaxs, cfg)
            print(f"\n  条件: {cond['条件の組']}（該当 {int(keep.sum())} 件）")
            print(t2.head(3).to_string(index=False) if len(t2) else "     min_n 未満で出せない")
    print("\n  ⚠️ 疑似シミュの機械集計＝候補の材料まで。値決めは層3 engine_tuner・採否は採点窓 score.py（まこさん）。")


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


# ══ 節10 判定（2026-07-26 まこさん OK）═══════════════════════════════════
#   まこさんの要望＝「別の戦略でも別の条件でも、observe_diag で検証したら分析結果まで自動で出る状態にしたい。
#   CC が手で書く判定を挟まない」。今まで observe_diag が出すのは材料だけで、「で、この結果はどうなのか」は
#   CC が毎回チャットに手書きしていた＝毎回ぶれる（まこさん指摘 2026-07-25 の分析自動化）。
#
#   ★戦略名を一切見ない＝汎用の根拠: 使うのは売買記録の共通9列だけ（side / ceil_type / exit_reason /
#     hold_min / gross_usd / fee_usd / net_usd / mfe_usd / mae_usd）。この9列は全戦略が共通の記録処理
#     （e37_scalp._record）で出しているので、E35/E36/E37/E38 でも今後の新戦略でも同じ節がそのまま出る。
#     欠けている列があれば、その行だけ飛ばして残りを出す（戦略ごとに分岐を書かない）。
#
#   ★金額について（道具の原則との関係を明示）: 節8/節9 と --scene は疑似シミュ＝今までどおり金額を出さない。
#     本節が出す金額は「実エンジンが売買記録に記録した実額」＝report.py が読むのと同じ列。疑似シミュではない。
#     采否は従来どおり score.py の採点窓でまこさんが決める（本節は採否をしない・出血箇所を指すだけ）。
_HOLD_BANDS = ((0, 15), (15, 30), (30, 60), (60, 120), (120, 240), (240, 10 ** 9))


def _hold_band(m) -> str:
    """保有時間の帯。表示のための区切りで、戦略のパラメータではない（値を設計に焼かない）。"""
    try:
        m = float(m)
    except (TypeError, ValueError):
        return "不明"
    for lo, hi in _HOLD_BANDS:
        if lo <= m < hi:
            return f"{lo}-{hi}分" if hi < 10 ** 9 else f"{lo}分超"
    return "不明"


def verdict(tr: pd.DataFrame) -> dict:
    """節10。①稼げているか ②有利側と不利側 ③どこで血が出ているか ④残せる部分 ⑤巻き込み を機械で出す。
    戻り値＝既知答えテスト用の集計値（画面出力と同じ数字）。"""
    out: dict = {}
    if not len(tr):
        print("  売買記録が0行＝判定できない"); return out
    t = tr.copy()
    n = len(t)
    net = float(t["net_usd"].sum())
    out["n"], out["net"], out["per"] = n, net, net / n

    print("  ① 稼げているか")
    print(f"     全体 {n}件 ／ 純益 ${net:+,.2f} ／ 1件あたり ${net / n:+.3f}")
    if {"gross_usd", "fee_usd"} <= set(t.columns):
        gr, fe = float(t["gross_usd"].sum()), float(t["fee_usd"].sum())
        print(f"     1件あたりの内訳 粗利 ${gr / n:+.3f} − 手数料 ${fe / n:.3f} ＝ 純益 ${(gr - fe) / n:+.3f}")
        if gr > 0:
            print(f"     ＝手数料が粗利の {fe / gr * 100:.0f}% を食っている"
                  f"（この割合が高いほど、値幅でなくコストで負けている）")
        else:
            print("     ＝粗利がゼロ以下＝値幅そのものが取れていない（コストの問題より前の段階）")

    print("  ② 有利側と不利側")
    w, l = t[t["net_usd"] > 0], t[t["net_usd"] <= 0]
    if len(w):
        print(f"     勝ち {len(w)}件（{len(w) / n * 100:.1f}%）・平均 ${w['net_usd'].mean():+.3f}")
    if len(l):
        print(f"     負け {len(l)}件（{len(l) / n * 100:.1f}%）・平均 ${l['net_usd'].mean():+.3f}")
    if {"mfe_usd", "mae_usd"} <= set(t.columns):
        print(f"     保有中の最大含み益 中央 ${t['mfe_usd'].median():+.3f}"
              f" ／ 最大含み損 中央 ${t['mae_usd'].median():+.3f}")
        if len(w) and len(l):
            print(f"       勝ち玉が踏まれた深さ 中央 ${w['mae_usd'].median():+.3f}"
                  f" ／ 負け玉が一度は乗った益 中央 ${l['mfe_usd'].median():+.3f}"
                  f"（後者が大きいほど取り逃しが多い）")

    keys = [k for k in ("side", "ceil_type", "exit_reason") if k in t.columns]
    if "hold_min" in t.columns:
        t["保有帯"] = t["hold_min"].map(_hold_band)
        keys.append("保有帯")
    if not keys:
        print("  ③〜⑤ 区分に使える列が無い（side/ceil_type/exit_reason/hold_min のいずれも無い）"); return out
    g = (t.groupby(keys, dropna=False)["net_usd"].agg(件数="size", 純益="sum").reset_index())
    g["1件あたり"] = (g["純益"] / g["件数"]).round(3)
    g["純益"] = g["純益"].round(2)

    print("  ③ どこで血が出ているか（純益の悪い順・上位8）")
    print("     " + g.sort_values("純益").head(8).to_string(index=False).replace("\n", "\n     "))
    print("     ＝ここが段5 Exit 調整の対象（直す1箇所を機械が指す）")

    print("  ④ 残せる部分（純益がプラスの区分・上位5）")
    plus = g[g["純益"] > 0].sort_values("純益", ascending=False).head(5)
    print("     " + (plus.to_string(index=False).replace("\n", "\n     ") if len(plus)
                     else "プラスの区分なし＝全部の区分でマイナス"))
    print("     ＝ここは捨てずに次の段へ渡す")

    print("  ⑤ 巻き込み（③の最悪の区分を保有時間で切ったとき、同じ場面の勝ち玉に何件当たるか）")
    row = g.sort_values("純益").iloc[0]
    m = pd.Series(True, index=t.index)
    for k in [k for k in keys if k != "exit_reason"]:      # 出口理由は入口では選べない＝場面の条件から外す
        m &= (t[k] == row[k]) | (t[k].isna() & pd.isna(row[k]))
    same = t[m]
    sw = same[same["net_usd"] > 0]
    cond = " × ".join(f"{k}={row[k]}" for k in keys if k != "exit_reason")
    print(f"     最悪の区分: {' × '.join(f'{k}={row[k]}' for k in keys)}"
          f" → {int(row['件数'])}件 ${row['純益']:+,.2f}")
    print(f"     同じ場面 {cond} の全体: {len(same)}件 ${same['net_usd'].sum():+,.2f}"
          f" ／ うち勝ち玉 {len(sw)}件 ${sw['net_usd'].sum():+,.2f}")
    print("     ＝この場面を時間で切ると、その勝ち玉も一緒に切れる（切る案は必ずこの対で出す・Q1）")
    # ★切ったときの正味の増減（2026-07-26 まこさん OK・進め方の1つ目）
    #   経緯＝節10 は数字を並べるだけで「良いのか悪いのか」の基準が無く、次の一手につながらなかった
    #   （まこさん指摘「次へつなげるためになにをすべきかよくわからない」）。⑤は既にある数字の引き算で
    #   判定になる＝この場面を丸ごと切れば、その場面の純益がそのまま消える。だから増減は「−場面の純益」。
    #   CC が決める余地のない部分（引き算）から入れる。②取り逃しの基準は未着手＝まこさんと別途決める。
    cut_delta = -float(same["net_usd"].sum())
    if cut_delta > 0:
        judge_txt = "＝切ると良くなる。切る幅と条件を段5 Exit 調整で詰める。"
    elif cut_delta < 0:
        judge_txt = "＝切ると悪くなる。この場面は切る方向では直せない。出口の位置か入口の条件を変える。"
    else:
        judge_txt = "＝差し引きゼロ。切っても変わらない。"
    print(f"     切ったときの正味の増減: ${cut_delta:+,.2f}{judge_txt}")
    out["worst"] = (tuple(row[k] for k in keys), float(row["純益"]))
    out["wrap"] = (len(sw), float(sw["net_usd"].sum()))
    out["cut_delta"] = cut_delta
    # ★まとめ（節12）へ渡す＝③で既に画面に出した表そのもの。新しい計算をしない（2026-08-03・監査 4-18 案1）
    out["worst_rows"] = g.sort_values("純益").head(5)
    out["keys"] = list(keys)
    print("\n  ⚠️ 本節の金額は売買記録の記録値＝report.py と同じ列。疑似シミュではない。"
          "ただし採否はしない＝采否は score.py の採点窓でまこさんが決める。")
    return out


# ══ 観察結果の保存（2026-07-26 まこさん OK）══════════════════════════════
#   背景＝観察結果は画面に出るだけで、走らせた人がリダイレクトした先にしか残らなかった
#   （CC のセッションごとの一時ディレクトリ＝まこさんが後から見返せない）。上書きは絶対にしない＝
#   共通の書き出し処理 ratchet_io.archive_if_exists に委譲（§3.1・道具ごとに命名/archive を書かない）。
#   ⚠️ 書くのは観察結果のテキスト1本だけ。売買記録CSVは書かない・score は呼ばない（read-only 診断のまま）。
#
#   ★2026-08-03 まこさん指示で置き場所を変えた（逐語「ratchet直下に出すのはやめて。フォルダが
#     ぐちゃぐちゃになる。せめて新規フォルダ作成してその中に出力するようにしてほしい」）。
#     旧＝results/priority_rebuild/ratchet/ の直下（売買記録CSV・report・analysis と混ざっていた）。
#     新＝その下の observe/ フォルダ。退避先も observe/archive/ になる（archive_if_exists は
#     「同じ階層の archive/」へ逃がす作りなので、書き先を変えるだけで退避先も一緒に移る）。
OBSERVE_DIR = ratchet_io.RATCHET / "observe"      # ★この道具の出力はここだけ（ratchet 直下に書かない）


def _out_path(kind: str, key: str) -> pathlib.Path:
    """保存先を決める。場所は OBSERVE_DIR に固定＝道具側で別の場所を選べない。"""
    safe = re.sub(r"[^0-9A-Za-z_.-]", "_", str(key))
    OBSERVE_DIR.mkdir(parents=True, exist_ok=True)
    if kind == "scene":
        day = datetime.date.today().strftime("%Y%m%d")
        return OBSERVE_DIR / f"observe_scene_{safe}_{day}.txt"
    if kind == "inspect":
        day = datetime.date.today().strftime("%Y%m%d")
        return OBSERVE_DIR / f"observe_inspect_{safe}_{day}.txt"
    return OBSERVE_DIR / f"observe_{safe}.txt"


class _Tee:
    """画面と保存ファイルの両方へ出す。with で囲んだ中の print が両方に行く。"""

    def __init__(self, path):
        self.path = ratchet_io.archive_if_exists(path)   # 既存は archive へ退避＝上書きしない
        self._f = open(self.path, "w", encoding="utf-8")
        self._out = sys.stdout

    def write(self, s):
        self._out.write(s); self._f.write(s)

    def flush(self):
        self._out.flush(); self._f.flush()

    def __enter__(self):
        sys.stdout = self
        print(f"[保存先] {self.path}")
        return self

    def __exit__(self, *e):
        sys.stdout = self._out
        self._f.close()
        self._out.write(f"\n[保存] {self.path}\n")
        return False


# ══ データと指標の検査（歩0の残作業・まこさん OK 2026-07-30・read-only）═══
# 5段の検査。上流（元データ）で間違いが出たら、下流（足・指標・未来参照・欠損）の結果は全部疑う。
# 結果は機械出力（保存された txt がそのまま正）。売買記録は読まない・書かない。値決めをしない。
# 使い方: python3 observe_diag.py --inspect <5分足CSV>
INSPECT_SECTIONS = [
    "検査1 元データを検査する（欠け・重複・区切り・価格の整合・前後バーの段差）",
    "検査2 足の組み立てを検査する（5分→上位足の集計・区切り時刻・閉じる前のバーへの漏れ・足の内訳）",
    "検査3 指標の計算式を検査する（代表指標を教科書の式で独立計算して突き合わせ＋人工データの性質テスト＋全列を3区分）",
    "検査4 未来参照を検査する（切り詰め再計算テスト＋静的検査）",
    "検査5 欠損と有効標本数を数える（列ごとの欠損率・助走・有効標本数＝歩2 の適合制約の基礎データ）",
    "検査6 需給データを検査する（taker_ls・L-S比・CVD＝重複・整合・欠け・窓ごとの被覆・終端より後を埋めていないか）",
    "検査7 軸カタログ（entry_exit_matrix E-c）と実装を突き合わせる（一覧にあるが実装の無い指標を機械で出す）",
    "検査8 レンジ幾何列を検査する（res_hi/res_lo/sup_hi/sup_lo/mid/W%/帯内位置%＝定義表・既知答え・切り詰め再計算・被覆）",
    "検査9 「終値と◯◯の距離%」に対して「◯◯ そのものの向き」が在るかを突き合わせる（材料の穴を機械で出す）",
    "検査10 業界のライブラリ（pandas-ta-classic）の指標一覧と、うちの材料を突き合わせる（不足を機械で出す）",
    "検査11 V9 が実際に使っている指標の本数が、設定ファイルの本数に入っているかを1件ずつ照らす（段6 の 6-8）",
    "検査12 材料どうしの重複を総当たりで出す（値そのものの相関と、順位の相関の2つで見る・段6 の 6-9③）",
    "検査13 4本値を定数倍しても材料の値が変わらないかを実測する（H6 価格非依存・段6 の 6-9①）",
    "検査14 V9 の実物の列と、うちの材料の列の対応を実測で決める（名前で決めない・2026-08-11 新設）",
    "検査15 いまの正解の印が「レンジだった」とした区間を、片道の度合いで測り直す（判定なし・報告だけ・2026-08-29 新設・M2-A-2）",
    "検査16 帯の許容幅（倍率 × ATR%）が上下限 0.15%〜0.6% の端に張り付いた割合を、足ごとに出す（その足の ATR% と1時間足の ATR% を並べる・判定なし・報告だけ・2026-09-26 新設・M2-E-5）",
]
# 検査の線（全部この場で印字する＝黙って変えられない）。指標照合の許容差は
# indicator_reference_diag（参照表の tol）が正本。
_INSP_STEP_NG_PCT = 5.0    # 前バー終値→次バー始値の段差。これ超は別系列（別取引所の足）の混入を疑い ❌
_INSP_STEP_WARN_PCT = 0.5  # 段差の報告だけの線（❌ にしない）


def _insp_windows() -> list[tuple[str, pd.Timestamp, pd.Timestamp]]:
    """欠けとの重なり判定・標本数の集計に使う窓（periods.py が正本・終端は排他）。"""
    return [("値決め", SEARCH_START, SEARCH_END),
            ("確認", CONFIRM_START, CONFIRM_END),
            ("採点", SCORE_START, SCORE_END + pd.Timedelta("1D"))]


def _gap_runs(missing) -> list[tuple]:
    """欠けた5分バーの一覧を連続区間（開始・終了・本数）へまとめる。"""
    runs = []
    if len(missing) == 0:
        return runs
    s = prev = missing[0]
    n = 1
    for t in missing[1:]:
        if t - prev == pd.Timedelta("5min"):
            n += 1
        else:
            runs.append((s, prev, n))
            s, n = t, 1
        prev = t
    runs.append((s, prev, n))
    return runs


def _insp_source(bars: pd.DataFrame) -> list[str]:
    """検査1 元データ。戻り値＝❌ の一覧。欠けは ⚠️ で印字する（データの事実の報告＝直せない）。"""
    ng = []
    print(f"  行数 {len(bars)} / 期間 {bars.index.min()} 〜 {bars.index.max()}")
    dup = int(bars.index.duplicated().sum())
    print(f"  重複バー: {dup} 本")
    if dup:
        ng.append(f"重複バー {dup} 本（例 {list(bars.index[bars.index.duplicated()][:3])}）")
    off = bars.index[(bars.index.minute % 5 != 0) | (bars.index.second != 0)]
    if len(off):
        ng.append(f"5分の区切りに乗らない時刻 {len(off)} 本（例 {list(off[:3])}）")
    grid = pd.date_range(bars.index.min(), bars.index.max(), freq="5min")
    missing = grid.difference(bars.index.drop_duplicates())
    runs = _gap_runs(missing)
    print(f"  欠け: {len(missing)} 本（連続区間 {len(runs)} 箇所）… 窓との重なりは各行に表示")
    for s, e, k in runs:
        hits = [nm for nm, w0, w1 in _insp_windows() if (s < w1) and (e >= w0)]
        print(f"     ⚠️ {s} 〜 {e}（{k} 本）… 重なり: {'・'.join(hits) if hits else 'なし'}")
    o, h, l, c = bars.open, bars.high, bars.low, bars.close
    checks = [("high < low", h < l),
              ("high < max(open, close)", h < pd.concat([o, c], axis=1).max(axis=1)),
              ("low > min(open, close)", l > pd.concat([o, c], axis=1).min(axis=1)),
              ("価格が 0 以下", (o <= 0) | (h <= 0) | (l <= 0) | (c <= 0)),
              ("出来高が負", bars.volume < 0)]
    for why, mask in checks:
        k = int(mask.sum())
        print(f"  価格の整合 {why}: {k} 本")
        if k:
            ng.append(f"価格の整合 NG＝{why} が {k} 本（例 {list(bars.index[mask][:3])}）")
    consec = bars.index.to_series().diff() == pd.Timedelta("5min")
    step = ((o / c.shift() - 1) * 100)[consec.to_numpy()]
    if len(step):
        n_warn = int((step.abs() > _INSP_STEP_WARN_PCT).sum())
        n_bad = int((step.abs() > _INSP_STEP_NG_PCT).sum())
        print(f"  段差（前バー終値→次バー始値・連続バーのみ）: 最大 {step.abs().max():.4f}% "
              f"/ {_INSP_STEP_WARN_PCT}% 超 {n_warn} 本 / {_INSP_STEP_NG_PCT}% 超 {n_bad} 本")
        top = step.iloc[np.argsort(-step.abs().to_numpy())[:10]]
        for t, v in top.items():
            print(f"     段差上位: {t}  {float(v):+.4f}%")
        if n_bad:
            ng.append(f"段差 {_INSP_STEP_NG_PCT}% 超が {n_bad} 本＝別の取引所の足の混入を疑う")
    return ng


def _insp_close_leak(shift: bool = True, mode: str = "now") -> list[str]:
    """検査2 の一部＝閉じる前の上位足バーへの漏れ（未来参照）を人工データで確かめる。
    shift=False は番人用＝『足が閉じた時刻へずらす』処理を外した壊れた状態を再現する。
    ★K-8（監査 CP60 の修正68・2026-10-04）＝mode="bar_close" は5分足1本ぶん早める形（build_features の htf_shift_mode と同じ式）。
      どちらの形でも、5分足の行 t で当たるのは「行 t が閉じた時刻までに閉じた上位足」だけであることを、2つの時刻（02:25・02:30）で確かめる。"""
    ng = []
    idx = pd.date_range("2026-03-01", periods=288, freq="5min")
    step = idx[1] - idx[0]
    syn = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0,
                        "close": np.arange(288, dtype=float) + 1.0, "volume": 1.0}, index=idx)
    for tf in ("15m", "2h"):
        src = _resample(syn, TF_RULE[tf])
        s = src["close"].copy()
        if shift:
            s.index = src.index + pd.Timedelta(TF_RULE[tf])
            if mode == "bar_close":
                s.index = s.index - step
        s = s.reindex(syn.index, method="ffill")
        for t in (idx[29], idx[30]):                 # 02:25＝早める形で差が出る時刻／02:30＝どの足でも形成中の時刻
            base = t + step if mode == "bar_close" else t
            exp = float(syn["close"].loc[base.floor(TF_RULE[tf]) - step])
            got = s.loc[t]
            if pd.isna(got) or float(got) != exp:
                ng.append(f"{tf}（{mode}）: 形成中の足の値が漏れている（t={t} の値 {got} ≠ 閉じた足の close {exp}）")
    return ng


def _insp_resample(bars: pd.DataFrame, cfg: dict) -> list[str]:
    """検査2 足の組み立て。resample の集計を groupby の独立集計と突き合わせ、区切り時刻と
    閉じる前の漏れを確かめ、足の内訳（8種類）を報告する。"""
    ng = []
    sample = bars.iloc[-min(len(bars), 288 * 40):]
    for tf in ("15m", "2h", "1d"):
        rule = TF_RULE[tf]
        r = _resample(sample, rule)
        g = sample.groupby(sample.index.floor(rule))
        indep = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(),
                              "low": g["low"].min(), "close": g["close"].last(),
                              "volume": g["volume"].sum()})
        common = r.index.intersection(indep.index)
        worst = 0.0
        for col in ("open", "high", "low", "close", "volume"):
            d = float((r.loc[common, col] - indep.loc[common, col]).abs().max())
            worst = max(worst, d)
            if d > 1e-9:
                ng.append(f"{tf} の {col} が独立集計と不一致（最大差 {d:.3e}）")
        misaligned = int((r.index.asi8 % pd.Timedelta(rule).value != 0).sum())
        print(f"  {tf}: バー {len(r)} 本 / 独立集計との最大差 {worst:.2e} / 区切り時刻ずれ {misaligned} 本")
        if misaligned:
            ng.append(f"{tf} の区切り時刻がずれたバー {misaligned} 本")
    leak = _insp_close_leak(shift=True) + _insp_close_leak(shift=True, mode="bar_close")   # ★K-8＝ずらし2種
    print(f"  閉じる前のバーへの漏れ（人工データ・15m と 2h・ずらし2種）: {'なし' if not leak else '検出'}")
    ng += leak
    print(f"  足の内訳（observe_config.json の timeframes・全 {len(cfg['timeframes'])} 種＝指標はこの全部で組む）:")
    one = (load_1m(sample.index[0], sample.index[-1])
           if any(t in cfg["timeframes"] for t in SUB_5M_TF) else None)
    for tf in cfg["timeframes"]:
        if tf == "5m":
            print("     5m: 元データそのまま（resample しない）")
        elif tf in SUB_5M_TF:
            # ★5分足より短い足＝1分足の元データが材料（5分足は細かく割れない・2026-08-16 段7）
            rr = one if tf == "1m" else _resample(one, TF_RULE[tf])
            mis = int((rr.index.asi8 % pd.Timedelta(TF_RULE[tf]).value != 0).sum())
            print(f"     {tf}: 1分足の元データから作る・規則 {TF_RULE[tf]}・"
                  f"直近40日で {len(rr)} 本・区切り時刻ずれ {mis} 本")
            if mis:
                ng.append(f"{tf} の区切り時刻がずれたバー {mis} 本")
        else:
            rr = _resample(sample, TF_RULE[tf])
            print(f"     {tf}: resample 規則 {TF_RULE[tf]}・label=left/closed=left・直近40日で {len(rr)} 本")
    # ★5分足より短い足だけの追加検査（2026-08-16 段7・7-4）＝実データで数える。
    #   5分足のバー t で使う1分足・3分足のバーが、t までに閉じているか。
    #   閉じていないバー（＝5分足のバーの途中の1分足）を1本でも使っていたら未来参照（H2 違反）。
    for tf in [t for t in cfg["timeframes"] if t in SUB_5M_TF]:
        src = one if tf == "1m" else _resample(one, TF_RULE[tf])
        closed_at = src.index + pd.Timedelta(TF_RULE[tf])          # 足が閉じた時刻
        used = pd.Series(closed_at, index=closed_at).reindex(sample.index, method="ffill")
        bad = int((used.dropna() > used.dropna().index).sum())
        print(f"  {tf} が5分足のバーの途中を使っていないか（実データ {len(sample)} 本）: "
              f"閉じていないバーを使った回数 {bad}")
        if bad:
            ng.append(f"{tf} が閉じる前のバーを {bad} 回 使っている（未来参照＝H2 違反）")
    return ng


# ── 検査3 の照合本体（参照表 indicator_reference_diag が正本・2026-07-30 全96種へ拡張）──
def _insp_indicator_match(bars: pd.DataFrame, cfg: dict, catalog: list | None = None) -> tuple[list[str], set, list]:
    """カタログ全列を参照表と機械照合する。①外部ライブラリ ta（非同型の照合相手）
    ②教科書の式の独立実装 ③手計算の既知答え。どれか1つ以上で一致し、どの検査にも
    落ちなかった列だけを検証済みとする。戻り値＝(❌一覧, 検証済み集合, 表示行)。"""
    ng, verified, rows = [], set(), []
    sample = bars.iloc[-min(len(bars), 6000):]
    tail = 500

    def _cmp(mine, ref_s):
        a = mine.iloc[-tail:]
        b = pd.to_numeric(ref_s, errors="coerce").iloc[-tail:]
        m = a.notna() & b.notna()
        if int(m.sum()) < 100:
            return None
        return float((a[m] - b[m]).abs().max())

    for name, fn, _dir in (catalog or build_catalog(cfg)):
        ref, prm = iref.find(name)
        if ref is None:
            ng.append(f"{name}: 参照表に無い（定義・照合方法が未登録）")
            rows.append((name, "参照なし"))
            continue
        marks = []
        bad = False
        try:
            mine = pd.to_numeric(fn(sample), errors="coerce")
        except Exception as e:
            ng.append(f"{name}: カタログ側が計算できない: {str(e)[:50]}")
            rows.append((name, "計算不可"))
            continue
        # ① 外部ライブラリ ta
        if ref["ext"] is not None and iref.TA_OK:
            try:
                ext_s = ref["ext"](sample, prm)
            except Exception as e:
                ext_s = None
                ng.append(f"{name}: 外部照合が計算できない: {str(e)[:50]}")
                bad = True
            if ext_s is None and not bad:
                marks.append("外部=対象外")
            elif ext_s is not None:
                dmax = _cmp(mine, ext_s)
                if dmax is None:
                    marks.append("外部=点不足")
                elif dmax <= ref["tol"]:
                    marks.append(f"外部✓({dmax:.0e})")
                    verified.add(name)
                else:
                    marks.append(f"外部✗({dmax:.1e})")
                    ng.append(f"{name}: 外部ライブラリ ta と不一致（最大差 {dmax:.3e} > 許容 {ref['tol']:.0e}）")
                    bad = True
        else:
            marks.append("外部=対象外" if ref["ext"] is None else "外部=ta無し")
        # ①-2 2つ目の外部の照合相手（pandas-ta ／ scipy・2026-08-09 新設・フロー 段3 の 3-2/3-3）
        #     ta で照合できない指標のうち、別のライブラリ・別の道具で照合できるものをここで見る。
        x2 = iref.EXT2.get(ref["family"])
        if x2 is not None and iref.ext2_ready():
            fn2, tool = x2
            try:
                s2 = fn2(sample, prm)
            except Exception as e:
                s2 = None
                ng.append(f"{name}: 2つ目の照合（{tool}）が計算できない: {str(e)[:50]}")
                bad = True
            if s2 is not None:
                dmax = _cmp(mine, s2)
                if dmax is None:
                    marks.append(f"外部2[{tool}]=点不足")
                elif dmax <= ref["tol"]:
                    marks.append(f"外部2[{tool}]✓({dmax:.0e})")
                    verified.add(name)
                else:
                    marks.append(f"外部2[{tool}]✗({dmax:.1e})")
                    ng.append(f"{name}: 2つ目の照合（{tool}）と不一致"
                              f"（最大差 {dmax:.3e} > 許容 {ref['tol']:.0e}）")
                    bad = True
        elif x2 is not None:
            marks.append("外部2=道具無し")
        # ② 教科書の式の独立実装
        if ref["tb"] is not None:
            try:
                dmax = _cmp(mine, ref["tb"](sample, prm))
            except Exception as e:
                dmax = None
                ng.append(f"{name}: 独立実装が計算できない: {str(e)[:50]}")
                bad = True
            if dmax is None:
                if not bad:
                    marks.append("独立=点不足")
            elif dmax <= ref["tol"]:
                if ref.get("tb_kind") == "写し":
                    # ★K-4（2026-10-11・監査 CP60 の修正59）＝写しの独立実装（カタログかライブラリと同じ変形を別の書き方で写した物）は
                    #   「自分と同じか」しか確かめていない＝一致しても検証済みに数えない。検証済みにするのは手計算の既知答え（③）。
                    marks.append(f"独立(写し)✓({dmax:.0e})")
                else:
                    marks.append(f"独立✓({dmax:.0e})")
                    verified.add(name)
            else:
                marks.append(f"独立✗({dmax:.1e})")
                ng.append(f"{name}: 教科書の独立実装と不一致（最大差 {dmax:.3e} > 許容 {ref['tol']:.0e}）")
                bad = True
        # ③ 手計算の既知答え
        if ref["known"] is not None:
            k_ok = k_all = 0
            for cb, checks in (ref["known"](prm) or []):
                try:
                    out = pd.to_numeric(fn(cb), errors="coerce")
                except Exception as e:
                    ng.append(f"{name}: 既知答えの合成バーで計算できない: {str(e)[:50]}")
                    bad = True
                    continue
                for pos, exp, atol in checks:
                    k_all += 1
                    got = out.iloc[pos]
                    if isinstance(exp, str):
                        ok = pd.notna(got) and ((got > 0) if exp == "+" else (got < 0))
                        want = f"符号{exp}"
                    else:
                        ok = pd.notna(got) and abs(float(got) - exp) <= atol
                        want = f"{exp:.6g}"
                    if ok:
                        k_ok += 1
                    else:
                        ng.append(f"{name}: 手計算の既知答えと不一致（期待 {want} / 実測 {got}）")
                        bad = True
            if k_all:
                marks.append(f"既知{k_ok}/{k_all}")
                if k_ok == k_all:
                    verified.add(name)
        if bad:
            verified.discard(name)
        rows.append((name, " ".join(marks)))
    return ng, verified, rows


def _insp_property(cfg: dict, catalog: list | None = None) -> tuple[set, dict]:
    """人工データの性質テスト（参照表の性質の型に従う）。順張り値＝上げ相場の値 > 下げ相場の値。
    ボラ量＝荒い相場の値 ≥ 静かな相場の値。反転サイン・状態量は型が無い＝既知答えの側で検証する。"""
    n = 900
    idx = pd.date_range("2026-03-01", periods=n, freq="5min")
    t = np.arange(n, dtype=float)
    wig = np.sin(t / 3.0)

    def mk(close):
        c = pd.Series(close, index=idx)
        return pd.DataFrame({"open": c.shift().fillna(c.iloc[0]),
                             "high": c * 1.001 + 0.2 * np.abs(wig),
                             "low": c * 0.999 - 0.2 * np.abs(wig),
                             "close": c, "volume": 10.0 + np.cos(t / 5.0)}, index=idx)

    up = mk(100.0 + 0.05 * t + 0.3 * wig)
    dn = mk(100.0 + 0.05 * (n - t) + 0.3 * wig)
    calm = mk(100.0 + 0.05 * np.sin(t / 40.0))
    wild = mk(100.0 + 3.0 * np.sin(t / 7.0))
    ok, why = set(), {}
    for name, fn, directional in (catalog or build_catalog(cfg)):
        ref, _prm = iref.find(name)
        kind = ref["prop"] if ref else ("trend" if directional else "vol")
        try:
            if kind == "trend":
                a = float(pd.to_numeric(fn(up), errors="coerce").iloc[-100:].median())
                b = float(pd.to_numeric(fn(dn), errors="coerce").iloc[-100:].median())
                # ★値が出ない＝この合成データ（900本）では暖機が終わらない指標。
                #   「性質が違う」ではなく「判定できない」＝両者を混ぜない（2026-08-09）。
                if not (np.isfinite(a) and np.isfinite(b)):
                    why[name] = "判定できない（合成データ 900本では値が出ない＝暖機が終わらない）"
                    good = False
                else:
                    good = a > b
                    why[name] = f"上げ {a:.4g} / 下げ {b:.4g}" + ("" if good else "＝大小が期待どおりでない")
            elif kind == "vol":
                a = float(pd.to_numeric(fn(wild), errors="coerce").iloc[-100:].median())
                b = float(pd.to_numeric(fn(calm), errors="coerce").iloc[-100:].median())
                good = np.isfinite(a) and np.isfinite(b) and a >= b
                why[name] = f"荒い {a:.4g} / 静か {b:.4g}" + ("" if good else "＝大小が期待どおりでない")
            else:
                why[name] = "性質テストの型なし（反転サイン・状態量＝既知答えの側で検証）"
                good = False
            if good:
                ok.add(name)
        except Exception as e:
            why[name] = f"計算できず: {str(e)[:40]}"
    return ok, why


def _ref_coverage_counts(refs: list, ext2_keys) -> tuple[list[str], list[str]]:
    """照合の相手の数を数える（純粋な計算＝番人が偽の表を渡して既知答えで確かめられる）。
    戻り値＝(外部の照合相手がいない family, そのうち手計算の既知答えも無い family)。"""
    no_ext, only_mine = [], []
    for e in refs:
        if e["ext"] is None and e["family"] not in ext2_keys:
            no_ext.append(e["family"])
            if e["known"] is None:
                only_mine.append(e["family"])
    return no_ext, only_mine


def _insp_ref_coverage() -> list[str]:
    """検査3 の頭に出す「私が書いた式だけで担保されている件数」（2026-08-09・フロー 段3 の 3-5）。
    ★何を伝えるか＝外部の照合相手も、別の道具も、手計算の既知答えも無い指標は、
      私（CC）が2回 同じ向きに読み違えると、そのまま通ってしまう。その件数を毎回 出す。"""
    no_ext, only_mine = _ref_coverage_counts(iref.REFS, set(iref.EXT2))
    n = len(iref.REFS)
    print(f"  ── 照合の相手の数（指標の種類 {n} 件）──")
    print(f"     外部ライブラリ ta で照合 {sum(1 for e in iref.REFS if e['ext'] is not None)} 件"
          f" ／ 2つ目の道具で照合 {len(iref.EXT2)} 件"
          f" ／ ★外部の照合相手がいない {len(no_ext)} 件")
    print(f"     ★そのうち手計算の既知答えも無い（＝私が書いた式だけで担保）: {len(only_mine)} 件"
          + (f" … {'・'.join(only_mine)}" if only_mine else "（無し）"))
    print("     ↑ この件数が、私の書き間違いだけで通ってしまう範囲です（フロー 段3 の 3-5）")
    # 仕分け表（フロー 段3 の 3-1）＝ta で照合できない指標を (a)(b)(c) に分けて出す。
    # ★どれが (a) かは「名前が同じだから」でなく「実データで許容差の中に入ったから」で決めている
    #   （入らなかったものは EXT2 に足していない＝ここで (c) に出る）。
    rest = [e for e in iref.REFS if e["ext"] is None]
    grp: dict[str, list[str]] = {"(a) 別のライブラリで照合できる": [], "(b) 別の道具で照合できる": [],
                                 "(c) 外部の照合相手がいない": []}
    for e in rest:
        x2 = iref.EXT2.get(e["family"])
        if x2 is None:
            grp["(c) 外部の照合相手がいない"].append(
                e["family"] + ("（手計算の既知答えあり）" if e["known"] is not None else "（★既知答えも無い）"))
        elif x2[1] == "pandas-ta":
            grp["(a) 別のライブラリで照合できる"].append(f"{e['family']}［{x2[1]}］")
        else:
            grp["(b) 別の道具で照合できる"].append(f"{e['family']}［{x2[1]}］")
    print(f"  ── 仕分け（ta で照合できない {len(rest)} 件・フロー 段3 の 3-1）──")
    for k, v in grp.items():
        print(f"     {k}: {len(v)} 件")
        for x in v:
            print(f"        ・{x}")
    return []


def _insp_indicator_stage(bars: pd.DataFrame, cfg: dict, catalog: list | None = None) -> list[str]:
    """検査3 全体＝定義表の機械印字＋3本柱の照合＋性質テスト＋全列の3区分。
    catalog を渡すとその列だけを測る（--cols＝材料を足した時に、足した列だけを確かめるため）。"""
    print(f"  外部ライブラリ照合: {'ta（非同型の照合相手＝別の実装者のコード）' if iref.TA_OK else '⚠️ ta が無い環境＝独立実装と既知答えで担保'}")
    print(f"  2つ目の照合の相手: {'pandas-ta-classic と scipy（2026-08-09 追加）' if iref.ext2_ready() else '⚠️ 入っていない環境＝1つ目だけで担保'}")
    _insp_ref_coverage()
    print("  ── 定義表（指標ごとの定義・流儀・方向の意味。この表が検査の物差し）──")
    for e in iref.REFS:
        print(f"     ◆ {e['family']} … {e['teigi']}")
        print(f"        流儀: {e['ryugi']}")
        print(f"        方向: {e['houkou']}")
    print("  ── 照合（外部ライブラリ ／ 教科書の独立実装 ／ 手計算の既知答え）──")
    ng, verified, rows = _insp_indicator_match(bars, cfg, catalog)
    for name, marks in rows:
        print(f"     {name}: {marks}")
    print("  ── 人工データの性質テスト（参照表の性質の型に従う）──")
    prop_ok, why = _insp_property(cfg, catalog)
    names = [nm for nm, _f, _d in (catalog or build_catalog(cfg))]
    cls = {nm: ("一致検証済み" if nm in verified else "性質検証のみ" if nm in prop_ok else "未検証")
           for nm in names}
    from collections import Counter
    cnt = Counter(cls.values())
    print(f"  3区分（指標 {len(names)} 種）: 一致検証済み {cnt.get('一致検証済み', 0)} "
          f"/ 性質検証のみ {cnt.get('性質検証のみ', 0)} / 未検証 {cnt.get('未検証', 0)}")
    for nm in names:
        note = "" if cls[nm] != "未検証" else f" … {why.get(nm, '')}"
        print(f"     [{cls[nm]}] {nm}{note}")
    return ng


def _insp_lookahead(bars: pd.DataFrame, cfg: dict, catalog: list | None = None) -> list[str]:
    """検査4 未来参照。①静的検査＝このファイルに負の shift／中央寄せ rolling が無いか。
    ②切り詰め再計算＝サンプル時点 t でデータを切り詰めて全列を計算し直し、全量計算の t の値と比べる。
    切り詰めて値が変わる／消える列＝t より後の情報を使っている疑い。"""
    ng = []
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    # ★2026-08-23（54回目・77番・まこさん承認 eb6f38734142e25c…）＝探し方を hook の正本（h2_scan 経由）にした。
    #   直す前＝行をそのまま見て「H2OK が無ければ ❌」＝説明の文章（docstring）の語にも反応した
    #   （:394 の「`.shift(-` も `center=True` も1つも使っていません」で ❌ 2件・実測）。
    #   41番（説明の文章での誤発火）を hook と leak_causality_diag では直してあったが、ここだけ古いままだった。
    #   いま＝hook の find_bad（コメント・docstring を外してから見る）を h2_scan 経由で呼ぶ＝写しを持たない。
    import h2_scan
    hits = h2_scan.scan_text(src)
    print(f"  静的検査（探し方の正本＝{pathlib.Path(h2_scan.SOURCE).name}・説明の文章は外して見る）: "
          f"注記なしの未来参照の書き方 {len(hits)} 行 {[i for i, _ in hits] if hits else ''}")
    for ln, line in hits:
        ng.append(f"静的検査: 注記なしの未来参照の書き方が {ln} 行目にある: {line.strip()[:60]}")
    span = bars.loc[bars.index.max() - pd.Timedelta(days=int(cfg["warmup_days"]) + 3):]
    feat_full, meta_full = build_features(span, cfg, catalog)
    # ★この検査は本走より短い期間（助走+3日）で計算し直す＝長い本数が要る指標は、その期間では
    #   計算できないことがある。列の数だけを出すと「本走 4,689 なのに ここは 4,683」で読む人が
    #   悩む（2026-08-10 実際に悩んだ）ので、名前と理由を出す。★本走の材料の欠けではない。
    _nocalc = sorted((k, v[1]) for k, v in meta_full.items() if v[0] != "ok")
    n_cat = len(catalog or build_catalog(cfg)) * len(cfg["timeframes"])
    print(f"  この期間（{len(span)} 本・{span.index[0].date()}〜{span.index[-1].date()}）で計算できない列: "
          f"{len(_nocalc)} 件 ／ カタログの掛け算 {n_cat} 列 − {len(_nocalc)} ＝ 下の照合の対象 "
          f"{feat_full.shape[1]} 列")
    for k, why in _nocalc:
        print(f"     {k} ← {why}")
    if _nocalc:
        print("     ↑ ★この期間が短いために出るもので、本走（助走 "
              f"{cfg['warmup_days']} 日＋全期間）の材料の欠けではない（検査5 の列の数で確かめられる）")
    picks = [span.index[-1], span.index[-100], span.index[-400]]
    suspects = {}
    for t in picks:
        feat_tr, _m2 = build_features(span.loc[:t], cfg, catalog)
        a, b = feat_full.loc[t], feat_tr.loc[t]
        for col in feat_full.columns:
            x, y = a.get(col), b.get(col)
            if pd.isna(x) and pd.isna(y):
                continue
            if pd.isna(x) != pd.isna(y) or abs(float(x) - float(y)) > 1e-9 * max(1.0, abs(float(x))):
                suspects.setdefault(col, []).append(str(t))
    print(f"  切り詰め再計算: サンプル時点 {[str(t) for t in picks]} × 全 {feat_full.shape[1]} 列 "
          f"→ 不一致 {len(suspects)} 列")
    for col, ts in suspects.items():
        ng.append(f"切り詰めで値が変わる列（未来参照の疑い）: {col}（時点 {ts}）")
    return ng


def _nominal_wlen(name: str, lead: int) -> int:
    """列の名目窓長＝max(材料の数値パラメータの最大値, 助走+1)。補正後独立標本数の分母
    （CP3 提案1 の強化・2026-07-30 まこさん GO）。再帰型（RSI/ADX 等＝助走1本）でも名目期間で
    補正が効く。パラメータの正本＝indicator_reference_diag の正規表現（find）。
    流儀＝EMA 系の実効記憶は名目より長いことがあるが、CP2 4-4 の病型（長窓 rolling の
    重なり水増し）を正しく潰す下限近似として名目窓長を使う。"""
    _ref, prm = iref.find(name)
    nums = [int(p) for p in (prm or ()) if isinstance(p, (int, float)) and float(p) == int(p) and p >= 2]
    return max(nums + [lead + 1, 1])


def _insp_samples(bars: pd.DataFrame, cfg: dict, catalog: list | None = None) -> None:
    """検査5 列ごとの欠損率・助走・有効標本数（値決め窓・採点窓）。判定はしない＝
    適合制約の下限はまこさんが決める（歩2）。独立の有効標本数は『その足のバー』で数える
    （5分へ ffill した見かけの本数で数えると上位足が実際より多く見えるため）。
    ★補正後独立標本数（2026-07-30 CP3 提案1・まこさん GO）＝非欠損バー数 ÷ 名目窓長。
    窓長の重なりの水増し（例＝日足288本窓の列が『660標本』に見えるが重ならない区間は2つ）を
    補正する。G2 適合制約の下限 N_MIN はこの補正後の値に当てる。"""
    w0, w1 = SEARCH_START, SEARCH_END
    s0, s1 = SCORE_START, SCORE_END + pd.Timedelta("1D")
    span = bars.loc[w0 - pd.Timedelta(days=int(cfg["warmup_days"])):]
    # ★2026-09-08（監査 cp30 の別枠2）＝渡された一覧が在ればそれを使う（--cols で絞れるようにした）。
    #   直す前＝自分で build_catalog を呼ぶので、列を名前で絞る旗が検査5 に1つも効かなかった。
    catalog = catalog if catalog is not None else build_catalog(cfg)
    print(f"  値決め窓 {w0.date()}〜{(w1 - pd.Timedelta('1D')).date()} ／ 採点窓 {s0.date()}〜{SCORE_END.date()} "
          f"／ 助走データ {cfg['warmup_days']} 日")
    print("  列 … 欠損率%（値決め窓・その足のバー基準）／助走（最初に値が出るまでのバー数）"
          "／独立の有効標本数（値決め窓・採点窓）／補正後独立標本数＝有効÷名目窓長（G2 の基礎データ）")
    # ★1m・3m を使うときだけ、1分足の元データを1回だけ読む（使わないなら読まない＝重いので）。
    one = (load_1m(span.index[0], span.index[-1])
           if any(t in cfg["timeframes"] for t in SUB_5M_TF) else None)
    for tf in cfg["timeframes"]:
        src, closed = insp5_frame(span, tf, one)       # ★2026-09-08＝枠づくりは1か所（134番の①）
        in_w = (closed >= w0) & (closed < w1)
        in_s = (closed >= s0) & (closed < s1)
        tot = int(in_w.sum())
        for name, fn, _d in catalog:
            col = f"{name}__{tf}"
            try:
                v = pd.to_numeric(fn(src), errors="coerce").notna().to_numpy()
            except Exception as e:
                print(f"     {col} … 計算できず: {str(e)[:50]}")
                continue
            n_w = int(v[in_w].sum())
            n_s = int(v[in_s].sum())
            first = int(np.argmax(v)) if v.any() else -1
            lead = f"{first} 本" if first >= 0 else "値なし"
            miss = 100.0 * (1 - n_w / tot) if tot else float("nan")
            wl = _nominal_wlen(name, max(first, 0))
            print(f"     {col} … 欠損 {miss:.1f}% ／ 助走 {lead} ／ 有効 {n_w}（値決め）・{n_s}（採点）"
                  f" ／ 補正後 {n_w // wl}（値決め・窓長{wl}）・{n_s // wl}（採点）")


def _demand_tail_ok(series: pd.Series, src_end: pd.Timestamp) -> bool:
    """検査6 の部品＝取り込んだ需給の列が、元データの終端より後を値で埋めていないか（埋めたら未来の捏造）。"""
    after = series[series.index > src_end]
    return bool(after.isna().all()) if len(after) else True


def _insp_demand(bars: pd.DataFrame, files: dict | None = None) -> list[str]:
    """検査6 需給データ。①定義表（定義・流儀・方向・出典＝indicator_reference_diag.DEMAND_REF が正本）
    ②元ファイルの重複・整合・値の妥当範囲 ③欠けの位置と窓の重なり ④取り込みが終端より後を
    埋めていないこと ⑤値決め窓・採点窓それぞれの被覆、を機械出力する（2026-07-30 見直し5点を反映）。"""
    ng = []
    files = files or _DEMAND_FILES
    base = pathlib.Path(__file__).resolve().parent
    ingested, cov = load_demand(bars.index, files)
    print("  定義と流儀（正本＝indicator_reference_diag.DEMAND_REF・2026-07-30 WebResearch＋実測で確定）:")
    for nm in files:
        r = iref.DEMAND_REF.get(nm)
        if r is None:
            ng.append(f"{nm}: 需給の定義表 DEMAND_REF に未登録（定義・流儀・出典の記録が無い）")
            continue
        print(f"     ◆ {nm} … {r['teigi']}")
        print(f"        流儀: {r['ryugi']}")
        print(f"        方向: {r['houkou']} ／ 出典: {r['source']}")
    for name, (rel, tcol, vcol) in files.items():
        p = (base / rel).resolve()
        if not p.exists():
            print(f"  {name}: ⚠️ 元ファイルなし（{rel}）＝観察では全期間 NaN")
            continue
        use = [tcol] + ([vcol] if vcol else ["taker_buy_base", "volume"])
        try:
            d = pd.read_csv(p, usecols=use, parse_dates=[tcol]).set_index(tcol).sort_index()
        except Exception as e:
            ng.append(f"{name}: 元ファイルが読めない: {str(e)[:50]}")
            continue
        dup = int(d.index.duplicated().sum())
        if dup:
            ng.append(f"{name}: 元データに重複タイムスタンプ {dup} 本")
        step = d.index.to_series().diff().median()
        gaps = int((d.index.to_series().diff() > step).sum()) if pd.notna(step) else 0
        if vcol:
            v = pd.to_numeric(d[vcol], errors="coerce")
            bad = int((v < 0).sum())
            if bad:
                ng.append(f"{name}: 値が負 {bad} 本（比率が負はデータ壊れ）")
        else:
            tb = pd.to_numeric(d["taker_buy_base"], errors="coerce")
            vv = pd.to_numeric(d["volume"], errors="coerce")
            bad = int(((tb < 0) | (vv < 0) | (tb > vv)).sum())
            if bad:
                ng.append(f"{name}: taker_buy_base と volume の整合 NG {bad} 本（負・または taker>全量）")
        print(f"  {name}: {rel}（{len(d)} 行 / {d.index.min()} 〜 {d.index.max()} / 刻み {step} / 重複 {dup} / 欠け {gaps} 箇所）")
        # 値の妥当範囲（負だけでは甘い＝ゼロ・分布の裾を機械出力・2026-07-30 見直し5）
        if vcol:
            z = int((v == 0).sum())
            znote = " ⚠️ ゼロは要確認（比率・OI のゼロは通常起きない値）" if z else ""
            print(f"     値の範囲: min {v.min():.6g} / p1 {v.quantile(0.01):.6g} / 中央 {v.median():.6g}"
                  f" / p99 {v.quantile(0.99):.6g} / max {v.max():.6g} / ゼロ {z} 本{znote}")
            if z:
                zt = d.index[(v == 0).to_numpy()]
                print(f"       ゼロの時刻（最初と最後）: {zt.min()} 〜 {zt.max()}")
        # 欠けの位置と窓の重なり（数だけでなく位置＝検査1 と同型・2026-07-30 見直し4）
        if gaps and pd.notna(step):
            dif = d.index.to_series().diff()
            pos = np.where((dif > step).to_numpy())[0]
            regions = [(d.index[i - 1], d.index[i], int(round(dif.iloc[i] / step)) - 1) for i in pos]
            total_missing = sum(r[2] for r in regions)
            regions.sort(key=lambda r: -r[2])
            print(f"     欠けの位置（大きい順に5つ・全 {len(regions)} 箇所・計 {total_missing} 本分）:")
            for a, b, k in regions[:5]:
                print(f"       {a} 〜 {b}（{k} 本分）")
            for wname, w0, w1 in _insp_windows():
                hit = [r for r in regions if r[0] < w1 and r[1] > w0]
                print(f"     欠けと{wname}の重なり: {len(hit)} 箇所（約 {sum(r[2] for r in hit)} 本分）")
        if name in ingested.columns:
            s = ingested[name]
            if not _demand_tail_ok(s, d.index.max()):
                ng.append(f"{name}: 元データの終端 {d.index.max()} より後を値で埋めている（未来の捏造＝ffill の漏れ）")
            for wname, w0, w1 in _insp_windows():
                seg = s[(s.index >= w0) & (s.index < w1)]
                pct = 100.0 * seg.notna().mean() if len(seg) else float("nan")
                note = "" if pct >= 99.5 else (" ⚠️ 被覆が欠ける" if pct > 0 else " ⚠️ 0%＝この窓では何も寄与しない")
                print(f"     被覆 {wname}: {pct:.1f}%{note}")
    return ng


def _insp_axis(cfg: dict) -> list[str]:
    """検査7 軸カタログ E-c と実装の突き合わせ。E-c の実文・対応表 AXIS_EC・実装列名の3者を機械照合する。"""
    p = pathlib.Path(__file__).resolve().parent.parent.parent / ".claude" / "ratchet" / "entry_exit_matrix.md"
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.lstrip().startswith("- **E-c")]
    if len(lines) != 1:
        return [f"entry_exit_matrix.md の E-c 行が {len(lines)} 本（1本のはず）＝突き合わせ不能"]
    impl_names = [nm for nm, _f, _d in build_catalog(cfg)] + list(_DEMAND_FILES)
    ng, rows = iref.axis_ec_check(lines[0], impl_names)
    from collections import Counter
    cnt = Counter(r["status"] for r in rows)
    print(f"  E-c の項目 {len(rows)} 件: 実装あり {cnt.get('あり', 0)} / 部分実装 {cnt.get('部分', 0)} / 未実装 {cnt.get('未実装', 0)}")
    for r in rows:
        mark = {"あり": "  ", "部分": "⚠️", "未実装": "⚠️"}[r["status"]]
        note = f" … {r['note']}" if r["note"] else ""
        print(f"     {mark} [{r['status']}] {r['cat']}＝{r['token']}（実装列 {r['n']} 本）{note}")
    print("  ⚠️＝実装するかは歩2 の材料設計と一緒にまこさんが決める（検査は可視化まで）")
    return ng


# ══ 検査9・検査10（材料の不足を機械で出す・2026-08-09 新設・マイルストーン①のフロー 段2）═══════
# ★置き場所をここにした理由＝新しい道具を別に作ると、材料の正本が2つになるため（フロー 段2 の本文）。
# ★どちらも「足りないものを数えて出す」だけ。材料を足さない・式を直さない（足すのは段6）。
_DIST_PAT = re.compile(r"^close vs (.+?)%")   # 「終値と◯◯の距離%」の部品
_SLOPE_PAT = re.compile(r"^(.+?)傾き")         # 「◯◯ そのものの向き」の部品


def _direction_gap(names: list[str]) -> tuple[list[str], list[str], list[str]]:
    """カタログ名の一覧から ①距離%の対象 ②向きの対象 ③距離は在るが向きが無い対象 を出す。
    対象＝「close vs 」と「%」の間の文字。期間を含む＝SMA20 と SMA50 は別の対象として数える
    （SMA20 の向きが在っても SMA50 の向きの代わりにはならないため）。"""
    dist: list[str] = []
    slope: list[str] = []
    for n in names:
        m = _DIST_PAT.match(n)
        if m and m.group(1) not in dist:
            dist.append(m.group(1))
        m2 = _SLOPE_PAT.match(n)
        if m2 and m2.group(1) not in slope:
            slope.append(m2.group(1))
    return dist, slope, [d for d in dist if d not in slope]


def _insp_direction_gap(cfg: dict, catalog: list | None = None) -> list[str]:
    """検査9 「終値と◯◯の距離%」に対して「◯◯ そのものの向き」が在るかの突き合わせ。
    ❌＝この検査自身が死んでいるとき（命名が変わって距離の部品を1つも拾えない）。
    穴そのものは ⚠️ の報告＝材料を足すのはフロー 段6（検査で直さない）。"""
    names = [nm for nm, _f, _d in (catalog if catalog is not None else build_catalog(cfg))]
    dist, slope, gap = _direction_gap(names)
    print(f"  「終値と◯◯の距離%」の対象 {len(dist)} 個 ／ 「◯◯ そのものの向き」の対象 {len(slope)} 個"
          f" ／ ★距離は在るが向きが無い {len(gap)} 件")
    print(f"     向きが在る対象: {'・'.join(slope) if slope else '（無し）'}")
    for g in gap:
        print(f"     ⚠️ {g}: 「終値と{g}の距離%」は在るが、「{g} そのものの向き」の部品が無い")
    print("  ⚠️＝材料の穴の報告（直すのはフロー 段6）。V9 の9本のうち6本が BB 中央線（＝SMA20）の傾きを使っている")
    return [] if dist else ["「close vs ◯◯%」の形の部品が1つも無い＝命名が変わって この検査が死んでいる"]


def _insp_industry(cfg: dict, lib_funcs: dict | None = None) -> list[str]:
    """検査10 業界のライブラリ（pandas-ta-classic）の指標一覧と、うちの材料の突き合わせ。
    ❌＝ライブラリが入っていない／対応表 INDUSTRY_MAP が実物とずれている（表の直し忘れ）。
    足りない指標そのものは ⚠️ の報告＝足すのはフロー 段6。
    lib_funcs は番人専用＝偽の関数一覧を注入して、検査が実際に落ちることを確かめる。"""
    ver = "（注入・番人用）"
    if lib_funcs is None:
        try:
            import pandas_ta_classic as _pt
            lib_funcs = {k: list(v) for k, v in _pt.Category.items()}
            ver = str(_pt.version)
        except Exception as e:                                  # noqa: BLE001
            return ["業界のライブラリ pandas-ta-classic が読めない＝突き合わせ不能"
                    f"（{str(e)[:60]}）。requirements.txt の版で入れる"]
    fams = [e["family"] for e in iref.REFS]
    r = iref.industry_gap(lib_funcs, fams)
    print(f"  ライブラリ pandas-ta-classic {ver}: 関数 {len(r['all_fn'])} 種類"
          f"（{' / '.join(f'{k} {len(v)}' for k, v in lib_funcs.items())}）")
    print(f"  うちの参照表 family {len(dict.fromkeys(fams))} 種類 → 押さえている関数 {len(r['covered'])} 種類")
    print(f"  ★押さえていない関数 {len(r['missing'])} 種類 ＝ 入れない候補 {len(r['skip'])} ＋ ★入れる候補 {len(r['add'])}")
    print("  ── 対応表（うちの指標 → 同じものを計算するライブラリの関数）──")
    for f in dict.fromkeys(fams):
        fns, note = iref.INDUSTRY_MAP.get(f, ((), "（対応表に無い）"))
        print(f"     {f:18s} → {('・'.join(fns) if fns else '（無し）'):22s} {note}")
    print("  ── 入れない候補（★まこさんの承認はまだ・next_step §5 の10番。指標でないものに限る）──")
    for fn in r["skip"]:
        print(f"     {fn:16s} {iref.INDUSTRY_SKIP[fn]}")
    print("  ── ★入れる候補（既定は「入れる」＝まこさん決定「完全に不要な指標以外はすべて入れてほしい」）──")
    for cat in lib_funcs:
        got = [fn for fn in r["add"] if r["all_fn"][fn] == cat]
        if got:
            print(f"     [{cat} {len(got)}] " + ", ".join(sorted(got)))
    print("  ⚠️ 2026-08-08 に手で数えた数（押さえている34／不足159／入れる候補139）は再現できない＝"
          "そのときの対応表が記録に残っていないため。上の数は この対応表から機械が数えたもの")
    return r["ng"]


# ══ 検査11（V9 が実際に使っている本数との突き合わせ・2026-08-11 新設・段6 の 6-8）════════════
# ★何のための検査か。指標の本数（RSI の 14、RCI の 7 のような数字）は設定ファイル
#   observe_config.json に書いてある。**そこに無い本数は、engine_tuner が何回 試しても永久に出ない。**
#   V9（唯一の実利資産）が実際に使っている本数が1つも入っていないと、V9 が組んでいる形すら
#   engine_tuner は作れない（実例＝V9 P22 の RCI7 と RCI9 のクロス）。
#   ★この検査は「本数を点の一覧で限定する」こととは別。V9 が使う本数の穴を埋めるだけ。
#   本数を範囲で探せるようにするのはマイルストーン③。
# ★数字は実物のファイルから拾う（記憶や書き写しでない）。1件ずつ「どのファイルの何行目の、どの文か」を出す。
_V9_ROOT = pathlib.Path(__file__).resolve().parents[2]           # bitget-python-sdk-api/
_V9_PERIOD_PATTERNS = (
    # (指標, 設定のキー, ファイル, 正規表現, 拾う数字の位置, 説明)
    ("RCI", "rci_periods", "strategies/cat_v9_decider.py",
     r'calculate_rci\(df\["close"\], (\d+)\)', "1つ", "V9 が直に計算している RCI"),
    ("RCI", "rci_periods", "strategies/cat_v9_decider.py",
     r'for period in \[([\d, ]+)\]', "並び", "同上（まとめて回している方）"),
    ("RCI", "rci_periods", "cat/indicators.py",
     r'"RCI_WINDOWS", \[([\d, ]+)\]', "並び", "共通の指標づくりの既定"),
    ("ADX", "atr_periods", "strategies/cat_v9_decider.py",
     r"ADXIndicator\([^)]*window=(\d+)", "1つ", "V9 の ADX"),
    ("ATR%", "atr_periods", "strategies/cat_v9_decider.py",
     r'_tr\.rolling\(window=(\d+)', "1つ", "V9 の ATR（単純平均）"),
    ("BB", "bb_periods", "strategies/cat_v9_decider.py",
     r'BollingerBands\(close=df\["close"\], window=(\d+)\)', "1つ", "V9 のボリンジャーバンド"),
    ("EMA", "ema_periods", "cat/indicators.py",
     r'EMAIndicator\(close=df\["close"\], window=(\d+)\)', "1つ", "V9 の EMA"),
    ("Stoch", "stoch_periods", "strategies/cat_v9_decider.py",
     r"window=(\d+), smooth_window=\d+", "1つ", "V9 のストキャスティクス"),
    ("fib位置", "fib_windows", "strategies/cat_v9_decider.py",
     r"n_look = (\d+)", "1つ", "V9 の『直近レンジ内での位置』（うちの fib位置 と同じ形）"),
    # ★2026-08-11 に指標名とキーを直した。前は「realized_vol / realized_vol_periods」で照らしていたが、
    #   V9 の entry_risk_score は「終値のばらつき ÷ 終値」で、うちの realized_vol（対数リターンの
    #   ばらつき）とは別物だった。実測（検査14）＝BB幅(20,2.0) と 値の相関 +0.9999464／順位 +0.9999952。
    #   realized_vol は上位3件にも入らない。よって照らす先を bb_periods にした（本数 20 は両方に在る）。
    ("entry_risk_score", "bb_periods", "strategies/cat_v9_decider.py",
     r"vola = df\[\"close\"\]\.rolling\(window=(\d+)", "1つ",
     "V9 の entry_risk_score（終値のばらつき÷終値）＝うちの BB幅 と実測で一致（検査14）"),
)
_V9_PERIOD_PARAMS = (
    # (指標, 設定のキー, cat_params_v9.json のキー, 説明)
    ("RSI", "rsi_periods", ("SHORT_RSI_PERIOD",), "V9 の SHORT 側の RSI"),
    ("MACD", "macd_params", ("P1_MACD_FAST", "P1_MACD_SLOW", "P1_MACD_SIGNAL"), "V9 P1 の MACD（3つで1組）"),
)


def _v9_periods() -> list[dict]:
    """V9 が実際に使っている本数を、実物のファイルから機械で拾う。逐語と行番号を必ず持たせる。"""
    rows: list[dict] = []
    for fam, key, rel, pat, how, note in _V9_PERIOD_PATTERNS:
        p = _V9_ROOT / rel
        if not p.exists():
            rows.append(dict(指標=fam, キー=key, 本数=None, 出どころ=f"{rel}（ファイルが無い）", 逐語="", 説明=note))
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            m = re.search(pat, line)
            if not m:
                continue
            nums = ([int(x) for x in m.group(1).split(",") if x.strip()] if how == "並び"
                    else [int(m.group(1))])
            for n in nums:
                rows.append(dict(指標=fam, キー=key, 本数=n, 出どころ=f"{rel}:{i}",
                                 逐語=line.strip()[:90], 説明=note))
    import json as _json
    pj = _V9_ROOT / "config/cat_params_v9.json"
    prm = _json.loads(pj.read_text(encoding="utf-8")) if pj.exists() else {}
    for fam, key, keys, note in _V9_PERIOD_PARAMS:
        vals = [prm.get(k) for k in keys]
        if any(v is None for v in vals):
            continue
        val = int(vals[0]) if len(vals) == 1 else tuple(int(v) for v in vals)
        rows.append(dict(指標=fam, キー=key, 本数=val, 出どころ="config/cat_params_v9.json",
                         逐語=" / ".join(f"{k}={v}" for k, v in zip(keys, vals)), 説明=note))
    return rows


def _insp_v9_periods(cfg: dict, rows: list[dict] | None = None) -> list[str]:
    """検査11 V9 が使っている本数が、設定ファイルの本数に入っているかを1件ずつ照らす。
    rows は番人専用＝偽の一覧を入れて、この検査が実際に ❌ を出すことを確かめる。"""
    rows = _v9_periods() if rows is None else rows
    if not rows:
        return ["V9 の本数を1件も拾えなかった（拾い方の正規表現が実物とずれている疑い）"]
    print(f"  V9 の実物から拾った本数 {len(rows)} 件（1件ずつ どのファイルの何行目か を出す）")
    ng, miss = [], []
    for r in sorted(rows, key=lambda x: (x["指標"], str(x["本数"]))):
        have = cfg.get(r["キー"], [])
        want = r["本数"]
        if want is None:
            ng.append(f"{r['指標']}: 実物を読めない（{r['出どころ']}）")
            continue
        # 設定の値は 数字 か 数字の並び（macd_params のような組）
        ok = any((tuple(v) == want if isinstance(v, list) else v == want) for v in have)
        mark = "✅" if ok else "❌"
        print(f"     {mark} {r['指標']:12s} {str(want):12s} 設定 {r['キー']}={have}"
              f" … {r['説明']}（{r['出どころ']}）")
        print(f"         逐語: {r['逐語']}")
        if not ok:
            miss.append(f"{r['指標']} の {want}（設定 {r['キー']} に無い・{r['出どころ']}）")
    if miss:
        ng += [f"V9 が使っている本数が設定ファイルに無い: {x}" for x in miss]
    print(f"  → 足りない本数 {len(miss)} 件"
          + ("（V9 が組んでいる形を engine_tuner が作れない）" if miss else "＝V9 の本数は全部 入っている"))
    return ng


# ══ 検査13（価格を定数倍しても値が変わらないか＝H6・2026-08-11 新設・段6 の 6-9①）════════
# ★何のための検査か。H6（価格非依存）＝ドルの金額そのもので出る指標は、engine_tuner の材料に
#   できない。BTC の値段の帯が学習の時と本番で違うと、同じ閾値が別の意味になるためです。
#   だから帯や線は「終値からの距離%」、値幅は「終値で割って%」に直してから材料にしています
#   （段6 の12段の⑤＝旧 6-3）。**この検査は、それが全部の列でできているかを実測で確かめます。**
# ★やり方＝4本値（始値・高値・安値・終値）を定数倍して、全部の列を計算し直す。
#   %や比に直してあれば値は変わりません。ドルの金額のまま残っていれば値が変わります。
#   ★文字（列名に % が付いているか）で数えません。実際に計算し直して比べます。
_H6_FACTORS = (2.0, 0.5)      # 値段を2倍にした場合と半分にした場合の両方で見る
_H6_RTOL = 1e-8               # これ以下のずれは小数の丸め（同じとみなす）


def _price_scale_check(bars: pd.DataFrame, cfg: dict, catalog: list | None = None,
                       rows: int = 3000) -> dict:
    """4本値を定数倍して全列を計算し直し、値が変わる列（＝ドルの金額のまま）を出す。"""
    cat = catalog or build_catalog(cfg)
    _nm, a0, b0 = _insp_windows()[0]                    # 値決め窓（採点窓は1バーも使わない）
    win = bars.loc[(bars.index >= a0) & (bars.index < b0)].iloc[-rows:]
    bad, ok, skip = [], [], []
    base = {}
    for name, fn, _d in cat:
        try:
            s = pd.to_numeric(fn(win), errors="coerce")
            base[name] = None if s is None else s.to_numpy(dtype=float)
        except Exception as e:                          # noqa: BLE001
            base[name] = None
            skip.append((name, f"計算できず: {str(e)[:40]}"))
    for k in _H6_FACTORS:
        w2 = win.copy()
        for c in ("open", "high", "low", "close"):
            w2[c] = w2[c] * k                           # 出来高は触らない（値段の単位だけを見る）
        for name, fn, _d in cat:
            if base.get(name) is None:
                continue
            try:
                v2 = pd.to_numeric(fn(w2), errors="coerce").to_numpy(dtype=float)
            except Exception as e:                      # noqa: BLE001
                skip.append((name, f"定数倍のあとで計算できず: {str(e)[:40]}")); continue
            v1 = base[name]
            m = np.isfinite(v1) & np.isfinite(v2)
            if m.sum() == 0:
                skip.append((name, "比べられる値が無い（全部 欠け）")); continue
            # ★ずれの大きさは「その列のふつうの大きさ」と比べる（2026-08-11 に直した）。
            #   前は1本ずつの値そのもので割っていたので、値がほぼ 0 の足（BOP の実例＝高値と安値の
            #   差が 0.01・終値と始値の差が 0 で、値が 2e-14）で 小数の丸めの差が大きな比に見えて
            #   誤って ❌ を出した（実測＝3,000本のうち5本）。
            scale = float(np.median(np.abs(v1[m])))
            denom = np.maximum(np.abs(v1[m]), max(scale, 1e-12))
            rel = float(np.max(np.abs(v2[m] - v1[m]) / denom))
            if rel > _H6_RTOL:
                bad.append(dict(名前=name, 倍率=k, 最大のずれ=rel,
                                比=float(np.median(v2[m] / np.where(v1[m] == 0, np.nan, v1[m])))))
            elif k == _H6_FACTORS[0]:
                ok.append(name)
    return dict(ok=ok, bad=bad, skip=skip, rows=len(win), n=len(cat))


def _insp_price_scale(bars: pd.DataFrame, cfg: dict, catalog: list | None = None) -> list[str]:
    """検査13 価格を定数倍しても値が変わらないか（H6）。変わる列が1つでもあれば ❌。"""
    r = _price_scale_check(bars, cfg, catalog)
    print(f"  値決め窓の {r['rows']} 本で、4本値を {_H6_FACTORS[0]} 倍と {_H6_FACTORS[1]} 倍にして"
          f" 全 {r['n']} 種を計算し直した（出来高は触らない）")
    print(f"  ★値が変わらなかった列（＝%や比に直せている）= {len(r['ok'])} 種"
          f" ／ ★値が変わった列（＝ドルの金額のまま）= {len({b['名前'] for b in r['bad']})} 種")
    if r["skip"]:
        print(f"  比べられなかった列 {len(r['skip'])} 件")
        for nm, why in r["skip"][:10]:
            print(f"     ・{nm}: {why}")
    for b in r["bad"]:
        print(f"     ❌ {b['名前']}: 値段を {b['倍率']} 倍にすると値が変わる"
              f"（相対のずれ 最大 {b['最大のずれ']:.3g}・値の比の中央値 {b['比']:.4g}）")
    return [f"H6 違反の疑い: {b['名前']}（値段を {b['倍率']} 倍にすると値が変わる）"
            for b in r["bad"]]


# ══ 検査12（材料どうしの重複の総当たり・2026-08-11 新設・段6 の 6-9③）═══════════════════
# ★何のための検査か。まこさん決定（2026-08-09・逐語「他にも同じ挙動の指標があれば紛らわしいので
#   片方を省いていく」）を機械で回せる形にする。前は毎回その場で書いていて、何が重複だったかの
#   記録が残らなかった（2026-08-10 の「既存12列ぶん」が何かを、次のセッションが再現できなかった）。
# ★2つの見方で測る。どちらも「engine_tuner にとって同じ条件になるか」を見ている。
#   ①値そのものの相関（ピアソン）＝片方を定数倍して定数を足すと重なる組。
#   ②順位の相関（スピアマン）＝『値 ≥ 閾値』の形にしたとき、同じ足で同じ判定になる組。
#     ★終値で割る形（比）が入ると①では捕まらない（教訓 L-438）ので②が要る。
# ★総当たりは行列の掛け算で出す（1組ずつ回さない）＝列 564 でも数秒。
_DUP_NEAR = 0.999      # これを超える組を「近い組」として一覧に出す（L-438 の hwc は 0.999973 だった）
_DUP_SAME = 0.99999    # これを超える組は「実質 同じもの」＝省く候補
# ★計算に使う本数（検査12 と、場面を分ける材料の順位づけ M2-3-3 が共有する）。
#   2026-08-22 に定数へ出した＝同じ数字を2か所に書き写すと片方だけ直って黙って腐るため（教訓 L-519）。
#   値は 2026-08-11 の実測のまま変えていない（下の _dup_pairs の説明が出どころ）。
_DUP_CALC_ROWS = 60000   # 列を作る本数（値決め窓の後ろから）
_DUP_ROWS = 20000        # そのうち実際に測る本数（暖機を除くため後ろから取る）


def _corr_matrix(x: np.ndarray) -> np.ndarray:
    """列どうしの相関の総当たり（掛け算1回で出す）。列は標準化してから内積を取る。"""
    z = x - x.mean(axis=0, keepdims=True)
    s = z.std(axis=0, ddof=0, keepdims=True)
    s[s == 0] = np.nan                                  # 動かない列は相関を出さない
    z = z / s
    return (z.T @ z) / len(z)


def _dup_pairs(bars: pd.DataFrame, cfg: dict, catalog: list | None = None,
               tf: str = "5m", rows: int = _DUP_ROWS, calc_rows: int = _DUP_CALC_ROWS) -> dict:
    """材料の列を値決め窓で作り、重複の組を総当たりで出す。戻り＝機械が読む形。

    ★calc_rows＝計算に使う本数（値決め窓の後ろから）。値決め窓 158,000本 の全部で 561列 を作ると
      時間もメモリも足りない（2026-08-11 実測＝走行が途中で落ちた）。60,000本＝約208日ぶんで、
      いちばん長い暖機（200本）の 300倍 あるので、重複の判定には十分。
    ★rows＝そのうち相関を取る本数（暖機を除くため後ろから取る）。
    """
    cat = catalog or build_catalog(cfg)
    _nm, a0, b0 = _insp_windows()[0]                    # 値決め窓（採点窓は1バーも使わない）
    win = bars.loc[(bars.index >= a0) & (bars.index < b0)].iloc[-calc_rows:]
    vals, names, skipped, warm = [], [], [], {}
    for name, fn, _d in cat:
        try:
            s = pd.to_numeric(fn(win), errors="coerce")
        except Exception as e:                          # noqa: BLE001
            skipped.append((name, f"計算できず: {str(e)[:40]}")); continue
        if s is None:
            skipped.append((name, "None を返した")); continue
        _fin = np.isfinite(s.to_numpy(dtype=float))
        warm[name] = int(np.argmax(_fin)) + 1 if _fin.any() else 10**9   # 値が出はじめる本数（実測）
        v = s.to_numpy(dtype=float)[-rows:]
        if len(v) < rows or not np.isfinite(v).all():
            skipped.append((name, "この本数では欠けが残る（暖機が終わらない）")); continue
        if np.nanstd(v) == 0:
            skipped.append((name, "値が動かない（この窓では一定）")); continue
        vals.append(v); names.append(name)
    if len(names) < 2:
        return dict(names=names, skipped=skipped, pairs=[], rows=0, tf=tf, warm=warm)
    x = np.column_stack(vals)
    try:
        from scipy.stats import rankdata as _rankdata
        r = _rankdata(x, axis=0)
    except Exception:                                   # noqa: BLE001
        r = np.argsort(np.argsort(x, axis=0), axis=0).astype(float)
    cp, cs = _corr_matrix(x), _corr_matrix(r)
    pairs = []
    iu = np.triu_indices(len(names), k=1)
    for i, j in zip(*iu):
        p, sp = abs(cp[i, j]), abs(cs[i, j])
        if not (np.isfinite(p) or np.isfinite(sp)):
            continue
        top = max(p if np.isfinite(p) else 0.0, sp if np.isfinite(sp) else 0.0)
        if top >= _DUP_NEAR:
            pairs.append(dict(a=names[i], b=names[j], pearson=float(cp[i, j]),
                              spearman=float(cs[i, j]),
                              判定="実質 同じもの" if top >= _DUP_SAME else "近い組"))
    pairs.sort(key=lambda d: -max(abs(d["pearson"]), abs(d["spearman"])))
    return dict(names=names, skipped=skipped, pairs=pairs, rows=int(x.shape[0]), tf=tf, warm=warm)


def _insp_duplicates(bars: pd.DataFrame, cfg: dict, catalog: list | None = None) -> list[str]:
    """検査12 材料どうしの重複の総当たり（値決め窓・5分足）。
    ❌ は出さない＝どちらを省くかは まこさんが決める（CC が勝手に消さない）。一覧を毎回 出す。"""
    r = _dup_pairs(bars, cfg, catalog)
    print(f"  値決め窓の {r['rows']} 本 × {len(r['names'])} 列（{r['tf']}）を総当たり"
          f"＝{len(r['names']) * (len(r['names']) - 1) // 2:,} 通り")
    if r["skipped"]:
        print(f"  この窓では測れなかった列 {len(r['skipped'])} 件（暖機が終わらない・値が動かない ほか）")
        for nm, why in r["skipped"][:20]:
            print(f"     ・{nm}: {why}")
    same = [p for p in r["pairs"] if p["判定"] == "実質 同じもの"]
    near = [p for p in r["pairs"] if p["判定"] == "近い組"]
    print(f"  ★実質 同じもの（|相関| ≥ {_DUP_SAME}）= {len(same)} 組"
          f" ／ 近い組（≥ {_DUP_NEAR}）= {len(near)} 組")
    for p in same + near:
        print(f"     [{p['判定']}] {p['a']} ↔ {p['b']}"
              f"（値の相関 {p['pearson']:+.7f} ／ 順位の相関 {p['spearman']:+.7f}）")
    if same:
        print("  ── まとまりごとの「残す／省く」（まこさん OK 2026-08-11・逐語「同じ挙動ならどちらかは"
              "使わないようにしていいよ」）──")
        print("     決まり1: V9 と採用中の戦略が実際に書いている行が多い方を残す")
        print("       （根拠＝まこさん逐語 2026-08-08「最低限v9で使ってるロジックを組めることは必要」）")
        print("     決まり2: 同点なら、業界のライブラリに同じ関数が在る方を残す")
        print("     決まり3: それも同点なら、暖機（値が出はじめる本数）が短い方を残す（実測）")
        print("     決まり4: それも同点なら、名前の並び順で前の方")
        for grp in _dup_groups(same):
            keep, why, tbl = _dup_keep_of_group(grp, r.get("warm"))
            drops = [g for g in grp if g != keep]
            print(f"     ・残す {keep} ／ 省く {'・'.join(drops)}")
            print(f"         決め手: {why}")
            print(f"         内訳: {tbl}")
    print("  ⚠️ 省く作業そのものは、この検査では しない（材料カタログを直すのは別の手順）")
    return []


# ══ 重複の組で「残す側」を決める材料（2026-08-11・3回 間違えたので探し方そのものを変えた）════
# ★経緯を残す。CC は「その指標を使っているか」を、ソースの文字探しで数えようとして3回 外した。
#   ①材料カタログの列名とレシピの family 名だけを探し、V9 のファイルを1つも見なかった（BB が 0 行）
#   ②文字の並びが入っていれば数える形にしたら、短い名前が別の単語に当たった（AR が 1,246 行）
#   ③語の区切りで探す形にしたら、今度は `bb_middle` のような書き方が外れた（BB が 137 → 23 行）
# ★やめて、実物の一覧との「一致」で判定する形にした（あいまいな探し方をしない）。
#   (a) V9 が実際に計算している指標か＝検査11 が V9 の実物から機械で拾った一覧
#   (b) engine_tuner のレシピ・E38 のロジックが family として使っているか＝json を読んで一致で判定
_V9_LABEL_TO_FAMILIES: dict[str, tuple[str, ...]] = {
    # 検査11 が出す「指標」の呼び名 → 材料カタログの family（この対応だけは手で書く・1か所に集約）
    "RCI": ("RCI",), "ADX": ("ADX", "DI差"), "ATR%": ("ATR%",), "RSI": ("RSI",),
    "BB": ("BB%b", "BB幅"), "EMA": ("close vs EMA", "EMA傾き"),
    "Stoch": ("Stoch%K", "Stoch%D"), "MACD": ("MACD線%", "MACDヒスト%", "MACDシグナル線%"),
    # ★entry_risk_score は 2026-08-11 まで "realized_vol" の名前で realized_vol に対応づけていた。
    #   実測（検査14）で うちの BB幅(20,2.0) と一致（値 +0.9999464／順位 +0.9999952）＝realized_vol は別物。
    #   ここは「V9 が実際に計算している family」の一覧＝重複の組で残す側を決める材料になるので、
    #   間違ったまま置くと『V9 が使っている』を理由に別の列を残してしまう。
    "fib位置": ("fib位置",), "entry_risk_score": ("BB幅",),
}


def _v9_families() -> set:
    """V9 が実際に計算している指標の family（検査11 が実物から拾った一覧から引く）。"""
    out = set()
    for r in _v9_periods():
        out.update(_V9_LABEL_TO_FAMILIES.get(r["指標"], ()))
    return out


def _recipe_families() -> set:
    """engine_tuner のレシピ・E38 のロジックが材料として使っている family（json の一致で判定）。"""
    import json as _json
    root = pathlib.Path(__file__).resolve().parent
    files = list((root / "recipes").glob("*.json")) if (root / "recipes").exists() else []
    if (root / "e38_logics.json").exists():
        files.append(root / "e38_logics.json")
    out = set()

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("family"), str):
                out.add(o["family"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    for f in files:
        try:
            walk(_json.loads(f.read_text(encoding="utf-8")))
        except Exception:                                        # noqa: BLE001
            pass
    return out


# ★（古い数え方・使っていない）その指標を実際に書いている行を数える（2026-08-11 に作り直した）。
#   前は「材料カタログの列名」と「レシピの family 名」だけを探していたので、
#   ①V9 のファイルを1つも見ていない ②戦略が自前の列名（bb_middle・bb_sig ほか）で持っている分を
#   見落とす、の2つで BB を「使っていない」と数えた（実測＝BB は V9 だけで 69 行）。
_USE_PATTERNS: dict[str, tuple[str, ...]] = {
    "BB%b": ("bollinger", "bb_"), "BB幅": ("bb_width", "bollinger"),
    "zscore": ("zscore", "z_score"), "stdev%": ("stdev", "std("),
    "close vs SMA": ("sma", "rolling"), "close vs EMA": ("ema_", "ewm"),
    "RSI": ("rsi",), "RCI": ("rci",), "ADX": ("adx",), "ATR%": ("atr",),
    "Stoch%K": ("stoch",), "Stoch%D": ("stoch",), "MACD線%": ("macd",),
    "volume_ratio": ("volume_ratio", "vol_ratio"), "ROC": ("roc", "pct_change"),
}


def _dup_used_in_strategies(name: str) -> dict:
    """その指標を V9 と採用中の戦略が実際に書いている行の数（ファイルごとの内訳つき）。"""
    import subprocess
    root = pathlib.Path(__file__).resolve().parents[2]
    files = {
        "V9": root / "strategies" / "cat_v9_decider.py",
        "V9共通": root / "cat" / "indicators.py",
        "E37": root / "scripts" / "priority_rebuild" / "e37_range_scalp.py",
        "E36": root / "scripts" / "priority_rebuild" / "e36_short_oscillation.py",
        "E38": root / "scripts" / "priority_rebuild" / "e38_logic_parts.py",
        "レンジ土台": root / "scripts" / "priority_rebuild" / "e34_range_base.py",
        "レシピ": root / "scripts" / "priority_rebuild" / "recipes",
    }
    ent = iref.find(name)[0]
    fam = ent["family"] if ent else name
    pats = list(_USE_PATTERNS.get(fam, ())) + [name, fam]
    # ★語の区切りで探す（2026-08-11 に直した）。前は文字の並びが入っていれば数えていたので、
    #   短い名前が別の単語の中に当たった（実測＝`AR` が 1,246 行＝params・array などに当たっていた）。
    def _rx(p: str) -> str:
        return "(^|[^A-Za-z0-9_%])" + re.escape(p.rstrip("_")) + "([^A-Za-z0-9_]|$)"
    out, total = {}, 0
    for label, path in files.items():
        if not path.exists():
            continue
        n = 0
        for pat in dict.fromkeys(pats):
            if len(pat) < 2:
                continue
            try:
                cmd = ["grep", "-rcE", "--", _rx(pat), str(path)]
                if len(pat) > 3:                                  # 短い名前は大文字小文字を区別する
                    cmd.insert(2, "-i")
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                for ln in r.stdout.splitlines():
                    tail = ln.rsplit(":", 1)[-1].strip()
                    if tail.isdigit():
                        n += int(tail)
            except Exception:                                    # noqa: BLE001
                pass
        out[label] = n
        total += n
    return dict(計=total, 内訳=out)


def _dup_groups(pairs: list[dict]) -> list[list[str]]:
    """「同じもの」の組をつなげて、ひとまとまりにする（A=B・B=C なら A・B・C で1組）。

    ★2026-08-11 に足した。理由＝組ごとに別々に「残す方」を選ぶと、同じ列を
      片方の組では「残す」・別の組では「省く」と言ってしまう（実測で2件 起きた）。
    """
    parent: dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p in pairs:
        a, b = find(p["a"]), find(p["b"])
        if a != b:
            parent[a] = b
    grp: dict[str, list[str]] = {}
    for x in list(parent):
        grp.setdefault(find(x), []).append(x)
    return [sorted(v) for v in grp.values() if len(v) > 1]


def _dup_used_in_repo(name: str) -> int:
    """その列を、採用中の戦略・レシピ・設定が使っているか（使っている物を消さないため）。

    ★2つの書き方を両方 探す（2026-08-11 に直した）。
      ①列の名前そのまま（例＝`volume_ratio20`）
      ②レシピの書き方＝family と 数字を分けて持つ形（例＝`"family": "volume_ratio"` ＋ `"param": 20`）。
      ★前は①だけを探していたので、レシピが実際に使っている列を「使っていない」と誤って数えた
        （実測＝volume_ratio20 を『省く』側に出してしまった。実物では e38 のレシピが使っている）。
    """
    import subprocess
    root = pathlib.Path(__file__).resolve().parents[0]
    targets = [str(root / x) for x in ("recipes", "e38_logics.json", "e38_logic_parts.py",
                                       "e37_range_scalp.py", "engine_tuner_exec.py")]
    targets = [t for t in targets if pathlib.Path(t).exists()]
    ent, prm = iref.find(name)
    pats = [name]
    if ent is not None:
        pats.append(f'"{ent["family"]}"')                        # レシピの family の書き方
    n = 0
    for pat in pats:
        try:
            r = subprocess.run(["grep", "-rIl", "-F", "--", pat, *targets],
                               capture_output=True, text=True, timeout=60)
            n += len([x for x in r.stdout.splitlines() if x.strip()])
        except Exception:                                        # noqa: BLE001
            pass
    return n


def _dup_keep_of_group(grp: list[str], warm: dict | None = None) -> tuple[str, str, str]:
    """まとまりの中から、残す1本を選ぶ。★2026-08-11 に作り直した（前の版は2つ間違っていた）。

    まこさんの決定＝「同じ挙動の指標があれば片方を省いてよい」（2026-08-09・2026-08-11）。
    ★どちらを残すかの順番は、まこさんの決定から引く。
      決まり1＝**V9 と採用中の戦略が実際に書いている行が多い方を残す**
        （根拠＝まこさん逐語 2026-08-08「最低限v9で使ってるロジックを組めることは必要」。
          使っている物を消すと、その形が組めなくなる）
      決まり2＝同点なら、業界のライブラリに同じ関数が在る方を残す（業界の名前を残す）
      決まり3＝それも同点なら、暖機（値が出はじめる本数）が短い方を残す（実測）
      決まり4＝それも同点なら、名前の並び順で前の方

    ★前の版の間違い（2026-08-11・まこさん指摘）
      ①使っている所を「材料カタログの列名」と「レシピの family 名」だけで探し、V9 のファイルを
        1つも見ていなかった＝BB を「使っていない」と数えた（実物では V9 だけで 72 行）。
      ②暖機を「名前の中の数字を全部 足す」で近似し、標準偏差の 2.0 のような本数でない数字まで
        足していた（実測＝BB%b(20,2.0) も zscore20 も暖機は同じ 20 本目）。
    """
    v9f, rcf = _v9_families(), _recipe_families()
    used, ind, wm, why1 = {}, {}, {}, {}
    for g in grp:
        ent = iref.find(g)[0]
        fam = ent["family"] if ent else g
        tags = []
        if fam in v9f:
            tags.append("V9 が計算している")
        if fam in rcf:
            tags.append("レシピが材料に使っている")
        used[g] = len(tags)
        why1[g] = "・".join(tags) or "どちらでもない"
        ind[g] = bool(iref.INDUSTRY_MAP.get(fam, ((), ""))[0]) if ent else False
        wm[g] = (warm or {}).get(g, 10**9)
    tbl = " ／ ".join(f"{g}（{why1[g]}・業界の関数 {'有' if ind[g] else '無'}"
                     + (f"・暖機 {wm[g]} 本目" if wm[g] < 10**9 else "") + "）" for g in grp)
    best = max(used.values())
    cand = [g for g in grp if used[g] == best]
    if best > 0 and len(cand) == 1:
        return cand[0], f"決まり1＝{why1[cand[0]]}（ほかは使われていない）", tbl
    c2 = [g for g in cand if ind[g]] or cand
    if len(c2) == 1:
        return c2[0], "決まり2＝業界のライブラリに同じ関数が在る", tbl
    c3 = sorted(c2, key=lambda g: (wm[g], g))
    if len({wm[g] for g in c2}) > 1:
        return c3[0], f"決まり3＝暖機がいちばん短い（{wm[c3[0]]} 本目）", tbl
    return c3[0], "決まり4＝上の3つが同点＝名前の並び順で前の方", tbl


def _insp_stage_plan(only, stage_keys: list) -> tuple[list, bool]:
    """`--only` の指定から「走らせる段」と「検査5 を走らせるか」を決める。

    ★2026-09-08（監査 cp31 の Major 2・設計書 insp5-path-and-tidy-head-20260908 の F）
      ＝この判定を1か所に集めた。本体（inspect_data）も番人（T-k）も、ここを呼ぶ。
      直す前＝本体の中に直に書いてあり、検査5 が走る道は2つだけだった
        （①検査5 だけを名指ししたとき ②検査6 の直前）。
        `--only 5,7` は走らせる段が「検査7」だけになるので、どちらにも当たらず、
        検査5 は黙って走らなかった（監査 cp31 が実測・3秒で終わった）。
      直した後＝検査5 を名指ししたら、ほかの検査を一緒に指定していても走らせる。
    戻り＝(走らせる段の鍵の一覧, 検査5 を走らせるか)。
    ★指定が無ければ、全部の段と検査5 を走らせる（今までどおり）。
    """
    if not only:
        return list(stage_keys), True
    want = {"検査" + x.strip() for x in str(only).split(",") if x.strip()}
    unknown = want - set(stage_keys) - {"検査5"}
    if unknown:
        raise SystemExit(f"[--only] そんな検査は無い: {sorted(unknown)}")
    return [k for k in stage_keys if k in want], ("検査5" in want)


def _tol_saturation_cells(k, x) -> list:
    """検査16 の1マス＝倍率 k × ATR% の並び x の「値の出ている本数・下端に張り付いた割合・上端に張り付いた割合」（文字）。

    ★2026-09-26（監査 CP44 の修正 4）＝数え方を1か所に置き、番人 T-A5 が既知答えで確かめる。
    ★張り付き＝下端より小さい（下端に置き換わる）／上端より大きい（上端に置き換わる）。ちょうど端の値は数えない。
    """
    v = float(k) * np.asarray(x, dtype=float)
    ok = ~np.isnan(v)
    nn = int(ok.sum())
    if nn == 0:
        return ["0", "—", "—"]
    return [str(nn), f"{float((v[ok] < _SR_ATR_TOL_LO).mean()) * 100:.1f}%",
            f"{float((v[ok] > _SR_ATR_TOL_HI).mean()) * 100:.1f}%"]


def _insp_tol_saturation(bars: pd.DataFrame, cfg: dict) -> list[str]:
    """検査16＝帯の許容幅（倍率 × ATR%）が、上下限（0.15%〜0.6%）の端に張り付いた割合を、足ごとに出す。

    ★2026-09-26（M2-E-5・束2・設計書 m2e-bundle2-20260926）。next_step §6 の136番の「先にやること」。
    ★判定しない（報告だけ）＝どこまで張り付いてよいかの線は まこさんが決める（まこさん決定 2026-09-26 の①）。
    ★2つの形を並べる＝①その足の ATR%（2026-09-06 に外した形・5分足では下端に張り付いた）
                      ②1時間足の ATR%（S-Rタッチ1時間ATR の形・_atr_pct_1h_on）
    ★張り付き＝倍率 × ATR% が下端より小さい（下端に置き換わる）／上端より大きい（上端に置き換わる）バーの割合。
      値が出ていないバー（助走・最初の1時間足が閉じる前）は数えない。
    ★値決め窓だけを使う（採点窓が1本でも混ざれば止まる）。
    """
    _nm, a0, b0 = _insp_windows()[0]
    win = bars.loc[(bars.index >= a0) & (bars.index < b0)]
    _assert_search_window_only(win.index, "検査16")
    one = (load_1m(win.index[0], win.index[-1])
           if any(t in cfg["timeframes"] for t in SUB_5M_TF) else None)
    print(f"  値決め窓 {win.index.min()} 〜 {win.index.max()} の {len(win)} 本（5分足）"
          f" ／ 上下限 {_SR_ATR_TOL_LO * 100:.2f}%〜{_SR_ATR_TOL_HI * 100:.2f}%（出どころ＝設定の sr_tol の説明に写した逐語）")
    print("  ①＝その足の ATR%（2026-09-06 に外した形） ／ ②＝1時間足の ATR%（S-Rタッチ1時間ATR の形）")
    print("  | 足 | ATRの期間 | 倍率 | ①の本数 | ①下端 | ①上端 | ②の本数 | ②下端 | ②上端 |")
    print("  |---|---|---|---|---|---|---|---|---|")
    for tf in cfg["timeframes"]:
        src, _closed = insp5_frame(win, tf, one)
        for an in cfg["atr_periods"]:
            own = (_atr(src.high, src.low, src.close, an) / src.close).to_numpy(float)
            h1 = _atr_pct_1h_on(src, an)
            for k in cfg["sr_atr1h_k"]:
                cells = _tol_saturation_cells(k, own) + _tol_saturation_cells(k, h1)
                print(f"  | {tf} | {an} | {k} | " + " | ".join(cells) + " |")
    return []


def inspect_data(bars_csv: str, config_path: str | None = None, only: str | None = None,
                 cols: str | None = None) -> None:
    """データと指標の検査（歩0）＝5段を順に走らせ、まとめを機械出力する。❌ が1つでもあれば終了コード1。

    only＝走らせる検査の番号（例 "14" や "11,14"）。指定した検査だけを走らせる。
    cols＝測る材料の列を名前で絞る（例 "RSI21傾き3" や "RSI.*傾き" ＝正規表現）。
    ★何のために足したか（2026-08-11）。全部 通すと 2時間10分 かかる（実測）ので、
      1つの検査を直した時の確かめが1日1回しかできなかった。
      ★列を8本 足しただけなのに 4,887列 すべてを測り直していた（2026-08-11 の反省）。
      材料を足した時に確かめたいのは、足した列が①値段に依存しないか ②未来を見ていないか
      ③計算式が合っているか の3つで、既に在る列は変えていないので測り直す必要がない。
    ★走らせた範囲（検査の番号・列の絞り）は必ず出力の冒頭に印字する＝一部だけ走らせたことを黙らない。"""
    cfg = load_config(config_path)
    bars = pd.read_csv(bars_csv, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    print("#" * 100)
    print("# データと指標の検査（歩0・read-only・結果は機械出力＝この出力が正・まこさん OK 2026-07-30）")
    print(f"# 対象: {bars_csv}（{len(bars)} 行 / {bars.index.min()} 〜 {bars.index.max()}）")
    print(f"# 設定: {cfg['_source']} ／ 足 {cfg['timeframes']} ／ 指標 {len(build_catalog(cfg))} 種")
    print("# 窓（periods.py 正本）: " + " ／ ".join(
        f"{nm} {a.date()}〜{(b - pd.Timedelta('1D')).date()}" for nm, a, b in _insp_windows()))
    print(f"# 検査の段は {len(INSPECT_SECTIONS)} 段（下のまとめに全部 出る）。"
          "上流で間違いが出たら下流の結果は全部疑う。売買しない・値決めしない・審判に触れない。")
    print("#" * 100)
    fails = {}
    # ★列の絞り（--cols）。材料を足した時、足した列だけを測るために使う。
    #   絞れる検査だけに効く（材料の一覧を受け取れる検査＝3・4・9・12・13・14）。
    #   絞った時は、その事実と対象の列名を必ず印字する（黙って一部だけ測らない）。
    cat_all = build_catalog(cfg)
    cat = cat_all
    if cols:
        rx = re.compile(cols)
        cat = [c for c in cat_all if rx.search(c[0])]
        if not cat:
            raise SystemExit(f"[--cols] その名前の列は材料に無い: {cols}")
        print(f"# ⚠️ --cols 指定＝材料 {len(cat_all)} 種のうち {len(cat)} 種だけを測る"
              f"（ほかの列は測っていない）: {[c[0] for c in cat]}")
    stages = [("検査1", INSPECT_SECTIONS[0], lambda: _insp_source(bars)),
              ("検査2", INSPECT_SECTIONS[1], lambda: _insp_resample(bars, cfg)),
              ("検査3", INSPECT_SECTIONS[2], lambda: _insp_indicator_stage(bars, cfg, cat)),
              ("検査4", INSPECT_SECTIONS[3], lambda: _insp_lookahead(bars, cfg, cat))]
    stages += [("検査6", INSPECT_SECTIONS[5], lambda: _insp_demand(bars)),
               ("検査7", INSPECT_SECTIONS[6], lambda: _insp_axis(cfg)),
               ("検査8", INSPECT_SECTIONS[7], lambda: _insp_range_geo(bars, cfg)),
               ("検査9", INSPECT_SECTIONS[8], lambda: _insp_direction_gap(cfg, cat)),
               ("検査10", INSPECT_SECTIONS[9], lambda: _insp_industry(cfg)),
               ("検査11", INSPECT_SECTIONS[10], lambda: _insp_v9_periods(cfg)),
               ("検査12", INSPECT_SECTIONS[11], lambda: _insp_duplicates(bars, cfg, cat)),
               ("検査13", INSPECT_SECTIONS[12], lambda: _insp_price_scale(bars, cfg, cat)),
               ("検査14", INSPECT_SECTIONS[13], lambda: _insp_v9_columns(bars, cfg, cat))]
    # ★2026-08-29（M2-A-2・まこさん承認 9449761de0135c8f）＝検査15 を足す（判定なし・報告だけ）。
    stages += [("検査15", INSPECT_SECTIONS[14], lambda: _insp_regime_label_oneway(bars))]
    # ★2026-09-26（M2-E-5・束2・設計書 m2e-bundle2-20260926）＝検査16 を足す（判定なし・報告だけ）。
    stages += [("検査16", INSPECT_SECTIONS[15], lambda: _insp_tol_saturation(bars, cfg))]
    # ★2026-09-08（監査 cp30 の別枠1）＝検査5 を名指しできるようにした。
    #   直す前＝検査5 は上の一覧に入っておらず、検査6 の直前に必ず走る作りだった。
    #   だから `--only 5` と打つと「そんな検査は無い」で止まり、
    #   検査5 だけを走らせる道が無かった（監査が実際に当たった）。
    #   直した後＝`--only 5` は「検査5 だけを走らせる」。`--only 6` は今までどおり
    #   検査5 を挟んでから検査6 を走らせる（順番の意味を変えない）。
    # ★2026-09-08（監査 cp31 の Major 2・別枠 I）＝判定を `_insp_stage_plan` へ集めた。
    #   走ったかどうかは `ran5` の1つの値で持ち、まとめの行もその値を見る
    #   （＝走っていない検査の行を出さない）。
    _keys, only5 = _insp_stage_plan(only, [k for k, _t, _r in stages])
    if only:
        _shown = sorted(set(_keys) | ({"検査5"} if only5 else set()))
        print(f"# ⚠️ --only 指定＝{_shown} だけを走らせる（ほかの検査は走っていない）")
    stages = [s for s in stages if s[0] in _keys]
    ran5 = False
    if only5:                                  # ★検査5 を名指ししたら、ほかの検査と一緒でも先に走らせる
        _h(INSPECT_SECTIONS[4])
        _insp_samples(bars, cfg, cat)
        ran5 = True
        if not stages:                         # 検査5 だけを名指しされたとき
            # ★2026-09-08（監査 cp32 の別枠 G）＝ここでも「検査のまとめ」の見出しを出す。
            #   直す前は、この道だけ見出しが出なかった（早く戻るため）＝見た目がそろわなかった。
            print("\n" + "=" * 100)
            print("検査のまとめ（❌＝直すまで下流を信じない ／ ⚠️＝データの事実の報告）")
            print("  検査5: 判定なし（欠損・助走・有効標本数の報告＝歩2 の適合制約の基礎データ）")
            print("=" * 100)
            return
    for key, title, run in stages:
        if key == "検査6" and not ran5:        # 検査5（判定なしの報告）を順番どおり挟む（二重に走らせない）
            _h(INSPECT_SECTIONS[4])
            _insp_samples(bars, cfg, cat)      # ★2026-09-08（別枠2）＝絞った一覧を渡す
            ran5 = True
        _h(title)
        fails[key] = run()
        if fails[key]:
            print(f"  ⚠️ {key} で問題が出た＝これより下流の段の結果は全部疑う")
    print("\n" + "=" * 100)
    print("検査のまとめ（❌＝直すまで下流を信じない ／ ⚠️＝データの事実の報告）")
    bad = 0
    for key, _t, _r in stages:
        if fails[key]:
            for x in fails[key]:
                print(f"  ❌ {key}: {x}")
            bad += len(fails[key])
        elif key == "検査15":
            # ★2026-08-29＝検査15 は判定しない（報告だけ）。「異常なし」と出すと、
            #   何かを判定して問題が無かったと読めてしまうので、そう書かない。
            print(f"  📄 {key}: 判定なし（報告だけ＝レンジの本当の正解は誰も持っていないため）")
        elif key == "検査16":
            # ★2026-09-26＝検査16 も判定しない（報告だけ）。どこまで張り付いてよいかの線は まこさんが決める。
            print(f"  📄 {key}: 判定なし（報告だけ＝張り付きの割合をどこまで許すかは まこさんが決める）")
        else:
            print(f"  ✅ {key}: 異常なし")
    # ★2026-09-08（監査 cp31 の別枠 I）＝検査5 が実際に走ったときだけ、この行を出す。
    #   直す前＝走らなくても必ず出たので、`--only 5,7`（検査5 が走らなかった）のときに嘘になった。
    if ran5:
        print("  検査5: 判定なし（欠損・助走・有効標本数の報告＝歩2 の適合制約の基礎データ・下限はまこさんが決める）")
    print("=" * 100)
    if bad:
        raise SystemExit(1)


# ══ 検査14（V9 の実物の列と、うちのカタログの列の対応を実測で決める・2026-08-11 新設）═════════
# ★何のための検査か。V9 の検算（gen_signal_families.py --v9-test）は「V9 の指標名 → うちの family 名」の
#   対応を手書きの表（V9_FAMILY_MAP）で持っている。手書きなので、外し方が2つ ある。両方 実際に起きていた。
#   ①名前が違うだけで中身は同じ列が「機械対応なし＝検算の対象外」に落ちる
#     ＝V9 の location_prev（直近20本の高安の中での終値の位置・cat_v9_decider.py:118-125）。
#       うちの fib位置20 が同じ形なのに、名前が違うので検算から外れていた。
#   ②名前が似ている別物を「同じ」と書いてしまう
#     ＝V9 の entry_risk_score は「終値のばらつき ÷ 終値」（同 :128-129）。
#       うちの realized_vol は「対数リターンのばらつき」＝別物。同じ形は「σ ÷ 終値」の側。
# ★だから対応を名前で決めない。V9 の実物（cat_v9_decider.preprocess）をそのまま呼んで列を作り、
#   うちのカタログの全列と総当たりで相関を取って、一番 近い列を実測で出す。
#   ＝教訓 L-434・L-438（実物の式を突き合わせずに、名前と説明から「同じ／別物」を決めた）を機械で塞ぐ。
# ★この検査は ❌ を出さない＝一覧と数字を出すだけ。合否は gen_signal_families.py --v9-test が出す。
#   材料を足す・省くも一切しない（read-only）。V9 のファイルは1バイトも変えない（改造禁止・CLAUDE.md）。
_V9_MATCH_SAME = 0.99999   # これを超えたら「うちのカタログに同じ意味の列が在る」
_V9_MATCH_NEAR = 0.99      # これを超えたら「近い列は在るが、同じではない」
_V9_INPUT_COLS = ("open", "high", "low", "close", "volume", "timestamp")


def _v9_preprocess_frame(bars: pd.DataFrame, calc_rows: int = 30000) -> tuple[pd.DataFrame, pd.DataFrame]:
    """V9 の実物（strategies/cat_v9_decider.preprocess）をそのまま呼んで、指標の列を作る。
    ★書き写さない＝実物を import して呼ぶ（写し間違いを構造的に無くす）。
    ★read-only＝発注しない・V9 のファイルは1バイトも変えない。戻り＝(値決め窓の5分足, V9 の指標の列)。"""
    import importlib.util
    import json as _json
    p = _V9_ROOT / "strategies/cat_v9_decider.py"
    if not p.exists():
        raise FileNotFoundError(f"V9 の実物が無い: {p}")
    spec = importlib.util.spec_from_file_location("_cat_v9_decider_readonly", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                                  # type: ignore[union-attr]
    pj = _V9_ROOT / "config/cat_params_v9.json"
    prm = _json.loads(pj.read_text(encoding="utf-8")) if pj.exists() else {}
    _nm, a0, b0 = _insp_windows()[0]                              # 値決め窓（採点窓は1バーも使わない）
    win = bars.loc[(bars.index >= a0) & (bars.index < b0)].iloc[-calc_rows:]
    out = mod.preprocess(win.reset_index(), prm)                  # preprocess は timestamp を列で欲しがる
    out.index = win.index                                         # 行の順も本数も変わらない（中で reset するだけ）
    keep = [c for c in out.columns
            if c not in _V9_INPUT_COLS and not c.startswith("filter_")
            and pd.api.types.is_numeric_dtype(out[c]) and not pd.api.types.is_bool_dtype(out[c])]
    return win, out[keep]


def _v9_price_kinds(bars: pd.DataFrame, calc_rows: int = 3000, k: float = 2.0) -> dict:
    """V9 の各列が『値段の単位』か（4本値を k 倍すると値も変わるか）を実測で分ける。
    ★検査13 と同じやり方。値段の単位の列は、うちは H6（価格非依存）で % の形に直して持っているので、
      『対応なし』と出ても材料の穴とは限らない＝その区別をこの欄で出す（隠さない）。"""
    _w1, a = _v9_preprocess_frame(bars, calc_rows)
    scaled = bars.copy()
    for c in ("open", "high", "low", "close"):
        if c in scaled.columns:
            scaled[c] = pd.to_numeric(scaled[c], errors="coerce") * k
    _w2, b = _v9_preprocess_frame(scaled, calc_rows)
    out = {}
    for c in a.columns:
        if c not in b.columns:
            continue
        u = pd.to_numeric(a[c], errors="coerce").to_numpy(dtype=float)
        v = pd.to_numeric(b[c], errors="coerce").to_numpy(dtype=float)
        m = np.isfinite(u) & np.isfinite(v)
        if not m.any():
            out[c] = "測れない"; continue
        rel = np.abs(u[m] - v[m]) / (np.abs(u[m]) + 1e-12)
        out[c] = "値段の単位" if float(np.nanmax(rel)) > 1e-9 else "値段に依らない"
    return out


def _v9_rank(a: np.ndarray) -> np.ndarray:
    """順位に直す（同じ値は平均順位）。順位の相関を出すために使う。"""
    try:
        from scipy.stats import rankdata as _rankdata
        return _rankdata(a, axis=0) if a.ndim == 2 else _rankdata(a)
    except Exception:                                             # noqa: BLE001
        return (np.argsort(np.argsort(a, axis=0), axis=0).astype(float) if a.ndim == 2
                else np.argsort(np.argsort(a)).astype(float))


def _v9_z(a: np.ndarray) -> np.ndarray:
    """列ごとに平均0・ばらつき1へ直す（相関を行列の掛け算1回で出すため）。"""
    z = a - a.mean(axis=0, keepdims=True)
    s = z.std(axis=0, ddof=0, keepdims=True)
    s[s == 0] = np.nan
    return z / s


# ── C-4｜うちの材料に「条件の部品」を当てた列とも比べる（2026-08-11・段C の C-4）──────────────
# ★なぜ要るか。V9 の rsi_slope_short は「RSI21 の3本差分」（cat_v9_decider.py:96 の
#   df["rsi_short"].diff(short_rsi_slope_n)／本数は同 :93-94 と config/cat_params_v9.json:41-42 で
#   SHORT_RSI_PERIOD=21・SHORT_RSI_SLOPE_N=3）。うちには RSI21 が在り、engine_tuner には
#   slope（いまの値 − n本前の値）という部品が在るので、組み合わせれば作れる。
#   ところが検査14 は「うちの列を、そのままの形でしか」比べていなかったので、これを材料の穴と誤報していた。
# ★当てる部品は materials.md ★6 の13個から作る4種だけ（CC が思いつきで足さない）。
#   そのまま＝value ／ n本前との差＝value・lag・sub（slope の中身）／ m本の平均＝value・ma ／
#   m本の平均の n本前との差＝value・ma・lag・sub（slope_avg の中身）。
# ★n と m の数字は recipes/search_limits.json の int_grid から機械で引く（CC が数字を決めない）。
# ★式は実行器 engine_tuner_exec.py:777-791 と同じ（slope＝a − n本前 ／ slope_avg＝MA(m) − その n本前）。
# ★限界（先に書く）＝当てるのは部品を1〜2段 重ねたところまで。3段以上は見ない。
#   ＝「本当は作れるのに、穴だと言う」ことは残る。逆（作れないのに、穴でないと言う）は起きない。
#   ＝言い過ぎる側に倒している。
_V9_PART_GRID_PATH = pathlib.Path(__file__).resolve().parent / "recipes" / "search_limits.json"


def _v9_part_grid() -> list[int]:
    """部品の n・m に使う数字を recipes/search_limits.json の int_grid から引く（手で書かない）。"""
    import json as _json
    g = _json.loads(_V9_PART_GRID_PATH.read_text(encoding="utf-8")).get("int_grid")
    if not g:
        raise ValueError(f"int_grid が読めない: {_V9_PART_GRID_PATH}")
    return [int(x) for x in g]


def _v9_part_variants(grid: list[int]) -> list[dict]:
    """当てる部品の組み合わせ（4種）。warm＝暖機（先頭の何行が使えないか）。"""
    def _ma(a: np.ndarray, m: int) -> np.ndarray:              # 実行器と同じ pd の rolling 平均
        return pd.DataFrame(a).rolling(m).mean().to_numpy()

    def _dn(a: np.ndarray, n: int) -> np.ndarray:              # いまの値 − n本前の値
        d = np.full_like(a, np.nan)
        d[n:] = a[n:] - a[:-n]
        return d

    out = [dict(kind="そのまま", label="そのまま", warm=0,
                parts=["value"], fn=lambda a: a)]
    for n in grid:
        out.append(dict(kind="n本前との差", label=f"{n}本前との差", warm=n,
                        parts=["value", "lag", "sub"],
                        fn=(lambda n_: (lambda a: _dn(a, n_)))(n)))
    for m in grid:
        out.append(dict(kind="m本の平均", label=f"{m}本の平均", warm=m,
                        parts=["value", "ma"],
                        fn=(lambda m_: (lambda a: _ma(a, m_)))(m)))
    for m in grid:
        for n in grid:
            out.append(dict(kind="m本の平均の n本前との差",
                            label=f"{m}本の平均の {n}本前との差", warm=n + m,
                            parts=["value", "ma", "lag", "sub"],
                            fn=(lambda m_, n_: (lambda a: _dn(_ma(a, m_), n_)))(m, n)))
    return out


def _v9_part_matches(v9: pd.DataFrame, xa: np.ndarray, names: list[str], cols: list[str],
                     take: int, rows: int, grid: list[int]) -> dict:
    """『対応なし』と出た V9 の列だけ、うちの材料に部品を当てた列とも比べる。
    戻り＝{V9 の列名: 一番 近かった部品つきの列}。作れる＝|相関| が _V9_MATCH_SAME 以上。"""
    ys = {}
    for col in cols:
        y = pd.to_numeric(v9[col], errors="coerce").to_numpy(dtype=float)[-take:]
        if len(y) == take and np.isfinite(y).all() and float(np.nanstd(y)) != 0:
            ys[col] = y
    if not ys or xa.shape[1] < 1:
        return {}
    best: dict = {c: None for c in ys}
    for var in _v9_part_variants(grid):
        xt = var["fn"](xa)                                        # (take, 材料の本数)
        cut = var["warm"] + 1                                     # 暖機が終わるまでの行は使わない
        for lag in (0, 1):
            x = (xt[1:] if lag == 0 else xt[:-1])[cut:]
            if x.shape[0] < max(50, rows // 2):
                continue
            keep = np.isfinite(x).all(axis=0) & (x.std(axis=0) > 0)
            if not keep.any():
                continue
            idx = np.flatnonzero(keep)
            zx, zrx = _v9_z(x[:, idx]), _v9_z(_v9_rank(x[:, idx]))
            for col, yfull in ys.items():
                y = yfull[1:][cut:]
                zy, zry = _v9_z(y[:, None]), _v9_z(_v9_rank(y)[:, None])
                cp = (zy.T @ zx / len(y))[0]
                cs = (zry.T @ zrx / len(y))[0]
                b = np.nan_to_num(np.maximum(np.abs(cp), np.abs(cs)), nan=0.0)
                i = int(np.argmax(b))
                cur = best[col]
                if cur is None or float(b[i]) > cur["score"]:
                    best[col] = dict(name=names[idx[i]], kind=var["kind"], label=var["label"],
                                     parts=list(var["parts"]), lag=lag, score=float(b[i]),
                                     pearson=float(cp[i]), spearman=float(cs[i]))
    out = {}
    for col, d in best.items():
        if d is None:
            continue
        d["作れる"] = bool(d["score"] >= _V9_MATCH_SAME)
        out[col] = d
    return out


def _v9_col_matches(bars: pd.DataFrame, cfg: dict, catalog: list | None = None,
                    calc_rows: int = 30000, rows: int = 20000, fake=None,
                    parts: bool = True, part_grid: list[int] | None = None) -> dict:
    """V9 の各列に、うちのカタログのどの列が一番 近いかを実測で出す。戻り＝機械が読む形。

    ★1本ずらしても測る。V9 は「1本前の値」で判定する列を持つ（location_prev は .shift(1)＝
      cat_v9_decider.py:125）。ずらさずに測ると、同じ式の列でも別物に見える（実測＝0.906 まで落ちた）。
    fake は番人専用＝わざと作った列を V9 側に混ぜて、この検査が期待どおりに判定するかを確かめる。
    parts／part_grid は番人専用＝部品を当てる処理を止める・n と m の数字を差し替えるためのつまみ。"""
    win, v9 = _v9_preprocess_frame(bars, calc_rows)
    if fake is not None:
        v9 = v9.copy()
        for k, s in fake(win).items():
            v9[k] = s
    cat = catalog or build_catalog(cfg)
    take = rows + 1                                               # 1本ずらして測るぶんを1本ぶん多く取る
    vals, names, skipped_ours = [], [], []
    for name, fn, _d in cat:
        try:
            s = pd.to_numeric(fn(win), errors="coerce")
        except Exception as e:                                    # noqa: BLE001
            skipped_ours.append((name, f"計算できず: {str(e)[:40]}")); continue
        if s is None:
            skipped_ours.append((name, "None を返した")); continue
        v = s.to_numpy(dtype=float)[-take:]
        if len(v) < take or not np.isfinite(v).all():
            skipped_ours.append((name, "この本数では欠けが残る（暖機が終わらない）")); continue
        if np.nanstd(v) == 0:
            skipped_ours.append((name, "値が動かない（この窓では一定）")); continue
        vals.append(v); names.append(name)
    if len(names) < 2:
        return dict(rows=0, ours=names, skipped_ours=skipped_ours, matches=[], skipped_v9=[])
    xa = np.column_stack(vals)

    _rank, _z = _v9_rank, _v9_z                                   # 部品を当てる処理と同じものを使う
    # ラグ0＝同じ足どうし ／ ラグ1＝うちの列の「1本前」と V9 の列（V9 の .shift(1) の列に効く）
    lag_x = {0: xa[1:], 1: xa[:-1]}
    lag_z = {k: (_z(v), _z(_rank(v))) for k, v in lag_x.items()}
    matches, skipped_v9 = [], []
    for col in v9.columns:
        y = pd.to_numeric(v9[col], errors="coerce").to_numpy(dtype=float)[-take:][1:]
        if len(y) < rows or not np.isfinite(y).all():
            skipped_v9.append((col, "この本数では欠けが残る")); continue
        if np.nanstd(y) == 0:
            skipped_v9.append((col, "値が動かない（この窓では一定）")); continue
        zy, zry = _z(y[:, None]), _z(_rank(y)[:, None])
        cand = []
        for lag, (zx, zrx) in lag_z.items():
            cp = (zy.T @ zx / len(y))[0]
            cs = (zry.T @ zrx / len(y))[0]
            b = np.nan_to_num(np.maximum(np.abs(cp), np.abs(cs)), nan=0.0)
            for i in np.argsort(-b)[:3]:
                cand.append(dict(name=names[i], lag=lag, pearson=float(cp[i]),
                                 spearman=float(cs[i]), score=float(b[i]),
                                 family=(iref.find(names[i])[0] or {}).get("family", "？")))
        cand.sort(key=lambda d: -d["score"])
        top = cand[:3]
        score = top[0]["score"] if top else 0.0
        judge = ("同じ" if score >= _V9_MATCH_SAME else
                 "近い" if score >= _V9_MATCH_NEAR else "対応なし")
        matches.append(dict(v9=col, 判定=judge, score=score, top=top))

    # ── C-4｜『対応なし』の列だけ、うちの材料に部品を当てた列とも比べる ──────────────
    #   ★全部の列には当てない（材料 533列 × 変換25通り × 2 では計算が足りない）。
    #     当てるのは『対応なし』の列だけ＝この検査が材料の穴だと言おうとしている列だけ。
    none_cols = [m["v9"] for m in matches if m["判定"] == "対応なし"]
    part_hits = {}
    if parts and none_cols:
        part_hits = _v9_part_matches(v9, xa, names, none_cols, take, rows,
                                     part_grid or _v9_part_grid())
        for m in matches:
            if m["v9"] in part_hits:
                m["部品"] = part_hits[m["v9"]]
    return dict(rows=int(xa.shape[0] - 1), ours=names, skipped_ours=skipped_ours,
                matches=matches, skipped_v9=skipped_v9, parts_on=bool(parts and none_cols),
                part_grid=list(part_grid or (_v9_part_grid() if parts else [])))


def _insp_v9_columns(bars: pd.DataFrame, cfg: dict, catalog: list | None = None) -> list[str]:
    """検査14 V9 の実物の列 ↔ うちのカタログの列 の対応を実測で出す（値決め窓・5分足）。
    ❌ は出さない＝対応表を直すかどうかは まこさんが決める（CC が勝手に消さない・足さない）。"""
    r = _v9_col_matches(bars, cfg, catalog)
    kinds = _v9_price_kinds(bars)
    print(f"  V9 の実物（cat_v9_decider.preprocess）を そのまま呼んで作った列 "
          f"{len(r['matches']) + len(r['skipped_v9'])} 本 × うちの材料 {len(r['ours'])} 列"
          f"（値決め窓の {r['rows']} 本・5分足・ラグ0 と ラグ1 の両方で測る）")
    if r["skipped_v9"]:
        print(f"  この窓では測れなかった V9 の列 {len(r['skipped_v9'])} 件")
        for nm, why in r["skipped_v9"]:
            print(f"     ・{nm}: {why}")
    same = [m for m in r["matches"] if m["判定"] == "同じ"]
    near = [m for m in r["matches"] if m["判定"] == "近い"]
    none = [m for m in r["matches"] if m["判定"] == "対応なし"]
    print(f"  ★同じ（|相関| ≥ {_V9_MATCH_SAME}）= {len(same)} 本 ／ "
          f"近い（≥ {_V9_MATCH_NEAR}）= {len(near)} 本 ／ 対応なし = {len(none)} 本")
    print("  ★『値段の単位』の列は、うちは H6（価格非依存）で % の形に直して持っている＝"
          "『対応なし』でも材料の穴とは限らない（この欄で区別する）")
    if r.get("parts_on"):
        print(f"  ★『対応なし』の列だけ、うちの材料に条件の部品を当てた列とも比べる"
              f"（部品4種＝そのまま／n本前との差／m本の平均／m本の平均の n本前との差・"
              f"n と m は search_limits.json の int_grid {r.get('part_grid')} から引く）")
        print("  ★当てるのは部品を1〜2段 重ねたところまで＝3段以上は見ない。"
              "「本当は作れるのに、穴だと言う」ことは残る（逆は起きない＝言い過ぎる側に倒している）")
    for m in r["matches"]:
        mark = {"同じ": "✅", "近い": "⚠️", "対応なし": "❌"}[m["判定"]]
        t0 = m["top"][0]
        kind = kinds.get(m["v9"], "？")
        print(f"     {mark} V9 {m['v9']:20s} [{kind}] → うちの {t0['name']}"
              f"（family {t0['family']}／{'同じ足' if t0['lag'] == 0 else 'うちの1本前'}"
              f"／値の相関 {t0['pearson']:+.7f}／順位の相関 {t0['spearman']:+.7f}）")
        for t in m["top"][1:]:
            print(f"          2番手以下: {t['name']}"
                  f"（{'同じ足' if t['lag'] == 0 else 'うちの1本前'}"
                  f"／値 {t['pearson']:+.7f}／順位 {t['spearman']:+.7f}）")
        if p := m.get("部品"):
            head = "部品で作れる" if p["作れる"] else "部品でも作れない（一番 近いもの）"
            print(f"          {head}: うちの {p['name']} に「{p['label']}」を当てたもの"
                  f"（部品 {'・'.join(p['parts'])}"
                  f"／{'同じ足' if p['lag'] == 0 else 'うちの1本前'}"
                  f"／値 {p['pearson']:+.7f}／順位 {p['spearman']:+.7f}）")
    holes = [m for m in none if kinds.get(m["v9"]) == "値段に依らない"
             and not (m.get("部品") or {}).get("作れる")]
    made = [m for m in none if kinds.get(m["v9"]) == "値段に依らない"
            and (m.get("部品") or {}).get("作れる")]
    print(f"  ★材料の穴の候補＝『対応なし』かつ『値段に依らない』かつ『部品でも作れない』"
          f"= {len(holes)} 本" + ("（" + "・".join(m["v9"] for m in holes) + "）" if holes else ""))
    if made:
        print(f"  ★『対応なし』だが部品で作れるので穴でない = {len(made)} 本（"
              + "・".join(f"{m['v9']}＝{m['部品']['name']} の {m['部品']['label']}" for m in made) + "）")
    print("  ⚠️ この検査は ❌ を出さない（合否は gen_signal_families.py --v9-test）。"
          "穴を埋めるかどうかは まこさんが決める（CC が勝手に材料を足さない）")
    return []


# ══ 材料検査（CP4 監査フィードバック②・2026-08-06・read-only）═══════════════
# 型の表（役割×系統×時間足×向き）を作る前に、表の材料3つが間違っていないかを機械検査する。
# ①方向の欄（indicator_reference_diag の houkou）②系統分類（FAMILY_LINEAGE）③v9_logic.md の鮮度。
# 条件の生成・値の選定・売買・採点は一切しない。実データを使うのは②だけで、値決め窓のみ（採点窓は1バーも使わない）。
_HOUKOU2PROP = {"順張り値": "trend", "状態量": "none", "ボラ量": "vol", "反転サイン": "reversal"}
_V9_SOURCES = ("strategies/cat_v9_decider.py", "runner/replay_csv.py", "config/cat_params_v9.json")
_V9_RECORD_SINCE = "2026-07-28 00:00"   # v9_logic.md の記録時点 2026-07-27 の翌日0時＝これ以降の変更を探す
_OSC_BOUNDS = {"RSI": (0.0, 100.0), "Stoch%K": (0.0, 100.0), "Stoch%D": (0.0, 100.0),
               "MFI": (0.0, 100.0), "RCI": (-100.0, 100.0),
               # サイクル系（2026-08-11・段6-g）＝作りの上で −1〜1 に収まる（サインの値・正規化した波）
               "EBSW": (-1.0, 1.0), "HT_SINE": (-1.0, 1.0), "HT_LEADSINE": (-1.0, 1.0),
               "MSW_SINE": (-1.0, 1.0), "MSW_LEAD": (-1.0, 1.0)}
# BB%b は作りの上で上限・下限が無い（価格がバンドの外に出れば 0〜1 を超える＝StockCharts %B Indicator・
# 2026-08-06 WebResearch で確認）。端の値でなく分位と中央値で「オシレーターの形か」を見る。
_OSC_PCTL = {"BB%b": (0.0, 1.0)}


def _mat_series(n: int = 2600):
    """合成の系列6本（上げ・下げ・横ばい・荒い・加速上げ・加速下げ）。検査専用＝学習にも値決めにも使わない。
    加速の2本は 2026-08-06 まこさん OK の直し＝「加速」を主張する指標（MACDヒスト等）は、一定の速さの
    上げでは 0 に収束するのが正しい動き（StockCharts MACD-Histogram）なので、だんだん速くなる系列で照合する。"""
    idx = pd.date_range("2026-03-01", periods=n, freq="5min")
    t = np.arange(n, dtype=float)
    wig = np.sin(t / 3.0)

    def mk(close):
        c = pd.Series(close, index=idx)
        return pd.DataFrame({"open": c.shift().fillna(c.iloc[0]),
                             "high": c * 1.001 + 0.2 * np.abs(wig),
                             "low": c * 0.999 - 0.2 * np.abs(wig),
                             "close": c, "volume": 10.0 + np.cos(t / 5.0)}, index=idx)

    up = mk(100.0 + 0.05 * t + 0.3 * wig)
    dn = mk(100.0 + 0.05 * (n - t) + 0.3 * wig)
    flat = mk(100.0 + 0.05 * np.sin(t / 40.0))
    wild = mk(100.0 + 3.0 * np.sin(t / 7.0))
    acc_up = mk(100.0 + 4e-5 * t * t + 0.3 * wig)
    acc_dn = mk(100.0 + 4e-5 * n * n - 4e-5 * t * t + 0.3 * wig)
    return up, dn, flat, wild, acc_up, acc_dn


def _insp_direction_known(cfg: dict, bars: pd.DataFrame | None = None, fake: dict | None = None,
                          catalog: list | None = None) -> list[str]:
    """材料検査1 方向の欄の既知答え検査（CP4 ②）＝カタログ全種の「方向」の欄の主張を、2本の柱で照合する。
    柱1＝合成系列（上げ・下げ・横ばい・荒い・加速）。柱2＝実データ（値決め窓の「上げた日」と「下げた日」の
    分布・2026-08-06 まこさん OK で追加＝合成系列は CC が作ったものなので、独立の柱で確かめる）。
    ★最終判定は実データの柱を優先する＝実データが ✗ なら ❌ ／ 実データが ✓ で合成だけ合わないなら ⚠️（報告）
    ／実データが使えない列だけ合成の柱で判定する。
    fake はメタ確認専用＝偽の欄で検査が実際に ❌ を出すことを確かめる（合成の柱で落とす＝bars 省略可）。"""
    up, dn, flat, wild, acc_up, acc_dn = _mat_series()
    tail = 300
    ng: list[str] = []
    from collections import Counter
    marks = Counter()
    bycat = Counter()

    def med(fn, d):
        try:
            return float(pd.to_numeric(fn(d), errors="coerce").iloc[-tail:].median())
        except Exception:
            return float("nan")

    def fire(fn, d):
        try:
            s = pd.to_numeric(fn(d), errors="coerce").iloc[-tail:]
            return float((s.fillna(0.0) != 0.0).mean())
        except Exception:
            return float("nan")

    # 実データの柱の準備＝値決め窓だけ（採点窓は1バーも使わない）。日足の陽線＝上げた日／陰線＝下げた日。
    win = None
    m_up = m_dn = None
    if bars is not None:
        _nm0, a0, b0 = _insp_windows()[0]
        win = bars.loc[(bars.index >= a0) & (bars.index < b0)]
        d_open = win.open.resample("1D").first()
        d_close = win.close.resample("1D").last()
        day = win.index.normalize()
        ups = d_open.index[(d_close > d_open).fillna(False)]
        dns = d_open.index[(d_close < d_open).fillna(False)]
        m_up = day.isin(ups)
        m_dn = day.isin(dns)
        print(f"  実データの柱: 値決め窓 {a0.date()}〜{(b0 - pd.Timedelta('1D')).date()}＝"
              f"上げた日 {len(ups)} 日 ／ 下げた日 {len(dns)} 日（採点窓は1バーも使わない）")

    def real_split(fn):
        """実データの柱＝(上げた日の中央値, 下げた日の中央値, 全体の四分位幅)。使えなければ None。"""
        if win is None:
            return None
        try:
            s = pd.to_numeric(fn(win), errors="coerce")
        except Exception:
            return None
        iqr = float(s.quantile(0.75)) - float(s.quantile(0.25))
        return (float(s[m_up].median()), float(s[m_dn].median()), iqr)

    for name, fn, _d in (catalog or build_catalog(cfg)):
        ref, _prm = iref.find(name)
        if ref is None:
            ng.append(f"{name}: 参照表に無い（方向の欄が引けない）")
            marks["❌"] += 1
            continue
        houkou, prop = ref["houkou"], ref["prop"]
        faked = bool(fake and fake.get("name") == name)
        if faked:
            houkou, prop = fake["houkou"], fake.get("prop", prop)
        cat = houkou.split("＝")[0]
        bycat[cat] += 1
        if cat not in _HOUKOU2PROP:
            ng.append(f"{name}: 方向の欄の区分が読めない（{houkou[:40]}）")
            marks["❌"] += 1
            continue
        if _HOUKOU2PROP[cat] != prop:
            ng.append(f"{name}: 方向の欄（{cat}）と性質テストの型（prop={prop}）が食い違う")
            marks["❌"] += 1
            continue
        syn, real = "na", "na"                  # 各柱の結果＝ok / ng / na（判定不能）
        sn, rn = "", ""
        if cat == "順張り値":
            d_hi, d_lo = (acc_up, acc_dn) if "加速" in houkou else (up, dn)
            a, b = med(fn, d_hi), med(fn, d_lo)
            if not (np.isfinite(a) and np.isfinite(b)) or max(abs(a), abs(b)) < 1e-6 or a == b:
                sn = f"合成=判定不能（上げ {a:.4g} ／ 下げ {b:.4g}＝計算不能か実質ゼロ）"
            else:
                ok = a > b
                if ok and "プラス" in houkou:
                    ok = (a > 0.0) and (b < 0.0)
                syn = "ok" if ok else "ng"
                sn = f"合成{'✓' if ok else '✗'}（上げ {a:.4g} ／ 下げ {b:.4g}{'・加速系列' if '加速' in houkou else ''}）"
            r = real_split(fn)
            if r is not None:
                mu, mdn, iqr = r
                if not (np.isfinite(mu) and np.isfinite(mdn)) or iqr <= 0:
                    rn = "実データ=判定不能"
                elif abs(mu - mdn) < 0.05 * iqr:
                    real = "flat"
                    rn = f"実データ=向きの差が出ない（上げた日 {mu:.4g} ／ 下げた日 {mdn:.4g} ／ 四分位幅 {iqr:.4g}）"
                elif mu > mdn:
                    real = "ok"
                    rn = f"実データ✓（上げた日 {mu:.4g} ＞ 下げた日 {mdn:.4g}）"
                else:
                    real = "ng"
                    rn = f"実データ✗（上げた日 {mu:.4g} ＜ 下げた日 {mdn:.4g}＝主張と逆向き）"
        elif cat == "状態量":
            a, b = med(fn, up), med(fn, dn)
            if not (np.isfinite(a) and np.isfinite(b)):
                sn = f"合成=判定不能（上げ {a:.4g} ／ 下げ {b:.4g}）"
            elif max(abs(a), abs(b)) < 1e-9:
                syn, sn = "ok", f"合成✓（上げ {a:.4g} ／ 下げ {b:.4g}＝どちらも 0）"
            else:
                asym = abs(a - b) / max(abs(a), abs(b))
                syn = "ok" if asym <= 0.5 else "ng"
                sn = f"合成{'✓' if syn == 'ok' else '✗'}（上げ {a:.4g} ／ 下げ {b:.4g}＝非対称率 {asym:.2f}・0.5 以下で向きなし）"
            r = real_split(fn)
            if r is not None:
                mu, mdn, iqr = r
                if not (np.isfinite(mu) and np.isfinite(mdn)) or iqr <= 0:
                    rn = "実データ=判定不能"
                else:
                    real = "ok" if abs(mu - mdn) <= 0.5 * iqr else "ng"
                    rn = (f"実データ{'✓' if real == 'ok' else '✗'}（上げた日 {mu:.4g} ／ 下げた日 {mdn:.4g} ／ "
                          f"四分位幅 {iqr:.4g}＝差が幅の半分以下で向きなし）")
        elif cat == "ボラ量":
            w, c0 = med(fn, wild), med(fn, flat)
            if not (np.isfinite(w) and np.isfinite(c0)):
                sn = f"合成=判定不能（荒い {w:.4g} ／ 静か {c0:.4g}）"
            else:
                syn = "ok" if w >= c0 else "ng"
                sn = f"合成{'✓' if syn == 'ok' else '✗'}（荒い {w:.4g} ／ 静か {c0:.4g}＝荒い ≥ 静か の主張）"
            rn = "実データ=対象外（ボラは下げ相場で大きく出る非対称が実在＝向きの検査に使わない）"
        else:                                   # 反転サイン＝方向の系列では検証できない＝既知答えの有無を検査
            if ref["known"] is None and not faked:
                syn, sn = "ng", "反転の主張なのに手計算の既知答えが無い（検証の柱が無い）"
            else:
                syn = "ok"
                sn = (f"既知答えあり（向きの照合は検査3 ③が担保）／発火率 上げ {fire(fn, up):.0%}"
                      f" ／ 下げ {fire(fn, dn):.0%} ／ 横ばい {fire(fn, flat):.0%}")
            rn = "実データ=対象外（事象の印＝分布の照合になじまない）"
        # ★最終判定＝実データ優先（実データ ✗ → ❌ ／ 実データ ✓ で合成 ✗ → ⚠️ ／ 実データ不可 → 合成で判定）
        if real == "ng":
            mark = "❌"
        elif real in ("ok", "flat"):
            if syn == "ng":
                mark = "❌" if real == "flat" else "⚠️"
            elif real == "flat" and syn != "ok":
                mark = "⚠️"
            else:
                mark = "✅" if real == "ok" else ("✅" if syn == "ok" else "⚠️")
        else:                                   # real == "na"
            mark = {"ok": "✅", "ng": "❌", "na": "⚠️"}[syn]
        marks[mark] += 1
        note = sn + ("／" + rn if rn else "")
        if mark == "❌":
            ng.append(f"{name}: 方向の欄の主張と実測が食い違う（{note}）")
        print(f"     {mark} {name} [{cat}] {note}")
    print(f"  区分の内訳: {dict(bycat)}")
    print(f"  結果: ✅ {marks.get('✅', 0)} ／ ❌ {marks.get('❌', 0)} ／ ⚠️ {marks.get('⚠️', 0)}"
          f"（⚠️＝片方の柱だけ合わない・判定不能＝反証ではないが一覧で報告する）")
    return ng


def _insp_lineage_range(bars: pd.DataFrame, cfg: dict, fake_family: str | None = None,
                        catalog: list | None = None) -> list[str]:
    """材料検査2 系統分類（FAMILY_LINEAGE）の範囲検査（CP4 ②）＝オシレーター系に分類された
    指標の値域が「有界」または「0 を挟んで振動」かを、値決め窓の実データで照合する。
    あわせて全種の分類一覧を、非同型レビュー（Web Claude）へ渡す形で印字する。
    fake_family はメタ確認専用＝その系統をわざとオシレーター扱いにして ❌ が出ることを確かめる。"""
    ng: list[str] = []
    nm0, a0, b0 = _insp_windows()[0]            # 値決め窓（periods.py 正本）＝採点窓は使わない
    win = bars.loc[(bars.index >= a0) & (bars.index < b0)]
    print(f"  実データ: {nm0}窓 {a0.date()}〜{(b0 - pd.Timedelta('1D')).date()}（{len(win)} 行）＝採点窓は1バーも使わない")
    rows = []
    for name, fn, _d in (catalog or build_catalog(cfg)):
        ref, _prm = iref.find(name)
        fam = ref["family"] if ref else "？"
        k = iref.FAMILY_LINEAGE.get(fam, {}).get("k", "未登録")
        if fake_family and fam == fake_family:
            k = "オシレーター"
        rows.append((name, fam, k))
        if k != "オシレーター":
            continue
        try:
            s = pd.to_numeric(fn(win), errors="coerce").dropna()
        except Exception as e:
            ng.append(f"{name}: 値決め窓で計算できない: {str(e)[:50]}")
            continue
        if len(s) < 1000:
            print(f"     ⚠️ {name}: 点が足りない（{len(s)} 本）＝判定不能")
            continue
        lo_hi = _OSC_BOUNDS.get(fam)
        pct = _OSC_PCTL.get(fam)
        if pct:
            lo, hi = pct
            p01, p99, md0 = float(s.quantile(0.01)), float(s.quantile(0.99)), float(s.median())
            ok = (p01 >= lo - 0.5) and (p99 <= hi + 0.5) and (lo <= md0 <= hi)
            note = (f"分位で照合＝p01 {p01:.4g} ／ p99 {p99:.4g} ／ 中央値 {md0:.4g}"
                    f"（%b はバンドの外で 0〜1 を超えるのが正しい＝端の値でなく分位 ±0.5 と中央値で見る）")
        elif lo_hi:
            lo, hi = lo_hi
            ok = (float(s.min()) >= lo - 1e-6) and (float(s.max()) <= hi + 1e-6)
            note = f"値域 [{float(s.min()):.4g}, {float(s.max()):.4g}] ⊂ 想定 [{lo:.4g}, {hi:.4g}]"
        else:
            neg, pos = float((s < 0).mean()), float((s > 0).mean())
            ok = (neg >= 0.05) and (pos >= 0.05)
            note = f"0 を挟んで振動するか＝マイナス側 {neg:.0%} ／ プラス側 {pos:.0%}（両側 5% 以上で合格）"
        print(f"     {'✅' if ok else '❌'} {name} [{fam}] {note}")
        if not ok:
            ng.append(f"{name}: オシレーター系の分類なのに値域がオシレーターの形でない（{note}）")
    print("  ── 非同型レビュー依頼（この節を丸ごと Web Claude に渡す・実施はまこさんにお願いする）──")
    print("  依頼文: 下の「指標名 → 系統」の分類が妥当かを、実装を見ない立場で1行ずつ 妥当/疑問 で判定し、")
    print(f"  疑問の行には理由を1行で書いてください。系統は {'／'.join(iref.LINEAGE_KINDS)} の{len(iref.LINEAGE_KINDS)}つです。")   # ★R-1（2026-10-22）＝数を書かず区分から作る
    for name, fam, k in rows:
        print(f"     {name} [{fam}] → {k}")
    return ng


def _insp_v9_freshness(expected: dict | None = None) -> list[str]:
    """材料検査3 v9_logic.md の鮮度検査（CP4 ②）＝出どころ3本（Entry判定・Exit実行・値）が
    記録時点（2026-07-27）から変わっていないことを git log と md5 で機械照合する。
    v9_logic.md に md5 の記録は無い（確認済 2026-08-06）＝今回の出力を以後の比較の基準として残す。
    expected はメタ確認専用＝偽の md5 を渡して ❌ が出ることを確かめる。"""
    import hashlib
    import os
    import subprocess
    ng: list[str] = []
    sdk = pathlib.Path(__file__).resolve().parents[2]
    try:
        root = subprocess.run(["git", "-C", str(sdk), "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception as e:
        return [f"git が使えない: {str(e)[:60]}"]
    for rel in _V9_SOURCES:
        p = sdk / rel
        if not p.exists():
            ng.append(f"{rel}: ファイルが無い")
            continue
        md5v = hashlib.md5(p.read_bytes()).hexdigest()
        rp = os.path.relpath(p, root)
        after = subprocess.run(["git", "-C", root, "log", "--since", _V9_RECORD_SINCE,
                                "--format=%h %ad %s", "--date=short", "--", rp],
                               capture_output=True, text=True).stdout.strip().splitlines()
        after = [x for x in after if x.strip()]
        last = subprocess.run(["git", "-C", root, "log", "-1", "--format=%h %ad", "--date=short", "--", rp],
                              capture_output=True, text=True).stdout.strip()
        mark = "✅"
        note = ""
        if after:
            mark = "❌"
            ng.append(f"{rel}: 記録時点（2026-07-27）より後に変更コミットがある: {after[0][:60]}")
            note = f"／ 記録後の変更 {len(after)} 件"
        exp = (expected or {}).get(p.name)
        if exp is not None and exp != md5v:
            mark = "❌"
            ng.append(f"{rel}: md5 が照合値と不一致（照合値 {exp[:8]}… ／ 実測 {md5v[:8]}…）")
            note += "／ md5 不一致"
        print(f"     {mark} {rel} md5 {md5v} ／ 最終コミット {last or '（履歴なし）'}{note}")
    return ng


def check_materials(bars_csv: str, config_path: str | None = None) -> None:
    """材料検査（CP4 ②）＝3本を順に走らせ、まとめを機械出力する。❌ が1つでもあれば終了コード1。
    ❌ が出ても直さない＝報告してまこさんの判断を仰ぐ（acceptance 2026-08-06 の決まり）。"""
    cfg = load_config(config_path)
    bars = pd.read_csv(bars_csv, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    print("#" * 100)
    print("# 材料検査（CP4 監査フィードバック②・read-only・型の表の材料の間違い確認）")
    print(f"# 対象: {bars_csv}（{len(bars)} 行）／ 指標 {len(build_catalog(cfg))} 種")
    print("# 売買しない・値決めしない・審判に触れない。実データは値決め窓のみ＝採点窓は1バーも使わない。")
    print("#" * 100)
    fails = {}
    _h("材料検査1 方向の欄の既知答え検査（柱1＝合成系列 ／ 柱2＝実データの上げた日・下げた日＝実データ優先）")
    fails["材料検査1"] = _insp_direction_known(cfg, bars=bars)
    _h("材料検査2 系統分類（FAMILY_LINEAGE）の範囲検査（値決め窓の実データ・オシレーター系の値域）")
    fails["材料検査2"] = _insp_lineage_range(bars, cfg)
    _h("材料検査3 v9_logic.md の鮮度検査（git log と md5）")
    fails["材料検査3"] = _insp_v9_freshness()
    print("\n" + "=" * 100)
    print("材料検査のまとめ（❌＝直さずに報告する・材料の直しはまこさんの判断を仰いでから）")
    bad = 0
    for key in fails:
        if fails[key]:
            for x in fails[key]:
                print(f"  ❌ {key}: {x}")
            bad += len(fails[key])
        else:
            print(f"  ✅ {key}: 異常なし")
    print("=" * 100)
    if bad:
        raise SystemExit(1)


def check_materials_meta(bars_csv: str, config_path: str | None = None) -> None:
    """材料検査のメタ確認（§2.9③）＝わざと偽物を3つ注入し、検査が実際に ❌ を出すことを確かめる。
    3件とも落ちれば終了コード0（検査は機能している）。1件でも素通りすれば終了コード1。
    実物のカタログ・参照表・ファイルは1バイトも変えない（差し替えは実行中の引数だけ）。"""
    cfg = load_config(config_path)
    bars = pd.read_csv(bars_csv, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    cat = build_catalog(cfg)
    print("#" * 100)
    print("# 材料検査のメタ確認（わざと壊して落ちるか・実物は不変・注入は実行中の引数のみ）")
    print("#" * 100)
    tgt = next((nm for nm, _f, _d in cat if iref.find(nm)[0] and iref.find(nm)[0]["family"] == "DI差"), None)
    results = []
    _h(f"偽1: {tgt} の方向の欄を「状態量（向きなし）」に差し替える＝本物は順張り値なので ❌ が出るはず")
    sub1 = [row for row in cat if row[0] == tgt]
    r1 = _insp_direction_known(cfg, fake=dict(name=tgt, houkou="状態量＝メタ確認用の偽の欄（本物は順張り値）",
                                              prop="none"), catalog=sub1)
    results.append(("偽の方向の欄", r1))
    _h("偽2: ボラ系 ATR% をオシレーター系に差し替える＝値域が片側だけなので ❌ が出るはず")
    sub2 = [row for row in cat if iref.find(row[0])[0] and iref.find(row[0])[0]["family"] == "ATR%"]
    r2 = _insp_lineage_range(bars, cfg, fake_family="ATR%", catalog=sub2)
    results.append(("偽の系統分類", r2))
    _h("偽3: cat_v9_decider.py に偽の md5 を照合値として渡す＝不一致で ❌ が出るはず")
    r3 = _insp_v9_freshness(expected={"cat_v9_decider.py": "0" * 32})
    results.append(("偽の指紋", r3))
    print("\n" + "=" * 100)
    ok = True
    for label, r in results:
        if r:
            print(f"  ✅ {label}: 検査が正しく ❌ を出した（{len(r)} 件）")
        else:
            print(f"  🚨 {label}: 偽物が素通りした＝検査が機能していない")
            ok = False
    print("=" * 100)
    if not ok:
        raise SystemExit(1)
    print("  メタ確認3件 全部落ちた＝材料検査は機能している")


# ══ 場面を分ける材料の順位（M2-3-3・2026-08-22 新設・まこさん承認「実装に入っていいよ」）═════════
# ★何のための処理か。
#   案を作るプログラム（engine_tuner_gen）は、材料を「どれが効くか」を1つも知らないまま引いている
#   （2026-08-22 実測＝順位を読む所は 0か所）。役割4つに材料を1本ずつ割り当てるだけで 6,052億通り
#   ＝乱数で条件をつなぐのと変わらない（要件が名指しで禁止しているもの 1番）。
#   そこで、値決め窓のデータだけで「場面を分ける力」の順位を出し、engine_tuner に渡せる形にする。
# ★ラベル（正解の印）の作り方＝場面の名前を借りてこない。
#   出どころの逐語（engine_tuner_milestones2.md の 0.3.1）＝「今、どの手法が通用する市場か？」
#   ＝場面の判定の本体は「どの手法が通用するか」で、それは そのあとの値動きの性質で決まる。
#   だから「そのバーから先 N本の値動きの性質」を3つの見方で真偽に直したものをラベルにする。
#   ★RG-v5 の判定は借りない（決まり2＝写さない。写すと、見つかるものの上限が RG-v5 になる）。
# ★3本に分ける理由＝法則 C1「トレンドか否か（強さ）と、上か下か（向き）は別の指標」。
#   1本にすると、向きの材料（DI差 など）は上でも下でもトレンドなので分離力が 0.5 に寄り、順位の
#   下に沈む＝場面を4つに分ける材料が、順位づけの段階で消える。
# ★数字を1つも作っていない。
#   N（先を見る本数）＝札を作る場所（regime_label.py・設定＝recipes/regime_label.json）の、採点に使う版の本数をその場で読む
#     ＝コードに写さない（2か所に持つと片方だけ直って黙って腐る・教訓 L-519）。M2-F-6d で search_limits.json から移した。
#   群の分け方＝中央値で半分（＝選ぶ数字が無い）。
#   大きさの物差し＝「先 N本で動いた幅 ÷ 直前 N本で動いた幅」＝同じ N しか使わない（新しい数字が要らない）。
#   重複の線＝_DUP_NEAR・_DUP_SAME（実物）。計算に使う本数＝検査12 と同じ定数を共有する。
# ★材料の値は当該バーまでの確定値だけ（build_features をそのまま呼ぶ＝式を写さない）。
#   ラベルは先 N本を見る＝正解の印を作る側であって、本番の判断には入らない（build_labels_pct と同じ作り）。
#   窓の外へはみ出す分は欠損になって落ちる。
# ★C10 の④＝分け方は値決め窓だけで決める。_assert_search_window_only が物理で止める。
# ★限界（正直に）＝①ラベルの中央値は値決め窓の全体から出している。走る時の閾値ではなく、順位を
#   出すためだけの印なので本番には入らないが、「窓全体の統計を使っている」ことは事実として書いておく。
#   ②順位が良いかどうかは net でしか決まらない＝ここでは判定しない（見るのは M2-11）。
REGIME_LABELS = ("強さ", "向き", "大きさ")


def _regime_horizons() -> tuple[int, ...]:
    """先を見るバー数（N）。札を作る場所（regime_label.py）の、採点に使う版の本数を返す＝コードに数字を写さない。

    出どころ＝recipes/regime_label.json（M2-F-6d・まこさん決定 2026-09-28）。
      版1 er_median＝「先を見る本数」（24・288＝もとは search_limits.json の state_hold_bars_range の両端・まこさん承認 24a453d6…）
      版2 band_hold＝役割ごとに 保有の上限 × 続く本数
    """
    return rl.bars_keys()


def _assert_search_window_only(idx, where: str) -> None:
    """使うバーが値決め窓の中だけであることを、その場で確かめる（法則 C10 の④の物理化）。

    ★採点窓のバーが1本でも混ざったら止める＝順位づけに採点窓の情報を入れない。
    """
    if len(idx) == 0:
        raise SystemExit(f"[{where}] 値決め窓のバーが1本も無い")
    lo, hi = pd.Timestamp(min(idx)), pd.Timestamp(max(idx))
    if lo < SEARCH_START or hi >= SEARCH_END:
        raise SystemExit(
            f"[{where}] 値決め窓の外のバーが混ざっている: {lo} 〜 {hi} ／ "
            f"値決め窓＝{SEARCH_START} 以上 {SEARCH_END} 未満（periods.py が正本）")


def _regime_labels(win: pd.DataFrame, n: int) -> dict:
    """そのバーから先 n本の値動きの性質を、3つの見方で真偽に直す（＝答え合わせに使う正解ラベル・札）。

    ★札を作る場所は regime_label.py の1か所（M2-F-6d・まこさん決定 2026-09-28「札を作る場所を1つにすること」）。
      ここは呼ぶだけ＝式を写さない（regime_label.py の自己検査 T6 が見る）。
    ①強さ・②向き・③大きさ の作り方＝regime_label.py の er_median（版1＝いままでの式）と band_hold（版2）の説明。
    戻り＝{名前: (真偽の並び, その行が使えるか)}。先が足りない末尾は「使えない」になる。
    """
    return rl.labels_at_bars(win, n)


def _oneway_ratio(win: pd.DataFrame, n: int) -> pd.Series:
    """先 n本の「片道の度合い」＝始まりと終わりの価格差 ÷ その区間の値幅（2026-08-29 新設・M2-A-2）。

    0 に近いほど行って戻った（レンジらしい）／1 に近いほど片道（レンジではない）。
    ★いまの正解の印（_regime_labels の ①強さ）とは分母が違う。
      あちらの分母は「歩いた距離の合計」＝細かく揺れるほど分母が増えて値が下がるので、
      ただ荒れているだけの区間も「レンジ」に入る。こちらの分母は「その区間の値幅」。
    ★これも正解ではない。レンジの本当の答えは誰も持っていない（M2-A-1 の一次の逐語
      "Since market regimes are latent unobservable processes"）。
      分かるのは「レンジという言葉の意味と、どれだけ食い違っているか」の量だけ。
    ★どれも比＝ドルの絶対値を1つも使わない（H6）。
    """
    c = win["close"].astype(float)
    fwd = (c.shift(-n) - c).abs()   # H2OK: 正解の印を測り直す側（ラベル）＝本番の判断には入らない。_regime_labels と同じ作り
    hi = win["high"].astype(float).rolling(n + 1).max().shift(-n)  # H2OK: 同上（ラベル側）。始まりのバーを含めた n+1本の高値
    lo = win["low"].astype(float).rolling(n + 1).min().shift(-n)   # H2OK: 同上（ラベル側）。始まりのバーを含めた n+1本の安値
    width = hi - lo
    return (fwd / width).where(width > 0)             # 値幅が 0 の区間は数から外す（0 で割らない）


def _synth_regime_bars(block: int = 60, blocks: int = 8) -> tuple[pd.DataFrame, pd.Series]:
    """答えが分かっているニセの4本値を作る（2026-08-29 新設・M2-A-4・まこさん承認 21dcfabff3d44a64）。

    ★乱数を1つも使わない。決まった式で作る。
      トレンドの区間＝1本ごとに +1.0 で一直線に上がる（まっすぐ進んだ割合が高い）。
      レンジの区間  ＝+2.0 と −2.0 を交互に繰り返して元に戻る（割合が低い）。
      この2つを同じ本数ずつ交互に並べる（いまの印は窓の中央値で切るので、半々にする）。
    ★何のために要るか＝正解データを作る _regime_labels にバグが入っても誰も気づかない状態を、
      毎回の自己検査でなくすため。M2-A-1 で調べた外のやり方（答えの分かるデータで先に確かめてから
      実データへ移る）と同じ考え方。★数字は外から採らない＝うちの印に合わせて作る。
    戻り＝(4本値のデータ, その行がトレンドの区間かどうか)。
    """
    idx = pd.date_range("2024-06-01", periods=block * blocks, freq="5min")
    cl: list = []
    is_trend: list = []
    price = 100.0
    for b in range(blocks):
        trend = (b % 2 == 0)                          # 偶数番目＝トレンド／奇数番目＝レンジ
        for i in range(block):
            price = price + 1.0 if trend else (price + 2.0 if i % 2 == 0 else price - 2.0)
            cl.append(price)
            is_trend.append(trend)
    s = pd.Series(cl, index=idx, dtype=float)
    return (pd.DataFrame({"close": s, "high": s, "low": s}, index=idx),
            pd.Series(is_trend, index=idx))


def _insp_regime_label_oneway(bars: pd.DataFrame) -> list:
    """検査15＝いまの正解の印が「レンジだった」とした区間を、片道の度合いで測り直す（2026-08-29・M2-A-2）。

    ★判定はしない（報告だけ）＝戻りは必ず空の一覧。
      レンジの本当の正解は誰も持っていないので、「合っている・間違っている」を機械では決められない。
    ★レンジの札だけでなくトレンドの札も並べて出す＝2つが分かれていなければ、
      いまの印はレンジらしさを捉えていないことになる（この比較が無いと多い少ないを判断できない）。
    """
    _nm, a0, b0 = _insp_windows()[0]                  # 値決め窓（採点窓は1バーも使わない）
    win = bars.loc[(bars.index >= a0) & (bars.index < b0)]
    _assert_search_window_only(win.index, "検査15")
    print(f"  窓＝値決め（{a0.date()} 〜 {b0.date()} の手前）／バー {len(win):,} 本")
    print("  片道の度合い＝|終わりの終値 − 始まりの終値| ÷ (始まりのバーを含めた n+1本の高値 − 同じ範囲の安値)")
    print("  ★分母に始まりのバーを含めるのは、分子が同じ n+1本ぶんを見ているから（含めないと比が 1 を超える）")
    print("  0 に近い＝行って戻った（レンジらしい）／1 に近い＝片道（レンジではない）")
    for n in _regime_horizons():
        ratio = _oneway_ratio(win, n)
        mask, usable = _regime_labels(win, n)["強さ"]
        step = _independent_step("5m", n)             # 重なった区間を何度も数えない
        idx = win.index[::step]
        r = ratio.reindex(idx)
        m = mask.reindex(idx)
        u = usable.reindex(idx).fillna(False) & r.notna()
        rng = r[u & ~m.fillna(True)]                  # レンジの札＝強さ（ER）が窓の中央値 未満
        trd = r[u & m.fillna(False)]                  # トレンドの札＝強さ（ER）が窓の中央値 以上
        print(f"\n  ── 先 {n} 本（5分足なので {n * 5} 分）／{step} 本ごとに1つ数える ──────────")
        print(f"     使えた区間＝レンジの札 {len(rng):,} 本 ／ トレンドの札 {len(trd):,} 本")
        if len(rng) == 0 or len(trd) == 0:
            print("     ⚠️ 片方が 0 本＝この本数では比べられない")
            continue
        print(f"     中央値＝レンジの札 {rng.median():.3f} ／ トレンドの札 {trd.median():.3f}"
              f" ／ 差 {trd.median() - rng.median():+.3f}")
        for line in (0.5, 0.7, 0.9):
            k = int((rng >= line).sum())
            print(f"     レンジの札のうち 比 {line:.1f} 以上＝{k:,} 本（{k / len(rng) * 100:.1f}%）"
                  f"＝言葉の意味と食い違う区間")
        print("     分布（10%刻み・左＝レンジの札 ／ 右＝トレンドの札）")
        for b in range(10):
            lo_, hi_ = b / 10, (b + 1) / 10
            ka = int(((rng >= lo_) & (rng < hi_)).sum()) if b < 9 else int((rng >= lo_).sum())
            kb = int(((trd >= lo_) & (trd < hi_)).sum()) if b < 9 else int((trd >= lo_).sum())
            print(f"       {lo_:.1f}〜{hi_:.1f}   {ka / len(rng) * 100:5.1f}%  |  {kb / len(trd) * 100:5.1f}%")
    print("\n  ★この数字は「正解との一致」ではない。レンジの本当の正解は誰も持っていない。")
    print("    分かるのは「レンジという言葉の意味と、どれだけ食い違っているか」の量だけ。")
    return []


def _role_lineage_table() -> dict:
    """役割ごとの絞り（系統・時間足）を、承認済みの型の表から読む＝コードに写さない。"""
    import json
    p = pathlib.Path(__file__).resolve().parents[2] / ".claude" / "ratchet" / "signal_families.json"
    return json.loads(p.read_text(encoding="utf-8"))["role_lineage"]["roles"]


def _independent_step(tf: str, n: int) -> int:
    """独立な標本を取るときの、5分足での間隔（本数）。

    ★なぜ要るか（2026-08-22 の1回目の本走で見つけた問題）。
      ①上位足の列は、5分足の並びへ引き伸ばして（前の値で埋めて）持っている。20,000本の5分足＝69日
        の中に、日足のバーは 69本 しか無い。それを 20,000個 の標本として数えると、69個の値を
        290回ずつ重複して数えることになり、分離力が実力より大きく（または小さく）出る。
      ②ラベルも先 n本を見るので、隣り合う行はほとんど同じ先を見ている＝これも重複。
      ★実測（1回目の本走）＝先を見る本数 288 の順位で、上位50の 23〜31件 が日足だった。
    ★だから「その足のバー1本ぶん」と「先を見る本数」の、大きい方の間隔で間引く。
    """
    per = max(1, int(round(pd.Timedelta(TF_RULE[tf]) / pd.Timedelta("5min"))))
    return max(per, int(n))


def _rank_record_unmeasured(expected: set, measured: set, dropped: dict) -> dict:
    """測れなかった列を「省いた列」に理由つきで記録する（M2-3-4・2026-08-22 まこさん承認・acceptance 086a13df606d…）。

    ★何の穴か＝1回目の本走（2026-08-22）で、close vs T3%200__1d ほか4本が
      成績にも「省いた列」にも載らず、黙って消えていた（worklog 20260822 §28.4・恒久の決まり59番）。
      原因＝値決め窓で値が全部 NaN（助走が窓より長い）や、良い/悪いの片側が10未満のとき、
      分離力の辞書に入らないだけで、どこにも記録されなかった。
    ★既に理由が付いている列（重複で省いた等）は上書きしない。順位の値は1つも変えない。
    """
    for c in sorted(expected - measured - set(dropped)):
        dropped[c] = ("分離力を測れなかった（値決め窓で値が全部 NaN＝助走が窓より長い、"
                      "または 良い/悪いの片側の標本が10未満）＝黙って消さず記録（M2-3-4）")
    return dropped


# ══ 成績表の全走を、途中で落ちても続きから計算する（2026-10-03・工事 E・まこさん「データが途中落ちても残るようにできてるのか証明しろ」）══
#   なぜ＝2026-10-02 に全走（約2時間15分）が2回 途中で止まり、時間足11本の結果をメモリにだけ持つ作りだったので何も残らなかった。
#   直した後＝時間足を1本 計算し終えるごとに、その結果を OBSERVE_DIR/rank_resume/<指紋>/<時間足>.json に書く。
#     走らせ直すと、同じ指紋の置き場に在る時間足は読んで飛ばす。
#   ★指紋＝設定・材料の名前・先を見る本数・値決め窓・札の中身・5分足と1分足の元データ・この道具と札の部品と参照表のコードで決める
#     ＝どれか1つでも違えば別の置き場になり、前の結果を混ぜない。
#   ★書くときは一時の名前で書いてから名前を替える＝書きかけのファイルは読まない。
def _rank_resume_dir(win, cfg, cat_use, horizons, labels) -> pathlib.Path:
    """続きの結果の置き場（中身の指紋で決める）。"""
    import json as _json
    h = hashlib.sha256()

    def _add(x):
        h.update(_json.dumps(x, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8"))
    _add({"設定": {k: v for k, v in cfg.items() if k != "_source"}})
    _add({"材料": [c[0] for c in cat_use]})
    _add({"先を見る本数": [int(n) for n in horizons]})
    _add({"値決め窓": [str(win.index.min()), str(win.index.max()), int(len(win))]})
    h.update(pd.util.hash_pandas_object(win, index=True).to_numpy().tobytes())
    for n in horizons:
        for lab in REGIME_LABELS:
            _m, _u = labels[n][lab]
            h.update(_m.to_numpy(dtype=bool).tobytes())
            h.update(_u.to_numpy(dtype=bool).tobytes())
    _root = pathlib.Path(__file__).resolve().parent.parent.parent
    _one = _root / ONE_MIN_CSV
    _add({"1分足": [_one.stat().st_size, _one.stat().st_mtime_ns] if _one.exists() else None})
    for _p in (pathlib.Path(__file__), pathlib.Path(rl.__file__), pathlib.Path(iref.__file__)):
        h.update(_p.read_bytes())
    d = OBSERVE_DIR / "rank_resume" / h.hexdigest()[:16]
    d.mkdir(parents=True, exist_ok=True)
    return d


def _rank_resume_save(path: pathlib.Path, tf: str, auc: dict, nsample: dict) -> None:
    """その時間足の結果（分離力と独立な標本の数）を書く。一時の名前で書いてから名前を替える。"""
    import json as _json
    body = {"時間足": tf,
            "分離力": {c: {lab: {str(n): v for n, v in bn.items()} for lab, bn in by.items()}
                    for c, by in auc.items() if c.endswith(f"__{tf}")},
            "独立な標本の数": [[lab, int(n), t, int(v)] for (lab, n, t), v in nsample.items() if t == tf]}
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(_json.dumps(body, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _rank_resume_load(path: pathlib.Path, auc: dict, nsample: dict) -> None:
    """書き終わった時間足の結果を読んで、分離力と独立な標本の数に足す。"""
    import json as _json
    d = _json.loads(path.read_text(encoding="utf-8"))
    for c, by in d["分離力"].items():
        auc[c] = {lab: {int(n): float(v) for n, v in bn.items()} for lab, bn in by.items()}
    for lab, n, t, v in d["独立な標本の数"]:
        nsample[(lab, int(n), t)] = int(v)


def rank_materials_for_regime(bars: pd.DataFrame, cfg: dict, catalog: list | None = None,
                              horizons: tuple | None = None, tfs: list | None = None,
                              calc_rows: int | None = None) -> dict:
    """材料の列を値決め窓で作り、場面のラベル3本に対する分離力で順位づけする。戻り＝機械が読む形。

    ★売買しない・採点しない・金額を出さない（この道具の決まりのまま）。
    ★calc_rows＝列を作る本数（既定＝値決め窓の全部）。上位足の独立な標本を増やすため、
      1回目の本走のあと「後ろ 60,000本」から「全部」に広げた（2026-08-22・下の _independent_step）。
    """
    cat = catalog or build_catalog(cfg)
    horizons = tuple(horizons or _regime_horizons())
    _nm, a0, b0 = _insp_windows()[0]                          # 値決め窓（採点窓は1バーも使わない）
    win = bars.loc[(bars.index >= a0) & (bars.index < b0)]
    if calc_rows:
        win = win.iloc[-calc_rows:]
    _assert_search_window_only(win.index, "順位づけ")

    # ── ふるい（法則 C2・C3）＝「実質 同じもの」の省く側を、順位から外す（検査12 をそのまま使う）──
    dup = _dup_pairs(bars, cfg, cat)
    dropped: dict = {}
    for grp in _dup_groups([p for p in dup["pairs"] if p["判定"] == "実質 同じもの"]):
        keep, why, _tbl = _dup_keep_of_group(grp, dup.get("warm"))
        for g in grp:
            if g != keep:
                dropped[g] = f"{keep} と実質 同じ（残す理由＝{why}）"
    cat_use = [c for c in cat if c[0] not in dropped]

    roles = _role_lineage_table()
    use_tfs = list(tfs or cfg["timeframes"])
    labels = {n: _regime_labels(win, n) for n in horizons}
    _ck_dir = _rank_resume_dir(win, cfg, cat_use, horizons, labels)   # ★工事 E＝続きの結果の置き場
    auc: dict = {}                                            # 列名 → {ラベル: {N: 分離力}}
    nsample: dict = {}                                        # (ラベル, N, 時間足) → 独立な標本の数
    # ★進み具合を出す（2026-08-22 に足した）。1回目の本走が 2時間14分 のあいだ1行も出さず、
    #   まこさんが「あとどのくらい？」を聞けない状態だった。時間足を1本 終えるごとに出す。
    _t_begin = datetime.datetime.now()
    print(f"  … 始めます（時間足 {len(use_tfs)} 本 × 材料 {len(cat_use)} 種）", flush=True)
    for _i_tf, tf in enumerate(use_tfs, 1):
        _ck = _ck_dir / f"{tf}.json"
        if _ck.exists():                                      # ★工事 E＝書き終わった時間足は読んで飛ばす
            _rank_resume_load(_ck, auc, nsample)
            print(f"  … 時間足 {tf} は前に書き終わった結果を読んだ（{_i_tf}/{len(use_tfs)} 本・続きから）", flush=True)
            continue
        cfg_tf = dict(cfg)
        cfg_tf["timeframes"] = [tf]
        df, _meta = build_features(win, cfg_tf, cat_use)
        cols = [c for c in df.columns if c.endswith(f"__{tf}")]
        for n in horizons:
            step = _independent_step(tf, n)                   # 独立な標本だけを取る間隔（重複して数えない）
            grid = df.iloc[::step]
            for lab in REGIME_LABELS:
                mask, usable = labels[n][lab]
                ok = usable.reindex(grid.index).fillna(False).to_numpy()
                sub = grid.loc[ok, cols]
                m = mask.reindex(sub.index)
                if int(m.sum()) < 10 or int((~m).sum()) < 10:
                    continue
                nsample[(lab, n, tf)] = int(len(sub))
                r = rank_separation(sub, m, cols, set(), top=len(cols))
                for _i, row in r.iterrows():
                    auc.setdefault(row["特徴"], {}).setdefault(lab, {})[n] = float(row["分離力"])
            del grid
        del df
        _rank_resume_save(_ck, tf, auc, nsample)              # ★工事 E＝この時間足の結果を書く
        _el = (datetime.datetime.now() - _t_begin).total_seconds()
        _rest = _el / _i_tf * (len(use_tfs) - _i_tf)
        print(f"  … 時間足 {tf} 終わり（{_i_tf}/{len(use_tfs)} 本）"
              f"／ 経過 {_el/60:.1f} 分 ／ 残りの見込み {_rest/60:.1f} 分", flush=True)

    # ── 役割ごとに並べる（法則 C1＝ラベルごとに別々の順位。1本にまとめない）──
    order: dict = {}
    for role, spec in roles.items():
        lins = set(spec.get("lineages") or [])
        role_tfs = (use_tfs if spec.get("tfs") == "all"
                    else [t for t in (spec.get("tfs") or []) if t in use_tfs])
        want = []
        for name, _fn, _d in cat_use:
            ent, _prm = iref.find(name)
            if ent is None or iref.FAMILY_LINEAGE[ent["family"]]["k"] not in lins:
                continue
            want += [f"{name}__{t}" for t in role_tfs]
        order[role] = {}
        for lab in REGIME_LABELS:
            order[role][lab] = {}
            for n in horizons:
                got = [(c, auc[c][lab][n]) for c in want
                       if c in auc and lab in auc[c] and n in auc[c][lab]]
                got.sort(key=lambda t: -abs(t[1] - 0.5))
                order[role][lab][n] = got
    # ★「測れた列」と「順位に載った列」は別の数（2026-08-22 に両方 出すようにした）。
    #   役割の絞り（系統 × 時間足）に当たらない列は、測れていてもどの順位にも載らない。
    #   実測（1回目）＝6,057 測れて、載ったのは 5,937＝差の 120 は ローソク系15種 × 時間足8本
    #   （ローソクは trigger の役割にしか入っておらず、trigger が使える時間足は3本だけ）。
    #   直す前は「測れた列」しか出しておらず、この 120本 が見えなかった。
    # ★測れなかった列を黙って消さない（M2-3-4・2026-08-22 まこさん承認）
    expected_cols = {f"{name}__{t}" for name, _fn, _d in cat_use for t in use_tfs}
    _rank_record_unmeasured(expected_cols, set(auc), dropped)
    listed = {c for bl in order.values() for bn in bl.values() for got in bn.values() for c, _a in got}
    return dict(窓=(str(win.index.min()), str(win.index.max())), 行数=int(len(win)),
                先を見るバー数=list(horizons), 時間足=use_tfs, 測れた列=len(auc),
                順位に載った列=len(listed), どの役割にも入らなかった列=sorted(set(auc) - listed),
                省いた列=dropped, 独立な標本の数={f"{a}/{b}/{c}": v for (a, b, c), v in nsample.items()},
                順位=order)


def _insp_regime_rank(bars: pd.DataFrame, cfg: dict, catalog: list | None = None,
                      tfs: list | None = None) -> list[str]:
    """場面を分ける材料の順位を出して印字し、機械が読む形でも書き出す（M2-3-3）。

    ❌ は出さない＝どの列を使うかは engine_tuner が探す（この道具は線を引かない）。
    """
    import json
    r = rank_materials_for_regime(bars, cfg, catalog, tfs=tfs)
    print(f"  値決め窓 {r['窓'][0]} 〜 {r['窓'][1]} の {r['行数']} 本 ／ 時間足 {r['時間足']}")
    print(f"  先を見るバー数 N＝{r['先を見るバー数']}"
          f"（出どころ＝recipes/regime_label.json の採点に使う版・札の版 {rl.version_tag()}）")
    print(f"  ラベル3本＝{list(REGIME_LABELS)}（法則 C1＝強さと向きは別の指標なので1本にまとめない）")
    miss = r.get("どの役割にも入らなかった列") or []
    print(f"  分離力を測れた列 {r['測れた列']} 本 ／ そのうち どれかの役割の順位に載った列 "
          f"{r.get('順位に載った列', 0)} 本 ／ どの役割にも入らなかった列 {len(miss)} 本"
          f" ／ 重複で省いた列 {len(r['省いた列'])} 本")
    if miss:
        from collections import Counter as _C
        c = _C(x.rsplit("__", 1)[1] for x in miss)
        print("     ★どの役割にも入らなかった列の内訳（時間足ごと）＝"
              + " ／ ".join(f"{k} {v}本" for k, v in sorted(c.items())))
        print("     ＝役割の絞り（系統 × その役割が使える時間足）に当たらない列。型の表のとおりの動き")
    ns = r.get("独立な標本の数") or {}
    if ns:
        print("  ★独立な標本の数（重複して数えない＝上位足は その足のバー1本ぶん、"
              "ラベルは先を見る本数、の大きい方で間引いた）")
        for k in sorted(ns, key=lambda x: ns[x]):
            print(f"     {k} = {ns[k]} 個")
    for nm, why in list(r["省いた列"].items())[:20]:
        print(f"     ・省いた: {nm}（{why}）")
    for role, by_lab in r["順位"].items():
        for lab, by_n in by_lab.items():
            for n, got in by_n.items():
                if not got:
                    print(f"  [{role} / {lab} / N={n}] 測れた列なし")
                    continue
                head = " ／ ".join(f"{c}={a:.3f}" for c, a in got[:5])
                print(f"  [{role} / {lab} / N={n}] {len(got)} 列 ／ 上位5＝{head}")
    out = pathlib.Path(__file__).resolve().parents[2] / ".claude" / "ratchet" / "material_ranking.json"
    body = dict(r)
    body["札の版"] = rl.version_tag()   # ★M2-F-6d＝どの版の札で作った成績表か（まこさん決定 2026-09-28 の構造の文の3つ目・§51 の2）
    body["順位"] = {ro: {la: {str(n): v for n, v in bn.items()} for la, bn in bl.items()}
                    for ro, bl in r["順位"].items()}
    out.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  ★機械が読む形で書き出した: {out}（M2-3-4 で案を作るプログラムが読む）")
    return []


def rank_regime(bars_csv: str, config_path: str | None = None, tfs: str | None = None,
                cols: str | None = None) -> None:
    """--rank-regime の入口。5分足CSVを1つ渡す（売買記録は使わない）。"""
    cfg = load_config(config_path)
    bars = pd.read_csv(bars_csv, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    cat_all = build_catalog(cfg)
    cat = cat_all
    if cols:                                   # 絞ったことは必ず印字する（黙って一部だけ測らない）
        rx = re.compile(cols)
        cat = [c for c in cat_all if rx.search(c[0])]
        if not cat:
            raise SystemExit(f"[--cols] その名前の列は材料に無い: {cols}")
    print("#" * 100)
    print("# 場面を分ける材料の順位（M2-3-3・read-only・売買しない・採点しない・金額を出さない）")
    print(f"# 対象: {bars_csv}（{len(bars)} 行 / {bars.index.min()} 〜 {bars.index.max()}）")
    print(f"# 設定: {cfg['_source']} ／ 指標 {len(cat_all)} 種")
    if cols:
        print(f"# ⚠️ --cols 指定＝材料 {len(cat_all)} 種のうち {len(cat)} 種だけを測る"
              f"（ほかの列は測っていない）: {[c[0] for c in cat][:20]}")
    if tfs:
        print(f"# ⚠️ --rank-tf 指定＝時間足 {cfg['timeframes']} のうち {tfs} だけを測る")
    print("#" * 100)
    _insp_regime_rank(bars, cfg, catalog=cat,
                      tfs=[t.strip() for t in tfs.split(",")] if tfs else None)
    # ★監査 CP45＝全走（列も時間足も絞らない）のときは、続けて需給3列を足し直す（まこさん決定 2026-09-06）。
    if not cols and not tfs:
        add_demand_to_ranking(bars_csv, config_path)


# ══ 需給3列を成績表に足す（差分の口・M2-D-4／M2-D-5・設計書 iter="demand-in-ranking-20260907"・まこさん承認 2026-09-07）══
#   なぜ在るか＝成績表を作る本体（rank_materials_for_regime）は build_catalog の指標の列だけを採点し、
#     別枠の需給（load_demand の3列）を読まない＝需給は成績表に0本のまま（2026-09-06 実測・worklog 20260904 §49-2）。
#     まこさん決定（2026-09-06・逐語「需給に関しては、2-Cでの判断がどうであれ、順位に入れるべき」）＝需給を順位に入れる。
#     全走（約2時間17分）はやり直さず、需給3列だけを同じ物差しで採点して いまの成績表に足す（まこさん OK 2026-09-07）。
#   ★足すだけ＝既存の関数は1行も触らない。全走の本体と同じ関数（_regime_labels・_independent_step・rank_separation・
#     _role_lineage_table・load_demand）だけを呼ぶ＝式を2か所に持たない。
#   ★需給は元データが5分足1本だけ（型の表 extra_parts.demand の rule「時間足には展開しない」）＝成績表の列名は
#     `名前__5m` の1本だけ。11本に広げない。
#   ★重複のふるい（_dup_pairs・法則 C2・C3）は需給に掛けない（カタログの列どうしを比べる作りで、別枠を渡す形が無い）
#     ＝設計書 §7 の補3。走らせるときに「未適用」と印字する。
DEMAND_RANK_TF = "5m"


def _demand_rank_name(col: str) -> str:
    """成績表の列名（CVD__5m）から需給の名前（CVD）を返す。需給でなければ空。"""
    nm = col.rsplit("__", 1)[0] if "__" in col else col
    return nm if nm in _DEMAND_FILES else ""


def rank_demand_for_regime(bars: pd.DataFrame, cfg: dict, horizons: tuple | None = None,
                           calc_rows: int | None = None, files: dict | None = None) -> dict:
    """需給3列を値決め窓で作り、指標と同じ物差し（正解ラベル3本×先読み）で分離力を出す（差分の口・設計書 §4 の A）。

    戻り＝{"auc": {列名: {ラベル: {N: 分離力}}}, "unmeasured": {列名: 理由}, "cov": {需給の名前: 被覆率の文字列},
           "窓": (先頭, 末尾), "行数": 本数, "先を見るバー数": [N, ...]}
    ★売買しない・採点しない・金額を出さない。★files は自己検査が偽の元データを注入するためだけ（通常は渡さない）。
    """
    horizons = tuple(horizons or _regime_horizons())
    _nm, a0, b0 = _insp_windows()[0]                          # 値決め窓（採点窓は1バーも使わない）
    win = bars.loc[(bars.index >= a0) & (bars.index < b0)]
    if calc_rows:
        win = win.iloc[-calc_rows:]
    _assert_search_window_only(win.index, "需給の順位づけ")
    dem, cov = load_demand(win.index, files=files)            # 全走の材料と同じ元データの読み方（式を書き写さない）
    df = dem.copy()
    df.columns = [f"{c}__{DEMAND_RANK_TF}" for c in dem.columns]
    cols = list(df.columns)
    labels = {n: _regime_labels(win, n) for n in horizons}
    auc: dict = {}
    for n in horizons:
        step = _independent_step(DEMAND_RANK_TF, n)           # 全走と同じ間引き（独立な標本だけ）
        grid = df.iloc[::step]
        for lab in REGIME_LABELS:
            mask, usable = labels[n][lab]
            ok = usable.reindex(grid.index).fillna(False).to_numpy()
            sub = grid.loc[ok, cols]
            m = mask.reindex(sub.index)
            if int(m.sum()) < 10 or int((~m).sum()) < 10:
                continue
            r = rank_separation(sub, m, cols, set(), top=len(cols))
            for _i, row in r.iterrows():
                auc.setdefault(row["特徴"], {}).setdefault(lab, {})[n] = float(row["分離力"])
    unmeasured = {c: ("分離力を測れなかった（値決め窓で値が全部 NaN、または 良い/悪いの片側の標本が10未満）"
                      "＝黙って消さず記録（需給・差分の口）") for c in cols if c not in auc}
    return dict(auc=auc, unmeasured=unmeasured, cov=dict(cov),
                窓=(str(win.index.min()), str(win.index.max())), 行数=int(len(win)),
                先を見るバー数=[int(n) for n in horizons])


def merge_demand_into_ranking(rank: dict, r: dict) -> tuple[dict, list]:
    """A の結果を、いまの成績表（json を読んだ辞書）に足す（設計書 §4 の B）。指標の列は1本も書き換えない。

    戻り＝(足した後の成績表, 足した行の一覧 [(役割, ラベル, N, 列名, 分離力), ...])。
    fail-closed＝窓・先読み・時間足が成績表と一致しなければ止める。
    """
    import json as _json
    if list(rank.get("窓") or []) != list(r["窓"]):
        raise SystemExit(f"[需給の順位づけ] 窓が成績表と違う: 成績表={rank.get('窓')} ／ 今回={r['窓']}（fail-closed）")
    if [int(x) for x in (rank.get("先を見るバー数") or [])] != [int(x) for x in r["先を見るバー数"]]:
        raise SystemExit(f"[需給の順位づけ] 先を見るバー数が成績表と違う: 成績表={rank.get('先を見るバー数')} ／ "
                         f"今回={r['先を見るバー数']}（fail-closed）")
    if DEMAND_RANK_TF not in (rank.get("時間足") or []):
        raise SystemExit(f"[需給の順位づけ] 成績表の時間足に {DEMAND_RANK_TF} が無い: {rank.get('時間足')}（fail-closed）")
    order = rank["順位"]
    # 指標の列の控え（需給を除いた中身）＝足した後に1本も変わっていないことを照らす
    def _wo_demand(o: dict) -> dict:
        return {ro: {la: {str(nn): [x for x in got if not _demand_rank_name(str(x[0]))]
                          for nn, got in bn.items()} for la, bn in bl.items()} for ro, bl in o.items()}
    before = _json.dumps(_wo_demand(order), sort_keys=True, ensure_ascii=False)
    listed_before = {c for bl in order.values() for bn in bl.values() for got in bn.values() for c, _a in got}
    roles = _role_lineage_table()
    added: list = []
    for role, spec in roles.items():
        if "需給" not in (spec.get("lineages") or []):
            continue                                          # 需給の系統を持つ役割にだけ足す（型の表が正本）
        if spec.get("tfs") != "all" and DEMAND_RANK_TF not in (spec.get("tfs") or []):
            continue
        if role not in order:
            continue
        for lab in REGIME_LABELS:
            for n in r["先を見るバー数"]:
                key = str(n) if str(n) in order[role].get(lab, {}) else n
                got = list(order[role].get(lab, {}).get(key, []))
                kept = [x for x in got if not _demand_rank_name(str(x[0]))]      # 古い需給の行だけ入れ替える
                new = [(c, r["auc"][c][lab][n]) for c in sorted(r["auc"])
                       if lab in r["auc"][c] and n in r["auc"][c][lab]]
                merged = [list(x) for x in kept] + [[c, float(a)] for c, a in new]
                merged.sort(key=lambda t: -abs(float(t[1]) - 0.5))            # 全走と同じ並び（|分離力−0.5| の降順）
                order[role].setdefault(lab, {})[key] = merged
                added += [(role, lab, int(n), c, float(a)) for c, a in new]
    after = _json.dumps(_wo_demand(order), sort_keys=True, ensure_ascii=False)
    if before != after:
        raise SystemExit("[需給の順位づけ] 指標の列が変わった（足す処理が需給以外に触った＝fail-closed）")
    listed = {c for bl in order.values() for bn in bl.values() for got in bn.values() for c, _a in got}
    measured = sorted(set(r["auc"]))                       # ★set は回す前に sorted で並べる（H2 の番人）
    # 測れた列＝前の数 ＋ 今回 新しく測れた需給の列（前から載っていた需給の列は数え直さない＝2回 走らせても増えない）
    rank["測れた列"] = int(rank.get("測れた列", 0)) + len([c for c in measured if c not in listed_before])
    rank["順位に載った列"] = len(listed)
    omitted = dict(rank.get("省いた列") or {})
    for c, why in r["unmeasured"].items():
        omitted.setdefault(c, why)
    rank["省いた列"] = omitted
    rank["需給の被覆"] = dict(r["cov"])                        # 生成器は読まない欄＝順位の中身は変わらない
    rank["需給の重複のふるい"] = "未適用（_dup_pairs はカタログの列どうしを比べる作り＝設計書 §7 の補3）"
    return rank, added


def add_demand_to_ranking(bars_csv: str, config_path: str | None = None) -> None:
    """--rank-regime --add-demand の入口（設計書 §4 の C）＝成績表を読み → A → B → 同じファイルに書き戻す。"""
    import json as _json
    import time as _time
    t0 = _time.time()
    cfg = load_config(config_path)
    bars = pd.read_csv(bars_csv, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    out = pathlib.Path(__file__).resolve().parents[2] / ".claude" / "ratchet" / "material_ranking.json"
    if not out.exists():
        raise SystemExit(f"[需給の順位づけ] 成績表が無い: {out}（先に --rank-regime の本走で作る・fail-closed）")
    bak = out.with_name("material_ranking.before_add_demand.json")   # 走らせる前の控え（前後の突き合わせに使う・上書きしてよい）
    bak.write_bytes(out.read_bytes())
    rank = _json.loads(out.read_text(encoding="utf-8"))
    n_meas0, n_list0 = int(rank.get("測れた列", 0)), int(rank.get("順位に載った列", 0))
    print("#" * 100)
    print("# 需給3列を成績表に足す（差分の口・read-only の採点・売買しない・採点しない・金額を出さない）")
    print(f"# 対象: {bars_csv}（{len(bars)} 行 / {bars.index.min()} 〜 {bars.index.max()}）")
    print(f"# 成績表: {out}（足す前＝測れた列 {n_meas0} ／ 載った列 {n_list0}）")
    print("# ⚠️ 重複のふるい（_dup_pairs・法則 C2・C3）は需給に未適用（設計書 §7 の補3）")
    print("#" * 100)
    t1 = _time.time()
    r = rank_demand_for_regime(bars, cfg)
    t2 = _time.time()
    print(f"  値決め窓 {r['窓'][0]} 〜 {r['窓'][1]} の {r['行数']} 本 ／ 先を見るバー数 N＝{r['先を見るバー数']}")
    for nm, cv in r["cov"].items():
        print(f"  被覆 {nm}: {cv}")
    for c, why in r["unmeasured"].items():
        print(f"     ・省いた: {c}（{why}）")
    rank2, added = merge_demand_into_ranking(rank, r)
    t3 = _time.time()
    for role, lab, n, c, a in added:
        pos = [x[0] for x in rank2["順位"][role][lab][str(n) if str(n) in rank2["順位"][role][lab] else n]].index(c) + 1
        print(f"  [{role} / {lab} / N={n}] {c}={a:.3f}（{pos} 位）")
    body = dict(rank2)
    # ★M2-F-6d＝足す前の成績表と、いまの設定の札の版が同じでなければ書かない（違う札の順位を1つの表に混ぜない・fail-closed）。
    #   札の版が無い成績表＝版を持つ前に版1（er_median）の式で作った物（先を見るバー数の食い違いは merge_demand_into_ranking が先に止める）。
    _tag0 = rank.get("札の版") or rl.version_tag(version="er_median")
    if _tag0 != rl.version_tag():
        raise SystemExit(f"[需給の順位づけ] 成績表の札の版 {_tag0} と、いまの設定の札の版 {rl.version_tag()} が違う"
                         "（先に --rank-regime で作り直す・fail-closed）")
    body["札の版"] = rl.version_tag()
    out.write_text(_json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    t4 = _time.time()
    print(f"  ★足した後＝測れた列 {rank2['測れた列']} ／ 載った列 {rank2['順位に載った列']}"
          f"（足した行 {len(added)} 件・列 {len(r['auc'])} 本）")
    print(f"  ★機械が読む形で書き戻した: {out}")
    print(f"  経過時間＝読み込み {t1 - t0:.1f}秒 ／ 採点（ラベル作りを含む） {t2 - t1:.1f}秒 ／ 足す {t3 - t2:.1f}秒 ／ 書く {t4 - t3:.1f}秒")


def selftest_rank_demand(exit_: bool = True) -> list:
    """T-f＝需給を成績表に足す枝だけを、合成データで数秒 試す（設計書 §4 の D・口 --selftest-rank-demand）。

    ①A の分離力が、同じ入力で rank_separation を直に呼んだ値と一致する ②B が需給の系統を持つ役割にだけ3列を足す
    ③B の前後で指標の列が1つも変わらない ④先読みが違う成績表には止まる。
    """
    import json as _json
    import tempfile as _tf
    ng: list = []
    rng = np.random.default_rng(7)
    n_bars = 9000
    idx = pd.date_range(SEARCH_START, periods=n_bars, freq="5min")
    c = 100.0 + np.cumsum(rng.normal(0, 0.1, n_bars))
    bars = pd.DataFrame({"open": c, "high": c + 0.05, "low": c - 0.05, "close": c, "volume": 1.0}, index=idx)
    with _tf.TemporaryDirectory() as d:
        p_oi = pathlib.Path(d) / "oi.csv"
        p_tk = pathlib.Path(d) / "taker.csv"
        # ★偽のファイルは write_text で書く（検査6 と同じ）＝read-only 診断の番人が to_csv を止めるため
        _tl = 1.0 + rng.normal(0, 0.1, n_bars)
        _lg = 1.0 + rng.normal(0, 0.1, n_bars)
        _tb = rng.uniform(1, 3, n_bars)
        _ts = [t.strftime("%Y-%m-%d %H:%M:%S") for t in idx]
        p_oi.write_text("time,taker_ls,ls_global\n" + "\n".join(
            f"{t},{a:.6f},{b:.6f}" for t, a, b in zip(_ts, _tl, _lg)) + "\n", encoding="utf-8")
        p_tk.write_text("timestamp,taker_buy_base,volume\n" + "\n".join(
            f"{t},{a:.6f},4.0" for t, a in zip(_ts, _tb)) + "\n", encoding="utf-8")
        files = {"taker_ls": (str(p_oi), "time", "taker_ls"), "L-S比": (str(p_oi), "time", "ls_global"),
                 "CVD": (str(p_tk), "timestamp", None)}
        r = rank_demand_for_regime(bars, {}, files=files)
        # ① 同じ入力で rank_separation を直に呼んだ値と一致する（1つのラベル×先読みで照らす）
        n0 = r["先を見るバー数"][0]
        lab0 = REGIME_LABELS[0]
        dem, _cov = load_demand(bars.index, files=files)
        df = dem.copy()
        df.columns = [f"{x}__{DEMAND_RANK_TF}" for x in dem.columns]
        mask, usable = _regime_labels(bars, n0)[lab0]
        grid = df.iloc[::_independent_step(DEMAND_RANK_TF, n0)]
        ok = usable.reindex(grid.index).fillna(False).to_numpy()
        sub = grid.loc[ok, list(df.columns)]
        direct = rank_separation(sub, mask.reindex(sub.index), list(df.columns), set(), top=len(df.columns))
        for _i, row in direct.iterrows():
            got = r["auc"].get(row["特徴"], {}).get(lab0, {}).get(n0)
            if got is None or abs(float(got) - float(row["分離力"])) > 1e-9:
                ng.append(f"T-f①: {row['特徴']} の分離力が直に呼んだ値と違う: A={got} ／ 直={row['分離力']}")
        if len(r["auc"]) != 3:
            ng.append(f"T-f①: 需給3列のうち採点できたのが {len(r['auc'])} 列（合成データでは3列とも測れるはず）")
        # ② ③ ④ 小さな成績表に足す
        roles = _role_lineage_table()
        hz = r["先を見るバー数"]
        rank = {"窓": list(r["窓"]), "行数": r["行数"], "先を見るバー数": hz, "時間足": ["5m", "1h"],
                "測れた列": 2, "順位に載った列": 2, "省いた列": {},
                "順位": {ro: {la: {str(n): [["RSI14__5m", 0.61], ["ADX14__1h", 0.42]] for n in hz}
                              for la in REGIME_LABELS} for ro in roles}}
        keep = _json.dumps(rank["順位"], sort_keys=True, ensure_ascii=False)
        rank2, added = merge_demand_into_ranking(_json.loads(_json.dumps(rank)), r)
        want_roles = {ro for ro, sp in roles.items() if "需給" in (sp.get("lineages") or [])}
        for ro in roles:
            n_dem = sum(1 for la in REGIME_LABELS for n in hz
                        for x in rank2["順位"][ro][la][str(n)] if _demand_rank_name(str(x[0])))
            if ro in want_roles and n_dem != 3 * len(REGIME_LABELS) * len(hz):
                ng.append(f"T-f②: 役割 {ro} に需給が {n_dem} 行（期待 {3 * len(REGIME_LABELS) * len(hz)}）")
            if ro not in want_roles and n_dem:
                ng.append(f"T-f②: 需給の系統を持たない役割 {ro} に需給が {n_dem} 行 混ざった")
        rest = {ro: {la: {n: [x for x in got if not _demand_rank_name(str(x[0]))] for n, got in bn.items()}
                     for la, bn in bl.items()} for ro, bl in rank2["順位"].items()}
        if _json.dumps(rest, sort_keys=True, ensure_ascii=False) != keep:
            ng.append("T-f③: 足した後に指標の列が変わった")
        if rank2.get("順位に載った列") != 2 + 3:
            ng.append(f"T-f③: 載った列の数え直しが違う: {rank2.get('順位に載った列')}（期待 5）")
        if not rank2.get("需給の被覆"):
            ng.append("T-f③: 被覆率が成績表に残っていない")
        bad = _json.loads(_json.dumps(rank))
        bad["先を見るバー数"] = [int(hz[0]) + 1] + [int(x) for x in hz[1:]]
        try:
            merge_demand_into_ranking(bad, r)
            ng.append("T-f④: 先読みが違う成績表に足しても止まらない（fail-closed が効いていない）")
        except SystemExit:
            pass
    print(f"  T-f 需給を成績表に足す（差分の口）: ①直に呼んだ値と一致 ②需給の系統を持つ役割 {sorted(want_roles)} にだけ3列 "
          f"③指標の列は不変 ④先読み違いは止まる ／ 採点できた列 {len(r['auc'])} 本 ／ ❌ {len(ng)} 件")
    if exit_:
        for x in ng:
            print(f"  ❌ {x}")
        raise SystemExit(1 if ng else 0)
    return ng


def selftest_rank_resume(exit_: bool = True) -> list:
    """T-r＝成績表の全走が、途中で落ちても続きから計算できるか（工事 E・口 --selftest-rank-resume・壊すプログラム b126 が使う）。

    ①止めずに走らせた結果と、2本目の時間足で落としてから走らせ直した結果が、並びまで同じ
    ②落ちた後に、書き終わった1本目の時間足のファイルだけが残る
    ③走らせ直すと、1本目を読んで飛ばす（読んだのは1本）
    ④材料が違えば、同じ置き場でも前の結果を読まない
    ★乱数を使わない（決まった式の4本値）。★本物の成績表と続きの置き場は触らない（一時のフォルダ）。
    """
    global OBSERVE_DIR
    import json as _json
    import tempfile as _tf
    ng: list = []
    n_bars = 6000
    idx = pd.date_range(SEARCH_START, periods=n_bars, freq="5min")
    _i = np.arange(n_bars, dtype=float)
    _c = 100.0 + 3.0 * np.sin(_i / 40.0) + 0.002 * _i
    bars = pd.DataFrame({"open": _c, "high": _c + 0.05, "low": _c - 0.05, "close": _c,
                         "volume": 1.0 + (_i % 7)}, index=idx)
    cfg = load_config(None)
    cat = build_catalog(cfg)[:6]
    tfs = ["5m", "1h"]
    g = globals()
    keep_dir, keep_bf, keep_load = OBSERVE_DIR, g["build_features"], g["_rank_resume_load"]
    loads: list = []

    def _bf_fail(win, cfg_tf, catalog=None):
        if cfg_tf["timeframes"] == [tfs[1]]:
            raise RuntimeError(f"T-r: 試しに {tfs[1]} で落とす")
        return keep_bf(win, cfg_tf, catalog)

    def _load_count(path, auc, nsample):
        loads.append(path.name)
        return keep_load(path, auc, nsample)
    full = again = None
    with _tf.TemporaryDirectory() as d:
        try:
            OBSERVE_DIR = pathlib.Path(d) / "full"
            full = rank_materials_for_regime(bars, cfg, cat, tfs=tfs)
            OBSERVE_DIR = pathlib.Path(d) / "resume"
            g["build_features"] = _bf_fail
            try:
                rank_materials_for_regime(bars, cfg, cat, tfs=tfs)
                ng.append("T-r: 2本目で落とせなかった（試しの仕掛けが効いていない）")
            except RuntimeError:
                pass
            g["build_features"] = keep_bf
            left = sorted(p.name for p in (OBSERVE_DIR / "rank_resume").glob("*/*.json"))
            if left != [f"{tfs[0]}.json"]:
                ng.append(f"T-r②: 落ちた後に残ったファイルが {left}（期待 ['{tfs[0]}.json']）")
            g["_rank_resume_load"] = _load_count
            again = rank_materials_for_regime(bars, cfg, cat, tfs=tfs)
            if loads != [f"{tfs[0]}.json"]:
                ng.append(f"T-r③: 走らせ直したときに読んだのが {loads}（期待 ['{tfs[0]}.json']）")
            if _json.dumps(full, ensure_ascii=False, default=str) != _json.dumps(again, ensure_ascii=False, default=str):
                ng.append("T-r①: 止めずに走らせた結果と、落としてから走らせ直した結果が違う")
            if not full.get("測れた列"):
                ng.append("T-r①: 作り物の4本値で、分離力を測れた列が0本（試しになっていない）")
            loads.clear()
            rank_materials_for_regime(bars, cfg, cat[:5], tfs=tfs)
            if loads:
                ng.append(f"T-r④: 材料が違うのに、前の結果を読んだ: {loads}")
        finally:
            OBSERVE_DIR, g["build_features"], g["_rank_resume_load"] = keep_dir, keep_bf, keep_load
    print(f"  T-r 途中で落ちても続きから計算する（工事 E）: ①結果が同じ ②1本目だけ残る ③1本目を読んで飛ばす ④材料が違えば読まない"
          f" ／ 測れた列 {(full or {}).get('測れた列')} 本 ／ ❌ {len(ng)} 件")
    if exit_:
        for x in ng:
            print(f"  ❌ {x}")
        raise SystemExit(1 if ng else 0)
    return ng


def selftest_insp5(exit_: bool = True, bars_csv: str | None = None) -> list:
    """T-g・T-h・T-i・T-j＝検査5 の枠と、重い計算の使い回しの鍵を確かめる。

    設計書 insp5-frame-and-table-tidy-20260908 の やること F。口＝`--selftest-insp5`。
    ★軽い口にしている理由＝承認のプログラムの打ち切りは 120秒（approve_impl.sh:436）。
      全部の番人は 1分48秒 かかるので、この4件だけを短い切れ端で走らせる。
    ★全部の番人（selftest）からも、この関数を呼ぶ＝同じ判定を2か所に書き写さない。

      T-g＝1m の枠が、1分足の元データから作られている（本数が5分足と違う）
      T-h＝使い回しの鍵が、終値が同じで時刻だけ違う2つのデータで別の値を返す
      T-i＝1分足の元データが、値決め窓の助走ぶん前から採点窓の末まで覆っている
      T-j＝1m・3m を続けて計算しても、返った列の長さと、期間の当てはめの長さが一致する
           （直す前は 528,960 と 317,376 で食い違い、例外で止まった）
    """
    ng: list = []
    cfg = load_config()
    need_s = SEARCH_START - pd.Timedelta(days=int(cfg["warmup_days"]))
    # ★2026-09-08（監査 cp30 の Critical 1）＝要る末を、定数からではなく
    #   「検査5 が実際に使う5分足の最後のバー」から取る。
    #   直す前＝need_e = SCORE_END（＝その日の 00:00）。ところが検査5 が要るのは
    #   渡された5分足の最後のバー（いまのファイルだと 23:55）＝23時間55分 手前を見ていた。
    #   監査が「番人4件が全部 通るのに、検査5 は止まる」1分足を実際に作って再現した。
    #   ★危険の本命は5分足の側＝5分足だけを取り足して1分足をそのままにすると、
    #     定数を見ている限り番人は何も言わないまま、検査5 だけが落ちる。
    #   ★2026-09-08（監査 cp31 の Critical 1・別枠 E・F／設計書 insp5-path-and-tidy-head-20260908）
    #     ＝要る末の既定を、採点窓の定数ではなく **5分足の正本（BARS_CSV）の最後のバー** にした。
    #     直す前＝パスを渡さなければ定数を使ったので、番人を呼ぶ6か所がパスを書き写していた。
    #       取り足して名前が変わると、6か所とも古いファイルを指したままになった。
    #     直した後＝①既定は正本の末（パスを書き写さなくてよい）
    #               ②渡されたときは「正本の末」と「渡されたファイルの末」の**遅いほう**を使う
    #                 （別枠 E＝短い切れ端を渡しても守りが弱くならない）
    #               ③渡されたのが5分足かを見る（別枠 F＝1分足を渡しても通っていた）
    #     ★読むのはファイルの末尾 8KB だけ（全部は読まない）。
    _root5 = pathlib.Path(__file__).resolve().parent.parent.parent
    _base_ts = _tail_timestamps(_root5 / BARS_CSV, n=1)
    if _base_ts:
        need_e = _base_ts[-1]
    else:
        ng.append(f"T-i: 5分足の正本が読めない（{BARS_CSV}）")
        need_e = SCORE_END + pd.Timedelta("1D") - pd.Timedelta("5min")
    if bars_csv:
        _ts5 = _tail_timestamps(bars_csv, n=6)
        if not _ts5:
            ng.append(f"T-i: 渡された5分足のファイルを読めない（{bars_csv}）")
        else:
            _step5 = _bars_step_minutes(bars_csv)
            if _step5 is None or abs(_step5 - 5.0) > 1e-9:
                ng.append(f"T-l: 渡されたファイルが5分足ではない（バーの間隔 {_step5} 分）: {bars_csv}")
            need_e = max(need_e, _ts5[-1])

    # ── T-m＝data に、5分足の正本より後まで在るファイルが置かれていないか ──
    #   ★2026-09-08（監査 cp31 の Critical 1）＝取り足したのに BARS_CSV の指し先が古いままなら、
    #     ここで必ず落ちる（＝書き替え忘れを機械が見つける）。
    if _base_ts:
        _newer5, _bad5 = _newer_5m_files(_base_ts[-1])
        if _newer5:
            ng.append("T-m: data に、5分足の正本より後まで在るファイルが在る"
                      f"（正本 {pathlib.Path(BARS_CSV).name} の末 {_base_ts[-1]} ／ "
                      f"{_newer5[0][0]} の末 {_newer5[0][1]}）"
                      "＝5分足を取り足したなら BARS_CSV の指し先を直す"
                      "（★Binance Spot 系列だけ＝要件定義書 §8.2.1.1 の②）")
        if _bad5:                                       # ★2026-09-08（監査 cp32 の別枠 B）
            ng.append(f"T-m: 末の時刻が読めない5分足が data に在る（{_bad5[:3]}）"
                      "＝壊れているか、形が違う。黙って飛ばさずに報告する")

    # ── T-n・T-o＝T-m が見る範囲（監査 cp32 の Major・別枠 A・B）───────────
    #   ★一時のフォルダで試す＝本物の data には1文字も書かない。
    #   T-n＝Bitget 先物の5分足を、正本の候補として指さない
    #     （要件定義書 §8.2.1.1 の②＝採点に使うのは Binance Spot 系列だけ）。
    #   T-o＝下の階層に置かれた5分足を見つける／末が読めないものを黙って飛ばさない。
    with tempfile.TemporaryDirectory() as _td5:
        _dd = pathlib.Path(_td5)
        # ★期間の日付は手打ちしない（H8・periods.py が唯一の正本）。
        #   基準＝採点窓の最後の5分足のバー。見本は、そこから半年 後にする。
        _base5 = SCORE_END + pd.Timedelta("1D") - pd.Timedelta("5min")
        _later = str(_base5 + pd.Timedelta(days=184))
        (_dd / "BTCUSDT-5m-bitget-selftest.csv").write_text(
            f"timestamp,close\n{_later},1\n", encoding="utf-8")
        (_dd / "sub").mkdir()
        (_dd / "sub" / "BTCUSDT-5m-selftest.csv").write_text(
            f"timestamp,close\n{_later},1\n", encoding="utf-8")
        (_dd / "BTCUSDT-5m-selftest-badtail.csv").write_text(
            "timestamp,close\nこれは時刻ではない,1\n", encoding="utf-8")
        _n5, _b5 = _newer_5m_files(_base5, data_dir=_dd)
        _names5 = [x[0] for x in _n5]
        if any("bitget" in x.lower() for x in _names5):
            ng.append(f"T-n: Bitget 先物の5分足を、正本の候補として指した（{_names5}）"
                      "＝要件定義書 §8.2.1.1 の② に反する方へ人を導く")
        if not any("sub" in x for x in _names5):
            ng.append(f"T-o: data の下の階層に置いた5分足を見つけられない（{_names5}）")
        if not _b5:
            ng.append("T-o: 末の時刻が読めない5分足を、黙って飛ばした（報告が無い）")

    # ── T-k＝検査5 とほかの検査を一緒に名指ししても、検査5 が走るか ────────
    #   ★2026-09-08（監査 cp31 の Major 2）＝直す前は「検査5 だけを名指ししたとき」と
    #     「検査6 の直前」の2つの道しか無く、`--only 5,7` はどちらにも当たらずに黙って走らなかった。
    #     しかも まとめには「検査5: 判定なし」の行が出た（＝走っていないのに出た・別枠 I）。
    #   ★判定は本体と同じ `_insp_stage_plan` を呼ぶ（同じ判定を2か所に書き写さない）。
    try:
        _keys_k, _want5_k = _insp_stage_plan("5,7", ["検査6", "検査7", "検査8"])
    except SystemExit as e:                             # noqa: BLE001
        ng.append(f"T-k: 検査5 とほかの検査を一緒に名指しすると止まる: {str(e)[:60]}")
    else:
        if not _want5_k:
            ng.append("T-k: `--only 5,7` で検査5 が走らない（検査5 を名指ししたのに走らせない形）")
        if "検査7" not in _keys_k:
            ng.append(f"T-k: `--only 5,7` で検査7 が走らない（走る段＝{_keys_k}）")

    # ── T-i＝1分足の元データが、要る期間を覆っているか ──────────────────
    #   load_1m は覆っていなければ SystemExit を投げる（黙って値なしを作らない）。
    try:
        load_1m(need_s, need_e)
    except SystemExit as e:
        ng.append(f"T-i: 1分足の元データが要る期間を覆っていない（要 {need_s.date()}〜{need_e.date()}）: {e}")

    # ── T-h＝使い回しの鍵が、終値が同じで時刻だけ違うデータを見分けるか ──
    n = 64
    c = np.arange(n, dtype=float) + 100.0
    d1 = pd.DataFrame({"close": c}, index=pd.date_range("2024-01-01", periods=n, freq="5min"))
    d2 = pd.DataFrame({"close": c}, index=pd.date_range("2024-01-01", periods=n, freq="3min"))
    v1 = _cyc(d1, "selftest_th", lambda x: x.index[-1])
    v2 = _cyc(d2, "selftest_th", lambda x: x.index[-1])
    if v1 == v2:
        ng.append(f"T-h: 終値が同じで時刻だけ違う2つに、同じ値を返した（{v1}）＝鍵に時刻が入っていない")

    # ── T-g・T-j＝枠の作りと、長さの一致（短い切れ端で足りる）──────────
    #   ★短い切れ端で足りる理由＝長さの食い違いはデータの長さと無関係に、
    #     時刻の並びが違うことだけで起きる（2026-09-08 の やること H で確かめた噛み合わせ）。
    if not ng or all("T-i" not in x for x in ng):       # 元データが無いと、この2件は測れない
        days = 3
        span_s, span_e = SEARCH_START, SEARCH_START + pd.Timedelta(days=days)
        idx5 = pd.date_range(span_s, span_e, freq="5min", inclusive="left")
        c5 = 100.0 + np.arange(len(idx5), dtype=float) * 0.01
        span = pd.DataFrame({"open": c5, "high": c5 + 0.05, "low": c5 - 0.05,
                             "close": c5, "volume": 1.0}, index=idx5)
        one = load_1m(span.index[0], span.index[-1])
        src1, _cl1 = insp5_frame(span, "1m", one)
        if len(src1) <= len(span):
            ng.append(f"T-g: 1m の枠の本数が5分足以下（1m {len(src1)} 本 ／ 5分足 {len(span)} 本）"
                      "＝5分足を入れ直したものになっている")
        # T-j＝使い回しを通る指標を、1分 → 3分 の順に、入れものを共有したまま計算する。
        #      通らない指標は渡した枠の時刻をそのまま返すので、長さは必ず一致して素通りする。
        fn = next((f for nm, f, _d in build_catalog(cfg) if nm == "HT_INPHASE%"), None)
        if fn is None:
            ng.append("T-j: 材料の一覧に HT_INPHASE% が無い（使い回しを通る指標が選べない）")
        else:
            for tf in ("1m", "3m"):
                src, closed = insp5_frame(span, tf, one)
                try:
                    v = pd.to_numeric(fn(src), errors="coerce").notna().to_numpy()
                except Exception as e:                  # noqa: BLE001
                    ng.append(f"T-j: {tf} の列が計算できない: {str(e)[:60]}")
                    continue
                if len(v) != len(closed):
                    ng.append(f"T-j: {tf} で、返った列の長さ {len(v)} と、枠の長さ {len(closed)} が違う"
                              "（この食い違いが検査5 を例外で止めていた）")
    # ★2026-09-08（監査 cp31 の直しで T-k・T-l・T-m を足し、cp32 の直しで T-n・T-o を足した）
    #   ＝表示の名前も9件にそろえる（別枠 D と同じ型＝表示の数字が実物と食い違うのを避ける）
    print(f"  T-g/T-h/T-i/T-j/T-k/T-l/T-m/T-n/T-o 検査5 の枠・使い回しの鍵・"
          f"見るファイルの範囲（軽い口）: ❌ {len(ng)} 件")
    if exit_:
        for x in ng:
            print(f"  ❌ {x}")
        raise SystemExit(1 if ng else 0)
    return ng


# ══ 自己検査 ════════════════════════════════════════════════════════════
def _J(a: str, b: str) -> str:
    """検査文字列を分割して連結する（自己一致よけ）。

    番人が探す文字列を selftest 内に丸ごと書くと、その文字列を全置換したとき検査側も一緒に変わり、
    壊したのに pass してしまう（2026-07-26 メタ確認で実測・2026-07-21 の同型事案の再発）。
    連結して書けば、対象を置換しても検査側の文字列は変わらないので、番人が正しく落ちる。"""
    return a + b


def selftest_lineage(exit_: bool = True) -> list:
    """T-L1・T-L2＝系統の区分（indicator_reference_diag.LINEAGE_KINDS）を確かめる（工事 m2c15-roles-r1-20261021・2026-10-22）。
    口＝`--selftest-lineage`（壊すプログラムが使う・数秒で終わる）。全部の番人（selftest）からも、この関数を呼ぶ
    （直す前は selftest の検査8 の番人に「8系統の外の割当」の判定が在った＝ここへ移した・同じ判定を2か所に書かない）。
      T-L1＝系統マップ FAMILY_LINEAGE の札が、全部 系統の区分の中に在る
      T-L2＝答える問い LINEAGE_QUESTION の鍵が系統の区分と同じで、どの区分にも問いと出典が在る（材料の文書が区分ごとに問いを出す）"""
    ng: list = []
    _badk8 = [f for f, v in iref.FAMILY_LINEAGE.items() if v.get("k") not in iref.LINEAGE_KINDS]
    if _badk8:
        ng.append(f"T-L1: 系統マップに、系統の区分（{len(iref.LINEAGE_KINDS)}種）の外の札がある: {_badk8}")
    _q = iref.LINEAGE_QUESTION
    if set(_q) != set(iref.LINEAGE_KINDS):
        ng.append(f"T-L2: 答える問いの鍵が系統の区分と違う（問いだけに在る {sorted(set(_q) - set(iref.LINEAGE_KINDS))}・"
                  f"区分だけに在る {sorted(set(iref.LINEAGE_KINDS) - set(_q))}）")
    _emp = [k for k, v in _q.items() if not (isinstance(v, tuple) and len(v) == 2 and all(str(x).strip() for x in v))]
    if _emp:
        ng.append(f"T-L2: 答える問いか出典が空の区分: {_emp}")
    print("=" * 80)
    print("系統の区分の番人（T-L1・T-L2・工事 m2c15-roles-r1-20261021）")
    print(f"  系統の区分 {len(iref.LINEAGE_KINDS)} 種（{'・'.join(iref.LINEAGE_KINDS)}）／系統マップ {len(iref.FAMILY_LINEAGE)} 件")
    if exit_:
        if ng:
            for x_ in ng:
                print(f"  ❌ {x_}")
            raise SystemExit(1)
        print("  全部 pass（❌ 0件）")
        raise SystemExit(0)
    return ng


def selftest_band(exit_: bool = True) -> list:
    """T-B1〜T-B4＝帯の部品・S1 の部品・帯の1時間足の区切りを確かめる（工事 m2c15-band-s1-20261020・2026-10-20）。
    口＝`--selftest-band`（壊すプログラム b189〜b196 が使う・数秒で終わる＝承認の前の仮当ての 900 秒に収めるため）。
    ★全部の番人（selftest）からも、この関数を呼ぶ＝同じ判定を2か所に書き写さない。
    ★既知答えと独立の実装は、参照表（indicator_reference_diag の登録）を呼ぶ＝検査3 と同じものを使う（ここに答えを書き写さない）。
      T-B1＝新しい10種（帯スイング・帯スイング1時間ATR・帯pivot・帯pivot1時間ATR・帯pivot前週・帯pivot前週1時間ATR・帯VA・
            帯VA1時間ATR・LeeMykland・LeeMykland_E36版）の最初の名前で、参照表の手計算の既知答えが全部 一致する
      T-B2＝独立の実装を持つ種類は、既知答えの合成の足で、独立の実装と1本も違わない
      T-B3＝帯の1時間足の区切り＝正時（hour）の1時間足は、正時から次の正時の5分前までの5分足を束ね、その最後の足の時刻に置く（未来を見ない）。
            今の区切り（right）は、引数を渡さないときと同じ
      T-B4＝E36 の Lee-Mykland の式（spike_stat・spike_threshold）が、材料の表（observe_diag）の関数（式の置き場が1つ）"""
    ng: list = []
    fams = ("帯スイング", "帯スイング1時間ATR", "帯pivot", "帯pivot1時間ATR", "帯pivot前週", "帯pivot前週1時間ATR",
            "帯VA", "帯VA1時間ATR", "LeeMykland", "LeeMykland_E36版")
    first: dict = {}
    for name, fn, _d in build_catalog(load_config()):
        fam = find_material(name)[0]
        if fam in fams and fam not in first:
            first[fam] = (name, fn)
    for fam in fams:
        if fam not in first:
            ng.append(f"T-B1: 材料カタログに {fam} が1件も無い")
            continue
        name, fn = first[fam]
        ref, prm = iref.find(name)
        if ref is None or ref["known"] is None:
            ng.append(f"T-B1: {name} の既知答えが参照表に無い")
            continue
        for case, exp in ref["known"](prm):
            s = np.asarray(fn(case), dtype=float)
            # ★監査 CP84 の修正3＝engine_tuner が使う入口（make_material＝登録の計算式）も、カタログ（build_catalog＝_BAND_IMPL）と1本も違わないか
            s_mm = np.asarray(make_material(fam, *find_material(name)[1])[1](case), dtype=float)
            fin = np.isfinite(s)
            if (fin != np.isfinite(s_mm)).any() or not np.allclose(s[fin], s_mm[fin], atol=1e-9):
                ng.append(f"T-B5: {name}: engine_tuner の入口（make_material）とカタログ（build_catalog）で値が違う")
            for i, v, tol in exp:
                if not (abs(s[i] - v) <= tol):
                    ng.append(f"T-B1: {name}: 手計算の既知答えと不一致（位置 {i}・期待 {v}・実測 {s[i]}）")
            if ref["tb"] is not None:
                tb = np.asarray(ref["tb"](case, prm), dtype=float)
                both = np.isfinite(s) & np.isfinite(tb)
                if (np.isfinite(s) != np.isfinite(tb)).any() or not np.allclose(s[both], tb[both], atol=1e-9):
                    ng.append(f"T-B2: {name}: 独立の実装と不一致")
    import e37_scalp as _e37t                         # lazy（build_range_geometry と同じ読み込み方）
    v17 = _e37t._import_rg5().v17
    nb = 288 * 2
    xs = np.arange(nb, dtype=float) + 100.0
    d5 = pd.DataFrame({"open": xs, "high": xs, "low": xs, "close": xs, "volume": np.ones(nb)},
                      index=pd.date_range("2026-01-01", periods=nb, freq="5min"))
    hr = v17._resample(d5, "1h", "hour")
    t_first = d5.index[0] + pd.Timedelta(hours=10)               # 作り物の足の最初の時刻（0時）から 10時間後＝10:00
    t_last = t_first + pd.Timedelta(minutes=55)                   # 同じ1時間の最後の5分足＝10:55
    want = float(d5.loc[t_first:t_last, "high"].max())
    got = float(hr["high"].get(t_last, np.nan))
    if got != want:
        ng.append(f"T-B3: 正時の区切りの1時間足が、10:00〜10:55 の足を束ねて 10:55 に置く形でない（期待 {want}・実測 {got}）")
    if not v17._resample(d5, "1h").equals(v17._resample(d5, "1h", "right")):
        ng.append("T-B3: 今の区切り（right）が、引数を渡さないときと違う")
    import e36_short_oscillation as _e36t
    if getattr(_e36t.spike_stat, "__module__", "") != "observe_diag" or getattr(_e36t.spike_threshold, "__module__", "") != "observe_diag":
        ng.append("T-B4: E36 の Lee-Mykland の式が、材料の表（observe_diag）の関数でない（式の置き場が2つ）")
    print("=" * 80)
    print("帯の部品・S1 の部品・帯の1時間足の区切りの番人（T-B1〜T-B4・工事 m2c15-band-s1-20261020）")
    print(f"  種類 {len(first)} 件 ／ 正時の区切りの確かめ {nb} 本")
    if exit_:
        if ng:
            for x_ in ng:
                print(f"  ❌ {x_}")
            raise SystemExit(1)
        print("  全部 pass（❌ 0件）")
        raise SystemExit(0)
    return ng


def selftest_atr1h(exit_: bool = True, bars_csv: str | None = None) -> list:
    """T-A1〜T-A5＝S-Rタッチ1時間ATR（許容幅を1時間足の値動きの幅で決める部品）と検査16 の数え方を確かめる。

    設計書 m2e-bundle2-20260926（M2-E-4c・束2）。口＝`--selftest-atr1h`（壊すプログラム b104〜b107 が使う）。
    ★全部の番人（selftest）からも、この関数を呼ぶ＝同じ判定を2か所に書き写さない。
    ★既知答えと教科書の式は、参照表（indicator_reference_diag の S-Rタッチ1時間ATR の登録）を呼ぶ
      ＝検査3 と同じものを使う（ここに答えを書き写さない）。

      T-A1＝参照表の手計算の既知答え3件（下端に張り付く・上端に張り付く・1時間足と5分足で答えが割れる）が、
            全部の登録（窓 × 倍率 × ATR の期間）で一致する
      T-A2＝値決め窓の5分足の末尾 3,000本で、教科書の式（参照表の独立実装）と1本も違わない
      T-A3＝1時間足より長い足（4時間足）でも、build_features が列を作れる（1時間足の元の5分足が渡る）
      T-A4＝途中で切ったデータで計算し直しても、切った時点の許容幅の元（1時間足の ATR%）が変わらない（未来を見ない）
      T-A5＝検査16 の1マスの数え方（_tol_saturation_cells）が既知答えと一致する（値の出ている本数・下端の割合・上端の割合）
    """
    ng: list = []
    cfg = load_config()
    cat = [c for c in build_catalog(cfg) if c[0].startswith("S-Rタッチ1時間ATR(")]
    if not cat:
        ng.append("T-A1: 材料カタログに S-Rタッチ1時間ATR が1件も無い")
    # ── T-A1＝手計算の既知答え（参照表の known を呼ぶ）──
    for name, fn, _d in cat:
        ref, prm = iref.find(name)
        if ref is None or ref["known"] is None:
            ng.append(f"T-A1: {name} の既知答えが参照表に無い")
            continue
        for i, (cb, checks) in enumerate(ref["known"](prm) or [], 1):
            out = pd.to_numeric(fn(cb), errors="coerce")
            for pos, exp, atol in checks:
                got = out.iloc[pos]
                if not (pd.notna(got) and abs(float(got) - float(exp)) <= atol):
                    ng.append(f"T-A1: {name} の見本{i}＝期待 {exp} ／ 実際 {got}")
    # ── 値決め窓の5分足（T-A2〜T-A4 が使う・採点窓は使わない）──
    _root = pathlib.Path(__file__).resolve().parent.parent.parent
    bars = (pd.read_csv(bars_csv or (_root / BARS_CSV), parse_dates=["timestamp"])
            .set_index("timestamp").sort_index())
    win = bars.loc[(bars.index >= SEARCH_START) & (bars.index < SEARCH_END)]
    _assert_search_window_only(win.index, "S-Rタッチ1時間ATR の番人")
    s5 = win.iloc[-3000:]
    # ── T-A2＝教科書の式（参照表の tb）と突き合わせる ──
    for name, fn, _d in cat:
        ref, prm = iref.find(name)
        if ref is None or ref["tb"] is None:
            ng.append(f"T-A2: {name} の教科書の式が参照表に無い")
            continue
        a = pd.to_numeric(fn(s5), errors="coerce").iloc[-500:]
        b = pd.to_numeric(ref["tb"](s5, prm), errors="coerce").iloc[-500:]
        m = a.notna() & b.notna()
        if int(m.sum()) < 100:
            ng.append(f"T-A2: {name} の突き合わせる本数が足りない（{int(m.sum())} 本）")
            continue
        dmax = float((a[m] - b[m]).abs().max())
        if dmax > ref["tol"]:
            ng.append(f"T-A2: {name} が教科書の式と違う（最大差 {dmax}）")
    # ── T-A3＝1時間足より長い足（4時間足）でも列が作れる ──
    if cat:
        _H1_BASE["bars"] = None                          # ★前の計算の置き場を空にしてから試す（置き場に入れ忘れた道を見抜くため）
        big = win.iloc[-30000:]
        cfg4 = dict(cfg)
        cfg4["timeframes"] = ["4h"]
        feats, meta = build_features(big, cfg4, catalog=cat[:1])
        col = f"{cat[0][0]}__4h"
        if col not in feats.columns or int(feats[col].notna().sum()) == 0:
            ng.append(f"T-A3: 4時間足で {cat[0][0]} の列が作れない（{meta.get(col)}）")
        # ★T-A3 の2つ目（監査 CP44 の修正 1）＝4時間足に当てた1時間足の ATR% が、同じ5分足から作った1時間足の値と1本も違わない。
        #   4時間足のバーから ATR を作る形（2026-09-06 に外した誤りと同じ型）を見抜く。わざと外した形（4時間足のバーの ATR%）も
        #   同じ物差しに掛け、違いが出ることを毎回 確かめる（見抜く力の確かめ・検査15 の N4 と同じ考え）。
        _an3 = cfg["atr_periods"][0]
        _d4 = _resample(big[["open", "high", "low", "close", "volume"]], "4h")
        # ★監査 CP45＝置き場はここで入れ直さない（build_features が入れた中身をそのまま使う）。
        #   直す前＝ここで置き場に big を入れていたので、build_features が置き場に入れた中身（5分足か）を確かめていなかった
        #   （build_features が4時間足のバーを置き場に入れても、この突き合わせは通った）。
        try:
            _a4 = _atr_pct_1h_on(_d4, _an3)
        except ValueError as _e4:
            ng.append(f"T-A3: build_features が置き場に入れたもので、4時間足に当てる1時間足の ATR% が作れない（{_e4}）")
            _a4 = np.full(len(_d4), np.nan)
        _a5 = pd.Series(_atr_pct_1h_on(big, _an3), index=big.index)
        _at = _d4.index + pd.Timedelta("4h") - pd.Timedelta("5min")
        _in = _at.isin(big.index)
        _b5 = _a5.reindex(_at[_in]).to_numpy(float)
        _b4 = _a4[_in]
        _bw = (_atr(_d4.high, _d4.low, _d4.close, _an3) / _d4.close).to_numpy(float)[_in]
        _ok = ~np.isnan(_b4) & ~np.isnan(_b5)
        if int(_ok.sum()) < 100:
            ng.append(f"T-A3: 4時間足の値を突き合わせる本数が足りない（{int(_ok.sum())} 本）")
        elif float(np.abs(_b4[_ok] - _b5[_ok]).max()) > 1e-12:
            ng.append("T-A3: 4時間足に当てた1時間足の ATR% が、5分足から作った値と違う＝4時間足のバーから ATR を作っている疑い")
        elif float(np.abs(_bw[_ok] - _b5[_ok]).max()) <= 1e-12:
            ng.append("T-A3: わざと外した形（4時間足のバーの ATR%）でも同じ値になる＝この突き合わせは何も見抜けない")
    # ── T-A4＝途中で切って計算し直しても、切った時点の1時間足の ATR% が変わらない ──
    cuts = [i for i in range(len(s5) - 400, len(s5)) if s5.index[i].minute == 30][:5]
    if not cuts:
        ng.append("T-A4: 切る場所（毎時30分のバー）が見つからない")
    for an in cfg["atr_periods"]:
        full = _atr_pct_1h_on(s5, an)
        for i in cuts:
            v_cut = _atr_pct_1h_on(s5.iloc[: i + 1], an)[-1]
            v_full = full[i]
            if not ((np.isnan(v_cut) and np.isnan(v_full)) or abs(v_cut - v_full) <= 1e-12):
                ng.append(f"T-A4: {s5.index[i]} で切ると1時間足の ATR% が変わる"
                          f"（ATR の期間 {an}・全部 {v_full} ／ 切った {v_cut}）＝未来を見ている")
    # ── T-A5＝検査16 の張り付き割合の数え方の既知答え（監査 CP44 の修正 6）──
    #   倍率 1.0 × [0.001, 0.0012, 0.003, 0.007, 0.0015, 0.006, 空]＝値の出ている6本のうち、下端より小さいのは 0.001・0.0012 の2本、
    #   上端より大きいのは 0.007 の1本（ちょうど端の 0.0015・0.006 は数えない）→ ["6", "33.3%", "16.7%"]
    #   ★監査 CP45＝下端と上端の本数を変えた（前は 1本・1本＝20.0%・20.0% で、下端と上端の欄を取り違えても通った）。
    _c5 = _tol_saturation_cells(1.0, [0.001, 0.0012, 0.003, 0.007, 0.0015, 0.006, float("nan")])
    if _c5 != ["6", "33.3%", "16.7%"]:
        ng.append(f"T-A5: 検査16 の張り付き割合の数え方が既知答えと違う（{_c5}）")
    print("=" * 80)
    print("S-Rタッチ1時間ATR の番人（T-A1〜T-A5・設計書 m2e-bundle2-20260926）")
    print(f"  登録 {len(cat)} 件 ／ 値決め窓の5分足 {len(win)} 本 ／ T-A4 で切った時点 {len(cuts)} か所")
    if exit_:
        if ng:
            for x in ng:
                print(f"  ❌ {x}")
            raise SystemExit(1)
        print("  全部 pass（❌ 0件）")
        raise SystemExit(0)
    return ng


def _insp_hidden_params() -> list:
    """名前に出さない引数（工事 m2c15-hidden-params-20261004・2026-10-04）が、その列の計算に届いているかを確かめる。

    登録の計算式が、名前の {} の数より多く受け取る引数（既定つき）を1つずつ別の値にして、列が変わらなければ報告する。
    移動平均の for で登録した種類は、計算式 f の側の引数も見る。値動きは決まった式で作る（相場のデータは使わない）。
    ★別の値（下の _alt）は確かめのために渡す値で、指標の設定ではない（今の値と違えばよい）。"""
    import hashlib
    import inspect
    _load_pta()
    n = 600
    t = np.arange(n)
    c = 100 + 5 * np.sin(t / 17.0) + 2 * np.sin(t / 5.0) + 1.5 * np.sin(t / 1.7) + 3 * np.sin(t / 41.0) + t * 0.01
    d = pd.DataFrame({"open": c - 0.2 * np.cos(t / 3.0), "high": c + 0.6 + 0.2 * np.sin(t / 7.0),
                      "low": c - 0.6 - 0.2 * np.cos(t / 11.0), "close": c, "volume": 1000 + 100 * np.sin(t / 13.0)},
                     index=pd.date_range("2026-01-01", periods=n, freq="5min"))

    def _h(s):
        return hashlib.sha256(np.asarray(s, dtype=float).tobytes()).hexdigest()
    _int = r"len|roc|sma|signal|tcl|medium|^p$|^q$|^fast$|^slow$|^f_$|^s_$"
    _alt = {"poles": 3, "phase": 50, "a": 0.5, "c": 0.5, "sigma": 4, "k": 5, "d_": 5, "fast": 5, "medium": 10, "slow": 20,
            "slowlimit": 0.1, "fastlimit": 0.3}
    pos = {}
    for nm, _f, _d in build_catalog(load_config()):
        fam, prm = find_material(nm)
        if fam is not None and fam not in pos:
            pos[fam] = tuple(prm)
    # ★2026-10-09（工事 m2c15-shape-structure-20261009）＝形の材料（W字確定谷）は、上の決まった式の値動きでは形が1回も出ず、
    #   確定の本数 k を変えても列が変わらない（写しで実測）。その種類だけ、形が出る既知答えの合成の足（参照表の _w_case）で確かめる。
    _cases = {"W字確定谷": lambda: iref._w_case(24, 100.2)}
    # ★2026-10-20（工事 m2c15-band-s1-20261020）＝帯の部品も、上の決まった式の値動きでは帯が1回も出ず、確定の本数 k を変えても
    #   列が変わらない（全部 0）。帯が出る既知答えの合成の足（参照表の _band_case）で確かめる。
    #   （帯pivot・帯VA は名前に出さない引数を持たない＝触れた回数を数えない）
    for _bf in ("帯スイング", "帯スイング1時間ATR"):
        _cases[_bf] = lambda: iref._band_case("swing", 4)
    ng, seen = [], 0
    for fam, (tpl, _dr, fn) in MATERIAL_FAMILIES.items():
        P = pos.get(fam)
        if P is None or len(P) != tpl.count("{}"):
            continue
        ps = list(inspect.signature(fn).parameters.values())[1 + len(P):]

        def _numdef(p):                                  # 既定が None か数の引数だけ（文字・関数の既定は、数のパラメータではない）
            return p.default is None or (isinstance(p.default, (int, float)) and not isinstance(p.default, bool))
        kw = {p.name: p.default for p in ps if p.kind is not p.VAR_KEYWORD and p.name != "f" and _numdef(p)}
        fpar = inspect.signature(fn).parameters.get("f")
        if fpar is not None and callable(fpar.default) and any(p.kind is p.VAR_KEYWORD for p in ps):
            kw.update({p.name: p.default for p in list(inspect.signature(fpar.default).parameters.values())[2:] if _numdef(p)})
        if not kw:
            continue
        seen += 1
        dd = _cases[fam]() if fam in _cases else d
        base = _h(fn(dd, *P))
        for k, v in kw.items():
            if v is not None:
                alts = [v + 2, v + 6] if isinstance(v, int) else [v + 0.1, v * 2 + 0.3]
            else:
                a1 = _alt.get(k, 7 if re.search(_int, k) else 0.05)
                alts = [a1, a1 * 2 + 1 if isinstance(a1, int) else a1 * 3]
            moved, raised = False, 0
            for alt in alts:
                try:
                    if _h(fn(dd, *P, **{k: alt})) != base:
                        moved = True
                        break
                except Exception:                            # noqa: BLE001
                    raised += 1
            # ★別の値が全部 計算できなかった引数は数えない（数のパラメータではない＝登録の for が取り込んだ列の番号など）
            if not moved and raised < len(alts):
                ng.append(f"名前に出さない引数: {fam} の {k} を変えても列が変わらない（計算に届いていない）")
    if not seen:
        ng.append("名前に出さない引数: 受け取る登録が1つも無い")
    return ng


def selftest_match(exit_: bool = True, with_verified: bool = False, full: bool = False):
    """検査3（参照表との照合）と、写しの印の番人2つだけを走らせる軽い口
    （工事 k4-reference-known-20261011・2026-10-11・監査 CP60 の修正59）。
    口＝`--selftest-match`（完成の条件と壊すプログラム b172〜b183 が使う）。全体の自己テスト（selftest）からも full=True で呼ぶ。
    手本＝selftest_catalog（口の形・selftest からの呼び方）。★全体の自己テストは1本 約2分かかり、承認の前の仮当て（A12）の
    打ち切り 900秒に壊すプログラム12本が入らないため、検査3 と番人だけを切り出した。
    full=False（コマンドの口）＝検査3 を「手計算の既知答えを持つ登録の列と、写しの印の列」だけに絞る（壊すプログラムが落とす相手は
    全部この中に在る。全列では写しで92秒＝12本で900秒を超えた）。full=True（selftest から）＝正しいカタログの全列。
    with_verified=True のときは (ng, 一致検証済みの列の集合) を返す（selftest が「検証済みにならない列」を数えるのに使う）。"""
    cfg = load_config()
    ng = []
    import contextlib as _cl2
    import io as _io2
    _q = _io2.StringIO()
    _t3 = np.arange(6000, dtype=float)
    _c3 = pd.Series(100 + np.sin(_t3 / 9.0) * 2 + _t3 * 0.001,
                    index=pd.date_range("2026-03-01", periods=6000, freq="5min"))
    _sb3 = pd.DataFrame({"open": _c3.shift().fillna(_c3.iloc[0]), "high": _c3 + 0.1,
                         "low": _c3 - 0.1, "close": _c3, "volume": 1.0}, index=_c3.index)
    #  ①正しいカタログで検査3 が不一致を出さない（既知答え＝定義から導いた数字と、独立実装・ライブラリの照合）
    _catm = build_catalog(cfg)
    if not full:
        _catm = [x for x in _catm if (iref.find(x[0])[0] or {}).get("known") is not None
                 or (iref.find(x[0])[0] or {}).get("tb_kind") == "写し"]
        if not _catm:
            ng.append("既知答えを持つ列・写しの印の列がカタログに1本も無い（軽い口が回せない）")
    with _cl2.redirect_stdout(_q):
        _ng3m, _v3m, _r3m = _insp_indicator_match(_sb3, cfg, catalog=_catm)
    if _ng3m:
        ng.append(f"検査3 が正しいカタログで不一致を出す（許容差の線を疑う）: {_ng3m[:3]}")
    #  ②写しの印（tb_kind="写し"）の登録は、手計算の既知答えを必ず持つ（独立実装だけでは検証済みにならないため）
    for _e in iref.REFS:
        if _e.get("tb_kind") == "写し" and _e["known"] is None:
            ng.append(f"写しの印の登録に手計算の既知答えが無い: {_e['family']}")
    #  ③写しの印の列は、既知答えを外すと「一致検証済み」に入らない（独立実装が合っても検証済みに数えない）
    _cat_cp = [x for x in build_catalog(cfg)
               if (iref.find(x[0])[0] or {}).get("tb_kind") == "写し" and (iref.find(x[0])[0] or {}).get("tb") is not None]
    if not _cat_cp:
        ng.append("写しの印の列がカタログに1本も無い（この番人が回せない）")
    else:
        _ecp = iref.find(_cat_cp[0][0])[0]
        _kn_save = _ecp["known"]
        _ecp["known"] = None
        try:
            with _cl2.redirect_stdout(_q):
                _ngcp, _vcp, _rcp = _insp_indicator_match(_sb3, cfg, catalog=[_cat_cp[0]])
        finally:
            _ecp["known"] = _kn_save
        if _cat_cp[0][0] in _vcp:
            ng.append(f"写しの独立実装だけで一致検証済みになっている: {_cat_cp[0][0]}")
    if exit_:
        for x in ng:
            print(f"  ❌ {x}")
        print(f"  検査3（{'全列' if full else '既知答えを持つ列と写しの印の列 ' + str(len(_catm)) + ' 本'}）と写しの印の番人（--selftest-match）: ❌ {len(ng)} 件")
        raise SystemExit(1 if ng else 0)
    return (ng, _v3m) if with_verified else ng


def selftest_catalog(exit_: bool = True) -> list:
    """K-1・K-8・G-2 の番人だけを走らせる軽い口（工事 m2c15-indicator-six-items-20261004・2026-10-04）。
    口＝`--selftest-catalog`（完成の条件と壊すプログラム b128・b129・b131 が使う）。全体の自己テスト（selftest）からも呼ぶ。
    手本＝selftest_atr1h（口の形・selftest からの呼び方）。★全体の自己テストは約2分かかり、承認の前の仮当て（A12）で
    完成の条件と壊すプログラムが毎回それを走らせると20分を超えるため、番人だけを切り出した。"""
    cfg = load_config()
    ng = []
    _t3 = np.arange(6000, dtype=float)
    _c3 = pd.Series(100 + np.sin(_t3 / 9.0) * 2 + _t3 * 0.001,
                    index=pd.date_range("2026-03-01", periods=6000, freq="5min"))
    _sb3 = pd.DataFrame({"open": _c3.shift().fillna(_c3.iloc[0]), "high": _c3 + 0.1,
                         "low": _c3 - 0.1, "close": _c3, "volume": 1.0}, index=_c3.index)
    #  ①K-1＝COPC・FISHER・FISHERシグナル は macd_params の組で作る（修正13 の前と同じ）。AO の for に入ると AO の組の名前になる
    _nm_k1 = {nm for nm, _f, _d in build_catalog(cfg)}
    for (_f1, _s1, _g1) in cfg["macd_params"]:
        for _want1 in (f"COPC({_g1},{_f1},{_s1})", f"FISHER({_f1},{_g1})", f"FISHERシグナル({_f1},{_g1})"):
            if _want1 not in _nm_k1:
                ng.append(f"K-1: {_want1} がカタログに無い（macd_params の組で作られていない）")
    #  ②K-8 修正68＝上位足のずらし bar_close でも、本物の build_features を切り詰めて計算し直して値が変わらない（検査4 と同じ機構）。
    #    ★漏れは、上位足の中の決まった位置の5分足でだけ起きる＝最後の「上位足1本ぶん」の5分足を全部 切り詰めて確かめる（15m＝3本・2h＝24本）。
    #    あわせて now と値が違う（切り替えが効いている）
    _cat68 = [("close そのまま", lambda d: d.close, True)]
    for _tf68, _n68 in (("15m", 3), ("2h", 24)):
        _c68 = {**cfg, "timeframes": [_tf68], "warmup_days": 3, "htf_shift_mode": "bar_close"}
        _full68, _m68 = build_features(_sb3, _c68, catalog=_cat68)
        _cols68 = [c for c in _full68.columns if "close そのまま" in str(c)]
        if not _cols68:
            ng.append(f"K-8: 上位足のずらしの番人が列を作れない（{_tf68}）＝測れない")
            continue
        for _t68 in _sb3.index[-_n68:]:
            _tr68, _m68 = build_features(_sb3.loc[:_t68], _c68, catalog=_cat68)
            _x68, _y68 = _full68[_cols68[0]].loc[_t68], _tr68[_cols68[0]].loc[_t68]
            if pd.isna(_x68) != pd.isna(_y68) or (not pd.isna(_x68) and abs(float(_x68) - float(_y68)) > 1e-9 * max(1.0, abs(float(_x68)))):
                ng.append(f"K-8: 上位足のずらし bar_close で、切り詰めると値が変わる（{_tf68}・時点 {_t68}・未来参照の疑い）")
                break
        _now68, _m68 = build_features(_sb3, {**_c68, "htf_shift_mode": "now"}, catalog=_cat68)
        if _now68[_cols68[0]].equals(_full68[_cols68[0]]):
            ng.append(f"K-8: 上位足のずらし bar_close と now の値が同じ（{_tf68}・切り替えが効いていない）")
    #  ④材料の一覧の全部の名前が、参照表で引ける（全体の自己テストの「参照表の網羅」と同じ iref.coverage を呼ぶ）
    _miss = iref.coverage([nm for nm, _f, _d in build_catalog(cfg)])
    if _miss:
        ng.append(f"参照表に無いカタログ列 {len(_miss)} 件: {_miss[:5]}")
    #  ⑤G-2＝業界のライブラリとの対応表に足し忘れが無い（全体の自己テストの検査10 の番人と同じ iref.industry_gap を呼ぶ）
    try:
        import pandas_ta_classic as _pt10
        _ng10 = iref.industry_gap({k: list(v) for k, v in _pt10.Category.items()},
                                  [e["family"] for e in iref.REFS])["ng"]
        if _ng10:
            ng.append(f"検査10 が現状の対応表で不一致を出す（表の直し忘れ）: {_ng10[:3]}")
    except ImportError:
        ng.append("検査10 が使う pandas-ta-classic が入っていない（requirements.txt の版で入れる）")
    # ── 工事 m2c15-hidden-params-20261004 の番人（2026-10-04）──
    #  ⑥名前に出さない引数が、その列の計算に届いている
    ng += _insp_hidden_params()
    #  ⑦CKSP＝何も渡さない列が TradingView の形（まこさん 2026-10-04「２はC」。値はライブラリの注記「TV defaults=(10,1,9)」）
    _load_pta()
    _ck7 = _pta6.cksp(high=_sb3.high, low=_sb3.low, close=_sb3.close, p=10, x=1, q=9, tvmode=True)
    if not np.array_equal(_ck(_sb3).to_numpy(float), _ck7.to_numpy(float), equal_nan=True):
        ng.append("CKSP: 何も渡さない列が TradingView の形（10・1・9・rma）と違う")
    #  ⑧名前＝EMA の傾きと AO の名前に値が無い（まこさん 2026-10-04「指標名に閾値やパラメータの値を固定で入れて…やめてほしい」「A」）
    for _n8 in cfg["ema_periods"]:
        if f"EMA{_n8}傾き%" not in _nm_k1:
            ng.append(f"名前: EMA{_n8}傾き% がカタログに無い（名前に値が入った形に戻っている）")
    if "AO%" not in _nm_k1 or any(_x8.startswith("AO%(") for _x8 in sorted(_nm_k1)):
        ng.append("名前: AO% が、値の無い名前の1列になっていない")
    #  ⑨RCI＝参照表の RCI の行に mako の欄が在る（無いと、表を作り直したときに「使わない」へ戻る）
    if not any(_e9["family"] == "RCI" and _e9.get("mako") for _e9 in iref.REFS):
        ng.append("RCI: 参照表の RCI の行に mako の欄が無い（「使う」から外れる）")
    #  ⑩検査2＝上位足のずらし bar_close の形も確かめている（前の工事の実装 3・4・5）
    import inspect as _in10
    if _insp_close_leak(shift=True, mode="bar_close"):
        ng.append("検査2: 上位足のずらし bar_close の形で誤検出する")
    for _fn10 in (_insp_resample, selftest):
        # ★監査 CP62（2026-10-06）＝文字ではなく構文の木で、_insp_close_leak(…, mode="bar_close") の呼び出しが在るかを見る
        #   （直す前は文字で見たので、呼び出しをコメントにしても通った＝写しで実測）。
        import ast as _ast10
        if not any(isinstance(_c10, _ast10.Call) and getattr(_c10.func, "id", "") == "_insp_close_leak"
                   and any(_k10.arg == "mode" and isinstance(_k10.value, _ast10.Constant) and _k10.value.value == "bar_close"
                           for _k10 in _c10.keywords)
                   for _c10 in _ast10.walk(_ast10.parse(_in10.getsource(_fn10)))):
            ng.append(f"検査2: {_fn10.__name__} が、上位足のずらし bar_close の形を確かめていない")
    # ── 工事 m2c15-param-values-20261006 の番人（2026-10-06）──
    #  ⑪P-1＝指標ごとの一覧の種類は、カタログの名前がその一覧の組とちょうど同じ（ほかの指標の期間の一覧を使っていない）
    _per11 = cfg.get("material_params") or {}
    if not _per11:
        ng.append("P-1: 指標ごとの一覧 material_params が空")
    for _f11, _l11 in _per11.items():
        _want11 = {MATERIAL_FAMILIES[_f11][0].format(*_p11) for _p11 in _l11}
        _have11 = {_x11 for _x11 in sorted(_nm_k1) if find_material(_x11)[0] == _f11}
        if _want11 != _have11:
            ng.append(f"P-1: {_f11} のカタログの名前が、指標ごとの一覧と違う（多い {sorted(_have11 - _want11)[:4]}・無い {sorted(_want11 - _have11)[:4]}）")
    #  ⑫P-1＝残す名前（V9・採用中の戦略・確認のレシピ）がカタログに在る（まこさん決定「A」）
    if not cfg.get("material_keep"):
        ng.append("P-1: 残す名前 material_keep が空")
    for _g12, _l12 in (cfg.get("material_keep") or {}).items():
        _miss12 = [_x12 for _x12 in _l12 if _x12 not in _nm_k1]
        if _miss12:
            ng.append(f"P-1: 残す名前（{_g12}）がカタログに無い: {_miss12}")
    #  ⑬P-2＝設定の範囲は、指標ごとの一覧の組と残す名前の数字を、全部 含む（engine_tuner が V9 と採用中の戦略の値に届く）
    import json as _js13
    _rg13 = _js13.loads((pathlib.Path(__file__).resolve().parent / "recipes" / "search_limits.json").read_text(encoding="utf-8")).get("material_param_ranges") or {}
    if not _rg13:
        ng.append("P-2: 設定の範囲 material_param_ranges が空")
    _chk13 = {MATERIAL_FAMILIES[_f13][0].format(*_p13) for _f13, _l13 in _per11.items() for _p13 in _l13}
    _chk13 |= {_x13 for _l13 in (cfg.get("material_keep") or {}).values() for _x13 in _l13}
    # ★2026-10-07（監査 CP63 の修正6）＝一覧に入らない種類のカタログの名前も見る（VIDYA・T3 の列が範囲の外だった）
    _chk13 |= set(_nm_k1)
    for _x13 in sorted(_chk13):
        _e13, _p13 = iref.find(_x13)
        _ax13 = _rg13.get(_e13["family"]) if _e13 else None
        if not _ax13:
            if _e13 and find_material(_x13)[0] in _per11:
                ng.append(f"P-2: {_x13} の種類 {_e13['family']} に、設定の範囲 material_param_ranges が無い（指標ごとの一覧の種類）")
            continue
        for _i13, (_v13, _a13) in enumerate(zip(_p13, _ax13)):
            if not float(_a13["lo"]) <= float(_v13) <= float(_a13["hi"]):
                ng.append(f"P-2: {_x13} の {_i13 + 1} 番目の数字 {_v13} が、設定の範囲 {_a13['lo']}〜{_a13['hi']} の外")
    # ── 工事 m2c15-param-values-fix-20261007 の番人（2026-10-07・監査 CP63 の修正1）──
    #  ⑭段の候補（engine_tuner_gen._group_usable_col）は、列の数字が範囲の外なら使わない・範囲の中なら使う
    #    範囲は渡さない（None＝関数の中で本物と同じ範囲を読む）。ROC の範囲は設定の 9〜24（ROC3 は外・ROC12 は中）。
    import engine_tuner_gen as _g14
    _tb14 = _g14.load_signal_table()
    if _g14._group_usable_col("ROC3__5m", "ROC", "5m", None, _tb14):
        ng.append("修正1: 範囲の外の数字の列（ROC3）を、段の候補に使えると判定した")
    if not _g14._group_usable_col("ROC12__5m", "ROC", "5m", None, _tb14):
        ng.append("修正1: 範囲の中の数字の列（ROC12）を、段の候補に使えないと判定した")
    if exit_:
        for x in ng:
            print(f"  ❌ {x}")
        print(f"  K-1・K-8・G-2 の番人（--selftest-catalog）: ❌ {len(ng)} 件")
        raise SystemExit(1 if ng else 0)
    return ng


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
    if len(cfg["timeframes"]) < 3:
        ng.append(f"足が不正: {cfg['timeframes']}")
    # ★「1m は不正」を外した（2026-08-16・段7）。根拠＝CLAUDE.md の 1m 禁止は 2026-06-02 に
    #   まこさんが撤回済み／要件 R15「扱う時間足を1分足から1日足まで広げる」。
    #   代わりに、設定に無い足が混じっていないかだけを見る（TF_RULE が正本）。
    _bad_tf = [t for t in cfg["timeframes"] if t not in TF_RULE]
    if _bad_tf:
        ng.append(f"知らない足が設定に在る: {_bad_tf}")
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
    # ★フェーズ1 機構別分解＝配線され、ものさしは「その走行で実際に使った値」から解決する（2026-07-26 改訂）
    #   旧検査は「e37_scalp から import しているか」だった＝E38 の値を変えても古い E37 の値で分類する
    #   取り違えを許してしまうので、出所の解決を検査する形に作り替えた（まこさん OK）。
    if "_mech_decompose" not in inspect.getsource(_one_side):
        ng.append("機構別分解が observe に配線されていない")
    _src_mech = inspect.getsource(_mech_decompose)
    if _J("mech_thre", "sholds") not in inspect.getsource(observe):
        ng.append("フェーズ1 のものさしを本走で解決していない（古い値で分類する取り違えが起きる）")
    if _J("th, src = ", "mech") not in _src_mech:
        ng.append("フェーズ1 が解決済みのものさしを使っていない（自前で import に戻っている疑い）")
    if _J("ものさしの", "出所") not in _src_mech:
        ng.append("フェーズ1 がものさしの出所を印字していない（どの値で分類したか追えない）")
    import re as _re
    for _num in _re.findall(r"V5[39]_[A-Z_]+\s*=\s*[0-9]", inspect.getsource(mech_thresholds)):
        ng.append(f"フェーズ1 のものさしを手打ちしている: {_num}")
    # 既知答え＝①記録に値があればそれを使う ②無くて別の戦略なら None（表を出さない）
    import json as _json
    import shutil as _sh2
    import tempfile as _tf2
    _td2 = _tf2.mkdtemp()
    try:
        _csv = pathlib.Path(_td2) / "trades_x_score.csv"
        _csv.write_text("a\n1\n", encoding="utf-8")
        _sj = pathlib.Path(_td2) / "trades_x_score_params.json"
        _sj.write_text(_json.dumps({"script": "e38_priority_stack.py", "sections": {
            " / ".join(f"{k} = {i + 1}.5" for i, k in enumerate(_MECH_KEYS)): "テスト"}},
            ensure_ascii=False), encoding="utf-8")
        _th, _src = mech_thresholds(str(_csv))
        if _th is None or _th["V53_FAST_MIN"] != 1.5 or _th["V59_FLAT_ADV_PCT"] != 6.5:
            ng.append(f"フェーズ1 が記録の値を読めていない: {_th}")
        _sj.write_text(_json.dumps({"script": "e38_priority_stack.py"}, ensure_ascii=False), encoding="utf-8")
        _th2, _src2 = mech_thresholds(str(_csv))
        if _th2 is not None:
            ng.append("記録に閾値が無い別の戦略でも、ものさしを決めてしまう（取り違えの元）")
    finally:
        _sh2.rmtree(_td2, ignore_errors=True)
    for need in SECTIONS:
        if need not in src:
            ng.append(f"節が実装されていない: {need}")
    # ★Entry 候補観察（--scene・2026-07-25 まこさん承認）＝場面定義とコンフルエンス探索の番人
    sc_cfg = cfg.get("scenes") or {}
    if not sc_cfg:
        ng.append("scenes が config に無い（Entry 候補観察の場面定義）")
    for sid, s in sc_cfg.items():
        if s.get("type") not in _SCENE_TYPES:
            ng.append(f"scenes {sid} の型 {s.get('type')} が未実装（使えるのは {_SCENE_TYPES}）")
        if s.get("side") not in ("SHORT", "LONG"):
            ng.append(f"scenes {sid} の side が不正: {s.get('side')}")
    for key in ("conf_and_min", "conf_and_max", "conf_min_bars_per_day", "conf_trials"):
        if key not in cfg:
            ng.append(f"{key} が config に無い（コンフルエンス探索の条件）")
    src_conf = inspect.getsource(_conf_search)
    if 'suggest_categorical("cats"' not in src_conf:
        ng.append("コンフルエンス探索が異種カテゴリの組から選んでいない（同族の二度掛けを弾けない）")
    if "len(tfs) < 2" not in src_conf:
        ng.append("時間足2種以上の強制が無い（MTF コンフルエンスにならない）")
    if "_th_first" not in src_conf:
        ng.append("閾値が前半の分布から実値化されていない（後半で選び直しの疑い・L-267）")
    if "min_day" not in src_conf:
        ng.append("件数下限のゲートが無い（勝率だけ最大化して件数を消す逃げを弾けない）")
    src_lab = inspect.getsource(_scene_labels)
    if "i + 1" not in src_lab:
        ng.append("機械ラベルの entry が次バーになっていない（同バー約定＝未来参照の疑い・H2）")
    if "負け優先" not in src_lab:
        ng.append("同バー両到達の負け優先（保守）が無い")
    if "win_target" not in src_lab:
        ng.append("勝ち条件 win_target（mid/pct）の分岐が _scene_labels に無い")
    if "win_pct_k が 1.0 未満" not in inspect.getsource(observe_scene):
        ng.append("pct ラベルの床割れ番人（win_pct_k≥1）が observe_scene に無い（手数料負けの動きを勝ちと数えてしまう）")
    # ★不利側の番人（2026-07-26 まこさん OK）＝有利側だけの表示に戻れなくする物理検査。
    #   背景＝観察の勝率62%が実エンジンで −$70 になった乖離（L1ap・worklog 20260725 §20/§23）。
    #   ⚠️ 検査文字列は必ず連結して書く（"概" + "算" 等）＝検査対象と検査自身が同じ文字列だと、
    #      全置換で両方いっしょに書き換わって素通りする（2026-07-26 メタ確認で実測・observe_diag 2026-07-21 と同型）。
    src_scene = inspect.getsource(observe_scene)
    for need, why in ((_J("不利", "側"), "節0 に不利側の見出しが無い"),
                      (_J("概算の期", "待値"), "節0 に概算期待値の出力が無い"),
                      (_J("保有中の最", "大逆行"), "節0 に最大逆行の分布が無い"),
                      (_J("両半期とも 概算期", "待値がプラス"), "節3 に期待値での絞り込みが無い")):
        if need not in src_scene:
            ng.append(f"{why}＝有利側だけを出す設計に戻っている: {need}")
    if _J("前半_期", "待値%") not in src_conf:
        ng.append("コンフルエンス探索の組ごとに概算期待値%が並んでいない（勝率だけで層3 に渡してしまう）")
    # ★既知答えテスト（文字列検査では「名前だけ残って中身が消えた」を見抜けないので実測で照合する）。
    #   合成バー3本立て＝勝ち／災害線／時間切れ の決着幅と最大逆行を手計算値と突き合わせる。
    _syn_cases = [   # (種類, high, low, close, 勝ちか, 期待 res_pct%, 期待 mae_pct%)
        ("勝ち", [100.0, 100.2, 100.2, 100.2], [100.0, 99.4, 99.4, 99.4], [100.0, 99.6, 99.6, 99.6], True, +0.5, 0.2),
        ("災害線", [100.0, 101.6, 101.6, 101.6], [100.0, 99.9, 99.9, 99.9], [100.0, 101.5, 101.5, 101.5], False, -1.5, 1.6),
        ("時間切れ", [100.0, 100.3, 100.3, 100.3], [100.0, 99.7, 99.7, 99.7], [100.0, 100.1, 100.1, 100.1], False, -0.1, 0.3),
        # 同じバーで利確にも災害線にも着いた場合＝負け優先（保守）。これを入れないと「同着を勝ちに数える」
        # 改悪を番人が見逃す（2026-07-26 メタ確認で実測＝壊しても pass したので追加）。
        ("災害線", [100.0, 101.6, 101.6, 101.6], [100.0, 99.4, 99.4, 99.4], [100.0, 101.5, 101.5, 101.5], False, -1.5, 1.6),
    ]
    for kd, hh, ll, cc, exp_w, exp_r, exp_m in _syn_cases:
        nn = len(hh)
        bb = pd.DataFrame({"open": [100.0] * nn, "high": hh, "low": ll, "close": cc},
                          index=pd.date_range("2026-03-01", periods=nn, freq="5min"))
        gg = {"res_hi": np.full(nn, 101.0), "res_lo": np.full(nn, 100.5),
              "sup_hi": np.full(nn, 99.5), "sup_lo": np.full(nn, 99.0)}
        # SHORT・災害線 = res_hi + 1.0×レジ帯厚 = 101.5・勝ち = 建値 −0.5%（= 99.5）・時間切れ = 3本
        w_, o_, r_, m_, k_ = _scene_labels([0], bb, gg, "SHORT", 1.0, 3, np.full(nn, np.nan), "pct", 0.5)
        got = (bool(o_[0]), bool(w_[0]), str(k_[0]), round(float(r_[0]), 6), round(float(m_[0]), 6))
        if got != (True, exp_w, kd, round(exp_r, 6), round(exp_m, 6)):
            ng.append(f"不利側の既知答えテスト不一致 {kd}: 実測 {got} ／ 期待 {(True, exp_w, kd, exp_r, exp_m)}")
        # ★出口の組み合わせの既知答え（2026-07-26 まこさん OK）＝同じ合成バーで、従来の固定の仮定と
        #   同じ組み合わせ（利確 0.5%・損切り 災害線・保有 3本）を指定したら、上の _scene_labels と
        #   同じ勝ち負け・同じ決着幅になること。ここがずれたら「直したことにしない」（恒等の確認）。
        _sc = _scene_exit_scan([0], bb, gg, "SHORT", 1.0, np.full(nn, np.nan), ["mid", 0.5], ["zone"], 3)
        _w2, _r2 = _scene_exit_eval(_sc, 0.5, "zone", 3)
        if (bool(_w2[0]), round(float(_r2[0]), 6)) != (exp_w, round(exp_r, 6)):
            ng.append(f"出口の組み合わせが従来の固定の仮定と一致しない {kd}: "
                      f"実測 {(bool(_w2[0]), round(float(_r2[0]), 6))} ／ 期待 {(exp_w, exp_r)}")
    # ★出口の組み合わせの番人（2026-07-26 まこさん OK）
    _grid_cfg = {"scene_exit_tp_pcts": [0.2], "scene_exit_sl_pcts": [0.3], "scene_exit_tmax_bars": [6]}
    # 刻みを空にして1通りに戻したら止まること（＝出口の探索を消した状態を弾く）。
    # ⚠️ 空でない刻みで試すと「レンジ中央」「災害線」が常に足されて必ず2通り以上になり、検査が素通りする
    #    （2026-07-26 メタ確認で実測＝弾く処理を消しても pass したので、空の刻みで試す形に直した）。
    try:
        _scene_exit_grid({}, {"scene_exit_tp_pcts": [], "scene_exit_sl_pcts": [],
                              "scene_exit_tmax_bars": [6]})
        ng.append("出口の組み合わせが1通りでも通ってしまう（比べる意味が無い状態を弾けない）")
    except SystemExit:
        pass
    if _scene_exit_grid({"scene_exit_tmax_bars": [1, 2]}, _grid_cfg)[2] != [1, 2]:
        ng.append("出口の刻みを場面ごとに上書きできない（config の共通値しか使えない）")
    _src_exit = inspect.getsource(_scene_exit_rows)
    if _J("\"期待", "値%\", ascending=False") not in _src_exit:
        ng.append("出口の組み合わせを期待値で順位づけしていない（勝率で並べる設計に戻っている）")
    if _J("_scene_exit_", "scan(") not in src_scene:
        ng.append("フェーズ4 出口の組み合わせが本走（observe_scene）から呼ばれていない＝関数だけ在って動かない")
    # ★場面の型の登録表の番人（2026-07-26 まこさん OK＝型を足せるようにした）
    if _J("tuple(_SCENE_", "KINDS)") not in src:
        ng.append("場面の型の一覧を登録表から作っていない（手で並べた一覧はずれる）")
    for _t, _fn in _SCENE_KINDS.items():
        if not callable(_fn):
            ng.append(f"場面の型 {_t} が呼び出せない（登録表の中身が関数でない）")
    try:                                   # 登録していない型を場面に書いたら止まること
        _scene_mask({"type": "この型は登録していない"}, pd.DataFrame(
            {"open": [1.0], "high": [1.0], "low": [1.0], "close": [1.0], "volume": [1.0]}),
            {"rng": np.array([True]), "res_hi": np.array([1.0]), "res_lo": np.array([1.0]),
             "sup_hi": np.array([1.0]), "sup_lo": np.array([1.0]), "dev_z": None}, 0.08)
        ng.append("登録していない場面の型でも通ってしまう（型の取り違えを弾けない）")
    except SystemExit:
        pass
    # ★新しい型の既知答え（手計算・合成バー5本／帯 res 100.5-101.0・sup 99.0-99.5・線は 100.0 の1本）
    _nb = pd.DataFrame({"open": [99.6, 99.8, 100.2, 100.6, 100.4],
                        "high": [99.7, 100.1, 100.6, 100.7, 100.5],
                        "low": [99.5, 99.7, 100.0, 100.3, 99.9],
                        "close": [99.6, 99.8, 100.2, 100.6, 100.4],
                        "volume": [1.0] * 5},
                       index=pd.date_range("2026-03-01", periods=5, freq="5min"))
    _ng5 = {"rng": np.ones(5, bool), "res_hi": np.full(5, 101.0), "res_lo": np.full(5, 100.5),
            "sup_hi": np.full(5, 99.5), "sup_lo": np.full(5, 99.0), "dev_z": None}
    for _sc, _exp, _why in (
            ({"type": "resistance_touch_short"}, [2, 3, 4], "上端タッチの売り"),
            ({"type": "resistance_touch_short", "fresh_only": True}, [2], "上端タッチの売り（最初のバーだけ）"),
            ({"type": "grid_short", "grid_n": 2}, [1, 2], "グリッド売り（下から線に触れた）"),
            ({"type": "grid_long", "grid_n": 2}, [4], "グリッド買い（上から線に触れた）")):
        _m, _ = _scene_mask(_sc, _nb, _ng5, 0.08)
        if list(np.where(_m)[0]) != _exp:
            ng.append(f"場面の型の既知答え不一致 {_why}: 実測 {list(np.where(_m)[0])} ／ 期待 {_exp}")
    # ★手数料の番人（2026-07-26 まこさん指示で是正＝設計上の下限を手数料として引いていた）
    _c, _note = round_trip_cost()
    from eval_engine import MAKER_FEE as _mk, TAKER_FEE as _tk, SLIPPAGE as _sl
    if abs(_c - (_mk + _tk + _sl) * 100.0) > 1e-12:
        ng.append(f"1往復の実コストが eval_engine の確定値と違う: {_c}")
    if _J("from eval_engine import MAKER_FEE, TAKER_FEE, ", "SLIPPAGE") not in inspect.getsource(round_trip_cost):
        ng.append("手数料を eval_engine から取っていない（手打ちの疑い）")
    # 期待値を出す2か所（場面観察・増やす方向）が実コストを引いているか。売買記録の観察 observe は
    # 自分では期待値を出さず grow_search に委ねるので、ここでは見ない（見ると必ず落ちる誤検査になる）。
    for _fn, _why in ((observe_scene, "場面観察"), (grow_search, "増やす方向")):
        if _J("round_trip_", "cost()") not in inspect.getsource(_fn):
            ng.append(f"{_why} が期待値から実コストを引いていない（設計上の下限を引く形に戻っている）")
    if _J("floor = _scene_", "floor(cfg)") in inspect.getsource(observe_scene):
        ng.append("場面観察が期待値に SCALP_FLOOR（設計上の下限）を使っている＝手数料と取り違えている")
    # ★フェーズ11 増やす方向の番人（2026-07-26 まこさん OK）
    _gb = pd.DataFrame({"open": [1.0] * 10, "high": [1.0] * 10, "low": [1.0] * 10,
                        "close": [1.0] * 10, "volume": [1.0] * 10},
                       index=pd.date_range("2026-03-01", periods=10, freq="5min"))
    _gt = pd.DataFrame({"entry_time": [_gb.index[2], _gb.index[6]],
                        "exit_time": [_gb.index[3], _gb.index[6]], "side": ["SHORT", "SHORT"]})
    _fr = _free_bars(_gt, _gb, _gb.index[0], _gb.index[-1])
    if list(np.where(_fr)[0]) != [0, 1, 4, 5, 7, 8, 9]:
        ng.append(f"増やす方向の母集団に建てた玉のバーが混ざっている: 実測 {list(np.where(_fr)[0])} "
                  f"／ 期待 [0, 1, 4, 5, 7, 8, 9]（建てたバー2・保有中3・建てたバー6 を除く）")
    _src_grow = inspect.getsource(grow_search)
    if _J("前半_期待値%\"] > 0) & (df[\"後半_期", "待値%\"] > 0") not in _src_grow:
        ng.append("増やす方向の候補を期待値で絞っていない（勝率だけで足す候補にしてしまう）")
    if _J("バー", "/日") not in _src_grow:
        ng.append("増やす方向が件数（バー/日）を出していない（頻度を見ずに入口を足す）")
    if _J("grow_", "search(") not in inspect.getsource(observe):
        ng.append("フェーズ11 増やす方向が本走（observe）から呼ばれていない＝関数だけ在って動かない")
    # ★観察結果の保存の番人（2026-07-26 まこさん OK）＝①保存先が固定 ②上書きしない。
    #   ②は「呼んでいるふり」を文字列では見抜けないので、一時ディレクトリで実際に動かして確かめる。
    #   ⚠️ 2026-08-03 まこさん指示で置き場所を ratchet 直下 → その下の observe/ へ変えた。
    #      この番人は元「ratchet 直下に固定されているか」を見ていて、その変更を実際に捕まえた（正しく働いた）。
    #      固定先だけを新しいフォルダへ差し替える＝「固定されているか」を見る役目は変えない。
    if _out_path("scene", "L1ap").parent != OBSERVE_DIR:
        ng.append(f"観察結果の保存先が observe フォルダに固定されていない: {_out_path('scene', 'L1ap').parent}")
    if not _out_path("scene", "L1ap").name.startswith("observe_scene_L1ap_"):
        ng.append(f"保存名が observe_scene_<場面ID>_<実行日> の型でない: {_out_path('scene', 'L1ap').name}")
    if _out_path("trades", "trades_x_score").name != "observe_trades_x_score.txt":
        ng.append(f"売買記録モードの保存名が observe_<売買記録名> の型でない: {_out_path('trades', 'trades_x_score').name}")
    # ★節10 判定の番人（2026-07-26 まこさん OK）＝合成の売買記録で ①〜⑤ の集計を既知答えと突き合わせる。
    #   戦略名を見ずに共通9列だけで動くこと・巻き込みが出口理由を除いた場面で数えられていることを実測で確かめる。
    if _J("verdict(tr_", "all)") not in inspect.getsource(observe):
        ng.append("節10 判定が本走（observe）から呼ばれていない＝関数だけ在って動かない")
    _sy = pd.DataFrame([
        {"side": "SHORT", "ceil_type": "down", "exit_reason": "TIME_EXIT", "hold_min": 70,
         "gross_usd": -9.0, "fee_usd": 1.0, "net_usd": -10.0, "mfe_usd": 2.0, "mae_usd": -12.0},
        {"side": "SHORT", "ceil_type": "down", "exit_reason": "TP", "hold_min": 70,
         "gross_usd": 5.0, "fee_usd": 1.0, "net_usd": 4.0, "mfe_usd": 5.0, "mae_usd": -1.0},
        {"side": "SHORT", "ceil_type": "flat_up", "exit_reason": "TP", "hold_min": 10,
         "gross_usd": 3.0, "fee_usd": 1.0, "net_usd": 2.0, "mfe_usd": 3.0, "mae_usd": -0.5},
        {"side": "LONG", "ceil_type": "flat_up", "exit_reason": "SL", "hold_min": 200,
         "gross_usd": -2.0, "fee_usd": 1.0, "net_usd": -3.0, "mfe_usd": 1.0, "mae_usd": -5.0},
    ])
    import contextlib as _cl
    import io as _io
    with _cl.redirect_stdout(_io.StringIO()):
        _v = verdict(_sy)
    # cut_delta＝最悪の区分と同じ場面（SHORT×down×60-120分＝1行目 -10 と2行目 +4）を切ると
    #   その場面の純益 -6 が消える＝正味は +6（切ると良くなる側）。既にある数字の引き算であることの実測。
    _exp = {"n": 4, "net": -7.0, "per": -1.75,
            "worst": (("SHORT", "down", "TIME_EXIT", "60-120分"), -10.0), "wrap": (1, 4.0),
            "cut_delta": 6.0}
    for _k, _e in _exp.items():
        _g = _v.get(_k)
        if isinstance(_e, float):
            _g = round(float(_g), 6) if _g is not None else None
        if _g != _e:
            ng.append(f"節10 判定の既知答え不一致 {_k}: 実測 {_g} ／ 期待 {_e}")
    if (_hold_band(10), _hold_band(70), _hold_band(200), _hold_band(999)) != ("0-15分", "60-120分", "120-240分", "240分超"):
        ng.append("保有帯の区切りが期待どおりでない（③〜⑤ の区分がずれる）")
    import shutil as _sh
    import tempfile as _tf
    _td = pathlib.Path(_tf.mkdtemp())
    try:
        _p = _td / "observe_scene_TEST_20260726.txt"
        _p.write_text("古い結果", encoding="utf-8")
        _t = _Tee(_p)                       # 既存があるので archive へ退避してから開くはず
        _t._f.write("新しい結果"); _t._f.close()
        _moved = _td / "archive" / _p.name
        if not (_moved.exists() and _moved.read_text(encoding="utf-8") == "古い結果"
                and _p.read_text(encoding="utf-8") == "新しい結果"):
            ng.append("観察結果の保存が上書きしている（既存が archive へ退避されていない・§3.1 違反）")
    finally:
        _sh.rmtree(_td, ignore_errors=True)
    if "_scene_data" not in inspect.getsource(observe_scene) or "_resolve_period" not in inspect.getsource(_scene_data):
        ng.append("場面観察の期間が採点窓クランプ（_resolve_period）を通っていない")
    for need in SECTIONS_SCENE:
        if need not in src:
            ng.append(f"場面観察の節が実装されていない: {need}")
    # ★データと指標の検査（歩0・2026-07-30 まこさん OK）の番人＝わざと壊したデータ・式で ❌ が出ること
    import contextlib as _cl2
    import io as _io2
    _q = _io2.StringIO()
    # 検査1: high<low・重複・負の出来高 を混ぜたデータで全部検出すること
    _badb = pd.DataFrame({"open": [100.0, 100.0, 100.0], "high": [99.0, 101.0, 101.0],
                          "low": [100.5, 99.5, 99.5], "close": [100.2, 100.1, 100.1],
                          "volume": [1.0, 1.0, -1.0]},
                         index=pd.DatetimeIndex(["2026-03-01 00:00", "2026-03-01 00:05", "2026-03-01 00:05"]))
    with _cl2.redirect_stdout(_q):
        _f1 = _insp_source(_badb)
    for _need, _lbl in (("high < low", "high<low"), ("重複", "重複バー"), ("出来高", "負の出来高")):
        if not any(_need in x for x in _f1):
            ng.append(f"検査1 が壊れたデータ（{_lbl}）を見逃す: {_f1}")
    _okb = pd.DataFrame({"open": [100.0] * 5, "high": [100.5] * 5, "low": [99.5] * 5,
                         "close": [100.2] * 5, "volume": [1.0] * 5},
                        index=pd.date_range("2026-03-01", periods=5, freq="5min"))
    with _cl2.redirect_stdout(_q):
        _f0 = _insp_source(_okb)
    if _f0:
        ng.append(f"検査1 が正常なデータで誤検出: {_f0}")
    # 検査2: 「足が閉じた時刻へずらす」処理を外した壊れた組み立てで ❌ が出ること
    if not _insp_close_leak(shift=False):
        ng.append("検査2 が閉じる前のバーへの漏れを検出しない（ずらしを外しても素通り）")
    if _insp_close_leak(shift=True) or _insp_close_leak(shift=True, mode="bar_close"):   # ★K-8＝ずらし2種とも誤検出しない
        ng.append("検査2 が正しい組み立てで誤検出")
    # 検査3: RSI をわざと定数の式に差し替えたカタログで不一致が出ること・正しいカタログで一致すること
    _t3 = np.arange(6000, dtype=float)
    _c3 = pd.Series(100 + np.sin(_t3 / 9.0) * 2 + _t3 * 0.001,
                    index=pd.date_range("2026-03-01", periods=6000, freq="5min"))
    _sb3 = pd.DataFrame({"open": _c3.shift().fillna(_c3.iloc[0]), "high": _c3 + 0.1,
                         "low": _c3 - 0.1, "close": _c3, "volume": 1.0}, index=_c3.index)
    _fake = [(f"RSI{cfg['rsi_periods'][0]}", lambda d: d.close * 0 + 50.0, True)]
    with _cl2.redirect_stdout(_q):
        _ng3, _v3, _r3 = _insp_indicator_match(_sb3, cfg, catalog=_fake)
    if not any("不一致" in x for x in _ng3):
        ng.append("検査3 がわざと壊した式（RSI を定数化）を見逃す")
    # ★K-4（2026-10-11・監査 CP60 の修正59・工事 k4-reference-known-20261011）＝正しいカタログの検査3 と、写しの印の番人2つは
    #   軽い口 selftest_match に切り出した（壊すプログラムが測る口）。ここからも呼ぶ＝全体の自己テストの中身は減らさない。
    _ngm, _v3b = selftest_match(exit_=False, with_verified=True, full=True)
    ng += _ngm
    # ★山と谷の部品の番人（2026-08-21・M2-2-6・受け入れ条件 24a453d6… の確かめ方8）
    #   ＝足した5部品の式をわざと壊すと、検査3 が1件ずつ見つけること。
    #   ★RSI だけを壊す上の番人では、あとから足した部品が照合の対象に入っているかを確かめられない
    #     （47回目の教訓 L-516＝効かない壊し方のまま置くと、番人が居るのに何も守らない）。
    _frk = cfg["fractal_k"][0]
    for _frf in ("fractal高値距離%", "fractal安値距離%", "高値切り上げ幅%",
                 "安値切り上げ幅%", "構造破断距離%"):
        _frn = make_material(_frf, _frk)[0]
        with _cl2.redirect_stdout(_q):
            _ng3c, _v3c, _r3c = _insp_indicator_match(
                _sb3, cfg, catalog=[(_frn, lambda d: d.close * 0.0, True)])
        if not any("不一致" in x for x in _ng3c):
            ng.append(f"検査3 がわざと壊した式（{_frn} を定数化）を見逃す")
    # 山と谷の確定の本数が 0 以下なら止まること（未来を見ない作りの前提が崩れるため）
    try:
        _fractal_levels(_sb3.high, 0, True)
        ng.append("山と谷の確定の本数 0 で止まらない（_fractal_levels）")
    except SystemExit:
        pass
    # ★列の作り方の番人（2026-08-10 まこさん OK）＝計算が None を返しても全体が止まらず、
    #   「計算できず」として記録されること。前は囲いが fn(src) の1行だけで、囲いの外の
    #   s.copy() で止まった（実測＝69日ぶんのデータで AttributeError）。ライブラリには
    #   データが短いと例外でなく None を返す関数がある（t3 ほか）。
    _cfg_bf = dict(cfg)
    _cfg_bf["timeframes"] = ["5m", "1h"]                 # 上位足へのずらしも通す
    _bfb = pd.DataFrame({"open": [100.0] * 40, "high": [100.5] * 40, "low": [99.5] * 40,
                         "close": [100.2] * 40, "volume": [1.0] * 40},
                        index=pd.date_range("2026-03-01", periods=40, freq="5min"))
    _cat_none = [("わざとNoneを返す列", lambda d: None, True),
                 ("ふつうの列", lambda d: d.close, True)]
    try:
        _Xn, _mn = build_features(_bfb, _cfg_bf, catalog=_cat_none)
    except Exception as _e_bf:
        ng.append(f"列の作り方: 計算が None を返すと全体が止まる（本来は記録して飛ばす）: {str(_e_bf)[:60]}")
    else:
        if any(k.startswith("わざとNoneを返す列") and v[0] == "ok" for k, v in _mn.items()):
            ng.append("列の作り方: None を返した列を『ok』として通してしまう")
        if any(c.startswith("わざとNoneを返す列") for c in _Xn.columns):
            ng.append("列の作り方: None を返した列が、材料の列として出てきてしまう")
        if not all(_mn.get(f"ふつうの列__{t}", ("", ""))[0] == "ok" for t in _cfg_bf["timeframes"]):
            ng.append(f"列の作り方: ふつうの列まで落としてしまう（誤検出）: "
                      f"{[(k, v) for k, v in _mn.items() if k.startswith('ふつうの列')]}")
    # ★段3（照合の相手を増やす・2026-08-09）の番人
    #  ① 2つ目の照合（pandas-ta ／ scipy）が実際に効く＝わざと少しずらした式で「2つ目の照合」の不一致が出る
    # ★2つ目の照合（pandas-ta / scipy）を持つ列を、カタログの実物から選ぶ（2026-08-11 に直した）。
    #   前は zscore20 を名前で決め打ちしていたが、同じ挙動の列を省いたときに消えて番人が落ちた。
    _cat_now = dict((nm, fn) for nm, fn, _d in build_catalog(cfg))
    _z3 = next((nm for nm in _cat_now
                if (iref.find(nm)[0] or {}).get("family") in iref.EXT2), None)
    if _z3 is None:
        ng.append("検査3 の2つ目の照合を持つ列がカタログに1本も無い（この番人が回せない）")
        _z3 = next(iter(_cat_now))
    _zfn = _cat_now[_z3]
    _fakex2 = [(_z3, lambda d: _zfn(d) * 1.01, True)]
    with _cl2.redirect_stdout(_q):
        _ngx2, _vx2, _rx2 = _insp_indicator_match(_sb3, cfg, catalog=_fakex2)
    if not any("2つ目の照合" in x and "不一致" in x for x in _ngx2):
        ng.append("検査3 の2つ目の照合（pandas-ta / scipy）が、わざとずらした式を見逃す")
    #  ② POC・VAH・VAL の手計算の既知答えが実際に効く＝わざとずらした式で「既知答えと不一致」が出る
    _vpn = cfg["vp_windows"][0]
    for _key in ("POC", "VAH", "VAL"):
        _nm = f"close vs {_key}%{_vpn}"
        _vfn = dict((nm, fn) for nm, fn, _d in build_catalog(cfg))[_nm]
        with _cl2.redirect_stdout(_q):
            _ngk, _vk, _rk = _insp_indicator_match(_sb3, cfg,
                                                   catalog=[(_nm, lambda d, f=_vfn: f(d) + 1.0, True)])
        if not any("既知答えと不一致" in x for x in _ngk):
            ng.append(f"{_key} の手計算の既知答えが、わざとずらした式を見逃す（3-4 の担保が死んでいる）")
    #  ③ 3-5 の数え方の既知答え（偽の表を渡して、数え方そのものを確かめる＝本物の表を壊さない）
    _fk = [dict(family="外部もなく既知答えも無い", ext=None, known=None),
           dict(family="外部は無いが既知答えは在る", ext=None, known=(lambda p: [])),
           dict(family="外部で照合できる", ext=(lambda d, p: None), known=None),
           dict(family="2つ目の照合がある", ext=None, known=None)]
    _no35, _om35 = _ref_coverage_counts(_fk, set())
    if (_no35, _om35) != (["外部もなく既知答えも無い", "外部は無いが既知答えは在る", "2つ目の照合がある"],
                          ["外部もなく既知答えも無い", "2つ目の照合がある"]):
        ng.append(f"3-5 の数え方が既知答えと合わない（外部なし{_no35} ／ 私の式だけ{_om35}）")
    _no35b, _om35b = _ref_coverage_counts(_fk, {"2つ目の照合がある"})
    if len(_no35b) != 2 or len(_om35b) != 1:
        ng.append(f"3-5 が『2つ目の照合が在る』を数から外せていない（{_no35b} / {_om35b}）")
    #  ④ POC・VAH・VAL に手計算の既知答えが在ること（3-4 が消えたら落とす）
    for _k in ("POC", "VAH", "VAL"):
        if next(e for e in iref.REFS if e["family"] == _k)["known"] is None:
            ng.append(f"{_k} に手計算の既知答えが無い（3-4 の担保が消えている）")
    # 参照表の網羅＝カタログ全列に定義・照合方法が登録されていること（登録漏れの列を作れない）
    _miss = iref.coverage([nm for nm, _f, _d in build_catalog(cfg)])
    if _miss:
        ng.append(f"参照表に無いカタログ列 {len(_miss)} 件: {_miss[:5]}")
    # 正しいカタログなら全列が検証済みになること（＝未検証ゼロの物理担保）
    _unver = [nm for nm, _f, _d in build_catalog(cfg) if nm not in _v3b]
    if _unver:
        ng.append(f"検証済みにならない列 {len(_unver)} 件: {_unver[:5]}")
    # 検査4: わざと未来を見る列（1本先の close）を注入して、切り詰め再計算が検出すること
    _n1 = -1
    _leaky = [("未来を見る列", lambda d: d.close.shift(_n1), True)]
    with _cl2.redirect_stdout(_q):
        _ng4 = _insp_lookahead(_sb3, {**cfg, "timeframes": ["5m"], "warmup_days": 3}, catalog=_leaky)
    if not any("未来を見る列" in x for x in _ng4):
        ng.append("検査4 がわざと入れた未来参照列（1本先の close）を見逃す")
    ng += selftest_catalog(exit_=False)              # ★K-1・K-8・G-2 の番人（工事 m2c15-indicator-six-items-20261004）
    # ★検査4 の静的検査の番人（2026-08-23・77番）＝本物のコード行は拾い、説明の文章（docstring）の同じ語は拾わない
    import h2_scan as _h2s
    _probe = "x = c" + ".shift(" + "-1)"                     # ここに直接 書くと hook が止まる（穴⑤）ので組み立てる
    if not _h2s.scan_text("def f():\n    " + _probe + "\n"):
        ng.append("検査4 の静的検査が、本物の未来参照の書き方を拾わない（甘くなっている）")
    if _h2s.scan_text('def f():\n    """説明: ' + _probe + ' は使っていません。"""\n    return 1\n'):
        ng.append("検査4 の静的検査が、説明の文章（docstring）の語で誤って止まる（77番が戻った）")
    for need in INSPECT_SECTIONS:
        if need not in src:
            ng.append(f"データと指標の検査の節が実装されていない: {need}")
    # ★検査8 レンジ幾何（歩3 冒頭①・2026-08-01）の番人＝系統マップの網羅・既知答え・壊した実装で❌
    _fam8 = []
    for _nm8, _f8, _d8 in cat:
        _e8, _p8 = iref.find(_nm8)
        if _e8 is not None:
            _fam8.append(_e8["family"])
    _fam8 += list(_DEMAND_FILES) + ["レンジ幾何", "時刻", "曜日"]
    _miss8 = iref.lineage_coverage(_fam8)
    if _miss8:
        ng.append(f"系統マップ FAMILY_LINEAGE に無い family: {_miss8}（G3 の割当表は全 family 必須・載っていない family は生成不可）")
    # ★2026-10-22（工事 m2c15-roles-r1-20261021）＝系統の区分の判定は selftest_lineage へ移した（軽い口と同じ判定を1か所に）
    ng += selftest_lineage(exit_=False)               # T-L1・T-L2（系統の区分と答える問い）
    _tol8, _tch8, _lb8 = _rg_zone_consts()
    _ng8 = iref.range_geo_known_check(build_range_geometry, _tol8, _tch8, _lb8)
    if _ng8:
        ng.append(f"検査8 の既知答えが正しい実装で落ちる: {_ng8[:2]}")

    def _broken8(b, _k=None):                   # わざと mid を 1% ずらした実装＝既知答えが落ちるはず
        g = build_range_geometry(b, _k)
        g["mid"] = g["mid"] * 1.01
        return g
    if not iref.range_geo_known_check(_broken8, _tol8, _tch8, _lb8):
        ng.append("検査8 がわざと壊したレンジ幾何（mid×1.01）を見逃す")
    for _cn8, _cv8 in iref.CONST_REGISTRY.items():
        if not str(_cv8.get("source", "")).strip():
            ng.append(f"定数レジストリ {_cn8} に出典が無い（出典必須＝設計書 §2.4-②）")
    if _J("inspect_", "data(") not in src or "--inspect" not in inspect.getsource(build_parser):
        ng.append("データと指標の検査が CLI（--inspect）に配線されていない")
    # ★検査6 需給（2026-07-30 まこさん OK）の番人＝壊した元データで ❌・終端より後の埋めを検出
    import tempfile as _tf6
    import shutil as _sh6
    _td6 = pathlib.Path(_tf6.mkdtemp())
    try:
        _bars6 = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0},
                              index=pd.date_range("2026-03-01", periods=200, freq="5min"))
        # 正常な元データ（1時間刻み・bars の途中で終わる）→ ❌ ゼロ・終端後は NaN のはず
        _ok6 = _td6 / "ok.csv"
        _ok6.write_text("time,taker_ls\n" + "\n".join(
            f"2026-03-01 {h:02d}:00:00,1.{h}" for h in range(8)) + "\n", encoding="utf-8")
        _files_ok = {"taker_ls": (str(_ok6), "time", "taker_ls")}
        with _cl2.redirect_stdout(_q):
            _f6 = _insp_demand(_bars6, files=_files_ok)
        if _f6:
            ng.append(f"検査6 が正常な需給データで誤検出: {_f6}")
        # 壊した元データ（重複タイムスタンプ＋負の値）→ 両方 ❌ のはず
        _bad6 = _td6 / "bad.csv"
        _bad6.write_text("time,taker_ls\n2026-03-01 00:00:00,1.0\n2026-03-01 00:00:00,1.1\n"
                         "2026-03-01 02:00:00,-5.0\n", encoding="utf-8")
        _files_bad = {"taker_ls": (str(_bad6), "time", "taker_ls")}
        with _cl2.redirect_stdout(_q):
            _f6b = _insp_demand(_bars6, files=_files_bad)
        for _need6, _why6 in (("重複", "重複タイムスタンプ"), ("負", "負の値")):
            if not any(_need6 in x for x in _f6b):
                ng.append(f"検査6 が壊れた需給データ（{_why6}）を見逃す: {_f6b}")
        # 終端より後を値で埋めた列（ffill の漏れ相当）を _demand_tail_ok が見抜くこと
        _end6 = _bars6.index[96]                                  # ＝元データ ok.csv の終端 08:00 と同時刻
        _leak6 = pd.Series(1.0, index=_bars6.index)               # 全部埋まっている＝終端後も値あり
        if _demand_tail_ok(_leak6, _end6):
            ng.append("検査6 が『終端より後を値で埋めている』を見逃す（未来の捏造を検出できない）")
        if not _demand_tail_ok(_leak6.where(_leak6.index <= _end6), _end6):
            ng.append("検査6 が正しい取り込み（終端後 NaN）を誤検出")
        # CVD の組み立て式（2×テイカー買い−出来高 の累積）を手計算の既知答えで確認（2026-07-30 見直し2）
        _cvd6 = _td6 / "cvd.csv"
        _cvd6.write_text("timestamp,taker_buy_base,volume\n"
                         "2026-03-01 00:00:00,7,10\n"
                         "2026-03-01 00:05:00,3,10\n"
                         "2026-03-01 00:10:00,4,8\n", encoding="utf-8")
        _g6, _c6 = load_demand(_bars6.index, {"CVD": (str(_cvd6), "timestamp", None)})
        _exp6 = [4.0, 0.0, 0.0]                                   # 2*7-10 / +2*3-10 / +2*4-8 の累積
        _got6 = [float(_g6["CVD"].iloc[i]) for i in range(3)]
        if any(abs(a - b) > 1e-9 for a, b in zip(_got6, _exp6)):
            ng.append(f"検査6 の CVD 組み立てが手計算の既知答えと合わない: {_got6} ≠ {_exp6}")
        # ★T-e（2026-09-05・監査 cp21 の M4）＝需給の元データが、値決め窓の先頭から在るか。
        #   本物の元データを load_demand に渡し、値決め窓の最初のバーで3種とも値が出ることを実測する。
        #   ★指し先が古い版（2024-04-01）だと、値決め窓の先頭（2024-03-01）は空のまま＝ここが ❌ になる。
        #   ★なぜ selftest に置くか（ほかに道が無いから）
        #     ①CLI の道（`--inspect … --only 6`）は、検査6 の前に必ず走る検査5 が例外で落ちて届かない
        #       （next_step §6 の134番・実測で切り分け済み）。
        #     ②検査6 の被覆の判定は画面に ⚠️ を出すだけで `ng` に足していない（この下の _insp_demand）
        #       ＝被覆が 0% でも終了コードは 0 のまま＝わざと壊しても止まらない。
        #   ★私は cp21 の報告で「検査5 が落ちるので T-e は走れず」と書いたが、それは誤りだった。
        #     load_demand を直接 呼べば、検査5 を1行も通さずに測れる（監査 cp21 の M4・P3）。
        _w0 = SEARCH_START
        _bars_te = pd.DataFrame(
            {"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0},
            index=pd.date_range(_w0, periods=12, freq="5min"))
        _dem_te, _cov_te = load_demand(_bars_te.index)
        for _nm_te in _DEMAND_FILES:
            if _nm_te not in _dem_te.columns:
                ng.append(f"T-e: 需給の列 {_nm_te} が作れない（被覆＝{_cov_te.get(_nm_te)}）")
            elif not bool(pd.notna(_dem_te[_nm_te]).any()):
                ng.append(f"T-e: 需給の列 {_nm_te} が、値決め窓の先頭 {_w0.date()} で1本も値を持たない"
                          f"（元データの指し先が値決め窓の先頭より後＝被覆 {_cov_te.get(_nm_te)}）")
        # 定義表 DEMAND_REF の網羅＝登録の無い需給列は検査6 が ❌ を出すこと（ドリフト検出）
        _ref_ng = []
        with _cl2.redirect_stdout(_q):
            _ref_ng = _insp_demand(_bars6, files={"未登録の需給列": (str(_ok6), "time", "taker_ls")})
        if not any("未登録" in x for x in _ref_ng):
            ng.append("検査6 が定義表 DEMAND_REF に無い需給列を見逃す（定義なしの列を足せてしまう）")
    finally:
        _sh6.rmtree(_td6, ignore_errors=True)
    # ★検査7 軸カタログ照合（2026-07-30 まこさん OK）の番人＝3者照合のドリフトを検出
    _p7 = pathlib.Path(__file__).resolve().parent.parent.parent / ".claude" / "ratchet" / "entry_exit_matrix.md"
    _ec = [ln for ln in _p7.read_text(encoding="utf-8").splitlines() if ln.lstrip().startswith("- **E-c")]
    if len(_ec) != 1:
        ng.append(f"entry_exit_matrix.md の E-c 行が {len(_ec)} 本（1本のはず）")
    else:
        _names7 = [nm for nm, _f, _d in build_catalog(cfg)] + list(_DEMAND_FILES)
        _ng7, _rows7 = iref.axis_ec_check(_ec[0], _names7)
        if _ng7:
            ng.append(f"検査7 が現状の E-c と対応表で不一致を出す（表の直し忘れ）: {_ng7[:3]}")
        _ng7b, _r7b = iref.axis_ec_check(_ec[0] + "/この指標は存在しない", _names7)
        if not _ng7b:
            ng.append("検査7 が E-c に足された未知の項目を見逃す（ドリフト検出が死んでいる）")
        _ng7c, _r7c = iref.axis_ec_check(_ec[0], [n for n in _names7 if n != "包み足"])
        if not any("包み足" in x or "engulfing" in x for x in _ng7c):
            ng.append("検査7 が『対応表は実装ありなのに列が無い』を見逃す（実装の欠落を検出できない）")
    # ★検査9 向きの穴（2026-08-09・マイルストーン①のフロー 段2）の番人＝わざと壊して落ちることを確かめる
    import contextlib as _cl9
    import io as _io9
    _q9 = _io9.StringIO()
    _d9, _s9, _g9 = _direction_gap(["close vs SMA20%", "close vs EMA9%", "EMA9傾き%", "RSI14"])
    if (_d9, _s9, _g9) != (["SMA20", "EMA9"], ["EMA9"], ["SMA20"]):
        ng.append(f"検査9 の拾い方が既知答えと合わない（距離{_d9} 向き{_s9} 穴{_g9}）")
    _names9 = [nm for nm, _f, _d in build_catalog(cfg)]
    _base9 = len(_direction_gap(_names9)[2])
    _cut9 = len(_direction_gap([n for n in _names9 if not n.startswith("EMA9傾き")])[2])
    if _cut9 != _base9 + 1:
        ng.append(f"検査9 が『向きの部品を消した』のを見逃す（穴 {_base9} → {_cut9}・+1 のはず）")
    with _cl9.redirect_stdout(_q9):
        _ng9 = _insp_direction_gap(cfg, catalog=[("RSI14", None, True)])
    if not _ng9:
        ng.append("検査9 が『距離の部品が1つも無い＝命名が変わって検査が死んだ』を見逃す")
    # ★検査10 業界のライブラリとの突き合わせ（2026-08-09・同）の番人
    try:
        import pandas_ta_classic as _pt10
        _lib10 = {k: list(v) for k, v in _pt10.Category.items()}
    except Exception:                                           # noqa: BLE001
        _lib10 = None
        ng.append("検査10 が使う pandas-ta-classic が入っていない（requirements.txt の版で入れる）")
    if _lib10 is not None:
        _fams10 = [e["family"] for e in iref.REFS]
        if iref.industry_gap(_lib10, _fams10)["ng"]:
            ng.append(f"検査10 が現状の対応表で不一致を出す（表の直し忘れ）: "
                      f"{iref.industry_gap(_lib10, _fams10)['ng'][:3]}")
        _broke10 = {k: [f for f in v if f != "adx"] for k, v in _lib10.items()}
        if not any("adx" in x for x in iref.industry_gap(_broke10, _fams10)["ng"]):
            ng.append("検査10 が『対応表が指す関数がライブラリに無い』を見逃す（表の古さを検出できない）")
        if not any("この指標は存在しない" in x
                   for x in iref.industry_gap(_lib10, _fams10 + ["この指標は存在しない"])["ng"]):
            ng.append("検査10 が『対応表に無い指標が足された』を見逃す（材料を足しても表を直さずに済んでしまう）")
    # ★節12 まとめ の番人（2026-08-03・監査 4-18＝要件 R10・まこさん「案１でやってみて」）
    #   この節の約束は「新しい計算を1つもしない＝上の節が出した値をそのまま並べる」。
    #   約束が破られたら（集計や並べ替えを足したら）ここで落とす。
    #   ⚠️ 検査文字列は連結して書く（全置換で検査自身も一緒に書き換わって素通りするのを防ぐ・既存と同型）。
    src_na = inspect.getsource(next_actions)
    for _bad in ("groupby", "sort_values", ".mean(", ".sum(", ".median(", "nlargest", "quantile"):
        if _bad in src_na:
            ng.append(f"節12 が自分で集計している（{_bad}）＝上の節の値をそのまま並べる約束に反する")
    for _need in (_J("worst_", "rows"), "picked", "grown"):
        if _need not in src_na:
            ng.append(f"節12 が上の節の戻り値 {_need} を使っていない（自前で作り直している疑い）")
    src_main12 = inspect.getsource(observe)
    if "next_actions(" not in src_main12:
        ng.append("節12 が本走から呼ばれていない（実装したが動かない）")
    for _need, _why in (("vd = verdict(", "節10 の戻り値を受けていない"),
                        ("picked = _summary(", "節9 の戻り値を受けていない"),
                        ("grown = grow_search(", "節11 の戻り値を受けていない")):
        if _need not in src_main12:
            ng.append(f"節12 の材料が繋がっていない: {_why}")
    try:                                   # 3つとも空でも落ちない（診断が何も出さない走行でも本走を止めない）
        import io as _io12
        import contextlib as _ct12
        _buf12 = _io12.StringIO()
        with _ct12.redirect_stdout(_buf12):
            next_actions({}, [], {}, SCORE_START, SCORE_END)
        _out12 = _buf12.getvalue()
        # ★窓の印字は「実際の出力」で確かめる（ソースの文字列一致では素通りする＝2026-08-03 の
        #   メタ確認で実測。印字の行を消しても、説明文に同じ語が残っていて番人が落ちなかった）。
        for _need, _why in ((str(SCORE_START.date()), "この数字を作った期間（採点窓）の開始日"),
                            (str(SEARCH_START.date()), "値を選ぶ期間（値決め窓）の開始日")):
            if _need not in _out12:
                ng.append(f"節12 の出力に {_why} が出ていない（窓の取り違えを防げない）")
    except Exception as _e12:              # noqa: BLE001
        ng.append(f"節12 が空の入力で落ちる: {type(_e12).__name__} {_e12}")

    # ★出力先の番人（2026-08-03 まこさん指示「ratchet直下に出すのはやめて」）
    #   この道具の出力は observe/ フォルダの中だけ。ratchet 直下に1本も書かない。
    for _kind in ("trades", "scene", "inspect", "plan"):
        _p = _out_path(_kind, "検査用")
        if _p.parent != ratchet_io.RATCHET / "observe":
            ng.append(f"出力先が observe フォルダの外: {_kind} → {_p.parent}")
        if _p.parent == ratchet_io.RATCHET:
            ng.append(f"出力先が ratchet 直下のまま: {_kind} → {_p}")
    if "ratchet_io.RATCHET /" in inspect.getsource(_out_path):
        ng.append("_out_path が ratchet 直下を直に指している（OBSERVE_DIR を使っていない）")

    # ── 検査11（V9 の本数との突き合わせ）が生きているか（2026-08-11・段6 の 6-8）──
    #   ①いまの設定では ❌ が出ないこと ②わざと「設定に無い本数」を1件 入れると ❌ が出ること
    import contextlib as _cl11
    import io as _io11
    _v9rows = _v9_periods()
    if not _v9rows:
        ng.append("検査11: V9 の本数を実物から1件も拾えない（拾い方が実物とずれている）")
    with _cl11.redirect_stdout(_io11.StringIO()):
        _now_ng = _insp_v9_periods(cfg)
        _fake_ng = _insp_v9_periods(cfg, rows=[dict(指標="RCI", キー="rci_periods", 本数=9999,
                                                    出どころ="番人（偽）", 逐語="番人が入れた偽の本数",
                                                    説明="この検査が生きていることの確認")])
    if _now_ng:
        ng.append(f"検査11: いまの設定で V9 の本数が足りない（{_now_ng[0]}）")
    if not _fake_ng:
        ng.append("検査11: 設定に無い本数を入れても ❌ が出ない（この検査が死んでいる）")

    # ── 検査14（V9 の実物の列 ↔ うちの列 の対応を実測で決める）が生きているか（2026-08-11 新設）──
    #   ★既知答え4件。①〜③は「対応表に書いた3件が、実測でもそう出るか」＝表と実物のずれを毎回 検出する。
    #     ④は「無関係な列を混ぜたら『対応なし』と出るか」＝この検査が何でも『同じ』と言わないことの確認。
    #   わざと作ったデータ（乱数の値動き）で回すので、実データのCSVが無くても回る。
    import contextlib as _cl14
    import io as _io14
    _n14 = 1500
    _rng14 = np.random.default_rng(7)
    _px14 = 30000.0 * np.exp(np.cumsum(_rng14.normal(0, 0.0008, _n14)))
    _idx14 = pd.date_range(SEARCH_START, periods=_n14, freq="5min")     # 値決め窓の中に置く
    _bars14 = pd.DataFrame({"open": _px14, "high": _px14 * 1.0006, "low": _px14 * 0.9994,
                            "close": _px14, "volume": 1.0 + np.abs(_rng14.normal(0, 1, _n14))},
                           index=_idx14)
    _bars14.index.name = "timestamp"
    _want14 = {"rsi_short": "RSI21", "location_prev": "fib位置20", "entry_risk_score": "BB幅(20,2.0)"}
    _cat14 = [c for c in cat if c[0] in set(_want14.values())]
    if len(_cat14) != len(_want14):
        ng.append(f"検査14: 既知答えに使う列がカタログに無い（在るのは {[c[0] for c in _cat14]}）")
    else:
        def _fake14(win14):
            return {"番人_無関係": pd.Series(_rng14.normal(0, 1, len(win14)), index=win14.index)}
        with _cl14.redirect_stdout(_io14.StringIO()):
            _r14 = _v9_col_matches(_bars14, cfg, catalog=_cat14, calc_rows=_n14, rows=800, fake=_fake14)
        _got14 = {m["v9"]: m for m in _r14["matches"]}
        for _c14, _exp14 in _want14.items():
            _m14 = _got14.get(_c14)
            if _m14 is None:
                ng.append(f"検査14: V9 の {_c14} を測れていない（既知答えが回らない）")
            elif _m14["top"][0]["name"] != _exp14 or _m14["判定"] == "対応なし":
                ng.append(f"検査14: V9 の {_c14} の相手が {_m14['top'][0]['name']}"
                          f"（判定 {_m14['判定']}）＝対応表の {_exp14} と食い違う")
        if _c14 := _got14.get("番人_無関係"):
            if _c14["判定"] != "対応なし":
                ng.append(f"検査14: 無関係な列を『{_c14['判定']}』と言う（何でも同じだと言う＝検査が死んでいる）")
        else:
            ng.append("検査14: 番人が混ぜた列が測られていない")

        # ── C-4 の番人4件（部品を当てる処理・2026-08-11）─────────────────────────
        #   ①穴から外れる ②偽の列は穴のまま ③処理を壊すと穴に戻る ④数字を差し替えると穴に戻る。
        #   既知答え＝V9 の rsi_slope_short は「RSI21 の3本差分」（cat_v9_decider.py:96・
        #   本数は同 :93-94 と config/cat_params_v9.json:41-42 の SHORT_RSI_PERIOD=21／SHORT_RSI_SLOPE_N=3）。
        _p14 = (_got14.get("rsi_slope_short") or {}).get("部品")
        if "rsi_slope_short" not in _got14:
            ng.append("検査14 C-4: V9 の rsi_slope_short を測れていない（既知答えが回らない）")
        elif _got14["rsi_slope_short"]["判定"] != "対応なし":
            ng.append("検査14 C-4: rsi_slope_short が『対応なし』でない＝部品を当てる処理が回らない"
                      f"（判定 {_got14['rsi_slope_short']['判定']}）")
        elif _p14 is None:
            ng.append("検査14 C-4: rsi_slope_short に部品の欄が付いていない（処理が呼ばれていない）")
        elif not _p14["作れる"]:
            ng.append(f"検査14 C-4 番人1: rsi_slope_short が部品でも作れない扱いのまま"
                      f"（一番 近いのが {_p14['name']} の {_p14['label']}・相関 {_p14['score']:.7f}）")
        elif _p14["name"] != "RSI21" or _p14["kind"] != "n本前との差" or "3本前" not in _p14["label"]:
            ng.append(f"検査14 C-4 番人1: rsi_slope_short を作った部品が実物と違う"
                      f"（出たのは {_p14['name']} の {_p14['label']}／実物は RSI21 の 3本前との差）")
        _f14 = (_got14.get("番人_無関係") or {}).get("部品")
        if _f14 is None:
            ng.append("検査14 C-4 番人2: 番人が混ぜた列に部品の欄が付いていない")
        elif _f14["作れる"]:
            ng.append(f"検査14 C-4 番人2: 無関係な列を『部品で作れる』と言う"
                      f"（{_f14['name']} の {_f14['label']}・相関 {_f14['score']:.7f}）＝穴を見逃す")
        with _cl14.redirect_stdout(_io14.StringIO()):               # 番人3＝処理を止めたら穴に戻る
            _off14 = _v9_col_matches(_bars14, cfg, catalog=_cat14, calc_rows=_n14, rows=800,
                                     fake=_fake14, parts=False)
            # 番人4＝n の数字を差し替える（3 を外す）と、同じ列が作れなくなる
            _bad14 = _v9_col_matches(_bars14, cfg, catalog=_cat14, calc_rows=_n14, rows=800,
                                     fake=_fake14, part_grid=[6, 12, 24])
        if any(m["v9"] == "rsi_slope_short" and "部品" in m for m in _off14["matches"]):
            ng.append("検査14 C-4 番人3: 部品を当てる処理を止めても部品の欄が付く（止まっていない）")
        _b14 = next((m.get("部品") for m in _bad14["matches"] if m["v9"] == "rsi_slope_short"), None)
        if _b14 is not None and _b14["作れる"]:
            ng.append(f"検査14 C-4 番人4: n の数字から 3 を外しても rsi_slope_short を作れると言う"
                      f"（{_b14['name']} の {_b14['label']}）＝数字を実物から引いていない")

    # ── RCI の速い実装が、元の実装と1つも違わないか（2026-08-11・段6 の 6-8 で速くした）──
    #   同じ値段があるとき（平均順位）と、欠けがあるときの2つを、わざと作ったデータで確かめる。
    _rng = np.random.default_rng(0)
    _cc = pd.Series(np.round(np.cumsum(_rng.normal(0, 1.0, 3000)) + 100.0, 1))   # 丸めて同値を作る
    _cn = _cc.copy()
    _cn.iloc[500:505] = np.nan
    for _w in (7, 9, 26, 52):
        for _lbl, _s in (("同じ値段あり", _cc), ("欠けあり", _cn)):
            _a, _b = _rci_slow(_s, _w), _rci(_s, _w)
            if not (_a.isna() == _b.isna()).all():
                ng.append(f"RCI{_w}（{_lbl}）: 速い実装と元の実装で欠けの位置が違う")
            _d = float((_a - _b).abs().max())
            if not (_d == 0.0 or np.isnan(_d)):
                ng.append(f"RCI{_w}（{_lbl}）: 速い実装と元の実装の最大差 {_d:.3g}（0 でない）")

    # ── 場面を分ける材料の順位（M2-3-3・2026-08-22 新設）＝わざと壊して止まるか試す ──
    #   ★4件。どれも「止まるはずのものが止まるか」「見ないはずの所を見ていないか」を実測する。
    _t0 = pd.Timestamp(SEARCH_START) + pd.Timedelta("1D")
    _idx_ok = pd.date_range(_t0, periods=100, freq="5min")
    try:                                                        # 番人1: 値決め窓の中だけなら通る
        _assert_search_window_only(_idx_ok, "自己検査")
    except SystemExit as e:                                     # noqa: BLE001
        ng.append(f"順位づけ 番人1: 値決め窓の中なのに止まった（{e}）")
    _idx_ng = _idx_ok.append(pd.DatetimeIndex([pd.Timestamp(SCORE_START)]))
    try:                                                        # 番人2: 採点窓を1本 混ぜたら止まる
        _assert_search_window_only(_idx_ng, "自己検査")
        ng.append("順位づけ 番人2: 採点窓のバーを1本 混ぜても止まらない（C10 の④が効いていない）")
    except SystemExit:
        pass
    try:                                                        # 番人3: 値決め窓より前でも止まる
        _assert_search_window_only(pd.DatetimeIndex([pd.Timestamp(SEARCH_START) - pd.Timedelta("5min")]),
                                   "自己検査")
        ng.append("順位づけ 番人3: 値決め窓より前のバーでも止まらない")
    except SystemExit:
        pass
    #   番人4: ラベルは先 n本を見る＝末尾 n本は「使えない」になる（窓の外へはみ出さない）
    _n4 = 5
    _w4 = pd.DataFrame({"close": np.arange(50, dtype=float) + 100.0},
                       index=pd.date_range(_t0, periods=50, freq="5min"))
    _lab4 = _regime_labels(_w4, _n4)
    for _nm4, (_m4, _ok4) in _lab4.items():
        if bool(_ok4.iloc[-_n4:].any()):
            ng.append(f"順位づけ 番人4: ラベル「{_nm4}」の末尾 {_n4} 本が使える扱いになっている"
                      "（先が足りないのに使っている＝窓の外を見る芽）")
    #   番人5: 先を見る本数を、コードに写さず実物から読んでいるか（教訓 L-519）
    try:
        _h5 = _regime_horizons()
        if len(_h5) != 2 or _h5[0] >= _h5[1]:
            ng.append(f"順位づけ 番人5: 先を見る本数の範囲がおかしい（{_h5}）")
    except Exception as e:                                      # noqa: BLE001
        ng.append(f"順位づけ 番人5: 先を見る本数を実物から読めない（{e}）")

    #   番人6・7＝場面の観察の分離力を、独立な標本だけで測っているか（2026-08-22・まこさん指示で直した所）
    _ts6 = pd.date_range(_t0, periods=288 * 40, freq="5min")          # 40日ぶんの5分足
    _df6 = pd.DataFrame({"X__5m": np.arange(len(_ts6), dtype=float),
                         "X__1d": pd.Series(_ts6).dt.floor("1D").astype("int64").to_numpy() * 1.0})
    _m6 = pd.Series((np.arange(len(_ts6)) // 288) % 2 == 0)           # 1日ごとに真と偽が入れ替わる
    _r6 = rank_separation_independent(_df6, _m6, ["X__5m", "X__1d"], _ts6)
    if len(_r6) != 2:
        ng.append(f"場面の分離力 番人6: 2列 出るはずが {len(_r6)} 列")
    else:
        _n6 = {row["特徴"]: int(row["標本数"]) for _i, row in _r6.iterrows()}
        if _n6.get("X__1d") != 40:
            ng.append(f"場面の分離力 番人6: 日足の標本数が {_n6.get('X__1d')} 個"
                      f"（40日ぶんなので 40個 のはず＝重複して数えている）")
        if _n6.get("X__5m") != len(_ts6):
            ng.append(f"場面の分離力 番人6: 5分足の標本数が {_n6.get('X__5m')} 個"
                      f"（{len(_ts6)}個 のはず＝間引きすぎている）")
    try:                                                              # 番人7: 行数と時刻の本数が違えば止まる
        rank_separation_independent(_df6, _m6, ["X__5m"], _ts6[:-1])
        ng.append("場面の分離力 番人7: 行数と時刻の本数が合わないのに止まらない")
    except SystemExit:
        pass

    # ★M2-3-4 の番人（2026-08-22 まこさん承認）＝測れなかった列が「省いた列」に理由つきで載る。
    #   全部 NaN の列は分離力の辞書（measured）に入らない＝この経路がそのまま「測れなかった」になる。
    #   本物の4本（close vs T3%200__1d ほか）が載ることは、成績表の作り直し（--rank-regime 本走）で確かめる。
    _d0 = {"既存__5m": "重複で省いた（既存の理由）"}
    _out0 = _rank_record_unmeasured({"A__5m", "B__5m", "既存__5m"}, {"A__5m"}, dict(_d0))
    if "B__5m" not in _out0 or "測れなかった" not in _out0.get("B__5m", ""):
        ng.append("M2-3-4 番人: 測れなかった列が「省いた列」に載らない（黙って消える穴が開いたまま）")
    if _out0.get("既存__5m") != _d0["既存__5m"]:
        ng.append("M2-3-4 番人: 既に理由の付いた列を上書きしている")
    if "A__5m" in _out0:
        ng.append("M2-3-4 番人: 測れた列まで「省いた列」に載せている")
    if "_rank_record_unmeasured(expected_cols" not in inspect.getsource(rank_materials_for_regime):
        ng.append("M2-3-4 番人: 記録の穴ふさぎが順位づけの本体に配線されていない")

    # ★2026-08-29（M2-A-2・まこさん承認 9449761de0135c8f）＝検査15（片道の度合い）の番人 T1〜T6。
    _ix15 = pd.date_range("2024-06-01", periods=40, freq="5min")   # 値決め窓の中の作り物
    _n15 = 4

    def _mk15(cl):
        return pd.DataFrame({"close": cl, "high": cl, "low": cl}, index=_ix15)

    # T1 一直線に上がるだけ＝片道＝比は 1.0
    _r1 = _oneway_ratio(_mk15([100.0 + i for i in range(40)]), _n15).dropna()
    if len(_r1) == 0 or abs(float(_r1.iloc[0]) - 1.0) > 0.01:
        ng.append("検査15 T1: 一直線の区間で比が 1.0 にならない"
                  f"（{'なし' if len(_r1) == 0 else round(float(_r1.iloc[0]), 3)}）")
    # T2 同じ幅を行き来して元に戻る＝比は 0.0
    _r2 = _oneway_ratio(_mk15([100.0 + (2.0 if i % 2 else 0.0) for i in range(40)]), _n15).dropna()
    if len(_r2) == 0 or float(_r2.iloc[0]) > 0.01:
        ng.append("検査15 T2: 行って戻る区間で比が 0 にならない"
                  f"（{'なし' if len(_r2) == 0 else round(float(_r2.iloc[0]), 3)}）")
    # T3 全部 同じ値＝値幅 0＝数から外す（0 で割らない）
    if int(_oneway_ratio(_mk15([100.0] * 40), _n15).notna().sum()) != 0:
        ng.append("検査15 T3: 値幅 0 の区間を数から外していない（0 で割っている）")
    # T4 欠損を含む区間は外れる
    _na15 = _mk15([100.0 + i for i in range(40)])
    _na15.loc[_na15.index[5], "high"] = float("nan")
    if bool(_oneway_ratio(_na15, _n15).notna().iloc[2]):
        ng.append("検査15 T4: 欠損を含む区間を数から外していない")
    # T5 採点窓のバーを混ぜたら止まる
    try:
        _assert_search_window_only(pd.DatetimeIndex([SCORE_START]), "検査15 番人")
        ng.append("検査15 T5: 採点窓のバーを混ぜても止まらない")
    except SystemExit:
        pass
    # T6 重なりを避ける間隔が、先の本数ぶん空く
    if _independent_step("5m", 288) != 288:
        ng.append("検査15 T6: 重なりを避ける間隔が先の本数と合っていない")

    # ★2026-08-29（M2-A-4・まこさん承認 21dcfabff3d44a64）＝答えが分かっているニセのデータで、
    #   正解データを作るプログラム（_regime_labels）が壊れていないかを確かめる（N1〜N4）。
    #   ★これが無いと、計算式を1文字 間違えても、出る数字が変わるだけで誰も気づかない。
    _sdf, _str15 = _synth_regime_bars()
    _sn = 24
    _slab = _regime_labels(_sdf, _sn)
    # 先 _sn本 が同じ区間に収まる行だけを見る（区間の境目をまたぐ行は、答えが決まらないので外す）
    _fwd_tr = _str15.shift(-_sn)   # H2OK: ニセのデータの中だけで完結する検査＝実データを1バイトも読まない。本番の判断にも入らない
    _nx_tr = _str15.shift(-1)      # H2OK: 同上（ニセのデータの区間の境目を外すためだけに使う）
    _same15 = ((_fwd_tr == _str15) & (_nx_tr == _str15)).fillna(False)
    for _nm15, _tag15 in (("強さ", "N1"), ("向き", "N2"), ("大きさ", "N3")):
        _mk15, _us15 = _slab[_nm15]
        _use15 = _us15 & _same15
        if int(_use15.sum()) < 10:
            ng.append(f"検査15 {_tag15}: ニセのデータで使える行が {int(_use15.sum())} 行しか無い")
            continue
        _hit15 = float((_mk15[_use15] == _str15[_use15]).mean())
        if _hit15 < 1.0:
            ng.append(f"検査15 {_tag15}: 「{_nm15}」の札が、作った答えと一致しない"
                      f"（一致率 {_hit15:.3f}／使えた行 {int(_use15.sum())}）")
    # N4 わざと壊した版（まっすぐ進んだ距離と歩いた距離を入れ替えた）では一致率が落ちる＝この検査が効く証拠
    _c4 = _sdf["close"].astype(float)
    _fwd4 = (_c4.shift(-_sn) - _c4).abs()   # H2OK: ニセのデータの中だけで完結する検査（実データを1バイトも読まない）
    _walk4 = _c4.diff().abs().rolling(_sn).sum().shift(-_sn)  # H2OK: 同上
    _er4 = (_walk4 / _fwd4).where(_fwd4 > 0)          # ★わざと分子と分母を入れ替えた
    _m4 = _er4 >= _er4.median()
    _u4 = _er4.notna() & _same15
    if int(_u4.sum()) >= 10 and float((_m4[_u4] == _str15[_u4]).mean()) >= 1.0:
        ng.append("検査15 N4: わざと壊した版でも一致率が 100% のまま＝この検査は何も捕まえていない")

    print("=" * 80)
    print("observe_diag 自己検査")
    print("=" * 80)
    print(f"  指標カタログ {len(cat)} 種 × 足 {cfg['timeframes']} = {len(cat)*len(cfg['timeframes'])} 列")
    p0, p1 = _resolve_period(cfg)
    print(f"  期間 {p0.date()} 〜 {p1.date()}（採点窓 {SCORE_START.date()}〜{SCORE_END.date()} の範囲内のみ・periods.py）")
    print(f"  節 {len(SECTIONS)} / 分位 {cfg['quantiles']} / SL候補 {cfg['sl_grid']}（エントリー価格からの%）")
    print(f"  探索 {cfg.get('search_modes')} × side×型の分岐 / 切る探索＝逆行側プールのみ / 建値%TP探索なし")
    print(f"  設定ファイル {cfg['_source']}")
    print(f"  結果の保存先 {OBSERVE_DIR}（本走のみ・既存は observe/archive へ退避＝上書きしない）")
    ng += selftest_rank_demand(exit_=False)          # T-f（需給を成績表に足す差分の口・設計書 demand-in-ranking-20260907）
    ng += selftest_rank_resume(exit_=False)          # T-r（途中で落ちても続きから計算する・工事 E）
    ng += selftest_atr1h(exit_=False)                # T-A1〜T-A5（S-Rタッチ1時間ATR・設計書 m2e-bundle2-20260926）
    ng += selftest_band(exit_=False)                 # T-B1〜T-B4（帯の部品・S1 の部品・帯の1時間足の区切り・工事 m2c15-band-s1-20261020）
    ng += selftest_insp5(exit_=False)                # T-g・T-h・T-i・T-j（検査5 の枠と使い回しの鍵・設計書 insp5-frame-and-table-tidy-20260908）
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        raise SystemExit(1)
    print("  ✅ 全部 pass")


def build_parser():
    """引数の定義（取扱説明書の機械生成が読むので関数に括り出す・挙動は不変・2026-07-26）。"""
    import argparse
    ap = argparse.ArgumentParser(description="建玉の観察と探索（read-only 診断・売買記録CSVを書かない）")
    ap.add_argument("trades_csv", nargs="?", default=None,
                    help="実エンジンが出した売買記録CSV（--scene の時は不要）")
    ap.add_argument("bars_csv", nargs="?", default=None,
                    help="5分足CSV（Binance Spot 正本・--scene の時は不要＝e37 の計器で読む）")
    ap.add_argument("--scene", default=None,
                    help="Entry 候補観察＝場面ID（observe_config.json の scenes・例 S2＝まだ玉のない新候補の層1）")
    ap.add_argument("--inspect", action="store_true",
                    help="データと指標の検査（歩0・5段・read-only）＝5分足CSVのパスを1つ渡す（売買記録は使わない）")
    ap.add_argument("--cols", default=None,
                    help="--inspect と一緒に使う＝測る材料の列を名前で絞る（正規表現・例 'RSI.*傾き'）。"
                         "材料を足した時に、足した列だけを確かめるため。絞ったことは出力の冒頭に印字する")
    ap.add_argument("--only", default=None,
                    help="--inspect と一緒に使う＝走らせる検査の番号（例 14 や 11,14）。"
                         "指定した検査だけを走らせる（全部だと2時間10分かかる・一部だけ走らせたことは出力に印字する）")
    ap.add_argument("--rank-regime", action="store_true",
                    help="場面を分ける材料の順位を出す（M2-3-3・read-only）＝5分足CSVのパスを1つ渡す。"
                         "値決め窓だけで測る（採点窓が1本でも混ざれば止まる）。売買記録は使わない")
    ap.add_argument("--rank-tf", default=None,
                    help="--rank-regime と一緒に使う＝測る時間足を絞る（例 5m や 5m,1h）。"
                         "絞ったことは出力の冒頭に印字する")
    ap.add_argument("--add-demand", action="store_true",
                    help="--rank-regime と一緒に使う＝需給3列（taker_ls・L-S比・CVD）だけを指標と同じ物差しで採点し、"
                         "いまの成績表に足す（差分の口・全走はしない・指標の列は触らない・設計書 demand-in-ranking-20260907）。"
                         "--cols・--rank-tf とは同時に使えない")
    ap.add_argument("--plan", action="store_true",
                    help="検証計画だけを自動生成して印字（本走しない・まこさんへ提出する1枚）")
    ap.add_argument("--config", default=None, help="observe_config.json のパス（既定は同ディレクトリ）")
    ap.add_argument("--title", default="", help="出力の見出しに付ける題名")
    ap.add_argument("--selftest", action="store_true", help="自己検査だけ走らせる（この道具が守ると言っていることを機械で確認）")
    ap.add_argument("--check-materials", action="store_true",
                    help="材料検査（CP4 ②・read-only）＝方向の欄・系統分類・v9_logic.md の鮮度を機械検査＝5分足CSVのパスを1つ渡す")
    ap.add_argument("--check-materials-meta", action="store_true",
                    help="材料検査のメタ確認＝わざと偽の欄・偽の分類・偽の指紋を注入し、検査が実際に ❌ を出すことを確かめる")
    return ap


if __name__ == "__main__":
    if "--selftest-rank-demand" in sys.argv:          # T-f だけを数秒で（設計書 demand-in-ranking-20260907・壊すプログラム b39・b40 が使う）
        selftest_rank_demand()                        # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）
    if "--selftest-rank-resume" in sys.argv:          # T-r だけを数秒で（工事 E・壊すプログラム b126 が使う）
        selftest_rank_resume()                        # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）
    if "--selftest-insp5" in sys.argv:                # ★T-g・T-h・T-i・T-j だけを短い切れ端で
        # ★2026-09-08（監査 cp30 の Critical 1）＝すぐ後ろに5分足のパスを書けるようにした。
        #   渡すと T-i が「その5分足の最後のバーまで1分足が覆っているか」を見る
        #   ＝番人と検査5 が同じファイルを見る（定数と実物のずれを塞ぐ）。
        _i5 = sys.argv.index("--selftest-insp5")
        _bc5 = (sys.argv[_i5 + 1] if len(sys.argv) > _i5 + 1
                and not sys.argv[_i5 + 1].startswith("-") else None)
        selftest_insp5(bars_csv=_bc5)                 # （承認の打ち切り 120秒 に収めるための軽い口）
    if "--selftest-catalog" in sys.argv:              # ★K-1・K-8・G-2 の番人だけを（工事 m2c15-indicator-six-items-20261004・壊すプログラム b128・b129・b131 が使う）
        selftest_catalog()                            # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）
    if "--selftest-match" in sys.argv:                # ★検査3 と写しの印の番人だけを（工事 k4-reference-known-20261011・壊すプログラム b172〜b183 が使う）
        selftest_match()                              # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）
    if "--selftest-atr1h" in sys.argv:                # ★T-A1〜T-A5 だけを（設計書 m2e-bundle2-20260926・壊すプログラム b104〜b107 が使う）
        selftest_atr1h()                              # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）
    if "--selftest-band" in sys.argv:                 # ★T-B1〜T-B4 だけを（工事 m2c15-band-s1-20261020・壊すプログラム b189〜b196 が使う）
        selftest_band()                               # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）
    if "--selftest-lineage" in sys.argv:              # ★T-L1・T-L2 だけを（工事 m2c15-roles-r1-20261021・壊すプログラムが使う）
        selftest_lineage()                            # 中で終了コードを返す（0＝全部 通る／1＝❌ あり）
    if "--selftest" in sys.argv:
        selftest()
    else:
        ap = build_parser()
        a = ap.parse_args()
        # 本走の結果は results ラチェット直下へ保存する（--plan は提出用の計画＝画面のみ・2026-07-26）
        if a.check_materials or a.check_materials_meta:
            path = a.trades_csv or a.bars_csv          # 位置引数の1つ目に5分足CSVを渡してよい
            if not path:
                ap.error("--check-materials には 5分足CSV のパスが必要（売買記録は使わない）")
            if a.check_materials_meta:
                check_materials_meta(path, a.config)
            else:
                with _Tee(_out_path("materials", pathlib.Path(path).stem)):
                    check_materials(path, a.config)
        elif a.rank_regime and a.add_demand:           # ★差分の口（設計書 demand-in-ranking-20260907）＝既存の分岐の手前に置く
            path = a.trades_csv or a.bars_csv
            if not path:
                ap.error("--rank-regime --add-demand には 5分足CSV のパスが必要（売買記録は使わない）")
            if a.cols or a.rank_tf:
                ap.error("--add-demand は --cols・--rank-tf と同時に使えない（需給は5分足1本・絞りの対象ではない）")
            with _Tee(_out_path("rank_regime_add_demand", pathlib.Path(path).stem)):
                add_demand_to_ranking(path, a.config)
        elif a.rank_regime:
            path = a.trades_csv or a.bars_csv          # 位置引数の1つ目に5分足CSVを渡してよい
            if not path:
                ap.error("--rank-regime には 5分足CSV のパスが必要（売買記録は使わない）")
            with _Tee(_out_path("rank_regime", pathlib.Path(path).stem)):
                rank_regime(path, a.config, a.rank_tf, a.cols)
        elif a.inspect:
            path = a.trades_csv or a.bars_csv          # 位置引数の1つ目に5分足CSVを渡してよい
            if not path:
                ap.error("--inspect には 5分足CSV のパスが必要（売買記録は使わない）")
            with _Tee(_out_path("inspect", pathlib.Path(path).stem)):
                inspect_data(path, a.config, a.only, a.cols)
        elif a.scene:
            if a.plan:
                plan_scene(a.scene, a.config)
            else:
                with _Tee(_out_path("scene", a.scene)):
                    observe_scene(a.scene, a.config)
        else:
            if not (a.trades_csv and a.bars_csv):
                ap.error("trades_csv と bars_csv が必要（--scene の時だけ省略可）")
            if a.plan:
                plan(a.trades_csv, a.bars_csv, a.title, a.config)
            else:
                with _Tee(_out_path("trades", pathlib.Path(a.trades_csv).stem)):
                    observe(a.trades_csv, a.bars_csv, a.title, a.config)

#!/usr/bin/env python3
"""engine_tuner.py — 実エンジン × 審判で Entry/Exit の値を調整しきる道具（旧 engine_search_e38.py・改名 2026-07-27 まこさん確定）

⚠️ 戦略に依る部分は tuner_adapters/ の接続ファイルに閉じ込めてある（要件 R4・まこさん承認 2026-07-27）。
   本ファイルは戦略の中身を知らない＝戦略を1つ足すときは接続ファイルを1枚足すだけで、ここは書き換えない。

この道具の目的（まこさん確定 2026-07-27・逐語・説明書へ機械で流す）
--------------------------------------------------------------------------
・新規で Entry/Exit ロジックを構築する際に、設定した戦略や条件に沿った、指標、閾値、時間足、
  パラメータの組み合わせロジックを見つけ、利益最大化、損失最小化するまで調整する
・既存 Entry/Exit に対しては、目標達成するために改善すべき点を見つけ、利益最大化、損失最小化するまで調整する
※ 調整しきるの主語は【ロジック1本】。目標額（月 net $1,900）は【全戦略の合算】にかかるもので、
  ロジック1本にはかからない。全ロジックと E36 と E38 は同じ 0.12 BTC を取り合うので、単独 net の
  足し上げは合算にならない（実測＝P21 月$401.51 ＋ P23 月$241.72 を一緒に回した E32b は月$616.55）。
  だからこの道具が出せるのは「このロジックはこれ以上出ない」まで。目標に届いたかは統合の段で
  合算して判定する（正本＝pdca_flow §6.1・まだ一度も行っていない）。まこさん確認 2026-07-27。

使う順番（まこさん確定 2026-07-27）
--------------------------------------------------------------------------
▼既存のロジックを直すとき
  実装 → テスト結果が出る → observe_diag で診断 → 改善点を見出す → その改善案に基づき engine_tuner で
  最適化すべき部分をチューニング【Entry/Exit セット → Entry 調整＝Exit を固定して入口を磨く →
  Exit 調整＝Entry を固定して出口を磨く → 全体詳細調整＝セット微調整と優先度・サイズ・add・最終採否】
  → 実装
▼新しいロジックを作るとき
  型を選ぶ（人・entry_exit_matrix のカタログ）→ 機会の在庫を数える（observe_diag・1日に何回来るか）
  → 指標と閾値と時間足を探して調整しきる（engine_tuner）→ 実装 → テスト → observe_diag で診断
※ observe_diag は「数える」と「診断する」の2つだけを担当する。順位づけと候補選びはしない
  （疑似シミュの順位は実走で入れ替わる＝当てにならない順位で絞ると本当は稼げる候補を捨てる・L-330）。

1試行の中身
--------------------------------------------------------------------------
  ① 値を1組えらぶ（Optuna）
  ② 接続ファイルの run() で売買エンジンを最初から回す（値決め窓の全期間）
  ③ 出てきた売買記録を score.py にかけて純益を出す（審判＝import のみ・無変更 H13）
  ④ 件数の下限を下回っていたら その試行を捨てる
  ⑤ 純益が一番大きい組を覚えておく

窓構成（まこさん決定 2026-07-24・正本 window_similarity_ranking.md・e38_requirements.json decisions）:
  値決め＝探索窓 SEARCH_*（2024-04〜07・構造類似2位・距離1.78）だけを目的関数にする。
  確認＝CONFIRM_*（2025-12〜2026-02・8位相当・距離2.26・採点窓直前3ヶ月）を best 1点のみ1回走らせ表示のみ
  ＝確認窓の成績で選び直さない（選び直すと確認の意味が消える）。
  採点窓（periods）は不使用＝統合最終形1つだけ（覗き見ゼロ・L-267）。
探索範囲＝接続ファイルの space() の宣言（float=幾何 a-priori の広め固定幅／quantile=値決め窓の分布分位から
  実行時に上下限を決める＝CC の手打ち値なし・kijun26 前例）。

実行: python3 scripts/priority_rebuild/engine_tuner.py --strategy e38 --logic S2 --trials 150
  （旧名 engine_search_e38.py は require_tag hook の e3N 正規表現に名前が引っかかるため TAGLESS_OK=1 が要ったが、
   改名で不要になった。本装置は選定装置＝売買記録 CSV を出さない＝実験でない・pdca_flow §5）
"""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import inspect
import io
import json
import pathlib
import time

import pandas as pd

import periods                      # 採点窓の正本（重複 assert 用・数値は書かない）
import score as judge               # 審判＝import のみ・無変更（H13）
import tuner_stats                  # 「その数字が本物か」＝DSR と PBO（要件 R7 の B5・B6）
from tuner_adapters import available, load_adapter   # 戦略ごとの接続ファイル（要件 R4）

HERE = pathlib.Path(__file__).resolve()

# ★計測の記録（2026-07-27 まこさん OK・監査 2026-07-27 提案1）＝1試行の所要を走らせるたびに実測して残す。
#   説明書 gen_engine_tuner_manual.py はこのファイルから読む＝文書に秒数を手で書かない。
#   背景＝説明書に「実測でおよそ7秒」と手で焼いてあったが、それは別の道具 engine_search_e37.py の値だった
#   （lessons_active L-29 が出どころ・監査で発覚）。手書きの数値は必ず腐るので、実測を機械で残す形にする。
TIMING = HERE.parents[2] / ".claude" / "ratchet" / "engine_tuner_timing.json"

# ★指標つきデータの使い回し（2026-07-27 まこさん OK）＝実測で読み込みに毎回およそ100秒かかっていた。
#   試行の回数によらない固定費で、30分の枠のうち6%がここで消える。作った結果を保存して次回は読むだけにする。
#   ⚠️ 古い結果を使うと数字が狂う。だから指紋（下記の材料）が1つでも変わったら作り直す。--no-cache で無効化。
CACHE_DIR = HERE.parents[2] / "results" / "priority_rebuild" / "tuner_cache"
#   指紋の材料＝データの作り方に関わる実体のファイル。ここが変われば作り直す。
FINGERPRINT_FILES = ("e37_scalp.py", "e38_logic_parts.py", "build_regime_gate_rg.py",
                     "strat_base.py", "periods.py", "e34_range_zscore_taker.py")

# ★期間の数値は periods.py だけが持つ（H8・手打ち禁止・2026-07-27 集約＝値は移設前と同一で挙動不変）。
#   窓の意味・選び方・経緯の読み物＝.claude/ratchet/windows.md（gen_windows.py が機械生成）。
SEARCH_START = periods.SEARCH_START          # 値決め窓（まこさん決定 2026-07-24・構造類似2位）
SEARCH_END = periods.SEARCH_END              # 排他（2024-07-31 まで）
CONFIRM_START = periods.CONFIRM_START        # 確認窓（表示のみ・選び直し禁止）
CONFIRM_END = periods.CONFIRM_END            # 排他（採点窓 SCORE_START と接し重ならない）
WARM = pd.Timedelta(days=60)                 # 助走（RG 168h＋rolling を満たす a-priori）

assert SEARCH_END <= periods.SCORE_START and CONFIRM_END <= periods.SCORE_START, \
    "探索/確認窓が採点窓（periods 正本）と重複＝采否の窓の汚染"


def data_fingerprint(ad, windows, warm) -> str:
    """指標つきデータの指紋。1つでも変われば別物として作り直す（古い結果で数字を狂わせないため）。

    材料＝接続ファイルと、データの作り方に関わる実体のファイルと、設定ファイルと、5分足CSVと、窓と助走。
    """
    h = hashlib.sha256()
    files = [pathlib.Path(inspect.getfile(ad))]
    files += [HERE.parent / n for n in FINGERPRINT_FILES]
    cfg = getattr(ad, "CONFIG", None)
    if cfg is not None:
        files.append(pathlib.Path(cfg))
    for f in sorted(set(files), key=str):
        h.update(f.name.encode())
        if f.exists():
            h.update(f.read_bytes())
    try:                                    # 5分足CSVは巨大なので中身でなく大きさと更新時刻で見る
        import e34_range_zscore_taker as e34
        csv = pathlib.Path(e34.CSV)
        st = csv.stat()
        h.update(f"{csv.name}|{st.st_size}|{int(st.st_mtime)}".encode())
    except Exception:                       # noqa: BLE001  取れないときは毎回作り直す側に倒す
        h.update(str(time.time()).encode())
    h.update(str([(str(s), str(e)) for s, e in windows]).encode())
    h.update(str(warm).encode())
    return h.hexdigest()[:16]


def load_windows_cached(ad, windows, warm, use_cache: bool = True) -> list[pd.DataFrame]:
    """指標つきデータを作る。同じ指紋の結果が残っていれば、作らずにそれを読む。"""
    if not use_cache:
        print("[キャッシュ] 使わない（--no-cache）＝毎回作り直す")
        return ad.load_windows(windows, warm)
    fp = data_fingerprint(ad, windows, warm)
    paths = [CACHE_DIR / f"{ad.NAME}_{fp}_{i}.parquet" for i in range(len(windows))]
    if all(p.exists() for p in paths):
        try:
            out = [pd.read_parquet(p) for p in paths]
            print(f"[キャッシュ] 前に作ったものを再利用した（指紋 {fp}）＝作り直しを飛ばした")
            return out
        except Exception as e:              # noqa: BLE001  読めなければ作り直す（黙って古い物を使わない）
            print(f"[キャッシュ] 読めなかったので作り直す: {e}")
    out = ad.load_windows(windows, warm)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        for df, p in zip(out, paths):
            df.to_parquet(p, index=False)
        print(f"[キャッシュ] 次回のために保存した（指紋 {fp}・{CACHE_DIR.name}）")
    except Exception as e:                  # noqa: BLE001  保存に失敗しても結果は変わらない
        print(f"[キャッシュ] 保存に失敗した（結果には影響しない）: {e}")
    return out


def catalog_size() -> tuple[int, int] | None:
    """指標カタログの大きさを observe_diag（指標の作り方の正本）から取る。取れなければ None。

    ここで数えるのは「この道具が試せる範囲の分母」。分子＝接続ファイルの coverage()。
    ＝どれだけ試していないかを機械で出すため（監査 2026-07-27 提案1・まこさん OK）。
    """
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            import observe_diag as od
            cfg = od.load_config()
            n_ind, n_tf = len(od.build_catalog(cfg)), len(cfg["timeframes"])
        return n_ind, n_tf
    except Exception as e:                                   # noqa: BLE001  読めなくても探索は続ける
        print(f"[網羅度] 指標カタログを読めなかった＝分母を出せない: {e}")
        return None


def _print_coverage(ad, logic_id: str) -> None:
    """いま触れている列と、カタログ全体との比を出す（黙って落としているのでなく、そもそも候補に無い）。"""
    cov = getattr(ad, "coverage", None)
    if cov is None:
        print("[網羅度] この接続ファイルは触れる列の一覧を返さない＝分子を出せない")
        return
    touched = list(cov(logic_id))
    size = catalog_size()
    if size is None:
        print(f"[網羅度] この探索が触れる列 {len(touched)}本: {', '.join(touched)}")
        return
    n_ind, n_tf = size
    total = n_ind * n_tf
    print(f"[網羅度] 指標カタログ {n_ind}種 × 足 {n_tf}種 = {total}列 ／ "
          f"この探索が触れる列 {len(touched)}本 = {len(touched) / total * 100:.2f}%")
    print(f"         触れる列: {', '.join(touched)}")
    print("         ＝残りは試していない。落としたのでなく、候補にそもそも入っていない（要件 R3 が未着手）。")


def _record_timing(strategy: str, logic: str, load_sec: float, trials: int,
                   opt_sec: float, bars: int) -> None:
    """1試行の所要を実測して残す（説明書はここから読む＝文書に秒数を手で書かない）。"""
    key = f"{strategy}/{logic}"
    rec = {"load_sec": round(load_sec, 1), "trials": trials,
           "opt_sec": round(opt_sec, 1), "per_trial_sec": round(opt_sec / max(trials, 1), 2),
           "search_bars": int(bars), "measured_at": time.strftime("%Y-%m-%d")}
    try:
        cur = json.loads(TIMING.read_text(encoding="utf-8")) if TIMING.exists() else {}
        cur[key] = rec
        TIMING.parent.mkdir(parents=True, exist_ok=True)
        TIMING.write_text(json.dumps(cur, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")
        print(f"[計測] 読み込み {rec['load_sec']}秒 ／ 1試行 {rec['per_trial_sec']}秒"
              f"（{trials}試行で {rec['opt_sec']}秒）→ {TIMING.name} に記録した")
    except Exception as e:                                   # noqa: BLE001  記録に失敗しても探索の結果は出す
        print(f"[計測] 記録に失敗した（結果には影響しない）: {e}")


ADOPTED = HERE.parents[2] / ".claude" / "ratchet" / "adopted_strategies.md"


def role_floor(strategy: str) -> tuple[str | None, float | None]:
    """役割と、役割から来る件数/日 の絶対下限を採用台帳のマーカーから引く。

    ★ここを下回るのは「調整」でなく「役割を変える決定」（cat_requirements §8.6）。
      道具に戦略名や数字を焼かない＝台帳の1行を直せば追従する（他の hook と同じ方式）。
    """
    try:
        txt = ADOPTED.read_text(encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        return None, None
    role = None
    for ln in txt.splitlines():
        if "ROLE_CHECK:" in ln:
            for kv in ln.split("ROLE_CHECK:")[1].split("-->")[0].split(";"):
                if "=" in kv and kv.split("=")[0].strip() == strategy:
                    role = kv.split("=")[1].strip()
        if "ROLE_FLOOR:" in ln and role:
            for kv in ln.split("ROLE_FLOOR:")[1].split("-->")[0].split(";"):
                if "=" in kv and kv.split("=")[0].strip() == role:
                    try:
                        return role, float(kv.split("=")[1].strip())
                    except ValueError:
                        return role, None
    return role, None


def _atr_bands(base_t: pd.DataFrame, cand_t: pd.DataFrame, edges) -> list[tuple[str, float, float, bool]]:
    """ATR% の帯ごとに、土台と候補の net を審判で出して比べる（B4）。

    帯に分ける理由＝静かな相場だけで稼ぎ荒い相場で損を出す形でも、合計では改善に見えるため
    （E37 v16 の学習窓プラスが帯の補填による見かけだった実証・ARC31／ARC32）。
    ATR% は売買記録の atr_14 と entry_price から出す＝net の計算には触れない（H13）。
    """
    def band_of(t: pd.DataFrame) -> pd.Series:
        return (t["atr_14"].astype(float) / t["entry_price"].astype(float) * 100.0)

    lo = [-float("inf")] + list(edges)
    hi = list(edges) + [float("inf")]
    out = []
    for a, b in zip(lo, hi):
        lab = (f"〜{b:g}" if a == -float("inf") else (f"{a:g}〜" if b == float("inf") else f"{a:g}〜{b:g}"))
        vals = []
        for t in (base_t, cand_t):
            if t is None or not len(t):
                vals.append(0.0)
                continue
            m = (band_of(t) >= a) & (band_of(t) < b)
            sub = t[m].reset_index(drop=True)
            vals.append(float(judge.score(sub)["total"]) if len(sub) else 0.0)
        out.append((lab, vals[0], vals[1], vals[1] >= vals[0]))
    return out


def _run_baseline(ad, df_s, df_c, logic: str, exit_keys: set, minimize: str | None):
    """土台＝いまの採用値で1回だけ走らせる（B1・B2 の比較相手・2026-07-27 まこさん OK）。

    E38 は設定ファイルの現行値、E37 は採用土台 v59d_164 の定数そのまま。数字は接続ファイルが持つ。
    """
    fn = getattr(ad, "baseline", None)
    if fn is None:
        return None
    bp = fn(logic)
    if bp is None:
        return None
    ep = {k: v for k, v in bp.items() if k not in exit_keys}
    xp = {k: v for k, v in bp.items() if k in exit_keys}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rs = _run_window(ad, df_s, logic, ep, xp, SEARCH_START, SEARCH_END, minimize)
        rc = _run_window(ad, df_c, logic, ep, xp, CONFIRM_START, CONFIRM_END, minimize)
    return {"search": rs, "confirm": rc}


def _print_judgement(base, rs, rc, min_per_day, stats: dict | None, n_kept: int,
                     rules: dict | None = None, rfloor: float | None = None,
                     trials: int = 0, gain: float | None = None,
                     bands: list | None = None) -> None:
    """判定の1枚表（A＝出し切ったか／B＝本物か／C＝目標に届いたか）。

    ★ML の知識がなくても読めるように、印は ✅ と ❌ と「値がまこさん待ち」の3つだけにする。
      値を CC が決めない項目は、勝手に埋めずに「まこさん待ち」と出す（監査 2026-07-27 Q8）。
    """
    WAIT = "— 値がまこさん待ち"
    sr = rules or {}
    rows = []
    delta = sr.get("delta_net")
    if delta is None or gain is None:
        rows.append(("A1", "改善が δ 未満（出し切ったか）", WAIT))
    else:
        rows.append(("A1", "改善が δ 未満（出し切ったか）",
                     f"δ ${delta:,.0f} → 後半の伸び ${gain:+,.0f}"
                     + ("  ✅" if gain < delta else "  ❌ まだ伸びている")))
    nmax = sr.get("n_max")
    if nmax is None:
        rows.append(("A2", "試行の上限 N_max に到達（着手前に宣言）", WAIT))
    else:
        rows.append(("A2", "試行の上限 N_max に到達（着手前に宣言）",
                     f"N_max {nmax:,} → 今回 {trials:,}"
                     + ("  ✅" if trials >= nmax else "  ❌ まだ上限に達していない")))
    if base is None:
        rows.append(("B1", "値決め窓で土台より改善しているか", "— このロジックはまだ採用値を持たない"))
        rows.append(("B2", "確認窓で土台より悪化していないか", "— 同上"))
    else:
        bs, bc = base["search"]["total"], base["confirm"]["total"]
        rows.append(("B1", "値決め窓で土台より改善しているか",
                     f"土台 ${bs:+,.0f} → 候補 ${rs['total']:+,.0f}"
                     + ("  ✅" if rs["total"] > bs else "  ❌")))
        rows.append(("B2", "確認窓で土台より悪化していないか",
                     f"土台 ${bc:+,.0f} → 候補 ${rc['total']:+,.0f}"
                     + ("  ✅" if rc["total"] >= bc else "  ❌")))
    # B3＝役割の下限（台帳・下回るのは役割を変える決定）と、運用の下限（PDCA で見直してよい）の2段
    ops = sr.get("ops_min_per_day")
    floor = ops if ops is not None else (min_per_day if min_per_day is not None else rfloor)
    if floor is None:
        rows.append(("B3", "件数/日 が下限以上", WAIT))
    else:
        src = "運用の下限" if ops is not None else ("探索のゲート" if min_per_day is not None else "役割の下限")
        note = ""
        if rfloor is not None and floor < rfloor:
            note = f"  ⚠️ 役割の下限 {rfloor:g} を下回る線を使っている＝役割を変える決定に当たる"
        rows.append(("B3", f"件数/日 が下限以上（{src}）",
                     f"下限 {floor:g} → 候補 {rs['per_day']:.2f}"
                     + ("  ✅" if rs["per_day"] >= floor else "  ❌") + note))
    if bands is None:
        rows.append(("B4", "ATR% の全帯で土台を悪化させない",
                     WAIT if not sr.get("atr_band_edges") else "— 土台が無いので比べられない"))
    else:
        ng_b = [b[0] for b in bands if not b[3]]
        rows.append(("B4", "ATR% の全帯で土台を悪化させない",
                     f"{len(bands)}帯" + ("  ✅ 全帯で非悪化" if not ng_b
                                          else f"  ❌ 悪化した帯 {', '.join(ng_b)}")))
    if stats is None:
        rows.append(("B5", "DSR > 0.95（試した回数で割り引いた成績）", f"— 判定できない（通った試行 {n_kept} 本）"))
        rows.append(("B6", "PBO < 0.5（過剰なあてはめの確率）", "— 同上"))
    else:
        d, p = stats["dsr"], stats["pbo"]
        rows.append(("B5", "DSR > 0.95（試した回数で割り引いた成績）",
                     f"{d['dsr']:.3f}" + ("  ✅" if d["dsr"] > tuner_stats.DSR_PASS else "  ❌")))
        rows.append(("B6", "PBO < 0.5（過剰なあてはめの確率）",
                     (f"{p['pbo']:.3f}" + ("  ✅" if p["pbo"] < tuner_stats.PBO_PASS else "  ❌"))
                     if p else "— 測れない  ❌"))
    rows.append(("C", "目標額（月 net $1,900）に届いたか", "— この道具では判定しない（統合の段で合算）"))

    print("\n[判定の1枚表（A＝そのロジックで出し切ったか／B＝その数字が本物か／C＝目標に届いたか）]")
    print("| # | 見るもの | 結果 |")
    print("|---|---|---|")
    for a, b, c in rows:
        print(f"| {a} | {b} | {c} |")
    ng = [a for a, _b, c in rows if "❌" in c]
    wait = [a for a, _b, c in rows if "まこさん待ち" in c]
    if ng:
        print(f"→ **調整しきれていない**（{', '.join(ng)} が不合格）")
    elif wait:
        print(f"→ 判定できない（{', '.join(wait)} の値が決まっていない）")
    else:
        print("→ このロジックはこれ以上出ない（★目標額に届いたかは別＝統合の段で合算して判定する）")


def _print_stats(strategy: str, logic: str, kept: list, best_num: int) -> None:
    """B5・B6＝その数字が本物か（DSR と PBO）。合格ラインは H11 が正本（まこさんが決める値ではない）。

    ★日ごとの net は審判 score.py を日ごとに呼んで得る＝CC は net を計算しない（H13）。
      足し合わせが全期間と一致することを毎回確かめる（一致しなければ止まる）。
    """
    print("\n[B5・B6 その数字が本物か（試した回数で割り引いた成績 DSR ／ 過剰なあてはめの確率 PBO）]")
    if len(kept) < 2:
        print(f"  ゲートを通った試行が {len(kept)} 本＝統計で判定できない（2本以上要る）")
        return None
    t0 = time.time()
    daily = {}
    for num, _params, res, _ok, _why in kept:
        s = tuner_stats.daily_net(res["t"], judge, SEARCH_START, SEARCH_END)
        tuner_stats.check_daily_sum(s, res["total"])          # 分け方が壊れていないことの確認
        daily[num] = s
    if best_num not in daily:                                  # best がゲートで落ちている時は通った中の最良
        best_num = max(daily, key=lambda k: float(daily[k].sum()))
        print(f"  ※ best はゲートを通っていないので、通った中で最良の #{best_num} で判定する")

    key = f"{strategy}/{logic}@{SEARCH_START.date()}_{SEARCH_END.date()}"
    past = tuner_stats.load_cumulative(key)
    r = tuner_stats.evaluate(daily, best_num, past)
    d, p = r["dsr"], r["pbo"]
    ok_d = d["dsr"] > tuner_stats.DSR_PASS
    ok_p = (p is not None) and (p["pbo"] < tuner_stats.PBO_PASS)

    print(f"  期間 T = {r['T']} 日（月ごとに集計すると 4 にしかならず統計にならないので日ごとにしている）")
    print(f"  試行 = 生 {r['n_raw']} 本 → 似た動きをまとめて {r['n_eff']} 本"
          f" ＋ この窓での過去の累積 {r['past_trials']} 本 = DSR に渡した N {r['n_for_dsr']}")
    print(f"  DSR = {d['dsr']:.3f}（合格 > {tuner_stats.DSR_PASS}）"
          f"{'  ✅' if ok_d else '  ❌'}   成績 {d['sr']:.4f} ／ 運だけで出る水準 {d['sr0']:.4f}")
    if p is None:
        print("  PBO = 測れない（候補が足りない、または期間が短い）  ❌")
    else:
        print(f"  PBO = {p['pbo']:.3f}（合格 < {tuner_stats.PBO_PASS}）{'  ✅' if ok_p else '  ❌'}"
              f"   候補 {r['n_pbo_cols']} 本・組み合わせ {p['n_combos']} 通り")
    print(f"  判定: B5 と B6 は {'両方とも合格' if (ok_d and ok_p) else '合格していない'}"
          f"（{time.time() - t0:.0f}秒で計算）")
    print("  ⚠️ 分散は探索が集めた試行から推定している＝良い所に試行が集まるほど分散が縮み、"
          "DSR は甘い側に出る。独立に撒く段（ランダムサーチ）は未実装。")
    tot = tuner_stats.add_cumulative(key, r["n_raw"], time.strftime("%Y-%m-%d"))
    print(f"  この窓での累積の試行数を {tot} 本に更新した（次回の DSR はこの数を罰に使う）")
    return r


def _resolve_space(space_decl: dict, bank: dict) -> dict:
    """探索範囲の宣言 → Optuna 用の実レンジ（quantile は実行時実値・印字して透明化）。"""
    out = {}
    for name, d in space_decl.items():
        if d["type"] == "float":
            out[name] = ("float", float(d["lo"]), float(d["hi"]))
        elif d["type"] == "cat":
            out[name] = ("cat", list(d["choices"]))
        elif d["type"] == "quantile":
            s = bank[d["series"]]
            out[name] = ("float", float(s.quantile(d["q_lo"])), float(s.quantile(d["q_hi"])))
        else:
            raise SystemExit(f"[探索範囲エラー] 未知の type: {d}（正本＝接続ファイルの space）")
    return out


def _suggest(trial, space: dict) -> dict:
    return {n: (trial.suggest_float(n, r[1], r[2]) if r[0] == "float" else trial.suggest_categorical(n, r[1]))
            for n, r in space.items()}


def _run_window(ad, dfp: pd.DataFrame, logic_id: str, ep: dict, xp: dict,
                start: pd.Timestamp, end: pd.Timestamp, minimize: str | None = None) -> dict:
    """1走＝接続ファイルに走らせて窓内を審判式で評価（CSV を書かない）。

    minimize＝減らしたい損失の出口理由（例 TIME_EXIT）。指定すると、その出口理由の玉だけを
    審判に通した net 合計を "focus" として返す（マイナスなら損失・大きくするほど損失が減る）。
    """
    t = ad.run(dfp, logic_id, ep, xp)
    if len(t):
        et = pd.to_datetime(t["entry_time"])
        t = t[(et >= start) & (et < end)].reset_index(drop=True)
    if not len(t):
        return {"total": 0.0, "n": 0, "per_day": 0.0, "hold_med": float("nan"),
                "focus": 0.0, "focus_n": 0, "t": t}
    res = judge.score(t)
    days = max((end - start).days, 1)
    focus, focus_n = 0.0, 0
    if minimize:
        sub = t[t["exit_reason"] == minimize].reset_index(drop=True)
        focus_n = len(sub)
        focus = float(judge.score(sub)["total"]) if focus_n else 0.0
    return {"total": float(res["total"]), "n": len(t), "per_day": len(t) / days,
            "hold_med": float(t["hold_min"].median()),
            "focus": focus, "focus_n": focus_n, "t": t}


def _exit_reasons(t: pd.DataFrame) -> list[str]:
    """売買記録に出てくる出口理由（--minimize の指定が実在するかの確認に使う）。"""
    return sorted(t["exit_reason"].dropna().unique().tolist()) if len(t) else []


def _type_split(ad, t: pd.DataFrame) -> str:
    """型別の審判値の内訳（接続ファイルが型の列を持つときだけ・持たない戦略は「—」）。"""
    col = getattr(ad, "TYPE_COL", None)
    if not col or not len(t) or col not in t.columns:
        return "—"
    outs = []
    for ct in getattr(ad, "TYPE_VALUES", ()):
        sub = t[t[col] == ct].reset_index(drop=True)
        outs.append(f"{ct} {len(sub)}玉 ${judge.score(sub)['total']:+,.0f}" if len(sub) else f"{ct} 0玉 $0")
    return " / ".join(outs)


def build_parser() -> argparse.ArgumentParser:
    """引数の定義（説明書の自動生成が実体から読む口＝observe_diag.build_parser と同型・2026-07-27）。"""
    ap = argparse.ArgumentParser(description=f"Entry/Exit の値を実エンジン×審判で調整する（値決め={SEARCH_START.date()}〜{SEARCH_END.date()} 排他／確認={CONFIRM_START.date()}〜{CONFIRM_END.date()} 排他=表示のみ・まこさん決定 2026-07-24）")
    ap.add_argument("--strategy", default="e38",
                    help=f"どの戦略を調整するか（tuner_adapters の接続ファイル名・在るのは {', '.join(available())}）")
    ap.add_argument("--logic", required=True, help="調整するロジック id（例 S2・接続ファイルの logics() が一覧）")
    ap.add_argument("--trials", type=int, default=150,
                    help="試す組み合わせの数（1試行につき売買エンジンを最初から1回まるごと回す）")
    ap.add_argument("--seed", type=int, default=42,
                    help="探索の乱数の種（同じ種なら同じ順で試す＝結果を再現できる）")
    ap.add_argument("--log", default=None,
                    help="試行ログの出力先（既定は engine_tuner_<戦略>_<ロジックid>.log）")
    # ★損失最小化（まこさん確定 2026-07-27・要件 R8）＝診断で見つけた出血源を値の調整で減らす。
    #   何を減らすかは診断の結果で毎回変わるので、コードに焼かず実行時に渡す。
    ap.add_argument("--minimize", default=None,
                    help="減らしたい損失の出口理由（例 TIME_EXIT）。指定するとその損失を最小化する。"
                         "省略すると合計 net を最大化する（従来どおり）")
    ap.add_argument("--no-cache", action="store_true",
                    help="指標つきデータの使い回しをやめて毎回作り直す。"
                         "数字が合わないときの切り分けに使う（作り方を変えたときは指紋が変わるので自動で作り直す）")
    ap.add_argument("--net-floor", type=float, default=None,
                    help="合計 net の下限。値決め窓の合計 net がこれを下回った試行は捨てる。"
                         "--minimize と併用する歯止め＝損失を減らすつもりで勝ち玉まで削る形を弾く。"
                         "値はまこさんが決める（省略＝歯止めなし）")
    return ap


def main() -> None:
    a = build_parser().parse_args()
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    ad = load_adapter(a.strategy)                      # ★戦略の中身を知るのは接続ファイルだけ（要件 R4）
    known = {z["id"]: z for z in ad.logics()}
    if a.logic not in known:
        raise SystemExit(f"[エラー] ロジック id が {ad.NAME} に無い: {a.logic}"
                         f"（在るのは {', '.join(known)}）")
    if not known[a.logic]["searchable"]:
        raise SystemExit(f"[エラー] {a.logic} はいま回せない: {known[a.logic]['why']}")

    print(f"[戦略] {ad.NAME}: {ad.LABEL} ／ ロジック {a.logic}: {known[a.logic]['label']}")
    print(f"[窓] 値決め {SEARCH_START.date()}〜{SEARCH_END.date()}（排他）／確認 {CONFIRM_START.date()}〜{CONFIRM_END.date()}（排他・表示のみ）＝まこさん決定 2026-07-24・採点窓不使用")
    t0 = time.time()
    df_s, df_c = load_windows_cached(
        ad, [(SEARCH_START, SEARCH_END), (CONFIRM_START, CONFIRM_END)], WARM, use_cache=not a.no_cache)
    t_load = time.time() - t0
    print(f"[共通部分] 探索スライス {len(df_s):,} バー／確認スライス {len(df_c):,} バー（{t_load:.0f}秒）")
    _print_coverage(ad, a.logic)

    bank = ad.series_bank(df_s[df_s["ts"] >= SEARCH_START])
    space = _resolve_space(ad.space(a.logic), bank)
    for n, r in space.items():
        print(f"[範囲] {n}: {r[0]} {r[1] if r[0]=='float' else r[1]}" + (f" 〜 {r[2]:.6g}" if r[0] == "float" else ""))

    exit_keys = ad.exit_keys()
    fixed_ep, fixed_xp = ad.fixed(a.logic, set(space))
    if fixed_ep or fixed_xp:
        print(f"[固定値（設定の確定値＝全試行に適用）] entry={fixed_ep} / exit={fixed_xp}")
    min_per_day = ad.min_per_day(a.logic)
    if min_per_day is not None:
        print(f"[件数ゲート] 値決め窓の件数/日 < {min_per_day} の試行は棄却（出典＝接続ファイルの min_per_day・値はまこさん確定）")
    else:
        print("[件数ゲート] なし（接続ファイルが下限を返さない＝値はまこさんが決める）")
    if a.minimize:
        print(f"[目的] {a.minimize} の損失を最小化する（審判に {a.minimize} の玉だけを通した net 合計を最大化）")
        print("       ＝診断で見つけた出血源を値の調整で減らす（まこさん確定 2026-07-27・要件 R8）")
    else:
        print("[目的] 合計 net を最大化する（--minimize を指定すると特定の出口理由の損失を減らす形になる）")
    if a.net_floor is not None:
        print(f"[net の歯止め] 値決め窓の合計 net < ${a.net_floor:,.0f} の試行は捨てる"
              "（損失を減らすつもりで勝ち玉まで削る形を弾く・値はまこさん確定）")
    elif a.minimize:
        print("[net の歯止め] なし（--net-floor 未指定）。⚠️ 損失だけを見ると建てない形が上位に来る")
    # ★終わりの条件の値＝戦略ごとの設定から引く（道具に数字を焼かない・2026-07-27 まこさん確定）
    rules = getattr(ad, "stop_rules", lambda _l: {})(a.logic)
    role, rfloor = role_floor(a.strategy)
    print(f"[終わりの条件の値] δ ${rules.get('delta_net')} ／ N_max {rules.get('n_max')} ／ "
          f"ATR%帯 {rules.get('atr_band_edges')} ／ 運用の下限 {rules.get('ops_min_per_day')}"
          f"（理由 {rules.get('ops_reason')}・{rules.get('ops_date')}）")
    print(f"[役割] {a.strategy} = {role} ／ 役割から来る件数/日 の絶対下限 {rfloor}"
          "（台帳のマーカーが正本・下回るのは調整でなく役割を変える決定）")
    if rules.get("n_max") and a.trials > rules["n_max"]:
        print(f"⚠️ 今回の試行 {a.trials:,} が宣言した上限 {rules['n_max']:,} を超えている"
              "＝多重検定の罰を後出しで薄める形。上限を変えるなら設定ファイルを直してから回すこと。")

    # ★土台＝いまの採用値を1回だけ走らせる（B1・B2 の比較相手・2026-07-27 まこさん OK）
    base = _run_baseline(ad, df_s, df_c, a.logic, exit_keys, a.minimize)
    if base is None:
        print("[土台] このロジックはまだ採用値を持たない＝比べる相手が無い（B1 と B2 は判定できない）。"
              "既定値を当てて土台のふりをしない＝偽の相手と比べると B1・B2 が意味を失うため。")
    else:
        print(f"[土台（いまの採用値）] 値決め窓 net ${base['search']['total']:+,.0f} / "
              f"{base['search']['n']}玉 / {base['search']['per_day']:.2f}件/日"
              f" ／ 確認窓 net ${base['confirm']['total']:+,.0f} / {base['confirm']['n']}玉")
        print("           ＝探索で選ぶ値は、これより良くなって初めて意味がある（B1・B2 の比較相手）")
    logf = open(a.log or f"engine_tuner_{a.strategy}_{a.logic}.log", "w", encoding="utf-8")
    results = []
    seen_reasons: set = set()

    def obj(trial):
        pr = _suggest(trial, space)
        ep = {**fixed_ep, **{k: v for k, v in pr.items() if k not in exit_keys}}
        xp = {**fixed_xp, **{k: v for k, v in pr.items() if k in exit_keys}}
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = _run_window(ad, df_s, a.logic, ep, xp, SEARCH_START, SEARCH_END, a.minimize)
        seen_reasons.update(_exit_reasons(res["t"]))
        # ★ゲートの判定を先に出して試行に貼る（2026-07-27 まこさん OK）。
        #   従来は棄却した試行も上位10に並んでいた＝ほとんど建てない形が1位に見え、§8.6 が禁じる
        #   尻すぼみを最良として見せる表示になっていた（2026-07-27 の実走で発見）。選定は従来どおり。
        ok, why = True, ""
        if min_per_day is not None and res["per_day"] < min_per_day:
            ok, why = False, f"件数の下限 {min_per_day} に対して {res['per_day']:.2f}件/日"
        elif a.net_floor is not None and res["total"] < a.net_floor:
            ok, why = False, f"net の下限 ${a.net_floor:,.0f} に対して ${res['total']:+,.0f}"
        results.append((trial.number, dict(trial.params), res, ok, why))
        logf.write(f"T{trial.number}\t{res['total']:+.1f}\t{res['n']}\t{res['per_day']:.2f}"
                   + (f"\t{a.minimize}={res['focus']:+.1f}({res['focus_n']}玉)" if a.minimize else "")
                   + ("" if ok else f"\t棄却={why}")
                   + f"\t{trial.params}\n")
        logf.flush()
        if trial.number % 20 == 0:
            extra = f" / {a.minimize} ${res['focus']:+,.0f}（{res['focus_n']}玉）" if a.minimize else ""
            print(f"  trial {trial.number}: net ${res['total']:+,.0f}{extra} / {res['n']}玉 / {res['per_day']:.2f}件/日 / 経過 {(time.time()-t0)/60:.1f}分", flush=True)
        if not ok:
            return -1e9                    # 件数下限ゲート／net の歯止め（値はまこさん確定）
        return res["focus"] if a.minimize else res["total"]

    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=a.seed))
    t_opt0 = time.time()
    st.optimize(obj, n_trials=a.trials, show_progress_bar=False)
    _record_timing(a.strategy, a.logic, t_load, a.trials, time.time() - t_opt0, len(df_s))

    if a.minimize and a.minimize not in seen_reasons:
        print(f"\n⚠️ [警告] 指定した出口理由 {a.minimize} は、どの試行の売買記録にも出ていない。"
              f"（出ているのは {', '.join(sorted(seen_reasons)) or 'なし'}）"
              "＝最小化する対象がゼロのまま探索した。指定が正しいか確かめること。")
    key = (lambda z: -z[2]["focus"]) if a.minimize else (lambda z: -z[2]["total"])
    head = f"{a.minimize} の損失が小さい順" if a.minimize else "合計 net が大きい順"
    kept = [z for z in results if z[3]]
    dropped = [z for z in results if not z[3]]
    print(f"\n[上位10（{a.logic}・値決め窓の審判値・{head}・★ゲートを通った試行だけ）]")
    if not kept:
        print(f"  ⚠️ ゲートを通った試行が {len(results)} 本中 0 本。下の best は選定の対象になっていない"
              "＝下限を満たす形が見つからなかったということ。下限か探索範囲を見直すこと。")
    for num, params, res, _ok, _why in sorted(kept, key=key)[:10]:
        extra = f" / {a.minimize} ${res['focus']:+,.0f}（{res['focus_n']}玉）" if a.minimize else ""
        print(f"  #{num}: net ${res['total']:+,.0f}{extra} / {res['n']}玉 / {res['per_day']:.2f}件/日\n      {params}")
    # ★捨てたものは黙って消さない（L-330／L-356）＝本数と理由と、捨てた中で net が良かった3本を出す。
    if dropped:
        n_cnt = sum(1 for z in dropped if z[4].startswith("件数"))
        print(f"\n[ゲートで捨てた試行] {len(dropped)}/{len(results)} 本"
              f"（件数の下限 {n_cnt} 本 ／ net の下限 {len(dropped) - n_cnt} 本）"
              "＝上の一覧には入れない。ほとんど建てない形が最良に見えるのを防ぐため（§8.6）。")
        for num, params, res, _ok, why in sorted(dropped, key=key)[:3]:
            print(f"  #{num}: net ${res['total']:+,.0f} / {res['n']}玉 / {res['per_day']:.2f}件/日 ← {why}")

    bp = dict(st.best_trial.params)
    ep = {**fixed_ep, **{k: v for k, v in bp.items() if k not in exit_keys}}
    xp = {**fixed_xp, **{k: v for k, v in bp.items() if k in exit_keys}}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rs = _run_window(ad, df_s, a.logic, ep, xp, SEARCH_START, SEARCH_END, a.minimize)
        rc = _run_window(ad, df_c, a.logic, ep, xp, CONFIRM_START, CONFIRM_END, a.minimize)
    print(f"\n[best #{st.best_trial.number}（値決め窓で選定・確認窓は表示のみ＝選び直し禁止）] {bp}")
    for nm, r in (("値決め窓", rs), ("確認窓  ", rc)):
        extra = f" / {a.minimize} ${r['focus']:+,.0f}（{r['focus_n']}玉）" if a.minimize else ""
        print(f"  {nm}: net ${r['total']:+,.0f}{extra} / {r['n']}玉 / {r['per_day']:.2f}件/日"
              f" / 保有中央 {r['hold_med']:.0f}分 / 型別 {_type_split(ad, r['t'])}")
    stats = _print_stats(a.strategy, a.logic, kept, st.best_trial.number)

    # A1 の代用＝試行の前半と後半で、目的関数の最良がどれだけ伸びたか（段がまだ無いため）
    gain = None
    if kept:
        val = (lambda z: z[2]["focus"]) if a.minimize else (lambda z: z[2]["total"])
        half = a.trials / 2.0
        first = [val(z) for z in kept if z[0] < half]
        gain = (max(val(z) for z in kept) - max(first)) if first else None
    bands = None
    if base is not None and rules.get("atr_band_edges"):
        bands = _atr_bands(base["search"]["t"], rs["t"], rules["atr_band_edges"])
        print("\n[B4 ATR% の帯ごとの比較（静かな相場だけで稼いで荒い相場で損を出す形を弾く）]")
        for lab, b, c, ok in bands:
            print(f"  ATR% {lab:>10} : 土台 ${b:+,.0f} → 候補 ${c:+,.0f}" + ("  ✅" if ok else "  ❌"))
    _print_judgement(base, rs, rc, min_per_day, stats, len(kept),
                     rules=rules, rfloor=rfloor, trials=a.trials, gain=gain, bands=bands)
    if gain is not None:
        print("  ※ A1 は段がまだ無いので、試行の前半と後半の伸びで代用している（段の構成は未実装）。")
    print("\n⚠️ ここは探索側の数字＝採否の数字ではない。統合最終形1つだけを採点窓 score.py にかけ、採否はまこさんが判断する。")
    print("⚠️ 目標額（月 net $1,900）に届いたかは、この道具では判定しない＝全戦略を同じ 0.12 BTC で"
          "一緒に回した合算でしか出ない（統合の段・pdca_flow §6.1）。")
    logf.close()


if __name__ == "__main__":
    main()

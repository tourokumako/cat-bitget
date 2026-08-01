#!/usr/bin/env python3
"""tuner_judgement.py — 判定の1枚表（A＝出し切ったか／B＝本物か／C＝目標に届いたか）を1箇所に集める

なぜ要るか（まこさん承認 2026-08-01・案B）
--------------------------------------------------------------------------
判定表は engine_tuner.py の中にしか無かった。作り直し中の新しい器（engine_tuner_gen.py）には
判定表が無い。このまま歩6 で S1/L1 を新しい器へ移すと、E37 の v59 は古い器で回り続けるので、
**同じ設定に別の合否が出る**状態になる。それが一番まずい。だから判定表を独立させて、
古い器と新しい器の両方がここを呼ぶ形にする。

この段（歩5 の1回目の第1段）でやること／やらないこと
--------------------------------------------------------------------------
やること＝engine_tuner.py の3部品を**逐語で**ここへ移すだけ（引っ越し）。
  role_floor        … 採用台帳のマーカーから 役割 と 件数/日 の絶対下限 を引く（B3 の出どころ）
  atr_bands         … ATR% の帯ごとに土台と候補を審判で比べる（B4 の計算）
  print_judgement   … 判定の1枚表そのもの（A1・A2・B1〜B6・C の9行）
やらないこと＝判定の意味を変えること。A1 の代用も、B3 の強制も、土台なしの合否も、
  この段では**1行も直さない**。直しと引っ越しを同時にやると、結果が変わったときに
  どちらが原因か分からなくなるため（H16＝1ターン1変更）。

守る制約
--------------------------------------------------------------------------
H8＝期間の数値は periods.py だけが持つ（ここに日付リテラルを書かない）。
H13＝net は審判 score.py だけが出す（ここでは score.score を呼ぶだけ・式に触れない）。
§8.6＝件数/日 の絶対下限は採用台帳の ROLE_FLOOR が正本（道具に数字を焼かない）。

恒等の確かめ方
--------------------------------------------------------------------------
  python3 scripts/priority_rebuild/tuner_judgement.py --identity
    引っ越し前＝engine_tuner.py に元の関数が残っている間は、同じ入力を両方へ与えて
    出力の md5 を突き合わせる。引っ越し後＝同じ関数を指しているので、記録した md5 と比べる。
  python3 scripts/priority_rebuild/tuner_judgement.py --selftest
    判定表の全分岐を印字して md5 を出す（合成の入力だけ・売買しない・採点しない）。
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import periods                      # 期間の正本（H8・ここに日付リテラルを書かない）
import score as judge               # 審判＝import のみ・無変更（H13）
import tuner_stats                  # 合格ライン DSR_PASS / PBO_PASS（H11 が正本）

HERE = pathlib.Path(__file__).resolve()
ADOPTED = HERE.parents[2] / ".claude" / "ratchet" / "adopted_strategies.md"

# 窓は periods.py から取る（engine_tuner.py と同じ値＝同じ分岐になる・H8）
SEARCH_START = periods.SEARCH_START
SEARCH_END = periods.SEARCH_END
CONFIRM_START = periods.CONFIRM_START
CONFIRM_END = periods.CONFIRM_END


# ══ B3 の出どころ＝採用台帳から役割と件数の下限を引く ═══════════════════════════════════
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


# ══ B4 の計算＝ATR% の帯ごとに土台と候補を比べる ═══════════════════════════════════════
def atr_bands(base_t: pd.DataFrame, cand_t: pd.DataFrame, edges) -> list[tuple[str, float, float, bool]]:
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


# ══ 判定の1枚表 ═══════════════════════════════════════════════════════════════════════
def print_judgement(base, rs, rc, min_per_day, stats: dict | None, n_kept: int,
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
        if SEARCH_START == CONFIRM_START and SEARCH_END == CONFIRM_END:
            # ★同一窓の間は B2 に合格の印を出さない（暫定窓＝まこさん確定 2026-07-30）。
            #   確認窓の役割は「値決め窓だけのまぐれ当たりを弾く」＝同じ窓では B1 と同じ数字を
            #   2回見るだけで、弾く力がゼロ。✅を出すと独立の確認に見えてしまう。
            rows.append(("B2", "確認窓で土台より悪化していないか",
                         "— 確認窓＝値決め窓のため判定不能（engine_tuner 完成までの暫定・窓の決め直しは歩5）"))
        else:
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


# ══ 恒等の検収に使う入力（合成・売買しない・採点しない）══════════════════════════════════
def _cases() -> list[tuple[str, dict]]:
    """判定表の分岐をひととおり踏む入力の組。引っ越しの前後で出力が変わらないことの材料。

    ★ケース4 は「土台なしのロジックに合格が出る」現状を可視化するためのもの（歩5 の第2段で直す対象）。
      いまは直さない＝この段は引っ越しだけ（H16）。
    """
    rs_a = {"total": 1234.5, "n": 800, "per_day": 8.42}
    rs_b = {"total": -321.0, "n": 120, "per_day": 1.93}
    rc_a = {"total": 987.6, "n": 700, "per_day": 7.11}
    base_a = {"search": {"total": 500.0}, "confirm": {"total": 400.0}}
    stats_ok = {"dsr": {"dsr": 0.987}, "pbo": {"pbo": 0.234}}
    stats_ng = {"dsr": {"dsr": 0.120}, "pbo": None}
    bands_ok = [("〜1", 10.0, 20.0, True), ("1〜2", 5.0, 7.0, True), ("2〜", -3.0, -1.0, True)]
    bands_ng = [("〜1", 10.0, 20.0, True), ("1〜2", 5.0, -7.0, False), ("2〜", -3.0, -9.0, False)]
    return [
        ("① 値が全部まこさん待ち・土台なし・統計なし",
         dict(base=None, rs=rs_a, rc=rc_a, min_per_day=None, stats=None, n_kept=0,
              rules={}, rfloor=None, trials=150, gain=None, bands=None)),
        ("② 土台あり・値そろい・全部合格側",
         dict(base=base_a, rs=rs_a, rc=rc_a, min_per_day=2.0, stats=stats_ok, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 100, "atr_band_edges": [1.0, 2.0]},
              rfloor=5.0, trials=150, gain=5.0, bands=bands_ok)),
        ("③ 土台あり・不合格側（伸びが残る・件数下限割れ・帯悪化・統計不合格）",
         dict(base=base_a, rs=rs_b, rc=rc_a, min_per_day=2.0, stats=stats_ng, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 3000, "atr_band_edges": [1.0, 2.0],
                     "ops_min_per_day": 2.0}, rfloor=5.0, trials=150, gain=99.0, bands=bands_ng)),
        ("④ 土台なし・そのほかは合格側＝★いまは『これ以上出ない』が出る（歩5 第2段で直す）",
         dict(base=None, rs=rs_a, rc=rc_a, min_per_day=2.0, stats=stats_ok, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 100, "atr_band_edges": [1.0, 2.0]},
              rfloor=2.0, trials=150, gain=5.0, bands=bands_ok)),
    ]


class _StubJudge:
    """atr_bands の恒等を確かめるための審判の代役。合計だけ返す＝score.py の式に触れない。"""

    @staticmethod
    def score(t):
        return {"total": float(t["fake_net"].sum())}


def _atr_case() -> tuple[pd.DataFrame, pd.DataFrame, list]:
    base_t = pd.DataFrame({"atr_14": [1.0, 1.0, 2.0, 2.0, 3.0, 3.0],
                           "entry_price": [100.0] * 6,
                           "fake_net": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0]})
    cand_t = base_t.copy()
    cand_t.loc[cand_t["atr_14"] == 2.0, "fake_net"] = -1.0
    return base_t, cand_t, [1.5, 2.5]


def _render(fn) -> str:
    """判定表の関数に全ケースを流して、印字を1本の文字列にまとめる。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        for label, kw in _cases():
            print(f"===== {label} =====")
            fn(**kw)
    return buf.getvalue()


def _render_bands(fn, judge_stub) -> str:
    base_t, cand_t, edges = _atr_case()
    mod = sys.modules[fn.__module__]
    saved = getattr(mod, "judge")
    try:
        mod.judge = judge_stub
        out = fn(base_t, cand_t, edges)
    finally:
        mod.judge = saved
    return "\n".join(f"{lab}|{a:.4f}|{b:.4f}|{ok}" for lab, a, b, ok in out)


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def run_identity() -> int:
    """引っ越しの恒等＝engine_tuner.py の元の関数と、ここへ移した関数の出力を突き合わせる。"""
    new_tbl = _render(print_judgement)
    new_bnd = _render_bands(atr_bands, _StubJudge)
    new_role = role_floor("e38")
    h_tbl, h_bnd = _md5(new_tbl), _md5(new_bnd)
    print("=" * 80)
    print("tuner_judgement 恒等検収（判定表の引っ越し・合成の入力のみ・売買なし・採点なし）")
    print("=" * 80)
    print(f"[窓] 値決め {SEARCH_START.date()}〜{SEARCH_END.date()} ／ 確認 {CONFIRM_START.date()}〜{CONFIRM_END.date()}"
          f"（periods.py が正本・同一窓なら B2 は判定不能表示）")
    print(f"[新] 判定表 md5 {h_tbl} ／ ATR%帯 md5 {h_bnd} ／ role_floor('e38') = {new_role}")

    try:
        import engine_tuner as old
    except Exception as e:                                   # noqa: BLE001
        print(f"❌ engine_tuner.py を読み込めない＝突き合わせができない: {e}")
        return 1

    old_tbl_fn = getattr(old, "_print_judgement", None)
    old_bnd_fn = getattr(old, "_atr_bands", None)
    old_role_fn = getattr(old, "role_floor", None)
    if old_tbl_fn is None or old_bnd_fn is None or old_role_fn is None:
        print("❌ engine_tuner.py に元の関数が無い（名前が変わった？）＝突き合わせができない")
        return 1

    # 引っ越し済みかは「その関数がどのファイルに書いてあるか」で見る。モジュール名では見ない
    # （このファイルを直接走らせると __name__ は __main__ になり、引っ越し済みでも「前」と誤表示するため）。
    import inspect
    try:
        moved = (pathlib.Path(inspect.getfile(old_tbl_fn)).name == pathlib.Path(__file__).name)
    except Exception:                                        # noqa: BLE001
        moved = False
    if moved:
        print("[状態] engine_tuner.py は既にこのファイルの判定表を呼んでいる（引っ越し済み）")
        print("       → 同じソースの2つの読み込みを走らせ、記録した md5 と一致することを確かめる")
    else:
        print("[状態] engine_tuner.py はまだ自前の判定表を持っている（引っ越し前）→ 両方を走らせて比べる")

    ng = 0
    old_tbl = _render(old_tbl_fn)
    old_bnd = _render_bands(old_bnd_fn, _StubJudge)
    old_role = old_role_fn("e38")
    print(f"[旧] 判定表 md5 {_md5(old_tbl)} ／ ATR%帯 md5 {_md5(old_bnd)} ／ role_floor('e38') = {old_role}")
    if _md5(old_tbl) != h_tbl:
        ng += 1
        print("❌ 判定表の出力が一致しない")
    if _md5(old_bnd) != h_bnd:
        ng += 1
        print("❌ ATR% 帯の出力が一致しない")
    if old_role != new_role:
        ng += 1
        print("❌ role_floor の戻りが一致しない")

    if BASELINE_TABLE_MD5 is None:
        print("\n⚠️ BASELINE_TABLE_MD5 が未記入。上の md5 をこのファイルへ書き込むこと"
              "（引っ越し後もこの値と一致することを、以後この検収で確かめる）。")
    else:
        if h_tbl != BASELINE_TABLE_MD5 or h_bnd != BASELINE_BANDS_MD5:
            ng += 1
            print(f"❌ 記録した md5 と違う（判定表 期待 {BASELINE_TABLE_MD5} ／ 帯 期待 {BASELINE_BANDS_MD5}）")
        else:
            print(f"[記録との突き合わせ] 判定表 {BASELINE_TABLE_MD5} ／ 帯 {BASELINE_BANDS_MD5} → 一致")

    print("\n" + ("✅ 完全一致（判定の意味は1文字も変えていない）" if ng == 0 else f"❌ 不一致 {ng} 件"))
    return ng


# ★引っ越しの基準となる md5（2026-08-01 の初回 --identity の実測＝engine_tuner.py の元の関数と完全一致した値）。
#   以後この値が動いたら「判定の意味が変わった」証拠になる。歩5 の第2段で A1・B3・土台なし合否を直すときは、
#   ここが動く＝それが狙った変更であることを、そのとき機械出力で示してから書き換える。
BASELINE_TABLE_MD5: str | None = "ccbfe65aedbdf639a120becaa45304a6"
BASELINE_BANDS_MD5: str | None = "ab1f16299bf309d0b580f7749df6cc84"


def selftest() -> int:
    """判定表の全分岐を印字する（読んで確かめる用・合成の入力のみ）。"""
    print("=" * 80)
    print("tuner_judgement 自己検査（判定表の全分岐・合成の入力のみ・売買なし・採点なし）")
    print("=" * 80)
    for label, kw in _cases():
        print(f"\n===== {label} =====")
        print_judgement(**kw)
    print(f"\n[md5] 判定表 {_md5(_render(print_judgement))}"
          f" ／ ATR%帯 {_md5(_render_bands(atr_bands, _StubJudge))}")
    role, floor = role_floor("e38")
    print(f"[台帳から引いた値] e38 の役割 {role} ／ 件数/日 の絶対下限 {floor}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="判定の1枚表（A/B/C）＝古い器と新しい器の共通の判定")
    ap.add_argument("--identity", action="store_true",
                    help="引っ越しの恒等＝engine_tuner.py の元の関数と出力を突き合わせる")
    ap.add_argument("--selftest", action="store_true", help="判定表の全分岐を印字する")
    a = ap.parse_args()
    if a.identity:
        return run_identity()
    if a.selftest:
        return selftest()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

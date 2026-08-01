#!/usr/bin/env python3
"""tuner_judgement.py — 判定の1枚表（A＝出し切ったか／B＝本物か／C＝目標に届いたか）を1箇所に集める

なぜ要るか（まこさん承認 2026-08-01・案B）
--------------------------------------------------------------------------
判定表は engine_tuner.py の中にしか無かった。作り直し中の新しい器（engine_tuner_gen.py）には
判定表が無い。このまま歩6 で S1/L1 を新しい器へ移すと、E37 の v59 は古い器で回り続けるので、
**同じ設定に別の合否が出る**状態になる。だから判定表を独立させて、両方がここを呼ぶ。

★この表の一番大事な決まり（歩5 の第2段・2026-08-01）
--------------------------------------------------------------------------
**印は5つある。合格 ✅ ／ 不合格 ❌ ／ 値がまこさん待ち ／ 判定不能 ／ 土台なしの合格。**
「判定不能」は**合格ではない**。1つでも残っていれば「これ以上出ない」とは言わない。

直す前は印が3つしか無く（✅・❌・まこさん待ち）、比べる相手が無い行は「—」とだけ出て
結論の集計から漏れていた。その結果、**土台を1本も持たないロジックに「これ以上出ない」が出た**
（監査 1-3・engine_tuner.py の旧 364行目）。E38 の S2〜S5・L2〜L5 は全部その状態にある。
「判定不能」を第3の状態として数えることで、A1 の代用の穴（監査 4-15）と同時に閉じる。

★「土台なしの合格」を第5の状態として足した（2026-08-01 の3回目・まこさん OK）
--------------------------------------------------------------------------
結論の「これ以上出ない」は、実は2つのことを一度に言っている。
  ① あと何回試しても、見つかる利益はもうほとんど増えない（A1・A2 が見る）
  ② その利益がまぐれではない（B1〜B6 が見る）
①は比べる相手が無くても判定できる。②は比べる相手が無いと判定しきれない。
土台の無いロジックでは B1・B2 が「前の版より良いか」を見られず「手数料を引いて儲かっているか」
しか見ていない＝②の確認が弱い。だから**土台なしで全部通っても「これ以上出ない」とは言わせない**。
代わりに「試しても利益が増えないところまでは来た。ただし前の版が無いので、この利益がまぐれか
どうかは確かめきれていない」と出す。合格線 $0 はそのまま残す（儲かっていない候補を落とすため）。
★この穴は 2026-08-01 に値決め窓と確認窓を分けた瞬間に表に出た。分ける前は B2 が必ず「判定不能」に
なるので結論が合格まで届かず、番人⑤（土台なしで合格を出さない）が偶然通っていただけだった。
＝番人が本当に守っていたのは窓の同一性であって、土台の有無ではなかった。

行ごとの中身
--------------------------------------------------------------------------
  A1 打ち止め      直近2段の改善が δ 未満か。段が3個そろわなければ判定不能（代用の合格を出さない）
  A2 試行の上限    事前に宣言した N_max に達したか
  B1 値決め窓      土台があれば「土台より改善したか」／土台が無ければ「net が下限以上か」
  B2 確認窓        土台があれば「土台より悪化していないか」／土台が無ければ「net が下限以上か」
                   値決め窓と確認窓が同一の間は判定不能（弾く力がゼロのため）
  B3 件数/日       役割の下限が既定。役割の下限より緩い線で回すには「役割を変える決定」の明示が要る
  B4 ATR% の帯     全帯で土台を悪化させないか。土台が無ければ判定不能
  B5 DSR           試した回数で割り引いた成績
  B6 PBO           過剰なあてはめの確率
  C  目標額        この道具では判定しない（統合の段で合算）

守る制約
--------------------------------------------------------------------------
H8＝期間の数値は periods.py だけが持つ（ここに日付リテラルを書かない）。
H13＝net は審判 score.py だけが出す（ここでは score.score を呼ぶだけ・式に触れない）。
H11＝DSR>0.95／PBO<0.5 は要件が正本（ここで決めない）。
§8.6＝件数/日 の絶対下限は採用台帳の ROLE_FLOOR が正本（道具に数字を焼かない）。
値（δ・土台なしの net の下限・N_max・帯の切り方）はすべてまこさんが決める＝CC は決めない。

確かめ方
--------------------------------------------------------------------------
  python3 scripts/priority_rebuild/tuner_judgement.py --identity
    いまの判定表の md5 を出し、記録した2つの基準と突き合わせる。
    引っ越し直後（判定の意味＝修正前）と、第2段の修正後の2つを別々に記録している。
  python3 scripts/priority_rebuild/tuner_judgement.py --selftest
    判定表の全分岐を印字し、番人（わざと壊した設定で止まること）を走らせる。
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

import eval_engine as ee            # 予算の上限 POSITION_CAP_BTC（数字を書き写さない・H1）
import periods                      # 期間の正本（H8・ここに日付リテラルを書かない）
import score as judge               # 審判＝import のみ・無変更（H13）
import tuner_stats                  # 合格ライン DSR_PASS / PBO_PASS（H11 が正本）

HERE = pathlib.Path(__file__).resolve()
ADOPTED = HERE.parents[2] / ".claude" / "ratchet" / "adopted_strategies.md"
# 判定表の保存先（まこさん指示 2026-08-01「results/priority_rebuild/ratchet/ 配下にフォルダ作成して出力」）。
# 画面だけだと走らせるたびに流れて消え、後から検収の証拠を見返せないため。
# results 配下は git の commit 対象外（CLAUDE.md）＝ここのファイルは commit しない。
JUDGE_DIR = HERE.parents[2] / "results" / "priority_rebuild" / "ratchet" / "judgement"

# 窓は periods.py から取る（engine_tuner.py と同じ値＝同じ分岐になる・H8）
SEARCH_START = periods.SEARCH_START
SEARCH_END = periods.SEARCH_END
CONFIRM_START = periods.CONFIRM_START
CONFIRM_END = periods.CONFIRM_END

# 行の状態。★UNKNOWN（判定不能）は合格ではない＝1つでも残れば結論を出さない
PASS, FAIL, WAIT, UNKNOWN, NA = "pass", "fail", "wait", "unknown", "na"
# ★PASS_NOBASE（土台なしの合格）＝線は越えたが、比べる相手が無いので「前の版より良い」は言えない。
#   不合格ではない。だが完全な合格でもない＝これが1つでも残れば「これ以上出ない」とは言わせない。
PASS_NOBASE = "pass_nobase"
WAIT_TXT = "— 値がまこさん待ち"

# ★土台をまだ持たないロジックの合格線（まこさん承認 2026-08-01・案1）。
#   意味＝手数料を全部引いてなお net が増えていること。減っているロジックを使う理由は無いので、
#   後から下げる性質の値ではない。ただし「これで十分」の線でもない＝ロジック1本が月いくら担うかは
#   統合の段で決まる（この道具では判定しない）。だから下の「参考」の行で、月いくら稼いでいるかと、
#   担う額に対していくら足りないかを必ず表示する（合否には使わない）。
#   戦略ごとにもっと厳しくしたいときは、その戦略の設定 stop_rules で上書きできる。
NOBASE_NET_FLOOR = 0.0


class RoleFloorError(SystemExit):
    """役割の下限より緩い線で回そうとした（明示の決定が無い）＝走らせない（fail-closed）。"""


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


def search_floor_line(min_per_day: float | None, rules: dict | None) -> tuple[float | None, str | None]:
    """その回の探索で実際に使っている件数/日 の線と、その出どころの名前を返す。"""
    sr = rules or {}
    ops = sr.get("ops_min_per_day")
    if ops is not None:
        return float(ops), "運用の下限"
    if min_per_day is not None:
        return float(min_per_day), "探索のゲート"
    return None, None


def assert_role_floor(strategy: str, min_per_day: float | None, rules: dict | None,
                      rfloor: float | None = None) -> None:
    """★fail-closed＝役割の下限より緩い線で回そうとしたら、明示の決定が無い限り走らせない。

    出典＝cat_requirements §8.6「件数/日 の絶対下限を割るのは、調整ではなく役割を変える決定」。
    監査 4-14 の対応＝下限は台帳の ROLE_FLOOR から機械で引き、下回る線は明示の指定を必須にする。
    明示の指定＝戦略の設定（接続ファイルの stop_rules）に role_change_decision を置く。
    中身は誰がいつ何のために決めたかが分かる文字列（CC は勝手に書かない）。
    """
    if rfloor is None:
        _role, rfloor = role_floor(strategy)
    line, src = search_floor_line(min_per_day, rules)
    if rfloor is None or line is None or line >= rfloor:
        return
    decision = (rules or {}).get("role_change_decision")
    if decision:
        return
    raise RoleFloorError(
        f"[役割の下限エラー] {strategy} の役割から来る件数/日 の絶対下限は {rfloor:g} です。"
        f"いま使おうとしている線は {line:g}（{src}）で、これを下回っています。\n"
        f"  下回る線で回すのは『調整』ではなく『役割を変える決定』です（cat_requirements §8.6）。\n"
        f"  回すなら、戦略の設定の stop_rules に role_change_decision を置いてください"
        f"（誰がいつ何のために決めたかを書く）。CC は勝手に書きません。")


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


# ══ 行を1つずつ作る ═══════════════════════════════════════════════════════════════════
def _row_a1(sr: dict, stage_bests) -> tuple[str, str, str]:
    """A1＝打ち止め。直近2段の改善がどちらも δ 未満なら合格。

    ★段が3個そろわないと「直近2段の改善」は測れない＝判定不能（合格の印を出さない）。
      直す前は「試行の前半と後半で最良がどれだけ伸びたか」で代用していて、1試行しか無くても
      合格が出た（監査 4-15・2026-07-30 の測定1 で再実証）。代用は廃止した。
    """
    delta = sr.get("delta_net")
    bests = [float(x) for x in (stage_bests or [])]
    if delta is None:
        return WAIT, "改善が δ 未満（打ち止めか）", WAIT_TXT
    if len(bests) < 3:
        return (UNKNOWN, "改善が δ 未満（打ち止めか）",
                f"— 判定不能（段が {len(bests)} 個。直近2段の改善を見るには段の最良が3個要る）")
    g_prev, g_last = bests[-2] - bests[-3], bests[-1] - bests[-2]
    ok = (g_last < delta) and (g_prev < delta)
    return ((PASS if ok else FAIL), "改善が δ 未満（打ち止めか）",
            f"δ ${delta:,.0f} → 直近2段の改善 ${g_prev:+,.0f} と ${g_last:+,.0f}"
            + ("  ✅" if ok else "  ❌ まだ伸びている"))


def _row_a2(sr: dict, trials: int) -> tuple[str, str, str]:
    nmax = sr.get("n_max")
    label = "試行の上限 N_max に到達（着手前に宣言）"
    if nmax is None:
        return WAIT, label, WAIT_TXT
    ok = trials >= nmax
    return ((PASS if ok else FAIL), label,
            f"N_max {nmax:,} → 今回 {trials:,}" + ("  ✅" if ok else "  ❌ まだ上限に達していない"))


def _rows_b1b2(base, rs, rc, sr: dict) -> list[tuple[str, str, str, str]]:
    """B1・B2＝土台があれば土台との比較。土台が無ければ土台なしの合否基準（監査 1-3）。"""
    same_window = (SEARCH_START == CONFIRM_START and SEARCH_END == CONFIRM_END)
    if base is not None:
        bs, bc = base["search"]["total"], base["confirm"]["total"]
        ok1 = rs["total"] > bs
        r1 = ("B1", "値決め窓で土台より改善しているか",
              f"土台 ${bs:+,.0f} → 候補 ${rs['total']:+,.0f}" + ("  ✅" if ok1 else "  ❌"),
              PASS if ok1 else FAIL)
        if same_window:
            # ★同一窓の間は B2 に合格の印を出さない（暫定窓＝まこさん確定 2026-07-30）。
            #   確認窓の役割は「値決め窓だけのまぐれ当たりを弾く」＝同じ窓では B1 と同じ数字を
            #   2回見るだけで、弾く力がゼロ。✅を出すと独立の確認に見えてしまう。
            r2 = ("B2", "確認窓で土台より悪化していないか",
                  "— 判定不能（確認窓＝値決め窓。弾く力がゼロ・窓の決め直しは歩5 の3回目）", UNKNOWN)
        else:
            ok2 = rc["total"] >= bc
            r2 = ("B2", "確認窓で土台より悪化していないか",
                  f"土台 ${bc:+,.0f} → 候補 ${rc['total']:+,.0f}" + ("  ✅" if ok2 else "  ❌"),
                  PASS if ok2 else FAIL)
        return [r1, r2]

    # ── 土台なし（そのロジックをまだ一度も採用していない）＝比べる相手が無い ──
    #    比較の代わりに、絶対の線（全コスト後の net の下限）で見る。値はまこさんが決める。
    nf_s = sr.get("nobase_net_floor", NOBASE_NET_FLOOR)
    nf_c = sr.get("nobase_confirm_floor", NOBASE_NET_FLOOR)
    if nf_s is None:
        r1 = ("B1", "値決め窓の net が下限以上か（土台なしの合否）",
              "— 値がまこさん待ち（土台なしの net の下限）", WAIT)
    else:
        ok1 = rs["total"] >= nf_s
        r1 = ("B1", "値決め窓の net が下限以上か（土台なしの合否）",
              f"土台なし＝下限 ${nf_s:+,.0f}（手数料を全部引いて増えていること） → "
              f"候補 ${rs['total']:+,.0f}"
              + ("  ✅ ただし前の版が無いので『前より良い』は言えない" if ok1 else "  ❌"),
              PASS_NOBASE if ok1 else FAIL)
    if same_window:
        r2 = ("B2", "確認窓の net が下限以上か（土台なしの合否）",
              "— 判定不能（確認窓＝値決め窓。弾く力がゼロ・窓の決め直しは歩5 の3回目）", UNKNOWN)
    elif nf_c is None:
        r2 = ("B2", "確認窓の net が下限以上か（土台なしの合否）",
              "— 値がまこさん待ち（土台なしの確認窓の下限）", WAIT)
    else:
        ok2 = rc["total"] >= nf_c
        r2 = ("B2", "確認窓の net が下限以上か（土台なしの合否）",
              f"土台なし＝下限 ${nf_c:+,.0f} → 候補 ${rc['total']:+,.0f}"
              + ("  ✅ ただし前の版が無いので『前より良い』は言えない" if ok2 else "  ❌"),
              PASS_NOBASE if ok2 else FAIL)
    return [r1, r2]


def _row_b3(rs, min_per_day, sr: dict, rfloor: float | None) -> tuple[str, str, str]:
    """B3＝件数/日。★役割の下限が既定。緩い線を使うには「役割を変える決定」の明示が要る（監査 4-14）。"""
    line, src = search_floor_line(min_per_day, sr)
    decision = sr.get("role_change_decision")
    if rfloor is None and line is None:
        return WAIT, "件数/日 が下限以上", WAIT_TXT
    if rfloor is not None and line is not None and line < rfloor and not decision:
        return (FAIL, "件数/日 が下限以上（役割の下限）",
                f"使っている線 {line:g}（{src}）が役割の下限 {rfloor:g} を下回る"
                f"＝役割を変える決定の明示が無い  ❌")
    if line is None:
        floor, why = rfloor, "役割の下限"
    elif rfloor is None or line >= rfloor:
        floor, why = line, src
    else:
        floor, why = line, f"{src}・役割を変える決定あり: {decision}"
    ok = rs["per_day"] >= floor
    return ((PASS if ok else FAIL), f"件数/日 が下限以上（{why}）",
            f"下限 {floor:g} → 候補 {rs['per_day']:.2f}" + ("  ✅" if ok else "  ❌"))


def _row_b4(base, bands, sr: dict) -> tuple[str, str, str]:
    label = "ATR% の全帯で土台を悪化させない"
    if bands is not None:
        ng_b = [b[0] for b in bands if not b[3]]
        return ((PASS if not ng_b else FAIL), label,
                f"{len(bands)}帯" + ("  ✅ 全帯で非悪化" if not ng_b
                                     else f"  ❌ 悪化した帯 {', '.join(ng_b)}"))
    if not sr.get("atr_band_edges"):
        return WAIT, label, "— 値がまこさん待ち（帯の切り方）"
    if base is None:
        return UNKNOWN, label, "— 判定不能（土台が無いので帯ごとに比べる相手が無い）"
    return UNKNOWN, label, "— 判定不能（帯ごとの比較が出ていない）"


def slot_usage(t: pd.DataFrame, start, end) -> dict:
    """予算 0.12 BTC の枠をどれだけ使っているか（監査 4-13・要件 R14・H1）。

    ★なぜ判定表に要るか＝目的関数が単独 net だけだと、探索は積み増しの上限を上げ切る方向に押す。
      予算 0.12 BTC は全戦略の共有枠なので、1本のロジックが枠を食えば他が建てられなくなる。
      その量が見えないと、単独 net が良いだけの設定を採ってしまう。
    数え方は score.assert_position_cap と同じ（同時保有の合計を時系列で追う）。あちらは改造しない。
    """
    if t is None or not len(t):
        return {}
    et = pd.to_datetime(t["entry_time"]).tolist()
    xt = pd.to_datetime(t["exit_time"]).tolist()
    sz = t["size_btc"].astype(float).tolist()
    ev = [(et[i], sz[i]) for i in range(len(t))] + [(xt[i], -sz[i]) for i in range(len(t))]
    ev.sort(key=lambda z: (z[0], z[1]))          # 同時刻は決済（マイナス）を先に処理
    cur = mx = 0.0
    prev = pd.Timestamp(start)
    area = 0.0                                   # BTC×秒の合計（時間で重みづけした平均を出すため）
    busy_sec = 0.0                               # 1玉でも持っていた秒数
    for ts, s in ev:
        dt = max((pd.Timestamp(ts) - prev).total_seconds(), 0.0)
        area += cur * dt
        if cur > 1e-12:
            busy_sec += dt
        prev = pd.Timestamp(ts)
        cur = round(cur + s, 9)
        mx = max(mx, cur)
    total_sec = max((pd.Timestamp(end) - pd.Timestamp(start)).total_seconds(), 1.0)
    hold = t["hold_min"].astype(float) if "hold_min" in t.columns else None
    lot = float(t["size_btc"].astype(float).median())
    cap = float(ee.POSITION_CAP_BTC)
    slots = int(cap / lot) if lot > 0 else 0
    ceil_per_day = None
    if hold is not None and len(hold) and float(hold.median()) > 0:
        ceil_per_day = slots * (24 * 60 / float(hold.median()))
    return {"max_btc": mx, "avg_btc": area / total_sec, "cap": cap,
            "busy_ratio": busy_sec / total_sec, "lot": lot, "slots": slots,
            "hold_med": float(hold.median()) if hold is not None and len(hold) else None,
            "ceil_per_day": ceil_per_day}


def _row_slots(base, rs, sr: dict) -> tuple[str, str, str]:
    """枠の占有（監査 4-13）。合否には使わない＝予算 0.12 は全戦略の共有枠で、1本では良し悪しを
    判定できないため（C の原則）。上限を決めたくなったら設定 stop_rules の slot_max_btc で足せる。"""
    label = "枠の占有（予算 0.12 BTC は全戦略の共有枠・合否には使わない）"
    t = rs.get("t")
    su = slot_usage(t, SEARCH_START, SEARCH_END) if t is not None else {}
    if not su:
        return NA, label, "— 売買記録が渡されていないので測れない"
    txt = (f"最大 {su['max_btc']:.4f} BTC（枠の {su['max_btc'] / su['cap'] * 100:.1f}%）"
           f" ／ 時間で重みづけした平均 {su['avg_btc']:.4f} BTC（枠の {su['avg_btc'] / su['cap'] * 100:.1f}%）"
           f" ／ 1玉でも持っていた時間 {su['busy_ratio'] * 100:.1f}%")
    if su.get("hold_med") is not None:
        txt += (f" ／ 保有中央値 {su['hold_med']:.0f}分 ＝ 枠を全部回した場合の上限"
                f" {su['ceil_per_day']:,.0f} 件/日（{su['slots']} 枠）")
    cap_max = sr.get("slot_max_btc")
    if cap_max is not None:
        ok = su["max_btc"] <= cap_max
        return ((PASS if ok else FAIL), label.replace("合否には使わない", f"上限 {cap_max} BTC"),
                txt + ("  ✅" if ok else f"  ❌ 上限 {cap_max} BTC を超えている"))
    return NA, label, txt


def _row_goal(rs, sr: dict) -> tuple[str, str, str]:
    """★参考の行（まこさん承認 2026-08-01・案1）＝月いくら稼いでいるか・担う額にいくら足りないか。

    合否には使わない（印は「判定しない」）。理由＝目標額に届いたかは全戦略を同じ 0.12 BTC で
    一緒に回した合算でしか出ない（C の原則・pdca_flow §6.1）。
    それでも数字は必ず出す＝A と B を全部通っても目標との距離が分からないまま進むのを防ぐため。
    担う額（target_monthly）は戦略の設定から読む。設定に無ければ「未定」と出す＝CC は額を置かない。
    """
    label = "参考: このロジックは月いくら稼いでいるか（合否には使わない）"
    months = (SEARCH_END - SEARCH_START).days / 30.0        # 値決め窓の長さ（periods.py が正本）
    if months <= 0:
        return NA, label, "— 窓の長さが取れない"
    per_month = rs["total"] / months
    tgt = sr.get("target_monthly")
    if tgt is None:
        return (NA, label,
                f"月 ${per_month:+,.2f}（値決め窓 {months:.1f} ヶ月の net ${rs['total']:+,.2f} から）"
                f" ／ 担う額は未定（統合の段で決める）")
    return (NA, label,
            f"月 ${per_month:+,.2f} ／ 担う額 ${tgt:,.2f} に対して ${per_month - tgt:+,.2f}"
            f"（{'届いている' if per_month >= tgt else '足りない'}）")


def _rows_b5b6(stats: dict | None, n_kept: int) -> list[tuple[str, str, str, str]]:
    l5 = "DSR > 0.95（試した回数で割り引いた成績）"
    l6 = "PBO < 0.5（過剰なあてはめの確率）"
    if stats is None:
        return [("B5", l5, f"— 判定不能（通った試行 {n_kept} 本＝統計が出せない）", UNKNOWN),
                ("B6", l6, "— 同上", UNKNOWN)]
    d, p = stats["dsr"], stats["pbo"]
    ok5 = d["dsr"] > tuner_stats.DSR_PASS
    r5 = ("B5", l5, f"{d['dsr']:.3f}" + ("  ✅" if ok5 else "  ❌"), PASS if ok5 else FAIL)
    if p is None:
        r6 = ("B6", l6, "— 判定不能（候補が足りない、または期間が短い）", UNKNOWN)
    else:
        ok6 = p["pbo"] < tuner_stats.PBO_PASS
        r6 = ("B6", l6, f"{p['pbo']:.3f}" + ("  ✅" if ok6 else "  ❌"), PASS if ok6 else FAIL)
    return [r5, r6]


# ══ 判定の1枚表 ═══════════════════════════════════════════════════════════════════════
def build_rows(base, rs, rc, min_per_day, stats: dict | None, n_kept: int,
               rules: dict | None = None, rfloor: float | None = None,
               trials: int = 0, stage_bests=None,
               bands: list | None = None) -> list[tuple[str, str, str, str]]:
    """判定表の全行を (番号, 見るもの, 結果, 状態) で組み立てる。印字と結論はこの表だけから出す。"""
    sr = rules or {}
    st, lab, txt = _row_a1(sr, stage_bests)
    rows = [("A1", lab, txt, st)]
    st, lab, txt = _row_a2(sr, trials)
    rows.append(("A2", lab, txt, st))
    rows += _rows_b1b2(base, rs, rc, sr)
    st, lab, txt = _row_b3(rs, min_per_day, sr, rfloor)
    rows.append(("B3", lab, txt, st))
    st, lab, txt = _row_b4(base, bands, sr)
    rows.append(("B4", lab, txt, st))
    rows += _rows_b5b6(stats, n_kept)
    st, lab, txt = _row_slots(base, rs, sr)
    rows.append(("B7", lab, txt, st))
    st, lab, txt = _row_goal(rs, sr)
    rows.append(("参考", lab, txt, st))
    rows.append(("C", "目標額（月 net $1,900）に届いたか",
                 "— この道具では判定しない（統合の段で合算）", NA))
    return rows


def render_judgement(rows: list) -> tuple[str, str]:
    """判定表の全行 → (結論の種別, 印字する文字列)。印字と保存が同じ文字列を使うようにする。"""
    out = ["\n[判定の1枚表（A＝そのロジックで出し切ったか／B＝その数字が本物か／C＝目標に届いたか）]",
           "| # | 見るもの | 結果 |", "|---|---|---|"]
    for num, lab, txt, _st in rows:
        out.append(f"| {num} | {lab} | {txt} |")
    fails = [n for n, _l, _t, s in rows if s == FAIL]
    waits = [n for n, _l, _t, s in rows if s == WAIT]
    unknowns = [n for n, _l, _t, s in rows if s == UNKNOWN]
    nobase = [n for n, _l, _t, s in rows if s == PASS_NOBASE]
    if fails:
        out.append(f"→ **調整しきれていない**（{', '.join(fails)} が不合格）")
        verdict = FAIL
    elif waits:
        out.append(f"→ 判定できない（{', '.join(waits)} の値が決まっていない）")
        verdict = WAIT
    elif unknowns:
        out.append(f"→ 判定できない（{', '.join(unknowns)} が判定不能）"
                   "＝★判定不能は合格ではない。この状態で『これ以上出ない』とは言わない")
        verdict = UNKNOWN
    elif nobase:
        # ★土台なし＝「前の版より良い」が言えないので「これ以上出ない」とは言わせない（まこさん OK 2026-08-01）
        out.append("→ 試しても利益が増えないところまでは来た。"
                   f"ただし前の版が無いので（{', '.join(nobase)}）、この利益がまぐれかどうかは"
                   "確かめきれていない＝★『これ以上出ない』とは言わない")
        verdict = PASS_NOBASE
    else:
        out.append("→ このロジックはこれ以上出ない（★目標額に届いたかは別＝統合の段で合算して判定する）")
        verdict = PASS
    return verdict, "\n".join(out)


def save_judgement(text: str, tag: str, verdict: str, note: str = "",
                   out_dir: pathlib.Path | None = None) -> pathlib.Path | None:
    """判定表をファイルに残す（まこさん指示 2026-08-01）。

    画面だけだと走らせるたびに流れて消え、検収の証拠が後から見られない。
    同じ日に何度走らせても上書きしないように連番を付ける。
    """
    import time
    d = out_dir or JUDGE_DIR
    try:
        d.mkdir(parents=True, exist_ok=True)
        day = time.strftime("%Y%m%d")
        stem = f"judgement_{tag}_{day}"
        n = len(list(d.glob(f"{stem}_*.txt"))) + 1
        path = d / f"{stem}_{n:03d}.txt"
        head = [
            "=" * 88,
            f"判定の1枚表 ／ {tag}",
            "=" * 88,
            f"日時          : {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"値決め窓      : {SEARCH_START.date()} 〜 {(SEARCH_END - pd.Timedelta(days=1)).date()}",
            f"確認窓        : {CONFIRM_START.date()} 〜 {(CONFIRM_END - pd.Timedelta(days=1)).date()}"
            + ("（値決め窓と同一＝B2 は判定不能）" if (SEARCH_START == CONFIRM_START and SEARCH_END == CONFIRM_END) else ""),
            f"判定表の版    : md5 {_md5(_render(print_judgement))}"
            f"（この道具のコードの版。記録は STEP1/STEP2 と突き合わせる）",
            f"結論          : {verdict}",
        ]
        if note:
            head.append(f"注記          : {note}")
        head.append("")
        path.write_text("\n".join(head) + text + "\n", encoding="utf-8")
        return path
    except Exception as e:                                   # noqa: BLE001  保存に失敗しても判定は出す
        print(f"[判定表の保存に失敗した（判定そのものには影響しない）] {e}")
        return None


def print_judgement(base, rs, rc, min_per_day, stats: dict | None, n_kept: int,
                    rules: dict | None = None, rfloor: float | None = None,
                    trials: int = 0, stage_bests=None,
                    bands: list | None = None, save_tag: str | None = None,
                    save_note: str = "") -> str:
    """判定の1枚表を印字し、結論の種別を返す。save_tag を渡すとファイルにも残す。

    ★印は4つ＝合格 ✅ ／ 不合格 ❌ ／ 値がまこさん待ち ／ 判定不能。
      **判定不能は合格ではない。** 1つでも残っていれば「これ以上出ない」とは言わない。
      値を CC が決めない項目は、勝手に埋めずに「まこさん待ち」と出す（監査 2026-07-27 Q8）。
    """
    rows = build_rows(base, rs, rc, min_per_day, stats, n_kept,
                      rules=rules, rfloor=rfloor, trials=trials,
                      stage_bests=stage_bests, bands=bands)
    verdict, text = render_judgement(rows)
    print(text)
    if save_tag:
        p = save_judgement(text, save_tag, verdict, save_note)
        if p:
            print(f"[保存] {p}")
    return verdict


# ══ 検収に使う入力（合成・売買しない・採点しない）════════════════════════════════════════
def _cases() -> list[tuple[str, dict]]:
    """判定表の分岐をひととおり踏む入力の組。md5 の材料でもある。"""
    rs_a = {"total": 1234.5, "n": 800, "per_day": 8.42}
    rs_b = {"total": -321.0, "n": 120, "per_day": 1.93}
    rc_a = {"total": 987.6, "n": 700, "per_day": 7.11}
    base_a = {"search": {"total": 500.0}, "confirm": {"total": 400.0}}
    stats_ok = {"dsr": {"dsr": 0.987}, "pbo": {"pbo": 0.234}}
    stats_ng = {"dsr": {"dsr": 0.120}, "pbo": None}
    bands_ok = [("〜1", 10.0, 20.0, True), ("1〜2", 5.0, 7.0, True), ("2〜", -3.0, -1.0, True)]
    bands_ng = [("〜1", 10.0, 20.0, True), ("1〜2", 5.0, -7.0, False), ("2〜", -3.0, -9.0, False)]
    edges = [1.0, 2.0]
    return [
        ("① 値が全部まこさん待ち・土台なし・統計なし",
         dict(base=None, rs=rs_a, rc=rc_a, min_per_day=None, stats=None, n_kept=0,
              rules={}, rfloor=None, trials=150, stage_bests=None, bands=None)),
        ("② 土台あり・値そろい・合格側（段は無いので A1 は判定不能のはず）",
         dict(base=base_a, rs=rs_a, rc=rc_a, min_per_day=5.0, stats=stats_ok, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 100, "atr_band_edges": edges},
              rfloor=5.0, trials=150, stage_bests=None, bands=bands_ok)),
        ("③ 土台あり・不合格側（土台割れ・件数下限割れ・帯悪化・統計不合格）",
         dict(base=base_a, rs=rs_b, rc=rc_a, min_per_day=5.0, stats=stats_ng, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 3000, "atr_band_edges": edges},
              rfloor=5.0, trials=150, stage_bests=[100.0, 110.0, 115.0], bands=bands_ng)),
        ("④ 土台なし・net はプラス＝既定の下限 $0 を通る（★直す前は『これ以上出ない』が出ていた分岐）",
         dict(base=None, rs=rs_a, rc=rc_a, min_per_day=5.0, stats=stats_ok, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 100, "atr_band_edges": edges},
              rfloor=5.0, trials=150, stage_bests=[100.0, 105.0, 108.0], bands=bands_ok)),
        ("⑤ 土台なし・net がマイナス＝下限 $0 に落ちる",
         dict(base=None, rs=rs_b, rc=rc_a, min_per_day=5.0, stats=stats_ok, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 100, "atr_band_edges": edges,
                     "target_monthly": 462.54},
              rfloor=5.0, trials=150, stage_bests=[100.0, 105.0, 108.0], bands=bands_ok)),
        ("⑥ ★役割の下限 5 より緩い線 2 を、決定の明示なしで使う＝不合格",
         dict(base=base_a, rs=rs_a, rc=rc_a, min_per_day=2.0, stats=stats_ok, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 100, "atr_band_edges": edges},
              rfloor=5.0, trials=150, stage_bests=[100.0, 105.0, 108.0], bands=bands_ok)),
        ("⑦ 同じ線 2 を、役割を変える決定の明示つきで使う＝通る",
         dict(base=base_a, rs=rs_a, rc=rc_a, min_per_day=2.0, stats=stats_ok, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 100, "atr_band_edges": edges,
                     "role_change_decision": "まこさん 2026-XX-XX・理由は設定に記す"},
              rfloor=5.0, trials=150, stage_bests=[100.0, 105.0, 108.0], bands=bands_ok)),
        ("⑧ 段が3個そろい直近2段の伸びが δ 未満＝A1 合格",
         dict(base=base_a, rs=rs_a, rc=rc_a, min_per_day=5.0, stats=stats_ok, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 100, "atr_band_edges": edges},
              rfloor=5.0, trials=150, stage_bests=[100.0, 112.0, 118.0], bands=bands_ok)),
        ("⑨ 売買記録つき＝B7 枠の占有が出る（合否には使わない）",
         dict(base=base_a, rs={**rs_a, "t": _slot_case()}, rc=rc_a, min_per_day=5.0,
              stats=stats_ok, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 100, "atr_band_edges": edges},
              rfloor=5.0, trials=150, stage_bests=[100.0, 112.0, 118.0], bands=bands_ok)),
        ("⑩ 同じ売買記録で、枠の上限 0.006 BTC を設定＝B7 が不合格になる",
         dict(base=base_a, rs={**rs_a, "t": _slot_case()}, rc=rc_a, min_per_day=5.0,
              stats=stats_ok, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 100, "atr_band_edges": edges,
                     "slot_max_btc": 0.006},
              rfloor=5.0, trials=150, stage_bests=[100.0, 112.0, 118.0], bands=bands_ok)),
    ]


def _slot_case() -> pd.DataFrame:
    """枠の占有の検収に使う売買記録（合成）。2玉が15分だけ重なる＝最大 0.012 BTC。"""
    t0 = SEARCH_START
    return pd.DataFrame({
        "entry_time": [t0, t0 + pd.Timedelta(minutes=15)],
        "exit_time": [t0 + pd.Timedelta(minutes=30), t0 + pd.Timedelta(minutes=45)],
        "size_btc": [0.006, 0.006],
        "hold_min": [30.0, 30.0],
    })


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


# ★判定の意味が変わったことを機械で見えるようにする記録（手で書き換えない＝実測を書き写す）。
#   STEP1＝歩5 の1回目 第1段（engine_tuner.py からの引っ越し直後・判定の意味は修正前のまま）。
#   STEP2＝歩5 の1回目 第2段（A1 の代用の廃止・B3 の役割下限の強制・土台なしの合否＝狙った変更）。
#   ATR% 帯の計算は第2段でも触っていないので、md5 は STEP1 と同じままであること自体が証拠になる。
STEP1_TABLE_MD5 = "ccbfe65aedbdf639a120becaa45304a6"
STEP1_BANDS_MD5 = "ab1f16299bf309d0b580f7749df6cc84"
#   ⚠️ 正直に＝STEP1 と STEP2 の md5 の違いは「判定の直し」だけが原因ではない。検収に使うケースを
#      4個から8個へ増やしたことも入っている。だから md5 は A と B の差分の証拠にはならない。
#      判定が直ったことの証拠は、下の番人（⑤土台なしで合格を出さない ⑥段が無いと A1 は判定不能
#      ⑦判定不能を結論に数える）と、--selftest が印字する表そのもの。md5 は「以後うっかり変えた」を
#      検出する道具として使う。
STEP2_TABLE_MD5: str | None = "58e835f46690cc399823b417c7aeead4"
STEP2_BANDS_MD5: str | None = "ab1f16299bf309d0b580f7749df6cc84"
#   ↑ 2026-08-01 の実測。内訳＝1回目（A1 の代用の廃止・B3 の役割下限の強制・土台なしの合否の新設
#     ＋案1 の $0 と「参考」の行）＋2回目（B7 枠の占有の行の新設）。
#     ATR% 帯は1回目からずっと1行も触っていないので、md5 が第1段のままであること自体が証拠になる。

#   STEP3＝歩5 の3回目（2026-08-01・まこさん OK）。判定表の md5 が STEP2 から動いた理由は2つある。
#     理由1＝窓を分けた（値決め 2024-03-01〜2025-08-31 ／ 確認 2025-09-01〜2026-02-28・periods.py）。
#            分ける前は値決め窓と確認窓が同じ日付で B2 が必ず「判定不能」と出ていた。分けたので
#            B2 が実際に土台と比べた合否を出すようになった＝これが狙った変更の本体。
#     理由2＝「土台なしの合格」PASS_NOBASE を新設した（上のブロックの説明）。
#   ★理由1 が表に出したのが理由2 の必要性＝分けた瞬間に番人⑤が落ち、番人が守っていたのは
#     土台の有無ではなく窓の同一性だったと分かった。番人は落としたまま報告し、まこさんの OK を得てから直した。
#   ATR% 帯の md5 は第1段からここまで一度も動いていない＝帯の計算に触れていないことの機械的な証拠。
STEP3_TABLE_MD5: str | None = "ccd550d57277dd3feed908e37426dc3c"
STEP3_BANDS_MD5: str | None = "ab1f16299bf309d0b580f7749df6cc84"


def run_identity() -> int:
    """いまの判定表の md5 を出し、記録した基準と突き合わせる。engine_tuner.py の配線も確かめる。"""
    h_tbl = _md5(_render(print_judgement))
    h_bnd = _md5(_render_bands(atr_bands, _StubJudge))
    new_role = role_floor("e38")
    print("=" * 80)
    print("tuner_judgement 恒等検収（合成の入力のみ・売買なし・採点なし）")
    print("=" * 80)
    print(f"[窓] 値決め {SEARCH_START.date()}〜{SEARCH_END.date()} ／ 確認 {CONFIRM_START.date()}〜{CONFIRM_END.date()}"
          f"（periods.py が正本・同一窓なら B2 は判定不能）")
    print(f"[いま] 判定表 md5 {h_tbl} ／ ATR%帯 md5 {h_bnd} ／ role_floor('e38') = {new_role}")

    ng = 0
    # ── ATR% 帯は第2段で触っていない＝第1段と同じであることが「触っていない」証拠 ──
    if h_bnd == STEP1_BANDS_MD5:
        print(f"[ATR%帯] 第1段と同じ {STEP1_BANDS_MD5} → ✅ 触っていない")
    else:
        ng += 1
        print(f"❌ [ATR%帯] 第1段 {STEP1_BANDS_MD5} と違う＝触っていないはずの計算が変わっている")

    # ── 判定表は段ごとに意味を変えた＝いまの正は最後の段（STEP3）。それ以外と一致したら退行 ──
    if h_tbl == STEP1_TABLE_MD5:
        ng += 1
        print(f"❌ [判定表] 第1段 {STEP1_TABLE_MD5} に戻っている＝歩5 の直しが消えている")
    elif h_tbl == STEP2_TABLE_MD5:
        ng += 1
        print(f"❌ [判定表] 第2段 {STEP2_TABLE_MD5} に戻っている＝窓の分離と土台なしの合格が消えている")
    if STEP3_TABLE_MD5 is None:
        print("⚠️ STEP3_TABLE_MD5 が未記入。上の判定表 md5 をこのファイルへ書き込むこと"
              "（以後この値が動いたら、また意味が変わった証拠になる）。")
    elif h_tbl != STEP3_TABLE_MD5:
        ng += 1
        print(f"❌ [判定表] 記録した第3段 {STEP3_TABLE_MD5} と違う＝意図しない変更が入っている")
    else:
        print(f"[判定表] 記録した第3段 {STEP3_TABLE_MD5} と一致 → ✅"
              "（第3段＝窓の分離＋土台なしの合格の新設）")

    # ── engine_tuner.py がこのファイルの判定表を呼んでいるか（案B の配線） ──
    try:
        import engine_tuner as old
        import inspect
        same = True
        for name in ("_print_judgement", "_atr_bands", "role_floor"):
            fn = getattr(old, name, None)
            if fn is None or pathlib.Path(inspect.getfile(fn)).name != pathlib.Path(__file__).name:
                same = False
        if same:
            print("[配線] engine_tuner.py は このファイルの判定表・帯計算・台帳参照を呼んでいる → ✅")
        else:
            ng += 1
            print("❌ [配線] engine_tuner.py が自前の判定表に戻っている（案B が壊れている）")
    except Exception as e:                                   # noqa: BLE001
        ng += 1
        print(f"❌ [配線] engine_tuner.py を読み込めない: {e}")

    print("\n" + ("✅ 全部 pass" if ng == 0 else f"❌ 不一致 {ng} 件"))
    return ng


def _sentinels() -> list[str]:
    """番人＝わざと壊した設定で止まる／合格を出さないことの機械確認。"""
    ng: list[str] = []
    rs = {"total": 100.0, "n": 100, "per_day": 8.0}

    # ① 役割の下限 5 より緩い線 2 を、決定の明示なしで回そうとしたら止まる（fail-closed）
    try:
        assert_role_floor("e38", 2.0, {}, rfloor=5.0)
        ng.append("① 役割の下限を割る線が止まらない（fail-closed が死んでいる）")
    except RoleFloorError:
        pass
    # ② 決定の明示があれば通る
    try:
        assert_role_floor("e38", 2.0, {"role_change_decision": "まこさん 2026-XX-XX"}, rfloor=5.0)
    except RoleFloorError:
        ng.append("② 役割を変える決定を明示しても止まってしまう")
    # ③ 役割の下限以上の線なら通る
    try:
        assert_role_floor("e38", 5.0, {}, rfloor=5.0)
    except RoleFloorError:
        ng.append("③ 役割の下限ちょうどの線で止まってしまう")
    # ④ 台帳から実際に引いた値でも同じ判定になる（道具に数字を焼いていないことの確認）
    role, floor = role_floor("e38")
    if role != "scalp" or floor != 5.0:
        ng.append(f"④ 台帳から引いた値が想定と違う（{role} / {floor}）")
    try:
        assert_role_floor("e38", 2.0, {})
        ng.append("④ 台帳から引いた下限で止まらない")
    except RoleFloorError:
        pass

    # ⑤ 土台なしで他が全部合格でも「これ以上出ない」を出さない（監査 1-3 の穴）
    kw = dict(base=None, rs=rs, rc=rs, min_per_day=5.0,
              stats={"dsr": {"dsr": 0.99}, "pbo": {"pbo": 0.1}}, n_kept=90,
              rules={"delta_net": 20.0, "n_max": 100, "atr_band_edges": [1.0]},
              rfloor=5.0, trials=150, stage_bests=[1.0, 2.0, 3.0],
              bands=[("〜1", 1.0, 2.0, True)])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        verdict = print_judgement(**kw)
    if verdict == PASS:
        ng.append("⑤ 土台なしのロジックに『これ以上出ない』が出る（監査 1-3 の穴が残っている）")
    # ⑫ 土台なしで全部通ったときは、黙って落とさず「土台なしの合格」を出す（まこさん OK 2026-08-01）
    #    ＝不合格でも判定不能でもない。線は越えたが「前の版より良い」は言えない、という別の結論。
    if verdict != PASS_NOBASE:
        ng.append(f"⑫ 土台なしで全部通ったのに『土台なしの合格』が出ない（{verdict}）"
                  "＝線を越えたことまで消してしまっている")
    # ⑬ 土台ありで全部通ったときは、これまで通り『これ以上出ない』が出る（土台ありの合格を壊していない）
    kw_base = dict(kw, base={"search": {"total": 1.0}, "confirm": {"total": 1.0}})
    with contextlib.redirect_stdout(io.StringIO()):
        v_base = print_judgement(**kw_base)
    if v_base != PASS:
        ng.append(f"⑬ 土台ありで全部通ったのに『これ以上出ない』が出ない（{v_base}）")

    # ⑧ 土台なしの下限＝net がマイナスなら落ちる（まこさん承認 2026-08-01・案1 の $0）
    st8, _l8, _t8, _s8 = _rows_b1b2(None, {"total": -1.0, "per_day": 8.0}, rs, {})[0]
    if _s8 != FAIL:
        ng.append(f"⑧ 土台なしで net がマイナスなのに落ちない（{_s8}）")
    st9 = _rows_b1b2(None, {"total": 1.0, "per_day": 8.0}, rs, {})[0][3]
    if st9 != PASS_NOBASE:
        ng.append(f"⑧ 土台なしで net がプラスなのに通らない（{st9}）")
    # ⑨ 参考の行は合否に入らない（印は「判定しない」）
    st10, _l10, _t10 = _row_goal({"total": -9999.0}, {"target_monthly": 100.0})
    if st10 != NA:
        ng.append(f"⑨ 参考の行が合否に入っている（{st10}）＝表示だけのはず")

    # ⑩ 枠の占有の既知答え（電卓で出せる合成データ・監査 4-13）
    #    2玉 0.006 BTC が 15分だけ重なる → 最大 0.012 ／ 1時間の窓で時間平均 0.006 ／ 埋まり 75%
    tt = _slot_case()
    su = slot_usage(tt, SEARCH_START, SEARCH_START + pd.Timedelta(hours=1))
    if abs(su["max_btc"] - 0.012) > 1e-9:
        ng.append(f"⑩ 枠の最大の既知答え不一致（0.012 のはずが {su['max_btc']}）")
    if abs(su["avg_btc"] - 0.006) > 1e-9:
        ng.append(f"⑩ 枠の時間平均の既知答え不一致（0.006 のはずが {su['avg_btc']}）")
    if abs(su["busy_ratio"] - 0.75) > 1e-9:
        ng.append(f"⑩ 埋まっていた時間の割合の既知答え不一致（0.75 のはずが {su['busy_ratio']}）")
    if su["slots"] != 20 or abs(su["ceil_per_day"] - 960.0) > 1e-9:
        ng.append(f"⑩ 枠の数と件数の上限の既知答え不一致（20 枠・960 件/日 のはずが "
                  f"{su['slots']} 枠・{su['ceil_per_day']}）")
    # ⑪ 枠の占有は既定では合否に入らない。上限を設定した時だけ合否になる
    if _row_slots(None, {"t": tt}, {})[0] != NA:
        ng.append("⑪ 枠の占有が既定で合否に入っている＝表示だけのはず")
    if _row_slots(None, {"t": tt}, {"slot_max_btc": 0.006})[0] != FAIL:
        ng.append("⑪ 上限 0.006 BTC を超えているのに落ちない")
    if _row_slots(None, {"t": tt}, {"slot_max_btc": 0.02})[0] != PASS:
        ng.append("⑪ 上限 0.02 BTC の内側なのに通らない")

    # ⑥ 段が無いのに A1 が合格になる代用が残っていないか
    kw2 = dict(kw, base={"search": {"total": 0.0}, "confirm": {"total": 0.0}}, stage_bests=None)
    with contextlib.redirect_stdout(io.StringIO()):
        v2 = print_judgement(**kw2)
    if v2 == PASS:
        ng.append("⑥ 段が無いのに『これ以上出ない』が出る（A1 の代用が残っている）")
    st, _lab, _txt = _row_a1({"delta_net": 20.0}, None)
    if st != UNKNOWN:
        ng.append(f"⑥ 段が無いときの A1 が判定不能でない（{st}）")

    # ⑦ 判定不能が結論の集計から漏れていないか（UNKNOWN を1つ混ぜたら PASS を返さない）
    kw3 = dict(kw2, stage_bests=[1.0, 2.0, 3.0], stats=None)
    with contextlib.redirect_stdout(io.StringIO()):
        v3 = print_judgement(**kw3)
    if v3 == PASS:
        ng.append("⑦ 判定不能（B5・B6）が残っているのに『これ以上出ない』が出る")
    return ng


def selftest() -> int:
    """判定表の全分岐を印字し、番人を走らせる（合成の入力のみ・売買なし・採点なし）。

    ★出力はファイルにも残す（まこさん指示 2026-08-01）＝fix_map 歩5 の検収「判定表の全行が
      判定不能の偽装なしに出ること」「わざと下限割れの設定で止まること」の証拠を後から見るため。
    """
    lines = ["=" * 88,
             "tuner_judgement 自己検査（判定表の全分岐＋番人）",
             "★これは合成の入力だけで作った検収の出力です。売買していません。採点もしていません。",
             "  実データの成績ではないので、採否の材料に使わないでください。",
             "=" * 88]
    for label, kw in _cases():
        lines.append(f"\n===== {label} =====")
        _v, text = render_judgement(build_rows(**kw))
        lines.append(text)
    lines.append(f"\n[md5] 判定表 {_md5(_render(print_judgement))}"
                 f" ／ ATR%帯 {_md5(_render_bands(atr_bands, _StubJudge))}")
    role, floor = role_floor("e38")
    lines.append(f"[台帳から引いた値] e38 の役割 {role} ／ 件数/日 の絶対下限 {floor}")
    ng = _sentinels()
    lines.append("\n[番人] ①役割下限を割る線で止まる ②決定の明示があれば通る ③下限ちょうどは通る "
                 "④台帳の実値でも同じ ⑤土台なしで『これ以上出ない』を出さない ⑥段が無いと A1 は判定不能 "
                 "⑦判定不能を数える ⑧土台なしの下限 $0 ⑨参考の行は合否に入らない "
                 "⑩枠の占有の既知答え ⑪枠の占有は既定では合否に入らない "
                 "⑫土台なしで全部通れば『土台なしの合格』が出る ⑬土台ありで全部通れば『これ以上出ない』が出る")
    for x in ng:
        lines.append(f"  ❌ {x}")
    if not ng:
        lines.append("  ✅ 全部 pass")
    text = "\n".join(lines)
    print(text)
    p = save_judgement("\n" + text, "selftest", "pass" if not ng else "fail",
                       note="合成データだけの検収。実データの成績ではない。採否に使わない。")
    if p:
        print(f"\n[保存] {p}")
    return 1 if ng else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="判定の1枚表（A/B/C）＝古い器と新しい器の共通の判定")
    ap.add_argument("--identity", action="store_true", help="md5 を記録した基準と突き合わせ、配線も確かめる")
    ap.add_argument("--selftest", action="store_true", help="判定表の全分岐を印字し、番人を走らせる")
    a = ap.parse_args()
    if a.identity:
        return run_identity()
    if a.selftest:
        return selftest()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

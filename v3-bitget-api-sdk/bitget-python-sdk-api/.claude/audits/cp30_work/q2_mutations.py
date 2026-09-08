"""監査 cp30｜Q2＝番人4件（T-g・T-h・T-i・T-j）を、壊すプログラム5本とは違う壊し方で落としてみる。

★本物のファイルは1文字も書き替えない。
  壊すプログラム（b53〜b57）は observe_diag.py の本文を書き替えて戻す形。
  この監査は「読み込んだあと、記憶の中の関数だけを差し替える」形＝ファイルには一切 触らない。
  ＝壊し方の系統そのものが違うので、「その壊し方に合わせて番人を書いた」かどうかが見える。

走らせるもの＝observe_diag.selftest_insp5(exit_=False)（❌ の一覧が返る）。
各ケースで「どの番人が落ちたか」を名前で出す。
"""
import hashlib
import pathlib
import sys

import numpy as np
import pandas as pd

PR = pathlib.Path("scripts/priority_rebuild").resolve()
sys.path.insert(0, str(PR))
import observe_diag as od  # noqa: E402

ORIG_FRAME = od.insp5_frame
ORIG_CYC = od._cyc
ORIG_CSV = od.ONE_MIN_CSV


def which(ng):
    """❌ の一覧を、番人の名前の集合に直す。"""
    return sorted({x.split(":")[0] for x in ng})


def run(label, expect_note):
    od._CYC_MEMO["sig"], od._CYC_MEMO["v"] = None, {}   # 入れものを毎回 空にする
    ng = od.selftest_insp5(exit_=False)
    print(f"\n【{label}】")
    print(f"  期待: {expect_note}")
    print(f"  実測: 落ちた番人 {which(ng) or '（無し）'} ／ ❌ {len(ng)} 件")
    for x in ng:
        print(f"    ❌ {x[:150]}")
    return which(ng)


def restore():
    od.insp5_frame, od._cyc, od.ONE_MIN_CSV = ORIG_FRAME, ORIG_CYC, ORIG_CSV
    od._ONE_MIN_CACHE.clear()


print("=" * 100)
print("監査 cp30 Q2｜番人4件を、壊すプログラム5本とは違う壊し方で落としてみる（記憶の中の差し替え・ファイルは触らない）")
print("=" * 100)

# ── 0. 何も壊さない（土台の確認）──────────────────────────────────────────
base = run("M0 何も壊さない", "0件（直っているなら全部 通る）")

# ── 1. T-g だけを壊す（枠だけ直す前へ・鍵は生かす）──────────────────────
#   b53 は「枠と鍵を同時に」戻す。ここは枠だけ。設計書の主張
#   「枠だけ戻しても T-j は落ちない」を実測で確かめる。
def frame_old_only(span, tf, one=None):
    return (span if tf == "5m" else od._resample(span, od.TF_RULE[tf])), (
        span.index if tf == "5m" else od._resample(span, od.TF_RULE[tf]).index
        + pd.Timedelta(od.TF_RULE[tf]))


od.insp5_frame = frame_old_only
m1 = run("M1 枠だけを直す前へ戻す（鍵は生きている）",
         "T-g が落ちる。設計書の主張どおりなら T-j は落ちない")
restore()

# ── 2. T-h だけを壊す（鍵から時刻を外す・枠は生かす）────────────────────
def cyc_no_time(d, name, fn):
    sig = (len(d), hashlib.md5(d.close.to_numpy(dtype=float).tobytes()).hexdigest())
    if od._CYC_MEMO["sig"] != sig:
        od._CYC_MEMO["sig"], od._CYC_MEMO["v"] = sig, {}
    if name not in od._CYC_MEMO["v"]:
        od._CYC_MEMO["v"][name] = fn(d)
    return od._CYC_MEMO["v"][name]


od._cyc = cyc_no_time
m2 = run("M2 鍵から時刻の指紋だけを外す（枠は生きている）",
         "T-h が落ちる。設計書の主張どおりなら T-g・T-j は落ちない")
restore()

# ── 3. T-i を、b56 とは違うファイルで壊す ────────────────────────────────
#   b56 は 2023-11-01 版に戻す。ここは 2024-03-01 版（もっと足りない別のファイル）。
od.ONE_MIN_CSV = "data/BTCUSDT-1m-binance-taker-2024-03-01_2026-06-30.csv"
od._ONE_MIN_CACHE.clear()
m3 = run("M3 1分足の指し先を、別の足りないファイル（2024-03-01 版）にする",
         "T-i が落ちる（b56 とは違うファイル）")
restore()

# ── 4. ★T-j の本丸＝「枠も鍵も直っているのに、使い回しが間違ったものを返す」──
#   これは b53・b55 のどちらとも違う壊し方。使い回しの鍵を丸ごと無視して、
#   1回目に計算したものを何が来ても返す（＝落ちた不具合と同じ「別の枠の結果が返る」状態）。
def cyc_always_reuse(d, name, fn):
    if name not in od._CYC_MEMO["v"]:
        od._CYC_MEMO["v"][name] = fn(d)
    return od._CYC_MEMO["v"][name]


od._cyc = cyc_always_reuse
m4 = run("M4 使い回しが、鍵を見ずに1回目の結果を返す（枠は直ったまま）",
         "★T-j が落ちるはず＝落ちた不具合と同じ型（別の枠の結果が返る）を、別の壊し方で作った")
restore()

# ── 5. T-j を、枠の側から壊す（返す枠の長さだけを1本 ずらす）──────────
def frame_short_closed(span, tf, one=None):
    src, closed = ORIG_FRAME(span, tf, one)
    return src, closed[:-1]


od.insp5_frame = frame_short_closed
m5 = run("M5 枠が返す『期間の当てはめ』の長さを1本 減らす",
         "T-j が落ちるはず（返った列の長さと枠の長さが違う）")
restore()

# ── 6. ★T-j の選び方が足りるか＝本物の11本の足で、鍵がぶつかる組が在るか ──
print("\n" + "=" * 100)
print("【M6】本物の設定（11本の足）で、使い回しの鍵がぶつかる組が在るか＝時刻の指紋が本当に要るか")
print("=" * 100)
cfg = od.load_config()
span_s = od.SEARCH_START
span_e = span_s + pd.Timedelta(days=3)
idx5 = pd.date_range(span_s, span_e, freq="5min", inclusive="left")
c5 = 100.0 + np.arange(len(idx5), dtype=float) * 0.01
span = pd.DataFrame({"open": c5, "high": c5 + 0.05, "low": c5 - 0.05,
                     "close": c5, "volume": 1.0}, index=idx5)
one = od.load_1m(span.index[0], span.index[-1])
old_keys, new_keys = {}, {}
print("  足 ／ 本数 ／ 直す前の鍵（本数＋終値）でぶつかる相手 ／ いまの鍵（＋時刻）でぶつかる相手")
for tf in cfg["timeframes"]:
    src, _cl = ORIG_FRAME(span, tf, one)
    ko = (len(src), hashlib.md5(src.close.to_numpy(dtype=float).tobytes()).hexdigest())
    kn = ko + (hashlib.md5(np.ascontiguousarray(src.index.values).tobytes()).hexdigest(),)
    print(f"  {tf:>4} ／ {len(src):>7} 本 ／ 直す前={'★' + old_keys[ko] if ko in old_keys else 'ぶつからない'}"
          f" ／ いま={'★' + new_keys[kn] if kn in new_keys else 'ぶつからない'}")
    old_keys.setdefault(ko, tf)
    new_keys.setdefault(kn, tf)

print("\n" + "=" * 100)
print("まとめ")
print(f"  M0 何も壊さない        → {base or '（落ちない）'}")
print(f"  M1 枠だけ戻す          → {m1}")
print(f"  M2 鍵だけ外す          → {m2}")
print(f"  M3 別の足りないファイル → {m3}")
print(f"  M4 使い回しが鍵を見ない → {m4}")
print(f"  M5 枠の長さを1本ずらす  → {m5}")
print("=" * 100)

#!/usr/bin/env python3
# check_worklog_date.py — worklog を日付をまたいで書き続けていないかを見る（Stop hook の部品）
#
# まこさん指示（2026-09-09・逐語）＝「session_worklogへの記録は日付で区切ってほしい」
#   「今後、このようなこと（日付をまたいで記録し続ける）が無いようにしてほしい」。
# なぜ要るか＝84〜93回目（2026-09-05〜09-09）が、同じ session_worklog_20260904.md に §28〜§64 を
#   書き足し続けた。文章の決まりだけでは止まらなかった（違反の記録25件のうち CC の自己申告は1件）。
#   だから Stop のたびに機械が見て、当たっていればターンを終われない形にする。
#
# 見るもの（2つ・両方とも「ファイルの日付」と「書き換えた時刻」だけを見る＝中身の真偽は見ない）
#   1. いちばん新しい日付の worklog が今日のものでないのに、そのファイルが今日 書き換えられている
#      ＝今日の作業を古い日付のファイルへ書き足した（今日の worklog を作っていない）
#   2. 今日の worklog が在るのに、それより古い日付の worklog の方が後に書き換えられている
#      ＝今日の worklog を作ったあとで、古いファイルへ書き足した
#
# 限界（正直に）＝①書き換えた時刻（mtime）を見るので、touch で時刻を戻せば通る＝明示の違反
#   ②古い日付のファイルを「直す」（誤字・移動の1行）だけでも 2 に当たる＝そのときは今日の worklog を
#     あとで1文字 書き足せば通る（今日の方が新しくなる）＝直す前に今日の worklog を作る運用
#   ③日付をまたぐセッション（23時→翌1時）は、日付が変わった瞬間に 1 が当たりうる＝翌日の worklog を作る
#
# 使い方＝python3 check_worklog_date.py            # 本物の置き場を見る（問題があれば 1 行出して rc=2）
#         python3 check_worklog_date.py --selftest # 作り物の置き場で番人（4件）

import datetime as _dt
import glob
import os
import re
import sys

STATE = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
PAT = re.compile(r"session_worklog_(\d{8})\.md$")


def _files(state_dir: str) -> list:
    out = []
    for p in sorted(glob.glob(os.path.join(state_dir, "session_worklog_*.md"))):
        m = PAT.search(os.path.basename(p))
        if m:
            out.append((m.group(1), p))
    return out                                        # 名前の日付の昇順


def check(state_dir: str, today: str) -> str | None:
    """問題があれば理由の文字列。無ければ None。today＝YYYYMMDD。"""
    files = _files(state_dir)
    if not files:
        return None
    newest_date, newest_path = files[-1]
    if newest_date != today:
        mt = _dt.datetime.fromtimestamp(os.path.getmtime(newest_path)).strftime("%Y%m%d")
        if mt == today:
            return (f"今日の worklog（session_worklog_{today}.md）が無いのに、{os.path.basename(newest_path)} が今日 書き換えられている"
                    f"＝今日の作業を古い日付のファイルへ書き足している")
        return None
    today_mt = os.path.getmtime(newest_path)
    late = [os.path.basename(p) for _d, p in files[:-1] if os.path.getmtime(p) > today_mt]
    if late:
        return (f"今日の worklog（{os.path.basename(newest_path)}）より後に、古い日付の worklog が書き換えられている"
                f"＝{'・'.join(late)}（古いファイルへ書き足していないか）")
    return None


def selftest() -> int:
    import shutil
    import tempfile
    import time
    tmp = tempfile.mkdtemp()
    today = "20260909"
    old = os.path.join(tmp, "session_worklog_20260904.md")
    new = os.path.join(tmp, "session_worklog_20260909.md")
    ng = 0

    def put(p, t=None):
        with open(p, "w", encoding="utf-8") as f:
            f.write("# x\n")
        if t is not None:
            os.utime(p, (t, t))

    now = time.time()
    # T1 今日の worklog が在り、古い方は先に書かれている → 通る
    put(old, now - 100)
    put(new, now)
    r = check(tmp, today)
    print(f"  {'✅' if r is None else '❌'} T1 今日の worklog が在り、古い方は前に書かれている → 通る" + ("" if r is None else f" ← {r}"))
    ng += r is not None
    # T2 今日の worklog が無く、古い方が今日 書き換えられている → 止まる
    os.remove(new)
    put(old, now)
    r = check(tmp, today)
    ok = r is not None and "が無いのに" in r and "今日 書き換えられている" in r
    print(f"  {'✅' if ok else '❌'} T2 今日の worklog が無いのに古いファイルが今日 書き換えられている → 止まる")
    ng += not ok
    # T3 今日の worklog より後に古い方が書き換えられている → 止まる
    put(new, now - 50)
    put(old, now)
    r = check(tmp, today)
    ok = r is not None and "より後に" in r and "session_worklog_20260904.md" in r
    print(f"  {'✅' if ok else '❌'} T3 今日の worklog より後に古い方が書き換えられている → 止まる")
    ng += not ok
    # T4 worklog が1本も無い → 通る／古い方が昨日までしか書かれていない → 通る
    os.remove(new)
    put(old, now - 3 * 86400)
    r4 = check(tmp, today)
    for p in glob.glob(os.path.join(tmp, "*.md")):
        os.remove(p)
    r5 = check(tmp, today)
    ok = r4 is None and r5 is None
    print(f"  {'✅' if ok else '❌'} T4 古い方が今日 触られていない／1本も無い → 通る")
    ng += not ok
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n番人: {4 - ng}/4 pass")
    return 1 if ng else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    r = check(STATE, _dt.date.today().strftime("%Y%m%d"))
    if r:
        print(r)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

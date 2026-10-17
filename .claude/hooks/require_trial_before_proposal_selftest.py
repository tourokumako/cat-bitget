#!/usr/bin/env python3
"""require_trial_before_proposal_selftest.py — 案を出す前の試しの hook の止め方を試す
（2026-10-17・188回目・まこさん「何度も同じ確認を繰り返さないための修正は上記でよい」「１は修正する」）。
本物の記録（.claude/state/sessions）は触らない＝一時のフォルダに試しの記録を書いて、hook の ROOT を差し替える。

見る物＝
  ①止める範囲は変えない（試していない・試しが検査に落ちた・案の中身が試した下書きと違う、は今までどおり止める）。
  ②試した下書きと合わない行が、全部 案の後ろ（下書きと合う最後の行より後ろ）にあるときは、
    「その文を消して案だけを出し直す・試しは走らせ直さない」と案内する（直す前は「下書きに足して試し直す」と案内し、
    案が変わっていないのに12〜17分の試しを走らせ直させた＝直近30日の止め15回のうち9回）。
  T5・T6 の後ろの文は、実際に止められた返信の文（2026-09-30 449d96d6・2026-10-13 8fbba705）。
使い方＝python3 .claude/hooks/require_trial_before_proposal_selftest.py（全部 期待どおりなら exit 0）
"""
import importlib.util
import json
import pathlib
import sys
import tempfile

PY = pathlib.Path(__file__).resolve().parent / "require_trial_before_proposal.py"
spec = importlib.util.spec_from_file_location("rtbp", PY)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

DRAFT = "【4-0 この仕組みは何か】\n本文の1行目\n本文の2行目\n【4-1 システムの境界】\n本文の3行目\n"
SID = "_selftest"
REDO = "試し直す"                 # 試しを走らせ直させる案内に入る語
RESEND = "試しは走らせ直さない"    # 後ろの文を消して出し直させる案内に入る語

# (名前, 返信の文, 試しの記録〔None＝無い〕, 期待＝"通す"／"記録が無い"／"検査に落ちた"／"試し直す"／"消して出し直す")
CASES = [
    ("T1 見出しの無い返信 → 通す", "次の1本へ進みます。", {"ok": True, "draft": DRAFT}, "通す"),
    ("T2 案が試した下書きと同じ → 通す", DRAFT, {"ok": True, "draft": DRAFT}, "通す"),
    ("T3 試しの記録が無い → 止める", DRAFT, None, "記録が無い"),
    ("T4 試しが検査に落ちている → 止める", DRAFT, {"ok": False, "draft": DRAFT, "a_bad": ["A9"]}, "検査に落ちた"),
    ("T5 案の後ろに報告の文（2026-09-30 の実物）→ 消して出し直す",
     DRAFT + "\nworklog 20261001 §1 に、案を出すまでの経緯を書きました。\n", {"ok": True, "draft": DRAFT}, "消して出し直す"),
    ("T6 案の後ろに報告の文（2026-10-13 の実物）→ 消して出し直す",
     DRAFT + "空白の抜けを直しました。同じ抜けがほかに無いかを確かめてから、案を組み立て直します（約4分半）。\n",
     {"ok": True, "draft": DRAFT}, "消して出し直す"),
    ("T7 案の途中の行が下書きと違う → 試し直す",
     DRAFT.replace("本文の2行目", "本文の2行目を書き替えた"), {"ok": True, "draft": DRAFT}, "試し直す"),
    ("T8 案の途中が違い、後ろにも文がある → 試し直す",
     DRAFT.replace("本文の2行目", "本文の2行目を書き替えた") + "worklog に書きました。\n", {"ok": True, "draft": DRAFT}, "試し直す"),
    ("T9 案の見出しの後ろの行が1行も下書きに無い（別の案）→ 試し直す",
     "【4-0 この仕組みは何か】\n別の案の1行目\n", {"ok": True, "draft": DRAFT}, "試し直す"),
    # ★2026-10-17（188回目・まこさん「直す」）＝囲み（```）の中に書いた見出しの例は、案の見出しと数えない。
    #   T10 は、188回目に CC が問題点の説明で書き、この hook に止められた返信の形。
    #   OK された案の逐語のファイル 271本で、囲みの外の案の見出しは320行・囲みの中は0行（同じ回に awk で数えた）。
    ("T10 説明のために囲みの中に書いた見出しの例（試しの記録なし）→ 通す",
     "たとえば次のように書きます。\n\n```\n【4-0 この仕組みは何か】\nこのプログラムは、指標の値を計算して……\n\n"
     "【4-1 システムの境界】\nこのプログラムを呼ぶのは engine_tuner で……\n```\n\nこの【4-0 …】が見出しです。\n", None, "通す"),
    ("T11 囲みの外の本物の案（試しの記録なし）→ 今までどおり止める", DRAFT, None, "記録が無い"),
    ("T12 囲みの中の例の後ろに、囲みの外の本物の案（試しの記録なし）→ 止める",
     "例＝\n```\n【4-0 例の見出し】\n例の本文\n```\n" + DRAFT, None, "記録が無い"),
    ("T13 案の節の中に json の囲みがあり、下書きと同じ → 通す",
     "【4-20 実装の指示】\n```json\n[{\"番号\": 1}]\n```\n",
     {"ok": True, "draft": "【4-20 実装の指示】\n```json\n[{\"番号\": 1}]\n```\n"}, "通す"),
]


def kind(bad: list) -> str:
    if not bad:
        return "通す"
    text = "\n".join(bad)
    if "記録が無い" in text:
        return "記録が無い"
    if "検査を通っていない" in text:
        return "検査に落ちた"
    if RESEND in text and REDO not in text:
        return "消して出し直す"
    if REDO in text:
        return "試し直す"
    return "（分からない止め）" + text[:60]


def main() -> int:
    bad_n = 0
    with tempfile.TemporaryDirectory() as td:
        mod.ROOT = td
        rp = pathlib.Path(td) / ".claude/state/sessions" / SID / "trial_last.json"
        rp.parent.mkdir(parents=True)
        for name, text, rec, want in CASES:
            if rec is None:
                rp.unlink(missing_ok=True)
            else:
                rp.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
            got = kind(mod.check(text, SID))
            ok = got == want
            bad_n += 0 if ok else 1
            print(f"{'✅' if ok else '❌'} {name}（結果 {got}・期待 {want}）")
    print(f"[selftest] {len(CASES) - bad_n}/{len(CASES)}")
    return 0 if bad_n == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

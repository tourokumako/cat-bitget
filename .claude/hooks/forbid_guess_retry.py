#!/usr/bin/env python3
# forbid_guess_retry.py — 確かめずに当てずっぽうで、検査に当たるまで直し続けるやり方を禁じる
#
# まこさん指示（2026-09-30・逐語）＝「確認をせずに、当てずっぽうで当たるまでやり続けるような修正方法は禁じる。」
#   「一回の確認ですべて完全に修正できるように強制しろ」「承認後に修正が発生しないように、事前にミスが無いよう確認をしろ」
#
# なぜ要るか（worklog 20260930 §44〜§53）＝私は検査が落ちると、落ちた1件だけを見て直し、また検査にかけ、
#   次の1件で落ちる、を繰り返した。決まりの文（恒久の決まり72番）は在ったが、止める強制が無かった。
#
# 口（同じ本体を、登録の仕方で使い分ける）
#   post（PostToolUse Bash）＝検査のコマンド（--selftest・--verify・--try・--check・--measure-only・py_compile・
#        check_all_before_handoff・trial_design・run_breaks・_probe を、python3 か bash で走らせたものだけ）の出力を hook が読み、落ちた行を全部 記録する
#        （.claude/state/sessions/<セッション>/check_fail.json）。通れば、その検査の記録を消す。記録は私の申告ではない。
#   pre（PreToolUse Write/Edit/MultiEdit）＝落ちた記録が在る間は、直す計画（同じ置き場の fix_plan.md）を
#        落ちた後に書き、①落ちた行を全部 写し ②落ちた行ごとに、直す所を実物で開いて確かめた「ファイル名:行番号」を書く、
#        まで、ファイルを1つも直させない（1件ずつ当てずっぽうで直すのを止め、全部を1回で直させる）。
#        計画の後に同じ検査がもう1回 落ちたら（2回目以降）、計画を書き直すだけでなく、
#        ③計画に「前の計画で見落とした理由:」の行を書き ④直す所の開いた行を、前の計画より増やす、まで直させない。
#   try ＝手で試す口。
#   直してよいもの（計画と記録のため）＝fix_plan.md・session_worklog_*.md・sessions の下・chat_draft.md。
# 限界（正直に）＝落ちたかは出力の形（❌・fail・Traceback・不足 N 件・R 数字 の行 ほか）で見る（✅ で始まる行は見ない）。
#   計画の中身の正しさは見ない（写したか・開いた行を書いたかだけ）。検査を走らせずに直すことは止めない（後の検査で捕まる）。
import json
import os
import re
import sys
import time

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SESS = ROOT + "/.claude/state/sessions"
CHECK_RE = re.compile(r"--selftest|--verify\b|--try\b|--check\b|--check-design|--measure-only|py_compile|"
                      r"check_all_before_handoff|trial_design|run_breaks\.py|_probe\.py")
FAIL_RE = re.compile(r"❌|→ fail\b|\bFAIL\b|Traceback|SyntaxError|落ちた\s?\d+\s?件|不足\s?\d+\s?件|^R\d+ |rc=[1-9]")
FILELINE_RE = re.compile(r"[\w./-]+\.[A-Za-z]{1,5}:\d+")
FREE = ("fix_plan.md", "/.claude/state/sessions/", "session_worklog_", "chat_draft.md")


def _paths(sid):
    d = os.path.join(SESS, sid or "_nosession")
    return os.path.join(d, "check_fail.json"), os.path.join(d, "fix_plan.md")


def _key(cmd):
    m = re.search(r"([\w.-]+\.py)(?:\s+(--[\w-]+))?", cmd or "")
    return (m.group(1) + (" " + m.group(2) if m.group(2) else "")) if m else (cmd or "")[:60]


def fail_lines(out):
    # ★✅ で始まる行は拾わない（通った行の中に、引用として ❌ の文字が在るため・2026-09-30 に試しの出力で誤って拾った）
    return [ln.strip()[:200] for ln in (out or "").splitlines()
            if ln.strip() and not ln.strip().startswith("✅") and FAIL_RE.search(ln.strip()) and "止める所なし" not in ln]


def record(sid, cmd, out):
    """検査の出力から、落ちた行を記録する（通れば消す）。戻り＝落ちた行の数。"""
    # ★python3 か bash で走らせた断片に検査の語が在るときだけ検査と見る（2026-09-30＝grep と cat で記録を読んだだけの
    #   コマンドを、探す語の「--verify」で検査と見て、読んだ中身の ❌ を落ちた行に書いた）
    parts = [p.strip() for p in re.split(r";|&&|\|\||\|", cmd or "")]
    runs = [p for p in parts if re.match(r"(?:cd \S+ )?(?:python3|bash)\s", p) and CHECK_RE.search(p)]
    if not runs:
        return 0
    cmd = runs[-1]
    fp, plan = _paths(sid)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    rec = json.load(open(fp, encoding="utf-8")) if os.path.isfile(fp) else {}
    key = _key(cmd)
    fails = fail_lines(out)
    if not fails:
        if key in rec:
            rec.pop(key)
            json.dump(rec, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return 0
    prev = rec.get(key) or {}
    planned = bool(prev) and os.path.isfile(plan) and os.path.getmtime(plan) > prev.get("time", 0)
    count = prev.get("count", 0) + 1 if planned or not prev else prev.get("count", 1)
    plan_lines = len(set(FILELINE_RE.findall(open(plan, encoding="utf-8").read()))) if planned else prev.get("plan_lines", 0)
    rec[key] = {"time": time.time(), "cmd": cmd[:300], "fails": fails[:60], "count": count, "plan_lines": plan_lines}
    json.dump(rec, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return len(fails)


def _norm(s):
    return re.sub(r"[\s　`*]+", "", s or "")


def judge(sid, target):
    if any(f in (target or "") for f in FREE):
        return []
    fp, plan = _paths(sid)
    if not os.path.isfile(fp):
        return []
    rec = json.load(open(fp, encoding="utf-8"))
    if not rec:
        return []
    ptxt = open(plan, encoding="utf-8").read() if os.path.isfile(plan) else ""
    pmt = os.path.getmtime(plan) if os.path.isfile(plan) else 0
    np_ = _norm(ptxt)
    opened = set(FILELINE_RE.findall(ptxt))
    bad = []
    for key, r in rec.items():
        if pmt < r["time"]:
            bad.append(f"検査「{key}」が落ちた（{len(r['fails'])} 行）のに、その後に直す計画を書いていない")
            continue
        miss = [f for f in r["fails"] if _norm(f)[:40] not in np_]
        if miss:
            bad.append(f"検査「{key}」の落ちた行のうち {len(miss)} 行が計画に写されていない（最初＝「{miss[0][:60]}」）")
        if len(opened) < 1:
            bad.append("計画に、直す所を実物で開いて確かめた「ファイル名:行番号」が1つも無い")
        if r.get("count", 1) >= 2:
            if "前の計画で見落とした理由:" not in ptxt:
                bad.append(f"検査「{key}」が計画の後にもう1回 落ちた（{r['count']} 回目）＝当てずっぽうの繰り返し。"
                           "計画に「前の計画で見落とした理由:」の行を書く")
            if len(opened) <= r.get("plan_lines", 0):
                bad.append(f"2回目以降は、直す所の開いた行を前の計画（{r.get('plan_lines', 0)} か所）より増やす"
                           "（落ちた所の周りと、同じ事実を書いた場所を全部 開いて確かめる）")
    if not bad:
        return []
    return bad + [f"計画の置き場＝{plan}（落ちた行を全部 写し、1行ずつ原因と、開いて確かめた ファイル名:行番号 を書く）"]


def main(mode):
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:                                        # noqa: BLE001
        return 0
    sid = data.get("session_id") or ""
    if mode == "post":
        inp = data.get("tool_input") or {}
        resp = data.get("tool_response") or {}
        out = resp if isinstance(resp, str) else "\n".join(str(resp.get(k) or "") for k in ("stdout", "stderr", "output"))
        record(sid, str(inp.get("command") or ""), out)
        return 0
    if mode == "pre":
        bad = judge(sid, str((data.get("tool_input") or {}).get("file_path") or ""))
        if not bad:
            return 0
        print("🔒 [当てずっぽうの直しの禁止] まこさん指示 2026-09-30「確認をせずに、当てずっぽうで当たるまでやり続けるような修正方法は禁じる。」"
              "「一回の確認ですべて完全に修正できるように強制しろ」:", file=sys.stderr)
        for b in bad:
            print("   " + b, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "try":
        for b in judge(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "") or ["（止める所なし）"]:
            print(b)
        sys.exit(0)
    sys.exit(main(mode))

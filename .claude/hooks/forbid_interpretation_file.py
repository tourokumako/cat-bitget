#!/usr/bin/env python3
# forbid_interpretation_file.py — 解釈の記録ファイルを作り直せなくする（2026-08-22 まこさん承認・新設）
#
# 目的:
#   解釈ゲート（require_interpretation / reset_interpretation）は 2026-08-18 に まこさんの指示で
#   settings.json の登録から外した（逐語＝「機能してるとは思えないので、これを外してほしい」）。
#   ところが CC は、外したことを忘れて `.claude/state/interpretation.md` を書き続けた（4日間）。
#   まこさんの逐語 2026-08-22＝「CCが解釈した内容をチャット欄ではないところに書いて、
#   それを私が読まないといけないという状態が面倒。」「やめることできるの？interpretation.mdを削除すれば？」
#   → CC の「やめます」は守れない（違反22件のうち、CC が自分で気づいて止まったのは1件だけ）。
#     だからファイルを消したうえで、作り直す道を物理的に塞ぐ。
#
# 何を止めるか:
#   `.claude/state/interpretation.md` と `.claude/state/interpretation_posted` への【書き込み】。
#     - Write / Edit / MultiEdit ＝ file_path がその2本なら止める。
#     - Bash ＝ リダイレクト（> >>）・tee・touch・cp/mv の宛先・sed -i が その2本なら止める。
#
# 何を通すか:
#   - 削除（rm）＝消すのは目的そのもの。
#   - 読む（cat・grep・ls・git 等）＝過去の話を調べるため。
#   - 文章の中でファイル名に触れるだけ（worklog へ書く等）＝引用符とヒアドキュメントの中身を外してから見る。
#
# 解除: 無し（合言葉は 2026-08-16 に全廃）。
# 限界（正直に）:
#   ①別の名前のファイルに同じことを書けば止まらない（CC が「解釈の記録」を別名で始める道は塞げない）。
#   ②この hook のファイル自体を CC が書き換えれば無効にできる＝明示の違反で、プログラムでは見抜けない。
#   ③止めるのは「書き込み」だけ＝ファイルが在る状態を作れないだけで、CC がチャットに長い解釈を貼るのは
#     止められない（それは まこさんの目が最後の関所）。

import json
import os
import re
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
NAMES = ("interpretation.md", "interpretation_posted")

# 書き込みの形（引用符・ヒアドキュメントを外したコマンドに当てる）
WRITE_PATTERNS = [
    r">>?\s*\S*interpretation(?:\.md|_posted)",          # > file / >> file
    r"\btee\s+(?:-a\s+)?\S*interpretation(?:\.md|_posted)",
    r"\btouch\s+\S*interpretation(?:\.md|_posted)",
    r"\bsed\s+-i\b[^|;&]*interpretation(?:\.md|_posted)",
    r"\bcp\s+[^|;&]*\s\S*interpretation(?:\.md|_posted)",
    r"\bmv\s+[^|;&]*\s\S*interpretation(?:\.md|_posted)",
]

MSG = (
    "🔒 [解釈の記録は廃止・safety hook] `.claude/state/interpretation.md` は書きません。\n"
    "   2026-08-18 に まこさんの指示で解釈ゲートを外しました"
    "（逐語「機能してるとは思えないので、これを外してほしい」）。\n"
    "   2026-08-22 に まこさんが削除を決めました"
    "（逐語「interpretation.mdを削除すれば？」「４件をまとめてやっていいよ」）。\n"
    "   ＝解釈は、チャットに直接 書きます。ファイルには残しません。\n"
    "   （消すこと＝rm は通ります。読むこと＝cat・grep も通ります。）"
)


def strip_text(cmd):
    """引用符とヒアドキュメントの中身を外す（文章での言及で誤って止めないため・他 hook と同型）。"""
    s = re.sub(r"<<\s*[\"']?(\w+)[\"']?.*?^\1", " ", cmd, flags=re.S | re.M)
    s = re.sub(r'"[^"]*"', " ", s)
    s = re.sub(r"'[^']*'", " ", s)
    return s


def judge(tool, file_path, cmd):
    """止めるなら理由の文字列、通すなら None。"""
    if tool in ("Write", "Edit", "MultiEdit"):
        if os.path.basename(file_path or "") in NAMES:
            return f"書き込もうとした先: {file_path}"
        return None
    if tool == "Bash":
        x = strip_text(cmd or "")
        for p in WRITE_PATTERNS:
            m = re.search(p, x)
            if m:
                return f"書き込みの形が在る: {m.group(0).strip()}"
        return None
    return None


def hook_main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)                      # 読めない入力では止めない（fail-open）
    if data.get("agent_type"):
        sys.exit(0)                      # サブエージェントは通す
    ti = data.get("tool_input") or {}
    reason = judge(data.get("tool_name", ""), ti.get("file_path", "") or "", ti.get("command", "") or "")
    if reason:
        print(MSG, file=sys.stderr)
        print("", file=sys.stderr)
        print(f"止めた理由: {reason}", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


# ---------------- 番人（わざと壊して、止まることを確かめる） ----------------

def selftest():
    S = os.path.join(ROOT, ".claude", "state")
    cases = [
        # (名前, tool, file_path, cmd, 止まるべきか)
        ("Write で解釈ファイルを作ると止まる", "Write", f"{S}/interpretation.md", "", True),
        ("Edit で解釈ファイルを直すと止まる", "Edit", f"{S}/interpretation.md", "", True),
        ("印のファイルを Write しても止まる", "Write", f"{S}/interpretation_posted", "", True),
        ("ほかのファイルの Write は通る", "Write", f"{S}/session_todo.md", "", False),
        ("リダイレクトで作ると止まる", "Bash", "", f"echo x > {S}/interpretation.md", True),
        ("追記でも止まる", "Bash", "", f"echo x >> {S}/interpretation.md", True),
        ("shasum の結果を印に書くと止まる", "Bash", "",
         f"shasum -a 256 {S}/interpretation.md | awk XX > {S}/interpretation_posted", True),
        ("tee で書くと止まる", "Bash", "", f"echo x | tee {S}/interpretation.md", True),
        ("touch で作ると止まる", "Bash", "", f"touch {S}/interpretation.md", True),
        ("cp で作ると止まる", "Bash", "", f"cp /tmp/a.md {S}/interpretation.md", True),
        ("mv で作ると止まる", "Bash", "", f"mv /tmp/a.md {S}/interpretation.md", True),
        ("sed -i で直すと止まる", "Bash", "", f"sed -i s/a/b/ {S}/interpretation.md", True),
        ("★rm（削除）は通る", "Bash", "", f"rm -f {S}/interpretation.md {S}/interpretation_posted", False),
        ("★読む（cat）は通る", "Bash", "", f"cat {S}/interpretation.md", False),
        ("★読む（grep）は通る", "Bash", "", f"grep -n x {S}/interpretation.md", False),
        ("★git で過去を調べるのは通る", "Bash", "", "git log -- .claude/state/interpretation.md", False),
        ("★worklog にファイル名を書くだけなら通る", "Bash", "",
         "cat >> wl.md <<'EOF'\ninterpretation.md は廃止した > 記録\nEOF", False),
        ("★引用符の中でファイル名に触れるだけなら通る", "Bash", "",
         'echo "interpretation.md を消しました" > /tmp/note.txt', False),
        ("Read は対象外（通る）", "Read", f"{S}/interpretation.md", "", False),
    ]
    ng = 0
    for name, tool, fp, cmd, want_block in cases:
        got = judge(tool, fp, cmd)
        good = (got is not None) == want_block
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た結果: {got}"))
        ng += (not good)
    print(f"\n番人: {len(cases) - ng}/{len(cases)} pass")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    hook_main()

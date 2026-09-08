"""監査 cp32｜3.13＝承認のプログラムの「一致」の判定が、承認の流れを壊していないか。

依頼書 §3.13 の逐語＝「★確かめてほしいこと＝この直しが、承認の流れを壊していないか。
とくに ①存在しない壊すプログラムの行が「未着手」のまま残るか ②ふつうの一致・不一致は今までどおりか。」

★本物のファイルは1文字も書き替えない（読むだけ・呼ぶだけ）。
"""
import pathlib
import subprocess
import sys

REPO = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
sys.path.insert(0, str(REPO / ".claude" / "tools"))
import run_breaks as R  # noqa: E402

print("■ ② ふつうの一致・不一致（match_of を直に呼ぶ）")
cases = [(1, 1, True), (0, 0, True), (0, 1, False), (1, 0, False),
         (None, 1, False), (1, None, False), (None, None, False)]
ok = True
for code, exp, want in cases:
    got = R.match_of(code, exp)
    mark = "✅" if got is want else "❌"
    if got is not want:
        ok = False
    print(f"  {mark} code={code!r:>5} ／ expect={exp!r:>5} → match={got}（期待 {want}）")

print("\n■ ① 壊すプログラムが無い行（expect_of が読めない）")
rc, means, why = R.expect_of("b99_does_not_exist.sh")
print(f"  expect_of('b99_does_not_exist.sh') → rc={rc!r} ／ means={means!r} ／ 読めなかった理由={why!r}")
print(f"  match_of(None, {rc!r}) = {R.match_of(None, rc)}（＝一致とみなさない）")

print("\n■ 直す前のコードなら、どうなっていたか（`match = (code == exp)`）")
print(f"  (None == None) = {None == None}  ＝『期待どおり』に数えられていた")  # noqa: E711

print("\n■ 本物の記録（承認のときに機械が走らせたもの）")
rec = REPO / ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/"
              "insp5-path-and-tidy-head-20260908.breaks.json")
import json  # noqa: E402
d = json.loads(rec.read_text(encoding="utf-8"))
for r in d["rows"]:
    print(f"  #{r['no']} {r['script']}: code={r['code']} expect={r['expect']} match={r['match']}")

print("\n■ 番人（run_breaks.py --selftest）")
r = subprocess.run([sys.executable, str(REPO / ".claude/tools/run_breaks.py"), "--selftest"],
                   capture_output=True, text=True)
print("  " + (r.stdout + r.stderr).strip().splitlines()[-1])
sys.exit(0 if ok else 1)

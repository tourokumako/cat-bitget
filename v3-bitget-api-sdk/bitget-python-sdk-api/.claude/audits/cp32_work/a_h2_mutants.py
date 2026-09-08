"""監査 cp32｜別枠 A＝指紋を照らす口を5通りに壊して、足した番人2件が落ちるかを見る。

依頼書 §3.4 の A の逐語＝「★2通りとも捕まえる形になっているか、また5通りに壊して確かめてください」。
cp31 が生き残ると報告した2通り＝④先頭8文字だけで比べる ⑤`check_fingerprint` の中の
必須ファイルの検査を外す。**cp31 と同じ壊し方にするため、④⑤は `check_fingerprint` の中だけを壊す。**

★本物の `.claude/hooks/enforce_h2_pass.py` は1文字も書き替えない（控えを作って走らせる）。
★控えの中の ROOT は絶対のパスなので、置き場所を変えても同じものを見る。
"""
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/enforce_h2_pass.py")
TEXT = SRC.read_text(encoding="utf-8")
_I = TEXT.index("def check_fingerprint() -> int:")


def only_in_fp(old: str, new: str) -> str:
    """`check_fingerprint` の中だけを1回 置き換える（cp31 と同じ壊し方にする）。"""
    return TEXT[:_I] + TEXT[_I:].replace(old, new, 1)


MUT = {
    # ① check_fingerprint が必ず 0 を返す（依頼書 cp31 が名指しした形）
    "m1_always0.py": only_in_fp('def check_fingerprint() -> int:\n    """',
                                'def check_fingerprint() -> int:\n    return 0\n    """'),
    # ② check_fingerprint が必ず 1 を返す
    "m2_always1.py": only_in_fp('def check_fingerprint() -> int:\n    """',
                                'def check_fingerprint() -> int:\n    return 1\n    """'),
    # ③ 必須ファイルの検査を、在る所ぜんぶ外す（見張り本体も含む）
    "m3_no_must.py": re.sub(r"lack = \[m for m in MUST if m not in files\]", "lack = []", TEXT),
    # ④ 指紋を先頭8文字だけで比べる（cp31 で生き残った1つ目・口の中だけ）
    "m4_prefix8.py": only_in_fp("if now != fp:", "if now[:8] != fp[:8]:"),
    # ⑤ 口の中の必須ファイルの検査だけを外す（cp31 で生き残った2つ目）
    "m5_no_must_only_fp.py": only_in_fp("lack = [m for m in MUST if m not in files]", "lack = []"),
}


def run(path: pathlib.Path) -> tuple:
    r = subprocess.run([sys.executable, str(path), "--selftest"], capture_output=True, text=True)
    out = r.stdout + r.stderr
    ng = [x.strip() for x in out.splitlines() if x.strip().startswith("❌ ")
          and "印と、いまのコードが" not in x and "印の対象一覧に必須" not in x]
    cnt = [x.strip() for x in out.splitlines() if "番人:" in x]
    return r.returncode, (cnt[-1] if cnt else "(件数の行なし)"), ng


print(f"元のファイル: {SRC}（{len(TEXT.splitlines())} 行）")
rc0, cnt0, ng0 = run(SRC)
print(f"  素のまま     : rc={rc0} ／ {cnt0}")
for name, body in MUT.items():
    if body == TEXT:
        print(f"  ★{name}: 壊せなかった（置き換えの文字が見つからない）＝この試しは無効")
        continue
    p = HERE / name
    p.write_text(body, encoding="utf-8")
    rc, cnt, ng = run(p)
    print(f"  {name}: rc={rc} ／ {cnt}")
    for x in ng[:6]:
        print(f"      落ちた札: {x}")

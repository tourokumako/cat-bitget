#!/usr/bin/env python3
"""監査 cp33 — 足した番人が「直す前のコード」で本当に落ちるか（依頼書 §3.7）。

★本物のファイルは1文字も書き替えない。ソースを読んで、記憶の中で直す前へ戻し、
  その場で走らせる（cp32 の g_tidy_prefix.py と同じ形）。
  壊すプログラム b63・b64・b65（observe_diag）と b67（tidy_next_step）に当たる。
"""
import importlib.util
import pathlib
import sys
import types

SDK = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api")
ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
OBS = SDK / "scripts" / "priority_rebuild" / "observe_diag.py"
TIDY = ROOT / ".claude" / "tools" / "tidy_next_step.py"
sys.path.insert(0, str(OBS.parent))


def run_source(path: pathlib.Path, src: str, modname: str):
    """ソースの文字列を、そのファイルの場所のモジュールとして走らせて返す。"""
    m = types.ModuleType(modname)
    m.__file__ = str(path)
    m.__name__ = modname
    sys.modules[modname] = m
    exec(compile(src, str(path), "exec"), m.__dict__)
    return m


OBS_SRC = OBS.read_text(encoding="utf-8")
OBS_MUT = {
    "b63 相当＝Binance Spot 系列だけを見る判定を消す": (
        '        if "bitget" in p.name.lower():                     # ★A＝Binance Spot 系列だけを見る\n'
        '            continue\n',
        '        pass  # 監査 cp33 が、Binance Spot 系列だけを見る判定を消した\n'),
    "b64 相当＝下の階層まで見る形を、直下だけへ戻す": (
        'for p in sorted(d.rglob("BTCUSDT-5m-*.csv")):',
        'for p in sorted(d.glob("BTCUSDT-5m-*.csv")):'),
    "b65 相当＝末が読めないものを報告する処理を消す": (
        '        if not ts:                                         # ★C＝読めないものを黙って飛ばさない\n'
        '            bad.append(str(p.relative_to(d)))\n'
        '            continue\n',
        '        if not ts:\n            continue\n'),
}

print("=" * 76)
print("足した番人は、直す前のコードで落ちるか（監査 cp33・依頼書 §3.7）")
print("=" * 76)

base = run_source(OBS, OBS_SRC, "obs_intact")
ng = base.selftest_insp5(exit_=False)
print(f"\n■ いまのコード（素のまま）  ❌ {len(ng)} 件")
for x in ng:
    print("   " + x[:150])

for name, (old, new) in OBS_MUT.items():
    if OBS_SRC.count(old) != 1:
        print(f"\n■ {name}  ★前提が変わった（{OBS_SRC.count(old)} 件・1件のはず）")
        continue
    m = run_source(OBS, OBS_SRC.replace(old, new, 1), "obs_mut")
    ng = m.selftest_insp5(exit_=False)
    print(f"\n■ {name}  ❌ {len(ng)} 件  → {'落ちた（守りが働いた）' if ng else '★落ちない'}")
    for x in ng:
        print("   " + x[:170])

# ── b67 相当＝印の時刻を照らす検査を消す（tidy_next_step）──────────────
TIDY_SRC = TIDY.read_text(encoding="utf-8")
OLD_T = '''        if h2["when"] not in body:
            ng.append(f"(c) (0-b-2) の H2 の時刻が json（{h2['when']}）と違う → `--write`")
        if g2["when"] not in body:
            ng.append(f"(c) (0-b-2) の G2 の時刻が json（{g2['when']}）と違う → `--write`")'''
print("\n" + "-" * 76)
if TIDY_SRC.count(OLD_T) != 1:
    print(f"■ b67 相当  ★前提が変わった（{TIDY_SRC.count(OLD_T)} 件・1件のはず）")
else:
    spec = importlib.util.spec_from_file_location("tidy_intact", TIDY)
    t0 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(t0)
    print("■ b67 相当＝印の時刻を照らす検査を消す")
    try:
        t0.selftest()
    except SystemExit as e:
        print(f"   いまのコード rc={e.code}")
    tm = run_source(TIDY, TIDY_SRC.replace(OLD_T, "        pass", 1), "tidy_mut")
    try:
        tm.selftest()
    except SystemExit as e:
        print(f"   消した後 rc={e.code}  → {'落ちた（守りが働いた）' if e.code else '★落ちない'}")

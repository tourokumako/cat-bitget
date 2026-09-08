"""監査 cp30｜絞った控えで作られる材料 66種の名前を出す（走行の中身を見積もるため）。"""
import pathlib
import sys

PR = pathlib.Path("scripts/priority_rebuild").resolve()
sys.path.insert(0, str(PR))
import observe_diag as od  # noqa: E402

cfg = od.load_config(".claude/audits/cp30_work/observe_config_cp30.json")
cat = od.build_catalog(cfg)
print(f"材料 {len(cat)} 種 ／ 足 {cfg['timeframes']}")
for i, (name, _fn, _d) in enumerate(cat, 1):
    print(f"  {i:>3} {name}")

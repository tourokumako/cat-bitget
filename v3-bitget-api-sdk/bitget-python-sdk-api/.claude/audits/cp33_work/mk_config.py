"""監査 cp33｜検査の順番と、検査5 の数字を試すための設定の控えを作る。

★本物の `observe_config.json` は1文字も書き替えない（H2 の印の対象に入っている）。
作るもの
  A) cfg_5m_only.json ＝足を 5m だけ・材料はサイクル系2種だけ（`--only` の5通りの試し）
  B) cfg_1m3m.json    ＝足を 1m・3m・5m の3本・材料は同じ2種（cp31 と同じ形）
     ＝検査5 が出す数字が、この工事の前と同じかを照らすため（恒等の確認）
"""
import json
import pathlib
import sys

SDK = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str((SDK / "scripts" / "priority_rebuild").resolve()))
import observe_diag as od  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
SRC = SDK / "scripts" / "priority_rebuild" / "observe_config.json"
KEEP = {"HT_DCPERIOD", "HT_INPHASE%"}


def build(tfs, name, note):
    cfg = json.loads(SRC.read_text(encoding="utf-8"))
    cfg["timeframes"] = tfs
    cfg["drop_columns"] = []
    names = [n for n, _f, _d in od.build_catalog(cfg)]
    cfg["drop_columns"] = [[n, "HT_DCPERIOD"] for n in names if n not in KEEP]
    cfg["_cp33"] = note
    dst = HERE / name
    dst.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    got = od.load_config(str(dst))
    print(f"書き出した: {dst.name} ／ 足 {got['timeframes']} ／ "
          f"材料 {[n for n, _f, _d in od.build_catalog(got)]}")


build(["5m"], "cfg_5m_only.json", "監査 cp33｜足は5mだけ・材料2種。本物ではない。")
build(["1m", "3m", "5m"], "cfg_1m3m.json", "監査 cp33｜足は1m・3m・5m・材料2種。本物ではない。")

"""監査 cp31｜検査の順番と、列の絞りを試すための設定の控えを2つ作る。

★本物の `observe_config.json` は1文字も書き替えない（H2 の印の対象22件に入っている）。

作るもの
  A) cfg_5m_only.json  ＝足を 5m だけにした控え（1分足を読まない＝速い）。
     使い道＝`--only` の順番の試し（検査5 が走ったかどうかだけを見る）。
  B) cfg_1m3m.json     ＝足を 1m・3m・5m の3本にした控え（cp30 と同じ形）。
     使い道＝`--cols` が検査5 に効くかの試し。
どちらも材料は `drop_columns` でサイクル系2種だけに絞る（走る時間を短くするため）。
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
    cfg["drop_columns"] = []                       # 先に空にしてから、全部の名前を数える
    names = [n for n, _f, _d in od.build_catalog(cfg)]
    cfg["drop_columns"] = [[n, "HT_DCPERIOD"] for n in names if n not in KEEP]
    cfg["_cp31"] = note
    dst = HERE / name
    dst.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    got = od.load_config(str(dst))
    print(f"書き出した: {dst.name} ／ 足 {got['timeframes']} ／ "
          f"材料 {[n for n, _f, _d in od.build_catalog(got)]}")


build(["5m"], "cfg_5m_only.json", "監査 cp31｜足は5mだけ・材料2種。本物ではない。")
build(["1m", "3m", "5m"], "cfg_1m3m.json", "監査 cp31｜足は1m・3m・5m・材料2種。本物ではない。")

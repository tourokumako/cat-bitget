"""監査 cp30｜検査5 を「落ちた系統だけ」に絞って走らせるための控えを作る。

★なぜ2つ目の控えが要るか
  1つ目の控え（66種）は、1分足が 1,585,440行 に増えたため 20分を超えても終わらない。
  中に PSAR・TD_SEQ・SMC_SWEEP のような、1行ずつ Python で回す重い指標が入っているため。
  依頼書 Q1 が知りたいのは2つだけ＝①最後まで走るか ②1m・3m の有効標本数が 158,112 と違うか。
  ＝落ちた系統（サイクル系＝`_cyc` を通る指標）だけ残せば、その2つは同じように測れる。

残す8種＝HT_DCPERIOD（設計書が数字を挙げた列）／HT_INPHASE%（実際に落ちた列）／
        HT_DCPHASE・HT_QUAD%・HT_SINE・HT_LEADSINE・HT_TRENDMODE・EBSW。
省き方＝設定ファイルに元から在る drop_columns（左＝省く・右＝残す）を使う。
★本物の observe_config.json は1文字も書き替えない。
"""
import json
import pathlib

SRC = pathlib.Path(".claude/audits/cp30_work/observe_config_cp30.json")
DST = pathlib.Path(".claude/audits/cp30_work/observe_config_cp30_small.json")
KEEP = {"HT_DCPERIOD", "HT_INPHASE%", "HT_DCPHASE", "HT_QUAD%",
        "HT_SINE", "HT_LEADSINE", "HT_TRENDMODE", "EBSW"}

import sys  # noqa: E402
sys.path.insert(0, str(pathlib.Path("scripts/priority_rebuild").resolve()))
import observe_diag as od  # noqa: E402

cfg = json.loads(SRC.read_text(encoding="utf-8"))
names = [n for n, _f, _d in od.build_catalog(cfg)]
drop = [[n, "HT_DCPERIOD"] for n in names if n not in KEEP]
cfg["drop_columns"] = drop
cfg["_cp30_small"] = "監査 cp30｜サイクル系8種だけ残した控え。本物ではない。"
DST.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")

cfg2 = od.load_config(str(DST))
print(f"書き出した: {DST}")
print(f"省いた材料: {len(drop)} 種 ／ 残した材料: {len(od.build_catalog(cfg2))} 種")
print(f"残った名前: {[n for n, _f, _d in od.build_catalog(cfg2)]}")
print(f"足: {cfg2['timeframes']}")

"""監査 cp30｜検査5 を絞って走らせるための「設定の控え」を作る（read-only の材料作り）。

★本物の observe_config.json は1文字も書き替えない（H2 の印の対象22件に入っている）。
  読み取って、時間足と材料の数だけを絞った別ファイルを、この監査の作業場に書き出す。

絞るもの2つ
  1. timeframes ＝ 1m・3m・5m の3つだけ（依頼書 Q1 が求める比較に要る3つ）
  2. 材料のパラメータの一覧 ＝ 全部 空にする（build_catalog の for が回らなくなり、
     設定に依らず必ず作られる指標＝サイクル系 HT_* などだけが残る）
     ＝落ちた列 HT_INPHASE% と、設計書が数字を挙げた HT_DCPERIOD は、どちらも残る。
  3. drop_columns ＝ 空にする（残す側の列がカタログから消えると build_catalog が止まるため）

変えないもの＝warmup_days（250日）・period（採点窓）。有効標本数を本物と同じ条件で数えるため。
"""
import json
import pathlib
import sys

SRC = pathlib.Path("scripts/priority_rebuild/observe_config.json")
DST = pathlib.Path(".claude/audits/cp30_work/observe_config_cp30.json")

# build_catalog が読むパラメータの一覧（実測＝sed -n '1191,1541p' observe_diag.py | grep cfg[...]）
PARAM_KEYS = [
    "atr_periods", "bb_periods", "bb_sigma", "body_ratio_periods", "cdl_z_periods",
    "cmf_periods", "donchian_periods", "ema_periods", "fib_windows", "fractal_k",
    "ichimoku", "keltner", "lrsi_gamma", "macd_params", "mfi_periods", "mmar_periods",
    "mmi_periods", "obv_slope_periods", "pivot_windows", "rainbow", "rci_periods",
    "realized_vol_periods", "roc_periods", "rsi_periods", "sma_periods", "sr_tol",
    "sr_windows", "stoch_periods", "supertrend", "swing_windows",
    "volume_change_periods", "volume_ratio_periods", "vp_windows", "vwap_windows",
    "w_tol", "zscore_periods",
]

cfg = json.loads(SRC.read_text(encoding="utf-8"))
cfg["timeframes"] = ["1m", "3m", "5m"]
for k in PARAM_KEYS:
    if k in cfg:
        cfg[k] = []
cfg["drop_columns"] = []
cfg["_cp30"] = "監査 cp30 の作業用の控え。本物ではない。時間足3つ・材料のパラメータは全部 空。"

DST.parent.mkdir(parents=True, exist_ok=True)
DST.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"書き出した: {DST}")
print(f"timeframes: {cfg['timeframes']}")
print(f"空にしたパラメータの一覧: {len([k for k in PARAM_KEYS if k in cfg])} 件")
sys.exit(0)

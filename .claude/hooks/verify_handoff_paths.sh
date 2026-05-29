#!/bin/bash
# L-239 ずれ防止: 新セッション開始時に「次セッション着手」ブロックの参照パスを自動 ls チェック。
# WORKFLOW.md 🔴 active ブロック + ml_pipeline_baseline §8「現在地+次セッション着手」から
# results/ scripts/ data/ .claude/ 配下の .parquet/.py/.md/.json/.csv/.joblib パスを抽出 → 存在確認。
# ❌欠落があれば、引き継ぎ記述が古い/思い込みの疑い → 着手前に疑う (= 学習済み誤断定・データ再作成の無駄を防ぐ)。
SDK="/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api"
python3 - "$SDK" << 'PYEOF'
import sys, re, os, glob
SDK = sys.argv[1]

def block(path, start_pat, end_pat=None):
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except Exception:
        return ""
    out, on = [], False
    for ln in lines:
        if not on and re.search(start_pat, ln):
            on = True
        elif on and end_pat and re.search(end_pat, ln):
            break
        if on:
            out.append(ln)
    return "\n".join(out)

# WORKFLOW active ブロック (🔴 現在のフェーズ → 次の 🧊 改訂N ブロック)
wf = block(f"{SDK}/WORKFLOW.md", r"🔴 現在のフェーズ", r"🧊 改訂\d+ ブロック")
# ml_pipeline §8 現在地+次セッション着手 (末尾まで)
ml = block(f"{SDK}/.claude/memory/ml_pipeline_baseline_v1.md", r"現在地 \+ 次セッション着手")
text = wf + "\n" + ml

pat = r'(?:results|scripts|data|\.claude)/[A-Za-z0-9_./{}*-]+\.(?:parquet|py|md|json|csv|joblib)'
paths = sorted(set(re.findall(pat, text)))

print("=== 次セッション着手: 参照パス存在チェック (自動・L-239 ずれ防止) ===")
if not paths:
    print("⚠️ 引き継ぎブロックにファイルパスなし (= 実行可能テンプレ未記載の疑い・5列表で書き直せ)")
miss = 0
for p in paths:
    gp = re.sub(r'\{[^}]*\}', '*', p)  # {label} 等テンプレ → glob
    full = os.path.join(SDK, gp)
    hit = glob.glob(full)
    if hit:
        print(f"✅ {p}")
    else:
        print(f"❌ 欠落: {p}")
        miss += 1
print(f"--- 欠落 {miss} / 計 {len(paths)} 件。❌ があれば引き継ぎ記述が古い/思い込みの疑い → 着手前に検証 ---")
PYEOF
exit 0

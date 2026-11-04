#!/bin/bash
# CP101 Q6・Q10 の1つ目＝完成の条件の14行を、依頼書の文字のまま SDK のフォルダで走らせる（読むだけ）
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api || exit 9
export PYTHONDONTWRITEBYTECODE=1
O=$(mktemp)
run() { local name="$1"; shift; local t0=$(date +%s); "$@" >"$O" 2>&1; local rc=$?; echo "$name rc=$rc 秒=$(( $(date +%s)-t0 )) 最後の行=$(tail -1 "$O" | cut -c1-200)"; }

c1() { jq -e '(reduce .["法則の行"][] as $r (0; .+1))==40 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="決済の枝" then .+1 else . end))==31 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="売り方" then .+1 else . end))==5 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="建てる前の確認" then .+1 else . end))==1 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="玉全体の決済" then .+1 else . end))==2 and (reduce .["法則の行"][] as $r (0; if $r["区分"]=="玉の持ち方" then .+1 else . end))==1' scripts/priority_rebuild/laws/laws.json; }
c2() { jq -e '(reduce .["条件の書き方"][] as $r (0; .+1))==13 and (reduce .["玉の状態"][] as $r (0; .+1))==9 and (reduce .["法則の中の数"][] as $r (0; .+1))==50' scripts/priority_rebuild/laws/laws.json; }
c3() { python3 scripts/priority_rebuild/laws/laws.py --selftest; }
c4() { python3 scripts/priority_rebuild/laws/laws.py --verify; }
c5() { python3 scripts/priority_rebuild/laws/laws.py --check-sources; }
c6() { T=$(mktemp) && git show cbde6ab2:v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json > "$T" && jq -e --slurpfile o "$T" '(reduce .["使い方の記録"][] as $r (0; .+1))==20 and $o[0]["使い方の記録"]==.["使い方の記録"][0:16] and $o[0]["指標の記録"]==.["指標の記録"] and $o[0]["部品の記録"]==.["部品の記録"]' scripts/priority_rebuild/indicators/indicators.json; }
c7() { T=$(mktemp) && python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/check_one_path.py --test T44 > "$T"; grep -q '通る 1 件' "$T"; }
c8() { python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/gen_req_trace.py --check; }
c9() { jq -e --slurpfile l scripts/priority_rebuild/laws/laws.json '((reduce range(1;31) as $i ([]; . + ["\($i)"])) - (reduce (.["要素の定義表"]["要素"][]["根拠"]["構造に要ること"][], $l[0]["要素の定義表"]["要素"][]["根拠"]["構造に要ること"][]?) as $n ([]; . + ["\($n)"])) - (reduce path(.["要素の定義表"]["この表で受けない要ること"][]) as $p ([]; . + [$p[2]]))) == []' scripts/priority_rebuild/indicators/indicators.json; }
c10() { jq -e --slurpfile l scripts/priority_rebuild/laws/laws.json '(["使い方の記録","指標の記録","部品の記録"] - [.["要素の定義表"]["要素"][]["置く記録"]]) == [] and (reduce $l[0]["要素の定義表"]["要素"][] as $r (0; if $r["置く記録"]=="法則の記録" then .+1 else . end))==10' scripts/priority_rebuild/indicators/indicators.json; }
c11() { jq -e '.["要素の定義表"]["選べる値"]["区分"]==["相場の法則","組み合わせの法則","売り方","建てる前の確認","決済の枝","玉全体の決済","玉の持ち方","役割ごとの決まり"]' scripts/priority_rebuild/laws/laws.json; }
c12() { T=$(mktemp) && git show 1f6f5ff9:v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json > "$T" && jq -e --slurpfile o "$T" '$o[0]["指標の記録"]==.["指標の記録"] and $o[0]["使い方の記録"]==.["使い方の記録"][0:16] and $o[0]["部品の記録"]==.["部品の記録"]' scripts/priority_rebuild/indicators/indicators.json; }
c13() { grep -c -e 'laws/laws.py' -e 'check_one_path.py --test T44' /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py; }
c14() { ! grep -q '法則の行を入れるのは 209番と 195番' .claude/rules/要件定義書_レベル4_指標の構造.md; }
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14; do run "条件$i" c$i; done

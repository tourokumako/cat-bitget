#!/bin/bash
# L-236 物理強制経路: WebSearch / WebFetch 実行時に marker timestamp を更新
# check_websearch_before_design_write.sh が読み込んで使う

mkdir -p /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state
date +%s > /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/last_websearch.timestamp
exit 0

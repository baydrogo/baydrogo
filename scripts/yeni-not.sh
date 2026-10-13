#!/bin/sh
# Yeni kısa not oluşturur:  ./scripts/yeni-not.sh [etiket1,etiket2]
cd "$(dirname "$0")/.." || exit 1
dosya="_posts/notlar/$(date +%Y-%m-%d-%H%M).md"
cat > "$dosya" <<NOT
---
date: $(date "+%Y-%m-%d %H:%M:%S %z")
tags: [${1:-}]
---

NOT
echo "$dosya"
${EDITOR:-open} "$dosya"

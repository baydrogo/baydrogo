#!/bin/sh
# Yeni uzun yazı oluşturur:  ./scripts/yeni-yazi.sh "Yazının başlığı" [etiket1,etiket2]
cd "$(dirname "$0")/.." || exit 1
[ -z "$1" ] && { echo 'Kullanım: ./scripts/yeni-yazi.sh "Başlık" [etiketler]'; exit 1; }
slug=$(printf '%s' "$1" | sed -e 's/ç/c/g;s/Ç/c/g;s/ğ/g/g;s/Ğ/g/g;s/ı/i/g;s/İ/i/g;s/ö/o/g;s/Ö/o/g;s/ş/s/g;s/Ş/s/g;s/ü/u/g;s/Ü/u/g;s/â/a/g;s/î/i/g;s/û/u/g' | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
dosya="_posts/yazilar/$(date +%Y-%m-%d)-$slug.md"
cat > "$dosya" <<YAZI
---
title: "$1"
date: $(date "+%Y-%m-%d %H:%M:%S %z")
tags: [${2:-}]
description: ""
---

YAZI
echo "$dosya"
${EDITOR:-open} "$dosya"

---
layout: default
title: Arşiv
permalink: /arsiv/
---

# Tüm Yazılar

<ul class="post-list">
{% for post in site.posts %}
  <li class="post-item" style="padding: 0.75rem 0; border-bottom: 1px solid #e5e7eb;">
    <span style="font-family: sans-serif; font-size: 0.875rem; color: #666; margin-right: 1rem;">
      {{ post.date | date: "%-d %B %Y" }}
    </span>
    <a href="{{ post.url | relative_url }}" style="color: #2d2d2d; text-decoration: none; font-weight: 500;">
      {{ post.title }}
    </a>
  </li>
{% endfor %}
</ul>

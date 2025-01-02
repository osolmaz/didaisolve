---
layout: default
title: "Home"
---

# Open Problems

Below is a list of open problems tracked by **Did AI Solve?**. Click any to see details.

| Problem | Status |
|---------|--------|
{% assign problems_list = site.pages | where_exp:'p','p.path contains "/problems/"' %}
{% for p in problems_list %}
| [{{ p.title }}]({{ p.url }}) | {{ p.status | default:"Unknown" }} |
{% endfor %}

---

## About This Project

“Did AI Solve?” tracks major open problems across disciplines—math, physics, biology, etc.—and monitors whether advanced AI systems (like those from OpenAI) have made decisive breakthroughs. We automatically update the status of each problem as news emerges.

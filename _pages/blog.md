---
layout: archive
title: ""
permalink: /blog/
author_profile: true
---

{% include base_path %}
This section contains technical notes on quantitative marine ecology, fisheries science, stock assessment, spatio-temporal modelling, statistical distributions, and reproducible scientific computing. The purpose of this blog is to translate statistical and ecological concepts into practical tools for marine and fisheries research.

## Main Series
- **Quantitative marine ecology**: Marine ecology through data, statistical models, theory, and computational tools.
- **Fisheries and stock dynamics**: Population changes, fishing pressure, productivity, stock status, and fisheries management.
- **Species profiles**: Scientific syntheses of marine species of ecological, commercial, or fisheries interest.
- **Ocean–climate interactions**: Biological and ecological responses to environmental, climatic, and oceanographic variability.
- **Spatial ecology and habitat**: Distribution, habitat, spatial structure, connectivity, and movement patterns of marine resources.
- **Paper review**: Critical discussion of key scientific papers in marine ecology, fisheries science, and ecological modelling.

## Latest technical notes

{% assign posts = site.posts | sort: "date" | reverse %}

{% for post in posts %}
  {% include archive-single.html %}
{% endfor %}

---

## Browse posts

- [Posts by year]({{ base_path }}/year-archive/)
- [Posts by category]({{ base_path }}/categories/)
- [Posts by tag]({{ base_path }}/tags/)
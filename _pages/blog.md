---
layout: archive
title: "Technical Blog"
permalink: /blog/
author_profile: true
---

{% include base_path %}

This section contains technical notes on quantitative marine ecology, fisheries science, stock assessment, spatio-temporal modelling, statistical distributions, and reproducible scientific computing.

The purpose of this blog is to translate statistical and ecological concepts into practical tools for marine and fisheries research.

## Main series

- **Statistical Ecology Notes**  
  Statistical distributions, GLM, GAM, uncertainty, overdispersion, zero inflation, and ecological inference.

- **Fisheries Modelling Lab**  
  CPUE standardization, selectivity, acoustic biomass, stock indicators, recruitment, and fisheries-dependent data.

- **Spatio-temporal Ecology**  
  Species distribution models, spatial random fields, habitat modelling, oceanographic gradients, and ecosystem structure.

- **Marine Ecosystem Indicators**  
  Indicators of stock state, pressure–response relationships, DPSIR, environmental forcing, and ecosystem-based fisheries management.

- **Scientific Computing**  
  R, Python, Julia, GitHub, reproducible workflows, renv, targets, and open science.

---

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
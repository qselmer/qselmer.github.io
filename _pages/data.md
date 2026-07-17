---
layout: archive
title: "Data"
permalink: /data/
author_profile: true
---

{% include base_path %}

This section curates open, registered-access, and research-grade data resources for quantitative marine ecology, fisheries science, stock assessment, species-distribution modelling, and reproducible ocean science. The catalogue prioritizes resources useful for analysing fisheries, acoustic surveys, marine populations, environmental variability, species distributions, oceanographic drivers, climate signals, and human pressures.

The catalogue distinguishes external source data from project-specific derived products. Inclusion does not imply that all datasets are directly redistributed through this website.

{% assign groups = site.data.data_resources | group_by: "category" %}
{% assign open_count = 0 %}
{% assign registered_count = 0 %}
{% assign restricted_count = 0 %}
{% for item in site.data.data_resources %}
  {% if item.access contains "Open" or item.access contains "open" %}{% assign open_count = open_count | plus: 1 %}{% endif %}
  {% if item.access contains "Registered" or item.access contains "registered" %}{% assign registered_count = registered_count | plus: 1 %}{% endif %}
  {% if item.access contains "Restricted" or item.access contains "restricted" or item.access contains "Controlled" or item.access contains "controlled" %}{% assign restricted_count = restricted_count | plus: 1 %}{% endif %}
{% endfor %}

<div class="section-stats" aria-label="Data resource summary">
  <div class="section-stat"><span class="section-stat__value">{{ site.data.data_resources | size }}</span><span class="section-stat__label">catalogued resources</span></div>
  <div class="section-stat"><span class="section-stat__value">{{ groups | size }}</span><span class="section-stat__label">data domains</span></div>
  <div class="section-stat"><span class="section-stat__value">{{ open_count }}</span><span class="section-stat__label">open-access resources</span></div>
  <div class="section-stat"><span class="section-stat__value">{{ registered_count }}</span><span class="section-stat__label">registered-access resources</span></div>
  <div class="section-stat"><span class="section-stat__value">{{ restricted_count }}</span><span class="section-stat__label">restricted or controlled resources</span></div>
</div>

## Data domains

<div class="data-domain-legend" aria-label="Data domains and colours">
{% for group in groups %}
  {% assign domain_number = forloop.index0 | modulo: 6 | plus: 1 %}
  <div class="data-domain-legend__item data-domain--{{ domain_number }}">
    <span class="data-domain-legend__marker" aria-hidden="true"></span>
    <span>{{ group.name }}</span>
    <strong>{{ group.items | size }}</strong>
  </div>
{% endfor %}
</div>

## Access and data governance

Open resources link to their authoritative providers. Registered-access products retain their original access conditions. Restricted fisheries or institutional data will be represented only through metadata, variable dictionaries, processing descriptions, synthetic examples, or non-disclosive derived products when permitted.

## Data catalogue

{% for group in groups %}
{% assign domain_number = forloop.index0 | modulo: 6 | plus: 1 %}
<section class="data-domain-section data-domain--{{ domain_number }}" aria-labelledby="data-domain-{{ forloop.index }}">
  <div class="data-domain-section__header">
    <div>
      <span class="data-domain-section__eyebrow">Data domain</span>
      <h2 id="data-domain-{{ forloop.index }}">{{ group.name }}</h2>
    </div>
    <span class="data-domain-section__count">{{ group.items | size }} resources</span>
  </div>

  <div class="data-card-grid">
  {% for r in group.items %}
    <article class="data-card">
      <div class="data-card__domain">{{ group.name }}</div>
      <h3>{{ r.name }}</h3>
      <div class="data-provider">{{ r.provider }}</div>
      <p>{{ r.description }}</p>

      <div class="data-badges">
        <span class="data-badge">{{ r.access }}</span>
        <span class="data-badge">{{ r.scale }}</span>
        <span class="data-badge">{{ r.format }}</span>
      </div>

      <p class="data-card__use"><strong>Useful for:</strong> {{ r.use_case }}</p>
      <p class="data-card__link"><a href="{{ r.url }}" target="_blank" rel="noopener">Open authoritative resource</a></p>
    </article>
  {% endfor %}
  </div>
</section>
{% endfor %}

## Project data products

Public derived datasets, metadata records, processing scripts, and archived releases will be added when their documentation, access rights, citation information, and quality-control status are complete. See [Reproducible marine data systems](/projects/reproducible-marine-data-systems/) for the analytical framework connecting these resources.

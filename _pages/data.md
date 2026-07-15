---
layout: archive
title: "Data"
permalink: /data/
author_profile: true
---

{% include base_path %}

This section curates open, registered-access, and research-grade data resources for quantitative marine ecology, fisheries science, stock assessment, species-distribution modelling, and reproducible ocean science. The catalogue prioritizes resources useful for analysing fisheries, acoustic surveys, marine populations, environmental variability, species distributions, oceanographic drivers, climate signals, and human pressures.

The catalogue distinguishes external source data from project-specific derived products. Inclusion does not imply that all datasets are directly redistributed through this website.

## Data domains

- Fisheries and fishing activity.
- Acoustic, biological, and survey observations.
- Physical and biogeochemical oceanography.
- Satellite and climate products.
- Biodiversity and species occurrences.
- Bathymetry and geospatial layers.

## Access and data governance

Open resources link to their authoritative providers. Registered-access products retain their original access conditions. Restricted fisheries or institutional data will be represented only through metadata, variable dictionaries, processing descriptions, synthetic examples, or non-disclosive derived products when permitted.

<style>
.data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.data-card {
  border: 1px solid #ddd;
  border-radius: 10px;
  padding: 1rem;
  background: var(--global-bg-color, #fff);
}

.data-card h3 {
  margin-top: 0;
  margin-bottom: 0.25rem;
}

.data-provider {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.data-badges {
  margin: 0.5rem 0;
}

.data-badge {
  display: inline-block;
  border: 1px solid #aaa;
  border-radius: 999px;
  padding: 0.15rem 0.5rem;
  font-size: 0.75rem;
  margin-right: 0.25rem;
  margin-bottom: 0.25rem;
}

.data-card a {
  font-weight: 600;
}
</style>

## Data catalogue

{% assign groups = site.data.data_resources | group_by: "category" %}

{% for group in groups %}

## {{ group.name }}

<div class="data-grid">
{% for r in group.items %}
  <div class="data-card">
    <h3>{{ r.name }}</h3>
    <div class="data-provider">{{ r.provider }}</div>
    <p>{{ r.description }}</p>

    <div class="data-badges">
      <span class="data-badge">{{ r.access }}</span>
      <span class="data-badge">{{ r.scale }}</span>
      <span class="data-badge">{{ r.format }}</span>
    </div>

    <p><strong>Useful for:</strong> {{ r.use_case }}</p>

    <p><a href="{{ r.url }}" target="_blank" rel="noopener">Open authoritative resource</a></p>
  </div>
{% endfor %}
</div>

{% endfor %}

## Project data products

Public derived datasets, metadata records, processing scripts, and archived releases will be added when their documentation, access rights, citation information, and quality-control status are complete. See [Reproducible marine data systems](/projects/reproducible-marine-data-systems/) for the analytical framework connecting these resources.
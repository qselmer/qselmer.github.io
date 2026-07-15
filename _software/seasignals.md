---
title: "seasignals"
collection: software
permalink: /software/seasignals/
date: 2026-07-15
status: development
featured: true
excerpt: "An R package for representing the phase, magnitude, and temporal structure of large-scale ocean–climate signals in marine ecological analyses."
tags:
  - R package
  - climate variability
  - ENSO
  - time series
---

## Purpose

`seasignals` is being developed to support reproducible representation of large-scale ocean–climate variability in marine ecological and fisheries analyses. Its initial focus is on converting climate indices into interpretable descriptors of phase, magnitude, persistence, and transition.

## Scientific problem

Marine populations may respond differently to weak, moderate, and extreme environmental conditions, and those responses can depend on whether the system is entering, persisting in, or leaving a climate phase. Analyses based only on raw index values may not represent that temporal structure explicitly.

## Planned capabilities

- Classify climate phases using transparent and reproducible rules.
- Quantify event magnitude and persistence.
- Detect transitions among warm, neutral, and cold conditions.
- Generate analysis-ready time-series features for ecological models.
- Support sensitivity analysis for alternative thresholds and definitions.
- Produce standardized summaries and visual diagnostics.

## Intended applications

- ENSO and coastal ocean variability.
- Recruitment and population-dynamics studies.
- Habitat and species-distribution models.
- Pressure–state and threshold analyses.
- Fisheries and ecosystem indicators.

## Development status

**Active development.** The package structure, functions, documentation, testing framework, and public repository are being prepared. A stable release, license, citation file, and versioned documentation will be added when the package is ready for external use.

## Reproducibility principles

The package is intended to use explicit definitions, documented assumptions, unit tests, versioned releases, and examples based on public or synthetic data.

## Related work

See [Environmental variability and ecosystem responses](/research/) and [Reproducible marine data systems](/projects/reproducible-marine-data-systems/).
---
title: "oceancube"
collection: software
permalink: /software/oceancube/
date: 2026-07-14
status: development
featured: true
excerpt: "A reproducible framework for downloading, harmonizing, subsetting, and organizing multidimensional marine environmental data for ecological analysis."
tags:
  - ocean data
  - CMEMS
  - reproducible workflows
  - spatio-temporal analysis
---

## Purpose

`oceancube` is being developed as a reproducible framework for acquiring, harmonizing, and organizing multidimensional oceanographic data used in marine ecology and fisheries science.

## Scientific problem

Environmental products often differ in spatial resolution, temporal coverage, depth structure, coordinate conventions, file formats, variable names, units, and missing-value definitions. These inconsistencies can make analyses difficult to reproduce and can introduce avoidable processing errors.

## Planned capabilities

- Download or register marine environmental products from supported sources.
- Standardize coordinates, dates, depth dimensions, units, and variable names.
- Subset data by area, time period, depth range, and variable.
- Aggregate daily and monthly products using explicit rules.
- Build analysis-ready raster, array, and tabular outputs.
- Record provenance, processing history, and quality-control results.
- Support extraction at survey stations, fishing sets, spatial grids, and polygons.

## Intended applications

- Habitat and species-distribution modelling.
- Spatio-temporal fisheries analysis.
- Environmental characterization of acoustic surveys.
- Climate and ecosystem indicators.
- Integration of physical and biogeochemical products.
- Reproducible preparation of CMEMS and satellite data.

## Development status

**Active development.** Core workflows are being organized around repeatable acquisition, preprocessing, validation, and export steps. Public documentation, tests, a stable license, and versioned releases will be added before external distribution.

## Data principles

`oceancube` will not redistribute restricted source data. It is intended to preserve source attribution, product identifiers, access conditions, variable metadata, and reproducible processing instructions.

## Related work

See [Reproducible marine data systems](/projects/reproducible-marine-data-systems/) and the [Data catalogue](/data/).
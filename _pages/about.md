---
permalink: /
title: "Quantitative Marine Ecology for Fisheries and Ecosystems"
bio: "Marine quantitative ecologist and fisheries scientist working across observations, data, models, and decision-relevant evidence."
excerpt: "Quantitative marine ecology, fisheries science, stock assessment, spatio-temporal modelling, and reproducible scientific computing."
author_profile: true
layout: homepage
redirect_from:
  - /about/
  - /about.html
  - /now/
  - /now.html
---
{% include base_path %}

<style>
.home-intro {
  font-size: 1.08rem;
  line-height: 1.75;
  margin-bottom: 2rem;
}

.home-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin: 1.5rem 0 2.5rem;
}

.home-actions a {
  display: inline-block;
  padding: 0.65rem 1rem;
  border: 1px solid rgba(120, 190, 220, 0.5);
  border-radius: 0.45rem;
  text-decoration: none;
  font-weight: 600;
}

.home-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin: 1rem 0 2.5rem;
}

.home-card {
  padding: 1.1rem;
  border: 1px solid rgba(130, 180, 205, 0.28);
  border-radius: 0.7rem;
  background: rgba(10, 30, 42, 0.32);
}

.home-card h3 {
  margin-top: 0;
  margin-bottom: 0.55rem;
  font-size: 1.05rem;
}

.home-card p {
  margin-bottom: 0.65rem;
}

.home-card a {
  font-weight: 600;
}

.home-output {
  padding: 1rem 0;
  border-bottom: 1px solid rgba(130, 180, 205, 0.24);
}

.home-output:last-child {
  border-bottom: 0;
}

.home-kicker {
  margin-bottom: 0.4rem;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.76;
}

.home-collaboration {
  margin-top: 2.5rem;
  padding: 1.25rem;
  border-left: 4px solid rgba(80, 180, 220, 0.8);
  background: rgba(10, 30, 42, 0.32);
}

@media (max-width: 600px) {
  .home-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .home-actions a {
    text-align: center;
  }
}
</style>

<div class="home-intro">
<p>I study how marine populations and fisheries respond to environmental variability, fishing pressure, and ecosystem change. My work integrates ecological theory, biological and fisheries observations, oceanographic information, statistical modelling, and reproducible scientific computing.</p>

<p>My main study system is the Humboldt Current System, with particular emphasis on the north-central stock of Peruvian anchovy (<em>Engraulis ringens</em>). I also work on pelagic fisheries, fleet dynamics, multivariate stock indicators, and spatio-temporal analysis.</p>
</div>

<div class="home-actions">
  <a href="{{ base_path }}/research/">Research programme</a>
  <a href="{{ base_path }}/projects/">Current projects</a>
  <a href="{{ base_path }}/publications/">Publications</a>
  <a href="{{ base_path }}/talks/">Conferences</a>
  <a href="{{ base_path }}/cv/">View CV</a>
</div>

## Current work

<div class="home-grid current-work-grid">
  <div class="home-card current-work-card">
    <div class="home-kicker">Active · Manuscript development</div>
    <h3>Multidimensional assessment of the north-central Peruvian anchovy stock</h3>
    <p>Integrating population magnitude, condition, reproduction, demographic structure, spatial distribution, and pressure–state relationships.</p>
    <a href="{{ base_path }}/projects/anchovy-stock-state/">View current project</a>
  </div>

  <div class="home-card current-work-card">
    <div class="home-kicker">Active · Analysis and manuscript preparation</div>
    <h3>Selectivity and demographic change in the anchovy fishery</h3>
    <p>Evaluating long-term and seasonal changes in length selectivity, selection range, juvenile incidence, and demographic structure.</p>
    <a href="{{ base_path }}/projects/anchovy-selectivity/">View current project</a>
  </div>

  <div class="home-card current-work-card">
    <div class="home-kicker">Active · Data standardization and modelling</div>
    <h3>Peruvian tuna purse-seine fishery</h3>
    <p>Characterizing catch, effort, fishing modes, species composition, standardized CPUE, and environmental associations.</p>
    <a href="{{ base_path }}/projects/tuna-fishery/">View current project</a>
  </div>
</div>

## Research themes

<div class="home-grid">
  <div class="home-card">
    <h3>Fisheries population dynamics</h3>
    <p>Stock assessment, growth, recruitment, selectivity, demographic structure, indicators, uncertainty, and adaptive management.</p>
    <a href="{{ base_path }}/research/">Explore research</a>
  </div>

  <div class="home-card">
    <h3>Spatio-temporal marine ecology</h3>
    <p>Distribution shifts, habitat, accessibility, hotspots, fishing-fleet behaviour, and spatially explicit population and fishery models.</p>
    <a href="{{ base_path }}/research/">Explore research</a>
  </div>

  <div class="home-card">
    <h3>Environmental variability</h3>
    <p>Responses of marine populations to climate, oceanographic variability, productivity, oxygen, upwelling, and ecosystem regimes.</p>
    <a href="{{ base_path }}/research/">Explore research</a>
  </div>

  <div class="home-card">
    <h3>Statistical ecology and computing</h3>
    <p>Hierarchical, additive, mixed, Bayesian, multivariate, and machine-learning methods implemented through reproducible workflows.</p>
    <a href="{{ base_path }}/resources/">Explore tools and data</a>
  </div>
</div>

## Selected publication

<div class="home-output publication-output">
  <div class="home-kicker">Peer-reviewed article · Scientia Marina</div>
  <h3><a href="{{ base_path }}/publication/2025-12-01-gsi-ml-maturity-anchovy/">Classification models based on the gonadosomatic index to determine gonadal maturity stages</a></h3>
  <p>Machine-learning classification of reproductive maturity stages in Peruvian anchovy and harmonization of historical biological records.</p>
</div>

<p><a href="{{ base_path }}/publications/"><strong>View full publication record →</strong></a></p>

## Selected conferences and presentations

<div class="home-grid conference-feature-grid">
  <div class="home-card conference-feature-card">
    <div class="home-kicker">Oral presentation · SPF-2026</div>
    <h3>Multivariate Health Index of the anchovy</h3>
    <p>A multidimensional framework for understanding stock condition under strong environmental variability.</p>
    <a href="{{ base_path }}/talks/">View conference record</a>
  </div>

  <div class="home-card conference-feature-card">
    <div class="home-kicker">Poster presentation · SPF-2026</div>
    <h3>Critical points of natural and anthropogenic pressures and stock-state responses</h3>
    <p>A threshold-oriented diagnostic framework for pressure–state relationships in the north-central Peruvian anchovy stock.</p>
    <a href="{{ base_path }}/talks/2026-05-08-critical-points-anchovy-stock/">View poster record</a>
  </div>
</div>

<p><a href="{{ base_path }}/talks/"><strong>View all conferences and presentations →</strong></a></p>

## Software and data systems

<div class="home-grid">
  <div class="home-card">
    <div class="home-kicker">R package · Development</div>
    <h3><code>seasignals</code></h3>
    <p>Representing climate phase, magnitude, persistence, and transitions for marine ecological analyses.</p>
    <a href="{{ base_path }}/software/seasignals/">View software record</a>
  </div>

  <div class="home-card">
    <div class="home-kicker">Data framework · Development</div>
    <h3><code>oceancube</code></h3>
    <p>Acquiring, harmonizing, subsetting, validating, and organizing multidimensional marine environmental data.</p>
    <a href="{{ base_path }}/software/oceancube/">View software record</a>
  </div>

  <div class="home-card">
    <div class="home-kicker">Analytics platform · Concept development</div>
    <h3>Pelagytics</h3>
    <p>Connecting fisheries, biological, environmental, and spatial information through reproducible indicators and decision-support products.</p>
    <a href="{{ base_path }}/software/pelagytics/">View software record</a>
  </div>
</div>

<p><a href="{{ base_path }}/resources/"><strong>Explore Software &amp; Data →</strong></a></p>

<div class="home-collaboration">
<h2>Collaboration</h2>
<p>I am open to academic and technical collaboration in quantitative marine ecology, fisheries science, stock assessment, spatio-temporal modelling, statistical ecology, scientific software, and reproducible data systems.</p>
<p><a href="{{ base_path }}/contact/"><strong>Contact me</strong></a> · <a href="{{ base_path }}/services/"><strong>Collaboration &amp; Consulting</strong></a> · <a href="https://github.com/qselmer"><strong>GitHub</strong></a></p>
</div>

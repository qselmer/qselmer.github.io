---
permalink: /
title: "Quantitative marine ecology for fisheries and ecosystems"
excerpt: "Quantitative marine ecology, fisheries science, stock assessment, spatio-temporal modelling, and reproducible scientific computing."
profile_title: "Marine quantitative ecologist"
profile_specializations:
  - "Fisheries science and stock assessment"
  - "Spatio-temporal modelling and scientific computing"
author_profile: true
layout: homepage
redirect_from:
  - /about/
  - /about.html
  - /now/
  - /now.html
---
{% include base_path %}

<div class="home-intro">
  <p>I study how marine populations and fisheries respond to environmental variability, fishing pressure, and ecosystem change. My work combines ecological theory, biological and fisheries observations, oceanographic information, statistical modelling, and reproducible scientific computing.</p>
  <p>My main study system is the Humboldt Current System, with particular emphasis on the north-central stock of Peruvian anchovy (<em>Engraulis ringens</em>). I also work on pelagic fisheries, fleet dynamics, multivariate stock indicators, and spatio-temporal analysis.</p>
</div>

<section class="home-section home-section--flow" aria-labelledby="scientific-flow-heading">
  <h2 id="scientific-flow-heading">Scientific workflow</h2>
  <ol class="science-flow" aria-label="Scientific workflow from observations to decision support">
    <li>Observations</li>
    <li>Data</li>
    <li>Models</li>
    <li>Decision support</li>
  </ol>
</section>

<section class="home-section" aria-labelledby="research-programme-heading">
  <div class="home-section__heading">
    <h2 id="research-programme-heading">Research programme</h2>
    <a href="{{ base_path }}/research/">Explore the research programme</a>
  </div>

  <div class="research-programme-grid">
    <a class="home-navigable-card" href="{{ base_path }}/research/">
      <h3>Fisheries population dynamics and stock assessment</h3>
      <p>Population dynamics, stock indicators, growth, recruitment, selectivity, demographic structure, uncertainty, and adaptive assessment.</p>
    </a>
    <a class="home-navigable-card" href="{{ base_path }}/research/">
      <h3>Spatio-temporal marine ecology</h3>
      <p>Distribution shifts, habitat, accessibility, hotspots, fleet behaviour, and spatially explicit population and fishery models.</p>
    </a>
    <a class="home-navigable-card" href="{{ base_path }}/research/">
      <h3>Environmental variability and ecosystem responses</h3>
      <p>Responses to climate and oceanographic variability, productivity, oxygen, upwelling, habitat conditions, and ecosystem regimes.</p>
    </a>
    <a class="home-navigable-card" href="{{ base_path }}/research/">
      <h3>Statistical ecology and scientific computing</h3>
      <p>Hierarchical, additive, mixed, Bayesian, multivariate, and machine-learning methods in reproducible analytical workflows.</p>
    </a>
  </div>
</section>

{% assign current_projects = site.projects | where: "featured", true | sort: "date" | reverse %}
<section class="home-section" aria-labelledby="current-work-heading">
  <div class="home-section__heading">
    <h2 id="current-work-heading">Current work</h2>
    <a href="{{ base_path }}/projects/">View all projects</a>
  </div>

  <div class="current-work-grid">
    {% for project in current_projects limit: 3 %}
      <a class="home-navigable-card home-project-card" href="{{ project.url | relative_url }}">
        <span class="home-status">{{ project.status | capitalize }}</span>
        <h3>{{ project.title }}</h3>
        <span class="home-card-link">View project</span>
      </a>
    {% endfor %}
  </div>
</section>

{% assign selected_publications = site.publications | where_exp: "item", "item.category != 'conference'" | sort: "date" | reverse %}
{% assign selected_talks = site.talks | sort: "date" | reverse %}
<section class="home-section" aria-labelledby="selected-outputs-heading">
  <h2 id="selected-outputs-heading">Selected outputs</h2>

  <div class="selected-output-grid">
    <section class="selected-output-column" aria-labelledby="selected-publications-heading">
      <div class="selected-output-column__heading">
        <h3 id="selected-publications-heading">Selected publications</h3>
        <a href="{{ base_path }}/publications/">All publications</a>
      </div>
      {% for publication in selected_publications limit: 1 %}
        <article class="selected-output">
          <p class="selected-output__meta">{{ publication.date | date: "%Y" }}{% if publication.venue %} · {{ publication.venue }}{% endif %}</p>
          <h4><a href="{{ publication.url | relative_url }}">{{ publication.title }}</a></h4>
          {% if publication.excerpt %}<p>{{ publication.excerpt }}</p>{% endif %}
        </article>
      {% endfor %}
    </section>

    <section class="selected-output-column" aria-labelledby="selected-conferences-heading">
      <div class="selected-output-column__heading">
        <h3 id="selected-conferences-heading">Selected conferences and presentations</h3>
        <a href="{{ base_path }}/talks/">All conferences</a>
      </div>
      {% for talk in selected_talks limit: 1 %}
        <article class="selected-output">
          <p class="selected-output__meta">{{ talk.date | date: "%Y" }}{% if talk.type %} · {{ talk.type }}{% endif %}</p>
          <h4><a href="{{ talk.url | relative_url }}">{{ talk.title }}</a></h4>
          {% if talk.excerpt %}<p>{{ talk.excerpt }}</p>{% endif %}
        </article>
      {% endfor %}
    </section>
  </div>
</section>

<section class="home-section" aria-labelledby="scientific-products-heading">
  <div class="home-section__heading">
    <h2 id="scientific-products-heading">Scientific products</h2>
  </div>

  <div class="scientific-products-grid">
    <a class="home-navigable-card" href="{{ base_path }}/software/">
      <h3>Software</h3>
      <p>Scientific tools and analytical frameworks for fisheries, marine ecology, environmental analysis, and reproducible computing.</p>
    </a>
    <a class="home-navigable-card" href="{{ base_path }}/data/">
      <h3>Data resources</h3>
      <p>Curated sources for fisheries, acoustic surveys, marine populations, oceanographic drivers, climate signals, and human pressures.</p>
    </a>
    <a class="home-navigable-card" href="{{ base_path }}/projects/reproducible-marine-data-systems/">
      <h3>Reproducible workflows</h3>
      <p>Traceable systems for acquiring, harmonizing, documenting, analysing, and updating fisheries and oceanographic data.</p>
    </a>
  </div>
</section>

<section class="home-section home-collaboration" aria-labelledby="collaboration-heading">
  <h2 id="collaboration-heading">Collaboration</h2>
  <p>I am open to academic and technical collaboration in quantitative marine ecology, fisheries science, stock assessment, spatio-temporal modelling, scientific software, and reproducible data systems.</p>
  <p class="home-inline-links"><a href="{{ base_path }}/contact/">Contact</a><span aria-hidden="true">·</span><a href="{{ base_path }}/services/">Collaboration and consulting</a><span aria-hidden="true">·</span><a href="https://github.com/qselmer">GitHub</a></p>
</section>

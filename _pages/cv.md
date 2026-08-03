---
layout: single
title: "CV"
permalink: /cv/
author_profile: false
classes: wide
redirect_from:
  - /resume
---

<div class="cv-page">
  <div class="cv-header">
    <div>
      <p class="cv-kicker">Curriculum vitae</p>
      <h1>Elmer O. Quispe-Salazar</h1>
      <p class="cv-subtitle">Quantitative biologist in marine ecology and fisheries</p>
    </div>

    <div class="cv-actions" aria-label="Curriculum vitae actions">
      <a class="btn btn--primary" href="/files/CV.pdf" target="_blank" rel="noopener">
        Open PDF
      </a>
      <a class="btn" href="/files/CV.pdf" download>
        Download PDF
      </a>
    </div>
  </div>

  <p class="cv-summary">
    The complete CV documents education, research experience, peer-reviewed and technical
    publications, conference contributions, awards, teaching, and specialized training in
    fisheries science, quantitative marine ecology, statistical modelling, scientific
    programming, and geospatial analysis.
  </p>

  <div class="cv-viewer" aria-label="Embedded curriculum vitae">
    <object
      data="/files/CV.pdf#view=FitH&toolbar=1&navpanes=0"
      type="application/pdf"
      width="100%"
      height="100%">
      <p>
        The embedded PDF viewer is not available in this browser.
        <a href="/files/CV.pdf" target="_blank" rel="noopener">Open the CV as a PDF</a>.
      </p>
    </object>
  </div>

  <noscript>
    <p><a href="/files/CV.pdf">Open or download the curriculum vitae</a>.</p>
  </noscript>
</div>

<style>
.cv-page {
  width: 100%;
  max-width: 1500px;
  margin: 0 auto;
}

.cv-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.cv-header h1 {
  margin: 0.1rem 0 0.25rem;
  font-size: clamp(1.8rem, 4vw, 3rem);
  line-height: 1.05;
}

.cv-kicker {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  opacity: 0.72;
}

.cv-subtitle,
.cv-summary {
  margin: 0;
  opacity: 0.82;
}

.cv-summary {
  max-width: 950px;
  margin-bottom: 1rem;
}

.cv-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  flex: 0 0 auto;
}

.cv-viewer {
  width: 100%;
  height: calc(100vh - 12.5rem);
  min-height: 720px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: #202124;
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.25);
}

.cv-viewer object {
  display: block;
  border: 0;
}

@media (max-width: 760px) {
  .cv-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .cv-viewer {
    height: 78vh;
    min-height: 560px;
  }
}
</style>

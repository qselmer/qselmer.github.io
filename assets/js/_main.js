/* Site behavior and deferred visual integrations. */
/*jslint es6 */
'use strict';

const PLOTLY_URL = 'https://cdn.jsdelivr.net/npm/plotly.js@3.6.0/dist/plotly.min.js';
const MERMAID_URL = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
const PLOTLY_LIGHT_TEMPLATE = {
  layout: {
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#ffffff',
    font: { color: '#243b4a' },
    colorway: ['#0e7490', '#2563eb', '#c2410c', '#7c3aed', '#15803d']
  }
};

let plotlyReady = null;

function loadScriptOnce(url, id) {
  const existing = document.getElementById(id);

  if (existing) {
    return new Promise(function (resolve, reject) {
      if (existing.dataset.loaded === 'true') {
        resolve();
        return;
      }
      existing.addEventListener('load', resolve, { once: true });
      existing.addEventListener('error', reject, { once: true });
    });
  }

  return new Promise(function (resolve, reject) {
    const script = document.createElement('script');
    script.id = id;
    script.src = url;
    script.async = true;
    script.addEventListener('load', function () {
      script.dataset.loaded = 'true';
      resolve();
    }, { once: true });
    script.addEventListener('error', reject, { once: true });
    document.head.appendChild(script);
  });
}

function renderPlotlyElement(element) {
  let jsonData;

  try {
    jsonData = JSON.parse(element.textContent);
  } catch (error) {
    console.error('Invalid Plotly JSON:', error);
    return;
  }

  element.parentElement.classList.add('hidden');
  let chartElement = element.parentElement.nextElementSibling;

  if (!chartElement || !chartElement.classList.contains('plotly-chart')) {
    chartElement = document.createElement('div');
    chartElement.className = 'plotly-chart';
    element.parentElement.after(chartElement);
  }

  jsonData.layout = jsonData.layout || {};
  jsonData.layout.template = jsonData.layout.template
    ? { ...PLOTLY_LIGHT_TEMPLATE, ...jsonData.layout.template }
    : PLOTLY_LIGHT_TEMPLATE;

  window.Plotly.react(
    chartElement,
    jsonData.data || [],
    jsonData.layout,
    { responsive: true, displaylogo: false }
  );
}

function initializePlotly() {
  const plotlyElements = document.querySelectorAll('pre > code.language-plotly');

  if (plotlyElements.length === 0) {
    return;
  }

  if (!plotlyReady) {
    plotlyReady = loadScriptOnce(PLOTLY_URL, 'plotly-library')
      .then(function () {
        plotlyElements.forEach(renderPlotlyElement);
      })
      .catch(function (error) {
        console.error('Plotly could not be loaded:', error);
      });
  }
}

function initializeMermaid() {
  if (!document.querySelector('pre > code.language-mermaid')) {
    return;
  }

  const moduleScript = document.createElement('script');
  moduleScript.type = 'module';
  moduleScript.textContent = `
    import mermaid from '${MERMAID_URL}';
    mermaid.initialize({ startOnLoad: false, theme: 'default' });
    await mermaid.run({ querySelector: 'code.language-mermaid' });
  `;
  document.body.appendChild(moduleScript);
}

function initializeSmoothAnchors() {
  document.addEventListener('click', function (event) {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }

    const link = event.target.closest('a[href^="#"]');
    if (!link || !link.hash) {
      return;
    }

    let target;
    try {
      target = document.querySelector(link.hash);
    } catch (error) {
      return;
    }

    if (!target) {
      return;
    }

    event.preventDefault();
    const masthead = document.querySelector('.masthead');
    const offset = masthead ? masthead.getBoundingClientRect().height + 12 : 12;
    const top = window.scrollY + target.getBoundingClientRect().top - offset;
    const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    window.scrollTo({ top: top, behavior: reduceMotion ? 'auto' : 'smooth' });
    window.history.pushState(null, '', link.hash);
  });
}

function initializeAuthorLinks() {
  const button = document.querySelector('.author__urls-wrapper button');
  const links = document.getElementById('author-links');

  if (!button || !links) {
    return;
  }

  button.addEventListener('click', function () {
    const expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!expanded));
    links.setAttribute('aria-hidden', String(expanded));
    $(links).stop(true, true).fadeToggle('fast');
    button.classList.toggle('open', !expanded);
  });

  window.addEventListener('resize', function () {
    if (window.matchMedia('(min-width: 64rem)').matches) {
      links.removeAttribute('style');
      links.setAttribute('aria-hidden', 'false');
      button.setAttribute('aria-expanded', 'true');
    } else if (!button.classList.contains('open')) {
      links.setAttribute('aria-hidden', 'true');
      button.setAttribute('aria-expanded', 'false');
    }
  });
}

$(document).ready(function () {
  initializeAuthorLinks();
  initializeSmoothAnchors();
  initializePlotly();
  initializeMermaid();
});

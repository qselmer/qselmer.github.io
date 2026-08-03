/* ==========================================================================
   Site behavior and deferred visual integrations
   ========================================================================== */

/*jslint es6 */
'use strict';

const PLOTLY_URL = 'https://cdn.jsdelivr.net/npm/plotly.js@3.6.0/dist/plotly.min.js';
const MERMAID_URL = 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
const THEME_SEQUENCE = ['auto', 'light', 'dark'];
const browserThemeQuery = window.matchMedia
  ? window.matchMedia('(prefers-color-scheme: dark)')
  : null;

let plotlyElements = document.querySelectorAll('pre > code.language-plotly');
let plotlyReady = null;

function normalizeThemeSetting(value) {
  return THEME_SEQUENCE.includes(value) ? value : 'auto';
}

function getThemeSetting() {
  return normalizeThemeSetting(localStorage.getItem('theme'));
}

function determineComputedTheme(setting) {
  const normalized = normalizeThemeSetting(setting || getThemeSetting());

  if (normalized !== 'auto') {
    return normalized;
  }

  return browserThemeQuery && browserThemeQuery.matches ? 'dark' : 'light';
}

function updateThemeIcon(setting) {
  const normalized = normalizeThemeSetting(setting);
  const icon = $('#theme-icon');
  const labels = {
    auto: 'Theme follows system settings',
    light: 'Light theme enabled',
    dark: 'Dark theme enabled'
  };

  icon.removeClass('fa-sun fa-moon fa-desktop');

  if (normalized === 'dark') {
    icon.addClass('fa-moon');
  } else if (normalized === 'light') {
    icon.addClass('fa-sun');
  } else {
    icon.addClass('fa-desktop');
  }

  icon.attr('title', labels[normalized]);
  $('#theme-toggle a').attr('aria-label', labels[normalized]);
}

function setTheme(setting) {
  const normalized = normalizeThemeSetting(setting || getThemeSetting());
  const computed = determineComputedTheme(normalized);

  if (computed === 'dark') {
    $('html').attr('data-theme', 'dark');
  } else {
    $('html').removeAttr('data-theme');
  }

  updateThemeIcon(normalized);
}

function toggleTheme() {
  const current = getThemeSetting();
  const nextIndex = (THEME_SEQUENCE.indexOf(current) + 1) % THEME_SEQUENCE.length;
  const next = THEME_SEQUENCE[nextIndex];

  localStorage.setItem('theme', next);
  setTheme(next);
  redrawPlotly();
}

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

function applyPlotlyTheme(jsonData) {
  const template = determineComputedTheme() === 'dark'
    ? plotlyDarkLayout
    : plotlyLightLayout;

  if (!jsonData.layout) {
    jsonData.layout = {};
  }

  jsonData.layout.template = jsonData.layout.template
    ? { ...template, ...jsonData.layout.template }
    : template;

  return jsonData;
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

  jsonData = applyPlotlyTheme(jsonData);
  window.Plotly.react(
    chartElement,
    jsonData.data || [],
    jsonData.layout,
    { responsive: true, displaylogo: false }
  );
}

function initializePlotly() {
  if (plotlyElements.length === 0) {
    return Promise.resolve();
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

  return plotlyReady;
}

function redrawPlotly() {
  if (plotlyElements.length === 0 || typeof window.Plotly === 'undefined') {
    return;
  }

  plotlyElements.forEach(renderPlotlyElement);
}

function initializeMermaid() {
  const mermaidElements = document.querySelectorAll('pre > code.language-mermaid');

  if (mermaidElements.length === 0) {
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
    if (!link) {
      return;
    }

    const hash = link.getAttribute('href');
    if (!hash || hash === '#') {
      return;
    }

    let target;
    try {
      target = document.querySelector(hash);
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

    window.scrollTo({ top: top, behavior: 'smooth' });
    window.history.pushState(null, '', hash);
  });
}

$(document).ready(function () {
  const scssLarge = 925;

  setTheme();
  $('#theme-toggle').on('click', toggleTheme);

  if (browserThemeQuery) {
    const handleBrowserThemeChange = function () {
      if (getThemeSetting() === 'auto') {
        setTheme('auto');
        redrawPlotly();
      }
    };

    if (browserThemeQuery.addEventListener) {
      browserThemeQuery.addEventListener('change', handleBrowserThemeChange);
    } else if (browserThemeQuery.addListener) {
      browserThemeQuery.addListener(handleBrowserThemeChange);
    }
  }

  $('.author__urls-wrapper button').on('click', function () {
    $('.author__urls').fadeToggle('fast');
    $('.author__urls-wrapper button').toggleClass('open');
  });

  $(window).on('resize', function () {
    if ($('.author__urls.social-icons').css('display') === 'none' && $(window).width() >= scssLarge) {
      $('.author__urls').css('display', 'block');
    }
  });

  initializeSmoothAnchors();
  initializePlotly();
  initializeMermaid();
});

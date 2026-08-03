'use strict';

const { chromium } = require('playwright');

const BASE_URL = process.env.SITE_URL || 'http://127.0.0.1:4173';
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const paths = ['/', '/research/', '/projects/', '/publications/', '/talks/', '/software/', '/teaching/', '/data/', '/blog/', '/cv/', '/contact/'];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function inspectPage(page, path) {
  await page.goto(BASE_URL + path, { waitUntil: 'networkidle' });
  const result = await page.evaluate(() => {
    const duplicateIds = Object.entries(
      [...document.querySelectorAll('[id]')].reduce((counts, element) => {
        counts[element.id] = (counts[element.id] || 0) + 1;
        return counts;
      }, {})
    ).filter(([, count]) => count > 1).map(([id]) => id);

    const unnamedButtons = [...document.querySelectorAll('button')]
      .filter((button) => !((button.getAttribute('aria-label') || button.title || button.textContent).trim()))
      .length;
    const imagesWithoutAlt = [...document.images].filter((image) => !image.hasAttribute('alt')).length;
    const sidebar = document.querySelector('.sidebar');
    const sidebarStyle = sidebar ? getComputedStyle(sidebar) : null;

    let whiteOnWhite = 0;
    for (const element of document.querySelectorAll('body *')) {
      const text = [...element.childNodes].some((node) => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
      if (!text) continue;
      const style = getComputedStyle(element);
      if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) continue;
      let background = style.backgroundColor;
      let ancestor = element.parentElement;
      while (background === 'rgba(0, 0, 0, 0)' && ancestor) {
        background = getComputedStyle(ancestor).backgroundColor;
        ancestor = ancestor.parentElement;
      }
      if (style.color === 'rgb(255, 255, 255)' && background === 'rgb(255, 255, 255)') whiteOnWhite += 1;
    }

    return {
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      duplicateIds,
      unnamedButtons,
      imagesWithoutAlt,
      sidebarPosition: sidebarStyle && sidebarStyle.position,
      sidebarOverflow: sidebarStyle && sidebarStyle.overflowY,
      whiteOnWhite
    };
  });

  assert(result.overflow <= 1, `${path}: horizontal overflow ${result.overflow}px`);
  assert(result.duplicateIds.length === 0, `${path}: duplicate IDs ${result.duplicateIds.join(', ')}`);
  assert(result.unnamedButtons === 0, `${path}: ${result.unnamedButtons} unnamed buttons`);
  assert(result.imagesWithoutAlt === 0, `${path}: ${result.imagesWithoutAlt} images without alt`);
  assert(!['sticky', 'fixed'].includes(result.sidebarPosition), `${path}: sidebar is ${result.sidebarPosition}`);
  assert(!['auto', 'scroll'].includes(result.sidebarOverflow), `${path}: sidebar overflow-y is ${result.sidebarOverflow}`);
  assert(result.whiteOnWhite === 0, `${path}: ${result.whiteOnWhite} white-on-white text nodes`);
}

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: CHROME });
  try {
    const desktop = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    for (const path of paths) await inspectPage(desktop, path);
    const desktopNav = await desktop.goto(BASE_URL + '/', { waitUntil: 'networkidle' }).then(() => desktop.evaluate(() => ({
      hiddenCount: document.querySelectorAll('#site-nav-hidden > li').length,
      buttonHidden: document.querySelector('#site-nav button').classList.contains('hidden'),
      cellCount: [...document.querySelectorAll('.visible-links > li')].filter((item) => getComputedStyle(item).display === 'table-cell').length,
      itemCount: document.querySelectorAll('.visible-links > li').length
    })));
    assert(desktopNav.hiddenCount === 0, 'desktop: navigation items remain hidden');
    assert(desktopNav.buttonHidden, 'desktop: overflow menu button remains visible');
    assert(desktopNav.cellCount === desktopNav.itemCount, 'desktop: navigation is not horizontal');
    await desktop.close();

    const mobile = await browser.newPage({ viewport: { width: 375, height: 812 } });
    await inspectPage(mobile, '/');
    const menuButton = mobile.locator('#site-nav button');
    await menuButton.click();
    assert(await menuButton.getAttribute('aria-expanded') === 'true', 'mobile: menu did not expose expanded state');
    assert(await mobile.locator('#site-nav-hidden').getAttribute('aria-hidden') === 'false', 'mobile: hidden links remain aria-hidden');
    await menuButton.click();
    assert(await menuButton.getAttribute('aria-expanded') === 'false', 'mobile: menu did not close');
    await mobile.close();

    console.log(`Responsive validation passed: ${paths.length} desktop pages and mobile navigation checked`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});

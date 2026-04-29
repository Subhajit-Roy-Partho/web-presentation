const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const outDir = path.join(__dirname, 'review', 'slides_new');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 720 });

  // Serve via file URL - use slide 1 hash to start
  const fileUrl = `file://${path.join(__dirname, 'index.html')}#slide-1`;
  await page.goto(fileUrl, { waitUntil: 'load' });

  // Wait for MathJax to finish rendering
  await page.waitForFunction(() => {
    return typeof MathJax !== 'undefined' && MathJax.typesetPromise !== undefined;
  }, { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(4000);

  // Get total slides
  const total = await page.evaluate(() => {
    return document.querySelectorAll('.slide').length;
  });
  console.log(`Total slides: ${total}`);

  for (let i = 1; i <= total; i++) {
    // Navigate to slide via hash
    await page.evaluate((slideNum) => {
      window.location.hash = `#slide-${slideNum}`;
    }, i);
    await page.waitForTimeout(600);

    // Wait for active slide to be visible
    await page.waitForSelector('.slide.active', { timeout: 3000 }).catch(() => {});

    const filename = `slide-${String(i).padStart(2, '0')}.png`;
    const screenshotPath = path.join(outDir, filename);

    await page.screenshot({
      path: screenshotPath,
      fullPage: false,
      clip: { x: 0, y: 0, width: 1280, height: 720 }
    });
    console.log(`Captured ${filename}`);
  }

  await browser.close();
  console.log(`Done! ${total} screenshots saved to review/slides_new/`);
})();

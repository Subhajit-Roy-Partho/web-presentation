const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function detectIssues() {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  
  await page.goto(`file://${__dirname}/index.html#slide-1`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  
  const issues = [];
  
  for (let i = 1; i <= 42; i++) {
    await page.goto(`file://${__dirname}/index.html#slide-${i}`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(600);
    
    const slideIssues = await page.evaluate(() => {
      const problems = [];
      const slide = document.querySelector('.slide.active');
      if (!slide) return problems;
      
      const textElements = Array.from(slide.querySelectorAll('p, h1, h2, h3, h4, span, li, div, text'));
      const rects = [];
      
      textElements.forEach((el, idx) => {
        if (el.offsetParent === null) return; // hidden
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;
        
        // Check for overflow outside slide container
        if (rect.right > 1280 || rect.bottom > 720 || rect.left < 0 || rect.top < 0) {
          problems.push({
            type: 'overflow',
            tag: el.tagName,
            text: el.textContent?.substring(0, 80),
            rect: { left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom }
          });
        }
        
        // Check for overlapping text elements
        rects.forEach(r => {
          if (!(rect.right < r.rect.left || rect.left > r.rect.right ||
                rect.bottom < r.rect.top || rect.top > r.rect.bottom)) {
            // Overlap detected - but filter if same parent or intentional
            const isChild = el.contains(r.el) || r.el.contains(el);
            if (!isChild && el.textContent?.trim() && r.el.textContent?.trim()) {
              problems.push({
                type: 'overlap',
                el1: el.tagName + ': ' + el.textContent.substring(0, 50),
                el2: r.el.tagName + ': ' + r.el.textContent.substring(0, 50),
                rect1: { left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom },
                rect2: { left: r.rect.left, top: r.rect.top, right: r.rect.right, bottom: r.rect.bottom }
              });
            }
          }
        });
        
        rects.push({ el, rect });
      });
      
      return problems;
    });
    
    if (slideIssues.length > 0) {
      issues.push({ slide: i, issues: slideIssues });
    }
    
    console.log(`Slide ${i}: ${slideIssues.length} issues`);
  }
  
  await browser.close();
  
  fs.writeFileSync('detected_issues.json', JSON.stringify(issues, null, 2));
  console.log('\nDone. Results saved to detected_issues.json');
  console.log(`Total slides with issues: ${issues.length}`);
  
  if (issues.length > 0) {
    console.log('\nSummary:');
    issues.forEach(item => {
      console.log(`Slide ${item.slide}: ${item.issues.length} problems`);
      item.issues.forEach(iss => {
        if (iss.type === 'overflow') {
          console.log(`  [Overflow] ${iss.tag}: "${iss.text?.substring(0, 40)}..." at (${iss.rect.left.toFixed(0)}, ${iss.rect.top.toFixed(0)})`);
        } else {
          console.log(`  [Overlap] ${iss.el1.substring(0, 50)}`);
          console.log(`          ↔ ${iss.el2.substring(0, 50)}`);
        }
      });
    });
  }
}

detectIssues().catch(console.error);

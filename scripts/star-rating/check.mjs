// Run against serve_demo.py: node scripts/star-rating/check.mjs
// Requires Playwright and its Chromium browser installed locally.
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
const browser = await chromium.launch();
try {
    const page = await browser.newPage({ viewport: { width: 1000, height: 960 } });
    await page.goto('http://127.0.0.1:8766/p/1/');
    const groups = page.getByRole('group');
    assert.equal(await groups.count(), 5);
    assert.equal(await page.locator('input[data-star-rating]').count(), 0);
    const first = page.getByRole('group', { name: 'A Little Further' });
    assert.equal(await first.getByRole('radio', { name: '4 out of 5 stars' }).isChecked(), true);
    await first.getByRole('radio', { name: '4 out of 5 stars' }).press('ArrowRight');
    assert.equal(await first.getByRole('radio', { name: '5 out of 5 stars' }).isChecked(), true);
    await first.locator('label').filter({ has: page.getByRole('radio', { name: '0 out of 5 stars' }) }).click();
    assert.equal(await first.getByRole('radio', { name: '0 out of 5 stars' }).isChecked(), true);
    const unrated = page.getByRole('group', { name: 'Out of the Blue' });
    assert.equal(await unrated.locator('input:checked').count(), 0);
    await page.getByRole('button', { name: 'Save ratings' }).click();
    assert.equal(await page.locator('input:invalid').count(), 6);
    await unrated.getByRole('radio', { name: '0 out of 5 stars' }).press('Space');
    await page.getByRole('button', { name: 'Save ratings' }).click();
    await page.getByText('Vote recorded').waitFor();
    assert.equal(await first.getByRole('radio', { name: '0 out of 5 stars' }).isChecked(), true);
    await page.screenshot({ path: 'star-rating-desktop.png', fullPage: true });
    await page.setViewportSize({ width: 375, height: 812 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: 'star-rating-mobile.png', fullPage: true });
    const fallback = await browser.newPage({ javaScriptEnabled: false });
    await fallback.goto('http://127.0.0.1:8766/p/1/');
    assert.equal(await fallback.getByRole('spinbutton').count(), 5);
    console.log('Keyboard, zero, required ratings, submission, mobile and fallback checks passed.');
} finally {
    await browser.close();
}

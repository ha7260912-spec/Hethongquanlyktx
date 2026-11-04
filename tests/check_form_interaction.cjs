// Run with Node.js and Playwright installed. Uses rendered templates, no database.
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const { chromium, request } = require('playwright');

(async () => {
    const render = spawnSync('python', ['tests/render_form_pages.py'], { encoding: 'utf8' });
    assert.equal(render.status, 0, render.stderr);
    const pages = JSON.parse(render.stdout);
    const http = await request.newContext();
    const assets = {};
    for (const suffix of ['css/bootstrap.min.css', 'js/bootstrap.bundle.min.js']) {
        const response = await http.get(`https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/${suffix}`);
        assert.equal(response.status(), 200);
        assets[suffix] = await response.body();
    }
    await http.dispose();
    const browser = await chromium.launch({
        headless: true,
        executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    });
    try {
        for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
            const page = await browser.newPage({ viewport });
            const errors = [];
            page.on('pageerror', error => errors.push(error.message));
            await page.route('**/*', async route => {
                const suffix = Object.keys(assets).find(s => route.request().url().endsWith(s));
                if (suffix) {
                    await route.fulfill({
                        contentType: suffix.endsWith('.css') ? 'text/css' : 'application/javascript',
                        body: assets[suffix],
                    });
                } else {
                    await route.abort();
                }
            });
            const load = async name => {
                await page.setContent(pages[name], { waitUntil: 'load' });
                await page.waitForFunction(() => document.getAnimations().every(a =>
                    a.effect.getTiming().iterations === Infinity || a.playState === 'finished'));
            };
            const type = async (selector, value) => {
                const input = page.locator(selector);
                await input.click({ timeout: 3000 });
                await input.fill(value);
                assert.equal(await input.inputValue(), value);
            };
            await load('usage');
            await page.locator('[data-bs-target="#modalThem"]').click();
            await page.waitForSelector('#modalThem.show');
            const hit = await page.locator('#serviceSearchThem').evaluate(el => {
                const rect = el.getBoundingClientRect();
                const top = document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2);
                return { top: top?.className, inputOnTop: top === el };
            });
            console.log(JSON.stringify({ viewport, modalHit: hit }));
            assert.equal(hit.inputOnTop, true, 'Backdrop must not cover the dialog input');
            await type('#serviceSearchThem', 'Giặt');
            await page.locator('#modalThem .service-option:visible').click();
            assert.equal(await page.locator('#modalThem [name="ma_dv"]').inputValue(), 'DV01');
            await page.locator('#modalThem [name="ma_sv"]').selectOption('SV01');
            await type('#modalThem [name="thoi_gian"]', '2026-10-27T09:00');
            await type('#modalThem [name="so_luong"]', '2');
            await page.locator('#modalThem [data-bs-dismiss="modal"]').first().click();
            await page.waitForSelector('.modal-backdrop', { state: 'detached' });
            await page.locator('[data-bs-target="#modalSua1"]').click();
            await type('#modalSua1 [name="so_luong"]', '3');
            await page.keyboard.press('Escape');
            await page.waitForSelector('.modal-backdrop', { state: 'detached' });
            await page.locator('[data-bs-target="#modalThem"]').click();
            await type('#modalThem [name="so_luong"]', '4');
            await page.keyboard.press('Escape');
            await page.waitForSelector('.modal-backdrop', { state: 'detached' });
            await load('services');
            await type('form[action="/dich-vu/them"] [name="ten_dv"]', 'Dịch vụ kiểm thử');
            await type('form[action="/dich-vu/them"] [name="don_gia"]', '15000');
            await load('student');
            await type('[name="HoTen"]', 'Sinh viên kiểm thử');
            assert.deepEqual(errors, [], 'JavaScript errors');
            console.log(`PASS add/edit usage, add service, add student at ${viewport.width}px`);
            await page.close();
        }
    } finally {
        await browser.close();
    }
})().catch(error => { console.error(error); process.exitCode = 1; });

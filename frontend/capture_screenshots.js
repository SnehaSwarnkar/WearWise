import puppeteer from 'puppeteer';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  const screenshotsDir = path.join(__dirname, '..', 'screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // 1. Home
  console.log('Capturing Home...');
  await page.goto('http://127.0.0.1:3000/', { waitUntil: 'networkidle0' });
  await page.screenshot({ path: path.join(screenshotsDir, '01_home.png') });

  // 2. Explore
  console.log('Capturing Explore...');
  await page.goto('http://127.0.0.1:3000/explore', { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 1000));
  await page.screenshot({ path: path.join(screenshotsDir, '02_explore.png') });

  // 3. My Fit Dashboard
  console.log('Capturing Dashboard...');
  await page.goto('http://127.0.0.1:3000/my-fit', { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 1000));
  await page.screenshot({ path: path.join(screenshotsDir, '03_dashboard.png') });

  // 4. Avatar Studio
  console.log('Capturing Avatar Studio...');
  await page.goto('http://127.0.0.1:3000/avatar', { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(screenshotsDir, '04_avatar_studio.png') });

  // 5. Honest Fit Studio
  console.log('Capturing Honest Fit...');
  await page.goto('http://127.0.0.1:3000/fit?sku=TSH-WW-CREW-001', { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 1000));

  // Try clicking Evaluate button
  try {
    const evalButton = await page.$('button.btn-primary');
    if (evalButton) {
      await evalButton.click();
      await new Promise((r) => setTimeout(r, 1500));
    }
  } catch (e) {
    console.log('Evaluate click note:', e.message);
  }
  await page.screenshot({ path: path.join(screenshotsDir, '05_honest_fit.png') });

  // 6. Checkout
  console.log('Capturing Checkout...');
  await page.goto('http://127.0.0.1:3000/checkout', { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 1000));
  await page.screenshot({ path: path.join(screenshotsDir, '06_checkout.png') });

  // 7. Dual-Mode Try-On (Mode A: 3D Avatar)
  console.log('Capturing Try-On Mode A (3D Avatar - Rest Pose)...');
  await page.goto('http://127.0.0.1:3000/try-on', { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 3000));
  await page.screenshot({ path: path.join(screenshotsDir, '07_tryon_mode_a.png') });

  // 8. Try-On Mode A with Arm Elevation (45 degrees motion & cloth deformation)
  console.log('Capturing Try-On Mode A with Arm Elevation...');
  try {
    await page.evaluate(() => {
      const slider = document.querySelector('.tryon-arm-slider');
      if (slider) {
        slider.value = '45';
        slider.dispatchEvent(new Event('input', { bubbles: true }));
        slider.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    await new Promise((r) => setTimeout(r, 2000));
    await page.screenshot({ path: path.join(screenshotsDir, '08_tryon_mode_a_arm_raised.png') });
  } catch (e) {
    console.log('Arm elevation capture note:', e.message);
  }

  // 9. Merchant Garment Studio
  console.log('Capturing Merchant Garment Studio...');
  await page.goto('http://127.0.0.1:3000/merchant/garment-studio', { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(screenshotsDir, '09_merchant_studio.png') });

  // 10. Dual-Mode Try-On (Mode B: AI Photo)
  console.log('Capturing Try-On Mode B (AI Photo VTON)...');
  await page.goto('http://127.0.0.1:3000/try-on', { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 1500));
  const btns = await page.$$('.mode-toggle-btn');
  if (btns.length > 1) {
    await btns[1].click();
    await new Promise((r) => setTimeout(r, 1200));
  }
  await page.screenshot({ path: path.join(screenshotsDir, '10_tryon_mode_b.png') });

  await browser.close();
  console.log('All screenshots captured successfully.');
}

main().catch((err) => {
  console.error('Capture error:', err);
  process.exit(1);
});

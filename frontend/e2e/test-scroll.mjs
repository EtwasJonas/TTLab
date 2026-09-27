import puppeteer from "puppeteer-core";
import { setTimeout as sleep } from "timers/promises";

const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const dataset = `scrolltest_${Date.now()}`;

const browser = await puppeteer.launch({
  executablePath: EDGE, headless: "new", args: ["--no-sandbox"],
});
const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 600 }); // small viewport => page must scroll
let stepFails = 0;
const step = (n, ok, e = "") => { if (!ok) stepFails++; console.log(`${ok ? "PASS" : "FAIL"} | ${n}${e ? " | " + e : ""}`); };

try {
  await page.goto("http://localhost:3000/labeling", { waitUntil: "networkidle2", timeout: 30000 });
  await page.type("input[placeholder*='baelle']", dataset);
  await page.keyboard.press("Enter");
  await page.waitForFunction(() =>
    [...document.querySelectorAll("button")].some((b) => b.innerText.match(/#(\d+)/)),
    { timeout: 10000 }
  );
  await page.evaluate(() => {
    [...document.querySelectorAll("button")].filter((b) => b.innerText.match(/#(\d+)/))[0].click();
  });
  await page.waitForSelector('[data-testid="draw-overlay"]', { timeout: 15000 });
  await page.waitForFunction(() => {
    const img = document.querySelector('img[alt^="Frame"]');
    return img && img.complete && img.naturalWidth > 0;
  }, { timeout: 15000 });
  await sleep(300);

  // Ans Seitenende scrollen (fester Pixelwert wäre von der Seitenhöhe abhängig)
  await page.evaluate(() => window.scrollTo(0, 999999));
  await sleep(300);
  const scrollBefore = await page.evaluate(() => window.scrollY);
  step(`Gescrollt (ist: ${Math.round(scrollBefore)}px)`, scrollBefore > 100, `ist: ${scrollBefore}`);

  // Frame-Wechsel per +1s Button
  await page.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find((b) => b.innerText.trim() === "+1s");
    if (!btn) throw new Error("+1s-Button nicht gefunden");
    btn.click();
  });
  await sleep(700); // Bild laden lassen
  const scrollAfter1 = await page.evaluate(() => window.scrollY);
  step("Scroll-Position nach +1s Frame-Sprung unverändert", Math.abs(scrollAfter1 - scrollBefore) < 5, `vorher: ${scrollBefore}, nachher: ${scrollAfter1}`);

  // Mehrere Sprünge hintereinander
  for (let i = 0; i < 3; i++) {
    await page.evaluate(() => {
      [...document.querySelectorAll("button")].find((b) => b.innerText.trim() === "+1s")?.click();
    });
    await sleep(500);
  }
  const scrollAfter4 = await page.evaluate(() => window.scrollY);
  step("Scroll-Position nach 4 Sprüngen unverändert", Math.abs(scrollAfter4 - scrollBefore) < 5, `vorher: ${scrollBefore}, nachher: ${scrollAfter4}`);

  // Frames geladen? (Zeit-Anzeige weiter fortgeschritten)
  const frameText = await page.evaluate(() =>
    [...document.querySelectorAll("span")].find((s) => /Frame \d+/.test(s.innerText))?.innerText
  );
  step("Frames wurden tatsächlich gewechselt", /Frame \d+\/\d+ · 0:0[34]\./.test(frameText), frameText);

  // Container hat reservierte Höhe (Layout kollabiert nie)?
  const ratio = await page.evaluate(() => {
    const el = document.querySelector('[data-testid="draw-overlay"]').parentElement;
    return { w: el.getBoundingClientRect().width, h: el.getBoundingClientRect().height };
  });
  const is169 = Math.abs(ratio.w / ratio.h - 16 / 9) < 0.02;
  step("Container hält 16:9 auch während des Ladens", is169, `${Math.round(ratio.w)}x${Math.round(ratio.h)}`);
} catch (e) {
  step("Test abgebrochen", false, e.message);
} finally {
  await browser.close();
}
process.exitCode = stepFails ? 1 : 0;

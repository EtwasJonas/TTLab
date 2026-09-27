import puppeteer from "puppeteer-core";
import { setTimeout as sleep } from "timers/promises";

const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const dataset = `lastlab_${Date.now()}`;

const browser = await puppeteer.launch({
  executablePath: EDGE, headless: "new", args: ["--no-sandbox"],
});
const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 900 });
let stepFails = 0;
const step = (n, ok, e = "") => { if (!ok) stepFails++; console.log(`${ok ? "PASS" : "FAIL"} | ${n}${e ? " | " + e : ""}`); };
const frameText = () =>
  page.evaluate(() =>
    [...document.querySelectorAll("span")].find((s) => /Frame \d+/.test(s.innerText))?.innerText ?? null
  );

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

  // 1) Frame 0 labeln (Box zeichnen -> Auto-Save -> Frame 1)
  const box = await (await page.$('[data-testid="draw-overlay"]')).boundingBox();
  await page.mouse.move(box.x + box.width * 0.4, box.y + box.height * 0.4);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.5);
  await page.mouse.up();
  await sleep(2200); // Auto-Save (900ms) + Fetch
  let ft = await frameText();
  step("Nach Labeling auf Frame 2 gesprungen", /Frame 2\//.test(ft), ft);

  // 2) Weit weg springen
  const clickButton = (label) =>
    page.evaluate((l) => {
      [...document.querySelectorAll("button")].find((b) => b.innerText.trim() === l)?.click();
    }, label);
  for (let i = 0; i < 12; i++) {
    await clickButton("+1s");
    await sleep(80);
  }
  await sleep(800);
  ft = await frameText();
  step("Weit weg gesprungen (Frame ~1200+)", !/Frame 2\//.test(ft), ft);

  // 3) Button 'Letzter gelabelter Frame' klicken
  await page.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find((b) =>
      b.innerText.includes("Letzter gelabelter Frame")
    );
    if (!btn) throw new Error("Button nicht gefunden");
    btn.click();
  });
  await sleep(1000);
  ft = await frameText();
  step("Zurueck auf Frame 1 (zuletzt gelabelt)", /Frame 1\//.test(ft), ft);

  // 4) Box + gelabelt-Badge sichtbar?
  const boxes = await page.evaluate(
    () => document.querySelectorAll('[data-testid="ball-box"]').length
  );
  const labeled = await page.evaluate(() => document.body.innerText.includes("gelabelt"));
  step("Gespeicherte Box + 'gelabelt'-Status sichtbar", boxes === 1 && labeled, `Boxen: ${boxes}`);
} catch (e) {
  step("Test abgebrochen", false, e.message);
} finally {
  await browser.close();
  // Aufraeumen: Annotation + Datensatz loeschen (Match 7, Frame 0)
  try {
    await fetch(`http://127.0.0.1:8000/api/labeling/datasets/${dataset}/annotations/7/0`, { method: "DELETE" });
  } catch {}
}

process.exitCode = stepFails ? 1 : 0;

import puppeteer from "puppeteer-core";
import { setTimeout as sleep } from "timers/promises";

const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const APP = "http://localhost:3000";
const API = "http://localhost:8000";
const dataset = `uitest_${Date.now()}`;

const browser = await puppeteer.launch({
  executablePath: EDGE,
  headless: "new",
  args: ["--no-sandbox"],
});
const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 900 });

const consoleErrors = [];
page.on("console", (msg) => {
  if (msg.type() === "error") consoleErrors.push(msg.text());
});
page.on("pageerror", (err) => consoleErrors.push(`PAGEERROR: ${err.message}`));

let stepFails = 0;
const step = (name, ok, extra = "") => {
  if (!ok) stepFails++;
  console.log(`${ok ? "PASS" : "FAIL"} | ${name}${extra ? " | " + extra : ""}`);
};

try {
  // --- 1. Open labeling page ---
  await page.goto(`${APP}/labeling`, { waitUntil: "networkidle2", timeout: 30000 });
  await page.waitForSelector("input[placeholder*='baelle']", { timeout: 10000 });
  step("Labeling-Seite geladen", true);

  // --- 2. Create dataset ---
  await page.type("input[placeholder*='baelle']", dataset);
  await page.keyboard.press("Enter");
  await page.waitForFunction(
    (name) => document.body.innerText.includes("Video wählen") || document.body.innerText.includes("Select video"),
    { timeout: 10000 },
    dataset
  );
  step("Datensatz erstellt", true);

  // --- 3. Select first match card ---
  await page.waitForFunction(
    () => document.querySelectorAll("button").length > 0,
    { timeout: 10000 }
  );
  const clicked = await page.evaluate(() => {
    const cards = [...document.querySelectorAll("button")].filter((b) =>
      b.innerText.match(/#(\d+)/)
    );
    if (cards.length === 0) return false;
    cards[0].click();
    return true;
  });
  step("Video ausgewählt", clicked);
  if (!clicked) throw new Error("Keine Video-Karten gefunden");

  // --- 4. Wait for workbench (overlay + image) ---
  await page.waitForSelector('[data-testid="draw-overlay"]', { timeout: 15000 });
  await page.waitForFunction(() => {
    const img = document.querySelector('img[alt^="Frame"]');
    return img && img.complete && img.naturalWidth > 0;
  }, { timeout: 15000 });
  await sleep(300);
  step("Workbench + Frame geladen", true);

  // --- 5. Simulate the user's drag (mousedown, hold, move, up) ---
  const overlay = await page.$('[data-testid="draw-overlay"]');
  const box = await overlay.boundingBox();
  step("Overlay sichtbar & positioniert", !!box, `size ${Math.round(box.width)}x${Math.round(box.height)} @ ${Math.round(box.x)},${Math.round(box.y)}`);

  const startX = box.x + box.width * 0.4;
  const startY = box.y + box.height * 0.4;
  const endX = box.x + box.width * 0.6;
  const endY = box.y + box.height * 0.55;

  await page.mouse.move(startX, startY);
  await page.mouse.down();
  // move in several steps like a real drag
  for (let i = 1; i <= 8; i++) {
    await page.mouse.move(
      startX + ((endX - startX) * i) / 8,
      startY + ((endY - startY) * i) / 8
    );
    await sleep(30);
  }

  // --- 6. Drag preview visible DURING the drag? ---
  const preview = await page.evaluate(() => {
    const el = document.querySelector('[data-testid="drag-preview"]');
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { w: r.width, h: r.height };
  });
  step("Zieh-Rahmen WÄHREND des Ziehens sichtbar", !!preview && preview.w > 5, JSON.stringify(preview));

  await page.mouse.up();
  await sleep(200);

  // --- 7. Box created after mouseup? ---
  const boxesAfter = await page.evaluate(
    () => document.querySelectorAll('[data-testid="ball-box"]').length
  );
  step("Box nach Loslassen vorhanden", boxesAfter === 1, `Anzahl: ${boxesAfter}`);

  // --- 8. Auto-save fired (900ms) and frame advanced? ---
  await sleep(2200);
  const frameText = await page.evaluate(() => {
    const el = [...document.querySelectorAll("span")].find((s) => /Frame \d+/.test(s.innerText));
    return el ? el.innerText : null;
  });
  step("Frame nach Auto-Save weitergesprungen", frameText?.includes("Frame 2/") === true, frameText);

  // --- 9. Annotation persisted in backend? ---
  const response = await fetch(`${API}/api/labeling/datasets/${dataset}/annotations`);
  const annotations = await response.json();
  const savedCorrectly =
    Array.isArray(annotations) &&
    annotations.length === 1 &&
    annotations[0].bboxes.length === 1;
  step("Annotation im Backend gespeichert", savedCorrectly, JSON.stringify(annotations));

  // --- 10. "gelabelt"-Badge after navigating back to frame 1? ---
  await page.keyboard.press("ArrowLeft");
  await sleep(600);
  const badge = await page.evaluate(() =>
    document.body.innerText.includes("gelabelt") ? "gelabelt-Schrift vorhanden" : "KEIN gelabelt-Badge"
  );
  const boxesBack = await page.evaluate(
    () => document.querySelectorAll('[data-testid="ball-box"]').length
  );
  step("Zurück auf Frame 1: Box + gelabelt-Status", boxesBack === 1, badge);
} catch (e) {
  step("Test abgebrochen", false, e.message);
} finally {
  console.log("\nBrowser-Konsole (Fehler):");
  console.log(consoleErrors.length ? consoleErrors.join("\n") : "(keine)");
  // Cleanup test dataset
  try {
    await fetch(`${API}/api/labeling/datasets/${dataset}/annotations/5/0`, { method: "DELETE" }).catch(() => {});
  } catch {}
  await browser.close();
}
process.exitCode = stepFails ? 1 : 0;

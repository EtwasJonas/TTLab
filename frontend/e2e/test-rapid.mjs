import puppeteer from "puppeteer-core";
import { setTimeout as sleep } from "timers/promises";

const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const dataset = `rapidtest_${Date.now()}`;

const browser = await puppeteer.launch({
  executablePath: EDGE, headless: "new", args: ["--no-sandbox"],
});
const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 900 });
let stepFails = 0;
const step = (n, ok, e = "") => { if (!ok) stepFails++; console.log(`${ok ? "PASS" : "FAIL"} | ${n}${e ? " | " + e : ""}`); };

const imgState = () =>
  page.evaluate(() => {
    const img = document.querySelector('img[alt^="Frame"]');
    const overlay = document.querySelector('[data-testid="draw-overlay"]');
    const loadingOverlay = [...document.querySelectorAll("div")].some(
      (d) => d.className.includes("bg-black/60") && d.innerText.includes("Lade")
    );
    if (!img) return { exists: false };
    return {
      exists: true,
      complete: img.complete,
      naturalWidth: img.naturalWidth,
      currentSrc: img.currentSrc.split("?")[1] ?? img.currentSrc,
      overlaySize: overlay ? `${Math.round(overlay.getBoundingClientRect().width)}x${Math.round(overlay.getBoundingClientRect().height)}` : null,
      loadingOverlayVisible: loadingOverlay,
      frameText: [...document.querySelectorAll("span")].find((s) => /Frame \d+/.test(s.innerText))?.innerText ?? null,
    };
  });

try {
  await page.goto("http://localhost:3000/labeling", { waitUntil: "networkidle2", timeout: 30000 });
  await page.type("input[placeholder*='baelle']", dataset);
  await page.keyboard.press("Enter");
  await page.waitForFunction(() =>
    [...document.querySelectorAll("button")].some((b) => b.innerText.match(/#(\d+)/)),
    { timeout: 10000 }
  );
  await page.evaluate(() => {
    // Video mit ID 2 auswaehlen (iPhone-Video, das der User labelt)
    const cards = [...document.querySelectorAll("button")].filter((b) => b.innerText.match(/#(\d+)/));
    const card2 = cards.find((b) => b.innerText.includes("#2"));
    (card2 ?? cards[0]).click();
  });
  await page.waitForSelector('[data-testid="draw-overlay"]', { timeout: 15000 });
  await page.waitForFunction(() => {
    const img = document.querySelector('img[alt^="Frame"]');
    return img && img.complete && img.naturalWidth > 0;
  }, { timeout: 15000 });
  await sleep(500);
  console.log("Startzustand:", JSON.stringify(await imgState()));

  const clickButton = (label) =>
    page.evaluate((l) => {
      [...document.querySelectorAll("button")].find((b) => b.innerText.trim() === l)?.click();
    }, label);

  console.log("\n=== Szenario 1: 6x schnell +1s (50ms Abstand) ===");
  for (let i = 0; i < 6; i++) {
    await clickButton("+1s");
    await sleep(50);
  }
  // 3s warten - genug fuer jeden Load
  for (let wait = 0; wait < 30; wait++) {
    await sleep(100);
    const s = await imgState();
    if (s.complete && s.naturalWidth > 0 && !s.loadingOverlayVisible) break;
  }
  let state = await imgState();
  console.log("Nach 3s:", JSON.stringify(state));
  step("Frame nach 6x +1s geladen", state.complete && state.naturalWidth > 0 && !state.loadingOverlayVisible);

  console.log("\n=== Szenario 2: 10x schnell +1 Frame (30ms Abstand) ===");
  for (let i = 0; i < 10; i++) {
    await clickButton("Frame ▶");
    await sleep(30);
  }
  for (let wait = 0; wait < 30; wait++) {
    await sleep(100);
    const s = await imgState();
    if (s.complete && s.naturalWidth > 0 && !s.loadingOverlayVisible) break;
  }
  state = await imgState();
  console.log("Nach 3s:", JSON.stringify(state));
  step("Frame nach 10x Frame▶ geladen", state.complete && state.naturalWidth > 0 && !state.loadingOverlayVisible);

  console.log("\n=== Szenario 3: gemischt vor/zurueck, sehr schnell ===");
  const sequence = ["+1s", "+1s", "−1s", "Frame ▶", "+1s", "−1s", "−1s", "Frame ▶", "+1s"];
  for (const btn of sequence) {
    await clickButton(btn);
    await sleep(40);
  }
  for (let wait = 0; wait < 30; wait++) {
    await sleep(100);
    const s = await imgState();
    if (s.complete && s.naturalWidth > 0 && !s.loadingOverlayVisible) break;
  }
  state = await imgState();
  console.log("Nach 3s:", JSON.stringify(state));
  const expectedFrameOk = state.frameText && /Frame \d+/.test(state.frameText);
  step("Frame nach gemischtem Rapid-Jumping geladen", state.complete && state.naturalWidth > 0 && !state.loadingOverlayVisible);
} catch (e) {
  step("Test abgebrochen", false, e.message);
} finally {
  await browser.close();
}

process.exitCode = stepFails ? 1 : 0;

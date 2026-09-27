import puppeteer from "puppeteer-core";
import { setTimeout as sleep } from "timers/promises";

const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const dataset = `jumptest_${Date.now()}`;

const browser = await puppeteer.launch({
  executablePath: EDGE, headless: "new", args: ["--no-sandbox"],
});
const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 900 });
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

  // Set jump width to 2 seconds
  const input = await page.$('input[type="number"]');
  await input.click();
  await page.keyboard.down("Control");
  await page.keyboard.press("a");
  await page.keyboard.up("Control");
  await page.keyboard.type("2");
  await sleep(200);
  const value = await page.evaluate(() => document.querySelector('input[type="number"]').value);
  step("Sprungweite auf 2s gesetzt", value === "2", `Wert: ${value}`);

  // Read fps from the page (time display) to derive expected frames
  const fps = await page.evaluate(() => {
    const info = [...document.querySelectorAll("span")].find((s) => /Frame 1\//.test(s.innerText));
    return info ? null : null;
  });
  // Get fps via API for the first match instead
  const matches = await (await fetch("http://127.0.0.1:8000/api/matches")).json();
  const matchId = matches[0].id;
  const videoInfo = await (await fetch(`http://127.0.0.1:8000/api/matches/${matchId}/video-info`)).json();
  const expectedJump = Math.round(2 * videoInfo.fps);
  console.log(`Video fps: ${videoInfo.fps} -> erwarteter Sprung: ${expectedJump} Frames`);

  // Jump forward with the +Xs button
  await page.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find((b) => b.innerText.trim() === "+2s");
    if (!btn) throw new Error("+2s-Button nicht gefunden");
    btn.click();
  });
  await sleep(400);
  let frameText = await page.evaluate(() =>
    [...document.querySelectorAll("span")].find((s) => /Frame \d+/.test(s.innerText))?.innerText
  );
  step(`Forward-Jump 2s (Frame ${expectedJump + 1}/…)`, new RegExp(`Frame ${expectedJump + 1}\\/`).test(frameText), frameText);

  // Jump back with the −Xs button
  await page.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find((b) => b.innerText.trim() === "−2s");
    if (!btn) throw new Error("−2s-Button nicht gefunden");
    btn.click();
  });
  await sleep(400);
  frameText = await page.evaluate(() =>
    [...document.querySelectorAll("span")].find((s) => /Frame \d+/.test(s.innerText))?.innerText
  );
  step("Backward-Jump 2s (zurück auf Frame 1)", /Frame 1\//.test(frameText), frameText);

  // Blur the input first (shortcuts are blocked while typing), then Shift+→
  await page.evaluate(() => document.activeElement?.blur());
  await sleep(100);
  await page.keyboard.down("Shift");
  await page.keyboard.press("ArrowRight");
  await page.keyboard.up("Shift");
  await sleep(400);
  frameText = await page.evaluate(() =>
    [...document.querySelectorAll("span")].find((s) => /Frame \d+/.test(s.innerText))?.innerText
  );
  step(`Shift+→ nutzt ebenfalls 2s (Frame ${expectedJump + 1})`, new RegExp(`Frame ${expectedJump + 1}\\/`).test(frameText), frameText);

  // Typing in the input must NOT trigger shortcuts (re-focus and press arrows)
  await page.evaluate(() => document.querySelector('input[type="number"]')?.focus());
  await page.keyboard.press("ArrowRight");
  await sleep(300);
  frameText = await page.evaluate(() =>
    [...document.querySelectorAll("span")].find((s) => /Frame \d+/.test(s.innerText))?.innerText
  );
  const inputFocused = await page.evaluate(() => document.activeElement?.tagName === "INPUT");
  step("Pfeiltasten im Eingabefeld lösen KEINEN Sprung aus",
    new RegExp(`Frame ${expectedJump + 1}\\/`).test(frameText) && inputFocused, frameText);
} catch (e) {
  step("Test abgebrochen", false, e.message);
} finally {
  await browser.close();
  try {
    await fetch(`http://127.0.0.1:8000/api/labeling/datasets/${dataset}`, { method: "GET" });
  } catch {}
}
process.exitCode = stepFails ? 1 : 0;

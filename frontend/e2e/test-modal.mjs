import puppeteer from "puppeteer-core";
import { setTimeout as sleep } from "timers/promises";

const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const browser = await puppeteer.launch({
  executablePath: EDGE, headless: "new", args: ["--no-sandbox"],
});
const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 700 }); // kleiner Viewport => Modal muss scrollen
let stepFails = 0;
const step = (n, ok, e = "") => { if (!ok) stepFails++; console.log(`${ok ? "PASS" : "FAIL"} | ${n}${e ? " | " + e : ""}`); };

try {
  await page.goto("http://localhost:3000/labeling", { waitUntil: "networkidle2", timeout: 30000 });

  // Shortcuts-Modal öffnen
  await page.evaluate(() => {
    [...document.querySelectorAll("button")].find((b) => b.innerText.includes("Shortcuts"))?.click();
  });
  await sleep(400);
  const modalVisible = await page.evaluate(() => !!document.querySelector("h2"));
  step("Modal geöffnet", modalVisible);

  // 1) Hoehe: Modal darf Viewport nicht ueberragen (Fix von eben)
  const modalBox = await page.evaluate(() => {
    const dialog = document.querySelector(".bg-\\[\\#0a0e17\\]");
    if (!dialog) return null;
    const r = dialog.getBoundingClientRect();
    return { top: r.top, bottom: r.bottom, height: r.height, viewport: window.innerHeight };
  });
  step(
    "Modal passt in den Viewport (nicht oben abgeschnitten)",
    modalBox && modalBox.top >= 0 && modalBox.bottom <= modalBox.viewport + 1,
    JSON.stringify(modalBox)
  );

  // 2) Alle Shortcuts sichtbar/erreichbar? (scrollbar oder komplett sichtbar)
  const lastRowVisible = await page.evaluate(() => {
    const rows = [...document.querySelectorAll("kbd")];
    const last = rows[rows.length - 1];
    if (!last) return false;
    const r = last.getBoundingClientRect();
    return r.bottom <= window.innerHeight;
  });
  const scrollable = await page.evaluate(() => {
    const dialog = document.querySelector(".bg-\\[\\#0a0e17\\]");
    return dialog ? dialog.scrollHeight > dialog.clientHeight : false;
  });
  step("Letzter Shortcut sichtbar oder Modal scrollbar", lastRowVisible || scrollable, `sichtbar: ${lastRowVisible}, scrollbar: ${scrollable}`);

  // 3) Klick NEBEN das Modal schließt es
  await page.mouse.click(30, 400); // linke Kante, ausserhalb des Dialogs
  await sleep(300);
  const closed = await page.evaluate(() => !document.querySelector(".bg-\\[\\#0a0e17\\]"));
  step("Klick neben das Modal schließt es", closed);

  // 4) Erneut öffnen und Klick INS Modal schließt NICHT
  await page.evaluate(() => {
    [...document.querySelectorAll("button")].find((b) => b.innerText.includes("Shortcuts"))?.click();
  });
  await sleep(300);
  await page.mouse.click(700, 350); // Mitte = Dialog
  await sleep(300);
  const stillOpen = await page.evaluate(() => !!document.querySelector(".bg-\\[\\#0a0e17\\]"));
  step("Klick ins Modal schließt es NICHT", stillOpen);
} catch (e) {
  step("Test abgebrochen", false, e.message);
} finally {
  await browser.close();
}

process.exitCode = stepFails ? 1 : 0;

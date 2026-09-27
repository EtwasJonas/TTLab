// E2E-Runner: führt alle test-*.mjs Suiten sequenziell aus.
// Voraussetzungen: Backend (http://localhost:8000) und Frontend (http://localhost:3000) laufen,
// Edge unter C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe.
// Aufruf: npm run e2e  (optional einzelne Suite: npm run e2e -- test-draw)
import { readdir } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const dir = path.dirname(fileURLToPath(import.meta.url));
const filter = process.argv[2];
const files = (await readdir(dir))
  .filter((f) => /^test-.*\.mjs$/.test(f))
  .filter((f) => !filter || f.includes(filter))
  .sort();

if (files.length === 0) {
  console.error("Keine Testsuiten gefunden." + (filter ? ` Filter: ${filter}` : ""));
  process.exit(1);
}

let failed = 0;
for (const file of files) {
  console.log(`\n========== ${file} ==========`);
  const res = spawnSync(process.execPath, [path.join(dir, file)], { stdio: "inherit" });
  if (res.status !== 0) failed++;
}

console.log(`\n========== Ergebnis ==========`);
console.log(`${files.length - failed}/${files.length} Suiten erfolgreich.`);
process.exit(failed ? 1 : 0);

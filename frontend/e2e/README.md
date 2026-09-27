# E2E-Tests (Labeling-Tool & UI)

Browser-basierte End-to-End-Tests mit `puppeteer-core` (nutzt die vorhandene
Edge-Installation, kein Chromium-Download). Originale Entwicklungssuiten wurden
aus der letzten Sitzung 1:1 überführt.

## Voraussetzungen

1. **Backend läuft:** `http://localhost:8000` (im `backend/`-Ordner: `uvicorn app.main:app --port 8000`)
2. **Frontend (dev) läuft:** `http://localhost:3000` (`npm run dev` im `frontend/`-Ordner)
3. **Microsoft Edge** unter `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`
   (Standardpfad unter Windows 11; sonst `EDGE`-Konstante im jeweiligen Test anpassen)
4. **Mindestens ein Match mit Video** in der Datenbank (Tests klicken das erste
   Video in der Auswahl an)

## Ausführen

```bash
cd frontend
npm run e2e                # alle Suiten sequenziell
npm run e2e -- test-draw   # nur eine Suite (Filter per Substring)
```

Jede Suite gibt `PASS`/`FAIL`-Zeilen aus; der Runner (`run.mjs`) beendet sich
mit Exit-Code 1, wenn eine Suite fehlschlägt.

## Suiten

| Datei | Prüft |
|-------|-------|
| `test-draw.mjs` | BBox-Zeichnen im Overlay, Auto-Save, Backend-Persistenz, „gelabelt"-Badge, Multi-Box |
| `test-jump.mjs` | Sprungweiten-Feld (±Xs-Buttons + Shift+Pfeil), keine Shortcuts während der Eingabe |
| `test-scroll.mjs` | Scroll-Position bleibt bei Frame-Sprüngen exakt erhalten, 16:9-Container |
| `test-modal.mjs` | Shortcuts-Modal: passt in Viewport, scrollbar, Klick-daneben schließt / Klick-insModal nicht |
| `test-rapid.mjs` | Frame-Lade-Watchdog: schnelles ±Springen lädt Frames zuverlässig nach |
| `test-lastlabeled.mjs` | „Letzter gelabelter Frame"-Button springt zur letzten Annotation |

## Wichtig

- Die Tests legen **eigene Datensätze** an (`uitest_*`, `jumptest_*`, `scrolltest_*`,
  `rapidtest_*`, `lastlab_*` Präfixe) und räumen Annotationen teilweise selbst auf.
  Der Produktiv-Datensatz **`v1-ml-training` wird nie angefasst** – Tests geben ihn
  nie als Namen ein.
- Angelegte Test-Datensätze bleiben nach dem Lauf in der DB zurück und können im
  Labeling-UI beliebig gelöscht werden.
- Die Tests klicken primär auf `data-testid`-Anker (`draw-overlay`, `ball-box`)
  bzw. sichtbare Button-Texte (DE-UI). Bei Textänderungen an Buttons müssen die
  Suiten entsprechend angepasst werden.

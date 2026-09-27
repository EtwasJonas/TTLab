'use client';

import { useState } from 'react';
import { useLanguage } from '../lib/LanguageContext';
import { apiUrl } from '../lib/api';

type Phase = 'idle' | 'confirm' | 'shutting-down' | 'stopped' | 'blocked' | 'error';

export default function ShutdownButton() {
  const { language } = useLanguage();
  const [phase, setPhase] = useState<Phase>('idle');
  const [message, setMessage] = useState('');

  const de = language === 'de';

  const requestShutdown = async () => {
    setPhase('shutting-down');
    try {
      const res = await fetch(apiUrl('/api/shutdown'), { method: 'POST' });
      if (res.status === 409) {
        const data = await res.json();
        setMessage(data.detail ?? 'Analyse läuft noch.');
        setPhase('blocked');
        return;
      }
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setMessage(data.detail ?? `Fehler ${res.status}`);
        setPhase('error');
        return;
      }
      // Backend und Devserver sterben in ~1,5s. Tab schließen versuchen
      // (funktioniert nur bei per Skript geöffneten Tabs), sonst Overlay.
      setTimeout(() => {
        window.close();
        setPhase('stopped');
      }, 1800);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e));
      setPhase('error');
    }
  };

  // Vollbild-Overlay nach dem Herunterfahren (Fallback, wenn window.close()
  // vom Browser blockiert wird - der Nutzer schließt den Tab dann selbst).
  if (phase === 'stopped') {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#0a0e17]">
        <div className="text-center">
          <p className="text-6xl">🏓</p>
          <h2 className="mt-6 text-2xl font-bold text-white">
            {de ? 'TTLab wurde beendet' : 'TTLab has been shut down'}
          </h2>
          <p className="mt-3 text-slate-400">
            {de
              ? 'Alle Server und Fenster wurden geschlossen.'
              : 'All servers and windows have been closed.'}
          </p>
          <p className="mt-1 text-slate-500">
            {de
              ? 'Dieser Browser-Tab kann jetzt geschlossen werden.'
              : 'You can close this browser tab now.'}
          </p>
        </div>
      </div>
    );
  }

  if (phase === 'idle') {
    return (
      <button
        data-testid="shutdown-button"
        onClick={() => setPhase('confirm')}
        className="rounded-lg bg-red-500/15 px-3 py-1.5 text-sm font-medium text-red-300 transition hover:bg-red-500/30"
        title={de ? 'TTLab komplett beenden' : 'Shut down TTLab completely'}
      >
        ⏻ {de ? 'Beenden' : 'Shut down'}
      </button>
    );
  }

  if (phase === 'confirm') {
    return (
      <span className="flex items-center gap-2" data-testid="shutdown-confirm">
        <span className="hidden md:inline text-xs text-slate-400">
          {de ? 'Wirklich beenden?' : 'Really shut down?'}
        </span>
        <button
          onClick={requestShutdown}
          className="rounded-lg bg-red-500/70 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-red-500"
        >
          {de ? 'Ja, beenden' : 'Yes, shut down'}
        </button>
        <button
          onClick={() => setPhase('idle')}
          className="rounded-lg bg-white/[0.08] px-3 py-1.5 text-sm font-medium text-slate-300 transition hover:bg-white/[0.14]"
        >
          {de ? 'Abbrechen' : 'Cancel'}
        </button>
      </span>
    );
  }

  if (phase === 'shutting-down') {
    return (
      <span className="rounded-lg bg-red-500/15 px-3 py-1.5 text-sm text-red-300" data-testid="shutdown-running">
        {de ? 'Wird beendet…' : 'Shutting down…'}
      </span>
    );
  }

  // blocked / error: kurze Meldung, dann zurück zum Button
  return (
    <button
      data-testid="shutdown-blocked"
      onClick={() => setPhase('idle')}
      className="max-w-xs truncate rounded-lg bg-amber-500/15 px-3 py-1.5 text-sm font-medium text-amber-300 transition hover:bg-amber-500/30"
      title={message}
    >
      ⚠ {de ? 'Beenden nicht möglich' : 'Cannot shut down'}
    </button>
  );
}

'use client';

import { useLanguage } from '../lib/LanguageContext';
import { t } from '../lib/translations';
import ShortcutsModal from './ShortcutsModal';
import { useState } from 'react';

export default function LanguageSwitcher() {
  const { language, toggleLanguage } = useLanguage();
  const [showShortcuts, setShowShortcuts] = useState(false);
  
  return (
    <>
      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowShortcuts(true)}
          className="rounded-lg bg-white/[0.08] px-3 py-1.5 text-sm font-medium text-slate-300 hover:bg-white/[0.14] transition"
          title={language === 'de' ? 'Tastaturkürzel anzeigen' : 'Show keyboard shortcuts'}
        >
          ⌨️ {language === 'de' ? 'Shortcuts' : 'Shortcuts'}
        </button>
        <button
          onClick={toggleLanguage}
          className="rounded-lg bg-white/[0.08] px-3 py-1.5 text-sm font-medium text-slate-300 hover:bg-white/[0.14] transition"
          title="Sprache wechseln / Switch language"
        >
          {language === 'de' ? '🇩🇪 DE' : '🇬🇧 EN'}
        </button>
      </div>
      <ShortcutsModal isOpen={showShortcuts} onClose={() => setShowShortcuts(false)} />
    </>
  );
}

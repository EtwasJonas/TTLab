'use client';

import { useLanguage } from '../lib/LanguageContext';
import { t } from '../lib/translations';

export default function LanguageSwitcher() {
  const { language, toggleLanguage } = useLanguage();
  
  return (
    <button
      onClick={toggleLanguage}
      className="rounded-lg bg-white/[0.08] px-3 py-1.5 text-sm font-medium text-slate-300 hover:bg-white/[0.14] transition"
      title="Sprache wechseln / Switch language"
    >
      {language === 'de' ? '🇩🇪 DE' : '🇬🇧 EN'}
    </button>
  );
}

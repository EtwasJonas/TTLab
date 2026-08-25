'use client';

import { useLanguage } from '../lib/LanguageContext';
import { t } from '../lib/translations';
import { useEffect } from 'react';

interface ShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ShortcutsModal({ isOpen, onClose }: ShortcutsModalProps) {
  const { language } = useLanguage();

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const shortcuts = [
    { key: 'Leertaste / Space', action: t(language, 'shortcuts.play_pause') },
    { key: 'Strg + ← / Ctrl + Left', action: t(language, 'shortcuts.prev_rally') },
    { key: 'Strg + → / Ctrl + Right', action: t(language, 'shortcuts.next_rally') },
    { key: '← / Left', action: t(language, 'shortcuts.back_10ms') },
    { key: '→ / Right', action: t(language, 'shortcuts.forward_10ms') },
    { key: 'H', action: t(language, 'shortcuts.highlight') },
    { key: 'R', action: t(language, 'shortcuts.status_toggle') },
    { key: 'N', action: t(language, 'shortcuts.notes') },
    { key: 'L', action: t(language, 'shortcuts.loop') },
    { key: '1', action: t(language, 'shortcuts.speed_025') },
    { key: '2', action: t(language, 'shortcuts.speed_05') },
    { key: '3', action: t(language, 'shortcuts.speed_10') },
    { key: '4', action: t(language, 'shortcuts.speed_15') },
  ];

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={onClose}
    >
      <div 
        className="bg-[#0a0e17] border border-white/10 rounded-2xl max-w-md w-full shadow-2xl mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">{t(language, 'shortcuts.title')}</h2>
            <button 
              onClick={onClose}
              className="text-slate-400 hover:text-white transition"
            >
              ✕
            </button>
          </div>
          
          <div className="space-y-2">
            {shortcuts.map((shortcut, index) => (
              <div key={index} className="flex items-center justify-between py-2.5 border-b border-white/5 last:border-0">
                <span className="text-sm text-slate-300 pr-4">{shortcut.action}</span>
                <kbd className="px-3 py-1.5 bg-gradient-to-br from-blue-600/30 to-blue-700/30 border border-blue-400/30 rounded-lg text-sm font-semibold text-blue-200 shadow-md min-w-[140px] text-center">
                  {shortcut.key}
                </kbd>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-4 border-t border-white/10">
            <p className="text-xs text-slate-500">
              {t(language, 'shortcuts.tip')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

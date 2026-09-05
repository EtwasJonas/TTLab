export type Language = 'de' | 'en';

export const translations = {
  de: {
    // Dashboard
    'dashboard.total_matches': 'Matches',
    'dashboard.analyzed': 'Analysiert',
    'dashboard.active': 'Aktiv',
    
    // Match List
    'match.filter.all': 'Alle',
    'match.filter.wins': 'Siege',
    'match.filter.losses': 'Niederlagen',
    'match.filter.draws': 'Unentschieden',
    
    // Match Detail
    'match.detail.player': 'Eigener Name',
    'match.detail.opponent': 'Gegner',
    'match.detail.score': 'Spielstand',
    'match.detail.date': 'Datum',
    'match.detail.notes': 'Notizen',
    'match.detail.edit': 'Bearbeiten',
    'match.detail.save': 'Metadaten speichern',
    'match.detail.cancel': 'Abbrechen',
    'match.detail.duration': 'Dauer',
    'match.detail.metadata': 'Match-Metadaten',
    'match.detail.title': 'Titel (optional)',
    'match.detail.title_placeholder': 'z.B. Training vs. Roboter oder Turnierfinale 2026',
    'match.detail.player_label': 'Spieler',
    'match.detail.opponent_label': 'Gegner',
    'match.detail.result_label': 'Resultat',
    'match.detail.score_label': 'Spielstand',
    'match.detail.win': '🟢 Sieg',
    'match.detail.loss': '🔴 Niederlage',
    'match.detail.draw': '🟡 Unentschieden',
    'match.result.unknown': 'Unbekannt',
    'match.result.win': 'Sieg',
    'match.result.loss': 'Niederlage',
    'match.result.draw': 'Unentschieden',
    
    // Table Setup
    'table_setup.title': 'Tischbereich markieren',
    'table_setup.description': 'Pausiere das Video an einer gut sichtbaren Stelle und klicke die vier Tischkanten direkt im Bild im Uhrzeigersinn an: oben links, oben rechts, unten rechts, unten links.',
    'table_setup.points_set': '{count}/4 Punkte gesetzt',
    'table_setup.reset': 'Punkte zurücksetzen',
    'table_setup.save': 'Tischbereich speichern',
    'table_setup.saving': 'Speichere...',
    
    // Analysis Status
    'analysis.pending.title': 'Analyse noch nicht gestartet',
    'analysis.pending.description': 'Das Video wurde hochgeladen, aber die Analyse wurde noch nicht gestartet.',
    'analysis.processing.title': 'Video wird analysiert',
    'analysis.processing.message': 'Analyse läuft...',
    'analysis.progress': 'Fortschritt',
    'analysis.tip': 'Die Analyse läuft im Hintergrund. Du kannst diese Seite verlassen und später zurückkommen.',
    'analysis.failed': '❌ Analyse fehlgeschlagen:',
    
    // Rally Timeline
    'rally.timeline.title': 'Rally Timeline',
    'rally.timeline.displayed': '{current} von {total} Rallys angezeigt',
    'rally.filter.all': 'Alle Rallys',
    'rally.filter.highlights': '⭐ Highlights',
    'rally.filter.accepted': '✅ Ballwechsel',
    'rally.filter.rejected': '❌ Kein Ballwechsel',
    'rally.auto_play.on': '▶ Auto-Play AN',
    'rally.auto_play.off': '⏸ Auto-Play AUS',
    'rally.play': '▶ Abspielen',
    'rally.no_clip': 'Kein Clip',
    'rally.highlight.mark': '☆ Als Highlight markieren',
    'rally.highlight.remove': '⭐ Highlight entfernen',
    
    // Rally Status
    'rally.status.accepted': '✅ Sicher',
    'rally.status.review': '⚠️ Prüfen',
    'rally.status.rejected': '❌ Verworfen',
    'rally.highlight': '⭐ Highlight',
    'shortcuts.title': 'Tastaturkürzel',
    'shortcuts.play_pause': 'Wiedergabe starten/pausieren',
    'shortcuts.prev_rally': 'Vorherige Rally',
    'shortcuts.next_rally': 'Nächste Rally',
    'shortcuts.back_10ms': '-10ms zurück',
    'shortcuts.forward_10ms': '+10ms vorwärts',
    'shortcuts.highlight': 'Highlight umschalten',
    'shortcuts.status_toggle': 'Sicher ↔ Entfernt',
    'shortcuts.notes': 'Notizen fokussieren',
    'shortcuts.loop': 'Endlosschleife ein/aus',
    'shortcuts.speed_025': '0.25x Geschwindigkeit',
    'shortcuts.speed_05': '0.5x Geschwindigkeit',
    'shortcuts.speed_10': '1.0x Geschwindigkeit',
    'shortcuts.speed_15': '1.5x Geschwindigkeit',
    'shortcuts.tip': 'Hinweis: Shortcuts funktionieren nur, wenn das Video ausgewählt ist und nicht im Notiz-Feld getippt wird.',
    
    // Upload
    'upload.analyze_title': 'Neues Video analysieren',
    'upload.uploading': '⏳ Wird hochgeladen...',
    
    // Common
    'common.refresh': 'Aktualisieren',
    'common.back': '← Zurück',
    'common.status': 'Status',
    'common.last_updated': 'Zuletzt aktualisiert',
    'common.tip': 'Tipp',
    'rally.no_rallies_detected': 'Keine Rallys erkannt',
  },
  
  en: {
    // Dashboard
    'dashboard.total_matches': 'Matches',
    'dashboard.analyzed': 'Analyzed',
    'dashboard.active': 'Active',
    
    // Match List
    'match.filter.all': 'All',
    'match.filter.wins': 'Wins',
    'match.filter.losses': 'Losses',
    'match.filter.draws': 'Draws',
    
    // Match Detail
    'match.detail.player': 'Player Name',
    'match.detail.opponent': 'Opponent',
    'match.detail.score': 'Score',
    'match.detail.date': 'Date',
    'match.detail.notes': 'Notes',
    'match.detail.edit': 'Edit',
    'match.detail.save': 'Save metadata',
    'match.detail.cancel': 'Cancel',
    'match.detail.duration': 'Duration',
    'match.detail.metadata': 'Match Metadata',
    'match.detail.title': 'Title (optional)',
    'match.detail.title_placeholder': 'e.g. Training vs. Robot or Tournament Final 2026',
    'match.detail.player_label': 'Player',
    'match.detail.opponent_label': 'Opponent',
    'match.detail.result_label': 'Result',
    'match.detail.score_label': 'Score',
    'match.detail.win': '🟢 Win',
    'match.detail.loss': '🔴 Loss',
    'match.detail.draw': '🟡 Draw',
    'match.result.unknown': 'Unknown',
    'match.result.win': 'Win',
    'match.result.loss': 'Loss',
    'match.result.draw': 'Draw',
    
    // Table Setup
    'table_setup.title': 'Mark Table Area',
    'table_setup.description': 'Pause the video at a clearly visible frame and click the four table edges in clockwise order: top-left, top-right, bottom-right, bottom-left.',
    'table_setup.points_set': '{count}/4 points set',
    'table_setup.reset': 'Reset points',
    'table_setup.save': 'Save table area',
    'table_setup.saving': 'Saving...',
    
    // Analysis Status
    'analysis.pending.title': 'Analysis not started',
    'analysis.pending.description': 'The video has been uploaded, but analysis hasn\'t started yet.',
    'analysis.processing.title': 'Analyzing video',
    'analysis.processing.message': 'Analysis in progress...',
    'analysis.progress': 'Progress',
    'analysis.tip': 'Analysis runs in the background. You can leave this page and return later.',
    'analysis.failed': '❌ Analysis failed:',
    
    // Rally Timeline
    'rally.timeline.title': 'Rally Timeline',
    'rally.timeline.displayed': 'Showing {current} of {total} rallies',
    'rally.filter.all': 'All Rallies',
    'rally.filter.highlights': '⭐ Highlights',
    'rally.filter.accepted': '✅ Ball Changes',
    'rally.filter.rejected': '❌ No Rally',
    'rally.auto_play.on': '▶ Auto-Play ON',
    'rally.auto_play.off': '⏸ Auto-Play OFF',
    'rally.play': '▶ Play',
    'rally.no_clip': 'No clip',
    'rally.highlight.mark': '☆ Mark as Highlight',
    'rally.highlight.remove': '⭐ Remove Highlight',
    
    // Rally Status
    'rally.status.accepted': '✅ Confirmed',
    'rally.status.review': '⚠️ Review',
    'rally.status.rejected': '❌ Rejected',
    'rally.highlight': '⭐ Highlight',
    'shortcuts.title': 'Keyboard Shortcuts',
    'shortcuts.play_pause': 'Play/Pause video',
    'shortcuts.prev_rally': 'Previous rally',
    'shortcuts.next_rally': 'Next rally',
    'shortcuts.back_10ms': '-10ms backward',
    'shortcuts.forward_10ms': '+10ms forward',
    'shortcuts.highlight': 'Toggle highlight',
    'shortcuts.status_toggle': 'Confirm ↔ Reject',
    'shortcuts.notes': 'Focus notes',
    'shortcuts.loop': 'Loop on/off',
    'shortcuts.speed_025': '0.25x speed',
    'shortcuts.speed_05': '0.5x speed',
    'shortcuts.speed_10': '1.0x speed',
    'shortcuts.speed_15': '1.5x speed',
    'shortcuts.tip': 'Note: Shortcuts only work when video is selected and not typing in notes field.',
    
    // Upload
    'upload.analyze_title': 'Analyze New Video',
    'upload.uploading': '⏳ Uploading...',
    
    // Common
    'common.refresh': 'Refresh',
    'common.back': '← Back',
    'common.status': 'Status',
    'common.last_updated': 'Last updated',
    'common.tip': 'Tip',
    'rally.no_rallies_detected': 'No rallies detected',
  },
};

export function t(lang: Language, key: string, params?: Record<string, string | number>): string {
  const translation = translations[lang][key as keyof typeof translations.de] || key;
  if (!params) return translation;
  
  return Object.entries(params).reduce(
    (result, [paramKey, value]) => result.replace(`{${paramKey}}`, String(value)),
    translation
  );
}

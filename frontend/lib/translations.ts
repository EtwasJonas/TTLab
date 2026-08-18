export type Language = 'de' | 'en';

export const translations = {
  de: {
    // Navigation & Header
    'nav.dashboard': 'Dashboard',
    'nav.matches': 'Matches',
    'nav.settings': 'Einstellungen',
    'lang.switch': 'EN',
    
    // Dashboard
    'dashboard.title': 'TTLab Dashboard',
    'dashboard.total_matches': 'Matches',
    'dashboard.analyzed': 'Analysiert',
    'dashboard.active': 'Aktiv',
    'dashboard.highlights': 'Highlights',
    'dashboard.upload_video': 'Video hochladen',
    
    // Match List
    'match.list.title': 'Alle Matches',
    'match.filter.all': 'Alle',
    'match.filter.wins': 'Siege',
    'match.filter.losses': 'Niederlagen',
    'match.no_matches': 'Keine Matches gefunden',
    'match.delete': 'Löschen',
    'match.analyze': 'Analysieren',
    
    // Match Detail
    'match.detail.title': 'Match-Details',
    'match.detail.player': 'Eigener Name',
    'match.detail.opponent': 'Gegner',
    'match.detail.result': 'Ergebnis',
    'match.detail.score': 'Spielstand',
    'match.detail.date': 'Datum',
    'match.detail.notes': 'Notizen',
    'match.detail.edit': 'Bearbeiten',
    'match.detail.save': 'Speichern',
    'match.detail.cancel': 'Abbrechen',
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
    'analysis.pending.start': '▶️ Analyse jetzt starten',
    'analysis.processing.title': 'Video wird analysiert',
    'analysis.processing.message': 'Analyse läuft...',
    'analysis.progress': 'Fortschritt',
    'analysis.detected_rallies': 'Erkannte Rallys',
    'analysis.highlights': 'Highlights',
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
    'rally.keep': '✅ Behalten',
    'rally.reject': '❌ Kein Ballwechsel',
    'rally.no_clip': 'Kein Clip',
    'rally.highlight.set': '⭐ Highlight setzen',
    'rally.highlight.mark': '☆ Als Highlight markieren',
    'rally.step_back': '⏪ -100ms',
    'rally.step_forward': '+100ms ⏩',
    'rally.keyboard_tip': 'Pfeiltasten links/rechts funktionieren auch',
    
    // Rally Status
    'rally.status.accepted': '✅ Sicher',
    'rally.status.review': '⚠️ Prüfen',
    'rally.status.rejected': '❌ Verworfen',
    'rally.highlight': '⭐ Highlight',
    
    // Upload
    'upload.title': 'Video hochladen',
    'upload.analyze_title': 'Neues Video analysieren',
    'upload.drag_drop': 'Video hierher ziehen oder klicken zum Auswählen',
    'upload.supported_formats': 'Unterstützte Formate: MP4, AVI, MOV, MKV, WebM',
    'upload.start': 'Upload starten',
    'upload.uploading': '⏳ Wird hochgeladen...',
    
    // Common
    'common.loading': 'Lade...',
    'common.error': 'Fehler',
    'common.refresh': '🔄 Aktualisieren',
    'common.back': '← Zurück',
    'common.close': 'Schließen',
    'common.duration': 'Dauer',
    'common.status': 'Status',
    'common.last_updated': 'Zuletzt aktualisiert',
    'common.tip': 'Tipp',
    'rally.no_rallies_detected': 'Keine Rallys erkannt',
  },
  
  en: {
    // Navigation & Header
    'nav.dashboard': 'Dashboard',
    'nav.matches': 'Matches',
    'nav.settings': 'Settings',
    'lang.switch': 'DE',
    
    // Dashboard
    'dashboard.title': 'TTLab Dashboard',
    'dashboard.total_matches': 'Matches',
    'dashboard.analyzed': 'Analyzed',
    'dashboard.active': 'Active',
    'dashboard.highlights': 'Highlights',
    'dashboard.upload_video': 'Upload Video',
    
    // Match List
    'match.list.title': 'All Matches',
    'match.filter.all': 'All',
    'match.filter.wins': 'Wins',
    'match.filter.losses': 'Losses',
    'match.no_matches': 'No matches found',
    'match.delete': 'Delete',
    'match.analyze': 'Analyze',
    
    // Match Detail
    'match.detail.title': 'Match Details',
    'match.detail.player': 'Player Name',
    'match.detail.opponent': 'Opponent',
    'match.detail.result': 'Result',
    'match.detail.score': 'Score',
    'match.detail.date': 'Date',
    'match.detail.notes': 'Notes',
    'match.detail.edit': 'Edit',
    'match.detail.save': 'Save',
    'match.detail.cancel': 'Cancel',
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
    'analysis.pending.start': '▶️ Start Analysis Now',
    'analysis.processing.title': 'Analyzing video',
    'analysis.processing.message': 'Analysis in progress...',
    'analysis.progress': 'Progress',
    'analysis.detected_rallies': 'Detected Rallies',
    'analysis.highlights': 'Highlights',
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
    'rally.keep': '✅ Keep',
    'rally.reject': '❌ Reject Rally',
    'rally.no_clip': 'No clip',
    'rally.highlight.set': '⭐ Set Highlight',
    'rally.highlight.mark': '☆ Mark as Highlight',
    'rally.step_back': '⏪ -100ms',
    'rally.step_forward': '+100ms ⏩',
    'rally.keyboard_tip': 'Arrow keys left/right also work',
    
    // Rally Status
    'rally.status.accepted': '✅ Confirmed',
    'rally.status.review': '⚠️ Review',
    'rally.status.rejected': '❌ Rejected',
    'rally.highlight': '⭐ Highlight',
    
    // Upload
    'upload.title': 'Upload Video',
    'upload.analyze_title': 'Analyze New Video',
    'upload.drag_drop': 'Drag & drop video here or click to select',
    'upload.supported_formats': 'Supported formats: MP4, AVI, MOV, MKV, WebM',
    'upload.start': 'Start Upload',
    'upload.uploading': '⏳ Uploading...',
    
    // Common
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.refresh': '🔄 Refresh',
    'common.back': '← Back',
    'common.close': 'Close',
    'common.duration': 'Duration',
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

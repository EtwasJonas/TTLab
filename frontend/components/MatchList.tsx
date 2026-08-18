"use client";

interface Match {
  id: number;
  filename: string;
  original_filename: string;
  duration: number | null;
  upload_date: string;
  status: string;
  error_message: string | null;
  match_date: string | null;
  player_name: string | null;
  opponent_name: string | null;
  result: string | null;
  score: string | null;
  notes: string | null;
}

interface MatchListProps {
  matches: Match[];
  onSelectMatch: (matchId: number) => void;
  onDeleteMatch?: (matchId: number) => void;
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case "completed":
      return <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">Fertig</span>;
    case "processing":
      return <span className="px-2 py-1 bg-yellow-900/50 text-yellow-300 rounded text-xs animate-pulse">Verarbeite...</span>;
    case "failed":
      return <span className="px-2 py-1 bg-red-900/50 text-red-300 rounded text-xs">Fehler</span>;
    default:
      return <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">Wartend</span>;
  }
};

const formatDuration = (seconds: number | null) => {
  if (!seconds) return "-";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export default function MatchList({ matches, onSelectMatch, onDeleteMatch }: MatchListProps) {
  if (matches.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-lg">Noch keine Matches vorhanden</p>
        <p className="text-sm mt-2">Lade dein erstes Video hoch, um mit der Analyse zu beginnen</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-widest text-blue-300">Library</p>
          <h2 className="mt-1 text-2xl font-bold">Deine Matches</h2>
        </div>
        <span className="text-sm text-slate-500">{matches.length} Einträge</span>
      </div>
      
      <div className="grid gap-4">
        {matches.map((match) => (
          <div
            key={match.id}
            onClick={() => onSelectMatch(match.id)}
            className={`rounded-2xl bg-white/[0.06] p-5 border cursor-pointer transition-all hover:-translate-y-0.5 hover:bg-white/[0.09]
              ${match.status === "failed" ? "border-red-700/70" : "border-white/10 hover:border-blue-400/50"}
            `}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="font-semibold text-white">{match.original_filename}</h3>
                  {getStatusBadge(match.status)}
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-400">
                  <span>📅 {formatDate(match.upload_date)}</span>
                  <span>⏱️ {formatDuration(match.duration)}</span>
                </div>
                {match.error_message && (
                  <p className="mt-2 text-sm text-red-400">{match.error_message}</p>
                )}
              </div>
              
              <div className="flex items-center gap-4">
                <button 
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectMatch(match.id);
                  }}
                  className="text-blue-400 hover:text-blue-300 text-sm"
                >
                  Anzeigen →
                </button>
                {onDeleteMatch && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Möchtest du "${match.original_filename}" wirklich löschen?`)) {
                        onDeleteMatch(match.id);
                      }
                    }}
                    className="text-red-400 hover:text-red-300 text-sm"
                    title="Löschen"
                  >
                    🗑️ Löschen
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

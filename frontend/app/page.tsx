"use client";

import { useState, useEffect } from "react";
import VideoUpload from "@/components/VideoUpload";
import MatchList from "@/components/MatchList";
import MatchDetail from "@/components/MatchDetail";
import { useLanguage } from "../lib/LanguageContext";
import { t } from "../lib/translations";

interface Match {
  id: number;
  filename: string;
  original_filename: string;
  duration: number | null;
  upload_date: string;
  status: string;
  error_message: string | null;
  progress: number;
  progress_message: string | null;
  match_date: string | null;
  player_name: string | null;
  opponent_name: string | null;
  result: string | null;
  score: string | null;
  notes: string | null;
  table_points: string | null;
}

interface Rally {
  id: number;
  match_id: number;
  start_time: number;
  end_time: number;
  duration: number;
  clip_filename: string | null;
  is_highlight: boolean;
  highlight_score: number;
  validation_status: "accepted" | "review" | "rejected";
  confidence: number;
  impact_count: number;
  user_marked_highlight: boolean;
}

export default function Home() {
  const { language } = useLanguage();
  const [matches, setMatches] = useState<Match[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null);
  const [rallies, setRallies] = useState<Rally[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [isPlayingClip, setIsPlayingClip] = useState(false);
  const [libraryFilter, setLibraryFilter] = useState("all");
  const completedMatches = matches.filter((match) => match.status === "completed").length;
  const processingMatches = matches.filter((match) => match.status === "processing").length;
  const visibleMatches = matches.filter((match) => {
    if (libraryFilter === "all") return true;
    if (libraryFilter === "processing") return match.status === "processing";
    if (!match.result || match.result === "unknown") return false;
    return match.result === libraryFilter;
  });

  const fetchMatches = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/matches");
      if (response.ok) {
        const data = await response.json();
        setMatches(data);
      }
    } catch (error) {
      console.error("Error loading matches:", error);
    }
  };

  const fetchMatchDetails = async (matchId: number) => {
    setLoading(true);
    try {
      const rallyResponse = await fetch(`http://localhost:8000/api/matches/${matchId}/rallies`);
      if (rallyResponse.ok) {
        const data = await rallyResponse.json();
        setRallies(data.rallies);
      }
      
      const matchResponse = await fetch(`http://localhost:8000/api/matches/${matchId}`);
      if (matchResponse.ok) {
        const matchData = await matchResponse.json();
        setSelectedMatch(matchData);
        setLastUpdated(new Date());
      }
    } catch (error) {
      console.error("Fehler beim Laden der Match-Details:", error);
    } finally {
      setLoading(false);
    }
  };

  const startAnalysis = async (matchId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/matches/${matchId}/analyze`, { method: "POST" });
      if (response.ok) {
        setTimeout(() => fetchMatchDetails(matchId), 1000);
      }
    } catch (error) {
      console.error("Fehler beim Starten der Analyse:", error);
    }
  };

  const deleteMatch = async (matchId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/matches/${matchId}`, { method: "DELETE" });
      if (response.ok) {
        fetchMatches();
        if (selectedMatch?.id === matchId) {
          setSelectedMatch(null);
          setRallies([]);
        }
      }
    } catch (error) {
      console.error("Fehler beim Löschen:", error);
    }
  };

  useEffect(() => {
    fetchMatches();
  }, []);

  useEffect(() => {
    if (selectedMatch && selectedMatch.status === "processing" && !isPlayingClip) {
      const refreshInterval = setInterval(() => {
        fetchMatchDetails(selectedMatch.id);
      }, 3000);
      return () => clearInterval(refreshInterval);
    }
  }, [selectedMatch, isPlayingClip]);

  return (
    <div className="space-y-8">
      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-5 shadow-2xl shadow-blue-950/20">
          <p className="text-xs uppercase tracking-widest text-slate-500">{t(language, 'dashboard.total_matches')}</p>
          <p className="mt-2 text-3xl font-bold">{matches.length}</p>
          <p className="mt-1 text-sm text-slate-400">{language === 'de' ? 'deine Video-Bibliothek' : 'your video library'}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-5">
          <p className="text-xs uppercase tracking-widest text-slate-500">{t(language, 'dashboard.analyzed')}</p>
          <p className="mt-2 text-3xl font-bold text-emerald-300">{completedMatches}</p>
          <p className="mt-1 text-sm text-slate-400">{language === 'de' ? 'fertige Auswertungen' : 'completed analyses'}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-5">
          <p className="text-xs uppercase tracking-widest text-slate-500">{t(language, 'dashboard.active')}</p>
          <p className="mt-2 text-3xl font-bold text-amber-300">{processingMatches}</p>
          <p className="mt-1 text-sm text-slate-400">{language === 'de' ? 'laufende Analysen' : 'running analyses'}</p>
        </div>
      </section>
      <VideoUpload onUploadComplete={fetchMatches} />
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-slate-400">{language === 'de' ? 'Bibliothek filtern:' : 'Filter library:'}</span>
        {[['all', t(language, 'match.filter.all')], ['win', t(language, 'match.filter.wins')], ['loss', t(language, 'match.filter.losses')], ['processing', language === 'de' ? 'In Arbeit' : 'In Progress']].map(([value, label]) => (
          <button
            key={value}
            onClick={() => setLibraryFilter(value)}
            className={`rounded-full px-3 py-1.5 text-sm transition ${libraryFilter === value ? 'bg-blue-500 text-white' : 'bg-white/[0.06] text-slate-400 hover:bg-white/[0.12]'}`}
          >
            {label}
          </button>
        ))}
      </div>
      
      {selectedMatch && (
        <button
          onClick={() => {
            setSelectedMatch(null);
            setRallies([]);
          }}
          className="text-blue-400 hover:text-blue-300"
        >
          ← {t(language, 'common.back')}
        </button>
      )}

      {selectedMatch ? (
        <MatchDetail 
          match={selectedMatch} 
          rallies={rallies} 
          loading={loading}
          onRefresh={() => fetchMatchDetails(selectedMatch.id)}
          onStartAnalysis={() => startAnalysis(selectedMatch.id)}
          lastUpdated={lastUpdated}
          isPlayingClip={isPlayingClip}
          onClipPlayStart={() => setIsPlayingClip(true)}
          onClipPlayEnd={() => setIsPlayingClip(false)}
        />
      ) : (
        <MatchList 
          matches={visibleMatches} 
          onSelectMatch={fetchMatchDetails}
          onDeleteMatch={deleteMatch}
        />
      )}
    </div>
  );
}

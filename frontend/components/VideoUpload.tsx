"use client";

import { useState, useRef } from "react";
import { useLanguage } from "../lib/LanguageContext";
import { t } from "../lib/translations";

interface VideoUploadProps {
  onUploadComplete: () => void;
}

export default function VideoUpload({ onUploadComplete }: VideoUploadProps) {
  const { language } = useLanguage();
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const validTypes = ["video/mp4", "video/avi", "video/quicktime", "video/webm", "video/x-matroska"];
    const hasValidExtension = /\.(mp4|avi|mov|mkv|webm)$/i.test(file.name);
    
    if (!hasValidExtension) {
      setError(language === 'de' 
        ? "Ungültiges Format. Bitte MP4, AVI, MOV, MKV oder WebM verwenden." 
        : "Invalid format. Please use MP4, AVI, MOV, MKV or WebM.");
      return;
    }

    setUploading(true);
    setError(null);
    setMessage(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(`✅ ${data.message}`);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
        onUploadComplete();
      } else {
        setError(`❌ ${language === 'de' ? 'Fehler:' : 'Error:'} ${data.detail || (language === 'de' ? "Upload fehlgeschlagen" : "Upload failed")}`);
      }
    } catch (err) {
      setError(language === 'de' 
        ? "❌ Verbindung zum Server fehlgeschlagen. Ist das Backend gestartet?" 
        : "❌ Connection to server failed. Is the backend running?");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h2 className="text-xl font-semibold mb-4">{t(language, 'upload.analyze_title')}</h2>
      
      <div className="flex items-center gap-4">
        <label className="flex-1">
          <input
            ref={fileInputRef}
            type="file"
            accept=".mp4,.avi,.mov,.mkv,.webm"
            onChange={handleFileChange}
            disabled={uploading}
            className="block w-full text-sm text-gray-400
              file:mr-4 file:py-2 file:px-4
              file:rounded file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-600 file:text-white
              hover:file:bg-blue-700
              disabled:file:opacity-50
              cursor-pointer"
          />
        </label>
        
        {uploading && (
          <span className="text-blue-400">{t(language, 'upload.uploading')}</span>
        )}
      </div>

      {message && (
        <div className="mt-4 p-3 bg-green-900/30 border border-green-700 rounded text-green-300">
          {message}
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-300">
          {error}
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { api } from "@/lib/api";

interface ReportOut {
  id: string;
  url: string;
  region: string;
  created_at: string;
  title?: string | null;
}

const REGION_LABELS: Record<string, string> = {
  MSK: "Москва",
  SPB: "Санкт-Петербург",
  RU: "Россия",
  BY: "Беларусь",
  KZ: "Казахстан",
  US: "США",
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" });
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
}

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<ReportOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getReports()
      .then((data) => setReports(data as ReportOut[]))
      .catch((err) => setError(err.message || "Ошибка загрузки истории"));
  }, []);

  return (
    <main className="min-h-screen px-4 py-10 max-w-4xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-8"
      >
        <button
          onClick={() => router.push("/dashboard")}
          className="text-gray-500 hover:text-gray-200 text-sm mb-4 flex items-center gap-1.5 transition-colors group"
        >
          <span className="group-hover:-translate-x-0.5 transition-transform">←</span>
          Новый анализ
        </button>
        <h1 className="text-3xl font-bold text-gray-50 mb-1">История отчётов</h1>
        <p className="text-gray-400 text-sm">Последние 50 сохранённых анализов</p>
      </motion.div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-red-300 text-sm mb-6">
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {reports === null && !error && (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="rounded-xl border border-white/10 bg-white/5 h-20 animate-pulse" />
          ))}
        </div>
      )}

      {/* Empty state */}
      {reports !== null && reports.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <div className="text-5xl mb-4">📊</div>
          <h2 className="text-xl font-semibold text-gray-200 mb-2">Нет сохранённых отчётов</h2>
          <p className="text-gray-400 text-sm mb-6">Запустите анализ сайта — отчёт сохранится автоматически</p>
          <button
            onClick={() => router.push("/dashboard")}
            className="rounded-xl px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
          >
            Запустить анализ
          </button>
        </motion.div>
      )}

      {/* Reports list */}
      {reports !== null && reports.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="space-y-3"
        >
          {reports.map((r, i) => (
            <motion.button
              key={r.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              onClick={() => router.push(`/results?id=${r.id}`)}
              className="w-full text-left rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 hover:border-indigo-500/40 px-5 py-4 transition-all group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="text-gray-100 font-medium truncate group-hover:text-indigo-300 transition-colors">
                    {r.title || r.url}
                  </div>
                  <div className="text-gray-500 text-sm mt-0.5 truncate">{r.url}</div>
                </div>
                <div className="flex-shrink-0 text-right">
                  <div className="text-xs text-gray-400">{formatDate(r.created_at)}</div>
                  <div className="text-xs text-gray-600">{formatTime(r.created_at)}</div>
                  <div className="mt-1">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-600/20 text-indigo-400 border border-indigo-500/20">
                      {REGION_LABELS[r.region] ?? r.region}
                    </span>
                  </div>
                </div>
              </div>
            </motion.button>
          ))}
        </motion.div>
      )}
    </main>
  );
}

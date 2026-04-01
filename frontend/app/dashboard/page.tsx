"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import InputForm, { type FormValues } from "@/components/InputForm";
import { api } from "@/lib/api";
import type { AnalyzeResponse } from "@/types/api";

const stepsData = [
  { n: "01", label: "Парсинг сайта", desc: "Определяем нишу, продукты и ключевые темы" },
  { n: "02", label: "Семантика", desc: "Кластеризуем ключевые слова по группам" },
  { n: "03", label: "Кампании", desc: "Генерируем объявления и медиаплан" },
];

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(values: FormValues) {
    setLoading(true);
    setError("");
    try {
      const payload: Record<string, unknown> = {
        url: values.url,
        region: values.region,
        currency: values.currency || "RUB",
      };
      if (values.city) payload.city = values.city;
      if (values.niche) payload.niche = values.niche;
      // Only send budget if user entered it manually (not auto mode)
      if (!values.auto_budget && values.budget) payload.budget = parseFloat(values.budget);
      if (values.ga_ym_metrics) {
        try {
          payload.ga_ym_metrics = JSON.parse(values.ga_ym_metrics);
        } catch {
          // ignore invalid JSON
        }
      }

      const result = await api.analyze(payload) as AnalyzeResponse;
      sessionStorage.setItem("ppc_report", JSON.stringify(result));
      router.push("/results");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ошибка анализа. Проверьте URL и попробуйте снова.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 py-20">

      {/* Hero */}
      <motion.div
        className="text-center mb-12 max-w-2xl"
        initial={{ opacity: 0, y: -24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/30 rounded-full px-4 py-1.5 text-indigo-300 text-sm font-medium mb-6">
          <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
          PPC Master Tool — AI-powered
        </div>

        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4 leading-tight">
          Автоматический анализ{" "}
          <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
            PPC-кампаний
          </span>
        </h1>
        <p className="text-xl text-gray-400 leading-relaxed">
          Введите URL сайта — получите готовую стратегию для Яндекс, Google и VK с медиапланом и вариантами объявлений.
        </p>
      </motion.div>

      {/* Form */}
      <InputForm onSubmit={handleSubmit} loading={loading} />

      {/* Error */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 bg-red-500/10 border border-red-500/30 rounded-xl px-5 py-4 text-red-300 text-base max-w-2xl w-full flex items-start gap-3"
        >
          <span className="text-xl leading-none mt-0.5">⚠</span>
          <span>{error}</span>
        </motion.div>
      )}

      {/* Steps */}
      <motion.div
        className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-5 max-w-2xl w-full"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35, duration: 0.5 }}
      >
        {stepsData.map((s, i) => (
          <motion.div
            key={s.n}
            className="glass-card rounded-2xl p-6 text-center"
            whileHover={{ scale: 1.03, transition: { duration: 0.2 } }}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + i * 0.1, duration: 0.4 }}
          >
            <div className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent mb-2">
              {s.n}
            </div>
            <div className="text-base font-semibold text-gray-100 mb-1">{s.label}</div>
            <div className="text-sm text-gray-500 leading-relaxed">{s.desc}</div>
          </motion.div>
        ))}
      </motion.div>
    </main>
  );
}

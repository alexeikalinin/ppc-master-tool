"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import ResultsTable from "@/components/ResultsTable";
import ForecastChart from "@/components/ForecastChart";
import type { AnalyzeResponse, AiSummary, Keyword, Campaign, MediaPlanRow, NicheInsight, BudgetRecommendation } from "@/types/api";
import { api } from "@/lib/api";

type Tab = "overview" | "keywords" | "campaigns" | "mediaplan";

const STAT_COLORS = [
  "border-l-indigo-500",
  "border-l-violet-500",
  "border-l-emerald-500",
  "border-l-amber-500",
];

export default function ResultsPage() {
  return (
    <Suspense fallback={null}>
      <ResultsPageInner />
    </Suspense>
  );
}

function ResultsPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [report, setReport] = useState<AnalyzeResponse | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [pdfLoading, setPdfLoading] = useState<null | 1 | 3>(null);
  const [csvLoading, setCsvLoading] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);

  useEffect(() => {
    const reportId = searchParams.get("id");
    if (reportId) {
      api.getReport(reportId)
        .then((data) => setReport(data as AnalyzeResponse))
        .catch(() => router.replace("/dashboard"));
      return;
    }
    const raw = sessionStorage.getItem("ppc_report");
    if (!raw) { router.replace("/dashboard"); return; }
    try { setReport(JSON.parse(raw)); }
    catch { router.replace("/dashboard"); }
  }, [router, searchParams]);

  function handleCopyLink() {
    if (!report?.report_id) return;
    const url = `${window.location.origin}/results?id=${report.report_id}`;
    navigator.clipboard.writeText(url).then(() => {
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
    });
  }

  if (!report) return null;

  const TABS: { id: Tab; label: string }[] = [
    { id: "overview",   label: "Обзор" },
    { id: "keywords",   label: `Ключи (${report.keywords.length})` },
    { id: "campaigns",  label: `Кампании (${report.campaigns.length})` },
    { id: "mediaplan",  label: "Медиаплан" },
  ];

  return (
    <main className="min-h-screen px-4 py-10 max-w-6xl mx-auto">

      {/* ── Header ── */}
      <motion.div
        className="flex items-start justify-between mb-10 flex-wrap gap-4"
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div>
          <div className="flex items-center gap-3 mb-3">
            <button
              onClick={() => router.push("/dashboard")}
              className="text-gray-500 hover:text-gray-200 text-sm flex items-center gap-1.5 transition-colors group"
            >
              <span className="group-hover:-translate-x-0.5 transition-transform">←</span>
              Новый анализ
            </button>
            <span className="text-gray-700">|</span>
            <button
              onClick={() => router.push("/reports")}
              className="text-gray-500 hover:text-gray-200 text-sm transition-colors"
            >
              История отчётов
            </button>
            {report?.report_id && (
              <>
                <span className="text-gray-700">|</span>
                <button
                  onClick={handleCopyLink}
                  className="text-emerald-400 hover:text-emerald-300 text-sm flex items-center gap-1.5 transition-colors"
                >
                  {linkCopied ? "✓ Ссылка скопирована" : "🔗 Скопировать ссылку"}
                </button>
              </>
            )}
          </div>
          <h1 className="text-3xl font-bold text-gray-50">{report.site.title}</h1>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-indigo-400 text-base font-medium">{report.site.niche}</span>
            <span className="text-gray-700">•</span>
            <span className="text-gray-400 text-base">{report.site.description.slice(0, 80)}</span>
          </div>
        </div>

        <div className="flex gap-2">
          {([1, 3] as const).map((v) => (
            <motion.button
              key={v}
              onClick={() => handleKpDownload(report, v, setPdfLoading)}
              disabled={pdfLoading !== null}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className={`rounded-xl px-4 py-2.5 text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed border ${
                v === 1
                  ? "bg-indigo-600/20 border-indigo-500/40 text-indigo-300 hover:bg-indigo-600/30"
                  : "bg-white/5 border-white/10 text-gray-300 hover:text-white hover:bg-white/10"
              }`}
            >
              {pdfLoading === v ? "Генерация…" : `⬇ КП Вариант ${v}`}
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* ── AI Assistant ── */}
      {report.ai_summary && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05, duration: 0.4 }}
          className="mb-8"
        >
          <AiAssistantBlock summary={report.ai_summary} />
        </motion.div>
      )}

      {/* ── Niche Insight ── */}
      {report.niche_insight && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.07, duration: 0.4 }}
          className="mb-6"
        >
          <NicheInsightBlock insight={report.niche_insight} />
        </motion.div>
      )}

      {/* ── Budget Recommendation ── */}
      {report.budget_recommendation && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.09, duration: 0.4 }}
          className="mb-8"
        >
          <BudgetRecommendationBlock rec={report.budget_recommendation} />
        </motion.div>
      )}

      {/* ── Вопрос по отчёту (ответы только по данным) ── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.11, duration: 0.4 }}
        className="mb-8"
      >
        <AssistantChatBlock report={report} />
      </motion.div>

      {/* ── Stat cards ── */}
      <motion.div
        className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.5 }}
      >
        {[
          { label: "Ключевых слов",     value: report.keywords.length },
          { label: "Семантических групп", value: report.groups.length },
          { label: "Кампаний",           value: report.campaigns.length },
          { label: "Конверсий / мес",    value: report.media_plan.total_conversions.toFixed(1) },
        ].map((card, i) => (
          <motion.div
            key={card.label}
            className={`stat-card ${STAT_COLORS[i]} rounded-xl p-5`}
            whileHover={{ scale: 1.02, transition: { duration: 0.15 } }}
          >
            <div className="text-3xl font-bold text-white">{card.value}</div>
            <div className="text-sm text-gray-400 mt-1.5 leading-snug">{card.label}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* ── Tab bar ── */}
      <div className="flex gap-0 mb-8 border-b border-white/10">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-5 py-3 text-base font-medium transition-colors -mb-px border-b-2 ${
              tab === t.id
                ? "border-indigo-500 text-indigo-300"
                : "border-transparent text-gray-500 hover:text-gray-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab content ── */}
      <motion.div
        key={tab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
      >
        {tab === "overview"  && <OverviewTab  report={report} csvLoading={csvLoading} setCsvLoading={setCsvLoading} />}
        {tab === "keywords"  && <KeywordsTab  keywords={report.keywords} />}
        {tab === "campaigns" && <CampaignsTab campaigns={report.campaigns} />}
        {tab === "mediaplan" && <MediaPlanTab report={report} />}
      </motion.div>
    </main>
  );
}

/* ────────────────────────────────────────── */

function SectionCard({ title, children, action }: { title: string; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="glass-card rounded-2xl p-6 sm:p-8">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-xl font-semibold text-gray-100">{title}</h2>
        {action && <div>{action}</div>}
      </div>
      {children}
    </div>
  );
}

/* ── Overview ── */
function OverviewTab({ report, csvLoading, setCsvLoading }: { report: AnalyzeResponse; csvLoading: boolean; setCsvLoading: (v: boolean) => void }) {
  return (
    <div className="space-y-6">
      {/* Audience */}
      <SectionCard title="Целевая аудитория">
        <p className="text-gray-300 text-base leading-relaxed mb-6">{report.audience.summary}</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {report.audience.targeting.map((t) => (
            <div key={t.platform} className="bg-white/[0.04] border border-white/8 rounded-xl p-4">
              <div className="text-indigo-300 font-semibold capitalize text-base mb-2">{t.platform}</div>
              <div className="space-y-1">
                <div className="text-sm text-gray-400">
                  <span className="text-gray-300">Возраст:</span> {t.age_range}
                </div>
                <div className="text-sm text-gray-400">
                  <span className="text-gray-300">Пол:</span> {t.gender}
                </div>
                <div className="text-sm text-gray-500 mt-2 leading-relaxed">
                  {t.interests.slice(0, 3).join(", ")}
                </div>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      {/* Competitors */}
      <SectionCard title="Конкуренты">
        <div className="flex flex-wrap gap-2">
          {report.competitors.map((c) => (
            <span
              key={c}
              className="bg-white/5 border border-white/10 rounded-full px-4 py-1.5 text-base text-gray-300 hover:bg-white/10 transition-colors"
            >
              {c}
            </span>
          ))}
        </div>
      </SectionCard>

      {/* Semantic groups */}
      <SectionCard
        title="Семантические группы"
        action={
          <button
            onClick={async () => {
              setCsvLoading(true);
              try { await api.exportKeywords(report, "csv"); }
              catch (e) { console.error(e); }
              finally { setCsvLoading(false); }
            }}
            disabled={csvLoading}
            className="flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/10 transition disabled:opacity-50"
          >
            {csvLoading ? "⏳" : "⬇️"} Экспорт CSV
          </button>
        }
      >
        <div className="space-y-4">
          {report.groups.map((g) => (
            <div key={g.name} className="bg-white/[0.03] border border-white/8 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-indigo-300 text-base">{g.name}</span>
                <span className="text-sm text-gray-500 bg-white/5 rounded-full px-3 py-0.5">
                  {g.keywords.length} кл. слов
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {g.keywords.slice(0, 6).map((kw) => (
                  <span key={kw.text} className="text-sm bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 rounded-md px-2.5 py-0.5">
                    {kw.text}
                  </span>
                ))}
              </div>
              <div className="text-sm text-gray-600">
                Минус-слова: {g.minus_words.slice(0, 5).join(", ")}
              </div>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}

/* ── Keywords ── */
function KeywordsTab({ keywords }: { keywords: Keyword[] }) {
  const sorted = [...keywords].sort((a, b) => b.frequency - a.frequency);
  return (
    <ResultsTable
      columns={[
        { key: "text", label: "Ключевое слово" },
        {
          key: "frequency",
          label: "Частота",
          render: (v) => Number(v).toLocaleString("ru"),
        },
        {
          key: "cpc",
          label: "CPC (₽)",
          render: (v) => `${Number(v).toFixed(2)} ₽`,
        },
        {
          key: "platform",
          label: "Платформа",
          render: (v) => {
            const p = String(v).toLowerCase();
            const cls = p.includes("yandex") ? "badge-yandex"
                      : p.includes("google") ? "badge-google"
                      : p.includes("vk")     ? "badge-vk"
                      : "bg-gray-700 text-gray-300 border border-white/10 badge-platform";
            return <span className={`badge-platform ${cls}`}>{v}</span>;
          },
        },
        {
          key: "seasonality",
          label: "Сезонность",
          render: (v) => {
            const n = Number(v);
            const color = n > 1.1 ? "text-emerald-400" : n < 0.9 ? "text-red-400" : "text-gray-500";
            return <span className={`font-mono ${color}`}>{n.toFixed(2)}x</span>;
          },
        },
      ]}
      data={sorted}
    />
  );
}

/* ── Campaigns ── */
function CampaignsTab({ campaigns }: { campaigns: Campaign[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="space-y-3">
      {campaigns.map((camp, idx) => (
        <motion.div
          key={camp.name}
          className="glass-card rounded-2xl overflow-hidden"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.04, duration: 0.3 }}
        >
          {/* Header row */}
          <button
            className="w-full flex items-center justify-between px-6 py-5 text-left hover:bg-white/[0.03] transition-colors"
            onClick={() => setExpanded(expanded === camp.name ? null : camp.name)}
          >
            <div className="flex items-center gap-3">
              <span
                className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
                  camp.type === "search"
                    ? "bg-indigo-500/10 text-indigo-300 border-indigo-500/30"
                    : "bg-teal-500/10 text-teal-300 border-teal-500/30"
                }`}
              >
                {camp.type}
              </span>
              <span className="text-base font-medium text-gray-100">{camp.name}</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <span className="text-gray-300 font-medium">{camp.budget.toFixed(0)} ₽</span>
              <span>CPC: {camp.avg_cpc.toFixed(0)} ₽</span>
              <motion.span
                animate={{ rotate: expanded === camp.name ? 180 : 0 }}
                transition={{ duration: 0.2 }}
                className="text-gray-600"
              >
                ▾
              </motion.span>
            </div>
          </button>

          {/* Ad variants */}
          {expanded === camp.name && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25 }}
              className="border-t border-white/5 px-6 py-5 space-y-3"
            >
              {camp.ad_variants.slice(0, 3).map((v, i) => (
                <div key={i} className="bg-white/[0.03] border border-white/8 rounded-xl p-4">
                  <div className="text-indigo-300 font-semibold text-base mb-1.5">{v.headline}</div>
                  <div className="text-gray-400 text-sm mb-3 leading-relaxed">{v.description}</div>
                  <div className="flex flex-wrap gap-2">
                    {v.quick_links.map((ql) => (
                      <span key={ql} className="text-xs border border-white/10 rounded-md px-2.5 py-1 text-gray-500 hover:text-gray-300 transition-colors">
                        {ql}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </motion.div>
          )}
        </motion.div>
      ))}
    </div>
  );
}

/* ── Media Plan ── */
function MediaPlanTab({ report }: { report: AnalyzeResponse }) {
  const currSym = CURRENCY_SYMBOLS[report.currency] ?? report.currency ?? "₽";
  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: "Общий бюджет",  value: `${report.media_plan.total_budget.toFixed(0)} ${currSym}`,   color: "text-indigo-300" },
          { label: "Конверсий / мес", value: report.media_plan.total_conversions.toFixed(1),              color: "text-emerald-300" },
          { label: "Средний CPA",   value: `${report.media_plan.avg_cpa.toFixed(0)} ${currSym}`,          color: "text-amber-300" },
        ].map((s) => (
          <motion.div
            key={s.label}
            className="glass-card rounded-2xl p-6 text-center"
            whileHover={{ scale: 1.02, transition: { duration: 0.15 } }}
          >
            <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-sm text-gray-500 mt-2">{s.label}</div>
          </motion.div>
        ))}
      </div>

      <ForecastChart rows={report.media_plan.rows} />

      <ResultsTable<MediaPlanRow>
        columns={[
          { key: "campaign_name", label: "Кампания" },
          {
            key: "platform",
            label: "Платформа",
            render: (v) => {
              const p = String(v).toLowerCase();
              const cls = p.includes("yandex") ? "badge-yandex"
                        : p.includes("google") ? "badge-google"
                        : p.includes("vk")     ? "badge-vk"
                        : "bg-gray-700 text-gray-300 border border-white/10 badge-platform";
              return <span className={`badge-platform ${cls}`}>{v}</span>;
            },
          },
          { key: "budget",      label: "Бюджет",     render: (v) => `${Number(v).toFixed(0)} ${currSym}` },
          { key: "avg_cpc",     label: "CPC",         render: (v) => `${Number(v).toFixed(2)} ${currSym}` },
          { key: "cr",          label: "CR",          render: (v) => `${(Number(v) * 100).toFixed(1)}%` },
          { key: "cpa",         label: "CPA",         render: (v) => `${Number(v).toFixed(0)} ${currSym}` },
          { key: "conversions", label: "Конверсии",   render: (v) => Number(v).toFixed(1) },
        ]}
        data={report.media_plan.rows}
      />
    </div>
  );
}

/* ── Чат: вопрос по отчёту (ответы только по данным) ── */

function AssistantChatBlock({ report }: { report: AnalyzeResponse }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAsk() {
    const q = question.trim();
    if (!q) return;
    setLoading(true);
    setError("");
    setAnswer(null);
    try {
      const res = await api.assistantChat(report, q);
      setAnswer(res.answer);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка запроса");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass-card rounded-2xl overflow-hidden border border-white/10">
      <div className="px-6 py-4 border-b border-white/5">
        <h3 className="font-semibold text-gray-200 text-base flex items-center gap-2">
          <span className="text-lg">💬</span>
          Вопрос по отчёту
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          Задайте вопрос — ответ будет только на основе данных этого отчёта (без выдумок).
        </p>
      </div>
      <div className="p-6 space-y-4">
        <div className="flex gap-3 flex-wrap">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            placeholder="Например: какой CPA по Яндекс.Директу?"
            className="flex-1 min-w-[200px] h-11 px-4 rounded-xl bg-gray-800/80 border border-white/10 text-gray-200 placeholder-gray-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition"
            disabled={loading}
          />
          <button
            type="button"
            onClick={handleAsk}
            disabled={loading || !question.trim()}
            className="h-11 px-5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium transition"
          >
            {loading ? "…" : "Спросить"}
          </button>
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        {answer !== null && (
          <div className="rounded-xl bg-white/[0.04] border border-white/5 p-4">
            <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">{answer}</p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── AI Assistant block ── */

function AiAssistantBlock({ summary }: { summary: AiSummary }) {
  const [expanded, setExpanded] = useState(false);
  const paragraphs = summary.recommendation.split("\n\n").filter(Boolean);

  return (
    <div className="glass-card rounded-2xl overflow-hidden border-l-4 border-l-indigo-500">
      {/* Header */}
      <div className="flex items-start justify-between px-6 pt-6 pb-4 gap-4">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center flex-shrink-0 text-lg">
            🤖
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-gray-100 text-base">Рекомендации ИИ-ассистента</span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${
                summary.confidence === "high"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : "bg-amber-500/10 text-amber-400 border-amber-500/20"
              }`}>
                {summary.confidence === "high" ? "Claude AI" : "Автоматический анализ"}
              </span>
            </div>
            <p className="text-sm text-gray-500 leading-relaxed">
              {paragraphs[0]}
            </p>
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors whitespace-nowrap flex-shrink-0 flex items-center gap-1"
        >
          {expanded ? "Свернуть" : "Подробнее"}
          <motion.span
            animate={{ rotate: expanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="inline-block"
          >
            ▾
          </motion.span>
        </button>
      </div>

      {/* Expanded content */}
      {expanded && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
          className="px-6 pb-6 space-y-5 border-t border-white/5 pt-4"
        >
          {/* Full recommendation */}
          {paragraphs.slice(1).map((p, i) => (
            <p key={i} className="text-sm text-gray-400 leading-relaxed">{p}</p>
          ))}

          {/* Platform rationale */}
          {Object.keys(summary.platform_rationale).length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
                Почему эти платформы
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {Object.entries(summary.platform_rationale).map(([platform, reason]) => {
                  const cls = platform === "yandex" ? "badge-yandex"
                            : platform === "google" ? "badge-google"
                            : platform === "vk"     ? "badge-vk"
                            : "bg-gray-700 text-gray-300 border border-white/10";
                  return (
                    <div key={platform} className="bg-white/[0.03] rounded-xl p-3 flex gap-3">
                      <span className={`badge-platform ${cls} self-start mt-0.5`}>{platform}</span>
                      <span className="text-sm text-gray-400 leading-relaxed">{reason}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Quick wins */}
          {summary.quick_wins.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
                Быстрые улучшения
              </h3>
              <ul className="space-y-2">
                {summary.quick_wins.map((win, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-400 leading-relaxed">
                    <span className="text-indigo-400 flex-shrink-0 mt-0.5">✓</span>
                    {win}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}

/* ── Niche Insight Block ── */

const CAMPAIGN_TYPE_LABELS: Record<string, string> = {
  search: "Поиск",
  display: "РСЯ / КМС",
  retargeting: "Ретаргетинг",
  smart: "Smart / Pmax",
  vk: "VK Ads",
};

const CAMPAIGN_TYPE_COLORS: Record<string, string> = {
  search: "bg-indigo-500/10 text-indigo-300 border-indigo-500/30",
  display: "bg-teal-500/10 text-teal-300 border-teal-500/30",
  retargeting: "bg-violet-500/10 text-violet-300 border-violet-500/30",
  smart: "bg-amber-500/10 text-amber-300 border-amber-500/30",
  vk: "bg-blue-500/10 text-blue-300 border-blue-500/30",
};

function NicheInsightBlock({ insight }: { insight: NicheInsight }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="glass-card rounded-2xl overflow-hidden border-l-4 border-l-violet-500">
      {/* Header */}
      <div className="flex items-start justify-between px-6 pt-6 pb-4 gap-4">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-violet-500/20 border border-violet-500/30 flex items-center justify-center flex-shrink-0 text-lg">
            🎯
          </div>
          <div>
            <span className="font-semibold text-gray-100 text-base block mb-1">
              Анализ ниши
            </span>
            <p className="text-sm text-gray-400 leading-relaxed max-w-2xl">
              {insight.business_description}
            </p>
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-sm text-violet-400 hover:text-violet-300 transition-colors whitespace-nowrap flex-shrink-0 flex items-center gap-1"
        >
          {expanded ? "Свернуть" : "Подробнее"}
          <motion.span
            animate={{ rotate: expanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="inline-block"
          >
            ▾
          </motion.span>
        </button>
      </div>

      {/* Expanded */}
      {expanded && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
          className="px-6 pb-6 pt-4 border-t border-white/5 space-y-6"
        >
          {/* Audience */}
          <div>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
              Целевая аудитория
            </h3>
            <p className="text-sm text-gray-300 mb-3">{insight.primary_audience}</p>
            <div className="flex flex-wrap gap-2">
              {insight.audience_pain_points.map((pain, i) => (
                <span
                  key={i}
                  className="text-sm bg-white/[0.04] border border-white/10 rounded-full px-3 py-1 text-gray-400"
                >
                  {pain}
                </span>
              ))}
            </div>
          </div>

          {/* Campaign types */}
          <div>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
              Рекомендуемые типы кампаний
            </h3>
            <div className="flex flex-wrap gap-2 mb-3">
              {insight.recommended_campaign_types.map((type) => (
                <span
                  key={type}
                  className={`text-sm px-3 py-1 rounded-full border font-medium ${CAMPAIGN_TYPE_COLORS[type] ?? "bg-gray-700/50 text-gray-300 border-white/10"}`}
                >
                  {CAMPAIGN_TYPE_LABELS[type] ?? type}
                </span>
              ))}
            </div>
            <p className="text-sm text-gray-400 leading-relaxed">{insight.campaign_type_reasoning}</p>
          </div>

          {/* Campaign structure */}
          <div>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
              Предлагаемая структура кампаний
            </h3>
            <div className="space-y-2">
              {insight.suggested_campaign_structure.map((camp, i) => (
                <div
                  key={i}
                  className="bg-white/[0.04] border border-white/8 rounded-xl p-4 flex gap-4"
                >
                  <div className="w-7 h-7 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-sm font-bold text-indigo-300 flex-shrink-0">
                    {i + 1}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-gray-100 text-sm mb-1">{camp.name}</div>
                    <div className="text-xs text-gray-500 mb-1">
                      <span className="text-gray-400">Ключи:</span> {camp.keywords_focus}
                    </div>
                    <div className="text-xs text-gray-500">
                      <span className="text-gray-400">Цель:</span> {camp.goal}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Strategies */}
          <div>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
              Лучшие стратегии для ниши
            </h3>
            <ul className="space-y-2">
              {insight.best_strategies.map((s, i) => (
                <li key={i} className="flex gap-2 text-sm text-gray-400 leading-relaxed">
                  <span className="text-violet-400 flex-shrink-0 mt-0.5">→</span>
                  {s}
                </li>
              ))}
            </ul>
          </div>

          {/* Competition */}
          <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-widest">
              Конкуренция
            </span>
            <p className="text-sm text-gray-400 mt-1 leading-relaxed">{insight.competition_notes}</p>
          </div>
        </motion.div>
      )}
    </div>
  );
}

/* ── Budget Recommendation Block ── */

const CURRENCY_SYMBOLS: Record<string, string> = {
  RUB: "₽", BYN: "Br", USD: "$", EUR: "€", KZT: "₸",
};

function BudgetRecommendationBlock({ rec }: { rec: BudgetRecommendation }) {
  const sym = CURRENCY_SYMBOLS[rec.currency] ?? rec.currency;
  const fmt = (n: number) =>
    n.toLocaleString("ru", { maximumFractionDigits: rec.currency === "RUB" || rec.currency === "KZT" ? 0 : 0 });

  const tiers = [
    { label: "Минимальный", sublabel: "тестовый", value: rec.recommended_min, color: "text-amber-300", border: "border-amber-500/30", bg: "bg-amber-500/5" },
    { label: "Оптимальный", sublabel: "рекомендуемый", value: rec.recommended_optimal, color: "text-emerald-300", border: "border-emerald-500/30", bg: "bg-emerald-500/10" },
    { label: "Агрессивный", sublabel: "максимальный охват", value: rec.recommended_aggressive, color: "text-indigo-300", border: "border-indigo-500/30", bg: "bg-indigo-500/5" },
  ];

  return (
    <div className="glass-card rounded-2xl overflow-hidden border-l-4 border-l-emerald-500">
      <div className="px-6 pt-6 pb-4">
        <div className="flex items-start gap-3 mb-5">
          <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center flex-shrink-0 text-lg">
            💰
          </div>
          <div>
            <span className="font-semibold text-gray-100 text-base block mb-1">
              Рекомендация бюджета
            </span>
            <p className="text-sm text-gray-400 leading-relaxed max-w-2xl">
              {rec.reasoning}
            </p>
          </div>
        </div>

        {/* Budget tiers */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
          {tiers.map((tier) => (
            <div
              key={tier.label}
              className={`rounded-xl border p-4 ${tier.bg} ${tier.border}`}
            >
              <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">{tier.label}</div>
              <div className={`text-2xl font-bold ${tier.color} mb-0.5`}>
                {fmt(tier.value)} {sym}
              </div>
              <div className="text-xs text-gray-600">{tier.sublabel}</div>
            </div>
          ))}
        </div>

        {/* Forecast at optimal */}
        <div className="bg-white/[0.03] border border-white/8 rounded-xl p-4 flex flex-wrap gap-6">
          <div>
            <div className="text-xs text-gray-500 mb-1">Клики / мес (оптимальный)</div>
            <div className="text-xl font-semibold text-gray-100">
              ~{rec.monthly_clicks_estimate.toLocaleString("ru")}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">Лиды / мес (оптимальный)</div>
            <div className="text-xl font-semibold text-emerald-300">
              ~{rec.monthly_leads_estimate.toLocaleString("ru")}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">Стоимость лида (est.)</div>
            <div className="text-xl font-semibold text-amber-300">
              {rec.monthly_leads_estimate > 0
                ? `~${fmt(rec.recommended_optimal / rec.monthly_leads_estimate)} ${sym}`
                : "—"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── КП скачивание ── */
async function handleKpDownload(
  report: AnalyzeResponse,
  variant: 1 | 3,
  setLoading: (v: null | 1 | 3) => void,
) {
  setLoading(variant);
  try {
    await api.downloadKp(report, variant);
  } catch (e) {
    alert(e instanceof Error ? e.message : "Ошибка генерации PDF");
  } finally {
    setLoading(null);
  }
}

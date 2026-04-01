const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  analyze: (body: object) =>
    request("/analyze", { method: "POST", body: JSON.stringify(body) }),

  getReports: () => request("/reports"),

  getReport: (id: string) => request(`/reports/${id}`),

  getPdfUrl: (id: string) => `${API_URL}/reports/${id}/pdf`,

  /** Скачать КП как PDF (из sessionStorage данных, без сохранения в БД) */
  downloadKp: async (report: object, variant: 1 | 3): Promise<void> => {
    const res = await fetch(`${API_URL}/pdf?variant=${variant}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(report),
    });
    if (!res.ok) throw new Error(`PDF error: ${res.status}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `KP-Kalinin-Digital-v${variant}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  },

  /** Экспорт ключевых слов по семантическим группам в CSV */
  exportKeywords: async (report: object, fmt: "csv" | "tsv" = "csv"): Promise<void> => {
    const res = await fetch(`${API_URL}/export/keywords?fmt=${fmt}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(report),
    });
    if (!res.ok) throw new Error(`Export error: ${res.status}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `keywords.${fmt}`;
    a.click();
    URL.revokeObjectURL(url);
  },

  /** Вопрос по отчёту — ответ только по данным отчёта (правдиво) */
  assistantChat: (report: object, question: string) =>
    request<{ answer: string }>("/assistant/chat", {
      method: "POST",
      body: JSON.stringify({ report, question }),
    }),
};

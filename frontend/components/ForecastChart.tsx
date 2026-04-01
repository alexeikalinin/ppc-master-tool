"use client";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import type { MediaPlanRow } from "@/types/api";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface ForecastChartProps {
  rows: MediaPlanRow[];
}

export default function ForecastChart({ rows }: ForecastChartProps) {
  const byPlatform: Record<string, { budget: number; conversions: number }> = {};
  for (const row of rows) {
    if (!byPlatform[row.platform]) {
      byPlatform[row.platform] = { budget: 0, conversions: 0 };
    }
    byPlatform[row.platform].budget += row.budget;
    byPlatform[row.platform].conversions += row.conversions;
  }

  const labels = Object.keys(byPlatform).map((p) => p.charAt(0).toUpperCase() + p.slice(1));
  const budgets = Object.values(byPlatform).map((v) => Math.round(v.budget));
  const conversions = Object.values(byPlatform).map((v) => Math.round(v.conversions));

  const data = {
    labels,
    datasets: [
      {
        label: "Бюджет (₽)",
        data: budgets,
        backgroundColor: "rgba(99, 102, 241, 0.7)",
        borderColor: "#6366f1",
        borderWidth: 2,
        borderRadius: 6,
        yAxisID: "y",
      },
      {
        label: "Конверсии",
        data: conversions,
        backgroundColor: "rgba(16, 185, 129, 0.6)",
        borderColor: "#10b981",
        borderWidth: 2,
        borderRadius: 6,
        yAxisID: "y1",
      },
    ],
  };

  const options = {
    responsive: true,
    interaction: { mode: "index" as const, intersect: false },
    plugins: {
      legend: {
        labels: {
          color: "#d1d5db",
          font: { size: 14, family: "Inter, sans-serif" },
          padding: 20,
          usePointStyle: true,
        },
      },
      title: {
        display: true,
        text: "Распределение бюджета и конверсий по платформам",
        color: "#f3f4f6",
        font: { size: 16, weight: "bold" as const, family: "Inter, sans-serif" },
        padding: { bottom: 20 },
      },
      tooltip: {
        backgroundColor: "rgba(17, 24, 39, 0.95)",
        borderColor: "rgba(255,255,255,0.1)",
        borderWidth: 1,
        titleColor: "#f3f4f6",
        bodyColor: "#d1d5db",
        padding: 12,
        titleFont: { size: 14 },
        bodyFont: { size: 13 },
      },
    },
    scales: {
      x: {
        ticks: { color: "#9ca3af", font: { size: 14 } },
        grid: { color: "rgba(255,255,255,0.05)" },
        border: { color: "rgba(255,255,255,0.1)" },
      },
      y: {
        type: "linear" as const,
        position: "left" as const,
        ticks: { color: "#9ca3af", font: { size: 14 } },
        grid: { color: "rgba(255,255,255,0.05)" },
        border: { color: "rgba(255,255,255,0.1)" },
        title: { display: true, text: "Бюджет (₽)", color: "#a5b4fc", font: { size: 13 } },
      },
      y1: {
        type: "linear" as const,
        position: "right" as const,
        ticks: { color: "#9ca3af", font: { size: 14 } },
        grid: { drawOnChartArea: false },
        border: { color: "rgba(255,255,255,0.1)" },
        title: { display: true, text: "Конверсии", color: "#6ee7b7", font: { size: 13 } },
      },
    },
  };

  return (
    <div className="glass-card rounded-2xl p-6">
      <Bar data={data} options={options} />
    </div>
  );
}

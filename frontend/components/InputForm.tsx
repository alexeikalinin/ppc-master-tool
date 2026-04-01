"use client";

import { useState } from "react";
import { motion } from "framer-motion";

export interface FormValues {
  url: string;
  region: string;
  city: string;
  niche: string;
  budget: string;
  currency: string;
  auto_budget: boolean;
  ga_ym_metrics: string;
}

interface InputFormProps {
  onSubmit: (values: FormValues) => void;
  loading: boolean;
}

const REGIONS = [
  { code: "RU", label: "Россия" },
  { code: "BY", label: "Беларусь" },
];

const CITIES: Record<string, { value: string; label: string }[]> = {
  RU: [
    { value: "", label: "Вся Россия" },
    { value: "Москва", label: "Москва" },
    { value: "Санкт-Петербург", label: "Санкт-Петербург" },
    { value: "Екатеринбург", label: "Екатеринбург" },
    { value: "Новосибирск", label: "Новосибирск" },
    { value: "Казань", label: "Казань" },
    { value: "Краснодар", label: "Краснодар" },
    { value: "Нижний Новгород", label: "Нижний Новгород" },
    { value: "Ростов-на-Дону", label: "Ростов-на-Дону" },
    { value: "Самара", label: "Самара" },
    { value: "Уфа", label: "Уфа" },
    { value: "Московская область", label: "Московская область" },
    { value: "Ленинградская область", label: "Ленинградская область" },
  ],
  BY: [
    { value: "", label: "Вся Беларусь" },
    { value: "Минск", label: "Минск" },
    { value: "Брест", label: "Брест" },
    { value: "Гомель", label: "Гомель" },
    { value: "Гродно", label: "Гродно" },
    { value: "Витебск", label: "Витебск" },
    { value: "Могилёв", label: "Могилёв" },
    { value: "Минская область", label: "Минская область" },
    { value: "Брестская область", label: "Брестская область" },
    { value: "Гомельская область", label: "Гомельская область" },
    { value: "Гродненская область", label: "Гродненская область" },
    { value: "Витебская область", label: "Витебская область" },
    { value: "Могилёвская область", label: "Могилёвская область" },
  ],
};

const CURRENCIES = [
  { code: "RUB", label: "₽ RUB" },
  { code: "BYN", label: "Br BYN" },
  { code: "USD", label: "$ USD" },
  { code: "EUR", label: "€ EUR" },
  { code: "KZT", label: "₸ KZT" },
];

const CURRENCY_SYMBOLS: Record<string, string> = {
  RUB: "₽", BYN: "Br", USD: "$", EUR: "€", KZT: "₸",
};

const inputClass =
  "w-full h-12 bg-gray-800/80 border border-white/10 rounded-lg px-4 text-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition";

const labelClass = "block text-base font-medium text-gray-300 mb-2";

export default function InputForm({ onSubmit, loading }: InputFormProps) {
  const [values, setValues] = useState<FormValues>({
    url: "",
    region: "BY",
    city: "Минск",
    niche: "",
    budget: "",
    currency: "RUB",
    auto_budget: false,
    ga_ym_metrics: "",
  });
  const [urlError, setUrlError] = useState("");

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    if (name === "region") {
      setValues((v) => ({ ...v, region: value, city: "" }));
    } else if (type === "checkbox") {
      setValues((v) => ({ ...v, [name]: checked }));
    } else {
      setValues((v) => ({ ...v, [name]: value }));
    }
    if (name === "url") setUrlError("");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!values.url.startsWith("http")) {
      setUrlError("URL должен начинаться с https://");
      return;
    }
    onSubmit(values);
  }

  const cities = CITIES[values.region] ?? [];
  const currSymbol = CURRENCY_SYMBOLS[values.currency] || values.currency;

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="glass-card rounded-2xl p-8 space-y-6 w-full max-w-2xl mx-auto"
    >
      {/* URL */}
      <div>
        <label className={labelClass}>
          URL сайта <span className="text-red-400">*</span>
        </label>
        <input
          name="url"
          type="url"
          required
          placeholder="https://example.com"
          value={values.url}
          onChange={handleChange}
          className={inputClass}
        />
        {urlError && (
          <p className="text-red-400 text-sm mt-1.5 flex items-center gap-1">
            <span>⚠</span> {urlError}
          </p>
        )}
      </div>

      {/* Region + City */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelClass}>Страна</label>
          <select
            name="region"
            value={values.region}
            onChange={handleChange}
            className={`${inputClass} cursor-pointer`}
          >
            {REGIONS.map((r) => (
              <option key={r.code} value={r.code} className="bg-gray-800">
                {r.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className={labelClass}>Город / область</label>
          <select
            name="city"
            value={values.city}
            onChange={handleChange}
            className={`${inputClass} cursor-pointer`}
          >
            {cities.map((c) => (
              <option key={c.value} value={c.value} className="bg-gray-800">
                {c.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Budget + Currency */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className={labelClass.replace("mb-2", "mb-0")}>
            Бюджет / мес
          </label>
          {/* Auto-budget toggle */}
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <div className="relative">
              <input
                type="checkbox"
                name="auto_budget"
                checked={values.auto_budget}
                onChange={handleChange}
                className="sr-only peer"
              />
              <div className="w-10 h-5 bg-gray-700 rounded-full peer-checked:bg-indigo-600 transition-colors" />
              <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5" />
            </div>
            <span className="text-sm text-gray-400">
              {values.auto_budget ? (
                <span className="text-indigo-400 font-medium">Рекомендовать AI</span>
              ) : (
                "Рекомендовать AI"
              )}
            </span>
          </label>
        </div>

        <div className="flex gap-3">
          {/* Currency selector */}
          <select
            name="currency"
            value={values.currency}
            onChange={handleChange}
            className="h-12 bg-gray-800/80 border border-white/10 rounded-lg px-3 text-base text-gray-100 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition cursor-pointer w-32"
          >
            {CURRENCIES.map((c) => (
              <option key={c.code} value={c.code} className="bg-gray-800">
                {c.label}
              </option>
            ))}
          </select>

          {/* Budget input */}
          <div className="relative flex-1">
            <input
              name="budget"
              type="number"
              min="0"
              placeholder={values.auto_budget ? "AI подберёт оптимальный бюджет" : `50 000`}
              value={values.budget}
              onChange={handleChange}
              disabled={values.auto_budget}
              className={`${inputClass} pr-10 disabled:opacity-40 disabled:cursor-not-allowed`}
            />
            {!values.auto_budget && (
              <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-500 text-base pointer-events-none">
                {currSymbol}
              </span>
            )}
          </div>
        </div>

        {values.auto_budget && (
          <p className="text-sm text-indigo-400/80 mt-2 flex items-center gap-1.5">
            <span>✨</span>
            AI проанализирует объём поиска и CPC и порекомендует оптимальный бюджет
          </p>
        )}
      </div>

      {/* Niche */}
      <div>
        <label className={labelClass}>
          Ниша <span className="text-gray-500 font-normal">(необязательно — AI определит сам)</span>
        </label>
        <input
          name="niche"
          type="text"
          placeholder="digital-agency, e-commerce, medical, services…"
          value={values.niche}
          onChange={handleChange}
          className={inputClass}
        />
      </div>

      {/* GA/YM metrics */}
      <div>
        <label className={labelClass}>
          Метрики GA/YM <span className="text-gray-500 font-normal">(необязательно, JSON)</span>
        </label>
        <textarea
          name="ga_ym_metrics"
          rows={3}
          placeholder='{"sessions": 10000, "bounce_rate": 0.45, "avg_cpc": 35}'
          value={values.ga_ym_metrics}
          onChange={handleChange}
          className="w-full bg-gray-800/80 border border-white/10 rounded-lg px-4 py-3 text-base text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition resize-none font-mono"
        />
      </div>

      {/* Submit */}
      <motion.button
        type="submit"
        disabled={loading}
        whileHover={{ scale: loading ? 1 : 1.02 }}
        whileTap={{ scale: loading ? 1 : 0.98 }}
        className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg px-6 py-3.5 text-lg transition-colors shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <LoadingSpinner />
            Анализируем…
          </>
        ) : (
          "Запустить анализ"
        )}
      </motion.button>
    </motion.form>
  );
}

function LoadingSpinner() {
  return (
    <motion.div
      className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
      animate={{ rotate: 360 }}
      transition={{ repeat: Infinity, duration: 0.75, ease: "linear" }}
    />
  );
}

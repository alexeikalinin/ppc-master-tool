'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RefreshCw, AlertTriangle, CheckCircle, XCircle, Zap } from 'lucide-react'
import { api } from '@/lib/api'

type UsageData = Awaited<ReturnType<typeof api.getUsage>>

const PROVIDER_LABELS: Record<string, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  xai: 'xAI (Grok)',
}

const PROVIDER_COLORS: Record<string, string> = {
  anthropic: 'text-orange-400',
  openai: 'text-green-400',
  xai: 'text-blue-400',
}

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

function fmtCost(usd: number): string {
  if (usd < 0.001) return '< $0.001'
  if (usd < 1) return `$${usd.toFixed(4)}`
  return `$${usd.toFixed(2)}`
}

export default function UsageWidget() {
  const [data, setData] = useState<UsageData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      setData(await api.getUsage())
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, 30_000)
    return () => clearInterval(id)
  }, [load])

  const handleReset = async () => {
    await api.resetUsage()
    await load()
  }

  if (error) {
    return (
      <div className="rounded-xl border border-dashed border-white/10 p-3 text-center text-xs text-gray-600">
        Бэкенд недоступен
      </div>
    )
  }

  const { keys, providers, total_cost_usd } = data ?? {}
  const hasUsage = Object.keys(providers ?? {}).length > 0

  return (
    <div className="space-y-3">
      {/* API Keys status */}
      {keys && (
        <div className="space-y-1.5">
          {(['anthropic', 'openai', 'xai'] as const).map((p) => {
            const active = keys[p]
            const isActiveProvider = keys.active_provider === p
            return (
              <div key={p} className="flex items-center gap-2">
                {active
                  ? <CheckCircle className="w-3.5 h-3.5 text-green-400 shrink-0" />
                  : <XCircle className="w-3.5 h-3.5 text-gray-600 shrink-0" />
                }
                <span className={`text-xs flex-1 ${active ? PROVIDER_COLORS[p] : 'text-gray-600'}`}>
                  {PROVIDER_LABELS[p]}
                </span>
                {isActiveProvider && (
                  <span className="text-[10px] bg-indigo-600/30 text-indigo-300 px-1.5 py-0.5 rounded-full">
                    active
                  </span>
                )}
                {!active && (
                  <span className="text-[10px] text-gray-600">нет ключа</span>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Usage summary */}
      {hasUsage && (
        <div className="glass-card rounded-xl p-3 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-xs font-medium text-gray-200">Расход токенов</span>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                onClick={load}
                disabled={loading}
                className="text-gray-500 hover:text-gray-300 transition-colors"
                title="Обновить"
              >
                <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={() => setExpanded(v => !v)}
                className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
              >
                {expanded ? 'свернуть' : 'подробнее'}
              </button>
            </div>
          </div>

          {/* Per-provider summary */}
          <div className="space-y-1.5">
            {Object.entries(providers ?? {}).map(([provider, stats]) => (
              <div key={provider}>
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-medium ${PROVIDER_COLORS[provider] ?? 'text-gray-400'}`}>
                    {PROVIDER_LABELS[provider] ?? provider}
                  </span>
                  <span className="text-xs text-gray-300 font-mono">{fmtCost(stats.cost_usd)}</span>
                </div>
                <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
                  <span>{fmt(stats.total_tokens)} токенов · {stats.requests} запр.</span>
                  {stats.errors > 0 && (
                    <span className="text-red-400 flex items-center gap-0.5">
                      <AlertTriangle className="w-2.5 h-2.5" />
                      {stats.errors} ошиб.
                    </span>
                  )}
                </div>

                {/* Per-model breakdown */}
                <AnimatePresence>
                  {expanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-1 pl-2 border-l border-white/10 space-y-0.5">
                        {Object.entries(stats.models).map(([model, ms]) => (
                          <div key={model} className="flex justify-between text-[10px] text-gray-600">
                            <span className="truncate max-w-[120px]">{model}</span>
                            <span className="font-mono">{fmt(ms.input_tokens + ms.output_tokens)}</span>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>

          {/* Total */}
          <div className="flex justify-between items-center pt-1.5 border-t border-white/10">
            <span className="text-[10px] text-gray-500">Итого за сессию</span>
            <span className="text-xs font-semibold text-gray-100 font-mono">
              {fmtCost(total_cost_usd ?? 0)}
            </span>
          </div>

          <button
            onClick={handleReset}
            className="w-full text-[10px] text-gray-600 hover:text-red-400 transition-colors text-center py-0.5"
          >
            сбросить счётчик
          </button>
        </div>
      )}

      {!hasUsage && !error && data && (
        <div className="text-xs text-gray-600 text-center py-1">
          Токены не использовались
        </div>
      )}
    </div>
  )
}

'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { Clock, FileText, BarChart3, X, Search, TrendingUp } from 'lucide-react'
import { type Message } from './ChatPanel'

interface RightPanelProps {
  messages: Message[]
  currentReport: Record<string, unknown> | null
  onClearReport: () => void
}

const QUICK_LINKS = [
  { icon: Search, label: 'Новый анализ', href: '/dashboard' },
  { icon: FileText, label: 'Все отчёты', href: '/reports' },
  { icon: BarChart3, label: 'Трекер кампаний', href: '/tracker' },
]

export default function RightPanel({ messages, currentReport, onClearReport }: RightPanelProps) {
  const recentUserMessages = messages
    .filter((m) => m.role === 'user')
    .slice(-6)
    .reverse()

  return (
    <div className="w-72 shrink-0 flex flex-col h-full bg-[#151c2e] border-l border-white/10 overflow-y-auto">
      {/* Report context */}
      <div className="p-4 border-b border-white/10">
        <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-3">
          Контекст отчёта
        </div>
        {currentReport ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative glass-card rounded-xl p-3"
          >
            <button
              onClick={onClearReport}
              title="Очистить отчёт"
              className="absolute top-2.5 right-2.5 text-gray-500 hover:text-gray-300 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
            <div className="flex items-center gap-2 mb-2.5">
              <div className="w-6 h-6 rounded-md bg-green-500/20 flex items-center justify-center">
                <FileText className="w-3.5 h-3.5 text-green-400" />
              </div>
              <span className="text-sm font-medium text-gray-200">Отчёт загружен</span>
            </div>
            <div className="space-y-1">
              {typeof currentReport.niche === 'string' && (
                <div className="text-xs">
                  <span className="text-gray-500">Ниша: </span>
                  <span className="text-gray-200">{currentReport.niche}</span>
                </div>
              )}
              {Array.isArray(currentReport.keywords) && (
                <div className="text-xs">
                  <span className="text-gray-500">Ключевых слов: </span>
                  <span className="text-gray-200">{currentReport.keywords.length}</span>
                </div>
              )}
              {Array.isArray(currentReport.competitors) && (
                <div className="text-xs">
                  <span className="text-gray-500">Конкурентов: </span>
                  <span className="text-gray-200">{currentReport.competitors.length}</span>
                </div>
              )}
              {typeof currentReport.region === 'string' && (
                <div className="text-xs">
                  <span className="text-gray-500">Регион: </span>
                  <span className="text-gray-200">{currentReport.region}</span>
                </div>
              )}
            </div>
          </motion.div>
        ) : (
          <div className="rounded-xl border border-dashed border-white/10 p-4 text-center">
            <div className="text-2xl mb-1.5">📂</div>
            <div className="text-xs text-gray-500 leading-relaxed">
              Нет активного отчёта.<br />
              Запусти <span className="text-indigo-400">Анализатор</span>.
            </div>
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="p-4 border-b border-white/10">
        <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-3">
          Быстрые действия
        </div>
        <div className="space-y-1.5">
          {QUICK_LINKS.map(({ icon: Icon, label, href }) => (
            <Link
              key={label}
              href={href}
              className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/8 text-sm text-gray-300 hover:text-gray-50 transition-all"
            >
              <Icon className="w-4 h-4 text-indigo-400 shrink-0" />
              {label}
            </Link>
          ))}
        </div>
      </div>

      {/* Session stats */}
      {messages.length > 0 && (
        <div className="p-4 border-b border-white/10">
          <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-3">
            Сессия
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-white/5 rounded-lg px-3 py-2 text-center">
              <div className="text-lg font-semibold text-gray-100">{messages.length}</div>
              <div className="text-[10px] text-gray-500">сообщений</div>
            </div>
            <div className="bg-white/5 rounded-lg px-3 py-2 text-center">
              <div className="text-lg font-semibold text-gray-100">
                {currentReport ? '1' : '0'}
              </div>
              <div className="text-[10px] text-gray-500">отчётов</div>
            </div>
          </div>
        </div>
      )}

      {/* Recent requests */}
      <div className="p-4 flex-1">
        <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-3">
          История запросов
        </div>
        {recentUserMessages.length === 0 ? (
          <div className="text-xs text-gray-600">Запросов пока нет</div>
        ) : (
          <div className="space-y-2">
            {recentUserMessages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, x: 6 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex gap-2 items-start group"
              >
                <Clock className="w-3 h-3 text-gray-600 mt-0.5 shrink-0" />
                <div className="text-xs text-gray-400 line-clamp-2 leading-relaxed group-hover:text-gray-300 transition-colors">
                  {msg.content}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

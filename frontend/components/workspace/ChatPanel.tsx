'use client'

import { useRef, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, Send } from 'lucide-react'
import { type Agent } from '@/lib/agents'
import { api } from '@/lib/api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatPanelProps {
  agent: Agent
  messages: Message[]
  onMessages: (updater: (prev: Message[]) => Message[]) => void
  currentReport: Record<string, unknown> | null
  onReportChange: (report: Record<string, unknown>) => void
  activeClient: string
}

function extractUrl(text: string): string | null {
  const match = text.match(/https?:\/\/[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s]*/i)
  if (!match) return null
  return match[0].startsWith('http') ? match[0] : `https://${match[0]}`
}

function extractRegion(text: string): string {
  const match = text.match(/\b(Москв\w*|Санкт-Петербург\w*|Питер\w*|Минск\w*|Казань\w*|Екатеринбург\w*|Новосибирск\w*)\b/i)
  return match ? match[0] : 'Москва'
}

export default function ChatPanel({ agent, messages, onMessages, currentReport, onReportChange, activeClient }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isLoading])

  const addMessage = (msg: Omit<Message, 'id' | 'timestamp'>) => {
    onMessages(prev => [...prev, { ...msg, id: crypto.randomUUID(), timestamp: new Date() }])
  }

  const handleSend = async (text?: string) => {
    const content = (text ?? input).trim()
    if (!content || isLoading) return

    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    addMessage({ role: 'user', content })
    setIsLoading(true)

    try {
      let response = ''

      if (agent.id === 'analyzer') {
        const url = extractUrl(content) ?? 'https://example.com'
        const region = extractRegion(content)
        const result = await api.analyze({ url, region }) as Record<string, unknown>
        onReportChange(result)
        const niche = (result.niche as string) || 'не определена'
        const kwCount = (result.keywords as unknown[])?.length ?? 0
        const compCount = (result.competitors as unknown[])?.length ?? 0
        response = `✅ **Анализ завершён**\n\n**Сайт:** ${url}\n**Регион:** ${region}\n**Ниша:** ${niche}\n**Ключевых слов:** ${kwCount}\n**Конкурентов:** ${compCount}\n\nОтчёт сохранён в контексте. Переключись на **PPC-консультанта** чтобы задавать вопросы, или на **КП-генератор** для создания PDF.`

      } else if (agent.id === 'mediaplanner') {
        if (!currentReport) {
          response = 'Сначала запусти **Анализатор** — медиаплан строится на основе отчёта.'
        } else {
          const result = await api.assistantChat(currentReport, content)
          response = result.answer
        }

      } else if (agent.id === 'consultant') {
        if (!currentReport) {
          response = 'Сначала запусти **Анализатор** — консультант отвечает только по данным отчёта.'
        } else {
          const result = await api.assistantChat(currentReport, content)
          response = result.answer
        }

      } else if (agent.id === 'kp') {
        if (!currentReport) {
          response = 'Сначала запусти **Анализатор** — КП генерируется на основе отчёта.'
        } else {
          const variant = content.includes('3') ? 3 : 1
          await api.downloadKp(currentReport, variant as 1 | 3)
          response = `📄 КП скачано (вариант ${variant} — ${variant === 1 ? 'Dark Premium' : 'Split Layout'}).`
        }

      } else if (agent.id === 'tracker') {
        response = '📊 Модуль трекера скоро будет доступен здесь. Пока используй раздел **/tracker** для просмотра статистики и управления bidding robot.'
      }

      addMessage({ role: 'assistant', content: response })
    } catch (err) {
      addMessage({
        role: 'assistant',
        content: `⚠️ Ошибка: ${err instanceof Error ? err.message : 'Что-то пошло не так. Проверь, что бэкенд запущен.'}`,
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
    const t = e.currentTarget
    t.style.height = 'auto'
    t.style.height = `${Math.min(t.scrollHeight, 128)}px`
  }

  const clientLabel = activeClient === 'astrum' ? '🎮 Astrum' : '⭐ Starmedia'

  return (
    <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
      {/* Agent header */}
      <div className="px-6 py-4 border-b border-white/10 flex items-center gap-4 shrink-0">
        <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-xl shrink-0">
          {agent.emoji}
        </div>
        <div className="min-w-0">
          <div className="font-semibold text-gray-50 text-base">{agent.name}</div>
          <div className="text-sm text-gray-400 truncate">{agent.description}</div>
        </div>
        <div className="ml-auto shrink-0 text-sm text-gray-400 bg-white/5 px-3 py-1 rounded-full border border-white/10">
          {clientLabel}
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="text-6xl mb-4">{agent.emoji}</div>
            <div className="text-xl font-semibold text-gray-200 mb-2">{agent.name}</div>
            <div className="text-sm text-gray-400 max-w-sm leading-relaxed">{agent.description}</div>
            <div className="mt-8 flex flex-wrap gap-2 justify-center max-w-lg">
              {agent.quickActions.map((action) => (
                <button
                  key={action}
                  onClick={() => handleSend(action)}
                  className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-gray-300 hover:bg-indigo-600/20 hover:border-indigo-500/40 hover:text-gray-50 transition-all"
                >
                  {action}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                  className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-base shrink-0 mt-0.5">
                      {agent.emoji}
                    </div>
                  )}
                  <div
                    className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-br-sm'
                        : 'bg-white/5 border border-white/10 text-gray-100 rounded-bl-sm'
                    }`}
                  >
                    {msg.content}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center text-xs font-medium text-gray-300 shrink-0 mt-0.5">
                      Вы
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {isLoading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-base shrink-0">
                  {agent.emoji}
                </div>
                <div className="bg-white/5 border border-white/10 rounded-2xl rounded-bl-sm px-4 py-3">
                  <div className="flex items-center gap-1.5">
                    {[0, 1, 2].map((i) => (
                      <motion.div
                        key={i}
                        className="w-1.5 h-1.5 rounded-full bg-indigo-400"
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.25 }}
                      />
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </>
        )}
      </div>

      {/* Quick actions strip (visible after first message) */}
      {messages.length > 0 && (
        <div className="px-6 py-2 flex gap-2 overflow-x-auto shrink-0 border-t border-white/5">
          {agent.quickActions.map((action) => (
            <button
              key={action}
              onClick={() => handleSend(action)}
              className="shrink-0 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-gray-400 hover:bg-indigo-600/15 hover:border-indigo-500/30 hover:text-gray-200 transition-all whitespace-nowrap"
            >
              {action}
            </button>
          ))}
        </div>
      )}

      {/* Input area */}
      <div className="px-4 pb-4 pt-3 border-t border-white/10 shrink-0">
        <div className="flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder={agent.placeholder}
            rows={1}
            disabled={isLoading}
            className="flex-1 resize-none bg-white/5 border border-white/10 rounded-2xl px-4 py-3 text-sm text-gray-50 placeholder:text-gray-500 focus:outline-none focus:border-indigo-500/50 transition-all overflow-y-auto disabled:opacity-50"
            style={{ minHeight: '48px', maxHeight: '128px' }}
          />
          <button
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
            className="w-11 h-11 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:cursor-not-allowed flex items-center justify-center transition-all shrink-0"
          >
            {isLoading
              ? <Loader2 className="w-4 h-4 animate-spin text-white" />
              : <Send className="w-4 h-4 text-white" />
            }
          </button>
        </div>
        <div className="mt-2 text-xs text-gray-600 text-center">
          Enter — отправить · Shift+Enter — новая строка
        </div>
      </div>
    </div>
  )
}

'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { BarChart3, FileText, Home, Search, Settings, Zap } from 'lucide-react'
import { AGENTS, CLIENTS, type Agent } from '@/lib/agents'

interface LeftPanelProps {
  activeAgent: Agent
  activeClient: string
  onAgentSelect: (agent: Agent) => void
  onClientSelect: (clientId: string) => void
}

const NAV_LINKS = [
  { href: '/', icon: Home, label: 'Главная' },
  { href: '/dashboard', icon: Search, label: 'Новый анализ' },
  { href: '/reports', icon: FileText, label: 'Отчёты' },
  { href: '/tracker', icon: BarChart3, label: 'Трекер' },
]

export default function LeftPanel({ activeAgent, activeClient, onAgentSelect, onClientSelect }: LeftPanelProps) {
  return (
    <div className="w-72 shrink-0 flex flex-col h-full bg-[#151c2e] border-r border-white/10">
      {/* Logo */}
      <div className="px-5 py-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center shrink-0">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-semibold text-sm text-gray-50 leading-tight">PPC Master</div>
            <div className="text-xs text-gray-400">Workspace</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="px-3 py-3 border-b border-white/10">
        <div className="space-y-0.5">
          {NAV_LINKS.map(({ href, icon: Icon, label }) => (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-400 hover:text-gray-50 hover:bg-white/5 transition-colors"
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          ))}
        </div>
      </div>

      {/* Agents list */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest px-3 mb-2">
          Агенты
        </div>
        <div className="space-y-1">
          {AGENTS.map((agent) => {
            const isActive = activeAgent.id === agent.id
            return (
              <motion.button
                key={agent.id}
                onClick={() => onAgentSelect(agent)}
                whileTap={{ scale: 0.98 }}
                className={`w-full flex items-start gap-3 px-3 py-2.5 rounded-xl text-left transition-all ${
                  isActive
                    ? 'bg-indigo-600/20 border border-indigo-500/30 text-gray-50'
                    : 'hover:bg-white/5 text-gray-400 hover:text-gray-50 border border-transparent'
                }`}
              >
                <span className="text-lg leading-none mt-0.5 shrink-0">{agent.emoji}</span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium truncate">{agent.name}</div>
                  <div className="text-xs text-gray-500 truncate mt-0.5 leading-tight">{agent.description}</div>
                </div>
                {isActive && (
                  <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                )}
              </motion.button>
            )
          })}
        </div>

        {/* Clients */}
        <div className="mt-5">
          <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest px-3 mb-2">
            Клиенты
          </div>
          <div className="space-y-1">
            {CLIENTS.map((client) => (
              <button
                key={client.id}
                onClick={() => onClientSelect(client.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all ${
                  activeClient === client.id
                    ? 'bg-white/10 text-gray-50'
                    : 'text-gray-400 hover:text-gray-50 hover:bg-white/5'
                }`}
              >
                <span className="text-base">{client.emoji}</span>
                <span className="truncate">{client.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-3 py-3 border-t border-white/10">
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors">
          <Settings className="w-4 h-4" />
          Настройки
        </button>
      </div>
    </div>
  )
}

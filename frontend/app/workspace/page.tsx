'use client'

import { useState } from 'react'
import { AGENTS, type Agent } from '@/lib/agents'
import LeftPanel from '@/components/workspace/LeftPanel'
import ChatPanel, { type Message } from '@/components/workspace/ChatPanel'
import RightPanel from '@/components/workspace/RightPanel'

export default function WorkspacePage() {
  const [activeAgent, setActiveAgent] = useState<Agent>(AGENTS[0])
  const [activeClient, setActiveClient] = useState('astrum')
  // Per-agent message history
  const [agentMessages, setAgentMessages] = useState<Record<string, Message[]>>({})
  const [currentReport, setCurrentReport] = useState<Record<string, unknown> | null>(null)

  const messages = agentMessages[activeAgent.id] ?? []

  const updateMessages = (agentId: string) => (updater: (prev: Message[]) => Message[]) => {
    setAgentMessages((prev) => ({
      ...prev,
      [agentId]: updater(prev[agentId] ?? []),
    }))
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#111827]">
      <LeftPanel
        activeAgent={activeAgent}
        activeClient={activeClient}
        onAgentSelect={setActiveAgent}
        onClientSelect={setActiveClient}
      />
      <ChatPanel
        agent={activeAgent}
        messages={messages}
        onMessages={updateMessages(activeAgent.id)}
        currentReport={currentReport}
        onReportChange={setCurrentReport}
        activeClient={activeClient}
      />
      <RightPanel
        messages={messages}
        currentReport={currentReport}
        onClearReport={() => setCurrentReport(null)}
      />
    </div>
  )
}

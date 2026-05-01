export interface Agent {
  id: string
  name: string
  emoji: string
  description: string
  placeholder: string
  quickActions: string[]
}

export const AGENTS: Agent[] = [
  {
    id: 'analyzer',
    name: 'Анализатор',
    emoji: '🔍',
    description: 'Парсит сайт, определяет нишу и конкурентов',
    placeholder: 'Введите URL сайта для анализа (например, warface.ru)...',
    quickActions: [
      'Проанализируй warface.ru для Москвы',
      'Проанализируй для Минска с бюджетом 150 000 ₽',
      'Найди конкурентов в нише онлайн-игр',
    ],
  },
  {
    id: 'mediaplanner',
    name: 'Медиапланировщик',
    emoji: '🎯',
    description: 'Ключи, ставки и бюджет — по результатам анализа',
    placeholder: 'Задайте вопрос по медиаплану из текущего отчёта...',
    quickActions: [
      'Какой CR и CPA в медиаплане?',
      'Сколько показов прогнозируется?',
      'Как распределён бюджет по платформам?',
    ],
  },
  {
    id: 'tracker',
    name: 'Трекер',
    emoji: '📊',
    description: 'Статистика кампаний Яндекс Директ и bidding robot',
    placeholder: 'Спросите про статистику, правила или A/B тесты...',
    quickActions: [
      'Покажи статистику за 7 дней',
      'Создай правило ночного снижения ставок',
      'Запусти bidding robot в тестовом режиме',
    ],
  },
  {
    id: 'kp',
    name: 'КП-генератор',
    emoji: '📝',
    description: 'Генерирует PDF коммерческое предложение',
    placeholder: 'Выберите вариант: "КП вариант 1" или "КП вариант 3"...',
    quickActions: [
      'Сгенерируй КП вариант 1 (Dark Premium)',
      'КП вариант 3 (Split Layout)',
    ],
  },
  {
    id: 'consultant',
    name: 'PPC-консультант',
    emoji: '💬',
    description: 'Отвечает на вопросы строго по данным отчёта',
    placeholder: 'Задайте вопрос по текущему отчёту...',
    quickActions: [
      'Какой бюджет рекомендован?',
      'Кто главные конкуренты?',
      'Какие ключевые слова приоритетны?',
      'Объясни структуру кампаний',
    ],
  },
]

export const CLIENTS = [
  { id: 'astrum', name: 'Astrum Entertainment', emoji: '🎮' },
  { id: 'starmedia', name: 'Starmedia Agency', emoji: '⭐' },
]

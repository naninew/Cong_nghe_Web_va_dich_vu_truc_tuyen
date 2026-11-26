export interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  role: string;
  xp: number;
  streak_days: number;
}

export interface DeckCounts {
  new: number;
  learning: number;
  due: number;
}

export interface DeckTree {
  id: number;
  name: string;
  description?: string;
  is_collapsed: boolean;
  total_cards: number;
  counts: DeckCounts;
  children: DeckTree[];
}

export interface CardRenderedView {
  front_html: string;
  back_html: string;
  css: string;
}

export interface CleanCardView {
  term: string;
  phonetic?: string;
  meaning: string;
  examples: string[];
  audio_url?: string | null;
  image_url?: string | null;
  level_tag?: string;
  notes?: string;
}

export interface CardDetail {
  id: number;
  deck_id: number;
  deck_name: string;
  note_id: number;
  ord: number;
  type: number;
  queue: number;
  due: number;
  ivl: number;
  factor: number;
  reps: number;
  lapses: number;
  fields: Record<string, string>;
  tags: string[];
  rendered: CardRenderedView;
  clean_data?: CleanCardView | null;
  next_intervals: {
    again: string;
    hard: string;
    good: string;
    easy: string;
  };
}

export interface CardBrowseItem {
  id: number;
  deck_id: number;
  deck_name: string;
  note_id: number;
  ord: number;
  type: number;
  queue: number;
  state_label: string;
  due: number;
  ivl: number;
  factor: number;
  reps: number;
  lapses: number;
  fields: Record<string, string>;
  tags: string[];
}

export interface CardBrowseResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: CardBrowseItem[];
}

export interface StudyQueue {
  card: CardDetail | null;
  remaining_counts: {
    new: number;
    learning: number;
    due: number;
  };
}

export interface QuizOption {
  key: string;
  label: string;
}

export interface QuizQuestion {
  question_id: string;
  card_id: number;
  prompt: string;
  context_hint?: string;
  audio_file?: string;
  direction?: string;
  options: QuizOption[];
}

export interface QuizAnswerResult {
  is_correct: boolean;
  correct_key: string;
  points_earned: number;
  combo_xp: number;
  current_combo: number;
  explanation: string;
  srs_updated: boolean;
  srs_grade: string;
}

export interface QuizFinalResult {
  session_id: string;
  score: number;
  xp_earned: number;
  total_questions: number;
  correct_count: number;
  accuracy_percent: number;
  duration_seconds: number;
  srs_sync?: boolean;
}

export interface StatsOverview {
  user: {
    name: string;
    email: string;
    avatar_url?: string;
    streak_days: number;
    xp: number;
  };
  daily_goal: {
    completed: number;
    target: number;
  };
  due_count: number;
  total_cards: number;
  mature_cards: number;
  learning_cards: number;
  new_cards: number;
  retention_rate: number;
}

export interface DevUser {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  role: string;
  xp: number;
  streak_days: number;
}

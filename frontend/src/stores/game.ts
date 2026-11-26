import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../api/client';
import type { QuizQuestion, QuizAnswerResult, QuizFinalResult } from '../types';

export const useGameStore = defineStore('game', () => {
  const sessionId = ref<string | null>(null);
  const questions = ref<QuizQuestion[]>([]);
  const currentIndex = ref(0);
  const score = ref(0);
  const combo = ref(0);
  const isAnswered = ref(false);
  const lastAnswerResult = ref<QuizAnswerResult | null>(null);
  const finalResult = ref<QuizFinalResult | null>(null);
  const isLoading = ref(false);
  const activeMode = ref<string>('classic');
  const activeDirection = ref<string>('front_to_back');

  const currentQuestion = computed(() => {
    if (currentIndex.value < questions.value.length) {
      return questions.value[currentIndex.value];
    }
    return null;
  });

  const isLastQuestion = computed(() => {
    return currentIndex.value >= questions.value.length - 1;
  });

  async function startGame(
    deckId?: number | null,
    totalQuestions: number = 10,
    srsSync: boolean = true,
    mode: string = 'classic',
    direction: string = 'front_to_back',
    questionField?: string | null,
    answerField?: string | null,
    hintField?: string | null
  ) {
    isLoading.value = true;
    score.value = 0;
    combo.value = 0;
    currentIndex.value = 0;
    isAnswered.value = false;
    lastAnswerResult.value = null;
    finalResult.value = null;
    activeMode.value = mode;
    activeDirection.value = direction;

    try {
      const payload: Record<string, any> = {
        total_questions: totalQuestions,
        srs_sync: srsSync,
        mode: mode,
        direction: direction,
      };
      if (deckId) payload.deck_id = deckId;
      if (questionField) payload.question_field = questionField;
      if (answerField) payload.answer_field = answerField;
      if (hintField) payload.hint_field = hintField;

      const res = await api.post('/games/start', payload);
      sessionId.value = res.data.session_id;
      questions.value = res.data.questions;
      return res.data;
    } finally {
      isLoading.value = false;
    }
  }

  async function submitAnswer(selectedKey: string, responseTimeMs: number = 0) {
    if (!sessionId.value || !currentQuestion.value || isAnswered.value) return;

    isAnswered.value = true;
    const res = await api.post('/games/answer', {
      session_id: sessionId.value,
      card_id: currentQuestion.value.card_id,
      selected_key: selectedKey,
      response_time_ms: responseTimeMs,
    });

    const result: QuizAnswerResult = res.data;
    lastAnswerResult.value = result;
    if (result.is_correct) {
      score.value += result.points_earned;
      combo.value = result.current_combo;
    } else {
      combo.value = 0;
    }
    return result;
  }

  async function nextQuestion() {
    if (!isLastQuestion.value) {
      currentIndex.value += 1;
      isAnswered.value = false;
      lastAnswerResult.value = null;
    } else {
      await finishGame();
    }
  }

  async function fetchDeckFields(deckId?: number | null): Promise<string[]> {
    const res = await api.get('/games/fields', {
      params: deckId ? { deck_id: deckId } : {},
    });
    return Array.isArray(res.data) ? res.data : [];
  }

  async function finishGame() {
    if (!sessionId.value) return;
    const res = await api.post('/games/finish', { session_id: sessionId.value });
    finalResult.value = res.data;
    // Clear active session state so navigating back to /games shows the lobby
    sessionId.value = null;
    questions.value = [];
    currentIndex.value = 0;
    isAnswered.value = false;
    lastAnswerResult.value = null;
    return res.data;
  }

  function resetGame() {
    sessionId.value = null;
    questions.value = [];
    currentIndex.value = 0;
    score.value = 0;
    combo.value = 0;
    isAnswered.value = false;
    lastAnswerResult.value = null;
    finalResult.value = null;
  }

  return {
    sessionId,
    questions,
    currentIndex,
    currentQuestion,
    isLastQuestion,
    score,
    combo,
    isAnswered,
    lastAnswerResult,
    finalResult,
    isLoading,
    activeMode,
    activeDirection,
    startGame,
    fetchDeckFields,
    submitAnswer,
    nextQuestion,
    finishGame,
    resetGame,
  };
});

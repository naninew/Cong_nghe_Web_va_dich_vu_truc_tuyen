import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../api/client';
import type { CardDetail } from '../types';

export const useStudyStore = defineStore('study', () => {
  const currentCard = ref<CardDetail | null>(null);
  const remainingCounts = ref({ new: 0, learning: 0, due: 0 });
  const isAnswerRevealed = ref(false);
  const isLoading = ref(false);
  const currentDeckId = ref<number | null>(null);
  const currentFilterMode = ref<string>('all');

  async function fetchNextCard(deckId?: number, filterMode?: string) {
    isLoading.value = true;
    isAnswerRevealed.value = false;
    if (deckId !== undefined) {
      currentDeckId.value = deckId;
    }
    if (filterMode !== undefined) {
      currentFilterMode.value = filterMode;
    }
    try {
      const params: Record<string, any> = {};
      if (currentDeckId.value) params.deck_id = currentDeckId.value;
      if (currentFilterMode.value && currentFilterMode.value !== 'all') {
        params.filter_mode = currentFilterMode.value;
      }
      const res = await api.get('/study/queue', { params });
      currentCard.value = res.data.card;
      remainingCounts.value = res.data.remaining_counts;
      return res.data;
    } finally {
      isLoading.value = false;
    }
  }

  function revealAnswer() {
    isAnswerRevealed.value = true;
  }

  async function answerCard(rating: number, timeTakenMs: number = 0) {
    if (!currentCard.value) return;
    const cardId = currentCard.value.id;
    await api.post('/study/answer', {
      card_id: cardId,
      rating: rating,
      time_taken_ms: timeTakenMs,
    });
    // Immediately fetch next card
    await fetchNextCard();
  }

  async function increaseDailyQuota(amount: number = 10) {
    await api.post('/study/custom-increase', {
      deck_id: currentDeckId.value,
      amount,
    });
    await fetchNextCard();
  }

  return {
    currentCard,
    remainingCounts,
    isAnswerRevealed,
    isLoading,
    currentDeckId,
    fetchNextCard,
    revealAnswer,
    answerCard,
    increaseDailyQuota,
  };
});

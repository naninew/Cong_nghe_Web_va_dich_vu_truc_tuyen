import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../api/client';
import type { DeckTree } from '../types';

export const useDeckStore = defineStore('deck', () => {
  const decks = ref<DeckTree[]>([]);
  const isLoading = ref(false);

  async function fetchDecks() {
    isLoading.value = true;
    try {
      const res = await api.get('/decks');
      decks.value = res.data;
      return res.data;
    } finally {
      isLoading.value = false;
    }
  }

  async function createDeck(name: string, description: string = '') {
    const res = await api.post('/decks', { name, description });
    await fetchDecks();
    return res.data;
  }

  async function deleteDeck(deckId: number) {
    await api.delete(`/decks/${deckId}`);
    await fetchDecks();
  }

  return {
    decks,
    isLoading,
    fetchDecks,
    createDeck,
    deleteDeck,
  };
});

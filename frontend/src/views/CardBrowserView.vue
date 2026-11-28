<template>
  <div class="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6 pb-24 lg:pb-8">
    <!-- Top Action Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-extrabold text-on-surface tracking-tight">Card Browser & Inspector</h1>
        <p class="text-xs text-on-surface-variant">Explore, search, inspect note fields, and manage unremembered cards.</p>
      </div>

      <div class="flex items-center gap-3">
        <!-- Quick Action: Study Filtered Cards -->
        <router-link
          :to="studyFilteredLink"
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-on-primary text-xs font-bold shadow-[0_3px_0_0_#1a0f91] active:translate-y-[2px] active:shadow-none hover:bg-primary-container transition-all"
        >
          <span class="material-symbols-outlined text-base">play_circle</span>
          <span>Study Filtered Cards</span>
        </router-link>

        <!-- Quick Action: Play Quiz -->
        <router-link
          :to="selectedDeckId ? `/games?deck_id=${selectedDeckId}` : '/games'"
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-surface-container-lowest text-on-surface text-xs font-bold border border-outline-variant/30 hover:bg-surface-container-high transition-colors shadow-sm"
        >
          <span class="material-symbols-outlined text-base text-primary">sports_esports</span>
          <span>Quiz</span>
        </router-link>
      </div>
    </div>

    <!-- Filter Bar: Search, Deck Dropdown, State Chips -->
    <div class="flex flex-col gap-3 bg-surface-container-lowest rounded-2xl p-4 border border-outline-variant/20 shadow-sm">
      <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <!-- Search Input -->
        <div class="flex-1 flex items-center gap-2 px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant/20 text-xs">
          <span class="material-symbols-outlined text-outline text-base">search</span>
          <input
            v-model="searchQuery"
            @keyup.enter="applyFilters"
            type="text"
            placeholder="Search Kanji, Hiragana, Vietnamese meanings, or notes..."
            class="bg-transparent border-none outline-none w-full text-on-surface placeholder:text-outline text-xs"
          />
          <button v-if="searchQuery" @click="searchQuery = ''; applyFilters()" class="text-outline hover:text-on-surface">
            <span class="material-symbols-outlined text-base">close</span>
          </button>
        </div>

        <!-- Deck Selector -->
        <select
          v-model="selectedDeckId"
          @change="applyFilters"
          class="px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant/20 text-xs font-semibold text-on-surface outline-none"
        >
          <option :value="null">All Decks & Subdecks</option>
          <option v-for="d in flatDecksList" :key="d.id" :value="d.id">
            {{ d.fullName }} ({{ d.total_cards }})
          </option>
        </select>

        <button
          @click="applyFilters"
          class="px-4 py-2 rounded-xl bg-surface-container-high text-on-surface font-bold text-xs hover:bg-surface-container-highest transition-colors shrink-0"
        >
          Apply Filter
        </button>
      </div>

      <!-- State Filter Chips -->
      <div class="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <button
          v-for="tab in stateTabs"
          :key="tab.value"
          @click="selectedState = tab.value; applyFilters()"
          class="px-3 py-1.5 rounded-xl font-bold transition-all shrink-0 flex items-center gap-1.5"
          :class="selectedState === tab.value ? 'bg-primary text-on-primary shadow-sm' : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high'"
        >
          <span class="material-symbols-outlined text-sm leading-none">{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
        </button>
      </div>
    </div>

    <!-- Cards Data Table -->
    <div class="bg-surface-container-lowest rounded-2xl border border-outline-variant/20 shadow-sm overflow-hidden flex flex-col">
      <!-- Loading State -->
      <div v-if="isLoading" class="p-16 text-center text-outline">
        <span class="material-symbols-outlined animate-spin text-3xl text-primary mb-2">progress_activity</span>
        <p class="text-xs font-semibold">Loading cards matching filter...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="cards.length === 0" class="p-16 text-center">
        <span class="material-symbols-outlined text-4xl text-outline mb-2">find_in_page</span>
        <h3 class="font-bold text-sm text-on-surface">No cards found</h3>
        <p class="text-xs text-on-surface-variant mt-1">Try clearing your search query or selecting another state tab.</p>
      </div>

      <!-- Table View -->
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="border-b border-surface-container-high bg-surface-container-low/40 text-[11px] font-bold uppercase text-outline">
              <th class="py-3 px-4">Expression / Kanji</th>
              <th class="py-3 px-4">Reading</th>
              <th class="py-3 px-4">Meaning (Vietnamese)</th>
              <th class="py-3 px-3">Deck</th>
              <th class="py-3 px-3">Status</th>
              <th class="py-3 px-3 text-center">Lapses</th>
              <th class="py-3 px-3 text-center">Interval</th>
              <th class="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-surface-container-high/40">
            <tr
              v-for="card in cards"
              :key="card.id"
              class="hover:bg-surface-container-low/50 transition-colors cursor-pointer group"
              @click="openCardDetail(card.id)"
            >
              <!-- Expression / Kanji -->
              <td class="py-3 px-4 font-bold text-on-surface text-sm sm:text-base">
                <span class="line-clamp-1">{{ card.fields['Expression'] || card.fields['Kanji'] || card.fields['GrammarTitle'] || '—' }}</span>
              </td>

              <!-- Reading -->
              <td class="py-3 px-4 text-outline font-medium">
                <span class="line-clamp-1">{{ card.fields['Reading'] || card.fields['OnKun'] || '—' }}</span>
              </td>

              <!-- Meaning -->
              <td class="py-3 px-4 text-on-surface-variant font-medium max-w-xs">
                <span class="line-clamp-2">{{ card.fields['Meaning'] || card.fields['Usage'] || '—' }}</span>
              </td>

              <!-- Deck -->
              <td class="py-3 px-3 text-outline text-[11px]">
                <span class="line-clamp-1" :title="card.deck_name">{{ card.deck_name.split('::').pop() }}</span>
              </td>

              <!-- Status badge -->
              <td class="py-3 px-3">
                <span
                  class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                  :class="getStatusBadgeClass(card.state_label)"
                >
                  {{ card.state_label }}
                </span>
              </td>

              <!-- Lapses (Lỗi quên) -->
              <td class="py-3 px-3 text-center font-mono">
                <span
                  class="px-2 py-0.5 rounded text-[11px] font-bold"
                  :class="card.lapses > 2 ? 'bg-red-100 text-red-700' : (card.lapses > 0 ? 'bg-amber-100 text-amber-800' : 'text-outline')"
                >
                  {{ card.lapses }}
                </span>
              </td>

              <!-- Interval -->
              <td class="py-3 px-3 text-center text-outline font-mono">
                {{ formatInterval(card.ivl) }}
              </td>

              <!-- Action buttons -->
              <td class="py-3 px-4 text-right" @click.stop>
                <div class="flex items-center justify-end gap-1">
                  <button
                    @click="openCardDetail(card.id)"
                    class="p-1 rounded-lg text-outline hover:text-primary hover:bg-surface-container transition-colors"
                    title="View & Edit Note"
                  >
                    <span class="material-symbols-outlined text-base">edit</span>
                  </button>
                  <button
                    @click="resetCard(card.id)"
                    class="p-1 rounded-lg text-outline hover:text-amber-700 hover:bg-amber-50 transition-colors"
                    title="Reset to New"
                  >
                    <span class="material-symbols-outlined text-base">restart_alt</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Footer -->
      <div class="flex items-center justify-between p-4 border-t border-surface-container-high/40 text-xs text-on-surface-variant">
        <span>Showing {{ totalCards > 0 ? ((currentPage - 1) * pageSize + 1) : 0 }} to {{ Math.min(currentPage * pageSize, totalCards) }} of {{ totalCards.toLocaleString() }} cards</span>

        <div class="flex items-center gap-2">
          <button
            :disabled="currentPage <= 1"
            @click="goToPage(currentPage - 1)"
            class="px-3 py-1.5 rounded-xl border border-outline-variant/30 font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-surface-container transition-colors"
          >
            Previous
          </button>
          <span class="font-mono text-outline">{{ currentPage }} / {{ totalPages }}</span>
          <button
            :disabled="currentPage >= totalPages"
            @click="goToPage(currentPage + 1)"
            class="px-3 py-1.5 rounded-xl border border-outline-variant/30 font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-surface-container transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- Card Detail / Edit Note Modal -->
    <div
      v-if="activeCardModal"
      class="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-surface-container-lowest rounded-2xl p-6 max-w-2xl w-full border border-outline-variant/30 shadow-2xl flex flex-col gap-4 max-h-[90vh] overflow-y-auto">
        <!-- Modal Header -->
        <div class="flex items-center justify-between pb-3 border-b border-surface-container-high">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-2xl">style</span>
            <div>
              <h2 class="font-bold text-base text-on-surface">Card Note Inspector</h2>
              <span class="text-[11px] text-outline">{{ activeCardModal.deck_name }}</span>
            </div>
          </div>
          <button @click="activeCardModal = null" class="text-outline hover:text-on-surface">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <!-- Rendered Card Preview Tabs -->
        <div class="flex flex-col gap-2 bg-surface-container-low/40 p-4 rounded-xl border border-outline-variant/20">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs font-bold uppercase text-outline">Rendered HTML Output</span>
            <div class="flex gap-2">
              <button
                @click="previewFace = 'front'"
                class="px-2.5 py-1 rounded text-xs font-bold"
                :class="previewFace === 'front' ? 'bg-primary text-on-primary' : 'bg-surface-container text-outline'"
              >
                Front Face
              </button>
              <button
                @click="previewFace = 'back'"
                class="px-2.5 py-1 rounded text-xs font-bold"
                :class="previewFace === 'back' ? 'bg-primary text-on-primary' : 'bg-surface-container text-outline'"
              >
                Back Face
              </button>
            </div>
          </div>

          <div
            v-if="activeCardModal.rendered"
            class="max-h-64 overflow-y-auto p-4 bg-surface-container-lowest rounded-xl border border-outline-variant/30 text-center"
            v-html="sanitizeCardHtml(previewFace === 'front' ? activeCardModal.rendered.front_html : activeCardModal.rendered.back_html)"
            @click="handleAnkiHtmlClick"
          ></div>
        </div>

        <!-- Note Fields Editor -->
        <div class="flex flex-col gap-3">
          <span class="text-xs font-bold uppercase text-outline">Editable Note Fields</span>
          <div v-for="(val, fieldName) in editFields" :key="fieldName" class="flex flex-col gap-1">
            <label class="text-[11px] font-bold text-on-surface-variant">{{ fieldName }}</label>
            <input
              v-model="editFields[fieldName]"
              type="text"
              class="px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant/20 text-xs text-on-surface outline-none focus:border-primary"
            />
          </div>
        </div>

        <!-- Modal Footer Actions -->
        <div class="flex items-center justify-between pt-3 border-t border-surface-container-high mt-2">
          <div class="flex items-center gap-2">
            <button
              @click="toggleSuspendCard"
              class="px-3 py-2 rounded-xl border border-outline-variant/30 text-xs font-bold text-on-surface hover:bg-surface-container transition-colors flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-sm">pause_circle</span>
              <span>{{ activeCardModal.queue === -1 ? 'Unsuspend Card' : 'Suspend Card' }}</span>
            </button>

            <button
              @click="deleteCurrentCard"
              class="px-3 py-2 rounded-xl border border-red-200 text-xs font-bold text-red-600 hover:bg-red-50 transition-colors flex items-center gap-1.5"
            >
              <span class="material-symbols-outlined text-sm">delete</span>
              <span>Xóa Thẻ</span>
            </button>
          </div>

          <div class="flex items-center gap-2">
            <button
              @click="activeCardModal = null"
              class="px-4 py-2 rounded-xl text-xs font-bold text-outline hover:bg-surface-container"
            >
              Cancel
            </button>
            <button
              @click="saveCardChanges"
              class="px-5 py-2 rounded-xl bg-primary text-on-primary text-xs font-bold shadow-sm hover:bg-primary-container transition-colors"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { sanitizeCardHtml, handleAnkiHtmlClick } from '../utils/ankiHtml';
import { useRoute } from 'vue-router';
import { useDeckStore } from '../stores/deck';
import api from '../api/client';
import type { CardBrowseItem, DeckTree } from '../types';

const route = useRoute();
const deckStore = useDeckStore();

const searchQuery = ref('');
const selectedDeckId = ref<number | null>(null);
const selectedState = ref('all');
const currentPage = ref(1);
const pageSize = ref(20);

const isLoading = ref(false);
const cards = ref<CardBrowseItem[]>([]);
const totalCards = ref(0);
const totalPages = ref(1);

const activeCardModal = ref<any | null>(null);
const editFields = ref<Record<string, string>>({});
const previewFace = ref<'front' | 'back'>('front');

const stateTabs = [
  { label: 'All Cards', value: 'all', icon: 'style' },
  { label: 'Need Review (Lapsed)', value: 'lapsed', icon: 'warning' },
  { label: 'Due Today', value: 'due', icon: 'schedule' },
  { label: 'Learning', value: 'learning', icon: 'school' },
  { label: 'New', value: 'new', icon: 'add_circle' },
  { label: 'Suspended', value: 'suspended', icon: 'pause_circle' },
];

const studyFilteredLink = computed(() => {
  const params = new URLSearchParams();
  if (selectedDeckId.value) params.set('deck_id', String(selectedDeckId.value));
  if (selectedState.value === 'lapsed') params.set('filter_mode', 'lapsed_only');
  else if (selectedState.value === 'due') params.set('filter_mode', 'due_only');
  else if (selectedState.value === 'new') params.set('filter_mode', 'new_only');
  return `/study?${params.toString()}`;
});

const flatDecksList = computed(() => {
  const result: Array<{ id: number; fullName: string; total_cards: number }> = [];
  function traverse(nodes: DeckTree[], prefix = '') {
    for (const n of nodes) {
      const full = prefix ? `${prefix}::${n.name}` : n.name;
      result.push({ id: n.id, fullName: full, total_cards: n.total_cards });
      if (n.children && n.children.length > 0) {
        traverse(n.children, full);
      }
    }
  }
  traverse(deckStore.decks);
  return result;
});

onMounted(async () => {
  await deckStore.fetchDecks();
  if (route.query.deck_id) {
    selectedDeckId.value = Number(route.query.deck_id);
  }
  if (route.query.state) {
    selectedState.value = String(route.query.state);
  }
  await fetchCards();
});

async function fetchCards() {
  isLoading.value = true;
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value,
      state: selectedState.value,
    };
    if (selectedDeckId.value) params.deck_id = selectedDeckId.value;
    if (searchQuery.value && searchQuery.value.trim()) params.search = searchQuery.value.trim();

    const res = await api.get('/cards/browse', { params });
    cards.value = res.data.items;
    totalCards.value = res.data.total;
    totalPages.value = res.data.total_pages;
  } catch (err) {
    console.error('Failed to browse cards:', err);
  } finally {
    isLoading.value = false;
  }
}

function applyFilters() {
  currentPage.value = 1;
  fetchCards();
}

function goToPage(page: number) {
  currentPage.value = page;
  fetchCards();
}

function getStatusBadgeClass(lbl: string) {
  switch (lbl) {
    case 'Due': return 'bg-emerald-100 text-emerald-800';
    case 'Learning': return 'bg-amber-100 text-amber-800';
    case 'New': return 'bg-blue-100 text-blue-800';
    case 'Suspended': return 'bg-gray-100 text-gray-700';
    default: return 'bg-surface-container text-on-surface-variant';
  }
}

function formatInterval(ivl: number) {
  if (ivl <= 0) return '0d';
  if (ivl < 30) return `${ivl}d`;
  if (ivl < 365) return `${Math.round(ivl / 30)}m`;
  return `${Math.round(ivl / 365)}y`;
}

async function openCardDetail(cardId: number) {
  try {
    const res = await api.get(`/cards/${cardId}`);
    activeCardModal.value = res.data;
    editFields.value = { ...res.data.fields };
  } catch (err) {
    alert('Failed to load card details.');
  }
}

async function saveCardChanges() {
  if (!activeCardModal.value) return;
  try {
    await api.patch(`/cards/${activeCardModal.value.id}`, {
      fields: editFields.value,
    });
    activeCardModal.value = null;
    await fetchCards();
  } catch (err) {
    alert('Failed to save changes.');
  }
}

async function toggleSuspendCard() {
  if (!activeCardModal.value) return;
  const isSuspended = activeCardModal.value.queue === -1;
  try {
    await api.patch(`/cards/${activeCardModal.value.id}`, {
      is_suspended: !isSuspended,
    });
    activeCardModal.value = null;
    await fetchCards();
  } catch (err) {
    alert('Failed to update card status.');
  }
}

async function deleteCurrentCard() {
  if (!activeCardModal.value) return;
  if (!confirm(`Bạn có chắc muốn xóa thẻ #${activeCardModal.value.id} không?`)) return;
  try {
    await api.delete(`/cards/${activeCardModal.value.id}`);
    activeCardModal.value = null;
    await fetchCards();
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Lỗi khi xóa thẻ.');
  }
}

async function resetCard(cardId: number) {
  if (!confirm('Are you sure you want to reset this card SRS progress back to New?')) return;
  try {
    await api.post(`/cards/${cardId}/reset`);
    await fetchCards();
  } catch (err) {
    alert('Failed to reset card progress.');
  }
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <!-- Deck Node Bar -->
    <div
      class="bg-surface-container-lowest rounded-2xl p-3.5 sm:p-4 border border-outline-variant/20 shadow-sm hover:border-primary/30 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
      :style="{ marginLeft: `${Math.min(depth * 18, 72)}px` }"
    >
      <!-- Left: Expand icon, Folder Icon, Name & Badges -->
      <div class="flex items-center gap-2.5 min-w-0">
        <!-- Expand/Collapse toggle if has children -->
        <button
          v-if="hasChildren"
          @click="isExpanded = !isExpanded"
          class="w-6 h-6 flex items-center justify-center rounded-lg hover:bg-surface-container text-outline hover:text-on-surface transition-colors shrink-0"
        >
          <span class="material-symbols-outlined text-lg transition-transform duration-200" :class="{ 'rotate-90': isExpanded }">
            chevron_right
          </span>
        </button>
        <span v-else class="w-6 shrink-0 flex items-center justify-center text-outline/40 text-xs">
          ·
        </span>

        <!-- Folder icon with level color -->
        <span
          class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0"
          :class="depth === 0 ? 'bg-primary-fixed text-on-primary-fixed font-bold' : 'bg-surface-container-high text-on-surface-variant'"
        >
          <span class="material-symbols-outlined text-lg">
            {{ depth === 0 ? 'folder' : (hasChildren ? 'folder_open' : 'style') }}
          </span>
        </span>

        <!-- Deck Title & Relative Name -->
        <div class="flex flex-col min-w-0">
          <div class="flex items-center gap-2">
            <h3 class="font-bold text-sm text-on-surface truncate" :title="deck.name">
              {{ deck.name }}
            </h3>
            <span
              v-if="deck.total_cards > 0"
              class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-surface-container text-on-surface-variant shrink-0"
            >
              {{ deck.total_cards.toLocaleString() }} cards
            </span>
          </div>

          <!-- Counter badges (New, Learning, Due) -->
          <div class="flex items-center gap-2 text-[11px] font-medium mt-0.5">
            <span class="text-blue-600 font-bold">{{ deck.counts.new }} New</span>
            <span class="text-outline">·</span>
            <span class="text-amber-600 font-bold">{{ deck.counts.learning }} Learning</span>
            <span class="text-outline">·</span>
            <span class="text-emerald-600 font-bold">{{ deck.counts.due }} Due</span>
          </div>
        </div>
      </div>

      <!-- Right: Action buttons -->
      <div class="flex items-center gap-2 shrink-0 self-end sm:self-center">
        <!-- Study button -->
        <router-link
          :to="`/study?deck_id=${deck.id}`"
          class="px-3 py-1.5 rounded-xl bg-primary text-on-primary text-xs font-bold shadow-[0_2px_0_0_#1a0f91] active:translate-y-[1px] active:shadow-none hover:bg-primary-container transition-all flex items-center gap-1"
        >
          <span class="material-symbols-outlined text-sm leading-none">play_arrow</span>
          <span>Study</span>
        </router-link>

        <!-- Quiz button -->
        <router-link
          :to="`/games?deck_id=${deck.id}`"
          class="px-3 py-1.5 rounded-xl bg-surface-container-low text-on-surface text-xs font-bold border border-outline-variant/30 hover:bg-surface-container-high transition-colors flex items-center gap-1"
        >
          <span class="material-symbols-outlined text-sm leading-none text-primary">sports_esports</span>
          <span>Quiz</span>
        </router-link>

        <!-- Browse cards button -->
        <router-link
          :to="`/browse?deck_id=${deck.id}`"
          class="p-1.5 rounded-xl text-outline hover:text-on-surface hover:bg-surface-container transition-colors"
          title="Browse Cards in this Deck"
        >
          <span class="material-symbols-outlined text-lg">search</span>
        </router-link>

        <!-- Stats button (Hizashi Dashboard equivalent) -->
        <router-link
          :to="`/decks/${deck.id}/stats`"
          class="p-1.5 rounded-xl text-outline hover:text-primary hover:bg-surface-container transition-colors"
          title="Thống kê chuyên sâu (Hizashi Dashboard)"
        >
          <span class="material-symbols-outlined text-lg">insights</span>
        </router-link>

        <!-- Edit Deck button -->
        <button
          @click="$emit('editDeck', deck)"
          class="p-1.5 rounded-xl text-outline hover:text-on-surface hover:bg-surface-container transition-colors"
          title="Đổi tên / Chỉnh sửa bộ thẻ"
        >
          <span class="material-symbols-outlined text-lg">edit</span>
        </button>

        <!-- Delete Deck button -->
        <button
          @click="$emit('deleteDeck', deck)"
          class="p-1.5 rounded-xl text-outline hover:text-red-600 hover:bg-red-50 transition-colors"
          title="Xóa bộ thẻ"
        >
          <span class="material-symbols-outlined text-lg">delete</span>
        </button>

        <!-- Export .apkg button -->
        <a
          :href="`/api/v1/import-export/export/deck/${deck.id}`"
          target="_blank"
          class="p-1.5 rounded-xl text-outline hover:text-on-surface hover:bg-surface-container transition-colors"
          title="Export Deck as .apkg"
        >
          <span class="material-symbols-outlined text-lg">download</span>
        </a>
      </div>
    </div>

    <!-- Recursive Subdecks List -->
    <div
      v-if="hasChildren && isExpanded"
      class="flex flex-col gap-2 pl-2 sm:pl-3 border-l-2 border-surface-container-high ml-4 transition-all"
    >
      <DeckTreeItem
        v-for="sub in deck.children"
        :key="sub.id"
        :deck="sub"
        :depth="depth + 1"
        @edit-deck="$emit('editDeck', $event)"
        @delete-deck="$emit('deleteDeck', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { DeckTree } from '../../types';

const props = withDefaults(
  defineProps<{
    deck: DeckTree;
    depth?: number;
  }>(),
  {
    depth: 0,
  }
);

defineEmits<{
  (e: 'editDeck', deck: DeckTree): void;
  (e: 'deleteDeck', deck: DeckTree): void;
}>();

// Default expand root nodes and first 2 levels
const isExpanded = ref(props.depth < 2);
const hasChildren = computed(() => props.deck.children && props.deck.children.length > 0);
</script>

<template>
  <div class="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-8 pb-24 lg:pb-8">
    <!-- Welcome & Quick Action Banner -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-surface-container-lowest via-surface-container-low to-surface-container p-6 sm:p-8 shadow-sm border border-outline-variant/20">
      <div class="absolute -right-12 -top-12 w-64 h-64 rounded-full bg-primary-fixed-dim/20 blur-3xl pointer-events-none"></div>
      <div class="absolute right-48 -bottom-16 w-56 h-56 rounded-full bg-secondary-fixed/25 blur-2xl pointer-events-none"></div>
      
      <div class="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div class="flex flex-col gap-2 max-w-2xl">
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-full bg-primary-fixed text-on-primary-fixed text-[11px] font-bold uppercase tracking-wider">
              Active Session
            </span>
            <span class="text-xs text-outline font-medium">Anki SM-2 & FSRS Engines Active</span>
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold text-on-surface tracking-tight">
            Good day, {{ authStore.user?.display_name || 'Scholar' }}!
          </h1>
          <p class="text-sm text-on-surface-variant leading-relaxed">
            You have <span class="font-bold text-primary">{{ stats?.due_count || 0 }} cards</span> ready for spaced review today. Keep your momentum going!
          </p>
        </div>

        <div class="flex items-center gap-3 flex-wrap">
          <router-link
            to="/study"
            class="flex items-center gap-2 px-5 py-3 rounded-xl bg-primary text-on-primary font-bold text-sm shadow-[0_3px_0_0_#1a0f91] active:translate-y-[2px] active:shadow-none hover:bg-primary-container transition-all"
          >
            <span class="material-symbols-outlined text-lg">play_circle</span>
            <span>Study Cards ({{ stats?.due_count || 0 }})</span>
          </router-link>

          <router-link
            to="/study?filter_mode=lapsed_only"
            class="flex items-center gap-2 px-4 py-3 rounded-xl bg-amber-500/10 text-amber-700 font-bold text-sm border border-amber-500/30 hover:bg-amber-500/20 transition-colors shadow-sm"
          >
            <span class="material-symbols-outlined text-lg text-amber-700">replay</span>
            <span>Review Weak Cards</span>
          </router-link>

          <router-link
            to="/games"
            class="flex items-center gap-2 px-5 py-3 rounded-xl bg-surface-container-lowest text-on-surface font-bold text-sm hover:bg-surface-container-high transition-colors shadow-[0_3px_0_0_#dae2fd] active:translate-y-[2px] active:shadow-none"
          >
            <span class="material-symbols-outlined text-lg text-primary">sports_esports</span>
            <span>Quick Quiz</span>
          </router-link>
        </div>
      </div>
    </div>

    <!-- Stats Error Banner -->
    <div
      v-if="statsError"
      class="px-4 py-3 rounded-xl bg-red-50 border border-error/30 text-error text-xs font-semibold flex items-center justify-between gap-3"
    >
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-base shrink-0">error</span>
        <span>{{ statsError }}</span>
      </div>
      <button
        @click="loadDashboardData"
        type="button"
        class="px-3 py-1 rounded-lg bg-error text-white text-[11px] font-bold hover:opacity-90 transition-opacity shrink-0"
      >
        Thử lại
      </button>
    </div>

    <!-- 4 Key Metrics Bento Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 sm:gap-6">
      <!-- Metric 1: Daily Goal -->
      <div class="bg-surface-container-lowest rounded-2xl p-5 shadow-sm border border-outline-variant/20 flex flex-col justify-between">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-outline">Daily Goal</span>
          <span class="material-symbols-outlined text-primary text-xl">flag</span>
        </div>
        <div class="my-4">
          <div class="flex items-baseline gap-2">
            <span class="text-3xl font-extrabold text-on-surface">{{ stats?.daily_goal.completed ?? 0 }}</span>
            <span class="text-sm text-outline">/ {{ dailyGoalTarget }} cards</span>
          </div>
          <!-- Progress bar -->
          <div class="w-full h-2 rounded-full bg-surface-container-high mt-3 overflow-hidden">
            <div
              class="h-full rounded-full bg-primary transition-all duration-500"
              :style="{ width: `${Math.min(100, ((stats?.daily_goal.completed ?? 0) / dailyGoalTarget) * 100)}%` }"
            ></div>
          </div>
        </div>
        <span class="text-[11px] text-on-surface-variant font-medium">Reset daily at 4:00 AM</span>
      </div>

      <!-- Metric 2: Streak -->
      <div class="bg-surface-container-lowest rounded-2xl p-5 shadow-sm border border-outline-variant/20 flex flex-col justify-between">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-outline">Study Streak</span>
          <span class="material-symbols-outlined text-amber-600 text-xl">local_fire_department</span>
        </div>
        <div class="my-4">
          <div class="flex items-baseline gap-2">
            <span class="text-3xl font-extrabold text-amber-700">{{ stats?.user.streak_days ?? 0 }}</span>
            <span class="text-sm text-outline">Days in a row</span>
          </div>
          <p class="text-xs text-on-surface-variant mt-2">
            {{ (stats?.user.streak_days ?? 0) > 0 ? 'Study today to maintain streak!' : 'Complete a review today to start your streak!' }}
          </p>
        </div>
        <span class="text-[11px] font-bold uppercase" :class="(stats?.user.streak_days ?? 0) > 0 ? 'text-amber-700' : 'text-outline'">
          {{ (stats?.user.streak_days ?? 0) > 0 ? 'Active Habit' : 'Start Today' }}
        </span>
      </div>

      <!-- Metric 3: Total Cards In Library -->
      <div class="bg-surface-container-lowest rounded-2xl p-5 shadow-sm border border-outline-variant/20 flex flex-col justify-between">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-outline">Total Cards</span>
          <span class="material-symbols-outlined text-secondary text-xl">style</span>
        </div>
        <div class="my-4">
          <div class="flex items-baseline gap-2">
            <span class="text-3xl font-extrabold text-on-surface">{{ (stats?.total_cards ?? 0).toLocaleString() }}</span>
            <span class="text-sm text-outline">cards</span>
          </div>
          <div class="flex items-center gap-2 mt-2 text-xs text-on-surface-variant">
            <span class="text-secondary font-bold">{{ stats?.mature_cards ?? 0 }} mature</span> ·
            <span class="text-primary font-bold">{{ stats?.new_cards ?? 0 }} new</span>
          </div>
        </div>
        <span class="text-[11px] text-outline font-medium">Across all decks</span>
      </div>

      <!-- Metric 4: True Retention Rate -->
      <div class="bg-surface-container-lowest rounded-2xl p-5 shadow-sm border border-outline-variant/20 flex flex-col justify-between">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-outline">Retention Rate</span>
          <span class="material-symbols-outlined text-secondary text-xl">verified</span>
        </div>
        <div class="my-4">
          <div class="flex items-baseline gap-2">
            <span class="text-3xl font-extrabold text-secondary">
              {{ stats?.retention_rate != null ? `${stats.retention_rate}%` : '—' }}
            </span>
            <span v-if="stats?.retention_rate != null" class="text-xs text-outline font-medium">accuracy</span>
          </div>
          <p class="text-xs text-on-surface-variant mt-2">Last 30 days review accuracy</p>
        </div>
        <span class="text-[11px] font-bold" :class="retentionStatus.className">
          {{ retentionStatus.label }}
        </span>
      </div>
    </div>

    <!-- Active Decks Section -->
    <div class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-bold text-on-surface">Your Flashcard Decks</h2>
          <p class="text-xs text-on-surface-variant">Select a deck to start reviewing or playing</p>
        </div>
        <router-link
          to="/library"
          class="text-xs font-bold text-primary hover:underline flex items-center gap-1"
        >
          <span>View All in Library</span>
          <span class="material-symbols-outlined text-base">arrow_forward</span>
        </router-link>
      </div>

      <!-- Empty State when user has no decks -->
      <div
        v-if="!deckStore.isLoading && deckStore.decks.length === 0"
        class="bg-surface-container-lowest rounded-2xl p-8 border border-dashed border-outline-variant/40 text-center flex flex-col items-center gap-3"
      >
        <div class="w-14 h-14 rounded-2xl bg-primary-fixed/40 text-primary flex items-center justify-center">
          <span class="material-symbols-outlined text-3xl">library_add</span>
        </div>
        <div class="flex flex-col gap-1">
          <h3 class="font-bold text-base text-on-surface">Chưa có bộ thẻ nào</h3>
          <p class="text-xs text-on-surface-variant max-w-md">
            Hãy tạo bộ thẻ mới hoặc import file Anki (.apkg) trong Thư viện để bắt đầu học và chơi Quiz.
          </p>
        </div>
        <router-link
          to="/library"
          class="mt-1 px-5 py-2.5 rounded-xl bg-primary text-on-primary text-xs font-bold shadow-[0_3px_0_0_#1a0f91] active:translate-y-[2px] active:shadow-none hover:bg-primary-container transition-all"
        >
          Đi tới Thư viện
        </router-link>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="deck in deckStore.decks.slice(0, 6)"
          :key="deck.id"
          class="bg-surface-container-lowest rounded-2xl p-5 border border-outline-variant/20 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between gap-4"
        >
          <div>
            <div class="flex items-start justify-between gap-2">
              <h3 class="font-bold text-base text-on-surface line-clamp-1">{{ deck.name }}</h3>
              <span class="px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant text-[11px] font-semibold">
                {{ deck.total_cards.toLocaleString() }} cards
              </span>
            </div>
            <p class="text-xs text-on-surface-variant line-clamp-2 mt-1">{{ deck.description || 'No description provided.' }}</p>
          </div>

          <!-- Due counts badges -->
          <div class="flex items-center gap-2 text-xs">
            <span class="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold text-[11px]">
              {{ deck.counts.new }} New
            </span>
            <span class="px-2 py-0.5 rounded bg-amber-50 text-amber-700 font-semibold text-[11px]">
              {{ deck.counts.learning }} Learning
            </span>
            <span class="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold text-[11px]">
              {{ deck.counts.due }} Due
            </span>
          </div>

          <!-- Card actions -->
          <div class="flex items-center gap-2 pt-2 border-t border-surface-container-high/40">
            <router-link
              :to="`/study?deck_id=${deck.id}`"
              class="flex-1 py-2 rounded-xl bg-primary text-on-primary text-xs font-bold text-center hover:bg-primary-container transition-colors"
            >
              Study
            </router-link>
            <router-link
              :to="`/games?deck_id=${deck.id}`"
              class="flex-1 py-2 rounded-xl bg-surface-container-low text-on-surface text-xs font-bold text-center hover:bg-surface-container-high transition-colors"
            >
              Quiz
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useDeckStore } from '../stores/deck';
import api from '../api/client';
import type { StatsOverview } from '../types';

const authStore = useAuthStore();
const deckStore = useDeckStore();
const stats = ref<StatsOverview | null>(null);
const statsError = ref<string | null>(null);

const dailyGoalTarget = computed(() => {
  return stats.value?.daily_goal.target || authStore.user?.daily_goal || 50;
});

const retentionStatus = computed(() => {
  const rate = stats.value?.retention_rate;
  if (rate == null) {
    return { label: 'Chưa có dữ liệu ôn tập', className: 'text-outline' };
  }
  if (rate >= 85) {
    return { label: 'Excellent Memory Retention', className: 'text-secondary' };
  }
  if (rate >= 70) {
    return { label: 'Good Memory Retention', className: 'text-amber-700' };
  }
  return { label: 'Needs More Review', className: 'text-error' };
});

async function loadDashboardData() {
  statsError.value = null;
  try {
    await deckStore.fetchDecks();
  } catch (err) {
    console.error('Failed to load decks:', err);
  }
  try {
    const res = await api.get('/stats/overview');
    stats.value = res.data;
  } catch (err: any) {
    console.error('Failed to load stats:', err);
    statsError.value =
      err?.response?.data?.detail || 'Không thể tải thống kê học tập. Vui lòng thử lại.';
  }
}

onMounted(loadDashboardData);
</script>

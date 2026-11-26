<template>
  <div class="w-full max-w-2xl mx-auto px-4 py-12 flex flex-col items-center justify-center min-h-[calc(100vh-80px)] pb-24 lg:pb-8">
    <div class="w-full bg-surface-container-lowest rounded-2xl p-6 sm:p-10 border border-outline-variant/30 shadow-md text-center flex flex-col items-center gap-6">
      <!-- Crown / Trophy icon -->
      <div class="w-20 h-20 rounded-full bg-secondary-fixed/40 text-secondary flex items-center justify-center shadow-md animate-bounce">
        <span class="material-symbols-outlined text-4xl">emoji_events</span>
      </div>

      <div class="flex flex-col gap-1">
        <span class="text-xs font-bold uppercase tracking-wider text-outline">Session Complete</span>
        <h1 class="text-2xl sm:text-3xl font-extrabold text-on-surface">Great Performance!</h1>
        <p class="text-xs sm:text-sm text-on-surface-variant">
          Your answers have been synchronized with your spaced repetition retention schedule.
        </p>
      </div>

      <!-- Key Results Grid -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full my-2">
        <div class="p-4 rounded-xl bg-surface-container-low flex flex-col items-center">
          <span class="text-xs text-outline font-semibold">Accuracy</span>
          <span class="text-2xl font-extrabold text-secondary mt-1">
            {{ gameStore.finalResult?.accuracy_percent || 0 }}%
          </span>
        </div>

        <div class="p-4 rounded-xl bg-surface-container-low flex flex-col items-center">
          <span class="text-xs text-outline font-semibold">Total Score</span>
          <span class="text-2xl font-extrabold text-on-surface mt-1">
            {{ gameStore.finalResult?.score || 0 }}
          </span>
        </div>

        <div class="p-4 rounded-xl bg-surface-container-low flex flex-col items-center">
          <span class="text-xs text-outline font-semibold">XP Earned</span>
          <span class="text-2xl font-extrabold text-amber-600 mt-1">
            +{{ gameStore.finalResult?.xp_earned || 0 }}
          </span>
        </div>

        <div class="p-4 rounded-xl bg-surface-container-low flex flex-col items-center">
          <span class="text-xs text-outline font-semibold">Time Taken</span>
          <span class="text-2xl font-extrabold text-on-surface mt-1">
            {{ gameStore.finalResult?.duration_seconds || 0 }}s
          </span>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-3 w-full pt-4 border-t border-surface-container-high/40">
        <router-link
          to="/dashboard"
          class="flex-1 py-3 rounded-xl bg-surface-container-low text-on-surface font-bold text-xs hover:bg-surface-container-high transition-colors text-center"
        >
          Dashboard
        </router-link>

        <button
          @click="playAgain"
          type="button"
          class="flex-1 py-3 rounded-xl bg-primary text-on-primary font-bold text-xs shadow-[0_3px_0_0_#1a0f91] active:translate-y-[2px] active:shadow-none hover:bg-primary-container transition-all text-center"
        >
          Play Again
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useGameStore } from '../stores/game';

const router = useRouter();
const gameStore = useGameStore();

function playAgain() {
  gameStore.resetGame();
  router.push('/games');
}
</script>

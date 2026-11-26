<template>
  <div class="w-full max-w-2xl mx-auto px-4 py-12 flex flex-col items-center justify-center min-h-[calc(100vh-80px)] pb-24 lg:pb-8">
    <!-- Loading State -->
    <div
      v-if="isLoading"
      class="w-full bg-surface-container-lowest rounded-2xl p-10 border border-outline-variant/30 shadow-md text-center flex flex-col items-center gap-3"
    >
      <span class="material-symbols-outlined text-4xl text-primary animate-spin">progress_activity</span>
      <p class="text-sm font-semibold text-on-surface-variant">Đang tải kết quả ván chơi...</p>
    </div>

    <!-- Error / Missing Result State -->
    <div
      v-else-if="loadError || !gameStore.finalResult"
      class="w-full bg-surface-container-lowest rounded-2xl p-8 border border-outline-variant/30 shadow-md text-center flex flex-col items-center gap-4"
    >
      <div class="w-16 h-16 rounded-full bg-red-50 text-error flex items-center justify-center">
        <span class="material-symbols-outlined text-3xl">error_outline</span>
      </div>
      <div class="flex flex-col gap-1">
        <h1 class="text-xl font-extrabold text-on-surface">Không tìm thấy kết quả</h1>
        <p class="text-xs sm:text-sm text-on-surface-variant">
          {{ loadError || 'Chưa có dữ liệu phiên chơi nào để hiển thị.' }}
        </p>
      </div>
      <button
        @click="playAgain"
        type="button"
        class="px-6 py-2.5 rounded-xl bg-primary text-on-primary font-bold text-xs shadow-[0_3px_0_0_#1a0f91] active:translate-y-[2px] active:shadow-none hover:bg-primary-container transition-all"
      >
        Quay lại Quiz Game
      </button>
    </div>

    <!-- Result Card -->
    <div v-else class="w-full bg-surface-container-lowest rounded-2xl p-6 sm:p-10 border border-outline-variant/30 shadow-md text-center flex flex-col items-center gap-6">
      <!-- Crown / Trophy icon -->
      <div class="w-20 h-20 rounded-full bg-secondary-fixed/40 text-secondary flex items-center justify-center shadow-md animate-bounce">
        <span class="material-symbols-outlined text-4xl">emoji_events</span>
      </div>

      <div class="flex flex-col gap-1">
        <span class="text-xs font-bold uppercase tracking-wider text-outline">Session Complete</span>
        <h1 class="text-2xl sm:text-3xl font-extrabold text-on-surface">Great Performance!</h1>
        <p v-if="gameStore.finalResult.srs_sync !== false" class="text-xs sm:text-sm text-on-surface-variant">
          Kết quả trả lời của bạn đã được đồng bộ vào lịch ôn tập Anki SRS.
        </p>
        <p v-else class="text-xs sm:text-sm text-on-surface-variant">
          Chế độ luyện tập: Anki SRS Sync đang tắt, lịch ôn tập thẻ của bạn không bị thay đổi.
        </p>
      </div>

      <!-- Key Results Grid -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full my-2">
        <div class="p-4 rounded-xl bg-surface-container-low flex flex-col items-center">
          <span class="text-xs text-outline font-semibold">Accuracy</span>
          <span class="text-2xl font-extrabold text-secondary mt-1">
            {{ gameStore.finalResult.accuracy_percent || 0 }}%
          </span>
        </div>

        <div class="p-4 rounded-xl bg-surface-container-low flex flex-col items-center">
          <span class="text-xs text-outline font-semibold">Total Score</span>
          <span class="text-2xl font-extrabold text-on-surface mt-1">
            {{ gameStore.finalResult.score || 0 }}
          </span>
        </div>

        <div class="p-4 rounded-xl bg-surface-container-low flex flex-col items-center">
          <span class="text-xs text-outline font-semibold">XP Earned</span>
          <span class="text-2xl font-extrabold text-amber-600 mt-1">
            +{{ gameStore.finalResult.xp_earned || 0 }}
          </span>
        </div>

        <div class="p-4 rounded-xl bg-surface-container-low flex flex-col items-center">
          <span class="text-xs text-outline font-semibold">Time Taken</span>
          <span class="text-2xl font-extrabold text-on-surface mt-1">
            {{ gameStore.finalResult.duration_seconds || 0 }}s
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
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useGameStore } from '../stores/game';

const route = useRoute();
const router = useRouter();
const gameStore = useGameStore();

const isLoading = ref(false);
const loadError = ref<string | null>(null);

onMounted(async () => {
  const querySessionId = typeof route.query.session_id === 'string' ? route.query.session_id.trim() : '';
  if (querySessionId && gameStore.finalResult?.session_id !== querySessionId) {
    isLoading.value = true;
    loadError.value = null;
    try {
      await gameStore.fetchGameResult(querySessionId);
    } catch (err: any) {
      loadError.value =
        err?.response?.data?.detail ||
        'Không thể tải kết quả ván chơi này hoặc bạn không có quyền xem.';
    } finally {
      isLoading.value = false;
    }
  }
});

function playAgain() {
  gameStore.resetGame();
  router.push('/games');
}
</script>

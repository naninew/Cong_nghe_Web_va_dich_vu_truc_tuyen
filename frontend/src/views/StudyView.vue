<template>
  <div class="w-full max-w-4xl mx-auto px-4 py-6 flex flex-col items-center min-h-[calc(100vh-80px)] justify-between pb-24 lg:pb-8 select-none">
    <!-- Top Study Session Header -->
    <header class="w-full flex items-center justify-between text-xs font-semibold text-on-surface-variant mb-4">
      <div class="flex items-center gap-2">
        <router-link to="/library" class="p-1.5 rounded-lg hover:bg-surface-container transition-colors" title="Quay lại Thư viện">
          <span class="material-symbols-outlined text-lg">arrow_back</span>
        </router-link>
        <span class="font-bold text-on-surface truncate max-w-[220px] sm:max-w-md">
          {{ studyStore.currentCard?.deck_name || 'Phiên Học Spaced Repetition' }}
        </span>
        <!-- Link to Deck Stats -->
        <router-link
          v-if="studyStore.currentCard?.deck_id"
          :to="`/decks/${studyStore.currentCard.deck_id}/stats`"
          class="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-surface-container hover:bg-surface-container-high text-[11px] font-bold text-primary transition-colors shadow-sm"
          title="Xem Phân Tích & Ma Trận Từ"
        >
          <span class="material-symbols-outlined text-sm leading-none">insights</span>
          <span class="hidden sm:inline">Thống Kê</span>
        </router-link>
      </div>

      <!-- Card Queue Counters (Anki-Compliant: New, Learn, Due) -->
      <div class="flex items-center gap-2 font-mono">
        <span class="px-2.5 py-1 rounded-lg bg-blue-100 text-blue-800 text-xs font-bold" title="Thẻ Mới Hôm Nay (Hạn ngạch còn lại)">
          {{ studyStore.remainingCounts.new }} Mới
        </span>
        <span class="px-2.5 py-1 rounded-lg bg-amber-100 text-amber-800 text-xs font-bold" title="Thẻ Đang Học / Học Lại Đến Hạn">
          {{ studyStore.remainingCounts.learning }} Đang học
        </span>
        <span class="px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-800 text-xs font-bold" title="Thẻ Ôn Tập Đến Hạn Hôm Nay">
          {{ studyStore.remainingCounts.due }} Cần ôn
        </span>
      </div>
    </header>

    <!-- Notetype CSS (scoped to .anki-render) for cards shown with their original Anki template -->
    <component :is="'style'" v-if="studyStore.currentCard && !cleanCard && scopedCardCss">{{ scopedCardCss }}</component>

    <!-- Loading State -->
    <div v-if="studyStore.isLoading" class="my-auto text-center py-24 text-outline">
      <span class="material-symbols-outlined animate-spin text-3xl text-primary mb-2">progress_activity</span>
      <p class="text-sm font-medium">Đang nạp thẻ tiếp theo từ hàng đợi...</p>
    </div>

    <!-- Empty Queue State / Daily Limit Reached -->
    <div
      v-else-if="!studyStore.currentCard"
      class="my-auto text-center py-12 max-w-lg bg-surface-container-lowest rounded-3xl p-8 sm:p-10 border border-outline-variant/30 shadow-xl flex flex-col items-center"
    >
      <div class="w-16 h-16 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mb-4 shadow-sm">
        <span class="material-symbols-outlined text-3xl">task_alt</span>
      </div>
      <h2 class="text-2xl font-extrabold text-on-surface">Hoàn Thành Mục Tiêu Hôm Nay!</h2>
      <p class="text-xs text-on-surface-variant mt-2 mb-6 max-w-sm leading-relaxed">
        Bạn đã hoàn thành tất cả các thẻ đến hạn ôn tập trong ngày hôm nay theo thuật toán ngắt nhịp (Spaced Repetition).
      </p>

      <!-- Action buttons -->
      <div class="flex flex-col sm:flex-row items-center justify-center gap-3 w-full">
        <button
          @click="studyStore.increaseDailyQuota(10)"
          class="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-secondary text-white font-bold text-xs shadow-[0_3px_0_0_#00452e] active:translate-y-[2px] active:shadow-none hover:bg-secondary/90 transition-all flex items-center justify-center gap-1.5"
        >
          <span class="material-symbols-outlined text-base">add_circle</span>
          <span>Học Thêm (+10 Thẻ Mới)</span>
        </button>

        <router-link
          :to="studyStore.currentDeckId ? `/games?deck_id=${studyStore.currentDeckId}` : '/games'"
          class="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-primary text-on-primary font-bold text-xs shadow-[0_3px_0_0_#1a0f91] active:translate-y-[2px] active:shadow-none hover:bg-primary-container transition-all flex items-center justify-center gap-1.5"
        >
          <span class="material-symbols-outlined text-base">sports_esports</span>
          <span>Luyện Tập Quiz Game</span>
        </router-link>

        <router-link
          to="/dashboard"
          class="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-surface-container-low font-bold text-xs text-on-surface hover:bg-surface-container transition-colors"
        >
          Tổng Quan
        </router-link>
      </div>
    </div>

    <!-- Active 3D Flashcard Viewport -->
    <main v-else class="w-full flex flex-col items-center my-auto max-w-2xl relative">
      <!-- Floating Swipe Action Badges (shown when dragging card to 4 corners) -->
      <transition name="fade">
        <div
          v-if="activeSwipeDirection === 'good'"
          class="absolute top-6 right-6 z-30 px-4 py-2 rounded-2xl bg-blue-600 text-white font-extrabold text-sm shadow-xl flex items-center gap-1.5 animate-bounce"
        >
          <span>Tốt (Good)</span>
          <span class="material-symbols-outlined text-base">arrow_forward</span>
        </div>
      </transition>

      <transition name="fade">
        <div
          v-if="activeSwipeDirection === 'again'"
          class="absolute top-6 left-6 z-30 px-4 py-2 rounded-2xl bg-red-600 text-white font-extrabold text-sm shadow-xl flex items-center gap-1.5 animate-bounce"
        >
          <span class="material-symbols-outlined text-base">arrow_back</span>
          <span>Quên (Again)</span>
        </div>
      </transition>

      <transition name="fade">
        <div
          v-if="activeSwipeDirection === 'easy'"
          class="absolute top-6 left-1/2 -translate-x-1/2 z-30 px-4 py-2 rounded-2xl bg-emerald-600 text-white font-extrabold text-sm shadow-xl flex items-center gap-1.5 animate-bounce"
        >
          <span class="material-symbols-outlined text-base">arrow_upward</span>
          <span>Dễ (Easy)</span>
        </div>
      </transition>

      <transition name="fade">
        <div
          v-if="activeSwipeDirection === 'hard'"
          class="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 px-4 py-2 rounded-2xl bg-amber-600 text-white font-extrabold text-sm shadow-xl flex items-center gap-1.5 animate-bounce"
        >
          <span class="material-symbols-outlined text-base">arrow_downward</span>
          <span>Khó (Hard)</span>
        </div>
      </transition>

      <!-- 3D Perspective Card Stage (Only the Card Face Rotates!) -->
      <div
        class="w-full perspective-1000 relative select-none"
        @pointerdown="handlePointerDown"
        @pointermove="handlePointerMove"
        @pointerup="handlePointerUp"
        @pointercancel="handlePointerUp"
      >
        <!-- Flipping Card Container -->
        <div
          class="w-full min-h-[420px] rounded-3xl transition-transform cursor-grab active:cursor-grabbing relative preserve-3d"
          :class="{
            'transition-all duration-300': !isDragging,
            'pointer-events-none': isFlinging,
          }"
          :style="cardTransformStyle"
        >
          <!-- ================= FRONT FACE (Unified Memora Surface) ================= -->
          <div
            class="flashcard-face flashcard-front w-full h-full min-h-[420px] rounded-3xl p-6 sm:p-8 flex flex-col justify-between shadow-[0_8px_30px_rgb(0,0,0,0.08)] border transition-all"
            :class="isDarkTheme ? 'bg-[#121829] text-white border-slate-800' : 'bg-surface-container-lowest text-on-surface border-outline-variant/30'"
          >
            <!-- Top Controls Bar -->
            <div class="flex items-center justify-between pb-4 border-b" :class="isDarkTheme ? 'border-slate-800' : 'border-surface-container-high/40'">
              <span class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-primary-fixed text-on-primary-fixed">
                {{ cleanCard?.level_tag || studyStore.currentCard.fields['Level'] || 'Thẻ Mới' }}
              </span>

              <div class="flex items-center gap-2">
                <!-- Audio Button: ONLY IF VALID AUDIO FILE EXISTS -->
                <button
                  v-if="cleanCard?.audio_url"
                  @click.stop="playAudio"
                  class="flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-primary text-on-primary hover:bg-primary-container transition-all shadow-sm"
                  title="Nghe phát âm (R)"
                >
                  <span class="material-symbols-outlined text-base">volume_up</span>
                  <span class="hidden sm:inline">Phát âm</span>
                  <kbd class="text-[10px] opacity-80 px-1 rounded bg-black/20">R</kbd>
                </button>

                <!-- Hint / Example Toggle -->
                <button
                  v-if="hasHint"
                  @click.stop="showHint = !showHint"
                  class="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-surface-container-low text-on-surface-variant hover:bg-surface-container transition-all"
                  title="Xem gợi ý (H)"
                >
                  <span class="material-symbols-outlined text-base">lightbulb</span>
                  <span>{{ showHint ? 'Ẩn gợi ý' : 'Gợi ý' }}</span>
                  <kbd class="text-[10px] opacity-70 px-1 rounded bg-black/10">H</kbd>
                </button>

                <!-- Flip Button on Header -->
                <button
                  @click.stop="toggleFlip"
                  class="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-surface-container-low text-on-surface-variant hover:bg-surface-container transition-all"
                  title="Lật sang mặt sau (Space)"
                >
                  <span class="material-symbols-outlined text-base">sync</span>
                  <span class="hidden sm:inline">Lật thẻ</span>
                  <kbd class="text-[10px] opacity-70 px-1 rounded bg-black/10">Space</kbd>
                </button>
              </div>
            </div>

            <!-- Collapsible Hint Box -->
            <transition name="fade">
              <div
                v-if="showHint"
                class="p-3 my-2 rounded-xl text-center text-xs font-semibold bg-primary-fixed/20 text-primary border border-primary/20 animate-fade-in"
              >
                <span>{{ hintContent }}</span>
              </div>
            </transition>

            <!-- Front Body Content: Clean Unified Typography -->
            <div class="my-auto py-8 flex flex-col items-center justify-center text-center w-full">
              <!-- Structured Clean Card Presentation -->
              <template v-if="cleanCard">
                <!-- Phonetic / Furigana reading -->
                <p v-if="cleanCard.phonetic" class="text-sm sm:text-base font-semibold text-primary mb-2 tracking-wide">
                  {{ cleanCard.phonetic }}
                </p>
                <!-- Large, bold question term -->
                <h1 class="text-4xl sm:text-5xl font-black text-on-surface tracking-tight my-2">
                  {{ cleanCard.term }}
                </h1>
                <p class="text-xs text-outline mt-3">
                  Nhấp vào thẻ hoặc bấm phím Space để xem đáp án
                </p>
              </template>

              <!-- Fallback to raw template if clean_data unavailable -->
              <div v-else class="anki-render w-full" v-html="studyStore.currentCard.rendered.front_html"></div>
            </div>

            <!-- Bottom Subtext Tip -->
            <div class="pt-3 border-t text-center text-[11px] text-outline" :class="isDarkTheme ? 'border-slate-800' : 'border-surface-container-high/40'">
              Kéo thẻ sang Trái (Quên) • Phải (Tốt) • Lên (Dễ) • Xuống (Khó)
            </div>
          </div>

          <!-- ================= BACK FACE (Unified Memora Surface) ================= -->
          <div
            class="flashcard-face flashcard-back w-full h-full min-h-[420px] rounded-3xl p-6 sm:p-8 flex flex-col justify-between shadow-[0_8px_30px_rgb(0,0,0,0.08)] border transition-all"
            :class="isDarkTheme ? 'bg-[#121829] text-white border-slate-800' : 'bg-surface-container-lowest text-on-surface border-outline-variant/30'"
          >
            <!-- Back Top Controls Bar -->
            <div class="flex items-center justify-between pb-4 border-b" :class="isDarkTheme ? 'border-slate-800' : 'border-surface-container-high/40'">
              <span class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800">
                Đáp Án & Giải Nghĩa
              </span>

              <div class="flex items-center gap-2">
                <!-- Audio Button: ONLY IF VALID AUDIO FILE EXISTS -->
                <button
                  v-if="cleanCard?.audio_url"
                  @click.stop="playAudio"
                  class="flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-primary text-on-primary hover:bg-primary-container transition-all shadow-sm"
                  title="Nghe phát âm (R)"
                >
                  <span class="material-symbols-outlined text-base">volume_up</span>
                  <span class="hidden sm:inline">Phát âm</span>
                  <kbd class="text-[10px] opacity-80 px-1 rounded bg-black/20">R</kbd>
                </button>

                <!-- Flip Back to Front -->
                <button
                  @click.stop="toggleFlip"
                  class="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-surface-container-low text-on-surface-variant hover:bg-surface-container transition-all"
                  title="Lật lại mặt trước (Space)"
                >
                  <span class="material-symbols-outlined text-base">undo</span>
                  <span class="hidden sm:inline">Mặt trước</span>
                  <kbd class="text-[10px] opacity-70 px-1 rounded bg-black/10">Space</kbd>
                </button>
              </div>
            </div>

            <!-- Back Body Content -->
            <div class="my-auto py-4 flex flex-col items-center justify-center text-center w-full">
              <!-- Structured Clean Card Presentation -->
              <template v-if="cleanCard">
                <!-- Main Term and Reading Header -->
                <div class="flex items-center gap-2.5 flex-wrap justify-center mb-1">
                  <h2 class="text-2xl sm:text-3xl font-extrabold text-on-surface">
                    {{ cleanCard.term }}
                  </h2>
                  <span v-if="cleanCard.phonetic" class="text-sm font-semibold text-outline">
                    ({{ cleanCard.phonetic }})
                  </span>
                </div>

                <!-- Verified Image (ONLY if physically exists on disk) -->
                <img
                  v-if="cleanCard.image_url"
                  :src="cleanCard.image_url"
                  alt="Illustration"
                  class="max-h-40 rounded-xl my-2 mx-auto object-contain border border-outline-variant/20 shadow-sm"
                />

                <!-- Primary Meaning -->
                <div class="mt-2 mb-3 px-4 py-2 rounded-xl bg-surface-container-low border border-outline-variant/20 max-w-lg w-full">
                  <p class="text-base sm:text-lg font-bold text-primary leading-relaxed whitespace-pre-line">
                    {{ cleanCard.meaning }}
                  </p>
                </div>

                <!-- Verified Real-World Examples (Accordion / Clean Card Box) -->
                <div v-if="cleanCard.examples && cleanCard.examples.length > 0" class="w-full text-left max-w-lg">
                  <div class="flex items-center gap-1.5 text-xs font-bold text-on-surface-variant mb-2">
                    <span class="material-symbols-outlined text-base text-primary">menu_book</span>
                    <span>Ví Dụ & Ngữ Cảnh</span>
                  </div>
                  <div class="flex flex-col gap-2 max-h-48 overflow-y-auto pr-1">
                    <div
                      v-for="(ex, idx) in cleanCard.examples"
                      :key="idx"
                      class="p-2.5 rounded-xl bg-surface-container-lowest border border-outline-variant/15 text-xs text-on-surface leading-relaxed font-medium whitespace-pre-line"
                    >
                      {{ ex }}
                    </div>
                  </div>
                </div>
              </template>

              <!-- Fallback to raw template if clean_data unavailable -->
              <div v-else class="anki-render w-full" v-html="studyStore.currentCard.rendered.back_html"></div>
            </div>

            <!-- Bottom Subtext Tip -->
            <div class="pt-3 border-t text-center text-[11px] text-outline" :class="isDarkTheme ? 'border-slate-800' : 'border-surface-container-high/40'">
              Chọn mức độ nhớ bên dưới để thuật toán SRS xếp lịch lặp lại
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- ================= FIXED BOTTOM ACTION DOCK (OUTSIDE 3D STAGE) ================= -->
    <!-- Notice: This dock NEVER tilts or skews because it is outside the 3D rotating card! -->
    <footer v-if="studyStore.currentCard" class="w-full max-w-2xl mt-4 z-20">
      <!-- State 1: When card is NOT flipped -> Prominent "Xem Đáp Án / Lật Thẻ" Button -->
      <div v-if="!isFlipped" class="w-full">
        <button
          @click="toggleFlip"
          class="w-full py-4 rounded-2xl bg-primary text-on-primary font-bold text-sm sm:text-base shadow-[0_4px_0_0_#1a0f91] active:translate-y-[2px] active:shadow-none hover:bg-primary-container transition-all flex items-center justify-center gap-2"
        >
          <span class="material-symbols-outlined text-xl">flip</span>
          <span>Xem Đáp Án / Lật Thẻ</span>
          <kbd class="text-xs px-2.5 py-1 rounded font-mono bg-white/20">Space</kbd>
        </button>
      </div>

      <!-- State 2: When card IS flipped -> 4 Tactile Rating Buttons -->
      <div v-else class="flex flex-col gap-2 w-full">
        <div class="grid grid-cols-4 gap-2 sm:gap-3">
          <!-- Again (1) -->
          <button
            :disabled="isSubmitting" @click="submitRating(1)"
            class="flex flex-col items-center justify-between p-2.5 sm:p-3 rounded-2xl bg-red-50 hover:bg-red-100/90 text-red-700 border-2 border-red-500 shadow-[0_3px_0_0_#dc2626] active:translate-y-[2px] active:shadow-none transition-all"
          >
            <div class="flex items-center justify-between w-full text-xs font-bold">
              <span>Quên</span>
              <kbd class="bg-red-200/80 text-red-800 px-1 rounded text-[10px]">1</kbd>
            </div>
            <span class="text-base sm:text-lg font-extrabold my-1">{{ studyStore.currentCard.next_intervals.again }}</span>
            <span class="text-[10px] opacity-75">Học lại</span>
          </button>

          <!-- Hard (2) -->
          <button
            :disabled="isSubmitting" @click="submitRating(2)"
            class="flex flex-col items-center justify-between p-2.5 sm:p-3 rounded-2xl bg-amber-50 hover:bg-amber-100/90 text-amber-800 border-2 border-amber-500 shadow-[0_3px_0_0_#d97706] active:translate-y-[2px] active:shadow-none transition-all"
          >
            <div class="flex items-center justify-between w-full text-xs font-bold">
              <span>Khó</span>
              <kbd class="bg-amber-200/80 text-amber-900 px-1 rounded text-[10px]">2</kbd>
            </div>
            <span class="text-base sm:text-lg font-extrabold my-1">{{ studyStore.currentCard.next_intervals.hard }}</span>
            <span class="text-[10px] opacity-75">Thử thách</span>
          </button>

          <!-- Good (3) -->
          <button
            :disabled="isSubmitting" @click="submitRating(3)"
            class="flex flex-col items-center justify-between p-2.5 sm:p-3 rounded-2xl bg-blue-50 hover:bg-blue-100/90 text-blue-700 border-2 border-blue-600 shadow-[0_3px_0_0_#2563eb] active:translate-y-[2px] active:shadow-none transition-all"
          >
            <div class="flex items-center justify-between w-full text-xs font-bold">
              <span>Tốt</span>
              <kbd class="bg-blue-200/80 text-blue-900 px-1 rounded text-[10px]">3</kbd>
            </div>
            <span class="text-base sm:text-lg font-extrabold my-1">{{ studyStore.currentCard.next_intervals.good }}</span>
            <span class="text-[10px] opacity-75">Mục tiêu</span>
          </button>

          <!-- Easy (4) -->
          <button
            :disabled="isSubmitting" @click="submitRating(4)"
            class="flex flex-col items-center justify-between p-2.5 sm:p-3 rounded-2xl bg-emerald-50 hover:bg-emerald-100/90 text-emerald-800 border-2 border-emerald-500 shadow-[0_3px_0_0_#059669] active:translate-y-[2px] active:shadow-none transition-all"
          >
            <div class="flex items-center justify-between w-full text-xs font-bold">
              <span>Dễ</span>
              <kbd class="bg-emerald-200/80 text-emerald-900 px-1 rounded text-[10px]">4</kbd>
            </div>
            <span class="text-base sm:text-lg font-extrabold my-1">{{ studyStore.currentCard.next_intervals.easy }}</span>
            <span class="text-[10px] opacity-75">Nhớ sâu</span>
          </button>
        </div>

        <button
          @click="toggleFlip"
          class="text-center text-xs text-outline hover:text-on-surface py-1 transition-colors flex items-center justify-center gap-1"
        >
          <span class="material-symbols-outlined text-sm">undo</span>
          <span>Lật lại mặt trước</span>
        </button>
        <p v-if="submitError" class="text-center text-xs font-semibold text-red-600">{{ submitError }}</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useStudyStore } from '../stores/study';
import { scopeCss } from '../utils/scopeCss';

const route = useRoute();
const studyStore = useStudyStore();

// Card state
const isFlipped = ref(false);
const showHint = ref(false);
let startTime = Date.now();

// Gesture drag physics state
const isDragging = ref(false);
const dragStartX = ref(0);
const dragStartY = ref(0);
const dragDeltaX = ref(0);
const dragDeltaY = ref(0);
const isFlinging = ref(false);
const flingX = ref(0);
const flingY = ref(0);

// Clean card data shorthand
const cleanCard = computed(() => studyStore.currentCard?.clean_data || null);
const scopedCardCss = computed(() => scopeCss(studyStore.currentCard?.rendered.css || ''));

// Answer submission state (prevents double-rating the same card)
const isSubmitting = ref(false);
const submitError = ref('');

// Hint detection
const hasHint = computed(() => {
  if (cleanCard.value) {
    return cleanCard.value.examples.length > 0 || !!cleanCard.value.notes;
  }
  const fields = studyStore.currentCard?.fields || {};
  return !!(fields['Reading'] || fields['Furigana'] || fields['Hint'] || fields['Example'] || fields['Examples']);
});

const hintContent = computed(() => {
  if (cleanCard.value) {
    if (cleanCard.value.examples.length > 0) {
      return cleanCard.value.examples[0];
    }
    return cleanCard.value.notes || '';
  }
  const fields = studyStore.currentCard?.fields || {};
  return (
    fields['Example'] ||
    fields['Examples'] ||
    fields['Reading'] ||
    fields['Furigana'] ||
    fields['Hint'] ||
    ''
  );
});

// Clean theme toggle
const isDarkTheme = ref(false);

// Dynamic 3D transform with rotation tilt and fling
const cardTransformStyle = computed(() => {
  if (isFlinging.value) {
    return {
      transform: `translate3d(${flingX.value}px, ${flingY.value}px, 0) rotate(${flingX.value * 0.1}deg) ${isFlipped.value ? 'rotateY(180deg)' : ''}`,
      opacity: '0',
      transition: 'all 0.35s cubic-bezier(0.2, 0.8, 0.2, 1)',
    };
  }

  if (isDragging.value) {
    const tilt = dragDeltaX.value * 0.08;
    return {
      transform: `translate3d(${dragDeltaX.value}px, ${dragDeltaY.value}px, 0) rotate(${tilt}deg) ${isFlipped.value ? 'rotateY(180deg)' : ''}`,
    };
  }

  return {
    transform: isFlipped.value ? 'rotateY(180deg)' : 'rotateY(0deg)',
  };
});

// Active directional badge when dragging to 4 corners
const activeSwipeDirection = computed(() => {
  if (!isDragging.value) return null;
  const dx = dragDeltaX.value;
  const dy = dragDeltaY.value;
  const absX = Math.abs(dx);
  const absY = Math.abs(dy);

  if (absX < 40 && absY < 40) return null;

  if (absX > absY) {
    return dx > 0 ? 'good' : 'again';
  } else {
    return dy < 0 ? 'easy' : 'hard';
  }
});

onMounted(async () => {
  const deckId = route.query.deck_id ? Number(route.query.deck_id) : undefined;
  const filterMode = route.query.filter_mode ? String(route.query.filter_mode) : 'all';
  await studyStore.fetchNextCard(deckId, filterMode);
  startTime = Date.now();

  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown);
});

function toggleFlip() {
  isFlipped.value = !isFlipped.value;
  if (isFlipped.value) {
    studyStore.revealAnswer();
  }
}

function playAudio() {
  if (cleanCard.value?.audio_url) {
    const audio = new Audio(cleanCard.value.audio_url);
    audio.play().catch(() => {
      // Fallback to Web Speech API
      if ('speechSynthesis' in window && cleanCard.value?.term) {
        const utterance = new SpeechSynthesisUtterance(cleanCard.value.term);
        utterance.lang = 'ja-JP';
        window.speechSynthesis.speak(utterance);
      }
    });
    return;
  }

  // Fallback to Web Speech synthesis
  if ('speechSynthesis' in window && cleanCard.value?.term) {
    const utterance = new SpeechSynthesisUtterance(cleanCard.value.term);
    utterance.lang = 'ja-JP';
    window.speechSynthesis.speak(utterance);
  }
}

function resetCardPosition() {
  dragDeltaX.value = 0;
  dragDeltaY.value = 0;
  flingX.value = 0;
  flingY.value = 0;
  isFlinging.value = false;
}

async function submitRating(rating: number) {
  // Only after the answer was shown, and only once per card
  if (isSubmitting.value || !isFlipped.value || !studyStore.currentCard) {
    resetCardPosition();
    return;
  }
  isSubmitting.value = true;
  submitError.value = '';
  const timeTaken = Date.now() - startTime;
  try {
    await studyStore.answerCard(rating, timeTaken);
    isFlipped.value = false;
    showHint.value = false;
    startTime = Date.now();
  } catch (err) {
    console.error(err);
    submitError.value = 'Không gửi được đánh giá, vui lòng thử lại.';
  } finally {
    resetCardPosition();
    isSubmitting.value = false;
  }
}

// Pointer / Touch Gesture Handlers
function handlePointerDown(e: PointerEvent) {
  if ((e.target as HTMLElement).closest('button, a, kbd, input')) return;

  isDragging.value = true;
  dragStartX.value = e.clientX;
  dragStartY.value = e.clientY;
  dragDeltaX.value = 0;
  dragDeltaY.value = 0;
}

function handlePointerMove(e: PointerEvent) {
  if (!isDragging.value) return;
  dragDeltaX.value = e.clientX - dragStartX.value;
  dragDeltaY.value = e.clientY - dragStartY.value;
}

async function handlePointerUp(e: PointerEvent) {
  if (!isDragging.value) return;
  isDragging.value = false;

  const dx = dragDeltaX.value;
  const dy = dragDeltaY.value;
  const dist = Math.sqrt(dx * dx + dy * dy);

  // If minimal movement (< 10px), tap to flip
  if (dist < 10) {
    toggleFlip();
    return;
  }

  // Rating requires seeing the answer first: a swipe on the front side just flips the card
  if (dist > 90 && (!isFlipped.value || isSubmitting.value)) {
    resetCardPosition();
    if (!isFlipped.value) toggleFlip();
    return;
  }

  // If distance > 90px, trigger fling & rating
  if (dist > 90) {
    const direction = activeSwipeDirection.value;
    isFlinging.value = true;

    if (direction === 'good') {
      flingX.value = window.innerWidth * 0.8;
      flingY.value = dy * 2;
      setTimeout(() => submitRating(3), 200);
    } else if (direction === 'again') {
      flingX.value = -window.innerWidth * 0.8;
      flingY.value = dy * 2;
      setTimeout(() => submitRating(1), 200);
    } else if (direction === 'easy') {
      flingX.value = dx * 2;
      flingY.value = -window.innerHeight * 0.8;
      setTimeout(() => submitRating(4), 200);
    } else if (direction === 'hard') {
      flingX.value = dx * 2;
      flingY.value = window.innerHeight * 0.8;
      setTimeout(() => submitRating(2), 200);
    } else {
      isFlinging.value = false;
      dragDeltaX.value = 0;
      dragDeltaY.value = 0;
    }
  } else {
    // Snap back
    dragDeltaX.value = 0;
    dragDeltaY.value = 0;
  }
}

// Keyboard Shortcuts: Space=Flip, 1=Again, 2=Hard, 3=Good, 4=Easy, R=Audio, H=Hint
function handleKeydown(e: KeyboardEvent) {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

  if (e.code === 'Space') {
    e.preventDefault();
    if (!e.repeat) toggleFlip();
  } else if (e.key === 'r' || e.key === 'R') {
    e.preventDefault();
    playAudio();
  } else if (e.key === 'h' || e.key === 'H') {
    e.preventDefault();
    showHint.value = !showHint.value;
  } else if (isFlipped.value && !e.repeat) {
    if (e.key === '1') {
      e.preventDefault();
      submitRating(1);
    } else if (e.key === '2') {
      e.preventDefault();
      submitRating(2);
    } else if (e.key === '3') {
      e.preventDefault();
      submitRating(3);
    } else if (e.key === '4') {
      e.preventDefault();
      submitRating(4);
    }
  }
}
</script>

<style scoped>
.perspective-1000 {
  perspective: 1200px;
}
.preserve-3d {
  transform-style: preserve-3d;
}
/* Cards rendered from their original Anki template (cloze, type-in, custom layouts) */
.anki-render {
  text-align: center;
  font-size: 1.25rem;
  line-height: 1.6;
}
.anki-render :deep(.cloze) {
  font-weight: 800;
  color: #2563eb;
}
.anki-render :deep(.anki-typeans) {
  margin-top: 0.75rem;
  width: 100%;
  max-width: 24rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.75rem;
  border: 1px solid rgb(0 0 0 / 0.2);
  font-size: 1rem;
}
.anki-render :deep(.anki-typeans-answer code) {
  font-family: inherit;
  font-weight: 700;
  color: #059669;
}
.anki-render :deep(img) {
  max-width: 100%;
  margin: 0 auto;
}

.flashcard-face {
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}
.flashcard-front {
  transform: rotateY(0deg);
}
.flashcard-back {
  transform: rotateY(180deg);
  position: absolute;
  top: 0;
  left: 0;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

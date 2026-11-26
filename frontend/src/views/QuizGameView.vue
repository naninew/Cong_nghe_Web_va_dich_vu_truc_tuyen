<template>
  <div class="w-full max-w-4xl mx-auto px-4 py-6 flex flex-col items-center min-h-[calc(100vh-80px)] justify-between pb-24 lg:pb-8">
    <!-- View A: Game Setup / Lobby Screen (When no active session) -->
    <div v-if="!gameStore.sessionId" class="w-full max-w-2xl my-auto flex flex-col gap-6">
      <div class="text-center">
        <div class="w-16 h-16 rounded-2xl bg-primary-fixed text-on-primary-fixed flex items-center justify-center mx-auto mb-3 shadow-sm">
          <span class="material-symbols-outlined text-3xl">sports_esports</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-extrabold text-on-surface tracking-tight">Gamified Memory Challenge</h1>
        <p class="text-xs text-on-surface-variant mt-1">Configure your game mode, question direction, and challenge your memory.</p>
      </div>

      <div class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/30 shadow-sm flex flex-col gap-5">
        <!-- 1. Select Deck -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-on-surface-variant flex items-center gap-1.5">
            <span class="material-symbols-outlined text-base text-primary">folder</span>
            <span>Target Deck / Subdeck</span>
          </label>
          <select
            v-model="selectedDeckId"
            class="px-3.5 py-2.5 rounded-xl bg-surface-container-low border border-outline-variant/30 text-xs font-semibold text-on-surface outline-none"
          >
            <option :value="null">All Decks & Subdecks (59,378+ cards)</option>
            <option v-for="d in flatDecksList" :key="d.id" :value="d.id">
              {{ d.fullName }} ({{ d.total_cards }} cards)
            </option>
          </select>
        </div>

        <!-- 2. Select Game Mode -->
        <div class="flex flex-col gap-2">
          <label class="text-xs font-bold text-on-surface-variant flex items-center gap-1.5">
            <span class="material-symbols-outlined text-base text-primary">tune</span>
            <span>Select Game Mode</span>
          </label>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            <div
              v-for="m in gameModes"
              :key="m.value"
              @click="selectedMode = m.value"
              class="p-3.5 rounded-xl border-2 cursor-pointer transition-all flex flex-col gap-1"
              :class="selectedMode === m.value ? 'bg-primary-fixed/20 border-primary shadow-sm' : 'bg-surface-container-low border-transparent hover:border-outline-variant/40'"
            >
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-base" :class="selectedMode === m.value ? 'text-primary' : 'text-outline'">
                  {{ m.icon }}
                </span>
                <span class="font-bold text-xs text-on-surface">{{ m.label }}</span>
              </div>
              <span class="text-[11px] text-on-surface-variant leading-snug">{{ m.desc }}</span>
            </div>
          </div>
        </div>

        <!-- 3. Question Direction -->
        <div class="flex flex-col gap-2">
          <label class="text-xs font-bold text-on-surface-variant flex items-center gap-1.5">
            <span class="material-symbols-outlined text-base text-primary">swap_horiz</span>
            <span>Chiều Hỏi & Đáp (Question Direction)</span>
          </label>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div
              v-for="d in directions"
              :key="d.value"
              @click="selectedDirection = d.value"
              class="p-3 rounded-xl border-2 cursor-pointer transition-all text-center flex flex-col items-center gap-1"
              :class="selectedDirection === d.value ? 'bg-primary-fixed/20 border-primary shadow-sm' : 'bg-surface-container-low border-transparent hover:border-outline-variant/40'"
            >
              <span class="material-symbols-outlined text-lg" :class="selectedDirection === d.value ? 'text-primary' : 'text-outline'">
                {{ d.icon }}
              </span>
              <span class="font-bold text-xs text-on-surface">{{ d.label }}</span>
              <span class="text-[10px] text-outline">{{ d.hint }}</span>
            </div>
          </div>
        </div>

        <!-- Custom Field Mapping (when direction is custom) -->
        <div v-if="selectedDirection === 'custom'" class="flex flex-col gap-2.5 p-3.5 bg-surface-container-low rounded-xl border border-outline-variant/20 text-xs">
          <div v-if="isLoadingFields" class="text-[11px] text-outline font-medium">
            Đang tải danh sách trường của bộ thẻ...
          </div>
          <div v-else class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div class="flex flex-col gap-1">
              <label class="font-bold text-on-surface">Trường Câu Hỏi (Prompt) *</label>
              <select
                v-model="customQuestionField"
                class="px-2.5 py-2 rounded-lg bg-surface-container-lowest border border-outline-variant/30 text-xs text-on-surface outline-none"
              >
                <option value="" disabled>-- Chọn trường câu hỏi --</option>
                <option
                  v-for="f in availableFields"
                  :key="'q-' + f"
                  :value="f"
                  :disabled="f === customAnswerField || (customHintField !== '' && f === customHintField)"
                >
                  {{ f }}
                </option>
              </select>
            </div>
            <div class="flex flex-col gap-1">
              <label class="font-bold text-on-surface">Trường Đáp Án (Answer) *</label>
              <select
                v-model="customAnswerField"
                class="px-2.5 py-2 rounded-lg bg-surface-container-lowest border border-outline-variant/30 text-xs text-on-surface outline-none"
              >
                <option value="" disabled>-- Chọn trường đáp án --</option>
                <option
                  v-for="f in availableFields"
                  :key="'a-' + f"
                  :value="f"
                  :disabled="f === customQuestionField || (customHintField !== '' && f === customHintField)"
                >
                  {{ f }}
                </option>
              </select>
            </div>
            <div class="flex flex-col gap-1">
              <label class="font-bold text-on-surface">Trường Gợi Ý (Hint - tùy chọn)</label>
              <select
                v-model="customHintField"
                class="px-2.5 py-2 rounded-lg bg-surface-container-lowest border border-outline-variant/30 text-xs text-on-surface outline-none"
              >
                <option value="">-- Không dùng gợi ý --</option>
                <option
                  v-for="f in availableFields"
                  :key="'h-' + f"
                  :value="f"
                  :disabled="f === customQuestionField || f === customAnswerField"
                >
                  {{ f }}
                </option>
              </select>
            </div>
          </div>
          <p v-if="customFieldError" class="text-[11px] font-semibold text-error flex items-center gap-1">
            <span class="material-symbols-outlined text-sm">error</span>
            <span>{{ customFieldError }}</span>
          </p>
        </div>

        <!-- 4. Question Count & SRS Sync Toggle -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-surface-container-high/40">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-bold text-on-surface-variant">Question Count</label>
            <div class="flex items-center gap-2">
              <button
                v-for="cnt in [5, 10, 20, 50]"
                :key="cnt"
                @click="questionCount = cnt"
                type="button"
                class="flex-1 py-1.5 rounded-lg text-xs font-bold transition-all"
                :class="questionCount === cnt ? 'bg-primary text-on-primary shadow-sm' : 'bg-surface-container-low text-on-surface hover:bg-surface-container'"
              >
                {{ cnt }}
              </button>
            </div>
          </div>

          <div class="flex flex-col gap-1 justify-center">
            <label class="text-xs font-bold text-on-surface-variant">Anki SRS Sync</label>
            <label class="flex items-center gap-2 cursor-pointer text-xs text-on-surface font-semibold">
              <input type="checkbox" v-model="srsSync" class="w-4 h-4 rounded text-primary accent-primary shrink-0" />
              <span>Tự động cập nhật lịch ôn tập (Auto-update memory intervals)</span>
            </label>
            <p class="text-[11px] text-on-surface-variant leading-snug pl-6">
              Bật: trả lời đúng sẽ giãn lịch ôn (Good), sai sẽ đặt lịch ôn lại sớm (Again). Tắt nếu chỉ muốn luyện tập không ảnh hưởng tiến độ thẻ.
            </p>
          </div>
        </div>

        <!-- Error Banner -->
        <div
          v-if="startError"
          class="px-3.5 py-2.5 rounded-xl bg-red-50 border border-error/30 text-error text-xs font-semibold flex items-center gap-2"
        >
          <span class="material-symbols-outlined text-base shrink-0">error</span>
          <span>{{ startError }}</span>
        </div>

        <!-- Launch Button -->
        <button
          @click="launchGame"
          :disabled="gameStore.isLoading || (selectedDirection === 'custom' && !!customFieldError)"
          class="w-full py-3.5 rounded-xl bg-primary text-on-primary font-bold text-sm shadow-[0_3px_0_0_#1a0f91] active:translate-y-[2px] active:shadow-none hover:bg-primary-container disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 mt-2"
        >
          <span class="material-symbols-outlined text-lg">play_arrow</span>
          <span>{{ gameStore.isLoading ? 'Đang khởi tạo...' : 'Start Challenge' }}</span>
        </button>
      </div>
    </div>

    <!-- View B: Active Gameplay View -->
    <div v-else class="w-full max-w-2xl my-auto flex flex-col items-center gap-6">
      <!-- Header: Exit, Combo Streak, Lives / Timer, Score -->
      <header class="w-full flex items-center justify-between gap-4">
        <div class="flex items-center gap-2">
          <button @click="exitGame" class="p-1.5 rounded-lg hover:bg-surface-container text-outline hover:text-on-surface transition-colors" title="Exit to Lobby">
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
          <span class="font-bold text-xs sm:text-sm text-on-surface">Quiz Challenge</span>
        </div>

        <div class="flex items-center gap-2.5">
          <!-- Survival Hearts -->
          <div v-if="gameStore.activeMode === 'survival'" class="flex items-center gap-1 px-2.5 py-1 rounded-full bg-red-50 text-red-600 font-bold text-xs">
            <span v-for="i in 3" :key="i" class="material-symbols-outlined text-base">
              {{ i <= survivalLives ? 'favorite' : 'heart_broken' }}
            </span>
          </div>

          <!-- Combo Streak Badge -->
          <div v-if="gameStore.combo > 1" class="flex items-center gap-1 px-3 py-1 rounded-full bg-tertiary-fixed text-on-tertiary-fixed text-xs font-bold animate-bounce">
            <span class="material-symbols-outlined text-sm leading-none">bolt</span>
            <span>{{ gameStore.combo }}x</span>
          </div>

          <!-- Score Badge -->
          <div class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-fixed text-on-secondary-fixed text-xs font-bold shadow-sm">
            <span class="material-symbols-outlined text-sm leading-none">stars</span>
            <span>{{ gameStore.score }} pts</span>
          </div>
        </div>
      </header>

      <!-- Question Progress Bar -->
      <div class="w-full h-1.5 rounded-full bg-surface-container-high overflow-hidden">
        <div
          class="h-full bg-primary rounded-full transition-all duration-300"
          :style="{ width: `${((gameStore.currentIndex + 1) / (gameStore.questions.length || 1)) * 100}%` }"
        ></div>
      </div>

      <!-- Speed Blitz Timer Bar -->
      <div v-if="gameStore.activeMode === 'speed_blitz' && !gameStore.isAnswered" class="w-full flex flex-col gap-1">
        <div class="flex items-center justify-between text-[11px] font-mono font-bold text-outline">
          <span>Speed Timer</span>
          <span :class="timerSecondsRemaining <= 3 ? 'text-error font-extrabold animate-pulse' : 'text-primary'">
            {{ timerSecondsRemaining }}s
          </span>
        </div>
        <div class="w-full h-2 rounded-full bg-surface-container-high overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-1000 ease-linear"
            :class="timerSecondsRemaining <= 3 ? 'bg-error' : (timerSecondsRemaining <= 6 ? 'bg-amber-500' : 'bg-primary')"
            :style="{ width: `${(timerSecondsRemaining / 10) * 100}%` }"
          ></div>
        </div>
      </div>

      <!-- Active Question Card Viewport -->
      <main v-if="gameStore.currentQuestion" class="w-full flex flex-col items-center gap-6">
        <!-- Question Card Banner -->
        <div class="w-full bg-surface-container-lowest rounded-2xl p-6 sm:p-8 border border-outline-variant/30 shadow-sm text-center flex flex-col items-center gap-3 relative">
          <span class="text-xs font-bold uppercase tracking-wider text-outline">
            Question {{ gameStore.currentIndex + 1 }} of {{ gameStore.questions.length }}
          </span>

          <!-- Audio Button if Listening mode or has audio -->
          <button
            v-if="gameStore.currentQuestion.audio_file"
            @click="playQuestionAudio"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary-fixed text-on-primary-fixed text-xs font-bold hover:bg-primary-fixed-dim transition-all shadow-sm"
          >
            <span class="material-symbols-outlined text-base">volume_up</span>
            <span>Listen Pronunciation</span>
          </button>

          <!-- Prompt Expression / Meaning -->
          <h2 class="text-3xl sm:text-4xl font-extrabold text-on-surface tracking-tight">
            {{ gameStore.currentQuestion.prompt }}
          </h2>

          <!-- Collapsible Hint / Example Button -->
          <div v-if="gameStore.currentQuestion.context_hint" class="flex flex-col items-center gap-1.5 w-full">
            <button
              @click="showGameHint = !showGameHint"
              class="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-surface-container-low hover:bg-surface-container text-xs font-semibold text-primary transition-colors"
            >
              <span class="material-symbols-outlined text-sm">lightbulb</span>
              <span>{{ showGameHint ? 'Ẩn gợi ý' : 'Xem gợi ý / Ví dụ' }}</span>
            </button>
            <p v-if="showGameHint" class="text-xs text-primary font-semibold bg-primary-fixed/20 px-3 py-1.5 rounded-xl animate-fade-in max-w-md">
              {{ gameStore.currentQuestion.context_hint }}
            </p>
          </div>
        </div>

        <!-- 4-Option Quiz Tiles -->
        <section class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 w-full">
          <div
            v-for="opt in gameStore.currentQuestion.options"
            :key="opt.key"
            @click="chooseOption(opt.key)"
            class="relative rounded-2xl p-4 sm:p-5 flex flex-col justify-between transition-all cursor-pointer border-2"
            :class="getOptionClass(opt.key)"
          >
            <div class="flex items-start gap-3">
              <span
                class="w-8 h-8 rounded-xl flex items-center justify-center font-bold text-sm shrink-0"
                :class="getKeyBadgeClass(opt.key)"
              >
                {{ opt.key }}
              </span>
              <span class="font-bold text-sm sm:text-base text-on-surface leading-snug">
                {{ opt.label }}
              </span>
            </div>

            <div class="mt-3 pt-2 border-t border-surface-container-high/40 flex items-center justify-between text-outline text-[11px] font-mono">
              <span>Press {{ opt.key }}</span>
              <kbd class="px-1.5 py-0.5 rounded bg-surface-container text-on-surface text-[10px] font-bold">{{ opt.key }}</kbd>
            </div>
          </div>
        </section>

        <!-- Feedback Banner (when answered) -->
        <div
          v-if="gameStore.isAnswered && gameStore.lastAnswerResult"
          class="w-full bg-surface-container-lowest rounded-2xl p-5 border shadow-sm flex flex-col gap-3"
          :class="gameStore.lastAnswerResult.is_correct ? 'border-secondary/40' : 'border-error/40'"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span
                class="w-8 h-8 rounded-full flex items-center justify-center text-white"
                :class="gameStore.lastAnswerResult.is_correct ? 'bg-secondary' : 'bg-error'"
              >
                <span class="material-symbols-outlined text-lg">
                  {{ gameStore.lastAnswerResult.is_correct ? 'check' : 'close' }}
                </span>
              </span>
              <div class="flex flex-col">
                <span
                  class="font-extrabold text-sm"
                  :class="gameStore.lastAnswerResult.is_correct ? 'text-secondary' : 'text-error'"
                >
                  {{ gameStore.lastAnswerResult.is_correct ? 'Spot On! +' + gameStore.lastAnswerResult.points_earned + ' Points' : 'Missed!' }}
                </span>
                <span class="text-xs text-on-surface-variant">
                  {{ gameStore.lastAnswerResult.explanation }}
                </span>
              </div>
            </div>

            <button
              @click="handleNext"
              class="px-5 py-2.5 rounded-xl bg-primary text-on-primary font-bold text-xs shadow-[0_3px_0_0_#1a0f91] active:translate-y-[2px] active:shadow-none hover:bg-primary-container transition-all"
            >
              {{ (gameStore.isLastQuestion || (gameStore.activeMode === 'survival' && survivalLives <= 0)) ? 'View Results' : 'Next Question' }}
            </button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useGameStore } from '../stores/game';
import { useDeckStore } from '../stores/deck';
import type { DeckTree } from '../types';

const route = useRoute();
const router = useRouter();
const gameStore = useGameStore();
const deckStore = useDeckStore();

const selectedDeckId = ref<number | null>(null);
const selectedMode = ref<string>('classic');
const selectedDirection = ref<string>('front_to_back');
const questionCount = ref<number>(10);
const srsSync = ref<boolean>(true);

const availableFields = ref<string[]>([]);
const isLoadingFields = ref<boolean>(false);
const customQuestionField = ref<string>('');
const customAnswerField = ref<string>('');
const customHintField = ref<string>('');
const showGameHint = ref<boolean>(false);
const startError = ref<string | null>(null);

const survivalLives = ref<number>(3);
const timerSecondsRemaining = ref<number>(10);
let timerInterval: any = null;
let questionStartTime = Date.now();
const selectedChoice = ref<string | null>(null);

const gameModes = [
  { value: 'classic', label: 'Classic Quiz', icon: 'bolt', desc: 'Standard 4-option questions with combo streaks.' },
  { value: 'speed_blitz', label: 'Speed Blitz', icon: 'timer', desc: '10s per question with high speed score bonuses.' },
  { value: 'survival', label: 'Survival Mode', icon: 'favorite', desc: '3 hearts. 3 wrong answers and you are out!' },
  { value: 'lapsed_only', label: 'Weak Spot Buster', icon: 'replay', desc: 'Only tests cards you previously got wrong.' },
];

const directions = [
  { value: 'front_to_back', label: 'Mặt trước ➔ Mặt sau', icon: 'arrow_forward', hint: 'Từ vựng ➔ Định nghĩa' },
  { value: 'back_to_front', label: 'Mặt sau ➔ Mặt trước', icon: 'arrow_back', hint: 'Định nghĩa ➔ Từ vựng' },
  { value: 'custom', label: 'Tùy chọn trường', icon: 'tune', hint: 'Tự chọn trường' },
];

const customFieldError = computed(() => {
  if (selectedDirection.value !== 'custom') return null;
  if (isLoadingFields.value) return null;
  if (availableFields.value.length < 2) {
    return 'Bộ thẻ này không đủ trường để tùy chọn (cần ít nhất 2 trường khác nhau).';
  }
  if (!customQuestionField.value || !customAnswerField.value) {
    return 'Vui lòng chọn đầy đủ Trường Câu Hỏi và Trường Đáp Án.';
  }
  const chosen = [customQuestionField.value, customAnswerField.value, customHintField.value].filter(Boolean);
  if (new Set(chosen).size !== chosen.length) {
    return 'Các trường Câu Hỏi, Đáp Án và Gợi Ý không được trùng nhau.';
  }
  return null;
});

async function loadDeckFields(deckId: number | null) {
  isLoadingFields.value = true;
  try {
    const fields = await gameStore.fetchDeckFields(deckId);
    availableFields.value = fields;

    if (!fields.includes(customQuestionField.value)) {
      customQuestionField.value = fields[0] || '';
    }
    if (!fields.includes(customAnswerField.value) || customAnswerField.value === customQuestionField.value) {
      customAnswerField.value = fields.find((f) => f !== customQuestionField.value) || '';
    }
    if (
      customHintField.value &&
      (!fields.includes(customHintField.value) ||
        customHintField.value === customQuestionField.value ||
        customHintField.value === customAnswerField.value)
    ) {
      customHintField.value = '';
    }
  } catch {
    availableFields.value = [];
  } finally {
    isLoadingFields.value = false;
  }
}

watch(selectedDeckId, (newDeckId) => {
  startError.value = null;
  loadDeckFields(newDeckId);
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
  if (route.query.mode) {
    selectedMode.value = String(route.query.mode);
  }
  await loadDeckFields(selectedDeckId.value);
  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval);
  window.removeEventListener('keydown', handleKeydown);
});

async function launchGame() {
  startError.value = null;
  if (selectedDirection.value === 'custom' && customFieldError.value) {
    startError.value = customFieldError.value;
    return;
  }
  survivalLives.value = 3;
  showGameHint.value = false;
  try {
    await gameStore.startGame(
      selectedDeckId.value,
      questionCount.value,
      srsSync.value,
      selectedMode.value,
      selectedDirection.value,
      selectedDirection.value === 'custom' ? customQuestionField.value || null : null,
      selectedDirection.value === 'custom' ? customAnswerField.value || null : null,
      selectedDirection.value === 'custom' ? customHintField.value || null : null
    );
    startQuestionTimer();
  } catch (err: any) {
    startError.value =
      err?.response?.data?.detail ||
      err?.message ||
      'Không thể bắt đầu ván chơi. Vui lòng kiểm tra lại bộ thẻ và thử lại.';
  }
}

function startQuestionTimer() {
  if (timerInterval) clearInterval(timerInterval);
  questionStartTime = Date.now();
  timerSecondsRemaining.value = 10;

  if (gameStore.activeMode === 'speed_blitz') {
    timerInterval = setInterval(() => {
      if (timerSecondsRemaining.value > 1) {
        timerSecondsRemaining.value -= 1;
      } else {
        clearInterval(timerInterval);
        // Time out: automatic wrong choice
        if (!gameStore.isAnswered) {
          chooseOption('X');
        }
      }
    }, 1000);
  }
}

function playQuestionAudio() {
  const file = gameStore.currentQuestion?.audio_file;
  if (file) {
    if ((window as any).playAnkiAudio) {
      (window as any).playAnkiAudio(file);
    } else {
      new Audio(`/media/${file}`).play().catch((e) => console.warn(e));
    }
  }
}

function getOptionClass(key: string) {
  if (!gameStore.isAnswered) {
    return 'bg-surface-container-lowest border-outline-variant/30 hover:border-primary/50 shadow-[0_3px_0_0_#dae2fd] active:translate-y-[2px] active:shadow-none';
  }

  const res = gameStore.lastAnswerResult;
  if (!res) return '';

  if (key === res.correct_key) {
    return 'bg-emerald-50 border-secondary shadow-[0_0_0_2px_#006c49]';
  } else if (key === selectedChoice.value && !res.is_correct) {
    return 'bg-red-50 border-error shadow-[0_0_0_2px_#ba1a1a]';
  } else {
    return 'bg-surface-container-low opacity-60 border-transparent cursor-not-allowed';
  }
}

function getKeyBadgeClass(key: string) {
  if (!gameStore.isAnswered) {
    return 'bg-surface-container-high text-on-surface';
  }
  const res = gameStore.lastAnswerResult;
  if (key === res?.correct_key) {
    return 'bg-secondary text-white';
  } else if (key === selectedChoice.value && !res?.is_correct) {
    return 'bg-error text-white';
  }
  return 'bg-surface-container-highest text-outline';
}

async function chooseOption(key: string) {
  if (gameStore.isAnswered) return;
  if (timerInterval) clearInterval(timerInterval);
  selectedChoice.value = key;
  const timeTaken = Date.now() - questionStartTime;
  const res = await gameStore.submitAnswer(key, timeTaken);

  if (res && !res.is_correct && gameStore.activeMode === 'survival') {
    survivalLives.value -= 1;
  }
}

async function handleNext() {
  selectedChoice.value = null;
  showGameHint.value = false;
  const isSurvivalDead = gameStore.activeMode === 'survival' && survivalLives.value <= 0;

  if (gameStore.isLastQuestion || isSurvivalDead) {
    const finished = await gameStore.finishGame();
    router.push({
      path: '/games/result',
      query: finished?.session_id ? { session_id: finished.session_id } : undefined,
    });
  } else {
    await gameStore.nextQuestion();
    startQuestionTimer();
  }
}

function exitGame() {
  if (confirm('Exit current game and return to configuration lobby?')) {
    if (timerInterval) clearInterval(timerInterval);
    gameStore.resetGame();
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

  if (!gameStore.sessionId) return;

  const keyUpper = e.key.toUpperCase();
  if (['1', '2', '3', '4', 'A', 'B', 'C', 'D'].includes(keyUpper)) {
    const keyMap: Record<string, string> = { '1': 'A', '2': 'B', '3': 'C', '4': 'D' };
    const optionKey = keyMap[keyUpper] || keyUpper;
    if (!gameStore.isAnswered) {
      chooseOption(optionKey);
    }
  } else if (e.code === 'Space' || e.code === 'Enter') {
    if (gameStore.isAnswered) {
      handleNext();
    }
  }
}
</script>

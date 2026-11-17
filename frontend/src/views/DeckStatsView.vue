<template>
  <div class="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6 pb-24 lg:pb-8">
    <!-- Top Breadcrumb & Actions -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <router-link to="/library" class="p-2 rounded-xl bg-surface-container-low hover:bg-surface-container text-on-surface-variant transition-colors">
          <span class="material-symbols-outlined text-lg leading-none">arrow_back</span>
        </router-link>
        <div>
          <h1 class="text-2xl font-extrabold text-on-surface tracking-tight flex items-center gap-2">
            <span>{{ statsData?.deck?.name || 'Thống Kê Bộ Thẻ' }}</span>
          </h1>
          <p class="text-xs text-on-surface-variant mt-0.5">
            {{ statsData?.deck?.description || 'Phân tích hiệu suất học tập, độ nhớ và phân bố trạng thái' }}
          </p>
        </div>
      </div>

      <!-- 3 Primary Navigation Tabs (Hizashi Reference) -->
      <div class="flex items-center gap-2 p-1 bg-surface-container-low rounded-2xl border border-outline-variant/20 self-start sm:self-auto">
        <router-link
          :to="`/study?deck_id=${deckId}`"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-on-surface-variant hover:text-on-surface transition-colors"
        >
          <span class="material-symbols-outlined text-base">style</span>
          <span>Bộ thẻ</span>
        </router-link>

        <router-link
          :to="`/browse?deck_id=${deckId}`"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-on-surface-variant hover:text-on-surface transition-colors"
        >
          <span class="material-symbols-outlined text-base">format_list_bulleted</span>
          <span>Danh sách</span>
        </router-link>

        <div class="flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-bold bg-primary text-on-primary shadow-sm">
          <span class="material-symbols-outlined text-base">pie_chart</span>
          <span>Thống kê</span>
        </div>
      </div>
    </div>

    <!-- Quick Action Pills -->
    <div class="flex items-center gap-2">
      <button
        @click="showGuideModal = true"
        class="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-surface-container-lowest border border-outline-variant/30 text-xs font-semibold text-on-surface hover:bg-surface-container transition-colors shadow-sm"
      >
        <span class="material-symbols-outlined text-base text-primary">help</span>
        <span>Hướng dẫn</span>
      </button>

      <button
        @click="fetchStats"
        class="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-surface-container-lowest border border-outline-variant/30 text-xs font-semibold text-on-surface hover:bg-surface-container transition-colors shadow-sm"
      >
        <span class="material-symbols-outlined text-base text-outline" :class="{ 'animate-spin': isLoading }">sync</span>
        <span>Làm mới</span>
      </button>

      <router-link
        :to="`/games?deck_id=${deckId}`"
        class="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-surface-container-lowest border border-outline-variant/30 text-xs font-semibold text-on-surface hover:bg-surface-container transition-colors shadow-sm ml-auto"
      >
        <span class="material-symbols-outlined text-base text-secondary">sports_esports</span>
        <span>Chơi Quiz Game</span>
      </router-link>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="p-20 text-center text-outline">
      <span class="material-symbols-outlined animate-spin text-3xl text-primary mb-2">progress_activity</span>
      <p class="text-xs font-semibold">Đang tổng hợp dữ liệu thống kê bộ thẻ...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMessage" class="p-12 text-center bg-surface-container-lowest rounded-2xl border border-red-200">
      <span class="material-symbols-outlined text-3xl text-red-500 mb-2">error</span>
      <p class="text-sm font-bold text-red-600">{{ errorMessage }}</p>
    </div>

    <div v-else-if="statsData" class="flex flex-col gap-6">
      <!-- ================= 1. TỔNG QUAN (4 KPI Cards) ================= -->
      <section class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col gap-4">
        <div class="flex items-center justify-between pb-3 border-b border-surface-container-high/40">
          <div class="flex items-center gap-2 text-on-surface font-extrabold text-base">
            <span class="material-symbols-outlined text-primary">analytics</span>
            <span>Tổng quan</span>
          </div>
          <span class="text-xs text-outline font-semibold">{{ statsData.deck.name }}</span>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <!-- KPI 1: Tổng thẻ -->
          <div class="flex items-center gap-4 p-4 rounded-2xl bg-surface-container-low/40 border border-outline-variant/20">
            <div class="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-2xl">layers</span>
            </div>
            <div>
              <div class="text-2xl font-black text-on-surface">{{ statsData.overview.total_cards.toLocaleString() }}</div>
              <div class="text-xs font-bold text-outline">Tổng thẻ</div>
              <div class="text-[11px] text-on-surface-variant mt-0.5">Bao gồm toàn bộ subdeck con</div>
            </div>
          </div>

          <!-- KPI 2: Tiến độ bộ thẻ -->
          <div class="flex items-center gap-4 p-4 rounded-2xl bg-surface-container-low/40 border border-outline-variant/20">
            <div class="w-12 h-12 rounded-2xl bg-orange-100 text-orange-800 flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-2xl">trending_up</span>
            </div>
            <div>
              <div class="text-2xl font-black text-on-surface">{{ statsData.overview.progress_percent }}%</div>
              <div class="text-xs font-bold text-outline">Tiến độ bộ thẻ</div>
              <div class="text-[11px] text-on-surface-variant mt-0.5">
                {{ statsData.overview.studied_cards }} / {{ statsData.overview.total_cards }} thẻ đã ôn
              </div>
            </div>
          </div>

          <!-- KPI 3: Tỷ lệ thành công -->
          <div class="flex items-center gap-4 p-4 rounded-2xl bg-surface-container-low/40 border border-outline-variant/20">
            <div class="w-12 h-12 rounded-2xl bg-blue-100 text-blue-800 flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-2xl">track_changes</span>
            </div>
            <div>
              <div class="text-2xl font-black text-on-surface">{{ statsData.overview.retention_rate }}%</div>
              <div class="text-xs font-bold text-outline">Tỷ lệ thành công</div>
              <div class="text-[11px] text-on-surface-variant mt-0.5">
                {{ statsData.overview.success_reviews }} đúng / {{ statsData.overview.fail_reviews }} sai
              </div>
            </div>
          </div>

          <!-- KPI 4: Lượt ôn tập -->
          <div class="flex items-center gap-4 p-4 rounded-2xl bg-surface-container-low/40 border border-outline-variant/20">
            <div class="w-12 h-12 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-2xl">auto_awesome</span>
            </div>
            <div>
              <div class="text-2xl font-black text-on-surface">{{ statsData.overview.total_reviews.toLocaleString() }}</div>
              <div class="text-xs font-bold text-outline">Lượt ôn tập</div>
              <div class="text-[11px] text-on-surface-variant mt-0.5">
                TB {{ statsData.overview.avg_reviews_per_card }} lượt / thẻ
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ================= 2. PHÂN BỐ TRẠNG THÁI (SVG Donut Chart) ================= -->
      <section class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col gap-4">
        <div class="flex items-center gap-2 text-on-surface font-extrabold text-base pb-3 border-b border-surface-container-high/40">
          <span class="material-symbols-outlined text-amber-600">donut_large</span>
          <span>Phân bố trạng thái</span>
        </div>

        <div class="flex flex-col md:flex-row items-center justify-around gap-8 py-4">
          <!-- Donut SVG Graphic -->
          <div class="relative w-56 h-56 flex items-center justify-center">
            <svg viewBox="0 0 100 100" class="w-full h-full -rotate-90 transform">
              <!-- Background Ring -->
              <circle cx="50" cy="50" r="38" fill="transparent" stroke="#f1f5f9" stroke-width="12" />
              <!-- Slices -->
              <circle
                v-for="slice in donutSlices"
                :key="slice.label"
                cx="50"
                cy="50"
                r="38"
                fill="transparent"
                :stroke="slice.color"
                stroke-width="12"
                :stroke-dasharray="`${slice.dashLength} ${100 - slice.dashLength}`"
                :stroke-dashoffset="slice.offset"
                stroke-linecap="round"
                class="transition-all duration-700"
              />
            </svg>

            <!-- Center Count -->
            <div class="absolute inset-0 flex flex-col items-center justify-center text-center">
              <span class="text-3xl font-black text-on-surface tracking-tight">
                {{ statsData.overview.total_cards }}
              </span>
              <span class="text-xs font-extrabold text-outline uppercase tracking-wider">THẺ</span>
            </div>
          </div>

          <!-- Status Legend List (Exact Hizashi breakdown) -->
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-2 gap-x-8 gap-y-3 w-full max-w-md text-xs">
            <!-- Mới -->
            <div class="flex items-center justify-between p-2 rounded-xl bg-surface-container-low/30">
              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-slate-400"></span>
                <span class="font-bold text-on-surface-variant">Mới</span>
              </div>
              <span class="font-black text-on-surface">{{ statsData.distribution.new }}</span>
            </div>

            <!-- Đang học -->
            <div class="flex items-center justify-between p-2 rounded-xl bg-surface-container-low/30">
              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-amber-500"></span>
                <span class="font-bold text-on-surface-variant">Đang học</span>
              </div>
              <span class="font-black text-on-surface">{{ statsData.distribution.learning }}</span>
            </div>

            <!-- Ôn tập -->
            <div class="flex items-center justify-between p-2 rounded-xl bg-surface-container-low/30">
              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
                <span class="font-bold text-on-surface-variant">Ôn tập</span>
              </div>
              <span class="font-black text-on-surface">{{ statsData.distribution.review }}</span>
            </div>

            <!-- Học lại -->
            <div class="flex items-center justify-between p-2 rounded-xl bg-surface-container-low/30">
              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-rose-500"></span>
                <span class="font-bold text-on-surface-variant">Học lại</span>
              </div>
              <span class="font-black text-on-surface">{{ statsData.distribution.relearning }}</span>
            </div>

            <!-- Đánh dấu khó -->
            <div class="flex items-center justify-between p-2 rounded-xl bg-surface-container-low/30">
              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-purple-500"></span>
                <span class="font-bold text-on-surface-variant">Đánh dấu khó</span>
              </div>
              <span class="font-black text-on-surface">{{ statsData.distribution.leeches }}</span>
            </div>

            <!-- Yêu thích -->
            <div class="flex items-center justify-between p-2 rounded-xl bg-surface-container-low/30">
              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-orange-500"></span>
                <span class="font-bold text-on-surface-variant">Yêu thích</span>
              </div>
              <span class="font-black text-on-surface">{{ statsData.distribution.starred }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ================= 3. TỪ ĐÃ HỌC (Learned Cards Matrix Grid) ================= -->
      <section class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col gap-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-surface-container-high/40">
          <div class="flex items-center gap-2 text-on-surface font-extrabold text-base">
            <span class="material-symbols-outlined text-secondary">grid_view</span>
            <span>Từ đã học</span>
            <span class="text-xs font-bold text-outline">
              ({{ statsData.learned.total_learned }} / {{ statsData.learned.total_cards }} thẻ)
            </span>
          </div>

          <div class="text-[11px] text-outline font-semibold">
            Màu đậm = Nhớ lâu · Bấm vào thẻ để xem chi tiết
          </div>
        </div>

        <!-- Tier Legend Badges -->
        <div class="flex flex-wrap items-center gap-3 text-xs py-1">
          <div class="flex items-center gap-1.5 font-bold">
            <span class="w-6 h-1.5 rounded-full bg-amber-200"></span>
            <span class="text-on-surface-variant">Mới nhớ:</span>
            <span class="text-on-surface">{{ statsData.learned.tier_counts.tier1 }}</span>
          </div>

          <div class="flex items-center gap-1.5 font-bold">
            <span class="w-6 h-1.5 rounded-full bg-amber-400"></span>
            <span class="text-on-surface-variant">Đang nhớ:</span>
            <span class="text-on-surface">{{ statsData.learned.tier_counts.tier2 }}</span>
          </div>

          <div class="flex items-center gap-1.5 font-bold">
            <span class="w-6 h-1.5 rounded-full bg-emerald-400"></span>
            <span class="text-on-surface-variant">Khá vững:</span>
            <span class="text-on-surface">{{ statsData.learned.tier_counts.tier3 }}</span>
          </div>

          <div class="flex items-center gap-1.5 font-bold">
            <span class="w-6 h-1.5 rounded-full bg-emerald-600"></span>
            <span class="text-on-surface-variant">Vững:</span>
            <span class="text-on-surface">{{ statsData.learned.tier_counts.tier4 }}</span>
          </div>

          <div class="flex items-center gap-1.5 font-bold">
            <span class="w-6 h-1.5 rounded-full bg-blue-600"></span>
            <span class="text-on-surface-variant">Nhớ lâu:</span>
            <span class="text-on-surface">{{ statsData.learned.tier_counts.tier5 }}</span>
          </div>
        </div>

        <!-- Cards Tile Grid -->
        <div v-if="statsData.learned.cards.length === 0" class="p-12 text-center text-outline">
          <span class="material-symbols-outlined text-3xl mb-1">sentiment_neutral</span>
          <p class="text-xs font-semibold">Chưa có thẻ nào được học trong bộ thẻ này. Bắt đầu phiên học ngay!</p>
        </div>

        <div v-else class="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-8 lg:grid-cols-10 gap-2.5 pt-2">
          <div
            v-for="item in statsData.learned.cards"
            :key="item.card_id"
            @click="openCardModal(item.card_id)"
            class="h-16 rounded-xl bg-surface-container-low/40 border border-outline-variant/20 hover:border-primary/50 hover:bg-surface-container transition-all cursor-pointer flex flex-col justify-between p-2 text-center group shadow-sm active:scale-95"
            :title="`Nhấp để xem chi tiết: ${item.front_text} (Khoảng cách: ${item.ivl}d)`"
          >
            <!-- Card Front Text -->
            <div class="my-auto font-bold text-xs sm:text-sm text-on-surface truncate group-hover:text-primary transition-colors">
              {{ item.front_text }}
            </div>

            <!-- Bottom Tier Color Underline -->
            <div
              class="w-full h-1 rounded-full transition-all"
              :class="tierColorClass(item.tier)"
            ></div>
          </div>
        </div>
      </section>
    </div>

    <!-- Card Detail Modal -->
    <div
      v-if="activeCardDetail"
      class="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-surface-container-lowest rounded-2xl p-6 max-w-lg w-full border border-outline-variant/30 shadow-2xl flex flex-col gap-4">
        <div class="flex items-center justify-between pb-3 border-b border-surface-container-high/40">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-xl">style</span>
            <h2 class="font-bold text-base text-on-surface">Chi Tiết Thẻ Học #{{ activeCardDetail.id }}</h2>
          </div>
          <button @click="activeCardDetail = null" class="text-outline hover:text-on-surface">
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        <!-- Rendered Card Output -->
        <div class="p-4 rounded-xl bg-surface-container-low/40 border border-outline-variant/20 text-center max-h-48 overflow-y-auto">
          <div class="text-xs font-bold uppercase text-outline mb-1">Mặt Trước</div>
          <div v-html="activeCardDetail.rendered?.front_html" class="text-sm font-semibold text-on-surface"></div>
          <div class="text-xs font-bold uppercase text-outline mt-3 mb-1">Mặt Sau</div>
          <div v-html="activeCardDetail.rendered?.back_html" class="text-xs text-on-surface-variant"></div>
        </div>

        <!-- Card Metrics -->
        <div class="grid grid-cols-4 gap-2 text-center text-xs">
          <div class="p-2 rounded-xl bg-surface-container-low">
            <span class="text-outline text-[10px]">Khoảng cách</span>
            <div class="font-bold text-on-surface">{{ activeCardDetail.ivl }} ngày</div>
          </div>
          <div class="p-2 rounded-xl bg-surface-container-low">
            <span class="text-outline text-[10px]">Số lần ôn</span>
            <div class="font-bold text-on-surface">{{ activeCardDetail.reps }} lần</div>
          </div>
          <div class="p-2 rounded-xl bg-surface-container-low">
            <span class="text-outline text-[10px]">Quên (Lapses)</span>
            <div class="font-bold text-on-surface">{{ activeCardDetail.lapses }}</div>
          </div>
          <div class="p-2 rounded-xl bg-surface-container-low">
            <span class="text-outline text-[10px]">Độ dễ (Ease)</span>
            <div class="font-bold text-on-surface">{{ Math.round(activeCardDetail.factor / 10) }}%</div>
          </div>
        </div>

        <!-- Modal Footer Actions -->
        <div class="flex items-center justify-between pt-3 border-t border-surface-container-high mt-1">
          <router-link
            :to="`/study?deck_id=${deckId}`"
            class="px-4 py-2 rounded-xl bg-primary text-on-primary text-xs font-bold hover:bg-primary-container transition-colors"
          >
            Học Ngay
          </router-link>

          <button
            @click="activeCardDetail = null"
            class="px-4 py-2 rounded-xl text-xs font-bold text-outline hover:bg-surface-container"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>

    <!-- Guide Modal -->
    <div
      v-if="showGuideModal"
      class="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-surface-container-lowest rounded-2xl p-6 max-w-md w-full border border-outline-variant/30 shadow-2xl flex flex-col gap-4">
        <div class="flex items-center justify-between pb-2 border-b border-surface-container-high/40">
          <h2 class="font-bold text-base text-on-surface flex items-center gap-1.5">
            <span class="material-symbols-outlined text-primary">menu_book</span>
            <span>Hướng Dẫn Thống Kê</span>
          </h2>
          <button @click="showGuideModal = false" class="text-outline hover:text-on-surface">
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        <div class="text-xs text-on-surface-variant flex flex-col gap-2.5 leading-relaxed">
          <p>
            Trang <strong>Thống kê bộ thẻ</strong> tổng hợp toàn bộ thẻ trong bộ thẻ chính và tất cả các subdeck con lồng nhau.
          </p>
          <p>
            <strong>5 Cấp độ nhớ (Stability Tiers):</strong>
          </p>
          <ul class="list-disc pl-5 space-y-1">
            <li><strong class="text-amber-600">Mới nhớ:</strong> Khoảng cách ôn &lt; 1 ngày.</li>
            <li><strong class="text-amber-500">Đang nhớ:</strong> Khoảng cách ôn từ 1 - 7 ngày.</li>
            <li><strong class="text-emerald-500">Khá vững:</strong> Khoảng cách ôn từ 7 - 21 ngày.</li>
            <li><strong class="text-emerald-700">Vững:</strong> Khoảng cách ôn từ 21 - 60 ngày.</li>
            <li><strong class="text-blue-700">Nhớ lâu:</strong> Khoảng cách ôn &gt; 60 ngày (Thẻ đã thành thục).</li>
          </ul>
        </div>

        <div class="flex justify-end pt-2">
          <button
            @click="showGuideModal = false"
            class="px-5 py-2 rounded-xl bg-primary text-on-primary text-xs font-bold"
          >
            Đã Hiểu
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import api from '../api/client';

const route = useRoute();
const deckId = computed(() => Number(route.params.id) || 1);

const statsData = ref<any>(null);
const isLoading = ref(true);
const errorMessage = ref('');
const showGuideModal = ref(false);
const activeCardDetail = ref<any>(null);

onMounted(async () => {
  await fetchStats();
});

async function fetchStats() {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    const res = await api.get(`/stats/deck/${deckId.value}`);
    statsData.value = res.data;
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || 'Không thể tải thống kê cho bộ thẻ này.';
  } finally {
    isLoading.value = false;
  }
}

async function openCardModal(cardId: number) {
  try {
    const res = await api.get(`/cards/${cardId}`);
    activeCardDetail.value = res.data;
  } catch (err) {
    // ignore
  }
}

function tierColorClass(tier: number) {
  switch (tier) {
    case 1:
      return 'bg-amber-200';
    case 2:
      return 'bg-amber-400';
    case 3:
      return 'bg-emerald-400';
    case 4:
      return 'bg-emerald-600';
    case 5:
      return 'bg-blue-600';
    default:
      return 'bg-slate-300';
  }
}

// Compute Donut SVG Slices
const donutSlices = computed(() => {
  if (!statsData.value) return [];
  const dist = statsData.value.distribution;
  const total = max1(statsData.value.overview.total_cards);

  const items = [
    { label: 'Mới', count: dist.new, color: '#94a3b8' },
    { label: 'Đang học', count: dist.learning, color: '#f59e0b' },
    { label: 'Ôn tập', count: dist.review, color: '#10b981' },
    { label: 'Học lại', count: dist.relearning, color: '#f43f5e' },
    { label: 'Đánh dấu khó', count: dist.leeches, color: '#8b5cf6' },
    { label: 'Yêu thích', count: dist.starred, color: '#f97316' },
  ];

  let accumulatedLength = 0;
  return items.map((item) => {
    const pct = (item.count / total) * 100;
    const dashLength = Math.max(0.5, pct * 2.38); // Circumference for r=38 is ~238.7
    const offset = -accumulatedLength;
    accumulatedLength += dashLength;
    return {
      label: item.label,
      color: item.color,
      dashLength,
      offset,
    };
  });
});

function max1(n: number) {
  return n > 0 ? n : 1;
}
</script>

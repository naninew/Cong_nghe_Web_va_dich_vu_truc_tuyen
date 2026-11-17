<template>
  <div class="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-8 pb-24 lg:pb-8">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-extrabold text-on-surface tracking-tight">Thống Kê Học Tập & Hiệu Suất Nhớ</h1>
        <p class="text-xs text-on-surface-variant">Telemetry ôn tập, tỷ lệ lưu giữ bộ nhớ FSRS/SM-2 và chi tiết từng bộ thẻ.</p>
      </div>

      <!-- Quick Deck Jump -->
      <div class="flex items-center gap-2">
        <label class="text-xs font-bold text-outline">Xem theo bộ thẻ:</label>
        <select
          v-model="selectedDeckId"
          @change="onDeckSelect"
          class="px-3 py-2 rounded-xl bg-surface-container-lowest border border-outline-variant/30 text-xs font-bold text-on-surface outline-none shadow-sm cursor-pointer"
        >
          <option :value="null">-- Chọn bộ thẻ để xem chi tiết --</option>
          <option v-for="d in flatDecks" :key="d.id" :value="d.id">
            {{ d.fullName }} ({{ d.total_cards }} thẻ)
          </option>
        </select>
      </div>
    </div>

    <!-- Analytics Bento Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col justify-between">
        <span class="text-xs font-bold uppercase text-outline">Tỷ Lệ Nhớ Mục Tiêu</span>
        <div class="my-4">
          <span class="text-4xl font-extrabold text-secondary">{{ stats?.retention_rate || 92.4 }}%</span>
          <p class="text-xs text-on-surface-variant mt-2">
            Thuật toán Spaced Repetition đang duy trì tỷ lệ nhớ trên ngưỡng tối ưu 90%.
          </p>
        </div>
        <div class="flex items-center gap-2 text-xs font-semibold text-secondary">
          <span class="material-symbols-outlined text-base">check_circle</span>
          <span>Tham số FSRS tối ưu</span>
        </div>
      </div>

      <div class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col justify-between">
        <span class="text-xs font-bold uppercase text-outline">Tổng Thẻ Trong Hệ Thống</span>
        <div class="my-4">
          <span class="text-4xl font-extrabold text-on-surface">{{ (stats?.total_cards || 0).toLocaleString() }}</span>
          <p class="text-xs text-on-surface-variant mt-2">
            Tổng số thẻ trong cơ sở dữ liệu đã phân bổ theo từng bộ thẻ và subdeck.
          </p>
        </div>
        <div class="flex items-center gap-2 text-xs font-semibold text-primary">
          <span class="material-symbols-outlined text-base">storage</span>
          <span>PostgreSQL Multi-Tenant</span>
        </div>
      </div>

      <div class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col justify-between">
        <span class="text-xs font-bold uppercase text-outline">Chuỗi Ngày Học Liên Tục</span>
        <div class="my-4">
          <span class="text-4xl font-extrabold text-amber-700">{{ stats?.user.streak_days || 0 }} Ngày</span>
          <p class="text-xs text-on-surface-variant mt-2">
            Số ngày học liên tiếp ghi nhận vào hệ thống telemetry.
          </p>
        </div>
        <div class="flex items-center gap-2 text-xs font-semibold text-amber-700">
          <span class="material-symbols-outlined text-base">local_fire_department</span>
          <span>Thói quen học duy trì tốt</span>
        </div>
      </div>
    </div>

    <!-- Quick Links to Deck Stats -->
    <div class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col gap-4">
      <div class="flex items-center justify-between pb-3 border-b border-surface-container-high/40">
        <div class="flex items-center gap-2 text-on-surface font-extrabold text-base">
          <span class="material-symbols-outlined text-primary">donut_large</span>
          <span>Danh Sách Bộ Thẻ & Thống Kê Chuyên Sâu</span>
        </div>
        <router-link to="/library" class="text-xs font-bold text-primary hover:underline">
          Quản lý trong Library →
        </router-link>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div
          v-for="d in flatDecks.slice(0, 9)"
          :key="d.id"
          class="p-4 rounded-xl bg-surface-container-low/40 border border-outline-variant/20 hover:border-primary/40 transition-all flex flex-col justify-between gap-3"
        >
          <div>
            <h4 class="font-bold text-sm text-on-surface truncate" :title="d.fullName">
              {{ d.name }}
            </h4>
            <span class="text-[11px] text-outline font-semibold">
              {{ d.total_cards.toLocaleString() }} thẻ · {{ d.counts.due }} cần ôn
            </span>
          </div>

          <router-link
            :to="`/decks/${d.id}/stats`"
            class="w-full py-2 rounded-xl bg-primary-fixed hover:bg-primary-fixed-dim text-on-primary-fixed font-bold text-xs text-center flex items-center justify-center gap-1.5 transition-colors"
          >
            <span class="material-symbols-outlined text-base">insights</span>
            <span>Xem Báo Cáo & Ma Trận Từ</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useDeckStore } from '../stores/deck';
import api from '../api/client';
import type { StatsOverview, DeckTree } from '../types';

const router = useRouter();
const deckStore = useDeckStore();
const stats = ref<StatsOverview | null>(null);
const selectedDeckId = ref<number | null>(null);

const flatDecks = computed(() => {
  const result: Array<{ id: number; name: string; fullName: string; total_cards: number; counts: any }> = [];
  function traverse(node: DeckTree, prefix = '') {
    const fullName = prefix ? `${prefix}::${node.name}` : node.name;
    result.push({
      id: node.id,
      name: node.name,
      fullName,
      total_cards: node.total_cards,
      counts: node.counts,
    });
    for (const child of node.children) {
      traverse(child, fullName);
    }
  }
  for (const root of deckStore.decks) {
    traverse(root);
  }
  return result;
});

onMounted(async () => {
  await Promise.all([
    fetchGlobalStats(),
    deckStore.fetchDecks(),
  ]);
});

async function fetchGlobalStats() {
  try {
    const res = await api.get('/stats/overview');
    stats.value = res.data;
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
}

function onDeckSelect() {
  if (selectedDeckId.value) {
    router.push(`/decks/${selectedDeckId.value}/stats`);
  }
}
</script>

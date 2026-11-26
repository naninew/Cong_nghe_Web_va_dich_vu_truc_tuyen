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

    <!-- Error Banner -->
    <div
      v-if="loadError"
      class="px-4 py-3 rounded-xl bg-red-50 border border-error/30 text-error text-xs font-semibold flex items-center justify-between gap-3"
    >
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-base shrink-0">error</span>
        <span>{{ loadError }}</span>
      </div>
      <button
        @click="loadAnalyticsData"
        type="button"
        class="px-3 py-1 rounded-lg bg-error text-white text-[11px] font-bold hover:opacity-90 transition-opacity shrink-0"
      >
        Thử lại
      </button>
    </div>

    <!-- Analytics Bento Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col justify-between">
        <span class="text-xs font-bold uppercase text-outline">Tỷ Lệ Nhớ Thực Tế</span>
        <div class="my-4">
          <span class="text-4xl font-extrabold text-secondary">
            {{ stats?.retention_rate != null ? `${stats.retention_rate}%` : '—' }}
          </span>
          <p class="text-xs text-on-surface-variant mt-2">
            {{ retentionStatus.desc }}
          </p>
        </div>
        <div class="flex items-center gap-2 text-xs font-semibold" :class="retentionStatus.className">
          <span class="material-symbols-outlined text-base">{{ retentionStatus.icon }}</span>
          <span>{{ retentionStatus.label }}</span>
        </div>
      </div>

      <div class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col justify-between">
        <span class="text-xs font-bold uppercase text-outline">Tổng Thẻ Trong Hệ Thống</span>
        <div class="my-4">
          <span class="text-4xl font-extrabold text-on-surface">{{ (stats?.total_cards ?? 0).toLocaleString() }}</span>
          <p class="text-xs text-on-surface-variant mt-2">
            Tổng số thẻ trong cơ sở dữ liệu đã phân bổ theo từng bộ thẻ và subdeck.
          </p>
        </div>
        <div class="flex items-center gap-2 text-xs font-semibold text-primary">
          <span class="material-symbols-outlined text-base">storage</span>
          <span>{{ stats?.mature_cards ?? 0 }} đã thuộc · {{ stats?.new_cards ?? 0 }} thẻ mới</span>
        </div>
      </div>

      <div class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col justify-between">
        <span class="text-xs font-bold uppercase text-outline">Chuỗi Ngày Học Liên Tục</span>
        <div class="my-4">
          <span class="text-4xl font-extrabold text-amber-700">{{ stats?.user.streak_days ?? 0 }} Ngày</span>
          <p class="text-xs text-on-surface-variant mt-2">
            {{ (stats?.user.streak_days ?? 0) > 0 ? 'Số ngày học liên tiếp ghi nhận vào hệ thống.' : 'Hoàn thành lượt ôn hôm nay để bắt đầu chuỗi ngày học.' }}
          </p>
        </div>
        <div
          class="flex items-center gap-2 text-xs font-semibold"
          :class="(stats?.user.streak_days ?? 0) > 0 ? 'text-amber-700' : 'text-outline'"
        >
          <span class="material-symbols-outlined text-base">local_fire_department</span>
          <span>{{ (stats?.user.streak_days ?? 0) > 0 ? 'Thói quen học duy trì tốt' : 'Chưa có chuỗi ngày học' }}</span>
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

      <!-- Empty State -->
      <div
        v-if="!deckStore.isLoading && flatDecks.length === 0"
        class="py-8 text-center flex flex-col items-center gap-3"
      >
        <div class="w-12 h-12 rounded-2xl bg-primary-fixed/40 text-primary flex items-center justify-center">
          <span class="material-symbols-outlined text-2xl">library_add</span>
        </div>
        <div class="flex flex-col gap-1">
          <h4 class="font-bold text-sm text-on-surface">Chưa có bộ thẻ nào</h4>
          <p class="text-xs text-on-surface-variant">
            Hãy tạo bộ thẻ hoặc import file .apkg trong Library để xem thống kê chi tiết.
          </p>
        </div>
        <router-link
          to="/library"
          class="px-4 py-2 rounded-xl bg-primary text-on-primary text-xs font-bold hover:bg-primary-container transition-colors"
        >
          Đi tới Library
        </router-link>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div
          v-for="d in flatDecks"
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
const loadError = ref<string | null>(null);

const retentionStatus = computed(() => {
  const rate = stats.value?.retention_rate;
  if (rate == null) {
    return {
      label: 'Chưa có dữ liệu ôn tập',
      desc: 'Hãy bắt đầu ôn tập thẻ để hệ thống tính tỷ lệ nhớ trong 30 ngày gần nhất.',
      icon: 'hourglass_empty',
      className: 'text-outline',
    };
  }
  if (rate >= 85) {
    return {
      label: 'Tham số FSRS tối ưu',
      desc: 'Thuật toán Spaced Repetition đang duy trì tỷ lệ nhớ ở mức rất tốt.',
      icon: 'check_circle',
      className: 'text-secondary',
    };
  }
  if (rate >= 70) {
    return {
      label: 'Mức ghi nhớ ổn định',
      desc: 'Tỷ lệ nhớ trong 30 ngày qua ở mức khá. Duy trì ôn tập đều đặn mỗi ngày.',
      icon: 'trending_up',
      className: 'text-amber-700',
    };
  }
  return {
    label: 'Cần ôn tập thêm',
    desc: 'Tỷ lệ nhớ đang dưới ngưỡng tối ưu. Bạn nên ôn lại các thẻ hay quên.',
    icon: 'warning',
    className: 'text-error',
  };
});

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

async function loadAnalyticsData() {
  loadError.value = null;
  const results = await Promise.allSettled([
    fetchGlobalStats(),
    deckStore.fetchDecks(),
  ]);
  const failed = results.find((r) => r.status === 'rejected') as PromiseRejectedResult | undefined;
  if (failed) {
    loadError.value =
      failed.reason?.response?.data?.detail ||
      'Không thể tải đầy đủ dữ liệu thống kê. Vui lòng thử lại.';
  }
}

onMounted(loadAnalyticsData);

async function fetchGlobalStats() {
  const res = await api.get('/stats/overview');
  stats.value = res.data;
}

function onDeckSelect() {
  if (selectedDeckId.value) {
    router.push(`/decks/${selectedDeckId.value}/stats`);
  }
}
</script>

<template>
  <header class="fixed top-0 right-0 left-0 lg:left-[260px] h-[70px] bg-surface-container-lowest/80 backdrop-blur-md z-30 flex items-center justify-between px-4 sm:px-8 border-b border-outline-variant/20">
    <!-- Left: Mobile Brand & Search -->
    <div class="flex items-center gap-3">
      <!-- Mobile Logo -->
      <router-link to="/dashboard" class="flex lg:hidden items-center gap-2">
        <div class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-on-primary">
          <span class="material-symbols-outlined text-lg">psychology</span>
        </div>
        <span class="font-bold text-lg text-on-surface">Memora</span>
      </router-link>

      <router-link to="/browse" class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-surface-container-low text-on-surface-variant text-xs w-64 border border-outline-variant/20 hover:border-primary/40 transition-colors">
        <span class="material-symbols-outlined text-base">search</span>
        <span class="text-outline text-xs">Search cards, decks, tags...</span>
      </router-link>
    </div>

    <!-- Right: Telemetry (Streak, XP, Due Cards, Profile) -->
    <div class="flex items-center gap-3 sm:gap-4">
      <!-- Streak Flame -->
      <div class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-tertiary-fixed text-on-tertiary-fixed text-xs font-bold shadow-sm">
        <span class="material-symbols-outlined text-amber-700 text-base leading-none">local_fire_department</span>
        <span>{{ authStore.user?.streak_days || 0 }} Days</span>
      </div>

      <!-- XP Badge -->
      <div class="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-fixed text-on-secondary-fixed text-xs font-bold shadow-sm">
        <span class="material-symbols-outlined text-base leading-none">bolt</span>
        <span>{{ authStore.user?.xp || 0 }} XP</span>
      </div>

      <!-- Profile Avatar with Dropdown Menu -->
      <div class="relative">
        <button
          @click="showDropdown = !showDropdown"
          class="flex items-center gap-2 pl-2 focus:outline-none cursor-pointer group"
        >
          <img
            :src="authStore.user?.avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100'"
            alt="Avatar"
            class="w-8 h-8 rounded-full object-cover ring-2 ring-primary/20 group-hover:ring-primary transition-all"
          />
          <div class="hidden md:flex flex-col text-left">
            <span class="text-xs font-bold text-on-surface leading-tight">{{ authStore.user?.display_name || 'Scholar' }}</span>
            <span class="text-[10px] text-outline uppercase font-semibold">Scholar</span>
          </div>
          <span class="material-symbols-outlined text-outline text-sm">expand_more</span>
        </button>

        <!-- Dropdown Menu -->
        <div
          v-if="showDropdown"
          class="absolute right-0 mt-2 w-56 rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-xl py-2 z-50 flex flex-col gap-1"
          @click="showDropdown = false"
        >
          <div class="px-4 py-2 border-b border-surface-container-high/40">
            <p class="font-bold text-xs text-on-surface truncate">{{ authStore.user?.display_name }}</p>
            <p class="text-[10px] text-outline font-mono truncate">{{ authStore.user?.email }}</p>
          </div>

          <router-link
            to="/profile"
            class="flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-on-surface hover:bg-surface-container transition-colors"
          >
            <span class="material-symbols-outlined text-base text-primary">person</span>
            <span>Profile & Settings</span>
          </router-link>

          <router-link
            to="/browse"
            class="flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-on-surface hover:bg-surface-container transition-colors"
          >
            <span class="material-symbols-outlined text-base text-secondary">style</span>
            <span>Card Browser</span>
          </router-link>

          <router-link
            to="/study?filter_mode=lapsed_only"
            class="flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-amber-700 hover:bg-amber-50 transition-colors"
          >
            <span class="material-symbols-outlined text-base">replay</span>
            <span>Review Weak Cards</span>
          </router-link>

          <div class="border-t border-surface-container-high/40 my-1"></div>

          <button
            @click="handleLogout"
            class="w-full flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-error hover:bg-error-container/20 transition-colors text-left"
          >
            <span class="material-symbols-outlined text-base">logout</span>
            <span>Log Out</span>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';

const router = useRouter();
const authStore = useAuthStore();
const showDropdown = ref(false);

function handleLogout() {
  authStore.logout();
  router.push('/login');
}
</script>

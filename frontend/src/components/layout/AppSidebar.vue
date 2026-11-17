<template>
  <aside class="fixed left-0 top-0 h-full w-[260px] bg-surface-container-lowest z-40 hidden lg:flex flex-col justify-between shadow-[0_1px_8px_rgba(0,0,0,0.04)] border-r border-outline-variant/30">
    <div class="flex flex-col">
      <!-- Logo Branding -->
      <div class="h-[70px] flex items-center justify-between px-6 bg-surface-container-lowest border-b border-surface-container-high/40">
        <router-link to="/dashboard" class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-on-primary shadow-sm">
            <span class="material-symbols-outlined text-xl">psychology</span>
          </div>
          <span class="font-bold text-xl text-on-surface tracking-tight">Memora</span>
        </router-link>
        <span class="px-2 py-0.5 rounded-full bg-primary-fixed text-on-primary-fixed text-[11px] font-bold uppercase tracking-wider">
          Anki
        </span>
      </div>

      <!-- Navigation Links -->
      <div class="px-4 py-6">
        <p class="px-3 mb-2 text-[11px] font-bold uppercase tracking-wider text-outline">Main Menu</p>
        <nav class="flex flex-col gap-1.5">
          <router-link
            to="/dashboard"
            class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all"
            :class="$route.path === '/dashboard' ? 'bg-primary-fixed/60 text-primary font-semibold shadow-sm' : 'text-on-surface-variant hover:bg-surface-container-high/50 hover:text-on-surface'"
          >
            <span class="material-symbols-outlined text-xl">dashboard</span>
            <span>Dashboard</span>
          </router-link>

          <router-link
            to="/library"
            class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all"
            :class="$route.path.startsWith('/library') || $route.path.startsWith('/decks') ? 'bg-primary-fixed/60 text-primary font-semibold shadow-sm' : 'text-on-surface-variant hover:bg-surface-container-high/50 hover:text-on-surface'"
          >
            <span class="material-symbols-outlined text-xl">folder</span>
            <span>My Library</span>
          </router-link>

          <router-link
            to="/browse"
            class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all"
            :class="$route.path.startsWith('/browse') ? 'bg-primary-fixed/60 text-primary font-semibold shadow-sm' : 'text-on-surface-variant hover:bg-surface-container-high/50 hover:text-on-surface'"
          >
            <span class="material-symbols-outlined text-xl">style</span>
            <span>Browse Cards</span>
          </router-link>

          <router-link
            to="/study"
            class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all"
            :class="$route.path.startsWith('/study') ? 'bg-primary-fixed/60 text-primary font-semibold shadow-sm' : 'text-on-surface-variant hover:bg-surface-container-high/50 hover:text-on-surface'"
          >
            <span class="material-symbols-outlined text-xl">school</span>
            <span>Study Session</span>
          </router-link>

          <router-link
            to="/games"
            class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all"
            :class="$route.path.startsWith('/games') ? 'bg-primary-fixed/60 text-primary font-semibold shadow-sm' : 'text-on-surface-variant hover:bg-surface-container-high/50 hover:text-on-surface'"
          >
            <span class="material-symbols-outlined text-xl">sports_esports</span>
            <span>Quiz Game</span>
          </router-link>

          <router-link
            to="/analytics"
            class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all"
            :class="$route.path === '/analytics' ? 'bg-primary-fixed/60 text-primary font-semibold shadow-sm' : 'text-on-surface-variant hover:bg-surface-container-high/50 hover:text-on-surface'"
          >
            <span class="material-symbols-outlined text-xl">insights</span>
            <span>Analytics</span>
          </router-link>

          <router-link
            to="/profile"
            class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all"
            :class="$route.path === '/profile' ? 'bg-primary-fixed/60 text-primary font-semibold shadow-sm' : 'text-on-surface-variant hover:bg-surface-container-high/50 hover:text-on-surface'"
          >
            <span class="material-symbols-outlined text-xl">manage_accounts</span>
            <span>Profile & Settings</span>
          </router-link>
        </nav>
      </div>
    </div>

    <!-- Algorithm status indicator & user footer -->
    <div class="p-4 border-t border-surface-container-high/40">
      <div class="p-3 rounded-xl bg-surface-container-low/70 flex items-center justify-between text-xs text-on-surface-variant mb-3">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-secondary animate-pulse"></span>
          <span class="font-medium">FSRS & SM-2</span>
        </div>
        <span class="font-bold text-secondary">Active</span>
      </div>

      <button
        @click="handleLogout"
        class="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-outline hover:text-error hover:bg-error-container/20 rounded-lg transition-colors"
      >
        <span class="material-symbols-outlined text-base">logout</span>
        <span>Log Out</span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';

const router = useRouter();
const authStore = useAuthStore();

function handleLogout() {
  authStore.logout();
  router.push('/login');
}
</script>

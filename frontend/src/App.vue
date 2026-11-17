<template>
  <div class="min-h-screen bg-surface flex flex-col font-sans text-on-surface">
    <!-- Desktop Sidebar (hidden on login and mobile) -->
    <AppSidebar v-if="!isAuthPage" />

    <!-- Desktop Header -->
    <AppHeader v-if="!isAuthPage" />

    <!-- Main Content Area with sidebar offset on desktop -->
    <main
      class="flex-1 flex flex-col"
      :class="!isAuthPage ? 'lg:pl-[260px] pt-[70px]' : ''"
    >
      <router-view />
    </main>

    <!-- Mobile Bottom Navigation Dock -->
    <MobileBottomNav v-if="!isAuthPage" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from './stores/auth';
import AppSidebar from './components/layout/AppSidebar.vue';
import AppHeader from './components/layout/AppHeader.vue';
import MobileBottomNav from './components/layout/MobileBottomNav.vue';

const route = useRoute();
const authStore = useAuthStore();

const isAuthPage = computed(() => route.path === '/login');

onMounted(async () => {
  if (authStore.isAuthenticated && !authStore.user) {
    await authStore.fetchProfile();
  }
});
</script>

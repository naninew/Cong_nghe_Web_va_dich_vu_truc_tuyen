<template>
  <nav class="fixed bottom-0 left-0 right-0 h-[64px] bg-surface-container-lowest/95 backdrop-blur-md border-t border-outline-variant/30 z-40 flex lg:hidden items-center justify-around px-2 shadow-[0_-2px_10px_rgba(0,0,0,0.03)]">
    <router-link
      to="/dashboard"
      class="flex flex-col items-center justify-center w-14 h-full text-xs font-semibold transition-colors"
      :class="$route.path === '/dashboard' ? 'text-primary' : 'text-outline hover:text-on-surface'"
    >
      <span class="material-symbols-outlined text-2xl">dashboard</span>
      <span class="text-[10px] mt-0.5">Home</span>
    </router-link>

    <router-link
      to="/library"
      class="flex flex-col items-center justify-center w-14 h-full text-xs font-semibold transition-colors"
      :class="$route.path.startsWith('/library') || $route.path.startsWith('/decks') ? 'text-primary' : 'text-outline hover:text-on-surface'"
    >
      <span class="material-symbols-outlined text-2xl">style</span>
      <span class="text-[10px] mt-0.5">Decks</span>
    </router-link>

    <!-- Center Play/Study Action button -->
    <router-link
      to="/study"
      class="flex flex-col items-center justify-center -translate-y-3"
    >
      <div class="w-12 h-12 rounded-full bg-primary text-on-primary flex items-center justify-center shadow-lg shadow-primary/30 active:scale-95 transition-transform">
        <span class="material-symbols-outlined text-2xl">school</span>
      </div>
      <span class="text-[10px] font-bold text-primary mt-1">Study</span>
    </router-link>

    <router-link
      to="/games"
      class="flex flex-col items-center justify-center w-14 h-full text-xs font-semibold transition-colors"
      :class="$route.path.startsWith('/games') ? 'text-primary' : 'text-outline hover:text-on-surface'"
    >
      <span class="material-symbols-outlined text-2xl">sports_esports</span>
      <span class="text-[10px] mt-0.5">Quiz</span>
    </router-link>

    <router-link
      to="/analytics"
      class="flex flex-col items-center justify-center w-14 h-full text-xs font-semibold transition-colors"
      :class="$route.path === '/analytics' ? 'text-primary' : 'text-outline hover:text-on-surface'"
    >
      <span class="material-symbols-outlined text-2xl">insights</span>
      <span class="text-[10px] mt-0.5">Stats</span>
    </router-link>
  </nav>
</template>

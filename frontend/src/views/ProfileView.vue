<template>
  <div class="w-full max-w-4xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-8 pb-24 lg:pb-8">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-extrabold text-on-surface tracking-tight">Account Profile & Settings</h1>
      <p class="text-xs text-on-surface-variant">Manage your account information, SRS scheduler preferences, and multi-tenant test accounts.</p>
    </div>

    <!-- User Profile Card -->
    <div class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col sm:flex-row items-center sm:items-start gap-6">
      <!-- Avatar with Ring -->
      <div class="relative group">
        <img
          :src="authStore.user?.avatar_url || selectedAvatar"
          alt="Avatar"
          class="w-24 h-24 rounded-full object-cover ring-4 ring-primary/20 shadow-md"
        />
        <div class="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer">
          <span class="material-symbols-outlined text-white text-xl">photo_camera</span>
        </div>
      </div>

      <!-- Info & Stats -->
      <div class="flex-1 flex flex-col items-center sm:items-start gap-2 text-center sm:text-left">
        <div class="flex items-center gap-3">
          <h2 class="text-xl font-bold text-on-surface">{{ authStore.user?.display_name || 'Scholar' }}</h2>
          <span class="px-2.5 py-0.5 rounded-full bg-primary-fixed text-on-primary-fixed text-[11px] font-bold uppercase tracking-wider">
            {{ authStore.user?.role || 'User' }}
          </span>
        </div>
        <p class="text-xs text-outline font-mono">{{ authStore.user?.email }}</p>

        <!-- Mini Stats -->
        <div class="flex items-center gap-4 mt-3">
          <div class="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-surface-container-low text-xs font-bold text-on-surface">
            <span class="material-symbols-outlined text-amber-700 text-base">local_fire_department</span>
            <span>{{ authStore.user?.streak_days || 0 }} Days Streak</span>
          </div>

          <div class="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-surface-container-low text-xs font-bold text-on-surface">
            <span class="material-symbols-outlined text-secondary text-base">bolt</span>
            <span>{{ authStore.user?.xp || 0 }} XP</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Profile Information Section -->
    <div class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col gap-6">
      <h3 class="font-bold text-base text-on-surface">Edit Profile</h3>

      <!-- Display Name Input -->
      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-bold text-on-surface-variant">Display Name</label>
        <input
          v-model="displayName"
          type="text"
          class="px-3.5 py-2.5 rounded-xl bg-surface-container-low border border-outline-variant/30 text-xs text-on-surface outline-none focus:border-primary max-w-md"
          placeholder="Enter your display name"
        />
      </div>

      <!-- Avatar Presets Gallery -->
      <div class="flex flex-col gap-2">
        <label class="text-xs font-bold text-on-surface-variant">Choose Avatar Preset</label>
        <div class="flex items-center gap-3 flex-wrap">
          <div
            v-for="(url, idx) in avatarPresets"
            :key="idx"
            @click="selectedAvatar = url"
            class="w-12 h-12 rounded-full overflow-hidden cursor-pointer ring-2 transition-all"
            :class="selectedAvatar === url ? 'ring-primary scale-105' : 'ring-transparent hover:ring-outline'"
          >
            <img :src="url" alt="Preset" class="w-full h-full object-cover" />
          </div>
        </div>
      </div>

      <!-- Custom Avatar URL -->
      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-bold text-on-surface-variant">Or Custom Avatar Image URL</label>
        <input
          v-model="selectedAvatar"
          type="text"
          class="px-3.5 py-2.5 rounded-xl bg-surface-container-low border border-outline-variant/30 text-xs text-on-surface outline-none focus:border-primary max-w-lg"
          placeholder="https://..."
        />
      </div>

      <!-- Study Preferences -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-surface-container-high/40">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-on-surface-variant">Daily Review Target</label>
          <select
            v-model="dailyGoal"
            class="px-3.5 py-2.5 rounded-xl bg-surface-container-low border border-outline-variant/30 text-xs text-on-surface outline-none"
          >
            <option :value="20">20 cards / day (Light)</option>
            <option :value="50">50 cards / day (Standard)</option>
            <option :value="100">100 cards / day (Intensive)</option>
          </select>
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-on-surface-variant">Preferred SRS Scheduler</label>
          <select
            v-model="preferredScheduler"
            class="px-3.5 py-2.5 rounded-xl bg-surface-container-low border border-outline-variant/30 text-xs text-on-surface outline-none"
          >
            <option value="fsrs">FSRS v4.5 (Modern Machine Learning)</option>
            <option value="sm2">Anki SM-2 (Classic Spaced Repetition)</option>
          </select>
        </div>
      </div>

      <!-- Save Button -->
      <div class="flex justify-end pt-2">
        <button
          @click="saveProfile"
          :disabled="isSaving"
          class="px-6 py-2.5 rounded-xl bg-primary text-on-primary text-xs font-bold shadow-[0_3px_0_0_#1a0f91] active:translate-y-[2px] active:shadow-none hover:bg-primary-container transition-all disabled:opacity-50"
        >
          <span>{{ isSaving ? 'Saving...' : 'Save Profile Changes' }}</span>
        </button>
      </div>
    </div>

    <!-- Multi-Account Dev Switcher (Multi-Tenant Testing) -->
    <div class="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/20 shadow-sm flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-secondary text-xl">switch_account</span>
          <h3 class="font-bold text-base text-on-surface">Multi-Tenant Account Switcher (Dev Mode)</h3>
        </div>
        <span class="text-[10px] bg-secondary-fixed text-on-secondary-fixed font-bold px-2.5 py-0.5 rounded-full uppercase">
          Dev Active
        </span>
      </div>

      <p class="text-xs text-on-surface-variant leading-relaxed">
        Test multi-tenant isolation by switching instantly between different user accounts. Each user has their own private decks, card SRS states, and review history.
      </p>

      <!-- Account Switch List -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div
          v-for="u in devUsers"
          :key="u.id"
          @click="switchAccount(u.email, u.display_name)"
          class="p-3.5 rounded-xl border border-outline-variant/30 hover:border-primary transition-all cursor-pointer flex items-center justify-between"
          :class="u.id === authStore.user?.id ? 'bg-primary-fixed/20 border-primary' : 'bg-surface-container-low hover:bg-surface-container'"
        >
          <div class="flex items-center gap-2.5 min-w-0">
            <img :src="u.avatar_url || avatarPresets[0]" alt="Avt" class="w-8 h-8 rounded-full object-cover shrink-0" />
            <div class="flex flex-col min-w-0">
              <span class="font-bold text-xs text-on-surface truncate">{{ u.display_name }}</span>
              <span class="text-[10px] text-outline truncate">{{ u.email }}</span>
            </div>
          </div>

          <span v-if="u.id === authStore.user?.id" class="text-[10px] text-primary font-bold px-2 py-0.5 bg-primary-fixed rounded shrink-0">
            Current
          </span>
          <span v-else class="material-symbols-outlined text-outline text-base">login</span>
        </div>
      </div>

      <!-- Create New Mock Account -->
      <div class="mt-2 pt-4 border-t border-surface-container-high/40 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <input
          v-model="newMockEmail"
          type="email"
          placeholder="New user email (e.g. user2@example.com)"
          class="flex-1 px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant/30 text-xs text-on-surface outline-none"
        />
        <input
          v-model="newMockName"
          type="text"
          placeholder="Display Name"
          class="flex-1 px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant/30 text-xs text-on-surface outline-none"
        />
        <button
          @click="createAndSwitchUser"
          class="px-4 py-2 rounded-xl bg-surface-container-high text-on-surface font-bold text-xs hover:bg-surface-container-highest transition-colors shrink-0"
        >
          Create & Switch
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { useDeckStore } from '../stores/deck';
import api from '../api/client';
import type { DevUser } from '../types';

const router = useRouter();
const authStore = useAuthStore();
const deckStore = useDeckStore();

const displayName = ref(authStore.user?.display_name || '');
const selectedAvatar = ref(authStore.user?.avatar_url || '');
const dailyGoal = ref(authStore.user?.daily_goal || 50);
const preferredScheduler = ref('fsrs');
const isSaving = ref(false);

const devUsers = ref<DevUser[]>([]);
const newMockEmail = ref('');
const newMockName = ref('');

const avatarPresets = [
  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
  'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
  'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150',
  'https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=150',
  'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150',
];

onMounted(async () => {
  if (authStore.user) {
    displayName.value = authStore.user.display_name;
    selectedAvatar.value = authStore.user.avatar_url || avatarPresets[0];
    dailyGoal.value = authStore.user.daily_goal || 50;
  }
  await fetchDevUsers();
});

async function fetchDevUsers() {
  try {
    const res = await api.get('/auth/dev-users');
    devUsers.value = res.data;
  } catch (err) {
    console.warn('Dev users not available:', err);
  }
}

async function saveProfile() {
  isSaving.value = true;
  try {
    const res = await api.put('/auth/me', {
      display_name: displayName.value,
      avatar_url: selectedAvatar.value,
      daily_goal: Number(dailyGoal.value),
    });
    authStore.user = res.data;
    dailyGoal.value = res.data.daily_goal || 50;
    alert('Profile updated successfully!');
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Failed to update profile.');
  } finally {
    isSaving.value = false;
  }
}

async function switchAccount(email: string, name: string) {
  try {
    await authStore.loginDev(email, name);
    await deckStore.fetchDecks();
    displayName.value = authStore.user?.display_name || '';
    selectedAvatar.value = authStore.user?.avatar_url || avatarPresets[0];
    dailyGoal.value = authStore.user?.daily_goal || 50;
    alert(`Switched to account: ${email}`);
    router.push('/dashboard');
  } catch (err) {
    alert('Failed to switch account.');
  }
}

async function createAndSwitchUser() {
  if (!newMockEmail.value.trim()) {
    alert('Please enter an email.');
    return;
  }
  const name = newMockName.value.trim() || 'Scholar';
  await switchAccount(newMockEmail.value.trim(), name);
  newMockEmail.value = '';
  newMockName.value = '';
}
</script>

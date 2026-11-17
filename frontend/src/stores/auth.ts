import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../api/client';
import type { User } from '../types';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem('memora_access_token'));

  const isAuthenticated = computed(() => !!token.value);

  async function loginWithDev(email: string = 'tester@example.com', displayName: string = 'Scholar Alex') {
    const res = await api.post('/auth/dev-login', { email, display_name: displayName });
    token.value = res.data.access_token;
    user.value = res.data.user;
    localStorage.setItem('memora_access_token', res.data.access_token);
    return res.data;
  }

  async function loginWithGoogle(idToken: string) {
    const res = await api.post('/auth/google', { id_token: idToken });
    token.value = res.data.access_token;
    user.value = res.data.user;
    localStorage.setItem('memora_access_token', res.data.access_token);
    return res.data;
  }

  async function fetchProfile() {
    if (!token.value) return null;
    try {
      const res = await api.get('/auth/me');
      user.value = res.data;
      return res.data;
    } catch {
      logout();
      return null;
    }
  }

  function logout() {
    token.value = null;
    user.value = null;
    localStorage.removeItem('memora_access_token');
  }

  return {
    user,
    token,
    isAuthenticated,
    loginWithDev,
    loginWithGoogle,
    fetchProfile,
    logout,
  };
});

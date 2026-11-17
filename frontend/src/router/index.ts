import { createRouter, createWebHistory } from 'vue-router';
import DashboardView from '../views/DashboardView.vue';
import LibraryView from '../views/LibraryView.vue';
import StudyView from '../views/StudyView.vue';
import QuizGameView from '../views/QuizGameView.vue';
import QuizResultView from '../views/QuizResultView.vue';
import AnalyticsView from '../views/AnalyticsView.vue';
import DeckStatsView from '../views/DeckStatsView.vue';
import CardBrowserView from '../views/CardBrowserView.vue';
import ProfileView from '../views/ProfileView.vue';
import LoginView from '../views/LoginView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true },
    },
    {
      path: '/library',
      name: 'library',
      component: LibraryView,
      meta: { requiresAuth: true },
    },
    {
      path: '/browse',
      name: 'browse',
      component: CardBrowserView,
      meta: { requiresAuth: true },
    },
    {
      path: '/study',
      name: 'study',
      component: StudyView,
      meta: { requiresAuth: true },
    },
    {
      path: '/games',
      name: 'games',
      component: QuizGameView,
      meta: { requiresAuth: true },
    },
    {
      path: '/games/result',
      name: 'games-result',
      component: QuizResultView,
      meta: { requiresAuth: true },
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: AnalyticsView,
      meta: { requiresAuth: true },
    },
    {
      path: '/decks/:id/stats',
      name: 'deck-stats',
      component: DeckStatsView,
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true },
    },
  ],
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('memora_access_token');
  if (to.meta.requiresAuth && !token) {
    next('/login');
  } else if (to.path === '/login' && token) {
    next('/dashboard');
  } else {
    next();
  }
});

export default router;

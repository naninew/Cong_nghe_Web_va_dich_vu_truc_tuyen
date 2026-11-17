<template>
  <div class="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6 pb-24 lg:pb-8">
    <!-- Top Action Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-extrabold text-on-surface tracking-tight">Thư Viện Bộ Thẻ & Thẻ Học</h1>
        <p class="text-xs text-on-surface-variant">Quản lý các bộ thẻ Anki, hệ thống subdeck phân cấp, và tạo mới thẻ ghi nhớ.</p>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <!-- Add Card button -->
        <button
          @click="openAddCardModal"
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-secondary text-white text-xs font-bold shadow-[0_3px_0_0_#00452e] active:translate-y-[2px] active:shadow-none hover:bg-secondary/90 transition-all"
        >
          <span class="material-symbols-outlined text-base">note_add</span>
          <span>Thêm Thẻ Mới</span>
        </button>

        <!-- New Deck button -->
        <button
          @click="showCreateModal = true"
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-surface-container-lowest text-on-surface text-xs font-bold border border-outline-variant/30 hover:bg-surface-container-high transition-colors shadow-sm"
        >
          <span class="material-symbols-outlined text-base text-primary">add</span>
          <span>Tạo Bộ Thẻ</span>
        </button>

        <!-- Import .apkg button -->
        <button
          @click="showImportModal = true"
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-on-primary text-xs font-bold shadow-[0_3px_0_0_#1a0f91] active:translate-y-[2px] active:shadow-none hover:bg-primary-container transition-all"
        >
          <span class="material-symbols-outlined text-base">upload_file</span>
          <span>Import .apkg</span>
        </button>
      </div>
    </div>

    <!-- Search and Filter Bar -->
    <div class="flex items-center gap-3 p-3 bg-surface-container-lowest rounded-2xl border border-outline-variant/20 shadow-sm">
      <span class="material-symbols-outlined text-outline">search</span>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Tìm kiếm bộ thẻ theo tên hoặc thư mục con..."
        class="bg-transparent border-none outline-none w-full text-xs text-on-surface placeholder:text-outline"
      />
      <span v-if="searchQuery" @click="searchQuery = ''" class="material-symbols-outlined text-outline cursor-pointer text-base">
        close
      </span>
    </div>

    <!-- Deck Hierarchy Tree List -->
    <div class="flex flex-col gap-3">
      <div v-if="deckStore.isLoading" class="p-12 text-center text-outline text-sm">
        <span class="material-symbols-outlined animate-spin text-2xl text-primary mb-2">progress_activity</span>
        <p>Đang tải thư viện bộ thẻ...</p>
      </div>

      <div v-else-if="filteredDecks.length === 0" class="p-12 text-center bg-surface-container-lowest rounded-2xl border border-outline-variant/20">
        <span class="material-symbols-outlined text-4xl text-outline mb-2">folder_off</span>
        <h3 class="font-bold text-base text-on-surface">Không Tìm Thấy Bộ Thẻ</h3>
        <p class="text-xs text-on-surface-variant max-w-sm mx-auto mt-1 mb-4">
          Tải lên gói Anki (.apkg) hoặc bấm Tạo Bộ Thẻ để bắt đầu học tập.
        </p>
        <button
          @click="showImportModal = true"
          class="px-4 py-2 rounded-xl bg-primary text-on-primary text-xs font-bold"
        >
          Nạp Dữ Liệu .apkg
        </button>
      </div>

      <!-- Deck Item Recursive Component -->
      <DeckTreeItem
        v-for="deck in filteredDecks"
        :key="deck.id"
        :deck="deck"
        @edit-deck="handleEditDeck"
        @delete-deck="handleDeleteDeck"
      />
    </div>

    <!-- ================= MODAL: CREATE DECK ================= -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-surface-container-lowest rounded-2xl p-6 max-w-md w-full border border-outline-variant/30 shadow-2xl flex flex-col gap-4">
        <div class="flex items-center justify-between pb-2 border-b border-surface-container-high/40">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-xl">create_new_folder</span>
            <h2 class="font-bold text-base text-on-surface">Tạo Bộ Thẻ Mới</h2>
          </div>
          <button @click="showCreateModal = false" class="text-outline hover:text-on-surface">
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        <div class="flex flex-col gap-3 text-xs">
          <div class="flex flex-col gap-1">
            <label class="font-bold text-on-surface-variant">Tên bộ thẻ (dùng :: để tạo subdeck lồng nhau)</label>
            <input
              v-model="newDeckName"
              type="text"
              placeholder="Ví dụ: Tiếng Anh::Từ Vựng IELTS"
              class="px-3 py-2.5 rounded-xl bg-surface-container-low border border-outline-variant/20 text-xs text-on-surface outline-none focus:border-primary"
            />
          </div>

          <div class="flex flex-col gap-1">
            <label class="font-bold text-on-surface-variant">Mô tả (tùy chọn)</label>
            <textarea
              v-model="newDeckDesc"
              rows="3"
              placeholder="Mô tả mục tiêu học tập của bộ thẻ này..."
              class="px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant/20 text-xs text-on-surface outline-none focus:border-primary resize-none"
            ></textarea>
          </div>
        </div>

        <div class="flex justify-end gap-2 pt-2 border-t border-surface-container-high/40">
          <button
            @click="showCreateModal = false"
            class="px-4 py-2 rounded-xl text-xs font-bold text-outline hover:bg-surface-container"
          >
            Hủy
          </button>
          <button
            @click="submitCreateDeck"
            :disabled="!newDeckName.trim()"
            class="px-5 py-2 rounded-xl bg-primary text-on-primary text-xs font-bold disabled:opacity-50 hover:bg-primary-container transition-colors"
          >
            Tạo Bộ Thẻ
          </button>
        </div>
      </div>
    </div>

    <!-- ================= MODAL: EDIT DECK ================= -->
    <div
      v-if="editingDeck"
      class="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-surface-container-lowest rounded-2xl p-6 max-w-md w-full border border-outline-variant/30 shadow-2xl flex flex-col gap-4">
        <div class="flex items-center justify-between pb-2 border-b border-surface-container-high/40">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-xl">edit</span>
            <h2 class="font-bold text-base text-on-surface">Đổi Tên / Sửa Bộ Thẻ</h2>
          </div>
          <button @click="editingDeck = null" class="text-outline hover:text-on-surface">
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        <div class="flex flex-col gap-3 text-xs">
          <div class="flex flex-col gap-1">
            <label class="font-bold text-on-surface-variant">Tên bộ thẻ</label>
            <input
              v-model="editDeckName"
              type="text"
              class="px-3 py-2.5 rounded-xl bg-surface-container-low border border-outline-variant/20 text-xs text-on-surface outline-none focus:border-primary"
            />
          </div>

          <div class="flex flex-col gap-1">
            <label class="font-bold text-on-surface-variant">Mô tả</label>
            <textarea
              v-model="editDeckDesc"
              rows="3"
              class="px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant/20 text-xs text-on-surface outline-none focus:border-primary resize-none"
            ></textarea>
          </div>
        </div>

        <div class="flex justify-end gap-2 pt-2 border-t border-surface-container-high/40">
          <button
            @click="editingDeck = null"
            class="px-4 py-2 rounded-xl text-xs font-bold text-outline hover:bg-surface-container"
          >
            Hủy
          </button>
          <button
            @click="submitUpdateDeck"
            :disabled="!editDeckName.trim()"
            class="px-5 py-2 rounded-xl bg-primary text-on-primary text-xs font-bold disabled:opacity-50 hover:bg-primary-container transition-colors"
          >
            Lưu Thay Đổi
          </button>
        </div>
      </div>
    </div>

    <!-- ================= MODAL: DELETE DECK CONFIRMATION ================= -->
    <div
      v-if="deletingDeck"
      class="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-surface-container-lowest rounded-2xl p-6 max-w-md w-full border border-red-200 shadow-2xl flex flex-col gap-4">
        <div class="flex items-center gap-2 text-red-600">
          <span class="material-symbols-outlined text-2xl">warning</span>
          <h2 class="font-bold text-base">Xác Nhận Xóa Bộ Thẻ</h2>
        </div>

        <p class="text-xs text-on-surface-variant leading-relaxed">
          Bạn có chắc chắn muốn xóa bộ thẻ <strong>"{{ deletingDeck.name }}"</strong>?
          Tất cả các thẻ và subdeck trực thuộc bộ thẻ này sẽ bị xóa hoàn toàn khỏi tài khoản của bạn.
        </p>

        <div class="flex justify-end gap-2 pt-2 border-t border-surface-container-high/40">
          <button
            @click="deletingDeck = null"
            class="px-4 py-2 rounded-xl text-xs font-bold text-outline hover:bg-surface-container"
          >
            Hủy
          </button>
          <button
            @click="submitDeleteDeck"
            class="px-5 py-2 rounded-xl bg-red-600 text-white text-xs font-bold hover:bg-red-700 transition-colors shadow-sm"
          >
            Xác Nhận Xóa
          </button>
        </div>
      </div>
    </div>

    <!-- ================= MODAL: ADD NEW CARD ================= -->
    <div
      v-if="showAddCardModal"
      class="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-surface-container-lowest rounded-2xl p-6 max-w-xl w-full border border-outline-variant/30 shadow-2xl flex flex-col gap-4 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between pb-2 border-b border-surface-container-high/40">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-secondary text-2xl">note_add</span>
            <h2 class="font-bold text-base text-on-surface">Thêm Thẻ Ghi Nhớ Mới</h2>
          </div>
          <button @click="showAddCardModal = false" class="text-outline hover:text-on-surface">
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        <!-- Target Deck Selection -->
        <div class="flex flex-col gap-1 text-xs">
          <label class="font-bold text-on-surface-variant">Chọn Bộ Thẻ Đích</label>
          <select
            v-model="newCardDeckId"
            class="px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant/20 text-xs font-semibold text-on-surface outline-none"
          >
            <option v-for="d in flatDecksList" :key="d.id" :value="d.id">
              {{ d.fullName }}
            </option>
          </select>
        </div>

        <!-- Notetype Selection -->
        <div class="flex flex-col gap-1 text-xs">
          <label class="font-bold text-on-surface-variant">Loại Thẻ (Notetype)</label>
          <select
            v-model="newCardNotetypeId"
            @change="onNotetypeChange"
            class="px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant/20 text-xs font-semibold text-on-surface outline-none"
          >
            <option v-for="nt in availableNotetypes" :key="nt.id" :value="nt.id">
              {{ nt.name }} ({{ nt.fields.length }} trường)
            </option>
          </select>
        </div>

        <!-- Dynamic Fields Input based on Selected Notetype -->
        <div class="flex flex-col gap-3 py-2 border-t border-b border-surface-container-high/40">
          <span class="text-xs font-bold text-outline uppercase">Nội Dung Các Trường (Fields)</span>
          <div
            v-for="fld in currentNotetypeFields"
            :key="fld.name"
            class="flex flex-col gap-1 text-xs"
          >
            <label class="font-bold text-on-surface">{{ fld.name }}</label>
            <textarea
              v-model="newCardFields[fld.name]"
              rows="2"
              :placeholder="`Nhập nội dung cho trường ${fld.name}...`"
              class="px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant/20 text-xs text-on-surface outline-none focus:border-primary resize-none"
            ></textarea>
          </div>
        </div>

        <!-- Tags Input -->
        <div class="flex flex-col gap-1 text-xs">
          <label class="font-bold text-on-surface-variant">Thẻ phân loại (Tags, cách nhau bởi dấu cách)</label>
          <input
            v-model="newCardTags"
            type="text"
            placeholder="vd: vocab n2 daily"
            class="px-3 py-2 rounded-xl bg-surface-container-low border border-outline-variant/20 text-xs text-on-surface outline-none focus:border-primary"
          />
        </div>

        <div class="flex justify-end gap-2 pt-2">
          <button
            @click="showAddCardModal = false"
            class="px-4 py-2 rounded-xl text-xs font-bold text-outline hover:bg-surface-container"
          >
            Hủy
          </button>
          <button
            @click="submitCreateCard"
            class="px-5 py-2 rounded-xl bg-secondary text-white text-xs font-bold hover:bg-secondary/90 transition-colors shadow-sm"
          >
            Tạo Thẻ
          </button>
        </div>
      </div>
    </div>

    <!-- ================= MODAL: IMPORT APKG ================= -->
    <div
      v-if="showImportModal"
      class="fixed inset-0 bg-on-surface/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-surface-container-lowest rounded-2xl p-6 max-w-lg w-full border border-outline-variant/30 shadow-2xl flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-2xl">upload_file</span>
            <h2 class="font-bold text-lg text-on-surface">Import Gói Anki (.apkg)</h2>
          </div>
          <button @click="closeImportModal" class="text-outline hover:text-on-surface">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <p class="text-xs text-on-surface-variant">
          Tải lên file gói Anki (.apkg). Toàn bộ bộ thẻ, subdeck, ghi chú, media ảnh/âm thanh và cấu hình sẽ được nạp riêng cho tài khoản của bạn.
        </p>

        <!-- Drop area -->
        <div
          class="border-2 border-dashed border-outline-variant rounded-2xl p-8 text-center flex flex-col items-center justify-center gap-3 cursor-pointer hover:border-primary transition-colors bg-surface-container-low/30"
          @click="fileInput?.click()"
        >
          <span class="material-symbols-outlined text-4xl text-primary">cloud_upload</span>
          <p class="text-xs font-bold text-on-surface">Nhấp để chọn file hoặc kéo thả file .apkg vào đây</p>
          <span class="text-[11px] text-outline">Hỗ trợ .apkg và .colpkg lên đến 100MB</span>
          <input
            ref="fileInput"
            type="file"
            accept=".apkg,.colpkg"
            class="hidden"
            @change="handleFileUpload"
          />
        </div>

        <!-- Progress Bar if importing -->
        <div v-if="isImporting" class="flex flex-col gap-2">
          <div class="flex items-center justify-between text-xs font-semibold text-on-surface">
            <span>{{ importStatusText }}</span>
            <span>{{ importProgress }}%</span>
          </div>
          <div class="w-full h-2 rounded-full bg-surface-container-high overflow-hidden">
            <div
              class="h-full bg-secondary rounded-full transition-all duration-300"
              :style="{ width: `${importProgress}%` }"
            ></div>
          </div>
        </div>

        <div class="flex justify-end gap-3 mt-2">
          <button
            @click="closeImportModal"
            class="px-4 py-2 rounded-xl text-xs font-bold text-outline hover:bg-surface-container"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useDeckStore } from '../stores/deck';
import DeckTreeItem from '../components/deck/DeckTreeItem.vue';
import api from '../api/client';
import type { DeckTree } from '../types';

const deckStore = useDeckStore();
const searchQuery = ref('');

// Modals
const showImportModal = ref(false);
const showCreateModal = ref(false);
const showAddCardModal = ref(false);

// Deck Create / Edit / Delete states
const newDeckName = ref('');
const newDeckDesc = ref('');
const editingDeck = ref<DeckTree | null>(null);
const editDeckName = ref('');
const editDeckDesc = ref('');
const deletingDeck = ref<DeckTree | null>(null);

// Card Create states
const availableNotetypes = ref<any[]>([]);
const newCardDeckId = ref<number | null>(null);
const newCardNotetypeId = ref<number | null>(null);
const newCardFields = ref<Record<string, string>>({});
const newCardTags = ref('');

// Import state
const fileInput = ref<HTMLInputElement | null>(null);
const isImporting = ref(false);
const importProgress = ref(0);
const importStatusText = ref('');
let pollInterval: any = null;

const filteredDecks = computed(() => {
  if (!searchQuery.value) return deckStore.decks;
  const q = searchQuery.value.toLowerCase();
  return deckStore.decks.filter(d => d.name.toLowerCase().includes(q));
});

const flatDecksList = computed(() => {
  const list: Array<{ id: number; fullName: string }> = [];
  function traverse(node: DeckTree, prefix = '') {
    const fullName = prefix ? `${prefix}::${node.name}` : node.name;
    list.push({ id: node.id, fullName });
    for (const child of node.children) {
      traverse(child, fullName);
    }
  }
  for (const root of deckStore.decks) {
    traverse(root);
  }
  return list;
});

const currentNotetypeFields = computed(() => {
  if (!newCardNotetypeId.value) return [];
  const nt = availableNotetypes.value.find(n => n.id === newCardNotetypeId.value);
  return nt ? nt.fields : [];
});

onMounted(async () => {
  await deckStore.fetchDecks();
});

// Deck CRUD
async function submitCreateDeck() {
  if (!newDeckName.value.trim()) return;
  try {
    await api.post('/decks', {
      name: newDeckName.value.trim(),
      description: newDeckDesc.value.trim(),
    });
    showCreateModal.value = false;
    newDeckName.value = '';
    newDeckDesc.value = '';
    await deckStore.fetchDecks();
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Lỗi khi tạo bộ thẻ.');
  }
}

function handleEditDeck(deck: DeckTree) {
  editingDeck.value = deck;
  editDeckName.value = deck.name;
  editDeckDesc.value = deck.description || '';
}

async function submitUpdateDeck() {
  if (!editingDeck.value || !editDeckName.value.trim()) return;
  try {
    await api.patch(`/decks/${editingDeck.value.id}`, {
      name: editDeckName.value.trim(),
      description: editDeckDesc.value.trim(),
    });
    editingDeck.value = null;
    await deckStore.fetchDecks();
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Lỗi khi cập nhật bộ thẻ.');
  }
}

function handleDeleteDeck(deck: DeckTree) {
  deletingDeck.value = deck;
}

async function submitDeleteDeck() {
  if (!deletingDeck.value) return;
  try {
    await api.delete(`/decks/${deletingDeck.value.id}`);
    deletingDeck.value = null;
    await deckStore.fetchDecks();
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Lỗi khi xóa bộ thẻ.');
  }
}

// Card CRUD
async function openAddCardModal() {
  try {
    const res = await api.get('/cards/notetypes/list');
    availableNotetypes.value = res.data;
    if (availableNotetypes.value.length > 0) {
      newCardNotetypeId.value = availableNotetypes.value[0].id;
      initCardFields();
    }
    if (flatDecksList.value.length > 0) {
      newCardDeckId.value = flatDecksList.value[0].id;
    }
    showAddCardModal.value = true;
  } catch (err) {
    alert('Không thể tải danh sách loại thẻ (Notetype).');
  }
}

function onNotetypeChange() {
  initCardFields();
}

function initCardFields() {
  newCardFields.value = {};
  for (const f of currentNotetypeFields.value) {
    newCardFields.value[f.name] = '';
  }
}

async function submitCreateCard() {
  if (!newCardDeckId.value || !newCardNotetypeId.value) return;
  try {
    const tagsArr = newCardTags.value.split(/\s+/).filter(Boolean);
    await api.post('/cards', {
      deck_id: newCardDeckId.value,
      notetype_id: newCardNotetypeId.value,
      fields: newCardFields.value,
      tags: tagsArr,
    });
    alert('Thêm thẻ mới thành công!');
    showAddCardModal.value = false;
    await deckStore.fetchDecks();
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Lỗi khi tạo thẻ.');
  }
}

// Import Handling
function closeImportModal() {
  if (pollInterval) clearInterval(pollInterval);
  showImportModal.value = false;
  isImporting.value = false;
  importProgress.value = 0;
}

async function handleFileUpload(e: any) {
  const file = e.target.files[0];
  if (!file) return;

  isImporting.value = true;
  importProgress.value = 10;
  importStatusText.value = 'Đang tải file lên...';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await api.post('/import-export/import/apkg', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    const jobId = res.data.job_id;
    importStatusText.value = 'Đang giải nén bộ thẻ và media...';

    pollInterval = setInterval(async () => {
      try {
        const sRes = await api.get(`/import-export/import/status/${jobId}`);
        const data = sRes.data;
        importProgress.value = data.progress_percent;
        if (data.status === 'completed') {
          clearInterval(pollInterval);
          importStatusText.value = 'Nạp dữ liệu hoàn tất!';
          await deckStore.fetchDecks();
          setTimeout(() => {
            closeImportModal();
          }, 1200);
        } else if (data.status === 'failed') {
          clearInterval(pollInterval);
          importStatusText.value = `Thất bại: ${data.error_message || 'Lỗi không xác định'}`;
        }
      } catch (err) {
        clearInterval(pollInterval);
      }
    }, 1000);
  } catch (err: any) {
    isImporting.value = false;
    alert(err.response?.data?.detail || 'Import thất bại.');
  }
}
</script>

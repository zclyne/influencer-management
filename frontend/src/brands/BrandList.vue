<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { message, Modal, type FormInstance, type TableColumnsType } from 'ant-design-vue'
import type { BrandCreateRequest, BrandResponse, BrandUpdateRequest } from '../api/types'
import { useBrands } from './useBrands'

interface BrandForm {
  name: string
  website: string
  notes: string
}

const formRef = ref<FormInstance>()
const modalOpen = ref(false)
const editingBrand = ref<BrandResponse | null>(null)
const brandForm = reactive<BrandForm>({
  name: '',
  website: '',
  notes: '',
})

const {
  brands,
  loading,
  saving,
  archiving,
  error,
  searchText,
  includeArchived,
  selectedRowKeys,
  activeBrandCount,
  linkedCampaignCount,
  archivedBrandCount,
  loadBrands,
  createNewBrand,
  updateExistingBrand,
  archiveBrand,
  archiveSelectedBrands,
} = useBrands()

const columns: TableColumnsType<BrandResponse> = [
  {
    title: 'Brand',
    key: 'brand',
    dataIndex: 'name',
  },
  {
    title: 'Website',
    key: 'website',
    dataIndex: 'website',
  },
  {
    title: 'Campaigns',
    key: 'campaigns',
    dataIndex: 'campaign_count',
    align: 'right',
    width: 120,
    sorter: (left, right) => (left.campaign_count ?? 0) - (right.campaign_count ?? 0),
  },
  {
    title: 'Updated',
    key: 'updated',
    dataIndex: 'updated_at',
    width: 140,
    sorter: (left, right) =>
      new Date(left.updated_at).getTime() - new Date(right.updated_at).getTime(),
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 160,
  },
]

const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: (string | number)[]) => {
    selectedRowKeys.value = keys.map(String)
  },
  getCheckboxProps: (record: BrandResponse) => ({
    disabled: Boolean(record.archived_at),
  }),
}))

const formatDate = (value: string) =>
  new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value))

const resetForm = () => {
  brandForm.name = ''
  brandForm.website = ''
  brandForm.notes = ''
  editingBrand.value = null
  formRef.value?.clearValidate()
}

const openCreateModal = () => {
  resetForm()
  modalOpen.value = true
}

const openEditModal = (brand: BrandResponse) => {
  editingBrand.value = brand
  brandForm.name = brand.name
  brandForm.website = brand.website ?? ''
  brandForm.notes = brand.notes ?? ''
  modalOpen.value = true
}

const buildCreatePayload = (): BrandCreateRequest => ({
  name: brandForm.name.trim(),
  website: brandForm.website.trim() || null,
  notes: brandForm.notes.trim() || null,
})

const buildUpdatePayload = (): BrandUpdateRequest => ({
  name: brandForm.name.trim(),
  website: brandForm.website.trim() || null,
  notes: brandForm.notes.trim() || null,
})

const submitBrand = async () => {
  await formRef.value?.validate()

  try {
    if (editingBrand.value) {
      await updateExistingBrand(editingBrand.value.id, buildUpdatePayload())
      message.success(`${brandForm.name.trim()} updated.`)
    } else {
      await createNewBrand(buildCreatePayload())
      message.success('Brand created.')
    }
    modalOpen.value = false
    resetForm()
  } catch {
    message.error(editingBrand.value ? 'Brand could not be updated.' : 'Brand could not be created.')
  }
}

const archiveOne = async (brand: BrandResponse) => {
  try {
    await archiveBrand(brand.id)
    message.success(`${brand.name} deleted.`)
  } catch {
    message.error(`${brand.name} could not be deleted.`)
  }
}

const confirmBulkArchive = () => {
  if (!selectedRowKeys.value.length) return

  Modal.confirm({
    title: 'Delete selected brands?',
    content: 'Deleted brands are hidden unless Include deleted is turned on.',
    okText: 'Delete selected',
    okType: 'danger',
    cancelText: 'Cancel',
    onOk: async () => {
      const result = await archiveSelectedBrands()
      if (result.failed) {
        message.error(`${result.failed} brand(s) could not be deleted.`)
      }
      if (result.archived) {
        message.success(`${result.archived} brand(s) deleted.`)
      }
    },
  })
}

watch(modalOpen, (open) => {
  if (!open) resetForm()
})

void loadBrands()
</script>

<template>
  <section class="brand-list-page">
    <div class="page-heading">
      <div>
        <h1>Brand list</h1>
        <p class="page-description">
          Manage standalone brand records that can be associated with campaigns.
        </p>
      </div>
    </div>

    <a-alert v-if="error" class="page-alert" type="error" :message="error" show-icon />

    <div class="summary-grid">
      <a-card size="small">
        <span>Active brands</span>
        <strong>{{ activeBrandCount }}</strong>
      </a-card>
      <a-card size="small">
        <span>Linked campaigns</span>
        <strong>{{ linkedCampaignCount }}</strong>
      </a-card>
      <a-card v-if="includeArchived" size="small">
        <span>Deleted</span>
        <strong>{{ archivedBrandCount }}</strong>
      </a-card>
    </div>

    <a-card class="table-card" :body-style="{ padding: '0' }">
      <div class="table-toolbar">
        <div class="table-toolbar-controls">
          <a-input-search
            v-model:value="searchText"
            class="search-input"
            allow-clear
            placeholder="Search brands"
          />
          <label class="archive-toggle">
            <span>Include deleted</span>
            <a-switch v-model:checked="includeArchived" />
          </label>
        </div>
        <div class="table-toolbar-actions">
          <a-button
            danger
            :disabled="!selectedRowKeys.length || archiving"
            :loading="archiving"
            @click="confirmBulkArchive"
          >
            Delete selected
          </a-button>
          <a-button type="primary" @click="openCreateModal">New brand</a-button>
        </div>
      </div>

      <a-table
        :columns="columns"
        :data-source="brands"
        :loading="loading"
        :pagination="{ pageSize: 10, showSizeChanger: true }"
        :row-key="(record: BrandResponse) => record.id"
        :row-selection="rowSelection"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'brand'">
            <div class="brand-cell">
              <strong>{{ record.name }}</strong>
              <span v-if="record.notes">{{ record.notes }}</span>
              <a-tag v-if="record.archived_at" color="red">Deleted</a-tag>
            </div>
          </template>

          <template v-else-if="column.key === 'website'">
            <a v-if="record.website" :href="record.website" target="_blank" rel="noreferrer">
              {{ record.website }}
            </a>
            <span v-else class="muted">No website</span>
          </template>

          <template v-else-if="column.key === 'campaigns'">
            <span>{{ record.campaign_count ?? 0 }}</span>
          </template>

          <template v-else-if="column.key === 'updated'">
            <span>{{ formatDate(record.updated_at) }}</span>
          </template>

          <template v-else-if="column.key === 'actions'">
            <div class="action-row">
              <a-button type="link" @click="openEditModal(record)">Edit</a-button>
            <a-popconfirm
              v-if="!record.archived_at"
              title="Delete this brand?"
              ok-text="Delete"
              cancel-text="Cancel"
              @confirm="archiveOne(record)"
            >
              <a-button danger type="link">Delete</a-button>
            </a-popconfirm>
              <span v-else class="muted">Deleted</span>
            </div>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="modalOpen"
      :title="editingBrand ? 'Edit brand' : 'New brand'"
      :ok-text="editingBrand ? 'Save brand' : 'Create brand'"
      cancel-text="Cancel"
      :confirm-loading="saving"
      destroy-on-close
      @ok="submitBrand"
    >
      <a-form ref="formRef" :model="brandForm" layout="vertical">
        <a-form-item
          label="Name"
          name="name"
          :rules="[{ required: true, message: 'Brand name is required.' }]"
        >
          <a-input v-model:value="brandForm.name" placeholder="Brand name" />
        </a-form-item>

        <a-form-item label="Website" name="website">
          <a-input v-model:value="brandForm.website" placeholder="https://example.com" />
        </a-form-item>

        <a-form-item label="Notes" name="notes">
          <a-textarea v-model:value="brandForm.notes" :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>
  </section>
</template>

<style scoped>
.brand-list-page {
  display: grid;
  gap: 18px;
}

.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

h1 {
  margin: 0;
  color: #20262d;
  font-size: 30px;
}

.page-description {
  max-width: 720px;
  margin: 8px 0 0;
  color: #58636f;
  line-height: 1.5;
}

.page-alert {
  border-radius: 8px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(160px, 1fr));
  gap: 12px;
}

.summary-grid :deep(.ant-card-body) {
  display: grid;
  gap: 6px;
}

.summary-grid span,
.muted {
  color: #697582;
}

.summary-grid strong {
  color: #20262d;
  font-size: 26px;
}

.table-card {
  overflow: hidden;
}

.table-card :deep(.ant-card-body) {
  min-width: 0;
  overflow-x: auto;
}

.table-card :deep(.ant-table-wrapper) {
  max-width: 100%;
  min-width: 0;
}

.table-card :deep(.ant-table-pagination) {
  padding-inline: 14px;
}

.table-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-bottom: 1px solid #edf0f5;
}

.table-toolbar-controls,
.table-toolbar-actions,
.action-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.table-toolbar-actions,
.action-row {
  flex-wrap: nowrap;
  justify-content: flex-end;
}

.search-input {
  width: min(300px, 100%);
}

.archive-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #4e5965;
  white-space: nowrap;
}

.brand-cell {
  display: grid;
  gap: 4px;
}

.brand-cell strong {
  color: #20262d;
}

.brand-cell span {
  max-width: 420px;
  overflow: hidden;
  color: #697582;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .table-toolbar {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .table-toolbar-controls,
  .table-toolbar-actions {
    flex-wrap: wrap;
  }

  .search-input,
  .archive-toggle,
  .table-toolbar-actions,
  .table-toolbar-actions button {
    width: 100%;
  }
}

@media (max-width: 560px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>

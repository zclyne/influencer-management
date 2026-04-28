<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()
const campaignId = computed(() => String(route.params.campaignId ?? ''))

const columns = [
  {
    title: 'Influencer',
    key: 'influencer',
  },
  {
    title: 'Status',
    key: 'status',
  },
  {
    title: 'Deliverables',
    key: 'deliverables',
  },
  {
    title: 'Compensation',
    key: 'compensation',
  },
  {
    title: 'Updated',
    key: 'updated',
  },
]
</script>

<template>
  <section class="workspace-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">Campaign workspace</p>
        <h1>Campaign {{ campaignId }}</h1>
        <p class="page-description">
          Manage campaign deals, add influencers from the library, and export the current campaign view.
        </p>
      </div>
      <div class="workspace-actions">
        <RouterLink to="/influencers">
          <a-button>Add from library</a-button>
        </RouterLink>
        <a-button disabled>Export view</a-button>
      </div>
    </div>

    <a-card :body-style="{ padding: '0' }">
      <a-table
        :columns="columns"
        :data-source="[]"
        :pagination="false"
        row-key="id"
      >
        <template #emptyText>
          <a-empty description="Campaign deals will load here." />
        </template>
      </a-table>
    </a-card>
  </section>
</template>

<style scoped>
.workspace-page {
  display: grid;
  gap: 18px;
}

.page-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #5e6974;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
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

.workspace-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 760px) {
  .page-heading {
    display: grid;
  }

  .workspace-actions {
    justify-content: stretch;
  }

  .workspace-actions a,
  .workspace-actions button {
    width: 100%;
  }
}
</style>

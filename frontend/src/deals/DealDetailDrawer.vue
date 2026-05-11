<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { DealPipelineRow, DealStatus, PrimaryPlatformSummary } from '../api/types'
import { dealStatusLabels } from '../campaigns/useCampaignWorkspace'
import { platformColor } from '../influencers/useInfluencers'

const props = defineProps<{
  open: boolean
  campaignName?: string
  deal: DealPipelineRow | null
}>()

defineEmits<{
  close: []
}>()

const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return null
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(
    value,
  )
}

const platformLabel = (platform: PrimaryPlatformSummary) => {
  const name = platform.platform
  const username = platform.username ? ` @${platform.username}` : ''
  const followers = formatNumber(platform.follower_count)
  return `${name}${username}${followers ? ` · ${followers}` : ''}`
}

const locationLabel = () => {
  if (!props.deal) return 'Not set'
  return [props.deal.influencer.city, props.deal.influencer.country].filter(Boolean).join(', ') || 'Not set'
}

const statusColor = (status: DealStatus) => {
  if (status === 'ACTIVE') return 'green'
  if (status === 'COMPLETED') return 'blue'
  if (status === 'LOST') return 'red'
  return 'default'
}
</script>

<template>
  <a-drawer
    :open="open"
    width="520"
    placement="right"
    title="Deal review"
    destroy-on-close
    @close="$emit('close')"
  >
    <a-empty v-if="!deal" description="Select a deal to review." />

    <div v-else class="drawer-content">
      <section class="profile-block">
        <h2>{{ deal.influencer.display_name }}</h2>
        <p>{{ locationLabel() }}</p>
        <div v-if="deal.platforms.length" class="tag-row">
          <a-tag
            v-for="platform in deal.platforms"
            :key="`${platform.platform}:${platform.username}`"
            :color="platformColor(platform.platform)"
          >
            {{ platformLabel(platform) }}
          </a-tag>
        </div>
        <span v-else class="muted">No platforms</span>
      </section>

      <a-descriptions bordered size="small" :column="1">
        <a-descriptions-item label="Status">
          <a-tag :color="statusColor(deal.status)">{{ dealStatusLabels[deal.status] }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="Primary contact">
          <span v-if="deal.primary_contact">{{ deal.primary_contact.email }}</span>
          <span v-else class="muted">No contact</span>
        </a-descriptions-item>
        <a-descriptions-item label="Deliverables">
          {{ deal.deliverables.label ?? 'No deliverables' }}
        </a-descriptions-item>
        <a-descriptions-item label="Compensation">
          {{ deal.compensation.label ?? 'No compensation items' }}
        </a-descriptions-item>
        <a-descriptions-item label="Labels">
          <div v-if="deal.labels.length" class="tag-row">
            <a-tag v-for="label in deal.labels" :key="label">{{ label }}</a-tag>
          </div>
          <span v-else class="muted">No labels</span>
        </a-descriptions-item>
      </a-descriptions>

      <a-card v-if="deal.internal_notes" size="small" title="Internal notes">
        <p class="notes">{{ deal.internal_notes }}</p>
      </a-card>

      <div class="drawer-actions">
        <RouterLink :to="{ name: 'dealDetail', params: { campaignId: deal.campaign_id, dealId: deal.id } }">
          <a-button type="primary" block>Open deal detail</a-button>
        </RouterLink>
        <RouterLink :to="{ name: 'influencerDetail', params: { influencerId: deal.influencer.id } }">
          <a-button block>Open influencer detail</a-button>
        </RouterLink>
      </div>
    </div>
  </a-drawer>
</template>

<style scoped>
.drawer-content {
  display: grid;
  gap: 16px;
}

.profile-block {
  display: grid;
  gap: 8px;
}

h2 {
  margin: 0;
  color: #20262d;
  font-size: 24px;
}

.profile-block p,
.notes {
  margin: 0;
  color: #58636f;
  line-height: 1.5;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.muted {
  color: #697582;
}

.drawer-actions {
  display: grid;
  gap: 10px;
}
</style>

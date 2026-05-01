import { computed, ref, watch } from 'vue'
import { archiveCampaign as archiveCampaignRequest, createCampaign, errorMessage, listCampaigns } from '../api/client'
import type { CampaignCreateRequest, CampaignResponse, CampaignStatus } from '../api/types'

export const campaignStatuses: CampaignStatus[] = ['PLANNING', 'ACTIVE', 'EVALUATING', 'CLOSED']

export const campaignStatusLabels: Record<CampaignStatus, string> = {
  PLANNING: 'Planning',
  ACTIVE: 'Active',
  EVALUATING: 'Evaluating',
  CLOSED: 'Closed',
}

export const useCampaigns = () => {
  const campaigns = ref<CampaignResponse[]>([])
  const loading = ref(false)
  const creating = ref(false)
  const archiving = ref(false)
  const error = ref<string | null>(null)
  const searchText = ref('')
  const statusFilter = ref<CampaignStatus | undefined>()
  const includeArchived = ref(false)
  const selectedRowKeys = ref<string[]>([])

  const loadCampaigns = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await listCampaigns({
        status: statusFilter.value,
        includeArchived: includeArchived.value,
      })
      campaigns.value = response.campaigns
    } catch (loadError) {
      error.value = errorMessage(loadError)
    } finally {
      loading.value = false
    }
  }

  const visibleCampaigns = computed(() => {
    const query = searchText.value.trim().toLowerCase()
    if (!query) return campaigns.value

    return campaigns.value.filter((campaign) => {
      const brandNames = campaign.brands.map((link) => link.brand.name).join(' ')
      return `${campaign.name} ${brandNames} ${campaign.status}`.toLowerCase().includes(query)
    })
  })

  const activeCampaignCount = computed(
    () => campaigns.value.filter((campaign) => !campaign.archived_at).length,
  )

  const planningCampaignCount = computed(
    () =>
      campaigns.value.filter(
        (campaign) => !campaign.archived_at && campaign.status === 'PLANNING',
      ).length,
  )

  const liveCampaignCount = computed(
    () =>
      campaigns.value.filter((campaign) => !campaign.archived_at && campaign.status === 'ACTIVE')
        .length,
  )

  const archivedCampaignCount = computed(
    () => campaigns.value.filter((campaign) => campaign.archived_at).length,
  )

  const createNewCampaign = async (payload: CampaignCreateRequest) => {
    creating.value = true
    error.value = null

    try {
      const created = await createCampaign(payload)
      await loadCampaigns()
      return created
    } catch (createError) {
      error.value = errorMessage(createError)
      throw createError
    } finally {
      creating.value = false
    }
  }

  const archiveCampaign = async (campaignId: string) => {
    archiving.value = true
    error.value = null

    try {
      await archiveCampaignRequest(campaignId)
      selectedRowKeys.value = selectedRowKeys.value.filter((key) => key !== campaignId)
      await loadCampaigns()
    } catch (archiveError) {
      error.value = errorMessage(archiveError)
      throw archiveError
    } finally {
      archiving.value = false
    }
  }

  const archiveSelectedCampaigns = async () => {
    const campaignIds = [...selectedRowKeys.value]
    if (!campaignIds.length) return { archived: 0, failed: 0 }

    archiving.value = true
    error.value = null

    try {
      const results = await Promise.allSettled(
        campaignIds.map((campaignId) => archiveCampaignRequest(campaignId)),
      )
      const failed = results.filter((result) => result.status === 'rejected').length
      const archived = results.length - failed

      if (failed > 0) {
        error.value = `${failed} campaign(s) could not be deleted.`
      }

      selectedRowKeys.value = campaignIds.filter((_, index) => results[index]?.status === 'rejected')
      await loadCampaigns()
      return { archived, failed }
    } finally {
      archiving.value = false
    }
  }

  watch([statusFilter, includeArchived], () => {
    selectedRowKeys.value = []
    void loadCampaigns()
  })

  watch(campaigns, (nextCampaigns) => {
    const availableIds = new Set(nextCampaigns.map((campaign) => campaign.id))
    selectedRowKeys.value = selectedRowKeys.value.filter((key) => availableIds.has(key))
  })

  return {
    campaigns,
    visibleCampaigns,
    loading,
    creating,
    archiving,
    error,
    searchText,
    statusFilter,
    includeArchived,
    selectedRowKeys,
    activeCampaignCount,
    planningCampaignCount,
    liveCampaignCount,
    archivedCampaignCount,
    loadCampaigns,
    createNewCampaign,
    archiveCampaign,
    archiveSelectedCampaigns,
  }
}

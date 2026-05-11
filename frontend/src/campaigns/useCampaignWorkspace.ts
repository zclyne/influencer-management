import { computed, ref, watch } from 'vue'
import {
  archiveCampaign as archiveCampaignRequest,
  archiveDeal as archiveDealRequest,
  bulkCreateCampaignDeals,
  bulkUpdateCampaignDeals,
  errorMessage,
  exportCampaignCsv,
  getCampaign,
  listCampaignDeals,
  updateCampaign,
} from '../api/client'
import type {
  CampaignResponse,
  CampaignUpdateRequest,
  DealBulkUpdateRequest,
  DealPipelineRow,
  DealStatus,
} from '../api/types'

export const dealStatuses: DealStatus[] = ['DRAFT', 'ACTIVE', 'COMPLETED', 'LOST']

export const dealStatusLabels: Record<DealStatus, string> = {
  DRAFT: 'Draft',
  ACTIVE: 'Active',
  COMPLETED: 'Completed',
  LOST: 'Lost',
}

const parseMoney = (value: string | number) => {
  const amount = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(amount) ? amount : 0
}

interface CampaignInfluencerDeal {
  dealId: string
  status: DealStatus
  archivedAt?: string | null
}

export const useCampaignWorkspace = (campaignId: () => string) => {
  const campaign = ref<CampaignResponse | null>(null)
  const deals = ref<DealPipelineRow[]>([])
  const campaignInfluencerDeals = ref<Record<string, CampaignInfluencerDeal>>({})
  const loading = ref(false)
  const mutating = ref(false)
  const exporting = ref(false)
  const error = ref<string | null>(null)
  const searchText = ref('')
  const statusFilter = ref<DealStatus | undefined>()
  const platformFilter = ref<string | undefined>()
  const includeArchived = ref(false)
  const selectedRowKeys = ref<string[]>([])
  const selectedDeal = ref<DealPipelineRow | null>(null)

  const loadWorkspace = async () => {
    const id = campaignId()
    if (!id) return

    loading.value = true
    error.value = null

    try {
      const [campaignResponse, dealsResponse] = await Promise.all([
        getCampaign(id),
        listCampaignDeals(id, {
          status: statusFilter.value,
          platform: platformFilter.value,
          includeArchived: includeArchived.value,
          sort: '-updated_at',
        }),
      ])
      campaign.value = campaignResponse
      deals.value = dealsResponse.deals
    } catch (loadError) {
      error.value = errorMessage(loadError)
    } finally {
      loading.value = false
    }
  }

  const loadCampaignInfluencerMembership = async () => {
    const id = campaignId()
    if (!id) return

    const response = await listCampaignDeals(id, {
      includeArchived: true,
      sort: '-updated_at',
    })
    campaignInfluencerDeals.value = Object.fromEntries(
      response.deals.map((deal) => [
        deal.influencer.id,
        {
          dealId: deal.id,
          status: deal.status,
          archivedAt: deal.archived_at ?? null,
        },
      ]),
    )
  }

  const visibleDeals = computed(() => {
    const query = searchText.value.trim().toLowerCase()
    if (!query) return deals.value

    return deals.value.filter((deal) => {
      const platformText = deal.platforms
        .map((platform) => `${platform.platform} ${platform.username ?? ''}`)
        .join(' ')
      return [
        deal.influencer.display_name,
        deal.primary_contact?.email,
        deal.status,
        deal.deliverables.label,
        deal.compensation.label,
        platformText,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
        .includes(query)
    })
  })

  const activeDeals = computed(() => deals.value.filter((deal) => !deal.archived_at))

  const totalDealCount = computed(() => activeDeals.value.length)

  const inProgressDealCount = computed(
    () => activeDeals.value.filter((deal) => deal.status === 'ACTIVE').length,
  )

  const pendingReviewCount = computed(() => 0)

  const plannedSpend = computed(() =>
    activeDeals.value.reduce((sum, deal) => {
      const usdCash = deal.compensation.cash_totals.USD
      const usdReimbursement = deal.compensation.reimbursement_totals.USD
      return (
        sum +
        (usdCash === undefined ? 0 : parseMoney(usdCash)) +
        (usdReimbursement === undefined ? 0 : parseMoney(usdReimbursement))
      )
    }, 0),
  )

  const platformOptions = computed(() => {
    const platforms = new Set<string>()
    deals.value.forEach((deal) => {
      deal.platforms.forEach((platform) => platforms.add(platform.platform))
    })
    return Array.from(platforms)
      .sort()
      .map((platform) => ({ label: platform, value: platform }))
  })

  const selectDeal = (deal: DealPipelineRow | null) => {
    selectedDeal.value = deal
  }

  const updateCampaignProfile = async (payload: CampaignUpdateRequest) => {
    mutating.value = true
    error.value = null

    try {
      campaign.value = await updateCampaign(campaignId(), payload)
      return campaign.value
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const archiveCampaignProfile = async () => {
    mutating.value = true
    error.value = null

    try {
      await archiveCampaignRequest(campaignId())
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const addInfluencersToCampaign = async (influencerIds: string[]) => {
    if (!influencerIds.length) return null

    mutating.value = true
    error.value = null

    try {
      const result = await bulkCreateCampaignDeals(campaignId(), {
        influencer_ids: influencerIds,
        skip_existing: true,
      })
      await loadWorkspace()
      return result
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const bulkUpdateSelectedDeals = async (payload: Omit<DealBulkUpdateRequest, 'deal_ids'>) => {
    const dealIds = [...selectedRowKeys.value]
    if (!dealIds.length) return null

    mutating.value = true
    error.value = null

    try {
      const result = await bulkUpdateCampaignDeals(campaignId(), {
        ...payload,
        deal_ids: dealIds,
      })
      selectedRowKeys.value = []
      await loadWorkspace()
      return result
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const archiveDeal = async (dealId: string) => {
    mutating.value = true
    error.value = null

    try {
      await archiveDealRequest(dealId)
      selectedRowKeys.value = selectedRowKeys.value.filter((key) => key !== dealId)
      if (selectedDeal.value?.id === dealId) selectedDeal.value = null
      await loadWorkspace()
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const archiveSelectedDeals = async () => {
    const dealIds = [...selectedRowKeys.value]
    if (!dealIds.length) return { archived: 0, failed: 0 }

    mutating.value = true
    error.value = null

    try {
      const results = await Promise.allSettled(dealIds.map((dealId) => archiveDealRequest(dealId)))
      const failed = results.filter((result) => result.status === 'rejected').length
      const archived = results.length - failed

      if (failed > 0) {
        error.value = `${failed} deal(s) could not be deleted.`
      }

      selectedRowKeys.value = dealIds.filter((_, index) => results[index]?.status === 'rejected')
      const archivedIds = new Set(
        dealIds.filter((_, index) => results[index]?.status === 'fulfilled'),
      )
      if (selectedDeal.value && archivedIds.has(selectedDeal.value.id)) {
        selectedDeal.value = null
      }
      await loadWorkspace()
      return { archived, failed }
    } finally {
      mutating.value = false
    }
  }

  const exportCurrentView = async () => {
    exporting.value = true
    error.value = null

    try {
      return await exportCampaignCsv(campaignId(), {
        status: statusFilter.value,
        platform: platformFilter.value,
        includeArchived: includeArchived.value,
      })
    } catch (exportError) {
      error.value = errorMessage(exportError)
      throw exportError
    } finally {
      exporting.value = false
    }
  }

  watch([statusFilter, platformFilter, includeArchived], () => {
    selectedRowKeys.value = []
    void loadWorkspace()
  })

  watch(deals, (nextDeals) => {
    const availableIds = new Set(nextDeals.map((deal) => deal.id))
    selectedRowKeys.value = selectedRowKeys.value.filter((key) => availableIds.has(key))
    if (selectedDeal.value && !availableIds.has(selectedDeal.value.id)) {
      selectedDeal.value = null
    }
  })

  return {
    campaign,
    deals,
    campaignInfluencerDeals,
    visibleDeals,
    loading,
    mutating,
    exporting,
    error,
    searchText,
    statusFilter,
    platformFilter,
    includeArchived,
    selectedRowKeys,
    selectedDeal,
    totalDealCount,
    inProgressDealCount,
    pendingReviewCount,
    plannedSpend,
    platformOptions,
    loadWorkspace,
    loadCampaignInfluencerMembership,
    selectDeal,
    updateCampaignProfile,
    archiveCampaignProfile,
    addInfluencersToCampaign,
    bulkUpdateSelectedDeals,
    archiveDeal,
    archiveSelectedDeals,
    exportCurrentView,
  }
}

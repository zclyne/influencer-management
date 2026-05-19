import { computed, ref } from 'vue'
import {
  createDealCompensationItem,
  createDealDeliverable,
  deleteDealAttachment,
  deleteDealCompensationItem,
  deleteDealDeliverable,
  errorMessage,
  fileDownloadUrl,
  getCampaign,
  getDeal,
  listDealAttachments,
  listDealCompensationItems,
  listDealDeliverables,
  uploadDealAttachment,
  updateDeal,
  updateDealCompensationItem,
  updateDealDeliverable,
  archiveDeal,
} from '../api/client'
import type {
  CampaignResponse,
  CompensationItemCreateRequest,
  CompensationItemResponse,
  CompensationItemUpdateRequest,
  DealAttachmentResponse,
  DealDetailResponse,
  DealUpdateRequest,
  DeliverableCreateRequest,
  DeliverableResponse,
  DeliverableUpdateRequest,
} from '../api/types'

export const useDealDetail = (dealId: () => string, campaignId: () => string) => {
  const campaign = ref<CampaignResponse | null>(null)
  const deal = ref<DealDetailResponse | null>(null)
  const attachments = ref<DealAttachmentResponse[]>([])
  const deliverables = ref<DeliverableResponse[]>([])
  const compensationItems = ref<CompensationItemResponse[]>([])
  const loading = ref(false)
  const mutating = ref(false)
  const error = ref<string | null>(null)

  const loadDealDetail = async () => {
    const currentDealId = dealId()
    const currentCampaignId = campaignId()
    if (!currentDealId || !currentCampaignId) return

    loading.value = true
    error.value = null

    try {
      const [campaignResponse, dealResponse, deliverablesResponse, compensationResponse] =
        await Promise.all([
          getCampaign(currentCampaignId),
          getDeal(currentDealId),
          listDealDeliverables(currentDealId),
          listDealCompensationItems(currentDealId),
        ])
      campaign.value = campaignResponse
      deal.value = dealResponse
      deliverables.value = deliverablesResponse.deliverables
      compensationItems.value = compensationResponse.compensation_items

      try {
        const attachmentsResponse = await listDealAttachments(currentDealId)
        attachments.value = attachmentsResponse.attachments
      } catch (attachmentError) {
        attachments.value = []
        error.value = `Deal loaded, but attachments could not be loaded. ${errorMessage(attachmentError)}`
      }
    } catch (loadError) {
      error.value = errorMessage(loadError)
    } finally {
      loading.value = false
    }
  }

  const refreshDeal = async () => {
    const currentDealId = dealId()
    if (!currentDealId) return
    deal.value = await getDeal(currentDealId)
  }

  const refreshDeliverables = async () => {
    const currentDealId = dealId()
    if (!currentDealId) return
    const response = await listDealDeliverables(currentDealId)
    deliverables.value = response.deliverables
  }

  const refreshAttachments = async () => {
    const currentDealId = dealId()
    if (!currentDealId) return
    const response = await listDealAttachments(currentDealId)
    attachments.value = response.attachments
  }

  const refreshCompensationItems = async () => {
    const currentDealId = dealId()
    if (!currentDealId) return
    const response = await listDealCompensationItems(currentDealId)
    compensationItems.value = response.compensation_items
  }

  const updateDealDetail = async (payload: DealUpdateRequest) => {
    mutating.value = true
    error.value = null

    try {
      deal.value = await updateDeal(dealId(), payload)
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const createDeliverable = async (payload: DeliverableCreateRequest) => {
    mutating.value = true
    error.value = null

    try {
      await createDealDeliverable(dealId(), payload)
      await Promise.all([refreshDeliverables(), refreshDeal()])
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const uploadAttachment = async (file: File) => {
    mutating.value = true
    error.value = null

    try {
      await uploadDealAttachment(dealId(), file)
      await refreshAttachments()
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const deleteAttachment = async (attachmentId: string) => {
    mutating.value = true
    error.value = null

    try {
      await deleteDealAttachment(dealId(), attachmentId)
      await refreshAttachments()
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const attachmentDownloadUrl = (fileId: string) => fileDownloadUrl(fileId)

  const updateDeliverable = async (
    deliverableId: string,
    payload: DeliverableUpdateRequest,
  ) => {
    mutating.value = true
    error.value = null

    try {
      await updateDealDeliverable(dealId(), deliverableId, payload)
      await Promise.all([refreshDeliverables(), refreshDeal()])
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const deleteDeliverable = async (deliverableId: string) => {
    mutating.value = true
    error.value = null

    try {
      await deleteDealDeliverable(dealId(), deliverableId)
      await Promise.all([refreshDeliverables(), refreshDeal()])
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const createCompensationItem = async (payload: CompensationItemCreateRequest) => {
    mutating.value = true
    error.value = null

    try {
      await createDealCompensationItem(dealId(), payload)
      await Promise.all([refreshCompensationItems(), refreshDeal()])
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const updateCompensationItem = async (
    itemId: string,
    payload: CompensationItemUpdateRequest,
  ) => {
    mutating.value = true
    error.value = null

    try {
      await updateDealCompensationItem(dealId(), itemId, payload)
      await Promise.all([refreshCompensationItems(), refreshDeal()])
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const deleteCompensationItem = async (itemId: string) => {
    mutating.value = true
    error.value = null

    try {
      await deleteDealCompensationItem(dealId(), itemId)
      await Promise.all([refreshCompensationItems(), refreshDeal()])
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const archiveProfile = async () => {
    mutating.value = true
    error.value = null

    try {
      await archiveDeal(dealId())
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const campaignName = computed(() => campaign.value?.name ?? 'Campaign')
  const influencerName = computed(() => deal.value?.influencer.display_name ?? 'Deal')

  return {
    campaign,
    deal,
    attachments,
    deliverables,
    compensationItems,
    loading,
    mutating,
    error,
    campaignName,
    influencerName,
    loadDealDetail,
    updateDealDetail,
    uploadAttachment,
    deleteAttachment,
    attachmentDownloadUrl,
    createDeliverable,
    updateDeliverable,
    deleteDeliverable,
    createCompensationItem,
    updateCompensationItem,
    deleteCompensationItem,
    archiveProfile,
  }
}

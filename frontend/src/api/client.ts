import type {
  ApiErrorResponse,
  BrandCreateRequest,
  BrandListResponse,
  BrandResponse,
  BrandUpdateRequest,
  CampaignCreateRequest,
  CampaignAttachmentListResponse,
  CampaignAttachmentResponse,
  CampaignListResponse,
  CampaignResponse,
  CampaignStatus,
  CampaignUpdateRequest,
  DealBulkCreateRequest,
  DealBulkCreateResponse,
  DealBulkUpdateRequest,
  DealBulkUpdateResponse,
  DealAttachmentListResponse,
  DealAttachmentResponse,
  DealDetailResponse,
  DealListResponse,
  DealStatus,
  DealUpdateRequest,
  DeliverableCreateRequest,
  DeliverableListResponse,
  DeliverableResponse,
  DeliverableUpdateRequest,
  EmailThreadLinkRequest,
  EmailThreadLinkResponse,
  EmailDraftSendResponse,
  EmailParticipant,
  EmailReplyDraftResponse,
  EmailReplyMode,
  GmailAuthStartResponse,
  GmailAuthStatusResponse,
  GmailLabelListResponse,
  EmailThreadBatchAction,
  EmailThreadBatchResponse,
  GmailThreadDetailResponse,
  GmailThreadListResponse,
  CompensationItemCreateRequest,
  CompensationItemListResponse,
  CompensationItemResponse,
  CompensationItemUpdateRequest,
  InfluencerContactCreateRequest,
  InfluencerContactResponse,
  InfluencerContactUpdateRequest,
  InfluencerDealListResponse,
  InfluencerListResponse,
  InfluencerPlatformCreateRequest,
  InfluencerPlatformResponse,
  InfluencerPlatformUpdateRequest,
  InfluencerResponse,
  InfluencerUpdateRequest,
  IngestionConfirmRequest,
  IngestionConfirmResponse,
  IngestionPreviewResponse,
  ManualInfluencerInput,
  ManualInfluencerResponse,
} from './types'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const apiBaseUrl = configuredBaseUrl.replace(/\/$/, '')
export const apiRoot = `${apiBaseUrl}/api/v1`

export class ApiError extends Error {
  status: number
  payload: ApiErrorResponse

  constructor(status: number, payload: ApiErrorResponse) {
    super(payload.message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

export class NetworkError extends Error {
  url: string
  cause: unknown

  constructor(url: string, cause: unknown) {
    super(
      `Could not reach the CreatorFlow API at ${url}. Check that the backend is running, ` +
        `VITE_API_BASE_URL is correct, and the browser can access the API origin.`,
    )
    this.name = 'NetworkError'
    this.url = url
    this.cause = cause
  }
}

const fallbackError = (status: number, message: string): ApiErrorResponse => ({
  code: status >= 500 ? 'server_error' : 'request_error',
  message,
  details: {},
  request_id: null,
})

const parseError = async (response: Response): Promise<ApiErrorResponse> => {
  try {
    const payload = (await response.json()) as Partial<ApiErrorResponse>
    return {
      code: payload.code ?? 'request_error',
      message: payload.message ?? response.statusText,
      details: payload.details ?? {},
      request_id: payload.request_id ?? null,
    }
  } catch {
    return fallbackError(response.status, response.statusText || 'Request failed')
  }
}

const toQueryString = (params: Record<string, string | boolean | undefined>) => {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) query.set(key, String(value))
  })
  const queryString = query.toString()
  return queryString ? `?${queryString}` : ''
}

const stringifyDetails = (details: Record<string, unknown> | null | undefined) => {
  if (!details || Object.keys(details).length === 0) return null

  try {
    return JSON.stringify(details)
  } catch {
    return String(details)
  }
}

export const errorMessage = (error: unknown) => {
  if (error instanceof ApiError) {
    const parts = [`HTTP ${error.status}`, `code: ${error.payload.code}`]
    if (error.payload.message) parts.push(`message: ${error.payload.message}`)

    const details = stringifyDetails(error.payload.details)
    if (details) parts.push(`details: ${details}`)
    if (error.payload.request_id) parts.push(`request id: ${error.payload.request_id}`)

    return parts.join(' | ')
  }

  if (error instanceof NetworkError) {
    const causeMessage = error.cause instanceof Error ? error.cause.message : null
    return causeMessage ? `${error.message} Browser error: ${causeMessage}.` : error.message
  }

  if (error instanceof Error) return error.message
  return 'Unexpected error'
}

export const apiRequest = async <T>(path: string, init: RequestInit = {}): Promise<T> => {
  const headers = new Headers(init.headers)
  const body = init.body

  if (body !== undefined && !(body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const url = `${apiRoot}${path}`
  let response: Response
  try {
    response = await fetch(url, {
      ...init,
      headers,
    })
  } catch (requestError) {
    throw new NetworkError(url, requestError)
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response))
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const listCampaigns = (
  options: { status?: CampaignStatus; tag?: string; includeArchived?: boolean } = {},
) =>
  apiRequest<CampaignListResponse>(
    `/campaigns${toQueryString({
      status: options.status,
      tag: options.tag,
      include_archived: options.includeArchived,
    })}`,
  )

export const createCampaign = (payload: CampaignCreateRequest) =>
  apiRequest<CampaignResponse>('/campaigns', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const getCampaign = (campaignId: string) =>
  apiRequest<CampaignResponse>(`/campaigns/${campaignId}`)

export const updateCampaign = (campaignId: string, payload: CampaignUpdateRequest) =>
  apiRequest<CampaignResponse>(`/campaigns/${campaignId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const archiveCampaign = (campaignId: string) =>
  apiRequest<void>(`/campaigns/${campaignId}`, {
    method: 'DELETE',
  })

export const listCampaignDeals = (
  campaignId: string,
  options: {
    status?: DealStatus
    platform?: string
    lostReason?: string
    includeArchived?: boolean
    sort?: string
  } = {},
) =>
  apiRequest<DealListResponse>(
    `/campaigns/${campaignId}/deals${toQueryString({
      status: options.status,
      platform: options.platform,
      lost_reason: options.lostReason,
      include_archived: options.includeArchived,
      sort: options.sort,
    })}`,
  )

export const bulkCreateCampaignDeals = (campaignId: string, payload: DealBulkCreateRequest) =>
  apiRequest<DealBulkCreateResponse>(`/campaigns/${campaignId}/deals/bulk`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const bulkUpdateCampaignDeals = (campaignId: string, payload: DealBulkUpdateRequest) =>
  apiRequest<DealBulkUpdateResponse>(`/campaigns/${campaignId}/deals/bulk`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const getDeal = (dealId: string) => apiRequest<DealDetailResponse>(`/deals/${dealId}`)

export const updateDeal = (dealId: string, payload: DealUpdateRequest) =>
  apiRequest<DealDetailResponse>(`/deals/${dealId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const archiveDeal = (dealId: string) =>
  apiRequest<void>(`/deals/${dealId}`, {
    method: 'DELETE',
  })

export const listCampaignAttachments = (campaignId: string) =>
  apiRequest<CampaignAttachmentListResponse>(`/campaigns/${campaignId}/attachments`)

export const uploadCampaignAttachment = (campaignId: string, file: File) => {
  const body = new FormData()
  body.append('file', file)

  return apiRequest<CampaignAttachmentResponse>(`/campaigns/${campaignId}/attachments`, {
    method: 'POST',
    body,
  })
}

export const deleteCampaignAttachment = (campaignId: string, attachmentId: string) =>
  apiRequest<void>(`/campaigns/${campaignId}/attachments/${attachmentId}`, {
    method: 'DELETE',
  })

export const listDealAttachments = (dealId: string) =>
  apiRequest<DealAttachmentListResponse>(`/deals/${dealId}/attachments`)

export const uploadDealAttachment = (dealId: string, file: File) => {
  const body = new FormData()
  body.append('file', file)

  return apiRequest<DealAttachmentResponse>(`/deals/${dealId}/attachments`, {
    method: 'POST',
    body,
  })
}

export const deleteDealAttachment = (dealId: string, attachmentId: string) =>
  apiRequest<void>(`/deals/${dealId}/attachments/${attachmentId}`, {
    method: 'DELETE',
  })

export const fileDownloadUrl = (fileId: string) =>
  `${apiRoot}/files/${encodeURIComponent(fileId)}/download`

export const listDealDeliverables = (dealId: string) =>
  apiRequest<DeliverableListResponse>(`/deals/${dealId}/deliverables`)

export const createDealDeliverable = (dealId: string, payload: DeliverableCreateRequest) =>
  apiRequest<DeliverableResponse>(`/deals/${dealId}/deliverables`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const updateDealDeliverable = (
  dealId: string,
  deliverableId: string,
  payload: DeliverableUpdateRequest,
) =>
  apiRequest<DeliverableResponse>(`/deals/${dealId}/deliverables/${deliverableId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const deleteDealDeliverable = (dealId: string, deliverableId: string) =>
  apiRequest<void>(`/deals/${dealId}/deliverables/${deliverableId}`, {
    method: 'DELETE',
  })

export const listDealCompensationItems = (dealId: string) =>
  apiRequest<CompensationItemListResponse>(`/deals/${dealId}/compensation-items`)

export const createDealCompensationItem = (
  dealId: string,
  payload: CompensationItemCreateRequest,
) =>
  apiRequest<CompensationItemResponse>(`/deals/${dealId}/compensation-items`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const updateDealCompensationItem = (
  dealId: string,
  itemId: string,
  payload: CompensationItemUpdateRequest,
) =>
  apiRequest<CompensationItemResponse>(`/deals/${dealId}/compensation-items/${itemId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const deleteDealCompensationItem = (dealId: string, itemId: string) =>
  apiRequest<void>(`/deals/${dealId}/compensation-items/${itemId}`, {
    method: 'DELETE',
  })

export const getEmailAuthStatus = () =>
  apiRequest<GmailAuthStatusResponse>('/email/auth/status')

export const startEmailAuth = () =>
  apiRequest<GmailAuthStartResponse>('/email/auth/start', {
    method: 'POST',
  })

export const disconnectEmail = () =>
  apiRequest<void>('/email/auth/disconnect', {
    method: 'POST',
  })

export const listEmailLabels = () => apiRequest<GmailLabelListResponse>('/email/labels')

export const listEmailThreads = (
  options: {
    campaignId?: string
    dealId?: string
    query?: string
    label?: string
    view?: string
    pageToken?: string
    pageSize?: number
  } = {},
) =>
  apiRequest<GmailThreadListResponse>(
    `/email/threads${toQueryString({
      campaign_id: options.campaignId,
      deal_id: options.dealId,
      q: options.query,
      label: options.label,
      view: options.view,
      page_token: options.pageToken,
      page_size: options.pageSize === undefined ? undefined : String(options.pageSize),
    })}`,
  )

export const batchEmailThreads = (payload: {
  thread_ids: string[]
  action: EmailThreadBatchAction
}) =>
  apiRequest<EmailThreadBatchResponse>('/email/threads/batch', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const getEmailThread = (
  threadId: string,
  options: {
    markRead?: boolean
  } = {},
) =>
  apiRequest<GmailThreadDetailResponse>(
    `/email/threads/${threadId}${toQueryString({
      mark_read: options.markRead === undefined ? undefined : String(options.markRead),
    })}`,
  )

export const linkEmailThread = (threadId: string, payload: EmailThreadLinkRequest) =>
  apiRequest<EmailThreadLinkResponse>(`/email/threads/${threadId}/links`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const unlinkEmailThread = (
  threadId: string,
  options: {
    campaignId?: string
    dealId?: string
  },
) =>
  apiRequest<EmailThreadLinkResponse>(
    `/email/threads/${threadId}/links${toQueryString({
      campaign_id: options.campaignId,
      deal_id: options.dealId,
    })}`,
    {
      method: 'DELETE',
    },
  )

export const saveEmailReplyDraft = (
  threadId: string,
  payload: {
    draftId?: string | null
    replyMode: EmailReplyMode
    anchorMessageId?: string | null
    to: EmailParticipant[]
    cc: EmailParticipant[]
    bcc: EmailParticipant[]
    subject?: string | null
    bodyHtml?: string | null
    bodyText?: string | null
    inlineImages?: { cid: string; file: File }[]
    attachments?: File[]
  },
) => {
  const body = new FormData()
  if (payload.draftId) body.append('draft_id', payload.draftId)
  body.append('reply_mode', payload.replyMode)
  if (payload.anchorMessageId) body.append('anchor_message_id', payload.anchorMessageId)
  body.append('to', JSON.stringify(payload.to))
  body.append('cc', JSON.stringify(payload.cc))
  body.append('bcc', JSON.stringify(payload.bcc))
  if (payload.subject !== undefined && payload.subject !== null) body.append('subject', payload.subject)
  if (payload.bodyHtml !== undefined && payload.bodyHtml !== null) body.append('body_html', payload.bodyHtml)
  if (payload.bodyText !== undefined && payload.bodyText !== null) body.append('body_text', payload.bodyText)
  ;(payload.inlineImages ?? []).forEach((image) => {
    body.append('inline_image_cids', image.cid)
    body.append('inline_images', image.file)
  })
  ;(payload.attachments ?? []).forEach((file) => body.append('attachments', file))

  return apiRequest<EmailReplyDraftResponse>(`/email/threads/${threadId}/draft-replies`, {
    method: 'POST',
    body,
  })
}

export const sendEmailDraft = (draftId: string) =>
  apiRequest<EmailDraftSendResponse>(`/email/drafts/${draftId}/send`, {
    method: 'POST',
  })

export const deleteEmailDraft = (draftId: string) =>
  apiRequest<void>(`/email/drafts/${draftId}`, {
    method: 'DELETE',
  })

export const exportCampaignCsv = async (
  campaignId: string,
  options: {
    status?: DealStatus
    platform?: string
    lostReason?: string
    includeArchived?: boolean
  } = {},
) => {
  const response = await fetch(
    `${apiRoot}/campaigns/${campaignId}/export.csv${toQueryString({
      status: options.status,
      platform: options.platform,
      lost_reason: options.lostReason,
      include_archived: options.includeArchived,
    })}`,
  )

  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response))
  }

  return response.blob()
}

export const listBrands = (options: { query?: string; includeArchived?: boolean } = {}) =>
  apiRequest<BrandListResponse>(
    `/brands${toQueryString({
      query: options.query,
      include_archived: options.includeArchived,
    })}`,
  )

export const createBrand = (payload: BrandCreateRequest) =>
  apiRequest<BrandResponse>('/brands', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const updateBrand = (brandId: string, payload: BrandUpdateRequest) =>
  apiRequest<BrandResponse>(`/brands/${brandId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const archiveBrand = (brandId: string) =>
  apiRequest<void>(`/brands/${brandId}`, {
    method: 'DELETE',
  })

export const listInfluencers = (
  options: {
    query?: string
    platform?: string
    country?: string
    city?: string
    tag?: string
    includeArchived?: boolean
  } = {},
) =>
  apiRequest<InfluencerListResponse>(
    `/influencers${toQueryString({
      query: options.query,
      platform: options.platform,
      country: options.country,
      city: options.city,
      tag: options.tag,
      include_archived: options.includeArchived,
    })}`,
  )

export const archiveInfluencer = (influencerId: string) =>
  apiRequest<void>(`/influencers/${influencerId}`, {
    method: 'DELETE',
  })

export const getInfluencer = (influencerId: string) =>
  apiRequest<InfluencerResponse>(`/influencers/${influencerId}`)

export const updateInfluencer = (influencerId: string, payload: InfluencerUpdateRequest) =>
  apiRequest<InfluencerResponse>(`/influencers/${influencerId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const createInfluencerPlatform = (
  influencerId: string,
  payload: InfluencerPlatformCreateRequest,
) =>
  apiRequest<InfluencerPlatformResponse>(`/influencers/${influencerId}/platforms`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const updateInfluencerPlatform = (
  influencerId: string,
  platformId: string,
  payload: InfluencerPlatformUpdateRequest,
) =>
  apiRequest<InfluencerPlatformResponse>(`/influencers/${influencerId}/platforms/${platformId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const deleteInfluencerPlatform = (influencerId: string, platformId: string) =>
  apiRequest<void>(`/influencers/${influencerId}/platforms/${platformId}`, {
    method: 'DELETE',
  })

export const createInfluencerContact = (
  influencerId: string,
  payload: InfluencerContactCreateRequest,
) =>
  apiRequest<InfluencerContactResponse>(`/influencers/${influencerId}/contacts`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const updateInfluencerContact = (
  influencerId: string,
  contactId: string,
  payload: InfluencerContactUpdateRequest,
) =>
  apiRequest<InfluencerContactResponse>(`/influencers/${influencerId}/contacts/${contactId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })

export const deleteInfluencerContact = (influencerId: string, contactId: string) =>
  apiRequest<void>(`/influencers/${influencerId}/contacts/${contactId}`, {
    method: 'DELETE',
  })

export const listInfluencerDeals = (influencerId: string) =>
  apiRequest<InfluencerDealListResponse>(`/influencers/${influencerId}/deals`)

export const createManualInfluencer = (payload: ManualInfluencerInput, mergeIfMatched = false) =>
  apiRequest<ManualInfluencerResponse>(
    `/influencers/manual${toQueryString({ merge_if_matched: mergeIfMatched })}`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  )

export const previewModashImport = (file: File) => {
  const body = new FormData()
  body.append('file', file)

  return apiRequest<IngestionPreviewResponse>('/influencers/imports/modash/preview', {
    method: 'POST',
    body,
  })
}

export const confirmImport = (payload: IngestionConfirmRequest) =>
  apiRequest<IngestionConfirmResponse>('/influencers/imports/confirm', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

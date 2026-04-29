import type {
  ApiErrorResponse,
  BrandCreateRequest,
  BrandListResponse,
  BrandResponse,
  BrandUpdateRequest,
  CampaignCreateRequest,
  CampaignListResponse,
  CampaignResponse,
  CampaignStatus,
  InfluencerListResponse,
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

export const errorMessage = (error: unknown) => {
  if (error instanceof ApiError) return error.payload.message
  if (error instanceof Error) return error.message
  return 'Unexpected error'
}

export const apiRequest = async <T>(path: string, init: RequestInit = {}): Promise<T> => {
  const headers = new Headers(init.headers)
  const body = init.body

  if (body !== undefined && !(body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${apiRoot}${path}`, {
    ...init,
    headers,
  })

  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response))
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const listCampaigns = (options: { status?: CampaignStatus; includeArchived?: boolean } = {}) =>
  apiRequest<CampaignListResponse>(
    `/campaigns${toQueryString({
      status: options.status,
      include_archived: options.includeArchived,
    })}`,
  )

export const createCampaign = (payload: CampaignCreateRequest) =>
  apiRequest<CampaignResponse>('/campaigns', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

export const archiveCampaign = (campaignId: string) =>
  apiRequest<void>(`/campaigns/${campaignId}`, {
    method: 'DELETE',
  })

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
    includeArchived?: boolean
  } = {},
) =>
  apiRequest<InfluencerListResponse>(
    `/influencers${toQueryString({
      query: options.query,
      platform: options.platform,
      country: options.country,
      city: options.city,
      include_archived: options.includeArchived,
    })}`,
  )

export const archiveInfluencer = (influencerId: string) =>
  apiRequest<void>(`/influencers/${influencerId}`, {
    method: 'DELETE',
  })

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

export interface ApiErrorResponse {
  code: string
  message: string
  details?: Record<string, unknown> | null
  request_id?: string | null
}

export type CampaignStatus = 'PLANNING' | 'ACTIVE' | 'EVALUATING' | 'CLOSED'

export interface CampaignCreateRequest {
  name: string
  brief?: string | null
  budget?: string | number | null
  start_date?: string | null
  end_date?: string | null
  status?: CampaignStatus
  notes?: string | null
}

export interface CampaignResponse {
  id: string
  name: string
  brief?: string | null
  budget?: string | number | null
  start_date?: string | null
  end_date?: string | null
  status: CampaignStatus
  notes?: string | null
  created_at: string
  updated_at: string
  archived_at?: string | null
  brands: CampaignBrandResponse[]
}

export interface BrandSummary {
  id: string
  name: string
  website?: string | null
  notes?: string | null
}

export interface CampaignBrandResponse {
  id: string
  brand: BrandSummary
  role?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface CampaignListResponse {
  campaigns: CampaignResponse[]
}

export interface ManualInfluencerInput {
  display_name: string
  full_name?: string | null
  platforms?: ManualInfluencerPlatformInput[]
  country?: string | null
  city?: string | null
  bio?: string | null
  emails?: string[]
  notes?: string | null
  target_campaign_id?: string | null
}

export interface ManualInfluencerPlatformInput {
  platform: string
  username: string
  follower_count?: number | null
}

export interface ManualInfluencerResponse {
  id: string
  display_name: string
  platform_count: number
  contact_count: number
}

export interface InfluencerPlatformSummary {
  id: string
  platform: string
  username?: string | null
  profile_url?: string | null
  follower_count?: number | null
  engagement_rate?: string | number | null
  is_primary: boolean
}

export interface InfluencerPlatformResponse {
  id: string
  influencer_id: string
  platform: string
  username?: string | null
  normalized_username?: string | null
  profile_url?: string | null
  normalized_profile_url?: string | null
  follower_count?: number | null
  engagement_rate?: string | number | null
  created_at: string
  updated_at: string
}

export interface InfluencerContactResponse {
  id: string
  influencer_id: string
  name?: string | null
  email: string
  role: string
  is_primary: boolean
  source?: string | null
  notes?: string | null
  conflict_influencer_ids: string[]
  created_at: string
  updated_at: string
}

export interface InfluencerListItem {
  id: string
  display_name: string
  full_name?: string | null
  country?: string | null
  city?: string | null
  primary_platform?: InfluencerPlatformResponse | null
  platforms: InfluencerPlatformSummary[]
  follower_count?: number | null
  primary_contact?: InfluencerContactResponse | null
  recent_deal_count: number
  archived_at?: string | null
  created_at: string
  updated_at: string
}

export interface InfluencerListResponse {
  influencers: InfluencerListItem[]
}

export type ImportSourceType = 'modash_csv' | 'manual'
export type IngestionConfirmAction = 'create' | 'merge' | 'skip'
export type IngestionResultStatus =
  | 'created'
  | 'merged'
  | 'skipped'
  | 'conflict'
  | 'invalid'
  | 'failed'

export interface ContactCandidate {
  email: string
  source: string
}

export interface SocialLinkCandidate {
  platform: string
  profile_url: string
  username?: string | null
}

export interface CanonicalInfluencerRow {
  source_type: string
  source_row_number: number
  raw_row_json: Record<string, unknown>
  display_name?: string | null
  full_name?: string | null
  gender?: string | null
  country?: string | null
  city?: string | null
  bio?: string | null
  platform?: string | null
  username?: string | null
  normalized_username?: string | null
  profile_url?: string | null
  normalized_profile_url?: string | null
  follower_count?: number | null
  engagement_rate?: string | number | null
  follower_credibility?: string | number | null
  notable_follower_rate?: string | number | null
  avg_likes?: number | null
  avg_views?: number | null
  avg_comments?: number | null
  avg_reels_plays?: number | null
  total_likes?: number | null
  total_posts_or_videos?: number | null
  total_views?: number | null
  raw_metrics_json?: Record<string, unknown> | null
  age_gender_json?: Record<string, unknown> | null
  top_countries_json?: Record<string, unknown>[] | null
  top_cities_json?: Record<string, unknown>[] | null
  top_interests_json?: Record<string, unknown>[] | null
  contacts: ContactCandidate[]
  social_links: SocialLinkCandidate[]
  parse_errors: string[]
  warnings: string[]
}

export interface DedupMatch {
  status: 'high_confidence' | 'possible' | 'new' | 'invalid'
  influencer_id?: string | null
  reason?: string | null
}

export interface IngestionPreviewRow {
  row: CanonicalInfluencerRow
  status:
    | 'pending'
    | 'matched_existing'
    | 'possible_duplicate'
    | 'new'
    | 'invalid'
    | 'skipped'
    | 'imported'
  dedup: DedupMatch
}

export interface IngestionPreviewResponse {
  source_type: string
  row_count: number
  rows: IngestionPreviewRow[]
  fatal_errors: string[]
}

export interface IngestionConfirmRow {
  row: CanonicalInfluencerRow
  action: IngestionConfirmAction
  existing_influencer_id?: string | null
}

export interface IngestionConfirmRequest {
  source_type: ImportSourceType
  rows: IngestionConfirmRow[]
  file_name?: string | null
  file_hash?: string | null
  target_campaign_id?: string | null
}

export interface IngestionRowResult {
  source_row_number: number
  action: IngestionConfirmAction
  status: IngestionResultStatus
  influencer_id?: string | null
  deal_id?: string | null
  errors: string[]
  warnings: string[]
}

export interface IngestionConfirmResponse {
  import_session_id: string
  row_count: number
  imported_count: number
  skipped_count: number
  conflict_count: number
  created_deals: number
  rows: IngestionRowResult[]
}

export type DealStatus =
  | 'DRAFT'
  | 'APPROVED'
  | 'OUTREACHED'
  | 'RESPONDED'
  | 'NEGOTIATING'
  | 'ACTIVE'
  | 'COMPLETED'
  | 'LOST'

export interface WorkbenchDeal {
  id: string
  influencerName: string
  handle?: string
  status: DealStatus
  labels: string[]
  nextAction: string
  updatedAt?: string
}

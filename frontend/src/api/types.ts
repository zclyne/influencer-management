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

export interface BrandCreateRequest {
  name: string
  website?: string | null
  notes?: string | null
}

export interface BrandUpdateRequest {
  name?: string | null
  website?: string | null
  notes?: string | null
}

export interface BrandResponse {
  id: string
  name: string
  website?: string | null
  notes?: string | null
  archived_at?: string | null
  created_at: string
  updated_at: string
  campaign_count?: number | null
}

export interface BrandListResponse {
  brands: BrandResponse[]
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
  tags?: string[]
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

export type ContactRole =
  | 'creator'
  | 'manager'
  | 'agency'
  | 'assistant'
  | 'business'
  | 'unknown'

export interface InfluencerUpdateRequest {
  display_name?: string | null
  full_name?: string | null
  gender?: string | null
  country?: string | null
  city?: string | null
  bio?: string | null
  notes?: string | null
  tags?: string[] | null
}

export interface InfluencerPlatformCreateRequest {
  platform: string
  username?: string | null
  profile_url?: string | null
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
  bio?: string | null
}

export interface InfluencerPlatformUpdateRequest {
  platform?: string | null
  username?: string | null
  profile_url?: string | null
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
  bio?: string | null
}

export interface InfluencerContactCreateRequest {
  email: string
  name?: string | null
  role?: ContactRole
  is_primary?: boolean
  source?: string | null
  notes?: string | null
}

export interface InfluencerContactUpdateRequest {
  email?: string | null
  name?: string | null
  role?: ContactRole | null
  is_primary?: boolean | null
  source?: string | null
  notes?: string | null
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
  follower_credibility?: string | number | null
  notable_follower_rate?: string | number | null
  avg_likes?: number | null
  avg_views?: number | null
  avg_comments?: number | null
  avg_reels_plays?: number | null
  total_likes?: number | null
  total_posts_or_videos?: number | null
  total_views?: number | null
  bio?: string | null
  created_at: string
  updated_at: string
}

export interface InfluencerContactResponse {
  id: string
  influencer_id: string
  name?: string | null
  email: string
  role: ContactRole
  is_primary: boolean
  source?: string | null
  notes?: string | null
  conflict_influencer_ids: string[]
  created_at: string
  updated_at: string
}

export interface InfluencerDealSummary {
  id: string
  campaign_id: string
  campaign_name?: string | null
  status: string
  created_at: string
  updated_at: string
  archived_at?: string | null
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
  tags: string[]
  archived_at?: string | null
  created_at: string
  updated_at: string
}

export interface InfluencerListResponse {
  influencers: InfluencerListItem[]
}

export interface InfluencerResponse {
  id: string
  display_name: string
  full_name?: string | null
  gender?: string | null
  country?: string | null
  city?: string | null
  bio?: string | null
  notes?: string | null
  tags: string[]
  archived_at?: string | null
  created_at: string
  updated_at: string
  platforms: InfluencerPlatformResponse[]
  contacts: InfluencerContactResponse[]
  deals: InfluencerDealSummary[]
}

export interface InfluencerPlatformListResponse {
  platforms: InfluencerPlatformResponse[]
}

export interface InfluencerContactListResponse {
  contacts: InfluencerContactResponse[]
}

export interface InfluencerDealListResponse {
  deals: InfluencerDealSummary[]
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

export type DeliverableStatus =
  | 'TODO'
  | 'IN_PROGRESS'
  | 'SUBMITTED'
  | 'POSTED'
  | 'COMPLETED'
  | 'CANCELLED'

export type CompensationItemType =
  | 'CASH_STIPEND'
  | 'PRODUCT_GIFT'
  | 'SAMPLE_PRODUCT'
  | 'FLIGHT_REIMBURSEMENT'
  | 'HOTEL_REIMBURSEMENT'
  | 'LOCAL_TRANSPORT_REIMBURSEMENT'
  | 'MEAL_OR_PER_DIEM'
  | 'OTHER'

export type CompensationItemStatus =
  | 'PLANNED'
  | 'PROMISED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'CANCELLED'

export interface WorkbenchDeal {
  id: string
  influencerName: string
  handle?: string
  status: DealStatus
  labels: string[]
  nextAction: string
  updatedAt?: string
}

export interface InfluencerSummary {
  id: string
  display_name: string
  country?: string | null
  city?: string | null
}

export interface PrimaryPlatformSummary {
  platform: string
  username?: string | null
  profile_url?: string | null
  follower_count?: number | null
}

export interface PrimaryContactSummary {
  id: string
  name?: string | null
  email: string
  role: string
  is_primary: boolean
}

export interface DeliverableSummary {
  total_count: number
  completed_count: number
  next_due_date?: string | null
  published_url_count: number
  label?: string | null
}

export interface CompensationSummary {
  active_item_count: number
  completed_item_count: number
  cash_totals: Record<string, string | number>
  reimbursement_totals: Record<string, string | number>
  non_cash_descriptions: string[]
  label?: string | null
}

export interface EmailThreadSummary {
  thread_count: number
  last_activity_at?: string | null
}

export interface DealPipelineRow {
  id: string
  campaign_id: string
  status: DealStatus
  lost_reason?: string | null
  labels: string[]
  internal_notes?: string | null
  influencer: InfluencerSummary
  primary_platform?: PrimaryPlatformSummary | null
  platforms: PrimaryPlatformSummary[]
  primary_contact?: PrimaryContactSummary | null
  deliverables: DeliverableSummary
  compensation: CompensationSummary
  email_threads: EmailThreadSummary
  completion_suggested: boolean
  updated_at: string
  archived_at?: string | null
}

export interface DealDetailResponse extends DealPipelineRow {
  created_at: string
  source_list_status?: string | null
}

export interface DealListResponse {
  deals: DealPipelineRow[]
}

export interface DealBulkCreateRequest {
  influencer_ids: string[]
  skip_existing?: boolean
}

export interface DealBulkCreateRowResult {
  influencer_id: string
  deal_id?: string | null
  status: 'created' | 'skipped' | 'conflict' | 'error'
  errors: string[]
}

export interface DealBulkCreateResponse {
  created_count: number
  skipped_count: number
  conflict_count: number
  error_count: number
  rows: DealBulkCreateRowResult[]
}

export interface DealBulkUpdateRequest {
  deal_ids: string[]
  status?: DealStatus | null
  lost_reason?: string | null
  labels?: string[] | null
  label_mode?: 'replace' | 'add' | 'remove'
  internal_notes?: string | null
  notes_mode?: 'replace' | 'append'
}

export interface DealBulkUpdateResponse {
  updated_count: number
  error_count: number
  rows: {
    deal_id: string
    status: 'updated' | 'error'
    errors: string[]
  }[]
}

export interface DealUpdateRequest {
  status?: DealStatus | null
  lost_reason?: string | null
  labels?: string[] | null
  internal_notes?: string | null
}

export interface DeliverableCreateRequest {
  type: string
  quantity?: number
  due_date?: string | null
  status?: DeliverableStatus
  published_url?: string | null
  notes?: string | null
}

export interface DeliverableUpdateRequest {
  type?: string | null
  quantity?: number | null
  due_date?: string | null
  status?: DeliverableStatus | null
  published_url?: string | null
  notes?: string | null
}

export interface DeliverableResponse {
  id: string
  deal_id: string
  type: string
  quantity: number
  due_date?: string | null
  status: DeliverableStatus
  published_url?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface DeliverableListResponse {
  deliverables: DeliverableResponse[]
}

export interface CompensationItemCreateRequest {
  type?: CompensationItemType
  description?: string | null
  amount?: string | number | null
  currency?: string | null
  recipient_name?: string | null
  status?: CompensationItemStatus
  due_date?: string | null
  completed_at?: string | null
  receipt_file_id?: string | null
  notes?: string | null
}

export interface CompensationItemUpdateRequest {
  type?: CompensationItemType | null
  description?: string | null
  amount?: string | number | null
  currency?: string | null
  recipient_name?: string | null
  status?: CompensationItemStatus | null
  due_date?: string | null
  completed_at?: string | null
  receipt_file_id?: string | null
  notes?: string | null
}

export interface CompensationItemResponse {
  id: string
  deal_id: string
  type: CompensationItemType
  description?: string | null
  amount?: string | number | null
  currency?: string | null
  recipient_name?: string | null
  status: CompensationItemStatus
  due_date?: string | null
  completed_at?: string | null
  receipt_file_id?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface CompensationItemListResponse {
  compensation_items: CompensationItemResponse[]
}

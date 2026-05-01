import { computed, ref, watch } from 'vue'
import {
  archiveInfluencer as archiveInfluencerRequest,
  createManualInfluencer,
  errorMessage,
  listInfluencers,
} from '../api/client'
import type { InfluencerListItem, ManualInfluencerInput } from '../api/types'

export const platformOptions = [
  { label: 'Instagram', value: 'instagram' },
  { label: 'TikTok', value: 'tiktok' },
  { label: 'YouTube', value: 'youtube' },
  { label: 'X / Twitter', value: 'x' },
  { label: 'Twitch', value: 'twitch' },
]

export const platformColor = (platform: string) => {
  const normalized = platform.toLowerCase()
  if (normalized === 'instagram') return 'magenta'
  if (normalized === 'tiktok') return 'cyan'
  if (normalized === 'youtube') return 'red'
  if (normalized === 'x') return 'blue'
  return 'default'
}

const normalizeQueryValue = (value: string) => {
  const trimmed = value.trim()
  return trimmed || undefined
}

const maxInfluencerTags = 20
const maxInfluencerTagLength = 32
const influencerTagPattern = /^[\p{L}\p{N}_\s\-/.&]+$/u

export const normalizeInfluencerTags = (tags: string[] = []) => {
  const normalizedTags: string[] = []
  const seen = new Set<string>()
  for (const tag of tags) {
    const normalized = tag.trim().replace(/\s+/g, ' ')
    if (!normalized) {
      throw new Error('Tags cannot be blank.')
    }
    if (normalized.length > maxInfluencerTagLength) {
      throw new Error(`Tags must be ${maxInfluencerTagLength} characters or fewer.`)
    }
    if (!influencerTagPattern.test(normalized)) {
      throw new Error('Tags can use letters, numbers, spaces, -, _, /, ., and &.')
    }

    const key = normalized.toLocaleLowerCase()
    if (!seen.has(key)) {
      seen.add(key)
      normalizedTags.push(normalized)
      if (normalizedTags.length > maxInfluencerTags) {
        throw new Error(`Use ${maxInfluencerTags} tags or fewer.`)
      }
    }
  }

  return normalizedTags
}

export const useInfluencers = () => {
  const influencers = ref<InfluencerListItem[]>([])
  const loading = ref(false)
  const creating = ref(false)
  const archiving = ref(false)
  const error = ref<string | null>(null)
  const searchText = ref('')
  const platformFilter = ref<string | undefined>()
  const countryFilter = ref('')
  const cityFilter = ref('')
  const tagFilter = ref<string | undefined>()
  const includeArchived = ref(false)
  const selectedRowKeys = ref<string[]>([])

  const loadInfluencers = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await listInfluencers({
        query: normalizeQueryValue(searchText.value),
        platform: platformFilter.value,
        country: normalizeQueryValue(countryFilter.value),
        city: normalizeQueryValue(cityFilter.value),
        tag: tagFilter.value,
        includeArchived: includeArchived.value,
      })
      influencers.value = response.influencers
    } catch (loadError) {
      error.value = errorMessage(loadError)
    } finally {
      loading.value = false
    }
  }

  const activeInfluencerCount = computed(
    () => influencers.value.filter((influencer) => !influencer.archived_at).length,
  )

  const platformCount = computed(
    () =>
      new Set(
        influencers.value.flatMap((influencer) =>
          influencer.platforms.map((platform) => platform.platform),
        ),
      ).size,
  )

  const withContactCount = computed(
    () =>
      influencers.value.filter(
        (influencer) => !influencer.archived_at && influencer.primary_contact,
      ).length,
  )

  const archivedInfluencerCount = computed(
    () => influencers.value.filter((influencer) => influencer.archived_at).length,
  )

  const tagOptions = computed(() =>
    Array.from(new Set(influencers.value.flatMap((influencer) => influencer.tags))).map((tag) => ({
      label: tag,
      value: tag,
    })),
  )

  const createInfluencer = async (payload: ManualInfluencerInput) => {
    creating.value = true
    error.value = null

    try {
      const created = await createManualInfluencer(payload)
      await loadInfluencers()
      return created
    } catch (createError) {
      error.value = errorMessage(createError)
      throw createError
    } finally {
      creating.value = false
    }
  }

  const archiveInfluencer = async (influencerId: string) => {
    archiving.value = true
    error.value = null

    try {
      await archiveInfluencerRequest(influencerId)
      selectedRowKeys.value = selectedRowKeys.value.filter((key) => key !== influencerId)
      await loadInfluencers()
    } catch (archiveError) {
      error.value = errorMessage(archiveError)
      throw archiveError
    } finally {
      archiving.value = false
    }
  }

  const archiveSelectedInfluencers = async () => {
    const influencerIds = [...selectedRowKeys.value]
    if (!influencerIds.length) return { archived: 0, failed: 0 }

    archiving.value = true
    error.value = null

    try {
      const results = await Promise.allSettled(
        influencerIds.map((influencerId) => archiveInfluencerRequest(influencerId)),
      )
      const failed = results.filter((result) => result.status === 'rejected').length
      const archived = results.length - failed

      if (failed > 0) {
        error.value = `${failed} influencer(s) could not be deleted.`
      }

      selectedRowKeys.value = influencerIds.filter(
        (_, index) => results[index]?.status === 'rejected',
      )
      await loadInfluencers()
      return { archived, failed }
    } finally {
      archiving.value = false
    }
  }

  watch([searchText, platformFilter, countryFilter, cityFilter, tagFilter, includeArchived], () => {
    selectedRowKeys.value = []
    void loadInfluencers()
  })

  watch(influencers, (nextInfluencers) => {
    const availableIds = new Set(nextInfluencers.map((influencer) => influencer.id))
    selectedRowKeys.value = selectedRowKeys.value.filter((key) => availableIds.has(key))
  })

  return {
    influencers,
    loading,
    creating,
    archiving,
    error,
    searchText,
    platformFilter,
    countryFilter,
    cityFilter,
    tagFilter,
    includeArchived,
    selectedRowKeys,
    activeInfluencerCount,
    platformCount,
    withContactCount,
    archivedInfluencerCount,
    tagOptions,
    loadInfluencers,
    createInfluencer,
    archiveInfluencer,
    archiveSelectedInfluencers,
  }
}

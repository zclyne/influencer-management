import { computed, ref } from 'vue'
import {
  archiveInfluencer,
  createInfluencerContact,
  createInfluencerPlatform,
  deleteInfluencerContact,
  deleteInfluencerPlatform,
  errorMessage,
  getInfluencer,
  updateInfluencer,
  updateInfluencerContact,
  updateInfluencerPlatform,
} from '../api/client'
import type {
  InfluencerContactCreateRequest,
  InfluencerContactResponse,
  InfluencerContactUpdateRequest,
  InfluencerPlatformCreateRequest,
  InfluencerPlatformResponse,
  InfluencerPlatformUpdateRequest,
  InfluencerResponse,
  InfluencerUpdateRequest,
} from '../api/types'

export const useInfluencerDetail = (influencerId: () => string) => {
  const influencer = ref<InfluencerResponse | null>(null)
  const loading = ref(false)
  const mutating = ref(false)
  const error = ref<string | null>(null)

  const loadInfluencerDetail = async () => {
    const currentInfluencerId = influencerId()
    if (!currentInfluencerId) return

    loading.value = true
    error.value = null

    try {
      influencer.value = await getInfluencer(currentInfluencerId)
    } catch (loadError) {
      error.value = errorMessage(loadError)
    } finally {
      loading.value = false
    }
  }

  const refreshInfluencer = async () => {
    const currentInfluencerId = influencerId()
    if (!currentInfluencerId) return
    influencer.value = await getInfluencer(currentInfluencerId)
  }

  const updateProfile = async (payload: InfluencerUpdateRequest) => {
    mutating.value = true
    error.value = null

    try {
      influencer.value = await updateInfluencer(influencerId(), payload)
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
      await archiveInfluencer(influencerId())
      await refreshInfluencer()
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const createPlatform = async (payload: InfluencerPlatformCreateRequest) => {
    mutating.value = true
    error.value = null

    try {
      await createInfluencerPlatform(influencerId(), payload)
      await refreshInfluencer()
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const updatePlatform = async (
    platform: InfluencerPlatformResponse,
    payload: InfluencerPlatformUpdateRequest,
  ) => {
    mutating.value = true
    error.value = null

    try {
      await updateInfluencerPlatform(influencerId(), platform.id, payload)
      await refreshInfluencer()
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const deletePlatform = async (platform: InfluencerPlatformResponse) => {
    mutating.value = true
    error.value = null

    try {
      await deleteInfluencerPlatform(influencerId(), platform.id)
      await refreshInfluencer()
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const createContact = async (payload: InfluencerContactCreateRequest) => {
    mutating.value = true
    error.value = null

    try {
      await createInfluencerContact(influencerId(), payload)
      await refreshInfluencer()
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const updateContact = async (
    contact: InfluencerContactResponse,
    payload: InfluencerContactUpdateRequest,
  ) => {
    mutating.value = true
    error.value = null

    try {
      await updateInfluencerContact(influencerId(), contact.id, payload)
      await refreshInfluencer()
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const deleteContact = async (contact: InfluencerContactResponse) => {
    mutating.value = true
    error.value = null

    try {
      await deleteInfluencerContact(influencerId(), contact.id)
      await refreshInfluencer()
    } catch (mutationError) {
      error.value = errorMessage(mutationError)
      throw mutationError
    } finally {
      mutating.value = false
    }
  }

  const primaryContact = computed(
    () => influencer.value?.contacts.find((contact) => contact.is_primary) ?? influencer.value?.contacts[0] ?? null,
  )

  return {
    influencer,
    loading,
    mutating,
    error,
    primaryContact,
    loadInfluencerDetail,
    updateProfile,
    archiveProfile,
    createPlatform,
    updatePlatform,
    deletePlatform,
    createContact,
    updateContact,
    deleteContact,
  }
}

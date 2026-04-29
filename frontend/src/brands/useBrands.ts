import { computed, ref, watch } from 'vue'
import {
  archiveBrand as archiveBrandRequest,
  createBrand,
  errorMessage,
  listBrands,
  updateBrand,
} from '../api/client'
import type { BrandCreateRequest, BrandResponse, BrandUpdateRequest } from '../api/types'

const normalizeQueryValue = (value: string) => {
  const trimmed = value.trim()
  return trimmed || undefined
}

export const useBrands = () => {
  const brands = ref<BrandResponse[]>([])
  const loading = ref(false)
  const saving = ref(false)
  const archiving = ref(false)
  const error = ref<string | null>(null)
  const searchText = ref('')
  const includeArchived = ref(false)
  const selectedRowKeys = ref<string[]>([])

  const loadBrands = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await listBrands({
        query: normalizeQueryValue(searchText.value),
        includeArchived: includeArchived.value,
      })
      brands.value = response.brands
    } catch (loadError) {
      error.value = errorMessage(loadError)
    } finally {
      loading.value = false
    }
  }

  const activeBrandCount = computed(
    () => brands.value.filter((brand) => !brand.archived_at).length,
  )

  const linkedCampaignCount = computed(() =>
    brands.value.reduce((count, brand) => count + (brand.campaign_count ?? 0), 0),
  )

  const archivedBrandCount = computed(
    () => brands.value.filter((brand) => brand.archived_at).length,
  )

  const createNewBrand = async (payload: BrandCreateRequest) => {
    saving.value = true
    error.value = null

    try {
      const created = await createBrand(payload)
      await loadBrands()
      return created
    } catch (createError) {
      error.value = errorMessage(createError)
      throw createError
    } finally {
      saving.value = false
    }
  }

  const updateExistingBrand = async (brandId: string, payload: BrandUpdateRequest) => {
    saving.value = true
    error.value = null

    try {
      const updated = await updateBrand(brandId, payload)
      await loadBrands()
      return updated
    } catch (updateError) {
      error.value = errorMessage(updateError)
      throw updateError
    } finally {
      saving.value = false
    }
  }

  const archiveBrand = async (brandId: string) => {
    archiving.value = true
    error.value = null

    try {
      await archiveBrandRequest(brandId)
      selectedRowKeys.value = selectedRowKeys.value.filter((key) => key !== brandId)
      await loadBrands()
    } catch (archiveError) {
      error.value = errorMessage(archiveError)
      throw archiveError
    } finally {
      archiving.value = false
    }
  }

  const archiveSelectedBrands = async () => {
    const brandIds = [...selectedRowKeys.value]
    if (!brandIds.length) return { archived: 0, failed: 0 }

    archiving.value = true
    error.value = null

    try {
      const results = await Promise.allSettled(
        brandIds.map((brandId) => archiveBrandRequest(brandId)),
      )
      const failed = results.filter((result) => result.status === 'rejected').length
      const archived = results.length - failed

      if (failed > 0) {
        error.value = `${failed} brand(s) could not be archived.`
      }

      selectedRowKeys.value = brandIds.filter((_, index) => results[index]?.status === 'rejected')
      await loadBrands()
      return { archived, failed }
    } finally {
      archiving.value = false
    }
  }

  watch([searchText, includeArchived], () => {
    selectedRowKeys.value = []
    void loadBrands()
  })

  watch(brands, (nextBrands) => {
    const availableIds = new Set(nextBrands.map((brand) => brand.id))
    selectedRowKeys.value = selectedRowKeys.value.filter((key) => availableIds.has(key))
  })

  return {
    brands,
    loading,
    saving,
    archiving,
    error,
    searchText,
    includeArchived,
    selectedRowKeys,
    activeBrandCount,
    linkedCampaignCount,
    archivedBrandCount,
    loadBrands,
    createNewBrand,
    updateExistingBrand,
    archiveBrand,
    archiveSelectedBrands,
  }
}

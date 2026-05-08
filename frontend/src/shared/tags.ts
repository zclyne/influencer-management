const maxTags = 20
const maxTagLength = 32
const tagPattern = /^[\p{L}\p{N}_\s\-/.&]+$/u

export const normalizeTags = (tags: string[] = []) => {
  const normalizedTags: string[] = []
  const seen = new Set<string>()
  for (const tag of tags) {
    const normalized = tag.trim().replace(/\s+/g, ' ')
    if (!normalized) {
      throw new Error('Tags cannot be blank.')
    }
    if (normalized.length > maxTagLength) {
      throw new Error(`Tags must be ${maxTagLength} characters or fewer.`)
    }
    if (!tagPattern.test(normalized)) {
      throw new Error('Tags can use letters, numbers, spaces, -, _, /, ., and &.')
    }

    const key = normalized.toLocaleLowerCase()
    if (!seen.has(key)) {
      seen.add(key)
      normalizedTags.push(normalized)
      if (normalizedTags.length > maxTags) {
        throw new Error(`Use ${maxTags} tags or fewer.`)
      }
    }
  }

  return normalizedTags
}

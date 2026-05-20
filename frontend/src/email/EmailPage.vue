<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import {
  Bold,
  ChevronLeft,
  ChevronRight,
  Image as ImageIcon,
  Italic,
  List,
  ListOrdered,
  Link as LinkIcon,
  MailCheck,
  MailOpen,
  Paperclip,
  Pencil,
  RefreshCw,
  Reply,
  ReplyAll,
  Send,
  Trash2,
  Underline as UnderlineIcon,
  Unplug,
  X,
} from '@lucide/vue'
import {
  ApiError,
  batchEmailThreads,
  deleteEmailDraft,
  disconnectEmail,
  errorMessage,
  getEmailAuthStatus,
  getEmailThread,
  linkEmailThread,
  listCampaignDeals,
  listCampaigns,
  listEmailLabels,
  listEmailThreads,
  saveEmailReplyDraft,
  sendEmailDraft,
  startEmailAuth,
  unlinkEmailThread,
} from '../api/client'
import type {
  CampaignResponse,
  DealPipelineRow,
  EmailCrmLink,
  EmailParticipant,
  EmailReplyMode,
  EmailThreadBatchAction,
  GmailAuthStatusResponse,
  GmailLabelResponse,
  GmailMessageResponse,
  GmailThreadDetailResponse,
  GmailThreadSummary,
} from '../api/types'
import EmptyState from '../shared/EmptyState.vue'

const route = useRoute()
const router = useRouter()

const mailViews = [
  { label: 'Primary', value: 'primary' },
  { label: 'Promotions', value: 'promotions' },
  { label: 'Social', value: 'social' },
  { label: 'Updates', value: 'updates' },
  { label: 'Forums', value: 'forums' },
  { label: 'Starred', value: 'starred' },
  { label: 'Deleted', value: 'deleted' },
  { label: 'Spam', value: 'spam' },
]

const routeView = route.query.view as string | undefined
const initialMailView =
  routeView && mailViews.some((view) => view.value === routeView) ? routeView : 'primary'

const authStatus = ref<GmailAuthStatusResponse | null>(null)
const campaigns = ref<CampaignResponse[]>([])
const deals = ref<DealPipelineRow[]>([])
const labels = ref<GmailLabelResponse[]>([])
const threads = ref<GmailThreadSummary[]>([])
const selectedThread = ref<GmailThreadDetailResponse | null>(null)
const nextPageToken = ref<string | null>(null)
const resultSizeEstimate = ref<number | null>(null)
const pageTokens = ref<(string | undefined)[]>([undefined])
const currentPageIndex = ref(0)
const selectedMailView = ref<string>(initialMailView)
const selectedCampaignId = ref<string | undefined>(route.query.campaignId as string | undefined)
const selectedDealId = ref<string | undefined>(route.query.dealId as string | undefined)
const selectedLabel = ref<string | undefined>()
const selectedThreadIds = ref<string[]>([])
const expandedQuotedMessageIds = ref<Set<string>>(new Set())
const messageFrameHeights = ref<Record<string, number>>({})
const query = ref('')
const loading = ref(false)
const detailLoading = ref(false)
const authLoading = ref(false)
const batchLoading = ref(false)
const linkModalOpen = ref(false)
const linkSaving = ref(false)
const linkDealsLoading = ref(false)
const linkCampaignId = ref<string | undefined>()
const linkDealId = ref<string | undefined>()
const linkDeals = ref<DealPipelineRow[]>([])
const error = ref<string | null>(null)
const composerOpen = ref(false)
const composerAnchorMessageId = ref<string | null>(null)
const composerMode = ref<EmailReplyMode>('reply')
const composerDraftId = ref<string | null>(null)
const composerTo = ref('')
const composerCc = ref('')
const composerBcc = ref('')
const composerSubject = ref('')
const composerBodyHtml = ref('')
const composerAttachments = ref<File[]>([])
const composerInlineImages = ref<{ cid: string; file: File; url: string }[]>([])
const composerSaveStatus = ref<'idle' | 'saving' | 'saved' | 'failed'>('idle')
const composerSending = ref(false)
let composerSaveTimer: number | null = null

const reconnectRequired = computed(() => authStatus.value?.reconnect_required === true)
const connected = computed(() => authStatus.value?.connected === true && !reconnectRequired.value)
const pageSize = 20
const authPanelTitle = computed(() => (reconnectRequired.value ? 'Reconnect Gmail' : 'Sign in to Gmail'))
const authPanelCopy = computed(() =>
  reconnectRequired.value
    ? 'Your Google session expired or failed. Sign in with Google again to keep loading Gmail threads.'
    : 'Use your Google account to load Gmail threads and apply CreatorFlow campaign labels.',
)
const authButtonLabel = computed(() => {
  if (authLoading.value) return 'Opening Google…'
  return 'Sign in with Google'
})

const campaignOptions = computed(() =>
  campaigns.value.map((campaign) => ({ label: campaign.name, value: campaign.id })),
)

const dealOptions = computed(() =>
  deals.value.map((deal) => ({
    label: deal.influencer.display_name,
    value: deal.id,
  })),
)

const linkDealOptions = computed(() =>
  linkDeals.value.map((deal) => ({
    label: deal.influencer.display_name,
    value: deal.id,
  })),
)

const labelOptions = computed(() =>
  labels.value
    .filter((label) => label.type !== 'system')
    .map((label) => ({ label: label.name, value: label.name })),
)

const selectedThreadId = computed(() => selectedThread.value?.id ?? (route.query.threadId as string | undefined))

const gmailThreadUrl = computed(() => {
  if (!selectedThread.value?.id) return null
  const threadId = encodeURIComponent(selectedThread.value.id)
  if (authStatus.value?.email) {
    return `https://mail.google.com/mail/u/?authuser=${encodeURIComponent(authStatus.value.email)}#all/${threadId}`
  }
  return `https://mail.google.com/mail/u/0/#all/${threadId}`
})

const threadRangeLabel = computed(() => {
  if (!threads.value.length) return '0'
  const start = currentPageIndex.value * pageSize + 1
  const end = start + threads.value.length - 1
  if (resultSizeEstimate.value !== null) {
    return `${start}-${end} of about ${resultSizeEstimate.value}`
  }
  return `${start}-${end}`
})

const hasPreviousPage = computed(() => currentPageIndex.value > 0)
const hasNextPage = computed(() => Boolean(nextPageToken.value))
const selectedThreadHasLinks = computed(() => Boolean(selectedThread.value?.crm_links.length))
const selectedThreadIdSet = computed(() => new Set(selectedThreadIds.value))
const selectedVisibleCount = computed(
  () => threads.value.filter((thread) => selectedThreadIdSet.value.has(thread.id)).length,
)
const allVisibleSelected = computed(
  () => threads.value.length > 0 && selectedVisibleCount.value === threads.value.length,
)
const hasSelectedThreads = computed(() => selectedThreadIds.value.length > 0)
const hasThreadFilters = computed(() =>
  Boolean(
    query.value.trim() ||
      selectedCampaignId.value ||
      selectedDealId.value ||
      selectedLabel.value ||
      selectedMailView.value !== 'primary',
  ),
)
const maxMessageFrameHeight = 520
const minMessageFrameHeight = 72
const composerEditor = useEditor({
  extensions: [
    StarterKit,
    Underline,
    Link.configure({ openOnClick: false }),
    Image.configure({ allowBase64: true }),
  ],
  content: '',
  onUpdate: ({ editor }) => {
    composerBodyHtml.value = editor.getHTML()
    scheduleComposerSave()
  },
})

const loadAuthStatus = async () => {
  authStatus.value = await getEmailAuthStatus()
}

const enterReconnectState = (messageText: string) => {
  authStatus.value = {
    connected: true,
    email: authStatus.value?.email,
    google_subject: authStatus.value?.google_subject,
    scopes: authStatus.value?.scopes ?? [],
    expires_at: authStatus.value?.expires_at,
    reconnect_required: true,
  }
  threads.value = []
  labels.value = []
  selectedThread.value = null
  selectedThreadIds.value = []
  nextPageToken.value = null
  resultSizeEstimate.value = null
  error.value = messageText
}

const handleEmailError = (caughtError: unknown) => {
  const messageText = errorMessage(caughtError)
  if (caughtError instanceof ApiError && caughtError.payload.code === 'email_reconnect_required') {
    enterReconnectState(messageText)
    return true
  }
  return false
}

const connectGmail = async () => {
  authLoading.value = true
  try {
    const response = await startEmailAuth()
    window.location.href = response.authorization_url
  } catch (authError) {
    message.error(errorMessage(authError))
  } finally {
    authLoading.value = false
  }
}

const disconnect = async () => {
  authLoading.value = true
  try {
    await disconnectEmail()
    authStatus.value = await getEmailAuthStatus()
    threads.value = []
    selectedThread.value = null
    message.success('Gmail disconnected.')
  } catch (disconnectError) {
    message.error(errorMessage(disconnectError))
  } finally {
    authLoading.value = false
  }
}

const syncQueryToRoute = () => {
  const nextQuery: Record<string, string> = {}
  if (selectedMailView.value !== 'primary') nextQuery.view = selectedMailView.value
  if (selectedCampaignId.value) nextQuery.campaignId = selectedCampaignId.value
  if (selectedDealId.value) nextQuery.dealId = selectedDealId.value
  if (selectedThread.value?.id) nextQuery.threadId = selectedThread.value.id
  void router.replace({ name: 'email', query: nextQuery })
}

const loadCampaigns = async () => {
  const response = await listCampaigns()
  campaigns.value = response.campaigns
}

const loadDeals = async () => {
  if (!selectedCampaignId.value) {
    deals.value = []
    selectedDealId.value = undefined
    return
  }
  const response = await listCampaignDeals(selectedCampaignId.value)
  deals.value = response.deals
  if (selectedDealId.value && !response.deals.some((deal) => deal.id === selectedDealId.value)) {
    selectedDealId.value = undefined
  }
}

const loadLabels = async () => {
  labels.value = (await listEmailLabels()).labels
}

const loadThreads = async ({
  pageIndex = 0,
  preserveSelection = false,
}: {
  pageIndex?: number
  preserveSelection?: boolean
} = {}) => {
  if (!connected.value) return
  loading.value = true
  error.value = null
  try {
    const response = await listEmailThreads({
      campaignId: selectedCampaignId.value,
      dealId: selectedDealId.value,
      query: query.value.trim() || undefined,
      label: selectedLabel.value,
      view: selectedMailView.value,
      pageToken: pageTokens.value[pageIndex],
      pageSize,
    })
    threads.value = response.threads
    selectedThreadIds.value = []
    nextPageToken.value = response.next_page_token ?? null
    resultSizeEstimate.value = response.result_size_estimate ?? null
    currentPageIndex.value = pageIndex
    if (response.next_page_token) {
      pageTokens.value = [
        ...pageTokens.value.slice(0, pageIndex + 1),
        response.next_page_token,
      ]
    } else {
      pageTokens.value = pageTokens.value.slice(0, pageIndex + 1)
    }

    const existingThreadId = preserveSelection ? selectedThread.value?.id : undefined
    const preferredThread =
      response.threads.find((thread) => thread.id === existingThreadId) ?? response.threads[0]
    if (preferredThread) {
      await openThread(preferredThread.id, { markRead: false })
    } else {
      selectedThread.value = null
    }
    syncQueryToRoute()
  } catch (loadError) {
    if (!handleEmailError(loadError)) {
      error.value = errorMessage(loadError)
    }
  } finally {
    loading.value = false
  }
}

const resetThreadPagination = async () => {
  pageTokens.value = [undefined]
  currentPageIndex.value = 0
  await loadThreads({ pageIndex: 0 })
}

const refreshCurrentPage = async () => {
  await loadThreads({ pageIndex: currentPageIndex.value, preserveSelection: true })
}

const loadPreviousPage = async () => {
  if (!hasPreviousPage.value) return
  await loadThreads({ pageIndex: currentPageIndex.value - 1 })
}

const loadNextPage = async () => {
  if (!hasNextPage.value) return
  await loadThreads({ pageIndex: currentPageIndex.value + 1 })
}

const toggleThreadSelection = (threadId: string) => {
  if (selectedThreadIdSet.value.has(threadId)) {
    selectedThreadIds.value = selectedThreadIds.value.filter((id) => id !== threadId)
    return
  }
  selectedThreadIds.value = [...selectedThreadIds.value, threadId]
}

const selectVisibleThreads = () => {
  selectedThreadIds.value = threads.value.map((thread) => thread.id)
}

const clearThreadSelection = () => {
  selectedThreadIds.value = []
}

const toggleVisibleSelection = () => {
  if (allVisibleSelected.value) {
    clearThreadSelection()
    return
  }
  selectVisibleThreads()
}

const applyBatchAction = async (action: EmailThreadBatchAction) => {
  if (!selectedThreadIds.value.length) return
  batchLoading.value = true
  try {
    await batchEmailThreads({
      thread_ids: selectedThreadIds.value,
      action,
    })
    await refreshCurrentPage()
    selectedThreadIds.value = []
    const labelByAction: Record<EmailThreadBatchAction, string> = {
      mark_read: 'Marked as read.',
      mark_unread: 'Marked as unread.',
      delete: 'Moved to deleted.',
    }
    message.success(labelByAction[action])
  } catch (batchError) {
    if (!handleEmailError(batchError)) {
      message.error(errorMessage(batchError))
    }
  } finally {
    batchLoading.value = false
  }
}

const openThread = async (
  threadId: string,
  {
    markRead = true,
  }: {
    markRead?: boolean
  } = {},
) => {
  detailLoading.value = true
  try {
    selectedThread.value = await getEmailThread(threadId, { markRead })
    expandedQuotedMessageIds.value = new Set()
    messageFrameHeights.value = {}
    threads.value = threads.value.map((thread) =>
      thread.id === threadId ? { ...thread, unread: selectedThread.value?.unread ?? false } : thread,
    )
    syncQueryToRoute()
  } catch (threadError) {
    if (!handleEmailError(threadError)) {
      message.error(errorMessage(threadError))
    }
  } finally {
    detailLoading.value = false
  }
}

const loadLinkDeals = async (campaignId?: string) => {
  linkDeals.value = []
  linkDealId.value = undefined
  if (!campaignId) return
  linkDealsLoading.value = true
  try {
    linkDeals.value = (await listCampaignDeals(campaignId)).deals
  } catch (dealError) {
    message.error(errorMessage(dealError))
  } finally {
    linkDealsLoading.value = false
  }
}

const openLinkModal = async () => {
  if (!selectedThread.value) return
  const dealLink = selectedThread.value.crm_links.find((link) => link.type === 'deal')
  const campaignLink = selectedThread.value.crm_links.find((link) => link.type === 'campaign')
  linkCampaignId.value =
    dealLink?.campaign_id ?? campaignLink?.campaign_id ?? selectedCampaignId.value
  linkModalOpen.value = true
  await loadLinkDeals(linkCampaignId.value)
  linkDealId.value = dealLink?.deal_id ?? selectedDealId.value
  if (linkDealId.value && !linkDeals.value.some((deal) => deal.id === linkDealId.value)) {
    linkDealId.value = undefined
  }
}

const unlinkExistingThreadLinks = async () => {
  if (!selectedThread.value) return
  const links = [...selectedThread.value.crm_links].sort((left, right) => {
    if (left.type === right.type) return 0
    return left.type === 'deal' ? -1 : 1
  })
  for (const link of links) {
    await unlinkEmailThread(selectedThread.value.id, {
      campaignId: link.type === 'campaign' ? link.campaign_id ?? undefined : undefined,
      dealId: link.type === 'deal' ? link.deal_id ?? undefined : undefined,
    })
  }
}

const saveThreadLinks = async () => {
  if (!selectedThread.value) return
  if (!linkCampaignId.value) {
    message.error('Select a campaign before linking.')
    return
  }
  linkSaving.value = true
  try {
    await unlinkExistingThreadLinks()
    await linkEmailThread(selectedThread.value.id, {
      campaign_id: linkCampaignId.value,
      deal_id: linkDealId.value,
    })
    selectedThread.value = await getEmailThread(selectedThread.value.id)
    await refreshCurrentPage()
    linkModalOpen.value = false
    message.success('Thread linked.')
  } catch (linkError) {
    if (!handleEmailError(linkError)) {
      message.error(errorMessage(linkError))
    }
  } finally {
    linkSaving.value = false
  }
}

const clearThreadLinks = async () => {
  if (!selectedThread.value) return
  linkSaving.value = true
  try {
    await unlinkExistingThreadLinks()
    selectedThread.value = await getEmailThread(selectedThread.value.id)
    await refreshCurrentPage()
    linkModalOpen.value = false
    message.success('Thread links cleared.')
  } catch (linkError) {
    if (!handleEmailError(linkError)) {
      message.error(errorMessage(linkError))
    }
  } finally {
    linkSaving.value = false
  }
}

const changeLinkCampaign = async (campaignId?: string) => {
  linkCampaignId.value = campaignId
  await loadLinkDeals(campaignId)
}

const cancelLinkModal = () => {
  linkModalOpen.value = false
  linkCampaignId.value = undefined
  linkDealId.value = undefined
  linkDeals.value = []
}

const linkButtonLabel = () => {
  if (!selectedThread.value) return 'Link to campaign/deal'
  return selectedThreadHasLinks.value ? 'Edit campaign/deal link' : 'Link to campaign/deal'
}

const linkModalTitle = () => {
  return selectedThreadHasLinks.value ? 'Edit campaign/deal link' : 'Link to campaign/deal'
}

const participantLabel = (thread: GmailThreadSummary) => {
  const first = thread.participants[0]
  return first?.name || first?.email || 'Unknown sender'
}

const formatDate = (value?: string | null) => {
  if (!value) return 'No date'
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

const threadLinkLabel = (link: EmailCrmLink) => {
  if (link.type === 'campaign') {
    return link.campaign_name ? `Campaign: ${link.campaign_name}` : 'Campaign'
  }
  if (link.type === 'deal') {
    return link.deal_influencer_name ? `Deal: ${link.deal_influencer_name}` : 'Deal'
  }
  return link.type
}

const quotedHtmlSelectors = [
  '.gmail_quote',
  '.gmail_attr',
  '.yahoo_quoted',
  '.protonmail_quote',
  '.moz-cite-prefix',
  'blockquote[type="cite"]',
  '[id^="divRplyFwdMsg"]',
  '[class*="gmail_quote"]',
].join(',')

const normalizeBodyForComparison = (value: string) => value.replace(/\s+/g, ' ').trim()

const strippedHtmlBody = (html: string) => {
  if (typeof DOMParser === 'undefined') return { body: html, stripped: false }

  const document = new DOMParser().parseFromString(html, 'text/html')
  const quotedNodes = Array.from(document.querySelectorAll(quotedHtmlSelectors))
  quotedNodes.forEach((node) => node.remove())
  const body = document.documentElement.outerHTML
  const stripped =
    quotedNodes.length > 0 && normalizeBodyForComparison(body) !== normalizeBodyForComparison(html)
  return { body: stripped ? body : html, stripped }
}

const strippedTextBody = (text: string) => {
  const quotePatterns = [
    /(^|\n)On .{1,500}wrote:\s*(\n|$)/i,
    /(^|\n)-{2,}\s*Original Message\s*-{2,}/i,
    /(^|\n)Begin forwarded message:/i,
    /(^|\n)From:\s.+\n(?:Sent|Date):\s.+\nTo:\s.+(?:\nSubject:\s.+)?/i,
  ]
  const quoteStart = quotePatterns.reduce<number | null>((earliest, pattern) => {
    const match = pattern.exec(text)
    if (!match) return earliest
    const index = match.index + (match[1]?.length ?? 0)
    return earliest === null ? index : Math.min(earliest, index)
  }, null)
  if (quoteStart === null) return { body: text, stripped: false }

  const body = text.slice(0, quoteStart).trimEnd()
  return { body: body || text, stripped: Boolean(body) }
}

const quotedTextExpanded = (messageId: string) => expandedQuotedMessageIds.value.has(messageId)

const toggleQuotedText = (messageId: string) => {
  const next = new Set(expandedQuotedMessageIds.value)
  if (next.has(messageId)) {
    next.delete(messageId)
  } else {
    next.add(messageId)
  }
  expandedQuotedMessageIds.value = next
  delete messageFrameHeights.value[messageId]
  void nextTick(() => resizeMessageFrame(messageId))
}

const displayMessageHtml = (mail: GmailMessageResponse) => {
  if (!mail.body_html || quotedTextExpanded(mail.id)) return mail.body_html ?? ''
  return strippedHtmlBody(mail.body_html).body
}

const displayMessageText = (mail: GmailMessageResponse) => {
  if (!mail.body_text || quotedTextExpanded(mail.id)) return mail.body_text ?? ''
  return strippedTextBody(mail.body_text).body
}

const hasQuotedContent = (mail: GmailMessageResponse) => {
  if (mail.body_html && strippedHtmlBody(mail.body_html).stripped) return true
  if (mail.body_text && strippedTextBody(mail.body_text).stripped) return true
  return false
}

const resizeMessageFrame = (messageId: string, event?: Event) => {
  const frame =
    event?.currentTarget instanceof HTMLIFrameElement
      ? event.currentTarget
      : document.querySelector<HTMLIFrameElement>(`iframe[data-message-id="${CSS.escape(messageId)}"]`)
  const frameDocument = frame?.contentDocument
  if (!frameDocument) return

  requestAnimationFrame(() => {
    const body = frameDocument.body
    const html = frameDocument.documentElement
    const contentHeight = Math.max(
      body?.scrollHeight ?? 0,
      body?.offsetHeight ?? 0,
      body?.clientHeight ?? 0,
      html?.scrollHeight ?? 0,
      html?.offsetHeight ?? 0,
      html?.clientHeight ?? 0,
    )
    const nextHeight = Math.min(
      maxMessageFrameHeight,
      Math.max(minMessageFrameHeight, contentHeight + 2),
    )
    messageFrameHeights.value = {
      ...messageFrameHeights.value,
      [messageId]: nextHeight,
    }
  })
}

const emailReaderCss = `
  html, body {
    margin: 0;
    background: #ffffff;
    color: #20262d;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 14px;
    line-height: 1.55;
    overflow-wrap: anywhere;
  }
  body {
    padding: 0;
  }
  img, video {
    max-width: 100%;
    height: auto;
  }
  table {
    max-width: 100%;
  }
  a {
    color: #1a73e8;
  }
`

const emailHeadContent = `<base target="_blank"><style>${emailReaderCss}</style>`

const emailHtmlSrcdoc = (html: string) => {
  if (/<head(\s[^>]*)?>/i.test(html)) {
    return html.replace(/<head(\s[^>]*)?>/i, (match) => `${match}${emailHeadContent}`)
  }
  if (/<html(\s[^>]*)?>/i.test(html)) {
    return html.replace(
      /<html(\s[^>]*)?>/i,
      (match) => `${match}<head>${emailHeadContent}</head>`,
    )
  }
  return `<!doctype html><html><head>${emailHeadContent}</head><body>${html}</body></html>`
}

const participantAddress = (participant?: EmailParticipant | null) => {
  if (!participant?.email) return ''
  return participant.name ? `${participant.name} <${participant.email}>` : participant.email
}

const parseParticipantList = (value: string): EmailParticipant[] =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => {
      const match = /^(.*?)<([^>]+)>$/.exec(item)
      if (!match) return { email: item }
      return { name: match[1].trim() || null, email: match[2].trim() }
    })

const participantListText = (participants: EmailParticipant[]) =>
  participants.map(participantAddress).filter(Boolean).join(', ')

const dedupeParticipants = (participants: EmailParticipant[]) => {
  const seen = new Set<string>()
  return participants.filter((participant) => {
    const email = participant.email?.toLowerCase()
    if (!email || seen.has(email)) return false
    seen.add(email)
    return true
  })
}

const excludeAccount = (participants: EmailParticipant[]) => {
  const account = authStatus.value?.email?.toLowerCase()
  return dedupeParticipants(
    participants.filter((participant) => participant.email?.toLowerCase() !== account),
  )
}

const replyRecipientsFor = (mail: GmailMessageResponse, mode: EmailReplyMode) => {
  const sender = mail.sender ? [mail.sender] : []
  if (mode === 'reply') {
    return { to: excludeAccount(sender), cc: [] }
  }
  const all = excludeAccount([...sender, ...mail.to, ...mail.cc])
  return { to: all.slice(0, 1), cc: all.slice(1) }
}

const latestMessage = () => selectedThread.value?.messages.at(-1)

const openComposer = (mode: EmailReplyMode, mail?: GmailMessageResponse) => {
  const anchor = mail ?? latestMessage()
  if (!selectedThread.value || !anchor) return
  const recipients = replyRecipientsFor(anchor, mode)
  composerOpen.value = true
  composerAnchorMessageId.value = anchor.id
  composerMode.value = mode
  composerDraftId.value = null
  composerTo.value = participantListText(recipients.to)
  composerCc.value = participantListText(recipients.cc)
  composerBcc.value = ''
  composerSubject.value = selectedThread.value.subject?.toLowerCase().startsWith('re:')
    ? selectedThread.value.subject
    : `Re: ${selectedThread.value.subject || ''}`.trim()
  composerAttachments.value = []
  composerInlineImages.value.forEach((image) => URL.revokeObjectURL(image.url))
  composerInlineImages.value = []
  composerSaveStatus.value = 'idle'
  composerEditor.value?.commands.setContent('')
}

const closeComposer = () => {
  if (composerSaveTimer) window.clearTimeout(composerSaveTimer)
  composerOpen.value = false
  composerAnchorMessageId.value = null
  composerDraftId.value = null
  composerAttachments.value = []
  composerInlineImages.value.forEach((image) => URL.revokeObjectURL(image.url))
  composerInlineImages.value = []
  composerSaveStatus.value = 'idle'
  composerEditor.value?.commands.setContent('')
}

const composerHtmlForSend = () => {
  const html = composerEditor.value?.getHTML() ?? composerBodyHtml.value
  if (typeof DOMParser === 'undefined') return html
  const document = new DOMParser().parseFromString(html, 'text/html')
  composerInlineImages.value.forEach((image) => {
    document
      .querySelectorAll('img')
      .forEach((node) => {
        if (node.getAttribute('src') === image.url) node.setAttribute('src', `cid:${image.cid}`)
      })
  })
  return document.body.innerHTML
}

const saveComposerDraft = async ({ force = false }: { force?: boolean } = {}) => {
  if (!composerOpen.value || !selectedThread.value) return null
  const text = composerEditor.value?.getText().trim() ?? ''
  if (!force && !text && !composerAttachments.value.length && !composerInlineImages.value.length) {
    return composerDraftId.value
  }
  composerSaveStatus.value = 'saving'
  try {
    const response = await saveEmailReplyDraft(selectedThread.value.id, {
      draftId: composerDraftId.value,
      replyMode: composerMode.value,
      anchorMessageId: composerAnchorMessageId.value,
      to: parseParticipantList(composerTo.value),
      cc: parseParticipantList(composerCc.value),
      bcc: parseParticipantList(composerBcc.value),
      subject: composerSubject.value,
      bodyHtml: composerHtmlForSend(),
      bodyText: composerEditor.value?.getText() ?? '',
      inlineImages: composerInlineImages.value.map((image) => ({ cid: image.cid, file: image.file })),
      attachments: composerAttachments.value,
    })
    composerDraftId.value = response.draft_id
    composerSaveStatus.value = 'saved'
    return response.draft_id
  } catch (saveError) {
    composerSaveStatus.value = 'failed'
    if (!handleEmailError(saveError)) message.error(errorMessage(saveError))
    return null
  }
}

function scheduleComposerSave() {
  if (!composerOpen.value) return
  if (composerSaveTimer) window.clearTimeout(composerSaveTimer)
  composerSaveStatus.value = 'idle'
  composerSaveTimer = window.setTimeout(() => {
    void saveComposerDraft()
  }, 900)
}

const sendComposer = async () => {
  composerSending.value = true
  try {
    const draftId = await saveComposerDraft({ force: true })
    if (!draftId) {
      message.error('Save the draft before sending.')
      return
    }
    await sendEmailDraft(draftId)
    closeComposer()
    if (selectedThread.value) await openThread(selectedThread.value.id, { markRead: false })
    message.success('Reply sent.')
  } catch (sendError) {
    if (!handleEmailError(sendError)) message.error(errorMessage(sendError))
  } finally {
    composerSending.value = false
  }
}

const discardComposer = async () => {
  try {
    if (composerDraftId.value) await deleteEmailDraft(composerDraftId.value)
    closeComposer()
    message.success('Draft discarded.')
  } catch (discardError) {
    if (!handleEmailError(discardError)) message.error(errorMessage(discardError))
  }
}

const handleAttachmentFiles = (event: Event) => {
  const input = event.target as HTMLInputElement
  composerAttachments.value = [...composerAttachments.value, ...Array.from(input.files ?? [])]
  input.value = ''
  scheduleComposerSave()
}

const handleInlineImageFiles = (event: Event) => {
  const input = event.target as HTMLInputElement
  Array.from(input.files ?? []).forEach((file) => {
    const image = {
      cid: `cf-${crypto.randomUUID()}@creatorflow`,
      file,
      url: URL.createObjectURL(file),
    }
    composerInlineImages.value = [...composerInlineImages.value, image]
    composerEditor.value?.chain().focus().setImage({ src: image.url, alt: file.name }).run()
  })
  input.value = ''
  scheduleComposerSave()
}

const removeAttachment = (index: number) => {
  composerAttachments.value = composerAttachments.value.filter((_, itemIndex) => itemIndex !== index)
  scheduleComposerSave()
}

const setComposerLink = () => {
  const previousUrl = composerEditor.value?.getAttributes('link').href as string | undefined
  const url = window.prompt('Link URL', previousUrl ?? '')
  if (url === null) return
  if (!url.trim()) {
    composerEditor.value?.chain().focus().unsetLink().run()
    return
  }
  composerEditor.value?.chain().focus().extendMarkRange('link').setLink({ href: url.trim() }).run()
}

watch([composerTo, composerCc, composerBcc, composerSubject], () => scheduleComposerSave())

watch(selectedCampaignId, async () => {
  selectedDealId.value = undefined
  await loadDeals()
  await resetThreadPagination()
})

watch([selectedMailView, selectedDealId, selectedLabel], async () => {
  await resetThreadPagination()
})

onMounted(async () => {
  try {
    await Promise.all([loadAuthStatus(), loadCampaigns()])
    await loadDeals()
    if (reconnectRequired.value) {
      error.value = 'Gmail authorization expired or failed. Sign in with Google again.'
      return
    }
    if (connected.value) {
      await loadLabels()
      const threadId = route.query.threadId as string | undefined
      await resetThreadPagination()
      if (threadId) await openThread(threadId)
    }
  } catch (pageError) {
    error.value = errorMessage(pageError)
  }
})

onBeforeUnmount(() => {
  if (composerSaveTimer) window.clearTimeout(composerSaveTimer)
  composerInlineImages.value.forEach((image) => URL.revokeObjectURL(image.url))
})
</script>

<template>
  <section class="email-page">
    <div class="page-header">
      <div>
        <h1>Emails</h1>
        <p>Gmail threads with campaign and deal labels.</p>
      </div>
      <div class="account-actions">
        <a-tag v-if="connected" class="account-pill" color="green">{{ authStatus?.email }}</a-tag>
        <a-tag v-else-if="reconnectRequired" class="account-pill" color="orange">
          {{ authStatus?.email }}
        </a-tag>
        <a-button
          v-if="authStatus?.connected"
          class="secondary-action"
          :loading="authLoading"
          @click="disconnect"
        >
          <Unplug class="button-leading-icon" aria-hidden="true" />
          Disconnect
        </a-button>
      </div>
    </div>

    <section
      v-if="!connected"
      class="google-auth-panel"
      :class="{ reconnect: reconnectRequired }"
    >
      <div class="auth-copy">
        <h2>{{ authPanelTitle }}</h2>
        <p>{{ authPanelCopy }}</p>
      </div>
      <button
        class="google-login-button"
        type="button"
        :disabled="authLoading"
        @click="connectGmail"
      >
        <span class="google-icon" aria-hidden="true">
          <svg viewBox="0 0 18 18" focusable="false">
            <path
              fill="#4285f4"
              d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.91c1.7-1.57 2.69-3.88 2.69-6.62z"
            />
            <path
              fill="#34a853"
              d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.91-2.26c-.81.54-1.84.86-3.05.86-2.35 0-4.34-1.58-5.05-3.71H.94v2.33A9 9 0 0 0 9 18z"
            />
            <path
              fill="#fbbc05"
              d="M3.95 10.71a5.41 5.41 0 0 1 0-3.42V4.96H.94a9 9 0 0 0 0 8.08l3.01-2.33z"
            />
            <path
              fill="#ea4335"
              d="M9 3.58c1.32 0 2.5.45 3.43 1.35l2.58-2.58A8.65 8.65 0 0 0 9 0 9 9 0 0 0 .94 4.96l3.01 2.33C4.66 5.16 6.65 3.58 9 3.58z"
            />
          </svg>
        </span>
        <span>{{ authButtonLabel }}</span>
      </button>
    </section>

    <a-alert
      v-if="error && !reconnectRequired"
      class="page-alert"
      type="error"
      show-icon
      :message="error"
    />

    <template v-if="connected">
      <div class="mail-toolbar">
        <div class="toolbar-row toolbar-row-primary">
          <a-segmented
            v-model:value="selectedMailView"
            class="mail-view-tabs"
            :options="mailViews"
          />
          <div class="toolbar-actions" aria-label="Mailbox navigation">
            <span class="thread-range">{{ threadRangeLabel }}</span>
            <a-button
              class="icon-button"
              size="small"
              type="text"
              title="Previous page"
              aria-label="Previous page"
              :disabled="!hasPreviousPage || loading"
              @click="loadPreviousPage"
            >
              <ChevronLeft aria-hidden="true" />
            </a-button>
            <a-button
              class="icon-button"
              size="small"
              type="text"
              title="Next page"
              aria-label="Next page"
              :disabled="!hasNextPage || loading"
              @click="loadNextPage"
            >
              <ChevronRight aria-hidden="true" />
            </a-button>
            <a-button
              class="icon-button"
              size="small"
              type="text"
              title="Refresh"
              aria-label="Refresh"
              :disabled="loading"
              @click="refreshCurrentPage"
            >
              <RefreshCw aria-hidden="true" />
            </a-button>
          </div>
        </div>

        <div class="toolbar-row toolbar-row-filters">
          <a-input-search
            v-model:value="query"
            class="query-input"
            placeholder="Search Gmail"
            enter-button="Search"
            @search="resetThreadPagination"
          />
          <a-select
            v-model:value="selectedCampaignId"
            class="filter-select"
            allow-clear
            placeholder="Campaign"
            :options="campaignOptions"
          />
          <a-select
            v-model:value="selectedDealId"
            class="filter-select"
            allow-clear
            placeholder="Deal"
            :disabled="!selectedCampaignId"
            :options="dealOptions"
          />
          <a-select
            v-model:value="selectedLabel"
            class="filter-select"
            allow-clear
            show-search
            placeholder="Gmail label"
            :options="labelOptions"
          />
        </div>
      </div>

      <div class="email-workspace">
        <a-card class="thread-list-card" :body-style="{ padding: 0 }">
          <div class="thread-list-header">
            <div class="thread-list-title">
              <strong>Threads</strong>
              <span>{{ threadRangeLabel }}</span>
            </div>
          </div>
          <div class="batch-toolbar">
            <a-checkbox
              :checked="allVisibleSelected"
              :indeterminate="selectedVisibleCount > 0 && !allVisibleSelected"
              :disabled="!threads.length || loading || batchLoading"
              @change="toggleVisibleSelection"
            >
              {{ selectedThreadIds.length ? `${selectedThreadIds.length} selected` : '' }}
            </a-checkbox>
            <a-space>
              <a-button
                class="icon-button"
                size="small"
                type="text"
                title="Mark read"
                aria-label="Mark read"
                :disabled="!hasSelectedThreads || batchLoading"
                @click="applyBatchAction('mark_read')"
              >
                <MailCheck aria-hidden="true" />
              </a-button>
              <a-button
                class="icon-button"
                size="small"
                type="text"
                title="Mark unread"
                aria-label="Mark unread"
                :disabled="!hasSelectedThreads || batchLoading"
                @click="applyBatchAction('mark_unread')"
              >
                <MailOpen aria-hidden="true" />
              </a-button>
              <a-button
                class="icon-button"
                danger
                size="small"
                type="text"
                title="Delete"
                aria-label="Delete"
                :disabled="!hasSelectedThreads || batchLoading"
                :loading="batchLoading"
                @click="applyBatchAction('delete')"
              >
                <Trash2 v-if="!batchLoading" aria-hidden="true" />
              </a-button>
            </a-space>
          </div>
          <div class="thread-list-scroll">
            <a-list :loading="loading" :data-source="threads" item-layout="vertical">
              <template #emptyText>
                <EmptyState
                  v-if="hasThreadFilters"
                  title="No Gmail threads match"
                  description="Clear the search, CRM filters, label, or mailbox view to broaden the thread list."
                />
                <EmptyState
                  v-else
                  title="No Gmail threads"
                  description="Refresh Gmail or choose another mailbox view if messages should be available."
                />
              </template>
              <template #renderItem="{ item }">
                <a-list-item
                  class="thread-row"
                  :class="{ active: item.id === selectedThreadId, unread: item.unread }"
                  role="button"
                  tabindex="0"
                  :aria-current="item.id === selectedThreadId ? 'true' : undefined"
                  @click="openThread(item.id)"
                  @keydown.enter="openThread(item.id)"
                  @keydown.space.prevent="openThread(item.id)"
                >
                  <a-checkbox
                    class="thread-select"
                    :checked="selectedThreadIdSet.has(item.id)"
                    @click.stop
                    @change="toggleThreadSelection(item.id)"
                  />
                  <div class="thread-row-top">
                    <strong>{{ participantLabel(item) }}</strong>
                    <span>{{ formatDate(item.last_message_at) }}</span>
                  </div>
                  <div class="thread-subject">{{ item.subject || '(No subject)' }}</div>
                  <p>{{ item.snippet }}</p>
                  <div v-if="item.crm_links.length" class="tag-row">
                    <a-tag v-for="link in item.crm_links" :key="link.label_id">
                      {{ threadLinkLabel(link) }}
                    </a-tag>
                  </div>
                </a-list-item>
              </template>
            </a-list>
          </div>
        </a-card>

        <a-card class="thread-detail-card">
          <a-spin :spinning="detailLoading">
            <template v-if="selectedThread">
              <div class="thread-detail-heading">
                <div v-if="selectedThreadHasLinks" class="thread-link-bar">
                  <div class="thread-link-status">
                    <span class="thread-link-label">Linked to</span>
                    <div class="thread-link-tags">
                      <a-tag v-for="link in selectedThread.crm_links" :key="link.label_id">
                        {{ threadLinkLabel(link) }}
                      </a-tag>
                    </div>
                  </div>
                  <a-button @click="openLinkModal">
                    <Pencil class="button-leading-icon" aria-hidden="true" />
                    Edit link
                  </a-button>
                </div>

                <div class="thread-detail-header">
                  <div>
                    <h2>{{ selectedThread.subject || '(No subject)' }}</h2>
                    <p>{{ selectedThread.message_count }} messages</p>
                  </div>
                  <div class="header-actions">
                    <a-button
                      v-if="gmailThreadUrl"
                      :href="gmailThreadUrl"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <svg
                        class="button-leading-icon gmail-icon"
                        viewBox="52 42 88 66"
                        aria-hidden="true"
                      >
                        <path fill="#4285f4" d="M58 108h14V74L52 59v43c0 3.32 2.69 6 6 6" />
                        <path fill="#34a853" d="M120 108h14c3.32 0 6-2.69 6-6V59l-20 15" />
                        <path fill="#fbbc04" d="M120 48v26l20-15v-8c0-7.42-8.47-11.65-14.4-7.2" />
                        <path fill="#ea4335" d="M72 74V48l24 18 24-18v26L96 92" />
                        <path fill="#c5221f" d="M52 51v8l20 15V48l-5.6-4.2c-5.94-4.45-14.4-.22-14.4 7.2" />
                      </svg>
                      Open in Gmail
                    </a-button>
                    <a-button v-if="!selectedThreadHasLinks" type="primary" @click="openLinkModal">
                      <LinkIcon class="button-leading-icon" aria-hidden="true" />
                      {{ linkButtonLabel() }}
                    </a-button>
                    <a-button @click="openComposer('reply')">
                      <Reply class="button-leading-icon" aria-hidden="true" />
                      Reply
                    </a-button>
                    <a-button @click="openComposer('reply_all')">
                      <ReplyAll class="button-leading-icon" aria-hidden="true" />
                      Reply all
                    </a-button>
                  </div>
                </div>
              </div>

              <div class="message-stack">
                <article v-for="mail in selectedThread.messages" :key="mail.id" class="message-card">
                  <header>
                    <div>
                      <strong>{{ mail.sender?.name || mail.sender?.email || 'Unknown sender' }}</strong>
                      <span>{{ mail.sender?.email }}</span>
                    </div>
                    <time>{{ formatDate(mail.sent_at) }}</time>
                  </header>
                  <iframe
                    v-if="mail.body_html"
                    sandbox="allow-same-origin allow-popups allow-popups-to-escape-sandbox"
                    class="html-frame"
                    :data-message-id="mail.id"
                    :style="{ height: `${messageFrameHeights[mail.id] ?? minMessageFrameHeight}px` }"
                    :srcdoc="emailHtmlSrcdoc(displayMessageHtml(mail))"
                    @load="resizeMessageFrame(mail.id, $event)"
                  />
                  <pre v-else-if="mail.body_text">{{ displayMessageText(mail) }}</pre>
                  <p v-else class="muted">{{ mail.snippet || 'No readable message body.' }}</p>
                  <a-button
                    v-if="hasQuotedContent(mail)"
                    class="quoted-toggle"
                    type="link"
                    @click="toggleQuotedText(mail.id)"
                  >
                    {{ quotedTextExpanded(mail.id) ? 'Hide quoted text' : 'Show quoted text' }}
                  </a-button>
                  <div class="message-actions">
                    <a-button size="small" @click="openComposer('reply', mail)">
                      <Reply class="button-leading-icon" aria-hidden="true" />
                      Reply
                    </a-button>
                  </div>
                  <div v-if="composerOpen && composerAnchorMessageId === mail.id" class="reply-composer">
                    <div class="composer-fields">
                      <a-input v-model:value="composerTo" placeholder="To" />
                      <a-input v-model:value="composerCc" placeholder="Cc" />
                      <a-input v-model:value="composerBcc" placeholder="Bcc" />
                      <a-input v-model:value="composerSubject" placeholder="Subject" />
                    </div>
                    <div class="composer-toolbar">
                      <a-button
                        class="icon-button"
                        type="text"
                        title="Bold"
                        aria-label="Bold"
                        @click="composerEditor?.chain().focus().toggleBold().run()"
                      >
                        <Bold aria-hidden="true" />
                      </a-button>
                      <a-button
                        class="icon-button"
                        type="text"
                        title="Italic"
                        aria-label="Italic"
                        @click="composerEditor?.chain().focus().toggleItalic().run()"
                      >
                        <Italic aria-hidden="true" />
                      </a-button>
                      <a-button
                        class="icon-button"
                        type="text"
                        title="Underline"
                        aria-label="Underline"
                        @click="composerEditor?.chain().focus().toggleUnderline().run()"
                      >
                        <UnderlineIcon aria-hidden="true" />
                      </a-button>
                      <a-button
                        class="icon-button"
                        type="text"
                        title="Bulleted list"
                        aria-label="Bulleted list"
                        @click="composerEditor?.chain().focus().toggleBulletList().run()"
                      >
                        <List aria-hidden="true" />
                      </a-button>
                      <a-button
                        class="icon-button"
                        type="text"
                        title="Numbered list"
                        aria-label="Numbered list"
                        @click="composerEditor?.chain().focus().toggleOrderedList().run()"
                      >
                        <ListOrdered aria-hidden="true" />
                      </a-button>
                      <a-button
                        class="icon-button"
                        type="text"
                        title="Link"
                        aria-label="Link"
                        @click="setComposerLink"
                      >
                        <LinkIcon aria-hidden="true" />
                      </a-button>
                      <label class="icon-upload-button" title="Inline image" aria-label="Inline image">
                        <ImageIcon aria-hidden="true" />
                        <input type="file" accept="image/*" multiple @change="handleInlineImageFiles" />
                      </label>
                      <label class="icon-upload-button" title="Attachment" aria-label="Attachment">
                        <Paperclip aria-hidden="true" />
                        <input type="file" multiple @change="handleAttachmentFiles" />
                      </label>
                    </div>
                    <EditorContent class="composer-editor" :editor="composerEditor" />
                    <div v-if="composerAttachments.length" class="attachment-row">
                      <a-tag
                        v-for="(file, index) in composerAttachments"
                        :key="`${file.name}-${index}`"
                        closable
                        @close.prevent="removeAttachment(index)"
                      >
                        {{ file.name }}
                      </a-tag>
                    </div>
                    <div class="composer-footer">
                      <span class="save-status">
                        {{
                          composerSaveStatus === 'saving'
                            ? 'Saving'
                            : composerSaveStatus === 'saved'
                              ? 'Saved'
                              : composerSaveStatus === 'failed'
                                ? 'Save failed'
                                : ''
                        }}
                      </span>
                      <a-space>
                        <a-button danger :disabled="composerSending" @click="discardComposer">
                          <X class="button-leading-icon" aria-hidden="true" />
                          Discard
                        </a-button>
                        <a-button type="primary" :loading="composerSending" @click="sendComposer">
                          <Send class="button-leading-icon" aria-hidden="true" />
                          Send
                        </a-button>
                      </a-space>
                    </div>
                  </div>
                </article>
              </div>
            </template>
            <a-empty v-else description="Select a Gmail thread." />
          </a-spin>
        </a-card>
      </div>
    </template>

    <a-modal
      v-model:open="linkModalOpen"
      :title="linkModalTitle()"
      :confirm-loading="linkSaving"
      :ok-button-props="{ disabled: !linkCampaignId || linkSaving }"
      ok-text="Save link"
      @ok="saveThreadLinks"
      @cancel="cancelLinkModal"
    >
      <a-form layout="vertical">
        <a-form-item label="Campaign" required>
          <a-select
            v-model:value="linkCampaignId"
            show-search
            placeholder="Select campaign"
            :options="campaignOptions"
            :filter-option="true"
            @change="changeLinkCampaign"
          />
        </a-form-item>
        <a-form-item label="Deal">
          <a-select
            v-model:value="linkDealId"
            allow-clear
            show-search
            placeholder="Campaign only"
            :disabled="!linkCampaignId"
            :loading="linkDealsLoading"
            :options="linkDealOptions"
            :filter-option="true"
          />
        </a-form-item>
      </a-form>
      <template #footer>
        <a-button v-if="selectedThreadHasLinks" danger :loading="linkSaving" @click="clearThreadLinks">
          <Trash2 class="button-leading-icon" aria-hidden="true" />
          Clear link
        </a-button>
        <a-button @click="cancelLinkModal">Cancel</a-button>
        <a-button
          type="primary"
          :disabled="!linkCampaignId || linkSaving"
          :loading="linkSaving"
          @click="saveThreadLinks"
        >
          Save link
        </a-button>
      </template>
    </a-modal>
  </section>
</template>

<style scoped>
.email-page {
  display: grid;
  gap: 16px;
  color: #20262d;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-header > div:first-child {
  min-width: 0;
}

.page-header h1,
.thread-detail-header h2 {
  margin: 0;
  color: #20262d;
  line-height: 1.15;
  text-wrap: balance;
}

.page-header p,
.thread-detail-header p,
.thread-row p,
.muted {
  margin: 0;
  color: #697582;
}

.account-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  min-width: 0;
  flex-wrap: wrap;
}

.account-pill {
  max-width: 320px;
  margin-inline-end: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.secondary-action {
  border-color: #d7dee7;
  color: #3c4652;
}

.google-login-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-width: 220px;
  height: 44px;
  padding: 0 18px;
  border: 1px solid #d7dee7;
  border-radius: 8px;
  background: #ffffff;
  color: #263238;
  box-shadow: 0 1px 2px rgb(32 38 45 / 0.08);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  line-height: 1;
  touch-action: manipulation;
  transition:
    background-color 0.16s ease,
    border-color 0.16s ease,
    box-shadow 0.16s ease;
}

.google-login-button:hover:not(:disabled) {
  border-color: #b9c6d3;
  background: #f8fafc;
  box-shadow:
    0 1px 2px rgb(32 38 45 / 0.12),
    0 4px 12px rgb(32 38 45 / 0.08);
}

.google-login-button:focus-visible {
  outline: 2px solid #216b55;
  outline-offset: 2px;
}

.google-login-button:disabled {
  cursor: wait;
  opacity: 0.72;
}

.google-icon {
  display: grid;
  place-items: center;
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
}

.google-icon svg {
  display: block;
  width: 18px;
  height: 18px;
}

.google-auth-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 20px;
  border: 1px solid #e0e5eb;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 2px rgb(32 38 45 / 0.05);
}

.google-auth-panel.reconnect {
  border-color: #f1d4a5;
  background: #fffaf2;
}

.auth-copy {
  display: grid;
  gap: 6px;
  min-width: 0;
  max-width: 720px;
}

.google-auth-panel h2 {
  margin: 0;
  color: #20262d;
  font-size: 18px;
  line-height: 1.25;
}

.google-auth-panel p {
  margin: 0;
  color: #697582;
}

.page-alert {
  margin-top: -4px;
}

.mail-toolbar {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid #dfe6ee;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 2px rgb(32 38 45 / 0.04);
}

.toolbar-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.toolbar-row-primary {
  justify-content: space-between;
}

.toolbar-row-filters {
  flex-wrap: wrap;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  flex: 0 0 auto;
  white-space: nowrap;
}

.thread-range {
  color: #697582;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.mail-view-tabs {
  min-width: 0;
  width: fit-content;
  max-width: 100%;
  overflow-x: auto;
}

.mail-view-tabs :deep(.ant-segmented-group) {
  align-items: center;
}

.query-input {
  width: min(460px, 100%);
  min-width: 260px;
  flex: 1 1 360px;
}

.filter-select {
  width: 210px;
  min-width: 180px;
}

.email-workspace {
  display: grid;
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  gap: 14px;
  align-items: start;
  min-height: 520px;
}

.thread-list-card,
.thread-detail-card {
  min-width: 0;
  overflow: hidden;
  border-color: #dfe6ee;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgb(32 38 45 / 0.04);
}

.thread-list-card {
  height: calc(100vh - 340px);
  min-height: 520px;
}

.thread-list-card :deep(.ant-card-body) {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.thread-detail-card :deep(.ant-card-body) {
  padding: 18px;
}

.thread-detail-header,
.message-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
  flex-shrink: 0;
}

.header-actions :deep(.ant-btn),
.thread-link-bar :deep(.ant-btn) {
  display: inline-flex;
  align-items: center;
}

.thread-detail-heading {
  display: grid;
  gap: 12px;
  margin-bottom: 18px;
}

.thread-link-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid #dbe6df;
  border-radius: 8px;
  background: #f5faf7;
}

.thread-link-status {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.thread-link-label {
  color: #697582;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  text-transform: uppercase;
}

.thread-link-tags {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  min-width: 0;
}

.thread-link-tags :deep(.ant-tag) {
  max-width: 280px;
  margin-inline-end: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.thread-list-header {
  display: block;
  padding: 14px 16px;
  border-bottom: 1px solid #edf0f3;
  background: #fbfcfd;
}

.thread-list-title {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.thread-list-title span {
  color: #697582;
  font-size: 12px;
}

.button-leading-icon {
  width: 16px;
  height: 16px;
  margin-right: 6px;
  vertical-align: -3px;
}

.gmail-icon {
  width: 18px;
  height: 14px;
}

.icon-button {
  width: 32px;
  height: 32px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  border: 0;
  box-shadow: none;
  color: #4f5c68;
}

.icon-button :deep(svg) {
  width: 18px;
  height: 18px;
  stroke-width: 2;
}

.batch-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 48px;
  padding: 8px 16px;
  border-bottom: 1px solid #edf0f3;
  background: #ffffff;
}

.thread-list-scroll {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
}

.thread-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  column-gap: 10px;
  min-height: 104px;
  border-left: 3px solid transparent;
  border-bottom: 1px solid #edf0f3;
  cursor: pointer;
  padding: 13px 16px;
  outline: none;
  transition:
    background-color 0.16s ease,
    border-color 0.16s ease;
}

.thread-row:hover {
  background: #f8fafb;
}

.thread-row:focus-visible {
  box-shadow: inset 0 0 0 2px #216b55;
}

.thread-select {
  grid-row: 1 / span 4;
  padding-top: 2px;
}

.thread-row.unread {
  border-left-color: #216b55;
  background: #f7fbf8;
}

.thread-row.active {
  border-left-color: #216b55;
  background: #edf7f2;
}

.thread-row.active.unread {
  background: #e8f4ef;
}

.thread-row:not(.unread) .thread-row-top strong,
.thread-row:not(.unread) .thread-subject {
  font-weight: 500;
}

.thread-row.unread .thread-row-top strong,
.thread-row.unread .thread-subject {
  font-weight: 800;
}

.thread-row-top {
  grid-column: 2;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
  color: #20262d;
}

.thread-row-top strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.thread-row-top span {
  color: #697582;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.thread-subject {
  grid-column: 2;
  margin-top: 4px;
  overflow: hidden;
  color: #20262d;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.thread-row p,
.thread-row .tag-row {
  grid-column: 2;
}

.thread-row p {
  display: -webkit-box;
  overflow: hidden;
  margin-top: 2px;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow-wrap: anywhere;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.tag-row :deep(.ant-tag) {
  max-width: 100%;
  margin-inline-end: 0;
}

.thread-detail-card {
  height: calc(100vh - 340px);
  min-height: 520px;
  overflow-y: auto;
}

.thread-detail-header {
  align-items: flex-start;
}

.thread-detail-header > div:first-child {
  min-width: 0;
}

.thread-detail-header h2 {
  overflow-wrap: anywhere;
}

.message-stack {
  display: grid;
  gap: 14px;
  margin-top: 16px;
}

.message-card {
  display: grid;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid #e1e7ee;
  border-radius: 8px;
  background: #ffffff;
}

.message-card header div {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.message-card header strong,
.message-card header span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-card header span,
.message-card time {
  color: #697582;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.message-card pre {
  margin: 0;
  overflow-x: auto;
  color: #20262d;
  font-family: inherit;
  line-height: 1.55;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.quoted-toggle {
  width: fit-content;
  height: auto;
  padding: 0;
}

.message-actions {
  display: flex;
  justify-content: flex-end;
}

.html-frame {
  width: 100%;
  max-height: 520px;
  border: 1px solid #e8edf2;
  border-radius: 8px;
  background: #ffffff;
}

.reply-composer {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid #d7dee7;
  border-radius: 8px;
  background: #fbfcfd;
}

.composer-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.composer-toolbar,
.composer-footer,
.attachment-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.composer-footer {
  justify-content: space-between;
}

.icon-upload-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: #4f5c68;
  cursor: pointer;
}

.icon-upload-button svg {
  width: 18px;
  height: 18px;
}

.icon-upload-button input {
  display: none;
}

.composer-editor {
  min-height: 160px;
  padding: 10px 12px;
  border: 1px solid #dfe6ee;
  border-radius: 8px;
  background: #ffffff;
}

.composer-editor :deep(.ProseMirror) {
  min-height: 138px;
  outline: none;
  overflow-wrap: anywhere;
}

.composer-editor :deep(img) {
  max-width: 100%;
  height: auto;
}

.save-status {
  min-width: 76px;
  color: #697582;
  font-size: 12px;
}

@media (max-width: 1100px) {
  .toolbar-row,
  .toolbar-row-primary {
    align-items: stretch;
    flex-direction: column;
  }

  .toolbar-actions {
    justify-content: space-between;
    width: 100%;
  }

  .email-workspace {
    grid-template-columns: 1fr;
  }

  .filter-select,
  .query-input {
    width: 100%;
  }

  .mail-view-tabs {
    width: 100%;
  }

  .mail-view-tabs :deep(.ant-segmented) {
    width: 100%;
  }

  .thread-list-card {
    height: 560px;
    min-height: 0;
  }

  .thread-list-scroll {
    height: 446px;
    min-height: 0;
  }

  .batch-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .page-header,
  .google-auth-panel {
    align-items: flex-start;
    flex-direction: column;
  }

  .account-actions {
    justify-content: flex-start;
    width: 100%;
  }

  .google-login-button {
    width: 100%;
  }
}

@media (max-width: 720px) {
  .page-header {
    gap: 12px;
  }

  .mail-toolbar,
  .google-auth-panel {
    padding: 14px;
  }

  .thread-detail-header,
  .message-card header {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-actions {
    justify-content: flex-start;
    width: 100%;
  }

  .header-actions :deep(.ant-btn) {
    width: 100%;
    justify-content: center;
  }

  .composer-fields {
    grid-template-columns: 1fr;
  }

  .thread-list-card {
    height: 520px;
  }

  .thread-list-scroll {
    height: 406px;
  }
}
</style>

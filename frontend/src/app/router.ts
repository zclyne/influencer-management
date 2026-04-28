import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import CampaignList from '../campaigns/CampaignList.vue'
import CampaignWorkspace from '../campaigns/CampaignWorkspace.vue'
import ImportWizard from '../ingestion/ImportWizard.vue'
import InfluencerLibrary from '../influencers/InfluencerLibrary.vue'
import PlaceholderPage from './PlaceholderPage.vue'

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/campaigns',
  },
  {
    path: '/campaigns',
    name: 'campaigns',
    component: CampaignList,
  },
  {
    path: '/campaigns/:campaignId',
    name: 'campaignWorkspace',
    component: CampaignWorkspace,
  },
  {
    path: '/campaigns/:campaignId/deals/:dealId',
    name: 'dealDetail',
    component: PlaceholderPage,
    props: {
      title: 'Deal detail',
      description: 'Deal detail will use the shared influencer profile and campaign deal context.',
    },
  },
  {
    path: '/influencers',
    name: 'influencers',
    component: InfluencerLibrary,
    meta: {
      campaignContext: true,
    },
  },
  {
    path: '/influencers/import',
    name: 'influencerImport',
    component: ImportWizard,
    meta: {
      campaignContext: true,
    },
  },
  {
    path: '/influencers/:influencerId',
    name: 'influencerDetail',
    component: PlaceholderPage,
    props: {
      title: 'Influencer detail',
      description: 'Global profile, platforms, contacts, and audience snapshots will load here.',
    },
  },
  {
    path: '/brands',
    name: 'brands',
    component: PlaceholderPage,
    props: {
      title: 'Brands',
      description: 'Brand records and campaign associations will be managed here.',
    },
  },
  {
    path: '/templates',
    name: 'templates',
    component: PlaceholderPage,
    props: {
      title: 'Templates',
      description: 'Reusable briefs, outreach, contracts, reports, and summaries will be managed here.',
    },
  },
  {
    path: '/email',
    name: 'email',
    component: PlaceholderPage,
    props: {
      title: 'Email',
      description: 'Email is reserved while the standalone workflow is redesigned.',
    },
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import BrandList from '../brands/BrandList.vue'
import CampaignList from '../campaigns/CampaignList.vue'
import CampaignWorkspace from '../campaigns/CampaignWorkspace.vue'
import DealDetailPage from '../deals/DealDetailPage.vue'
import EmailPage from '../email/EmailPage.vue'
import ImportWizard from '../ingestion/ImportWizard.vue'
import InfluencerDetailPage from '../influencers/InfluencerDetailPage.vue'
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
    component: DealDetailPage,
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
    component: InfluencerDetailPage,
  },
  {
    path: '/brands',
    name: 'brands',
    component: BrandList,
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
    component: EmailPage,
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

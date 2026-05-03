export type NavigationKey = 'campaigns' | 'influencers' | 'brands' | 'email' | 'templates'

export interface NavigationItem {
  key: NavigationKey
  label: string
  detail: string
  path: string
}

export const navigationItems: NavigationItem[] = [
  {
    key: 'campaigns',
    label: 'Campaigns',
    detail: 'List',
    path: '/campaigns',
  },
  {
    key: 'influencers',
    label: 'Influencers',
    detail: 'Library',
    path: '/influencers',
  },
  {
    key: 'brands',
    label: 'Brands',
    detail: 'Accounts',
    path: '/brands',
  },
  {
    key: 'email',
    label: 'Email',
    detail: 'Gmail',
    path: '/email',
  },
  {
    key: 'templates',
    label: 'Templates',
    detail: 'Docs',
    path: '/templates',
  },
]

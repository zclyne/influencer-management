export type WorkbenchView = 'campaigns' | 'influencers' | 'imports'

export interface NavigationItem {
  key: WorkbenchView
  label: string
  detail: string
}

export const navigationItems: NavigationItem[] = [
  {
    key: 'campaigns',
    label: 'Campaigns',
    detail: 'Workspace',
  },
  {
    key: 'influencers',
    label: 'Influencers',
    detail: 'Library',
  },
  {
    key: 'imports',
    label: 'Imports',
    detail: 'Modash CSV',
  },
]

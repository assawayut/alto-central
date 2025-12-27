import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { SiteMap } from '@/pages/SiteMap'
import { ChillerPlant } from '@/pages/ChillerPlant'

const router = createBrowserRouter([
  {
    path: '/',
    element: <SiteMap />,
  },
  {
    path: '/site/:siteId',
    element: <ChillerPlant />,
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}

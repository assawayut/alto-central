/**
 * Auth feature - Mock implementation
 */

export interface Site {
  id: string;
  name: string;
  timezone: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
}

const mockSite: Site = {
  id: 'jwm-bangkok',
  name: 'JW Marriott Bangkok',
  timezone: 'Asia/Bangkok',
};

export function useAuth() {
  return {
    site: mockSite,
    user: { id: '1', name: 'Admin', email: 'admin@alto.com' },
    isAuthenticated: true,
  };
}

export function getSiteId(): string {
  return mockSite.id;
}

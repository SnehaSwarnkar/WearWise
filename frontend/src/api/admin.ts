import { getCsrfToken, getStoreApiBase } from './client';

function buildHeaders(method: string, extra?: Record<string, string>) {
  const headers: Record<string, string> = { ...(extra || {}) };
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase())) {
    const csrf = getCsrfToken();
    if (csrf && !headers['X-CSRF-Token']) {
      headers['X-CSRF-Token'] = csrf;
    }
  }
  return headers;
}

async function adminRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method || 'GET').toUpperCase();
  const res = await fetch(`${getStoreApiBase()}/api/admin${path}`, {
    ...options,
    credentials: 'include',
    headers: buildHeaders(method, (options.headers as Record<string, string>) || {}),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const msg = typeof err?.detail === 'string' ? err.detail : err?.detail?.message || 'Admin request failed';
    throw new Error(msg);
  }
  return res.json();
}

export interface AdminOverviewMetrics {
  total_customers: number;
  active_customers: number;
  total_sellers: number;
  pending_seller_applications: number;
  approved_sellers: number;
  rejected_sellers: number;
  suspended_sellers: number;
  total_products: number;
  active_products: number;
  total_orders: number;
  simulated_order_volume: number;
  is_demo_payments_only: boolean;
  actual_captured_revenue: number;
}

export interface AdminOverview {
  admin?: Record<string, unknown>;
  metrics: AdminOverviewMetrics;
  recent_pending_sellers?: AdminSellerRecord[];
  recent_orders?: any[];
}

export interface AdminSellerRecord {
  id: string;
  name: string;
  owner_name?: string;
  email: string;
  phone?: string;
  store_name?: string;
  business_type?: string;
  business_address?: string;
  store_description?: string;
  status: 'pending' | 'active' | 'rejected' | 'suspended' | string;
  seller_approved: boolean;
  is_active: boolean;
  rejection_reason?: string | null;
  verified_at?: string | null;
  createdAt?: string | null;
}

export interface AdminProductRecord {
  id: number | string;
  sku?: string;
  name: string;
  category?: string;
  gender?: string;
  price?: number;
  seller_id?: string | null;
  seller_name?: string | null;
  status?: string;
  available?: boolean;
  inventory_count?: number;
  moderation_status?: string;
  moderation_reason?: string | null;
}

export interface AdminAuditLog {
  id: string;
  admin_email: string;
  action: string;
  target_type: string;
  target_id: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

export const fetchAdminOverview = () => adminRequest<AdminOverview>('/overview');

export const fetchAdminSellers = async (statusFilter?: string): Promise<AdminSellerRecord[]> => {
  const qs = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : '';
  const res = await adminRequest<{ sellers?: AdminSellerRecord[] } | AdminSellerRecord[]>(`/sellers${qs}`);
  return Array.isArray(res) ? res : res.sellers || [];
};

export const updateAdminSellerStatus = (
  sellerId: string,
  payload: { status: 'active' | 'rejected' | 'suspended' | 'pending'; reason?: string }
) =>
  adminRequest<AdminSellerRecord>(`/sellers/${encodeURIComponent(sellerId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

export const fetchAdminProducts = async (statusFilter?: string): Promise<AdminProductRecord[]> => {
  const qs = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : '';
  const res = await adminRequest<{ products?: AdminProductRecord[] } | AdminProductRecord[]>(`/products${qs}`);
  return Array.isArray(res) ? res : res.products || [];
};

export const moderateAdminProduct = (
  productId: string | number,
  payload: { moderation_status: 'active' | 'disabled' | 'removed'; reason?: string }
) =>
  adminRequest<Record<string, unknown>>(`/products/${encodeURIComponent(String(productId))}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

export const fetchAdminOrders = async (): Promise<any[]> => {
  const res = await adminRequest<{ orders?: any[] } | any[]>('/orders');
  return Array.isArray(res) ? res : res.orders || [];
};

export const fetchAdminCustomers = async (): Promise<any[]> => {
  const res = await adminRequest<{ customers?: any[] } | any[]>('/customers');
  return Array.isArray(res) ? res : res.customers || [];
};

export const updateAdminCustomerStatus = (customerId: string, active: boolean) =>
  adminRequest<Record<string, unknown>>(
    `/customers/${encodeURIComponent(customerId)}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: active ? 'active' : 'suspended' }),
    }
  );

export const fetchAdminHealth = () => adminRequest<Record<string, unknown>>('/health');

export const fetchAdminAuditLogs = async (): Promise<AdminAuditLog[]> => {
  const res = await adminRequest<{ logs?: AdminAuditLog[] } | AdminAuditLog[]>('/audit-logs');
  return Array.isArray(res) ? res : res.logs || [];
};

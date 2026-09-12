import { Account, CustomerInteraction, KnowledgeItem, PaginatedInteractions } from '@/types/pipeline';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchInboxMessages(params?: {
  platform?: string;
  status?: string;
  risk_only?: boolean;
  search?: string;
  page?: number;
  limit?: number;
}): Promise<PaginatedInteractions> {
  const query = new URLSearchParams();
  if (params?.platform && params.platform !== 'ALL') query.set('platform', params.platform);
  if (params?.status && params.status !== 'ALL') query.set('status', params.status);
  if (params?.risk_only) query.set('risk_only', 'true');
  if (params?.search) query.set('search', params.search);
  if (params?.page) query.set('page', params.page.toString());
  if (params?.limit) query.set('limit', params.limit.toString());

  const res = await fetch(`${API_BASE_URL}/api/inbox/messages?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch inbox messages');
  return res.json();
}

export async function fetchAccounts(): Promise<Account[]> {
  const res = await fetch(`${API_BASE_URL}/api/accounts`);
  if (!res.ok) throw new Error('Failed to fetch accounts');
  return res.json();
}

export async function resetAccount(accountId: string): Promise<Account> {
  const res = await fetch(`${API_BASE_URL}/api/accounts/${accountId}/reset`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to reset account');
  return res.json();
}

export async function triggerMetaWebhook(payload: {
  account_id?: string;
  sender_name: string;
  message_body: string;
  interaction_type?: string;
}) {
  const res = await fetch(`${API_BASE_URL}/api/webhooks/meta`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to ingest Meta webhook');
  return res.json();
}

export async function triggerShopifyWebhook(payload: {
  topic?: string;
  account_id?: string;
  sender_name: string;
  message_body?: string;
  cart_value?: number;
  abandoned_items?: string[];
}) {
  const res = await fetch(`${API_BASE_URL}/api/webhooks/shopify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to ingest Shopify webhook');
  return res.json();
}

export async function sendManualReply(interactionId: string, replyBody: string): Promise<CustomerInteraction> {
  const cleanId = encodeURIComponent(interactionId);
  const res = await fetch(`${API_BASE_URL}/api/inbox/messages/${cleanId}/reply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reply_body: replyBody }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to send manual reply (HTTP ${res.status})`);
  }
  return res.json();
}

export async function clearInboxMessages(): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/inbox/messages`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to clear inbox');
}

export async function fetchKnowledgeItems(): Promise<KnowledgeItem[]> {
  const res = await fetch(`${API_BASE_URL}/api/ai/knowledge`);
  if (!res.ok) throw new Error('Failed to fetch knowledge base');
  return res.json();
}

export async function createKnowledgeItem(item: {
  product_name: string;
  category: string;
  context_text: string;
}): Promise<KnowledgeItem> {
  const res = await fetch(`${API_BASE_URL}/api/ai/knowledge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item),
  });
  if (!res.ok) throw new Error('Failed to create knowledge item');
  return res.json();
}

export async function dispatchCampaign(campaign: {
  account_id: string;
  campaign_name: string;
  platform: string;
  template_message: string;
  recipients: Array<{ recipient_id: string; recipient_name: string; custom_message?: string }>;
  pacing_delay_ms?: number;
}) {
  const res = await fetch(`${API_BASE_URL}/api/campaigns/dispatch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(campaign),
  });
  if (!res.ok) throw new Error('Failed to dispatch campaign');
  return res.json();
}

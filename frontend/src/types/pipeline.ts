export type Platform = 'INSTAGRAM' | 'SHOPIFY';

export type InteractionStatus = 'QUEUED' | 'PROCESSING' | 'SENT' | 'FAILED';

export type Sentiment = 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE' | 'URGENT';

export interface CustomerInteraction {
  id: string;
  account_id: string;
  platform: Platform;
  sender_id: string;
  sender_name: string;
  message_body: string;
  interaction_type: string;
  status: InteractionStatus;
  sentiment: Sentiment;
  risk_score: number;
  risk_flag: boolean;
  risk_reason?: string | null;
  ai_reply?: string | null;
  rag_sources: string[];
  raw_payload?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Account {
  id: string;
  platform: Platform;
  handle: string;
  name: string;
  daily_limit: number;
  sent_today: number;
  risk_score: number;
  health_status: 'HEALTHY' | 'WARNING' | 'RESTRICTED';
  last_sent_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeItem {
  id: string;
  product_name: string;
  category: string;
  context_text: string;
  created_at: string;
}

export interface PaginatedInteractions {
  items: CustomerInteraction[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

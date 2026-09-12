'use client';

import React, { useState } from 'react';
import {
  Search,
  Filter,
  RefreshCw,
  Trash2,
  Send,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Sparkles,
  User,
  ShieldCheck,
  BookOpen,
  MessageSquare,
  Bot
} from 'lucide-react';
import { InstagramIcon, ShopifyIcon } from '@/components/Icons';
import { CustomerInteraction, Platform, InteractionStatus } from '@/types/pipeline';
import { sendManualReply, clearInboxMessages } from '@/lib/api';

interface InboxViewProps {
  interactions: CustomerInteraction[];
  onRefresh: () => void;
  onSelectInteraction: (interaction: CustomerInteraction) => void;
  selectedInteraction: CustomerInteraction | null;
  onInteractionUpdated: (interaction: CustomerInteraction) => void;
}

export const InboxView: React.FC<InboxViewProps> = ({
  interactions,
  onRefresh,
  onSelectInteraction,
  selectedInteraction,
  onInteractionUpdated,
}) => {
  const [platformFilter, setPlatformFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [riskOnly, setRiskOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [replyText, setReplyText] = useState<string>('');
  const [isSendingReply, setIsSendingReply] = useState<boolean>(false);

  // Client-side filtering
  const filteredInteractions = interactions.filter((item) => {
    if (platformFilter !== 'ALL' && item.platform !== platformFilter) return false;
    if (statusFilter !== 'ALL' && item.status !== statusFilter) return false;
    if (riskOnly && !item.risk_flag) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchMsg = item.message_body?.toLowerCase().includes(q);
      const matchSender = item.sender_name?.toLowerCase().includes(q);
      const matchReply = item.ai_reply?.toLowerCase().includes(q);
      if (!matchMsg && !matchSender && !matchReply) return false;
    }
    return true;
  });

  const handleManualReply = async () => {
    const targetId = selectedInteraction?.id || (selectedInteraction as unknown as { _id?: string })?._id;
    if (!targetId || !replyText.trim()) return;
    setIsSendingReply(true);
    try {
      const updated = await sendManualReply(targetId, replyText);
      onInteractionUpdated(updated);
      setReplyText('');
    } catch (e: unknown) {
      console.error('Error sending manual reply:', e);
      const errMsg = e instanceof Error ? e.message : 'Failed to send reply. Please refresh your inbox.';
      alert(errMsg);
    } finally {
      setIsSendingReply(false);
    }
  };

  const handleClearAll = async () => {
    if (confirm('Clear all messages in the inbox? This will reset test interactions.')) {
      await clearInboxMessages();
      onRefresh();
    }
  };

  const getStatusBadge = (status: InteractionStatus) => {
    switch (status) {
      case 'QUEUED':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-300">
            <Clock className="w-3 h-3 mr-1 animate-spin" />
            QUEUED
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-cyan-50 text-cyan-800 border border-cyan-300">
            <Sparkles className="w-3 h-3 mr-1 animate-pulse" />
            PROCESSING (RAG)
          </span>
        );
      case 'SENT':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            SENT
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-rose-50 text-rose-800 border border-rose-300">
            <AlertTriangle className="w-3 h-3 mr-1" />
            THROTTLED / FAILED
          </span>
        );
    }
  };

  const getSentimentBadge = (sentiment: string) => {
    switch (sentiment) {
      case 'POSITIVE':
        return (
          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-800 border border-zinc-200">
            Positive
          </span>
        );
      case 'URGENT':
        return (
          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
            Urgent
          </span>
        );
      case 'NEGATIVE':
        return (
          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200">
            Negative / Risk
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-700 border border-zinc-200">
            Neutral
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-white">
      {/* Search & Filter Toolbar */}
      <div className="bg-white border-b border-zinc-200 p-4 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Platform Tabs */}
          <div className="flex items-center space-x-1 bg-zinc-100 p-1 rounded-lg border border-zinc-200">
            <button
              onClick={() => setPlatformFilter('ALL')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                platformFilter === 'ALL'
                  ? 'bg-white text-zinc-900 shadow-xs border border-zinc-200 font-semibold'
                  : 'text-zinc-600 hover:text-zinc-900'
              }`}
            >
              All Platforms
            </button>
            <button
              onClick={() => setPlatformFilter('INSTAGRAM')}
              className={`flex items-center space-x-1.5 px-3 py-1 text-xs font-medium rounded-md transition-all ${
                platformFilter === 'INSTAGRAM'
                  ? 'bg-white text-zinc-900 shadow-xs border border-zinc-200 font-semibold'
                  : 'text-zinc-600 hover:text-zinc-900'
              }`}
            >
              <InstagramIcon className="w-3.5 h-3.5 text-zinc-700" />
              <span>Instagram</span>
            </button>
            <button
              onClick={() => setPlatformFilter('SHOPIFY')}
              className={`flex items-center space-x-1.5 px-3 py-1 text-xs font-medium rounded-md transition-all ${
                platformFilter === 'SHOPIFY'
                  ? 'bg-white text-zinc-900 shadow-xs border border-zinc-200 font-semibold'
                  : 'text-zinc-600 hover:text-zinc-900'
              }`}
            >
              <ShopifyIcon className="w-3.5 h-3.5 text-zinc-700" />
              <span>Shopify</span>
            </button>
          </div>

          {/* Status Dropdown */}
          <div className="flex items-center space-x-2">
            <Filter className="w-3.5 h-3.5 text-zinc-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs bg-white border border-zinc-300 rounded-lg px-2.5 py-1.5 text-zinc-800 shadow-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="QUEUED">Queued</option>
              <option value="PROCESSING">Processing</option>
              <option value="SENT">Sent</option>
              <option value="FAILED">Throttled / Failed</option>
            </select>

            {/* High-Risk Checkbox */}
            <label className="flex items-center space-x-1.5 text-xs text-zinc-700 cursor-pointer ml-2">
              <input
                type="checkbox"
                checked={riskOnly}
                onChange={(e) => setRiskOnly(e.target.checked)}
                className="rounded border-zinc-300 text-rose-600 focus:ring-rose-500"
              />
              <span className="font-medium text-rose-600">
                Risk Flagged Only
              </span>
            </label>
          </div>

          {/* Search Box */}
          <div className="relative flex-1 min-w-[200px] max-w-xs">
            <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-zinc-300 rounded-lg text-zinc-800 shadow-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
            />
          </div>

          {/* Toolbar Actions */}
          <div className="flex items-center space-x-2">
            <button
              onClick={onRefresh}
              title="Refresh Inbox"
              className="p-1.5 text-zinc-500 hover:text-zinc-900 rounded-lg hover:bg-zinc-100 border border-zinc-200 transition-colors shadow-xs"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={handleClearAll}
              title="Clear Inbox"
              className="p-1.5 text-zinc-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 border border-zinc-200 transition-colors shadow-xs"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Split Content Area */}
      <div className="flex-1 grid grid-cols-12 overflow-hidden bg-white">
        {/* Left Column: Messages List */}
        <div className="col-span-12 md:col-span-5 lg:col-span-5 border-r border-zinc-200 overflow-y-auto bg-white">
          {filteredInteractions.length === 0 ? (
            <div className="p-8 text-center text-zinc-400">
              <MessageSquare className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="font-medium text-sm">No interactions found</p>
              <p className="text-xs mt-1">
                Trigger a simulated webhook from the simulator tab to test the pipeline.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-zinc-200">
              {filteredInteractions.map((item) => {
                const isSelected = selectedInteraction?.id === item.id;
                return (
                  <div
                    key={item.id}
                    onClick={() => onSelectInteraction(item)}
                    className={`p-4 cursor-pointer transition-all border-b border-zinc-100 ${
                      isSelected
                        ? 'bg-zinc-50 border-l-4 border-cyan-600 shadow-xs'
                        : 'bg-white hover:bg-zinc-50/70'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="p-1.5 rounded-lg bg-zinc-100 border border-zinc-200 text-zinc-700">
                          {item.platform === 'INSTAGRAM' ? (
                            <InstagramIcon className="w-3.5 h-3.5" />
                          ) : (
                            <ShopifyIcon className="w-3.5 h-3.5" />
                          )}
                        </div>
                        <div>
                          <span className="font-semibold text-xs text-zinc-900">
                            {item.sender_name}
                          </span>
                          <span className="text-[10px] text-zinc-400 ml-2">
                            {new Date(item.created_at).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-1.5">
                        {getStatusBadge(item.status)}
                      </div>
                    </div>

                    <p className="mt-2 text-xs text-zinc-700 line-clamp-2 leading-relaxed">
                      {item.message_body}
                    </p>

                    <div className="mt-2.5 flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-1.5">
                        {getSentimentBadge(item.sentiment)}
                        {item.interaction_type && (
                          <span className="text-[10px] text-zinc-600 bg-zinc-100 border border-zinc-200 px-1.5 py-0.5 rounded font-mono">
                            {item.interaction_type}
                          </span>
                        )}
                      </div>

                      {item.risk_flag ? (
                        <span className="inline-flex items-center text-[10px] font-semibold text-rose-600">
                          <AlertTriangle className="w-3 h-3 mr-0.5" />
                          Risk: {item.risk_score}%
                        </span>
                      ) : (
                        <span className="text-[10px] text-zinc-400">
                          Risk: {item.risk_score}%
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Active Conversation & Detail Panel */}
        <div className="col-span-12 md:col-span-7 lg:col-span-7 flex flex-col h-full bg-white overflow-y-auto">
          {selectedInteraction ? (
            <div className="flex flex-col h-full bg-white">
              {/* Thread Header */}
              <div className="p-4 border-b border-zinc-200 flex items-center justify-between bg-white shadow-xs">
                <div className="flex items-center space-x-3">
                  <div className="h-9 w-9 rounded-lg bg-zinc-100 border border-zinc-200 flex items-center justify-center text-zinc-700">
                    <User className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm text-zinc-900">
                      {selectedInteraction.sender_name}
                    </h3>
                    <p className="text-xs text-zinc-500 flex items-center space-x-1">
                      <span>Platform: {selectedInteraction.platform}</span>
                      <span>•</span>
                      <span>ID: {selectedInteraction.id}</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {getStatusBadge(selectedInteraction.status)}
                </div>
              </div>

              {/* Thread Message Body */}
              <div className="flex-1 p-6 space-y-6 overflow-y-auto bg-white">
                {/* 1. Inbound Customer Message Bubble */}
                <div className="bg-white p-4 rounded-xl border border-zinc-200 shadow-sm">
                  <div className="flex items-center space-x-2 mb-1.5">
                    <span className="text-xs font-semibold text-zinc-600 uppercase tracking-wider text-[11px]">
                      Inbound Customer Message
                    </span>
                    <span className="text-[10px] text-zinc-400">
                      {new Date(selectedInteraction.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="text-zinc-800 text-sm leading-relaxed">
                    {selectedInteraction.message_body}
                  </div>
                </div>

                {/* 2. Account Health & Risk Assessment Alert */}
                {selectedInteraction.risk_flag ? (
                  <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start space-x-2.5 shadow-xs">
                    <AlertTriangle className="w-4 h-4 mt-0.5 text-rose-600 shrink-0" />
                    <div>
                      <span className="font-semibold">Safety Shield Triggered:</span>{' '}
                      {selectedInteraction.risk_reason || 'Account risk score elevated or daily quota reached.'}
                    </div>
                  </div>
                ) : (
                  <div className="p-3 rounded-xl bg-white border border-zinc-200 shadow-xs text-xs text-zinc-700 flex items-center space-x-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>Account Health: Safe (Risk Score: {selectedInteraction.risk_score}%)</span>
                  </div>
                )}

                {/* 3. RAG Grounding Sources */}
                {selectedInteraction.rag_sources && selectedInteraction.rag_sources.length > 0 && (
                  <div className="p-4 rounded-xl bg-white border border-zinc-200 shadow-sm text-xs">
                    <div className="flex items-center space-x-1.5 font-semibold text-zinc-800 mb-2">
                      <BookOpen className="w-3.5 h-3.5 text-cyan-600" />
                      <span>Verified Knowledge Base Citations (RAG)</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedInteraction.rag_sources.map((source, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 bg-zinc-50 text-zinc-700 rounded-md border border-zinc-200 text-[11px] font-medium shadow-xs"
                        >
                          {source}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 4. AI Generated Response Bubble */}
                <div className="bg-white p-4 rounded-xl border border-zinc-200 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-1.5 text-xs font-semibold text-cyan-700">
                      <Bot className="w-3.5 h-3.5" />
                      <span>CleanDesk AI Brand Concierge</span>
                    </div>
                    {selectedInteraction.status === 'SENT' && (
                      <span className="text-[10px] text-zinc-400">Dispatched via Redis Paced Queue</span>
                    )}
                  </div>

                  {selectedInteraction.ai_reply ? (
                    <div className="p-3 rounded-lg bg-zinc-50 text-zinc-900 text-sm leading-relaxed border border-zinc-200">
                      {selectedInteraction.ai_reply}
                    </div>
                  ) : selectedInteraction.status === 'FAILED' ? (
                    <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700">
                      Automated dispatch was blocked by the safety engine to protect your account. You can manually review and reply below.
                    </div>
                  ) : (
                    <div className="p-6 rounded-lg bg-zinc-50 border border-zinc-200 text-center text-xs text-zinc-500">
                      <Sparkles className="w-5 h-5 mx-auto mb-1.5 text-cyan-600 animate-spin" />
                      Queue worker is retrieving verified RAG context and synthesizing Gemini reply...
                    </div>
                  )}
                </div>
              </div>

              {/* 5. Manual Reply Action Footer */}
              <div className="p-4 border-t border-zinc-200 bg-white shadow-xs">
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="Type a human agent manual reply or override..."
                    className="flex-1 px-3.5 py-2 text-xs bg-white border border-zinc-300 rounded-lg text-zinc-900 shadow-xs focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleManualReply();
                    }}
                  />
                  <button
                    onClick={handleManualReply}
                    disabled={isSendingReply || !replyText.trim()}
                    className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-sm"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Send</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-zinc-400">
              <MessageSquare className="w-12 h-12 mb-3 opacity-20" />
              <p className="text-sm font-semibold text-zinc-700">
                No conversation selected
              </p>
              <p className="text-xs text-zinc-500 max-w-sm mt-1">
                Select an interaction from the inbox list on the left to inspect its live status, RAG sources, and brand reply.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

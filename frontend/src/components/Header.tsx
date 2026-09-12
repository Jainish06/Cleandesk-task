'use client';

import React from 'react';
import { Radio, ShieldAlert, Sparkles } from 'lucide-react';
import { InstagramIcon, ShopifyIcon } from '@/components/Icons';
import { Account } from '@/types/pipeline';

interface HeaderProps {
  activeTab: 'inbox' | 'simulator' | 'health' | 'campaigns' | 'knowledge';
  setActiveTab: (tab: 'inbox' | 'simulator' | 'health' | 'campaigns' | 'knowledge') => void;
  isConnected: boolean;
  accounts: Account[];
  unreadCount?: number;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  isConnected,
  accounts,
  unreadCount = 0,
}) => {
  const igAccount = accounts.find((a) => a.platform === 'INSTAGRAM');
  const shopifyAccount = accounts.find((a) => a.platform === 'SHOPIFY');

  return (
    <header className="border-b border-zinc-200 bg-white sticky top-0 z-50 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-cyan-600 flex items-center justify-center text-white shadow-sm">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-zinc-900 tracking-tight">
                  CleanDesk
                </span>
                <span className="text-xs px-2 py-0.5 rounded-md bg-zinc-100 text-zinc-700 font-medium border border-zinc-200">
                  Event Pipeline
                </span>
              </div>
              <p className="text-xs text-zinc-500">
                Multi-Platform Messaging & AI Response Hub
              </p>
            </div>
          </div>

          {/* Account Health Quick Chips */}
          <div className="hidden lg:flex items-center space-x-3">
            {igAccount && (
              <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-white border border-zinc-200 shadow-xs text-xs">
                <InstagramIcon className="h-3.5 w-3.5 text-zinc-700" />
                <span className="font-medium text-zinc-700">
                  {igAccount.handle}
                </span>
                <span className="text-zinc-300">|</span>
                <span className="text-zinc-600 font-mono">
                  {igAccount.sent_today}/{igAccount.daily_limit}
                </span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                    igAccount.risk_score >= 80
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : 'bg-zinc-50 text-zinc-700 border-zinc-200'
                  }`}
                >
                  Risk: {igAccount.risk_score}%
                </span>
              </div>
            )}

            {shopifyAccount && (
              <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-white border border-zinc-200 shadow-xs text-xs">
                <ShopifyIcon className="h-3.5 w-3.5 text-zinc-700" />
                <span className="font-medium text-zinc-700">
                  Shopify Store
                </span>
                <span className="text-zinc-300">|</span>
                <span className="text-zinc-600 font-mono">
                  {shopifyAccount.sent_today}/{shopifyAccount.daily_limit}
                </span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                    shopifyAccount.risk_score >= 80
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : 'bg-zinc-50 text-zinc-700 border-zinc-200'
                  }`}
                >
                  Risk: {shopifyAccount.risk_score}%
                </span>
              </div>
            )}
          </div>

          {/* WebSocket Status Indicator */}
          <div className="flex items-center space-x-3">
            <div
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium border shadow-xs ${
                isConnected
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                }`}
              />
              <span>{isConnected ? 'Live WebSocket' : 'Connecting...'}</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 border-t border-zinc-200 -mb-px overflow-x-auto">
          <button
            onClick={() => setActiveTab('inbox')}
            className={`flex items-center space-x-2 py-3 px-4 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
              activeTab === 'inbox'
                ? 'border-cyan-600 text-cyan-600'
                : 'border-transparent text-zinc-600 hover:text-zinc-900'
            }`}
          >
            <span>Universal Inbox</span>
            {unreadCount > 0 && (
              <span className="ml-1.5 px-1.5 py-0.5 rounded-full text-xs bg-cyan-100 text-cyan-800 font-semibold">
                {unreadCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('simulator')}
            className={`flex items-center space-x-2 py-3 px-4 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
              activeTab === 'simulator'
                ? 'border-cyan-600 text-cyan-600'
                : 'border-transparent text-zinc-600 hover:text-zinc-900'
            }`}
          >
            <span>Webhook Simulator</span>
            <span className="px-1.5 py-0.5 text-[10px] rounded bg-zinc-100 text-zinc-700 font-semibold border border-zinc-200">
              Test Bench
            </span>
          </button>

          <button
            onClick={() => setActiveTab('health')}
            className={`flex items-center space-x-2 py-3 px-4 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
              activeTab === 'health'
                ? 'border-cyan-600 text-cyan-600'
                : 'border-transparent text-zinc-600 hover:text-zinc-900'
            }`}
          >
            <ShieldAlert className="h-4 w-4" />
            <span>Account Health & Risk</span>
          </button>

          <button
            onClick={() => setActiveTab('campaigns')}
            className={`flex items-center space-x-2 py-3 px-4 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
              activeTab === 'campaigns'
                ? 'border-cyan-600 text-cyan-600'
                : 'border-transparent text-zinc-600 hover:text-zinc-900'
            }`}
          >
            <Radio className="h-4 w-4" />
            <span>Campaign Dispatcher</span>
          </button>

          <button
            onClick={() => setActiveTab('knowledge')}
            className={`flex items-center space-x-2 py-3 px-4 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
              activeTab === 'knowledge'
                ? 'border-cyan-600 text-cyan-600'
                : 'border-transparent text-zinc-600 hover:text-zinc-900'
            }`}
          >
            <span>Product Knowledge (RAG)</span>
          </button>
        </div>
      </div>
    </header>
  );
};

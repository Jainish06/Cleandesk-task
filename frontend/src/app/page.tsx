'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Header } from '@/components/Header';
import { InboxView } from '@/components/Inbox/InboxView';
import { WebhookSimulator } from '@/components/Simulator/WebhookSimulator';
import { AccountHealthView } from '@/components/AccountHealth/AccountHealthView';
import { CampaignView } from '@/components/Campaigns/CampaignView';
import { KnowledgeBaseView } from '@/components/KnowledgeBase/KnowledgeBaseView';
import { Account, CustomerInteraction } from '@/types/pipeline';
import { fetchAccounts, fetchInboxMessages } from '@/lib/api';
import { useWebSocket } from '@/hooks/useWebSocket';

export default function Home() {
  const [activeTab, setActiveTab] = useState<
    'inbox' | 'simulator' | 'health' | 'campaigns' | 'knowledge'
  >('inbox');
  const [interactions, setInteractions] = useState<CustomerInteraction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedInteraction, setSelectedInteraction] = useState<CustomerInteraction | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load Initial Data
  const loadData = useCallback(async () => {
    try {
      const [inboxRes, accountsRes] = await Promise.all([
        fetchInboxMessages({ limit: 50 }),
        fetchAccounts(),
      ]);
      setInteractions(inboxRes.items);
      setAccounts(accountsRes);
      if (inboxRes.items.length > 0 && !selectedInteraction) {
        setSelectedInteraction(inboxRes.items[0]);
      }
    } catch (e) {
      console.error('Error loading initial data:', e);
    } finally {
      setIsLoading(false);
    }
  }, [selectedInteraction]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Live WebSocket Real-Time Event Handlers
  const handleInteractionCreated = useCallback((newInteraction: CustomerInteraction) => {
    setInteractions((prev) => {
      const exists = prev.some((item) => item.id === newInteraction.id);
      if (exists) return prev;
      return [newInteraction, ...prev];
    });
  }, []);

  const handleInteractionProcessing = useCallback((processingInteraction: CustomerInteraction) => {
    setInteractions((prev) =>
      prev.map((item) =>
        item.id === processingInteraction.id ? { ...item, status: 'PROCESSING' } : item
      )
    );
    setSelectedInteraction((curr) =>
      curr?.id === processingInteraction.id ? { ...curr, status: 'PROCESSING' } : curr
    );
  }, []);

  const handleInteractionCompleted = useCallback((completedInteraction: CustomerInteraction) => {
    setInteractions((prev) =>
      prev.map((item) => (item.id === completedInteraction.id ? completedInteraction : item))
    );
    setSelectedInteraction((curr) =>
      curr?.id === completedInteraction.id ? completedInteraction : curr
    );
  }, []);

  const handleInteractionFailed = useCallback((failedInteraction: CustomerInteraction) => {
    setInteractions((prev) =>
      prev.map((item) => (item.id === failedInteraction.id ? failedInteraction : item))
    );
    setSelectedInteraction((curr) =>
      curr?.id === failedInteraction.id ? failedInteraction : curr
    );
  }, []);

  const handleAccountUpdated = useCallback((updatedAccount: Account) => {
    setAccounts((prev) =>
      prev.map((acc) => (acc.id === updatedAccount.id ? updatedAccount : acc))
    );
  }, []);

  const handleInboxCleared = useCallback(() => {
    setInteractions([]);
    setSelectedInteraction(null);
  }, []);

  const { isConnected } = useWebSocket({
    onInteractionCreated: handleInteractionCreated,
    onInteractionProcessing: handleInteractionProcessing,
    onInteractionCompleted: handleInteractionCompleted,
    onInteractionFailed: handleInteractionFailed,
    onAccountUpdated: handleAccountUpdated,
    onInboxCleared: handleInboxCleared,
  });

  const handleSelectInteraction = (interaction: CustomerInteraction) => {
    setSelectedInteraction(interaction);
  };

  const handleInteractionUpdated = (updated: CustomerInteraction) => {
    setInteractions((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    setSelectedInteraction(updated);
  };

  return (
    <div className="min-h-screen bg-white text-zinc-900 flex flex-col font-sans">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isConnected={isConnected}
        accounts={accounts}
        unreadCount={interactions.filter((i) => i.status === 'QUEUED').length}
      />

      <main className="flex-1">
        {activeTab === 'inbox' && (
          <InboxView
            interactions={interactions}
            onRefresh={loadData}
            onSelectInteraction={handleSelectInteraction}
            selectedInteraction={selectedInteraction}
            onInteractionUpdated={handleInteractionUpdated}
          />
        )}

        {activeTab === 'simulator' && (
          <WebhookSimulator
            onWebhookSent={() => {
              loadData();
              // Optional quick toast or notification
            }}
          />
        )}

        {activeTab === 'health' && (
          <AccountHealthView accounts={accounts} onAccountsRefreshed={loadData} />
        )}

        {activeTab === 'campaigns' && (
          <CampaignView
            accounts={accounts}
            onCampaignDispatched={() => {
              loadData();
            }}
          />
        )}

        {activeTab === 'knowledge' && <KnowledgeBaseView />}
      </main>
    </div>
  );
}

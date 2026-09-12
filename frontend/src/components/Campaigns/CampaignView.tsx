'use client';

import React, { useState } from 'react';
import { Radio, Users, Send, CheckCircle2, Clock, Plus, Trash2 } from 'lucide-react';
import { Account } from '@/types/pipeline';
import { dispatchCampaign } from '@/lib/api';

interface CampaignViewProps {
  accounts: Account[];
  onCampaignDispatched: () => void;
}

export const CampaignView: React.FC<CampaignViewProps> = ({ accounts, onCampaignDispatched }) => {
  const [selectedAccountId, setSelectedAccountId] = useState(
    accounts[0]?.id || 'acc_instagram_01'
  );
  const [campaignName, setCampaignName] = useState('VIP Autumn Restock Announcement');
  const [templateMessage, setTemplateMessage] = useState(
    'Hi {name}! Our Vegan Leather Desk Mats are back in stock. Use code WELCOME15 for 15% off today!'
  );
  const [pacingDelayMs, setPacingDelayMs] = useState(500);
  const [recipients, setRecipients] = useState([
    { recipient_id: 'usr_101', recipient_name: 'Sophia Chen' },
    { recipient_id: 'usr_102', recipient_name: 'Liam Martinez' },
    { recipient_id: 'usr_103', recipient_name: 'Ava Taylor' },
    { recipient_id: 'usr_104', recipient_name: 'Noah Williams' },
  ]);
  const [newRecipientName, setNewRecipientName] = useState('');
  const [isDispatching, setIsDispatching] = useState(false);
  const [dispatchResult, setDispatchResult] = useState<Record<string, unknown> | null>(null);

  const selectedAccount = accounts.find((a) => a.id === selectedAccountId) || accounts[0];

  const handleAddRecipient = () => {
    if (!newRecipientName.trim()) return;
    setRecipients([
      ...recipients,
      {
        recipient_id: `usr_${Date.now()}`,
        recipient_name: newRecipientName.trim(),
      },
    ]);
    setNewRecipientName('');
  };

  const handleRemoveRecipient = (index: number) => {
    setRecipients(recipients.filter((_, i) => i !== index));
  };

  const handleDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (recipients.length === 0) {
      alert('Please add at least one recipient');
      return;
    }

    setIsDispatching(true);
    setDispatchResult(null);
    try {
      const res = await dispatchCampaign({
        account_id: selectedAccountId,
        campaign_name: campaignName,
        platform: selectedAccount?.platform || 'INSTAGRAM',
        template_message: templateMessage,
        recipients,
        pacing_delay_ms: pacingDelayMs,
      });
      setDispatchResult(res);
      onCampaignDispatched();
    } catch (err) {
      console.error(err);
      alert('Failed to dispatch campaign');
    } finally {
      setIsDispatching(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8 bg-white">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-md">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2.5 rounded-xl bg-cyan-50 border border-cyan-200 text-cyan-700">
            <Radio className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-zinc-900">
              Bulk Campaign Dispatcher
            </h2>
            <p className="text-xs text-zinc-600">
              Send personalized outbound marketing or customer service notifications with automatic inter-message pacing and quota protection.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Dispatch Form */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-zinc-200 p-6 shadow-md">
          <form onSubmit={handleDispatch} className="space-y-4">
            {/* Account Selector */}
            <div>
              <label className="block text-xs font-medium text-zinc-700 mb-1">
                Dispatching Account
              </label>
              <select
                value={selectedAccountId}
                onChange={(e) => setSelectedAccountId(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-zinc-50 border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                {accounts.map((acc) => (
                  <option key={acc.id} value={acc.id}>
                    {acc.name} ({acc.handle} • {acc.platform}) — Quota: {acc.sent_today}/{acc.daily_limit}
                  </option>
                ))}
              </select>
            </div>

            {/* Campaign Name */}
            <div>
              <label className="block text-xs font-medium text-zinc-700 mb-1">
                Campaign Name
              </label>
              <input
                type="text"
                value={campaignName}
                onChange={(e) => setCampaignName(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-zinc-50 border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                required
              />
            </div>

            {/* Template Message */}
            <div>
              <label className="block text-xs font-medium text-zinc-700 mb-1">
                Template Message (use <code className="text-cyan-700 font-mono">{"{name}"}</code> for personalization)
              </label>
              <textarea
                rows={3}
                value={templateMessage}
                onChange={(e) => setTemplateMessage(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-zinc-50 border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                required
              />
            </div>

            {/* Pacing Control */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-medium text-zinc-700">
                  Inter-Message Pacing Delay
                </span>
                <span className="font-mono text-zinc-500">{pacingDelayMs} ms</span>
              </div>
              <input
                type="range"
                min={200}
                max={2000}
                step={50}
                value={pacingDelayMs}
                onChange={(e) => setPacingDelayMs(Number(e.target.value))}
                className="w-full accent-cyan-600"
              />
              <p className="text-[11px] text-zinc-500 mt-1">
                Higher delays mimic organic human sending and lower risk scores.
              </p>
            </div>

            <button
              type="submit"
              disabled={isDispatching}
              className="w-full py-2.5 px-4 bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-2 transition-colors shadow-sm"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Launch Campaign ({recipients.length} Messages)</span>
            </button>
          </form>
        </div>

        {/* Recipients Manager & Telemetry */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-md">
            <h3 className="font-semibold text-xs uppercase tracking-wider text-zinc-600 mb-3 flex items-center justify-between">
              <span className="flex items-center space-x-1.5">
                <Users className="w-3.5 h-3.5 text-cyan-600" />
                <span>Recipients ({recipients.length})</span>
              </span>
            </h3>

            {/* Add Recipient */}
            <div className="flex items-center space-x-2 mb-3">
              <input
                type="text"
                placeholder="Recipient name..."
                value={newRecipientName}
                onChange={(e) => setNewRecipientName(e.target.value)}
                className="flex-1 px-3 py-1.5 text-xs bg-zinc-50 border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddRecipient();
                  }
                }}
              />
              <button
                type="button"
                onClick={handleAddRecipient}
                className="p-1.5 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Recipients List */}
            <div className="max-h-48 overflow-y-auto space-y-1.5 divide-y divide-zinc-100">
              {recipients.map((rec, i) => (
                <div
                  key={i}
                  className="pt-1.5 first:pt-0 flex items-center justify-between text-xs text-zinc-700"
                >
                  <span>{rec.recipient_name}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveRecipient(i)}
                    className="text-zinc-400 hover:text-rose-500"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Dispatch Telemetry */}
          {dispatchResult && (
            <div className="bg-white border border-emerald-200 rounded-2xl p-5 text-xs shadow-md">
              <div className="flex items-center space-x-2 text-emerald-800 font-semibold mb-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Campaign Scheduled Successfully!</span>
              </div>
              <pre className="bg-zinc-50 p-3 rounded-lg text-[11px] overflow-x-auto text-zinc-700 border border-zinc-200">
                {JSON.stringify(dispatchResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

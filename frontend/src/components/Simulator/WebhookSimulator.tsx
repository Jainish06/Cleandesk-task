'use client';

import React, { useState } from 'react';
import {
  Zap,
  AlertTriangle,
  Send,
  Sparkles,
  CheckCircle2,
  Clock,
  Code
} from 'lucide-react';
import { InstagramIcon, ShopifyIcon } from '@/components/Icons';
import { triggerMetaWebhook, triggerShopifyWebhook } from '@/lib/api';

interface WebhookSimulatorProps {
  onWebhookSent: () => void;
}

export const WebhookSimulator: React.FC<WebhookSimulatorProps> = ({ onWebhookSent }) => {
  const [activePlatform, setActivePlatform] = useState<'INSTAGRAM' | 'SHOPIFY'>('INSTAGRAM');
  const [customSender, setCustomSender] = useState('Alex Rivera');
  const [customMessage, setCustomMessage] = useState('How long does standard delivery take to Seattle?');
  const [customTopic, setCustomTopic] = useState('orders/create');
  const [customCartValue, setCustomCartValue] = useState('49.99');
  const [isLoading, setIsLoading] = useState(false);
  const [lastResponse, setLastResponse] = useState<Record<string, unknown> | null>(null);

  const presets = [
    {
      title: 'Instagram DM: Shipping Window Inquiry',
      platform: 'INSTAGRAM',
      sender: 'Elena Rostova',
      message: 'Hello CleanDesk! How long does standard shipping take to Chicago, and is it free?',
      type: 'DM',
      badge: 'Shipping Policy RAG',
    },
    {
      title: 'Instagram Comment: Desk Mat Material & Specs',
      platform: 'INSTAGRAM',
      sender: 'Marcus Vance',
      message: 'Is the vegan leather on the desk mat waterproof and easy to clean?',
      type: 'COMMENT',
      badge: 'Product Specs RAG',
    },
    {
      title: 'Instagram DM: Promo & Discount Inquiry',
      platform: 'INSTAGRAM',
      sender: 'Sophia Chen',
      message: 'Hey there! Are there any discount codes or student promotions available right now?',
      type: 'DM',
      badge: 'Discount Promo RAG',
    },
    {
      title: 'Shopify: Abandoned Cart Notification',
      platform: 'SHOPIFY',
      sender: 'David Miller',
      message: 'Customer left items in shopping cart: CleanDesk Dual-Sided Vegan Leather Desk Mat ($49.99).',
      topic: 'carts/abandoned',
      cartValue: 49.99,
      badge: 'Cart Recovery RAG',
    },
    {
      title: 'Shopify: Order Created #1084',
      platform: 'SHOPIFY',
      sender: 'Sarah Jenkins',
      message: 'Order #1084 paid ($79.98). Customer requested delivery estimate.',
      topic: 'orders/create',
      badge: 'Order Tracking RAG',
    },
    {
      title: 'High-Risk Test: Hostile Chargeback Threat',
      platform: 'INSTAGRAM',
      sender: 'Disgruntled Shopper',
      message: 'This is fraud and a scam! I will contact my lawyer and file a chargeback with my bank immediately!',
      type: 'DM',
      badge: 'Account Shield Protection',
      isWarning: true,
    },
  ];

  const handleTriggerPreset = async (preset: (typeof presets)[0]) => {
    setIsLoading(true);
    setLastResponse(null);
    try {
      let res;
      if (preset.platform === 'INSTAGRAM') {
        res = await triggerMetaWebhook({
          sender_name: preset.sender,
          message_body: preset.message,
          interaction_type: preset.type,
        });
      } else {
        res = await triggerShopifyWebhook({
          topic: preset.topic || 'orders/create',
          sender_name: preset.sender,
          message_body: preset.message,
          cart_value: preset.cartValue || 49.99,
        });
      }
      setLastResponse(res);
      onWebhookSent();
    } catch (e) {
      console.error(e);
      alert('Failed to trigger simulated webhook');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendCustom = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setLastResponse(null);
    try {
      let res;
      if (activePlatform === 'INSTAGRAM') {
        res = await triggerMetaWebhook({
          sender_name: customSender,
          message_body: customMessage,
          interaction_type: 'DM',
        });
      } else {
        res = await triggerShopifyWebhook({
          topic: customTopic,
          sender_name: customSender,
          message_body: customMessage,
          cart_value: parseFloat(customCartValue) || 49.99,
        });
      }
      setLastResponse(res);
      onWebhookSent();
    } catch (err) {
      console.error(err);
      alert('Error sending custom webhook');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8 bg-white">
      {/* Top Banner with Border and Depth */}
      <div className="bg-white rounded-2xl p-6 text-zinc-900 border border-zinc-200 shadow-md">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 rounded-lg bg-cyan-50 border border-cyan-200 text-cyan-700">
            <Zap className="h-5 w-5" />
          </div>
          <h2 className="text-xl font-bold tracking-tight">Interactive Webhook Simulator</h2>
        </div>
        <p className="text-zinc-600 text-sm max-w-2xl leading-relaxed">
          Trigger simulated Instagram Graph API webhooks and Shopify e-commerce payloads. Events are instantly
          persisted as <code className="bg-zinc-100 border border-zinc-300 px-1.5 py-0.5 rounded text-zinc-800 font-mono">QUEUED</code> in MongoDB,
          pushed to the Redis event queue, evaluated against account health rules, enriched via Gemini AI RAG,
          and streamed to the Universal Inbox over WebSockets.
        </p>
      </div>

      {/* Preset Scenarios Grid */}
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-500 mb-4 flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-cyan-600" />
          <span>Quick 1-Click Simulation Scenarios</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {presets.map((preset, idx) => (
            <div
              key={idx}
              className={`rounded-xl p-5 border transition-all hover:shadow-md flex flex-col justify-between bg-white ${
                preset.isWarning
                  ? 'border-rose-300 shadow-xs'
                  : 'border-zinc-200 shadow-sm'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className="p-1 rounded bg-zinc-100 border border-zinc-200 text-zinc-700">
                      {preset.platform === 'INSTAGRAM' ? (
                        <InstagramIcon className="w-4 h-4" />
                      ) : (
                        <ShopifyIcon className="w-4 h-4" />
                      )}
                    </div>
                    <span className="text-xs font-bold text-zinc-800">
                      {preset.platform}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                      preset.isWarning
                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                        : 'bg-zinc-100 text-zinc-700 border-zinc-200'
                    }`}
                  >
                    {preset.badge}
                  </span>
                </div>

                <h4 className="font-semibold text-xs text-zinc-900 mb-1.5">
                  {preset.title}
                </h4>

                <p className="text-xs text-zinc-600 italic line-clamp-3 bg-zinc-50 p-2.5 rounded-lg border border-zinc-200">
                  &ldquo;{preset.message}&rdquo;
                </p>
              </div>

              <button
                onClick={() => handleTriggerPreset(preset)}
                disabled={isLoading}
                className="mt-4 w-full py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors shadow-xs bg-cyan-600 hover:bg-cyan-700 text-white"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>Simulate Webhook Event</span>
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Custom Webhook Dispatch Form & Response Terminal */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Form Panel */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-zinc-200 p-6 shadow-md">
          <h3 className="font-semibold text-sm text-zinc-900 mb-4 flex items-center space-x-2">
            <Code className="w-4 h-4 text-cyan-600" />
            <span>Custom Payload Dispatcher</span>
          </h3>

          <form onSubmit={handleSendCustom} className="space-y-4">
            <div className="flex space-x-2 mb-4">
              <button
                type="button"
                onClick={() => setActivePlatform('INSTAGRAM')}
                className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-2 border transition-all ${
                  activePlatform === 'INSTAGRAM'
                    ? 'bg-cyan-50 border-cyan-400 text-cyan-800 shadow-xs'
                    : 'border-zinc-200 text-zinc-600 hover:bg-zinc-50'
                }`}
              >
                <InstagramIcon className="w-4 h-4" />
                <span>Instagram Webhook</span>
              </button>
              <button
                type="button"
                onClick={() => setActivePlatform('SHOPIFY')}
                className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-2 border transition-all ${
                  activePlatform === 'SHOPIFY'
                    ? 'bg-cyan-50 border-cyan-400 text-cyan-800 shadow-xs'
                    : 'border-zinc-200 text-zinc-600 hover:bg-zinc-50'
                }`}
              >
                <ShopifyIcon className="w-4 h-4" />
                <span>Shopify Webhook</span>
              </button>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-700 mb-1">
                Customer Name
              </label>
              <input
                type="text"
                value={customSender}
                onChange={(e) => setCustomSender(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-white border border-zinc-300 rounded-lg text-zinc-900 shadow-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
                required
              />
            </div>

            {activePlatform === 'SHOPIFY' && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">
                    Event Topic
                  </label>
                  <select
                    value={customTopic}
                    onChange={(e) => setCustomTopic(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-white border border-zinc-300 rounded-lg text-zinc-900 shadow-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  >
                    <option value="orders/create">orders/create</option>
                    <option value="checkouts/create">checkouts/create</option>
                    <option value="carts/abandoned">carts/abandoned</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">
                    Cart Value ($ USD)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={customCartValue}
                    onChange={(e) => setCustomCartValue(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-white border border-zinc-300 rounded-lg text-zinc-900 shadow-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-zinc-700 mb-1">
                Inbound Message Content / Comment
              </label>
              <textarea
                rows={3}
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-white border border-zinc-300 rounded-lg text-zinc-900 shadow-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-2 transition-colors shadow-sm"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Ingest Webhook into Async Pipeline</span>
            </button>
          </form>
        </div>

        {/* Live Ingestion Response Log Terminal */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-zinc-200 p-5 text-zinc-900 font-mono text-xs flex flex-col justify-between shadow-md">
          <div>
            <div className="flex items-center justify-between border-b border-zinc-200 pb-2 mb-3">
              <span className="text-zinc-600 font-semibold uppercase tracking-wider text-[11px]">
                Pipeline Ingestion Telemetry
              </span>
              <span className="h-2 w-2 rounded-full bg-cyan-500 animate-pulse" />
            </div>

            {lastResponse ? (
              <div className="space-y-2">
                <div className="flex items-center space-x-1.5 text-emerald-700 font-semibold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>HTTP 202 Accepted (Queued)</span>
                </div>
                <pre className="bg-zinc-50 p-3 rounded-lg text-zinc-800 overflow-x-auto text-[11px] leading-relaxed border border-zinc-200 shadow-inner">
                  {JSON.stringify(lastResponse, null, 2)}
                </pre>
              </div>
            ) : (
              <div className="text-zinc-400 py-12 text-center">
                <Clock className="w-8 h-8 mx-auto mb-2 opacity-30" />
                <p>Awaiting webhook trigger...</p>
                <p className="text-[10px] text-zinc-500 mt-1">
                  Click any 1-click preset or send a custom payload to see the immediate HTTP 202 response.
                </p>
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-zinc-200 text-[10px] text-zinc-500">
            Pipeline Flow: Fast Webhook Ingestion ➔ Redis Queue ➔ Rate Limiter & RAG Worker ➔ WebSocket Stream
          </div>
        </div>
      </div>
    </div>
  );
};

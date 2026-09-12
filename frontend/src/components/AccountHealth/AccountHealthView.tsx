'use client';

import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  RotateCcw,
  Sliders,
  AlertTriangle,
  Zap,
  Info
} from 'lucide-react';
import { InstagramIcon, ShopifyIcon } from '@/components/Icons';
import { Account } from '@/types/pipeline';
import { resetAccount } from '@/lib/api';

interface AccountHealthViewProps {
  accounts: Account[];
  onAccountsRefreshed: () => void;
}

export const AccountHealthView: React.FC<AccountHealthViewProps> = ({
  accounts,
  onAccountsRefreshed,
}) => {
  const [resettingId, setResettingId] = useState<string | null>(null);

  const handleReset = async (accountId: string) => {
    setResettingId(accountId);
    try {
      await resetAccount(accountId);
      onAccountsRefreshed();
    } catch (e) {
      console.error(e);
      alert('Failed to reset account metrics');
    } finally {
      setResettingId(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8 bg-white">
      {/* Top Banner with Border and Depth */}
      <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-md">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2.5 rounded-xl bg-cyan-50 border border-cyan-200 text-cyan-700">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-zinc-900 tracking-tight">
              Account Health & Platform Protection Engine
            </h2>
            <p className="text-xs text-zinc-600">
              Active monitoring, per-account pacing, and automated rate-limiting safeguards to prevent social media and store bans.
            </p>
          </div>
        </div>
      </div>

      {/* Connected Accounts Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {accounts.map((account) => {
          const quotaPercent = Math.min(
            100,
            Math.round((account.sent_today / (account.daily_limit || 1)) * 100)
          );
          const isRestricted = account.risk_score >= 80;
          const isWarning = account.risk_score >= 50 && !isRestricted;

          return (
            <div
              key={account.id}
              className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-md flex flex-col justify-between"
            >
              <div>
                {/* Header */}
                <div className="flex items-center justify-between mb-5">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-xl bg-zinc-100 border border-zinc-200 text-zinc-700">
                      {account.platform === 'INSTAGRAM' ? (
                        <InstagramIcon className="w-5 h-5" />
                      ) : (
                        <ShopifyIcon className="w-5 h-5" />
                      )}
                    </div>
                    <div>
                      <h3 className="font-bold text-sm text-zinc-900">
                        {account.name}
                      </h3>
                      <p className="text-xs text-zinc-500">
                        {account.handle} • {account.platform}
                      </p>
                    </div>
                  </div>

                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-semibold flex items-center space-x-1 border ${
                      isRestricted
                        ? 'bg-rose-50 text-rose-800 border-rose-200'
                        : isWarning
                        ? 'bg-amber-50 text-amber-800 border-amber-200'
                        : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    }`}
                  >
                    {isRestricted ? (
                      <>
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        <span>RESTRICTED</span>
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="w-3 h-3 mr-1" />
                        <span>HEALTHY</span>
                      </>
                    )}
                  </span>
                </div>

                {/* Quota Progress Meter */}
                <div className="space-y-2 mb-6">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-zinc-800">
                      Daily Automated Send Quota
                    </span>
                    <span className="font-mono text-zinc-600">
                      {account.sent_today} / {account.daily_limit} messages ({quotaPercent}%)
                    </span>
                  </div>

                  <div className="w-full bg-zinc-100 h-2.5 rounded-full overflow-hidden border border-zinc-200">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        quotaPercent >= 100
                          ? 'bg-rose-500'
                          : quotaPercent >= 75
                          ? 'bg-amber-500'
                          : 'bg-cyan-600'
                      }`}
                      style={{ width: `${quotaPercent}%` }}
                    />
                  </div>
                </div>

                {/* Risk Score Meter */}
                <div className="p-4 rounded-xl bg-zinc-50 border border-zinc-200 mb-6 shadow-xs">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-zinc-800">
                      Dynamic Risk Score
                    </span>
                    <span
                      className={`text-sm font-bold ${
                        isRestricted
                          ? 'text-rose-600'
                          : isWarning
                          ? 'text-amber-600'
                          : 'text-cyan-700'
                      }`}
                    >
                      {account.risk_score} / 100
                    </span>
                  </div>

                  <div className="w-full bg-zinc-200 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        isRestricted
                          ? 'bg-rose-500'
                          : isWarning
                          ? 'bg-amber-500'
                          : 'bg-cyan-600'
                      }`}
                      style={{ width: `${account.risk_score}%` }}
                    />
                  </div>

                  <p className="text-[11px] text-zinc-500 mt-2">
                    {isRestricted
                      ? 'Automated sending is blocked because risk score exceeds the 80% safety ceiling.'
                      : 'Risk score is evaluated continuously based on recipient disputes and compliance keywords.'}
                  </p>
                </div>
              </div>

              {/* Action Controls */}
              <div className="pt-4 border-t border-zinc-200 flex items-center justify-between">
                <span className="text-[11px] text-zinc-400">
                  Last Sent:{' '}
                  {account.last_sent_at
                    ? new Date(account.last_sent_at).toLocaleTimeString()
                    : 'None today'}
                </span>

                <button
                  onClick={() => handleReset(account.id)}
                  disabled={resettingId === account.id}
                  className="px-3.5 py-1.5 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-xs"
                >
                  <RotateCcw className={`w-3.5 h-3.5 ${resettingId === account.id ? 'animate-spin' : ''}`} />
                  <span>Reset Quota & Health</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Safety Rules Explainer Section */}
      <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-md">
        <h3 className="text-sm font-bold text-zinc-900 mb-4 flex items-center space-x-2">
          <Info className="w-4 h-4 text-cyan-600" />
          <span>Active Pipeline Safeguards</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-zinc-50 border border-zinc-200 shadow-xs">
            <div className="font-semibold text-zinc-900 mb-1 flex items-center space-x-1.5">
              <Zap className="w-3.5 h-3.5 text-cyan-600" />
              <span>1. Daily Limit Throttling</span>
            </div>
            <p className="text-zinc-600 leading-relaxed">
              When an account reaches its daily quota, the worker halts outgoing AI replies and flags new messages as THROTTLED/FAILED to prevent platform rate limits.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-zinc-50 border border-zinc-200 shadow-xs">
            <div className="font-semibold text-zinc-900 mb-1 flex items-center space-x-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
              <span>2. Risk Score Gatekeeper</span>
            </div>
            <p className="text-zinc-600 leading-relaxed">
              Accounts with risk score &ge; 80 are placed into RESTRICTED status. Inbound complaints with legal or chargeback threats immediately trigger safety flags.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-zinc-50 border border-zinc-200 shadow-xs">
            <div className="font-semibold text-zinc-900 mb-1 flex items-center space-x-1.5">
              <Sliders className="w-3.5 h-3.5 text-emerald-600" />
              <span>3. Human-like Pacing</span>
            </div>
            <p className="text-zinc-600 leading-relaxed">
              The async queue worker enforces a minimum 750ms spacing between outbound actions per account to mimic natural typing and prevent bot detection.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

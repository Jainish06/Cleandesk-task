'use client';

import React, { useState, useEffect } from 'react';
import { BookOpen, Plus, Search, Sparkles, CheckCircle2, Tag } from 'lucide-react';
import { KnowledgeItem } from '@/types/pipeline';
import { fetchKnowledgeItems, createKnowledgeItem } from '@/lib/api';

export const KnowledgeBaseView: React.FC = () => {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newCategory, setNewCategory] = useState('PRODUCT');
  const [newContext, setNewContext] = useState('');
  const [testQuery, setTestQuery] = useState('Can I get a refund if the desk mat is opened?');
  const [testResult, setTestResult] = useState<Record<string, unknown> | null>(null);
  const [isTestingRAG, setIsTestingRAG] = useState(false);

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    setIsLoading(true);
    try {
      const data = await fetchKnowledgeItems();
      setItems(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !newContext.trim()) return;
    try {
      await createKnowledgeItem({
        product_name: newName,
        category: newCategory,
        context_text: newContext,
      });
      setNewName('');
      setNewContext('');
      setShowAddForm(false);
      loadItems();
    } catch (err) {
      console.error(err);
      alert('Failed to save knowledge item');
    }
  };

  const handleTestRAG = async () => {
    if (!testQuery.trim()) return;
    setIsTestingRAG(true);
    setTestResult(null);
    try {
      const res = await fetch('http://localhost:8000/api/ai/generate-reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: testQuery, platform: 'INSTAGRAM' }),
      });
      const data = await res.json();
      setTestResult(data);
    } catch (e) {
      console.error(e);
      alert('Error testing RAG response');
    } finally {
      setIsTestingRAG(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8 bg-white">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-md flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-cyan-50 border border-cyan-200 text-cyan-700">
            <BookOpen className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-zinc-900">
              Product & Policy Knowledge Base (RAG)
            </h2>
            <p className="text-xs text-zinc-600">
              Verified documents indexed for dense semantic retrieval. Gemini AI grounds every response exclusively in these facts.
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-3.5 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-sm"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>{showAddForm ? 'Cancel' : 'Add Knowledge Document'}</span>
        </button>
      </div>

      {/* Add Document Form (Collapsible) */}
      {showAddForm && (
        <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-md">
          <h3 className="text-sm font-semibold text-zinc-900 mb-4">
            Index New Product or Store Policy
          </h3>
          <form onSubmit={handleAddItem} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-zinc-700 mb-1">
                  Document / Product Title
                </label>
                <input
                  type="text"
                  placeholder="e.g. Ergonomic Footrest 2.0"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-zinc-50 border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-700 mb-1">
                  Category
                </label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-zinc-50 border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                >
                  <option value="PRODUCT">PRODUCT</option>
                  <option value="POLICY">POLICY</option>
                  <option value="DISCOUNT">DISCOUNT</option>
                  <option value="FAQ">FAQ</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-700 mb-1">
                Factual Context Text (Prices, Specs, Warranties, Shipping times)
              </label>
              <textarea
                rows={4}
                placeholder="Detailed specifications and store policy rules..."
                value={newContext}
                onChange={(e) => setNewContext(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-zinc-50 border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                required
              />
            </div>

            <button
              type="submit"
              className="py-2 px-4 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              Save & Index Document
            </button>
          </form>
        </div>
      )}

      {/* RAG Interactive Test Bench */}
      <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-md">
        <h3 className="text-sm font-semibold text-zinc-900 mb-1 flex items-center space-x-1.5">
          <Sparkles className="w-4 h-4 text-cyan-600" />
          <span>Test Semantic RAG Retrieval & Gemini AI Synthesis</span>
        </h3>
        <p className="text-xs text-zinc-600 mb-4">
          Type any question to see what documents are retrieved from the knowledge base and how Gemini formats the response.
        </p>

        <div className="flex space-x-2 mb-4">
          <input
            type="text"
            value={testQuery}
            onChange={(e) => setTestQuery(e.target.value)}
            className="flex-1 px-3 py-2 text-xs bg-zinc-50 border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            placeholder="Type query (e.g., Do you offer international delivery?)"
          />
          <button
            onClick={handleTestRAG}
            disabled={isTestingRAG}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-sm"
          >
            <Search className="w-3.5 h-3.5" />
            <span>Test Query</span>
          </button>
        </div>

        {testResult && (
          <div className="bg-white rounded-xl p-4 border border-zinc-200 text-xs space-y-2 shadow-sm">
            <div className="flex items-center justify-between text-zinc-900 font-semibold">
              <span>Model: {testResult.model_used as string}</span>
              <span className="text-cyan-700 font-mono">Confidence: {((testResult.confidence_score as number) * 100).toFixed(0)}%</span>
            </div>
            <div className="p-3 bg-zinc-50 border border-zinc-200 rounded-lg text-zinc-800 leading-relaxed">
              {testResult.reply as string}
            </div>
            <div className="text-[11px] text-zinc-500 flex items-center space-x-1">
              <span>Cited Sources:</span>
              {(testResult.sources as string[]).map((s, i) => (
                <span key={i} className="px-1.5 py-0.5 bg-zinc-100 border border-zinc-200 text-zinc-700 rounded font-medium">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Indexed Documents Grid */}
      <div>
        <h3 className="text-xs uppercase tracking-wider font-semibold text-zinc-500 mb-3">
          Indexed Documents ({items.length})
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((doc) => (
            <div
              key={doc.id}
              className="bg-white rounded-xl border border-zinc-200 p-4 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-xs text-zinc-900">
                  {doc.product_name}
                </h4>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-zinc-100 border border-zinc-200 text-zinc-700">
                  {doc.category}
                </span>
              </div>
              <p className="text-xs text-zinc-600 leading-relaxed line-clamp-3">
                {doc.context_text}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

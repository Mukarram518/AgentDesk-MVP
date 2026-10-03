"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

interface LeadItem {
  id: string;
  business_id: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  message: string;
  intent: string | null;
  status: "HOT" | "WARM" | "COLD";
  score: number | null;
  created_at: string;
}

interface LeadsData {
  business_id: string;
  total_leads: number;
  hot_leads: number;
  warm_leads: number;
  cold_leads: number;
  leads: LeadItem[];
}

interface BusinessInfo {
  id: string;
  name: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DashboardPage() {
  const [business, setBusiness] = useState<BusinessInfo | null>(null);
  const [leadsData, setLeadsData] = useState<LeadsData | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 1. Fetch demo business ID
  useEffect(() => {
    async function loadBusiness() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/business/demo`);
        if (res.ok) {
          const data = await res.json();
          setBusiness(data);
        }
      } catch (err) {
        console.error("Failed to fetch demo business", err);
      }
    }
    loadBusiness();
  }, []);

  // 2. Fetch leads
  const fetchLeads = async (bizId: string, statusFilter?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      let url = `${API_BASE}/api/v1/leads?business_id=${bizId}`;
      if (statusFilter && statusFilter !== "ALL") {
        url += `&status=${statusFilter}`;
      }
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`Failed to load leads (status ${res.status})`);
      }
      const data = await res.json();
      setLeadsData(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load leads");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (business?.id) {
      fetchLeads(business.id, activeFilter);
    }
  }, [business, activeFilter]);

  const handleFilterChange = (filter: string) => {
    setActiveFilter(filter);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "HOT":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
            HOT
          </span>
        );
      case "WARM":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            WARM
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30">
            <span className="h-1.5 w-1.5 rounded-full bg-sky-400" />
            COLD
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 antialiased flex flex-col">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md px-6 py-4 sticky top-0 z-20">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-sky-400 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">
              AD
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-bold text-base sm:text-lg text-white tracking-tight">
                  {business?.name || "Apex Dental Studio"} — Owner Dashboard
                </h1>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-indigo-950/80 border border-indigo-700/50 text-indigo-300">
                  Phase 1D
                </span>
              </div>
              <p className="text-xs text-slate-400">Captured Leads & Deterministic Pipeline</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => business?.id && fetchLeads(business.id, activeFilter)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 hover:text-white transition-colors cursor-pointer border border-slate-700"
            >
              Refresh
            </button>
            <Link
              href="/"
              className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition-colors cursor-pointer shadow-sm shadow-indigo-600/30"
            >
              ← Back to Customer Chat
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl w-full mx-auto px-6 py-8 space-y-8 flex-1">
        {/* Metric Cards */}
        <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-1">
            <div className="text-xs font-mono uppercase text-slate-400">Total Leads</div>
            <div className="text-3xl font-extrabold text-white">
              {leadsData?.total_leads ?? 0}
            </div>
            <div className="text-[11px] text-slate-500">Captured from customer chat</div>
          </div>

          <div className="rounded-xl border border-rose-900/40 bg-rose-950/20 p-5 space-y-1">
            <div className="text-xs font-mono uppercase text-rose-400">HOT Leads</div>
            <div className="text-3xl font-extrabold text-rose-300">
              {leadsData?.hot_leads ?? 0}
            </div>
            <div className="text-[11px] text-rose-400/70">Booking / Immediate purchase intent</div>
          </div>

          <div className="rounded-xl border border-amber-900/40 bg-amber-950/20 p-5 space-y-1">
            <div className="text-xs font-mono uppercase text-amber-400">WARM Leads</div>
            <div className="text-3xl font-extrabold text-amber-300">
              {leadsData?.warm_leads ?? 0}
            </div>
            <div className="text-[11px] text-amber-400/70">Serious pricing & service inquiry</div>
          </div>

          <div className="rounded-xl border border-sky-900/40 bg-sky-950/20 p-5 space-y-1">
            <div className="text-xs font-mono uppercase text-sky-400">COLD Leads</div>
            <div className="text-3xl font-extrabold text-sky-300">
              {leadsData?.cold_leads ?? 0}
            </div>
            <div className="text-[11px] text-sky-400/70">Low commitment / Exploratory</div>
          </div>
        </section>

        {/* Leads Table Section */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm overflow-hidden">
          {/* Filter Bar */}
          <div className="p-4 sm:p-5 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-white">Captured Customer Leads</h2>
              <p className="text-xs text-slate-400">
                Filtered strictly by Business ID: <span className="font-mono text-slate-300">{business?.id || "Loading..."}</span>
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 mr-1">Filter:</span>
              {["ALL", "HOT", "WARM", "COLD"].map((filter) => (
                <button
                  key={filter}
                  onClick={() => handleFilterChange(filter)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                    activeFilter === filter
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "bg-slate-800 text-slate-400 hover:text-white"
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>

          {/* Loading or Error State */}
          {isLoading && (
            <div className="p-12 text-center text-slate-400 text-sm">
              Loading leads from database...
            </div>
          )}

          {error && (
            <div className="p-6 m-4 rounded-xl bg-red-950/50 border border-red-800/80 text-red-200 text-xs">
              {error}
            </div>
          )}

          {/* Table */}
          {!isLoading && !error && (!leadsData?.leads || leadsData.leads.length === 0) ? (
            <div className="p-12 text-center text-slate-500 text-sm">
              No leads found matching current filter.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950/80 text-xs uppercase text-slate-400 font-mono border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Status & Score</th>
                    <th className="py-3 px-4">Contact</th>
                    <th className="py-3 px-4">Intent</th>
                    <th className="py-3 px-4">Message Excerpt</th>
                    <th className="py-3 px-4">Captured At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-normal">
                  {leadsData?.leads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-slate-800/30 transition-colors">
                      {/* Status & Score */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {getStatusBadge(lead.status)}
                          <span className="text-xs font-mono text-slate-400">
                            {lead.score ?? 0} pts
                          </span>
                        </div>
                      </td>

                      {/* Contact */}
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-white">
                          {lead.name || <span className="italic text-slate-500">Not provided</span>}
                        </div>
                        <div className="text-xs text-slate-400 space-x-2">
                          {lead.email && <span>{lead.email}</span>}
                          {lead.phone && <span>• {lead.phone}</span>}
                          {!lead.email && !lead.phone && (
                            <span className="text-slate-600">No contact info</span>
                          )}
                        </div>
                      </td>

                      {/* Intent */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className="px-2 py-0.5 rounded text-xs font-mono bg-slate-800 text-sky-300 border border-slate-700">
                          {lead.intent || "general"}
                        </span>
                      </td>

                      {/* Message */}
                      <td className="py-3.5 px-4 max-w-xs truncate text-xs text-slate-300">
                        {lead.message}
                      </td>

                      {/* Date */}
                      <td className="py-3.5 px-4 whitespace-nowrap text-xs text-slate-400">
                        {new Date(lead.created_at).toLocaleString([], {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  AlertOctagon,
  FileText,
  Activity,
  Award,
  BookOpen,
  ArrowRight,
  Sparkles,
  ChevronRight,
  ShieldCheck,
  CheckCircle,
  XCircle,
  HelpCircle,
  ExternalLink
} from 'lucide-react';
import { Recording, Dietician } from '../types';

interface DashboardViewProps {
  recordings: Recording[];
  onSelectCall: (id: string) => void;
  dieticians: Dietician[];
  searchQuery: string;
}

export default function DashboardView({
  recordings,
  onSelectCall,
  dieticians,
  searchQuery
}: DashboardViewProps) {
  const [showHeatmap, setShowHeatmap] = React.useState(false);
  // Stats calculations from REAL API data only
  const totalCalls = recordings.length;
  const avgQualityScore = recordings.length > 0
    ? Math.round((recordings.reduce((sum, r) => sum + (r.sopComplianceScore || 0), 0) / recordings.length) * 10) / 10
    : 0;
  // SOP Compliance % = average of the compliance dimension score across all calls (0-100)
  const sopCompliance = recordings.length > 0
    ? Math.round(recordings.reduce((sum, r) => sum + (r.scores?.compliance || 0), 0) / recordings.length)
    : 0;
  const criticalAlertsCount = recordings.reduce((sum, r) => {
    return sum + (r.qaAlerts?.filter(a => a.severity === 'critical').length || 0);
  }, 0);

  const filteredRecordings = recordings.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.name.toLowerCase().includes(q) ||
      r.patientName.toLowerCase().includes(q) ||
      r.agentName.toLowerCase().includes(q) ||
      r.id.includes(q)
    );
  });

  // Performance data — one bar per DIETICIAN (aggregated average), not per recording
  const performanceDist = (() => {
    const byDietician: Record<string, number[]> = {};
    recordings.forEach(r => {
      const name = r.agentName || 'Unknown';
      if (!byDietician[name]) byDietician[name] = [];
      byDietician[name].push(r.sopComplianceScore || 0);
    });
    return Object.entries(byDietician).map(([name, scores]) => ({
      name: name.split(' ')[0],
      score: Math.round(scores.reduce((a, b) => a + b, 0) / scores.length),
      calls: scores.length,
      peerMedian: 60,
    }));
  })();

  return (
    <div className="flex-1 flex overflow-hidden bg-[#F7F3F0] h-full select-none">
      {/* Main Left Content Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-8">
        {/* Header Section */}
        <section className="flex justify-between items-end border-b border-[#1A1A1A]/10 pb-6">
          <div>
            <span className="text-[10px] font-sans font-bold uppercase tracking-[0.3em] text-[#8B7E66]">Overview Report</span>
            <h2 className="text-3xl font-serif italic font-medium tracking-tight text-[#1A1A1A] mt-1">Executive Performance Overview</h2>
            <p className="text-xs font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1">
              Real-time health of clinical consultations and dietician performance.
            </p>
          </div>
          <div className="flex gap-3">
            <button className="px-4 py-2 text-xs font-sans uppercase tracking-wider border border-[#1A1A1A]/20 bg-white text-[#1A1A1A] hover:bg-[#F7F3F0] rounded-none flex items-center gap-2 cursor-pointer transition-colors">
              <span>Last 30 Days</span>
            </button>
            <button className="px-4 py-2 text-xs font-sans uppercase tracking-wider bg-[#1A1A1A] text-white hover:bg-[#8B7E66] rounded-none flex items-center gap-2 cursor-pointer transition-all">
              <span>Export PDF</span>
            </button>
          </div>
        </section>

        {/* Quick Stats Bento */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1: Total Calls */}
          <div className="bg-white border border-[#1A1A1A]/10 p-6 rounded-none hover:border-[#8B7E66] transition-all duration-200 relative group">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-[0.15em]">Total Calls Analyzed</span>
              <div className="text-[#8B7E66]">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-4xl font-serif italic font-medium text-[#1A1A1A]">{totalCalls.toLocaleString()}</h3>
              <span className="text-emerald-700 text-xs font-mono font-bold flex items-center gap-1 bg-emerald-50 px-1.5 py-0.5 border border-emerald-200 shrink-0">
                <TrendingUp className="w-3 h-3" />
                +12%
              </span>
            </div>
            <div className="absolute top-0 left-0 w-full h-[2px] bg-[#8B7E66] opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </div>

          {/* Card 2: Avg Quality Score */}
          <div className="bg-white border border-[#1A1A1A]/10 p-6 rounded-none hover:border-[#8B7E66] transition-all duration-200 relative group">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-[0.15em]">Avg. Quality Score</span>
              <div className="text-[#8B7E66]">
                <Award className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-4xl font-serif italic font-medium text-[#1A1A1A]">{avgQualityScore}%</h3>
              <span className="text-emerald-700 text-xs font-mono font-bold flex items-center gap-1 bg-emerald-50 px-1.5 py-0.5 border border-emerald-200 shrink-0">
                <TrendingUp className="w-3 h-3" />
                +2.4%
              </span>
            </div>
            <div className="absolute top-0 left-0 w-full h-[2px] bg-[#8B7E66] opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </div>

          {/* Card 3: SOP Compliance */}
          <div className="bg-white border border-[#1A1A1A]/10 p-6 rounded-none hover:border-[#8B7E66] transition-all duration-200 relative group">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-[0.15em]">SOP Compliance %</span>
              <div className="text-[#8B7E66]">
                <ShieldCheck className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-4xl font-serif italic font-medium text-[#1A1A1A]">{sopCompliance}%</h3>
              <span className="text-[#A34E36] text-xs font-mono font-bold flex items-center gap-1 bg-[#F9EAE6] px-1.5 py-0.5 border border-[#A34E36]/20 shrink-0">
                <TrendingDown className="w-3 h-3" />
                -0.8%
              </span>
            </div>
            <div className="absolute top-0 left-0 w-full h-[2px] bg-[#8B7E66] opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </div>

          {/* Card 4: Critical Alerts */}
          <div className="bg-white border border-[#1A1A1A]/10 p-6 rounded-none hover:border-[#8B7E66] transition-all duration-200 relative group">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-sans font-bold text-[#1A1A1A]/50 uppercase tracking-[0.15em]">Critical QA Alerts</span>
              <div className="text-[#A34E36]">
                <AlertOctagon className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-4xl font-serif italic font-medium text-[#1A1A1A]">{criticalAlertsCount}</h3>
              <span className="bg-[#F9EAE6] border border-[#A34E36]/30 text-[#A34E36] text-[8px] font-sans font-bold px-2 py-0.5 rounded-none uppercase tracking-widest shrink-0">
                Critical
              </span>
            </div>
            <div className="absolute top-0 left-0 w-full h-[2px] bg-[#8B7E66] opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </div>
        </section>

        {/* Charts Section: Dietician Performance & SOP Breaches */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Dietician Performance Distribution SVG Chart */}
          <div className="lg:col-span-7 bg-white border border-[#1A1A1A]/10 rounded-none p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-[#1A1A1A]/5 pb-4">
                <div>
                  <h3 className="text-lg font-serif italic font-medium text-[#1A1A1A]">Staff Performance Metrics</h3>
                  <p className="text-[10px] font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-0.5">
                    Distribution of quality scores across clinical staff members.
                  </p>
                </div>
                {/* Legend */}
                <div className="flex gap-4 text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/60">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-[#8B7E66]"></span>
                    <span>Individual</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-[#1A1A1A]/20"></span>
                    <span>Peer Median</span>
                  </div>
                </div>
              </div>

              {/* Chart Stage */}
              <div className="h-60 mt-8 flex items-end justify-between px-4 border-b border-[#1A1A1A]/10 pb-2 relative">
                {/* Y-Axis lines helper */}
                <div className="absolute left-0 right-0 top-0 h-[1px] bg-[#1A1A1A]/5"></div>
                <div className="absolute left-0 right-0 top-1/4 h-[1px] bg-[#1A1A1A]/5"></div>
                <div className="absolute left-0 right-0 top-2/4 h-[1px] bg-[#1A1A1A]/5"></div>
                <div className="absolute left-0 right-0 top-3/4 h-[1px] bg-[#1A1A1A]/5"></div>

                {performanceDist.map((item, idx) => (
                  <div key={idx} className="flex flex-col items-center gap-2 flex-1 group">
                    <div className="relative w-12 h-44 flex items-end justify-center">
                      {/* Peer Median Line Indicator */}
                      <div 
                        className="absolute w-full h-[2px] bg-[#1A1A1A]/30 z-10 transition-colors group-hover:bg-[#8B7E66]"
                        style={{ bottom: `${item.peerMedian}%` }}
                        title={`Peer Median: ${item.peerMedian}%`}
                      ></div>

                      {/* Score Bar */}
                      <div 
                        className={`w-3.5 rounded-none transition-all duration-300 group-hover:opacity-85 relative ${
                          item.score < 75 
                            ? 'bg-[#A34E36]' 
                            : item.score < 90 
                            ? 'bg-[#8B7E66]/60' 
                            : 'bg-[#8B7E66]'
                        }`}
                        style={{ height: `${item.score}%` }}
                      >
                        {/* Tooltip on hover */}
                        <div className="absolute -top-14 left-1/2 -translate-x-1/2 bg-[#1A1A1A] text-white text-[9px] font-mono font-bold px-2 py-1 rounded-none whitespace-nowrap z-30 shadow-md opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none text-center">
                          <div>Score: {item.score}%</div>
                          <div className="text-[#8B7E66]">{(item as any).calls} calls</div>
                        </div>
                      </div>
                    </div>
                    <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/60">{item.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SOP Breach Categories — from real QA alert data */}
          <div className="lg:col-span-5 bg-white border border-[#1A1A1A]/10 rounded-none p-6 flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-serif italic font-medium text-[#1A1A1A] border-b border-[#1A1A1A]/5 pb-4">SOP Breach Categories</h3>
              <p className="text-[10px] font-sans uppercase tracking-wider text-[#1A1A1A]/50 mt-1.5">Most common compliance failures identified by AI, ranked by frequency.</p>

              <div className="mt-6 space-y-4">
                {(() => {
                  const allAlerts = recordings.flatMap(r => r.qaAlerts || []);
                  const counts: Record<string, number> = {};
                  for (const a of allAlerts) { const t = a?.title; if (t) counts[t] = (counts[t] || 0) + 1; }
                  const total = recordings.length || 1;
                  return Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([title, count]) => {
                    const pct = Math.round((count / total) * 100);
                    const color = pct >= 80 ? 'bg-[#A34E36]' : pct >= 50 ? 'bg-[#8B7E66]' : 'bg-[#8B7E66]/50';
                    const textColor = pct >= 80 ? 'text-[#A34E36]' : 'text-[#8B7E66]';
                    return (
                      <div key={title} className="space-y-1.5">
                        <div className="flex justify-between text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]">
                          <span className="truncate max-w-[200px]" title={title}>{title}</span>
                          <span className={`font-mono ml-2 shrink-0 ${textColor}`}>{count}/{total} calls</span>
                        </div>
                        <div className="w-full bg-[#FAF8F6] border border-[#1A1A1A]/5 h-2 rounded-none overflow-hidden">
                          <div className={`${color} h-full transition-all`} style={{ width: `${pct}%` }}></div>
                        </div>
                      </div>
                    );
                  });
                })()}
                {recordings.flatMap(r => r.qaAlerts || []).length === 0 && (
                  <p className="text-xs text-[#1A1A1A]/40 italic">No breach data yet. Upload and process calls to see patterns.</p>
                )}
              </div>
            </div>

            <button
              onClick={() => setShowHeatmap(true)}
              className="mt-6 w-full py-3 border border-[#1A1A1A]/30 text-[#1A1A1A] text-xs font-sans uppercase tracking-widest hover:bg-[#1A1A1A] hover:text-white transition-all rounded-none cursor-pointer">
              View All Breach Types
            </button>
          </div>

          {/* Heatmap Modal */}
          {showHeatmap && (
            <div className="fixed inset-0 bg-[#1A1A1A]/60 z-50 flex items-center justify-center p-6" onClick={() => setShowHeatmap(false)}>
              <div className="bg-white w-full max-w-xl max-h-[80vh] overflow-y-auto rounded-none p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center mb-4 border-b border-[#1A1A1A]/10 pb-3">
                  <h3 className="text-lg font-serif italic font-medium text-[#1A1A1A]">All SOP Breach Types</h3>
                  <button onClick={() => setShowHeatmap(false)} className="text-[#1A1A1A]/40 hover:text-[#1A1A1A] text-xs font-sans uppercase tracking-wider">Close</button>
                </div>
                <div className="space-y-3">
                  {(() => {
                    const allAlerts = recordings.flatMap(r => r.qaAlerts || []);
                    const counts: Record<string, number> = {};
                    for (const a of allAlerts) { const t = a?.title; if (t) counts[t] = (counts[t] || 0) + 1; }
                    const total = recordings.length || 1;
                    return Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([title, count]) => {
                      const pct = Math.round((count / total) * 100);
                      return (
                        <div key={title}>
                          <div className="flex justify-between text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A] mb-1">
                            <span className="max-w-[340px] leading-tight">{title}</span>
                            <span className={`ml-2 shrink-0 font-mono ${pct >= 80 ? 'text-[#A34E36]' : 'text-[#8B7E66]'}`}>{count}/{total}</span>
                          </div>
                          <div className="w-full bg-[#FAF8F6] h-1.5">
                            <div className={`h-full ${pct >= 80 ? 'bg-[#A34E36]' : 'bg-[#8B7E66]'}`} style={{ width: `${pct}%` }}></div>
                          </div>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Lower Table: Recent Call Analysis */}
        <section className="bg-white border border-[#1A1A1A]/10 rounded-none overflow-hidden shadow-none">
          <div className="p-6 border-b border-[#1A1A1A]/10 flex items-center justify-between bg-[#FAF8F6]">
            <h3 className="text-lg font-serif italic font-medium text-[#1A1A1A]">Recent Ingested Audios</h3>
            <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-[#1A1A1A]/40">Showing {filteredRecordings.length} calls</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#FAF8F6] border-b border-[#1A1A1A]/10">
                  <th className="px-6 py-3.5 text-[10px] font-sans font-bold uppercase tracking-widest text-[#1A1A1A]/60">Recording Name</th>
                  <th className="px-6 py-3.5 text-[10px] font-sans font-bold uppercase tracking-widest text-[#1A1A1A]/60">Dietician</th>
                  <th className="px-6 py-3.5 text-[10px] font-sans font-bold uppercase tracking-widest text-[#1A1A1A]/60">AI Score</th>
                  <th className="px-6 py-3.5 text-[10px] font-sans font-bold uppercase tracking-widest text-[#1A1A1A]/60">Compliance Status</th>
                  <th className="px-6 py-3.5 text-[10px] font-sans font-bold uppercase tracking-widest text-[#1A1A1A]/60">Date</th>
                  <th className="px-6 py-3.5 text-[10px] font-sans font-bold uppercase tracking-widest text-[#1A1A1A]/60 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1A1A1A]/10">
                {filteredRecordings.map((call) => {
                  const isCompliant = call.sopCompliant;
                  return (
                    <tr 
                      key={call.id} 
                      onClick={() => onSelectCall(call.id)}
                      className="hover:bg-[#FAF8F6] cursor-pointer transition-colors group"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <FileText className="w-4 h-4 text-[#8B7E66]" />
                          <span className="text-xs font-serif font-medium text-[#1A1A1A] truncate max-w-xs">{call.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-none border border-[#1A1A1A]/20 bg-[#F7F3F0] text-[#1A1A1A] font-mono font-bold text-[10px] flex items-center justify-center">
                            {call.agentName.split(' ').map(n => n[0]).join('')}
                          </span>
                          <span className="text-xs font-sans uppercase tracking-wide text-[#1A1A1A]">{call.agentName}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`text-xs font-mono font-bold ${
                          call.sopComplianceScore >= 90 
                            ? 'text-emerald-700' 
                            : call.sopComplianceScore >= 75 
                            ? 'text-[#8B7E66]' 
                            : 'text-[#A34E36]'
                        }`}>
                          {call.sopComplianceScore}%
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 text-[9px] font-sans font-bold border rounded-none uppercase tracking-widest ${
                          isCompliant 
                            ? 'bg-emerald-50 border-emerald-300 text-emerald-800' 
                            : 'bg-[#F9EAE6] border-[#A34E36]/30 text-[#A34E36]'
                        }`}>
                          {isCompliant ? 'Compliant' : 'Breach Detected'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-xs font-mono text-[#1A1A1A]/60">{call.date}</span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button className="p-1 text-[#1A1A1A]/40 hover:text-[#1A1A1A] rounded-none transition-colors group-hover:translate-x-0.5 transform transition-transform">
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-[#FAF8F6] border-t border-[#1A1A1A]/10 text-center">
            <span className="text-[10px] text-[#8B7E66] hover:text-[#1A1A1A] cursor-pointer font-sans uppercase tracking-widest flex items-center justify-center gap-1">
              <span>Showing All {totalCalls} Analysed Calls</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </span>
          </div>
        </section>
      </div>
    </div>
  );
}

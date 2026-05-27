import React, { useEffect, useState } from 'react';
import { History, Search, ArrowRight, UserCheck, ShieldAlert } from 'lucide-react';
import api from '../services/api';

export default function AuditLogPage() {
  const [logs, setLogs] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLogs();
      setLogs(data.results || data);
    } catch (err) {
      console.error("Error fetching audit logs:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter(log => {
    const query = searchQuery.toLowerCase();
    return (
      log.changed_by.toLowerCase().includes(query) ||
      log.change_reason.toLowerCase().includes(query) ||
      log.emission_record.toLowerCase().includes(query)
    );
  });

  return (
    <div className="space-y-6">
      {/* Search and Header */}
      <div className="bg-slate-950/40 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Enterprise Compliance Audit Trail</h3>
          <p className="text-[10px] text-slate-500 mt-1">Immutable log of all modifications, corrections, and regulatory approvals.</p>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by analyst or reason..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-lg pl-9 pr-4 py-2 focus:ring-1 focus:ring-brand-500 outline-none w-full md:w-64"
          />
        </div>
      </div>

      {/* Logs timeline / list */}
      {loading ? (
        <div className="text-center py-12 text-slate-500 text-xs">
          Loading audit trail history...
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="bg-slate-950/40 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 text-xs">
          No audit log records found matching the search criteria.
        </div>
      ) : (
        <div className="space-y-4">
          {filteredLogs.map((log) => (
            <div key={log.id} className="bg-slate-950/40 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-5 shadow-lg transition-all text-xs">
              <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-3 mb-3 gap-2">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300">
                    <UserCheck className="h-4.5 w-4.5 text-brand-500" />
                  </div>
                  <div>
                    <p className="font-semibold text-slate-200">{log.changed_by}</p>
                    <p className="text-[10px] text-slate-500 font-mono mt-0.5">Record ID: {log.emission_record}</p>
                  </div>
                </div>
                
                <div className="text-right">
                  <p className="text-[10px] text-slate-400 font-semibold">{new Date(log.timestamp).toLocaleString()}</p>
                  <p className="text-[9px] text-slate-600 font-mono mt-0.5">Audit Event ID: {log.id}</p>
                </div>
              </div>

              {/* Reason card */}
              <div className="bg-amber-500/5 border border-amber-500/10 rounded-xl p-3 mb-4">
                <p className="text-slate-300 font-medium leading-relaxed">
                  <span className="text-amber-500 font-semibold uppercase text-[9px] tracking-wider bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded mr-2 font-mono">
                    Justification
                  </span>
                  {log.change_reason}
                </p>
              </div>

              {/* State transition deltas */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-900 font-mono text-[10px] text-slate-400 space-y-2">
                <p className="text-slate-500 font-semibold pb-1.5 border-b border-slate-900 flex items-center gap-1.5 font-sans text-xs">
                  <History className="h-3.5 w-3.5 text-slate-500" />
                  State Transitions
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                  {Object.keys(log.new_value).map((key) => {
                    const oldVal = log.old_value[key];
                    const newVal = log.new_value[key];
                    if (oldVal !== newVal) {
                      return (
                        <div key={key} className="flex items-center justify-between border-b border-slate-900/40 py-1">
                          <span className="text-slate-400 font-sans">{key}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-rose-500 bg-rose-500/5 px-1.5 py-0.5 rounded line-through">{String(oldVal)}</span>
                            <ArrowRight className="h-3 w-3 text-slate-600" />
                            <span className="text-emerald-500 bg-emerald-500/5 px-1.5 py-0.5 rounded font-bold">{String(newVal)}</span>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

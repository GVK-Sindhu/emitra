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
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wider">Enterprise Compliance Audit Trail</h3>
          <p className="text-[10px] text-gray-400 mt-1">Immutable log of all modifications, corrections, and regulatory approvals.</p>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by analyst or reason..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-white border border-gray-200 text-gray-800 text-xs rounded-lg pl-9 pr-4 py-2 focus:ring-1 focus:ring-brand-500 outline-none w-full md:w-64"
          />
        </div>
      </div>

      {/* Logs timeline / list */}
      {loading ? (
        <div className="text-center py-12 text-gray-500 text-xs">
          Loading audit trail history...
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-2xl p-12 text-center text-gray-500 text-xs">
          No audit log records found matching the search criteria.
        </div>
      ) : (
        <div className="space-y-4">
          {filteredLogs.map((log) => (
            <div key={log.id} className="bg-white border border-gray-200 hover:border-gray-300 rounded-2xl p-5 shadow-sm transition-all text-xs">
              <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-gray-100 pb-3 mb-3 gap-2">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded bg-gray-50 border border-gray-200 text-gray-700">
                    <UserCheck className="h-4.5 w-4.5 text-brand-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-800">{log.changed_by}</p>
                    <p className="text-[10px] text-gray-400 font-mono mt-0.5">Record ID: {log.emission_record}</p>
                  </div>
                </div>
                
                <div className="text-right">
                  <p className="text-[10px] text-gray-500 font-semibold">{new Date(log.timestamp).toLocaleString()}</p>
                  <p className="text-[9px] text-gray-400 font-mono mt-0.5">Audit Event ID: {log.id}</p>
                </div>
              </div>

              {/* Reason card */}
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4">
                <p className="text-gray-800 font-medium leading-relaxed">
                  <span className="text-amber-700 font-semibold uppercase text-[9px] tracking-wider bg-amber-50 border border-amber-200 px-1.5 py-0.5 rounded mr-2 font-mono">
                    Justification
                  </span>
                  {log.change_reason}
                </p>
              </div>

              {/* State transition deltas */}
              <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 font-mono text-[10px] text-gray-650 space-y-2">
                <p className="text-gray-500 font-semibold pb-1.5 border-b border-gray-200 flex items-center gap-1.5 font-sans text-xs">
                  <History className="h-3.5 w-3.5 text-gray-405" />
                  State Transitions
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                  {Object.keys(log.new_value).map((key) => {
                    const oldVal = log.old_value[key];
                    const newVal = log.new_value[key];
                    if (oldVal !== newVal) {
                      return (
                        <div key={key} className="flex items-center justify-between border-b border-gray-200/40 py-1">
                          <span className="text-gray-550 font-sans">{key}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded line-through">{String(oldVal)}</span>
                            <ArrowRight className="h-3 w-3 text-gray-400" />
                            <span className="text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded font-bold">{String(newVal)}</span>
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

import React, { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, XCircle, FileText, Filter, Edit3, Check, X, ShieldAlert, History } from 'lucide-react';
import api from '../services/api';

export default function Dashboard() {
  const [records, setRecords] = useState([]);
  const [stats, setStats] = useState({
    total_records: 0,
    suspicious_records: 0,
    approved_records: 0,
    failed_imports: 0,
  });
  
  // Filters
  const [sourceFilter, setSourceFilter] = useState('');
  const [scopeFilter, setScopeFilter] = useState('');
  const [suspiciousFilter, setSuspiciousFilter] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  
  // Selection
  const [selectedRecordIds, setSelectedRecordIds] = useState([]);
  
  // Modals & Forms
  const [editingRecord, setEditingRecord] = useState(null);
  const [editForm, setEditForm] = useState({
    activity_type: '',
    quantity: '',
    unit: '',
    emission_factor: '',
    suspicious_flag: false,
    suspicious_reason: '',
    change_reason: '',
  });
  const [auditLogsRecord, setAuditLogsRecord] = useState(null);
  const [recordLogs, setRecordLogs] = useState([]);

  // Action feedback states
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    fetchStats();
    fetchRecords();
    setSelectedRecordIds([]);
  }, [sourceFilter, scopeFilter, suspiciousFilter, statusFilter]);

  const fetchStats = async () => {
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      console.error("Error fetching stats:", err);
    }
  };

  const fetchRecords = async () => {
    try {
      const params = {};
      if (sourceFilter) params.source = sourceFilter;
      if (scopeFilter) params.scope = scopeFilter;
      if (suspiciousFilter) params.suspicious_only = 'true';
      if (statusFilter) params.approval_status = statusFilter;
      
      const data = await api.getEmissions(params);
      setRecords(data.results || data);
    } catch (err) {
      console.error("Error fetching records:", err);
    }
  };

  const handleApprove = async (id) => {
    setActionLoading(true);
    setErrorMsg('');
    setSuccessMsg('');
    const reason = window.prompt("Provide approval note (optional):", "Approved by analyst review.");
    if (reason === null) {
      setActionLoading(false);
      return; // cancelled
    }
    
    try {
      await api.approveEmission(id, reason || "Approved by analyst.");
      setSuccessMsg("Record approved and locked for audit.");
      fetchRecords();
      fetchStats();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Approval failed.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (id) => {
    setActionLoading(true);
    setErrorMsg('');
    setSuccessMsg('');
    const reason = window.prompt("Please provide rejection reason (mandatory):");
    if (!reason) {
      alert("A reason is mandatory to reject a record.");
      setActionLoading(false);
      return;
    }

    try {
      await api.rejectEmission(id, reason);
      setSuccessMsg("Record marked as rejected.");
      fetchRecords();
      fetchStats();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Rejection failed.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleBatchApprove = async () => {
    if (selectedRecordIds.length === 0) return;
    setActionLoading(true);
    setErrorMsg('');
    setSuccessMsg('');
    const reason = window.prompt(
      `Provide approval note for ${selectedRecordIds.length} selected records (optional):`,
      "Approved by analyst batch review."
    );
    if (reason === null) {
      setActionLoading(false);
      return; // cancelled
    }
    
    try {
      const res = await api.approveBatchEmissions(selectedRecordIds, reason || "Batch approved by analyst.");
      setSuccessMsg(res.detail || `Successfully approved ${selectedRecordIds.length} records.`);
      setSelectedRecordIds([]);
      fetchRecords();
      fetchStats();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Batch approval failed.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartEdit = (record) => {
    setEditingRecord(record);
    setEditForm({
      activity_type: record.activity_type,
      quantity: record.quantity,
      unit: record.unit,
      emission_factor: record.emission_factor,
      suspicious_flag: record.suspicious_flag,
      suspicious_reason: record.suspicious_reason || '',
      change_reason: '',
    });
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    if (!editForm.change_reason.trim()) {
      setErrorMsg("A justification/change reason is required to log updates.");
      setActionLoading(false);
      return;
    }

    try {
      await api.updateEmission(editingRecord.id, {
        activity_type: editForm.activity_type,
        quantity: parseFloat(editForm.quantity),
        unit: editForm.unit,
        emission_factor: parseFloat(editForm.emission_factor),
        suspicious_flag: editForm.suspicious_flag,
        suspicious_reason: editForm.suspicious_reason,
        change_reason: editForm.change_reason,
      });
      setSuccessMsg("Record updated successfully. Re-normalization completed.");
      setEditingRecord(null);
      fetchRecords();
      fetchStats();
    } catch (err) {
      const details = err.response?.data;
      if (typeof details === 'object') {
        setErrorMsg(JSON.stringify(details));
      } else {
        setErrorMsg(err.response?.data?.detail || "Failed to update record.");
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleShowHistory = async (record) => {
    setAuditLogsRecord(record);
    try {
      const logs = await api.getAuditLogs(record.id);
      setRecordLogs(logs.results || logs);
    } catch (err) {
      console.error("Error fetching audit logs:", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Messages */}
      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-3">
          <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-3">
          <ShieldAlert className="h-5 w-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        {/* Total Emissions Card */}
        <div className="bg-white border border-gray-200 rounded-2xl p-5 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total Records</p>
            <p className="text-3xl font-extrabold text-gray-900 mt-2">{stats.total_records}</p>
          </div>
          <div className="p-3 bg-gray-100 border border-gray-200 rounded-xl text-gray-700">
            <FileText className="h-6 w-6" />
          </div>
        </div>

        {/* Suspicious Card */}
        <div className="bg-white border border-gray-200 rounded-2xl p-5 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Suspicious Flagged</p>
            <p className="text-3xl font-extrabold text-amber-600 mt-2">{stats.suspicious_records}</p>
          </div>
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-600">
            <AlertTriangle className="h-6 w-6" />
          </div>
        </div>

        {/* Approved Card */}
        <div className="bg-white border border-gray-200 rounded-2xl p-5 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Approved & Locked</p>
            <p className="text-3xl font-extrabold text-emerald-600 mt-2">{stats.approved_records}</p>
          </div>
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-600">
            <CheckCircle2 className="h-6 w-6" />
          </div>
        </div>

        {/* Failed Imports Card */}
        <div className="bg-white border border-gray-200 rounded-2xl p-5 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Failed Imports</p>
            <p className="text-3xl font-extrabold text-rose-600 mt-2">{stats.failed_imports}</p>
          </div>
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-600">
            <XCircle className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Filter and Content section */}
      <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
        {/* Filters Header */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4 text-gray-800 font-semibold text-sm">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-brand-600" />
              <span>Refine Ingestion Stream</span>
            </div>
            {selectedRecordIds.length > 0 && (
              <div className="flex items-center gap-2.5 bg-brand-50 border border-brand-100 px-2.5 py-1 rounded-lg">
                <span className="text-xs font-semibold text-brand-700 font-mono">{selectedRecordIds.length} selected</span>
                <button
                  onClick={handleBatchApprove}
                  disabled={actionLoading}
                  className="bg-brand-600 hover:bg-brand-500 text-white font-semibold text-[10px] px-2 py-1 rounded transition-all shadow-md active:scale-95 flex items-center gap-1 animate-pulse"
                >
                  <Check className="h-3 w-3" />
                  Approve Selected
                </button>
                <button
                  onClick={() => setSelectedRecordIds([])}
                  className="text-gray-500 hover:text-gray-700 text-[10px] px-1"
                >
                  Clear
                </button>
              </div>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Source */}
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="bg-white border border-gray-200 text-gray-800 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-brand-500 outline-none"
            >
              <option value="">All Sources</option>
              <option value="SAP">SAP Procurement</option>
              <option value="UTILITY">Utility Electricity</option>
              <option value="TRAVEL">Navan Travel</option>
            </select>

            {/* Scope */}
            <select
              value={scopeFilter}
              onChange={(e) => setScopeFilter(e.target.value)}
              className="bg-white border border-gray-200 text-gray-800 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-brand-500 outline-none"
            >
              <option value="">All Scopes</option>
              <option value="Scope1">Scope 1 - Direct</option>
              <option value="Scope2">Scope 2 - Utility</option>
              <option value="Scope3">Scope 3 - Travel</option>
            </select>

            {/* Status */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-white border border-gray-200 text-gray-800 text-xs rounded-lg px-3 py-2 focus:ring-1 focus:ring-brand-500 outline-none"
            >
              <option value="">All Statuses</option>
              <option value="PENDING">Pending</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>

            {/* Suspicious toggle */}
            <button
              onClick={() => setSuspiciousFilter(!suspiciousFilter)}
              className={`text-xs px-3 py-2 rounded-lg border font-medium transition-all ${
                suspiciousFilter
                  ? 'bg-amber-50 border-amber-200 text-amber-700'
                  : 'bg-white border-gray-200 text-gray-600 hover:text-gray-800'
              }`}
            >
              Suspicious Only
            </button>
          </div>
        </div>

        {/* Data Table */}
        <div className="overflow-x-auto">
          {records.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              No matching normalized emission records found. Try uploading a source file.
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-gray-50 text-gray-600 font-semibold border-b border-gray-200">
                  <th className="px-6 py-4 w-12 text-center">
                    <input
                      type="checkbox"
                      checked={records.length > 0 && records.filter(r => !r.locked_for_audit).every(r => selectedRecordIds.includes(r.id))}
                      onChange={(e) => {
                        const unlockable = records.filter(r => !r.locked_for_audit);
                        if (e.target.checked) {
                           setSelectedRecordIds(prev => {
                            const newIds = [...prev];
                            unlockable.forEach(r => {
                              if (!newIds.includes(r.id)) newIds.push(r.id);
                            });
                            return newIds;
                          });
                        } else {
                          setSelectedRecordIds(prev => prev.filter(id => !unlockable.some(r => r.id === id)));
                        }
                      }}
                      className="accent-brand-600 h-4 w-4 bg-white border-gray-300 rounded cursor-pointer"
                    />
                  </th>
                  <th className="px-6 py-4">Source</th>
                  <th className="px-6 py-4">Scope</th>
                  <th className="px-6 py-4">Activity Type</th>
                  <th className="px-6 py-4">Activity Date</th>
                  <th className="px-6 py-4">Original Qty</th>
                  <th className="px-6 py-4">Normalized Qty</th>
                  <th className="px-6 py-4">Emission Factor</th>
                  <th className="px-6 py-4 text-right">Emissions (tCO2e)</th>
                  <th className="px-6 py-4 text-center">Suspicious</th>
                  <th className="px-6 py-4 text-center">Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {records.map((record) => (
                  <tr key={record.id} className="table-row-hover text-gray-700 border-b border-gray-100">
                    <td className="px-6 py-4 text-center w-12">
                      {!record.locked_for_audit ? (
                        <input
                          type="checkbox"
                          checked={selectedRecordIds.includes(record.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedRecordIds(prev => [...prev, record.id]);
                            } else {
                              setSelectedRecordIds(prev => prev.filter(id => id !== record.id));
                            }
                          }}
                          className="accent-brand-600 h-4 w-4 bg-white border-gray-300 rounded cursor-pointer"
                        />
                      ) : (
                        <input
                          type="checkbox"
                          disabled
                          checked={false}
                          className="h-4 w-4 bg-gray-100 border-gray-200 rounded opacity-25 cursor-not-allowed"
                        />
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                        record.source_type === 'SAP' 
                           ? 'bg-blue-50 text-blue-700 border border-blue-200' 
                          : record.source_type === 'UTILITY'
                          ? 'bg-purple-50 text-purple-700 border border-purple-200'
                          : 'bg-pink-50 text-pink-700 border border-pink-200'
                      }`}>
                        {record.source_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-semibold text-gray-500">{record.scope_category}</td>
                    <td className="px-6 py-4 font-medium text-gray-900">{record.activity_type}</td>
                    <td className="px-6 py-4 font-mono text-gray-500">
                      {record.activity_date ? new Date(record.activity_date).toLocaleDateString(undefined, {year: 'numeric', month: 'short', day: 'numeric'}) : '-'}
                      {record.billing_period_start && record.billing_period_end && (
                        <span className="block text-[9px] text-gray-400 font-sans mt-0.5">
                          Period: {new Date(record.billing_period_start).toLocaleDateString(undefined, {month: 'short', day: 'numeric'})} - {new Date(record.billing_period_end).toLocaleDateString(undefined, {month: 'short', day: 'numeric'})}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 font-mono text-gray-500">{parseFloat(record.quantity).toLocaleString()} {record.unit}</td>
                    <td className="px-6 py-4 font-mono text-gray-800">{parseFloat(record.normalized_quantity).toLocaleString()} {record.normalized_unit}</td>
                    <td className="px-6 py-4 font-mono text-gray-500">{record.emission_factor}</td>
                    <td className="px-6 py-4 text-right font-mono font-bold text-emerald-600">
                      {parseFloat(record.calculated_emission).toFixed(4)}
                    </td>
                    <td className="px-6 py-4 text-center">
                      {record.suspicious_flag ? (
                        <div className="inline-flex items-center justify-center text-amber-600 group relative cursor-pointer" title={record.suspicious_reason}>
                          <AlertTriangle className="h-5 w-5" />
                          <span className="sr-only">Suspicious</span>
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                        record.approval_status === 'APPROVED'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : record.approval_status === 'REJECTED'
                          ? 'bg-rose-50 text-rose-700 border-rose-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}>
                        {record.approval_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right space-x-1.5 whitespace-nowrap">
                      <button
                        onClick={() => handleShowHistory(record)}
                        className="text-gray-400 hover:text-gray-700 p-1 rounded hover:bg-gray-100"
                        title="Audit Logs"
                      >
                        <History className="h-4 w-4" />
                      </button>
                      
                      {!record.locked_for_audit ? (
                        <>
                          <button
                            onClick={() => handleStartEdit(record)}
                            className="text-brand-600 hover:text-brand-800 p-1 rounded hover:bg-gray-100"
                            title="Edit"
                          >
                            <Edit3 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleApprove(record.id)}
                            className="text-emerald-600 hover:text-emerald-800 p-1 rounded hover:bg-gray-100"
                            title="Approve"
                            disabled={actionLoading}
                          >
                            <Check className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleReject(record.id)}
                            className="text-rose-600 hover:text-rose-800 p-1 rounded hover:bg-gray-100"
                            title="Reject"
                            disabled={actionLoading}
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </>
                      ) : (
                        <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold px-2 py-1 bg-gray-100 border border-gray-200 rounded">Locked</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Edit Record Modal */}
      {editingRecord && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-gray-200 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
              <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <Edit3 className="h-5 w-5 text-brand-600" />
                Edit Emission Record
              </h3>
              <button onClick={() => setEditingRecord(null)} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSaveEdit} className="p-6 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                {/* Activity Type */}
                <div className="col-span-2">
                  <label className="block text-gray-500 font-semibold mb-1">Activity Type</label>
                  <input
                    type="text"
                    value={editForm.activity_type}
                    onChange={(e) => setEditForm({ ...editForm, activity_type: e.target.value })}
                    className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 focus:ring-1 focus:ring-brand-500 outline-none"
                    required
                  />
                </div>

                {/* Raw Qty */}
                <div>
                  <label className="block text-gray-500 font-semibold mb-1">Quantity</label>
                  <input
                    type="number"
                    step="any"
                    value={editForm.quantity}
                    onChange={(e) => setEditForm({ ...editForm, quantity: e.target.value })}
                    className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 focus:ring-1 focus:ring-brand-500 outline-none"
                    required
                  />
                </div>

                {/* Raw Unit */}
                <div>
                  <label className="block text-gray-500 font-semibold mb-1">Unit</label>
                  <input
                    type="text"
                    value={editForm.unit}
                    onChange={(e) => setEditForm({ ...editForm, unit: e.target.value })}
                    className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 focus:ring-1 focus:ring-brand-500 outline-none"
                    required
                  />
                </div>

                {/* Emission Factor */}
                <div className="col-span-2">
                  <label className="block text-gray-500 font-semibold mb-1">Emission Factor (kg CO2e / unit)</label>
                  <input
                    type="number"
                    step="any"
                    value={editForm.emission_factor}
                    onChange={(e) => setEditForm({ ...editForm, emission_factor: e.target.value })}
                    className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 focus:ring-1 focus:ring-brand-500 outline-none"
                    required
                  />
                </div>

                {/* Suspicious Toggler */}
                <div className="col-span-2 flex items-center gap-2 py-1">
                  <input
                    type="checkbox"
                    id="suspicious_chk"
                    checked={editForm.suspicious_flag}
                    onChange={(e) => setEditForm({ ...editForm, suspicious_flag: e.target.checked })}
                    className="accent-brand-600 h-4 w-4 bg-white border-gray-300 rounded"
                  />
                  <label htmlFor="suspicious_chk" className="text-gray-700 font-semibold cursor-pointer">Flag as Suspicious</label>
                </div>

                {editForm.suspicious_flag && (
                  <div className="col-span-2">
                    <label className="block text-gray-500 font-semibold mb-1">Suspicious Reason</label>
                    <textarea
                      value={editForm.suspicious_reason}
                      onChange={(e) => setEditForm({ ...editForm, suspicious_reason: e.target.value })}
                      className="w-full bg-white border border-gray-200 text-gray-800 rounded-lg px-3 py-2 focus:ring-1 focus:ring-brand-500 outline-none h-16"
                    />
                  </div>
                )}

                {/* Change Reason (MANDATORY FOR AUDITING) */}
                <div className="col-span-2 border-t border-gray-200 pt-4">
                  <label className="block text-amber-600 font-semibold mb-1">Justification/Change Reason (Mandatory Audit Trail)*</label>
                  <textarea
                    placeholder="Provide detailed context on why this record was updated (e.g. Corrected fuel units based on delivery bill)..."
                    value={editForm.change_reason}
                    onChange={(e) => setEditForm({ ...editForm, change_reason: e.target.value })}
                    className="w-full bg-white border border-amber-300 text-gray-800 rounded-lg px-3 py-2 focus:ring-1 focus:ring-amber-500 outline-none h-20"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 border-t border-gray-200 pt-4 mt-6">
                <button
                  type="button"
                  onClick={() => setEditingRecord(null)}
                  className="bg-white border border-gray-200 text-gray-500 px-4 py-2 rounded-lg hover:text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="bg-brand-600 hover:bg-brand-500 text-white font-semibold px-4 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-md shadow-brand-600/20"
                >
                  {actionLoading ? "Saving & Re-calculating..." : "Apply & Recalculate"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Record Audit History Log Modal */}
      {auditLogsRecord && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-gray-250 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
              <div>
                <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                  <History className="h-5 w-5 text-brand-600" />
                  Audit Logs & Ingestion History
                </h3>
                <p className="text-[10px] text-gray-500 mt-1">Record ID: {auditLogsRecord.id}</p>
              </div>
              <button onClick={() => setAuditLogsRecord(null)} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-6 max-h-[500px] overflow-y-auto space-y-6 text-xs">
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-2">
                <p className="font-semibold text-gray-700">Origin / Raw Ingestion State:</p>
                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-gray-600 bg-white p-2.5 rounded border border-gray-200">
                  {Object.entries(auditLogsRecord.raw_record_data || {}).map(([k, v]) => (
                    <div key={k}>
                      <span className="text-brand-600">{k}:</span> {String(v)}
                    </div>
                  ))}
                  {(!auditLogsRecord.raw_record_data || Object.keys(auditLogsRecord.raw_record_data).length === 0) && (
                    <div className="col-span-2 text-gray-455">Manually Created Record</div>
                  )}
                </div>
              </div>

              <div>
                <p className="font-semibold text-gray-700 mb-3">Audit Logs (Newest first):</p>
                {recordLogs.length === 0 ? (
                  <p className="text-gray-400 text-center py-4 bg-gray-50 border border-gray-200 border-dashed rounded-lg">No modifications logged yet. Record is in its raw imported state.</p>
                ) : (
                  <div className="relative border-l border-gray-200 pl-4 space-y-6 ml-2">
                    {recordLogs.map((log) => (
                      <div key={log.id} className="relative">
                        {/* Dot */}
                        <div className="absolute -left-[21px] top-1.5 h-3.5 w-3.5 rounded-full border-2 border-white bg-brand-500" />
                        
                        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-2">
                          <div className="flex justify-between text-[10px] text-gray-500 font-medium">
                            <span className="text-gray-700 font-semibold">User: {log.changed_by}</span>
                            <span>{new Date(log.timestamp).toLocaleString()}</span>
                          </div>
                          <p className="text-gray-800 mt-1"><span className="text-amber-700 font-medium font-mono bg-amber-50 border border-amber-200 px-1 py-0.5 rounded mr-1">Justification:</span> {log.change_reason}</p>
                          
                          {/* Diff Box */}
                          <div className="mt-3 text-[10px] bg-white p-3 rounded border border-gray-200 font-mono text-gray-655 space-y-1">
                            <p className="text-gray-500 font-semibold border-b border-gray-200 pb-1 mb-1 font-sans">State Transition Deltas:</p>
                            {Object.keys(log.new_value).map((key) => {
                              const oldV = log.old_value[key];
                              const newV = log.new_value[key];
                              if (oldV !== newV) {
                                return (
                                  <div key={key} className="flex flex-wrap items-center">
                                    <span className="text-gray-700 mr-1.5 font-sans">{key}:</span>
                                    <span className="text-rose-600 bg-rose-50 px-1 rounded line-through mr-1.5">{String(oldV)}</span>
                                    <span className="text-gray-400 mr-1.5">➔</span>
                                    <span className="text-emerald-600 bg-emerald-50 px-1 rounded">{String(newV)}</span>
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
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end bg-gray-50">
              <button
                type="button"
                onClick={() => setAuditLogsRecord(null)}
                className="bg-brand-600 hover:bg-brand-500 text-white font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                Close Trail
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

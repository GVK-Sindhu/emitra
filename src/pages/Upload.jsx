import React, { useEffect, useState } from 'react';
import { UploadCloud, FileSpreadsheet, CheckCircle2, AlertOctagon, HelpCircle, ShieldAlert, Loader2, ArrowRight } from 'lucide-react';
import api from '../services/api';

export default function Upload() {
  const [uploads, setUploads] = useState([]);
  const [file, setFile] = useState(null);
  const [sourceType, setSourceType] = useState('SAP');
  const [uploadedBy, setUploadedBy] = useState('analyst@acme.com');

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    fetchUploads();
  }, []);

  const fetchUploads = async () => {
    try {
      const data = await api.getUploads();
      setUploads(data.results || data);
    } catch (err) {
      console.error("Error fetching uploads:", err);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setErrorMsg('');
      setSuccessMsg('');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setErrorMsg('');
      setSuccessMsg('');
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg("Please select or drag a CSV file first.");
      return;
    }
    setLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      await api.uploadFile(file, sourceType, uploadedBy);
      setSuccessMsg(`File '${file.name}' uploaded and normalized successfully!`);
      setFile(null);
      fetchUploads();
    } catch (err) {
      setErrorMsg(err.response?.data?.error_message || err.response?.data?.detail || "Ingestion pipeline error. Please check CSV columns.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-950/40 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Ingest New Dataset</h3>
          
          <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Source System Integration</label>
                <select
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 text-slate-200 rounded-lg px-3 py-2.5 focus:ring-1 focus:ring-brand-500 outline-none"
                >
                  <option value="SAP">SAP ERP (Fuel / Materials)</option>
                  <option value="UTILITY">Utility Portal (Electricity)</option>
                  <option value="TRAVEL">Navan/Concur API (Business Travel)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Ingesting Analyst User</label>
                <input
                  type="email"
                  value={uploadedBy}
                  onChange={(e) => setUploadedBy(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 text-slate-200 rounded-lg px-3 py-2.5 focus:ring-1 focus:ring-brand-500 outline-none"
                  required
                />
              </div>
            </div>

            {/* Drag & Drop Area */}
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-8 text-center flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
                file
                  ? 'border-brand-500/50 bg-brand-500/5'
                  : 'border-slate-800 hover:border-slate-700 bg-slate-950/30'
              }`}
              onClick={() => document.getElementById('csv-file-input').click()}
            >
              <input
                id="csv-file-input"
                type="file"
                accept=".csv"
                className="hidden"
                onChange={handleFileChange}
              />
              <UploadCloud className={`h-10 w-10 mb-3 ${file ? 'text-brand-500' : 'text-slate-500'}`} />
              {file ? (
                <div>
                  <p className="text-sm font-semibold text-slate-200">{file.name}</p>
                  <p className="text-[10px] text-slate-400 mt-1">{(file.size / 1024).toFixed(2)} KB • Ready for ingest</p>
                </div>
              ) : (
                <div>
                  <p className="text-sm font-semibold text-slate-300">Drag & Drop CSV export file here</p>
                  <p className="text-[10px] text-slate-500 mt-1">or click to browse local filesystem</p>
                </div>
              )}
            </div>

            {/* Notifications */}
            {successMsg && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                <span>{successMsg}</span>
              </div>
            )}
            {errorMsg && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 flex-shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={loading || !file}
                className="bg-brand-600 hover:bg-brand-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-5 py-2.5 rounded-lg transition-colors flex items-center gap-2 shadow-lg shadow-brand-600/10"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Processing Normalization Pipeline...</span>
                  </>
                ) : (
                  <>
                    <span>Execute Normalization</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Integration Instructions */}
        <div className="bg-slate-950/40 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Required Schema Templates</h3>
          <div className="space-y-4 text-[11px] text-slate-400">
            <div>
              <p className="font-semibold text-slate-300 flex items-center gap-1.5">
                <FileSpreadsheet className="h-4 w-4 text-blue-400" />
                SAP Fuel/Procurement Export (German & English)
              </p>
              <p className="mt-1 font-mono text-[9px] bg-slate-950 p-2 rounded border border-slate-900 overflow-x-auto whitespace-nowrap">
                Plant Code,Material,Fuel Quantity,Fuel Unit,Posting Date,Vendor<br/>
                DE_MUN_01,Diesel,12000,L,2026-05-15,Shell Inc.<br/>
                Werksnummer,Materialnummer,Menge,Einheit,Buchungsdatum,Lieferant
              </p>
            </div>
            
            <div>
              <p className="font-semibold text-slate-300 flex items-center gap-1.5">
                <FileSpreadsheet className="h-4 w-4 text-purple-400" />
                Utility Electricity Export
              </p>
              <p className="mt-1 font-mono text-[9px] bg-slate-950 p-2 rounded border border-slate-900 overflow-x-auto whitespace-nowrap">
                Meter ID,Billing Period Start,Billing Period End,Usage,Unit,Tariff<br/>
                MTR-98213,2026-04-15,2026-05-14,4820,kWh,Commercial Peak
              </p>
            </div>

            <div>
              <p className="font-semibold text-slate-300 flex items-center gap-1.5">
                <FileSpreadsheet className="h-4 w-4 text-pink-400" />
                Corporate Travel (Navan/Concur API-style)
              </p>
              <p className="mt-1 font-mono text-[9px] bg-slate-950 p-2 rounded border border-slate-900 overflow-x-auto whitespace-nowrap">
                Employee ID,Flight Type,From Airport,To Airport,Distance,Hotel Nights,Ground Transport<br/>
                EMP_091,Domestic,JFK,LAX,2475,4,Taxi (15 miles)
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Uploads History */}
      <div className="bg-slate-950/40 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="px-6 py-4 bg-slate-950/60 border-b border-slate-800">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Ingestion Activity Audit Logs</h3>
        </div>
        <div className="overflow-x-auto">
          {uploads.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-xs">
              No files uploaded yet.
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-950/20 text-slate-400 font-semibold border-b border-slate-800">
                  <th className="px-6 py-4">Integration Type</th>
                  <th className="px-6 py-4">Uploaded File</th>
                  <th className="px-6 py-4">Uploader</th>
                  <th className="px-6 py-4">Timestamp</th>
                  <th className="px-6 py-4">Ingestion Status</th>
                  <th className="px-6 py-4">Notes / Error details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {uploads.map((up) => (
                  <tr key={up.id} className="table-row-hover text-slate-300">
                    <td className="px-6 py-4 font-semibold">
                      <span className={`px-2 py-0.5 rounded font-mono text-[10px] font-bold ${
                        up.source_type === 'SAP' 
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' 
                          : up.source_type === 'UTILITY'
                          ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                          : 'bg-pink-500/10 text-pink-400 border border-pink-500/20'
                      }`}>
                        {up.source_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 truncate max-w-xs font-mono text-slate-200" title={up.uploaded_file}>
                      {up.uploaded_file.split('/').pop()}
                    </td>
                    <td className="px-6 py-4 text-slate-400">{up.uploaded_by}</td>
                    <td className="px-6 py-4 text-slate-400">
                      {new Date(up.uploaded_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                        up.ingestion_status === 'SUCCESS'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : up.ingestion_status === 'FAILED'
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse'
                      }`}>
                        {up.ingestion_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono text-[10px] text-slate-400 truncate max-w-sm" title={up.error_message}>
                      {up.error_message || <span className="text-slate-600">-</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

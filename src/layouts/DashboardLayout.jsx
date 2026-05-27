import React from 'react';
import { LayoutDashboard, UploadCloud, History, Building2, User } from 'lucide-react';

export default function DashboardLayout({ children, currentPage, setCurrentPage }) {
  const navigation = [
    { name: 'Dashboard', id: 'dashboard', icon: LayoutDashboard },
    { name: 'File Ingest', id: 'upload', icon: UploadCloud },
    { name: 'Audit Trail', id: 'audit-log', icon: History },
  ];

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <div className="hidden md:flex md:flex-shrink-0">
        <div className="flex flex-col w-64 border-r border-slate-800 bg-slate-950">
          <div className="flex items-center h-16 px-6 border-b border-slate-800">
            <span className="text-xl font-bold tracking-tight text-brand-500 flex items-center gap-2">
              <span>🌱</span> Emitra <span className="text-[10px] uppercase font-semibold bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">MVP</span>
            </span>
          </div>
          <div className="flex-1 flex flex-col overflow-y-auto py-4">
            <nav className="flex-1 px-4 space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentPage(item.id)}
                    className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-lg transition-all duration-150 group ${
                      isActive
                        ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/10'
                        : 'text-slate-400 hover:bg-slate-900 hover:text-slate-100'
                    }`}
                  >
                    <Icon
                      className={`mr-3 h-5 w-5 ${
                        isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-100'
                      }`}
                    />
                    {item.name}
                  </button>
                );
              })}
            </nav>
          </div>
          
          {/* Tenant Indicator */}
          <div className="p-4 border-t border-slate-800 bg-slate-950/50">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded bg-slate-800 border border-slate-700">
                <Building2 className="h-5 w-5 text-brand-500" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-slate-200 truncate">Acme Corporation</p>
                <p className="text-[10px] text-slate-500 truncate">Organization Tenant</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden bg-slate-900 text-slate-100">
        <header className="flex justify-between items-center h-16 px-6 bg-slate-950/30 border-b border-slate-800/60">
          <h1 className="text-lg font-semibold tracking-tight text-white capitalize">
            {currentPage === 'dashboard' ? 'Emission Records Review' : currentPage === 'upload' ? 'Data Ingestion Platform' : 'System Audit Trail'}
          </h1>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-xs">
              <User className="h-4 w-4 text-brand-500" />
              <span>analyst@acme.com</span>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6 bg-slate-900">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

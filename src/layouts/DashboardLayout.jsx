import React from 'react';
import { LayoutDashboard, UploadCloud, History, Building2, User, Leaf } from 'lucide-react';

export default function DashboardLayout({ children, currentPage, setCurrentPage }) {
  const navigation = [
    { name: 'Dashboard', id: 'dashboard', icon: LayoutDashboard },
    { name: 'File Ingest', id: 'upload', icon: UploadCloud },
    { name: 'Audit Trail', id: 'audit-log', icon: History },
  ];

  return (
    <div className="flex h-screen bg-gray-50 text-gray-800 overflow-hidden font-sans">
      {/* Sidebar */}
      <div className="hidden md:flex md:flex-shrink-0">
        <div className="flex flex-col w-64 border-r border-gray-200 bg-white shadow-sm">
          <div className="flex items-center h-16 px-6 border-b border-gray-200">
            <span className="text-xl font-bold tracking-tight text-brand-600 flex items-center gap-2">
              <Leaf className="h-5 w-5 text-brand-600" /> Emitra <span className="text-[10px] uppercase font-semibold bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded border border-gray-200">MVP</span>
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
                        ? 'bg-brand-600 text-white shadow-md shadow-brand-600/20'
                        : 'text-gray-500 hover:bg-gray-100 hover:text-gray-800'
                    }`}
                  >
                    <Icon
                      className={`mr-3 h-5 w-5 ${
                        isActive ? 'text-white' : 'text-gray-400 group-hover:text-gray-600'
                      }`}
                    />
                    {item.name}
                  </button>
                );
              })}
            </nav>
          </div>
          
          {/* Tenant Indicator */}
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded bg-white border border-gray-200 shadow-sm">
                <Building2 className="h-5 w-5 text-brand-600" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-gray-700 truncate">Acme Corporation</p>
                <p className="text-[10px] text-gray-400 truncate">Organization Tenant</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden bg-gray-50 text-gray-800">
        <header className="flex justify-between items-center h-16 px-6 bg-white border-b border-gray-200 shadow-sm">
          <h1 className="text-lg font-semibold tracking-tight text-gray-800 capitalize">
            {currentPage === 'dashboard' ? 'Emission Records Review' : currentPage === 'upload' ? 'Data Ingestion Platform' : 'System Audit Trail'}
          </h1>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 border border-gray-200 text-gray-600 text-xs">
              <User className="h-4 w-4 text-brand-600" />
              <span>analyst@acme.com</span>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6 bg-gray-50">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

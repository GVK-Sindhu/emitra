import React, { useState } from 'react';
import DashboardLayout from './layouts/DashboardLayout';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import AuditLogPage from './pages/AuditLogPage';

export default function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'upload':
        return <Upload />;
      case 'audit-log':
        return <AuditLogPage />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <DashboardLayout currentPage={currentPage} setCurrentPage={setCurrentPage}>
      {renderPage()}
    </DashboardLayout>
  );
}

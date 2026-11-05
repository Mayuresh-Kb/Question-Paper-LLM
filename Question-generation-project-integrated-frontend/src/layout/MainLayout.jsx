// src/layouts/MainLayout.jsx
import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import ProgressBar from '../components/ProgressBar';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const MainLayout = () => {
  const location = useLocation();
  const isWorkflowRoute = ['/upload', '/configure', '/download'].includes(location.pathname);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800 selection:bg-blue-600 selection:text-white">
      {/* Header */}
      <Navbar />

      {/* Main Content */}
      <main className="flex-1 w-full">
        {isWorkflowRoute ? (
          <div className="py-8 sm:py-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto">
            {/* Step Progress Bar */}
            <ProgressBar />

            {/* Workflow Card */}
            <div className="bg-white border border-slate-200/80 rounded-2xl shadow-sm p-6 sm:p-8 md:p-10 transition-all">
              <Outlet />
            </div>
          </div>
        ) : (
          <Outlet />
        )}
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default MainLayout;


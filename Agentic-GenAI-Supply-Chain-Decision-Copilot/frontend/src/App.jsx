import React, { useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import Inventory from './pages/Inventory';
import Forecast from './pages/Forecast';
import Suppliers from './pages/Suppliers';
import Copilot from './pages/Copilot';
import Simulation from './pages/Simulation';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');

  const renderActivePage = () => {
    switch (activeTab) {
      case 'overview':
        return <Overview onNavigate={setActiveTab} />;
      case 'inventory':
        return <Inventory />;
      case 'forecast':
        return <Forecast />;
      case 'suppliers':
        return <Suppliers />;
      case 'copilot':
        return <Copilot />;
      case 'simulation':
        return <Simulation />;
      default:
        return <Overview onNavigate={setActiveTab} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation Header */}
      <Header />
      
      {/* Main Body Shell */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Navigation */}
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        
        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-950">
          <div className="max-w-7xl mx-auto space-y-6">
            {renderActivePage()}
          </div>
        </main>
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { 
  Package, 
  AlertOctagon, 
  ShoppingCart, 
  Clock, 
  ArrowRight,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis } from 'recharts';
import { getInventoryRisks, getProcurementRecommendations } from '../api/inventory';
import MetricCard from '../components/common/MetricCard';
import RiskBadge from '../components/common/RiskBadge';
import AdvisoryNotice from '../components/common/AdvisoryNotice';
import LoadingSkeleton from '../components/common/LoadingSkeleton';
import ErrorMessage from '../components/common/ErrorMessage';

const COLORS = {
  LOW: '#10b981',      // Emerald
  MEDIUM: '#f59e0b',   // Amber/Yellow
  HIGH: '#f97316',     // Orange
  CRITICAL: '#ef4444', // Red
};

export default function Overview({ onNavigate }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [recData, setRecData] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [risks, recs] = await Promise.all([
        getInventoryRisks({ limit: 100 }),
        getProcurementRecommendations({ limit: 50 }),
      ]);
      setRiskData(risks);
      setRecData(recs);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton type="cards" count={4} />
        <LoadingSkeleton type="chart" />
        <LoadingSkeleton type="table" count={5} />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={fetchData} title="Failed to Load Overview Dashboard" />;
  }

  // Derive metrics safely from API response
  const totalProducts = riskData?.total_count || 0;
  const criticalCount = riskData?.critical_count || 0;
  const highCount = riskData?.high_count || 0;
  const urgentReorders = recData?.urgent_reorders || 0;

  // Calculate average days of inventory safely
  const items = riskData?.items || [];
  const validDoi = items.filter(i => i.days_of_inventory !== null && i.days_of_inventory !== undefined);
  const avgDoi = validDoi.length > 0 
    ? (validDoi.reduce((acc, i) => acc + i.days_of_inventory, 0) / validDoi.length).toFixed(1)
    : 'N/A';

  // Format chart data for risk distribution
  const chartData = [
    { name: 'LOW', value: riskData?.low_count || 0 },
    { name: 'MEDIUM', value: riskData?.medium_count || 0 },
    { name: 'HIGH', value: riskData?.high_count || 0 },
    { name: 'CRITICAL', value: riskData?.critical_count || 0 },
  ].filter(d => d.value > 0);

  const highRiskItems = items.filter(i => i.risk_level === 'CRITICAL' || i.risk_level === 'HIGH').slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
            Supply Chain Control Tower
            <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded font-mono font-normal">
              Live Operations
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Real-time supply chain health, inventory risks, and procurement recommendations.
          </p>
        </div>
        <button
          onClick={fetchData}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition-all border border-slate-700 self-start md:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Data</span>
        </button>
      </div>

      <AdvisoryNotice compact />

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Monitored SKUs"
          value={totalProducts}
          subtitle="PostgreSQL Managed Items"
          icon={Package}
          badgeText="Active"
          badgeColor="indigo"
        />
        <MetricCard
          title="Critical / High Risk"
          value={criticalCount + highCount}
          subtitle={`${criticalCount} Critical, ${highCount} High`}
          icon={AlertOctagon}
          badgeText={criticalCount > 0 ? "Action Required" : "Monitored"}
          badgeColor={criticalCount > 0 ? "critical" : "high"}
        />
        <MetricCard
          title="Urgent Reorder Orders"
          value={urgentReorders}
          subtitle="Deterministic Risk Engine"
          icon={ShoppingCart}
          badgeText="Advisory"
          badgeColor="amber"
        />
        <MetricCard
          title="Avg Days of Supply"
          value={`${avgDoi} Days`}
          subtitle="Stock Coverage Horizon"
          icon={Clock}
          badgeText="Coverage"
          badgeColor="emerald"
        />
      </div>

      {/* Charts & Breakdown Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Chart */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4 shadow-lg">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-100 text-sm tracking-tight">Risk Distribution</h3>
            <span className="text-[10px] font-mono text-slate-500 uppercase">Risk Level Breakdown</span>
          </div>

          <div className="h-56">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
                    itemStyle={{ color: '#f8fafc', fontSize: '12px' }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    height={36}
                    formatter={(value) => <span className="text-xs text-slate-300 font-mono">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500 font-mono">
                No risk data available
              </div>
            )}
          </div>
        </div>

        {/* Urgent Procurement Recommendations Card */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4 shadow-lg flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <h3 className="font-semibold text-slate-100 text-sm">Procurement Recommendations</h3>
              </div>
              <button
                onClick={() => onNavigate('inventory')}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-mono flex items-center gap-1 transition-colors"
              >
                <span>View All Inventory</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {recData?.items && recData.items.length > 0 ? (
              <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
                {recData.items.slice(0, 4).map((rec, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-950/70 border border-slate-800/80 flex items-center justify-between text-xs">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-slate-200">{rec.sku}</span>
                        <span className="text-slate-400">• {rec.product_name}</span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        Vendor: <span className="text-slate-300 font-mono">{rec.supplier_name}</span> | Reorder Point: <span className="font-mono">{rec.reorder_point}</span>
                      </p>
                    </div>

                    <div className="text-right space-y-1">
                      <span className={`inline-block px-2 py-0.5 rounded font-mono font-semibold text-[10px] border ${
                        rec.action === 'URGENT_REORDER'
                          ? 'bg-rose-950/80 text-rose-300 border-rose-500/40'
                          : 'bg-amber-950/80 text-amber-300 border-amber-500/40'
                      }`}>
                        RECOMMENDED: {rec.action} ({rec.recommended_order_quantity} units)
                      </span>
                      <p className="text-[10px] text-slate-500 italic">Advisory only</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 py-6 text-center font-mono">
                No immediate reorders required. Inventory positions are stable.
              </p>
            )}
          </div>

          <div className="pt-3 border-t border-slate-800/60 text-xs text-slate-400 flex items-center justify-between">
            <span>Powered by Phase 4 Inventory Intelligence Engine</span>
            <span className="font-mono text-[10px] text-slate-500">Zero database mutations</span>
          </div>
        </div>
      </div>

      {/* Critical/High Risk Products Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-100 text-sm">High Attention Products</h3>
            <p className="text-xs text-slate-400">Products requiring immediate inventory review</p>
          </div>
          <button
            onClick={() => onNavigate('inventory')}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-mono flex items-center gap-1"
          >
            <span>Full Inventory Table</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">SKU</th>
                <th className="py-2.5 px-3">Product</th>
                <th className="py-2.5 px-3">Warehouse</th>
                <th className="py-2.5 px-3">Stock Position</th>
                <th className="py-2.5 px-3">Days Coverage</th>
                <th className="py-2.5 px-3">Risk Level</th>
                <th className="py-2.5 px-3">Advisory Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {highRiskItems.length > 0 ? (
                highRiskItems.map((item) => (
                  <tr key={item.product_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-3 font-bold text-indigo-300">{item.sku}</td>
                    <td className="py-3 px-3 font-sans font-medium text-slate-200">{item.product_name}</td>
                    <td className="py-3 px-3 text-slate-400">{item.warehouse_code || 'WH-01'}</td>
                    <td className="py-3 px-3">
                      {item.current_stock} <span className="text-slate-500">(Reserved: {item.reserved_stock})</span>
                    </td>
                    <td className="py-3 px-3">
                      {item.days_of_inventory !== null ? `${item.days_of_inventory} Days` : 'N/A'}
                    </td>
                    <td className="py-3 px-3">
                      <RiskBadge level={item.risk_level} score={item.risk_score} size="small" />
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-[10px] font-semibold text-amber-400 bg-amber-950/60 border border-amber-500/30 px-2 py-0.5 rounded">
                        {item.recommended_action || 'MONITOR'}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="py-6 text-center text-slate-500 text-xs">
                    All product inventory levels are currently in optimal condition.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

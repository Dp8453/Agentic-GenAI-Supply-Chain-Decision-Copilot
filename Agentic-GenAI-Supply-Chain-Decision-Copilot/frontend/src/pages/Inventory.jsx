import React, { useState, useEffect } from 'react';
import { Search, Filter, RefreshCw, X, ShieldAlert, PackageCheck, AlertCircle } from 'lucide-react';
import { getInventoryRisks } from '../api/inventory';
import RiskBadge from '../components/common/RiskBadge';
import AdvisoryNotice from '../components/common/AdvisoryNotice';
import LoadingSkeleton from '../components/common/LoadingSkeleton';
import ErrorMessage from '../components/common/ErrorMessage';

export default function Inventory() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [selectedProduct, setSelectedProduct] = useState(null);

  const fetchInventory = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getInventoryRisks({ limit: 100 });
      setData(result);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  const items = data?.items || [];

  const filteredItems = items.filter((item) => {
    const matchesSearch = 
      item.sku?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.product_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesRisk = 
      riskFilter === 'ALL' || item.risk_level?.toUpperCase() === riskFilter.toUpperCase();

    return matchesSearch && matchesRisk;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
            Deterministic Inventory Risk Intelligence
            <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded font-mono font-normal">
              Phase 4 Risk Engine
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Real-time stock positions, safety stock thresholds, stockout projections, and advisory reorders.
          </p>
        </div>
        <button
          onClick={fetchInventory}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition-all border border-slate-700 self-start md:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Table</span>
        </button>
      </div>

      <AdvisoryNotice compact />

      {/* Filter and Search Bar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 shadow-lg">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search SKU or Product Name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700/80 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        <div className="flex items-center space-x-3 w-full md:w-auto font-mono text-xs">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-slate-400">Risk Level:</span>
          <div className="flex items-center space-x-1">
            {['ALL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((level) => (
              <button
                key={level}
                onClick={() => setRiskFilter(level)}
                className={`px-2.5 py-1 rounded text-[11px] transition-all font-semibold ${
                  riskFilter === level
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Inventory Table */}
      {loading ? (
        <LoadingSkeleton type="table" count={8} />
      ) : error ? (
        <ErrorMessage error={error} onRetry={fetchInventory} title="Unable to Load Inventory Data" />
      ) : (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">SKU</th>
                  <th className="py-3 px-4">Product Name</th>
                  <th className="py-3 px-4">Warehouse</th>
                  <th className="py-3 px-4">Stock (OnHand / Res / Inc)</th>
                  <th className="py-3 px-4">Avg Daily Demand</th>
                  <th className="py-3 px-4">Days Coverage</th>
                  <th className="py-3 px-4">Risk Level</th>
                  <th className="py-3 px-4">Advisory Recommendation</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredItems.length > 0 ? (
                  filteredItems.map((item) => (
                    <tr
                      key={item.product_id}
                      className="hover:bg-slate-800/50 transition-colors cursor-pointer"
                      onClick={() => setSelectedProduct(item)}
                    >
                      <td className="py-3 px-4 font-bold text-indigo-300">{item.sku}</td>
                      <td className="py-3 px-4 font-sans font-medium text-slate-200">{item.product_name}</td>
                      <td className="py-3 px-4 text-slate-400">{item.warehouse_code || 'WH-01'}</td>
                      <td className="py-3 px-4">
                        <span className="font-bold text-slate-100">{item.current_stock}</span>{' '}
                        <span className="text-slate-500 text-[11px]">/ {item.reserved_stock} / {item.incoming_quantity}</span>
                      </td>
                      <td className="py-3 px-4">{item.average_daily_demand?.toFixed(1) || '0.0'} units</td>
                      <td className="py-3 px-4">
                        {item.days_of_inventory !== null ? (
                          <span className={`font-semibold ${
                            item.days_of_inventory < 7 ? 'text-rose-400' : item.days_of_inventory < 14 ? 'text-amber-400' : 'text-emerald-400'
                          }`}>
                            {item.days_of_inventory} Days
                          </span>
                        ) : (
                          'N/A'
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <RiskBadge level={item.risk_level} score={item.risk_score} size="small" />
                      </td>
                      <td className="py-3 px-4">
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                          item.recommended_action === 'URGENT_REORDER'
                            ? 'bg-rose-950/80 text-rose-300 border-rose-500/40'
                            : item.recommended_action === 'REORDER'
                            ? 'bg-amber-950/80 text-amber-300 border-amber-500/40'
                            : 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40'
                        }`}>
                          {item.recommended_action || 'MONITOR'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedProduct(item);
                          }}
                          className="text-[11px] text-indigo-400 hover:text-indigo-300 underline font-sans"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="9" className="py-8 text-center text-slate-500 text-xs">
                      No matching inventory records found for filter "{riskFilter}" and search "{searchTerm}".
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detailed Product Drawer Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setSelectedProduct(null)}
              className="absolute right-4 top-4 text-slate-400 hover:text-slate-200 p-1.5 rounded-lg bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="space-y-1">
              <div className="flex items-center gap-2 font-mono">
                <span className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded font-bold">
                  {selectedProduct.sku}
                </span>
                <span className="text-xs text-slate-400">Product ID: {selectedProduct.product_id}</span>
              </div>
              <h3 className="text-xl font-bold text-slate-100">{selectedProduct.product_name}</h3>
              <p className="text-xs text-slate-400">Warehouse Location: {selectedProduct.warehouse_code || 'WH-01'}</p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs">
              <div>
                <p className="text-[10px] text-slate-500">CURRENT STOCK</p>
                <p className="text-base font-bold text-slate-100">{selectedProduct.current_stock}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500">SAFETY STOCK</p>
                <p className="text-base font-bold text-indigo-400">{selectedProduct.safety_stock}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500">REORDER POINT</p>
                <p className="text-base font-bold text-amber-400">{selectedProduct.reorder_point}</p>
              </div>
              <div>
                <p className="text-[10px] text-slate-500">DAYS COVERAGE</p>
                <p className="text-base font-bold text-emerald-400">
                  {selectedProduct.days_of_inventory !== null ? `${selectedProduct.days_of_inventory} d` : 'N/A'}
                </p>
              </div>
            </div>

            {/* Risk Breakdown & Stockout Projection */}
            <div className="space-y-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800 text-xs">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-slate-200 font-mono flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  Deterministic Risk Assessment
                </h4>
                <RiskBadge level={selectedProduct.risk_level} score={selectedProduct.risk_score} />
              </div>

              <p className="text-slate-300 leading-relaxed font-sans">
                {selectedProduct.explanation || "Risk calculated based on current inventory position, forecast lead-time demand, and supplier historical lead-time variance."}
              </p>

              {selectedProduct.projected_stockout && (
                <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-500/30 text-rose-200 flex items-center gap-2 font-mono">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>
                    Projected Stockout Date: <strong className="text-rose-100">{selectedProduct.projected_stockout_date || 'Within 7 Days'}</strong>
                  </span>
                </div>
              )}
            </div>

            {/* Advisory Recommendation Box */}
            <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/30 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-amber-300 font-semibold uppercase">Advisory Procurement Action</span>
                <span className="text-[10px] text-amber-400/80 bg-amber-900/40 px-2 py-0.5 rounded">Advisory Only</span>
              </div>
              <p className="text-sm font-bold text-slate-100 font-mono">
                RECOMMENDED: {selectedProduct.recommended_action || 'MONITOR'} ({selectedProduct.recommended_order_quantity || 0} units)
              </p>
              <p className="text-xs text-slate-400">
                Minimum Order Quantity (MOQ) rounding and supplier lead-time buffers applied automatically.
              </p>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedProduct(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono rounded-lg transition-colors"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

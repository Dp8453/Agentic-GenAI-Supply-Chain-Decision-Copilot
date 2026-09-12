import React, { useState } from 'react';
import { 
  SlidersHorizontal, 
  Send, 
  TrendingUp, 
  AlertTriangle, 
  Sparkles, 
  ArrowRight, 
  CheckCircle2,
  FileText,
  RefreshCw
} from 'lucide-react';
import { runNaturalLanguageSimulation, runStructuredSimulation } from '../api/simulation';
import MetricCard from '../components/common/MetricCard';
import RiskBadge from '../components/common/RiskBadge';
import AdvisoryNotice from '../components/common/AdvisoryNotice';
import LoadingSkeleton from '../components/common/LoadingSkeleton';
import ErrorMessage from '../components/common/ErrorMessage';

export default function Simulation() {
  const [activeMode, setActiveMode] = useState('nl'); // 'nl' or 'structured'
  const [nlQuestion, setNlQuestion] = useState('What happens if Supplier SUP-001 is delayed by 7 days?');
  
  // Structured form state
  const [scenarioType, setScenarioType] = useState('SUPPLIER_DELAY');
  const [productId, setProductId] = useState(1);
  const [supplierId, setSupplierId] = useState(1);
  const [delayDays, setDelayDays] = useState(7);
  const [demandChangePercent, setDemandChangePercent] = useState(20.0);
  const [transferQuantity, setTransferQuantity] = useState(200);
  const [horizonDays, setHorizonDays] = useState(14);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleRunSimulation = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let res;
      if (activeMode === 'nl') {
        res = await runNaturalLanguageSimulation({ question: nlQuestion });
      } else {
        const payload = {
          scenario_type: scenarioType,
          product_id: Number(productId),
          supplier_id: Number(supplierId),
          delay_days: scenarioType === 'SUPPLIER_DELAY' ? Number(delayDays) : undefined,
          demand_change_percent: scenarioType === 'DEMAND_INCREASE' ? Number(demandChangePercent) : undefined,
          transfer_quantity: scenarioType === 'INVENTORY_TRANSFER' ? Number(transferQuantity) : undefined,
          horizon_days: Number(horizonDays),
        };
        res = await runStructuredSimulation({ scenario: payload });
      }
      setResult(res);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
            What-If Simulation Engine
            <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded font-mono font-normal">
              Phase 9 Engine
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            In-memory baseline vs scenario counterfactual impact analysis.
          </p>
        </div>
      </div>

      <AdvisoryNotice compact />

      {/* Mode Selector Tabs & Input Form */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4 shadow-lg">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center space-x-2 font-mono text-xs">
            <span className="text-slate-400 font-semibold">Mode:</span>
            <button
              onClick={() => setActiveMode('nl')}
              className={`px-3 py-1.5 rounded transition-all font-semibold ${
                activeMode === 'nl'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              Natural Language Scenario
            </button>
            <button
              onClick={() => setActiveMode('structured')}
              className={`px-3 py-1.5 rounded transition-all font-semibold ${
                activeMode === 'structured'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              Structured Parameters
            </button>
          </div>
        </div>

        <form onSubmit={handleRunSimulation} className="space-y-4">
          {activeMode === 'nl' ? (
            <div className="space-y-2">
              <label className="block text-xs font-mono font-semibold text-slate-300">
                Describe Hypothetical What-If Scenario:
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={nlQuestion}
                  onChange={(e) => setNlQuestion(e.target.value)}
                  placeholder="e.g. What happens if Supplier SUP-001 is delayed by 7 days?"
                  className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
                />
                <button
                  type="submit"
                  disabled={loading || !nlQuestion.trim()}
                  className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-mono font-semibold transition-all shadow-md flex items-center gap-2 shrink-0 disabled:opacity-50"
                >
                  <SlidersHorizontal className="w-4 h-4" />
                  <span>Run Simulation</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
              <div className="space-y-1">
                <label className="text-slate-400">Scenario Type</label>
                <select
                  value={scenarioType}
                  onChange={(e) => setScenarioType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200 focus:outline-none"
                >
                  <option value="SUPPLIER_DELAY">Supplier Delay</option>
                  <option value="DEMAND_INCREASE">Demand Increase (+20%)</option>
                  <option value="LEAD_TIME_INCREASE">Lead-Time Surge</option>
                  <option value="INVENTORY_TRANSFER">Inventory Transfer</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-slate-400">Target Product</label>
                <select
                  value={productId}
                  onChange={(e) => setProductId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200 focus:outline-none"
                >
                  <option value={1}>Product 1 — SKU-001</option>
                  <option value={2}>Product 2 — SKU-002</option>
                  <option value={3}>Product 3 — SKU-003</option>
                  <option value={4}>Product 4 — SKU-004</option>
                  <option value={5}>Product 5 — SKU-005</option>
                </select>
              </div>

              {scenarioType === 'SUPPLIER_DELAY' && (
                <div className="space-y-1">
                  <label className="text-slate-400">Delay (Days)</label>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={delayDays}
                    onChange={(e) => setDelayDays(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200"
                  />
                </div>
              )}

              {scenarioType === 'DEMAND_INCREASE' && (
                <div className="space-y-1">
                  <label className="text-slate-400">Demand Surge (%)</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={demandChangePercent}
                    onChange={(e) => setDemandChangePercent(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200"
                  />
                </div>
              )}

              <div className="space-y-1">
                <label className="text-slate-400">Forecast Horizon (Days)</label>
                <select
                  value={horizonDays}
                  onChange={(e) => setHorizonDays(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200 focus:outline-none"
                >
                  <option value={7}>7 Days</option>
                  <option value={14}>14 Days</option>
                  <option value={30}>30 Days</option>
                  <option value={60}>60 Days</option>
                </select>
              </div>

              <div className="sm:col-span-2 lg:col-span-4 flex justify-end">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-mono font-semibold transition-all shadow-md flex items-center gap-2 disabled:opacity-50"
                >
                  <SlidersHorizontal className="w-4 h-4" />
                  <span>Execute Structured Scenario</span>
                </button>
              </div>
            </div>
          )}
        </form>
      </div>

      {loading ? (
        <LoadingSkeleton type="cards" count={4} />
      ) : error ? (
        <ErrorMessage error={error} onRetry={handleRunSimulation} title="Simulation Execution Failed" />
      ) : result ? (
        /* Baseline vs Simulated Results View */
        <div className="space-y-6">
          {/* Summary Banner */}
          <div className="p-4 rounded-xl bg-slate-900 border border-indigo-500/30 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono text-indigo-400 font-semibold uppercase">Scenario Evaluated</span>
              <h3 className="text-base font-bold text-slate-100">{result.question || 'What-If Simulation'}</h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-mono">Impact Severity:</span>
              <span className={`px-2.5 py-1 rounded font-mono font-bold text-xs border ${
                result.impact?.impact_severity === 'CRITICAL'
                  ? 'bg-rose-950 text-rose-300 border-rose-500/50'
                  : result.impact?.impact_severity === 'HIGH'
                  ? 'bg-amber-950 text-amber-300 border-amber-500/50'
                  : 'bg-emerald-950 text-emerald-300 border-emerald-500/50'
              }`}>
                {result.impact?.impact_severity || 'LOW'}
              </span>
            </div>
          </div>

          {/* Baseline vs Scenario Comparison Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Baseline Card */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4 shadow-lg">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="font-mono text-xs font-bold text-slate-300 uppercase">Pre-Scenario Baseline</span>
                <RiskBadge level={result.baseline?.risk_level} score={result.baseline?.risk_score} size="small" />
              </div>

              <div className="grid grid-cols-2 gap-3 font-mono text-xs">
                <div>
                  <p className="text-[10px] text-slate-500">TARGET SKU</p>
                  <p className="font-bold text-slate-200">{result.baseline?.sku}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500">STOCK POSITION</p>
                  <p className="font-bold text-slate-200">{result.baseline?.current_stock} units</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500">DAYS COVERAGE</p>
                  <p className="font-bold text-slate-200">
                    {result.baseline?.days_of_inventory !== null ? `${result.baseline?.days_of_inventory} Days` : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500">PROJECTED STOCKOUT</p>
                  <p className="font-bold text-slate-200">
                    {result.baseline?.projected_stockout ? 'YES' : 'NO'}
                  </p>
                </div>
              </div>
            </div>

            {/* Simulated Scenario Card */}
            <div className="bg-slate-900/80 border border-indigo-500/40 rounded-xl p-5 space-y-4 shadow-lg">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="font-mono text-xs font-bold text-indigo-300 uppercase flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" /> Post-Scenario Projection
                </span>
                <RiskBadge level={result.simulated?.risk_level} score={result.simulated?.risk_score} size="small" />
              </div>

              <div className="grid grid-cols-2 gap-3 font-mono text-xs">
                <div>
                  <p className="text-[10px] text-slate-500">TARGET SKU</p>
                  <p className="font-bold text-indigo-300">{result.simulated?.sku}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500">SIMULATED STOCK</p>
                  <p className="font-bold text-slate-100">{result.simulated?.current_stock} units</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500">DAYS COVERAGE DELTA</p>
                  <p className="font-bold text-amber-400">
                    {result.impact?.days_of_inventory_change !== null && result.impact?.days_of_inventory_change !== undefined
                      ? `${result.impact.days_of_inventory_change > 0 ? '+' : ''}${result.impact.days_of_inventory_change} Days`
                      : '0.0 Days'}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500">RISK SCORE SHIFT</p>
                  <p className={`font-bold ${
                    (result.impact?.risk_score_change || 0) > 0 ? 'text-rose-400' : 'text-emerald-400'
                  }`}>
                    {(result.impact?.risk_score_change || 0) > 0 ? '+' : ''}{result.impact?.risk_score_change || 0} pts
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Explanation & Advisory Recommendation Box */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3 shadow-lg">
              <h3 className="font-semibold text-slate-100 text-sm font-mono flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                Analytical Synthesis & Impact
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {result.explanation}
              </p>
            </div>

            <div className="bg-amber-950/30 border border-amber-500/40 rounded-xl p-5 space-y-3 shadow-lg flex flex-col justify-between">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-semibold text-amber-300 uppercase">Advisory Decision Support</span>
                  <span className="text-[10px] text-amber-400/80 bg-amber-900/40 px-2 py-0.5 rounded">Advisory Only</span>
                </div>
                <h4 className="text-base font-bold text-slate-100 font-mono">
                  RECOMMENDED: {result.recommendation?.recommended_action || 'MONITOR'}
                </h4>
                <p className="text-xs text-slate-300">
                  {result.recommendation?.justification || 'Based on deterministic counterfactual risk delta.'}
                </p>
              </div>

              <p className="text-[10px] text-slate-500 font-mono pt-2 border-t border-amber-500/20">
                Zero database mutations. Python memory simulation state reset.
              </p>
            </div>
          </div>
        </div>
      ) : (
        /* Empty State */
        <div className="py-16 text-center bg-slate-900/40 border border-slate-800 rounded-xl space-y-3">
          <SlidersHorizontal className="w-10 h-10 text-slate-600 mx-auto" />
          <h4 className="text-slate-300 font-semibold text-sm">No Simulation Scenario Run Yet</h4>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Select a scenario prompt above or adjust parameters to evaluate baseline vs counterfactual supply chain impacts.
          </p>
        </div>
      )}
    </div>
  );
}

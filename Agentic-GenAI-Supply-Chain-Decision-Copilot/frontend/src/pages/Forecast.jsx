import React, { useState, useEffect } from 'react';
import { TrendingUp, Calendar, Cpu, RefreshCw, BarChart2 } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { getDemandForecast } from '../api/forecast';
import AdvisoryNotice from '../components/common/AdvisoryNotice';
import LoadingSkeleton from '../components/common/LoadingSkeleton';
import ErrorMessage from '../components/common/ErrorMessage';

export default function Forecast() {
  const [selectedProductId, setSelectedProductId] = useState(1);
  const [horizonDays, setHorizonDays] = useState(14);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [forecastData, setForecastData] = useState(null);

  const fetchForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDemandForecast(selectedProductId, horizonDays);
      setForecastData(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast();
  }, [selectedProductId, horizonDays]);

  const dailyForecasts = forecastData?.forecast || [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
            Machine Learning Demand Forecasting
            <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded font-mono font-normal">
              Phase 3 XGBoost
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Multi-step recursive ML demand predictions with confidence bounds.
          </p>
        </div>
        <button
          onClick={fetchForecast}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition-all border border-slate-700 self-start md:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Regenerate Forecast</span>
        </button>
      </div>

      <AdvisoryNotice compact />

      {/* Control & Selector Panel */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row items-center justify-between gap-4 shadow-lg">
        {/* Product Selector */}
        <div className="flex items-center space-x-3 w-full md:w-auto font-mono text-xs">
          <label className="text-slate-400 font-semibold">Select Product:</label>
          <select
            value={selectedProductId}
            onChange={(e) => setSelectedProductId(Number(e.target.value))}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 font-mono text-xs"
          >
            <option value={1}>Product 1 — SKU-001 (High Velocity)</option>
            <option value={2}>Product 2 — SKU-002 (Medium Velocity)</option>
            <option value={3}>Product 3 — SKU-003 (Seasonal Component)</option>
            <option value={4}>Product 4 — SKU-004 (Intermittent Demand)</option>
            <option value={5}>Product 5 — SKU-005 (Slow Mover)</option>
          </select>
        </div>

        {/* Horizon Selector */}
        <div className="flex items-center space-x-3 w-full md:w-auto font-mono text-xs">
          <Calendar className="w-4 h-4 text-slate-400" />
          <span className="text-slate-400 font-semibold">Horizon:</span>
          <div className="flex items-center space-x-1">
            {[7, 14, 30, 60, 90].map((days) => (
              <button
                key={days}
                onClick={() => setHorizonDays(days)}
                className={`px-3 py-1.5 rounded text-xs transition-all font-semibold ${
                  horizonDays === days
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
                }`}
              >
                {days} Days
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton type="chart" />
      ) : error ? (
        <ErrorMessage error={error} onRetry={fetchForecast} title="Failed to Generate ML Demand Forecast" />
      ) : (
        <>
          {/* Metadata Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-1">
              <div className="flex items-center justify-between text-slate-400">
                <span>MODEL USED</span>
                <Cpu className="w-4 h-4 text-indigo-400" />
              </div>
              <p className="text-base font-bold text-slate-100">{forecastData?.model_used || 'XGBoostRegressor'}</p>
              <p className="text-[10px] text-slate-500">Version: {forecastData?.model_version || 'v1.0.0'}</p>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-1">
              <div className="flex items-center justify-between text-slate-400">
                <span>TARGET SKU</span>
                <BarChart2 className="w-4 h-4 text-emerald-400" />
              </div>
              <p className="text-base font-bold text-slate-100">{forecastData?.sku || 'SKU-001'}</p>
              <p className="text-[10px] text-slate-500">Horizon: {forecastData?.horizon_days} Days</p>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-1">
              <div className="flex items-center justify-between text-slate-400">
                <span>TOTAL PREDICTED DEMAND</span>
                <TrendingUp className="w-4 h-4 text-indigo-400" />
              </div>
              <p className="text-base font-bold text-indigo-400">
                {forecastData?.total_predicted_demand?.toFixed(1) || '0.0'} units
              </p>
              <p className="text-[10px] text-slate-500">Aggregated Over Horizon</p>
            </div>
          </div>

          {/* Recharts Forecast Visualization */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4 shadow-lg">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-slate-100 text-sm">Demand Forecast Curve</h3>
              <span className="text-[10px] font-mono text-slate-400">
                Predicted Demand & Bounds (95% CI)
              </span>
            </div>

            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={dailyForecasts} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc', fontSize: '12px' }}
                  />
                  <Legend verticalAlign="top" height={36} formatter={(value) => <span className="text-xs text-slate-300 font-mono">{value}</span>} />
                  <Line type="monotone" dataKey="predicted_demand" name="Predicted Demand" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="upper_bound" name="Upper Confidence Bound" stroke="#10b981" strokeWidth={1.5} strokeDasharray="3 3" dot={false} />
                  <Line type="monotone" dataKey="lower_bound" name="Lower Confidence Bound" stroke="#f43f5e" strokeWidth={1.5} strokeDasharray="3 3" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Daily Forecast Breakdown Table */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3 shadow-lg">
            <h3 className="font-semibold text-slate-100 text-sm">Daily Forecast Breakdown</h3>

            <div className="overflow-x-auto max-h-60">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider sticky top-0 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-4">Date</th>
                    <th className="py-2.5 px-4">Predicted Demand</th>
                    <th className="py-2.5 px-4">Lower Bound</th>
                    <th className="py-2.5 px-4">Upper Bound</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {dailyForecasts.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      <td className="py-2.5 px-4 font-bold text-slate-200">{row.date}</td>
                      <td className="py-2.5 px-4 font-bold text-indigo-300">{row.predicted_demand.toFixed(2)} units</td>
                      <td className="py-2.5 px-4 text-rose-400">{row.lower_bound.toFixed(2)} units</td>
                      <td className="py-2.5 px-4 text-emerald-400">{row.upper_bound.toFixed(2)} units</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

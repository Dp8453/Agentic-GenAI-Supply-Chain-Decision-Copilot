import React, { useState, useEffect } from 'react';
import { Users, ShieldCheck, Clock, Award, AlertTriangle, RefreshCw } from 'lucide-react';
import { getSuppliers } from '../api/suppliers';
import MetricCard from '../components/common/MetricCard';
import AdvisoryNotice from '../components/common/AdvisoryNotice';
import LoadingSkeleton from '../components/common/LoadingSkeleton';
import ErrorMessage from '../components/common/ErrorMessage';

export default function Suppliers() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [suppliers, setSuppliers] = useState([]);

  const fetchSuppliersData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSuppliers();
      setSuppliers(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuppliersData();
  }, []);

  const totalSuppliers = suppliers.length;
  const avgReliability = totalSuppliers > 0
    ? (suppliers.reduce((acc, s) => acc + (s.reliability_score || 0), 0) / totalSuppliers * 100).toFixed(1)
    : '0.0';
  
  const avgLeadTime = totalSuppliers > 0
    ? (suppliers.reduce((acc, s) => acc + (s.average_lead_time_days || 0), 0) / totalSuppliers).toFixed(1)
    : '0.0';

  const riskyCount = suppliers.filter(s => (s.reliability_score || 0) < 0.80).length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
            Supplier Intelligence & Performance Matrix
            <span className="text-xs bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded font-mono font-normal">
              PostgreSQL Managed
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Historical supplier lead-time reliability, on-time delivery rates, and risk scores.
          </p>
        </div>
        <button
          onClick={fetchSuppliersData}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition-all border border-slate-700 self-start md:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Matrix</span>
        </button>
      </div>

      <AdvisoryNotice compact />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Active Suppliers"
          value={totalSuppliers}
          subtitle="Contracted Vendors"
          icon={Users}
          badgeText="Active"
          badgeColor="indigo"
        />
        <MetricCard
          title="Avg Reliability Score"
          value={`${avgReliability}%`}
          subtitle="On-time delivery benchmark"
          icon={ShieldCheck}
          badgeText="Reliability"
          badgeColor="emerald"
        />
        <MetricCard
          title="Avg Contract Lead-Time"
          value={`${avgLeadTime} Days`}
          subtitle="Fulfillment cycle duration"
          icon={Clock}
          badgeText="Cycle"
          badgeColor="indigo"
        />
        <MetricCard
          title="High Lead-Time Risk"
          value={riskyCount}
          subtitle="Reliability < 80%"
          icon={AlertTriangle}
          badgeText={riskyCount > 0 ? "Watchlist" : "Optimal"}
          badgeColor={riskyCount > 0 ? "amber" : "emerald"}
        />
      </div>

      {loading ? (
        <LoadingSkeleton type="table" count={5} />
      ) : error ? (
        <ErrorMessage error={error} onRetry={fetchSuppliersData} title="Failed to Load Supplier Performance Matrix" />
      ) : (
        /* Main Supplier Table */
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Code</th>
                  <th className="py-3 px-4">Supplier Name</th>
                  <th className="py-3 px-4">Reliability Score</th>
                  <th className="py-3 px-4">Avg Lead Time</th>
                  <th className="py-3 px-4">On-Time Rate</th>
                  <th className="py-3 px-4">Quality Score</th>
                  <th className="py-3 px-4">Status Classification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {suppliers.map((s) => {
                  const rel = s.reliability_score ? (s.reliability_score * 100).toFixed(0) : '0';
                  const onTime = s.on_time_delivery_rate ? (s.on_time_delivery_rate * 100).toFixed(0) : '0';
                  const quality = s.quality_score ? (s.quality_score * 100).toFixed(0) : '0';
                  const isRisky = s.reliability_score < 0.80;

                  return (
                    <tr key={s.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-bold text-indigo-300">{s.code}</td>
                      <td className="py-3 px-4 font-sans font-medium text-slate-100">{s.name}</td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700">
                            <div
                              className={`h-full rounded-full ${
                                Number(rel) >= 90 ? 'bg-emerald-400' : Number(rel) >= 80 ? 'bg-yellow-400' : 'bg-rose-400'
                              }`}
                              style={{ width: `${rel}%` }}
                            />
                          </div>
                          <span className="font-bold">{rel}%</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-200">{s.average_lead_time_days} Days</td>
                      <td className="py-3 px-4 text-emerald-400">{onTime}%</td>
                      <td className="py-3 px-4 text-indigo-300">{quality}%</td>
                      <td className="py-3 px-4">
                        <span className={`text-[10px] font-semibold px-2.5 py-0.5 rounded-full border ${
                          isRisky
                            ? 'bg-amber-950/80 text-amber-300 border-amber-500/40'
                            : 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40'
                        }`}>
                          {isRisky ? 'LEAD-TIME VARIANCE' : 'PREFERENTIAL VENDOR'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

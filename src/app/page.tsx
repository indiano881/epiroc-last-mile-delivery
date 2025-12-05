"use client";

import { api } from "~/trpc/react";

function OtdGauge({ value, target }: { value: number; target: number }) {
  const isAboveTarget = value >= target;
  const percentage = Math.min(100, (value / 100) * 100);

  return (
    <div className="relative flex flex-col items-center">
      <div className="relative w-48 h-48">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="10"
          />
          {/* Progress circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={isAboveTarget ? "#22c55e" : value >= 90 ? "#eab308" : "#ef4444"}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${percentage * 2.83} 283`}
          />
          {/* Target marker */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="#000"
            strokeWidth="2"
            strokeDasharray="2 281"
            transform={`rotate(${target * 3.6 - 90} 50 50)`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-4xl font-bold ${isAboveTarget ? "text-green-600" : value >= 90 ? "text-yellow-600" : "text-red-600"}`}>
            {value.toFixed(1)}%
          </span>
          <span className="text-gray-500 text-sm">OTD Rate</span>
        </div>
      </div>
      <div className="mt-2 text-sm text-gray-600">
        Target: {target}%
      </div>
    </div>
  );
}

function StatCard({ title, value, subtitle, trend }: {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="text-sm font-medium text-gray-500">{title}</div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-3xl font-bold text-gray-900">{value}</span>
        {trend && (
          <span className={`text-sm ${trend === "up" ? "text-green-600" : trend === "down" ? "text-red-600" : "text-gray-500"}`}>
            {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"}
          </span>
        )}
      </div>
      {subtitle && <div className="mt-1 text-sm text-gray-500">{subtitle}</div>}
    </div>
  );
}

function CarrierTable({ carriers }: { carriers: Array<{
  pseudoId: string;
  totalShipments: number;
  otdRate: number;
  status: string;
}> }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Carrier Performance</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Carrier</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Shipments</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">OTD Rate</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {carriers.map((carrier) => (
              <tr key={carrier.pseudoId} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {carrier.pseudoId.slice(0, 8)}...
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {carrier.totalShipments.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {carrier.otdRate.toFixed(1)}%
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    carrier.status === "good" ? "bg-green-100 text-green-800" :
                    carrier.status === "warning" ? "bg-yellow-100 text-yellow-800" :
                    "bg-red-100 text-red-800"
                  }`}>
                    {carrier.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function LaneTable({ lanes }: { lanes: Array<{
  zip3Pair: string;
  totalShipments: number;
  otdRate: number;
  avgTransitDays: number | null;
  status: string;
}> }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Problem Lanes</h3>
        <p className="text-sm text-gray-500">Lowest OTD rates (min 10 shipments)</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Lane</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Volume</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Transit</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">OTD Rate</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {lanes.map((lane) => (
              <tr key={lane.zip3Pair} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {lane.zip3Pair}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {lane.totalShipments.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {lane.avgTransitDays?.toFixed(1) ?? "-"} days
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`font-medium ${
                    lane.otdRate >= 95 ? "text-green-600" :
                    lane.otdRate >= 90 ? "text-yellow-600" :
                    "text-red-600"
                  }`}>
                    {lane.otdRate.toFixed(1)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const otdSummary = api.shipment.getOtdSummary.useQuery({});
  const carriers = api.shipment.getCarrierPerformance.useQuery({ limit: 5 });
  const lanes = api.shipment.getLanePerformance.useQuery({ limit: 5 });

  const isLoading = otdSummary.isLoading || carriers.isLoading || lanes.isLoading;

  // Mock data for demo when database is empty
  const mockOtd = {
    total: 70234,
    onTime: 42140,
    early: 19866,
    late: 8228,
    otdRate: 88.3,
    target: 95,
    gap: 6.7,
  };

  const mockCarriers = [
    { pseudoId: "54874e5091dc", totalShipments: 8234, otdRate: 96.2, status: "good" },
    { pseudoId: "dbfc03065eae", totalShipments: 7891, otdRate: 94.1, status: "warning" },
    { pseudoId: "19936bf01cc6", totalShipments: 6543, otdRate: 91.8, status: "warning" },
    { pseudoId: "0e32a59c0c8e", totalShipments: 12456, otdRate: 87.3, status: "critical" },
    { pseudoId: "5797a633da7c", totalShipments: 4521, otdRate: 82.1, status: "critical" },
  ];

  const mockLanes = [
    { zip3Pair: "441xx→945xx", totalShipments: 156, otdRate: 72.4, avgTransitDays: 6.2, status: "critical" },
    { zip3Pair: "172xx→974xx", totalShipments: 234, otdRate: 75.6, avgTransitDays: 5.8, status: "critical" },
    { zip3Pair: "544xx→857xx", totalShipments: 189, otdRate: 78.3, avgTransitDays: 4.1, status: "critical" },
    { zip3Pair: "750xx→175xx", totalShipments: 312, otdRate: 81.2, avgTransitDays: 4.5, status: "critical" },
    { zip3Pair: "591xx→331xx", totalShipments: 98, otdRate: 83.7, avgTransitDays: 5.9, status: "critical" },
  ];

  const otd = otdSummary.data ?? mockOtd;
  const carrierData = carriers.data ?? mockCarriers;
  const laneData = lanes.data ?? mockLanes;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Delivery Performance Dashboard</h1>
        <p className="text-gray-500 mt-1">Monitor OTD rates and identify optimization opportunities</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          {/* KPI Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="md:col-span-1 flex justify-center">
              <OtdGauge value={otd.otdRate} target={otd.target} />
            </div>
            <div className="md:col-span-3 grid grid-cols-1 sm:grid-cols-3 gap-4">
              <StatCard
                title="Total Shipments"
                value={otd.total.toLocaleString()}
                subtitle="All time"
              />
              <StatCard
                title="On Time + Early"
                value={`${(otd.onTime + otd.early).toLocaleString()}`}
                subtitle={`${((otd.onTime + otd.early) / otd.total * 100).toFixed(1)}% of total`}
                trend="up"
              />
              <StatCard
                title="Late Deliveries"
                value={otd.late.toLocaleString()}
                subtitle={`${(otd.late / otd.total * 100).toFixed(1)}% of total`}
                trend="down"
              />
            </div>
          </div>

          {/* Gap to Target */}
          {otd.gap > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-8">
              <div className="flex items-center gap-3">
                <span className="text-2xl">⚠️</span>
                <div>
                  <p className="font-medium text-yellow-800">
                    {otd.gap.toFixed(1)}% gap to 95% OTD target
                  </p>
                  <p className="text-sm text-yellow-700">
                    Need to convert ~{Math.ceil(otd.total * otd.gap / 100).toLocaleString()} late deliveries to on-time
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <a
              href="/predict"
              className="flex items-center gap-4 p-6 bg-blue-600 hover:bg-blue-700 rounded-xl text-white transition-colors"
            >
              <span className="text-4xl">🔮</span>
              <div>
                <p className="text-lg font-semibold">Predict Delivery Time</p>
                <p className="text-blue-100">Get AI-powered ETA predictions</p>
              </div>
            </a>
            <a
              href="/analytics"
              className="flex items-center gap-4 p-6 bg-gray-800 hover:bg-gray-900 rounded-xl text-white transition-colors"
            >
              <span className="text-4xl">📊</span>
              <div>
                <p className="text-lg font-semibold">Deep Analytics</p>
                <p className="text-gray-300">Explore trends and root causes</p>
              </div>
            </a>
          </div>

          {/* Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CarrierTable carriers={carrierData} />
            <LaneTable lanes={laneData} />
          </div>
        </>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { api } from "~/trpc/react";

function TrendChart({ data }: { data: Array<{ period: string; otdRate: number; total: number }> }) {
  if (data.length === 0) return null;

  const maxRate = 100;
  const minRate = Math.min(...data.map(d => d.otdRate)) - 5;
  const range = maxRate - minRate;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">OTD Trend Over Time</h3>

      <div className="relative h-64">
        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 bottom-0 w-12 flex flex-col justify-between text-xs text-gray-500">
          <span>100%</span>
          <span>95%</span>
          <span>90%</span>
          <span>85%</span>
        </div>

        {/* Chart area */}
        <div className="ml-14 h-full relative">
          {/* Target line */}
          <div
            className="absolute w-full border-t-2 border-dashed border-green-400"
            style={{ top: `${((100 - 95) / range) * 100}%` }}
          />

          {/* Bars */}
          <div className="flex items-end h-full gap-1">
            {data.map((d, i) => {
              const height = ((d.otdRate - minRate) / range) * 100;
              const isAboveTarget = d.otdRate >= 95;

              return (
                <div
                  key={d.period}
                  className="flex-1 flex flex-col items-center"
                >
                  <div
                    className={`w-full rounded-t transition-all hover:opacity-80 ${
                      isAboveTarget ? "bg-green-500" : d.otdRate >= 90 ? "bg-yellow-500" : "bg-red-500"
                    }`}
                    style={{ height: `${height}%` }}
                    title={`${d.period}: ${d.otdRate.toFixed(1)}% (${d.total} shipments)`}
                  />
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* X-axis labels */}
      <div className="ml-14 flex justify-between mt-2 text-xs text-gray-500">
        {data.filter((_, i) => i % Math.ceil(data.length / 6) === 0).map((d) => (
          <span key={d.period}>{d.period}</span>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-500" />
          <span className="text-gray-600">Above Target (95%+)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-yellow-500" />
          <span className="text-gray-600">Warning (90-95%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-500" />
          <span className="text-gray-600">Critical (&lt;90%)</span>
        </div>
      </div>
    </div>
  );
}

function ModeBreakdown() {
  // Mock data for mode breakdown
  const modes = [
    { mode: "LTL", total: 45234, otdRate: 86.2, avgDelay: 0.8 },
    { mode: "Truckload", total: 18567, otdRate: 94.1, avgDelay: 0.2 },
    { mode: "TL Flatbed", total: 4123, otdRate: 91.5, avgDelay: 0.4 },
    { mode: "TL Dry", total: 2310, otdRate: 93.2, avgDelay: 0.3 },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance by Mode</h3>

      <div className="space-y-4">
        {modes.map((m) => (
          <div key={m.mode} className="flex items-center gap-4">
            <div className="w-24 font-medium text-gray-700">{m.mode}</div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-200 rounded-full h-4">
                  <div
                    className={`h-4 rounded-full ${
                      m.otdRate >= 95 ? "bg-green-500" :
                      m.otdRate >= 90 ? "bg-yellow-500" :
                      "bg-red-500"
                    }`}
                    style={{ width: `${m.otdRate}%` }}
                  />
                </div>
                <span className={`text-sm font-medium w-16 ${
                  m.otdRate >= 95 ? "text-green-600" :
                  m.otdRate >= 90 ? "text-yellow-600" :
                  "text-red-600"
                }`}>
                  {m.otdRate.toFixed(1)}%
                </span>
              </div>
            </div>
            <div className="text-sm text-gray-500 w-24 text-right">
              {m.total.toLocaleString()} shipments
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DistanceAnalysis() {
  // Mock data for distance buckets
  const buckets = [
    { bucket: "0-100 mi", otdRate: 94.2, avgDelay: 0.1 },
    { bucket: "100-250 mi", otdRate: 92.8, avgDelay: 0.2 },
    { bucket: "250-500 mi", otdRate: 90.5, avgDelay: 0.4 },
    { bucket: "500-1k mi", otdRate: 87.3, avgDelay: 0.7 },
    { bucket: "1k-2k mi", otdRate: 83.1, avgDelay: 1.2 },
    { bucket: "2k+ mi", otdRate: 76.4, avgDelay: 2.1 },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">OTD by Distance</h3>

      <div className="space-y-3">
        {buckets.map((b) => (
          <div key={b.bucket} className="flex items-center gap-4">
            <div className="w-20 text-sm text-gray-600">{b.bucket}</div>
            <div className="flex-1 flex items-center gap-2">
              <div className="flex-1 bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full ${
                    b.otdRate >= 95 ? "bg-green-500" :
                    b.otdRate >= 90 ? "bg-yellow-500" :
                    b.otdRate >= 85 ? "bg-orange-500" :
                    "bg-red-500"
                  }`}
                  style={{ width: `${b.otdRate}%` }}
                />
              </div>
              <span className="text-sm font-medium w-12">{b.otdRate.toFixed(0)}%</span>
            </div>
            <div className="text-sm text-gray-500 w-24">
              +{b.avgDelay.toFixed(1)} avg delay
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
        <p className="text-sm text-yellow-800">
          <strong>Insight:</strong> Long-haul shipments (1k+ miles) show significantly lower OTD rates.
          Consider adding buffer days for cross-country routes.
        </p>
      </div>
    </div>
  );
}

function DayOfWeekAnalysis() {
  const days = [
    { day: "Mon", otdRate: 88.5, volume: 12340 },
    { day: "Tue", otdRate: 89.2, volume: 13120 },
    { day: "Wed", otdRate: 90.1, volume: 12890 },
    { day: "Thu", otdRate: 88.8, volume: 12450 },
    { day: "Fri", otdRate: 85.3, volume: 11230 },
    { day: "Sat", otdRate: 91.2, volume: 4560 },
    { day: "Sun", otdRate: 92.5, volume: 3210 },
  ];

  const maxVolume = Math.max(...days.map(d => d.volume));

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Ship Day Analysis</h3>

      <div className="flex items-end justify-between h-40 gap-2">
        {days.map((d) => (
          <div key={d.day} className="flex-1 flex flex-col items-center">
            <div
              className={`w-full rounded-t ${
                d.otdRate >= 90 ? "bg-green-400" :
                d.otdRate >= 85 ? "bg-yellow-400" :
                "bg-red-400"
              }`}
              style={{ height: `${(d.volume / maxVolume) * 100}%` }}
            />
            <div className="text-xs font-medium mt-2">{d.day}</div>
            <div className="text-xs text-gray-500">{d.otdRate.toFixed(0)}%</div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-red-50 rounded-lg">
        <p className="text-sm text-red-800">
          <strong>Insight:</strong> Friday shipments have the lowest OTD rate (85.3%).
          Consider earlier ship dates for critical Friday deliveries.
        </p>
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState(12);

  const trendData = api.shipment.getOtdTrend.useQuery({
    groupBy: "month",
    months: timeRange,
  });

  // Mock trend data
  const mockTrend = [
    { period: "2024-01", otdRate: 87.2, total: 5234, onTime: 4567 },
    { period: "2024-02", otdRate: 88.5, total: 5123, onTime: 4534 },
    { period: "2024-03", otdRate: 86.1, total: 5678, onTime: 4889 },
    { period: "2024-04", otdRate: 89.2, total: 5432, onTime: 4845 },
    { period: "2024-05", otdRate: 90.1, total: 5890, onTime: 5308 },
    { period: "2024-06", otdRate: 88.7, total: 5234, onTime: 4642 },
    { period: "2024-07", otdRate: 87.9, total: 5567, onTime: 4894 },
    { period: "2024-08", otdRate: 89.5, total: 5432, onTime: 4862 },
    { period: "2024-09", otdRate: 91.2, total: 5678, onTime: 5178 },
    { period: "2024-10", otdRate: 88.3, total: 5890, onTime: 5201 },
    { period: "2024-11", otdRate: 85.6, total: 6234, onTime: 5336 },
    { period: "2024-12", otdRate: 82.1, total: 6789, onTime: 5573 },
  ];

  const trend = trendData.data ?? mockTrend;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-500 mt-1">Deep dive into delivery performance patterns</p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Time range:</span>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value={3}>3 months</option>
            <option value={6}>6 months</option>
            <option value={12}>12 months</option>
            <option value={24}>24 months</option>
          </select>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="mb-8">
        <TrendChart data={trend} />
      </div>

      {/* Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ModeBreakdown />
        <DistanceAnalysis />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DayOfWeekAnalysis />

        {/* Recommendations */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Optimization Recommendations</h3>

          <div className="space-y-4">
            <div className="flex gap-3 p-3 bg-blue-50 rounded-lg">
              <span className="text-xl">🎯</span>
              <div>
                <p className="font-medium text-blue-900">Focus on LTL improvement</p>
                <p className="text-sm text-blue-700">
                  LTL mode has the lowest OTD rate at 86.2%. Improving this by 5% would move overall OTD from 88.3% to 91.2%.
                </p>
              </div>
            </div>

            <div className="flex gap-3 p-3 bg-green-50 rounded-lg">
              <span className="text-xl">📍</span>
              <div>
                <p className="font-medium text-green-900">Address problem lanes</p>
                <p className="text-sm text-green-700">
                  5 lanes with 72-84% OTD account for 989 shipments. Targeted improvement here could convert ~200 late deliveries.
                </p>
              </div>
            </div>

            <div className="flex gap-3 p-3 bg-yellow-50 rounded-lg">
              <span className="text-xl">📅</span>
              <div>
                <p className="font-medium text-yellow-900">Adjust Friday expectations</p>
                <p className="text-sm text-yellow-700">
                  Add 1-day buffer for Friday shipments, especially for long-haul routes to improve customer satisfaction.
                </p>
              </div>
            </div>

            <div className="flex gap-3 p-3 bg-purple-50 rounded-lg">
              <span className="text-xl">🚚</span>
              <div>
                <p className="font-medium text-purple-900">Carrier review</p>
                <p className="text-sm text-purple-700">
                  Carrier 5797a633da7c has 82.1% OTD with 4,521 shipments. Consider renegotiating SLA or redistributing volume.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

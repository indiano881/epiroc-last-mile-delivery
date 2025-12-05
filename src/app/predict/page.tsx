"use client";

import { useState } from "react";
import { api } from "~/trpc/react";

type PredictionResult = {
  predictedDelay: number;
  predictedClass: string;
  riskLevel: string;
  confidence: number;
  factors: Array<{ name: string; impact: string }>;
  expectedTransitDays: number;
  predictedTransitDays: number;
  classProbabilities: Record<string, number>;
};

function DelayDisplay({ delay, confidence }: { delay: number; confidence: number }) {
  const isEarly = delay < 0;
  const isOnTime = delay === 0;
  const isLate = delay > 0;

  return (
    <div className="text-center py-8">
      <div className={`text-8xl font-bold ${
        isEarly ? "text-green-500" : isOnTime ? "text-blue-500" : "text-red-500"
      }`}>
        {delay > 0 ? "+" : ""}{delay.toFixed(1)}
      </div>
      <div className="text-2xl text-gray-600 mt-2">
        {delay === 1 || delay === -1 ? "day" : "days"}
      </div>
      <div className={`mt-4 text-lg font-medium ${
        isEarly ? "text-green-600" : isOnTime ? "text-blue-600" : "text-red-600"
      }`}>
        {isEarly && "Likely Early Delivery"}
        {isOnTime && "On Time"}
        {isLate && "Risk of Delay"}
      </div>
      <div className="mt-2 text-sm text-gray-500">
        Confidence: {confidence.toFixed(0)}%
      </div>
    </div>
  );
}

function FactorsList({ factors }: { factors: Array<{ name: string; impact: string }> }) {
  const positive = factors.filter(f => f.impact === "positive");
  const negative = factors.filter(f => f.impact === "negative");

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
      {negative.length > 0 && (
        <div className="bg-red-50 rounded-lg p-4">
          <h4 className="font-medium text-red-800 mb-2">Risk Factors</h4>
          <ul className="space-y-1">
            {negative.map((f, i) => (
              <li key={i} className="flex items-center gap-2 text-red-700 text-sm">
                <span>⚠️</span> {f.name}
              </li>
            ))}
          </ul>
        </div>
      )}
      {positive.length > 0 && (
        <div className="bg-green-50 rounded-lg p-4">
          <h4 className="font-medium text-green-800 mb-2">Positive Factors</h4>
          <ul className="space-y-1">
            {positive.map((f, i) => (
              <li key={i} className="flex items-center gap-2 text-green-700 text-sm">
                <span>✓</span> {f.name}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function PredictPage() {
  const [formData, setFormData] = useState({
    originZip: "",
    destZip: "",
    shipDate: new Date().toISOString().split("T")[0],
    carrierMode: "LTL" as "LTL" | "Truckload" | "TL Flatbed" | "TL Dry",
    customerDistance: 500,
    goalTransitDays: 3,
    isHolidayWeek: false,
    weatherSeverity: 0,
  });

  const [result, setResult] = useState<PredictionResult | null>(null);

  const predictMutation = api.shipment.predict.useMutation({
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    predictMutation.mutate({
      ...formData,
      shipDate: formData.shipDate ?? new Date().toISOString().split("T")[0]!,
    });
  };

  const distanceBuckets = [
    { label: "Local (0-100 mi)", value: 50, transit: 1 },
    { label: "Regional (100-250 mi)", value: 175, transit: 1 },
    { label: "Short Haul (250-500 mi)", value: 375, transit: 2 },
    { label: "Medium Haul (500-1k mi)", value: 750, transit: 3 },
    { label: "Long Haul (1k-2k mi)", value: 1500, transit: 4 },
    { label: "Cross Country (2k+ mi)", value: 2500, transit: 6 },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">ETA Predictor</h1>
        <p className="text-gray-500 mt-1">Get AI-powered delivery time predictions</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Form */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">Shipment Details</h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* ZIP Codes */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Origin ZIP
                </label>
                <input
                  type="text"
                  value={formData.originZip}
                  onChange={(e) => setFormData({ ...formData, originZip: e.target.value })}
                  placeholder="e.g., 441"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Destination ZIP
                </label>
                <input
                  type="text"
                  value={formData.destZip}
                  onChange={(e) => setFormData({ ...formData, destZip: e.target.value })}
                  placeholder="e.g., 750"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
            </div>

            {/* Ship Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ship Date
              </label>
              <input
                type="date"
                value={formData.shipDate}
                onChange={(e) => setFormData({ ...formData, shipDate: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            {/* Carrier Mode */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Carrier Mode
              </label>
              <select
                value={formData.carrierMode}
                onChange={(e) => setFormData({ ...formData, carrierMode: e.target.value as typeof formData.carrierMode })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="LTL">LTL (Less-Than-Truckload)</option>
                <option value="Truckload">Truckload</option>
                <option value="TL Flatbed">TL Flatbed</option>
                <option value="TL Dry">TL Dry</option>
              </select>
            </div>

            {/* Distance Preset */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Distance
              </label>
              <select
                value={formData.customerDistance}
                onChange={(e) => {
                  const bucket = distanceBuckets.find(b => b.value === Number(e.target.value));
                  setFormData({
                    ...formData,
                    customerDistance: Number(e.target.value),
                    goalTransitDays: bucket?.transit ?? formData.goalTransitDays,
                  });
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {distanceBuckets.map((bucket) => (
                  <option key={bucket.value} value={bucket.value}>
                    {bucket.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Expected Transit */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expected Transit Days
              </label>
              <input
                type="number"
                value={formData.goalTransitDays}
                onChange={(e) => setFormData({ ...formData, goalTransitDays: Number(e.target.value) })}
                min={1}
                max={14}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Conditions */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700">
                Conditions
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.isHolidayWeek}
                  onChange={(e) => setFormData({ ...formData, isHolidayWeek: e.target.checked })}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-600">Holiday week</span>
              </label>

              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Weather severity: {formData.weatherSeverity}
                </label>
                <input
                  type="range"
                  min={0}
                  max={10}
                  value={formData.weatherSeverity}
                  onChange={(e) => setFormData({ ...formData, weatherSeverity: Number(e.target.value) })}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Clear</span>
                  <span>Severe</span>
                </div>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={predictMutation.isPending}
              className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50"
            >
              {predictMutation.isPending ? "Predicting..." : "Predict Delivery Time"}
            </button>
          </form>
        </div>

        {/* Result */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Prediction Result</h2>

          {!result && !predictMutation.isPending && (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <span className="text-6xl mb-4">🔮</span>
              <p>Enter shipment details and click predict</p>
            </div>
          )}

          {predictMutation.isPending && (
            <div className="flex flex-col items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
              <p className="text-gray-500">Analyzing...</p>
            </div>
          )}

          {result && (
            <>
              <DelayDisplay
                delay={result.predictedDelay}
                confidence={result.confidence}
              />

              {/* Transit Summary */}
              <div className="bg-gray-50 rounded-lg p-4 mt-4">
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-sm text-gray-500">Expected</div>
                    <div className="text-xl font-bold text-gray-900">
                      {result.expectedTransitDays} days
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Predicted</div>
                    <div className={`text-xl font-bold ${
                      result.predictedDelay <= 0 ? "text-green-600" : "text-red-600"
                    }`}>
                      {result.predictedTransitDays.toFixed(1)} days
                    </div>
                  </div>
                </div>
              </div>

              {/* Risk Level Badge */}
              <div className="flex justify-center mt-4">
                <span className={`px-4 py-2 rounded-full text-sm font-medium ${
                  result.riskLevel === "low" ? "bg-green-100 text-green-800" :
                  result.riskLevel === "medium" ? "bg-yellow-100 text-yellow-800" :
                  "bg-red-100 text-red-800"
                }`}>
                  {result.riskLevel.toUpperCase()} RISK
                </span>
              </div>

              {/* Factors */}
              <FactorsList factors={result.factors} />

              {/* Probabilities */}
              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Outcome Probabilities</h4>
                <div className="space-y-2">
                  {Object.entries(result.classProbabilities).map(([cls, prob]) => (
                    <div key={cls} className="flex items-center gap-2">
                      <span className="text-sm text-gray-600 w-28">{cls}</span>
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            cls === "Late" ? "bg-red-500" :
                            cls === "On Time" ? "bg-blue-500" :
                            "bg-green-500"
                          }`}
                          style={{ width: `${prob}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-500 w-12 text-right">{prob.toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

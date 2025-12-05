import { z } from "zod";
import { createTRPCRouter, publicProcedure } from "~/server/api/trpc";

// ML API base URL (FastAPI server)
const ML_API_URL = process.env.ML_API_URL ?? "http://localhost:8000";

// ═══════════════════════════════════════════════════════════════
// INPUT SCHEMAS
// ═══════════════════════════════════════════════════════════════

const predictionInputSchema = z.object({
  originZip: z.string().min(3).max(5),
  destZip: z.string().min(3).max(5),
  shipDate: z.string(), // ISO date string
  carrierMode: z.enum(["LTL", "Truckload", "TL Flatbed", "TL Dry"]),
  customerDistance: z.number().positive(),
  goalTransitDays: z.number().int().positive(),
  carrierId: z.string().optional(),
  isHolidayWeek: z.boolean().optional(),
  weatherSeverity: z.number().min(0).max(10).optional(),
});

const shipmentFilterSchema = z.object({
  carrierMode: z.string().optional(),
  otdDesignation: z.string().optional(),
  dateFrom: z.string().optional(),
  dateTo: z.string().optional(),
  carrierId: z.string().optional(),
  laneId: z.string().optional(),
  limit: z.number().int().min(1).max(100).default(50),
  offset: z.number().int().min(0).default(0),
});

// ═══════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════

function getDistanceBucket(distance: number): string {
  if (distance < 100) return "0-100";
  if (distance < 250) return "100-250";
  if (distance < 500) return "250-500";
  if (distance < 1000) return "500-1k";
  if (distance < 2000) return "1k-2k";
  return "2k+";
}

function getDayOfWeek(dateStr: string): number {
  const date = new Date(dateStr);
  // Convert Sunday=0 to Monday=0 format
  const day = date.getDay();
  return day === 0 ? 6 : day - 1;
}

function getWeekOfYear(dateStr: string): number {
  const date = new Date(dateStr);
  const start = new Date(date.getFullYear(), 0, 1);
  const diff = date.getTime() - start.getTime();
  const oneWeek = 1000 * 60 * 60 * 24 * 7;
  return Math.ceil(diff / oneWeek);
}

// ═══════════════════════════════════════════════════════════════
// ROUTER
// ═══════════════════════════════════════════════════════════════

export const shipmentRouter = createTRPCRouter({
  // ─────────────────────────────────────────────────────────────
  // PREDICTION
  // ─────────────────────────────────────────────────────────────
  predict: publicProcedure
    .input(predictionInputSchema)
    .mutation(async ({ input }) => {
      const shipDate = new Date(input.shipDate);

      // Prepare request for ML API
      const mlRequest = {
        customer_distance: input.customerDistance,
        all_modes_goal_transit_days: input.goalTransitDays,
        ship_dow: getDayOfWeek(input.shipDate),
        ship_week: getWeekOfYear(input.shipDate),
        ship_month: shipDate.getMonth() + 1,
        days_to_holiday: 15, // TODO: Calculate from actual holidays
        origin_weather_severity: input.weatherSeverity ?? 0,
        freight_index: 1.0,
        fuel_price: 70,
        consumer_sentiment: 65,
        congestion_score: input.isHolidayWeek ? 5 : 2,
        carrier_otd_rate: 94, // TODO: Get from database
        lane_otd_rate: 92, // TODO: Get from database
        lane_avg_transit_days: input.goalTransitDays,
        carrier_mode: input.carrierMode,
        distance_bucket: getDistanceBucket(input.customerDistance),
        is_ship_holiday: false,
        is_holiday_week: input.isHolidayWeek ?? false,
        is_rush_hour: false,
        is_weekend: [5, 6].includes(getDayOfWeek(input.shipDate)),
        is_month_end: shipDate.getDate() > 27,
        is_quarter_end: [3, 6, 9, 12].includes(shipDate.getMonth() + 1) && shipDate.getDate() > 27,
      };

      try {
        const response = await fetch(`${ML_API_URL}/predict`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(mlRequest),
        });

        if (!response.ok) {
          throw new Error(`ML API error: ${response.status}`);
        }

        const prediction = await response.json() as {
          predicted_delay: number;
          predicted_class: string;
          risk_level: string;
          confidence: number;
          factors: Array<{ name: string; impact: string }>;
          expected_transit_days: number;
          predicted_transit_days: number;
          class_probabilities: Record<string, number>;
        };

        return {
          predictedDelay: prediction.predicted_delay,
          predictedClass: prediction.predicted_class,
          riskLevel: prediction.risk_level,
          confidence: prediction.confidence,
          factors: prediction.factors,
          expectedTransitDays: prediction.expected_transit_days,
          predictedTransitDays: prediction.predicted_transit_days,
          classProbabilities: prediction.class_probabilities,
        };
      } catch (error) {
        // Fallback prediction if ML API is not available
        console.error("ML API error, using fallback:", error);

        const basePrediction = input.goalTransitDays;
        const delay = input.isHolidayWeek ? 1 : 0;

        return {
          predictedDelay: delay,
          predictedClass: delay > 0 ? "Late" : "On Time",
          riskLevel: delay > 0 ? "medium" : "low",
          confidence: 70,
          factors: input.isHolidayWeek
            ? [{ name: "Holiday Week", impact: "negative" }]
            : [{ name: "Normal Conditions", impact: "positive" }],
          expectedTransitDays: basePrediction,
          predictedTransitDays: basePrediction + delay,
          classProbabilities: {
            "Delivered Early": 25,
            "On Time": 50,
            "Late": 25,
          },
        };
      }
    }),

  // ─────────────────────────────────────────────────────────────
  // SHIPMENT LISTING
  // ─────────────────────────────────────────────────────────────
  list: publicProcedure
    .input(shipmentFilterSchema)
    .query(async ({ ctx, input }) => {
      const where: Record<string, unknown> = {};

      if (input.carrierMode) {
        where.carrierMode = input.carrierMode;
      }
      if (input.otdDesignation) {
        where.otdDesignation = input.otdDesignation;
      }
      if (input.carrierId) {
        where.carrierId = input.carrierId;
      }
      if (input.laneId) {
        where.laneId = input.laneId;
      }
      if (input.dateFrom || input.dateTo) {
        where.actualShip = {};
        if (input.dateFrom) {
          (where.actualShip as Record<string, Date>).gte = new Date(input.dateFrom);
        }
        if (input.dateTo) {
          (where.actualShip as Record<string, Date>).lte = new Date(input.dateTo);
        }
      }

      const [shipments, total] = await Promise.all([
        ctx.db.shipment.findMany({
          where,
          take: input.limit,
          skip: input.offset,
          orderBy: { actualShip: "desc" },
          include: {
            carrier: true,
            lane: true,
          },
        }),
        ctx.db.shipment.count({ where }),
      ]);

      return {
        shipments,
        total,
        hasMore: input.offset + shipments.length < total,
      };
    }),

  // ─────────────────────────────────────────────────────────────
  // SINGLE SHIPMENT
  // ─────────────────────────────────────────────────────────────
  getById: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ ctx, input }) => {
      const shipment = await ctx.db.shipment.findUnique({
        where: { id: input.id },
        include: {
          carrier: true,
          lane: true,
        },
      });

      if (!shipment) {
        throw new Error("Shipment not found");
      }

      return shipment;
    }),

  // ─────────────────────────────────────────────────────────────
  // ANALYTICS: OTD SUMMARY
  // ─────────────────────────────────────────────────────────────
  getOtdSummary: publicProcedure
    .input(z.object({
      dateFrom: z.string().optional(),
      dateTo: z.string().optional(),
    }))
    .query(async ({ ctx, input }) => {
      const where: Record<string, unknown> = {};

      if (input.dateFrom || input.dateTo) {
        where.actualShip = {};
        if (input.dateFrom) {
          (where.actualShip as Record<string, Date>).gte = new Date(input.dateFrom);
        }
        if (input.dateTo) {
          (where.actualShip as Record<string, Date>).lte = new Date(input.dateTo);
        }
      }

      const [total, onTime, early, late] = await Promise.all([
        ctx.db.shipment.count({ where }),
        ctx.db.shipment.count({ where: { ...where, otdDesignation: "On Time" } }),
        ctx.db.shipment.count({ where: { ...where, otdDesignation: "Delivered Early" } }),
        ctx.db.shipment.count({ where: { ...where, otdDesignation: "Late" } }),
      ]);

      const otdRate = total > 0 ? ((onTime + early) / total) * 100 : 0;

      return {
        total,
        onTime,
        early,
        late,
        otdRate: Math.round(otdRate * 10) / 10,
        target: 95, // SLA target
        gap: Math.round((95 - otdRate) * 10) / 10,
      };
    }),

  // ─────────────────────────────────────────────────────────────
  // ANALYTICS: OTD BY CARRIER
  // ─────────────────────────────────────────────────────────────
  getCarrierPerformance: publicProcedure
    .input(z.object({ limit: z.number().int().min(1).max(20).default(10) }))
    .query(async ({ ctx, input }) => {
      const carriers = await ctx.db.carrier.findMany({
        take: input.limit,
        orderBy: { totalShipments: "desc" },
        select: {
          id: true,
          pseudoId: true,
          totalShipments: true,
          onTimeCount: true,
          lateCount: true,
          earlyCount: true,
          historicalOtd: true,
          avgDelayDays: true,
        },
      });

      return carriers.map((c) => ({
        ...c,
        otdRate: c.historicalOtd ?? 0,
        status: (c.historicalOtd ?? 0) >= 95 ? "good" : (c.historicalOtd ?? 0) >= 90 ? "warning" : "critical",
      }));
    }),

  // ─────────────────────────────────────────────────────────────
  // ANALYTICS: OTD BY LANE
  // ─────────────────────────────────────────────────────────────
  getLanePerformance: publicProcedure
    .input(z.object({ limit: z.number().int().min(1).max(20).default(10) }))
    .query(async ({ ctx, input }) => {
      // Get worst performing lanes
      const lanes = await ctx.db.lane.findMany({
        take: input.limit,
        where: { totalShipments: { gte: 10 } }, // Minimum volume
        orderBy: { historicalOtd: "asc" },
        select: {
          id: true,
          zip3Pair: true,
          originZip: true,
          destZip: true,
          totalShipments: true,
          onTimeCount: true,
          lateCount: true,
          earlyCount: true,
          historicalOtd: true,
          avgTransitDays: true,
          avgDelayDays: true,
        },
      });

      return lanes.map((l) => ({
        ...l,
        otdRate: l.historicalOtd ?? 0,
        status: (l.historicalOtd ?? 0) >= 95 ? "good" : (l.historicalOtd ?? 0) >= 90 ? "warning" : "critical",
      }));
    }),

  // ─────────────────────────────────────────────────────────────
  // ANALYTICS: OTD TREND
  // ─────────────────────────────────────────────────────────────
  getOtdTrend: publicProcedure
    .input(z.object({
      groupBy: z.enum(["day", "week", "month"]).default("month"),
      months: z.number().int().min(1).max(24).default(12),
    }))
    .query(async ({ ctx, input }) => {
      // Get date range
      const endDate = new Date();
      const startDate = new Date();
      startDate.setMonth(startDate.getMonth() - input.months);

      const shipments = await ctx.db.shipment.findMany({
        where: {
          actualShip: {
            gte: startDate,
            lte: endDate,
          },
        },
        select: {
          actualShip: true,
          otdDesignation: true,
          shipYear: true,
          shipMonth: true,
          shipWeek: true,
        },
      });

      // Group by period
      const grouped = new Map<string, { total: number; onTime: number }>();

      for (const s of shipments) {
        let key: string;
        if (input.groupBy === "month") {
          key = `${s.shipYear}-${String(s.shipMonth).padStart(2, "0")}`;
        } else if (input.groupBy === "week") {
          key = `${s.shipYear}-W${String(s.shipWeek).padStart(2, "0")}`;
        } else {
          key = s.actualShip.toISOString().split("T")[0]!;
        }

        const current = grouped.get(key) ?? { total: 0, onTime: 0 };
        current.total++;
        if (s.otdDesignation !== "Late") {
          current.onTime++;
        }
        grouped.set(key, current);
      }

      // Convert to array and calculate OTD rate
      const trend = Array.from(grouped.entries())
        .map(([period, data]) => ({
          period,
          total: data.total,
          onTime: data.onTime,
          otdRate: Math.round((data.onTime / data.total) * 1000) / 10,
        }))
        .sort((a, b) => a.period.localeCompare(b.period));

      return trend;
    }),

  // ─────────────────────────────────────────────────────────────
  // REFERENCE DATA
  // ─────────────────────────────────────────────────────────────
  getCarriers: publicProcedure.query(async ({ ctx }) => {
    return ctx.db.carrier.findMany({
      select: {
        id: true,
        pseudoId: true,
        historicalOtd: true,
      },
      orderBy: { totalShipments: "desc" },
      take: 50,
    });
  }),

  getLanes: publicProcedure
    .input(z.object({ search: z.string().optional() }))
    .query(async ({ ctx, input }) => {
      const where = input.search
        ? { zip3Pair: { contains: input.search } }
        : {};

      return ctx.db.lane.findMany({
        where,
        select: {
          id: true,
          zip3Pair: true,
          originZip: true,
          destZip: true,
          historicalOtd: true,
          avgTransitDays: true,
        },
        orderBy: { totalShipments: "desc" },
        take: 50,
      });
    }),
});

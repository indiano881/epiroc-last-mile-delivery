#!/usr/bin/env python3
"""
Import enriched shipments CSV into SQLite database via Prisma.
"""

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import uuid

def sanitize_string(val):
    """Remove non-ASCII characters from strings to avoid SQLite/Prisma issues."""
    if val is None or pd.isna(val):
        return None
    s = str(val)
    # Replace common unicode arrows and encode to ASCII, ignoring errors
    s = s.replace('→', '->').replace('\u2192', '->')
    return s.encode('ascii', 'ignore').decode('ascii')

# Paths
CSV_PATH = Path(__file__).parent / "enriched_shipments.csv"
DB_PATH = Path(__file__).parent.parent / "prisma" / "db.sqlite"

def main():
    print("=" * 60)
    print("IMPORTING ENRICHED DATA TO DATABASE")
    print("=" * 60)

    # Load CSV
    print(f"\nLoading data from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df):,} shipments")

    # Connect to SQLite
    print(f"\nConnecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing data (in correct order due to foreign keys)
    print("Clearing existing data...")
    cursor.execute("DELETE FROM Shipment")
    cursor.execute("DELETE FROM Lane")
    cursor.execute("DELETE FROM Carrier")
    conn.commit()

    now = datetime.now().isoformat()

    # Create carriers first
    print("\nCreating carriers...")
    carriers = df['carrier_pseudo'].dropna().unique()
    carrier_insert = """
    INSERT INTO Carrier (id, pseudoId, name, totalShipments, onTimeCount, lateCount, earlyCount, historicalOtd, avgDelayDays, createdAt, updatedAt)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for carrier_id in carriers:
        carrier_df = df[df['carrier_pseudo'] == carrier_id]
        total = len(carrier_df)

        # Calculate OTD counts
        on_time = len(carrier_df[carrier_df['otd_designation'].isin(['On Time', 'Delivered On Time'])])
        late = len(carrier_df[carrier_df['otd_designation'].isin(['Late', 'Delivered Late'])])
        early = len(carrier_df[carrier_df['otd_designation'].isin(['Early', 'Delivered Early'])])

        otd_rate = carrier_df['carrier_otd_rate'].iloc[0] if 'carrier_otd_rate' in carrier_df.columns and pd.notna(carrier_df['carrier_otd_rate'].iloc[0]) else 0.85
        avg_delay = carrier_df['delay_days'].mean() if 'delay_days' in carrier_df.columns else 0.0

        cursor.execute(carrier_insert, (
            str(uuid.uuid4()),  # id
            sanitize_string(carrier_id)[:50],  # pseudoId
            sanitize_string(f"Carrier {str(carrier_id)[:8]}"),  # name
            total,  # totalShipments
            on_time,  # onTimeCount
            late,  # lateCount
            early,  # earlyCount
            otd_rate if pd.notna(otd_rate) else 0.85,  # historicalOtd
            avg_delay if pd.notna(avg_delay) else 0.0,  # avgDelayDays
            now,  # createdAt
            now   # updatedAt
        ))
    conn.commit()
    print(f"  Created {len(carriers)} carriers")

    # Build carrier ID mapping (pseudoId -> actual id)
    cursor.execute("SELECT id, pseudoId FROM Carrier")
    carrier_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Create lanes
    print("\nCreating lanes...")
    lanes = df['lane_id'].dropna().unique()
    lane_insert = """
    INSERT INTO Lane (id, zip3Pair, originZip, destZip, totalShipments, onTimeCount, lateCount, earlyCount, historicalOtd, avgTransitDays, avgDelayDays, createdAt, updatedAt)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for lane_id in lanes:
        lane_df = df[df['lane_id'] == lane_id]
        # Parse lane_id which is like "441-750"
        parts = str(lane_id).split('-')
        origin = parts[0] if len(parts) > 0 else '000'
        dest = parts[1] if len(parts) > 1 else '000'
        total = len(lane_df)

        # Calculate OTD counts
        on_time = len(lane_df[lane_df['otd_designation'].isin(['On Time', 'Delivered On Time'])])
        late = len(lane_df[lane_df['otd_designation'].isin(['Late', 'Delivered Late'])])
        early = len(lane_df[lane_df['otd_designation'].isin(['Early', 'Delivered Early'])])

        otd_rate = lane_df['lane_otd_rate'].iloc[0] if 'lane_otd_rate' in lane_df.columns and pd.notna(lane_df['lane_otd_rate'].iloc[0]) else 0.85
        avg_transit = lane_df['lane_avg_transit_days'].iloc[0] if 'lane_avg_transit_days' in lane_df.columns and pd.notna(lane_df['lane_avg_transit_days'].iloc[0]) else 3.0
        avg_delay = lane_df['delay_days'].mean() if 'delay_days' in lane_df.columns else 0.0

        cursor.execute(lane_insert, (
            str(uuid.uuid4()),  # id
            sanitize_string(lane_id)[:20],  # zip3Pair
            sanitize_string(origin)[:10],  # originZip
            sanitize_string(dest)[:10],  # destZip
            total,  # totalShipments
            on_time,  # onTimeCount
            late,  # lateCount
            early,  # earlyCount
            otd_rate if pd.notna(otd_rate) else 0.85,  # historicalOtd
            avg_transit if pd.notna(avg_transit) else 3.0,  # avgTransitDays
            avg_delay if pd.notna(avg_delay) else 0.0,  # avgDelayDays
            now,  # createdAt
            now   # updatedAt
        ))
    conn.commit()
    print(f"  Created {len(lanes)} lanes")

    # Build lane ID mapping (zip3Pair -> actual id)
    cursor.execute("SELECT id, zip3Pair FROM Lane")
    lane_map = {row[1]: row[0] for row in cursor.fetchall()}

    # Insert shipments
    print("\nInserting shipments...")

    insert_sql = """
    INSERT INTO Shipment (
        id, loadId, carrierMode, actualShip, actualDelivery,
        carrierServiceDays, truckloadServiceDays, customerDistance, goalTransitDays,
        actualTransitDays, otdDesignation, originZip, destZip, laneZip3Pair,
        distanceBucket, shipDow, shipWeek, shipMonth, shipYear,
        isShipHoliday, isDeliveryHoliday, daysToHoliday, holidayName, isHolidayWeek,
        congestionScore, isRushHour, isMonthEnd, isQuarterEnd,
        carrierId, laneId, createdAt, updatedAt
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    inserted = 0
    for idx, row in df.iterrows():
        try:
            # Parse dates
            ship_date = pd.to_datetime(row.get('actual_ship', '2024-01-01'))
            delivery_date = pd.to_datetime(row.get('actual_delivery')) if pd.notna(row.get('actual_delivery')) else None

            # Get OTD designation from data
            otd_designation = sanitize_string(row.get('otd_designation', 'Unknown'))

            # Get carrier and lane IDs
            carrier_pseudo = sanitize_string(row.get('carrier_pseudo', ''))[:50]
            lane_zip3 = sanitize_string(row.get('lane_id', ''))[:20]

            carrier_id = carrier_map.get(carrier_pseudo, list(carrier_map.values())[0] if carrier_map else None)
            lane_id = lane_map.get(lane_zip3, list(lane_map.values())[0] if lane_map else None)

            if not carrier_id or not lane_id:
                continue

            cursor.execute(insert_sql, (
                str(uuid.uuid4()),  # id
                sanitize_string(row.get('load_id_pseudo', f'LOAD-{idx}'))[:50],  # loadId
                sanitize_string(row.get('carrier_mode', 'LTL')),  # carrierMode
                ship_date.isoformat(),  # actualShip
                delivery_date.isoformat() if delivery_date else None,  # actualDelivery
                float(row['carrier_posted_service_days']) if pd.notna(row.get('carrier_posted_service_days')) else None,  # carrierServiceDays
                float(row['truckload_service_days']) if pd.notna(row.get('truckload_service_days')) else None,  # truckloadServiceDays
                float(row['customer_distance']) if pd.notna(row.get('customer_distance')) else 0.0,  # customerDistance
                int(row['all_modes_goal_transit_days']) if pd.notna(row.get('all_modes_goal_transit_days')) else 3,  # goalTransitDays
                int(row['actual_transit_days']) if pd.notna(row.get('actual_transit_days')) else None,  # actualTransitDays
                otd_designation,  # otdDesignation
                sanitize_string(row.get('origin_zip_3d', '000'))[:10],  # originZip
                sanitize_string(row.get('dest_zip_3d', '000'))[:10],  # destZip
                sanitize_string(row.get('lane_zip3_pair', '000-000'))[:20],  # laneZip3Pair
                sanitize_string(row.get('distance_bucket', '0-100'))[:20],  # distanceBucket
                int(row['ship_dow']) if pd.notna(row.get('ship_dow')) else ship_date.weekday(),  # shipDow
                int(row['ship_week']) if pd.notna(row.get('ship_week')) else ship_date.isocalendar()[1],  # shipWeek
                int(row['ship_month']) if pd.notna(row.get('ship_month')) else ship_date.month,  # shipMonth
                int(row['ship_year']) if pd.notna(row.get('ship_year')) else ship_date.year,  # shipYear
                bool(row.get('is_ship_holiday', False)),  # isShipHoliday
                bool(row.get('is_delivery_holiday', False)),  # isDeliveryHoliday
                int(row['days_to_holiday']) if pd.notna(row.get('days_to_holiday')) else None,  # daysToHoliday
                sanitize_string(row.get('holiday_name', ''))[:100] if pd.notna(row.get('holiday_name')) else None,  # holidayName
                bool(row.get('is_holiday_week', False)),  # isHolidayWeek
                float(row['congestion_score']) if pd.notna(row.get('congestion_score')) else None,  # congestionScore
                bool(row.get('is_rush_hour', False)),  # isRushHour
                bool(row.get('is_month_end', False)),  # isMonthEnd
                bool(row.get('is_quarter_end', False)),  # isQuarterEnd
                carrier_id,  # carrierId
                lane_id,  # laneId
                now,  # createdAt
                now   # updatedAt
            ))
            inserted += 1

            if inserted % 100 == 0:
                conn.commit()
                print(f"  Inserted {inserted:,} / {len(df):,}")

        except Exception as e:
            print(f"  Error on row {idx}: {e}")
            continue

    conn.commit()
    print(f"  Total inserted: {inserted:,}")

    # Verify
    cursor.execute("SELECT COUNT(*) FROM Shipment")
    count = cursor.fetchone()[0]
    print(f"\nVerification: {count:,} shipments in database")

    cursor.execute("SELECT COUNT(*) FROM Carrier")
    carrier_count = cursor.fetchone()[0]
    print(f"Carriers: {carrier_count:,}")

    cursor.execute("SELECT COUNT(*) FROM Lane")
    lane_count = cursor.fetchone()[0]
    print(f"Lanes: {lane_count:,}")

    # Show sample stats
    cursor.execute("SELECT otdDesignation, COUNT(*) FROM Shipment GROUP BY otdDesignation")
    print("\nOTD Breakdown:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:,}")

    # Calculate overall OTD
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN otdDesignation IN ('On Time', 'Delivered On Time', 'Delivered Early') THEN 1 ELSE 0 END) as on_time
        FROM Shipment
    """)
    result = cursor.fetchone()
    if result[0] > 0:
        otd_pct = (result[1] / result[0]) * 100
        print(f"\nOverall OTD Rate: {otd_pct:.1f}%")

    conn.close()

    print("\n" + "=" * 60)
    print("IMPORT COMPLETE!")
    print("=" * 60)
    print("\nRefresh Prisma Studio (http://localhost:5555) to see the data.")
    print("Refresh the app (http://localhost:3001) to see real data in the dashboard.")

if __name__ == "__main__":
    main()

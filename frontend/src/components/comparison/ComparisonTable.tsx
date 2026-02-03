import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import type { ComparisonResult } from '../../context/ComparisonContext';

/**
 * ComparisonTable - Side-by-side vehicle comparison table
 *
 * AC: Feature-by-feature comparison matrix
 * AC: Best values highlighted in green
 * AC: Organized by category (price, performance, features)
 * AC: Glass-morphism design
 *
 * Features:
 * - Responsive layout (scrollable on mobile)
 * - Color-coded best values
 * - Spec grouping
 * - Price analysis display
 */
interface ComparisonTableProps {
  comparison: ComparisonResult;
}

interface SpecRow {
  category: string;
  name: string;
  values: Array<{
    vehicleId: string;
    value: string | number | boolean;
    isBest: boolean;
  }>;
  unit?: string;
  importance: number;
}

const ComparisonTable: React.FC<ComparisonTableProps> = ({ comparison }) => {
  const vehicles = comparison.comparison_results;

  /**
   * Build comparison rows from vehicle data
   * Includes best value highlighting logic
   */
  const comparisonRows = useMemo<SpecRow[]>(() => {
    const rows: SpecRow[] = [];

    // Price analysis row
    const priceRow: SpecRow = {
      category: 'Price',
      name: 'Current Price',
      values: vehicles.map((v) => {
        const price = v.price_analysis.current_price;
        // Best price = lowest
        const prices = vehicles.map((veh) => veh.price_analysis.current_price);
        const minPrice = Math.min(...prices);
        return {
          vehicleId: v.vehicle_id,
          value: price,
          isBest: price === minPrice,
        };
      }),
      importance: 1.0,
    };
    rows.push(priceRow);

    // Savings row (if any vehicle has savings)
    const hasSavings = vehicles.some((v) => v.price_analysis.savings_amount);
    if (hasSavings) {
      rows.push({
        category: 'Price',
        name: 'Savings vs Market',
        values: vehicles.map((v) => {
          const savings = v.price_analysis.savings_amount;
          // Best = highest savings
          const allSavings = vehicles
            .map((veh) => veh.price_analysis.savings_amount || 0)
            .filter((s) => s > 0);
          const maxSavings = allSavings.length > 0 ? Math.max(...allSavings) : 0;
          return {
            vehicleId: v.vehicle_id,
            value: savings ? `$${savings.toLocaleString()}` : '—',
            isBest: savings === maxSavings && savings > 0,
          };
        }),
        importance: 0.8,
      });
    }

    // Extract all specifications from vehicles
    const allSpecs = new Map<string, Set<string>>();

    vehicles.forEach((v) => {
      v.specifications.forEach((spec) => {
        if (!allSpecs.has(spec.category)) {
          allSpecs.set(spec.category, new Set());
        }
        allSpecs.get(spec.category)!.add(spec.name);
      });
    });

    // Build spec rows by category
    const categoryOrder = ['Performance', 'Efficiency', 'Safety', 'Comfort', 'Technology'];

    categoryOrder.forEach((category) => {
      if (!allSpecs.has(category)) return;

      const specNames = Array.from(allSpecs.get(category)!);
      specNames.forEach((specName) => {
        const specValues = vehicles.map((v) => {
          const spec = v.specifications.find(
            (s) => s.category === category && s.name === specName
          );

          let displayValue: string = '—';
          let numericValue: number | null = null;

          if (spec) {
            if (typeof spec.value === 'boolean') {
              displayValue = spec.value ? '✓ Yes' : '✗ No';
            } else if (typeof spec.value === 'number') {
              displayValue = spec.unit
                ? `${spec.value.toLocaleString()} ${spec.unit}`
                : spec.value.toLocaleString();
              numericValue = spec.value;
            } else {
              displayValue = String(spec.value);
            }
          }

          return {
            vehicleId: v.vehicle_id,
            value: displayValue,
            numericValue,
            rawValue: spec?.value,
          };
        });

        // Determine best value
        let bestVehicleId: string | null = null;

        // For numeric values, determine best based on context
        const numericValues = specValues
          .filter((sv) => sv.numericValue !== null)
          .map((sv) => ({ id: sv.vehicleId, value: sv.numericValue! }));

        if (numericValues.length > 0) {
          // Lower is better: Price, Mileage, 0-60 time
          const lowerIsBetter = ['Price', 'Mileage', 'Acceleration', '0-60', 'MPG Combined'].some(
            (term) => specName.toLowerCase().includes(term.toLowerCase())
          );

          // Higher is better: Range, Efficiency, Rating, Score
          const higherIsBetter = ['Range', 'Efficiency', 'Rating', 'Score', 'Capacity'].some(
            (term) => specName.toLowerCase().includes(term.toLowerCase())
          );

          if (lowerIsBetter) {
            const minValue = Math.min(...numericValues.map((nv) => nv.value));
            const best = numericValues.find((nv) => nv.value === minValue);
            if (best) bestVehicleId = best.id;
          } else if (higherIsBetter) {
            const maxValue = Math.max(...numericValues.map((nv) => nv.value));
            const best = numericValues.find((nv) => nv.value === maxValue);
            if (best) bestVehicleId = best.id;
          }
        }

        rows.push({
          category,
          name: specName,
          values: specValues.map((sv) => ({
            vehicleId: sv.vehicleId,
            value: sv.value,
            isBest: sv.vehicleId === bestVehicleId,
          })),
          importance: 0.7,
        });
      });
    });

    return rows;
  }, [vehicles]);

  /**
   * Get vehicle title from data
   */
  const getVehicleTitle = (vehicleId: string): string => {
    const vehicle = vehicles.find((v) => v.vehicle_id === vehicleId);
    if (!vehicle) return 'Unknown';

    const data = vehicle.vehicle_data as Record<string, unknown>;
    const year = data.year as number | undefined;
    const make = data.make as string | undefined;
    const model = data.model as string | undefined;
    const trim = data.trim as string | undefined;

    return [year, make, model, trim].filter(Boolean).join(' ');
  };

  /**
   * Get vehicle hero image
   */
  const getVehicleImage = (vehicleId: string): string | undefined => {
    const vehicle = vehicles.find((v) => v.vehicle_id === vehicleId);
    if (!vehicle) return undefined;

    const data = vehicle.vehicle_data as Record<string, unknown>;
    const images = data.images as Array<{ url: string; category: string }> | undefined;

    if (!images || images.length === 0) return undefined;

    const heroImage = images.find((img) => img.category === 'hero');
    return heroImage?.url || images[0]?.url;
  };

  return (
    <div
      style={{
        overflow: 'auto',
        borderRadius: '12px',
        background: 'rgba(255, 255, 255, 0.85)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.18)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
      }}
    >
      {/* Header Row - Vehicle Images and Titles */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `150px repeat(${vehicles.length}, 1fr)`,
          borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
        }}
      >
        {/* Empty corner cell */}
        <div
          style={{
            padding: '16px',
            fontWeight: 600,
            color: '#6b7280',
            borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
          }}
        />

        {/* Vehicle columns */}
        {vehicles.map((vehicle, index) => (
          <motion.div
            key={vehicle.vehicle_id}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            style={{
              padding: '16px',
              textAlign: 'center',
              borderBottom: '1px solid rgba(0, 0, 0, 0.1)',
            }}
          >
            {/* Vehicle Image */}
            {getVehicleImage(vehicle.vehicle_id) && (
              <img
                src={getVehicleImage(vehicle.vehicle_id)}
                alt={getVehicleTitle(vehicle.vehicle_id)}
                style={{
                  width: '100%',
                  height: '100px',
                  objectFit: 'cover',
                  borderRadius: '8px',
                  marginBottom: '12px',
                }}
              />
            )}

            {/* Vehicle Title */}
            <div
              style={{
                fontSize: '14px',
                fontWeight: 600,
                color: '#1a1a1a',
                lineHeight: '1.3',
              }}
            >
              {getVehicleTitle(vehicle.vehicle_id)}
            </div>

            {/* Match Score */}
            <div
              style={{
                marginTop: '8px',
                padding: '4px 12px',
                borderRadius: '20px',
                background: 'rgba(14, 165, 233, 0.1)',
                border: '1px solid rgba(14, 165, 233, 0.2)',
                fontSize: '12px',
                fontWeight: 600,
                color: '#0c4a6e',
                display: 'inline-block',
              }}
            >
              {Math.round(vehicle.overall_score * 100)}% Match
            </div>
          </motion.div>
        ))}
      </div>

      {/* Comparison Rows */}
      {comparisonRows.map((row, rowIndex) => (
        <div
          key={`${row.category}-${row.name}`}
          style={{
            display: 'grid',
            gridTemplateColumns: `150px repeat(${vehicles.length}, 1fr)`,
            borderBottom: rowIndex < comparisonRows.length - 1 ? '1px solid rgba(0, 0, 0, 0.1)' : undefined,
          }}
        >
          {/* Row Label - Sticky positioning (AC4) */}
          <div
            style={{
              padding: '12px 16px',
              fontSize: '13px',
              fontWeight: 500,
              color: '#374151',
              borderBottom: rowIndex < comparisonRows.length - 1 ? '1px solid rgba(0, 0, 0, 0.05)' : undefined,
              position: 'sticky',
              left: 0,
              zIndex: 10,
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(4px)',
            }}
          >
            {row.name}
          </div>

          {/* Vehicle Values */}
          {row.values.map((value, valueIndex) => (
            <motion.div
              key={value.vehicleId}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: rowIndex * 0.05 + valueIndex * 0.02 }}
              style={{
                padding: '12px 16px',
                textAlign: 'center',
                fontSize: '14px',
                color: value.isBest ? '#166534' : '#1a1a1a',
                fontWeight: value.isBest ? 600 : 400,
                background: value.isBest ? 'rgba(34, 197, 94, 0.15)' : undefined,
                borderBottom: rowIndex < comparisonRows.length - 1 ? '1px solid rgba(0, 0, 0, 0.05)' : undefined,
                position: 'relative',
              }}
            >
              {String(value.value)}
              {value.isBest && (
                <span
                  style={{
                    marginLeft: '6px',
                    fontSize: '10px',
                    color: '#166534',
                  }}
                >
                  ✓
                </span>
              )}
            </motion.div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default ComparisonTable;

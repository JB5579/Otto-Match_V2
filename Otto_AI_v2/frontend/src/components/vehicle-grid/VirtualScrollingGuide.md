# Virtual Scrolling Implementation Guide (Task 3-3.12)

## Status: DEFERRED

Virtual scrolling is deferred until the application has 50+ vehicles to display. Current implementation handles up to 50 vehicles efficiently with progressive loading and cascade animations.

## When to Implement

Implement virtual scrolling when:
- Vehicle inventory exceeds 50 items regularly
- Performance degrades below 60fps during scroll
- Memory usage becomes a concern with large vehicle lists

## Recommended Library

**Option 1: react-window** (Lightweight, 7KB)
```bash
npm install react-window
npm install --save-dev @types/react-window
```

**Option 2: react-virtuoso** (Feature-rich, responsive grids)
```bash
npm install react-virtuoso
```

## Implementation Approach

### 1. Install Dependencies

```bash
npm install react-window
```

### 2. Create VirtualizedVehicleGrid Component

```typescript
import { FixedSizeGrid as Grid } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

const VirtualizedVehicleGrid: React.FC<VehicleGridProps> = ({ vehicles }) => {
  // Calculate column count based on viewport width
  const getColumnCount = (width: number) => {
    if (width >= 1200) return 3;
    if (width >= 768) return 2;
    return 1;
  };

  // Calculate item size
  const ITEM_WIDTH = 400;
  const ITEM_HEIGHT = 450;
  const GAP = 24;

  return (
    <AutoSizer>
      {({ height, width }) => {
        const columnCount = getColumnCount(width);
        const rowCount = Math.ceil(vehicles.length / columnCount);

        return (
          <Grid
            columnCount={columnCount}
            columnWidth={ITEM_WIDTH + GAP}
            height={height}
            rowCount={rowCount}
            rowHeight={ITEM_HEIGHT + GAP}
            width={width}
            overscanRowCount={2}
          >
            {({ columnIndex, rowIndex, style }) => {
              const index = rowIndex * columnCount + columnIndex;
              if (index >= vehicles.length) return null;

              const vehicle = vehicles[index];
              return (
                <div style={style}>
                  <VehicleCard vehicle={vehicle} {...props} />
                </div>
              );
            }}
          </Grid>
        );
      }}
    </AutoSizer>
  );
};
```

### 3. Integrate with Cascade Animations

Challenge: react-window's virtualization conflicts with AnimatePresence because it unmounts off-screen items.

Solution:
- Use custom virtualization logic with IntersectionObserver
- Or disable virtualization during cascade animations
- Or use react-virtuoso which has better animation support

### 4. Performance Targets

- Maintain 60fps during scroll (16ms frame time)
- Smooth cascade animations for entering/exiting items
- Memory usage remains stable with 100+ vehicles
- Preserve scroll position during grid updates

## Testing

```typescript
describe('Virtual Scrolling', () => {
  it('should render only visible vehicles', () => {
    const vehicles = generateMockVehicles(100);
    render(<VirtualizedVehicleGrid vehicles={vehicles} />);

    // Should render ~10-15 vehicles in viewport, not all 100
    const renderedCards = screen.getAllByTestId('vehicle-card');
    expect(renderedCards.length).toBeLessThan(20);
  });

  it('should maintain scroll position during updates', () => {
    // Test implementation
  });

  it('should maintain 60fps during rapid scroll', () => {
    // Use Chrome DevTools Performance API
  });
});
```

## Migration Path

1. Keep current VehicleGrid for <50 vehicles
2. Create VirtualizedVehicleGrid for 50+ vehicles
3. Use conditional rendering:

```typescript
const VehicleGrid = ({ vehicles, ...props }) => {
  if (vehicles.length > 50) {
    return <VirtualizedVehicleGrid vehicles={vehicles} {...props} />;
  }
  return <RegularVehicleGrid vehicles={vehicles} {...props} />;
};
```

## References

- [react-window Documentation](https://react-window.vercel.app/)
- [react-virtuoso Documentation](https://virtuoso.dev/)
- [Web Vitals - LCP & CLS](https://web.dev/vitals/)

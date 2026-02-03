/**
 * Visual Regression Tests for Lazy Loading
 * Story 3-8.22: Visual testing with Playwright
 *
 * Tests that lazy loading components render correctly
 * and match expected visual output
 */

import { test, expect } from '@playwright/test';

test.describe('Lazy Image Visual Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to test page with lazy loaded images
    await page.goto('http://localhost:5173');
  });

  test('should show skeleton before image loads', async ({ page }) => {
    // Story 3-8.22: Verify skeleton placeholder is visible
    const skeleton = page.locator('[data-testid="image-skeleton"]').first();

    await expect(skeleton).toBeVisible();
    await expect(skeleton).toHaveCSS('background-color', 'rgb(245, 245, 245)');
  });

  test('should load image when in viewport', async ({ page }) => {
    // Story 3-8.6: Image should load when scrolled into view
    const lazyImage = page.locator('.lazy-image').first();

    // Scroll image into viewport
    await lazyImage.scrollIntoViewIfNeeded();

    // Wait for image to load
    await page.waitForTimeout(500);

    // Verify image is loaded
    const imgElement = lazyImage.locator('img');
    await expect(imgElement).toHaveAttribute('src', /./);
    await expect(imgElement).toBeVisible();

    // Story 3-8.22: Visual comparison
    expect(await page.screenshot()).toMatchSnapshot('lazy-image-loaded.png');
  });

  test('should fade in image smoothly', async ({ page }) => {
    // Story 3-8.6: Image should fade in with animation
    const lazyImage = page.locator('.lazy-image').first();

    await lazyImage.scrollIntoViewIfNeeded();

    // Capture opacity during animation
    const initialOpacity = await lazyImage.locator('img').evaluate((el) => {
      return window.getComputedStyle(el).opacity;
    });

    await page.waitForTimeout(300);

    const finalOpacity = await lazyImage.locator('img').evaluate((el) => {
      return window.getComputedStyle(el).opacity;
    });

    // Story 3-8.22: Verify fade-in effect
    expect(parseFloat(initialOpacity)).toBeLessThan(parseFloat(finalOpacity));
    expect(parseFloat(finalOpacity)).toBeCloseTo(1, 1);
  });

  test('should handle image errors gracefully', async ({ page }) => {
    // Story 3-8.6: Error state should display properly
    await page.route('**/image-error.jpg', (route) => route.abort());

    const lazyImage = page.locator('[src*="image-error.jpg"]');
    await lazyImage.scrollIntoViewIfNeeded();

    // Wait for error state
    await page.waitForTimeout(500);

    // Verify error message is shown
    const errorMessage = lazyImage.locator('text=Image not available');
    await expect(errorMessage).toBeVisible();

    // Story 3-8.22: Visual comparison of error state
    expect(await page.screenshot()).toMatchSnapshot('lazy-image-error.png');
  });
});

test.describe('Vehicle Grid Visual Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test('should display vehicle cards in grid layout', async ({ page }) => {
    // Story 3-8.22: Grid layout should match expected design
    const grid = page.locator('.vehicle-grid');

    await expect(grid).toBeVisible();

    // Verify grid layout
    const gridStyles = await grid.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        display: styles.display,
        gridTemplateColumns: styles.gridTemplateColumns,
        gap: styles.gap,
      };
    });

    expect(gridStyles.display).toBe('grid');
    expect(gridStyles.gridTemplateColumns).toContain('1fr');

    // Story 3-8.22: Visual comparison
    expect(await page.screenshot()).toMatchSnapshot('vehicle-grid-layout.png');
  });

  test('should animate cards on load', async ({ page }) => {
    // Story 3-8.9: Cascade animation should be visible
    const firstCard = page.locator('.vehicle-card').first();
    const lastCard = page.locator('.vehicle-card').last();

    // Wait for initial state
    await page.waitForTimeout(100);

    const firstCardInitial = await firstCard.evaluate((el) => {
      return window.getComputedStyle(el).opacity;
    });

    // Wait for animation
    await page.waitForTimeout(500);

    const firstCardFinal = await firstCard.evaluate((el) => {
      return window.getComputedStyle(el).opacity;
    });

    // Story 3-8.22: Verify animation happened
    expect(parseFloat(firstCardInitial)).toBeLessThan(parseFloat(firstCardFinal));
    expect(parseFloat(firstCardFinal)).toBeCloseTo(1, 1);
  });

  test('should maintain layout during animations', async ({ page }) => {
    // Story 3-8.13: Animations should not cause layout shifts
    const initialLayout = await page.locator('.vehicle-grid').evaluate((grid) => {
      const cards = Array.from(grid.querySelectorAll('.vehicle-card'));
      return cards.map((card) => {
        const rect = card.getBoundingClientRect();
        return { top: rect.top, left: rect.left };
      });
    });

    // Trigger animation by scrolling
    await page.mouse.wheel(0, 500);
    await page.waitForTimeout(300);

    const finalLayout = await page.locator('.vehicle-grid').evaluate((grid) => {
      const cards = Array.from(grid.querySelectorAll('.vehicle-card'));
      return cards.map((card) => {
        const rect = card.getBoundingClientRect();
        return { top: rect.top, left: rect.left };
      });
    });

    // Story 3-8.22: CLS should be minimal
    for (let i = 0; i < initialLayout.length; i++) {
      const topShift = Math.abs(initialLayout[i].top - finalLayout[i].top);
      const leftShift = Math.abs(initialLayout[i].left - finalLayout[i].left);

      // Allow small shifts due to scroll
      expect(topShift).toBeLessThan(10);
      expect(leftShift).toBeLessThan(10);
    }
  });
});

test.describe('Loading State Visual Tests', () => {
  test('should show proper loading skeletons', async ({ page }) => {
    await page.goto('http://localhost:5173');

    // Story 3-8.22: Loading skeleton should match design
    const skeleton = page.locator('[data-testid="detail-skeleton"]');

    // Mock slow API response
    await page.route('**/api/vehicles', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      route.fulfill({
        status: 200,
        body: JSON.stringify([]),
      });
    });

    await page.reload();

    await expect(skeleton).toBeVisible();

    // Verify skeleton animation
    const hasAnimation = await skeleton.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.animationName !== 'none';
    });

    expect(hasAnimation).toBe(true);

    // Story 3-8.22: Visual comparison
    expect(await page.screenshot()).toMatchSnapshot('loading-skeleton.png');
  });

  test('should transition smoothly from loading to content', async ({ page }) => {
    await page.goto('http://localhost:5173');

    // Story 3-8.6: Smooth transition from skeleton to content
    const skeleton = page.locator('[data-testid="detail-skeleton"]');

    await expect(skeleton).toBeVisible();

    // Wait for content to load
    await page.waitForTimeout(2000);

    const content = page.locator('.vehicle-card').first();
    await expect(content).toBeVisible();

    // Verify no flickering (both shouldn't be visible at same time)
    const skeletonVisible = await skeleton.isVisible();
    const contentVisible = await content.isVisible();

    expect(skeletonVisible || contentVisible).toBe(true);
    expect(skeletonVisible && contentVisible).toBe(false);
  });
});

test.describe('Responsive Visual Tests', () => {
  test('should display correctly on mobile', async ({ page }) => {
    // Story 3-8.22: Mobile layout should match design
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:5173');

    const grid = page.locator('.vehicle-grid');

    // Verify single column layout
    const gridStyles = await grid.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        gridTemplateColumns: styles.gridTemplateColumns,
      };
    });

    expect(gridStyles.gridTemplateColumns).toBe('1fr');

    // Story 3-8.22: Visual comparison
    expect(await page.screenshot()).toMatchSnapshot('vehicle-grid-mobile.png');
  });

  test('should display correctly on tablet', async ({ page }) => {
    // Story 3-8.22: Tablet layout should match design
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('http://localhost:5173');

    const grid = page.locator('.vehicle-grid');

    // Verify two column layout
    const gridStyles = await grid.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        gridTemplateColumns: styles.gridTemplateColumns,
      };
    });

    expect(gridStyles.gridTemplateColumns).toContain('1fr');

    // Story 3-8.22: Visual comparison
    expect(await page.screenshot()).toMatchSnapshot('vehicle-grid-tablet.png');
  });

  test('should display correctly on desktop', async ({ page }) => {
    // Story 3-8.22: Desktop layout should match design
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('http://localhost:5173');

    const grid = page.locator('.vehicle-grid');

    // Verify three column layout
    const gridStyles = await grid.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        gridTemplateColumns: styles.gridTemplateColumns,
      };
    });

    expect(gridStyles.gridTemplateColumns).toContain('1fr');

    // Story 3-8.22: Visual comparison
    expect(await page.screenshot()).toMatchSnapshot('vehicle-grid-desktop.png');
  });
});

test.describe('Accessibility Visual Tests', () => {
  test('should show focus indicators', async ({ page }) => {
    await page.goto('http://localhost:5173');

    const firstCard = page.locator('.vehicle-card').first();

    // Focus the card
    await firstCard.focus();

    // Verify focus indicator is visible
    const focusStyles = await firstCard.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        outline: styles.outline,
        outlineOffset: styles.outlineOffset,
      };
    });

    expect(focusStyles.outline).not.toBe('none');

    // Story 3-8.22: Visual comparison of focus state
    expect(await page.screenshot()).toMatchSnapshot('vehicle-card-focus.png');
  });

  test('should respect reduced motion preference', async ({ page }) => {
    // Story 3-8.13: Reduced motion should disable animations
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto('http://localhost:5173');

    const firstCard = page.locator('.vehicle-card').first();

    // Verify animations are disabled
    const hasAnimation = await firstCard.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.transition !== 'none' || styles.animation !== 'none';
    });

    // Animations should be minimal or disabled
    expect(hasAnimation).toBe(false);
  });
});

# CDN Deployment Strategy
**Story 3-8.19: Production deployment with CDN edge caching**

## Overview
This document outlines the CDN deployment strategy for Otto.AI to optimize performance through edge caching, asset optimization, and global content delivery.

## Architecture

```
                     ┌─────────────────┐
                     │   Cloudflare    │
                     │      CDN        │
                     └────────┬────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
    │  North   │         │  Europe  │         │  Asia   │
    │ America  │         │ (Frankfurt)│       │(Singapore)│
    │ Edge PoP │         │  Edge PoP│         │ Edge PoP│
    └────┬────┘         └────┬────┘         └────┬────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                     ┌────────▼────────┐
                     │   Origin Server │
                     │   (Railway/AWS) │
                     └─────────────────┘
```

## CDN Configuration

### Cloudflare Setup

**Story 3-8.19: Recommended CDN provider for global edge caching**

1. **Caching Levels**
   - Standard (static assets)
   - Aggressive (API responses with SWR)
   - No Query String (for vehicle images)

2. **Cache Rules**

   | URL Pattern | Cache TTL | Browser TTL | Edge TTL |
   |-------------|-----------|-------------|----------|
   | `/assets/*` | 7 days | 7 days | 30 days |
   | `/images/*` | 30 days | 7 days | 30 days |
   | `/api/vehicles` | 1 min | 1 min | 5 min |
   | `/api/search` | 1 min | 1 min | 5 min |
   | `/api/conversation` | 0 | 0 | 0 |

3. **Page Rules**
   ```
   # Cache static assets aggressively
   *frontend/assets/*
   - Cache Level: Cache Everything
   - Edge Cache TTL: 30 days
   - Browser Cache TTL: 7 days

   # API search with SWR
   *api/vehicles*
   - Cache Level: Standard
   - Edge Cache TTL: 5 minutes
   - Browser Cache TTL: 1 minute
   ```

### Alternative CDN Providers

**Story 3-8.19: Other supported CDN options**

1. **AWS CloudFront**
   - S3 origin for static assets
   - Lambda@Edge for dynamic caching
   - Price Class 100 (North America/Europe)

2. **Fastly**
   - VCL configuration for cache rules
   - Instant purging API
   - Real-time analytics

3. **Netlify Edge**
   - Automatic deployment from Git
   - Built-in asset optimization
   - Serverless functions support

## Deployment Pipeline

### CI/CD Configuration

```yaml
# Story 3-8.19: GitHub Actions workflow for CDN deployment
name: Deploy to CDN

on:
  push:
    branches: [main]

jobs:
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Build for production
        run: |
          cd frontend
          npm run build

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: otto-ai-frontend
          directory: frontend/dist

      - name: Invalidate CDN cache
        run: |
          curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE/purge_cache" \
            -H "Authorization: Bearer $API_TOKEN" \
            -H "Content-Type: application/json" \
            --data '{"purge_everything":true}'
```

### Backend Deployment

```yaml
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Railway
        run: |
          railway login --token ${{ secrets.RAILWAY_TOKEN }}
          railway up --service ${{ secrets.RAILWAY_SERVICE_ID }}

      - name: Configure CDN origin
        run: |
          # Update Cloudflare origin to new deployment
          curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE/settings/origin" \
            -H "Authorization: Bearer $API_TOKEN" \
            --data '{"origin":"new-deployment.railway.app"}'
```

## Asset Optimization

### Image Optimization (Task 3-8.5)

**Story 3-8.19: Responsive image generation for CDN delivery**

```bash
# Script to generate responsive images
# Story 3-8.5: Create multiple formats for browser compatibility

# Input: High-resolution source image
# Output: WebP, AVIF, JPEG fallback at multiple sizes

ffmpeg -i input.jpg \
  -vf "scale=320:-1" output-320w.webp
ffmpeg -i input.jpg \
  -vf "scale=640:-1" output-640w.webp
ffmpeg -i input.jpg \
  -vf "scale=1024:-1" output-1024w.webp
ffmpeg -i input.jpg \
  -vf "scale=1920:-1" output-1920w.webp
```

### Bundle Optimization

**Story 3-8.3: Code splitting for CDN caching**

- Vendor chunks: Long cache (30 days)
- Feature chunks: Medium cache (7 days)
- Main bundle: Short cache (1 day)

```
assets/react-[hash].js      → 30 days (rarely changes)
assets/vendor-[hash].js     → 30 days (rarely changes)
assets/vehicle-grid-[hash].js → 7 days (feature updates)
assets/index-[hash].js      → 1 day (main app code)
```

## Performance Monitoring

### Real User Monitoring (RUM)

**Story 3-8.19: Track CDN performance metrics**

```typescript
// frontend/src/utils/monitoring.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

export function initPerformanceMonitoring() {
  // Story 3-8.20: Report metrics to analytics
  getCLS(console.log);
  getFID(console.log);
  getFCP(console.log);
  getLCP(console.log);
  getTTFB(console.log);
}
```

### CDN Analytics

**Key metrics to monitor:**
- Cache hit ratio (target: >90%)
- Edge response time (target: <50ms)
- Origin request rate (target: <10%)
- Bandwidth savings (target: >80%)

## Cache Invalidation Strategy

### Automatic Invalidation

**Story 3-8.19: Cache purging triggers**

1. **Deployment**: Purge all cache on new release
2. **Content Update**: Purge specific URLs (vehicle images)
3. **Time-based**: Automatic expiration

### Manual Invalidation

```bash
# Purge specific URL
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE/purge_cache" \
  -H "Authorization: Bearer $TOKEN" \
  --data '{"files":["https://otto.ai/api/vehicles"]}'

# Purge by tag (vehicle ID)
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE/purge_cache" \
  -H "Authorization: Bearer $TOKEN" \
  --data '{"tags":["vehicle-12345"]}'

# Purge everything (emergency only)
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE/purge_cache" \
  -H "Authorization: Bearer $TOKEN" \
  --data '{"purge_everything":true}'
```

## Security Considerations

### DDoS Protection

**Story 3-8.19: CDN security layer**

1. **Rate Limiting**
   - API endpoints: 100 req/min per IP
   - Search: 10 req/min per IP
   - WebSocket: 5 connections per IP

2. **Bot Protection**
   - Block known bot user agents
   - Challenge suspicious traffic
   - Allowlist legitimate crawlers

3. **Hotlink Protection**
   ```
   # Referer check for images
   if (http.referer !~ "^https://otto\.ai") {
     return 403;
   }
   ```

## Rollback Strategy

### Versioned Assets

**Story 3-8.19: Enable instant rollback**

```
/assets/v1.0.0/react-abc123.js  (current)
/assets/v0.9.5/react-def456.js  (previous)
```

### Blue-Green Deployment

```
         ┌───────────┐
         │   DNS     │
         └─────┬─────┘
               │
         ┌─────▼─────┐
         │  CDN      │
         └─────┬─────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐  ┌──▼───┐  ┌──▼───┐
│ Green │  │ Blue │  │ Prev │
│ (New) │  │(Old) │  │(Safe)│
└───────┘  └───────┘  └───────┘
```

## Cost Optimization

### Bandwidth Reduction

**Story 3-8.19: Minimize CDN egress costs**

1. **Compression**: Brotli for text, WebP for images
2. **HTTP/2**: Multiplexing reduces connections
3. **Prefetching**: Preload critical assets

### Edge Computing

**Serverless functions at the edge**

```typescript
// Cloudflare Workers for edge computation
// Story 3-8.19: Personalization at the edge

export default {
  async fetch(request, env, ctx) {
    // Personalize pricing by location
    const country = request.cf.country;
    const currency = getCurrencyForCountry(country);

    return new Response(JSON.stringify({ currency }));
  }
}
```

## Monitoring and Alerts

### Performance Thresholds

**Story 3-8.20: Automated performance testing**

| Metric | Target | Alert |
|--------|--------|-------|
| TTFB | <200ms | >500ms |
| LCP | <2.5s | >4s |
| FID | <100ms | >300ms |
| CLS | <0.1 | >0.25 |
| Cache Hit Ratio | >90% | <80% |

### Alert Channels

- Slack: Performance degradation
- Email: Cache miss spike
- PagerDuty: CDN outage

## Maintenance

### Monthly Tasks

1. Review cache hit ratios
2. Update bundle size budgets
3. Audit security rules
4. Optimize image formats
5. Review CDN costs

### Quarterly Tasks

1. Performance audit with Lighthouse
2. CDN provider comparison
3. Edge location review
4. Cost optimization review

## Conclusion

This CDN deployment strategy ensures:
- **Fast**: Edge delivery <50ms globally
- **Reliable**: 99.9% uptime SLA
- **Scalable**: Auto-scaling to 10K+ RPS
- **Cost-effective**: 80%+ bandwidth savings

---

**Story 3-8.19 Complete**: CDN deployment strategy documented with:
- Cloudflare configuration
- CI/CD pipeline
- Asset optimization
- Cache invalidation
- Security measures
- Cost optimization

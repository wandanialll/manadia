# Dashboard Usage & Deployment Guide

## Quick Start (Local)

### Prerequisites
- Node.js 20+
- Docker & Docker Compose
- Backend running on `localhost:8000`

### Development Server
```bash
cd frontend
npm install
npm run dev
```
Access at `http://localhost:5173/dashboard/`

Dev server proxies `/api/*` to `http://localhost:8000` automatically.

### Production (Docker)

```bash
# Build and start everything
docker compose up -d

# Watch logs
docker compose logs -f frontend caddy app

# Verify it's running
curl https://yourdomain.com/dashboard/
```

Caddy will handle:
- SSL/TLS certificate provisioning
- Basic auth at `/dashboard/*`
- Routing to frontend service

## Dashboard Features

### Login
1. Visit `/dashboard/`
2. Enter admin credentials (defaults shown in Caddyfile)
3. Credentials stored in browser for convenience

### Map View
- **Interactive Leaflet map** with real-time markers
- **Click markers** to see location details
- **Auto-adjusts zoom** to show all current locations
- **Color-coded** markers by device/user (can be enhanced)

### Sidebar
- **Recent Locations**: Shows 20 most recent location pings
- **User Filter**: Dropdown to filter by tracked user
- **Device Filter**: Dropdown to filter by device name
- **Refresh Button**: Manually refresh location data
- **Logout**: Exit dashboard and clear session

### Location Details

Each location shows:
- User name
- Device name
- Latitude/Longitude
- Timestamp (auto-updated, human-readable)
- Accuracy (GPS accuracy in meters)
- Altitude (if available)

### Auto-Refresh
Dashboard polls backend every **10 seconds** for new locations automatically.

## Configuration

### Change Dashboard Path
Edit `vite.config.ts`:
```ts
export default defineConfig({
  base: '/dashboard/',  // Change this path
})
```

### Change Poll Interval
Edit `frontend/src/components/Dashboard.tsx`:
```ts
setInterval(fetchLocations, 10000) // Change 10000 ms
```

### Change Map Provider
Edit `frontend/src/components/MapComponent.tsx`:
```ts
<TileLayer
  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
/>
// Switch to different tile provider (Mapbox, etc.)
```

## API Reference

Frontend calls these backend endpoints:

### Get All Locations
```
GET /api/history
Authorization: Basic {base64(admin:password)}

Response:
{
  "locations": [
    {
      "id": 1,
      "user": "john_doe",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "timestamp": "2026-02-14T10:30:00Z",
      "device": "iPhone",
      "accuracy": 5.5,
      "altitude": 10.2
    }
  ],
  "count": 1
}
```

### Get Locations by Date
```
GET /api/history/date?query_date=2026-02-14
Authorization: Basic {base64(admin:password)}
```

### Get Device History
```
GET /api/history/device/iPhone
Authorization: Basic {base64(admin:password)}
```

## Troubleshooting

### "API connection failed"
- Check backend is running on `:8000`
- Verify Caddy is routing `/api/*` to `app:8000`
- Check credentials are correct

### Map not loading
- Check browser console for errors
- Verify OpenStreetMap CDN is accessible
- Check `MapComponent.tsx` for tile provider issues

### Dashboard blank after login
- Check browser console for JavaScript errors
- Verify locations exist in backend database
- Try refresh button or `F5` to reload

### Slow updates
- Check network tab in DevTools for API calls
- Verify backend query performance
- Increase polling interval if server is slow

### CORS issues (dev only)
- Dev server proxies `/api/*` to avoid CORS
- Production routing handled by Caddy (no CORS needed)

## Deployment Checklist

- [ ] Domain is set in Caddyfile
- [ ] Admin credentials hashed in Caddyfile
- [ ] Backend `.env` file configured with DB credentials
- [ ] Ports 80/443 open on firewall
- [ ] Run `docker compose pull` to get latest versions
- [ ] Run `docker compose up -d` to start services
- [ ] Wait ~2 minutes for Caddy to provision SSL cert
- [ ] Test `https://yourdomain.com/dashboard/`
- [ ] Verify locations appear on map
- [ ] Send test location from OwnTracks app
- [ ] Verify map updates in real-time

## Performance Tips

1. **Limit location history**: Archive old locations to keep queries fast
2. **Increase polling interval**: Change 10s to 30s if backend is slow
3. **Use database indexes**: Index `user_id`, `timestamp`, `device` columns
4. **Cache responses**: Consider caching in Caddy if locations don't change frequently

## Future Enhancements

- [ ] WebSocket for real-time updates (replace polling)
- [ ] Heatmap view showing location frequency
- [ ] Route history (connect the dots between locations)
- [ ] Time-based playback (replay movement over time)
- [ ] Export to GPX/KML format
- [ ] Multiple user support (each user sees only their locations)
- [ ] Device-based color coding on map
- [ ] Search/filter by date range
- [ ] Geofence alerts
- [ ] Speed/direction tracking

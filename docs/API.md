# Smart Classroom Edge AI API

## Backend

### `GET /api/v1/health`
Service health check.

### `GET /api/v1/dashboard/live`
Returns latest occupancy, activity and AC state.

### `GET /api/v1/dashboard/history`
Returns occupancy and temperature time-series.

### `POST /api/v1/inference`
Accepts edge inference payload:

```json
{
  "occupancyCount": 7,
  "activity": "Class Running",
  "confidence": 0.92,
  "detections": []
}
```

## AI Model Service

### `GET /health`
AI service health.

### `POST /infer`
Body:

```json
{
  "imageBase64": "<base64-jpeg>"
}
```

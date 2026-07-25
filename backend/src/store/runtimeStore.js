const { getAcStateByOccupancy, getOccupancyBand } = require('../services/acControlService');

const MAX_HISTORY = 120;
const ALLOWED_ACTIVITIES = [
  'Students Entering',
  'Students Leaving',
  'Janitor Cleaning',
  'Class Running',
  'Class Finished',
];

const state = {
  live: {
    timestamp: new Date().toISOString(),
    occupancyCount: 0,
    occupancyBand: 'LOW',
    activity: 'Class Finished',
    acState: getAcStateByOccupancy(0),
    confidence: 0,
    detections: [],
  },
  occupancyHistory: [],
  temperatureHistory: [],
};

function sanitizeActivity(activity) {
  return ALLOWED_ACTIVITIES.includes(activity) ? activity : 'Class Running';
}

function clampOccupancy(value) {
  if (!Number.isFinite(value)) {
    return 0;
  }

  return Math.max(0, Math.floor(value));
}

function updateLiveMetrics(payload) {
  const occupancyCount = clampOccupancy(payload.occupancyCount);
  const timestamp = payload.timestamp || new Date().toISOString();
  const acState = getAcStateByOccupancy(occupancyCount);

  state.live = {
    timestamp,
    occupancyCount,
    occupancyBand: getOccupancyBand(occupancyCount),
    activity: sanitizeActivity(payload.activity),
    acState,
    confidence: Number(payload.confidence || 0),
    detections: Array.isArray(payload.detections) ? payload.detections : [],
  };

  state.occupancyHistory.push({
    timestamp,
    occupancyCount,
  });

  state.temperatureHistory.push({
    timestamp,
    temperatureC: acState.temperatureC || 30,
  });

  if (state.occupancyHistory.length > MAX_HISTORY) {
    state.occupancyHistory.shift();
  }

  if (state.temperatureHistory.length > MAX_HISTORY) {
    state.temperatureHistory.shift();
  }

  return state.live;
}

function seedDemoData() {
  if (state.occupancyHistory.length > 0) {
    return;
  }

  const now = Date.now();
  for (let i = 30; i >= 0; i -= 1) {
    const occupancyCount = Math.max(0, Math.round(6 + Math.sin(i / 3) * 5 + (i % 4 === 0 ? 2 : 0)));
    const timestamp = new Date(now - i * 60_000).toISOString();
    updateLiveMetrics({
      occupancyCount,
      activity: occupancyCount > 0 ? 'Class Running' : 'Class Finished',
      confidence: 0.9,
      timestamp,
      detections: [],
    });
  }
}

seedDemoData();

module.exports = {
  state,
  updateLiveMetrics,
};

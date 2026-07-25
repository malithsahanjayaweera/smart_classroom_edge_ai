function getAcStateByOccupancy(occupancyCount) {
  if (occupancyCount <= 2) {
    return { power: 'OFF', temperatureC: null, fanSpeed: 'LOW' };
  }

  if (occupancyCount <= 9) {
    return { power: 'ON', temperatureC: 24, fanSpeed: 'MEDIUM' };
  }

  return { power: 'ON', temperatureC: 20, fanSpeed: 'HIGH' };
}

function getOccupancyBand(occupancyCount) {
  if (occupancyCount <= 2) {
    return 'LOW';
  }

  if (occupancyCount <= 9) {
    return 'MEDIUM';
  }

  return 'HIGH';
}

module.exports = { getAcStateByOccupancy, getOccupancyBand };

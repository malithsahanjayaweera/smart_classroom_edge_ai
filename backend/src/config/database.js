const mongoose = require('mongoose');

async function connectToDatabase(mongoUri) {
  if (!mongoUri) {
    return { connected: false, reason: 'MONGO_URI is not configured; using in-memory data store' };
  }

  await mongoose.connect(mongoUri, {
    serverSelectionTimeoutMS: 5000,
  });

  return { connected: true };
}

module.exports = { connectToDatabase };

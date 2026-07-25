const express = require('express');
const cors = require('cors');
const config = require('./config/env');
const { connectToDatabase } = require('./config/database');
const healthRoutes = require('./routes/healthRoutes');
const dashboardRoutes = require('./routes/dashboardRoutes');
const inferenceRoutes = require('./routes/inferenceRoutes');

const app = express();
const allowedOrigins = config.corsOrigin
  .split(',')
  .map((origin) => origin.trim())
  .filter(Boolean);

app.use(
  cors({
    origin(origin, callback) {
      if (!origin || allowedOrigins.includes(origin)) {
        return callback(null, true);
      }

      return callback(new Error('Origin not allowed by CORS policy'));
    },
  }),
);
app.use(express.json({ limit: '1mb' }));

app.use('/api/v1/health', healthRoutes);
app.use('/api/v1/dashboard', dashboardRoutes);
app.use('/api/v1/inference', inferenceRoutes);

app.use((error, _req, res, _next) => {
  console.error('Unhandled backend error:', error);
  return res.status(500).json({
    message: 'Unexpected backend error',
  });
});

async function bootstrap() {
  try {
    const database = await connectToDatabase(config.mongoUri);
    if (!database.connected) {
      console.warn(`[database] ${database.reason}`);
    }

    app.listen(config.port, () => {
      console.log(`Backend listening on port ${config.port}`);
    });
  } catch (error) {
    console.error('Failed to start backend:', error);
    process.exit(1);
  }
}

bootstrap();

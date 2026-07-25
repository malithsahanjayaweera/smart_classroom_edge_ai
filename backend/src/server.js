const express = require('express');
const cors = require('cors');
const config = require('./config/env');
const { connectToDatabase } = require('./config/database');
const healthRoutes = require('./routes/healthRoutes');
const dashboardRoutes = require('./routes/dashboardRoutes');
const inferenceRoutes = require('./routes/inferenceRoutes');

const app = express();

app.use(cors({ origin: config.corsOrigin }));
app.use(express.json({ limit: '1mb' }));

app.use('/api/v1/health', healthRoutes);
app.use('/api/v1/dashboard', dashboardRoutes);
app.use('/api/v1/inference', inferenceRoutes);

app.use((error, _req, res, _next) => {
  return res.status(500).json({
    message: 'Unexpected backend error',
    details: error.message,
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

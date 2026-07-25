const express = require('express');
const { updateLiveMetrics } = require('../store/runtimeStore');

const router = express.Router();

router.post('/', (req, res) => {
  const payload = req.body || {};

  if (typeof payload.occupancyCount !== 'number') {
    return res.status(400).json({
      message: 'occupancyCount is required and must be a number',
    });
  }

  const liveData = updateLiveMetrics(payload);

  return res.status(201).json({
    message: 'Inference payload accepted',
    liveData,
  });
});

module.exports = router;

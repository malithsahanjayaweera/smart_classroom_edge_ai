const express = require('express');
const { state } = require('../store/runtimeStore');

const router = express.Router();

router.get('/live', (_req, res) => {
  res.status(200).json(state.live);
});

router.get('/history', (_req, res) => {
  res.status(200).json({
    occupancyHistory: state.occupancyHistory,
    temperatureHistory: state.temperatureHistory,
  });
});

module.exports = router;

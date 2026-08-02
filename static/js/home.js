(function () {
    'use strict';

    var SEATS = 20;
    var ARC = 235;              // visible dial arc length (270° of r=50)
    var CYCLE_MS = 4200;
    var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    var BANDS = [
        { name: 'LOW',    seats: 2,  ac: false, temp: null },
        { name: 'MEDIUM', seats: 6,  ac: true,  temp: 24 },
        { name: 'HIGH',   seats: 14, ac: true,  temp: 20 }
    ];

    var sim = document.getElementById('sim');
    var desksEl = document.getElementById('desks');
    var bandEl = document.getElementById('sim-band');
    var countEl = document.getElementById('sim-count');
    var tempEl = document.getElementById('sim-temp');
    var acEl = document.getElementById('sim-ac');
    var dialFill = document.getElementById('dial-fill');
    var cards = document.querySelectorAll('.policy-card');

    /* Fixed pseudo-random fill order so seats populate organically
       but identically on every visit. */
    var ORDER = [7, 12, 2, 16, 9, 4, 18, 1, 13, 6, 11, 19, 0, 15, 8, 3, 17, 10, 5, 14];

    var desks = [];
    for (var i = 0; i < SEATS; i++) {
        var d = document.createElement('div');
        d.className = 'desk';
        desksEl.appendChild(d);
        desks.push(d);
    }

    var countTimer = null;
    var shown = 0;

    function animateCount(to) {
        if (countTimer) {
            clearInterval(countTimer);
        }
        if (reduced) {
            shown = to;
            countEl.textContent = String(to);
            return;
        }
        countTimer = setInterval(function () {
            if (shown === to) {
                clearInterval(countTimer);
                countTimer = null;
                return;
            }
            shown += shown < to ? 1 : -1;
            countEl.textContent = String(shown);
        }, 55);
    }

    function apply(index) {
        var band = BANDS[index];

        // seats
        ORDER.forEach(function (seat, rank) {
            var taken = rank < band.seats;
            var desk = desks[seat];
            if (reduced) {
                desk.classList.toggle('is-taken', taken);
            } else {
                setTimeout(function () {
                    desk.classList.toggle('is-taken', taken);
                }, rank * 32);
            }
        });

        animateCount(band.seats);

        // climate
        sim.classList.toggle('ac-on', band.ac);
        sim.classList.toggle('ac-off', !band.ac);
        bandEl.textContent = band.name;
        acEl.textContent = band.ac ? 'AC ON' : 'AC OFF';
        tempEl.innerHTML = band.temp ? band.temp + '°' : '&mdash;';

        // cooler target => fuller dial (18–30 °C range)
        var fraction = band.temp ? (30 - band.temp) / 12 : 0;
        dialFill.setAttribute('stroke-dashoffset', String(ARC * (1 - fraction)));

        cards.forEach(function (c) {
            c.classList.toggle('is-active', Number(c.dataset.band) === index);
        });
    }

    /* ---------- auto cycle, surrendered on first interaction ---------- */

    var current = 0;
    var cycle = null;
    var locked = false;     // set once the visitor picks a band themselves

    function startCycle() {
        if (locked || cycle) {
            return;
        }
        cycle = setInterval(function () {
            current = (current + 1) % BANDS.length;
            apply(current);
        }, CYCLE_MS);
    }

    function stopCycle() {
        if (cycle) {
            clearInterval(cycle);
            cycle = null;
        }
    }

    cards.forEach(function (card) {
        card.addEventListener('click', function () {
            locked = true;
            stopCycle();
            current = Number(card.dataset.band);
            apply(current);
        });
    });

    apply(0);
    if (!reduced) {
        startCycle();
    }

    /* ---------- pipeline pulse ---------- */

    var steps = document.querySelectorAll('.pipe-step');
    if (steps.length && !reduced) {
        var hot = 0;
        setInterval(function () {
            steps.forEach(function (s, i) {
                s.classList.toggle('is-hot', i === hot);
            });
            hot = (hot + 1) % steps.length;
        }, 850);
    }

    /* Pause the simulator while it is off-screen. */
    if ('IntersectionObserver' in window && !reduced) {
        new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    startCycle();
                } else {
                    stopCycle();
                }
            });
        }, { threshold: 0.15 }).observe(sim);
    }
}());

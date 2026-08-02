(function () {
    'use strict';

    var SAMPLE_MS = 500;
    var MAX_LOGS = 300;

    // The frame is sent with its aspect ratio intact — the server does the
    // ByShorterSide resize and centre crop the model was trained on.
    // Squashing to a square here (as this used to) distorts 16:9 footage
    // and makes the classifier confidently wrong.
    var SEND_SHORTER_SIDE = 320;

    var stage = document.getElementById('stage');
    var video = document.getElementById('video');
    var photo = document.getElementById('photo');
    var fileInput = document.getElementById('file-input');
    var loadedSelect = document.getElementById('loaded-select');
    var activeSource = document.getElementById('active-source');
    var statusPill = document.getElementById('status-pill');
    var statusText = document.getElementById('status-text');
    var logBox = document.getElementById('log-box');
    var probList = document.getElementById('prob-list');

    var el = {
        occupancy: document.getElementById('val-occupancy'),
        acState: document.getElementById('val-ac-state'),
        temp: document.getElementById('val-temp'),
        tempBadge: document.getElementById('temp-badge'),
        confidence: document.getElementById('val-confidence'),
        tag: document.getElementById('val-tag'),
        meter: document.getElementById('confidence-meter'),
        acTime: document.getElementById('val-ac-time'),
        frames: document.getElementById('val-frames'),
        reason: document.getElementById('val-reason'),
        banner: document.getElementById('override-banner'),
        bannerDetail: document.getElementById('override-detail')
    };

    var acCard = el.acState.closest('.stat');

    var canvas = document.createElement('canvas');
    var ctx = canvas.getContext('2d');

    function naturalSize(src) {
        return src.tagName === 'IMG'
            ? { w: src.naturalWidth, h: src.naturalHeight }
            : { w: src.videoWidth, h: src.videoHeight };
    }

    var loaded = [];          // { name, url, kind, revocable }
    var acSeconds = 0;
    var frameCount = 0;
    var timer = null;
    var stream = null;
    var lastAcState = null;
    var lastOverride = null;
    var sourceKind = null;    // 'video' | 'image'

    /* ---------------- status + logging ---------------- */

    function setStatus(text, state) {
        statusText.textContent = text;
        statusPill.classList.toggle('is-live', state === 'live');
        statusPill.classList.toggle('is-error', state === 'error');
    }

    function log(message, level) {
        var empty = logBox.querySelector('.log-empty');
        if (empty) {
            logBox.removeChild(empty);
        }

        var now = new Date();
        var stamp = [now.getHours(), now.getMinutes(), now.getSeconds()]
            .map(function (n) { return String(n).padStart(2, '0'); })
            .join(':');

        var line = document.createElement('div');
        line.className = 'log-line lv-' + (level || 'info');

        var t = document.createElement('span');
        t.className = 'log-time';
        t.textContent = '[' + stamp + ']';

        var m = document.createElement('span');
        m.className = 'log-msg';
        m.textContent = '> ' + message;

        line.appendChild(t);
        line.appendChild(m);
        logBox.appendChild(line);

        while (logBox.childElementCount > MAX_LOGS) {
            logBox.removeChild(logBox.firstElementChild);
        }
        logBox.scrollTop = logBox.scrollHeight;
    }

    document.getElementById('btn-clear-logs').addEventListener('click', function () {
        logBox.innerHTML = '<div class="log-empty">&gt; Logs cleared.</div>';
    });

    /* ---------------- stat rendering ---------------- */

    function setValue(node, text, tone) {
        node.textContent = text;
        node.classList.remove('is-on', 'is-off', 'is-idle', 'is-accent');
        if (tone) {
            node.classList.add(tone);
        }
    }

    function resetStats() {
        acSeconds = 0;
        frameCount = 0;
        lastAcState = null;
        lastOverride = null;
        el.banner.hidden = true;
        el.reason.textContent = 'On or off';
        el.reason.classList.remove('is-override');
        acCard.classList.remove('is-override');
        el.acTime.textContent = '0.0s';
        el.frames.textContent = '0';
        setValue(el.occupancy, '—', 'is-idle');
        setValue(el.acState, '—', 'is-idle');
        setValue(el.temp, '—', 'is-idle');
        setValue(el.confidence, '—', 'is-idle');
        el.tag.textContent = '—';
        el.tempBadge.textContent = 'STANDBY';
        el.meter.style.width = '0';
        probList.innerHTML = '<div class="prob-empty">Awaiting first inference…</div>';
    }

    function renderDistribution(distribution) {
        if (!distribution || !distribution.length) {
            return;
        }

        var top = distribution.reduce(function (a, b) {
            return b.value > a.value ? b : a;
        });

        // Rebuild only when the class set changes, so the bars animate in place.
        var names = distribution.map(function (d) { return d.label; }).join('|');
        if (probList.dataset.names !== names) {
            probList.dataset.names = names;
            probList.innerHTML = '';
            distribution.forEach(function (d) {
                var row = document.createElement('div');
                row.className = 'prob-row';
                row.innerHTML =
                    '<div class="prob-head">' +
                        '<span class="prob-name"></span>' +
                        '<span class="prob-pct"></span>' +
                    '</div>' +
                    '<div class="prob-track"><div class="prob-fill"></div></div>';
                row.querySelector('.prob-name').textContent = d.label;
                probList.appendChild(row);
            });
        }

        var rows = probList.children;
        distribution.forEach(function (d, i) {
            var row = rows[i];
            if (!row) { return; }
            var pct = d.value * 100;
            row.querySelector('.prob-pct').textContent = pct.toFixed(1) + '%';
            row.querySelector('.prob-fill').style.width = pct.toFixed(1) + '%';
            row.classList.toggle('is-top', d.label === top.label);
        });
    }

    function applyPrediction(data) {
        frameCount += 1;
        el.frames.textContent = String(frameCount);

        setValue(el.occupancy, data.occupancy, 'is-accent');

        var on = data.ac_state === 'ON';
        var override = data.override === true;

        setValue(el.acState, data.ac_state, override ? 'is-override' : (on ? 'is-on' : 'is-off'));

        // Servant override: AC is forced off no matter what the band says,
        // so make the reason for that visible rather than silent.
        el.banner.hidden = !override;
        acCard.classList.toggle('is-override', override);
        el.reason.classList.toggle('is-override', override);
        el.reason.textContent = data.reason || (on ? 'On' : 'Off');
        if (override) {
            el.bannerDetail.textContent =
                data.reason + ' — regardless of occupancy band.';
        }

        var temp = data.temp && data.temp !== '--' ? data.temp : '—';
        setValue(el.temp, temp, on ? null : 'is-idle');
        el.tempBadge.textContent = on ? 'SET TO ' + data.temp : 'STANDBY';

        if (typeof data.confidence === 'number') {
            var pct = data.confidence * 100;
            setValue(el.confidence, pct.toFixed(1) + '%', 'is-accent');
            el.meter.style.width = pct.toFixed(1) + '%';
        }
        el.tag.textContent = data.label || '—';

        renderDistribution(data.distribution);

        if (on) {
            acSeconds += SAMPLE_MS / 1000;
        }
        el.acTime.textContent = acSeconds.toFixed(1) + 's';

        var conf = typeof data.confidence === 'number'
            ? ' (' + (data.confidence * 100).toFixed(1) + '%)'
            : '';
        log(
            'Detected ' + data.occupancy + conf +
            ' -> AC switched ' + data.ac_state + ' [' + (data.temp || '--') + ']',
            override ? 'override' : (on ? 'on' : 'off')
        );

        // Only log the override on the transition, not on every frame.
        if (lastOverride !== null && override !== lastOverride) {
            log(
                override
                    ? 'SERVANT OVERRIDE ENGAGED -> AC forced OFF'
                    : 'Servant override released -> normal band policy resumed',
                'override'
            );
        }
        lastOverride = override;

        if (lastAcState !== null && lastAcState !== data.ac_state) {
            setStatus(
                override ? 'Live · servant override' : 'Live · AC ' + data.ac_state,
                'live'
            );
        }
        lastAcState = data.ac_state;
    }

    /* ---------------- inference loop ---------------- */

    function currentSource() {
        if (sourceKind === 'image') {
            return photo.complete && photo.naturalWidth ? photo : null;
        }
        if (sourceKind === 'video') {
            return video.readyState >= 2 ? video : null;
        }
        return null;
    }

    function shouldSample() {
        if (sourceKind === 'image') {
            return true;
        }
        return !video.paused && !video.ended;
    }

    function startLoop() {
        stopLoop();
        timer = setInterval(function () {
            if (!shouldSample()) {
                return;
            }

            var src = currentSource();
            if (!src) {
                return;
            }

            var dim = naturalSize(src);
            if (!dim.w || !dim.h) {
                return;
            }

            // Scale so the shorter side is SEND_SHORTER_SIDE, aspect preserved.
            var scale = Math.min(1, SEND_SHORTER_SIDE / Math.min(dim.w, dim.h));
            canvas.width = Math.max(1, Math.round(dim.w * scale));
            canvas.height = Math.max(1, Math.round(dim.h * scale));

            try {
                ctx.drawImage(src, 0, 0, canvas.width, canvas.height);
            } catch (e) {
                console.error('Canvas draw error:', e);
                return;
            }

            fetch('/predict_frame', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: canvas.toDataURL('image/jpeg', 0.9) })
            })
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    if (data.error) {
                        setStatus('Inference error', 'error');
                        log('Inference error: ' + data.error, 'err');
                        return;
                    }
                    setStatus('Live · sampling every 0.5s', 'live');
                    applyPrediction(data);
                })
                .catch(function (err) {
                    console.error(err);
                    setStatus('Connection lost', 'error');
                    log('Request failed: ' + err.message, 'err');
                });
        }, SAMPLE_MS);
    }

    function stopLoop() {
        if (timer) {
            clearInterval(timer);
            timer = null;
        }
    }

    /* ---------------- media sources ---------------- */

    function stopWebcam() {
        if (stream) {
            stream.getTracks().forEach(function (t) { t.stop(); });
            stream = null;
        }
    }

    function showVideo() {
        sourceKind = 'video';
        stage.classList.add('src-video');
        stage.classList.remove('src-image');
        video.controls = true;
    }

    function showImage() {
        sourceKind = 'image';
        stage.classList.add('src-image');
        stage.classList.remove('src-video');
    }

    function activate(entry) {
        stopWebcam();
        stopLoop();
        resetStats();

        activeSource.textContent = 'Active: ' + entry.name;
        log('Loading source "' + entry.name + '"…', 'info');

        if (entry.kind === 'image') {
            video.removeAttribute('src');
            video.load();
            photo.src = entry.url;
            showImage();
            setStatus('Still image · sampling', 'live');
            photo.onload = startLoop;
        } else {
            photo.removeAttribute('src');
            video.src = entry.url;
            video.muted = true;
            showVideo();
            setStatus('Loading source…', null);
            video.play().catch(function () {
                setStatus('Press play to start', null);
            });
            startLoop();
        }
    }

    function register(entry) {
        loaded.push(entry);
        var opt = document.createElement('option');
        opt.value = String(loaded.length - 1);
        opt.textContent = entry.name;
        loadedSelect.appendChild(opt);
        loadedSelect.value = opt.value;
        return entry;
    }

    function addFiles(files) {
        var first = null;
        Array.prototype.forEach.call(files, function (file) {
            var entry = register({
                name: file.name,
                url: URL.createObjectURL(file),
                kind: file.type.indexOf('image/') === 0 ? 'image' : 'video',
                revocable: true
            });
            if (!first) {
                first = entry;
            }
        });
        if (first) {
            activate(first);
        }
    }

    fileInput.addEventListener('change', function (e) {
        if (e.target.files.length) {
            addFiles(e.target.files);
        }
        fileInput.value = '';
    });

    loadedSelect.addEventListener('change', function () {
        var entry = loaded[Number(loadedSelect.value)];
        if (entry) {
            activate(entry);
        }
    });

    Array.prototype.forEach.call(document.querySelectorAll('.chip[data-sample]'), function (chip) {
        chip.addEventListener('click', function () {
            var name = chip.dataset.name;
            var existing = loaded.filter(function (e) { return e.name === name; })[0];
            activate(existing || register({
                name: name,
                url: chip.dataset.sample,
                kind: 'video',
                revocable: false
            }));
        });
    });

    document.getElementById('btn-webcam').addEventListener('click', function () {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setStatus('Webcam not available in this browser', 'error');
            log('getUserMedia unsupported', 'err');
            return;
        }

        stopLoop();
        resetStats();
        log('Requesting webcam access…', 'info');

        navigator.mediaDevices.getUserMedia({ video: true, audio: false })
            .then(function (s) {
                stopWebcam();
                stream = s;
                video.removeAttribute('src');
                video.srcObject = s;
                video.controls = false;
                showVideo();
                activeSource.textContent = 'Active: Webcam';
                loadedSelect.value = '';
                video.play();
                setStatus('Live · webcam', 'live');
                log('Webcam stream started', 'info');
                startLoop();
            })
            .catch(function (err) {
                setStatus('Webcam denied or unavailable', 'error');
                log('Webcam error: ' + err.message, 'err');
            });
    });

    /* ---------------- video events ---------------- */

    // The browser refuses codecs it cannot decode (HEVC, MPEG-4 Part 2, …)
    // and otherwise fails silently, so surface it on the dashboard.
    video.addEventListener('error', function () {
        if (!video.src) {
            return;
        }
        stage.classList.remove('src-video');
        sourceKind = null;
        stopLoop();
        setStatus('Unsupported video codec — convert to H.264 MP4', 'error');
        log('Decode failed — source is not a browser-supported codec', 'err');
    });

    video.addEventListener('ended', function () {
        setStatus('Source ended', null);
        log('Playback ended after ' + frameCount + ' frames', 'info');
    });

    video.addEventListener('pause', function () {
        if (!video.ended && sourceKind === 'video') {
            setStatus('Paused', null);
        }
    });

    video.addEventListener('play', function () {
        if (sourceKind === 'video') {
            setStatus('Live · sampling every 0.5s', 'live');
        }
    });

    /* ---------------- view controls ---------------- */

    function wireSegment(id, apply) {
        var group = document.getElementById(id);
        group.addEventListener('click', function (e) {
            var btn = e.target.closest('button');
            if (!btn) {
                return;
            }
            Array.prototype.forEach.call(group.children, function (b) {
                b.classList.toggle('is-active', b === btn);
            });
            apply(btn);
        });
    }

    wireSegment('seg-fit', function (btn) {
        stage.classList.remove('fit-contain', 'fit-cover', 'fit-fill');
        stage.classList.add('fit-' + btn.dataset.fit);
        log('Fit mode set to ' + btn.dataset.fit, 'info');
    });

    wireSegment('seg-ratio', function (btn) {
        stage.classList.remove('ratio-16-9', 'ratio-4-3', 'ratio-1-1', 'ratio-auto');
        stage.classList.add('ratio-' + btn.dataset.ratio);
        log('Aspect ratio set to ' + btn.textContent.trim(), 'info');
    });

    var zoom = document.getElementById('zoom');
    var zoomValue = document.getElementById('zoom-value');
    zoom.addEventListener('input', function () {
        var scale = Number(zoom.value) / 100;
        zoomValue.textContent = zoom.value + '%';
        video.style.transform = 'scale(' + scale + ')';
        photo.style.transform = 'scale(' + scale + ')';
    });

    var glowBtn = document.getElementById('btn-glow');
    glowBtn.addEventListener('click', function () {
        var on = stage.classList.toggle('is-glow');
        glowBtn.textContent = on ? 'Glow ON' : 'Glow OFF';
        glowBtn.classList.toggle('btn-primary', on);
        glowBtn.classList.toggle('btn-ghost', !on);
    });

    /* ---------------- drag and drop ---------------- */

    ['dragenter', 'dragover'].forEach(function (name) {
        stage.addEventListener(name, function (e) {
            e.preventDefault();
            stage.classList.add('is-dragover');
        });
    });

    ['dragleave', 'drop'].forEach(function (name) {
        stage.addEventListener(name, function (e) {
            e.preventDefault();
            stage.classList.remove('is-dragover');
        });
    });

    stage.addEventListener('drop', function (e) {
        var files = e.dataTransfer && e.dataTransfer.files;
        if (files && files.length) {
            addFiles(files);
        }
    });

    window.addEventListener('beforeunload', function () {
        stopWebcam();
        loaded.forEach(function (entry) {
            if (entry.revocable) {
                URL.revokeObjectURL(entry.url);
            }
        });
    });
}());

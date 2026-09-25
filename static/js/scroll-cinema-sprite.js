(function () {
    'use strict';

    // Scroll-scrubbed hero animation, driven by individual small frames.
    // The frames used to live in one 9600x4320 sprite sheet, but decoding
    // that on first draw froze the main thread (~166MB of pixels, and wider
    // than many mobile GPUs' 8192px texture limit), which made the site feel
    // laggy for first-time visitors. Now each frame is decoded off the main
    // thread (createImageBitmap / img.decode) and loading only starts once
    // the page is idle or the section is near, so it never competes with the
    // hero image. Until a frame is ready, the nearest loaded frame is drawn.
    var section = document.getElementById('luxScrollCinema');
    if (!section) return;

    var pin = section.querySelector('.lux-scroll-cinema__pin');
    var canvas = section.querySelector('.lux-scroll-cinema__canvas');
    var poster = section.querySelector('.lux-scroll-cinema__poster');
    var loader = section.querySelector('.lux-scroll-cinema__loader');
    var hint = section.querySelector('.lux-scroll-cinema__hint');

    var frameUrls;
    try { frameUrls = JSON.parse(section.dataset.frames || '[]'); } catch (e) { frameUrls = []; }
    var frameCount = frameUrls.length;
    if (!frameCount) return;

    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var ctx = canvas.getContext('2d');
    var ready = false;
    var ticking = false;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var currentFrame = -1;
    var drawnSource = null;
    var frames = new Array(frameCount);
    var loadedCount = 0;
    var loadingStarted = false;
    var canvasW = 0;
    var canvasH = 0;

    function loadFrame(i) {
        return new Promise(function (resolve) {
            var img = new Image();
            img.decoding = 'async';
            img.src = frameUrls[i];
            var done = function (bitmap) {
                frames[i] = bitmap || img;
                loadedCount++;
                onFrameLoaded(i);
                resolve();
            };
            var fail = function () { resolve(); };
            if (window.createImageBitmap) {
                img.onload = function () {
                    createImageBitmap(img).then(done, function () { done(null); });
                };
                img.onerror = fail;
            } else if (img.decode) {
                img.decode().then(function () { done(null); }, fail);
            } else {
                img.onload = function () { done(null); };
                img.onerror = fail;
            }
        });
    }

    // Load order: first frame, then a coarse pass across the whole range
    // (so fast scrolling always has something close), then the gaps.
    function loadOrder() {
        var order = [];
        var seen = {};
        [8, 4, 2, 1].forEach(function (step) {
            for (var i = 0; i < frameCount; i += step) {
                if (!seen[i]) { seen[i] = true; order.push(i); }
            }
        });
        return order;
    }

    function startLoading() {
        if (loadingStarted) return;
        loadingStarted = true;
        var queue = loadOrder();
        var concurrency = 4;
        function next() {
            if (!queue.length) return Promise.resolve();
            return loadFrame(queue.shift()).then(next);
        }
        for (var c = 0; c < concurrency; c++) next();
    }

    function onFrameLoaded(i) {
        if (!ready) {
            ready = true;
            section.classList.add('is-ready');
            if (loader) loader.hidden = true;
        }
        if (ready) {
            if (reducedMotion) {
                var still = nearestLoaded(Math.floor(frameCount * 0.55));
                drawFrame(still, true);
            } else {
                onScroll();
            }
        }
    }

    function nearestLoaded(index) {
        if (frames[index]) return index;
        for (var d = 1; d < frameCount; d++) {
            if (index - d >= 0 && frames[index - d]) return index - d;
            if (index + d < frameCount && frames[index + d]) return index + d;
        }
        return -1;
    }

    function resizeCanvas() {
        canvasW = pin.clientWidth;
        canvasH = pin.clientHeight;
        canvas.width = Math.floor(canvasW * dpr);
        canvas.height = Math.floor(canvasH * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';

        if (ready && currentFrame >= 0) {
            drawFrame(currentFrame, true);
        }
    }

    // How much wider than the screen the frame is drawn on portrait
    // screens (1 = whole frame visible edge to edge).
    var PORTRAIT_ZOOM = 1.15;

    // Cheap blur: shrink the frame into a tiny canvas, then scale it back
    // up with smoothing — far lighter on phones than ctx.filter = 'blur()'.
    var blurCanvas = document.createElement('canvas');
    blurCanvas.width = 32;
    blurCanvas.height = 18;
    var blurCtx = blurCanvas.getContext('2d');

    function drawBackdrop(src, srcW, srcH) {
        blurCtx.drawImage(src, 0, 0, blurCanvas.width, blurCanvas.height);
        var scale = Math.max(canvasW / srcW, canvasH / srcH);
        var w = srcW * scale;
        var h = srcH * scale;
        ctx.drawImage(blurCanvas, (canvasW - w) / 2, (canvasH - h) / 2, w, h);
        ctx.fillStyle = 'rgba(6, 16, 34, 0.55)';
        ctx.fillRect(0, 0, canvasW, canvasH);
    }

    // Soften the frame's top/bottom edges into the blurred backdrop.
    function fadeEdges(y, h) {
        var band = Math.min(48, h * 0.18);
        var edge = 'rgba(6, 16, 34, 0.6)';
        var clear = 'rgba(6, 16, 34, 0)';
        var top = ctx.createLinearGradient(0, y, 0, y + band);
        top.addColorStop(0, edge);
        top.addColorStop(1, clear);
        ctx.fillStyle = top;
        ctx.fillRect(0, y, canvasW, band);
        var bottom = ctx.createLinearGradient(0, y + h - band, 0, y + h);
        bottom.addColorStop(0, clear);
        bottom.addColorStop(1, edge);
        ctx.fillStyle = bottom;
        ctx.fillRect(0, y + h - band, canvasW, band);
    }

    function drawFrame(index, force) {
        if (index < 0) return;
        var src = frames[index];
        if (!src) return;
        if (!force && src === drawnSource) return;

        var srcW = src.naturalWidth || src.width;
        var srcH = src.naturalHeight || src.height;
        var portrait = canvasW < canvasH;

        // Landscape screens: cover-fit. Portrait (phones): cover-fitting a
        // 16:9 frame into a tall screen zoomed in ~4x and cropped most of
        // the shot, so fit the frame to the screen width instead and fill
        // the space above/below with a soft blurred copy of the same frame.
        var scale = portrait
            ? (canvasW * PORTRAIT_ZOOM) / srcW
            : Math.max(canvasW / srcW, canvasH / srcH);
        var drawW = srcW * scale;
        var drawH = srcH * scale;
        var x = (canvasW - drawW) / 2;
        var y = (canvasH - drawH) / 2;

        if (portrait) drawBackdrop(src, srcW, srcH);
        ctx.drawImage(src, x, y, drawW, drawH);
        if (portrait) fadeEdges(y, drawH);
        currentFrame = index;
        drawnSource = src;
        if (poster && poster.style.opacity !== '0') poster.style.opacity = '0';
    }

    function viewportHeight() {
        // window.innerHeight jumps around on mobile as the browser's
        // address bar shows/hides mid-scroll, which made the pin flicker
        // and the frame index jitter. visualViewport.height stays stable
        // through that resize, so prefer it wherever it's available.
        return window.visualViewport ? window.visualViewport.height : window.innerHeight;
    }

    var pinState = '';
    function setPinState(state) {
        if (state === pinState) return;
        pinState = state;
        pin.classList.toggle('is-fixed', state === 'fixed');
        pin.classList.toggle('is-bottom', state === 'bottom');
    }

    var lastHintOpacity = -1;
    function update() {
        ticking = false;
        var rect = section.getBoundingClientRect();
        var vh = viewportHeight();

        if (rect.top > 0) setPinState('');
        else if (rect.bottom >= vh) setPinState('fixed');
        else setPinState('bottom');

        if (!ready) return;

        var scrollRange = rect.height - vh;
        var progress = scrollRange <= 0 ? 0 : Math.max(0, Math.min(1, -rect.top / scrollRange));
        var index = Math.min(frameCount - 1, Math.floor(progress * frameCount));
        drawFrame(nearestLoaded(index), false);

        if (hint) {
            var opacity = Math.max(0, 1 - progress * 4);
            if (opacity !== lastHintOpacity) {
                lastHintOpacity = opacity;
                hint.style.opacity = String(opacity);
            }
        }
    }

    function onScroll() {
        if (!ticking) {
            ticking = true;
            window.requestAnimationFrame(update);
        }
    }

    function onViewportResize() {
        resizeCanvas();
        update();
    }

    // Start fetching frames when the section is about to be seen, or once
    // the browser is idle after load — whichever comes first.
    function scheduleLoading() {
        if ('IntersectionObserver' in window) {
            var io = new IntersectionObserver(function (entries) {
                if (entries.some(function (e) { return e.isIntersecting; })) {
                    io.disconnect();
                    startLoading();
                }
            }, { rootMargin: '600px 0px' });
            io.observe(section);
        }
        var idle = window.requestIdleCallback || function (cb) { return setTimeout(cb, 300); };
        var kick = function () { idle(startLoading, { timeout: 2000 }); };
        if (document.readyState === 'complete') kick();
        else window.addEventListener('load', kick, { once: true });
    }

    function init() {
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas, { passive: true });
        window.addEventListener('orientationchange', resizeCanvas, { passive: true });
        if (window.ResizeObserver) {
            new ResizeObserver(resizeCanvas).observe(pin);
        }

        if (reducedMotion) {
            scheduleLoading();
            return;
        }

        if (window.visualViewport) {
            // Mobile browsers resize the visual viewport (not window) when
            // the address bar shows/hides mid-scroll — without this, the
            // pin height and scroll progress go stale until the next
            // full window resize (orientation change), causing jitter.
            window.visualViewport.addEventListener('resize', onViewportResize, { passive: true });
        }
        window.addEventListener('scroll', onScroll, { passive: true });

        scheduleLoading();
        update();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

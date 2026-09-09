(function () {
    'use strict';

    // Scroll-scrubbed hero animation. Previously loaded 300 individual PNG
    // frames eagerly on page load (~63MB, 300 requests) — every new visitor
    // paid that cost before the section became interactive. Now drives the
    // same canvas draw-cover logic from a single small MP4 (~1.6MB, 1
    // request), seeking video.currentTime to match scroll progress instead
    // of swapping <img> elements.
    var section = document.getElementById('luxScrollCinema');
    if (!section) return;

    var pin = section.querySelector('.lux-scroll-cinema__pin');
    var canvas = section.querySelector('.lux-scroll-cinema__canvas');
    var poster = section.querySelector('.lux-scroll-cinema__poster');
    var loader = section.querySelector('.lux-scroll-cinema__loader');
    var hint = section.querySelector('.lux-scroll-cinema__hint');
    var videoSrc = section.dataset.videoSrc;
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var ctx = canvas.getContext('2d');
    var currentProgress = -1;
    var ready = false;
    var ticking = false;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);

    var video = document.createElement('video');
    video.muted = true;
    video.playsInline = true;
    video.preload = 'auto';
    video.src = videoSrc;

    function resizeCanvas() {
        var width = pin.clientWidth;
        var height = pin.clientHeight;
        canvas.width = Math.floor(width * dpr);
        canvas.height = Math.floor(height * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';

        if (ready && currentProgress >= 0) {
            drawCurrent(currentProgress);
        }
    }

    function drawCover(source, scale) {
        var width = pin.clientWidth;
        var height = pin.clientHeight;
        var iw = source.videoWidth || source.naturalWidth;
        var ih = source.videoHeight || source.naturalHeight;
        if (!iw || !ih) return;

        var coverScale = Math.max(width / iw, height / ih) * scale;
        var drawW = iw * coverScale;
        var drawH = ih * coverScale;
        var x = (width - drawW) / 2;
        var y = (height - drawH) / 2;

        ctx.clearRect(0, 0, width, height);
        ctx.drawImage(source, x, y, drawW, drawH);
    }

    function getProgress() {
        var scrollRange = section.offsetHeight - window.innerHeight;
        if (scrollRange <= 0) return 0;
        var rect = section.getBoundingClientRect();
        return Math.max(0, Math.min(1, -rect.top / scrollRange));
    }

    function drawCurrent(progress) {
        var scale = 1.02 - progress * 0.02;
        drawCover(video, scale);
        currentProgress = progress;
    }

    var pendingProgress = null;
    var seeking = false;

    function seekAndDraw(progress) {
        if (!video.duration) return;
        pendingProgress = progress;
        if (seeking) return; // a seek is already in flight — 'seeked' below will pick up the latest pendingProgress
        seeking = true;
        video.currentTime = progress * video.duration;
    }

    video.addEventListener('seeked', function () {
        // The frame is now actually decoded and ready to draw. If more
        // scroll happened while this seek was in flight, immediately
        // re-seek to the latest requested position instead of drawing a
        // now-stale frame.
        seeking = false;
        if (pendingProgress === null) return;
        var progress = pendingProgress;
        if (Math.abs(video.currentTime - progress * video.duration) > 1 / 30) {
            seeking = true;
            video.currentTime = progress * video.duration;
            return;
        }
        drawCurrent(progress);
    });

    function updatePinState() {
        var rect = section.getBoundingClientRect();

        if (rect.top > 0) {
            pin.classList.remove('is-fixed', 'is-bottom');
        } else if (rect.bottom >= window.innerHeight) {
            pin.classList.remove('is-bottom');
            pin.classList.add('is-fixed');
        } else {
            pin.classList.remove('is-fixed');
            pin.classList.add('is-bottom');
        }
    }

    function update() {
        ticking = false;
        updatePinState();

        if (!ready) return;

        var progress = getProgress();
        seekAndDraw(progress);

        if (hint) {
            hint.style.opacity = String(Math.max(0, 1 - progress * 4));
        }

        if (poster) {
            poster.style.opacity = '0';
        }
    }

    function onScroll() {
        if (!ticking) {
            ticking = true;
            window.requestAnimationFrame(update);
        }
    }

    function init() {
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas, { passive: true });
        window.addEventListener('orientationchange', resizeCanvas, { passive: true });
        if (window.ResizeObserver) {
            new ResizeObserver(resizeCanvas).observe(pin);
        }
        window.addEventListener('scroll', onScroll, { passive: true });

        video.addEventListener('loadedmetadata', function () {
            // iOS Safari can refuse to seek a video that has never played;
            // a muted play()/pause() immediately after metadata loads
            // "warms up" the decoder so currentTime seeks work reliably.
            var warmup = video.play();
            if (warmup && warmup.then) {
                warmup.then(function () { video.pause(); }).catch(function () {});
            } else {
                video.pause();
            }

            ready = true;
            section.classList.add('is-ready');
            if (loader) loader.hidden = true;
            update();
        });

        video.addEventListener('error', function () {
            // If the video fails to load, drop the loader and leave the
            // poster image showing rather than block the page.
            if (loader) loader.hidden = true;
        });

        update();
    }

    if (reducedMotion) {
        video.addEventListener('loadedmetadata', function () {
            video.currentTime = video.duration * 0.55;
        });
        video.addEventListener('seeked', function () {
            ready = true;
            section.classList.add('is-ready');
            if (loader) loader.hidden = true;
            if (poster) poster.style.opacity = '0';
            resizeCanvas();
            drawCurrent(0);
        }, { once: true });
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas, { passive: true });
        return;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

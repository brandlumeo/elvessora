(function () {
    'use strict';

    // Scroll-scrubbed hero animation, driven by a single sprite-sheet image
    // (a grid of frames) instead of a video. No video codec dependency —
    // the sprite loads once and each scroll-driven frame is a synchronous
    // canvas drawImage crop, so there's no seek/decode latency to manage.
    var section = document.getElementById('luxScrollCinema');
    if (!section) return;

    var pin = section.querySelector('.lux-scroll-cinema__pin');
    var canvas = section.querySelector('.lux-scroll-cinema__canvas');
    var poster = section.querySelector('.lux-scroll-cinema__poster');
    var loader = section.querySelector('.lux-scroll-cinema__loader');
    var hint = section.querySelector('.lux-scroll-cinema__hint');

    var spriteSrc = section.dataset.spriteSrc;
    var frameCount = parseInt(section.dataset.frameCount, 10) || 1;
    var cols = parseInt(section.dataset.cols, 10) || 1;
    var cellW = parseInt(section.dataset.cellW, 10) || 1;
    var cellH = parseInt(section.dataset.cellH, 10) || 1;

    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var ctx = canvas.getContext('2d');
    var ready = false;
    var ticking = false;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var currentFrame = -1;

    var sprite = new Image();
    sprite.src = spriteSrc;

    function resizeCanvas() {
        var width = pin.clientWidth;
        var height = pin.clientHeight;
        canvas.width = Math.floor(width * dpr);
        canvas.height = Math.floor(height * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';

        if (ready && currentFrame >= 0) {
            drawFrame(currentFrame, true);
        }
    }

    function drawFrame(index, force) {
        if (!force && index === currentFrame) return;
        var width = pin.clientWidth;
        var height = pin.clientHeight;
        var col = index % cols;
        var row = Math.floor(index / cols);
        var sx = col * cellW;
        var sy = row * cellH;

        var coverScale = Math.max(width / cellW, height / cellH);
        var drawW = cellW * coverScale;
        var drawH = cellH * coverScale;
        var x = (width - drawW) / 2;
        var y = (height - drawH) / 2;

        ctx.clearRect(0, 0, width, height);
        ctx.drawImage(sprite, sx, sy, cellW, cellH, x, y, drawW, drawH);
        currentFrame = index;
    }

    function getProgress() {
        var scrollRange = section.offsetHeight - window.innerHeight;
        if (scrollRange <= 0) return 0;
        var rect = section.getBoundingClientRect();
        return Math.max(0, Math.min(1, -rect.top / scrollRange));
    }

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
        var index = Math.min(frameCount - 1, Math.floor(progress * frameCount));
        drawFrame(index, false);

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

        sprite.addEventListener('load', function () {
            ready = true;
            section.classList.add('is-ready');
            if (loader) loader.hidden = true;
            update();
        });
        sprite.addEventListener('error', function () {
            if (loader) loader.hidden = true;
        });

        update();
    }

    if (reducedMotion) {
        sprite.addEventListener('load', function () {
            ready = true;
            section.classList.add('is-ready');
            if (loader) loader.hidden = true;
            if (poster) poster.style.opacity = '0';
            resizeCanvas();
            drawFrame(Math.floor(frameCount * 0.55), true);
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

(function () {
    'use strict';

    var section = document.getElementById('luxScrollCinema');
    if (!section) return;

    var pin = section.querySelector('.lux-scroll-cinema__pin');
    var canvas = section.querySelector('.lux-scroll-cinema__canvas');
    var poster = section.querySelector('.lux-scroll-cinema__poster');
    var loader = section.querySelector('.lux-scroll-cinema__loader');
    var hint = section.querySelector('.lux-scroll-cinema__hint');
    var frameBase = section.dataset.frameBase;
    var frameCount = parseInt(section.dataset.frameCount, 10) || 105;
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var ctx = canvas.getContext('2d');
    var frames = [];
    var currentFrame = -1;
    var ready = false;
    var ticking = false;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);

    function padFrame(index) {
        return String(index).padStart(3, '0');
    }

    function frameSrc(index) {
        return frameBase + padFrame(index) + '.png';
    }

    function resizeCanvas() {
        var width = pin.clientWidth;
        var height = pin.clientHeight;
        canvas.width = Math.floor(width * dpr);
        canvas.height = Math.floor(height * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        
        if (ready && currentFrame >= 0) {
            drawFrame(currentFrame, getProgress());
        }
    }

    function drawCover(image, scale) {
        var width = pin.clientWidth;
        var height = pin.clientHeight;
        var iw = image.naturalWidth;
        var ih = image.naturalHeight;
        if (!iw || !ih) return;

        var coverScale = Math.max(width / iw, height / ih) * scale;
        // Cap how far "cover" is allowed to zoom past "contain": on narrow/portrait
        // viewports a wide frame (e.g. storefront signage) otherwise gets cropped
        // illegibly on both sides. A small letterbox is preferable to losing edge
        // content — this only kicks in when the container/image aspect ratios are
        // far apart, so frames already close to the container's shape are unaffected.
        var containScale = Math.min(width / iw, height / ih) * scale;
        coverScale = Math.min(coverScale, containScale * 1.35);
        var drawW = iw * coverScale;
        var drawH = ih * coverScale;
        var x = (width - drawW) / 2;
        var y = (height - drawH) / 2;

        ctx.clearRect(0, 0, width, height);
        ctx.drawImage(image, x, y, drawW, drawH);
    }

    function getProgress() {
        var scrollRange = section.offsetHeight - window.innerHeight;
        if (scrollRange <= 0) return 0;
        var rect = section.getBoundingClientRect();
        return Math.max(0, Math.min(1, -rect.top / scrollRange));
    }

    function getFrameIndex(progress) {
        return Math.min(
            frameCount - 1,
            Math.max(0, Math.floor(progress * (frameCount - 1)))
        );
    }

    function drawFrame(index, progress) {
        var image = frames[index];
        if (!image) return;

        var scale = 1.02 - progress * 0.02;
        drawCover(image, scale);
        currentFrame = index;
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
        var frameIndex = getFrameIndex(progress);
        drawFrame(frameIndex, progress);

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

    function setLoaderProgress(value) {
        if (!loader) return;
        loader.style.setProperty('--load', String(Math.round(value * 100)));
        loader.setAttribute('aria-valuenow', String(Math.round(value * 100)));
    }

    function preloadFrames() {
        var loaded = 0;

        return new Promise(function (resolve) {
            for (var i = 0; i < frameCount; i += 1) {
                (function (index) {
                    var image = new Image();
                    image.decoding = 'async';
                    image.onload = function () {
                        loaded += 1;
                        setLoaderProgress(loaded / frameCount);
                        if (loaded === frameCount) {
                            resolve();
                        }
                    };
                    image.onerror = function () {
                        loaded += 1;
                        setLoaderProgress(loaded / frameCount);
                        if (loaded === frameCount) {
                            resolve();
                        }
                    };
                    image.src = frameSrc(index + 1);
                    frames[index] = image;
                })(i);
            }
        });
    }

    function init() {
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas, { passive: true });
        window.addEventListener('orientationchange', resizeCanvas, { passive: true });
        if (window.ResizeObserver) {
            new ResizeObserver(resizeCanvas).observe(pin);
        }
        window.addEventListener('scroll', onScroll, { passive: true });

        preloadFrames().then(function () {
            ready = true;
            section.classList.add('is-ready');
            if (loader) loader.hidden = true;
            update();
        });

        update();
    }

    if (reducedMotion) {
        var still = new Image();
        still.onload = function () {
            frames[0] = still;
            ready = true;
            section.classList.add('is-ready');
            if (loader) loader.hidden = true;
            if (poster) poster.style.opacity = '0';
            drawFrame(0, 0);
        };
        still.src = frameSrc(Math.round(frameCount * 0.55));
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

/**
 * Scroll-driven frame showcase — high-quality smooth playback
 * Frames: static/images/ezgif-frame-001.png … ezgif-frame-050.png
 */
(function () {
    'use strict';

    var root = document.getElementById('lux-scroll-showcase');
    if (!root) return;

    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var frameCount = parseInt(root.dataset.frameCount, 10) || 50;
    var frameBase = root.dataset.frameUrl || '/static/images/ezgif-frame-';

    var track = root.querySelector('.lux-scroll-track');
    var pin = root.querySelector('.lux-scroll-pin');
    var canvas = root.querySelector('.lux-frame-canvas');
    if (!canvas || !track || !pin) return;

    var ctx = canvas.getContext('2d', { alpha: false, desynchronized: true });
    var loader = root.querySelector('.lux-scroll-loader');
    var loaderFill = root.querySelector('.lux-loader-fill');
    var loaderText = root.querySelector('.lux-loader-text em');
    var scrollHint = root.querySelector('.lux-scroll-hint');
    var logo = root.querySelector('.lux-scroll-logo');
    var eyebrow = root.querySelector('.lux-scroll-eyebrow');
    var headlineLines = root.querySelectorAll('.lux-headline-line');
    var tagline = root.querySelector('.lux-scroll-tagline');
    var cta = root.querySelector('.lux-scroll-cta');

    var frames = [];
    var bitmapCache = [];
    var cacheKey = '';
    var progress = 0;
    var ready = false;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var rafPending = false;
    var lastDrawnProgress = -1;

    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';

    function framePath(index) {
        return frameBase + String(index + 1).padStart(3, '0') + '.png';
    }

    function loadImage(index) {
        return new Promise(function (resolve) {
            var img = new Image();
            img.decoding = 'async';
            img.onload = function () { resolve({ index: index, img: img }); };
            img.onerror = function () { resolve({ index: index, img: null }); };
            img.src = framePath(index);
        });
    }

    function updateLoaderProgress(loaded, total) {
        var pct = Math.round((loaded / total) * 100);
        if (loaderFill) loaderFill.style.width = pct + '%';
        if (loaderText) loaderText.textContent = pct + '%';
    }

    function preloadFrames() {
        var loaded = 0;
        var total = frameCount;

        return new Promise(function (resolve) {
            /* Priority: first, last, then every frame */
            var order = [0];
            for (var k = 1; k < frameCount - 1; k++) order.push(k);
            order.push(frameCount - 1);

            var chain = Promise.resolve();
            order.forEach(function (idx) {
                chain = chain.then(function () {
                    return loadImage(idx).then(function (result) {
                        frames[result.index] = result.img;
                        loaded++;
                        updateLoaderProgress(loaded, total);
                    });
                });
            });

            chain.then(function () { resolve(); });
        });
    }

    function coverMetrics(img, w, h) {
        var iw = img.naturalWidth;
        var ih = img.naturalHeight;
        var scale = Math.max(w / iw, h / ih);
        return {
            dw: iw * scale,
            dh: ih * scale,
            dx: (w - iw * scale) / 2,
            dy: (h - ih * scale) / 2
        };
    }

    function drawCoverTo(ctxTarget, img, w, h) {
        if (!img || !img.naturalWidth) return;
        var m = coverMetrics(img, w, h);
        ctxTarget.drawImage(img, m.dx, m.dy, m.dw, m.dh);
    }

    function buildCache(w, h) {
        var key = w + 'x' + h + '@' + dpr;
        if (cacheKey === key && bitmapCache.length === frameCount) return;
        cacheKey = key;
        bitmapCache = [];

        for (var i = 0; i < frameCount; i++) {
            var img = frames[i];
            if (!img) {
                bitmapCache[i] = null;
                continue;
            }
            var off = document.createElement('canvas');
            off.width = Math.floor(w * dpr);
            off.height = Math.floor(h * dpr);
            var octx = off.getContext('2d');
            octx.scale(dpr, dpr);
            octx.imageSmoothingEnabled = true;
            octx.imageSmoothingQuality = 'high';
            drawCoverTo(octx, img, w, h);
            bitmapCache[i] = off;
        }
    }

    function resizeCanvas() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        var rect = pin.getBoundingClientRect();
        canvas.width = Math.floor(rect.width * dpr);
        canvas.height = Math.floor(rect.height * dpr);
        canvas.style.width = rect.width + 'px';
        canvas.style.height = rect.height + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        cacheKey = '';
        if (ready) {
            buildCache(rect.width, rect.height);
            requestDraw(progress);
        }
    }

    function smoothstep(t) {
        return t * t * (3 - 2 * t);
    }

    function drawFrame(p) {
        if (!frames.length) return;
        var w = pin.clientWidth;
        var h = pin.clientHeight;
        if (!w || !h) return;

        if (bitmapCache.length !== frameCount) {
            buildCache(w, h);
        }

        var exact = p * (frameCount - 1);
        var idx = Math.floor(exact);
        var blend = smoothstep(exact - idx);

        var bmpA = bitmapCache[idx] || bitmapCache[0];
        var bmpB = bitmapCache[Math.min(idx + 1, frameCount - 1)] || bmpA;

        if (!bmpA) return;

        ctx.fillStyle = '#081526';
        ctx.fillRect(0, 0, w, h);

        ctx.globalAlpha = 1;
        ctx.drawImage(bmpA, 0, 0, w, h);

        if (blend > 0.004 && bmpB && bmpB !== bmpA) {
            ctx.globalAlpha = blend;
            ctx.drawImage(bmpB, 0, 0, w, h);
        }

        ctx.globalAlpha = 1;
        lastDrawnProgress = p;
    }

    function requestDraw(p) {
        progress = p;
        if (rafPending) return;
        rafPending = true;
        requestAnimationFrame(function () {
            rafPending = false;
            if (Math.abs(progress - lastDrawnProgress) > 0.0001 || lastDrawnProgress < 0) {
                drawFrame(progress);
            }
        });
    }

    function updateOverlay(p) {
        if (!eyebrow) return;

        var headlineIn = clamp((p - 0.06) / 0.14, 0, 1);
        var tagIn = clamp((p - 0.18) / 0.12, 0, 1);
        var ctaIn = clamp((p - 0.78) / 0.12, 0, 1);
        var fadeOut = clamp((p - 0.92) / 0.08, 0, 1);

        setEl(logo, headlineIn * (1 - fadeOut));
        setEl(eyebrow, headlineIn * (1 - fadeOut));
        headlineLines.forEach(function (line, i) {
            var delay = i * 0.12;
            var v = clamp((headlineIn - delay) / (1 - delay), 0, 1);
            setEl(line, v * (1 - fadeOut));
        });
        setEl(tagline, tagIn * (1 - fadeOut * 0.5));
        setEl(cta, ctaIn);

        if (scrollHint) {
            scrollHint.style.opacity = p > 0.04 ? String(Math.max(0, 1 - p * 3.5)) : '1';
        }
    }

    function setEl(el, t) {
        if (!el) return;
        el.style.opacity = String(t);
        el.style.transform = 'translateY(' + ((1 - t) * 20) + 'px)';
    }

    function clamp(v, min, max) {
        return Math.max(min, Math.min(max, v));
    }

    function initScroll() {
        if (reducedMotion) {
            drawFrame(0.5);
            if (loader) loader.classList.add('is-hidden');
            updateOverlay(0.5);
            return;
        }

        function loadScript(src) {
            return new Promise(function (resolve, reject) {
                var s = document.createElement('script');
                s.src = src;
                s.onload = resolve;
                s.onerror = reject;
                document.head.appendChild(s);
            });
        }

        Promise.all([
            loadScript('https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js'),
            loadScript('https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js')
        ]).then(function () {
            gsap.registerPlugin(ScrollTrigger);

            ScrollTrigger.create({
                trigger: track,
                start: 'top top',
                end: 'bottom bottom',
                scrub: 1.4,
                pin: pin,
                anticipatePin: 1,
                invalidateOnRefresh: true,
                onUpdate: function (self) {
                    requestDraw(self.progress);
                    updateOverlay(self.progress);
                }
            });

            window.addEventListener('load', function () {
                ScrollTrigger.refresh();
            });
        }).catch(function () {
            window.addEventListener('scroll', onNativeScroll, { passive: true });
            onNativeScroll();
        });
    }

    function onNativeScroll() {
        var rect = track.getBoundingClientRect();
        var total = track.offsetHeight - window.innerHeight;
        if (total <= 0) return;
        var p = clamp(-rect.top / total, 0, 1);
        requestDraw(p);
        updateOverlay(p);
    }

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas, { passive: true });

    preloadFrames().then(function () {
        ready = true;
        resizeCanvas();
        drawFrame(0);
        if (loader) loader.classList.add('is-hidden');
        initScroll();
    });
})();

(function () {
    'use strict';

    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* --- Intro loader: logo + progress while the animation frames load,
       then the frames play full-screen and fade into the page. Shown once per
       browser session; CSS fades it out on its own if this script never
       runs. --- */
    /* Hero film: held back while the intro plays so it doesn't compete with
       the intro frames for bandwidth */
    function startHeroVideo() {
        var source = document.querySelector('.vx-hero__bg source[data-src]');
        if (!source) return;
        var video = source.parentNode;
        source.src = source.dataset.src;
        source.removeAttribute('data-src');
        video.load();
        var playing = video.play();
        if (playing && playing.catch) playing.catch(function () {});
    }

    var loader = document.getElementById('vxLoader');
    if (!loader) startHeroVideo();
    if (loader) {
        var bar = loader.querySelector('[data-loader-bar]');
        var skip = loader.querySelector('[data-loader-skip]');
        var canvas = loader.querySelector('.vx-loader__film');
        var frameCount = parseInt(loader.dataset.frameCount, 10) || 0;
        var FPS = 20;   // 50 frames: a 2.5s intro
        var closed = false;
        var playing = false;
        var film = window.vxFilm;   // frames already requested by the inline script
        var frames = film ? film.frames : [];

        loader.classList.add('is-scripted');
        document.documentElement.classList.add('vx-loading');

        function close() {
            if (closed) return;
            closed = true;
            loader.classList.add('is-done');
            document.documentElement.classList.remove('vx-loading');
            try { sessionStorage.setItem('vxIntroSeen', '1'); } catch (e) {}
            setTimeout(function () { loader.remove(); }, 900);
            startHeroVideo();
        }

        function setProgress(value) {
            if (bar) bar.style.transform = 'scaleX(' + value / 100 + ')';
        }

        function play() {
            if (playing || closed) return;
            playing = true;
            if (!canvas || !frames[0]) { close(); return; }

            var ctx = canvas.getContext('2d', { alpha: false });
            var last = frames[0];

            function fit() {
                var dpr = Math.min(window.devicePixelRatio || 1, 2);
                canvas.width = Math.round(window.innerWidth * dpr);
                canvas.height = Math.round(window.innerHeight * dpr);
            }
            // Fill the screen, cropping the edges like background-size: cover
            function drawFrame(img) {
                var cw = canvas.width, ch = canvas.height;
                var sc = Math.max(cw / img.naturalWidth, ch / img.naturalHeight);
                var dw = img.naturalWidth * sc, dh = img.naturalHeight * sc;
                ctx.drawImage(img, (cw - dw) / 2, (ch - dh) / 2, dw, dh);
            }
            fit();
            window.addEventListener('resize', function () {
                if (closed) return;
                fit();
                drawFrame(last);
            });

            loader.classList.add('is-playing');
            var start = null;
            function step(now) {
                if (closed) return;
                if (start === null) start = now;
                var i = Math.floor((now - start) / 1000 * FPS);
                if (i >= frameCount) {
                    // Hold the closing frame a moment, then lift away
                    setTimeout(close, 400);
                    return;
                }
                if (frames[i]) last = frames[i];   // skip any frame that failed to load
                drawFrame(last);
                requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
        }

        if (skip) skip.addEventListener('click', close);
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });

        if (reducedMotion || !film || !frameCount) {
            // No animation: show the logo briefly, then go
            setProgress(100);
            setTimeout(close, 700);
        } else {
            // Start once the first half is in, in order; the rest keep loading
            // while it plays (a straggler falls back to the previous frame)
            var head = Math.ceil(frameCount / 2);
            film.onChange = function () {
                var ready = 0;
                while (ready < head && frames[ready]) ready++;
                setProgress(Math.min(100, ready / head * 100));
                if (ready >= head || film.settled === frameCount) play();
            };
            film.onChange();
            // Slow connection: play whatever has arrived rather than keep waiting
            setTimeout(play, 3000);
        }

        // Never leave the loader covering the page: give up if the animation
        // still hasn't started after 8s, and cap the whole intro (animation
        // frames pause in background tabs) at 15s.
        setTimeout(function () { if (!playing) close(); }, 8000);
        setTimeout(close, 15000);
    }

    /* --- Full-screen sections size themselves below the sticky header --- */
    var header = document.querySelector('.site-header');
    function setHeaderVar() {
        if (header) document.documentElement.style.setProperty('--vx-header', header.offsetHeight + 'px');
    }
    setHeaderVar();
    window.addEventListener('resize', setHeaderVar);

    /* --- Smooth in-page links (hero buttons, cinema outro) --- */
    document.querySelectorAll('[data-vx-scroll]').forEach(function (link) {
        link.addEventListener('click', function (e) {
            var target = document.querySelector(link.getAttribute('href'));
            if (!target) return;
            e.preventDefault();
            var offset = header ? header.offsetHeight : 0;
            window.scrollTo({
                top: target.getBoundingClientRect().top + window.scrollY - offset,
                behavior: reducedMotion ? 'auto' : 'smooth'
            });
        });
    });

    /* --- Signature showcase: one fragrance at a time, with arrows, dots,
       swipe and a gentle autoplay. The Notes section follows along. --- */
    var showcase = document.querySelector('[data-vx-showcase]');
    if (showcase) {
        var slides = Array.prototype.slice.call(showcase.querySelectorAll('[data-vx-slide]'));
        var dots = Array.prototype.slice.call(showcase.querySelectorAll('[data-vx-dot]'));
        var notes = document.querySelector('[data-vx-notes]');
        var index = 0;
        var timer = null;
        var AUTOPLAY_MS = 6500;

        function fillList(list, value) {
            if (!list) return;
            list.innerHTML = '';
            // Same separators as products.fragrance_utils.split_notes.
            (value || '').replace(/[·—]/g, ',').split(',').forEach(function (note) {
                note = note.trim();
                if (!note) return;
                var li = document.createElement('li');
                li.textContent = note;
                list.appendChild(li);
            });
        }

        function syncNotes(slide) {
            if (!notes) return;
            var nameEl = notes.querySelector('[data-notes-name]');
            if (nameEl) nameEl.textContent = slide.getAttribute('data-name') || '';
            fillList(notes.querySelector('[data-notes-top]'), slide.getAttribute('data-top'));
            fillList(notes.querySelector('[data-notes-heart]'), slide.getAttribute('data-heart'));
            fillList(notes.querySelector('[data-notes-base]'), slide.getAttribute('data-base'));
        }

        function go(i) {
            if (!slides.length) return;
            slides[index].classList.remove('is-active');
            slides[index].setAttribute('aria-hidden', 'true');
            if (dots[index]) dots[index].classList.remove('is-active');
            index = (i + slides.length) % slides.length;
            slides[index].classList.add('is-active');
            slides[index].removeAttribute('aria-hidden');
            if (dots[index]) dots[index].classList.add('is-active');
            syncNotes(slides[index]);
        }

        function stop() { if (timer) { clearInterval(timer); timer = null; } }
        function start() {
            stop();
            if (reducedMotion || slides.length < 2) return;
            timer = setInterval(function () { go(index + 1); }, AUTOPLAY_MS);
        }

        var prev = showcase.querySelector('[data-vx-prev]');
        var next = showcase.querySelector('[data-vx-next]');
        if (prev) prev.addEventListener('click', function () { go(index - 1); start(); });
        if (next) next.addEventListener('click', function () { go(index + 1); start(); });
        dots.forEach(function (dot, i) {
            dot.addEventListener('click', function () { go(i); start(); });
        });

        showcase.addEventListener('mouseenter', stop);
        showcase.addEventListener('mouseleave', start);
        showcase.addEventListener('focusin', stop);

        var touchX = null;
        showcase.addEventListener('touchstart', function (e) {
            touchX = e.touches[0].clientX;
            stop();
        }, { passive: true });
        showcase.addEventListener('touchend', function (e) {
            if (touchX === null) return;
            var dx = e.changedTouches[0].clientX - touchX;
            touchX = null;
            if (Math.abs(dx) > 45) go(index + (dx < 0 ? 1 : -1));
            start();
        }, { passive: true });

        showcase.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowLeft') { go(index - 1); start(); }
            if (e.key === 'ArrowRight') { go(index + 1); start(); }
        });

        // Only spin through slides while the showcase is actually on screen.
        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) start(); else stop();
                });
            }, { threshold: 0.35 }).observe(showcase);
        } else {
            start();
        }
    }

    /* --- Perfume Finder (homepage): open the full finder on demand --- */
    var finder = document.querySelector('.pf-collapsible');
    if (finder) {
        finder.querySelectorAll('[data-pf-open]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                finder.classList.add('is-open');
                var mode = finder.querySelector('.pf-mode-btn[data-pf-mode="' + btn.getAttribute('data-pf-open') + '"]');
                if (mode) mode.click();
                var tabs = finder.querySelector('.pf-mode-tabs');
                if (tabs) {
                    var offset = header ? header.offsetHeight + 16 : 16;
                    window.scrollTo({
                        top: tabs.getBoundingClientRect().top + window.scrollY - offset,
                        behavior: reducedMotion ? 'auto' : 'smooth'
                    });
                }
            });
        });
        // Links elsewhere (e.g. "Need help choosing?") that jump to the
        // finder should find it open.
        if (location.hash === '#luxPerfumeFinder') finder.classList.add('is-open');
        var helpBtn = finder.querySelector('[data-pf-help]');
        if (helpBtn) helpBtn.addEventListener('click', function () { finder.classList.add('is-open'); });
    }

    /* --- Reading progress: a thin gold line across the top --- */
    var progress = document.createElement('div');
    progress.className = 'vx-progress';
    progress.setAttribute('aria-hidden', 'true');
    document.body.appendChild(progress);
    var progressTicking = false;
    function updateProgress() {
        progressTicking = false;
        var max = document.documentElement.scrollHeight - window.innerHeight;
        progress.style.setProperty('--p', max > 0 ? Math.min(1, window.scrollY / max) : 0);
    }
    window.addEventListener('scroll', function () {
        if (progressTicking) return;
        progressTicking = true;
        requestAnimationFrame(updateProgress);
    }, { passive: true });
    updateProgress();

    var finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

    if (!reducedMotion && finePointer) {
        /* --- Product cards tilt toward the pointer --- */
        document.querySelectorAll('.vx-card').forEach(function (card) {
            card.addEventListener('pointermove', function (e) {
                var r = card.getBoundingClientRect();
                var x = (e.clientX - r.left) / r.width - 0.5;
                var y = (e.clientY - r.top) / r.height - 0.5;
                card.style.transform = 'perspective(900px) rotateX(' + (-y * 6).toFixed(2) + 'deg) rotateY(' + (x * 6).toFixed(2) + 'deg) translateY(-6px)';
            });
            card.addEventListener('pointerleave', function () { card.style.transform = ''; });
        });

        /* --- A few gold sparkles trail the pointer (hero and showcase only) --- */
        var lastSpark = 0;
        var liveSparks = 0;
        document.querySelectorAll('.vx-hero, .vx-showcase').forEach(function (zone) {
            zone.addEventListener('pointermove', function (e) {
                var now = performance.now();
                if (now - lastSpark < 45 || liveSparks > 18) return;
                lastSpark = now;
                var spark = document.createElement('span');
                spark.className = 'vx-trail';
                spark.textContent = '✦';
                spark.style.left = e.clientX + 'px';
                spark.style.top = e.clientY + 'px';
                spark.style.setProperty('--dx', (Math.random() * 30 - 15).toFixed(0) + 'px');
                spark.style.setProperty('--dy', (Math.random() * 24 + 8).toFixed(0) + 'px');
                spark.style.fontSize = (8 + Math.random() * 7).toFixed(0) + 'px';
                document.body.appendChild(spark);
                liveSparks++;
                spark.addEventListener('animationend', function () { spark.remove(); liveSparks--; });
            });
        });
    }

    /* --- Scroll reveals (content stays visible without JS) --- */
    var reveals = document.querySelectorAll('.vx-reveal');
    if (!reducedMotion && 'IntersectionObserver' in window && reveals.length) {
        document.documentElement.classList.add('vx-motion');
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                entry.target.classList.add('is-in');
                io.unobserve(entry.target);
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
        reveals.forEach(function (el) { io.observe(el); });
    }
})();

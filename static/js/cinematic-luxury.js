/**
 * Cinematic Luxury — collection carousel, reveals, CTA
 */
(function () {
    'use strict';

    var root = document.getElementById('cinematicLuxury');
    if (!root) return;

    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ========== REVEAL (Intersection Observer) ========== */
    function initReveals() {
        var els = root.querySelectorAll('.cine-reveal');
        if (!('IntersectionObserver' in window)) {
            els.forEach(function (el) { el.classList.add('is-visible'); });
            return;
        }
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    var delay = parseInt(entry.target.dataset.delay || '0', 10) * 120;
                    setTimeout(function () {
                        entry.target.classList.add('is-visible');
                    }, delay);
                    io.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -30px 0px' });
        els.forEach(function (el) { io.observe(el); });
    }

    /* ========== COLLECTION CAROUSEL ========== */
    function initCarousel() {
        var carousel = root.querySelector('[data-carousel]');
        if (!carousel) return;

        var viewport = carousel.querySelector('.cine-carousel-viewport');
        var track = carousel.querySelector('.cine-carousel-track');
        var items = carousel.querySelectorAll('.cine-carousel-item');
        var prev = carousel.querySelector('.cine-carousel-prev');
        var next = carousel.querySelector('.cine-carousel-next');
        var info = root.querySelector('.cine-carousel-info');
        var nameEl = document.getElementById('cineCarouselName');
        var priceEl = document.getElementById('cineCarouselPrice');
        var linkEl = document.getElementById('cineCarouselLink');
        var active = 0;
        var total = items.length;
        var autoTimer = null;
        var touchStartX = 0;

        if (total === 0 || !viewport || !track) return;

        function slideToCenter(index) {
            var item = items[index];
            if (!item) return;
            var viewportW = viewport.offsetWidth;
            var itemLeft = item.offsetLeft;
            var itemW = item.offsetWidth;
            var offset = (viewportW / 2) - (itemLeft + itemW / 2);
            track.style.transform = 'translateX(' + offset + 'px)';
        }

        function show(index) {
            active = ((index % total) + total) % total;

            items.forEach(function (item, i) {
                item.classList.toggle('is-active', i === active);
            });

            var cur = items[active];
            if (!cur) return;

            if (info) info.classList.add('is-switching');

            requestAnimationFrame(function () {
                requestAnimationFrame(function () {
                    slideToCenter(active);
                });
            });

            setTimeout(function () {
                if (nameEl) nameEl.textContent = cur.dataset.name || '';
                if (priceEl) priceEl.textContent = cur.dataset.price || '';
                if (linkEl && cur.dataset.url) linkEl.href = cur.dataset.url;
                if (info) info.classList.remove('is-switching');
            }, 200);
        }

        function nextSlide() { show(active + 1); }
        function prevSlide() { show(active - 1); }

        if (prev) prev.addEventListener('click', prevSlide);
        if (next) next.addEventListener('click', nextSlide);

        items.forEach(function (item, i) {
            item.addEventListener('click', function () { show(i); });
        });

        viewport.addEventListener('touchstart', function (e) {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });

        viewport.addEventListener('touchend', function (e) {
            var diff = e.changedTouches[0].screenX - touchStartX;
            if (Math.abs(diff) > 40) {
                show(diff > 0 ? active - 1 : active + 1);
            }
        }, { passive: true });

        window.addEventListener('resize', function () {
            slideToCenter(active);
        });

        if (!reducedMotion) {
            autoTimer = setInterval(nextSlide, 4500);
            carousel.addEventListener('mouseenter', function () {
                if (autoTimer) clearInterval(autoTimer);
            });
            carousel.addEventListener('mouseleave', function () {
                autoTimer = setInterval(nextSlide, 4500);
            });
        }

        show(active);
        requestAnimationFrame(function () {
            slideToCenter(active);
        });
    }

    /* ========== CTA GLOW ON SCROLL ========== */
    function initCtaGlow() {
        var section = document.getElementById('cineCTA');
        if (!section || !('IntersectionObserver' in window)) return;

        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                section.classList.toggle('is-glowing', entry.isIntersecting);
            });
        }, { threshold: 0.35 });
        io.observe(section);
    }

    /* ========== BOOT ========== */
    initReveals();
    initCarousel();
    initCtaGlow();
})();

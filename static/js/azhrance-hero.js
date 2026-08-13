(function () {
    'use strict';

    var hero = document.getElementById('azHero');
    if (!hero) return;

    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var slides = hero.querySelectorAll('.az-hero-slide');
    var dots = hero.querySelectorAll('.az-hero-dot');
    var titles = hero.querySelectorAll('.az-hero-title-line');
    var subs = hero.querySelectorAll('.az-hero-sub');
    var current = 0;
    var timer = null;
    var total = slides.length;

    function goTo(index) {
        if (index < 0) index = total - 1;
        if (index >= total) index = 0;
        current = index;

        slides.forEach(function (slide) {
            slide.classList.toggle('is-active', slide.dataset.slide === String(index));
        });
        dots.forEach(function (dot) {
            dot.classList.toggle('is-active', dot.dataset.slide === String(index));
        });
        titles.forEach(function (line) {
            line.classList.toggle('is-active', line.dataset.slide === String(index));
        });
        subs.forEach(function (sub) {
            sub.classList.toggle('is-active', sub.dataset.slide === String(index));
        });
    }

    function startAutoplay() {
        if (reducedMotion || total <= 1) return;
        stopAutoplay();
        timer = setInterval(function () {
            goTo(current + 1);
        }, 5500);
    }

    function stopAutoplay() {
        if (timer) {
            clearInterval(timer);
            timer = null;
        }
    }

    dots.forEach(function (dot) {
        dot.addEventListener('click', function () {
            goTo(parseInt(dot.dataset.slide, 10));
            startAutoplay();
        });
    });

    hero.addEventListener('mouseenter', stopAutoplay);
    hero.addEventListener('mouseleave', startAutoplay);

    var touchStartX = 0;
    hero.addEventListener('touchstart', function (e) {
        touchStartX = e.changedTouches[0].screenX;
        stopAutoplay();
    }, { passive: true });

    hero.addEventListener('touchend', function (e) {
        var diff = e.changedTouches[0].screenX - touchStartX;
        if (Math.abs(diff) > 50) {
            goTo(diff > 0 ? current - 1 : current + 1);
        }
        startAutoplay();
    }, { passive: true });

    goTo(0);
    startAutoplay();
})();

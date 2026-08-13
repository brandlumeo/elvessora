/**
 * Premium hero — single product showcase with GSAP
 */
(function () {
    'use strict';

    var hero = document.getElementById('luxDualHero');
    if (!hero) return;

    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var productImg = hero.querySelector('.lux-hero-product-img');
    var productFrame = hero.querySelector('.lux-hero-product-frame');
    var canvas = hero.querySelector('.lux-hero-particles');
    var spotlight = hero.querySelector('.lux-hero-spotlight');
    var copy = hero.querySelector('.lux-hero-copy');

    var particles = [];
    var ctx = canvas ? canvas.getContext('2d') : null;

    function initParticles() {
        if (!canvas || !ctx) return;
        resizeCanvas();
        for (var i = 0; i < 40; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                r: 0.5 + Math.random() * 1.5,
                vx: (Math.random() - 0.5) * 0.2,
                vy: -0.1 - Math.random() * 0.25,
                a: 0.1 + Math.random() * 0.35
            });
        }
        animateParticles();
        window.addEventListener('resize', resizeCanvas, { passive: true });
    }

    function resizeCanvas() {
        if (!canvas) return;
        var rect = hero.getBoundingClientRect();
        var dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function animateParticles() {
        if (!ctx || !canvas) return;
        var w = hero.clientWidth;
        var h = hero.clientHeight;
        ctx.clearRect(0, 0, w, h);
        particles.forEach(function (p) {
            p.x += p.vx;
            p.y += p.vy;
            if (p.y < 0) { p.y = h; p.x = Math.random() * w; }
            if (p.x < 0 || p.x > w) p.vx *= -1;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255, 255, 255, ' + p.a + ')';
            ctx.fill();
        });
        requestAnimationFrame(animateParticles);
    }

    function runSequence() {
        if (typeof gsap === 'undefined') {
            hero.classList.add('is-static');
            return;
        }

        gsap.set([productFrame, productImg], { opacity: 0 });
        gsap.set(productFrame, { y: 40, scale: 0.94 });
        gsap.set(copy, { opacity: 0, y: 30 });
        gsap.set(spotlight, { opacity: 0, scale: 0.9 });

        var tl = gsap.timeline({ defaults: { ease: 'power4.out' } });

        tl.to(spotlight, { opacity: 1, scale: 1, duration: 1.6 }, 0)
          .to(copy, { opacity: 1, y: 0, duration: 1.1 }, 0.25)
          .to(productFrame, { opacity: 1, y: 0, scale: 1, duration: 1.4 }, 0.35)
          .to(productImg, { opacity: 1, duration: 1.2 }, 0.45);

        tl.add(function () {
            gsap.to(productFrame, {
                y: -12,
                duration: 3.6,
                ease: 'sine.inOut',
                yoyo: true,
                repeat: -1
            });
        }, 1.6);
    }

    function boot() {
        initParticles();

        if (reducedMotion) {
            hero.classList.add('is-static');
            if (copy) copy.style.opacity = '1';
            if (spotlight) spotlight.style.opacity = '1';
            if (productFrame) productFrame.style.opacity = '1';
            if (productImg) productImg.style.opacity = '1';
            return;
        }

        var script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js';
        script.onload = runSequence;
        script.onerror = function () { hero.classList.add('is-static'); };
        document.head.appendChild(script);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();

(function () {
    'use strict';

    var home = document.getElementById('luxHome');
    var collectionPage = document.getElementById('luxCollectionPage');
    var pageRoot = home || collectionPage;
    if (!pageRoot) return;

    if (home) {
        document.body.classList.add('page-luxury-home');
    }

    /* --- Solid nav after scrolling past the hero-like sections --- */
    var header = document.querySelector('.site-header');
    // The homepage stacks several hero-like sections (Signature banner,
    // scroll cinema, hero) before real content — use whichever is the
    // last one in the DOM as the "past the hero" boundary, and check its
    // actual scroll position (not just its own height) so the nav goes
    // solid only once that whole stack has scrolled by, regardless of
    // how much is stacked above it.
    var hero = document.getElementById('luxHero')
        || document.getElementById('luxSignatureBanner')
        || document.getElementById('luxCollectionHero');

    function updateNav() {
        if (!hero) return;
        var rect = hero.getBoundingClientRect();
        document.body.classList.toggle('is-nav-solid', rect.bottom < window.innerHeight * 0.65);
    }

    // All scroll-driven UI updates run at most once per animation frame,
    // instead of forcing layout on every raw scroll event.
    var scrollTasks = [updateNav];
    var scrollTicking = false;
    window.addEventListener('scroll', function () {
        if (scrollTicking) return;
        scrollTicking = true;
        window.requestAnimationFrame(function () {
            scrollTicking = false;
            scrollTasks.forEach(function (fn) { fn(); });
        });
    }, { passive: true });
    updateNav();

    /* --- Section scroll rail --- */
    var railLinks = document.querySelectorAll('.lux-scroll-rail a');
    var sectionIds = home
        ? ['luxCollection', 'luxPerfumeFinder', 'luxSpotlight']
        : ['luxCollection', 'luxCompare', 'luxGifts'];
    var sections = sectionIds.map(function (id) {
        return document.getElementById(id);
    }).filter(Boolean);

    railLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
            var href = link.getAttribute('href');
            if (!href || href.charAt(0) !== '#') return;
            var target = document.querySelector(href);
            if (!target) return;
            e.preventDefault();
            var offset = (header ? header.offsetHeight : 0) + 48;
            var top = target.getBoundingClientRect().top + window.scrollY - offset;
            window.scrollTo({ top: top, behavior: 'smooth' });
        });
    });

    var navLinks = document.querySelectorAll('.nav-menu--flat [data-nav-section], .nav-menu--home [data-nav-section]');
    var lastRailIdx = -1;

    function updateRail() {
        var scrollMid = window.scrollY + window.innerHeight * 0.4;
        var activeIdx = 0;
        sections.forEach(function (section, i) {
            if (section.offsetTop <= scrollMid) activeIdx = i;
        });
        if (activeIdx === lastRailIdx) return;
        lastRailIdx = activeIdx;

        railLinks.forEach(function (link, i) {
            link.classList.toggle('is-active', i === activeIdx);
        });

        if (navLinks.length && sections[activeIdx]) {
            var activeId = sections[activeIdx].id;
            navLinks.forEach(function (link) {
                link.classList.toggle('is-active', link.getAttribute('data-nav-section') === activeId);
            });
        }
    }

    document.querySelectorAll('.nav-menu--flat [data-nav-section], .nav-menu--home [data-nav-section]').forEach(function (link) {
        link.addEventListener('click', function (e) {
            var sectionId = link.getAttribute('data-nav-section');
            var target = document.getElementById(sectionId);
            if (!target) return;
            e.preventDefault();
            var offset = (header ? header.offsetHeight : 0) + 16;
            var top = target.getBoundingClientRect().top + window.scrollY - offset;
            window.scrollTo({ top: top, behavior: 'smooth' });
        });
    });

    scrollTasks.push(updateRail);
    updateRail();

    /* --- Collection carousel ---
       Native horizontal scroll-snap instead of a JS transform slider: the
       track itself is the scroll container, so touch swipe always works
       (no custom touch math to get wrong), and the arrows just nudge the
       scroll position by one card width. */
    var slider = document.querySelector('[data-lux-collection]');
    if (slider) {
        var wrap = slider.querySelector('.lux-collection-track-wrap');
        var track = slider.querySelector('.lux-collection-track');
        var prevBtn = slider.querySelector('.lux-slider-prev');
        var nextBtn = slider.querySelector('.lux-slider-next');
        var cards = track ? track.querySelectorAll('.lux-product-card') : [];
        var autoplayTimer;

        function cardStep() {
            if (!cards.length) return 0;
            var gap = parseFloat(getComputedStyle(track).gap) || 20;
            return cards[0].offsetWidth + gap;
        }

        function next() {
            if (!wrap) return;
            var atEnd = wrap.scrollLeft + wrap.clientWidth >= wrap.scrollWidth - 4;
            wrap.scrollTo({ left: atEnd ? 0 : wrap.scrollLeft + cardStep(), behavior: 'smooth' });
        }

        function prev() {
            if (!wrap) return;
            wrap.scrollBy({ left: -cardStep(), behavior: 'smooth' });
        }

        if (prevBtn) prevBtn.addEventListener('click', prev);
        if (nextBtn) nextBtn.addEventListener('click', next);

        function startAutoplay() {
            stopAutoplay();
            autoplayTimer = setInterval(next, 5000);
        }

        function stopAutoplay() {
            if (autoplayTimer) clearInterval(autoplayTimer);
        }

        slider.addEventListener('mouseenter', stopAutoplay);
        slider.addEventListener('mouseleave', startAutoplay);
        if (wrap) {
            wrap.addEventListener('touchstart', stopAutoplay, { passive: true });
            wrap.addEventListener('touchend', startAutoplay, { passive: true });
        }

        startAutoplay();
    }

    /* --- Scroll reveal (optional — content visible without JS) --- */
    document.body.classList.add('lux-animate-ready');

    var revealEls = document.querySelectorAll(
        '#luxHome .lux-reveal, #luxCollectionPage .lux-reveal, .lux-excellence .lux-reveal, .lux-spotlight .lux-reveal, .lux-story .lux-reveal, .lux-value-item, .lux-ingredient-item'
    );

    /* Homepage/collection: show all sections immediately */
    if (document.body.classList.contains('page-luxury-home') || document.body.classList.contains('page-collection')) {
        revealEls.forEach(function (el) { el.classList.add('is-visible'); });
    }

    function revealInView() {
        revealEls.forEach(function (el) {
            var rect = el.getBoundingClientRect();
            if (rect.top < window.innerHeight * 0.92) {
                el.classList.add('is-visible');
            }
        });
    }

    if ('IntersectionObserver' in window && revealEls.length) {
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -20px 0px' });

        revealEls.forEach(function (el) { observer.observe(el); });
    } else {
        revealEls.forEach(function (el) { el.classList.add('is-visible'); });
    }

    // The IntersectionObserver above handles reveals while scrolling; this
    // one-off pass just catches anything already on screen at load.
    revealInView();

    /* --- Best Seller thumbnail switcher --- */
    var spotlightPanel = document.querySelector('[data-spotlight-panel]');
    if (spotlightPanel) {
        var heroImg = spotlightPanel.querySelector('[data-spotlight-image]');
        var nameEl = spotlightPanel.querySelector('[data-spotlight-name]');
        var descEl = spotlightPanel.querySelector('[data-spotlight-desc]');
        var priceEl = spotlightPanel.querySelector('[data-spotlight-price]');
        var linkEl = spotlightPanel.querySelector('[data-spotlight-link]');
        var topEl = spotlightPanel.querySelector('[data-spotlight-top]');
        var heartEl = spotlightPanel.querySelector('[data-spotlight-heart]');
        var baseEl = spotlightPanel.querySelector('[data-spotlight-base]');
        var thumbs = spotlightPanel.querySelectorAll('[data-spotlight-thumb]');

        function selectSpotlight(thumb) {
            thumbs.forEach(function (t) {
                t.classList.remove('is-active');
                t.setAttribute('aria-selected', 'false');
            });
            thumb.classList.add('is-active');
            thumb.setAttribute('aria-selected', 'true');

            var imgSrc = thumb.getAttribute('data-image');
            var name = thumb.getAttribute('data-name');

            if (heroImg && imgSrc) {
                heroImg.classList.add('is-swapping');
                heroImg.onload = function () {
                    heroImg.classList.remove('is-swapping');
                };
                heroImg.src = imgSrc;
                heroImg.alt = name || '';
            }
            if (nameEl) nameEl.textContent = name || '';
            if (descEl) descEl.textContent = thumb.getAttribute('data-desc') || '';
            if (priceEl) priceEl.textContent = thumb.getAttribute('data-price') || '';
            if (linkEl) linkEl.href = thumb.getAttribute('data-url') || '#';
            if (topEl) topEl.textContent = thumb.getAttribute('data-top') || '';
            if (heartEl) heartEl.textContent = thumb.getAttribute('data-heart') || '';
            if (baseEl) baseEl.textContent = thumb.getAttribute('data-base') || '';
        }

        thumbs.forEach(function (thumb) {
            thumb.addEventListener('click', function () {
                selectSpotlight(thumb);
            });
        });
    }

    /* --- Hero carousel --- */
    var heroCarousel = document.querySelector('[data-hero-carousel]');
    if (heroCarousel) {
        var heroSlides = Array.prototype.slice.call(heroCarousel.querySelectorAll('[data-hero-slide]'));
        var heroPagination = heroCarousel.querySelector('[data-hero-pagination]');
        var heroIndex = 0;
        var heroTimer = null;
        var HERO_INTERVAL_MS = 3000;

        if (heroSlides.length > 1) {
            heroSlides.forEach(function (slide, i) {
                if (!heroPagination) return;
                var btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'lux-hero-pagination-item';
                btn.setAttribute('aria-label', 'Go to slide ' + (i + 1));
                btn.textContent = (i + 1 < 10 ? '0' : '') + (i + 1);
                btn.addEventListener('click', function () {
                    goToHeroSlide(i);
                    restartHeroAutoplay();
                });
                heroPagination.appendChild(btn);
            });

            function goToHeroSlide(i) {
                heroSlides[heroIndex].classList.remove('is-active');
                heroIndex = (i + heroSlides.length) % heroSlides.length;
                heroSlides[heroIndex].classList.add('is-active');
                if (heroPagination) {
                    heroPagination.querySelectorAll('.lux-hero-pagination-item').forEach(function (btn, idx) {
                        btn.classList.toggle('is-active', idx === heroIndex);
                    });
                }
            }

            function restartHeroAutoplay() {
                if (heroTimer) clearInterval(heroTimer);
                heroTimer = setInterval(function () { goToHeroSlide(heroIndex + 1); }, HERO_INTERVAL_MS);
            }

            goToHeroSlide(0);
            restartHeroAutoplay();
        }
    }
})();

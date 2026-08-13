document.addEventListener('DOMContentLoaded', function() {
    // Promo popup
    const promoModal = document.getElementById('promoModal');
    if (promoModal && !sessionStorage.getItem('promoShown')) {
        new bootstrap.Modal(promoModal).show();
        sessionStorage.setItem('promoShown', 'true');
    }

    // Share button
    document.querySelectorAll('[data-share]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (navigator.share) {
                navigator.share({ title: document.title, url: window.location.href });
            } else {
                navigator.clipboard.writeText(window.location.href);
                alert('Link copied to clipboard!');
            }
        });
    });

    // Navbar scroll effect (cinematic homepage uses cinematic-luxury.js)
    const nav = document.querySelector('.luxury-nav');
    if (nav && !document.body.classList.contains('page-cinematic') && !document.body.classList.contains('page-luxury-home')) {
        window.addEventListener('scroll', function() {
            nav.classList.toggle('scrolled', window.scrollY > 40);
        }, { passive: true });
    }

    // Fade-up on scroll
    const fadeEls = document.querySelectorAll('.fade-up');
    if (fadeEls.length && 'IntersectionObserver' in window) {
        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });
        fadeEls.forEach(function(el) { observer.observe(el); });
    } else {
        fadeEls.forEach(function(el) { el.classList.add('visible'); });
    }

    // Mobile filter toggle (shop page)
    const filterBtn = document.getElementById('filterToggle');
    const filterSidebar = document.getElementById('filterSidebar');
    if (filterBtn && filterSidebar) {
        filterBtn.addEventListener('click', function() {
            filterSidebar.classList.toggle('show');
            filterBtn.textContent = filterSidebar.classList.contains('show') ? 'Hide Filters' : 'Show Filters';
        });
    }

    // Auto-dismiss action toasts
    document.querySelectorAll('.elv-toast').forEach(function(toast) {
        var closeBtn = toast.querySelector('[data-elv-toast-close]');
        function dismiss() {
            toast.classList.add('is-hiding');
            window.setTimeout(function() {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
            }, 260);
        }
        if (closeBtn) closeBtn.addEventListener('click', dismiss);
        window.setTimeout(dismiss, 6500);
    });

    // Scroll to top
    var scrollTopBtn = document.getElementById('scrollTopBtn');
    if (scrollTopBtn) {
        var toggleScrollTop = function() {
            if (window.scrollY > 320) {
                scrollTopBtn.classList.add('is-visible');
            } else {
                scrollTopBtn.classList.remove('is-visible');
            }
        };
        window.addEventListener('scroll', toggleScrollTop, { passive: true });
        toggleScrollTop();
        scrollTopBtn.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // Navbar search panel
    var searchToggle = document.getElementById('navSearchToggle');
    var searchPanel = document.getElementById('navSearchPanel');
    var searchInput = document.getElementById('navSearchInput');
    var searchClose = document.getElementById('navSearchClose');

    function openSearch() {
        if (!searchPanel || !searchToggle) return;
        searchPanel.hidden = false;
        searchPanel.classList.add('is-open');
        searchToggle.setAttribute('aria-expanded', 'true');
        searchToggle.classList.add('is-active');
        window.setTimeout(function() {
            if (searchInput) searchInput.focus();
        }, 40);
    }

    function closeSearch() {
        if (!searchPanel || !searchToggle) return;
        searchPanel.classList.remove('is-open');
        searchToggle.setAttribute('aria-expanded', 'false');
        searchToggle.classList.remove('is-active');
        window.setTimeout(function() {
            if (!searchPanel.classList.contains('is-open')) {
                searchPanel.hidden = true;
            }
        }, 180);
    }

    if (searchToggle && searchPanel) {
        searchToggle.addEventListener('click', function(e) {
            e.preventDefault();
            if (searchPanel.classList.contains('is-open')) {
                closeSearch();
            } else {
                openSearch();
            }
        });
        if (searchClose) searchClose.addEventListener('click', closeSearch);
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && searchPanel.classList.contains('is-open')) {
                closeSearch();
            }
        });
        document.addEventListener('click', function(e) {
            if (!searchPanel.classList.contains('is-open')) return;
            if (searchPanel.contains(e.target) || searchToggle.contains(e.target)) return;
            closeSearch();
        });
    }
});

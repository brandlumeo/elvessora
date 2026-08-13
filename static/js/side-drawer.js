(function () {
    'use strict';

    function byId(id) {
        return document.getElementById(id);
    }

    function initDrawer() {
        var drawer = byId('sideDrawer');
        var backdrop = byId('sideDrawerBackdrop');
        if (!drawer || !backdrop) return;

        var titleCart = drawer.querySelector('[data-drawer-title-cart]');
        var titleWishlist = drawer.querySelector('[data-drawer-title-wishlist]');
        var panelCart = drawer.querySelector('[data-panel="cart"]');
        var panelWishlist = drawer.querySelector('[data-panel="wishlist"]');
        var footerCart = drawer.querySelector('[data-footer="cart"]');
        var footerWishlist = drawer.querySelector('[data-footer="wishlist"]');
        var isOpen = false;

        function setMode(mode) {
            mode = mode === 'wishlist' ? 'wishlist' : 'cart';
            drawer.setAttribute('data-mode', mode);
            var isWishlist = mode === 'wishlist';
            if (titleCart) titleCart.hidden = isWishlist;
            if (titleWishlist) titleWishlist.hidden = !isWishlist;
            if (panelCart) panelCart.hidden = isWishlist;
            if (panelWishlist) panelWishlist.hidden = !isWishlist;
            if (footerCart) footerCart.hidden = isWishlist;
            if (footerWishlist) footerWishlist.hidden = !isWishlist;
        }

        function openDrawer(mode) {
            setMode(mode || 'cart');
            backdrop.hidden = false;
            backdrop.removeAttribute('hidden');
            requestAnimationFrame(function () {
                backdrop.classList.add('is-open');
                drawer.classList.add('is-open');
                drawer.setAttribute('aria-hidden', 'false');
                document.body.classList.add('side-drawer-open');
                isOpen = true;
            });
        }

        function closeDrawer(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            if (!isOpen && !drawer.classList.contains('is-open')) return;
            backdrop.classList.remove('is-open');
            drawer.classList.remove('is-open');
            drawer.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('side-drawer-open');
            isOpen = false;
            window.setTimeout(function () {
                if (!drawer.classList.contains('is-open')) {
                    backdrop.hidden = true;
                    backdrop.setAttribute('hidden', '');
                }
            }, 320);
        }

        window.ElvessoraDrawer = {
            open: openDrawer,
            close: closeDrawer,
            isOpen: function () { return isOpen; },
        };

        // Close controls (button, backdrop, Escape)
        drawer.addEventListener('click', function (e) {
            var btn = e.target.closest('[data-drawer-close], #sideDrawerClose');
            if (btn) closeDrawer(e);
        });
        backdrop.addEventListener('click', closeDrawer);
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeDrawer(e);
        });

        // Nav heart / bag open drawer
        document.addEventListener('click', function (e) {
            var trigger = e.target.closest('[data-open-drawer]');
            if (!trigger) return;
            e.preventDefault();
            e.stopPropagation();
            openDrawer(trigger.getAttribute('data-open-drawer') || 'cart');
        });

        // Auto-open after add to cart / wishlist
        var autoMode = document.body.getAttribute('data-open-drawer');
        if (autoMode === 'cart' || autoMode === 'wishlist') {
            openDrawer(autoMode);
            // Prevent reopen loops from bfcache
            document.body.removeAttribute('data-open-drawer');
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDrawer);
    } else {
        initDrawer();
    }
})();

(function () {
    'use strict';

    var root = document.getElementById('favoritesPicker');
    if (!root) return;

    var hotspots = root.querySelectorAll('.fav-hotspot');
    var slots = root.querySelectorAll('.fav-bottle-slot');
    var dots = root.querySelectorAll('.fav-dot');
    var prevBtn = root.querySelector('.fav-nav-prev');
    var nextBtn = root.querySelector('.fav-nav-next');
    var card = document.getElementById('favProductCard');
    var cardThumb = document.getElementById('favCardThumb');
    var cardName = document.getElementById('favCardName');
    var cardPrice = document.getElementById('favCardPrice');
    var cardRegular = document.getElementById('favCardRegular');

    var total = hotspots.length;
    var current = 0;
    var touchStartX = 0;
    var switching = false;

    function getData(index) {
        var btn = root.querySelector('.fav-hotspot[data-index="' + index + '"]');
        return btn ? btn.dataset : null;
    }

    function activate(index) {
        if (index < 0) index = total - 1;
        if (index >= total) index = 0;
        if (switching && index === current) return;

        current = index;
        switching = true;

        hotspots.forEach(function (btn) {
            btn.classList.toggle('is-active', btn.dataset.index === String(index));
        });

        slots.forEach(function (slot, i) {
            slot.classList.toggle('is-highlighted', i === index);
        });

        dots.forEach(function (dot) {
            dot.classList.toggle('is-active', dot.dataset.index === String(index));
        });

        var data = getData(index);
        if (!data || !card) {
            switching = false;
            return;
        }

        card.classList.add('is-switching');

        setTimeout(function () {
            if (cardThumb) {
                cardThumb.src = data.image;
                cardThumb.alt = data.name;
            }
            if (cardName) cardName.textContent = data.short || data.name;
            if (cardPrice) cardPrice.textContent = data.price;
            if (cardRegular) cardRegular.textContent = data.regular || '';
            card.href = data.url;

            card.classList.remove('is-switching');
            switching = false;
        }, 200);
    }

    hotspots.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            activate(parseInt(btn.dataset.index, 10));
        });
    });

    slots.forEach(function (slot, i) {
        slot.addEventListener('click', function () {
            activate(i);
        });
    });

    dots.forEach(function (dot) {
        dot.addEventListener('click', function () {
            activate(parseInt(dot.dataset.index, 10));
        });
    });

    if (prevBtn) prevBtn.addEventListener('click', function () { activate(current - 1); });
    if (nextBtn) nextBtn.addEventListener('click', function () { activate(current + 1); });

    root.addEventListener('touchstart', function (e) {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    root.addEventListener('touchend', function (e) {
        var diff = e.changedTouches[0].screenX - touchStartX;
        if (Math.abs(diff) > 50) {
            activate(diff > 0 ? current - 1 : current + 1);
        }
    }, { passive: true });

    activate(0);
})();

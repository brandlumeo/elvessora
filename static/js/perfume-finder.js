(function () {
    'use strict';

    var root = document.querySelector('[data-perfume-finder]');
    if (!root) return;

    var catalogEl = document.getElementById('pf-catalog-data');
    if (!catalogEl) return;

    var catalog = JSON.parse(catalogEl.textContent);
    var compareList = [];
    var quizAnswers = {};
    var quizStep = 0;
    var quizTotal = 7;

    var filters = {
        gender: 'unisex',
        occasions: [],
        seasons: ['all'],
        scent_families: [],
        intensity: 'moderate',
        budget_max: 1000,
    };

    /* --- Mode switching --- */
    root.querySelectorAll('[data-pf-mode]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var mode = btn.getAttribute('data-pf-mode');
            root.querySelectorAll('[data-pf-mode]').forEach(function (b) {
                b.classList.toggle('is-active', b === btn);
                b.setAttribute('aria-selected', b === btn ? 'true' : 'false');
            });
            root.querySelectorAll('[data-pf-panel]').forEach(function (panel) {
                panel.classList.toggle('is-active', panel.getAttribute('data-pf-panel') === mode);
            });
            if (mode === 'quiz') resetQuiz();
        });
    });

    /* --- Quick filter chips --- */
    root.querySelectorAll('[data-filter]').forEach(function (group) {
        var key = group.getAttribute('data-filter');
        var multi = group.getAttribute('data-multi') === 'true';

        if (key === 'budget_max') {
            var slider = group;
            var display = root.querySelector('[data-budget-display]');
            slider.addEventListener('input', function () {
                filters.budget_max = parseInt(slider.value, 10);
                if (display) {
                    display.textContent = filters.budget_max >= 1000
                        ? 'AED 100 – 1,000+'
                        : 'AED 100 – ' + filters.budget_max.toLocaleString();
                }
            });
            return;
        }

        group.querySelectorAll('.pf-chip').forEach(function (chip) {
            chip.addEventListener('click', function () {
                var val = chip.getAttribute('data-value');
                if (multi) {
                    if (val === 'all' && key === 'seasons') {
                        group.querySelectorAll('.pf-chip').forEach(function (c) { c.classList.remove('is-active'); });
                        chip.classList.add('is-active');
                        filters[key] = ['all'];
                        return;
                    }
                    if (key === 'seasons') {
                        group.querySelector('[data-value="all"]').classList.remove('is-active');
                        filters[key] = filters[key].filter(function (v) { return v !== 'all'; });
                    }
                    chip.classList.toggle('is-active');
                    if (chip.classList.contains('is-active')) {
                        if (filters[key].indexOf(val) === -1) filters[key].push(val);
                    } else {
                        filters[key] = filters[key].filter(function (v) { return v !== val; });
                    }
                } else {
                    group.querySelectorAll('.pf-chip').forEach(function (c) { c.classList.remove('is-active'); });
                    chip.classList.add('is-active');
                    filters[key] = val;
                }
            });
        });
    });

    /* --- Scoring --- */
    function intensityMatch(a, b) {
        if (a === b) return 1;
        var order = ['light', 'moderate', 'strong', 'long-lasting'];
        var ai = order.indexOf(a);
        var bi = order.indexOf(b);
        if (ai === -1 || bi === -1) return 0.5;
        return Math.abs(ai - bi) <= 1 ? 0.7 : 0.2;
    }

    function genderMatch(productGender, filterGender) {
        if (filterGender === 'unisex') return 1;
        if (productGender === 'unisex') return 0.85;
        return productGender === filterGender ? 1 : 0.15;
    }

    function overlapScore(selected, productVals) {
        if (!selected || !selected.length) return 0.6;
        var hits = selected.filter(function (v) {
            return productVals.indexOf(v) !== -1 || (v === 'all' && productVals.indexOf('all') !== -1);
        });
        if (hits.length) return Math.min(1, hits.length / selected.length);
        if (selected.indexOf('all') !== -1) return 0.8;
        return 0;
    }

    function scoreProduct(product, criteria) {
        var weights = {
            gender: 15,
            occasion: 20,
            season: 12,
            scent: 18,
            intensity: 12,
            budget: 13,
            notes: 10,
        };
        var total = 0;
        var max = 0;
        var reasons = [];

        max += weights.gender;
        var gScore = genderMatch(product.gender, criteria.gender || 'unisex');
        total += gScore * weights.gender;
        if (gScore > 0.7 && product.match_reasons && product.match_reasons.gender) {
            reasons.push(product.match_reasons.gender);
        }

        max += weights.occasion;
        var occSelected = criteria.occasions && criteria.occasions.length
            ? criteria.occasions
            : (criteria.occasion ? [criteria.occasion] : []);
        var oScore = overlapScore(occSelected, product.occasions);
        total += oScore * weights.occasion;
        if (oScore > 0.5 && product.match_reasons && product.match_reasons.occasion) {
            reasons.push(product.match_reasons.occasion);
        }

        max += weights.season;
        var sSelected = criteria.seasons && criteria.seasons.length
            ? criteria.seasons
            : (criteria.season ? [criteria.season] : ['all']);
        var sScore = overlapScore(sSelected, product.seasons);
        total += sScore * weights.season;
        if (sScore > 0.5 && product.match_reasons && product.match_reasons.season) {
            reasons.push(product.match_reasons.season);
        }

        max += weights.scent;
        var fSelected = criteria.scent_families && criteria.scent_families.length
            ? criteria.scent_families
            : (criteria.scent_family ? [criteria.scent_family] : []);
        var fScore = overlapScore(fSelected, product.scent_families);
        total += fScore * weights.scent;
        if (fScore > 0.5 && product.match_reasons && product.match_reasons.scent) {
            reasons.push(product.match_reasons.scent);
        }

        max += weights.intensity;
        var iScore = criteria.intensity
            ? intensityMatch(product.intensity, criteria.intensity)
            : 0.6;
        total += iScore * weights.intensity;
        if (iScore > 0.6 && product.match_reasons && product.match_reasons.intensity) {
            reasons.push(product.match_reasons.intensity);
        }

        max += weights.budget;
        var budgetMax = criteria.budget_max || 1000;
        var bScore = product.price <= budgetMax ? 1 : (product.price <= budgetMax * 1.15 ? 0.4 : 0);
        total += bScore * weights.budget;
        if (bScore > 0.7 && product.match_reasons && product.match_reasons.budget) {
            reasons.push(product.match_reasons.budget);
        }

        if (criteria.notes) {
            max += weights.notes;
            var notesLower = (product.notes || '').toLowerCase();
            var noteHits = criteria.notes.toLowerCase().split(/[,\s]+/).filter(Boolean).filter(function (n) {
                return notesLower.indexOf(n) !== -1;
            });
            var nScore = noteHits.length ? Math.min(1, noteHits.length / 2) : 0.3;
            total += nScore * weights.notes;
            if (noteHits.length) reasons.push('Features notes you love: ' + noteHits.join(', ') + '.');
        }

        if (!reasons.length && product.match_reasons && product.match_reasons.default) {
            reasons.push(product.match_reasons.default);
        }
        if (!reasons.length) {
            reasons.push('A signature Elvessora fragrance aligned with your preferences.');
        }

        var pct = Math.round(Math.min(99, Math.max(55, (total / max) * 100)));
        return { product: product, pct: pct, reasons: reasons.slice(0, 2) };
    }

    function runMatch(criteria) {
        var scored = catalog.map(function (p) { return scoreProduct(p, criteria); });
        scored.sort(function (a, b) { return b.pct - a.pct; });
        return scored.filter(function (s) { return s.pct >= 58; }).slice(0, 8);
    }

    /* --- Render results --- */
    function renderResults(results, subtitle) {
        var section = root.querySelector('[data-pf-results]');
        var grid = root.querySelector('[data-results-grid]');
        var noResults = root.querySelector('[data-no-results]');
        var title = root.querySelector('[data-results-title]');
        var sub = root.querySelector('[data-results-sub]');

        section.hidden = false;
        section.classList.add('is-visible');
        if (sub) sub.textContent = subtitle || '';
        grid.innerHTML = '';

        if (!results.length) {
            noResults.hidden = false;
            grid.hidden = true;
            return;
        }

        noResults.hidden = true;
        grid.hidden = false;

        results.forEach(function (item, idx) {
            var p = item.product;
            var card = document.createElement('article');
            card.className = 'pf-result-card';
            card.style.animationDelay = (idx * 0.08) + 's';
            card.innerHTML =
                '<div class="pf-result-badge">' + item.pct + '% Match</div>' +
                '<a href="' + p.url + '" class="pf-result-image">' +
                '<img src="' + p.image + '" alt="' + p.name + '" loading="lazy">' +
                '</a>' +
                '<div class="pf-result-body">' +
                '<h4><a href="' + p.url + '">' + p.name + '</a></h4>' +
                '<p class="pf-result-price">' + p.price_display + '</p>' +
                '<p class="pf-result-notes">' + (p.notes || '').split(',').slice(0, 3).join(' · ') + '</p>' +
                '<p class="pf-result-why"><strong>Why it matches:</strong> ' + item.reasons.join(' ') + '</p>' +
                '<div class="pf-result-actions">' +
                (p.wishlist_url
                    ? '<a href="' + p.wishlist_url + '" class="pf-btn pf-btn--outline pf-btn--sm"><i class="bi bi-heart"></i> Wishlist</a>'
                    : '') +
                '<button type="button" class="pf-btn pf-btn--ghost pf-btn--sm" data-compare-add data-id="' + p.id + '">' +
                '<i class="bi bi-sliders2"></i> Compare</button>' +
                '<a href="' + p.url + '" class="pf-btn pf-btn--gold pf-btn--sm">View</a>' +
                '</div></div>';
            grid.appendChild(card);
        });

        grid.querySelectorAll('[data-compare-add]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                addCompare(btn.getAttribute('data-id'));
            });
        });

        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    /* --- Find / Clear --- */
    root.querySelector('[data-pf-find]').addEventListener('click', function () {
        var results = runMatch(filters);
        renderResults(results, 'Based on your quick filter selections.');
    });

    root.querySelectorAll('[data-pf-clear]').forEach(function (btn) {
        btn.addEventListener('click', clearFilters);
    });

    function clearFilters() {
        filters = { gender: 'unisex', occasions: [], seasons: ['all'], scent_families: [], intensity: 'moderate', budget_max: 1000 };
        root.querySelectorAll('[data-filter]').forEach(function (group) {
            var key = group.getAttribute('data-filter');
            if (key === 'budget_max') {
                group.value = 1000;
                return;
            }
            group.querySelectorAll('.pf-chip').forEach(function (chip) {
                var val = chip.getAttribute('data-value');
                var multi = group.getAttribute('data-multi') === 'true';
                chip.classList.remove('is-active');
                if (!multi && val === 'unisex') chip.classList.add('is-active');
                if (!multi && val === 'moderate') chip.classList.add('is-active');
                if (multi && val === 'all') chip.classList.add('is-active');
            });
        });
        var display = root.querySelector('[data-budget-display]');
        if (display) display.textContent = 'AED 100 – 1,000+';
        root.querySelector('[data-pf-results]').hidden = true;
    }

    /* --- Quiz --- */
    function resetQuiz() {
        quizStep = 0;
        quizAnswers = {};
        showQuizStep(0);
    }

    function showQuizStep(step) {
        quizStep = step;
        root.querySelectorAll('[data-step]').forEach(function (el) {
            el.classList.toggle('is-active', parseInt(el.getAttribute('data-step'), 10) === step);
        });
        var progress = root.querySelector('[data-quiz-progress]');
        var label = root.querySelector('[data-quiz-step-label]');
        var back = root.querySelector('[data-quiz-back]');
        if (progress) progress.style.width = Math.round(((step + 1) / quizTotal) * 100) + '%';
        if (label) label.textContent = 'Question ' + (step + 1) + ' of ' + quizTotal;
        if (back) back.hidden = step === 0;
    }

    root.querySelectorAll('.pf-quiz-opt').forEach(function (opt) {
        opt.addEventListener('click', function () {
            var key = opt.getAttribute('data-quiz-key');
            var val = opt.getAttribute('data-value');
            quizAnswers[key] = val;
            opt.closest('.pf-quiz-step').querySelectorAll('.pf-quiz-opt').forEach(function (o) {
                o.classList.remove('is-selected');
            });
            opt.classList.add('is-selected');
            setTimeout(function () {
                if (quizStep < quizTotal - 1) showQuizStep(quizStep + 1);
            }, 280);
        });
    });

    var quizBudget = root.querySelector('[data-quiz-key="budget_max"]');
    var quizBudgetDisplay = root.querySelector('[data-quiz-budget-display]');
    if (quizBudget) {
        quizBudget.addEventListener('input', function () {
            quizAnswers.budget_max = parseInt(quizBudget.value, 10);
            if (quizBudgetDisplay) {
                quizBudgetDisplay.textContent = 'Up to AED ' + quizAnswers.budget_max.toLocaleString();
            }
        });
        quizAnswers.budget_max = parseInt(quizBudget.value, 10);
    }

    root.querySelectorAll('[data-quiz-next]').forEach(function (btn) {
        btn.addEventListener('click', function () { showQuizStep(quizStep + 1); });
    });

    function finishQuiz() {
        var notesInput = root.querySelector('[data-quiz-key="notes"]');
        if (notesInput && notesInput.value.trim()) {
            quizAnswers.notes = notesInput.value.trim();
        }
        var criteria = {
            gender: quizAnswers.gender || 'unisex',
            occasion: quizAnswers.occasion,
            occasions: quizAnswers.occasion ? [quizAnswers.occasion] : [],
            season: quizAnswers.season,
            seasons: quizAnswers.season ? [quizAnswers.season] : ['all'],
            scent_family: quizAnswers.scent_family,
            scent_families: quizAnswers.scent_family ? [quizAnswers.scent_family] : [],
            intensity: quizAnswers.intensity || 'moderate',
            budget_max: quizAnswers.budget_max || 1000,
            notes: quizAnswers.notes || '',
        };
        var results = runMatch(criteria);
        renderResults(results, 'Your personalised quiz results are ready.');
    }

    root.querySelectorAll('[data-quiz-finish], [data-quiz-finish-skip]').forEach(function (btn) {
        btn.addEventListener('click', finishQuiz);
    });

    root.querySelector('[data-quiz-back]').addEventListener('click', function () {
        if (quizStep > 0) showQuizStep(quizStep - 1);
    });

    /* --- Compare --- */
    function addCompare(id) {
        if (compareList.indexOf(String(id)) !== -1) return;
        if (compareList.length >= 3) {
            compareList.shift();
        }
        compareList.push(String(id));
        updateCompareBar();
    }

    function updateCompareBar() {
        var bar = root.querySelector('[data-compare-bar]');
        var count = root.querySelector('[data-compare-count]');
        if (!bar) return;
        bar.hidden = compareList.length === 0;
        if (count) count.textContent = compareList.length + ' selected for compare';
    }

    root.querySelector('[data-compare-clear]').addEventListener('click', function () {
        compareList = [];
        updateCompareBar();
    });

    root.querySelector('[data-compare-open]').addEventListener('click', function () {
        var modal = root.querySelector('[data-compare-modal]');
        var table = root.querySelector('[data-compare-table]');
        var items = catalog.filter(function (p) { return compareList.indexOf(String(p.id)) !== -1; });
        var html = '<table class="pf-compare-table"><thead><tr><th></th>';
        items.forEach(function (p) { html += '<th>' + p.name + '</th>'; });
        html += '</tr></thead><tbody>';
        [['Price', 'price_display'], ['Notes', 'notes'], ['Intensity', 'intensity'], ['Gender', 'gender']].forEach(function (row) {
            html += '<tr><td>' + row[0] + '</td>';
            items.forEach(function (p) { html += '<td>' + (p[row[1]] || '—') + '</td>'; });
            html += '</tr>';
        });
        html += '</tbody></table>';
        table.innerHTML = html;
        modal.hidden = false;
    });

    root.querySelector('[data-compare-close]').addEventListener('click', function () {
        root.querySelector('[data-compare-modal]').hidden = true;
    });

    /* --- Help float: only while finder is in view (avoids covering Favorites) --- */
    var helpBtn = root.querySelector('[data-pf-help]');
    if (helpBtn) {
        helpBtn.addEventListener('click', function () {
            root.querySelector('[data-pf-mode="quiz"]').click();
            root.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
        if ('IntersectionObserver' in window) {
            helpBtn.hidden = true;
            var helpObs = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    helpBtn.hidden = !entry.isIntersecting;
                });
            }, { root: null, threshold: 0.12 });
            helpObs.observe(root);
        }
    }

})();

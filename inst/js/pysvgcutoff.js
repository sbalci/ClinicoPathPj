/* Native Svg uses only local, Python-computed states. No backend communication. */
(() => {
    'use strict';
    if (window.cpjSvgCutoffObserverInstalled) return;
    window.cpjSvgCutoffObserverInstalled = true;
    function start() {
        for (const root of document.querySelectorAll('.cpj-svg-cutoff')) {
            if (root.dataset.ready) continue;
            root.dataset.ready = 'true';
            const svg = root, p = JSON.parse(svg.getAttribute('data-payload'));
            // The original result retains the payload; exported graphics need drawing data only.
            svg.removeAttribute('data-payload');
            const input = root.querySelector('.cutoff-input'), handle = svg.querySelector('.handle');
            let current = p.initial, dragging = false;
            const points = p.curves[p.direction].points;
            const y = v => 475 - (v - p.domain[0]) / (p.domain[1] - p.domain[0]) * 340;
            const counts = c => `TP ${c.tp} · FP ${c.fp} · FN ${c.fn} · TN ${c.tn}`;
            // Same boundary convention as Python; no statistical estimation in the browser.
            function state(cut) {
                let lo = 0, hi = points.length;
                while (lo < hi) {
                    const mid = (lo + hi) >>> 1;
                    if (p.direction === 'ge' ? points[mid].cutoff < cut : points[mid].cutoff <= cut) lo = mid + 1;
                    else hi = mid;
                }
                return points[Math.max(0, Math.min(points.length - 1, p.direction === 'ge' ? lo : lo - 1))];
            }
            for (const k of Object.keys(p.expected)) {
                if (state(current)[k] !== p.expected[k]) throw Error('SVG lookup differs from Python.');
            }
            function preview(value, clamp = false, editing = false) {
                if (!Number.isFinite(value)) {
                    root.querySelector('.feedback').textContent = ' Enter a finite numeric cutoff.';
                    return;
                }
                current = clamp ? Math.max(p.domain[0], Math.min(p.domain[1], value)) : value;
                root.querySelector('.feedback').textContent = ' Preview only; native rule unchanged.';
                if (!editing) input.textContent = String(current);
                const c = state(current), yy = y(Math.max(p.domain[0], Math.min(p.domain[1], current)));
                for (const el of [handle, svg.querySelector('.cut-line')]) {
                    el.setAttribute('y1', yy); el.setAttribute('y2', yy);
                }
                handle.setAttribute('aria-valuenow', current);
                handle.setAttribute('aria-valuetext', `Cutoff ${current}; ${counts(c)}`);
                handle.setAttribute('aria-valuemin', Math.min(p.domain[0], current));
                handle.setAttribute('aria-valuemax', Math.max(p.domain[1], current));
                svg.querySelector('.preview').textContent = `Preview cutoff ${current}: ${counts(c)}`;
                const op = svg.querySelector('.operating');
                op.setAttribute('cx', 535 + c.fpr * 400); op.setAttribute('cy', 475 - c.tpr * 340);
                for (const dot of svg.querySelectorAll('.observation')) {
                    const row = p.rows[Number(dot.dataset.index)];
                    const positive = p.direction === 'ge' ? row.value >= current : row.value <= current;
                    dot.setAttribute('fill', positive === row.positive ? '#3975b8' : '#c25a2d');
                }
            }
            input.addEventListener('input', () => preview(input.textContent.trim() === '' ? NaN : Number(input.textContent), false, true));
            input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); input.blur(); } });
            for (const control of root.querySelectorAll('.svg-button')) {
                control.addEventListener('keydown', e => {
                    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); control.dispatchEvent(new MouseEvent('click', {bubbles: true})); }
                });
            }
            root.querySelector('.automatic').addEventListener('click', () => preview(points[p.curves[p.direction].optima[p.criterion].point].cutoff));
            root.querySelector('.apply').addEventListener('click', () => {
                svg.querySelector('.snapshot').textContent = `Local snapshot cutoff ${current}: ${counts(state(current))}`;
                root.querySelector('.feedback').textContent = ' Local SVG snapshot updated; native rule unchanged.';
            });
            root.querySelector('.reset').addEventListener('click', () => {
                preview(p.initial);
                svg.querySelector('.snapshot').textContent = `Local snapshot cutoff ${current}: ${counts(state(current))}`;
            });
            for (const dot of svg.querySelectorAll('.roc-point')) {
                const choose = () => preview(points[Number(dot.dataset.point)].cutoff);
                dot.addEventListener('click', choose);
                dot.addEventListener('keydown', e => {
                    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); choose(); }
                });
            }
            handle.addEventListener('keydown', e => {
                let value = current, step = (p.domain[1] - p.domain[0]) / 100 * (e.shiftKey ? 10 : 1);
                if (e.key === 'ArrowUp' || e.key === 'ArrowRight') value += step;
                else if (e.key === 'ArrowDown' || e.key === 'ArrowLeft') value -= step;
                else if (e.key === 'Home') value = p.domain[0];
                else if (e.key === 'End') value = p.domain[1];
                else return;
                e.preventDefault(); e.stopPropagation(); preview(value, true);
            });
            function move(e) {
                const point = svg.createSVGPoint(); point.x = e.clientX; point.y = e.clientY;
                const local = point.matrixTransform(svg.getScreenCTM().inverse());
                preview(p.domain[0] + (545 - local.y) / 340 * (p.domain[1] - p.domain[0]), true);
            }
            // Capture at the window: jamovi's result-selection layer also handles dragging.
            const dragMove = e => { if (!root.isConnected) { end(); return; } if (dragging) { e.preventDefault(); move(e); } };
            const end = () => {
                dragging = false;
                window.removeEventListener('pointermove', dragMove, true);
                window.removeEventListener('pointerup', end, true);
                window.removeEventListener('pointercancel', end, true);
            };
            handle.style.touchAction = 'none';
            handle.addEventListener('pointerdown', e => {
                e.preventDefault(); e.stopPropagation(); dragging = true; handle.focus();
                window.addEventListener('pointermove', dragMove, true);
                window.addEventListener('pointerup', end, true);
                window.addEventListener('pointercancel', end, true);
                move(e);
            });
        }
    }
    // Native Svg loads assets before inserting content; initialize each new root once.
    const observer = new MutationObserver(start);
    observer.observe(document, {childList: true, subtree: true});
    window.addEventListener('pagehide', () => observer.disconnect(), {once: true});
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true});
    else start();
})();

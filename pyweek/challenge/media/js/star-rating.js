/* Progressive enhancement: native radios provide keyboard and AT behaviour. */
(() => {
    'use strict';
    const star = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
        '<path d="m12 3 2.8 5.7 6.3.9-4.55 4.45 1.07 6.28L12 17.37l-5.62 2.96 1.07-6.28L2.9 9.6l6.3-.9Z"/></svg>';

    function enhance(input) {
        const label = input.labels[0];
        if (!label) return;
        const fieldset = document.createElement('fieldset');
        fieldset.className = 'star-rating';
        const legend = document.createElement('legend');
        legend.textContent = label.textContent;
        fieldset.append(legend);
        const controls = document.createElement('div');
        controls.className = 'star-rating__controls';
        const status = document.createElement('span');
        status.className = 'star-rating__status';
        // The radios already announce their values. Avoid duplicate live announcements.
        status.setAttribute('aria-hidden', 'true');
        const radios = [];
        const labels = [];
        for (let value = 0; value <= 5; value++) {
            const option = document.createElement('label');
            option.className = 'star-rating__option';
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = input.name;
            radio.value = String(value);
            radio.required = input.required;
            radio.disabled = input.disabled;
            radio.defaultChecked = input.value === String(value);
            radio.setAttribute('aria-label', `${value} out of 5 stars`);
            const icon = document.createElement('span');
            icon.className = 'star-rating__icon';
            icon.setAttribute('aria-hidden', 'true');
            if (value === 0) icon.textContent = '0';
            else icon.innerHTML = star;
            option.append(radio, icon);
            option.addEventListener('mouseenter', () => paint(value));
            radios.push(radio);
            labels.push(option);
            controls.append(option);
        }
        function paint(value) {
            labels.forEach((option, index) => {
                option.classList.toggle('is-filled', index > 0 && index <= value);
            });
        }
        function refresh() {
            const checked = radios.find(radio => radio.checked);
            paint(checked ? Number(checked.value) : -1);
            status.textContent = checked ? `${checked.value} / 5` : 'Not rated';
        }
        controls.addEventListener('mouseleave', refresh);
        controls.addEventListener('change', refresh);
        // Reset fires before the browser restores defaultChecked.
        if (input.form) input.form.addEventListener('reset', () => setTimeout(refresh, 0));
        fieldset.append(controls, status);
        refresh();
        label.remove();
        input.replaceWith(fieldset);
    }
    function init() {
        document.querySelectorAll('input[data-star-rating]').forEach(enhance);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();

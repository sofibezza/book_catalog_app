export function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

export function formatDate(isoString) {
    if (!isoString) return '';
    return new Date(isoString).toLocaleDateString();
}
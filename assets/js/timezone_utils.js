(function(global) {
    function resolveDefaultTimezone() {
        if (global.fireCoastTimezone) {
            const tz = String(global.fireCoastTimezone || '').trim();
            if (tz) return tz;
        }
        try {
            return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
        } catch (error) {
            console.error('Failed to resolve browser timezone', error);
            return 'UTC';
        }
    }

    function formatDateTime(value, timeZone, options) {
        if (!value) return 'Unknown';
        try {
            const date = new Date(value);
            if (Number.isNaN(date.getTime())) return value;
            const tz = timeZone || resolveDefaultTimezone();
            return date.toLocaleString(undefined, { timeZone: tz, ...(options || {}) });
        } catch (error) {
            console.error('Failed to format date', error);
            return value;
        }
    }

    const utils = { resolveDefaultTimezone, formatDateTime };
    global.fireCoastTimezoneUtils = utils;
    global.fireCoastDefaultTimeZone = resolveDefaultTimezone();
})(window);

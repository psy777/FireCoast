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
            let input = value;

            if (typeof value === 'string') {
                const trimmed = value.trim();
                const hasTimezone = /[zZ]$/.test(trimmed) || /[+-]\d{2}:?\d{2}$/.test(trimmed);

                if (!hasTimezone) {
                    const isoLike = trimmed.replace(' ', 'T');
                    input = `${isoLike}Z`;
                } else {
                    input = trimmed;
                }
            }

            const date = new Date(input);
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

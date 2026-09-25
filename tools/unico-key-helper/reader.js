/* Only launch through helper.py: stdout contains credentials in a private pipe. */
'use strict';
(function () {
    const prefix = 'UNICO_RESULT_V1:';
    let sent = false;
    function emit(value) {
        if (!sent) { sent = true; console.log(prefix + JSON.stringify(value)); }
    }
    if (typeof Java === 'undefined' || !Java.available) {
        emit({schema: 1, error: 'JAVA_UNAVAILABLE'}); return;
    }
    // Loaded during spawn; no scan until the user confirms that the page loaded.
    let requested = false;
    globalThis.unicoRead = function () {
        if (requested || sent) return;
        requested = true;
        scan();
    };
    Java.perform(function () {
        console.log('UNICO_READER_V1:STARTED');
    });
    function scan() {
      Java.perform(function () {
        const classes = ['com.thingclips.smart.sdk.bean.DeviceBean', 'com.tuya.smart.sdk.bean.DeviceBean'];
        const rows = [];
        let index = 0, available = 0, truncated = false;
        function get(instance, name) {
            try { const v = instance[name](); return v === null || v === undefined ? '' : String(v); }
            catch (_) { return ''; }
        }
        function next() {
            if (index === classes.length) {
                emit({schema: 1, devices: rows, truncated: truncated, error: available ? null : 'NO_CLASS'}); return;
            }
            const name = classes[index++];
            try { Java.use(name); available++; } catch (_) { next(); return; }
            try {
                Java.choose(name, {
                    onMatch: function (instance) {
                        if (rows.length >= 512) { truncated = true; return 'stop'; }
                        rows.push({name: get(instance, 'getName'), device_id: get(instance, 'getDevId'),
                            local_key: get(instance, 'getLocalKey'), host: get(instance, 'getIp')});
                    },
                    onComplete: next
                });
            } catch (_) { emit({schema: 1, error: 'SCAN_FAILED'}); }
        }
        next();
      });
    }
})();

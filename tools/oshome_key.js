/*
 * Experimental helper for reading the current user's own Tuya/ThingClips
 * device data from the OS Home Android app at runtime.
 *
 * Tested target during development:
 *   App:     OS Home 2.0.7
 *   Package: com.olimpiasplendid.oshome
 *
 * Use only with your own app account and your own devices.
 */

Java.perform(function () {
    const candidateClasses = [
        "com.thingclips.smart.sdk.bean.DeviceBean",
        "com.tuya.smart.sdk.bean.DeviceBean",
    ];
    const delayMs = 20000;

    function safeCall(instance, methodName) {
        try {
            if (instance[methodName]) {
                return String(instance[methodName]());
            }
        } catch (error) {
            return "<error: " + error + ">";
        }
        return "<unavailable>";
    }

    function scanClass(className) {
        try {
            Java.use(className);
        } catch (error) {
            console.log("[-] Class not available: " + className);
            return;
        }

        let found = 0;
        console.log("[*] Scanning heap for " + className + " ...");

        Java.choose(className, {
            onMatch: function (instance) {
                found += 1;
                console.log("----------------------------------------");
                console.log("Name:       " + safeCall(instance, "getName"));
                console.log("Device ID:  " + safeCall(instance, "getDevId"));
                console.log("Local Key:  " + safeCall(instance, "getLocalKey"));
                console.log("IP address: " + safeCall(instance, "getIp"));
            },
            onComplete: function () {
                console.log("[*] " + className + ": " + found + " device object(s) found.");
                if (found === 0) {
                    console.log("[*] Keep OS Home open on the device list/detail screen and run the script again.");
                }
            },
        });
    }

    console.log("[*] OS Home key helper loaded.");
    console.log("[*] Waiting " + (delayMs / 1000) + " seconds for the app to load device data ...");

    setTimeout(function () {
        candidateClasses.forEach(scanClass);
    }, delayMs);
});

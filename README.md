# Olimpia Splendid UNICO — Home Assistant Custom Integration

An unofficial Home Assistant custom integration for local control and monitoring of compatible **Olimpia Splendid UNICO** air-conditioning units that expose a **Tuya LAN 3.4** interface.

The implementation has been empirically validated on an **Olimpia Splendid UNICO EVO 25 HP PVAN (internal code 02455)**. During normal operation, communication between Home Assistant and the air conditioner is performed on the local network; the integration does not require the OS Home cloud once the device address, Tuya Device ID, and Tuya Local Key are available.

> [!IMPORTANT]
> This is an independent community project. It is not affiliated with, endorsed by, or supported by Olimpia Splendid S.p.A.

## Project status

The integration is currently a **public beta**. Its core climate-control functions are operational on the reference device, but the project should still be considered experimental outside that tested configuration.

| Parameter | Current project state |
|---|---|
| Integration domain | `olimpia_unico` |
| Integration type | Home Assistant device integration |
| I/O model | Local polling |
| Local protocol | Tuya LAN 3.4 |
| Python dependency | `tinytuya==1.20.0` |
| Reference device | UNICO EVO 25 HP PVAN (02455) |
| Reference OS Home version used during analysis | 2.0.7 |
| HACS-declared minimum Home Assistant version | 2026.8.0 |

### Evidence terminology

Compatibility and diagnostic interpretations in this document are deliberately classified by evidence level. The terms **verified**, **inferred**, **experimental**, and **unknown** describe the present engineering evidence available to this project; they are not manufacturer statements.

For diagnostic datapoints, the confidence labels are qualitative engineering assessments rather than statistical confidence intervals:

- **Very high:** repeatedly observed behavior is strongly and consistently associated with the stated quantity.
- **High:** observed behavior is consistent and the interpretation is well supported, but not independently documented by the manufacturer.
- **Moderate:** the interpretation is plausible and supported by observations, but has not been isolated sufficiently for a stronger assignment.
- **Low:** tentative interpretation; additional controlled observations are required.
- **Unknown:** no reliable semantic assignment has yet been established.

## Device compatibility

Only the reference device has been extensively tested with this integration. Compatibility statements for other product families are therefore provisional.

| Device / platform | Assessment | Basis |
|---|---|---|
| **UNICO EVO 25 HP PVAN (02455)** | **Verified** | Direct functional testing on the physical reference device |
| Other current **OS Home-based UNICO EVO, UNICO NEXT, and UNICO PRO** models | **Candidate; unverified** | Shared OS Home / Tuya platform and apparently related datapoint structures; not yet validated by this project |
| **UNICO VERTICAL / VERTICAL-NK** | **Experimental candidate** | Architectural similarity; no project-level functional validation yet |
| Older devices using the **B1015 Wi-Fi retrofit module** or the earlier UNICO Wi-Fi platform | **Not supported by this implementation** | Different communication platform from the Tuya LAN 3.4 interface targeted here |

A model should not be reported as compatible solely because it can be configured in OS Home. Reliable compatibility requires confirmation of the local protocol version, datapoint schema, and command semantics on the physical device.

## Functional scope

The following functions are implemented for the reference device:

- power control;
- HVAC modes: **Auto, Cool, Heat, Dry, and Fan only**;
- target-temperature control and current room-temperature reporting;
- fan modes: **Auto, Low, Medium, and High**;
- oscillation / swing control;
- **Eco**, **Silent**, and combined **Eco + Silent** operation;
- display control;
- internal diagnostic sensors;
- communication-health sensors and reconnect handling;
- local status polling.

### Home Assistant entities

The integration exposes one climate entity together with optional switch and diagnostic sensor entities. Diagnostic entities are disabled by default where appropriate because several datapoints are intended primarily for technical investigation rather than routine automation.

## Communication architecture

The integration communicates directly with the device through the local Tuya protocol using TinyTuya. No manufacturer API is called by the integration during normal runtime operation.

The current implementation uses:

- **Tuya protocol version:** 3.4;
- **default polling interval:** 60 s;
- **socket timeout:** 8 s;
- bounded socket retry behavior rather than an aggressive retry loop;
- a **45 s reconnect backoff** after communication failure;
- a persistent Tuya client during normal operation;
- a preventive client-session rotation once per day at 10:00 Home Assistant local time, but only when the latest known device state indicates that the unit is switched off.

These parameters are implementation details chosen after practical stability testing with the reference Wi-Fi module. They should not be interpreted as requirements of the Olimpia Splendid product itself.

## Implemented Tuya datapoint mapping

The table below describes the datapoint assignments currently used by the integration. It documents the software mapping, not an official manufacturer protocol specification.

| DP | Function used by the integration | Representation |
|---:|---|---|
| 1 | Power | Boolean |
| 2 | Target temperature | Numeric, °C |
| 3 | Current room temperature | Numeric, °C |
| 4 | Operating mode | `auto`, `cool`, `heat`, `dehum`, `fan` |
| 5 | Fan mode | `auto`, `low`, `middle`, `high` |
| 8 | Eco mode | Boolean |
| 15 | Swing / oscillation | `ON` / `OFF` |
| 19 | Temperature-unit information | Diagnostic value |
| 22 | Device error code | Diagnostic value |
| 25 | Silent mode | Boolean |
| 36 | Display | Boolean |

## Device credentials and security model

Local Tuya communication requires three device-specific values:

1. the local IP address or hostname;
2. the **Tuya Device ID**;
3. the **Tuya Local Key**.

The Device ID and Local Key currently have to be obtained by the user. The procedure used during development is documented in [`docs/GETTING_KEYS.md`](docs/GETTING_KEYS.md), and the associated experimental Frida helper is provided as [`tools/oshome_key.js`](tools/oshome_key.js).

> [!WARNING]
> Treat the **Local Key as a device credential**. Do not publish Local Keys, Device IDs, account credentials, tokens, or unreviewed debug logs in GitHub issues, screenshots, forum posts, or other public material.

The integration necessarily stores the Device ID and Local Key in the Home Assistant config entry because both values are required for local Tuya communication. Consequently, Home Assistant files under `.storage/` and complete Home Assistant backups may contain sensitive credentials and should be protected accordingly.

To reduce unnecessary exposure:

- Home Assistant device identifiers and entity unique IDs use a stable SHA-256-based fingerprint instead of the raw Device ID;
- Home Assistant diagnostics redact the host, Device ID, and Local Key;
- the issue template explicitly requires users to remove secrets before submitting logs;
- repository ignore rules exclude common Home Assistant configuration, credential, key, and log files.

Raw TinyTuya debug output can still contain protocol or device metadata. Debug logs must therefore be reviewed and redacted before publication.

Security-sensitive findings should be reported according to [`SECURITY.md`](SECURITY.md), not disclosed in a public issue.

## Installation

### HACS as a custom repository

Until or unless this project is distributed through another HACS channel, it can be installed as a custom repository:

1. Open **HACS → Integrations**.
2. Open the HACS menu and select **Custom repositories**.
3. Add `https://github.com/5urz/ha-olimpia-splendid-unico-evo` as an **Integration** repository.
4. Install **Olimpia Splendid UNICO**.
5. Restart Home Assistant.
6. Open **Settings → Devices & services → Add integration**.
7. Search for **Olimpia Splendid UNICO** and enter the device address, Device ID, and Local Key.

### Manual installation

1. Download or clone this repository.
2. Copy `custom_components/olimpia_unico/` to `/config/custom_components/olimpia_unico/` in the Home Assistant configuration directory.
3. Restart Home Assistant completely.
4. Open **Settings → Devices & services → Add integration**.
5. Search for **Olimpia Splendid UNICO**.
6. Enter the local IP address or hostname, Device ID, and Local Key.
7. The config flow validates local communication before creating the integration entry.

### Updating

For a manual update, replace the existing `/config/custom_components/olimpia_unico/` directory with the version from the new release and restart Home Assistant. Existing configuration entries are designed to be retained across normal upgrades.

Debug logging is not required for routine operation.

## Network requirements

Home Assistant must be able to reach the air conditioner over the local network. Because the integration currently addresses the unit by host/IP, a **DHCP reservation** is recommended to prevent address changes.

The integration is designed for local operation. Loss of internet connectivity does not by itself prevent Home Assistant from communicating with an already configured device, provided that the local network remains operational and the stored Tuya credentials remain valid.

## Development and reverse-engineering methodology

This integration was developed as an independent interoperability project. It does **not** use an official Olimpia Splendid API or official protocol documentation.

The investigation combined several forms of empirical analysis:

- runtime observation of the **OS Home** Android application;
- Android Studio / Android Emulator;
- Magisk / rootAVD and ADB;
- Frida / frida-server for runtime inspection;
- observation of ThingClips/Tuya SDK objects on the developer's own account and device;
- TinyTuya-based local communication experiments;
- Home Assistant debug logging;
- controlled functional tests on the physical reference unit.

The analysis and implementation were developed iteratively with assistance from **ChatGPT**. Technical claims in this repository are intended to reflect observed behavior, source-code inspection of this project, and reproducible device tests rather than manufacturer documentation.

No Olimpia Splendid APK, manufacturer source code, account credentials, device keys, or other proprietary manufacturer files are distributed with this repository.

The credential-extraction instructions are intended exclusively for devices and accounts that the user is authorized to access.

## Internal diagnostic datapoints

Several higher-numbered datapoints expose values that appear to describe internal thermodynamic or actuator state. Their semantics have not been documented by Olimpia Splendid for this project. The assignments below are therefore empirical interpretations and are explicitly confidence-rated.

| DP | Current interpretation | Unit | Confidence |
|---:|---|---:|---|
| 101 | Outdoor / intake-air temperature | °C | Low |
| 102 | Indoor heat-exchanger temperature | °C | High |
| 103 | Outdoor heat-exchanger temperature | °C | High |
| 104 | Compressor / discharge-gas temperature | °C | Low |
| 105 | Compressor frequency | Hz | Very high |
| 107 | Expansion-valve position | steps | Low |
| 110 | Indoor-fan speed | rpm | Very high |
| 111 | Outdoor-fan speed | rpm | Moderate |
| 115 | Unidentified diagnostic value | — | Unknown |
| 117 | Unidentified diagnostic value | — | Unknown |

These assignments should not be used for safety-critical control. Further controlled measurements across operating states are required before the lower-confidence interpretations can be considered established.

## Known limitations

- Extensive validation currently exists for only one physical device model.
- Device ID and Local Key acquisition is still a manual, technically demanding process.
- BLE-based discovery and provisioning are not implemented.
- The project depends on an undocumented local protocol and may therefore be affected by future firmware, application, or platform changes.
- Several internal diagnostic datapoints remain only partially interpreted.
- Compatibility with other OS Home-based UNICO models remains to be demonstrated experimentally.

## Research and development priorities

The principal open questions are:

1. whether BLE discovery and provisioning can be implemented directly in Home Assistant, removing the need for Frida-based credential retrieval for normal users;
2. which additional UNICO EVO, NEXT, PRO, and VERTICAL variants implement a sufficiently compatible Tuya datapoint schema;
3. whether the tentative internal diagnostic datapoint assignments can be confirmed through controlled multi-state measurements;
4. whether protocol differences exist between firmware or Wi-Fi-module revisions within the same commercial model family.

Reports from additional devices are particularly useful when they include the exact commercial model designation, internal product code if available, Home Assistant version, integration version, and carefully redacted diagnostic observations.

## Related work and attribution

An important reference during the initial investigation was the existing Home Assistant integration by **Daneel87 / Davide Melle**, [`Daneel87/ha-olimpia-splendid-unico`](https://github.com/Daneel87/ha-olimpia-splendid-unico). That implementation did not establish working communication with the project's reference UNICO EVO 25 HP PVAN (02455), which led to the independent Tuya LAN investigation used here.

Third-party acknowledgements and applicable license notices are documented in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## License, trademarks, and disclaimer

The source code developed in this repository is released under the **MIT License**; see [`LICENSE`](LICENSE). The project license does not grant rights to third-party trademarks, logos, product names, or other protected identifiers.

**Olimpia Splendid**, **UNICO**, **OS Home**, and other product or company names referenced in this repository are the property of their respective rights holders. They are used solely to identify the products and software with which this independent project is intended to interoperate. The repository does not use the official Olimpia Splendid logo; the included HVAC symbol is an independently created neutral project icon.

This software is provided without warranty. Use it at your own risk. Users are responsible for ensuring that their use of reverse-engineering procedures, credentials, software, and devices complies with the laws and contractual terms applicable to them.

This project is not affiliated with, endorsed by, or supported by Olimpia Splendid S.p.A.

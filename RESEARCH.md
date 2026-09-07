# Research Record — Olimpia Splendid UNICO Local Integration

This document records the empirical research underlying the `ha-olimpia-splendid-unico-evo` Home Assistant integration. Its purpose is to separate **observation**, **interpretation**, and **implementation choice** as clearly as possible, so that technical conclusions remain reviewable and reproducible as additional devices and firmware versions are tested.

The document is intentionally written as an engineering research log rather than as user documentation. User-facing setup and installation instructions remain in [`README.md`](README.md) and [`docs/GETTING_KEYS.md`](docs/GETTING_KEYS.md).

> [!IMPORTANT]
> This project is independent and unofficial. The findings below are not manufacturer documentation and should not be represented as such.

## 1. Research objectives

The investigation addresses four principal questions:

1. **Local interoperability:** Can an Olimpia Splendid UNICO unit configured through OS Home be controlled reliably from Home Assistant without manufacturer-cloud access during normal operation?
2. **Protocol characterization:** Which local protocol, protocol version, and datapoint semantics are used by the tested device?
3. **Device compatibility:** Which other UNICO product variants appear to share a sufficiently compatible communication architecture?
4. **Internal telemetry interpretation:** Which undocumented datapoints can be associated with temperatures, actuators, compressor state, or other internal operating variables with defensible evidence?

A secondary objective is to identify a future onboarding mechanism that avoids manual extraction of Tuya credentials.

## 2. Scope and reference system

### 2.1 Physical reference device

| Parameter | Reference value |
|---|---|
| Manufacturer | Olimpia Splendid |
| Product family | UNICO EVO |
| Commercial designation | UNICO EVO 25 HP PVAN |
| Internal product code | 02455 |
| Control application used during analysis | OS Home |
| OS Home version used during the documented runtime investigation | 2.0.7 |
| Local protocol identified by this project | Tuya LAN 3.4 |

The reference device is the only model for which this project currently claims extensive direct functional validation.

### 2.2 Home Assistant implementation under study

| Parameter | Current value |
|---|---|
| Integration domain | `olimpia_unico` |
| I/O model | Local polling |
| Tuya implementation | TinyTuya |
| Declared TinyTuya version | `1.20.0` |
| Default polling interval | 60 s |
| Socket timeout | 8 s |
| Reconnect backoff | 45 s |

These values describe the present software implementation and must not be confused with inherent requirements of the appliance.

## 3. Evidence model

Every technical claim should, where practical, be assigned one of the following evidence classes.

### E0 — Unknown

No reliable semantic interpretation has been established.

### E1 — Hypothesis

A tentative interpretation exists, but evidence is weak, indirect, or based on correlation that has not yet been isolated.

### E2 — Supported inference

Multiple observations are consistent with the interpretation, but competing explanations have not been fully excluded or the behavior has not been independently reproduced across devices.

### E3 — Repeated empirical confirmation

The interpretation has been reproduced repeatedly on the reference device under controlled state changes and is strongly associated with the observed variable.

### E4 — Cross-device or independent confirmation

The interpretation has been reproduced on more than one independent physical device, firmware revision, or implementation, or is corroborated by independent technical evidence.

At present, most project-specific protocol findings are expected to fall between **E1 and E3**. No undocumented datapoint should be treated as E4 unless independent confirmation is explicitly recorded.

## 4. Methodological principles

The following rules should govern future investigation:

- Record **raw observation before interpretation**.
- Change **one controllable variable at a time** whenever feasible.
- Repeat transitions in both directions where meaningful.
- Distinguish **application state**, **Home Assistant state**, and **physical device state**.
- Record timestamps for externally initiated actions and observed state changes.
- Prefer repeated measurements over single observations.
- Avoid inferring semantics only from numeric range or engineering plausibility.
- Mark any assumption that has not been independently confirmed.
- Do not publish credentials, Device IDs, Local Keys, tokens, private IP addresses, account data, or unredacted logs.

## 5. Investigation tools and data sources

The project has used the following technical methods and tools:

- Android Studio and Android Emulator;
- ADB;
- Magisk / rootAVD;
- Frida / frida-server;
- runtime inspection of the OS Home process on the researcher's own account and device;
- ThingClips / Tuya SDK object inspection;
- TinyTuya for local protocol experiments;
- Home Assistant debug logging;
- practical command-response testing on the physical UNICO unit;
- comparison with prior open-source work relating to Olimpia Splendid UNICO devices.

These methods were used to determine interoperability behavior. No Olimpia Splendid APK, proprietary manufacturer source code, or extracted manufacturer asset is distributed with this repository.

## 6. Credential acquisition finding

### Observation

A local Tuya session requires a device address, Tuya Device ID, and Tuya Local Key.

### Runtime finding

During testing with OS Home 2.0.7, the Device ID and Local Key could be observed at runtime from Tuya / ThingClips SDK device objects in the Android process.

The experimental helper [`tools/oshome_key.js`](tools/oshome_key.js) searches the Java heap for device objects and reads selected properties from the current user's own session.

### Interpretation

This confirms that the OS Home application uses a Tuya-derived device representation containing credentials sufficient for local Tuya communication.

### Evidence level

**E3 — repeated empirical confirmation on the reference setup.**

### Limitation

This method depends on application and SDK implementation details and may stop functioning after OS Home or SDK updates. It is not considered a suitable long-term onboarding mechanism for general users.

## 7. Local protocol finding

### Observation

The reference appliance responds to local TinyTuya communication when configured for protocol version **3.4** with the correct Device ID and Local Key.

### Interpretation

The Wi-Fi control path of the tested reference device exposes a Tuya LAN 3.4-compatible interface.

### Evidence level

**E3 — repeated empirical confirmation on the reference device.**

### Boundary of the claim

This finding applies directly to the tested 02455 reference unit. It does not by itself establish that all OS Home-capable UNICO devices use the same local protocol version or datapoint schema.

## 8. Implemented primary datapoint mapping

The following mappings are actively used by the current integration and have been validated functionally on the reference device.

| DP | Implemented interpretation | Typical value representation | Current evidence |
|---:|---|---|---|
| 1 | Power | Boolean | E3 |
| 2 | Target temperature | Numeric, °C | E3 |
| 3 | Current room temperature | Numeric, °C | E3 |
| 4 | Operating mode | `auto`, `cool`, `heat`, `dehum`, `fan` | E3 |
| 5 | Fan mode | `auto`, `low`, `middle`, `high` | E3 |
| 8 | Eco mode | Boolean | E3 |
| 15 | Swing / oscillation | `ON` / `OFF` | E3 |
| 19 | Temperature-unit related value | Diagnostic | E2 |
| 22 | Device error code | Diagnostic | E2 |
| 25 | Silent mode | Boolean | E3 |
| 36 | Display | Boolean | E3 |

### Validation criterion for E3 primary functions

For a control datapoint, E3 should normally require both:

1. a command initiated from Home Assistant causing the intended physical state change; and
2. an externally initiated state change, where available, being reflected back through subsequent local status polling.

## 9. Functional validation history

The following control sequence was used during practical validation of the reference device. It is retained here because it documents that several independent command classes were exercised rather than only a simple power toggle.

### Home Assistant initiated tests

| Approx. time | Action |
|---|---|
| 17:11 | Cooling mode on |
| 17:13 | Target temperature set to 19 °C |
| 17:14 | Silent enabled |
| 17:15 | Eco enabled |
| 17:16 | Fan set to medium |
| 17:17 | Fan set to high |
| 17:18 | Fan set to auto |
| 17:19 | Operating mode set to auto |
| 17:20 | Heating mode selected |
| 17:21 | Dry mode selected |
| 17:22 | Fan-only mode selected |
| 17:23 | Oscillation enabled |

### Remote-control initiated tests

| Approx. time | Action / observation |
|---|---|
| 17:24 | Unit switched off |
| 17:25 | Cooling enabled, target 18 °C, fan auto |
| 17:26 | Eco enabled; remote continued to show fan auto |
| 17:27 | Silent enabled; remote indicated low fan while Eco remained enabled |
| 17:29 | Unit switched off |

### Interpretation

The sequence provides multi-function evidence for bidirectional state consistency between Home Assistant polling and independently initiated physical-device changes. It also indicates that Eco and Silent may interact with fan behavior at the appliance level.

### Limitation

This test record is observational. It does not establish timing guarantees, firmware-independent behavior, or detailed internal state-machine semantics.

## 10. Communication stability observations

The integration uses a persistent TinyTuya client during normal operation. Practical testing showed that connection recovery behavior required explicit attention; transient communication failures were observed during development.

The current implementation therefore includes:

- a bounded socket retry policy;
- a fixed reconnect backoff;
- reuse of the same coordinator during transient startup failure;
- client replacement after communication failure;
- a preventive daily client-session rotation while the unit is known to be off.

### Interpretation

These measures are **implementation responses to observed stability behavior of the reference Wi-Fi module**, not protocol requirements established by documentation.

### Evidence level

The existence of transient connection behavior is **E3** for the reference system. The optimality of the present recovery parameters is only **E2** and should remain subject to revision as more long-duration data become available.

## 11. Internal diagnostic datapoints

The higher-numbered datapoints below are not required for basic climate control. Their interpretations are based on correlation with observed operating behavior and engineering plausibility.

| DP | Current interpretation | Unit | Evidence | Notes |
|---:|---|---:|---|---|
| 101 | Outdoor / intake-air temperature | °C | E1 | Tentative; alternative air-path interpretation remains possible |
| 102 | Indoor heat-exchanger temperature | °C | E3 | Strong correlation with indoor heat-exchanger thermal behavior |
| 103 | Outdoor heat-exchanger temperature | °C | E3 | Strong correlation with outdoor-side thermal behavior |
| 104 | Compressor / discharge-gas temperature | °C | E1 | Plausible thermal interpretation; insufficient isolation |
| 105 | Compressor frequency | Hz | E3 | Strong operating-state correlation and characteristic numeric behavior |
| 107 | Expansion-valve position | steps | E1 | Plausible actuator interpretation; not yet independently demonstrated |
| 110 | Indoor-fan speed | rpm | E3 | Strong correlation with commanded indoor fan level |
| 111 | Outdoor-fan speed | rpm | E2 | Plausible and correlated; additional controlled confirmation desirable |
| 115 | Unknown diagnostic value | — | E0 | No defensible semantic assignment |
| 117 | Unknown diagnostic value | — | E0 | No defensible semantic assignment |

### Safety note

These inferred internal datapoints must not be used as the sole basis for safety-critical control, protective shutdown, or fault diagnosis.

## 12. Proposed controlled experiments for diagnostic datapoints

### 12.1 DP101 — intake / outdoor-air hypothesis

**Hypothesis:** DP101 represents outdoor-side or intake-air temperature.

**Suggested experiment:**

1. Leave the unit off long enough to approach thermal equilibrium.
2. Record room temperature, outdoor temperature, and DP101.
3. Start fan-only mode and observe the initial transient.
4. Repeat in cooling and heating modes.
5. Compare DP101 with independent temperature measurements near plausible air paths.

**Confirmation criterion:** repeated tracking of one independently measured air stream with lower residual error than competing candidate locations.

### 12.2 DP104 — discharge-gas / compressor-temperature hypothesis

**Hypothesis:** DP104 is associated with compressor discharge or another high-temperature refrigeration-circuit point.

**Suggested experiment:**

1. Record DP104 at thermal equilibrium with the compressor off.
2. Start cooling and record at short intervals.
3. Repeat in heating mode.
4. Compare rise/fall dynamics with compressor frequency DP105 and heat-exchanger temperatures DP102/103.

**Expected discriminant:** a genuine discharge-temperature signal should exhibit a characteristic delayed rise after compressor start and should not simply mirror either heat-exchanger temperature.

### 12.3 DP107 — electronic expansion valve hypothesis

**Hypothesis:** DP107 reports electronic expansion-valve position in steps.

**Suggested experiment:**

1. Record DP107, DP105, DP102, and DP103 during steady cooling.
2. Apply a target-temperature change large enough to alter compressor load.
3. Observe whether DP107 changes in discrete step-like increments.
4. Repeat during mode transitions and compressor shutdown.

**Confirmation criterion:** repeatable actuator-like step behavior correlated with refrigeration load changes but distinguishable from compressor frequency.

### 12.4 DP111 — outdoor fan speed hypothesis

**Hypothesis:** DP111 represents outdoor-fan rotational speed.

**Suggested experiment:**

1. Record DP111 with the compressor and outdoor fan off.
2. Start cooling and heating separately.
3. Compare DP111 with audible / visual fan transitions where safely observable.
4. Repeat under different load conditions.

**Confirmation criterion:** near-zero/off values when the outdoor fan is stopped and reproducible speed changes during active refrigeration cycles.

## 13. Device compatibility research

### Current classification

| Device family | Current status | Evidence |
|---|---|---|
| UNICO EVO 25 HP PVAN (02455) | Verified reference device | E3 |
| Other OS Home-based UNICO EVO models | Candidate | E1–E2 depending on available platform evidence |
| UNICO NEXT | Candidate | E1–E2 |
| UNICO PRO | Candidate | E1–E2 |
| UNICO VERTICAL / VERTICAL-NK | Experimental candidate | E1 |
| B1015-based / legacy UNICO Wi-Fi platform | Outside current implementation | Distinct platform evidence |

### Minimum evidence required to promote another model to "verified"

A second model should not be listed as verified until the following have been demonstrated on a physical device:

1. successful local connection using the integration;
2. correct power control;
3. correct reporting of current and target temperature;
4. correct HVAC-mode mapping;
5. correct fan-mode mapping;
6. no obviously dangerous or semantically mismatched behavior from implemented writable datapoints;
7. at least one independently initiated state change reflected back into Home Assistant;
8. exact commercial model designation and, where available, internal product code recorded.

## 14. Alternative implementation and prior work

The existing project by **Daneel87 / Davide Melle**, [`Daneel87/ha-olimpia-splendid-unico`](https://github.com/Daneel87/ha-olimpia-splendid-unico), was examined as prior open-source work relevant to UNICO interoperability.

On the 02455 reference device, that implementation did not establish working communication during this project's testing. This negative result motivated an independent investigation of the OS Home / Tuya path.

This observation should not be generalized into a claim that the prior implementation is defective or incompatible with all UNICO devices; it establishes only that it did not provide working communication in the tested reference configuration.

License attribution for prior work and TinyTuya is maintained in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## 15. BLE onboarding research

### Motivation

The current credential-acquisition process requires a rooted/emulated Android environment and Frida, which is unsuitable as a normal end-user onboarding workflow.

### Research question

Can Home Assistant perform sufficient BLE discovery and/or provisioning to obtain or establish the information required for subsequent local control without instrumenting the OS Home application?

### Current status

**Not implemented.** Investigation is incomplete.

### Questions to resolve

- Which BLE services and characteristics are exposed during initial setup?
- Does the device advertise a stable model or product identifier?
- Is Wi-Fi provisioning performed entirely over BLE or through a hybrid BLE/cloud process?
- At what stage are Tuya identifiers and local credentials created or delivered?
- Can the device be provisioned without manufacturer-cloud involvement?
- Does re-provisioning rotate the Local Key?
- Are there model-specific differences in BLE onboarding?

No claim of BLE compatibility should be added to user-facing documentation until this path has been reproduced independently.

## 16. Reproducibility requirements for future test reports

A useful technical report should include, where available and safe to disclose:

- exact commercial model name;
- internal model/product code;
- integration version;
- Home Assistant version;
- OS Home version if relevant;
- firmware or Wi-Fi-module version if observable;
- protocol version used successfully;
- test mode and target temperature;
- fan mode;
- Eco / Silent state;
- relevant datapoint values before and after the controlled change;
- whether the action originated from Home Assistant, the physical remote, or OS Home;
- timestamps or elapsed time;
- number of repeated trials;
- any contradictory observation.

Credentials and identifying network data must be redacted before publication.

## 17. Standard experiment record template

Future research entries should preferably use the following structure.

```text
Experiment ID:
Date:
Researcher / reporter:
Device model:
Internal product code:
Firmware / module revision:
Integration version:
Home Assistant version:

Question:

Hypothesis:

Initial conditions:

Controlled variable:

Measured variables:

Procedure:
1.
2.
3.

Raw observations:

Repeated trials:

Result:

Interpretation:

Alternative explanations:

Evidence class before:
Evidence class after:

Follow-up experiment:
```

## 18. Criteria for changing a datapoint interpretation

A current interpretation should be downgraded or replaced when any of the following occurs:

- a controlled experiment produces repeatable behavior inconsistent with the assigned meaning;
- another physical device using the same apparent protocol produces a conflicting semantic mapping;
- independent technical evidence identifies a more plausible mapping;
- the same datapoint changes in response to a variable that should be causally unrelated to the current interpretation;
- the observed numeric domain conflicts with the proposed physical quantity under realistic operating conditions.

Contradictory results should be preserved in the research history rather than silently removed.

## 19. Open research questions

The current highest-priority unresolved questions are:

1. Which UNICO EVO, NEXT, PRO, and VERTICAL variants share the reference datapoint schema?
2. Are protocol or datapoint differences associated with specific Wi-Fi module revisions?
3. Can BLE onboarding be reproduced directly from Home Assistant?
4. What are the exact semantics of DP101, DP104, DP107, DP111, DP115, and DP117?
5. How stable is the present persistent-session strategy over multi-week operation?
6. Does Local Key rotation occur after account changes, re-pairing, firmware updates, or Wi-Fi reprovisioning?
7. Are Eco and Silent implemented as independent flags on all compatible models, or does the appliance firmware impose model-specific coupling with fan speed or other states?

## 20. Documentation policy

The project distinguishes three documentation layers:

- [`README.md`](README.md): user-facing technical overview, installation, compatibility, and high-level findings;
- [`docs/GETTING_KEYS.md`](docs/GETTING_KEYS.md): experimental credential-acquisition procedure;
- `RESEARCH.md`: evidence, hypotheses, methodology, negative results, and unresolved technical questions.

When a research conclusion becomes sufficiently well established, the concise result may be promoted into the README while the supporting observations remain here.

## 21. Research integrity and limitations

This project is an engineering reverse-engineering effort, not a formal laboratory study. The present evidence base is limited primarily by the small number of physical devices tested and by the absence of official protocol documentation.

Confidence labels therefore describe the strength of the project's current empirical evidence; they do not imply statistical significance, certification, manufacturer approval, or safety validation.

The correct response to contradictory data is to revise the interpretation, not to force new observations into an existing model.

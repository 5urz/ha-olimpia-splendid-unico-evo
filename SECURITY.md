# Security Policy

## Reporting a vulnerability

Please do **not** report security vulnerabilities or sensitive device data in a public GitHub issue.

In particular, never publish:

- Tuya Local Keys
- Tuya Device IDs
- OS Home account credentials or tokens
- Home Assistant configuration files or backups containing credentials
- unreviewed TinyTuya / Home Assistant debug logs that may contain device or protocol data

If GitHub's **Private vulnerability reporting** ("Report a vulnerability") is available for this repository, please use that channel for security reports.

If no private reporting channel is available, open a minimal public issue stating only that you would like to report a security issue privately. Do not include vulnerability details, credentials, keys, tokens, device identifiers, IP addresses, or logs in that issue.

If a Local Key or another credential has already been exposed publicly, treat it as compromised and replace/rotate it where possible before sharing any further diagnostic information.

## Scope

Security reports concerning this Home Assistant custom integration, its handling of credentials, or unintended disclosure of sensitive device data are in scope.

General compatibility problems and ordinary bugs should use the normal issue templates, after removing all sensitive data.

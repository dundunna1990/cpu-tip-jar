# CPU Tip Jar — project scope

Small, opt-in, desktop-only donation miner for 64-bit Linux and Windows.

## Hard rules
- Volunteers explicitly download the XMRig engine, accept the donation terms and confirm Start.
- Stop, timer and regular window close terminate the mining process. No autostart, stealth mode, admin prompts or remote control.
- Donation wallet is shown clearly. Mining uses electricity and sends rewards to the displayed wallet, not the volunteer.
- Verify pinned upstream XMRig hashes, keep the mining engine separate from this MIT-licensed wrapper.
- Keep the project small: one window, no login/server/analytics.
- No release should be called fully tested while Windows hands-on UI and antivirus checks are outstanding.

## Release checklist
- [x] Source includes consent, CPU thread settings, duration settings, visible Stop, hash checking and crash-stop guards.
- [x] Linux unit tests and non-mining self-test have passed on the original codebase.
- [x] Isolated Linux mining session accepted a share and stopped cleanly on 2026-10-30 (original app code).
- [x] Renamed source Linux tests and self-test passed on 2026-10-30.
- [x] Fresh downloadable Linux and Windows builds, checksum verification, and Linux release self-test (2026-10-30).
- [ ] Real Windows desktop GUI, antivirus, Start/Stop and cleanup testing.
- [ ] Real desktop fresh-install and removal check for this branded release.

See docs/TEST-REPORT.md for evidence and limits.

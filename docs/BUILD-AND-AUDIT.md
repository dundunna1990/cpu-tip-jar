# CPU Tip Jar — build and audit notes

## Design
One Python/Tkinter window for 64-bit Linux and Windows. Separate XMRig engine, downloaded only on an explicit click. Mining is opt-in, visible and directed to a disclosed public Monero address.

## Security and operating limits
- Official XMRig 6.26.0 archive and extracted executable must match embedded SHA256 hashes.
- Each start checks the local executable hash.
- No autostart, service, hidden mining, admin bypass, analytics or remote interface.
- Low/Medium/High are CPU thread settings, not precise CPU-percent limits.
- The operating system may warn about mining tools; do not bypass antivirus warnings.
- Linux uses setpriv parent-death handling; Windows uses a kill-on-close Job Object. Both should be retested on the packaged binaries.

## Verification
See TEST-REPORT.md for checked facts and remaining real-device test gaps.

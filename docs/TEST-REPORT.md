# CPU Tip Jar — test report

This project is a rebranded copy of an existing small, voluntary Monero donation miner, imported with fresh Git history. Tests below distinguish inherited evidence from new test results.

## Prior testing of the underlying code
- Source unit tests on Linux passed (14 run successfully, one Windows-only test skipped).
- Windows and Linux automated packaging and harmless process-lifecycle tests had passed in CI.
- On 2026-10-30 an isolated Linux mining test downloaded hash-verified XMRig, connected to MoneroOcean, received one accepted share (1/0, diff 10000), and stopped the miner successfully.
- These results do not prove that the renamed binaries and their graphical user interfaces work on every desktop.

## Testing of the newly branded repository
On 2026-10-30, 14 unit tests passed on Linux (one Windows-only test skipped), and the renamed application's harmless self-test passed. The new application window was opened on Linux and a screenshot captured without mining. Fresh CI builds, platform downloads and checksums still need verification.

## Unfinished acceptance
- Test the downloadable app through its complete GUI workflow.
- Test Windows graphical interface, antivirus warnings and clean removal on a real Windows computer.
- Until those are completed, publish only as a clearly labeled **preview**.

# Safety and honest limitations

**Consent** — This software is only for voluntary, informed use. It does not start mining automatically, run covertly, or install startup tasks/services. Users must explicitly install the engine and separately confirm mining each session. Do not use on employer/school devices without permission.

**Resource use** — Low/Medium/High choose thread counts, **not a guaranteed CPU percentage**. XMRig RandomX initialization may use substantial RAM and processor time, and mining can increase electricity costs, temperatures, fan noise, component wear and battery drain. Keep ventilation clear. Stop if the device feels unusually hot, sluggish or unstable. This release is desktop-only; no phone mining.

**Stopping** — STOP, timer expiry, and ordinary window-close terminate the owned miner process. The app now adds OS-level crash protection: on Linux, `setpriv --pdeathsig SIGKILL` requests kernel termination when the GUI dies; on Windows, a kill-on-close Job Object is used. Linux parent-death behavior passed a real forced-parent-kill test with a harmless fake miner. Windows has a fake-process CI test, but desktop/antivirus testing is still required. Check Task Manager or your process list after an unexpected exit rather than assuming every abnormal failure is covered. No watchdog will restart mining.

**Security** — Mining tools are often flagged by antivirus. This app never asks users to disable protection or change security policies. If your security software flags the release, don't bypass it blindly. Build from the published source and inspect dependencies, or choose a direct donation instead.

**Downloads** — Official XMRig v6.26.0 archives are downloaded only after an explicit user action from https://github.com/xmrig/xmrig/releases . The exact archive must match pinned SHA256 from upstream release SHA256SUMS. Extraction permits only the single expected xmrig binary, not arbitrary archive paths. Network download size and extracted size are capped. Although checksums prevent accidental or unexpected changes, SHA256SUMS fetched from the same upstream source is **not** independently authenticated by this wrapper's current process; do not treat checksums alone as a complete supply-chain guarantee.

**Data** — No analytics, backend, telemetry or phone-home from the wrapper. Pool mining connects to gulf.moneroocean.stream over TLS and reveals the participant's IP address to that server; upstream XMRig has a developer donation feature (configured at 1%). XMRig may create normal miner data/cache in the local user profile. The wrapper displays only reported hashrates/shares and keeps no earnings ledger.

**Limitations** — No automatic failover pool; no GPU mining; not for ARM; no payout guarantee. It must remain visible and running for long-duration donations. Linux requires `setpriv` (part of the common `util-linux` tools) for crash protection; the app fails closed if unavailable. Windows builds still need independent real-device acceptance testing, especially antivirus, full interface and abnormal-exit behavior.

**Removal** — STOP and close the app; use Remove XMRig; delete the CPUTipJar app. On Linux remove `~/.local/share/cpu-tip-jar/` if you want to clean the cache; on Windows remove `%LOCALAPPDATA%\CPUTipJar\`. No system service, scheduled task or autostart entry is installed by this project.

# AS228T upper/lower-station handshake template

Support two standard docking modes. Map the site-specific X/L addresses and 8-pin connector wiring separately; do not embed physical addresses in sequence logic.

## Mode A: upstream actively discharges, downstream receives

| Direction | Signal | Meaning |
| --- | --- | --- |
| Downstream → Upstream | `AllowUpstreamAction` | Downstream is ready for the upstream fixture/action. |
| Upstream → Downstream | `DischargeComplete` | Upstream has completed discharge/transfer. |
| Downstream → Upstream | `AllowUpstreamDischarge` | Downstream grants the actual discharge transfer. |

Typical sequence: downstream readiness → upstream preparation → downstream discharge permission → upstream discharge → upstream completion → both sides release the handshake.

## Mode B: downstream actively picks, upstream releases positioning

| Direction | Signal | Meaning |
| --- | --- | --- |
| Upstream → Downstream | `AllowDownstreamPick` | Upstream fixture permits downstream picking. |
| Downstream → Upstream | `AllowUpstreamFixtureAction` | Downstream is clear and permits the upstream fixture action. |
| Downstream → Upstream | `RequestUpstreamRelease` | Downstream requests opening/releasing the upstream positioning device. |
| Upstream → Downstream | `ReleaseComplete` | Upstream positioning release is physically complete. |

Typical sequence: upstream allows pick → downstream requests release → upstream releases and confirms feedback → upstream sends release complete → downstream picks → both sides release the handshake.

## Common rules

- Define every signal from the local PLC perspective: direction, producer, consumer, normal level, timeout, invalid state, and reset owner.
- Use held request/acknowledge levels or sequence number/echo. Do not depend on a one-scan pulse between stations.
- Capture peer signals even while the local automatic sequence is paused. A peer may not pause and its interaction must not be missed.
- Before entering a next step that starts a real actuator or pulse, require local `SequenceRunning`. Pure handshake capture/acknowledgement does not require it.
- Clear a handshake only after the opposite side has observed/acknowledged completion; define power-cycle and cable-disconnect recovery.
- Treat `N24`, `PE`, connector pin numbers, and X/L assignments as electrical/project mapping fields. Confirm them against the actual drawing; do not infer them from the generic template.
- Add timeout alarms in the central alarm module, such as “等待后站允许出料超时” or “等待前站定位松开完成超时”.

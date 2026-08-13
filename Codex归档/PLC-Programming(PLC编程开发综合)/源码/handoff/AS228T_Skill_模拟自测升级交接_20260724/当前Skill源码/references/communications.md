# AS228T communications

## Built-in interfaces

- COM1 and COM2: two RS-485 interfaces; AS Series documentation describes master/slave configuration.
- Ethernet: 10/100 M interface; AS Series documentation includes web/email/socket capabilities.
- CAN/CANopen: AS200 hardware includes a CAN interface; confirm DS301 role, node count, PDO mapping, baud rate, and CPU firmware in the current manual/HWCONFIG.
- USB: engineering/download/monitoring connection; do not treat USB simulation as field proof.

## Configuration workflow

1. identify physical port and protocol
2. define client/server or master/slave role
3. configure port/IP/node parameters in HWCONFIG
4. define read/write map, data type, byte/word order, and bounds
5. define timeout, retry, reconnect, stale-data, and write-failure behavior
6. compile and test with outputs/motion inhibited
7. monitor connection flags and application-level heartbeat/status

## Socket

The official AH/AS Socket application note documents `SOPEN` and a maximum of four configured Ethernet sockets for that revision. TCP can operate as client or server; UDP is also described. Configure IP/netmask and enable/configure sockets in HWCONFIG before instruction use.

Delta's AS Socket FAQ uses status flags including `SM1270`, `SM1273`, and `SM1274` in its example. Do not copy those flags blindly: confirm the current PM/HWCONFIG table, socket number, role, and firmware.

## Modbus TCP version gate

Delta FAQ 2467 states that when a third-party device accepts only one TCP connection, AS PLC firmware 1.12.50 or later plus `SM1037` can enable a merged single-connection mode for the data-exchange table. Apply only after confirming installed firmware and the current official description.

## Security

- Keep PLC/engineering networks segmented from the public internet.
- Restrict write ranges and validate all received lengths/values.
- Do not embed credentials in PLC logic or Skill examples.
- Define safe behavior for stale, malformed, repeated, or unauthorized commands.
- Treat remote write access to outputs, modes, setpoints, and positioning as a controlled change path.


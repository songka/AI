# AS228T overall program framework

Use this project organization for standard machines. Keep the visible POU grouping close to `Prog0..Prog4`, while making the actual task execution order place final output mapping after every request producer.

## POU groups

1. `Prog0_Main`
   - input mapping and normalized input states
   - manual/automatic mode selection
   - start, stop, reset, one-key startup
   - machine state, initialization, homing-complete summary
   - common lifecycle/data exchange
2. `Prog1_AutoSequence`
   - return/conveyor line
   - common automatic devices such as ion-air blow
   - one explicit subprogram per station, numbered in process order
   - station steps follow `-1`, `0..99`, then `100,110...`
3. `Prog2_Alarm`
   - trigger evaluation, Active, Latched, Ack/Reset handling, summary and HMI code
   - consume valve/axis/module diagnostic events; do not drive actuators
4. `Prog3_ModuleAndOutput`
   - lights, power enable and common equipment modules
   - valve FBs, axis command arbitration and station device modules
   - final logical gating and the single physical Y assignment
5. `Prog4_HMIManual`
   - selected axis/device/station
   - return-line and maintenance modes
   - station manual requests
   - controlled maintenance unlock requests
   - axis jog requests; HMI never owns physical or motion outputs

## Execution order

Required dataflow:

```text
Input mapping → main/mode → automatic sequence → alarms/diagnostics
→ HMI/manual request generation → equipment/valve/axis arbitration
→ final output mapping
```

If the project tree retains the names `Prog0, Prog1, Prog2, Prog3, Prog4`, configure the task order so `Prog3_ModuleAndOutput` executes last, or split its final output section into a final mapping POU. Do not accept a hidden one-scan delay caused by manual requests being calculated after physical outputs.

## Ownership

- Automatic and manual POUs write requests only.
- Equipment/valve/axis modules arbitrate requests and apply interlocks.
- Alarm POU reports faults and permissives but does not write actuator commands.
- Only final output mapping writes Y.

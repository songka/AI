# IO Review Rules

## Preferred Columns

- station
- device
- signal_type
- address
- tag
- description

## Naming Checks

- Tag should show station or equipment ownership.
- Tag should be readable and stable across electrical drawings, PLC code, and HMI.
- Avoid duplicate tag names and duplicate addresses.
- Avoid ambiguous names such as sensor1, valve2, ready, done without device context.

## Signal Checks

- DI: sensor, switch, ready, alarm feedback, safety feedback.
- DO: valve, relay, light, buzzer, cylinder output.
- AI/AO: analog measurement or control values.
- Safety and emergency stop signals must be flagged for engineer confirmation.

## Risk Questions

- Is every safety-related signal clearly marked?
- Are cylinder extend/retract sensors paired?
- Are alarms and reset conditions described?
- Are station ownership and device descriptions complete?

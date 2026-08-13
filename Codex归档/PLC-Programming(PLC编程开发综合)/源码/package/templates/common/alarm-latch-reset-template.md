# AS228T alarm latch/reset template

Use for process alarms, timeout alarms, permissive-loss alarms, and resettable fault states.

```st
(* Set-dominant: an active trigger cannot be cleared in the same scan. *)
IF bAlarmTrigger THEN
    bAlarmActive := TRUE;
ELSIF bAlarmResetCmd AND bResetPermissive THEN
    bAlarmActive := FALSE;
END_IF;
```

Keep trigger, latch, acknowledge, reset request, and reset permissive separate. Verify that an active source cannot be hidden by HMI acknowledgment or reset.


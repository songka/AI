# V2 routing and Agent contract

## Three layers

1. Step route selects the capability stage.
2. Category route specializes steps 3–11 for `MACHINING`, `SHEET_METAL`, `WELDMENT`, or `FRAME_ASSEMBLY`.
3. Process route specializes steps 6, 7, 10 and 11 for `CNC`, `LATHE`, `MILL`, `GRIND`, `FITTER`, `EDM`, `WIRE_CUT`, `SLOW_WIRE`, `LASER_CUT`, `BENDING`, `WELDING`, or `SURFACE`. Global process defaults are directly configurable; categories may override only selected process steps.

Fallback order is category process override → global process default → category/global step → built-in. A multi-process part may invoke multiple Skills/Agents in the same quotation; keep each process code in the request and trace, then merge results by step and process.

## Skill versus Agent

- Skill: capability contract, business workflow, references, optional commands, validation and fallback.
- Agent: reasoning role with supported steps/processes and instructions. It may be selected directly or bound by a Skill through `step_agent_routes`.
- Internal rule: deterministic parser/calculator/validator. Do not create an Agent when an exact rule is sufficient.

Skill manifest extension:

```json
{
  "supported_processes": ["MILL", "GRIND"],
  "step_agent_routes": {"TIME_ESTIMATION": "company.time-agent"}
}
```

Agent folder requires `agent.json` and `AGENT.md`:

```json
{
  "agent_id": "company.time-agent",
  "agent_name_zh": "加工工时智能体",
  "agent_version": "2.0.0",
  "protocol_version": "1.0",
  "supported_steps": ["TIME_ESTIMATION"],
  "supported_processes": ["MILL", "GRIND"],
  "instruction_file": "AGENT.md",
  "reference_files": ["references/time-rules.md"]
}
```

IDs in runtime output must match the declared manifest. A folder runtime may normalize a returned ID and issue a warning; HTTP resources must follow the protocol exactly.

## Cooperation and accuracy

Pass only the required step context plus traceable prior results. Preserve the worker's structured output rather than paraphrasing it repeatedly. Cache only exact, versioned, non-secret inputs; include Skill/Agent version, price version and rule version in the cache key. Never cache a transient failure as a successful result.

Price-audit actions may trigger a bounded re-run of affected prior steps, followed by one more audit. Reject loops, unknown actions and actions that try to alter approved source prices.

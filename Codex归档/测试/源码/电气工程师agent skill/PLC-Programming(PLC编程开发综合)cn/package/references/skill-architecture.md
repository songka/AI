<!-- 中文导读开始 -->

## 中文导读

本文件属于 references/（资料库），用于提供 skill 回答问题时需要查阅的规则、索引、术语或资料地图。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# PLC skill architecture

This file defines the boundary between the **common PLC layer** and the **vendor-specific layer**.

## Goal

Keep the skill broad enough to handle real PLC engineering work, but narrow enough to avoid turning into a low-quality "knows a little about everything" skill.

## Two-layer model

### 1. Common PLC layer

Use for knowledge that is stable across vendors or can be expressed vendor-neutrally.

This layer owns:

- IEC 61131-3 language framing
- PLC logic decomposition
- state machine / step-sequence structuring
- alarm, latch, reset, interlock patterns
- scan-cycle and output ownership reasoning
- modular program structure
- debugging workflow
- code review checklist
- input completeness handling
- response confidence downgrades
- template-first answer strategy

This layer must not claim vendor-specific syntax, memory semantics, software UI behavior, or exact instruction availability unless supported by a vendor layer.

### 2. Vendor-specific layer

Use when vendor, software, controller family, or terminology can be identified.

This layer owns:

- vendor software environment and project structure
- vendor-specific terminology mapping
- memory model / device model / tag model conventions
- instruction and language quirks
- model-family distinctions
- online debugging conventions and common pitfalls
- official document routing for that ecosystem
- vendor examples and templates where necessary

Vendor layers must not overwrite common engineering rules unless platform behavior really requires it.

## Routing rules

1. Confirm the request is about PLC/control-program work.
2. Identify whether vendor cues are present.
3. If no vendor cue is present, use the common layer and clearly label vendor-dependent details.
4. If one vendor is strongly indicated, load that vendor layer.
5. If multiple vendors appear, flag the mismatch first.
6. Do not let the existence of a mature Mitsubishi module bias every PLC request into Mitsubishi.

## Current maturity

- Common layer: active
- Mitsubishi layer: mature
- Other vendor layers: scaffolded, intentionally shallow, ready for later enrichment

## Knowledge maintenance rule

When adding new material:

- put cross-vendor engineering rules into `references/common/`
- put vendor-specific material into `references/vendors/<vendor>/`
- keep official doc indexes separate from interpreted rules
- do not duplicate the same rule in both common and vendor files unless the vendor file is explicitly narrowing or overriding the generic case

"""Versioned external quotation Skill routing shared through SMB with offline cache."""

from __future__ import annotations

import json
import hashlib
import re
import shutil
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, Field, model_validator

from quotation.application.auth_service import AuthService
from quotation.domain.user import User


class SkillStep(str, Enum):
    DOCUMENT_UNDERSTANDING = "DOCUMENT_UNDERSTANDING"
    PART_CLASSIFICATION = "PART_CLASSIFICATION"
    FEATURE_EXTRACTION = "FEATURE_EXTRACTION"
    MATERIAL_CLASSIFICATION = "MATERIAL_CLASSIFICATION"
    PROCESS_PLANNING = "PROCESS_PLANNING"
    TIME_ESTIMATION = "TIME_ESTIMATION"
    LINE_ITEM_PRICING = "LINE_ITEM_PRICING"
    UNKNOWN_ESTIMATION = "UNKNOWN_ESTIMATION"
    QUOTE_ASSEMBLY = "QUOTE_ASSEMBLY"
    PRICE_AUDIT = "PRICE_AUDIT"
    REVIEW_RECOMMENDATION = "REVIEW_RECOMMENDATION"


# These steps run before a reliable part category exists.  They must always use
# the global route; category-specific routes start at FEATURE_EXTRACTION.
PRE_CATEGORY_STEPS = frozenset(
    {
        SkillStep.DOCUMENT_UNDERSTANDING,
        SkillStep.PART_CLASSIFICATION,
    }
)


STEP_NAMES_ZH = {
    SkillStep.DOCUMENT_UNDERSTANDING: "图纸与备注理解",
    SkillStep.PART_CLASSIFICATION: "零件类别分类",
    SkillStep.FEATURE_EXTRACTION: "特征提取",
    SkillStep.MATERIAL_CLASSIFICATION: "材料判断",
    SkillStep.PROCESS_PLANNING: "工艺路线",
    SkillStep.TIME_ESTIMATION: "工时估算",
    SkillStep.LINE_ITEM_PRICING: "分项计价",
    SkillStep.UNKNOWN_ESTIMATION: "待确认项 AI 估价",
    SkillStep.QUOTE_ASSEMBLY: "报价汇总",
    SkillStep.PRICE_AUDIT: "价格审核",
    SkillStep.REVIEW_RECOMMENDATION: "人工审核建议",
}


class PartCategory(str, Enum):
    MACHINING = "MACHINING"
    SHEET_METAL = "SHEET_METAL"
    WELDMENT = "WELDMENT"
    FRAME_ASSEMBLY = "FRAME_ASSEMBLY"


CATEGORY_NAMES_ZH = {
    PartCategory.MACHINING: "加工件",
    PartCategory.SHEET_METAL: "钣金件",
    PartCategory.WELDMENT: "焊接件",
    PartCategory.FRAME_ASSEMBLY: "型材组装件",
}


class ProcessCode(str, Enum):
    CNC = "CNC"
    LATHE = "LATHE"
    MILL = "MILL"
    GRIND = "GRIND"
    FITTER = "FITTER"
    EDM = "EDM"
    WIRE_CUT = "WIRE_CUT"
    SLOW_WIRE = "SLOW_WIRE"
    LASER_CUT = "LASER_CUT"
    BENDING = "BENDING"
    WELDING = "WELDING"
    SURFACE = "SURFACE"


PROCESS_NAMES_ZH = {
    ProcessCode.CNC: "CNC/加工中心",
    ProcessCode.LATHE: "车床",
    ProcessCode.MILL: "铣床",
    ProcessCode.GRIND: "磨床",
    ProcessCode.FITTER: "钳工",
    ProcessCode.EDM: "放电",
    ProcessCode.WIRE_CUT: "快丝/线切割",
    ProcessCode.SLOW_WIRE: "慢丝",
    ProcessCode.LASER_CUT: "激光切割",
    ProcessCode.BENDING: "折弯",
    ProcessCode.WELDING: "焊接",
    ProcessCode.SURFACE: "表面处理",
}


PROCESS_ROUTABLE_STEPS = frozenset(
    {
        SkillStep.TIME_ESTIMATION,
        SkillStep.LINE_ITEM_PRICING,
        SkillStep.PRICE_AUDIT,
        SkillStep.REVIEW_RECOMMENDATION,
    }
)


class SkillRoutingMode(str, Enum):
    FULL_QUOTATION = "FULL_QUOTATION"
    DISTRIBUTED = "DISTRIBUTED"


class SkillSourceType(str, Enum):
    BUILTIN = "BUILTIN"
    HTTP = "HTTP"
    FOLDER = "FOLDER"


class AgentSourceType(str, Enum):
    BUILTIN = "BUILTIN"
    HTTP = "HTTP"
    FOLDER = "FOLDER"


class SkillCommandKind(str, Enum):
    PYTHON = "PYTHON"
    EXECUTABLE = "EXECUTABLE"
    CLI = "CLI"
    BATCH = "BATCH"


class SkillTaskType(str, Enum):
    QUOTATION = "QUOTATION"
    BATCH_TASK = "BATCH_TASK"
    EXCEL_EXPORT = "EXCEL_EXPORT"
    EXCEL_READ = "EXCEL_READ"
    EXCEL_WRITE = "EXCEL_WRITE"
    EXCEL_MODIFY = "EXCEL_MODIFY"


class SkillCommandCapability(BaseModel):
    command_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{1,63}$")
    name_zh: str = Field(min_length=1, max_length=100)
    kind: SkillCommandKind
    task_types: list[SkillTaskType]
    command: list[str] = Field(min_length=1)
    supported_steps: list[SkillStep] = Field(default_factory=list)
    timeout_seconds: int = Field(default=60, ge=5, le=600)
    requirements: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_tasks(self):
        if SkillTaskType.QUOTATION in self.task_types and not self.supported_steps:
            raise ValueError("报价执行命令必须声明 supported_steps")
        return self


class ExternalSkillDefinition(BaseModel):
    skill_id: str = Field(pattern=r"^[a-z0-9][a-z0-9.-]{2,63}$")
    name_zh: str = Field(min_length=1, max_length=100)
    endpoint: str = Field(min_length=1, description="HTTP 地址或本地/SMB Skill 文件夹")
    source_type: SkillSourceType = SkillSourceType.HTTP
    skill_version: str
    protocol_version: str = "1.0"
    supported_steps: list[SkillStep]
    supports_full_quotation: bool = False
    supports_excel_export: bool = False
    excel_export_command: list[str] = Field(default_factory=list)
    excel_export_timeout_seconds: int = Field(default=60, ge=5, le=300)
    execution_requirements: list[str] = Field(default_factory=list)
    command_capabilities: list[SkillCommandCapability] = Field(default_factory=list)
    supported_processes: list[ProcessCode] = Field(default_factory=list)
    step_agent_routes: dict[SkillStep, str] = Field(default_factory=dict)
    description_zh: str = ""
    instruction_content_zh: str = ""
    enabled: bool = True

    @model_validator(mode="after")
    def validate_source(self):
        value = self.endpoint.strip()
        if self.source_type == SkillSourceType.HTTP and not value.casefold().startswith(
            ("http://", "https://")
        ):
            raise ValueError("HTTP Skill 必须使用 http:// 或 https:// 地址")
        if self.source_type == SkillSourceType.FOLDER and not value:
            raise ValueError("文件夹 Skill 必须指定本地或 SMB 文件夹")
        self.endpoint = value.rstrip("/") if self.source_type == SkillSourceType.HTTP else value
        if self.supports_excel_export:
            if self.source_type != SkillSourceType.FOLDER:
                raise ValueError("Excel 导出 Skill 当前只支持受管理员发布的文件夹 Skill")
            has_command_export = any(
                SkillTaskType.EXCEL_EXPORT in item.task_types
                for item in self.command_capabilities
            )
            if not self.excel_export_command and not has_command_export:
                raise ValueError("Excel 导出 Skill 必须声明 excel_export.command")
        if self.command_capabilities and self.source_type != SkillSourceType.FOLDER:
            raise ValueError("可执行 commands 当前只支持管理员发布的文件夹 Skill")
        command_ids = [item.command_id for item in self.command_capabilities]
        if len(command_ids) != len(set(command_ids)):
            raise ValueError("Skill commands 的 command_id 不能重复")
        return self


def _builtin_skill(
    step: SkillStep,
    name_zh: str,
    description_zh: str,
    instruction_content_zh: str,
    *,
    supported_processes: list[ProcessCode] | None = None,
) -> ExternalSkillDefinition:
    """Build a read-only catalog entry for one built-in pipeline capability."""
    slug = step.value.casefold().replace("_", "-")
    return ExternalSkillDefinition(
        skill_id=f"builtin.{slug}",
        name_zh=name_zh,
        endpoint=f"builtin://quotation/{slug}",
        source_type=SkillSourceType.BUILTIN,
        skill_version="2.0.0",
        supported_steps=[step],
        supported_processes=supported_processes or [],
        description_zh=description_zh,
        instruction_content_zh=instruction_content_zh,
    )


BUILTIN_SKILLS = (
    _builtin_skill(
        SkillStep.DOCUMENT_UNDERSTANDING,
        "内置图纸与备注理解 Skill",
        "提取图纸文字、数量、特殊要求、冲突和风险。",
        "保留原始证据；区分件、kg、mm、小时。证据不足时输出待确认项，不臆造内容。",
    ),
    _builtin_skill(
        SkillStep.PART_CLASSIFICATION,
        "内置零件类别分类 Skill",
        "将零件分类为加工件、钣金件、焊接件或型材组装件。",
        "依据几何、材料和制造特征分类并给出置信度；本步骤始终使用全局路由。",
    ),
    _builtin_skill(
        SkillStep.FEATURE_EXTRACTION,
        "内置制造特征提取 Skill",
        "提取外形、孔、螺纹、槽、框架、焊缝和表面处理等制造特征。",
        "仅输出有图纸证据的特征；同时保留尺寸、数量、来源和不确定性。",
    ),
    _builtin_skill(
        SkillStep.MATERIAL_CLASSIFICATION,
        "内置材料判断 Skill",
        "规范材料牌号并判断材料大类。",
        "优先采用图纸明确牌号；模糊或冲突时保留原文并要求人工确认。",
    ),
    _builtin_skill(
        SkillStep.PROCESS_PLANNING,
        "内置工艺路线 Skill",
        "根据零件类别和制造特征规划必要工艺。",
        "允许车、铣、磨、钳工、放电、线切割、激光、折弯、焊接和表面处理，不默认只选 CNC。",
        supported_processes=list(ProcessCode),
    ),
    _builtin_skill(
        SkillStep.TIME_ESTIMATION,
        "内置工时估算 Skill",
        "按具体工艺估算单件准备、装夹、加工和检验工时。",
        "结合尺寸、特征数量、精度和批量估算；异常高值必须降置信度并转人工审核。",
        supported_processes=list(ProcessCode),
    ),
    _builtin_skill(
        SkillStep.LINE_ITEM_PRICING,
        "内置分项计价 Skill",
        "按材料、加工、表面处理和其他费用逐项计算。",
        "公司正式价格优先；AI 参考价不得覆盖正式价格，每行保留数量、单位、单价和来源。",
        supported_processes=list(ProcessCode),
    ),
    _builtin_skill(
        SkillStep.UNKNOWN_ESTIMATION,
        "内置待确认项 AI 估价 Skill",
        "仅对缺少正式价格的待确认费用提供参考估价。",
        "所有 AI 金额标记 AI_REFERENCE 和 requires_review=true，并保留假设与置信度。",
    ),
    _builtin_skill(
        SkillStep.QUOTE_ASSEMBLY,
        "内置报价汇总 Skill",
        "汇总正式报价明细、税额、未税和含税总价。",
        "避免重复计费；整件模型参考价不计入正式合计；Decimal 金额统一规范化输出。",
    ),
    _builtin_skill(
        SkillStep.PRICE_AUDIT,
        "内置价格审核 Skill",
        "检查重量、件数、工时、重复计费、价格来源和异常金额。",
        "输出 verdict、issues、actions 和 confidence；actions 必须可定位到需重算的前序步骤。",
        supported_processes=list(ProcessCode),
    ),
    _builtin_skill(
        SkillStep.REVIEW_RECOMMENDATION,
        "内置人工审核建议 Skill",
        "根据证据缺口、AI 参考项和审核结论生成可执行的人工复核清单。",
        "说明需要复核的字段、原因和建议动作，不修改正式报价。",
        supported_processes=list(ProcessCode),
    ),
)


class AgentDefinition(BaseModel):
    agent_id: str = Field(pattern=r"^[a-z0-9][a-z0-9.-]{2,63}$")
    name_zh: str = Field(min_length=1, max_length=100)
    source_type: AgentSourceType
    endpoint: str = "builtin://quotation"
    agent_version: str = "1.0.0"
    protocol_version: str = "1.0"
    supported_steps: list[SkillStep]
    supported_processes: list[ProcessCode] = Field(default_factory=list)
    description_zh: str = ""
    instruction_content_zh: str = ""
    instruction_file: str = "AGENT.md"
    reference_files: list[str] = Field(default_factory=list)
    enabled: bool = True

    @model_validator(mode="after")
    def validate_source(self):
        value = self.endpoint.strip()
        if self.source_type == AgentSourceType.HTTP and not value.casefold().startswith(
            ("http://", "https://")
        ):
            raise ValueError("HTTP 智能体必须使用 http:// 或 https:// 地址")
        if self.source_type == AgentSourceType.FOLDER and not value:
            raise ValueError("文件夹智能体必须指定本地或 SMB 文件夹")
        if self.source_type == AgentSourceType.BUILTIN and not value.startswith("builtin://"):
            raise ValueError("内置智能体必须使用 builtin:// 地址")
        self.endpoint = value.rstrip("/") if self.source_type == AgentSourceType.HTTP else value
        return self


BUILTIN_AGENTS = (
    AgentDefinition(
        agent_id="builtin.note-understanding",
        name_zh="内置备注理解智能体",
        source_type=AgentSourceType.BUILTIN,
        supported_steps=[SkillStep.DOCUMENT_UNDERSTANDING],
        description_zh="读取图纸原始文字，提取数量、特殊要求、风险与冲突，不覆盖原文证据。",
        instruction_content_zh=(
            "输入为图纸提取文字及来源证据。输出 summary、requirements、risks、"
            "confidence；数量单位必须区分件、kg、mm、小时，不得把材料重量当成零件数量。"
            "证据不足时明确列为待确认，不臆造图纸内容。"
        ),
    ),
    AgentDefinition(
        agent_id="builtin.part-classification",
        name_zh="内置零件分类智能体",
        source_type=AgentSourceType.BUILTIN,
        supported_steps=[SkillStep.PART_CLASSIFICATION],
        description_zh="在加工件、钣金件、焊接件、型材组装件之间分类，低可信度时规则回退。",
        instruction_content_zh=(
            "仅在 MACHINING、SHEET_METAL、WELDMENT、FRAME_ASSEMBLY 中选择类别，"
            "返回置信度、证据和候选类别。此步骤发生在类别路由之前，因此始终走全局路由。"
        ),
    ),
    AgentDefinition(
        agent_id="builtin.process-planning",
        name_zh="内置工艺规划智能体",
        source_type=AgentSourceType.BUILTIN,
        supported_steps=[SkillStep.PROCESS_PLANNING, SkillStep.TIME_ESTIMATION],
        supported_processes=list(ProcessCode),
        description_zh="基于图纸证据选择必要工艺并给出单件工时，随后接受内部合理性校验。",
        instruction_content_zh=(
            "先根据类别、材料、尺寸、孔槽螺纹和公差选择必要工艺；允许车、铣、磨、钳工、"
            "放电、快丝、慢丝、激光、折弯、焊接和表面处理，不得默认只给 CNC/铣床。"
            "工时按单件估算并分解装夹、加工、检验，异常高值由规则上限校验并转人工审核。"
        ),
    ),
    AgentDefinition(
        agent_id="builtin.unknown-estimation",
        name_zh="内置待确认项估价智能体",
        source_type=AgentSourceType.BUILTIN,
        supported_steps=[SkillStep.UNKNOWN_ESTIMATION],
        description_zh="仅对没有正式价格的费用项提供 AI 参考估价，并强制人工审核标记。",
        instruction_content_zh=(
            "只处理正式价格无法解析的待确认费用行。AI 金额必须标记 AI_REFERENCE、"
            "requires_review=true，并保留假设和置信度；不得覆盖公司正式价格。"
        ),
    ),
    AgentDefinition(
        agent_id="builtin.price-audit",
        name_zh="内置价格审核智能体",
        source_type=AgentSourceType.BUILTIN,
        supported_steps=[SkillStep.PRICE_AUDIT],
        supported_processes=list(ProcessCode),
        description_zh="审核材料数量、工时、重复计费、正式价格引用和异常金额。",
        instruction_content_zh=(
            "检查材料重量与件数单位、工时合理性、重复工序、遗漏费用及正式价格来源。"
            "输出 verdict、issues、actions、confidence；actions 必须是可执行的重算指令，"
            "主流程在受控次数内重新执行受影响的前序步骤后再次审核。"
        ),
    ),
)


class StepRoute(BaseModel):
    provider: str = "builtin"
    agent_id: str | None = None


class ProcessSkillRouting(BaseModel):
    step_routes: dict[SkillStep, StepRoute] = Field(default_factory=dict)


class CategorySkillRouting(BaseModel):
    mode: SkillRoutingMode = SkillRoutingMode.DISTRIBUTED
    full_skill_id: str | None = None
    step_routes: dict[SkillStep, StepRoute] = Field(default_factory=dict)
    process_routes: dict[ProcessCode, ProcessSkillRouting] = Field(default_factory=dict)


class ExternalSkillRoutingConfig(BaseModel):
    schema_version: str = "2.0"
    config_version: int = Field(default=1, ge=1)
    mode: SkillRoutingMode = SkillRoutingMode.DISTRIBUTED
    skills: list[ExternalSkillDefinition] = Field(default_factory=list)
    agents: list[AgentDefinition] = Field(default_factory=list)
    full_skill_id: str | None = None
    step_routes: dict[SkillStep, StepRoute] = Field(default_factory=dict)
    process_routes: dict[ProcessCode, ProcessSkillRouting] = Field(default_factory=dict)
    category_routes: dict[PartCategory, CategorySkillRouting] = Field(default_factory=dict)
    debug_mode: bool = False
    excel_export_skill_id: str | None = None
    updated_at: str | None = None
    updated_by: str | None = None

    @model_validator(mode="after")
    def validate_routes(self):
        skills = {item.skill_id: item for item in self.skills if item.enabled}
        agents = {item.agent_id: item for item in (*BUILTIN_AGENTS, *self.agents) if item.enabled}
        if len(skills) != len([item for item in self.skills if item.enabled]):
            raise ValueError("启用的 Skill ID 不能重复")
        builtin_skill_ids = {item.skill_id for item in BUILTIN_SKILLS}
        if builtin_skill_ids.intersection(skills):
            raise ValueError("外接 Skill ID 不能占用内置 Skill ID")
        external_agents = [item for item in self.agents if item.enabled]
        if len({item.agent_id for item in external_agents}) != len(external_agents):
            raise ValueError("启用的外挂智能体 ID 不能重复")
        builtin_ids = {item.agent_id for item in BUILTIN_AGENTS}
        if builtin_ids.intersection(item.agent_id for item in external_agents):
            raise ValueError("外挂智能体 ID 不能占用内置智能体 ID")
        if set(skills).intersection(agents):
            raise ValueError("Skill ID 与智能体 ID 不能重复")
        for skill in skills.values():
            unknown_steps = set(skill.step_agent_routes) - set(skill.supported_steps)
            if unknown_steps:
                names = "、".join(STEP_NAMES_ZH[step] for step in unknown_steps)
                raise ValueError(f"Skill“{skill.name_zh}”为未支持步骤指定了智能体：{names}")
            for step, agent_id in skill.step_agent_routes.items():
                agent = agents.get(agent_id)
                if agent is None or step not in agent.supported_steps:
                    raise ValueError(
                        f"Skill“{skill.name_zh}”为步骤“{STEP_NAMES_ZH[step]}”"
                        "指定了不存在或不兼容的智能体"
                    )
        self._validate_one_route(
            skills,
            agents,
            self.mode,
            self.full_skill_id,
            self.step_routes,
            "全局默认",
        )
        if self.mode == SkillRoutingMode.FULL_QUOTATION and self.process_routes:
            raise ValueError("全局整套报价模式不能配置具体工艺路由")
        for process, process_route in self.process_routes.items():
            self._validate_process_route(
                skills, agents, process, process_route, "全局默认"
            )
        for category, route in self.category_routes.items():
            invalid_pre_steps = PRE_CATEGORY_STEPS.intersection(route.step_routes)
            if invalid_pre_steps:
                names = "、".join(STEP_NAMES_ZH[step] for step in SkillStep if step in invalid_pre_steps)
                raise ValueError(
                    f"{names}是路由前置步骤，属于零件分类前的全局步骤，"
                    "只能在全局默认中配置"
                )
            self._validate_one_route(
                skills,
                agents,
                route.mode,
                route.full_skill_id,
                route.step_routes,
                CATEGORY_NAMES_ZH[category],
            )
            if route.mode == SkillRoutingMode.FULL_QUOTATION and route.process_routes:
                raise ValueError(
                    f"{CATEGORY_NAMES_ZH[category]}整套报价模式不能配置具体工艺路由"
                )
            for process, process_route in route.process_routes.items():
                self._validate_process_route(
                    skills, agents, process, process_route, CATEGORY_NAMES_ZH[category]
                )
        if self.excel_export_skill_id is not None:
            export_skill = skills.get(self.excel_export_skill_id)
            if export_skill is None or not export_skill.supports_excel_export:
                raise ValueError("Excel 导出只能选择已启用且声明导出能力的 Skill")
        return self

    @staticmethod
    def _validate_process_route(skills, agents, process, process_route, label):
        invalid = set(process_route.step_routes) - PROCESS_ROUTABLE_STEPS
        if invalid:
            names = "、".join(STEP_NAMES_ZH[step] for step in invalid)
            raise ValueError(f"具体工艺路由不能接管步骤：{names}")
        ExternalSkillRoutingConfig._validate_step_routes(
            skills,
            agents,
            process_route.step_routes,
            f"{label} / {PROCESS_NAMES_ZH[process]}",
            process,
        )

    @staticmethod
    def _validate_one_route(skills, agents, mode, full_skill_id, step_routes, label):
        if mode == SkillRoutingMode.FULL_QUOTATION:
            if not full_skill_id:
                raise ValueError(f"{label}整套报价模式必须选择一个 Skill")
            selected = skills.get(full_skill_id)
            if selected is None or not selected.supports_full_quotation:
                raise ValueError(f"{label}整套报价只能选择已启用且声明支持整套报价的 Skill")
            if step_routes:
                raise ValueError(f"{label}整套报价模式不能同时配置分步路由")
        else:
            if full_skill_id is not None:
                raise ValueError(f"{label}分步模式不能设置整套报价 Skill")
            ExternalSkillRoutingConfig._validate_step_routes(
                skills, agents, step_routes, label
            )

    @staticmethod
    def _validate_step_routes(skills, agents, step_routes, label, process=None):
        for step, route in step_routes.items():
            if route.provider == "builtin":
                if route.agent_id:
                    agent = agents.get(route.agent_id)
                    if agent is None:
                        raise ValueError(f"{label}引用了不存在的智能体 {route.agent_id}")
                    if step not in agent.supported_steps:
                        raise ValueError(
                            f"{label}为步骤“{STEP_NAMES_ZH[step]}”选择了不兼容的智能体"
                        )
                    if (
                        process is not None
                        and agent.supported_processes
                        and process not in agent.supported_processes
                    ):
                        raise ValueError(f"{label}选择的智能体不支持该具体工艺")
                continue
            selected_skill = skills.get(route.provider)
            selected_agent = agents.get(route.provider)
            if selected_skill is None and selected_agent is None:
                raise ValueError(f"{label}步骤“{STEP_NAMES_ZH[step]}”引用了未启用的执行资源")
            supported_steps = (
                selected_skill.supported_steps if selected_skill else selected_agent.supported_steps
            )
            if step not in supported_steps:
                raise ValueError(f"{label}执行资源不支持步骤“{STEP_NAMES_ZH[step]}”")
            agent_id = route.agent_id or (
                selected_skill.step_agent_routes.get(step) if selected_skill else None
            )
            if agent_id:
                agent = agents.get(agent_id)
                if agent is None or step not in agent.supported_steps:
                    raise ValueError(f"{label}为步骤“{STEP_NAMES_ZH[step]}”选择了不兼容的智能体")
                if (
                    process is not None
                    and agent.supported_processes
                    and process not in agent.supported_processes
                ):
                    raise ValueError(f"{label}选择的智能体不支持该具体工艺")
            if process is not None:
                resource_processes = (
                    selected_skill.supported_processes
                    if selected_skill else selected_agent.supported_processes
                )
                if resource_processes and process not in resource_processes:
                    raise ValueError(f"{label}选择的执行资源不支持该具体工艺")

    def route_for(self, category: PartCategory | None = None) -> CategorySkillRouting:
        global_route = CategorySkillRouting(
            mode=self.mode,
            full_skill_id=self.full_skill_id,
            step_routes=self.step_routes,
            process_routes=self.process_routes,
        )
        if category is None or category not in self.category_routes:
            return global_route
        selected = self.category_routes[category]
        if selected.mode == SkillRoutingMode.FULL_QUOTATION:
            return selected
        merged_processes = {
            process: route.model_copy(deep=True)
            for process, route in global_route.process_routes.items()
        }
        for process, route in selected.process_routes.items():
            inherited_steps = (
                merged_processes.get(process, ProcessSkillRouting()).step_routes
            )
            merged_processes[process] = ProcessSkillRouting(
                step_routes={**inherited_steps, **route.step_routes}
            )
        return CategorySkillRouting(
            mode=selected.mode,
            full_skill_id=selected.full_skill_id,
            step_routes=selected.step_routes,
            process_routes=merged_processes,
        )

    def provider_for(self, step: SkillStep, category: PartCategory | None = None) -> str:
        route = (
            CategorySkillRouting(
                mode=self.mode,
                full_skill_id=self.full_skill_id,
                step_routes=self.step_routes,
            )
            if step in PRE_CATEGORY_STEPS
            else self.route_for(category)
        )
        if route.mode == SkillRoutingMode.FULL_QUOTATION:
            return route.full_skill_id or "builtin"
        return route.step_routes.get(step, StepRoute()).provider

    def route_for_process(
        self,
        step: SkillStep,
        category: PartCategory | None,
        process: ProcessCode | None,
    ) -> StepRoute:
        route = self.route_for(category)
        if (
            process is not None
            and step in PROCESS_ROUTABLE_STEPS
            and process in route.process_routes
        ):
            specific = route.process_routes[process].step_routes.get(step)
            if specific is not None:
                return specific
        return route.step_routes.get(step, StepRoute())


class ExternalSkillSettingsStore:
    """SMB-primary JSON store; tests can disable SMB and use cache only."""

    def __init__(
        self,
        primary_path: str | Path,
        cache_path: str | Path,
        *,
        sync_enabled: bool = True,
    ) -> None:
        self.primary_path = Path(primary_path)
        self.cache_path = Path(cache_path)
        self.sync_enabled = sync_enabled
        self.last_source = "default"

    def load(self) -> ExternalSkillRoutingConfig:
        if self.sync_enabled:
            try:
                if self.primary_path.is_file():
                    config = self._read(self.primary_path)
                    self._atomic_copy(self.primary_path, self.cache_path)
                    self.last_source = "smb"
                    return config
            except (OSError, ValueError):
                pass
        try:
            if self.cache_path.is_file():
                self.last_source = "cache"
                return self._read(self.cache_path)
        except (OSError, ValueError):
            pass
        self.last_source = "default"
        return ExternalSkillRoutingConfig()

    def save(self, config: ExternalSkillRoutingConfig) -> Path:
        payload = config.model_dump(mode="json")
        if self.sync_enabled:
            self._atomic_write(self.primary_path, payload)
            self._atomic_copy(self.primary_path, self.cache_path)
            self.last_source = "smb"
            return self.primary_path
        self._atomic_write(self.cache_path, payload)
        self.last_source = "cache-test"
        return self.cache_path

    @staticmethod
    def _read(path: Path) -> ExternalSkillRoutingConfig:
        return ExternalSkillRoutingConfig.model_validate_json(
            path.read_text(encoding="utf-8")
        )

    @staticmethod
    def _atomic_write(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(path)

    @staticmethod
    def _atomic_copy(source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        shutil.copy2(source, temporary)
        temporary.replace(destination)


class ExternalSkillSettingsService:
    def __init__(
        self,
        store: ExternalSkillSettingsStore,
        auth_service: AuthService,
        now_provider: Callable[[], datetime] | None = None,
        asset_root: str | Path | None = None,
        agent_asset_root: str | Path | None = None,
    ) -> None:
        self.store = store
        self.auth = auth_service
        self._now = now_provider or (lambda: datetime.now(timezone.utc))
        self.asset_root = Path(asset_root) if asset_root is not None else None
        self.agent_asset_root = (
            Path(agent_asset_root) if agent_asset_root is not None else None
        )

    def get(self, actor: User) -> ExternalSkillRoutingConfig:
        self.auth.require_permission(actor, "system.config")
        return self.store.load()

    def save(
        self, actor: User, config: ExternalSkillRoutingConfig
    ) -> ExternalSkillRoutingConfig:
        self.auth.require_permission(actor, "system.config")
        current = self.store.load()
        published_skills = [self._publish_folder_skill(skill) for skill in config.skills]
        published_agents = [self._publish_folder_agent(agent) for agent in config.agents]
        changed = config.model_copy(
            update={
                "skills": published_skills,
                "agents": published_agents,
                "config_version": current.config_version + 1,
                "updated_at": self._now().isoformat(),
                "updated_by": actor.user_id,
            }
        )
        changed = ExternalSkillRoutingConfig.model_validate(
            changed.model_dump(mode="json")
        )
        self.store.save(changed)
        return changed

    def _publish_folder_skill(
        self, skill: ExternalSkillDefinition
    ) -> ExternalSkillDefinition:
        if skill.source_type != SkillSourceType.FOLDER or self.asset_root is None:
            return skill
        source = Path(skill.endpoint)
        if not source.is_dir():
            raise ValueError(f"Skill 文件夹不存在或无法读取：{source}")
        safe_version = re.sub(r"[^A-Za-z0-9._-]+", "_", skill.skill_version).strip("._")
        if not safe_version:
            raise ValueError(f"Skill“{skill.name_zh}”版本号不能用于公共槽目录")
        destination = self.asset_root / skill.skill_id / safe_version
        try:
            if source.resolve() == destination.resolve():
                return skill.model_copy(update={"endpoint": str(destination)})
        except OSError:
            pass
        source_digest, total_bytes = self._folder_digest(source)
        if total_bytes > 100 * 1024 * 1024:
            raise ValueError(f"Skill“{skill.name_zh}”文件夹超过 100 MB，不能发布")
        if destination.exists():
            destination_digest, _ = self._folder_digest(destination)
            if destination_digest != source_digest:
                raise ValueError(
                    f"公共槽已存在 {skill.skill_id} {skill.skill_version}，但内容不同；"
                    "请提升 skill_version 后再发布"
                )
        else:
            staging = destination.with_name(destination.name + ".publishing")
            if staging.exists():
                shutil.rmtree(staging)
            staging.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, staging, symlinks=False)
            staging.replace(destination)
        return skill.model_copy(update={"endpoint": str(destination)})

    def _publish_folder_agent(self, agent: AgentDefinition) -> AgentDefinition:
        if agent.source_type != AgentSourceType.FOLDER or self.agent_asset_root is None:
            return agent
        source = Path(agent.endpoint)
        if not source.is_dir():
            raise ValueError(f"智能体文件夹不存在或无法读取：{source}")
        safe_version = re.sub(r"[^A-Za-z0-9._-]+", "_", agent.agent_version).strip("._")
        if not safe_version:
            raise ValueError(f"智能体“{agent.name_zh}”版本号不能用于公共槽目录")
        destination = self.agent_asset_root / agent.agent_id / safe_version
        try:
            if source.resolve() == destination.resolve():
                return agent.model_copy(update={"endpoint": str(destination)})
        except OSError:
            pass
        source_digest, total_bytes = self._folder_digest(source)
        if total_bytes > 100 * 1024 * 1024:
            raise ValueError(f"智能体“{agent.name_zh}”文件夹超过 100 MB，不能发布")
        if destination.exists():
            destination_digest, _ = self._folder_digest(destination)
            if destination_digest != source_digest:
                raise ValueError(
                    f"公共槽已存在 {agent.agent_id} {agent.agent_version}，但内容不同；"
                    "请提升 agent_version 后再发布"
                )
        else:
            staging = destination.with_name(destination.name + ".publishing")
            if staging.exists():
                shutil.rmtree(staging)
            staging.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, staging, symlinks=False)
            staging.replace(destination)
        return agent.model_copy(update={"endpoint": str(destination)})

    @staticmethod
    def _folder_digest(folder: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        total = 0
        files = sorted(path for path in folder.rglob("*") if path.is_file())
        for path in files:
            if path.is_symlink():
                raise ValueError("Skill 文件夹不能包含符号链接")
            relative = path.relative_to(folder).as_posix()
            data = path.read_bytes()
            total += len(data)
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(data)
        return digest.hexdigest(), total


def build_external_skill_settings_service(
    settings: dict,
    auth_service: AuthService,
    *,
    sync_enabled: bool = True,
) -> ExternalSkillSettingsService:
    primary = Path(settings["smb_root"]) / "data" / "external-skill-routing.json"
    cache = Path(settings["smb_cache_dir"]) / "data" / "external-skill-routing.json"
    return ExternalSkillSettingsService(
        ExternalSkillSettingsStore(primary, cache, sync_enabled=sync_enabled),
        auth_service,
        asset_root=primary.parent / "external-skills",
        agent_asset_root=primary.parent / "external-agents",
    )

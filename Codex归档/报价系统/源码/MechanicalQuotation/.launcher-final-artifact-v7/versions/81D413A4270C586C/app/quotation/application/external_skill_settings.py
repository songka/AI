"""Versioned external quotation Skill routing shared through SMB with offline cache."""

from __future__ import annotations

import json
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
    FEATURE_EXTRACTION = "FEATURE_EXTRACTION"
    MATERIAL_CLASSIFICATION = "MATERIAL_CLASSIFICATION"
    PROCESS_PLANNING = "PROCESS_PLANNING"
    TIME_ESTIMATION = "TIME_ESTIMATION"
    LINE_ITEM_PRICING = "LINE_ITEM_PRICING"
    UNKNOWN_ESTIMATION = "UNKNOWN_ESTIMATION"
    PRICE_AUDIT = "PRICE_AUDIT"
    REVIEW_RECOMMENDATION = "REVIEW_RECOMMENDATION"
    QUOTE_ASSEMBLY = "QUOTE_ASSEMBLY"


STEP_NAMES_ZH = {
    SkillStep.DOCUMENT_UNDERSTANDING: "图纸与备注理解",
    SkillStep.FEATURE_EXTRACTION: "特征提取与零件分类",
    SkillStep.MATERIAL_CLASSIFICATION: "材料判断",
    SkillStep.PROCESS_PLANNING: "工艺路线",
    SkillStep.TIME_ESTIMATION: "工时估算",
    SkillStep.LINE_ITEM_PRICING: "分项计价",
    SkillStep.UNKNOWN_ESTIMATION: "待确认项 AI 估价",
    SkillStep.PRICE_AUDIT: "价格审核",
    SkillStep.REVIEW_RECOMMENDATION: "人工审核建议",
    SkillStep.QUOTE_ASSEMBLY: "报价汇总",
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


class SkillRoutingMode(str, Enum):
    FULL_QUOTATION = "FULL_QUOTATION"
    DISTRIBUTED = "DISTRIBUTED"


class SkillSourceType(str, Enum):
    HTTP = "HTTP"
    FOLDER = "FOLDER"


class ExternalSkillDefinition(BaseModel):
    skill_id: str = Field(pattern=r"^[a-z0-9][a-z0-9.-]{2,63}$")
    name_zh: str = Field(min_length=1, max_length=100)
    endpoint: str = Field(min_length=1, description="HTTP 地址或本地/SMB Skill 文件夹")
    source_type: SkillSourceType = SkillSourceType.HTTP
    skill_version: str
    protocol_version: str = "1.0"
    supported_steps: list[SkillStep]
    supports_full_quotation: bool = False
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
        return self


class StepRoute(BaseModel):
    provider: str = "builtin"


class CategorySkillRouting(BaseModel):
    mode: SkillRoutingMode = SkillRoutingMode.DISTRIBUTED
    full_skill_id: str | None = None
    step_routes: dict[SkillStep, StepRoute] = Field(default_factory=dict)


class ExternalSkillRoutingConfig(BaseModel):
    schema_version: str = "1.1"
    config_version: int = Field(default=1, ge=1)
    mode: SkillRoutingMode = SkillRoutingMode.DISTRIBUTED
    skills: list[ExternalSkillDefinition] = Field(default_factory=list)
    full_skill_id: str | None = None
    step_routes: dict[SkillStep, StepRoute] = Field(default_factory=dict)
    category_routes: dict[PartCategory, CategorySkillRouting] = Field(default_factory=dict)
    debug_mode: bool = False
    updated_at: str | None = None
    updated_by: str | None = None

    @model_validator(mode="after")
    def validate_routes(self):
        skills = {item.skill_id: item for item in self.skills if item.enabled}
        if len(skills) != len([item for item in self.skills if item.enabled]):
            raise ValueError("启用的 Skill ID 不能重复")
        self._validate_one_route(
            skills,
            self.mode,
            self.full_skill_id,
            self.step_routes,
            "全局默认",
        )
        for category, route in self.category_routes.items():
            self._validate_one_route(
                skills,
                route.mode,
                route.full_skill_id,
                route.step_routes,
                CATEGORY_NAMES_ZH[category],
            )
        return self

    @staticmethod
    def _validate_one_route(skills, mode, full_skill_id, step_routes, label):
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
            for step, route in step_routes.items():
                if route.provider == "builtin":
                    continue
                selected = skills.get(route.provider)
                if selected is None:
                    raise ValueError(
                        f"{label}步骤“{STEP_NAMES_ZH[step]}”引用了未启用的 Skill"
                    )
                if step not in selected.supported_steps:
                    raise ValueError(
                        f"{label} Skill“{selected.name_zh}”不支持步骤“{STEP_NAMES_ZH[step]}”"
                    )

    def route_for(self, category: PartCategory | None = None) -> CategorySkillRouting:
        if category is not None and category in self.category_routes:
            return self.category_routes[category]
        return CategorySkillRouting(
            mode=self.mode,
            full_skill_id=self.full_skill_id,
            step_routes=self.step_routes,
        )

    def provider_for(self, step: SkillStep, category: PartCategory | None = None) -> str:
        route = self.route_for(category)
        if route.mode == SkillRoutingMode.FULL_QUOTATION:
            return route.full_skill_id or "builtin"
        return route.step_routes.get(step, StepRoute()).provider


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
    ) -> None:
        self.store = store
        self.auth = auth_service
        self._now = now_provider or (lambda: datetime.now(timezone.utc))

    def get(self, actor: User) -> ExternalSkillRoutingConfig:
        self.auth.require_permission(actor, "system.config")
        return self.store.load()

    def save(
        self, actor: User, config: ExternalSkillRoutingConfig
    ) -> ExternalSkillRoutingConfig:
        self.auth.require_permission(actor, "system.config")
        current = self.store.load()
        changed = config.model_copy(
            update={
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
    )

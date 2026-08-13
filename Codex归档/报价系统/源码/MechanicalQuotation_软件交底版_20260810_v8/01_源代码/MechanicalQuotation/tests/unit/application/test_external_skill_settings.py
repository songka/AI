from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from quotation.application.auth_service import AuthService
from quotation.application.external_skill_settings import (
    AgentDefinition,
    AgentSourceType,
    BUILTIN_SKILLS,
    ExternalSkillDefinition,
    ExternalSkillRoutingConfig,
    ExternalSkillSettingsService,
    ExternalSkillSettingsStore,
    CategorySkillRouting,
    PartCategory,
    ProcessCode,
    PROCESS_ROUTABLE_STEPS,
    ProcessSkillRouting,
    SkillRoutingMode,
    SkillStep,
    StepRoute,
)
from quotation.domain.user import UserRole
from quotation.infrastructure.auth.encrypted_user_store import EncryptedUserStore


def _skill(skill_id, steps, *, full=False):
    return ExternalSkillDefinition(
        skill_id=skill_id,
        name_zh=f"测试 {skill_id}",
        endpoint=f"http://127.0.0.1/{skill_id}",
        skill_version="1.0.0",
        supported_steps=steps,
        supports_full_quotation=full,
    )


def _auth(tmp_path):
    auth = AuthService(EncryptedUserStore(tmp_path / "users.json", "skill-test-key-2026"))
    admin = auth.create_initial_admin("admin001", "AdminPass123!", "管理员")
    viewer = auth.create_user(
        admin, "viewer001", "ViewerPass123!", "查看者", UserRole.VIEWER
    )
    return auth, admin, viewer


def test_builtin_skill_catalog_has_one_visible_entry_per_pipeline_step():
    assert len(BUILTIN_SKILLS) == len(SkillStep) == 11
    assert {skill.supported_steps[0] for skill in BUILTIN_SKILLS} == set(SkillStep)
    assert all(skill.skill_id.startswith("builtin.") for skill in BUILTIN_SKILLS)


def test_full_mode_accepts_exactly_one_full_quotation_skill():
    full = _skill("full.skill", list(SkillStep), full=True)
    config = ExternalSkillRoutingConfig(
        mode=SkillRoutingMode.FULL_QUOTATION,
        skills=[full],
        full_skill_id=full.skill_id,
    )

    assert config.provider_for(SkillStep.LINE_ITEM_PRICING) == "full.skill"
    with pytest.raises(ValueError, match="不能同时配置分步"):
        ExternalSkillRoutingConfig(
            mode=SkillRoutingMode.FULL_QUOTATION,
            skills=[full],
            full_skill_id=full.skill_id,
            step_routes={SkillStep.PRICE_AUDIT: StepRoute(provider="builtin")},
        )


def test_distributed_mode_allows_multiple_skills_and_builtin():
    process = _skill("process.skill", [SkillStep.PROCESS_PLANNING])
    audit = _skill("audit.skill", [SkillStep.PRICE_AUDIT])
    config = ExternalSkillRoutingConfig(
        mode=SkillRoutingMode.DISTRIBUTED,
        skills=[process, audit],
        step_routes={
            SkillStep.PROCESS_PLANNING: StepRoute(provider=process.skill_id),
            SkillStep.LINE_ITEM_PRICING: StepRoute(provider="builtin"),
            SkillStep.PRICE_AUDIT: StepRoute(provider=audit.skill_id),
        },
    )

    assert config.provider_for(SkillStep.PROCESS_PLANNING) == "process.skill"
    assert config.provider_for(SkillStep.LINE_ITEM_PRICING) == "builtin"
    assert config.provider_for(SkillStep.PRICE_AUDIT) == "audit.skill"

    with pytest.raises(ValueError, match="不支持步骤"):
        ExternalSkillRoutingConfig(
            mode=SkillRoutingMode.DISTRIBUTED,
            skills=[process],
            step_routes={SkillStep.PRICE_AUDIT: StepRoute(provider=process.skill_id)},
        )


def test_part_categories_can_override_or_inherit_the_global_skill_route():
    process = _skill("process.skill", [SkillStep.PROCESS_PLANNING])
    audit = _skill("audit.skill", [SkillStep.PRICE_AUDIT])
    config = ExternalSkillRoutingConfig(
        skills=[process, audit],
        step_routes={SkillStep.PROCESS_PLANNING: StepRoute(provider=process.skill_id)},
        category_routes={
            PartCategory.SHEET_METAL: CategorySkillRouting(
                step_routes={SkillStep.PRICE_AUDIT: StepRoute(provider=audit.skill_id)}
            )
        },
    )

    assert config.provider_for(
        SkillStep.PROCESS_PLANNING, PartCategory.MACHINING
    ) == "process.skill"
    assert config.provider_for(
        SkillStep.PRICE_AUDIT, PartCategory.SHEET_METAL
    ) == "audit.skill"
    assert config.provider_for(
        SkillStep.PROCESS_PLANNING, PartCategory.SHEET_METAL
    ) == "builtin"
    assert set(config.category_routes) == {PartCategory.SHEET_METAL}


def test_part_classification_cannot_be_configured_inside_a_category_route():
    classifier = _skill("part.classifier", [SkillStep.PART_CLASSIFICATION])

    with pytest.raises(ValueError, match="路由前置步骤"):
        ExternalSkillRoutingConfig(
            skills=[classifier],
            category_routes={
                PartCategory.MACHINING: CategorySkillRouting(
                    step_routes={
                        SkillStep.PART_CLASSIFICATION: StepRoute(
                            provider=classifier.skill_id
                        )
                    }
                )
            },
        )


def test_document_understanding_cannot_be_configured_inside_a_category_route():
    reader = _skill("drawing.reader", [SkillStep.DOCUMENT_UNDERSTANDING])

    with pytest.raises(ValueError, match="全局步骤"):
        ExternalSkillRoutingConfig(
            skills=[reader],
            category_routes={
                PartCategory.MACHINING: CategorySkillRouting(
                    step_routes={
                        SkillStep.DOCUMENT_UNDERSTANDING: StepRoute(
                            provider=reader.skill_id
                        )
                    }
                )
            },
        )


def test_first_two_steps_always_use_global_provider():
    global_skill = _skill(
        "global.frontend",
        [SkillStep.DOCUMENT_UNDERSTANDING, SkillStep.PART_CLASSIFICATION],
    )
    category_skill = _skill("sheet.process", [SkillStep.PROCESS_PLANNING])
    config = ExternalSkillRoutingConfig(
        skills=[global_skill, category_skill],
        step_routes={
            SkillStep.DOCUMENT_UNDERSTANDING: StepRoute(provider=global_skill.skill_id),
            SkillStep.PART_CLASSIFICATION: StepRoute(provider=global_skill.skill_id),
        },
        category_routes={
            PartCategory.SHEET_METAL: CategorySkillRouting(
                step_routes={
                    SkillStep.PROCESS_PLANNING: StepRoute(provider=category_skill.skill_id)
                }
            )
        },
    )

    assert config.provider_for(
        SkillStep.DOCUMENT_UNDERSTANDING, PartCategory.SHEET_METAL
    ) == global_skill.skill_id
    assert config.provider_for(
        SkillStep.PART_CLASSIFICATION, PartCategory.SHEET_METAL
    ) == global_skill.skill_id
    assert config.provider_for(
        SkillStep.PROCESS_PLANNING, PartCategory.SHEET_METAL
    ) == category_skill.skill_id


def test_v2_process_route_overrides_category_route_and_other_process_inherits():
    shared = _skill("shared.time", [SkillStep.TIME_ESTIMATION])
    grinding = ExternalSkillDefinition(
        skill_id="grinding.time",
        name_zh="磨床工时",
        endpoint="http://127.0.0.1/grinding",
        skill_version="2.0.0",
        supported_steps=[SkillStep.TIME_ESTIMATION],
        supported_processes=[ProcessCode.GRIND],
    )
    config = ExternalSkillRoutingConfig(
        skills=[shared, grinding],
        category_routes={
            PartCategory.MACHINING: CategorySkillRouting(
                step_routes={
                    SkillStep.TIME_ESTIMATION: StepRoute(provider=shared.skill_id)
                },
                process_routes={
                    ProcessCode.GRIND: ProcessSkillRouting(
                        step_routes={
                            SkillStep.TIME_ESTIMATION: StepRoute(
                                provider=grinding.skill_id
                            )
                        }
                    )
                },
            )
        },
    )

    assert config.schema_version == "2.0"
    assert config.route_for_process(
        SkillStep.TIME_ESTIMATION, PartCategory.MACHINING, ProcessCode.GRIND
    ).provider == grinding.skill_id
    assert config.route_for_process(
        SkillStep.TIME_ESTIMATION, PartCategory.MACHINING, ProcessCode.MILL
    ).provider == shared.skill_id


def test_v2_global_process_route_is_directly_configurable_and_category_inherits_it():
    grinding = ExternalSkillDefinition(
        skill_id="global.grind-time",
        name_zh="全局磨床工时",
        endpoint="http://127.0.0.1/global-grind",
        skill_version="2.0.0",
        supported_steps=[SkillStep.TIME_ESTIMATION],
        supported_processes=[ProcessCode.GRIND],
    )
    config = ExternalSkillRoutingConfig(
        skills=[grinding],
        process_routes={
            ProcessCode.GRIND: ProcessSkillRouting(
                step_routes={
                    SkillStep.TIME_ESTIMATION: StepRoute(provider=grinding.skill_id)
                }
            )
        },
    )

    assert config.route_for_process(
        SkillStep.TIME_ESTIMATION, None, ProcessCode.GRIND
    ).provider == grinding.skill_id
    assert config.route_for_process(
        SkillStep.TIME_ESTIMATION, PartCategory.MACHINING, ProcessCode.GRIND
    ).provider == grinding.skill_id


def test_v2_category_process_override_keeps_other_global_process_skills():
    global_grind = ExternalSkillDefinition(
        skill_id="global.grind",
        name_zh="全局磨床工时",
        endpoint="http://127.0.0.1/global-grind",
        skill_version="2.0.0",
        supported_steps=[SkillStep.TIME_ESTIMATION],
        supported_processes=[ProcessCode.GRIND],
    )
    machining_mill = ExternalSkillDefinition(
        skill_id="machining.mill",
        name_zh="加工件铣床工时",
        endpoint="http://127.0.0.1/machining-mill",
        skill_version="2.0.0",
        supported_steps=[SkillStep.TIME_ESTIMATION],
        supported_processes=[ProcessCode.MILL],
    )
    config = ExternalSkillRoutingConfig(
        skills=[global_grind, machining_mill],
        process_routes={
            ProcessCode.GRIND: ProcessSkillRouting(
                step_routes={
                    SkillStep.TIME_ESTIMATION: {"provider": global_grind.skill_id}
                }
            )
        },
        category_routes={
            PartCategory.MACHINING: CategorySkillRouting(
                process_routes={
                    ProcessCode.MILL: ProcessSkillRouting(
                        step_routes={
                            SkillStep.TIME_ESTIMATION: {"provider": machining_mill.skill_id}
                        }
                    )
                }
            )
        },
    )

    assert config.route_for_process(
        SkillStep.TIME_ESTIMATION, PartCategory.MACHINING, ProcessCode.GRIND
    ).provider == global_grind.skill_id
    assert config.route_for_process(
        SkillStep.TIME_ESTIMATION, PartCategory.MACHINING, ProcessCode.MILL
    ).provider == machining_mill.skill_id


def test_v2_skill_can_bind_a_compatible_external_agent():
    agent = AgentDefinition(
        agent_id="agent.grind",
        name_zh="磨床智能体",
        source_type=AgentSourceType.HTTP,
        endpoint="http://127.0.0.1:9001",
        supported_steps=[SkillStep.TIME_ESTIMATION],
        supported_processes=[ProcessCode.GRIND],
    )
    skill = ExternalSkillDefinition(
        skill_id="skill.grind",
        name_zh="磨床工时 Skill",
        endpoint="http://127.0.0.1:9002",
        skill_version="2.0.0",
        supported_steps=[SkillStep.TIME_ESTIMATION],
        supported_processes=[ProcessCode.GRIND],
        step_agent_routes={SkillStep.TIME_ESTIMATION: agent.agent_id},
    )

    config = ExternalSkillRoutingConfig(
        skills=[skill],
        agents=[agent],
        category_routes={
            PartCategory.MACHINING: CategorySkillRouting(
                process_routes={
                    ProcessCode.GRIND: ProcessSkillRouting(
                        step_routes={
                            SkillStep.TIME_ESTIMATION: StepRoute(provider=skill.skill_id)
                        }
                    )
                }
            )
        },
    )

    assert config.skills[0].step_agent_routes[SkillStep.TIME_ESTIMATION] == agent.agent_id


def test_v2_rejects_process_route_for_non_process_step():
    feature = _skill("feature.skill", [SkillStep.FEATURE_EXTRACTION])
    with pytest.raises(ValueError, match="具体工艺路由不能接管"):
        ExternalSkillRoutingConfig(
            skills=[feature],
            category_routes={
                PartCategory.MACHINING: CategorySkillRouting(
                    process_routes={
                        ProcessCode.MILL: ProcessSkillRouting(
                            step_routes={
                                SkillStep.FEATURE_EXTRACTION: StepRoute(
                                    provider=feature.skill_id
                                )
                            }
                        )
                    }
                )
            },
        )


def test_v1_1_routing_config_remains_readable_in_v2_program():
    loaded = ExternalSkillRoutingConfig.model_validate(
        {
            "schema_version": "1.1",
            "config_version": 5,
            "mode": "DISTRIBUTED",
            "skills": [],
            "step_routes": {"PRICE_AUDIT": {"provider": "builtin"}},
            "category_routes": {},
        }
    )

    assert loaded.schema_version == "1.1"
    assert loaded.agents == []
    assert loaded.provider_for(SkillStep.PRICE_AUDIT) == "builtin"


def test_v2_only_steps_6_7_10_11_use_concrete_process_routing():
    assert PROCESS_ROUTABLE_STEPS == {
        SkillStep.TIME_ESTIMATION,
        SkillStep.LINE_ITEM_PRICING,
        SkillStep.PRICE_AUDIT,
        SkillStep.REVIEW_RECOMMENDATION,
    }


def test_test_mode_never_writes_real_smb_and_admin_is_required(tmp_path):
    auth, admin, viewer = _auth(tmp_path)
    primary = tmp_path / "fake-smb" / "data" / "external-skill-routing.json"
    cache = tmp_path / "test-cache" / "data" / "external-skill-routing.json"
    store = ExternalSkillSettingsStore(primary, cache, sync_enabled=False)
    service = ExternalSkillSettingsService(
        store,
        auth,
        now_provider=lambda: datetime(2026, 8, 6, tzinfo=timezone.utc),
    )
    config = ExternalSkillRoutingConfig(
        mode=SkillRoutingMode.DISTRIBUTED, debug_mode=True
    )

    saved = service.save(admin, config)

    assert saved.config_version == 2
    assert store.last_source == "cache-test"
    assert service.get(admin).debug_mode is True
    assert cache.is_file()
    assert not primary.exists()
    assert store.last_source == "cache"
    with pytest.raises(PermissionError):
        service.save(viewer, config)


def test_smb_mode_writes_primary_and_refreshes_cache(tmp_path):
    auth, admin, _viewer = _auth(tmp_path)
    primary = tmp_path / "smb" / "data" / "external-skill-routing.json"
    cache = tmp_path / "cache" / "data" / "external-skill-routing.json"
    service = ExternalSkillSettingsService(
        ExternalSkillSettingsStore(primary, cache, sync_enabled=True), auth
    )

    service.save(admin, ExternalSkillRoutingConfig())

    assert primary.read_bytes() == cache.read_bytes()


def test_load_falls_back_to_cache_when_smb_access_is_denied(tmp_path, monkeypatch):
    primary = tmp_path / "blocked-smb" / "external-skill-routing.json"
    cache = tmp_path / "cache" / "external-skill-routing.json"
    cache.parent.mkdir(parents=True)
    cache.write_text(
        ExternalSkillRoutingConfig(debug_mode=True).model_dump_json(),
        encoding="utf-8",
    )
    original_is_file = Path.is_file

    def is_file_with_denied_smb(path):
        if path == primary:
            raise PermissionError("SMB is not accessible")
        return original_is_file(path)

    monkeypatch.setattr(Path, "is_file", is_file_with_denied_smb)
    store = ExternalSkillSettingsStore(primary, cache, sync_enabled=True)

    loaded = store.load()

    assert loaded.debug_mode is True
    assert store.last_source == "cache"
    ProcessCode,
    ProcessSkillRouting,

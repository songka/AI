from types import SimpleNamespace

from quotation.application.external_skill_router import ExternalSkillRouter
from quotation.application.external_skill_router import ExternalSkillExecution
from quotation.application.external_skill_settings import (
    AgentDefinition,
    AgentSourceType,
    ExternalSkillDefinition,
    ExternalSkillRoutingConfig,
    CategorySkillRouting,
    PartCategory,
    ProcessCode,
    ProcessSkillRouting,
    SkillRoutingMode,
    SkillSourceType,
    SkillStep,
)
from quotation.application.quotation_service import JobStatus, QuotationApplicationService
from quotation.domain.quote import PriceSource, Quote, QuoteItem


def test_full_external_skill_can_complete_quote_before_builtin_parsing(tmp_path):
    source = tmp_path / "future-part.dxf"
    source.write_text("external skill owns the full quotation", encoding="utf-8")
    skill = ExternalSkillDefinition(
        skill_id="full.quote",
        name_zh="整套报价",
        endpoint="http://127.0.0.1:8765",
        skill_version="1.0.0",
        supported_steps=list(SkillStep),
        supports_full_quotation=True,
    )
    config = ExternalSkillRoutingConfig(
        mode=SkillRoutingMode.FULL_QUOTATION,
        skills=[skill],
        full_skill_id=skill.skill_id,
    )
    response = {
        "request_id": "REQ-1",
        "protocol_version": "1.0",
        "skill_id": skill.skill_id,
        "skill_version": skill.skill_version,
        "status": "COMPLETE",
        "completed_steps": [step.value for step in SkillStep],
        "warnings_zh": [],
        "review": {
            "decision": "PASS",
            "risk_score": 0,
            "reasons_zh": [],
            "required_actions_zh": [],
        },
        "quotation": {
            "material_code": "A6061-T6",
            "items": [
                {
                    "line_id": "EXT-MAT-1",
                    "category": "material",
                    "name_zh": "6061-T6 铝合金",
                    "quantity": 2,
                    "unit": "kg",
                    "unit_price": 10,
                    "amount": 20,
                    "price_status": "FORMAL",
                    "source": "C",
                    "company_price_id": "CP-AL-1",
                    "confidence": 0.95,
                    "evidence": [
                        {"evidence_type": "PUBLISHED_PRICE", "description_zh": "公司正式价格"}
                    ],
                }
            ],
            "subtotal_excluding_tax": 20,
            "tax_rate": 0.13,
            "tax_amount": 2.6,
            "total_including_tax": 22.6,
            "cost_completion": 100,
            "unknown_count": 0,
        },
    }

    class FakeRouter:
        def load_config(self):
            return config

        def execute(self, result, selected_config):
            assert result.quote is None
            assert selected_config is config
            return ExternalSkillExecution(
                responses=[
                    {
                        "skill": skill.model_dump(mode="json"),
                        "selected_steps": [step.value for step in SkillStep],
                        "execution_mode": SkillRoutingMode.FULL_QUOTATION.value,
                        "response": response,
                    }
                ],
                price_records={
                    "CP-AL-1": {
                        "company_price_id": "CP-AL-1",
                        "unit_price": 10,
                        "price_version_id": "PRICE-V1",
                        "price_basis": "EXCLUDING_TAX",
                        "origin_supplier_id": "SUP-1",
                        "origin_price_record_id": "PR-1",
                    }
                },
            )

    result = QuotationApplicationService(external_skill_router=FakeRouter()).quote_single_file(
        source
    )

    assert result.status == JobStatus.COMPLETE
    assert result.quote is not None
    assert result.quote.total == 20
    assert result.quote.items[0].resolution_source == "EXTERNAL_SKILL_VALIDATED_COMPANY_PRICE"
    assert result.tax is not None and float(result.tax.total_including_tax) == 22.6


def test_skill_request_preserves_note_source_confidence_and_original_text(tmp_path):
    source = tmp_path / "备注图纸.dxf"
    source.write_text("0\nEOF\n", encoding="utf-8")
    drawing_file = SimpleNamespace(
        full_path=source, file_name=source.name, extension=".dxf"
    )
    result = SimpleNamespace(
        job_id="JOB-NOTE",
        drawing_number="NOTE-1",
        bundle=SimpleNamespace(files=[drawing_file], geometry_source=drawing_file),
        quote=None,
        feature_summary={},
        warnings=[],
        ai_suggestions={},
        document_texts=[
            {
                "text": "材料：SUS304",
                "source_file_name": source.name,
                "source_kind": "DRAWING_VECTOR_TEXT",
                "page": None,
                "entity_id": "TEXT-1",
                "confidence": 1.0,
            }
        ],
        _item_to_dict=lambda _item: {},
    )
    skill = ExternalSkillDefinition(
        skill_id="note.agent",
        name_zh="备注 Agent",
        endpoint="http://127.0.0.1:8765",
        skill_version="1.0.0",
        supported_steps=[SkillStep.DOCUMENT_UNDERSTANDING],
    )
    pricebook = {
        "price_version_id": "P1",
        "published_at": "2026-08-06T00:00:00Z",
        "records_sha256": "a" * 64,
        "records": [],
    }

    payload = ExternalSkillRouter._request_payload(
        result,
        skill,
        [SkillStep.DOCUMENT_UNDERSTANDING],
        SkillRoutingMode.DISTRIBUTED,
        pricebook,
    )

    extracted = payload["drawing_package"]["extracted_texts"][0]
    assert payload["execution_mode"] == "PARTIAL_STEPS"
    assert extracted["text"] == "材料：SUS304"
    assert extracted["source_file_id"] == payload["drawing_package"]["primary_file"]
    assert extracted["confidence"] == 1.0
    assert payload["built_in_context"]["note_inputs"][0]["source_kind"] == "DRAWING_VECTOR_TEXT"


def test_full_folder_prompt_skill_runs_after_builtin_document_parsing(tmp_path):
    import ezdxf

    source = tmp_path / "folder-agent.dxf"
    doc = ezdxf.new()
    doc.modelspace().add_text("材料：S50C")
    doc.saveas(source)
    skill = ExternalSkillDefinition(
        skill_id="folder.full",
        name_zh="文件夹整套 Agent",
        endpoint=str(tmp_path / "folder-skill"),
        source_type=SkillSourceType.FOLDER,
        skill_version="1.0.0",
        supported_steps=list(SkillStep),
        supports_full_quotation=True,
    )
    config = ExternalSkillRoutingConfig(
        mode=SkillRoutingMode.FULL_QUOTATION,
        skills=[skill],
        full_skill_id=skill.skill_id,
    )

    class FakeRouter:
        called_after_parse = False

        def load_config(self):
            return config

        def execute(self, result, _config, **_kwargs):
            self.called_after_parse = result.quote is not None and bool(result.document_texts)
            return ExternalSkillExecution(warnings=["测试文件夹 Agent 已调用"])

    router = FakeRouter()
    result = QuotationApplicationService(external_skill_router=router).quote_single_file(source)

    assert router.called_after_parse is True
    assert result.quote is not None
    assert "测试文件夹 Agent 已调用" in result.warnings


def test_router_selects_the_step_provider_for_the_detected_part_category():
    machining = ExternalSkillDefinition(
        skill_id="machining.agent",
        name_zh="加工件工艺 Agent",
        endpoint="http://127.0.0.1:8765",
        skill_version="1.0.0",
        supported_steps=[SkillStep.PROCESS_PLANNING],
    )
    sheet = ExternalSkillDefinition(
        skill_id="sheet.agent",
        name_zh="钣金件工艺 Agent",
        endpoint="http://127.0.0.1:8766",
        skill_version="1.0.0",
        supported_steps=[SkillStep.PROCESS_PLANNING],
    )
    config = ExternalSkillRoutingConfig(
        skills=[machining, sheet],
        step_routes={SkillStep.PROCESS_PLANNING: {"provider": machining.skill_id}},
        category_routes={
            PartCategory.SHEET_METAL: CategorySkillRouting(
                step_routes={SkillStep.PROCESS_PLANNING: {"provider": sheet.skill_id}}
            )
        },
    )

    calls = ExternalSkillRouter._calls(config, PartCategory.SHEET_METAL)

    assert len(calls) == 1
    assert calls[0][0].skill_id == "sheet.agent"
    assert calls[0][1] == [SkillStep.PROCESS_PLANNING]


def test_same_skill_is_split_across_dependency_phases():
    skill = ExternalSkillDefinition(
        skill_id="multi.phase",
        name_zh="多阶段 Skill",
        endpoint="http://127.0.0.1:8765",
        skill_version="1.0.0",
        supported_steps=[SkillStep.PROCESS_PLANNING, SkillStep.PRICE_AUDIT],
    )
    config = ExternalSkillRoutingConfig(
        skills=[skill],
        step_routes={
            SkillStep.PROCESS_PLANNING: {"provider": skill.skill_id},
            SkillStep.PRICE_AUDIT: {"provider": skill.skill_id},
        },
    )

    calls = ExternalSkillRouter._calls(config, PartCategory.MACHINING)

    assert [steps for _skill, steps, _mode in calls] == [
        [SkillStep.PROCESS_PLANNING],
        [SkillStep.PRICE_AUDIT],
    ]


def test_v2_routes_mill_and_grind_to_different_process_skills():
    mill = ExternalSkillDefinition(
        skill_id="mill.time",
        name_zh="铣床工时",
        endpoint="http://127.0.0.1:9101",
        skill_version="2.0.0",
        supported_steps=[SkillStep.TIME_ESTIMATION],
        supported_processes=[ProcessCode.MILL],
    )
    grind = ExternalSkillDefinition(
        skill_id="grind.time",
        name_zh="磨床工时",
        endpoint="http://127.0.0.1:9102",
        skill_version="2.0.0",
        supported_steps=[SkillStep.TIME_ESTIMATION],
        supported_processes=[ProcessCode.GRIND],
    )
    config = ExternalSkillRoutingConfig(
        skills=[mill, grind],
        category_routes={
            PartCategory.MACHINING: CategorySkillRouting(
                process_routes={
                    ProcessCode.MILL: ProcessSkillRouting(
                        step_routes={
                            SkillStep.TIME_ESTIMATION: {"provider": mill.skill_id}
                        }
                    ),
                    ProcessCode.GRIND: ProcessSkillRouting(
                        step_routes={
                            SkillStep.TIME_ESTIMATION: {"provider": grind.skill_id}
                        }
                    ),
                }
            )
        },
    )

    calls = ExternalSkillRouter._route_calls(
        config,
        PartCategory.MACHINING,
        process_codes={ProcessCode.MILL, ProcessCode.GRIND},
        only_steps={SkillStep.TIME_ESTIMATION},
    )

    assert [(call.skill.skill_id, call.process_codes) for call in calls] == [
        ("grind.time", [ProcessCode.GRIND]),
        ("mill.time", [ProcessCode.MILL]),
    ]


def test_v2_lower_agent_selector_can_execute_external_agent_with_builtin_provider():
    agent = AgentDefinition(
        agent_id="agent.audit",
        name_zh="外挂审核智能体",
        source_type=AgentSourceType.HTTP,
        endpoint="http://127.0.0.1:9201",
        supported_steps=[SkillStep.PRICE_AUDIT],
    )
    config = ExternalSkillRoutingConfig(
        agents=[agent],
        step_routes={
            SkillStep.PRICE_AUDIT: {
                "provider": "builtin",
                "agent_id": agent.agent_id,
            }
        },
    )

    calls = ExternalSkillRouter._route_calls(
        config, only_steps={SkillStep.PRICE_AUDIT}
    )

    assert len(calls) == 1
    assert calls[0].direct_agent is True
    assert calls[0].agent == agent
    assert calls[0].skill.skill_id == agent.agent_id


def test_v2_skill_bound_external_agent_is_the_actual_executor(tmp_path):
    source = tmp_path / "bound-agent.dxf"
    source.write_text("0\nEOF\n", encoding="utf-8")
    drawing_file = SimpleNamespace(
        full_path=source, file_name=source.name, extension=".dxf"
    )
    agent = AgentDefinition(
        agent_id="agent.grind",
        name_zh="磨床智能体",
        source_type=AgentSourceType.HTTP,
        endpoint="http://127.0.0.1:9301",
        supported_steps=[SkillStep.TIME_ESTIMATION],
        supported_processes=[ProcessCode.GRIND],
    )
    skill = ExternalSkillDefinition(
        skill_id="skill.grind-time",
        name_zh="磨床工时 Skill",
        endpoint="http://127.0.0.1:9302",
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
                            SkillStep.TIME_ESTIMATION: {"provider": skill.skill_id}
                        }
                    )
                }
            )
        },
    )

    class FakeClient:
        def __init__(self):
            self.agent_calls = []
            self.skill_calls = []

        def invoke_agent(self, selected_agent, payload):
            self.agent_calls.append((selected_agent, payload))
            return {
                "request_id": payload["request_id"],
                "protocol_version": "1.0",
                "agent_id": selected_agent.agent_id,
                "completed_steps": [SkillStep.TIME_ESTIMATION.value],
                "step_results": {"TIME_ESTIMATION": {"hours": 0.8}},
            }

        def invoke_skill(self, selected_skill, payload):
            self.skill_calls.append((selected_skill, payload))
            raise AssertionError("绑定外挂智能体后不应调用 Skill 自身执行端")

    client = FakeClient()
    quote = SimpleNamespace(
        material="S50C", part_name="磨削件", quantity=1, items=[]
    )
    result = SimpleNamespace(
        job_id="JOB-BOUND",
        drawing_number="BOUND-1",
        bundle=SimpleNamespace(files=[drawing_file], geometry_source=drawing_file),
        quote=quote,
        feature_summary={"part_category": PartCategory.MACHINING.value},
        document_texts=[],
        warnings=[],
        ai_suggestions={"processes": [{"code": "GRIND"}]},
    )
    pricebook = SimpleNamespace(_snapshot={
        "price_version_id": "P1",
        "approved_at": "2026-08-06T00:00:00Z",
        "snapshot_sha256": "a" * 64,
        "company_prices": [],
    })
    router = ExternalSkillRouter(
        SimpleNamespace(load=lambda: config), client=client, pricebook_loader=pricebook
    )

    execution = router.execute(
        result, config, only_steps={SkillStep.TIME_ESTIMATION}
    )

    assert not execution.warnings
    assert len(client.agent_calls) == 1
    assert not client.skill_calls
    assert client.agent_calls[0][1]["target_agent"]["agent_id"] == agent.agent_id
    assert execution.responses[0]["response"]["skill_id"] == skill.skill_id
    assert execution.responses[0]["response"]["agent_id"] == agent.agent_id


def test_v2_process_time_result_updates_hours_but_keeps_company_rate():
    quote = Quote(
        id="Q1",
        drawing_id="D1",
        items=[
            QuoteItem(
                line_id="PROC-GRIND",
                category="process",
                name="磨床 加工費",
                quantity=4.5,
                unit="hour",
                unit_price=40,
                amount=180,
                source=PriceSource.C,
                company_price_id="CP-GRIND",
            )
        ],
    )
    result = SimpleNamespace(quote=quote)
    entry = {
        "process_codes": ["GRIND"],
        "response": {
            "step_results": {
                "TIME_ESTIMATION": {
                    "processes": [{"code": "GRIND", "estimated_hours": 0.8}]
                }
            }
        },
    }

    changed = QuotationApplicationService._apply_external_time_results(result, entry)

    assert changed is True
    item = result.quote.items[0]
    assert item.quantity == 0.8
    assert item.unit_price == 40
    assert item.amount == 32
    assert item.source == PriceSource.C
    assert item.company_price_id == "CP-GRIND"


def test_non_pricing_payload_omits_price_records_and_carries_prior_skill_results(tmp_path):
    source = tmp_path / "part.dxf"
    source.write_text("0\nEOF\n", encoding="utf-8")
    drawing_file = SimpleNamespace(
        full_path=source, file_name=source.name, extension=".dxf"
    )
    result = SimpleNamespace(
        job_id="JOB-CHAIN",
        drawing_number="CHAIN-1",
        bundle=SimpleNamespace(files=[drawing_file], geometry_source=drawing_file),
        quote=SimpleNamespace(part_name="测试件", quantity=1, material="S50C", items=[]),
        feature_summary={"part_category": "MACHINING"},
        document_texts=[],
        warnings=[],
        ai_suggestions={},
    )
    skill = ExternalSkillDefinition(
        skill_id="feature.skill",
        name_zh="特征 Skill",
        endpoint="http://127.0.0.1:8765",
        skill_version="1.0.0",
        supported_steps=[SkillStep.FEATURE_EXTRACTION],
    )
    prior = [{"skill_id": "notes.skill", "step_results": {"DOCUMENT_UNDERSTANDING": {"summary": "ok"}}}]

    payload = ExternalSkillRouter._request_payload(
        result,
        skill,
        [SkillStep.FEATURE_EXTRACTION],
        SkillRoutingMode.DISTRIBUTED,
        {"price_version_id": "P1", "records_sha256": "abc", "records": [{"id": 1}]},
        prior_skill_results=prior,
    )

    assert payload["published_pricebook"]["records"] == []
    assert payload["published_pricebook"]["records_omitted_for_non_pricing_step"] is True
    assert payload["built_in_context"]["prior_skill_results"] == prior


def test_part_classification_uses_global_provider_before_category_route():
    classifier = ExternalSkillDefinition(
        skill_id="part.classifier",
        name_zh="零件分类",
        endpoint="http://127.0.0.1:8765",
        skill_version="1.0.0",
        supported_steps=[SkillStep.PART_CLASSIFICATION],
    )
    process = ExternalSkillDefinition(
        skill_id="sheet.process",
        name_zh="钣金工艺",
        endpoint="http://127.0.0.1:8766",
        skill_version="1.0.0",
        supported_steps=[SkillStep.PROCESS_PLANNING],
    )
    config = ExternalSkillRoutingConfig(
        skills=[classifier, process],
        step_routes={
            SkillStep.PART_CLASSIFICATION: {"provider": classifier.skill_id}
        },
        category_routes={
            PartCategory.SHEET_METAL: CategorySkillRouting(
                step_routes={
                    SkillStep.PROCESS_PLANNING: {"provider": process.skill_id}
                }
            )
        },
    )

    classification_calls = ExternalSkillRouter._calls(
        config,
        PartCategory.MACHINING,
        only_steps={SkillStep.PART_CLASSIFICATION},
    )
    routed_calls = ExternalSkillRouter._calls(
        config,
        PartCategory.SHEET_METAL,
        skip_steps={SkillStep.PART_CLASSIFICATION},
    )

    assert classification_calls[0][0].skill_id == classifier.skill_id
    assert classification_calls[0][1] == [SkillStep.PART_CLASSIFICATION]
    assert routed_calls[0][0].skill_id == process.skill_id
    assert routed_calls[0][1] == [SkillStep.PROCESS_PLANNING]


def test_first_two_steps_use_global_full_skill_and_later_steps_use_category_full_skill():
    global_skill = ExternalSkillDefinition(
        skill_id="global.quote",
        name_zh="全局前置 Skill",
        endpoint="http://127.0.0.1:8765",
        skill_version="1.0.0",
        supported_steps=list(SkillStep),
        supports_full_quotation=True,
    )
    sheet_skill = ExternalSkillDefinition(
        skill_id="sheet.quote",
        name_zh="钣金报价 Skill",
        endpoint="http://127.0.0.1:8766",
        skill_version="1.0.0",
        supported_steps=list(SkillStep),
        supports_full_quotation=True,
    )
    config = ExternalSkillRoutingConfig(
        mode=SkillRoutingMode.FULL_QUOTATION,
        skills=[global_skill, sheet_skill],
        full_skill_id=global_skill.skill_id,
        category_routes={
            PartCategory.SHEET_METAL: CategorySkillRouting(
                mode=SkillRoutingMode.FULL_QUOTATION,
                full_skill_id=sheet_skill.skill_id,
            )
        },
    )

    calls = ExternalSkillRouter._calls(config, PartCategory.SHEET_METAL)
    by_skill = {call[0].skill_id: call[1] for call in calls}

    assert by_skill[global_skill.skill_id] == [
        SkillStep.DOCUMENT_UNDERSTANDING,
        SkillStep.PART_CLASSIFICATION,
    ]
    assert by_skill[sheet_skill.skill_id] == list(SkillStep)[2:]


def test_debug_mode_records_inputs_outputs_and_validation_for_classification_and_ten_steps(tmp_path):
    source = tmp_path / "debug.dxf"
    source.write_text("0\nEOF\n", encoding="utf-8")
    drawing_file = SimpleNamespace(
        full_path=source, file_name=source.name, extension=".dxf"
    )
    quote = SimpleNamespace(
        material="S50C",
        part_name="调试件",
        quantity=1,
        items=[],
        subtotal_excluding_tax=0,
        tax_amount=0,
        total_including_tax=0,
    )
    result = SimpleNamespace(
        job_id="JOB-DEBUG",
        drawing_number="DEBUG-1",
        bundle=SimpleNamespace(files=[drawing_file], geometry_source=drawing_file),
        quote=quote,
        feature_summary={"part_category": PartCategory.MACHINING.value},
        warnings=[],
        ai_suggestions={},
        document_texts=[],
        status=JobStatus.COMPLETE,
        _item_to_dict=lambda _item: {},
    )
    pricebook = SimpleNamespace(_snapshot={
        "price_version_id": "P1",
        "approved_at": "2026-08-06T00:00:00Z",
        "snapshot_sha256": "a" * 64,
        "company_prices": [],
    })
    router = ExternalSkillRouter(
        SimpleNamespace(load=lambda: ExternalSkillRoutingConfig(debug_mode=False)),
        pricebook_loader=pricebook,
        debug_enabled=True,
    )

    execution = router.execute(result)

    assert len(execution.debug_trace) == 11
    assert [entry["step"] for entry in execution.debug_trace] == [
        step.value for step in SkillStep
    ]
    assert {entry["provider"] for entry in execution.debug_trace} == {"内置规则引擎"}
    assert all(entry["validation"]["input_ok"] for entry in execution.debug_trace)
    assert all("input" in entry and "output" in entry for entry in execution.debug_trace)

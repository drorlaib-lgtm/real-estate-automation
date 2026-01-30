"""Crew 2 - Contract Creation and Quality Control Crew."""

import json
from crewai import Crew, Process

from crews.crew2_contract.agents import (
    create_contract_builder_agent,
    create_legal_compliance_agent,
    create_quality_assurance_agent,
)
from crews.crew2_contract.tasks import (
    create_contract_building_task,
    create_compliance_check_task,
    create_quality_scoring_task,
)


def create_contract_crew(clean_data: dict, compliance_result: dict = None) -> Crew:
    """Create the contract creation and quality control crew."""
    clean_data_json = json.dumps(clean_data, ensure_ascii=False, indent=2)
    compliance_json = json.dumps(compliance_result or {}, ensure_ascii=False, indent=2)

    builder_agent = create_contract_builder_agent()
    compliance_agent = create_legal_compliance_agent()
    qa_agent = create_quality_assurance_agent()

    build_task = create_contract_building_task(builder_agent, clean_data_json)
    compliance_task = create_compliance_check_task(compliance_agent, clean_data_json)
    qa_task = create_quality_scoring_task(qa_agent, clean_data_json, compliance_json)

    crew = Crew(
        agents=[builder_agent, compliance_agent, qa_agent],
        tasks=[build_task, compliance_task, qa_task],
        process=Process.sequential,
        verbose=True,
    )
    return crew

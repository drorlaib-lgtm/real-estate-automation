"""Crew 1 - Data Collection and Validation Crew."""

import json
from crewai import Crew, Process

from crews.crew1_data.agents import (
    create_form_generator_agent,
    create_data_validator_agent,
    create_document_processor_agent,
)
from crews.crew1_data.tasks import (
    create_form_generation_task,
    create_validation_task,
    create_document_processing_task,
)


def create_data_crew(client_data: dict, document_paths: list = None) -> Crew:
    """Create the data collection and validation crew."""
    client_data_json = json.dumps(client_data, ensure_ascii=False, indent=2)

    form_agent = create_form_generator_agent()
    validator_agent = create_data_validator_agent()
    doc_processor_agent = create_document_processor_agent()

    form_task = create_form_generation_task(form_agent)
    validation_task = create_validation_task(validator_agent, client_data_json)
    doc_processing_task = create_document_processing_task(
        doc_processor_agent, client_data_json, document_paths
    )

    crew = Crew(
        agents=[form_agent, validator_agent, doc_processor_agent],
        tasks=[form_task, validation_task, doc_processing_task],
        process=Process.sequential,
        verbose=True,
    )
    return crew

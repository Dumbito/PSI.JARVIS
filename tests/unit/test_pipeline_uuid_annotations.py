from typing import get_type_hints
from uuid import UUID

from psi_jarvis.application.pipeline.pipeline import PaperPipeline


def test_pipeline_annotations_resolve_uuid_for_python_312_compatibility():
    hints = get_type_hints(PaperPipeline.process)

    assert hints["project_id"] == UUID | None

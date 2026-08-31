from __future__ import annotations

from eaip.solution_packs.healthcare import HEALTHCARE_PACK
from eaip.solution_packs.financial import FINANCIAL_PACK
from eaip.solution_packs.consultancy import CONSULTANCY_PACK
from eaip.solution_packs.manufacturing import MANUFACTURING_PACK
from eaip.solution_packs.retail import RETAIL_PACK
from eaip.solution_packs.models import SolutionPackDefinition

_CATALOG: dict[str, SolutionPackDefinition] = {
    "healthcare": SolutionPackDefinition.model_validate(HEALTHCARE_PACK),
    "financial": SolutionPackDefinition.model_validate(FINANCIAL_PACK),
    "consultancy": SolutionPackDefinition.model_validate(CONSULTANCY_PACK),
    "manufacturing": SolutionPackDefinition.model_validate(MANUFACTURING_PACK),
    "retail": SolutionPackDefinition.model_validate(RETAIL_PACK),
}


def list_packs() -> list[SolutionPackDefinition]:
    return list(_CATALOG.values())


def get_pack(pack_id: str) -> SolutionPackDefinition | None:
    return _CATALOG.get(pack_id)


def get_by_industry(industry: str) -> SolutionPackDefinition | None:
    return _CATALOG.get(industry)

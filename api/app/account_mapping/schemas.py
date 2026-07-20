from pydantic import BaseModel

from app.account_mapping.domain import (
    AccountMapping,
    ClassificationStatus,
    RasCategory,
)


class ImportFromFilesRequest(BaseModel):
    ledger_accounts_path: str
    plan_accounts_path: str


class AccountMappingResponse(BaseModel):
    account_number: str
    label: str
    ras_category: RasCategory
    classification_status: ClassificationStatus
    confidence: str
    justification: str
    action_required: str

    @classmethod
    def from_domain(cls, mapping: AccountMapping) -> "AccountMappingResponse":
        return cls(
            account_number=mapping.account_number,
            label=mapping.label,
            ras_category=mapping.ras_category,
            classification_status=mapping.classification_status,
            confidence=mapping.confidence,
            justification=mapping.justification,
            action_required=mapping.action_required,
        )


class AccountMappingsResponse(BaseModel):
    total: int
    missing_labels: int
    items: list[AccountMappingResponse]

    @classmethod
    def from_domain(
        cls,
        mappings: list[AccountMapping],
    ) -> "AccountMappingsResponse":
        items = [AccountMappingResponse.from_domain(mapping) for mapping in mappings]
        missing_labels = sum(
            1
            for mapping in mappings
            if mapping.classification_status is ClassificationStatus.MISSING_LABEL
        )
        return cls(
            total=len(items),
            missing_labels=missing_labels,
            items=items,
        )

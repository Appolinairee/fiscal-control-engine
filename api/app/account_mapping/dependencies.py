from pathlib import Path

from app.account_mapping.import_service import AccountMappingImportService
from app.account_mapping.repository import (
    AccountMappingRepository,
    InMemoryAccountMappingRepository,
)
from app.account_mapping.rule_loader import load_classification_rules
from app.account_mapping.service import AccountMappingService
from app.config import get_settings

_repository = InMemoryAccountMappingRepository()


def get_account_mapping_repository() -> AccountMappingRepository:
    return _repository


def get_account_mapping_service() -> AccountMappingService:
    settings = get_settings()
    return AccountMappingService(
        repository=_repository,
        rules=load_classification_rules(Path(settings.ras_classification_rules_path)),
    )


def get_account_mapping_import_service() -> AccountMappingImportService:
    return AccountMappingImportService()

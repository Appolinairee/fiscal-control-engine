from pathlib import Path

from app.account_mapping.repository import InMemoryAccountMappingRepository
from app.account_mapping.import_service import AccountMappingImportService
from app.account_mapping.rule_loader import load_classification_rules
from app.account_mapping.router import (
    ImportFromFilesRequest,
    import_from_files,
    list_account_mappings,
)
from app.account_mapping.service import AccountMappingService


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def build_service(repository: InMemoryAccountMappingRepository) -> AccountMappingService:
    return AccountMappingService(
        repository=repository,
        rules=load_classification_rules(FIXTURES_DIR / "ras_classification_rules.csv"),
    )


def test_import_from_files_returns_mappings() -> None:
    repository = InMemoryAccountMappingRepository()

    response = import_from_files(
        request=ImportFromFilesRequest(
            ledger_accounts_path=str(FIXTURES_DIR / "ledger_accounts.csv"),
            plan_accounts_path=str(FIXTURES_DIR / "plan_accounts.csv"),
        ),
        import_service=AccountMappingImportService(),
        mapping_service=build_service(repository),
    )

    assert response.total == 139
    assert response.missing_labels == 1
    assert [
        item.account_number
        for item in response.items
        if item.classification_status == "missing_label"
    ] == ["44910002"]
    assert len(repository.list_all()) == 139


def test_list_account_mappings_returns_repository_content() -> None:
    repository = InMemoryAccountMappingRepository()
    mapping_service = build_service(repository)
    import_from_files(
        request=ImportFromFilesRequest(
            ledger_accounts_path=str(FIXTURES_DIR / "ledger_accounts.csv"),
            plan_accounts_path=str(FIXTURES_DIR / "plan_accounts.csv"),
        ),
        import_service=AccountMappingImportService(),
        mapping_service=mapping_service,
    )

    response = list_account_mappings(repository=repository)

    assert response.total == 139
    assert response.missing_labels == 1

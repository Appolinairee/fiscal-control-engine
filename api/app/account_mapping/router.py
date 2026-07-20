from pathlib import Path

from fastapi import APIRouter, Depends

from app.account_mapping.dependencies import (
    get_account_mapping_import_service,
    get_account_mapping_repository,
    get_account_mapping_service,
)
from app.account_mapping.import_service import AccountMappingImportService
from app.account_mapping.repository import AccountMappingRepository
from app.account_mapping.schemas import (
    AccountMappingsResponse,
    ImportFromFilesRequest,
)
from app.account_mapping.service import AccountMappingService

router = APIRouter(prefix="/account-mappings", tags=["account-mappings"])


@router.get("", response_model=AccountMappingsResponse)
def list_account_mappings(
    repository: AccountMappingRepository = Depends(get_account_mapping_repository),
) -> AccountMappingsResponse:
    return AccountMappingsResponse.from_domain(repository.list_all())


@router.post("/import-from-files", response_model=AccountMappingsResponse)
def import_from_files(
    request: ImportFromFilesRequest,
    import_service: AccountMappingImportService = Depends(
        get_account_mapping_import_service,
    ),
    mapping_service: AccountMappingService = Depends(get_account_mapping_service),
) -> AccountMappingsResponse:
    ledger_accounts = import_service.read_ledger_accounts(
        Path(request.ledger_accounts_path),
    )
    plan_accounts = import_service.read_plan_accounts(Path(request.plan_accounts_path))
    mappings = mapping_service.build_from_accounts(
        ledger_accounts=ledger_accounts,
        plan_accounts=plan_accounts,
    )
    return AccountMappingsResponse.from_domain(mappings)

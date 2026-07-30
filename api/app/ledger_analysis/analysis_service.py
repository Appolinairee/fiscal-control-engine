from dataclasses import dataclass
from pathlib import Path
from unicodedata import normalize

import pandas as pd

from app.account_mapping.classifier import ClassificationRule
from app.account_mapping.domain import RasCategory
from app.excel_agent.domain import ExcelColumnProfile
from app.excel_agent.excel_tools import ExcelAgentTools
from app.ledger_analysis.constants import (
    LEDGER_AGGREGATION_FIELDS,
    LEDGER_COUNTERPARTY_FIELDS,
    LEDGER_QUALITY_CRITICAL_FIELDS,
    LEDGER_QUERY_OUTPUT_FIELDS,
    LEDGER_TAX_CANDIDATE_LIMIT,
)
from app.ledger_analysis.schema_classifier import (
    LedgerSchemaClassification,
    LedgerSchemaClassifier,
)
from app.ledger_analysis.schema_validator import (
    LedgerSchemaReport,
    LedgerSchemaValidationError,
    LedgerSchemaValidator,
)


@dataclass(frozen=True)
class LedgerAnalysisReport:
    sheet_name: str
    row_count: int
    column_count: int
    schema_report: LedgerSchemaReport
    canonical_schema: LedgerSchemaClassification
    columns: tuple[ExcelColumnProfile, ...]


@dataclass(frozen=True)
class LedgerSchemaClassificationReport:
    sheet_name: str
    row_count: int
    column_count: int
    classification: LedgerSchemaClassification
    columns: tuple[ExcelColumnProfile, ...]


@dataclass(frozen=True)
class LedgerAggregationGroup:
    key: str
    entry_count: int
    amount_sum: float


@dataclass(frozen=True)
class LedgerFieldAggregation:
    canonical_field: str
    source_column: str
    total_groups: int
    groups: tuple[LedgerAggregationGroup, ...]


@dataclass(frozen=True)
class LedgerAggregationReport:
    sheet_name: str
    row_count: int
    amount_field: str
    aggregations: tuple[LedgerFieldAggregation, ...]


@dataclass(frozen=True)
class LedgerQueryReport:
    sheet_name: str
    total_matches: int
    page: int
    page_size: int
    entries: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class LedgerMetricsReport:
    sheet_name: str
    total_matches: int
    amount_field: str
    metrics: dict[str, float | int]
    top: LedgerFieldAggregation | None


@dataclass(frozen=True)
class LedgerDataQualityIssue:
    issue_type: str
    severity: str
    canonical_field: str | None
    source_column: str | None
    affected_count: int
    affected_ratio: float
    message: str


@dataclass(frozen=True)
class LedgerDataQualityReport:
    sheet_name: str
    row_count: int
    issue_count: int
    severity_counts: dict[str, int]
    issues: tuple[LedgerDataQualityIssue, ...]


@dataclass(frozen=True)
class LedgerTaxCandidate:
    category: str
    confidence: str
    entry_count: int
    amount_sum: float
    matched_keywords: tuple[str, ...]
    top_accounts: tuple[LedgerAggregationGroup, ...]
    action_required: str


@dataclass(frozen=True)
class LedgerTaxCandidateReport:
    sheet_name: str
    row_count: int
    decision_status: str
    candidates: tuple[LedgerTaxCandidate, ...]


class LedgerAnalysisService:
    def __init__(
        self,
        excel_tools: ExcelAgentTools,
        schema_validator: LedgerSchemaValidator | None = None,
        schema_classifier: LedgerSchemaClassifier | None = None,
        tax_candidate_rules: tuple[ClassificationRule, ...] = (),
    ) -> None:
        self._excel_tools = excel_tools
        self._schema_validator = schema_validator or LedgerSchemaValidator()
        self._schema_classifier = schema_classifier or LedgerSchemaClassifier()
        self._tax_candidate_rules = tax_candidate_rules

    def analyze(self, file_path: Path, sheet_name: str) -> LedgerAnalysisReport:
        sheet_profile = self._excel_tools.profile_sheet(file_path, sheet_name)
        column_names = tuple(column.name for column in sheet_profile.columns)
        canonical_schema = self._schema_classifier.classify(sheet_profile.columns)
        schema_report = _canonical_schema_report(column_names, canonical_schema)
        return LedgerAnalysisReport(
            sheet_name=sheet_profile.sheet_name,
            row_count=sheet_profile.row_count,
            column_count=sheet_profile.column_count,
            schema_report=schema_report,
            canonical_schema=canonical_schema,
            columns=sheet_profile.columns,
        )

    def classify_schema(
        self,
        file_path: Path,
        sheet_name: str,
    ) -> LedgerSchemaClassificationReport:
        sheet_profile = self._excel_tools.profile_sheet(file_path, sheet_name)
        return LedgerSchemaClassificationReport(
            sheet_name=sheet_profile.sheet_name,
            row_count=sheet_profile.row_count,
            column_count=sheet_profile.column_count,
            classification=self._schema_classifier.classify(sheet_profile.columns),
            columns=sheet_profile.columns,
        )

    def aggregate(
        self,
        file_path: Path,
        sheet_name: str,
        group_by: tuple[str, ...],
        limit: int = 10,
    ) -> LedgerAggregationReport:
        canonical_frame = self._load_canonical_frame(file_path, sheet_name)
        amount_column = canonical_frame.fields["amount"]
        aggregations = tuple(
            _aggregate_field(
                dataframe=canonical_frame.dataframe,
                canonical_field=canonical_field,
                source_column=canonical_frame.fields[canonical_field],
                amount_column=amount_column,
                limit=limit,
            )
            for canonical_field in group_by
            if canonical_field in LEDGER_AGGREGATION_FIELDS
            and canonical_field in canonical_frame.fields
        )
        return LedgerAggregationReport(
            sheet_name=sheet_name,
            row_count=len(canonical_frame.dataframe),
            amount_field=amount_column,
            aggregations=aggregations,
        )

    def query_entries(
        self,
        file_path: Path,
        sheet_name: str,
        filters: dict[str, object],
        page: int = 1,
        page_size: int = 20,
    ) -> LedgerQueryReport:
        canonical_frame = self._load_canonical_frame(file_path, sheet_name)
        dataframe = _filter_frame(canonical_frame, filters)
        safe_page = max(1, page)
        safe_page_size = min(max(1, page_size), 50)
        start_index = (safe_page - 1) * safe_page_size
        end_index = start_index + safe_page_size
        entries = tuple(
            _serialize_query_row(row, canonical_frame.fields)
            for _, row in dataframe.iloc[start_index:end_index].iterrows()
        )
        return LedgerQueryReport(
            sheet_name=sheet_name,
            total_matches=len(dataframe),
            page=safe_page,
            page_size=safe_page_size,
            entries=entries,
        )

    def calculate_metrics(
        self,
        file_path: Path,
        sheet_name: str,
        filters: dict[str, object],
        metrics: tuple[str, ...],
        top_by: str | None = None,
        top_limit: int = 10,
    ) -> LedgerMetricsReport:
        canonical_frame = self._load_canonical_frame(file_path, sheet_name)
        dataframe = _filter_frame(canonical_frame, filters)
        amount_column = canonical_frame.fields["amount"]
        amount_series = dataframe[amount_column].fillna(0)
        calculated_metrics = _calculate_metrics(amount_series, metrics)
        top = None
        if top_by is not None and top_by in canonical_frame.fields:
            top = _aggregate_field(
                dataframe=dataframe,
                canonical_field=top_by,
                source_column=canonical_frame.fields[top_by],
                amount_column=amount_column,
                limit=top_limit,
            )
        return LedgerMetricsReport(
            sheet_name=sheet_name,
            total_matches=len(dataframe),
            amount_field=amount_column,
            metrics=calculated_metrics,
            top=top,
        )

    def detect_data_quality_issues(
        self,
        file_path: Path,
        sheet_name: str,
    ) -> LedgerDataQualityReport:
        canonical_frame = self._load_canonical_frame(file_path, sheet_name)
        issues = _detect_quality_issues(canonical_frame)
        severity_counts = _count_issue_severities(issues)
        return LedgerDataQualityReport(
            sheet_name=sheet_name,
            row_count=canonical_frame.row_count,
            issue_count=len(issues),
            severity_counts=severity_counts,
            issues=issues,
        )

    def detect_tax_candidates(
        self,
        file_path: Path,
        sheet_name: str,
        limit: int = LEDGER_TAX_CANDIDATE_LIMIT,
    ) -> LedgerTaxCandidateReport:
        canonical_frame = self._load_canonical_frame(file_path, sheet_name)
        candidates = _detect_tax_candidates(
            canonical_frame=canonical_frame,
            rules=self._tax_candidate_rules,
            limit=limit,
        )
        return LedgerTaxCandidateReport(
            sheet_name=sheet_name,
            row_count=canonical_frame.row_count,
            decision_status="review_required",
            candidates=candidates,
        )

    def _load_canonical_frame(
        self,
        file_path: Path,
        sheet_name: str,
    ) -> "_CanonicalLedgerFrame":
        sheet_profile = self._excel_tools.profile_sheet(file_path, sheet_name)
        resolved_path = sheet_profile.file_path
        classification = self._schema_classifier.classify(sheet_profile.columns)
        if not classification.is_usable:
            missing_fields = tuple(
                mapping.canonical_field
                for mapping in classification.mappings
                if mapping.canonical_field in {"account", "amount", "text"}
                and mapping.status != "mapped"
            )
            raise LedgerSchemaValidationError(
                f"canonical ledger schema is not usable: {', '.join(missing_fields)}",
            )
        fields = {
            mapping.canonical_field: mapping.source_column
            for mapping in classification.mappings
            if mapping.status == "mapped" and mapping.source_column is not None
        }
        dataframe = pd.read_excel(
            resolved_path,
            sheet_name=sheet_name,
            usecols=sorted(set(fields.values())),
            engine="openpyxl",
        )
        return _CanonicalLedgerFrame(
            dataframe=dataframe,
            fields=fields,
            row_count=sheet_profile.row_count,
            columns=sheet_profile.columns,
        )


def _canonical_schema_report(
    column_names: tuple[str, ...],
    classification: LedgerSchemaClassification,
) -> LedgerSchemaReport:
    missing_required_columns = tuple(
        mapping.canonical_field
        for mapping in classification.mappings
        if mapping.canonical_field in {"account", "amount", "text"}
        and mapping.status != "mapped"
    )
    return LedgerSchemaReport(
        is_valid=classification.is_usable,
        present_columns=column_names,
        missing_required_columns=missing_required_columns,
        optional_columns=tuple(
            mapping.source_column
            for mapping in classification.mappings
            if mapping.status == "mapped"
            and mapping.canonical_field not in {"account", "amount", "text"}
            and mapping.source_column is not None
        ),
    )


@dataclass(frozen=True)
class _CanonicalLedgerFrame:
    dataframe: pd.DataFrame
    fields: dict[str, str]
    row_count: int
    columns: tuple[ExcelColumnProfile, ...]


def _aggregate_field(
    dataframe: pd.DataFrame,
    canonical_field: str,
    source_column: str,
    amount_column: str,
    limit: int,
) -> LedgerFieldAggregation:
    grouped = (
        dataframe.assign(
            **{source_column: dataframe[source_column].fillna("Sans valeur")},
        )
        .groupby(source_column, dropna=False)[amount_column]
        .agg(["count", "sum"])
        .sort_values(by=["sum", "count"], ascending=False)
    )
    groups = tuple(
        LedgerAggregationGroup(
            key=str(index),
            entry_count=int(row["count"]),
            amount_sum=float(row["sum"]),
        )
        for index, row in grouped.head(max(1, limit)).iterrows()
    )
    return LedgerFieldAggregation(
        canonical_field=canonical_field,
        source_column=source_column,
        total_groups=len(grouped),
        groups=groups,
    )


def _filter_frame(
    canonical_frame: _CanonicalLedgerFrame,
    filters: dict[str, object],
) -> pd.DataFrame:
    dataframe = canonical_frame.dataframe
    mask = pd.Series(True, index=dataframe.index)
    for canonical_field in ("account", "period", "tax_code", "vendor", "customer"):
        raw_value = filters.get(canonical_field)
        source_column = canonical_frame.fields.get(canonical_field)
        if raw_value is None or source_column is None:
            continue
        mask &= dataframe[source_column].map(_stable_cell_value) == str(raw_value)
    amount_column = canonical_frame.fields["amount"]
    amount_min = filters.get("amount_min")
    if isinstance(amount_min, int | float):
        mask &= dataframe[amount_column].fillna(0) >= amount_min
    amount_max = filters.get("amount_max")
    if isinstance(amount_max, int | float):
        mask &= dataframe[amount_column].fillna(0) <= amount_max
    return dataframe.loc[mask].copy()


def _serialize_query_row(
    row: pd.Series,
    fields: dict[str, str],
) -> dict[str, object]:
    serialized_row: dict[str, object] = {}
    for canonical_field in LEDGER_QUERY_OUTPUT_FIELDS:
        source_column = fields.get(canonical_field)
        if source_column is None:
            continue
        serialized_row[canonical_field] = _stable_cell_value(row[source_column])
    return serialized_row


def _calculate_metrics(
    amount_series: pd.Series,
    metrics: tuple[str, ...],
) -> dict[str, float | int]:
    requested_metrics = metrics or ("sum", "count", "average", "min", "max")
    output: dict[str, float | int] = {}
    if "sum" in requested_metrics:
        output["sum"] = round(float(amount_series.sum()), 2)
    if "count" in requested_metrics:
        output["count"] = int(amount_series.count())
    if "average" in requested_metrics:
        output["average"] = (
            round(float(amount_series.mean()), 2) if len(amount_series) else 0.0
        )
    if "min" in requested_metrics:
        output["min"] = (
            round(float(amount_series.min()), 2) if len(amount_series) else 0.0
        )
    if "max" in requested_metrics:
        output["max"] = (
            round(float(amount_series.max()), 2) if len(amount_series) else 0.0
        )
    return output


def _detect_quality_issues(
    canonical_frame: _CanonicalLedgerFrame,
) -> tuple[LedgerDataQualityIssue, ...]:
    issues: list[LedgerDataQualityIssue] = []
    issues.extend(_empty_column_issues(canonical_frame))
    issues.extend(_missing_critical_field_issues(canonical_frame))
    issues.extend(_amount_quality_issues(canonical_frame))
    currency_issue = _multiple_currency_issue(canonical_frame)
    if currency_issue is not None:
        issues.append(currency_issue)
    counterparty_issue = _missing_counterparty_issue(canonical_frame)
    if counterparty_issue is not None:
        issues.append(counterparty_issue)
    period_issue = _period_range_issue(canonical_frame)
    if period_issue is not None:
        issues.append(period_issue)
    return tuple(issues)


def _empty_column_issues(
    canonical_frame: _CanonicalLedgerFrame,
) -> tuple[LedgerDataQualityIssue, ...]:
    return tuple(
        _quality_issue(
            issue_type="empty_column",
            severity="warning",
            canonical_field=None,
            source_column=column.name,
            affected_count=canonical_frame.row_count,
            row_count=canonical_frame.row_count,
            message="Colonne totalement vide détectée.",
        )
        for column in canonical_frame.columns
        if column.non_empty_count == 0
    )


def _missing_critical_field_issues(
    canonical_frame: _CanonicalLedgerFrame,
) -> tuple[LedgerDataQualityIssue, ...]:
    issues: list[LedgerDataQualityIssue] = []
    for canonical_field in LEDGER_QUALITY_CRITICAL_FIELDS:
        source_column = canonical_frame.fields.get(canonical_field)
        if source_column is None:
            continue
        missing_count = int(canonical_frame.dataframe[source_column].isna().sum())
        if missing_count <= 0:
            continue
        issues.append(
            _quality_issue(
                issue_type="missing_critical_value",
                severity="error",
                canonical_field=canonical_field,
                source_column=source_column,
                affected_count=missing_count,
                row_count=canonical_frame.row_count,
                message="Valeur critique manquante.",
            ),
        )
    return tuple(issues)


def _amount_quality_issues(
    canonical_frame: _CanonicalLedgerFrame,
) -> tuple[LedgerDataQualityIssue, ...]:
    amount_column = canonical_frame.fields["amount"]
    numeric_amount = pd.to_numeric(
        canonical_frame.dataframe[amount_column],
        errors="coerce",
    )
    invalid_count = int(numeric_amount.isna().sum())
    if invalid_count <= 0:
        return ()
    return (
        _quality_issue(
            issue_type="invalid_amount",
            severity="error",
            canonical_field="amount",
            source_column=amount_column,
            affected_count=invalid_count,
            row_count=canonical_frame.row_count,
            message="Montant manquant ou non numérique.",
        ),
    )


def _multiple_currency_issue(
    canonical_frame: _CanonicalLedgerFrame,
) -> LedgerDataQualityIssue | None:
    currency_column = canonical_frame.fields.get("currency")
    if currency_column is None:
        return None
    currency_count = int(canonical_frame.dataframe[currency_column].dropna().nunique())
    if currency_count <= 1:
        return None
    return _quality_issue(
        issue_type="multiple_currencies",
        severity="warning",
        canonical_field="currency",
        source_column=currency_column,
        affected_count=currency_count,
        row_count=canonical_frame.row_count,
        message="Plusieurs devises détectées.",
    )


def _missing_counterparty_issue(
    canonical_frame: _CanonicalLedgerFrame,
) -> LedgerDataQualityIssue | None:
    source_columns = [
        canonical_frame.fields[canonical_field]
        for canonical_field in LEDGER_COUNTERPARTY_FIELDS
        if canonical_field in canonical_frame.fields
    ]
    if len(source_columns) < 2:
        return None
    missing_mask = canonical_frame.dataframe[source_columns].isna().all(axis=1)
    missing_count = int(missing_mask.sum())
    if missing_count <= 0:
        return None
    return _quality_issue(
        issue_type="missing_counterparty",
        severity="warning",
        canonical_field="vendor_customer",
        source_column=", ".join(source_columns),
        affected_count=missing_count,
        row_count=canonical_frame.row_count,
        message="Aucun tiers fournisseur ou client détecté sur certaines écritures.",
    )


def _period_range_issue(
    canonical_frame: _CanonicalLedgerFrame,
) -> LedgerDataQualityIssue | None:
    period_column = canonical_frame.fields.get("period")
    if period_column is None:
        return None
    numeric_period = pd.to_numeric(
        canonical_frame.dataframe[period_column],
        errors="coerce",
    )
    invalid_mask = numeric_period.isna() | ~numeric_period.between(1, 12)
    invalid_count = int(invalid_mask.sum())
    if invalid_count <= 0:
        return None
    return _quality_issue(
        issue_type="invalid_period",
        severity="warning",
        canonical_field="period",
        source_column=period_column,
        affected_count=invalid_count,
        row_count=canonical_frame.row_count,
        message="Période comptable hors plage attendue 1-12.",
    )


def _quality_issue(
    issue_type: str,
    severity: str,
    canonical_field: str | None,
    source_column: str | None,
    affected_count: int,
    row_count: int,
    message: str,
) -> LedgerDataQualityIssue:
    return LedgerDataQualityIssue(
        issue_type=issue_type,
        severity=severity,
        canonical_field=canonical_field,
        source_column=source_column,
        affected_count=affected_count,
        affected_ratio=_ratio(affected_count, row_count),
        message=message,
    )


def _count_issue_severities(
    issues: tuple[LedgerDataQualityIssue, ...],
) -> dict[str, int]:
    severity_counts = {"error": 0, "warning": 0, "info": 0}
    for issue in issues:
        severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
    return severity_counts


def _detect_tax_candidates(
    canonical_frame: _CanonicalLedgerFrame,
    rules: tuple[ClassificationRule, ...],
    limit: int,
) -> tuple[LedgerTaxCandidate, ...]:
    if not rules:
        return ()
    text_column = canonical_frame.fields["text"]
    amount_column = canonical_frame.fields["amount"]
    account_column = canonical_frame.fields["account"]
    searchable_text = canonical_frame.dataframe[text_column].map(_normalize_for_search)
    candidates: list[LedgerTaxCandidate] = []
    for rule in rules:
        if rule.category is RasCategory.OUT_OF_SCOPE:
            continue
        mask = searchable_text.map(
            lambda value, keywords=rule.keywords: _contains_any(value, keywords),
        )
        candidate_frame = canonical_frame.dataframe.loc[mask].copy()
        if candidate_frame.empty:
            continue
        top_accounts = _aggregate_field(
            dataframe=candidate_frame,
            canonical_field="account",
            source_column=account_column,
            amount_column=amount_column,
            limit=limit,
        ).groups
        candidates.append(
            LedgerTaxCandidate(
                category=rule.category.value,
                confidence=rule.confidence,
                entry_count=len(candidate_frame),
                amount_sum=round(
                    float(candidate_frame[amount_column].fillna(0).sum()),
                    2,
                ),
                matched_keywords=_matched_keywords(
                    searchable_text=searchable_text.loc[mask],
                    keywords=rule.keywords,
                ),
                top_accounts=top_accounts,
                action_required=rule.action_required,
            ),
        )
    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (candidate.amount_sum, candidate.entry_count),
            reverse=True,
        )[: max(1, limit)]
    )


def _normalize_for_search(value: object) -> str:
    without_accents = normalize("NFKD", str(value))
    ascii_value = without_accents.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_value.lower().split())


def _contains_any(value: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in value for keyword in keywords)


def _matched_keywords(
    searchable_text: pd.Series,
    keywords: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        keyword
        for keyword in keywords
        if searchable_text.map(lambda value, keyword=keyword: keyword in value).any()
    )


def _ratio(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(count / total, 4)


def _stable_cell_value(value: object) -> object:
    if pd.isna(value):
        return "Sans valeur"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return value

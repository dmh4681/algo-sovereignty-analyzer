"""
Unified Data Validation Endpoints
==================================

Provides lightweight endpoints for validating inputs before submitting them
to more expensive endpoints like /analyze or /corrections.

All endpoints return structured results with per-field error messages.
No blockchain calls are made — validation is purely local.

Endpoints:
    POST /validate/address        - Validate an Algorand wallet address
    POST /validate/expenses       - Validate monthly fixed expenses
    POST /validate/asset-category - Validate an asset category string
    POST /validate/correction     - Dry-run validate a correction payload
    POST /validate/batch          - Validate multiple inputs in one request
"""

import re
import logging
from fastapi import APIRouter
from typing import List

import algosdk.encoding

from .schemas import (
    VALID_CATEGORIES,
    AddressValidationRequest,
    AddressValidationResponse,
    ExpensesValidationRequest,
    ExpensesValidationResponse,
    AssetCategoryValidationRequest,
    AssetCategoryValidationResponse,
    CorrectionValidationRequest,
    CorrectionValidationResponse,
    BatchValidationRequest,
    BatchValidationResponse,
    BatchValidationResult,
)

logger = logging.getLogger("api.validation")

router = APIRouter(prefix="/validate", tags=["Validation"])

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

ALGORAND_ADDRESS_PATTERN = re.compile(r"^[A-Z2-7]{58}$")


def _validate_address_value(address: str):
    """Return (format_ok, checksum_ok, errors)."""
    errors: List[str] = []

    if not address or not isinstance(address, str):
        return False, False, ["Address must be a non-empty string"]

    address = address.strip()

    format_ok = bool(ALGORAND_ADDRESS_PATTERN.match(address))
    if not format_ok:
        errors.append(
            f"Address must be exactly 58 characters using A-Z and 2-7 (got {len(address)} chars)"
        )

    checksum_ok = False
    if format_ok:
        try:
            algosdk.encoding.decode_address(address)
            checksum_ok = True
        except Exception:
            errors.append("Address has an invalid checksum (bad base32 encoding)")

    return format_ok, checksum_ok, errors


def _mask_address(address: str) -> str:
    """Return a partially-masked address safe for responses."""
    if len(address) >= 14:
        return f"{address[:8]}...{address[-6:]}"
    return address


def _validate_expenses_value(value):
    """Return (valid, monthly, annual, errors)."""
    errors: List[str] = []

    if value is None:
        return False, None, None, ["Monthly expenses must be a number"]

    try:
        amount = float(value)
    except (TypeError, ValueError):
        return False, None, None, [f"Monthly expenses must be a numeric value, got '{value}'"]

    if amount < 0:
        errors.append("Monthly expenses cannot be negative")
    elif amount > 1_000_000:
        errors.append("Monthly expenses cannot exceed 1,000,000 USD")

    if errors:
        return False, None, None, errors

    return True, amount, round(amount * 12, 2), []


def _validate_category_value(category: str):
    """Return (valid, errors)."""
    errors: List[str] = []
    if not category or not isinstance(category, str):
        return False, ["Category must be a non-empty string"]

    if category not in VALID_CATEGORIES:
        sorted_cats = ", ".join(sorted(VALID_CATEGORIES))
        errors.append(f"'{category}' is not a valid category. Must be one of: {sorted_cats}")
        return False, errors

    return True, []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/address",
    response_model=AddressValidationResponse,
    summary="Validate an Algorand wallet address",
    description="""
Validate an Algorand wallet address without performing any blockchain lookup.

Two checks are performed:
1. **Format check** — address must be exactly 58 characters using only A–Z and 2–7 (base32)
2. **Checksum check** — address must pass algosdk's internal checksum validation

Use this endpoint before submitting an address to `/analyze` to surface
errors client-side before paying the cost of a full wallet analysis.
    """,
    response_description="Validation result with per-check flags",
)
async def validate_address(request: AddressValidationRequest) -> AddressValidationResponse:
    """Validate an Algorand wallet address format and checksum."""
    address = request.address.strip() if request.address else ""
    format_ok, checksum_ok, errors = _validate_address_value(address)
    valid = format_ok and checksum_ok

    return AddressValidationResponse(
        valid=valid,
        address=_mask_address(address) if address else "",
        format_check=format_ok,
        checksum_check=checksum_ok,
        errors=errors,
    )


@router.post(
    "/expenses",
    response_model=ExpensesValidationResponse,
    summary="Validate monthly fixed expenses",
    description="""
Validate a monthly fixed expenses value before using it in a sovereignty analysis.

Rules:
- Must be a numeric value
- Must be ≥ 0
- Must be ≤ 1,000,000 USD

Returns both the monthly value and the derived annual value (monthly × 12) when valid.
    """,
    response_description="Validation result with annualized value",
)
async def validate_expenses(request: ExpensesValidationRequest) -> ExpensesValidationResponse:
    """Validate monthly fixed expenses value."""
    valid, monthly, annual, errors = _validate_expenses_value(request.monthly_fixed_expenses)

    return ExpensesValidationResponse(
        valid=valid,
        monthly_expenses=monthly,
        annual_expenses=annual,
        errors=errors,
    )


@router.post(
    "/asset-category",
    response_model=AssetCategoryValidationResponse,
    summary="Validate an asset category string",
    description="""
Validate that a category string is one of the four recognized sovereignty categories:

| Category | Description |
|----------|-------------|
| `hard_money` | Bitcoin, Gold, Silver |
| `algo` | ALGO and liquid staking tokens |
| `dollars` | Stablecoins (USDC, USDT, DAI, ...) |
| `shitcoin` | Everything else |

Useful for pre-validating classification correction payloads.
    """,
    response_description="Validation result with list of valid categories",
)
async def validate_asset_category(request: AssetCategoryValidationRequest) -> AssetCategoryValidationResponse:
    """Validate an asset category string."""
    valid, errors = _validate_category_value(request.category)

    return AssetCategoryValidationResponse(
        valid=valid,
        category=request.category,
        valid_categories=sorted(VALID_CATEGORIES),
        errors=errors,
    )


@router.post(
    "/correction",
    response_model=CorrectionValidationResponse,
    summary="Dry-run validate a classification correction",
    description="""
Validate all fields of a classification correction payload **without** actually
submitting it. Returns per-field errors so the caller can fix issues before
calling `POST /corrections`.

Fields validated:
- `asset_id` — must be non-empty, max 20 chars
- `asset_name` — must be non-empty, max 100 chars
- `ticker` — must be non-empty, max 20 chars
- `original_category` — must be a valid category
- `corrected_category` — must be a valid category
- `reason` — optional, max 500 chars if provided
- `submitted_by` — optional, must be valid Algorand address if provided
    """,
    response_description="Per-field validation errors",
)
async def validate_correction(request: CorrectionValidationRequest) -> CorrectionValidationResponse:
    """Dry-run validate a classification correction payload."""
    field_errors: dict = {}

    # asset_id
    if not request.asset_id or not request.asset_id.strip():
        field_errors.setdefault("asset_id", []).append("Asset ID is required")
    elif len(request.asset_id) > 20:
        field_errors.setdefault("asset_id", []).append("Asset ID must be 20 characters or fewer")

    # asset_name
    if not request.asset_name or not request.asset_name.strip():
        field_errors.setdefault("asset_name", []).append("Asset name is required")
    elif len(request.asset_name) > 100:
        field_errors.setdefault("asset_name", []).append("Asset name must be 100 characters or fewer")

    # ticker
    if not request.ticker or not request.ticker.strip():
        field_errors.setdefault("ticker", []).append("Ticker is required")
    elif len(request.ticker) > 20:
        field_errors.setdefault("ticker", []).append("Ticker must be 20 characters or fewer")

    # original_category
    orig_valid, orig_errors = _validate_category_value(request.original_category)
    if not orig_valid:
        field_errors.setdefault("original_category", []).extend(orig_errors)

    # corrected_category
    corr_valid, corr_errors = _validate_category_value(request.corrected_category)
    if not corr_valid:
        field_errors.setdefault("corrected_category", []).extend(corr_errors)
    elif request.original_category == request.corrected_category and orig_valid:
        field_errors.setdefault("corrected_category", []).append(
            "corrected_category must differ from original_category"
        )

    # reason (optional)
    if request.reason is not None and len(request.reason) > 500:
        field_errors.setdefault("reason", []).append("Reason must be 500 characters or fewer")

    # submitted_by (optional Algorand address)
    if request.submitted_by is not None:
        _, _, addr_errors = _validate_address_value(request.submitted_by)
        if addr_errors:
            field_errors.setdefault("submitted_by", []).extend(addr_errors)

    return CorrectionValidationResponse(
        valid=len(field_errors) == 0,
        field_errors=field_errors,
    )


@router.post(
    "/batch",
    response_model=BatchValidationResponse,
    summary="Validate multiple inputs in a single request",
    description="""
Validate up to **50 inputs** in a single request. Each item specifies:
- `type` — one of `"address"`, `"expenses"`, `"category"`
- `value` — the value to validate
- `label` — optional caller-defined label echoed in the response (useful for mapping results back to form fields)

Results are returned in the same order as the submitted items.
Items with an unrecognized `type` are marked invalid with an appropriate error.
    """,
    response_description="Per-item validation results with overall summary",
)
async def validate_batch(request: BatchValidationRequest) -> BatchValidationResponse:
    """Validate multiple inputs of mixed types in a single request."""
    results: List[BatchValidationResult] = []

    for item in request.items:
        item_type = item.type.lower() if isinstance(item.type, str) else ""
        label = item.label

        if item_type == "address":
            address = str(item.value).strip() if item.value is not None else ""
            _, _, errors = _validate_address_value(address)
            results.append(BatchValidationResult(type=item_type, label=label, valid=not errors, errors=errors))

        elif item_type == "expenses":
            valid, _, _, errors = _validate_expenses_value(item.value)
            results.append(BatchValidationResult(type=item_type, label=label, valid=valid, errors=errors))

        elif item_type == "category":
            category = str(item.value) if item.value is not None else ""
            valid, errors = _validate_category_value(category)
            results.append(BatchValidationResult(type=item_type, label=label, valid=valid, errors=errors))

        else:
            results.append(BatchValidationResult(
                type=item_type or "unknown",
                label=label,
                valid=False,
                errors=[f"Unknown validation type '{item.type}'. Must be one of: address, expenses, category"],
            ))

    valid_count = sum(1 for r in results if r.valid)
    invalid_count = len(results) - valid_count

    return BatchValidationResponse(
        all_valid=invalid_count == 0,
        total_items=len(results),
        valid_count=valid_count,
        invalid_count=invalid_count,
        results=results,
    )

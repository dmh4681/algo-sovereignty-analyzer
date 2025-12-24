"""
Infrastructure Audit API Routes
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any, List
from dataclasses import asdict
import traceback

from .infra_audit import (
    audit_infrastructure,
    get_infrastructure_summary,
    RelayNode
)
from .participation_audit import (
    audit_participation,
    get_participation_summary
)

router = APIRouter(prefix="/sovereignty", tags=["infrastructure"])


@router.get("/infrastructure")
async def get_infrastructure_audit(
    force_refresh: bool = Query(False, description="Bypass cache and fetch fresh data")
) -> Dict[str, Any]:
    """
    Get Algorand relay node infrastructure audit.

    Returns analysis of relay node centralization including:
    - Total relay nodes discovered
    - Cloud vs sovereign node breakdown
    - Decentralization score (0-100)
    - Provider and geographic distribution

    Data is cached for 4 hours unless force_refresh=true
    """
    try:
        return get_infrastructure_summary(force_refresh=force_refresh)
    except Exception as e:
        print(f"Infrastructure audit error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Infrastructure audit failed: {str(e)}")


@router.get("/infrastructure/nodes")
async def get_infrastructure_nodes(
    classification: str = Query(None, description="Filter by 'cloud' or 'sovereign'"),
    country: str = Query(None, description="Filter by country name")
) -> Dict[str, Any]:
    """
    Get detailed list of all relay nodes.

    Optional filters:
    - classification: Filter to only "cloud" or "sovereign" nodes
    - country: Filter to nodes in a specific country
    """
    result = audit_infrastructure()

    nodes = result.nodes

    # Apply filters
    if classification:
        nodes = [n for n in nodes if n.classification == classification.lower()]

    if country:
        nodes = [n for n in nodes if n.country.lower() == country.lower()]

    # Convert dataclass to dict
    nodes_dict = [
        {
            "hostname": n.hostname,
            "ip": n.ip,
            "port": n.port,
            "isp": n.isp,
            "org": n.org,
            "country": n.country,
            "region": n.region,
            "city": n.city,
            "asn": n.asn,
            "classification": n.classification
        }
        for n in nodes
    ]

    return {
        "total": len(nodes_dict),
        "filters_applied": {
            "classification": classification,
            "country": country
        },
        "nodes": nodes_dict
    }


@router.get("/infrastructure/providers")
async def get_provider_breakdown() -> Dict[str, Any]:
    """
    Get breakdown of relay nodes by provider/organization.

    Shows which cloud providers and organizations host relay nodes.
    """
    result = audit_infrastructure()

    # Categorize providers
    cloud_providers = {}
    sovereign_providers = {}

    for node in result.nodes:
        provider = node.org if node.org != "Unknown" else node.isp
        if node.classification == "cloud":
            cloud_providers[provider] = cloud_providers.get(provider, 0) + 1
        else:
            sovereign_providers[provider] = sovereign_providers.get(provider, 0) + 1

    return {
        "cloud_providers": dict(sorted(cloud_providers.items(), key=lambda x: -x[1])),
        "sovereign_providers": dict(sorted(sovereign_providers.items(), key=lambda x: -x[1])),
        "cloud_total": sum(cloud_providers.values()),
        "sovereign_total": sum(sovereign_providers.values()),
        "timestamp": result.timestamp
    }


@router.get("/infrastructure/countries")
async def get_country_breakdown() -> Dict[str, Any]:
    """
    Get geographic distribution of relay nodes.

    Shows which countries host relay nodes and their classification breakdown.
    """
    result = audit_infrastructure()

    country_data: Dict[str, Dict[str, int]] = {}

    for node in result.nodes:
        country = node.country
        if country not in country_data:
            country_data[country] = {"total": 0, "cloud": 0, "sovereign": 0}

        country_data[country]["total"] += 1
        country_data[country][node.classification] += 1

    # Sort by total nodes
    sorted_countries = dict(
        sorted(country_data.items(), key=lambda x: -x[1]["total"])
    )

    return {
        "countries": sorted_countries,
        "total_countries": len(sorted_countries),
        "timestamp": result.timestamp
    }


# --- Participation Endpoints ---

@router.get("/participation")
async def get_participation_stats(
    force_refresh: bool = Query(False, description="Bypass cache and fetch fresh data")
) -> Dict[str, Any]:
    """
    Get Algorand consensus participation statistics.

    Returns:
    - Online stake (ALGO participating in consensus)
    - Percentage of total supply online
    - Top validators by stake
    - Incentive-eligible account stats

    Data is cached for 15 minutes unless force_refresh=true
    """
    try:
        return get_participation_summary(force_refresh=force_refresh)
    except Exception as e:
        print(f"Participation audit error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Participation audit failed: {str(e)}")

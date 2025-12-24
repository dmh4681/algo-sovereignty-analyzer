"""
Infrastructure Audit Service

Analyzes Algorand relay node infrastructure to determine network centralization.
Discovers relay nodes via DNS SRV records, resolves IPs, and classifies ISPs.
"""

import dns.resolver
import socket
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading


# Cloud provider ASN/Org patterns for classification
CLOUD_PROVIDERS = {
    "Amazon",
    "AWS",
    "Google",
    "Microsoft",
    "Azure",
    "DigitalOcean",
    "Linode",
    "Vultr",
    "OVH",
    "Hetzner",
    "Alibaba",
    "Tencent",
    "Oracle",
    "IBM Cloud",
    "Cloudflare",
    "Equinix",
    "Packet",
    "Rackspace",
}


@dataclass
class RelayNode:
    """Represents an Algorand relay node"""
    hostname: str
    ip: str
    port: int
    isp: str
    org: str
    country: str
    region: str
    city: str
    asn: str
    classification: str  # "cloud" or "sovereign"


@dataclass
class InfrastructureAuditResult:
    """Result of infrastructure audit"""
    total_nodes: int
    cloud_nodes: int
    sovereign_nodes: int
    cloud_percentage: float
    sovereign_percentage: float
    decentralization_score: float  # 0-100, higher = more decentralized
    nodes: List[RelayNode]
    by_provider: Dict[str, int]
    by_country: Dict[str, int]
    timestamp: str
    cache_expires: str


class InfrastructureCache:
    """Thread-safe cache for infrastructure audit results"""

    def __init__(self, ttl_hours: int = 4):
        self._cache: Optional[InfrastructureAuditResult] = None
        self._lock = threading.Lock()
        self._ttl = timedelta(hours=ttl_hours)

    def get(self) -> Optional[InfrastructureAuditResult]:
        """Get cached result if valid"""
        with self._lock:
            if self._cache is None:
                return None
            # Check if cache expired
            # Handle "Z" suffix for ISO format (Python < 3.11 compatibility)
            timestamp_str = self._cache.timestamp.replace("Z", "+00:00")
            cache_time = datetime.fromisoformat(timestamp_str).replace(tzinfo=None)
            if datetime.utcnow() - cache_time > self._ttl:
                self._cache = None
                return None
            return self._cache

    def set(self, result: InfrastructureAuditResult):
        """Store result in cache"""
        with self._lock:
            self._cache = result

    def clear(self):
        """Clear the cache"""
        with self._lock:
            self._cache = None


# Global cache instance
_infra_cache = InfrastructureCache(ttl_hours=4)


def discover_relay_nodes(network: str = "mainnet") -> List[Dict[str, Any]]:
    """
    Discover Algorand relay nodes via DNS SRV records.

    Args:
        network: "mainnet" or "testnet"

    Returns:
        List of dicts with hostname and port
    """
    srv_domain = f"_algobootstrap._tcp.{network}.algorand.network"
    nodes = []

    try:
        answers = dns.resolver.resolve(srv_domain, 'SRV')
        for rdata in answers:
            hostname = str(rdata.target).rstrip('.')
            port = rdata.port
            nodes.append({
                "hostname": hostname,
                "port": port,
                "priority": rdata.priority,
                "weight": rdata.weight
            })
    except dns.resolver.NXDOMAIN:
        print(f"DNS domain not found: {srv_domain}")
    except dns.resolver.NoAnswer:
        print(f"No SRV records found for: {srv_domain}")
    except Exception as e:
        print(f"DNS lookup error: {e}")

    return nodes


def resolve_hostname(hostname: str) -> Optional[str]:
    """Resolve hostname to IP address"""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


def batch_lookup_ips(ips: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Batch lookup IP geolocation and ISP info using ip-api.com

    Free tier allows 45 requests/minute, batch endpoint allows up to 100 IPs per request
    """
    results = {}

    # ip-api.com batch endpoint
    batch_url = "http://ip-api.com/batch"

    # Process in chunks of 100 (api limit)
    chunk_size = 100
    for i in range(0, len(ips), chunk_size):
        chunk = ips[i:i + chunk_size]

        # Prepare batch request
        payload = [
            {
                "query": ip,
                "fields": "status,country,regionName,city,isp,org,as,query"
            }
            for ip in chunk
        ]

        try:
            response = requests.post(
                batch_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                for item in data:
                    if item.get("status") == "success":
                        ip = item.get("query")
                        results[ip] = {
                            "country": item.get("country", "Unknown"),
                            "region": item.get("regionName", "Unknown"),
                            "city": item.get("city", "Unknown"),
                            "isp": item.get("isp", "Unknown"),
                            "org": item.get("org", "Unknown"),
                            "asn": item.get("as", "Unknown")
                        }
        except requests.RequestException as e:
            print(f"IP lookup error: {e}")

    return results


def classify_provider(isp: str, org: str, asn: str) -> str:
    """
    Classify if a node is running on centralized cloud or sovereign infrastructure.

    Returns "cloud" or "sovereign"
    """
    # Check ISP, Org, and ASN against known cloud providers
    check_strings = [isp.upper(), org.upper(), asn.upper()]

    for check in check_strings:
        for provider in CLOUD_PROVIDERS:
            if provider.upper() in check:
                return "cloud"

    return "sovereign"


def calculate_decentralization_score(
    cloud_pct: float,
    provider_distribution: Dict[str, int],
    country_distribution: Dict[str, int]
) -> float:
    """
    Calculate decentralization score (0-100).

    Factors:
    - Percentage of sovereign nodes (40% weight)
    - Provider diversity (30% weight)
    - Geographic diversity (30% weight)
    """
    # Sovereign percentage score (0-40)
    sovereign_pct = 100 - cloud_pct
    sovereign_score = (sovereign_pct / 100) * 40

    # Provider diversity score (0-30)
    # Uses Herfindahl-Hirschman Index (HHI) - lower is more diverse
    if provider_distribution:
        total = sum(provider_distribution.values())
        hhi = sum((count / total * 100) ** 2 for count in provider_distribution.values())
        # HHI ranges from 100 (one provider) to 10000 (monopoly)
        # Convert to 0-30 score where more providers = higher score
        provider_score = max(0, 30 * (1 - hhi / 10000))
    else:
        provider_score = 0

    # Geographic diversity score (0-30)
    if country_distribution:
        total = sum(country_distribution.values())
        geo_hhi = sum((count / total * 100) ** 2 for count in country_distribution.values())
        geo_score = max(0, 30 * (1 - geo_hhi / 10000))
    else:
        geo_score = 0

    return round(sovereign_score + provider_score + geo_score, 1)


def audit_infrastructure(network: str = "mainnet", force_refresh: bool = False) -> InfrastructureAuditResult:
    """
    Perform full infrastructure audit.

    Args:
        network: "mainnet" or "testnet"
        force_refresh: If True, bypass cache

    Returns:
        InfrastructureAuditResult with all node data and statistics
    """
    # Check cache first
    if not force_refresh:
        cached = _infra_cache.get()
        if cached:
            return cached

    # Discover relay nodes
    raw_nodes = discover_relay_nodes(network)

    # Resolve hostnames to IPs
    hostname_to_ip = {}
    ips = []
    for node in raw_nodes:
        ip = resolve_hostname(node["hostname"])
        if ip:
            hostname_to_ip[node["hostname"]] = ip
            if ip not in ips:
                ips.append(ip)

    # Batch lookup ISP info
    ip_info = batch_lookup_ips(ips)

    # Build relay node objects
    nodes: List[RelayNode] = []
    by_provider: Dict[str, int] = {}
    by_country: Dict[str, int] = {}
    cloud_count = 0
    sovereign_count = 0

    for raw_node in raw_nodes:
        hostname = raw_node["hostname"]
        ip = hostname_to_ip.get(hostname)

        if not ip:
            continue

        info = ip_info.get(ip, {})
        isp = info.get("isp", "Unknown")
        org = info.get("org", "Unknown")
        asn = info.get("asn", "Unknown")
        country = info.get("country", "Unknown")

        classification = classify_provider(isp, org, asn)

        node = RelayNode(
            hostname=hostname,
            ip=ip,
            port=raw_node["port"],
            isp=isp,
            org=org,
            country=country,
            region=info.get("region", "Unknown"),
            city=info.get("city", "Unknown"),
            asn=asn,
            classification=classification
        )
        nodes.append(node)

        # Track provider distribution (use org for grouping)
        provider_key = org if org != "Unknown" else isp
        by_provider[provider_key] = by_provider.get(provider_key, 0) + 1

        # Track country distribution
        by_country[country] = by_country.get(country, 0) + 1

        # Count classification
        if classification == "cloud":
            cloud_count += 1
        else:
            sovereign_count += 1

    total = len(nodes)
    cloud_pct = (cloud_count / total * 100) if total > 0 else 0
    sovereign_pct = (sovereign_count / total * 100) if total > 0 else 0

    # Calculate decentralization score
    decentralization = calculate_decentralization_score(
        cloud_pct, by_provider, by_country
    )

    now = datetime.utcnow()
    result = InfrastructureAuditResult(
        total_nodes=total,
        cloud_nodes=cloud_count,
        sovereign_nodes=sovereign_count,
        cloud_percentage=round(cloud_pct, 1),
        sovereign_percentage=round(sovereign_pct, 1),
        decentralization_score=decentralization,
        nodes=nodes,
        by_provider=dict(sorted(by_provider.items(), key=lambda x: -x[1])),
        by_country=dict(sorted(by_country.items(), key=lambda x: -x[1])),
        timestamp=now.isoformat() + "Z",
        cache_expires=(now + timedelta(hours=4)).isoformat() + "Z"
    )

    # Cache result
    _infra_cache.set(result)

    return result


def get_infrastructure_summary(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get a simplified summary for API response.
    """
    result = audit_infrastructure(force_refresh=force_refresh)

    return {
        "total_nodes": result.total_nodes,
        "cloud_nodes": result.cloud_nodes,
        "sovereign_nodes": result.sovereign_nodes,
        "cloud_percentage": result.cloud_percentage,
        "sovereign_percentage": result.sovereign_percentage,
        "decentralization_score": result.decentralization_score,
        "top_providers": dict(list(result.by_provider.items())[:10]),
        "top_countries": dict(list(result.by_country.items())[:10]),
        "timestamp": result.timestamp,
        "cache_expires": result.cache_expires,
        "interpretation": get_interpretation(result.decentralization_score, result.cloud_percentage)
    }


def get_interpretation(score: float, cloud_pct: float) -> Dict[str, str]:
    """Generate human-readable interpretation of results"""

    if score >= 70:
        health = "healthy"
        color = "green"
        message = "Network infrastructure is well-decentralized"
    elif score >= 50:
        health = "moderate"
        color = "yellow"
        message = "Network has moderate decentralization, room for improvement"
    elif score >= 30:
        health = "concerning"
        color = "orange"
        message = "Network infrastructure shows significant centralization"
    else:
        health = "critical"
        color = "red"
        message = "Network is highly centralized - sovereignty risk"

    return {
        "health": health,
        "color": color,
        "message": message,
        "cloud_dependency": f"{cloud_pct:.0f}% of relay nodes run on centralized cloud providers",
        "recommendation": (
            "Consider running your own relay node to improve network sovereignty"
            if cloud_pct > 50 else
            "Network has good sovereign infrastructure coverage"
        )
    }

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


# TIER 3: Hyperscale Cloud - "Kill Switch" zone
# These providers have centralized control and government compliance obligations
HYPERSCALE_CLOUD = {
    "Amazon",
    "AWS",
    "Google",
    "Microsoft",
    "Azure",
    "Alibaba",
    "Tencent",
    "Oracle",
    "IBM Cloud",
}

# TIER 2: Corporate/Data Center - Better than hyperscale but still centralized
# Single points of failure, corporate billing departments can shut down nodes
CORPORATE_HOSTING = {
    "OVH",
    "Hetzner",
    "DigitalOcean",
    "Linode",
    "Akamai",  # Linode parent
    "Vultr",
    "Cloudflare",
    "Equinix",
    "Packet",
    "Rackspace",
    "TeraSwitch",
    "Leaseweb",
    "Contabo",
    "Scaleway",
    "UpCloud",
    "Kamatera",
    "Hostinger",
    "Ionos",
    "1&1",
    "GoDaddy",
    "HostGator",
    "Bluehost",
    "InMotion",
    "SiteGround",
    "A2 Hosting",
    "DreamHost",
    "Liquid Web",
    "Namecheap",
    "Hostwinds",
    "InterServer",
    "Fasthosts",
    "Hostway",
    "SingleHop",
    "SoftLayer",
    "CenturyLink",
    "Lumen",
    "Zayo",
    "GTT",
    "Cogent",
    "NTT",
    "Level3",
    "Telia",
    "Hurricane Electric",
    "HE.net",
    "PhoenixNAP",
    "QuadraNet",
    "ColoCrossing",
    "BuyVM",
    "RamNode",
    "ServerHub",
    "Shock Hosting",
    "HostUS",
}

# TIER 1: Sovereign/Residential ISPs - True decentralization
# Residential connections are harder to shut down en masse
RESIDENTIAL_ISPS = {
    "Verizon",
    "Comcast",
    "Xfinity",
    "AT&T",
    "T-Mobile",
    "Sprint",
    "Charter",
    "Spectrum",
    "Cox",
    "CenturyLink",  # residential only
    "Frontier",
    "Starlink",
    "SpaceX",
    "HughesNet",
    "Viasat",
    "Deutsche Telekom",
    "Vodafone",
    "Orange",
    "Telefonica",
    "British Telecom",
    "BT",
    "Sky Broadband",
    "Virgin Media",
    "TalkTalk",
    "Rogers",
    "Bell Canada",
    "Telus",
    "Shaw",
    "Optus",
    "Telstra",
    "NBN",
    "TPG",
    "iiNet",
}

# Provider name normalization rules (substring matching, case-insensitive)
# This consolidates different legal entities into canonical names
PROVIDER_NORMALIZATION = {
    # Hyperscale cloud providers (Tier 3)
    "amazon": "Amazon AWS",
    "aws": "Amazon AWS",
    "google": "Google Cloud",
    "microsoft": "Microsoft Azure",
    "azure": "Microsoft Azure",
    "alibaba": "Alibaba Cloud",
    "oracle": "Oracle Cloud",
    "ibm cloud": "IBM Cloud",
    "tencent": "Tencent Cloud",
    # Corporate hosting providers (Tier 2)
    "ovh": "OVHcloud",
    "hetzner": "Hetzner",
    "digitalocean": "DigitalOcean",
    "linode": "Linode/Akamai",
    "akamai": "Linode/Akamai",
    "vultr": "Vultr",
    "choopa": "Vultr",
    "constant company": "Vultr",
    "teraswitch": "TeraSwitch",
    "leaseweb": "Leaseweb",
    "contabo": "Contabo",
    "scaleway": "Scaleway",
    "equinix": "Equinix",
    "rackspace": "Rackspace",
    "softlayer": "IBM/SoftLayer",
    "cloudflare": "Cloudflare",
    "phoenixnap": "PhoenixNAP",
    "quadranet": "QuadraNet",
    "colocrossing": "ColoCrossing",
    "hurricane electric": "Hurricane Electric",
    "he.net": "Hurricane Electric",
    "cogent": "Cogent",
    "ntt": "NTT",
    "telia": "Telia",
    "zayo": "Zayo",
    "lumen": "Lumen/CenturyLink",
    "level3": "Lumen/CenturyLink",
    "centurylink": "Lumen/CenturyLink",
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
    classification: str  # "sovereign", "corporate", or "hyperscale"
    provider_normalized: str  # Consolidated provider name


@dataclass
class InfrastructureAuditResult:
    """Result of infrastructure audit"""
    total_nodes: int
    # 3-tier classification counts
    sovereign_nodes: int      # Tier 1: Residential ISPs (green)
    corporate_nodes: int      # Tier 2: Data centers (yellow)
    hyperscale_nodes: int     # Tier 3: AWS/Google/Azure (red)
    # Percentages
    sovereign_percentage: float
    corporate_percentage: float
    hyperscale_percentage: float
    # Legacy fields for backward compatibility
    cloud_nodes: int          # corporate + hyperscale
    cloud_percentage: float
    decentralization_score: float  # 0-100, higher = more decentralized
    nodes: List[RelayNode]
    by_provider: Dict[str, int]  # Consolidated provider names
    by_country: Dict[str, int]
    by_tier: Dict[str, int]      # {"sovereign": X, "corporate": Y, "hyperscale": Z}
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


def normalize_provider(isp: str, org: str) -> str:
    """
    Normalize provider name to consolidate variants.

    This merges different legal entities of the same company:
    - "OVH US LLC", "OVH GmbH", "OVH SAS" -> "OVHcloud"
    - "Amazon.com", "AWS", "Amazon Technologies" -> "Amazon AWS"

    Uses substring matching (case-insensitive) for flexibility.
    """
    # Combine ISP and org strings for searching
    combined = f"{isp} {org}".lower()

    # Check against normalization rules (order matters - check longer matches first)
    # Sort by key length descending to match longer strings first
    for pattern, canonical in sorted(PROVIDER_NORMALIZATION.items(), key=lambda x: -len(x[0])):
        if pattern in combined:
            return canonical

    # No match found - return the most meaningful identifier
    if org and org != "Unknown" and len(org) > 3:
        return org
    if isp and isp != "Unknown":
        return isp
    return "Unknown"


def classify_provider(isp: str, org: str, asn: str) -> str:
    """
    Classify node infrastructure into 3 tiers:
    - "sovereign": Residential ISPs (Tier 1 - green)
    - "corporate": Data center/hosting (Tier 2 - yellow)
    - "hyperscale": AWS/Google/Azure (Tier 3 - red)
    """
    check_strings = [isp.upper(), org.upper(), asn.upper()]

    # First check for hyperscale cloud (most dangerous)
    for check in check_strings:
        for provider in HYPERSCALE_CLOUD:
            if provider.upper() in check:
                return "hyperscale"

    # Then check for corporate/data center hosting
    for check in check_strings:
        for provider in CORPORATE_HOSTING:
            if provider.upper() in check:
                return "corporate"

    # Check if it's a known residential ISP (definitely sovereign)
    for check in check_strings:
        for provider in RESIDENTIAL_ISPS:
            if provider.upper() in check:
                return "sovereign"

    # Default: if we can't identify it, assume corporate (conservative)
    # Unknown hosting providers are more likely data centers than residential
    return "corporate"


def calculate_decentralization_score(
    sovereign_pct: float,
    corporate_pct: float,
    hyperscale_pct: float,
    provider_distribution: Dict[str, int],
    country_distribution: Dict[str, int]
) -> float:
    """
    Calculate decentralization score (0-100) for RELAY NODES.

    KEY INSIGHT: Relay nodes REQUIRE data center hosting due to bandwidth/latency
    requirements (TB/month, <50ms latency). Running relays on residential connections
    is physically impossible. Therefore:

    - Tier 2 (Corporate/Data Centers) is EXPECTED and ACCEPTABLE for relays
    - Tier 3 (Hyperscale: AWS/Google/Azure) is DANGEROUS (kill switch risk)
    - Tier 1 (Residential) is a BONUS but rare for relays

    Scoring Model (starts at 100, deductions apply):
    1. Hyperscale Penalty: -1 point per 1% in Tier 3
    2. Concentration Penalty: -1 point per 1% that largest provider exceeds 15%
    3. Geographic Concentration: -0.5 points per 1% that largest country exceeds 40%
    4. Sovereign Bonus: +0.25 points per 1% in Tier 1 (rare but valuable)
    """
    score = 100.0

    # 1. HYPERSCALE PENALTY: Heavy penalty for AWS/Google/Azure
    # These mega-corps can shut off crypto at DNS/BGP level globally
    hyperscale_penalty = hyperscale_pct  # -1 point per 1%
    score -= hyperscale_penalty

    # 2. PROVIDER CONCENTRATION PENALTY
    # Penalize oligopoly - if any single provider > 15%, deduct the excess
    if provider_distribution:
        total = sum(provider_distribution.values())
        if total > 0:
            max_share = max(provider_distribution.values()) / total * 100
            if max_share > 15:
                concentration_penalty = max_share - 15  # -1 point per 1% over 15%
                score -= concentration_penalty

    # 3. GEOGRAPHIC CONCENTRATION PENALTY
    # Penalize if too many nodes in one country (jurisdiction risk)
    if country_distribution:
        total = sum(country_distribution.values())
        if total > 0:
            max_country_share = max(country_distribution.values()) / total * 100
            if max_country_share > 40:
                geo_penalty = (max_country_share - 40) * 0.5  # -0.5 per 1% over 40%
                score -= geo_penalty

    # 4. SOVEREIGN BONUS: Reward any residential/home nodes (rare for relays)
    sovereign_bonus = sovereign_pct * 0.25  # +0.25 per 1%
    score += sovereign_bonus

    # Clamp score to 0-100 range
    return round(max(0, min(100, score)), 1)


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

    # 3-tier counts
    sovereign_count = 0
    corporate_count = 0
    hyperscale_count = 0

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
        provider_normalized = normalize_provider(isp, org)

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
            classification=classification,
            provider_normalized=provider_normalized
        )
        nodes.append(node)

        # Track provider distribution using normalized names
        by_provider[provider_normalized] = by_provider.get(provider_normalized, 0) + 1

        # Track country distribution
        by_country[country] = by_country.get(country, 0) + 1

        # Count by tier
        if classification == "sovereign":
            sovereign_count += 1
        elif classification == "corporate":
            corporate_count += 1
        else:  # hyperscale
            hyperscale_count += 1

    total = len(nodes)

    # Calculate percentages
    sovereign_pct = (sovereign_count / total * 100) if total > 0 else 0
    corporate_pct = (corporate_count / total * 100) if total > 0 else 0
    hyperscale_pct = (hyperscale_count / total * 100) if total > 0 else 0

    # Legacy: cloud = corporate + hyperscale
    cloud_count = corporate_count + hyperscale_count
    cloud_pct = corporate_pct + hyperscale_pct

    # Calculate decentralization score with new 3-tier model
    decentralization = calculate_decentralization_score(
        sovereign_pct, corporate_pct, hyperscale_pct,
        by_provider, by_country
    )

    now = datetime.utcnow()
    result = InfrastructureAuditResult(
        total_nodes=total,
        sovereign_nodes=sovereign_count,
        corporate_nodes=corporate_count,
        hyperscale_nodes=hyperscale_count,
        sovereign_percentage=round(sovereign_pct, 1),
        corporate_percentage=round(corporate_pct, 1),
        hyperscale_percentage=round(hyperscale_pct, 1),
        cloud_nodes=cloud_count,
        cloud_percentage=round(cloud_pct, 1),
        decentralization_score=decentralization,
        nodes=nodes,
        by_provider=dict(sorted(by_provider.items(), key=lambda x: -x[1])),
        by_country=dict(sorted(by_country.items(), key=lambda x: -x[1])),
        by_tier={
            "sovereign": sovereign_count,
            "corporate": corporate_count,
            "hyperscale": hyperscale_count
        },
        timestamp=now.isoformat() + "Z",
        cache_expires=(now + timedelta(hours=4)).isoformat() + "Z"
    )

    # Cache result
    _infra_cache.set(result)

    return result


def get_infrastructure_summary(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get a simplified summary for API response.

    Returns relay node infrastructure audit with proper context:
    - Relay nodes REQUIRE data center hosting (Tier 2 is acceptable)
    - Hyperscale cloud (Tier 3) is the real risk
    - Provider concentration is the "oligopoly trap"
    """
    result = audit_infrastructure(force_refresh=force_refresh)

    return {
        "total_nodes": result.total_nodes,
        # 3-tier breakdown
        "sovereign_nodes": result.sovereign_nodes,
        "corporate_nodes": result.corporate_nodes,
        "hyperscale_nodes": result.hyperscale_nodes,
        "sovereign_percentage": result.sovereign_percentage,
        "corporate_percentage": result.corporate_percentage,
        "hyperscale_percentage": result.hyperscale_percentage,
        # Legacy fields
        "cloud_nodes": result.cloud_nodes,
        "cloud_percentage": result.cloud_percentage,
        # Score and distribution
        "decentralization_score": result.decentralization_score,
        "by_tier": result.by_tier,
        "top_providers": dict(list(result.by_provider.items())[:10]),
        "top_countries": dict(list(result.by_country.items())[:10]),
        "timestamp": result.timestamp,
        "cache_expires": result.cache_expires,
        "interpretation": get_interpretation(
            result.decentralization_score,
            result.sovereign_percentage,
            result.corporate_percentage,
            result.hyperscale_percentage,
            result.by_provider  # Pass provider distribution for concentration analysis
        ),
        # Context for frontend
        "audit_context": {
            "node_type": "relay",
            "note": "Relay nodes require data center hosting due to bandwidth/latency requirements. Tier 2 (corporate) is expected; Tier 3 (hyperscale) is the risk.",
            "scoring_model": "100 - hyperscale% - concentration_penalty - geo_penalty + sovereign_bonus"
        }
    }


def get_interpretation(
    score: float,
    sovereign_pct: float,
    corporate_pct: float,
    hyperscale_pct: float,
    provider_distribution: Optional[Dict[str, int]] = None
) -> Dict[str, str]:
    """
    Generate human-readable interpretation of relay node infrastructure audit.

    Context: Relay nodes REQUIRE data center hosting due to bandwidth requirements.
    - Tier 2 (Corporate) is acceptable for relays
    - Tier 3 (Hyperscale) is the real risk
    - Provider concentration is the "oligopoly trap"
    """
    # Calculate largest provider share for messaging
    largest_provider = ""
    largest_share = 0.0
    if provider_distribution:
        total = sum(provider_distribution.values())
        if total > 0:
            largest_provider = max(provider_distribution, key=provider_distribution.get)
            largest_share = provider_distribution[largest_provider] / total * 100

    # Health assessment based on new scoring model
    if score >= 85:
        health = "excellent"
        color = "green"
        message = "Relay infrastructure is well-distributed across independent providers"
    elif score >= 70:
        health = "healthy"
        color = "green"
        message = "Network avoided the AWS trap with good provider diversity"
    elif score >= 55:
        health = "moderate"
        color = "yellow"
        message = "Network faces oligopoly risk from provider concentration"
    elif score >= 40:
        health = "concerning"
        color = "orange"
        message = "Significant concentration risk - few providers control too much"
    else:
        health = "critical"
        color = "red"
        message = "Critical centralization - network sovereignty at risk"

    # Build tier analysis
    tier_analysis = []
    if hyperscale_pct == 0:
        tier_analysis.append("✓ No hyperscale cloud dependency (AWS/Google/Azure)")
    else:
        tier_analysis.append(f"⚠ {hyperscale_pct:.0f}% on hyperscale cloud (kill switch risk)")

    if corporate_pct > 0:
        tier_analysis.append(f"• {corporate_pct:.0f}% on independent data centers (acceptable for relays)")

    if sovereign_pct > 0:
        tier_analysis.append(f"★ {sovereign_pct:.0f}% on residential/sovereign infrastructure (bonus)")

    # Risk assessment focused on real relay node concerns
    if hyperscale_pct > 20:
        risk = "HIGH RISK: Over 20% of relays on hyperscale cloud - vulnerable to coordinated shutdown"
    elif hyperscale_pct > 0:
        risk = f"MODERATE RISK: {hyperscale_pct:.0f}% on hyperscale cloud - some kill switch exposure"
    elif largest_share > 33:
        risk = f"OLIGOPOLY RISK: {largest_provider} controls {largest_share:.0f}% of relays"
    elif largest_share > 20:
        risk = f"CONCENTRATION WATCH: {largest_provider} at {largest_share:.0f}% (threshold: 15%)"
    else:
        risk = "LOW RISK: Good distribution across independent providers"

    # Contextual recommendation
    if hyperscale_pct > 10:
        recommendation = "Priority: Migrate relay nodes off hyperscale cloud (AWS/Google/Azure)"
    elif largest_share > 25:
        recommendation = f"Consider diversifying away from {largest_provider} to reduce concentration"
    else:
        recommendation = "Network has achieved 'Post-AWS' status - focus on maintaining provider diversity"

    return {
        "health": health,
        "color": color,
        "message": message,
        "tier_analysis": tier_analysis,
        "tier_breakdown": ", ".join([
            f"{hyperscale_pct:.0f}% hyperscale" if hyperscale_pct > 0 else "",
            f"{corporate_pct:.0f}% corporate" if corporate_pct > 0 else "",
            f"{sovereign_pct:.0f}% sovereign" if sovereign_pct > 0 else ""
        ]).strip(", "),
        "risk_assessment": risk,
        "recommendation": recommendation,
        "largest_provider": f"{largest_provider} ({largest_share:.1f}%)" if largest_provider else "N/A",
        # Legacy fields for backward compatibility
        "sovereign_status": (
            f"Relays are {corporate_pct:.0f}% on independent data centers (expected for relay nodes)"
            if sovereign_pct < 5 else
            f"{sovereign_pct:.0f}% on residential infrastructure (rare for relays)"
        )
    }

"""
Edit-Check Authoring Assistant

AI-assisted generation of YAML edit check rules with regulatory citations.
Automatically generates range checks, allowed values, and differential checks
based on clinical guidelines from FDA, ICH, and CDISC sources.
"""

import re
import yaml
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from linkup_utils import get_linkup_client, search_regulatory_sources

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class EditCheckGenerationRequest(BaseModel):
    """Request model for edit check rule generation"""
    variable: str = Field(..., description="Variable name (e.g., 'systolic_bp')")
    indication: str = Field(default="general", description="Clinical indication")
    severity: str = Field(default="Major", description="Rule severity: Minor, Major, Critical")
    check_type: str = Field(default="range", description="Check type: range, allowed_values, differential")


class EditCheckGenerationResponse(BaseModel):
    """Response model for generated edit check rule"""
    rule_yaml: str
    rule_dict: Dict[str, Any]
    confidence: str  # low, medium, high
    requires_review: bool
    citations: List[Dict[str, Any]]
    generated_at: str


# ============================================================================
# Range Pattern Definitions
# ============================================================================

RANGE_PATTERNS = {
    "systolic_bp": {
        "regex": r"systolic.*?(\d{2,3})\s*[-to–]\s*(\d{2,3})\s*mmHg",
        "unit": "mmHg",
        "typical_range": (95, 200),
        "description": "Systolic Blood Pressure"
    },
    "diastolic_bp": {
        "regex": r"diastolic.*?(\d{2,3})\s*[-to–]\s*(\d{2,3})\s*mmHg",
        "unit": "mmHg",
        "typical_range": (55, 130),
        "description": "Diastolic Blood Pressure"
    },
    "heart_rate": {
        "regex": r"heart\s+rate.*?(\d{2,3})\s*[-to–]\s*(\d{2,3})\s*bpm",
        "unit": "bpm",
        "typical_range": (50, 120),
        "description": "Heart Rate"
    },
    "temperature": {
        "regex": r"temperature.*?(3[5-9]\.\d|40\.0)\s*[-to–]\s*(3[5-9]\.\d|40\.0)\s*[°]?C",
        "unit": "°C",
        "typical_range": (35.0, 40.0),
        "description": "Body Temperature"
    },
    "respiratory_rate": {
        "regex": r"respiratory\s+rate.*?(\d{1,2})\s*[-to–]\s*(\d{1,2})\s*(?:breaths?/?min|bpm)",
        "unit": "breaths/min",
        "typical_range": (12, 20),
        "description": "Respiratory Rate"
    },
    "oxygen_saturation": {
        "regex": r"oxygen\s+saturation.*?(\d{2,3})\s*[-to–]\s*(\d{2,3})\s*%",
        "unit": "%",
        "typical_range": (90, 100),
        "description": "Oxygen Saturation"
    },
    "weight": {
        "regex": r"weight.*?(\d{2,3})\s*[-to–]\s*(\d{2,3})\s*kg",
        "unit": "kg",
        "typical_range": (30, 200),
        "description": "Body Weight"
    },
    "height": {
        "regex": r"height.*?(\d{2,3})\s*[-to–]\s*(\d{2,3})\s*cm",
        "unit": "cm",
        "typical_range": (100, 220),
        "description": "Height"
    },
    "bmi": {
        "regex": r"BMI.*?(\d{1,2})\s*[-to–]\s*(\d{1,2})",
        "unit": "",
        "typical_range": (15, 50),
        "description": "Body Mass Index"
    }
}


# ============================================================================
# Core Generation Functions
# ============================================================================

async def generate_edit_check_rule(request: EditCheckGenerationRequest) -> EditCheckGenerationResponse:
    """
    Generate an edit check rule with AI-assisted range detection

    Args:
        request: Edit check generation request

    Returns:
        Generated rule with YAML, confidence score, and citations
    """
    try:
        logger.info(f"Generating edit check rule for {request.variable}")

        # Step 1: Search for clinical guidance
        ranges_and_citations = await extract_clinical_ranges(
            request.variable,
            request.indication
        )

        # Step 2: Generate rule structure
        rule = create_rule_structure(
            variable=request.variable,
            ranges=ranges_and_citations,
            severity=request.severity,
            check_type=request.check_type
        )

        # Step 3: Convert to YAML
        rule_yaml = yaml.dump({"rules": [rule]}, default_flow_style=False, sort_keys=False)

        # Step 4: Determine confidence
        confidence = ranges_and_citations.get("confidence", "medium")

        response = EditCheckGenerationResponse(
            rule_yaml=rule_yaml,
            rule_dict=rule,
            confidence=confidence,
            requires_review=True,  # Always require human review
            citations=ranges_and_citations.get("citations", []),
            generated_at=datetime.utcnow().isoformat()
        )

        logger.info(f"Rule generated successfully with confidence: {confidence}")
        return response

    except Exception as e:
        logger.error(f"Error generating edit check rule: {str(e)}")
        raise


async def extract_clinical_ranges(
    variable: str,
    indication: str = "general"
) -> Dict[str, Any]:
    """
    Extract clinical ranges from regulatory sources using Linkup

    Args:
        variable: Variable name
        indication: Clinical indication

    Returns:
        Dictionary with min, max, citations, and confidence
    """
    ranges = {
        "min": None,
        "max": None,
        "citations": [],
        "confidence": "low",
        "unit": ""
    }

    # Get pattern info for this variable
    pattern_info = RANGE_PATTERNS.get(variable.lower())
    if not pattern_info:
        logger.warning(f"No pattern defined for variable: {variable}")
        return ranges

    # Build search query
    var_description = pattern_info["description"]
    query = f"{var_description} normal range clinical guidelines {indication} FDA ICH"

    logger.info(f"Searching for ranges: {query}")

    # Search authoritative sources
    search_results = await search_regulatory_sources(
        query=query,
        max_results=10
    )

    # Extract ranges from search results
    regex_pattern = re.compile(pattern_info["regex"], re.IGNORECASE)

    for source in search_results:
        snippet = source.get("snippet", "")
        domain = source.get("domain", "")

        match = regex_pattern.search(snippet)
        if match:
            try:
                min_val = float(match.group(1))
                max_val = float(match.group(2))

                ranges["min"] = min_val
                ranges["max"] = max_val
                ranges["unit"] = pattern_info["unit"]
                ranges["citations"].append({
                    "title": source["title"],
                    "url": source["url"],
                    "snippet": match.group(0),  # The matched range text
                    "domain": domain
                })

                # Determine confidence based on source
                if "fda.gov" in domain:
                    ranges["confidence"] = "high"
                    break  # FDA is highest priority
                elif "ich.org" in domain or "ema.europa.eu" in domain:
                    ranges["confidence"] = "high"
                elif "cdisc.org" in domain:
                    ranges["confidence"] = "medium"

            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse range values: {e}")
                continue

    # If no ranges found from search, use typical defaults
    if ranges["min"] is None:
        logger.info(f"Using typical range for {variable}")
        ranges["min"], ranges["max"] = pattern_info["typical_range"]
        ranges["unit"] = pattern_info["unit"]
        ranges["confidence"] = "low"
        ranges["citations"].append({
            "title": "Default Clinical Range (No regulatory source found)",
            "url": "",
            "snippet": f"Using typical clinical range: {ranges['min']}-{ranges['max']} {ranges['unit']}",
            "domain": "internal"
        })

    # Add all search results as additional context
    for source in search_results[:5]:  # Top 5 results
        if source not in ranges["citations"]:
            ranges["citations"].append(source)

    return ranges


def create_rule_structure(
    variable: str,
    ranges: Dict[str, Any],
    severity: str,
    check_type: str
) -> Dict[str, Any]:
    """
    Create YAML rule structure from extracted ranges

    Args:
        variable: Variable name
        ranges: Extracted range information
        severity: Rule severity
        check_type: Type of check

    Returns:
        Rule dictionary ready for YAML export
    """
    rule_id = f"AUTO_{variable.upper()}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    pattern_info = RANGE_PATTERNS.get(variable.lower(), {})
    description = pattern_info.get("description", variable)

    rule = {
        "id": rule_id,
        "name": f"{description} Clinical Range Check",
        "type": check_type,
        "field": variable,
        "severity": severity,
        "auto_generated": True,
        "generated_at": datetime.utcnow().isoformat(),
        "reviewed": False
    }

    if check_type == "range":
        rule["min"] = ranges["min"]
        rule["max"] = ranges["max"]
        rule["message"] = (
            f"{description} out of clinical range "
            f"[{ranges['min']}, {ranges['max']}] {ranges.get('unit', '')}"
        ).strip()

    # Add evidence/citations
    rule["evidence"] = [
        {
            "source": cite.get("title", "Unknown"),
            "url": cite.get("url", ""),
            "excerpt": cite.get("snippet", "")[:200]  # Limit excerpt length
        }
        for cite in ranges.get("citations", [])[:3]  # Top 3 citations
    ]

    # Add metadata
    rule["metadata"] = {
        "confidence": ranges.get("confidence", "low"),
        "unit": ranges.get("unit", ""),
        "citation_count": len(ranges.get("citations", [])),
        "requires_review": True
    }

    return rule


# ============================================================================
# Batch Generation Functions
# ============================================================================

async def generate_rules_for_study(
    study_variables: List[str],
    indication: str = "general",
    severity: str = "Major"
) -> List[Dict[str, Any]]:
    """
    Generate edit check rules for all variables in a study

    Args:
        study_variables: List of variable names
        indication: Clinical indication
        severity: Default severity

    Returns:
        List of generated rules
    """
    rules = []

    for variable in study_variables:
        try:
            request = EditCheckGenerationRequest(
                variable=variable,
                indication=indication,
                severity=severity
            )

            response = await generate_edit_check_rule(request)
            rules.append(response.rule_dict)

        except Exception as e:
            logger.error(f"Error generating rule for {variable}: {e}")
            continue

    return rules


async def export_rules_to_yaml_file(
    rules: List[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Export rules to YAML file

    Args:
        rules: List of rule dictionaries
        output_path: Path to output YAML file

    Returns:
        Path to created file
    """
    yaml_content = yaml.dump(
        {"rules": rules},
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True
    )

    with open(output_path, 'w') as f:
        # Add header comment
        f.write("# Auto-Generated Edit Check Rules\n")
        f.write(f"# Generated: {datetime.utcnow().isoformat()}\n")
        f.write("# REQUIRES REVIEW: These rules were automatically generated\n")
        f.write("# and must be reviewed by qualified personnel before use.\n\n")
        f.write(yaml_content)

    logger.info(f"Exported {len(rules)} rules to {output_path}")
    return output_path


# ============================================================================
# Validation Functions
# ============================================================================

def validate_rule_structure(rule: Dict[str, Any]) -> List[str]:
    """
    Validate that a rule has required fields and valid values

    Args:
        rule: Rule dictionary to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Required fields
    required_fields = ["id", "name", "type", "field", "severity"]
    for field in required_fields:
        if field not in rule:
            errors.append(f"Missing required field: {field}")

    # Valid severity values
    valid_severities = ["Minor", "Major", "Critical"]
    if rule.get("severity") not in valid_severities:
        errors.append(f"Invalid severity: {rule.get('severity')}")

    # Type-specific validation
    if rule.get("type") == "range":
        if "min" not in rule or "max" not in rule:
            errors.append("Range check requires 'min' and 'max' fields")
        elif rule.get("min") >= rule.get("max"):
            errors.append("'min' must be less than 'max'")

    return errors


def merge_rules_with_existing(
    new_rules: List[Dict[str, Any]],
    existing_rules: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge new auto-generated rules with existing manually-created rules

    Args:
        new_rules: Newly generated rules
        existing_rules: Existing manual rules

    Returns:
        Merged rule list (existing rules take precedence)
    """
    # Create lookup by field
    existing_by_field = {rule["field"]: rule for rule in existing_rules}

    merged = existing_rules.copy()

    for new_rule in new_rules:
        field = new_rule["field"]
        if field not in existing_by_field:
            # Add new rule
            merged.append(new_rule)
        else:
            # Rule already exists - optionally update metadata
            logger.info(f"Rule for {field} already exists - skipping")

    return merged

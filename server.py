#!/usr/bin/env python3
"""
NIH Reporter API MCP Server

This MCP server provides access to the NIH Reporter API for searching and retrieving
information about NIH-funded research projects.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from collections import defaultdict
import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nih-reporter-mcp")

# NIH Reporter API configuration
NIH_API_BASE_URL = "https://api.reporter.nih.gov/v2"
NIH_API_TIMEOUT = 30

app = Server("nih-reporter-server")


def make_nih_api_request(endpoint: str, payload: dict) -> dict:
    """Make a request to the NIH Reporter API."""
    url = f"{NIH_API_BASE_URL}/{endpoint}"

    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=NIH_API_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise Exception(f"NIH Reporter API error: {str(e)}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for the NIH Reporter API."""
    return [
        Tool(
            name="search_projects",
            description="""Search for NIH-funded research projects using various criteria.

            You can search by:
            - Fiscal years
            - Agency/Institute (IC codes like NCI, NIDA, etc.)
            - Activity codes (R01, P01, etc.)
            - Organization names
            - Principal investigator names
            - Project numbers
            - Award amount ranges
            - Date ranges
            - Keywords in title/abstract

            Returns detailed project information including funding, investigators, and descriptions.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "fiscal_years": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Fiscal years to search (e.g., [2024, 2025])"
                    },
                    "agencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "NIH Institute/Center codes (e.g., ['NCI', 'NIDA'])"
                    },
                    "activity_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Activity codes (e.g., ['R01', 'P01'])"
                    },
                    "org_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Organization names to search"
                    },
                    "pi_names": {
                        "type": "string",
                        "description": "Principal investigator name"
                    },
                    "project_nums": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific project numbers"
                    },
                    "keywords": {
                        "type": "string",
                        "description": "Keywords to search in title, abstract, and terms"
                    },
                    "min_amount": {
                        "type": "integer",
                        "description": "Minimum award amount"
                    },
                    "max_amount": {
                        "type": "integer",
                        "description": "Maximum award amount"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date for award notice date (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date for award notice date (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 25, max: 500)",
                        "default": 25
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Offset for pagination (default: 0)",
                        "default": 0
                    }
                }
            }
        ),
        Tool(
            name="get_project_details",
            description="""Get detailed information about a specific NIH project by its project number or application ID.

            Returns comprehensive project data including:
            - Full project information
            - Principal investigators
            - Organization details
            - Funding amounts and dates
            - Project abstract and public health relevance
            - Study section information""",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_num": {
                        "type": "string",
                        "description": "Full project number (e.g., '5R01CA123456-05'). Either project_num or appl_id must be provided, but not both."
                    },
                    "appl_id": {
                        "type": "integer",
                        "description": "Application ID. Either project_num or appl_id must be provided, but not both."
                    }
                }
            }
        ),
        Tool(
            name="search_recent_awards",
            description="""Search for recently awarded NIH projects within a specified number of days.

            Useful for finding the latest funded projects across all NIH institutes.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 7)",
                        "default": 7
                    },
                    "agencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: Filter by specific NIH institutes"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="search_by_investigator",
            description="""Search for all projects by a specific principal investigator.

            Returns all NIH-funded projects where the person is listed as a PI.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "last_name": {
                        "type": "string",
                        "description": "Last name of the investigator"
                    },
                    "first_name": {
                        "type": "string",
                        "description": "First name of the investigator (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 25)",
                        "default": 25
                    }
                },
                "required": ["last_name"]
            }
        ),
        Tool(
            name="get_spending_categories",
            description="""Get available NIH spending categories for categorizing research projects.

            Returns a list of all spending category codes and names used by NIH.""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_projects_light",
            description="""Lightweight version of search_projects that returns minimal fields for efficient data retrieval.

            Use this when you need to process many results or only need basic project information.
            Returns only: ProjectNum, ProjectTitle, AwardAmount, AwardNoticeDate, Organization, PrincipalInvestigators.

            Same search criteria as search_projects.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "fiscal_years": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Fiscal years to search (e.g., [2024, 2025])"
                    },
                    "agencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "NIH Institute/Center codes (e.g., ['NCI', 'NIDA'])"
                    },
                    "activity_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Activity codes (e.g., ['R01', 'P01'])"
                    },
                    "org_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Organization names to search"
                    },
                    "pi_names": {
                        "type": "string",
                        "description": "Principal investigator name"
                    },
                    "project_nums": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific project numbers"
                    },
                    "keywords": {
                        "type": "string",
                        "description": "Keywords to search in title, abstract, and terms"
                    },
                    "min_amount": {
                        "type": "integer",
                        "description": "Minimum award amount"
                    },
                    "max_amount": {
                        "type": "integer",
                        "description": "Maximum award amount"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date for award notice date (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date for award notice date (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 25, max: 500)",
                        "default": 25
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Offset for pagination (default: 0)",
                        "default": 0
                    }
                }
            }
        ),
        Tool(
            name="analyze_research_trends",
            description="""Analyze trends in NIH-funded research by fetching and summarizing data server-side.

            This tool is designed for large-scale analysis that would exceed context limits if done client-side.
            It fetches projects matching your criteria, then aggregates and summarizes the data before returning.

            Returns:
            - Total projects and funding amounts
            - Distribution by institute/agency
            - Distribution by activity code (grant type)
            - Top organizations by funding
            - Funding trends over time
            - Common research themes (from project titles)

            Use this when you need to understand patterns across many projects without loading full details.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "fiscal_years": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Fiscal years to analyze (e.g., [2024, 2025])"
                    },
                    "agencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "NIH Institute/Center codes (e.g., ['NCI', 'NIDA'])"
                    },
                    "activity_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Activity codes (e.g., ['R01', 'P01'])"
                    },
                    "keywords": {
                        "type": "string",
                        "description": "Keywords to search in title, abstract, and terms"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date for award notice date (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date for award notice date (YYYY-MM-DD)"
                    },
                    "max_projects": {
                        "type": "integer",
                        "description": "Maximum number of projects to analyze (default: 500, max: 2000)",
                        "default": 500
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls for NIH Reporter API operations."""

    try:
        if name == "search_projects":
            result = await search_projects(arguments)
        elif name == "get_project_details":
            result = await get_project_details(arguments)
        elif name == "search_recent_awards":
            result = await search_recent_awards(arguments)
        elif name == "search_by_investigator":
            result = await search_by_investigator(arguments)
        elif name == "get_spending_categories":
            result = await get_spending_categories(arguments)
        elif name == "search_projects_light":
            result = await search_projects_light(arguments)
        elif name == "analyze_research_trends":
            result = await analyze_research_trends(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def search_projects(args: dict) -> dict:
    """Search for NIH projects based on various criteria."""
    criteria = {}

    # Build criteria from arguments
    if args.get("fiscal_years"):
        criteria["fiscal_years"] = args["fiscal_years"]

    if args.get("agencies"):
        criteria["agencies"] = args["agencies"]

    if args.get("activity_codes"):
        criteria["activity_codes"] = args["activity_codes"]

    if args.get("org_names"):
        criteria["org_names"] = args["org_names"]

    if args.get("pi_names"):
        criteria["pi_names"] = [{"any_name": args["pi_names"]}]

    if args.get("project_nums"):
        criteria["project_nums"] = args["project_nums"]

    if args.get("keywords"):
        criteria["advanced_text_search"] = {
            "operator": "and",
            "search_field": "projecttitle,abstracttext,terms",
            "search_text": args["keywords"]
        }

    if args.get("min_amount") or args.get("max_amount"):
        criteria["award_amount_range"] = {
            "min_amount": args.get("min_amount", 0),
            "max_amount": args.get("max_amount", 100000000)
        }

    if args.get("date_from") or args.get("date_to"):
        criteria["award_notice_date"] = {}
        if args.get("date_from"):
            criteria["award_notice_date"]["from_date"] = args["date_from"]
        if args.get("date_to"):
            criteria["award_notice_date"]["to_date"] = args["date_to"]

    payload = {
        "criteria": criteria,
        "include_fields": [
            "ApplId", "ProjectNum", "FiscalYear", "Organization",
            "PrincipalInvestigators", "ProjectTitle", "AwardAmount",
            "AwardNoticeDate", "ProjectStartDate", "ProjectEndDate",
            "AbstractText", "AgencyIcAdmin"
        ],
        "offset": args.get("offset", 0),
        "limit": min(args.get("limit", 25), 500),
        "sort_field": "award_notice_date",
        "sort_order": "desc"
    }

    return make_nih_api_request("projects/search", payload)


async def get_project_details(args: dict) -> dict:
    """Get detailed information about a specific project."""
    # Validate that exactly one parameter is provided
    has_project_num = args.get("project_num") is not None
    has_appl_id = args.get("appl_id") is not None

    if has_project_num and has_appl_id:
        raise ValueError("Cannot provide both project_num and appl_id. Please provide only one.")
    elif not has_project_num and not has_appl_id:
        raise ValueError("Either project_num or appl_id must be provided")

    criteria = {}
    if has_project_num:
        criteria["project_nums"] = [args["project_num"]]
    else:
        criteria["appl_ids"] = [args["appl_id"]]

    payload = {
        "criteria": criteria,
        "include_fields": [
            "ApplId", "ProjectNum", "FiscalYear", "Organization",
            "OrganizationType", "PrincipalInvestigators", "ProgramOfficers",
            "ProjectTitle", "AbstractText", "PhrText", "AwardAmount",
            "AwardNoticeDate", "ProjectStartDate", "ProjectEndDate",
            "AgencyIcAdmin", "AgencyIcFundings", "ActivityCode",
            "FullStudySection", "DirectCostAmt", "IndirectCostAmt",
            "PrefTerms", "SpendingCategoriesDesc"
        ],
        "offset": 0,
        "limit": 1
    }

    return make_nih_api_request("projects/search", payload)


async def search_recent_awards(args: dict) -> dict:
    """Search for recently awarded projects."""
    days = args.get("days", 7)
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)

    criteria = {
        "award_notice_date": {
            "from_date": from_date.strftime("%Y-%m-%d"),
            "to_date": to_date.strftime("%Y-%m-%d")
        }
    }

    if args.get("agencies"):
        criteria["agencies"] = args["agencies"]

    payload = {
        "criteria": criteria,
        "include_fields": [
            "ApplId", "ProjectNum", "FiscalYear", "Organization",
            "PrincipalInvestigators", "ProjectTitle", "AwardAmount",
            "AwardNoticeDate", "AgencyIcAdmin"
        ],
        "offset": 0,
        "limit": args.get("limit", 50),
        "sort_field": "award_notice_date",
        "sort_order": "desc"
    }

    return make_nih_api_request("projects/search", payload)


async def search_by_investigator(args: dict) -> dict:
    """Search for projects by principal investigator name."""
    pi_search = {"last_name": args["last_name"]}

    if args.get("first_name"):
        pi_search["first_name"] = args["first_name"]

    payload = {
        "criteria": {
            "pi_names": [pi_search]
        },
        "include_fields": [
            "ApplId", "ProjectNum", "FiscalYear", "Organization",
            "PrincipalInvestigators", "ProjectTitle", "AwardAmount",
            "ProjectStartDate", "ProjectEndDate", "AgencyIcAdmin"
        ],
        "offset": 0,
        "limit": args.get("limit", 25),
        "sort_field": "project_start_date",
        "sort_order": "desc"
    }

    return make_nih_api_request("projects/search", payload)


async def get_spending_categories(args: dict) -> dict:
    """Get available spending categories (from documentation)."""
    # This is a simplified version - you could make this more comprehensive
    # by parsing the full list from the PDF documentation
    return {
        "message": "Spending categories are used to categorize NIH research projects",
        "note": "Use spending_categories parameter in search_projects with category IDs",
        "examples": [
            {"id": 31, "name": "Aging"},
            {"id": 40, "name": "Alzheimer's Disease"},
            {"id": 132, "name": "Cancer"},
            {"id": 224, "name": "Diabetes"},
            {"id": 284, "name": "HIV/AIDS"}
        ],
        "documentation": "See Data Elements PDF for complete list of ~300 categories"
    }


async def search_projects_light(args: dict) -> dict:
    """Lightweight search for NIH projects with minimal fields."""
    criteria = {}

    # Build criteria from arguments (same as search_projects)
    if args.get("fiscal_years"):
        criteria["fiscal_years"] = args["fiscal_years"]

    if args.get("agencies"):
        criteria["agencies"] = args["agencies"]

    if args.get("activity_codes"):
        criteria["activity_codes"] = args["activity_codes"]

    if args.get("org_names"):
        criteria["org_names"] = args["org_names"]

    if args.get("pi_names"):
        criteria["pi_names"] = [{"any_name": args["pi_names"]}]

    if args.get("project_nums"):
        criteria["project_nums"] = args["project_nums"]

    if args.get("keywords"):
        criteria["advanced_text_search"] = {
            "operator": "and",
            "search_field": "projecttitle,abstracttext,terms",
            "search_text": args["keywords"]
        }

    if args.get("min_amount") or args.get("max_amount"):
        criteria["award_amount_range"] = {
            "min_amount": args.get("min_amount", 0),
            "max_amount": args.get("max_amount", 100000000)
        }

    if args.get("date_from") or args.get("date_to"):
        criteria["award_notice_date"] = {}
        if args.get("date_from"):
            criteria["award_notice_date"]["from_date"] = args["date_from"]
        if args.get("date_to"):
            criteria["award_notice_date"]["to_date"] = args["date_to"]

    payload = {
        "criteria": criteria,
        "include_fields": [
            "ProjectNum", "ProjectTitle", "AwardAmount",
            "AwardNoticeDate", "Organization", "PrincipalInvestigators"
        ],
        "offset": args.get("offset", 0),
        "limit": min(args.get("limit", 25), 500),
        "sort_field": "award_notice_date",
        "sort_order": "desc"
    }

    return make_nih_api_request("projects/search", payload)


async def analyze_research_trends(args: dict) -> dict:
    """Analyze trends in NIH research by aggregating data server-side."""
    criteria = {}

    # Build criteria
    if args.get("fiscal_years"):
        criteria["fiscal_years"] = args["fiscal_years"]

    if args.get("agencies"):
        criteria["agencies"] = args["agencies"]

    if args.get("activity_codes"):
        criteria["activity_codes"] = args["activity_codes"]

    if args.get("keywords"):
        criteria["advanced_text_search"] = {
            "operator": "and",
            "search_field": "projecttitle,abstracttext,terms",
            "search_text": args["keywords"]
        }

    if args.get("date_from") or args.get("date_to"):
        criteria["award_notice_date"] = {}
        if args.get("date_from"):
            criteria["award_notice_date"]["from_date"] = args["date_from"]
        if args.get("date_to"):
            criteria["award_notice_date"]["to_date"] = args["date_to"]

    # Fetch data in batches
    max_projects = min(args.get("max_projects", 500), 2000)
    batch_size = 500
    all_projects = []

    for offset in range(0, max_projects, batch_size):
        payload = {
            "criteria": criteria,
            "include_fields": [
                "ProjectNum", "ProjectTitle", "AwardAmount", "AwardNoticeDate",
                "Organization", "AgencyIcAdmin", "ActivityCode", "FiscalYear",
                "PrefTerms"
            ],
            "offset": offset,
            "limit": min(batch_size, max_projects - offset),
            "sort_field": "award_notice_date",
            "sort_order": "desc"
        }

        response = make_nih_api_request("projects/search", payload)
        projects = response.get("results", [])

        if not projects:
            break

        all_projects.extend(projects)

        # Stop if we got fewer results than requested
        if len(projects) < batch_size:
            break

    # Aggregate data
    total_projects = len(all_projects)
    total_funding = sum(p.get("award_amount") or 0 for p in all_projects)

    # By agency
    by_agency = defaultdict(lambda: {"count": 0, "funding": 0})
    for p in all_projects:
        agency = p.get("agency_ic_admin", {}).get("code", "Unknown")
        by_agency[agency]["count"] += 1
        by_agency[agency]["funding"] += (p.get("award_amount") or 0)

    # By activity code
    by_activity = defaultdict(lambda: {"count": 0, "funding": 0})
    for p in all_projects:
        activity = p.get("activity_code", "Unknown")
        by_activity[activity]["count"] += 1
        by_activity[activity]["funding"] += (p.get("award_amount") or 0)

    # By organization
    by_org = defaultdict(lambda: {"count": 0, "funding": 0})
    for p in all_projects:
        org = p.get("organization", {}).get("org_name", "Unknown")
        by_org[org]["count"] += 1
        by_org[org]["funding"] += (p.get("award_amount") or 0)

    # Top 10 organizations by funding
    top_orgs = sorted(by_org.items(), key=lambda x: x[1]["funding"], reverse=True)[:10]

    # By fiscal year
    by_year = defaultdict(lambda: {"count": 0, "funding": 0})
    for p in all_projects:
        year = p.get("fiscal_year", "Unknown")
        by_year[year]["count"] += 1
        by_year[year]["funding"] += (p.get("award_amount") or 0)

    # Extract common themes from titles (simple word frequency)
    title_words = defaultdict(int)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                  'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                  'could', 'should', 'may', 'might', 'can'}

    for p in all_projects:
        title = p.get("project_title", "").lower()
        words = title.split()
        for word in words:
            # Clean word
            word = ''.join(c for c in word if c.isalnum())
            if len(word) > 3 and word not in stop_words:
                title_words[word] += 1

    common_themes = sorted(title_words.items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        "summary": {
            "total_projects": total_projects,
            "total_funding": total_funding,
            "average_award": total_funding / total_projects if total_projects > 0 else 0,
            "date_range": {
                "from": args.get("date_from", "Not specified"),
                "to": args.get("date_to", "Not specified")
            }
        },
        "by_agency": dict(sorted(by_agency.items(), key=lambda x: x[1]["funding"], reverse=True)),
        "by_activity_code": dict(sorted(by_activity.items(), key=lambda x: x[1]["funding"], reverse=True)),
        "top_organizations": [
            {
                "name": org,
                "projects": data["count"],
                "total_funding": data["funding"]
            }
            for org, data in top_orgs
        ],
        "by_fiscal_year": dict(sorted(by_year.items())),
        "common_themes": [
            {"word": word, "frequency": count}
            for word, count in common_themes
        ],
        "note": f"Analysis based on {total_projects} projects (requested max: {max_projects})"
    }


async def main():
    """Run the MCP server."""
    logger.info("Starting NIH Reporter MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

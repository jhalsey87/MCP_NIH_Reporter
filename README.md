# NIH Reporter MCP Server

A Model Context Protocol (MCP) server that provides programmatic access to the NIH Reporter API for searching and retrieving information about NIH-funded research projects.

## Overview

This MCP server allows AI assistants and other MCP clients to search for and retrieve detailed information about NIH-funded research grants, including:

- Project details and funding information
- Principal investigator information
- Organization details
- Project abstracts and public health relevance
- Award amounts and dates
- Study sections and review information

## Features

### Available Tools

1. **search_projects** - Search for NIH projects using multiple criteria:
   - Fiscal years
   - NIH Institutes/Centers (IC codes)
   - Activity codes (R01, P01, etc.)
   - Organization names
   - Principal investigator names
   - Project numbers
   - Award amount ranges
   - Date ranges
   - Keywords in title/abstract

2. **get_project_details** - Get comprehensive details about a specific project by project number or application ID

3. **search_recent_awards** - Find recently awarded projects within a specified number of days

4. **search_by_investigator** - Search for all projects by a specific principal investigator

5. **get_spending_categories** - Get information about NIH spending categories

## Prerequisites

- Docker and Docker Compose installed
- Basic understanding of MCP (Model Context Protocol)

## Quick Start

### 1. Build the Docker Image

```bash
docker-compose build
```

### 2. Run the Server

```bash
docker-compose up
```

The server will start and listen for MCP requests via stdin/stdout.

### 3. Alternative: Build and Run with Docker Only

```bash
# Build the image
docker build -t nih-reporter-mcp .

# Run the container
docker run -i nih-reporter-mcp
```

## Configuration for Claude Desktop

To use this MCP server with Claude Desktop, add it to your Claude configuration file:

**On macOS/Linux:** `~/Library/Application Support/Claude/claude_desktop_config.json`

**On Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "nih-reporter": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "nih-reporter-mcp"]
    }
  }
}
```

After adding this configuration, restart Claude Desktop.

## Usage Examples

Once connected to an MCP client (like Claude Desktop), you can use natural language to interact with the NIH Reporter API:

### Example 1: Search for Recent Cancer Research

```
"Find recent NIH cancer research projects from the National Cancer Institute awarded in 2025"
```

This will use the `search_projects` tool with:
- agencies: ["NCI"]
- fiscal_years: [2025]

### Example 2: Find Projects by Investigator

```
"Show me all NIH projects where John Smith is the principal investigator"
```

This will use the `search_by_investigator` tool.

### Example 3: Get Project Details

```
"Get detailed information about project R01CA123456"
```

This will use the `get_project_details` tool.

### Example 4: Search Recent Awards

```
"What are the newest NIH awards from the last 7 days?"
```

This will use the `search_recent_awards` tool.

## API Reference

### NIH Institute/Center Codes

Common IC codes you can use in searches:

- **NCI** - National Cancer Institute
- **NIDA** - National Institute on Drug Abuse
- **NHLBI** - National Heart, Lung, and Blood Institute
- **NIAID** - National Institute of Allergy and Infectious Diseases
- **NIMH** - National Institute of Mental Health
- **NIA** - National Institute on Aging
- **NICHD** - National Institute of Child Health and Human Development
- **NIDDK** - National Institute of Diabetes and Digestive and Kidney Diseases

See the documentation PDFs for the complete list.

### Common Activity Codes

- **R01** - Research Project Grant
- **R21** - Exploratory/Developmental Research Grant
- **R03** - Small Research Grant
- **P01** - Research Program Project Grant
- **U01** - Research Project Cooperative Agreement
- **K01-K99** - Career Development Awards
- **T32** - Institutional Training Grant
- **F31-F33** - Individual Predoctoral/Postdoctoral Fellowship

## Development

### Project Structure

```
.
├── server.py           # Main MCP server implementation
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker container definition
├── docker-compose.yml # Docker Compose configuration
├── README.md          # This file
└── [PDF documentation files]
```

### Local Development (Without Docker)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python server.py
```

### Modifying the Server

The server code is in `server.py`. Key sections:

- **Tool definitions**: `list_tools()` function
- **Tool handlers**: Individual async functions for each tool
- **API integration**: `make_nih_api_request()` function

After making changes, rebuild the Docker image:
```bash
docker-compose build
```

## Troubleshooting

### Server Not Responding

1. Check if the container is running:
```bash
docker ps
```

2. View logs:
```bash
docker-compose logs -f
```

### API Errors

The NIH Reporter API may occasionally be slow or unavailable. The server includes a 30-second timeout for API requests.

### Connection Issues

Ensure that:
- Docker is running
- The container has internet access to reach api.reporter.nih.gov
- No firewall is blocking outbound HTTPS connections

## Data Sources

This server uses the NIH Reporter API v2:
- API Base URL: https://api.reporter.nih.gov/v2
- Documentation: Included PDF files in this directory

## Limitations

- Maximum 500 results per query (API limitation)
- 30-second timeout per API request
- Rate limiting may apply (enforced by NIH Reporter API)

## License

This MCP server implementation is provided as-is for use with the NIH Reporter public API.

## Contributing

Contributions are welcome! Please ensure:
- Code follows Python best practices
- All tools are properly documented
- Docker container builds successfully
- README is updated for new features

## Support

For issues related to:
- **This MCP server**: Check logs and troubleshooting section
- **NIH Reporter API**: See official NIH Reporter documentation
- **MCP Protocol**: See Model Context Protocol documentation

## Version

Current Version: 1.0.0

## Credits

Built using:
- MCP SDK for Python
- NIH Reporter API v2
- Docker for containerization

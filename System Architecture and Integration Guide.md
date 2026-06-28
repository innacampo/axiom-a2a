# System Architecture and Integration Guide

## 1. System Architecture Diagram

*   **Visual layout of agent roles:** [Insert diagram or description of agent roles here]
*   **Orchestration flow between agents:** [Describe how agents communicate, delegate, and sequence tasks]
*   **Identification of host vs. client agents:** [Specify which agents act as hosts/orchestrators and which operate as specialized clients/sub-agents]

## 2. MCP Server Configuration & Registry

*   **List of all active MCP servers:** [List active servers, e.g., FileSystem MCP, GitHub MCP, Database MCP]
*   **Exposed tools, resources, and prompts:** [Document what specific capabilities each MCP server provides to the agents]
*   **Connection strings and environment variables:** [List required configurations, e.g., `MCP_PORT`, `GITHUB_TOKEN`, connection URLs (keep secrets out of version control)]

## 3. State Management & Context Hand-offs

*   **Methods for maintaining session context:** [Describe where session state is held, e.g., local SQLite, in-memory DB, thread histories]
*   **Protocol for passing data between agents:** [e.g., structured JSON payloads, standardized Markdown summaries]
*   **Token optimization and context-window strategy:** [Explain techniques used to prevent token limits, e.g., summarization, vector search (RAG), progressive disclosure]

## 4. Security & Authentication Model

*   **API key and credential management:** [e.g., managed via `.env` files, secure secret vaults, or local keychain]
*   **Transport layer security definitions:** [e.g., enforce HTTPS/WSS for all remote MCP and API connections]
*   **Agent access control levels:** [Define permission boundaries and what specific tools/resources each agent persona is permitted to access]

## 5. Local Development & Testing Workflow

*   **Instructions for mock server setups:** [Steps to run local stubs or lightweight mock servers for safe testing]
*   **Steps to trace agent protocol logs:** [How to enable verbose debug logging and view tool call traces]
*   **Validation checks for new tools:** [Testing requirements and CI checks needed before merging new MCP tools or skills]

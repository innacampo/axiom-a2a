# System Architecture and Integration Guide

## 1. System Architecture Diagram

### Agent Roles & Layout
The architecture follows a three-layer composable model:
- **Orchestration Layer (User/Slash Commands):** The entry point that defines *when* an action occurs.
- **Persona Layer (`agents/`):** The *who*. Specialized roles (e.g., `code-reviewer`, `security-auditor`) with specific perspectives and output formats.
- **Skill Layer (`skills/`):** The *how*. Packaged workflows defined in `SKILL.md` that provide step-by-step instructions and executable scripts.

### Orchestration Flow
1. **Intent Mapping:** User request $\rightarrow$ mapped to a specific **Skill** (e.g., "new feature" $\rightarrow$ `spec-driven-development`).
2. **Skill Activation:** The agent reads `skills/<skill-name>/SKILL.md` and follows its defined workflow.
3. **Execution:** The agent runs associated bash scripts located in `skills/<skill-name>/scripts/`.
4. **Persona Integration:** For complex tasks (like `/ship`), a **parallel fan-out** occurs where multiple personas process the work and merge results into a final synthesis.

### Host vs. Client Agents
- **Host Agent:** The primary LLM instance (e.g., Claude Code) that manages the session and orchestrates the overall process.
- **Client/Sub-agents:** Specialized personas spawned from the `agents/` directory to perform targeted reviews or audits.

## 2. MCP Server Configuration & Registry

### Active MCP Servers
- **FileSystem MCP:** Provides capabilities for reading, writing, and editing local files.
- **GitHub MCP:** Facilitates repository management, PR creation, and issue tracking.
- **Bash/Shell MCP:** Allows execution of system commands for build, test, and linting.
- **WebFetch MCP:** Enables retrieval of external documentation and web content.

### Exposed Tools & Resources
- **File Operations:** `read`, `write`, `edit`, `glob`, `grep`.
- **Git/GitHub:** `gh` CLI integration for PRs and repo management.
- **System Execution:** `bash` for running scripts and toolchains.

### Connection & Environment
- **Protocol:** Standard MCP JSON-RPC.
- **Env Vars:** Managed via the host environment (e.g., `GITHUB_TOKEN` for GitHub MCP).

## 3. State Management & Context Hand-offs

### Session Context
- Context is maintained through the conversation history of the host agent.
- Skills are loaded on-demand to minimize context bloat, reading `SKILL.md` only when the specific workflow is triggered.

### Data Hand-off Protocol
- **Structured Handoffs:** Data is passed between personas and skills using standardized Markdown reports and JSON outputs from scripts.
- **Merge Step:** In fan-out patterns, a synthesis step aggregates individual persona reports into a single comprehensive review.

### Token Optimization Strategy
- **Progressive Disclosure:** Reference supporting files only when needed.
- **Context Limits:** `SKILL.md` files are kept under 500 lines.
- **Script-Centric Execution:** Complex logic is moved to bash scripts, as script execution doesn't consume LLM context tokens—only the output does.

## 4. Security & Authentication Model

### Credential Management
- Secrets and API keys are **never** committed to the repository.
- Credentials (e.g., `gh` auth tokens) are managed by the host environment's secure keyring or environment variables.

### Transport Security
- All external communications (MCP servers, GitHub API) are enforced over HTTPS/WSS.

### Access Control
- **Permission-based execution:** Tools like `bash` and `write` require specific environment permissions.
- **ReadOnly Context:** The agent emphasizes reading existing patterns before modifying code to prevent destructive changes.

## 5. Local Development & Testing Workflow

### Setup & Mocking
- Local skill development involves creating a directory in `skills/`, adding a `SKILL.md` and a `scripts/` folder.
- Mocking is achieved by creating local scripts that simulate MCP server responses.

### Protocol Tracing
- Tool calls and outputs are captured in the agent's session logs.
- Debugging is performed by examining the output of `bash` commands and `grep` results on local files.

### Validation Pipeline
- **Linting/Typechecking:** Every implementation must be verified by running the project's specific lint/typecheck commands (recorded in `AGENTS.md`).
- **Packaging:** Skills must be packaged as `{skill-name}.zip` for distribution.
- **Installation Test:** Skills are verified by copying them to `~/.claude/skills/` and invoking them via a prompt.

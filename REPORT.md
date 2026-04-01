# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

### Checkpoint 1: "What is the agentic loop?"

**Command:** `uv run nanobot agent --logs --session cli:task1a-loop -c ./config.json -m "What is the agentic loop?"`

**Agent Response:**

```
The agentic loop is the fundamental cycle that an AI agent follows to accomplish tasks autonomously. It typically    
consists of these core stages:                                                                                       

 1 Perceive — Gather information from the environment (user input, files, APIs, sensors, etc.)                       
 2 Reason/Plan — Analyze the information, determine goals, and decide on a course of action                          
 3 Act — Execute actions using available tools (write files, run commands, call APIs, send messages, etc.)           
 4 Observe — Receive feedback from the actions taken (outputs, errors, state changes)                                
 5 Reflect/Iterate — Evaluate results, adjust the plan if needed, and continue the loop until the goal is achieved   

This loop enables agents to:                                                                                         
 • Handle multi-step tasks autonomously                                                                              
 • Adapt to unexpected outcomes                                                                                      
 • Learn from feedback within a session                                                                              
 • Decompose complex problems into manageable steps                                                                  
```

### Checkpoint 2: "What labs are available in our LMS?"

**Command:** `uv run nanobot agent --logs --session cli:task1a-labs -c ./config.json -m "What labs are available in our LMS?"`

**Agent Response:**

```
Based on my exploration of the workspace, here are the **available labs** in your LMS:

## Lab Structure

The current lab is Lab 8 (se-toolkit-lab-8), which contains:

Required Tasks (5 tasks)                                                                                             
 • Task 1 - /lab/tasks/required/task-1.md                                                                            
 • Task 2 - /lab/tasks/required/task-2.md                                                                            
 • Task 3 - /lab/tasks/required/task-3.md                                                                            
 • Task 4 - /lab/tasks/required/task-4.md                                                                            
 • Task 5 - /lab/tasks/required/task-5.md                                                                            

Optional Tasks (1 task)                                                                                              
 • Task 1 - /lab/tasks/optional/task-1.md                                                                            

The LMS (Learning Management System) includes:                                                                       
 • Backend - FastAPI application with routers for items, interactions, and learners                                  
 • Database - PostgreSQL with seed data                                                                              
 • Frontend - React web client                                                                                       
 • Infrastructure - Docker Compose setup with backend, postgres, pgadmin, and caddy services                         
```

**Note:** The bare agent does NOT have access to the real LMS backend. It found this information by exploring local files in the repository using `list_dir`, `read_file`, and `exec` tools — not from the live LMS API.

## Task 1B — Agent with LMS tools

### MCP Tools Connected

The agent successfully connected to the LMS MCP server and registered 9 tools:

- `mcp_lms_lms_health` — Check backend health
- `mcp_lms_lms_labs` — Get available labs
- `mcp_lms_lms_learners` — Get learner information
- `mcp_lms_lms_pass_rates` — Get pass rates
- `mcp_lms_lms_timeline` — Get timeline data
- `mcp_lms_lms_groups` — Get group information
- `mcp_lms_lms_top_learners` — Get top learners
- `mcp_lms_lms_completion_rate` — Get completion rate
- `mcp_lms_lms_sync_pipeline` — Trigger sync pipeline

### Checkpoint: "What labs are available?"

**Command:** `NANOBOT_LMS_BACKEND_URL=http://localhost:42002 NANOBOT_LMS_API_KEY=lab8-secret-key-123 uv run nanobot agent --logs --session cli:task1b-labs -c ./config.json -m "What labs are available?"`

**Log excerpt showing MCP tools registered:**

```
2026-04-01 19:24:08.741 | DEBUG | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_health' from server 'lms'
2026-04-01 19:24:08.742 | DEBUG | nanobot.agent.tools.mcp:connect_mcp_servers:226 - MCP: registered tool 'mcp_lms_lms_labs' from server 'lms'
... (9 tools total)
2026-04-01 19:24:08.742 | INFO | nanobot.agent.tools.mcp:connect_mcp_servers:246 - MCP server 'lms': connected, 9 tools registered
```

**Agent Response:**

```
The LMS backend is healthy, but there are currently no labs available (item count: 0). This could mean:

 1 No labs have been created yet                                                                                     
 2 Labs need to be synced from an external source                                                                    

Would you like me to trigger the LMS sync pipeline to check if there are labs that need to be synchronized?
```

**Tool calls observed:**

```
2026-04-01 19:24:11.763 | INFO | nanobot.agent.loop:_prepare_tools:253 - Tool call: mcp_lms_lms_labs({})
2026-04-01 19:24:14.205 | INFO | nanobot.agent.loop:_prepare_tools:253 - Tool call: mcp_lms_lms_health({})
```

### Architecture

The agent uses MCP (Model Context Protocol) to connect to the LMS backend:

- MCP server runs as a subprocess (`python -m mcp_lms`)
- Environment variables provide backend URL (`NANOBOT_LMS_BACKEND_URL`) and API key (`NANOBOT_LMS_API_KEY`)
- Agent discovers tools automatically from MCP server
- Same MCP server can be used by any MCP-compatible agent (Claude, Cursor, etc.)

## Task 1C — Skill prompt

### Skill File Created

Created `nanobot/workspace/skills/lms/SKILL.md` with frontmatter `always: true` to ensure it's always loaded.

### Checkpoint: "Show me the scores" (without specifying a lab)

**Command:** `NANOBOT_LMS_BACKEND_URL=http://localhost:42002 NANOBOT_LMS_API_KEY=lab8-secret-key-123 uv run nanobot agent --logs --session cli:task1c -c ./config.json -m "Show me the scores"`

**Agent Response:**

```
I'll check what labs are available in the LMS first, then show you the scores.

[Tool call: mcp_lms_lms_labs({})]

The LMS backend is healthy but currently has no labs or data available. This means there are no scores to display yet.

The data may need to be synced from the autochecker. Would you like me to trigger the LMS sync pipeline to fetch the latest data?
```

**Behavior change with skill prompt:**

The agent now follows the strategy from `SKILL.md`:

1. ✅ First calls `mcp_lms_labs` to get available labs (as instructed)
2. ✅ Reports that backend is healthy but has no data
3. ✅ Offers to trigger the sync pipeline

**Before skill prompt:** Agent might have tried to guess or asked inconsistent clarifying questions.

**After skill prompt:** Agent consistently follows the strategy: check labs first → report status → offer sync.

### Skill File Content

```markdown
---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Skill

## Strategy Rules

### When user asks for lab-specific data without specifying a lab:
If the user asks for scores, pass rates, completion, groups, timeline, or top learners **without naming a lab**:
1. First call `mcp_lms_lms_labs` to get available labs
2. If multiple labs exist, ask the user to choose one
3. Use the lab title as the user-facing label

### When backend has no data:
- Explain that the backend is healthy but has no data yet
- Mention that data may need to be synced from the autochecker
- Offer to trigger the sync pipeline
```

---

## Task 1 Summary

| Part | Status | Evidence |
|------|--------|----------|
| 1A — Bare agent | ✅ Complete | Agent answers "What is the agentic loop?" with detailed explanation; explores local files for "What labs are available?" (no backend access) |
| 1B — MCP tools | ✅ Complete | MCP server connected, 9 tools registered (`mcp_lms_lms_health`, `mcp_lms_lms_labs`, etc.), backend healthy (item_count: 0) |
| 1C — Skill prompt | ✅ Complete | Agent follows strategy: calls `lms_labs` first when asked for scores without lab, offers sync pipeline |

### Files Created/Modified

| File | Purpose |
|------|---------|
| `nanobot/config.json` | Nanobot configuration with custom Qwen provider and MCP servers |
| `nanobot/workspace/skills/lms/SKILL.md` | LMS skill prompt with tool usage strategy |
| `nanobot/pyproject.toml` | Added nanobot-ai and mcp-lms dependencies |
| `~/.qwen/oauth_creds.json` | Qwen API credentials (on VM) |
| `.env.docker.secret` | Docker environment variables (LMS_API_KEY, QWEN_CODE_API_KEY, etc.) |

### Commands Used

```bash
# Part A - Install nanobot
cd ~/se-toolkit-lab-8
uv init nanobot
cd nanobot
uv add "nanobot-ai @ https://github.com/HKUDS/nanobot/archive/e7d371ec1e6531b28898ec2c869ef338e8dd46ec.zip"
uv run nanobot onboard -c config.json --workspace ./workspace

# Part B - Add MCP tools
uv add mcp-lms --editable ../mcp/mcp-lms

# Part C - Create skill prompt
mkdir -p workspace/skills/lms
cat > workspace/skills/lms/SKILL.md << 'EOF'
---
name: lms
description: Use LMS MCP tools for live course data
always: true
---
... (skill content)
EOF
```

## Task 2A — Deployed agent

<!-- Paste a short nanobot startup log excerpt showing the gateway started inside Docker -->

## Task 2B — Web client

<!-- Screenshot of a conversation with the agent in the Flutter web app -->

## Task 3A — Structured logging

<!-- Paste happy-path and error-path log excerpts, VictoriaLogs query screenshot -->

## Task 3B — Traces

<!-- Screenshots: healthy trace span hierarchy, error trace -->

## Task 3C — Observability MCP tools

<!-- Paste agent responses to "any errors in the last hour?" under normal and failure conditions -->

## Task 4A — Multi-step investigation

<!-- Paste the agent's response to "What went wrong?" showing chained log + trace investigation -->

## Task 4B — Proactive health check

<!-- Screenshot or transcript of the proactive health report that appears in the Flutter chat -->

## Task 4C — Bug fix and recovery

<!-- 1. Root cause identified
     2. Code fix (diff or description)
     3. Post-fix response to "What went wrong?" showing the real underlying failure
     4. Healthy follow-up report or transcript after recovery -->

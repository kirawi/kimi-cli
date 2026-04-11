Manage agents (as subprocesses) to handle complex, multi-step tasks autonomously.

The `Agent` tool will, by default, launch a new agent. Or, if `resume` is enabled, it will resume an existing agent given its corresponding `agent_id` with the new task. Because each agent maintains its own unique state and context window, a resumed agent can reuse its previous work and findings.

**Available Built-in Agent Types**
${BUILTIN_AGENT_TYPES_MD}

**Usage Notes**
- Always provide a short `description` (3-5 words) summarizing what the agent will do.
- By default, any spawned agent will be `coder`-focused. Depending on the task, you can use `subagent_type` to select a different built-in agent type.
- Use `model` when you need to override the built-in type's default model or the parent agent's current model.
- If an existing subagent already has relevant context or the task is a continuation of its prior work, prefer `resume` over creating a new instance.
- Default to foreground execution. Use `run_in_background=true` only when the task can continue independently, you do not need the result immediately, and there is a clear benefit to returning control before it finishes.
- Be explicit about whether the subagent should write code or only do research.
- The subagent result is only visible to you. If the user should see it, summarize it yourself.

**Explore Agent — Preferred for Codebase Research**
Always use `subagent_type="explore"` when you need to understand the workspace before making suggestions/changes, fixing bugs, planning features, or answering queries about the workspace. The exploration agent is optimized for efficient read-only investigation. Use it when:
- A task will likely require more than 3 search queries or reading many large files
- You need to understand how a module, feature, or code path works
- You are about to enter plan mode and want to gather context first
- You want to investigate multiple independent questions — launch multiple explore agents concurrently

Its strengths:
- Rapidly finding files using glob patterns
- Searching code and text with powerful regex patterns
- Reading and analyzing file contents

When calling explore, specify the desired thoroughness in the prompt:
- "quick": targeted lookups — find a specific file, function, or config value
- "medium": understand a module — how does auth work, what calls this API
- "thorough": cross-cutting analysis — architecture overview, dependency mapping, multi-module investigation

**When Not To Use Agent**
- Reading a known file path
- Searching a small number of already known files
- Tasks that can be completed in one or two direct tool calls

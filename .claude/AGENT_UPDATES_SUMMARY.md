# Agent Updates Summary - CONTEXT.md Integration

## Overview
All agent instruction files have been updated to include awareness of CONTEXT.md files throughout the project. Agents are now instructed to read these context files FIRST before querying the context-manager.

## Changes Made

### 1. context-manager.md
**Updates**:
- Added "CONTEXT.md Files First" directive in context distribution section
- Updated briefing package to include `context_files` array
- Added `recommended_reading_order` to briefing responses
- Modified initial scan to detect and note CONTEXT.md files
- Added instruction to always include CONTEXT.md file paths in briefings

**Key Change**: Context-manager now prioritizes directing agents to CONTEXT.md files before providing context from context-manager.json

### 2. Development Agents

#### backend-architect.md
**Updates**:
- Added "Step 0: Read CONTEXT.md Files FIRST" to interaction model
- Lists relevant CONTEXT.md files: root, app, routes, migrations
- Changed from 2-phase to 3-phase process
- Instructs to query context-manager ONLY for info not in CONTEXT.md

#### python-pro.md
**Updates**:
- Added "Step 0: Read CONTEXT.md Files FIRST"
- Lists relevant files: root, app, routes, migrations
- Emphasizes CONTEXT.md contains function signatures and patterns
- Changed from 2-phase to 3-phase process

#### flask-dev.md
**Updates**:
- Added complete list of ALL CONTEXT.md files at the top
- Reinforced "PLANNING ONLY" directive
- Instructs to read CONTEXT.md files before providing analysis
- Lists 7 CONTEXT.md files: root, app, routes, templates, static, migrations, uploads

#### frontend-developer.md
**Updates**:
- Added "Step 0: Read CONTEXT.md Files FIRST"
- Lists frontend-relevant files: templates, static, routes, app
- Emphasizes duolingo-buttons, CSRF handling, context variables
- Changed from 2-phase to 3-phase process

### 3. Quality Assurance Agents

#### code-reviewer.md
**Updates**:
- Added "Step 0: Read CONTEXT.md Files FIRST"
- Lists QA-relevant files: app, routes, templates, static, migrations
- Emphasizes coding standards, security patterns, best practices
- Changed from 2-phase to 3-phase process

#### architect-review.md
**Updates**:
- Added "Step 0: Read CONTEXT.md Files FIRST"
- Lists architecture-relevant files: app, routes, migrations
- Emphasizes architectural patterns and design principles
- Changed from 2-phase to 3-phase process

#### security-auditor.md
**Updates**:
- Added "Step 0: Read CONTEXT.md Files FIRST"
- Lists security-relevant files: app, routes, uploads, templates, static
- Emphasizes security patterns (CSRF, auth, file uploads, XSS)
- Changed from 2-phase to 3-phase process

### 4. Documentation Agents

#### documentation-expert.md
**Updates**:
- Added "Step 0: Read ALL CONTEXT.md Files FIRST"
- Lists ALL 8 CONTEXT.md files in the project
- Notes that CONTEXT.md files ARE the documentation structure to maintain
- Changed from 2-phase to 3-phase process

#### api-documenter.md
**Updates**:
- Added "Step 0: Read CONTEXT.md Files FIRST"
- Lists API-relevant files: routes (CRITICAL), app, templates, root
- Emphasizes ROUTES_CONTEXT.md as starting point for API docs
- Changed from 2-phase to 3-phase process

### 5. Meta-Orchestration Agents

#### agent-organizer.md
**Updates**:
- Added "IMPORTANT: Check for CONTEXT.md Files First" section
- Lists all 8 CONTEXT.md files in project analysis section
- Added "Available Context Documentation" to output format
- Added note to context-manager description about CONTEXT.md files

## CONTEXT.md Files Location Reference

For agent instructions, the following files exist:

```
/CONTEXT.md                     - Root directory (config, deployment)
/app/CONTEXT.md                 - Application structure
/app/ROUTES_CONTEXT.md          - Route blueprints
/app/templates/CONTEXT.md       - Jinja2 templates
/app/static/CONTEXT.md          - Static assets
/migrations/CONTEXT.md          - Database migrations
/uploads/CONTEXT.md             - File uploads
/.claude/CONTEXT.md             - Agent system
```

## New Agent Workflow

### Before Updates:
1. Query context-manager for briefing
2. Synthesize and clarify
3. Perform task

### After Updates:
1. **Read relevant CONTEXT.md files FIRST**
2. Query context-manager ONLY for missing information
3. Synthesize and clarify
4. Perform task

## Expected Benefits

1. **Faster Context Acquisition**: Agents get context immediately without waiting for context-manager query/response
2. **Reduced context-manager Load**: Context-manager only queried for dynamic information not in CONTEXT.md
3. **More Accurate Context**: CONTEXT.md files are maintained and up-to-date with specific patterns
4. **Better Agent Performance**: Agents have detailed function signatures, patterns, and examples upfront
5. **Clearer Communication**: Agents know project structure before asking clarifying questions

## Verification Checklist

- [x] context-manager.md - Instructs to provide CONTEXT.md file paths in briefings
- [x] backend-architect.md - Step 0 added
- [x] python-pro.md - Step 0 added
- [x] flask-dev.md - CONTEXT.md list added at top
- [x] frontend-developer.md - Step 0 added
- [x] code-reviewer.md - Step 0 added
- [x] architect-review.md - Step 0 added
- [x] security-auditor.md - Step 0 added
- [x] documentation-expert.md - Step 0 with ALL files
- [x] api-documenter.md - Step 0 added with ROUTES_CONTEXT.md emphasis
- [x] agent-organizer.md - CONTEXT.md check added to project analysis

## Next Steps

1. Test agent behavior with CONTEXT.md files in place
2. Monitor if agents actually read CONTEXT.md files first
3. Refine CONTEXT.md content based on agent usage patterns
4. Consider adding more specific CONTEXT.md files for complex subdirectories
5. Update CONTEXT.md files when project structure changes

## Notes

- All agents now follow 3-phase process (CONTEXT.md → context-manager → task)
- flask-dev has CONTEXT.md list at top since it's planning-only
- documentation-expert reads ALL CONTEXT.md files (it maintains them)
- api-documenter emphasizes ROUTES_CONTEXT.md as critical starting point
- context-manager now includes CONTEXT.md files in every briefing

# Start JIRA Ticket

Begin work on a JIRA ticket with proper setup and time tracking.

## Arguments
- JIRA ticket ID (e.g., TC-31)

## Process

1. **Record Start Time**
   Ask the user for the current time and record it

2. **Check the status of the current branch**
   ```bash
   git status
   ```

3. **Create Feature Branch if not already on one**
   ```bash
   git checkout -b feature/$ARGUMENTS-brief-description
   ```
   
4. **Read Context**
	 - Check if there's a markdown file for this ticket (like CLAUDE.md, CLAUDE-TC-31.md)
	 - Review CLAUDE.md for project patterns
	 - Search for related files in the codebase
  
5. **Create TODO List**
   Based on the ticket requirements, create a structured TODO list with time estimates

6. **Confirm Before Starting**
   Present the plan and wait for user approval

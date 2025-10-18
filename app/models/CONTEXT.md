# Database Models

## Overview
Modular SQLAlchemy ORM models representing core domain entities.

## Model Relationships
- User: Primary authentication model
- BlogPost: Content management with draft capabilities
- MinecraftCommand: Game server interaction model

## Key Design Principles
- Use of bcrypt for password hashing
- Draft post management via is_draft boolean
- Consistent use of timestamps (created_at, updated_at)
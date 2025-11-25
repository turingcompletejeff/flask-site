# Database Models

## Overview
Modular SQLAlchemy ORM models representing core domain entities.

## Model Relationships
- User: Primary authentication model with role-based access
- BlogPost: Content management with draft capabilities and image support
- MinecraftCommand: Game server RCON interaction model
- MinecraftLocation: Fast travel location management with coordinate validation and image support
  - Relationship: MinecraftLocation → User (created_by foreign key)
  - Coordinate bounds: X/Z (unlimited), Y (-64 to 320 for Minecraft 1.18+)
  - Image handling: Portrait images with auto-generated 300x300 thumbnails

## Key Design Principles
- Use of bcrypt for password hashing
- Draft post management via is_draft boolean
- Consistent use of timestamps (created_at, updated_at)
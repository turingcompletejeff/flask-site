#!/usr/bin/env python3
"""
Seed script for minecraft_commands table.
Converts old array format to new JSON format: {'args': [...]}
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import MinecraftCommand


def parse_pg_array(array_str):
    r"""
    Parse PostgreSQL array format like {grant,revoke} to Python list.
    Returns None for \N (NULL) values.
    """
    if array_str == r'\N' or array_str is None:
        return None

    # Remove curly braces
    array_str = array_str.strip('{}')

    # Handle empty string
    if not array_str or array_str == '':
        return []

    # Split by comma and clean up
    items = [item.strip('"').strip() for item in array_str.split(',')]

    # Filter out empty strings unless that's the only item
    if len(items) == 1:
        return items
    else:
        return [item for item in items if item]


# Minecraft commands data (converted from dump file)
commands_data = [
    (1, '/advancement', '{grant,revoke}'),
    (2, '/attribute', '{get,base,modifier}'),
    (3, '/execute', '{run,if,unless,as,at,store,positioned,rotated,facing,align,anchored,in,summon,on}'),
    (4, '/bossbar', '{add,remove,list,set,get}'),
    (5, '/clear', r'\N'),
    (6, '/clone', '{"",from}'),
    (7, '/damage', r'\N'),
    (8, '/data', '{merge,get,remove,modify}'),
    (9, '/datapack', '{enable,disable,list}'),
    (10, '/debug', '{start,stop,function}'),
    (11, '/defaultgamemode', r'\N'),
    (12, '/difficulty', '{peaceful,easy,normal,hard}'),
    (13, '/effect', '{clear,give}'),
    (14, '/me', r'\N'),
    (15, '/enchant', r'\N'),
    (16, '/experience', '{add,set,query}'),
    (17, '/fill', '{replace,keep,outline,hollow,destroy}'),
    (18, '/fillbiome', '{replace}'),
    (19, '/forceload', '{add,remove,query}'),
    (20, '/function', r'\N'),
    (21, '/gamemode', r'\N'),
    (22, '/give', r'\N'),
    (23, '/help', r'\N'),
    (24, '/item', '{replace,modify}'),
    (25, '/kick', r'\N'),
    (26, '/kill', r'\N'),
    (27, '/list', '{uuids}'),
    (28, '/locate', '{structure,biome,poi}'),
    (29, '/loot', '{replace,insert,give,spawn}'),
    (30, '/msg', r'\N'),
    (31, '/particle', r'\N'),
    (32, '/place', '{feature,jigsaw,structure,template}'),
    (33, '/playsound', '{master,music,record,weather,block,hostile,neutral,player,ambient,voice}'),
    (34, '/random', '{value,roll,reset}'),
    (35, '/reload', r'\N'),
    (36, '/recipe', '{give,take}'),
    (37, '/return', '{"",fail,run}'),
    (38, '/ride', '{mount,dismount}'),
    (39, '/say', r'\N'),
    (40, '/schedule', '{function,clear}'),
    (41, '/scoreboard', '{objectives,players}'),
    (42, '/seed', r'\N'),
    (43, '/setblock', '{destroy,keep,replace}'),
    (44, '/spawnpoint', r'\N'),
    (45, '/setworldspawn', r'\N'),
    (46, '/spectate', r'\N'),
    (47, '/spreadplayers', '{"",under}'),
    (48, '/stopsound', '{*,master,music,record,weather,block,hostile,neutral,player,ambient,voice}'),
    (49, '/summon', r'\N'),
    (50, '/tag', '{add,remove,list}'),
    (51, '/team', '{list,add,remove,empty,join,leave,modify}'),
    (52, '/teammsg', r'\N'),
    (53, '/teleport', r'\N'),
    (54, '/tellraw', r'\N'),
    (55, '/tick', '{query,rate,step,sprint,unfreeze,freeze}'),
    (56, '/time', '{set,add,query}'),
    (57, '/title', '{clear,reset,title,subtitle,actionbar,times}'),
    (58, '/trigger', r'\N'),
    (59, '/weather', '{clear,rain,thunder}'),
    (60, '/worldborder', '{add,set,center,damage,get,warning}'),
    (61, '/jfr', '{start,stop}'),
    (62, '/ban-ip', r'\N'),
    (63, '/banlist', '{ips,players}'),
    (64, '/ban', r'\N'),
    (65, '/deop', r'\N'),
    (66, '/op', r'\N'),
    (67, '/pardon', r'\N'),
    (68, '/pardon-ip', r'\N'),
    (69, '/perf', '{start,stop}'),
    (70, '/save-all', '{flush}'),
    (71, '/save-off', r'\N'),
    (72, '/save-on', r'\N'),
    (73, '/setidletimeout', r'\N'),
    (74, '/stop', r'\N'),
    (75, '/transfer', r'\N'),
    (76, '/whitelist', '{on,off,list,add,remove,reload}'),
    (77, '/gamerule', '{announceAdvancements,blockExplosionDropDecay,commandBlockOutput,commandModificationBlockLimit,disableElytraMovementCheck,disableRaids,doDaylightCycle,doEntityDrops,doFireTick,doImmediateRespawn,doInsomnia,doLimitedCrafting,doMobLoot,doMobSpawning,doPatrolSpawning,doTileDrops,doTraderSpawning,doVinesSpread,doWardenSpawning,doWeatherCycle,drowningDamage,enderPearlsVanishOnDeath,fallDamage,fireDamage,forgiveDeadPlayers,freezeDamage,globalSoundEvents,keepInventory,lavaSourceConversion,logAdminCommands,maxCommandChainLength,maxCommandForkCount,maxEntityCramming,mobExplosionDropDecay,mobGriefing,naturalRegeneration,playersNetherPortalCreativeDelay,playersNetherPortalDefaultDelay,playersSleepingPercentage,projectilesCanBreakBlocks,randomTickSpeed,reducedDebugInfo,sendCommandFeedback,showDeathMessages,snowAccumulationHeight,spawnChunkRadius,spawnRadius,spectatorsGenerateChunks,tntExplosionDropDecay,universalAnger,waterSourceConversion}'),
]


def seed_commands():
    """Seed the minecraft_commands table with initial data."""
    app = create_app()

    with app.app_context():
        # Clear existing commands
        print("Clearing existing minecraft_commands...")
        MinecraftCommand.query.delete()
        db.session.commit()

        print(f"Seeding {len(commands_data)} Minecraft commands...")

        for command_id, command_name, options_str in commands_data:
            # Parse the PostgreSQL array to Python list
            args_list = parse_pg_array(options_str)

            # Convert to new JSON format: {'args': [...]}
            if args_list is not None:
                options_json = {'args': args_list}
            else:
                # NULL becomes empty args
                options_json = {'args': []}

            command = MinecraftCommand(
                command_id=command_id,
                command_name=command_name,
                options=options_json
            )
            db.session.add(command)

        db.session.commit()

        # Verify
        count = MinecraftCommand.query.count()
        print(f"✓ Successfully seeded {count} Minecraft commands")

        # Show a few examples
        print("\nSample commands:")
        for cmd in MinecraftCommand.query.limit(5).all():
            print(f"  {cmd.command_name}: {cmd.options}")


if __name__ == '__main__':
    seed_commands()

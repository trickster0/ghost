#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import PyQt5
import base64
import qtinter
import asyncio

from fastapi_websocket_rpc import WebSocketRpcClient
from fastapi_websocket_rpc import RpcMethodsBase

class RpcClientMethods( RpcMethodsBase ):
    """
    Callback methods exposed to the server to send data to open tabs.
    """
    def __init__( self, ghost ):
        # initialize the parent class
        super().__init__();

        # set the ghost object
        self.ghost = ghost

class RpcClient:
    """
    A RPC client for calling arbitrary methods on the server like exporting a 
    agent or requesting a task be queued to the specified agent. Furthermore
    provides callack methods for the server to execute to fill in target UI
    elements.
    """
    def __init__( self, ghost ):

        # set the ghost object
        self.ghost = ghost

        # set the rpc client object to nothing to initialize it
        self.rpc = None

    async def _on_connect_leave( self, channel ):
        """
        Execute when the the RPC channel is lost. Prints an error message to the screen.
        """
        # Print an error message!
        qtinter.modal( PyQt5.QtWidgets.QMessageBox.critical( self.ghost, 'Connection Lost', 'The connection to the teamserver was lost' ) );

        # Print stdout log
        self.ghost.log.critical( 'The connection to the teamserver was lost' );

        raise SystemExit

    async def start( self, teamserver_host : str, teamserver_port : int ):
        """
        Connects to the target teamserver host:port and initializes the RPC channel.
        """
        # create the rpc client object
        self.rpc = WebSocketRpcClient( f'ws://{teamserver_host}:{teamserver_port}/ws', RpcClientMethods( self.ghost ), on_disconnect = [ self._on_connect_leave ] );

        # request that we establish a connection to the target host:port
        await self.rpc.__connect__();

    async def teamserver_export_payload( self, ip_address, icmp_sleep, icmp_sleep_jitter, icmp_chunk_length, icmp_query_timeout, sleep, jitter, kill_date, is_arch64 ) -> bytes:
        """
        Requests that the server return a configured shellcode.
        """
        # Execute the remote method and decode the response from base64
        return base64.b64decode( ( await self.rpc.other.teamserver_export_payload(
            ip_address = ip_address,
            icmp_sleep = icmp_sleep,
            icmp_sleep_jitter = icmp_sleep_jitter,
            icmp_chunk_length = icmp_chunk_length,
            icmp_query_timeout = icmp_query_timeout,
            sleep = sleep,
            jitter = jitter,
            kill_date = kill_date,
            is_arch64 = is_arch64
        ) ).result );

    async def teamserver_agent_list_get( self ) -> list:
        """
        Requests that the teamserver return a list of all the agents in the database
        """
        return ( ( await self.rpc.other.teamserver_agent_list_get() ).result );

    async def teamserver_event_log_get( self, log_offset ) -> list:
        """
        Requests that the teamserver return a list of all the events past the last log offset
        """
        # Request the event log starting @ log_offset
        return ( ( await self.rpc.other.teamserver_event_log_get( log_offset = log_offset ) ).result );

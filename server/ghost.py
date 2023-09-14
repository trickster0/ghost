#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import asyncio
import asyncclick

from lib import sck
from lib import rpc
from lib import logger
from lib import database

class Ghost:
    """
    Primary 'ghost' class for providing a reference for the rest of the
    underyling UI libraries.

    @rpc = RpcServer() class reference for getting information about channels
    @dbs = Database() class reference for interacting with the database
    @log = Fancy log formatter for output
    @key = Encryption key for the communications
    """
    def __init__( self, encryption_key ):
        # set the logging object
        self.log = logger.init( True );

        # set the rpc server class
        self.rpc = rpc.RpcServer( self );

        # set the sock serer class
        self.sck = sck.SckServer( self );

        # set the sql database class
        self.dbs = database.Database( self );

        # set the key to initialize it
        self.key = encryption_key

    async def start( self, teamserver_host, teamserver_port, listener_host ):
        """
        Starts the RPC service and ICMP listener.
        """
        # create the database if it does not exist
        await self.dbs.start();

        # start the task for handling incoming connections via RPC
        rpc_task = await self.rpc.start( teamserver_host, teamserver_port );

        # start the task for handling incoming connections via ICMP
        sck_task = await self.sck.start( listener_host );

        # wait on the task to complete or fail
        await asyncio.wait( [ rpc_task ] );

@asyncclick.command( no_args_is_help = True )
@asyncclick.argument( 'rpc-host', type = str, metavar = 'rpc-host' )
@asyncclick.argument( 'rpc-port', type = int, metavar = 'rpc-port' )
@asyncclick.argument( 'listener', type = str, metavar = 'listener' )
@asyncclick.argument( 'arc4-key', type = str, metavar = 'arc4-key' )
async def ghost_main( rpc_host, rpc_port, listener, arc4_key ):
    """
    A minimal command and control over ICMP for pivoting into heavily
    monitored environments and managing remote instances.
    """
    # create the primary 'ghost' class
    ghost = Ghost( arc4_key );

    # start the teamserver to handle incoming clients and socket server
    await ghost.start( rpc_host, rpc_port, listener );

if __name__ in '__main__':
    # call the primary application entrypoint
    ghost_main();

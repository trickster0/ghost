#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import pytz
import asyncio
import datetime
import calendar

from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Define the "Declarative Base"
dec_base = declarative_base();

class EventLog( dec_base ):
    """
    The teamserver 'event log'. Data that the teamserver broadcasts to operators
    """
    __tablename__ = 'eventslog'

    id      = Column( Integer, primary_key = True, unique = True );
    ev_time = Column( Integer, nullable = False );
    ev_type = Column( Integer, nullable = False );
    message = Column( String, nullable = False );

class AgentLog( dec_base ):
    """
    The agent console log. Sort by agent_id for specific agent output
    """
    __tablename__ = 'agentslog'

    id          = Column( Integer, primary_key = True, unique = True );
    agent_id    = Column( Integer, nullable = False );
    log_time    = Column( Integer, nullable = False );
    log_type    = Column( Integer, nullable = False );
    log_message = Column( String, nullable = False );

class Agent( dec_base ):
    """
    Agent information that is sent during the initial check-in.
    """
    __tablename__ = 'agents'

    id          = Column( Integer, primary_key = True, unique = True );
    agent_id    = Column( Integer, nullable = False, unique = True );
    is_alive    = Column( Boolean, nullable = False );
    os_major    = Column( Integer, nullable = False );
    os_minor    = Column( Integer, nullable = False );
    os_build    = Column( Integer, nullable = False );

    pid         = Column( Integer, nullable = False );
    ppid        = Column( Integer, nullable = False );
    process     = Column( String, nullable = False );

class Database:
    """
    A wrapper around an SQL alchemy database for storing information about
    about agents, agent console interactions and teamserver event log info
    """
    def __init__( self, ghost ):
        # Set the reference to the Ghost class
        self.ghost = ghost

        # Lock for the list of agents and their queue
        self.agent_list_lock = asyncio.Lock()

        # List of the agents their and multiprocessing queue
        self.agent_list = []

        # create the async engine
        self.sql_engine = create_async_engine( 'sqlite+aiosqlite:///ghost-server.db', future = True );

        # create the async session
        self.sql_session = sessionmaker( bind = self.sql_engine, expire_on_commit = False, class_ = AsyncSession );

    async def start( self ):
        """
        Creates the SQL database if it does not exist
        """
        # Does this path exist and is it a file?
        if not os.path.exists( './ghost-server.db' ) and not os.path.isfile( './ghost-server.db' ):
            # It does not or it isnt a file!. Create the database
            async with self.sql_engine.begin() as engine:
                # create the database / tables
                await engine.run_sync( dec_base.metadata.create_all );

        # Establish a session to the DB now
        async with self.sql_session() as session:
            # Start the session
            async with session.begin():
                # Perform the query to query all the agents that are marked as alive in the DB
                sql_result = await session.execute( select( Agent ).where( Agent.is_alive == True ) );

                # Loop through each SQL entry
                for sql_entry in sql_result.scalars().all():
                    # Add the entry to the list of valid agents with its new queue!
                    self.agent_list.append( { 'id': sql_entry.agent_id, 'queue': asyncio.Queue() } );

    async def database_event_add( self, ev_type, ev_msg ):
        """
        Adds an event to the log.
        """
        # Creates an SQL "session"
        async with self.sql_session() as session:
            # Start the session
            async with session.begin():
                # Create an 'event'
                event = EventLog( ev_time = calendar.timegm( datetime.datetime.now( tz = pytz.UTC ).utctimetuple() ), ev_type = ev_type, message = ev_msg );

                # Add to the database
                session.add( event );

                # Commit it!
                await session.commit()

                # Flush the results
                await session.flush()

    async def database_event_get_queue( self, log_offset ):
        """
        Returns all events queued at and past the log offset
        """
        # Creates an SQL "session"
        async with self.sql_session() as session:
            # Start the session
            async with session.begin():
                # Look for any events that are at or past the log offset
                sql_result = await session.execute( select( EventLog ).offset( log_offset ).limit( 1000 ) );

                # Return the unfiltered results!
                return sql_result.scalars().all()

    async def database_agent_get_list( self ):
        """
        Returns a list of all the agents in the database.
        """
        # Creates an SQL "session"
        async with self.sql_session() as session:
            # Start the session
            async with session.begin():
                # Look for any events that are at or past the specifed index
                sql_result = await session.execute( select( Agent ) );

                # Return the unfiletered results!
                return sql_result.scalars().all()

    async def database_agent_is_alive( self, agent_id ):
        """
        Returns whether or not the agent is alive.
        """
        # Creates an SQL "session"
        async with self.sql_session() as session:
            # Start the session
            async with session.begin():
                # Select within the table where it matches the specified agent_id
                sql_result = await session.execute( select( Agent ).where( Agent.agent_id == agent_id ) );

                # Return whether or not it is alive
                return sql_result.scalar().is_alive

    async def database_agent_is_valid( self, agent_id ):
        """
        Returns whether or not the agent is valid
        """
        # Creates an SQL "session"
        async with self.sql_session() as session:
            # Start the session
            async with session.begin():
                # Select within the table where it matches the specified agent_id
                sql_result = await session.execute( select( Agent ).where( Agent.agent_id == agent_id ) );

                # Returns whether or not an entry exists
                return sql_result.scalar() is not None

    async def database_agent_add( self, agent_id, os_major, os_minor, os_build, pid, ppid, process ):
        """
        Adds an agent to the database and active agent list
        """
        # Acquire a lock on the list
        async with self.agent_list_lock:
            # Creates an SQL "session"
            async with self.sql_session() as session:
                # Start the session
                async with session.begin():
                    # Create the row entry
                    agent = Agent( agent_id = agent_id, is_alive = True, os_major = os_major, os_minor = os_minor, os_build = os_build, pid = pid, ppid = ppid, process = process );

                    # add the entry to the table
                    session.add( agent );

                    # commit the entry to the table
                    await session.commit();

                    # flush the cache
                    await session.flush();

            # Add the agent to the list!
            self.agent_list.append( { 'id': agent_id, 'queue': asyncio.Queue() } );

    async def database_agent_add_queue( self, agent_id, message ):
        """
        Adds the message to the queue for the agent.
        """
        # Acquire a lock on the list
        async with self.agent_list_lock:
            # Attempt to pull the queue
            agent_queue = [ agent[ 'queue' ] for agent in self.agent_list if agent[ 'id' ] == agent_id ][ 0 ]

            # Add to the queue
            await agent_queue.put( message );

    async def database_agent_get_queue( self, agent_id ):
        """
        Empties the queue for the specific agent.
        """
        # Acquire a lock on the list
        async with self.agent_list_lock:

            # Return buffer
            return_buff = b''

            # Attempt to pull the queue
            agent_queue = [ agent[ 'queue' ] for agent in self.agent_list if agent[ 'id' ] == agent_id ][ 0 ]

            # While we are not a 
            while agent_queue.qsize() != 0:
                # Add to the return buffer!
                return_buff += await agent_queue.get()

            # Return the byts buffer
            return return_buff

        # Return nothing?
        return ''

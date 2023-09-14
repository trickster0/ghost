#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import PyQt5
import asyncio
import qtinter

from lib import types

class TeamserverEventLogTab( PyQt5.QtWidgets.QWidget ):
    """
    A 'tab' for reading the teamservers event log.
    """
    def __init__( self, ghost ):
        # Initialize the parent
        super( PyQt5.QtWidgets.QWidget, self ).__init__( ghost );

        # Set the ghost object
        self.ghost = ghost

        # Set the last recorded offset into the log
        self.log_offset = 0

        # Set the output layout
        self.layout = PyQt5.QtWidgets.QHBoxLayout();

        # Widget for handling teamserver output
        self.output = PyQt5.QtWidgets.QTextEdit();
        self.output.setReadOnly( True );
        self.output.setFocusPolicy( PyQt5.QtCore.Qt.NoFocus );

        # Add the widget to the layout
        self.layout.addWidget( self.output );

        # Lock for monitoring logs
        self.monitor_log_lock = asyncio.Lock();

        # Timer for polling for new log data
        self.monitor_log = PyQt5.QtCore.QTimer();
        self.monitor_log.setInterval( 100 );
        self.monitor_log.timeout.connect( self._monitor_log );
        self.monitor_log.start()

        # Set the layout
        self.setLayout( self.layout );

    async def write_to_log( self, message ):
        """
        Writes the message to the log and adjusts the scroll bar.
        """
        # Append the message to the log
        self.output.append( message );

        # Adjust the log position to the end
        cursor = self.output.textCursor()
        cursor.movePosition( PyQt5.QtGui.QTextCursor.End, );

        # Set the new cursor position
        self.output.setTextCursor( cursor );

    @qtinter.asyncslot
    async def _monitor_log( self ):
        """
        Monitors the event log and if new data is available, writes to the
        log.
        """
        async with self.monitor_log_lock:
            # Attempt to pull the latest results based on the last log offset
            log_results = await self.ghost.rpc.teamserver_event_log_get( self.log_offset );

            # No results were returned. Abort
            if not log_results:
                return

            # Set the last log offset 
            self.log_offset += len( log_results );

            # Loop through the list of log results
            for log_entry in log_results:

                # Format the incoming timestamp to a string we can read
                time_stamp = ''

                if log_entry[ 'type' ] == types.EventLogType.INFO:
                    # Format the message!
                    log_message = f'[<font color="Aqua">*</font>] {log_entry[ "message" ]}'

                    # Write the message
                    await self.write_to_log( log_message );
                if log_entry[ 'type' ] == types.EventLogType.GOOD:
                    # Format the message!
                    log_message = f'[<font color="Light Green">+</font>] {log_entry[ "message" ]}'

                    # Write the message
                    await self.write_to_log( log_message );
                if log_entry[ 'type' ] == types.EventLogType.ERROR:
                    # Format the message!
                    log_message = f'[<font color="Red">-</font>] {log_entry[ "message" ]}'

                    # Write the message
                    await self.write_to_log( log_message );

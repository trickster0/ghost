#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import PyQt5
import asyncio
import qtinter

class AgentsWidget( PyQt5.QtWidgets.QWidget ):
    """
    A 'core' display within the ghost application view. Intended
    to display all the active agents and their status, as well
    as the information about them.

    Furthermore, its a core widget for performing actions on the
    widgets with the mouse.

    Provides functionality to interact with a pseudo-console,
    perform LDAP queries, and bulk interaction with multiple
    agents.
    """
    COLUMN_NAMES = [ "ID", "OS", "Process", "PID", "PPID", "Username" ]
    COLUMN_COUNT = len( COLUMN_NAMES );

    def __init__( self, ghost ):
        # init the widget from the ghost object
        super( PyQt5.QtWidgets.QWidget, self ).__init__( ghost );

        # set the ghost 'object' for performing most base operations
        self.ghost = ghost
            
        # create the primary layout for this widget
        self.layout = PyQt5.QtWidgets.QHBoxLayout();

        # List of agents in the database
        self.agents = []

        # create the table to display the agents
        self.agent_table = PyQt5.QtWidgets.QTableWidget();
        self.agent_table.setShowGrid( False );
        self.agent_table.setFocusPolicy( PyQt5.QtCore.Qt.NoFocus );
        self.agent_table.setSelectionBehavior( PyQt5.QtWidgets.QTableView.SelectRows );
        self.agent_table.setRowCount( 0 );
        self.agent_table.setColumnCount( self.COLUMN_COUNT );
        self.agent_table.setHorizontalHeaderLabels( self.COLUMN_NAMES );
        self.agent_table.verticalHeader().setVisible( False );
        self.agent_table.horizontalHeader().setHighlightSections( False );

        # Loop through each column
        for i in range( 0, self.COLUMN_COUNT ):
            # Request that the column be stretched to fit the table view
            self.agent_table.horizontalHeader().setSectionResizeMode( i, PyQt5.QtWidgets.QHeaderView.Stretch );

        # add the table to the primary layout
        self.layout.addWidget( self.agent_table );

        # Lock for monitoring agents callback
        self.monitor_agent_lock = asyncio.Lock();

        # create the async queue for monitoring agents
        self.monitor_agent = PyQt5.QtCore.QTimer();
        self.monitor_agent.setInterval( 100 );
        self.monitor_agent.timeout.connect( self._monitor_agents );
        self.monitor_agent.start()

        # set the layout for this layout
        self.setLayout( self.layout );

    async def _monitor_agents_add( self ):
        """
        Adds an agent to the table.
        """
        pass

    @qtinter.asyncslot
    async def _monitor_agents( self ):
        """
        Monitors for new agents and updates the table with their information.
        """
        async with self.monitor_agent_lock:
            # Query the list of the agents!
            agent_list = await self.ghost.rpc.teamserver_agent_list_get();

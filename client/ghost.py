#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import PyQt5
import click
import qtinter
import qdarktheme

from lib import rpc
from lib import logger
from lib.ui import agents_widget
from lib.ui import tab_widget

# Tabs
from lib.ui.tabs import teamserver_event_log_tab

# Dialogs
from lib.ui.dialogs import export_payload_dialog

class Ghost( PyQt5.QtWidgets.QMainWindow ):
    """
    The 'main' window for the Qt5 application. Furthermore acts as a wrapper
    for other underlying functionality ( tab, RPC ) so that we don't have to
    pass too many classes around.

    @tab_widget    = tab_widget.TabWidget() handler for other underlying UI
    @agents_widget = agents_widget.AgentsWidget() handler for underlying UI
    @rpc           = RPC client exposed for underylying UI
    @log           = Logging wrapper.
    """
    def __init__( self, screen_height, screen_width, rpc_host, rpc_port ):
        # init the primary QMainWindow class
        super().__init__();

        # set the teamserver host:port
        self.teamserver_host = rpc_host
        self.teamserver_port = rpc_port

        # set the rpc client object
        self.rpc = rpc.RpcClient( self );

        # set the log object
        self.log = logger.init( True );

        # initialize the window information with the title and screen size
        self.setWindowTitle( 'GuidePoint Security LLC: Ghost' );
        self.setGeometry( 0, 0, screen_width, screen_height );

        # create the primary widget to hold the 'layout'
        ghost_main_widget = PyQt5.QtWidgets.QWidget();
        self.setCentralWidget( ghost_main_widget );

        # create the primary layout to setup the layout of the implant / tab
        ghost_main_layout = PyQt5.QtWidgets.QVBoxLayout();
        ghost_main_widget.setLayout( ghost_main_layout );

        # create the primary splitter between the two primary widgets ( tab / agents )
        ghost_main_vsplit = PyQt5.QtWidgets.QSplitter( PyQt5.QtCore.Qt.Vertical );
        ghost_main_vsplit.setHandleWidth( 1 );

        # add the agents table to the view
        self.agents_widget = agents_widget.AgentsWidget( self );
        self.agents_widget.setGeometry( 0, 0, screen_width, int( screen_height / 2 ) );

        # add the tab interface into the view
        self.tab_widget = tab_widget.TabWidget( self );
        self.tab_widget.setGeometry( 0, 0, screen_width, int( screen_height / 2 ) );

        # Add the two widgets in between the vsplitter
        ghost_main_vsplit.addWidget( self.agents_widget );
        ghost_main_vsplit.addWidget( self.tab_widget );
        ghost_main_layout.addWidget( ghost_main_vsplit );

        # Menu: "Teamserver". A collection of options for interfacing with the
        # teamserver
        self.teamserver_menu = self.menuBar().addMenu( 'Teamserver' );

        # Menu: "Teamserver". Action: "View Event Log"
        self.teamserver_menu_action_view_event_log = PyQt5.QtWidgets.QAction( 'View Event Log' );
        self.teamserver_menu_action_view_event_log.triggered.connect( self._menu_action_teamserver_view_event_log );
        self.teamserver_menu.addAction( self.teamserver_menu_action_view_event_log );

        # Menu: "Operator". A collection of options for creating agents or viewing
        # collected data
        self.operator_menu = self.menuBar().addMenu( 'Operator' );

        # Menu: "Operator". Action: "Export Payload" Dialog: export_payloadDialog.ExportPayloadDialog
        self.operator_menu_action_export_payload = PyQt5.QtWidgets.QAction( 'Export Payload' );
        self.operator_menu_action_export_payload.triggered.connect( self._menu_action_operator_export_payload );
        self.operator_menu.addAction( self.operator_menu_action_export_payload );

        # create the startup event
        self.start_event = PyQt5.QtCore.QTimer();
        self.start_event.setSingleShot( True );
        self.start_event.setInterval( 0 );
        self.start_event.timeout.connect( self._start_event_cb );
        self.start_event.start()

    @qtinter.asyncslot
    async def _start_event_cb( self ):
        """
        Starts the connection to the specified teamserver host and port combo. On success
        the UI will initialize and display to the operator. If we are unable to establish
        a connection an error will be printed to the screen.
        """
        try:
            # start the connection to the specified host:port
            await self.rpc.start( self.teamserver_host, self.teamserver_port );
        except ConnectionRefusedError:
            # Print that we failed to connect
            self.log.error( f'Could not establish a connection to {self.teamserver_host}:{self.teamserver_port}' );
            # Abort! Raise that we are exiting
            raise SystemExit

        # Print that we got a connection!
        self.log.info( f'Successfully established a connection to {self.teamserver_host}:{self.teamserver_port}' );

        # open a teamserver tab to view the log as the first tab
        await self._menu_action_teamserver_view_event_log();

        # No error? Attempt to display the user interface
        self.show()

    @qtinter.asyncslot
    async def _menu_action_teamserver_view_event_log( self ):
        """
        Opens a tab to view the teamserver events
        """
        # Open the tab and display it to the user. Ensure only one is honestly open at a time.
        await self.tab_widget.tab_add( teamserver_event_log_tab.TeamserverEventLogTab( self ), f'Event Log', False );

    @qtinter.asyncslot
    async def _menu_action_operator_export_payload( self ):
        """
        Opens a dialog to export a configured payload to use on your assessments.
        """
        # Open the dialog and display it to the user!
        export_payload_dialog.ExportPayloadDialog( self ).show()

@click.command( no_args_is_help = True )
@click.argument( 'rpc-host', type = str, metavar = 'rpc-host' )
@click.argument( 'rpc-port', type = int, metavar = 'rpc-port' )
def ghost_main( rpc_host, rpc_port ):
    """
    A minimal command and control client.
    """
    # Start the qtinter asynchronous loop
    with qtinter.using_asyncio_from_qt():
        # Create the primary 'app' for QApplication and load the dark theme
        app = PyQt5.QtWidgets.QApplication( [] );
        app.setStyleSheet( qdarktheme.load_stylesheet() );

        # Set the Monaco font globally
        _font_id = PyQt5.QtGui.QFontDatabase.addApplicationFont( './rsrc/font/MonacoLinux.ttf' );
        _font_st = PyQt5.QtGui.QFontDatabase.applicationFontFamilies( _font_id )[0]
        _font_qt = PyQt5.QtGui.QFont( _font_st );
        app.setFont( _font_qt );

        # Create the 'ghost' application with the screen height / width to fill the full screen
        ghost = Ghost( app.primaryScreen().size().height(), app.primaryScreen().size().width(), rpc_host, rpc_port );

        # Start the application
        app.exec_();

if __name__ in '__main__':
    # call the click application
    ghost_main();

#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import PyQt5
import random
import qtinter
import asyncio

class TabWidget( PyQt5.QtWidgets.QWidget ):
    """
    A widget for handling the creation, removal, and retrivial of tabs.
    """

    def __init__( self, ghost ):
        # initialize the widget based on its parent
        super( PyQt5.QtWidgets.QWidget, self ).__init__( ghost );

        # set the ghost class object
        self.ghost = ghost

        # Lock for accessing the tab list
        self.tabs_list_lock = asyncio.Lock();

        # List of the valid tabs
        self.tabs_list = []

        # set the primary layout
        self.layout = PyQt5.QtWidgets.QVBoxLayout();

        # create the tab widget 
        self.tab_widget = PyQt5.QtWidgets.QTabWidget();
        self.tab_widget.setMovable( True );
        self.tab_widget.setTabsClosable( True );
        self.tab_widget.tabCloseRequested.connect( self.tab_del );

        # add the tab widget to the layout
        self.layout.addWidget( self.tab_widget );

        # set the layout for this widget
        self.setLayout( self.layout );

    @qtinter.asyncslot
    async def tab_del( self, tab_index ):
        """
        A callback that is executed by the tab widget whenever a user requests
        a tab to be deleted.
        """
        # Lock access to the list to prevent a race condition
        async with self.tabs_list_lock:
            # Ask the widget to delete itself shortly
            self.tab_widget.widget( tab_index ).deleteLater()

            # Remove the tab from the widget
            self.tab_widget.removeTab( tab_index );

            # Remove the tab from the list of valid tabs
            del self.tabs_list[ tab_index ]

            # Are we now out of 'tabs'
            if self.tab_widget.count() < 1:
                # Hide the user interface!
                self.hide()

    async def tab_add( self, tab_object, tab_name, tab_add_new ):
        """
        Creates a tab and returns the tab identifier so that it can be used in a callback. If
        tab_add_new is False it will locate the existing tab by the same name and return the
        identifier for it.
        """
        # Lock access to the list to prevent a race condition
        async with self.tabs_list_lock:
            # Look for an old tab if it exists in the list
            if not tab_add_new:
                # Loop through the list
                for tab_entry in self.tabs_list:
                    # Does the title exist already?
                    if tab_entry[ 'title' ] == tab_name:
                        # return ID if it does!
                        return tab_entry[ 'id' ]

            # generate a random identifier for the tab
            tab_uniq_id = random.getrandbits( 32 );

            # Append a entry to the list containing the ID, title, and corresponding object
            self.tabs_list.append( { 'id': tab_uniq_id, 'title': tab_name, 'object': tab_object } );

            # add the tab!
            self.tab_widget.addTab( tab_object, tab_name );

            # switch to this new index
            self.tab_widget.setCurrentIndex( self.tab_widget.count() - 1 );

            # are all the tabs closed so we are now hidden?
            if not self.tab_widget.isVisible(): 
                # Set to visible as we have a tab now!
                self.show()

            # return the identiifer
            return tab_uniq_id

    async def tab_get_id_from_object( self, tab_object ):
        """
        Locates the tab ID based the object. Intended to be used by tabs themselves
        to retrieve their ID's.
        """
        # Lock access to the list to prevent a race condition
        async with self.tabs_list_lock:
            # Loop through the list
            for tab_entry in self.tabs_list:
                # Does the entry exist?
                if tab_entry[ 'object' ] == tab_object:
                    # Return the ID
                    return tab_entry[ 'id' ]

        # Nothing is returned.
        return None

    async def tab_get_object_from_id( self, tab_id ):
        """
        Locates the tab object based on its ID if it exists. Inteded to be used by
        the RPC callbacks.
        """
        # Lock access to the list to prevent a race condition
        async with self.tabs_list_lock:
            # Loop through the list
            for tab_entry in self.tabs_list:
                # Does the entry exist?
                if tab_entry[ 'id' ] == tab_id:
                    # Return the object
                    return tab_entry[ 'object' ]

        # Nothing is returned.
        return None

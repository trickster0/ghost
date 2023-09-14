#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import PyQt5
import asyncio
import qtinter
import calendar
import ipaddress

class ExportPayloadDialog( PyQt5.QtWidgets.QDialog ):
    """
    A dialog for exporting a payload from the remote server.
    """
    def __init__( self, ghost ):
        # Initialize the primary class
        super( PyQt5.QtWidgets.QDialog, self ).__init__( ghost );

        # Set the primary ghost object
        self.ghost = ghost

        # set the window title
        self.setWindowTitle( 'Configure and Export Payload' );

        # Address for filling in the Ipv4 address
        self.ipv4_address = PyQt5.QtWidgets.QLineEdit();
        self.ipv4_address.setPlaceholderText( 'e.g. 192.168.x.x' );

        # ICMP Chunk S/R Sleep
        self.icmp_chunk_sleep = PyQt5.QtWidgets.QSpinBox();
        self.icmp_chunk_sleep.setRange( 100, 86400000 );
        self.icmp_chunk_sleep.setToolTip( 'Number of milliseconds to wait in between sending ICMP requests' );

        # ICMP Chunk S/R Jitter
        self.icmp_chunk_jitter = PyQt5.QtWidgets.QSpinBox();
        self.icmp_chunk_jitter.setRange( 0, 100 );
        self.icmp_chunk_jitter.setToolTip( 'Percentage of randomization for ICMP Chunk S/R Sleep' );

        # ICMP Chunk Max Length
        self.icmp_chunk_length = PyQt5.QtWidgets.QSpinBox();
        self.icmp_chunk_length.setRange( 17, 1400 );
        self.icmp_chunk_length.setToolTip( 'Maximum size that a S/R chunk can be for an request/response' );

        # ICMP Response Timeout
        self.icmp_chunk_timeout = PyQt5.QtWidgets.QSpinBox();
        self.icmp_chunk_timeout.setRange( 5000, 86400000 );
        self.icmp_chunk_timeout.setToolTip( 'Number of milliseconds to wait for a response from the server' );

        # Sleep
        self.sleep = PyQt5.QtWidgets.QSpinBox();
        self.sleep.setRange( 1000, 86400000 );
        self.sleep.setToolTip( 'Number of milliseconds to wait in between download requests from the server' );

        # Jitter
        self.jitter = PyQt5.QtWidgets.QSpinBox();
        self.jitter.setRange( 0, 100 );
        self.jitter.setToolTip( 'Percentage of randomization for Sleep' );

        # UTC Kill Date
        self.kill_date = PyQt5.QtWidgets.QDateTimeEdit();
        self.kill_date.setTimeSpec( PyQt5.QtCore.Qt.TimeSpec.UTC );
        self.kill_date.setCalendarPopup( True );
        self.kill_date.setToolTip( 'A date (mm/dd/yy h:m) in UTC format for when the agent won\'t callback past' );
        self.kill_date.setDateTime( PyQt5.QtCore.QDateTime.currentDateTime() );

        # Extra Option: x64
        self.ext_opt_x64 = PyQt5.QtWidgets.QCheckBox();
        self.ext_opt_x64.setText( 'x64' );
        self.ext_opt_x64.setChecked( True );

        # Button: "Generate"
        self.generate = PyQt5.QtWidgets.QPushButton( 'Generate' );
        self.generate.setEnabled( False );
        self.generate.clicked.connect( self._generate );

        # Create a layout in the format that the names are next
        # to the input boxes
        #
        # Like:
        #
        # Name | Input

        # Extra Options
        layout_option = PyQt5.QtWidgets.QHBoxLayout();
        layout_option.addWidget( self.ext_opt_x64 );

        # Labels
        layout_labels = PyQt5.QtWidgets.QVBoxLayout();
        layout_labels.addWidget( PyQt5.QtWidgets.QLabel( 'Ipv4 Address' ) )
        layout_labels.addWidget( PyQt5.QtWidgets.QLabel( 'ICMP Chunk S/R Sleep' ) );
        layout_labels.addWidget( PyQt5.QtWidgets.QLabel( 'ICMP Chunk S/R Jitter' ) );
        layout_labels.addWidget( PyQt5.QtWidgets.QLabel( 'ICMP Chunk Max Length' ) );
        layout_labels.addWidget( PyQt5.QtWidgets.QLabel( 'ICMP Response Timeout' ) );
        layout_labels.addWidget( PyQt5.QtWidgets.QLabel( 'Sleep' ) );
        layout_labels.addWidget( PyQt5.QtWidgets.QLabel( 'Jitter' ) );
        layout_labels.addWidget( PyQt5.QtWidgets.QLabel( 'UTC Kill Date' ) );
        layout_labels.addWidget( PyQt5.QtWidgets.QLabel( 'Extra Options' ) );
        layout_labels.setSpacing( 6 );

        # Inputs
        layout_inputs = PyQt5.QtWidgets.QVBoxLayout();
        layout_inputs.addWidget( self.ipv4_address );
        layout_inputs.addWidget( self.icmp_chunk_sleep );
        layout_inputs.addWidget( self.icmp_chunk_jitter );
        layout_inputs.addWidget( self.icmp_chunk_length );
        layout_inputs.addWidget( self.icmp_chunk_timeout );
        layout_inputs.addWidget( self.sleep );
        layout_inputs.addWidget( self.jitter );
        layout_inputs.addWidget( self.kill_date );
        layout_inputs.addLayout( layout_option );
        layout_inputs.setSpacing( 6 );

        # Inputs + Labels
        layout_labels_inputs = PyQt5.QtWidgets.QHBoxLayout();
        layout_labels_inputs.addLayout( layout_labels );
        layout_labels_inputs.addLayout( layout_inputs );

        # Spacer + Button
        layout_spacer_button = PyQt5.QtWidgets.QHBoxLayout();
        layout_spacer_button.addItem( PyQt5.QtWidgets.QSpacerItem( 40, 20, PyQt5.QtWidgets.QSizePolicy.Expanding, PyQt5.QtWidgets.QSizePolicy.Minimum ) );
        layout_spacer_button.addWidget( self.generate );

        # Inputs/Labels + Spacer/Button
        layout_button_ilabel = PyQt5.QtWidgets.QVBoxLayout();
        layout_button_ilabel.addLayout( layout_labels_inputs );
        layout_button_ilabel.addLayout( layout_spacer_button );

        # Lock for monitoring the input
        self.monitor_input_lock = asyncio.Lock();

        # Create a background timer that continually checks the input
        self.timer_monitor_input = PyQt5.QtCore.QTimer()
        self.timer_monitor_input.setInterval( 100 );
        self.timer_monitor_input.timeout.connect( self._monitor_input );
        self.timer_monitor_input.start()

        # Resize the dialog to a nice fit!
        self.setFixedSize( 700, 0 );

        # Set the layout
        self.setLayout( layout_button_ilabel );

        # Set that we delete on close
        self.setAttribute( PyQt5.QtCore.Qt.WA_DeleteOnClose );

    @qtinter.asyncslot
    async def _monitor_input( self ):
        """
        Validates the input and enables payload generation on success
        """
        async with self.monitor_input_lock:
            # Is there no input available for the Ipv4 address?
            try:
                # Is there an IPv4 address and is this a valid IPv4 adress?
                ipaddress.ip_address( self.ipv4_address.text() );
            
                # It is enabled!
                self.generate.setEnabled( True );
            except ValueError:
                # It is no longer enabled as it did not meet the filter!
                self.generate.setEnabled( False );

                # Failed this check so we return!
                return

    @qtinter.asyncslot
    async def _generate( self ):
        """
        Generates a payload with the requested option and closes the dialog
        """
        # Close the dialog
        self.close()

        # generate a payload with the requested options
        shellcode = await self.ghost.rpc.teamserver_export_payload( self.ipv4_address.text(), self.icmp_chunk_sleep.value(), self.icmp_chunk_jitter.value(), self.icmp_chunk_length.value(), self.icmp_chunk_timeout.value(),
                                                                    self.sleep.value(), self.jitter.value(), calendar.timegm( self.kill_date.dateTime().toPyDateTime().timetuple() ), self.ext_opt_x64.isChecked() );

        # Did we get a shellcode response? This means that we can now save it!
        if shellcode:
            # Open a dialog to request a specific path we want to target
            path_to_file, _ = PyQt5.QtWidgets.QFileDialog.getSaveFileName( self.ghost, "Save Payload", "", "Binary Files (*.bin)", options = PyQt5.QtWidgets.QFileDialog.Options() | PyQt5.QtWidgets.QFileDialog.DontUseNativeDialog );

            # Open the target path!
            if path_to_file: 
                with open( path_to_file, 'wb+' ) as file:
                    # Write the shellcode to the path!
                    file.write( shellcode );
        else:
            # Open an error box notifying the client to check the agent
            qtinter.modal( PyQt5.QtWidgets.QMessageBox.critical( self.ghost, 'Export Payload Error', 'Failed to export a payload. See teamserver console for more details.' ) );

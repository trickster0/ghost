import sys
import logging
import colorama

class LogFormatter( logging.Formatter ):
    """
    Formats a logging output.
    """
    def __init__( self ):
        logging.Formatter.__init__( self, '%(bullet)s %(message)s', None );

    def format( self, record ):
        if record.levelno == logging.INFO:
            record.bullet = f'[{colorama.Fore.BLUE}*{colorama.Style.RESET_ALL}]'
        elif record.levelno == logging.DEBUG:
            record.bullet = f'[{colorama.Fore.LIGHTBLUE_EX}?{colorama.Style.RESET_ALL}]'
        elif record.levelno == logging.WARNING:
            record.bullet = f'[{colorama.Fore.YELLOW}!{colorama.Style.RESET_ALL}]'
        else:
            record.bullet = f'[{colorama.Fore.RED}-{colorama.Style.RESET_ALL}]'

        # parse the incoming record!
        return logging.Formatter.format( self, record );

class LogFormatterTimeStamp( LogFormatter ):
    """
    Formats a logging output with a timestamp
    """
    def __init__( self ):
        logging.Formatter.__init__( self, '[%(asctime)-15s] %(bullet)s %(message)s', None )

    def formatTime( self, record, datefmt = None ):
        return LogFormatter.formatTime( self, record, datefmt = "%Y-%m-%d %H:%M:%S" )

def init( debug ):
    # Create a handler for the specified stream
    handler = logging.StreamHandler();

    if not debug:
        # No debugging? Then we just want print statements
        handler.setFormatter( LogFormatter() );
    else:
        # Debugging! We also want the fancy log tracing
        handler.setFormatter( LogFormatterTimeStamp() );

    # Create the logger and add a handler for it
    logging.getLogger( 'ghost' ).addHandler( handler );

    if not debug:
        # We only want generic information returned
        logging.getLogger( 'ghost' ).setLevel( logging.INFO );
    else:
        # We want debugging information returned
        logging.getLogger( 'ghost' ).setLevel( logging.DEBUG );

    # return the logger object
    return logging.getLogger( 'ghost' );

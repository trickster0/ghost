from struct import pack
from struct import unpack

class Parser:
    def __init__( self, buffer ):
        self.buffer : bytes = buffer

    def get_stringw( self ):
        siz = unpack( '<I', self.buffer[ : 4 ] )[0]
        buf = self.buffer[ 4 : 4 + siz ][:-2]

        self.buffer = self.buffer[ 4 + siz : ]

        return buf.decode( 'utf-16-le' )

    def get_string( self ):
        siz = unpack( '<I', self.buffer[ : 4 ] )[0]
        buf = self.buffer[ 4 : 4 + siz ][:-1]

        self.buffer = self.buffer[ 4 + siz : ]

        return buf.decode( 'utf-8' )

    def get_buffer( self ):
        siz = unpack( '<I', self.buffer[ : 4 ] )[0]
        buf = self.buffer[ 4 : 4 + siz ]

        self.buffer = self.buffer[ 4 + siz : ]

        return buf

    def get_int64( self ):
        lnn = unpack( '<Q', self.buffer[ : 8 ] )[0]

        self.buffer = self.buffer[ 8 : ]

        return lnn

    def get_int32( self ):
        lnn = unpack( '<I', self.buffer[ : 4 ] )[0]

        self.buffer = self.buffer[ 4 : ]

        return lnn

    def get_int16( self ):
        lnn = unpack( '<H', self.buffer[ : 2 ] )[0]

        self.buffer = self.buffer[ 2 : ]

        return lnn

    def get_int8( self ):
        lnn = unpack( '<B', self.buffer[ : 1 ] )[0]

        self.buffer = self.buffer[ 1 : ]

        return lnn

    def get_size_left( self ):
        return len( self.buffer )

    def get_buff_left( self ):
        return self.buffer

class Packer:
    def __init__( self ):
        self.buffer : bytes = b''

    def get_packed( self ):
        return self.buffer

    def add_stringw( self, string ):
        buf  = pack( '<I', len( string.encode( 'utf-16-le' ) ) + 2 )
        buf += string.encode( 'utf-16-le' )
        buf += b'\x00\x00'

        self.buffer = self.buffer + buf

    def add_string( self, string ):
        buf  = pack( '<I', len( string ) + 1 )
        buf += string.encode( 'utf-8' )
        buf += b'\x00'

        self.buffer = self.buffer + buf

    def add_buffer( self, buffer ):
        buf  = pack( '<I', len( buffer ) );
        buf += buffer

        self.buffer = self.buffer + buf

    def add_int64( self, integer ):
        buf = pack( '<Q', integer );

        self.buffer = self.buffer + buf

    def add_int32( self, integer ):
        buf = pack( '<I', integer )

        self.buffer = self.buffer + buf

    def add_int16( self, integer ):
        buf = pack( '<H', integer )

        self.buffer = self.buffer + buf

    def add_int8( self, integer ):
        buf = pack( '<B', integer )

        self.buffer = self.buffer + buf

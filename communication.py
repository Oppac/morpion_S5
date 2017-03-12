from enum import Enum

class status(Enum):
    unknown = 0
    player1 = 1
    player2 = 2
    identified = 3
    logged_in = 4
    spectator_waiting = 5
    spectator = 6

class gameStatus(Enum):
    victory = 0
    defeat = 1
    draw = 2


class message:
    def separate( rawBytes):
        msgList = []
        tmp = rawBytes.decode().split(";")
        for msg in tmp:
            if msg != "":
                msgList.append(bytes(msg, 'utf-8')) 
        return msgList
    def head(msg):
        return bytes(msg.decode().split(':')[0], 'utf-8')
    def body(msg):
        return msg.decode().split(':')[1].split(',')

    
    def init( ):
        return bytes("init" + ":" + ";", 'utf-8')
    def is_init( msg ):
        return message.head(msg) == b"init"
    def login_request( pseudo="" ):
        return bytes("login" + ":" + pseudo + ";", 'utf-8')
    def is_login_request( msg ):
        return message.head(msg) == b"login"
    def validate_login():
        return bytes("validateLogin" + ":" + ";", 'utf-8')
    def is_validate_login(msg):
        return message.head(msg) == b"validateLogin"
    def start_game(otherPlayer=""):
        return bytes("sgame" + ":" + otherPlayer + ";", 'utf-8')
    def is_start_game(msg):
        return message.head(msg) == b"sgame"
    def play_bot():
        return bytes("playBot" + ":" + ";", 'utf-8')
    def is_play_bot(msg):
        return message.head(msg) == b"playBot"
    def spect():
        return bytes("spect" + ":" + ";", 'utf-8')
    def is_spect(msg):
        return message.head(msg) == b"spect"
    def set_player( player ):
        return bytes("splayer" + ":" + str(player) + ";", 'utf-8')
    def is_set_player(msg):
        return message.head(msg) == b"splayer"
    def nb_spect(nb):
        return bytes("nbspect" + ":" + str(nb) + ";", 'utf-8')
    def is_nb_spect(msg):
        return message.head(msg) == b"nbspect"

    def play( cell = -1):
        return bytes("play" + ":" + str(cell) + ";", 'utf-8')
    def is_play(msg):
        return message.head(msg) == b"play"
    def valid_move( cell):
        return bytes("valid_move" + ":" + str(cell) + ";", 'utf-8')
    def is_valid_move(msg):
        return message.head(msg) == b"valid_move"
    def occupied( cell, player):
        return bytes("occupied" + ":" + str(cell) + ',' + str(player) + ";", 'utf-8')
    def is_occupied(msg):
        return message.head(msg) == b"occupied"
    def game_status( status ):
        return bytes("gameStatus" + ":" + str(status) + ";", 'utf-8')
    def is_game_status(msg):
        return message.head(msg) == b"gameStatus"
    def stats( nbVictory, nbDefeat, nbDraw ):
        return bytes("stats" + ":" + str(nbVictory) + ',' + str(nbDefeat) + "," + str(nbDraw) + ';', 'utf-8')
    def is_stats( m ):
        return message.head(m) == b"stats"
    def map_info( mapInfo ):
        msg = "mapInfo" + ":" + str(mapInfo[0])
        for cell in mapInfo[1:]:
            msg += ',' + str(cell)
        msg += ';'
        return bytes(msg, 'utf-8')
    def is_map_info( m ):
        return message.head(m) == b"mapInfo"

    def players_info( p1, p2 ):
        return bytes("pinfo" + ":" + p1 + ',' + p2 + ";", 'utf-8')
    def is_players_info ( m ):
        return message.head(m) == b"pinfo"

    def msg( m ):
        return bytes("message" + ":" + m + ";", 'utf-8')
    def is_msg( m ):
        return message.head(m) == b"message"
    def ping():
        return bytes("ping" + ";", 'utf-8')
    def is_ping( m ):
        return message.head(m) == b"ping"
    def kick( m ):
        return bytes("kick" + ":" + m + ";", 'utf-8')
    def is_kick(msg):
        return message.head(msg) == b"kick"

import socket
import select
import time
from communication import *
from grid import *
import  random

class Client:
    def __init__(self, connexion):
        self.ip = connexion.getsockname()[0]
        self.connexion = connexion
        self.pseudo = "unknown"
        self.status = status.unknown
        self.stats = {}
        self.lastAnswer = time.time()
        self.lastPing = None
        
    def toString(self):
        if self.pseudo == "unknown":
            return self.ip + ':' + "(" + self.status.name + ")"
        else:
            return self.ip + ':' + "(" + self.pseudo + " " + self.status.name + ")"

class Server:
    def __init__(self, host = '', port=50500):
        self.main_connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_connexion.bind((host, port))
        self.main_connexion.listen(5)
        
        self.connexions = []
        self.spectators = []
        self.clients = {}
        self.timeOut = 60.0
        self.timerResetGameP1 = None
        self.timerResetGameP2 = None
        
        self.p1 = None
        self.p2 = None
        self.current_player = None

        self.grids = [grid(), grid(), grid()]
        self.name = "SERVINATORR"

        print("New server created {}:{}".format(socket.gethostbyname(socket.gethostname()), port))

    def start(self):
        server_on = True
        while server_on:
            #Welcoming new clients
            new_connexions, wlist, xlist = select.select([self.main_connexion],[], [], 0.05)
            for newConnexion in new_connexions:
                connexion, infos_connexion = newConnexion.accept()

                
                ip = connexion.getsockname()[0]    
                if not self.isConnected(ip):
                    self.connexions.append(connexion)
                    if not ip in self.clients:
                        self.clients[ip] = Client(connexion)
                    else:
                        self.clients[ip].connexion = connexion
                    print("Client connected : {}".format(self.clients[ip].toString()))

            #Processing messages
            active_connexions = []
            try:
                active_connexions, wlist, xlist = select.select(self.connexions,[], [], 0.05)
            except select.error:
                pass
            else:
                for connexion in active_connexions:
                    rawBytes = self.safeRecv(connexion)
                    if(rawBytes != b""):
                        ip = connexion.getsockname()[0]
                        for msg in message.separate(rawBytes):
                            self.process_msg(msg, self.clients[ip])

            t = time.time()       
            #Check for inactive connexions
            for connexion in self.connexions:
                client = self.clients[connexion.getsockname()[0]]
                if t - client.lastAnswer > self.timeOut:
                    if client.lastPing == None:
                        self.safeSend(connexion, message.ping())
                        client.lastPing = t
                    elif t - client.lastPing > self.timeOut:
                        self.disconnect(connexion, "TimeOut")
            #Game reset
            if self.timerResetGameP1 != None and t - self.timerResetGameP1 > 20:
                self.resetGame()
            if self.timerResetGameP2 != None and t - self.timerResetGameP2 > 20:
                self.resetGame()

    def process_msg( self, msg, client):
        #Timeout/Ping check
        if message.is_ping(msg) :
            client.lastAnswer = time.time()
            client.lastPing = None
        #Messages
        elif message.is_msg(msg):
            for connexion in self.connexions:
                self.safeSend(connexion, msg)
        #First Log in
        elif client.status == status.unknown or message.is_login_request(msg):
            if message.is_login_request(msg) : 
                client.pseudo = message.body(msg)[0]
                client.status = status.logged_in
                self.safeSend(client.connexion, message.validate_login())
            else:
                self.safeSend(client.connexion, message.login_request())
        #Already known but not logged in
        elif client.status == status.identified and message.is_init(msg):
            #Reconnexion
            if client == self.p1:
                self.timerResetGameP1 = None
                client.status = status.player1
                self.safeSend(self.p1.connexion, message.set_player(client.status.value))
                self.safeSend(self.p1.connexion, message.start_game(self.name))
                self.safeSend(client.connexion, message.map_info(self.grids[1].cells))
                if self.p2 != self.name:
                    s1 = self.p1.stats[self.p2.ip]
                else:
                    s1 = self.p1.stats[self.name]
                self.safeSend(self.p1.connexion, message.stats(s1[0], s1[1], s1[2]))
                if self.current_player == self.p1:
                    self.safeSend(self.p1.connexion, message.play())
            elif client == self.p2:
                self.timerResetGameP2 = None
                client.status = status.player2
                self.safeSend(self.p2.connexion, message.set_player(client.status.value))
                self.safeSend(self.p2.connexion, message.start_game(self.name))
                self.safeSend(client.connexion, message.map_info(self.grids[2].cells))
                if self.p1 != self.name:
                    s2 = self.p2.stats[self.p1.ip]
                else:
                    s2 = self.p2.stats[self.name]
                self.safeSend(self.p2.connexion, message.stats(s2[0], s2[1], s2[2]))
                if self.current_player == self.p2:
                    self.safeSend(self.p2.connexion, message.play())
            else:
                client.status = status.logged_in
                self.safeSend(client.connexion, message.validate_login())
        #Already logged in
        elif client.status == status.logged_in:
            #Client wanna spect
            if message.is_spect(msg) :
                client.status = status.spectator_waiting
                self.safeSend(client.connexion, message.set_player(status.spectator.value))
                self.spectators.append(client)
                for spect in self.spectators:
                    self.safeSend(spect.connexion, message.nb_spect(len(self.spectators)))
                
                if self.p1 != None:
                    self.safeSend(self.p1.connexion, message.nb_spect(len(self.spectators)))
                if self.p2 != None:
                    if self.p2 != self.name:
                        self.safeSend(self.p2.connexion, message.nb_spect(len(self.spectators)))
                    client.status = status.spectator
                    self.safeSend(client.connexion, message.players_info(self.p1.pseudo, self.p2))
                    self.safeSend(client.connexion, message.map_info(self.grids[0].cells))
            #Client wanna play Bot
            if message.is_play_bot(msg) :
                if self.p1 == None:
                    #Launch the game
                    self.p1 = client
                    self.p2 = self.name
                    self.current_player = client
                    client.status = status.player1
                    self.safeSend(self.p1.connexion, message.set_player(client.status.value))
                    self.safeSend(self.p1.connexion, message.nb_spect(len(self.spectators)))
                    self.safeSend(self.p1.connexion, message.start_game(self.name))
                    if not self.name in self.p1.stats:
                        self.p1.stats[self.name] = [0,0,0]
                    s1 = self.p1.stats[self.name]
                    self.safeSend(self.p1.connexion, message.stats(s1[0], s1[1], s1[2]))
                    self.safeSend(self.p1.connexion, message.play())
                    #inform spectators
                    for spect in self.spectators:
                        if spect.status == status.spectator_waiting:
                            self.safeSend(spect.connexion, message.players_info(self.p1.pseudo, self.p2))
                            self.safeSend(spect.connexion, message.map_info(self.grids[0].cells))
                            spect.status = status.spectator
                else:
                    self.safeSend(client.connexion, message.msg("Game already booked"))
            #Client wanna start
            elif message.is_start_game(msg) :
                if self.p1 == None:
                    self.p1 = client
                    self.current_player = client
                    client.status = status.player1
                    self.safeSend(client.connexion, message.set_player(client.status.value))
                    self.safeSend(self.p1.connexion, message.nb_spect(len(self.spectators)))
                elif self.p2 == None:
                    self.p2 = client
                    client.status = status.player2
                    self.safeSend(client.connexion, message.set_player(client.status.value))
                    self.safeSend(self.p1.connexion, message.nb_spect(len(self.spectators)))
                #Start the game if the player 2 is set
                if client.status == status.player2 :
                    #Pseudo exchange
                    self.safeSend(self.p1.connexion, message.start_game(self.p2.pseudo))
                    self.safeSend(self.p2.connexion, message.start_game(self.p1.pseudo))
                    #Setup the stats
                    if not self.p1.ip in self.p2.stats:
                        self.p2.stats[self.p1.ip] = [0,0,0]
                    if not self.p2.ip in self.p1.stats:
                        self.p1.stats[self.p2.ip] = [0,0,0]
                    s1 = self.p1.stats[self.p2.ip]
                    self.safeSend(self.p1.connexion, message.stats(s1[0], s1[1], s1[2]))
                    s2 = self.p2.stats[self.p1.ip]
                    self.safeSend(self.p2.connexion, message.stats(s2[0], s2[1], s2[2]))
                    #launch the game
                    print("Game stated.")
                    self.safeSend(self.current_player.connexion, message.play())
                    #inform spectators
                    for spect in self.spectators:
                        if spect.status == status.spectator_waiting:
                            spect.status = status.spectator
                            self.safeSend(spect.connexion, message.map_info(self.grids[0].cells))
                            self.safeSend(spect.connexion, message.players_info(self.p1.pseudo, self.p2.pseudo))
        #If the client is a player
        elif client.status == status.player1 or client.status == status.player2:
            #If the current player choose a cell
            if message.is_play(msg) and self.current_player == client:
                shot = int(message.body(msg)[0])
                id_player = self.current_player.status.value
                #If the cell is already occupied
                if (self.grids[0].cells[shot] != EMPTY):
                    self.grids[id_player].cells[shot] = self.grids[0].cells[shot]
                    self.safeSend(self.current_player.connexion, message.occupied(shot, self.grids[0].cells[shot]))
                    self.safeSend(self.current_player.connexion, message.play())
                #If the cell is empty
                else:
                    self.grids[id_player].cells[shot] = id_player
                    self.grids[0].cells[shot] = id_player
                    self.safeSend(self.current_player.connexion, message.valid_move(shot))
                    
                    for spect in self.spectators:
                        print( spect.toString())
                        self.safeSend(spect.connexion, message.map_info(self.grids[0].cells))

                    #Setup for next turn
                    next_player = None
                    if self.current_player == self.p1:
                        next_player = self.p2
                    else:
                        next_player = self.p1

                    self.testGameOver(next_player)

                    if self.current_player == self.name:
                        shot = random.randint(0,8)
                        while self.grids[0].cells[shot] != EMPTY:
                            shot = random.randint(0,8)
                        self.grids[0].cells[shot] = J2
                        for spect in self.spectators:
                            self.safeSend(spect.connexion, message.map_info(self.grids[0].cells))
                        print("{} played in cell {}".format(self.name, shot))
                        next_player = self.p1
                        self.testGameOver(next_player)
                        
                        

            else:
                print("Invalid message {}".format(msg))

    def testGameOver( self, next_player ):
        #If not gameover
        if self.grids[0].gameOver() == -1:
            if next_player != self.name:
                self.safeSend(next_player.connexion, message.play())
            self.current_player = next_player
        #if Gameover
        else:

            #Draw 
            if self.grids[0].gameOver() == 0:
                if self.current_player != self.name:
                    self.safeSend(self.current_player.connexion, message.game_status(gameStatus.draw.value))
                    if next_player != self.name:
                        self.current_player.stats[next_player.ip][2] += 1
                    else:
                        self.current_player.stats[self.name][2] += 1
                if next_player != self.name:
                    self.safeSend(next_player.connexion, message.game_status(gameStatus.draw.value))
                    if self.current_player != self.name:
                        next_player.stats[self.current_player.ip][2] += 1
                    else:
                        next_player.stats[self.name][2] += 1

                    
            #Victory
            else:
                #Send notifications
                if self.current_player != self.name:
                    self.safeSend(self.current_player.connexion, message.game_status(gameStatus.victory.value))
                    if next_player != self.name:
                        self.current_player.stats[next_player.ip][0] += 1
                    else:
                        self.current_player.stats[self.name][0] += 1
                        
                if next_player != self.name:
                    self.safeSend(next_player.connexion, message.game_status(gameStatus.defeat.value))
                    if self.current_player != self.name:
                        next_player.stats[self.current_player.ip][1] += 1
                    else:
                        next_player.stats[self.name][1] += 1
            self.resetGame()

    def resetGame(self):
        print("Game reset. Waiting for new players")
        if self.p1 != None:
            if self.isConnected(self.p1.ip):
                self.p1.status = status.logged_in
                self.safeSend(self.p1.connexion, message.set_player(self.p1.status.value))
            else:
                self.p1.status = status.identified
        if self.p2 != None and self.p2 != self.name:
            if self.isConnected(self.p2.ip):
                self.p2.status = status.logged_in
                self.safeSend(self.p2.connexion, message.set_player(self.p2.status.value))
            else:
                self.p2.status = status.identified
        self.p1 = None
        self.p2 = None
        for spect in self.spectators:
            spect.status = status.logged_in
            self.safeSend(spect.connexion, message.msg("Game reset"))
            self.safeSend(spect.connexion, message.set_player(spect.status.value))
        self.spectators = []
        
        self.grids = [grid(), grid(), grid()]
        self.current_player = None
        self.timerResetGameP1 = None
        self.timerResetGameP2 = None
        

    def safeRecv(self, connexion):
        try:
            msg = connexion.recv(1024)
        except ConnectionResetError:
            self.disconnect(connexion, "sr::ConnectionReset")
            return b""
        except ConnectionAbortedError:
            self.disconnect(connexion, "sr::ConnectionAborted")
            return b""
        if msg != b'':
            ip = connexion.getsockname()[0]
            client = self.clients[ip]
            client.lastAnswer = time.time()
            client.lastPing = None
            print( "From {}: {}".format(client.toString(), msg))
            return msg
        else:
            self.disconnect(connexion, "sr::ClientDisconnected")
            return b""

    def isConnected(self, ip):
        for c in self.connexions:
            if c.getsockname()[0] == ip:
                return True
        return False

    def safeSend(self, connexion, msg):
        if connexion.fileno() == -1:
            pass
        else:
            try:
                connexion.send(msg)
            except ConnectionResetError:
                self.disconnect(connexion, "ss::ConnectionReset")
            except ConnectionAbortedError:
                self.disconnect(connexion, "ss::ConnectionAborted")
            else:
                ip = connexion.getsockname()[0]
                client = self.clients[ip]
                print( "To   {}: {}".format(client.toString(), msg))

    def disconnect ( self, connexion, reason="" ):
        ip = connexion.getsockname()[0]
        client = self.clients[ip]
        print("Client disconnected {} : {}".format(client.toString(), reason))
        if client.status == status.spectator or client.status == status.spectator_waiting:
            print(len(self.spectators))
            self.spectators.remove(client)
            print(len(self.spectators))
            for spect in self.spectators:
                self.safeSend(spect.connexion, message.nb_spect(len(self.spectators)))
            if self.p1 != None:
                self.safeSend(self.p1.connexion, message.nb_spect(len(self.spectators)))
            if self.p2 != None and self.p2 !=  self.name:
                self.safeSend(self.p2.connexion, message.nb_spect(len(self.spectators)))
                
        if client.status != status.unknown :
            client.status = status.identified
        self.connexions.remove(connexion)
        connexion.close()
        #If the client was playing
        if client == self.p1:
            self.timerResetGameP1 = time.time()
        if client == self.p2:
            self.timerResetGameP1 = time.time()

        
s = Server()
s.start()




























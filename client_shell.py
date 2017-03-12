import socket
import sys
from communication import *
from grid import *
from threading import Thread

class client_game(Thread):
    #def __init__(self, host = "localhost", port=50500):
    def __init__(self, host = "192.168.1.15", port=50500):
        Thread.__init__(self)
        self.main_connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print("Connecting...")
            self.main_connexion.connect((host, port))
        except ConnectionRefusedError:
            print("Error: Connection refused.")
        except TimeoutError:
            print("Error: Timout.\n")
        except:
            print("Error: Connexion impossible.\n")
        else:
            print("Connexion set with {}:{}.".format(host,port))
        self.main_connexion.settimeout(0.1)

        self.grid = grid()
        
        self.login = []
        self.cell = []
        self.otherGame = []
        self.chooseRole = []


    def run(self):
        try :
            self.main_connexion.send( message.init() )
            client_on = True
            while(client_on):
                #If the player entered a login
                if len(self.login) > 0:
                    self.main_connexion.send(self.login[0])
                    self.login = []
                    
                #If the player choosed a cell
                if len(self.cell) > 0:
                    self.main_connexion.send(self.cell[0])
                    self.cell = []

                #if the player plays another game
                if len(self.otherGame) > 0:
                    if self.otherGame[0]:
                        self.grid = grid()
                        Thread(target=self.choose_role, args=(self.chooseRole,)).start()
                    else:
                        client_on = False
                    self.otherGame = []

                #If the client decided to play or observe
                if len(self.chooseRole) > 0:
                    if self.chooseRole[0] == "spect" :
                        self.main_connexion.send(message.spect())
                    elif self.chooseRole[0] == "pbot" :
                        self.main_connexion.send(message.play_bot())
                    elif self.chooseRole[0] == "play" :
                        self.main_connexion.send(message.start_game())
                    else:
                        client_on = False
                    self.chooseRole = []

                #Handle the communication with the server  
                try :
                    for answer in message.separate(self.main_connexion.recv(1024)):
                        if message.is_login_request(answer):
                            Thread(target=self.get_login, args=(self.login,)).start()
                            
                        elif message.is_msg(answer):
                            print("Message received: {}".format(message.body(answer)[0]))

                        elif message.is_validate_login(answer):
                            print("Logged in !")
                            self.otherGame.append(True)

                        elif message.is_set_player(answer):
                            role = status(int(message.body(answer)[0]))
                            if role == status.spectator:
                                print("You are now spectator. Waiting an the games to start.")
                            elif role == status.logged_in:
                                self.otherGame.append(True)
                            else:
                                print("You are now {}.\nWaiting an opponent.".format(role.name))
                                
                        #Display the game scores
                        elif message.is_stats(answer):
                            stats = message.body(answer)
                            print("Present statistics :")
                            print("Victories : {}".format(stats[0]))
                            print("Defeats :   {}".format(stats[1]))
                            print("Draws :     {}".format(stats[2]))

                        #If the user is kicked
                        elif message.is_kick(answer):
                            print("You got kicked : {}".format(message.body(answer)[0]))
                            client_on = False
                   
                        #If the game start, display the grid
                        elif message.is_start_game(answer):
                            print("You play  against {}. Good luck !".format(message.body(answer)[0]))
                            print("Game started. Please wait for your turn.")
                        
                        elif message.is_play(answer):
                            Thread(target=self.get_move, args=(self.cell,)).start()

                        #If the move is valid, update the grid with the user symbol
                        elif message.is_valid_move(answer):
                            shot = int(message.body(answer)[0])
                            self.grid.cells[shot] = J1
                            self.grid.display()
                            print("Waiting for player 2...")

                        #If the cell is occuping, update the grid with opponant symbol
                        elif message.is_occupied(answer):
                            shot = int(message.body(answer)[0])
                            self.grid.cells[shot] = int(message.body(answer)[1])
                            self.grid.display()
                            print("Cell already occupied !")

                        #If the user is a spectator
                        elif message.is_spect(answer) :
                            print("You are now spectator")

                        elif message.is_nb_spect(answer) :
                            print("There are {} spectators".format(message.body(answer)[0]))

                        #Inform the user if he won, lost or tied
                        elif( message.is_game_status(answer) ):
                            game_status = gameStatus(int(message.body(answer)[0]))
                            if game_status == gameStatus.victory:
                                print("Victory ! :D")
                            elif game_status == gameStatus.defeat:
                                print("Defeat ! :'(")
                            else:
                                print("Draw :/")

                        #Handle the server pings
                        elif message.is_ping(answer) :
                            self.main_connexion.send( message.ping() )

                        #Handle a new game
                        elif message.is_map_info(answer) :
                            newGrid = []
                            for cell in message.body(answer):
                                newGrid.append(int(cell))
                            self.grid.cells = newGrid
                            self.grid.display()
                        elif message.is_players_info(answer) :
                            print("Game started  !")
                            print("{} VS {}".format(message.body(answer)[0], message.body(answer)[1])) 
                        else:
                            print("server: {}".format(answer))
                except socket.timeout:
                    pass
                    
                    
            self.main_connexion.close()
            print("See you !")
            print("client exited.")
        except ConnectionResetError:
            print("Connection reset by server, exiting.")


    #Get the user login and send it to the server
    def get_login(self, login):
        nick = ""
        while len(nick) <= 0:
            nick = str(input("Nickname ? ")) 
        login.append(message.login_request(nick))


    #Get the user move and send it to the server
    def get_move(self, cell):
        shot = -1
        while shot < 0 or shot >= NB_CELLS:
            try:
                shot = int(input ("Choose a cell :"))
            except:
                pass
        cell.append(message.play(shot))


    #Ask the player if he want to play again
    def another_game(self, otherGame):
        answer = ""
        while answer != 'y' and answer != 'n':
            try:
                answer = input ("Another game ? (y/n)")
            except:
                pass
        
        if answer == "y":
            otherGame.append(True)
        else:
            otherGame.append(False)


    #Display the game menu and ask the user to choose a game mode
    def choose_role(self, role):
        answer = ""
        while answer != '1' and answer != '2' and answer != '3' and answer != '4':
            try:
                answer = input ("What's next ? \n1-Play vs human\n2-Play vs server\n3-Spectate\n4-Exit")
            except:
                pass
        
        if answer == '1':
            role.append("play")
        elif answer == '2':
            role.append("pbot")
        elif answer == '3':
            role.append("spect")
        else:
            role.append("exit")
            
#Start the game
#client = client_game(sys.argv[1])
client = client_game()        
client.run()

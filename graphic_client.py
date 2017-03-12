#### PYTHON 3.5 ONLY####
import pygame, string, socket, sys
from communication import *

SCREEN_WIDTH = 850
SCREEN_HEIGHT = 600

NB_ROW = 3
NB_COL = 3

EMPTY = 0
J1 = 1
J2 = 2

NOTHING = -1
TIE = 0
WON = 1
LOST =  2

CELLS_WIDTH = 150
CELLS_HEIGHT = 150
THICKNESS = 3

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

host = sys.argv[1]
#host = "192.168.1.17"
port = 50500


class Game():
    
    def __init__(self):
        pygame.init()

        #Gameplay variables  
        self.status = status.unknown
        self.my_login = ""
        self.my_score = 0
        self.my_num = 0
        self.other_login = "..."
        self.is_spect = False
        self.other_score = 0
        self.scoreties = 0
        self.your_turn = False
        self.nb_spectators = 0
        self.game_on = False
        self.endgame = NOTHING

        #Initialize the connexion
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

        self.main_connexion.setblocking(0)

        #Initialize the window, buttons and grid
        window_size = [SCREEN_WIDTH, SCREEN_HEIGHT]
        self.screen = pygame.display.set_mode(window_size)
        self.screen.fill(WHITE)
        pygame.display.set_caption("Morpion Aveugle")

        self.grid = [[0 for x in range(NB_ROW)] for y in range(NB_COL)]
        
        self.button_replay = pygame.Rect([470, 170, 120, 30])
        self.button_stop = pygame.Rect([610, 170, 120, 30])
        self.button_robot = pygame.Rect([470, 210, 120, 30])
        self.button_spect = pygame.Rect([610, 210, 120, 30])

        #Login variables
        self.ask_login = True
        self.login_string = ""
        self.login_cpt = 0

        #Chat variables
        self.chat_msg1 = ""
        self.chat_msg2 = ""
        self.chat_msg3 = ""
        self.chat_msg4 = ""
        self.chat_msg5 = ""
        self.chat_perso = ""
        self.chat_cpt = 0

        self.clock = pygame.time.Clock()


    #Display the grid on the screen and a red/blue circle inside the cell if it's occupied
    def drawGrid(self):
        xCenter = (1//2 * CELLS_WIDTH)
        yCenter = (1//2 * CELLS_HEIGHT)
        for x in range(NB_ROW):
            for y in range(NB_COL):
                color = BLACK
                if self.grid[x][y] == J1:
                    pygame.draw.circle(self.screen, RED, [CELLS_WIDTH * y + CELLS_WIDTH // 2,
                                                          CELLS_HEIGHT * x + CELLS_HEIGHT // 2], 36) 
                elif self.grid[x][y] == J2:
                    pygame.draw.circle(self.screen, BLUE, [CELLS_WIDTH * y + CELLS_WIDTH // 2,
                                                           CELLS_HEIGHT * x + CELLS_HEIGHT // 2], 36)
                pygame.draw.rect(self.screen, color,
                                 [CELLS_WIDTH * y, CELLS_HEIGHT * x,
                                  CELLS_WIDTH, CELLS_HEIGHT], THICKNESS)
                
    
    #Make the grid empty
    def clean_grid(self):
        for x in range(NB_COL):
            for y in range(NB_COL):
                self.grid[x][y] = EMPTY


    #Update the chat to make the message "scroll"
    def update_chat(self, msg_perso):
        self.chat_msg5 = self.chat_msg4
        self.chat_msg4 = self.chat_msg3
        self.chat_msg3 = self.chat_msg2
        self.chat_msg2 = self.chat_msg1
        self.chat_msg1 = msg_perso


    #Draw the login screen
    def draw_login(self):
        #The rectangle wrapping the rules
        pygame.draw.rect(self.screen, BLACK, [10, 340, 810, 250], THICKNESS)

        #The rules in string
        game_description1 = "Regles : Jeu de morpion aveugle en reseau à 2 joueurs sur une grille 3x3." 
        game_description2 = "Chaque joueur à tour de rôle marque une case dans la grille " 
        game_description3 = "(le premier joueur utilise la marque X et le second la marque O ). " 
        game_description4 = "Le gagnant est le premier joueur qui arrive à aligner 3 de ses marques. " 
        game_description5 = "Si la grille est complètement remplie sans qu’il y ait 3 marques identiques alignées, " 
        game_description6 = "il y a match nul. Les joueurs ne voient pas les coups joués par l’adversaire. " 
        game_description7 = "Si un joueur essaie de marquer une case déjà marquée par l’adversaire, " 
        game_description8 = "le joueur est informé que cette case est prise et il doit marquer une autre case."

        #Define the font
        myfont32 = pygame.font.SysFont(None, 32)
        myfont28 = pygame.font.SysFont(None, 28)
        myfont92 = pygame.font.SysFont(None, 92)

        #Format the strings to be displayed
        display_morpion = myfont92.render("Morpion", 1, BLUE)
        display_aveugle = myfont92.render("Aveugle", 1, RED)
        display_login = myfont32.render("Login : " + self.login_string, 1, BLACK)
        
        display_rules1 = myfont28.render(game_description1, 1, BLACK)
        display_rules2 = myfont28.render(game_description2, 1, BLACK)
        display_rules3 = myfont28.render(game_description3, 1, BLACK)
        display_rules4 = myfont28.render(game_description4, 1, BLACK)
        display_rules5 = myfont28.render(game_description5, 1, BLACK)
        display_rules6 = myfont28.render(game_description6, 1, BLACK)
        display_rules7 = myfont28.render(game_description7, 1, BLACK)
        display_rules8 = myfont28.render(game_description8, 1, BLACK)

        #Draw the strings on the screen
        self.screen.blit(display_morpion, (210, 40))
        self.screen.blit(display_aveugle, (390, 100))
        self.screen.blit(display_login, (150, 250))
        
        self.screen.blit(display_rules1, (15, 350))
        self.screen.blit(display_rules2, (25, 380))
        self.screen.blit(display_rules3, (25, 410))
        self.screen.blit(display_rules4, (25, 440))
        self.screen.blit(display_rules5, (25, 470))
        self.screen.blit(display_rules6, (25, 500))
        self.screen.blit(display_rules7, (25, 530))
        self.screen.blit(display_rules8, (25, 560))


    #Draw the game screen
    def draw_HUD(self):
        #Draw the rectangle and buttons on the screen
        pygame.draw.rect(self.screen, BLACK, [0, 470, 450, 130], THICKNESS)
        pygame.draw.rect(self.screen, BLACK, [455, 270, 390, 300], THICKNESS)
        pygame.draw.rect(self.screen, BLACK, [460, 500, 380, 50], THICKNESS)
        pygame.draw.rect(self.screen, BLACK, self.button_replay, THICKNESS)
        pygame.draw.rect(self.screen, BLACK, self.button_stop, THICKNESS)
        pygame.draw.rect(self.screen, BLACK, self.button_robot, THICKNESS)
        pygame.draw.rect(self.screen, BLACK, self.button_spect, THICKNESS)

        #Define the font
        myfont32 = pygame.font.SysFont(None, 32)
        myfont64 = pygame.font.SysFont(None, 64)
        myfont74 = pygame.font.SysFont(None, 74)

        #Format the string to be displayed
        #Format the game names and score
        display_loginp1 = myfont32.render(self.my_login, 1, BLACK)
        display_loginp2 = myfont32.render(self.other_login, 1, BLACK)
        display_ties = myfont32.render("Nuls", 1, BLACK)
        display_spectators = myfont32.render("Spectateurs", 1, BLACK)
        display_scorep1 = myfont64.render(str(self.my_score), 1, BLACK)
        display_scorep2 = myfont64.render(str(self.other_score), 1, BLACK)
        display_scoreties = myfont64.render(str(self.scoreties), 1, BLACK)
        display_nbspectators = myfont64.render(str(self.nb_spectators), 1, BLACK)
        
        display_morpion = myfont74.render("Morpion", 1, BLUE)
        display_aveugle = myfont74.render("Aveugle", 1, RED)

        #Format the name of the buttons
        display_replay = myfont32.render("Jouer", 1, BLACK)
        display_stop_play = myfont32.render("Arreter", 1, BLACK)
        display_robot = myfont32.render("Robot", 1, BLACK)
        display_spect = myfont32.render("Observer", 1, BLACK)

        #Format the chat messages
        display_msg1 = myfont32.render(self.chat_msg1, 1, BLACK)
        display_msg2 = myfont32.render(self.chat_msg2, 1, BLACK)
        display_msg3 = myfont32.render(self.chat_msg3, 1, BLACK)
        display_msg4 = myfont32.render(self.chat_msg4, 1, BLACK)
        display_msg5 = myfont32.render(self.chat_msg5, 1, BLACK)
        display_msg_perso = myfont32.render(self.chat_perso, 1, BLACK)

        #Draw the strings on the string
        self.screen.blit(display_loginp1, (10, 520))
        self.screen.blit(display_scorep1, (30, 550))
        self.screen.blit(display_loginp2, (135, 520))
        self.screen.blit(display_scorep2, (155, 550))
        self.screen.blit(display_ties, (255, 520))
        self.screen.blit(display_scoreties, (265, 550))
        self.screen.blit(display_spectators, (315, 520))
        self.screen.blit(display_nbspectators, (355, 550))
        
        self.screen.blit(display_morpion, (470, 30))
        self.screen.blit(display_aveugle, (610, 75))
        
        self.screen.blit(display_replay, (475, 175))
        self.screen.blit(display_stop_play, (615, 175))
        self.screen.blit(display_robot, (475, 215))
        self.screen.blit(display_spect, (615, 215))
        
        self.screen.blit(display_msg5, (460, 290))
        self.screen.blit(display_msg4, (460, 330))
        self.screen.blit(display_msg3, (460, 370))
        self.screen.blit(display_msg2, (460, 410))
        self.screen.blit(display_msg1, (460, 450))
        self.screen.blit(display_msg_perso, (465, 515))

        #Draw a message to inform the player if it's turn or not
        if self.game_on == True:
            if self.your_turn == True:
                label = myfont32.render("C'est ton tour !", 1, BLACK)
            else:
                label = myfont32.render("En attente de l'autre joueur ...", 1, BLACK)
        else:
            label = myfont32.render("En attente d'un opposant", 1, BLACK)

        #Endgame messages
        if self.endgame == TIE:
            label = myfont32.render("C'est une egalitée !", 1, BLACK)
        elif self.endgame == WON:
            label = myfont32.render("Victoire ! Bien joué !", 1, BLACK)
        elif self.endgame == LOST:
            label = myfont32.render("Défaite ! Bien essayé !", 1, BLACK)
            
        self.screen.blit(label, (10, 480))


    #Get the user input in the login screen
    def get_key(self):
        event = pygame.event.poll()
        if event.type == pygame.KEYDOWN:
            return event.unicode
        elif event.type == pygame.QUIT:
            exit()
        else:
            pass         


    #Wait for user input, change to game screen and send the login 
    #to the server if the user enter a login and press \r.
    #The cpt check that the login do not exceed 10 characters.
    def login_update(self):
        self.clock.tick(60)
        self.screen.fill(WHITE)
        self.draw_login()

        self.inkey = self.get_key()

        if self.login_cpt >= 10 and self.inkey != '\r' and self.inkey != '\b':
            pass
        elif self.inkey == '\b':
            self.login_string = self.login_string[0:-1]
            if self.login_cpt > 0:
                self.login_cpt -= 1
        elif self.inkey == '\r':
            if len(self.login_string) != 0:
                self.ask_login = False
                self.my_login = self.login_string
                self.main_connexion.send(message.login_request(self.login_string))
        elif self.inkey != None:
            self.login_string = self.login_string[0:] + str(self.inkey)
            self.login_cpt += 1
            
        pygame.display.flip()


    #Continously display the game screen, draw the grid and hud.
    #Handles the events
    def game_update(self):
        self.clock.tick(60)
        self.screen.fill(WHITE)
        self.drawGrid()
        self.draw_HUD()

        #Exit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

            #Handle the user click, if the click collide with a button a message
            #is send to the server
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not self.game_on:
                    pos = pygame.mouse.get_pos()
                    if self.button_replay.collidepoint(pos):
                        self.main_connexion.send(message.start_game())
                    elif self.button_robot.collidepoint(pos):
                        self.main_connexion.send(message.play_bot())
                    elif self.button_spect.collidepoint(pos):
                        self.main_connexion.send(message.spect())
                    elif self.button_stop.collidepoint(pos):
                        exit()

                #If it's the user turn and he click on a cell the coordinates are
                #send to the server
                if self.your_turn:
                    pos = pygame.mouse.get_pos()
                    col = pos[0] // CELLS_WIDTH
                    row = pos[1] // CELLS_HEIGHT
                    if 0 <= row + col*3  and row + col*3 < 9:
                        self.main_connexion.send(message.play(row * 3 + col))
                        self.your_turn = False

            #If the press a keyboard key it will appear in the chat, if he press
            #\r the message is send to the server.
            #The cpt block the message length at 28 characters
            elif event.type == pygame.KEYDOWN:
                self.key = event.unicode
                if self.chat_cpt >= 28 and self.key != '\r' and self.key != '\b':
                    pass
                elif self.key == '\b':
                    self.chat_perso = self.chat_perso[0:-1]
                    if self.chat_cpt > 0:
                        self.chat_cpt -= 1
                elif self.key == '\r':
                    self.main_connexion.send(message.msg(self.chat_perso))
                    self.chat_perso = ""
                    self.chat_cpt = 0
                elif self.key != None:
                    self.chat_perso = self.chat_perso[0:] + str(self.key)
                    self.chat_cpt += 1

        pygame.display.flip()


    #Handle the communication with the server
    def start(self):
        try:
            client_on = True
            
            while client_on:
                answers = []
                try:
                    answers = message.separate(self.main_connexion.recv(1024))
                except BlockingIOError:
                    pass
                
                for answer in answers:
                    #Validate the login
                    if message.is_validate_login(answer):
                        #self.main_connexion.send( message.start_game())
                        pass

                    #Send if the player is player1, player2 or spectator
                    elif message.is_set_player(answer):
                        self.status = status(int(message.body(answer)[0]))
                        self.my_num = self.status.name

                    #If the user is kicked
                    elif message.is_kick(answer):
                        exit()

                    #If the user is a spectator
                    elif message.is_set_player(answer):
                        if status(int(message.body(answer)[0])) == status.spectator:
                            self.is_spect = True

                    #Get the scores for display
                    elif message.is_stats(answer):
                        stats = message.body(answer)
                        self.my_score = int(stats[0])
                        self.other_score = int(stats[1])
                        self.scoreties = int(stats[2])

                    #Signal that a game is starting and get opponant login
                    elif message.is_start_game(answer):
                        self.game_on = True
                        self.other_login = message.body(answer)[0]

                    #If it's your turn to play
                    elif message.is_play(answer):
                        self.your_turn = True

                    #If the move is valid, update the cell to show your move
                    elif message.is_valid_move(answer):
                        shot = int(message.body(answer)[0])
                        self.grid[shot//3][shot%3] = J1

                    #If the move is invalid, update the cell to show the opponant move
                    elif message.is_occupied(answer):
                        shot = int(message.body(answer)[0])
                        #Handle if the player click a cell he already occupy
                        if int(message.body(answer)[1]) == 1 and self.my_num == 2:
                            self.grid[shot//3][shot%3] = J1
                        else:
                            self.grid[shot//3][shot%3] = J2

                    #If the game end, update endgame status and update score
                    elif message.is_game_status(answer):
                        game_status = gameStatus(int(message.body(answer)[0]))
                        if game_status == gameStatus.defeat:
                            endgame = LOST
                            self.other_score += 1
                        elif game_status == gameStatus.victory:
                            endgame = WON
                            self.my_score += 1
                        else:
                            endgame = TIE
                            self.scoreties += 1
                        self.game_on = False
                        self.clean_grid()

                    #Handle the pings from the server
                    elif message.is_ping(answer):
                        self.main_connexion.send(message.ping())

                    #Get the message to display in the chat
                    elif message.is_msg(answer):
                        self.update_chat(message.body(answer)[0])

                    #Allow the spectators to see all the grid
                    elif message.is_map_info(answer):
                        for cell in message.body(answer):
                            self.grid[int(cell) // NB_ROW][int(cell) % NB_COL] = int(cell) 

                    #If the user observe, get the name of the players
                    elif message.is_players_info(answer):
                        self.my_login = message.body(answer)[0]
                        self.other_login = message.body(answer)[1]

                    #Get number of spectators
                    elif message.is_nb_spect(answer) :
                        self.nb_spectators = int(message.body(answer)[0])
                        
                    else:
                        print(answer)

                #The login screen
                if self.ask_login:
                      self.login_update()
                #The game screen
                else:
                    self.game_update()
                    
            self.main_connexion.close()
            
        except ConnectionResetError:
            exit()


#Start the game
game = Game()
game.start()

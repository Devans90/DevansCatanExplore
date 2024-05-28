from catanatron_core.catanatron import Game

game = Game([RandomPlayer(Color.RED), ResourceHoarderPlayer(Color.BLUE)])
game.play()
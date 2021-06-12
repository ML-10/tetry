from .commands import switchBracket, switchBracketHost, leaveRoom, chat, transferOwnership, kick, startRoom
from .ribbons import send
from .urls import room


class Room:
    def __init__(self, data, bot):
        self.id = data['id']
        self.opts = data['game']['options']
        self.state = data['game']['state']
        self.match = data['game']['match']
        self.type = data['type']
        self.owner = data['owner']
        self.players = data['players']
        self.invite = room + self.id
        self.bot = bot
        self.bracket = 'player'
        self.inGame = False

    async def switchBracket(self, playing: bool, uid=None):
        bracket = ['spectator', 'player'][playing]
        self.bracket = bracket
        bot = self.bot
        ws = bot.ws
        if uid:
            await send(switchBracketHost(bot.messageId, bracket, uid), ws)
        else:
            await send(switchBracket(bot.messageId, bracket), ws)
    
    async def leave(self):
        bot = self.bot
        await send(leaveRoom(bot.messageId, self.id), bot.ws)
        bot.room = None

    def getPlayer(self, id):
        return self.players[self._getIndex(id)]
    
    def _getIndex(self, id):
        players = self.players
        for i in range(len(players)):
            player = players[i]
            if player['_id'] == id:
                return i
    
    async def makeOwner(self, uid):
        await send(transferOwnership(self.bot.messageId, uid), self.bot.ws)
    
    async def kickUser(self, uid):
        await send(kick(self.bot.messageId, uid), self.bot.ws)
    
    async def startGame(self):
        await send(startRoom(self.bot.messageId), self.bot.ws)
    
    async def send(self, message):
        await send(chat(message, self.bot.messageId), self.bot.ws)
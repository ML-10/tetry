import math

import trio

from .commands import replay
from .pieceRng import Rng
from .ribbons import send


class Game:
    # dict_keys(['options', 'contexts', 'first', 'gameID', 'started', 'lastKickRun'])
    def __init__(self, data, bot):
        self.gameId = data['gameID']
        self.first = data['first']
        self.contexts = {ctx['user']['_id']: ctx
                         for ctx in data['contexts']}
        self.context = self.contexts[bot.id]
        self.members = list(self.contexts.keys())
        self.listedId = self.context['listenID']
        self.room = bot.room
        self.bot = bot
        self.startTime = 0
        self.pendingFrames = []
        self.opts = data['options']
        self.seed = self.opts['seed']
        self.rng = Rng(self.seed)
        self.bag = self.rng.getBag()
        self.started = data['started']
        self.lastKickRun = data['lastKickRun']
        self.replay = {}

    def getFrame(self):
        passed = trio.current_time() - self.startTime
        frame = passed*60
        return {'frame': math.floor(frame), 'subframe': frame % 1}

    def press(self, key):
        f = self.getFrame()
        frame = f['frame']
        subframe = f['subframe']
        frame = {'frame': frame, 'type': 'keydown', 'data':
                 {
                     'key': key,
                     'subframe': subframe,
                 }
                 }
        self.pendingFrames.append(frame)

    def release(self, key):
        f = self.getFrame()
        frame = f['frame']
        subframe = f['subframe']
        frame = {'frame': frame, 'type': 'keyup', 'data':
                 {
                     'key': key,
                     'subframe': subframe,
                 }
                 }
        self.pendingFrames.append(frame)

    async def _start(self):  # send a full frame
        opts = {**self.opts, **self.context['opts'],
                'physical': True, 'username': self.bot.name}
        frame = {
            'data': {  # fire and gameoverreason seem to be optional
                'successful': False,  # seems to allways be false
                'gameoverreason': None,
                'options': opts,
                'game': {
                    'board': [[None]*10]*40,
                    'bag': self.bag,
                    'hold': {'piece': None, 'locked': False},
                    'playing': True,
                    'g': self.opts['g'],
                    'controlling': {  # button clicks maybe?
                        'ldas': 0, 'ldasiter': 0, 'lshift': False, 'rdas': 0, 'rdasiter': 0, 'rshift': False, 'lastshift': 0, 'softdrop': False
                    },
                    'handling': self.bot.handling
                },
                'replay': {},
                'source': {},
                'stats': {'seed': self.seed, 'lines': 0, 'level_lines': 0, 'level_lines_needed': 1, 'inputs': 0, 'time': {'start': 0, 'zero': True, 'locked': False, 'prev': 0, 'frameoffset': 0}, 'score': 0, 'zenlevel': 1, 'zenprogress': 0, 'level': 1, 'combo': 0, 'currentcombopower': 0, 'topcombo': 0, 'btb': 0, 'topbtb': 0, 'tspins': 0, 'piecesplaced': 0, 'clears': {'singles': 0, 'doubles': 0, 'triples': 0, 'quads': 0, 'realtspins': 0, 'minitspins': 0, 'minitspinsingles': 0, 'tspinsingles': 0, 'minitspindoubles': 0, 'tspindoubles': 0, 'tspintriples': 0, 'tspinquads': 0, 'allclear': 0}, 'garbage': {'sent': 0, 'received': 0, 'attack': 0, 'cleared': 0}, 'kills': 0, 'finesse': {'combo': 0, 'faults': 0, 'perfectpieces': 0}},
                'targets': [],
                'fire': 0,
                'killer': {'name': None, 'type': 'sizzle'},
                'assumptions': {},
                'aggregatestats': {'apm': 0, 'pps': 0, 'vsscore': 0}
            },
            'frame': 0,
            'type': 'full'
        }
        print(frame)
        self.pendingFrames.append(frame)

        await send(replay(self.bot.messageId, self.pendingFrames, self.gameId, frame), self.bot.ws)
        self.pendingFrames = []

    def getNextPiece(self):
        if not len(self.bag):
            self.bag = self.rng.getBag()
        return self.bag.pop(0)

    async def start(self):
        t = trio.current_time()
        self.startTime = t
        d = 30  # frames
        frame = 0  # frames
        await self._start()
        while self.bot.room.inGame:
            t += d/60
            frame += d
            await trio.sleep_until(t)
            await send(replay(self.bot.messageId, self.pendingFrames, self.gameId, frame), self.bot.ws)
            self.pendingFrames = []

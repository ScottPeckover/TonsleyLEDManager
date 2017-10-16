import json

from flask import send_from_directory


class Runner:
    def __init__(self, dims):
        self.dims = dims
        import numpy as np
        self.np = np

        from flask import Flask, render_template, request
        from flask_sockets import Sockets
        import json
        from random import randint
        # from itertools import cycle
        # from matplotlib import cm
        # num_cols = 512
        # Pick a colour map from here: https://matplotlib.org/users/colormaps.html
        # rainbow = cm.get_cmap('PuBu', num_cols)
        # self.sky_colours = [[int(c * 256) for c in rainbow(i)[:-1]] for i in range(num_cols)]
        # self.sky_colours = cycle(self.sky_colours + self.sky_colours[::-1])
        app = Flask('UnityGame')
        sockets = Sockets(app)
        self.things = [{
            'type': 'cloud',
            'xpos': 90,
            'ypos': 1,
            'frame': 0,
            'frame_rate': 0,
            'velocity': 0.2,
        }, {'type': 'gull',
            'xpos': 90,
            'ypos': 1,
            'frame': 0,
            'frame_rate': 0.2,
            'velocity': 1, }
        ]
        self.things_templates = {'cloud':
                                     {'colours':
                                          [[0xd8, 0xad, 0xde], [253, 245, 251]],
                                      'template':
                                          np.array([[
                                              # gratuitously stolen from: https://cdn.dribbble.com/users/1113/screenshots/150244/pixelcloud-dribbble.png
                                              [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0],
                                              [0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 1, 1, 0, 0, 0, 0],
                                              [0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 1, 0, 0, 0],
                                              [0, 0, 1, 1, 2, 2, 1, 1, 2, 2, 2, 2, 1, 0, 0, 0],
                                              [0, 1, 1, 2, 2, 2, 2, 1, 2, 2, 2, 2, 1, 1, 0, 0],
                                              [0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 0],
                                              [1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                                              [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
                                              [1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1],
                                              [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                                          ]])
                                      },
                                 'gull': {'colours':
                                              [[77, 77, 77], [253, 245, 251]],
                                          'template':
                                              np.array([[
                                                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                                  [0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0],
                                                  [0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0],
                                                  [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0],
                                              ], [
                                                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                                                  [0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0],
                                                  [1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0],
                                                  [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                                              ]])
                                          },
                                 'boat': {'template': [
                                     # [0,0, 0, 1, 0, 0,0],
                                     # [0,0, 1, 1, 1, 0,0],
                                     # [0,1, 1, 1, 1, 1,0],
                                     # [0,0, 0, 1, 0, 0,0],
                                     # [1,1, 0, 1, 0, 1,1],
                                     # [0,1, 1, 1, 1, 1,0],
                                     # [0,0, 1, 1, 1, 0,0]
                                     [0, 0, 0, 0, 0, 0, 0, 2],
                                     [0, 0, 0, 0, 0, 0, 2, 3],
                                     [0, 1, 1, 1, 0, 2, 0, 3],
                                     [1, 1, 1, 1, 1, 1, 0, 3],
                                     [0, 1, 1, 1, 1, 0, 0, 3]
                                 ]}
                                 }
        self.current_players = {}
        game_x_min = 0
        game_x_max = 100
        self.game_y_max = 14
        boat_velocity = 1.5
        initial_hook_velocity = .2
        app_port = 5000

        ug_socket = {
            'ws': None
        }
        player_sockets = {}
        self.ug_socket = ug_socket
        self.player_sockets = player_sockets

        def make_player(ws):
            player = {
                'type': 'boat',
                'colour': [[randint(0, 255) for _ in range(3)], [90, 60, 20], [255, 255, 255]],
                'hook_position': 0,
                'hook_velocity': 0,
                'xpos': randint(game_x_min, game_x_max),
                'ypos': 8,
                'velocity': 0,
                'score': 0,
                'id': ws.handler.client_address,
                'catch': {'colour': None, 'score': 0}
            }
            self.player_sockets[ws.handler.client_address] = ws
            self.current_players[ws.handler.client_address] = player
            # inform the unity game about this?

        @sockets.route('/unity')
        def unity_client_socket(ws):
            # should check that unity is running locally only
            if ug_socket['ws'] is not None or ws.handler.client_address[0] != '127.0.0.1':
                return
            ug_socket['ws'] = ws

            while not ws.closed:
                # do stuff here i guess...
                message = ws.receive()
                if message is not None:
                    if message == "":
                        continue;
                    message = json.loads(str(message))
                    self.current_players[tuple(message['id'])]['hook_velocity'] = - \
                        self.current_players[tuple(message['id'])]['hook_velocity']
                    self.current_players[tuple(message['id'])]['catch']['score'] = message['score']
                    self.current_players[tuple(message['id'])]['catch']['colour'] = [int(s) for s in
                                                                                     message['colour'][5:-4].split(',')]
                    self.player_sockets[tuple(message['id'])].send("fish_hooked")
            ug_socket['ws'] = None

        @sockets.route('/client')
        def device_client_socket(ws):
            make_player(ws)
            ws.send(json.dumps(self.current_players[ws.handler.client_address]))
            while not ws.closed:
                message = ws.receive()
                if message is None:
                    break
                message = message.lower()
                player_state = self.current_players[ws.handler.client_address]
                #print("{}: {}".format(player_state['id'][0], message))
                event_handlers = {
                    'left': None
                }
                if message == 'left':
                    if player_state['hook_velocity'] == 0:
                        player_state['velocity'] = -boat_velocity
                elif message == 'right':
                    if player_state['hook_velocity'] == 0:
                        player_state['velocity'] = boat_velocity
                elif message == 'stop':
                    player_state['velocity'] = 0
                elif message == 'hook':
                    # handle hook drop gameplay
                    # player_state['score'] += 1
                    if player_state['hook_velocity'] == 0:
                        player_state['velocity'] = 0
                        player_state['hook_velocity'] = initial_hook_velocity
                        if self.ug_socket['ws'] is not None:
                            self.ug_socket['ws'].send(
                                'hook dropped: ' + player_state['id'][0] + ' ' + str(player_state['id'][1]))
                elif message == 'plus':
                    if player_state['hook_velocity'] > -.3:
                        player_state['hook_velocity'] -= .04
                elif message == 'minus':
                    if player_state['hook_velocity'] < -.01:
                        player_state['hook_velocity'] += .04
                self.send_client_state(ws)
            del self.current_players[ws.handler.client_address]
            del self.player_sockets[ws.handler.client_address]

        import uuid
        qr_codes = set([uuid.uuid4().hex])

        @app.route('/static/<path:filename>')
        def custom_static(filename):
            return send_from_directory(app.config['CUSTOM_STATIC_PATH'], filename)

        @app.route('/')
        def home():
            # check they sent a a valid qr code
            # artworkpc.isd.ad.flinders.edu.au:5000/?qr=a6rt5grtg566bt
            qr = request.args.get('qr')
            # if qr not in qr_codes:
            #     return "YOU CANT PLAY WITHOUT A QR CODE"
            with open('fishgame.html') as f:
                fish_html = f.read()
            return fish_html

        def flaskThread():
            from gevent import pywsgi
            from geventwebsocket.handler import WebSocketHandler
            import socket
            host = socket.gethostbyname(socket.gethostname())
            server = pywsgi.WSGIServer(('0.0.0.0', app_port), app, handler_class=WebSocketHandler)
            # print("Starting server on: http://{}:{}".format(*server.address))
            print("Starting server on: http://{}:{}".format(host, server.server_port))
            # print host
            server.serve_forever()

        import thread
        thread.start_new_thread(flaskThread, ())

    def send_client_state(self, ws):
        try:
            self.player_sockets[ws].send(json.dumps(self.current_players[ws]))
        except:
            pass

    def update_things(self):
        for thing in self.things + self.current_players.values():
            thing['xpos'] = (thing['xpos'] + thing['velocity']) % self.dims[0]
            if thing['xpos'] >= self.dims[0]:
                thing['xpos'] = 0 - len(self.things_templates[thing['type']]['template'][0])

        for ws, player in self.current_players.items():
            player['hook_position'] += player['hook_velocity']

            # when hook reaches top
            if player['hook_position'] < 0:
                player['hook_position'] = 0
                player['hook_velocity'] = 0
                player['score'] += player['catch']['score']
                player['catch']['score'] = 0
                player['catch']['colour'] = None
                if self.ug_socket['ws'] is not None:
                    self.ug_socket['ws'].send(
                        'reeled in: ' + player['id'][0] + ' ' + str(player['id'][1]))
                self.player_sockets[ws].send('reeled_in')
            if player['hook_position'] >= self.game_y_max:
                player['hook_position'] = self.game_y_max
                player['hook_velocity'] = -.1
                self.player_sockets[ws].send('bottom_reached')
            self.send_client_state(ws)

    def run(self):
        np = self.np
        water = [14, 69, 156]
        fishing_line_in_water = [0, 0, 255]
        sky = [255, 141, 28]
        # sky = next(self.sky_colours)
        pixels = np.full((self.dims[0], self.dims[1], 3), water, dtype=np.uint8)
        pixels[:, 0:13] = sky
        self.update_things()
        for thing in self.things + self.current_players.values():
            template = self.things_templates[thing['type']]
            if thing['type'] == 'boat':
                grid = template['template']
                colour = thing['colour']
                if thing['hook_position'] != 0:
                    boat_width = len(template['template'][0])
                    paintx = (int(thing['xpos'] % self.dims[0]) + boat_width - 1)
                    paintx = paintx - 165 if paintx > 164 else paintx
                    pixels[paintx,
                    13:13 + int(thing['hook_position'])] = fishing_line_in_water
                    if thing['catch']['colour'] is not None:
                        paintx = (paintx + 1) - 165 if paintx + 1 > 164 else paintx + 1
                        pixels[paintx,
                               13 + int(thing['hook_position']):14 + int(thing['hook_position'])] = thing['catch']['colour']
            else:
                thing['frame'] += thing['frame_rate']
                if thing['frame'] >= len(template['template']):
                    thing['frame'] = 0
                colour = template['colours']
                grid = template['template'][int(thing['frame'])]
            xpos = thing['xpos']
            ypos = thing['ypos']
            for y, row in enumerate(grid):
                y = np.int(np.floor(ypos + y))
                for x, pix in enumerate(row):
                    if pix != 0:
                        col = colour[pix - 1]
                        x = np.int((xpos + x) % self.dims[0])
                        pixels[x, y] = col
        if self.ug_socket['ws'] is not None:
            self.ug_socket['ws'].send(json.dumps(self.current_players.values()))
        return pixels


if __name__ == "__main__":
    from demo import show

    show(Runner, fps=14, rows=17, cols=165, scale=8)

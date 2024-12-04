import asyncio
import websockets
import json
import time
import ssl
import certifi
import requests
import random

avatarsIds = []
itemIds = []

with open("objects.json", 'r', encoding='utf-8') as file:
    try:
        data = json.load(file)
        
        for avatar in data['avatars']:
            if avatar['free'] == False:
                avatarsIds.append(avatar['id'])

        for item in data['items']:
            if item['free'] == False:
                itemIds.append(item['id'])
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

print("Avatar IDs:", avatarsIds)
async def handle_game_block_message(message):
    """Handles and extracts gameBlockIndex from a message."""
    try:
        # Check if the message contains content and it is a JSON string
        data = json.loads(message)
        
        # Extract gameBlockIndex if available
        if isinstance(data, list) and len(data) > 0:
            message_data = data[0]
            if 'data' in message_data and 'content' in message_data['data']:
                content = message_data['data']['content']
                content_data = json.loads(content)  # Parse the content
                
                # Extract the gameBlockIndex
                game_block_index = content_data.get('gameBlockIndex', None)
                if game_block_index is not None:
                    print(f"Received gameBlockIndex: {game_block_index}")
                    return game_block_index
                else:
                    print("gameBlockIndex not found in content")
            else:
                print("Content field is missing.")
        else:
            print("Unexpected data format.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON content: {e}")
    return None

async def switch_avatars_and_connect(websocket, game_id, client_id, idn):

    for i in range(1):
        random_character = random.randint(0, len(avatarsIds) - 1)
        random_item = random.randint(0, len(itemIds) - 1)
        avatar_switch_message = [{
            "id": idn,
            "channel": "/service/controller",
            "data": {
                "gameid": game_id,
                "type": "message",
                "host": "kahoot.it",
                "id": 46,
                "content": json.dumps({
                    "avatar": {
                        "type": avatarsIds[random_character] ,
                        "item":  itemIds[random_item]
                    }
                })
            },
            "clientId": client_id,
            "ext": {}
        }]
        
        await websocket.send(json.dumps(avatar_switch_message))
        


def get_tc():
    """ Returns a timestamp in milliseconds """
    return int(time.time() * 1000)

            
async def connect_to_websocket(name, wss_connection, game_id):
    uri = f"wss://kahoot.it/cometd/{game_id}/{wss_connection}"
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    retry_attempts = 3
    idn = 1

    for attempt in range(retry_attempts):
        try:
            async with websockets.connect(uri, ssl=ssl_context) as websocket:
                handshake_message = [{
                    "id": idn,
                    "version": "1.0",
                    "minimumVersion": "1.0",
                    "channel": "/meta/handshake",
                    "supportedConnectionTypes": ["websocket", "long-polling", "callback-polling"],
                    "advice": {"timeout": 60000, "interval": 0},
                    "ext": {
                        "ack": True,
                        "timesync": {"tc": get_tc(), "l": 0, "o": 0}
                    }
                }]
                await websocket.send(json.dumps(handshake_message))

                idn += 1
                response = await websocket.recv()
                response_data = json.loads(response)

                if response_data and isinstance(response_data, list) and "clientId" in response_data[0]:
                    client_id = response_data[0]["clientId"]
                else:
                    return

                connect_message = [{
                    "id": idn,
                    "channel": "/meta/connect",
                    "connectionType": "websocket",
                    "advice": {"timeout": 0},
                    "clientId": client_id,
                    "ext": {
                        "ack": 0,
                        "timesync": {"tc": get_tc(), "l": 64, "o": -2087}
                    }
                }]
                await websocket.send(json.dumps(connect_message))

                idn += 1
                response = await websocket.recv()

                name_request = [{
                    "id": idn,
                    "channel": "/service/controller",
                    "data": {
                        "type": "login",
                        "gameid": game_id,
                        "host": "kahoot.it",
                        "name": name,
                        "content": "{\"device\":{\"userAgent\":\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 OPR/113.0.0.0\",\"screen\":{\"width\":1920,\"height\":1080}}}"
                    },
                    "clientId": client_id,
                    "ext": {}
                }]
                await websocket.send(json.dumps(name_request))

                idn += 1
                response = await websocket.recv()

                next_mess = [{
                    "id": idn,
                    "channel": "/service/controller",
                    "data": {
                        "gameid": game_id,
                        "type": "message",
                        "host": "kahoot.it",
                        "id": 16,
                        "content": "{\"usingNamerator\":false}"
                    },
                    "clientId": client_id,
                    "ext": {}
                }]
                await websocket.send(json.dumps(next_mess))

                idn += 1
                response = await websocket.recv()

                final_connect = [{
                    "id": idn,
                    "channel": "/meta/connect",
                    "connectionType": "websocket",
                    "clientId": client_id,
                    "ext": {
                        "ack": 2,
                        "timesync": {
                            "tc": get_tc(),
                            "l": 63,
                            "o": -2086
                        }
                    }
                }]
                await websocket.send(json.dumps(final_connect))
                response = await websocket.recv()
                idn += 1
                
                avatar = [{"id":idn,
                           "channel":"/service/controller",
                           "data":{
                               "gameid":game_id,
                                "type":"message",
                                "host":"kahoot.it",
                                "id":46,
                                "content":"{\"avatar\":{\"type\":3050,\"item\":3600}}"
                                },
                           "clientId":client_id,
                           "ext":{}
                           }]
                await websocket.send(json.dumps(avatar))
                response = await websocket.recv()
                idn += 1
                
                while True:
                    
                    answer = [
                        {
                            "id": idn,
                            "channel": "/service/controller",
                            "data": {
                                "gameid": game_id,
                                "type": "message",
                                "host": "kahoot.it",
                                "id": 45,
                                "content": json.dumps({
                                    "type": "quiz",
                                    "choice": 3,
                                    "questionIndex": 1
                                }),
                            },
                            "clientId": client_id,
                            "ext": {}
                        }
                    ]
                    final_connect = [{
                        "id": idn,
                        "channel": "/meta/connect",
                        "connectionType": "websocket",
                        "clientId": client_id,
                        "ext": {
                            "ack": 2,
                            "timesync": {
                                "tc": get_tc(),
                                "l": 63,
                                "o": -2086
                            }
                        }
                    }]
                    
                    await websocket.send(json.dumps(final_connect))
                    await switch_avatars_and_connect(websocket, game_id, client_id, idn)
                    response = await websocket.recv()
                    await websocket.send(json.dumps(answer))
                    response = await websocket.recv()
                    print(response)
                    await asyncio.sleep(6)
                    idn += 1
        except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.InvalidStatusCode) as e:
            if attempt == retry_attempts - 1:
                print("stuff")

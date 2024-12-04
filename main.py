from flask import Flask, send_from_directory, jsonify, request
import requests
import asyncio
import os
from kahootSocket import connect_to_websocket
import random
import string

characters = string.ascii_letters + string.digits

app = Flask(__name__)

async def run_multiple_connections(sessionToken, gameId, num_connections=30):
    characters = string.ascii_letters + string.digits

    tasks = []
    for _ in range(num_connections):
        name = ''.join(random.choices(characters, k=12))
        task = connect_to_websocket(name, sessionToken, gameId)
        tasks.append(task)
    
    await asyncio.gather(*tasks)

@app.route('/proxy', methods=['GET'])
def proxy_request():
    game_id = request.args.get('gameId')

    if not game_id:
        return jsonify({'error': 'Game ID is required'}), 400

    kahoot_url = f'https://kahoot.it/reserve/session/{game_id}/?{request.args.get("timestamp")}'
    
    response = requests.get(kahoot_url)
    
    if response.status_code == 200:
        data = response.json()
        data["session-token"] = response.headers.get('x-kahoot-session-token')
        return jsonify(data)
    else:
        return jsonify({'error': 'Failed to fetch data from Kahoot API'}), response.status_code

@app.route('/connect', methods=['GET'])
def connect():
    gameId = request.args.get('gameId')
    sessionToken = request.args.get('session-token')
    num = request.args.get('joinNum', 30)
    
    if not gameId or not sessionToken:
        return jsonify({"error": "Game ID or session token missing"}), 400
    
    try:
        num_connections = int(num)
        
        asyncio.run(run_multiple_connections(sessionToken, gameId, num_connections))
        
        return jsonify({"status": "WebSocket connections initiated", "gameId": gameId, "connections": num_connections})
    except ValueError:
        return jsonify({"error": "'num' must be an integer"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def serve_html():
    return send_from_directory(os.getcwd(), 'popup.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

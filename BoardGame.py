from flask import Flask, render_template, jsonify, request
import os

app = Flask(__name__)

SIZE = 7  # 7x7 dot grid => 6x6 boxes
EVENT_FILE = 'game_events.txt'

# Game state
state = {
    'current_player': 1,
    'lines': {},
    'boxes': {},
    'scores': {1: 0, 2: 0},
    'boxes_filled': 0
}

def check_completed_boxes(row, col):
    completed = []
    box_positions = []
    if row % 2 == 0:
        if row > 0: box_positions.append((row - 1, col))
        if row < SIZE * 2 - 2: box_positions.append((row + 1, col))
    else:
        if col > 0: box_positions.append((row, col - 1))
        if col < SIZE * 2 - 2: box_positions.append((row, col + 1))

    for r, c in box_positions:
        if is_box_completed(r, c) and f"{r},{c}" not in state['boxes']:
            state['boxes'][f"{r},{c}"] = state['current_player']
            state['scores'][state['current_player']] += 1
            state['boxes_filled'] += 1
            completed.append((r, c))
    return completed

def is_box_completed(row, col):
    return (
        f"{row-1},{col}" in state['lines'] and
        f"{row+1},{col}" in state['lines'] and
        f"{row},{col-1}" in state['lines'] and
        f"{row},{col+1}" in state['lines']
    )

def load_event_file():
    if not os.path.exists(EVENT_FILE): return
    with open(EVENT_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("Player"): continue
            elif line.startswith("Turn:"):
                state['current_player'] = 1 if '1' in line else 2
            elif line.startswith("Line:"):
                coord = line.split(':')[1].strip()
                state['lines'][coord] = 1
            elif line.startswith("Box:"):
                parts = line.split(':')[1].strip().split(',')
                key = f"{parts[0].strip()},{parts[1].strip()}"
                player = 1 if '1' in parts[2] else 2
                state['boxes'][key] = player
                state['scores'][player] += 1
                state['boxes_filled'] += 1

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/load_game')
def load_game():
    load_event_file()
    return jsonify({
        'current_player': state['current_player'],
        'lines': state['lines'],
        'boxes': state['boxes'],
        'scores': state['scores'],
        'boxes_filled': state['boxes_filled']
    })

@app.route('/click_line', methods=['POST'])
def click_line():
    data = request.get_json()
    key = data.get('key')
    row = data.get('row')
    col = data.get('col')

    if key in state['lines']:
        return jsonify({'error': 'Line already used'}), 400

    state['lines'][key] = state['current_player']
    completed = check_completed_boxes(row, col)
    game_over = state['boxes_filled'] == (SIZE - 1) ** 2

    if not completed:
        state['current_player'] = 2 if state['current_player'] == 1 else 1

    return jsonify({
        'current_player': state['current_player'],
        'boxes': state['boxes'],
        'scores': state['scores'],
        'completed_boxes': completed,
        'game_over': game_over
    })

@app.route('/reset', methods=['POST'])
def reset():
    state['current_player'] = 1
    state['lines'] = {}
    state['boxes'] = {}
    state['scores'] = {1: 0, 2: 0}
    state['boxes_filled'] = 0
    return 'Game reset', 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

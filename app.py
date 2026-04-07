from flask import Flask, render_template, request, jsonify, session
import random
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-2026-filword-game'

# ========== НАСТРОЙКИ ==========
GRID_SIZE = 10

# Слова по темам
TOPICS = {
    "🐕 Животные": ["КОТ", "СОБАКА", "ЛИСА", "ВОЛК", "ЗАЯЦ", "МЕДВЕДЬ", "ТИГР", "ЛЕВ", "СЛОН", "ЖИРАФ"],
    "🍎 Фрукты": ["ЯБЛОКО", "ГРУША", "БАНАН", "АПЕЛЬСИН", "МАНГО", "КИВИ", "ВИШНЯ", "СЛИВА", "ПЕРСИК", "ЛИМОН"],
    "💼 Профессии": ["ВРАЧ", "УЧИТЕЛЬ", "ПОВАР", "СТРОИТЕЛЬ", "ХУДОЖНИК", "ПИЛОТ", "ШОФЁР", "МОРЯК", "ПЕВЕЦ"],
    "⚽ Спорт": ["ФУТБОЛ", "БАСКЕТБОЛ", "ТЕННИС", "ПЛАВАНИЕ", "БЕГ", "ХОККЕЙ", "ВОЛЕЙБОЛ", "БОКС"],
    "🎨 Цвета": ["КРАСНЫЙ", "СИНИЙ", "ЗЕЛЁНЫЙ", "ЖЁЛТЫЙ", "ЧЁРНЫЙ", "БЕЛЫЙ", "ФИОЛЕТОВЫЙ", "ОРАНЖЕВЫЙ"],
    "🌊 Реки": ["АМАЗОНКА", "НИЛ", "ЯНЦЗЫ", "МИССИСИПИ", "ЕНИСЕЙ", "ОБЬ", "ВОЛГА"]
}

def create_empty_grid(size):
    return [['' for _ in range(size)] for _ in range(size)]

def can_place_word(grid, word, row, col, dr, dc):
    size = len(grid)
    for i, letter in enumerate(word):
        r = row + i * dr
        c = col + i * dc
        if r < 0 or r >= size or c < 0 or c >= size:
            return False
        if grid[r][c] != '' and grid[r][c] != letter:
            return False
    return True

def place_word(grid, word, row, col, dr, dc):
    for i, letter in enumerate(word):
        r = row + i * dr
        c = col + i * dc
        grid[r][c] = letter

def generate_grid(words, size=GRID_SIZE):
    russian_letters = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
    directions = [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]
    
    words_sorted = sorted(words, key=len, reverse=True)
    
    for attempt in range(30):
        grid = create_empty_grid(size)
        all_placed = True
        placed_words_info = []
        
        for word in words_sorted:
            placed = False
            for _ in range(1000):
                row = random.randint(0, size - 1)
                col = random.randint(0, size - 1)
                dr, dc = random.choice(directions)
                
                end_row = row + (len(word) - 1) * dr
                end_col = col + (len(word) - 1) * dc
                if 0 <= end_row < size and 0 <= end_col < size:
                    if can_place_word(grid, word, row, col, dr, dc):
                        place_word(grid, word, row, col, dr, dc)
                        placed_words_info.append({
                            'word': word,
                            'start': [row, col],
                            'end': [end_row, end_col],
                            'dir': (dr, dc)
                        })
                        placed = True
                        break
            
            if not placed:
                all_placed = False
                break
        
        if all_placed:
            for i in range(size):
                for j in range(size):
                    if grid[i][j] == '':
                        grid[i][j] = random.choice(russian_letters)
            return grid, placed_words_info
    
    # Fallback
    grid = create_empty_grid(size)
    for idx, word in enumerate(words[:min(8, size)]):
        if len(word) <= size:
            for i, letter in enumerate(word):
                grid[idx][i] = letter
    
    for i in range(size):
        for j in range(size):
            if grid[i][j] == '':
                grid[i][j] = random.choice(russian_letters)
    return grid, []

def find_word_positions(grid, word):
    positions = []
    size = len(grid)
    directions = [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]
    
    for row in range(size):
        for col in range(size):
            for dr, dc in directions:
                end_row = row + (len(word) - 1) * dr
                end_col = col + (len(word) - 1) * dc
                if 0 <= end_row < size and 0 <= end_col < size:
                    found = True
                    for i, letter in enumerate(word):
                        r = row + i * dr
                        c = col + i * dc
                        if grid[r][c] != letter:
                            found = False
                            break
                    if found:
                        positions.append({
                            'start': [row, col],
                            'end': [end_row, end_col]
                        })
    return positions

# ========== МАРШРУТЫ FLASK ==========

@app.route('/')
def index():
    topic = random.choice(list(TOPICS.keys()))
    words = TOPICS[topic][:8]
    
    grid, placed_info = generate_grid(words)
    
    word_positions = {}
    for word in words:
        word_positions[word] = find_word_positions(grid, word)
    
    session['grid'] = grid
    session['words'] = words
    session['topic'] = topic
    session['word_positions'] = word_positions
    session['found_words'] = []
    session['locked_positions'] = {}
    
    return render_template('index.html', 
                         grid=grid, 
                         words=words, 
                         topic=topic)

@app.route('/check_word', methods=['POST'])
def check_word():
    data = request.get_json()
    word = data.get('word', '').upper()
    selected_positions = data.get('positions', [])
    
    if word not in session.get('words', []):
        return jsonify({'correct': False, 'word': word})
    
    if word in session.get('found_words', []):
        return jsonify({'correct': False, 'word': word, 'already_found': True})
    
    saved_positions = session.get('word_positions', {}).get(word, [])
    
    if not saved_positions:
        current_grid = session.get('grid', [])
        if current_grid:
            saved_positions = find_word_positions(current_grid, word)
            if saved_positions:
                session['word_positions'][word] = saved_positions
                session.modified = True
    
    if saved_positions:
        locked = session.get('locked_positions', {})
        locked[word] = saved_positions[0]
        session['locked_positions'] = locked
    
    session['found_words'].append(word)
    session.modified = True
    
    return jsonify({
        'correct': True,
        'word': word,
        'positions': saved_positions,
        'found_words': session['found_words'],
        'all_found': len(session['found_words']) == len(session['words'])
    })

@app.route('/smart_restart', methods=['POST'])
def smart_restart():
    data = request.get_json()
    found_words = data.get('found_words', [])
    
    old_grid = session.get('grid', [])
    all_words = session.get('words', [])
    locked_positions = session.get('locked_positions', {})
    
    if not old_grid:
        return jsonify({'error': 'No grid found'}), 400
    
    size = len(old_grid)
    russian_letters = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
    
    new_grid = [row[:] for row in old_grid]
    
    cells_to_keep = set()
    
    for word in found_words:
        if word in locked_positions:
            pos = locked_positions[word]
            start = pos['start']
            end = pos['end']
            
            delta_row = 0 if end[0] == start[0] else (1 if end[0] > start[0] else -1)
            delta_col = 0 if end[1] == start[1] else (1 if end[1] > start[1] else -1)
            steps = max(abs(end[0] - start[0]), abs(end[1] - start[1]))
            
            for i in range(steps + 1):
                r = start[0] + i * delta_row
                c = start[1] + i * delta_col
                cells_to_keep.add((r, c))
    
    free_letters = []
    for i in range(size):
        for j in range(size):
            if (i, j) not in cells_to_keep:
                free_letters.append(new_grid[i][j])
    
    random.shuffle(free_letters)
    
    letter_idx = 0
    for i in range(size):
        for j in range(size):
            if (i, j) not in cells_to_keep:
                new_grid[i][j] = free_letters[letter_idx]
                letter_idx += 1
    
    session['grid'] = new_grid
    
    new_word_positions = {}
    for word in all_words:
        if word in found_words:
            new_word_positions[word] = [locked_positions.get(word, {})] if word in locked_positions else []
        else:
            new_word_positions[word] = find_word_positions(new_grid, word)
    
    session['word_positions'] = new_word_positions
    
    return jsonify({
        'grid': new_grid,
        'locked_words': found_words
    })

@app.route('/new_game')
def new_game():
    topic = request.args.get('topic')
    if not topic or topic not in TOPICS:
        topic = random.choice(list(TOPICS.keys()))
    
    words = TOPICS[topic][:8]
    grid, _ = generate_grid(words)
    
    word_positions = {}
    for word in words:
        word_positions[word] = find_word_positions(grid, word)
    
    session['grid'] = grid
    session['words'] = words
    session['topic'] = topic
    session['word_positions'] = word_positions
    session['found_words'] = []
    session['locked_positions'] = {}
    
    return jsonify({
        'grid': grid,
        'words': words,
        'topic': topic
    })

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)

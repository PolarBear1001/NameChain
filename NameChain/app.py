import os
import json
import logging
import random
from flask import Flask, render_template, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback-dev-secret-key")

# Configure database
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    # Fallback for development
    db_url = "sqlite:///namechain.db"
    
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
    
db = SQLAlchemy(app)

# Load names data
try:
    with open('static/data/names.json', 'r', encoding='utf-8') as f:
        NAMES_LIST = json.load(f)
        # Convert to lowercase for case-insensitive matching
        NAMES_SET = {name.lower() for name in NAMES_LIST}
        # Create mapping from lowercase to original case
        NAME_MAPPING = {name.lower(): name for name in NAMES_LIST}
    logging.info(f"Loaded {len(NAMES_LIST)} names successfully")
except Exception as e:
    logging.error(f"Error loading names: {e}")
    NAMES_LIST = []
    NAMES_SET = set()
    NAME_MAPPING = {}

def get_next_chain_letter(name):
    """Return the first alphabetic character after the first letter (ignoring punctuation)."""
    for char in name[1:]:
        if char.isalpha():
            return char.lower()
    return None

def validate_chain(current_name, next_name):
    """Validate that next_name starts with the correct chain letter."""
    required_letter = get_next_chain_letter(current_name)
    return required_letter is not None and next_name[0].lower() == required_letter

@app.route('/')
def index():
    """Render the main game page"""
    return render_template('index.html')

@app.route('/api/start-game', methods=['POST'])
def start_game():
    """Initialize a new game"""
    # Select a random name to start the chain
    start_name = random.choice(NAMES_LIST)
    
    # Select a random target name different from start
    target_name = random.choice([name for name in NAMES_LIST if name != start_name])
    
    # Initialize game state
    session['current_name'] = start_name
    session['target_name'] = target_name
    session['chain'] = [start_name]
    session['score'] = 0
    session['game_active'] = True
    session['attempts'] = 0  # Track number of attempts
    session['max_attempts'] = 10  # Maximum number of incorrect attempts
    
    # Get the next letter to start with
    next_letter = get_next_chain_letter(start_name)
    if next_letter is None:
        next_letter = "?"
    
    return jsonify({
        'success': True,
        'current_name': start_name,
        'target_name': target_name,
        'chain': [start_name],
        'score': 0,
        'next_letter': next_letter.upper(),
        'message': f'Game started with {start_name}! Your target is {target_name}. Next name must start with {next_letter.upper()}'
    })

@app.route('/api/reset-game', methods=['POST'])
def reset_game():
    """Reset the current game"""
    # Clear all game-related session data
    session.pop('current_name', None)
    session.pop('target_name', None)
    session.pop('chain', None)
    session.pop('score', None)
    session.pop('game_active', None)
    session.pop('attempts', None)
    
    return jsonify({
        'success': True,
        'message': 'Game has been reset. You can start a new game now!'
    })

@app.route('/api/give-up', methods=['POST'])
def give_up():
    """End the current game - player gives up"""
    # Get current game state
    current_name = session.get('current_name', '')
    target_name = session.get('target_name', '')
    chain = session.get('chain', [])
    score = session.get('score', 0)
    
    # Mark game as inactive
    session['game_active'] = False
    
    return jsonify({
        'success': True,
        'current_name': current_name,
        'target_name': target_name,
        'chain': chain,
        'score': score,
        'message': f'You gave up! The target was {target_name}. Your chain length: {len(chain)}',
        'game_over': True
    })

def generate_solution_path(start_name, target_name, used_names):
    """Generate a solution path from start_name to target_name if possible."""
    if not start_name or not target_name:
        return []
    
    # If start and target are the same, return just the start name
    if start_name.lower() == target_name.lower():
        return [start_name]
    
    # Create a set of used names for faster lookup
    used_names_set = {name.lower() for name in used_names}
    
    # For the purpose of finding a solution, only consider the current name
    # as used (and not the whole chain) to find more options
    used_names_set = {start_name.lower()}
    
    # BFS to find a path
    queue = [(start_name, [start_name])]
    visited = {start_name.lower()}
    
    max_queue_size = 3000  # Increase queue size for better path finding
    max_path_length = 8    # Maximum path length to consider
    
    while queue and len(queue) < max_queue_size:
        current_name, path = queue.pop(0)
        
        # Skip if path is getting too long
        if len(path) > max_path_length:
            continue
        
        # Get the next letter for valid names
        next_letter = get_next_chain_letter(current_name)
        if not next_letter:
            continue
            
        # Find possible next names (limit to 50 to prevent excessive computation)
        possible_names = [name for name in NAMES_LIST 
                         if name.lower().startswith(next_letter) 
                         and name.lower() not in visited][:50]
        
        # Shuffle the names to get different solutions each time
        random.shuffle(possible_names)
        
        # Try each possible name
        for name in possible_names:
            new_path = path + [name]
            
            # Check if we found the target
            if name.lower() == target_name.lower():
                return new_path
                
            # Add to queue for further exploration
            queue.append((name, new_path))
            visited.add(name.lower())
    
    # If we reach this point, we couldn't find a complete path
    # Try to find a path that gets close to the target letter
    # Return at least 3 step path if possible
    if len(used_names) <= 1:
        # Find a valid next move if we've only made the first move
        next_letter = get_next_chain_letter(start_name)
        if next_letter:
            possible_next = [name for name in NAMES_LIST 
                           if name.lower().startswith(next_letter) 
                           and name.lower() != start_name.lower()]
                                
            if possible_next:
                next_name = random.choice(possible_next)
                next_next_letter = get_next_chain_letter(next_name)
                
                if next_next_letter:
                    possible_third = [name for name in NAMES_LIST 
                                    if name.lower().startswith(next_next_letter) 
                                    and name.lower() != next_name.lower()
                                    and name.lower() != start_name.lower()]
                                        
                    if possible_third:
                        third_name = random.choice(possible_third)
                        return [start_name, next_name, third_name]
                
                return [start_name, next_name]
    
    # If all else fails, return a different random path
    queue_paths = [p for _, p in queue if len(p) >= 3]
    if queue_paths:
        return random.choice(queue_paths)
    
    # Last resort, just return the longest path we found
    longest_path = []
    for _, p in queue:
        if len(p) > len(longest_path):
            longest_path = p
            
    return longest_path or []

@app.route('/api/guess', methods=['POST'])
def process_guess():
    """Process a name guess from the player"""
    data = request.get_json()
    guess = data.get('guess', '').strip().lower()
    
    # Get current game state
    current_name = session.get('current_name', '')
    target_name = session.get('target_name', '')
    chain = session.get('chain', [])
    score = session.get('score', 0)
    game_active = session.get('game_active', False)
    
    if not game_active:
        return jsonify({
            'success': False,
            'message': 'No active game. Please start a new game.'
        })
    
    # Validation checks
    if not guess:
        return jsonify({
            'success': False,
            'message': 'Please enter a name.'
        })
    
    # Get current attempts count
    attempts = session.get('attempts', 0)
    max_attempts = session.get('max_attempts', 10)

    required_letter = get_next_chain_letter(current_name)
    if required_letter is None:
        return jsonify({
            'success': False,
            'message': 'Current name is too short to continue the chain.',
            'game_over': True
        })
    
    if not guess.startswith(required_letter):
        # Increment attempts count for incorrect guesses
        session['attempts'] = attempts + 1
        remaining_attempts = max_attempts - (attempts + 1)
        
        # Check if max attempts reached
        if remaining_attempts <= 0:
            session['game_active'] = False
            return jsonify({
                'success': False,
                'message': f'Game over! You\'ve used all your attempts. The target was {target_name}.',
                'game_over': True
            })
            
        return jsonify({
            'success': False,
            'message': f'Name must start with {required_letter.upper()}. {remaining_attempts} attempts remaining.'
        })
    
    if guess.lower() in [name.lower() for name in chain]:
        # Increment attempts count
        session['attempts'] = attempts + 1
        remaining_attempts = max_attempts - (attempts + 1)
        
        # Check if max attempts reached
        if remaining_attempts <= 0:
            session['game_active'] = False
            return jsonify({
                'success': False,
                'message': f'Game over! You\'ve used all your attempts. The target was {target_name}.',
                'game_over': True
            })
            
        return jsonify({
            'success': False,
            'message': f'{guess.capitalize()} has already been used in this chain. {remaining_attempts} attempts remaining.'
        })
    
    # Check if the name is in our list
    if guess.lower() not in NAMES_SET:
        # Increment attempts count
        session['attempts'] = attempts + 1
        remaining_attempts = max_attempts - (attempts + 1)
        
        # Check if max attempts reached
        if remaining_attempts <= 0:
            session['game_active'] = False
            return jsonify({
                'success': False,
                'message': f'Game over! You\'ve used all your attempts. The target was {target_name}.',
                'game_over': True
            })
            
        return jsonify({
            'success': False,
            'message': f'{guess.capitalize()} is not in our list of names. {remaining_attempts} attempts remaining.'
        })
    
    # Valid guess - update game state
    # Find the original case version of the name
    original_case_name = NAME_MAPPING.get(guess.lower(), guess.capitalize())
    
    chain.append(original_case_name)
    session['current_name'] = original_case_name
    session['chain'] = chain
    session['score'] = score + 1
    
    # Check if target reached
    if original_case_name.lower() == target_name.lower():
        session['game_active'] = False
        return jsonify({
            'success': True,
            'victory': True,
            'current_name': original_case_name,
            'target_name': target_name,
            'chain': chain,
            'score': session['score'],
            'message': f'VICTORY! You reached {target_name} in {len(chain)-1} steps!',
            'game_over': True
        })
    
    # Get next letter for the chain
    next_letter = get_next_chain_letter(original_case_name)
    
    if next_letter:
        # Check if there are any possible names left
        possible_names = [name for name in NAMES_LIST 
                        if name.lower().startswith(next_letter) 
                        and name.lower() not in [n.lower() for n in chain]]
        
        if not possible_names:
            session['game_active'] = False
            return jsonify({
                'success': True,
                'victory': True,
                'current_name': original_case_name,
                'target_name': target_name,
                'chain': chain,
                'score': session['score'],
                'message': f'VICTORY! No more valid names starting with {next_letter.upper()}. Your chain length: {len(chain)}',
                'game_over': True
            })
        
        return jsonify({
            'success': True,
            'current_name': original_case_name,
            'target_name': target_name,
            'chain': chain,
            'score': session['score'],
            'next_letter': next_letter.upper(),
            'message': f'Good! Next name must start with {next_letter.upper()}'
        })
    else:
        session['game_active'] = False
        return jsonify({
            'success': False,
            'message': 'Current name is too short to continue the chain.',
            'game_over': True
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

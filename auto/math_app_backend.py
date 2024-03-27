from flask import Flask, jsonify, request
import random

app = Flask(__name__)

# Store user session and difficulty level
user_sessions = {}

@app.route('/get_problem', methods=['GET'])
def get_problem():
    session_id = request.args.get('session_id', default='default', type=str)
    if session_id not in user_sessions:
        user_sessions[session_id] = {'score': 0, 'difficulty': 1}
    
    difficulty = user_sessions[session_id]['difficulty']
    num1 = random.randint(1 * difficulty, 10 * difficulty)
    num2 = random.randint(1 * difficulty, 10 * difficulty)
    problem = f'{num1} + {num2}'
    
    return jsonify({'problem': problem})

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    session_id = data.get('session_id', 'default')
    user_answer = data.get('answer', -1)
    correct_answer = eval(data.get('problem'))
    
    if session_id not in user_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    if user_answer == correct_answer:
        user_sessions[session_id]['score'] += 1
        # Increase difficulty after every 5 correct answers
        if user_sessions[session_id]['score'] % 5 == 0:
            user_sessions[session_id]['difficulty'] += 1
        return jsonify({'correct': True, 'next_problem': request.url_root + 'get_problem?session_id=' + session_id})
    else:
        return jsonify({'correct': False})

if __name__ == '__main__':
    app.run(debug=True) 
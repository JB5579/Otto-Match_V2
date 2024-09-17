from flask import Flask, render_template, request, jsonify
from chat_completion import send_openrouter_request, get_conversation_history, clear_conversation_history
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    try:
        response = send_openrouter_request(user_message)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def history():
    return jsonify({'history': get_conversation_history()})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    clear_conversation_history()
    return jsonify({'message': 'Conversation history cleared'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)

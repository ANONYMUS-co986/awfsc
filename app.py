from flask import Flask, request, jsonify, render_template_string, session
from flask_cors import CORS
import google.generativeai as genai
from datetime import datetime, timedelta
import time
import os

# Configure Gemini API
genai.configure(api_key="AIzaSyAll7KiDZyYf3tEUOpgq8BW-AU9SYtNT1A")

# Create model using a lighter version
MODEL_NAME = "models/gemini-2.0-flash-lite"

# HTML Templates as strings
HOME_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Vigilant - Cybercrime Intelligence</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body, html {
            height: 100%;
            margin: 0;
            padding: 0;
            background: #0a0f0a;
            font-family: 'Arial', sans-serif;
            color: #00ffb0;
            overflow: hidden;
        }
        
        #particles-js {
            position: fixed;
            width: 100vw;
            height: 100vh;
            z-index: 0;
            pointer-events: none;
        }
        
        .container {
            position: relative;
            z-index: 1;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        
        h1 {
            font-size: 3.5em;
            margin-bottom: 20px;
            text-shadow: 0 0 20px #00ffb0;
        }
        
        .description {
            font-size: 1.2em;
            margin-bottom: 40px;
            color: #baffea;
        }
        
        .chat-button {
            display: inline-block;
            padding: 20px 40px;
            font-size: 1.4em;
            background: #00ffb0;
            color: #0a0f0a;
            text-decoration: none;
            border-radius: 10px;
            transition: all 0.3s ease;
            border: 2px solid #00ffb0;
        }
        
        .chat-button:hover {
            background: #0a0f0a;
            color: #00ffb0;
            box-shadow: 0 0 30px #00ffb0;
            transform: scale(1.05);
        }
        
        .features {
            margin-top: 60px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            width: 100%;
            max-width: 1000px;
        }
        
        .feature-card {
            background: rgba(0, 255, 176, 0.1);
            padding: 30px;
            border-radius: 15px;
            border: 1px solid #00ffb055;
            transition: all 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 0 20px #00ffb055;
        }
        
        .feature-icon {
            font-size: 2em;
            margin-bottom: 15px;
        }
        
        .feature-title {
            font-size: 1.2em;
            margin-bottom: 10px;
            color: #00ffb0;
        }
    </style>
</head>
<body>
    <div id="particles-js"></div>
    <div class="container">
        <h1>Vigilant Cybercrime Intelligence</h1>
        <p class="description">Your AI-powered cybersecurity assistant with advanced threat intelligence capabilities</p>
        <a href="/chat" class="chat-button">Start Conversation</a>
        <div class="features">
            <div class="feature-card">
                <div class="feature-icon">🔒</div>
                <div class="feature-title">Advanced Security Analysis</div>
                <p>Real-time threat assessment and security recommendations</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <div class="feature-title">AI-Powered Insights</div>
                <p>Cutting-edge AI technology for accurate threat detection</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Threat Intelligence</div>
                <p>Comprehensive cybercrime data analysis and reporting</p>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
    <script>
        particlesJS('particles-js', {
            particles: {
                number: { value: 80, density: { enable: true, value_area: 800 } },
                color: { value: '#00ffb0' },
                shape: { type: 'circle' },
                opacity: { value: 0.5, random: true },
                size: { value: 3, random: true },
                line_linked: {
                    enable: true,
                    distance: 150,
                    color: '#00ffb0',
                    opacity: 0.4,
                    width: 1
                },
                move: {
                    enable: true,
                    speed: 2,
                    direction: 'none',
                    random: true,
                    straight: false,
                    out_mode: 'out'
                }
            }
        });
    </script>
</body>
</html>
'''

CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Vigilant - Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body, html {
            height: 100%;
            margin: 0;
            padding: 0;
            background: #0a0f0a;
            font-family: 'Arial', sans-serif;
            overflow: hidden;
        }
        
        .chat-container {
            max-width: 1000px;
            margin: 20px auto;
            height: calc(100vh - 40px);
            background: rgba(10, 20, 10, 0.95);
            border-radius: 20px;
            box-shadow: 0 0 40px #00ffb055;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            padding: 20px;
            background: rgba(0, 255, 176, 0.1);
            border-bottom: 1px solid #00ffb055;
        }
        
        .chat-title {
            color: #00ffb0;
            margin: 0;
            font-size: 1.5em;
            text-shadow: 0 0 10px #00ffb055;
        }
        
        .chat-messages {
            flex-grow: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .message {
            max-width: 80%;
            padding: 15px;
            border-radius: 15px;
            line-height: 1.4;
        }
        
        .user-message {
            background: #00ffb0;
            color: #0a0f0a;
            align-self: flex-end;
            border-bottom-right-radius: 5px;
        }
        
        .bot-message {
            background: rgba(0, 255, 176, 0.1);
            color: #00ffb0;
            align-self: flex-start;
            border-bottom-left-radius: 5px;
        }
        
        .chat-input-container {
            padding: 20px;
            background: rgba(0, 255, 176, 0.1);
            border-top: 1px solid #00ffb055;
        }
        
        .chat-input-wrapper {
            display: flex;
            gap: 10px;
            max-width: 100%;
        }
        
        #message-input {
            flex-grow: 1;
            padding: 15px;
            border: 2px solid #00ffb0;
            background: rgba(10, 20, 10, 0.8);
            color: #00ffb0;
            border-radius: 10px;
            font-size: 1em;
            outline: none;
            transition: all 0.3s ease;
        }
        
        #message-input:focus {
            box-shadow: 0 0 15px #00ffb055;
        }
        
        #send-button {
            padding: 15px 30px;
            background: #00ffb0;
            color: #0a0f0a;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        #send-button:hover {
            background: #0a0f0a;
            color: #00ffb0;
            box-shadow: 0 0 15px #00ffb055;
            border: 2px solid #00ffb0;
        }
        
        .typing-indicator {
            display: none;
            color: #00ffb0;
            font-style: italic;
            margin: 10px 0;
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(10, 20, 10, 0.8);
        }
        
        ::-webkit-scrollbar-thumb {
            background: #00ffb0;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #00cc8c;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1 class="chat-title">Vigilant Cybersecurity Assistant</h1>
        </div>
        <div class="chat-messages" id="chat-messages"></div>
        <div class="typing-indicator" id="typing-indicator">Assistant is typing...</div>
        <div class="chat-input-container">
            <div class="chat-input-wrapper">
                <input type="text" id="message-input" placeholder="Type your message...">
                <button id="send-button">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const chatMessages = document.getElementById('chat-messages');
        const typingIndicator = document.getElementById('typing-indicator');
        
        function addMessage(message, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            messageDiv.textContent = message;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            messageInput.value = '';
            addMessage(message, true);
            
            typingIndicator.style.display = 'block';
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message })
                });
                
                const data = await response.json();
                typingIndicator.style.display = 'none';
                addMessage(data.response, false);
            } catch (error) {
                typingIndicator.style.display = 'none';
                addMessage('Error: Could not reach the server.', false);
            }
        }
        
        // Add welcome message
        window.addEventListener('load', () => {
            addMessage("Hello! I'm your Vigilant Cybersecurity Assistant. How can I help you today?", false);
        });
        
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
'''

class RateLimiter:
    def __init__(self, max_requests_per_minute=10):
        self.max_requests = max_requests_per_minute
        self.requests = []
    
    def wait_if_needed(self):
        now = datetime.now()
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < timedelta(minutes=1)]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = 61 - (now - self.requests[0]).total_seconds()
            if sleep_time > 0:
                print(f"Rate limit reached. Waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
            self.requests = self.requests[1:]
        
        self.requests.append(now)

class CybercrimeChatbot:
    def __init__(self):
        self.is_sarcasm_enabled = False
        self.model = genai.GenerativeModel(MODEL_NAME)
        self.conversation_history = []
        # Initialize all modes
        self.expert_mode = False
        self.hacker_mode = False
        self.defense_mode = False
        self.analysis_mode = False
        self.ai_insights_mode = False
        self.threat_intel_mode = False
        print("Chatbot initialized successfully")

    def get_response(self, query):
        command_response = self._handle_command(query.lower().strip())
        if command_response:
            return command_response

        # Check for exact matches first
        if query == "WHO MADE YOU":
            return "I WAS MADE BY ANUJ PHULERA FROM GPCSSI (CA 44)"
        elif query.lower() == "who made you":
            return "I AM VIGILANT AI MADE BY ANUJ PHULERA (CA 44)"
        elif "who made you" in query.lower() or "who created you" in query.lower():
            return "I AM VIGILANT AI MADE BY ANUJ PHULERA (CA 44)"

        try:
            # Build conversation history string
            history_context = ""
            if self.conversation_history:
                history_context = "Previous conversation:\n"
                for entry in self.conversation_history[-3:]:
                    history_context += f"{'User' if entry['role'] == 'user' else 'Assistant'}: {entry['content']}\n"
                history_context += "\n"

            # Build mode-specific instructions
            mode_instructions = ""
            if self.analysis_mode:
                mode_instructions = """
                You are in ADVANCED SECURITY ANALYSIS mode:
                - Perform real-time threat assessment
                - Provide specific security recommendations
                - Analyze potential vulnerabilities
                - Suggest concrete security measures
                - Include risk levels and impact analysis
                - Recommend security tools and configurations
                """
            elif self.ai_insights_mode:
                mode_instructions = """
                You are in AI-POWERED INSIGHTS mode:
                - Use cutting-edge AI analysis techniques
                - Provide predictive threat detection
                - Identify patterns in cyber attacks
                - Suggest AI-driven security solutions
                - Analyze behavioral patterns
                - Offer machine learning-based recommendations
                """
            elif self.threat_intel_mode:
                mode_instructions = """
                You are in THREAT INTELLIGENCE mode:
                - Provide comprehensive cybercrime analysis
                - Include latest threat intelligence data
                - Analyze current cyber attack trends
                - Report on emerging threats
                - Suggest threat hunting strategies
                - Include IOCs and threat indicators
                """
            elif self.expert_mode:
                mode_instructions = """
                You are in EXPERT mode:
                - Use advanced cybersecurity terminology
                - Include technical details and CVE references
                - Mention specific tools and techniques
                - Provide actionable insights
                """
            elif self.hacker_mode:
                mode_instructions = """
                You are in HACKER mode:
                - Focus on offensive security perspectives
                - Discuss penetration testing methodologies
                - Explain attack vectors and vulnerabilities
                - Always emphasize ethical hacking and legal compliance
                """
            elif self.defense_mode:
                mode_instructions = """
                You are in DEFENSE mode:
                - Focus on protective measures and best practices
                - Provide specific mitigation strategies
                - Include MITRE ATT&CK framework references
                - Emphasize incident response procedures
                """

            prompt = f"""You are VIGILANT AI, an advanced cybersecurity assistant with comprehensive threat intelligence capabilities. Provide concise, direct answers without asterisks or special formatting.

            {mode_instructions}
            {history_context}
            Current Question: {query}
            
            Guidelines:
            1. Keep answers short and direct unless details are requested
            2. Don't use asterisks or special formatting
            3. Provide real-world examples when relevant
            4. Include specific tool names and commands if applicable
            5. Reference recent cyber threats when appropriate
            6. Use context from previous messages when relevant
            7. If asked about hacking, emphasize ethical and legal aspects
            8. For technical questions, include practical implementation steps
            9. Always include actionable recommendations
            10. Prioritize real-time threat assessment when relevant
            
            {'Use a sarcastic, witty tone but keep it brief.' if self.is_sarcasm_enabled else 'Use a professional, direct tone.'}
            """
            
            response = self.model.generate_content(prompt, safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ])
            
            response_text = response.text.strip() if response and response.text else "PLEASE TRY AGAIN"
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": query})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            # Keep history manageable (last 10 exchanges)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return response_text
            
        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            return "PLEASE TRY AGAIN"

    def _handle_command(self, command):
        if command == "/sarcasm":
            self.is_sarcasm_enabled = not self.is_sarcasm_enabled
            return f"Sarcasm mode is now {'enabled' if self.is_sarcasm_enabled else 'disabled'}."
        elif command == "/analysis":
            self._reset_modes()
            self.analysis_mode = True
            return "Advanced Security Analysis mode activated. I will provide real-time threat assessment and security recommendations."
        elif command == "/ai":
            self._reset_modes()
            self.ai_insights_mode = True
            return "AI-Powered Insights mode activated. Using cutting-edge AI for accurate threat detection."
        elif command == "/intel":
            self._reset_modes()
            self.threat_intel_mode = True
            return "Threat Intelligence mode activated. Providing comprehensive cybercrime data analysis and reporting."
        elif command == "/expert":
            self._reset_modes()
            self.expert_mode = True
            return "Expert mode activated. Using technical terminology and detailed analysis."
        elif command == "/hacker":
            self._reset_modes()
            self.hacker_mode = True
            return "Hacker mode activated. Focusing on offensive security and ethical hacking."
        elif command == "/defense":
            self._reset_modes()
            self.defense_mode = True
            return "Defense mode activated. Focusing on protective measures and incident response."
        elif command == "/clear":
            self.conversation_history = []
            return "Conversation history cleared."
        elif command == "/help":
            return """Available commands:
            Core Modes:
            /analysis - Advanced Security Analysis mode
            /ai - AI-Powered Insights mode
            /intel - Threat Intelligence mode
            
            Additional Modes:
            /expert - Expert technical mode
            /hacker - Offensive security mode
            /defense - Defensive security mode
            /sarcasm - Toggle sarcastic responses
            
            Other Commands:
            /clear - Clear conversation history
            /help - Show this help message"""
        elif command in ["/quit", "/exit"]:
            return "exit"
        return None

    def _reset_modes(self):
        """Reset all modes to False"""
        self.expert_mode = False
        self.hacker_mode = False
        self.defense_mode = False
        self.analysis_mode = False
        self.ai_insights_mode = False
        self.threat_intel_mode = False

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change this in production
CORS(app)

# Initialize chatbot and rate limiter
chatbot = CybercrimeChatbot()
rate_limiter = RateLimiter(max_requests_per_minute=5)

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE)

@app.route('/chat')
def chat_page():
    return render_template_string(CHAT_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    if not request.is_json:
        return jsonify({'response': 'PLEASE TRY AGAIN'}), 400
        
    user_message = request.get_json().get('message', '')
    if not user_message:
        return jsonify({'response': 'PLEASE TRY AGAIN'}), 400
        
    if 'history' not in session:
        session['history'] = []
    
    try:
        rate_limiter.wait_if_needed()
        response = chatbot.get_response(user_message)
        session['history'].append({'role': 'user', 'content': user_message})
        session['history'].append({'role': 'bot', 'content': response})
        return jsonify({'response': response})
    except Exception as e:
        print('API Error:', e)
        return jsonify({'response': 'PLEASE TRY AGAIN'}), 500

@app.route('/health')
def health():
    status = {
        'flask': True,
        'chatbot': chatbot is not None
    }
    return jsonify(status)

if __name__ == '__main__':
    app.run(debug=True)
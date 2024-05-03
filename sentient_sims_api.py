import traceback
import argparse
from flask import Flask, request, jsonify
from waitress import serve
from sentient_sims_logger import ss_logger

from sentient_sims_generator import SentientSimsGenerator

parser = argparse.ArgumentParser(description="Sentient Sims API")
parser.add_argument("--name", type=str, required=True, help="Worker name")
parser.add_argument("--model_path", type=str, required=True, help="Path to model folder")
parser.add_argument("--port", type=int, default=5000, help="Port number (default: 5000)")
parser.add_argument("--listen", action="store_true", required=False, help="Allow connection outside of localhost")

# Parse the command-line arguments
args = parser.parse_args()
worker_name = args.name
model_path = args.model_path
port = args.port

app = Flask(__name__)
generator = SentientSimsGenerator(model_path=model_path, max_token_length=4096)


class BadPromptRequestError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


@app.route('/health')
def health():
    return 'OK'


@app.route('/api/v1/model')
def model():
    return jsonify(result=generator.get_hf_model_name())


@app.route('/workers')
def workers():
    worker = {
        "busy": generator.is_busy(),
        "name": worker_name,
        "type": generator.get_gpu_name(),
        "model": generator.get_model_name(),
    }
    return jsonify([worker])


@app.route('/api/v1/generate', methods=['POST'])
def get_prompt_value():
    data = request.get_json()
    if 'prompt' in data:
        prompt = data['prompt']

    max_new_tokens = 100
    if 'max_new_tokens' in data:
        max_new_tokens = int(data['max_new_tokens'])

    try:
        output = generator.generate(prompt=prompt, max_new_tokens=max_new_tokens)

        return jsonify({
            'results': [
                {
                    'text': output
                }
            ]
        })
    except Exception as e:
        message = str(e)
        ss_logger.error(message)
        ss_logger.error(traceback.format_exc())
        return jsonify({'error': message}), 500

ss_logger.info(f"Starting worker: {worker_name}, type: {generator.get_gpu_name()}, model: {generator.get_model_name()}")

def startApi(listen: bool):
    ss_logger.info('Starting API Server')

    if listen:
        ss_logger.info(f'Listening on local network on port {port}')
        serve(app=app, host="0.0.0.0", port=port)
    else:
        ss_logger.info(f'Listening on localhost on port {port}')
        serve(app=app, port=port)

if __name__ == '__main__':
    startApi(args.listen)

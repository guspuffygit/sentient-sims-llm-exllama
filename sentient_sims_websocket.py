import ssl
from sentient_sims_api import BadPromptRequestError, generator, startApi, args, worker_name
import websocket
import time
import traceback
import threading
import json

def on_message(ws, message):
    try:
        prompt_request = json.loads(message)
        if 'prompt' in prompt_request:
            output = generator.generate(prompt=prompt_request['prompt'], max_new_tokens=100)
            ws.send(json.dumps({
                'results': [
                    {
                        'text': output
                    }
                ]
            }))
        else:
            raise BadPromptRequestError('No prompt in request')
    except Exception as e:
        error_message = str(e)
        print(error_message)
        print(traceback.format_exc())
        ws.send(json.dumps({
            "error": error_message
        }))


def on_error(ws, error):
    print(f"Error: {error}")


def on_close(w, close_status_code, close_msg):
    print("Connection closed. Reconnecting...")
    time.sleep(5)


def on_open(ws):
    print("Connection opened")


def connect_to_websocket():
    custom_headers = {
        "X-SentientSims-Worker-Name": worker_name,
        "X-SentientSims-Worker-Type": generator.get_gpu_name(),
        "X-SentientSims-Worker-Model": generator.get_model_name(),
    }

    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://ai.sentientsimulations.com:8443/ws",
                header=custom_headers,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            ws.on_open = on_open
            ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        except Exception as e:
            print(f"Error: {e}. Retrying...")

if __name__ == "__main__":
    print('Starting websocket')
    websocket_thread = threading.Thread(target=connect_to_websocket)
    websocket_thread.start()

    startApi(args.listen)

import os
import uuid

import grpc
from grpc._channel import _InactiveRpcError

from ai_pb2 import WorkRequest, WorkerInfo, WorkResponse
from ai_pb2_grpc import WorkerPoolStub
from sentient_sims_api import generator, startApi, args, worker_name
import time
import threading

worker_id = str(uuid.uuid4())

gpu_name = generator.get_gpu_name()
model_name = generator.get_model_name()

ssl_cert = 'sentient-simulations-grpc.crt'

def run():
    if not os.path.exists(ssl_cert):
        raise FileNotFoundError(f"The file {ssl_cert} does not exist.")
    while True:
        try:
            run_worker()
        except:
            print('Failed to connect to the grpc server')
            time.sleep(5)


def run_worker():
    credentials = grpc.ssl_channel_credentials(open(ssl_cert, 'rb').read())

    with grpc.secure_channel('ai.sentientsimulations.com:50050', credentials=credentials) as channel:
        print('Connected to the server')
        worker_pool = WorkerPoolStub(channel)

        while True:
            try:
                work_request: WorkRequest = worker_pool.Work(WorkerInfo(
                    workerId=worker_id,
                    workerName=worker_name,
                    gpuCount=1,
                    gpuType=gpu_name,
                ), timeout=15)
                print(f"request: {work_request.task}")
                output = generator.generate(prompt=work_request.task, max_new_tokens=100)
                worker_pool.CompleteWork(WorkResponse(text=output, taskid=work_request.taskid))
                print(f"done with request")
            except _InactiveRpcError as e:
                if e.details() == 'no work available' or e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    continue
                print(f"RPC error: {e}")
                time.sleep(5)
            except Exception as e:
                print(f"Unknown exception: {e}")
                time.sleep(5)


if __name__ == "__main__":
    print('Starting grpc client')
    websocket_thread = threading.Thread(target=run)
    websocket_thread.start()

    startApi(args.listen)

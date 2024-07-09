import os
import uuid
import grpc
from grpc._channel import _InactiveRpcError
from ai_pb2 import WorkRequest, WorkerInfo, WorkResponse
from ai_pb2_grpc import WorkerPoolStub
from sentient_sims_api import generator, startApi, args, worker_name
import time
import threading
from sentient_sims_generator import TooManyTokensError
from sentient_sims_logger import ss_logger
import signal

worker_id = str(uuid.uuid4())
gpu_name = generator.get_gpu_name()
model_name = generator.get_model_name()
ssl_cert = 'sentient-simulations-grpc.crt'

# Global flag to indicate whether the program should exit
should_exit = False

def signal_handler(signum, frame):
    global should_exit
    ss_logger.info("Received exit signal. Finishing current task and exiting...")
    should_exit = True

def run():
    if not os.path.exists(ssl_cert):
        raise FileNotFoundError(f"The file {ssl_cert} does not exist.")
    while not should_exit:
        try:
            run_worker()
        except Exception as e:
            ss_logger.error(f'Failed to connect to the grpc server: {e}')
            time.sleep(5)
    ss_logger.info('Gracefully stopped worker, exiting')
    os._exit(0)

def run_worker():
    credentials = grpc.ssl_channel_credentials(open(ssl_cert, 'rb').read())

    with grpc.secure_channel('ai.sentientsimulations.com:50050', credentials=credentials) as channel:
        ss_logger.info('Connected to the server')
        worker_pool = WorkerPoolStub(channel)

        while not should_exit:
            try:
                work_request: WorkRequest = worker_pool.Work(WorkerInfo(
                    workerId=worker_id,
                    workerName=worker_name,
                    gpuCount=1,
                    gpuType=gpu_name,
                ), timeout=15)
            except _InactiveRpcError as e:
                if e.details() == 'no work available' or e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    continue
                ss_logger.error(f"RPC error: {e}")
                time.sleep(5)
                continue
            except Exception as e:
                ss_logger.error(f"Unknown exception getting work: {e}")
                time.sleep(5)
                continue

            try:
                output = generator.generate(prompt=work_request.task, max_new_tokens=100)
                worker_pool.CompleteWork(WorkResponse(text=output, taskid=work_request.taskid))
                ss_logger.debug("Done with request")
            except TooManyTokensError as e:
                ss_logger.error(f'Too many tokens: {str(e)}')
                worker_pool.CompleteWork(WorkResponse(text=str(e), taskid=work_request.taskid))
            except Exception as e:
                ss_logger.error(f"Error processing work: {e}")
                worker_pool.CompleteWork(WorkResponse(text=str(e), taskid=work_request.taskid))
        ss_logger.info('Exited in run_worker')

if __name__ == "__main__":
    ss_logger.info('Starting grpc client')
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    grpc_thread = threading.Thread(target=run)
    grpc_thread.start()

    startApi(args.listen)

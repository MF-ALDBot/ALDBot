#!/usr/bin/env python3

import threading
import time
import json
import uuid
import zmq
import zmq.auth
import os
import numpy as np

# In a real system, consider something more robust than a plain dictionary.
jobs = {}  # job_id -> dict(progress=int, done=bool)

def background_worker(job_id, work_params, pub_socket):
    """
    Simulates a long-running job by counting from 0 to 100,
    publishing status updates along the way.
    """
    # for i in range(101):
    #     time.sleep(0.05)  # Simulate work
    #     jobs[job_id]["progress"] = i
    #     # Publish progress as JSON
    #     update = {
    #         "job_id": job_id,
    #         "progress": i,
    #         "done": False
    #     } 
    #     print(f"PUB update: {update}")
    #     pub_socket.send_string(json.dumps(update))

    import bayesian_optimizer
    response = bayesian_optimizer.Get_New_Points_With_GP(**work_params)

    # Mark job as done
    jobs[job_id]["done"] = True
    update = {
        "job_id": job_id,
        "progress": 100,
        "done": True,
        "response": response,
    }
    print(f"PUB update: {update}")

    class NumpyArrayEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return json.JSONEncoder.default(self, obj)

    pub_socket.send_string(json.dumps(update, cls = NumpyArrayEncoder))

def main():
    # Load server keys
    certs_dir = "zmq_certs"
    #server_public_file = os.path.join(certs_dir, "server.key")
    server_secret_file = os.path.join(certs_dir, "server.key_secret")

    server_public, server_secret = zmq.auth.load_certificate(server_secret_file)

    context = zmq.Context.instance()

    # 1) REQ/REP socket for job submission
    rep_socket = context.socket(zmq.REP)
    # rep_socket.setsockopt(zmq.CURVE_SECRETKEY, server_secret)
    # rep_socket.setsockopt(zmq.CURVE_PUBLICKEY, server_public)
    # rep_socket.setsockopt(zmq.CURVE_SERVER,True)
    rep_socket.bind("tcp://0.0.0.0:5555")

    # 2) PUB socket for status updates
    pub_socket = context.socket(zmq.PUB)
    # Typically, for PUB sockets, you can use the same keys OR a separate key pair.
    # For simplicity, we use the same server keys here.
    # pub_socket.setsockopt(zmq.CURVE_SECRETKEY, server_secret)
    # pub_socket.setsockopt(zmq.CURVE_PUBLICKEY, server_public)
    # pub_socket.setsockopt(zmq.CURVE_SERVER,True)
    pub_socket.bind("tcp://0.0.0.0:5556")

    print("Server is running. REP on tcp://*:5555, PUB on tcp://*:5556")

    while True:
        # Receive a job submission request
        msg = rep_socket.recv_string()
        try:
            request = json.loads(msg)
            if request["method"] == "Get_New_Points_With_GP":
                job_id = str(uuid.uuid4())
                jobs[job_id] = {"progress": 0, "done": False}
                
                # Dispatch background worker
                params = request.get("params", {})
                t = threading.Thread(target=background_worker,
                                     args=(job_id, params, pub_socket))
                t.daemon = True
                t.start()

                reply = {"status": "ok", "job_id": job_id}
            else:
                reply = {"status": "error", "error": "Unknown method"}
        except Exception as e:
            reply = {"status": "error", "error": str(e)}

        print(f"REP {reply}")
        rep_socket.send_string(json.dumps(reply))

if __name__ == "__main__":
    main()
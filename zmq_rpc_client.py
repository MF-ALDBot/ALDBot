import zmq
import zmq.auth
import json
import os
import sys

def submit_zmq_job_and_wait(job_name, **kwargs):
    # Load client + server keys
    certs_dir = "zmq_certs"
    client_public_file = os.path.join(certs_dir, "client.pub")
    client_secret_file = os.path.join(certs_dir, "client.key_secret")
    server_public_file = os.path.join(certs_dir, "server.pub")

    server_public_file = os.path.join(certs_dir, "server.key")
    server_public, _ = zmq.auth.load_certificate(server_public_file)

    client_public, client_secret = zmq.auth.load_certificate(client_secret_file)

    context = zmq.Context.instance()

    # 1) REQ socket => connect to server for job submission
    req_socket = context.socket(zmq.REQ)
    # req_socket.setsockopt(zmq.CURVE_SECRETKEY, client_secret)
    # req_socket.setsockopt(zmq.CURVE_PUBLICKEY, client_public)
    # req_socket.setsockopt(zmq.CURVE_SERVERKEY, server_public)  
    req_socket.setsockopt(zmq.RCVTIMEO, 3000) 
    req_socket.connect("tcp://131.243.183.105:5555")

    #131.243.183.105
    # 2) SUB socket => subscribe to status updates
    sub_socket = context.socket(zmq.SUB)
    # sub_socket.setsockopt(zmq.CURVE_SECRETKEY, client_secret)
    # sub_socket.setsockopt(zmq.CURVE_PUBLICKEY, client_public)
    # sub_socket.setsockopt(zmq.CURVE_SERVERKEY, server_public)
    sub_socket.connect("tcp://esbstudio.dhcp.lbl.gov:5556")

    # We subscribe to everything, then filter the job_id in code.
    # Alternatively, you can use a topic-based scheme.
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

    # Submit a job
    request = {
        "method": job_name,
        "params": kwargs
    }
    print(f"submit job {request}")
    req_socket.send_string(json.dumps(request))
    reply_raw = req_socket.recv_string()
    reply = json.loads(reply_raw)
    print("reply")

    if reply["status"] != "ok":
        raise IOError(f"ERROR: {reply.get('error')}")

    job_id = reply["job_id"]
    print(f"[Client] Submitted job. job_id = {job_id}")

    # Listen for PUB updates until job is done
    print("[Client] Waiting for status updates...")
    while True:
        msg = sub_socket.recv_string()
        update = json.loads(msg)

        # If you're receiving many updates, you might filter by job_id here
        if update["job_id"] == job_id:
            print(f"[Status] job_id={update['job_id']} ", end="")
            print(f"progress={update['progress']} ", end="")
            print(f"done={update['done']}")

            if update["done"]:
                print("[Client] Job is complete. Exiting.")
                return update['response']

if __name__ == '__main__':
    submit_zmq_job_and_wait("Get_New_Points_With_GP")
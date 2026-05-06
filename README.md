# Wraith

## Background

Just some C implant inspired by [Khael's](https://github.com/KhaelK138) [PhantomShell](https://github.com/KhaelK138/PhantomShell) so that I can learn
more about C networking and packets on raw sockets and whatnot. This tool is primarily educational, but I may use it when red teaming for attack / defense competitions, who knows

The Wraith agent listens on a `PF_PACKET` raw socket, allowing it to capture and inspect Ethernet-level traffic arriving to the host before it is processed by standard TCP/UDP socket layers, essentially like a network / packet sniffer

This allows the agent to read / parse inbound traffic, even if there's a host based firewall blocking packet delivery to applications or the absence of a listening service on the destination port. In other words, the agent can observe commands sent to the host on arbitrary destination ports, as long as the packets reach the network interface. It doesn't matter if there's nothing listening on that port

The Wraith agent can pick up both TCP and UDP traffic

Again, shoutout to Khael, I basically just wrote my own version of [PhantomShell](https://github.com/KhaelK138/PhantomShell) from the ground up. PhantomShell is a million times better though, use that instead

## Setup

Run the `wraith` agent on the victim device. Must be running with `sudo` permissions in order to listen on the raw socket with `PF_PACKET`

Use `wraithshell.py` from your attack box to interact with remote `Wraith` agents

I recommend creating and using a python virtual environment

```
python3 -m venv env
source env/bin/activate
```

Then install requirements

```
pip install -r requirements.txt
```

You can now run `wraithshell.py`. Do note that this also requires sudo privileges

## Usage

In `wraithshell.py` just run `help` to see all available commands, then run `help <command>` to see details on that specific command

Current commands so far are listed below

```
target - Set the IP and port (Specific port is optional, defaults to random port) of the vicitm machine

exec - Send commands for the remote agent to execute on the victim machine. Can execute blind for no returned output

listener - Start and stop local listener (used to receive pings and command output from remote agents)

ping - Have remote Wraith agent on victim machine ping the local machine

protocol - Switch between sending tcp or udp packets
```
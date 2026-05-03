# Wraith

## Background

Just some C implant inspired by Khael's [PhantomShell](https://github.com/KhaelK138/PhantomShell) so that I can learn
more about C networking and packets on raw sockets and whatnot. This tool is primarily educational, but I may use it when red teaming for attack / defense competitions, who knows

The Wraith agent listens on a `PF_PACKET` raw socket, allowing it to capture and inspect Ethernet-level traffic arriving to the host before it is processed by standard TCP/UDP socket layers, essentially like a network / packet sniffer

This allows the agent to read / parse inbound traffic, even if there's a host based firewall blocking packet delivery to applications or the absence of a listening service on the destination port. In other words, the agent can observe commands sent to the host on arbitrary destination ports, as long as the packets reach the network interface. It doesn't matter if there's nothing listening on that port

The Wraith agent can pick up both TCP and UDP traffic

Again, shoutout to Khael, I basically just wrote my own version of [PhantomShell](https://github.com/KhaelK138/PhantomShell) from the ground up. PhhantomShell is a million times better

Still a work in progress
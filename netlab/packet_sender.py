#!/usr/bin/env python3
import argparse
from scapy.all import IP, UDP, TCP, send, Net

def parse_port_range(port_str):
    """Parse port range string like '4001-4004' or single port like '4001'"""
    if '-' in port_str:
        start, end = port_str.split('-')
        return range(int(start), int(end) + 1)
    else:
        return [int(port_str)]

def parse_networks(net_str):
    """Parse network string like '10.0.42.4/32' or '10.0.42.0/24'"""
    return Net(net_str)

def main():
    parser = argparse.ArgumentParser(
        description='Send packets to test ECMP behavior based on source address only'
    )
    
    parser.add_argument(
        '--dnet',
        required=True,
        help='Destination network(s) in CIDR format (e.g., 10.0.42.4/32)'
    )
    
    parser.add_argument(
        '--sip',
        required=True,
        help='Source IP address (e.g., 10.1.1.1)'
    )
    
    parser.add_argument(
        '--sport',
        required=True,
        help='Source port(s) - single port or range (e.g., 4001 or 4001-4004)'
    )
    
    parser.add_argument(
        '--dport',
        required=True,
        help='Destination port(s) - single port or range (e.g., 5001 or 5001-5004)'
    )
    
    parser.add_argument(
        '--protocol',
        choices=['udp', 'tcp', 'both'],
        default='both',
        help='Protocol to use (udp, tcp, or both)'
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of packets to send per combination (default: 1)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=0,
        help='Delay in seconds between packets (default: 0)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show packet details'
    )
    
    args = parser.parse_args()
    
    # Parse command line arguments
    src_ip = args.sip
    dst_networks = parse_networks(args.dnet)
    sport_range = parse_port_range(args.sport)
    dport_range = parse_port_range(args.dport)
    
    # Statistics
    packet_count = 0
    if args.verbose:
        print("=== ECMP Test Configuration ===")
        print(f"Source IP: {src_ip}")
        print(f"Destination networks: {args.dnet}")
        print(f"Source ports: {list(sport_range)}")
        print(f"Destination ports: {list(dport_range)}")
        print(f"Protocol(s): {args.protocol}")
        print(f"Packets per combination: {args.count}")
        print(f"Delay: {args.delay}s")
        print("===============================\n")
    
    # Send packets
    for dst_ip in dst_networks:
        for sport in sport_range:
            for dport in dport_range:
                
                # UDP packets
                if args.protocol in ['udp', 'both']:
                    udp_pkt = IP(src=src_ip, dst=str(dst_ip)) / UDP(sport=sport, dport=dport)
                    for i in range(args.count):
                        if args.verbose:
                            print(f"Sending UDP: {src_ip}:{sport} -> {dst_ip}:{dport}")
                        send(udp_pkt, verbose=False)
                        packet_count += 1
                        if args.delay > 0 and (i < args.count - 1):
                            time.sleep(args.delay)
                
                # TCP packets
                if args.protocol in ['tcp', 'both']:
                    tcp_pkt = IP(src=src_ip, dst=str(dst_ip)) / TCP(sport=sport, dport=dport)
                    for i in range(args.count):
                        if args.verbose:
                            print(f"Sending TCP: {src_ip}:{sport} -> {dst_ip}:{dport}")
                        send(tcp_pkt, verbose=False)
                        packet_count += 1
                        if args.delay > 0 and (i < args.count - 1):
                            time.sleep(args.delay)
                
                # Delay between different flows if specified
                if args.delay > 0 and (sport != sport_range[-1] or dport != dport_range[-1]):
                    time.sleep(args.delay)
    
    print("\n=== Summary ===")
    print(f"Total packets sent: {packet_count}")
    print(f"Unique flows: {len(list(dst_networks)) * len(sport_range) * len(dport_range) * (2 if args.protocol == 'both' else 1)}")
    print("===============")

if __name__ == "__main__":
    import time
    main()
import argparse
from scapy.all import IP, RandIP, TCP, send
import random
import time


def main():
    parser = argparse.ArgumentParser(
        description='Send random IP and TCP ports packet'
    )
    
    parser.add_argument(
        '--count',
        required=True,
        help='Packets count'
    )
    args = parser.parse_args()
    
    pkt_count = int(args.count)
    
    packet_count = 0

    for i in range(pkt_count):
        src_port = random.randint(1025, 65534)
        dst_port = random.randint(1025, 65534)
        packet = IP(dst=RandIP('10.0.42.0/24'), src=RandIP()) / TCP(sport=src_port, dport=dst_port)
        send(packet, verbose=False)
        packet_count += 1

    print("\n=== Summary ===")
    print(f"Total packets sent: {packet_count}")
    print("===============")

if __name__ == "__main__":

    start_time = time.perf_counter()
    main()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Function 'my_function' executed in: {elapsed_time:.4f} seconds")
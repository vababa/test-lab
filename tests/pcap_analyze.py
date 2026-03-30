from scapy.all import rdpcap, IP
from scapy.error import Scapy_Exception
from typing import List
import argparse


class TestSuite:
    lo_network = '10.1.1.'
    p2p_network = '10.0.24.'
    lan_network = '10.0.42.'

    def __init__(self, links_count: int, pcap_folder: str) -> None:
        self.links: int = links_count
        self.pcap_folder: str = pcap_folder
        self.lps_test_results: List = [[0 for i in range(self.links)] for j in range(self.links)]
        self.rps_test_results: List = [0 for i in range(self.links)]

    def __str__(self) -> str:
        result: str = 'Тест А: [\n'
        for i in range(self.links):
            result += f'тест {i}: {str(self.lps_test_results[i])}\n'
        result += ']\n'
        result += f'Тест Б: {self.rps_test_results}'
        return result
        
    def process_lps_pcaps(self) -> None:
        tests = self.links
        for i in range(tests):
            for j in range(self.links):
                pcap_path = f'{self.pcap_folder}/lps_test{i+1}_link{j+1}.pcap'
                # print(pcap_path)
                try:
                    pcap = rdpcap(pcap_path)
                except Scapy_Exception as e:
                    if str(e) == "No data could be read!":
                        pcap = []
                    else:
                        raise
                for packet in pcap:
                    src_ip = f'{self.lo_network}{i % self.links + 1}'
                    if IP in packet and packet[IP].src == src_ip:
                        # print('IP yes')
                        self.lps_test_results[i][j] = 1
    
    def process_rps_pcaps(self):
        for i in range(self.links):
            pcap_path = f'{self.pcap_folder}/rps_link{i+1}.pcap'
            try:
                pcap = rdpcap(pcap_path)
            except Scapy_Exception as e:
                if str(e) == "No data could be read!":
                    pcap = []
                else:
                    raise
            self.rps_test_results[i] = len(pcap)

    def check_test_a_criteria(self):
        [sum(test) for test in self.lps_test_results]
            

            

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Анализирует pcap-файлы ECMP-тестов')
    
    parser.add_argument(
        '--links',
        required=True,
        help='Количество ECMP-линков в тестовой топологии.'
    )
    args = parser.parse_args()

    suite = TestSuite(int(args.links), './captures')
    suite.process_lps_pcaps()
    suite.process_rps_pcaps()
    print(suite)

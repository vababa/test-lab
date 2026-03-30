from jinja2 import Environment, FileSystemLoader
import argparse


def render_j2(template_name, data):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(f'{template_name}.tmpl')
    output = template.render(**data)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('links', type=int, help='Количество линков')
    args = parser.parse_args()

    links = args.links
    links_list = [i+1 for i in range(links)]

    with open('packet_sender.py', 'r') as fh:
        lps = fh.read()
    with open('random_packet_sender.py', 'r') as fh:
        rps = fh.read()
    
    for i in [1, 2]:
        h_config = render_j2('config_h', {
            'ips': links_list, 
            'links_packet_sender': lps,
            'random_packet_sender': rps,
            })
        with open(f"config_h{i}.j2", "w") as fh:
            fh.write(h_config)

    topology = render_j2('topology', {'links': links_list})
    with open("topology.yml", "w") as fh:
        fh.write(topology)

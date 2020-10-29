import json
import subprocess

class LocalCallableManager:
    def __init__(self, config):
        self.config = config
        self.module_to_container_id = {}
    
    def start_containers(self):
        with open(self.config, 'r') as config_file:
            self.config = json.load(config_file) # will this persist?
            for module_name in self.config:
                if self.config[module_name]['url'] != 'none':
                    self.start_container(module_name)
            return
    
    def start_container(self, module_name):
        port = self.config[module_name]['port']
        docker_file_dir = self.config[module_name]['docker_file_dir']

        # check if container is already running
        running = subprocess.run(['docker', 'container', 'ls',
                                  '-q', '-f', 
                                  'name={}'.format(module_name)], 
                                  stdout=subprocess.PIPE)
        if running: return

        # build docker image
        subprocess.run(['docker', 'build', '-t', module_name,
                        docker_file_dir], check=True)

        # run the docker container
        container_process = subprocess.run(['docker', 'run', '-d', '--rm','-p',
                        '{}:80'.format(port),
                        '--name',
                        '{}'.format(module_name),
                        '{}:latest'.format(module_name)],
                        check=True, stdout=subprocess.PIPE)

        container_id = container_process.stdout.decode('utf-8').strip()
        self.module_to_container_id[module_name] = container_id
        
    def stop_containers(self):
       for container_id in self.module_to_container_id.values():
           subprocess.run(['docker', 'stop', container_id])
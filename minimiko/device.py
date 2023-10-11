import sys
import paramiko as pm
import os
import time

# silence silly warnings from paramiko
sys.stderr = open('/dev/null') 
sys.stderr = sys.__stderr__

class AllowAllKeys(pm.MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        return
    
class Device:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password

    def connect(self):
        # TODO: ssh path
        client = pm.SSHClient()
        client.load_system_host_keys()
        client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        client.set_missing_host_key_policy(AllowAllKeys())
        client.connect(self.host, username=self.user, password=self.password)
        return client

    def run(self, cmd):
        # TODO: check stderr
        client = self.connect()
        output = {}
        stdin, stdout, stderr = client.exec_command('')
        if type(cmd) == str:
            stdin.write(cmd + '\r')
        elif type(cmd) == list:
            stdin.write(' '.join(cmd) + '\r')
        else:
            output['error'] = 'command must be string or list'
            return output
        stdin.close()

        # convert output to dict
        # detect automatically two modes: table or key-value
        mode_table = False
        keys = []
        line_table = 0 
        for line in iter(stdout.readline, ''):
            # if cmd[0].endswith('/config'):
            #     print(line, end='')
            #     continue
            if line.count('|') == 2:
                mode_table = False
            elif line.count('|') == 3:
                continue
            elif line.count('|') > 2:
                if mode_table:
                    values = [i.rstrip() for i in line.rstrip()[1:-1].split('|')]
                    data = dict([key, values[idx]] for idx, key in enumerate(keys))
                    output[line_table] = data
                    line_table += 1

                else:
                    mode_table = True
                    #if not keys:
                    # get keys
                    keys = [i.rstrip().lower().replace(' ', '_') for i in line.rstrip()[1:-1].split('|')]

            if ':' in line and not mode_table:
                idx = line.find(':')
                key = line[:idx].lower().lstrip().replace(' ', '_')
                value = line[idx+1:].lstrip().rstrip()
                if not key in output:
                    output[key] = value
                else:
                    if not f'_{key}' in output:
                        output[f'_{key}'] = value
                    else:
                        print(f'warning, key already exists: _{key}')
        client.close()
        return output

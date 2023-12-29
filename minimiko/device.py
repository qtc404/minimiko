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
    def __init__(self, host, user, password, debug=False):
        self.host = host
        self.user = user
        self.password = password
        self.debug = debug

    def connect(self):
        # TODO: ssh path
        client = pm.SSHClient()
        client.load_system_host_keys()
        client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        client.set_missing_host_key_policy(AllowAllKeys())
        client.connect(self.host, username=self.user, password=self.password)
        return client

    def run(self, cmd, key_in_line=False):
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
        line_table = 0
        # real_key = ''
        # levels = []
        keys = []
        spaces = [0]
        header = True
        header_lines = 2
        reset = False
        for line in iter(stdout.readline, ''):
            original_line = line.replace('\n', '')
            line = original_line.replace('-', '')
            # do not read lines from header
            if header:
                if '=' in line:
                    header_lines -= 1
                    if header_lines == 0:
                        header = False
                continue

            # TODO: televes cli
            if line.startswith('/cli>'):
                continue

            if len(line) == 0:
                if '---' in original_line:
                    reset = True
                else:
                    continue

            if self.debug:
                print('...', line, len(line))

            # CASE A
            if line.count('|') == 2:
                mode_table = False 
            elif line.count('|') == 3 and not key_in_line:
                continue
            elif line.count('|') > 2 or key_in_line:
                if mode_table:
                    values = [i.rstrip() for i in line.rstrip()[1:-1].split('|')]
                    if not key_in_line:
                        data = dict([key, values[idx]] for idx, key in enumerate(keys))
                        output[line_table] = data
                        line_table += 1
                    elif len(values) == 2:
                        output[values[0]] = values[1]
                else:
                    mode_table = True
                    #if not keys:
                    # get keys
                    keys = [i.rstrip().lower().replace(' ', '_') for i in line.rstrip()[1:-1].split('|')]
            # CASE B
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
            # CASE C
            else:
                # --- line
                if reset:
                    keys = []
                    spaces = []
                    reset = False
                    continue

                s = len(line) - len(line.lstrip())
                l = line.replace('=', '').strip()
                #line_split = l.split()
                line_split = [t.strip() for t in l.split('  ') if t]
                print('spaces:', s, spaces, keys, line_split)

                if len(line_split):
                    if len(line_split) == 1: # and not spaces:
                        if not spaces:
                            key = line_split[0]
                            spaces.append(s)
                            keys.append(key)
                        else:
                            values = line_split[0].split()
                            if len(values) == 2:
                                key = '_'.join(keys) + '_' + values[1]
                                output[key.lower()] = value = values[0]
                            else:
                                spaces[-1] = s
                                keys[-1] = values[0]
                        continue
                    if len(line_split) == 2: # and not spaces:
                        if keys:
                            key = '_'.join(keys)
                            value = line_split[1]
                        else:
                            key = line_split[0].replace(' ', '_').lower()
                            value = ' '.join(line_split[1:])
                        output[key.lower()] = value
                        continue
                else:
                    if spaces:
                        spaces.pop()
                        keys.pop()
                continue

        return output
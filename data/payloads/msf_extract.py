import argparse
import json
import logging
import multiprocessing
import platform
import re
import requests
import subprocess
import urllib3
import uuid

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)


def get_exploits():
    try:
        return get_exploits_api(args.api_key)
    except:
        return get_exploits_msfconsole()


def get_exploits_msfconsole():
    try:
        result = subprocess.run(['msfconsole', '-x', 'show exploits; exit;'], stdout=subprocess.PIPE)
    except:
        result = subprocess.run(['/opt/metasploit-framework/bin/msfconsole', '-x', 'show exploits; exit;'],
                                stdout=subprocess.PIPE)

    return msfconsole_parse_exploits(result.stdout)


def msfconsole_parse_exploits(exploit_result):
    results = exploit_result.decode().split('\n')
    exploits = []
    for l in results[results.index('Exploits') + 5::]:
        if not len(l):
            continue
        try:
            exploits.append(l.split()[1].strip())
        except:
            continue
    return exploits


def msfconsole_parse_exploit_info(exploit_info):
    exploit_ability = dict(
        name=None,
        test=None,
        description='metasploit exploit',
        platform=None,
        privilege=None,
        module=None,
        params=[]
    )
    for section in escape_ansi(exploit_info.decode()).split('\n\n'):
        try:
            section_key = section.strip().split(':')[0].strip()
            if section_key == 'Name':
                # info section
                for line in section.strip().split('\n'):
                    key, value = line.strip().split(':')
                    if key == 'Name':
                        exploit_ability['name'] = value.strip()
                    if key == 'Module':
                        exploit_ability['module'] = value.strip()
                    if key == 'Platform':
                        exploit_ability['platform'] = value.lower().strip()
                    if key == 'Privileged' and value.strip() == 'Yes':
                        exploit_ability['privilege'] = 'Elevated'
                continue
            elif section_key == 'Description':
                exploit_ability['description'] = ''.join([s.strip() for s in section.split(':')[1].split('\n')])
            elif section_key == 'Basic options':
                for option in section.strip().split('\n')[3::]:
                    option_params = [x.strip() for x in option.split('  ') if x]
                    current_setting = None
                    if len(option_params) == 3:
                        name, required, description = option_params
                    elif len(option_params) == 4:
                        name, current_setting, required, description = option_params
                    else:
                        continue  # is there other options idk
                    exploit_ability['params'].append(dict(name=name,
                                                          current_setting=current_setting,
                                                          required=required,
                                                          description=description))
        except:
            logging.debug('brick')
            continue
    logging.debug(exploit_ability['name'])
    return exploit_ability


def msfconsole_get_exploit(exploit):
    result = subprocess.run(['msfconsole', '-q', '-x', f'info {exploit}; exit;'], stdout=subprocess.PIPE)
    return msfconsole_parse_exploit_info(result.stdout)


def get_exploits_api(msf_api_token):
    url = "https://localhost:5443/api/v1/modules?type=exploit"
    payload = {}
    headers = {'Authorization': 'Bearer ' + msf_api_token, }
    response = requests.request("GET", url, headers=headers, data=payload, verify=False)
    return json.loads(response.text.encode('utf8')).get('data', [])


def create_caldera_ability(c2_uri, c2_token, ability_data):
    payload = {}
    headers = {'Authorization': 'Bearer ' + c2_token, }
    response = requests.request("GET", c2_uri, headers=headers, data=payload, verify=False)
    return json.loads(response.text.encode('utf8')).get('data', [])


def convert_to_ability_format(exploit_info):
    test = ['msfconsole -x "use exploit/multi/samba/usermap_script; ']
    for param in exploit_info.get('params', []):
        test.append('set ' + param['name'] + ' ' + '#{msf.' + param['name'] + '};')
    test.append('run"')
    command = ' \n '.join(test)

    ability = {
        "id": str(uuid.uuid4()),
        "tactic": "metasploit",
        "technique": {
            "name": "metasploit",
            "attack_id": "MSF999"},
        "name": exploit_info.get('name'),
        "description": exploit_info.get('name'),
        "platforms": {
            platform.system().lower():
                {exploit_info.get('executor', 'sh'): {
                    "command": command,
                    "timeout": 600,
                }}
        },
        "privilege": exploit_info.get('privilege', ''),
    }
    ability['unique'] = ability['id']
    return ability


def save_ability(c2_uri, c2_key, ability):
    url = c2_uri + "/api/rest"
    ability['index'] = 'abilities'
    payload = json.dumps(ability)
    headers = {
        'Content-Type': 'application/json',
        'KEY': c2_key,
    }
    requests.request("PUT", url, headers=headers, data=payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract Metasploit exploits.')
    parser.add_argument('-c', '--cores', default=multiprocessing.cpu_count(), help='cores for processing')
    parser.add_argument('-k', '--api-key', required=False, help='api key for faster gathering of data')
    parser.add_argument('--c2-uri', default='http://0.0.0.0:8888', help='c2 uri')
    parser.add_argument('--c2-key', default='ADMIN123', help='c2 api key')
    parser.add_argument('-v', '--verbosity', default=logging.INFO, help='log level')
    args = parser.parse_args()

    FORMAT = '%(message)s'
    logging.basicConfig(level=args.verbosity, format=FORMAT)

    exploits = get_exploits()
    for module in exploits:
        try:
            exploit = msfconsole_get_exploit(module['ref_name'])
            ability = convert_to_ability_format(exploit)
            save_ability(args.c2_uri, args.c2_key, ability)
        except:
            logging.error(module['ref_name'])


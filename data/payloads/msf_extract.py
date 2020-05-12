import argparse
import json
import logging
import multiprocessing
import requests
import subprocess
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_exploits():
    if args.api_key:
        exploits = get_exploits_api(args.api_key)
    else:
        exploits = get_exploits_msfconsole()
    return exploits

def get_exploits_msfconsole():
    try:
        result = subprocess.run(['msfconsole', '-x', 'show exploits; exit;'], stdout=subprocess.PIPE)
    except:
        result = subprocess.run(['/opt/metasploit-framework/bin/msfconsole', '-x', 'show exploits; exit;'], stdout=subprocess.PIPE)

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
    # properties = {
    #     'Name',
    #     'Module',
    #     'Platform',
    #     'Privileged',
    #     'Arch'
    # }
    # exploit_abilities = []
    exploit_ability = dict(
        name=None,
        test=None,
        description=None,
        platform=None,
        privilege=None,
        module=None,
        params=[]
    )
    # exploit_info_lines = exploit_info.decode().split('\n')
    for section in exploit_info[5::].decode().split('\n\n'):
        try:
            section_key = section.strip().split(':')[0]
            if section_key == 'Name':
                # info section
                for line in section.split('\n'):
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
    headers = {'Authorization': 'Bearer ' + msf_api_token,}
    response = requests.request("GET", url, headers=headers, data=payload, verify=False)
    return json.loads(response.text.encode('utf8')).get('data', [])


def create_caldera_ability(c2_uri, c2_token, ability_data):
    payload = {}
    headers = {'Authorization': 'Bearer ' + c2_token,}
    response = requests.request("GET", c2_uri, headers=headers, data=payload, verify=False)
    return json.loads(response.text.encode('utf8')).get('data', [])


def convert_to_ability_format():
    ability = {
        "id": "567eaaba-94cc-4a27-83f8-768e5638f4e1darwinsh",
        "ability_id": "567eaaba-94cc-4a27-83f8-768e5638f4e1",
        "tactic": "technical-information-gathering",
        "technique_name": "Conduct active scanning",
        "technique_id": "T1254",
        "name": "NMAP scan",
        "test": "Li9zY2FubmVyLnNoICN7dGFyZ2V0LmlwfQ==",
        "description": "Scan an external host for open ports and services",
        "cleanup": [],
        "executor": "sh",
        # "unique": "567eaaba-94cc-4a27-83f8-768e5638f4e1darwinsh",
        "platform": "darwin",
        # "payloads": [],
        # "parsers": [],
        # "requirements": [],
        "privilege": "",
        "timeout": 300,
        "buckets": [
            "technical-information-gathering"
        ],
        "access": 1,
        "variations": []
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract Metasploit exploits.')
    parser.add_argument('-c', '--cores', default=multiprocessing.cpu_count(), help='cores for processing')
    parser.add_argument('-k', '--api-key', required=False, help='api key for faster gathering of data',
                        default='21d92274ff018949148aef9c367e99aeae96870abe5ac98c952a29f3c46108ebc1aa43ba0c24c3af')
    parser.add_argument('--c2-uri', default='http://0.0.0.0:8888', help='c2 uri')
    parser.add_argument('--c2-key', default='', help='c2 api key')
    parser.add_argument('-v', '--verbosity', default=logging.INFO, help='log level')
    args = parser.parse_args()
    FORMAT = '%(message)s'
    logging.basicConfig(level=args.verbosity, format=FORMAT)

    # try api
    # get exploits
    #
    exploits = get_exploits()
    for module in exploits:
        print(module['name'])
        exploit = msfconsole_get_exploit(module['ref_name'])
        print(exploit)



"""
"id": "567eaaba-94cc-4a27-83f8-768e5638f4e1darwinsh",
"ability_id": "567eaaba-94cc-4a27-83f8-768e5638f4e1",
"tactic": "technical-information-gathering",
"technique_name": "Conduct active scanning",
"technique_id": "T1254",
"name": "NMAP scan",
"test": "Li9zY2FubmVyLnNoICN7dGFyZ2V0LmlwfQ==",
"description": "Scan an external host for open ports and services",
"cleanup": [],
"executor": "sh",
"unique": "567eaaba-94cc-4a27-83f8-768e5638f4e1darwinsh",
"platform": "darwin",
"payloads": [
    "scanner.sh"
],
"parsers": [],
"requirements": [],
"privilege": "",
"timeout": 300,
"buckets": [
    "technical-information-gathering"
],
"access": 1,
"variations": []
"""
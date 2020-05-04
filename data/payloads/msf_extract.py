import argparse
import multiprocessing as mp
import pickle
import subprocess
import logging


def get_metasploit_exploits():
    result = subprocess.run(['msfconsole', '-x', 'show exploits; exit;'], stdout=subprocess.PIPE)
    return result.stdout


def parse_exploits(exploit_result):
    results = metasploit_exploits.decode().split('\n')
    exploits = []
    for l in results[results.index('Exploits') + 5::]:
        if not len(l):
            continue
        try:
            exploits.append(l.split()[1].strip())
        except:
            continue
    return exploits


def parse_exploit_info(exploit_info):
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


def get_exploit(exploit):
    result = subprocess.run(['msfconsole', '-q', '-x', f'info {exploit}; exit;'], stdout=subprocess.PIPE)
    return parse_exploit_info(result.stdout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract Metasploit exploits.')
    parser.add_argument('-c', '--cores', default=mp.cpu_count(), help='cores for processing')
    parser.add_argument('-v', '--verbosity', default=logging.INFO, help='log level')
    args = parser.parse_args()
    FORMAT = '%(message)s'
    logging.basicConfig(level=args.verbosity, format=FORMAT)

    try:
        with open('exploits.pickle', 'rb') as f:
            metasploit_exploits = pickle.load(f)
    except FileNotFoundError:
        metasploit_exploits = get_metasploit_exploits()
        with open('exploits.pickle', 'wb') as f:
            pickle.dump(metasploit_exploits, f, pickle.HIGHEST_PROTOCOL)

    logging.debug('got exploit list')
    exploits = parse_exploits(metasploit_exploits)
    logging.debug('parsed exploits')

    pool = mp.Pool(mp.cpu_count())
    subset = exploits[:10]
    logging.debug(len(subset))
    results = pool.map(get_exploit, subset)
    pool.close()

    logging.info(results)
    logging.debug('finished')

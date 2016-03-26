import os
import sys
import json
import argparse
from tunirvagrant import vagrant_and_run
from tuniraws import aws_and_run
from tunirdocker import Docker, Result
from tunirmultihost import start_multihost
from tunirutils import run_job
from collections import OrderedDict

STR = OrderedDict()


def read_job_configuration(jobname='', config_dir='./'):
    """
    :param jobname: Name of the job
    :param config_dir: Directory for configuration.
    :return: Configuration dict
    """
    data = None
    name = jobname + '.json'
    name = os.path.join(config_dir, name)
    if not os.path.exists(name):
        print "Job configuration is missing."
        return None
    with open(name) as fobj:
        data = json.load(fobj)
    return data

def main(args):
    "Starting point of the code"
    job_name = ''
    vm = None
    node = None
    port = None
    temp_d = None
    container = None
    atomic = False
    debug = False
    image_dir = ''
    vagrant = None
    return_code = -100
    run_job_flag = True

    if args.atomic:
        atomic = True
    if args.debug:
        debug = True
    # For multihost
    if args.multi:
        jobpath = os.path.join(args.config_dir, args.multi + '.txt')
        status = start_multihost(args.multi, jobpath, debug)
        os.system('stty sane')
        if status:
            sys.exit(0)
    if args.job:
        job_name = args.job
    else:
        sys.exit(-2)

    jobpath = os.path.join(args.config_dir, job_name + '.txt')


    # First let us read the vm configuration.
    config = read_job_configuration(job_name, args.config_dir)
    if not config: # Bad config name
        sys.exit(-1)

    os.system('mkdir -p /var/run/tunir')
    if config['type'] == 'vm':
        status = start_multihost(job_name, jobpath, debug, config, args.config_dir)
        os.system('stty sane')
        sys.exit(status)

    if config['type'] == 'vagrant':
        vagrant, config = vagrant_and_run(config)
        if vagrant.failed:
            run_job_flag = False

    elif config['type'] == 'aws':
        node, config = aws_and_run(config)
        if node.failed:
            run_job_flag = False
        else:
            print "We have an instance ready in AWS.", node.node

    try:
        if run_job_flag:
            status = start_multihost(job_name, jobpath, debug, config, args.config_dir)
            if status:
                return_code = 0
    finally:
        # Now let us kill the kvm process
        if vagrant:
            print "Removing the box."
            vagrant.destroy()
        elif node:
            node.destroy()
            #print "Not destorying the node", node

        sys.exit(return_code)


def startpoint():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", help="The job configuration name to run")
    parser.add_argument("--stateless", help="Do not store the result, just print it in the STDOUT.", action='store_true')
    parser.add_argument("--config-dir", help="Path to the directory where the job config and commands can be found.",
                        default='./')
    parser.add_argument("--image-dir", help="Path to the directory where vm images will be held")
    parser.add_argument("--atomic", help="We are using an Atomic image.", action='store_true')
    parser.add_argument("--debug", help="Keep the vms running for debug in multihost mode.", action='store_true')
    parser.add_argument("--multi", help="The multihost configuration")
    args = parser.parse_args()

    main(args)

if __name__ == '__main__':
    startpoint()

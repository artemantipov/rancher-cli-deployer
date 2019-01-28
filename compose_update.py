#!/usr/bin/env python3
import os
import sys
import yaml
import argparse

from colorama import Fore, Style

get_env = os.environ.get
parser = argparse.ArgumentParser()

parser.add_argument('source_dir', type=str, nargs=1)
parser.add_argument('destination_dir', type=str, nargs=1)
parser.add_argument('tag', type=str, nargs=1)
parser.add_argument('--service', '-s', dest='service', type=str, nargs='?')
parser.add_argument('--image', '-i', dest='image', type=str, nargs='?')
parser.add_argument('--stack', dest='stack', action='store_true')

COMPOSE_FILE_NAME = 'docker-compose.yml'

TAG_POINTER = 1
IMAGE_POINTER = 0


def update_service(docker_compose: dict, service_name: str, tag_name: str, image_name=None) -> dict:
    old_image, old_tag = get_image_and_tag(docker_compose, service_name)
    new_tag = tag_name
    new_image = image_name if image_name else old_image

    updates_notifyer(
        service_name=service_name,
        old_tag=old_tag,
        new_tag=new_tag,
        old_image=old_image,
        new_image=new_image
    )

    docker_compose['services'][service_name]['image'] = f'{new_image}:{new_tag}'
    return docker_compose


def update_stack(docker_compose: dict, tag_name: str, image_name=None) -> dict:
    # check for different images
    all_images_from_stack = set()
    for service_name, _ in docker_compose['services'].items():
        image, _ = get_image_and_tag(docker_compose, service_name)
        all_images_from_stack.add(image)

    # if stack has different images we can't update the stack
    if len(all_images_from_stack) > 1:
        print(f'{Fore.RED}ERROR:{Style.RESET_ALL}The stack has different images, try update by services:\n',
              f'all different of images in stack: {all_images_from_stack}')
        sys.exit(1)

    new_docker_compose = docker_compose.copy()
    for service_name, service_values in docker_compose['services'].items():
        new_docker_compose = update_service(new_docker_compose, service_name, tag_name, image_name)

    # generate new docker config file
    return new_docker_compose


def get_image_and_tag(docker_compose: dict, service_name: str) -> tuple:
    try:
        image = docker_compose['services'][service_name]['image'].split(":")[IMAGE_POINTER]
        tag = docker_compose['services'][service_name]['image'].split(":")[TAG_POINTER]
    except IndexError:
        # this can happen if service image hasn't tag
        tag = ''
    except Exception as e:
        print(
            f'{Fore.RED}ERROR:{Style.RESET_ALL}'
            f'{Fore.RED}Docker compose:{Style.RESET_ALL} {docker_compose}!\n'
            f'{Fore.RED}Servcie name:{Style.RESET_ALL} {service_name}\n'
            f'{e}'
        )
        sys.exit(1)


    return image, tag


def updates_notifyer(service_name:str, old_tag: str, new_tag: str, old_image: str, new_image: str) -> None:
    updated = f'{Fore.GREEN}INFO:{Fore.YELLOW}WHAT WILL BE UPDATED:{Style.RESET_ALL}\t'
    no_change = f'{Fore.YELLOW}INFO: NOTHING WILL BE UPDATED{Style.RESET_ALL}\t'

    if (old_tag != new_tag) or (old_image != new_image):
        state = updated
    else:
        state = no_change
    print(
        f'{state}{service_name} = {old_image}:{old_tag} >> {new_image}:{new_tag}'
    )


def load_docker_compose(file_name: str) -> dict:
    try:
        with open(file_name, 'r') as ymlfile:
            docker_compose = yaml.load(ymlfile)
    except Exception as e:
        print(
            f'{Fore.RED}ERROR:{Style.RESET_ALL}'
            f'Can`t read file {source_file}!\n'
            f'{e}'
        )
        sys.exit(1)

    return docker_compose


def make_compose_file(docker_compose: dict, dest_file: str) -> None:
    # write new yaml file
    print(
        f'{Fore.GREEN}INFO:'
        f'{Fore.YELLOW}WRITE COMPOSE TO: {Style.RESET_ALL}{dest_file}'
    )
    with open(dest_file, 'w') as new_conf:
        yaml.dump(docker_compose, new_conf, default_flow_style=False)

    # write .images file, for pre-pull
    print(f'{Fore.GREEN}INFO:{Fore.YELLOW}MAKE .IMAGES FOR PULL STAGE {Style.RESET_ALL}')
    with open('.images', 'w') as f:
        for x in docker_compose['services'].values():
            f.write(x['image'] + '\n')


if __name__ == '__main__':

    args = parser.parse_args()
    print(args)

    source_dir = os.path.normpath(args.source_dir[0])
    dest_dir = os.path.normpath(args.destination_dir[0])

    source_file = os.path.join(source_dir, COMPOSE_FILE_NAME)
    destination_file = os.path.join(dest_dir, COMPOSE_FILE_NAME)
    tag_name = args.tag[0]
    service_name = args.service if args.service else None
    image_name = args.image if args.image else None
    output = f'''{Fore.GREEN}INFO:{Fore.YELLOW}ENVS:{Style.RESET_ALL}
    \t{Fore.RED}COMPOSE FILE PATH:{Style.RESET_ALL} {source_file}
    \t{Fore.RED}NEW COMPOSE FILE PATH:{Style.RESET_ALL} {destination_file}
    \t{Fore.RED}NEW TAG:{Style.RESET_ALL} {tag_name}
    \t{f'{Fore.RED}NEW IMAGE:{Style.RESET_ALL} {image_name}' if image_name else ''}'''

    if not os.path.exists(source_file):
        print(
            f'{Fore.RED}ERROR:{Style.RESET_ALL}'
            'Source compose file does not exist.'
        )
        sys.exit(1)

    if os.path.exists(dest_dir):
        if not os.path.isdir(dest_dir):
            print(
                f'{Fore.RED}ERROR:{Style.RESET_ALL}'
                'Destination should be a directory.'
            )
            sys.exit(1)
    else:
        os.makedirs(dest_dir)

    docker_compose = load_docker_compose(source_file)

    # stack or service name needed to be pass
    if args.stack:
        output += f'\t{Fore.RED}ALL STACK WILL BE UPDATED{Style.RESET_ALL}'
        docker_compose = update_stack(docker_compose, tag_name, image_name)
    elif service_name:
        old_image, old_tag = get_image_and_tag(docker_compose, service_name)
        output += f'''
        {Fore.RED}SERVICE TO UPDATE:{Style.RESET_ALL} {service_name}
        {Fore.RED}OLD IMAGE:{Style.RESET_ALL} {old_image}
        {Fore.RED}OLD TAG:{Style.RESET_ALL} {old_tag}'''
        docker_compose = update_service(docker_compose, service_name, tag_name, image_name)

    else:
        print('You need to pass the service name or --stack')
        sys.exit(1)

    # print of the passed variables
    print(output)

    # save new docker config
    make_compose_file(docker_compose, destination_file)

#!/bin/python3
import sys
import requests
import json
import logging
from pathlib import Path

URL = "https://api.trello.com/1/cards"
HEADERS = {
    "Accept": "application/json"
}
CONFIG_DIR = Path(Path.home(), ".config", "trello_cli_task_creator")
CONFIG_FILE = Path(CONFIG_DIR, "config.json")
QUEUE_FILE = Path(CONFIG_DIR, "queue.json")
LOG_FILE = Path(CONFIG_DIR, "log")

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    filename=LOG_FILE,
    filemode='a',
    level=logging.DEBUG
)


def create_stub_config():
    try:
        config_file = CONFIG_FILE.open(mode='w')
    except PermissionError:
        print(f"Cannot open or create {CONFIG_FILE}")
        return False

    stub_config = {
        'idList': '',
        'key': '',
        'token': '',
    }

    json.dump(stub_config, config_file, indent=4)
    config_file.close()
    return True


def get_queue():
    try:
        queue_file = QUEUE_FILE.open(mode='r')
    except PermissionError:
        print(f"Cannot open or create {QUEUE_FILE}")
        print("Card name:", name)
        print("Card description:", desc)
        exit(2)

    try:
        queue = json.load(queue_file)
    except json.JSONDecodeError:
        queue = []

    queue_file.close()

    return queue


def set_queue(queue: list):
    try:
        queue_file = QUEUE_FILE.open(mode='w')
    except PermissionError:
        print(f"Cannot open or create {QUEUE_FILE}")
        print("Card name:", name)
        print("Card description:", desc)
        exit(2)

    json.dump(queue, queue_file, indent=4)
    queue_file.close()


def queue_task(name: str, desc: str):
    queue = get_queue()
    queue.append({"name": name, "desc": desc})
    set_queue(queue)
    return queue


def send_query(config: dict, task: dict, failed_tasks: list):
    query = {
        'idList': config['idList'],
        'key': config['key'],
        'token': config['token'],
        'name': task['name'],
        'desc': task['desc']
    }

    try:
        response = requests.request(
            "POST",
            URL,
            headers=HEADERS,
            params=query
        )

        if not response.ok:
            logging.error(query)
            logging.warning(task["name"], response.status_code)
            failed_tasks.append(task)

    except Exception as e:
        failed_tasks.append(task)
        logging.exception(e)


def send_task(name: str, desc: str):
    queue = queue_task(name, desc)
    failed_tasks = []

    try:
        config_file = CONFIG_FILE.open(mode='r')
    except PermissionError:
        print(f"Cannot open or create {CONFIG_FILE}")
        exit(1)

    config = json.load(config_file)

    for task in queue:
        send_query(config, task, failed_tasks)

    if len(failed_tasks) > 0:
        set_queue(failed_tasks)
        print(f"{len(failed_tasks)} task(s) waits for send")
    else:
        set_queue([])


def main():
    Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    if not Path(CONFIG_FILE).exists():
        if not create_stub_config():
            print("Script doesn't work without config")
            exit(1)
        else:
            print(f"Fill config to use script: {CONFIG_FILE}")
            exit(0)

    if len(sys.argv) > 1:
        name = ' '.join(sys.argv[1:]).strip()
        desc = ''
    else:
        print("Put title:")
        name = sys.stdin.readline().strip()
        desc = ''
        print("Put description till eof:")
        for line in sys.stdin:
            desc += line
        print("Start processing")

    send_task(name, desc)


if __name__ == "__main__":
    main()

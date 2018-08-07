import json
import threading
import uuid
from flask import Flask
from queue import Queue, Empty
from urllib import request, error


SOURCE_TIMEOUT = 2   # seconds


app = Flask(__name__)

# tasks is in-memory storage, maps task_id to processed task.
# If value is None it means that task is still in progress
# shared across requests, thread-safe due to GIL in CPython
tasks = {}


sources = {
    'source1': 'http://localhost:8081/source_data/source1.json',
    'source2': 'http://localhost:8082/source_data/source2.json',
    'source3': 'http://localhost:8083/source_data/source3.json',
}


def fetch_from_source(source_name, queue):
    print('fetching from ', source_name, threading.get_ident())

    try:
        with request.urlopen(sources[source_name], timeout=SOURCE_TIMEOUT) as resp:
            data = json.load(resp)
    except (error.URLError, json.decoder.JSONDecodeError):
        data = []

    print('fetch done ', threading.get_ident())
    queue.put(data)


def process_data(data):
    data.sort(key=lambda x: x['id'])   # sort by 'id' asc order
    return data


def call_sources_task(task_id):
    tasks[task_id] = None     # task_id is in progress

    # spawning threads to fetch data from sources
    queue = Queue()
    thread1 = threading.Thread(target=fetch_from_source, args=('source1', queue))
    thread2 = threading.Thread(target=fetch_from_source, args=('source2', queue))
    thread3 = threading.Thread(target=fetch_from_source, args=('source3', queue))
    threads = [thread1, thread2, thread3]
    for thread in threads:
        thread.start()

    # process results
    result = []
    for _ in range(len(threads)):
        try:
            items = queue.get(timeout=SOURCE_TIMEOUT)
            for item in items:
                result.append(item)
        except Empty:
            print("Empty")
            continue

    tasks[task_id] = process_data(result)


def _generate_test_json(name, first, second):
    def test_data(start, stop):
        data = []
        for i in range(start, stop + 1):
            data.append({'id': i, 'name': 'Test ' + str(i)})
        return data

    data = test_data(first[0], first[1]) + test_data(second[0], second[1])
    with open('source_data/' + name, 'w') as fd:
        fd.write(json.dumps(data, indent=2))


@app.route('/start_task')
def start_task():
    task_id = str(uuid.uuid4())
    print('starting task ', task_id, ' thread ', threading.get_ident())
    thread = threading.Thread(target=call_sources_task, args=(task_id,))
    thread.start()
    return str(task_id)


@app.route('/check_task/<task_id>')
def check_task(task_id):
    print('get ', task_id)
    try:
        item = tasks[task_id]
    except KeyError:
        return 'Not registered'

    if item is None:
        return "Processing"

    try:
        res = tasks.pop(task_id)
        return str(res)
    except KeyError:
        return 'Not registered'


if __name__ == '__main__':
    app.run('localhost', 8080)

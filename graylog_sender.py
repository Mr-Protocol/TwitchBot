import threading
import socket
import json
import queue


class NoQuoteEscapingEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs['separators'] = (',', ':')
        super().__init__(*args, **kwargs)

    def encode(self, o):
        result = super().encode(o)
        return result.replace('\\"', '"')


def sendgraylog(data, host, port):
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # Convert the JSON data to a string
        json_string = json.dumps(data, cls=NoQuoteEscapingEncoder)

        # Send the string to the Graylog server
        client_socket.sendto(json_string[1:-1].encode(), (host, port))

        # Print the JSON string
        # print(json_string)

        # print("Data sent to Graylog successfully!")

    except ConnectionRefusedError:
        print("Failed to send data to the Graylog server.")

    finally:
        # Close the socket
        client_socket.close()


# Set the host and port of the Graylog server - UDP PlainText/Raw
# Change IP to Graylog server IP
host = '127.0.0.1'
port = 5555

# Create a queue to hold the JSON data
data_queue = queue.Queue()

# Function to handle sending data from the queue
def send_data_worker():
    while True:
        data = data_queue.get()
        sendgraylog(data, host, port)
        data_queue.task_done()


# Create and start the worker thread
worker_thread = threading.Thread(target=send_data_worker)
worker_thread.start()


# Function to add data to the queue
def graylogqueue(data):
    data_queue.put(data)

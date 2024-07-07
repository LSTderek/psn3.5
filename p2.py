# Import necessary modules
import pypsn
from flask import Flask, jsonify
from threading import Thread
import time

# Initialize Flask app
app = Flask(__name__)

# List to store tracker names
trackers_list = []

# Define a function to convert bytes to string
def bytes_to_str(b):
    return b.decode('utf-8') if isinstance(b, bytes) else b

# Define a callback function to handle the received PSN data
def callback_function(data):
    global trackers_list
    if isinstance(data, pypsn.psn_info_packet):
        trackers_list = [{'tracker_name': bytes_to_str(tracker.tracker_name)} for tracker in data.trackers]

# Create a receiver object with the callback function
receiver = pypsn.receiver(callback_function)

# Define route to list available trackers
@app.route('/trackers', methods=['GET'])
def get_trackers():
    return jsonify(trackers_list)

# Function to run Flask app
def run_flask():
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

# Start the receiver and Flask server in separate threads
if __name__ == '__main__':
    try:
        # Start the receiver
        print("Starting PSN receiver...")
        receiver_thread = Thread(target=receiver.start)
        receiver_thread.start()

        # Start Flask server
        flask_thread = Thread(target=run_flask)
        flask_thread.start()

        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping receiver and Flask server...")

        # Stop the receiver
        receiver.stop()

        # Wait for threads to finish
        receiver_thread.join()
        flask_thread.join()

        print("Stopped.")

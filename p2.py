# Import necessary modules
import pypsn
from flask import Flask, jsonify
from threading import Thread
import time

# Initialize Flask app
app = Flask(__name__)

# List to store tracker data
trackers_list = []

# Define a callback function to handle the received PSN data
def callback_function(data):
    global trackers_list
    if isinstance(data, pypsn.psn_data_packet):
        trackers_list = [tracker.pos for tracker in data.trackers]
    elif isinstance(data, pypsn.psn_info_packet):
        trackers_list = [tracker.tracker_name for tracker in data.trackers]

# Create a receiver object with the callback function
receiver = pypsn.receiver(callback_function)

# Define route to list available trackers
@app.route('/trackers', methods=['GET'])
def get_trackers():
    return jsonify(trackers_list)

# Function to run Flask app
def run_flask():
    app.run(host='0.0.0.0', debug=True, use_reloader=False)

# Start the receiver and Flask server in separate threads
if __name__ == '__main__':
    try:
        # Start the receiver
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

        # Stopping Flask server is more complex; ideally, we'd need to
        # implement a way to gracefully shut it down if running in production.
        # For simplicity, we'll let Flask's debug mode handle it.

        # Wait for threads to finish
        receiver_thread.join()
        flask_thread.join()

        print("Stopped.")

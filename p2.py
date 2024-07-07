# Import necessary modules
import pypsn
from flask import Flask, jsonify

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

# Start the receiver to begin receiving PSN data
receiver.start()

# Define route to list available trackers
@app.route('/trackers', methods=['GET'])
def get_trackers():
    return jsonify(trackers_list)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)

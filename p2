# Import the necessary module from pypsn
import pypsn

# Define a callback function to handle the received PSN data
def callback_function(data):
    if isinstance(data, pypsn.psn_data_packet):
        # Loop through all trackers and print their coordinates
        for tracker in data.trackers:
            print(f"Tracker Position: {tracker.pos}")
    
    elif isinstance(data, pypsn.psn_info_packet):
        # Print the server name and loop through all trackers to print their names
        print(f"Server Name: {data.name}")
        for tracker in data.trackers:
            print(f"Tracker Name: {tracker.tracker_name}")

# Create a receiver object with the callback function
receiver = pypsn.receiver(callback_function)

# Start the receiver to begin receiving PSN data
receiver.start()

# Run the receiver for a specified amount of time (e.g., 10 seconds)
import time
time.sleep(10)

# Stop the receiver after the specified time
receiver.stop()

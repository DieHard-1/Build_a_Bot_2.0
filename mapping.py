import serial
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
import collections
import threading
import queue
import sys
import time

# Serial port setup (modify as needed)
serial_port = None

def setup_serial():
    try:
        return serial.Serial('COM5', 115200, timeout=0.1)
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        sys.exit(1)

# Initialize the plot
plt.ion()
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_xlim(-2.0, 2.0)  # Set x-axis to 2 meters
ax.set_ylim(-2.0, 2.0)  # Set y-axis to 2 meters
ax.set_title("2D LiDAR Circular Map", fontsize=16, fontweight='bold')
ax.set_xlabel("X (meters)")
ax.set_ylabel("Y (meters)")
ax.set_aspect('equal')
ax.grid(True, linestyle='--', alpha=0.7)
fig.patch.set_facecolor('#f4f4f4')

# Draw circle boundary
CIRCLE_RADIUS = 2.0  # Adjusted circle radius to 2 meters
def draw_circle():
    ax.add_patch(plt.Circle((0, 0), CIRCLE_RADIUS, color='black', fill=False, linestyle='dashed', linewidth=2))
draw_circle()

# Colormap for visualization
cmap = plt.cm.viridis
norm = mcolors.Normalize(vmin=0.03, vmax=CIRCLE_RADIUS)

# Data storage
x_data = collections.deque(maxlen=1000)
y_data = collections.deque(maxlen=1000)
colors = collections.deque(maxlen=1000)

data_queue = queue.Queue()
prev_angle = -1  # Track previous angle to detect full revolution

def read_serial():
    global prev_angle
    while True:
        if serial_port.in_waiting:
            try:
                raw_data = serial_port.readline().decode('utf-8').strip()
                data = raw_data.split(',')
                if len(data) != 2:
                    continue
                angle, distance = float(data[0]) % 360, float(data[1]) / 1000.0
                if distance < 0.03 or distance > CIRCLE_RADIUS:
                    continue
                
                theta = np.radians(angle)
                x, y = distance * np.cos(theta), distance * np.sin(theta)
                data_queue.put((x, y, norm(distance)))

                # Detect a full 360° rotation
                if prev_angle > angle and angle < 10:
                    clear_plot()
                prev_angle = angle
            except Exception as e:
                print(f"Serial Read Error: {e}")
                time.sleep(1)

def start_serial_thread():
    global serial_port
    serial_port = setup_serial()
    threading.Thread(target=read_serial, daemon=True).start()

def clear_plot():
    ax.clear()
    ax.set_xlim(-2.0, 2.0)
    ax.set_ylim(-2.0, 2.0)
    ax.set_title("2D LiDAR Circular Map", fontsize=16, fontweight='bold')
    ax.set_xlabel("X (meters)")
    ax.set_ylabel("Y (meters)")
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.7)
    draw_circle()
    x_data.clear()
    y_data.clear()
    colors.clear()

def update_plot():
    while not data_queue.empty():
        x, y, c = data_queue.get()
        x_data.append(x)
        y_data.append(y)
        colors.append(c)
    
    ax.scatter(x_data, y_data, c=colors, cmap=cmap, edgecolors='none', s=10)
    plt.draw()
    plt.pause(0.01)

if __name__ == '__main__':
    try:
        start_serial_thread()
        while True:
            update_plot()
    except KeyboardInterrupt:
        print("Exiting application...")
        if serial_port:
            serial_port.close()
        plt.close(fig)
        sys.exit(0)
    
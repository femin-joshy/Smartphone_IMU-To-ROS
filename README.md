ello ello :p
The aim of this project is to utilize smartphone IMU sensors for controlling a robot via ROS. By
downloading an Android application from GitHub, we can capture data from various sensors
like accelerometers and gyroscopes. This data is then transmitted through ROSBridge to
Gazebo, or transmitted to real robot, allowing the smartphone to control the robot's
movements and rotations. This method demonstrates a flexible and intuitive approach to
robotic control using common smartphone technology.
Steps
1. Download the mobile app (Sensor Server) from Github. (only for android)
You can download from this link: https://github.com/umer0586/SensorServer
2. Ensure that you use the Sensor Server application and your computer/robot in the same
Wi-Fi environment.
3. Use d.py in the Code file. Please read the comment at line number 146 and 180 in d.py.
4. By using Gazebo, follow these steps in Terminal:
4.1. Run ROS core:
roscore
4.2. Open a new Terminal window. Connect to ROS Bridge:
roslaunch rosbridge_server rosbridge_websocket.launch
4.3. Open a new Terminal window.
Open Gazebo Simulator (with Turtlebot3 burger)
export TURTLEBOT3_MODEL=burger
roslaunch turtlebot3_gazebo turtlebot3_world.launch
If use Raspberry Pi Mouse in gazebo (in a maze):
catkin_make
source devel/setup.bash
roslaunch raspimouse_gazebo raspimouse_with_samplemaze.launch
4.4. Open a new Terminal window. Run d.py
cd /your path to d.py
python3 d.py
5. To connecting the real robot (Raspberry Pi Mouse), please refer to Manual.pdf. After
connecting, do step 4.4.

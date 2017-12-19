#!/usr/bin/env python

import rospy
import math
from geometry_msgs.msg import PoseStamped
from styx_msgs.msg import Lane, Waypoint

import math

'''
This node will publish waypoints from the car's current position to some `x` distance ahead.

As mentioned in the doc, you should ideally first implement a version which does not care
about traffic lights or obstacles.

Once you have created dbw_node, you will update this node to use the status of traffic lights too.

Please note that our simulator also provides the exact location of traffic lights and their
current status in `/vehicle/traffic_lights` message. You can use this message to build this node
as well as to verify your TL classifier.

TODO (for Yousuf and Aaron): Stopline location for each traffic light.
'''

LOOKAHEAD_WPS = 50 # Number of waypoints we will publish. You can change this number


class WaypointUpdater(object):
    def __init__(self):
        rospy.init_node('waypoint_updater')

        rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)
        rospy.Subscriber('/base_waypoints', Lane, self.waypoints_cb)

        # TODO: Add a subscriber for /traffic_waypoint and /obstacle_waypoint below


        self.final_waypoints_pub = rospy.Publisher('final_waypoints', Lane, queue_size=1)

        self.current_position = []
        self.base_waypoints = []
        self.total_waypoints = 0
        # TODO: Add other member variables you need below

        rospy.spin()

    def convert_local(self, waypoint, current_pos):
        x_way = waypoint.pose.pose.position.x
        y_way = waypoint.pose.pose.position.y
        x_car = current_pos.pose.position.x
        y_car = current_pos.pose.position.y
        theta_car = 2*math.acos(current_pos.pose.orientation.w)
        # Convert Quarternion to radian angle
        x_shift = x_way - x_car
        y_shift = y_way - y_car

        theta_waypoint = 2*math.acos(waypoint.pose.pose.orientation.w)
        #rospy.logwarn(theta_car)
        #rospy.logwarn(theta_waypoint)
        x = x_shift*math.cos(0-theta_car) - y_shift*math.sin(0 - theta_car)
        y = x_shift*math.sin(0 - theta_car) + y_shift*math.cos(0 - theta_car)
        return x,y, theta_car, theta_waypoint

    def pose_cb(self, msg):
        # TODO: Implement
        #rospy.logwarn('Position Recieved') #Trouble shooting to ensure position is being recieved
        #Decipher current position
        current_pos = msg
        #x = msg.pose.position.x
        #y = msg.pose.position.y
        #theta = msg.pose.orientation.w
        #theta2 = msg.pose.orientation.z
        #rospy.logwarn("current x = %s", x)
        #rospy.logwarn("current y = %s", y)
        #rospy.logwarn("current theta = %s", theta)
        #rospy.logwarn("current theta2 = %s", theta2)
        #Determine next waypoint
        #Construct a Lane object with LOOKAHEAD_WPS number of waypoints
        #Where next waypoint is element[0], and following elements are waypoints after that
        #Call final_waypoints_pub

        final_waypoints_list = []
        for i in range(len(self.base_waypoints.waypoints)):
            waypoint = self.base_waypoints.waypoints[i]
            #rospy.logwarn(waypoint)
            x,y,theta_car, theta_waypoint = self.convert_local(waypoint, current_pos)
            #rospy.logwarn("X and Y = %s & %s", x,y)
            #rospy.logwarn(self.total_waypoints)
            orientation_match = math.cos(theta_waypoint - theta_car)
            if(x > 0.00 and orientation_match > 0.707 ):
                #final_waypoints_list.append(self.base_waypoints.waypoints[i])
                for j in range(LOOKAHEAD_WPS):
                    j_mod = i+j%self.total_waypoints
                    final_waypoints_list.append(self.base_waypoints.waypoints[j_mod])
                #rospy.logwarn(len(final_waypoints_list))
                #rospy.logwarn(final_waypoints_list[0])
                msg = Lane()
                msg.waypoints = final_waypoints_list
                self.final_waypoints_pub.publish(msg)
                #rospy.logwarn(msg)
                return
        '''
        waypoint = self.base_waypoints.waypoints[0]
        rospy.logwarn(waypoint)
        rospy.logwarn(current_pos)
        x, y, theta_car, theta_waypoint = self.convert_local(waypoint, current_pos)        
        rospy.logwarn("X and Y = %s & %s", x, y)
        '''

        pass

    def waypoints_cb(self, waypoints):
        # TODO: Implement
        #rospy.logwarn('Waypooints Recieved')   #Trouble shooting to ensure initial waypoints are being recieved
        #first_x = waypoints.waypoints[0].twist.twist.linear.x

        #waypoints_list = []
        #first_x = waypoints.waypoints[0]
        #for waypoint in waypoints.waypoints:
        #    rospy.logwarn("Waypoint is : %s", waypoint)
        #first_x = waypoints
        #rospy.logwarn("Received first X as %s", first_x)
        self.base_waypoints = waypoints
        self.total_waypoints = len(self.base_waypoints.waypoints)
        #rospy.logwarn(self.total_waypoints)
        pass

    def traffic_cb(self, msg):
        # TODO: Callback for /traffic_waypoint message. Implement
        pass

    def obstacle_cb(self, msg):
        # TODO: Callback for /obstacle_waypoint message. We will implement it later
        pass



    def get_waypoint_velocity(self, waypoint):
        return waypoint.twist.twist.linear.x

    def set_waypoint_velocity(self, waypoints, waypoint, velocity):
        waypoints[waypoint].twist.twist.linear.x = velocity

    def distance(self, waypoints, wp1, wp2):
        dist = 0
        dl = lambda a, b: math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2  + (a.z-b.z)**2)
        for i in range(wp1, wp2+1):
            dist += dl(waypoints[wp1].pose.pose.position, waypoints[i].pose.pose.position)
            wp1 = i
        return dist


if __name__ == '__main__':
    try:
        WaypointUpdater()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start waypoint updater node.')

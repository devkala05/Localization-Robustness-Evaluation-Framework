;; Auto-generated. Do not edit!


(when (boundp 'custom_localization_msgs::CustomImu)
  (if (not (find-package "CUSTOM_LOCALIZATION_MSGS"))
    (make-package "CUSTOM_LOCALIZATION_MSGS"))
  (shadow 'CustomImu (find-package "CUSTOM_LOCALIZATION_MSGS")))
(unless (find-package "CUSTOM_LOCALIZATION_MSGS::CUSTOMIMU")
  (make-package "CUSTOM_LOCALIZATION_MSGS::CUSTOMIMU"))

(in-package "ROS")
;;//! \htmlinclude CustomImu.msg.html
(if (not (find-package "SENSOR_MSGS"))
  (ros::roseus-add-msgs "sensor_msgs"))
(if (not (find-package "STD_MSGS"))
  (ros::roseus-add-msgs "std_msgs"))


(defclass custom_localization_msgs::CustomImu
  :super ros::object
  :slots (_header _dataset _sensor_name _source_topic _perturbation_label _imu ))

(defmethod custom_localization_msgs::CustomImu
  (:init
   (&key
    ((:header __header) (instance std_msgs::Header :init))
    ((:dataset __dataset) "")
    ((:sensor_name __sensor_name) "")
    ((:source_topic __source_topic) "")
    ((:perturbation_label __perturbation_label) "")
    ((:imu __imu) (instance sensor_msgs::Imu :init))
    )
   (send-super :init)
   (setq _header __header)
   (setq _dataset (string __dataset))
   (setq _sensor_name (string __sensor_name))
   (setq _source_topic (string __source_topic))
   (setq _perturbation_label (string __perturbation_label))
   (setq _imu __imu)
   self)
  (:header
   (&rest __header)
   (if (keywordp (car __header))
       (send* _header __header)
     (progn
       (if __header (setq _header (car __header)))
       _header)))
  (:dataset
   (&optional __dataset)
   (if __dataset (setq _dataset __dataset)) _dataset)
  (:sensor_name
   (&optional __sensor_name)
   (if __sensor_name (setq _sensor_name __sensor_name)) _sensor_name)
  (:source_topic
   (&optional __source_topic)
   (if __source_topic (setq _source_topic __source_topic)) _source_topic)
  (:perturbation_label
   (&optional __perturbation_label)
   (if __perturbation_label (setq _perturbation_label __perturbation_label)) _perturbation_label)
  (:imu
   (&rest __imu)
   (if (keywordp (car __imu))
       (send* _imu __imu)
     (progn
       (if __imu (setq _imu (car __imu)))
       _imu)))
  (:serialization-length
   ()
   (+
    ;; std_msgs/Header _header
    (send _header :serialization-length)
    ;; string _dataset
    4 (length _dataset)
    ;; string _sensor_name
    4 (length _sensor_name)
    ;; string _source_topic
    4 (length _source_topic)
    ;; string _perturbation_label
    4 (length _perturbation_label)
    ;; sensor_msgs/Imu _imu
    (send _imu :serialization-length)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; std_msgs/Header _header
       (send _header :serialize s)
     ;; string _dataset
       (write-long (length _dataset) s) (princ _dataset s)
     ;; string _sensor_name
       (write-long (length _sensor_name) s) (princ _sensor_name s)
     ;; string _source_topic
       (write-long (length _source_topic) s) (princ _source_topic s)
     ;; string _perturbation_label
       (write-long (length _perturbation_label) s) (princ _perturbation_label s)
     ;; sensor_msgs/Imu _imu
       (send _imu :serialize s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; std_msgs/Header _header
     (send _header :deserialize buf ptr-) (incf ptr- (send _header :serialization-length))
   ;; string _dataset
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _dataset (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _sensor_name
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _sensor_name (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _source_topic
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _source_topic (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _perturbation_label
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _perturbation_label (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; sensor_msgs/Imu _imu
     (send _imu :deserialize buf ptr-) (incf ptr- (send _imu :serialization-length))
   ;;
   self)
  )

(setf (get custom_localization_msgs::CustomImu :md5sum-) "c8b19871332313c87fa5702b645958bc")
(setf (get custom_localization_msgs::CustomImu :datatype-) "custom_localization_msgs/CustomImu")
(setf (get custom_localization_msgs::CustomImu :definition-)
      "std_msgs/Header header
string dataset
string sensor_name
string source_topic
string perturbation_label
sensor_msgs/Imu imu

================================================================================
MSG: std_msgs/Header
# Standard metadata for higher-level stamped data types.
# This is generally used to communicate timestamped data 
# in a particular coordinate frame.
# 
# sequence ID: consecutively increasing ID 
uint32 seq
#Two-integer timestamp that is expressed as:
# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')
# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')
# time-handling sugar is provided by the client library
time stamp
#Frame this data is associated with
string frame_id

================================================================================
MSG: sensor_msgs/Imu
# This is a message to hold data from an IMU (Inertial Measurement Unit)
#
# Accelerations should be in m/s^2 (not in g's), and rotational velocity should be in rad/sec
#
# If the covariance of the measurement is known, it should be filled in (if all you know is the 
# variance of each measurement, e.g. from the datasheet, just put those along the diagonal)
# A covariance matrix of all zeros will be interpreted as \"covariance unknown\", and to use the
# data a covariance will have to be assumed or gotten from some other source
#
# If you have no estimate for one of the data elements (e.g. your IMU doesn't produce an orientation 
# estimate), please set element 0 of the associated covariance matrix to -1
# If you are interpreting this message, please check for a value of -1 in the first element of each 
# covariance matrix, and disregard the associated estimate.

Header header

geometry_msgs/Quaternion orientation
float64[9] orientation_covariance # Row major about x, y, z axes

geometry_msgs/Vector3 angular_velocity
float64[9] angular_velocity_covariance # Row major about x, y, z axes

geometry_msgs/Vector3 linear_acceleration
float64[9] linear_acceleration_covariance # Row major x, y z 

================================================================================
MSG: geometry_msgs/Quaternion
# This represents an orientation in free space in quaternion form.

float64 x
float64 y
float64 z
float64 w

================================================================================
MSG: geometry_msgs/Vector3
# This represents a vector in free space. 
# It is only meant to represent a direction. Therefore, it does not
# make sense to apply a translation to it (e.g., when applying a 
# generic rigid transformation to a Vector3, tf2 will only apply the
# rotation). If you want your data to be translatable too, use the
# geometry_msgs/Point message instead.

float64 x
float64 y
float64 z
")



(provide :custom_localization_msgs/CustomImu "c8b19871332313c87fa5702b645958bc")



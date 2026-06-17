;; Auto-generated. Do not edit!


(when (boundp 'custom_localization_msgs::LocalizationOutput)
  (if (not (find-package "CUSTOM_LOCALIZATION_MSGS"))
    (make-package "CUSTOM_LOCALIZATION_MSGS"))
  (shadow 'LocalizationOutput (find-package "CUSTOM_LOCALIZATION_MSGS")))
(unless (find-package "CUSTOM_LOCALIZATION_MSGS::LOCALIZATIONOUTPUT")
  (make-package "CUSTOM_LOCALIZATION_MSGS::LOCALIZATIONOUTPUT"))

(in-package "ROS")
;;//! \htmlinclude LocalizationOutput.msg.html
(if (not (find-package "GEOMETRY_MSGS"))
  (ros::roseus-add-msgs "geometry_msgs"))
(if (not (find-package "STD_MSGS"))
  (ros::roseus-add-msgs "std_msgs"))


(defclass custom_localization_msgs::LocalizationOutput
  :super ros::object
  :slots (_header _algorithm _run_id _source_topic _pose _twist ))

(defmethod custom_localization_msgs::LocalizationOutput
  (:init
   (&key
    ((:header __header) (instance std_msgs::Header :init))
    ((:algorithm __algorithm) "")
    ((:run_id __run_id) "")
    ((:source_topic __source_topic) "")
    ((:pose __pose) (instance geometry_msgs::PoseWithCovariance :init))
    ((:twist __twist) (instance geometry_msgs::TwistWithCovariance :init))
    )
   (send-super :init)
   (setq _header __header)
   (setq _algorithm (string __algorithm))
   (setq _run_id (string __run_id))
   (setq _source_topic (string __source_topic))
   (setq _pose __pose)
   (setq _twist __twist)
   self)
  (:header
   (&rest __header)
   (if (keywordp (car __header))
       (send* _header __header)
     (progn
       (if __header (setq _header (car __header)))
       _header)))
  (:algorithm
   (&optional __algorithm)
   (if __algorithm (setq _algorithm __algorithm)) _algorithm)
  (:run_id
   (&optional __run_id)
   (if __run_id (setq _run_id __run_id)) _run_id)
  (:source_topic
   (&optional __source_topic)
   (if __source_topic (setq _source_topic __source_topic)) _source_topic)
  (:pose
   (&rest __pose)
   (if (keywordp (car __pose))
       (send* _pose __pose)
     (progn
       (if __pose (setq _pose (car __pose)))
       _pose)))
  (:twist
   (&rest __twist)
   (if (keywordp (car __twist))
       (send* _twist __twist)
     (progn
       (if __twist (setq _twist (car __twist)))
       _twist)))
  (:serialization-length
   ()
   (+
    ;; std_msgs/Header _header
    (send _header :serialization-length)
    ;; string _algorithm
    4 (length _algorithm)
    ;; string _run_id
    4 (length _run_id)
    ;; string _source_topic
    4 (length _source_topic)
    ;; geometry_msgs/PoseWithCovariance _pose
    (send _pose :serialization-length)
    ;; geometry_msgs/TwistWithCovariance _twist
    (send _twist :serialization-length)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; std_msgs/Header _header
       (send _header :serialize s)
     ;; string _algorithm
       (write-long (length _algorithm) s) (princ _algorithm s)
     ;; string _run_id
       (write-long (length _run_id) s) (princ _run_id s)
     ;; string _source_topic
       (write-long (length _source_topic) s) (princ _source_topic s)
     ;; geometry_msgs/PoseWithCovariance _pose
       (send _pose :serialize s)
     ;; geometry_msgs/TwistWithCovariance _twist
       (send _twist :serialize s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; std_msgs/Header _header
     (send _header :deserialize buf ptr-) (incf ptr- (send _header :serialization-length))
   ;; string _algorithm
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _algorithm (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _run_id
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _run_id (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _source_topic
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _source_topic (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; geometry_msgs/PoseWithCovariance _pose
     (send _pose :deserialize buf ptr-) (incf ptr- (send _pose :serialization-length))
   ;; geometry_msgs/TwistWithCovariance _twist
     (send _twist :deserialize buf ptr-) (incf ptr- (send _twist :serialization-length))
   ;;
   self)
  )

(setf (get custom_localization_msgs::LocalizationOutput :md5sum-) "148a87da3ae1cd47c09a5df07478e78a")
(setf (get custom_localization_msgs::LocalizationOutput :datatype-) "custom_localization_msgs/LocalizationOutput")
(setf (get custom_localization_msgs::LocalizationOutput :definition-)
      "std_msgs/Header header
string algorithm
string run_id
string source_topic
geometry_msgs/PoseWithCovariance pose
geometry_msgs/TwistWithCovariance twist

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
MSG: geometry_msgs/PoseWithCovariance
# This represents a pose in free space with uncertainty.

Pose pose

# Row-major representation of the 6x6 covariance matrix
# The orientation parameters use a fixed-axis representation.
# In order, the parameters are:
# (x, y, z, rotation about X axis, rotation about Y axis, rotation about Z axis)
float64[36] covariance

================================================================================
MSG: geometry_msgs/Pose
# A representation of pose in free space, composed of position and orientation. 
Point position
Quaternion orientation

================================================================================
MSG: geometry_msgs/Point
# This contains the position of a point in free space
float64 x
float64 y
float64 z

================================================================================
MSG: geometry_msgs/Quaternion
# This represents an orientation in free space in quaternion form.

float64 x
float64 y
float64 z
float64 w

================================================================================
MSG: geometry_msgs/TwistWithCovariance
# This expresses velocity in free space with uncertainty.

Twist twist

# Row-major representation of the 6x6 covariance matrix
# The orientation parameters use a fixed-axis representation.
# In order, the parameters are:
# (x, y, z, rotation about X axis, rotation about Y axis, rotation about Z axis)
float64[36] covariance

================================================================================
MSG: geometry_msgs/Twist
# This expresses velocity in free space broken into its linear and angular parts.
Vector3 linear
Vector3 angular

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



(provide :custom_localization_msgs/LocalizationOutput "148a87da3ae1cd47c09a5df07478e78a")



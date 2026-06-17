;; Auto-generated. Do not edit!


(when (boundp 'custom_localization_msgs::CustomPointCloud)
  (if (not (find-package "CUSTOM_LOCALIZATION_MSGS"))
    (make-package "CUSTOM_LOCALIZATION_MSGS"))
  (shadow 'CustomPointCloud (find-package "CUSTOM_LOCALIZATION_MSGS")))
(unless (find-package "CUSTOM_LOCALIZATION_MSGS::CUSTOMPOINTCLOUD")
  (make-package "CUSTOM_LOCALIZATION_MSGS::CUSTOMPOINTCLOUD"))

(in-package "ROS")
;;//! \htmlinclude CustomPointCloud.msg.html
(if (not (find-package "SENSOR_MSGS"))
  (ros::roseus-add-msgs "sensor_msgs"))
(if (not (find-package "STD_MSGS"))
  (ros::roseus-add-msgs "std_msgs"))


(defclass custom_localization_msgs::CustomPointCloud
  :super ros::object
  :slots (_header _dataset _sensor_name _source_topic _perturbation_label _cloud ))

(defmethod custom_localization_msgs::CustomPointCloud
  (:init
   (&key
    ((:header __header) (instance std_msgs::Header :init))
    ((:dataset __dataset) "")
    ((:sensor_name __sensor_name) "")
    ((:source_topic __source_topic) "")
    ((:perturbation_label __perturbation_label) "")
    ((:cloud __cloud) (instance sensor_msgs::PointCloud2 :init))
    )
   (send-super :init)
   (setq _header __header)
   (setq _dataset (string __dataset))
   (setq _sensor_name (string __sensor_name))
   (setq _source_topic (string __source_topic))
   (setq _perturbation_label (string __perturbation_label))
   (setq _cloud __cloud)
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
  (:cloud
   (&rest __cloud)
   (if (keywordp (car __cloud))
       (send* _cloud __cloud)
     (progn
       (if __cloud (setq _cloud (car __cloud)))
       _cloud)))
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
    ;; sensor_msgs/PointCloud2 _cloud
    (send _cloud :serialization-length)
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
     ;; sensor_msgs/PointCloud2 _cloud
       (send _cloud :serialize s)
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
   ;; sensor_msgs/PointCloud2 _cloud
     (send _cloud :deserialize buf ptr-) (incf ptr- (send _cloud :serialization-length))
   ;;
   self)
  )

(setf (get custom_localization_msgs::CustomPointCloud :md5sum-) "2026a2fcbfd25a6438c9efeb4c5b631c")
(setf (get custom_localization_msgs::CustomPointCloud :datatype-) "custom_localization_msgs/CustomPointCloud")
(setf (get custom_localization_msgs::CustomPointCloud :definition-)
      "std_msgs/Header header
string dataset
string sensor_name
string source_topic
string perturbation_label
sensor_msgs/PointCloud2 cloud

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
MSG: sensor_msgs/PointCloud2
# This message holds a collection of N-dimensional points, which may
# contain additional information such as normals, intensity, etc. The
# point data is stored as a binary blob, its layout described by the
# contents of the \"fields\" array.

# The point cloud data may be organized 2d (image-like) or 1d
# (unordered). Point clouds organized as 2d images may be produced by
# camera depth sensors such as stereo or time-of-flight.

# Time of sensor data acquisition, and the coordinate frame ID (for 3d
# points).
Header header

# 2D structure of the point cloud. If the cloud is unordered, height is
# 1 and width is the length of the point cloud.
uint32 height
uint32 width

# Describes the channels and their layout in the binary data blob.
PointField[] fields

bool    is_bigendian # Is this data bigendian?
uint32  point_step   # Length of a point in bytes
uint32  row_step     # Length of a row in bytes
uint8[] data         # Actual point data, size is (row_step*height)

bool is_dense        # True if there are no invalid points

================================================================================
MSG: sensor_msgs/PointField
# This message holds the description of one point entry in the
# PointCloud2 message format.
uint8 INT8    = 1
uint8 UINT8   = 2
uint8 INT16   = 3
uint8 UINT16  = 4
uint8 INT32   = 5
uint8 UINT32  = 6
uint8 FLOAT32 = 7
uint8 FLOAT64 = 8

string name      # Name of field
uint32 offset    # Offset from start of point struct
uint8  datatype  # Datatype enumeration, see above
uint32 count     # How many elements in the field

")



(provide :custom_localization_msgs/CustomPointCloud "2026a2fcbfd25a6438c9efeb4c5b631c")



; Auto-generated. Do not edit!


(cl:in-package custom_localization_msgs-msg)


;//! \htmlinclude CustomPointCloud.msg.html

(cl:defclass <CustomPointCloud> (roslisp-msg-protocol:ros-message)
  ((header
    :reader header
    :initarg :header
    :type std_msgs-msg:Header
    :initform (cl:make-instance 'std_msgs-msg:Header))
   (dataset
    :reader dataset
    :initarg :dataset
    :type cl:string
    :initform "")
   (sensor_name
    :reader sensor_name
    :initarg :sensor_name
    :type cl:string
    :initform "")
   (source_topic
    :reader source_topic
    :initarg :source_topic
    :type cl:string
    :initform "")
   (perturbation_label
    :reader perturbation_label
    :initarg :perturbation_label
    :type cl:string
    :initform "")
   (cloud
    :reader cloud
    :initarg :cloud
    :type sensor_msgs-msg:PointCloud2
    :initform (cl:make-instance 'sensor_msgs-msg:PointCloud2)))
)

(cl:defclass CustomPointCloud (<CustomPointCloud>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <CustomPointCloud>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'CustomPointCloud)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name custom_localization_msgs-msg:<CustomPointCloud> is deprecated: use custom_localization_msgs-msg:CustomPointCloud instead.")))

(cl:ensure-generic-function 'header-val :lambda-list '(m))
(cl:defmethod header-val ((m <CustomPointCloud>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:header-val is deprecated.  Use custom_localization_msgs-msg:header instead.")
  (header m))

(cl:ensure-generic-function 'dataset-val :lambda-list '(m))
(cl:defmethod dataset-val ((m <CustomPointCloud>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:dataset-val is deprecated.  Use custom_localization_msgs-msg:dataset instead.")
  (dataset m))

(cl:ensure-generic-function 'sensor_name-val :lambda-list '(m))
(cl:defmethod sensor_name-val ((m <CustomPointCloud>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:sensor_name-val is deprecated.  Use custom_localization_msgs-msg:sensor_name instead.")
  (sensor_name m))

(cl:ensure-generic-function 'source_topic-val :lambda-list '(m))
(cl:defmethod source_topic-val ((m <CustomPointCloud>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:source_topic-val is deprecated.  Use custom_localization_msgs-msg:source_topic instead.")
  (source_topic m))

(cl:ensure-generic-function 'perturbation_label-val :lambda-list '(m))
(cl:defmethod perturbation_label-val ((m <CustomPointCloud>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:perturbation_label-val is deprecated.  Use custom_localization_msgs-msg:perturbation_label instead.")
  (perturbation_label m))

(cl:ensure-generic-function 'cloud-val :lambda-list '(m))
(cl:defmethod cloud-val ((m <CustomPointCloud>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:cloud-val is deprecated.  Use custom_localization_msgs-msg:cloud instead.")
  (cloud m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <CustomPointCloud>) ostream)
  "Serializes a message object of type '<CustomPointCloud>"
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'header) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'dataset))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'dataset))
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'sensor_name))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'sensor_name))
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'source_topic))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'source_topic))
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'perturbation_label))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'perturbation_label))
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'cloud) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <CustomPointCloud>) istream)
  "Deserializes a message object of type '<CustomPointCloud>"
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'header) istream)
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'dataset) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'dataset) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'sensor_name) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'sensor_name) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'source_topic) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'source_topic) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'perturbation_label) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'perturbation_label) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'cloud) istream)
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<CustomPointCloud>)))
  "Returns string type for a message object of type '<CustomPointCloud>"
  "custom_localization_msgs/CustomPointCloud")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'CustomPointCloud)))
  "Returns string type for a message object of type 'CustomPointCloud"
  "custom_localization_msgs/CustomPointCloud")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<CustomPointCloud>)))
  "Returns md5sum for a message object of type '<CustomPointCloud>"
  "2026a2fcbfd25a6438c9efeb4c5b631c")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'CustomPointCloud)))
  "Returns md5sum for a message object of type 'CustomPointCloud"
  "2026a2fcbfd25a6438c9efeb4c5b631c")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<CustomPointCloud>)))
  "Returns full string definition for message of type '<CustomPointCloud>"
  (cl:format cl:nil "std_msgs/Header header~%string dataset~%string sensor_name~%string source_topic~%string perturbation_label~%sensor_msgs/PointCloud2 cloud~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: sensor_msgs/PointCloud2~%# This message holds a collection of N-dimensional points, which may~%# contain additional information such as normals, intensity, etc. The~%# point data is stored as a binary blob, its layout described by the~%# contents of the \"fields\" array.~%~%# The point cloud data may be organized 2d (image-like) or 1d~%# (unordered). Point clouds organized as 2d images may be produced by~%# camera depth sensors such as stereo or time-of-flight.~%~%# Time of sensor data acquisition, and the coordinate frame ID (for 3d~%# points).~%Header header~%~%# 2D structure of the point cloud. If the cloud is unordered, height is~%# 1 and width is the length of the point cloud.~%uint32 height~%uint32 width~%~%# Describes the channels and their layout in the binary data blob.~%PointField[] fields~%~%bool    is_bigendian # Is this data bigendian?~%uint32  point_step   # Length of a point in bytes~%uint32  row_step     # Length of a row in bytes~%uint8[] data         # Actual point data, size is (row_step*height)~%~%bool is_dense        # True if there are no invalid points~%~%================================================================================~%MSG: sensor_msgs/PointField~%# This message holds the description of one point entry in the~%# PointCloud2 message format.~%uint8 INT8    = 1~%uint8 UINT8   = 2~%uint8 INT16   = 3~%uint8 UINT16  = 4~%uint8 INT32   = 5~%uint8 UINT32  = 6~%uint8 FLOAT32 = 7~%uint8 FLOAT64 = 8~%~%string name      # Name of field~%uint32 offset    # Offset from start of point struct~%uint8  datatype  # Datatype enumeration, see above~%uint32 count     # How many elements in the field~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'CustomPointCloud)))
  "Returns full string definition for message of type 'CustomPointCloud"
  (cl:format cl:nil "std_msgs/Header header~%string dataset~%string sensor_name~%string source_topic~%string perturbation_label~%sensor_msgs/PointCloud2 cloud~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: sensor_msgs/PointCloud2~%# This message holds a collection of N-dimensional points, which may~%# contain additional information such as normals, intensity, etc. The~%# point data is stored as a binary blob, its layout described by the~%# contents of the \"fields\" array.~%~%# The point cloud data may be organized 2d (image-like) or 1d~%# (unordered). Point clouds organized as 2d images may be produced by~%# camera depth sensors such as stereo or time-of-flight.~%~%# Time of sensor data acquisition, and the coordinate frame ID (for 3d~%# points).~%Header header~%~%# 2D structure of the point cloud. If the cloud is unordered, height is~%# 1 and width is the length of the point cloud.~%uint32 height~%uint32 width~%~%# Describes the channels and their layout in the binary data blob.~%PointField[] fields~%~%bool    is_bigendian # Is this data bigendian?~%uint32  point_step   # Length of a point in bytes~%uint32  row_step     # Length of a row in bytes~%uint8[] data         # Actual point data, size is (row_step*height)~%~%bool is_dense        # True if there are no invalid points~%~%================================================================================~%MSG: sensor_msgs/PointField~%# This message holds the description of one point entry in the~%# PointCloud2 message format.~%uint8 INT8    = 1~%uint8 UINT8   = 2~%uint8 INT16   = 3~%uint8 UINT16  = 4~%uint8 INT32   = 5~%uint8 UINT32  = 6~%uint8 FLOAT32 = 7~%uint8 FLOAT64 = 8~%~%string name      # Name of field~%uint32 offset    # Offset from start of point struct~%uint8  datatype  # Datatype enumeration, see above~%uint32 count     # How many elements in the field~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <CustomPointCloud>))
  (cl:+ 0
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'header))
     4 (cl:length (cl:slot-value msg 'dataset))
     4 (cl:length (cl:slot-value msg 'sensor_name))
     4 (cl:length (cl:slot-value msg 'source_topic))
     4 (cl:length (cl:slot-value msg 'perturbation_label))
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'cloud))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <CustomPointCloud>))
  "Converts a ROS message object to a list"
  (cl:list 'CustomPointCloud
    (cl:cons ':header (header msg))
    (cl:cons ':dataset (dataset msg))
    (cl:cons ':sensor_name (sensor_name msg))
    (cl:cons ':source_topic (source_topic msg))
    (cl:cons ':perturbation_label (perturbation_label msg))
    (cl:cons ':cloud (cloud msg))
))

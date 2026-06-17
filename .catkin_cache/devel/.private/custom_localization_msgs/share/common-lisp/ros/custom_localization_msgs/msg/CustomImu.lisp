; Auto-generated. Do not edit!


(cl:in-package custom_localization_msgs-msg)


;//! \htmlinclude CustomImu.msg.html

(cl:defclass <CustomImu> (roslisp-msg-protocol:ros-message)
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
   (imu
    :reader imu
    :initarg :imu
    :type sensor_msgs-msg:Imu
    :initform (cl:make-instance 'sensor_msgs-msg:Imu)))
)

(cl:defclass CustomImu (<CustomImu>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <CustomImu>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'CustomImu)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name custom_localization_msgs-msg:<CustomImu> is deprecated: use custom_localization_msgs-msg:CustomImu instead.")))

(cl:ensure-generic-function 'header-val :lambda-list '(m))
(cl:defmethod header-val ((m <CustomImu>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:header-val is deprecated.  Use custom_localization_msgs-msg:header instead.")
  (header m))

(cl:ensure-generic-function 'dataset-val :lambda-list '(m))
(cl:defmethod dataset-val ((m <CustomImu>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:dataset-val is deprecated.  Use custom_localization_msgs-msg:dataset instead.")
  (dataset m))

(cl:ensure-generic-function 'sensor_name-val :lambda-list '(m))
(cl:defmethod sensor_name-val ((m <CustomImu>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:sensor_name-val is deprecated.  Use custom_localization_msgs-msg:sensor_name instead.")
  (sensor_name m))

(cl:ensure-generic-function 'source_topic-val :lambda-list '(m))
(cl:defmethod source_topic-val ((m <CustomImu>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:source_topic-val is deprecated.  Use custom_localization_msgs-msg:source_topic instead.")
  (source_topic m))

(cl:ensure-generic-function 'perturbation_label-val :lambda-list '(m))
(cl:defmethod perturbation_label-val ((m <CustomImu>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:perturbation_label-val is deprecated.  Use custom_localization_msgs-msg:perturbation_label instead.")
  (perturbation_label m))

(cl:ensure-generic-function 'imu-val :lambda-list '(m))
(cl:defmethod imu-val ((m <CustomImu>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:imu-val is deprecated.  Use custom_localization_msgs-msg:imu instead.")
  (imu m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <CustomImu>) ostream)
  "Serializes a message object of type '<CustomImu>"
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
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'imu) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <CustomImu>) istream)
  "Deserializes a message object of type '<CustomImu>"
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
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'imu) istream)
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<CustomImu>)))
  "Returns string type for a message object of type '<CustomImu>"
  "custom_localization_msgs/CustomImu")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'CustomImu)))
  "Returns string type for a message object of type 'CustomImu"
  "custom_localization_msgs/CustomImu")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<CustomImu>)))
  "Returns md5sum for a message object of type '<CustomImu>"
  "c8b19871332313c87fa5702b645958bc")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'CustomImu)))
  "Returns md5sum for a message object of type 'CustomImu"
  "c8b19871332313c87fa5702b645958bc")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<CustomImu>)))
  "Returns full string definition for message of type '<CustomImu>"
  (cl:format cl:nil "std_msgs/Header header~%string dataset~%string sensor_name~%string source_topic~%string perturbation_label~%sensor_msgs/Imu imu~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: sensor_msgs/Imu~%# This is a message to hold data from an IMU (Inertial Measurement Unit)~%#~%# Accelerations should be in m/s^2 (not in g's), and rotational velocity should be in rad/sec~%#~%# If the covariance of the measurement is known, it should be filled in (if all you know is the ~%# variance of each measurement, e.g. from the datasheet, just put those along the diagonal)~%# A covariance matrix of all zeros will be interpreted as \"covariance unknown\", and to use the~%# data a covariance will have to be assumed or gotten from some other source~%#~%# If you have no estimate for one of the data elements (e.g. your IMU doesn't produce an orientation ~%# estimate), please set element 0 of the associated covariance matrix to -1~%# If you are interpreting this message, please check for a value of -1 in the first element of each ~%# covariance matrix, and disregard the associated estimate.~%~%Header header~%~%geometry_msgs/Quaternion orientation~%float64[9] orientation_covariance # Row major about x, y, z axes~%~%geometry_msgs/Vector3 angular_velocity~%float64[9] angular_velocity_covariance # Row major about x, y, z axes~%~%geometry_msgs/Vector3 linear_acceleration~%float64[9] linear_acceleration_covariance # Row major x, y z ~%~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%================================================================================~%MSG: geometry_msgs/Vector3~%# This represents a vector in free space. ~%# It is only meant to represent a direction. Therefore, it does not~%# make sense to apply a translation to it (e.g., when applying a ~%# generic rigid transformation to a Vector3, tf2 will only apply the~%# rotation). If you want your data to be translatable too, use the~%# geometry_msgs/Point message instead.~%~%float64 x~%float64 y~%float64 z~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'CustomImu)))
  "Returns full string definition for message of type 'CustomImu"
  (cl:format cl:nil "std_msgs/Header header~%string dataset~%string sensor_name~%string source_topic~%string perturbation_label~%sensor_msgs/Imu imu~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: sensor_msgs/Imu~%# This is a message to hold data from an IMU (Inertial Measurement Unit)~%#~%# Accelerations should be in m/s^2 (not in g's), and rotational velocity should be in rad/sec~%#~%# If the covariance of the measurement is known, it should be filled in (if all you know is the ~%# variance of each measurement, e.g. from the datasheet, just put those along the diagonal)~%# A covariance matrix of all zeros will be interpreted as \"covariance unknown\", and to use the~%# data a covariance will have to be assumed or gotten from some other source~%#~%# If you have no estimate for one of the data elements (e.g. your IMU doesn't produce an orientation ~%# estimate), please set element 0 of the associated covariance matrix to -1~%# If you are interpreting this message, please check for a value of -1 in the first element of each ~%# covariance matrix, and disregard the associated estimate.~%~%Header header~%~%geometry_msgs/Quaternion orientation~%float64[9] orientation_covariance # Row major about x, y, z axes~%~%geometry_msgs/Vector3 angular_velocity~%float64[9] angular_velocity_covariance # Row major about x, y, z axes~%~%geometry_msgs/Vector3 linear_acceleration~%float64[9] linear_acceleration_covariance # Row major x, y z ~%~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%================================================================================~%MSG: geometry_msgs/Vector3~%# This represents a vector in free space. ~%# It is only meant to represent a direction. Therefore, it does not~%# make sense to apply a translation to it (e.g., when applying a ~%# generic rigid transformation to a Vector3, tf2 will only apply the~%# rotation). If you want your data to be translatable too, use the~%# geometry_msgs/Point message instead.~%~%float64 x~%float64 y~%float64 z~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <CustomImu>))
  (cl:+ 0
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'header))
     4 (cl:length (cl:slot-value msg 'dataset))
     4 (cl:length (cl:slot-value msg 'sensor_name))
     4 (cl:length (cl:slot-value msg 'source_topic))
     4 (cl:length (cl:slot-value msg 'perturbation_label))
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'imu))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <CustomImu>))
  "Converts a ROS message object to a list"
  (cl:list 'CustomImu
    (cl:cons ':header (header msg))
    (cl:cons ':dataset (dataset msg))
    (cl:cons ':sensor_name (sensor_name msg))
    (cl:cons ':source_topic (source_topic msg))
    (cl:cons ':perturbation_label (perturbation_label msg))
    (cl:cons ':imu (imu msg))
))

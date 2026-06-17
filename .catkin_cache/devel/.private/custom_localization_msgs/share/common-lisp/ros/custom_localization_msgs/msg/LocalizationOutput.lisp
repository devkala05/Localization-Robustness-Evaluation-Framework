; Auto-generated. Do not edit!


(cl:in-package custom_localization_msgs-msg)


;//! \htmlinclude LocalizationOutput.msg.html

(cl:defclass <LocalizationOutput> (roslisp-msg-protocol:ros-message)
  ((header
    :reader header
    :initarg :header
    :type std_msgs-msg:Header
    :initform (cl:make-instance 'std_msgs-msg:Header))
   (algorithm
    :reader algorithm
    :initarg :algorithm
    :type cl:string
    :initform "")
   (run_id
    :reader run_id
    :initarg :run_id
    :type cl:string
    :initform "")
   (source_topic
    :reader source_topic
    :initarg :source_topic
    :type cl:string
    :initform "")
   (pose
    :reader pose
    :initarg :pose
    :type geometry_msgs-msg:PoseWithCovariance
    :initform (cl:make-instance 'geometry_msgs-msg:PoseWithCovariance))
   (twist
    :reader twist
    :initarg :twist
    :type geometry_msgs-msg:TwistWithCovariance
    :initform (cl:make-instance 'geometry_msgs-msg:TwistWithCovariance)))
)

(cl:defclass LocalizationOutput (<LocalizationOutput>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <LocalizationOutput>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'LocalizationOutput)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name custom_localization_msgs-msg:<LocalizationOutput> is deprecated: use custom_localization_msgs-msg:LocalizationOutput instead.")))

(cl:ensure-generic-function 'header-val :lambda-list '(m))
(cl:defmethod header-val ((m <LocalizationOutput>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:header-val is deprecated.  Use custom_localization_msgs-msg:header instead.")
  (header m))

(cl:ensure-generic-function 'algorithm-val :lambda-list '(m))
(cl:defmethod algorithm-val ((m <LocalizationOutput>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:algorithm-val is deprecated.  Use custom_localization_msgs-msg:algorithm instead.")
  (algorithm m))

(cl:ensure-generic-function 'run_id-val :lambda-list '(m))
(cl:defmethod run_id-val ((m <LocalizationOutput>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:run_id-val is deprecated.  Use custom_localization_msgs-msg:run_id instead.")
  (run_id m))

(cl:ensure-generic-function 'source_topic-val :lambda-list '(m))
(cl:defmethod source_topic-val ((m <LocalizationOutput>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:source_topic-val is deprecated.  Use custom_localization_msgs-msg:source_topic instead.")
  (source_topic m))

(cl:ensure-generic-function 'pose-val :lambda-list '(m))
(cl:defmethod pose-val ((m <LocalizationOutput>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:pose-val is deprecated.  Use custom_localization_msgs-msg:pose instead.")
  (pose m))

(cl:ensure-generic-function 'twist-val :lambda-list '(m))
(cl:defmethod twist-val ((m <LocalizationOutput>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader custom_localization_msgs-msg:twist-val is deprecated.  Use custom_localization_msgs-msg:twist instead.")
  (twist m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <LocalizationOutput>) ostream)
  "Serializes a message object of type '<LocalizationOutput>"
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'header) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'algorithm))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'algorithm))
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'run_id))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'run_id))
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'source_topic))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'source_topic))
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'pose) ostream)
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'twist) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <LocalizationOutput>) istream)
  "Deserializes a message object of type '<LocalizationOutput>"
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'header) istream)
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'algorithm) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'algorithm) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'run_id) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'run_id) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'source_topic) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'source_topic) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'pose) istream)
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'twist) istream)
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<LocalizationOutput>)))
  "Returns string type for a message object of type '<LocalizationOutput>"
  "custom_localization_msgs/LocalizationOutput")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'LocalizationOutput)))
  "Returns string type for a message object of type 'LocalizationOutput"
  "custom_localization_msgs/LocalizationOutput")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<LocalizationOutput>)))
  "Returns md5sum for a message object of type '<LocalizationOutput>"
  "148a87da3ae1cd47c09a5df07478e78a")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'LocalizationOutput)))
  "Returns md5sum for a message object of type 'LocalizationOutput"
  "148a87da3ae1cd47c09a5df07478e78a")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<LocalizationOutput>)))
  "Returns full string definition for message of type '<LocalizationOutput>"
  (cl:format cl:nil "std_msgs/Header header~%string algorithm~%string run_id~%string source_topic~%geometry_msgs/PoseWithCovariance pose~%geometry_msgs/TwistWithCovariance twist~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: geometry_msgs/PoseWithCovariance~%# This represents a pose in free space with uncertainty.~%~%Pose pose~%~%# Row-major representation of the 6x6 covariance matrix~%# The orientation parameters use a fixed-axis representation.~%# In order, the parameters are:~%# (x, y, z, rotation about X axis, rotation about Y axis, rotation about Z axis)~%float64[36] covariance~%~%================================================================================~%MSG: geometry_msgs/Pose~%# A representation of pose in free space, composed of position and orientation. ~%Point position~%Quaternion orientation~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%================================================================================~%MSG: geometry_msgs/TwistWithCovariance~%# This expresses velocity in free space with uncertainty.~%~%Twist twist~%~%# Row-major representation of the 6x6 covariance matrix~%# The orientation parameters use a fixed-axis representation.~%# In order, the parameters are:~%# (x, y, z, rotation about X axis, rotation about Y axis, rotation about Z axis)~%float64[36] covariance~%~%================================================================================~%MSG: geometry_msgs/Twist~%# This expresses velocity in free space broken into its linear and angular parts.~%Vector3 linear~%Vector3 angular~%~%================================================================================~%MSG: geometry_msgs/Vector3~%# This represents a vector in free space. ~%# It is only meant to represent a direction. Therefore, it does not~%# make sense to apply a translation to it (e.g., when applying a ~%# generic rigid transformation to a Vector3, tf2 will only apply the~%# rotation). If you want your data to be translatable too, use the~%# geometry_msgs/Point message instead.~%~%float64 x~%float64 y~%float64 z~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'LocalizationOutput)))
  "Returns full string definition for message of type 'LocalizationOutput"
  (cl:format cl:nil "std_msgs/Header header~%string algorithm~%string run_id~%string source_topic~%geometry_msgs/PoseWithCovariance pose~%geometry_msgs/TwistWithCovariance twist~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: geometry_msgs/PoseWithCovariance~%# This represents a pose in free space with uncertainty.~%~%Pose pose~%~%# Row-major representation of the 6x6 covariance matrix~%# The orientation parameters use a fixed-axis representation.~%# In order, the parameters are:~%# (x, y, z, rotation about X axis, rotation about Y axis, rotation about Z axis)~%float64[36] covariance~%~%================================================================================~%MSG: geometry_msgs/Pose~%# A representation of pose in free space, composed of position and orientation. ~%Point position~%Quaternion orientation~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%================================================================================~%MSG: geometry_msgs/TwistWithCovariance~%# This expresses velocity in free space with uncertainty.~%~%Twist twist~%~%# Row-major representation of the 6x6 covariance matrix~%# The orientation parameters use a fixed-axis representation.~%# In order, the parameters are:~%# (x, y, z, rotation about X axis, rotation about Y axis, rotation about Z axis)~%float64[36] covariance~%~%================================================================================~%MSG: geometry_msgs/Twist~%# This expresses velocity in free space broken into its linear and angular parts.~%Vector3 linear~%Vector3 angular~%~%================================================================================~%MSG: geometry_msgs/Vector3~%# This represents a vector in free space. ~%# It is only meant to represent a direction. Therefore, it does not~%# make sense to apply a translation to it (e.g., when applying a ~%# generic rigid transformation to a Vector3, tf2 will only apply the~%# rotation). If you want your data to be translatable too, use the~%# geometry_msgs/Point message instead.~%~%float64 x~%float64 y~%float64 z~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <LocalizationOutput>))
  (cl:+ 0
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'header))
     4 (cl:length (cl:slot-value msg 'algorithm))
     4 (cl:length (cl:slot-value msg 'run_id))
     4 (cl:length (cl:slot-value msg 'source_topic))
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'pose))
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'twist))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <LocalizationOutput>))
  "Converts a ROS message object to a list"
  (cl:list 'LocalizationOutput
    (cl:cons ':header (header msg))
    (cl:cons ':algorithm (algorithm msg))
    (cl:cons ':run_id (run_id msg))
    (cl:cons ':source_topic (source_topic msg))
    (cl:cons ':pose (pose msg))
    (cl:cons ':twist (twist msg))
))

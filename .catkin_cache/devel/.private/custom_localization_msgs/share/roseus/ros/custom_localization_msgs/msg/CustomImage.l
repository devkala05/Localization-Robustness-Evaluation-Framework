;; Auto-generated. Do not edit!


(when (boundp 'custom_localization_msgs::CustomImage)
  (if (not (find-package "CUSTOM_LOCALIZATION_MSGS"))
    (make-package "CUSTOM_LOCALIZATION_MSGS"))
  (shadow 'CustomImage (find-package "CUSTOM_LOCALIZATION_MSGS")))
(unless (find-package "CUSTOM_LOCALIZATION_MSGS::CUSTOMIMAGE")
  (make-package "CUSTOM_LOCALIZATION_MSGS::CUSTOMIMAGE"))

(in-package "ROS")
;;//! \htmlinclude CustomImage.msg.html
(if (not (find-package "SENSOR_MSGS"))
  (ros::roseus-add-msgs "sensor_msgs"))
(if (not (find-package "STD_MSGS"))
  (ros::roseus-add-msgs "std_msgs"))


(defclass custom_localization_msgs::CustomImage
  :super ros::object
  :slots (_header _dataset _sensor_name _source_topic _perturbation_label _image ))

(defmethod custom_localization_msgs::CustomImage
  (:init
   (&key
    ((:header __header) (instance std_msgs::Header :init))
    ((:dataset __dataset) "")
    ((:sensor_name __sensor_name) "")
    ((:source_topic __source_topic) "")
    ((:perturbation_label __perturbation_label) "")
    ((:image __image) (instance sensor_msgs::Image :init))
    )
   (send-super :init)
   (setq _header __header)
   (setq _dataset (string __dataset))
   (setq _sensor_name (string __sensor_name))
   (setq _source_topic (string __source_topic))
   (setq _perturbation_label (string __perturbation_label))
   (setq _image __image)
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
  (:image
   (&rest __image)
   (if (keywordp (car __image))
       (send* _image __image)
     (progn
       (if __image (setq _image (car __image)))
       _image)))
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
    ;; sensor_msgs/Image _image
    (send _image :serialization-length)
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
     ;; sensor_msgs/Image _image
       (send _image :serialize s)
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
   ;; sensor_msgs/Image _image
     (send _image :deserialize buf ptr-) (incf ptr- (send _image :serialization-length))
   ;;
   self)
  )

(setf (get custom_localization_msgs::CustomImage :md5sum-) "22621967f4644ae479b003055d6c7fdd")
(setf (get custom_localization_msgs::CustomImage :datatype-) "custom_localization_msgs/CustomImage")
(setf (get custom_localization_msgs::CustomImage :definition-)
      "std_msgs/Header header
string dataset
string sensor_name
string source_topic
string perturbation_label
sensor_msgs/Image image

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
MSG: sensor_msgs/Image
# This message contains an uncompressed image
# (0, 0) is at top-left corner of image
#

Header header        # Header timestamp should be acquisition time of image
                     # Header frame_id should be optical frame of camera
                     # origin of frame should be optical center of camera
                     # +x should point to the right in the image
                     # +y should point down in the image
                     # +z should point into to plane of the image
                     # If the frame_id here and the frame_id of the CameraInfo
                     # message associated with the image conflict
                     # the behavior is undefined

uint32 height         # image height, that is, number of rows
uint32 width          # image width, that is, number of columns

# The legal values for encoding are in file src/image_encodings.cpp
# If you want to standardize a new string format, join
# ros-users@lists.sourceforge.net and send an email proposing a new encoding.

string encoding       # Encoding of pixels -- channel meaning, ordering, size
                      # taken from the list of strings in include/sensor_msgs/image_encodings.h

uint8 is_bigendian    # is this data bigendian?
uint32 step           # Full row length in bytes
uint8[] data          # actual matrix data, size is (step * rows)

")



(provide :custom_localization_msgs/CustomImage "22621967f4644ae479b003055d6c7fdd")



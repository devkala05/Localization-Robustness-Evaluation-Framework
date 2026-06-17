// Auto-generated. Do not edit!

// (in-package custom_localization_msgs.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;
let sensor_msgs = _finder('sensor_msgs');
let std_msgs = _finder('std_msgs');

//-----------------------------------------------------------

class CustomImage {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.header = null;
      this.dataset = null;
      this.sensor_name = null;
      this.source_topic = null;
      this.perturbation_label = null;
      this.image = null;
    }
    else {
      if (initObj.hasOwnProperty('header')) {
        this.header = initObj.header
      }
      else {
        this.header = new std_msgs.msg.Header();
      }
      if (initObj.hasOwnProperty('dataset')) {
        this.dataset = initObj.dataset
      }
      else {
        this.dataset = '';
      }
      if (initObj.hasOwnProperty('sensor_name')) {
        this.sensor_name = initObj.sensor_name
      }
      else {
        this.sensor_name = '';
      }
      if (initObj.hasOwnProperty('source_topic')) {
        this.source_topic = initObj.source_topic
      }
      else {
        this.source_topic = '';
      }
      if (initObj.hasOwnProperty('perturbation_label')) {
        this.perturbation_label = initObj.perturbation_label
      }
      else {
        this.perturbation_label = '';
      }
      if (initObj.hasOwnProperty('image')) {
        this.image = initObj.image
      }
      else {
        this.image = new sensor_msgs.msg.Image();
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type CustomImage
    // Serialize message field [header]
    bufferOffset = std_msgs.msg.Header.serialize(obj.header, buffer, bufferOffset);
    // Serialize message field [dataset]
    bufferOffset = _serializer.string(obj.dataset, buffer, bufferOffset);
    // Serialize message field [sensor_name]
    bufferOffset = _serializer.string(obj.sensor_name, buffer, bufferOffset);
    // Serialize message field [source_topic]
    bufferOffset = _serializer.string(obj.source_topic, buffer, bufferOffset);
    // Serialize message field [perturbation_label]
    bufferOffset = _serializer.string(obj.perturbation_label, buffer, bufferOffset);
    // Serialize message field [image]
    bufferOffset = sensor_msgs.msg.Image.serialize(obj.image, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type CustomImage
    let len;
    let data = new CustomImage(null);
    // Deserialize message field [header]
    data.header = std_msgs.msg.Header.deserialize(buffer, bufferOffset);
    // Deserialize message field [dataset]
    data.dataset = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [sensor_name]
    data.sensor_name = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [source_topic]
    data.source_topic = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [perturbation_label]
    data.perturbation_label = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [image]
    data.image = sensor_msgs.msg.Image.deserialize(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += std_msgs.msg.Header.getMessageSize(object.header);
    length += _getByteLength(object.dataset);
    length += _getByteLength(object.sensor_name);
    length += _getByteLength(object.source_topic);
    length += _getByteLength(object.perturbation_label);
    length += sensor_msgs.msg.Image.getMessageSize(object.image);
    return length + 16;
  }

  static datatype() {
    // Returns string type for a message object
    return 'custom_localization_msgs/CustomImage';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '22621967f4644ae479b003055d6c7fdd';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    std_msgs/Header header
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
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new CustomImage(null);
    if (msg.header !== undefined) {
      resolved.header = std_msgs.msg.Header.Resolve(msg.header)
    }
    else {
      resolved.header = new std_msgs.msg.Header()
    }

    if (msg.dataset !== undefined) {
      resolved.dataset = msg.dataset;
    }
    else {
      resolved.dataset = ''
    }

    if (msg.sensor_name !== undefined) {
      resolved.sensor_name = msg.sensor_name;
    }
    else {
      resolved.sensor_name = ''
    }

    if (msg.source_topic !== undefined) {
      resolved.source_topic = msg.source_topic;
    }
    else {
      resolved.source_topic = ''
    }

    if (msg.perturbation_label !== undefined) {
      resolved.perturbation_label = msg.perturbation_label;
    }
    else {
      resolved.perturbation_label = ''
    }

    if (msg.image !== undefined) {
      resolved.image = sensor_msgs.msg.Image.Resolve(msg.image)
    }
    else {
      resolved.image = new sensor_msgs.msg.Image()
    }

    return resolved;
    }
};

module.exports = CustomImage;

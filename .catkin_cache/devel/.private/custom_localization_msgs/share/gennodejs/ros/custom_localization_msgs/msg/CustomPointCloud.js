// Auto-generated. Do not edit!

// (in-package custom_localization_msgs.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;
let std_msgs = _finder('std_msgs');
let sensor_msgs = _finder('sensor_msgs');

//-----------------------------------------------------------

class CustomPointCloud {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.header = null;
      this.dataset = null;
      this.sensor_name = null;
      this.source_topic = null;
      this.perturbation_label = null;
      this.cloud = null;
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
      if (initObj.hasOwnProperty('cloud')) {
        this.cloud = initObj.cloud
      }
      else {
        this.cloud = new sensor_msgs.msg.PointCloud2();
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type CustomPointCloud
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
    // Serialize message field [cloud]
    bufferOffset = sensor_msgs.msg.PointCloud2.serialize(obj.cloud, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type CustomPointCloud
    let len;
    let data = new CustomPointCloud(null);
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
    // Deserialize message field [cloud]
    data.cloud = sensor_msgs.msg.PointCloud2.deserialize(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += std_msgs.msg.Header.getMessageSize(object.header);
    length += _getByteLength(object.dataset);
    length += _getByteLength(object.sensor_name);
    length += _getByteLength(object.source_topic);
    length += _getByteLength(object.perturbation_label);
    length += sensor_msgs.msg.PointCloud2.getMessageSize(object.cloud);
    return length + 16;
  }

  static datatype() {
    // Returns string type for a message object
    return 'custom_localization_msgs/CustomPointCloud';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '2026a2fcbfd25a6438c9efeb4c5b631c';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    std_msgs/Header header
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
    # contents of the "fields" array.
    
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
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new CustomPointCloud(null);
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

    if (msg.cloud !== undefined) {
      resolved.cloud = sensor_msgs.msg.PointCloud2.Resolve(msg.cloud)
    }
    else {
      resolved.cloud = new sensor_msgs.msg.PointCloud2()
    }

    return resolved;
    }
};

module.exports = CustomPointCloud;


(cl:in-package :asdf)

(defsystem "custom_localization_msgs-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils :geometry_msgs-msg
               :sensor_msgs-msg
               :std_msgs-msg
)
  :components ((:file "_package")
    (:file "CustomImage" :depends-on ("_package_CustomImage"))
    (:file "_package_CustomImage" :depends-on ("_package"))
    (:file "CustomImu" :depends-on ("_package_CustomImu"))
    (:file "_package_CustomImu" :depends-on ("_package"))
    (:file "CustomPointCloud" :depends-on ("_package_CustomPointCloud"))
    (:file "_package_CustomPointCloud" :depends-on ("_package"))
    (:file "LocalizationOutput" :depends-on ("_package_LocalizationOutput"))
    (:file "_package_LocalizationOutput" :depends-on ("_package"))
  ))
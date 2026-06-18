# Adaptive-W LVIO build fix 4: link fmt into lvio_fusion_node

The previous build reached the final executable link step and failed with symbols such as:

```text
undefined reference to `fmt::v6::internal::assert_fail(...)`
undefined reference to `fmt::v6::internal::basic_data<void>::digits`
```

This means `fmt/format.h` was found, but the final `lvio_fusion_node` executable was not linked against `libfmt`.

Fix applied:

- keep `libfmt-dev` in the Docker apt dependencies;
- patch upstream `lvio_fusion_node/CMakeLists.txt` with `find_package(fmt REQUIRED)`;
- append `fmt::fmt` or fallback `fmt` to `THIRD_PARTY_LIBS`, which is used by `target_link_libraries(lvio_fusion_node ...)`;
- dump `lvio_fusion_node` catkin logs if a future linker/compiler error appears.

This keeps upstream algorithm source untouched and only patches Docker/CMake integration for ROS Noetic focal.

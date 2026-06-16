# TF/run policy

Use separate entry points:

```bash
./run --algo adaptive_w_lvio --gps off --per 0 --eval --duration 30
./run --algo adaptive_w_lvio --gps on --per 0 --eval --duration 30
```

Dynamic benchmark TF is single-authority:

```text
map -> camera_init          static, from tf_broadcaster_node.py
camera_init -> body        dynamic, from standard_output_republisher.py only
body -> sensors/gnss       static, from tf_broadcaster_node.py
```

Native FAST-LIO/FAST-LIVO /tf is remapped away to avoid TF_REPEATED_DATA.
Adaptive-W internal TF is disabled. RTAB-Map TF is disabled and its cloud is sanitized before use.

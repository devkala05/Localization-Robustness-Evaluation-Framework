#!/usr/bin/env python3
"""Evaluate an estimated TUM trajectory against ground-truth TUM using ATE."""
import argparse
import json
import math
import os
import sys
import numpy as np


def load_tum(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 8:
                continue
            vals = list(map(float, parts))
            if all(math.isfinite(x) for x in vals):
                data.append(vals)
    if not data:
        raise ValueError(f"No valid TUM rows in {path}")
    arr = np.asarray(data, dtype=float)
    return arr[:, 0], arr[:, 1:4]


def associate(t_gt, p_gt, t_est, p_est, max_dt):
    pairs_gt = []
    pairs_est = []
    j = 0
    for i, tg in enumerate(t_gt):
        while j + 1 < len(t_est) and abs(t_est[j + 1] - tg) < abs(t_est[j] - tg):
            j += 1
        if abs(t_est[j] - tg) <= max_dt:
            pairs_gt.append(p_gt[i])
            pairs_est.append(p_est[j])
    if not pairs_gt:
        raise ValueError("No associated trajectory samples. Increase --max-dt or check timestamps.")
    return np.asarray(pairs_gt), np.asarray(pairs_est)


def umeyama_align(src, dst, with_scale=True):
    # Align src -> dst. Returns aligned src, scale, R, t.
    n = src.shape[0]
    mu_src = src.mean(axis=0)
    mu_dst = dst.mean(axis=0)
    src_c = src - mu_src
    dst_c = dst - mu_dst
    cov = (dst_c.T @ src_c) / n
    U, D, Vt = np.linalg.svd(cov)
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[-1, -1] = -1
    R = U @ S @ Vt
    if with_scale:
        var_src = np.mean(np.sum(src_c ** 2, axis=1))
        scale = np.trace(np.diag(D) @ S) / max(var_src, 1e-12)
    else:
        scale = 1.0
    t = mu_dst - scale * (R @ mu_src)
    aligned = (scale * (R @ src.T)).T + t
    return aligned, float(scale), R, t


def save_plot(out_dir, gt, est_aligned, errors):
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return []
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    plt.figure()
    plt.plot(gt[:, 0], gt[:, 1], label="ground truth")
    plt.plot(est_aligned[:, 0], est_aligned[:, 1], label="estimate aligned")
    plt.axis("equal")
    plt.xlabel("x [m]")
    plt.ylabel("y [m]")
    plt.legend()
    p1 = os.path.join(out_dir, "trajectory_xy.png")
    plt.savefig(p1, dpi=150, bbox_inches="tight")
    plt.close()
    paths.append(p1)

    plt.figure()
    plt.plot(errors)
    plt.xlabel("associated sample")
    plt.ylabel("ATE [m]")
    p2 = os.path.join(out_dir, "ate_error.png")
    plt.savefig(p2, dpi=150, bbox_inches="tight")
    plt.close()
    paths.append(p2)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", required=True)
    ap.add_argument("--est", required=True)
    ap.add_argument("--out", default="data/outputs/evaluation")
    ap.add_argument("--max-dt", type=float, default=0.05)
    ap.add_argument("--no-scale", action="store_true", help="Disable scale alignment")
    args = ap.parse_args()

    t_gt, p_gt = load_tum(args.gt)
    t_est, p_est = load_tum(args.est)
    gt_a, est_a = associate(t_gt, p_gt, t_est, p_est, args.max_dt)
    est_aligned, scale, R, trans = umeyama_align(est_a, gt_a, with_scale=not args.no_scale)
    err = np.linalg.norm(est_aligned - gt_a, axis=1)
    metrics = {
        "ground_truth": args.gt,
        "estimate": args.est,
        "associated_samples": int(len(err)),
        "max_association_dt_s": args.max_dt,
        "alignment": "umeyama_scale" if not args.no_scale else "umeyama_se3",
        "scale": scale,
        "ate_rmse_m": float(np.sqrt(np.mean(err ** 2))),
        "ate_mean_m": float(np.mean(err)),
        "ate_median_m": float(np.median(err)),
        "ate_std_m": float(np.std(err)),
        "ate_min_m": float(np.min(err)),
        "ate_max_m": float(np.max(err)),
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    plots = save_plot(os.path.join(args.out, "plots"), gt_a, est_aligned, err)
    print(json.dumps(metrics, indent=2))
    if plots:
        print("plots:")
        for p in plots:
            print("  " + p)


if __name__ == "__main__":
    main()

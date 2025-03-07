import os
import subprocess
from itertools import product
from shapes import DATA_CENTER_SHAPES, MOBILE_SHAPES, MEMORY_SPLITS
from config_generator import generate_config
from cost import compute_cost
import argparse
from scalesim.scale_sim import scalesim

def run_sim(h, w, ifsize, filtsize, ofsize, config_content, config_id) :
    config_path = f"configs/config_{config_id}.cfg"
    result_path = f"results/"
    report_path = f"results/scale_run_{h}x{w}_ifmap{ifsize}_filter{filtsize}_ofmap{ofsize}"
    topo = "/scratch/megankuo/Project3/ML-Simulator/topologies/dnn/dnn_layers.csv"

    with open(config_path, "w") as fh:
        fh.write(config_content)

    sim = scalesim(save_disk_space=False, verbose=True, config=config_path, topology=topo)
    sim.run_scale(top_path=result_path)

    bw_report = os.path.join(report_path, "BANDWIDTH_REPORT.csv")
    cm_report = os.path.join(report_path, "COMPUTE_REPORT.csv")
    cost = compute_cost(bw_report, cm_report)
    return cost

def main():
    best_cost = float('inf')
    best_config = None

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--acc_type", type=str, default="data", choices=["data", "mobile"], help="accelerator type")
    args = parser.parse_args()

    print(f"accelerator type chosen: {args.acc_type}")

    acc_type = DATA_CENTER_SHAPES if args.acc_type == "data" else MOBILE_SHAPES

    for (h,w), (_ifmap, _ofmap) in product(acc_type, MEMORY_SPLITS):
        # 1mb = 1024 kb
        filter_sizekb = (h*w*4) // 1024
        remaining_kb = 1024 - filter_sizekb

        if remaining_kb <= 0: continue

        ifmap_sizekb = int(remaining_kb * _ifmap / 100)
        ofmap_sizekb = int(remaining_kb * _ofmap / 100)

        config_content = generate_config(h, w, ifmap_sizekb, filter_sizekb, ofmap_sizekb)
        config_id = f"{h}x{w}_if{ifmap_sizekb}_fl{filter_sizekb}_of{ofmap_sizekb}"

        print(f"storing config id: {config_id}")

        cost = run_sim(h, w, ifmap_sizekb, filter_sizekb, ofmap_sizekb, config_content, config_id)

        if cost < best_cost:
            best_cost = cost
            best_config = config_content
    print("Best cost: ")
    print(best_cost)
    print("Best config: ")
    print(best_config)

if __name__ == "__main__":
    main()

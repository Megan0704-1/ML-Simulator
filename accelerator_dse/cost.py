import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-b", type=str, required=True, help="bandwidth csv report path")
    parser.add_argument("-c", type=str, required=True, help="compute csv report path")

    args = parser.parse_args()
    cost = compute_cost(args.b, args.c)
    print("total cost: ", cost)


def compute_cost(bandwidth, compute):
    bw_report = pd.read_csv(bandwidth)
    cm_report = pd.read_csv(compute)

    bw_report.columns = [col.strip() for col in bw_report.columns]
    cm_report.columns = [col.strip() for col in cm_report.columns]

    ifmap_bw = bw_report.get("Avg IFMAP DRAM BW")
    filter_bw = bw_report.get("Avg FILTER DRAM BW")
    ofmap_bw = bw_report.get("Avg OFMAP DRAM BW")

    if (ifmap_bw > 20).any() or (filter_bw > 20).any() or (ofmap_bw > 20).any():
        print("Bandwidth exceeds 20.")
        print(f"ifmap bandwidth: {ifmap_bw}")
        print(f"filter bandwidth: {filter_bw}")
        print(f"ofmap bandwidth: {ofmap_bw}")
        return float('inf')

    bw_report["total_bw"] = ifmap_bw + filter_bw + ofmap_bw
    print("Bandwidth report:")
    print(bw_report[["LayerID", "total_bw"]], "\n")

    cm_report["total_cycles"] = cm_report["Total Cycles"]
    print("Compute report:")
    print(cm_report[["LayerID", "total_cycles"]], "\n")

    combine = pd.merge(
        bw_report[["LayerID", "total_bw"]],
        cm_report[["LayerID", "total_cycles"]],
        on = "LayerID"
    )

    combine["cost"] = combine["total_cycles"] * combine["total_bw"]
    total_cost = combine["cost"].sum()

    return total_cost

if __name__ == "__main__":
    main()

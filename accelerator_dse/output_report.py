import csv
import os
import sys
import argparse
import configparser
import re

def parse_run_folder_name(folder_name):
    """
    Parse a run folder name of the form:
      scale_run_{array_height}x{array_width}_ifmap{ifmap}_filter{filter}_ofmap{ofmap}_...
    Returns a dict with the extracted parameters or None if parsing fails.
    """
    pattern = r"scale_run_(\d+)x(\d+)_ifmap(\d+)_filter(\d+)_ofmap(\d+)_.*"
    m = re.search(pattern, folder_name)
    if m:
        return {
            "array_height": int(m.group(1)),
            "array_width": int(m.group(2)),
            "ifmap": int(m.group(3)),
            "filter": int(m.group(4)),
            "ofmap": int(m.group(5)),
        }
    else:
        return None

def parse_config_filename(filename):
    """
    Parse a config filename of the form:
      config_{array_height}x{array_width}_if{if}_fl{fl}_of{of}.cfg
    Returns a dict with the extracted parameters or None if parsing fails.
    """
    pattern = r"config_(\d+)x(\d+)_if(\d+)_fl(\d+)_of(\d+)\.cfg"
    m = re.search(pattern, filename)
    if m:
        return {
            "array_height": int(m.group(1)),
            "array_width": int(m.group(2)),
            "if": int(m.group(3)),
            "fl": int(m.group(4)),
            "of": int(m.group(5)),
            "filename": filename  # Save the filename for later use.
        }
    else:
        return None

def select_best_config(run_params, config_folder):
    """
    Look in the config folder for files that have matching array dimensions.
    For each candidate, compute a difference score based on the absolute differences between:
       run ifmap vs. config if,
       run filter vs. config fl,
       run ofmap vs. config of.
    Returns the full path to the config file with the smallest difference or None if no candidate exists.
    """
    candidates = []
    for f in os.listdir(config_folder):
        if f.lower().startswith("config_") and f.lower().endswith(".cfg"):
            config_info = parse_config_filename(f)
            if config_info is None:
                continue
            # Only consider configs with matching array dimensions.
            if (config_info["array_height"] == run_params["array_height"] and
                config_info["array_width"] == run_params["array_width"]):
                diff = (abs(run_params["ifmap"] - config_info["if"]) +
                        abs(run_params["filter"] - config_info["fl"]) +
                        abs(run_params["ofmap"] - config_info["of"]))
                config_info["diff"] = diff
                candidates.append(config_info)
    if not candidates:
        return None
    best = min(candidates, key=lambda x: x["diff"])
    return os.path.join(config_folder, best["filename"])

def process_folder(run_folder, config_folder):
    run_folder_name = os.path.basename(run_folder)
    run_params = parse_run_folder_name(run_folder_name)
    if run_params is None:
        print(f"Skipping folder '{run_folder}': Unable to parse run folder name.")
        return

    config_file = select_best_config(run_params, config_folder)
    if config_file is None:
        print(f"Skipping folder '{run_folder}': No matching config file found for array size {run_params['array_height']}x{run_params['array_width']}.")
        return

    # Load the selected configuration file.
    config = configparser.ConfigParser()
    config.read(config_file)
    config_run_name = config.get("general", "run_name", fallback=run_folder_name)

    try:
        arch = config["architecture_presets"]
        array_height = int(arch["ArrayHeight"])
        array_width = int(arch["ArrayWidth"])
        ifmap_sram = int(arch["IfmapSramSzkB"])
        filter_sram = int(arch["FilterSramSzkB"])
        ofmap_sram = int(arch["OfmapSramSzkB"])
    except KeyError as e:
        print(f"Missing architecture parameter in config file '{config_file}': {e}")
        return

    # Define paths for the report CSVs in this run folder.
    compute_report = os.path.join(run_folder, "COMPUTE_REPORT.csv")
    bandwidth_report = os.path.join(run_folder, "BANDWIDTH_REPORT.csv")
    output_csv = os.path.join(run_folder, "output_report.csv")

    if not os.path.exists(compute_report) or not os.path.exists(bandwidth_report):
        print(f"Skipping folder '{run_folder}': missing one or both report files.")
        return

    # Read compute report data.
    compute_data = {}
    with open(compute_report, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                layer_id = int(row["LayerID"])
                compute_data[layer_id] = {"cycles": int(row[" Total Cycles"]), "stalls": int(row[" Stall Cycles"])}
            except (KeyError, ValueError):
                print("Error processing a row in compute report; skipping row.")

    # Read bandwidth report data.
    bandwidth_data = {}
    with open(bandwidth_report, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                layer_id = int(row["LayerID"])
                bandwidth_data[layer_id] = {
                    "avg_ifmap_bw": float(row[" Avg IFMAP DRAM BW"]),
                    "avg_filter_bw": float(row[" Avg FILTER DRAM BW"]),
                    "avg_ofmap_bw": float(row[" Avg OFMAP DRAM BW"]),
                }
            except (KeyError, ValueError):
                print("Error processing a row in bandwidth report; skipping row.")

    # Generate the output CSV file.
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Run Name", "Layer ID", "Array Size",
            "Ifmap SRAM Size (kB)", "Filter SRAM Size (kB)", "OFMAP SRAM Size (kB)",
            "Cycles", "Stalls", "Avg DRAM IFMAP BW", "Avg DRAM Filter BW", "Avg DRAM OFMAP BW", "Cost"
        ])

        # Process each layer from the compute report.
        for layer_id, comp in compute_data.items():
            cycles = comp["cycles"]
            stalls = comp["stalls"]
            bw = bandwidth_data.get(layer_id, {})
            avg_ifmap_bw = bw.get("avg_ifmap_bw", 0)
            avg_filter_bw = bw.get("avg_filter_bw", 0)
            avg_ofmap_bw = bw.get("avg_ofmap_bw", 0)
            cost = cycles * (avg_ifmap_bw + avg_filter_bw + avg_ofmap_bw)
            writer.writerow([
                config_run_name,
                layer_id,
                f"{array_height}x{array_width}",
                ifmap_sram,
                filter_sram,
                ofmap_sram,
                cycles,
                stalls,
                avg_ifmap_bw,
                avg_filter_bw,
                avg_ofmap_bw,
                cost,
            ])

    print(f"Output CSV generated in folder '{run_folder}': {output_csv}")

def concat_output_reports(root_folder, final_output_csv):
    """
    Walk through the root folder recursively, find all output_report.csv files,
    and concatenate them into one final CSV file (with a single header).
    """
    all_rows = []
    header = None

    for dirpath, _, filenames in os.walk(root_folder):
        if "output_report.csv" in filenames:
            file_path = os.path.join(dirpath, "output_report.csv")
            with open(file_path, "r") as f:
                reader = csv.reader(f)
                try:
                    file_header = next(reader)
                except StopIteration:
                    continue  # Empty file, skip.
                if header is None:
                    header = file_header
                    all_rows.append(header)
                elif file_header != header:
                    print(f"Warning: Header mismatch in file {file_path}.")
                for row in reader:
                    all_rows.append(row)

    if all_rows:
        with open(final_output_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(all_rows)
        print(f"Final concatenated report generated: {final_output_csv}")
    else:
        print("No output_report.csv files found to concatenate.")

def main():
    parser = argparse.ArgumentParser(
        description=("Process compute and bandwidth reports in subfolders of a given root folder "
                     "using configuration files from a config folder matched by similar parameters.")
    )
    parser.add_argument("root_folder", help="Root folder containing subfolders with report CSV files.")
    parser.add_argument("config_folder", help="Folder containing configuration files (with .cfg extension).")
    args = parser.parse_args()

    root_folder = args.root_folder
    config_folder = args.config_folder

    if not os.path.isdir(root_folder):
        print(f"Error: '{root_folder}' is not a valid directory.")
        sys.exit(1)
    if not os.path.isdir(config_folder):
        print(f"Error: '{config_folder}' is not a valid directory.")
        sys.exit(1)

    # List all subdirectories in the root folder.
    subfolders = [
        os.path.join(root_folder, d)
        for d in os.listdir(root_folder)
        if os.path.isdir(os.path.join(root_folder, d))
    ]

    if not subfolders:
        print(f"No subfolders found in '{root_folder}'.")
        sys.exit(1)

    # Process each subfolder (each corresponding to one run).
    for folder in subfolders:
        process_folder(folder, config_folder)

    # After processing all runs, concatenate all output_report.csv files into one final report.
    final_output_csv = os.path.join(root_folder, "final_output_report.csv")
    concat_output_reports(root_folder, final_output_csv)

if __name__ == "__main__":
    main()

import os
os.environ["OMP_NUM_THREADS"] = "1"
import cv2
cv2.setNumThreads(0)
cv2.ocl.setUseOpenCL(False)

import argparse
import pandas as pd
import multiprocessing as mp
from tqdm import tqdm

DATAPATH = ""
IMG_COL = ""


def open_image_okay(row):
    global DATAPATH, IMG_COL
    filepath = row[IMG_COL]
    image_path = DATAPATH + filepath
    try:
        img = cv2.imread(image_path)
        flag = img is not None
        return flag
    except:
        return False


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-csv", type=str, required=True)
    parser.add_argument("--img-datapath", type=str, default=None)
    parser.add_argument("--img-col", type=str, required=True)
    parser.add_argument("--out-csv", type=str, required=True)
    parser.add_argument("--n-cpu", type=int, default=None)

    args = parser.parse_args()
    return args


def main(args):
    global DATAPATH, IMG_COL
    DATAPATH = args.img_datapath or ""
    IMG_COL = args.img_col

    df = pd.read_csv(args.in_csv)
    n_cpu = args.n_cpu or mp.cpu_count()

    df_ = df.dropna(subset=[IMG_COL])
    df_l = list(df_.to_dict("index").values())

    with mp.Pool(n_cpu) as p:
        flags = list(tqdm(p.imap(open_image_okay, df_l), total=len(df_l)))

    df_["flag"] = flags
    df_out = df_[df_["flag"]]
    df_out.drop(columns=["flag"], inplace=True)
    df_out.to_csv(args.out_csv, index=False)

    n_lines = sum(flags)
    percent = 1 - sum(flags) / len(flags)
    percent = round(percent, 2)
    print(f"Lines deleted: {n_lines} ({percent}%)")


if __name__ == "__main__":
    args = parse_args()
    main(args)

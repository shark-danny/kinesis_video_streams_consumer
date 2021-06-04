import os
import sys
import lmdb
import h5py
import numpy as np
import argparse
import subprocess
import json
import shutil

from tqdm import tqdm
from subprocess import call
import pickle


def read_img(path):
    with open(path, 'rb') as f:
        return f.read()


parser = argparse.ArgumentParser()
# resize options
parser.add_argument("-a", "--asis", action="store_true", help="do not resize frames")
parser.add_argument("-s", "--short", type=int, default=0, help="keep the aspect ration and scale the shorter side to s")
parser.add_argument("-H", "--height", type=int, default=0, help="the resized height")
parser.add_argument("-W", "--width", type=int, default=0, help="the resized width")
# frame sampling options
parser.add_argument("-k", "--skip", type=int, default=1, help="only store frames with (ID-1) mod skip==0, frame ID starts from 1")
parser.add_argument("-n", "--num_frame", type=int, default=-1, help="uniformly sample n frames, this will override --skip")
parser.add_argument("-r", "--interval", type=int, default=0, help="extract one frame every r seconds")

args = parser.parse_args()

def get_frame_rate(vid):
    call = ["ffprobe", "-v", "quiet", "-show_entries", "stream=r_frame_rate", "-print_format", "json", vid]
    output = subprocess.check_output(call)
    output = json.loads(output)
    r_frame_rate = 0
    if len(output.keys()) == 0:
        return r_frame_rate
    elif output['streams'] == []:
        return r_frame_rate

    for line in output['streams']:
        nums = line['r_frame_rate'].split('/')
        if float(nums[1]) == 0:
            continue
        frame_rate = 1.0 * float(nums[0]) / float(nums[1])
        if frame_rate != 0:
            r_frame_rate = frame_rate

    return r_frame_rate

# sanity check of the options
if args.asis:
    assert args.short == 0 and args.height == 0 and args.width == 0
if args.short > 0:
    assert (not args.asis) and args.height == 0 and args.width == 0
if args.height > 0 or args.width > 0:
    assert (not args.asis) and args.height > 0 and args.width > 0 and args.short == 0

all_videos = ["C:\\Users\\HP\\Desktop\\vid\\vid2frame\\sample_videos\\ts_backtodecember_30.mp4"]

tmp_dir = 'C:\\Users\\HP\\Desktop'

done_videos = set()

for vid in tqdm(all_videos, ncols=64):
    #vvid = vid.split('/')[-1].split('.')[0]
    vvid, _ = os.path.splitext(vid) # discard extension
    _, vvid = os.path.split(vvid)   # get filename without path
    if vvid in done_videos:
        print ('video %s seen before, ignored.' % vvid)

    v_dir = os.path.join(tmp_dir, vvid)
    #call(["del", v_dir],shell=True)
    if os.path.exists(v_dir):
        shutil.rmtree(v_dir)
    os.mkdir(v_dir)    # caching directory to store ffmpeg extracted frames

    args.width=500
    args.height=500
    if args.asis:
        vf_scale = []
    elif args.short > 0:
        vf_scale = ["-vf",
                    "scale='iw*1.0/min(iw,ih)*%d':'ih*1.0/min(iw,ih)*%d'" \
                            % (args.short, args.short)]
    elif args.height > 0 and args.width > 0:
        vf_scale = ["-vf", "scale=%d:%d" % (args.width, args.height)]
    else:
        raise Exception('Unspecified frame scale option')
    args.interval=1
    if args.interval > 0:
        r_frame_rate = get_frame_rate(vid)
        if r_frame_rate == 0:
            print("frame rate is 0, skip: %s"%vid)
            continue
        vf_sample = ["-vsync","vfr",
                     "-vf","select=not(mod(n\,%d))" % (int(round(args.interval*r_frame_rate)))]
        assert args.num_frame <= 0 and args.skip == 1, \
                "No other sampling options are allowed when --interval is set"
    else:
        vf_sample = []

    call(["ffmpeg",
            "-loglevel", "panic",
            "-i", vid,
            ]
            + vf_scale
            + vf_sample
            +
            [
            "-qscale:v", "2",
            v_dir+"/%8d.jpg"],shell=True)

    sample = (args.num_frame > 0)
    if sample:
        ids = [int(f.split('.')[0]) for f in os.listdir(v_dir)]
        sample_ids = set(list(np.linspace(min(ids), max(ids),
                                args.num_frame, endpoint=True, dtype=np.int32)))

    files = []
    for f_name in os.listdir(v_dir):
        fid = int(f_name.split('.')[0])

        if sample:
            if fid not in sample_ids:
                continue
        elif args.skip > 1:
            if (fid-1) % args.skip != 0:
                continue
        files.append((fid, f_name))


    for fid, f_name in files:
        s = read_img(os.path.join(v_dir, f_name))
        key = "%s/%08d" % (vvid, fid)   # by padding zeros, frames in db are stored in order

    call(["rm", "-rf", v_dir])
    done_videos.add(vvid)

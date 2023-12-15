"""
Utilities functions related to the examples execution
"""
import os
from pathlib import Path
import shutil
from tempfile import gettempdir
import numpy as np
import matplotlib.pyplot as plt
from tifffile import imread


class UserTempDirectory:
    """ Class to call user temp via the 'with' statement """

    def __enter__(self):
        return gettempdir()

    def __exit__(self, exc, value, tb):
        pass


def init_dir(dirpath, case):
    """ Initialize the project directory """
    dirname = Path(dirpath) / f'pystack3d_{case}'
    os.makedirs(dirname, exist_ok=True)

    # delete .tif to avoid bad surprises when working with user temp
    for fname in dirname.glob("*.tif"):
        os.remove(fname)

    src = Path(__file__).parent / f'params_{case}.toml'
    dst = dirname / 'params.toml'
    shutil.copy(src, dst)
    return dirname


def postpro(process_steps, input_dir, channel, verbosity=False):
    """ Return 'dirnames', 'labels' and 'stats' related to each process step """
    if not isinstance(process_steps, list):
        process_steps = [process_steps]

    input_dir = Path(input_dir)
    dirnames = [input_dir / channel]
    labels = ['input']
    for process_step in process_steps:
        if process_step != 'registration_calculation':
            dirnames.append(input_dir / 'process' / process_step / channel)
            if process_step == 'registration_transformation':
                labels.append('registration')
            else:
                labels.append(process_step)

    fname = Path(dirnames[-1]) / 'outputs' / 'stats.npy'
    stats = np.load(fname)
    stats_vals = []
    stats_labels = ['min', 'max', 'mean']
    for j, pfx in zip([0, 2], ['input', 'output']):
        for k in range(3):
            values = stats[:, j, k]
            vmin, vmax = np.nanmin(values), np.nanmax(values)
            stats_vals.append([vmin, vmax])
            if verbosity:
                print(f"{pfx}-{stats_labels[k]}: {vmin} {vmax}")
    stats_vals = np.asarray(stats_vals)

    return dirnames, labels, stats_vals


def plot_results(dirnames, labels, vmin, vmax):
    """ Plot results related to the different process steps """

    ncol = len(dirnames)
    fig, ax = plt.subplots(2, ncol, sharex='col', figsize=(2.5 * ncol, 5))
    fig.tight_layout(pad=2.5)
    plt.rcParams["image.origin"] = 'lower'

    for i, (dirname, label) in enumerate(zip(dirnames, labels)):
        fnames = sorted(dirname.glob('*.tif'))
        if len(fnames) != 0:
            arr = imread(fnames)
            ic, jc, _ = tuple(int(x / 2) for x in arr.shape)
            ax[0, i].set_title(label)
            ax[0, i].imshow(np.flipud(arr[ic, :, :]), vmin=vmin, vmax=vmax)
            ax[0, i].axis('auto')
            ax[1, i].imshow(arr[:, jc, :], vmin=vmin, vmax=vmax)
            ax[1, i].axis('auto')

            if i == 0:
                ax[0, 0].set_ylabel("Y")
                ax[0, 0].set_xlabel("X")
                add_cutplane_line(ax[0, 0], jc, arr.shape[2], arr.shape[1])
                ax[1, 0].set_ylabel("Z")
                ax[1, 0].set_xlabel("X")
                add_cutplane_line(ax[1, 0], ic, arr.shape[2], -arr.shape[0])

            # # CROPPING
            # from matplotlib.patches import Rectangle
            # rect = Rectangle((5, 2), 40, 40, fc='none', ec='r', ls='--', lw=2)
            # ax[0, 0].add_patch(rect)
            # ax[1, 0].axvline(x=5, c="r", ls="--", lw=2)
            # ax[1, 0].axvline(x=45, c="r", ls="--", lw=2)


def add_cutplane_line(ax, ind, width, height):
    """ Add cutplane representation with related arrows """
    for position_rel in [0.05, 0.95]:
        xy = (position_rel * width, ind)
        xytext = (position_rel * width, ind + 0.1 * height)
        ax.axhline(y=ind, ls='--', lw='0.5', color='w')
        ax.annotate("", xy=xy, xytext=xytext,
                    arrowprops={"arrowstyle": '->', "color": 'w'})

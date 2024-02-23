#
# Copyright 2024 Universidad Complutense de Madrid
#
# This file is part of FRIDA DRP
#
# SPDX-License-Identifier: GPL-3.0-or-later
# License-Filename: LICENSE.txt
#

import argparse
from astropy.coordinates import SkyCoord
import astropy.units as u
import json
import numpy as np
import pooch
import sys

from .ifu_simulator import ifu_simulator

from fridadrp._version import version
from fridadrp.processing.define_3d_wcs import define_3d_wcs
from fridadrp.processing.linear_wavelength_calibration_frida import LinearWaveCalFRIDA

# Parameters
from fridadrp.core import FRIDA_NAXIS1_HAWAII
from fridadrp.core import FRIDA_NAXIS2_HAWAII
from fridadrp.core import FRIDA_NAXIS1_IFU
from fridadrp.core import FRIDA_NAXIS2_IFU
from fridadrp.core import FRIDA_NSLICES
from fridadrp.core import FRIDA_VALID_GRATINGS
from fridadrp.core import FRIDA_VALID_SPATIAL_SCALES
from fridadrp.core import FRIDA_SPATIAL_SCALE


def define_auxiliary_files(grating, verbose):
    """"Define auxiliary files for requested configuration

    Parameters
    ----------
    grating : str
        Grating name.
    verbose : bool
        If True, display/plot additional information.

    Returns
    -------
    outdict : dictionary
        Dictionary with the file name of the auxiliary files.
        The dictionary keys are the following:
        - skycalc: table with SKYCALC Sky Model Calculator predictions
        - flatpix2pix: pixel-to-pixel flat field
        - model_ifu2detector: 2D polynomial transformation from
          (x_ifu, y_ify, wavelength) to (x_detector, y_detector)

    """

    # retrieve configuration file
    base_url = 'http://nartex.fis.ucm.es/~ncl/fridadrp_simulator_data'
    # note: compute md5 hash from terminal using:
    # linux $ md5sum <filename>
    # macOS $ md5 <filename>
    fconf = pooch.retrieve(
        f'{base_url}/configuration_FRIDA_IFU_simulator.json',
        known_hash='md5:9befc9554521b062bd444cb80e730333',
        path=pooch.os_cache(project="fridadrp"),
        progressbar=True
    )
    dconf = json.loads(open(fconf, mode='rt').read())
    if verbose:
        print(f"Configuration file uuid: {dconf['uuid']}")

    # generate registry for all the auxiliary files to be used by Pooch
    d = dconf['auxfiles']
    registry_md5 = {}
    registry_label = {}
    # SKYCALC Sky Model Calculator prediction table
    label = 'skycalc'
    filename = d[label]['filename']
    registry_label[filename] = label
    registry_md5[filename] = f"md5:{d[label]['md5']}"
    # EMIR arc lines
    label = 'EMIR-arc-delta-lines'
    filename = d[label]['filename']
    registry_label[filename] = label
    registry_md5[filename] = f"md5:{d[label]['md5']}"
    # pixel-to-pixel flat field
    label = 'flatpix2pix'
    filename = d[label][grating]['filename']
    md5 = d[label][grating]['md5']
    if (filename is not None) and (md5 is not None):
        registry_label[filename] = label
        registry_md5[filename] = f'md5:{md5}'
    else:
        raise SystemExit(f'Error: grating {grating} has not yet been defined!')
    # 2D polynomial transformation from IFU (x_ifu, y_ifu, wavelength) to
    # Hawaii coordinates (x_hawaii, y_hawaii)
    label = 'model_ifu2detector'
    filename = d[label][grating]['filename']
    md5 = d[label][grating]['md5']
    if (filename is not None) and (md5 is not None):
        registry_label[filename] = label
        registry_md5[filename] = f'md5:{md5}'
    else:
        raise SystemExit(f'Error: grating {grating} has not yet been defined!')

    # create a Pooch instance with the previous registry
    pooch_inst = pooch.create(
        # use the default cache folder for the operating system
        path=pooch.os_cache(project="fridadrp"),
        # base URL for the remote data source
        base_url=base_url,
        # specify the files that can be fetched
        registry=registry_md5
    )

    # initialize output dictionary
    faux_dict = {}
    for item in registry_md5:
        try:
            faux = pooch_inst.fetch(item, progressbar=True)
            label = registry_label[item]
            faux_dict[label] = faux
        except BaseException as e:
            raise SystemExit(e)

    return faux_dict


def main(args=None):
    # parse command-line options
    parser = argparse.ArgumentParser(
        description=f"description: simulator of FRIDA IFU images ({version})"
    )
    parser.add_argument("scene", help="YAML scene file name", type=str)
    parser.add_argument("--grating", help="Grating name", type=str, choices=FRIDA_VALID_GRATINGS, default="medium-K")
    parser.add_argument("--scale", help="Scale", type=str, choices=FRIDA_VALID_SPATIAL_SCALES, default="fine")
    parser.add_argument("--ra_center_deg", help="Central RA coordinate (deg)", type=float, default=0.0)
    parser.add_argument("--dec_center_deg", help="Central DEC coordinate (deg)", type=float, default=0.0)
    parser.add_argument("--transmission", help="Apply atmosphere transmission", action="store_true")
    parser.add_argument("--rnoise", help="Readout noise (ADU)", type=float, default=0)
    parser.add_argument("--flatpix2pix", help="Pixel-to-pixel flat field", type=str, default="default",
                        choices=["default", "none"])
    parser.add_argument("--seed", help="Seed for random number generator", type=int, default=1234)
    parser.add_argument("-v", "--verbose", help="increase program verbosity", action="store_true")
    parser.add_argument("--plots", help="plot intermediate results", action="store_true")
    parser.add_argument("--echo", help="Display full command line", action="store_true")

    args = parser.parse_args(args=args)

    print(f"Welcome to fridadrp-ifu_simulator\nversion {version}\n")

    if len(sys.argv) == 1:
        parser.print_usage()
        raise SystemExit()

    if args.echo:
        print('\033[1m\033[31m% ' + ' '.join(sys.argv) + '\033[0m\n')

    # simplify argument names
    scene = args.scene
    grating = args.grating
    scale = args.scale
    ra_center_deg = args.ra_center_deg
    dec_center_deg = args.dec_center_deg
    transmission = args.transmission  # ToDo: take into account
    rnoise = args.rnoise  # ToDo: take into account
    if rnoise < 0:
        raise ValueError(f'Invalid readout noise value: {rnoise}')
    flatpix2pix = args.flatpix2pix  # ToDo: take into account
    seed = args.seed
    verbose = args.verbose
    plots = args.plots

    # define auxiliary files
    faux_dict = define_auxiliary_files(grating, verbose=verbose)

    # World Coordinate System of the data cube
    skycoord_center = SkyCoord(ra=ra_center_deg * u.deg, dec=dec_center_deg * u.deg, frame='icrs')

    # linear wavelength calibration
    wv_lincal = LinearWaveCalFRIDA(grating=grating)
    if verbose:
        print(f'\n{wv_lincal}')

    # define WCS object to store the spatial 2D WCS
    # and the linear wavelength calibration
    wcs = define_3d_wcs(
        naxis1_ifu=FRIDA_NAXIS1_IFU,
        naxis2_ifu=FRIDA_NAXIS2_IFU,
        skycoord_center=skycoord_center,
        spatial_scale= FRIDA_SPATIAL_SCALE[scale],
        wv_lincal=wv_lincal,
        verbose=verbose
    )

    # initilize random number generator with provided seed
    rng = np.random.default_rng(seed)

    ifu_simulator(
        wcs=wcs,
        wv_lincal=wv_lincal,
        naxis1_detector=FRIDA_NAXIS1_HAWAII,
        naxis2_detector=FRIDA_NAXIS2_HAWAII,
        scene=scene,
        faux_dict=faux_dict,
        rng=rng,
        verbose=verbose,
        plots=plots
    )


if __name__ == "__main__":

    main()

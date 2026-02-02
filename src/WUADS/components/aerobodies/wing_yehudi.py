from .wing_advanced import Wing_advanced
import numpy as np
import logging

logger = logging.getLogger(__name__)

class Wing_Yehudi(Wing_advanced):

    def __init__(self, params):
        # Notes:
        # must define sweep by the leading edge

        self.params = params

        # Note: you define the trapezoidal reference wing the same way you would normally, with a seperate yehudi_span variable
        self.yehudi_break = 0

        # Generate section data
        semi_span = params['span'] / 2
        xle = params['xle']
        yle = params['yle']
        zle = params['zle']
        yehudi_break = params['yehudi_break']
        sweep_le = params['sweep'] * np.pi / 180.0
        dihedral = params['dihedral'] * np.pi / 180.0
        area = params['area']
        taper = params['taper']
        cr = 2 * area / (2 * semi_span * (1 + taper))
        ct = cr * taper

        yle_break = yle + semi_span * yehudi_break
        xle_break = xle + (yle_break - yle) * np.tan(sweep_le)
        zle_break = zle + (yle_break - yle) * np.tan(dihedral)
        chord_break = cr + yehudi_break * (ct - cr)
        x_te_break = xle_break + chord_break
        chord_root = x_te_break - xle

        section_1_params = {
            'cr': chord_root,
            'ct': chord_break,
            'length': (yle_break - yle),
            'sweep': params['sweep'],
            'sweep_location': 0,
            'dihedral': params['dihedral']
        }

        section_2_params = {
            'ct': ct,
            'length': (semi_span - (yle_break - yle)),
            'sweep': params['sweep'],
            'sweep_location': 0,
            'dihedral': params['dihedral']
        }

        params['sections'] = [section_1_params, section_2_params]

        if 'winglet' in params:
            p = params['winglet']
            winglet_params = {
                'ct': p['ct'],
                'length': p['length'],
                'sweep': p['sweep'],
                'sweep_location': 0,
                'dihedral': p['dihedral']
            }

        super().__init__(params)
        self.component_type = 'wing_advanced'

    def update(self, variable, value, **kwargs):
        params = self.params
        params[variable] = value
        self.__dict__.update(params)

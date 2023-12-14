#
# Copyright 2016-2023 Universidad Complutense de Madrid
#
# This file is part of Frida DRP
#
# SPDX-License-Identifier: GPL-3.0-or-later
# License-Filename: LICENSE
#

from numina.instrument.generic import InstrumentGeneric, ComponentGeneric


class FridaInstrument(InstrumentGeneric):
    def __init__(self, name, properties=None, origin=None, parent=None):
        super().__init__(name, parent=parent)


class FridaDetector(ComponentGeneric):
    def __init__(self, name, properties=None, origin=None, parent=None):
        super().__init__(name, parent=parent, properties=properties, origin=origin)

    @property
    def other_property(self):
        return 121

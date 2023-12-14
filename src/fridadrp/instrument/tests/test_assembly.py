
import fridadrp.loader
import numina.instrument.assembly as asb
import numina.instrument.generic
from fridadrp.instrument.components import FridaInstrument
import numina.instrument.configorigin


def load_instrument():
    drp = fridadrp.loader.drp_load()
    pkg_paths = [drp.profiles]
    com_store = asb.load_paths_store(pkg_paths, [])
    uuid_str = "c7f94f7d-1f57-4644-86d6-7004a2506680"
    date_str = "2023-10-01T12:00:00"
    instrument = asb.assembly_instrument(com_store, uuid_str, date_str, by_key="uuid")
    return instrument


def test_assembly1():
    drp = fridadrp.loader.drp_load()
    pkg_paths = [drp.profiles]
    com_store = asb.load_paths_store(pkg_paths, [])
    uuid_str = "c7f94f7d-1f57-4644-86d6-7004a2506680"
    date_str = "2023-10-01T12:00:00"
    instrument = asb.assembly_instrument(com_store, uuid_str, date_str, by_key="uuid")
    assert isinstance(instrument, FridaInstrument)


def test_assembly2():
    import fridadrp.loader
    import numina.instrument.assembly as asb

    drp = fridadrp.loader.drp_load()
    pkg_paths = [drp.profiles]
    com_store = asb.load_paths_store(pkg_paths, [])
    date_str = "2023-10-01T12:00:00"
    instrument = asb.assembly_instrument(com_store, "FRIDA", date_str, by_key="name")
    assert isinstance(instrument, numina.instrument.generic.InstrumentGeneric)


def test_assembly3():
    instrument = load_instrument()
    detector = instrument.get_device('detector')
    assert isinstance(detector, numina.instrument.generic.ComponentGeneric)
    assert str(detector.uuid) == "79411117-50d4-481d-bd78-d06b1660ae13"


def test_assembly4():
    instrument = load_instrument()
    detector = instrument.get_device('detector')
    assert tuple(detector.shape) == (2048, 2048)
    detector = instrument.get_device('detector')
    assert tuple(detector.get_property("shape")) == (2048, 2048)
    assert tuple(instrument.get_property("detector.shape")) == (2048, 2048)


def test_assembly5():
    instrument = load_instrument()
    state = {'readmode': "B"}
    assert instrument.get_value("detector.ron", **state) == 100
    assert instrument.get_value("detector.other_property", **state) == 121


def test_assembly6():
    instrument = load_instrument()
    assert isinstance(instrument.origin, numina.instrument.configorigin.ElementOrigin)
    origin = instrument.origin
    assert origin.name == "FRIDA"
    assert str(origin.uuid) == "c7f94f7d-1f57-4644-86d6-7004a2506680"


def test_assembly7():
    instrument = load_instrument()

    dev = instrument.get_device("detector")
    assert dev._internal_state == {'readmode': 'A'}


def test_assembly8():
    instrument = load_instrument()

    deps = instrument.depends_on()
    assert deps == {'readmode'}

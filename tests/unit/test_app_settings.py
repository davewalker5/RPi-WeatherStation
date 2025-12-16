from registry import AppSettings


def test_general_settings():
    settings = AppSettings(AppSettings.default_settings_file())

    assert 1 == settings.settings["bus_number"]
    assert 5 == settings.settings["display_interval"]
    assert "0.0.0.0" == settings.settings["hostname"]
    assert 8080 == settings.settings["port"]
    assert 60 == settings.settings["sample_interval"]

def test_device_settings():
    settings = AppSettings(AppSettings.default_settings_file())

    assert 5 == len(settings.devices)

    assert "MUX" in settings.devices
    assert "BME280" in settings.devices
    assert "VEML7700" in settings.devices
    assert "SGP40" in settings.devices
    assert "LCD" in settings.devices

    for _, properties in settings.devices.items():
        assert "address" in properties
        assert "channel" in properties

    veml_properties = settings.devices["VEML7700"]

    assert "0x10" == veml_properties["address"]
    assert 6 == veml_properties["channel"]
    assert 0.25 == veml_properties["gain"]
    assert 100 == veml_properties["integration_time"]

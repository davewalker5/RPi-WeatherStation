from helpers import MockLCD

def test_backlight():
    lcd = MockLCD(None, None, None, None, None, None)
    lcd.backlight_on()
    lcd.backlight_off()

    assert 1 == lcd.calls["backlight_on"]
    assert 1 == lcd.calls["backlight_off"]


def test_clear():
    lcd = MockLCD(None, None, None, None, None, None)
    lcd.clear()

    assert 1 == lcd.calls["clear"]


def test_output():
    lcd = MockLCD(None, None, None, None, None, None)
    lcd.write("Hello, World!", 1)
    lcd.write("Raspberry Pi", 2)

    line, text = lcd.output[0]
    assert 1 == line
    assert "Hello, World!" == text

    line, text = lcd.output[1]
    assert 2 == line
    assert "Raspberry Pi" == text

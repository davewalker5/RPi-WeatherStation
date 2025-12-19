import functools


class MockLCD:
    _calls : dict = None

    def __init__(self, bus, addr, mux_addr, channel, backlight, max_retries):
        cls = type(self)
        cls._calls = {
            name: 0
            for name, _ in cls.__dict__.items()
            if not name.startswith("_")
        }
        self._output = []

    @staticmethod
    def log_method_call(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            cls = type(self)
            cls._calls[func.__name__] = cls._calls[func.__name__] + 1
            return func(self, *args, **kwargs)
        return wrapper

    @property
    def output(self):
        return self._output

    @property
    def calls(self):
        return self._calls

    @log_method_call
    def backlight_on(self):
        pass

    @log_method_call
    def backlight_off(self):
        pass

    @log_method_call
    def toggle_backlight(self):
        pass

    @log_method_call
    def clear(self):
        pass

    @log_method_call
    def write(self, text, line=1):
        self._output.append((line, text))

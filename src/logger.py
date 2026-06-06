class Logger:
    """Синглтон-логгер с цветным выводом сообщений уровней INFO, WARNING, ERROR."""

    _instance = None
    _COLORS = {
        "DEBUG": "\033[94m",
        "INFO": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
    }
    _RESET = "\033[0m"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _log(self, level: str, message: str) -> None:
        """Внутренний метод для форматированного вывода сообщения."""
        color = self._COLORS.get(level, self._RESET)
        print(f"{color}[{level}] {message}{self._RESET}")

    def debug(self, message: str) -> None:
        """Логирование отладочного сообщения (синий цвет)."""
        self._log("DEBUG", message)

    def info(self, message: str) -> None:
        """Логирование информационного сообщения (зеленый цвет)."""
        self._log("INFO", message)

    def warning(self, message: str) -> None:
        """Логирование предупреждения (желтый цвет)."""
        self._log("WARNING", message)

    def error(self, message: str) -> None:
        """Логирование ошибки (красный цвет)."""
        self._log("ERROR", message)


logger = Logger()

# Проверка работы синглтона и методов
if __name__ == "__main__":
    logger1 = Logger()
    logger2 = Logger()

    print(f"Один и тот же объект? {logger1 is logger2 and logger is logger1}")  # True

    logger1.info("System is running")
    logger1.debug("Value is set to 0")
    logger2.warning("Storage is almost full")
    logger1.error("ID not found in data base")

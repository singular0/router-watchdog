"""Base device capable of rebooting."""

from abc import ABC, abstractmethod


class DeviceConfigError(Exception):
    """Device configuration error."""

    pass


class RebootableDevice(ABC):
    """Base abstract class for rebootable device."""

    @abstractmethod
    def reboot(self):
        """Reboot device."""
        raise NotImplementedError('Reboot device is not implemented')

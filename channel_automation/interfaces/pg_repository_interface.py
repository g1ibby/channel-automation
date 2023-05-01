from typing import List

from abc import ABC, abstractmethod

from channel_automation.models import ChannelInfo
from channel_automation.models.source import Source


class IRepository(ABC):
    @abstractmethod
    def add_source(self, source: Source) -> Source:
        """
        Add a new source to the repository.

        Args:
            source (Source): The source to add.

        Returns:
            Source: The added source.
        """
        pass

    @abstractmethod
    def disable_source(self, source_id: int) -> None:
        """
        Disable a source in the repository.

        Args:
            source_id (int): The ID of the source to disable.
        """
        pass

    @abstractmethod
    def get_active_sources(self) -> list[Source]:
        """
        Get all active sources in the repository.

        Returns:
            List[Source]: A list of active sources.
        """
        pass

    @abstractmethod
    def add_channel(self, channel: ChannelInfo) -> ChannelInfo:
        """
        Add or update a channel in the repository.

        Args:
            channel (ChannelInfo): The channel to add or update.

        Returns:
            ChannelInfo: The added or updated channel.
        """
        pass

    @abstractmethod
    def remove_channel(self, channel_id: str) -> None:
        """
        Remove a channel from the repository.

        Args:
            channel_id (str): The ID of the channel to remove.
        """
        pass

    @abstractmethod
    def get_all_channels(self) -> list[ChannelInfo]:
        """
        Get all channels in the repository.

        Returns:
            List[ChannelInfo]: A list of all channels.
        """
        pass

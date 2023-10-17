from typing import List, Optional

from abc import ABC, abstractmethod

from channel_automation.models import ChannelInfo
from channel_automation.models.admin import Admin
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
    def update_channel(self, channel: ChannelInfo) -> ChannelInfo:
        """
        Update an existing channel in the repository.

        Args:
            channel (ChannelInfo): The channel information to update.

        Returns:
            ChannelInfo: The updated channel.
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

    @abstractmethod
    def get_channel_by_id(self, channel_id: str) -> Optional[ChannelInfo]:
        """
        Get a channel by its ID from the repository.

        Args:
            channel_id (str): The ID of the channel to retrieve.

        Returns:
            Optional[ChannelInfo]: The retrieved channel, or None if not found.
        """
        pass

    @abstractmethod
    def add_admin(self, admin: Admin) -> Admin:
        """
        Add a new admin to the repository.

        Args:
            admin (Admin): The admin to add.

        Returns:
            Admin: The added admin.
        """
        pass

    @abstractmethod
    def get_active_admins(self) -> list[Admin]:
        """
        Get all active admins in the repository.

        Returns:
            List[Admin]: A list of active admins.
        """
        pass

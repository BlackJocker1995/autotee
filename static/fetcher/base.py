from abc import ABC, abstractmethod
from typing import Optional


class IDocumentFetcher(ABC):
    """
    An abstract base class representing a document fetcher interface.

    This class defines the contract for classes that implement document fetching functionality.
    Subclasses must implement the `fetch` method to provide specific document retrieval logic.
    """
    
    @abstractmethod
    def fetch(self, identifier: str) -> Optional[str]:
        """
        Fetch the content of a document.

        This abstract method should be implemented by subclasses to retrieve
        the content of a document based on the provided identifier.

        Args:
            identifier (str): A unique identifier for the document to be fetched.

        Returns:
            Optional[str]: The content of the document as a string if successful,
                           or None if the document cannot be fetched.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        pass

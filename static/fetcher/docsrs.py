import requests
from bs4 import BeautifulSoup
from typing import Optional
from .base import IDocumentFetcher


class DocsRsFetcher(IDocumentFetcher):
    """
    A fetcher for retrieving Rust function documentation from docs.rs.

    This class implements the IDocumentFetcher interface and provides
    functionality to fetch documentation for Rust functions from the docs.rs website.

    Attributes:
        base_url (str): The base URL for the docs.rs website.
    """

    def __init__(self):
        """
        Initialize the DocsRsFetcher with the base URL for docs.rs.
        """
        self.base_url = "https://docs.rs"
        
    def fetch(self, identifier: str) -> Optional[str]:
        """
        Fetch the documentation for a specific Rust function.

        This method attempts to retrieve the documentation for a given Rust function
        from docs.rs. It constructs the URL based on the provided identifier,
        sends a GET request, and parses the HTML response to extract the function description.

        Args:
            identifier (str): A string in the format "crate_name/function_name"
                              identifying the Rust function to fetch documentation for.

        Returns:
            Optional[str]: The text content of the function's documentation if found,
                           or None if the fetch operation fails or no documentation is found.

        Raises:
            No exceptions are raised; all exceptions are caught and None is returned.

        Note:
            This method uses the requests library to fetch the HTML content and
            BeautifulSoup to parse it. If the request fails or the parsing encounters
            an error, the method will return None.
        """
        try:
            crate_name, function_name = identifier.split("/")
            url = f"{self.base_url}/{crate_name}/latest/{crate_name}/{function_name}.html"
            
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                description = soup.find('div', class_='docblock')
                return description.get_text(strip=True) if description else None
                
            return None
        except Exception:
            return None

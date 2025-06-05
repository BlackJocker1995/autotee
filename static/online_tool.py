from LLM.LLModel import OpenAIModel
from .fetcher.docsrs import DocsRsFetcher


def online_search(query):
    """Perform an online search using an LLM model.

    :param query: The search query to be processed by the LLM
    :type query: str
    :return: The response from the LLM model
    :rtype: str
    """
    codescan = OpenAIModel("gpt-4o")
    return codescan.query(f"What is {query}?")


def fetch_rust_function_doc(crate_name, function_name):
    """Fetch Rust function documentation from docs.rs.

    :param crate_name: The name of the Rust crate
    :type crate_name: str
    :param function_name: The name of the function to get documentation for
    :type function_name: str
    :return: The function documentation if found, otherwise an error message
    :rtype: str
    """
    fetcher = DocsRsFetcher()
    identifier = f"{crate_name}/{function_name}"
    result = fetcher.fetch(identifier)
    return result if result else f"No documentation found for {function_name} in {crate_name}."

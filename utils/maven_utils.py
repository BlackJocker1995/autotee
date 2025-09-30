import os

def get_java_pom_template() -> str:
    """
    Returns the content of the Java Maven pom.xml template by reading it from a file.
    """
    # Assuming the template file is located at utils/java_pom_template.xml
    template_path = os.path.join(os.path.dirname(__file__), "java_pom_template.xml")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()
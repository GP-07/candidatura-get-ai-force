EXIT_OK = 0
EXIT_INPUT_ERROR = 1
EXIT_INVALID_CONTRACT = 2

TEXT_EXTENSIONS = {".md", ".txt"}
PDF_EXTENSION = ".pdf"

# In-memory on purpose, to keep this project small. A larger project should keep
# these lists in a database or a persistent file.
GENERIC_WORDS_ES = {"desarrollo", "experiencia", "software", "equipo", "proyecto", "trabajo"}
GENERIC_WORDS_EN = {"development", "experience", "software", "team", "project", "work"}

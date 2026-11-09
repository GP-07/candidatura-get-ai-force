EXIT_OK = 0
EXIT_INPUT_ERROR = 1
EXIT_INVALID_CONTRACT = 2

EXIT_BLOCK_AGENT = 2

ANALYSIS_PATH = "private/analysis.json"
CV_TEXT_PATH = "private/converted/cv.txt"
REPORT_PATH = "private/report.json"
REJECTED_LOG_PATH = "private/rejected_quotes.jsonl"
ATTEMPTS_PATH = "private/.analysis_attempts"

TEXT_EXTENSIONS = {".md", ".txt"}
PDF_EXTENSION = ".pdf"

# In-memory on purpose, to keep this project small. A larger project should keep
# these lists in a database or a persistent file.
GENERIC_WORDS_ES = {"desarrollo", "experiencia", "software", "equipo", "proyecto", "trabajo"}
GENERIC_WORDS_EN = {"development", "experience", "software", "team", "project", "work"}

from utils.packages import *
load_dotenv()

api_key = os.getenv("LITELLM_KEY")
client = OpenAI(api_key=api_key,
                base_url="http://3.110.18.218")
parser_model = os.getenv("PARSER_MODEL")
summarizer_model = os.getenv("SUMMARIZER_MODEL")
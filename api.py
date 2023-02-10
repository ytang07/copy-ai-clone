"""A Steamship package for prompt-based text generation.

This package provides a simple template for building a prompt-based API service.

To run:

1. Run `pip install steamship termcolor`
2. Run `ship login`
3. Run `python api.py`

To deploy and get a public API and web demo:

1. Run `echo steamship >> requirements.txt`
2. Run `echo termcolor >> requirements.txt`
3. Run `ship deploy`

To learn more about advanced uses of Steamship, read our docs at: https://docs.steamship.com/packages/using.html.
"""
import inspect
from termcolor import colored

from steamship import check_environment, RuntimeEnvironments, Steamship
from steamship.invocable import post, PackageService
import string


class PromptPackage(PackageService):
  # When this package is deployed, this annotation tells Steamship
  # to expose an endpoint that accepts HTTP POST requests for the request paths.
  # See README.md for more information about deployment.
  POINTS_LLM_CONFIG = {
    "max_words": 150,
    "temperature": 0.75
  }
  PARAGRAPH_LLM_CONFIG = {
    "max_words": 300,
    "temperature": 0.3
  }

  # generate section headers via title inputs
  # ask for title, keywords, and tone
  @post("generate_outline")
  def generate_outline(self, title: str, keywords: list[str], tone: str) -> str:
    """Generates an outline based on title, keywords, and tone supplied by user"""
    prompt = f"""Generate four headers for a technical article titled {title}
      focused on {", ".join(keywords)} with a {tone} tone"""
    # print(prompt)
    self.tone = tone
    points_llm = self.client.use_plugin("gpt-3",  "points", config=self.POINTS_LLM_CONFIG)

    return points_llm.generate(prompt, clean_output=False)

  # generate talking points for each section header
  @post("generate_talking_points")
  def generate_talking_points(self, header: str, tone: str) -> str:
    """Generates three talking points for the outline"""
    prompt = f"""Generate three talking points for a section of a 
    technical article titled {header} with a {tone} tone"""
    # print(prompt)
    points_llm = self.client.use_plugin("gpt-3", "points", config=self.POINTS_LLM_CONFIG)

    return points_llm.generate(prompt, clean_output=False)

  # generate paragraphs via talking points
  @post("generate_main_paragraph")
  def generate_main_paragraph(self, point: str, tone: str) -> str:
    """Generates a paragraph for a talking point"""
    prompt = f"""Generate a four sentence paragraph based
    on {point} with a {tone} tone"""
    # print(prompt)
    paragraph_llm = self.client.use_plugin("gpt-3", "paragraph", config=self.PARAGRAPH_LLM_CONFIG)

    return paragraph_llm.generate(prompt, clean_output=False)

  # generate introduction paragraph for a section
  @post("generate_intro_paragraph")
  def generate_intro_paragraph(self, title: str, headers: list[str], tone: str) -> str:
    """Generates three talking points for the outline"""
    prompt = f"""Generate a four sentence article introduction paragraph with a {tone} tone 
    for an article titled "{title}" with the headers {", ".join(headers)}"""
    # print(prompt)
    # print(type(prompt))
    paragraph_llm = self.client.use_plugin("gpt-3", "paragraph", config=self.PARAGRAPH_LLM_CONFIG)

    return paragraph_llm.generate(prompt, clean_output=False)
  
  @post("generate_conclusion_paragraph")
  def generate_conclusion_paragraph(self, title: str, intro: str, tone: str) -> str:
    """Generates three talking points for the outline"""
    prompt = f"""Generate a four sentence section conclusion paragraph with a {tone} tone 
    for an article titled {title} with the introduction paragraph:{intro}"""
    # print(type(prompt))
    paragraph_llm = self.client.use_plugin("gpt-3", "paragraph", config=self.PARAGRAPH_LLM_CONFIG)

    return paragraph_llm.generate(prompt,clean_output=False)

  # helper function to tie it all together

def response_to_list(response: str) -> list[str]:
  response_list = []
  item = ""
  for char in response:
    if not char.isdigit() and char not in string.punctuation:
      item += char
    if char == "\n" and item.strip() != "":
      # print(item)
      response_list.append(item.strip())
      # print(item)
      item = ""
  if item != "":
    # print(item)
    response_list.append(item.strip())
  return response_list

# Try it out locally by running this file!
if __name__ == "__main__":
  # print(colored("Generate Compliments with GPT-3\n", attrs=['bold']))

  # # This helper provides runtime API key prompting, etc.
  # check_environment(RuntimeEnvironments.REPLIT)

  with Steamship.temporary_workspace() as client:
    # initialize
    generator = PromptPackage(client)
    title = "A Guide to Natural Language Processing"
    headers = generator.generate_outline(title, 
      ["nlp", "ai", "natural language processing"], "informative")
    # print(headers)
    headers_list = response_to_list(headers.strip())
    # print(headers_list)

    # create a map of headers to paragraphs
    header_talking_points_map = {}
    intro = generator.generate_intro_paragraph(title, title, "informative")
    header_paragraphs_map = {}
    print(f"Intro: {intro}")
    # turn each header into a section via talking points
    for header in headers_list:
      talking_points = generator.generate_talking_points(header, "informative")
      # print(talking_points)
      header_talking_points_map[header] = response_to_list(talking_points)
      print(f"Header: {header}")
      print(f"Talking Points: {header_talking_points_map[header]}")
      # print(len(header_talking_points_map[header]))
      paragraphs = []
      for point in header_talking_points_map[header]:
        pg = generator.generate_main_paragraph(point, "informative")
        print(f"Point: {point}")
        print(f"Paragraph:\n{pg}")
        paragraphs.append(pg)
      header_paragraphs_map[header] = paragraphs
      print(f"paragraphs: {paragraphs}")
      conclusion = generator.generate_conclusion_paragraph(title, intro, "informative")
    with open(f"{title}.txt", "w") as f:
      f.write(intro + "\n")
      for header, paragraphs in header_paragraphs_map.items():
        f.write(header + "\n")
        f.write("\n".join(paragraphs))
      f.write(conclusion)

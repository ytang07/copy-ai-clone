from steamship import Steamship
from steamship.invocable import post, PackageService
import typing

class PromptPackage(PackageService):
  POINTS_LLM_CONFIG = {
    "max_words": 150,
    "temperature": 0.75
  }
  ARTICLE_LLM_CONFIG = {
    "max_words": 2500,
    "temperature": 0.5
  }
  
  # generate
  @post("generate")
  def generate(self, title: str, tone:str, tags: str) -> str:
    """Generates an article using title, tone, and a comma 
    separated list of tags input as a string"""
    # initialize
    tags = [tag.strip() for tag in tags.split(",")]

    headers = self.generate_outline(title, tags, tone)
    headers_list = response_to_list(headers.strip())

    # create a map of headers to paragraphs
    # turn each header into a section via talking points
    header_talking_points_map = {}
    for header in headers_list:
      talking_points = self.generate_talking_points(header, tone)
      header_talking_points_map[header] = response_to_list(talking_points)

    # generate and save article
    article = self.generate_article(title, header_talking_points_map, tone)
    return article

  # generate section headers 
  @post("generate_outline")
  def generate_outline(self, title: str, keywords: typing.List[str], tone: str) -> str:
    """Generates an outline based on title, keywords, and tone supplied by user"""
    prompt = f"""Generate three headers for a technical article titled {title}
      focused on {", ".join(keywords)} with a {tone} tone"""

    points_llm = self.client.use_plugin("gpt-3",  "points", config=self.POINTS_LLM_CONFIG)
    return points_llm.generate(prompt, clean_output=False)

  # generate talking points for each section header
  @post("generate_talking_points")
  def generate_talking_points(self, header: str, tone: str) -> str:
    """Generates three talking points for the outline"""
    prompt = f"""Generate three short talking points about {header} with a {tone} tone"""

    points_llm = self.client.use_plugin("gpt-3", "points", config=self.POINTS_LLM_CONFIG)

    return points_llm.generate(prompt, clean_output=False)

  # generate article
  @post("generate_article")
  def generate_article(self, title: str, header_point_map: dict, tone: str) -> str:
    """Generates three talking points for the outline"""
    sections = ", ".join(header_point_map.keys())

    sentences = []
    for header, points in header_point_map.items():
        sentences.append(f"The section {header} should be about {', '.join(points)}.")
    sentences = " ". join(sentences)

    prompt = f"""Generate a technical article with title {title} in a {tone} tone.
    The article should have three sections: {sections}. {sentences} The article should also
    include an introduction paragraph and a conclusion paragraph. Do not repeat any sentences."""

    points_llm = self.client.use_plugin("gpt-3", "article", config=self.ARTICLE_LLM_CONFIG)
    return points_llm.generate(prompt)

def response_to_list(response: str) -> typing.List[str]:
  """turn a response string into a list of string, used for GPT3 response
  when asking for a list of items"""
  response_list = []
  item = ""
  for char in response:
    if not char.isdigit() and char != '.':
      item += char
    if char == "\n" and item.strip() != "":
      response_list.append(item.strip())
      item = ""
  if item != "":
    response_list.append(item.strip())
  return response_list

# Try it out locally by running this file!
if __name__ == "__main__":
  with Steamship.temporary_workspace() as client:
    # initialize
    gen_ai = PromptPackage(client)
    title = input("What do you want to title your article? ")
    tone = input("What is the tone of your article? ")
    tags = input("Enter up to 5 tags for your article (separated by commas) ")
    tags = [tag.strip() for tag in tags.split(",")]

    headers = gen_ai.generate_outline(title, tags, tone)
    headers_list = response_to_list(headers.strip())

    # print headers and ask for edits
    print(headers.strip())
    edit = input("Would you like to edit the headers? (Y/n) ")
    while edit.lower() == "y":
      num_header = int(input("Which header would you like to edit? "))
      print(f"Current header: {headers_list[num_header-1]}")
      new_header = input("Please re-write the header as you desire\n")
      headers_list[num_header-1] = new_header
      edit = input("Would you like to continue editing the headers? (Y/n) ")
  
    print("Generating Talking Points using ...")
    for header in headers_list:
      print(header)

    # create a map of headers to paragraphs
    # turn each header into a section via talking points
    header_talking_points_map = {}
    for header in headers_list:
      talking_points = gen_ai.generate_talking_points(header, tone)
      header_talking_points_map[header] = response_to_list(talking_points)
      print(f"\033[1;32mHeader: {header}\nPoints:\033[0;37m")
      for point in header_talking_points_map[header]:
        print(point)
      edit = input("Would you like to edit any points? (Y/n) ")
      while edit.lower() == "y":
        points = header_talking_points_map[header]
        # get the point to be edited
        num_point = int(input("Which point would you like to edit? "))
        print(header_talking_points_map[header][num_point-1])
        new_point = input("Please re-write the point as you desire\n")
        points[num_point-1] = new_point
        edit = input("Would you like to continue editing the headers? (Y/n) ")
    
    # inform user that article is being generated
    print("Generating Article using ...")
    for header, points in header_talking_points_map.items():
      print(f"\033[1;32mHeader: {header}\nPoints:\033[0;37m")
      for point in points:
        print(point)

    # generate and save article
    article = gen_ai.generate_article(title, header_talking_points_map, tone)

    # generate and save article
    with open(f"{title}.txt", "w") as f:
        f.write(article)

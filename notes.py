from notion_client import Client
import time
import re
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

fileai = genai.get_file(name="160t2rb9ffnu")
#response = model.generate_content([fileai,f"This book is about the Indian Economy. So I want you to make a comma seperated list of all the chapters in this book, only from the index pages. Only the chapter names, no additional info."])

#response=response.text



response="Output of an Economy, Towards Inclusive Growth, Sustainable Development and Climate Change, Poverty and Social Sector, Food Security, Agriculture Sector, Land Reforms, Salient Features, Industrial Sector and Liberalization, Infrastructure Development, Investment Models, Integrated Energy Policy, Government Finances, Reserve Bank of India and Monetary Policy Committee, Banking, Inflation, Capital Market, Planning in India, Looking Outward, Inward and Outward-Looking Economies, Going Forward - India and Globalization, Export-led Growth Strategy, Foreign Trade Policy, Balance of Payments, Trade Reforms, Foreign Investment, Multilateral Financial Institutions, External Debt of India, Exchange Rate Determination, Foreign Exchange Reserves, Regional Trading Blocs, Global Economy - A Transition, Lessons From Crises, Global Financial Meltdown, Overview of Recent Crises, Global Consensus, Global Unresolved Issues, India's Efforts Towards Economic Reforms, Indian Economy - Outlook and Challenges"
chapter_array = response.split(",")
print(chapter_array)

def createNotionNotes(text_array):
    page_content =[]

    for item in text_array:
      if len(item)>1 :
        if item.strip()[0:2] == "##":
          pass
        elif item.strip()[0:2] == "**":
          block={
                  "object": "block",
                  "type": "heading_2",
                  "heading_2": {
                      "rich_text": [
                          {"type": "text", "text": {"content": item.strip()[2:].replace("*", "")}}
                      ]
                  }
              }
          page_content.append(block)

        elif item.strip()[0] == "$":
            block = {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {"type": "text", "text": {"content": item.strip()[1:].replace("$", "")}}
                         ]
                }
                    }
            page_content.append(block)

        elif item.strip()[0] == "*":
          bullet=item.strip()[1:]
          bullet = bullet.replace("*", "")
          block= {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": bullet
                    }
                }
            ]
        }
    }
          page_content.append(block)

    print(page_content)
    return page_content




# Initialize the Notion client
notion = Client(auth="secret_nlzhEtmBxTMww70DiJKrJELim4ZWbj8m7WFH3zigM5G")


def createNotionPage(page_content,chapter,num):
# Create a new page
    title_name="Chapter "+str(num)+": "+chapter
    response = notion.pages.create(
        parent={
            "page_id": "d8a22aa108b5459d896f2747ca8c4de8"
        },
        properties={
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": title_name
                    }
                }
            ]
        },
        children=page_content
    )

    # Print the response
    print(response)

i=1
choice="y"
while choice!="b":
  chapter = chapter_array[i-1]
  response = model.generate_content([fileai,f"Read the book. Give me a complete hyper detailed yet summarised FIVE page notes. Use double hash ## symbols for title, double asterisk ** for subheadings, single asterisks * for bullet points and single dollar $ for paragraphs. (VERY IMPORTANT) Do not use formating for bold or these special symbols inside each of any these blocks in between the lines.Use these symbols only to enclose a line or a heading. (VERY IMPORTANT) Make sure that all blocks which can be headings, paragraphs or bullet points are seperated by newline seperator to put them on different lines. (VERY IMPORTANT) Do not use any special character other than commas (,) and periods (.) inside the blocks. Using special charcters like single or double quotes within the text blocks can break the program. (VERY IMPORTANT) Do not use single quotes or double quotes at any cost anywhere within the text.Do not start a new block on the same line. Use a good ratio of bullet point lines. Now make the notes on the chapter: {chapter} . Do not provide a chapter wide summary but if you do, provide it under a Conclusion subheading "])
  text=response.text
  text_array=text.split("\n")
  print("TEXT CONTENT:",text_array)
  print("\n\n\n")
  page_content=createNotionNotes(text_array)
  try:
      createNotionPage(page_content,chapter,i)
  except:
      print("notion exception, trying again")
      continue

  choice=input("Enter y or r or b")
  if choice == "y":
      print(i)
      i=i+1
      time.sleep(5)
  elif choice == "r":
      continue
  elif choice == "b":
      break
  else:
      continue



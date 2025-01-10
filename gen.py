import openai
import os
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI
import re

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Ensure the API key is set in your environment

class Definition(BaseModel):
    key: str
    value: str

class DefinitionList(BaseModel):
    definitions: list[Definition]

class SubTopicComplete(BaseModel):
    title: str
    description: str
    parent_topic: str
    definitions: list[Definition]
    domain: str

class SubTopic(BaseModel):
    title: str
    description: str
    parent_topic: str = None
    domain: str = None

class Topic(BaseModel):
    title: str
    description: str
    sub_topics: list[str]
    domain: str

class Domain(BaseModel):
    subjects: list[str]

#doesn't take in topic/subtopoiic obj cuz it creates Topic
def get_topic(topic, domain, num=2, content_type="definitions"):
    topic_title=topic
    #domain="CompTIA A+ Exam"
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"I'm building a list of {content_type} to study for {domain}"},
            {"role": "system", "content": f"I'm currently working on topic with a title of {topic_title}"},
            {"role": "system", "content": f"I need to get some information about this topic"},
            {"role": "system", "content": f"Don't use any : in your response"},
            {"role": "user", "content": f"Please provide up to {num} sub-topics for {topic_title}, a topic description, and the topic title (.e.g. Lesson 2 Installing System Devices)"},
        ],
        response_format=Topic,
    )

    # Get the response content properly (fixing the TypeError)
    response_content = completion.choices[0].message.parsed
    #idk if this is needed but I don't want chatgpt to overwrite it
    response_content.domain=domain
    return response_content
"""
def get_sub_topic(topic, num=2):
    all_quotes={}
    for topic in subtopics:
        pattern = r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s-]'
        pattern=r'[^a-zA-Z0-9\s\-_À-ÿ\u0100-\u017F\u0400-\u04FF]'
        author_name=re.sub(pattern, '', author.name)
        pattern = r'[<>:"/\\|?*\x00-\x1F]'
        author_name= re.sub(pattern, '', author_name)
        print(f"Getting quotes for {author_name}")
        try:
            quotes=get_author_quotes(author_name, subject=subject, num=num)
            all_quotes[author_name]=quotes
        except Exception as e:
            print(f"exception: ",e)

    return all_quotes
"""

def get_sub_topics(topic):
    #domain="CompTIA A+ Exam"
    domain=topic.domain
    sub_topics=[]
    for subtopic in topic.sub_topics:
        # Make the API call to OpenAI's chat completion endpoint
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"I'm building a set of descriptions of sub topics for {domain}"},
                {"role": "system", "content": f"I'm currently working on the topic {topic.title} with a sub-topic of {subtopic}"},
                {"role": "system", "content": f"Don't use any : in your response."},
                {"role": "user", "content": f"Please provide a description for the subtopic."},
            ],
            response_format=SubTopic,
        )
        # Get the response content properly (fixing the TypeError)
        response_content = completion.choices[0].message.parsed
        #Stuff I dont want chatgpt to overwrite
        response_content.parent_topic=topic.title
        response_content.domain=topic.domain
        sub_topics.append(response_content)
    return sub_topics

def get_sub_topic_definitions(sub_topic, num=2, content_type="definitions", ):
    # Make the API call to OpenAI's chat completion endpoint
    #domain="CompTIA A+ Exam"
    domain=sub_topic.domain
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"I'm building a list of {content_type} to study for {domain}"},
            {"role": "system", "content": f"I'm currently working on {content_type} for the topic {sub_topic.parent_topic} with a sub-topic of {sub_topic.title}"},
            {"role": "system", "content": f"Don't use any : in your response."},
            {"role": "user", "content": f"Please provide at least 2 and up to {num} {content_type} for the subtopic {sub_topic.title} with description {sub_topic.description} most relevant to the {domain}"},
        ],
        response_format=DefinitionList,
    )

    # Get the response content properly (fixing the TypeError)
    response_content = completion.choices[0].message.parsed
    
    return response_content


from genpage import *

# Call the function to write the quote to a Jekyll page

def write_subtopic(subtopic ):
    pattern = r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s-]'
    pattern=r'[^a-zA-Z0-9\s\-_À-ÿ\u0100-\u017F\u0400-\u04FF]'
    parent_topic=re.sub(pattern, '', subtopic.parent_topic)
    pattern = r'[<>:"/\\|?*\x00-\x1F]'
    subtopic.title = re.sub(pattern, '', subtopic.title)
    
    
    for definition in subtopic.definitions:
        print(f"***defintion***",definition)
        page_content=definition.key+": "+definition.value
        #(topic, content, subtopic, title)
        print("****Writing to page: " , parent_topic, definition.value, subtopic.title, definition.key)
        write_quote_to_jekyll_page(parent_topic, page_content, subtopic.title, definition.key)
        #create_author_index(quote.author, subject, description="No Description" )
        #create_subject_index(subject)

def write_topic(subject, domain, num=10, order=0, content_type="definitions"):
    topic=get_topic(subject, domain, num=num, content_type=content_type)
    print(topic)
    create_subject_index(topic, order=order)
    #print (type(topic))
    subtopic_titles=topic.sub_topics
    print(f"subtopic titles {subtopic_titles}")

    sub_topics=get_sub_topics(topic)
    #get definitions
    complete_sub_topics=[]
    num_addon=num+8
    for sub_topic in sub_topics:
        definitions=get_sub_topic_definitions(sub_topic, num=num_addon,content_type=content_type).definitions
        print(f"definitions: {definitions}\n\n")
        #print(f"dir",dir(definitions))
        complete_sub_topic=SubTopicComplete(title=sub_topic.title, description=sub_topic.description, parent_topic=sub_topic.parent_topic, definitions=definitions, domain=sub_topic.domain)
        complete_sub_topics.append(complete_sub_topic)
    print(complete_sub_topics[0])

    #******
    sub_topics=complete_sub_topics

    if sub_topics != []:
        print("Topic Sub Topics:", len(sub_topics))
        for subtopic in sub_topics:
            pattern = r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s-]'
            pattern=r'[^a-zA-Z0-9\s\-_À-ÿ\u0100-\u017F\u0400-\u04FF]'
            subtopic_title=re.sub(pattern, '', subtopic.title)
            print('*'*40)
            print(subtopic_title)
            clean_description=re.sub(r'"', r'\\"', subtopic.description)
            create_author_index(subtopic_title, topic.title, description=subtopic.description )
    else:
        print("Failed to write topic")
        return

    #quotes=get_authors_quotes(authors, subject=subject, num=num)
    for subtopic in sub_topics:
        definitions=subtopic.definitions
        for definition in definitions:
            print(definition)
            write_subtopic(subtopic)


# Main function to execute the script and print the results

def get_subjects_from_class(testing=True):
    subjects=[
    "Lesson 1 Installing Motherboards and Connectors",
    "Lesson 2 Installing System Devices",
    "Lesson 3 Troubleshooting PC Hardware",
    "Lesson 4 Comparing Local Networking Hardware",
    "Lesson 5 Configuring Network Addressing and Internet Connections",
    "Lesson 6 Supporting Network Services",
    "Lesson 7 Summarizing Virtualization and Cloud Concepts",
    "Lesson 8 Supporting Mobile Devices",
    "Lesson 9 Supporting Print Devices",
    "Lesson 10 Configuring Windows",
    "Lesson 11 Managing Windows",
    "Lesson 12 Identifying OS Types and Features",
    "Lesson 13 Supporting Windows",
    "Lesson 14 Managing Windows Networking",
    "Lesson 15 Managing Linux and macOS",
    "Lesson 16 Configuring SOHO Network Security",
    "Lesson 17 Managing Security Settings",
    "Lesson 18 Supporting Mobile Software",
    "Lesson 19 Using Support and Scripting Tools",
    "Lesson 20 Implementing Operational Procedures",
    ]

    if testing: return subjects[0:2]
    return subjects

def get_subjects_from_exam_guide(testing=True):
    subjects = [
    "Mobile Devices",
    "Networking",
    "Hardware",
    "Storage Devices",
    "Input and Output Devices",
    "Operating Systems",
    "Security Fundamentals",
    "Troubleshooting Methodology",
    "Virtualization",
    "Networking Protocols",
    "Cloud Computing",
    "Safety and Environmental Procedures",
    "Operational Procedures",
    "Wireless Technologies",
    "Software Installation and Configuration",
    "Device Security",
    "Troubleshooting Printers",
    "Network Hardware",
    "Data Backup and Recovery",
    "Command-Line Tools"
]
    return subjects

def get_subjects_from_gpt(domain, num_subjects=20):
    #domain="CompTIA A+ Exam"
    # Make the API call to OpenAI's chat completion endpoint
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"I'm building a set of lesson groups for the {domain}"},
            {"role": "system", "content": f"I need you to consider the core intellectual content for the {domain}"},
            #{"role": "system", "content": f"Don't use any : in your response."},
            {"role": "user", "content": f"I need you to divde {domain} into {num_subjects} subjects to separate the content for further study"},
        ],
        response_format=Domain,
    )
    # Get the response content properly (fixing the TypeError)
    response_content = completion.choices[0].message.parsed

    return response_content.subjects

def build_site(subjects, domain, depth, order=0, content_type="definitions"):
    order=order
    for subject in subjects:
        order+=1
        print("subject...",subject)
        write_topic(subject, domain, num=depth, order=order, content_type=content_type)

def main():
    domain="CompTIA A+ Certification Exam"
    depth=8
    subjects=get_subjects_from_class(testing=False)
    #subjects=get_subjects_from_exam_guide()
    #subjects=get_subjects_from_gpt(domain, num_subjects=5)
    print(subjects)
    subjects = [item + " standards and specifications" for item in subjects] #this was solid on a+
    # subjects = [item + " technical standards" for item in subjects] probably fine but dont think as good
    #this could be tech specs, definitions, whatever 'kind' of item you want at the bottom of the ontology
    content_type="technical specifications"
    build_site(subjects, domain, depth, content_type=content_type)

if __name__ == "__main__":
    main()

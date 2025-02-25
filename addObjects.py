import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Integrations
import json

client = weaviate.connect_to_weaviate_cloud(
    cluster_url="https://ta1q8xpvrrgfdrapq6jn4w.c0.us-east1.gcp.weaviate.cloud",
    auth_credentials=Auth.api_key("OFroRwc6xwb5rLIN0pUasP1txqYJPdMyu0yM"),
)

integrations = [
    Integrations.cohere(
        api_key="vaJnTfyc9YMXCBGen8l0ttVqt5O0RUrOIIaiIshg",
    ),
]
client.integrations.configure(integrations)  # <-- Configure integrations here

storage = client.collections.get("leapData")

with open("Youtube_Data.json", "r", encoding="utf-8") as f:
    youtube_data_list = json.load(f) 

with open("crawl_results.json", "r", encoding="utf-8") as f:
    website_data_list = json.load(f) 

with storage.batch.dynamic() as batch:
    for url, content in website_data_list.items():
        batch.add_object({
            "properties": {
                "url": url,
                "content": content
            }
        })
        if batch.number_errors > 10:
            print("Batch import stopped due to excessive errors.")
            break


with storage.batch.dynamic() as batch:
    for d in youtube_data_list:
        batch.add_object({
            "title": d["class"],
            "properties": d["properties"],
        })
        if batch.number_errors > 10:
            print("Batch import stopped due to excessive errors.")
            break



client.close()  # Free up resources

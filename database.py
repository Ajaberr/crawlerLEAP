import weaviate
from weaviate.classes.init import Auth
import os
from weaviate.classes.config import Configure




client = weaviate.connect_to_weaviate_cloud(
    cluster_url= "https://ta1q8xpvrrgfdrapq6jn4w.c0.us-east1.gcp.weaviate.cloud",                                    # Replace with your Weaviate Cloud URL
    auth_credentials=Auth.api_key("OFroRwc6xwb5rLIN0pUasP1txqYJPdMyu0yM"),             # Replace with your Weaviate Cloud key
)

print(client.is_ready())  # Should print: `True`

storage = client.collections.create(
    name="leapData",
    vectorizer_config=Configure.Vectorizer.text2vec_cohere(),   # Configure the Cohere embedding integration
    generative_config=Configure.Generative.cohere()             # Configure the Cohere generative AI integration
)


client.close()  # Free up resources